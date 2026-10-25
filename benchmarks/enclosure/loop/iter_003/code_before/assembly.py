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
    │                      ConfirmArrangement: Python words the result, LLM p_yes, next feasible assignment on "no"
    ├── BuildEnvelopes     plug sweeps, keep-outs, seat / hole columns, module envelopes (parts.py, from datums)
    ├── ChooseArchetype    feasible archetypes; one feasible -> recorded as a rule choice (no LLM call)
    ├── DeriveFeatures     cavity from contents, base shell, standoffs + pilots, port cuts, lid + lip,
    │                      corner pilaster bosses + lid holes: feature-graph nodes whose params are expressions
    ├── Build              resolve, manifold solid per body, OpenSCAD compile per body (manifold fallback, parity)
    ├── Verify             rule-derived checks on the manifold solids and on the delivered STLs (never fails)
    ├── RenderViews        views/model_* (bodies), views/ghost_* (bodies + references)
    └── WritePackage       base/lid .stl/.scad, model.scad, layout.json, self_report.json, feature_graph.json,
                           checks.json, verification_matrix.{md,json}, model.3mf
    finalize(): verified (every check passes on the delivered STLs) | unsatisfied

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
from typing import Any, Dict, List, Optional, Sequence, Tuple

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

    def prompt(self, numbers, slots, violation: str = "") -> str:
        lines = "\n".join(f'- {s["name"]}: {s["meaning"]} ({s["unit"]})' for s in slots)
        again = (f"\nYour previous answer broke these rules: {violation}. Answer again and fix that.\n"
                 if violation else "")
        return (f"An enclosure is being designed from this request and its requirements.\n\n"
                f"Numbers found in the text (each occurrence has its own id):\n{number_lines(numbers)}\n\n"
                f"For each quantity below, give the id of the number in the text that states it, or \"none\" "
                f"if the text does not state it. Never use a number for something it does not describe.\n"
                f"{lines}\n{again}")

    def ask(self, numbers, slots, violation="") -> Dict[str, Optional[str]]:
        ids = [n["id"] for n in numbers] + ["none"]
        schema = ca.obj_schema({s["name"]: {"type": "string", "enum": ids} for s in slots})
        label = "assy_spec_reask" if violation else "assy_spec"
        counts = tally(self.llm, self.prompt(numbers, slots, violation), schema, label,
                       {s["name"]: ids for s in slots})
        return {k: (None if majority(c) in (None, "none") else majority(c)) for k, c in counts.items()}

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
        req = [s["name"] for s in slots if s["default_rule"] is None]
        picked = [answer.get(k) for k in req if answer.get(k)]
        if len(picked) != len(set(picked)):
            out.append((f"{', '.join(req)} must be different numbers in the text", req))
        return out

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
    """The largest-thread catalogue screw (its boss OD = max(min_boss_od, pilot + 2 x boss_wall_min))."""
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
    ConfirmArrangement: Python words the arrangement, the LLM says whether it matches the request; on
    "no" the next feasible assignment (ordered by the LLM's own votes) is tried until confirmed or exhausted."""

    def __init__(self, design, llm):
        super().__init__("ArrangeContents", design, llm)

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
        if exposed:
            words = "\n".join(f"- {s}: {edges[s]['words']}" for s in sides)
            items = "\n".join(f"- {it.id}: {it.name} x{it.quantity} "
                              f"({st.catalog.get(it.part).data['connectors'][0]['name']} connector)" for it in exposed)
            prompt = (f"Request: {self.design.base_request or self.design.request}\n\n"
                      f"The board edges:\n{words}\n\nWhich board edge does each part's connector face, so its "
                      f"cable plugs in through that end or side of the enclosure?\n{items}")
            schema = ca.obj_schema({it.id: {"type": "string", "enum": sides} for it in exposed})
            counts = tally(self.llm, prompt, schema, "assy_edge", {it.id: sides for it in exposed})
            first = {it.id: majority(counts[it.id]) or sides[0] for it in exposed}
            for it in exposed:
                if majority(counts[it.id]) is None:
                    st.assumptions.append(f"edge[{it.id}]: no valid answer, {sides[0]} tried first")
            order = self.assignments(exposed, sides, counts, first)
        else:
            counts, order = {}, [{}]
        tried = []
        for assign in order:
            try:
                result = placer.place(st.items, assign)
            except lay.LayoutError as e:
                tried.append(f"{assign}: {e}")
                st.notes.append(f"arrange: {assign} infeasible ({e.kind}: {e.detail})")
                continue
            if not exposed:
                return self.accept(result, assign, placer, "rule:no_exposed_connector")
            text = lay.describe(result, st.items)
            p = self.llm.p_yes(f"Request: {self.design.base_request or self.design.request}\n\n"
                               f"Proposed arrangement on the board: {text}.\n"
                               "Does this arrangement match the request? Answer yes or no.", label="assy_confirm")
            st.history.append({"stage": "confirm_arrangement", "assignment": dict(assign), "words": text, "p_yes": p})
            if p >= 0.5:
                return self.accept(result, assign, placer, "llm", counts=counts, p_yes=p)
            tried.append(f"{assign}: rejected by the controller (p_yes {p:.2f})")
        return self.fail("no confirmed feasible arrangement: " + " | ".join(tried[-4:]))

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
        if "p_yes" in extra:
            st.choices["arrangement_confirmed"] = {"value": True, "by": "llm", "p_yes": extra["p_yes"]}
        for note in result.notes:
            st.notes.append(f"arrange: {note}")
        st.frame = {"origin": "board min corner on its top surface", "x": "along the board's longest edge",
                    "z": "up", "edges": result.edges}
        st.layout = {p.node_id: p.to_json() for p in result.placed}
        st.layout_grid_residual = placer.grid_residual(result.placed)
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
            st.graph.add(pt.column(holes, i, seat_d, bottom - s["keepout_below"] - r["cut_overrun"],
                                   top + r["cut_overrun"], "seat", prefix="seat"))
            st.graph.add(pt.column(holes, i, seat_d, top, top + s["keepout_above"], "hole_keepout", prefix="hole_ko"))
        for p in st.placed.placed:
            stacks = [q for q in st.placed.placed if q.of == p.node_id]
            if stacks:
                st.graph.add(pt.content_envelope([(p.inst, p.pose)] + [(q.inst, q.pose) for q in stacks],
                                                 f"{p.node_id}_envelope", role="module_envelope"))
        return Status.SUCCESS


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
    """The cavity: AABB of every reference part with the board keep-outs, grown by spec.board_clearance
    in plan; floor at the solder-side keep-out; top at the component keep-out (or the tallest part plus
    the headroom). Every size is an expression, so a spec change re-derives it (the size-leak fix)."""
    refs = [n.id for n in st.graph.references()]
    p = {
        "x0": f"{_fold('min', [f'{r}.bbox.min_x' for r in refs])} - spec.board_clearance",
        "x1": f"{_fold('max', [f'{r}.bbox.max_x' for r in refs])} + spec.board_clearance",
        "y0": f"{_fold('min', [f'{r}.bbox.min_y' for r in refs])} - spec.board_clearance",
        "y1": f"{_fold('max', [f'{r}.bbox.max_y' for r in refs])} + spec.board_clearance",
        "z0": "board.BOTTOM.z - spec.keepout_below",
        "z1": f"max(board.TOP.z + spec.keepout_above, {_fold('max', [f'{r}.bbox.max_z' for r in refs])} + spec.headroom)",
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
    the opening (their cross-section + 2 x plug_to_opening); all-cylinder -> round cut, else a box."""
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
    w = f"{_fold('max', [f'{n.id}.cw' for n in crossing])} + 2*rules.plug_to_opening"
    h = f"{_fold('max', [f'{n.id}.ch' for n in crossing])} + 2*rules.plug_to_opening"
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


def derive_features(st: AssemblyState) -> List[str]:
    """Tray + lid with screws (ARCHITECTURE.md 4.3, 7.4). Returns the port-cut node ids."""
    g = st.graph
    r = st.rules.values
    g.add(derive_cavity(st))
    res = resolve(st)
    cuts = []
    for p, c in exposed_connectors(st):
        node, side = derive_port_cut(st, p, c, res)
        g.add(node)
        cuts.append(node)
    split_terms = ["cavity.z1 + rules.lip_engagement"] + [f"{n.id}.top + rules.min_ligament" for n in cuts]
    g.add(fg.Node("base", "body", "shell", {
        "wall": "cavity.wall", "floor": "cavity.floor", "split": _fold("max", split_terms),
        "x": "cavity.x + 2*wall", "y": "cavity.y + 2*wall", "z": "split - cavity.z0 + floor", "open_top": 1},
        fg.Pose(offset=("cavity.cx", "cavity.cy", "cavity.z0 - floor")), role="tray",
        source="rule:tray_lid.base", color=fg.BODY_COLORS[0]))
    holes = lay.world_datum(st.placed.get("board"), "HOLE")
    for i in range(len(holes.at)):
        hole = f"board.HOLE[{i}]"
        g.add(fg.Node(f"standoff_{i + 1}", "add", "cylinder", {
            "d": "max(fastener.board.pilot_diameter + 2*rules.standoff_wall_min, fastener.board.min_boss_od)",
            "h": "board.BOTTOM.z - cavity.z0 + base.floor", "top": "board.BOTTOM.z",
            "height": "board.BOTTOM.z - cavity.z0"},
            fg.Pose(at=hole, offset=(0, 0, f"cavity.z0 - base.floor - {hole}.z")), body="base", role="standoff",
            source="rule:mount_hole_to_standoff"))
        g.add(fg.Node(f"standoff_{i + 1}_pilot", "cut", "cylinder", {
            "d": "fastener.board.pilot_diameter", "h": "fastener.board.min_engagement + rules.cut_overrun",
            "depth": "fastener.board.min_engagement"},
            fg.Pose(at=hole, offset=(0, 0, f"board.BOTTOM.z - fastener.board.min_engagement - {hole}.z")),
            body="base", role="pilot", source="rule:mount_hole_to_standoff"))
    g.add(fg.Node("lid", "body", "box", {"x": "base.x", "y": "base.y", "z": "cavity.wall"},
                  fg.Pose(offset=("cavity.cx", "cavity.cy", "base.split")), role="lid_plate",
                  source="rule:tray_lid.lid", color=fg.BODY_COLORS[1]))
    g.add(fg.Node("lid_lip", "add", "shell", {
        "x": "cavity.x - 2*rules.sliding_fit", "y": "cavity.y - 2*rules.sliding_fit",
        "z": "rules.lip_engagement + lid.z", "wall": "rules.lip_wall", "floor": 0, "open_top": 1,
        "fit": "rules.sliding_fit", "bottom": "base.split - rules.lip_engagement"},
        fg.Pose(offset=("cavity.cx", "cavity.cy", "base.split - rules.lip_engagement")), body="lid", role="lip",
        source="rule:lid_to_fastening.lip"))
    corners = [("x0", "y0", -1, -1), ("x1", "y0", 1, -1), ("x0", "y1", -1, 1), ("x1", "y1", 1, 1)]
    for k, (bx, by, sx, sy) in enumerate(corners, 1):
        boss = f"boss_{k}"
        cx = f"cavity.{bx} {'+' if sx < 0 else '-'} spec.board_clearance"
        cy = f"cavity.{by} {'+' if sy < 0 else '-'} spec.board_clearance"
        g.add(fg.Node(boss, "add", "cylinder", {
            "d": "max(fastener.lid.min_boss_od, fastener.lid.pilot_diameter + 2*rules.boss_wall_min)",
            "ax": f"{cx} {'-' if sx < 0 else '+'} {DIAGONAL!r}*(d/2 + spec.board_clearance)",
            "ay": f"{cy} {'-' if sy < 0 else '+'} {DIAGONAL!r}*(d/2 + spec.board_clearance)",
            "h": "base.split - cavity.z0 + base.floor"},
            fg.Pose(offset=("ax", "ay", "cavity.z0 - base.floor")), body="base", role="boss",
            source="rule:lid_to_fastening.corner_pilaster"))
        g.add(fg.Node(f"{boss}_pilot", "cut", "cylinder", {
            "d": "fastener.lid.pilot_diameter", "h": "fastener.lid.min_engagement + rules.cut_overrun",
            "depth": "fastener.lid.min_engagement"},
            fg.Pose(offset=(f"{boss}.ax", f"{boss}.ay", "base.split - fastener.lid.min_engagement")),
            body="base", role="pilot", source="rule:lid_to_fastening.corner_pilaster"))
        g.add(fg.Node(f"{boss}_pad", "add", "cylinder", {"d": f"{boss}.d", "h": "lid.z"},
                      fg.Pose(offset=(f"{boss}.ax", f"{boss}.ay", "base.split")), body="lid", role="pad",
                      source="rule:lid_to_fastening.corner_pilaster"))
        g.add(fg.Node(f"{boss}_lid_hole", "cut", "cylinder", {
            "d": "fastener.lid.clearance_diameter", "h": "lid.z + 2*rules.cut_overrun"},
            fg.Pose(offset=(f"{boss}.ax", f"{boss}.ay", "base.split - rules.cut_overrun")), body="lid",
            role="screw_hole", source="rule:lid_to_fastening.corner_pilaster"))
        g.add(fg.Node(f"{boss}_lip_notch", "cut", "cylinder", {
            "d": f"{boss}.d + 2*rules.sliding_fit", "h": "rules.lip_engagement + rules.cut_overrun"},
            fg.Pose(offset=(f"{boss}.ax", f"{boss}.ay", "base.split - rules.lip_engagement - rules.cut_overrun")),
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


def build_plan(st: AssemblyState) -> ac.Plan:
    """The rule-derived check set (iteration 002 subset) and the volumes it measures against."""
    r, s, res, g = st.rules.values, st.spec, st.resolved, st.graph
    plan = ac.Plan(tol=ac.Tol.from_rules(r), seg=res.segments())
    vols = plan.volumes
    refs = g.references()
    ref_solids = {n.id: fg.solid(n, res) for n in refs}
    seats = ac.union([fg.solid(n, res) for n in g if n.role == "seat"])
    vols["seats"] = seats
    vols["board"] = ref_solids["board"]
    vols["references"] = ac.union(list(ref_solids.values()))
    for n in g:
        if n.role in ("keepout_top", "keepout_bottom") or n.role == "module_envelope":
            vols[n.id] = fg.solid(n, res)
    plan.add("separable", "separable", "base and lid are each one shell and overlap by at most "
             f"{r['overlap_max']:g} mm3 when closed", bodies=list(BODIES), overlap_max=r["overlap_max"])
    plan.add("inside_references", "inside", f"the board assembly (minus the seat columns) lies inside the closed "
             f"enclosure with {s['board_clearance']:g} mm clearance", volume="references", minus="seats",
             clearance=s["board_clearance"])
    plan.add("clear_board", "clear_of", f"no printed surface within {s['board_clearance']:g} mm of the board, "
             "except the standoff tops in the seat columns", volume="board", minus="seats", clearance=s["board_clearance"])
    for n in g:
        if n.role == "module_envelope":
            plan.add(f"clear_{n.id}", "clear_of", f"{n.id} at least {r['part_to_wall']:g} mm from every printed surface",
                     volume=n.id, clearance=r["part_to_wall"])
    plan.add("clear_keepout_top", "clear_of", "nothing printed inside the component keep-out above the board",
             volume="board_ko_top", clearance=0.0)
    plan.add("clear_keepout_bottom", "clear_of", "nothing printed inside the solder-side keep-out, except standoffs "
             "in the seat columns", volume="board_ko_bot", minus="seats", clearance=0.0)
    for p, c in exposed_connectors(st):
        name = f"{p.node_id}_plug"
        vols[name] = ac.union([fg.solid(n, res) for n in g if n.kind == "envelope" and n.id.startswith(name + "_")])
        plan.add(f"clear_{name}", "clear_of", f"the {c['mates']} plug in {p.node_id} at full mate and its withdrawal path "
                 f"stay {r['plug_to_opening']:g} mm from the enclosure", volume=name, clearance=r["plug_to_opening"])
    base, cav = res.params["base"], res.params["cavity"]
    lid = res.params["lid"]
    # Wall slabs (rubric.md 3.4): between the wall's inner and outer face planes, across the cavity's span
    # (the corners belong to the perpendicular walls and hold the lid-screw pilots), from the base's
    # bottom to the lid's top. Each face is inset by measure_tol so coplanar faces leave no skin.
    eps = r["measure_tol"]
    z_lo, z_hi = cav["z0"] - base["floor"] + eps, base["split"] + lid["z"] - eps
    cuts = [n for n in g if n.role == "port_cut"]
    for side, (bound, i, sign) in SIDE_BOUND.items():
        inner = cav[bound]
        outer = inner + sign * base["wall"]
        t = 1 - i
        tb = ("x0", "x1") if t == 0 else ("y0", "y1")
        t_lo, t_hi = cav[tb[0]], cav[tb[1]]
        lo, hi = [0.0, 0.0, z_lo], [0.0, 0.0, z_hi]
        lo[i], hi[i] = min(inner, outer) + eps, max(inner, outer) - eps
        lo[t], hi[t] = t_lo, t_hi
        slab = f"slab_{side}"
        vols[slab] = ac.m3d.Manifold.cube([hi[k] - lo[k] for k in range(3)]).translate(lo)
        on_wall = [n for n in cuts if n.wall == side]
        plan.add(f"apertures_{side}", "aperture_count", f"wall {side} has exactly {len(on_wall)} opening(s)",
                 slab=slab, n=len(on_wall), wall=side)
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
        for scad, stem in (("views.scad", "model"), ("ghost.scad", "ghost")):
            try:
                done, failures = ca.render_openscad(self.design.workdir / scad, ca.VIEWS, views, stem=stem)
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


def finalize(design, llm) -> dict:
    """verified exactly when every check passes on the delivered STLs; otherwise unsatisfied."""
    st = design.assy
    failed = [r.check_id for r in st.results if not r.passed]
    outcome = "verified" if st.results and not failed else "unsatisfied"
    st.stage = "done"
    print(f"assembly: {outcome}; {len(st.results) - len(failed)}/{len(st.results)} checks pass on the delivered STLs"
          + (f"; failing: {', '.join(failed)}" if failed else ""), flush=True)
    return {"outcome": outcome, "failed": failed, "checks": len(st.results)}
