# G22 2020 corner bracket with captive nuts: requirements (L1 / L2 / L3)

A generalization design (train split) in the style of E1-01 (`benchmarks/enclosure/requirements.md`).
The machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file.
`benchmarks/generalize/rubric.md` did not exist when this file was written, so section 9 holds the
design-specific grading rules; measuring recipes are those of `benchmarks/enclosure/rubric.md`
section 3 (load, `clear_of`, `inside`, slices, ray casting, overhang scan).

**Owner's request (verbatim):** "A 90 degree corner bracket joining two 2020 extrusions, one bolt
into each T-slot, with captive hex pockets for M5 nuts so I can assemble it from the outside. The
gussets should be at least 4 mm thick. Print orientation matters because the bolt loads are tensile
across the layers."

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete Python check on the delivered STL. Every row has a method
(inspection, analysis, demonstration, test, human), a pass/fail criterion with a number and a
tolerance, a weight (3 = critical, 2 = major, 1 = minor) and a gate mark (G0 to G5) where a failure
makes the design WRONG. Numbers that come from an assumption (section 3) are provisional until the
owner confirms them. Do not relax a criterion because the agent fails it.

---

## 1. Frame, tolerances and designed contact

- **Bracket frame:** the concave corner edge of the bracket (where the two bearing faces meet) lies
  along Y through the origin. The horizontal extrusion E1 runs along +X below the bracket
  (its top face is the plane Z = 0, x ≥ 0); the vertical extrusion E2 runs along Z at x ≤ 0 (its
  side face is the plane X = 0). The end of E1 butts the side face of E2. Leg A lies on E1's top
  face (Z from 0 up), leg B lies on E2's side face (X from 0 out). A design delivered in another
  frame is normalised by rotations by multiples of 90 degrees and mirroring only (rubric: put the
  concave corner at the origin with legs toward +X and +Z); that is never penalised. Units mm.
- **Measurement tolerances ε:** length and distance 0.02; diameter 0.03 (largest inscribed circle for
  holes, smallest enclosing circle for bosses); angle 0.5 degrees; area 1.0 mm²; volume 0.01 mm³. A
  value passes if it meets its limit to within ε.
- **Designed contact (this design).** The following are never interference (only a penetration above
  0.01 mm³ counts):
  1. each leg's bearing face on its extrusion face, and each leg's end face against the other
     extrusion's face (A's end face on E2's side face, B's end face on E1's top face);
  2. a tongue inside its slot (a clearance is required, section 5, L3.4.1.1);
  3. the bolt head on its counterbore floor and the bolt in its hole (a clearance is required);
  4. the T-nut's bearing plane against the underside of the slot lips (the nut is a reference model;
     the bracket may not touch it except at the cage gap, L3.5.1.1).
  Anything else touching or overlapping an extrusion, a nut or a bolt is interference.
- **Checks used** (`enclosure/requirements.md` 1.3 and `enclosure/rubric.md` 3.2, 3.3): `clear_of(bodies, volume, clearance)`
  (pass: penetration ≤ 0.01 mm³ and d ≥ clearance − ε) and `inside`. The grader builds all reference models and
  envelopes itself from the catalogue and the delivered bolt declaration; the design never builds or edits them for grading.

## 2. Reference models and envelopes

| Name | What | Source | Definition (bracket frame, mm) | Datums |
|---|---|---|---|---|
| **M-E1** | horizontal extrusion stub | catalogue `extrusion_2020` (length 100) | section 20 × 20, X 0 to 100, Y −10 to 10, Z −20 to 0; slot on the top face (Z = 0) centred Y = 0 with the **slot void V-SLOT-1** carved (below) | `FACE_PZ` (plane Z = 0), `SLOT_PZ` (axis along X at Y = 0, Z = 0) |
| **M-E2** | vertical extrusion stub | catalogue `extrusion_2020` (length 200) | section 20 × 20, X −20 to 0, Y −10 to 10, Z −100 to 100; slot on the +X face (X = 0) centred Y = 0 with **V-SLOT-2** carved | `FACE_PX` (plane X = 0), `SLOT_PX` (axis along Z at Y = 0) |
| **V-SLOT-k** | the slot void, carved by the grader (the catalogue does not model it; A3) | envelope | cross-section: opening 6.2 wide from the face to depth 1.8 (the lip), then interior 11.0 wide from depth 1.8 to depth 6.1; runs the full length | slot datums |
| **M-TNUT-1, -2** | M5 T-nut in each slot | catalogue `tnut_2020_m5` | plate 10.0 across the slot × 9.7 along the slot × 3.5 thick; bearing plane at depth 1.8 (underside of the lips); centred on the declared bolt axis (the thread axis), long side across the slot (FD4) | `BEARING`, `AXIS` |
| **M-BOLT-1, -2** | M5 button-head bolt per leg | catalogue `bolt_m5_iso7380` (length declared in `layout.json`) | head Ø9.5 × 2.75, shank Ø5.0; axis = the declared bolt axis, pointing into the slot; head bearing plane = the declared counterbore floor | `HEAD_BEARING`, `HEAD_TOP`, `TIP` |
| **V-BOLT-IN-k** | bolt insertion path | envelope | M-BOLT-k head and shank swept along the bolt axis from 30.0 outside the leg to seated | bolt axis |
| **V-HEAD-k** | bolt head seat | envelope | cylinder Ø9.5 from the counterbore floor (`HEAD_BEARING`) to `HEAD_TOP` (2.75 above) on the bolt axis | bolt axis |
| **V-DRIVER-k** | hex-key access | envelope | Ø6.0 column on the bolt axis from `HEAD_TOP` out to 25.0 beyond it (`tool_access_height`) | bolt axis |
| **V-OTHER-SLOTS** | openings of the unused slots | envelope | for E1: the slot openings on its +Y, −Y and −Z faces; for E2: the openings on its +Y, −Y and −X faces, each 6.2 wide, 6.1 deep, over the length | extrusion datums |

Sanity checks before grading (not L3s): R1 units, the bracket's largest axis is 30 to 60; R2 M-E1
and M-E2 each carry their slot datums within 0.01; R3 M-TNUT-k and M-BOLT-k do not overlap the
extrusions (nut inside V-SLOT, plate behind the lips); R4 the declared bolt axes lie within
0.3 of the measured hole axes (L3.12.1.2, otherwise the references are built from the measured axes).

**Placing the references.** The grader finds the bracket's two leg bearing faces (the two large
flat faces whose normals are 90 degrees apart, facing the extrusions), puts E1's top face and E2's
side face on them, and places each slot on the declared bolt axis. If the declaration is missing,
the bolt axes are taken from the measured clearance holes.

## 3. Assumptions and open questions for the owner

| # | Question | Value chosen | Why / uncertainty |
|---|---|---|---|
| **A1** | How do the two extrusions meet? | The end of the horizontal extrusion butts against the side face of the vertical one (a T-corner); the bracket sits in the inner corner. | "Corner bracket" and "joining two extrusions" at 90 degrees. Alternative: an L-corner with both ends meeting (needs two brackets or a different leg arrangement). Uncertainty medium. |
| **A2** | "captive hex pockets for M5 nuts so I can assemble it from the outside" | Read as: pockets in the bracket that keep each M5 **T-nut** captive, so the nuts can be dropped into the slots from outside. Realised by two tongues per leg that enter the slot opening on either side of the nut (the cage). No hex-nut pocket is graded. | Only the T-nut is in the parts list; a hex nut cannot be both captive and tightened from outside here, and a button-head bolt cannot be turned from inside a slot. Uncertainty **high**: if the owner means an M5 hex nut (ISO 4032, 8.0 across flats, 4.7 thick) trapped in a pocket on the leg's outer face, L1.5 changes. Confirm. |
| **A3** | 2020 slot numbers | Opening 6.2, lip thickness 1.8, interior width 11.0, slot depth 6.1, centre bore 4.2, section 20 × 20. | `extrusion_2020/part.json` (Misumi HFS5-2020 drawing); ±0.3 between vendors. The grader carves the void from these numbers. Uncertainty medium. |
| **A4** | Nut and bolt | T-nut 10.0 × 9.7 × 3.5 (±0.3). Bolt M5 ISO 7380 button head (Ø9.5 × 2.75, hex key 3.0), clearance hole 5.5, counterbore Ø9.9 and 2.95 deep per `part.json`. | `tnut_2020_m5` and `bolt_m5_iso7380` part.json. Vendors differ by ±0.3. The part.json T-nut `min_engagement` 5.0 cannot be met by a 3.5 plate; this document uses the engaged thread length in the plate, 3.0 (L3.3.3.1). Uncertainty medium. |
| **A5** | Load | No load number is given. Each bolt is assumed to see a pull up to 250 N and a shear of the same order. Only geometry is graded (leg thickness, corner section, ligaments), not a stress calculation. | The owner gives no load. Uncertainty high. |
| **A6** | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. Fit clearances between printed parts and metal: 0.10 to 0.25 per side. Horizontal cantilevers of at most 12 mm² area and 5.6 mm length (the tongues) are tolerated without supports. | Common printer. The tongue tolerance is an FDM convention. Uncertainty medium. |
| **A7** | Why the orientation matters | Layer adhesion is weaker than in-plane strength, so each bolt's tension should run along the layers: the angle between each bolt axis and the build direction is at least 75 degrees. | The owner says the loads are tensile across the layers. Here both bolt axes are perpendicular to Y, so the build direction is Y. Uncertainty low. |
| A8 | Extrusion stubs | Length 100 (E1) and 200 (E2). | Only used to build the reference solids. |
| A9 | Gusset meaning | A gusset is any web of material between the two legs. Its thickness is its smallest extent perpendicular to its plane. A single web spanning the full leg width counts. | The owner says "gussets at least 4 mm thick". Uncertainty low. |
| A10 | Surface finish, edge breaks, corner radius | Not graded. | Not asked. |

## 4. Fixed decisions (a choice was ambiguous; this is the one graded)

- **FD1 Corner type.** The T-corner of A1 in the frame of section 1. One leg per extrusion, one bolt per leg.
- **FD2 Slots used.** Leg A uses the top slot of E1 (centreline Y = 0 on the face Z = 0). Leg B uses the +X slot of E2.
- **FD3 Bolt axes.** Bolt 1 points along −Z (into E1's slot) at X = a. Bolt 2 points along −X (into E2's slot) at Z = b. a and b are the distances from the corner (L3.2.1.2).
- **FD4 T-nut seat.** The nut's 10.0 side lies across the slot, its 9.7 side along the slot, bearing plane at depth 1.8, body toward the slot floor; centred on the bolt axis. Its position along the slot is the bolt axis position, so the cage is graded against that.
- **FD5 Counterbore on the outside.** The bolt head is sunk into the leg's outer face (the face away from the extrusion).
- **FD6 Print orientation.** The build direction is a declared unit vector in `layout.json`; the graded rule is the angle to each bolt axis (L3.9.1.1). The overhang rule is applied in that direction.
- **FD7 Tongue overhang exemption.** The underside of each slot tongue (a cantilever of at most 12 mm² area and 5.6 mm length from its leg face) and round holes up to Ø12 are not counted as overhangs.

## 5. Requirements tree

### L1.1 One body, two legs flat on the extrusion faces, 90 degrees apart

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | Each leg's bearing face rests on its extrusion face. | analysis | contact area (area of bracket faces within 0.10 of the extrusion face plane, outside the slot opening) ≥ 400 mm² for each leg | 3 | |
| L3.1.1.1 | Leg A on M-E1's top face. | analysis | ≥ 400 mm² (sketch: 552) | 3 | |
| L3.1.1.2 | Leg B on M-E2's side face. | analysis | ≥ 400 mm² (sketch: 552) | 3 | |
| L2.1.2 | The bearing faces are 90 degrees apart. | inspection | angle between the two bearing planes (least-squares fit to the contact faces) 90 ± 0.5° | 3 | |
| L3.1.2.1 | Bearing-plane angle. | inspection | 89.5° to 90.5° | 3 | |
| L2.1.3 | The bracket does not penetrate the extrusions. | analysis | clear_of(BRACKET, (M-E1 ∪ M-E2 with V-SLOT carved), 0.0): penetration ≤ 0.01 mm³ | 3 | G2 |
| L3.1.3.1 | Bracket vs extrusions. | analysis | penetration ≤ 0.01 mm³ | 3 | G2 |

### L1.2 One bolt axis per leg, on the slot centreline, square to the leg, 15 to 30 mm from the corner

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Each clearance hole is on its slot centreline and at a sensible distance from the corner. | inspection | hole axis (largest inscribed circle centre, mid-depth slice) within 0.2 of Y = 0; distance from the corner plane (X for bolt 1, Z for bolt 2, FD3) between 15.0 and 30.0 | 3 | |
| L3.2.1.1 | Hole axes on the slot centreline. | inspection | \|Y\| ≤ 0.20 for both | 3 | |
| L3.2.1.2 | Hole axis distance from the corner. | inspection | a, b ∈ [15.0, 30.0] | 2 | |
| L3.2.1.3 | Symmetry of the pattern. | inspection | \|a − b\| ≤ 0.5 | 1 | |
| L2.2.2 | Each bolt axis is square to its bearing face. | inspection | angle between hole axis (ray-cast fit) and the bearing-plane normal ≤ 1.0° | 2 | |
| L3.2.2.1 | Hole squareness. | inspection | ≤ 1.0° (+ ε) | 2 | |

### L1.3 Bolt holes, sunk heads and a bolt length that engages the T-nut

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Clearance hole for M5. | inspection | Ø 5.5 to 5.9, through the leg, coaxial ≤ 0.1 with its axis | 3 | |
| L3.3.1.1 | Clearance hole diameter. | inspection | 5.5 ≤ Ø ≤ 5.9 | 3 | |
| L2.3.2 | Counterbore sinks the button head from the leg's outer face. | inspection | Ø 9.9 to 10.6; depth 2.95 to 3.4; floor flat (planarity ≤ 0.1) and square to the axis | 2 | |
| L3.3.2.1 | Counterbore diameter and depth. | inspection | as L2.3.2 | 2 | |
| L3.3.2.2 | Head sunk below the face. | inspection | `HEAD_TOP` at least 0.1 below the leg outer face (so the head is not proud) | 1 | |
| L2.3.3 | The declared bolt length engages the nut and clears the slot floor. | inspection | with `HEAD_BEARING` on the counterbore floor and the nut at its seat: thread engaged in the nut ≥ 3.0 (nut body penetrated by the shank along the axis, max 3.5) and `TIP` at least 0.5 above the slot floor (depth 6.1) | 3 | G4 |
| L3.3.3.1 | Engagement window. | inspection | engaged ≥ 3.0 and tip-to-floor ≥ 0.5, i.e. the tip depth below the extrusion face lies in [4.8, 5.6] (sketch: 5.45) | 3 | G4 |

### L1.4 Tongues key into the slot, and nothing else enters a slot

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Each leg has two tongues that enter its slot opening and stay in the slot void. | analysis | count = 2 per leg (4 in all); inside(each tongue, V-SLOT, 0.10): d ≥ 0.10 from the lip faces and slot walls | 3 | G3 |
| L3.4.1.1 | Tongues inside the slot with clearance. | analysis | d ≥ 0.10 (+ ε) for every tongue; count 2 + 2 | 3 | G3 |
| L3.4.1.2 | Tongue width (across the slot). | inspection | 5.7 ≤ w ≤ 6.0 | 2 | |
| L3.4.1.3 | Tongue depth below the bearing face. | inspection | 3.5 ≤ depth ≤ 5.6 (slot depth 6.1 less 0.5) | 2 | |
| L2.4.2 | No other bracket material enters a slot. | analysis | every connected region of BRACKET ∩ V-SLOT-k is one of the four tongues | 2 | |
| L3.4.2.1 | Material in the slot. | analysis | region count = 4, each within 15.0 of its leg's bolt axis along the slot | 2 | |

### L1.5 The T-nut is held captive in the leg's cage, centred on the bolt

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Each nut has a gap on both sides along the slot. | demonstration | gap from each nut end face (9.7 side) to the nearest tongue face 0.2 to 0.5, both sides | 3 | |
| L3.5.1.1 | Cage gaps. | demonstration | each of the four gaps ∈ [0.20, 0.50] | 3 | |
| L3.5.1.2 | The nut cannot walk away. | demonstration | translating M-TNUT-k by 1.0 along the slot in either direction makes it intersect the bracket (> 0.01 mm³) | 2 | |
| L2.5.2 | The cage is centred on the thread axis. | inspection | midpoint between the two tongues of a leg within 0.3 of its bolt axis along the slot | 2 | |
| L3.5.2.1 | Cage centring. | inspection | offset ≤ 0.3 | 2 | |
| L2.5.3 | The bracket does not touch the nut except at the cage. | analysis | BRACKET ∩ M-TNUT-k ≤ 0.01 mm³ | 3 | |
| L3.5.3.1 | Bracket vs nut. | analysis | ≤ 0.01 mm³ | 3 | |

### L1.6 Assembly from the outside with a hex key

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Each bolt goes in along its own axis. | test | clear_of(BRACKET, V-BOLT-IN-k, 0.0) | 3 | |
| L3.6.1.1 | Bolt insertion paths clear (the hole and counterbore are the path). | test | penetration ≤ 0.01 mm³ for both | 3 | |
| L2.6.2 | A hex key reaches each head. | test | clear_of(BRACKET ∪ M-E1 ∪ M-E2, V-DRIVER-k, 0.0) | 2 | |
| L3.6.2.1 | Driver columns clear. | test | d ≥ 0 for both | 2 | |

### L1.7 A gusset at least 4.0 mm thick joins the legs

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | At least one gusset (A9) of thickness ≥ 4.0. | inspection | web between the legs; smallest extent perpendicular to its plane ≥ 4.0 | 3 | |
| L3.7.1.1 | Gusset thickness. | inspection | ≥ 4.0 (sketch: 20.0 for the full-width wedge) | 3 | |
| L2.7.2 | The gusset reaches along both legs. | inspection | extent from the corner along each leg, measured from the other leg's outer face, ≥ 10.0 | 2 | |
| L3.7.2.1 | Gusset reach. | inspection | ≥ 10.0 on both legs | 2 | |
| L2.7.3 | The gusset and legs leave room for each bolt head. | analysis | clear_of(BRACKET, V-HEAD-k, 0.1) where V-HEAD-k is the head cylinder Ø9.5 from the counterbore floor to `HEAD_TOP` | 2 | |
| L3.7.3.1 | Head clearance. | analysis | d ≥ 0.1 between head and counterbore wall or gusset | 2 | |

### L1.8 Load path: thick legs, a solid corner, material round the holes

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Leg thickness. | inspection | each leg, bearing face to outer face, away from features: 5.0 to 8.0 | 3 | |
| L3.8.1.1 | Leg thickness. | inspection | median over a 2 mm grid at least 3 mm from any hole, edge or gusset: 5.0 ≤ t ≤ 8.0 | 3 | |
| L2.8.2 | The corner section is solid and large. | analysis | area of the section by the plane through the corner line at 45° to both legs ≥ 150 mm² | 2 | |
| L3.8.2.1 | Corner section area. | analysis | ≥ 150 mm² (sketch: 304) | 2 | |
| L2.8.3 | Material round each bolt hole. | analysis | distance from each counterbore edge to the nearest bracket edge, leg end, other hole or gusset ≥ 3.0 | 2 | |
| L3.8.3.1 | Ligament round each counterbore. | analysis | ≥ 3.0 (sketch: 3.9) | 2 | |

### L1.9 The print orientation keeps bolt tension along the layers

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The declared build direction is at least 75 degrees from each bolt axis. | inspection | angle(bolt axis, build direction) ≥ 75° for both (sketch: 90°) | 3 | G5 |
| L3.9.1.1 | Build direction vs bolt axes. | inspection | ≥ 75° (− ε) for both bolt axes | 3 | G5 |
| L3.9.1.2 | The orientation is declared and the bed face named. | inspection | `layout.json` has a unit build vector and a bed-side description | 2 | |

### L1.10 One manifold body, printable without supports, thick enough

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | One watertight shell. | analysis | shells = 1; manifold status NoError | 3 | G1 |
| L3.10.1.1 | Shells and manifold. | analysis | 1; NoError | 3 | G1 |
| L2.10.2 | No unsupported overhang in the declared orientation. | analysis | faces with n·build < −cos 45° (patch > 1 mm²) = 0 apart from FD7 (round holes ≤ Ø12; tongue undersides each ≤ 12 mm² and ≤ 5.6 long) | 3 | |
| L3.10.2.1 | Overhang scan. | analysis | 0 offending patches | 3 | |
| L2.10.3 | Bed contact. | analysis | area of faces with n = −build at the bed ≥ 20% of the plan bounding box (the plan is L-shaped, so it cannot reach 50%) | 2 | |
| L3.10.3.1 | Bed contact. | analysis | ≥ 20% (sketch: 23%) | 2 | |
| L2.10.4 | No thin feature; fits the bed. | analysis | local thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 | |
| L3.10.4.1 | Thin features and build volume. | analysis | as L2.10.4 | 1 | |

### L1.11 Size and room for the rest of the frame

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Leg width and overall size. | inspection | each leg's width along the slot-perpendicular direction 19.0 to 21.0; bounding box ≤ 48 × 22 × 48 (X × Y × Z) | 2 | |
| L3.11.1.1 | Leg width. | inspection | 19.0 ≤ w ≤ 21.0 | 2 | |
| L3.11.1.2 | Bounding box. | inspection | ≤ 48.0 × 22.0 × 48.0 | 1 | |
| L2.11.2 | The unused slots stay open. | analysis | clear_of(BRACKET, V-OTHER-SLOTS, 0.5) | 1 | |
| L3.11.2.1 | Unused slot openings. | analysis | d ≥ 0.5 | 1 | |

### L1.12 The package says what was built and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds `bracket.stl` (mm, bracket frame), the `.scad` source, `layout.json` (the two bolt axes as point + direction, bolt length, counterbore floor, T-nut centres, build direction) and the agent's own report. | inspection | all present and readable; largest axis 30 to 60 | 3 | G0 |
| L3.12.1.1 | Files present and parse; units. | inspection | true | 3 | G0 |
| L3.12.1.2 | Declared bolt axes match the measured holes. | inspection | each within 0.2 (position) and 1.0° (direction) | 2 | |
| L2.12.2 | The agent's report agrees with the grader. | analysis | for every `clear_of`/`inside` value the agent reports: same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 | |
| L3.12.2.1 | Self-report vs judge. | analysis | 100% within 0.10 | 1 | |

## 6. Gates and counts

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.12.1.1), **G1** one
manifold body (L3.10.1.1), **G2** no penetration of the extrusions (L3.1.3.1), **G3** tongues inside
the slots (L3.4.1.1), **G4** the bolt engages the T-nut and clears the floor (L3.3.3.1), **G5** the print
orientation keeps bolt tension along the layers (L3.9.1.1). Classes: WRONG (a gate fails), MINOR
(no gate fails, a weight-3 L3 fails), CORRECT (all weight-3 pass), MEETS (CORRECT and every L3 of
weight 1 and 2 passes).

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 30 |
| L3 | 40 |

## 7. Feasibility (a design exists)

Built and checked with `manifold3d` (one shell, NoError, volume 8 918 mm³, bounding box
X −5 to 40, Y −10 to 10, Z −5 to 40 = 45 × 20 × 45). Numbers in mm, bracket frame:

| Feature | Value |
|---|---|
| leg A | X 0 to 40, Y −10 to 10, Z 0 to 5.5 (on E1's top face) |
| leg B | X 0 to 5.5, Y −10 to 10, Z 0 to 40 (on E2's side face) |
| gusset | full-width wedge, triangle (5.5, 5.5) – (16.0, 5.5) – (5.5, 16.0) in X–Z, Y −10 to 10: thickness 20.0, reach 10.5 along each leg; corner section on the plane X = Z is 304 mm² |
| bolt 1 | axis along −Z at X = 25.0, Y = 0; hole Ø5.7; counterbore Ø10.2 × 2.95 from Z 5.5 (floor at Z 2.55); bolt M5 × 8 head bearing at Z 2.55; head top at Z 5.30 (0.20 below the face) |
| bolt 2 | axis along −X at Z = 25.0, Y = 0; same hole and counterbore from X 5.5; bearing at X 2.55 |
| T-nut seats | plate bearing at depth 1.8 (Z −1.8 / X −1.8), body to depth 5.3, 9.7 along the slot centred on the bolt axis |
| tongues | per leg two, 5.8 wide (0.2 per side in the 6.2 opening), 2.0 along the slot, 5.0 deep below the bearing face (floor 1.1 further): leg A at X 17.85 to 19.85 and 30.15 to 32.15; leg B at Z 17.85 to 19.85 and 30.15 to 32.15 |
| cage gaps | nut ends at X 20.15 and 29.85, tongue faces at 19.85 and 30.15: 0.30 each side (measured min gap 0.30) |
| bolt tip | at depth 5.45 (nut back at 5.3, floor at 6.1): engaged 3.5, tip-to-floor 0.65 |
| penetration | bracket vs E1 and E2 (slots carved): 0.0 mm³; vs the nut: 0.0; vs the bolt: 0.0 |
| contact area | leg A on E1: 40 × 20 − 6.2 × 40 = 552 mm²; leg B likewise |
| ligament | counterbore edge (X 19.9) to the wedge tip (X 16.0): 3.9; to the leg side: 4.9; to the leg end: 9.9 |
| print | build direction Y (bed on the Y = −10 face, 465 mm² = 23% of the 45 × 45 plan); both bolt axes are 90° from Y; overhang scan finds only the four tongue undersides (10.0 mm² each, exempt by FD7) and the round holes |

## 8. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 | Method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | 90 degree joint, legs flat | L2.1.1–L2.1.3 | L3.1.1.1–2, L3.1.2.1, L3.1.3.1 | L1.1 | analysis | "90 degree corner bracket joining two 2020 extrusions" |
| L1.2 | Bolt pattern | L2.2.1–L2.2.2 | L3.2.1.1–3, L3.2.2.1 | L1.2 | inspection | "one bolt into each T-slot" |
| L1.3 | Bolt and head fit | L2.3.1–L2.3.3 | L3.3.1.1, L3.3.2.1–2, L3.3.3.1 | L1.3 | inspection | "M5", "bolt" |
| L1.4 | Slot engagement | L2.4.1–L2.4.2 | L3.4.1.1–3, L3.4.2.1 | L1.4 | analysis | "into each T-slot" |
| L1.5 | Captive nut | L2.5.1–L2.5.3 | L3.5.1.1–2, L3.5.2.1, L3.5.3.1 | L1.5 | demonstration | "captive hex pockets for M5 nuts" (A2) |
| L1.6 | Assemble from outside | L2.6.1–L2.6.2 | L3.6.1.1, L3.6.2.1 | L1.6 | test | "assemble it from the outside" |
| L1.7 | Gussets | L2.7.1–L2.7.3 | L3.7.1.1, L3.7.2.1, L3.7.3.1 | L1.7 | inspection | "gussets should be at least 4 mm thick" |
| L1.8 | Load path | L2.8.1–L2.8.3 | L3.8.1.1, L3.8.2.1, L3.8.3.1 | L1.8 | analysis | "bolt loads are tensile" |
| L1.9 | Print orientation | L2.9.1 | L3.9.1.1–2 | L1.9 | inspection | "print orientation matters", "tensile across the layers" |
| L1.10 | Printable | L2.10.1–L2.10.4 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1 | L1.10 | analysis | implied (FDM) |
| L1.11 | Size, rest of frame | L2.11.1–L2.11.2 | L3.11.1.1–2, L3.11.2.1 | L1.11 | inspection | "2020 extrusions" (the rest of the frame) |
| L1.12 | Evidence | L2.12.1–L2.12.2 | L3.12.1.1–2, L3.12.2.1 | L1.12 | inspection | needed by the judge |

## 9. Grading (design-specific; used because `generalize/rubric.md` is missing)

- **Verdict:** WRONG (any gate G0 to G5 fails), MINOR (no gate fails, some weight-3 L3 fails), CORRECT
  (every weight-3 L3 passes), MEETS (CORRECT and every L3 of weight 1 and 2 passes). UNVERIFIED counts
  as FAIL. Report also the weighted score Σ(weight × pass)/Σ(weight) and the worst normalised margin
  among weight-3 L3s.
- **Precedence:** numbers in this document beat `part.json` (for example the T-nut `min_engagement` 5.0, A4). The slot void
  is carved by the grader from A3. Never relax a criterion or round in the design's favour beyond ε.
- **WHERE a defect is:** one entry per failed or UNVERIFIED L3, gates first then weight 3, 2, 1, with:
  `req` (L3 with L2 and L1), `status`, `body` (`bracket` or `layout`), `feature` (named by function, for example
  "tongue 2 of leg B" or "counterbore of bolt 1"), `face` (surface and outward normal), `location` (point or bounding box
  in the bracket frame), `measured` / `limit` / `margin`, `reference` (M-TNUT-1, V-SLOT-2 and so on, with the datum),
  `needed` (the target as numbers, for example "tongue width must be 5.7 to 6.0, now 6.3"), `evidence` (saved defect STL).
  `needed` never says how to build it.
- **Measured-values table (always filled in):** contact areas; bearing angle; hole Ø, Y offset and distance a, b;
  counterbore Ø and depth; engaged length and tip-to-floor; tongue count, widths, depths and slot clearance; cage gaps;
  gusset thickness and reach; leg thickness; corner section; ligament; build angle to each bolt axis; overhang patches;
  bed contact; shells; bounding box; self-report agreement.

## Audit

Adversarial audit against `benchmarks/enclosure/rubric.md` (the generalize rubric is absent), the catalogue and the L1 text in
`design.json`. The feasibility sketch of section 7 was rebuilt in `manifold3d` with the two extrusions, all four T-slot voids each,
the T-nuts, the bolts and every envelope of section 2, and re-measured; `extrusion_2020`, `tnut_2020_m5` and `bolt_m5_iso7380`
load through `parts.Catalog` (they need `length` from the request, as designed). L1 12 (E1-01: 12), L2 30 (45), L3 40 (69):
a single-part design, so simpler than the enclosure; counts in section 6 match the tables.

| # | Finding | Fix |
|---|---|---|
| 1 | Re-measured and confirmed: one shell, volume 8 918 mm³, bounding box 45 x 20 x 45; penetration of E1 and E2 (slots carved) 0.0; tongue-to-slot clearance 0.20; two real regions of 58 mm³ in each slot (the tongues); cage gaps 0.30; bracket vs nut and vs bolt 0.0; bolt tip at depth 5.45 (engaged 3.5, tip to floor 0.65); V-BOLT-IN and V-DRIVER columns clear; distance to every unused slot void 1.0 or more; bed contact 465 mm² = 23.0%; overhang scan: the round holes and counterbores (Ø10.2 <= Ø12) and the four tongue undersides of 10.0 mm² each (FD7). The contact area quoted as 552 is the area outside the slot opening (751 mm² is the whole bearing face). | None needed. |
| 2 | Numbers the judge uses that the agent was never told: bearing area 400 mm² per leg; hole squareness 1 degree; counterbore Ø9.9 to 10.6 and depth 2.95 to 3.4; tongue depth 3.5 to 5.6 and slot clearance 0.1; tolerance of the declared axes (0.2 mm, 1 degree). | Added to the L1 texts in `design.json` (ids and count unchanged). |
| 3 | A4 / L2.3.3: `tnut_2020_m5/part.json` has `min_engagement` 5.0 and a `screw_tip` keep-out of that length, which a 3.5 mm plate can never give; an agent that follows the catalogue literally would size an M5 x 12 and hit the slot floor (G4). This document overrides it (engaged 3.0 to 3.5, tip depth 4.8 to 5.6) and L1.3 states the 3.0 minimum. | Left as is: the catalogue file is shared by G16, G21, G24 and the hold-out G25 and G48, and changing it is a catalogue decision. Reported as an open problem: the catalogue value should become 3.0 (or the keep-out should be re-based on the bolt tip). |

Observation (not changed): the counterbore leaves 2.55 mm of leg under the bolt head (leg 5.5, counterbore 2.95 deep); only geometry is graded (A5), but a load-bearing design may want a thicker leg within the 5.0 to 8.0 band.
