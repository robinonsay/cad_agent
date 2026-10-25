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
5. grid: pins are shifted by at most pitch/2 along the edge so they land on the board grid (the
   direction normal to the edge stays flush: a port reaching its wall outranks grid conformance);
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

    def grid_shift(self, module: Placed, tangent: Optional[int]) -> np.ndarray:
        """Shift (<= pitch/2 per axis) that puts the module's first pin on the board grid along `tangent`
        (None: both plan axes)."""
        shift = np.zeros(3)
        rows = module.inst.part.data.get("mount", {}).get("stack_pins", [])
        if self.grid is None or not rows:
            return shift
        origin, pitch = self.grid
        pin = np.asarray(world_datum(module, rows[0]).at[0], dtype=float)
        for ax in ((tangent,) if tangent is not None else (0, 1)):
            res = (pin[ax] - origin[ax] + pitch / 2) % pitch - pitch / 2
            shift[ax] = -res
        return shift

    def grid_residual(self, placed: Sequence[Placed]) -> float:
        """Largest plan distance from a module pin to its nearest grid hole (0 when no grid)."""
        if self.grid is None:
            return 0.0
        origin, pitch = self.grid
        worst = 0.0
        for p in placed:
            for name in p.inst.part.data.get("mount", {}).get("stack_pins", []):
                for q in world_datum(p, name).at:
                    d = (np.asarray(q[:2]) - origin[:2] + pitch / 2) % pitch - pitch / 2
                    worst = max(worst, float(np.linalg.norm(d)))
        return worst

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
