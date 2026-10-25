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
FACE_TOUCH = 1e-4           # mm: a region whose bbox comes this close to a slab face plane reaches it (STL is float32)
FACE_SLICE = 1e-3           # mm: thickness of the face slice that confirms a region really meets a face plane


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


def _capped(d: float, search: float, tol: Tol) -> bool:
    """min_gap returns its search radius when nothing lies inside it: that value is a lower bound, not a distance."""
    return d >= search - tol.measure - 1e-9


def _bound(d: Optional[float], capped: bool) -> str:
    """'4.2000' for a measured distance, '≥ 5.2000' for a capped one (iteration 011 C3)."""
    return "None" if d is None else f"{'≥ ' if capped else ''}{d:.4f}"


def _clear_measure(bodies, vol, clearance: float, tol: Tol) -> dict:
    """rubric.md 3.2 on one (already exempted) volume: penetration volume, then min_gap. d is None when they penetrate.
    When nothing lies within the search radius, d is that radius and the row says so (d_capped, d_at_least)."""
    inter = bodies ^ vol
    pen = float(inter.volume())
    if pen > tol.pen:
        return {"penetration_mm3": round(pen, 6), "d": None, "where": _bbox(inter), "_pen": pen}
    search = clearance + SEARCH_EXTRA
    d = float(bodies.min_gap(vol, search))
    out = {"penetration_mm3": round(pen, 6), "d": round(d, 6)}
    if _capped(d, search, tol):
        out.update(d_capped=True, d_at_least=round(search, 6))
    return out


def _per_source(parts: Optional[Mapping[str, Any]], labels: Optional[Mapping[str, str]], minus, measure) -> Optional[dict]:
    """ARCHITECTURE.md 7.8: every member of a composite volume measured alone by the same recipe and the same
    `minus`, so the d of any union an independent reader forms is the minimum of its members' d."""
    if not parts:
        return None
    out = {}
    for nid, solid in parts.items():
        vol = solid - minus if minus is not None else solid
        row = {"part": (labels or {}).get(nid, nid)}
        if vol.is_empty():
            row.update(d=None, empty=True)
        else:
            row.update({k: v for k, v in measure(vol).items() if not k.startswith("_")})
        out[nid] = row
    return out


def clear_of(bodies, volume, clearance: float, tol: Tol, minus=None, check_id: str = "clear_of",
             what: str = "volume", depends_on: Optional[dict] = None, parts: Optional[Mapping[str, Any]] = None,
             labels: Optional[Mapping[str, str]] = None) -> cc.CheckResult:
    """rubric.md 3.2: penetration volume first; if none, min_gap(bodies, volume) >= clearance.
    parts: {node id: solid} of a composite volume; each is measured too (evidence.per_source)."""
    vol = volume - minus if minus is not None else volume
    m = _clear_measure(bodies, vol, clearance, tol)
    per = _per_source(parts, labels, minus, lambda v: _clear_measure(bodies, v, clearance, tol))
    extra = {"per_source": per} if per is not None else {}
    if m["d"] is None:
        pen = m["_pen"]
        margin = -(pen ** (1.0 / 3.0) + clearance) / tol.scale
        return _result(check_id, "clear_of", False, margin, "mm",
                       {"penetration_mm3": m["penetration_mm3"], "gap": None, "d": None, "clearance": clearance,
                        "where": m["where"], **extra,
                        "detail": f"bodies penetrate {what} by {pen:.4g} mm3 at {m['where']}"}, depends_on)
    gap = m["d"]
    passed = gap >= clearance - tol.measure
    return _result(check_id, "clear_of", passed, (gap - clearance + tol.measure) / tol.scale, "mm",
                   {"penetration_mm3": m["penetration_mm3"], "gap": gap, "d": gap, "clearance": clearance,
                    **{k: m[k] for k in ("d_capped", "d_at_least") if k in m}, **extra,
                    "detail": f"min gap to {what} {_bound(gap, bool(m.get('d_capped')))} mm (need >= {clearance:g})"},
                   depends_on)


def _hull_shell(solids, clearance: float):
    """The closed bodies' hull and the outside of it (a padded box minus the hull), for rubric.md 3.3."""
    hull = solids.hull()
    lo, hi = np.asarray(hull.bounding_box()[:3]), np.asarray(hull.bounding_box()[3:])
    pad = 2 * (clearance + SEARCH_EXTRA) + 1.0
    box = m3d.Manifold.cube((hi - lo + 2 * pad).tolist()).translate((lo - pad).tolist())
    return hull, box - hull


def _inside_measure(vol, solids, hull, shell, clearance: float, tol: Tol) -> dict:
    """rubric.md 3.3 on one (already exempted) volume: volume outside the hull, then the gaps to the solids and to
    the outside. d is None when it sticks out."""
    outside = vol - hull
    out = float(outside.volume())
    if out > tol.pen:
        return {"outside_mm3": round(out, 6), "d": None, "where": _bbox(outside), "_out": out}
    search = clearance + SEARCH_EXTRA
    d_solid = float(vol.min_gap(solids, search))
    d_out = float(vol.min_gap(shell, search))
    row = {"outside_mm3": round(out, 6), "gap_to_solids": round(d_solid, 6), "gap_to_outside": round(d_out, 6),
           "d": round(min(d_solid, d_out), 6)}
    for key, v in (("gap_to_solids", d_solid), ("gap_to_outside", d_out)):
        if _capped(v, search, tol):
            row[f"{key}_capped"] = True
    if _capped(min(d_solid, d_out), search, tol):
        row.update(d_capped=True, d_at_least=round(search, 6))
    return row


def inside(volume, bodies: Sequence[Any], clearance: float, tol: Tol, minus=None, check_id: str = "inside",
           what: str = "volume", parts: Optional[Mapping[str, Any]] = None,
           labels: Optional[Mapping[str, str]] = None) -> cc.CheckResult:
    """rubric.md 3.3: the volume lies in the closed bodies' hull, `clearance` from the solids and the outside.
    parts: {node id: solid} of a composite volume; each is measured too (evidence.per_source); the hull once."""
    vol = volume - minus if minus is not None else volume
    solids = union(bodies)
    hull, shell = _hull_shell(solids, clearance)
    m = _inside_measure(vol, solids, hull, shell, clearance, tol)
    per = _per_source(parts, labels, minus, lambda v: _inside_measure(v, solids, hull, shell, clearance, tol))
    extra = {"per_source": per} if per is not None else {}
    if m["d"] is None:
        out = m["_out"]
        return _result(check_id, "inside", False, -(out ** (1.0 / 3.0) + clearance) / tol.scale, "mm",
                       {"outside_mm3": m["outside_mm3"], "where": m["where"], "d": None, "clearance": clearance, **extra,
                        "detail": f"{what} sticks out of the enclosure by {out:.4g} mm3 at {m['where']}"})
    d = m["d"]
    return _result(check_id, "inside", d >= clearance - tol.measure, (d - clearance + tol.measure) / tol.scale, "mm",
                   {"outside_mm3": m["outside_mm3"], "gap_to_solids": m["gap_to_solids"],
                    "gap_to_outside": m["gap_to_outside"], "d": d, "clearance": clearance,
                    **{k: v for k, v in m.items() if k.endswith("_capped") or k == "d_at_least"}, **extra,
                    "detail": f"{what}: {_bound(d, bool(m.get('d_capped')))} mm from the enclosure "
                              f"(need >= {clearance:g})"})


def apertures(bodies, slab, tol: Tol) -> List[Any]:
    """rubric.md 3.4: the regions of a wall slab not filled by the bodies, slivers dropped."""
    return [r for r in (slab - bodies).decompose() if r.volume() >= tol.sliver]


def _reaches(region, slab, axis: int, upper: bool, min_extent: float = 0.0) -> bool:
    """The region meets the slab's face plane normal to `axis`: its bbox reaches the plane, and a thin slice at the
    face intersects it in a real cross-section, at least `min_extent` across along both in-plane axes
    (ARCHITECTURE.md 7.10). With min_extent 0 any positive slice volume counts (the iteration 006 test), so a skin
    of float-noise thickness could make a region reach a face."""
    rb, sb = region.bounding_box(), slab.bounding_box()
    face = sb[axis + 3] if upper else sb[axis]
    if (rb[axis + 3] < face - FACE_TOUCH) if upper else (rb[axis] > face + FACE_TOUCH):
        return False
    lo, hi = list(sb[:3]), list(sb[3:])
    thick = min(FACE_SLICE, (sb[axis + 3] - sb[axis]) / 4)
    lo[axis], hi[axis] = (face - thick, face) if upper else (face, face + thick)
    cut = m3d.Manifold.cube([hi[k] - lo[k] for k in range(3)]).translate(lo)
    inter = region ^ cut
    if float(inter.volume()) <= 0.0:
        return False
    b = inter.bounding_box()
    return all(b[k + 3] - b[k] >= min_extent for k in range(3) if k != axis)


def classify_apertures(regions: Sequence[Any], slab, normal_axis: int, cuts: Optional[Mapping[str, Any]] = None,
                       tol: Optional[Tol] = None) -> List[dict]:
    """ARCHITECTURE.md 7.9: each aperture region of a wall slab is `through` (it reaches both face planes of the
    wall, so it is an opening) or `blind` (anything else: a pilot or a hole that stops inside the wall). `nodes`
    are the cut nodes (id -> solid) the region intersects. A face is reached only by a cross-section at least
    tol.measure across in both in-plane directions (ARCHITECTURE.md 7.10)."""
    pen = tol.pen if tol is not None else 0.0
    ext = tol.measure if tol is not None else 0.0
    out = []
    for r in regions:
        through = _reaches(r, slab, normal_axis, False, ext) and _reaches(r, slab, normal_axis, True, ext)
        nodes = sorted(nid for nid, c in (cuts or {}).items() if float((r ^ c).volume()) > pen)
        out.append({"class": "through" if through else "blind", "bbox": _bbox(r), "nodes": nodes,
                    "volume": round(float(r.volume()), 4)})
    return out


def aperture_count(bodies, slab, n: int, tol: Tol, check_id: str = "aperture_count", wall: str = "",
                   normal_axis: Optional[int] = None, cuts: Optional[Mapping[str, Any]] = None) -> cc.CheckResult:
    """rubric.md 3.4 regions of a wall slab. With `normal_axis` (the wall's normal) each region is classified and
    only `through` regions count as openings (blind pilots and lid holes are listed in evidence); without it
    every region counts."""
    regions = apertures(bodies, slab, tol)
    if normal_axis is None:
        count = len(regions)
        return _result(check_id, "aperture_count", count == n, -float(abs(n - count)), "count",
                       {"count": count, "expected": n, "regions": [_bbox(r) for r in regions],
                        "detail": f"wall {wall}: {count} opening(s), expected {n}"})
    rows = classify_apertures(regions, slab, normal_axis, cuts, tol)
    count = sum(r["class"] == "through" for r in rows)
    blind = [{"nodes": r["nodes"], "bbox": r["bbox"]} for r in rows if r["class"] == "blind"]
    return _result(check_id, "aperture_count", count == n, -float(abs(n - count)), "count",
                   {"count": count, "through": count, "blind": blind, "total": len(rows), "expected": n,
                    "regions": rows,
                    "detail": f"wall {wall}: {count} through opening(s), expected {n}; {len(blind)} blind region(s)"
                              + (f" ({', '.join(sorted({x for b in blind for x in b['nodes']}))})" if blind else "")})


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


def value_at_least(check_id: str, typ: str, value: float, limit: float, tol: Tol, detail: str) -> cc.CheckResult:
    """A one-sided minimum on resolved numbers (pilot_engagement, boss_od, lip_engagement; ARCHITECTURE.md 7.9)."""
    return _result(check_id, typ, value >= limit - tol.measure, (value - limit + tol.measure) / tol.scale, "mm",
                   {"value": round(value, 6), "limit": round(limit, 6), "detail": detail})


def value_in_band(check_id: str, typ: str, value: float, lo: float, hi: float, tol: Tol, detail: str) -> cc.CheckResult:
    """A two-sided band on a resolved number (pilot_band, ARCHITECTURE.md 7.13): passes at lo - measure_tol <= value <=
    hi + measure_tol; the margin is the distance to the nearer limit."""
    margin = (min(value - lo, hi - value) + tol.measure) / tol.scale
    return _result(check_id, typ, lo - tol.measure <= value <= hi + tol.measure, margin, "mm",
                   {"value": round(value, 6), "lo": round(lo, 6), "hi": round(hi, 6), "detail": detail})


SLICE_AXES = ((1, 2), (2, 0), (0, 1))   # in-plane (u, v) world axes of a slice normal to X, Y, Z (right-handed)
RIM_STEP = 10.0                          # rim sample spacing along the opening's outline, in units of measure_tol


def _slice_rings(solid, axis: int, plane: float) -> List[np.ndarray]:
    """The closed outlines of a solid's cross-section at `plane` along `axis`, as (u, v) rings (SLICE_AXES)."""
    u, v = SLICE_AXES[axis]
    rot = np.zeros((3, 4))
    rot[0, u] = rot[1, v] = rot[2, axis] = 1.0
    return [np.asarray(p, float) for p in solid.transform(rot).slice(float(plane)).to_polygons() if len(p) >= 2]


def _ring_edges(rings: Sequence[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    if not rings:
        return np.zeros((0, 2)), np.zeros((0, 2))
    return np.vstack(rings), np.vstack([np.roll(r, -1, axis=0) for r in rings])


def _seg_dist(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """(N, M) distances from points p (N, 2) to segments a-b (M, 2), and the (N, M) segment parameters t."""
    ab = b - a
    ll = np.maximum((ab ** 2).sum(axis=1), 1e-30)
    t = np.clip(((p[:, None, :] - a[None]) * ab[None]).sum(axis=2) / ll[None], 0.0, 1.0)
    q = a[None] + t[..., None] * ab[None]
    return np.linalg.norm(p[:, None, :] - q, axis=2), t


def _rim_samples(a: np.ndarray, b: np.ndarray, step: float) -> np.ndarray:
    """Points along the segments a-b: their vertices plus subdivisions, so no gap is longer than `step`."""
    out = []
    for p, q in zip(a, b):
        n = max(1, int(math.ceil(float(np.linalg.norm(q - p)) / step)))
        out.append(p[None] + (np.arange(n)[:, None] / n) * (q - p)[None])
    return np.vstack(out) if out else np.zeros((0, 2))


def _world(axis: int, plane: float, uv: Sequence[float]) -> List[float]:
    u, v = SLICE_AXES[axis]
    p = [0.0, 0.0, 0.0]
    p[axis], p[u], p[v] = float(plane), float(uv[0]), float(uv[1])
    return [round(x, 4) for x in p]


def ligament(body, cut, axis: int, plane: float, minimum: float, tol: Tol, check_id: str = "ligament",
             floor_z: Optional[float] = None, neighbours: Optional[Mapping[str, Any]] = None,
             what: str = "the opening") -> cc.CheckResult:
    """ARCHITECTURE.md 7.12 (L2.8.3): the material round an opening, in the cross-section normal to its axis at
    `plane` (the middle of the material it passes through). Rim samples are the points of the cut's outline that lie
    on the body's outline (where the opening has a wall); the other boundary is every body edge not on the cut's
    outline (outer edges, the seam, neighbouring openings). The ligament is the smallest rim-to-other-boundary 2-D
    distance, never larger than an outward ray's material length, so the agent errs against the design. With
    `floor_z`, the height of the opening's lowest rim point above the floor top counts too. An empty slice or no rim
    is a failure (margin -1), never a vacuous pass."""
    s_rings, c_rings = _slice_rings(body, axis, plane), _slice_rings(cut, axis, plane)
    base_ev = {"minimum": minimum, "plane": round(float(plane), 6), "axis": int(axis)}
    sa, sb = _ring_edges(s_rings)
    ca_, cb = _ring_edges(c_rings)
    rim = np.zeros((0, 2))
    if len(sa) and len(ca_):
        pts = _rim_samples(ca_, cb, max(tol.measure * RIM_STEP, 1e-3))
        on_body = _seg_dist(pts, sa, sb)[0].min(axis=1) <= FACE_TOUCH
        rim = pts[on_body]
    if not len(rim):
        return _result(check_id, "ligament", False, -1.0, "mm", dict(
            base_ev, ligament=None, detail=f"no material round {what} at {axis_name(axis)} = {plane:.3f}"))
    mid = (sa + sb) / 2
    other = _seg_dist(mid, ca_, cb)[0].min(axis=1) > FACE_TOUCH
    rows = []
    if other.any():
        oa, ob = sa[other], sb[other]
        dist, t = _seg_dist(rim, oa, ob)
        i, j = np.unravel_index(int(np.argmin(dist)), dist.shape)
        near = oa[j] + t[i, j] * (ob[j] - oa[j])
        toward = "outer"
        for name, solid in (neighbours or {}).items():
            na, nb = _ring_edges(_slice_rings(solid, axis, plane))
            if len(na) and float(_seg_dist(near[None], na, nb)[0].min()) <= FACE_TOUCH:
                toward = name
                break
        rows.append((float(dist[i, j]), toward, _world(axis, plane, rim[i]), _world(axis, plane, near)))
    if floor_z is not None:
        z = np.array([_world(axis, plane, p)[2] for p in rim])
        k = int(np.argmin(z))
        low = _world(axis, plane, rim[k])
        rows.append((float(z[k] - floor_z), "floor_top", low, low[:2] + [round(float(floor_z), 4)]))
    if not rows:
        return _result(check_id, "ligament", False, -1.0, "mm", dict(
            base_ev, ligament=None, detail=f"no boundary round {what} at {axis_name(axis)} = {plane:.3f}"))
    lig, toward, at, to = min(rows, key=lambda r: r[0])
    passed = lig >= minimum - tol.measure
    return _result(check_id, "ligament", passed, (lig - minimum + tol.measure) / tol.scale, "mm", dict(
        base_ev, ligament=round(lig, 6), toward=toward, where=[at, to], rim_samples=int(len(rim)),
        needed=f"material radius at {at} >= hole edge + {minimum:g} mm",
        detail=f"{lig:.4f} mm of material round {what} toward {toward} at {axis_name(axis)} = {plane:.3f} "
               f"(need >= {minimum:g})"))


def axis_name(axis: int) -> str:
    return "xyz"[axis]


def grid_conformance(check_id: str, value: float, limit: float, unverified: Sequence[str], tol: Tol,
                     evidence: Mapping[str, Any]) -> cc.CheckResult:
    """Every part with pin data has its pins within `limit` of the board grid; a part with a connector but
    no pin data cannot be verified and fails (the rubric counts UNVERIFIED as FAIL)."""
    unverified = list(unverified)
    margin = (limit - value + tol.measure) / tol.scale
    if unverified:
        margin = min(margin, -float(len(unverified)))
    passed = value <= limit + tol.measure and not unverified
    detail = f"worst pin-to-grid residual {value:.4f} mm (max {limit:g})"
    if unverified:
        detail += f"; no pin data: {', '.join(unverified)}"
    if evidence.get("conflict"):
        detail += f"; conflict: {evidence['conflict']}"
    return _result(check_id, "grid_conformance", passed, margin, "mm",
                   dict(evidence, value=round(value, 6), limit=round(limit, 6), no_pin_data=unverified, detail=detail))


def text_coverage(check_id: str, uncovered: Sequence[dict], covered: Sequence[dict],
                  evidence: Mapping[str, Any]) -> cc.CheckResult:
    """ARCHITECTURE.md 7.10: every content connector whose mating plug the request or an L1 names has a plug check
    (it is exposed). margin = -(uncovered count). A graph-data check: the same on the solids and on the STLs."""
    uncovered, covered = list(uncovered), list(covered)
    detail = (f"{len(covered)} named plug connection(s) covered" + (
        "; uncovered: " + "; ".join(f"{u['item']}.{u['connector']} takes {u['plug']} named by "
                                    f"{', '.join(e['source'] for e in u['evidence'])}" for u in uncovered)
        if uncovered else ""))
    return _result(check_id, "coverage", not uncovered, -float(len(uncovered)), "count",
                   dict(evidence, uncovered=uncovered, covered=covered, detail=detail))


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
    sources: volume name -> the node ids it was built from (the no-dead-envelope audit reads it).
    parts: composite volume -> its member solids, so clear_of / inside report per-source d (ARCHITECTURE.md 7.8).
    A clear_of spec may name `bodies` (a subset of body names, default all), e.g. V-DRIVER with the lid off, or a
    `subject` volume in place of the bodies (a check between reference volumes, e.g. plug_refs_*).
    """
    specs: List[dict] = field(default_factory=list)
    volumes: Dict[str, Any] = field(default_factory=dict)
    tol: Tol = field(default_factory=Tol)
    seg: int = 64
    sources: Dict[str, List[str]] = field(default_factory=dict)    # volume name -> the graph nodes it is built from
    parts: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # composite volume -> {source node id: solid}
    labels: Dict[str, str] = field(default_factory=dict)            # source node id -> catalogue id (or role)
    references: Dict[str, str] = field(default_factory=dict)        # reference node id -> catalogue id

    def add(self, check_id: str, typ: str, text: str, slots: Sequence[str] = (), parts: Sequence[str] = (),
            **args) -> None:
        """slots: the spec slots whose values the check uses; parts: the catalogue ids it concerns. Both only feed the
        deterministic L1 trace (assembly.trace_links, ARCHITECTURE.md 7.10); they are not measurement arguments."""
        self.specs.append({"id": check_id, "type": typ, "text": text, "args": args, "slots": list(slots),
                           "parts": list(parts)})

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


MINIMUM_TYPES = ("pilot_engagement", "boss_od", "lip_engagement")


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
            if a.get("subject"):              # a reference-only check (plug_refs_*): a plan volume, no body
                subject = vols[a["subject"]]
            else:
                subject = union([bodies[k] for k in a["bodies"]]) if a.get("bodies") else all_bodies
            out.append(_with_volume_parts(plan, a, clear_of(
                subject, vols[a["volume"]], a["clearance"], plan.tol, vols[a["minus"]] if a.get("minus") else None,
                cid, a["volume"], parts=plan.parts.get(a["volume"]), labels=plan.labels)))
            if a.get("subject"):
                out[-1].evidence["subject"] = a["subject"]
        elif typ == "inside":
            out.append(_with_volume_parts(plan, a, inside(
                vols[a["volume"]], list(bodies.values()), a["clearance"], plan.tol,
                vols[a["minus"]] if a.get("minus") else None, cid, a["volume"],
                parts=plan.parts.get(a["volume"]), labels=plan.labels)))
        elif typ == "aperture_count":
            out.append(aperture_count(all_bodies, vols[a["slab"]], a["n"], plan.tol, cid, a["wall"],
                                      a.get("normal_axis"), {c: vols[c] for c in a.get("cuts", [])}))
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
        elif typ in ("port_below_split", "pilot_depth", "screw_through_hole"):
            out.append(value_at_most(cid, typ, a["value"], a["limit"], plan.tol, a["detail"]))
        elif typ in MINIMUM_TYPES:
            out.append(value_at_least(cid, typ, a["value"], a["limit"], plan.tol, a["detail"]))
        elif typ == "pilot_band":
            out.append(value_in_band(cid, typ, a["value"], a["lo"], a["hi"], plan.tol, a["detail"]))
        elif typ == "grid_conformance":
            out.append(grid_conformance(cid, a["value"], a["limit"], a["no_pin_data"], plan.tol, a["evidence"]))
        elif typ == "coverage":
            out.append(text_coverage(cid, a["uncovered"], a["covered"], a["evidence"]))
        elif typ == "ligament":
            out.append(ligament(bodies[a["body"]], vols[a["cut"]], a["axis"], a["plane"], a["min"], plan.tol, cid,
                                a.get("floor_z"), {c: vols[c] for c in a.get("neighbours", [])}, a["cut"]))
        else:
            raise ValueError(f"unknown check type {typ!r}")
    return out


def _with_volume_parts(plan: Plan, args: Mapping[str, Any], result: cc.CheckResult) -> cc.CheckResult:
    """Which solids the d is about (node id -> catalogue id) and what was exempted, without reading code."""
    ev = result.evidence
    ev["volume_parts"] = {i: plan.labels.get(i, i) for i in plan.sources.get(args["volume"], [])}
    if args.get("minus"):
        ev["minus"] = {"volume": args["minus"], "sources": list(plan.sources.get(args["minus"], [])),
                       "grown_by": args.get("minus_grown_by", 0.0)}
    return result


def reference_table(plan: Plan, results: Sequence[cc.CheckResult]) -> Dict[str, dict]:
    """self_report.json "references": per reference node, its catalogue id and its smallest reported body clear_of /
    inside d (from the per-source figures of composite volumes, or the headline d of a single-part volume). A d that is
    only the search radius (nothing found within it) carries d_capped and prints as '≥ x' in d_text (iteration 011 C3)."""
    out: Dict[str, dict] = {nid: {"part": part, "d": None, "check": None} for nid, part in plan.references.items()}
    for r in results:
        if r.type not in ("clear_of", "inside") or r.evidence.get("subject"):   # reference-to-reference checks
            continue
        ev = r.evidence
        per = ev.get("per_source") or {}
        members = ev.get("volume_parts") or {}
        for nid in out:
            if nid in per:
                row = per[nid]
            elif list(members) == [nid]:
                row = ev
            else:
                continue
            d = row.get("d")
            if d is not None and (out[nid]["d"] is None or d < out[nid]["d"]):
                out[nid].update(d=d, check=r.check_id)
                if row.get("d_capped"):
                    out[nid].update(d_capped=True, d_text=_bound(d, True))
                else:
                    out[nid].pop("d_capped", None)
                    out[nid].pop("d_text", None)
    return out


def aperture_table(results: Sequence[cc.CheckResult]) -> Dict[str, dict]:
    """self_report.json "apertures": per wall, the through-opening count and the blind regions with the cut nodes
    they meet (ARCHITECTURE.md 7.9), so a reader applying rubric 3.4 literally sees the agent's classification."""
    out = {}
    for r in results:
        ev = r.evidence
        if r.type == "aperture_count" and "through" in ev:
            wall = r.check_id.split("_", 1)[1] if "_" in r.check_id else r.check_id
            out[wall] = {"through": ev["through"], "blind": list(ev["blind"]), "total": ev["total"]}
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
        "references": reference_table(plan, results),
        "apertures": aperture_table(results),
        "results": [r.to_dict() for r in results],
    }


def write_json(path: Path, data: Any) -> Path:
    path.write_text(json.dumps(_jsonable(data), indent=2, default=str))
    return path
