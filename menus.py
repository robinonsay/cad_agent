"""Content-keyed, shuffled menus and permutation voting for every discrete LLM question (migration delta R02, owner
decision D1; loop/ARCHITECTURE.md 10.3 and 10.4).

Why: in R01 the controller chose the first menu option in 38 of 39 votes, with the sensor's correction always first
and `stop` always last, so agreement could not be told apart from option-ID / position bias (Zheng et al., ICLR 2024:
multiple-choice selection bias in LLMs is mainly option-ID token bias). Here:

- **Content-keyed**: the model answers with a stable option id (an action key such as `expose:usb_1`, a catalogue id, a
  board edge), never a letter or an index. The JSON schema (Ollama `format`) constrains the answer to the enum of ids in
  Python's canonical order; the model never sees the schema, only the prompt.
- **Shuffled**: the orderings of the shown options are the cyclic rotations of one deterministic permutation (sha256
  of a seed material), so every option leads once when K = the number of options, runs stay reproducible, and no
  option is pinned first or last; a menu with fewer distinct orderings than K is asked fewer times.
- **Permutation voting**: one question is asked under K seeded orderings (S samples each; design_rules.json
  `menu_orderings`, `menu_samples`). A choice is high-confidence only when it is consistent across orderings (the share
  of valid answers that agree with the winner is at least `menu_consistency_min`, with at least `menu_min_valid` valid
  answers). An inconsistent choice is low-confidence: the closed loop hands it to verifier-guided search
  (controller.py) instead of trusting it; a proposal stage records it.
- An optional short free-text `reason` comes before the constrained field (reason-then-answer).

Nothing here knows a design, a part or an action kind: an option is an id plus the words a caller renders, so new
action kinds and new menus plug in without changes here (test_no_hardcoding.py scans this module).
"""

from __future__ import annotations

import hashlib
import random
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

REASON_KEY = "reason"
REASON_SCHEMA = {"type": "string", "maxLength": 240, "description": "one short sentence"}
REPLY_TOKENS = 512          # num_predict for a reason + enum reply (assembly.REPLY_TOKENS)
SAMPLE_TEMPERATURE = 0.7    # temperature of the samples after the first in one ordering (assembly.tally's)

# defaults when design_rules.json lacks a key (the rules file carries the sourced values)
DEFAULTS = {"menu_orderings": 3, "menu_samples": 1, "menu_consistency_min": 1.0, "menu_min_valid": 2}


def vote_rules(values: Optional[Mapping[str, Any]]) -> Dict[str, float]:
    """The permutation-vote parameters from design_rules.json values (a `{"value": ...}` wrapper is unwrapped)."""
    out = {}
    for k, d in DEFAULTS.items():
        v = (values or {}).get(k, d)
        if isinstance(v, Mapping):
            v = v.get("value", d)
        out[k] = type(d)(v)
    out["menu_orderings"] = max(1, int(out["menu_orderings"]))
    out["menu_samples"] = max(1, int(out["menu_samples"]))
    return out


def permute(seq: Sequence[Any], material: str, k: int) -> List[Any]:
    """A deterministic shuffle of seq: sha256(material | k) seeds the generator (benchmarks/generalize/
    audit_controller.py uses the same function)."""
    rnd = random.Random(int(hashlib.sha256(f"{material}|{k}".encode()).hexdigest()[:16], 16))
    out = list(seq)
    rnd.shuffle(out)
    return out


def orderings(seq: Sequence[Any], material: str, k: int) -> List[List[Any]]:
    """Up to k distinct orderings of seq: the cyclic rotations of one seeded permutation (a Latin-square design: with
    k = len(seq) every option is shown once in every position), then further seeded permutations when k > len(seq).
    Fewer than k when seq has fewer distinct orderings (two options have two): a repeated ordering would only repeat
    the greedy answer and overstate the agreement."""
    base = permute(seq, material, 0)
    n = len(base)
    out: List[List[Any]] = []
    for j in range(min(k, max(1, n))):
        rot = base[j:] + base[:j]
        if rot not in out:
            out.append(rot)
    tries = 0
    while len(out) < k and tries < 64:
        tries += 1
        cand = permute(seq, material, 1000 + tries)
        if cand not in out:
            out.append(cand)
    return out


def material(*parts: Any) -> str:
    """Seed material for the orderings of one question: a sha1 of its parts (request, state, step, label, run seed)."""
    return hashlib.sha1("\x1f".join(str(p) for p in parts).encode()).hexdigest()


def run_seed(llm) -> int:
    return int(getattr(llm, "seed_offset", 0) or 0)


def menu_schema(ids: Sequence[str], key: str = "action", reason: bool = True) -> dict:
    props: Dict[str, Any] = {}
    if reason:
        props[REASON_KEY] = dict(REASON_SCHEMA)
    props[key] = {"type": "string", "enum": list(ids)}
    return {"type": "object", "properties": props, "required": list(props)}


@dataclass
class MenuVote:
    """The outcome of one permutation-voted menu question."""
    ids: List[str]                          # Python's canonical order (the schema enum; the stub's first option)
    pick: Optional[str] = None
    votes: Dict[str, int] = field(default_factory=dict)
    valid: int = 0
    calls: int = 0
    consistency: float = 0.0
    confident: bool = False
    orders: List[List[str]] = field(default_factory=list)
    answers: List[dict] = field(default_factory=list)       # per call: ordering, sample, answer, reason, position
    first_position: int = 0                 # valid answers that picked the option shown first

    def ranked(self) -> List[str]:
        """Option ids by votes (most first), ties and unvoted options in canonical order."""
        return sorted(self.ids, key=lambda i: (-self.votes.get(i, 0), self.ids.index(i)))

    def to_dict(self) -> dict:
        return {"pick": self.pick, "votes": dict(self.votes), "valid": self.valid, "calls": self.calls,
                "consistency": self.consistency, "confident": self.confident, "orders": [list(o) for o in self.orders],
                "answers": [dict(a) for a in self.answers], "first_position": self.first_position}


def decide(v: MenuVote, rules: Mapping[str, float]) -> MenuVote:
    """Winner: most votes; a tie goes to the tied option that was answered earliest (answers in asking order: ordering
    0's first sample first), so ordering 0's answer wins a tie whenever it is valid and among the tied; an invalid
    answer is never a candidate (review fix 4: the docstring said "the first ordering's answer", which the code only
    gave when that answer was valid and tied). Confident when enough answers are valid and they agree with the winner
    at least menu_consistency_min."""
    if not v.votes:
        v.pick, v.consistency, v.confident = None, 0.0, False
        return v
    best = max(v.votes.values())
    tied = [i for i in v.ids if v.votes.get(i, 0) == best]
    first = next((a["answer"] for a in v.answers if a["answer"] in tied), None)
    v.pick = first if first is not None else tied[0]   # tied[0]: unreachable (every tied option has an answer)
    v.consistency = round(v.votes[v.pick] / max(1, v.valid), 4)
    v.confident = v.valid >= int(rules["menu_min_valid"]) and v.consistency >= float(rules["menu_consistency_min"]) - 1e-9
    return v


def perm_vote(llm, label: str, render: Callable[[List[str]], str], ids: Sequence[str],
              rules: Mapping[str, float], seed_material: str, key: str = "action", reason: bool = True) -> MenuVote:
    """Ask one menu question under rules.menu_orderings seeded orderings of `ids` (menu_samples each; the first sample
    of an ordering greedy, the others at SAMPLE_TEMPERATURE with seed = the sample index). `render(order)` returns the
    prompt with the options listed in `order`. Answers outside the enum (or unparsable replies) count as invalid."""
    ids = list(ids)
    v = MenuVote(ids=ids)
    schema = menu_schema(ids, key, reason)
    for k, order in enumerate(orderings(ids, seed_material, int(rules["menu_orderings"]))):
        v.orders.append(order)
        prompt = render(order)
        for s in range(int(rules["menu_samples"])):
            v.calls += 1
            try:
                reply = llm.ask_json(prompt, schema, temperature=0.0 if s == 0 else SAMPLE_TEMPERATURE, seed=s,
                                     label=label, num_predict=REPLY_TOKENS)
            except ValueError:
                reply = {}
            got = reply.get(key) if isinstance(reply, dict) else None
            ok = got in ids
            row = {"ordering": k, "sample": s, "answer": got if ok else None,
                   "position": order.index(got) if ok else None}
            if reason and isinstance(reply, dict) and reply.get(REASON_KEY):
                row["reason"] = str(reply.get(REASON_KEY))[:240]
            v.answers.append(row)
            if ok:
                v.valid += 1
                v.votes[got] = v.votes.get(got, 0) + 1
                v.first_position += int(order.index(got) == 0)
    return decide(v, rules)


def perm_tally(llm, label: str, render: Callable[[Dict[str, List[str]]], str], lists: Mapping[str, Sequence[str]],
               schema: dict, allowed: Mapping[str, Sequence[Any]], rules: Mapping[str, float],
               seed_material: str) -> Dict[str, Any]:
    """The multi-key form (one question, several answer keys, e.g. a board edge per part): every list in `lists` (the
    options shown in the prompt) is permuted per ordering, `render(orders)` builds the prompt, and each flat answer key
    in `allowed` is counted like assembly.tally (an answer outside its enum counts as None). Returns {"counts":
    {key: Counter}, "consistency": {key: share agreeing with the key's winner}, "orders": [...], "calls": n}; the counts
    keep the order of first appearance, ordering 0 first, with the invalid answer (None) moved last, so
    assembly.majority's tie rule (first seen wins) gives the earliest valid tied answer (ordering 0's when it is valid
    and tied) and None wins only with strictly more votes than every valid answer (review fix 4)."""
    counts: Dict[str, Counter] = {k: Counter() for k in allowed}
    orders = []
    calls = 0
    per_list = {name: orderings(lst, f"{seed_material}|{name}", int(rules["menu_orderings"]))
                for name, lst in lists.items()}
    n = max([len(o) for o in per_list.values()] or [1])
    for k in range(n):
        order = {name: os_[k % len(os_)] for name, os_ in per_list.items()}
        orders.append(order)
        prompt = render(order)
        for s in range(int(rules["menu_samples"])):
            calls += 1
            try:
                reply = llm.ask_json(prompt, schema, temperature=0.0 if s == 0 else SAMPLE_TEMPERATURE, seed=s,
                                     label=label, num_predict=REPLY_TOKENS)
            except ValueError:
                continue
            for key, ok in allowed.items():
                val: Any = reply
                for part in key.split("."):
                    val = val.get(part) if isinstance(val, dict) else None
                counts[key][val if val in ok else None] += 1
    for key, c in counts.items():           # review fix 4: an invalid answer never wins a tie (majority: first seen)
        if None in c:
            n_none = c.pop(None)
            c[None] = n_none
    consistency = {}
    for key, c in counts.items():
        valid = {v: n for v, n in c.items() if v is not None}
        consistency[key] = round(max(valid.values()) / sum(valid.values()), 4) if valid else 0.0
    return {"counts": counts, "consistency": consistency, "orders": orders, "calls": calls}
