"""--mode assembly: the enclosure-designing agent (ARCHITECTURE.md sections 2-4).

The target tree (ARCHITECTURE.md section 4) is built one milestone at a time.
Iteration 002 wires the walking skeleton (ARCHITECTURE.md 7.1 step 2, 7.4):

    cad_assembly (Sequence)
    ├── LoadCatalog        parts.Catalog.load + validation gate; a failing part is dropped and noted
    ├── LoadRules          design_rules.json (generic FDM / fastener rules and spec slots, each with a source)
    ├── ParseSpec          LLM maps generic spec slots onto number ids Python extracted from the text (enum)
    ├── Contents           Python proposes catalogue candidates; LLM gives quantity + exposed (enums)
    ├── ChooseStack        LLM enum among a module's stack options
    ├── ArrangeContents    LLM: board edge per exposed item (enum); Python: mm placement (layout.py);
    │                      ConfirmArrangement: LLM ranks the feasible classes (p_yes) + vote; comparative pick
    │                      on disagreement (board-symmetric layouts are one class; p_yes is never a gate)
    ├── BuildEnvelopes     plug sweeps, keep-outs, seat / hole columns (datum-anchored), module envelopes
    │                      (parts.py, from datums); KEEP_OUTS says how each envelope role is consumed
    ├── ChooseArchetype    feasible archetypes; one feasible -> recorded as a rule choice (no LLM call)
    ├── DeriveFeatures     cavity from contents + plan keep-outs (+ design_margin), base shell, V-DRIVER columns,
    │                      standoffs + pilots, port cuts, lid + lip, corner pilaster bosses + lid holes:
    │                      feature-graph nodes whose params are expressions; every one-sided minimum is
    │                      derived at setpoint(limit) = limit + design_margin (ARCHITECTURE.md 7.9)
    ├── Build              resolve, manifold solid per body, OpenSCAD compile per body (manifold fallback, parity)
    ├── Verify             rule-derived checks on the manifold solids and on the delivered STLs (never fails)
    ├── RenderViews        views/model_* (bodies), views/ghost_* (bodies + references), views/open_* (lid off)
    └── WritePackage       base/lid .stl/.scad, model.scad, layout.json, self_report.json, feature_graph.json,
                           checks.json, verification_matrix.{md,json}, model.3mf
    finalize(): verified (every check passes on the delivered STLs) | unsatisfied; failing checks that name a
                competing rule are listed as typed requirement conflicts (assembly.conflicts, one per part,
                with a kind such as pin_pattern / flush_to_edge / no_pin_data)

The local LLM is the controller for discrete choices and answers only enums that
Python builds; Python is the plant model and the sensor. Nothing here holds a
number, part or face that is specific to one request (test_no_hardcoding.py
scans this module).
"""

import itertools
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import py_trees
from py_trees.common import Status

import assembly_checks as ac
import cad_checks as cc
import feature_graph as fg
import layout as lay
import parts as pt

ca = cc._ca()  # cad_agent (the running script's module when cad_agent.py is __main__)

REPLY_TOKENS = 512           # num_predict for the schema-constrained replies (short JSON objects)
QUOTE_CHARS = 120            # longest context quote shown for a number
CONTENT_KINDS = ("board", "module", "connector", "generic")   # plugs mate, fasteners are chosen by rules
BODIES = ("base", "lid")
DIAGONAL = math.sqrt(0.5)    # unit diagonal component (a boss sits on the diagonal of a corner)
GHOST_ALPHA = 0.3            # body opacity in the ghost renders
APERTURE_CUT_ROLES = ("port_cut", "pilot", "screw_hole")   # cuts a wall-slab region is attributed to (7.9)
OPEN_BODY = BODIES[0]        # the body shown alone, lid off, in views/open_* (the tray: standoffs, rim, bosses)
OPEN_VIEWS = ("iso", "top")  # cameras (cad_agent.VIEWS keys) rendered for the lid-off view
EVEN_ODDS = 0.5              # p_yes below this is reported as low absolute confidence (a report, never a gate)


@dataclass
class AssemblyState:
    """The blackboard of assembly mode (ARCHITECTURE.md section 3). Stages fill it in order."""
    spec: Dict[str, Any] = field(default_factory=dict)        # request numbers with provenance + rules defaults
    spec_provenance: Dict[str, str] = field(default_factory=dict)
    numbers: List[dict] = field(default_factory=list)         # the number occurrences offered to the LLM
    contents: List[dict] = field(default_factory=list)        # what goes inside, resolved against the catalogue
    items: List[lay.Item] = field(default_factory=list)
    frame: Dict[str, Any] = field(default_factory=dict)       # enclosure frame (section 3.4)
    layout: Dict[str, Any] = field(default_factory=dict)      # declared pose of every reference part
    placed: Optional[lay.Layout] = None
    graph: Optional[fg.FeatureGraph] = None                   # reference / body / add / cut / envelope nodes
    fasteners: Dict[str, float] = field(default_factory=dict)  # fastener.<use>.<param> values
    choices: Dict[str, dict] = field(default_factory=dict)    # discrete decisions + who made them
    checks: List[Any] = field(default_factory=list)           # frozen check set
    results: List[Any] = field(default_factory=list)          # latest measurement (delivered STLs)
    results_manifold: List[Any] = field(default_factory=list)
    self_report: Dict[str, Any] = field(default_factory=dict)
    reports: List[Any] = field(default_factory=list)          # loop endings
    assumptions: List[str] = field(default_factory=list)      # estimates and rules defaults used
    history: List[dict] = field(default_factory=list)         # accepted moves with error keys
    catalog: Optional[pt.Catalog] = None
    rules: Optional[pt.Rules] = None
    stage: str = ""                                           # the stage reached (or the one that failed)
    notes: List[str] = field(default_factory=list)
    parts_dir: Optional[str] = None
    rules_path: Optional[str] = None
    with_models: bool = False
    stl_source: Dict[str, str] = field(default_factory=dict)
    components: List[dict] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    resolved: Any = None
    solids: Dict[str, Any] = field(default_factory=dict)
    plan: Any = None
    layout_grid_residual: Optional[float] = None
    grid_report: Dict[str, Any] = field(default_factory=dict)  # layout.Placer.grid_report of the accepted layout
    conflicts: List[dict] = field(default_factory=list)       # typed requirement conflicts (finalize)
    arrange: Dict[str, Any] = field(default_factory=dict)     # ConfirmArrangement's whole ranking (candidates, classes)

    def summary(self) -> dict:
        return {
            "stage": self.stage,
            "notes": list(self.notes),
            "parts_dir": self.parts_dir,
            "rules_path": self.rules_path,
            "with_models": self.with_models,
            "catalog": self.catalog.ids() if self.catalog else [],
            "catalog_errors": list(self.catalog.errors) if self.catalog else [],
            "rules": dict(self.rules.values) if self.rules else {},
            "spec": dict(self.spec),
            "spec_provenance": dict(self.spec_provenance),
            "contents": list(self.contents),
            "layout": dict(self.layout),
            "arrange": dict(self.arrange),
            "grid_report": dict(self.grid_report),
            "conflicts": list(self.conflicts),
            "fasteners": dict(self.fasteners),
            "choices": dict(self.choices),
            "assumptions": list(self.assumptions),
            "stl_source": dict(self.stl_source),
            "components": list(self.components),
            "results": [r.to_dict() for r in self.results],
            "results_manifold": [r.to_dict() for r in self.results_manifold],
            "files": list(self.files),
            "deferred_gate_rules": dict(pt.DEFERRED_RULES),
            "feature_graph": self.graph.to_json() if self.graph is not None else None,
        }


class AssemblyStep(ca.Step):
    def __init__(self, name: str, design, llm=None):
        super().__init__(name, design)
        self.llm = llm

    @property
    def state(self) -> AssemblyState:
        return self.design.assy

    def fail(self, msg: str) -> Status:
        self.state.notes.append(msg)
        self.feedback_message = msg
        self.logger.info(msg)
        print(f"{self.state.stage}: {msg}", flush=True)
        return Status.FAILURE


# ---------------------------------------------------------------------------
# Controller interface helpers
# ---------------------------------------------------------------------------


def tally(llm, prompt: str, schema: dict, label: str, allowed: Dict[str, Sequence[Any]],
          n: Optional[int] = None) -> Dict[str, Counter]:
    """Per-key vote: n samples of one schema-constrained question; each flat key ("a" or "a.b") counts
    only answers inside its enum (anything else counts as None). Next to OllamaAgent.vote, which
    takes the majority of whole answers."""
    n = n or ca.VOTES
    counts = {k: Counter() for k in allowed}
    for i in range(n):
        try:
            reply = llm.ask_json(prompt, schema, temperature=0.0 if i == 0 else 0.7, seed=i, label=label,
                                 num_predict=REPLY_TOKENS)
        except ValueError:
            continue
        for key, ok in allowed.items():
            v = reply
            for part in key.split("."):
                v = v.get(part) if isinstance(v, dict) else None
            counts[key][v if v in ok else None] += 1
    return counts


def majority(c: Counter):
    """The most voted value (first seen wins a tie); None when nothing valid was voted."""
    if not c:
        return None
    best = max(c.values())
    return next(v for v, k in c.items() if k == best)


def choice(st: AssemblyState, name: str, value: Any, by: str, **extra) -> None:
    st.choices[name] = dict({"value": value, "by": by}, **extra)


# ---------------------------------------------------------------------------
# Numbers in the text (ParseSpec input)
# ---------------------------------------------------------------------------

NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_.\-])(\d+(?:\.\d+)?)(?:\s?(mm|cm|deg|degrees)\b)?(?![A-Za-z0-9])")
UNIT_SCALE = {"mm": 1.0, "cm": 10.0, "deg": 1.0, "degrees": 1.0, None: 1.0}
GROUP_SEP = re.compile(r"^\s*[x×]\s*$")
RANGE_SEP = re.compile(r"^\s*(to|-|–)\s*$")


def extract_numbers(texts: Sequence[Tuple[str, str]]) -> List[dict]:
    """Every number occurrence in (source, text) pairs: {id, value, unit, quote, source, group}.

    Each occurrence keeps its own id, so the same value in two places stays two ids. In "a x b (x c)"
    groups and "a to b" ranges the trailing unit applies to every member.
    """
    out: List[dict] = []
    for source, text in texts:
        found = list(NUMBER_RE.finditer(text))
        groups: List[List[re.Match]] = []
        for m in found:
            if groups and (GROUP_SEP.match(text[groups[-1][-1].end():m.start()])
                           or RANGE_SEP.match(text[groups[-1][-1].end():m.start()])):
                groups[-1].append(m)
            else:
                groups.append([m])
        for g in groups:
            unit = next((m.group(2) for m in reversed(g) if m.group(2)), None)
            gid = f"g{len(out) + 1}" if len(g) > 1 else None
            for m in g:
                u = m.group(2) or unit
                half = QUOTE_CHARS // 2
                lo, hi = max(0, m.start() - half), min(len(text), m.end() + half)
                quote = " ".join(text[lo:hi].split())[:QUOTE_CHARS]
                out.append({"id": f"n{len(out) + 1}", "value": float(m.group(1)) * UNIT_SCALE[u],
                            "unit": "mm" if u == "cm" else u, "text": m.group(0).strip(), "quote": quote,
                            "source": source, "group": gid})
    return out


def number_lines(numbers: Sequence[dict]) -> str:
    return "\n".join(f'{n["id"]} = {n["text"]} ({n["source"]}): "...{n["quote"]}..."' for n in numbers)


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------


class LoadCatalog(AssemblyStep):
    """Load the parts catalogue and run the import gate on every part; drop and note any failure."""

    def __init__(self, design):
        super().__init__("LoadCatalog", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "load_catalog"
        cat = pt.Catalog.load(st.parts_dir)
        for err in cat.errors:
            st.notes.append(f"catalogue: {err}")
        for pid in cat.ids():
            part = cat.get(pid)
            try:
                fails = pt.validate(pt.instantiate(part, part.gate_params()))
            except (pt.PartError, fg.ExprError, fg.MissingRefError, KeyError, ValueError) as e:
                fails = [pt.GateFailure(pid, "load", str(e))]
            if fails:
                cat.drop(pid, "; ".join(f"{f.rule}: {f.detail}" for f in fails))
                st.notes.append(f"catalogue: {pid} failed the import gate and is not used: "
                                + "; ".join(str(f) for f in fails))
        for problem in cat.cross_references():
            st.notes.append(f"catalogue: {problem}")
        st.catalog = cat
        if not cat.parts:
            st.notes.append(f"catalogue: no usable parts in {st.parts_dir}")
            self.feedback_message = "no usable parts"
            return Status.FAILURE
        self.logger.info(f"catalogue: {len(cat.parts)} parts ({', '.join(cat.ids())})")
        return Status.SUCCESS


class LoadRules(AssemblyStep):
    """Load design_rules.json (generic FDM / fastener values and spec slots, each with a source)."""

    def __init__(self, design):
        super().__init__("LoadRules", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "load_rules"
        try:
            st.rules = pt.load_rules(st.rules_path)
        except (OSError, ValueError) as e:
            st.notes.append(f"rules: cannot load {st.rules_path}: {e}")
            return Status.FAILURE
        if not st.rules.spec_slots:
            st.notes.append(f"rules: {st.rules_path} has no spec_slots")
            return Status.FAILURE
        self.logger.info(f"rules: {len(st.rules.values)} values from {st.rules_path}")
        return Status.SUCCESS


class ParseSpec(AssemblyStep):
    """Typed spec slots from the text: the LLM maps each slot onto a number id (or none); Python checks
    generic relations (one re-ask naming the violation) and fills silent slots from the rules."""

    def __init__(self, design, llm):
        super().__init__("ParseSpec", design, llm)

    def texts(self) -> List[Tuple[str, str]]:
        d = self.design
        return [("request", d.base_request or d.request)] + [(r["id"], r["text"]) for r in d.l1]

    def prompt(self, numbers, slots, violation: str = "", note: str = "") -> str:
        lines = "\n".join(f'- {s["name"]}: {s["meaning"]} ({s["unit"]})' for s in slots)
        again = (f"\nYour previous answer broke these rules: {violation}. Answer again and fix that.\n"
                 if violation else "")
        note = f"{note}\n\n" if note else ""
        return (f"An enclosure is being designed from this request and its requirements.\n\n"
                f"Numbers found in the text (each occurrence has its own id):\n{number_lines(numbers)}\n\n"
                f"{note}"
                f"For each quantity below, give the id of the number in the text that states it, or \"none\" "
                f"if the text does not state it. Never use a number for something it does not describe.\n"
                f"{lines}\n{again}")

    def ask(self, numbers, slots, violation="", label: Optional[str] = None, note: str = "") -> Dict[str, Optional[str]]:
        ids = [n["id"] for n in numbers] + ["none"]
        schema = ca.obj_schema({s["name"]: {"type": "string", "enum": ids} for s in slots})
        label = label or ("assy_spec_reask" if violation else "assy_spec")
        counts = tally(self.llm, self.prompt(numbers, slots, violation, note), schema, label,
                       {s["name"]: ids for s in slots})
        return {k: (None if majority(c) in (None, "none") else majority(c)) for k, c in counts.items()}

    @staticmethod
    def shared(answer, slots) -> Dict[str, List[str]]:
        """Number ids that the answer uses for two or more slots (each occurrence states one quantity)."""
        users: Dict[str, List[str]] = {}
        for s in slots:
            ref = answer.get(s["name"])
            if ref:
                users.setdefault(ref, []).append(s["name"])
        return {ref: names for ref, names in users.items() if len(names) > 1}

    def violations(self, answer, by_id, slots) -> List[Tuple[str, List[str]]]:
        out = []
        val = {k: by_id[v]["value"] for k, v in answer.items() if v}
        for s in slots:
            if s["default_rule"] is None and not answer.get(s["name"]):
                out.append((f"{s['name']} has no default and must be one of the numbers", [s["name"]]))
        for k, v in val.items():
            if v <= 0:
                out.append((f"{k} must be greater than 0 (got {v:g})", [k]))
        if "wall_min" in val and "wall_max" in val and val["wall_min"] > val["wall_max"]:
            out.append((f"wall_min ({val['wall_min']:g}) must not exceed wall_max ({val['wall_max']:g})",
                        ["wall_min", "wall_max"]))
        no_default = {s["name"] for s in slots if s["default_rule"] is None}
        for ref, names in self.shared(answer, slots).items():
            n = by_id[ref]
            msg = (f"{' and '.join(names)} {'both' if len(names) == 2 else 'all'} use {ref} ({n['text']}, "
                   f"'{n['quote']}'); each number in the text states one quantity")
            if set(names) <= no_default:
                msg += f" ({', '.join(names)} must be different numbers in the text)"
            out.append((msg, names))
        return out

    def resolve_shared(self, ref: str, names: List[str], numbers, by_id, slots, answer) -> Dict[str, Optional[str]]:
        """A number id still shared after the re-ask: one voted owner question gives it to one slot, then the
        other slots are re-asked with that id removed from their enum (the contested answer is no longer an
        action). No valid owner: every sharing slot falls back (rules default, flagged), as for any violation."""
        st = self.state
        n = by_id[ref]
        meaning = {s["name"]: s for s in slots}
        lines = "\n".join(f"- {k}: {meaning[k]['meaning']} ({meaning[k]['unit']})" for k in names)
        prompt = (f"An enclosure is being designed from this request and its requirements.\n\n"
                  f'Number {ref} = {n["text"]} ({n["source"]}): "...{n["quote"]}..."\n\n'
                  f"Each number in the text states exactly one quantity. Which one of these quantities does "
                  f"{ref} state?\n{lines}")
        counts = tally(self.llm, prompt, ca.obj_schema({"owner": {"type": "string", "enum": list(names)}}),
                       "assy_spec_owner", {"owner": list(names)})
        owner = majority(counts["owner"])
        if owner is None:
            st.notes.append(f"parse_spec: no valid owner for {ref} among {', '.join(names)}; they fall back")
            for k in names:
                answer[k] = None
            return answer
        losers = [k for k in names if k != owner]
        st.notes.append(f"parse_spec: {ref} states {owner} (owner vote {dict(counts['owner'])}); re-asking "
                        f"{', '.join(losers)} without it")
        got = self.ask([x for x in numbers if x["id"] != ref], [meaning[k] for k in losers], label="assy_spec_slot",
                       note=f'{ref} ({n["text"]}) states {owner}, so it is not offered for the quantities below.')
        answer.update({k: got.get(k) for k in losers})
        return answer

    def update(self) -> Status:
        st = self.state
        st.stage = "parse_spec"
        numbers = extract_numbers(self.texts())
        st.numbers = numbers
        by_id = {n["id"]: n for n in numbers}
        slots = st.rules.spec_slots
        answer = self.ask(numbers, slots)
        bad = self.violations(answer, by_id, slots)
        if bad:
            st.notes.append("parse_spec: re-asking: " + "; ".join(b[0] for b in bad))
            answer = self.ask(numbers, slots, "; ".join(b[0] for b in bad))
            for ref, names in self.shared(answer, slots).items():
                st.notes.append(f"parse_spec: still violated after one re-ask: {' and '.join(names)} share {ref}")
                answer = self.resolve_shared(ref, names, numbers, by_id, slots, answer)
            for msg, names in self.violations(answer, by_id, slots):
                st.notes.append(f"parse_spec: still violated after one re-ask: {msg}")
                for k in names:
                    answer[k] = None
        missing = [s["name"] for s in slots if s["default_rule"] is None and not answer.get(s["name"])]
        if missing:
            return self.fail(f"no number in the text for {', '.join(missing)} (no default exists)")
        for s in slots:
            k, ref = s["name"], answer.get(s["name"])
            if ref:
                n = by_id[ref]
                st.spec[k] = n["value"]
                st.spec_provenance[k] = f'{n["source"]}:"{n["quote"]}"'
            else:
                v = st.rules.values[s["default_rule"]]
                st.spec[k] = v
                st.spec_provenance[k] = f"rules:{s['default_rule']}"
                st.assumptions.append(f"{k} = {v:g} {s['unit']} from rules:{s['default_rule']} "
                                      "(the text states no number for it)")
        lo, hi = "wall_min", "wall_max"
        if lo in st.spec and hi in st.spec and st.spec[lo] > st.spec[hi]:
            # a band with one end from the text and the other from a default: the default yields to the text
            fix = hi if st.spec_provenance[hi].startswith("rules:") else lo
            other = lo if fix == hi else hi
            st.spec[fix] = st.spec[other]
            st.spec_provenance[fix] = f"{st.spec_provenance[other]} (band end set equal: its default broke the band)"
            st.assumptions.append(f"{fix} = {st.spec[fix]:g} (its rules default fell outside the stated band)")
        if st.spec["board_depth"] > st.spec["board_width"]:   # frame rule: X along the board's longest edge
            st.spec["board_width"], st.spec["board_depth"] = st.spec["board_depth"], st.spec["board_width"]
            st.spec_provenance["board_width"], st.spec_provenance["board_depth"] = (
                st.spec_provenance["board_depth"], st.spec_provenance["board_width"])
            st.notes.append("parse_spec: board_width/board_depth swapped so X runs along the longest edge")
        self.logger.info(f"spec: {st.spec}")
        return Status.SUCCESS


def part_words(part: pt.Part) -> str:
    conns = part.data.get("connectors", [])
    extra = ""
    if conns:
        extra = "; cable connector: " + ", ".join(f"{c['name']} (takes a {c.get('mates', 'plug')})" for c in conns)
    return f"{part.names[0] if part.names else part.id} ({part.kind}{extra})"


class Contents(AssemblyStep):
    """Python proposes catalogue candidates per content kind; the LLM answers quantity (and whether the
    connector is exposed) per candidate; Python checks there is exactly one board."""

    def __init__(self, design, llm):
        super().__init__("Contents", design, llm)

    def candidates(self) -> List[str]:
        st = self.state
        text = self.design.base_request or self.design.request
        k = int(st.rules.values["lookup_k"])
        ranked = st.catalog.lookup(text, k=len(st.catalog.parts))
        out = []
        for kind in CONTENT_KINDS:
            out += [pid for pid, _ in ranked if st.catalog.get(pid).kind == kind][:k]
        return out

    def update(self) -> Status:
        st = self.state
        st.stage = "contents"
        cands = self.candidates()
        if not any(st.catalog.get(c).kind == "board" for c in cands):
            return self.fail("no catalogue board matches the request")
        qmax = int(st.rules.values["max_quantity"])
        props, allowed = {}, {}
        for pid in cands:
            part = st.catalog.get(pid)
            p = {"quantity": {"type": "integer", "enum": list(range(qmax + 1))}}
            allowed[f"{pid}.quantity"] = list(range(qmax + 1))
            if part.data.get("connectors"):
                p["exposed"] = {"type": "string", "enum": ["yes", "no"]}
                allowed[f"{pid}.exposed"] = ["yes", "no"]
            props[pid] = ca.obj_schema(p)
        lines = "\n".join(f"- {pid}: {part_words(st.catalog.get(pid))}" for pid in cands)
        prompt = (f"Request: {self.design.base_request or self.design.request}\n\n"
                  f"Catalogue parts that may be in the request:\n{lines}\n\n"
                  "For each part give how many the request puts inside the enclosure (0 if none), and for parts "
                  "with a cable connector whether that connector must be reachable from outside (exposed).")
        counts = tally(self.llm, prompt, ca.obj_schema(props), "assy_contents", allowed)
        items = []
        for pid in cands:
            q = majority(counts[f"{pid}.quantity"])
            if not q:
                continue
            part = st.catalog.get(pid)
            exposed = majority(counts.get(f"{pid}.exposed", Counter())) == "yes"
            items.append({"part": pid, "kind": part.kind, "quantity": int(q), "exposed": exposed,
                          "name": part.names[0] if part.names else pid})
        boards = [i for i in items if i["kind"] == "board"]
        if len(boards) != 1 or boards[0]["quantity"] != 1:
            return self.fail(f"exactly one board is needed, the answer has {sum(b['quantity'] for b in boards)}")
        board = st.catalog.get(boards[0]["part"])
        rp = board.request_params()
        if len(rp) < 2:
            return self.fail(f"board {board.id} does not take its size from the request")
        boards[0]["params"] = {rp[0]: st.spec["board_width"], rp[1]: st.spec["board_depth"]}
        kinds = Counter()
        for it in items:
            kinds[it["kind"]] += 1
            it["id"] = "board" if it["kind"] == "board" else f"{it['kind']}_{kinds[it['kind']]}"
            it.setdefault("params", {})
            part = st.catalog.get(it["part"])
            need = [p for p in part.request_params() if p not in it["params"]]
            if need:
                got = self.ask_params(it, part, need)
                if got is None:
                    return self.fail(f"{it['part']}: no number in the text for {', '.join(need)}")
                it["params"].update(got)
        st.contents = items
        st.items = [lay.Item(i["id"], i["part"], dict(i["params"]), i["quantity"], i["exposed"], None, i["name"])
                    for i in items if i["kind"] != "board"]
        self.logger.info(f"contents: {[(i['part'], i['quantity'], i['exposed']) for i in items]}")
        return Status.SUCCESS

    def ask_params(self, item, part: pt.Part, need: List[str]) -> Optional[Dict[str, float]]:
        st = self.state
        ids = [n["id"] for n in st.numbers] + ["none"]
        by_id = {n["id"]: n for n in st.numbers}
        schema = ca.obj_schema({p: {"type": "string", "enum": ids} for p in need})
        lines = "\n".join(f"- {p}: {part.params[p].get('source', p)}" for p in need)
        prompt = (f"Numbers found in the text:\n{number_lines(st.numbers)}\n\n"
                  f"The request includes a {item['name']}. For each of its sizes below give the id of the number "
                  f"that states it, or \"none\".\n{lines}")
        counts = tally(self.llm, prompt, schema, "assy_params", {p: ids for p in need})
        out = {}
        for p in need:
            ref = majority(counts[p])
            if ref in (None, "none"):
                return None
            out[p] = by_id[ref]["value"]
            st.spec_provenance[f"{item['id']}.{p}"] = f'{by_id[ref]["source"]}:"{by_id[ref]["quote"]}"'
        return out


class ChooseStack(AssemblyStep):
    """Per module with stack options: the LLM picks one option id; Python words each option."""

    def __init__(self, design, llm):
        super().__init__("ChooseStack", design, llm)

    def update(self) -> Status:
        st = self.state
        st.stage = "choose_stack"
        for it in st.items:
            part = st.catalog.get(it.part)
            options = [o for o in part.data.get("mount", {}).get("stack_options", []) if o in st.catalog]
            if not options:
                continue
            words = []
            for o in options:
                stack = st.catalog.instantiate(o)
                h = pt.lookup_datum(stack.datums, "STACK_TOP").at[2] - pt.lookup_datum(stack.datums, "STACK_BOTTOM").at[2]
                words.append(f"- {o}: {st.catalog.get(o).names[0]} (the {it.name} sits {h:g} mm above the board)")
            prompt = (f"Request: {self.design.base_request or self.design.request}\n\n"
                      f"How is the {it.name} mounted on the board? Options:\n" + "\n".join(words))
            counts = tally(self.llm, prompt, ca.obj_schema({"stack": {"type": "string", "enum": options}}),
                           "assy_stack", {"stack": options})
            pick = majority(counts["stack"])
            if pick is None:
                pick = options[0]
                st.assumptions.append(f"stack[{it.id}] = {pick}: no valid answer, first catalogue option used")
                choice(st, f"stack[{it.id}]", pick, "rule:first_option")
            else:
                choice(st, f"stack[{it.id}]", pick, "llm", votes=dict(counts["stack"]))
            it.stack = pick
        return Status.SUCCESS


def board_screw(catalog: pt.Catalog, board: pt.PartInstance, rules) -> Optional[pt.Part]:
    """The smallest-thread catalogue screw that passes the board hole with the minimum clearance."""
    hole = pt.lookup_datum(board.datums, "HOLE").diameter
    ok = []
    for pid in catalog.ids():
        part = catalog.get(pid)
        p = {k: v.get("default") for k, v in part.params.items()}
        if part.kind != "fastener" or p.get("pilot_diameter") is None or p.get("thread_diameter") is None:
            continue
        if p["thread_diameter"] + 2 * rules["screw_hole_clearance_min"] <= hole + 1e-9:
            ok.append((p["thread_diameter"], pid))
    return catalog.get(min(ok)[1]) if ok else None


def lid_screw(catalog: pt.Catalog, rules) -> Optional[pt.Part]:
    """The largest-thread catalogue screw (its boss OD = max(setpoint(min_boss_od), pilot + 2 x boss_wall_min))."""
    ok = []
    for pid in catalog.ids():
        part = catalog.get(pid)
        p = {k: v.get("default") for k, v in part.params.items()}
        if part.kind != "fastener" or any(p.get(k) is None for k in
                                          ("pilot_diameter", "thread_diameter", "clearance_diameter", "min_engagement")):
            continue
        ok.append((p["thread_diameter"], pid))
    return catalog.get(max(ok)[1]) if ok else None


def fastener_values(use: str, part: pt.Part) -> Dict[str, float]:
    inst = pt.instantiate(part)
    return {f"fastener.{use}.{k}": float(v) for k, v in inst.params.items()}


class ArrangeContents(AssemblyStep):
    """LLM: the board edge each exposed item faces (voted enum). Python: millimetre placement (layout.py).

    ConfirmArrangement (ARCHITECTURE.md 7.6): Python enumerates the edge assignments in the LLM's vote
    order, prunes the infeasible ones (placer.place), groups the feasible ones into board-symmetry classes
    and asks p_yes once per class. p_yes is a ranking signal, never an absolute gate: when the vote
    winner's class ranks top it is accepted; otherwise one voted A/B question decides between the two.
    The stage fails only when no feasible assignment exists, and then it lists every candidate."""

    def __init__(self, design, llm):
        super().__init__("ArrangeContents", design, llm)

    def request_text(self) -> str:
        return self.design.base_request or self.design.request

    def update(self) -> Status:
        st = self.state
        st.stage = "arrange_contents"
        board_item = next(i for i in st.contents if i["kind"] == "board")
        board_inst = st.catalog.instantiate(board_item["part"], board_item["params"])
        screw = board_screw(st.catalog, board_inst, st.rules.values)
        if screw is None:
            return self.fail("no catalogue screw passes the board's mounting holes")
        st.fasteners.update(fastener_values("board", screw))
        choice(st, "fastener[board]", screw.id, "rule:smallest_thread_through_board_hole")
        board = lay.Placed("board", board_item["part"], dict(board_item["params"]), 0.0, 0.0, 0.0, 0.0, "",
                           role="board", inst=board_inst)
        seat_d = st.fasteners["fastener.board.head_diameter"] + 2 * st.rules.values["driver_clearance"]
        placer = lay.Placer(st.catalog, board, st.rules.values, seat_d, st.spec["keepout_above"])
        exposed = [it for it in st.items if it.exposed and st.catalog.get(it.part).data.get("connectors")]
        edges = placer.edges
        sides = list(edges)
        voted = False
        if exposed:
            words = "\n".join(f"- {s}: {edges[s]['words']}" for s in sides)
            items = "\n".join(f"- {it.id}: {it.name} x{it.quantity} "
                              f"({st.catalog.get(it.part).data['connectors'][0]['name']} connector)" for it in exposed)
            prompt = (f"Request: {self.request_text()}\n\n"
                      f"The board edges:\n{words}\n\nWhich board edge does each part's connector face, so its "
                      f"cable plugs in through that end or side of the enclosure?\n{items}")
            schema = ca.obj_schema({it.id: {"type": "string", "enum": sides} for it in exposed})
            counts = tally(self.llm, prompt, schema, "assy_edge", {it.id: sides for it in exposed})
            first = {it.id: majority(counts[it.id]) or sides[0] for it in exposed}
            for it in exposed:
                if majority(counts[it.id]) is None:
                    st.assumptions.append(f"edge[{it.id}]: no valid answer, {sides[0]} tried first")
            voted = any(majority(counts[it.id]) is not None for it in exposed)
            order = self.assignments(exposed, sides, counts, first)
        else:
            counts, order = {}, [{}]
        cap = int(st.rules.values["arrange_rank_max"]) if exposed else 1
        cands, pruned, truncated = [], [], 0
        for k, assign in enumerate(order):
            if len(cands) >= cap:
                truncated = len(order) - k
                break
            try:
                result = placer.place(st.items, assign)
            except lay.LayoutError as e:
                pruned.append({"assignment": dict(assign), "outcome": "pruned", "kind": e.kind, "detail": e.detail})
                st.notes.append(f"arrange: {assign} infeasible ({e.kind}: {e.detail})")
                continue
            cands.append({"assignment": dict(assign), "layout": result, "words": lay.describe(result, st.items),
                          "votes": sum(counts[i].get(v, 0) for i, v in assign.items())})
        st.arrange = {"candidates": [], "classes": 0, "truncated": truncated, "decision": None}
        if truncated:
            st.notes.append(f"arrange: {truncated} lower-voted assignments were not evaluated "
                            f"(rules.arrange_rank_max = {cap})")
        if not cands:
            st.arrange["candidates"] = pruned
            return self.fail("no feasible arrangement: " + " | ".join(
                f"{c['assignment']}: {c['kind']}: {c['detail']}" for c in pruned))
        if not exposed:
            st.arrange.update(candidates=[self.record(cands[0], chosen=True)], decision="rule:no_exposed_connector")
            return self.accept(cands[0]["layout"], {}, placer, "rule:no_exposed_connector")
        notes: List[str] = []
        symmetries = lay.board_symmetries(board_inst, st.rules.values["measure_tol"], notes)
        st.notes += [f"arrange: {n}" for n in notes]
        classes = self.rank_candidates(cands, symmetries)
        pick, by, extra = self.decide(cands, classes, 0 if voted else None)
        chosen = cands[pick]
        score = classes[chosen["class"]]["p_yes"]
        ranked = sorted(range(len(classes)), key=lambda c: -classes[c]["p_yes"])
        others = [classes[c]["p_yes"] for c in ranked if c != chosen["class"]]
        margin = None if not others else score - others[0]
        confirmed = dict({"value": dict(chosen["assignment"]), "by": by, "p_yes": score,
                          "rank": ranked.index(chosen["class"]) + 1, "margin_to_next": margin}, **extra)
        for c in cands:
            st.history.append(dict({"stage": "confirm_arrangement"}, **self.record(c, chosen=c is chosen)))
        if score < EVEN_ODDS:
            nxt = f"{others[0]:.2f}" if others else "none"
            st.assumptions.append(f"arrangement accepted by rank: the controller's absolute confidence was low "
                                  f"(p_yes {score:.2f}; next class {nxt})")
        st.arrange.update(
            candidates=sorted([self.record(c, chosen=c is chosen) for c in cands], key=lambda r: -r["p_yes"]) + pruned,
            classes=len(classes), decision=by, symmetries=len(symmetries))
        return self.accept(chosen["layout"], chosen["assignment"], placer, "llm", counts=counts, confirmed=confirmed)

    @staticmethod
    def record(c: dict, chosen: bool) -> dict:
        return {"assignment": dict(c["assignment"]), "outcome": "scored", "class": c.get("class"),
                "words": c["words"], "votes": c["votes"], "p_yes": c.get("p_yes", 0.0), "asked": c.get("asked", False),
                "chosen": chosen}

    def rank_candidates(self, cands: List[dict], symmetries) -> List[dict]:
        """Group the feasible candidates (already in vote order) into board-symmetry classes; the first member
        of a class (most votes, then fewest changes from the vote, then side order) represents it. p_yes is
        asked once per representative, batched; every member carries its class's score."""
        keys: List[Tuple] = []
        classes: List[dict] = []
        for i, c in enumerate(cands):
            key = lay.canonical_class(c["assignment"], symmetries)
            if key not in keys:
                keys.append(key)
                classes.append({"key": key, "rep": i, "members": []})
            c["class"] = keys.index(key)
            classes[c["class"]]["members"].append(i)
        prompts = [f"Request: {self.request_text()}\n\n"
                   f"Proposed arrangement on the board: {cands[k['rep']]['words']}.\n"
                   "Does this arrangement match the request? Answer yes or no." for k in classes]
        ask = getattr(self.llm, "p_yes_many", None)
        scores = ask(prompts, "assy_confirm") if ask else [self.llm.p_yes(q, label="assy_confirm") for q in prompts]
        for k, p in zip(classes, scores):
            k["p_yes"] = float(p)
            cands[k["rep"]]["asked"] = True
            for i in k["members"]:
                cands[i]["p_yes"] = float(p)
        return classes

    def decide(self, cands: List[dict], classes: List[dict], voted: Optional[int]) -> Tuple[int, str, dict]:
        """(candidate index, by, extra). No absolute threshold: the vote and the ranking either agree, or one
        comparative A/B vote decides; with no valid edge vote the top class is taken."""
        top = max(range(len(classes)), key=lambda c: classes[c]["p_yes"])     # a tie goes to the more voted
        best = classes[top]["rep"]
        if voted is None:
            return best, "llm:rank", {}
        vc = cands[voted]["class"]
        if classes[vc]["p_yes"] >= classes[top]["p_yes"]:
            return voted, "llm:vote+rank", {}
        a, b = cands[voted]["words"], cands[best]["words"]
        prompt = (f"Request: {self.request_text()}\n\nTwo arrangements of the parts on the board:\n"
                  f"A: {a}.\nB: {b}.\n\nWhich arrangement matches the request?")
        counts = tally(self.llm, prompt, ca.obj_schema({"pick": {"type": "string", "enum": ["A", "B"]}}),
                       "assy_arrange_pick", {"pick": ["A", "B"]})
        votes = counts["pick"]
        pick = voted if votes.get("A", 0) > votes.get("B", 0) else best       # a tie goes to the higher ranked
        return pick, "llm:pick", {"pick_votes": {k: v for k, v in votes.items() if k is not None}}

    def assignments(self, exposed, sides, counts, first) -> List[Dict[str, str]]:
        """Every edge assignment, ordered by the LLM's votes, then by how few items differ from its answer."""
        out = []
        for combo in itertools.product(sides, repeat=len(exposed)):
            a = {it.id: s for it, s in zip(exposed, combo)}
            votes = sum(counts[it.id].get(a[it.id], 0) for it in exposed)
            diff = sum(a[it.id] != first[it.id] for it in exposed)
            out.append((-votes, diff, [sides.index(s) for s in combo], a))
        out.sort(key=lambda t: t[:3])
        return [t[3] for t in out]

    def accept(self, result: lay.Layout, assign, placer: lay.Placer, by: str, **extra) -> Status:
        st = self.state
        st.placed = result
        for k, v in assign.items():
            choice(st, f"edge[{k}]", v, by, **({"votes": dict(extra["counts"][k])} if "counts" in extra else {}))
        if extra.get("confirmed"):
            st.choices["arrangement_confirmed"] = extra["confirmed"]
        for note in result.notes:
            st.notes.append(f"arrange: {note}")
        st.frame = {"origin": "board min corner on its top surface", "x": "along the board's longest edge",
                    "z": "up", "edges": result.edges}
        st.layout = {p.node_id: p.to_json() for p in result.placed}
        st.layout_grid_residual = placer.grid_residual(result.placed)
        st.grid_report = placer.grid_report(result.placed)
        st.graph = fg.FeatureGraph()
        for p in result.placed:
            st.graph.add(fg.Node(p.node_id, "reference", "part", dict(p.params),
                                 fg.Pose(offset=(p.x, p.y, p.z), rot_z=p.rot_z), part=p.part,
                                 source=f"layout:{p.role}"))
        self.logger.info("arrangement: " + lay.describe(result, st.items))
        return Status.SUCCESS


def exposed_connectors(st: AssemblyState) -> List[Tuple[lay.Placed, dict]]:
    exposed = {it.id for it in st.items if it.exposed}
    return [(p, c) for p in st.placed.placed if p.role == "content" and p.item in exposed
            for c in p.inst.connectors[:1] if c.get("mates") in st.catalog]


class BuildEnvelopes(AssemblyStep):
    """V- volumes from the placed datums (parts.py generators); lengths from spec and rules only."""

    def __init__(self, design):
        super().__init__("BuildEnvelopes", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "build_envelopes"
        r, s = st.rules.values, st.spec
        board = st.placed.get("board")
        for p, c in exposed_connectors(st):
            world = {"mouth": lay.world_datum(p, c["mouth"]), "axis": lay.world_datum(p, c["axis"])}
            try:
                nodes = pt.plug_sweep(world, st.catalog.instantiate(c["mates"]), 0.0, r["plug_travel"],
                                      prefix=f"{p.node_id}_plug")
            except pt.PartError as e:
                return self.fail(str(e))
            for n in nodes:
                st.graph.add(n)
        for n in pt.board_keepout(board.inst, board.pose, s["keepout_above"], s["keepout_below"], prefix="board"):
            st.graph.add(n)
        holes = lay.world_datum(board, "HOLE")
        top, bottom = lay.world_datum(board, "TOP").at[2], lay.world_datum(board, "BOTTOM").at[2]
        seat_d = st.fasteners["fastener.board.head_diameter"] + 2 * r["driver_clearance"]
        for i in range(len(holes.at)):
            anchor = f"board.HOLE[{i}]"
            st.graph.add(pt.column(holes, i, seat_d, bottom - s["keepout_below"] - r["cut_overrun"],
                                   top + r["cut_overrun"], "seat", prefix="seat", anchor=anchor))
            st.graph.add(pt.column(holes, i, seat_d, top, top + s["keepout_above"], "hole_keepout", prefix="hole_ko",
                                   anchor=anchor))
        for p in st.placed.placed:
            stacks = [q for q in st.placed.placed if q.of == p.node_id]
            if stacks:
                for n in pt.content_envelope([(p.inst, p.pose)] + [(q.inst, q.pose) for q in stacks],
                                             f"{p.node_id}_envelope", role="module_envelope"):
                    st.graph.add(n)
        return Status.SUCCESS


# How each envelope role is consumed (ARCHITECTURE.md 7.7: no dead envelopes). The single place that says what
# an envelope means. Keys per row:
#   plan       "self": the envelope bounds the cavity in plan by its own diameter around its anchor datum;
#              an expression: a diameter added on the axes of the role named by `on` (never by referencing
#              this role's nodes, which may depend on the cavity); None: not a plan bound
#   z          the cavity bound this envelope sets in Z ("z0" / "z1"), documentary (derive_cavity writes them)
#   clearance  the clear_of clearance (a number or a "rules.<key>" / "spec.<key>" ref); None: no check
#   bodies     the bodies the clear_of check measures (None: all)
#   minus      a plan volume subtracted from the envelope before measuring
#   volume     the plan volume this role's nodes are unioned into instead of being checked (seats)
#   group      one check per Node.group over its primitives (plug sweeps: per exposed connector; module
#              envelopes: the module and its stack parts, ARCHITECTURE.md 7.8)
#   type       the check type: "clear_of" (default) or "inside" (a containment requirement)
#   check_id / text: the check's id and words ({id} = node id, {group} = group volume, {c} = clearance)
KEEP_OUTS: Dict[str, Dict[str, Any]] = {
    "module_envelope": {"plan": None, "z": None, "clearance": "rules.part_to_wall", "group": True, "type": "inside",
                        "check_id": "clear_{group}",
                        "text": "{group} (the module and its stack parts) lies inside the closed enclosure, at least "
                                "{c:g} mm from every printed surface and from the outside"},
    "keepout_top": {"plan": None, "z": "z1", "clearance": 0.0, "check_id": "clear_keepout_top",
                    "text": "nothing printed inside the component keep-out above the board"},
    "keepout_bottom": {"plan": None, "z": "z0", "clearance": 0.0, "minus": "seats", "check_id": "clear_keepout_bottom",
                       "text": "nothing printed inside the solder-side keep-out, except standoffs in the seat columns"},
    "hole_keepout": {"plan": "self", "z": None, "clearance": 0.0, "check_id": "clear_{id}",
                     "text": "nothing printed inside the screw-head column {id} (head + driver clearance, from the "
                             "board top to the component keep-out height)"},
    "driver": {"plan": "rules.driver_diameter", "on": "hole_keepout", "z": None, "clearance": 0.0, "bodies": ("base",),
               "check_id": "clear_{id}", "text": "the screwdriver column {id} is clear of the base (lid off)"},
    "seat": {"plan": None, "z": None, "clearance": None, "volume": "seats"},
    "plug_overmold": {"plan": None, "z": None, "clearance": "rules.plug_to_opening", "group": True,
                      "check_id": "clear_{group}", "text": "the {mates} plug in {part} at full mate and its "
                                                           "withdrawal path stay {c:g} mm from the enclosure"},
    "plug_shell": {"plan": None, "z": None, "clearance": "rules.plug_to_opening", "group": True,
                   "check_id": "clear_{group}", "text": "the {mates} plug in {part} at full mate and its "
                                                        "withdrawal path stay {c:g} mm from the enclosure"},
    "cavity": {"plan": None, "z": None, "clearance": None},
}


def keep_out(node: fg.Node) -> Dict[str, Any]:
    """The KEEP_OUTS row of an envelope node; an envelope role without a row is an error (a dead envelope)."""
    if node.role not in KEEP_OUTS:
        raise ValueError(f"{node.id}: envelope role {node.role!r} has no KEEP_OUTS row")
    return KEEP_OUTS[node.role]


def keepout_clearance(row: Mapping[str, Any], spec: Mapping[str, float], rules: Mapping[str, float]) -> float:
    c = row["clearance"]
    if isinstance(c, str):
        ns, _, key = c.partition(".")
        return float((rules if ns == "rules" else spec)[key])
    return float(c)


def plan_axes(st: AssemblyState) -> Dict[str, List[str]]:
    """Anchor datum ref -> the diameter expressions of every envelope that bounds the cavity in plan there."""
    axes: Dict[str, List[str]] = {}
    roles: Dict[str, List[str]] = {}
    for n in st.graph:
        if n.kind != "envelope" or keep_out(n).get("plan") != "self":
            continue
        if n.pose.at in ("frame.origin", "", None):
            raise ValueError(f"{n.id}: a plan keep-out must be anchored on a datum")
        axes.setdefault(n.pose.at, []).append(f"{n.id}.d")
        roles.setdefault(n.role, []).append(n.pose.at)
    for row in KEEP_OUTS.values():
        if row.get("plan") not in (None, "self"):
            for anchor in roles.get(row.get("on"), []):
                axes[anchor].append(row["plan"])
    return axes


def driver_columns(st: AssemblyState) -> List[fg.Node]:
    """V-DRIVER on every board hole axis: Ø rules.driver_diameter from the board top up to the base rim plus
    rules.driver_reach (lid off). Added after the base exists (its height reads base.split); the cavity never
    reads these nodes (KEEP_OUTS bounds it through rules.driver_diameter on the hole axes instead)."""
    r = st.rules.values
    board = st.placed.get("board")
    holes = lay.world_datum(board, "HOLE")
    top = lay.world_datum(board, "TOP").at[2]
    return [pt.column(holes, i, r["driver_diameter"], top, "base.split + rules.driver_reach", "driver",
                      prefix="driver", anchor=f"board.HOLE[{i}]") for i in range(len(holes.at))]


def feasible_archetypes(st: AssemblyState) -> List[Tuple[str, str]]:
    """(archetype, closure) pairs the derivation rules can build. The skeleton has one (ARCHITECTURE.md 4.3)."""
    return [("tray_lid", "screws")]


class ChooseArchetype(AssemblyStep):
    def __init__(self, design, llm):
        super().__init__("ChooseArchetype", design, llm)

    def update(self) -> Status:
        st = self.state
        st.stage = "choose_archetype"
        options = feasible_archetypes(st)
        if len(options) == 1:
            choice(st, "archetype", "+".join(options[0]), "rule:only_feasible")
            return Status.SUCCESS
        keys = ["+".join(o) for o in options]
        counts = tally(self.llm, f"Request: {self.design.base_request}\n\nWhich enclosure type fits best?\n"
                       + "\n".join(f"- {k}" for k in keys), ca.obj_schema({"archetype": {"type": "string", "enum": keys}}),
                       "assy_archetype", {"archetype": keys})
        choice(st, "archetype", majority(counts["archetype"]) or keys[0], "llm")
        return Status.SUCCESS


# ---------------------------------------------------------------------------
# DeriveFeatures: rules that turn contents + spec + rules into feature-graph nodes (expressions)
# ---------------------------------------------------------------------------


def _fold(fn: str, terms: Sequence[str]) -> str:
    terms = list(terms)
    return terms[0] if len(terms) == 1 else f"{fn}({', '.join(terms)})"


def derive_cavity(st: AssemblyState) -> fg.Node:
    """CavityFromContents = hull(references ∪ keep-outs) + clearances (ARCHITECTURE.md 4, 7.7).

    In plan: the AABB of every reference part grown by spec.board_clearance, and every plan keep-out
    (KEEP_OUTS "plan") around its anchor axis by its radius (no clearance: its limit is d >= 0); floor at
    the solder-side keep-out; top at the component keep-out (or the tallest part plus the headroom). Every
    one-sided bound carries rules.design_margin (setpoint inside the band; the checks keep the limits).
    Every size is an expression, so a spec or board change re-derives it (the size-leak fix)."""
    refs = [n.id for n in st.graph.references()]
    axes = plan_axes(st)
    m = "rules.design_margin"

    def bound(fn: str, axis: str, sign: str) -> str:
        terms = [f"{_fold(fn, [f'{r}.bbox.{fn}_{axis}' for r in refs])} {sign} spec.board_clearance {sign} {m}"]
        terms += [f"{a}.{axis} {sign} {_fold('max', ds)}/2 {sign} {m}" for a, ds in axes.items()]
        return _fold(fn, terms)

    p = {
        "x0": bound("min", "x", "-"), "x1": bound("max", "x", "+"),
        "y0": bound("min", "y", "-"), "y1": bound("max", "y", "+"),
        "z0": f"board.BOTTOM.z - spec.keepout_below - {m}",
        "z1": f"max(board.TOP.z + spec.keepout_above + {m}, "
              f"{_fold('max', [f'{r}.bbox.max_z' for r in refs])} + spec.headroom + {m})",
        "wall": "min(max(rules.wall_default, spec.wall_min), spec.wall_max)",
        "floor": "min(max(rules.floor_default, spec.wall_min), spec.wall_max)",
        "x": "x1 - x0", "y": "y1 - y0", "z": "z1 - z0", "cx": "(x0 + x1) / 2", "cy": "(y0 + y1) / 2",
    }
    return fg.Node("cavity", "envelope", "box", p, fg.Pose(offset=("cx", "cy", "z0")), role="cavity",
                   source="rule:cavity_from_contents")


SIDE_BOUND = {"-X": ("x0", 0, -1.0), "+X": ("x1", 0, 1.0), "-Y": ("y0", 1, -1.0), "+Y": ("y1", 1, 1.0)}


def wall_facing(direction: Sequence[float]) -> str:
    """The base wall whose outward normal is nearest to a direction."""
    best = max(SIDE_BOUND, key=lambda s: SIDE_BOUND[s][2] * float(direction[SIDE_BOUND[s][1]]))
    return best


def derive_port_cut(st: AssemblyState, p: lay.Placed, conn: dict, res: fg.Resolved) -> Tuple[fg.Node, str]:
    """ConnectorToCut: the wall the connector faces; the plug primitives crossing that wall's slab give
    the opening (their cross-section + 2 x (plug_to_opening + design_margin)); all-cylinder -> round cut,
    else a box."""
    axis = lay.world_datum(p, conn["axis"])
    mouth = lay.world_datum(p, conn["mouth"])
    u = np.asarray(axis.dir, dtype=float)
    side = wall_facing(u)
    bound, i, sign = SIDE_BOUND[side]
    cav = res.params["cavity"]
    if abs(u[i]) < 1e-9:
        raise ValueError(f"{p.node_id}: connector axis is parallel to wall {side}")
    s_in = (cav[bound] - mouth.at[i]) / u[i]
    s_out = s_in + cav["wall"] / abs(u[i])
    plugs = [n for n in st.graph if n.kind == "envelope" and n.id.startswith(f"{p.node_id}_plug_")]
    crossing = [n for n in plugs if res.params[n.id]["s0"] < s_out and res.params[n.id]["s1"] > s_in]
    if not crossing:
        raise ValueError(f"{p.node_id}: no plug primitive crosses wall {side}")
    w = f"{_fold('max', [f'{n.id}.cw' for n in crossing])} + 2*(rules.plug_to_opening + rules.design_margin)"
    h = f"{_fold('max', [f'{n.id}.ch' for n in crossing])} + 2*(rules.plug_to_opening + rules.design_margin)"
    m = f"{p.node_id}.{conn['mouth']}"
    xyz = "xyz"[i]
    cid = f"{p.node_id}_cut"
    if all(n.primitive == "cylinder" for n in crossing):
        start = f"cavity.{bound} {'-' if sign > 0 else '+'} rules.cut_overrun - {m}.{xyz}"
        offset = [0, 0, 0]
        offset[i] = start
        params = {"d": w, "h": "cavity.wall + 2*rules.cut_overrun", "top": f"{m}.z + d/2", "cw": w, "ch": w}
        pose = fg.Pose(at=m, offset=tuple(offset), axis=f"{p.node_id}.{conn['axis']}")
        prim = "cylinder"
    else:
        centre = f"cavity.{bound} {'+' if sign > 0 else '-'} cavity.wall/2 - {m}.{xyz}"
        offset = [0, 0, "-z/2"]
        offset[i] = centre
        params = {"x": "cavity.wall + 2*rules.cut_overrun", "y": w, "z": h, "top": f"{m}.z + z/2", "cw": w, "ch": h}
        pose = fg.Pose(at=m, offset=tuple(offset), rot_z=lay.angle_of(u))
        prim = "box"
    node = fg.Node(cid, "cut", prim, params, pose, body="base", role="port_cut",
                   source=f"rule:connector_to_cut({p.node_id}.{conn['name']})")
    node.wall = side
    node.crossing = [n.id for n in crossing]
    return node, side


def setpoint(limit_expr: str) -> str:
    """The derivation target for a one-sided minimum: limit + rules.design_margin (ARCHITECTURE.md 7.7, 7.9).

    Used at every one-sided-minimum derivation, so no derived value sits exactly on its limit (a rounding or
    tessellation change would flip it): one-sided clearances (cavity bounds, plug openings: written inline in
    derive_cavity / derive_port_cut), pilot depths (fastener min_engagement), standoff and boss outside
    diameters (fastener min_boss_od) and the lid lip's engagement (rules.lip_engagement). The checks keep the
    limits (pilot_engagement_*, boss_od_*, lip_engagement)."""
    expr = str(limit_expr).strip()
    if any(ch in expr for ch in " +-*/"):
        expr = f"({expr})"
    return f"{expr} + rules.design_margin"


def derive_features(st: AssemblyState) -> List[str]:
    """Tray + lid with screws (ARCHITECTURE.md 4.3, 7.4). Returns the port-cut node ids."""
    g = st.graph
    r = st.rules.values
    engagement = setpoint("rules.lip_engagement")
    g.add(derive_cavity(st))
    res = resolve(st)
    cuts = []
    for p, c in exposed_connectors(st):
        node, side = derive_port_cut(st, p, c, res)
        g.add(node)
        cuts.append(node)
    split_terms = [f"cavity.z1 + {engagement}"] + [f"{n.id}.top + rules.min_ligament" for n in cuts]
    g.add(fg.Node("base", "body", "shell", {
        "wall": "cavity.wall", "floor": "cavity.floor", "split": _fold("max", split_terms),
        "x": "cavity.x + 2*wall", "y": "cavity.y + 2*wall", "z": "split - cavity.z0 + floor", "open_top": 1},
        fg.Pose(offset=("cavity.cx", "cavity.cy", "cavity.z0 - floor")), role="tray",
        source="rule:tray_lid.base", color=fg.BODY_COLORS[0]))
    for n in driver_columns(st):
        g.add(n)
    holes = lay.world_datum(st.placed.get("board"), "HOLE")
    for i in range(len(holes.at)):
        hole = f"board.HOLE[{i}]"
        g.add(fg.Node(f"standoff_{i + 1}", "add", "cylinder", {
            "d": f"max(fastener.board.pilot_diameter + 2*rules.standoff_wall_min, "
                 f"{setpoint('fastener.board.min_boss_od')})",
            "h": "board.BOTTOM.z - cavity.z0 + base.floor", "top": "board.BOTTOM.z",
            "height": "board.BOTTOM.z - cavity.z0"},
            fg.Pose(at=hole, offset=(0, 0, f"cavity.z0 - base.floor - {hole}.z")), body="base", role="standoff",
            source="rule:mount_hole_to_standoff"))
        g.add(fg.Node(f"standoff_{i + 1}_pilot", "cut", "cylinder", {
            "d": "fastener.board.pilot_diameter", "h": "depth + rules.cut_overrun",
            "depth": setpoint("fastener.board.min_engagement")},
            fg.Pose(at=hole, offset=(0, 0, f"board.BOTTOM.z - depth - {hole}.z")),
            body="base", role="pilot", source="rule:mount_hole_to_standoff"))
    g.add(fg.Node("lid", "body", "box", {"x": "base.x", "y": "base.y", "z": "cavity.wall"},
                  fg.Pose(offset=("cavity.cx", "cavity.cy", "base.split")), role="lid_plate",
                  source="rule:tray_lid.lid", color=fg.BODY_COLORS[1]))
    g.add(fg.Node("lid_lip", "add", "shell", {
        "x": "cavity.x - 2*rules.sliding_fit", "y": "cavity.y - 2*rules.sliding_fit",
        "engagement": engagement, "z": "engagement + lid.z", "wall": "rules.lip_wall", "floor": 0, "open_top": 1,
        "fit": "rules.sliding_fit", "bottom": "base.split - engagement"},
        fg.Pose(offset=("cavity.cx", "cavity.cy", "base.split - engagement")), body="lid", role="lip",
        source="rule:lid_to_fastening.lip"))
    corners = [("x0", "y0", -1, -1), ("x1", "y0", 1, -1), ("x0", "y1", -1, 1), ("x1", "y1", 1, 1)]
    for k, (bx, by, sx, sy) in enumerate(corners, 1):
        boss = f"boss_{k}"
        cx = f"cavity.{bx} {'+' if sx < 0 else '-'} spec.board_clearance"
        cy = f"cavity.{by} {'+' if sy < 0 else '-'} spec.board_clearance"
        g.add(fg.Node(boss, "add", "cylinder", {
            "d": f"max({setpoint('fastener.lid.min_boss_od')}, fastener.lid.pilot_diameter + 2*rules.boss_wall_min)",
            "ax": f"{cx} {'-' if sx < 0 else '+'} {DIAGONAL!r}*(d/2 + spec.board_clearance)",
            "ay": f"{cy} {'-' if sy < 0 else '+'} {DIAGONAL!r}*(d/2 + spec.board_clearance)",
            "h": "base.split - cavity.z0 + base.floor"},
            fg.Pose(offset=("ax", "ay", "cavity.z0 - base.floor")), body="base", role="boss",
            source="rule:lid_to_fastening.corner_pilaster"))
        g.add(fg.Node(f"{boss}_pilot", "cut", "cylinder", {
            "d": "fastener.lid.pilot_diameter", "h": "depth + rules.cut_overrun",
            "depth": setpoint("fastener.lid.min_engagement")},
            fg.Pose(offset=(f"{boss}.ax", f"{boss}.ay", "base.split - depth")),
            body="base", role="pilot", source="rule:lid_to_fastening.corner_pilaster"))
        g.add(fg.Node(f"{boss}_pad", "add", "cylinder", {"d": f"{boss}.d", "h": "lid.z"},
                      fg.Pose(offset=(f"{boss}.ax", f"{boss}.ay", "base.split")), body="lid", role="pad",
                      source="rule:lid_to_fastening.corner_pilaster"))
        g.add(fg.Node(f"{boss}_lid_hole", "cut", "cylinder", {
            "d": "fastener.lid.clearance_diameter", "h": "lid.z + 2*rules.cut_overrun"},
            fg.Pose(offset=(f"{boss}.ax", f"{boss}.ay", "base.split - rules.cut_overrun")), body="lid",
            role="screw_hole", source="rule:lid_to_fastening.corner_pilaster"))
        g.add(fg.Node(f"{boss}_lip_notch", "cut", "cylinder", {
            "d": f"{boss}.d + 2*rules.sliding_fit", "h": "lid_lip.engagement + rules.cut_overrun"},
            fg.Pose(offset=(f"{boss}.ax", f"{boss}.ay", "base.split - lid_lip.engagement - rules.cut_overrun")),
            body="lid", role="lip_notch", source="rule:lid_to_fastening.corner_pilaster"))
    return [n.id for n in cuts]


def resolve(st: AssemblyState) -> fg.Resolved:
    return st.graph.resolve(st.spec, st.rules.values, catalog=st.catalog, fasteners=st.fasteners)


class DeriveFeatures(AssemblyStep):
    def __init__(self, design):
        super().__init__("DeriveFeatures", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "derive_features"
        screw = lid_screw(st.catalog, st.rules.values)
        if screw is None:
            return self.fail("no catalogue screw can hold the lid")
        st.fasteners.update(fastener_values("lid", screw))
        choice(st, "fastener[lid]", screw.id, "rule:largest_thread_screw")
        try:
            derive_features(st)
            st.resolved = resolve(st)
        except (ValueError, KeyError, fg.ExprError) as e:
            return self.fail(f"derivation failed: {e}")
        return Status.SUCCESS


# ---------------------------------------------------------------------------
# Build, Verify, RenderViews, WritePackage
# ---------------------------------------------------------------------------


def mesh_volume(tris) -> float:
    v = np.asarray(tris, dtype=float)
    if v.size == 0:
        return 0.0
    return float(np.einsum("ij,ij->i", v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() / 6.0)


def _colored_body(graph: fg.FeatureGraph, body: str, res: fg.Resolved, color: str, alpha: float = 1.0) -> str:
    """scad_body with the colour on the union only, so the faces the cuts leave keep OpenSCAD's cut colour
    in preview renders (an opening is then visible even in an orthographic view)."""
    text = fg.scad_body(graph, body, res)
    rgba = f'"{color}"' if alpha >= 1.0 else f'"{color}", {alpha:g}'
    return text.replace("\n  union() {", f"\n  color({rgba}) union() {{", 1)


def views_scad(graph: fg.FeatureGraph, res: fg.Resolved, ghosts: bool = False, alpha: float = 1.0) -> str:
    """Bodies in the closed pose (views/model_*); with ghosts=True the bodies are translucent and every
    reference part is drawn solid (views/ghost_*). Render-only files: model.scad is the deliverable."""
    out = [fg._comment("render file: printed bodies, closed pose" + ("; references drawn solid" if ghosts else ""))]
    if ghosts:  # opaque references first: the preview draws translucent bodies over them
        for k, ref in enumerate(graph.references()):
            color = fg.BODY_COLORS[(k + 2) % len(fg.BODY_COLORS)]
            out.append(f'color("{color}") {fg.scad_node(ref, res)} {fg._comment("reference " + ref.id)}')
    for i, body in enumerate(graph.bodies()):
        node = graph.nodes[body]
        out.append(_colored_body(graph, body, res, node.color or fg.BODY_COLORS[i % len(fg.BODY_COLORS)], alpha))
    return "\n".join(out) + "\n"


def open_scad(graph: fg.FeatureGraph, res: fg.Resolved, body: str = OPEN_BODY) -> str:
    """The lid-off evidence view (views/open_*, ARCHITECTURE.md 7.9): one body in its closed pose with the
    references as translucent ghosts (drawn after the body, never printed), every other body omitted, so the
    standoffs under the board, the bosses and the rim the lip seats on can be seen. Render-only."""
    out = [fg._comment(f"render file: {body} only (lid off), closed pose; references are translucent ghosts")]
    i = list(graph.bodies()).index(body)
    node = graph.nodes[body]
    out.append(_colored_body(graph, body, res, node.color or fg.BODY_COLORS[i % len(fg.BODY_COLORS)]))
    for ref in graph.references():
        out.append(f'color("{ref.color or fg.GHOST_COLOR}", {GHOST_ALPHA:g}) {fg.scad_node(ref, res)} '
                   f'{fg._comment("ghost " + ref.id)}')
    return "\n".join(out) + "\n"


class Build(AssemblyStep):
    """Resolve the graph, build a manifold solid per body, write the SCAD, compile each body with OpenSCAD;
    when OpenSCAD fails, times out or disagrees with the manifold, deliver the manifold mesh instead."""

    def __init__(self, design):
        super().__init__("Build", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "build"
        wd = self.design.workdir
        wd.mkdir(parents=True, exist_ok=True)
        res = st.resolved = resolve(st)
        g = st.graph
        st.solids = {b: fg.body_solid(g, b, res) for b in g.bodies()}
        for b in g.bodies():
            (wd / f"{b}.scad").write_text(fg.scad_body(g, b, res))
        (wd / "model.scad").write_text(fg.scad_model(g, res))
        (wd / "views.scad").write_text(views_scad(g, res))
        (wd / "ghost.scad").write_text(views_scad(g, res, ghosts=True, alpha=GHOST_ALPHA))
        if OPEN_BODY in g.bodies():
            (wd / "open.scad").write_text(open_scad(g, res))
        self.design.assembly = wd / "model.scad"
        for b, solid in st.solids.items():
            stl = wd / f"{b}.stl"
            reason = self.compile(b, solid, stl)
            if reason:
                fg.write_stl(solid, stl)
                st.stl_source[b] = "manifold"
                st.notes.append(f"build: {b}.stl written from the manifold ({reason})")
            else:
                st.stl_source[b] = "openscad"
        st.components = self.components(res)
        return Status.SUCCESS

    def compile(self, body: str, solid, stl: Path) -> str:
        r = self.state.rules.values
        try:
            result = ca.compile_scad(self.design.workdir / f"{body}.scad", stl)
        except Exception as e:  # OpenSCAD missing or crashed: the manifold mesh is delivered instead
            return f"OpenSCAD failed: {e}"
        if not result.ok:
            return "OpenSCAD: " + "; ".join(result.problems)[:200]
        vol, man = abs(mesh_volume(result.tris)), float(solid.volume())
        lo, hi = result.bbox
        b = solid.bounding_box()
        dbox = max(abs(a - c) for a, c in zip(list(lo) + list(hi), list(b)))
        if abs(vol - man) > r["parity_volume_rel"] * max(man, 1e-9) or dbox > r["parity_bbox"]:
            return f"parity: OpenSCAD volume {vol:.2f} vs manifold {man:.2f}, bbox differs by {dbox:.3f} mm"
        return ""

    def components(self, res: fg.Resolved) -> List[dict]:
        """Generated from the graph and measured solids, never from LLM text."""
        out = []
        for n in self.state.graph:
            if n.kind not in fg.BUILD_KINDS:
                continue
            bb = fg.solid(n, res).bounding_box()
            out.append({"id": n.id, "kind": n.kind, "role": n.role, "body": n.body or n.id, "primitive": n.primitive,
                        "params": {k: round(v, 4) for k, v in res.params[n.id].items()},
                        "bbox": [[round(v, 4) for v in bb[:3]], [round(v, 4) for v in bb[3:]]], "source": n.source})
        return out


def add_keepout_checks(st: AssemblyState, plan: ac.Plan, envelopes: Sequence[fg.Node]) -> None:
    """One check per checked envelope (per Node.group for grouped rows: plug sweeps, module envelopes), generated
    from KEEP_OUTS, in the table's role order. The check ids are the iteration 002 ids (checks.json stays comparable)."""
    r, s, res = st.rules.values, st.spec, st.resolved
    plugs = {f"{p.node_id}_plug": (p, c) for p, c in exposed_connectors(st)}
    done = set()
    for role, row in KEEP_OUTS.items():
        if row.get("clearance") is None:
            continue
        c = keepout_clearance(row, s, r)
        for n in envelopes:
            if n.role != role:
                continue
            words = {"id": n.id, "c": c}
            vol = n.id
            if row.get("group"):
                vol = n.group
                if not vol:
                    raise ValueError(f"{n.id}: envelope role {role!r} is grouped but the node has no group")
                if vol in done:
                    continue
                members = [m for m in envelopes if m.group == vol]
                plan.volumes[vol] = ac.union([fg.solid(m, res) for m in members])
                plan.sources[vol] = [m.id for m in members]
                words["group"] = vol
                if vol in plugs:
                    part, conn = plugs[vol]
                    words.update(mates=conn["mates"], part=part.node_id)
                elif "{mates}" in row["text"]:
                    raise ValueError(f"{n.id}: plug sweep of no exposed connector")
            else:
                plan.volumes[vol] = fg.solid(n, res)
                plan.sources[vol] = [n.id]
            done.add(vol)
            args = {"volume": vol, "clearance": c}
            if row.get("minus"):
                args["minus"] = row["minus"]
            if row.get("bodies"):
                args["bodies"] = list(row["bodies"])
            plan.add(row["check_id"].format(**words), row.get("type", "clear_of"), row["text"].format(**words), **args)


def grow_exemptions(st: AssemblyState, plan: ac.Plan) -> None:
    """ARCHITECTURE.md 7.8: a contact exemption (`minus`) on a clear_of / inside check with clearance c > 0 is the
    exempt nodes grown by c (volume "<minus>@<c>"), so a body touching legally inside the exemption is measured
    against the next real surface, not against the exemption's rim. With c = 0 the exemption is unchanged."""
    g, res = st.graph, st.resolved
    for sp in plan.specs:
        a = sp["args"]
        if sp["type"] not in ("clear_of", "inside") or not a.get("minus") or a["clearance"] <= 0:
            continue
        m, c = a["minus"], float(a["clearance"])
        name = f"{m}@{c:g}"
        if name not in plan.volumes:
            plan.volumes[name] = ac.union([fg.grown_solid(g.nodes[i], res, c) for i in plan.sources[m]])
            plan.sources[name] = list(plan.sources[m])
        a["minus"] = name
        a["minus_grown_by"] = c


def grown_words(st: AssemblyState, plan: ac.Plan, minus: str, c: float) -> str:
    """'grown by the clearance (Ø d)' from the resolved exempt nodes (never a literal)."""
    ds = sorted({round(st.resolved.params[i]["d"] + 2 * c, 6) for i in plan.sources.get(minus, [])
                 if "d" in st.resolved.params[i]})
    return "grown by the clearance" + (f" (Ø {'/'.join(f'{d:g}' for d in ds)})" if ds else "")


def add_part_maps(st: AssemblyState, plan: ac.Plan) -> None:
    """Plan.parts (every check volume with two or more sources: its member solids, so reports are decomposable)
    and Plan.labels (node id -> catalogue id, or the role when the node is no catalogue part)."""
    g, res = st.graph, st.resolved
    for sp in plan.specs:
        if sp["type"] not in ("clear_of", "inside"):
            continue
        for key in ("volume", "minus"):
            for i in plan.sources.get(sp["args"].get(key), []):
                n = g.nodes[i]
                plan.labels[i] = n.part or n.role or n.id
        vol = sp["args"]["volume"]
        ids = plan.sources.get(vol, [])
        if len(ids) >= 2 and vol not in plan.parts:
            plan.parts[vol] = {i: fg.solid(g.nodes[i], res) for i in ids}
    plan.references = {n.id: n.part or n.role for n in g.references()}


GRID_CONFLICT_KINDS = ("pin_pattern", "flush_to_edge", "no_pin_data")   # a question for Robin, not for agent code


def grid_conflict_text(st: AssemblyState, nid: str, row: Mapping[str, Any], limit: float) -> str:
    """Python's words for one typed grid failure (ARCHITECTURE.md 7.9)."""
    kind = row["kind"]
    if kind == "pin_pattern":
        return (f"{nid}: the part's own pin pattern cannot meet the board grid at any position (best "
                f"{row['best_any']:.3f} mm > {limit:g}); a catalogue or requirement question")
    if kind == "flush_to_edge":
        p = st.placed.get(nid)
        mouth = p.inst.connectors[0]["mouth"] if p.inst.connectors else "position"
        return (f"fixing it moves {nid}.{mouth} off its flush edge position by {abs(row['normal_needed']):.3f} mm "
                f"(rule flush_to_edge, ARCHITECTURE.md 7.5)")
    if kind == "no_pin_data":
        return f"{nid}: the catalogue part has no pin data, so its grid conformance cannot be verified (a catalogue question)"
    return (f"{nid}: the grid snap left {row['residual']:.3f} mm although {row['best_free']:.3f} mm is reachable along "
            "its edge (a placement bug)")


def grid_check(st: AssemblyState, plan: ac.Plan) -> None:
    """grid_conformance (ARCHITECTURE.md 7.7, 7.9): the worst pin-to-grid residual against rules.grid_residual_max;
    parts with a connector but no pin data fail it. Every failing part carries a typed kind from the grid sensor
    (layout.Placer.grid_report): pin_pattern (no position can pass), flush_to_edge (it passes somewhere, but the
    move off the flush edge position is forbidden, 7.5), no_pin_data, or tangential (a placement bug). The first
    three are typed requirement / catalogue conflicts, never hidden ones."""
    rep = st.grid_report
    if not rep or not rep.get("grid"):
        return
    r = st.rules.values
    limit, tol = r["grid_residual_max"], r["measure_tol"]
    conflicts, kinds = [], {}
    for nid, row in rep["parts"].items():
        kind = row.get("kind") or lay.grid_kind(row["residual"], row.get("best_any", row["residual"]),
                                                row.get("best_free", row["residual"]), limit, tol)
        row = dict(row, kind=kind)
        kinds[nid] = kind
        if kind not in GRID_CONFLICT_KINDS:
            continue
        conflicts.append({"part": nid, "kind": kind, "competing_rule": kind, "residual": round(row["residual"], 6),
                          "best_any": round(row["best_any"], 6), "best_free": round(row["best_free"], 6),
                          "normal_needed": None if row.get("normal_needed") is None else round(row["normal_needed"], 6),
                          "normal_fix": None if row.get("normal_fix") is None else round(row["normal_fix"], 6),
                          "text": grid_conflict_text(st, nid, row, limit)})
    for nid in rep["no_pin_data"]:
        kinds[nid] = "no_pin_data"
        conflicts.append({"part": nid, "kind": "no_pin_data", "competing_rule": "no_pin_data", "residual": None,
                          "best_any": None, "best_free": None, "normal_needed": None, "normal_fix": None,
                          "text": grid_conflict_text(st, nid, {"kind": "no_pin_data"}, limit)})
    evidence = {"parts": rep["parts"], "kinds": kinds, "soft": rep.get("soft", False)}
    if conflicts:
        worst = max(conflicts, key=lambda c: -1.0 if c["residual"] is None else c["residual"])
        evidence.update(conflict=worst["text"], competing_rule=worst["competing_rule"], conflicts=conflicts)
    if rep.get("soft"):
        evidence["soft"] = True
    plan.add("grid_conformance", "grid_conformance", f"every part pin lies within {limit:g} mm of the board grid "
             "(parts with a connector need pin data)", value=float(rep["max"]), limit=limit,
             no_pin_data=list(rep["no_pin_data"]), evidence=evidence)


def add_minimum_checks(st: AssemblyState, plan: ac.Plan) -> None:
    """ARCHITECTURE.md 7.9: every one-sided minimum the derivation sets with `setpoint` has its own check at the
    limit, on the resolved graph: pilot depth >= the fastener's min_engagement (standoffs: the board screw;
    bosses: the lid screw), outside diameter >= its min_boss_od, and the lid lip's engagement >= rules.lip_engagement."""
    r, res, g, f = st.rules.values, st.resolved, st.graph, st.fasteners
    for n in g:
        use = {"standoff": "board", "boss": "lid"}.get(n.role)
        if use is None:
            continue
        pilot = res.params[f"{n.id}_pilot"]["depth"]
        need = f[f"fastener.{use}.min_engagement"]
        plan.add(f"pilot_engagement_{n.id}", "pilot_engagement", f"the pilot in {n.id} is at least {need:g} mm deep "
                 f"(the {use} screw's minimum engagement)", value=pilot, limit=need,
                 detail=f"pilot depth {pilot:.3f} vs min_engagement {need:g}")
        od, need_od = res.params[n.id]["d"], f[f"fastener.{use}.min_boss_od"]
        plan.add(f"boss_od_{n.id}", "boss_od", f"{n.id} is at least {need_od:g} mm across (the {use} screw's minimum "
                 "boss diameter)", value=od, limit=need_od, detail=f"outside diameter {od:.3f} vs min_boss_od {need_od:g}")
    if "lid_lip" in g.nodes:
        eng = res.params["base"]["split"] - res.params["lid_lip"]["bottom"]
        plan.add("lip_engagement", "lip_engagement", f"the lid lip reaches at least {r['lip_engagement']:g} mm below "
                 "the split plane", value=eng, limit=r["lip_engagement"],
                 detail=f"lip engagement {eng:.3f} vs {r['lip_engagement']:g}")


def build_plan(st: AssemblyState) -> ac.Plan:
    """The rule-derived check set (iteration 002 subset) and the volumes it measures against."""
    r, s, res, g = st.rules.values, st.spec, st.resolved, st.graph
    plan = ac.Plan(tol=ac.Tol.from_rules(r), seg=res.segments())
    vols = plan.volumes
    refs = g.references()
    ref_solids = {n.id: fg.solid(n, res) for n in refs}
    envelopes = [n for n in g if n.kind == "envelope"]
    for n in envelopes:                      # role-only rows (seats) become named plan volumes
        row = keep_out(n)
        if row.get("volume"):
            plan.sources.setdefault(row["volume"], []).append(n.id)
    for name, ids in plan.sources.items():
        vols[name] = ac.union([fg.solid(g.nodes[i], res) for i in ids])
    vols.setdefault("seats", ac.union([]))
    plan.sources.setdefault("seats", [])
    board_id = st.placed.get("board").node_id
    contents = [i for i in ref_solids if i != board_id]
    vols["board"] = ref_solids[board_id]
    vols["contents"] = ac.union([ref_solids[i] for i in contents])
    plan.sources["board"] = [board_id]
    plan.sources["contents"] = contents
    bc = s["board_clearance"]
    seat_words = grown_words(st, plan, "seats", bc)
    plan.add("separable", "separable", "base and lid are each one shell and overlap by at most "
             f"{r['overlap_max']:g} mm3 when closed", bodies=list(BODIES), overlap_max=r["overlap_max"])
    plan.add("inside_board", "inside", f"the board (minus the seat columns {seat_words}) lies inside the closed "
             f"enclosure with {bc:g} mm clearance", volume="board", minus="seats", clearance=bc)
    plan.add("inside_contents", "inside", "every part the board carries lies inside the closed enclosure, at least "
             f"{r['part_to_wall']:g} mm from every printed surface and from the outside", volume="contents",
             clearance=r["part_to_wall"])
    plan.add("clear_board", "clear_of", f"no printed surface within {bc:g} mm of the board, "
             f"except the standoff tops in the seat columns {seat_words}", volume="board", minus="seats", clearance=bc)
    add_keepout_checks(st, plan, envelopes)
    base, cav = res.params["base"], res.params["cavity"]
    lid = res.params["lid"]
    # Wall slabs (rubric.md 3.4, ARCHITECTURE.md 7.9): between the wall's inner and outer face planes, over the
    # wall's full tangential extent (the base's outside, corners included) and full Z extent (base bottom to lid
    # top, closed). Only the two face planes are inset by measure_tol, so coplanar faces leave no skin. Regions are
    # classified through (they reach both face planes) or blind (with the cut nodes they meet); counts use through.
    eps = r["measure_tol"]
    z_lo, z_hi = cav["z0"] - base["floor"], base["split"] + lid["z"]
    cuts = [n for n in g if n.role == "port_cut"]
    all_cuts = [n for n in g if n.kind == "cut" and n.role in APERTURE_CUT_ROLES]
    for side, (bound, i, sign) in SIDE_BOUND.items():
        inner = cav[bound]
        outer = inner + sign * base["wall"]
        t = 1 - i
        tb = ("x0", "x1") if t == 0 else ("y0", "y1")
        t_lo, t_hi = cav[tb[0]] - base["wall"], cav[tb[1]] + base["wall"]
        lo, hi = [0.0, 0.0, z_lo], [0.0, 0.0, z_hi]
        lo[i], hi[i] = min(inner, outer) + eps, max(inner, outer) - eps
        lo[t], hi[t] = t_lo, t_hi
        slab = f"slab_{side}"
        vols[slab] = ac.m3d.Manifold.cube([hi[k] - lo[k] for k in range(3)]).translate(lo)
        near = []
        for n in all_cuts:                    # the cuts that reach into this slab: blind regions name them
            if n.id not in vols:
                vols[n.id] = fg.solid(n, res)
                plan.sources[n.id] = [n.id]
            if not (vols[n.id] ^ vols[slab]).is_empty():
                near.append(n.id)
        on_wall = [n for n in cuts if n.wall == side]
        plan.add(f"apertures_{side}", "aperture_count", f"wall {side} has exactly {len(on_wall)} through opening(s) "
                 "(blind regions in the wall slab are listed, not counted)", slab=slab, n=len(on_wall), wall=side,
                 normal_axis=i, cuts=near)
        for n in on_wall:
            pose = res.poses[n.id][:3, 3]
            point = [float(v) for v in pose]
            point[i] = (inner + outer) / 2
            if n.primitive == "box":
                point[2] = float(pose[2] + res.params[n.id]["z"] / 2)
            crossing = n.crossing
            env_w = max(res.params[c]["cw"] for c in crossing)
            env_h = max(res.params[c]["ch"] for c in crossing)
            plan.add(f"oversize_{n.id}", "aperture_oversize", f"the opening of {n.id} is at most "
                     f"{s['opening_oversize_max']:g} mm bigger than its plug per side", slab=slab, wall=side,
                     normal_axis=i, point=point, env_w=env_w, env_h=env_h, max=s["opening_oversize_max"])
    board = st.placed.get("board")
    holes = lay.world_datum(board, "HOLE")
    bottom = lay.world_datum(board, "BOTTOM").at[2]
    standoffs = [n for n in g if n.role == "standoff"]
    probe = min(res.params[f"{n.id}_pilot"]["depth"] for n in standoffs) / 2
    search_d = min((res.params[f"{n.id}_pilot"]["d"] + res.params[n.id]["d"]) / 2 for n in standoffs)
    plan.add("seated", "seated", f"the board rests on the standoff tops (gap <= {r['seat_gap_max']:g} mm) with every "
             f"hole on a pilot axis (offset <= {r['seat_axis_residual_max']:g} mm)", body="base",
             holes=[[float(v) for v in p[:2]] for p in holes.at], board_bottom=float(bottom),
             search_d=float(search_d), z_lo=float(cav["z0"]), z_hi=float(bottom + r["cut_overrun"]), probe_depth=float(probe),
             gap_max=r["seat_gap_max"], residual_max=r["seat_axis_residual_max"])
    plan.add("bbox", "bbox_within", f"closed outside size within {s['max_x']:g} x {s['max_y']:g} x {s['max_z']:g} mm",
             max=[s["max_x"], s["max_y"], s["max_z"]], x_longest=s["max_x"] > s["max_y"])
    for n in cuts:
        plan.add(f"below_split_{n.id}", "port_below_split", f"{n.id} top plus the minimum ligament stays below the "
                 "split plane", value=res.params[n.id]["top"] + r["min_ligament"], limit=base["split"],
                 detail=f"{n.id} top {res.params[n.id]['top']:.3f} + ligament {r['min_ligament']:g} vs split "
                        f"{base['split']:.3f}")
    for n in g:
        if n.role == "standoff":
            pilot = res.params[f"{n.id}_pilot"]
            plan.add(f"pilot_depth_{n.id}", "pilot_depth", f"the pilot in {n.id} leaves at least "
                     f"{r['min_feature']:g} mm of floor under it", value=pilot["depth"],
                     limit=res.params[n.id]["height"] + base["floor"] - r["min_feature"],
                     detail=f"pilot depth {pilot['depth']:g} vs standoff {res.params[n.id]['height']:.3f} + floor "
                            f"{base['floor']:.3f} - {r['min_feature']:g}")
    add_minimum_checks(st, plan)
    grid_check(st, plan)
    grow_exemptions(st, plan)
    add_part_maps(st, plan)
    return plan


class Verify(AssemblyStep):
    """Rule-derived checks on the manifold solids, then on the delivered STLs. Never fails the tree:
    the package is always written and finalize() reports the outcome."""

    def __init__(self, design):
        super().__init__("Verify", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "verify"
        st.plan = build_plan(st)
        st.checks = st.plan.checks()
        st.results_manifold = ac.run_plan(st.plan, st.solids)
        st.self_report = ac.measure_package(self.design.workdir, st.plan, list(st.solids))
        st.results = [cc.CheckResult(**r) for r in st.self_report["results"]]
        if st.self_report["errors"]:
            st.notes.append("verify: " + "; ".join(st.self_report["errors"]))
        failed = [r.check_id for r in st.results if not r.passed]
        self.logger.info(f"verify: {len(st.results) - len(failed)}/{len(st.results)} checks pass on the delivered STLs"
                         + (f"; failing: {', '.join(failed)}" if failed else ""))
        return Status.SUCCESS


class RenderViews(AssemblyStep):
    def __init__(self, design):
        super().__init__("RenderViews", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "render_views"
        views = self.design.workdir / "views"
        open_views = {k: ca.VIEWS[k] for k in OPEN_VIEWS if k in ca.VIEWS}
        for scad, stem, cams in (("views.scad", "model", ca.VIEWS), ("ghost.scad", "ghost", ca.VIEWS),
                                 ("open.scad", "open", open_views)):
            if not (self.design.workdir / scad).is_file():
                continue
            try:
                done, failures = ca.render_openscad(self.design.workdir / scad, cams, views, stem=stem)
            except Exception as e:  # a render failure is a note, never a crash
                done, failures = {}, [str(e)]
            if stem == "model":
                self.design.views = done
            for f in failures:
                st.notes.append(f"render {stem}: {f}")
        return Status.SUCCESS


class WritePackage(AssemblyStep):
    def __init__(self, design):
        super().__init__("WritePackage", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "write_package"
        wd = self.design.workdir
        refs = [{"id": nid, **v} for nid, v in st.layout.items()]
        ac.write_json(wd / "layout.json", {
            "schema": 1, "frame": st.frame, "units": "mm", "references": refs,
            "bodies": {b: dict(st.rules.print_orientation.get(b) or st.rules.print_orientation.get("default", {}))
                       for b in st.graph.bodies()},
            "spec": st.spec, "grid_residual": getattr(st, "layout_grid_residual", None)})
        ac.write_json(wd / "self_report.json", st.self_report)
        ac.write_json(wd / "feature_graph.json", st.graph.to_json())
        ac.write_json(wd / "checks.json", [c.to_dict() for c in st.checks])
        l1 = list(self.design.l1) + [{"id": ac.L1_RULES, "text": "rule-derived checks (generic consequences of the "
                                      "contents, the spec and printing)", "method": "analysis"}]
        rows = cc.verification_matrix(l1, st.checks, st.results)
        ac.write_json(wd / "verification_matrix.json", rows)
        (wd / "verification_matrix.md").write_text(
            "# Verification matrix (delivered STLs)\n\n```\n" + cc.matrix_text(rows) + "\n```\n\n"
            + "\n".join(f"- {'PASS' if r.passed else 'FAIL'} {r.check_id}: {r.evidence.get('detail', '')}"
                        for r in st.results) + "\n")
        try:  # ExportModel: the delivered bodies (closed pose) as one 3MF, one object per body
            self.design.export_path = write_3mf(wd / "model.3mf", {b: ac.load_mesh(wd / f"{b}.stl")
                                                                   for b in st.graph.bodies()})
        except Exception as e:  # a failed export is a note, never a crash
            st.notes.append(f"export: model.3mf not written ({e})")
            self.design.export_path = wd / "base.stl"
        st.files = sorted(str(p.relative_to(wd)) for p in wd.rglob("*") if p.is_file() and "llm" not in p.parts)
        return Status.SUCCESS


THREE_MF_TYPES = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/'
                  'package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-'
                  'package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.'
                  '3dmanufacturing-3dmodel+xml"/></Types>')
THREE_MF_RELS = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/'
                 'package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.'
                 'microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')


def write_3mf(path: Path, bodies: Dict[str, Any]) -> Path:
    """A minimal 3MF core package (millimetres): one mesh object per body, all placed in the build."""
    import zipfile
    objs, items = [], []
    for k, (name, m) in enumerate(bodies.items(), 1):
        mesh = m.to_mesh()
        v = np.asarray(mesh.vert_properties, dtype=float)[:, :3]
        t = np.asarray(mesh.tri_verts, dtype=np.int64)
        verts = "".join(f'<vertex x="{a:.6f}" y="{b:.6f}" z="{c:.6f}"/>' for a, b, c in v)
        tris = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t)
        objs.append(f'<object id="{k}" name="{name}" type="model"><mesh><vertices>{verts}</vertices>'
                    f'<triangles>{tris}</triangles></mesh></object>')
        items.append(f'<item objectid="{k}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(objs)}</resources><build>{"".join(items)}</build></model>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", THREE_MF_TYPES)
        z.writestr("_rels/.rels", THREE_MF_RELS)
        z.writestr("3D/3dmodel.model", model)
    return Path(path)


def build_assembly_tree(design, llm, parts_dir, rules_path, with_models: bool = False,
                        auto_approve: bool = False) -> py_trees.behaviour.Behaviour:
    """The assembly-mode tree. `llm` is the controller for the discrete choices."""
    if design.assy is None:
        design.assy = AssemblyState(parts_dir=str(parts_dir), rules_path=str(rules_path),
                                    with_models=bool(with_models))
    return py_trees.composites.Sequence("cad_assembly", memory=True, children=[
        LoadCatalog(design), LoadRules(design), ParseSpec(design, llm), Contents(design, llm),
        ChooseStack(design, llm), ArrangeContents(design, llm), BuildEnvelopes(design),
        ChooseArchetype(design, llm), DeriveFeatures(design), Build(design), Verify(design),
        RenderViews(design), WritePackage(design)])


def conflict_entries(results: Sequence[cc.CheckResult]) -> List[dict]:
    """assembly.conflicts: one typed entry per conflicting part of a failing check (evidence.conflicts), or one per
    check when it names a single conflict. `kind` says what kind of question it is (ARCHITECTURE.md 7.9)."""
    out = []
    for r in results:
        ev = r.evidence
        if r.passed or not ev.get("conflict"):
            continue
        rows = ev.get("conflicts") or [{"text": ev["conflict"], "kind": ev.get("competing_rule"),
                                        "competing_rule": ev.get("competing_rule")}]
        for row in rows:
            out.append({"check_id": r.check_id, "part": row.get("part"), "kind": row.get("kind"),
                        "competing_rule": row.get("competing_rule"), "conflict": row["text"],
                        "value": row.get("residual", ev.get("value")), "limit": ev.get("limit"), "details": row})
    return out


def finalize(design, llm) -> dict:
    """verified exactly when every check passes on the delivered STLs; otherwise unsatisfied."""
    st = design.assy
    failed = [r.check_id for r in st.results if not r.passed]
    outcome = "verified" if st.results and not failed else "unsatisfied"
    st.conflicts = conflict_entries(st.results)
    for c in st.conflicts:
        print(f"assembly: requirement conflict in {c['check_id']}: {c['conflict']}", flush=True)
    st.stage = "done"
    print(f"assembly: {outcome}; {len(st.results) - len(failed)}/{len(st.results)} checks pass on the delivered STLs"
          + (f"; failing: {', '.join(failed)}" if failed else ""), flush=True)
    return {"outcome": outcome, "failed": failed, "checks": len(st.results), "conflicts": list(st.conflicts)}
