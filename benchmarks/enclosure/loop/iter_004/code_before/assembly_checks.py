"""Typed geometric checks for --mode assembly (ARCHITECTURE.md section 5, milestone M5 subset).

Every check measures manifold3d solids and returns a `cad_checks.CheckResult` with
`passed`, a signed margin (>= 0 passes; margin_scale mm of slack = 1.0), the raw
value, `depends_on` and `evidence` (location bbox, volume). The recipes follow
rubric.md section 3 (the judge's reference implementation): the same
intersection-volume / `min_gap` clearance, the same hull-minus-solids cavity,
the same slab-minus-bodies apertures counted with `decompose()`, so the agent's
numbers can agree with the judge's.

The checks run twice per design: on the manifold solids the feature graph builds,
and on the delivered STL files (`measure_package`), whose results are the
package's `self_report.json`. Nothing here holds a number specific to one
request: tolerances come from design_rules.json and limits from the spec.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

import cad_checks as cc

try:
    import manifold3d as m3d
except ImportError:  # pragma: no cover
    m3d = None

L1_RULES = "rules"          # l1_id of the rule-derived checks (translation to L1s is milestone M10)
SEARCH_EXTRA = 5.0          # mm beyond the clearance that min_gap searches (rubric.md 3.2: c + 5)


def _result(check_id: str, typ: str, passed: bool, margin: float, unit: str, evidence: dict,
            depends_on: Optional[dict] = None) -> cc.CheckResult:
    if not math.isfinite(margin):
        margin = -1e9 if margin < 0 else 1e9
    return cc.CheckResult(check_id, L1_RULES, typ, bool(passed), round(float(margin), 6), unit,
                          depends_on or {}, evidence, layer=1, hard=True)


def _bbox(m) -> List[List[float]]:
    b = m.bounding_box()
    return [[round(float(v), 4) for v in b[:3]], [round(float(v), 4) for v in b[3:]]]


def union(solids: Sequence[Any]):
    solids = [s for s in solids if s is not None]
    if not solids:
        return m3d.Manifold()
    return m3d.Manifold.batch_boolean(list(solids), m3d.OpType.Add) if len(solids) > 1 else solids[0]


@dataclass
class Tol:
    """Measurement settings, all read from design_rules.json."""
    measure: float = 0.0          # measure_tol: pass at value >= limit - measure
    scale: float = 1.0            # margin_scale
    pen: float = 0.0              # interference_max: intersection volume counted as touching
    sliver: float = 0.0           # aperture_min_volume

    @classmethod
    def from_rules(cls, rules: Mapping[str, float]) -> "Tol":
        return cls(rules["measure_tol"], rules["margin_scale"], rules["interference_max"],
                   rules["aperture_min_volume"])


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------


def separable(bodies: Mapping[str, Any], overlap_max: float, tol: Tol, check_id: str = "separable") -> cc.CheckResult:
    """Each body is one valid shell; every pair overlaps by at most overlap_max (closed pose)."""
    shells = {name: len(b.decompose()) for name, b in bodies.items()}
    status = {name: str(b.status()).split(".")[-1] for name, b in bodies.items()}
    names = list(bodies)
    overlaps = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            overlaps[f"{a}^{b}"] = float((bodies[a] ^ bodies[b]).volume())
    worst = max(overlaps.values(), default=0.0)
    ok_status = all(s == "NoError" for s in status.values())
    shell_margin = min((1.0 if n == 1 else -float(abs(n - 1)) for n in shells.values()), default=1.0)
    margin = min(shell_margin, (overlap_max - worst) / tol.scale) if ok_status else -1.0
    passed = ok_status and all(n == 1 for n in shells.values()) and worst <= overlap_max
    return _result(check_id, "separable", passed, margin, "count",
                   {"shells": shells, "status": status, "overlap_mm3": overlaps, "overlap_max": overlap_max,
                    "detail": f"shells {shells}, worst overlap {worst:.4g} mm3 (max {overlap_max:g})"},
                   {"bodies": names})


def clear_of(bodies, volume, clearance: float, tol: Tol, minus=None, check_id: str = "clear_of",
             what: str = "volume", depends_on: Optional[dict] = None) -> cc.CheckResult:
    """rubric.md 3.2: penetration volume first; if none, min_gap(bodies, volume) >= clearance."""
    vol = volume - minus if minus is not None else volume
    inter = bodies ^ vol
    pen = float(inter.volume())
    if pen > tol.pen:
        margin = -(pen ** (1.0 / 3.0) + clearance) / tol.scale
        return _result(check_id, "clear_of", False, margin, "mm",
                       {"penetration_mm3": round(pen, 6), "gap": None, "clearance": clearance, "where": _bbox(inter),
                        "detail": f"bodies penetrate {what} by {pen:.4g} mm3 at {_bbox(inter)}"}, depends_on)
    gap = float(bodies.min_gap(vol, clearance + SEARCH_EXTRA))
    passed = gap >= clearance - tol.measure
    return _result(check_id, "clear_of", passed, (gap - clearance + tol.measure) / tol.scale, "mm",
                   {"penetration_mm3": round(pen, 6), "gap": round(gap, 6), "clearance": clearance,
                    "detail": f"min gap to {what} {gap:.4f} mm (need >= {clearance:g})"}, depends_on)


def inside(volume, bodies: Sequence[Any], clearance: float, tol: Tol, minus=None, check_id: str = "inside",
           what: str = "volume") -> cc.CheckResult:
    """rubric.md 3.3: the volume lies in the closed bodies' hull, `clearance` from the solids and the outside."""
    vol = volume - minus if minus is not None else volume
    solids = union(bodies)
    hull = solids.hull()
    outside = vol - hull
    out = float(outside.volume())
    if out > tol.pen:
        return _result(check_id, "inside", False, -(out ** (1.0 / 3.0) + clearance) / tol.scale, "mm",
                       {"outside_mm3": round(out, 6), "where": _bbox(outside), "clearance": clearance,
                        "detail": f"{what} sticks out of the enclosure by {out:.4g} mm3 at {_bbox(outside)}"})
    lo, hi = np.asarray(hull.bounding_box()[:3]), np.asarray(hull.bounding_box()[3:])
    pad = 2 * (clearance + SEARCH_EXTRA) + 1.0
    box = m3d.Manifold.cube((hi - lo + 2 * pad).tolist()).translate((lo - pad).tolist())
    shell = box - hull
    search = clearance + SEARCH_EXTRA
    d_solid = float(vol.min_gap(solids, search))
    d_out = float(vol.min_gap(shell, search))
    d = min(d_solid, d_out)
    return _result(check_id, "inside", d >= clearance - tol.measure, (d - clearance + tol.measure) / tol.scale, "mm",
                   {"outside_mm3": round(out, 6), "gap_to_solids": round(d_solid, 6), "gap_to_outside": round(d_out, 6),
                    "clearance": clearance, "detail": f"{what}: {d:.4f} mm from the enclosure (need >= {clearance:g})"})


def apertures(bodies, slab, tol: Tol) -> List[Any]:
    """rubric.md 3.4: the regions of a wall slab not filled by the bodies, slivers dropped."""
    return [r for r in (slab - bodies).decompose() if r.volume() >= tol.sliver]


def aperture_count(bodies, slab, n: int, tol: Tol, check_id: str = "aperture_count", wall: str = "") -> cc.CheckResult:
    regions = apertures(bodies, slab, tol)
    count = len(regions)
    return _result(check_id, "aperture_count", count == n, -float(abs(n - count)), "count",
                   {"count": count, "expected": n, "regions": [_bbox(r) for r in regions],
                    "detail": f"wall {wall}: {count} opening(s), expected {n}"})


def aperture_oversize(aperture, normal_axis: int, env_w: float, env_h: float, max_excess: float, tol: Tol,
                      check_id: str = "aperture_oversize") -> cc.CheckResult:
    """Per-side excess of an aperture's cross-section bbox over the plug envelope's cross-section."""
    lo, hi = np.asarray(aperture.bounding_box()[:3]), np.asarray(aperture.bounding_box()[3:])
    across = 1 - normal_axis if normal_axis < 2 else 0
    w, h = float(hi[across] - lo[across]), float(hi[2] - lo[2])
    excess = max((w - env_w) / 2, (h - env_h) / 2)
    passed = excess <= max_excess + tol.measure
    return _result(check_id, "aperture_oversize", passed, (max_excess - excess + tol.measure) / tol.scale, "mm",
                   {"opening": [round(w, 4), round(h, 4)], "envelope": [round(env_w, 4), round(env_h, 4)],
                    "excess_per_side": round(excess, 6), "max": max_excess, "where": _bbox(aperture),
                    "detail": f"opening {w:.3f} x {h:.3f} vs plug {env_w:.3f} x {env_h:.3f}: "
                              f"{excess:.3f} mm per side (max {max_excess:g})"})


def seated(board_bottom: float, standoff_tops: Sequence[float], hole_axes: Sequence[Sequence[float]],
           pilot_axes: Sequence[Optional[Sequence[float]]], gap_max: float, residual_max: float, tol: Tol,
           check_id: str = "seated") -> cc.CheckResult:
    """Board underside on the standoff tops (gap) and every hole coaxial with a pilot (axis residual)."""
    gaps = [abs(board_bottom - t) if t is not None else math.inf for t in standoff_tops]
    residuals = []
    for h in hole_axes:
        cands = [p for p in pilot_axes if p is not None]
        residuals.append(min((float(np.linalg.norm(np.subtract(h[:2], p[:2]))) for p in cands), default=math.inf))
    gap = max(gaps, default=math.inf)
    res = max(residuals, default=math.inf)
    passed = gap <= gap_max and res <= residual_max and len(standoff_tops) == len(hole_axes)
    margin = min(gap_max - gap, residual_max - res) / tol.scale
    return _result(check_id, "seated", passed, margin, "mm",
                   {"gaps": [round(g, 6) for g in gaps], "residuals": [round(r, 6) for r in residuals],
                    "detail": f"worst standoff gap {gap:.4f} mm (max {gap_max:g}), worst hole-pilot offset "
                              f"{res:.4f} mm (max {residual_max:g})"})


def bbox_within(bodies, max_xyz: Sequence[float], tol: Tol, x_longest: bool = False,
                check_id: str = "bbox_within") -> cc.CheckResult:
    lo, hi = np.asarray(bodies.bounding_box()[:3]), np.asarray(bodies.bounding_box()[3:])
    size = hi - lo
    margins = [(float(m) - float(s) + tol.measure) / tol.scale for s, m in zip(size, max_xyz)]
    if x_longest:
        margins.append((float(size[0] - size[1])) / tol.scale)
    margin = min(margins)
    return _result(check_id, "bbox_within", margin >= 0 and all(m >= 0 for m in margins), margin, "mm",
                   {"size": [round(float(s), 4) for s in size], "max": list(max_xyz), "x_longest": x_longest,
                    "detail": f"outside {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} mm, max "
                              f"{max_xyz[0]:g} x {max_xyz[1]:g} x {max_xyz[2]:g}" + (" with X longest" if x_longest else "")})


def value_at_most(check_id: str, typ: str, value: float, limit: float, tol: Tol, detail: str) -> cc.CheckResult:
    """A design-level inequality on resolved numbers (port_below_split, pilot_depth)."""
    return _result(check_id, typ, value <= limit + tol.measure, (limit - value + tol.measure) / tol.scale, "mm",
                   {"value": round(value, 6), "limit": round(limit, 6), "detail": detail})


# ---------------------------------------------------------------------------
# Mesh measurements used by `seated` (work on any manifold: graph-built or loaded from STL)
# ---------------------------------------------------------------------------


def _column(xy: Sequence[float], d: float, z0: float, z1: float, seg: int):
    return m3d.Manifold.cylinder(z1 - z0, d / 2, d / 2, seg).translate([float(xy[0]), float(xy[1]), z0])


def standoff_top(base, xy: Sequence[float], search_d: float, z_lo: float, z_hi: float, seg: int) -> Optional[float]:
    """Highest point of the body inside a vertical column (the top of the standoff on that axis)."""
    inter = base ^ _column(xy, search_d, z_lo, z_hi, seg)
    if inter.is_empty():
        return None
    return float(inter.bounding_box()[5])


def pilot_axis(base, xy: Sequence[float], search_d: float, z: float, depth: float, seg: int) -> Optional[List[float]]:
    """The axis of the hole nearest `xy` in a thin layer below z: the air region inside the search
    column that does not touch the column's outside."""
    region = _column(xy, search_d, z - depth, z - depth / 2, seg)
    air = region - base
    rlo, rhi = np.asarray(region.bounding_box()[:3]), np.asarray(region.bounding_box()[3:])
    best = None
    for comp in air.decompose():
        lo, hi = np.asarray(comp.bounding_box()[:3]), np.asarray(comp.bounding_box()[3:])
        if np.any(lo[:2] <= rlo[:2] + 1e-3) or np.any(hi[:2] >= rhi[:2] - 1e-3):
            continue
        c = (lo + hi) / 2
        dist = float(np.linalg.norm(c[:2] - np.asarray(xy[:2], dtype=float)))
        if best is None or dist < best[0]:
            best = (dist, c[:2].tolist())
    return best[1] if best else None


# ---------------------------------------------------------------------------
# A check plan: what to measure, independent of where the bodies come from
# ---------------------------------------------------------------------------


@dataclass
class Plan:
    """The frozen rule-derived check set with the reference and envelope solids it measures against.

    specs: [{"id", "type", "args"}]; volumes: name -> manifold (references, envelopes, slabs);
    values: resolved design numbers (split, cut tops, pilot depths) for design-level checks.
    """
    specs: List[dict] = field(default_factory=list)
    volumes: Dict[str, Any] = field(default_factory=dict)
    tol: Tol = field(default_factory=Tol)
    seg: int = 64

    def add(self, check_id: str, typ: str, text: str, **args) -> None:
        self.specs.append({"id": check_id, "type": typ, "text": text, "args": args})

    def checks(self) -> List[cc.Check]:
        return [cc.Check(id=s["id"], l1_id=L1_RULES, type=s["type"], params=_jsonable(s["args"]), text=s["text"])
                for s in self.specs]


def _jsonable(v):
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, (np.floating, np.integer)):
        return v.item()
    return v


def run_plan(plan: Plan, bodies: Mapping[str, Any]) -> List[cc.CheckResult]:
    """Every check of the plan on the given bodies (manifold solids or meshes loaded from STL)."""
    all_bodies = union(list(bodies.values()))
    vols = plan.volumes
    out = []
    for s in plan.specs:
        a, cid, typ = s["args"], s["id"], s["type"]
        if typ == "separable":
            out.append(separable({k: bodies[k] for k in a["bodies"]}, a["overlap_max"], plan.tol, cid))
        elif typ == "clear_of":
            out.append(clear_of(all_bodies, vols[a["volume"]], a["clearance"], plan.tol,
                                vols[a["minus"]] if a.get("minus") else None, cid, a["volume"]))
        elif typ == "inside":
            out.append(inside(vols[a["volume"]], list(bodies.values()), a["clearance"], plan.tol,
                              vols[a["minus"]] if a.get("minus") else None, cid, a["volume"]))
        elif typ == "aperture_count":
            out.append(aperture_count(all_bodies, vols[a["slab"]], a["n"], plan.tol, cid, a["wall"]))
        elif typ == "aperture_oversize":
            regions = apertures(all_bodies, vols[a["slab"]], plan.tol)
            hit = _region_at(regions, a["point"])
            if hit is None:
                out.append(_result(cid, "aperture_oversize", False, -1.0, "mm",
                                   {"detail": f"no opening on {a['wall']} at the port axis {a['point']}"}))
            else:
                out.append(aperture_oversize(hit, a["normal_axis"], a["env_w"], a["env_h"], a["max"], plan.tol, cid))
        elif typ == "seated":
            base = bodies[a["body"]]
            tops = [standoff_top(base, h, a["search_d"], a["z_lo"], a["z_hi"], plan.seg) for h in a["holes"]]
            pilots = [pilot_axis(base, h, a["search_d"], t, a["probe_depth"], plan.seg) if t is not None else None
                      for h, t in zip(a["holes"], tops)]
            out.append(seated(a["board_bottom"], tops, a["holes"], pilots, a["gap_max"], a["residual_max"],
                              plan.tol, cid))
        elif typ == "bbox_within":
            out.append(bbox_within(all_bodies, a["max"], plan.tol, a.get("x_longest", False), cid))
        elif typ in ("port_below_split", "pilot_depth"):
            out.append(value_at_most(cid, typ, a["value"], a["limit"], plan.tol, a["detail"]))
        else:
            raise ValueError(f"unknown check type {typ!r}")
    return out


def _region_at(regions: Sequence[Any], point: Sequence[float]):
    """The aperture region whose bbox holds the point across the wall (nearest centre otherwise)."""
    best = None
    p = np.asarray(point, dtype=float)
    for r in regions:
        lo, hi = np.asarray(r.bounding_box()[:3]), np.asarray(r.bounding_box()[3:])
        d = float(np.linalg.norm(np.maximum(np.maximum(lo - p, p - hi), 0.0)))
        if best is None or d < best[0]:
            best = (d, r)
    return best[1] if best and best[0] <= 1e-6 else None


# ---------------------------------------------------------------------------
# Delivered meshes
# ---------------------------------------------------------------------------


def load_mesh(path: Path):
    """rubric.md 3.1: trimesh -> manifold3d (status must be NoError)."""
    import trimesh
    tm = trimesh.load(str(path), force="mesh")
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                                 tri_verts=np.asarray(tm.faces, np.uint32)))


def measure_package(pkg_dir: Path, plan: Plan, bodies: Sequence[str]) -> dict:
    """Re-measure the delivered `<body>.stl` files with the plan: this is self_report.json."""
    pkg_dir = Path(pkg_dir)
    loaded, errors = {}, []
    for name in bodies:
        path = pkg_dir / f"{name}.stl"
        try:
            loaded[name] = load_mesh(path)
        except Exception as e:  # a missing or unreadable STL is a failed measurement, not a crash
            errors.append(f"{path.name}: {e}")
    results = run_plan(plan, loaded) if not errors else []
    return {
        "source": "delivered STL files, rubric.md section 3 recipes",
        "bodies": {n: {"file": f"{n}.stl", "shells": len(m.decompose()), "status": str(m.status()).split(".")[-1],
                       "volume": round(float(m.volume()), 4), "bbox": _bbox(m)} for n, m in loaded.items()},
        "errors": errors,
        "all_passed": bool(results) and all(r.passed for r in results),
        "results": [r.to_dict() for r in results],
    }


def write_json(path: Path, data: Any) -> Path:
    path.write_text(json.dumps(_jsonable(data), indent=2, default=str))
    return path
