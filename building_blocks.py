"""Generic, catalogue-driven building blocks of --mode assembly (migration delta R11; owner decision D1).

Each block is three things, and nothing else:

* a **plant builder** that derives geometry from part.json data (geometry primitives, keep-outs, plane datums) and the
  generic values of design_rules.json (`rules` and the `building_blocks` vocabularies);
* a **typed action** the controller (the local LLM) may choose, over the options Python enumerates as buildable for
  this design (each option is validated before it is offered; an option the plant cannot build is not offered, and why
  is reported to the controller in the sensor's words);
* **checks** that report whether it works. Each result says how it knows (evidence `basis`, review fix 3):
  `measured` on the built solids and the delivered STLs (support, rib interference, panel seat, panel hole, the
  clear_of checks), or `design` (a design check on the plant's resolved numbers that cannot see a defect in the solids:
  the retention free travel, snap strain and overlap, panel thickness).

Python never reads the request to pick a block: the proposal takes the vocabulary's default option (a plant default,
`rule:default_retention`), the sensors report the physics, and the controller corrects it with an action.

Blocks in this module:

1. Contents admission (plant / controller information): every catalogue part the text names by a part.json alias is
   offered to the Contents question, unless the part is an accessory another catalogue part refers to (a plug a
   connector `mates`, a stack option) or a fastener (chosen by the fastener rules). Until R11 only electronics kinds and
   parts with a mount_holes interface were offered, so motors, bearings, extrusions, fans, batteries and switches could
   never enter a design.
2. Cradle retention for a primary part without mounting holes (plant + action `set_retention` + checks `retention`,
   `supported`, `rib_interference`, `snap_strain`, `snap_overlap`; retention and snap_* are design checks): the part rests on its seat plane
   (parts.seat_interface) on printed ledges under its edges, inside a locating rim with a sliding fit; the option adds
   crush ribs or two cantilever snap clips. Every position comes from the part's own geometry and keep-outs; every size
   from design_rules.json.

Nothing here holds a number, part or face of one request (test_no_hardcoding.py scans this module); every rule:*
decision string is registered in controller_rules.json (test_controller_authority.py).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

import assembly as A            # circular on purpose: only module attributes are read, at call time
import assembly_checks as ac
import cad_checks as cc
import feature_graph as fg
import parts as pt

RETENTION = "retention"                  # the building_blocks vocabulary of the cradle block (design_rules.json)
RETENTION_CHOICE = "retention[{item}]"   # the decision key (st.choices)
SET_RETENTION = "set_retention"          # the action kind
SIDES = {"-X": (0, -1.0), "+X": (0, 1.0), "-Y": (1, -1.0), "+Y": (1, 1.0)}   # side -> (normal axis, outward sign)
AXIS_SIDES = (("-X", "+X"), ("-Y", "+Y"))
DIRECTIONS_HELD = ("-z", "+z", "-X", "+X", "-Y", "+Y")
CRADLE_ROLES = ("support", "rim", "crush_rib", "snap_arm", "snap_hook")
EPS = 1e-6
MEASURED = "measured"   # evidence basis: measured on the built solids / delivered STLs (review fix 3)
DESIGN = "design"       # evidence basis: a design check on resolved numbers, not a measurement of the solids


# ---------------------------------------------------------------------------
# Block 1: Contents admission (every named non-accessory catalogue part is a candidate)
# ---------------------------------------------------------------------------


def accessory_ids(catalog: pt.Catalog) -> set:
    """Parts another catalogue part refers to as its accessory (a plug some connector `mates`, a stack option some
    module's mount offers) and fasteners: they are chosen by the rules that read those references, never put in a design
    by the Contents question. Read from catalogue data only."""
    out = set()
    for pid in catalog.ids():
        part = catalog.get(pid)
        if part.kind == "fastener":
            out.add(pid)
        for c in part.data.get("connectors", []) or []:
            if c.get("mates"):
                out.add(c["mates"])
        out.update((part.data.get("mount") or {}).get("stack_options", []) or [])
    return out


def report_unsized(st: "A.AssemblyState", unsized: Sequence[Tuple[dict, str]]) -> None:
    """Parts the Contents answer put in whose request-sized params the text states no number for: the plant cannot
    instantiate them, so the answer is rejected for that part (as an infeasible action is) and reported: each becomes an
    unplaced item whose content_placed check fails with the reason. Until R11 one such part stopped the whole run at
    Contents. (A set_param action for its size is migration delta R08.)"""
    for it, why in unsized:
        u = {"id": it.get("id") or it["part"], "part": it["part"], "quantity": it.get("quantity", 1),
             "reason": f"{why}; the plant cannot build a part whose size the text does not state"}
        st.unplaced.append(u)
        st.notes.append(f"contents: {u['id']} ({u['part']}) is not in the design: {u['reason']}")


def admissible_named(st: "A.AssemblyState", already: Sequence[str]) -> List[str]:
    """The catalogue parts the request or an L1 names (A.named_parts: a contiguous alias run) that are not already
    candidates and not accessories, in catalogue order. The controller answers each one's quantity (0 = not in the
    design); Python adds nothing to the design here."""
    named = A.named_parts(st)
    skip = accessory_ids(st.catalog)
    return [pid for pid in st.catalog.ids() if pid in named and pid not in already and pid not in skip]


# ---------------------------------------------------------------------------
# Block 2: cradle retention for a primary without mounting holes
# ---------------------------------------------------------------------------


def supportable(st: "A.AssemblyState", item: Mapping[str, Any]) -> bool:
    """The plant can hold this content item as the primary: it offers a mount_holes interface, or a seat interface (it
    rests flat on a seat plane: parts.seat_interface). Plant feasibility for the primary-reference rule; no text."""
    part = st.catalog.get(item["part"])
    if pt.mount_interface(part) is not None:
        return True
    try:
        return pt.seat_interface(st.catalog.instantiate(part.id, item.get("params") or {})) is not None
    except (pt.PartError, fg.ExprError, fg.MissingRefError, KeyError, ValueError):
        return False


def primary_placed(st: "A.AssemblyState"):
    try:
        return st.placed.get(A.PRIMARY)
    except (AttributeError, StopIteration, KeyError):
        return None


SUPPORT_CHOICE = "support[{item}]"       # a primary with mounting holes held by a cradle instead of screws
CRADLE = "cradle"


def cradle_support(st: "A.AssemblyState") -> bool:
    """The primary's holes take no catalogue screw and the arrangement put it in a cradle (cradle_instead_of_screws)."""
    return (st.choices.get(SUPPORT_CHOICE.format(item=A.PRIMARY)) or {}).get("value") == CRADLE


def is_cradle(st: "A.AssemblyState") -> bool:
    """The placed primary rests on its seat plane in a cradle: it offers no mount_holes interface, or no catalogue screw
    passes its holes (cradle_support)."""
    p = primary_placed(st)
    return p is not None and (pt.mount_interface(p.inst.part) is None or cradle_support(st))


def cradle_instead_of_screws(st: "A.AssemblyState", inst: pt.PartInstance) -> bool:
    """A primary whose mounting holes no catalogue screw passes (the guardrail: a screw that physically fits its hole)
    is held by a cradle on its mount `seat` plane instead, when its geometry rests on that plane; records
    support[board] = cradle (rule:no_screw_fits). False when it cannot rest there (the arrangement then stops)."""
    _, seat, top = pt.mount_names(inst.part)
    z = float(inst.datums[seat].at[2])
    tol = st.rules.values["measure_tol"]
    if not any(abs(float(g.bbox()[0][2]) - z) <= tol for g in inst.geometry):
        return False
    A.choice(st, SUPPORT_CHOICE.format(item=A.PRIMARY), CRADLE, "rule:no_screw_fits",
             reason=f"no catalogue screw passes the {inst.part.id} mounting holes; it rests on {seat} in a cradle")
    return True


def options(rules: pt.Rules) -> Dict[str, dict]:
    return dict(((rules.building_blocks or {}).get(RETENTION) or {}).get("options") or {})


def default_option(rules: pt.Rules) -> str:
    return next(k for k, v in options(rules).items() if v.get("default"))


@dataclass
class Box3:
    """An axis-aligned box in the world frame: lo, hi (3 each). `keepout`: a part.json keep-out (a clearance volume the
    part's author declared, so the plant does not grow it by a clearance again)."""
    lo: np.ndarray
    hi: np.ndarray
    what: str = ""
    keepout: bool = False

    def grown(self, d: float) -> "Box3":
        if self.keepout:
            return self
        g = np.array([d, d, 0.0])
        return Box3(self.lo - g, self.hi + g, self.what, self.keepout)


def world_box(prim, pose: np.ndarray, what: str = "", keepout: bool = False) -> Box3:
    pose = np.asarray(pose, dtype=float)
    lo, hi = prim.bbox()
    pts = np.array([[hi[i] if c >> i & 1 else lo[i] for i in range(3)] for c in range(8)])
    pts = pts @ pose[:3, :3].T + pose[:3, 3]
    return Box3(pts.min(axis=0), pts.max(axis=0), what, keepout)


def free_intervals(lo: float, hi: float, blocked: Sequence[Tuple[float, float]], min_len: float) -> List[Tuple[float, float]]:
    """[lo, hi] minus the blocked intervals; pieces shorter than min_len are dropped."""
    out, cur = [], lo
    for a, b in sorted(blocked):
        if b <= cur:
            continue
        if a >= hi:
            break
        if a - cur >= min_len - EPS:
            out.append((cur, min(a, hi)))
        cur = max(cur, b)
    if hi - cur >= min_len - EPS:
        out.append((cur, hi))
    return [(a, b) for a, b in out if b - a >= min_len - EPS]


@dataclass
class Feature:
    """One printed cradle feature: a box in the world frame from z0 (a number, or None = the base bottom) to z1."""
    id: str
    role: str
    side: str
    x0: float
    x1: float
    y0: float
    y1: float
    z1: float
    z0: Optional[float] = None


@dataclass
class CradlePlan:
    """The cradle the plant derives for one option, in numbers (world frame), or the reason it cannot be built."""
    option: str
    seat: str
    top: str
    seat_z: float
    top_z: float
    part_top_z: float
    floor_z: float
    footprint: Tuple[float, float, float, float]          # x0, x1, y0, y1 of the geometry resting on the seat
    clearance: float
    features: List[Feature] = field(default_factory=list)
    held: Dict[str, float] = field(default_factory=dict)    # direction -> designed free travel (None: not held here)
    infeasible: Optional[str] = None
    ribs: List[dict] = field(default_factory=list)          # {id, side, interference}
    clips: List[dict] = field(default_factory=list)         # {id, side, overlap, strain, free_length}
    notes: List[str] = field(default_factory=list)

    @property
    def centre(self) -> Tuple[float, float]:
        x0, x1, y0, y1 = self.footprint
        return (x0 + x1) / 2, (y0 + y1) / 2


def _side_geometry(fp, side: str) -> Tuple[int, float, float, int, float, float]:
    """(normal axis, outward sign, edge coordinate, tangent axis, tangent lo, tangent hi) of a footprint side."""
    x0, x1, y0, y1 = fp
    axis, sign = SIDES[side]
    lo = (x0, y0)
    hi = (x1, y1)
    edge = hi[axis] if sign > 0 else lo[axis]
    t = 1 - axis
    return axis, sign, edge, t, lo[t], hi[t]


def _rect(axis: int, n0: float, n1: float, t0: float, t1: float) -> Tuple[float, float, float, float]:
    """(x0, x1, y0, y1) of a rectangle given along a normal axis (n) and its tangent (t)."""
    a, b = sorted((n0, n1))
    return (a, b, t0, t1) if axis == 0 else (t0, t1, a, b)


def _overlaps(box: Box3, rect: Tuple[float, float, float, float], z0: float, z1: float) -> bool:
    x0, x1, y0, y1 = rect
    return (box.lo[0] < x1 - EPS and box.hi[0] > x0 + EPS and box.lo[1] < y1 - EPS and box.hi[1] > y0 + EPS
            and box.lo[2] < z1 - EPS and box.hi[2] > z0 + EPS)


def cradle_plan(st: "A.AssemblyState", option: Optional[str] = None) -> CradlePlan:
    """The cradle for `option` (the current retention choice when None), sized from the primary's own data:

    * footprint: the plan box of the geometry primitives that rest on the seat plane (parts.seat_interface);
    * ledges (`support`): on each footprint side, the strip rules.support_ledge_width inside the edge, minus every part
      primitive or keep-out below the seat there (grown by rules.part_to_wall), in pieces of at least
      rules.support_min_length, from the floor up to the seat; they must hold the part's plan centre between them;
    * rim (`rim`): on each side, outside the edge by the sliding fit (rules.sliding_fit), rules.retention_wall thick,
      up to the seat + min(top - seat, rules.pocket_rim_height), broken wherever a part primitive or keep-out outside the
      footprint comes within spec.board_clearance of it (an overhanging connector);
    * crush_ribs: per rim piece, one rib per rules.crush_rib_pitch (at least one), rules.crush_rib_width wide, reaching
      rules.crush_rib_interference into the outline between the seat and the rim top; a rib a part feature blocks is
      dropped;
    * snap_clips: on the first pair of opposite sides (long sides first) whose longest rim pieces take a clip and whose
      hook strip over the top face is clear of every part primitive and keep-out, a cantilever arm
      (rules.snap_arm_thickness x rules.snap_clip_width) with a hook rules.snap_overlap over the top face, rules.snap_gap
      above it, rules.snap_hook_height tall; strain 1.5 t y / L^2 (y = fit + overlap, L = free arm length) must stay
      within rules.snap_strain_max, else the option is infeasible.
    """
    r, s = st.rules.values, st.spec
    p = primary_placed(st)
    inst, pose = p.inst, p.pose
    _, seat_name, top_name = A.primary_mount(st)       # the seat interface, or the mount's seat/top (support[board])
    iface = {"seat": seat_name, "top": top_name}
    seat_z = float(pt.transform(pt.lookup_datum(inst.datums, iface["seat"]), pose).at[2])
    top_z = float(pt.transform(pt.lookup_datum(inst.datums, iface["top"]), pose).at[2])
    tol = r["measure_tol"]
    boxes = [world_box(g, pose, g.id) for g in inst.geometry]
    flat = [g.primitive == "box" or (g.primitive == "cylinder" and abs(abs(float(g.dir[2])) - 1.0) <= pt.UNIT_TOL)
            for g in inst.geometry]                      # a face rests on a ledge; a lying cylinder only touches a line
    resting = [b for b, f in zip(boxes, flat) if f and abs(b.lo[2] - seat_z) <= tol]
    if not resting:
        raise pt.PartError(f"{inst.part.id}: no flat face of its geometry rests on {seat_name}, no cradle")
    keepouts = [world_box(k, pose, f"keepout {k.id}", keepout=True) for k in inst.keepouts]
    others = [b for b in boxes if abs(b.lo[2] - seat_z) > tol] + keepouts
    above = [b for b in boxes + keepouts if b.hi[2] > top_z + tol]       # what a hook over the top face could meet
    fp = (min(b.lo[0] for b in resting), max(b.hi[0] for b in resting),
          min(b.lo[1] for b in resting), max(b.hi[1] for b in resting))
    floor_z = seat_z - s["keepout_below"] - r["design_margin"]
    part_top = max(float(b.hi[2]) for b in boxes)
    c, wall, bc = r["sliding_fit"], r["retention_wall"], s["board_clearance"]
    option = option or retention_choice(st)["value"]
    plan = CradlePlan(option, iface["seat"], iface["top"], seat_z, top_z, part_top, floor_z, fp, c)
    min_len = r["support_min_length"]

    # ledges under the edges
    w, ptw = r["support_ledge_width"], r["part_to_wall"]
    below = [b for b in others if b.lo[2] < seat_z - tol]
    for side in SIDES:
        axis, sign, edge, t, tlo, thi = _side_geometry(fp, side)
        n0, n1 = edge + sign * (c + wall), edge - sign * w
        rect = _rect(axis, n0, n1, tlo, thi)
        blocked = [(b.grown(ptw).lo[t], b.grown(ptw).hi[t]) for b in below
                   if _overlaps(b.grown(ptw), rect, floor_z - bc, seat_z)]
        for k, (a, b) in enumerate(free_intervals(tlo, thi, blocked, min_len)):
            plan.features.append(Feature(f"cradle_support_{side[1].lower()}{'m' if sign < 0 else 'p'}_{k + 1}",
                                         "support", side, *_rect(axis, n0, n1, a, b), z1=seat_z))
    sup = [f for f in plan.features if f.role == "support"]
    cx, cy = plan.centre
    if not sup:
        plan.infeasible = "no ledge fits under the part: its own features or keep-outs cover every edge strip"
        return plan
    inner = []
    for f in sup:                                  # the part of each ledge under the outline
        x0, x1, y0, y1 = f.x0, f.x1, f.y0, f.y1
        inner.append((max(x0, fp[0]), min(x1, fp[1]), max(y0, fp[2]), min(y1, fp[3])))
    if not (min(q[0] for q in inner) <= cx <= max(q[1] for q in inner)
            and min(q[2] for q in inner) <= cy <= max(q[3] for q in inner)):
        plan.infeasible = "the ledges that fit do not hold the part's plan centre between them (it would tip)"
        return plan
    plan.held["-z"] = 0.0

    # the locating rim
    rim_top = seat_z + min(top_z - seat_z, r["pocket_rim_height"])
    rims: Dict[str, List[Tuple[float, float]]] = {}
    for side in SIDES:
        axis, sign, edge, t, tlo, thi = _side_geometry(fp, side)
        n0, n1 = edge + sign * c, edge + sign * (c + wall)
        t0, t1 = (tlo - c - wall, thi + c + wall) if axis == 0 else (tlo - c, thi + c)
        rect = _rect(axis, n0, n1, t0, t1)
        blocked = [(b.grown(bc).lo[t], b.grown(bc).hi[t]) for b in others
                   if _overlaps(b.grown(bc), rect, floor_z, rim_top)]
        rims[side] = free_intervals(t0, t1, blocked, min_len)

    # the option's feature
    if option == "snap_clips":
        clip = _snap_clips(st, plan, rims, others, above, fp, seat_z, top_z, floor_z)
        if clip is not None:
            plan.infeasible = clip
            return plan
    for side, pieces in rims.items():
        axis, sign, edge, t, tlo, thi = _side_geometry(fp, side)
        n0, n1 = edge + sign * c, edge + sign * (c + wall)
        for k, (a, b) in enumerate(pieces):
            plan.features.append(Feature(f"cradle_rim_{side[1].lower()}{'m' if sign < 0 else 'p'}_{k + 1}", "rim", side,
                                         *_rect(axis, n0, n1, a, b), z1=rim_top))
    if option == "crush_ribs":
        _crush_ribs(st, plan, rims, others, fp, seat_z, rim_top)
        sides_with = {x["side"] for x in plan.ribs}
        if not any(a in sides_with and b in sides_with for a, b in AXIS_SIDES):
            plan.infeasible = "no pair of opposite rim sides takes a crush rib clear of the part's own features"
            return plan
    for side in SIDES:                              # lateral free travel on each side
        if option == "crush_ribs" and any(x["side"] == side for x in plan.ribs):
            plan.held[side] = 0.0
        elif rims.get(side) or any(x["side"] == side for x in plan.clips):
            plan.held[side] = c
    if option == "crush_ribs":
        sides_with = {x["side"] for x in plan.ribs}
        if all(a in sides_with and b in sides_with for a, b in AXIS_SIDES):
            plan.held["+z"] = 0.0                    # friction on both axes holds the part down
    elif option == "snap_clips":
        plan.held["+z"] = r["snap_gap"]
    return plan


def _crush_ribs(st, plan: CradlePlan, rims, others, fp, seat_z: float, rim_top: float) -> None:
    r = st.rules.values
    c, wall = plan.clearance, r["retention_wall"]
    rw, pitch, i = r["crush_rib_width"], r["crush_rib_pitch"], r["crush_rib_interference"]
    for side, pieces in rims.items():
        axis, sign, edge, t, tlo, thi = _side_geometry(fp, side)
        n0, n1 = edge + sign * (c + wall / 2), edge - sign * i
        k = 0
        for a, b in pieces:
            lo, hi = max(a, tlo), min(b, thi)            # a rib presses on the part's edge, not past its corners
            if hi - lo < rw:
                continue
            n = max(1, int(math.floor((hi - lo) / pitch)))
            for j in range(n):
                tc = lo + (j + 0.5) * (hi - lo) / n
                rect = _rect(axis, n0, n1, tc - rw / 2, tc + rw / 2)
                if any(_overlaps(o, rect, seat_z, rim_top) for o in others):
                    plan.notes.append(f"crush rib on {side} at {tc:.2f} dropped: a part feature is there")
                    continue
                k += 1
                fid = f"cradle_rib_{side[1].lower()}{'m' if sign < 0 else 'p'}_{k}"
                plan.features.append(Feature(fid, "crush_rib", side, *rect, z1=rim_top, z0=seat_z))
                plan.ribs.append({"id": fid, "side": side, "interference": i})


def _snap_clips(st, plan: CradlePlan, rims, others, above, fp, seat_z: float, top_z: float,
                floor_z: float) -> Optional[str]:
    """Adds two snap clips on opposite sides and frees their arms from the rim; returns why none fits, or None."""
    r, s = st.rules.values, st.spec
    c, t_arm, b = plan.clearance, r["snap_arm_thickness"], r["snap_clip_width"]
    ov, gap, hh, slot, bc = r["snap_overlap"], r["snap_gap"], r["snap_hook_height"], r["snap_slot"], s["board_clearance"]
    hook0, hook1 = top_z + gap, top_z + gap + r["snap_hook_height"]
    free_len = hook0 - floor_z
    y = c + ov
    strain = 1.5 * t_arm * y / (free_len * free_len) if free_len > 0 else math.inf
    x0, x1, y0, y1 = fp
    # long sides first: a side whose normal is X runs along Y, so its length is the footprint's Y extent
    pairs = sorted(AXIS_SIDES, key=lambda pr: -((y1 - y0) if SIDES[pr[0]][0] == 0 else (x1 - x0)))
    reasons = []
    for pair in pairs:
        placed = []
        for side in pair:
            axis, sign, edge, t, tlo, thi = _side_geometry(fp, side)
            pieces = [(a, bb) for a, bb in rims.get(side, []) if min(bb, thi) - max(a, tlo) >= b + 2 * slot]
            if not pieces:
                reasons.append(f"{side}: no rim piece {b + 2 * slot:g} mm long")
                break
            a, bb = max(pieces, key=lambda q: q[1] - q[0])
            tc = (max(a, tlo) + min(bb, thi)) / 2
            arm = _rect(axis, edge + sign * c, edge + sign * (c + t_arm), tc - b / 2, tc + b / 2)
            hook = _rect(axis, edge + sign * (c + t_arm), edge - sign * ov, tc - b / 2, tc + b / 2)
            hit = [o.what for o in others if _overlaps(o.grown(bc), arm, floor_z, hook1 + bc)]
            hit += [o.what for o in above if _overlaps(o.grown(bc), hook, top_z, hook1 + bc)]
            if hit:
                reasons.append(f"{side}: the hook or arm meets {', '.join(sorted(set(hit)))}")
                break
            placed.append((side, axis, sign, edge, tc, arm, hook))
        else:
            if strain > r["snap_strain_max"] + EPS:
                return (f"a snap arm {free_len:.2f} mm long bends to strain {strain:.3f} > rules.snap_strain_max "
                        f"{r['snap_strain_max']:g} (too short above the floor)")
            for side, axis, sign, edge, tc, arm, hook in placed:
                tag = f"{side[1].lower()}{'m' if sign < 0 else 'p'}"
                plan.features.append(Feature(f"cradle_snap_arm_{tag}", "snap_arm", side, *arm, z1=hook1))
                plan.features.append(Feature(f"cradle_snap_hook_{tag}", "snap_hook", side, *hook, z1=hook1, z0=hook0))
                plan.clips.append({"id": f"cradle_snap_arm_{tag}", "side": side, "overlap": ov, "strain": strain,
                                   "free_length": free_len})
                rims[side] = [q for a, bb in rims[side]
                              for q in free_intervals(a, bb, [(tc - b / 2 - slot, tc + b / 2 + slot)],
                                                      r["support_min_length"])]
            return None
    return "no pair of opposite sides takes a snap clip: " + "; ".join(reasons)


# ----- the decision, the options, the derivation -----


def retention_choice(st: "A.AssemblyState") -> dict:
    """The retention option the plant derives: the controller's set_retention decision (st.control), else the
    vocabulary's default (rule:default_retention, plant: reads no text)."""
    if st.control.get(RETENTION):
        key = RETENTION_CHOICE.format(item=A.PRIMARY)
        return {"value": st.control[RETENTION], "by": (st.choices.get(key) or {}).get("by", "llm:controller")}
    return {"value": default_option(st.rules), "by": "rule:default_retention"}


def record_retention(st: "A.AssemblyState") -> None:
    """Record the proposal's retention decision (DeriveFeatures); a controller decision keeps its own record."""
    if not is_cradle(st) or st.control.get(RETENTION):
        return
    ch = retention_choice(st)
    A.choice(st, RETENTION_CHOICE.format(item=A.PRIMARY), ch["value"], ch["by"])


def retention_options(st: "A.AssemblyState") -> List[dict]:
    """Every retention option of the vocabulary with its feasibility for this design: {name, meaning, feasible,
    reason}. Feasibility is the plant's: the option's cradle can be derived from the part's data."""
    out = []
    for name, entry in options(st.rules).items():
        try:
            plan = cradle_plan(st, name)
            reason = plan.infeasible
        except (pt.PartError, KeyError, ValueError) as e:
            reason = str(e)
        out.append({"name": name, "meaning": entry.get("meaning", name), "feasible": reason is None,
                    "reason": reason})
    return out


def derive_cradle(st: "A.AssemblyState") -> None:
    """The cradle's feature-graph nodes (DeriveFeatures, after the base exists): each feature an `add` box on the base,
    from the base bottom (cavity.z0 - base.floor) or its own z0 up to its top, plus a `seat` envelope of the same box
    (the designed contact: the part touches its ledges, rim and ribs, so clear_board, inside_board and the solder-side
    keep-out exempt exactly these volumes, grown by their clearance). Raises ValueError when the chosen option cannot be
    built (the derivation fails with that note, so a controller action that chose it is infeasible)."""
    plan = cradle_plan(st)
    if plan.infeasible:
        raise ValueError(f"retention {plan.option}: {plan.infeasible}")
    g = st.graph
    for f in plan.features:
        cx, cy = (f.x0 + f.x1) / 2, (f.y0 + f.y1) / 2
        sx, sy = f.x1 - f.x0, f.y1 - f.y0
        z0 = "cavity.z0 - base.floor" if f.z0 is None else repr(float(f.z0))
        params = {"x": float(sx), "y": float(sy), "z": f"{float(f.z1)!r} - ({z0})"}
        pose = fg.Pose(offset=(float(cx), float(cy), z0))
        g.add(fg.Node(f.id, "add", "box", dict(params), pose, body="base", role=f.role,
                      source=f"rule:cradle.{plan.option}.{f.role}"))
        g.add(fg.Node(f"{f.id}_contact", "envelope", "box", dict(params), fg.Pose(offset=(float(cx), float(cy), z0)),
                      role="seat", source=f"rule:cradle.{plan.option}.contact"))
    for note in plan.notes:
        line = f"derive: {note}"
        if line not in st.notes:
            st.notes.append(line)


# ----- sensors -----


def add_cradle_checks(st: "A.AssemblyState", plan: ac.Plan) -> None:
    """The cradle's sensors (build_plan, in place of `seated` for a primary with mounting holes):

    * supported (measured on the base body): the base reaches the seat plane under every ledge (gap <=
      rules.seat_gap_max) and the ledges hold the part's plan centre between them;
    * retention (a design check, evidence basis `design`: computed from the cradle plan and the resolved cavity, not
      measured on the solids): the part's worst designed free travel over the six directions is at most
      rules.retention_play_max (-z: ledges; +-X, +-Y: rim or ribs, else the gap to the wall; +z: ribs (friction) or
      snap hooks, else the gap up to the lid at the split); controllable, actionable (set_retention);
    * rib_interference_<rib> (measured: band rules.crush_rib_interference_min..max); snap_strain_<arm> (design check:
      the beam formula on the planned arm, at most rules.snap_strain_max) and snap_overlap_<arm> (design check: the
      planned hook overlap, at least rules.snap_overlap_min)."""
    if not is_cradle(st):
        return
    r, res = st.rules.values, st.resolved
    cp = cradle_plan(st)
    cav, base = res.params["cavity"], res.params["base"]
    held = dict(cp.held)
    x0, x1, y0, y1 = cp.footprint
    wall_gap = {"-X": x0 - cav["x0"], "+X": cav["x1"] - x1, "-Y": y0 - cav["y0"], "+Y": cav["y1"] - y1}
    travel = {}
    for d in DIRECTIONS_HELD:
        if d in held:
            travel[d] = float(held[d])
        elif d == "-z":
            travel[d] = float(cp.seat_z - cav["z0"])
        elif d == "+z":
            travel[d] = float(base["split"] - cp.part_top_z)
        else:
            travel[d] = float(max(0.0, wall_gap[d]))
    worst = max(travel, key=lambda k: travel[k])
    opts = retention_options(st)
    cant = [f"{o['name']} ({o['reason']})" for o in opts if not o["feasible"]]
    item = A.primary_item(st) or {}
    name = A.human_name(st.catalog, item.get("part")) if item.get("part") else A.PRIMARY
    free = ", ".join(f"{d} {travel[d]:.2f}" for d in DIRECTIONS_HELD)
    detail = (f"{name} held by {cp.option}: designed free travel (mm) {free}; worst {worst} {travel[worst]:.2f} > "
              f"{r['retention_play_max']:g}" if travel[worst] > r["retention_play_max"] + r["measure_tol"] else
              f"{name} held by {cp.option}: designed free travel (mm) {free}")
    if cant:
        detail += "; options the plant cannot build here: " + "; ".join(cant)
    plan.add(f"retention_{A.PRIMARY}", RETENTION, f"the {name} is held in every direction: free travel at most "
             f"{r['retention_play_max']:g} mm (ledges, rim and the {cp.option} retention)", item=A.PRIMARY,
             option=cp.option, travel=travel, worst=worst, value=travel[worst], limit=r["retention_play_max"],
             detail=detail, where=f"{A.PRIMARY} ({name}) toward {worst}", parts=[item.get("part")] if item else [])
    probes, spans = [], []
    for f in cp.features:
        if f.role != "support":
            continue
        ix0, ix1, iy0, iy1 = max(f.x0, x0), min(f.x1, x1), max(f.y0, y0), min(f.y1, y1)
        probes.append({"id": f.id, "xy": [(ix0 + ix1) / 2, (iy0 + iy1) / 2],
                       "d": max(r["min_feature"], min(ix1 - ix0, iy1 - iy0) * 0.5)})
        spans.append([ix0, ix1, iy0, iy1])
    plan.add("supported", "supported", f"the {name} rests on printed ledges at its seat plane (gap <= "
             f"{r['seat_gap_max']:g} mm under every ledge) that hold its plan centre between them", body="base",
             probes=probes, seat_z=cp.seat_z, z_lo=float(cav["z0"]) - float(base["floor"]),
             z_hi=cp.seat_z + r["cut_overrun"], gap_max=r["seat_gap_max"], centre=list(cp.centre), spans=spans,
             parts=[item.get("part")] if item else [])
    for sp in plan.specs:                    # the cradle's contacts are the only printed material allowed at the
        if sp["id"] == "clear_keepout_top" and not sp["args"].get("minus"):   # part's top plane (rim, rib tops, hooks)
            sp["args"]["minus"] = "seats"
            sp["text"] += ", except the cradle's contacts with the part (rim, rib tops, snap hooks)"
    for rib in cp.ribs:                      # measured: how far the rib solid reaches into the part's reference solid
        vol = f"{rib['id']}_solid"
        plan.volumes[vol] = fg.solid(st.graph.nodes[rib["id"]], res)
        plan.sources[vol] = [rib["id"]]
        plan.add(f"rib_interference_{rib['id']}", "rib_interference", f"crush rib {rib['id']} reaches "
                 f"{r['crush_rib_interference_min']:g}-{r['crush_rib_interference_max']:g} mm into the part outline",
                 rib=vol, part_volume="board", axis=SIDES[rib["side"]][0], lo=r["crush_rib_interference_min"],
                 hi=r["crush_rib_interference_max"], designed=rib["interference"])
    for clip in cp.clips:
        plan.add(f"snap_strain_{clip['id']}", "snap_strain", f"snap arm {clip['id']} bends at most "
                 f"{r['snap_strain_max']:g} strain when the part goes in", value=clip["strain"],
                 limit=r["snap_strain_max"], detail=f"design check: strain 1.5 t y / L^2 = {clip['strain']:.4f} (L "
                 f"{clip['free_length']:.2f} mm) vs {r['snap_strain_max']:g}")
        plan.add(f"snap_overlap_{clip['id']}", "snap_overlap", f"the hook of {clip['id']} reaches at least "
                 f"{r['snap_overlap_min']:g} mm over the part's top face", value=clip["overlap"],
                 limit=r["snap_overlap_min"], detail=f"design check: planned overlap {clip['overlap']:.3f} vs {r['snap_overlap_min']:g}")


def _value(kind: str):
    def run(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
        if kind == "at_most":
            res = ac.value_at_most(cid, typ, a["value"], a["limit"], plan.tol, a.get("detail", ""))
        elif kind == "at_least":
            res = ac.value_at_least(cid, typ, a["value"], a["limit"], plan.tol, a.get("detail", ""))
        else:
            res = ac.value_in_band(cid, typ, a["value"], a["lo"], a["hi"], plan.tol, a.get("detail", ""))
        for k in ("where", "travel", "worst", "option", "item"):
            if k in a:
                res.evidence[k] = a[k]
        res.evidence["basis"] = DESIGN        # review fix 3: a value from the plan, not a measurement of the solids
        return res
    return run


def rib_interference_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured on the solids: the depth of the rib solid inside the part's reference solid, along the rib's side
    normal (0 when they do not meet: the rib does not grip), within the rules' band."""
    rib = plan.volumes[a["rib"]]
    inter = rib ^ plan.volumes[a["part_volume"]]
    depth = 0.0
    if not inter.is_empty():                 # mean depth = overlap volume / the rib's face area (tangent x height), so
        b = rib.bounding_box()               # faces that only touch (zero volume) add nothing
        t = 1 - a["axis"]
        depth = float(inter.volume()) / max(EPS, float((b[3 + t] - b[t]) * (b[5] - b[2])))
    res = ac.value_in_band(cid, typ, depth, a["lo"], a["hi"], plan.tol,
                           f"rib depth in the part {depth:.3f} mm (designed {a['designed']:g}) vs [{a['lo']:g}, "
                           f"{a['hi']:g}]")
    res.evidence["basis"] = MEASURED
    return res


def ratio_at_most(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """A dimensionless limit (a strain): no millimetre tolerance applies, so the comparison is exact. A design check
    (evidence basis `design`): the value comes from the plan, not from the solids."""
    v, lim = float(a["value"]), float(a["limit"])
    return ac._result(cid, typ, v <= lim, lim - v, "ratio",
                      {"value": round(v, 6), "limit": round(lim, 6), "detail": a.get("detail", ""), "basis": DESIGN})


def supported_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the top of the base body in a column under each ledge's centre, against the seat plane."""
    base = bodies[a["body"]]
    gaps, rows = [], []
    for pr in a["probes"]:
        top = ac.standoff_top(base, pr["xy"], pr["d"], a["z_lo"], a["z_hi"], plan.seg)
        gap = math.inf if top is None else abs(a["seat_z"] - top)
        gaps.append(gap)
        rows.append({"id": pr["id"], "xy": [round(v, 4) for v in pr["xy"]],
                     "top": None if top is None else round(top, 4)})
    sp, cx, cy, m = a.get("spans") or [], a["centre"][0], a["centre"][1], plan.tol.measure
    tipping = not sp or not (min(q[0] for q in sp) - m <= cx <= max(q[1] for q in sp) + m
                             and min(q[2] for q in sp) - m <= cy <= max(q[3] for q in sp) + m)
    worst = max(gaps) if gaps else math.inf
    passed = bool(gaps) and worst <= a["gap_max"] + plan.tol.measure and not tipping
    margin = (a["gap_max"] - worst + plan.tol.measure) / plan.tol.scale if gaps else -1.0
    detail = (f"worst ledge gap {worst:.4f} mm (max {a['gap_max']:g}) over {len(gaps)} ledge(s)"
              + ("; the ledges do not hold the part's plan centre" if tipping else ""))
    return ac._result(cid, typ, passed, margin if not tipping else min(margin, -1.0), "mm",
                      {"ledges": rows, "detail": detail, "basis": MEASURED})


EXTRA_CHECKS: Dict[str, Callable] = {
    RETENTION: _value("at_most"),
    "supported": supported_check,
    "rib_interference": rib_interference_check,
    "snap_strain": ratio_at_most,
    "snap_overlap": _value("at_least"),
}


# ---------------------------------------------------------------------------
# Block 3: panel mount (a part whose catalogue `mount.type` is panel: a bushing or lens through a hole in a panel)
# ---------------------------------------------------------------------------

PANEL = "panel"                          # st.control key: {item id: face}
SET_PANEL = "set_panel"
PANEL_FACES = {"lid": "through the lid (the closed enclosure's top panel), the part hanging below it"}
PANEL_SOURCE = "rule:panel_mount"


def is_panel_part(part: pt.Part) -> bool:
    """Catalogue data: the part's `mount.type` is panel (it is held by a panel it passes through)."""
    return (part.data.get("mount") or {}).get("type") == PANEL


@dataclass
class PanelGeometry:
    """A panel part's geometry in its own frame, read from its primitives: the body (the primitive with the largest plan
    area) stops against the panel's inner face at `contact_z` (the body's top); the primitives above it pass through a
    hole of `through_d` round the axis at `axis_xy`; the part hangs `depth` below the contact plane over `footprint`."""
    contact_z: float
    through_d: float
    axis_xy: Tuple[float, float]
    depth: float
    footprint: Tuple[float, float, float, float]
    max_panel: Optional[float]


def panel_geometry(inst: pt.PartInstance) -> Optional[PanelGeometry]:
    prims = list(inst.geometry)
    if len(prims) < 2:
        return None
    boxes = [(g, g.bbox()) for g in prims]
    body, (blo, bhi) = max(boxes, key=lambda q: ((q[1][1][0] - q[1][0][0]) * (q[1][1][1] - q[1][0][1]), -q[1][0][2]))
    contact = float(bhi[2])
    through = [(g, b) for g, b in boxes if g is not body and float(b[1][2]) > contact + EPS]
    if not through:
        return None
    m = inst.part.data.get("mount") or {}
    axis = m.get("hole_axis")
    if axis and axis in inst.datums:
        ax = pt.lookup_datum(inst.datums, axis).at
        axis_xy = (float(ax[0]), float(ax[1]))
    else:
        axis_xy = (float(np.mean([(b[0][0] + b[1][0]) / 2 for _, b in through])),
                   float(np.mean([(b[0][1] + b[1][1]) / 2 for _, b in through])))
    d = max(max(float(b[1][0] - b[0][0]), float(b[1][1] - b[0][1])) for _, b in through)
    lo_z = min(float(b[0][2]) for _, b in boxes)
    fp = (min(float(b[0][0]) for _, b in boxes), max(float(b[1][0]) for _, b in boxes),
          min(float(b[0][1]) for _, b in boxes), max(float(b[1][1]) for _, b in boxes))
    mp = m.get("max_panel_thickness")
    max_panel = float(inst.params[mp]) if isinstance(mp, str) and mp in inst.params else None
    return PanelGeometry(contact, d, axis_xy, contact - lo_z, fp, max_panel)


def panel_items(st: "A.AssemblyState") -> List[dict]:
    """The unplaced content items whose part is a panel part (the ones a panel decision can place)."""
    return [u for u in st.unplaced if is_panel_part(st.catalog.get(u["part"]))]


def panel_decisions(st: "A.AssemblyState") -> Dict[str, str]:
    return dict(st.control.get(PANEL) or {})


def cavity_z1_terms(st: "A.AssemblyState") -> List[str]:
    """derive_cavity's extra top bounds for parts hanging from the lid (a panel decision on the lid): the lid's inner
    face must sit their hanging depth above the primary's component keep-out (and every placed part) plus
    rules.part_to_wall. Empty without panel decisions, so other plans are unchanged."""
    out = []
    dec = panel_decisions(st)
    if not dec:
        return out
    _, _, top = A.primary_mount(st)
    refs = [n.id for n in st.graph.references()]
    floor = A._fold("max", [f"{A.PRIMARY}.{top}.z + spec.keepout_above"] + [f"{r}.bbox.max_z" for r in refs])
    for u in panel_items(st):
        if dec.get(u["id"]) != "lid":
            continue
        g = panel_geometry(st.catalog.instantiate(u["part"], {}))
        if g is not None:
            out.append(f"{floor} + rules.part_to_wall + {g.depth!r} + rules.design_margin")
    return out


def _node_rect(n: fg.Node, res: fg.Resolved) -> Tuple[float, float, float, float, float, float]:
    b = fg.solid(n, res).bounding_box()
    return float(b[0]), float(b[3]), float(b[1]), float(b[4]), float(b[2]), float(b[5])


def derive_panels(st: "A.AssemblyState") -> None:
    """Each panel decision (the controller's set_panel; Python places nothing on its own): every copy of the item is a
    reference part hanging from the lid with its contact plane on the lid's inner face, and a through hole in the lid
    of the part's through diameter + 2 x rules.sliding_fit. Positions: the first free spot (grid rules.layout_step,
    nearest the lid centre first) inside the lid lip (rules.sliding_fit + rules.lip_wall + rules.part_to_wall from the
    cavity walls), clear by rules.part_to_wall of every placed part, boss, pad, vent and port cut whose height reaches
    the hanging part. Raises ValueError when a copy finds no spot (the action is then infeasible)."""
    dec = panel_decisions(st)
    items = [u for u in panel_items(st) if dec.get(u["id"]) == "lid"]
    if not items:
        return
    r = st.rules.values
    res = A.resolve(st)
    cav, base = res.params["cavity"], res.params["base"]
    split = float(base["split"])
    ptw = r["part_to_wall"]
    m = (r["sliding_fit"] + r["lip_wall"] + ptw) if "lid_lip" in st.graph.nodes else ptw
    x0, x1, y0, y1 = cav["x0"] + m, cav["x1"] - m, cav["y0"] + m, cav["y1"] - m
    obstacles = []
    for n in st.graph:
        if n.kind == "reference" or (n.kind in ("add", "cut") and n.role in ("boss", "pad", "vent_cut", "port_cut",
                                                                            "port_roof")):
            obstacles.append(_node_rect(n, res))
    step = r["layout_step"]
    nx, ny = int(math.floor((x1 - x0) / step)), int(math.floor((y1 - y0) / step))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    grid = sorted(((x0 + i * step, y0 + j * step) for i in range(nx + 1) for j in range(ny + 1)),
                  key=lambda p: (round((p[0] - cx) ** 2 + (p[1] - cy) ** 2, 6), p[0], p[1]))
    for u in items:
        inst = st.catalog.instantiate(u["part"], {})
        g = panel_geometry(inst)
        if g is None:
            raise ValueError(f"panel {u['id']}: {u['part']} has no body and through part to mount in a panel")
        bottom = split - g.depth
        hw = ((g.footprint[0] - g.axis_xy[0]), (g.footprint[1] - g.axis_xy[0]),
              (g.footprint[2] - g.axis_xy[1]), (g.footprint[3] - g.axis_xy[1]))
        for k in range(int(u["quantity"])):
            spot = None
            for px, py in grid:
                rect = (px + hw[0] - ptw, px + hw[1] + ptw, py + hw[2] - ptw, py + hw[3] + ptw)
                if rect[0] < x0 or rect[1] > x1 or rect[2] < y0 or rect[3] > y1:
                    continue
                if any(o[0] < rect[1] and o[1] > rect[0] and o[2] < rect[3] and o[3] > rect[2] and o[5] > bottom - ptw
                       for o in obstacles):
                    continue
                spot = (px, py)
                break
            if spot is None:
                raise ValueError(f"panel {u['id']}: no free spot on the lid for copy {k + 1} of {u['quantity']}")
            nid = f"{u['id']}_{k + 1}"
            pose = fg.Pose(offset=(float(spot[0] - g.axis_xy[0]), float(spot[1] - g.axis_xy[1]),
                                   f"base.split - {g.contact_z!r}"))
            st.graph.add(fg.Node(nid, "reference", "part", dict(inst.params), pose, part=u["part"],
                                 source=f"{PANEL_SOURCE}(lid)", group=u["id"]))
            st.graph.add(fg.Node(f"{nid}_panel_hole", "cut", "cylinder", {
                "d": f"{g.through_d!r} + 2*rules.sliding_fit", "h": "lid.z + 2*rules.cut_overrun"},
                fg.Pose(offset=(float(spot[0]), float(spot[1]), "base.split - rules.cut_overrun")), body="lid",
                role="panel_hole", source=f"{PANEL_SOURCE}.hole"))
            obstacles.append((spot[0] + hw[0], spot[0] + hw[1], spot[1] + hw[2], spot[1] + hw[3], bottom, split))
            st.layout[nid] = {"part": u["part"], "params": dict(inst.params), "x": float(spot[0] - g.axis_xy[0]),
                              "y": float(spot[1] - g.axis_xy[1]), "z": float(split - g.contact_z), "rot_z": 0.0,
                              "item": u["id"], "copy": k, "role": "panel", "edge": "lid", "of": None}


def panel_refs(st: "A.AssemblyState") -> List[fg.Node]:
    return [n for n in st.graph if n.kind == "reference" and str(n.source).startswith(PANEL_SOURCE)]


def panel_placed(st: "A.AssemblyState", item: str) -> bool:
    return any(n.group == item for n in panel_refs(st))


def _cube(lo, hi):
    return ac.m3d.Manifold.cube([float(hi[i] - lo[i]) for i in range(3)]).translate([float(v) for v in lo])


def add_panel_checks(st: "A.AssemblyState", plan: ac.Plan) -> None:
    """The panel parts' sensors (each copy): panel_keepouts_<copy> (the part's keep-outs above its contact plane: a nut
    on the bushing, a lever's swing, a lens's view, clear of every printed body, measured), panel_clear_<copy> (the part
    at least rules.part_to_wall from every printed body except its designed contact: the body's top face on the lid and
    the through part in its hole), panel_board_<copy> (the part clear of the primary by rules.part_to_wall), panel_seated
    _<copy> (measured: the lid's inner face meets the contact plane), panel_hole_<copy> (measured on the built lid since
    review fix 3: the hole's clearance per side within the sliding-fit band) and panel_thickness_<copy> (design check:
    the resolved lid thickness at most the part's max_panel_thickness, when it declares one)."""
    r, res = st.rules.values, st.resolved
    for n in panel_refs(st):
        inst = st.catalog.instantiate(n.part, dict(n.params))
        g = panel_geometry(inst)
        pose = res.poses[n.id]
        name = A.human_name(st.catalog, n.part)
        kos = [world_box(k, pose, k.id, True) for k in inst.keepouts if float(k.bbox()[0][2]) >= g.contact_z - EPS]
        if kos:
            vol = f"{n.id}_keepouts"
            plan.volumes[vol] = ac.union([_cube(b.lo, b.hi) for b in kos])
            plan.sources[vol] = [n.id]
            plan.add(f"panel_keepouts_{n.id}", "clear_of", f"the {name}'s keep-outs above the panel "
                     f"({', '.join(b.what for b in kos)}) are clear of every printed body", volume=vol, clearance=0.0,
                     parts=[n.part])
        ref = f"{n.id}_ref"
        plan.volumes[ref] = fg.solid(n, res)
        plan.sources[ref] = [n.id]
        hole = res.params[f"{n.id}_panel_hole"]
        hp = res.poses[f"{n.id}_panel_hole"][:3, 3]
        c = r["part_to_wall"]
        lid_top = float(res.params["base"]["split"] + res.params["lid"]["z"])
        contact_z = float(pose[2, 3] + g.contact_z)
        corners = np.array([[x, y, 0.0] for x in g.footprint[:2] for y in g.footprint[2:]]) @ pose[:3, :3].T + pose[:3, 3]
        fp = Box3(corners.min(axis=0), corners.max(axis=0))
        contact = ac.union([
            ac.m3d.Manifold.cylinder(lid_top - contact_z + 2 * c + r["cut_overrun"], hole["d"] / 2 + c, hole["d"] / 2 + c,
                                     plan.seg).translate([float(hp[0]), float(hp[1]), contact_z - c]),
            _cube([fp.lo[0] - c, fp.lo[1] - c, contact_z - 2 * c], [fp.hi[0] + c, fp.hi[1] + c, contact_z + c])])
        minus = f"{n.id}_contact"
        plan.volumes[minus] = contact
        plan.volumes[f"{minus}@{c:g}"] = contact        # built grown by the clearance already (grow_exemptions keeps it)
        plan.sources[minus] = []
        plan.sources[f"{minus}@{c:g}"] = []
        plan.add(f"panel_clear_{n.id}", "clear_of", f"the {name} is at least {c:g} mm from every printed body except "
                 "its body's face on the lid and its through part in the hole", volume=ref, clearance=c, minus=minus,
                 parts=[n.part])
        plan.add(f"panel_board_{n.id}", "clear_of", f"the {name} is at least {c:g} mm from the primary part",
                 subject=ref, volume="board", clearance=c, parts=[n.part])
        plan.add(f"panel_seated_{n.id}", "panel_seated", f"the {name}'s body stops against the lid's inner face (gap <= "
                 f"{r['seat_gap_max']:g} mm)", body="lid", contact_z=contact_z,
                 probe=[float(hp[0]) + (hole["d"] / 2 + (fp.hi[0] - float(hp[0]))) / 2, float(hp[1])],
                 d=r["min_feature"], gap_max=r["seat_gap_max"], parts=[n.part])
        # review fix 3: measured on the built lid (solids or the delivered STL), not the designed diameter: the lid's
        # cross-section at mid-thickness around the part's axis, the nearest lid edge to the axis minus the through
        # part's radius (designed value kept for the record)
        split = float(res.params["base"]["split"])
        plan.add(f"panel_hole_{n.id}", "panel_hole", f"the hole for the {name} is {r['sliding_fit_min']:g}-"
                 f"{r['sliding_fit_max']:g} mm bigger than its through part per side", body="lid",
                 xy=[float(hp[0]), float(hp[1])], z=split + float(res.params["lid"]["z"]) / 2,
                 z0=split, z1=lid_top, through_d=float(g.through_d),
                 window=float(hole["d"]) / 2 + r["sliding_fit_max"] + c, lo=r["sliding_fit_min"],
                 hi=r["sliding_fit_max"], designed=(float(hole["d"]) - g.through_d) / 2, parts=[n.part])
        if g.max_panel is not None:
            t = float(res.params["lid"]["z"])
            plan.add(f"panel_thickness_{n.id}", "panel_thickness", f"the lid is at most the {name}'s "
                     f"{g.max_panel:g} mm panel thickness", value=t, limit=g.max_panel,
                     detail=f"lid {t:.3f} mm vs max_panel_thickness {g.max_panel:g}", parts=[n.part])


def panel_hole_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured (review fix 3): the lid body's cross-section at mid-thickness inside a window around the part's axis;
    the clearance per side is the distance from the axis to the nearest lid edge minus the through part's radius (a
    faceted hole measures its flats). No lid material in the window: the hole is at least the window (too big); the
    axis inside lid material: no hole (negative clearance)."""
    lid = bodies[a["body"]]
    cx, cy, w = float(a["xy"][0]), float(a["xy"][1]), float(a["window"])
    win = lid ^ _cube([cx - w, cy - w, a["z0"]], [cx + w, cy + w, a["z1"]])
    rt = a["through_d"] / 2
    rings = [] if win.is_empty() else [np.asarray(q, float) for q in win.slice(float(a["z"])).to_polygons()
                                       if len(q) >= 2]
    if not rings:
        dist, inside = w, False
    else:
        pt_ = np.array([cx, cy])
        dist, crossings = math.inf, 0
        for ring in rings:
            p0, p1 = ring, np.roll(ring, -1, axis=0)
            seg = p1 - p0
            t = np.clip(np.einsum("ij,ij->i", pt_ - p0, seg) / np.maximum(np.einsum("ij,ij->i", seg, seg), EPS), 0, 1)
            dist = min(dist, float(np.min(np.linalg.norm(p0 + seg * t[:, None] - pt_, axis=1))))
            up = (p0[:, 1] > cy) != (p1[:, 1] > cy)           # even-odd ray cast toward +x
            xs = p0[up, 0] + (cy - p0[up, 1]) * seg[up, 0] / seg[up, 1]
            crossings += int(np.sum(xs > cx))
        inside = crossings % 2 == 1
    per_side = -(dist + rt) if inside else dist - rt
    res = ac.value_in_band(cid, typ, per_side, a["lo"], a["hi"], plan.tol,
                           f"measured on the lid: nearest edge {dist:.3f} mm from the axis"
                           + (" (the axis is inside lid material: no hole)" if inside else "")
                           + f", {per_side:.3f} per side for Ø{a['through_d']:g} (designed {a['designed']:.3f})")
    res.evidence["basis"] = MEASURED
    return res


def panel_seated_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the lowest point of the lid in a thin column on the part's contact face, against the contact plane."""
    lid = bodies[a["body"]]
    col = ac._column(a["probe"], a["d"], a["contact_z"] - 1.0, a["contact_z"] + 1.0, plan.seg)
    inter = lid ^ col
    if inter.is_empty():
        return ac._result(cid, typ, False, -1.0, "mm", {"detail": "no lid material over the part's contact face",
                                                        "basis": MEASURED})
    low = float(inter.bounding_box()[2])
    gap = abs(low - a["contact_z"])
    return ac._result(cid, typ, gap <= a["gap_max"] + plan.tol.measure,
                      (a["gap_max"] - gap + plan.tol.measure) / plan.tol.scale, "mm",
                      {"value": round(gap, 6), "detail": f"lid underside {low:.3f} vs contact plane "
                                                         f"{a['contact_z']:.3f} (gap {gap:.4f}, max {a['gap_max']:g})",
                       "basis": MEASURED})


def panel_actions(st: "A.AssemblyState", r: cc.CheckResult) -> list:
    """A failing content_placed check of a panel part: one set_panel action per panel face the plant derives (the lid);
    validated by application (a face with no free spot makes the action infeasible)."""
    import controller as C
    ev = r.evidence or {}
    item = ev.get("item")
    u = next((x for x in panel_items(st) if x["id"] == item), None)
    if u is None or panel_geometry(st.catalog.instantiate(u["part"], {})) is None:
        return []
    name = A.human_name(st.catalog, u["part"])
    # merged with R02 (R11): keyword construction against R02's Action (kind, target, value, words, targets,
    # invalidates, evidence, ident); the menu shows Action.desc (the words after the first ": "), so the words lead
    # with "<kind> <target>=<value>: " and the description keeps the part's name and the face
    return [C.Action(kind=SET_PANEL, target=item, value=face,
                     words=f"{SET_PANEL} {item}={face}: mount {item} ({name} x{u['quantity']}) {words}: its bushing or "
                           "lens passes through a hole, its body stops against the inside face",
                     targets=[r.check_id], invalidates="derive", evidence=[])
            for face, words in PANEL_FACES.items() if panel_decisions(st).get(item) != face]


def apply_panel(st: "A.AssemblyState", action, record: Mapping[str, Any], by: str = "llm:controller") -> None:
    """R02's applier signature (state, action, record, by): `by` is llm:controller or search:controller."""
    dec = dict(st.control.get(PANEL) or {})
    dec[action.target] = action.value
    st.control[PANEL] = dec
    A.choice(st, f"panel[{action.target}]", action.value, by, **dict(record))


# ---------------------------------------------------------------------------
# Controller registration (controller.py reads these; the Action class is controller.py's)
# ---------------------------------------------------------------------------

DIRECTIONS: Dict[str, Tuple[str, str]] = {
    RETENTION: ("free travel of the part in its worst direction", "decrease"),
    "supported": ("support gap under the part's ledges", "decrease"),
    "rib_interference": ("crush rib interference", "band"),
    "snap_strain": ("snap arm bending strain", "decrease"),
    "snap_overlap": ("snap hook overlap over the part", "increase"),
    "panel_seated": ("gap between the part's body and the panel's inner face", "decrease"),
    "panel_hole": ("panel hole clearance per side", "band"),
    "panel_thickness": ("panel thickness at the part", "decrease"),
}


def retention_actions(st: "A.AssemblyState", r: cc.CheckResult) -> list:
    """A failing retention check: one `set_retention` action per retention option the plant can build here other than
    the current one (Python validated each by deriving its cradle; the infeasible ones are named in the check's
    detail)."""
    import controller as C
    current = (r.evidence or {}).get("option") or retention_choice(st)["value"]
    item = A.primary_item(st) or {}
    name = A.human_name(st.catalog, item.get("part")) if item.get("part") else A.PRIMARY
    out = []
    for o in retention_options(st):
        if o["name"] == current or not o["feasible"]:
            continue
        out.append(C.Action(kind=SET_RETENTION, target=A.PRIMARY, value=o["name"],     # R11: keyword form, see above
                            words=f"{SET_RETENTION} {A.PRIMARY}={o['name']}: hold the {name} with {o['name']}: "
                                  f"{o['meaning']}",
                            targets=[r.check_id], invalidates="derive", evidence=[]))
    return out


def apply_retention(st: "A.AssemblyState", action, record: Mapping[str, Any], by: str = "llm:controller") -> None:
    """R02's applier signature (state, action, record, by)."""
    st.control[RETENTION] = action.value
    A.choice(st, RETENTION_CHOICE.format(item=action.target), action.value, by, **dict(record))


ACTUATORS: Dict[str, Callable] = {RETENTION: retention_actions, "content_placed": panel_actions}
APPLIERS: Dict[str, Callable] = {SET_RETENTION: apply_retention, SET_PANEL: apply_panel}


def state_lines(st: "A.AssemblyState") -> List[str]:
    """The design-state words the controller reads for these blocks (one line per decided block)."""
    out = []
    key = RETENTION_CHOICE.format(item=A.PRIMARY)
    if key in st.choices:
        out.append(f"- {A.PRIMARY} retention: {st.choices[key].get('value')}")
    for item, face in sorted(panel_decisions(st).items()):
        out.append(f"- {item}: mounted {face} ({'placed' if panel_placed(st, item) else 'not placed'})")
    return out


def decisions(st: "A.AssemblyState") -> Dict[str, Any]:
    """The blocks' discrete decisions for the controller's state digest."""
    key = RETENTION_CHOICE.format(item=A.PRIMARY)
    out = {"retention": (st.choices.get(key) or {}).get("value")} if key in st.choices else {}
    if panel_decisions(st):
        out["panel"] = panel_decisions(st)
    return out


EXTRA_CHECKS.update({"panel_seated": panel_seated_check, "panel_hole": panel_hole_check,
                     "panel_thickness": _value("at_most")})
ac.EXTRA_CHECKS.update(EXTRA_CHECKS)     # the sensors run in assembly_checks.run_plan (on solids and on the STLs)
