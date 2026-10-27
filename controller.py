"""The closed-loop controller of --mode assembly (generalization loop owner decision D1; loop/ARCHITECTURE.md section
"Controller architecture (D1)", migration deltas R01 and R02).

    initial proposal (the stages up to DeriveFeatures) -> build on manifold -> sense (typed error vector)
      -> the LLM picks one correction from a typed action menu (voted)
      -> Python applies it on a fork of the stage checkpoint the action invalidates, re-runs those stages, rebuilds on
         manifold and senses again -> the fork is kept only when the controllable error does not rise beyond the trust
         region (design_rules.json controller_trust_region); otherwise it is dropped and the reason is fed back
      -> until no failing check has an action, the controller says stop, or the step budget
         (design_rules.json controller_step_budget) is spent. OpenSCAD runs only afterwards, for the package (Build).

Python is the plant (the stages re-run from their checkpoints; a proposal stage may ask its own questions, e.g. the
arrangement's edge vote after a connector is exposed), the sensors (assembly.build_plan checks -> ErrorTerm rows: which
requirement, where, by how much, which direction) and the actuators (ACTUATORS: a failing check type -> typed actions,
each validated by being applied). The LLM only picks one menu entry; it never invents a number. Every step is logged
(controller_trace.json in the package). StubController is the authority probe: the first offered option of every
question, no corrective steps, no LLM calls.

R02 (option-ID bias, menus.py): the menu is content-keyed (the model answers an action id such as
`expose:module_1.usb`, after a one-sentence reason) and shown in seeded shuffled orders (stop is not pinned last); the
question is asked under K orderings (permutation voting). A choice consistent across orderings is high-confidence; the
surviving actions (every action with a vote, plus the next-ranked alternatives when the vote is inconsistent) are each
applied on a fork and measured, and the action with the lowest controllable error is kept (verifier-guided best-of-N:
design_rules.json controller_search_k / _depth / _max_evals); the LLM's ranking only breaks error ties.

Nothing here holds a number, part or face that is specific to one request (test_no_hardcoding.py scans this module);
every decision string is registered in controller_rules.json (test_controller_authority.py).
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import time
from collections import Counter
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from py_trees.common import Status

import assembly as A
import building_blocks as BB    # migration delta R11 (building blocks): actions register through ACTUATORS / APPLIERS
import forms as FM              # migration delta R12: set_archetype registers through ACTUATORS / APPLIERS
import plate as PL              # migration delta R12: the plate's actions (add_surface_feature, set_handedness)
import cad_checks as cc
import feature_graph as fg
import menus

ca = cc._ca()

CONTROL_LABEL = "assy_control"          # the label of the controller's voted question (transcripts, scripted fakes)
CONTROLLER_BY = "llm:controller"        # `by` of every decision the controller's accepted actions record
STOP = "stop"                           # the menu entry that ends the loop (always offered; R02: shown in a shuffled place)
SEARCH_BY = "search:controller"         # `by` of an action no LLM vote named, kept because it measured the lowest error
REGISTRY_PATH = Path(__file__).resolve().parent / "controller_rules.json"
RULE_RE = re.compile(r"rule:([A-Za-z_][A-Za-z0-9_]*)(\[[A-Za-z0-9_]+\])?")
QUOTE_MAX = 160                         # longest quote / detail shown to the controller per error term
DIGEST_HEX = 16                         # hex characters of a state digest (sha1 prefix)
TRACE_SCHEMA = 2                        # R02: content-keyed menus, permutation votes, search candidates

# The re-runnable stages in pipeline order (each takes a checkpoint of the state at its entry, assembly.checkpoint).
# An action names the first stage it invalidates; applying it re-runs that stage and every later one, from that
# stage's checkpoint, with every accepted action re-applied.
RERUN_ORDER = ("stack", "arrange", "vents", "envelopes", "archetype", "derive")


def stage_runner(name: str, design, llm):
    """The assembly stage behind a re-runnable stage name (its update() returns a py_trees Status)."""
    return {"stack": lambda: A.ChooseStack(design, llm), "arrange": lambda: A.ArrangeContents(design, llm),
            "vents": lambda: A.Vents(design, llm), "envelopes": lambda: A.BuildEnvelopes(design),
            "archetype": lambda: A.ChooseArchetype(design, llm), "derive": lambda: A.DeriveFeatures(design)}[name]()


# ---------------------------------------------------------------------------
# The registry of rule:* decisions (controller_rules.json) and the authority audit
# ---------------------------------------------------------------------------


def canonical_rule(text: str) -> Optional[str]:
    """The registered name of a rule decision string: "rule:<identifier>" plus a literal [qualifier], ending at the first
    other character ("rule:connector_to_cut(board.usb)" -> "rule:connector_to_cut", "rule:closure.rebate.plate" ->
    "rule:closure", "rule:text_evidence[board]" stays). None when the text holds no rule name."""
    m = RULE_RE.search(str(text or ""))
    return None if m is None else f"rule:{m.group(1)}{m.group(2) or ''}"


def load_registry(path: Optional[Path] = None) -> Dict[str, dict]:
    """controller_rules.json `rules` (name -> {class, status, ...}); {} when the file is missing or unreadable (the
    audit then reports every rule decision as unregistered, it never stops a run)."""
    p = Path(path or REGISTRY_PATH)
    try:
        return dict(json.loads(p.read_text()).get("rules") or {})
    except (OSError, ValueError):
        return {}


def decision_class(by: str, registry: Mapping[str, dict]) -> str:
    """Who made a recorded decision: llm (the controller, including a vote among Python's error-tied survivors),
    guardrail (an error-based plant choice: prescore, or since R02 the verifier search keeping an alternative no LLM vote
    named), or the registered class of a rule (plant, guardrail, semantic-rule, ...); unregistered for a rule name the
    registry lacks."""
    b = str(by or "")
    if b.startswith("llm") or "llm:" in b:
        return "llm"
    if b.startswith(("prescore:", "search:")):      # an error-based choice among the controller's alternatives
        return "guardrail"
    name = canonical_rule(b)
    if name is None:
        return "other"
    return str((registry.get(name) or {}).get("class") or "unregistered")


def authority(st: "A.AssemblyState", registry: Optional[Mapping[str, dict]] = None) -> dict:
    """The per-run authority audit (D1: measure the controller's authority): every recorded decision (st.choices)
    classified by who made it; semantic-rule decisions listed with the migration delta that retires them. The proposal
    questions' answers are counted too (`proposal`): each spec or part-size slot the LLM mapped onto a number of the
    text (a rules default is plant) and each content item the Contents vote put in the design; `llm_share` is over both."""
    reg = load_registry() if registry is None else registry
    counts: Counter = Counter()
    semantic, unregistered = [], []
    for name, rec in st.choices.items():
        by = rec.get("by", "") if isinstance(rec, dict) else ""
        cls = decision_class(by, reg)
        counts[cls] += 1
        if cls == "semantic-rule":
            rule = canonical_rule(by)
            semantic.append({"decision": name, "by": by, "migration": (reg.get(rule) or {}).get("migration")})
        elif cls == "unregistered":
            unregistered.append({"decision": name, "by": by})
    prov = [str(v) for v in st.spec_provenance.values()]
    proposal = {"llm_slots": sum(1 for v in prov if not v.startswith(("rules:", "catalogue:"))),
                "default_slots": sum(1 for v in prov if v.startswith("rules:")),
                "llm_contents_items": len(st.contents)}
    llm_total = counts["llm"] + proposal["llm_slots"] + proposal["llm_contents_items"]
    total = sum(counts.values()) + proposal["llm_slots"] + proposal["default_slots"] + proposal["llm_contents_items"]
    return {"decisions": dict(counts), "proposal": proposal, "semantic_rule_decisions": semantic,
            "unregistered": unregistered, "llm_share": round(llm_total / max(1, total), 4)}


# ---------------------------------------------------------------------------
# Sensors: the typed error vector
# ---------------------------------------------------------------------------

# What a failing check of each type needs, in words (`quantity`, `sense`): increase / decrease / band / count, or
# semantic (a text sensor: the design does not do what a sentence names). Unknown types read "fix the check".
DIRECTIONS: Dict[str, Tuple[str, str]] = {
    "clear_of": ("gap to the volume", "increase"), "inside": ("gap to the enclosure and its outside", "increase"),
    "ligament": ("material round the opening", "increase"), "pilot_engagement": ("pilot depth", "increase"),
    "boss_od": ("boss diameter", "increase"), "lip_engagement": ("lip engagement", "increase"),
    "pilot_bottoming": ("pilot depth", "increase"), "rebate_upstand": ("upstand thickness", "increase"),
    "vent_area": ("vent open area", "increase"),
    "port_below_split": ("opening top below the split", "decrease"), "pilot_depth": ("pilot depth", "decrease"),
    "screw_through_hole": ("screw thread against the hole", "decrease"), "bridge": ("flat bridge span", "decrease"),
    "lid_flush": ("lid step", "decrease"), "boss_top_plane": ("boss top offset", "decrease"),
    "vent_zone": ("vent row offset from its zone", "decrease"), "bbox_within": ("outside size", "decrease"),
    "aperture_oversize": ("opening oversize", "decrease"), "seated": ("board seat gap or hole offset", "decrease"),
    "separable": ("body shells or overlap", "decrease"), "grid_conformance": ("pin-to-grid residual", "decrease"),
    "pilot_band": ("pilot diameter", "band"), "lid_fit": ("lid fit gap", "band"), "vent_count": ("vent count", "band"),
    "vent_width": ("vent width", "band"), "vent_length": ("vent length", "band"), "vent_pitch": ("vent pitch", "band"),
    "aperture_count": ("through openings in the wall", "count"),
    "coverage": ("an opening for each connector whose mating plug the text names", "semantic"),
    "closure_evidence": ("the lid closure the text names", "semantic"),
    "face_relation": ("the connector faces the text states", "semantic"),
    "content_placed": ("every content part placed", "semantic"),
    "vent_placed": ("the vent slots the text asks for", "semantic"),
}


@dataclass
class ErrorTerm:
    """One failing check as the controller sees it: which requirement, where, by how much, which direction."""
    check: str
    type: str
    requirement: List[str]          # the L1 ids the check is traced to ([] = a rule-derived consequence)
    where: str                      # Python's words for the place (bodies, walls, connector, coordinates)
    deficit: Optional[float]        # how far from passing, in `unit` (None when not a measured quantity)
    unit: str
    direction: str                  # what would make it pass, in words
    controllable: bool              # False: a typed conflict (a requirement question), never actuated here
    actionable: bool                # a typed action exists for this check type (ACTUATORS)
    hard: bool
    margin: float
    detail: str

    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def words(self) -> str:
        req = ", ".join(self.requirement) or "a generic rule"
        how = "" if self.deficit is None or self.unit == "count" else f"; off by {self.deficit:.3g} {self.unit}"
        return f"{self.check} ({req}): {self.where}{how}; needs: {self.direction}"


def _short(text: Any, n: int = QUOTE_MAX) -> str:
    s = " ".join(str(text or "").split())
    return s if len(s) <= n else s[: n - 3] + "..."


def _part_name(st: "A.AssemblyState", pid: Optional[str]) -> str:
    return A.human_name(st.catalog, pid) if pid and st.catalog is not None else str(pid or "")


def where_words(st: "A.AssemblyState", r: cc.CheckResult) -> str:
    """Python's words for where a failing check fails, from its evidence (no LLM text)."""
    ev = r.evidence or {}
    if r.type == "coverage":
        bits, seen = [], set()
        for u in ev.get("uncovered") or []:
            if (u["item"], u["connector"]) in seen:
                continue
            seen.add((u["item"], u["connector"]))
            e = (u.get("evidence") or [{}])[0]
            part = next((c["part"] for c in st.contents if c.get("id") == u["item"]), None)
            bits.append(f"{u['item']}.{u['connector']} ({_part_name(st, part)}) is closed, but {e.get('source', 'the text')}"
                        f" names a {_part_name(st, u.get('plug'))}: \"{_short(e.get('quote', ''))}\"")
        return "; ".join(bits) or _short(ev.get("detail"))
    if r.type == "closure_evidence":
        q = (ev.get("quotes") or [{}])[0]
        return (f"the lid closure is {ev.get('current')}, but {q.get('source', 'the text')} names "
                f"{' or '.join(ev.get('expected') or [])}: \"{_short(q.get('quote', ''))}\"")
    if ev.get("walls") and ev.get("members"):
        return f"{' and '.join(ev['members'])} face {' and '.join(ev['walls'])}"
    if ev.get("where"):
        return f"{_short(ev.get('detail'))} at {ev['where']}"
    return _short(ev.get("detail") or r.check_id)


def deficit_of(r: cc.CheckResult, scale: float) -> Tuple[Optional[float], str]:
    """How far a failing check is from passing: -margin x margin_scale for millimetre checks, -margin for counts."""
    if r.passed:
        return 0.0, r.unit
    if r.unit == "mm":
        return round(max(0.0, -r.margin) * scale, 4), "mm"
    if r.unit == "count":
        return round(max(0.0, -r.margin), 4), "count"
    return None, r.unit


def error_vector(st: "A.AssemblyState", results: Sequence[cc.CheckResult],
                 links: Mapping[str, Sequence[str]]) -> List[ErrorTerm]:
    """The typed error vector of a measured design, ranked: actionable controllable failures first, then the other
    controllable ones, then typed conflicts; within each group the worst margin first."""
    scale = float(st.rules.values.get("margin_scale", 1.0)) if st.rules else 1.0
    out = []
    for r in results:
        if r.passed:
            continue
        conflict = bool((r.evidence or {}).get("conflict"))
        quantity, sense = DIRECTIONS.get(r.type, ("the check's value", "fix"))
        if sense == "semantic":
            direction = quantity
        elif sense == "band":
            direction = f"bring the {quantity} into its band"
        elif sense == "count":
            direction = f"make the number of {quantity} right"
        else:
            direction = f"{sense} the {quantity}"
        if conflict:
            direction += f" (typed conflict: {_short(r.evidence.get('conflict'), 100)})"
        d, unit = deficit_of(r, scale)
        out.append(ErrorTerm(r.check_id, r.type, list(links.get(r.check_id, [])), where_words(st, r), d, unit,
                             direction, not conflict, r.type in ACTUATORS and not conflict, bool(r.hard),
                             float(r.margin), _short((r.evidence or {}).get("detail"))))
    out.sort(key=lambda t: (not t.actionable, not t.controllable, t.margin))
    return out


def error_key(results: Sequence[cc.CheckResult]) -> cc.ErrorKey:
    """The controllable error (assembly.controllable, ARCHITECTURE.md 7.11): typed conflicts belong to the requirement
    loop and never rank a correction."""
    ctrl, _ = A.controllable(results)
    return cc.error_key(ctrl)


# ---------------------------------------------------------------------------
# Actuators: typed, generic actions; each failing check type that has an actuator offers some
# ---------------------------------------------------------------------------


@dataclass
class Action:
    """One typed correction. `invalidates` is the first re-runnable stage (RERUN_ORDER) whose result it changes."""
    kind: str                       # expose | set_closure | stop
    target: str                     # "<item>.<connector>" | "closure" | ""
    value: Any
    words: str                      # Python's words for the menu
    targets: List[str] = field(default_factory=list)   # the failing check ids it addresses
    invalidates: str = "derive"
    evidence: List[dict] = field(default_factory=list)  # the quotes of the check it addresses (recorded on the choice)
    ident: str = ""                 # the content key the controller answers with (R02); "" = the generic form (id)

    @property
    def key(self) -> str:
        """The tabu / infeasibility key (R01 form, kept so records stay comparable)."""
        return f"{self.kind}:{self.target}={self.value}"

    @property
    def id(self) -> str:
        """The content key shown in the menu and answered by the controller (R02): `<kind>:<target>` plus `=<value>`
        when the value is not a plain switch, or the actuator's own ident (`set_closure:rebate`, `stop`). Generic: a new
        action kind gets an id with no change here."""
        if self.ident:
            return self.ident
        if not self.target:
            return self.kind if self.value in (True, None, "") else f"{self.kind}:{self.value}"
        return f"{self.kind}:{self.target}" + ("" if self.value in (True, None, "") else f"={self.value}")

    @property
    def desc(self) -> str:
        """The action's words without the leading "<kind> <target>:" (the id says that)."""
        return self.words.split(": ", 1)[1] if ": " in self.words else self.words

    def to_dict(self) -> dict:
        return {"kind": self.kind, "target": self.target, "value": self.value, "words": self.words,
                "targets": list(self.targets), "invalidates": self.invalidates, "evidence": list(self.evidence),
                "key": self.key, "id": self.id, "ident": self.ident}

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Action":
        return cls(d["kind"], d["target"], d["value"], d.get("words", ""), list(d.get("targets", [])),
                   d.get("invalidates", "derive"), list(d.get("evidence", [])), d.get("ident", ""))


STOP_ACTION = Action(STOP, "", None, "stop: keep the design as it is (the failing requirements above stay failing)",
                     [], "", ident=STOP)


def expose_actions(st: "A.AssemblyState", r: cc.CheckResult) -> List[Action]:
    """text_coverage (R01, was rule:text_coverage): one `expose` action per closed connector whose mating part the text
    names: a feature action (an envelope aperture through the wall the arrangement gives it). A row with no placed copy
    (an item the primary does not carry, reported by its content_placed check) offers none: no opening can follow."""
    out, seen = [], set()
    for u in (r.evidence or {}).get("uncovered") or []:
        key = (u["item"], u["connector"])
        if key in seen or u.get("copy") is None:
            continue
        seen.add(key)
        part = next((c["part"] for c in st.contents if c.get("id") == u["item"]), None)
        ev = [{"source": e.get("source"), "quote": e.get("quote")} for e in u.get("evidence") or []]
        out.append(Action("expose", f"{u['item']}.{u['connector']}", True,
                          f"expose {u['item']}.{u['connector']}: open the enclosure wall for the {_part_name(st, part)}'s "
                          f"{u['connector']} connector so a {_part_name(st, u.get('plug'))} plugs in with the enclosure "
                          "closed", [r.check_id], "arrange", ev))
    return out


def closure_actions(st: "A.AssemblyState", r: cc.CheckResult) -> List[Action]:
    """closure_evidence (R01, was rule:text_evidence[closure]): one `set_closure` action per closure the plant can build
    other than the current one (structural form)."""
    ev = r.evidence or {}
    current = ev.get("current")
    quotes = [{"source": q.get("source"), "quote": q.get("quote")} for q in ev.get("quotes") or []]
    out = []
    for name in A.buildable_closures(st.rules):
        if name == current:
            continue
        meaning = (st.rules.closures.get(name) or {}).get("meaning", name)
        out.append(Action("set_closure", "closure", name, f"set the lid closure to {name}: {meaning}", [r.check_id],
                          "derive", quotes, ident=f"set_closure:{name}"))
    return out


ACTUATORS: Dict[str, Callable[["A.AssemblyState", cc.CheckResult], List[Action]]] = {
    "coverage": expose_actions,
    "closure_evidence": closure_actions,
}
# migration delta R11 (building blocks): the blocks' action kinds and sensor directions register here (generic Action);
# their appliers join APPLIERS below
ACTUATORS.update(BB.ACTUATORS)
DIRECTIONS.update(BB.DIRECTIONS)
# migration delta R12: the form sensor's set_archetype, the plate's actions; a failing content_placed check offers the
# panel mount (R11) and set_archetype to a form that would place the item (an engaged reference part)
ACTUATORS.update(PL.ACTUATORS)
ACTUATORS[FM.FORM_EVIDENCE] = FM.archetype_actions
_PANEL_ACTIONS = ACTUATORS["content_placed"]
ACTUATORS["content_placed"] = lambda st, r: _PANEL_ACTIONS(st, r) + FM.placing_actions(st, r)
DIRECTIONS.update(PL.DIRECTIONS)
DIRECTIONS.update(FM.DIRECTIONS)


def menu(st: "A.AssemblyState", results: Sequence[cc.CheckResult], tabu: Sequence[str]) -> List[Action]:
    """The typed actions the failing, controllable checks offer (in the error vector's order), minus every action already
    tried in this run, capped by rules.controller_menu_max. STOP is not included (the prompt adds it last)."""
    cap = int(st.rules.values.get("controller_menu_max", 8))
    ranked = sorted([r for r in results if not r.passed and not (r.evidence or {}).get("conflict")],
                    key=lambda r: r.margin)
    out, keys = [], set(tabu)
    for r in ranked:
        for a in ACTUATORS.get(r.type, lambda *_: [])(st, r):
            if a.key not in keys:
                keys.add(a.key)
                out.append(a)
    return out[:cap]


def _apply_expose(st: "A.AssemblyState", action: Action, record: Mapping[str, Any], by: str) -> None:
    item, connector = action.target.split(".", 1)
    A.expose_connector(st, item, connector, by=by, record=record)


def _apply_closure(st: "A.AssemblyState", action: Action, record: Mapping[str, Any], by: str) -> None:
    st.control["closure"] = action.value
    A.choice(st, "closure", action.value, by, **dict(record))


# action kind -> applier(state, action, record, by). A new action kind registers its applier here (and its actions in
# ACTUATORS); the menu, the permutation vote and the search take any kind unchanged.
APPLIERS: Dict[str, Callable[["A.AssemblyState", Action, Mapping[str, Any], str], None]] = {
    "expose": _apply_expose,
    "set_closure": _apply_closure,
}
APPLIERS.update(BB.APPLIERS)    # migration delta R11 (building blocks): set_retention, set_panel plug into R02's table
APPLIERS.update(PL.APPLIERS)    # migration delta R12: add_surface_feature, set_handedness
APPLIERS[FM.SET_ARCHETYPE] = FM.apply_archetype      # migration delta R12: set_archetype (invalidates the archetype stage)


def apply_action(st: "A.AssemblyState", action: Action, record: Mapping[str, Any], by: str = CONTROLLER_BY) -> None:
    """Apply one accepted (or candidate) action's decision to a state. Idempotent: it is re-applied on the checkpoint of
    every later action."""
    fn = APPLIERS.get(action.kind)
    if fn is None:
        raise ValueError(f"no actuator for action kind {action.kind!r}")
    fn(st, action, record, by)


# ---------------------------------------------------------------------------
# The plant on a state: re-run the invalidated stages from their checkpoint, build on manifold, sense
# ---------------------------------------------------------------------------


def plant(st: "A.AssemblyState") -> Tuple[Any, List[cc.CheckResult], Dict[str, List[str]]]:
    """Manifold-only build of a derived state and every check of its plan (no OpenSCAD, no files, no LLM). Returns
    (plan, results, L1 links)."""
    stage = st.stage
    st.stage = "controller"
    try:
        plan, results = A.plant_error(st)
        links = A.trace_links(st, plan)
    finally:
        st.stage = stage
    return plan, results, links


def fork_from(st: "A.AssemblyState", stage: str, control: Optional[Mapping[str, Any]] = None) -> "A.AssemblyState":
    """A fresh copy of the state as it was at the entry of `stage` (its checkpoint), carrying the checkpoints of every
    earlier stage; the stages from `stage` on re-take theirs when they run. `control` (default: st.control) is the
    controller's bookkeeping the fork starts from; the loop passes the snapshot taken before a step's candidates, so
    every candidate of one step is measured under the same sensor typing (review fix B1)."""
    if stage not in st.checkpoints:
        raise ValueError(f"no checkpoint for stage {stage!r} (stages run: {', '.join(st.checkpoints) or 'none'})")
    sc = A.snapshot(st.checkpoints[stage])
    order = RERUN_ORDER.index(stage)
    sc.checkpoints = {k: v for k, v in st.checkpoints.items() if k in RERUN_ORDER and RERUN_ORDER.index(k) < order}
    sc.control = copy.deepcopy(dict(st.control if control is None else control))
    return sc


def rerun(design, llm, stage: str) -> Optional[str]:
    """Run the re-runnable stages from `stage` to DeriveFeatures on design.assy (a fork). Returns None, or the typed
    failure of the stage that stopped (the action is then infeasible)."""
    st = design.assy
    for name in RERUN_ORDER[RERUN_ORDER.index(stage):]:
        status = stage_runner(name, design, llm).update()
        if status != Status.SUCCESS:
            return f"{name}: {st.notes[-1] if st.notes else 'failed'}"
    return None


def dedupe(seq: List[Any]) -> List[Any]:
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


# ---------------------------------------------------------------------------
# State presentation and the question
# ---------------------------------------------------------------------------


def decision_vector(st: "A.AssemblyState") -> dict:
    """The design's discrete decisions (what a state digest is computed over)."""
    ch = st.choices
    return {
        "contents": [[c.get("id"), c.get("part"), c.get("quantity"), sorted(c.get("exposed_connectors", []))]
                     for c in st.contents],
        "stacks": {i.id: i.stack for i in st.items},
        "faces": {k: v.get("value") for k, v in sorted(ch.items()) if k.startswith(("edge[", "wall["))},
        "relations": [[r["a"]["key"], r["b"]["key"], r["value"]] for r in st.relations],
        "closure": (ch.get("closure") or {}).get("value"), "boss_layout": (ch.get("boss_layout") or {}).get("value"),
        "archetype": (ch.get("archetype") or {}).get("value"), "vent_face": (ch.get("vent_face") or {}).get("value"),
        "fasteners": {u: (ch.get(f"fastener[{u}]") or {}).get("value") for u in ("board", "lid")},
        **BB.decisions(st),                          # R11: building-block decisions (only when a block decided)
        **PL.decisions(st),                          # R12: the plate's decisions (only for a plate)
    }


def state_digest(st: "A.AssemblyState") -> dict:
    """{decisions: sha1 prefix of the decision vector, graph: sha1 prefix of the feature graph, summary: the vector}."""
    dv = decision_vector(st)
    graph = None
    if st.graph is not None:
        graph = hashlib.sha1(json.dumps(st.graph.to_json(), sort_keys=True, default=str).encode()).hexdigest()
    return {"decisions": hashlib.sha1(json.dumps(dv, sort_keys=True, default=str).encode()).hexdigest()[:DIGEST_HEX],
            "graph": graph[:DIGEST_HEX] if graph else None, "summary": dv}


def state_words(st: "A.AssemblyState") -> str:
    """The design now, compactly: each content item with its connectors (open through which wall, or closed), the lid
    closure and the boss layout."""
    walls = {}
    if st.placed is not None:
        for p, c in A.exposed_connectors(st):
            walls[(A.PRIMARY if p.role == "board" else p.item, c["name"])] = A.wall_facing(
                A.lay.world_datum(p, c["axis"]).dir)
    lines = []
    for it in st.contents:
        conns = A.connector_list(st.catalog.get(it["part"]))
        bits = []
        for c in conns:
            w = walls.get((it["id"], c["name"]))
            bits.append(f"{c['name']} {'open through ' + w if w else 'closed'}")
        role = " (primary)" if it.get("id") == A.PRIMARY else ""
        lines.append(f"- {it['id']}{role}: {_part_name(st, it['part'])} x{it.get('quantity', 1)}"
                     + (f"; connectors: {', '.join(bits)}" if bits else ""))
    ch = st.choices
    if FM.is_plate(st):                  # R12: a plate has no lid; its own words
        return "\n".join(lines + FM.state_lines(st) + PL.state_lines(st))
    tail = [f"lid closure: {(ch.get('closure') or {}).get('value', '?')}"]
    if ch.get("boss_layout"):
        tail.append(f"lid bosses: {ch['boss_layout']['value']}")
    return "\n".join(lines + ["- " + "; ".join(tail)] + BB.state_lines(st) + FM.state_lines(st))   # R11, R12


ACTIONS_LINE = "Actions you can take now (one per step; Python applies it, rebuilds and measures again):"
CONTROL_QUESTION = ("Which one action makes the design do what the request asks? First give a one-sentence reason, then "
                    "the action's id exactly as listed.")


def menu_lines(options: Sequence[Action]) -> str:
    """The content-keyed menu (R02): one line per action, `- <id>: <words>`, in the order given."""
    return "\n".join(f"- {a.id}: {a.desc}" for a in options)


def menu_prompt(head: str, options: Sequence[Action]) -> str:
    """The question tail after `head` (request, error vector, state, feedback): the menu in the order given."""
    return f"{head}\n\n{ACTIONS_LINE}\n{menu_lines(options)}\n\n{CONTROL_QUESTION}"


def control_head(design, st: "A.AssemblyState", terms: Sequence[ErrorTerm], feedback: Sequence[str]) -> str:
    """Everything the controller reads before the menu: the request, the ranked error vector (top
    rules.controller_error_terms), the design now and the earlier steps."""
    n = int(st.rules.values.get("controller_error_terms", 6))
    errs = "\n".join(f"{k}. {t.words()}" for k, t in enumerate(terms[:n], 1)) or "(none)"
    more = f"\n({len(terms) - n} more failing checks not shown)" if len(terms) > n else ""
    past = ("\n\nEarlier steps:\n" + "\n".join(f"- {f}" for f in feedback)) if feedback else ""
    return (f"Request: {design.base_request or design.request}\n\n"
            f"The design was built and measured. Requirements that fail now (worst first):\n{errs}{more}\n\n"
            f"The design now:\n{state_words(st)}{past}")


def control_prompt(design, st: "A.AssemblyState", terms: Sequence[ErrorTerm], options: Sequence[Action],
                   feedback: Sequence[str]) -> str:
    """The controller's question with the menu in the order given (R02: content-keyed; the loop shows seeded shuffles
    of Python's enumeration, see ask)."""
    return menu_prompt(control_head(design, st, terms, feedback), options)


def ask(llm, render: Callable[[List[Action]], str], options: Sequence[Action], rules: Mapping[str, Any],
        seed_material: str) -> "menus.MenuVote":
    """One permutation-voted menu question (R02, menus.perm_vote): the options (Python's enumeration, the schema enum and
    the stub's first option) are shown in rules.menu_orderings seeded orders; the controller answers a reason and an
    action id. Returns the MenuVote (pick = an action id, or None when no answer was valid)."""
    by_id = {a.id: a for a in options}
    if len(by_id) != len(options):
        raise ValueError(f"duplicate action ids in the menu: {[a.id for a in options]}")
    return menus.perm_vote(llm, CONTROL_LABEL, lambda order: render([by_id[i] for i in order]), list(by_id), rules,
                           seed_material)


def accept(old: cc.ErrorKey, new: cc.ErrorKey, trust: float) -> Tuple[bool, str]:
    """Keep a step only when the controllable error does not rise beyond the trust region: fewer hard failures, or as
    many with the summed violation at most `trust` above the old one."""
    if new.hard_failures < old.hard_failures:
        return True, f"fewer failing checks ({old.hard_failures} -> {new.hard_failures})"
    if new.hard_failures > old.hard_failures:
        return False, f"more failing checks ({old.hard_failures} -> {new.hard_failures})"
    if new.violation <= old.violation + trust + 1e-12:
        how = "lower" if new.violation < old.violation - 1e-12 else "within the trust region"
        return True, f"violation {old.violation:.4g} -> {new.violation:.4g} ({how})"
    return False, f"violation rose {old.violation:.4g} -> {new.violation:.4g} (trust region {trust:g})"


def is_stub(llm) -> bool:
    return bool(getattr(llm, "stub", False))


def ncalls(llm) -> int:
    """The LLM calls so far (OllamaAgent counts them; a scripted fake keeps a list)."""
    c = getattr(llm, "calls", 0)
    return len(c) if isinstance(c, (list, tuple)) else int(c or 0)


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------


def key_dict(k: cc.ErrorKey) -> dict:
    return {"hard_failures": k.hard_failures, "violation": k.violation}


def search_rules(values: Mapping[str, Any]) -> Dict[str, int]:
    """The verifier-search budget (R02, design_rules.json): k candidates per step, lookahead depth (1 = best-of-N; deeper
    lookahead is not implemented and is clipped to 1, recorded in the trace), plant evaluations per run."""
    k = max(1, int(values.get("controller_search_k", 1)))
    depth = int(values.get("controller_search_depth", 1))
    return {"k": k, "depth": 1, "depth_requested": depth,
            "max_evals": max(0, int(values.get("controller_search_max_evals", k * 6)))}


def search_candidates(vote: "menus.MenuVote", k: int, evals_left: int) -> List[str]:
    """The action ids the verifier measures this step (R02): every action the controller voted for, most votes first;
    when the vote is not consistent across orderings, the next-ranked alternatives too (canonical order); at most k ids,
    and at most evals_left of them other than stop (stop costs no plant evaluation). evals_left is a hard cap (review
    fix 2: rules.controller_search_max_evals bounds the run's plant evaluations; none is measured once it is spent). A
    confident stop is the only candidate, whatever rules.menu_consistency_min allows other actions to have votes."""
    if vote.confident and vote.pick == STOP:
        return [STOP]
    ranked = vote.ranked()
    out = [i for i in ranked if vote.votes.get(i, 0) > 0][:k]
    if not vote.confident:
        out += [i for i in ranked if i not in out][: max(0, k - len(out))]
    trimmed, n = [], 0
    for i in out:
        if i != STOP:
            if n >= max(0, evals_left):
                continue
            n += 1
        trimmed.append(i)
    return trimmed


def evaluate(design, llm, st: "A.AssemblyState", accepted: Sequence[dict], action: Action, record: Mapping[str, Any],
             by: str, control: Optional[Mapping[str, Any]] = None) -> dict:
    """Apply one candidate action on a fork of the checkpoint it invalidates (every accepted action re-applied first),
    re-run the stages from there and measure on manifold. Returns {fork, err, plan, results, links}; err is the typed
    reason the action could not be applied (any exception of a re-run stage or the build: reviewer finding F5). `control`:
    the controller bookkeeping the fork starts from (fork_from; the loop passes the step's pre-candidate snapshot)."""
    out: Dict[str, Any] = {"fork": None, "err": None, "plan": None, "results": None, "links": None}
    design_fork = copy.copy(design)
    try:
        fork = fork_from(st, action.invalidates, control)
        design_fork.assy = fork
        out["fork"] = fork
        for done in accepted:
            apply_action(fork, Action.from_dict(done["action"]), done["record"], done.get("by", CONTROLLER_BY))
        apply_action(fork, action, record, by)
        err = rerun(design_fork, llm, action.invalidates)
        if err is None:
            fork.assumptions = dedupe(fork.assumptions)
            out["plan"], out["results"], out["links"] = plant(fork)
        out["err"] = err
    except AssertionError:
        raise                       # a scripted test's unexpected question: never hidden as an infeasible action
    except Exception as e:          # noqa: BLE001 - the loop never fails the tree (F5)
        out["err"] = f"{type(e).__name__}: {e}"
    return out


def _sel_key(c: dict, rank: Mapping[str, int]) -> Tuple:
    e = c["error_after"]
    return (e["hard_failures"], round(float(e["violation"]), 9), rank.get(c["id"], 10 ** 6))


def run_loop(design, llm) -> dict:
    """The closed loop on design.assy (a derived initial proposal). Mutates the state in place when a step is accepted
    and leaves the trajectory in st.trajectory; returns it.

    Each step (R02): the content-keyed menu is asked under seeded orderings (permutation vote); the surviving actions
    (search_candidates) are each applied on a fork and measured; among those the acceptance rule keeps (no more failing
    checks, the trust region), and stop when it is a candidate (the current error), the lowest controllable error wins,
    the controller's vote ranking breaking ties. Every candidate is logged with its measured error.

    Review fixes: every candidate of a step forks from the controller bookkeeping as it was before the step; when a
    candidate is infeasible, its infeasibility is merged after the step's evaluations and the current design and every
    feasible fork are re-measured under the merged sensor typing before acceptance (B1). The run measures at most
    rules.controller_search_max_evals forks in all; once spent the loop stops before asking (2). A confident stop ends
    the loop with no evaluation (search_candidates)."""
    st = design.assy
    r = st.rules.values
    budget = 0 if is_stub(llm) else int(r.get("controller_step_budget", 0))
    trust = float(r.get("controller_trust_region", 0.0))
    vr = menus.vote_rules(r)
    sr = search_rules(r)
    started = time.time()
    trace: Dict[str, Any] = {"schema": TRACE_SCHEMA, "controller": "stub" if is_stub(llm) else "llm",
                             "budget": budget, "trust_region": trust, "vote_rules": dict(vr), "search": dict(sr),
                             "steps": [], "stop": None, "evals": 0}
    st.trajectory = trace
    try:
        plan, results, links = plant(st)
    except AssertionError:
        raise
    except Exception as e:          # noqa: BLE001 - F5
        trace["stop"] = {"reason": f"the initial build failed: {type(e).__name__}: {e}", "step": 0}
        return trace
    terms = error_vector(st, results, links)
    key = error_key(results)
    trace["steps"].append({"step": 0, "kind": "initial", "state": state_digest(st), "error": key_dict(key),
                           "failing": [t.check for t in terms], "terms": [t.to_dict() for t in terms]})
    tabu: List[str] = []
    feedback: List[str] = []
    accepted: List[dict] = list(st.control.get("accepted", []))     # [{action: Action.to_dict(), record, by}]
    step = 0
    evals = 0
    nterms = int(r.get("controller_error_terms", 6))
    while True:
        offered = menu(st, results, tabu)
        if not offered:
            trace["stop"] = {"reason": "no failing check has an action" if any(not x.passed for x in results)
                             else "every check passes", "step": step}
            break
        if step >= budget:
            trace["stop"] = {"reason": "stub controller: no corrective steps" if is_stub(llm) else
                             f"step budget spent ({budget})", "step": step}
            break
        if evals >= sr["max_evals"]:           # review fix 2: max_evals is a hard cap on the run's plant evaluations
            trace["stop"] = {"reason": f"search evaluation budget spent ({sr['max_evals']} plant evaluations)",
                             "step": step}
            break
        step += 1
        options = offered + [STOP_ACTION]          # Python's enumeration: the schema enum and the stub's first option
        by_id = {a.id: a for a in options}
        before = state_digest(st)
        head = control_head(design, st, terms, feedback)
        seed = menus.material(design.base_request or design.request, before["decisions"], step, menus.run_seed(llm),
                              CONTROL_LABEL)
        calls0, t0 = ncalls(llm), time.time()
        vote = ask(llm, lambda order: menu_prompt(head, order), options, vr, seed)
        rank = {i: n for n, i in enumerate(vote.ranked())}
        row: Dict[str, Any] = {"step": step, "state_before": before["decisions"], "state_summary": before["summary"],
                               "error_before": key_dict(key), "terms_before": [t.to_dict() for t in terms[:nterms]],
                               "menu": [a.to_dict() for a in options], "orders": vote.orders, "vote": vote.to_dict(),
                               "votes": dict(vote.votes), "consistency": vote.consistency,
                               "confident": vote.confident, "chosen": vote.pick}
        cands = [] if vote.pick is None else search_candidates(vote, sr["k"], sr["max_evals"] - evals)
        if not cands or cands == [STOP]:
            row.update(action=STOP_ACTION.to_dict(), selected=STOP if cands else None, selected_by="llm",
                       candidates=[{"id": STOP, "outcome": "stop", "votes": vote.votes.get(STOP, 0), "rank": 0,
                                    "error_after": key_dict(key)}] if cands else [],
                       accepted=None, outcome="stop",
                       reason="no valid controller answer" if vote.pick is None else "the controller chose stop",
                       evals=0, llm_calls=ncalls(llm) - calls0, secs=round(time.time() - t0, 2))
            trace["steps"].append(row)
            trace["stop"] = {"reason": row["reason"], "step": step}
            break
        evaluated: List[dict] = []
        measured: Dict[str, dict] = {}            # every feasible candidate: its fork and measurement
        # review fix B1: every candidate of this step forks from the bookkeeping as it was before the step, and a
        # candidate found infeasible is collected here, not written to the live state mid-step (a sensor types a failure
        # as a conflict once its every action is infeasible: assembly.coverage_check / closure_evidence_check; a later
        # fork must not be measured under a different typing than `key` and the stop candidate)
        control0 = copy.deepcopy(dict(st.control))
        infeasible_now: Dict[str, str] = {}
        for cid in cands:
            if cid == STOP:
                evaluated.append({"id": STOP, "action": STOP_ACTION.to_dict(), "votes": vote.votes.get(STOP, 0),
                                  "rank": rank[STOP], "outcome": "stop", "error_after": key_dict(key),
                                  "reason": "keep the design as it is"})
                continue
            action = by_id[cid]
            by = CONTROLLER_BY if vote.votes.get(cid, 0) > 0 else SEARCH_BY
            record = {"step": step, "votes": dict(vote.votes), "consistency": vote.consistency,
                      "confident": vote.confident, "evidence": list(action.evidence), "menu": len(options)}
            t1 = time.time()
            ev = evaluate(design, llm, st, accepted, action, record, by, control=control0)
            evals += 1
            cand: Dict[str, Any] = {"id": cid, "action": action.to_dict(), "votes": vote.votes.get(cid, 0),
                                    "rank": rank[cid], "by": by}
            if ev["err"] is not None:
                infeasible_now[action.key] = ev["err"]
                cand.update(outcome="infeasible", reason=f"infeasible: {ev['err']}", error_after=None)
            else:
                measured[cid] = dict(ev, record=record, by=by, action=action)
            cand["secs"] = round(time.time() - t1, 2)
            evaluated.append(cand)
        if infeasible_now:
            # merge the step's infeasibility, then re-measure the current design and every feasible fork under the
            # merged typing, so `key`, the stop candidate and each candidate are compared on the same sensors
            st.control.setdefault("infeasible", {}).update(infeasible_now)
            merged = dict(st.control["infeasible"])
            try:
                plan, results, links = plant(st)
                key, terms = error_key(results), error_vector(st, results, links)
            except AssertionError:
                raise
            except Exception:       # noqa: BLE001 - F5: the current design built before; keep its measurement
                pass
            for c in evaluated:
                if c["id"] == STOP:
                    c["error_after"] = key_dict(key)
            row["error_before_retyped"] = key_dict(key)
            for cid, m in list(measured.items()):
                m["fork"].control["infeasible"] = dict(merged)
                try:
                    m["plan"], m["results"], m["links"] = plant(m["fork"])
                except AssertionError:
                    raise
                except Exception as e:  # noqa: BLE001 - F5
                    measured.pop(cid)
                    c = next(x for x in evaluated if x["id"] == cid)
                    c.update(outcome="infeasible", reason=f"infeasible: {type(e).__name__}: {e}", error_after=None)
        forks: Dict[str, dict] = {}
        for c in evaluated:
            m = measured.get(c["id"])
            if m is None:
                continue
            key2 = error_key(m["results"])
            ok, why = accept(key, key2, trust)
            c.update(outcome="acceptable" if ok else "undone", reason=why, error_after=key_dict(key2),
                     state_after=state_digest(m["fork"])["decisions"],
                     failing_after=[x.check_id for x in m["results"] if not x.passed],
                     sensor_delta={"hard_failures": key2.hard_failures - key.hard_failures,
                                   "violation": round(key2.violation - key.violation, 6)})
            if ok:
                forks[c["id"]] = dict(m, key=key2)
        pool = [c for c in evaluated if c["outcome"] in ("acceptable", "stop")]
        best = min(pool, key=lambda c: _sel_key(c, rank)) if pool else None
        for c in evaluated:
            if c is best:
                c["outcome"] = "kept" if c["id"] != STOP else "stop"
            elif c["outcome"] == "acceptable":
                c["outcome"] = "not_selected"
        row.update(candidates=evaluated, evals=sum(1 for c in evaluated if c["id"] != STOP))
        for c in evaluated:
            if c["id"] == STOP:
                continue
            a = by_id[c["id"]]
            words = f"{c['id']}"
            if c["outcome"] == "infeasible":
                tabu.append(a.key)
                why = _short(c["reason"].removeprefix("infeasible: "), 120)
                feedback.append(f"step {step}: {words} could not be applied ({why}); the design is unchanged")
            elif c["outcome"] == "undone":
                tabu.append(a.key)
                feedback.append(f"step {step}: {words} was undone: {c['reason']}; now failing: "
                                f"{', '.join(c['failing_after'])[:200]}")
            elif c["outcome"] == "not_selected":
                feedback.append(f"step {step}: {words} was measured ({c['reason']}) but another action measured lower")
        if best is not None and best["id"] == STOP:
            row.update(action=STOP_ACTION.to_dict(), selected=STOP,
                       selected_by="llm" if vote.pick == STOP else "search", accepted=None, outcome="stop",
                       reason="the controller chose stop" if vote.pick == STOP else
                       "search: no candidate action lowered the error below the current design; stop")
            row.update(llm_calls=ncalls(llm) - calls0, secs=round(time.time() - t0, 2))
            trace["steps"].append(row)
            trace["stop"] = {"reason": row["reason"], "step": step}
            break
        if best is None:
            only = evaluated[0] if len(evaluated) == 1 else None
            row.update(action=(only or {}).get("action") or by_id[cands[0]].to_dict(), selected=None,
                       selected_by=None, accepted=False,
                       outcome=(only or {}).get("outcome", "undone"),
                       reason=only["reason"] if only else "; ".join(f"{c['id']}: {c['reason']}" for c in evaluated),
                       error_after=(only or {}).get("error_after"),
                       **({"state_after": only["state_after"], "failing_after": only["failing_after"]}
                          if only and only.get("state_after") else {}))
        else:
            f = forks[best["id"]]
            action, fork = f["action"], f["fork"]
            tabu.append(action.key)
            accepted.append({"action": action.to_dict(), "record": dict(f["record"]), "by": f["by"]})
            fork.control["accepted"] = list(accepted)
            fork.control["infeasible"] = dict(st.control.get("infeasible", {}))
            fork.trajectory = trace
            st.__dict__.update(fork.__dict__)
            plan, results, links, key = f["plan"], f["results"], f["links"], f["key"]
            terms = error_vector(st, results, links)
            row.update(action=action.to_dict(), selected=best["id"],
                       selected_by="llm" if best["id"] == vote.pick else ("search" if best["by"] == SEARCH_BY
                                                                          else "search_among_votes"),
                       accepted=True, outcome="kept", reason=best["reason"], error_after=key_dict(key),
                       state_after=state_digest(st)["decisions"],
                       failing_after=[x.check_id for x in results if not x.passed],
                       sensor_delta=best.get("sensor_delta"))
            feedback.append(f"step {step}: {best['id']} was kept: {best['reason']}")
        row.update(llm_calls=ncalls(llm) - calls0, secs=round(time.time() - t0, 2))
        trace["steps"].append(row)
    trace["evals"] = evals
    trace["final"] = {"state": state_digest(st), "error": key_dict(key), "failing": [t.check for t in terms],
                      "terms": [t.to_dict() for t in terms]}
    trace["secs"] = round(time.time() - started, 2)
    st.control["accepted"] = accepted
    st.trajectory = trace
    return trace


class ControllerLoop(A.AssemblyStep):
    """The closed loop after the first (manifold) build of the initial proposal; never fails the tree (the package is
    always written and finalize reports the outcome)."""

    def __init__(self, design, llm):
        super().__init__("ControllerLoop", design, llm)

    def update(self) -> Status:
        st = self.state
        st.stage = "controller"
        trace = run_loop(self.design, self.llm)
        st = self.state
        st.stage = "controller"
        steps = [s for s in trace["steps"] if s.get("kind") != "initial"]
        kept = sum(1 for s in steps if s.get("accepted"))
        st.notes.append(f"controller: {len(steps)} step(s), {kept} kept; stop: {trace['stop']['reason']}")
        self.logger.info(st.notes[-1])
        return Status.SUCCESS


def trace_record(st: "A.AssemblyState") -> dict:
    """controller_trace.json: the trajectory plus the run's authority audit (every recorded decision classified)."""
    out = dict(st.trajectory or {"schema": TRACE_SCHEMA, "steps": [], "stop": {"reason": "the loop did not run"}})
    out["authority"] = authority(st)
    out["accepted"] = [dict(d["action"], step=d["record"].get("step")) for d in st.control.get("accepted", [])]
    return out


def controller_summary(st: "A.AssemblyState") -> dict:
    """design.json assembly.controller: kind, steps, kept, stop reason."""
    t = st.trajectory or {}
    steps = [s for s in t.get("steps", []) if s.get("kind") != "initial"]
    return {"kind": t.get("controller"), "budget": t.get("budget"), "steps": len(steps),
            "kept": sum(1 for s in steps if s.get("accepted")), "stop": (t.get("stop") or {}).get("reason")}


# ---------------------------------------------------------------------------
# One question, one answer per run: re-run stages reuse the answers to questions they ask again
# ---------------------------------------------------------------------------


class QuestionCache:
    """The controller's answers within one run, memoised: a question asked again with the same label, prompt, schema and
    sampling (temperature, seed) gets the answer it got the first time, with no LLM call. A stage the closed loop
    re-runs after an action asks such questions again (the vent size mapping after an `expose`); the seeded 9B gives
    the same answer to the same prompt, so the cache changes no decision and saves the calls. p_yes is memoised by
    (label, prompt). Everything else is the wrapped controller's (attributes, transcripts, call counts)."""

    def __init__(self, llm):
        self._llm = llm
        self._answers: Dict[Any, Any] = {}
        self.hits = 0

    def __getattr__(self, name):
        return getattr(self._llm, name)

    def ask_json(self, prompt: str, schema: dict, **kwargs) -> dict:
        key = ("json", kwargs.get("label"), prompt, json.dumps(schema, sort_keys=True), kwargs.get("temperature"),
               kwargs.get("seed"), kwargs.get("system"))
        if key in self._answers:
            self.hits += 1
            return copy.deepcopy(self._answers[key])
        answer = self._llm.ask_json(prompt, schema, **kwargs)
        self._answers[key] = copy.deepcopy(answer)
        return answer

    def p_yes(self, prompt: str, label: str = "p_yes", system: str = "", images: Sequence[Path] = ()) -> float:
        key = ("p_yes", label, prompt, system, tuple(str(i) for i in images))
        if key not in self._answers:
            self._answers[key] = self._llm.p_yes(prompt, label=label, system=system, images=images)
        else:
            self.hits += 1
        return self._answers[key]

    def p_yes_many(self, prompts: Sequence[str], label: Any = "p_yes", system: str = "",
                   images: Sequence[Path] = ()) -> List[float]:
        labels = [label] * len(prompts) if isinstance(label, str) else list(label)
        keys = [("p_yes", lb, q, system, tuple(str(i) for i in images)) for q, lb in zip(prompts, labels)]
        todo = [k for k, key in enumerate(keys) if key not in self._answers]
        self.hits += len(keys) - len(todo)
        if todo:
            ask = getattr(self._llm, "p_yes_many", None)
            got = ask([prompts[k] for k in todo], [labels[k] for k in todo], system, images) if ask else \
                [self._llm.p_yes(prompts[k], labels[k], system, images) for k in todo]
            for k, v in zip(todo, got):
                self._answers[keys[k]] = v
        return [self._answers[key] for key in keys]


# ---------------------------------------------------------------------------
# The stub controller (D1 authority probe): the first offered option, no corrective steps, no LLM calls
# ---------------------------------------------------------------------------


def first_option(schema: Mapping[str, Any]) -> Any:
    """The first offered option of a JSON schema: an enum's first value; an object's properties each at their first
    option; an integer / number at its minimum (0 when none); a boolean False; a string ""."""
    if not isinstance(schema, Mapping):
        return None
    if schema.get("enum"):
        return schema["enum"][0]
    t = schema.get("type")
    if t == "object":
        return {k: first_option(v) for k, v in (schema.get("properties") or {}).items()}
    if t == "array":
        return []
    if t in ("integer", "number"):
        return schema.get("minimum", 0)
    if t == "boolean":
        return False
    return ""


class StubController:
    """A controller with no information: every schema-constrained question gets the first offered option of each key,
    every p_yes is 0.5 (so a ranking keeps Python's enumeration order), and the closed loop takes no corrective step.
    It makes no network call; its questions and answers are written to llm/ like any transcript (marked STUB).

    R02: menus are shown in seeded shuffled orders, but every schema enum stays in Python's unshuffled enumeration
    order (menus.perm_vote; the model never sees the schema), so the stub's "first offered option" is the first option
    of Python's enumeration, not of a shuffle: it stays the same no-information baseline under every ordering."""

    stub = True
    model = "stub"
    judges: List[Any] = []
    seed_offset = 0

    def __init__(self, log_dir: Optional[Path] = None, **_):
        self.log_dir = Path(log_dir) if log_dir else None
        self.calls = 0

    def _log(self, label: str, prompt: str, text: str) -> None:
        self.calls += 1
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            (self.log_dir / f"{self.calls:03d}_{label}.txt").write_text(
                f"MODEL: STUB (first offered option; no LLM call)\nIMAGES: []\n\n=== SYSTEM ===\n\n\n"
                f"=== PROMPT ===\n{prompt}\n\n=== RESPONSE ===\n{text}\n")

    def chat(self, prompt: str, system: str = "", images: Sequence[Path] = (), schema: Optional[dict] = None,
             temperature: float = 0.0, seed: int = 0, label: str = "ask", num_predict: Optional[int] = None) -> str:
        text = json.dumps(first_option(schema) if schema else "")
        self._log(label, prompt, text)
        return text

    def ask_json(self, prompt: str, schema: dict, **kwargs) -> dict:
        data = json.loads(self.chat(prompt, schema=schema, **kwargs))
        if not isinstance(data, dict):
            raise ValueError("the reply was not a JSON object")
        return data

    def p_yes(self, prompt: str, label: str = "p_yes", system: str = "", images: Sequence[Path] = ()) -> float:
        self._log(label, prompt, "p_yes=0.500")
        return 0.5

    def p_yes_many(self, prompts: Sequence[str], label: Any = "p_yes", system: str = "",
                   images: Sequence[Path] = ()) -> List[float]:
        labels = [label] * len(prompts) if isinstance(label, str) else list(label)
        return [self.p_yes(q, lb) for q, lb in zip(prompts, labels)]

    def yes_score(self, prompt: str, label: str = "yes_no", **kwargs) -> float:
        self._log(label, prompt, "yes_score=0.5")
        return 0.5

    def vote(self, prompt: str, schema: dict, keys: Sequence[str], n: int = 1, **kwargs) -> Tuple[Optional[dict], int]:
        return self.ask_json(prompt, schema, **kwargs), 1
