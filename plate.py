"""The plate archetype: a printed plate or platform that catalogue parts bolt to face-on (migration delta R12; owner
decision D1; loop/ARCHITECTURE.md 4 and 10.8).

Generic and catalogue-driven, the plate is three things, as every building block (building_blocks.py):

* a **plant** (`derive_plate`): the part with a `bolt_face` interface (the primary) bears on the plate through its
  `face`; a reference part it `engage`s (a clip-in part in its holder) is placed by the engage datums and the plate's underside
  lies on that reference's mating plane; the fastener chain is chosen from catalogue data (bolts whose thread is the
  interface's and whose head fits the part's head seat, nuts of that thread, stock lengths); the bolts pass through
  slots (when the part declares an adjustment range, raised to a mapped adjust_min / adjust_cross_min: the slots and hex
  nut channels run along the largest range, since a hex trap only stops the nut turning while it slides one way) into
  captive nut channels, or a nut frame with its own floor that bears on the plate beside the slots; the part's own engage
  keep-outs (a recess round it) are cut, swept over its adjustment range; the outline is sized from the cuts plus
  rules.plate_wall_min and the request's mapped size band, and placed (a grid search) so it clears the engaged
  reference's keep-outs swept over the adjustment range and any catalogue `sweep` (a release twist); the thickness is the
  largest of the fastener stack, the mapped minimum and, when the request states a load case, the bending stress Python
  measures on the built section (never the LLM); the print orientation is the flat face with the least overhang;
* **typed actions** the controller chooses (`add_surface_feature` over the building_blocks.surface_feature options the
  plant can build: catalogue studs in tapped holes or printed pins; `set_handedness` mirror_pair when a reference part is
  used in mirror pairs): Python lays the features out and sizes them within the mapped bands, it never adds one itself;
* **sensors**, measured on the solids and on the delivered STLs where they can be (evidence `basis`): clearance to every
  reference keep-out (swept; the mapped clearance less the margin a keep-out already holds), the bolt travel over each
  required adjustment axis, fastener engagement and tip cover, nut-trap fit (measured across the channel at each nut),
  the clamp path (review fix B1: every nut, head, nut frame and bolted face bears on printed material round its bolt
  axis at every adjustment extreme), plan size and thickness bands, the bearing area on the engaged part, the bending
  stress of a stated load case at the support edge in the worst adjustment position with a 45-degree effective width
  (review fixes B2, N1; a section of the delivered mesh), printability (no overhang steeper than
  rules.overhang_angle_deg and no bridge longer than rules.bridge_max in the declared orientation), thin features
  (review fix N5), stud thread engagement in printed material, the surface features against the mapped count / height /
  edge / spread, the mirror image on the mirrored reference, and the bed.

Python never reads the request to pick any of this: each choice above is catalogue data, a design_rules.json value, a
number the controller mapped (ParseSpec slots) or the controller's action. Nothing here holds a number, part or face of
one request (test_no_hardcoding.py scans this module); every rule:* decision string is registered in
controller_rules.json (test_controller_authority.py).
"""

from __future__ import annotations

import itertools
import math
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

import assembly as A            # circular on purpose: only module attributes are read, at call time
import assembly_checks as ac
import cad_checks as cc
import feature_graph as fg
import parts as pt

BODY = "plate"                           # the printed body's node id (its STL is plate.stl)
SURFACE = "surface_feature"              # building_blocks vocabulary + st.control key
HANDEDNESS = "handedness"
RETENTION = "nut_retention"              # building_blocks vocabulary + st.control key: channel | frame
SET_RETENTION = "set_nut_retention"
FRAME = "nut_frame"                      # the frame option's printed body (its STL is nut_frame.stl)
SET_SURFACE = "add_surface_feature"
SET_HANDEDNESS = "set_handedness"
FACE_TOP = "top"                         # the plate's free face (the target of add_surface_feature)
MEASURED, DESIGN = "measured", "design"
EPS = 1e-6
ARC_SEGMENTS = 16                        # segments per half circle of a slot end (circumscribed: never undersize)
ORIENTATIONS = ("contact_face_down", "top_face_down")
AXIS_NAMES = ("x", "y", "z")


# ---------------------------------------------------------------------------
# Catalogue reading: the anchor part, its engaged reference, the fastener chain
# ---------------------------------------------------------------------------


def anchor(st: "A.AssemblyState") -> Tuple[Optional[dict], Optional[dict], str]:
    """(primary item, its bolt_face interface, reason) — the plate is anchored on the primary's bolt_face."""
    prim = A.primary_item(st)
    if prim is None:
        return None, None, "no primary part"
    bf = pt.bolt_face_interface(st.catalog.get(prim["part"]))
    if bf is None:
        return prim, None, f"the primary {prim['part']} offers no {pt.BOLT_FACE} interface (a face that bolts flat " \
                           "against a printed plate)"
    return prim, bf, ""


def chain_parts(st: "A.AssemblyState", inst: pt.PartInstance, bf: Mapping[str, Any]) -> Tuple[Optional[dict], str]:
    """The catalogue fastener chain for the interface (a guardrail on fit, rule:plate_fastener for the pick):
    bolt-through when the interface has a head_seat (a bolt whose thread is the interface's thread, or passes the hole,
    whose head fits the hole's keep-out circle, with stock lengths; and a nut of that thread). Returns (chain, reason)."""
    holes = inst.datums[bf["holes"]]
    thread = bf.get("thread") or holes.diameter
    into = "head_seat" not in bf and "thread_depth" in bf      # screws from the plate's free face into tapped holes
    if "head_seat" not in bf and not into:
        return None, "the interface declares neither a head seat nor a thread depth"
    tol = float(st.rules.values["measure_tol"])
    bolts, nuts = [], []
    for pid in st.catalog.ids():
        p = st.catalog.get(pid)
        role = pt.fastener_role(p)
        if role not in ("bolt", "nut"):
            continue
        d = {k: float(v.get("default")) for k, v in p.params.items() if v.get("default") is not None}
        if abs(d.get("thread_diameter", -1) - float(thread)) > tol:
            continue
        if holes.diameter is not None and d["thread_diameter"] > holes.diameter + tol:
            continue
        if role == "bolt":
            if not into and holes.keepout_diameter is not None and d["head_diameter"] > holes.keepout_diameter + tol:
                continue
            if not pt.stock_lengths(p):
                continue
            bolts.append((d["head_diameter"], pid, d))
        else:
            nuts.append((pid, d))
    if not bolts:
        return None, f"no catalogue bolt of thread {float(thread):g} mm with a head that fits the hole keep-out and " \
                     "stock lengths"
    if into:
        head, bolt, bd = max(bolts, key=lambda b: (b[0], [-ord(c) for c in b[1]]))
        return {"kind": "screw_into", "bolt": bolt, "nut": None, "bolt_params": bd, "nut_params": {},
                "lengths": pt.stock_lengths(st.catalog.get(bolt)), "thread": float(thread),
                "depth": float(fg.evaluate(bf["thread_depth"], inst.env))}, ""
    if not nuts:
        return None, f"no catalogue nut of thread {float(thread):g} mm"
    head, bolt, bd = max(bolts, key=lambda b: (b[0], [-ord(c) for c in b[1]]))   # the largest head that fits
    nut, nd = nuts[0]
    return {"kind": "bolt_through", "bolt": bolt, "nut": nut, "bolt_params": bd, "nut_params": nd,
            "lengths": pt.stock_lengths(st.catalog.get(bolt)), "thread": float(thread)}, ""


def feasibility(st: "A.AssemblyState") -> Tuple[bool, str]:
    """Plant feasibility of the plate for the chosen contents (catalogue data only, forms.catalogue_options)."""
    prim, bf, why = anchor(st)
    if bf is None:
        return False, why
    try:
        inst = st.catalog.instantiate(prim["part"], prim.get("params") or {})
    except (pt.PartError, fg.ExprError, fg.MissingRefError, KeyError, ValueError) as e:
        return False, f"the primary cannot be instantiated ({e})"
    face = inst.datums[bf["face"]]
    if abs(float(face.normal[2])) < 1 - EPS:
        return False, "the bolted face is not horizontal in the part frame (a tilted plate is not built yet)"
    if float(face.normal[2]) < 0:
        return False, "the bolted face looks down (a plate under the part is not built yet)"
    chain, why = chain_parts(st, inst, bf)
    if chain is None:
        return False, why
    return True, ""


def places(st: "A.AssemblyState", part_id: str) -> bool:
    """The plate places this catalogue part: the primary engages it (its engage interface `mates` it)."""
    prim = A.primary_item(st)
    eng = pt.engage_interface(st.catalog.get(prim["part"])) if prim else None
    return bool(eng and eng.get("mates") == part_id)


# ---------------------------------------------------------------------------
# Small geometry helpers (numbers only; the nodes carry numbers, no expressions)
# ---------------------------------------------------------------------------


def _world(d, pose: np.ndarray):
    return pt.transform(d, pose)


def _solid_of(prim: pt.Primitive, seg: int):
    if prim.primitive == "box":
        return ac.m3d.Manifold.cube(list(prim.size)).translate(list(prim.at))
    return fg._cyl(prim.d, prim.h, seg).transform(fg._m3(fg.matrix(fg.align_z_to(prim.dir), prim.at)))


def _rot_about(axis: np.ndarray, pivot: np.ndarray, deg: float, shift: np.ndarray) -> np.ndarray:
    """4x4: rotate by deg about the axis through pivot, then translate by shift."""
    a = math.radians(deg)
    k = np.asarray(axis, float) / np.linalg.norm(axis)
    kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    r = np.eye(3) + math.sin(a) * kx + (1 - math.cos(a)) * kx @ kx
    m = np.eye(4)
    m[:3, :3] = r
    m[:3, 3] = pivot - r @ pivot + shift
    return m


def _union(solids):
    return ac.union(list(solids))


def _shifts(adjust: Sequence[Tuple[np.ndarray, float]]) -> List[np.ndarray]:
    """Every combination of -range/2, 0, +range/2 along the adjustment axes (the reference relative to the plate)."""
    rows = [[-r / 2, 0.0, r / 2] if r > EPS else [0.0] for _, r in adjust] or [[0.0]]
    out = []
    for combo in itertools.product(*rows):
        s = np.zeros(3)
        for (d, _), c in zip(adjust, combo):
            s = s + d * c
        out.append(s)
    return out


def _angles(total: float, step: float) -> List[float]:
    if total <= EPS:
        return [0.0]
    n = max(1, int(math.ceil(2 * total / max(step, EPS))))
    return [float(-total + 2 * total * k / n) for k in range(n + 1)]


def stadium(length: float, width: float, seg: int = ARC_SEGMENTS) -> List[Tuple[float, float]]:
    """A slot outline along local +X centred on the origin: straight length `length` between the two arc centres,
    width `width`; the arc vertices are circumscribed (the slot is never narrower than `width`)."""
    r = width / 2 / math.cos(math.pi / (2 * seg))
    pts = []
    for k in range(seg + 1):
        a = -math.pi / 2 + math.pi * k / seg
        pts.append((length / 2 + r * math.cos(a), r * math.sin(a)))
    for k in range(seg + 1):
        a = math.pi / 2 + math.pi * k / seg
        pts.append((-length / 2 + r * math.cos(a), r * math.sin(a)))
    return pts


def hex_channel(length: float, flats: float) -> List[Tuple[float, float]]:
    """A hex nut channel along local +X centred on the origin: two flats parallel to X `flats` apart (the nut cannot
    turn), pointed ends, sliding range `length` between the two end positions of the nut's axis."""
    corners = flats / math.cos(math.radians(30.0))
    h, q = flats / 2, corners / 4
    return [(-length / 2 - corners / 2, 0.0), (-length / 2 - q, -h), (length / 2 + q, -h), (length / 2 + corners / 2, 0.0),
            (length / 2 + q, h), (-length / 2 - q, h)]


def prism_params(poly: Sequence[Tuple[float, float]], h: float) -> Dict[str, float]:
    p: Dict[str, float] = {"n": float(len(poly)), "h": float(h)}
    for k, (x, y) in enumerate(poly, 1):
        p[f"x{k}"], p[f"y{k}"] = float(x), float(y)
    return p


def _poly_world(poly, centre, angle_deg: float) -> List[Tuple[float, float]]:
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return [(centre[0] + c * x - s * y, centre[1] + s * x + c * y) for x, y in poly]


def setpoint_min(st, v: Optional[float]) -> Optional[float]:
    return None if v is None else float(v) + float(st.rules.values["design_margin"])


def setpoint_max(st, v: Optional[float]) -> Optional[float]:
    return None if v is None else float(v) - float(st.rules.values["design_margin"])


def band_setpoints(st, lo_name: str, hi_name: str) -> Tuple[Optional[float], Optional[float]]:
    """The derivation targets of a mapped lo/hi band: each end moved inside by rules.design_margin (setpoint_min /
    setpoint_max), except a band narrower than twice the margin (one stated value set both ends, R12 review 2 N6):
    both targets are its centre, so the setpoints never cross. The checks keep the stated limits."""
    lo, hi = spec(st, lo_name), spec(st, hi_name)
    if lo is not None and hi is not None and hi - lo < 2 * float(st.rules.values["design_margin"]) - EPS:
        c = (lo + hi) / 2
        return c, c
    return setpoint_min(st, lo), setpoint_max(st, hi)


def limit_words(st, name: str, target: Optional[float]) -> str:
    """A band end as the derivation compared it (R12 review 2 N5): the stated limit and, when it differs, the setpoint
    the plant aimed at (the limit less rules.design_margin)."""
    v = spec(st, name)
    if v is None or target is None or abs(target - v) < EPS:
        return f"{name} {v:g}" if v is not None else name
    return f"the {name} setpoint {target:.2f} ({name} {v:g} less the design margin)"


def spec(st, name: str) -> Optional[float]:
    v = st.spec.get(name)
    return None if v is None else float(v)


def ceil_to(x: float, step: float) -> float:
    return math.ceil(x / step - 1e-9) * step if step > 0 else x


# ---------------------------------------------------------------------------
# The plant
# ---------------------------------------------------------------------------


def control(st: "A.AssemblyState", key: str) -> str:
    """The controller's option for a plate vocabulary, else the vocabulary's default (rule:default_<key>, plant)."""
    opts = dict(((st.rules.building_blocks or {}).get(key) or {}).get("options") or {})
    value = st.control.get(key)
    if value in opts:
        return value
    return next(k for k, v in opts.items() if v.get("default"))


def surface_options(st: "A.AssemblyState") -> List[dict]:
    """The surface-feature options with their plant feasibility (studs need a catalogue stud fastener)."""
    opts = dict(((st.rules.building_blocks or {}).get(SURFACE) or {}).get("options") or {})
    out = []
    for name, o in opts.items():
        ok, why = True, ""
        if o.get("needs") == "stud" and stud_part(st) is None:
            ok, why = False, "no catalogue set screw with a tap drill and stock lengths"
        out.append({"name": name, "meaning": o.get("meaning", name), "feasible": ok, "reason": why,
                    "default": bool(o.get("default"))})
    return out


def stud_part(st: "A.AssemblyState") -> Optional[str]:
    """The catalogue stud (a set screw: thread, tap drill, request-sized length, stock lengths); the smallest thread."""
    cands = []
    for pid in st.catalog.ids():
        p = st.catalog.get(pid)
        if pt.fastener_role(p) == "stud" and pt.stock_lengths(p):
            cands.append((float(p.params["thread_diameter"]["default"]), pid))
    return min(cands)[1] if cands else None


def derive_plate(st: "A.AssemblyState") -> Optional[str]:
    """DeriveFeatures for the plate archetype (shared with forms.trial and the controller's re-runs). Returns None or
    the typed failure. Writes st.plate (the derived numbers the sensors and the state words read) and the graph."""
    try:
        return _derive(st)
    except (ValueError, KeyError, fg.ExprError, pt.PartError) as e:
        return f"plate derivation failed: {e}"


def _derive(st: "A.AssemblyState") -> Optional[str]:
    r = st.rules.values
    seg = int(r.get("fn", fg.DEFAULT_SEGMENTS))
    tol, margin = float(r["measure_tol"]), float(r["design_margin"])
    prim, bf, why = anchor(st)
    if bf is None:
        return why
    placed = st.placed.get(A.PRIMARY)
    inst, pose = placed.inst, np.asarray(placed.pose, float)
    chain, why = chain_parts(st, inst, bf)
    if chain is None:
        return why
    holes = _world(inst.datums[bf["holes"]], pose)
    face = _world(inst.datums[bf["face"]], pose)
    seat = _world(inst.datums[bf["head_seat"]], pose) if "head_seat" in bf else None
    up = np.asarray(face.normal, float)
    if up[2] < 1 - EPS:
        return "the bolted face is not horizontal and facing up"
    z_face = float(face.at[2])
    rot = pose[:3, :3]
    declared = [(rot @ d, rng) for d, rng in pt.adjust_axes(inst, bf)]
    adjust = required_adjust(st, declared, rot)
    notes, conflicts = [], []
    # --- the graph keeps the references only (the shell's envelopes belong to the shell)
    st.graph = fg.FeatureGraph([n for n in st.graph if n.kind == "reference"])
    # --- the engaged reference part (rule:engage_pose)
    eng = pt.engage_interface(inst.part)
    z_bot = z_face
    mate = None
    if eng is not None:
        item = next((c for c in st.contents if c.get("part") == eng["mates"] and c.get("id") != A.PRIMARY), None)
        plane = _world(inst.datums[eng["plane"]], pose)
        z_bot = min(z_face, float(plane.at[2]))
        if item is not None:
            mate = place_mate(st, item, eng, inst, pose)
            if isinstance(mate, str):
                return mate
    # --- the fastener chain: nut floor, nut top, stock length, tip (a screw into a tapped part: its length per thickness)
    nd, bd = chain["nut_params"], chain["bolt_params"]
    into = chain["kind"] == "screw_into"
    z_pocket = None
    if into:
        z_nut = nut_top = seat_z = tip = None
        length = None
        # the thinnest plate (at least rules.plate_wall_min) through which some stock screw engages the tapped hole by
        # rules.tapped_engagement_ratio diameters without bottoming in its thread depth
        t0 = float(r["plate_wall_min"]) + margin
        need_e = float(r["tapped_engagement_ratio"]) * bd["thread_diameter"]
        fits = [max(t0, L - (chain["depth"] - margin)) for L in chain["lengths"]
                if max(t0, L - (chain["depth"] - margin)) <= L - need_e + EPS]
        z_top_need = z_face + (min(fits) if fits else t0)
    else:
        # review fix B1: with the nut frame the nut bears on the frame's own floor (rules.plate_floor_min, a clearance
        # hole for the bolt) and the frame bears on the plate's pocket floor beside the slots
        floor = float(r["plate_floor_min"]) + margin
        z_pocket = z_face + floor
        frame_floor = floor if control(st, RETENTION) == "frame" and len(holes.at) >= 2 else 0.0
        z_nut = z_pocket + frame_floor
        nut_top = z_nut + nd["thickness"]
        seat_z = float(seat.at[2])
        need = nut_top - seat_z
        length = next((L for L in chain["lengths"] if L >= need - tol), None)
        if length is None:
            return f"no stock length of {chain['bolt']} reaches through the nut ({need:.2f} mm needed)"
        tip = seat_z + length
        z_top_need = tip + float(r["bolt_tip_cover"])
    # --- adjustment covered by the slots: the largest declared range (a hex trap holds the nut along one direction)
    slide = max(adjust, key=lambda a: a[1]) if adjust and max(a[1] for a in adjust) > EPS else (np.array([1.0, 0, 0]), 0.0)
    u, R_u = slide[0] / np.linalg.norm(slide[0]), float(slide[1])
    ang_u = math.degrees(math.atan2(u[1], u[0]))
    covered = {i: (R_u if abs(abs(float(np.dot(d, u))) - 1) < EPS else 0.0) for i, (d, _) in enumerate(adjust)}
    # --- cuts in plan (footprints) and the core the outline must hold
    flats = 0.0 if into else nd["across_flats"] + 2 * float(nd.get("trap_clearance", r["nut_trap_clearance_min"]))
    clear_d = bd["clearance_diameter"]
    retention = control(st, RETENTION)
    cuts: List[dict] = []
    frame = None
    if into:                                  # no nut: a slot over every declared range (rounded rectangle)
        v = np.cross([0.0, 0.0, 1.0], u)
        R_v = max([abs(float(np.dot(d, v))) * rng for d, rng in adjust] + [0.0])
        covered = {i: rng for i, (_, rng) in enumerate(adjust)}
        retention = None
        for k, p in enumerate(holes.at):
            c = (float(p[0]), float(p[1]))
            slot = rounded_rect(R_u, R_v, clear_d)
            cuts.append({"id": f"slot_{k}", "poly": _poly_world(slot, c, ang_u), "local": slot, "centre": c,
                         "angle": ang_u, "z0": z_bot - float(r["cut_overrun"]), "z1": None, "role": "bolt_slot"})
    elif retention == "frame":                # a printed frame holds every nut; it slides in a pocket (rule:nut_frame)
        if len(holes.at) < 2:
            return "nut_retention frame: a frame holding one nut could turn; it needs two or more holes"
        v = np.cross([0.0, 0.0, 1.0], u)
        R_v = max([abs(float(np.dot(d, v))) * rng for d, rng in adjust] + [0.0])
        covered = {i: rng for i, (_, rng) in enumerate(adjust)}
        frame, cuts = frame_layout(st, holes, u, v, R_u, R_v, ang_u, flats, clear_d, z_bot, z_pocket, z_nut,
                                   nd["thickness"])
    else:
        for k, p in enumerate(holes.at):
            c = (float(p[0]), float(p[1]))
            cuts.append({"id": f"slot_{k}", "poly": _poly_world(stadium(R_u, clear_d), c, ang_u),
                         "local": stadium(R_u, clear_d), "centre": c, "angle": ang_u,
                         "z0": z_bot - float(r["cut_overrun"]), "z1": z_nut + float(r["cut_overrun"]), "role": "bolt_slot"})
            cuts.append({"id": f"nut_channel_{k}", "poly": _poly_world(hex_channel(R_u, flats), c, ang_u),
                         "local": hex_channel(R_u, flats), "centre": c, "angle": ang_u, "z0": z_nut, "z1": None,
                         "role": "nut_channel"})
    shifts = _shifts(adjust)
    recess = []                               # the primary's own engage keep-outs, swept over its adjustment range
    for kid in (eng or {}).get("keepouts", []) or []:
        ko = next(k for k in inst.keepouts if k.id == kid)
        lo, hi = _world_box(ko, pose)
        grow = np.sum([np.abs(d) * rng / 2 for d, rng in adjust], axis=0) if adjust else np.zeros(3)
        lo2, hi2 = lo - grow, hi + grow
        z0 = lo2[2] - float(r["cut_overrun"]) if lo2[2] <= z_bot + tol else lo2[2]
        row = {"id": f"recess_{kid}", "lo": lo2, "hi": hi2, "z0": z0, "z1": min(hi2[2], z_face) if hi2[2] >= z_face - tol
               else hi2[2], "keepout": kid}
        hull = swept_plan(ko, pose, shifts)
        if hull is not None:              # a part-shaped seat: the keep-out's own plan swept over the adjustment only
            row["poly"] = hull
        recess.append(row)
    own = []                                  # the primary's geometry above its face (a pilot boss, a shaft) + clearance
    for g in inst.geometry:
        lo, hi = _world_box(g, pose)
        if hi[2] > z_face + tol:
            c = float(r["part_to_wall"])
            grow = np.sum([np.abs(d) * rng / 2 for d, rng in adjust], axis=0) if adjust else np.zeros(3)
            row = {"id": f"clear_{g.id}", "lo": lo - grow - [c, c, 0], "hi": hi + grow + [c, c, 0]}
            gd = None if g.dir is None else rot @ np.asarray(g.dir, float)
            if g.primitive == "cylinder" and not np.any(grow) and abs(abs(float(gd[2])) - 1) < EPS:
                row.update(cyl=True, xy=[float((lo[0] + hi[0]) / 2), float((lo[1] + hi[1]) / 2)], d=float(g.d) + 2 * c)
            own.append(row)
    from shapely.geometry import Polygon, box as sbox
    from shapely.ops import unary_union
    foot = [Polygon(c["poly"]) for c in cuts if c.get("body", BODY) == BODY] + [sbox(x["lo"][0], x["lo"][1], x["hi"][0], x["hi"][1]) for x in recess + own]
    core = unary_union(foot).bounds
    wall = float(r["plate_wall_min"]) + margin
    need_size = [core[2] - core[0] + 2 * wall, core[3] - core[1] + 2 * wall]
    smin, smax = band_setpoints(st, "size_min", "size_max")
    size = []
    for i, ns in enumerate(need_size):
        s = max(ns, smin) if smin is not None else ns
        if smax is not None and s > smax + tol:
            # R12 review 2 (N5): a conflict only beyond the stated limit; between the setpoint and the limit it is a
            # note, and each message names the value it was compared with
            if s > spec(st, "size_max") + tol:
                conflicts.append(f"the parts need {ns:.2f} mm along {AXIS_NAMES[i]}, more than size_max "
                                 f"{spec(st, 'size_max'):g}")
            else:
                notes.append(f"the parts need {ns:.2f} mm along {AXIS_NAMES[i]}: within size_max "
                             f"{spec(st, 'size_max'):g}, but more than {limit_words(st, 'size_max', smax)}")
        size.append(s)
    # --- thickness: fasteners, the mapped band
    tmin, tmax = band_setpoints(st, "thickness_min", "thickness_max")
    step = float(r.get("layer_height", 0.0))
    t = ceil_to(max(z_top_need - z_bot, tmin or 0.0), step)
    if tmax is not None and t > tmax + tol:
        need_t = f"the fastener stack needs a thickness of {t:.2f} mm ({z_top_need - z_bot:.2f} mm in whole layers)"
        if t > spec(st, "thickness_max") + tol:
            conflicts.append(f"{need_t}, more than thickness_max {spec(st, 'thickness_max'):g}")
        else:
            notes.append(f"{need_t}: within thickness_max {spec(st, 'thickness_max'):g}, but more than "
                         f"{limit_words(st, 'thickness_max', tmax)}")
    # --- reference keep-outs (swept) and the outline position that clears them
    refs = reference_keepouts(st, mate, shifts, seg) if mate is not None else []
    feature_h = feature_height(st) if control(st, SURFACE) != "none" else 0.0
    z_hi_est = z_bot + max(t, tmax or t) + feature_h
    clearance = max([keepout_clearance(st, k) for k in refs if not k["contact"]] + [0.0]) + margin
    centre, gap = position(st, core, wall, size, refs, z_bot, z_hi_est, margin)
    if gap is not None and gap < -tol:
        conflicts.append(f"no outline position keeps the required clearance (ref_clearance less each keep-out's own "
                         f"catalogue margin) from every reference keep-out (worst shortfall {-gap:.2f} mm)")
    outline = [centre[0] - size[0] / 2, centre[1] - size[1] / 2, centre[0] + size[0] / 2, centre[1] + size[1] / 2]
    st.plate = {"chain": dict(chain, length=length), "into": into, "z_face": z_face, "z_bot": z_bot, "z_nut": z_nut,
                "z_pocket": z_pocket, "nut_top": nut_top, "declared_adjust": [{"dir": d.tolist(), "range": rng}
                                                                             for d, rng in declared],
                "seat_z": seat_z, "tip": tip, "outline": outline, "size": size, "need_size": need_size,
                "thickness": t, "z_top": z_bot + t, "slide": {"dir": u.tolist(), "range": R_u},
                "adjust": [{"dir": d.tolist(), "range": rng, "covered": covered[i]} for i, (d, rng) in enumerate(adjust)],
                "holes": [list(map(float, p)) for p in holes.at], "cuts": cuts, "recess": recess, "own": own,
                "mate": None if mate is None else {k: v for k, v in mate.items() if k != "inst"}, "notes": notes,
                "conflicts": conflicts, "clearance": clearance, "gap": gap, "flats": flats,
                "surface": control(st, SURFACE), "handedness": control(st, HANDEDNESS), "retention": retention,
                "frame": frame}
    record_defaults(st)
    emit(st, seg)
    size_for_load(st, seg)
    choose_orientation(st)
    contact_face_openings(st)
    for c in conflicts + notes:
        line = f"derive: plate: {c}"
        if line not in st.notes:
            st.notes.append(line)
    drop_stale_notes(st)
    st.resolved = A.resolve(st)
    return None


FEATURE_SLOTS = ("feature_count_min", "feature_height_min", "feature_height_max", "feature_edge_min",
                 "feature_coverage_min")
FEATURE_ROLES = ("tap_hole",)               # a surface feature's own hole (the stud fills it)


def contact_face_openings(st: "A.AssemblyState") -> None:
    """R12 review 2 (N4): a typed note (st.plate["contact_face_openings"], a derive note, self_report typed_notes and
    the controller's state words) for every cut left open on a face the requirements or the catalogue declare a
    contact face: the free face when ParseSpec mapped a raised-feature slot (the text gives that face grip features: it
    meets something), the underside when the plate lies on an engaged catalogue part's mating plane (catalogue engage
    interface; the engaged part's own keep-out recess is a declared opening and is left out). Each with its open plan
    area on that face. A note, not a check: no actuator closes a cut yet (a closed pocket is ARCHITECTURE.md's open
    item), so the controller and the reader see it, nothing is hidden."""
    from shapely.geometry import Polygon, box as sbox
    from shapely.ops import unary_union
    p = st.plate
    tol = float(st.rules.values["measure_tol"])
    x0, y0, x1, y1 = p["outline"]
    plate_box = sbox(x0, y0, x1, y1)
    rows = []
    faces = []
    mapped = [k for k in FEATURE_SLOTS if spec(st, k) is not None]
    if mapped:
        faces.append(("top", f"the mapped raised-feature slots ({', '.join(mapped)}) make the free face a working face"))
    if p.get("mate"):
        faces.append(("underside", f"it lies on the {p['mate']['part']}'s mating plane (catalogue engage interface)"))
    recess = unary_union([Polygon(x["poly"]) if x.get("poly") else sbox(x["lo"][0], x["lo"][1], x["hi"][0], x["hi"][1])
                          for x in p["recess"]]) if p["recess"] else None
    for face, why in faces:
        cuts = []
        for c in p["cuts"]:
            if c.get("body", BODY) != BODY or c["role"] in FEATURE_ROLES:
                continue
            reaches = c["z1"] is None if face == "top" else c["z0"] <= p["z_bot"] + tol
            if not reaches:
                continue
            open_ = Polygon(c["poly"]).buffer(0).intersection(plate_box)
            if face == "underside" and recess is not None:
                open_ = open_.difference(recess)
            if open_.area > tol:
                cuts.append({"id": c["id"], "role": c["role"], "area_mm2": round(float(open_.area), 2)})
        for x in p["own"]:
            if face == "top" and x.get("z1") is None:
                a_ = sbox(x["lo"][0], x["lo"][1], x["hi"][0], x["hi"][1]).intersection(plate_box).area
                if a_ > tol:
                    cuts.append({"id": x["id"], "role": "recess", "area_mm2": round(float(a_), 2)})
        if cuts:
            rows.append({"type": "open_cut_on_contact_face", "face": face, "declared_by": why, "cuts": cuts,
                         "area_mm2": round(sum(c["area_mm2"] for c in cuts), 2)})
    p["contact_face_openings"] = rows
    for row in rows:
        line = (f"derive: plate: typed note: cuts open on the {row['face']} face, a contact face ({row['declared_by']}): "
                + ", ".join(f"{c['id']} ({c['role']}) {c['area_mm2']:.0f} mm2" for c in row["cuts"]))
        if line not in st.notes:
            st.notes.append(line)


def typed_notes(st: "A.AssemblyState") -> List[dict]:
    """The plate's typed notes for self_report.json (R12 review 2 N4)."""
    return list((st.plate or {}).get("contact_face_openings") or [])


def drop_stale_notes(st: "A.AssemblyState") -> None:
    """R12 review 2 (N8): notes of a form the design no longer uses are dropped from the record. The shell's layout
    stages (ArrangeContents, Vents, BuildEnvelopes: the notes between their checkpoints and ChooseArchetype's) describe
    the shell's supports and envelopes, which the plate replaces (it keeps the references only); a Contents note that
    an item is unplaced is dropped once the plate places it. Counted in st.plate["dropped_notes"]."""
    cps = st.checkpoints or {}
    stale = set()
    if "arrange" in cps and "archetype" in cps:
        a, b = len(cps["arrange"].notes), len(cps["archetype"].notes)
        stale = {n for n in st.notes[a:b]} if b >= a and st.notes[:b] == cps["archetype"].notes else set()
    unplaced = {u.get("id") for u in st.unplaced}
    prefix = "contents: "                     # the Contents stage's own note (assembly.Contents)
    gone = [c.get("id") for c in st.contents if c.get("id") not in unplaced and c.get("id") != A.PRIMARY]
    stale |= {n for n in st.notes for i in gone if n.startswith(f"{prefix}{i} (") and " is unplaced: " in n}
    if stale:
        st.notes[:] = [n for n in st.notes if n not in stale]
        st.plate["dropped_notes"] = len(stale)


def rounded_rect(a: float, b: float, d: float, seg: int = ARC_SEGMENTS) -> List[Tuple[float, float]]:
    """An a x b rectangle (local X x Y, centred) grown by d/2 with circumscribed round corners: the plan of a slot that
    lets a shaft of diameter d move a along X and b along Y."""
    r = d / 2 / math.cos(math.pi / (4 * seg))
    q = math.pi / 2                          # a quarter turn per corner
    pts = []
    for j, (cx, cy) in enumerate(((a / 2, -b / 2), (a / 2, b / 2), (-a / 2, b / 2), (-a / 2, -b / 2))):
        for k in range(seg + 1):
            t = (j - 1) * q + q * k / seg
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def rect(u0: float, u1: float, v0: float, v1: float) -> List[Tuple[float, float]]:
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def frame_layout(st, holes, u, v, R_u: float, R_v: float, ang: float, flats: float, clear_d: float, z_bot: float,
                 z_pocket: float, z_nut: float, nut_t: float) -> Tuple[dict, List[dict]]:
    """The frame option (rule:nut_frame): a printed frame round every nut lying on the plate's pocket floor, in a pocket
    of the plate open to the free face that is the frame grown by half of each adjustment range plus rules.sliding_fit
    per side; slots through the pocket floor let each bolt move over both ranges.

    Review fix B1 (the nuts had no seat): each nut sits in a blind hex trap on the frame's own floor (z_nut - z_pocket,
    rules.plate_floor_min) with a bolt clearance hole through it, so the nut bears on the frame and moves with it; the
    frame is wider than the pocket-floor slots by rules.plate_wall_min on both sides at every adjustment position (a
    flange: half-width >= R_v + clear_d / 2 + wall across the slide), so the frame bears on the plate beside the slots
    wherever the bolts are set. The clamp_seat sensors measure both seats. Returns (frame spec, cuts)."""
    r = st.rules.values
    w, c, over = float(r["plate_wall_min"]), float(r["sliding_fit"]), float(r["cut_overrun"])
    pts = np.asarray([[float(p[0]), float(p[1])] for p in holes.at])
    c0 = pts.mean(axis=0)
    du = (pts - c0) @ np.asarray(u[:2], float)
    dv = (pts - c0) @ np.asarray(v[:2], float)
    corners = flats / math.cos(math.radians(30.0))
    half_v = max(flats / 2 + w, R_v + clear_d / 2 + w)          # the flange: a land of `w` beside the slot at every shift
    half_u = max(corners / 2 + w, clear_d / 2 + w)
    fu0, fu1 = float(du.min() - half_u), float(du.max() + half_u)
    fv0, fv1 = float(dv.min() - half_v), float(dv.max() + half_v)
    pu0, pu1, pv0, pv1 = fu0 - R_u / 2 - c, fu1 + R_u / 2 + c, fv0 - R_v / 2 - c, fv1 + R_v / 2 + c
    centre = (float(c0[0]), float(c0[1]))
    cuts = [{"id": "nut_pocket", "poly": _poly_world(rect(pu0, pu1, pv0, pv1), centre, ang), "local": rect(pu0, pu1, pv0, pv1),
             "centre": centre, "angle": ang, "z0": z_pocket, "z1": None, "role": "nut_pocket"}]
    hole = stadium(0.0, clear_d)
    for k, p in enumerate(holes.at):
        hc = (float(p[0]), float(p[1]))
        slot = rounded_rect(R_u, R_v, clear_d)
        cuts.append({"id": f"slot_{k}", "poly": _poly_world(slot, hc, ang), "local": slot, "centre": hc, "angle": ang,
                     "z0": z_bot - over, "z1": z_pocket + over, "role": "bolt_slot"})
        cuts.append({"id": f"frame_trap_{k}", "poly": _poly_world(hex_channel(0.0, flats), hc, ang),
                     "local": hex_channel(0.0, flats), "centre": hc, "angle": ang, "z0": z_nut,
                     "z1": z_nut + nut_t + over, "role": "nut_trap", "body": FRAME})
        if z_nut > z_pocket + EPS:
            cuts.append({"id": f"frame_hole_{k}", "poly": _poly_world(hole, hc, ang), "local": hole, "centre": hc,
                         "angle": ang, "z0": z_pocket - over, "z1": z_nut + over, "role": "bolt_hole", "body": FRAME})
    frame = {"local": rect(fu0, fu1, fv0, fv1), "centre": centre, "angle": ang, "z0": z_pocket,
             "h": (z_nut - z_pocket) + nut_t, "floor": z_nut - z_pocket, "size": [fu1 - fu0, fv1 - fv0],
             "pocket": [pu1 - pu0, pv1 - pv0]}
    return frame, cuts


def required_adjust(st, declared: Sequence[Tuple[np.ndarray, float]], rot: np.ndarray) -> List[Tuple[np.ndarray, float]]:
    """The adjustment the plate must give the bolted part (review fix B1/N5): each declared catalogue axis, raised to the
    mapped adjust_min along the main (largest declared) direction and adjust_cross_min across it (ParseSpec slots, the
    controller's mapping of the text). Only the axes the catalogue declares are adjustable: a mapped range with no
    declared axis to raise adds nothing (the text may describe another part's adjustment); it is noted."""
    amin, cmin = spec(st, "adjust_min"), spec(st, "adjust_cross_min")
    out = [(np.asarray(d, float), float(rng)) for d, rng in declared]
    if amin is None and cmin is None:
        return out
    if not out:
        st.notes.append("derive: plate: adjust_min / adjust_cross_min are mapped, but the bolted part declares no "
                        "adjustment axis; nothing is made adjustable")
        return out
    k = max(range(len(out)), key=lambda i: out[i][1])
    u = out[k][0] / np.linalg.norm(out[k][0])
    if amin is not None:
        out[k] = (out[k][0], max(out[k][1], amin))
    if cmin is not None:
        cross = [i for i, (d, _) in enumerate(out) if i != k and abs(float(np.dot(d / np.linalg.norm(d), u))) < EPS]
        if cross:
            out[cross[0]] = (out[cross[0]][0], max(out[cross[0]][1], cmin))
        else:
            st.notes.append("derive: plate: adjust_cross_min is mapped, but the bolted part declares no adjustment "
                            "across its main direction; nothing is added")
    return out


def swept_plan(prim: pt.Primitive, pose: np.ndarray, shifts: Sequence[np.ndarray]) -> Optional[List[Tuple[float, float]]]:
    """The plan of a vertical-cylinder keep-out swept over the adjustment shifts (review: a part-shaped seat instead of
    its bounding rectangle): the convex hull of its circle at every shift, which for a convex plan swept over a
    rectangle of shifts is the exact Minkowski sum. None for a box (its swept plan is the grown rectangle already) or a
    tilted cylinder."""
    if prim.primitive != "cylinder":
        return None
    rot = np.asarray(pose, float)[:3, :3]
    d = rot @ np.asarray(prim.dir, float)
    if abs(abs(float(d[2])) - 1.0) > EPS:
        return None
    from shapely.geometry import MultiPoint
    c = np.asarray(pose, float)[:3, :3] @ np.asarray(prim.at, float) + np.asarray(pose, float)[:3, 3]
    r = float(prim.d) / 2 / math.cos(math.pi / (2 * ARC_SEGMENTS * 2))
    ring = [(r * math.cos(2 * math.pi * k / (4 * ARC_SEGMENTS)), r * math.sin(2 * math.pi * k / (4 * ARC_SEGMENTS)))
            for k in range(4 * ARC_SEGMENTS)]
    pts = [(float(c[0] + s[0] + x), float(c[1] + s[1] + y)) for s in shifts for x, y in ring]
    return [tuple(map(float, q)) for q in list(MultiPoint(pts).convex_hull.exterior.coords)[:-1]]


def _world_box(prim: pt.Primitive, pose: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    lo, hi = prim.bbox()
    pts = np.array([[hi[i] if c >> i & 1 else lo[i] for i in range(3)] for c in range(8)])
    pts = pts @ np.asarray(pose, float)[:3, :3].T + np.asarray(pose, float)[:3, 3]
    return pts.min(axis=0), pts.max(axis=0)


def place_mate(st, item: dict, eng: Mapping[str, Any], inst: pt.PartInstance, pose: np.ndarray):
    """Place the engaged reference part (rule:engage_pose): its mate_plane on the engage plane (normals opposite), its
    mate_point on the engage centre axis, its frame aligned with the primary's. Removes it from st.unplaced."""
    minst = st.catalog.instantiate(item["part"], item.get("params") or {})
    rot = np.asarray(pose, float)[:3, :3]
    plane = _world(inst.datums[eng["plane"]], pose)
    centre = _world(inst.datums[eng["centre"]], pose)
    mplane = minst.datums[eng["mate_plane"]]
    if float(np.dot(rot @ np.asarray(mplane.normal, float), np.asarray(plane.normal, float))) > -1 + 1e-6:
        return f"engage: {item['part']}.{eng['mate_plane']} does not face {eng['plane']} in the aligned frame"
    n = np.asarray(plane.normal, float)
    c0, cd = np.asarray(centre.at, float), np.asarray(centre.dir, float)
    q = c0 + cd * float(np.dot(np.asarray(plane.at, float) - c0, n) / np.dot(cd, n))
    mp = np.asarray(minst.datums[eng["mate_point"]].at, float)
    t = q - rot @ mp
    rot_z = math.degrees(math.atan2(rot[1, 0], rot[0, 0]))
    nid = item["id"]
    st.graph.add(fg.Node(nid, "reference", "part", dict(item.get("params") or {}),
                         fg.Pose(offset=tuple(float(v) for v in t), rot_z=float(rot_z)), part=item["part"],
                         source="rule:engage_pose"))
    st.layout[nid] = {"part": item["part"], "params": dict(item.get("params") or {}), "x": float(t[0]), "y": float(t[1]),
                      "z": float(t[2]), "rot_z": float(rot_z), "item": nid, "copy": 0, "role": "engaged",
                      "edge": None, "of": A.PRIMARY, "relation": f"{inst.part.id}.{eng['plane']} on "
                                                              f"{item['part']}.{eng['mate_plane']}"}
    st.unplaced = [u for u in st.unplaced if u.get("id") != nid]
    mpose = fg.matrix(fg.rot_z_matrix(rot_z), t)
    return {"id": nid, "part": item["part"], "pose": mpose.tolist(), "inst": minst,
            "plane_z": float(plane.at[2])}


def reference_keepouts(st, mate: Mapping[str, Any], shifts: Sequence[np.ndarray], seg: int) -> List[dict]:
    """The engaged reference's keep-outs, each swept over the adjustment shifts and its catalogue `sweep` (a rotation
    about one of its datums): {id, solid (world, manifold), contact (it touches the mating plane from below: designed
    contact, interference only), poly (shapely plan footprint)}."""
    r = st.rules.values
    minst, mpose = mate["inst"], np.asarray(mate["pose"], float)
    out = []
    for ko in minst.keepouts:
        entry = pt.keepout_entry(minst.part, ko.id)
        sw = entry.get("sweep")
        base = _solid_of(ko, seg).transform(fg._m3(mpose))
        angles, pivot, axis = [0.0], np.zeros(3), np.array([0.0, 0.0, 1.0])
        if sw:
            total = float(fg.evaluate(sw["angle"], minst.env))
            angles = _angles(total, float(r["sweep_step_deg"]))
            pivot = np.asarray(_world(minst.datums[sw["about"]], mpose).at, float)
            axis = np.asarray(mpose[:3, :3] @ np.asarray(sw["axis"], float))
        solids = [base.transform(fg._m3(_rot_about(axis, pivot, a, s))) for s in shifts for a in angles]
        solid = _union(solids)
        b = solid.bounding_box()
        contact = float(b[5]) <= mate["plane_z"] + float(r["measure_tol"])
        out.append({"id": ko.id, "solid": solid, "contact": contact, "swept": bool(sw), "angles": len(angles),
                    "zrange": (float(b[2]), float(b[5])), "poly": _plan(solid),
                    "margin": pt.keepout_margin(minst, ko.id), "names": pt.keepout_names(minst.part, ko.id)})
    return out


def _plan(solid):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    polys = [Polygon(p) for p in solid.project().to_polygons() if len(p) >= 3]
    return unary_union([p.buffer(0) for p in polys]) if polys else None


def keepout_clearance(st, k: Mapping[str, Any]) -> float:
    """The gap the plate must keep from a non-contact reference keep-out (review fix N6): the mapped ref_clearance less
    the clearance the catalogue already built into that keep-out (its entry's `margin`), never below 0; 0 when the text
    states no clearance (the keep-out itself is the boundary)."""
    ref = spec(st, "ref_clearance")
    return 0.0 if ref is None else max(0.0, ref - float(k.get("margin") or 0.0))


def position(st, core, wall: float, size: Sequence[float], refs: Sequence[dict], z_lo: float, z_hi: float,
             margin: float) -> Tuple[Tuple[float, float], Optional[float]]:
    """The outline centre (part of rule:plate, plant): every centre on a rules.position_step grid for which the outline
    holds the core plus the wall; the nearest to the core's centre that keeps each non-contact reference keep-out
    overlapping the plate's height at its own required gap (keepout_clearance) plus `margin` (the setpoint offset); else
    the one with the least shortfall. Returns (centre, the worst slack over the keep-outs in mm, or None)."""
    from shapely.geometry import box as sbox
    cx, cy = (core[0] + core[2]) / 2, (core[1] + core[3]) / 2
    obst = [(k["poly"], keepout_clearance(st, k) + margin) for k in refs if not k["contact"] and k["poly"] is not None
            and k["zrange"][1] > z_lo + EPS and k["zrange"][0] < z_hi - EPS]
    if not obst:
        return (cx, cy), None
    step = float(st.rules.values["position_step"])
    rng = []
    for i, (lo, hi) in enumerate(((core[0], core[2]), (core[1], core[3]))):
        a, b = hi + wall - size[i] / 2, lo - wall + size[i] / 2
        n = int(math.floor((b - a) / step + 1e-9)) if b > a else 0
        rng.append([a + k * step for k in range(n + 1)] or [(a + b) / 2])
    cands = sorted(((x, y) for x in rng[0] for y in rng[1]), key=lambda p: (abs(p[0] - cx) + abs(p[1] - cy), p))
    best = None
    for x, y in cands:
        box_ = sbox(x - size[0] / 2, y - size[1] / 2, x + size[0] / 2, y + size[1] / 2)
        g = min(box_.distance(poly) - target for poly, target in obst)
        if g >= 0.0:
            return (x, y), float(g)
        if best is None or g > best[1]:
            best = ((x, y), float(g))
    return best


def feature_height(st) -> float:
    lo, hi = spec(st, "feature_height_min"), spec(st, "feature_height_max")
    if lo is not None and hi is not None:
        return (lo + hi) / 2
    if lo is not None:
        return lo + float(st.rules.values["design_margin"])
    if hi is not None:
        return hi - float(st.rules.values["design_margin"])
    return float(st.rules.values["grip_height_default"])


def fastener_load(st) -> dict:
    """R12 review 2 (N4): the load each fastener seat carries and what the printed material allows. The preload is the
    mapped fastener_preload, else rules.fastener_preload_stress_default on the catalogue bolt's tap-drill (core) area
    (rule:default_preload); the material strength is the mapped strength, else rules.print_strength_default
    (rule:default_print_strength), divided by the mapped safety_factor (1 when silent); bearing pressure is allowed
    rules.bearing_strength_ratio of it, punch-through shear rules.shear_strength_ratio. Sensor input only."""
    r, p = st.rules.values, st.plate
    bd = p["chain"]["bolt_params"]
    F = spec(st, "fastener_preload")
    if F is None:
        F = float(r["fastener_preload_stress_default"]) * math.pi / 4 * float(bd["tap_diameter"]) ** 2
        A.choice(st, f"fastener_preload[{BODY}]", round(F, 3), "rule:default_preload",
                 basis=f"rules.fastener_preload_stress_default on the {p['chain']['bolt']} tap-drill area")
    strength = spec(st, "strength")
    if strength is None:
        strength = float(r["print_strength_default"])
        A.choice(st, f"print_strength[{BODY}]", strength, "rule:default_print_strength")
    sf = spec(st, "safety_factor") or 1.0
    return {"preload": round(float(F), 3), "strength": strength, "safety": sf,
            "allow_bearing": strength * float(r["bearing_strength_ratio"]) / sf,
            "allow_shear": strength * float(r["shear_strength_ratio"]) / sf,
            "preload_source": "fastener_preload" if spec(st, "fastener_preload") is not None else "rule:default_preload"}


def record_defaults(st) -> None:
    """The plate vocabularies' defaults are recorded as plant decisions when the controller has not chosen."""
    if st.control.get(SURFACE) is None:
        A.choice(st, f"{SURFACE}[{FACE_TOP}]", control(st, SURFACE), "rule:default_surface_feature")
    if st.control.get(RETENTION) is None and not st.plate.get("into"):
        A.choice(st, f"{RETENTION}[{BODY}]", control(st, RETENTION), "rule:default_nut_retention")
    if st.control.get(HANDEDNESS) is None and mirror_reference(st) is not None:
        A.choice(st, f"{HANDEDNESS}[{BODY}]", control(st, HANDEDNESS), "rule:default_handedness")
    st.plate["fastener_load"] = fastener_load(st)


def emit(st, seg: int) -> None:
    """(Re)write the plate's nodes from st.plate: the body, its cuts, the fasteners and the surface features. Every
    parameter is a number Python derived (the graph needs no expressions here)."""
    g, p, r = st.graph, st.plate, st.rules.values
    for nid in [n.id for n in g if n.id in (BODY, FRAME) or n.body in (BODY, FRAME)
                or (n.source or "").startswith("rule:plate_fastener")
                or (n.source or "").startswith("rule:surface_feature")]:
        del g.nodes[nid]
    x0, y0, x1, y1 = p["outline"]
    z_bot, z_top = p["z_bot"], p["z_bot"] + p["thickness"]
    p["z_top"] = z_top
    over = float(r["cut_overrun"])
    g.add(fg.Node(BODY, "body", "box", {"x": x1 - x0, "y": y1 - y0, "z": z_top - z_bot},
                  fg.Pose(offset=((x0 + x1) / 2, (y0 + y1) / 2, z_bot)), body=BODY, role="plate",
                  source="rule:plate", color=fg.BODY_COLORS[0]))
    fr = p.get("frame")
    if fr:
        g.add(fg.Node(FRAME, "body", "prism", prism_params(fr["local"], fr["h"]),
                      fg.Pose(offset=(fr["centre"][0], fr["centre"][1], fr["z0"]), rot_z=fr["angle"]), body=FRAME,
                      role="nut_frame", source="rule:nut_frame", color=fg.BODY_COLORS[1]))
    for c in p["cuts"]:
        z1 = c["z1"] if c["z1"] is not None else z_top + over
        body = c.get("body", BODY)
        g.add(fg.Node(c["id"], "cut", "prism", prism_params(c["local"], z1 - c["z0"]),
                      fg.Pose(offset=(c["centre"][0], c["centre"][1], c["z0"]), rot_z=c["angle"]), body=body,
                      role=c["role"], source="rule:nut_frame" if body == FRAME or c["role"] == "nut_pocket"
                      else "rule:adjust_slot"))
    for x in p["recess"] + p["own"]:
        if x.get("poly"):
            z0, z1 = x.get("z0", z_bot - over), x.get("z1", z_top + over)
            g.add(fg.Node(x["id"], "cut", "prism", prism_params(x["poly"], z1 - z0), fg.Pose(offset=(0.0, 0.0, z0)),
                          body=BODY, role="recess", source="rule:recess"))
            continue
        if x.get("cyl"):
            g.add(fg.Node(x["id"], "cut", "cylinder", {"d": x["d"], "h": z_top - z_bot + 2 * over},
                          fg.Pose(offset=(x["xy"][0], x["xy"][1], z_bot - over)), body=BODY, role="recess",
                          source="rule:recess"))
            continue
        lo, hi = np.asarray(x["lo"], float), np.asarray(x["hi"], float)
        z0 = x.get("z0", lo[2] - over)
        z1 = x.get("z1", z_top + over)
        g.add(fg.Node(x["id"], "cut", "box", {"x": float(hi[0] - lo[0]), "y": float(hi[1] - lo[1]), "z": float(z1 - z0)},
                      fg.Pose(offset=(float(lo[0] + hi[0]) / 2, float(lo[1] + hi[1]) / 2, float(z0))), body=BODY,
                      role="recess", source="rule:recess"))
    ch = p["chain"]
    if p.get("into"):
        screw_into_length(st)
    for k, h in enumerate(p["holes"]):
        if p.get("into"):                      # head on the free face, thread into the part's tapped hole
            g.add(fg.Node(f"bolt_{k}", "reference", "part", {"length": ch["length"]}, fg.Pose(offset=(h[0], h[1], z_top)),
                          part=ch["bolt"], source="rule:plate_fastener(screw)"))
            st.layout[f"bolt_{k}"] = {"part": ch["bolt"], "params": {"length": ch["length"]}, "x": h[0], "y": h[1],
                                      "z": z_top, "rot_z": 0.0, "item": f"bolt_{k}", "copy": k, "role": "fastener",
                                      "edge": None, "of": A.PRIMARY}
            continue
        g.add(fg.Node(f"bolt_{k}", "reference", "part", {"length": ch["length"]},
                      fg.Pose(offset=(h[0], h[1], p["seat_z"]), axis_dir=(0.0, 0.0, -1.0)), part=ch["bolt"],
                      source="rule:plate_fastener(bolt)"))
        g.add(fg.Node(f"nut_{k}", "reference", "part", {}, fg.Pose(offset=(h[0], h[1], p["z_nut"])), part=ch["nut"],
                      source="rule:plate_fastener(nut)"))
        st.layout[f"bolt_{k}"] = {"part": ch["bolt"], "params": {"length": ch["length"]}, "x": h[0], "y": h[1],
                                  "z": p["seat_z"], "rot_z": 0.0, "axis_dir": [0.0, 0.0, -1.0], "item": f"bolt_{k}",
                                  "copy": k, "role": "fastener", "edge": None, "of": A.PRIMARY}
        st.layout[f"nut_{k}"] = {"part": ch["nut"], "params": {}, "x": h[0], "y": h[1], "z": p["z_nut"], "rot_z": 0.0,
                                 "item": f"nut_{k}", "copy": k, "role": "fastener", "edge": None, "of": A.PRIMARY}
    for key in [k for k in st.layout if k.startswith(("stud_", "pin_"))]:
        del st.layout[key]
    p["features"] = []
    if p["surface"] != "none":
        place_features(st, seg)
    st.fasteners.update({f"fastener.plate.{k}": v for k, v in ch["bolt_params"].items()})


def screw_into_length(st) -> None:
    """A screw from the free face into the part's tapped hole (rule:plate_fastener): the longest stock length whose
    thread past the plate stays within the hole's thread depth (less rules.design_margin) and engages at least
    rules.tapped_engagement_ratio thread diameters; a length that cannot do both leaves the engagement sensor failing."""
    p, r = st.plate, st.rules.values
    ch = p["chain"]
    t_hole = p["z_bot"] + p["thickness"] - p["z_face"]
    d = ch["bolt_params"]["thread_diameter"]
    need = float(r["tapped_engagement_ratio"]) * d
    ok = [L for L in ch["lengths"] if need - EPS <= L - t_hole <= ch["depth"] - float(r["design_margin"])]
    L = max(ok) if ok else min(ch["lengths"], key=lambda x: abs(x - t_hole - need))
    ch["length"] = L
    p["engagement"] = L - t_hole
    p["engagement_min"] = need
    p["tip"] = p["z_face"] - (L - t_hole)


def place_features(st, seg: int) -> None:
    """The controller's surface feature (rule:surface_feature): count, height, edge distance from the mapped slots (or
    the rules defaults), spread by farthest-point sampling from the inset outline's corners over the free top face (no
    feature over an open cut, each at least rules.plate_wall_min from it); studs: the catalogue set screw in a tapped
    hole (stock length so the engagement is at least its min_engagement); pins: printed cylinders."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    g, p, r = st.graph, st.plate, st.rules.values
    kind = p["surface"]
    margin, wall = float(r["design_margin"]), float(r["plate_wall_min"])
    h = feature_height(st)
    n = int(math.ceil(spec(st, "feature_count_min") or r["grip_count_default"]))
    e = setpoint_min(st, spec(st, "feature_edge_min")) or float(r["grip_edge_default"])
    stud = stud_part(st) if kind == "studs" else None
    if kind == "studs":
        if stud is None:
            raise ValueError("surface feature studs: no catalogue set screw")
        sp = st.catalog.get(stud)
        d = float(sp.params["thread_diameter"]["default"])
        tap = float(sp.params["tap_diameter"]["default"])
        eng = max(float((sp.params.get("min_engagement") or {}).get("default") or 0.0),
                  float(r["plastic_thread_engagement_ratio"]) * d)
        L = next((x for x in pt.stock_lengths(sp) if x - h >= eng - EPS), None)
        if L is None:
            raise ValueError(f"surface feature studs: no stock length of {stud} gives {eng:g} mm engagement")
        depth = L - h
    else:
        d = float(r["grip_pin_diameter"])
        tap, depth, L = 0.0, 0.0, 0.0
    x0, y0, x1, y1 = p["outline"]
    inset = e + d / 2 + margin
    ix0, iy0, ix1, iy1 = x0 + inset, y0 + inset, x1 - inset, y1 - inset
    if ix1 <= ix0 or iy1 <= iy0:
        raise ValueError("surface feature: the face is too small for the edge distance")
    z_top = p["z_top"]
    blocked = []
    for c in p["cuts"]:
        top = c["z1"] if c["z1"] is not None else z_top + 1
        if top >= z_top - depth - EPS:                    # the cut reaches the feature's hole or the face
            blocked.append(Polygon(c["poly"]))
    for x in p["recess"] + p["own"]:
        top = x.get("z1", z_top)
        if top >= z_top - depth - float(r["plate_floor_min"]) - EPS:
            blocked.append(Polygon([(x["lo"][0], x["lo"][1]), (x["hi"][0], x["lo"][1]), (x["hi"][0], x["hi"][1]),
                                    (x["lo"][0], x["hi"][1])]))
    keep = unary_union(blocked).buffer(wall + d / 2) if blocked else None
    step = max(float(r["position_step"]), d / 4)
    xs = np.arange(ix0, ix1 + EPS, step)
    ys = np.arange(iy0, iy1 + EPS, step)
    cand = [(float(x), float(y)) for x in xs for y in ys if keep is None or not keep.contains(Point(x, y))]
    if not cand:
        raise ValueError("surface feature: no free spot on the face")
    chosen: List[Tuple[float, float]] = []
    pts = np.asarray(cand)
    for corner in ((ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)):
        if len(chosen) >= n:
            break
        k = int(np.argmin(np.hypot(pts[:, 0] - corner[0], pts[:, 1] - corner[1])))
        if tuple(pts[k]) not in chosen:
            chosen.append(tuple(map(float, pts[k])))
    min_pitch = d + wall
    while len(chosen) < n:
        dist = np.min(np.hypot(pts[:, None, 0] - np.asarray(chosen)[None, :, 0],
                               pts[:, None, 1] - np.asarray(chosen)[None, :, 1]), axis=1)
        k = int(np.argmax(dist))
        if dist[k] < min_pitch:
            break
        chosen.append(tuple(map(float, pts[k])))
    for k, (x, y) in enumerate(chosen):
        if kind == "studs":
            g.add(fg.Node(f"stud_hole_{k}", "cut", "cylinder", {"d": tap, "h": depth + float(r["cut_overrun"])},
                          fg.Pose(offset=(x, y, z_top - depth)), body=BODY, role="tap_hole",
                          source="rule:surface_feature(studs)"))
            g.add(fg.Node(f"stud_{k}", "reference", "part", {"length": L}, fg.Pose(offset=(x, y, z_top + h)),
                          part=stud, source="rule:surface_feature(stud)"))
            st.layout[f"stud_{k}"] = {"part": stud, "params": {"length": L}, "x": x, "y": y, "z": z_top + h, "rot_z": 0.0,
                                      "item": f"stud_{k}", "copy": k, "role": "surface_feature", "edge": None,
                                      "of": BODY}
        else:
            g.add(fg.Node(f"pin_{k}", "add", "cylinder", {"d": d, "h": h + float(r["cut_overrun"])},
                          fg.Pose(offset=(x, y, z_top - float(r["cut_overrun"]))), body=BODY, role="grip_pin",
                          source="rule:surface_feature(pins)"))
    p["features"] = [{"x": x, "y": y, "d": d, "h": h, "kind": kind} for x, y in chosen]
    p["feature_spec"] = {"kind": kind, "count": n, "height": h, "edge": e, "diameter": d, "part": stud,
                         "length": L, "depth": depth}


def plate_solid(st, seg: Optional[int] = None, body: str = BODY):
    """A printed body of the plate archetype as a manifold solid from its nodes only (numbers, no references)."""
    nodes = [n for n in st.graph if n.id == body or n.body == body]
    sub = fg.FeatureGraph(nodes)
    res = sub.resolve({}, st.rules.values)
    return fg.body_solid(sub, body, res)


def size_for_load(st, seg: int) -> None:
    """Load sizing (part of rule:plate, plant): when the request states a load case (mapped load_force, load_patch,
    strength), grow the thickness until the worst-case stress Python measures on the built section (edge_stresses: every
    adjustment extreme) is within strength / safety_factor, up to the mapped thickness_max (else
    rules.stress_sizing_iterations passes). A residue at the thickness limit is recorded (st.plate["load"]: capped) so
    the load_stress sensor types it as a requirement conflict; the plant has no other structural option yet."""
    case = load_case(st)
    p, r = st.plate, st.rules.values
    p["load"] = None
    if case is None:
        return
    tmax = band_setpoints(st, "thickness_min", "thickness_max")[1]
    step = float(r.get("layer_height", 0.0))
    cap = None if tmax is None else (math.floor(tmax / step + 1e-9) * step if step else tmax)
    worst = 0.0
    for _ in range(int(r["stress_sizing_iterations"])):
        rows = stresses(st, plate_solid(st, seg), case)
        worst = max((x["stress"] for x in rows), default=0.0)
        if worst <= case["allow"] + EPS:
            break
        t_new = ceil_to(p["thickness"] * math.sqrt(worst / case["allow"]), step)
        if cap is not None:
            t_new = min(t_new, max(p["thickness"], cap))
        if t_new <= p["thickness"] + EPS:
            break
        p["thickness"] = t_new
        emit(st, seg)
    else:
        worst = max((x["stress"] for x in stresses(st, plate_solid(st, seg), case)), default=0.0)
    capped = worst > case["allow"] + EPS and cap is not None and p["thickness"] >= cap - EPS
    p["load"] = {"worst": round(worst, 4), "allow": round(case["allow"], 4), "thickness": p["thickness"],
                 "capped": bool(capped), "cap": cap}
    rows = stresses(st, plate_solid(st, seg), case)
    if rows:                                  # R12 review 2 (N9): where the worst case is, and what each cut costs
        top = max(rows, key=lambda x: x["stress"])
        p["load"]["where"] = {k: top.get(k) for k in ("edge", "arm", "at", "patch_at", "window", "shift", "width")}
        p["load"]["section_loss"] = section_loss(top, case, plate_solid_without(st, cut_roles(st), seg),
                                                 {r: plate_solid_without(st, [r], seg) for r in cut_roles(st)})


def choose_orientation(st) -> None:
    """rule:print_orientation (guardrail): of the plate's two flat faces, the one to print on the bed is the one whose
    overhang violation (printability) is smaller; a tie goes to the larger flat area on the bed."""
    solid = plate_solid(st)
    rows = {}
    for o in ORIENTATIONS:
        rows[o] = overhangs(solid, o, st.rules.values)
    best = min(ORIENTATIONS, key=lambda o: (rows[o]["violation"], -rows[o]["bed_area"]))
    st.plate["orientation"] = best
    st.plate["orientations"] = {o: {k: v for k, v in rows[o].items() if k != "regions"} for o in ORIENTATIONS}
    A.choice(st, f"print_orientation[{BODY}]", best, "rule:print_orientation",
             violation={o: rows[o]["violation"] for o in ORIENTATIONS})


# ---------------------------------------------------------------------------
# Measurements shared by the sensors (on manifold solids and delivered meshes alike)
# ---------------------------------------------------------------------------


def _mesh(solid):
    m = solid.to_mesh()
    return np.asarray(m.vert_properties, float)[:, :3], np.asarray(m.tri_verts, np.int64)


def overhangs(solid, orientation: str, rules: Mapping[str, float]) -> dict:
    """Downward faces in a print orientation: triangles whose normal points down more steeply than
    rules.overhang_angle_deg from vertical, above the bed. Flat ones are bridges, grouped into connected regions whose
    span is the shorter side of the region's minimum rotated rectangle (<= rules.bridge_max passes); steeper slanted
    ones are overhangs (area > 0 fails). Returns {violation, worst_span, steep_area, bed_area, regions}."""
    import trimesh
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    v, f = _mesh(solid)
    if orientation == ORIENTATIONS[1]:
        v = v * np.array([1.0, -1.0, -1.0])           # a half turn about X: the top face goes onto the bed
    tm = trimesh.Trimesh(v, f, process=False)
    n = tm.face_normals
    zmin = float(v[:, 2].min())
    tol = float(rules["measure_tol"])
    cz = tm.triangles_center[:, 2]
    lim = math.cos(math.radians(float(rules["overhang_angle_deg"])))
    down = (n[:, 2] < -lim - 1e-6) & (cz > zmin + tol)
    bed = (n[:, 2] < -1 + 1e-6) & (cz <= zmin + tol)
    bed_area = float(tm.area_faces[bed].sum())
    flat = down & (n[:, 2] < -1 + 1e-4)
    steep = down & ~flat
    steep_area = float(tm.area_faces[steep].sum())
    regions = []
    idx = np.nonzero(flat)[0]
    if len(idx):
        adj = tm.face_adjacency
        keep = flat[adj[:, 0]] & flat[adj[:, 1]]
        import trimesh.graph as tg
        comps = tg.connected_components(adj[keep], nodes=idx, min_len=1)
        for comp in comps:
            polys = [Polygon(tm.triangles[k][:, :2]) for k in comp]
            shape = unary_union([q.buffer(1e-6) for q in polys if q.area > 0])
            if shape.is_empty:
                continue
            regions.append({"span": round(bridge_span(shape), 4), "area": round(float(shape.area), 4),
                            "z": round(float(tm.triangles_center[comp[0]][2]), 4)})
    worst = max((x["span"] for x in regions), default=0.0)
    bridge = float(rules["bridge_max"])
    violation = max(0.0, worst - bridge) + steep_area
    return {"violation": round(violation, 6), "worst_span": worst, "steep_area": round(steep_area, 6),
            "bed_area": round(bed_area, 4), "regions": sorted(regions, key=lambda x: -x["span"])[:6]}


def bridge_span(shape) -> float:
    """The span a flat downward region bridges: the diameter of the largest circle inside it (every point of a region
    lies within half of it from an edge where the layer below or a wall carries it). A pocket ceiling 43 mm wide spans 43;
    a ring 5 mm wide round a slot spans 5."""
    from shapely.ops import polylabel
    polys = list(getattr(shape, "geoms", [shape]))
    best = 0.0
    for poly in polys:
        if poly.is_empty or poly.area <= 0:
            continue
        c = polylabel(poly, tolerance=0.05)
        best = max(best, 2.0 * float(poly.boundary.distance(c)))
    return best


def load_case(st) -> Optional[dict]:
    """The request's load case from the mapped slots (load_force, load_patch, strength; safety_factor 1 when silent), or
    None when the text states none (no sizing, no stress sensor)."""
    F, a, s = spec(st, "load_force"), spec(st, "load_patch"), spec(st, "strength")
    if F is None or a is None or s is None:
        return None
    sf = spec(st, "safety_factor") or 1.0
    return {"force": F, "patch": a, "strength": s, "safety": sf, "allow": s / sf}


def section_props(rings: Sequence[np.ndarray], zi: int) -> Optional[dict]:
    """Area, centroid height and second moment about the horizontal centroidal axis of a planar section from its signed
    rings (outer counter-clockwise, holes clockwise); column zi of each ring is the vertical coordinate."""
    A_, Sz, Iz = 0.0, 0.0, 0.0
    allz = []
    for ring in rings:
        if len(ring) < 3:
            continue
        a_col = 1 - zi
        xs, zs = ring[:, a_col], ring[:, zi]
        xn, zn = np.roll(xs, -1), np.roll(zs, -1)
        cross = xs * zn - xn * zs
        sign = 1.0 if zi == 1 else -1.0           # (u, v) orientation: z in column 1 keeps the sign
        A_ += sign * cross.sum() / 2
        Sz += sign * ((zs + zn) * cross).sum() / 6
        Iz += sign * ((zs * zs + zs * zn + zn * zn) * cross).sum() / (2 * 6)   # the polygon formula's 1/12
        allz += list(zs)
    if abs(A_) < EPS:
        return None
    if A_ < 0:
        A_, Sz, Iz = -A_, -Sz, -Iz
    zc = Sz / A_
    I = Iz - A_ * zc * zc
    c = max(abs(z - zc) for z in allz)
    return {"area": A_, "zc": zc, "I": I, "c": c}


def clip_ring(ring: np.ndarray, col: int, lo: float, hi: float) -> np.ndarray:
    """A section ring clipped to lo <= ring[:, col] <= hi (Sutherland-Hodgman against the two lines of a strip). Each
    ring is clipped on its own: the signed area integrals of the clipped rings add up to those of the section inside
    the strip (holes keep their orientation)."""
    pts = [tuple(p) for p in ring]
    for keep in ((lambda q: q[col] >= lo - 1e-12, lo), (lambda q: q[col] <= hi + 1e-12, hi)):
        inside, bound = keep
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            ia, ib = inside(a), inside(b)
            if ia:
                out.append(a)
            if ia != ib and abs(b[col] - a[col]) > 1e-15:
                t = (bound - a[col]) / (b[col] - a[col])
                out.append(tuple(a[j] + t * (b[j] - a[j]) for j in range(2)))
        pts = out
        if not pts:
            break
    return np.asarray(pts, float).reshape(-1, 2)


def probe_points(lo: float, hi: float, step: float, extra: Sequence[float] = ()) -> List[float]:
    """Positions from lo to hi no more than `step` apart, both ends and any `extra` inside the range included (R12
    review 2 N1: a load-case search that also covers the corners and every intermediate shift)."""
    if hi - lo <= EPS:
        return [(lo + hi) / 2]
    n = max(1, int(math.ceil((hi - lo) / max(step, EPS) - 1e-9)))
    pts = [lo + (hi - lo) * k / n for k in range(n + 1)] + [x for x in extra if lo - EPS <= x <= hi + EPS]
    return sorted({round(float(x), 9) for x in pts})


def _section_stress(rings: Sequence[np.ndarray], zi: int, lo: float, hi: float, force: float, arm: float):
    """M c / I of the section rings clipped to lo <= u <= hi (the 45-degree window), or None for no section."""
    clipped = [clip_ring(r, 1 - zi, lo, hi) for r in rings]
    props = section_props([r for r in clipped if len(r) >= 3], zi)
    if props is None or props["I"] <= EPS:
        return None, None
    return force * arm * props["c"] / props["I"], props


def edge_stresses(solid, outline: Sequence[float], adjust: Sequence[Mapping[str, Any]], prim_lo, prim_hi,
                  case: Mapping[str, float], step: float = 1.0) -> List[dict]:
    """Per outline edge, the worst case of the load case over where it acts and where the bolted part is set (review
    fixes B2, N1; R12 review 2 N1): the load case's patch (a load_patch square, one side flush with the edge) at every
    position along that edge from corner to corner (`step` apart, both corners and the middle included), carried to the
    part's footprint at every position of its adjustment range along the edge's normal (`step` apart, both extremes and
    the middle included: the farthest is the longest lever arm, an intermediate one may cut a weaker section); the
    bending stress M c / I of the measured section of `solid` at that footprint edge, the section's width clipped to
    the patch width plus twice the arm, centred on the patch (a 45-degree load spread from the patch to the support:
    at a corner the plate's own edge clips it, the plate is never credited with more width than the load reaches).
    0 when the patch lies over the footprint. Each row records where: `arm`, `at` (the section plane), `patch_at` (the
    patch centre along the edge), `window` (the clipped width's bounds) and `shift`."""
    out = []
    for axis, sign, edge in ((0, 1, outline[2]), (0, -1, outline[0]), (1, 1, outline[3]), (1, -1, outline[1])):
        name = f"{'+' if sign > 0 else '-'}{AXIS_NAMES[axis]}"
        centroid = edge - sign * case["patch"] / 2
        other = 1 - axis
        e0, e1 = float(outline[other]), float(outline[other + 2])
        centres = (probe_points(e0 + case["patch"] / 2, e1 - case["patch"] / 2, step, ((e0 + e1) / 2,))
                   if e1 - e0 > case["patch"] + EPS else [(e0 + e1) / 2])
        ext = sum(abs(float(np.asarray(a["dir"], float)[axis])) * float(a["range"]) / 2 for a in adjust)
        zi = 1 if axis == 0 else 0
        worst = None
        for sh in probe_points(-ext, ext, step, (0.0,)):
            shift = [0.0, 0.0]
            shift[axis] = round(float(sh), 4)
            support = (float(prim_hi[axis]) if sign > 0 else float(prim_lo[axis])) + float(sh)
            arm = (centroid - support) * sign
            base = {"edge": name, "axis": axis, "sign": sign, "arm": round(arm, 4), "at": round(support, 4),
                    "shift": shift}
            if arm <= EPS:
                rows = [dict(base, stress=0.0)]
            else:
                rings = ac._slice_rings(solid, axis, support)
                half = case["patch"] / 2 + arm
                rows = []
                for c in centres:
                    sigma, props = _section_stress(rings, zi, c - half, c + half, case["force"], arm)
                    row = dict(base, patch_at=round(c, 4), window=[round(c - half, 4), round(c + half, 4)])
                    if sigma is None:
                        row["stress"] = 1e9
                    else:
                        lo_, hi_ = max(c - half, e0), min(c + half, e1)
                        row.update(stress=round(sigma, 4), I=round(props["I"], 2), c=round(props["c"], 4),
                                   area=round(props["area"], 2), width=round(hi_ - lo_, 4))
                    rows.append(row)
            for row in rows:
                if worst is None or row["stress"] > worst["stress"] + 1e-9:
                    worst = row
        out.append(worst)
    return out


def stress_at(solid, row: Mapping[str, Any], case: Mapping[str, float]) -> Optional[float]:
    """The bending stress of the load case on `solid` at one evaluated position (an edge_stresses row: the same
    section plane, window and arm). None when the row carries no section."""
    if "window" not in row or row.get("arm", 0.0) <= EPS:
        return None
    axis = int(row["axis"])
    zi = 1 if axis == 0 else 0
    sigma, _ = _section_stress(ac._slice_rings(solid, axis, float(row["at"])), zi, float(row["window"][0]),
                               float(row["window"][1]), case["force"], float(row["arm"]))
    return sigma


def plate_solid_without(st, roles: Sequence[str], seg: Optional[int] = None):
    """The plate body with the cuts of the given roles left out (R12 review 2 N9: what the section would carry
    without that cut)."""
    drop = set(roles)
    nodes = [n for n in st.graph if (n.id == BODY or n.body == BODY) and not (n.kind == "cut" and n.role in drop)]
    sub = fg.FeatureGraph(nodes)
    return fg.body_solid(sub, BODY, sub.resolve({}, st.rules.values))


def cut_roles(st) -> List[str]:
    return sorted({n.role for n in st.graph if n.body == BODY and n.kind == "cut" and n.role})


def section_loss(worst: Mapping[str, Any], case: Mapping[str, float], uncut, without: Mapping[str, Any]) -> dict:
    """R12 review 2 (N9): how much of the worst stress each cut role adds at that section (the stress with every
    cut, less the stress with that role's cuts left out), and the stress of the uncut plate there."""
    base = stress_at(uncut, worst, case) if uncut is not None else None
    rows = []
    for role, solid in without.items():
        v = stress_at(solid, worst, case)
        if v is not None:
            rows.append({"cut": role, "stress_without": round(v, 3), "adds": round(worst["stress"] - v, 3)})
    rows.sort(key=lambda x: -x["adds"])
    return {"uncut": None if base is None else round(base, 3), "by_cut": rows}


def loss_words(loss: Optional[Mapping[str, Any]]) -> str:
    if not loss or loss.get("uncut") is None:
        return ""
    parts = [f"{r['cut']} +{r['adds']:.1f}" for r in loss["by_cut"] if r["adds"] > 0.05]
    return (f"; section loss at that section: the uncut plate would carry {loss['uncut']:.2f} MPa"
            + (f", the cuts add (MPa): {', '.join(parts)}" if parts else ""))


def stresses(st, solid, case: Mapping[str, float]) -> List[dict]:
    placed = st.placed.get(A.PRIMARY)
    lo, hi = fg.instance_world_bbox(placed.inst, placed.pose)
    return edge_stresses(solid, st.plate["outline"], st.plate["adjust"], lo, hi, case,
                         float(st.rules.values["stress_probe_step"]))


def mirror_reference(st) -> Optional[dict]:
    """The engaged reference part's mirror_pair plane in the world frame, when its catalogue entry declares one."""
    m = (st.plate or {}).get("mate")
    if not m:
        return None
    part = st.catalog.get(m["part"])
    mp = part.data.get("mirror_pair")
    if not mp:
        return None
    inst = st.catalog.instantiate(m["part"], {})
    plane = _world(inst.datums[mp["plane"]], np.asarray(m["pose"], float))
    return {"at": list(map(float, plane.at)), "normal": list(map(float, plane.normal)), "part": m["part"]}


def mirrored(solid, plane: Mapping[str, Any]):
    p = np.asarray(plane["at"], float)
    return solid.translate(list(-p)).mirror(list(plane["normal"])).translate(list(p))


# ---------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------


def build_plan(st: "A.AssemblyState") -> ac.Plan:
    """The plate's check set (in place of the shell's build_plan)."""
    import forms
    r, s, res, g, p = st.rules.values, st.spec, st.resolved, st.graph, st.plate
    seg = res.segments()
    plan = ac.Plan(tol=ac.Tol.from_rules(r), seg=seg)
    vols = plan.volumes
    prim = A.primary_item(st)
    ch = p["chain"]
    bodies_ = [BODY] + ([FRAME] if p.get("frame") else [])
    plan.add("separable", "separable", f"{' and '.join(bodies_)} {'are each' if len(bodies_) > 1 else 'is'} one shell",
             bodies=bodies_, overlap_max=r["overlap_max"])
    for u in st.unplaced:
        plan.add(f"content_placed_{u['id']}", "content_placed", f"{u['id']} ({u['part']} x{u['quantity']}) is placed in "
                 "the design", item=u["id"], part=u["part"], reason=u["reason"], parts=[u["part"]])
    refs = {n.id: fg.solid(n, res) for n in g.references()}
    plan.references = {n.id: n.part for n in g.references()}
    for nid, solid in refs.items():
        plan.labels[nid] = g.nodes[nid].part
    board = st.placed.get(A.PRIMARY).node_id
    vols["primary"] = refs[board]
    plan.sources["primary"] = [board]
    plan.add("clear_primary", "clear_of", f"the plate does not enter the {prim['part']} (its face bears on the plate: "
             "designed contact)", volume="primary", clearance=0.0, parts=[prim["part"]])
    fast = [k for k in refs if k.startswith("bolt_")]    # a catalogue nut is its corner-circle envelope: nut_trap measures it
    vols["fasteners"] = _union([refs[k] for k in fast])
    plan.sources["fasteners"] = fast
    plan.parts["fasteners"] = {k: refs[k] for k in fast}
    plan.add("clear_fasteners", "clear_of", "the bolts pass their slots without entering the plate (a shank in its slot: "
             "designed contact)", volume="fasteners", clearance=0.0, parts=[ch["bolt"]])
    shifts = _shifts([(np.asarray(a["dir"]), a["range"]) for a in p["adjust"]])
    for x in p["recess"]:
        prim_inst = st.placed.get(A.PRIMARY).inst
        ko = next(k for k in prim_inst.keepouts if k.id == x["keepout"])
        base = _solid_of(ko, seg).transform(fg._m3(np.asarray(st.placed.get(A.PRIMARY).pose, float)))
        name = f"keepout_{x['keepout']}"
        vols[name] = _union([base.translate(list(sh)) for sh in shifts])
        plan.sources[name] = [board]
        plan.add(f"clear_{x['keepout']}", "clear_of", f"the {prim['part']}'s {x['keepout']} keep-out stays open at every "
                 "position of its adjustment range", volume=name, clearance=0.0, parts=[prim["part"]],
                 names=pt.keepout_names(prim_inst.part, x["keepout"]))
    if p.get("mate"):
        m = p["mate"]
        mate = dict(m, inst=st.catalog.instantiate(m["part"], {}))
        vols["engaged"] = refs[m["id"]]
        plan.sources["engaged"] = [m["id"]]
        plan.add(f"clear_{m['id']}", "clear_of", f"the plate does not enter the {m['part']} (the plate's underside on "
                 "its mating plane: designed contact)", volume="engaged", clearance=0.0, parts=[m["part"]])
        hand_vols = []
        for ko in reference_keepouts(st, mate, shifts, seg):
            name = f"keepout_{m['id']}_{ko['id']}"
            hand_vols.append([name, 0.0])
            vols[name] = ko["solid"]
            plan.sources[name] = [m["id"]]
            how = (f", swept over the adjustment range{' and its ' + str(ko['angles']) + '-step rotation' if ko['swept'] else ''}")
            if ko["contact"]:
                plan.add(f"clear_{m['id']}_{ko['id']}", "clear_of", f"nothing printed enters the {m['part']}'s "
                         f"{ko['id']} keep-out{how} (it meets the mating plane from below: designed contact)",
                         volume=name, clearance=0.0, parts=[m["part"]], names=ko["names"])
            else:
                need = keepout_clearance(st, ko)
                hand_vols[-1][1] = need
                built = (f" (the keep-out already holds the catalogue's {ko['margin']:g} mm margin)" if ko["margin"] > EPS
                         else "")
                plan.add(f"clear_{m['id']}_{ko['id']}", "clear_of", f"the plate stays {need:g} mm from the "
                         f"{m['part']}'s {ko['id']} keep-out{how}{built}", volume=name, clearance=need,
                         slots=("ref_clearance",), parts=[m["part"]], names=ko["names"])
        mref = mirror_reference(st)
        if mref is not None:
            plan.add(f"{HANDEDNESS}_{BODY}", HANDEDNESS, f"one part serves both sides of the {mref['part']} mirror pair "
                     "(its mirror image clears the same keep-outs), or a mirror pair is declared",
                     plane=mref, volumes=hand_vols, decision=p["handedness"], parts=[m["part"]],
                     names=pt.mirror_names(st.catalog.get(m["part"])))
    for i, a in enumerate(p["adjust"]):
        if a["range"] <= EPS:
            continue
        d = np.asarray(a["dir"], float)
        name = f"travel_{i}"
        fsol = vols["fasteners"] if not p.get("frame") else _union([vols["fasteners"], plate_solid(st, seg, FRAME)])
        vols[name] = _union([fsol.translate(list(d * a["range"] * f)) for f in (-0.5, -0.25, 0.25, 0.5)])
        plan.sources[name] = fast
        axis = AXIS_NAMES[int(np.argmax(np.abs(d)))]
        conflict = "" if a["covered"] >= a["range"] - float(r["measure_tol"]) or retention_actions_possible(st) else (
            f"the {prim['part']} declares {a['range']:g} mm of adjustment along {axis}, but a captive hex nut stops "
            f"turning only while it slides along one direction (the slots cover {p['slide']['range']:g} mm along "
            f"{AXIS_NAMES[int(np.argmax(np.abs(p['slide']['dir'])))]}); a requirement question: accept the covered axis, "
            "or a nut plate / threaded insert the catalogue does not hold")
        plan.add(f"travel_{axis}", "travel", f"the bolts move through the {prim['part']}'s full "
                 f"{a['range']:g} mm adjustment along {axis} without entering the plate (slots and nut channels "
                 f"cover {a['covered']:g} mm)", volume=name, clearance=0.0, conflict=conflict,
                 parts=[prim["part"], ch["bolt"]], slots=ADJUST_SLOTS)
    for k, h in enumerate(p["holes"] if p.get("into") else []):
        plan.add(f"bolt_engagement_{k}", "bolt_engagement", f"bolt_{k} engages at least {p['engagement_min']:.2g} mm of "
                 "the part's tapped hole", value=p["engagement"] - p["engagement_min"], limit=0.0,
                 detail=f"design check: engagement {p['engagement']:.2f} mm ({ch['bolt']} {ch['length']:g} mm through "
                        f"{p['z_bot'] + p['thickness'] - p['z_face']:.2f} mm of plate)", parts=[ch["bolt"]])
        plan.add(f"bolt_bottoming_{k}", "bolt_engagement", f"bolt_{k} does not bottom in the part's tapped hole",
                 value=ch["depth"] - p["engagement"], limit=0.0, detail=f"design check: engagement "
                 f"{p['engagement']:.2f} mm vs thread depth {ch['depth']:g} mm", parts=[ch["bolt"]])
    for k, h in enumerate([] if p.get("into") else p["holes"]):
        plan.add(f"bolt_engagement_{k}", "bolt_engagement", f"bolt_{k} engages its nut over the nut's whole thickness",
                 value=p["tip"] - p["nut_top"], limit=0.0, detail=f"design check: tip z {p['tip']:.3f} vs nut top "
                 f"{p['nut_top']:.3f} ({ch['bolt']} {ch['length']:g} mm)", parts=[ch["bolt"], ch["nut"]])
        plan.add(f"bolt_tip_{k}", "bolt_tip", f"bolt_{k}'s tip stays below the plate's top face",
                 value=p["z_top"] - p["tip"], limit=0.0, detail=f"design check: top face z {p['z_top']:.3f} vs tip "
                 f"{p['tip']:.3f}", parts=[ch["bolt"]])
        nd = ch["nut_params"]
        plan.add(f"nut_trap_{k}", "nut_trap", f"nut_{k} sits in a hex channel {r['nut_trap_clearance_min']:g}-"
                 f"{r['nut_trap_clearance_max']:g} mm per flat side, narrower than its corners (it cannot turn)",
                 body=BODY, xy=[h[0], h[1]], z=p["z_nut"] + nd["thickness"] / 2, across=[-p["slide"]["dir"][1],
                 p["slide"]["dir"][0]], flats=nd["across_flats"], corners=nd["across_corners"],
                 lo=r["nut_trap_clearance_min"], hi=r["nut_trap_clearance_max"], parts=[ch["nut"]])
    fr = p.get("frame")
    if fr:
        diag = math.hypot(*fr["size"])
        plan.add("nut_frame_turn", "nut_frame_turn", "the nut frame cannot turn in its pocket (its diagonal is longer than "
                 "the pocket is wide), so the nuts it holds cannot turn either", value=diag - min(fr["pocket"]),
                 limit=0.0, detail=f"design check: frame diagonal {diag:.2f} mm vs pocket width {min(fr['pocket']):.2f} mm",
                 parts=[ch["nut"]])
        plan.add(f"printable_{FRAME}", "printable", "the nut frame prints flat without supports", body=FRAME,
                 orientation=ORIENTATIONS[0], overhang_angle_deg=r["overhang_angle_deg"], bridge_max=r["bridge_max"])
    add_clamp_checks(st, plan)
    add_thin_checks(st, plan)
    for i, axis in enumerate(("x", "y")):
        lo, hi = spec(st, "size_min"), spec(st, "size_max")
        if lo is not None or hi is not None:
            plan.add(f"plate_size_{axis}", "plate_size", f"the plate's plan length along {axis} lies in "
                     f"[{lo if lo is not None else '-'}, {hi if hi is not None else '-'}] mm", body=BODY, axis=i,
                     lo=lo, hi=hi, slots=("size_min", "size_max"))
    if spec(st, "thickness_min") is not None or spec(st, "thickness_max") is not None:
        plan.add("plate_thickness", "plate_thickness", "the plate's thickness (raised features not counted) lies in its "
                 "band", body=BODY, z_bot=p["z_bot"], lo=spec(st, "thickness_min"), hi=spec(st, "thickness_max"),
                 outline=p["outline"], slots=("thickness_min", "thickness_max"))
    if spec(st, "bearing_area_min") is not None:
        on = f" of the {p['mate']['part']}" if p.get("mate") else ""
        plan.add("bearing_area", "bearing_area", f"the plate's underside bears on at least {spec(st, 'bearing_area_min'):g}"
                 f" mm2 of flat area{on}", body=BODY, z=p["z_bot"], limit=spec(st, "bearing_area_min"),
                 engaged=bool(p.get("mate")), slots=("bearing_area_min",))
    case = load_case(st)
    if case is not None:
        # R12 review 2 (N9): the plate without each cut role (and uncut), so the sensor can say what each cut costs
        vols["plate_uncut"] = plate_solid_without(st, cut_roles(st), seg)
        for role in cut_roles(st):
            vols[f"plate_without_{role}"] = plate_solid_without(st, [role], seg)
        plan.add("load_stress", "load_stress", f"the load case ({case['force']:g} N on a {case['patch']:g} mm patch at "
                 f"each outer edge, carried by the {prim['part']} footprint) bends the plate at most {case['allow']:.4g} "
                 "MPa (worst case over the adjustment range)", body=BODY, case=case,
                 plate={k: p[k] for k in ("outline", "adjust")}, tol=float(r["stress_tol"]),
                 capped=bool((p.get("load") or {}).get("capped")), thickness=p["thickness"],
                 step=float(r["stress_probe_step"]), cut_roles=cut_roles(st),
                 slots=("load_force", "load_patch", "strength", "safety_factor"))
    plan.add("printable", "printable", f"the plate prints {p['orientation'].replace('_', ' ')} without supports (no "
             f"overhang steeper than {r['overhang_angle_deg']:g} deg from vertical, no bridge longer than "
             f"{r['bridge_max']:g} mm)", body=BODY, orientation=p["orientation"],
             overhang_angle_deg=r["overhang_angle_deg"], bridge_max=r["bridge_max"])
    add_surface_checks(st, plan)
    plan.add("bbox", "bbox_within", f"the plate (with its raised features) fits within {s['max_x']:g} x {s['max_y']:g} x "
             f"{s['max_z']:g} mm", max=[s["max_x"], s["max_y"], s["max_z"]], x_longest=False,
             slots=("max_x", "max_y", "max_z"))
    forms.add_form_checks(st, plan)
    return plan


def add_surface_checks(st, plan: ac.Plan) -> None:
    """surface_features: only when ParseSpec mapped a raised-feature slot from the text (the text asks for them): the
    features' count, height band, edge distance and spread over the face (convex hull of the features / plan area)."""
    names = FEATURE_SLOTS
    if not any(spec(st, k) is not None for k in names):
        return
    p = st.plate
    plan.add("surface_features", "surface_features", "the free face carries the raised features the text asks for "
             "(count, height, edge distance, spread)", features=list(p.get("features") or []), outline=p["outline"],
             count=spec(st, "feature_count_min"), h_lo=spec(st, "feature_height_min"),
             h_hi=spec(st, "feature_height_max"), edge=spec(st, "feature_edge_min"),
             coverage=spec(st, "feature_coverage_min"), kind=p["surface"], slots=names)


def _bodies_plate(bodies):
    return bodies[BODY] if BODY in bodies else ac.union(list(bodies.values()))


def travel_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the bolts swept over the declared adjustment along one axis against the plate (clear_of, clearance 0);
    an axis the plant cannot cover carries a typed conflict (a requirement question, never actuated)."""
    res = ac.clear_of(_bodies_plate(bodies), plan.volumes[a["volume"]], a["clearance"], plan.tol, check_id=cid,
                      what=a["volume"])
    res.type = typ
    res.evidence["basis"] = MEASURED
    if a.get("conflict") and not res.passed:
        res.evidence.update(conflict=a["conflict"], competing_rule="nut_trap")
        res.evidence["detail"] = f"{res.evidence.get('detail', '')}; conflict: {a['conflict']}"
    return res


def value_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    res = ac.value_at_least(cid, typ, a["value"], a["limit"], plan.tol, a.get("detail", ""))
    res.evidence["basis"] = DESIGN
    return res


def nut_trap_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the plate's section at the nut's mid height; the opening round the nut axis; its width across the
    sliding direction through the axis; clearance per flat side in the band and the width below the nut's corners."""
    from shapely.geometry import LineString, Point, Polygon
    solid = ac.union(list(bodies.values()))       # the trap is the plate's channel or the nut frame's hole
    rings = [np.asarray(q, float) for q in solid.slice(float(a["z"])).to_polygons() if len(q) >= 3]
    pt_ = Point(a["xy"])
    hole = None
    for ring in rings:
        poly = Polygon(ring)
        if poly.is_valid and poly.contains(pt_) and (hole is None or poly.area < hole.area):
            area = sum(r[:, 0] @ np.roll(r[:, 1], -1) - np.roll(r[:, 0], -1) @ r[:, 1] for r in [ring]) / 2
            if area < 0:                       # a clockwise ring is a hole of the section
                hole = poly
    if hole is None:
        return ac._result(cid, typ, False, -1.0, "mm", {"detail": "no opening round the nut axis at its mid height",
                                                        "basis": MEASURED})
    d = np.asarray(a["across"], float)
    far = 1e3
    line = LineString([tuple(np.asarray(a["xy"]) - d * far), tuple(np.asarray(a["xy"]) + d * far)])
    seg_ = line.intersection(hole)
    width = seg_.length if not seg_.is_empty else 0.0
    if seg_.geom_type == "MultiLineString":
        width = next((s.length for s in seg_.geoms if s.distance(pt_) < 1e-6), width)
    per_side = (width - a["flats"]) / 2
    ok = a["lo"] - plan.tol.measure <= per_side <= a["hi"] + plan.tol.measure and width < a["corners"]
    margin = min(per_side - a["lo"], a["hi"] - per_side, a["corners"] - width) / plan.tol.scale
    return ac._result(cid, typ, ok, margin, "mm", {"value": round(per_side, 4), "width": round(width, 4),
                      "detail": f"channel width {width:.3f} mm across the slide at the nut axis: {per_side:.3f} per flat "
                                f"side (band {a['lo']:g}-{a['hi']:g}), corners {a['corners']:g}", "basis": MEASURED})


def band_result(cid, typ, value, lo, hi, plan, detail, basis=MEASURED) -> cc.CheckResult:
    if lo is None:
        res = ac.value_at_most(cid, typ, value, hi, plan.tol, detail)
    elif hi is None:
        res = ac.value_at_least(cid, typ, value, lo, plan.tol, detail)
    else:
        res = ac.value_in_band(cid, typ, value, lo, hi, plan.tol, detail)
    res.evidence["basis"] = basis
    return res


def plate_size_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the plate body's plan extent along the axis (raised features included: they stand inside it)."""
    b = _bodies_plate(bodies).bounding_box()
    v = float(b[3 + a["axis"]] - b[a["axis"]])
    return band_result(cid, typ, v, a["lo"], a["hi"], plan, f"plan length {v:.3f} mm")


def plate_thickness_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the height of the plate's top face above its underside, read at the outline's corners (raised
    features stand inside the edge distance, so a corner column sees the plate only)."""
    solid = _bodies_plate(bodies)
    x0, y0, x1, y1 = a["outline"]
    w = 0.5
    tops = []
    for cx, cy in ((x0 + w, y0 + w), (x1 - w, y0 + w), (x1 - w, y1 - w), (x0 + w, y1 - w)):
        col = ac.m3d.Manifold.cube([w, w, 1e3]).translate([cx - w / 2, cy - w / 2, a["z_bot"] - 1])
        inter = solid ^ col
        if not inter.is_empty():
            tops.append(float(inter.bounding_box()[5]) - a["z_bot"])
    v = min(tops) if tops else 0.0
    return band_result(cid, typ, v, a["lo"], a["hi"], plan, f"thickness {v:.3f} mm at the corners")


def bearing_area_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured (review fix N7): the area where the plate's section just above its underside overlaps the engaged
    reference part's section just below it (what it really bears on); with no engaged reference, the underside area."""
    d = 10 * plan.tol.measure
    under = section(_bodies_plate(bodies), float(a["z"]) + d)
    ref = plan.volumes.get("engaged") if a.get("engaged") else None
    if ref is not None:
        v = float(under.intersection(section(ref, float(a["z"]) - d)).area)
        what = "underside area on the engaged part"
    else:
        v = float(under.area)
        what = "underside area"
    res = ac.value_at_least(cid, typ, v, a["limit"], plan.tol, f"{what} {v:.1f} mm2")
    res.evidence["basis"] = MEASURED
    return res


def section(solid, z: float):
    """The solid's horizontal section at z as one shapely geometry (rings combined even-odd, so holes stay holes)."""
    from shapely.geometry import Polygon
    from shapely.geometry import GeometryCollection
    out = GeometryCollection()
    for ring in solid.slice(float(z)).to_polygons():
        if len(ring) >= 3:
            poly = Polygon(ring).buffer(0)
            if not poly.is_empty:
                out = out.symmetric_difference(poly)
    return out


def _rings_geom(rings: Sequence[np.ndarray]):
    from shapely.geometry import Polygon
    from shapely.geometry import GeometryCollection
    out = GeometryCollection()
    for ring in rings:
        if len(ring) >= 3:
            poly = Polygon(ring).buffer(0)
            if not poly.is_empty:
                out = out.symmetric_difference(poly)
    return out


def fastener_face(kind: str, size: float, centre: Sequence[float], angle_deg: float):
    """The bearing face of a nut (hex, `size` across flats, flats parallel to angle_deg) or a head (circle of diameter
    `size`) at `centre`, as a shapely polygon."""
    from shapely.geometry import Point, Polygon
    if kind == "hex":
        return Polygon(_poly_world(hex_channel(0.0, size), centre, angle_deg))
    return Point(centre).buffer(size / 2, 64)


def seat_bearing(support, face, hole_d: float, axis_xy: Sequence[float]) -> dict:
    """How a fastener face bears on a support section: the nominal face less its bolt clearance hole, the part of it on
    the support (area, ratio) and whether the bolt axis lies inside the convex hull of the bearing (else the fastener
    tips into the opening)."""
    from shapely.geometry import Point
    nominal = face.difference(Point(axis_xy).buffer(hole_d / 2, 64))
    bear = support.intersection(nominal) if not support.is_empty else support
    area = float(bear.area)
    hull = bear.convex_hull if area > 0 else None
    inside = bool(hull is not None and hull.buffer(1e-6).contains(Point(axis_xy)))
    return {"area": area, "nominal": float(nominal.area), "ratio": area / max(float(nominal.area), EPS), "axis_inside": inside}


ADJUST_SLOTS = ("adjust_min", "adjust_cross_min")


def _covered_shifts(p: Mapping[str, Any]) -> List[List[float]]:
    return [[float(v[0]), float(v[1])] for v in _shifts([(np.asarray(a["dir"], float), float(a["covered"]))
                                                         for a in p["adjust"]])]


def _all_shifts(p: Mapping[str, Any]) -> List[List[float]]:
    return [[float(v[0]), float(v[1])] for v in _shifts([(np.asarray(a["dir"], float), float(a["range"]))
                                                         for a in p["adjust"]])]


def add_clamp_checks(st: "A.AssemblyState", plan: ac.Plan) -> None:
    """Review fix B1: the clamp path, measured. For every bolt at every adjustment extreme the face that tightening
    presses on printed material must bear on it: a nut on the plate's floor or the nut frame's floor (clamp_seat_<k>),
    a screw head on the plate's free face (clamp_seat_<k>, screws into a tapped part), the nut frame on the plate's
    pocket floor beside the slots (clamp_frame) and the bolted part's face on the plate round its bolts (clamp_face):
    at least rules.clamp_bearing_ratio_min of the face's nominal bearing area, with the bolt axis inside the bearing's
    convex hull (a seat on one side tips the fastener into the opening). Linked to the adjustment slots and the
    fastener parts (the deterministic trace)."""
    p, r = st.plate, st.rules.values
    ch = p["chain"]
    prim = A.primary_item(st)
    bd, nd = ch["bolt_params"], ch["nut_params"]
    ratio = float(r["clamp_bearing_ratio_min"])
    u = p["slide"]["dir"]
    ang = math.degrees(math.atan2(u[1], u[0]))
    covered, every = _covered_shifts(p), _all_shifts(p)
    holes = [[float(h[0]), float(h[1])] for h in p["holes"]]
    if p.get("into"):
        for k, h in enumerate(holes):
            plan.add(f"clamp_seat_{k}", "clamp_seat", f"bolt_{k}'s head bears on the plate's free face at every position "
                     f"of the adjustment (at least {ratio:.0%} of its bearing face, round the axis)", xy=h,
                     z=p["z_top"], side="below", face="circle", size=bd["head_diameter"],
                     hole=bd["clearance_diameter"], angle=ang, shifts=covered, ratio=ratio, slots=ADJUST_SLOTS,
                     parts=[ch["bolt"]])
            add_bearing_check(st, plan, k, h, p["z_top"], "circle", bd["head_diameter"], ang, covered, [ch["bolt"]],
                              f"bolt_{k}'s head")
        return
    frame = p.get("frame")
    for k, h in enumerate(holes):
        where = "the nut frame's floor" if frame else "the plate's floor beside its slot"
        plan.add(f"clamp_seat_{k}", "clamp_seat", f"nut_{k} bears on {where} at every position of the adjustment (at "
                 f"least {ratio:.0%} of its bearing face, round the bolt axis), so tightening clamps instead of pulling "
                 "it through", xy=h, z=p["z_nut"], side="below", face="hex", size=nd["across_flats"],
                 hole=bd["clearance_diameter"], angle=ang, shifts=[[0.0, 0.0]] if frame else covered, ratio=ratio,
                 slots=ADJUST_SLOTS, parts=[ch["nut"], ch["bolt"]])
        add_bearing_check(st, plan, k, h, p["z_nut"], "hex", nd["across_flats"], ang,
                          [[0.0, 0.0]] if frame else covered, [ch["nut"], ch["bolt"]], f"nut_{k}")
    nut_face = fastener_face("hex", nd["across_flats"], (0.0, 0.0), 0.0)
    from shapely.geometry import Point
    nut_nominal = float(nut_face.difference(Point(0.0, 0.0).buffer(bd["clearance_diameter"] / 2, 64)).area)
    if frame:
        plan.add("clamp_frame", "clamp_frame", f"the nut frame bears on the plate's pocket floor beside the slots at every "
                 f"position of the adjustment (at least {ratio:.0%} of its nuts' bearing faces, round every bolt axis)",
                 z=p["z_pocket"], holes=holes, shifts=every, nominal=len(holes) * nut_nominal, ratio=ratio,
                 slots=ADJUST_SLOTS, parts=[ch["nut"], ch["bolt"]])
    head = fastener_face("circle", bd["head_diameter"], (0.0, 0.0), 0.0)
    head_nominal = float(head.difference(Point(0.0, 0.0).buffer(bd["clearance_diameter"] / 2, 64)).area)
    plan.add("clamp_face", "clamp_face", f"the {prim['part']}'s bolted face bears on the plate round its bolts at every "
             f"position of the adjustment (at least {ratio:.0%} of the heads' bearing faces, round every bolt axis)",
             z=p["z_face"], holes=holes, shifts=covered, nominal=len(holes) * head_nominal, ratio=ratio,
             slots=ADJUST_SLOTS, parts=[prim["part"], ch["bolt"]])


def add_bearing_check(st, plan: ac.Plan, k: int, xy, z: float, face: str, size: float, angle: float, shifts,
                      parts, what: str) -> None:
    """R12 review 2 (N4): fastener_bearing_<k>, the seat of a nut or a head under its preload (fastener_load)."""
    p, r = st.plate, st.rules.values
    fl = p.get("fastener_load") or fastener_load(st)
    plan.add(f"fastener_bearing_{k}", "fastener_bearing", f"{what} under its {fl['preload']:.0f} N preload neither "
             f"crushes the printed seat (bearing pressure at most {fl['allow_bearing']:.3g} MPa) nor punches through "
             f"the printed floor round it (shear at most {fl['allow_shear']:.3g} MPa), at every position of the "
             "adjustment", xy=list(xy), z=float(z), face=face, size=float(size),
             hole=float(p["chain"]["bolt_params"]["clearance_diameter"]), angle=float(angle), shifts=shifts,
             preload=fl["preload"], allow_bearing=fl["allow_bearing"], allow_shear=fl["allow_shear"],
             preload_source=fl["preload_source"], step=float(r["layer_height"]) or float(r["thin_probe_step"]),
             no_action=bool(p.get("into")) or not retention_actions_possible(st),
             slots=("fastener_preload", "strength", "safety_factor"), parts=list(parts))


def fastener_bearing_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured on the printed body the face bears on (the one with the most material just below it): the bearing
    pressure = preload / the face's area on that section (less its bolt hole), and the punch-through shear = preload /
    the shear area, the face's outline times the printed material directly under it (horizontal sections every `step`
    from the seat down, the outline's length inside each, until a section has none: the floor's contiguous depth), at
    every adjustment position; the worst of pressure / allowed and shear / allowed must not exceed 1."""
    d = 5 * plan.tol.measure
    z = float(a["z"])
    c0 = (a["xy"][0], a["xy"][1])
    face0 = fastener_face(a["face"], a["size"], c0, a["angle"])
    pick = max(bodies.items(), key=lambda kv: float(section(kv[1], z - d).intersection(face0).area))
    name, solid = pick
    zmin = float(solid.bounding_box()[2])
    n = max(1, int(math.ceil((z - zmin) / max(float(a["step"]), EPS) - 1e-9)))
    dz = (z - zmin) / n
    secs = [section(solid, z - (i + 0.5) * dz) for i in range(n)]
    top = section(solid, z - d)
    rows = []
    for sh in a["shifts"]:
        c = (c0[0] + sh[0], c0[1] + sh[1])
        face = fastener_face(a["face"], a["size"], c, a["angle"])
        bear = seat_bearing(top, face, a["hole"], c)
        line = face.exterior
        shear, depth = 0.0, 0.0
        for sec in secs:
            length = float(line.intersection(sec).length) if not sec.is_empty else 0.0
            if length <= EPS:
                break
            shear += length * dz
            depth += dz
        pressure = a["preload"] / bear["area"] if bear["area"] > EPS else math.inf
        tau = a["preload"] / shear if shear > EPS else math.inf
        ratio = max(pressure / a["allow_bearing"], tau / a["allow_shear"])
        rows.append({"shift": [round(v, 3) for v in sh], "bearing_area": round(bear["area"], 3),
                     "pressure": round(pressure, 3) if math.isfinite(pressure) else None,
                     "shear_area": round(shear, 3), "floor_depth": round(depth, 3),
                     "shear": round(tau, 3) if math.isfinite(tau) else None, "ratio": ratio})
    worst = max(rows, key=lambda x: x["ratio"])
    ok = worst["ratio"] <= 1.0 + 1e-9
    fmt = lambda v: "inf" if v is None else f"{v:.2f}"
    detail = (f"{name} seat under a {a['preload']:.0f} N preload ({a['preload_source']}): bearing pressure "
              f"{fmt(worst['pressure'])} MPa on {worst['bearing_area']:.1f} mm2 (allowed {a['allow_bearing']:.2f}), "
              f"punch-through shear {fmt(worst['shear'])} MPa on {worst['shear_area']:.1f} mm2 (the face outline over "
              f"{worst['floor_depth']:.2f} mm of floor; allowed {a['allow_shear']:.2f}) at shift {worst['shift']}")
    ratio = worst["ratio"] if math.isfinite(worst["ratio"]) else 1e9
    ev = {"value": round(ratio, 4), "limit": 1.0, "body": name, "positions": len(rows),
          "worst": {k: v for k, v in worst.items() if k != "ratio"}, "basis": MEASURED, "detail": detail}
    if not ok and a.get("no_action"):          # no retention option left to change the seat: a requirement question
        ev["conflict"] = (f"the {name} seat carries {worst['ratio']:.2f} x what the printed material allows under the "
                          f"{a['preload']:.0f} N preload ({a['preload_source']}), and no buildable retention option "
                          "changes the seat: a requirement question (a stated lower preload, a stronger material, a "
                          "washer or a nut plate the catalogue does not hold)")
        ev["competing_rule"] = "fastener_preload"
        ev["detail"] += f"; conflict: {ev['conflict']}"
    return ac._result(cid, typ, ok, 1.0 - min(ratio, 1e9), "ratio", ev)


def _clamp_result(cid, typ, rows, ratio, plan, what) -> cc.CheckResult:
    worst = min(rows, key=lambda x: (x["axis_inside"], x["ratio"]))
    ok = all(x["axis_inside"] for x in rows) and min(x["ratio"] for x in rows) >= ratio - 1e-9
    margin = (min(x["ratio"] for x in rows) - ratio) if all(x["axis_inside"] for x in rows) else -1.0
    detail = (f"{what}: worst {worst['ratio']:.0%} of the nominal bearing ({worst['area']:.1f} of {worst['nominal']:.1f}"
              f" mm2) at shift {worst['shift']}, axis {'inside' if worst['axis_inside'] else 'OUTSIDE'} the bearing "
              f"(need >= {ratio:.0%}, axis inside)")
    return ac._result(cid, typ, ok, margin, "ratio", {"value": round(worst["ratio"], 4), "limit": ratio,
                      "area": round(worst["area"], 3), "positions": len(rows), "basis": MEASURED, "detail": detail})


def clamp_seat_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the printed section just below the fastener's bearing face (all printed bodies: the plate or the nut
    frame), at each adjustment extreme, against the face (seat_bearing)."""
    d = 5 * plan.tol.measure
    sec = section(ac.union(list(bodies.values())), float(a["z"]) - d)
    rows = []
    for sh in a["shifts"]:
        c = (a["xy"][0] + sh[0], a["xy"][1] + sh[1])
        row = seat_bearing(sec, fastener_face(a["face"], a["size"], c, a["angle"]), a["hole"], c)
        rows.append(dict(row, shift=[round(v, 3) for v in sh]))
    return _clamp_result(cid, typ, rows, a["ratio"], plan, "fastener seat")


def _pair_bearing(cid, typ, a, below, above, plan, what) -> cc.CheckResult:
    from shapely import affinity
    from shapely.geometry import Point
    rows = []
    for sh in a["shifts"]:
        moved = affinity.translate(above, sh[0], sh[1])
        bear = below.intersection(moved)
        area = float(bear.area)
        hull = bear.convex_hull.buffer(1e-6) if area > 0 else None
        inside = bool(hull is not None and all(hull.contains(Point(h[0] + sh[0], h[1] + sh[1])) for h in a["holes"]))
        rows.append({"area": area, "nominal": a["nominal"], "ratio": area / max(a["nominal"], EPS),
                     "axis_inside": inside, "shift": [round(v, 3) for v in sh]})
    return _clamp_result(cid, typ, rows, a["ratio"], plan, what)


def clamp_frame_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the plate's section just below the frame's underside against the frame's section just above it,
    moved to each adjustment extreme."""
    d = 5 * plan.tol.measure
    if FRAME not in bodies:
        return ac._result(cid, typ, False, -1.0, "ratio", {"detail": "no nut frame body", "basis": MEASURED})
    return _pair_bearing(cid, typ, a, section(bodies[BODY], float(a["z"]) - d), section(bodies[FRAME], float(a["z"]) + d),
                         plan, "nut frame on the pocket floor")


def clamp_face_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the plate's section just above the bolted part's face against the part's own section just below it,
    moved to each adjustment extreme."""
    d = 5 * plan.tol.measure
    return _pair_bearing(cid, typ, a, section(_bodies_plate(bodies), float(a["z"]) + d),
                         section(plan.volumes["primary"], float(a["z"]) - d), plan, "bolted face on the plate")


def add_thin_checks(st: "A.AssemblyState", plan: ac.Plan) -> None:
    """Review fix N5: thin_feature_<body>: no printed feature thinner than the mapped feature_min (else rules.min_feature,
    two extrusion lines), measured on sections of each printed body; studs: the thread engagement in printed material
    of every catalogue stud (stud_engagement_<k>) against rules.plastic_thread_engagement_ratio thread diameters."""
    p, r = st.plate, st.rules.values
    lim = spec(st, "feature_min")
    limit = float(lim) if lim is not None else float(r["min_feature"])
    for b in [BODY] + ([FRAME] if p.get("frame") else []):
        plan.add(f"thin_feature_{b}", "thin_feature", f"no feature of {b} is thinner than {limit:g} mm (sections along "
                 "x, y and z)", body=b, limit=limit, step=float(r["thin_probe_step"]), slots=("feature_min",))
    fs = p.get("feature_spec") or {}
    if fs.get("kind") == "studs" and fs.get("part"):
        sp = st.catalog.get(fs["part"])
        d = float(sp.params["thread_diameter"]["default"])
        need = float(r["plastic_thread_engagement_ratio"]) * d
        for k, f in enumerate(p.get("features") or []):
            plan.add(f"stud_engagement_{k}", "stud_engagement", f"stud_{k} engages at least {need:g} mm of printed "
                     "material (its tapped hole)", body=BODY, xy=[f["x"], f["y"]], z_top=p["z_top"],
                     depth=fs["depth"], tap=float(sp.params["tap_diameter"]["default"]),
                     major=d, need=need, parts=[fs["part"]])


def thin_feature_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured on sections of the body. Horizontal sections at the middle of every band between two distinct vertex
    heights of the mesh (the plate's features are vertical prisms, so each band's section is exact and a vertical wall
    is cut square): the material a morphological opening with a disc of diameter `limit` removes is thinner than the
    limit in plan. Vertical sections every `step` mm along x and y find horizontal skins: the opening there is along z
    only (the section is stretched horizontally first), because a vertical section grazing a curved wall shows a thin
    sliver that is not thin in 3D. A removed piece longer than the limit (not a corner tip) is a thin feature; reports
    the thinnest (twice its largest inscribed radius) and where."""
    from shapely import affinity
    from shapely.ops import polylabel
    solid = bodies.get(a["body"])
    if solid is None:
        return ac._result(cid, typ, False, -1.0, "mm", {"detail": f"no body {a['body']}", "basis": MEASURED})
    rad = a["limit"] / 2 - plan.tol.measure
    stretch = 1e3
    b = solid.bounding_box()
    zs = np.unique(np.round(_mesh(solid)[0][:, 2], 5))
    probes = [(2, float((z0 + z1) / 2)) for z0, z1 in zip(zs[:-1], zs[1:]) if z1 - z0 > 2 * plan.tol.measure]
    for axis in (0, 1):
        lo, hi = float(b[axis]), float(b[axis + 3])
        n = max(1, int(math.floor((hi - lo) / a["step"])))
        probes += [(axis, lo + (i + 0.5) * (hi - lo) / n) for i in range(n)]
    found = []
    for axis, pos in probes:
        geom = _rings_geom(ac._slice_rings(solid, axis, pos))
        if geom.is_empty:
            continue
        zcol = None if axis == 2 else (1 if axis == 0 else 0)
        if zcol is not None:              # stretch the horizontal coordinate: the disc opening acts along z only
            geom = affinity.scale(geom, xfact=stretch if zcol == 1 else 1.0, yfact=stretch if zcol == 0 else 1.0,
                                  origin=(0, 0))
        opened = geom.buffer(-rad, 32).buffer(rad, 32)
        thin = geom.difference(opened)
        for piece in getattr(thin, "geoms", [thin]):
            if piece.is_empty or piece.geom_type != "Polygon":
                continue
            if zcol is not None:
                piece = affinity.scale(piece, xfact=1 / stretch if zcol == 1 else 1.0,
                                       yfact=1 / stretch if zcol == 0 else 1.0, origin=(0, 0))
            if piece.area < 1e-4:
                continue
            rr = piece.minimum_rotated_rectangle
            xs, ys = rr.exterior.coords.xy
            sides = [math.hypot(xs[j + 1] - xs[j], ys[j + 1] - ys[j]) for j in range(2)]
            if max(sides) <= a["limit"]:
                continue                                  # a corner tip the opening rounds off
            if zcol is not None:
                z_extent = piece.bounds[2 + zcol] - piece.bounds[zcol]
                width = float(z_extent)
            else:
                c = polylabel(piece, tolerance=0.01)
                width = 2.0 * float(piece.exterior.distance(c)) if piece.contains(c) else float(min(sides))
            if width >= a["limit"] - plan.tol.measure:
                continue
            found.append({"axis": AXIS_NAMES[axis], "at": round(pos, 3), "width": round(width, 3),
                          "length": round(max(sides), 3), "where": [round(piece.centroid.x, 3), round(piece.centroid.y, 3)]})
    if not found:
        return ac._result(cid, typ, True, rad, "mm", {"value": None, "limit": a["limit"], "basis": MEASURED,
                          "sections": len(probes), "detail": f"no feature thinner than {a['limit']:g} mm "
                                                             f"({len(probes)} sections)"})
    worst = min(found, key=lambda x: x["width"])
    return ac._result(cid, typ, False, worst["width"] - a["limit"], "mm",
                      {"value": worst["width"], "limit": a["limit"], "count": len(found), "worst": worst,
                       "basis": MEASURED, "detail": f"{len(found)} thin regions; thinnest {worst['width']:.2f} mm (< "
                       f"{a['limit']:g}) in the section at {worst['axis']} = {worst['at']:g}, about "
                       f"{worst['where']} (section coordinates), {worst['length']:.1f} mm long"})


def stud_engagement_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the printed material in the thread zone of the stud's tapped hole (the annulus between the tap drill
    and the thread's major diameter, down from the top face to the hole's depth): its volume over the annulus area is
    the engaged length."""
    solid = bodies.get(a["body"])
    seg = 48
    z0 = a["z_top"] - a["depth"]
    ring = (ac.m3d.Manifold.cylinder(a["depth"], a["major"] / 2, a["major"] / 2, seg)
            - ac.m3d.Manifold.cylinder(a["depth"] + 2, a["tap"] / 2, a["tap"] / 2, seg).translate([0, 0, -1]))
    ring = ring.translate([a["xy"][0], a["xy"][1], z0])
    area = math.pi / 4 * (a["major"] ** 2 - a["tap"] ** 2)
    v = float((solid ^ ring).volume()) / max(area, EPS) if solid is not None else 0.0
    res = ac.value_at_least(cid, typ, v, a["need"], plan.tol, f"thread engagement in printed material {v:.2f} mm "
                            f"(need {a['need']:g})")
    res.evidence["basis"] = MEASURED
    return res


def load_stress_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the worst-case bending stress of the load case at each edge on the section of these bodies
    (edge_stresses: every patch position along the edge, corners included, and every adjustment position, the 45-degree
    width); the primary's footprint is read from the plan's primary volume. A failure with the plate at its thickness
    limit is a typed requirement conflict (review fix B2: the plant has no other structural option, so it is a
    requirement question, never verified). R12 review 2 (N9): the evidence says what each cut role costs at the worst
    section (the design solids without that role's cuts, and uncut), so the controller sees that a retention or recess
    choice costs strength."""
    b = plan.volumes["primary"].bounding_box()
    rows = edge_stresses(_bodies_plate(bodies), a["plate"]["outline"], a["plate"]["adjust"], b[:3], b[3:], a["case"],
                         float(a.get("step", 1.0)))
    worst = max(rows, key=lambda x: x["stress"]) if rows else {"stress": 0.0, "edge": "-"}
    allow = a["case"]["allow"]
    ok = worst["stress"] <= allow + float(a["tol"])
    loss = None
    if "window" in worst and "plate_uncut" in plan.volumes:
        loss = section_loss(worst, a["case"], plan.volumes["plate_uncut"],
                            {r: plan.volumes[f"plate_without_{r}"] for r in a.get("cut_roles") or []
                             if f"plate_without_{r}" in plan.volumes})
    where = (f"edge {worst['edge']}, patch centre at {worst.get('patch_at', 0):.1f} mm along it" if "patch_at" in worst
             else f"edge {worst['edge']}")
    ev = {"value": worst["stress"], "limit": round(allow, 4), "edges": rows, "worst": worst, "basis": MEASURED,
          "section_loss": loss,
          "detail": f"worst bending stress {worst['stress']:.2f} MPa at {where} (arm {worst.get('arm', 0):.2f} mm, "
                    f"section width {worst.get('width', 0):.1f} mm, part shifted {worst.get('shift')}) vs "
                    f"{allow:.2f} MPa{loss_words(loss)}"}
    if not ok and a.get("capped"):
        ev["conflict"] = (f"the load case needs a bending stress of at most {allow:.2f} MPa, but at the largest allowed "
                          f"thickness ({a['thickness']:g} mm, thickness_max) the worst case over the patch positions "
                          f"and the adjustment range is {worst['stress']:.2f} MPa at {where}{loss_words(loss)}: a "
                          "requirement question (a thicker plate, a stronger material, a smaller load or patch, a "
                          "larger support, or a fastener retention or recess that removes less of that section)")
        ev["competing_rule"] = "thickness_max"
        ev["detail"] += f"; conflict: {ev['conflict']}"
    return ac._result(cid, typ, ok, (allow - worst["stress"]) / max(allow, EPS), "ratio", ev)


def printable_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured on these bodies in the declared orientation (overhangs())."""
    rules = {"measure_tol": plan.tol.measure, "overhang_angle_deg": a["overhang_angle_deg"],
             "bridge_max": a["bridge_max"]}
    o = overhangs(bodies[a["body"]] if a.get("body") in bodies else _bodies_plate(bodies), a["orientation"], rules)
    ok = o["violation"] <= plan.tol.measure
    return ac._result(cid, typ, ok, -o["violation"] if not ok else 1.0, "mm",
                      {"value": o["worst_span"], "limit": rules["bridge_max"], "steep_area": o["steep_area"],
                       "regions": o["regions"], "orientation": a["orientation"], "basis": MEASURED,
                       "detail": f"{a['orientation']}: longest bridge {o['worst_span']:.2f} mm (max "
                                 f"{rules['bridge_max']:g}), steep overhang area {o['steep_area']:.2f} mm2"})


def surface_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """A design check on the placed features (their solids are the plate's pins or the catalogue studs)."""
    from shapely.geometry import MultiPoint
    f = a["features"]
    x0, y0, x1, y1 = a["outline"]
    bad = []
    n = len(f)
    if a.get("count") is not None and n < a["count"] - 1e-9:
        bad.append(f"{n} features < {a['count']:g}")
    hs = [x["h"] for x in f]
    if hs and a.get("h_lo") is not None and min(hs) < a["h_lo"] - plan.tol.measure:
        bad.append(f"height {min(hs):.2f} < {a['h_lo']:g}")
    if hs and a.get("h_hi") is not None and max(hs) > a["h_hi"] + plan.tol.measure:
        bad.append(f"height {max(hs):.2f} > {a['h_hi']:g}")
    edge = min((min(x["x"] - x0, x1 - x["x"], x["y"] - y0, y1 - x["y"]) - x["d"] / 2 for x in f), default=None)
    if edge is not None and a.get("edge") is not None and edge < a["edge"] - plan.tol.measure:
        bad.append(f"edge distance {edge:.2f} < {a['edge']:g}")
    cov = 0.0
    if n >= 3:
        cov = 100.0 * MultiPoint([(x["x"], x["y"]) for x in f]).convex_hull.area / max((x1 - x0) * (y1 - y0), EPS)
    if a.get("coverage") is not None and cov < a["coverage"] - 1e-6:
        bad.append(f"spread {cov:.1f} % < {a['coverage']:g} %")
    if not f:
        bad = [f"no raised features on the face (kind {a.get('kind')})"] + bad[1:]
    return ac._result(cid, typ, not bad, 1.0 if not bad else -1.0, "count",   # one requirement, however many shortfalls
                      {"value": n, "coverage": round(cov, 2), "edge": None if edge is None else round(edge, 4),
                       "kind": a.get("kind"), "basis": DESIGN,
                       "detail": "; ".join(bad) if bad else f"{n} {a.get('kind')} features, spread {cov:.1f} %"})


def handedness_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    """Measured: the mirror image of the plate (about the reference's mirror plane) against the same swept keep-outs at
    their clearances; passes when it clears them (one part serves both sides) or a mirror pair is declared (design: the
    left part is the exact mirror image on the mirrored reference)."""
    img = mirrored(_bodies_plate(bodies), a["plane"])
    worst, where, worst_pen = math.inf, None, 0.0
    for name, clearance in a["volumes"]:
        vol = plan.volumes.get(name)
        if vol is None:
            continue
        pen = float((img ^ vol).volume())
        d = -1.0 - pen if pen > plan.tol.pen else float(img.min_gap(vol, clearance + ac.SEARCH_EXTRA)) - clearance
        if d < worst:
            worst, where, worst_pen = d, name, pen
    single_ok = worst >= -plan.tol.measure
    declared = a.get("decision") == "mirror_pair"
    ok = single_ok or declared
    how = (f"penetrates it by {worst_pen:.1f} mm3" if worst < -1.0 + EPS and where else f"margin {worst:.3f} mm")
    detail = (f"mirror image {'clears' if single_ok else 'does not clear'} {where} ({how})"
              + ("; a mirror pair is declared (the left part is the exact mirror image)" if declared else ""))
    return ac._result(cid, typ, ok, 1.0 if ok else -1.0, "count",      # a yes/no requirement: one failing count
                      {"value": round(worst, 4), "declared": a.get("decision"),
                       "basis": DESIGN if declared else MEASURED, "detail": detail, "where": where})


# ---------------------------------------------------------------------------
# Actuators
# ---------------------------------------------------------------------------


def surface_actions(st: "A.AssemblyState", r: cc.CheckResult) -> list:
    """A failing surface_features check (or a failing printable check while printed pins stand on the face): one
    add_surface_feature per buildable option other than the current one and `none`."""
    import controller as C
    cur = control(st, SURFACE)
    if r.type == "printable" and cur == "none":
        return []
    out = []
    for o in surface_options(st):
        if o["name"] in (cur, "none") or not o["feasible"]:
            continue
        out.append(C.Action(kind=SET_SURFACE, target=FACE_TOP, value=o["name"],
                            words=f"{SET_SURFACE} {FACE_TOP}={o['name']}: put raised features on the plate's free face: "
                                  f"{o['meaning']}", targets=[r.check_id], invalidates="derive", evidence=[]))
    return out


def retention_options(st: "A.AssemblyState") -> List[dict]:
    """The nut_retention options with their plant feasibility (the frame needs two or more holes)."""
    opts = dict(((st.rules.building_blocks or {}).get(RETENTION) or {}).get("options") or {})
    n = len((st.plate or {}).get("holes") or [])
    return [{"name": k, "meaning": o.get("meaning", k), "feasible": not (o.get("needs") == "two holes" and n < 2)}
            for k, o in opts.items()]


def retention_actions_possible(st: "A.AssemblyState") -> bool:
    cur = control(st, RETENTION)
    return any(o["feasible"] and o["name"] != cur for o in retention_options(st)) and cur != "frame"


def retention_actions(st: "A.AssemblyState", r: cc.CheckResult) -> list:
    """A failing travel check: one set_nut_retention per buildable option other than the current one."""
    import controller as C
    cur = control(st, RETENTION)
    if cur == "frame":
        return []
    return [C.Action(kind=SET_RETENTION, target=BODY, value=o["name"],
                     words=f"{SET_RETENTION} {BODY}={o['name']}: hold the nuts with {o['name']}: {o['meaning']}",
                     targets=[r.check_id], invalidates="derive", evidence=[])
            for o in retention_options(st) if o["feasible"] and o["name"] != cur]


def apply_retention(st: "A.AssemblyState", action, record: Mapping[str, Any], by: str = "llm:controller") -> None:
    st.control[RETENTION] = action.value
    A.choice(st, f"{RETENTION}[{action.target}]", action.value, by, **dict(record))


def handedness_actions(st: "A.AssemblyState", r: cc.CheckResult) -> list:
    import controller as C
    if control(st, HANDEDNESS) == "mirror_pair":
        return []
    opts = dict(((st.rules.building_blocks or {}).get(HANDEDNESS) or {}).get("options") or {})
    return [C.Action(kind=SET_HANDEDNESS, target=BODY, value="mirror_pair",
                     words=f"{SET_HANDEDNESS} {BODY}=mirror_pair: {opts.get('mirror_pair', {}).get('meaning', '')}",
                     targets=[r.check_id], invalidates="derive", evidence=[])]


def apply_surface(st: "A.AssemblyState", action, record: Mapping[str, Any], by: str = "llm:controller") -> None:
    st.control[SURFACE] = action.value
    A.choice(st, f"{SURFACE}[{action.target}]", action.value, by, **dict(record))


def apply_handedness(st: "A.AssemblyState", action, record: Mapping[str, Any], by: str = "llm:controller") -> None:
    st.control[HANDEDNESS] = action.value
    A.choice(st, f"{HANDEDNESS}[{action.target}]", action.value, by, **dict(record))


def state_lines(st: "A.AssemblyState") -> List[str]:
    """The plate's state words for the controller."""
    p = st.plate or {}
    if not p:
        return []
    ch = p["chain"]
    cov = ", ".join(f"{AXIS_NAMES[int(np.argmax(np.abs(a['dir'])))]} {a['covered']:g} of {a['range']:g} mm"
                    for a in p["adjust"]) or "none declared"
    held = "a sliding nut frame" if p.get("retention") == "frame" else "hex channels"
    if p.get("into"):
        return [f"- plate: {p['size'][0]:.1f} x {p['size'][1]:.1f} x {p['thickness']:.1f} mm, printed "
                f"{p.get('orientation', '?').replace('_', ' ')}; {len(p['holes'])} x {ch['bolt']} {ch['length']:g} mm "
                f"from its free face into the part's tapped holes (adjustment covered: {cov})",
                f"- raised features on the free face: {p['surface']}"] + (
                    [f"- handedness: {p['handedness']}"] if mirror_reference(st) is not None else [])
    lines = [f"- plate: {p['size'][0]:.1f} x {p['size'][1]:.1f} x {p['thickness']:.1f} mm, printed "
             f"{p.get('orientation', '?').replace('_', ' ')}; {len(p['holes'])} x {ch['bolt']} {ch['length']:g} mm "
             f"through slots into {ch['nut']} held in {held} (adjustment covered: {cov})",
             f"- raised features on the free face: {p['surface']}"]
    if mirror_reference(st) is not None:
        lines.append(f"- handedness: {p['handedness']}")
    for row in p.get("contact_face_openings") or []:
        lines.append(f"- cuts open on the {row['face']} face (a contact face): "
                     + ", ".join(f"{c['id']} {c['area_mm2']:.0f} mm2" for c in row["cuts"]))
    return lines


def decisions(st: "A.AssemblyState") -> Dict[str, Any]:
    p = st.plate or {}
    if not p:
        return {}
    return {"plate": {"surface": p.get("surface"), "handedness": p.get("handedness"), "retention": p.get("retention"),
                      "orientation": p.get("orientation")}}


def layout_bodies(st: "A.AssemblyState") -> Dict[str, dict]:
    """layout.json bodies for the plate: the chosen print orientation, and the declared mirror pair."""
    p = st.plate or {}
    out = {BODY: {"orientation": p.get("orientation"), "source": "rule:print_orientation (the flat face with the least "
                  "overhang)", "orientations": p.get("orientations")}}
    if p.get("frame"):
        out[FRAME] = {"orientation": ORIENTATIONS[0], "source": "a flat frame prints on either face"}
    if p.get("handedness") == "mirror_pair" and mirror_reference(st) is not None:
        out[BODY]["mirror_pair"] = {"file": f"{BODY}_mirror.stl", "plane": mirror_reference(st)}
    return out


def write_mirror(st: "A.AssemblyState", workdir) -> Optional[str]:
    """A declared mirror pair: the mirror image of the delivered plate STL as <body>_mirror.stl (not a checked body)."""
    p = st.plate or {}
    plane = mirror_reference(st)
    if p.get("handedness") != "mirror_pair" or plane is None:
        return None
    path = workdir / f"{BODY}_mirror.stl"
    fg.write_stl(mirrored(st.solids[BODY], plane), path)
    return str(path.name)


def _plain(v):
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items() if k not in ("inst", "solid", "poly")}
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, np.ndarray):
        return [_plain(x) for x in v.tolist()]
    if isinstance(v, (np.floating, np.integer)):
        return v.item()
    return v


def summary(p: Mapping[str, Any]) -> dict:
    """design.json assembly.plate: the derived plate's numbers (JSON-safe; the cut polygons left out)."""
    out = _plain(dict(p))
    for c in out.get("cuts", []):
        c.pop("poly", None)
        c.pop("local", None)
    return out


DIRECTIONS: Dict[str, Tuple[str, str]] = {
    "bolt_engagement": ("bolt thread through its nut", "increase"),
    "bolt_tip": ("cover over the bolt tip", "increase"),
    "nut_trap": ("nut trap clearance per flat side", "band"),
    "travel": ("bolt travel through the declared adjustment range", "increase"),
    "nut_frame_turn": ("nut frame diagonal beyond the pocket width", "increase"),
    "plate_size": ("plate plan length", "band"),
    "plate_thickness": ("plate thickness", "band"),
    "bearing_area": ("flat bearing area of the underside", "increase"),
    "load_stress": ("bending stress of the load case", "decrease"),
    "clamp_seat": ("share of a fastener's bearing face on printed material", "increase"),
    "clamp_frame": ("share of the nut frame's bearing on the plate", "increase"),
    "clamp_face": ("share of the bolted face's bearing on the plate", "increase"),
    "fastener_bearing": ("ratio of a fastener seat's bearing pressure and punch-through shear to what the printed "
                         "material allows", "decrease"),
    "thin_feature": ("thinnest printed feature", "increase"),
    "stud_engagement": ("stud thread engagement in printed material", "increase"),
    "printable": ("unsupported overhang or bridge in the print orientation", "decrease"),
    "surface_features": ("the raised features the text asks for (count, height, edge distance, spread)", "semantic"),
    HANDEDNESS: ("one part for both sides of the mirror pair, or a declared pair", "semantic"),
}
EXTRA_CHECKS: Dict[str, Callable] = {
    "bolt_engagement": value_check, "bolt_tip": value_check, "nut_trap": nut_trap_check, "travel": travel_check,
    "nut_frame_turn": value_check,
    "plate_size": plate_size_check, "plate_thickness": plate_thickness_check, "bearing_area": bearing_area_check,
    "load_stress": load_stress_check, "printable": printable_check, "surface_features": surface_check,
    HANDEDNESS: handedness_check, "clamp_seat": clamp_seat_check, "clamp_frame": clamp_frame_check,
    "clamp_face": clamp_face_check, "thin_feature": thin_feature_check, "stud_engagement": stud_engagement_check,
    "fastener_bearing": fastener_bearing_check,
}
ACTUATORS: Dict[str, Callable] = {"surface_features": surface_actions, "printable": surface_actions,
                                  HANDEDNESS: handedness_actions, "travel": retention_actions,
                                  "clamp_seat": retention_actions, "fastener_bearing": retention_actions}
APPLIERS: Dict[str, Callable] = {SET_SURFACE: apply_surface, SET_HANDEDNESS: apply_handedness,
                                 SET_RETENTION: apply_retention}
ac.EXTRA_CHECKS.update(EXTRA_CHECKS)
