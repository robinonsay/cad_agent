"""Pure placement math for --mode assembly (ArrangeContents, ARCHITECTURE.md section 4.2, milestone M7 subset).

The local LLM decides only discrete things (which board edge each exposed
connector faces). Everything in millimetres is computed here from part data and
generic rules:

1. rotate: rot_z = atan2(edge normal) - atan2(connector axis), in degrees, never a literal angle;
2. flush: the part's `size_of` geometry face on the connector side is flush with the board edge, so
   an overhanging receptacle sits exactly at its catalogue overhang;
3. Z: board TOP; a stacked module sits on its stack part (module stack datum = stack STACK_TOP), and
   the stack parts are placed on the module's `stack_pins` datums;
4. spread: the copies on one edge are spread with equal gaps over the edge's free span (the edge
   minus the corner-hole columns); one copy is centred; adjacent ports must be at least
   (plug widths)/2 + 2 x plug_to_opening + min_ligament apart, else `ports_do_not_fit`;
5. grid: pins are shifted by at most pitch/2 along the edge by the minimax shift (the one that makes the
   worst pin's distance to the board grid smallest; the direction normal to the edge stays flush: a port
   reaching its wall outranks grid conformance). `grid_feasibility` also says whether any position at all
   could put the part's own pin pattern on the grid (ARCHITECTURE.md 7.9);
6. interference: references may not intersect each other or a hole column (R7); a 1-D shift along
   the edge resolves what it can, anything left is a typed LayoutError;
7. parts without an exposed connector take the free spot nearest the board centre.

Everything is in the board frame, which is the enclosure frame (X along the board's longest edge,
origin at the board's min corner on its top surface). Nothing here is specific to one request
(test_no_hardcoding.py scans this module).
"""

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

import feature_graph as fg
import parts as pt

SIDES = ("-X", "+X", "-Y", "+Y")
EPS = 1e-9


class LayoutError(ValueError):
    """A typed placement failure: kind in {ports_do_not_fit, collides, on_screw_column, no_room, bad_part}."""

    def __init__(self, kind: str, detail: str, **data):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail
        self.data = data


@dataclass
class Placed:
    node_id: str
    part: str
    params: Dict[str, float]
    x: float
    y: float
    z: float
    rot_z: float
    item: str                    # the content item it belongs to ("" for the board)
    copy: int = 0
    role: str = "content"        # board | content | stack
    edge: Optional[str] = None
    of: Optional[str] = None     # stack parts: the module node they carry
    inst: Any = None             # parts.PartInstance (part frame)

    @property
    def pose(self) -> np.ndarray:
        return pose_of(self.x, self.y, self.z, self.rot_z)

    def to_json(self) -> dict:
        return {"part": self.part, "params": dict(self.params), "x": self.x, "y": self.y, "z": self.z,
                "rot_z": self.rot_z, "item": self.item, "copy": self.copy, "role": self.role,
                "edge": self.edge, "of": self.of}


@dataclass
class Layout:
    placed: List[Placed] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    edges: Dict[str, dict] = field(default_factory=dict)

    def get(self, node_id: str) -> Placed:
        return next(p for p in self.placed if p.node_id == node_id)

    def of_item(self, item: str) -> List[Placed]:
        return [p for p in self.placed if p.item == item and p.role == "content"]


def pose_of(x: float, y: float, z: float, rot_z: float) -> np.ndarray:
    return fg.matrix(fg.rot_z_matrix(rot_z), (x, y, z))


def angle_of(v: Sequence[float]) -> float:
    return math.degrees(math.atan2(float(v[1]), float(v[0])))


def bbox_of(inst: pt.PartInstance, pose: np.ndarray, of: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray]:
    """World AABB of an instance (or of its geometry primitive `of`)."""
    if of is None:
        return fg.instance_world_bbox(inst, pose)
    sub = pt.PartInstance(inst.part, inst.params, [g for g in inst.geometry if g.id == of], inst.datums)
    if not sub.geometry:
        raise LayoutError("bad_part", f"{inst.part_id}: size_of names no geometry {of!r}")
    return fg.instance_world_bbox(sub, pose)


def world_datum(p: Placed, name: str):
    return pt.transform(pt.lookup_datum(p.inst.datums, name), p.pose)


def fmt(v: float) -> str:
    return f"{v:.6g}"


# ---------------------------------------------------------------------------
# Board edges, words and columns
# ---------------------------------------------------------------------------


def board_edges(board: pt.PartInstance) -> Dict[str, dict]:
    """The four edges of the board's plan rectangle, keyed by outward normal, with Python's words."""
    lo, hi = fg.instance_world_bbox(board, np.eye(4))
    ext = hi - lo
    out = {}
    for side in SIDES:
        axis = "XY".index(side[1])
        tangent = 1 - axis
        sign = 1.0 if side[0] == "+" else -1.0
        normal = np.zeros(3)
        normal[axis] = sign
        length = float(ext[tangent])
        other = float(ext[axis])
        size = "short" if length < other - EPS else "long" if length > other + EPS else "equal"
        noun = "end" if size == "short" else "side" if size == "long" else "edge"
        out[side] = {
            "side": side, "axis": axis, "tangent": tangent, "sign": sign, "normal": normal.tolist(),
            "coord": float(hi[axis] if sign > 0 else lo[axis]), "span": (float(lo[tangent]), float(hi[tangent])),
            "length": length, "words": f"the {size} ({fmt(length)} mm) {noun} at {side}",
        }
    return out


def hole_columns(board: pt.PartInstance, diameter: float) -> List[Tuple[float, float, float]]:
    """(x, y, radius) of the column on every board HOLE axis (V-HOLE-KO in plan)."""
    try:
        holes = pt.lookup_datum(board.datums, "HOLE")
    except KeyError:
        return []
    return [(float(p[0]), float(p[1]), diameter / 2) for p in holes.at]


def free_span(edge: dict, board: pt.PartInstance, columns: Sequence[Tuple[float, float, float]]) -> Tuple[float, float]:
    """The edge's span along its tangent minus the hole columns on this edge's half of the board."""
    lo, hi = edge["span"]
    blo, bhi = fg.instance_world_bbox(board, np.eye(4))
    a, t = edge["axis"], edge["tangent"]
    half = (bhi[a] - blo[a]) / 2
    mid = (lo + hi) / 2
    for c in columns:
        if abs(c[a] - edge["coord"]) >= half:
            continue
        if c[t] < mid:
            lo = max(lo, c[t] + c[2])
        else:
            hi = min(hi, c[t] - c[2])
    return lo, hi


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------


@dataclass
class Item:
    """One content entry: a catalogue part, its params, how many copies, whether its connector is exposed."""
    id: str
    part: str
    params: Dict[str, float] = field(default_factory=dict)
    quantity: int = 1
    exposed: bool = False
    stack: Optional[str] = None
    name: str = ""


def plug_width(catalog: pt.Catalog, part: pt.Part) -> float:
    """Horizontal cross-section width of the plug that mates with the part's first connector (0 if none)."""
    conns = part.data.get("connectors", [])
    if not conns or not conns[0].get("mates") or conns[0]["mates"] not in catalog:
        return 0.0
    plug = catalog.instantiate(conns[0]["mates"])
    return float(max(g.bbox()[1][1] - g.bbox()[0][1] for g in plug.geometry))


def _solid(p: Placed, seg: int):
    return fg.part_solid(p.inst, seg).transform(fg._m3(p.pose))


def _column_solid(c: Tuple[float, float, float], z0: float, h: float, seg: int):
    return fg._cyl(2 * c[2], h, seg).translate([c[0], c[1], z0])


GRID_SEARCH_DIVISIONS = 256      # fallback coarse steps per pitch when rules.grid_search_step is absent
GRID_REFINE_POINTS = 17          # samples per axis in each local refinement of the grid search
GRID_REFINE_SHRINK = 10.0        # each refinement narrows the window by this factor
GRID_REFINE_FLOOR = 1e-10        # refine until the window half-width is below this (mm)
GRID_BISECT_ITERATIONS = 64      # bisection steps for normal_needed (resolution pitch / 2**64)
GRID_TIE_DIGITS = 10             # worst distances equal to this many decimals tie; the smaller free-axis offset wins


def grid_worst(pins: np.ndarray, shifts: np.ndarray, pitch: float) -> np.ndarray:
    """Worst pin-to-lattice distance for each shift (m x 2) of a pin set (n x 2, relative to a lattice point)."""
    d = (pins[None, :, :] + shifts[:, None, :] + pitch / 2) % pitch - pitch / 2
    return np.sqrt((d * d).sum(axis=2)).max(axis=1)


def _pick(pins: np.ndarray, shifts: np.ndarray, pitch: float, axes: Sequence[int]) -> int:
    """Index of the minimax shift. Near the optimum the worst distance is flat (it is quadratic in a tangential
    offset when a normal offset dominates), so equal worst values (to GRID_TIE_DIGITS) are broken by the
    smallest worst offset along the free axes: a part whose pins share one lattice lands exactly on it."""
    vals = np.round(grid_worst(pins, shifts, pitch), GRID_TIE_DIGITS)
    d = (pins[None, :, :] + shifts[:, None, :] + pitch / 2) % pitch - pitch / 2
    free = np.abs(d[:, :, list(axes)]).max(axis=(1, 2))
    return int(np.lexsort((free, vals))[0])


def _wrap(v: float, pitch: float) -> float:
    return float((v + pitch / 2) % pitch - pitch / 2)


def _minimax(pins: np.ndarray, pitch: float, axes: Sequence[int], base: np.ndarray, step: float) -> Tuple[float, np.ndarray]:
    """min over shifts along `axes` (others fixed at `base`) of the worst pin distance: a coarse search of the
    torus [0, pitch) per free axis with spacing <= step, then local refinement (vectorised)."""
    base = np.asarray(base, dtype=float)
    if not axes:
        return float(grid_worst(pins, base[None, :], pitch)[0]), base.copy()
    k = max(int(math.ceil(pitch / step)), 1)
    grid = np.arange(k) * (pitch / k)
    mesh = np.meshgrid(*([grid] * len(axes)), indexing="ij")
    shifts = np.repeat(base[None, :], mesh[0].size, axis=0)
    for j, ax in enumerate(axes):
        shifts[:, ax] = mesh[j].ravel()
    best = shifts[_pick(pins, shifts, pitch, axes)].copy()
    h = pitch / k
    local = np.linspace(-1.0, 1.0, GRID_REFINE_POINTS)
    while h > GRID_REFINE_FLOOR:
        mesh = np.meshgrid(*([local * h] * len(axes)), indexing="ij")
        trial = np.repeat(best[None, :], mesh[0].size, axis=0)
        for j, ax in enumerate(axes):
            trial[:, ax] += mesh[j].ravel()
        best = trial[_pick(pins, trial, pitch, axes)].copy()
        h /= GRID_REFINE_SHRINK
    for ax in axes:
        best[ax] = _wrap(best[ax], pitch)
    return float(grid_worst(pins, best[None, :], pitch)[0]), best


def grid_feasibility(pins_xy: Sequence[Sequence[float]], pitch: float, free_axes: Sequence[int] = (0, 1),
                     limit: Optional[float] = None, step: Optional[float] = None) -> dict:
    """Can this pin pattern meet a square lattice of `pitch`? (ARCHITECTURE.md 7.9: report feasibility, not only
    the violated value.) Uses only the pins (plan positions relative to a lattice point) and the pitch.

    best_any / any_shift: the minimax over every plan translation of the worst pin-to-lattice distance;
    best_free / free_shift: the same with only `free_axes` moving (the others stay where they are);
    normal_needed / normal_shift: with one free axis, the smallest |move| along the other (normal) axis after
    which the free-axis minimax is <= limit (None when best_any > limit, or with no limit or no normal axis).
    Shifts are added to the pins and wrapped to [-pitch/2, pitch/2)."""
    pins = np.asarray([[float(q[0]), float(q[1])] for q in pins_xy], dtype=float)
    step = float(step or pitch / GRID_SEARCH_DIVISIONS)
    zero = np.zeros(2)
    best_any, any_shift = _minimax(pins, pitch, (0, 1), zero, step)
    free = tuple(int(a) for a in free_axes)
    best_free, free_shift = _minimax(pins, pitch, free, zero, step)
    out = {"best_any": best_any, "any_shift": any_shift.tolist(), "best_free": best_free,
           "free_shift": free_shift.tolist(), "normal_needed": None, "normal_shift": None}
    if limit is None or len(free) != 1 or best_any > limit:
        return out
    if best_free <= limit:
        out.update(normal_needed=0.0, normal_shift=0.0)
        return out
    a = free[0]
    b = 1 - a

    def g(n: float) -> float:
        base = np.zeros(2)
        base[b] = n
        return _minimax(pins, pitch, (a,), base, step)[0]

    k = max(int(math.ceil(pitch / step)), 1)
    ns = (np.arange(k) - k // 2) * (pitch / k)
    order = np.argsort(np.abs(ns), kind="stable")
    for idx in order:
        n = float(ns[idx])
        if g(n) <= limit:
            lo = n - math.copysign(pitch / k, n) if n else 0.0   # one step nearer zero: fails
            hi = n
            for _ in range(GRID_BISECT_ITERATIONS):
                mid = (lo + hi) / 2
                if g(mid) <= limit:
                    hi = mid
                else:
                    lo = mid
            out.update(normal_needed=abs(hi), normal_shift=hi)
            break
    return out


def grid_kind(residual: float, best_any: float, best_free: float, limit: float, tol: float = 0.0) -> str:
    """ok | pin_pattern | flush_to_edge | tangential (see Placer.grid_report)."""
    if residual <= limit + tol:
        return "ok"
    if best_any > limit + tol:
        return "pin_pattern"
    if best_free > limit + tol:
        return "flush_to_edge"
    return "tangential"


class Placer:
    """Places a board's contents from discrete choices (edges, stacks) and generic rules."""

    def __init__(self, catalog: pt.Catalog, board: Placed, rules: Mapping[str, float], column_d: float,
                 column_h: float):
        self.catalog = catalog
        self.board = board
        self.rules = dict(rules)
        self.edges = board_edges(board.inst)
        self.columns = hole_columns(board.inst, column_d)
        self.column_h = column_h
        self.top = float(world_datum(board, "TOP").at[2])
        self.seg = int(self.rules.get("fn", fg.DEFAULT_SEGMENTS))
        self.notes: List[str] = []
        self.grid = self._grid()

    def _grid(self) -> Optional[Tuple[np.ndarray, float]]:
        g = self.board.inst.part.data.get("grid")
        if not g:
            return None
        env = self.board.inst.env
        return fg.evaluate3(g["origin"], env), fg.evaluate(g["pitch"], env)

    # ----- one part -----

    def _connector(self, inst: pt.PartInstance) -> Tuple[dict, np.ndarray]:
        if not inst.connectors:
            raise LayoutError("bad_part", f"{inst.part_id} has no connector to face an edge")
        c = inst.connectors[0]
        return c, np.asarray(pt.lookup_datum(inst.datums, c["axis"]).dir, dtype=float)

    def _stack_height(self, item: Item, inst: pt.PartInstance) -> Tuple[float, Optional[pt.PartInstance]]:
        if not item.stack:
            return 0.0, None
        stack = self.catalog.instantiate(item.stack, self._stack_params(item.stack, inst))
        top = pt.lookup_datum(stack.datums, "STACK_TOP").at[2]
        bottom = pt.lookup_datum(stack.datums, "STACK_BOTTOM").at[2]
        mount = inst.part.data.get("mount", {})
        datum_z = pt.lookup_datum(inst.datums, mount.get("stack_datum")).at[2] if mount.get("stack_datum") else 0.0
        return float(top - bottom - datum_z), stack

    def _stack_params(self, stack_id: str, module: pt.PartInstance) -> Dict[str, float]:
        """A stack part sized to the module's pin rows: as many positions as pins, at their pitch."""
        rows = module.part.data.get("mount", {}).get("stack_pins", [])
        declared = self.catalog.get(stack_id).params
        if not rows:
            return {}
        row = pt.lookup_datum(module.datums, rows[0])
        out = {}
        if "pins" in declared:
            out["pins"] = float(len(row.at))
        if "pitch" in declared and len(row.at) > 1:
            out["pitch"] = float(np.linalg.norm(np.subtract(row.at[1], row.at[0])))
        return out

    def place_on_edge(self, item: Item, copy: int, side: str, t_centre: float) -> Placed:
        inst = self.catalog.instantiate(item.part, item.params)
        edge = self.edges[side]
        _, axis = self._connector(inst)
        rot = angle_of(edge["normal"]) - angle_of(axis)
        lift, _ = self._stack_height(item, inst)
        size_of = inst.part.data.get("size_of")
        r = pose_of(0, 0, 0, rot)
        lo, hi = bbox_of(inst, r, size_of)
        flo, fhi = bbox_of(inst, r)
        a, t = edge["axis"], edge["tangent"]
        pos = np.zeros(3)
        pos[a] = edge["coord"] - (hi[a] if edge["sign"] > 0 else lo[a])
        pos[t] = t_centre - (flo[t] + fhi[t]) / 2
        pos[2] = self.top + lift
        return Placed(f"{item.id}_{copy + 1}", item.part, dict(item.params), float(pos[0]), float(pos[1]),
                      float(pos[2]), rot, item.id, copy, "content", side, inst=inst)

    def footprint(self, item: Item, side: str) -> float:
        p = self.place_on_edge(item, 0, side, 0.0)
        lo, hi = bbox_of(p.inst, p.pose)
        return float(hi[self.edges[side]["tangent"]] - lo[self.edges[side]["tangent"]])

    def stacks_for(self, module: Placed, item: Item) -> List[Placed]:
        if not item.stack:
            return []
        rows = module.inst.part.data.get("mount", {}).get("stack_pins", [])
        params = self._stack_params(item.stack, module.inst)
        stack = self.catalog.instantiate(item.stack, params)
        own = pt.lookup_datum(stack.datums, "PINS")
        own_angle = angle_of(np.subtract(own.at[1], own.at[0])) if len(own.at) > 1 else 0.0
        bottom = pt.lookup_datum(stack.datums, "STACK_BOTTOM").at[2]
        out = []
        for k, name in enumerate(rows):
            row = world_datum(module, name)
            angle = angle_of(np.subtract(row.at[1], row.at[0])) if len(row.at) > 1 else module.rot_z
            rot = angle - own_angle
            origin = np.asarray(row.at[0], dtype=float) - fg.rot_z_matrix(rot) @ np.asarray(own.at[0], dtype=float)
            out.append(Placed(f"{module.node_id}_stack_{k + 1}", item.stack, params, float(origin[0]),
                              float(origin[1]), float(self.top - bottom), rot, item.id, module.copy, "stack",
                              module.edge, of=module.node_id, inst=stack))
        return out

    # ----- grid -----

    def pins(self, p: Placed) -> Optional[List[np.ndarray]]:
        """World pin points of a placed part: its module `stack_pins` rows, else a `PINS` datum; None when the
        part declares no pin data. A stack part's pins are its module's, so they are not counted twice."""
        if p.role in ("board", "stack"):
            return None
        names = list(p.inst.part.data.get("mount", {}).get("stack_pins", []))
        if not names and "PINS" in p.inst.datums:
            names = ["PINS"]
        if not names:
            return None
        return [np.asarray(q, dtype=float) for name in names for q in world_datum(p, name).at]

    def _offgrid(self, q: np.ndarray) -> np.ndarray:
        """Plan vector from the nearest grid hole to a point (zero vector when the board has no grid)."""
        if self.grid is None:
            return np.zeros(2)
        origin, pitch = self.grid
        return (np.asarray(q[:2], dtype=float) - origin[:2] + pitch / 2) % pitch - pitch / 2

    def _relative(self, pins: Sequence[np.ndarray]) -> np.ndarray:
        """Plan pin positions relative to the grid origin (n x 2)."""
        origin, _ = self.grid
        return np.asarray([np.asarray(q[:2], dtype=float) - origin[:2] for q in pins])

    def _search_step(self, pitch: float) -> float:
        return float(self.rules.get("grid_search_step") or pitch / GRID_SEARCH_DIVISIONS)

    def grid_shift(self, module: Placed, tangent: Optional[int]) -> np.ndarray:
        """Shift (<= pitch/2 per axis) along `tangent` (None: both plan axes) that minimises the worst pin's
        distance to the board grid (minimax over every pin, not the first pin's offset; identical for a part
        whose pins all lie on one lattice). Any part with pin data (stack_pins or a PINS datum) is snapped."""
        shift = np.zeros(3)
        pins = self.pins(module)
        if self.grid is None or not pins:
            return shift
        _, pitch = self.grid
        axes = (tangent,) if tangent is not None else (0, 1)
        feas = grid_feasibility(self._relative(pins), pitch, axes, step=self._search_step(pitch))
        for ax in axes:
            shift[ax] = feas["free_shift"][ax]
        return shift

    def grid_residual(self, placed: Sequence[Placed]) -> float:
        """Largest plan distance from a part pin to its nearest grid hole (0 when no grid)."""
        if self.grid is None:
            return 0.0
        worst = 0.0
        for p in placed:
            for q in self.pins(p) or []:
                worst = max(worst, float(np.linalg.norm(self._offgrid(q))))
        return worst

    def grid_report(self, placed: Sequence[Placed]) -> dict:
        """Grid conformance per part (the sensor behind the grid_conformance check, ARCHITECTURE.md 7.7, 7.9).

        parts[node]: the worst pin's residual; for an edge-placed part its tangential and normal components and
        `normal_fix` (the shift normal to the edge that zeroes the worst pin's normal offset); and from
        `grid_feasibility` (the part's own pins and the pitch only): `best_any` (the best residual at any plan
        position), `best_free` (the best along the placement's free axis, the edge tangent), `normal_needed`
        (the smallest move normal to the edge that lets the part pass, None when no position can) and `kind`:
        ok | pin_pattern (no position passes: a catalogue or requirement question) | flush_to_edge (it passes
        somewhere, not at the flush position) | tangential (the snap failed: a placement bug).
        no_pin_data: parts with a connector but no pin data (they cannot be verified).
        """
        g = self.board.inst.part.data.get("grid") or {}
        out = {"grid": self.grid is not None, "soft": bool(g.get("soft")), "max": 0.0, "worst": None,
               "parts": {}, "no_pin_data": []}
        if self.grid is None:
            return out
        _, pitch = self.grid
        limit = float(self.rules.get("grid_residual_max", 0.0))
        tol = float(self.rules.get("measure_tol", 0.0))
        for p in placed:
            pins = self.pins(p)
            if pins is None:
                if p.role == "content" and p.inst.connectors:
                    out["no_pin_data"].append(p.node_id)
                continue
            d = max((self._offgrid(q) for q in pins), key=lambda v: float(np.linalg.norm(v)))
            row = {"residual": float(np.linalg.norm(d)), "edge": p.edge}
            axes: Tuple[int, ...] = (0, 1)
            if p.edge is not None:
                e = self.edges[p.edge]
                axes = (e["tangent"],)
                row.update(tangential=float(abs(d[e["tangent"]])), normal=float(abs(d[e["axis"]])),
                           normal_fix=float(-d[e["axis"]]))
            feas = grid_feasibility(self._relative(pins), pitch, axes, limit=limit, step=self._search_step(pitch))
            row.update(best_any=feas["best_any"], best_free=feas["best_free"], normal_needed=feas["normal_needed"],
                       normal_shift=feas["normal_shift"],
                       kind=grid_kind(row["residual"], feas["best_any"], feas["best_free"], limit, tol))
            out["parts"][p.node_id] = row
            if row["residual"] > out["max"]:
                out["max"], out["worst"] = row["residual"], p.node_id
        return out

    # ----- interference -----

    def collisions(self, placed: Sequence[Placed]) -> List[str]:
        """Pairs of references that intersect (> interference_max) and parts on a hole column."""
        limit = self.rules.get("interference_max", 0.0)
        solids = {p.node_id: _solid(p, self.seg) for p in placed}
        out = []
        ids = [p.node_id for p in placed]
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                v = (solids[a] ^ solids[b]).volume()
                if v > limit:
                    out.append(f"{a} x {b}: {v:.3g} mm3")
        for p in placed:
            if p.role == "board":
                continue
            for k, c in enumerate(self.columns):
                v = (solids[p.node_id] ^ _column_solid(c, self.top, self.column_h, self.seg)).volume()
                if v > limit:
                    out.append(f"{p.node_id} on hole column {k}: {v:.3g} mm3")
        return out

    def _group(self, module: Placed, item: Item) -> List[Placed]:
        return [module] + self.stacks_for(module, item)

    def _moved(self, group: List[Placed], d: np.ndarray, item: Item) -> List[Placed]:
        m = group[0]
        moved = Placed(m.node_id, m.part, m.params, m.x + float(d[0]), m.y + float(d[1]), m.z + float(d[2]),
                       m.rot_z, m.item, m.copy, m.role, m.edge, m.of, m.inst)
        return self._group(moved, item)

    # ----- the whole layout -----

    def place(self, items: Sequence[Item], edges: Mapping[str, Optional[str]]) -> Layout:
        lay = Layout(edges={k: {kk: vv for kk, vv in v.items() if kk != "normal"} for k, v in self.edges.items()})
        lay.placed.append(self.board)
        groups: Dict[str, Tuple[List[Placed], Item]] = {}
        by_edge: Dict[str, List[Tuple[Item, int]]] = {}
        for it in items:
            side = edges.get(it.id)
            if side:
                by_edge.setdefault(side, []).extend((it, k) for k in range(it.quantity))
        for side, copies in by_edge.items():
            edge = self.edges[side]
            lo, hi = free_span(edge, self.board.inst, self.columns)
            widths = [self.footprint(it, side) for it, _ in copies]
            free = (hi - lo) - sum(widths)
            if free < -EPS:
                raise LayoutError("ports_do_not_fit", f"{side}: parts need {fmt(sum(widths))} mm of the edge, "
                                  f"the free span is {fmt(hi - lo)} mm", edge=side, need=sum(widths), have=hi - lo)
            gap = free / (len(copies) + 1)
            t = lo + gap
            for (it, k), w in zip(copies, widths):
                module = self.place_on_edge(it, k, side, t + w / 2)
                groups[module.node_id] = (self._group(module, it), it)
                t += w + gap
            self._check_spacing(side, [groups[f"{it.id}_{k + 1}"][0][0] for it, k in copies])
        for gid, (group, it) in list(groups.items()):
            d = self.grid_shift(group[0], self.edges[group[0].edge]["tangent"])
            if np.linalg.norm(d) < EPS:
                continue
            trial = self._moved(group, d, it)
            others = [p for g, (grp, _) in groups.items() if g != gid for p in grp] + [self.board]
            if self.collisions(trial + others) or not self._spacing_ok(group[0].edge, groups, gid, trial[0]):
                self.notes.append(f"{gid}: grid snap of {fmt(float(np.linalg.norm(d)))} mm skipped (it would collide "
                                  "or crowd a port)")
                continue
            groups[gid] = (trial, it)
        for it in items:
            if edges.get(it.id):
                continue
            for k in range(it.quantity):
                group = self._free_spot(it, k, [p for grp, _ in groups.values() for p in grp])
                groups[group[0].node_id] = (group, it)
        for gid in list(groups):
            groups[gid] = (self._resolve(gid, groups), groups[gid][1])
        for group, _ in groups.values():
            lay.placed.extend(group)
        left = self.collisions(lay.placed)
        if left:
            raise LayoutError("collides", "; ".join(left), pairs=left)
        lay.notes = list(self.notes)
        return lay

    def _ports(self, side: str, placed: Sequence[Placed]) -> List[Tuple[float, float, str]]:
        t = self.edges[side]["tangent"]
        out = []
        for p in placed:
            c, _ = self._connector(p.inst)
            mouth = world_datum(p, c["mouth"]).at
            out.append((float(mouth[t]), plug_width(self.catalog, p.inst.part), p.node_id))
        return sorted(out)

    def _need(self, wa: float, wb: float) -> float:
        return wa / 2 + wb / 2 + 2 * self.rules["plug_to_opening"] + self.rules["min_ligament"]

    def _check_spacing(self, side: str, placed: Sequence[Placed]) -> None:
        ports = self._ports(side, placed)
        for (ta, wa, a), (tb, wb, b) in zip(ports, ports[1:]):
            need = self._need(wa, wb)
            if tb - ta < need - EPS:
                raise LayoutError("ports_do_not_fit", f"{side}: {a} and {b} are {fmt(tb - ta)} mm apart, the plugs "
                                  f"need {fmt(need)} mm", edge=side, need=need, have=tb - ta)

    def _spacing_ok(self, side: str, groups, gid: str, moved: Placed) -> bool:
        placed = [moved if g == gid else grp[0] for g, (grp, _) in groups.items() if grp[0].edge == side]
        try:
            self._check_spacing(side, placed)
        except LayoutError:
            return False
        return True

    def _free_spot(self, item: Item, copy: int, placed: Sequence[Placed]) -> List[Placed]:
        """The plan position nearest the board centre where the part fits on the board, off every column
        and clear of the placed parts (a grid search with step rules.layout_step)."""
        inst = self.catalog.instantiate(item.part, item.params)
        lift, _ = self._stack_height(item, inst)
        lo, hi = bbox_of(inst, np.eye(4))
        blo, bhi = fg.instance_world_bbox(self.board.inst, np.eye(4))
        step = self.rules.get("layout_step", 1.0)
        centre = (blo + bhi) / 2
        boxes = [bbox_of(p.inst, p.pose) for p in placed if p.role != "board"]
        best = None
        xs = np.arange(blo[0] - lo[0], bhi[0] - hi[0] + EPS, step)
        ys = np.arange(blo[1] - lo[1], bhi[1] - hi[1] + EPS, step)
        for x in xs:
            for y in ys:
                plo, phi = lo[:2] + (x, y), hi[:2] + (x, y)
                if any(np.all(plo < b[1][:2] - EPS) and np.all(phi > b[0][:2] + EPS) for b in boxes):
                    continue
                if any(_circle_hits_box(c, plo, phi) for c in self.columns):
                    continue
                d = float(np.linalg.norm((plo + phi) / 2 - centre[:2]))
                if best is None or d < best[0] - EPS:
                    best = (d, x, y)
        if best is None:
            raise LayoutError("no_room", f"{item.id}: no free spot on the board for {item.part}", item=item.id)
        module = Placed(f"{item.id}_{copy + 1}", item.part, dict(item.params), float(best[1]), float(best[2]),
                        self.top + lift, 0.0, item.id, copy, "content", None, inst=inst)
        return self._group(module, item)

    def _resolve(self, gid: str, groups) -> List[Placed]:
        """A 1-D shift along the group's edge (step rules.layout_step, inside its free span) that removes its
        collisions with everything placed so far; the group unchanged when it already fits or nothing helps."""
        group, it = groups[gid]
        others = [p for g, (grp, _) in groups.items() if g != gid for p in grp] + [self.board]
        if not self.collisions(group + others) or group[0].edge is None:
            return group
        edge = self.edges[group[0].edge]
        lo, hi = free_span(edge, self.board.inst, self.columns)
        t = edge["tangent"]
        step = self.rules.get("layout_step", 1.0)
        blo, bhi = bbox_of(group[0].inst, group[0].pose)
        for k in range(1, int((hi - lo) / step) + 1):
            for sgn in (1, -1):
                d = np.zeros(3)
                d[t] = sgn * k * step
                if blo[t] + d[t] < lo - EPS or bhi[t] + d[t] > hi + EPS:
                    continue
                trial = self._moved(group, d, it)
                if not self.collisions(trial + others) and self._spacing_ok(group[0].edge, groups, gid, trial[0]):
                    self.notes.append(f"{gid}: shifted {fmt(d[t])} mm along {group[0].edge} to clear a collision")
                    return trial
        return group


def _circle_hits_box(c: Tuple[float, float, float], lo: np.ndarray, hi: np.ndarray) -> bool:
    q = np.clip(np.array(c[:2]), lo, hi)
    return float(np.linalg.norm(q - np.array(c[:2]))) < c[2] - EPS


# ---------------------------------------------------------------------------
# Board symmetry (ConfirmArrangement groups equivalent edge assignments, ARCHITECTURE.md 7.6)
# ---------------------------------------------------------------------------

SIDE_VECTOR = {"-X": (-1, 0), "+X": (1, 0), "-Y": (0, -1), "+Y": (0, 1)}


def _quarter_turn(v: Sequence[float], k: int) -> Tuple[float, float]:
    """(x, y) turned by k quarter turns counter-clockwise (exact: no angle literal, no trigonometry)."""
    x, y = float(v[0]), float(v[1])
    for _ in range(k % 4):
        x, y = -y, x
    return x, y


def _side_after(side: str, k: int) -> str:
    v = _quarter_turn(SIDE_VECTOR[side], k)
    return next(s for s, u in SIDE_VECTOR.items() if abs(u[0] - v[0]) < EPS and abs(u[1] - v[1]) < EPS)


def _same_points(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]], tol: float) -> bool:
    """Every point of `a` has its own point of `b` within tol (a one-to-one match in plan)."""
    if len(a) != len(b):
        return False
    left = [np.asarray(q[:2], dtype=float) for q in b]
    for p in a:
        p = np.asarray(p[:2], dtype=float)
        k = next((i for i, q in enumerate(left) if np.linalg.norm(p - q) <= tol), None)
        if k is None:
            return False
        left.pop(k)
    return True


def board_symmetries(board: pt.PartInstance, tol: float, notes: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """The in-plane rotations about the board's plan centre that map the board onto itself, as edge maps.

    Candidates are generated, never listed per board: the identity and the half turn, plus the quarter
    turns when the outline is square. Mirrors are never candidates (parts are chiral, a mirrored layout
    is another product). A candidate is kept only when it maps the outline (`size_of`), every HOLE axis
    and the grid origin (modulo the pitch) onto themselves within `tol`. A grid the part declares `soft`
    (an assumed registration) does not veto a symmetry; the mismatch is reported in `notes`.
    """
    size_of = board.part.data.get("size_of")
    lo, hi = bbox_of(board, np.eye(4), size_of)
    centre = (np.asarray(lo[:2]) + np.asarray(hi[:2])) / 2
    ext = np.asarray(hi[:2]) - np.asarray(lo[:2])
    corners = [(lo[0], lo[1]), (hi[0], lo[1]), (lo[0], hi[1]), (hi[0], hi[1])]
    try:
        holes = [tuple(p[:2]) for p in pt.lookup_datum(board.datums, "HOLE").at]
    except KeyError:
        holes = []
    g = board.part.data.get("grid")
    grid = None
    if g:
        grid = (np.asarray(fg.evaluate3(g["origin"], board.env)[:2], dtype=float), float(fg.evaluate(g["pitch"], board.env)),
                bool(g.get("soft")))
    turns = (0, 1, 2, 3) if abs(ext[0] - ext[1]) <= tol else (0, 2)

    def turned(p, k):
        return tuple(centre + np.asarray(_quarter_turn(np.asarray(p, dtype=float) - centre, k)))

    out = []
    for k in turns:
        if not _same_points([turned(c, k) for c in corners], corners, tol):
            continue
        if not _same_points([turned(h, k) for h in holes], holes, tol):
            continue
        if grid is not None and k:
            origin, pitch, soft = grid
            d = np.asarray(turned(origin, k)) - origin
            res = (d + pitch / 2) % pitch - pitch / 2
            if np.any(np.abs(res) > tol):
                if not soft:
                    continue
                if notes is not None:
                    notes.append(f"{board.part_id}: the {k}-quarter-turn symmetry moves the grid by "
                                 f"{fmt(float(np.max(np.abs(res))))} mm off itself; kept because the part declares "
                                 "its grid soft (an assumed registration)")
        out.append({s: _side_after(s, k) for s in SIDES})
    return out


def canonical_class(assign: Mapping[str, Optional[str]], symmetries: Sequence[Mapping[str, str]]) -> Tuple:
    """The lexicographically smallest image of an edge assignment under the symmetries (its class key)."""
    maps = list(symmetries) or [{s: s for s in SIDES}]
    return min(tuple((k, m.get(v, v) if v else "") for k, v in sorted(assign.items())) for m in maps)


def describe(layout: Layout, items: Sequence[Item]) -> str:
    """Python's words for an arrangement, e.g. 'pico 2 (usb) faces the short (50 mm) end at -X'."""
    bits = []
    for it in items:
        copies = layout.of_item(it.id)
        if not copies or copies[0].edge is None:
            continue
        conn = copies[0].inst.connectors[0]["name"] if copies[0].inst.connectors else "connector"
        count = f" x{len(copies)}" if len(copies) > 1 else ""
        verb = "face" if len(copies) > 1 else "faces"
        bits.append(f"{it.name or it.part}{count} ({conn}) {verb} {layout.edges[copies[0].edge]['words']}")
    return "; ".join(bits)
