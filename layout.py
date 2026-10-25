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
5. grid (ARCHITECTURE.md 7.13): the board's grid is a finite hole array (`Grid`; a part without a grid
   `count` is an infinite lattice). A through-hole part whose own pin pattern can meet the grid
   (`grid_feasibility` best_any <= rules.grid_residual_max) is moved so that every pin is on an existing
   hole (`grid_positions`): among those positions, the smallest move inward from the flush pose, then
   the smallest move along the edge (a part with no edge: the smallest move from its free spot), the
   first that collides with nothing and crowds no port. A pattern that meets no lattice position at all
   is `pin_pattern` (mounted through enlarged holes) and is not moved. The plug envelope, not a flush
   rule, then sets the wall opening;
6. interference: references may not intersect each other or a hole column (R7); a 1-D shift along
   the edge resolves what it can (in whole pitches for a part on the grid), anything left is a typed
   LayoutError;
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
    snaps: Dict[str, dict] = field(default_factory=dict)    # module node -> the grid snap's outcome (Placer._snap)

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


def mount_holes(board: pt.PartInstance):
    """The primary's mounting-hole axis list, named by its mount_holes interface (generalize delta 001 C1); None when the
    part offers no such interface."""
    m = pt.mount_interface(board.part)
    if m is None or m.get("holes") not in board.datums:
        return None
    return pt.lookup_datum(board.datums, m["holes"])


def hole_columns(board: pt.PartInstance, diameter: float) -> List[Tuple[float, float, float]]:
    """(x, y, radius) of the column on every mounting-hole axis of the primary (V-HOLE-KO in plan)."""
    holes = mount_holes(board)
    if holes is None:
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
    connectors: Optional[List[str]] = None   # the exposed connector names (None: the part's first connector)


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
GRID_BLOCKED_SHOWN = 6           # blocking pairs quoted in a note (all of them are in Layout.snaps)


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


def grid_kind(residual: float, best_any: float, limit: float, tol: float = 0.0, extent_ok: bool = True,
              blocked: bool = False) -> str:
    """ok | pin_pattern | grid_extent | blocked | tangential (see Placer.grid_report, ARCHITECTURE.md 7.13).

    pin_pattern: the pattern meets no lattice position (exempt: mounted through enlarged holes); grid_extent: it
    meets the lattice but no position inside the finite grid (extent_ok False); blocked: on-grid positions exist but
    every one collides or crowds a port; tangential: the snap failed although nothing blocked it (an agent bug)."""
    if residual <= limit + tol:
        return "ok"
    if best_any > limit + tol:
        return "pin_pattern"
    if not extent_ok:
        return "grid_extent"
    if blocked:
        return "blocked"
    return "tangential"


@dataclass
class Grid:
    """A board's through-hole array (ARCHITECTURE.md 7.13): holes at origin + pitch x (i, j). With `count` it is
    finite (i < count[0], j < count[1]) and the nearest hole is clip(round((q - origin) / pitch), 0, count - 1);
    without, an infinite lattice. Unpacks as (origin, pitch), the iteration 002 tuple."""
    origin: np.ndarray
    pitch: float
    count: Optional[Tuple[int, int]] = None

    def __iter__(self):
        return iter((self.origin, self.pitch))

    def index(self, rel: np.ndarray) -> np.ndarray:
        """Nearest-hole indices of plan points given relative to the origin (any leading shape, last axis 2)."""
        k = np.round(np.asarray(rel, dtype=float) / self.pitch)
        if self.count is not None:
            k = np.clip(k, 0, np.asarray(self.count, dtype=float) - 1)
        return k

    def offset(self, q: np.ndarray) -> np.ndarray:
        """Plan vector(s) from the nearest existing hole to world point(s) q (last axis >= 2)."""
        rel = np.asarray(q, dtype=float)[..., :2] - self.origin[:2]
        if self.count is None:
            return (rel + self.pitch / 2) % self.pitch - self.pitch / 2
        return rel - self.pitch * self.index(rel)

    def holes(self) -> np.ndarray:
        """Every hole's plan position (finite grids only)."""
        if self.count is None:
            raise ValueError("an infinite lattice has no finite hole set")
        ii, jj = np.meshgrid(np.arange(self.count[0]), np.arange(self.count[1]), indexing="ij")
        return self.origin[:2] + self.pitch * np.stack([ii.ravel(), jj.ravel()], axis=1)


def grid_positions(pins_rel: Sequence[Sequence[float]], grid: Grid, limit: float, step: Optional[float] = None,
                   feas: Optional[dict] = None) -> np.ndarray:
    """Every plan shift (m x 2) that puts each pin (n x 2, relative to the grid origin) within `limit` of an existing
    hole (ARCHITECTURE.md 7.13). Empty when the pattern meets no lattice position (best_any > limit: pin_pattern).

    From the lattice minimax shift s0 (grid_feasibility any_shift; `feas` may pass it in), the candidates are
    s0 + pitch x (i, j) over the index ranges that keep every pin within [-limit, (count - 1) x pitch + limit] of the
    array; those whose finite-grid residual (nearest existing hole) is <= limit are kept. An infinite lattice has no
    extent: s0 and its eight neighbouring cells are returned. At most count_x x count_y candidates, vectorised."""
    pins = np.asarray([[float(q[0]), float(q[1])] for q in pins_rel], dtype=float)
    p = grid.pitch
    feas = feas or grid_feasibility(pins, p, (0, 1), step=step)
    if feas["best_any"] > limit:
        return np.zeros((0, 2))
    s0 = np.asarray(feas["any_shift"], dtype=float)[:2]
    base = pins + s0
    if grid.count is None:
        ranges = [np.arange(-1, 2)] * 2
    else:
        ranges = []
        for a in range(2):
            top = (grid.count[a] - 1) * p
            lo = math.ceil((-limit - base[:, a].min()) / p - EPS)
            hi = math.floor((top + limit - base[:, a].max()) / p + EPS)
            ranges.append(np.arange(lo, hi + 1))
    if any(len(r) == 0 for r in ranges):
        return np.zeros((0, 2))
    ii, jj = np.meshgrid(*ranges, indexing="ij")
    shifts = s0 + p * np.stack([ii.ravel(), jj.ravel()], axis=1)
    rel = base[None, :, :] - s0 + shifts[:, None, :]
    d = rel - p * grid.index(rel)
    worst = np.sqrt((d * d).sum(axis=2)).max(axis=1)
    return shifts[worst <= limit + EPS]


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
        self.top = float(world_datum(board, pt.mount_names(board.inst.part)[2]).at[2])
        self.seg = int(self.rules.get("fn", fg.DEFAULT_SEGMENTS))
        self.notes: List[str] = []
        self.grid = self._grid()

    def _grid(self) -> Optional[Grid]:
        return board_grid(self.board.inst)

    # ----- one part -----

    def _connector(self, inst: pt.PartInstance, names: Optional[Sequence[str]] = None) -> Tuple[dict, np.ndarray]:
        """The connector that faces the chosen edge: the first of `names` (the item's exposed connectors), else the
        part's first connector."""
        if not inst.connectors:
            raise LayoutError("bad_part", f"{inst.part_id} has no connector to face an edge")
        c = next((x for x in inst.connectors if names and x.get("name") in names), inst.connectors[0])
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
        _, axis = self._connector(inst, item.connectors)
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
        """Plan vector from the nearest existing grid hole to a point (zero vector when the board has no grid)."""
        if self.grid is None:
            return np.zeros(2)
        return self.grid.offset(q)

    def _relative(self, pins: Sequence[np.ndarray]) -> np.ndarray:
        """Plan pin positions relative to the grid origin (n x 2)."""
        origin, _ = self.grid
        return np.asarray([np.asarray(q[:2], dtype=float) - origin[:2] for q in pins])

    def _search_step(self, pitch: float) -> float:
        return float(self.rules.get("grid_search_step") or pitch / GRID_SEARCH_DIVISIONS)

    def grid_shift(self, module: Placed, tangent: Optional[int]) -> np.ndarray:
        """Shift (<= pitch/2 per axis) along `tangent` (None: both plan axes) that minimises the worst pin's
        distance to the board's lattice (minimax over every pin, not the first pin's offset; identical for a part
        whose pins all lie on one lattice). The lattice sensor of iteration 006; `place` now moves parts with
        `snap_moves`, which also respects the finite hole array (ARCHITECTURE.md 7.13)."""
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

    def _limits(self) -> Tuple[float, float]:
        return float(self.rules.get("grid_residual_max", 0.0)), float(self.rules.get("measure_tol", 0.0))

    def grid_report(self, placed: Sequence[Placed], snaps: Optional[Mapping[str, dict]] = None) -> dict:
        """Grid conformance per part (the sensor behind the grid_conformance check, ARCHITECTURE.md 7.7, 7.9, 7.13).

        parts[node]: the worst pin's residual to its nearest existing hole; for an edge-placed part its tangential and
        normal components and `normal_fix`; from `grid_feasibility` (the part's own pins and the pitch only) `best_any`
        (the best residual at any lattice position) and `best_free` (along the edge tangent); `positions` (how many
        plan positions put every pin on an existing hole, `grid_positions`); `snap` (the placer's outcome, from
        `snaps` = Layout.snaps) and `kind`: ok | pin_pattern (exempt, listed in `exempt`, not counted in `max`) |
        grid_extent | blocked (with `blocked_by`) | tangential (the snap failed: a placement bug).
        no_pin_data: parts with a connector but no pin data (they cannot be verified).
        """
        g = self.board.inst.part.data.get("grid") or {}
        grid = self.grid
        out = {"grid": grid is not None, "soft": bool(g.get("soft")), "finite": grid is not None and grid.count is not None,
               "max": 0.0, "worst": None, "parts": {}, "no_pin_data": [], "exempt": []}
        if grid is None:
            return out
        limit, tol = self._limits()
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
            rel = self._relative(pins)
            feas = grid_feasibility(rel, grid.pitch, axes, step=self._search_step(grid.pitch))
            positions = len(grid_positions(rel, grid, limit, feas=feas)) if feas["best_any"] <= limit + tol else 0
            snap = dict((snaps or {}).get(p.node_id) or {})
            kind = grid_kind(row["residual"], feas["best_any"], limit, tol,
                             extent_ok=positions > 0 and snap.get("status") != "grid_extent",
                             blocked=snap.get("status") == "blocked")
            row.update(best_any=feas["best_any"], best_free=feas["best_free"], positions=positions,
                       snap=snap.get("status"), kind=kind)
            if snap.get("pairs"):
                row["blocked_by"] = list(snap["pairs"])
            out["parts"][p.node_id] = row
            if kind == "pin_pattern":
                out["exempt"].append(p.node_id)
                continue
            if row["residual"] > out["max"]:
                out["max"], out["worst"] = row["residual"], p.node_id
        return out

    def snap_moves(self, p: Placed) -> Tuple[List[np.ndarray], dict]:
        """The on-grid moves of a placed part, best first, and the snap's typed status (ARCHITECTURE.md 7.13).

        status: no_pin_data | pin_pattern (no lattice position: not moved) | grid_extent (no position inside the finite
        grid, or only ones that push an edge part outward past its edge) | on_grid (moves returned). For an edge part
        (normal axis a, outward sign s) a move d has the inward component n = -s d[a]; moves with n < -measure_tol are
        dropped, the rest ordered by (n, |d[tangent]|): nearest the chosen edge, then nearest its spread slot. A part
        with no edge orders them by plan distance from its free spot."""
        pins = self.pins(p)
        if self.grid is None or not pins:
            return [], {"status": "no_pin_data"}
        limit, tol = self._limits()
        rel = self._relative(pins)
        feas = grid_feasibility(rel, self.grid.pitch, (0, 1), step=self._search_step(self.grid.pitch))
        info = {"best_any": feas["best_any"]}
        if feas["best_any"] > limit + tol:
            return [], dict(info, status="pin_pattern")
        shifts = grid_positions(rel, self.grid, limit, feas=feas)
        d = np.zeros((len(shifts), 3))
        d[:, :2] = shifts
        info["positions"] = len(shifts)
        if p.edge is not None and len(d):
            e = self.edges[p.edge]
            n = -e["sign"] * d[:, e["axis"]]
            keep = n >= -tol
            d, n = d[keep], n[keep]
            order = np.lexsort((np.round(np.abs(d[:, e["tangent"]]), GRID_TIE_DIGITS), np.round(n, GRID_TIE_DIGITS)))
        else:
            order = np.argsort(np.round(np.linalg.norm(d[:, :2], axis=1), GRID_TIE_DIGITS), kind="stable")
        if not len(d):
            return [], dict(info, status="grid_extent")
        return [d[i] for i in order], dict(info, status="on_grid")

    def on_grid(self, p: Placed) -> bool:
        """Every pin of a placed part lies within grid_residual_max of an existing hole."""
        limit, tol = self._limits()
        return all(float(np.linalg.norm(self._offgrid(q))) <= limit + tol for q in self.pins(p) or [])

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

    def _hits(self, trial: Sequence[Placed], others: Sequence[Placed], solids: Mapping[str, Any]) -> List[str]:
        """The collisions of a moved group with the other placed parts (solids given) and the hole columns; pairs inside
        the group are not counted. An AABB test skips the boolean for parts that cannot touch."""
        limit = self.rules.get("interference_max", 0.0)
        mine = {q.node_id for q in trial}
        out = []
        for q in trial:
            sq = _solid(q, self.seg)
            bq = sq.bounding_box()
            for o in others:
                if o.node_id in mine or not _boxes_overlap(bq, solids[o.node_id].bounding_box()):
                    continue
                v = (sq ^ solids[o.node_id]).volume()
                if v > limit:
                    out.append(f"{q.node_id} x {o.node_id}: {v:.3g} mm3")
            if q.role == "board":
                continue
            for k, c in enumerate(self.columns):
                col = _column_solid(c, self.top, self.column_h, self.seg)
                if not _boxes_overlap(bq, col.bounding_box()):
                    continue
                v = (sq ^ col).volume()
                if v > limit:
                    out.append(f"{q.node_id} on hole column {k}: {v:.3g} mm3")
        return out

    def _snap(self, gid: str, groups, snaps: Dict[str, dict]) -> List[Placed]:
        """Move a group onto the grid (ARCHITECTURE.md 7.13): the first of `snap_moves` that collides with nothing and
        crowds no port on its edge. Records the outcome in snaps[gid]: status snapped (with the move) | blocked (every
        on-grid position collides or crowds; `pairs` lists what blocked them) | pin_pattern | grid_extent | no_pin_data.
        The group is unchanged unless it snapped."""
        group, it = groups[gid]
        moves, info = self.snap_moves(group[0])
        snaps[gid] = dict(info)
        if not moves:
            if info["status"] == "grid_extent":
                self.notes.append(f"{gid}: its pins meet the grid lattice, but no position inside the board's hole array "
                                  "(grid_extent)")
            return group
        others = [p for g, (grp, _) in groups.items() if g != gid for p in grp] + [self.board]
        solids = {p.node_id: _solid(p, self.seg) for p in others}
        edge = group[0].edge
        blocked: List[str] = []
        for k, d in enumerate(moves):
            trial = self._moved(group, d, it)
            hits = self._hits(trial, others, solids)
            crowds = edge is not None and not self._spacing_ok(edge, groups, gid, trial[0])
            if not hits and not crowds:
                snaps[gid].update(status="snapped", move=[float(v) for v in d], tried=k + 1)
                if np.linalg.norm(d) > EPS:
                    self.notes.append(f"{gid}: moved ({fmt(d[0])}, {fmt(d[1])}) mm to put every pin on a grid hole")
                return trial
            blocked += hits or [f"{gid} crowds a port on {edge}"]
        pairs = sorted(set(blocked))
        snaps[gid].update(status="blocked", pairs=pairs, tried=len(moves))
        self.notes.append(f"{gid}: every one of {len(moves)} on-grid positions collides or crowds a port (blocked: "
                          f"{'; '.join(pairs[:GRID_BLOCKED_SHOWN])}{' ...' if len(pairs) > GRID_BLOCKED_SHOWN else ''})")
        return group

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
        snaps: Dict[str, dict] = {}
        for gid, (group, it) in list(groups.items()):
            groups[gid] = (self._snap(gid, groups, snaps), it)
        for it in items:
            if edges.get(it.id):
                continue
            for k in range(it.quantity):
                group = self._free_spot(it, k, [p for grp, _ in groups.values() for p in grp])
                gid = group[0].node_id
                groups[gid] = (group, it)
                groups[gid] = (self._snap(gid, groups, snaps), it)
        snapped = {g for g, v in snaps.items() if v.get("status") == "snapped"}
        for gid in list(groups):
            groups[gid] = (self._resolve(gid, groups, gid in snapped), groups[gid][1])
        for group, _ in groups.values():
            lay.placed.extend(group)
        left = self.collisions(lay.placed)
        if left:
            raise LayoutError("collides", "; ".join(left), pairs=left)
        lay.notes = list(self.notes)
        lay.snaps = snaps
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

    def _resolve(self, gid: str, groups, snapped: bool = False) -> List[Placed]:
        """A 1-D shift along the group's edge (step rules.layout_step, inside its free span) that removes its
        collisions with everything placed so far; the group unchanged when it already fits or nothing helps. A group
        on the grid (snapped) steps by whole pitches and keeps every pin on an existing hole (ARCHITECTURE.md 7.13)."""
        group, it = groups[gid]
        others = [p for g, (grp, _) in groups.items() if g != gid for p in grp] + [self.board]
        if not self.collisions(group + others) or group[0].edge is None:
            return group
        edge = self.edges[group[0].edge]
        lo, hi = free_span(edge, self.board.inst, self.columns)
        t = edge["tangent"]
        step = self.grid.pitch if snapped and self.grid is not None else self.rules.get("layout_step", 1.0)
        blo, bhi = bbox_of(group[0].inst, group[0].pose)
        for k in range(1, int((hi - lo) / step) + 1):
            for sgn in (1, -1):
                d = np.zeros(3)
                d[t] = sgn * k * step
                if blo[t] + d[t] < lo - EPS or bhi[t] + d[t] > hi + EPS:
                    continue
                trial = self._moved(group, d, it)
                if snapped and not self.on_grid(trial[0]):
                    continue
                if not self.collisions(trial + others) and self._spacing_ok(group[0].edge, groups, gid, trial[0]):
                    self.notes.append(f"{gid}: shifted {fmt(d[t])} mm along {group[0].edge} to clear a collision")
                    return trial
        return group


def _boxes_overlap(a: Sequence[float], b: Sequence[float]) -> bool:
    """Two manifold bounding boxes (min xyz, max xyz) overlap with a positive volume."""
    return all(a[k] < b[k + 3] - EPS and b[k] < a[k + 3] - EPS for k in range(3))


def board_grid(board: pt.PartInstance) -> Optional[Grid]:
    """The board's grid block as a Grid (None when the part declares none)."""
    g = board.grid()
    if g is None:
        return None
    count = None if g["count"] is None else (int(round(g["count"][0])), int(round(g["count"][1])))
    return Grid(np.asarray(g["origin"], dtype=float), float(g["pitch"]), count)


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
    and the grid onto themselves within `tol`: a finite grid's hole set onto itself (ARCHITECTURE.md 7.13), an
    infinite lattice's origin modulo the pitch. A grid the part declares `soft` (an assumed registration) does
    not veto a symmetry; the mismatch is reported in `notes`.
    """
    size_of = board.part.data.get("size_of")
    lo, hi = bbox_of(board, np.eye(4), size_of)
    centre = (np.asarray(lo[:2]) + np.asarray(hi[:2])) / 2
    ext = np.asarray(hi[:2]) - np.asarray(lo[:2])
    corners = [(lo[0], lo[1]), (hi[0], lo[1]), (lo[0], hi[1]), (hi[0], hi[1])]
    axes = mount_holes(board)
    holes = [tuple(p[:2]) for p in axes.at] if axes is not None else []
    grid = board_grid(board)
    soft = bool((board.part.data.get("grid") or {}).get("soft"))
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
            if grid.count is not None:
                if k % 2 and grid.count[0] != grid.count[1]:
                    res = np.array([grid.pitch])           # a quarter turn swaps the counts
                else:
                    res = grid.offset(np.array([turned(h, k) for h in grid.holes()]))
            else:
                d = np.asarray(turned(grid.origin[:2], k)) - grid.origin[:2]
                res = (d + grid.pitch / 2) % grid.pitch - grid.pitch / 2
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
        conn = (", ".join(it.connectors) if it.connectors else            # the exposed connectors the item names
                copies[0].inst.connectors[0]["name"] if copies[0].inst.connectors else "connector")
        count = f" x{len(copies)}" if len(copies) > 1 else ""
        verb = "face" if len(copies) > 1 else "faces"
        bits.append(f"{it.name or it.part}{count} ({conn}) {verb} {layout.edges[copies[0].edge]['words']}")
    return "; ".join(bits)
