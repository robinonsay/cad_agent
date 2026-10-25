# G19 625 idler block for 2020 slot: requirements (L1 / L2 / L3)

Design G19 is a 3D-printed idler block that clamps to the T-slot of a 2020 extrusion and carries
a 625 bearing on an M5 bolt. It is the held-out design of this batch: it exercises a sliding fit in
a slot, a bearing pocket with a side clearance, and a bolt-and-T-nut clamp stack, none of which
appears in the enclosure benchmark. The method (declared layout, catalogue parts placed by datums,
numbers only in the request and the catalogue) is the same.

**Request (as given to the agent):** I need an idler block that carries a 625 bearing (5 x 16 x 5 mm) on an M5 bolt and bolts to the T-slot of a 2020 aluminium extrusion. Model the extrusion as a 60 mm length, with the block nominally at its middle. One M5 button-head bolt does both jobs: it is the bearing's axle and it clamps the block into a drop-in M5 T-nut in the slot. The block needs a tongue for the profile's 6.2 mm slot opening that slides along the slot with 0.2 mm clearance (so the tongue is 6.0 mm wide). The bearing's outer ring must spin free of the block with 1 mm side clearance, and a belt runs on its outer ring. It is printed on an FDM printer in PLA.

**Plan brief (verbatim):** "An idler block that carries a 625 bearing (5 x 16 x 5 mm) on an M5 bolt and bolts to the T-slot of a 2020 extrusion. The block needs a 6.2 mm slot-engagement tongue that slides in the slot with 0.2 mm clearance. The bearing outer ring must spin free of the block with 1 mm side clearance."

**Split:** holdout. **Family:** mechanical_mount. **Capabilities exercised:** bearing_press_fit, shaft_clearance, slot_engagement, bolt_pattern, sliding_fit.

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

- **Extrusion frame (all tables below):** the catalogue `extrusion_2020` frame: Z along the profile,
  origin at the centre of the section on the start end face; slots face +X, +Y, −X, −Y. The block
  is mounted on the **+X** slot (`SLOT_PX`): the extrusion's +X face is the plane X = 10.0, the slot opening is
  |Y| < 3.1 from X = 10.0 to X = 8.2 (the lips are 1.8 thick), and the interior undercut is
  |Y| < 5.5 from X = 8.2 to the slot floor at X = 3.9. The reference extrusion is 60.0 long
  (Z 0 to 60). A block delivered on another face or rotated is normalised into this frame before grading (7.2 step 3); that is never penalised.
- **Block axis:** the bolt axis is the line Y = 0, Z = z0 along X, where z0 is the position along the extrusion declared in `layout.json` (nominal 30.0). The block frame is the extrusion frame.
- **Part frames:** `bearing_625` (axis Z, face A at Z = 0), `tnut_2020_m5` (origin on its bearing face, body toward −Z) and `bolt_m5_iso7380` (origin on the head bearing face, shank toward −Z) are each placed turned so their axis lies along the block axis; their datums give the X positions in 2.2.

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

- the block's shoulder faces resting on the extrusion's +X face (X = 10.0)
- the T-nut's bearing face against the underside of the lips (X = 8.2)
- the bolt thread in the T-nut thread and the bolt head on the bearing's inner ring
- the bearing's inner ring against the block's seat boss (inner-ring land only) and the bolt shank in the bearing bore
- the tongue's sides sliding in the slot opening (only the clearance band of L2.5.1 applies; touching is a failure there, not a designed contact)

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` in `benchmarks/generalize/parts/<id>/` (`extrusion_2020`, `tnut_2020_m5`, `bolt_m5_iso7380`, `bearing_625`). These are the only places target-specific part numbers may live.
- **envelope**: a keep-out or access volume generated by Python from datums. Never drawn by hand.
- **computed**: derived from the delivered STL (tongue faces, pocket, hole axes, apertures).

### 2.2 Reference models (M-) and datums

| Name | What | Source | Size and position (extrusion frame, mm) | Datums |
|---|---|---|---|---|
| **M-EXT** | 2020 T-slot profile, 60.0 long, with the real slot | catalogue `extrusion_2020`, length 60.0 (A1) | 20 × 20 section, Z 0 to 60. On each side: opening 6.2 wide through the 1.8 lip, interior undercut 11.0 wide to the slot floor (depth 6.1 from the face); centre bore Ø4.2. The part's slot boxes are the opening; the undercut is built from `slot_inner_width` and `lip_thickness` (A2). | `FACE_PX` (plane X = 10), `SLOT_PX` (axis), `SLOT_FLOOR_PX` (plane X = 3.9) |
| **M-NUT** | M5 drop-in T-nut | catalogue `tnut_2020_m5` | plate 3.5 (X) × 10.0 (across, Y) × 9.7 (along, Z), X 4.7 to 8.2, centred on (Y 0, Z z0); thread M5 along X | `BEARING` (plane X = 8.2), `AXIS` (−X), `BACK` (plane X = 4.7) |
| **M-BRG** | 625 bearing 5 × 16 × 5 | catalogue `bearing_625` | OD 16.0, bore 5.0, width 5.0; X 12.6 to 17.6 on the block axis; inner ring r 2.5 to 4.0, outer ring r 6.0 to 8.0 (A3) | `AXIS`, `FACE_A` (X = 12.6), `FACE_B` (X = 17.6) |
| **M-BOLT** | M5 button-head bolt, length L declared by the design (expected 12.0) | catalogue `bolt_m5_iso7380` | head Ø9.5 × 2.75, bearing plane X = 17.6 (on `FACE_B`), head X 17.6 to 20.35; shank Ø5.0 from X = 17.6 down to the tip at X = 17.6 − L | `AXIS`, `HEAD_BEARING`, `TIP` |
| **RBA** | reference block assembly = M-EXT ∪ M-NUT ∪ M-BRG ∪ M-BOLT at the declared (or default) layout | assembled | as above | all of the above |

Default layout (used when a design declares none): z0 = 30.0; bearing face A at X = 12.6; bolt length 12.0. The grader recomputes the X positions from the declared block: **M-BRG face A is placed on the block's seat boss top, M-BOLT's head on face B, M-NUT's bearing face on the lips' underside.**

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-RING** | the bearing's outer ring while it spins | M-BRG annulus r 6.0 to 8.0, X 12.6 to 17.6 (rotationally symmetric, so one volume covers every angle) |
| **V-HEADRING** | clearance zone round the bolt head | M-BOLT head Ø9.5 column, X 17.6 to 20.35 |
| **V-DRIVER** | access for the hex key | Ø9.5 column on the bolt axis from X = 20.35 to X = 45.35 (25.0 tool access, part value) |
| **V-SLIDE** | the block's sliding path | the block moved along ±Z from z0 in 1.0 steps, ±15.0 (within the 60.0 extrusion for a 24.0 block) |
| **V-SLOT-OPEN** | the slot opening the tongue lies in | M-EXT's opening: abs(Y) < 3.1, X 8.2 to 10.0 |
| **V-TONGUE** | the tongue actually present | computed: the part of the block below X = 10.0 (the shoulder plane), i.e. everything that enters the slot opening |
| **V-SHOULDER** | the block's contact face | computed: the largest planar face of the block with normal −X at X ≈ 10.0, outside the tongue |
| **V-POCKET** | the bearing pocket | computed: the connected void of the block that holds M-BRG (a circle of the largest inscribed radius in the YZ plane) |
| **V-BOLT-HOLE** | the clearance hole | computed: the through hole of the block on the block axis |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-EXT | section and slot | 20.0 × 20.0 ± 0.1; opening 6.2 ± 0.05; lip 1.8 ± 0.05; interior 11.0 ± 0.1; depth 6.1 ± 0.05 |
| R2 | M-NUT | size and fit in the slot | 10.0 × 9.7 × 3.5 ± 0.1; plate inside the interior (10.0 < 11.0) and wider than the opening |
| R3 | M-BRG | boundary dimensions | OD 16.0, bore 5.0, width 5.0 ± 0.02 |
| R4 | M-BOLT | head and shank | head Ø9.5 × 2.75 ± 0.1; shank Ø5.0 |
| R5 | RBA | parts do not collide except at designed contact | intersection ≤ 0.01 mm³ outside the contact list |
| R6 | M-NUT | seated under the lips | `BEARING` plane within 0.05 of X = 8.2 |

**Seating rule.** The RBA is placed at the pose declared in `layout.json`. The grader verifies the declaration: the block's shoulder plane lies on X = 10.0 (≤ 0.05), the block axis lies on Y = 0 (≤ 0.15), M-BRG face A lies on the seat boss top (≤ 0.10), M-BOLT's head bearing plane lies on M-BRG face B (≤ 0.10). If the declaration is missing or fails verification, the RBA is seated by that fit (shoulder on the face, axis on the bolt hole), and the pose L3 rows fail.
---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (with uncertainty)

Each line gives the value chosen and why. Robin may correct any of them; a correction changes this file and the catalogue, and earlier scores become stale.

| # | Question | Value chosen | Why and uncertainty |
|---|---|---|---|
| A1 | Extrusion length? | 60.0 (reference length, now stated in the request); the block's z0 is 30.0 (any z0 from 27.0 to 33.0 keeps the ±15.0 slide inside the 60.0 length for a 24.0 block). | Given in the request. The block must slide ±15 and stay clear of both ends. Uncertainty irrelevant to the block (it only sets the sweep range). |
| A2 | Real slot geometry? | Opening 6.2, lip 1.8, interior undercut 11.0 wide to depth 6.1, centre bore Ø4.2 (catalogue `extrusion_2020`). | Misumi HFS5-2020 drawing; the interior width and lip are ±0.3 between vendors, so the sweep tests the tongue only in the opening. The part model is a solid box with slot datums only; the grader builds the undercut from the datum numbers. |
| A3 | Bearing ring sizes? | 625: OD 16.0, bore 5.0, width 5.0 (ISO 15). Inner ring land r 2.5 to 4.0 (OD 8.0), outer ring r 6.0 to 8.0 (ring ID 12.0); these two land diameters are now `inner_ring_land_diameter` / `outer_ring_land_diameter` in `bearing_625/part.json`. | Boundary dimensions are standard; the ring split is typical (±0.5 on r 4.0 and 6.0). A shielded bearing's shield sits inside these. |
| A4 | T-nut orientation? | The nut's 10.0 side lies across the slot (Y), its 9.7 side along Z, its 3.5 thickness along X; it is dropped in from the end and sits under the lips. | Catalogue `tnut_2020_m5`: 10.0 × 9.7 × 3.5. Quarter-turn nuts behave the same. ±0.3 on the thickness between vendors. |
| A5 | Bolt length? | M5 × 12.0: from the bearing top (X 17.6) the tip is at X 5.6: 2.6 into the nut, 1.7 above the slot floor. | Stock length 12. For a different block stack the design picks another stock length so that engagement ≥ 2.4 and tip ≥ floor + 0.5 (L3.7.1.1). Engagement of 2.4 = 3 threads of the 0.8 pitch. Uncertainty ±0.5. |
| A6 | Load? | A belt tension of about 20 N across the pulley, radial (±Y or ±Z in the block's plane). | The tongue and bolt clamp carry it by friction on the shoulder (area in L3.6.1.2) and the tongue's side bearing on the lips. Not computed beyond the contact area; a physical test is optional. |
| A7 | Belt access? | The bearing's outer cylinder protrudes at least 1.5 above the block's outer face so a belt can run on it. | An idler runs a belt or cord on its outer ring. 2.0 is the nominal protrusion. |
| A8 | Printing? | FDM, PLA, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. A round hole with horizontal axis up to Ø20 is not an overhang (the bearing pocket Ø18; a teardrop or crown flat is welcome). A downward-facing step of at most 2.0 deep (the tongue relief's upper edge, 1.5 deep) is not an overhang. | The generic rule exempts round holes up to Ø12; Ø18 needs the larger limit for the bearing pocket. Uncertainty ±3 on the 20. Bridges ≤ 15 apply. |
| A9 | Fits of printed holes? | Pocket Ø18.0 and bolt hole Ø5.5 are the model's nominal sizes; the grader measures the delivered STL. | FDM prints holes about 0.1–0.2 small; the 1.0 side clearance and the 0.25 radial play of the bolt absorb it. |

### 3.2 Fixed decisions (one choice, no alternatives graded)

| # | Ambiguity | Decision | Reason |
|---|---|---|---|
| FD1 | How does one M5 bolt serve as axle and clamp? | The bolt axis is **perpendicular to the extrusion face** (along X) on the slot centre line. The bolt passes through the bearing bore, a seat boss, the block floor and the slot opening, and threads into the T-nut. The bolt head clamps the bearing's inner ring against the boss, the boss against the block, the block's shoulder against the extrusion face, and pulls the nut up against the lips. | The parts list has one bolt, one T-nut and one bearing; this is the usual 2020 idler. The bearing axis is therefore perpendicular to the face. |
| FD2 | What is the tongue width? | The 6.2 mm is the slot **opening**; the tongue is **6.0 ± 0.05** wide (0.2 total, 0.1 per side, band 0.05–0.15 per side). | 'A 6.2 mm slot-engagement tongue that slides in the slot with 0.2 mm clearance': the tongue cannot be 6.2 wide in a 6.2 opening and slide with 0.2 mm clearance. Alternative reading (6.2 + 0.2 slot) would not fit a standard 2020 slot. |
| FD3 | Where does the bolt pass through the tongue? | The tongue is two **pads** with a **relief** between them (relief 10.0 long (band 9.0–12.0), pads 7.0 each, overall 24.0 along Z). The bolt passes in the relief; the tongue has no hole. | The 6.0 wide tongue cannot hold a Ø5.5 hole (0.25 of material each side, below the 0.8 minimum feature). |
| FD4 | Tongue depth? | 1.5 ± 0.1 below the shoulder plane (band 1.0–1.6). | It stays inside the 1.8 lip (the lip must be sandwiched between the shoulder and the nut) and keeps 0.3 above the nut's bearing plane. |
| FD5 | Bearing pocket? | A round pocket **Ø18.0** (radial side clearance 1.0 to the bearing OD 16.0) with an inner-ring seat boss of Ø7.2 (6.0 to 7.4) and **0.6** high (0.5 to 0.8), a floor 2.0 thick (≥ 2.0), depth 3.6 from the block's outer face. | '1 mm side clearance' read as radial clearance between the bearing's OD and the block, which is what makes the outer ring free. The boss lifts the ring 0.6 off the floor so only the inner ring is clamped. |
| FD6 | Block outline? | 24.0 (Y) × 24.0 (Z) plan, 5.6 thick above the shoulder plane plus the tongue (7.1 overall in X); band ±0.5. | Wall round the Ø18.0 pocket in plan 3.0 (12.0 − 9.0). |
| FD7 | Print orientation? | Free, declared in `layout.json`. The sketch uses Z up (slot direction vertical): everything is extruded along Z except the horizontal bearing pocket and the relief between the pads (both exempt, A8). | In that orientation the tongue pads, floor, walls and boss are overhang-free. |

---

## 4. Requirements tree

### L1.1 The block, bearing, bolt and T-nut are placed on the extrusion's slot by their datums

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: the block's position along the extrusion, the bearing, the bolt (with its length) and the nut. | inspection | `layout.json` present and parses; names `extrusion_2020`, `tnut_2020_m5`, `bearing_625`, `bolt_m5_iso7380` (with length); gives z0 and the print orientation | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 |  |
| L3.1.1.2 | The declared pose verifies under the seating rule. | analysis | shoulder plane on X = 10.0 ≤ 0.05; axis on Y = 0 ≤ 0.15; bearing face A on the boss top ≤ 0.10; head on face B ≤ 0.10 | 3 |  |
| L2.1.2 | The assembled parts do not collide, except at designed contact. | analysis | every pair of RBA parts and the block: intersection ≤ 0.01 mm³ outside the contact list | 3 | |
| L3.1.2.1 | Pairwise interference of M-EXT, M-NUT, M-BRG, M-BOLT and the block. | analysis | ≤ 0.01 mm³ each pair | 3 |  |

### L1.2 The bearing is carried on the M5 bolt

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The bearing is coaxial with the bolt and the bolt hole. | analysis | M-BRG axis, M-BOLT axis and V-BOLT-HOLE axis coincide within 0.10; hole Ø5.5 ± 0.10 | 3 | |
| L3.2.1.1 | Bolt hole inscribed diameter at mid-length. | inspection | 5.5 ± 0.10 | 3 |  |
| L3.2.1.2 | Axis offset between the bolt hole and the declared bearing axis. | analysis | ≤ 0.10 | 3 | G2 |
| L2.2.2 | The inner ring is clamped between the head and the boss, and only the inner ring. | analysis | boss Ø 6.0–7.4 (touches the inner ring land r 2.5–4.0 only); boss height 0.6 (0.5–0.8); head bearing on face B; face A on the boss top | 3 | |
| L3.2.2.1 | Boss outer diameter and height. | inspection | 6.0 ≤ Ø ≤ 7.4; 0.5 ≤ h ≤ 0.8 | 3 | G2 |
| L3.2.2.2 | Planarity of the boss top and its distance to bearing face A. | analysis | flatness ≤ 0.10; face A on the top within 0.10 | 2 |  |
| L3.2.2.3 | The bolt's shank passes the bore without touching the boss or the block hole's wall except at the hole's radial play. | analysis | radial gap bolt/hole ≥ 0.20; shank in bore (designed contact) | 2 |  |

### L1.3 The bearing's outer ring spins free with 1 mm side clearance

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Radial side clearance to the block is 1.0. | analysis | radial distance, measured in the YZ section at each X from 12.6 to 15.6 (the pocket wall, floor excluded), from V-RING's outer circle (r 8.0) to the block: 1.00 (0.95 to 1.30) | 3 | |
| L3.3.1.1 | Pocket diameter (inscribed circle of V-POCKET). | inspection | 18.0 ± 0.10 (so side clearance 1.0) | 3 | G3 |
| L3.3.1.2 | Minimum radial distance V-RING to the block (YZ section per X; the floor's axial gap is L3.3.2.1). | analysis | 0.95 ≤ c ≤ 1.30 | 3 | G3 |
| L2.3.2 | The ring does not touch the floor, the boss or the bolt head. | analysis | clear_of(block ∪ M-BOLT, V-RING, 0.5) | 3 | |
| L3.3.2.1 | Axial gap from bearing face A to the pocket floor (X = 12.0). | analysis | ≥ 0.5 (nominal 0.6) | 3 |  |
| L3.3.2.2 | Distance from M-BOLT's head to V-RING (radially, head r 4.75 to ring r 6.0). | analysis | ≥ 0.5 | 2 |  |
| L2.3.3 | The ring's outside is accessible for a belt. | inspection | M-BRG's OD cylinder protrudes ≥ 1.5 above the block's outer face; no block material beyond the pocket rim in the protruding band | 2 | |
| L3.3.3.1 | Protrusion of the bearing OD above the block's outer face. | inspection | ≥ 1.5 (nominal 2.0) | 2 |  |
| L3.3.3.2 | Block material within r 8.0 + 0.5 of the axis above the pocket rim. | analysis | none | 1 |  |

### L1.4 The tongue enters the slot's 6.2 mm opening

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Tongue width and depth. | inspection | width 6.0 ± 0.05; depth 1.5 (1.0–1.6), measured below the shoulder plane | 3 | |
| L3.4.1.1 | Tongue width (distance between its two side faces, both pads). | inspection | 6.0 ± 0.05 | 3 | G4 |
| L3.4.1.2 | Tongue depth below the shoulder plane. | inspection | 1.0 ≤ d ≤ 1.6 (nominal 1.5; tongue end X = 10.0 − d ≥ 8.4 keeps 0.2 to the nut) | 3 |  |
| L2.4.2 | Two pads with a relief for the bolt. | inspection | two pads, each ≥ 6.0 long (Z); relief 9.0–12.0 long (nominal 10.0; 9.0 = 2 × (shank r 2.5 + 2.0)); overall length 24.0 ± 0.5; the pads are on both sides of the bolt axis | 3 | |
| L3.4.2.1 | Number, length and spacing of the pads along Z. | inspection | 2; ≥ 6.0 each; relief 9.0–12.0 | 3 |  |
| L3.4.2.2 | Clearance between the bolt shank (r 2.5) and the pads. | analysis | ≥ 2.0 | 2 |  |
| L2.4.3 | The tongue is one with the block. | analysis | tongue fused to the block (one shell); shoulder is flat | 2 | |
| L3.4.3.1 | The block is one connected shell. | analysis | 1 shell (see the printability L1) | 2 |  |

### L1.5 The tongue slides in the slot with 0.2 mm clearance

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Clearance in the slot opening. | analysis | min distance from the tongue's side faces to the slot opening faces 0.05–0.15 per side (total 0.10–0.30) | 3 | |
| L3.5.1.1 | Gap to the opening faces, both sides, both pads. | analysis | 0.05 ≤ g ≤ 0.15 per side; total 0.20 ± 0.10 | 3 | G4 |
| L2.5.2 | The block slides along the slot. | test | sweep(block, V-SLIDE, M-EXT): intersection ≤ 0.01 mm³ at every 1.0 step from −15.0 to +15.0 | 3 | |
| L3.5.2.1 | Slide sweep of the block along Z against the real slot profile. | test | penetration ≤ 0.01 mm³ at every step | 3 | G6 |
| L3.5.2.2 | Tongue clear of the lips' underside and the nut. | analysis | tongue end X ≥ 8.2 + 0.2 (nominal 8.5): distance to M-NUT ≥ 0.2 | 2 |  |

### L1.6 The block sits flat and square on the extrusion face

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | The shoulder is flat and on the face. | inspection | V-SHOULDER flatness ≤ 0.10; on X = 10.0 within 0.05; contact area ≥ 100 mm² | 3 | |
| L3.6.1.1 | Flatness and position of V-SHOULDER. | inspection | ≤ 0.10; ≤ 0.05 | 3 |  |
| L3.6.1.2 | Area of V-SHOULDER that lies on the extrusion face (\|Y\| ≤ 10). | analysis | ≥ 100 mm² | 2 |  |
| L2.6.2 | The bolt axis is square to the face and on the slot centre. | analysis | angle 90° ± 0.5° to the face; axis on Y = 0 within 0.15 | 3 | |
| L3.6.2.1 | Angle between the bolt hole axis and the face normal. | analysis | ≤ 0.5° | 3 |  |
| L3.6.2.2 | Position of the axis relative to `SLOT_PX`. | analysis | Y offset ≤ 0.15 | 3 |  |

### L1.7 One M5 bolt clamps the block into the T-nut

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Thread engagement in the nut and tip clearance. | analysis | tip X = 17.6 − L; engagement = 8.2 − tip X ≥ 2.4 and ≤ 3.5; tip ≥ slot floor + 0.5 (X ≥ 4.4) | 3 | |
| L3.7.1.1 | Engagement of M-BOLT in M-NUT. | analysis | 2.4 ≤ e ≤ 3.5 (nominal 2.6 for L = 12.0) | 3 | G5 |
| L3.7.1.2 | Tip to slot floor. | analysis | ≥ 0.5 (nominal 1.7) | 3 | G5 |
| L2.7.2 | The nut fits behind the lips and is not blocked by the tongue. | analysis | M-NUT inside the undercut; distance to the tongue ≥ 0.2; bolt clears the lip opening ≥ 0.3 | 2 | |
| L3.7.2.1 | Nut within the interior undercut and under the lips. | analysis | penetration ≤ 0.01 mm³; bearing plane at X = 8.2 ± 0.05 | 2 |  |
| L3.7.2.2 | Bolt shank to the lip opening faces. | analysis | ≥ 0.3 (shank Ø5.0 in 6.2: 0.6) | 2 |  |
| L2.7.3 | The clamp load path is closed. | analysis | stack head → inner ring → boss → block → extrusion lips ← nut has no gap above 0.1 at designed contacts | 2 | |
| L3.7.3.1 | Gaps along the stack (head bearing, face B/A, boss, shoulder). | analysis | each designed contact within 0.10 | 2 |  |

### L1.8 The bolt can be turned

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Driver access above the bolt. | analysis | clear_of(ALL, V-DRIVER, 0.0) | 2 | |
| L3.8.1.1 | The Ø9.5 × 25.0 tool column above the head is free of printed material. | analysis | penetration ≤ 0.01 mm³ | 2 |  |

### L1.9 A compact block with enough material everywhere

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | Size limit. | inspection | Y ≤ 30.0, Z ≤ 30.0, X ≤ 12.0 (tongue tip to outer face) | 1 | |
| L3.9.1.1 | Bounding box of the block. | inspection | as L2 (nominal 24.0 × 24.0 × 7.1) | 1 |  |
| L2.9.2 | Wall round the pocket and floor thickness. | inspection | wall ≥ 2.0 in plan (nominal 3.0); floor ≥ 2.0; no feature thinner than 0.8 | 2 | |
| L3.9.2.1 | Minimum wall between the pocket and the block's outer edges. | analysis | ≥ 2.0 | 2 |  |
| L3.9.2.2 | Floor thickness under the pocket. | inspection | ≥ 2.0 | 2 |  |
| L3.9.2.3 | Thin-feature scan. | analysis | ≥ 0.8 | 1 |  |

### L1.10 Printable on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | One manifold body. | analysis | 1 shell; manifold3d accepts it | 3 | |
| L3.10.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.10.2 | No unsupported overhang in the declared orientation. | analysis | 0 offending faces (area > 1 mm²) steeper than 45° from vertical, except round holes with horizontal axis Ø ≤ 20 (A8) and bridges ≤ 15 | 2 | |
| L3.10.2.1 | Overhang and bridge scan per patch. | analysis | as L2 | 2 |  |
| L3.10.2.2 | Bed contact in the declared orientation. | analysis | ≥ 50% of the plan bounding box | 1 |  |
| L2.10.3 | Build volume. | inspection | bounding box ≤ 200 per axis | 1 | |
| L3.10.3.1 | Bounding box. | inspection | ≤ 200 per axis | 1 |  |

### L1.11 The delivered package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | The package holds `block.stl`, the `.scad` source, `layout.json` and the agent's report. | inspection | all present and readable | 3 | |
| L3.11.1.1 | Files present and parse; STL in mm: largest bounding-box axis within 20–200 (a thin axis is not a units error). | inspection | true | 3 | G0 |
| L2.11.2 | The agent's report agrees with the judge. | analysis | for every clearance / engagement / width number reported: pass/fail the same and \|d_agent − d_judge\| ≤ 0.05 | 1 | |
| L3.11.2.1 | Self-report against the judge. | analysis | 100% within 0.05 | 1 |  |

---

## 5. Counts and gates

L1: 11. L2: 25. L3: 42.

Gates (a failing gate makes the design WRONG regardless of score):

- **G0** package present and readable: L3.11.1.1
- **G1** one manifold body: L3.10.1.1
- **G2** bearing coaxial with the bolt and clamped by the boss: L3.2.1.2, L3.2.2.1
- **G3** outer ring free: side clearance 1.0: L3.3.1.1, L3.3.1.2
- **G4** tongue 6.0 wide with 0.2 total clearance: L3.4.1.1, L3.5.1.1
- **G5** bolt reaches the nut without bottoming: L3.7.1.1, L3.7.1.2
- **G6** block slides along the slot: L3.5.2.1

---

## 6. Feasibility

A concrete design exists (extrusion frame, z0 = 30.0, mm; all numbers are arithmetic-checked):

- **Slot:** face X = 10.0, opening |Y| < 3.1 from X = 10.0 to 8.2, undercut |Y| < 5.5 from X = 8.2 to the floor at 3.9.
- **T-nut:** 3.5 thick, X 4.7 to 8.2 (bearing plane 8.2 against the lips), 10.0 across (< 11.0), 9.7 along Z.
- **Block:** plan 24.0 (Y) × 24.0 (Z), centred on (Y 0, Z 30.0); shoulder plane X = 10.0; floor X 10.0 to 12.0 (2.0); pocket Ø18.0 from X 12.0 to 15.6 (3.6 deep; wall in plan 12.0 − 9.0 = 3.0); seat boss Ø7.2 from X 12.0 to 12.6; bolt hole Ø5.5 through boss and floor.
- **Tongue:** two pads, each Y ±3.0 (6.0 wide: 0.1 per side in the 6.2 opening), X 8.5 to 10.0 (1.5 deep: inside the 1.8 lip and 0.3 above the nut), Z 30.0 ± (5.0 to 12.0) (relief 10.0, pads 7.0, overall 24.0). The nut's half-length along Z (4.85) is below the pad start (5.0).
- **Bearing:** X 12.6 to 17.6; radial clearance to the pocket wall (18.0 − 16.0)/2 = 1.0; axial gap to the floor 0.6; protrudes 17.6 − 15.6 = 2.0 above the block.
- **Bolt:** M5 × 12.0, head X 17.6 to 20.35, tip at 17.6 − 12.0 = 5.6: engagement 8.2 − 5.6 = 2.6 (2.4 to 3.5), tip 5.6 − 3.9 = 1.7 above the slot floor, shank passes the Ø5.5 hole with 0.25 radial play and the 6.2 opening with 0.6.
- **Head vs outer ring:** head r 4.75, outer ring r from 6.0: gap 1.25.
- **Print:** Z up (slot direction vertical): the block is then a constant-profile extrusion in XY except the Ø18 horizontal pocket (exempt up to Ø20 by A8), the tongue pads hang off the shoulder plane which is vertical; the only downward face is the upper pad's end face at the relief, a 1.5 deep step (exempt up to 2.0, A8); bed contact is the −Z face (block 7.1 × 24.0, about 84% solid at that level: (5.6 × 24.0 + 1.5 × 6.0) / (7.1 × 24.0)).
- **Size:** 24.0 × 24.0 × 7.1 within 30 × 30 × 12. Shoulder contact area on the profile face ≈ (20.0 − 6.2 opening) × 24.0 = 331 mm² ≥ 100 (the tongue pads fill the opening, not the face).

All numbers agree with the request (625: 5 × 16 × 5; 6.2 slot; 0.2 clearance; 1 mm side clearance) and with the catalogue (`extrusion_2020` opening 6.2, depth 6.1, lip 1.8, interior 11.0; `tnut_2020_m5` 10.0 × 9.7 × 3.5; `bolt_m5_iso7380` Ø5.0, head Ø9.5 × 2.75; `bearing_625` 5 × 16 × 5).
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
3. **Normalise the frame.** Put the block on the +X slot of the extrusion frame (1.1): shoulder plane X = 10.0, bolt axis along X on Y = 0. Rotations by multiples of 90° and mirroring only; record the transform.
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

Gates: G0 package present and readable; G1 one manifold body; G2 bearing coaxial with the bolt and clamped by the boss; G3 outer ring free: side clearance 1.0; G4 tongue 6.0 wide with 0.2 total clearance; G5 bolt reaches the nut without bottoming; G6 block slides along the slot.

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
| Bolt hole Ø; axis offset (L3.2.1.x), mm | 5.5 ± 0.10; ≤ 0.10 | |
| Boss Ø, height (L3.2.2.1), mm | 6.0–7.4; 0.5–0.8 | |
| Pocket Ø; radial side clearance (L3.3.1.x), mm | 18.0 ± 0.10; 0.95–1.30 | |
| Axial gap to floor; head to ring (L3.3.2.x), mm | ≥ 0.5; ≥ 0.5 | |
| Bearing protrusion (L3.3.3.1), mm | ≥ 1.5 | |
| Tongue width; depth (L3.4.1.x), mm | 6.0 ± 0.05; 1.0–1.6 | |
| Pad count, relief, bolt clearance (L3.4.2.x), mm | 2; 9.0–12.0; ≥ 2.0 | |
| Gap to opening faces per side (L3.5.1.1), mm | 0.05–0.15 | |
| Slide sweep penetration (L3.5.2.1) | ≤ 0.01 mm³ at every step | |
| Shoulder flatness; contact area (L3.6.1.x) | ≤ 0.10; ≥ 100 mm² | |
| Bolt engagement; tip to slot floor (L3.7.1.x), mm | 2.4–3.5; ≥ 0.5 | |
| Driver column penetration (L3.8.1.1) | ≤ 0.01 mm³ | |
| Bounding box; wall; floor (L3.9.x), mm | ≤ 30 × 30 × 12; ≥ 2.0; ≥ 2.0 | |
| Shells; overhang patches; bed contact (L3.10.x) | 1; 0; ≥ 50% | |
| Self-report agreement (L3.11.2.1) | 100% within 0.05 | |

---

## 8. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 (`design.json`) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1–L2.1.2 | L3.1.1.1, L3.1.1.2, L3.1.2.1 | L1.1 | inspection | "carries a 625 bearing on an M5 bolt", "bolts to the T-slot of a 2020 extrusion" |
| L1.2 | Bearing on the bolt | L2.2.1–L2.2.2 | L3.2.1.1, L3.2.1.2, L3.2.2.1, L3.2.2.2, L3.2.2.3 | L1.2 | analysis | "carries a 625 bearing ... on an M5 bolt" |
| L1.3 | Free spin | L2.3.1–L2.3.3 | L3.3.1.1, L3.3.1.2, L3.3.2.1, L3.3.2.2, L3.3.3.1, L3.3.3.2 | L1.3 | analysis | "The bearing outer ring must spin free of the block with 1 mm side clearance" |
| L1.4 | Tongue | L2.4.1–L2.4.3 | L3.4.1.1, L3.4.1.2, L3.4.2.1, L3.4.2.2, L3.4.3.1 | L1.4 | inspection | "6.2 mm slot-engagement tongue" |
| L1.5 | Sliding fit | L2.5.1–L2.5.2 | L3.5.1.1, L3.5.2.1, L3.5.2.2 | L1.5 | test | "slides in the slot with 0.2 mm clearance" |
| L1.6 | Seating | L2.6.1–L2.6.2 | L3.6.1.1, L3.6.1.2, L3.6.2.1, L3.6.2.2 | L1.6 | inspection | "bolts to the T-slot" |
| L1.7 | Clamp stack | L2.7.1–L2.7.3 | L3.7.1.1, L3.7.1.2, L3.7.2.1, L3.7.2.2, L3.7.3.1 | L1.7 | analysis | "bolts to the T-slot", "on an M5 bolt" |
| L1.8 | Tool access | L2.8.1–L2.8.1 | L3.8.1.1 | L1.8 | analysis | "bolts" |
| L1.9 | Size and walls | L2.9.1–L2.9.2 | L3.9.1.1, L3.9.2.1, L3.9.2.2, L3.9.2.3 | L1.9 | inspection | (implied: a small idler block) |
| L1.10 | Printable | L2.10.1–L2.10.3 | L3.10.1.1, L3.10.2.1, L3.10.2.2, L3.10.3.1 | L1.10 | analysis | "printed" (implied) |
| L1.11 | Evidence | L2.11.1–L2.11.2 | L3.11.1.1, L3.11.2.1 | L1.11 | inspection | (not the owner's words; needed by the judge) |

---

## Audit

Adversarial audit (second agent). Recomputed the X stack (nut 4.7 to 8.2, lips 8.2 to 10.0, floor 10.0 to 12.0, boss to 12.6, bearing 12.6 to 17.6, head to 20.35, bolt tip 17.6 − 12.0 = 5.6, engagement 2.6, tip 1.7 above the floor), the pocket (Ø18.0, wall 3.0, depth 3.6, protrusion 2.0), the block size (7.1 × 24.0 × 24.0) and the slide range (z0 27 to 33 inside the 60 length). The four parts load (`extrusion_2020`, `bolt_m5_iso7380` and the others need their `length` from the request/layout, as designed). L1 = 11, L2 = 25, L3 = 42 match section 5 and the traceability.

| # | Defect found | Fix |
|---|---|---|
| 1 | The request never gave the extrusion length (the catalogue part requires it from the request) yet the slide sweep and A1 depend on 60.0. | Request now says "Model the extrusion as a 60 mm length, with the block nominally at its middle" (also in `design.json`); A1 gives the legal z0 range 27.0 to 33.0. |
| 2 | The bearing's inner-ring land (r 4.0) and outer-ring land (r 6.0) drive G2 (boss Ø 6.0–7.4) and the head/ring checks but appeared nowhere in the catalogue. | Added `inner_ring_land_diameter` 8.0 and `outer_ring_land_diameter` 12.0 to `parts/bearing_625/part.json` (sourced, ±0.5). `validate` still passes. |
| 3 | L3.3.1.2 "minimum distance from V-RING to the block" is 0.6 (the floor gap) if read literally, outside its own 0.95–1.30 band: the criterion contradicted the nominal design. | Redefined as the radial distance in the YZ section at each X from 12.6 to 15.6 (pocket wall, floor excluded). The floor gap stays in L3.3.2.1 (≥ 0.5). |
| 4 | Tongue depth band 1.0–1.7 allowed a tongue end at X 8.3, 0.1 from the nut, while L3.5.2.2 / L2.7.2 need ≥ 0.2. | Band is now 1.0–1.6 (L2.4.1, L3.4.1.2, FD4, 7.5 table). |
| 5 | Relief band 8.0–12.0 contradicted L3.4.2.2 (shank r 2.5 + 2.0 clearance needs a relief ≥ 9.0). | Band is now 9.0–12.0 (L2.4.2, L3.4.2.1, FD3, 7.5 table). |
| 6 | The relief's upper pad face is a 1.5 deep downward step (about 9 mm²) in the Z-up print orientation; the 1 mm² overhang rule would fail every design, and the sketch claimed "everything is extruded along Z". | A8 and the print note now exempt a downward step of at most 2.0 deep (tongue relief edge, 1.5); the sketch text says the relief is exempt. Bed contact recomputed: about 84%. |
| 7 | Shoulder contact area was computed as 24 × 20 − pads = 396; the profile face has the 6.2 opening, so the area is (20.0 − 6.2) × 24.0 = 331. | Corrected (gate unaffected, limit 100). |
| 8 | Numbers the judge needs but the agent was never told: boss Ø and height, pad length and relief, belt protrusion 1.5 (the request never mentioned a belt), tip clearance 0.5, "axial" clearance to the head that is really radial, sliding "without touching" although the shoulder rests on the face. | Added to L1.2, L1.3, L1.4, L1.5, L1.7, L1.9 and to the request ("a belt runs on its outer ring"). |
| 9 | Not fixed (shared catalogue file): `tnut_2020_m5/part.json` `min_engagement` 5.0 (one diameter) is impossible in a 3.5 mm nut and its `screw_tip` keep-out reaches into the extrusion body; G19 needs 2.4 to 3.5. Used by G21, G22, G24 too. | Section 7.3 precedence (this file beats `part.json`) already applies; recorded as an open catalogue problem. |

Residual uncertainty: the nut's thread region is a solid plate in the catalogue (the bolt shank in it is a listed designed contact); inner and outer ring lands are typical values, not datasheet values.
