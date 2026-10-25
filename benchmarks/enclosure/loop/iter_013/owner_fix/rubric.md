# Enclosure judge rubric: does the rendered design meet the requirements?

This is the error signal of the enclosure control loop. A judge (a capable model, never the local
model under test) gets one design package and decides **MEETS** or **DOES NOT MEET** against
`requirements.md`. When it does not, the judge says **where**, precisely enough that a separate
agent can find the gap and make a delta design without seeing the judge's reasoning.

The same rubric grades E1-01 (`enclosure.json`), the variants (`variants.json`, with each
variant's `grading_deltas` applied to the requirements tree) and, for the A/B, Robin's own
design (`requirements.md` section 7).

---

## 1. Inputs

| Input | Where | Used for |
|---|---|---|
| `base.stl`, `lid.stl` | the design package (closed assembly pose, mm) | **every measurement** |
| `.scad` source | package | naming features; finding where a defect comes from; never for measuring |
| renders | package `views/*.png` (`iso`, `front`, `back`, `left`, `right`, `top`, plus highlight renders per part) | locating and illustrating defects; a render can show a failure but can never make a check pass |
| measured part table | package (the agent's list of parts with sizes and positions) | naming features and cross-checking; re-measure every number you rely on |
| `layout.json` | package | the declared board layout and print orientations (L2.1.1, seating rule) |
| self-report | package (the agent's own `clear_of` / `inside` results) | L3.12.2.1 only; never trusted for any other L3 |
| `requirements.md`, `parts/*/part.json` | this folder | criteria, reference models, envelopes |

The judge does **not** use: the agent's code or transcript, earlier iterations' verdicts (blind
per package), `benchmarks/heldout.json`, or anything about Robin's private design.

## 2. Procedure

1. **Package gate (G0).** Check that the files in L2.12.1 exist and load. If the STLs are missing or
   unreadable, stop: verdict DOES NOT MEET, one defect on L3.12.1.1.
2. **Load and check units.** Load each STL (section 3.1). Each body's largest bounding-box axis must be 20–200 mm (a thin lid axis is expected, L2.7.5);
   if it looks like inches or metres, record a defect, do not rescale silently.
3. **Normalise the frame.** Put the closed assembly in the enclosure frame (requirements 1.1): floor
   underside at Z = 0, the end wall that has the USB opening at −X. Use rotations by multiples of
   90° and mirroring only; record the transform. All coordinates in the report are in this
   frame, and in the board frame where a board-relative number is clearer.
4. **Build the references independently.** Build the RBA from `parts/*/part.json` at the pose in
   `layout.json` (or the default layout, A2, if there is none), then every V- envelope of
   requirements 2.3. Run sanity checks R1–R8. Then verify the seating rule (2.4).
5. **Run every applicable L3** with Python (section 3), in requirement order. Record for each: the
   measured value, the limit, the margin (measured − limit, signed so that negative = fail), and
   PASS / FAIL / UNVERIFIED / N/A. **UNVERIFIED counts as FAIL** (a check you could not run is not
   a pass). N/A only for the closure variant the design does not use, the physical tests
   (unless a print was made), and the cases in requirements section 7.
6. **Look at the renders** after measuring. Use them to (a) confirm each failure is where the numbers
   say and pick the render that shows it best, and (b) catch defects no L3 covers (a floating
   fragment, a wall on the wrong side, a lid upside down). Report (b) as **observations** with a
   location; they do not change the verdict unless they make an L3 fail on re-measurement.
7. **Decide** (section 4) and **report** (section 5).

## 3. Measurement recipes

Use `/Users/robinonsay/python/llm-bt/venv/bin/python` with `manifold3d` (3.5.x) and `trimesh`
(5.1). trimesh's graph engine is not installed, so count shells with manifold3d's `decompose()`,
not `trimesh.split()`. These recipes were tried on a test shell; they are the reference
implementation of the two checks.

### 3.1 Load

```python
import numpy as np, trimesh, manifold3d as m3d
M = m3d.Manifold

def load(path):
    tm = trimesh.load(path, force="mesh")
    man = M(m3d.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                     tri_verts=np.asarray(tm.faces, np.uint32)))
    return tm, man          # man.status() must be NoError (else L3.9.2.1 fails)

shells = len(man.decompose())   # L3.9.2.1, L3.7.1.1, L3.3.4.2: must be 1
```

### 3.2 `clear_of(bodies, volume, clearance)`

```python
def clear_of(bodies, vol, c):
    pen = (bodies ^ vol).volume()            # ^ = intersection
    if pen > 0.01:
        return {"d": None, "penetration_mm3": pen, "where": (bodies ^ vol).bounding_box()}
    return {"d": bodies.min_gap(vol, c + 5.0), "penetration_mm3": 0.0}
# PASS: penetration <= 0.01 and d >= c - 0.02.  min_gap returns the search length when farther.
```

When it fails, save the intersection (or, for a near miss, the two closest regions) as
`defect_<L3>.stl` and report its bounding box. For a near miss, find the location with
`bodies ^ minkowski_sum(vol, sphere(c))` or by sampling the volume's surface and taking the
closest points on the body (`trimesh.proximity.closest_point`).

### 3.3 `inside(volume, cavity, clearance)`

```python
def inside(vol, solids, c, big=2000):
    hull = M.hull(solids)                     # closed base + lid
    out = (vol - hull).volume()
    if out > 0.01:
        return {"d": None, "outside_mm3": out, "where": (vol - hull).bounding_box()}
    shell = M.cube([big] * 3, True) - hull    # everything outside the enclosure
    d = min(vol.min_gap(solids, c + 5.0), vol.min_gap(shell, c + 5.0))
    return {"d": d}                           # PASS: d >= c - 0.02
```

Note that `inside` also fails when a volume overlaps a solid: then `min_gap` is 0.

### 3.4 Apertures (V-AP-USB, V-AP-AUX, V-AP-OTHER)

- End-wall slab: find the wall's inner and outer faces (largest faces with normal ±X, from the
  mesh's facets or by ray casting along X at many (Y, Z) points). Slab = box between them over
  the wall's full Y and Z extent. Aperture = slab − (BASE ∪ LID, closed). Count regions with
  `decompose()`; ignore regions under 1 mm³.
- Opening size and centre: slice the aperture at mid-wall (`Manifold.slice(z)` after rotating X to
  Z, or `trimesh.section`) and report the polygon's bounding box, centroid and the largest
  inscribed circle (holes) in enclosure coordinates.
- Unlisted openings (L3.8.1.1): shoot rays from outside toward V-CAVITY on a 1 mm grid over every
  face of the hull and keep the rays that reach the cavity without hitting a solid; cluster them,
  then confirm a Ø2.0 sphere passes by intersecting a Ø2.0 sweep along the ray with the solids.
  Every cluster not in a listed opening or a screw hole is a defect.

### 3.5 Distances, thicknesses, holes

- **Gap between faces** (L3.2.2.2, L3.7.2.1, L3.7.4.1): `min_gap` between the two named regions,
  or ray casting from one face along its normal (report min, median and max over a 1 mm grid).
- **Wall / floor / lid thickness** (L3.8.2.x): ray cast through the wall along its normal on a
  2 mm grid, keep rays at least 3 mm from any edge, opening or boss; report the median and the
  range. The median is the measured value; a range wider than 0.5 mm is noted.
- **Hole diameter** (pilots, lid holes): slice at mid-depth; the largest inscribed circle of the
  hole polygon. **Depth**: ray cast down the hole axis.
- **Standoff / boss OD and axis**: slice at mid-height; smallest enclosing circle; axis = circle
  centre. **Pitch** = distances between axes.
- **Bounding boxes**: `manifold.bounding_box()` per body and for the closed union.

### 3.6 Printability

- **Overhang** (L3.9.1.1): rotate each body into its print orientation; a face with unit normal n
  overhangs if n_z < −cos(45°) and it is not on the bed (z > 0.05). Exempt the downward faces of
  round holes Ø ≤ 12 in vertical walls and bridges (a downward face whose both ends rest on
  material at most 15 mm apart). Report offending faces grouped by connected patch, with
  area and bounding box.
- **Bed contact** (L3.9.3.1): area of faces with n_z < −0.999 at z < 0.05 ÷ plan bounding box area.
- **Thin features** (L3.9.4.1): ray cast inward along each face's normal from sampled points; any
  local thickness < 0.8 mm (excluding edges) is a defect.

### 3.7 Stability

L3.10.2.1: centre of mass of the closed assembly plus the RBA (40 g total unless measured)
projected onto the table must stay inside the support polygon at 5° tilt in every direction.
L3.10.3.1: at each port centre, 0.5 N horizontal outward times port height vs weight times the
distance from the centre of mass to the tipping edge; margin = restoring − tipping.

## 4. Verdict

Gates (requirements section 5): G0 package, G1 manifold and two bodies, G2 board fit, G3 USB plug
seats, G4 both jack plugs seat, G5 board fixed.

| Class | Rule |
|---|---|
| **WRONG** | any gate fails |
| **MINOR** | no gate fails, but some weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |

**MEETS requirements** (the loop's zero-error state) = CORRECT **and** every applicable
non-physical L3 of weight 1 and 2 passes. Anything else is **DOES NOT MEET**.

Also report the weighted score Σ(weight × pass) / Σ(weight) over applicable L3s and the worst
normalised margin among weight-3 L3s (margin ÷ the criterion's tolerance or, for one-sided
limits, ÷ 0.5 mm), so the loop can tell progress inside DOES NOT MEET.

Precedence rules:
- The plug-seating and clearance checks (L3.5.1.1, L3.6.1.1) outrank everything about opening
  size; a smaller opening that lets the plug seat is fine as long as L3.5.2.1 / L3.6.2.1 pass.
- If a design meets an L2's intent another way that `requirements.md` lists as an alternative
  grade it on that alternative's numbers and say so. Robin fixed the following on 2026-10-24, and
  no alternatives are accepted for them: the lid form (L2.7.5: a flat plate with a lip and 4 × M3
  screws), the jack (PJ-320A), the board grid and holes (A7), and M2 board screws (A9). Any
  unlisted alternative is graded on the default numbers; note it as an observation for Robin.
- **Designed contact is not interference** (requirements 1.3). The board resting on the standoff
  tops, a screw in its pilot, the lid lip on its locating faces and the lid on the rim never count
  as interference. Only penetration above 0.01 mm³ counts.
- **The reference numbers in requirements.md section 2.2 (board grid, holes, default poses) are
  authoritative.** If `parts/*/part.json` disagrees with them, build the references from
  requirements.md, and record a defect on the requirement the stale catalogue data breaks (for
  example L3.1.6.1 or L3.3.1.3), with where = the part.json field.
- Never relax a criterion, never round in the design's favour beyond ε (requirements 1.2), never
  infer a pass from a render.

## 5. How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them, not just the first), most severe first
(gates, then weight 3, 2, 1). Each entry must let someone who has only the package and this entry
find the problem in under a minute.

| Field | What to write | Example |
|---|---|---|
| `req` | the L3 id, with its L2 and L1 | `L3.5.1.1 (L2.5.1, L1.5)` |
| `status` | FAIL or UNVERIFIED | `FAIL` |
| `body` | `base`, `lid`, `both`, or `layout` | `base` |
| `feature` | the feature, named by function and, if it exists, by its SCAD/part-table name | "USB opening in the −X end wall (`usb_cutout`)" |
| `face` | which surface: wall + side (inner/outer) + edge, with its outward normal | "top edge of the opening, normal −Z, on the wall's outer face" |
| `location` | coordinates in mm, enclosure frame, and board frame if useful: a point, or a bounding box `[xmin, ymin, zmin]–[xmax, ymax, zmax]` | "intersection box [−4.0, 20.1, 7.9]–[−2.0, 29.9, 8.4] (board frame Z +7.9 to +8.4)" |
| `measured` / `limit` / `margin` | numbers with units | "d = −0.5 mm (penetration 9.8 mm³) / ≥ 0.30 mm / −0.80 mm" |
| `reference` | the reference model or envelope involved and its datum | "V-USB-PLUG overmold, about `USB_MOUTH` (3.12, 25.0, 4.9) board frame" |
| `render` | the render that shows it and where in the image | "`left.png`, upper edge of the rectangular opening, centre of image" |
| `evidence` | saved files | "`defect_L3.5.1.1.stl` (the intersection solid)" |
| `needed` | the geometric change that would make this check pass, as numbers, not as a design instruction | "opening top edge must be at board-frame Z ≥ +8.7 (now +7.9)" |

Rules for the entries:
- Coordinates come from the measurement, not from the SCAD source or the part table.
- `needed` states a target the next agent can verify (a position, size or clearance), never "use a
  difference()" or "move the lid". The next agent decides how.
- Group several L3s that fail for one geometric reason under the first one and list the others
  in `also_fails`, but keep every L3 id in the report.
- Separate **observations** (render-only findings, section 2 step 6) from defects.

Report format: a short markdown summary (verdict, class, score, worst margin, gate table, the
measured-values table from section 6 of this file) followed by the defects as a JSON list with
the fields above, saved as `judge.md` and `defects.json` in the iteration folder.

## 6. Measured-values table (always filled in, pass or fail)

| Quantity | Limit (E1-01 defaults) | Measured |
|---|---|---|
| Board clearance to any surface (L3.2.1.1), mm | ≥ 0.5 | |
| Pico in cavity / headers and jacks in cavity (L3.2.2.1, L3.4.3.1), mm | ≥ 0.2 / ≥ 0.3 | |
| Standoff count, pitch X / Y, axis offset (L3.3.1.x), mm | 4; 66.0 / 46.0 ± 0.25; ≤ 0.25 | |
| Standoff OD, pilot Ø, pilot depth (L3.3.2.1, L3.3.3.x), mm | 5.0–7.0; 2.0–2.2; ≥ 5.0 | |
| Top / bottom keep-out d (L3.4.1.1, L3.4.2.1), mm | ≥ 0 / ≥ 0 | |
| USB plug d; USB opening oversize d (L3.5.1.1, L3.5.2.1), mm | ≥ 0.3; ≥ 0 | |
| USB opening W × H and centre (board frame), mm | (≤ 13 × 10 with defaults) | |
| Jack plug d (each); jack opening oversize d (L3.6.1.1, L3.6.2.1), mm | ≥ 0.3; ≥ 0 | |
| Jack opening Ø and centre (each, board frame), mm | (≤ 11 with defaults) | |
| Opening counts −X / +X / other (L3.5.3.1, L3.6.3.1, L3.8.1.1) | 1 / 2 / 0 | |
| Lid lip clearance per side; engagement (L3.7.2.x), mm | 0.15–0.35; ≥ 2.0 | |
| Wall / floor / lid thickness, median and range (L3.8.2.x), mm | 2.0–4.0 | |
| Overhang patches; bed contact per body (L3.9.1.1, L3.9.3.1) | 0; ≥ 50% | |
| Shells base / lid (L3.9.2.1) | 1 / 1 | |
| Closed envelope X × Y × Z (L3.10.1.1), mm | ≤ 90 × 70 × 35 | |
| Install sweep d; driver columns d (L3.11.x), mm | ≥ 0.2; ≥ 0 | |
| Self-report agreement (L3.12.2.1) | 100% within 0.10 mm | |

## 7. Convergence and over-fitting (for the loop)

- The loop has converged when the agent's E1-01 package **MEETS** on 3 runs with different seeds
  and each variant in `variants.json` is at least **CORRECT** on 1 run. One lucky run is not
  convergence; a variant that is WRONG means the agent over-fitted E1-01.
- A judge sees one package at a time. Do not compare against earlier iterations inside the
  verdict; the loop's ledger does that.
- If the judge finds a requirement that seems wrong (impossible, or contradicting another),
  report it as an observation addressed to Robin with the numbers; keep grading it as written.
