# G40 Pico mounting-hole drill guide: requirements (L1 / L2 / L3)

Design G40 is a printed drilling jig. It is graded on the position of four guide holes
relative to its own edge locator (hole centres to within 0.1 mm), on a recess that lets the owner
lay a Pico 2 in the guide to check the position, and on the usual printability and evidence
rows. It is a training design for the generalisation set: nothing here is specific to the
enclosure benchmark, but the method (declared layout, reference models built from the catalogue,
interference and clearance against swept envelopes, numbers only in the request and the
catalogue) is the same.

**Request (as given to the agent):** I need a flat guide for drilling the Raspberry Pi Pico 2 mounting-hole pattern into a panel. The Pico 2's four mounting holes are 2.1 mm and sit on a 47.0 x 11.4 mm pattern (47.0 mm apart along the long side, 11.4 mm across). The guide has a 2.3 mm guide hole for each of the four, so a 2.1 mm drill passes through with a little play. It must locate on a straight panel edge: I hold the guide against the edge of the panel, which is a flat sheet 3 mm thick, and drill through it. The nearest row of holes must be 10 mm from that edge; I set the position along the edge by eye, so only the distance from the edge and the rotation matter. The top face has a recess in the shape of the Pico's outline so I can lay a Pico in it and check the position before I drill. The hole centres must hit the pattern to within 0.1 mm. It is printed on an FDM printer in PLA.

**Plan brief (verbatim):** "A flat guide for drilling the Pico 2 mounting-hole pattern into a panel: two or four 2.1 mm holes 47.0 x 11.4 mm apart with guide hole 2.3 mm. The guide locates on a panel edge and has a recess for the Pico outline so I can check position. Hole centres must hit the pattern to within 0.1 mm."

**Split:** train. **Family:** fixture_adapter. **Capabilities exercised:** drill_guide, datum_placement, bolt_pattern, pocket_fit.

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check Python can run on the delivered STLs. Every L3
row has a method (inspection, analysis, demonstration, test, human; see `design.json`), a pass/fail
criterion with a number and a tolerance, a weight (3 = critical, 2 = major, 1 = minor) and a gate
mark where a failure makes the design WRONG. Every number that comes from an assumption (section
3.1) is provisional until Robin confirms it. No number here may appear in agent logic: target
numbers live in the request text, in `part.json` catalogue data and in this file only.
Where this file and a `part.json` disagree, this file wins (section 7.3).

---

## 1. Frames, tolerances and the checks

### 1.1 Frames

- **Guide frame (all tables below):** X along the panel edge, Y across the panel (into the panel
  is +Y), Z up. The panel's top face is Z = 0, its edge face is the plane Y = 0 and the panel
  occupies Y ≥ 0, Z from −3.0 to 0 (A2). The guide's plate sits on the panel top (Z ≥ 0), its
  fence hangs down on the panel edge (Y < 0). X = 0 is the centre of the hole pattern. A guide
  delivered mirrored or rotated is normalised into this frame before grading (7.2 step 3):
  the fence face is Y = 0, the fence points down, the plate is above Z = 0; that is never penalised.
- **Pico frame:** the catalogue `rpi_pico2` frame (origin at the PCB min corner, PCB bottom Z = 0, USB end at −X). When the Pico lies in the recess it is translated so its `HOLE` datum pattern is centred on the guide's hole pattern; it is never rotated.

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered meshes, never by eye.

| Quantity | Measurement tolerance ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within ε (e.g. "≥ 0.50" passes at 0.48) |
| angle | 0.5° | same |
| interference volume | 0.01 mm³ | "no interference" means intersection volume ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the hole's section (what a screw or pin sees) | |
| boss / pin / spigot OD | smallest enclosing circle of the section | |

Where a criterion is written "nominal ± t", t is the design tolerance and ε is added to it. A mesh
is tessellated: a circle of nominal diameter D measures D·cos(π/N) at worst, so compare diameters
with ε = 0.05 for holes and bosses (the grader fits circles to the section, it does not read vertices).

### 1.3 The checks and designed contact

- **`clear_of(bodies, volume, clearance)`**: the minimum Euclidean distance between every printed
  body in `bodies` and `volume` is ≥ `clearance`. Reported value: the signed minimum distance d
  (negative = penetration; the penetration volume is reported too). Pass: d ≥ clearance − ε.
- **`inside(volume, solids, clearance)`**: `volume` lies entirely inside the convex hull of `solids`
  (or inside the named cavity) and every point of it is ≥ `clearance` from the boundary. Pass:
  d ≥ clearance − ε.
- **`sweep(model, path, bodies)`**: the model is moved along `path` in steps of at most 1.0 mm
  (and the swept union is also tested); pass when the penetration volume with `bodies` stays
  ≤ 0.01 mm³ at every step.

`bodies` is **ALL** (every printed body, closed or in the assembly pose), or one named body. A
design never builds or edits the reference volumes: the grader generates them independently from
the catalogue and the design's declared layout. The agent may generate the same volumes for its
own checks, but its copies are not trusted for grading.

**Designed contact for this design (is never interference).** Parts that are meant to touch are excluded from every interference and clearance check; for these pairs only penetration counts (intersection volume above 0.01 mm³; a distance of zero is a pass):

- the guide plate's underside resting on the panel's top face (M-PANEL)
- the fence's inner face against the panel's edge face (M-PANEL)
- the Pico's underside resting on the recess floor (M-PICO in the recess)

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` (`benchmarks/enclosure/parts/rpi_pico2/part.json`; the generic box `benchmarks/generalize/parts/generic_box/part.json` for the panel). These are the only places target-specific part numbers may live.
- **envelope**: a keep-out or access volume generated by Python from datums (offsets, sweeps, columns). Never drawn by hand.
- **computed**: derived from the delivered STL (hole axes, recess outline, fence face).

### 2.2 Reference models (M-)

| Name | What | Source | Size and default position (guide frame, mm) | Datums |
|---|---|---|---|---|
| **M-PICO** | Raspberry Pi Pico 2 (bare board, no headers, A3) | catalogue `rpi_pico2` | PCB 51.0 × 21.0 × 1.0; receptacle 5.5 (X) × 8.0 (Y) × 2.8 (Z) on top, overhanging the PCB's −X edge by 1.3, its underside 1.0 above the PCB bottom; four holes Ø2.1 at 2.0 from each short edge and 4.8 from each long edge (pattern 47.0 × 11.4). Default pose: PCB centre at X 0, Y = (row-1 Y) + 5.7 = 15.7, PCB bottom on the recess floor. | `PICO_HOLE_1..4` (= the `HOLE` axis list, items 1 to 4), `PCB_BOTTOM`, `USB_AXIS` |
| **M-PANEL** | flat panel sheet | catalogue `generic_box` | X −75 to 75, Y 0 to 100, Z −3.0 to 0 (A2) | `TOP` (plane Z = 0), `FACE_MY` (edge plane Y = 0) |
| **M-DRILL-k** (k = 1..4) | 2.1 mm twist drill, as a cylinder | envelope | Ø2.1 along the declared hole axis k, from Z = +20 down to Z = −10 | hole axis |

### 2.3 Envelopes and computed volumes

| Name | What | Definition |
|---|---|---|
| **P-IDEAL** | the ideal hole pattern | four points at (X0 ± 23.5, Y1) and (X0 ± 23.5, Y1 + 11.4), with Y1 = 10.0 (FD3) and X0 the best-fit translation along X (free: the guide has no X stop, FD2). Pattern pitches come from `HOLE` of `rpi_pico2` (47.0 and 11.4). |
| **V-RECESS** | the recess actually present in the plate's top face | computed: the top face region below Z = 4.0 that is open to the top, as a connected region |
| **V-HOLE-k** | guide hole k | computed: the through hole in the plate at the declared axis, its largest inscribed circle per slice |
| **V-FENCE-FACE** | the fence face that touches the panel edge | computed: the largest planar face with normal +Y at Y ≈ 0 on the fence |
| **V-CHUCK-k** | drill chuck access above hole k | envelope: Ø8.0 column on hole axis k from the plate top (Z = 4.0) to Z = 40 |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-PICO | units and PCB size | 51.0 × 21.0 ± 0.2 mm |
| R2 | M-PICO | hole pattern | Ø2.1 ± 0.1; pitch 47.0 × 11.4 ± 0.1 |
| R3 | M-PICO | orientation | receptacle at −X, components on +Z |
| R4 | M-PANEL | size and datums | Z −3.0 to 0; `FACE_MY` at Y = 0 |
| R5 | M-PICO in the recess | the Pico collides with nothing it should not touch (default pose) | intersection with the guide ≤ 0.01 mm³ |

**Seating rule.** The guide is placed on M-PANEL by the declared pose in `layout.json`
(translation along X only). The grader verifies: the plate underside is on Z = 0 (≤ 0.05) and the fence face is on Y = 0 (≤ 0.05). If the declaration is missing or fails, the guide is seated by bringing its lowest plate-underside plane to Z = 0 and its fence face to Y = 0; the hole checks are then made in that pose.
---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (with uncertainty)

Each line gives the value chosen and why. Robin may correct any of them; a correction changes this file and the catalogue, and earlier scores become stale.

| # | Question | Value chosen | Why and uncertainty |
|---|---|---|---|
| A1 | Hole pattern? | Pico 2: four holes Ø2.1 at 2.0 mm from each short edge and 4.8 mm from each long edge (47.0 × 11.4); PCB 51.0 × 21.0 × 1.0. | Raspberry Pi Pico 2 datasheet and the catalogue part. Uncertainty ±0.1 on the pattern; measure the owner's board. The pattern pitches are in the request. |
| A2 | Panel? | A flat sheet 3.0 mm thick, any width and length, with one straight edge; the guide rests on its top face. | Not given. Typical electronics panel / plywood / acrylic, 2 to 5 mm; uncertainty ±1.5. The fence is 4.0 deep, so it covers any panel up to 4.0. |
| A3 | How does the Pico lie in the recess? | Bare board, no headers, components up, PCB underside on the recess floor. | The recess is a position check, not a mount. With headers soldered under the board the recess would need pockets for the pins (not graded). The USB receptacle then overhangs the plate with 0.2 clearance (receptacle underside 1.0 above the PCB bottom, plate top 0.8 above the floor). |
| A4 | Clearance between the Pico outline and the recess wall? | 0.2 mm per side (recess 51.4 × 21.4). | FDM prints a pocket 0.1 to 0.3 small; 0.2 per side keeps the Pico free yet within 0.2 of true. Uncertainty ±0.1. |
| A5 | Recess depth? | 0.8 mm, less than the 1.0 mm PCB thickness. | The Pico's top stands proud by 0.2 so a finger or a straight edge can sit it flat, and the receptacle (underside 1.0 above PCB bottom) clears the plate by 0.2. Uncertainty ±0.1. |
| A6 | Guide plate thickness? | 4.0 mm (recess floor leaves 3.2 mm of guide length; band 2.0 to 4.0). | The 0.2 mm diametral play over a 3.2 mm guide allows a drill tilt of atan(0.2 / 3.2) = 3.6° (2.9° over 4.0); at the plate underside, where the drill enters the panel, the centre error is only the 0.1 radial play, so tilt does not add to L2.8.2. Uncertainty ±0.5. The upper limit 4.0 follows from the plate (4.0 ± 0.3) less the recess (0.8). |
| A7 | Drill? | 2.1 mm twist drill, held in a chuck of at most Ø8.0 above the plate. | The request's 2.1 mm hole. The 0.1 mm radial play equals the 0.1 mm position tolerance, so guide-hole centre error counts one to one. |
| A8 | Which edge does the guide find? | One straight edge. The guide fixes Y (distance to the edge) and the rotation about Z; X is set by eye using the recess. | One edge cannot fix X. The owner positions the Pico recess visually along the panel. A second fence for X is not graded (FD2). |
| A9 | Printing? | FDM, PLA, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. A downward-facing step of at most 1.0 mm is not an overhang. | Common printers. The step exemption covers the recess edge when the guide is printed on its side (see 6). Uncertainty ±0.3 on the exemption. |
| A10 | Hole fidelity? | The grader measures the hole axis and diameter on the delivered STL. A design may compensate for printing shrinkage in the model; the numbers on the STL are what count. | The request ties accuracy to hole centres; shrinkage compensation is the designer's job. |

### 3.2 Fixed decisions (one choice, no alternatives graded)

| # | Ambiguity | Decision | Reason |
|---|---|---|---|
| FD1 | Two or four holes? | **Four.** All four Pico mounting holes are drilled (Ø2.3 guide holes on the full 47.0 × 11.4 pattern). | Four fix the Pico against rotation; a two-hole guide would need the owner to fix rotation by eye. The request says the Pico's four holes. |
| FD2 | How does it locate? | A **fence** hanging down from the plate's front edge. Its inner face butts the panel edge. The fence runs the whole plate length along X (62.0 ± 0.5). X is free (A8). | One straight edge gives Y and rotation. The Pico's long axis (47.0) is parallel to the edge. |
| FD3 | Where are the holes relative to the edge? | Nearest hole row at **Y = 10.0 ± 0.1** from the fence inner face; the second row at 21.4. Pattern centred on the plate in X (± 0.5). | A free choice that the brief leaves open; one number so the grader can test it. 10.0 leaves 8.95 mm of panel between the drilled hole and the panel edge. |
| FD4 | Plate and fence sizes? | Plate 62.0 × 35.0 × 4.0 (X × Y × Z) from Y = −3.0 to Y = 32.0, fence 3.0 thick (Y −3.0 to 0) and 4.0 deep (Z −4.0 to 0). Bands in the L3 rows are ± the stated tolerance around these. | Concrete numbers so the feasibility sketch is exact. |
| FD5 | Print orientation? | The guide is printed on its side: fence outer face (Y = −3.0) on the bed, plate rising from it. The orientation is declared in `layout.json`. | The fence hangs below the plate, so any upright orientation needs supports under the plate; on its side nothing overhangs but the recess's top edge, a 0.8 step (A9). |

---

## 4. Requirements tree

### L1.1 Four guide holes on the Pico 2 pattern

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The guide has exactly four through holes that lie on a rectangle 47.0 × 11.4. | inspection | count = 4; the pitches between hole axes are 47.0 ± 0.1 (X) and 11.4 ± 0.1 (Y) | 3 | |
| L3.1.1.1 | Number of guide holes through the plate (excluding the recess). | inspection | count = 4 | 3 | G2 |
| L3.1.1.2 | Hole-axis pitch along X and along Y (all four edge distances). | inspection | 47.0 ± 0.10 and 11.4 ± 0.10 for every edge of the rectangle | 3 | G2 |
| L3.1.1.3 | Hole axes are parallel to Z. | inspection | each axis within 0.5° of Z | 2 |  |
| L2.1.2 | Every hole axis is within 0.1 of its ideal position in the pattern fixed to the fence. | analysis | after the best-fit translation along X, max \|axis − P-IDEAL\| ≤ 0.10 | 3 | |
| L3.1.2.1 | Residual of each hole axis to P-IDEAL (X translation removed). | analysis | ≤ 0.10 for all four | 3 | G2 |
| L3.1.2.2 | Rotation of the hole rows against the fence face (Z axis). | analysis | rows parallel to the fence face within 0.10° | 2 |  |
| L2.1.3 | The design declares its layout: the guide's seating pose on M-PANEL and its print orientation. | inspection | `layout.json` parses, names `rpi_pico2` and `generic_box`, gives X translation and print orientation | 2 | |
| L3.1.3.1 | Layout file parses and every catalogue id exists. | inspection | true | 2 |  |

### L1.2 Guide holes that take a 2.1 mm drill

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Each guide hole is Ø2.3 and round. | inspection | largest inscribed circle 2.30 ± 0.05; ovality (max − min inscribed over a section) ≤ 0.10 | 3 | |
| L3.2.1.1 | Inscribed diameter at mid-length of each hole. | inspection | 2.30 ± 0.05 | 3 | G3 |
| L3.2.1.2 | Hole diameter at the underside and at the recess floor. | inspection | both within 2.30 ± 0.10 (no flare larger than 0.1) | 1 |  |
| L2.2.2 | Each hole is long enough to guide. | inspection | guide length (recess floor to plate underside) between 2.0 and 4.0 | 2 | |
| L3.2.2.1 | Length of every hole (ray along the axis from floor to underside). | inspection | 2.0 ≤ length ≤ 4.0 (nominal 3.2) | 2 |  |
| L2.2.3 | A 2.1 mm drill passes every hole without touching. | test | sweep(M-DRILL-k, Z from +20 to −10, guide) has penetration ≤ 0.01; clear_of(guide, M-DRILL-k, 0.05) | 3 | |
| L3.2.3.1 | Drill sweep through each hole at the declared axis. | test | penetration ≤ 0.01 mm³; d ≥ 0.05 | 3 |  |

### L1.3 Locates on a panel edge

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The fence face is flat and square to the plate underside. | inspection | flatness ≤ 0.10 over the face; angle to the plate underside 90° ± 0.5° | 3 | |
| L3.3.1.1 | Planarity of V-FENCE-FACE. | inspection | ≤ 0.10 | 3 |  |
| L3.3.1.2 | Angle between V-FENCE-FACE and the plate underside. | inspection | 90° ± 0.5° | 3 | G4 |
| L2.3.2 | The fence covers the panel edge and is long enough to seat the guide square. | inspection | fence depth below the plate underside 3.0–6.0 (nominal 4.0); fence length along X ≥ 40.0 (nominal 62.0); fence thickness ≥ 2.0 | 2 | |
| L3.3.2.1 | Fence depth, length and thickness. | inspection | depth 3.0–6.0; length ≥ 40.0; thickness ≥ 2.0 | 2 |  |
| L3.3.2.2 | Fence face and plate underside are one rigid body (one connected shell). | inspection | fence fused to the plate, one shell | 3 |  |
| L2.3.3 | The nearest hole row is 10.0 from the fence face. | inspection | 10.0 ± 0.10 measured on the delivered STL | 3 | |
| L3.3.3.1 | Distance from V-FENCE-FACE to the axis of the nearest hole row. | inspection | 10.00 ± 0.10 | 3 | G4 |
| L2.3.4 | Seated on M-PANEL the guide does not collide with it, except for the designed contact. | analysis | penetration of guide with M-PANEL ≤ 0.01 mm³; plate underside within 0.05 of Z = 0; fence face within 0.05 of Y = 0 | 2 | |
| L3.3.4.1 | Seating on the reference panel (guide in the pose of `layout.json`). | analysis | penetration ≤ 0.01; planes within 0.05 | 2 |  |

### L1.4 Recess shaped to the Pico outline

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The recess is a rectangle 51.4 × 21.4 and 0.8 deep. | inspection | 51.4 ± 0.10 × 21.4 ± 0.10; depth 0.8 ± 0.10; floor flat to 0.10 | 3 | |
| L3.4.1.1 | Recess length, width and corner radius. | inspection | 51.4 ± 0.10 and 21.4 ± 0.10; corner radius ≤ 0.6 (a larger radius cuts the catalogue board's square corner: 0.414 r > 0.28 for r > 0.68) | 3 |  |
| L3.4.1.2 | Recess depth and floor planarity. | inspection | 0.80 ± 0.10; floor flatness ≤ 0.10 | 2 |  |
| L2.4.2 | The recess is centred on the hole pattern, so a Pico laid in it puts its holes over the guide holes. | analysis | recess centre within 0.10 of the pattern centre; M-PICO in the recess: PICO_HOLE_k coaxial with hole k within 0.20 | 3 | |
| L3.4.2.1 | Recess centre against the mean of the four hole axes. | analysis | ≤ 0.10 in X and in Y | 3 |  |
| L3.4.2.2 | Hole-axis residual with M-PICO in the recess (best placement inside the recess walls). | analysis | ≤ 0.20 for all four | 2 |  |
| L2.4.3 | A Pico lies in the recess freely and its receptacle does not touch the plate. | analysis | clearance 0.1 to 0.3 per side to the recess walls; clear_of(guide, M-PICO receptacle, 0.1); penetration ≤ 0.01 | 2 | |
| L3.4.3.1 | Wall clearance around M-PICO PCB (four sides). | analysis | 0.10 ≤ c ≤ 0.30 on every side when centred | 2 |  |
| L3.4.3.2 | Receptacle of M-PICO against the plate. | analysis | d ≥ 0.10 and penetration ≤ 0.01 mm³ | 2 |  |

### L1.5 A flat, stiff plate with enough material around every feature

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The plate is 4.0 thick and flat underneath. | inspection | thickness 4.0 ± 0.3; underside flatness ≤ 0.10; plate Z extent 4.0 ± 0.3 above the underside | 3 | |
| L3.5.1.1 | Plate thickness (median over the plate away from the recess). | inspection | 4.0 ± 0.3 | 2 |  |
| L3.5.1.2 | Underside flatness over the area that rests on the panel. | inspection | ≤ 0.10 | 3 |  |
| L2.5.2 | Ligaments: recess to the plate's free edges, and the floor round each guide hole. | analysis | min ligament ≥ 3.0 from the recess to every plate edge (the fence side included); every hole edge has ≥ 1.0 of floor to the recess wall | 2 | |
| L3.5.2.1 | Minimum distance from the recess outline to the plate edge. | analysis | ≥ 3.0 (nominal 5.3, at the X ends) | 2 |  |
| L3.5.2.2 | Minimum floor ligament between a guide-hole edge and the recess wall. | analysis | ≥ 1.0 (nominal 1.05) | 2 |  |

### L1.6 Printable on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | One manifold body. | analysis | 1 shell; manifold3d accepts it | 3 | |
| L3.6.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.6.2 | No overhang steeper than 45° in the declared orientation. | analysis | 0 offending faces (area > 1 mm²), except round holes Ø ≤ 12 in vertical walls, bridges ≤ 15 and a downward step ≤ 1.0 deep (A9) | 2 | |
| L3.6.2.1 | Overhang and bridge scan. | analysis | as L2 | 2 |  |
| L3.6.2.2 | Bed contact in the declared orientation. | analysis | ≥ 50% of the plan bounding box | 1 |  |
| L2.6.3 | No feature thinner than 0.8; build volume. | analysis | min local thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 | |
| L3.6.3.1 | Thin-feature scan. | analysis | min thickness ≥ 0.8 | 1 |  |
| L3.6.3.2 | Bounding box. | inspection | ≤ 200 per axis | 1 |  |

### L1.7 Small enough to handle and to hold on a panel

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Bounding box limit. | inspection | X ≤ 70.0, Y ≤ 40.0, Z ≤ 10.0 | 1 | |
| L3.7.1.1 | Bounding box of the guide. | inspection | as L2 (nominal 62.0 × 35.0 × 8.0) | 1 |  |
| L2.7.2 | The top face stays flat: nothing rises above it. | inspection | max Z of the guide = plate top within 0.05 | 1 | |
| L3.7.2.1 | Highest point of the guide. | inspection | = plate top ± 0.05 | 1 |  |

### L1.8 A drill and chuck reach every hole

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | No material above the plate top around the holes. | analysis | clear_of(guide, V-CHUCK-k, 0.0) for k = 1..4 | 1 | |
| L3.8.1.1 | Chuck columns clear. | analysis | penetration ≤ 0.01 | 1 |  |
| L2.8.2 | The drilled holes land on the pattern relative to the panel edge. | analysis | with the guide seated, the axes of M-DRILL-k hit P-IDEAL within 0.10 + (2.3 − 2.1)/2 = 0.20 worst case; the nominal drill axis at the hole axis is within 0.10 | 3 | |
| L3.8.2.1 | Drilled-hole centre against the pattern in the panel frame. | analysis | nominal ≤ 0.10; worst case (drill touching the hole wall) ≤ 0.20 | 3 |  |

### L1.9 The delivered package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The package holds `guide.stl`, the `.scad` source, `layout.json` and the agent's report. | inspection | all present and readable | 3 | |
| L3.9.1.1 | Files present and parse; STL in mm: largest bounding-box axis within 20–200. | inspection | true | 3 | G0 |
| L3.9.1.2 | The declared seating pose verifies on M-PANEL (planes on Z = 0 and Y = 0). | analysis | ≤ 0.05 | 3 |  |
| L2.9.2 | The agent's report agrees with the judge. | analysis | for every hole position, diameter and recess number it reports: \|agent − judge\| ≤ 0.05 | 1 | |
| L3.9.2.1 | Self-report against the judge's measurements. | analysis | 100% within 0.05 | 1 |  |

---

## 5. Counts and gates

L1: 9. L2: 24. L3: 38.

Gates (a failing gate makes the design WRONG regardless of score):

- **G0** package present and readable: L3.9.1.1
- **G1** one manifold body: L3.6.1.1
- **G2** four holes on the 47.0 × 11.4 pattern within 0.1: L3.1.1.1, L3.1.1.2, L3.1.2.1
- **G3** guide hole Ø2.3 ± 0.05: L3.2.1.1
- **G4** fence face square and the nearest row at 10.0 ± 0.1: L3.3.1.2, L3.3.3.1

---

## 6. Feasibility

A concrete design exists (all values in mm, guide frame of 1.1):

- Plate: X −31.0 to 31.0, Y −3.0 to 32.0, Z 0 to 4.0. Fence: X −31.0 to 31.0, Y −3.0 to 0, Z −4.0 to 0, fused to the plate. One shell, bounding box 62.0 × 35.0 × 8.0 (within 70 × 40 × 10).
- Guide holes Ø2.3 through (Z 0 to 3.2 under the recess floor) at X = −23.5 and +23.5, Y = 10.0 and 21.4. Pitches 47.0 × 11.4 exactly; rows are parallel to the fence face Y = 0.
- Recess: X −25.7 to 25.7 (51.4), Y 5.0 to 26.4 (21.4), floor at Z 3.2 (depth 0.8). Pattern centre (0, 15.7) is the recess centre. A Pico lies in it: PCB bottom on the floor, PCB X −25.5 to 25.5, Y 5.2 to 26.2: clearance 0.2 on every side; its holes are at X ±23.5 and Y 10.0 and 21.4: coaxial with the guide holes. The receptacle underside (Z 3.2 + 1.0 = 4.2) clears the plate top (Z 4.0) by 0.2.
- Ligaments: recess to the fence-side edge 5.0 + 3.0 = 8.0 (to the fence's outer face), recess to the far edge 32.0 − 26.4 = 5.6, to the X ends 31.0 − 25.7 = 5.3; hole edge to recess wall 1.05 (nearest wall is the short wall: 25.7 − 23.5 − 1.15).
- Drill: Ø2.1 inside Ø2.3, 0.1 per side; worst-case centre error 0.1 from the hole wall.
- Print orientation: on its side, fence outer face (Y = −3.0, 62.0 × 8.0 mm = 496 mm²) on the bed; bed contact 100% of the 62.0 × 8.0 plan box. The plate stands 35.0 above the bed. The only downward-facing steps are the recess's top edge (0.8) and the guide holes (horizontal Ø2.3, exempt). No overhang, no supports.

Every number above is within the bands of section 4; the request, the L1s and `part.json` of `rpi_pico2` (47.0 × 11.4, Ø2.1, PCB 51.0 × 21.0 × 1.0) agree.
---

## 7. Grading procedure (design-specific rubric)

`benchmarks/generalize/rubric.md` (the generic rubric) did not exist when this file was written,
so the procedure is given here. When that file exists it governs the procedure and this section
governs only the numbers: **requirements numbers beat `part.json` numbers, and this section beats the
generic rubric where they differ.** The recipes for loading, `clear_of`, `inside`, apertures,
thicknesses, overhangs and bed contact are those of `benchmarks/enclosure/rubric.md` section 3
(Python at `/Users/robinonsay/python/llm-bt/venv/bin/python`, `trimesh`, `manifold3d`; count shells
with `manifold3d` `decompose()`, not `trimesh.split()`).

### 7.1 Inputs

STLs of every printed body in the assembly pose (mm), the `.scad` source (for naming features,
never for measuring), the declared layout file (`layout.json`: the pose of each catalogue part
and each body's print orientation) and the agent's own clearance report (graded only by the
evidence L3, never trusted elsewhere). The judge also gets `requirements.md` and `parts/*/part.json`
and nothing from the agent's code or transcript. The judge never opens `benchmarks/heldout.json`.

### 7.2 Procedure

1. **Package gate.** The listed files exist and load; otherwise stop with DOES NOT MEET and one
   defect on the package L3.
2. **Units.** Each body's largest bounding-box axis must be of the order stated in the package L3;
   if it looks like inches or metres record a defect and do not rescale silently.
3. **Normalise the frame.** Put the guide in the guide frame (1.1): fence face = Y = 0 with the plate at Y > 0, plate above Z = 0, fence pointing down. Rotations by multiples of 90° and mirroring only; record the transform.
4. **Build the references independently** from `part.json` and section 2 of this file at the
   declared layout (or the default layout where this file gives one), then run the sanity checks
   R1..Rn of section 2. A failing sanity check is fixed before grading.
5. **Run every applicable L3** with Python. Record measured value, limit, margin (measured minus
   limit, signed so that negative = fail) and PASS / FAIL / UNVERIFIED / N/A. **UNVERIFIED counts as
   FAIL.** N/A only for physical tests (unless a print was made).
6. **Look at the renders** after measuring, to confirm where a failure is and to catch defects
   no L3 covers (report those as observations; they do not change the verdict).
7. **Decide** and **report**.

### 7.3 Verdict classes

Gates: G0 package present and readable; G1 one manifold body; G2 four holes on the 47.0 × 11.4 pattern within 0.1; G3 guide hole Ø2.3 ± 0.05; G4 fence face square and the nearest row at 10.0 ± 0.1.

| Class | Rule |
|---|---|
| **WRONG** | any gate fails |
| **MINOR** | no gate fails, but some weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |
| **MEETS** | CORRECT and every applicable non-physical L3 of weight 1 and 2 passes (the loop's zero-error state) |

Anything that is not MEETS is DOES NOT MEET. Also report the weighted score Σ(weight × pass) /
Σ(weight) over applicable L3s, and the worst normalised margin among weight-3 L3s (margin divided
by the criterion's tolerance or, for one-sided limits, by 0.5 mm).

Precedence:
- A functional check outranks the size check that serves it (plug seats, bolt reaches, part fits
  beat opening size and wall size), as long as the size check still passes on its own numbers.
- **Designed contact is not interference** (section 1.3). Only penetration above 0.01 mm³ counts for the listed pairs.
- The numbers in this file are authoritative. If `parts/*/part.json` disagrees, build the reference from this file and record a defect on the L3 that the stale catalogue data breaks, with `where` = the part.json field.
- Fixed decisions (section 3.2) admit no alternative. Any unlisted alternative is graded on the default numbers and noted as an observation.
- Never relax a criterion, never round in the design's favour beyond ε, never infer a pass from a render.

### 7.4 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first (gates, then weight 3, 2, 1).
Each entry has: `req` (L3 with its L2 and L1), `status`, `body`, `feature` (by function and, if
it exists, by its SCAD name), `face` (surface with its outward normal), `location` (coordinates in
mm in the normalised frame, a point or a box `[xmin, ymin, zmin]–[xmax, ymax, zmax]`),
`measured` / `limit` / `margin` with units, `reference` (the reference model or envelope and its
datum), `render` (which view and where in the image), `evidence` (saved file, e.g. the
intersection solid `defect_<L3>.stl`) and `needed` (the geometric change that would make the
check pass, as numbers, never as a design instruction). Coordinates come from the measurement,
not from the SCAD source. Group L3s that fail for one geometric reason under the first and list
the rest in `also_fails`, keeping every L3 id. Keep observations separate from defects. Save the
report as `judge.md` and `defects.json`.

### 7.5 Measured-values table (always filled in, pass or fail)

| Quantity | Limit | Measured |
|---|---|---|
| Hole pitch X / Y (L3.1.1.2), mm | 47.0 / 11.4 ± 0.10 | |
| Hole-axis residual to P-IDEAL (L3.1.2.1), mm | ≤ 0.10 | |
| Hole Ø at mid-length (L3.2.1.1), mm | 2.30 ± 0.05 | |
| Hole length (L3.2.2.1), mm | 2.0–4.0 | |
| Fence face planarity / angle (L3.3.1.x) | ≤ 0.10 / 90° ± 0.5° | |
| Nearest-row distance to fence face (L3.3.3.1), mm | 10.00 ± 0.10 | |
| Recess size, depth (L3.4.1.x), mm | 51.4 × 21.4 ± 0.10; 0.80 ± 0.10 | |
| Recess centre vs pattern centre (L3.4.2.1), mm | ≤ 0.10 | |
| Pico wall clearance; receptacle d (L3.4.3.x), mm | 0.10–0.30; ≥ 0.10 | |
| Plate thickness, underside flatness (L3.5.1.x), mm | 4.0 ± 0.3; ≤ 0.10 | |
| Overhang patches; bed contact; shells (L3.6.x) | 0; ≥ 50%; 1 | |
| Bounding box (L3.7.1.1), mm | ≤ 70 × 40 × 10 | |
| Drill sweep penetration (L3.2.3.1); drilled-centre error (L3.8.2.1) | ≤ 0.01; ≤ 0.10 | |
| Self-report agreement (L3.9.2.1) | 100% within 0.05 | |

---

## 8. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 (`design.json`) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Hole positions | L2.1.1–L2.1.3 | L3.1.1.1, L3.1.1.2, L3.1.1.3, L3.1.2.1, L3.1.2.2, L3.1.3.1 | L1.1 | analysis | "mounting-hole pattern", "47.0 x 11.4 mm apart", "Hole centres must hit the pattern to within 0.1 mm" |
| L1.2 | Drill fit | L2.2.1–L2.2.3 | L3.2.1.1, L3.2.1.2, L3.2.2.1, L3.2.3.1 | L1.2 | analysis | "guide hole 2.3 mm", "2.1 mm holes" |
| L1.3 | Edge location | L2.3.1–L2.3.4 | L3.3.1.1, L3.3.1.2, L3.3.2.1, L3.3.2.2, L3.3.3.1, L3.3.4.1 | L1.3 | analysis | "locates on a panel edge" |
| L1.4 | Position check | L2.4.1–L2.4.3 | L3.4.1.1, L3.4.1.2, L3.4.2.1, L3.4.2.2, L3.4.3.1, L3.4.3.2 | L1.4 | analysis | "a recess for the Pico outline so I can check position" |
| L1.5 | Stiffness and ligaments | L2.5.1–L2.5.2 | L3.5.1.1, L3.5.1.2, L3.5.2.1, L3.5.2.2 | L1.5 | inspection | "A flat guide" |
| L1.6 | Printable | L2.6.1–L2.6.3 | L3.6.1.1, L3.6.2.1, L3.6.2.2, L3.6.3.1, L3.6.3.2 | L1.6 | analysis | "printed ... FDM ... PLA" (implied) |
| L1.7 | Size | L2.7.1–L2.7.2 | L3.7.1.1, L3.7.2.1 | L1.7 | inspection | "flat guide" |
| L1.8 | Drill access | L2.8.1–L2.8.2 | L3.8.1.1, L3.8.2.1 | L1.8 | analysis | "drilling" |
| L1.9 | Evidence | L2.9.1–L2.9.2 | L3.9.1.1, L3.9.1.2, L3.9.2.1 | L1.9 | inspection | (not the owner's words; needed by the judge) |

---

## Audit

Adversarial audit (second agent). Recomputed from `rpi_pico2` (PCB 51.0 x 21.0 x 1.0, holes 2.0 / 4.8 from the edges: 51 − 4 = 47.0, 21 − 9.6 = 11.4, receptacle 5.5 x 8.0 x 2.8 overhanging 1.3), the recess (51.4 x 21.4 x 0.8 at Y 5.0 to 26.4, centre 15.7), holes (X ±23.5, Y 10.0 and 21.4), hole-to-wall ligament 1.05, receptacle clearance 0.2, guide length 3.2, plate 62.0 x 35.0 x 4.0 plus fence 3.0 x 4.0 (bbox 62 x 35 x 8), and the print on its side (bed contact 62 x 8 = 100%). `rpi_pico2` loads and validates; `generic_box` (panel) loads with size_x/y/z = 150 / 100 / 3.0 and has the `TOP` and `FACE_MY` datums used. L1 = 9, L2 = 24, L3 = 38 match section 5 and the traceability. The Feasibility section satisfies every gate.

| # | Defect found | Fix |
|---|---|---|
| 1 | The request never said the panel thickness (A2: 3.0, only in L1.3), the 10.0 mm distance of the nearest row from the edge (gate G4, FD3, only in L1.3), or that the position along the edge is free (A8, FD2), though the 0.1 mm check is made after a best X shift. | Added to the request ("a flat sheet 3 mm thick ... the nearest row of holes must be 10 mm from that edge; I set the position along the edge by eye") and to L1.1. |
| 2 | Recess corner radius band "≤ 1.0" collides with the catalogue board's square corner: with 0.2 clearance, a radius above 0.68 cuts into the PCB corner (0.414 r vs 0.283), failing L3.4.3.1 and R5 for a design the band allows. | Band is ≤ 0.6 (L3.4.1.1) and L1.4 says so. |
| 3 | A6's rationale was wrong (1.4 x 2.3 = 3.22 > the nominal 3.2 guide length; a 3.2 mm guide with 0.2 play tilts the drill 3.6°, not 1.5°). | A6 rewritten with the computed tilt; band 2.0 to 4.0 unchanged and now stated in L1.2. |
| 4 | L3.5.2.1 said nominal 5.0; the smallest recess-to-edge distance in the sketch is 5.3 (X ends). | Nominal corrected to 5.3 (limit 3.0 unchanged). |
| 5 | The model datum names `PICO_HOLE_1..4` do not exist in `rpi_pico2` (the part has the `HOLE` axis list). | M-PICO row says they are items 1 to 4 of `HOLE`. |
| 6 | Judge bands not told to the agent: guide length 2.0 to 4.0, roundness 0.1, rows parallel to 0.1 degrees, fence thickness, length and depth, recess corner radius. | Added to L1.1, L1.2, L1.3, L1.4 in `design.json`. |

Noted, not changed: the panel size (150 x 100) is a reference choice of the grader (A2 says any width and length); the plan lists only `rpi_pico2` but the entry also uses `generic_box` (it exists); a horizontal 2.3 mm hole prints a little out of round on its side, which the ±0.05 diameter gate G3 and the 0.1 position gate G2 make the designer compensate (A10).
