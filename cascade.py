"""Two-level cascade control for cad_agent (opt-in: --mode cascade --l1 ...).

The default pipeline asks the model whether each part "is what the person asked
for" and repairs until it says yes. That verdict is lenient and unsigned. The
cascade instead turns the person's L1 requirements into typed checks
(cad_checks) BEFORE the design phase, freezes them, and then drives the design
towards zero check error like a controller drives a plant:

    reference  = the frozen checks (what "right" means)
    measure    = Python runs every check -> signed margins, evidence
    error      = lexicographic (hard failures, summed violation, soft error)
    correction = deadbeat for invertible dimension errors (Python sets the
                 parameter), a Python neighbourhood search localised by a
                 finite-difference sensitivity matrix for structural errors,
                 and the LLM only where Python has no move left
    acceptance = strict decrease of the error only (monotone, Lyapunov-like)

Two levels. The inner loop drives the design against the checks. The outer
loop (CEGAR-style, light) adjusts the checks themselves: when an L1's own check
fails while all its design-guidance sub-checks (level 2) pass, the
decomposition is too weak, so the LLM is asked for more sub-checks; when the L1
check passes but sub-checks fail, those sub-checks over-constrain and are
dropped. Every loop ends with a TYPED report (converged / saturated /
uncontrollable / stagnated, the residual errors and the best state), and the
run ends with a verification matrix for the person - never a silent "verified".

Who checks the checks: the LLM only fills typed JSON templates; Python renders
each check back into English, and a check is accepted only if it validates,
kills a Python-generated mutant of a provisional design (non-vacuity), the L1's
numbers all appear in its checks (coverage) and the LLM agrees the English
rendering tests the L1 (back-translation).

The tree (cad_agent's understand/build stages are reused unchanged):

    cad_cascade (Sequence)
    ├── review_loop (Retry)
    │   └── cascade_design (Sequence)
    │       ├── provisional_loop (Retry)        cad_agent: components, numbers, build
    │       ├── translate (ForEach L1)          ControlLoop per L1: LLM fills check templates, gates
    │       ├── FreezeChecks                    + system checks; writes checks.json
    │       ├── outer_loop (Retry, <= 3 refinements)
    │       │   └── outer_pass (Sequence)
    │       │       ├── ControlLoop "design"    inner loop: design vs frozen checks
    │       │       └── RefineChecks            CEGAR: add or drop level-2 sub-checks
    │       ├── Rebuild                         OpenSCAD of the best design
    │       ├── RenderViews
    │       ├── WriteMatrix                     verification_matrix.md / .json
    │       └── CascadeReview                   the person sees the matrix
    └── ExportModel
"""

import copy
import hashlib
import json
from collections import Counter
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

import py_trees
from py_trees.common import Status

import cad_checks as cc

ca = cc._ca()  # cad_agent (the running script's module when cad_agent.py is __main__)

MAX_OUTER = 30             # outer-loop refinements of the check set
TRANSLATE_ITERATIONS = 30  # LLM proposals per L1
DESIGN_ITERATIONS = 120    # accepted-or-rejected corrections of the inner loop
DESIGN_PATIENCE = 30       # consecutive rejected corrections before "stagnated"
BT_THRESHOLD = 0.6         # back-translation P(yes) needed (measured: correct >= 0.69, wrong part <= 0.53)
ACCEPT_EPS = 0.01         # smallest violation decrease the design loop accepts: below it a move
                          # mostly spends other checks' tolerance (a 4 mm panel shaved to 3.6 mm
                          # so a failing relation's margin moved by 0.006)
RANK_LIMIT = 4             # tied candidates the LLM ranks at most
FILL_TOKENS = 600          # reply caps (see OllamaAgent.chat): templates are short
TYPES_TOKENS = 120
SYSTEM_L1 = "SYS"          # l1_id of the checks Python adds on its own


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_") or "x"


def stable_hash(obj: Any) -> str:
    return hashlib.sha1(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# ControlLoop: a reusable closed loop as a py_trees composite
# ---------------------------------------------------------------------------


@dataclass
class Measurement:
    """What a loop's sensor reports about one state.

    `error` is compared lexicographically (lower is better); `failing` lists the
    hard items still wrong (empty = converged); `uncontrollable` is filled by the
    loop's diagnose() for the best state: failing items no available move can
    change, which the loop reports at once instead of spending attempts on them.
    """
    error: cc.ErrorKey
    failing: List[str] = field(default_factory=list)
    residual: List[str] = field(default_factory=list)
    uncontrollable: List[str] = field(default_factory=list)
    data: Any = None


@dataclass
class LoopContext:
    """Everything a proposer may use: the best state so far and the errors of what was tried."""
    loop_id: str
    iteration: int
    best_state: Any
    best: Measurement
    history: List[dict]
    rejected: Set[str]


@dataclass
class LoopReport:
    """How a loop ended. Typed, so a caller can never mistake "gave up" for "passed"."""
    loop_id: str
    status: str                  # converged | saturated | uncontrollable | stagnated
    iterations: int
    best_error: dict
    residual: List[str]
    uncontrollable: List[str]
    reference: str               # hash of the reference the loop tracked
    best_key: str
    history: List[dict]
    best_state: Any = None

    @property
    def converged(self) -> bool:
        return self.status == "converged"

    def to_dict(self) -> dict:
        out = asdict(self)
        out.pop("best_state", None)
        return out


class _LoopStep(py_trees.behaviour.Behaviour):
    """One phase of a ControlLoop iteration (propose, measure or accept)."""

    def __init__(self, name: str, fn: Callable[[], Status]):
        super().__init__(name)
        self.fn = fn

    def update(self):
        return self.fn()


class ControlLoop(py_trees.composites.Sequence):
    """reference -> propose -> measure -> accept, one iteration per tick, until a typed stop.

    Internally a memory Sequence of three leaves; the composite re-arms them after
    every iteration and returns RUNNING, so a long search never blocks the tree.

    - Acceptance is monotone: a proposal replaces the best state only when
      `accept(new_error, best_error)` (default: strict lexicographic decrease).
      The best state is therefore never worse than the starting point.
    - Memory (rejected state keys, history) is keyed by a hash of the reference.
      When the reference changes (the checks were refined) the memory is reset:
      states rejected against old checks may be right for the new ones
      (anti-windup).
    - Stops: SUCCESS when done(best) ("converged"); FAILURE with status
      "uncontrollable" when every failing item is one nothing can move,
      "stagnated" when the proposer has nothing new or `patience` proposals in a
      row were rejected, "saturated" after `max_iterations`.
    - The LoopReport is written to the blackboard under /loop/<loop_id>/ and to
      the `reports` dict (shared design state), and returned by `report`.
    """

    def __init__(self, name: str, loop_id: str, *,
                 reference: Callable[[], Any],
                 initial: Callable[[], Any],
                 propose: Callable[[Any, LoopContext], Any],
                 measure: Callable[[Any], Measurement],
                 commit: Optional[Callable[[Any, Measurement], None]] = None,
                 accept: Callable[[cc.ErrorKey, cc.ErrorKey], bool] = cc.strictly_better,
                 done: Optional[Callable[[Measurement], bool]] = None,
                 diagnose: Optional[Callable[[Any, Measurement], List[str]]] = None,
                 state_key: Optional[Callable[[Any], str]] = None,
                 max_iterations: int = 10, patience: int = 3,
                 reports: Optional[Dict[str, dict]] = None):
        super().__init__(name, memory=True, children=[
            _LoopStep("propose", self._propose), _LoopStep("measure", self._measure),
            _LoopStep("accept", self._accept)])
        self.loop_id = loop_id
        self.reference, self.initial, self.propose_fn, self.measure_fn = reference, initial, propose, measure
        self.commit_fn = commit
        self.accept_fn = accept
        self.done_fn = done or (lambda m: not m.failing)
        self.diagnose_fn = diagnose
        self.state_key = state_key or stable_hash
        self.max_iterations, self.patience = max_iterations, patience
        self.reports = reports if reports is not None else {}
        self.bb = py_trees.blackboard.Client(name=f"loop:{loop_id}", namespace=f"/loop/{slug(loop_id)}")
        for key in ("report", "status", "best_error", "iterations"):
            self.bb.register_key(key=key, access=py_trees.common.Access.WRITE)
        self.ref_hash: Optional[str] = None
        self.rejected: Set[str] = set()
        self.history: List[dict] = []
        self.report: Optional[LoopReport] = None
        self._reset_run()

    # ----- bookkeeping -----

    def _reset_run(self) -> None:
        self.iterations = 0
        self.streak = 0                 # consecutive rejected proposals
        self.exhausted = False          # the proposer had nothing new
        self.best_state: Any = None
        self.best: Optional[Measurement] = None
        self.candidate: Any = None
        self.cand_m: Optional[Measurement] = None
        self.final: Optional[str] = None

    def context(self) -> LoopContext:
        return LoopContext(self.loop_id, self.iterations, self.best_state, self.best, self.history, self.rejected)

    def _diagnose(self) -> None:
        if self.diagnose_fn is not None and self.best.failing:
            self.best.uncontrollable = list(self.diagnose_fn(self.best_state, self.best))

    def _log_entry(self, key: str, m: Measurement, accepted: bool, note: str = "") -> None:
        self.history.append({"iteration": self.iterations, "key": key, "error": m.error.to_dict() if m else None,
                             "accepted": accepted, "failing": list(m.failing) if m else [],
                             "residual": list(m.residual[:6]) if m else [], "note": note})

    def _start(self) -> None:
        ref = self.reference()
        h = stable_hash(ref)
        if h != self.ref_hash:
            if self.ref_hash is not None:
                self.logger.info(f"{self.loop_id}: reference changed; loop memory reset")
            self.ref_hash, self.rejected, self.history = h, set(), []
        self._reset_run()
        self.best_state = self.initial()
        self.best = self.measure_fn(self.best_state)
        self._diagnose()
        self._log_entry(self.state_key(self.best_state), self.best, True, "initial")
        if self.commit_fn is not None:
            self.commit_fn(self.best_state, self.best)
        self.final = self._stop_reason(start=True)

    def _stop_reason(self, start: bool = False) -> Optional[str]:
        m = self.best
        if self.done_fn(m):
            return "converged"
        if m.failing and set(m.failing) <= set(m.uncontrollable):
            return "uncontrollable"
        if start:
            return "saturated" if self.max_iterations <= 0 else None
        if self.exhausted or self.streak >= self.patience:
            return "stagnated"
        if self.iterations >= self.max_iterations:
            return "saturated"
        return None

    def _finish(self) -> Status:
        m = self.best
        self.report = LoopReport(
            self.loop_id, self.final, self.iterations, m.error.to_dict(), list(m.residual),
            list(m.uncontrollable), self.ref_hash or "", self.state_key(self.best_state),
            [dict(h) for h in self.history], self.best_state)
        self.reports[self.loop_id] = self.report.to_dict()
        self.bb.set("report", self.report)
        self.bb.set("status", self.final)
        self.bb.set("best_error", m.error.to_dict())
        self.bb.set("iterations", self.iterations)
        msg = (f"{self.loop_id}: {self.final} after {self.iterations} iteration(s); error "
               f"{m.error.hard_failures} hard / {m.error.violation:.3f} / {m.error.soft:.3f}")
        if self.final == "converged":
            self.logger.info(msg)
        else:
            self.logger.warning(msg + (f"; residual: {'; '.join(m.residual[:4])}" if m.residual else ""))
        self.feedback_message = self.final
        return Status.SUCCESS if self.final == "converged" else Status.FAILURE

    # ----- the three phases -----

    def _propose(self) -> Status:
        cand = self.propose_fn(self.best_state, self.context())
        if cand is None:
            self.exhausted = True
            return Status.FAILURE
        key = self.state_key(cand)
        if key in self.rejected or key == self.state_key(self.best_state):
            # Never pay to measure a state that is already known; it still counts as a try.
            self.iterations += 1
            self.streak += 1
            self._log_entry(key, None, False, "already tried")
            return Status.FAILURE
        self.candidate = cand
        return Status.SUCCESS

    def _measure(self) -> Status:
        self.cand_m = self.measure_fn(self.candidate)
        return Status.SUCCESS

    def _accept(self) -> Status:
        key = self.state_key(self.candidate)
        ok = self.accept_fn(self.cand_m.error, self.best.error)
        self.iterations += 1
        self._log_entry(key, self.cand_m, ok)
        if ok:
            self.best_state, self.best, self.streak = self.candidate, self.cand_m, 0
            self._diagnose()
            if self.commit_fn is not None:
                self.commit_fn(self.best_state, self.best)
        else:
            self.rejected.add(key)
            self.streak += 1
        return Status.SUCCESS

    # ----- ticking -----

    def tick(self):
        if self.status != Status.RUNNING:
            for child in self.children:
                if child.status != Status.INVALID:
                    child.stop(Status.INVALID)
            self.current_child = self.children[0]
            self._start()
            if self.final is not None:
                self.stop(self._finish())
                yield self
                return
        index = self.children.index(self.current_child) if self.current_child in self.children else 0
        for child in self.children[index:]:
            self.current_child = child
            for node in child.tick():
                yield node
            if child.status == Status.RUNNING:
                self.status = Status.RUNNING
                yield self
                return
            if child.status != Status.SUCCESS:
                break  # nothing (new) proposed: the iteration ends here
        self.final = self._stop_reason()
        if self.final is not None:
            self.stop(self._finish())
        else:
            for child in self.children:
                child.stop(Status.INVALID)
            self.current_child = self.children[0]
            self.status = Status.RUNNING
        yield self


# ---------------------------------------------------------------------------
# Cascade state (shared through Design.cascade)
# ---------------------------------------------------------------------------


@dataclass
class CascadeState:
    l1: List[dict]
    drafts: Dict[str, List[cc.Check]] = field(default_factory=dict)     # per L1, before freezing
    checks: List[cc.Check] = field(default_factory=list)                # the frozen set
    frozen: bool = False
    version: int = 0
    translation: Dict[str, dict] = field(default_factory=dict)          # per L1: uncovered numbers, rejected
    gates: Dict[str, dict] = field(default_factory=dict)                # check id -> gate outcome
    dropped: List[dict] = field(default_factory=list)                   # level-2 checks the outer loop dropped
    refinements: List[dict] = field(default_factory=list)               # what each outer iteration changed
    reports: Dict[str, dict] = field(default_factory=dict)              # loop id -> LoopReport dict
    design_reports: List[dict] = field(default_factory=list)            # every inner-loop run, in order
    outer_iterations: int = 0
    rows: List[dict] = field(default_factory=list)                      # final verification matrix rows
    system_rows: List[dict] = field(default_factory=list)
    outcome: Optional[str] = None
    started: float = field(default_factory=time.time)
    bt_cache: Dict[str, float] = field(default_factory=dict)
    counter: int = 0
    last_results: Any = None                                            # inner loop's latest accepted results
    llm_calls: Optional[int] = None

    def next_id(self, l1_id: str, tag: str) -> str:
        self.counter += 1
        return f"{l1_id}.{tag}{self.counter}"

    def l1_by_id(self, l1_id: str) -> Optional[dict]:
        return next((r for r in self.l1 if r["id"] == l1_id), None)

    def summary(self) -> dict:
        return {"frozen": self.frozen, "version": self.version, "outcome": self.outcome,
                "checks": len(self.checks), "outer_iterations": self.outer_iterations,
                "l1": [{k: r[k] for k in ("l1_id", "status", "margin")} for r in self.rows],
                "loops": {k: {"status": v["status"], "iterations": v["iterations"]} for k, v in self.reports.items()}}


def checks_record(cs: CascadeState) -> dict:
    return {"version": cs.version, "frozen": cs.frozen, "l1": cs.l1,
            "checks": [c.to_dict() for c in cs.checks],
            "gates": cs.gates, "translation": cs.translation, "dropped": cs.dropped,
            "refinements": cs.refinements}


def write_checks(d) -> Path:
    path = d.workdir / "checks.json"
    d.workdir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(checks_record(d.cascade), indent=2, default=str))
    return path


# ---------------------------------------------------------------------------
# L1 -> typed checks: the LLM fills templates, Python owns the meaning
# ---------------------------------------------------------------------------

TYPE_DOCS = {
    "count": "how many copies of a part there are (or how many parts the whole object has)",
    "dimension": "one size of a part or of the whole object (width, depth, height, length, thickness, "
                 "diameter, inner diameter, tilt angle, or how high its top/bottom is above the table)",
    "shape": "which kind of shape a part is (box, panel, wedge, cylinder, tube, sphere) and which way it lies",
    "relation": "a part sits on top of / underneath / in front of / behind / left of / right of / beside "
                "another part, touching it (in front of = outside it, against its front face; for 'on X along "
                "its front edge' use on_top_of plus an edge test)",
    "edge": "a part is along the front, back, left or right edge of another part, or centred on it",
    "span": "a part runs the full width, depth or height of another part",
    "arrangement": "the copies of a part are at the corners, at the two ends, in a row, in a triangle or spread out",
    "touches": "a part is joined to another part with real face contact",
    "connected": "the parts form one connected solid body",
    "no_overlap": "no two parts pass through each other",
    "stable": "the object stands on a table without tipping over (optionally with a load on a part)",
    "fits": "a stand-in object (phone, tablet, laptop, book, pencil, or a box/cylinder of given size) fits "
            "into a part or between two parts",
    "rests_on": "a stand-in object leans against or lies on a part without sliding off or tipping",
}
INSPECTION_TYPES = ("count", "dimension", "shape", "relation", "edge", "span", "arrangement")
METHOD_TYPES = {
    "inspection": INSPECTION_TYPES,
    "analysis": ("stable", "connected", "touches", "no_overlap") + INSPECTION_TYPES,
    "demonstration": ("fits", "rests_on", "stable") + INSPECTION_TYPES,
    "test": ("fits", "rests_on", "stable", "touches", "connected") + INSPECTION_TYPES,
}
BEHAVIOURAL = ("fits", "rests_on", "stable")   # checks whose failure (with passing sub-checks) triggers refinement
WHOLE, ANY, NONE = "whole_object", "any", "none"


def offered_types(method: Optional[str]) -> Tuple[str, ...]:
    return METHOD_TYPES.get(str(method or "").lower(), tuple(TYPE_DOCS))


def _enum(values: Sequence[str]) -> dict:
    return {"type": "string", "enum": list(dict.fromkeys(values))}


def template(check_type: str, names: Sequence[str]) -> Tuple[dict, List[str], dict]:
    """(item schema, slot explanations, example) for one check type.

    Only the slots that change what a check means are offered; the rest keep
    cad_checks' defaults. Every offered slot is required, with an explicit
    "not applicable" value (whole_object, any, none, 0, []), because a small
    model given optional slots fills them with invented numbers.
    """
    names = list(names)
    shapes = list(ca.SHAPES) + ["round", "any"]
    n0 = names[0] if names else "base"
    n1 = names[1] if len(names) > 1 else n0
    T: Dict[str, Tuple[dict, List[str], dict]] = {
        "count": ({"part": _enum(names + [WHOLE]), "shape": _enum(shapes + [ANY]),
                   "count": {"type": "integer"}, "op": _enum(cc.OPS)},
                  ["part: the part to count (whole_object = count all parts)",
                   "shape: only count parts of this shape (any = every shape)",
                   "count: the number", "op: eq = exactly, ge = at least, le = at most"],
                  {"part": n1, "shape": ANY, "count": 4, "op": "eq"}),
        "dimension": ({"part": _enum(names + [WHOLE]), "measure": _enum(cc.MEASURES),
                       "value": {"type": "number"}, "op": _enum(cc.OPS), "tol": {"type": "number"}},
                      ["part: which part (whole_object = the whole object's overall size)",
                       "measure: width = left to right (X), depth = front to back (Y), height = vertical (Z), "
                       "length = longest size, thickness = thinnest size (a tube's wall), diameter, "
                       "inner_diameter, angle = tilt from the horizontal, top / bottom = height of its "
                       "top / bottom surface above the table",
                       "value: the number in mm (degrees for angle)",
                       "op: eq = equal, ge = at least, le = at most",
                       "tol: allowed error in mm; 0 = the default"],
                      {"part": n0, "measure": "width", "value": 150, "op": "eq", "tol": 0}),
        "shape": ({"part": _enum(names), "shape": _enum(shapes),
                   "orient": _enum(["flat", "upright", "x", "y", "z", ANY])},
                  ["part: which part", f"shape: one of {', '.join(shapes)} (round = cylinder, tube or sphere; "
                   "any = only its orientation matters)",
                   "orient: flat = lying flat, upright = standing up (a vertical panel or wall), "
                   "x / y / z = a round part's axis runs "
                   "left-right / front-back / vertical, any = not stated"],
                  {"part": n0, "shape": "box", "orient": "flat"}),
        "relation": ({"part": _enum(names), "relation": _enum(cc.RELATIONS), "other": _enum(names)},
                     ["part: the part that is placed", "relation: where it is relative to other",
                      "other: the part it is placed against"],
                     {"part": n1, "relation": "on_top_of", "other": n0}),
        "edge": ({"part": _enum(names), "other": _enum(names), "where": _enum(cc.EDGE_PLACES)},
                 ["part: the part that is placed", "other: the part whose edge it is on",
                  "where: front / back / left / right edge, or center = centred on it"],
                 {"part": n1, "other": n0, "where": "back"}),
        "span": ({"part": _enum(names), "other": _enum(names), "axis": _enum(("x", "y", "z"))},
                 ["part: the part that spans", "other: the part it spans",
                  "axis: x = full width (left to right), y = full depth (front to back), z = full height"],
                 {"part": n1, "other": n0, "axis": "x"}),
        "arrangement": ({"part": _enum(names), "pattern": _enum(cc.PATTERNS), "other": _enum(names + ["parent"]),
                         "axis": _enum(("x", "y", "z", ANY))},
                        ["part: the repeated part", "pattern: corners, ends, row, triangle or spread",
                         "other: the part they are arranged on (parent = the part they are fixed to)",
                         "axis: for ends/row, the direction: x = left to right, y = front to back, z = up; "
                         "any = not stated"],
                        {"part": n1, "pattern": "corners", "other": n0, "axis": ANY}),
        "touches": ({"part": _enum(names), "other": _enum(names)},
                    ["part: one part", "other: the part it must be joined to"], {"part": n1, "other": n0}),
        "connected": ({"parts": {"type": "array", "items": _enum(names)}},
                      ["parts: the parts that must be joined into one body ([] = all parts)"], {"parts": []}),
        "stable": ({"load_mass_g": {"type": "number"}, "load_part": _enum(names + [NONE]),
                    "tilt_deg": {"type": "number"}},
                   ["load_mass_g: a load in grams resting on a part (0 = no load)",
                    "load_part: the part the load rests on (none = no load)",
                    "tilt_deg: how far the table may tilt without the object tipping; 0 = the default (5)"],
                   {"load_mass_g": 0, "load_part": NONE, "tilt_deg": 0}),
        "fits": ({"object": _enum(list(cc.STANDINS)), "size": {"type": "array", "items": {"type": "number"}},
                  "into": {"type": "array", "items": _enum(names)}, "between": {"type": "boolean"},
                  "orientation": _enum(("upright", "edge", "flat")), "min_depth": {"type": "number"}},
                 ["object: the stand-in (box = any box-shaped thing, cylinder = any round thing)",
                  "size: [] for a phone/tablet/laptop/book/pencil of normal size; otherwise box = "
                  "[three sizes in mm], cylinder = [diameter, length] in mm",
                  "into: the part it goes into, or the TWO parts it goes between",
                  "between: true if it goes between the two parts in `into`",
                  "orientation: upright = longest side vertical, edge = standing on its edge, flat = lying flat",
                  "min_depth: how deep it must go in mm (0 = the default, half the height)"],
                 {"object": "pencil", "size": [], "into": [n1], "between": False, "orientation": "upright",
                  "min_depth": 0}),
        "rests_on": ({"object": _enum(list(cc.STANDINS)), "size": {"type": "array", "items": {"type": "number"}},
                      "support": _enum(names), "mode": _enum(("lean", "lie")),
                      "also_touches": {"type": "array", "items": _enum(names)},
                      "orientation": _enum(("portrait", "landscape", ANY)), "mu": {"type": "number"}},
                     ["object: the stand-in (box = any box-shaped thing, cylinder = any round thing)",
                      "size: [] for a phone/tablet/laptop/book/pencil of normal size; otherwise box = "
                      "[three sizes in mm], cylinder = [diameter, length] in mm",
                      "support: the part it leans against (lean) or lies on (lie)",
                      "mode: lean = leaning against a sloped or upright part, lie = lying on a flat part",
                      "also_touches: other parts it must also touch, such as a lip ([] = none)",
                      "orientation: portrait, landscape or any",
                      "mu: friction coefficient; 0 = the default (0.3)"],
                     {"object": "phone", "size": [], "support": n1, "mode": "lean", "also_touches": [],
                      "orientation": ANY, "mu": 0}),
    }
    return T[check_type]


def params_from_template(check_type: str, raw: dict) -> dict:
    """Map a filled template to cad_checks parameters (sentinels -> defaults)."""
    p = {k: v for k, v in raw.items() if k != "reasoning"}

    def none_if(key, *sentinels):
        if p.get(key) in sentinels:
            p[key] = None

    if check_type == "count":
        none_if("part", WHOLE, "")
        none_if("shape", ANY, "")
    elif check_type == "dimension":
        none_if("part", WHOLE, "")
        if not p.get("tol"):
            p["tol"] = None
    elif check_type in ("shape",):
        none_if("orient", ANY, "")
    elif check_type == "arrangement":
        none_if("other", "parent", "")
        none_if("axis", ANY, "")
    elif check_type in ("connected", "no_overlap"):
        p["parts"] = list(p.get("parts") or []) or None
    elif check_type == "stable":
        mass, part = p.pop("load_mass_g", 0) or 0, p.pop("load_part", NONE)
        p["load"] = {"mass_g": float(mass), "part": part, "face": "top"} if mass and part not in (NONE, None) else None
        p["tilt_deg"] = p.get("tilt_deg") or cc.STABLE_TILT
    elif check_type in ("fits", "rests_on"):
        p["size"] = list(p.get("size") or []) or None
        if check_type == "fits":
            if not p.get("min_depth"):
                p["min_depth"] = None
        else:
            none_if("orientation", ANY, "")
            p["also_touches"] = list(p.get("also_touches") or []) or None
            if not p.get("mu"):
                p["mu"] = cc.DEFAULT_MU
    for k in ("value", "count"):
        if isinstance(p.get(k), float) and k == "count" and p[k] == int(p[k]):
            p[k] = int(p[k])
    return p


def parts_text(d) -> str:
    lines = [f"  - {c.name}{f' (x{c.count})' if c.count > 1 else ''}: {c.description}" for c in d.components]
    lines += [f"  - {n}: " + " and ".join(c.name for c in d.components if c.name.endswith("_" + n)) + " together"
              for n in group_names(d)]
    return "\n".join(lines) or "  (none yet)"


def make_check(cs: CascadeState, l1_id: str, check_type: str, params: dict, tag: str = "c",
               level: int = 1) -> cc.Check:
    chk = cc.Check(id=cs.next_id(l1_id, tag), l1_id=l1_id, type=check_type, params=dict(params), level=level)
    if not chk.text and not cc.validate_check(chk):
        chk.text = cc.render_check(chk)
    return chk


def group_names(d) -> List[str]:
    """Shared nouns of role-split parts ("panel" for front_panel and back_panel), so a test
    can name them together (a count over both, "each panel shall be 4 mm thick")."""
    nouns = Counter(c.name.split("_")[-1] for c in d.components if "_" in c.name)
    taken = {c.name for c in d.components}
    return [n for n, k in nouns.items() if k >= 2 and n not in taken]


def ask_checks(llm, d, req: dict, types: Sequence[str], errors: Sequence[str], attempt: int,
               header: Sequence[str] = (), tag: str = "c", level: int = 1) -> List[cc.Check]:
    """One LLM proposal of checks for one L1: pick check types, then fill each type's template."""
    cs: CascadeState = d.cascade
    names = [c.name for c in d.components] + group_names(d)
    base = [f"Object: {d.base_request or d.request}", ca.CONVENTIONS, "", "Parts of the design:", parts_text(d), "",
            f'Requirement {req["id"]}: "{req["text"]}"']
    if req.get("method"):
        base.append(f"Verification method: {req['method']}")
    base += list(header)
    if errors:
        base += ["", "Your previous tests were rejected:"] + [f"- {e}" for e in errors]
    temperature = 0.0 if attempt == 0 else 0.5
    lines = base + ["", "Which kinds of automatic test check this requirement? Pick 1 to 3:"]
    lines += [f"- {t}: {TYPE_DOCS[t]}" for t in types]
    schema = ca.obj_schema({"tests": {"type": "array", "minItems": 1, "maxItems": 3, "items": _enum(types)}})
    try:
        chosen = llm.ask_json("\n".join(lines), schema, temperature=temperature, seed=attempt,
                              label=f"l1types_{slug(req['id'])}", num_predict=TYPES_TOKENS).get("tests") or []
    except ValueError:
        chosen = []
    chosen = [t for t in dict.fromkeys(chosen) if t in types][:3] or [types[0]]
    out: List[cc.Check] = []
    for t in chosen:
        if t == "no_overlap":   # no slots to fill
            out.append(make_check(cs, req["id"], t, {}, tag, level))
            continue
        if not names:
            continue
        item, slots, example = template(t, names)
        fill = base + ["", f'Fill in one or more "{t}" tests that together check this requirement.',
                       f"A {t} test checks: {TYPE_DOCS[t]}.", "Slots:"] + [f"- {s}" for s in slots]
        fill += ["Use every number the requirement gives that this kind of test can check, exactly as given.",
                 "Example: " + json.dumps({"tests": [example]})]
        schema = ca.obj_schema({"tests": {"type": "array", "minItems": 1, "maxItems": 4,
                                          "items": ca.obj_schema(item)}})
        try:
            raw = llm.ask_json("\n".join(fill), schema, temperature=temperature, seed=attempt,
                               label=f"l1fill_{slug(req['id'])}_{t}", num_predict=FILL_TOKENS).get("tests") or []
        except ValueError:
            raw = []
        for r in raw[:4]:
            if isinstance(r, dict):
                out.append(make_check(cs, req["id"], t, params_from_template(t, r), tag, level))
    return out


def check_signature(chk: cc.Check) -> str:
    return json.dumps([chk.type, chk.params], sort_keys=True, default=str)


def design_mutants(d, cache: dict) -> List[cc.Mutant]:
    """The provisional design's mutants, computed once per geometry."""
    if not d.components:
        return []
    sig = cc.geometry_signature(d)
    if cache.get("sig") != sig:
        cache["sig"], cache["mutants"] = sig, cc.mutants(d)
    return cache["mutants"]


SIDE_RELATIONS = ("in_front_of", "behind", "left_of", "right_of")
# A count over the whole object only makes sense when the L1 talks about the object's parts as a whole.
WHOLE_COUNT_WORDS = r"\b(parts?|pieces?|components?|single|one[- ]piece|only)\b"


# Words in an L1 that a check of a particular kind must cover (the meaning counterpart of
# number coverage): (cue, pattern, check types that can cover it, predicate, what to add).
CUES: List[Tuple[str, str, Tuple[str, ...], Callable[[cc.Check], bool], str]] = [
    ("edge", r"\b(front|back|rear|left|right) edges?\b|\balong (its|the) (front|back|left|right)\b", ("edge", "span"),
     lambda c: c.type in ("edge", "span"), "an edge test"),
    ("corner", r"\bcorners?\b", ("arrangement",),
     lambda c: c.type == "arrangement" and c.params.get("pattern") == "corners", "an arrangement test (corners)"),
    ("centred", r"\bcent(re|er)(d|ed)?\b", ("edge",),
     lambda c: c.type == "edge" and c.params.get("where") == "center", "an edge test with where = center"),
    ("each end", r"(?<!open )(?<!open at )\b(each|both|either) ends?\b|\bat (the|its) ends\b", ("arrangement", "edge"),
     lambda c: (c.type == "arrangement" and c.params.get("pattern") in ("ends", "row")) or c.type == "edge",
     "an arrangement test (ends)"),
    ("row", r"\brow\b", ("arrangement",),
     lambda c: c.type == "arrangement" and c.params.get("pattern") == "row", "an arrangement test (row)"),
    ("on top", r"\bon top\b", ("relation", "rests_on"),
     lambda c: (c.type == "relation" and c.params.get("relation") == "on_top_of") or c.type == "rests_on",
     "a relation test (on_top_of)"),
    ("tipping", r"\btip(s|ping|ped)?\b|\btopple|\bstable\b", ("stable", "rests_on"),
     lambda c: c.type in ("stable", "rests_on"), "a stable test"),
    ("connected", r"\bconnected\b|\bone (solid |connected )?body\b", ("connected",),
     lambda c: c.type == "connected", "a connected test"),
    ("fit", r"\bfits?\b|\bslides? over\b", ("fits",), lambda c: c.type == "fits", "a fits test"),
    ("upright", r"\bupright\b|\bvertical(ly)?\b|\bstanding up\b", ("shape",),
     lambda c: (c.type == "shape" and c.params.get("orient") in ("upright", "z"))
     or (c.type in ("fits", "rests_on") and c.params.get("orientation") in ("upright", "edge", "portrait"))
     or (c.type == "dimension" and c.params.get("measure") == "angle"),
     "a shape test with orient upright (standing up) or z (axis vertical); shape any if only the orientation matters"),
]


def cue_coverage(req: dict, checks: Sequence[cc.Check]) -> List[Tuple[str, str]]:
    """(cue, suggestion) for each cue of the L1 that no passing check covers.

    Numbers alone let a translation drop the words: "one along the front edge and
    one along the back edge" was once covered only by "sits on top of the base".
    Cues whose check types the L1's verification method does not offer are skipped.
    """
    text, offered = req["text"].lower(), set(offered_types(req.get("method")))
    return [(cue, hint) for cue, pat, types, ok, hint in CUES
            if re.search(pat, text) and offered & set(types) and not any(ok(c) for c in checks)]


EDGE_AXES = {"front": ("y", "front"), "back": ("y", "back"), "left": ("x", "left"), "right": ("x", "right")}


def contradictions(checks: Sequence[cc.Check]) -> List[Tuple[cc.Check, cc.Check]]:
    """Pairs (earlier, later) of edge checks that put the same part at two places on one axis.

    An edge check applies to every copy of a part, so "the front panel is along the
    front edge" and "the front panel is centred front to back" cannot both pass;
    freezing both would hand the design loop an impossible target, which it then
    "solves" by trading one violation for another.
    """
    def places(c: cc.Check) -> Dict[str, str]:
        where = c.params.get("where")
        if where in EDGE_AXES:
            axis, pos = EDGE_AXES[where]
            return {axis: pos}
        axis = c.params.get("axis")
        return {a: "center" for a in (("x", "y") if axis in (None, "xy") else (axis,))}

    out, edges = [], [c for c in checks if c.type == "edge"]
    for i, a in enumerate(edges):
        for b in edges[i + 1:]:
            if (a.params.get("part"), a.params.get("other")) != (b.params.get("part"), b.params.get("other")):
                continue
            pa, pb = places(a), places(b)
            if any(pa[k] != pb[k] for k in set(pa) & set(pb)):
                out.append((a, b))
    return out


def foreign_number(req_text: str, chk: cc.Check) -> Optional[float]:
    """A dimension value or count the requirement never states (None if it is stated).

    Number coverage only proves the L1's numbers are used; this is the converse,
    for the slots that ARE the requirement's numbers. Without it a draft "angle =
    60" for "lean back at 70 degrees" survives next to the corrected "angle = 70",
    and the design loop is then asked to satisfy both.
    """
    slot = {"dimension": "value", "count": "count"}.get(chk.type)
    v = chk.params.get(slot) if slot else None
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return None
    stated = [n for n, _, _ in cc.l1_numbers(req_text)]
    if re.search(r"\b(upright|vertical(ly)?|standing up)\b", req_text.lower()):
        stated.append(90.0)   # "vertical" states 90 degrees
    if re.search(r"\b(single|one|only)\b", req_text.lower()):
        stated.append(1.0)    # "a single flat strip" states a count of 1
    return None if any(abs(n - v) <= max(0.5, 0.01 * abs(n)) for n in stated) else float(v)


def role_count_problem(d, chk: cc.Check) -> Optional[str]:
    """A count of more than one for a part that is one role among several of its kind.

    "Exactly two upright panels" became "exactly 2 front panels" and "exactly 2 back
    panels" once the panels were split into front_panel and back_panel; the design
    loop then doubled both.
    """
    if chk.type != "count" or not chk.params.get("part") or (chk.params.get("count") or 0) <= 1:
        return None
    chosen = cc.select(d, chk.params["part"], laid_out=False)
    if len(chosen) != 1:
        return None
    noun = chosen[0].name.split("_")[-1]
    roles = [c.name for c in d.components if c.name.split("_")[-1] == noun]
    if len(roles) < 2:
        return None
    return (f'the test "{chk.text}" counts only {chosen[0].name}, which is one of the separate parts '
            f'{", ".join(roles)}; to count them together use part "{noun}"')


def standin_problem(req_text: str, chk: cc.Check) -> Optional[str]:
    """A fits / rests_on stand-in whose size does not come from the requirement.

    "A letter 5 mm thick shall fit" once became a 160 x 240 x 30 mm book: the
    default book, which the requirement never mentions. A stand-in may use its
    default size only when the requirement names that object; otherwise, and
    whenever the requirement gives sizes, the stand-in must use one of them.
    """
    if chk.type not in ("fits", "rests_on"):
        return None
    obj, size = chk.params.get("object"), chk.params.get("size")
    text = req_text.lower()
    stated = [n for n, unit, _ in cc.l1_numbers(req_text) if unit != "deg"]
    named = bool(obj) and re.search(rf"\b{re.escape(str(obj))}s?\b", text)
    if not size:
        if named or obj in ("box", "cylinder"):
            return None
        return (f'the test "{chk.text}" uses a {obj} of the default size, but the requirement does not mention '
                f"a {obj}: give the size of the object the requirement describes")
    if stated and not any(abs(float(v) - n) <= max(0.5, 0.01 * n) for v in size for n in stated):
        return (f'the test "{chk.text}" gives the object sizes the requirement does not state; '
                "use the requirement's sizes for it")
    return None


def gate_checks(llm, d, req: dict, checks: Sequence[cc.Check], mutant_cache: dict,
                provenance: bool = True) -> Tuple[Dict[str, List[str]], List[tuple]]:
    """The gates a check must pass before it may be frozen.

    Returns ({check id: problems}, uncovered numbers of the L1 among the passing checks).
    Order: validation and number provenance (Python), non-vacuity on mutants of the
    provisional design (Python), back-translation (LLM, cached) - cheapest first,
    so the LLM is only asked about checks Python already accepts. Refined
    sub-checks (provenance=False) may use numbers the L1 does not state.
    """
    cs: CascadeState = d.cascade
    problems: Dict[str, List[str]] = {c.id: [] for c in checks}
    for c in checks:
        for e in cc.validate_check(c):
            problems[c.id].append(f'test {c.type} {json.dumps(c.params, default=str)}: {e}')
        if c.type == "relation" and c.params.get("relation") in SIDE_RELATIONS and re.search(r"\bedges?\b", req["text"].lower()):
            problems[c.id].append(f'the test "{c.text}" puts it outside, next to the other part, but the requirement '
                                  "says along an edge: use an edge test (and on_top_of if it stands on it)")
        if c.type == "count" and not c.params.get("part") and not re.search(WHOLE_COUNT_WORDS, req["text"].lower()):
            problems[c.id].append(f'the test "{c.text}" counts every part of the object, but the requirement '
                                  "is about particular parts; count those parts")
        role = role_count_problem(d, c)
        if role:
            problems[c.id].append(role)
        bad = foreign_number(req["text"], c) if provenance and not problems[c.id] else None
        if bad is not None:
            problems[c.id].append(f'the test "{c.text}" uses {fmt(bad)}, a number the requirement does not give')
        standin = standin_problem(req["text"], c) if provenance and not problems[c.id] else None
        if standin:
            problems[c.id].append(standin)
    for a, b in contradictions([c for c in checks if not problems[c.id]]):
        problems[b.id].append(f'the test "{b.text}" contradicts the test "{a.text}": both cannot hold for every copy')
    valid = [c for c in checks if not problems[c.id]]
    if valid and d.components:
        for rep in cc.non_vacuity(d, valid, design_mutants(d, mutant_cache)):
            cs.gates.setdefault(rep.check_id, {})["non_vacuity"] = {"ok": rep.ok, "reason": rep.reason,
                                                                   "killed": rep.killed[:8]}
            if not rep.ok:
                chk = next(c for c in valid if c.id == rep.check_id)
                problems[rep.check_id].append(f'the test "{chk.text}" would not catch a wrong design ({rep.reason})')
    accepted = [o for l1_id, drafts in cs.drafts.items() if l1_id != req["id"] for o in drafts]
    accepted += [o for o in cs.checks if o.l1_id != req["id"]]
    if d.components and accepted:
        for c in checks:
            if problems[c.id]:
                continue
            rep = cc.satisfiability(d, c, accepted, design_mutants(d, mutant_cache))
            cs.gates.setdefault(c.id, {})["satisfiable"] = {"ok": rep.ok, "reason": rep.reason,
                                                           "witness": rep.witness, "conflicts": rep.conflicts}
            if not rep.ok:
                clash = [o for o in accepted if o.id in rep.conflicts][:2]
                problems[c.id].append(f'the test "{c.text}" cannot pass without breaking '
                                      + " and ".join(f'"{o.text}"' for o in clash)
                                      + "; it probably reads the requirement wrongly (e.g. an object that rests "
                                        "on top rather than drops in)")
    todo = {stable_hash([req["text"], c.text]): c for c in checks if not problems[c.id]}
    todo = {k: c for k, c in todo.items() if k not in cs.bt_cache}
    if todo:   # one batch, so a judge panel loads each model once
        ask = getattr(llm, "p_yes_many", None)
        prompts = [cc.backtranslation_prompt(c, req["text"]) for c in todo.values()]
        label = f"bt_{slug(req['id'])}"
        scores = ask(prompts, label) if ask else [llm.p_yes(q, label=label) for q in prompts]
        cs.bt_cache.update(zip(todo, scores))
    for c in checks:
        if problems[c.id]:
            continue
        key = stable_hash([req["text"], c.text])
        p = cs.bt_cache[key]
        cs.gates.setdefault(c.id, {})["backtranslation"] = round(p, 3)
        if p < BT_THRESHOLD:
            problems[c.id].append(f'the test "{c.text}" does not check this requirement (reviewer said no)')
    passing = [c for c in checks if not problems[c.id]]
    return problems, cc.number_coverage(req["text"], passing)


class TranslationTask:
    """The callables of one L1's translation ControlLoop.

    State: a list of candidate checks. Measure: the gates. Error: (numbers of the
    L1 no passing check uses + 1 if no check passes, 0, number of checks failing a
    gate). A new proposal is merged with the passing checks of the best state, so
    acceptance only has to beat the best on what is still missing.
    """

    def __init__(self, design, llm, req: dict):
        self.design, self.llm, self.req = design, llm, req
        self.mutant_cache: dict = {}
        self.attempt = 0

    @property
    def cs(self) -> CascadeState:
        return self.design.cascade

    def reference(self):
        return [self.req["text"], self.req.get("method")]

    def initial(self):
        return []

    def measure(self, checks: List[cc.Check]) -> Measurement:
        problems, uncovered = gate_checks(self.llm, self.design, self.req, checks, self.mutant_cache)
        bad = [c for c in checks if problems[c.id]]
        passing = [c for c in checks if not problems[c.id]]
        cues = cue_coverage(self.req, passing)
        failing = [c.id for c in bad] + [f"number {fmt(v)}" for v, _, _ in uncovered] + [f"cue {q}" for q, _ in cues]
        residual = [p for c in bad for p in problems[c.id]]
        residual += [f'the number "{number_phrase(v, u)}" in the requirement is not used by any test'
                     for v, u, _ in uncovered]
        residual += [f'the requirement says "{q}" but no test checks it: add {hint}' for q, hint in cues]
        if not passing:
            failing.append("no_check")
            residual.append("no test was accepted yet")
        err = cc.ErrorKey(len(uncovered) + len(cues) + (0 if passing else 1), 0.0, float(len(bad)))
        # Every rejected check is recorded, also from proposals the loop did not accept.
        log = self.cs.translation.setdefault(self.req["id"], {"uncovered": [], "rejected": []})
        known = {r["check"]["id"] for r in log.setdefault("rejected", [])}
        log["rejected"] += [{"check": c.to_dict(), "problems": problems[c.id]} for c in bad if c.id not in known]
        return Measurement(err, failing, residual, data={"problems": problems, "uncovered": uncovered,
                                                         "cues": cues})

    def propose(self, best: List[cc.Check], ctx: LoopContext) -> Optional[List[cc.Check]]:
        if self.attempt >= TRANSLATE_ITERATIONS:
            return None
        # prior errors: what is still missing from the best set, and why the last proposal failed
        last = ctx.history[-1]["residual"] if ctx.history and ctx.history[-1]["note"] != "initial" else []
        errors = list(dict.fromkeys(list(ctx.best.residual) + list(last)))[:8] if (ctx.iteration or best) else []
        new = ask_checks(self.llm, self.design, self.req, offered_types(self.req.get("method")), errors, self.attempt)
        self.attempt += 1
        keep = [c for c in best if not ctx.best.data["problems"].get(c.id)]
        seen = {check_signature(c) for c in keep}
        merged = keep + [c for c in new if check_signature(c) not in seen and not seen.add(check_signature(c))]
        return merged

    def commit(self, checks: List[cc.Check], m: Measurement) -> None:
        problems, uncovered = m.data["problems"], m.data["uncovered"]
        self.cs.drafts[self.req["id"]] = [c for c in checks if not problems[c.id]]
        log = self.cs.translation.setdefault(self.req["id"], {"rejected": []})
        log["uncovered"] = [{"value": v, "unit": u, "text": number_phrase(v, u)} for v, u, _ in uncovered]
        log["uncovered_cues"] = [{"cue": q, "hint": h} for q, h in m.data.get("cues", [])]

    @staticmethod
    def key(checks: List[cc.Check]) -> str:
        return stable_hash(sorted(check_signature(c) for c in checks))


def fmt(v: float) -> str:
    return ca.fmt(v)


def number_phrase(value: float, unit: str) -> str:
    """How a number of the L1 is quoted back in a gate message ("120 mm", "70 degrees", "4")."""
    return f"{fmt(value)} degrees" if unit == "deg" else f"{fmt(value)} mm" if unit else fmt(value)


def translate_loop(design, llm, req: dict) -> ControlLoop:
    task = TranslationTask(design, llm, req)
    return ControlLoop(f"translate:{req['id']}", f"translate_{req['id']}", reference=task.reference,
                       initial=task.initial, propose=task.propose, measure=task.measure, commit=task.commit,
                       state_key=task.key, max_iterations=TRANSLATE_ITERATIONS, patience=TRANSLATE_ITERATIONS,
                       reports=design.cascade.reports)


def assign_levels(checks: List[cc.Check]) -> None:
    """Every check that passed the translation gates verifies its L1: level 1.

    Level 2 is reserved for the design-guidance sub-checks RefineChecks adds later
    (tag "r"). An earlier version demoted the non-behavioural checks of an L1 that
    also had a fits / rests_on / stable check to level 2; those checks carry the
    L1's own stated numbers ("the base shall be 200 mm wide so that it does not tip
    over"), so a failing 200 mm check was ignored by the matrix and even dropped by
    the outer loop, and the L1 was reported as verified with an 80 mm base.
    """
    for c in checks:
        c.level = 1


def system_checks() -> List[cc.Check]:
    """Python's own integrity checks, whatever the L1s say: one body, no interpenetration.

    Both hard: in the first smoke run a soft no_overlap let the loop stack two
    copies of a panel exactly on top of each other (100% overlap) to win a
    relation margin.
    """
    conn = cc.Check(id="SYS.connected", l1_id=SYSTEM_L1, type="connected", params={})
    overlap = cc.Check(id="SYS.no_overlap", l1_id=SYSTEM_L1, type="no_overlap", params={})
    return [conn, overlap]


class FreezeChecks(ca.Step):
    """Freeze the accepted checks (plus system checks) before the design phase; write checks.json."""

    def __init__(self, design):
        super().__init__("freeze_checks", design)

    def update(self):
        d = self.design
        cs: CascadeState = d.cascade
        if cs.frozen:
            return Status.SUCCESS
        checks = [c for req in cs.l1 for c in cs.drafts.get(req["id"], [])]
        assign_levels(checks)
        cs.checks = checks + system_checks()
        cs.frozen, cs.version = True, 1
        path = write_checks(d)
        empty = [r["id"] for r in cs.l1 if not cs.drafts.get(r["id"])]
        self.logger.info(f"froze {len(checks)} checks for {len(cs.l1)} L1s -> {path}"
                         + (f"; no accepted check for {', '.join(empty)}" if empty else ""))
        return Status.SUCCESS


# ---------------------------------------------------------------------------
# Inner loop: the design against the frozen checks
# ---------------------------------------------------------------------------

FIELDS = ("shape", "params", "place", "count", "arrangement")


def snapshot(d) -> List[dict]:
    return [dict({"name": c.name}, **{f: copy.deepcopy(getattr(c, f)) for f in FIELDS}) for c in d.components]


def design_from(d, snap: Sequence[dict]):
    """A laid-out copy of the design with the snapshot's decisions."""
    m = cc.clone_design(d)
    by_name = {s["name"]: s for s in snap}
    for c in m.components:
        s = by_name.get(c.name)
        if s:
            for f in FIELDS:
                setattr(c, f, copy.deepcopy(s[f]))
    ca.layout(m)
    return m


def apply_snapshot(d, snap: Sequence[dict]) -> None:
    by_name = {s["name"]: s for s in snap}
    for c in d.components:
        s = by_name.get(c.name)
        if s:
            for f in FIELDS:
                setattr(c, f, copy.deepcopy(s[f]))
    ca.layout(d)


def snap_key(snap: Sequence[dict]) -> str:
    return stable_hash(list(snap))


def default_arrangement(c, count: int) -> Optional[str]:
    if count <= 1 or not c.place:
        return None
    axes = "".join(ca.face_axes(c.place["side"]))
    if count == 4:
        return f"corners_{axes}"
    if count == 3 and c.place["side"] in ("top", "bottom"):
        return f"triangle_{axes}"
    return ("ends_" if count == 2 else "row_") + axes[0]


def arrangement_fits(arr: Optional[str], count: int) -> bool:
    if count <= 1:
        return arr is None
    if not arr:
        return False
    kind = arr.split("_")[0]
    return {"corners": count == 4, "triangle": count == 3, "ends": count == 2}.get(kind, True)


class DesignTask:
    """The callables of the inner ControlLoop (state = a snapshot of every component's decisions)."""

    def __init__(self, design, llm):
        self.design, self.llm = design, llm
        self.cache: Dict[str, Measurement] = {}
        self.sens: Dict[str, cc.SensitivityReport] = {}
        self.llm_tries: Dict[str, int] = {}
        self.last_note: Optional[str] = None
        self.logger = None   # the loop's logger, set by design_loop()

    @property
    def checks(self) -> List[cc.Check]:
        return self.design.cascade.checks

    def reference(self):
        return [c.to_dict() for c in self.checks]

    def initial(self):
        self.cache.clear()   # a new reference: old measurements are against other checks
        self.sens.clear()
        self.llm_tries.clear()
        ca.layout(self.design)
        return snapshot(self.design)

    def measure(self, snap) -> Measurement:
        key = snap_key(snap)
        if key not in self.cache:
            m = design_from(self.design, snap)
            results = cc.run_checks(m, self.checks)
            failing = [r.check_id for r in results if r.hard and not r.passed]
            order = sorted([r for r in results if not r.passed], key=lambda r: (not r.hard, r.margin))
            residual = [f"{r.check_id} [{r.type}]: {r.evidence.get('detail')}" for r in order]
            self.cache[key] = Measurement(cc.error_key(results), failing, residual, data=results)
        m = self.cache[key]
        return Measurement(m.error, list(m.failing), list(m.residual), [], m.data)

    def commit(self, snap, m: Measurement) -> None:
        apply_snapshot(self.design, snap)
        self.design.cascade.last_results = m.data

    # ----- diagnosis: localisation and controllability -----

    def failing_pairs(self, m: Measurement, include_soft: bool = False) -> List[Tuple[cc.Check, cc.CheckResult]]:
        by_id = {r.check_id: r for r in m.data}
        return [(c, by_id[c.id]) for c in self.checks
                if c.id in by_id and not by_id[c.id].passed and (c.hard or include_soft)]

    def sensitivity(self, snap, m: Measurement) -> cc.SensitivityReport:
        key = snap_key(snap)
        if key not in self.sens:
            failing = [c for c, _ in self.failing_pairs(m, include_soft=True)]
            self.sens[key] = cc.sensitivity(design_from(self.design, snap), failing)
        return self.sens[key]

    def diagnose(self, snap, m: Measurement) -> List[str]:
        """Failing checks that no knob moves AND no direct (deadbeat / count / shape) fix reaches."""
        rep = self.sensitivity(snap, m)
        d = design_from(self.design, snap)
        out = []
        for chk, r in self.failing_pairs(m):
            if chk.id in rep.uncontrollable and not self.direct_fixes(d, [(chk, r)]) \
                    and not (chk.type == "shape" and chk.params.get("shape") != "any"
                             and cc.select(d, chk.params.get("part"))):
                out.append(chk.id)
        return out

    # ----- corrections -----

    def direct_fixes(self, d, failing) -> List[List[dict]]:
        """Python-only corrections: deadbeat parameter values, counts, a round part's axis.

        Returns candidate snapshots: all fixes together first, then each alone.
        """
        edits: List[Tuple[str, str, Any]] = []   # (component, field or "params.<name>" / "arrangement", value)
        options: List[Tuple[str, str, Any]] = []  # alternatives tried one at a time (arrangements for a new count)
        for chk, r in failing:
            if chk.type in ("dimension", "span"):
                for f in cc.deadbeat(d, chk, r):
                    edits.append((f.component, f"params.{f.param}", f.new))
            elif chk.type == "count" and chk.params.get("part"):
                comps = [c for c in cc.select(d, chk.params["part"], laid_out=False) if c is not d.components[0]]
                if len(comps) == 1:
                    want, op, n = int(chk.params["count"]), chk.params.get("op") or "eq", comps[0].count
                    new = want if op == "eq" else max(n, want) if op == "ge" else min(n, want)
                    if new != n and 1 <= new <= 8:
                        edits.append((comps[0].name, "count", new))
                        c0 = comps[0]
                        if c0.place and new > 1:   # which layout of the copies is for the search to decide
                            axes = "".join(ca.face_axes(c0.place["side"]))
                            for arr in [f"corners_{axes}", f"triangle_{axes}"] + \
                                    [f"{k}_{a}" for k in ("ends", "row") for a in axes]:
                                if arrangement_fits(arr, new):
                                    options.append((c0.name, "arrangement", arr))
            elif chk.type == "shape" and chk.params.get("orient") in ("x", "y", "z"):
                for c in cc.select(d, chk.params["part"]):
                    if c.shape in ("cylinder", "tube") and c.params.get("axis") != chk.params["orient"]:
                        edits.append((c.name, "params.axis", chk.params["orient"]))
        if not edits:
            return []

        def build(group) -> Optional[List[dict]]:
            snap = snapshot(d)
            by = {s["name"]: s for s in snap}
            for name, fld, value in group:
                s = by[name]
                if fld.startswith("params."):
                    s["params"] = dict(s["params"], **{fld[7:]: value})
                    if ca.validate_params(ca.SHAPES[s["shape"]], s["params"])[0] is None:
                        return None
                elif fld == "count":
                    s["count"] = value
                    comp = d.component(name)
                    if not arrangement_fits(s["arrangement"], value):
                        s["arrangement"] = default_arrangement(comp, value)
                elif fld == "arrangement":
                    s["arrangement"] = value
            return snap

        out = []
        groups = ([edits] if len(edits) > 1 else []) + [[e] for e in edits]
        groups += [g + [o] for o in options for g in groups[:1]]
        for group in groups:
            snap = build(group)
            if snap is not None:
                out.append(snap)
        return out

    def localise(self, snap, m: Measurement, failing) -> List[str]:
        """Components to repair, most promising first: the sensitivity ranking, then what the checks depend on."""
        rep = self.sensitivity(snap, m)
        names: List[str] = []
        for chk, r in failing:
            for n in rep.localisation.get(chk.id, [])[:2] + r.depends_on.get("components", []):
                if n not in names:
                    names.append(n)
        return names

    def neighbours(self, d, names: Sequence[str], rep: cc.SensitivityReport) -> Dict[str, List[dict]]:
        """Single structural/size moves of the localised components (no OpenSCAD, no LLM)."""
        out: Dict[str, List[dict]] = {}
        base = snapshot(d)

        def with_comp(v) -> List[dict]:
            snap = copy.deepcopy(base)
            for s in snap:
                if s["name"] == v.name:
                    for f in FIELDS:
                        s[f] = copy.deepcopy(getattr(v, f))
            return snap

        for knob in cc.knobs(d):
            if knob.component in names:
                m = cc.apply_knob(d, knob)
                if m is not None:
                    out[knob.label] = snapshot(m)
        for name in names:
            c = d.component(name)
            if not (c and c.shape and c.params):
                continue
            spec = ca.SHAPES[c.shape].params
            for k, v in c.params.items():   # bigger steps than the sensitivity's +-10%
                if spec[k].kind != "mm":
                    continue
                for f in (0.5, 0.75, 1.5, 2.0):
                    trial = dict(c.params, **{k: round(v * f, 3)})
                    if ca.validate_params(ca.SHAPES[c.shape], trial)[0] is not None:
                        snap = copy.deepcopy(base)
                        next(s for s in snap if s["name"] == name)["params"] = trial
                        out[f"{name}.{k}x{f}"] = snap
            for label, v in ca.VerifyComponent(d, self.llm, c).size_moves().items():
                out[f"{name}:{label}"] = with_comp(v)
            if c.place:   # spans: as long as the parent along each in-face axis
                parent = d.component(c.place["parent"])
                for axis in ca.face_axes(c.place["side"]):
                    sp = ca.size_param(c, axis)
                    if sp and parent and parent.size:
                        trial = dict(c.params, **{sp: parent.size["xyz".index(axis)]})
                        if ca.validate_params(ca.SHAPES[c.shape], trial)[0] is not None:
                            v = ca.with_place(c, **dict(c.place, **{axis: "center"}))
                            v.params = trial
                            out[f"{name}:span_{axis}"] = with_comp(v)
                if c.place.get("side"):   # a new side with every alignment (two moves at once)
                    for side in ca.SIDES:
                        if side == c.place["side"]:
                            continue
                        a, b = ca.face_axes(side)
                        for va in ca.ALIGN[a]:
                            for vb in ca.ALIGN[b]:
                                v = ca.with_place(c, **dict(c.place, side=side, **{a: va, b: vb}))
                                out[f"{name}:{side}/{a}={va}/{b}={vb}"] = with_comp(v)
        return out

    @staticmethod
    def move_cost(label: str) -> int:
        """Smaller changes first among equally good candidates: sizes and alignments,
        then arrangements, then a new side, then a new parent."""
        if "+" in label:
            return 4 + DesignTask.move_cost(label.split("+", 1)[1])
        if "parent=" in label:
            return 3
        if ".side=" in label or re.search(r":(top|bottom|front|back|left|right)/", label):
            return 2
        if "arrangement=" in label:
            return 1
        return 0

    def rank(self, d, tied: Dict[str, List[dict]]) -> str:
        """LLM ranking of equally good candidates: back-translation P(yes) of the changed part."""
        labels = sorted(tied, key=self.move_cost)[:RANK_LIMIT]
        if len(labels) == 1 or self.llm is None:
            return labels[0]
        prompts, names = [], []
        for label in labels:
            vd = design_from(d, tied[label])
            changed = next((c for c, s in zip(vd.components, tied[label])
                            if any(s[f] != getattr(d.component(c.name), f) for f in FIELDS)), vd.components[0])
            prompts.append(ca.verify_prompt(vd, ca.describe(vd, changed)))
            names.append(f"rank_{changed.name}")
        ask = getattr(self.llm, "p_yes_many", None)
        scores = dict(zip(labels, ask(prompts, names) if ask else
                          [self.llm.p_yes(q, label=n) for q, n in zip(prompts, names)]))
        return max(labels, key=lambda k: (round(scores[k], 2), -labels.index(k)))

    def search(self, d, snap, m: Measurement, failing, tried: Set[str]) -> Optional[Tuple[str, List[dict]]]:
        """Best strictly improving single move; failing that, the best pair of improving knobs."""
        rep = self.sensitivity(snap, m)
        names = self.localise(snap, m, failing)
        cands = {k: s for k, s in self.neighbours(d, names, rep).items() if snap_key(s) not in tried}
        scored = {k: self.measure(s).error for k, s in cands.items()}
        better = {k: e for k, e in scored.items() if cc.strictly_better(e, m.error, eps=ACCEPT_EPS)}
        # Pairs, always (not only on a plateau): a knob that improves a failing check most,
        # combined with any other knob of the localised components. Greedy single moves
        # alone walked a sideways panel through ten small tilts towards a width check,
        # when "lean back + copies at the front/back ends" fixed it in one step.
        top: List[str] = []
        for chk, _ in failing:
            for k in rep.improvers.get(chk.id, [])[:4]:
                if k not in top:
                    top.append(k)
        all_knobs = cc.knobs(d)
        by_label = {k.label: k for k in all_knobs}
        partners = [k for k in all_knobs if k.component in names]
        for a in top[:6]:
            if a not in by_label:
                continue
            m1 = cc.apply_knob(d, by_label[a])
            if m1 is None:
                continue
            for kb in partners:
                if kb.label == a or (kb.component, kb.name) == (by_label[a].component, by_label[a].name):
                    continue
                m2 = cc.apply_knob(m1, kb)
                if m2 is None:
                    continue
                s2 = snapshot(m2)
                if snap_key(s2) in tried:
                    continue
                e = self.measure(s2).error
                if cc.strictly_better(e, m.error, eps=ACCEPT_EPS):
                    cands[f"{a}+{kb.label}"] = s2
                    better[f"{a}+{kb.label}"] = e
        if not better:
            return None
        best = min(better.values())
        tied = {k: cands[k] for k, e in better.items() if not cc.strictly_better(best, e) and not cc.strictly_better(e, best)}
        label = self.rank(d, tied)
        return label, cands[label]

    def llm_proposal(self, d, snap, m: Measurement, failing, ctx: LoopContext) -> Optional[Tuple[str, List[dict]]]:
        """Where Python has no improving move: a new shape for a failing shape check, or new
        parameters for a localised component, with the failing checks' evidence in the prompt."""
        for chk, r in failing:
            if chk.type != "shape" or chk.params["shape"] == "any":
                continue
            target = "cylinder" if chk.params["shape"] == "round" else chk.params["shape"]
            for c in cc.select(d, chk.params["part"]):
                tag = f"shape:{c.name}:{target}"
                if c.shape == target or self.llm_tries.get(tag):
                    continue
                self.llm_tries[tag] = 1
                v = copy.copy(c)
                v.shape, v.params = target, None
                notes = [f"It must be {cc.SHAPE_WORDS.get(target, target)}: {chk.text}"]
                params, _ = ca.propose_params(self.llm, d, v, notes, 0)
                if params:
                    if target in ("cylinder", "tube") and chk.params.get("orient") in ("x", "y", "z"):
                        params["axis"] = chk.params["orient"]
                    new = copy.deepcopy(snap)
                    s = next(s for s in new if s["name"] == c.name)
                    s["shape"], s["params"] = target, params
                    return tag, new
        for name in self.localise(snap, m, failing):
            c = d.component(name)
            if not (c and c.shape and c.params) or self.llm_tries.get(name, 0) >= 2:
                continue
            attempt = self.llm_tries.get(name, 0)
            self.llm_tries[name] = attempt + 1
            notes = [f"A requirement check fails: {chk.text} Measured: {r.evidence.get('detail')}"
                     for chk, r in failing if name in r.depends_on.get("components", [])]
            tried_params = [h for h in ctx.history if not h["accepted"] and h.get("note", "").startswith(f"params:{name}")]
            notes += [f"Already tried and still wrong: {h['note'][len('params:' + name) + 1:]}" for h in tried_params[-2:]]
            params, _ = ca.propose_params(self.llm, d, c, notes or [f"It does not meet: {failing[0][0].text}"], attempt)
            if params and params != c.params:
                new = copy.deepcopy(snap)
                next(s for s in new if s["name"] == name)["params"] = params
                return f"params:{name} {json.dumps(params)}", new
        return None

    def propose(self, snap, ctx: LoopContext) -> Optional[List[dict]]:
        m = ctx.best
        failing = [(c, r) for c, r in self.failing_pairs(m) if c.id not in m.uncontrollable]
        if not failing:
            return None
        d = design_from(self.design, snap)
        tried = set(ctx.rejected) | {snap_key(snap)}
        # Direct (deadbeat) fixes first, screened: the best one that strictly lowers the error.
        direct = [c for c in self.direct_fixes(d, failing) if snap_key(c) not in tried]
        better = [(self.measure(c).error, i, c) for i, c in enumerate(direct)
                  if cc.strictly_better(self.measure(c).error, m.error, eps=ACCEPT_EPS)]
        if better:
            self.note(ctx, "deadbeat")
            return min(better, key=lambda t: (t[0], t[1]))[2]
        found = self.search(d, snap, m, failing, tried)
        if found is None and self.llm is not None:
            found = self.llm_proposal(d, snap, m, failing, ctx)
        if found is None:
            return None
        self.note(ctx, found[0])
        return found[1]

    def note(self, ctx: LoopContext, what: str) -> None:
        self.last_note = what
        if self.logger is not None:
            self.logger.info(f"proposal {ctx.iteration + 1}: {what}")


def design_loop(design, llm) -> ControlLoop:
    task = DesignTask(design, llm)
    loop = ControlLoop("design_loop", "design", reference=task.reference, initial=task.initial,
                       propose=task.propose, measure=task.measure, commit=task.commit,
                       accept=lambda new, old: cc.strictly_better(new, old, eps=ACCEPT_EPS),
                       diagnose=task.diagnose, state_key=snap_key, max_iterations=DESIGN_ITERATIONS,
                       patience=DESIGN_PATIENCE, reports=design.cascade.reports)
    loop.task = task
    task.logger = loop.logger
    original_accept = loop._accept

    def accept_with_note():
        # label the history entry with what the proposal was (deadbeat, a knob, an LLM step)
        status = original_accept()
        if loop.history and task.last_note:
            loop.history[-1]["note"] = task.last_note
        task.last_note = None
        return status

    loop.children[2].fn = accept_with_note
    return loop


class RecordDesignReport(ca.Step):
    """Keep every inner-loop report (one per outer iteration) for the matrix."""

    def __init__(self, design, loop: ControlLoop):
        super().__init__("record_design_report", design)
        self.loop = loop

    def update(self):
        if self.loop.report is not None:
            rep = self.loop.report.to_dict()
            rep["checks_version"] = self.design.cascade.version
            self.design.cascade.design_reports.append(rep)
        return Status.SUCCESS


# ---------------------------------------------------------------------------
# Outer loop (CEGAR, light): refine or relax the level-2 sub-checks
# ---------------------------------------------------------------------------


def recheck_coverage(cs: CascadeState, req: dict) -> None:
    """After checks of an L1 were dropped, re-run number coverage against the level-1 checks left.

    translation["uncovered"] was computed when the dropped checks still existed;
    without this a number only a dropped check carried would silently count as
    checked. Uncovered numbers make the matrix row "unverified", never "pass".
    """
    left = [c for c in cs.checks if c.l1_id == req["id"] and c.level == 1]
    log = cs.translation.setdefault(req["id"], {"rejected": []})
    known = {(u["value"], u.get("unit")) for u in log.get("uncovered", [])}
    for v, u, _ in cc.number_coverage(req["text"], left):
        if (v, u) not in known:
            log.setdefault("uncovered", []).append({"value": v, "unit": u, "text": number_phrase(v, u)})


class RefineChecks(ca.Step):
    """After the inner loop: compare each L1's own checks with its level-2 sub-checks.

    - L1 check fails, every sub-check passes: the decomposition is too weak ->
      ask the LLM for more sub-checks (gated like any check), re-freeze, rerun.
    - L1 check passes, some sub-checks fail: they over-constrain -> drop them.
    FAILURE means "the checks changed, run the inner loop again"; at most MAX_OUTER times.
    """

    def __init__(self, design, llm):
        super().__init__("refine_checks", design)
        self.llm = llm
        self.mutant_cache: dict = {}

    def update(self):
        d = self.design
        cs: CascadeState = d.cascade
        if cs.outer_iterations >= MAX_OUTER:
            return Status.SUCCESS
        results = {r.check_id: r for r in cc.run_checks(d, cs.checks)}
        changed: List[str] = []
        for req in cs.l1:
            group = [c for c in cs.checks if c.l1_id == req["id"]]
            top = [c for c in group if c.level == 1 and c.type in BEHAVIOURAL]
            if not top:
                continue
            # Only the outer loop's own refinements (level 2) are scaffolding it may drop;
            # the translated checks are the L1's content and are never relaxed.
            subs = [c for c in group if c.level == 2]
            top_ok = all(results[c.id].passed for c in top)
            bad_subs = [c for c in subs if not results[c.id].passed]
            if top_ok and bad_subs:
                for c in bad_subs:
                    cs.checks.remove(c)
                    cs.dropped.append({"check": c.to_dict(), "reason": f"{req['id']} passes without it",
                                       "evidence": results[c.id].evidence.get("detail")})
                recheck_coverage(cs, req)
                changed.append(f"dropped {', '.join(c.id for c in bad_subs)} ({req['id']} passes without them)")
            elif not top_ok and not bad_subs:
                added = self.refine(req, top, results)
                if added:
                    idx = max((i for i, c in enumerate(cs.checks) if c.l1_id == req["id"]), default=len(cs.checks) - 1)
                    cs.checks[idx + 1:idx + 1] = added
                    changed.append(f"added {', '.join(c.id for c in added)} for {req['id']}")
        if not changed:
            return Status.SUCCESS
        cs.outer_iterations += 1
        cs.version += 1
        cs.refinements.append({"iteration": cs.outer_iterations, "version": cs.version, "changes": changed})
        write_checks(d)
        self.logger.info(f"outer loop {cs.outer_iterations}: {'; '.join(changed)}")
        self.feedback_message = "checks refined"
        return Status.FAILURE

    def refine(self, req: dict, top: List[cc.Check], results: Dict[str, cc.CheckResult]) -> List[cc.Check]:
        d = self.design
        evidence = [f'The test "{c.text}" FAILS: {results[c.id].evidence.get("detail")}' for c in top]
        header = ["", *evidence,
                  "Write extra design tests (sizes, positions, shapes of the parts) that a design must meet",
                  "for the failing test above to pass."]
        new = ask_checks(self.llm, d, req, INSPECTION_TYPES, [], d.cascade.outer_iterations, header=header,
                         tag="r", level=2)
        existing = {check_signature(c) for c in d.cascade.checks}
        new = [c for c in new if check_signature(c) not in existing]
        problems, _ = gate_checks(self.llm, d, req, new, self.mutant_cache, provenance=False)
        accepted = [c for c in new if not problems[c.id]]
        for c in accepted:
            c.level = 2
        d.cascade.translation.setdefault(req["id"], {}).setdefault("refinement_rejected", []).extend(
            {"check": c.to_dict(), "problems": problems[c.id]} for c in new if problems[c.id])
        return accepted


# ---------------------------------------------------------------------------
# Output: rebuild, verification matrix, review
# ---------------------------------------------------------------------------


class Rebuild(ca.Step):
    """OpenSCAD of the loop's best design (the checks, not the compile, judge it)."""

    def __init__(self, design):
        super().__init__("rebuild", design)

    def update(self):
        d = self.design
        ca.layout(d)
        d.workdir.mkdir(parents=True, exist_ok=True)
        d.assembly = d.workdir / "model.scad"
        d.assembly.write_text(ca.scad_source(d))
        ca.write_design_json(d)
        (d.workdir / "checks").mkdir(parents=True, exist_ok=True)
        result = ca.compile_scad(d.assembly, d.workdir / "model.stl")
        if not result.ok:
            raise RuntimeError(f"generated OpenSCAD failed to compile: {'; '.join(result.problems)}")
        d.mesh = result.tris
        return Status.SUCCESS


def l1_rows(cs: CascadeState, results: Sequence[cc.CheckResult]) -> Tuple[List[dict], List[dict]]:
    """Verification matrix rows: one per L1 (status pass / fail / unverified), failing first, and the system checks.

    An L1's status needs EVERY hard check that passed its translation gates (level 1)
    to pass; only the outer loop's refinement sub-checks (level 2) are advisory.
    """
    by_id = {r.check_id: r for r in results}
    rows = []
    for req in cs.l1:
        group = [c for c in cs.checks if c.l1_id == req["id"]]
        top = [c for c in group if c.level == 1] or group
        tr = cs.translation.get(req["id"], {})
        uncovered = tr.get("uncovered", [])
        cues = tr.get("uncovered_cues", [])
        judged = [c for c in top if c.hard] or top
        top_ok = bool(judged) and all(by_id[c.id].passed for c in judged)
        if not group:
            status, note = "unverified", "no check passed the gates"
        elif not top_ok:
            status, note = "fail", ""
        elif uncovered or cues:
            status = "unverified"
            note = "its checks pass, but not checked: " + ", ".join(
                [u["text"] for u in uncovered] + [f'"{q["cue"]}"' for q in cues])
        else:
            status, note = "pass", ""
        rows.append({
            "l1_id": req["id"], "text": req["text"], "method": req.get("method"), "status": status,
            "passed": status == "pass",
            "margin": min((by_id[c.id].margin for c in top), default=None), "note": note,
            "checks": [{"id": c.id, "type": c.type, "level": c.level, "hard": c.hard, "text": c.text,
                        "passed": by_id[c.id].passed, "margin": by_id[c.id].margin,
                        "measured": by_id[c.id].evidence.get("measured"),
                        "expected": by_id[c.id].evidence.get("expected"),
                        "evidence": by_id[c.id].evidence.get("detail")} for c in group],
            "rejected": len(tr.get("rejected", [])),
        })
    order = {"fail": 0, "unverified": 1, "pass": 2}
    rows.sort(key=lambda r: (order[r["status"]], r["margin"] if r["margin"] is not None else -1e9))
    system = [{"id": c.id, "text": c.text, "hard": c.hard, "passed": by_id[c.id].passed,
               "margin": by_id[c.id].margin, "evidence": by_id[c.id].evidence.get("detail")}
              for c in cs.checks if c.l1_id == SYSTEM_L1]
    return rows, system


def uncontrollable_items(cs: CascadeState) -> List[str]:
    last = cs.design_reports[-1] if cs.design_reports else cs.reports.get("design", {})
    return list(last.get("uncontrollable", [])) if last else []


def matrix_record(d) -> dict:
    cs: CascadeState = d.cascade
    llm_calls = cs.llm_calls
    return {
        "request": d.base_request or d.request, "outcome": cs.outcome,
        "rows": cs.rows, "system": cs.system_rows,
        "loops": cs.reports, "design_runs": cs.design_reports,
        "uncontrollable": uncontrollable_items(cs), "dropped": cs.dropped, "refinements": cs.refinements,
        "checks_version": cs.version, "wall_time_s": round(time.time() - cs.started, 1), "llm_calls": llm_calls,
    }


def matrix_markdown(rec: dict) -> str:
    def cell(text) -> str:
        return str(text).replace("|", "/").replace("\n", " ")

    lines = [f"# Verification matrix", "", f"Request: {cell(rec['request'])}", "",
             f"Outcome: **{rec['outcome']}** (checks version {rec['checks_version']}, "
             f"{rec['wall_time_s']} s, {rec['llm_calls']} LLM calls)", "",
             "| Status | L1 | Requirement | Margin | Evidence |", "|---|---|---|---|---|"]
    for r in rec["rows"]:
        failing = [c for c in r["checks"] if not c["passed"]]
        ev = "; ".join(f"{c['id']}: {c['evidence']}" for c in (failing or r["checks"])[:3]) or r["note"]
        if r["note"] and r["status"] != "fail":
            ev = r["note"] + ("; " + ev if ev and ev != r["note"] else "")
        margin = f"{r['margin']:+.3f}" if r["margin"] is not None else "n/a"
        lines.append(f"| {r['status'].upper()} | {r['l1_id']} | {cell(r['text'])} | {margin} | {cell(ev)} |")
    lines += ["", "## Checks per requirement", ""]
    for r in rec["rows"]:
        lines.append(f"**{r['l1_id']}** ({r['status']}): {r['text']}")
        for c in r["checks"]:
            lines.append(f"- {'ok' if c['passed'] else 'FAIL'} `{c['id']}` [{c['type']}, level {c['level']}"
                         f"{'' if c['hard'] else ', soft'}] {c['text']} -> {c['evidence']} (margin {c['margin']:+.3f})")
        if not r["checks"]:
            lines.append(f"- {r['note']}")
        lines.append("")
    lines += ["## System checks", ""]
    for s in rec["system"]:
        lines.append(f"- {'ok' if s['passed'] else 'FAIL'} `{s['id']}`{'' if s['hard'] else ' (soft)'}: "
                     f"{s['text']} -> {s['evidence']}")
    lines += ["", "## Loop reports", ""]
    for k, v in rec["loops"].items():
        if not isinstance(v, dict) or "status" not in v:
            continue
        lines.append(f"- `{k}`: {v['status']} after {v['iterations']} iteration(s); error {v['best_error']}"
                     + (f"; uncontrollable: {', '.join(v['uncontrollable'])}" if v.get("uncontrollable") else "")
                     + (f"; residual: {cell('; '.join(v['residual'][:3]))}" if v.get("residual") else ""))
    for i, v in enumerate(rec["design_runs"], 1):
        lines.append(f"- inner loop run {i} (checks v{v.get('checks_version')}): {v['status']}, "
                     f"{v['iterations']} iteration(s)")
    if rec["uncontrollable"]:
        lines += ["", "## Uncontrollable with the current shape library", ""]
        lines += [f"- {u}" for u in rec["uncontrollable"]]
    if rec["dropped"] or rec["refinements"]:
        lines += ["", "## Outer loop", ""]
        lines += [f"- iteration {r['iteration']}: {'; '.join(r['changes'])}" for r in rec["refinements"]]
        lines += [f"- dropped `{x['check']['id']}`: {x['reason']}" for x in rec["dropped"]]
    return "\n".join(lines) + "\n"


def matrix_text(rec: dict) -> str:
    lines = [f"Verification matrix ({rec['outcome']}):"]
    for r in rec["rows"]:
        margin = f"{r['margin']:+.3f}" if r["margin"] is not None else "  n/a "
        lines.append(f"  {r['status'].upper():<10} {margin}  {r['l1_id']}: {r['text']}"
                     + (f"  ({r['note']})" if r["note"] else ""))
        for c in r["checks"]:
            lines.append(f"      {'ok ' if c['passed'] else 'NO '} {c['id']} [{c['type']}/L{c['level']}] {c['evidence']}")
    for s in rec["system"]:
        lines.append(f"  {'ok ' if s['passed'] else 'NO '} {s['id']}: {s['evidence']}")
    if rec["uncontrollable"]:
        lines.append(f"  uncontrollable: {', '.join(rec['uncontrollable'])}")
    return "\n".join(lines)


def finalize(d, llm=None) -> dict:
    """Measure the final design against the frozen checks, set statuses, write the matrix files."""
    cs: CascadeState = d.cascade
    results = cc.run_checks(d, cs.checks) if cs.checks else []
    cs.rows, cs.system_rows = l1_rows(cs, results)
    sys_ok = all(s["passed"] for s in cs.system_rows if s["hard"])
    cs.outcome = "verified" if cs.rows and all(r["passed"] for r in cs.rows) and sys_ok else "unsatisfied"
    failing = [r for r in results if not r.passed and r.hard]
    names = {c.name for c in d.components}
    # Failures no existing part can be blamed for (a check on a missing part, a crashed
    # or invalid check, an unverified L1, a failing system check) are the whole
    # design's: every component carries them, so design.json's per-component summary
    # can never say all_verified while the outcome is unsatisfied.
    orphan = [f"{r.check_id}: {r.evidence.get('detail')}" for r in failing
              if not names.intersection(r.depends_on.get("components", []))]
    orphan += [f"L1 {r['l1_id']} {r['status']}" + (f": {r['note']}" if r["note"] else "")
               for r in cs.rows if r["status"] == "unverified"]
    if cs.outcome != "verified" and not failing and not orphan:
        orphan.append(f"outcome {cs.outcome}")
    for c in d.components:   # per-component status for design.json / verification_summary
        mine = [f"{r.check_id}: {r.evidence.get('detail')}" for r in failing
                if c.name in r.depends_on.get("components", [])]
        c.residual = mine + orphan
        c.status = "unsatisfied" if c.residual else "verified"
        c.verified = c.spec_key()
    if llm is not None:
        cs.llm_calls = llm.calls if isinstance(llm.calls, int) else len(llm.calls)
    rec = matrix_record(d)
    d.workdir.mkdir(parents=True, exist_ok=True)
    (d.workdir / "verification_matrix.json").write_text(json.dumps(rec, indent=2, default=str))
    (d.workdir / "verification_matrix.md").write_text(matrix_markdown(rec))
    d.feedback_notes = [n for n in d.feedback_notes if not n.startswith("L1 ")]
    for r in cs.rows:
        if r["status"] != "pass":
            d.feedback_notes.append(f"L1 {r['l1_id']} {r['status'].upper()}: {r['text']}")
    return rec


class WriteMatrix(ca.Step):
    def __init__(self, design, llm=None):
        super().__init__("write_matrix", design)
        self.llm = llm

    def update(self):
        rec = finalize(self.design, self.llm)
        self.logger.info(f"verification matrix: {rec['outcome']}; "
                         + ", ".join(f"{r['l1_id']} {r['status']}" for r in rec["rows"]))
        return Status.SUCCESS


class CascadeReview(ca.HumanReview):
    """HumanReview that shows the verification matrix instead of the per-part verdicts."""

    def show(self) -> None:
        d = self.design
        print("\n" + "=" * 72)
        print(d.base_request or d.request)
        print(matrix_text(matrix_record(d)))
        print(f"\nOpenSCAD: {d.assembly}")
        for name, path in d.views.items():
            print(f"  {name:>5}: {path}")
        print(f"Matrix: {d.workdir / 'verification_matrix.md'}")
        print("=" * 72)


# ---------------------------------------------------------------------------
# Tree
# ---------------------------------------------------------------------------


def outer_loop(design, llm) -> py_trees.behaviour.Behaviour:
    """Inner design loop + report + RefineChecks, retried while the checks change (<= MAX_OUTER)."""
    inner = design_loop(design, llm)
    return py_trees.decorators.Retry("outer_loop", py_trees.composites.Sequence("outer_pass", memory=True, children=[
        py_trees.decorators.FailureIsSuccess("inner", inner), RecordDesignReport(design, inner),
        RefineChecks(design, llm)]), num_failures=MAX_OUTER + 1)


def build_cascade_tree(design, llm, input_fn: Callable[[str], str] = input, auto_approve: bool = False,
                       max_rounds: int = 40) -> py_trees.behaviour.Behaviour:
    if not design.l1:
        raise ValueError("the cascade needs L1 requirements (--l1)")
    if design.cascade is None:
        design.cascade = CascadeState(l1=list(design.l1))
    cs: CascadeState = design.cascade
    understand = py_trees.composites.Sequence("understand", memory=True, children=[
        ca.ExtractComponents(design, llm),
        ca.ForEach("components", design, lambda d: [ca.component_subtree(d, llm, c) for c in d.components]),
    ])
    build = py_trees.composites.Sequence("build", memory=True, children=[
        ca.Layout(design), ca.EmitScad(design), ca.CompileCheck(design), ca.PhysicalChecks(design)])
    provisional = py_trees.decorators.Retry("provisional_loop", py_trees.composites.Sequence(
        "provisional", memory=True, children=[understand, ca.AccountForNumbers(design, llm), build]),
        num_failures=max_rounds)
    translate = ca.ForEach("translate", design, lambda d: [] if cs.frozen else [
        py_trees.decorators.FailureIsSuccess(f"translated:{r['id']}", translate_loop(d, llm, r)) for r in cs.l1])
    outer = outer_loop(design, llm)
    stages = [provisional, translate, FreezeChecks(design), outer, Rebuild(design), ca.RenderViews(design),
              WriteMatrix(design, llm), CascadeReview(design, llm, input_fn=input_fn, auto_approve=auto_approve)]
    review = py_trees.decorators.Retry("review_loop", py_trees.composites.Sequence(
        "cascade_design", memory=True, children=stages), num_failures=max_rounds)
    return py_trees.composites.Sequence("cad_cascade", memory=True, children=[review, ca.ExportModel(design)])
