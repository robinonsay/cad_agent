"""Parts catalogue: part.json loader, alias lookup, datums and the import validation gate.

A catalogue part is data handed to the agent (ARCHITECTURE.md section 3.1), one
folder per part under ``benchmarks/enclosure/parts/<id>/part.json``. Every
part-specific number lives in those files, never in agent logic: sizes,
datums (mouths, axes, hole patterns, stacking planes) and the part's own sanity
checks (``self_checks``) are expressions over the part's ``params``, evaluated
with ``feature_graph.evaluate``.

Datums carry the geometry the design is derived from:

* ``Point(at)`` - a location (a connector mouth);
* ``Axis(at, dir)`` - a located direction (a plug axis), optional diameter;
* ``Plane(at, normal)`` - a face (a board's top, a header's stacking top);
* ``AxisList(at=[...], dir)`` - a pattern of parallel axes (mounting holes, pins).

Axes and axis lists may carry a ``keepout_diameter``: the plan circle round each axis that the part
itself reserves (a board's component and fastener keep-out round its mounting holes).

A board's ``grid`` block is its through-hole array: ``pitch``, ``origin`` (the first hole) and, for a
finite array, ``count`` (holes per plan axis, expressions). Without ``count`` it is an infinite
lattice (the iteration 002 meaning, kept for compatibility). ``PartInstance.grid`` evaluates it.

A part may list measured ``specimens`` of its family: ``{id, match, params, source}``. When every ``match``
param is given and lies within ``size_tolerance``, the specimen's ``params`` replace the family defaults (an
explicitly given value still wins). ``PartInstance.specimen`` records which one was used. ``gate`` rejects
specimens without an id or source, matches on non-request params, params that are undeclared or request
params, and overlapping matches, and validates an instance at each specimen's match.

``validate`` is the import gate: a part whose bounding box does not match its
datasheet size (a x25.4 or x1000 unit error, swapped axes), whose datum
directions are not unit vectors, whose connector mouth is off its geometry, or
whose self-checks fail is not used.

This module never imports cad_agent. It imports ``feature_graph`` (which
imports this module back), using only module attributes at call time.
"""

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np

import feature_graph as fg

SCHEMA = 1
UNIT_TOL = 1e-6          # datum direction vectors must be unit length within this
MOUTH_TOL = 0.05         # mm: a connector mouth must lie on a geometry primitive's surface
DEFERRED_RULES = {
    "R7": "checked after placement: layout.place rejects pairwise interference > interference_max",
    "R8": "by construction: envelopes are generated from the placed datums (test_parts.TestEnvelopes)",
    "R9": "skipped: imported models are compared only in the --with-models arm (M14)",
}
STOPWORDS = {"a", "an", "the", "of", "and", "with", "for", "on", "in", "to", "x", "type"}


class PartError(ValueError):
    pass


class MissingParam(PartError):
    def __init__(self, part: str, name: str):
        super().__init__(f"{part}: parameter {name!r} must come from the request")
        self.part = part
        self.name = name


@dataclass
class GateFailure:
    part: str
    rule: str
    detail: str

    def __str__(self):
        return f"{self.part}: {self.rule}: {self.detail}"


# ---------------------------------------------------------------------------
# Datums
# ---------------------------------------------------------------------------


@dataclass
class Point:
    at: List[float]


@dataclass
class Axis:
    at: List[float]
    dir: List[float]
    diameter: Optional[float] = None
    keepout_diameter: Optional[float] = None


@dataclass
class Plane:
    at: List[float]
    normal: List[float]

    @property
    def dir(self) -> List[float]:
        return self.normal


@dataclass
class AxisList:
    at: List[List[float]]
    dir: List[float]
    diameter: Optional[float] = None
    keepout_diameter: Optional[float] = None

    def item(self, i: int) -> Axis:
        if not 0 <= i < len(self.at):
            raise KeyError(i)
        return Axis(list(self.at[i]), list(self.dir), self.diameter, self.keepout_diameter)


Datum = Union[Point, Axis, Plane, AxisList]


def pose_matrix(translation: Sequence[float] = (0, 0, 0), rot_z_deg: float = 0.0,
                rotation: Optional[Sequence[Sequence[float]]] = None) -> np.ndarray:
    """4x4 from a translation and a rotation about Z (or a general 3x3 rotation)."""
    r = np.asarray(rotation, dtype=float) if rotation is not None else fg.rot_z_matrix(rot_z_deg)
    return fg.matrix(r, translation)


def transform(d: Datum, pose: np.ndarray) -> Datum:
    """A datum moved by a 4x4 pose (points translate and rotate; directions only rotate)."""
    pose = np.asarray(pose, dtype=float)
    r, t = pose[:3, :3], pose[:3, 3]

    def pt(p):
        return (r @ np.asarray(p, dtype=float) + t).tolist()

    def vec(v):
        return (r @ np.asarray(v, dtype=float)).tolist()

    if isinstance(d, Point):
        return Point(pt(d.at))
    if isinstance(d, Axis):
        return Axis(pt(d.at), vec(d.dir), d.diameter, d.keepout_diameter)
    if isinstance(d, Plane):
        return Plane(pt(d.at), vec(d.normal))
    if isinstance(d, AxisList):
        return AxisList([pt(p) for p in d.at], vec(d.dir), d.diameter, d.keepout_diameter)
    raise TypeError(f"not a datum: {d!r}")


def lookup_datum(datums: Mapping[str, Datum], ref: str) -> Datum:
    """'board.HOLE[2]' -> the Axis of item 2; 'pico.USB_MOUTH' -> that datum. KeyError if absent."""
    if ref.endswith("]") and "[" in ref:
        base, idx = ref[:-1].rsplit("[", 1)
        d = datums[base]
        if not isinstance(d, AxisList) or not idx.isdigit():
            raise KeyError(ref)
        return d.item(int(idx))
    return datums[ref]


ATTRS = {"x": ("at", 0), "y": ("at", 1), "z": ("at", 2), "dx": ("dir", 0), "dy": ("dir", 1), "dz": ("dir", 2)}


def datum_value(datums: Mapping[str, Datum], ref: str) -> float:
    """'board.HOLE[3].x', 'HOLE.diameter', 'HOLE.keepout_diameter', 'HOLE.count', 'USB_AXIS.dx' -> a number.
    KeyError if absent."""
    if "." not in ref:
        raise KeyError(ref)
    base, attr = ref.rsplit(".", 1)
    d = lookup_datum(datums, base)
    if attr in ("diameter", "keepout_diameter"):
        if getattr(d, attr, None) is None:
            raise KeyError(ref)
        return float(getattr(d, attr))
    if attr == "count":
        if not isinstance(d, AxisList):
            raise KeyError(ref)
        return float(len(d.at))
    if attr not in ATTRS or isinstance(d, AxisList) and ATTRS[attr][0] == "at":
        raise KeyError(ref)
    slot, i = ATTRS[attr]
    vec = d.at if slot == "at" else d.dir
    return float(vec[i])


# ---------------------------------------------------------------------------
# Parts and instances
# ---------------------------------------------------------------------------


@dataclass
class Part:
    id: str
    data: dict
    path: Optional[Path] = None

    @property
    def names(self) -> List[str]:
        return list(self.data.get("names", []))

    @property
    def kind(self) -> str:
        return self.data.get("kind", "")

    @property
    def params(self) -> Dict[str, dict]:
        return dict(self.data.get("params", {}))

    def request_params(self) -> List[str]:
        return [k for k, v in self.params.items() if v.get("from_request")]

    def gate_params(self) -> Dict[str, float]:
        """The sample values the load-time gate uses for request-sized params (never design values)."""
        return {k: v for k, v in self.data.get("gate_params", {}).items() if k in self.params}

    @property
    def specimens(self) -> List[dict]:
        """Measured specimens of the part's family (ARCHITECTURE.md 3.1, iteration 011 C1): each
        {id, match: {request param: value}, params: {param: value}, source}."""
        return list(self.data.get("specimens", []) or [])

    def specimen_for(self, given: Mapping[str, Any]) -> Optional[dict]:
        """The one specimen whose `match` holds for these given params (every match key given and within the
        part's `size_tolerance`), or None. The gate rejects overlapping matches, so at most one can hold."""
        tol = float(self.data.get("size_tolerance", 0.0)) + 1e-9
        for sp in self.specimens:
            match = sp.get("match") or {}
            try:
                ok = bool(match) and all(given.get(k) is not None and abs(float(given[k]) - float(v)) <= tol
                                         for k, v in match.items())
            except (TypeError, ValueError):
                ok = False
            if ok:
                return sp
        return None


@dataclass
class Primitive:
    """A resolved part-geometry primitive in the part frame. Box: `at` is the min corner.
    Cylinder: `at` is the centre of its start face; it runs `h` along `dir`."""
    id: str
    primitive: str
    at: List[float]
    size: Optional[List[float]] = None
    d: Optional[float] = None
    h: Optional[float] = None
    dir: Optional[List[float]] = None

    def bbox(self) -> Tuple[np.ndarray, np.ndarray]:
        a = np.asarray(self.at, dtype=float)
        if self.primitive == "box":
            s = np.asarray(self.size, dtype=float)
            return np.minimum(a, a + s), np.maximum(a, a + s)
        u = np.asarray(self.dir, dtype=float)
        u = u / np.linalg.norm(u)
        r = self.d / 2
        ext = r * np.sqrt(np.clip(1.0 - u * u, 0.0, None))
        b = a + u * self.h
        return np.minimum(a, b) - ext, np.maximum(a, b) + ext


@dataclass
class PartInstance:
    part: Part
    params: Dict[str, float]
    geometry: List[Primitive]
    datums: Dict[str, Datum]
    keepouts: List[Primitive] = field(default_factory=list)
    connectors: List[dict] = field(default_factory=list)
    specimen: Optional[dict] = None          # {id, source, params} when a catalogue specimen supplied values

    @property
    def part_id(self) -> str:
        return self.part.id

    def bbox(self, of: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray]:
        prims = [g for g in self.geometry if of is None or g.id == of]
        if not prims:
            raise KeyError(of)
        boxes = [g.bbox() for g in prims]
        return np.min([b[0] for b in boxes], axis=0), np.max([b[1] for b in boxes], axis=0)

    def env(self, name: str) -> float:
        """Values for self-check expressions: params, `<geometry id>.min_x|max_x|size_x|center_x`,
        `bbox.*` (the union), `grid.origin_x|origin_y|count_x|count_y|pitch` and datum refs (`HOLE[1].x`,
        `USB_AXIS.dx`, `HOLE.diameter`)."""
        if name in self.params:
            return self.params[name]
        head, _, attr = name.partition(".")
        geom_ids = {g.id for g in self.geometry}
        if attr and (head in geom_ids or head == "bbox") and "[" not in head:
            lo, hi = self.bbox(None if head == "bbox" else head)
            return _box_attr(lo, hi, attr, name)
        if head == "grid" and attr and head not in geom_ids:
            return _grid_attr(self.grid(), attr, self.part.id, name)
        try:
            return datum_value(self.datums, name)
        except KeyError:
            raise fg.MissingRefError(self.part.id, name) from None


    def grid(self) -> Optional[dict]:
        """The part's `grid` block evaluated: {origin (3), pitch, count ([nx, ny] floats) or None (an infinite
        lattice), soft}; None when the part declares no grid. `count` is checked by `validate` (whole, >= 1)."""
        g = self.part.data.get("grid")
        if not g:
            return None
        count = g.get("count")
        return {"origin": fg.evaluate3(g["origin"], self.env), "pitch": fg.evaluate(g["pitch"], self.env),
                "count": None if count is None else [fg.evaluate(c, self.env) for c in count],
                "soft": bool(g.get("soft"))}


def _grid_attr(grid: Optional[dict], attr: str, part: str, name: str) -> float:
    if grid is None:
        raise fg.MissingRefError(part, name)
    if attr == "pitch":
        return float(grid["pitch"])
    kind, _, axis = attr.rpartition("_")
    if axis not in ("x", "y") or kind not in ("origin", "count") or kind == "count" and grid["count"] is None:
        raise fg.MissingRefError(part, name)
    i = "xy".index(axis)
    return float(grid["origin"][i] if kind == "origin" else grid["count"][i])


def _box_attr(lo: np.ndarray, hi: np.ndarray, attr: str, name: str) -> float:
    kind, _, axis = attr.rpartition("_")
    if axis not in ("x", "y", "z") or kind not in ("min", "max", "size", "center"):
        raise fg.MissingRefError(None, name)
    i = "xyz".index(axis)
    return float({"min": lo[i], "max": hi[i], "size": hi[i] - lo[i], "center": (lo[i] + hi[i]) / 2}[kind])


def _resolve_param_values(part: Part, given: Mapping[str, Any]) -> Dict[str, float]:
    """Order per param: given -> the matching specimen's value -> the family default -> MissingParam."""
    declared = part.params
    unknown = [k for k in given if k not in declared]
    if unknown:
        raise PartError(f"{part.id}: unknown parameter(s) {', '.join(sorted(unknown))}")
    sp = part.specimen_for(given)
    sp_params = dict((sp or {}).get("params") or {})
    values: Dict[str, float] = {}
    for name, spec in declared.items():
        if name in given and given[name] is not None:
            values[name] = fg.evaluate(given[name], values)
        elif name in sp_params and sp_params[name] is not None:
            values[name] = fg.evaluate(sp_params[name], values)
        elif spec.get("default") is not None:
            values[name] = float(spec["default"])
        else:
            raise MissingParam(part.id, name)
    return values


def _geometry(part: Part, items: Sequence[dict], env) -> List[Primitive]:
    out = []
    for g in items:
        prim = g.get("primitive")
        at = fg.evaluate3(g.get("at", [0, 0, 0]), env).tolist()
        if prim == "box":
            out.append(Primitive(g["id"], prim, at, size=fg.evaluate3(g["size"], env).tolist()))
        elif prim == "cylinder":
            out.append(Primitive(g["id"], prim, at, d=fg.evaluate(g["d"], env), h=fg.evaluate(g["h"], env),
                                 dir=fg.evaluate3(g.get("dir", [0, 0, 1]), env).tolist()))
        else:
            raise PartError(f"{part.id}: geometry {g.get('id')!r} has unknown primitive {prim!r}")
    return out


def _datums(part: Part, items: Mapping[str, dict], env) -> Dict[str, Datum]:
    out: Dict[str, Datum] = {}
    for name, d in items.items():
        kind = d.get("kind")
        dia = fg.evaluate(d["diameter"], env) if d.get("diameter") is not None else None
        ko = fg.evaluate(d["keepout_diameter"], env) if d.get("keepout_diameter") is not None else None
        if kind == "point":
            out[name] = Point(fg.evaluate3(d["at"], env).tolist())
        elif kind == "axis":
            out[name] = Axis(fg.evaluate3(d["at"], env).tolist(), fg.evaluate3(d["dir"], env).tolist(), dia, ko)
        elif kind == "plane":
            out[name] = Plane(fg.evaluate3(d["at"], env).tolist(), fg.evaluate3(d["normal"], env).tolist())
        elif kind == "axis_list":
            if "at" in d:
                pts = [fg.evaluate3(p, env).tolist() for p in d["at"]]
            else:
                count = int(round(fg.evaluate(d["count"], env)))
                start, step = fg.evaluate3(d["start"], env), fg.evaluate3(d["step"], env)
                pts = [(start + i * step).tolist() for i in range(count)]
            out[name] = AxisList(pts, fg.evaluate3(d["dir"], env).tolist(), dia, ko)
        else:
            raise PartError(f"{part.id}: datum {name!r} has unknown kind {kind!r}")
    return out


def instantiate(part: Part, params: Optional[Mapping[str, Any]] = None) -> PartInstance:
    """A part with every expression evaluated. MissingParam when a request-sized param is absent."""
    given = dict(params or {})
    values = _resolve_param_values(part, given)
    env = dict(values)
    geometry = _geometry(part, part.data.get("geometry", []), env)
    keepouts = _geometry(part, part.data.get("keepouts", []), env)
    partial = PartInstance(part, values, geometry, {}, keepouts, list(part.data.get("connectors", [])))
    sp = part.specimen_for(given)
    if sp is not None:
        used = {k: values[k] for k in (sp.get("params") or {}) if given.get(k) is None}
        partial.specimen = {"id": sp.get("id"), "source": sp.get("source"), "params": used}
    partial.datums = _datums(part, part.data.get("datums", {}), partial.env)
    return partial


# ---------------------------------------------------------------------------
# Validation gate
# ---------------------------------------------------------------------------


def _point_to_box_surface(p: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> float:
    outside = np.maximum(np.maximum(lo - p, p - hi), 0.0)
    if np.any(outside > 0):
        return float(np.linalg.norm(outside))
    return float(min(np.min(p - lo), np.min(hi - p)))


def validate(inst: PartInstance) -> List[GateFailure]:
    """The import gate (R1, datum directions, connector mouths, self_checks). Empty list = usable.

    R7 and R8 need a layout and envelopes and run later (DEFERRED_RULES); R9 is the
    --with-models arm only.
    """
    part, data = inst.part, inst.part.data
    fails: List[GateFailure] = []
    # R1: bounding box vs the datasheet size, sorted per axis (units) and unsorted (orientation).
    if data.get("datasheet_size") is not None:
        try:
            expected = fg.evaluate3(data["datasheet_size"], inst.env)
            lo, hi = inst.bbox(data.get("size_of"))
        except (KeyError, fg.ExprError) as e:
            fails.append(GateFailure(part.id, "R1", f"cannot measure: {e}"))
        else:
            got = hi - lo
            tol = float(data.get("size_tolerance", 0.0)) + 1e-9
            if np.any(np.abs(np.sort(got) - np.sort(expected)) > tol):
                fails.append(GateFailure(part.id, "R1", f"bounding box {np.round(got, 3).tolist()} does not match "
                                         f"datasheet size {np.round(expected, 3).tolist()} (+/- {tol:.3g}); unit error?"))
            elif np.any(np.abs(got - expected) > tol):
                fails.append(GateFailure(part.id, "R1", f"bounding box {np.round(got, 3).tolist()} matches the datasheet "
                                         f"size {np.round(expected, 3).tolist()} only with its axes swapped"))
    # Datum directions are unit vectors (never normalised silently: a wrong scale is a data error).
    for name, d in inst.datums.items():
        vec = getattr(d, "dir", None)
        if vec is None:
            continue
        n = float(np.linalg.norm(vec))
        if abs(n - 1.0) > UNIT_TOL:
            fails.append(GateFailure(part.id, "datum", f"{name} direction {vec} has length {n:.6g}, not 1"))
    # Connector mouths lie on the surface of a geometry primitive.
    for c in inst.connectors:
        try:
            mouth = np.asarray(lookup_datum(inst.datums, c["mouth"]).at, dtype=float)
            lookup_datum(inst.datums, c["axis"])
        except KeyError as e:
            fails.append(GateFailure(part.id, "connector", f"{c.get('name')}: missing datum {e}"))
            continue
        dist = min(_point_to_box_surface(mouth, *g.bbox()) for g in inst.geometry)
        if dist > MOUTH_TOL:
            fails.append(GateFailure(part.id, "connector", f"{c.get('name')}: mouth {np.round(mouth, 3).tolist()} is "
                                     f"{dist:.3f} from the geometry (max {MOUTH_TOL})"))
    # A grid's pitch is positive and a finite grid's counts are whole numbers >= 1.
    if data.get("grid"):
        try:
            grid = inst.grid()
        except (fg.MissingRefError, fg.ExprError, KeyError) as e:
            fails.append(GateFailure(part.id, "grid", f"cannot evaluate ({e})"))
        else:
            if not grid["pitch"] > 0:
                fails.append(GateFailure(part.id, "grid", f"pitch {grid['pitch']:.4g} is not positive"))
            if grid["count"] is not None and len(grid["count"]) != 2:
                fails.append(GateFailure(part.id, "grid", f"count needs 2 entries (x, y), has {len(grid['count'])}"))
            for axis, n in zip("xy", grid["count"] or []):
                if n < 1 or abs(n - round(n)) > UNIT_TOL:
                    fails.append(GateFailure(part.id, "grid", f"count along {axis} is {n:.6g}, not a whole number >= 1"))
    # Part-specific sanity checks (R2, R4, R5, R6 ...) are data.
    for chk in data.get("self_checks", []):
        try:
            v = fg.evaluate(chk["expr"], inst.env)
            target = fg.evaluate(chk.get("value", 0), inst.env)
        except (fg.MissingRefError, fg.ExprError, KeyError) as e:
            fails.append(GateFailure(part.id, "self_check", f"{chk.get('name')}: cannot evaluate ({e})"))
            continue
        tol = float(chk.get("tol", 0.0)) + 1e-9
        op = chk.get("op", "eq")
        ok = {"eq": abs(v - target) <= tol, "le": v <= target + tol, "ge": v >= target - tol}.get(op)
        if ok is None:
            fails.append(GateFailure(part.id, "self_check", f"{chk.get('name')}: unknown op {op!r}"))
        elif not ok:
            fails.append(GateFailure(part.id, "self_check",
                                     f"{chk.get('name')}: {chk['expr']} = {v:.4g}, expected {op} {target:.4g} +/- {tol:.3g}"))
    return fails


def specimen_failures(part: Part) -> List[GateFailure]:
    """Static checks of a part's `specimens` block (rule "specimen"): each specimen has an id (unique) and a
    source; `match` keys are request params with numbers; `params` keys are declared, non-request params; no two
    specimens' matches overlap within `size_tolerance` (the choice would be ambiguous)."""
    fails: List[GateFailure] = []
    raw = part.data.get("specimens")
    if raw is None:
        return fails
    if not isinstance(raw, list):
        return [GateFailure(part.id, "specimen", "specimens must be a list")]
    declared, req = part.params, set(part.request_params())
    tol = float(part.data.get("size_tolerance", 0.0)) + 1e-9
    seen = set()
    for i, sp in enumerate(raw):
        if not isinstance(sp, dict):
            fails.append(GateFailure(part.id, "specimen", f"specimen {i} is not an object"))
            continue
        sid = sp.get("id")
        name = f"specimen {sid!r}" if sid else f"specimen {i}"
        if not sid:
            fails.append(GateFailure(part.id, "specimen", f"{name} has no id"))
        elif sid in seen:
            fails.append(GateFailure(part.id, "specimen", f"{name}: duplicate id"))
        seen.add(sid)
        if not sp.get("source"):
            fails.append(GateFailure(part.id, "specimen", f"{name} has no source"))
        match = sp.get("match")
        if not isinstance(match, dict) or not match:
            fails.append(GateFailure(part.id, "specimen", f"{name}: match must name at least one request param"))
            match = {}
        for k, v in match.items():
            if k not in req:
                fails.append(GateFailure(part.id, "specimen", f"{name}: match key {k!r} is not a from_request param"))
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                fails.append(GateFailure(part.id, "specimen", f"{name}: match value for {k!r} is not a number"))
        params = sp.get("params")
        if not isinstance(params, dict) or not params:
            fails.append(GateFailure(part.id, "specimen", f"{name}: params must give at least one value"))
            params = {}
        for k in params:
            if k not in declared:
                fails.append(GateFailure(part.id, "specimen", f"{name}: params key {k!r} is not a declared param"))
            elif k in req:
                fails.append(GateFailure(part.id, "specimen", f"{name}: params key {k!r} is a from_request param"))
    good = [sp for sp in raw if isinstance(sp, dict) and isinstance(sp.get("match"), dict) and sp["match"]]
    for a in range(len(good)):
        for b in range(a + 1, len(good)):
            ma, mb = good[a]["match"], good[b]["match"]
            shared = set(ma) & set(mb)
            try:
                overlap = all(abs(float(ma[k]) - float(mb[k])) <= 2 * tol for k in shared)
            except (TypeError, ValueError):
                continue
            if overlap:
                fails.append(GateFailure(part.id, "specimen", f"specimens {good[a].get('id')!r} and "
                                         f"{good[b].get('id')!r} have overlapping matches (+/- {tol:.3g})"))
    return fails


def gate(part: Part) -> List[GateFailure]:
    """The whole load-time gate for one part: the static specimen checks, then `validate` on the gate sample
    (`gate_params`) and on an instance at each specimen's `match`. Empty list = usable."""
    fails = specimen_failures(part)
    if fails:
        return fails
    samples = [("gate_params", part.gate_params())]
    samples += [(f"specimen {sp['id']!r}", dict(sp["match"])) for sp in part.specimens]
    for label, given in samples:
        try:
            got = validate(instantiate(part, given))
        except (PartError, fg.ExprError, fg.MissingRefError, KeyError, ValueError) as e:
            got = [GateFailure(part.id, "load", f"{label}: {e}")]
        if label != "gate_params":
            got = [GateFailure(f.part, f.rule, f"{label}: {f.detail}") for f in got]
        fails += got
    return fails


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


def tokens(text: str) -> List[str]:
    """Normalised lookup tokens: lowercase, punctuation dropped, digit/letter runs split, plurals folded."""
    t = text.lower()
    t = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", t)
    t = re.sub(r"[^a-z0-9. ]+", " ", t)
    out = []
    for w in t.split():
        w = w.strip(".")
        if not w or w in STOPWORDS:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


REQUIRED_FIELDS = ("id", "schema", "names", "kind", "source", "geometry")


@dataclass
class Catalog:
    parts: Dict[str, Part] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    root: Optional[Path] = None
    roots: List[Path] = field(default_factory=list)

    @classmethod
    def load(cls, root: Union[str, Path, Sequence[Union[str, Path]]]) -> "Catalog":
        """Every `<root>/<id>/part.json` of one catalogue folder, or of several in the order given; unreadable or
        malformed files are skipped and reported. With several folders the first one holding an id keeps it: a
        byte-equal copy of that part in a later folder is skipped silently, a different one is reported."""
        roots = [Path(r) for r in root] if isinstance(root, (list, tuple)) else [Path(root)]
        cat = cls(root=roots[0] if roots else None, roots=roots)
        for folder in roots:
            if not folder.is_dir():
                cat.errors.append(f"{folder}: not a directory")
                continue
            for path in sorted(folder.glob("*/part.json")):
                try:
                    data = json.loads(path.read_text())
                except (OSError, ValueError) as e:
                    cat.errors.append(f"{path}: unreadable ({e})")
                    continue
                missing = [f for f in REQUIRED_FIELDS if f not in data] if isinstance(data, dict) else ["object"]
                if missing:
                    cat.errors.append(f"{path}: missing {', '.join(missing)}")
                    continue
                if data["schema"] != SCHEMA:
                    cat.errors.append(f"{path}: schema {data['schema']!r}, expected {SCHEMA}")
                    continue
                if data["id"] in cat.parts:
                    first = cat.parts[data["id"]]
                    if first.path is not None and first.path.parent.parent != path.parent.parent \
                            and first.data == data:
                        continue                      # the same part shipped in two catalogue folders
                    kept = f" (kept {first.path})" if first.path is not None else ""
                    cat.errors.append(f"{path}: duplicate id {data['id']!r}{kept}")
                    continue
                cat.parts[data["id"]] = Part(data["id"], data, path)
        return cat

    def __contains__(self, part_id: str) -> bool:
        return part_id in self.parts

    def ids(self) -> List[str]:
        return sorted(self.parts)

    def get(self, part_id: str) -> Part:
        return self.parts[part_id]

    def instantiate(self, part_id: str, params: Optional[Mapping[str, Any]] = None) -> PartInstance:
        return instantiate(self.parts[part_id], params)

    def drop(self, part_id: str, reason: str) -> None:
        self.parts.pop(part_id, None)
        self.errors.append(f"{part_id}: dropped ({reason})")

    def lookup(self, text: str, k: int = 3) -> List[Tuple[str, float]]:
        """Top-k (part id, score) by alias-token overlap; score = matched share of the best alias
        plus a small bonus per matched token, so a longer exact alias beats a shorter one."""
        want = set(tokens(text))
        scored = []
        for pid, part in self.parts.items():
            best = 0.0
            for alias in part.names + [pid]:
                al = set(tokens(alias))
                if not al:
                    continue
                hit = len(al & want)
                if hit:
                    best = max(best, hit / len(al) + 0.01 * hit)
            if best > 0:
                scored.append((pid, round(best, 6)))
        scored.sort(key=lambda s: (-s[1], s[0]))
        return scored[:k]

    def cross_references(self) -> List[str]:
        """Part ids named by other parts (connector `mates`, `mount.stack_options`) that are missing."""
        out = []
        for pid, part in self.parts.items():
            named = [c.get("mates") for c in part.data.get("connectors", [])]
            named += list(part.data.get("mount", {}).get("stack_options", []))
            out += [f"{pid}: refers to missing part {n!r}" for n in named if n and n not in self.parts]
        return out


# ---------------------------------------------------------------------------
# Generic design rules (design_rules.json)
# ---------------------------------------------------------------------------


@dataclass
class Rules:
    values: Dict[str, float]
    sources: Dict[str, str]
    print_orientation: Dict[str, dict] = field(default_factory=dict)
    path: Optional[Path] = None
    spec_slots: List[dict] = field(default_factory=list)     # {name, meaning, unit, default_rule (key or None)}

    def slot(self, name: str) -> dict:
        return next(s for s in self.spec_slots if s["name"] == name)


def load_rules(path: Union[str, Path]) -> Rules:
    """design_rules.json -> values (for `rules.*` refs) and the source of each value."""
    path = Path(path)
    data = json.loads(path.read_text())
    if data.get("schema") != SCHEMA:
        raise PartError(f"{path}: schema {data.get('schema')!r}, expected {SCHEMA}")
    values, sources = {}, {}
    for key, entry in data.get("rules", {}).items():
        if not isinstance(entry, dict) or "value" not in entry or not entry.get("source"):
            raise PartError(f"{path}: rule {key!r} needs a value and a source")
        if not isinstance(entry["value"], (int, float)) or isinstance(entry["value"], bool):
            raise PartError(f"{path}: rule {key!r} must be a number")
        values[key] = float(entry["value"])
        sources[key] = str(entry["source"])
    slots = []
    for slot in (data.get("spec_slots") or {}).get("slots", []):
        if not isinstance(slot, dict) or not all(slot.get(k) for k in ("name", "meaning", "unit")):
            raise PartError(f"{path}: spec slot {slot!r} needs a name, a meaning and a unit")
        default = slot.get("default_rule")
        if default is not None and default not in values:
            raise PartError(f"{path}: spec slot {slot['name']!r} defaults to unknown rule {default!r}")
        slots.append({"name": str(slot["name"]), "meaning": str(slot["meaning"]), "unit": str(slot["unit"]),
                      "default_rule": default})
    return Rules(values, sources, dict(data.get("print_orientation", {})), path, slots)


# ---------------------------------------------------------------------------
# Envelopes (milestone M4 subset): keep-out and access volumes generated from datums only
# ---------------------------------------------------------------------------
#
# Each generator returns feature_graph Nodes of kind "envelope" (never printed) whose
# params are numbers computed from placed datums and part data. Every length comes
# from the caller (spec / rules values) or from part.json; there are no literals here.
# Box envelopes use the feature-graph box frame (centred in X and Y, base at Z = 0);
# extra params carry what later rules read without re-deriving it:
#   s0, s1  axial extent from the connector mouth along its axis (outward positive)
#   cw, ch  cross-section across the axis (horizontal width, vertical height)


def _horizontal_angle(u: Sequence[float], what: str) -> float:
    """Degrees about Z taking +X onto a horizontal direction (computed, never a literal angle)."""
    u = np.asarray(u, dtype=float)
    if abs(u[2]) > UNIT_TOL or np.linalg.norm(u[:2]) < UNIT_TOL:
        raise PartError(f"{what}: direction {np.round(u, 6).tolist()} is not horizontal; "
                        "only horizontal connector axes are supported so far")
    return math.degrees(math.atan2(u[1], u[0]))


def plug_sweep(conn_world: Mapping[str, Datum], plug_inst: PartInstance, clearance: float, travel: float,
               prefix: str = "plug") -> List["fg.Node"]:
    """The mating plug at full mate, its cable-end primitive swept outward by `travel`.

    conn_world: the connector's world datums {"mouth": Point, "axis": Axis} (axis = out of the mouth).
    The plug's PLUG_AXIS (+X of its frame, toward the cable) is aligned with the connector axis and
    its SEAT datum is put on the mouth. Each plug primitive becomes one envelope; the one reaching
    farthest toward the cable (the overmold) is extended by `travel` and has role plug_overmold, the
    others plug_shell. `clearance` grows every cross-section by that much per side.
    """
    mouth = np.asarray(conn_world["mouth"].at, dtype=float)
    u = np.asarray(conn_world["axis"].dir, dtype=float)
    u = u / np.linalg.norm(u)
    rot = _horizontal_angle(u, f"{prefix}: connector axis")
    rz = fg.rot_z_matrix(rot)
    seat = np.asarray(lookup_datum(plug_inst.datums, "SEAT").at, dtype=float)
    plug_axis = lookup_datum(plug_inst.datums, "PLUG_AXIS")
    if np.linalg.norm(np.asarray(plug_axis.dir, dtype=float)[1:]) > UNIT_TOL:
        raise PartError(f"{plug_inst.part_id}: PLUG_AXIS must be the frame's X axis")
    t = mouth - rz @ seat
    far = max(plug_inst.geometry, key=lambda g: g.bbox()[1][0])
    nodes = []
    for g in plug_inst.geometry:
        lo, hi = g.bbox()
        ext = travel if g is far else 0.0
        role = "plug_overmold" if g is far else "plug_shell"
        s0, s1 = float(lo[0] - seat[0]), float(hi[0] - seat[0] + ext)
        if g.primitive == "box":
            length, w, h = float(hi[0] - lo[0] + ext), float(hi[1] - lo[1]), float(hi[2] - lo[2])
            centre_local = np.array([lo[0] + length / 2, (lo[1] + hi[1]) / 2, lo[2] - clearance])
            centre = rz @ centre_local + t
            params = {"x": length, "y": w + 2 * clearance, "z": h + 2 * clearance,
                      "s0": s0, "s1": s1, "cw": w + 2 * clearance, "ch": h + 2 * clearance}
            pose = fg.Pose(offset=tuple(float(v) for v in centre), rot_z=rot)
            nodes.append(fg.Node(f"{prefix}_{g.id}", "envelope", "box", params, pose, role=role,
                                 part=plug_inst.part_id, source=f"rule:plug_sweep({plug_inst.part_id})", group=prefix))
        else:
            v = np.asarray(g.dir, dtype=float)
            v = v / np.linalg.norm(v)
            start = rz @ np.asarray(g.at, dtype=float) + t
            d = float(g.d + 2 * clearance)
            params = {"d": d, "h": float(g.h + ext), "s0": s0, "s1": s1, "cw": d, "ch": d}
            pose = fg.Pose(offset=tuple(float(x) for x in start), axis_dir=tuple(float(x) for x in rz @ v))
            nodes.append(fg.Node(f"{prefix}_{g.id}", "envelope", "cylinder", params, pose, role=role,
                                 part=plug_inst.part_id, source=f"rule:plug_sweep({plug_inst.part_id})", group=prefix))
    return nodes


def board_keepout(board_inst: PartInstance, board_pose: np.ndarray, above: float, below: float,
                  prefix: str = "board") -> List["fg.Node"]:
    """V-KO-TOP (board footprint, TOP up by `above`) and V-KO-BOT (footprint, BOTTOM down by `below`).
    The seat columns are separate envelopes (`column`), which the checks subtract."""
    lo, hi = fg.instance_world_bbox(board_inst, board_pose)
    top = transform(lookup_datum(board_inst.datums, "TOP"), board_pose).at[2]
    bottom = transform(lookup_datum(board_inst.datums, "BOTTOM"), board_pose).at[2]
    cx, cy = float((lo[0] + hi[0]) / 2), float((lo[1] + hi[1]) / 2)
    sx, sy = float(hi[0] - lo[0]), float(hi[1] - lo[1])
    return [
        fg.Node(f"{prefix}_ko_top", "envelope", "box", {"x": sx, "y": sy, "z": float(above)},
                fg.Pose(offset=(cx, cy, float(top))), role="keepout_top", source="rule:board_keepout"),
        fg.Node(f"{prefix}_ko_bot", "envelope", "box", {"x": sx, "y": sy, "z": float(below)},
                fg.Pose(offset=(cx, cy, float(bottom - below))), role="keepout_bottom", source="rule:board_keepout"),
    ]


def column(axis_datum: AxisList, i: int, diameter: float, z_from: float, z_to: "fg.Expr", role: str,
           prefix: str = "column", anchor: Optional[str] = None) -> "fg.Node":
    """A vertical cylinder on item i of an axis list (V-SEAT-k, V-HOLE-KO-k, V-DRIVER-k).

    anchor: the datum ref of that axis in the feature graph (e.g. "board.HOLE[2]"). The column is then posed
    on the datum, not at frozen floats, so it follows the part when the part's params change (ARCHITECTURE.md
    7.7). z_to may be an expression (a column that reaches a derived height, e.g. V-DRIVER above the rim).
    """
    p = axis_datum.item(i).at
    h = f"{z_to} - ({float(z_from)!r})" if isinstance(z_to, str) else float(z_to - z_from)
    if anchor:
        pose = fg.Pose(at=anchor, offset=(0, 0, float(z_from - p[2])))
    else:
        pose = fg.Pose(offset=(float(p[0]), float(p[1]), float(z_from)))
    return fg.Node(f"{prefix}_{i}", "envelope", "cylinder", {"d": float(diameter), "h": h}, pose, role=role,
                   source=f"rule:column({role})")


def content_envelope(parts: Sequence[Tuple[PartInstance, np.ndarray]], node_id: str,
                     role: str = "content") -> List["fg.Node"]:
    """V-PICO for a Pico on headers: one envelope node per geometry primitive of each (instance, pose), so the
    union of the list is the union of the reference solids of the module and its stack parts (ARCHITECTURE.md
    7.8: a check measures the reference parts, never an AABB proxy). Poses are built as in `plug_sweep`:
    rot_z from the instance pose, offset from pose . primitive `at`. Every node has group = node_id."""
    nodes = []
    k = 0
    for inst, pose in parts:
        pose = np.asarray(pose, dtype=float)
        r, t = pose[:3, :3], pose[:3, 3]
        rot = math.degrees(math.atan2(r[1, 0], r[0, 0]))
        if np.abs(r - fg.rot_z_matrix(rot)).max() > UNIT_TOL:
            raise PartError(f"{node_id}: {inst.part_id} pose is not a rotation about Z")
        for g in inst.geometry:
            src = f"rule:content_envelope({inst.part_id})"
            if g.primitive == "box":
                lo, hi = g.bbox()
                centre = r @ np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]]) + t
                size = hi - lo
                node = fg.Node(f"{node_id}_{k}", "envelope", "box",
                               {"x": float(size[0]), "y": float(size[1]), "z": float(size[2])},
                               fg.Pose(offset=tuple(float(v) for v in centre), rot_z=float(rot)), role=role,
                               part=inst.part_id, source=src, group=node_id)
            elif g.primitive == "cylinder":
                start = r @ np.asarray(g.at, dtype=float) + t
                node = fg.Node(f"{node_id}_{k}", "envelope", "cylinder", {"d": float(g.d), "h": float(g.h)},
                               fg.Pose(offset=tuple(float(v) for v in start),
                                       axis_dir=tuple(float(v) for v in r @ np.asarray(g.dir, dtype=float))),
                               role=role, part=inst.part_id, source=src, group=node_id)
            else:
                raise PartError(f"{node_id}: {inst.part_id}.{g.id}: no envelope for primitive {g.primitive!r}")
            nodes.append(node)
            k += 1
    return nodes
