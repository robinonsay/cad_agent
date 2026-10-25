#!/usr/bin/env python
"""Option-ID / position bias audit of the closed-loop controller (migration delta R02, owner decision D1).

Replays real controller decisions taken from logged packages (controller_trace.json + the llm/ transcripts) against the
live model, under several menu formats, and measures whether the controller's choice follows the content of the menu or
its letters and order (Zheng et al., ICLR 2024: multiple-choice selection bias is mainly option-ID token bias).

  venv/bin/python benchmarks/generalize/audit_controller.py --out benchmarks/generalize/loop/iter_R02/audit_before.json
  venv/bin/python benchmarks/generalize/audit_controller.py --agent --out .../audit_after.json

Variants per controller decision (N offered actions, `stop` included):
  original   the logged lettered prompt, verbatim (A, B, ...; the sensor's corrections first, stop last)
  lettered   K seeded shuffles of the same menu, re-lettered
  keyed      K seeded shuffles, content-keyed: the model answers a short reason, then the action's id (enum of ids)
  planted_*  the menu plus one planted wrong action (sensor-refuted: it closes an opening the text names, which the
             coverage sensor reports as a new failure, or failing that it changes the closure no failing check asks
             about): lettered with the plant at A, and content-keyed under K shuffles
  agent      (--agent, after R02) the controller's own decision procedure: menus.perm_vote over the content-keyed menu
Edge votes (assy_edge, a multi-key question whose options are the board edges) are replayed too: original + K shuffles
of the edge list.

Reported per decision and overall: first-position pick rate vs 1/N, cross-permutation consistency (share of calls that
agree with the modal choice), planted-wrong pick rate, and agreement with the sensor-best actions (the corrections the
sensor offered for a failing check; the logged step measured the chosen one, and stop never lowers the error).

Every call is greedy (temperature 0, seed 0): differences come from the menu format only. Answers are memoised in
--cache (keyed by model, prompt, schema and sampling), so a re-run asks only the questions it has not asked before.
Read-only on the packages; never touches held-out data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

DEFAULT_SOURCES = ["benchmarks/generalize/loop/iter_005/*/*/", "benchmarks/enclosure/loop/iter_012/target_s0/*/"]
ACTIONS_HEAD = "\n\nActions you can take now"
ACTIONS_LINE = "Actions you can take now (one per step; Python applies it, rebuilds and measures again):"
LETTER_Q = "Which one action makes the design do what the request asks? Answer with its letter."
KEYED_Q = ("Which one action makes the design do what the request asks? First give a one-sentence reason, then the "
           "action's id exactly as listed.")
REASONING = {"type": "string", "maxLength": 240, "description": "one short sentence"}
REPLY_TOKENS = 512


def obj_schema(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props)}


def action_id(a: dict) -> str:
    """The content key of a logged menu action (the same form controller.Action.ident gives since R02)."""
    if a.get("ident"):
        return a["ident"]
    kind, target, value = a.get("kind"), a.get("target") or "", a.get("value")
    if kind == "stop":
        return "stop"
    if kind == "set_closure":
        return f"set_closure:{value}"
    return f"{kind}:{target}" + ("" if value in (True, None, "") else f"={value}")


def describe(a: dict) -> str:
    """The action's words without the leading "<kind> <target>:" (the id says that)."""
    w = a.get("words", "")
    return w.split(": ", 1)[1] if ": " in w else w


def permute(seq: Sequence[Any], material: str, k: int) -> List[Any]:
    """A deterministic shuffle (sha256 of material and k seeds the generator); the same as menus.permute."""
    rnd = random.Random(int(hashlib.sha256(f"{material}|{k}".encode()).hexdigest()[:16], 16))
    out = list(seq)
    rnd.shuffle(out)
    return out


def letters(n: int) -> List[str]:
    return [chr(ord("A") + k) for k in range(n)]


def read_transcript(path: Path) -> Dict[str, str]:
    text = path.read_text()
    prompt = text.split("=== PROMPT ===\n", 1)[1].split("\n\n=== RESPONSE ===\n", 1)[0]
    response = text.split("=== RESPONSE ===\n", 1)[1].strip() if "=== RESPONSE ===" in text else ""
    return {"prompt": prompt, "response": response, "file": str(path)}


def groups(paths: Sequence[Path]) -> List[List[Dict[str, str]]]:
    """Consecutive transcripts with the same prompt (the samples of one voted question)."""
    out: List[List[Dict[str, str]]] = []
    for p in paths:
        t = read_transcript(p)
        if out and out[-1][0]["prompt"] == t["prompt"]:
            out[-1].append(t)
        else:
            out.append([t])
    return out


# ---------------------------------------------------------------------------
# Decisions from the logs
# ---------------------------------------------------------------------------


def open_connectors(prompt: str) -> List[tuple]:
    """(item, connector) open through a wall, from the "The design now:" block of a controller prompt."""
    block = prompt.split("The design now:\n", 1)[1].split("\n\n", 1)[0] if "The design now:\n" in prompt else ""
    out = []
    for line in block.splitlines():
        m = re.match(r"- (\w+)(?: \(primary\))?: .*?; connectors: (.*)$", line)
        if not m:
            continue
        for c in m.group(2).split(", "):
            mm = re.match(r"(\w+) open through (\S+)", c.strip())
            if mm:
                out.append((m.group(1), mm.group(1)))
    return out


def planted_action(prompt: str, menu: Sequence[dict], coverage: Sequence[dict], closures: Sequence[str]) -> dict:
    """One plausible but sensor-refuted action. First choice: close a connector that is open now and whose mating plug
    the text names (a design.json coverage row): the text-coverage sensor reports it failing again, so the error rises.
    Else close any open connector (an opening the design has; nothing failing asks for it). Else set a closure no
    failing check asks for."""
    named = {(r.get("item"), r.get("connector")) for r in coverage or []}
    opened = open_connectors(prompt)
    ids = {action_id(a) for a in menu}
    for pool, why in ((([o for o in opened if o in named]), "closes an opening whose plug the text names: the coverage "
                       "sensor reports it failing again"),
                      (opened, "closes an opening the design has; no failing check asks for it")):
        for item, conn in pool:
            a = {"kind": "close", "target": f"{item}.{conn}", "value": True,
                 "words": f"close {item}.{conn}: remove the enclosure wall opening for the {conn} connector, so no "
                          "plug reaches it with the enclosure closed"}
            if action_id(a) not in ids:
                return dict(a, planted=True, why=why)
    current = re.search(r"lid closure: (\w+)", prompt)
    for name in closures:
        if current and name == current.group(1):
            continue
        a = {"kind": "set_closure", "target": "closure", "value": name,
             "words": f"set the lid closure to {name}: change how the lid attaches"}
        if action_id(a) not in ids:
            return dict(a, planted=True, why="changes the closure; no failing check asks for it")
    return {}


def control_decisions(pkg: Path, closures: Sequence[str]) -> List[dict]:
    tp = pkg / "controller_trace.json"
    if not tp.exists():
        return []
    trace = json.loads(tp.read_text())
    steps = [s for s in trace.get("steps", []) if s.get("menu")]
    files = sorted((pkg / "llm").glob("*_assy_control.txt"))
    gs = groups(files)
    if not steps or len(gs) != len(steps):
        return []
    coverage = []
    dj = pkg / "design.json"
    if dj.exists():
        coverage = (json.loads(dj.read_text()).get("assembly") or {}).get("coverage") or []
    out = []
    for s, g in zip(steps, gs):
        prompt = g[0]["prompt"]
        if ACTIONS_HEAD not in prompt:
            continue
        menu = [dict(a) for a in s["menu"]]
        sensor_best = [action_id(a) for a in menu if a["kind"] != "stop"]
        out.append({"id": f"{pkg.parent.name}/{pkg.name}/step{s['step']}", "family": "control",
                    "head": prompt.split(ACTIONS_HEAD, 1)[0], "prompt": prompt, "menu": menu,
                    "ids": [action_id(a) for a in menu], "logged_votes": s.get("votes"),
                    "logged_chosen": s.get("chosen"), "logged_accepted": s.get("accepted"),
                    "logged_reason": s.get("reason"), "sensor_best": sensor_best,
                    "planted": planted_action(prompt, menu, coverage, closures)})
    return out


def edge_decisions(pkg: Path) -> List[dict]:
    files = sorted((pkg / "llm").glob("*_assy_edge.txt"))
    out = []
    for n, g in enumerate(groups(files)):
        prompt = g[0]["prompt"]
        m = re.search(r"The board edges:\n((?:- .*\n)+)\n", prompt)
        if not m:
            continue
        lines = m.group(1).rstrip("\n").split("\n")
        sides = [ln[2:].split(":", 1)[0] for ln in lines]
        items = re.findall(r"^- (\w+): .*\(\w+ connector\)$", prompt.split("?\n", 1)[-1], re.M)
        if not items:
            continue
        out.append({"id": f"{pkg.parent.name}/{pkg.name}/edge{n + 1}", "family": "edge", "prompt": prompt,
                    "lines": lines, "sides": sides, "items": items, "block": m.group(1)})
    return out


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


def lettered_prompt(head: str, options: Sequence[dict]) -> str:
    lines = "\n".join(f"- {l}: {a['words']}" for l, a in zip(letters(len(options)), options))
    return f"{head}\n\n{ACTIONS_LINE}\n{lines}\n\n{LETTER_Q}"


def keyed_prompt(head: str, options: Sequence[dict]) -> str:
    lines = "\n".join(f"- {action_id(a)}: {describe(a)}" for a in options)
    return f"{head}\n\n{ACTIONS_LINE}\n{lines}\n\n{KEYED_Q}"


# ---------------------------------------------------------------------------
# The model, memoised
# ---------------------------------------------------------------------------


class Asker:
    def __init__(self, llm, cache_path: Optional[Path], model: str):
        self.llm, self.cache_path, self.model = llm, cache_path, model
        self.cache: Dict[str, Any] = {}
        if cache_path and cache_path.exists():
            self.cache = json.loads(cache_path.read_text())
        self.calls = self.hits = 0

    def ask(self, prompt: str, schema: dict, label: str) -> dict:
        key = hashlib.sha1(json.dumps([self.model, prompt, schema, 0.0, 0], sort_keys=True).encode()).hexdigest()
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        try:
            reply = self.llm.ask_json(prompt, schema, temperature=0.0, seed=0, label=label, num_predict=REPLY_TOKENS)
        except ValueError:
            reply = {}
        self.calls += 1
        self.cache[key] = reply
        if self.cache_path and self.calls % 5 == 0:
            self.save()
        return reply

    def save(self) -> None:
        if self.cache_path:
            self.cache_path.write_text(json.dumps(self.cache, indent=0, sort_keys=True))


# ---------------------------------------------------------------------------
# Audits
# ---------------------------------------------------------------------------


def audit_control(d: dict, asker: Asker, k: int, agent_rules: Optional[dict]) -> dict:
    head, menu = d["head"], d["menu"]
    n = len(menu)
    calls: List[dict] = []

    def lettered(fmt: str, options: List[dict], prompt: Optional[str] = None, order: int = -1):
        p = prompt or lettered_prompt(head, options)
        keys = letters(len(options))
        reply = asker.ask(p, obj_schema({"action": {"type": "string", "enum": keys}}), "audit_control")
        got = reply.get("action")
        pos = keys.index(got) if got in keys else None
        calls.append({"format": fmt, "order": [action_id(a) for a in options], "k": order, "answer": got,
                      "pick": None if pos is None else action_id(options[pos]), "position": pos,
                      "n": len(options)})

    def keyed(fmt: str, options: List[dict], order: int):
        ids = [action_id(a) for a in options]
        canonical = sorted(ids)            # the enum order is not shown to the model (grammar only)
        reply = asker.ask(keyed_prompt(head, options),
                          obj_schema({"reason": REASONING, "action": {"type": "string", "enum": canonical}}),
                          "audit_control")
        got = reply.get("action")
        calls.append({"format": fmt, "order": ids, "k": order, "answer": got, "reason": reply.get("reason"),
                      "pick": got if got in ids else None, "position": ids.index(got) if got in ids else None,
                      "n": len(options)})

    lettered("original", menu, prompt=d["prompt"])
    for j in range(k):
        lettered("lettered", permute(menu, d["id"] + "|lettered", j), order=j)
    for j in range(k):
        keyed("keyed", permute(menu, d["id"] + "|keyed", j), j)
    plant = d.get("planted") or {}
    if plant:
        lettered("planted_lettered", [plant] + menu, order=0)
        for j in range(k):
            keyed("planted_keyed", permute(menu + [plant], d["id"] + "|planted", j), j)
    agent = None
    if agent_rules is not None:
        agent = agent_vote(d, asker, agent_rules)
    return {"id": d["id"], "family": "control", "n": n, "ids": d["ids"], "sensor_best": d["sensor_best"],
            "planted": {k_: plant.get(k_) for k_ in ("kind", "target", "value", "why")} if plant else None,
            "logged": {"votes": d["logged_votes"], "chosen": d["logged_chosen"], "accepted": d["logged_accepted"],
                       "reason": d["logged_reason"]},
            "calls": calls, "agent": agent, "metrics": metrics(calls, d["sensor_best"], action_id(plant) if plant
                                                               else None)}


def agent_vote(d: dict, asker: Asker, rules: dict) -> dict:
    """The R02 controller's own decision procedure on the logged menu: menus.perm_vote over the content-keyed menu
    (the controller's renderer), with the planted action added in a second vote."""
    import menus
    import controller as C

    class Cached:          # route the agent's calls through the audit cache (same greedy calls hit)
        def ask_json(self, prompt, schema, **kw):
            key = hashlib.sha1(json.dumps([asker.model, prompt, schema, kw.get("temperature"), kw.get("seed")],
                                          sort_keys=True).encode()).hexdigest()
            if key in asker.cache:
                asker.hits += 1
                return asker.cache[key]
            reply = asker.llm.ask_json(prompt, schema, **kw)
            asker.calls += 1
            asker.cache[key] = reply
            return reply

    out = {}
    for name, menu in (("menu", d["menu"]), ("planted", d["menu"] + ([d["planted"]] if d.get("planted") else []))):
        if name == "planted" and not d.get("planted"):
            continue
        actions = [C.Action(a["kind"], a.get("target") or "", a.get("value"), a.get("words", ""),
                            ident=action_id(a)) for a in menu]
        v = C.ask(Cached(), lambda order: C.menu_prompt(d["head"], order), actions, rules, d["id"])
        out[name] = {"pick": v.pick, "votes": dict(v.votes), "consistency": v.consistency,
                     "confident": v.confident, "orders": v.orders, "first_position": v.first_position}
    return out


def metrics(calls: Sequence[dict], best: Sequence[str], planted: Optional[str]) -> dict:
    out = {}
    for fmt in sorted({c["format"] for c in calls}):
        cs = [c for c in calls if c["format"] == fmt]
        valid = [c for c in cs if c["pick"] is not None]
        picks = Counter(c["pick"] for c in valid)
        modal = picks.most_common(1)[0][1] if picks else 0
        out[fmt] = {"calls": len(cs), "valid": len(valid),
                    "first_position_rate": round(sum(c["position"] == 0 for c in valid) / max(1, len(valid)), 4),
                    "chance": round(sum(1 / c["n"] for c in valid) / max(1, len(valid)), 4),
                    "consistency": round(modal / max(1, len(valid)), 4),
                    "sensor_best_rate": round(sum(c["pick"] in best for c in valid) / max(1, len(valid)), 4),
                    "stop_rate": round(sum(c["pick"] == "stop" for c in valid) / max(1, len(valid)), 4),
                    "picks": dict(picks)}
        if fmt.startswith("planted"):
            out[fmt]["planted_rate"] = round(sum(c["pick"] == planted for c in valid) / max(1, len(valid)), 4)
    return out


def audit_edge(d: dict, asker: Asker, k: int) -> dict:
    calls = []
    sides = d["sides"]
    schema = obj_schema({it: {"type": "string", "enum": sides} for it in d["items"]})
    orders = [("original", -1, list(range(len(sides))))] + \
        [("lettered", j, permute(list(range(len(sides))), d["id"] + "|edge", j)) for j in range(k)]
    for fmt, j, order in orders:
        block = "\n".join(d["lines"][i] for i in order) + "\n"
        prompt = d["prompt"] if fmt == "original" else d["prompt"].replace(d["block"], block, 1)
        reply = asker.ask(prompt, schema, "audit_edge")
        shown = [sides[i] for i in order]
        for it in d["items"]:
            got = reply.get(it)
            calls.append({"format": "original" if fmt == "original" else "shuffled", "k": j, "item": it,
                          "order": shown, "pick": got if got in sides else None,
                          "position": shown.index(got) if got in shown else None, "n": len(sides)})
    per_item = {}
    for it in d["items"]:
        cs = [c for c in calls if c["item"] == it and c["pick"] is not None]
        picks = Counter(c["pick"] for c in cs)
        per_item[it] = {"picks": dict(picks), "consistency": round(picks.most_common(1)[0][1] / max(1, len(cs)), 4)
                        if picks else 0.0}
    valid = [c for c in calls if c["pick"] is not None]
    return {"id": d["id"], "family": "edge", "n": len(sides), "items": d["items"], "calls": calls,
            "metrics": {"first_position_rate": round(sum(c["position"] == 0 for c in valid) / max(1, len(valid)), 4),
                        "chance": round(1 / len(sides), 4),
                        "consistency": round(sum(v["consistency"] for v in per_item.values()) / max(1, len(per_item)),
                                             4),
                        "per_item": per_item}}


def pooled(rows: Sequence[dict], fmt: str) -> Optional[dict]:
    cs = [c for r in rows if r["family"] == "control" for c in r["calls"] if c["format"] == fmt]
    valid = [c for c in cs if c["pick"] is not None]
    if not cs:
        return None
    rows_f = [r["metrics"][fmt] for r in rows if r["family"] == "control" and fmt in r["metrics"]]
    out = {"calls": len(cs), "valid": len(valid),
           "first_position_rate": round(sum(c["position"] == 0 for c in valid) / max(1, len(valid)), 4),
           "chance": round(sum(1 / c["n"] for c in valid) / max(1, len(valid)), 4),
           "mean_consistency": round(sum(m["consistency"] for m in rows_f) / max(1, len(rows_f)), 4),
           "sensor_best_rate": round(sum(m["sensor_best_rate"] * m["valid"] for m in rows_f) /
                                     max(1, sum(m["valid"] for m in rows_f)), 4),
           "stop_rate": round(sum(c["pick"] == "stop" for c in valid) / max(1, len(valid)), 4)}
    if fmt.startswith("planted"):
        out["planted_rate"] = round(sum(m["planted_rate"] * m["valid"] for m in rows_f) /
                                    max(1, sum(m["valid"] for m in rows_f)), 4)
    return out


def summarise(rows: Sequence[dict]) -> dict:
    out: Dict[str, Any] = {"control": {}, "edge": {}}
    for fmt in ("original", "lettered", "keyed", "planted_lettered", "planted_keyed"):
        p = pooled(rows, fmt)
        if p:
            out["control"][fmt] = p
    ctrl = [r for r in rows if r["family"] == "control"]
    # lettered (original + shuffles) together: is the pick the same action across orders, or the same position?
    both = []
    for r in ctrl:
        cs = [c for c in r["calls"] if c["format"] in ("original", "lettered") and c["pick"] is not None]
        if cs:
            both.append({"same_action": len({c["pick"] for c in cs}) == 1,
                         "same_position": len({c["position"] for c in cs}) == 1})
    out["control"]["lettered_all_orders"] = {
        "decisions": len(both), "same_action_every_order": sum(b["same_action"] for b in both),
        "same_position_every_order_not_action": sum(b["same_position"] and not b["same_action"] for b in both)}
    agents = [r["agent"] for r in ctrl if r.get("agent")]
    if agents:
        m = [a["menu"] for a in agents if "menu" in a]
        p = [a["planted"] for a in agents if "planted" in a]
        out["control"]["agent"] = {
            "decisions": len(m), "confident": sum(bool(a["confident"]) for a in m),
            "mean_consistency": round(sum(a["consistency"] for a in m) / max(1, len(m)), 4),
            "sensor_best": sum(a["pick"] in r["sensor_best"] for a, r in zip(m, [r for r in ctrl if r.get("agent")])),
            "planted_picked": sum(a["pick"] is not None and a["pick"].startswith(("close:", "set_closure:"))
                                  and a["pick"] not in r["ids"] for a, r in
                                  zip(p, [r for r in ctrl if r.get("agent") and "planted" in r["agent"]])),
            "planted_decisions": len(p),
            "first_position_rate": round(sum(a["first_position"] for a in m) / max(1, sum(len(a["orders"])
                                                                                            for a in m)), 4)}
    edges = [r for r in rows if r["family"] == "edge"]
    if edges:
        cs = [c for r in edges for c in r["calls"] if c["pick"] is not None]
        out["edge"] = {"decisions": len(edges), "item_answers": len(cs),
                       "first_position_rate": round(sum(c["position"] == 0 for c in cs) / max(1, len(cs)), 4),
                       "chance": round(sum(1 / c["n"] for c in cs) / max(1, len(cs)), 4),
                       "mean_consistency": round(sum(r["metrics"]["consistency"] for r in edges) / len(edges), 4)}
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", nargs="*", default=DEFAULT_SOURCES, help="package globs (relative to the repo)")
    ap.add_argument("--k", type=int, default=3, help="seeded shuffles per format")
    ap.add_argument("--max-decisions", type=int, default=16, help="cap on controller decisions replayed")
    ap.add_argument("--max-edge", type=int, default=6, help="cap on edge votes replayed (0 = none)")
    ap.add_argument("--model", default="ornith-1.5:9b")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--cache", default="benchmarks/generalize/loop/iter_R02/audit_cache.json")
    ap.add_argument("--agent", action="store_true", help="also run the R02 controller's own vote (after R02)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    import cad_agent as ca
    rules = json.loads((REPO / "design_rules.json").read_text())
    closures = sorted(k for k, v in (rules.get("closures") or {}).items() if isinstance(v, dict))
    pkgs = []
    for g in args.sources:
        pkgs += sorted(p for p in REPO.glob(g) if p.is_dir() and (p / "llm").is_dir())
    ctrl, edge = [], []
    for p in pkgs:
        ctrl += control_decisions(p, closures)
        edge += edge_decisions(p)
    ctrl, edge = ctrl[: args.max_decisions], edge[: args.max_edge]
    llm = ca.OllamaAgent(args.model, args.host, num_ctx=args.num_ctx)
    asker = Asker(llm, REPO / args.cache if args.cache else None, args.model)
    agent_rules = None
    if args.agent:
        import menus
        agent_rules = menus.vote_rules(rules.get("rules", {}))
    started = time.time()
    rows = []
    for d in ctrl:
        rows.append(audit_control(d, asker, args.k, agent_rules))
        print(f"{d['id']}: {json.dumps(rows[-1]['metrics'])[:300]}", flush=True)
    for d in edge:
        rows.append(audit_edge(d, asker, args.k))
        print(f"{d['id']}: {json.dumps(rows[-1]['metrics'])[:200]}", flush=True)
    asker.save()
    out = {"schema": 1, "model": args.model, "k": args.k, "sources": args.sources, "agent": bool(args.agent),
           "packages": len(pkgs), "control_decisions": len(ctrl), "edge_decisions": len(edge),
           "llm_calls": asker.calls, "cache_hits": asker.hits, "secs": round(time.time() - started, 1),
           "summary": summarise(rows), "decisions": rows}
    Path(REPO / args.out if not Path(args.out).is_absolute() else args.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
