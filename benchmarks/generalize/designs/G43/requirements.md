# G43 40 to 50 mm PVC reducer with stop: requirements (L1 / L2 / L3)

A generalization design (train split) in the style of E1-01 (`benchmarks/enclosure/requirements.md`).
The machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file.
The generic grading rubric (`benchmarks/generalize/rubric.md`) did not exist when this file was
written, so section 9 holds the design-specific grading rules; measuring recipes are those of
`benchmarks/enclosure/rubric.md` section 3 (load, `clear_of`, `inside`, slices, ray casting, overhang scan).

**Owner's request (verbatim):** "A reducer that slides over a 40 mm pipe on one side and into a
50 mm pipe's inside on the other, with a shoulder stop at 15 mm depth on each. Wall thickness
2.4 mm, friction fit with 0.15 mm interference allowance. Printed vertically."

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete Python check on the delivered STL. Every row has a
method (inspection, analysis, demonstration, test, human), a pass/fail criterion with a number and
tolerance, a weight (3 = critical, 2 = major, 1 = minor) and a gate mark (G0 to G5) where a failure
makes the design WRONG. Every number that comes from an assumption (section 3) is provisional until
the owner confirms it. Do not relax a criterion because the agent fails it.

---

## 1. Frame, tolerances and designed contact

- **Frame:** the reducer's axis is Z. The 40 mm socket mouth is the plane Z = 0 and the 50 mm
  spigot is toward +Z. A design delivered with the axis along another direction, or flipped, is
  normalised by rotation by multiples of 90 degrees (rubric step: the end with the smaller outside
  diameter goes to Z = 0); the build direction it declares (L3.9.1.1) is transformed the same way.
  That is never penalised. Units are mm.
- **Measurement tolerances ε:** length and distance 0.02; diameter 0.03 (least-squares circle on a
  slice of at least 90 degrees per ring); angle 0.5 degrees; volume 0.01 mm³. A value passes if it
  meets its limit to within ε. "nominal ± t" means t plus ε.
- **Slices:** diameters, wall thicknesses and axes are measured on horizontal slices (Manifold
  `slice(z)`), at 5 stations spread evenly over the stated Z range; the reported value is the median,
  the range is noted.
- **Designed contact (this design).** The following are never interference:
  1. the pipe's end face resting on its stop face (distance 0 allowed; penetration deeper than
     0.05 mm counts);
  2. the friction fit itself: the 40.0 pipe's outside surface against the socket bore, and the
     spigot's outside surface against the 50.0 pipe's bore. Radial overlap up to 0.10 mm is the
     designed fit (L3.6.3.1); more counts as interference.
  Everything else (a pipe wall entering the shoulder, the two pipes touching each other, a pipe
  hitting the transition cones) is interference.
- **Checks used** (`enclosure/requirements.md` section 1.3, recipes in `enclosure/rubric.md` 3.2 and 3.3):
  `clear_of(bodies, volume, clearance)` (pass: penetration ≤ 0.01 mm³ and d ≥ clearance − ε) and
  `inside`. The grader builds all reference models and volumes itself from the catalogue and
  the delivered stop positions; a design never builds or edits them for grading.

## 2. Reference models and envelopes

All reference models come from `benchmarks/generalize/parts/generic_tube/part.json`
(outer diameter, inner diameter, length from the request; axis Z, origin at the centre of the
start end face, extending toward +Z; the bore is a datum).

| Name | What | Source | Definition (reducer frame, mm) | Datums |
|---|---|---|---|---|
| **S40** | stop face of the 40 side | measured on the STL | the annular face with normal −Z (facing the socket mouth) nearest the middle of the part; its plane Z = `Z_S40`, outer radius = bore radius, inner radius = measured | `S40_PLANE`, `S40_RINGS` |
| **S50** | stop face of the 50 side | measured on the STL | the annular face with normal +Z (facing the spigot end); plane Z = `Z_S50`, inner radius = spigot radius, outer radius = measured | `S50_PLANE`, `S50_RINGS` |
| **M-PIPE-40** | the 40 mm pipe | catalogue `generic_tube` | OD 40.0, ID 36.0 (A4), length 60.0, seated: Z from `Z_S40` − 60.0 to `Z_S40`, concentric with the fitted reducer axis | `PIPE40_END` (plane Z = `Z_S40`), `PIPE40_AXIS` |
| **M-PIPE-50** | the 50 mm pipe | catalogue `generic_tube` | OD 56.0, ID 50.0 (A4), length 60.0, seated: Z from `Z_S50` to `Z_S50` + 60.0, concentric | `PIPE50_END` (plane Z = `Z_S50`), `PIPE50_AXIS` |
| **V-BORE** | flow envelope | envelope | cylinder Ø34.0 (A5) on the reducer axis, over the full Z extent of the body | axis |
| **V-IN-40** | entry path of the 40 pipe | envelope | M-PIPE-40 with OD reduced to 39.40 (0.30 per side under the bore), swept along +Z from 40.0 below the mouth to seated | `PIPE40_AXIS` |
| **V-IN-50** | entry path of the 50 pipe | envelope | M-PIPE-50 with ID enlarged to 50.30 and OD kept 56.0, swept along −Z from 40.0 above the spigot end to seated | `PIPE50_AXIS` |

Sanity checks before grading (not L3s): R1 units, the reducer's largest bounding-box axis is
20 to 60 (a unit error otherwise); R2 the axis fit has residual ≤ 0.05; R3 the part has a socket
end with bore < 41 and a spigot end with OD > 49; R4 M-PIPE-40 and M-PIPE-50 do not touch each
other in the seated pose (their end planes differ by `Z_S50` − `Z_S40` ≥ 1.0, L3.11.1.1).

## 3. Assumptions and open questions for the owner

| # | Question | Value chosen | Why / uncertainty |
|---|---|---|---|
| **A1** | What is "40 mm"? | The **outside diameter** of the small pipe, 40.0. | The reducer slides *over* it. Uncertainty low. Nominal 40 mm PVC pressure pipe has OD 40.0. |
| **A2** | What is "50 mm"? | The **inside diameter** of the large pipe, 50.0. | The reducer slides *into the inside* of it. Uncertainty **high**: nominal 50 mm PVC pipe has an OD of 50.0 and an ID of about 44 to 46; the owner's words only fit an ID of 50 (a 55 or 56 mm OD pipe). If the owner means OD 50, the spigot must be about 44 and the numbers change. Confirm. |
| **A3** | Is the 0.15 mm interference on diameter or radius? | **Diametral**: bore = 40.0 − 0.15 = 39.85 and spigot OD = 50.0 + 0.15 = 50.15 nominal. | "Interference allowance" in printing is usually quoted on diameter. Radial would be 0.30 diametral, which is too tight for a hand push. Uncertainty medium. |
| **A4** | Reference pipe walls | M-PIPE-40: ID 36.0 (wall 2.0). M-PIPE-50: wall 3.0 (OD 56.0). | Only used to size the stop width and to build reference solids. The stops need width ≥ 1.0 to register a pipe end. Uncertainty medium; a wall different by ±1.0 does not change any criterion. |
| **A5** | Minimum through-bore | Ø34.0. | The 40 pipe's assumed ID is 36.0, so the reducer may not choke the flow by more than 2.0 mm of diameter. Uncertainty medium. |
| **A6** | Pipe tolerances | Pipe OD 40.0 ± 0.10, pipe ID 50.0 ± 0.10. | Typical PVC pipe tolerance order. Uncertainty medium: measure the owner's pipes. |
| **A7** | Print tolerance | A printed diameter lands within ± 0.05 of the model (after the usual hole compensation). | Typical FDM at 0.4 nozzle, 0.2 layers. Uncertainty medium. |
| A8 | Printer, material, orientation | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed, **axis vertical**, no supports. Horizontal ledges up to 1.5 mm wide (a stop) are bridged by the extrusion (exempt from the overhang rule). | Common printer. The owner said "printed vertically". |
| A9 | Flow medium, pressure | None. The part only locates and friction-holds two pipes. No seal is required. | The request does not mention a seal or pressure. |
| A10 | Length of pipes beyond the reducer | At least 60 mm each, used for the reference solids. | Needed so the insertion sweeps are long enough. |

## 4. Fixed decisions (a choice was ambiguous; this is the one graded)

- **FD1 Orientation of the print.** The graded print orientation is the one the design declares in
  `layout.json`, provided its build direction is the reducer axis (L3.9.1.1). Either end may be
  down. The overhang rule (L3.9.3.1) is applied to the declared direction.
- **FD2 Stops.** The 40 side stop is an internal shoulder (the bore steps inward); the 50 side stop is
  an external flange (the outside steps outward). A pipe end bottoms out on each.
- **FD3 Wall.** "Wall thickness 2.4" applies to the socket and the spigot walls (cylindrical
  regions). The shoulders and transition are exempt from the 2.4 value but not from the 2.0
  minimum (L3.5.2.1).
- **FD4 Frame of numbers.** The socket depth is measured from the mouth plane (Z = 0 at the end
  face, ignoring the lead-in) to `Z_S40`; the spigot length is from `Z_S50` to the spigot's end face.

## 5. Requirements tree

### L1.1 One manifold body with no enclosed voids

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The reducer is one connected, watertight body. | analysis | shells = 1 (Manifold `decompose()`), manifold3d status NoError | 3 | G1 |
| L3.1.1.1 | Shell count and manifold status. | analysis | shells = 1; NoError | 3 | G1 |
| L3.1.1.2 | No enclosed void. | analysis | the mesh has no inward-facing closed shell (a sealed cavity); count = 0 | 1 | |

### L1.2 The 40 mm end is a socket, bore 39.80 to 39.87 mm, 15.0 mm deep

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Bore diameter is 0.15 smaller than the pipe (A3, A6, A7). | inspection | bore Ø ∈ [39.80, 39.87] (nominal 39.85), median of 5 slices at Z 3 to 12 | 3 | G3 |
| L3.2.1.1 | Socket bore diameter. | inspection | as L2.2.1 | 3 | G3 |
| L3.2.1.2 | Out-of-round and taper of the bore. | inspection | per slice max diameter − min ≤ 0.05; median Ø at Z 3 minus at Z 12 ≤ 0.05 | 1 | |
| L2.2.2 | Socket depth. | inspection | mouth plane to `Z_S40` = 15.0 ± 0.2 | 3 | |
| L3.2.2.1 | Socket depth. | inspection | 14.8 ≤ `Z_S40` ≤ 15.2 | 3 | |
| L2.2.3 | A lead-in at the mouth helps the pipe start. | inspection | chamfer or radius, radial size 0.3 to 1.0, axial size 0.3 to 1.0 | 1 | |
| L3.2.3.1 | Mouth lead-in size. | inspection | radial 0.3 to 1.0 and axial 0.3 to 1.0 (from the bore profile in a vertical section) | 1 | |

### L1.3 The 50 mm end is a spigot, outside diameter 50.13 to 50.20 mm, 15.0 mm long

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Spigot outside diameter is 0.15 larger than the pipe's inside (A3, A6, A7). | inspection | OD ∈ [50.13, 50.20] (nominal 50.15), median of 5 slices over the spigot, 3 mm in from both ends | 3 | G4 |
| L3.3.1.1 | Spigot OD. | inspection | as L2.3.1 | 3 | G4 |
| L3.3.1.2 | Out-of-round and taper of the spigot. | inspection | per slice max − min ≤ 0.05; OD at the first and last station differ ≤ 0.05 | 1 | |
| L2.3.2 | Spigot length. | inspection | `Z_S50` to the spigot end face = 15.0 ± 0.2 | 3 | |
| L3.3.2.1 | Spigot length. | inspection | 14.8 ≤ length ≤ 15.2 | 3 | |
| L2.3.3 | A lead-in at the spigot end. | inspection | chamfer radial 0.3 to 1.0, axial 0.3 to 1.0 | 1 | |
| L3.3.3.1 | Spigot lead-in size. | inspection | as L2.3.3 | 1 | |

### L1.4 Each end has a flat shoulder stop at 15.0 mm depth on which the pipe seats

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | S40 is a flat full ring, square to the axis, wide enough to register a pipe end. | inspection | normal within 1.0° of −Z; planarity (max − min Z over the face) ≤ 0.10; the ring is complete over 360°; radial width ≥ 1.0 | 3 | |
| L3.4.1.1 | S40 flatness, squareness, completeness. | inspection | as L2.4.1 | 3 | |
| L3.4.1.2 | S40 radial width and inner diameter. | inspection | width = bore radius − S40 inner radius ≥ 1.0; S40 inner Ø ≥ 34.0 | 2 | |
| L2.4.2 | S50 is a flat full ring, square to the axis, wide enough. | inspection | normal within 1.0° of +Z; planarity ≤ 0.10; complete over 360°; radial width (S50 outer radius − spigot radius) ≥ 1.0 | 3 | |
| L3.4.2.1 | S50 flatness, squareness, completeness. | inspection | as L2.4.2 | 3 | |
| L3.4.2.2 | S50 radial width. | inspection | ≥ 1.0 | 2 | |
| L2.4.3 | Each seated pipe lands on its stop. | demonstration | with M-PIPE-40 and M-PIPE-50 placed so that their end faces lie on `Z_S40` and `Z_S50`: end-face contact area with the stop ≥ 60 mm², and the penetration of the pipe end into the stop ≤ 0.05 | 3 | G5 |
| L3.4.3.1 | M-PIPE-40 on S40. | demonstration | contact annulus area ≥ 60 mm² (sketch: 122 mm²); penetration depth ≤ 0.05 | 3 | G5 |
| L3.4.3.2 | M-PIPE-50 on S50. | demonstration | contact annulus area ≥ 60 mm² (sketch: 161 mm²); penetration depth ≤ 0.05 | 3 | G5 |

### L1.5 The socket and spigot walls are 2.4 mm thick; nothing is thinner than 2.0 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Socket wall and spigot wall (FD3). | inspection | each = (OD − bore) / 2 from slices: 2.4 ± 0.1 (socket: Z 3 to 12; spigot: 3 mm in from both ends) | 3 | |
| L3.5.1.1 | Socket wall. | inspection | 2.30 ≤ t ≤ 2.50 | 3 | |
| L3.5.1.2 | Spigot wall. | inspection | 2.30 ≤ t ≤ 2.50 | 3 | |
| L2.5.2 | No thin wall in the transition. | analysis | local thickness anywhere (ray cast inward along each face normal from samples, edges excluded) ≥ 2.0 | 2 | |
| L3.5.2.1 | Minimum local thickness. | analysis | ≥ 2.0 | 2 | |

### L1.6 Both joints are friction fits with interference between 0 and 0.35 mm over tolerances

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Stack on the 40 side. | analysis | I40 = 40.0 − measured bore Ø; worst case over pipe ±0.10 (A6) and print ±0.05 (A7) is [I40 − 0.15, I40 + 0.15]; require min ≥ −0.02 and max ≤ 0.35, i.e. 0.13 ≤ I40 ≤ 0.20 | 3 | |
| L3.6.1.1 | 40 side interference window. | analysis | 0.13 ≤ I40 ≤ 0.20 | 3 | G3 |
| L2.6.2 | Stack on the 50 side. | analysis | I50 = measured spigot OD − 50.0; same stack: 0.13 ≤ I50 ≤ 0.20 | 3 | |
| L3.6.2.1 | 50 side interference window. | analysis | 0.13 ≤ I50 ≤ 0.20 | 3 | G4 |
| L2.6.3 | Seated overlap is the designed fit only. | analysis | with both pipes seated, penetration of M-PIPE-40 ∪ M-PIPE-50 into the body occurs only as a thin radial layer along the bore and spigot surface | 3 | |
| L3.6.3.1 | Overlap depth. | analysis | maximum radial overlap depth ≤ 0.10 (+ ε) along the fit surfaces; no penetration elsewhere (> 0.01 mm³ outside the fit zones fails) | 3 | |
| L3.6.3.2 | Fit engagement length. | analysis | the fit surface (radial overlap > 0) covers ≥ 80% of 15.0 mm on each side, from the lead-in to the stop | 1 | |

### L1.7 Coaxial and square

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Socket bore, spigot outside and through-bore share an axis. | inspection | circle centres of the socket bore, spigot OD and the narrowest through-bore, at 5 stations each, all within 0.10 of the least-squares axis | 2 | |
| L3.7.1.1 | Coaxiality. | inspection | max offset ≤ 0.10 | 2 | |
| L2.7.2 | Stops are square to the axis. | inspection | both stop normals within 0.5° of the axis | 1 | |
| L3.7.2.1 | Stop squareness. | inspection | ≤ 0.5° (measurement ε 0.5° added) | 1 | |

### L1.8 The through-bore is open and at least 34.0 mm everywhere

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | A Ø34.0 cylinder passes end to end. | analysis | clear_of(BODY, V-BORE, 0.0): d ≥ 0, penetration ≤ 0.01 mm³ | 3 | G2 |
| L3.8.1.1 | V-BORE clear. | analysis | passes | 3 | G2 |
| L3.8.1.2 | Narrowest bore diameter on 40 slices over the full length. | analysis | ≥ 34.0 | 2 | |

### L1.9 It prints standing on its axis without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The declared build direction is the axis. | inspection | `layout.json` build direction within 1.0° of ±Z (reducer frame) | 3 | |
| L3.9.1.1 | Build direction declared and vertical. | inspection | angle ≤ 1.0° | 3 | |
| L2.9.2 | The lowest end face is a flat full annulus. | analysis | in the declared orientation, bed contact (area of faces with n_z < −0.999 at z < 0.05) ≥ 50% of the annulus area (π/4)(OD² − bore²) of that end (a permitted lead-in of 0.3 to 1.0 leaves 57% or more; the sketch has 80%) | 2 | |
| L3.9.2.1 | Bed contact. | analysis | ≥ 50% (sketch: 80%) | 2 | |
| L2.9.3 | No unsupported overhang. | analysis | faces with n_z < −cos 45° (patch area > 1 mm²) = 0, except a horizontal ledge no wider than 1.5 mm radially (A8); angle tolerance 0.5° (ε of section 1); every transition between diameters is a cone at 45° or steeper from vertical | 3 | |
| L3.9.3.1 | Overhang scan. | analysis | 0 offending patches | 3 | |
| L2.9.4 | No thin feature. | analysis | local thickness ≥ 0.8 everywhere (L3.5.2.1 is stricter and applies) | 1 | |
| L3.9.4.1 | Thin feature scan. | analysis | ≥ 0.8 | 1 | |

### L1.10 It is compact

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Size limit. | inspection | across (X, Y in the reducer frame) ≤ 56.0 each; length (Z) ≥ 30.0 and ≤ 45.0 | 1 | |
| L3.10.1.1 | Bounding box. | inspection | as L2.10.1 | 1 | |

### L1.11 The pipes seat, do not touch each other, and enter freely

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | The two pipe ends are apart. | test | `Z_S50` − `Z_S40` ≥ 1.0 | 2 | |
| L3.11.1.1 | Pipe end gap. | test | ≥ 1.0 | 2 | |
| L2.11.2 | The 40 pipe enters the socket freely until the lead-in. | test | clear_of(BODY, V-IN-40, 0.0) | 2 | |
| L3.11.2.1 | V-IN-40 clear. | test | passes | 2 | |
| L2.11.3 | The spigot enters the 50 pipe freely until the lead-in. | test | clear_of(BODY, V-IN-50, 0.0) (the pipe's wall sweeps down onto the flange without hitting anything except the stop) | 2 | |
| L3.11.3.1 | V-IN-50 clear. | test | passes | 2 | |

### L1.12 The package says what was built and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds `reducer.stl` (mm), the `.scad` source, `layout.json` (build direction, `Z_S40`, `Z_S50`, which end is down) and the agent's fit report. | inspection | all present and readable; the STL's largest axis is 20 to 60 | 3 | G0 |
| L3.12.1.1 | Files present and parse; units. | inspection | true | 3 | G0 |
| L3.12.1.2 | Declared stop positions match the STL. | inspection | `Z_S40`, `Z_S50` within 0.10 of the measured planes | 2 | |
| L2.12.2 | The agent's fit report agrees with the grader. | analysis | for each of bore, spigot OD, depth, length, wall the agent reports: |d_agent − d_judge| ≤ 0.05 | 1 | |
| L3.12.2.1 | Self-report vs judge. | analysis | 100% within 0.05 | 1 | |

## 6. Gates and counts

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.12.1.1), **G1** one
manifold body (L3.1.1.1), **G2** through-bore (L3.8.1.1), **G3** the 40 side fit (L3.2.1.1 and
L3.6.1.1), **G4** the 50 side fit (L3.3.1.1 and L3.6.2.1), **G5** both pipes seat on the stops
(L3.4.3.1 and L3.4.3.2). Classes: WRONG (a gate fails), MINOR (no gate fails, a weight-3 L3 fails),
CORRECT (all weight-3 pass), MEETS (CORRECT and every L3 of weight 1 and 2 passes).

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 28 |
| L3 | 38 |

## 7. Feasibility (a design exists)

A revolved profile (one body, axis Z, 40 side down), numbers in mm, verified with `manifold3d`
(watertight, one shell, volume 12 876 mm³, bounding box 52.15 × 52.15 × 34.75):

| Feature | Value |
|---|---|
| socket bore Ø | 39.85 (from Z 0.5; 0.5 × 0.5 lead-in at the mouth) |
| socket outside Ø | 44.65 (wall 2.4) up to Z 16.0 |
| S40 | internal shoulder, underside at Z 15.0, from bore R 19.925 to R 18.925 (width 1.0); inner Ø 37.85 up to Z 17.0 |
| through-bore | Ø 37.85 at the shoulder (≥ 34.0), then a 45° cone widening to Ø 45.35 at Z 20.75 |
| outside transition | 45° cone from R 22.325 at Z 16.0 to R 26.075 at Z 19.75 (cone-to-cone thickness 3.1) |
| S50 | flange top face at Z 19.75, from R 25.075 to R 26.075 (width 1.0) |
| spigot | OD 50.15, ID 45.35 (wall 2.4), Z 19.75 to 34.75 (length 15.0, 0.5 × 0.5 lead-in at the end) |
| interference | 40.0 − 39.85 = 0.15; 50.15 − 50.0 = 0.15; both stacks [0.00, 0.30] |
| pipe contact on stops | 40 pipe end annulus R 18.0 to 20.0 on R 18.925 to 19.925: 122 mm²; 50 pipe end R 25.0 to 28.0 on R 25.075 to 26.075: 161 mm² |
| pipe end gap | `Z_S50` − `Z_S40` = 19.75 − 15.0 = 4.75 |
| print | 40 end down; overhang scan finds one flat ring at Z 15.0 (the S40 underside), 1.0 mm wide, exempt (A8); bed contact 255 of 319 mm² = 80% (0.5 x 0.5 lead-in); the exterior and interior transitions are 45° cones |

## 8. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 | Method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | One printable part | L2.1.1 | L3.1.1.1–2 | L1.1 | analysis | "A reducer" |
| L1.2 | 40 mm socket | L2.2.1–L2.2.3 | L3.2.1.1–2, L3.2.2.1, L3.2.3.1 | L1.2 | inspection | "slides over a 40 mm pipe", "0.15 mm interference" |
| L1.3 | 50 mm spigot | L2.3.1–L2.3.3 | L3.3.1.1–2, L3.3.2.1, L3.3.3.1 | L1.3 | inspection | "into a 50 mm pipe's inside", "0.15 mm interference" |
| L1.4 | Shoulder stops | L2.4.1–L2.4.3 | L3.4.1.1–2, L3.4.2.1–2, L3.4.3.1–2 | L1.4 | demonstration | "shoulder stop at 15 mm depth on each" |
| L1.5 | Wall | L2.5.1–L2.5.2 | L3.5.1.1–2, L3.5.2.1 | L1.5 | inspection | "Wall thickness 2.4 mm" |
| L1.6 | Friction fit | L2.6.1–L2.6.3 | L3.6.1.1, L3.6.2.1, L3.6.3.1–2 | L1.6 | analysis | "friction fit with 0.15 mm interference allowance" |
| L1.7 | Concentric | L2.7.1–L2.7.2 | L3.7.1.1, L3.7.2.1 | L1.7 | inspection | "reducer" (a concentric step), implied |
| L1.8 | Flow | L2.8.1 | L3.8.1.1–2 | L1.8 | analysis | implied by "pipe" |
| L1.9 | Vertical print | L2.9.1–L2.9.4 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1 | L1.9 | analysis | "Printed vertically" |
| L1.10 | Compact | L2.10.1 | L3.10.1.1 | L1.10 | inspection | implied (printer bed) |
| L1.11 | Pipes seat | L2.11.1–L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | L1.11 | test | "slides over", "into" |
| L1.12 | Evidence | L2.12.1–L2.12.2 | L3.12.1.1–2, L3.12.2.1 | L1.12 | inspection | needed by the judge |

## 9. Grading (design-specific; used because `generalize/rubric.md` is missing)

- **Verdict:** WRONG (any gate G0 to G5 fails), MINOR (no gate fails, some weight-3 L3 fails),
  CORRECT (every weight-3 L3 passes), MEETS (CORRECT and every L3 of weight 1 and 2 passes).
  UNVERIFIED counts as FAIL. Report also the weighted score Σ(weight × pass)/Σ(weight).
- **Precedence:** the numbers in this document beat `part.json` (for example `generic_tube` has no default sizes;
  the sizes here are the request's). Never relax a criterion or round in the design's favour beyond ε.
- **WHERE a defect is:** one entry per failed or UNVERIFIED L3, gates first then weight 3, 2, 1, with:
  `req` (L3 with L2 and L1), `status`, `feature` (named by function, for example "socket bore" or "S50 flange top"),
  `face` (surface and outward normal), `location` (Z interval, or Z and radius, in the reducer frame, and the
  angle sector if local), `measured` / `limit` / `margin`, `reference` (M-PIPE-40, V-BORE and so on), `needed`
  (the target as numbers, for example "bore Ø must be 39.80 to 39.87, now 39.95") and `evidence` (saved slice or
  defect STL). `needed` never says how to build it.
- **Measured-values table (always filled in):** bore Ø; spigot OD; I40; I50; socket depth; spigot length;
  socket wall; spigot wall; min local thickness; narrowest bore; S40 and S50 width and flatness; contact areas;
  coaxial offset; overhang patches; bed contact; bounding box; pipe end gap; self-report agreement.

## Audit

Adversarial audit against `benchmarks/enclosure/rubric.md` (the generalize rubric is absent), the catalogue and the L1 text in
`design.json`. The feasibility sketch of section 7 was rebuilt as a revolved profile in `manifold3d` and re-measured with
two reference pipes, the entry sweeps, the Ø34.0 bore and a trimesh overhang scan; `generic_tube` loads through `parts.Catalog`
(it needs `outer_diameter` and `length` from the request). L1 12 (E1-01: 12), L2 28 (45), L3 38 (69): a single revolved part,
simpler than the enclosure; counts match section 6.

| # | Finding | Fix |
|---|---|---|
| 1 | Contradiction: L3.9.2.1 required bed contact >= 90% of the end annulus, but L1.2 / L1.3 require a lead-in of at least 0.3 mm radially at the printed end, and the sketch's own 0.5 x 0.5 lead-in leaves 255 of 319 mm² = 80% (re-measured). With a 0.3 lead-in at most 88%, with a 1.0 lead-in 60%, so 90% could never be met together with the lead-in. | L2.9.2 / L3.9.2.1 now require >= 50% (the end annulus with any permitted lead-in, 0.3 to 1.0, stays above 57%); the sketch says 80%. L1.9 states the 50% so the agent is told. |
| 2 | Knife edge: A8 exempted horizontal ledges "up to 1.0 mm wide", while L3.4.1.2 / L3.4.2.2 require a stop width of at least 1.0; the stop that faces down in the declared orientation had to be exactly 1.0 (+0.02). | A8 and L2.9.3 exempt flat ledges up to 1.5 mm wide (a stop); stop widths of 1.0 to 1.5 are feasible. L1.9 says so. |
| 3 | 45 degree cones have n_z = −cos 45 exactly; with a strict "<" a mesh with rounding noise can fail. | L2.9.3 adds the 0.5 degree angle tolerance of section 1 (the overhang threshold is 45.5 degrees from vertical). |
| 4 | The judge's references use pipe walls (40 mm pipe ID 36.0, 50 mm pipe OD 56.0, A4) that appear only in A4 and the request notes; the request text never gave them, yet they size V-IN-50, V-BORE and the 56 mm limit. | The request now says "The 40 mm pipe has a 2 mm wall and the 50 mm pipe a 3 mm wall", `request_notes` updated. |
| 5 | Numbers the judge uses that the agent was never told: lead-in 0.3 to 1.0 (both directions), minimum length 30.0 (L2.10.1), pipe-end gap >= 1.0 (L2.11.1), bed contact, the ledge rule. | Added to the L1 texts in `design.json` (ids and count unchanged). |
| 6 | Sketch volume 12 871 mm³: re-measured 12 876 (rounding). Re-measured and confirmed: one shell, NoError; bounding box 52.15 x 52.15 x 34.75; stop contact areas 122.05 and 160.69 mm²; V-IN-40, V-IN-50 and V-BORE penetration 0; pipes 6.9 apart; seated-pipe penetration is only the 0.075 radial fit layer (136 and 172 mm³); the only downward face above 45 degrees is the S40 ring (122 mm², 1.0 wide). | Number corrected. |

Observation (not changed): A2 stays an open question of uncertainty high (a "50 mm" PVC pipe usually has an outside diameter of 50 mm); the request text now fixes it (inside diameter 50 mm), which is the decision graded.
