"""--mode assembly: the enclosure-designing agent (ARCHITECTURE.md sections 2-4).

The target tree (ARCHITECTURE.md section 4) is built one milestone at a time.
Iteration 002 wires the walking skeleton (ARCHITECTURE.md 7.1 step 2, 7.4):

    cad_assembly (Sequence)
    ├── LoadCatalog        parts.Catalog.load + validation gate; a failing part is dropped and noted
    ├── LoadRules          design_rules.json (generic FDM / fastener rules and spec slots, each with a source)
    ├── ParseSpec          LLM maps generic spec slots onto number ids Python extracted from the text (enum)
    ├── Contents           Python proposes catalogue candidates; LLM gives quantity + exposed (enums)
    ├── ExposureCoverage   a text naming a plug requires the connector that takes it to be exposed: Python senses
    │                      each violation and exposes it by rule, no question (7.10, 7.11)
    ├── ChooseStack        evidence-gated: one option named by the text -> rule; several -> LLM enum among them;
    │                      none -> the catalogue default, flagged (7.10)
    ├── ArrangeContents    board screw by rule (role evidence > datasheet thread > smallest that passes, delta 002 C1);
    │                      LLM: board edge per exposed item (enum); a gated face-relation question (delta 002 C0: only
    │                      when one sentence names two exposed parts and a relation word; a unanimous reading becomes a
    │                      face_relation check); Python: mm placement (layout.py);
    │                      prescore: every feasible candidate through the downstream plant, only the ties at the
    │                      minimum controllable error go on (one survivor -> rule:prescore, 7.11);
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
    ├── RenderViews        views/model_* (bodies), views/ghost_* (bodies + references), views/open_* (lid off);
    │                      elevations tilted down by rules.view_elevation_deg (assembly_views, 7.11)
    └── WritePackage       base/lid .stl/.scad, model.scad, layout.json, self_report.json, feature_graph.json,
                           checks.json, verification_matrix.{md,json}, model.3mf
    finalize(): verified (every check passes on the delivered STLs) | unsatisfied; failing checks that name a
                competing rule are listed as typed requirement conflicts (assembly.conflicts, one per part,
                with a kind such as grid_extent / blocked / no_pin_data / coverage)

The local LLM is the controller for discrete choices and answers only enums that
Python builds; Python is the plant model and the sensor. Nothing here holds a
number, part or face that is specific to one request (test_no_hardcoding.py
scans this module).
"""

import copy
import itertools
import json
import math
import os
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
import cascade
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
COVERAGE_RULE = "rule:text_coverage"             # a named plug's connector is exposed by rule (7.11)
COVERAGE_INFEASIBLE = "rule:coverage_infeasible"  # ...unless no feasible arrangement exists with it exposed
ELEVATION_VIEWS = ("front", "back", "left", "right")   # cad_agent.VIEWS keys tilted down in assembly renders (7.11)
VIEW_ROTX = 3                # index of rotx in a cad_agent.VIEWS tuple (tx, ty, tz, rotx, roty, rotz, dist)
PRIMARY = "board"            # node id, item id and layout role of the primary reference (generalize delta 001 C1): kept
                             # for any primary part, so every downstream expression keeps its anchor
LID_FIELDS = ("pilot_diameter", "thread_diameter", "clearance_diameter", "min_engagement")   # a screw that can hold a lid


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
    parts_dirs: List[str] = field(default_factory=list)       # every catalogue folder, in lookup order
    rules_path: Optional[str] = None
    with_models: bool = False
    stl_source: Dict[str, str] = field(default_factory=dict)
    components: List[dict] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    resolved: Any = None
    solids: Dict[str, Any] = field(default_factory=dict)
    plan: Any = None
    layout_grid_residual: Optional[float] = None              # worst non-exempt pin residual (= grid_conformance)
    layout_grid_residual_all: Optional[float] = None          # worst over every placed part, pin_pattern-exempt included
    layout_grid_exempt: List[str] = field(default_factory=list)
    grid_report: Dict[str, Any] = field(default_factory=dict)  # layout.Placer.grid_report of the accepted layout
    conflicts: List[dict] = field(default_factory=list)       # typed requirement conflicts (finalize)
    arrange: Dict[str, Any] = field(default_factory=dict)     # ConfirmArrangement's whole ranking (candidates, classes)
    texts: List[Tuple[str, str]] = field(default_factory=list)  # (source, text): the request and every L1 (ParseSpec)
    coverage: List[dict] = field(default_factory=list)        # text-coverage violations and how each was resolved (7.10)
    links: Dict[str, List[str]] = field(default_factory=dict)  # check id -> the L1 ids it is traced to (7.10)
    number_owner: Dict[str, str] = field(default_factory=dict)  # number id -> the slot that states it (spec slot or
                                                                # <item>.<param>): one number, one slot across stages
    unplaced: List[dict] = field(default_factory=list)        # content items the primary does not carry (GM2b relations)
    relations: List[dict] = field(default_factory=list)       # face relations the controller read unanimously (delta 002
                                                              # C0): each becomes a face_relation_<A>_<B> check

    def summary(self) -> dict:
        return {
            "stage": self.stage,
            "notes": list(self.notes),
            "parts_dir": self.parts_dir,
            "parts_dirs": list(self.parts_dirs or [self.parts_dir]),
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
            "coverage": list(self.coverage),
            "links": dict(self.links),
            "number_owner": dict(self.number_owner),
            "unplaced": list(self.unplaced),
            "relations": list(self.relations),
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
# Evidence in the text (ARCHITECTURE.md 7.10): catalogue aliases and option numbers, quoted by sentence
# ---------------------------------------------------------------------------

SENTENCE_RE = re.compile(r"(?<=[.!?;])\s+")


def sentences(text: str) -> List[str]:
    """The text split after sentence punctuation followed by a space ("3.5 mm" stays whole)."""
    return [s.strip() for s in SENTENCE_RE.split(text or "") if s.strip()]


def text_evidence(texts: Sequence[Tuple[str, str]], aliases: Sequence[str], numbers: Sequence[float] = (),
                  tol: float = 0.0) -> List[dict]:
    """Where the text names something: per (source, sentence), the first alias whose `parts.tokens` are a contiguous
    run of the sentence's tokens, or else the first of `numbers` that a number occurrence of the sentence equals
    within `tol`. Each hit is {source, quote (the sentence), match, kind: alias | number}. Aliases come from part.json
    `names` and numbers from part data, so the helper is generic: the discrete counterpart of ParseSpec's number
    coverage."""
    runs = [(a, pt.tokens(a)) for a in aliases]
    runs = [(a, r) for a, r in runs if r]
    out: List[dict] = []
    for source, text in texts:
        for sent in sentences(text):
            toks = pt.tokens(sent)
            hit = next(({"match": a, "kind": "alias"} for a, r in runs
                        if any(toks[i:i + len(r)] == r for i in range(len(toks) - len(r) + 1))), None)
            if hit is None and numbers:
                hit = next(({"match": n["text"], "kind": "number"} for n in extract_numbers([(source, sent)])
                            for v in numbers if abs(n["value"] - float(v)) <= tol), None)
            if hit is not None:
                out.append(dict({"source": source, "quote": sent}, **hit))
    return out


def named_parts(st: "AssemblyState") -> Dict[str, List[dict]]:
    """Every catalogue part the request or an L1 names (its part.json `names`), with the text_evidence hits."""
    out: Dict[str, List[dict]] = {}
    for pid in st.catalog.ids():
        hits = text_evidence(st.texts, st.catalog.get(pid).names)
        if hits:
            out[pid] = hits
    return out


def human_name(catalog: pt.Catalog, pid: str) -> str:
    return catalog.get(pid).names[0] if pid in catalog and catalog.get(pid).names else pid


def primary_item(st: "AssemblyState") -> Optional[dict]:
    """The content item that is the primary reference (generalize delta 001 C1), or None before Contents chose it."""
    return next((i for i in st.contents if i.get("id") == PRIMARY), None)


def primary_mount(st: "AssemblyState") -> Tuple[str, str, str]:
    """(holes, seat, top) datum names of the placed primary's mount_holes interface: no datum name is literal here."""
    return pt.mount_names(st.placed.get(PRIMARY).inst.part)


def conn_key(p: lay.Placed, conn: dict) -> str:
    """The id stem of one exposed connector's plug sweep and port cut: the node id for a part with one connector (the
    iteration 002 ids), node id + connector name for a part with several, so each connector gets its own envelope."""
    return p.node_id if len(p.inst.connectors) <= 1 else f"{p.node_id}_{conn['name']}"


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
        cat = pt.Catalog.load(st.parts_dirs or st.parts_dir)
        for err in cat.errors:
            st.notes.append(f"catalogue: {err}")
        for pid in cat.ids():
            part = cat.get(pid)
            try:
                fails = pt.gate(part)        # gate sample + every specimen's match instance (iteration 011 C1)
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


def spec_prompt(numbers, slots, violation: str = "", note: str = "") -> str:
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


def ask_slots(llm, numbers, slots, violation: str = "", label: Optional[str] = None,
              note: str = "") -> Dict[str, Optional[str]]:
    """One voted slot-mapping question (ParseSpec's, also used to re-ask a spec slot that lost a number later)."""
    ids = [n["id"] for n in numbers] + ["none"]
    schema = ca.obj_schema({s["name"]: {"type": "string", "enum": ids} for s in slots})
    label = label or ("assy_spec_reask" if violation else "assy_spec")
    counts = tally(llm, spec_prompt(numbers, slots, violation, note), schema, label, {s["name"]: ids for s in slots})
    return {k: (None if majority(c) in (None, "none") else majority(c)) for k, c in counts.items()}


def owner_question(llm, ref: str, n: dict, names: Sequence[str], meaning: Mapping[str, dict]) -> Tuple[Optional[str], Counter]:
    """Each number in the text states one quantity: one voted question gives number `ref` to one of `names` (spec slots
    or part sizes, each {meaning, unit}). Lifted from ParseSpec.resolve_shared (generalize delta 001 C3) so the same
    question also runs across ParseSpec and Contents.ask_params. Returns (owner or None, the votes)."""
    lines = "\n".join(f"- {k}: {meaning[k]['meaning']} ({meaning[k]['unit']})" for k in names)
    prompt = (f"An enclosure is being designed from this request and its requirements.\n\n"
              f'Number {ref} = {n["text"]} ({n["source"]}): "...{n["quote"]}..."\n\n'
              f"Each number in the text states exactly one quantity. Which one of these quantities does "
              f"{ref} state?\n{lines}")
    counts = tally(llm, prompt, ca.obj_schema({"owner": {"type": "string", "enum": list(names)}}),
                   "assy_spec_owner", {"owner": list(names)})
    return majority(counts["owner"]), counts["owner"]


class ParseSpec(AssemblyStep):
    """Typed spec slots from the text: the LLM maps each slot onto a number id (or none); Python checks
    generic relations (one re-ask naming the violation) and fills silent slots from the rules."""

    def __init__(self, design, llm):
        super().__init__("ParseSpec", design, llm)

    def texts(self) -> List[Tuple[str, str]]:
        d = self.design
        return [("request", d.base_request or d.request)] + [(r["id"], r["text"]) for r in d.l1]

    def prompt(self, numbers, slots, violation: str = "", note: str = "") -> str:
        return spec_prompt(numbers, slots, violation, note)

    def ask(self, numbers, slots, violation="", label: Optional[str] = None, note: str = "") -> Dict[str, Optional[str]]:
        return ask_slots(self.llm, numbers, slots, violation, label, note)

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
            if s.get("required", s["default_rule"] is None) and not answer.get(s["name"]):
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
        owner, votes = owner_question(self.llm, ref, n, names, meaning)
        if owner is None:
            st.notes.append(f"parse_spec: no valid owner for {ref} among {', '.join(names)}; they fall back")
            for k in names:
                answer[k] = None
            return answer
        losers = [k for k in names if k != owner]
        st.notes.append(f"parse_spec: {ref} states {owner} (owner vote {dict(votes)}); re-asking "
                        f"{', '.join(losers)} without it")
        got = self.ask([x for x in numbers if x["id"] != ref], [meaning[k] for k in losers], label="assy_spec_slot",
                       note=f'{ref} ({n["text"]}) states {owner}, so it is not offered for the quantities below.')
        answer.update({k: got.get(k) for k in losers})
        return answer

    def update(self) -> Status:
        st = self.state
        st.stage = "parse_spec"
        st.texts = self.texts()
        numbers = extract_numbers(st.texts)
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
        missing = [s["name"] for s in slots if s.get("required", s["default_rule"] is None) and not answer.get(s["name"])]
        if missing:
            return self.fail(f"no number in the text for {', '.join(missing)} (no default exists)")
        for s in slots:
            k, ref = s["name"], answer.get(s["name"])
            if ref:
                n = by_id[ref]
                st.spec[k] = n["value"]
                st.spec_provenance[k] = f'{n["source"]}:"{n["quote"]}"'
                st.number_owner.setdefault(ref, k)
            elif s["default_rule"] is None:      # an optional slot with no default (the board size): left out of the spec
                continue
            else:
                v = st.rules.values[s["default_rule"]]
                st.spec[k] = v
                st.spec_provenance[k] = f"rules:{s['default_rule']}"
                st.assumptions.append(f"{k} = {v:g} {s['unit']} from rules:{s['default_rule']} "
                                      "(the text states no number for it)")
        settle_spec(st, "parse_spec")
        self.logger.info(f"spec: {st.spec}")
        return Status.SUCCESS


def spec_relation_error(spec: Mapping[str, float], name: str, value: float) -> Optional[str]:
    """ParseSpec's generic relations for one slot taking `value` (> 0; wall_min <= wall_max against a text-stated other
    end). Used when a spec slot is re-asked after ParseSpec (Contents.reask_spec_slot). Returns the violation or None."""
    if value <= 0:
        return f"{name} must be greater than 0 (got {value:g})"
    lo, hi = "wall_min", "wall_max"
    if name in (lo, hi):
        other = hi if name == lo else lo
        if other in spec and ((name == lo and value > spec[hi]) or (name == hi and spec[lo] > value)):
            return f"wall_min must not exceed wall_max ({name} {value:g}, {other} {spec[other]:g})"
    return None


def settle_spec(st: "AssemblyState", stage: str) -> None:
    """The spec rules that run after slots change (ParseSpec, and again after a cross-stage re-ask, C3): a band whose
    rules-default end breaks it yields to the text-stated end, and the frame rule puts X along the board's longest edge
    (board_width/board_depth swapped with their provenance and number ownership)."""
    lo, hi = "wall_min", "wall_max"
    if lo in st.spec and hi in st.spec and st.spec[lo] > st.spec[hi]:
        # a band with one end from the text and the other from a default: the default yields to the text
        fix = hi if st.spec_provenance[hi].startswith("rules:") else lo
        other = lo if fix == hi else hi
        st.spec[fix] = st.spec[other]
        st.spec_provenance[fix] = f"{st.spec_provenance[other]} (band end set equal: its default broke the band)"
        st.assumptions.append(f"{fix} = {st.spec[fix]:g} (its rules default fell outside the stated band)")
    w, d = "board_width", "board_depth"
    if w in st.spec and d in st.spec and st.spec[d] > st.spec[w]:   # frame rule: X along the board's longest edge
        st.spec[w], st.spec[d] = st.spec[d], st.spec[w]
        st.spec_provenance[w], st.spec_provenance[d] = st.spec_provenance[d], st.spec_provenance[w]
        swap = {w: d, d: w}
        st.number_owner = {ref: swap.get(slot, slot) for ref, slot in st.number_owner.items()}
        st.notes.append(f"{stage}: board_width/board_depth swapped so X runs along the longest edge")


def part_words(part: pt.Part, catalog: Optional[pt.Catalog] = None) -> str:
    """A candidate in words: its first human name and kind; each connector named by the mating plug's first human
    name from the catalogue (never its id), e.g. "<conn> connector (takes a <plug name>)"."""
    conns = part.data.get("connectors", [])
    extra = ""
    if conns:
        def mate(c):
            m = c.get("mates")
            return human_name(catalog, m) if catalog is not None and m else (m or "plug")
        extra = "; cable connector: " + ", ".join(f"{c['name']} connector (takes a {mate(c)})" for c in conns)
    return f"{part.names[0] if part.names else part.id} ({part.kind}{extra})"


def connector_list(part: pt.Part) -> List[dict]:
    return list(part.data.get("connectors", []) or [])


def exposure_key(conn: dict) -> str:
    """The per-connector yes/no key of a part with two or more connectors (generalize delta 001 C1)."""
    return f"{conn['name']}_exposed"


def assign_ids(items: Sequence[dict], primary: Optional[dict]) -> Dict[str, str]:
    """Item ids: the primary is PRIMARY, every other item <kind>_<n> in candidate order. Returns old id -> new id."""
    kinds: Counter = Counter()
    moved = {}
    for it in items:
        old = it.get("id")
        if it is primary:
            it["id"] = PRIMARY
        else:
            kinds[it["kind"]] += 1
            it["id"] = f"{it['kind']}_{kinds[it['kind']]}"
        if old is not None and old != it["id"]:
            moved[old] = it["id"]
    return moved


def plan_footprint(catalog: pt.Catalog, item: dict) -> float:
    """The part's catalogue plan footprint (bbox X x Y in its own frame, at the item's params)."""
    lo, hi = catalog.instantiate(item["part"], item.get("params") or {}).bbox()
    return float((hi[0] - lo[0]) * (hi[1] - lo[1]))


class Contents(AssemblyStep):
    """Python proposes catalogue candidates per content kind, plus every part with a mount_holes interface the text names;
    the LLM answers quantity and, per cable connector, whether it is exposed. Python then chooses the primary reference by
    rule (generalize delta 001 C1): the carrier (a part with a grid block) when exactly one is in the contents, else the
    content part with the largest catalogue plan footprint, which must offer a mount_holes interface. A non-carrier
    primary carries no other contents: they are listed as unplaced (each with a failing content_placed check)."""

    def __init__(self, design, llm):
        super().__init__("Contents", design, llm)
        self.param_stop: Optional[str] = None      # a typed stop from a final part-size re-ask (claim)

    def candidates(self) -> List[str]:
        st = self.state
        text = self.design.base_request or self.design.request
        k = int(st.rules.values["lookup_k"])
        ranked = st.catalog.lookup(text, k=len(st.catalog.parts))
        out = []
        for kind in CONTENT_KINDS:
            out += [pid for pid, _ in ranked if st.catalog.get(pid).kind == kind][:k]
        named = named_parts(st)        # a contiguous alias run: stricter than token overlap
        out += [pid for pid in st.catalog.ids()
                if pid in named and pid not in out and pt.mount_interface(st.catalog.get(pid)) is not None]
        return out

    def update(self) -> Status:
        st = self.state
        st.stage = "contents"
        self.param_stop = None
        cands = self.candidates()
        if not cands:
            return self.fail("nothing to design around: no catalogue part matches the request")
        qmax = int(st.rules.values["max_quantity"])
        props, allowed, multi = {}, {}, False
        for pid in cands:
            conns = connector_list(st.catalog.get(pid))
            p = {"quantity": {"type": "integer", "enum": list(range(qmax + 1))}}
            allowed[f"{pid}.quantity"] = list(range(qmax + 1))
            if len(conns) == 1:
                p["exposed"] = {"type": "string", "enum": ["yes", "no"]}
                allowed[f"{pid}.exposed"] = ["yes", "no"]
            elif conns:
                multi = True
                for c in conns:
                    p[exposure_key(c)] = {"type": "string", "enum": ["yes", "no"]}
                    allowed[f"{pid}.{exposure_key(c)}"] = ["yes", "no"]
            props[pid] = ca.obj_schema(p)
        lines = "\n".join(f"- {pid}: {part_words(st.catalog.get(pid), st.catalog)}" for pid in cands)
        prompt = (f"Request: {self.design.base_request or self.design.request}\n\n"
                  f"Catalogue parts that may be in the request:\n{lines}\n\n"
                  "For each part give how many the request puts inside the enclosure (0 if none), and for parts "
                  "with a cable connector whether that connector must be reachable from outside (exposed).")
        if multi:
            prompt += (" A part with several cable connectors has one answer per connector (<connector>_exposed), "
                       "because each one may or may not be exposed.")
        counts = tally(self.llm, prompt, ca.obj_schema(props), "assy_contents", allowed)
        items = []
        for pid in cands:
            q = majority(counts[f"{pid}.quantity"])
            if not q:
                continue
            part = st.catalog.get(pid)
            conns = connector_list(part)
            item = {"part": pid, "kind": part.kind, "quantity": int(q), "exposed": False,
                    "name": part.names[0] if part.names else pid, "exposed_connectors": []}
            if len(conns) == 1:
                if majority(counts.get(f"{pid}.exposed", Counter())) == "yes":
                    item["exposed_connectors"] = [conns[0]["name"]]
                # recorded only (7.11): text coverage may override it, never the reverse
                item["exposed_votes"] = {k: v for k, v in counts[f"{pid}.exposed"].items() if k is not None}
            elif conns:
                item["exposed_connectors"] = [c["name"] for c in conns
                                              if majority(counts[f"{pid}.{exposure_key(c)}"]) == "yes"]
                item["exposed_votes"] = {c["name"]: {k: v for k, v in counts[f"{pid}.{exposure_key(c)}"].items()
                                                     if k is not None} for c in conns}
            item["exposed"] = bool(item["exposed_connectors"])
            items.append(item)
        if not items:
            return self.fail("nothing to design around: the answer puts no catalogue part in the request")
        primary, why = self.choose_primary(items)
        if primary is None:
            return Status.FAILURE
        part = st.catalog.get(primary["part"])
        if pt.mount_interface(part) is None:
            return self.fail(f"primary {primary['part']} has no {pt.MOUNT_HOLES} interface; its support (pocket / ribs "
                             "/ bolt-through) is not implemented (GM3/GM6)")
        if primary["quantity"] != 1:
            return self.fail(f"primary {primary['part']} has quantity {primary['quantity']}; one primary reference is "
                             "placed (several copies of it are GM2b)")
        moved = assign_ids(items, primary)
        self.rename(moved)
        sized_by_slots = self.size_primary(primary, part)
        for it in items:
            it.setdefault("params", {})
            ipart = st.catalog.get(it["part"])
            need = [p for p in ipart.request_params() if p not in it["params"]]
            if need:
                got = self.ask_params(it, ipart, need)
                if got is None:
                    return self.fail(self.param_stop or f"{it['part']}: no number in the text for {', '.join(need)}")
                it["params"].update(got)
        if sized_by_slots:                    # a cross-stage owner question may have moved a size slot (C3)
            rp = part.request_params()
            if "board_width" not in st.spec or "board_depth" not in st.spec:
                return self.fail(f"primary {part.id}: its size slots lost their numbers to other quantities")
            primary["params"].update({rp[0]: st.spec["board_width"], rp[1]: st.spec["board_depth"]})
        choice(st, "primary", primary["part"], "rule:primary_reference", reason=why,
               interface=pt.mount_interface(part).get("id"))
        st.contents = items
        try:
            board_provenance(st, st.catalog.instantiate(part.id, primary["params"]))
        except (pt.PartError, fg.ExprError, fg.MissingRefError, KeyError, ValueError) as e:
            st.notes.append(f"contents: primary {part.id} not instantiated for provenance ({e})")
        others = [i for i in items if i is not primary]
        if pt.is_carrier(part):
            st.items = [lay.Item(i["id"], i["part"], dict(i["params"]), i["quantity"], i["exposed"], None, i["name"],
                                 list(i["exposed_connectors"])) for i in others]
        else:
            st.items = []
            st.unplaced = [{"id": i["id"], "part": i["part"], "quantity": i["quantity"],
                            "reason": f"{part.id} is not a carrier: no relation places it yet (GM2b)"} for i in others]
            for u in st.unplaced:
                st.notes.append(f"contents: {u['id']} ({u['part']}) is unplaced: {u['reason']}")
        self.logger.info(f"contents: {[(i['part'], i['quantity'], i['exposed']) for i in items]}")
        return Status.SUCCESS

    def choose_primary(self, items: List[dict]) -> Tuple[Optional[dict], str]:
        """The primary reference rule. Carrier: exactly one carrier with quantity 1. Otherwise the largest catalogue
        plan footprint (request-sized parts are sized first, under provisional ids)."""
        st = self.state
        carriers = [i for i in items if pt.is_carrier(st.catalog.get(i["part"]))]
        if carriers:
            if len(carriers) != 1 or carriers[0]["quantity"] != 1:
                self.fail(f"exactly one carrier board can be the primary reference, the answer has "
                          f"{sum(c['quantity'] for c in carriers)} (several carriers are not implemented)")
                return None, ""
            return carriers[0], "carrier"
        assign_ids(items, None)
        for it in items:
            it.setdefault("params", {})
            ipart = st.catalog.get(it["part"])
            need = [p for p in ipart.request_params() if p not in it["params"]]
            if need:
                got = self.ask_params(it, ipart, need)
                if got is None:
                    self.fail(self.param_stop or f"{it['part']}: no number in the text for {', '.join(need)}")
                    return None, ""
                it["params"].update(got)
        areas = {it["id"]: plan_footprint(st.catalog, it) for it in items}
        best = items[0]
        for it in items[1:]:
            if areas[it["id"]] > areas[best["id"]] + st.rules.values["measure_tol"]:
                best = it
        st.notes.append("contents: primary by the largest catalogue plan footprint: "
                        + ", ".join(f"{it['part']} {areas[it['id']]:.1f} mm2" for it in items))
        return best, "largest plan footprint"

    def rename(self, moved: Mapping[str, str]) -> None:
        """Provisional item ids -> final ids in the provenance and number ownership records."""
        st = self.state
        if not moved:
            return

        def new(key: str) -> str:
            head, dot, tail = key.partition(".")
            return f"{moved[head]}.{tail}" if dot and head in moved else key

        st.spec_provenance = {new(k): v for k, v in st.spec_provenance.items()}
        st.number_owner = {ref: new(slot) for ref, slot in st.number_owner.items()}

    def size_primary(self, primary: dict, part: pt.Part) -> bool:
        """A request-sized primary takes its two size params from the spec's board size slots when ParseSpec filled them
        (True); otherwise its params come from the part-size question like any request-sized part (False)."""
        st = self.state
        primary.setdefault("params", {})
        rp = part.request_params()
        if len(rp) >= 2 and not any(k in primary["params"] for k in rp[:2]) and \
                "board_width" in st.spec and "board_depth" in st.spec:
            primary["params"].update({rp[0]: st.spec["board_width"], rp[1]: st.spec["board_depth"]})
            return True
        return False

    def ask_params(self, item, part: pt.Part, need: List[str], exclude: Sequence[str] = ()) -> Optional[Dict[str, float]]:
        st = self.state
        numbers = [n for n in st.numbers if n["id"] not in exclude]
        ids = [n["id"] for n in numbers] + ["none"]
        by_id = {n["id"]: n for n in st.numbers}
        schema = ca.obj_schema({p: {"type": "string", "enum": ids} for p in need})
        lines = "\n".join(f"- {p}: {part.params[p].get('source', p)}" for p in need)
        prompt = (f"Numbers found in the text:\n{number_lines(numbers)}\n\n"
                  f"The request includes a {item['name']}. For each of its sizes below give the id of the number "
                  f"that states it, or \"none\".\n{lines}")
        counts = tally(self.llm, prompt, schema, "assy_params_reask" if exclude else "assy_params",
                       {p: ids for p in need})
        out = {}
        for p in need:
            ref = majority(counts[p])
            if ref in (None, "none"):
                return None
            ref = self.claim(item, part, p, ref, by_id, final=bool(exclude))
            if ref is None:
                return None
            out[p] = by_id[ref]["value"]
            st.spec_provenance[f"{item['id']}.{p}"] = f'{by_id[ref]["source"]}:"{by_id[ref]["quote"]}"'
        return out

    def claim(self, item: dict, part: pt.Part, param: str, ref: str, by_id: Mapping[str, dict],
              final: bool = False) -> Optional[str]:
        """One number, one slot across stages (generalize delta 001 C3). A number id a spec slot already owns goes to one
        of the two by the owner question; the loser is re-asked once with the id removed from its enum (a spec slot that
        still has none falls back to its rules default, flagged). The part-size re-ask is final (`final`): if it again
        picks an id a spec slot owns, no second owner question runs and the part size stops, typed (sets param_stop).
        Returns the id this part size keeps, or None."""
        st = self.state
        slot = f"{item['id']}.{param}"
        owner = st.number_owner.get(ref)
        if owner is None or owner == slot or "." in owner:     # free, already this slot's, or another part's size
            st.number_owner.setdefault(ref, slot)
            return ref
        if final:
            self.param_stop = (f"{item['part']}: no number in the text for {param}: the re-asked {param} chose {ref} "
                               f"({by_id[ref]['text']}), which spec slot {owner} owns, and the part-size re-ask is "
                               f"final")
            return None                                         # every caller stops with fail(param_stop)
        spec_slot = st.rules.slot(owner)
        meaning = {owner: spec_slot,
                   slot: {"meaning": f"the {param} of the {item['name']} ({part.params[param].get('source', param)})",
                          "unit": part.data.get("units", "mm")}}
        n = by_id[ref]
        won, votes = owner_question(self.llm, ref, n, [owner, slot], meaning)
        st.notes.append(f"contents: {ref} ({n['text']}) is claimed by spec slot {owner} and by {slot}; owner vote "
                        f"{dict(votes)}")
        if won == slot:
            st.number_owner[ref] = slot
            self.reask_spec_slot(owner, ref, slot)
            return ref
        st.notes.append(f"contents: {ref} stays with {owner}; re-asking {slot} without it")
        got = self.ask_params(item, part, [param], exclude=[ref])
        if got is None:
            return None
        return next((r for r, s in st.number_owner.items() if s == slot), None)

    def reask_spec_slot(self, name: str, ref: str, winner: str) -> None:
        """A spec slot that lost its number to a part size: re-asked once without that id (assy_spec_slot); with no
        answer it takes its rules default, flagged as an assumption (as for any ParseSpec violation)."""
        st = self.state
        s = st.rules.slot(name)
        n = next(x for x in st.numbers if x["id"] == ref)
        got = ask_slots(self.llm, [x for x in st.numbers if x["id"] != ref], [s], label="assy_spec_slot",
                        note=f'{ref} ({n["text"]}) states {winner}, so it is not offered for the quantities below.')
        new = got.get(name)
        if new and st.number_owner.get(new) not in (None, name):
            st.notes.append(f"contents: the re-asked {name} chose {new}, which {st.number_owner[new]} owns; not used")
            new = None
        if new:
            m = next(x for x in st.numbers if x["id"] == new)
            bad = spec_relation_error(st.spec, name, m["value"])
            if bad:
                st.notes.append(f"contents: the re-asked {name} chose {new} ({m['text']}): {bad}; not used")
                new = None
        if new:
            st.spec[name] = m["value"]
            st.spec_provenance[name] = f'{m["source"]}:"{m["quote"]}"'
            st.number_owner[new] = name
            st.notes.append(f"contents: {name} re-asked without {ref}: {new} ({m['text']})")
        elif s["default_rule"] is not None:
            v = st.rules.values[s["default_rule"]]
            st.spec[name] = v
            st.spec_provenance[name] = f"rules:{s['default_rule']}"
            st.assumptions.append(f"{name} = {v:g} {s['unit']} from rules:{s['default_rule']} (its number states "
                                  f"{winner}, and the text states no other)")
        else:
            st.spec.pop(name, None)
            st.spec_provenance.pop(name, None)
            st.notes.append(f"contents: {name} has no number left in the text and no default")
        settle_spec(st, "contents")          # the band and frame rules ParseSpec ran, again on the changed slot (N2)


def hole_pattern_params(inst: pt.PartInstance) -> List[str]:
    """The non-request params the primary's mounting-hole datum (its positions and diameter) is built from, read from
    the part data, so no param name is listed in agent code."""
    d = inst.part.data.get("datums", {}).get(pt.mount_names(inst.part)[0]) or {}
    exprs = json.dumps([d.get("at"), d.get("start"), d.get("step"), d.get("count"), d.get("diameter")])
    names = set(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", exprs))
    req = set(inst.part.request_params())
    return [k for k in inst.part.params if k in names and k not in req]


def hole_pattern_words(inst: pt.PartInstance) -> str:
    """'Ø3 holes 2.5 mm from each edge' (or the hole centres) read back from the instance's mounting holes and bbox."""
    holes = pt.lookup_datum(inst.datums, pt.mount_names(inst.part)[0])
    lo, hi = inst.bbox()
    insets = [min(abs(q[i] - lo[i]), abs(hi[i] - q[i])) for q in holes.at for i in (0, 1)]
    dia = f"Ø{holes.diameter:g} " if holes.diameter is not None else ""
    if insets and max(insets) - min(insets) <= 1e-6:
        return f"{dia}holes {insets[0]:g} mm from each edge"
    return f"{dia}holes at " + ", ".join(f"({q[0]:g}, {q[1]:g})" for q in holes.at)


def board_provenance(st: AssemblyState, inst: pt.PartInstance) -> None:
    """Where the board's non-request numbers came from (iteration 011 C1): a catalogue specimen selected by the
    request's size, or the family defaults, which are an assumption the package states."""
    part = inst.part.id
    if inst.specimen is not None:
        sp = inst.specimen
        for p in sp.get("params", {}):
            st.spec_provenance[f"board.{p}"] = f"catalogue:{part} specimen {sp['id']} ({sp.get('source', '')})"
        st.notes.append(f"contents: board matches catalogue specimen {sp['id']}")
        return
    if not inst.part.request_params() or pt.mount_interface(inst.part) is None:
        return                       # a fixed-size module: its holes are catalogue (datasheet) data, not a family default
    defaulted = hole_pattern_params(inst)
    for p in defaulted:
        st.spec_provenance[f"board.{p}"] = f"catalogue:{part} family default"
    if defaulted:
        st.assumptions.append("The request does not state the board's mounting-hole pattern; the catalogue family "
                              f"default is used: {hole_pattern_words(inst)}.")


def board_block(st: AssemblyState) -> Optional[dict]:
    """layout.json's `board` (iteration 011 C1): the board the agent used, enough to rebuild every hole-derived
    reference from the package alone (resolved params, HOLE axes in the enclosure frame, grid, board screw)."""
    if st.placed is None:
        return None
    try:
        b = st.placed.get(PRIMARY)
    except StopIteration:
        return None
    inst = b.inst
    holes = lay.world_datum(b, pt.mount_names(inst.part)[0]) if pt.mount_interface(inst.part) else None
    g = inst.grid()
    grid = None
    if g is not None:
        origin = (b.pose @ np.append(np.asarray(g["origin"], dtype=float), 1.0))[:3]
        grid = {"origin": [round(float(v), 6) for v in origin], "pitch": g["pitch"],
                "count": None if g["count"] is None else [int(round(c)) for c in g["count"]]}
    return {"part": b.part, "specimen": (inst.specimen or {}).get("id"), "params": dict(inst.params),
            "holes": None if holes is None else [[round(float(v), 6) for v in q] for q in holes.at],
            "hole_diameter": None if holes is None else holes.diameter,
            "hole_keepout_diameter": None if holes is None else holes.keepout_diameter,
            "grid": grid, "screw": (st.choices.get("fastener[board]") or {}).get("value")}


class ExposureCoverage(AssemblyStep):
    """Text coverage (ARCHITECTURE.md 7.10, 7.11; the first outer-loop correction of 4.1, run before ArrangeContents): a
    text (request or L1) that names a catalogue plug requires the content connector that takes it to be exposed. Python
    senses each violation (named_parts) and resolves it by rule: "unexposed" leaves a hard check failing and "exposed"
    closes it, so the two are no tie on error and no vote is asked (7.11). The Contents vote is recorded under
    `overrides`. Only geometric infeasibility reverts it (ArrangeContents, rule:coverage_infeasible); the row then stays
    in st.coverage as a failing text_coverage check and a `coverage` conflict."""

    def __init__(self, design):
        super().__init__("ExposureCoverage", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "exposure_coverage"
        named = named_parts(st)
        items = {i.id: i for i in st.items}
        takers = {}
        for it in st.contents:
            for c in st.catalog.get(it["part"]).data.get("connectors", []):
                takers.setdefault(c.get("mates"), []).append((it, c))
        mated = {c.get("mates") for pid in st.catalog.ids() for c in st.catalog.get(pid).data.get("connectors", [])}
        for plug, hits in named.items():
            if plug not in mated:            # only a part some catalogue connector takes (a plug) asks for an opening
                continue
            if plug not in takers:
                st.notes.append(f"coverage: the text names {human_name(st.catalog, plug)} ({hits[0]['source']}) but no "
                                "content connector takes it")
                continue
            for it, conn in takers[plug]:
                names = it.setdefault("exposed_connectors", [])
                if conn["name"] in names:
                    continue
                evidence = [{"source": h["source"], "quote": h["quote"]} for h in hits]
                multi = len(connector_list(st.catalog.get(it["part"]))) > 1
                votes = dict(it.get("exposed_votes", {}))
                if multi:
                    votes = dict(votes.get(conn["name"], {}))
                names.append(conn["name"])
                it["exposed"] = True
                if it["id"] in items:
                    items[it["id"]].exposed = True
                    items[it["id"]].connectors = list(names)
                it["exposed_by"] = COVERAGE_RULE
                it.setdefault("coverage_connectors", []).append(conn["name"])
                st.coverage.append({"item": it["id"], "part": it["part"], "connector": conn["name"], "plug": plug,
                                    "evidence": evidence, "resolved": "exposed", "by": COVERAGE_RULE})
                choice(st, exposure_choice(it, conn, multi), True, COVERAGE_RULE, evidence=evidence,
                       overrides={"contents_votes": votes})
                st.notes.append(f"coverage: {it['id']}.{conn['name']} exposed by rule: {hits[0]['source']} names "
                                f"{human_name(st.catalog, plug)} (Contents votes {votes} recorded, not used)")
        return Status.SUCCESS


def exposure_choice(it: dict, conn: dict, multi: bool) -> str:
    """The choice key of one connector's exposure: exposed[<item>] for a one-connector part (the iteration 007 key),
    exposed[<item>.<connector>] for a part with several."""
    return f"exposed[{it['id']}.{conn['name']}]" if multi else f"exposed[{it['id']}]"


def stack_height(catalog: pt.Catalog, option: str) -> float:
    stack = catalog.instantiate(option)
    return pt.lookup_datum(stack.datums, "STACK_TOP").at[2] - pt.lookup_datum(stack.datums, "STACK_BOTTOM").at[2]


class ChooseStack(AssemblyStep):
    """Per module with stack options, gated by evidence in the text (ARCHITECTURE.md 7.10): an option has evidence when
    the request or an L1 names one of its aliases or states its stack height. One option with evidence is chosen by
    rule (no question); two or more are offered to the LLM (enum among them only); none: the catalogue default (the
    first listed option), flagged as an assumption."""

    def __init__(self, design, llm):
        super().__init__("ChooseStack", design, llm)

    def update(self) -> Status:
        st = self.state
        st.stage = "choose_stack"
        tol = st.rules.values["measure_tol"]
        for it in st.items:
            part = st.catalog.get(it.part)
            options = [o for o in part.data.get("mount", {}).get("stack_options", []) if o in st.catalog]
            if not options:
                continue
            heights = {o: stack_height(st.catalog, o) for o in options}
            evidence = {o: [dict(h, option=o) for h in text_evidence(st.texts, st.catalog.get(o).names, [heights[o]],
                                                                     tol)] for o in options}
            backed = [o for o in options if evidence[o]]
            name = f"stack[{it.id}]"
            if len(backed) == 1:
                pick = backed[0]
                choice(st, name, pick, "rule:text_evidence", evidence=evidence[pick])
            elif not backed:
                pick = options[0]
                st.assumptions.append(f"{name} = {pick}: the text names no mounting; catalogue default used")
                choice(st, name, pick, "rule:catalogue_default", evidence=[])
            else:
                words = [f"- {o}: {st.catalog.get(o).names[0]} (the {it.name} sits {heights[o]:g} mm above the board)"
                         for o in backed]
                prompt = (f"Request: {self.design.base_request or self.design.request}\n\n"
                          f"How is the {it.name} mounted on the board? Options:\n" + "\n".join(words))
                counts = tally(self.llm, prompt, ca.obj_schema({"stack": {"type": "string", "enum": backed}}),
                               "assy_stack", {"stack": backed})
                pick = majority(counts["stack"])
                ev = [h for o in backed for h in evidence[o]]
                if pick is None:
                    pick = backed[0]
                    st.assumptions.append(f"{name} = {pick}: no valid answer, first catalogue option with evidence used")
                    choice(st, name, pick, "rule:first_option", evidence=ev)
                else:
                    choice(st, name, pick, "llm", votes=dict(counts["stack"]), evidence=ev)
            it.stack = pick
        return Status.SUCCESS


BOARD_ROLE = "board"                 # the fastener use whose role words design_rules.json fastener_roles gives (C1)
CLAUSE_RE = re.compile(r"[,;:]\s*")  # clause breaks inside a sentence (board role evidence is clause-scoped, C1)


def board_screw_candidates(catalog: pt.Catalog) -> List[Tuple[float, str]]:
    """(thread, id) of every catalogue-complete fastener with pilot and thread fields: the screws that can hold a board
    in a printed pilot (ARCHITECTURE.md 7.13)."""
    out = []
    for pid in catalog.ids():
        part = catalog.get(pid)
        p = {k: v.get("default") for k, v in part.params.items()}
        if part.kind != "fastener" or not catalogue_complete(part) or p.get("pilot_diameter") is None \
                or p.get("thread_diameter") is None:
            continue
        out.append((float(p["thread_diameter"]), pid))
    return out


def clauses(texts: Sequence[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """(source, clause): every sentence of the texts split at its clause breaks (, ; :)."""
    return [(src, c.strip()) for src, text in texts for sent in sentences(text) for c in CLAUSE_RE.split(sent)
            if c.strip()]


def board_screw_choice(catalog: pt.Catalog, board: pt.PartInstance, rules, texts: Sequence[Tuple[str, str]] = (),
                       roles: Optional[Mapping[str, dict]] = None) -> dict:
    """The board screw rule (generalize delta 002 C1), among the catalogue-complete screws with pilot and thread fields
    (board_screw_candidates). A screw passes the board's mounting hole when thread + 2 x rules.given_hole_clearance_min
    <= hole + rules.measure_tol (the hole is a given datum, not one the design drills; ISO 273 clearance is for the holes
    the design makes). In order:
    1. role evidence (rule:text_evidence[board]): the screws the text names (text_evidence over their names) in a clause
       that also names the primary (its part.json names) or a role word (design_rules.json fastener_roles.board); the
       largest thread among those that pass. A named screw that does not pass is noted and skipped. Clause scope: a
       requirement sentence often names a second part's fastener and the board in different clauses.
    2. the datasheet (rule:interface_thread): the screw whose thread equals the primary's mount_holes `thread` (within
       rules.measure_tol), if it passes;
    3. the smallest thread that passes (rule:smallest_thread_through_board_hole), an assumption.
    Returns {part, by, evidence, notes}."""
    hole = pt.lookup_datum(board.datums, pt.mount_names(board.part)[0]).diameter
    tol = rules["measure_tol"]
    cands = board_screw_candidates(catalog)

    def passes(thread: float) -> bool:
        return hole is not None and thread + 2 * rules["given_hole_clearance_min"] <= hole + tol

    notes: List[str] = []
    words = list(((roles or {}).get(BOARD_ROLE) or {}).get("evidence", [])) + list(board.part.names)
    role_clauses = {(h["source"], h["quote"]) for h in text_evidence(clauses(texts), words)} if texts and words else set()
    named: Dict[str, List[dict]] = {}
    for thread, pid in cands:
        hits = [h for h in text_evidence(clauses(texts), catalog.get(pid).names) if (h["source"], h["quote"]) in
                role_clauses] if role_clauses else []
        if not hits:
            continue
        if passes(thread):
            named[pid] = hits
        else:
            notes.append(f"board fastener {pid} named but does not pass the Ø{hole:g} hole "
                         f"({hits[0]['source']}: \"{hits[0]['quote']}\")")
    if named:
        pick = max((t, pid) for t, pid in cands if pid in named)[1]
        return {"part": catalog.get(pick), "by": f"rule:text_evidence[{BOARD_ROLE}]", "evidence": named[pick],
                "notes": notes}
    thread = pt.interface_thread(board.part)
    if thread is not None:
        match = [(t, pid) for t, pid in cands if abs(t - thread) <= tol and passes(t)]
        if match:
            return {"part": catalog.get(min(match)[1]), "by": "rule:interface_thread", "evidence": [], "notes": notes}
        notes.append(f"the {board.part.id} datasheet thread M{thread:g} has no catalogue screw that passes the "
                     f"Ø{hole:g} hole")
    ok = [(t, pid) for t, pid in cands if passes(t)]
    return {"part": catalog.get(min(ok)[1]) if ok else None, "by": "rule:smallest_thread_through_board_hole",
            "evidence": [], "notes": notes}


def board_screw(catalog: pt.Catalog, board: pt.PartInstance, rules, texts: Sequence[Tuple[str, str]] = (),
                roles: Optional[Mapping[str, dict]] = None) -> Optional[pt.Part]:
    """The board screw part (board_screw_choice)."""
    return board_screw_choice(catalog, board, rules, texts, roles)["part"]


def hole_column_terms(st: "AssemblyState", board: pt.PartInstance) -> Dict[str, float]:
    """The two terms of the screw-head and seat column on each board hole (ARCHITECTURE.md 7.13): the keep-out the board
    declares round its mounting holes (HOLE.keepout_diameter, 0 when it declares none) and the room the chosen board
    screw needs (head diameter + 2 x rules.driver_clearance)."""
    holes = pt.lookup_datum(board.datums, pt.mount_names(board.part)[0])
    return {"board_keepout": float(holes.keepout_diameter or 0.0),
            "fastener": st.fasteners["fastener.board.head_diameter"] + 2 * st.rules.values["driver_clearance"]}


def hole_column_d(st: "AssemblyState", board: pt.PartInstance) -> float:
    """The column diameter: max(board HOLE.keepout_diameter, head + 2 x driver_clearance). Used by the placer (hole
    columns the contents keep off) and by the V-SEAT / V-HOLE-KO envelopes, so both read one rule."""
    return max(hole_column_terms(st, board).values())


def catalogue_complete(part: pt.Part) -> bool:
    """A fastener is catalogue-complete when no param of it must come from the request (generalize delta 001 C2): a bolt
    whose length comes from a stock list is not, until the fastener-chain length rule exists (GM3)."""
    return not part.request_params()


def lid_screw_choice(catalog: pt.Catalog, rules, texts: Sequence[Tuple[str, str]] = ()) -> dict:
    """The lid screw rule (generalize delta 001 C2): among the catalogue-complete fasteners with the lid fields
    (LID_FIELDS), the ones the text names (text_evidence over their aliases) win, the largest thread among them
    (rule:text_evidence); with none named, the largest-thread one (rule:largest_complete_screw, an assumption). A named
    fastener that is not catalogue-complete is skipped and reported. Its boss OD = max(setpoint(min_boss_od), pilot +
    2 x boss_wall_min, clearance + 2 x setpoint(min_ligament)): the lid pad round its clearance hole is the same column
    (ARCHITECTURE.md 7.12). Returns {part, by, evidence, skipped}."""
    ok, named, skipped_hits = [], {}, {}
    for pid in catalog.ids():
        part = catalog.get(pid)
        if part.kind != "fastener":
            continue
        hits = text_evidence(texts, part.names) if texts else []
        if not catalogue_complete(part):
            if hits:
                skipped_hits[pid] = hits
            continue
        p = {k: v.get("default") for k, v in part.params.items()}
        if any(p.get(k) is None for k in LID_FIELDS):
            continue
        ok.append((float(p["thread_diameter"]), pid))
        if hits:
            named[pid] = hits
    # a skipped fastener is reported only when the text names it apart from a complete one: an alias both share
    # ("m3 screw") in the same sentence is evidence for the complete fastener, not a request for the skipped one
    key = lambda h: (h["source"], h["quote"], h["match"])
    shared = {key(h) for hs in named.values() for h in hs}
    skipped = [pid for pid, hs in skipped_hits.items() if any(key(h) not in shared for h in hs)]
    pool = [o for o in ok if o[1] in named]
    if pool:
        pick = max(pool)[1]
        return {"part": catalog.get(pick), "by": "rule:text_evidence", "evidence": named[pick], "skipped": skipped}
    if ok:
        return {"part": catalog.get(max(ok)[1]), "by": "rule:largest_complete_screw", "evidence": [], "skipped": skipped}
    return {"part": None, "by": "", "evidence": [], "skipped": skipped}


def lid_screw(catalog: pt.Catalog, rules, texts: Sequence[Tuple[str, str]] = ()) -> Optional[pt.Part]:
    """The lid screw part (lid_screw_choice)."""
    return lid_screw_choice(catalog, rules, texts)["part"]


def fastener_values(use: str, part: pt.Part) -> Dict[str, float]:
    inst = pt.instantiate(part)
    return {f"fastener.{use}.{k}": float(v) for k, v in inst.params.items()}


NOT_STATED = "not_stated"            # the face-relation enum value that constrains nothing (C0)
NOT_STATED_MEANING = "the request does not say how these two connectors are placed relative to each other"
RELATION_LABEL = "assy_relation"


def relation_members(st: AssemblyState) -> List[dict]:
    """The exposed connectors a face relation can name (generalize delta 002 C0): every exposed connector of a content
    item (an item with quantity > 1 is one member: its copies share an edge by construction) and the primary's own
    exposed connectors (`fixed`: their wall follows from the primary's axis). Only connectors that mate a catalogue plug
    count, as in exposed_connectors."""
    out = []
    prim = primary_item(st)
    if prim is not None:
        for c in connector_list(st.catalog.get(prim["part"])):
            if c["name"] in prim.get("exposed_connectors", []) and c.get("mates") in st.catalog:
                out.append({"key": f"{PRIMARY}.{c['name']}", "item": PRIMARY, "connector": c["name"],
                            "part": prim["part"], "name": prim.get("name") or human_name(st.catalog, prim["part"]),
                            "fixed": True})
    for it in st.items:
        conns = connector_list(st.catalog.get(it.part))
        if not it.exposed or not conns:
            continue
        names = list(it.connectors) if it.connectors else [conns[0]["name"]]
        for c in conns:
            if c["name"] in names and c.get("mates") in st.catalog:
                out.append({"key": f"{it.id}.{c['name']}", "item": it.id, "connector": c["name"], "part": it.part,
                            "name": it.name or human_name(st.catalog, it.part), "fixed": False})
    return out


def relation_gate(st: AssemblyState, members: Sequence[dict]) -> List[dict]:
    """The pairs a face relation may constrain, each with its gated values (generalize delta 002 C0). Pair (A, B) may take
    relation v only when one sentence of the request or an L1 names both A's and B's parts (text_evidence over their
    part.json names) and one of v's evidence words (design_rules.json face_relations). A pair no choice can change (both
    members on one item: two connectors of the primary, or of one content part) is never gated. Relations the sensor has
    no rule for (assembly_checks.FACE_RELATIONS) are not offered. Returns [{a, b, values, evidence}] in member order."""
    vocab = {v: e for v, e in (st.rules.face_relations or {}).items() if v in ac.FACE_RELATIONS}
    if not vocab or len(members) < 2:
        return []

    def where(words: Sequence[str]) -> List[Tuple[str, str]]:
        return [(h["source"], h["quote"]) for h in text_evidence(st.texts, words)]

    named = {pid: set(where(st.catalog.get(pid).names)) for pid in {m["part"] for m in members}}
    said = {v: where(e["evidence"]) for v, e in vocab.items()}
    pairs = []
    for a, b in itertools.combinations(members, 2):
        if a["item"] == b["item"]:
            continue
        both = named[a["part"]] & named[b["part"]]
        values, evidence = [], []
        for v in vocab:
            quotes = [q for q in said[v] if q in both]
            if quotes:
                values.append(v)
                evidence += [{"source": s, "quote": q, "relation": v} for s, q in quotes]
        if values:
            pairs.append({"a": a, "b": b, "values": values, "evidence": evidence})
    return pairs


def relation_check_id(r: Mapping[str, Any]) -> str:
    return f"face_relation_{r['a']['key'].replace('.', '_')}_{r['b']['key'].replace('.', '_')}"


def member_connector(st: AssemblyState, m: Mapping[str, Any]) -> Optional[Tuple[lay.Placed, dict]]:
    """The placed connector of a relation member (the first copy of a content item), or None when it is not exposed."""
    for p, c in exposed_connectors(st):
        if c["name"] == m["connector"] and ((m["item"] == PRIMARY and p.role == "board") or p.item == m["item"]):
            return p, c
    return None


def add_relation_checks(st: AssemblyState, plan: ac.Plan) -> None:
    """face_relation_<A>_<B> (generalize delta 002 C0): every face relation the controller read unanimously, computed
    from the layout (the wall each member's connector axis faces). A controllable hard check: prescore removes the
    arrangements that break it; when no feasible arrangement meets it, every candidate ties on it and the package
    carries it failing, with the quoted text and the votes."""
    for r in st.relations:
        got = [member_connector(st, r[k]) for k in ("a", "b")]
        if any(g is None for g in got):
            continue
        walls = [wall_facing(lay.world_datum(p, c["axis"]).dir) for p, c in got]
        quote = r["evidence"][0]
        meaning = (st.rules.face_relations.get(r["value"]) or {}).get("meaning", r["value"])
        plan.add(relation_check_id(r), "face_relation", f"{r['a']['key']} and {r['b']['key']}: {meaning}, as the text "
                 f"states ({quote['source']}: \"{quote['quote']}\")", relation=r["value"], walls=walls,
                 members=[r["a"]["key"], r["b"]["key"]],
                 evidence={"quotes": list(r["evidence"]), "votes": dict(r["votes"]), "by": r["by"]},
                 parts=sorted({r["a"]["part"], r["b"]["part"]}))


class ArrangeContents(AssemblyStep):
    """LLM: the board edge each exposed item faces (voted enum). Python: millimetre placement (layout.py).

    ConfirmArrangement (ARCHITECTURE.md 7.6): Python enumerates the edge assignments in the LLM's vote
    order, prunes the infeasible ones (placer.place), groups the feasible ones into board-symmetry classes
    and asks p_yes once per class. p_yes is a ranking signal, never an absolute gate: when the vote
    winner's class ranks top it is accepted; otherwise one voted A/B question decides between the two.
    The stage fails only when no feasible assignment exists, and then it lists every candidate.

    Pre-score (ARCHITECTURE.md 7.11, the M11 slice of the 4.1 middle loop): every feasible candidate is first run
    through the downstream plant (prescore); only the candidates tied at the minimum controllable error reach the
    LLM, and a single survivor is a rule decision (rule:prescore). When nothing is feasible while a coverage-forced
    item is exposed, that item is reverted (rule:coverage_infeasible) and the placement runs once more."""

    def __init__(self, design, llm):
        super().__init__("ArrangeContents", design, llm)
        self.relation_record: Optional[dict] = None

    def request_text(self) -> str:
        return self.design.base_request or self.design.request

    def ask_relations(self, st: AssemblyState) -> dict:
        """The face-relation stage (generalize delta 002 C0), once per run, after the edge vote. Python gates the pairs
        (relation_gate); with none gated nothing is asked and the transcript is unchanged. Otherwise one voted question
        (RELATION_LABEL): the request, the gating sentences quoted (the 9B read "the same short end" as not_stated in 13
        of 15 samples without them, and as same in 15 of 15 with them; LEDGER iteration 002), then per gated pair an
        enum of its gated values plus NOT_STATED. A relation constrains only when
        every valid sample names the same value and it is not NOT_STATED (7.6: one noisy signal never vetoes alone); a
        split vote is recorded and constrains nothing. Constraints go to st.relations (face_relation checks) and to
        choices relation[<A>|<B>]. Returns the record for design.json arrange.relations."""
        pairs = relation_gate(st, relation_members(st))
        record: Dict[str, Any] = {"asked": [], "constraints": []}
        st.relations = []
        if not pairs:
            return record
        vocab = st.rules.face_relations
        keys = [f"pair_{k}" for k in range(1, len(pairs) + 1)]
        lines = "\n".join(f"- {k}: {pr['a']['name']} ({pr['a']['connector']} connector) and {pr['b']['name']} "
                          f"({pr['b']['connector']} connector)" for k, pr in zip(keys, pairs))
        used = [v for v in vocab if any(v in pr["values"] for pr in pairs)]
        meanings = "\n".join([f"- {v}: {vocab[v]['meaning']}" for v in used] + [f"- {NOT_STATED}: {NOT_STATED_MEANING}"])
        these = "these two cable connectors" if len(pairs) == 1 else "the two cable connectors of each pair"
        quotes = []                          # the gating sentences, quoted (implementer's measured refinement, see LEDGER)
        for k, pr in zip(keys, pairs):
            seen = []
            for e in pr["evidence"]:
                if e["quote"] not in seen:
                    seen.append(e["quote"])
                    quotes.append(f'- "{e["quote"]}"' if len(pairs) == 1 else f'- {k}: "{e["quote"]}"')
        prompt = (f"Request: {self.request_text()}\n\n"
                  f"Where the text relates them:\n" + "\n".join(quotes) + "\n\n"
                  f"{'Pair' if len(pairs) == 1 else 'Pairs'} of cable connectors:\n{lines}\n\n"
                  f"How does the request place {these} relative to each other?\n{meanings}")
        enums = {k: pr["values"] + [NOT_STATED] for k, pr in zip(keys, pairs)}
        schema = ca.obj_schema({k: {"type": "string", "enum": e} for k, e in enums.items()})
        counts = tally(self.llm, prompt, schema, RELATION_LABEL, enums)
        for k, pr in zip(keys, pairs):
            votes = {v: n for v, n in counts[k].items() if v is not None}
            value = next(iter(votes)) if len(votes) == 1 else None
            constraint = value if value not in (None, NOT_STATED) else None
            name = f"{pr['a']['key']}|{pr['b']['key']}"
            row = {"pair": name, "a": pr["a"]["key"], "b": pr["b"]["key"], "enum": enums[k], "votes": votes,
                   "constraint": constraint, "evidence": pr["evidence"]}
            record["asked"].append(row)
            if constraint is None:
                st.notes.append(f"arrange: relation {name}: votes {votes} are not a unanimous relation; no constraint")
                continue
            ev = [e for e in pr["evidence"] if e["relation"] == constraint] or pr["evidence"]
            st.relations.append({"a": pr["a"], "b": pr["b"], "value": constraint, "votes": votes, "evidence": ev,
                                 "by": "llm:relation"})
            record["constraints"].append({"pair": name, "value": constraint})
            choice(st, f"relation[{name}]", constraint, "llm:relation", votes=votes,
                   evidence=[{"source": e["source"], "quote": e["quote"]} for e in ev])
        return record

    def candidates(self, st: AssemblyState, placer: lay.Placer) -> dict:
        """The edge vote over the exposed items and the feasible placements in vote order (capped by
        rules.arrange_rank_max); infeasible assignments are pruned with their typed kind."""
        exposed = [it for it in st.items if it.exposed and st.catalog.get(it.part).data.get("connectors")]
        edges = placer.edges
        sides = list(edges)
        voted = False
        if exposed:
            words = "\n".join(f"- {s}: {edges[s]['words']}" for s in sides)
            items = "\n".join(f"- {it.id}: {it.name} x{it.quantity} ({facing_connector(st, it)} connector)"
                              for it in exposed)
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
            if self.relation_record is None:          # once per run, even when the placement runs twice
                self.relation_record = self.ask_relations(st)
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
        return {"exposed": exposed, "counts": counts, "voted": voted, "cands": cands, "pruned": pruned,
                "truncated": truncated, "cap": cap}

    def revert_coverage(self, st: AssemblyState, pruned: Sequence[dict]) -> List[str]:  # noqa: C901
        """No feasible arrangement while a coverage-forced item is exposed (7.11): revert every such item to unexposed,
        mark its coverage row and choice (rule:coverage_infeasible). Returns the reverted item ids. Finite: the
        reduced set holds no coverage-forced item, so it runs at most once."""
        kinds = sorted({c["kind"] for c in pruned})
        reason = f"no feasible arrangement with it exposed: {', '.join(kinds)}"
        reverted = []
        for it in st.contents:
            if it.get("exposed_by") != COVERAGE_RULE:
                continue
            forced = list(it.get("coverage_connectors", []))
            it["exposed_connectors"] = [c for c in it.get("exposed_connectors", []) if c not in forced]
            it["exposed"] = bool(it["exposed_connectors"])
            it["exposed_by"] = COVERAGE_INFEASIBLE
            for item in st.items:
                if item.id == it["id"]:
                    item.exposed = it["exposed"]
                    item.connectors = list(it["exposed_connectors"])
            for row in st.coverage:
                if row["item"] == it["id"]:
                    row.update(resolved="unexposed", reason=reason, by=COVERAGE_INFEASIBLE)
            conns = connector_list(st.catalog.get(it["part"]))
            for conn in [c for c in conns if c["name"] in forced]:
                key = exposure_choice(it, conn, len(conns) > 1)
                old = st.choices.get(key, {})
                choice(st, key, False, COVERAGE_INFEASIBLE, reason=reason,
                       evidence=old.get("evidence", []), overrides=old.get("overrides", {}))
            reverted.append(it["id"])
        if reverted:
            st.notes.append(f"coverage: {', '.join(reverted)} reverted to unexposed ({reason}); placing once more "
                            "(reported as a failing text_coverage check)")
        return reverted

    def update(self) -> Status:
        st = self.state
        st.stage = "arrange_contents"
        self.relation_record = None
        st.relations = []
        board_item = primary_item(st)
        board_inst = st.catalog.instantiate(board_item["part"], board_item["params"])
        pick = board_screw_choice(st.catalog, board_inst, st.rules.values, st.texts, st.rules.fastener_roles)
        for note in pick["notes"]:
            st.notes.append(f"arrange: {note}")
        screw = pick["part"]
        if screw is None:
            return self.fail(f"no catalogue screw passes the board's mounting holes (primary {board_item['part']})")
        st.fasteners.update(fastener_values("board", screw))
        choice(st, "fastener[board]", screw.id, pick["by"],
               **({"evidence": [{"source": h["source"], "quote": h["quote"]} for h in pick["evidence"]]}
                  if pick["evidence"] else {}))
        if pick["by"] == "rule:smallest_thread_through_board_hole":
            st.assumptions.append(f"fastener[board] = {screw.id}: the text names no board screw and the "
                                  f"{board_item['part']} datasheet gives no thread; the smallest catalogue screw that "
                                  "passes the board's mounting holes is used")
        board = lay.Placed(PRIMARY, board_item["part"], dict(board_item["params"]), 0.0, 0.0, 0.0, 0.0, "",
                           role="board", inst=board_inst)
        for c in board_inst.connectors:      # the primary's own connectors: the wall follows from the axis, no choice
            if c["name"] in board_item.get("exposed_connectors", []):
                axis = pt.lookup_datum(board_inst.datums, c["axis"]).dir
                choice(st, f"wall[{PRIMARY}.{c['name']}]", wall_facing(axis), "rule:fixed_by_primary")
        terms = hole_column_terms(st, board_inst)
        column_d = max(terms.values())
        st.notes.append(f"hole columns: Ø{column_d:g} = max(board HOLE.keepout_diameter {terms['board_keepout']:g}, "
                        f"{screw.id} head + 2 x rules.driver_clearance {terms['fastener']:g}) (rule:hole_column_d)")
        placer = lay.Placer(st.catalog, board, st.rules.values, column_d, st.spec["keepout_above"])
        got = self.candidates(st, placer)
        if not got["cands"] and self.revert_coverage(st, got["pruned"]):
            got = self.candidates(st, placer)
        exposed, counts, voted = got["exposed"], got["counts"], got["voted"]
        cands, pruned, truncated, cap = got["cands"], got["pruned"], got["truncated"], got["cap"]
        st.arrange = {"candidates": [], "classes": 0, "truncated": truncated, "decision": None}
        if self.relation_record and self.relation_record["asked"]:
            st.arrange["relations"] = self.relation_record
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
        for c in cands:                      # Python's error first (7.11): the LLM ranks only the ties
            c["prescore"] = prescore(st, c, placer)
        keep = prescore_survivors(cands)
        survivors = [cands[i] for i in keep]
        filtered = [{"assignment": dict(c["assignment"]), "failing": list(c["prescore"]["failing"]),
                     "key": c["prescore"]["key"], "error": c["prescore"]["error"]}
                    for i, c in enumerate(cands) if i not in keep]
        for f in filtered:
            st.notes.append(f"arrange: {f['assignment']} removed by prescore (controllable failures: "
                            f"{', '.join(f['failing']) or f['error']})")
        prefix = "prescore+" if filtered else ""
        st.arrange.update(prescored=len(cands), filtered=filtered)
        if len(survivors) == 1:
            chosen, by = survivors[0], "rule:prescore"
            confirmed = {"value": dict(chosen["assignment"]), "by": by, "p_yes": None, "rank": 1,
                         "margin_to_next": None, "prescore": chosen["prescore"]["key"]}
            n_classes, n_sym = 0, None
        else:
            notes: List[str] = []
            symmetries = lay.board_symmetries(board_inst, st.rules.values["measure_tol"], notes)
            st.notes += [f"arrange: {n}" for n in notes]
            classes = self.rank_candidates(survivors, symmetries)
            pick, by, extra = self.decide(survivors, classes, 0 if voted else None)
            by = prefix + by
            chosen = survivors[pick]
            score = classes[chosen["class"]]["p_yes"]
            ranked = sorted(range(len(classes)), key=lambda c: -classes[c]["p_yes"])
            others = [classes[c]["p_yes"] for c in ranked if c != chosen["class"]]
            margin = None if not others else score - others[0]
            confirmed = dict({"value": dict(chosen["assignment"]), "by": by, "p_yes": score,
                              "rank": ranked.index(chosen["class"]) + 1, "margin_to_next": margin,
                              "prescore": chosen["prescore"]["key"]}, **extra)
            if score < EVEN_ODDS:
                nxt = f"{others[0]:.2f}" if others else "none"
                st.assumptions.append(f"arrangement accepted by rank: the controller's absolute confidence was low "
                                      f"(p_yes {score:.2f}; next class {nxt})")
            n_classes, n_sym = len(classes), len(symmetries)
        for c in survivors:
            st.history.append(dict({"stage": "confirm_arrangement"}, **self.record(c, chosen=c is chosen)))
        rows = sorted([self.record(c, chosen=c is chosen) for c in survivors], key=lambda r: -r["p_yes"])
        rows += [dict(self.record(c, chosen=False), outcome="filtered") for i, c in enumerate(cands) if i not in keep]
        st.arrange.update(candidates=rows + pruned, classes=n_classes, decision=by)
        if n_sym is not None:
            st.arrange["symmetries"] = n_sym
        return self.accept(chosen["layout"], chosen["assignment"], placer, "llm" if by != "rule:prescore" else by,
                           counts=counts, confirmed=confirmed)

    @staticmethod
    def record(c: dict, chosen: bool) -> dict:
        ps = c.get("prescore")
        return {"assignment": dict(c["assignment"]), "outcome": "scored", "class": c.get("class"),
                "words": c["words"], "votes": c["votes"], "p_yes": c.get("p_yes", 0.0), "asked": c.get("asked", False),
                "chosen": chosen, "prescore": None if ps is None else {k: ps[k] for k in ("key", "failing",
                                                                                            "uncontrollable", "error")}}

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
        for k, v in assign.items():
            choice(st, f"edge[{k}]", v, by, **({"votes": dict(extra["counts"][k])} if "counts" in extra else {}))
        if extra.get("confirmed"):
            st.choices["arrangement_confirmed"] = extra["confirmed"]
        for note in result.notes:
            st.notes.append(f"arrange: {note}")
        accept_layout(st, result, placer)
        for nid in st.grid_report.get("exempt", []):
            st.assumptions.append(grid_exempt_text(st.grid_report["parts"][nid], nid))
        self.logger.info("arrangement: " + lay.describe(result, st.items))
        return Status.SUCCESS


def accept_layout(st: AssemblyState, result: lay.Layout, placer: lay.Placer) -> None:
    """The state half of accepting an arrangement (shared by ArrangeContents.accept and prescore, 7.11): the placed
    layout, the frame, the grid sensor's report and a fresh feature graph holding the reference parts. No logging."""
    st.placed = result
    st.frame = {"origin": "board min corner on its top surface", "x": "along the board's longest edge",
                "z": "up", "edges": result.edges}
    st.layout = {p.node_id: p.to_json() for p in result.placed}
    st.grid_report = placer.grid_report(result.placed, result.snaps)
    st.layout_grid_residual = st.grid_report["max"]        # exempt parts excluded, as grid_conformance does (C2)
    st.layout_grid_exempt = list(st.grid_report["exempt"])
    st.layout_grid_residual_all = placer.grid_residual(result.placed)
    st.graph = fg.FeatureGraph()
    for p in result.placed:
        st.graph.add(fg.Node(p.node_id, "reference", "part", dict(p.params),
                             fg.Pose(offset=(p.x, p.y, p.z), rot_z=p.rot_z), part=p.part,
                             source=f"layout:{p.role}"))


def facing_connector(st: AssemblyState, it: lay.Item) -> str:
    """The name of the connector an exposed item turns toward its edge: its first exposed connector."""
    conns = connector_list(st.catalog.get(it.part))
    return next((c["name"] for c in conns if it.connectors and c["name"] in it.connectors), conns[0]["name"])


def exposed_connectors(st: AssemblyState) -> List[Tuple[lay.Placed, dict]]:
    """Every exposed connector of every placed part (generalize delta 001 C1): each exposed connector of a content part
    (a one-connector part: its connector, as before) and the primary's own exposed connectors."""
    items = {it.id: it for it in st.items if it.exposed}
    prim = primary_item(st) or {}
    out = []
    for p in st.placed.placed:
        if p.role == "board":
            names = list(prim.get("exposed_connectors", []))
        elif p.role == "content" and p.item in items:
            it = items[p.item]
            names = list(it.connectors) if it.connectors else [c["name"] for c in p.inst.connectors[:1]]
        else:
            continue
        out += [(p, c) for c in p.inst.connectors if c.get("name") in names and c.get("mates") in st.catalog]
    return out


def build_envelopes(st: AssemblyState) -> Optional[str]:
    """V- volumes from the placed datums (parts.py generators); lengths from spec and rules only. Shared by
    BuildEnvelopes and prescore (7.11); returns an error message or None."""
    r, s = st.rules.values, st.spec
    board = st.placed.get(PRIMARY)
    for p, c in exposed_connectors(st):
        world = {"mouth": lay.world_datum(p, c["mouth"]), "axis": lay.world_datum(p, c["axis"])}
        try:
            nodes = pt.plug_sweep(world, st.catalog.instantiate(c["mates"]), 0.0, r["plug_travel"],
                                  prefix=f"{conn_key(p, c)}_plug")
        except pt.PartError as e:
            return str(e)
        for n in nodes:
            st.graph.add(n)
    for n in pt.board_keepout(board.inst, board.pose, s["keepout_above"], s["keepout_below"], prefix="board"):
        st.graph.add(n)
    hole_name, seat_name, top_name = primary_mount(st)
    holes = lay.world_datum(board, hole_name)
    top, bottom = lay.world_datum(board, top_name).at[2], lay.world_datum(board, seat_name).at[2]
    seat_d = hole_column_d(st, board.inst)
    for i in range(len(holes.at)):
        anchor = f"{PRIMARY}.{hole_name}[{i}]"
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
    return None


class BuildEnvelopes(AssemblyStep):
    """V- volumes from the placed datums (parts.py generators); lengths from spec and rules only."""

    def __init__(self, design):
        super().__init__("BuildEnvelopes", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "build_envelopes"
        err = build_envelopes(st)
        return self.fail(err) if err else Status.SUCCESS


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
#   slots      the spec slots the envelope's size comes from (the L1 trace, ARCHITECTURE.md 7.10); the catalogue parts
#              a check concerns are its envelope nodes' `part` (plug sweeps, module envelopes)
KEEP_OUTS: Dict[str, Dict[str, Any]] = {
    "module_envelope": {"plan": None, "z": None, "clearance": "rules.part_to_wall", "group": True, "type": "inside",
                        "check_id": "clear_{group}",
                        "text": "{group} (the module and its stack parts) lies inside the closed enclosure, at least "
                                "{c:g} mm from every printed surface and from the outside"},
    "keepout_top": {"plan": None, "z": "z1", "clearance": 0.0, "check_id": "clear_keepout_top", "slots": ("keepout_above",),
                    "text": "nothing printed inside the component keep-out above the board"},
    "keepout_bottom": {"plan": None, "z": "z0", "clearance": 0.0, "minus": "seats", "check_id": "clear_keepout_bottom",
                       "slots": ("keepout_below",),
                       "text": "nothing printed inside the solder-side keep-out, except standoffs in the seat columns"},
    "hole_keepout": {"plan": "self", "z": None, "clearance": 0.0, "check_id": "clear_{id}", "slots": ("keepout_above",),
                     "text": "nothing printed inside the screw-head column {id} (the larger of the board's mounting-hole "
                             "keep-out and head + driver clearance, from the board top to the component keep-out height)"},
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
    board = st.placed.get(PRIMARY)
    hole_name, _, top_name = primary_mount(st)
    holes = lay.world_datum(board, hole_name)
    top = lay.world_datum(board, top_name).at[2]
    return [pt.column(holes, i, r["driver_diameter"], top, "base.split + rules.driver_reach", "driver",
                      prefix="driver", anchor=f"{PRIMARY}.{hole_name}[{i}]") for i in range(len(holes.at))]


SHELL = ("tray_lid", "screws")       # the one archetype + closure the derivation rules build (ARCHITECTURE.md 4.3)


def archetype_gate(st: AssemblyState) -> Tuple[List[Tuple[str, str]], str]:
    """(feasible (archetype, closure) pairs, the typed reason when there are none). tray_lid is feasible only when (a)
    the primary offers a mount_holes interface and (b) the request or an L1 names one of design_rules.json
    archetypes.tray_lid.evidence (text_evidence), so a fixture or a mount never gets a box (generalize delta 001 C4)."""
    prim = primary_item(st)
    pid = prim["part"] if prim else None
    if pid is None or pt.mount_interface(st.catalog.get(pid)) is None:
        return [], f"not implemented: archetype (primary {pid}; no {pt.MOUNT_HOLES} interface)"
    words = list((st.rules.archetypes.get(SHELL[0]) or {}).get("evidence", []))
    hits = text_evidence(st.texts, words) if words else []
    if not hits:
        return [], (f"not implemented: archetype (primary {pid}; no shell evidence; candidates for GM5: plate / "
                    "bracket / block / cradle)")
    return [SHELL], ""


def feasible_archetypes(st: AssemblyState) -> List[Tuple[str, str]]:
    """(archetype, closure) pairs the derivation rules can build for this request (archetype_gate)."""
    return archetype_gate(st)[0]


def choose_archetype_rule(st: AssemblyState) -> Optional[str]:
    """The rule half of ChooseArchetype (shared with prescore, 7.11): one feasible archetype is recorded as a rule
    choice; with two or more, the current choice holds, else the first (prescore never asks the LLM)."""
    feasible, reason = archetype_gate(st)
    options = ["+".join(o) for o in feasible]
    if not options:
        return reason or "no feasible archetype"
    if len(options) == 1:
        choice(st, "archetype", options[0], "rule:only_feasible")
    elif st.choices.get("archetype", {}).get("value") not in options:
        choice(st, "archetype", options[0], "rule:first_option")
    return None


class ChooseArchetype(AssemblyStep):
    def __init__(self, design, llm):
        super().__init__("ChooseArchetype", design, llm)

    def update(self) -> Status:
        st = self.state
        st.stage = "choose_archetype"
        options, _ = archetype_gate(st)
        if len(options) <= 1:
            err = choose_archetype_rule(st)
            return self.fail(err) if err else Status.SUCCESS
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
    the solder-side keep-out or lower, so every standoff holds its pilot over rules.min_feature of floor (delta 002 C2);
    top at the component keep-out (or the tallest part plus the headroom). Every
    one-sided bound carries rules.design_margin (setpoint inside the band; the checks keep the limits).
    Every size is an expression, so a spec or board change re-derives it (the size-leak fix)."""
    refs = [n.id for n in st.graph.references()]
    axes = plan_axes(st)
    m = "rules.design_margin"
    _, seat, top = primary_mount(st)
    # the floor also holds every standoff's pilot over rules.min_feature of floor (generalize delta 002 C2, RC-B3):
    # pilot_depth_standoff_* (depth <= seat - z0 + floor - min_feature) then holds by construction
    pilot = f"{PRIMARY}.{seat}.z - ({pilot_depth('board', st)}) - rules.min_feature + floor - {m}"

    def bound(fn: str, axis: str, sign: str) -> str:
        terms = [f"{_fold(fn, [f'{r}.bbox.{fn}_{axis}' for r in refs])} {sign} spec.board_clearance {sign} {m}"]
        terms += [f"{a}.{axis} {sign} {_fold('max', ds)}/2 {sign} {m}" for a, ds in axes.items()]
        return _fold(fn, terms)

    p = {
        "x0": bound("min", "x", "-"), "x1": bound("max", "x", "+"),
        "y0": bound("min", "y", "-"), "y1": bound("max", "y", "+"),
        "z0": f"min({PRIMARY}.{seat}.z - spec.keepout_below - {m}, {pilot})",
        "z1": f"max({PRIMARY}.{top}.z + spec.keepout_above + {m}, "
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
    key = conn_key(p, conn)
    plugs = [n for n in st.graph if n.kind == "envelope" and n.id.startswith(f"{key}_plug_")]
    crossing = [n for n in plugs if res.params[n.id]["s0"] < s_out and res.params[n.id]["s1"] > s_in]
    if not crossing:
        raise ValueError(f"{p.node_id}: no plug primitive crosses wall {side}")
    w = f"{_fold('max', [f'{n.id}.cw' for n in crossing])} + 2*(rules.plug_to_opening + rules.design_margin)"
    h = f"{_fold('max', [f'{n.id}.ch' for n in crossing])} + 2*(rules.plug_to_opening + rules.design_margin)"
    m = f"{p.node_id}.{conn['mouth']}"
    xyz = "xyz"[i]
    cid = f"{key}_cut"
    sec = crossing_section(res, crossing, 1 - i, mouth.at)
    if sec["offset"] and all(n.primitive == "cylinder" for n in crossing):
        raise ValueError(f"{p.node_id}: round plug primitives off the connector axis are not supported")
    if sec["offset"]:
        # generalize delta 002 D1: plug primitives whose section is not centred on the mouth (a card's access zone
        # above its axis): the box opening is centred on, and sized by, the union of their sections
        pad = "2*(rules.plug_to_opening + rules.design_margin)"
        w, h = f"{sec['w']!r} + {pad}", f"{sec['h']!r} + {pad}"
        centre = f"cavity.{bound} {'+' if sign > 0 else '-'} cavity.wall/2 - {m}.{xyz}"
        offset = [0, 0, f"{sec['dz']!r} - z/2"]
        offset[i], offset[1 - i] = centre, f"{sec['dt']!r}"
        params = {"x": "cavity.wall + 2*rules.cut_overrun", "y": w, "z": h, "top": f"{m}.z + {sec['dz']!r} + z/2",
                  "cw": w, "ch": h}
        node = fg.Node(cid, "cut", "box", params, fg.Pose(at=m, offset=tuple(offset), rot_z=lay.angle_of(u)),
                       body="base", role="port_cut", source=f"rule:connector_to_cut({p.node_id}.{conn['name']})")
        node.wall, node.crossing, node.env = side, [n.id for n in crossing], (sec["w"], sec["h"])
        return node, side
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
    node.env = (max(res.params[n.id]["cw"] for n in crossing), max(res.params[n.id]["ch"] for n in crossing))
    return node, side


def crossing_section(res: fg.Resolved, crossing: Sequence[fg.Node], t: int, mouth: Sequence[float]) -> dict:
    """The union of the crossing plug primitives' sections in the wall plane (generalize delta 002 D1): its width `w`
    along world axis t and height `h` along Z, and its centre's offset from the mouth (dt, dz). `offset` is False when
    every section is centred on the connector axis (every catalogue cable plug), so the opening keeps the iteration 002
    expressions. A box envelope's pose is its section centre in plan with its base at Z; a cylinder's is a point of its
    axis."""
    lo_t, hi_t, lo_z, hi_z = [], [], [], []
    for n in crossing:
        q, prm = res.poses[n.id][:3, 3], res.params[n.id]
        ct, cz = float(q[t]), float(q[2]) + (prm["z"] / 2 if n.primitive == "box" else 0.0)
        lo_t.append(ct - prm["cw"] / 2)
        hi_t.append(ct + prm["cw"] / 2)
        lo_z.append(cz - prm["ch"] / 2)
        hi_z.append(cz + prm["ch"] / 2)
    w, h = max(hi_t) - min(lo_t), max(hi_z) - min(lo_z)
    dt, dz = (max(hi_t) + min(lo_t)) / 2 - float(mouth[t]), (max(hi_z) + min(lo_z)) / 2 - float(mouth[2])
    tol = 1e-6
    centred = abs(dt) <= tol and abs(dz) <= tol and abs(w - max(res.params[n.id]["cw"] for n in crossing)) <= tol \
        and abs(h - max(res.params[n.id]["ch"] for n in crossing)) <= tol
    return {"w": w, "h": h, "dt": dt, "dz": dz, "offset": not centred}


def setpoint(limit_expr: str) -> str:
    """The derivation target for a one-sided minimum: limit + rules.design_margin (ARCHITECTURE.md 7.7, 7.9).

    Used at every one-sided-minimum derivation, so no derived value sits exactly on its limit (a rounding or
    tessellation change would flip it): one-sided clearances (cavity bounds, plug openings: written inline in
    derive_cavity / derive_port_cut), pilot depths (fastener min_engagement), standoff and boss outside
    diameters (fastener min_boss_od), the lid lip's engagement (rules.lip_engagement) and the ligaments round
    openings (rules.min_ligament: the corner column round the lid clearance hole, the split over port-cut tops;
    7.12). The checks keep the limits (pilot_engagement_*, boss_od_*, lip_engagement, ligament_*)."""
    expr = str(limit_expr).strip()
    if any(ch in expr for ch in " +-*/"):
        expr = f"({expr})"
    return f"{expr} + rules.design_margin"


PILOT_USES = {"standoff": "board", "boss": "lid"}   # the fastener use whose pilot each support role holds


def clamped_plate(use: str, st: AssemblyState) -> str:
    """The plate a fastener clamps before it enters its pilot (generalize delta 002 C2), as an expression: the board
    screw passes the primary between its mount_holes `seat` and `top` planes; the lid screw passes the lid plate
    (lid.z, which is also the lid pad's height)."""
    if use == "board":
        _, seat, top = primary_mount(st)
        return f"{PRIMARY}.{top}.z - {PRIMARY}.{seat}.z"
    return "lid.z"


def pilot_depth(use: str, st: AssemblyState) -> str:
    """The pilot depth of a fastener use, the one expression the pilot nodes and the cavity floor read (generalize delta
    002 C2, RC-B2): setpoint(max(fastener.<use>.min_engagement, fastener.<use>.length - clamped plate)). A catalogue
    screw of length L through a clamped plate t protrudes L - t; a shallower pilot would bottom the screw before its
    head seats. A fastener with no `length` keeps setpoint(min_engagement)."""
    eng = f"fastener.{use}.min_engagement"
    if f"fastener.{use}.length" not in st.fasteners:
        return setpoint(eng)
    return setpoint(f"max({eng}, fastener.{use}.length - ({clamped_plate(use, st)}))")


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
    split_terms = [f"cavity.z1 + {engagement}"] + [f"{n.id}.top + {setpoint('rules.min_ligament')}" for n in cuts]
    g.add(fg.Node("base", "body", "shell", {
        "wall": "cavity.wall", "floor": "cavity.floor", "split": _fold("max", split_terms),
        "x": "cavity.x + 2*wall", "y": "cavity.y + 2*wall", "z": "split - cavity.z0 + floor", "open_top": 1},
        fg.Pose(offset=("cavity.cx", "cavity.cy", "cavity.z0 - floor")), role="tray",
        source="rule:tray_lid.base", color=fg.BODY_COLORS[0]))
    for n in driver_columns(st):
        g.add(n)
    hole_name, seat_name, _ = primary_mount(st)
    seat = f"{PRIMARY}.{seat_name}.z"
    holes = lay.world_datum(st.placed.get(PRIMARY), hole_name)
    for i in range(len(holes.at)):
        hole = f"{PRIMARY}.{hole_name}[{i}]"
        g.add(fg.Node(f"standoff_{i + 1}", "add", "cylinder", {
            "d": f"max(fastener.board.pilot_diameter + 2*rules.standoff_wall_min, "
                 f"{setpoint('fastener.board.min_boss_od')})",
            "h": f"{seat} - cavity.z0 + base.floor", "top": seat,
            "height": f"{seat} - cavity.z0"},
            fg.Pose(at=hole, offset=(0, 0, f"cavity.z0 - base.floor - {hole}.z")), body="base", role="standoff",
            source="rule:mount_hole_to_standoff"))
        g.add(fg.Node(f"standoff_{i + 1}_pilot", "cut", "cylinder", {
            "d": "fastener.board.pilot_diameter", "h": "depth + rules.cut_overrun",
            "depth": pilot_depth("board", st)},
            fg.Pose(at=hole, offset=(0, 0, f"{seat} - depth - {hole}.z")),
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
            "d": f"max({setpoint('fastener.lid.min_boss_od')}, fastener.lid.pilot_diameter + 2*rules.boss_wall_min, "
                 f"fastener.lid.clearance_diameter + 2*({setpoint('rules.min_ligament')}))",
            "ax": f"{cx} {'-' if sx < 0 else '+'} {DIAGONAL!r}*(d/2 + spec.board_clearance)",
            "ay": f"{cy} {'-' if sy < 0 else '+'} {DIAGONAL!r}*(d/2 + spec.board_clearance)",
            "h": "base.split - cavity.z0 + base.floor"},
            fg.Pose(offset=("ax", "ay", "cavity.z0 - base.floor")), body="base", role="boss",
            source="rule:lid_to_fastening.corner_pilaster"))
        g.add(fg.Node(f"{boss}_pilot", "cut", "cylinder", {
            "d": "fastener.lid.pilot_diameter", "h": "depth + rules.cut_overrun",
            "depth": pilot_depth("lid", st)},
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


def derive(st: AssemblyState) -> Optional[str]:
    """DeriveFeatures on a state (shared with prescore, 7.11): the lid screw, the feature rules, resolve. Returns an
    error message or None."""
    try:                                 # part errors are contained: a note and a package, never a traceback (C2)
        pick = lid_screw_choice(st.catalog, st.rules.values, st.texts)
        for pid in pick["skipped"]:
            note = (f"derive: the text names {pid}, which is not catalogue-complete (a size comes from the request); "
                    "skipped for the lid (its length rule is GM3)")
            if note not in st.notes:
                st.notes.append(note)
        screw = pick["part"]
        if screw is None:
            return "no catalogue-complete screw can hold the lid"
        st.fasteners.update(fastener_values("lid", screw))
        choice(st, "fastener[lid]", screw.id, pick["by"],
               evidence=[{"source": h["source"], "quote": h["quote"]} for h in pick["evidence"]])
        if pick["by"] == "rule:largest_complete_screw":
            text = (f"fastener[lid] = {screw.id}: the text names no lid screw; the largest-thread catalogue-complete "
                    "screw is used")
            if text not in st.assumptions:
                st.assumptions.append(text)
        derive_features(st)
        st.resolved = resolve(st)
    except (ValueError, KeyError, fg.ExprError, pt.PartError) as e:
        return f"derivation failed: {e}"
    return None


class DeriveFeatures(AssemblyStep):
    def __init__(self, design):
        super().__init__("DeriveFeatures", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "derive_features"
        err = derive(st)
        return self.fail(err) if err else Status.SUCCESS


# ---------------------------------------------------------------------------
# Pre-scored discrete alternatives (ARCHITECTURE.md 4.1 middle loop, 7.11): the downstream plant on a scratch state
# ---------------------------------------------------------------------------

SCRATCH_FIELDS = ("choices", "fasteners", "notes", "assumptions", "history", "layout", "coverage", "stl_source",
                  "solids", "frame", "grid_report")   # the fields later stages mutate in place (graph is rebuilt)


def scratch_state(st: AssemblyState) -> AssemblyState:
    """A shallow copy of the blackboard with fresh copies of every field the downstream stages mutate; the catalogue,
    the rules and the contents are shared (read-only downstream)."""
    sc = copy.copy(st)
    for name in SCRATCH_FIELDS:
        setattr(sc, name, copy.copy(getattr(st, name)))
    sc.graph, sc.resolved, sc.plan = None, None, None
    return sc


def controllable(results: Sequence[cc.CheckResult]) -> Tuple[List[cc.CheckResult], List[cc.CheckResult]]:
    """(controllable failures, uncontrollable failures): a failing check whose evidence carries a typed `conflict`
    (grid grid_extent / blocked / no_pin_data, coverage) is the requirement loop's (4.4 item 3), never a discrete
    choice's."""
    failing = [r for r in results if not r.passed]
    return [r for r in failing if not r.evidence.get("conflict")], [r for r in failing if r.evidence.get("conflict")]


def prescore(st: AssemblyState, cand: dict, placer: lay.Placer) -> dict:
    """Python's error for one arrangement candidate before any LLM preference is used (7.11): accept it on a scratch
    state, run the downstream plant (envelopes, archetype rule, derive, manifold solids, build_plan, run_plan) and
    return {key (cc.ErrorKey over the controllable failures), failing, uncontrollable, checked (every check id run),
    error}. Pure: no LLM, no OpenSCAD, no files; `st` is left unchanged."""
    sc = scratch_state(st)
    try:
        accept_layout(sc, cand["layout"], placer)
        err = build_envelopes(sc) or choose_archetype_rule(sc) or derive(sc)
        if err is None:
            sc.solids = {b: fg.body_solid(sc.graph, b, sc.resolved) for b in sc.graph.bodies()}
            results = ac.run_plan(build_plan(sc), sc.solids)
    except (ValueError, KeyError, fg.ExprError, pt.PartError) as e:
        err = f"{type(e).__name__}: {e}"
    if err is not None:
        return {"key": {"hard_failures": math.inf, "violation": math.inf, "soft": 0.0}, "failing": [],
                "uncontrollable": [], "checked": [], "error": err}
    ctrl, unctrl = controllable(results)
    return {"key": cc.error_key(ctrl).to_dict(), "failing": [r.check_id for r in ctrl],
            "uncontrollable": [r.check_id for r in unctrl], "checked": [r.check_id for r in results], "error": None}


def prescore_survivors(cands: Sequence[dict]) -> List[int]:
    """Indices of the candidates whose controllable error ties the minimum (cc.strictly_better with
    cascade.ACCEPT_EPS, so near-equal violations tie): only a strict difference removes a candidate (4.1)."""
    keys = [cc.ErrorKey(c["prescore"]["key"]["hard_failures"], c["prescore"]["key"]["violation"]) for c in cands]
    best = keys[0]
    for k in keys[1:]:
        if cc.strictly_better(k, best, eps=cascade.ACCEPT_EPS):
            best = k
    return [i for i, k in enumerate(keys) if not cc.strictly_better(best, k, eps=cascade.ACCEPT_EPS)]


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
    plugs = {f"{conn_key(p, c)}_plug": (p, c) for p, c in exposed_connectors(st)}
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
            concerns = sorted({st.graph.nodes[i].part for i in plan.sources[vol] if st.graph.nodes[i].part})
            plan.add(row["check_id"].format(**words), row.get("type", "clear_of"), row["text"].format(**words),
                     slots=row.get("slots", ()), parts=concerns, **args)


def grow_exemptions(st: AssemblyState, plan: ac.Plan) -> None:
    """ARCHITECTURE.md 7.8: a contact exemption (`minus`) on a clear_of / inside check with clearance c > 0 is the
    exempt nodes grown by c (volume "<minus>@<c>"), so a body touching legally inside the exemption is measured
    against the next real surface, not against the exemption's rim. With c = 0 the exemption is unchanged. The grown
    polygon is inscribed (iteration 010): a subtracted exemption errs against the design only when it is not larger
    than its circle."""
    g, res = st.graph, st.resolved
    for sp in plan.specs:
        a = sp["args"]
        if sp["type"] not in ("clear_of", "inside") or not a.get("minus") or a["clearance"] <= 0:
            continue
        m, c = a["minus"], float(a["clearance"])
        name = f"{m}@{c:g}"
        if name not in plan.volumes:
            plan.volumes[name] = ac.union([fg.grown_solid(g.nodes[i], res, c, inscribed=True) for i in plan.sources[m]])
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


GRID_CONFLICT_KINDS = ("grid_extent", "blocked", "no_pin_data")   # a question for Robin, not for agent code


def grid_exempt_text(row: Mapping[str, Any], nid: str) -> str:
    """The assumption a pin_pattern part carries (ARCHITECTURE.md 7.13): it is exempt from the grid rule."""
    return (f"{nid}: mounted through enlarged holes; its pin pattern meets no grid position (best "
            f"{row['best_any']:.3f} mm), so it is exempt from grid conformance")


def grid_conflict_text(st: AssemblyState, nid: str, row: Mapping[str, Any], limit: float) -> str:
    """Python's words for one typed grid failure (ARCHITECTURE.md 7.9, 7.13)."""
    kind = row["kind"]
    if kind == "grid_extent":
        return (f"{nid}: its pin pattern meets the grid lattice (best {row['best_any']:.3f} mm <= {limit:g}), but no "
                "position inside the board's finite hole array reachable from its edge; a catalogue or requirement "
                "question")
    if kind == "blocked":
        pairs = row.get("blocked_by") or []
        return (f"{nid}: every on-grid position collides or crowds a port ({'; '.join(pairs) or 'no pairs recorded'}); "
                "a layout or requirement question")
    if kind == "no_pin_data":
        return f"{nid}: the catalogue part has no pin data, so its grid conformance cannot be verified (a catalogue question)"
    return (f"{nid}: the grid snap left {row['residual']:.3f} mm although {row.get('positions', 0)} on-grid "
            "position(s) exist and nothing blocked them (a placement bug)")


def grid_check(st: AssemblyState, plan: ac.Plan) -> None:
    """grid_conformance (ARCHITECTURE.md 7.7, 7.9, 7.13): the worst pin-to-hole residual of the parts that must sit on
    the grid against rules.grid_residual_max; parts with a connector but no pin data fail it. A pin_pattern part (its
    pattern meets no grid position) is exempt: listed in evidence.exempt with its assumption, never failing. Every
    other failing part carries a typed kind from the grid sensor (layout.Placer.grid_report): grid_extent, blocked and
    no_pin_data are typed requirement / catalogue conflicts; tangential is a placement bug (fails, no conflict)."""
    rep = st.grid_report
    if not rep or not rep.get("grid"):
        return
    r = st.rules.values
    limit, tol = r["grid_residual_max"], r["measure_tol"]
    conflicts, kinds, exempt = [], {}, []
    for nid, row in rep["parts"].items():
        kind = row.get("kind") or lay.grid_kind(row["residual"], row.get("best_any", row["residual"]), limit, tol)
        row = dict(row, kind=kind)
        kinds[nid] = kind
        if kind == "pin_pattern":
            exempt.append({"part": nid, "best_any": round(row["best_any"], 6), "assumption": grid_exempt_text(row, nid)})
            continue
        if kind not in GRID_CONFLICT_KINDS:
            continue
        conflicts.append({"part": nid, "kind": kind, "competing_rule": kind, "residual": round(row["residual"], 6),
                          "best_any": round(row["best_any"], 6), "best_free": round(row["best_free"], 6),
                          "positions": row.get("positions"), "blocked_by": list(row.get("blocked_by") or []),
                          "text": grid_conflict_text(st, nid, row, limit)})
    for nid in rep["no_pin_data"]:
        kinds[nid] = "no_pin_data"
        conflicts.append({"part": nid, "kind": "no_pin_data", "competing_rule": "no_pin_data", "residual": None,
                          "best_any": None, "best_free": None, "positions": None, "blocked_by": [],
                          "text": grid_conflict_text(st, nid, {"kind": "no_pin_data"}, limit)})
    evidence = {"parts": rep["parts"], "kinds": kinds, "soft": rep.get("soft", False), "finite": rep.get("finite", False),
                "exempt": exempt}
    if conflicts:
        worst = max(conflicts, key=lambda c: -1.0 if c["residual"] is None else c["residual"])
        evidence.update(conflict=worst["text"], competing_rule=worst["competing_rule"], conflicts=conflicts)
    concerns = sorted({st.placed.get(nid).part for nid in list(rep["parts"]) + list(rep["no_pin_data"])})
    plan.add("grid_conformance", "grid_conformance", f"every part pin lies within {limit:g} mm of a board grid hole "
             "(parts with a connector need pin data; a pin pattern that meets no grid position is exempt)",
             value=float(rep["max"]), limit=limit, no_pin_data=list(rep["no_pin_data"]), evidence=evidence,
             parts=concerns)


def coverage_check(st: AssemblyState, plan: ac.Plan) -> None:
    """text_coverage (ARCHITECTURE.md 7.10): for every catalogue plug the request or an L1 names, every placed copy of
    a content item whose connector takes it needs its plug check (clear_<copy>_plug), i.e. it is exposed. Computed on
    graph data (st.contents, the placed copies, the plan's check ids) plus named_parts; an uncovered connection is a
    `coverage` conflict that quotes the naming text, so the self-verdict cannot hide a missing opening."""
    named = named_parts(st)
    ids = {sp["id"] for sp in plan.specs}
    covered, uncovered, plugs = [], [], []
    for it in st.contents:
        for conn in st.catalog.get(it["part"]).data.get("connectors", []):
            plug = conn.get("mates")
            if plug not in named:
                continue
            plugs.append(plug)
            ev = [{"source": h["source"], "quote": h["quote"]} for h in named[plug]]
            copies = [p for p in st.placed.placed if p.part == it["part"]
                      and (p.item == it["id"] or (p.role == "board" and it["id"] == PRIMARY))] or [None]
            for p in copies:
                row = {"item": it["id"], "copy": p.node_id if p else None, "connector": conn["name"], "plug": plug,
                       "evidence": ev}
                (covered if p is not None and f"clear_{conn_key(p, conn)}_plug" in ids else uncovered).append(row)
    evidence: Dict[str, Any] = {"named": {pl: [{"source": h["source"], "quote": h["quote"]} for h in named[pl]]
                                          for pl in sorted(set(plugs))}}
    if uncovered:
        rows = []
        for u in uncovered:
            e = u["evidence"][0]
            rows.append({"part": u["copy"] or u["item"], "kind": "coverage", "competing_rule": "coverage",
                         "text": f"{u['item']}.{u['connector']} is not exposed, but {e['source']} names "
                                 f"{human_name(st.catalog, u['plug'])}: \"{e['quote']}\""})
        evidence.update(conflict=rows[0]["text"], competing_rule="coverage", conflicts=rows)
    plan.add("text_coverage", "coverage", "every content connector whose mating plug the request or an L1 names is "
             "exposed (it has its plug check)", uncovered=uncovered, covered=covered, evidence=evidence,
             parts=sorted(set(plugs)))


def add_minimum_checks(st: AssemblyState, plan: ac.Plan) -> None:
    """ARCHITECTURE.md 7.9: every one-sided minimum the derivation sets with `setpoint` has its own check at the
    limit, on the resolved graph: pilot depth >= the fastener's min_engagement (standoffs: the board screw;
    bosses: the lid screw), outside diameter >= its min_boss_od, and the lid lip's engagement >= rules.lip_engagement.
    Generalize delta 002 C2: pilot depth >= the screw's length - its clamped plate (`pilot_bottoming_<node>`, when the
    fastener declares a length), so the head seats before the tip bottoms. Engagement shortfall (length - plate <
    min_engagement) is not a check yet: it needs the stock-length rule of GM3."""
    r, res, g, f = st.rules.values, st.resolved, st.graph, st.fasteners
    for n in g:
        use = PILOT_USES.get(n.role)
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
        length = f.get(f"fastener.{use}.length")
        if length is not None:              # generalize delta 002 C2: the screw tip clears the pilot's bottom
            plate = clamped_plate_value(st, use)
            tip = length - plate
            plan.add(f"pilot_bottoming_{n.id}", "pilot_bottoming", f"the pilot in {n.id} is at least {tip:g} mm deep, "
                     f"so the {use} screw ({length:g} mm through a {plate:g} mm plate) seats its head before its tip "
                     "bottoms", value=pilot, limit=tip,
                     detail=f"pilot depth {pilot:.3f} vs screw length {length:g} - clamped plate {plate:.3f}")
    if "lid_lip" in g.nodes:
        eng = res.params["base"]["split"] - res.params["lid_lip"]["bottom"]
        plan.add("lip_engagement", "lip_engagement", f"the lid lip reaches at least {r['lip_engagement']:g} mm below "
                 "the split plane", value=eng, limit=r["lip_engagement"],
                 detail=f"lip engagement {eng:.3f} vs {r['lip_engagement']:g}")


def clamped_plate_value(st: AssemblyState, use: str) -> float:
    """clamped_plate resolved: the primary's top - seat plane heights (board screw) or the lid plate's height."""
    if use == "board":
        _, seat, top = primary_mount(st)
        board = st.placed.get(PRIMARY)
        return float(lay.world_datum(board, top).at[2] - lay.world_datum(board, seat).at[2])
    return float(st.resolved.params["lid"]["z"])


def add_fastener_checks(st: AssemblyState, plan: ac.Plan) -> None:
    """ARCHITECTURE.md 7.13 (audit rule 7.12): every fastener feature has a sensor for each L2 number. Each pilot's
    diameter lies within the chosen fastener's [pilot_min, pilot_max] (`pilot_band_<node>`; standoffs: the board
    screw, bosses: the lid screw), and the board screw's thread passes the board's mounting hole
    (`board_screw_passes_hole`: thread + 2 x given_hole_clearance_min <= HOLE.diameter). Graph-data checks on the
    resolved graph, so they read the same on the solids and on the STLs (no inscribed-circle recipe yet)."""
    r, res, g, f = st.rules.values, st.resolved, st.graph, st.fasteners
    for n in g:
        use = PILOT_USES.get(n.role)
        pilot = f"{n.id}_pilot"
        if use is None or pilot not in g.nodes:
            continue
        d, lo, hi = res.params[pilot]["d"], f[f"fastener.{use}.pilot_min"], f[f"fastener.{use}.pilot_max"]
        screw = st.choices.get(f"fastener[{use}]", {}).get("value")
        plan.add(f"pilot_band_{n.id}", "pilot_band", f"the pilot in {n.id} is {lo:g}-{hi:g} mm across (the {use} "
                 "screw's pilot range)", value=d, lo=lo, hi=hi, parts=[screw] if screw else [],
                 detail=f"pilot diameter {d:.3f} vs [{lo:g}, {hi:g}] ({screw or use + ' screw'})")
    board = st.placed.get(PRIMARY)
    hole = lay.world_datum(board, primary_mount(st)[0]).diameter
    if hole is not None and "fastener.board.thread_diameter" in f:
        thread = f["fastener.board.thread_diameter"]
        need = thread + 2 * r["given_hole_clearance_min"]
        screw = st.choices.get("fastener[board]", {}).get("value")
        plan.add("board_screw_passes_hole", "screw_through_hole", f"the board screw's thread passes the board's "
                 f"Ø{hole:g} mounting holes", value=need, limit=hole, parts=[screw] if screw else [],
                 detail=f"thread {thread:g} + 2 x {r['given_hole_clearance_min']:g} vs hole Ø{hole:g}")


def add_plug_reference_checks(st: AssemblyState, plan: ac.Plan) -> None:
    """ARCHITECTURE.md 7.13: every exposed connector's plug at full mate and its withdrawal path clear the reference
    parts other than the connector's own part and its stack parts (`plug_refs_<group>`, clearance 0). An inward-placed
    module puts its plug over the board margin; the plug_* keep-out checks see only the printed bodies. The measured
    volume is the references (per-source d names each one), the subject the plug group outside the connector's mouth
    plane (the mated length behind the mouth is inside the receptacle by design; a catalogue plug shaft longer than
    its receptacle body would otherwise poke out of the receptacle's back). No body is read, so the solids and the
    delivered STLs give the same result."""
    res, g = st.resolved, st.graph
    for p, c in exposed_connectors(st):
        group = f"{conn_key(p, c)}_plug"
        if group not in plan.volumes:
            continue
        mouth = np.asarray(lay.world_datum(p, c["mouth"]).at, dtype=float)
        u = np.asarray(lay.world_datum(p, c["axis"]).dir, dtype=float)
        u = u / np.linalg.norm(u)
        outside = f"{group}_outside"
        plan.volumes[outside] = plan.volumes[group].trim_by_plane(tuple(float(v) for v in u), float(np.dot(u, mouth)))
        plan.sources[outside] = list(plan.sources.get(group, []))
        own = {p.node_id} | {q.node_id for q in st.placed.placed if q.of == p.node_id}
        refs = [n.id for n in g.references() if n.id not in own]
        if not refs:
            continue
        vol = f"refs_{group}"
        plan.volumes[vol] = ac.union([fg.solid(g.nodes[i], res) for i in refs])
        plan.sources[vol] = refs
        parts = sorted({g.nodes[i].part for i in refs if g.nodes[i].part} | {c["mates"]})
        plan.add(f"plug_refs_{group}", "clear_of", f"the {c['mates']} plug in {p.node_id} at full mate and its withdrawal "
                 "path (outside its mouth) clear every other reference part (the board, the other contents)", volume=vol,
                 subject=outside, clearance=0.0, parts=parts)


def cut_axis(st: AssemblyState, n: fg.Node) -> int:
    """The world axis an opening passes along: a port cut's wall normal, else the axis nearest the cut's local Z."""
    if n.role == "port_cut":
        return SIDE_BOUND[n.wall][1]
    return int(np.argmax(np.abs(st.resolved.poses[n.id][:3, 2])))


def add_ligament_checks(st: AssemblyState, plan: ac.Plan) -> None:
    """ARCHITECTURE.md 7.12 (L2.8.3): every opening (a cut whose role is in APERTURE_CUT_ROLES) in the body it opens
    gets `ligament_<cut>_<body>` at rules.min_ligament: the material round it in the cross-section normal to its axis,
    at the middle of the material it passes through (a port cut: the wall's mid-plane, plus the floor-top clause on the
    tray). The plane is fixed at plan time, so the delivered STLs are sliced at the same place."""
    r, res, g = st.rules.values, st.resolved, st.graph
    solids = st.solids if st.solids and all(b in st.solids for b in g.bodies()) else \
        {b: fg.body_solid(g, b, res) for b in g.bodies()}
    cav, base = res.params["cavity"], res.params["base"]
    openings = [n for n in g if n.kind == "cut" and n.role in APERTURE_CUT_ROLES and n.body in solids]
    for n in openings:
        if n.id not in plan.volumes:
            plan.volumes[n.id] = fg.solid(n, res)
            plan.sources[n.id] = [n.id]
    for n in openings:
        b, axis = n.body, cut_axis(st, n)
        floor_z = None
        if n.role == "port_cut":
            bound, _, sign = SIDE_BOUND[n.wall]
            plane = cav[bound] + sign * base["wall"] / 2
            if g.nodes[b].role == "tray":
                floor_z = float(cav["z0"])
        else:
            shell = fg.grown_solid(n, res, r["measure_tol"]) ^ solids[b]
            if shell.is_empty():
                raise ValueError(f"{n.id}: the opening meets no material of {b}")
            bb = shell.bounding_box()
            plane = (bb[axis] + bb[axis + 3]) / 2
        neighbours = [m.id for m in openings if m.id != n.id and m.body == b]
        args = {"body": b, "cut": n.id, "axis": axis, "plane": float(plane), "min": r["min_ligament"],
                "neighbours": neighbours}
        if floor_z is not None:
            args["floor_z"] = floor_z
        plan.add(f"ligament_{n.id}_{b}", "ligament", f"at least {r['min_ligament']:g} mm of material round {n.id} in "
                 f"{b} (to the outer edges, the floor top, the seam and the neighbouring openings)", **args)


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
    board_id = st.placed.get(PRIMARY).node_id
    contents = [i for i in ref_solids if i != board_id]
    vols["board"] = ref_solids[board_id]
    vols["contents"] = ac.union([ref_solids[i] for i in contents])
    plan.sources["board"] = [board_id]
    plan.sources["contents"] = contents
    bc = s["board_clearance"]
    board_part = [st.placed.get(PRIMARY).part]
    content_parts = sorted({g.nodes[i].part for i in contents if g.nodes[i].part})
    seat_words = grown_words(st, plan, "seats", bc)
    plan.add("separable", "separable", "base and lid are each one shell and overlap by at most "
             f"{r['overlap_max']:g} mm3 when closed", bodies=list(BODIES), overlap_max=r["overlap_max"])
    plan.add("inside_board", "inside", f"the board (minus the seat columns {seat_words}) lies inside the closed "
             f"enclosure with {bc:g} mm clearance", volume="board", minus="seats", clearance=bc,
             slots=("board_clearance",), parts=board_part)
    if contents:
        plan.add("inside_contents", "inside", "every part the board carries lies inside the closed enclosure, at least "
                 f"{r['part_to_wall']:g} mm from every printed surface and from the outside", volume="contents",
                 clearance=r["part_to_wall"], parts=content_parts)
    for u in st.unplaced:                    # a sensor, so the package is honest about what it does not hold (C1)
        plan.add(f"content_placed_{u['id']}", "content_placed", f"{u['id']} ({u['part']} x{u['quantity']}) is placed in "
                 "the design", item=u["id"], part=u["part"], reason=u["reason"], parts=[u["part"]])
    plan.add("clear_board", "clear_of", f"no printed surface within {bc:g} mm of the board, "
             f"except the standoff tops in the seat columns {seat_words}", volume="board", minus="seats", clearance=bc,
             slots=("board_clearance",), parts=board_part)
    add_keepout_checks(st, plan, envelopes)
    add_plug_reference_checks(st, plan)
    base, cav = res.params["base"], res.params["cavity"]
    lid = res.params["lid"]
    # Wall slabs (rubric.md 3.4, ARCHITECTURE.md 7.9, 7.10): between the wall's inner and outer face planes, over the
    # wall's full tangential extent (the base's outside, corners included) and full Z extent (base bottom to lid
    # top, closed). Every face is inset by measure_tol (7.10), so no slab face is coplanar with a body face: a lid top
    # on an exactly representable Z left a zero-thickness skin that joined a wall's two corner pockets into one
    # `through` region. Regions are classified through (they reach both face planes with a real cross-section) or
    # blind (with the cut nodes they meet); counts use through.
    eps = r["measure_tol"]
    z_lo, z_hi = cav["z0"] - base["floor"] + eps, base["split"] + lid["z"] - eps
    cuts = [n for n in g if n.role == "port_cut"]
    all_cuts = [n for n in g if n.kind == "cut" and n.role in APERTURE_CUT_ROLES]
    mates = {f"{conn_key(p, c)}_cut": c["mates"] for p, c in exposed_connectors(st)}
    for side, (bound, i, sign) in SIDE_BOUND.items():
        inner = cav[bound]
        outer = inner + sign * base["wall"]
        t = 1 - i
        tb = ("x0", "x1") if t == 0 else ("y0", "y1")
        t_lo, t_hi = cav[tb[0]] - base["wall"] + eps, cav[tb[1]] + base["wall"] - eps
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
            env_w, env_h = getattr(n, "env", None) or (max(res.params[c]["cw"] for c in crossing),
                                                        max(res.params[c]["ch"] for c in crossing))
            plan.add(f"oversize_{n.id}", "aperture_oversize", f"the opening of {n.id} is at most "
                     f"{s['opening_oversize_max']:g} mm bigger than its plug per side", slab=slab, wall=side,
                     normal_axis=i, point=point, env_w=env_w, env_h=env_h, max=s["opening_oversize_max"],
                     slots=("opening_oversize_max",), parts=[mates[n.id]] if n.id in mates else [])
    add_ligament_checks(st, plan)
    board = st.placed.get(PRIMARY)
    hole_name, seat_name, _ = primary_mount(st)
    holes = lay.world_datum(board, hole_name)
    bottom = lay.world_datum(board, seat_name).at[2]
    standoffs = [n for n in g if n.role == "standoff"]
    probe = min(res.params[f"{n.id}_pilot"]["depth"] for n in standoffs) / 2
    search_d = min((res.params[f"{n.id}_pilot"]["d"] + res.params[n.id]["d"]) / 2 for n in standoffs)
    plan.add("seated", "seated", f"the board rests on the standoff tops (gap <= {r['seat_gap_max']:g} mm) with every "
             f"hole on a pilot axis (offset <= {r['seat_axis_residual_max']:g} mm)", body="base",
             holes=[[float(v) for v in p[:2]] for p in holes.at], board_bottom=float(bottom),
             search_d=float(search_d), z_lo=float(cav["z0"]), z_hi=float(bottom + r["cut_overrun"]), probe_depth=float(probe),
             gap_max=r["seat_gap_max"], residual_max=r["seat_axis_residual_max"])
    plan.add("bbox", "bbox_within", f"closed outside size within {s['max_x']:g} x {s['max_y']:g} x {s['max_z']:g} mm",
             max=[s["max_x"], s["max_y"], s["max_z"]], x_longest=s["max_x"] > s["max_y"],
             slots=("max_x", "max_y", "max_z"))
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
    add_fastener_checks(st, plan)
    add_relation_checks(st, plan)
    grid_check(st, plan)
    coverage_check(st, plan)
    grow_exemptions(st, plan)
    add_part_maps(st, plan)
    return plan


UNLINKED_NOTE = "no rule-derived check is traced to this requirement yet (translation to checks is milestone M10)"


def trace_links(st: AssemblyState, plan: ac.Plan) -> Dict[str, List[str]]:
    """ARCHITECTURE.md 7.10: the deterministic L1 trace of the rule-derived checks. A check links to every L1 that is
    the provenance source of one of its spec slots (spec_provenance "L1.k:\"quote\"") and to every L1 that names one
    of the catalogue parts it concerns (named_parts). M10's translation adds links; it never replaces these."""
    l1_ids = [src for src, _ in st.texts if src != "request"]
    slot_l1 = {}
    for slot, prov in st.spec_provenance.items():
        src = str(prov).partition(":")[0]
        if src in l1_ids:
            slot_l1[slot] = src
    part_l1 = {pid: [h["source"] for h in hits if h["source"] in l1_ids] for pid, hits in named_parts(st).items()}
    out: Dict[str, List[str]] = {}
    for sp in plan.specs:
        found = [slot_l1[k] for k in sp.get("slots", []) if k in slot_l1]
        found += [l for pid in sp.get("parts", []) for l in part_l1.get(pid, [])]
        out[sp["id"]] = sorted(set(found), key=l1_ids.index)
    return out


def trace_matrix(l1: Sequence[dict], checks: Sequence[cc.Check], results: Sequence[cc.CheckResult],
                 links: Mapping[str, Sequence[str]]) -> List[dict]:
    """The assembly verification matrix: one row per L1 over all its linked checks (a check may serve several L1s),
    status PASS / FAIL, or UNLINKED when no check is traced to it (never "FAIL n/a"); then one `rules` row holding every
    check with no L1 link. cc.verification_matrix (cascade's) is not used here."""
    by_id = {r.check_id: r for r in results}

    def row(rid, text, method, pairs, note=""):
        status = "UNLINKED" if not pairs else ("PASS" if all(r.passed for _, r in pairs) else "FAIL")
        return {"l1_id": rid, "text": text, "method": method, "status": status,
                "passed": bool(pairs) and all(r.passed for _, r in pairs),
                "margin": min((r.margin for _, r in pairs), default=None),
                "checks": [{"id": c.id, "type": c.type, "text": c.text, "passed": r.passed, "margin": r.margin,
                            "evidence": r.evidence.get("detail")} for c, r in pairs],
                "note": note if not pairs else ""}

    pairs = [(c, by_id[c.id]) for c in checks if c.id in by_id]
    rows = [row(req["id"], req.get("text", ""), req.get("method"),
                [(c, r) for c, r in pairs if req["id"] in links.get(c.id, ())], UNLINKED_NOTE) for req in l1]
    rest = [(c, r) for c, r in pairs if not links.get(c.id)]
    rows.append(row(ac.L1_RULES, "rule-derived checks with no L1 link (generic consequences of the contents, the "
                    "spec and printing)", "analysis", rest))
    return rows


def trace_matrix_text(rows: Sequence[dict]) -> str:
    lines = []
    for r in rows:
        margin = f"{r['margin']:+.3f}" if r["margin"] is not None else "      "
        lines.append(f"{r['status']:<8} {margin}  {r['l1_id']}: {r['text']}{'  (' + r['note'] + ')' if r['note'] else ''}")
        for c in r["checks"]:
            lines.append(f"      {'ok ' if c['passed'] else 'NO '} {c['id']} [{c['type']}] {c['evidence']}")
    return "\n".join(lines)


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
        st.links = trace_links(st, st.plan)
        st.results_manifold = ac.run_plan(st.plan, st.solids)
        st.self_report = ac.measure_package(self.design.workdir, st.plan, list(st.solids))
        st.results = [cc.CheckResult(**r) for r in st.self_report["results"]]
        if st.self_report["errors"]:
            st.notes.append("verify: " + "; ".join(st.self_report["errors"]))
        failed = [r.check_id for r in st.results if not r.passed]
        self.logger.info(f"verify: {len(st.results) - len(failed)}/{len(st.results)} checks pass on the delivered STLs"
                         + (f"; failing: {', '.join(failed)}" if failed else ""))
        return Status.SUCCESS


def assembly_views(rules: Mapping[str, float]) -> Dict[str, tuple]:
    """The cameras of assembly-mode renders (7.11): cad_agent.VIEWS with every elevation tilted down by
    rules.view_elevation_deg, so the floor seen through an opening is shaded unlike the wall and opposite views differ.
    iso and top are unchanged; the other modes keep cad_agent.VIEWS."""
    out = dict(ca.VIEWS)
    for k in ELEVATION_VIEWS:
        if k in out:
            v = list(out[k])
            v[VIEW_ROTX] = v[VIEW_ROTX] - rules["view_elevation_deg"]
            out[k] = tuple(v)
    return out


class RenderViews(AssemblyStep):
    def __init__(self, design):
        super().__init__("RenderViews", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "render_views"
        views = self.design.workdir / "views"
        open_views = {k: ca.VIEWS[k] for k in OPEN_VIEWS if k in ca.VIEWS}
        cams_all = assembly_views(st.rules.values)
        for scad, stem, cams in (("views.scad", "model", cams_all), ("ghost.scad", "ghost", cams_all),
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
            "spec": st.spec, "board": board_block(st),
            "grid_residual": None if st.layout_grid_residual is None else round(st.layout_grid_residual, 6),
            "grid_exempt": list(st.layout_grid_exempt),
            "grid_exempt_assumptions": {nid: grid_exempt_text(st.grid_report["parts"][nid], nid)
                                        for nid in st.layout_grid_exempt if nid in st.grid_report.get("parts", {})},
            "grid_residual_all_parts": None if st.layout_grid_residual_all is None
            else round(st.layout_grid_residual_all, 6), **({"unplaced": list(st.unplaced)} if st.unplaced else {})})
        ac.write_json(wd / "self_report.json", st.self_report)
        ac.write_json(wd / "feature_graph.json", st.graph.to_json())
        ac.write_json(wd / "checks.json", [dict(c.to_dict(), links=list(st.links.get(c.id, []))) for c in st.checks])
        rows = trace_matrix(list(self.design.l1), st.checks, st.results, st.links)
        ac.write_json(wd / "verification_matrix.json", rows)
        (wd / "verification_matrix.md").write_text(
            "# Verification matrix (delivered STLs)\n\nEach requirement row lists the rule-derived checks traced to it "
            "(spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).\n\n"
            "```\n" + trace_matrix_text(rows) + "\n```\n\n"
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
        dirs = [str(p) for p in parts_dir] if isinstance(parts_dir, (list, tuple)) else [str(parts_dir)]
        design.assy = AssemblyState(parts_dir=dirs[0] if len(dirs) == 1 else os.pathsep.join(dirs), parts_dirs=dirs,
                                    rules_path=str(rules_path), with_models=bool(with_models))
    return py_trees.composites.Sequence("cad_assembly", memory=True, children=[
        LoadCatalog(design), LoadRules(design), ParseSpec(design, llm), Contents(design, llm),
        ExposureCoverage(design), ChooseStack(design, llm), ArrangeContents(design, llm), BuildEnvelopes(design),
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
