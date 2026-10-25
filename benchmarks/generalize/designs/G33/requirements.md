# G33 Pin hinge pair, two leaves: requirements (L1 / L2 / L3)

A generalization design (train split) in the style of E1-01 (`benchmarks/enclosure/requirements.md`).
The machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file.
`benchmarks/generalize/rubric.md` did not exist when this file was written, so section 9 holds the
design-specific grading rules; measuring recipes are those of `benchmarks/enclosure/rubric.md`
section 3 (load, `clear_of`, `inside`, slices, ray casting, overhang scan).

**Owner's request (verbatim):** "Two printed hinge leaves joined by a 3 mm steel pin, 40 mm long,
each leaf 25 x 40 mm with two heat-set M3 inserts. The hinge opens 0 to 180 degrees with 0.3 mm
clearance between knuckles and 0.2 mm on the pin. The leaves must not collide through the whole swing."

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete Python check on the delivered STLs. Every row has a method
(inspection, analysis, demonstration, test, human), a pass/fail criterion with a number and a
tolerance, a weight (3 = critical, 2 = major, 1 = minor) and a gate mark (G0 to G5) where a failure
makes the design WRONG. Numbers that come from an assumption (section 3) are provisional until the
owner confirms them. Do not relax a criterion because the agent fails it.

---

## 1. Frame, poses, tolerances and designed contact

- **Hinge frame:** the pin axis is Y. The leaves are delivered in the **flat pose (180 degrees)**: the
  two mounting faces lie in the plane Z = 0 and the knuckle barrels stand proud toward +Z. Leaf A is
  the leaf that owns the knuckle at the Y = 0 end (FD1) and extends toward +X; leaf B extends toward −X.
  A delivery in another frame is normalised by rotations by multiples of 90 degrees and mirroring only
  (rubric: fit the pin axis to Y, put the coplanar mounting faces on Z = 0 with the barrels toward +Z); that
  is never penalised. Units mm.
- **Hinge angle θ (FD4):** θ = 180° is the flat pose; θ = 0° is folded shut with the leaves face to face.
  The grader fixes leaf A and rotates leaf B about the pin axis by (180° − θ) **through +Z** (the barrel side).
- **Measurement tolerances ε:** length and distance 0.02; diameter 0.03 (largest inscribed circle for holes,
  smallest enclosing circle for barrels); angle 0.5 degrees; volume 0.01 mm³. A value passes if it meets its
  limit to within ε. Diameters and thicknesses are measured on slices as in `enclosure/rubric.md` 3.5
  (median of the stations, range noted).
- **Designed contact (this design).** The following are never interference:
  1. the pin in leaf A's press-fit holes (radial overlap up to 0.05 mm, L3.10.1.1);
  2. a heat-set insert in its hole (radial overlap up to 0.35 mm, L3.5.3.1: the knurled insert is bigger than
     the printed hole by design);
  3. the leaf mounting faces on whatever they are screwed to (not modelled).
  Nothing else is designed to touch. In particular, the two leaves never touch each other at any θ
  (the minimum distance is a requirement, L3.6.1.2), and leaf B never touches the pin.
- **Checks used** (`enclosure/requirements.md` 1.3, recipes in `enclosure/rubric.md` 3.2): `clear_of(bodies, volume, clearance)`
  (pass: penetration ≤ 0.01 mm³ and d ≥ clearance − ε). The grader builds the reference models and every swept pose
  itself from the catalogue and the delivered layout; the design never builds or edits them for grading.

## 2. Reference models and envelopes

| Name | What | Source | Definition (hinge frame, mm) | Datums |
|---|---|---|---|---|
| **M-PIN** | the steel pin | catalogue `dowel_pin_generic` (Ø3.0, length 40.0) | cylinder Ø3.0 on the fitted pin axis, Y 0 to 40 (flush with the two outer faces); press-fit hole 3.0, clearance hole 3.2, chamfer 0.3 | `AXIS`, `BOTTOM`, `TOP` |
| **M-INSERT-1..4** | M3 heat-set inserts, two per leaf | catalogue `heatset_m3` (OD 4.6, length 5.7, printed hole 3.9 to 4.1, hole depth 7.2, boss OD 7.0, edge distance 3.0) | each on its measured hole axis, top face flush with the mounting face (Z 0), body toward +Z | `TOP`, `AXIS`, `HOLE_BOTTOM` |
| **M-BOLT-1..4** | M3 bolt used to mount, one per insert | catalogue `bolt_m3_iso4762` (head Ø5.5 × 3.0, tool access 25.0) | on the insert axis, entering from the mounting-face side | `AXIS`, `HEAD_BEARING` |
| **LEAF-B(θ)** | leaf B rotated about the pin axis | computed | θ ∈ {0, 5, 10, …, 180}, 37 poses | pin axis |
| **V-PIN-IN** | pin insertion path | envelope | M-PIN swept along +Y from 20.0 before Y = 0 to its seated pose | pin axis |
| **V-BOLT-k** | bolt access columns | envelope | Ø6.0 cylinder on each insert axis from the mounting face outward 25.0 | insert axis |

Sanity checks before grading (not L3s): R1 units, each leaf's largest axis is 20 to 60; R2 the pin axis fit
has residual ≤ 0.05; R3 the two leaves do not intersect in the delivered flat pose; R4 each leaf has
one knuckle at Y = 0 or Y = 40 end exactly (otherwise leaf A is the one with more knuckles).

## 3. Assumptions and open questions for the owner

| # | Question | Value chosen | Why / uncertainty |
|---|---|---|---|
| **A1** | What are 0 and 180 degrees? | 0° = folded shut, plates face to face; 180° = laid flat, mounting faces coplanar. | The usual hinge convention. Uncertainty medium: some call the flat position 0. The numbers only need relabelling. |
| **A2** | "0.3 mm clearance between knuckles and 0.2 mm on the pin" | 0.3 is both the axial gap between neighbouring knuckle faces and the minimum distance between the leaves over the whole swing. 0.2 is **diametral**: the turning leaf's hole is 0.2 larger than the pin (Ø3.2); the catalogue `dowel_pin_generic` also gives 3.2 as its clearance hole. | Matches `part.json` and FDM practice. Radial 0.2 would be Ø3.4. Uncertainty medium. |
| **A3** | What holds the pin in? | The outer knuckles of leaf A (the end knuckles) have a press-fit hole (Ø3.0 nominal, 2.95 to 3.05; the catalogue's press-fit hole), all other knuckle holes are 0.2 clearance, so the pin turns with leaf A and leaf B turns on it. At least 14.0 mm of press engagement (about a third of the 40 mm pin, derived; the catalogue `min_engagement` is only 4.5). | The owner gives a clearance only; with clearance everywhere the pin would fall out. Uncertainty **medium**: the owner may intend retention by another means (end caps, a bent pin); then L1.4 changes. Confirm. |
| **A4** | What does "25 × 40" include? | The leaf's plan bounding box at the flat pose, barrel included: X extent 25.0 (± 0.3), Y extent 40.0 (± 0.2). The 40 side is along the pin. | The pin is 40 long, so the knuckle stack is 40. Uncertainty low. |
| **A5** | Leaf thickness | 8.4 to 10.0. | The insert hole depth is 7.2 (`heatset_m3`); 8.4 = 7.2 + 1.2 of floor (three layers) is the lower limit, while the insert check itself needs a floor of at least 1.0 (L3.5.1.2). Uncertainty low. |
| **A6** | Insert data | OD 4.6, length 5.7, printed hole 3.9 to 4.1, depth 7.2, boss OD 7.0, edge distance 3.0. | `heatset_m3/part.json` (supplier tables). Uncertainty medium; measure the owner's inserts. |
| **A7** | Mounting and stops | The leaves are screwed to flat surfaces with M3 bolts through the insert holes from the mounting side. No hard stop at 0 or 180 is required. | Not stated. Uncertainty medium. |
| **A8** | Pin | Steel dowel Ø3.0 h8, 40.0 long, not printed. | `dowel_pin_generic` (ISO 2338). |
| A9 | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed, no supports; round holes up to Ø12 are not counted as overhangs. | Common printer. |
| A10 | Axis height | The pin axis lies slightly above the plates' outer face so that the folded plates clear each other: with the plate thickness t, the fold gap is twice the axis height above the face. The gap is required to be 0.30 to 0.60 (L3.7.2.1). | Derived from the 0.3 mm clearance of A2. Uncertainty low. |
| A11 | Knuckle count | Any odd number from 3 up that satisfies L1.2 and L1.4 (in practice 3 or 5: seven equal knuckles leave only 10.9 of press engagement). | Not stated. |
| A12 | Mounting surfaces | Not modelled. The leaves are screwed to flat surfaces that stop at abs(X) >= 4.8 around the hinge; the swing envelope dips to Z = −1.1 below the mounting plane inside that gap. | Not stated. Uncertainty low. |

## 4. Fixed decisions (a choice was ambiguous; this is the one graded)

- **FD1 Which leaf is A.** The leaf that owns the knuckle at the Y = 0 end, and by the odd count also the one at Y = 40. A's end knuckles are the press-fit knuckles.
- **FD2 Delivered pose.** The flat pose (θ = 180°). The grader generates every other pose.
- **FD3 Sampling.** θ = 0, 5, …, 180 (37 poses). A design that is collision-free at these poses is taken as collision-free throughout.
- **FD4 Angle convention and rotation direction.** As in section 1. B swings through +Z.
- **FD5 Hole classes.** A knuckle hole is "press" if its diameter is below 3.1, "clearance" otherwise. Leaf A's two end knuckles must be press; every other knuckle must be clearance.
- **FD6 Plate thickness** is measured mounting face to outer face on the plate, away from the barrels, notches and holes.

## 5. Requirements tree

### L1.1 Two printed leaves, 25 × 40 in plan, 8.4 to 10.0 thick, flat mounting face

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | Each leaf is one manifold body. | analysis | shells = 1 per STL (Manifold `decompose()`); manifold3d NoError | 3 | G1 |
| L3.1.1.1 | Shell count and manifold status per leaf. | analysis | 1 and NoError for both | 3 | G1 |
| L2.1.2 | Plan size (A4) and thickness (A5). | inspection | X extent 25.0 ± 0.3, Y extent 40.0 ± 0.2 per leaf (flat pose); thickness 8.4 to 10.0 | 3 | |
| L3.1.2.1 | Leaf plan extents. | inspection | as L2.1.2, both leaves | 3 | G5 |
| L3.1.2.2 | Plate thickness (FD6). | inspection | 8.4 ≤ t ≤ 10.0 | 2 | |
| L2.1.3 | The mounting face is flat. | inspection | the largest flat face on Z = 0: planarity (max − min Z) ≤ 0.2 | 2 | |
| L3.1.3.1 | Mounting-face planarity. | inspection | ≤ 0.2 for both leaves | 2 | |

### L1.2 Alternate knuckles along the pin axis

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | An odd number of at least 3 knuckles that alternate between the leaves, outermost belonging to A. | inspection | total count odd ≥ 3; adjacent knuckles belong to different leaves; knuckles at Y = 0 and Y = 40 are A's; each knuckle ≥ 5.0 long along Y | 3 | |
| L3.2.1.1 | Count and alternation. | inspection | as L2.2.1 | 3 | |
| L3.2.1.2 | Knuckle length. | inspection | each ≥ 5.0 | 2 | |
| L2.2.2 | Axial gaps and flush outer faces. | inspection | gap between neighbouring knuckle faces 0.30 to 0.40; the stack spans Y 0 to 40.0 ± 0.2 | 3 | |
| L3.2.2.1 | Axial gaps. | inspection | every gap ∈ [0.30, 0.40] | 3 | |
| L3.2.2.2 | Stack length and flush ends. | inspection | 39.8 ≤ length ≤ 40.2 | 2 | |

### L1.3 One common pin axis, clearance holes in the turning leaf, enough wall

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | All knuckle holes are coaxial. | inspection | centre of each hole (inscribed circle, mid-length slice) within 0.10 of the least-squares line through all of them | 3 | G3 |
| L3.3.1.1 | Hole coaxiality. | inspection | ≤ 0.10 for every knuckle | 3 | G3 |
| L2.3.2 | Turning-leaf holes are 0.2 larger than the pin (A2). | inspection | every clearance hole (FD5) Ø ∈ [3.15, 3.30] | 3 | |
| L3.3.2.1 | Clearance hole diameters. | inspection | 3.15 ≤ Ø ≤ 3.30 | 3 | |
| L2.3.3 | Wall round each hole. | inspection | barrel wall (outer radius − hole radius, minimum over angle) ≥ 2.0 | 2 | |
| L3.3.3.1 | Barrel wall. | inspection | ≥ 2.0 for every knuckle (sketch: 2.9) | 2 | |

### L1.4 The pin is held by a press fit in the other leaf's outer knuckles

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | A's end knuckles press the pin (A3, FD5). | inspection | the holes in A's two outer knuckles have Ø 2.95 to 3.05; their lengths add to at least 14.0 | 3 | |
| L3.4.1.1 | Press-fit hole diameter. | inspection | 2.95 ≤ Ø ≤ 3.05 | 3 | |
| L3.4.1.2 | Press engagement length. | inspection | ≥ 14.0 (sketch: 15.5) | 2 | |
| L2.4.2 | Leaf B never presses the pin. | inspection | every hole in B is clearance (FD5) | 2 | |
| L3.4.2.1 | B holes. | inspection | all Ø ≥ 3.15 | 2 | |
| L2.4.3 | The pin ends are flush. | inspection | pin end faces within 0.3 of Y = 0 and Y = 40 when the pin is seated (grader-placed, centred on the stack) | 1 | |
| L3.4.3.1 | Pin end flushness. | inspection | stack length within 40.0 ± 0.3 (the pin is 40.0) | 1 | |

### L1.5 Two M3 heat-set inserts per leaf

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Insert hole size (A6). | inspection | Ø 3.9 to 4.1; depth from the mounting face ≥ 7.2 and ≤ thickness − 1.0 | 3 | G4 |
| L3.5.1.1 | Insert hole diameter. | inspection | 3.9 ≤ Ø ≤ 4.1 for all four | 3 | G4 |
| L3.5.1.2 | Insert hole depth. | inspection | 7.2 ≤ depth ≤ t − 1.0 | 2 | |
| L2.5.2 | Insert holes are square and well placed. | inspection | axis within 1.0° of the mounting-face normal; wall to any outer edge, notch, barrel or other hole ≥ 3.0; the two holes of a leaf are at least 15.0 apart and centred on the leaf's mid-length within 0.5 | 2 | |
| L3.5.2.1 | Squareness. | inspection | ≤ 1.0° | 2 | |
| L3.5.2.2 | Wall round the insert hole. | inspection | ≥ 3.0 (sketch: 5.7 to the plate notch edge, 6.0 to the free edge) | 2 | |
| L3.5.2.3 | Spacing and symmetry. | inspection | spacing ≥ 15.0; midpoint Y = 20.0 ± 0.5 | 1 | |
| L2.5.3 | The insert seats in its hole. | analysis | M-INSERT-k top within 0.5 of the mounting face; radial overlap with the printed hole ≤ 0.35 (designed contact); no penetration anywhere else | 2 | |
| L3.5.3.1 | Insert seating. | analysis | as L2.5.3 | 2 | |

### L1.6 The whole swing is collision-free with 0.30 mm clearance

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | At every sampled angle (FD3) the leaves are apart. | analysis | for θ = 0, 5, …, 180: A ∩ LEAF-B(θ) ≤ 0.01 mm³ and minimum distance ≥ 0.30 | 3 | G2 |
| L3.6.1.1 | No intersection at any angle. | analysis | ≤ 0.01 mm³ at all 37 poses | 3 | G2 |
| L3.6.1.2 | Minimum distance over the swing. | analysis | ≥ 0.30 (− ε) at all 37 poses; the angle and place of the minimum are reported | 3 | G2 |
| L2.6.2 | The turning leaf stays clear of the pin. | analysis | clear_of(leaf B, M-PIN, 0.05) | 3 | |
| L3.6.2.1 | B vs pin. | analysis | d ≥ 0.05 (sketch: 0.10) | 3 | |

### L1.7 Flat and folded poses

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | At 180° the mounting faces are one plane. | analysis | the mounting-face planes of A and B (best fit) differ in Z by ≤ 0.2 and in angle ≤ 0.5° | 2 | |
| L3.7.1.1 | Flat pose coplanarity. | analysis | ≤ 0.2 and ≤ 0.5° | 2 | |
| L2.7.2 | At 0° the leaves fold face to face. | analysis | the mounting faces are parallel within 1.0°; the distance between the two plates' facing faces is 0.30 to 0.60 (A10) | 2 | |
| L3.7.2.1 | Folded plate gap. | analysis | 0.30 ≤ gap ≤ 0.60 | 2 | |
| L3.7.2.2 | Folded parallelism. | analysis | ≤ 1.0° | 1 | |

### L1.8 Size

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Folded and flat envelopes. | inspection | folded (θ = 0): ≤ 30.0 × 41.0 × 20.0 (X × Y × Z); flat (θ = 180): ≤ 45.0 × 41.0 × 15.0 | 1 | |
| L3.8.1.1 | Folded bounding box. | inspection | as L2.8.1 | 1 | |
| L3.8.1.2 | Flat bounding box. | inspection | as L2.8.1 | 1 | |

### L1.9 Each leaf prints without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | A print orientation is declared and the leaf prints without supports in it. | analysis | `layout.json` gives a unit build vector per leaf; faces with n·build < −cos 45° (patch > 1 mm²) = 0, apart from round holes up to Ø12 and bridges up to 15.0 | 3 | |
| L3.9.1.1 | Orientation declared. | inspection | present, unit length ± 0.01, for both leaves | 2 | |
| L3.9.1.2 | Overhang scan. | analysis | 0 offending patches per leaf | 3 | |
| L2.9.2 | Bed contact. | analysis | area of faces with n = −build at the bed ≥ 50% of the plan bounding box | 2 | |
| L3.9.2.1 | Bed contact. | analysis | ≥ 50% (sketch: A 82%, B 75%) | 2 | |
| L2.9.3 | No thin feature. | analysis | local thickness ≥ 0.8 everywhere (barrel wall rule L3.3.3.1 is stricter) | 1 | |
| L3.9.3.1 | Thin features. | analysis | ≥ 0.8 | 1 | |

### L1.10 The pin goes in and bolts reach the inserts, folded and flat

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | The pin can be pushed in along its axis. | test | clear_of(A ∪ B, V-PIN-IN, 0.0) except the press-fit knuckles: penetration only inside leaf A's press holes, radial depth ≤ 0.05 (+ ε); none against B | 3 | G3 |
| L3.10.1.1 | Pin insertion path. | test | penetration outside the press zones ≤ 0.01 mm³; radial overlap in press holes ≤ 0.05 | 3 | G3 |
| L2.10.2 | A bolt reaches every insert from outside. | test | clear_of(A ∪ B, V-BOLT-k, 0.0) for all four columns at θ = 180 and at θ = 0 | 2 | |
| L3.10.2.1 | Bolt columns clear. | test | d ≥ 0 at both poses | 2 | |

### L1.11 The package says what was built and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | The package holds `leaf_a.stl`, `leaf_b.stl` (flat pose, mm), the `.scad` source, `layout.json` (pin axis as point + direction, which leaf is A, the four insert axes with depths, build vectors) and the agent's own swing report. | inspection | all present and readable; each STL's largest axis 20 to 60 | 3 | G0 |
| L3.11.1.1 | Files present and parse; units. | inspection | true | 3 | G0 |
| L3.11.1.2 | Declared axes match the STLs. | inspection | pin axis within 0.10 and 0.5°; insert axes within 0.2 and 1.0° | 2 | |
| L2.11.2 | The agent's swing report agrees with the grader. | analysis | the agent's minimum distance over the swing and the angle where it occurs: \|d_agent − d_judge\| ≤ 0.05 | 1 | |
| L3.11.2.1 | Self-report vs judge. | analysis | within 0.05 | 1 | |

## 6. Gates and counts

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.11.1.1), **G1** both
leaves manifold single bodies (L3.1.1.1), **G2** collision-free swing with clearance (L3.6.1.1, L3.6.1.2),
**G3** pin axis and pin path (L3.3.1.1, L3.10.1.1), **G4** insert holes (L3.5.1.1), **G5** leaf plan
size (L3.1.2.1). Classes: WRONG (a gate fails), MINOR (no gate fails, a weight-3 L3 fails), CORRECT
(all weight-3 pass), MEETS (CORRECT and every L3 of weight 1 and 2 passes).

| Level | Count |
|---|---|
| L1 | 11 |
| L2 | 26 |
| L3 | 38 |

## 7. Feasibility (a design exists)

Built and checked with `manifold3d` (each leaf one shell, NoError; leaf A volume 7 513 mm³, leaf B
6 697 mm³). Numbers in mm, hinge frame (flat pose):

| Feature | Value |
|---|---|
| plate | thickness t = 8.4, Z 0 to 8.4 |
| barrel | R = 4.5 around the pin axis, axis at X 0, Z 8.55 (0.15 above the plate's outer face), so the barrel top is at Z 13.05 |
| plan | leaf A: X −4.5 to 20.5 (25.0) × Y 0 to 40 (40.0); leaf B mirrored: X −20.5 to 4.5 |
| knuckles | 5, each 7.76 long, 4 gaps of 0.30: A at Y 0–7.76, 16.12–23.88, 32.24–40.0; B at Y 8.06–15.82, 24.18–31.94 |
| plate notches | each leaf's plate is cut away for \|X\| < 4.8 (barrel R + 0.30) everywhere except at its own knuckles |
| pin holes | A end knuckles Ø3.0 (press; 15.52 mm engaged), A middle knuckle and both B knuckles Ø3.2; barrel wall 2.9 |
| inserts | A at X 12.5, Y 10 and 30; B at X −12.5, Y 10 and 30; Ø4.0, depth 7.2 from Z 0 (floor 1.2); 6.0 to the free edge, 6.0 to the barrel |
| swing | A fixed, B rotated about the pin axis through +Z in 5° steps: intersection 0.0 mm³ at all 37 poses; minimum distance 0.30 mm at all of them |
| flat / folded | flat bounding box 41.0 × 40.0 × 13.05 (≤ 45 × 41 × 15); folded 25.0 × 40.0 × 17.1 (≤ 30 × 41 × 20); folded plate gap 2 × 0.15 = 0.30 |
| print | each leaf mounting face down: overhang scan finds only the round pin and insert holes; bed contact A 819 mm² = 82%, B 747 mm² = 75% of the 25 × 40 plan |

## 8. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 | Method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Two leaves, size | L2.1.1–L2.1.3 | L3.1.1.1, L3.1.2.1–2, L3.1.3.1 | L1.1 | inspection | "two printed hinge leaves", "each leaf 25 x 40 mm" |
| L1.2 | Knuckles | L2.2.1–L2.2.2 | L3.2.1.1–2, L3.2.2.1–2 | L1.2 | inspection | "0.3 mm clearance between knuckles" |
| L1.3 | Pin axis and fit | L2.3.1–L2.3.3 | L3.3.1.1, L3.3.2.1, L3.3.3.1 | L1.3 | inspection | "3 mm steel pin", "0.2 mm on the pin" |
| L1.4 | Pin held | L2.4.1–L2.4.3 | L3.4.1.1–2, L3.4.2.1, L3.4.3.1 | L1.4 | inspection | "joined by a 3 mm steel pin, 40 mm long" (A3) |
| L1.5 | Inserts | L2.5.1–L2.5.3 | L3.5.1.1–2, L3.5.2.1–3, L3.5.3.1 | L1.5 | inspection | "two heat-set M3 inserts" |
| L1.6 | Swing | L2.6.1–L2.6.2 | L3.6.1.1–2, L3.6.2.1 | L1.6 | analysis | "must not collide through the whole swing" |
| L1.7 | Flat and folded | L2.7.1–L2.7.2 | L3.7.1.1, L3.7.2.1–2 | L1.7 | analysis | "opens 0 to 180 degrees" |
| L1.8 | Size | L2.8.1 | L3.8.1.1–2 | L1.8 | inspection | implied |
| L1.9 | Printable | L2.9.1–L2.9.3 | L3.9.1.1–2, L3.9.2.1, L3.9.3.1 | L1.9 | analysis | implied (FDM) |
| L1.10 | Assembly | L2.10.1–L2.10.2 | L3.10.1.1, L3.10.2.1 | L1.10 | test | "joined by a pin", "heat-set M3 inserts" |
| L1.11 | Evidence | L2.11.1–L2.11.2 | L3.11.1.1–2, L3.11.2.1 | L1.11 | inspection | needed by the judge |

## 9. Grading (design-specific; used because `generalize/rubric.md` is missing)

- **Verdict:** WRONG (any gate G0 to G5 fails), MINOR (no gate fails, some weight-3 L3 fails), CORRECT
  (every weight-3 L3 passes), MEETS (CORRECT and every L3 of weight 1 and 2 passes). UNVERIFIED counts as
  FAIL. Report also the weighted score Σ(weight × pass)/Σ(weight) and the worst normalised margin among
  weight-3 L3s.
- **Precedence:** numbers in this document beat `part.json`. Never relax a criterion or round in the
  design's favour beyond ε.
- **WHERE a defect is:** one entry per failed or UNVERIFIED L3, gates first then weight 3, 2, 1, with:
  `req` (L3 with L2 and L1), `status`, `body` (`leaf_a`, `leaf_b`, `both` or `layout`), `feature` (named by
  function, for example "knuckle 3 of leaf A" or "insert hole 2 of leaf B"), `face`, `location` (point or bounding box in
  the hinge frame, and θ for swing defects), `measured` / `limit` / `margin`, `reference` (M-PIN, LEAF-B(θ) and so on),
  `needed` (the target as numbers, for example "axial gap must be 0.30 to 0.40, now 0.12 between knuckles 1 and 2") and
  `evidence` (the saved intersection or closest-points solid). `needed` never says how to build it.
- **Measured-values table (always filled in):** leaf plan extents and thickness; knuckle count, lengths, gaps; hole Ø per
  knuckle; coaxiality; barrel wall; press engagement; insert Ø, depth, squareness, wall; minimum distance over the swing and
  its θ; intersection volumes; B-to-pin distance; flat coplanarity; folded gap and parallelism; bounding boxes; overhang
  patches; bed contact; shells; self-report agreement.

## Audit

Adversarial audit against `benchmarks/enclosure/rubric.md` (the generalize rubric is absent), the catalogue and the L1 text in
`design.json`. The feasibility sketch of section 7 was rebuilt in `manifold3d` (both leaves, the pin, all 37 poses) and
re-measured; `dowel_pin_generic`, `heatset_m3` and `bolt_m3_iso4762` load through `parts.Catalog` (they need `length` from the
request). L1 11 (E1-01: 12), L2 26 (45), L3 38 (69): a two-part mechanism, simpler than the enclosure; counts match section 6.

| # | Finding | Fix |
|---|---|---|
| 1 | Re-measured and confirmed: leaf A 7 513 mm³ and leaf B 6 697 mm³, one shell each (when the notched plate and its own knuckle blocks overlap, as a CAD union does; blocks that only touch faces come out as three shells in `decompose()`, which is worth knowing when writing the source); intersection 0.0 mm³ and minimum distance 0.300 at all 37 poses; B to pin 0.0999; A and pin penetration 0; flat box 41.0 x 40.0 x 13.05, folded 25.0 x 40.0 x 17.1; bed contact A 819.4 and B 747.3 mm²; the only downward faces are the pin holes and the Ø4 insert-hole ceilings (exempt round holes). | None needed. |
| 2 | A5 said the insert hole needs "at least 1.2 of floor" but L1.5 / L2.5.1 / L3.5.1.2 require a floor of at least 1.0 (depth <= t − 1.0). | A5 now reads: thickness 8.4 = 7.2 depth + 1.2 floor (three layers) is the lower limit of L1.1; the insert check itself needs 1.0. |
| 3 | Section 7 "6.0 to the barrel" for the insert-hole wall: the nearest material of the same body next to the hole at X 12.5 is the plate notch edge at X 4.8, 5.7 away from the hole edge (6.0 only to the barrel surface at X 4.5). | Corrected to 5.7 (notch edge) and 6.0 (free edge); still >= 3.0. |
| 4 | L3.4.1.2 asks for 14.0 of press engagement while the catalogue `dowel_pin_generic` has `min_engagement` 4.5. The 14.0 is not derived anywhere. | Derived in A3: the pin is retained by about one third of its length (40 / 3 = 13.3, rounded up to 14.0); a design with seven or more knuckles of 5.0 to 5.5 cannot reach it with two end knuckles, so the knuckle count is effectively 3 or 5 (7 equal knuckles give 10.9). |
| 5 | Numbers the judge uses that the agent was never told: mounting-face flatness 0.2; insert squareness 1 degree; insert spacing 15.0; hole depth <= t − 1.0; symmetry 0.5. | Added to the L1 texts in `design.json` (ids and count unchanged). |

Observation (not graded, new A12): the swing envelope of leaf B dips to Z = −1.10 (the corner of its knuckle block below the axis swings under the mounting plane) and leaf A's knuckle blocks reach X = −4.5; the surfaces the leaves are screwed to must stop at abs(X) >= 4.8 around the hinge or the swing needs a bevel. Exactly the same limit (0.300) governs the folded plate gap, the axial knuckle gaps and the plate-notch clearance, so the sketch has no margin on L3.6.1.2 and L3.7.2.1; a design with 0.30 to 0.40 everywhere passes.
