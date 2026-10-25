# G30 60 mm fan to heatsink duct: requirements (L1 / L2 / L3)

A training entry of the generalization benchmark (`benchmarks/generalize/`), modelled on E1-01
(`benchmarks/enclosure/requirements.md`). The machine-readable request (L1 only, `dev.json` format) is
`design.json` next to this file. This file holds the L2/L3 tree, the reference models, the assumptions, the fixed decisions, a feasibility sketch, the traceability and the design-specific judging rules (section 8). Catalogue parts:
`benchmarks/generalize/parts/` (`fan_60x60x25`, `generic_box`, `bolt_m4_iso4762`). No number here may appear in agent logic: they live in the request, this file, `design_rules.json` generic values and `part.json` data.

**Request (plan brief, verbatim):** "A duct that connects a 60 x 60 x 25 mm fan (50 mm hole pitch) to a 50 x 20 mm heatsink 30 mm tall, at the heatsink's leading face. The fan blows through a smoothly changing section into the heatsink fins with 1 mm side seals. I need to reach the fan screws with a driver from above."

**Expanded request** (the text the agent gets, `design.json`): A duct that connects a 60 x 60 x 25 mm fan (mounting holes on a 50 mm square pitch) to a 50 x 20 mm heatsink that is 30 mm tall. The fan sits on top and blows straight down; the heatsink stands below it with its fins running vertically, so the heatsink's leading face is its 50 x 20 mm top face and the duct meets it there. The air goes through a smoothly changing section from the fan to the heatsink and enters the fins with side seals of 1 mm at most (the duct's outlet slips over the top of the heatsink and the gap to its sides stays between 0.2 and 1 mm). Four M4 socket-head bolts hold the fan, through the fan's holes into the duct, and I need to reach those four screws with a hex driver from above. One printed duct on an FDM printer in PLA without supports, wall at least 1.6 mm.

**How to read this.** L1 says what the owner needs; L2 turns it into an engineering requirement with numbers; L3 is a concrete check Python can run on the delivered STL. Each row has a method, a pass/fail criterion with a number and tolerance, a weight (3 critical, 2 major, 1 minor) and, for must-pass rows, a gate mark. Numbers that come from an assumption (section 3) are provisional until Robin confirms them. Do not relax a criterion because a design fails it.

---

## 1. Frames, tolerances and the interference checks

### 1.1 Frames

- **Duct frame (all tables below):** **Z up, the air going down (−Z)**; origin at the **centre of the heatsink's leading (top) face**, so the heatsink occupies X ±25, Y ±10, Z −30 to 0 and the leading plane is Z = 0. The fan sits above on the same axis; its exhaust face is the plane Z = H (declared, H in [24, 40]) and its intake face Z = H + 25. A design delivered in another orientation is normalised into this frame before grading (rubric step 3): rotations by multiples of 90° and mirroring only, never penalised.
- The duct is graded as the single STL `duct.stl` placed in this frame.

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within ε (a "≥ 0.50" limit passes at 0.48) |
| angle | 0.5° | same |
| interference volume | 0.01 mm³ | "no interference" means intersection volume ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the hole's section (what a screw or pin sees) | |
| boss / standoff / stem OD | smallest enclosing circle of the section | |
| fitted circle (a bore) | least-squares circle through the section points of the arc | |

Where a criterion is written "nominal ± t", t is the design tolerance and ε is added to it.

### 1.3 The two interference checks

Fit, access and clearance requirements are written, wherever possible, as one of two checks
against named reference models (M-) and envelope volumes (V-) from section 2. The grader runs
its own implementation (section 8); a design may and should generate the same volumes for its own
checks, but its copies are not trusted for grading.

- **`clear_of(bodies, volume, clearance)`**: the minimum Euclidean distance between every printed
  body in `bodies` and `volume` is ≥ `clearance`. Reported value: the signed minimum distance d
  (negative = the body penetrates the volume; the penetration volume is reported too). Pass:
  penetration ≤ 0.01 mm³ and d ≥ clearance − ε.
- **`inside(volume, cavity, clearance)`**: `volume` lies entirely in `cavity`, and every point of it
  is ≥ `clearance` from the cavity's boundary. Pass: d ≥ clearance − ε.

**Designed contact is not interference (Robin's rule, 2026-10-24).** Parts that are meant to touch
are excluded from every interference and clearance check. For this design the designed-contact
pairs are:
- the flange face on the fan's exhaust face (plane contact)
- an M4 bolt in its pilot: the thread interference of Ø4.0 in the pilot (tap diameter 3.3) is designed contact, up to π/4 × (4.0² − 3.1²) per mm of engagement; the bolt head on the fan's intake face
- an M4 shank in the fan's Ø4.3 hole (clearance, not contact)

For these pairs only penetration counts (an intersection volume above 0.01 mm³, unless the pair
is given a larger allowance below). A distance of zero is a pass.

`bodies` is the duct (the only printed body); `clear_of(duct, volume, c)` is written without the first argument where it is unambiguous.

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` in `benchmarks/generalize/parts/<part_id>/`. The only place part numbers may live.
- **envelope**: a keep-out, sweep or access volume generated by Python from datums. Never drawn by hand.
- **computed**: derived from the design (slices, passage, gaps).

### 2.2 Reference models (M-)

Positions are the **declared layout**; the table gives the sketch's values (section 6).

| Name | What | Source | Size and position (duct frame, mm) | Datums |
|---|---|---|---|---|
| **M-FAN** | 60 × 60 × 25 DC axial fan, airflow down | catalogue `fan_60x60x25`, placed with its +Z airflow flipped to −Z | frame 60 × 60 × 25; X, Y ±30; exhaust face Z = H = 28, intake face Z = 53; four holes Ø4.3 at (±25, ±25); air bore Ø58; screw-head keep-out Ø8.0 | `AIRFLOW` (axis, −Z), `EXHAUST_FACE`, `INTAKE_FACE`, `HOLE` (4 axes) |
| **M-HS** | heatsink, solid envelope | catalogue `generic_box` (size_x 50, size_y 20, size_z 30) | X ±25, Y ±10, Z −30 to 0; fins along Z (not modelled) | `TOP` (leading plane Z = 0), `CENTRE` |
| **M-BOLT4-k** (k = 1..4) | M4 socket-head bolt | catalogue `bolt_m4_iso4762` (length declared, L) | shank Ø4.0, head Ø7.0 × 4.0, tool access 25; head bearing on the intake face Z = 53, axis −Z at the fan holes; L = 30 in the sketch (tip Z 23) | `HEAD_BEARING`, `HEAD_TOP`, `TIP`, `AXIS` |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Definition (duct frame, mm) |
|---|---|---|
| **V-FAN-INTAKE** | free air in front of the fan | Ø58 column on the fan axis from the intake face (Z = H + 25) up 15 (catalogue `intake_clearance`) |
| **V-DRIVER-k** | hex driver on a fan screw | Ø6.0 column on the bolt axis from the head top (Z = H + 29) up 25 (catalogue `tool_access_height`) |
| **V-PASSAGE** | the air passage | computed: the connected inner void of the duct between the flange face and the end of the sleeve, sliced on horizontal planes every 1.0 |
| **V-SEAL-n** (n = 1..4) | the gap between the sleeve and one heatsink side | computed: ray casting from each heatsink side face outward to the sleeve's inner face, at every 1.0 mm below the leading plane |
| **V-AP-OTHER** | every other opening | computed: every through-path from outside into the passage other than the inlet (at the fan face) and the outlet (the heatsink end of the sleeve) |
| **V-BOLT-PATH-k** | bolt insertion | M-BOLT4-k's solid swept straight down from 25 above its seat |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-FAN, M-HS | units and size | fan 60.0 × 60.0 × 25.0 ± 0.1; heatsink 50.0 × 20.0 × 30.0 ± 0.05 |
| R2 | M-FAN | hole pattern, bore, airflow | holes Ø4.3 on 50.0 ± 0.05; bore Ø58 ± 0.5; `AIRFLOW` along −Z after flipping |
| R3 | M-BOLT4 | sizes | head Ø7.0 × 4.0; shank Ø4.0 ± 0.05 |
| R4 | M-FAN, M-HS, M-BOLT4 at the declared poses | no collisions | ≤ 0.01 mm³ (designed-contact pairs excluded) |
| R5 | every V- envelope | datums equal the model datums it came from | ≤ 0.01 |

**Seating rule.** The grader verifies the declared layout: the duct's flange face lies on the fan exhaust plane (≤ 0.10), the pilot axes are coaxial with the fan holes (residual ≤ 0.15), the heatsink's top face on Z = 0 (≤ 0.05). If the declaration fails, the references are placed by that fit and the failing L3s stay failed.

---

## 3. Assumptions, fixed decisions and open questions

### 3.1 Assumptions (derived, with their uncertainty)

| # | Question | Value chosen | Why, and uncertainty |
|---|---|---|---|
| A1 | Which way does the air go, and which face is "leading"? | Straight down: fan on top, heatsink below with vertical fins; the leading face is the heatsink's 50 × 20 top face. | Needed for "reach the fan screws from above" and a smooth section without an elbow. **Alternative:** horizontal flow with an elbow, not graded. Medium uncertainty. |
| A2 | Heatsink model? | A solid 50 × 20 × 30 box (catalogue `generic_box`); fins are not modelled; the leading face is its top. | The brief gives only the outline. Low uncertainty. |
| A3 | What is a "1 mm side seal"? | The outlet sleeve slips over the heatsink's top with a gap of 0.2 to 1.0 to each of the four sides over 5 to 15 mm of overlap (no more than the 1 mm in the brief, enough for printing tolerance). | **Alternative:** a 1.0 mm thick printed lip; not graded. Medium uncertainty. |
| A4 | Fan data? | Frame 60 × 60 × 25, holes Ø4.3 on 50.0, air bore Ø58 (±1), intake free clearance 15 (catalogue). | Datasheet class of Sunon/Delta/Nidec fans; the bore and the free clearance are estimates. |
| A5 | How is the fan held? | Four M4 socket-head bolts from the fan's intake side through its holes into pilots Ø3.3 in the duct flange; engagement at least 5.0 (1.25 × thread), pilot depth at least 6.0. | The pattern is M4 (Ø4.3 holes); engagement is the plastic-thread convention (±1). |
| A6 | What does "from above" mean? | A Ø6.0 column, 25 long, along each bolt axis above its head. | Hex-key access (catalogue `tool_access_height`). |
| A7 | Walls? | At least 1.6 (four perimeters at 0.4); local thickness measured normal to the wall. | FDM convention. |
| A8 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed; overhang limit 45° from vertical; bed contact at least 25% (a flanged duct prints on its flange ring). | Common printers. |
| A9 | Size limit? | Printed duct ≤ 64 × 64 × 45. | The fan is 60 square; a tight duct is 60 × 60 × 34 (section 6). |
| A10 | Alignment? | Fan axis within 1.0 of the heatsink face centre. | Straight transition without an offset. |
| A11 | Transition height? | H (exhaust face to leading plane) in [24, 40]. | A ≤ 45° wall needs at least 17.1 for the (55 − 20.8)/2 Y change of the sketch's inlet, plus the 6.0 flange. |

### 3.2 Fixed decisions (a choice that would otherwise be ambiguous)

| # | Decision |
|---|---|
| F1 | The duct is one printed body. |
| F2 | The bolts go from the fan's intake side, down through the fan, into the flange pilots; nothing is placed above the fan. |
| F3 | The default print orientation is flange face down; a design may state another and is graded on it. |
| F4 | The passage's inlet is the opening at the flange face; its outlet is the opening at the end of the sleeve; the leading plane is Z = 0. |

---

## 4. Requirements tree

### L1.1 Layout declared: fan above, heatsink below, in line

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares the pose of the fan, the heatsink and the four bolts in the duct frame. | inspection | `layout.json` present, parses, names `fan_60x60x25`, the heatsink `generic_box` (50 × 20 × 30), four `bolt_m4_iso4762` with their lengths | 3 |  |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | parse errors = 0; unknown ids = 0; bolt entries = 4 | 3 | G0 |
| L2.1.2 | Airflow is straight down: the fan's `AIRFLOW` axis points along −Z and the heatsink's fins run along Z. | inspection | `AIRFLOW` within 1.0° of −Z; heatsink box X 50 × Y 20 × Z 30 with its top face at the declared leading plane | 3 |  |
| L3.1.2.1 | Airflow direction and heatsink orientation. | inspection | ≤ 1.0°; sizes ± 0.05 | 3 |  |
| L2.1.3 | The fan and the heatsink are in line: the fan axis passes within 1.0 of the heatsink face centre, and the fan's frame is square to the heatsink's axes. | inspection | axis offset ≤ 1.0 in X and Y; rotation about Z multiple of 90° within 0.5° | 2 |  |
| L3.1.3.1 | Concentricity and squareness. | inspection | ≤ 1.0; ≤ 0.5° | 2 |  |
| L2.1.4 | The distance from the fan's exhaust face to the heatsink's leading face is small enough for a compact duct and large enough for a ≤ 45° transition. | inspection | H in [24, 40] | 2 |  |
| L3.1.4.1 | Exhaust-face to leading-face distance H. | inspection | 24.0 to 40.0 | 2 |  |
| L2.1.5 | No two reference parts collide. | analysis | fan ∩ heatsink ≤ 0.01 mm³ and fan, heatsink, bolts pairwise ≤ 0.01 mm³ (designed-contact pairs excluded) | 2 |  |
| L3.1.5.1 | Pairwise interference of the reference parts. | analysis | each pair ≤ 0.01 mm³ | 2 |  |

### L1.2 Flange sits on the fan's exhaust face on the 50 mm bolt pattern

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The flange face is one plane on the fan's exhaust face, with enough contact area. | inspection | flatness ≤ 0.10; plane within 0.05 of the exhaust-face plane; contact area ≥ 800 mm² | 3 |  |
| L3.2.1.1 | Flange face flatness and position. | inspection | ≤ 0.10; ≤ 0.05 | 3 | G2 |
| L3.2.1.2 | Contact area with the fan face. | analysis | ≥ 800 mm² | 2 |  |
| L2.2.2 | The flange outline follows the fan's: 60 × 60 within 1.0 on every side, centred on the fan axis within 0.5. | inspection | plan outline at the mating face 60.0 ± 1.0 (X and Y); centre offset ≤ 0.5 | 2 |  |
| L3.2.2.1 | Flange outline. | inspection | 60.0 ± 1.0; ≤ 0.5 | 2 |  |
| L2.2.3 | Four pilots, one under each fan hole, on the 50.0 mm square. | inspection | count = 4; each axis within 0.15 of its fan `HOLE` datum; pitch 50.0 ± 0.15 in X and in Y | 3 |  |
| L3.2.3.1 | Pilot count. | inspection | 4 | 3 | G2 |
| L3.2.3.2 | Pilot axes versus the fan holes. | analysis | each offset ≤ 0.15 | 3 | G2 |
| L3.2.3.3 | Pilot pitch. | inspection | 50.0 ± 0.15 in X and Y | 3 | G2 |

### L1.3 Inlet does not choke the fan

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Inlet opening at the flange. | inspection | largest inscribed circle of the inner opening at the flange face ≥ 54.0; area ≥ 85% of the bore area (Ø58: 2642 mm²), i.e. ≥ 2246 mm²; inlet within the fan bore + 1.0 | 3 |  |
| L3.3.1.1 | Inscribed circle of the inlet. | inspection | ≥ 54.0 | 3 |  |
| L3.3.1.2 | Inlet area. | inspection | 2246 to 3000 mm² | 2 |  |
| L2.3.2 | The inlet is centred on the fan axis. | inspection | inlet centroid within 0.5 of the fan axis | 2 |  |
| L3.3.2.1 | Inlet centring. | inspection | ≤ 0.5 | 2 |  |

### L1.4 Smoothly changing section from the fan to the heatsink

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The cross-section area of the passage is monotone from the inlet to the outlet. | analysis | area A(z) of the inner void on horizontal slices every 1.0 from the leading plane to the fan face: non-increasing towards the heatsink within 1%; excluded: the first 1.0 below the fan face (the bore-to-inlet step) | 3 |  |
| L3.4.1.1 | Monotone area profile. | analysis | A(z) never rises towards the heatsink by more than 1% | 3 | G3 |
| L2.4.2 | No abrupt change: the area changes by no more than 10% per 1.0 mm and the inner outline has no step. | analysis | max \|A(z+1) − A(z)\| / A(z) ≤ 10% (slices in the transition; a hull from a ≥ 54 inlet to the outlet over the shortest allowed transition, 18, reaches 9.1% at the narrow end); inner-outline offset between neighbouring slices 1.0 apart ≤ 1.5 (a 45° wall moves 1.0 per slice, so only a step exceeds it) | 2 |  |
| L3.4.2.1 | Area change per millimetre. | analysis | ≤ 10% | 2 |  |
| L3.4.2.2 | Inner-outline steps. | analysis | offset between slices 1.0 apart ≤ 1.5 | 2 |  |
| L2.4.3 | Inner wall slope: every inner face makes at most 45° with the Z axis. | analysis | every inner face with area > 1 mm² (in the transition) has an angle from vertical, asin(|n_z|) for its unit normal n, of at most 45° (+0.5°) | 3 |  |
| L3.4.3.1 | Maximum inner wall slope. | analysis | ≤ 45° | 3 | G3 |
| L2.4.4 | The transition is long enough to be gentle but not wasteful. | inspection | transition length (from the flange's bottom edge to the leading plane) in [18, 34] | 1 |  |
| L3.4.4.1 | Transition length. | inspection | 18 to 34 | 1 |  |
| L2.4.5 | The passage never narrows below the heatsink opening. | analysis | min A(z) over the passage ≥ 950 mm² (95% of the heatsink face, 50 × 20 = 1000) | 2 |  |
| L3.4.5.1 | Smallest passage area. | analysis | ≥ 950 mm² | 2 |  |

### L1.5 The passage ends at the heatsink's leading face and covers it

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The funnel ends on the leading plane: the passage reaches its outlet size at the leading plane. | analysis | plane Z of the end of the funnel (where the passage stops changing and the sleeve starts) within 0.3 of the leading plane | 3 |  |
| L3.5.1.1 | Funnel end on the leading plane. | analysis | ≤ 0.3 | 3 | G4 |
| L2.5.2 | The outlet opening covers the heatsink face with a small margin on every side, and is not much bigger. | analysis | inside(heatsink top face, outlet polygon at the leading plane, 0.2); outlet opening ≤ 52.0 × 22.0 | 3 |  |
| L3.5.2.1 | Heatsink face inside the outlet. | analysis | d ≥ 0.2 each side | 3 | G4 |
| L3.5.2.2 | Outlet not oversized. | analysis | ≤ 52.0 × 22.0 | 2 |  |
| L2.5.3 | The outlet is centred on the heatsink face. | inspection | outlet centre within 0.5 of the face centre; sides parallel to X and Y within 0.5° | 2 |  |
| L3.5.3.1 | Outlet centring and squareness. | inspection | ≤ 0.5; ≤ 0.5° | 2 |  |

### L1.6 Side seals of 1 mm at most round the heatsink

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Sleeve overlap along the heatsink sides. | analysis | overlap depth below the leading plane in [5.0, 15.0] on all four sides | 3 |  |
| L3.6.1.1 | Sleeve overlap depth. | analysis | 5.0 to 15.0 | 3 | G4 |
| L2.6.2 | The gap between the sleeve's inner faces and the heatsink's sides. | analysis | each of the four gaps (X sides, Y sides) in [0.2, 1.0] over the whole overlap (min, median, max by ray casting every 1.0 mm) | 3 |  |
| L3.6.2.1 | Gap on the two X sides. | analysis | 0.2 to 1.0 | 3 | G4 |
| L3.6.2.2 | Gap on the two Y sides. | analysis | 0.2 to 1.0 | 3 | G4 |
| L2.6.3 | The sleeve does not touch the heatsink. | analysis | clear_of(duct, M-HS, 0.2) | 3 |  |
| L3.6.3.1 | Duct to heatsink distance. | analysis | d ≥ 0.20 | 3 | G4 |

### L1.7 The duct keeps off the fan and the heatsink and leaves the fan's intake free

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The duct touches the fan only on the flange face. | analysis | duct ∩ M-FAN ≤ 0.01 mm³; contact only on the exhaust-face plane | 3 |  |
| L3.7.1.1 | Duct versus the fan body. | analysis | ≤ 0.01 mm³ | 3 | G2 |
| L2.7.2 | The fan's intake is free: nothing printed within the Ø58 column up to 15 above the intake face, and nothing above the fan's top face. | analysis | clear_of(duct, V-FAN-INTAKE, 0.0); no printed material above the fan's intake plane Z | 2 |  |
| L3.7.2.1 | Intake column clear. | analysis | d ≥ 0.0 | 2 |  |
| L2.7.3 | The duct stays out of the heatsink's body and below the leading face only as the sleeve. | analysis | duct ∩ M-HS ≤ 0.01 mm³ (also in L2.6.3); no printed material lower than the sleeve's end (leading plane − 15) | 2 |  |
| L3.7.3.1 | Duct versus the heatsink body. | analysis | ≤ 0.01 mm³ | 2 |  |

### L1.8 Four M4 bolts into pilots in the flange

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Pilots for M4 thread-forming in printed plastic (catalogue `tap_diameter` 3.3), deep enough and coaxial with the fan holes. | inspection | Ø 3.1 to 3.5; depth from the flange face ≥ 6.0; blind (do not open into the passage); coaxial with the fan hole ≤ 0.15 | 3 |  |
| L3.8.1.1 | Pilot diameter. | inspection | 3.1 to 3.5 | 3 | G5 |
| L3.8.1.2 | Pilot depth. | inspection | ≥ 6.0 | 3 | G5 |
| L3.8.1.3 | Pilot blind: no opening into the passage. | analysis | wall to the passage ≥ 1.5 | 3 |  |
| L2.8.2 | Each declared bolt engages its pilot enough and stops short of the end. | analysis | bolt at its declared pose: engagement in the flange ≥ 5.0; tip at least 0.5 above the pilot end; head bearing on the fan intake face within 0.10; bolt ∩ passage and ∩ fan frame (outside its hole) ≤ 0.01 mm³; thread interference with the pilot is designed contact | 3 |  |
| L3.8.2.1 | Engagement length. | analysis | ≥ 5.0 and ≤ pilot depth − 0.5 | 3 | G5 |
| L3.8.2.2 | Head seat. | inspection | ≤ 0.10 | 2 |  |
| L3.8.2.3 | Bolt versus passage. | analysis | ≤ 0.01 mm³ | 2 |  |
| L2.8.3 | Wall round each pilot. | analysis | ligament from the pilot to the outside of the flange ≥ 1.2 and to the passage ≥ 1.5 | 2 |  |
| L3.8.3.1 | Pilot ligaments. | analysis | ≥ 1.2 outside; ≥ 1.5 passage | 2 |  |

### L1.9 The four fan screws can be reached with a hex driver from above

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | A Ø6.0 driver column from each head top up 25 (catalogue `tool_access_height`) is clear of the duct, the fan and the heatsink. | test | clear_of(duct ∪ M-FAN ∪ M-HS, V-DRIVER-1..4, 0.0) | 3 |  |
| L3.9.1.1 | Driver columns clear. | test | d ≥ 0.0 for each of the four | 3 | G5 |
| L2.9.2 | The bolts can be inserted from above through the fan holes into the pilots. | test | bolt solid swept straight down from 25 above the head position to its seat: ∩ duct ∪ M-FAN ≤ 0.01 mm³ except the pilot (thread) contact at the end | 2 |  |
| L3.9.2.1 | Bolt insertion path. | test | ≤ 0.01 mm³ | 2 |  |

### L1.10 Closed passage, walls at least 1.6 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | The only openings into the passage are the inlet and the outlet. | analysis | V-AP-OTHER (every through-path into the passage other than the inlet and outlet) has 0 regions admitting a Ø1.0 sphere | 3 |  |
| L3.10.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 3 |  |
| L2.10.2 | Wall thickness measured normal to the wall. | analysis | min local normal thickness ≥ 1.6 away from the flange block, pilots and edges | 3 |  |
| L3.10.2.1 | Minimum wall thickness. | analysis | ≥ 1.6 | 3 |  |
| L2.10.3 | The duct is one connected body. | analysis | 1 shell; manifold3d accepts it | 3 |  |
| L3.10.3.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |

### L1.11 Prints without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | In its stated print orientation (default: flange face down) no part has an unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12.0 and bridges ≤ 15.0. | analysis | 0 offending faces (area > 1 mm²) | 2 |  |
| L3.11.1.1 | Overhang and bridge scan. | analysis | 0 faces steeper than 45° with area > 1 mm²; every bridge ≤ 15.0; every round hole Ø ≤ 12.0 | 2 |  |
| L2.11.2 | The duct rests on a flat face in its print orientation. | analysis | bed contact ≥ 25% of the plan bounding box and ≥ 800 mm² | 1 |  |
| L3.11.2.1 | Bed-contact area. | analysis | ≥ 25% of the plan bounding box and ≥ 800 mm² | 1 |  |
| L2.11.3 | No feature thinner than 0.8; fits a 200 × 200 × 200 build volume. | analysis | min thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 |  |
| L3.11.3.1 | Thin-feature scan and bounding box. | analysis | min thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 |  |

### L1.12 Compact

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | Printed envelope. | inspection | X ≤ 64.0, Y ≤ 64.0, Z ≤ 45.0 | 1 |  |
| L3.12.1.1 | Bounding box of the duct. | inspection | X ≤ 64.0, Y ≤ 64.0, Z ≤ 45.0 | 1 |  |
| L2.12.2 | The duct is symmetric about the fan axis in plan. | inspection | bounding box centred on the fan axis within 1.0 | 1 |  |
| L3.12.2.1 | Plan symmetry. | inspection | ≤ 1.0 | 1 |  |

### L1.13 Package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | The package holds `duct.stl` (mm), the `.scad` source, `layout.json` (poses, bolt lengths, print orientation) and `report.json` (the agent's own checks). | inspection | all present and readable; the STL's largest bounding-box axis within 20 to 200 | 3 |  |
| L3.13.1.1 | Files present and parse; units are mm. | inspection | 4 of 4 files present; the STL's largest bounding-box axis within 20 to 200 | 3 | G0 |
| L3.13.1.2 | The declared layout verifies. | analysis | flange face on the fan exhaust plane ≤ 0.10; pilot axes on the fan holes ≤ 0.15; heatsink face on the leading plane ≤ 0.05 | 3 |  |
| L2.13.2 | The agent's own clearance report agrees with the judge's measurements. | analysis | for every clear_of / inside L3 the agent reports, same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 |  |
| L3.13.2.1 | Self-report versus judge. | analysis | 100% agreement within 0.10 | 1 |  |

---

## 5. Counts

| Level | Count |
|---|---|
| L1 | 13 |
| L2 | 39 |
| L3 | 51 (weight 3: 26, weight 2: 19, weight 1: 6; total weight 122) |


Gates (a failure makes a design WRONG regardless of score; section 8): **G0** package (L3.1.1.1, L3.13.1.1); **G1** manifold, one body (L3.10.3.1); **G2** fan interface: flange face, pilots, no collision with the fan (L3.2.1.1, L3.2.3.1, L3.2.3.2, L3.2.3.3, L3.7.1.1); **G3** smooth transition: monotone area, slope ≤ 45° (L3.4.1.1, L3.4.3.1); **G4** outlet at the heatsink face with side seals (L3.5.1.1, L3.5.2.1, L3.6.1.1, L3.6.2.1, L3.6.2.2, L3.6.3.1); **G5** M4 bolts and driver access from above (L3.8.1.1, L3.8.1.2, L3.8.2.1, L3.9.1.1).

---

## 6. Feasibility: a design that meets every number

A concrete design in the duct frame, checked with a `manifold3d` model (one shell; no interference with the fan or the heatsink; bolts and intake column clear; no overhang other than the blind pilot ends).

| Feature | Value |
|---|---|
| Layout | heatsink X ±25, Y ±10, Z −30 to 0; fan X, Y ±30, Z 28 to 53 on the same axis (H = 28); bolts M4 × 30 at (±25, ±25), head bearing Z 53, tip Z 23 |
| Flange | 60 × 60 block Z 22 to 28 (6.0 thick); face Z 28 on the fan; inlet Ø55 (area 2376 mm², 90% of the bore, inscribed Ø55) |
| Pilots | four Ø3.3 from Z 28 down to Z 22 (depth 6.0); engagement 5.0; tip 1.0 above the pilot end; ligament to the outside 3.35, to the passage 6.2 |
| Transition | Z 22 down to 0 (22 long): inner passage a convex hull from the Ø55 circle at Z 22 to a 50.8 × 20.8 rectangle at Z 0 (area 2376 to 1057 mm², monotone, largest rise 7.8% per mm at the narrow end); outer a hull from the 60 × 60 flange outline to 55.2 × 25.2 |
| Slopes | inner wall 37.9° from vertical in Y (17.1 over 22), 5.5° in X; wall 2.2 horizontal at the sleeve rising to 2.5 at the flange, normal thickness 1.74 at the thinnest (Z 0) |
| Sleeve | Z 0 to −6.0 (overlap 6.0), inner 50.8 × 20.8, outer 55.2 × 25.2; gap to each heatsink side 0.40 |
| Size | 60.0 × 60.0 × 34.0 (Z −6 to 28) |
| Margins | duct to heatsink 0.40; duct to fan 0 (flange contact); bolt thread interference 20 mm³ over 5.0 (designed); intake column gap clear |
| Print | flange face down, bed contact 1190 mm² (33.0%); overhang only the four blind pilot ends (Ø3.3, exempt) |

---

## 7. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 (design.json) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout declared: fan above, heatsink below, in line | L2.1.1 to L2.1.5 | L3.1.1.1, L3.1.2.1, L3.1.3.1, L3.1.4.1, L3.1.5.1 | L1.1 | inspection | "a 60 x 60 x 25 mm fan", "a 50 x 20 mm heatsink 30 mm tall, at the heatsink's leading face" |
| L1.2 | Flange sits on the fan's exhaust face on the 50 mm bolt pattern | L2.2.1 to L2.2.3 | L3.2.1.1, L3.2.1.2, L3.2.2.1, L3.2.3.1, L3.2.3.2, L3.2.3.3 | L1.2 | inspection | "a 60 x 60 x 25 mm fan (50 mm hole pitch)" |
| L1.3 | Inlet does not choke the fan | L2.3.1 to L2.3.2 | L3.3.1.1, L3.3.1.2, L3.3.2.1 | L1.3 | inspection | "a duct that connects a 60 x 60 x 25 mm fan" |
| L1.4 | Smoothly changing section from the fan to the heatsink | L2.4.1 to L2.4.5 | L3.4.1.1, L3.4.2.1, L3.4.2.2, L3.4.3.1, L3.4.4.1, L3.4.5.1 | L1.4 | analysis | "the fan blows through a smoothly changing section" |
| L1.5 | The passage ends at the heatsink's leading face and covers it | L2.5.1 to L2.5.3 | L3.5.1.1, L3.5.2.1, L3.5.2.2, L3.5.3.1 | L1.5 | analysis | "at the heatsink's leading face", "into the heatsink fins" |
| L1.6 | Side seals of 1 mm at most round the heatsink | L2.6.1 to L2.6.3 | L3.6.1.1, L3.6.2.1, L3.6.2.2, L3.6.3.1 | L1.6 | analysis | "with 1 mm side seals" |
| L1.7 | The duct keeps off the fan and the heatsink and leaves the fan's intake free | L2.7.1 to L2.7.3 | L3.7.1.1, L3.7.2.1, L3.7.3.1 | L1.7 | analysis | "a 60 x 60 x 25 mm fan" (its intake needs free air) |
| L1.8 | Four M4 bolts into pilots in the flange | L2.8.1 to L2.8.3 | L3.8.1.1, L3.8.1.2, L3.8.1.3, L3.8.2.1, L3.8.2.2, L3.8.2.3, L3.8.3.1 | L1.8 | analysis | "the fan screws", "50 mm hole pitch" |
| L1.9 | The four fan screws can be reached with a hex driver from above | L2.9.1 to L2.9.2 | L3.9.1.1, L3.9.2.1 | L1.9 | test | "I need to reach the fan screws with a driver from above" |
| L1.10 | Closed passage, walls at least 1.6 mm | L2.10.1 to L2.10.3 | L3.10.1.1, L3.10.2.1, L3.10.3.1 | L1.10 | analysis | "duct" (the air must go through the fins) |
| L1.11 | Prints without supports | L2.11.1 to L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | L1.11 | analysis | "printed ... without supports" (added) |
| L1.12 | Compact | L2.12.1 to L2.12.2 | L3.12.1.1, L3.12.2.1 | L1.12 | inspection | "a duct" (compact implied) |
| L1.13 | Package says what was built and its claims are true | L2.13.1 to L2.13.2 | L3.13.1.1, L3.13.1.2, L3.13.2.1 | L1.13 | inspection | needed by the judge (not in the brief) |

---

## 8. Judging this design

> `benchmarks/generalize/rubric.md` was not present when this file was written, so this
> section is the design-specific rubric for G30. It follows `benchmarks/enclosure/rubric.md`
> (sections 2 to 5 and the recipes of its section 3: load, `clear_of`, `inside`, apertures,
> distances, printability, stability) and adds what this design needs. When the generic rubric
> exists, it governs the procedure and report format and this section governs the numbers.

### 8.1 Inputs

| Input | Where | Used for |
|---|---|---|
| `duct.stl` | the design package (declared layout frame, mm) | **every measurement** |
| `.scad` source | package | naming features; never for measuring |
| `layout.json` | package | declared poses, bolt lengths, print orientation |
| `report.json` | package | L1.13 self-report check only |
| renders | package `views/*.png` | locating defects |
| `requirements.md`, `parts/*/part.json` | this folder and `benchmarks/generalize/parts/` | criteria and reference models |

The judge does **not** use the agent's code or transcript, earlier verdicts, `benchmarks/heldout.json`,
or any private design of Robin's. Renders locate defects; they never make a check pass.

### 8.2 Procedure

1. **Package gate (G0).** The files above exist and load; if the STLs are missing or unreadable, stop: DOES NOT MEET, one defect on the package L3.
2. **Units.** Load each STL with trimesh and build a `manifold3d.Manifold` (recipe 3.1 of the enclosure rubric). A body whose bounding-box maximum is not plausible in mm (outside 20 to 200) is a defect, never silently rescaled.
3. **Normalise the frame.** Put the duct in the duct frame (section 1.1): the fan end up (+Z), the heatsink end at Z ≈ 0, the fan axis on Z. Use rotations by multiples of 90° and mirroring only; record the transform.
4. **Build the references independently** from `parts/*/part.json` at the declared poses (section 2), run the sanity checks R1 to R5, then verify the seating rule.
5. **Run every applicable L3** with Python, in order. Record the measured value, the limit, the signed margin (negative = fail) and PASS / FAIL / UNVERIFIED / N/A. **UNVERIFIED counts as FAIL.** N/A only for physical tests (unless a print was made) and checks the section 3 fixed decisions switch off.
6. **Look at the renders** after measuring, to confirm where each failure is and to catch defects no L3 covers (a floating fragment, a feature on the wrong side). Report those as observations; they change the verdict only if a re-measurement makes an L3 fail.
7. **Decide** (8.4) and **report** (8.5).

### 8.3 Measurement recipes specific to this design

- **Passage slices:** for z in steps of 1.0 from the sleeve end to the flange face, `Manifold.slice(z)`; the passage is the polygon(s) enclosed by the duct section (the inner void); report its area, bounding box and largest inscribed circle. A(z) monotone and no-step checks are computed on that series; the first 1.0 below the fan face is excluded from monotonicity.
- **Inner wall slope:** for each inner face (normal pointing into the passage) take its angle from vertical as `asin(|n_z|)` for the unit normal n (0° = vertical wall, 90° = horizontal); report the maximum over faces of area > 1 mm² in the transition.
- **Seal gaps:** at every 1.0 mm below the leading plane within the overlap, cast rays along ±X and ±Y from the heatsink side faces to the sleeve; min, median, max per side.
- **Funnel end:** the Z at which the passage section becomes constant (the sleeve starts), found from the series of area changes < 0.3%.
- **Pilots, flange face, outline:** slice and ray cast as in enclosure rubric recipes 3.5; pilot depth by ray casting down the axis; flange flatness from the face's vertices.
- **Wall thickness:** ray cast inward along each face normal from sampled points, excluding points within 2.0 of an edge, a pilot or the flange block; report min.
- **Intake and driver columns, bolt path:** extrude cylinders along their axes; `clear_of`.
- **Printability:** enclosure rubric recipe 3.6; the blind pilot ends are exempt as round holes ≤ 12.

### 8.4 Verdict

Gates: G0 package, G1 one manifold body, G2 fan interface (flange face, pilots, no collision with the fan), G3 smooth transition (monotone area, slope ≤ 45°), G4 outlet at the heatsink face with side seals, G5 M4 bolts and driver access from above.

| Class | Rule |
|---|---|
| **WRONG** | any gate fails |
| **MINOR** | no gate fails, but some weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |

**MEETS requirements** (the zero-error state) = CORRECT **and** every applicable non-physical L3 of weight 1 and 2 passes. Anything else is **DOES NOT MEET**. Also report the weighted score Σ(weight × pass) / Σ(weight) over applicable L3s and the worst normalised margin among weight-3 L3s (margin ÷ the criterion's tolerance or, for one-sided limits, ÷ 0.5 mm), so a loop can tell progress inside DOES NOT MEET.

Precedence rules:
- **The numbers in this file beat `part.json`.** If a catalogue file disagrees with section 2 or 3 here, build the references from this file and record a defect on the requirement the stale data breaks, with `where` = the part.json field.
- **Designed contact is not interference** (section 1.3). Only penetration above 0.01 mm³ counts for the listed pairs.
- A clearance or fit check outranks a size or tidiness check when the two conflict.
- Never relax a criterion, never round in the design's favour beyond ε, never infer a pass from a render.

### 8.5 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first (gates, then weight 3, 2, 1). Fields: `req` (L3 id with its L2 and L1), `status` (FAIL or UNVERIFIED), `body` (name of the printed body, or `layout`), `feature` (by function and, if present, SCAD name), `face` (surface, side and outward normal), `location` (coordinates in mm in the design frame: a point or a bounding box), `measured` / `limit` / `margin` (numbers with units), `reference` (the reference model or envelope and datum), `render`, `evidence` (saved file, e.g. the intersection solid as `defect_<L3>.stl`), `needed` (the change that would make the check pass, as numbers, never as a design instruction). Coordinates come from the measurement, not from the SCAD source. Group L3s that fail for one geometric reason under the first and list the others in `also_fails`. Keep observations separate from defects. Save the report as `judge.md` and `defects.json`.

### 8.6 Measured-values table (always filled in, pass or fail)

| Quantity | Limit | Measured |
|---|---|---|
| Flange face flatness, offset, contact area | ≤ 0.10; ≤ 0.05; ≥ 800 mm² |  |
| Pilot count, offset to fan holes, pitch | 4; ≤ 0.15; 50.0 ± 0.15 |  |
| Pilot Ø, depth, ligaments | 3.1 to 3.5; ≥ 6.0; ≥ 1.2 / ≥ 1.5 |  |
| Inlet inscribed Ø; area | ≥ 54.0; ≥ 2246 mm² |  |
| A(z) monotone (max rise towards the heatsink) | ≤ 1% |  |
| Area change per mm; inner-outline offset per 1.0 slice | ≤ 10%; ≤ 1.5 |  |
| Maximum inner wall slope | ≤ 45° |  |
| Smallest passage area | ≥ 950 mm² |  |
| Funnel end versus leading plane | ≤ 0.3 |  |
| Outlet size and margin over the face | ≤ 52.0 × 22.0; ≥ 0.2 each side |  |
| Sleeve overlap; gap per side (X, Y) | 5.0 to 15.0; 0.2 to 1.0 |  |
| Duct to heatsink; duct to fan body | d ≥ 0.2; ≤ 0.01 mm³ |  |
| Intake column; driver columns d | ≥ 0; ≥ 0 |  |
| Bolt engagement; tip above pilot end | ≥ 5.0; ≥ 0.5 |  |
| Unlisted openings | 0 |  |
| Minimum wall thickness | ≥ 1.6 |  |
| Shells | 1 |  |
| Overhang patches; bed contact | 0; ≥ 25% and ≥ 800 mm² |  |
| Bounding box X × Y × Z | ≤ 64 × 64 × 45 |  |
| H (exhaust to leading plane) | 24 to 40 |  |
| Self-report agreement | 100% within 0.10 |  |

---

## Audit

Adversarial audit (2026-10-24). Part ids checked with `parts.py` (`fan_60x60x25`, `generic_box`, `bolt_m4_iso4762` load and pass the gate). Counts recomputed: L1 13, L2 39, L3 51 after fix 4 (weights 26 / 19 / 6, total 122; section 5 updated). Section 6 was rebuilt as a `manifold3d` model (Ø-inlet circle-to-rectangle hulls, 60 × 60 × 6 flange, sleeve, four pilots) and every number was measured on it: one shell, area profile by horizontal slices every 1.0, horizontal wall width per slice, bed contact, gap, bolt tip and engagement, pilot ligaments.

Fixes made in place:

1. **Wall thickness failed in the sketch.** The old inlet Ø56 left a horizontal wall of 2.0 at the flange end of the transition; on the 38.7° Y faces the normal thickness there is 1.57 (< 1.6, weight 3, L3.10.2.1), and the old table quoted only the 1.72 at the sleeve end. Inlet is now Ø55 (area 2376 mm² = 90% of the bore, inscribed 55, both inside L2.3.1); the thinnest normal thickness is now 1.74. Slopes (37.9° Y, 5.5° X), pilot ligament to the passage (6.2) and bed contact (1190 mm², 33%) updated; A11 uses the new Y change.
2. **L2.4.2 could not be met.** (a) The 8% per 1.0 mm area limit fails by the old sketch itself (measured 8.06% at the narrow end) and fails for any hull transition at the short end of the allowed range (9.1% at transition 18), so it is now 10% (sketch: 7.8%). (b) "no jump in the inner outline > 0.5 between slices" contradicted L2.4.3, which allows 45° walls moving up to 1.0 per 1.0 slice (the sketch's 37.9° wall moves 0.78); it is now an offset ≤ 1.5, which only a real step exceeds.
3. **Removed L3.10.2.2** (maximum wall 6.0, weight 1): not in any L1, arbitrary, and the section 6 hull has solid corner blocks about 14 thick under the flange, so the sketch could not meet it. Counts, traceability and gates updated.
4. **Hidden numbers moved into L1** (the text the agent gets): flange outline 60 ± 1 and 800 mm² contact (L1.2), inlet no bigger than bore + 1 (L1.3), 10% per mm, 950 mm² minimum area and 18 to 34 transition (L1.4), outlet ≤ 52 × 22 (L1.5), pilot Ø 3.1 to 3.5 and depth ≥ 6 (L1.8), 45° / 15 mm / 25% bed rule (L1.11), symmetry within 1 (L1.12).
5. **L3 rows with no number** (L3.1.1.1, L3.11.1.1, L3.11.2.1, L3.11.3.1, L3.12.1.1, L3.13.1.1) now carry a numeric band; unit-plausibility limit made 20 to 200 in both L3.13.1.1 and section 8.2 (they disagreed, 20 vs 5).

Checked and left alone: H 24 to 40 against transition 18 to 34 and the 6.0 flange; engagement 5.0 against pilot depth 6.0 and tip clearance 1.0; bolt thread interference 20 mm³ against the allowance in 1.3; driver and intake columns clear (nothing above Z 28); the 64 × 64 × 45 limit against H 40 plus sleeve 5 to 15 is a design trade-off, not a contradiction (the sketch is 60 × 60 × 34).
