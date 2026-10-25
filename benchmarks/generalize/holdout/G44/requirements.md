# G44 Screwdriver rack with pocketed holders: requirements (L1 / L2 / L3)

HELD-OUT design of the generalisation set (family fixture_adapter; capabilities pocket_fit, pattern_array,
wall_mount, load_path). The control loop never trains on it. The machine-readable request (L1 only,
`dev.json` format) is `design.json` next to this file. It is modelled on `benchmarks/enclosure/requirements.md`
(E1-01) and uses the same conventions: tolerances (1.2), `clear_of` and designed contact (1.3), reference
models and envelopes (2), assumptions with uncertainty and fixed decisions (3), a tree whose every L3 is
measured by Python on the delivered STL (4), gates (5), a feasibility sketch (7) and traceability (8).

**Brief (plan.json, verbatim):** "A wall-mounted rack holding six screwdrivers in pockets 25 mm deep with the
handle diameters 20, 22, 24, 26, 28 and 30 mm at 38 mm pitch. Pocket clearance 0.4 mm per side, wall mount
with two 5 mm screws and a back plate 6 mm thick. It must hold 1.5 kg in total."

**Rubric note.** The generic file `benchmarks/generalize/rubric.md` did not exist when this entry was written, so
section 6 below is the design-specific rubric (measuring recipes, classes, how to report where a defect is). If the
generic rubric appears later, it applies on top of this file; where they disagree, the numbers in this file win.

**How to read the tree.** L1 is what the owner needs, L2 an engineering requirement, L3 a check on the geometry. Each
L3 row has a method (inspection, analysis, demonstration, test, human; as in `design.json`), a pass/fail criterion with
a number and tolerance, a weight (3 critical, 2 major, 1 minor) and a gate mark (G0..G4) for must-pass rows. Every
number that comes from an assumption (section 3) is provisional until the owner confirms it. Never relax a criterion
because the agent fails it.

---

## 1. Frames, tolerances, designed contact

### 1.1 Frame

- **Rack frame:** Z up, Z = 0 on the rack's underside (the bed face in the stated print pose); the wall plane is
  Y = 0 and the rack extends to +Y (away from the wall); X runs along the pocket row. The grader normalises the
  delivered STL by rotations of 90 degrees and one X mirror so that the Ø20 pocket is at the smallest X and the
  back face is at Y = 0 (never penalised). Y measured **from the back face** (the face that touches the wall).
- Lengths in mm, angles in degrees, forces in N, stresses in MPa (N/mm²), moments in N·mm.

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered mesh, never by eye.

| Quantity | ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm | a value passes if it meets the limit within ε |
| angle | 0.5° | same |
| intersection volume | 0.01 mm³ | "no interference" means volume ≤ 0.01 mm³ |
| hole / pocket diameter | largest inscribed circle of the section at mid-depth | what a pin of that size sees |
| depth | ray cast along the axis from the mouth plane to the floor | |

"nominal ± t" means t is the design tolerance and ε is added to it.

### 1.3 Interference checks and designed contact

- **`clear_of(bodies, volume, c)`**: minimum distance between `bodies` and `volume` is ≥ c − ε; penetration volume
  must be ≤ 0.01 mm³ (recipe in 6.2).
- **`inside(volume, void, c)`**: `volume` lies in `void` with every point ≥ c − ε from the void boundary.

**Designed contact for this design (it is never interference; only penetration > 0.01 mm³ counts for these pairs):**
1. a handle model resting on its pocket floor (the bottom 0.2 mm of M-SD-k is excluded from side checks),
2. the M5 screw head on its counterbore floor and the screw shank in its clearance hole,
3. the back face lying on the wall plane (Y = 0).

A distance of zero is a pass for these pairs.

---

## 2. Reference models, envelopes

Built independently by the grader (never trusted from the agent) from the catalogue
(`benchmarks/enclosure/parts/generic_cylinder`, `benchmarks/generalize/parts/bolt_m5_iso7380`) and the
design's declared layout. `generic_cylinder` takes its diameter and height from the request text; the diameters
and the 100 mm height below are request/assumption numbers (A1, A2), not code constants.

### 2.1 Reference models (M-)

| Name | What | Source | Size and position (rack frame, mm) | Datums |
|---|---|---|---|---|
| **M-SD-k** (k = 1..6) | screwdriver handle k | catalogue `generic_cylinder` | Ø d_k with d_k = 20, 22, 24, 26, 28, 30 (request); height 100.0 (A2); axis +Z through the declared pocket axis; base on the declared pocket floor | `AXIS`, `BOTTOM`, `TOP` |
| **M-SCREW-j** (j = 1, 2) | 5 mm wall screw | catalogue `bolt_m5_iso7380` | thread Ø 5.0, head Ø 9.5 × 2.75, clearance Ø 5.5, counterbore Ø 9.9 × 2.95 (catalogue); axis along −Y; head bearing plane on the counterbore floor | `AXIS`, `HEAD_BEARING`, `HEAD_TOP` |
| **M-WALL** | the wall | envelope | half-space Y ≤ 0, flat and vertical | plane Y = 0 |

### 2.2 Envelopes (V-) and computed volumes

| Name | Definition | Used by |
|---|---|---|
| **V-POCKET-k** | the void of pocket k as built: the connected blind region open at +Z, from the floor to the mouth plane | L2.1.x, L2.2.x |
| **V-PLATE** | the slab Y in [0, 6.0] over the plate's X and Z extent (the back plate as required) | L2.2.4, L2.5.x |
| **V-INSERT-k** | M-SD-k swept along +Z from its seated pose to 150.0 above the pocket mouth plane (the drop-in path) | L2.4.2 |
| **V-DRIVER-j** | Ø 6.0 column on the axis of screw j from the counterbore floor along +Y for 50.0 (driver_diameter and driver_reach rules), with M-SD-1..6 seated | L2.6.4 |
| **V-SECTION** | the section of the delivered body by the plane Y = plate front face + 0.1 (the shelf root; from the mesh) | L2.7.3 |
| **V-CL-j** | head cylinder of M-SCREW-j (Ø 9.5, height 2.75 above the bearing plane) | L3.6.4.2 |

### 2.3 Seating rule

M-SD-k is placed at the pose in `layout.json`. The grader verifies it: the M-SD-k bottom lies on the pocket floor
(distance ≤ 0.10) and its axis is coaxial with the pocket (residual ≤ 0.25). If the layout is missing or fails, the
grader finds the six pockets by slicing at mid-depth, orders them along X, and seats M-SD-k by ascending diameter. If
fewer than six pockets exist, every L1.1 to L1.4 check fails.

---

## 3. Assumptions, fixed decisions and open questions for the owner

Each line gives the value chosen and why; every one is derived from the brief or engineering convention, not asked.

| # | Question | Value chosen | Why and uncertainty |
|---|---|---|---|
| A1 | How does a screwdriver sit in the rack? | Handle down in the pocket, shaft up. | The pocket diameters are the handle diameters, so the handle goes in. Alternative (shaft in a hole) is not graded. |
| A2 | Handle length and shape? | Plain cylinder, 100.0 long (±30). | Typical hand-tool handles are 90 to 130. Shorter handles only help the access checks. The shaft and tip are not modelled (they are thin and point up). |
| A3 | Handle taper? | None; the pocket is a straight bore. | Real handles taper at the butt; a straight bore with 0.4 per side is conservative. |
| A4 | Mass and load case? | 1.5 kg total, shared by six pockets, weight acts vertically through the six pocket axes (centroid X_G = mean of the six pocket X, Y = mean pocket Y). Design load F_d = 1.5 × 9.81 × 3 = 44.145 N (safety factor 3 for knocks and creep, in the load, not in the allowables). | "hold 1.5 kg in total" (brief). Safety factor 3 is a common value for printed hand-load parts. A single heavy tool in one pocket would load that pocket more; the pocket floor check (L3.7.3.2) covers the full F_d on the smallest pocket. |
| A5 | Which 5 mm screw? | M5 button head ISO 7380: head Ø 9.5 × 2.75, clearance hole Ø 5.5, catalogue counterbore Ø 9.9 × 2.95. The wall fixing (plug or wood) is the owner's. | "two 5 mm screws" (brief) and the catalogue part `bolt_m5_iso7380`. Counterbore band in L3.6.2.x is the catalogue value ±0.4 for FDM. |
| A6 | Screw allowables? | Tension T_a = 150 N and shear V_a = 300 N per screw in the wall, interaction T/T_a + V/V_a ≤ 1. | A 5 mm screw in a plug in drywall or a stud is rated at hundreds of N; 150 N tension is a low, conservative figure. Uncertainty ±50 percent; depends on the wall. |
| A7 | Printed-material allowables? | PLA, layers horizontal (XY). Bearing under the screw head ≤ 5.0 MPa; bending of the shelf root ≤ 3.0 MPa; pocket-floor bearing ≤ 1.0 MPa. | PLA tensile is about 40 to 50 MPa in-layer and 10 to 20 across layers; the figures include a factor of about 4 for layer lines and creep. Uncertainty ±30 percent. |
| A8 | Material and printing? | PLA, FDM, 0.4 nozzle, 0.2 layers. Wall and floor ≥ 2.4 (rules `wall_default`, 6 perimeters). Round holes Ø ≤ 12 and bridges ≤ 15 print unsupported; no face steeper than 45° from vertical. | Common settings (design_rules.json). |
| A9 | Print size? | One piece. The printer bed is 256 × 256 × 256 (stated in the request). The 200 mm default bed of E1-01 is overridden for this design because the row is longer than 200. | Bambu-class bed. The row needs about 221 mm. Uncertainty: owner's printer; the request carries the number. |
| A10 | Wall? | Flat, vertical, rigid; the back face is the only contact. | A rack screwed on a wall. |
| A11 | Order along the row? | Ascending 20, 22, 24, 26, 28, 30 in the listed order (X is mirrored by the grader if needed). | Listed order in the brief. |
| A12 | Pocket mouth, chamfers, labels? | None required, none graded. A lead-in chamfer is allowed if the diameter check is made at mid-depth. | Not in the brief. |

### Fixed decisions (one choice, no alternatives accepted)

| # | Decision | Why |
|---|---|---|
| FD1 | The rack is one body: back plate (vertical, Y 0 to 6.0) plus a shelf block (pockets) fused to the plate's front face. Pockets are vertical (axis +Z). | A shelf block carries the pockets; one body prints without assembly. |
| FD2 | Print pose = assembly pose (underside Z = 0 on the bed). The design may state another pose in `layout.json` and is then graded in that pose. | Vertical pockets then need no supports. |
| FD3 | The screws pass through the back plate **above** the shelf, between handles, with the heads recessed in counterbores on the plate's front face and driven from the front along +Y. | The screws must be reachable with all six screwdrivers in place (L1.6). |
| FD4 | Nothing is allowed behind the back face (Y < 0): no recess for wall bumps, no feet. | "hangs flat on the wall". |
| FD5 | Pocket diameter = handle diameter + 2 × 0.4 (both numbers from the request). | "pocket clearance 0.4 mm per side". |

---

## 4. Requirements tree

### L1.1 Six pockets with the right diameters

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | Exactly six blind round pockets open at the top. | inspection | six connected blind regions open at +Z, none through | 3 | |
| L3.1.1.1 | Pocket count. | inspection | = 6 | 3 | G2 |
| L3.1.1.2 | Pockets are round. | inspection | at mid-depth, max radius / min radius ≤ 1.02 for each | 1 | |
| L2.1.2 | Each pocket is its handle diameter plus 0.8. | inspection | Ø_k = d_k + 0.8 ± 0.10 for k = 1..6 (20.8, 22.8, 24.8, 26.8, 28.8, 30.8) | 3 | |
| L3.1.2.1 | Inscribed pocket diameters at mid-depth. | inspection | each within ± 0.10 of d_k + 0.8 | 3 | G2 |
| L3.1.2.2 | Radial clearance to the seated handle. | analysis | min distance M-SD-k (side) to pocket wall in [0.35, 0.45] for each k | 3 | |
| L2.1.3 | Pockets are vertical and open upward. | inspection | pocket axis within 1.0° of +Z | 2 | |
| L3.1.3.1 | Pocket axis direction. | inspection | ≤ 1.0° | 2 | |

### L1.2 Depth, floor and walls

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Each pocket is 25 mm deep with a flat floor. | inspection | depth 25.0 ± 0.3; floor normal within 1.0° of +Z, flatness ≤ 0.2 | 3 | |
| L3.2.1.1 | Pocket depth (mouth plane to floor), each k. | inspection | 24.7 ≤ depth ≤ 25.3 | 3 | G2 |
| L3.2.1.2 | Floor flat. | inspection | flatness ≤ 0.2; normal ≤ 1.0° from +Z | 2 | |
| L2.2.2 | The floor is thick enough. | inspection | material under each pocket floor to the underside ≥ 2.4 | 2 | |
| L3.2.2.1 | Floor thickness (ray cast down from the floor). | inspection | ≥ 2.4 | 2 | |
| L2.2.3 | Walls around every pocket are thick enough. | analysis | wall to every outer face ≥ 2.4; ligament between neighbours ≥ 2.4 | 2 | |
| L3.2.3.1 | Wall from each pocket to the nearest outer face (front, ends, back face counted). | analysis | ≥ 2.4 | 2 | |
| L3.2.3.2 | Ligament between neighbouring pockets. | analysis | ≥ 2.4 | 2 | |
| L2.2.4 | The pockets do not cut into the back plate. | analysis | V-POCKET-k ∩ V-PLATE ≤ 0.01 mm³ for every k | 3 | |
| L3.2.4.1 | Pocket / plate intersection. | analysis | ≤ 0.01 mm³ | 3 | |

### L1.3 One straight row at 38 mm pitch, ascending

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Neighbouring pocket axes are 38 apart. | inspection | 38.0 ± 0.25 (five distances) | 3 | |
| L3.3.1.1 | Centre-to-centre distance of neighbours. | inspection | 37.75 ≤ p ≤ 38.25, all five | 3 | G2 |
| L2.3.2 | The axes lie in one horizontal line and the mouths share one plane. | inspection | axes collinear within 0.25; mouth plane Z spread ≤ 0.10; floor Z spread ≤ 0.10 | 2 | |
| L3.3.2.1 | Collinearity of the six axes. | inspection | max deviation from the best-fit line ≤ 0.25 | 2 | |
| L3.3.2.2 | Common mouth plane and floor plane. | inspection | spread ≤ 0.10 each | 2 | |
| L2.3.3 | Increasing diameter along the row. | inspection | Ø increases monotonically with X, smallest at min X | 2 | |
| L3.3.3.1 | Diameter order. | inspection | strictly increasing | 2 | |

### L1.4 The handles drop in and seat

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | M-SD-k seats on its pocket floor, coaxial with the pocket (seating rule 2.3). | test | floor distance ≤ 0.10; axis residual ≤ 0.25 | 3 | |
| L3.4.1.1 | Seating of the six handles at the declared pose. | test | as L2.4.1 | 3 | |
| L2.4.2 | Each handle drops straight down into its pocket without touching anything. | test | clear_of(ALL, V-INSERT-k, 0.30) for every k (the floor patch excluded as designed contact) | 3 | |
| L3.4.2.1 | Insertion sweep clear. | test | d ≥ 0.30 for each k | 3 | G3 |
| L2.4.3 | Seated handles clear the pocket walls, each other and the back plate. | analysis | clear_of(ALL, M-SD-k side, 0.30); handle-to-handle distance ≥ 1.0 | 3 | |
| L3.4.3.1 | Seated handle (side) to the body, k = 1..6. | analysis | d ≥ 0.30 | 3 | |
| L3.4.3.2 | Handle-to-handle clearance (neighbours, full height). | analysis | ≥ 1.0 | 2 | |

### L1.5 Back plate 6 mm, flat, backing every pocket

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Plate thickness 6 mm. | inspection | 6.0 ± 0.2 (median ray cast along Y, 2 mm grid, away from holes and the shelf) | 3 | |
| L3.5.1.1 | Plate thickness. | inspection | 5.8 ≤ t ≤ 6.2 | 3 | G3 |
| L2.5.2 | The back face is flat and nothing is behind it. | inspection | all material at Y ≥ −0.02; planarity ≤ 0.2; back-face contact area ≥ 90 percent of the plate outline area | 3 | |
| L3.5.2.1 | No material behind the wall plane. | inspection | min Y ≥ −0.02 | 3 | |
| L3.5.2.2 | Back-face planarity. | inspection | ≤ 0.2 | 2 | |
| L3.5.2.3 | Back-face contact area. | inspection | ≥ 90 percent of plate X × Z outline | 2 | |
| L2.5.3 | The plate spans every pocket and is tall enough for the screws. | inspection | plate X extent covers every pocket outline; plate top Z in [45, 80]; each screw axis Z ≥ shelf top + 8.0; plate top ≥ screw axis Z + 8.0 | 2 | |
| L3.5.3.1 | X coverage of the pockets. | inspection | min plate X ≤ min pocket edge; max plate X ≥ max pocket edge | 2 | |
| L3.5.3.2 | Plate height and screw position. | inspection | as L2.5.3 | 2 | |

### L1.6 Two 5 mm screws, recessed, reachable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Exactly two clearance holes through the plate, along Y. | inspection | count = 2; Ø 5.5 ± 0.2; axis within 1.0° of Y | 3 | |
| L3.6.1.1 | Through-hole count. | inspection | = 2 | 3 | G3 |
| L3.6.1.2 | Hole diameter (inscribed, at mid-thickness of the floor under the counterbore). | inspection | 5.3 ≤ Ø ≤ 5.7 | 3 | G3 |
| L3.6.1.3 | Hole axis direction. | inspection | ≤ 1.0° from Y | 2 | |
| L2.6.2 | The head is recessed in a counterbore on the front face. | inspection | counterbore Ø 9.7 to 10.4; depth 2.9 to 3.6; plate floor under the head ≥ 2.4 | 2 | |
| L3.6.2.1 | Counterbore diameter. | inspection | 9.7 ≤ Ø ≤ 10.4 | 2 | |
| L3.6.2.2 | Counterbore depth and remaining floor. | inspection | 2.9 ≤ depth ≤ 3.6; floor ≥ 2.4 | 2 | |
| L2.6.3 | The screws are far apart, level, and straddle the load. | analysis | axis spacing along X ≥ 100.0; Z of the two axes within 1.0; x1 ≤ X_G ≤ x2 | 2 | |
| L3.6.3.1 | Screw spacing along X. | inspection | ≥ 100.0 | 2 | |
| L3.6.3.2 | Level. | inspection | ΔZ ≤ 1.0 | 1 | |
| L3.6.3.3 | Load centroid between the screws. | analysis | x1 ≤ X_G ≤ x2 (X_G = mean pocket X) | 2 | |
| L2.6.4 | Each screw is reachable with the six screwdrivers in place. | test | clear_of(ALL ∪ M-SD-1..6, V-DRIVER-j, 0.0) for j = 1, 2; head fits its counterbore | 3 | |
| L3.6.4.1 | Driver column clear of the body and handles. | test | d ≥ 0.0, both | 3 | G3 |
| L3.6.4.2 | Head in the counterbore (V-CL-j). | analysis | no penetration; radial clearance ≥ 0.0 | 2 | |

### L1.7 It holds 1.5 kg: the load path

The load path (grader recomputes; the agent's `load_path.json` must agree, L2.10.2). Symbols from the measured mesh:
a = mean pocket-axis Y (distance from the wall plane), z_s = mean screw-axis Z above Z = 0, x1 and x2 the screw
X positions, X_G the mean pocket X, h and L the Z height and X length of V-SECTION, I_x = ∫ z² dA of V-SECTION
about its centroid axis parallel to X, D_h the measured clearance-hole Ø.

- F_d = 1.5 × 9.81 × 3 = 44.145 N.
- Rotation about the lower back edge (Y = 0, Z = 0): T_tot = F_d · a / z_s. Lever rule on X: T_1 = T_tot (x2 − X_G)/(x2 − x1), T_2 = T_tot − T_1. Shear shared the same way: V_j = F_d · T_j / T_tot.

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Screw tension and shear stay in the screw limits (A6). | analysis | T_j/150 + V_j/300 ≤ 1.0 for j = 1, 2 | 3 | |
| L3.7.1.1 | Screw interaction ratio. | analysis | ≤ 1.0, both screws | 3 | G4 |
| L2.7.2 | The plate bears the head load. | analysis | σ_b = T_j / (π/4 (9.5² − D_h²)) ≤ 5.0 | 2 | |
| L3.7.2.1 | Head bearing stress on the counterbore floor. | analysis | ≤ 5.0 | 2 | |
| L2.7.3 | The shelf root carries the weight in bending. | analysis | σ = F_d (a − 6.0) (h/2) / I_x ≤ 3.0 (V-SECTION at the plate front face + 0.1) | 2 | |
| L3.7.3.1 | Shelf-root bending stress. | analysis | ≤ 3.0 | 2 | G4 |
| L3.7.3.2 | Pocket-floor bearing under the smallest handle with the full F_d. | analysis | F_d / (π/4 Ø_1²) ≤ 1.0 | 1 | |
| L2.7.4 | The load path is continuous. | analysis | the rack is one connected body and V-SECTION is a single connected region of area ≥ 0.5 × (X length × shelf height) | 2 | |
| L3.7.4.1 | Continuity of the shelf-to-plate joint. | analysis | single region; area ≥ 0.5 × h × L | 2 | |

### L1.8 Compact, hangs flat

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Overall size limits. | inspection | X ≤ 240.0, Y ≤ 45.0, Z ≤ 80.0 | 1 | |
| L3.8.1.1 | Bounding box. | inspection | as L2.8.1 | 1 | |
| L2.8.2 | The shelf is not taller than needed. | inspection | shelf block height = pocket depth + floor ≤ 34.0 | 1 | |
| L3.8.2.1 | Shelf top Z minus underside Z. | inspection | ≤ 34.0 | 1 | |

### L1.9 One manifold body that prints without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | One manifold shell. | analysis | 1 shell; manifold3d accepts it | 3 | |
| L3.9.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.9.2 | No unsupported overhang in the stated pose. | analysis | 0 offending faces (area > 1 mm²); round holes Ø ≤ 12.0 and bridges ≤ 15.0 exempt | 2 | |
| L3.9.2.1 | Overhang and bridge scan. | analysis | 0 patches | 2 | |
| L2.9.3 | It rests on a flat face. | analysis | bed contact ≥ 50 percent of the plan bounding box | 1 | |
| L3.9.3.1 | Bed-contact area. | analysis | ≥ 50 percent | 1 | |
| L2.9.4 | No thin features. | analysis | min local thickness ≥ 0.8 | 1 | |
| L3.9.4.1 | Thin-feature scan. | analysis | ≥ 0.8 | 1 | |
| L2.9.5 | It fits the bed. | inspection | bounding box ≤ 256 per axis | 1 | |
| L3.9.5.1 | Bounding box. | inspection | ≤ 256 | 1 | |

### L1.10 The package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Package present: `rack.stl` (assembly pose, mm), the `.scad` source, `layout.json` (pose of each pocket: diameter, axis X, Y, floor Z; screw axes; print pose), `load_path.json` (F_d, a, z_s, x1, x2, T_j, V_j, σ values) and the self-report. | inspection | all present and readable | 3 | |
| L3.10.1.1 | Files parse; the STL is in mm (largest bounding-box axis 100 to 256). | inspection | true | 3 | G0 |
| L3.10.1.2 | Declared layout verifies under the seating rule (2.3). | analysis | six handles seat; residuals as 2.3 | 3 | |
| L2.10.2 | The agent's own reports agree with the judge. | analysis | each `clear_of` d within 0.10; each load-path number within 10 percent of the grader's | 1 | |
| L3.10.2.1 | Self-report clearances vs judge. | analysis | same pass/fail, \|Δd\| ≤ 0.10 | 1 | |
| L3.10.2.2 | `load_path.json` numbers vs judge. | analysis | within 10 percent | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 10 |
| L2 | 33 |
| L3 | 51 (all measured by Python on the STL) |

Gates (a failure makes the design WRONG regardless of score):
**G0** package (L3.10.1.1); **G1** one manifold shell (L3.9.1.1); **G2** the pockets (L3.1.1.1, L3.1.2.1,
L3.2.1.1, L3.3.1.1); **G3** the handles drop in, the plate and the screws (L3.4.2.1, L3.5.1.1, L3.6.1.1,
L3.6.1.2, L3.6.4.1); **G4** the load path (L3.7.1.1, L3.7.3.1).

---

## 6. Design-specific rubric (the generic rubric was absent when this was written)

### 6.1 Procedure

1. G0: load the STL; if missing or unreadable stop (DOES NOT MEET, one defect on L3.10.1.1).
2. Units: largest bounding-box axis within 100 to 256; if it looks like inches or metres record a defect, do not rescale.
3. Normalise the frame (1.1), record the transform. Build M-SD-k from the layout (2.3), V- envelopes (2.2).
4. Run every L3 with Python, in order; record measured value, limit, signed margin (negative = fail), PASS / FAIL /
   UNVERIFIED. UNVERIFIED counts as FAIL. N/A only for physical tests nobody printed.
5. Look at renders after measuring; render-only findings are observations and do not change the verdict.
6. Decide and report (6.3, 6.4).

### 6.2 Measurement recipes (trimesh 5.1, manifold3d 3.5; count shells with `decompose()`)

```python
import numpy as np, trimesh, manifold3d as m3d
M = m3d.Manifold
def load(p):
    tm = trimesh.load(p, force="mesh")
    return tm, M(m3d.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                          tri_verts=np.asarray(tm.faces, np.uint32)))
def clear_of(bodies, vol, c):
    pen = (bodies ^ vol).volume()
    if pen > 0.01: return {"d": None, "pen": pen, "where": (bodies ^ vol).bounding_box()}
    return {"d": bodies.min_gap(vol, c + 5.0), "pen": 0.0}      # PASS: pen <= 0.01 and d >= c - 0.02
```

- **Pockets:** slice the body at Z = floor + depth/2 (`Manifold.slice`); each hole polygon -> largest inscribed circle
  (diameter) and centre; roundness from min/max centroid-to-vertex radius. Depth: ray cast down each axis from above the
  mouth to the floor. Floor flatness: fit a plane to floor vertices. Mouth plane: the top faces around the pocket.
- **Walls and ligaments:** minimum distance from the pocket boundary (sampled 1 mm) to the outer surface minus the
  pocket itself; neighbours: centre distance minus the two radii.
- **Seating and sweeps:** build the cylinder with `M.cylinder(h, r, r, 128)`, translate to the declared pose; V-INSERT-k =
  the cylinder extruded 150 above the mouth plane. For `clear_of` against M-SD-k side, cut the bottom 0.2 mm off first.
- **Screw holes:** slice at Y = mid-thickness of the floor under the counterbore for the through hole (Ø inscribed);
  slice at Y = plate front face − depth/2 for the counterbore; depth by ray cast along Y. Axis direction from a
  least-squares line through slice centres at two Y values.
- **V-DRIVER-j:** `M.cylinder(50, 3.0, 3.0, 64)` rotated to +Y, base on the counterbore floor, `clear_of(body ∪ M-SD, ., 0)`.
- **Load path:** compute a, z_s, x1, x2, X_G from the measured axes; V-SECTION by slicing the mesh at Y = front face + 0.1
  (polygon union); I_x = Σ over polygon triangles of ∫ z² dA about the centroid axis. Use the formulas in 4 / L1.7.
- **Printability:** rotate into the stated pose; a face with unit normal n overhangs if n_z < −cos 45° and z > 0.05, minus
  exemptions (round holes Ø ≤ 12 in vertical walls, bridges whose ends rest on material ≤ 15 apart). Bed contact: area of
  faces with n_z < −0.999 at z < 0.05 divided by the plan bounding-box area. Thin features: inward ray cast.

### 6.3 Classes

| Class | Rule |
|---|---|
| **WRONG** | any gate G0..G4 fails |
| **MINOR** | no gate fails but a weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |
| **MEETS requirements** | CORRECT and every applicable weight-1 and weight-2 L3 passes |

Also report the weighted score Σ(weight × pass)/Σ(weight) and the worst normalised margin among weight-3 L3s.
Precedence: numbers in this file beat `part.json`; designed contact (1.3) is never interference; never relax a criterion
and never infer a pass from a render.

### 6.4 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first. Fields: `req` (L3, L2, L1), `status`, `body`,
`feature` (for example "pocket 4, Ø26.8 nominal", "left screw counterbore"), `face` (surface and outward normal),
`location` (rack-frame coordinates, a point or a box), `measured / limit / margin`, `reference` (M-SD-k, V-DRIVER-j...),
`evidence` (saved files), `needed` (a numeric target, never a design instruction). Group L3s with one geometric cause
under the first and list the others in `also_fails`.

---

## 7. Feasibility (a concrete design that meets every L3)

Rack frame; one body, pose = print pose.

| Feature | Value |
|---|---|
| Back plate | X 0 to 220.8, Y 0 to 6.0, Z 0 to 60.0 |
| Shelf block | X 0 to 220.8, Y 6.0 to 40.0, Z 0 to 28.5 (pocket depth 25.0 + floor 3.5) |
| Pocket axes | Y = 22.0; X = 13.0, 51.0, 89.0, 127.0, 165.0, 203.0 (pitch 38.0); floor Z = 3.5, mouth Z = 28.5 |
| Pocket Ø | 20.8, 22.8, 24.8, 26.8, 28.8, 30.8 |
| Screws | axes at X = 31.5 and 145.5, Z = 45.0; clearance Ø 5.5 through the plate; counterbore Ø 10.0 × 3.0 from the front face (Y 3.0 to 6.0); plate floor 3.0 |

Checks by hand:
- Walls: pocket 1 left edge X = 2.6 (wall 2.6 ≥ 2.4); pocket 6 right edge X = 218.4 (wall 2.4); front wall 40 − (22 + 15.4) = 2.6;
  back edge of pocket 6 at Y = 6.6 ≥ 6.0 (no cut into the plate), wall to the back face 6.6; webs 16.2, 14.2 (using radii),
  down to 38 − (14.4 + 15.4) = 8.2 (all ≥ 2.4). Floor 3.5 ≥ 2.4.
- Insertion: radial gap 0.4 each side (≥ 0.30, in [0.35, 0.45]); handles 9.0 apart at the worst neighbours (≥ 1.0).
- Driver columns: Ø6 at X = 31.5 spans 28.5 to 34.5, between the Ø20 handle (X 3 to 23) and the Ø22 handle (X 40 to 62); at
  X = 145.5 spans 142.5 to 148.5, between the Ø26 handle (X 114 to 140) and the Ø28 handle (X 151 to 179). Both clear.
- Screw position: Z 45.0 ≥ shelf top 28.5 + 8.0; plate top 60.0 ≥ 45 + 8; spacing 114.0 ≥ 100; X_G = 108.0 between 31.5 and 145.5.
- Load: F_d = 44.145; a = 22.0; z_s = 45.0; T_tot = 44.145 × 22 / 45 = 21.58 N; share on screw 2 = (145.5 − 108)/114 → 0.329
  for screw 1 and 0.671 for screw 2: T_1 = 7.10, T_2 = 14.48; V_2 = 29.6. Interaction 14.48/150 + 29.6/300 = 0.195 ≤ 1.
  Head bearing 14.48 / (π/4 (9.5² − 5.5²) = 47.1) = 0.31 MPa ≤ 5. Shelf root: M = 44.145 × (22 − 6) = 706 N·mm,
  I_x = 220.8 × 28.5³ / 12 = 4.26 × 10⁵ mm⁴, σ = 706 × 14.25 / 4.26 × 10⁵ = 0.024 MPa ≤ 3. Floor bearing under Ø20.8:
  44.145 / 339.8 = 0.13 MPa ≤ 1.
- Size: 220.8 × 40 × 60 (limits 240, 45, 80); bed 256. Print: underside on the bed (bed contact 100 percent), pockets
  vertical, counterbores and holes are round Ø ≤ 12 horizontal holes (exempt). No face behind Y = 0.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 | Method | Words in the request |
|---|---|---|---|---|---|---|
| L1.1 | six pockets, right diameters | L2.1.1-3 | L3.1.1.1-2, L3.1.2.1-2, L3.1.3.1 | L1.1 | inspection | "six screwdrivers", "20, 22, 24, 26, 28 and 30 mm", "0.4 mm clearance per side" |
| L1.2 | depth, floor, walls | L2.2.1-4 | L3.2.1.1-2, L3.2.2.1, L3.2.3.1-2, L3.2.4.1 | L1.2 | inspection | "pockets 25 mm deep" |
| L1.3 | one row at 38 mm | L2.3.1-3 | L3.3.1.1, L3.3.2.1-2, L3.3.3.1 | L1.3 | inspection | "at a pitch of 38 mm", "in that order along one row" |
| L1.4 | handles drop in and seat | L2.4.1-3 | L3.4.1.1, L3.4.2.1, L3.4.3.1-2 | L1.4 | test | "holds six screwdrivers upright, handle down" |
| L1.5 | back plate | L2.5.1-3 | L3.5.1.1, L3.5.2.1-3, L3.5.3.1-2 | L1.5 | inspection | "back plate 6 mm thick", "flat wall" |
| L1.6 | two screws, reachable | L2.6.1-4 | L3.6.1.1-3, L3.6.2.1-2, L3.6.3.1-3, L3.6.4.1-2 | L1.6 | test | "two 5 mm screws", "reachable with a screwdriver" |
| L1.7 | holds 1.5 kg | L2.7.1-4 | L3.7.1.1, L3.7.2.1, L3.7.3.1-2, L3.7.4.1 | L1.7 | analysis | "In total it must hold 1.5 kg" |
| L1.8 | compact, flat on the wall | L2.8.1-2 | L3.8.1.1, L3.8.2.1 | L1.8 | inspection | "wall-mounted" (size limits are assumptions) |
| L1.9 | printable single piece | L2.9.1-5 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1, L3.9.5.1 | L1.9 | analysis | "printed in one piece ... 256 mm bed, with no supports" |
| L1.10 | evidence | L2.10.1-2 | L3.10.1.1-2, L3.10.2.1-2 | L1.10 | inspection | needed by the judge (not the owner's words) |

---

## Audit

Adversarial audit (second agent). Method: `generic_cylinder` (enclosure catalogue) and `bolt_m5_iso7380` load and pass
`parts.validate` (the cylinder's `diameter` and `height` come from the request, as the catalogue requires); every number of
section 7 was recomputed (all confirmed: wall 2.6 / 2.4, webs 16.2 down to 8.2, T_tot 21.58 N, T_1 7.10, T_2 14.48, V_2 29.6,
interaction 0.195, bearing 0.31 MPa, I_x 4.26e5 mm⁴, root bending 0.024 MPa, floor bearing 0.13 MPa); the feasibility design was
then built as one solid (manifold3d, six pockets, two counterbored holes) and run against the geometric L3s: 1 shell, 220.8 ×
40.0 × 60.0, handles seat with 0.4 mm radial gap and no penetration, handle insertion paths clear, both Ø6 driver columns clear
of the body and of all six 100 mm handles (gaps 5.0 and 2.5). No geometric contradiction was found. `claude-context` was
unavailable (server failed to connect), so targeted grep was used. The generic `generalize/rubric.md` still does not exist;
section 6 is this entry's rubric. `benchmarks/heldout.json` was not opened.

Fixes made (all in place):
1. **Judge-only numbers in L1.7.** The load model (weight through the pocket axes, tipping about the lower back edge, lever
   rule about the pocket centre, shear shared in proportion) and every limit (150 N tension, 300 N shear, interaction
   T/150 + V/300 ≤ 1, 5 MPa head bearing, 3 MPa root bending, 1 MPa pocket-floor bearing) were only in A4, A6, A7 and the
   L1.7 table. They are now in the L1.7 text the agent receives, with the factor of 3 stated as already inside the load.
2. **Judge-only layout numbers moved into L1:** wall and floor at least 2.4 mm (L1.2); plate top between 45 and 80 mm (L1.5);
   screws at least 100 mm apart, level within 1 mm, centre of the pockets between them, axis at least 8 mm above the pocket
   block and 8 mm below the plate top, counterbore Ø 9.7 to 10.4 × 2.9 to 3.6 leaving 2.4 mm (L1.6).
3. Request notes updated to say so.

Checked and left unchanged: counts (10 / 33 / 51), L1 count 10, no duplicate ids, the 256 mm bed override (A9, carried by
the request), pitch 38 with pocket diameters 20.8 to 30.8 (width 215.8 between outer pocket edges, plate 220.8), the
asymmetric screw positions (X 31.5 and 145.5 sit between handles by 5.5 and 2.5), counts and gates. Residual uncertainty: the
wall-fixing allowables (A6) and the 100 mm handle length (A2) are assumptions.
