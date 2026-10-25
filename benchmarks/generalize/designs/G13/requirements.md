# G13 Pico macro pad with four buttons: requirements (L1 / L2 / L3)

A training entry of the generalization benchmark (`benchmarks/generalize/`), modelled on E1-01
(`benchmarks/enclosure/requirements.md`). The machine-readable request (L1 only, `dev.json` format) is
`design.json` next to this file. This file holds the L2/L3 tree, the reference models, the assumptions, the fixed decisions, a feasibility sketch, the traceability and the design-specific judging rules (section 8). Catalogue parts:
`benchmarks/generalize/parts/` (`button_tact_6mm`) and `benchmarks/enclosure/parts/` (`perfboard`, `rpi_pico2`, `header_female_2p54`, `plug_microusb_b`, `screw_m2_selftap`, `screw_m3_selftap`). No number here may appear in agent logic: they live in the request, this file, `design_rules.json` generic values and `part.json` data.

**Request (plan brief, verbatim):** "A 2 x 2 macro pad: four 6 mm tactile switches on a 70 x 50 perfboard at 19.05 mm pitch with a Pico 2 above them. Each button plunger comes up through a top plate hole with 0.4 mm clearance and 1.5 mm travel before bottoming. Micro-USB opens at the rear."

**Expanded request** (the text the agent gets, `design.json`): A 2 x 2 macro pad. Four 6 mm tactile switches sit on a 70 x 50 mm perfboard (a mounting hole in each corner) at 19.05 mm pitch in both directions, with a Raspberry Pi Pico 2 plugged into female sockets on the same board behind them. Each switch is pressed by a printed plunger that comes up through a hole in the top plate with 0.4 mm clearance all round, and the plunger has 1.5 mm of travel before it bottoms out. The Pico's micro-USB port opens through the rear end wall, so the cable plugs in with the lid on. The enclosure is a base and a removable top plate (the plate is the lid), printed on an FDM printer without supports.

**How to read this.** L1 says what the owner needs; L2 turns it into an engineering requirement with numbers; L3 is a concrete check Python can run on the delivered STLs. Each row has a method, a pass/fail criterion with a number and tolerance, a weight (3 critical, 2 major, 1 minor) and, for must-pass rows, a gate mark. Numbers that come from an assumption (section 3) are provisional until Robin confirms them. Do not relax a criterion because a design fails it.

---

## 1. Frames, tolerances and the interference checks

### 1.1 Frames

- **Enclosure frame:** X along the board's 70 mm side, Y along its 50 mm side, Z up. The **rear is −X** (the USB end, A2); the switches are at larger X than the Pico's USB port, and the **Pico is behind the buttons towards +Y** (A1). A design delivered mirrored or rotated by 90° multiples is normalised into this frame before grading (rubric step 3) and never penalised.
- **Board frame (all tables below):** origin at the perfboard's top-surface corner at min X, min Y. Z = 0 is the board's top surface; the board occupies Z −1.6 to 0.

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
- the board's underside on the standoff tops, inside the V-SEAT-k columns
- an M2 board screw in its standoff pilot and an M3 lid screw in its boss pilot, each with its head on the board top or the lid top
- the lid plate's underside on the rebate floor and the four boss tops; its edge against the rebate upstand at the fit the lid requirements set (0.15 to 0.35 per side)
- a switch body on the board top (legs through their holes) and a socket on the board top
- the Pico's underside on the socket tops; its pins in the sockets
- a plunger's stop face on the lid plate underside at rest; a plunger's tip on the switch actuator (soft contact) and, at bottoming, on the switch body top
- a plug in its receptacle at full mate (the plug is an envelope, not part of the enclosure)

For these pairs only penetration counts (an intersection volume above 0.01 mm³, unless the pair
is given a larger allowance below). A distance of zero is a pass.

`bodies` is **ALL** (base, lid and the four plungers, closed, plungers at rest), **BASE**, **LID**, **PLUNGERS** or **BASE ∪ LID** where a check says so.

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` in the parts folders named in the header. The only place part numbers may live.
- **envelope**: a keep-out, sweep or access volume generated by Python from datums. Never drawn by hand.
- **computed**: derived from the design (cavity, apertures, plunger measurements).

### 2.2 Reference models (M-)

Positions are the **reference layout** of the feasibility sketch (section 6); a design declares its own poses in `layout.json` (L2.1.1) and every check is graded against the declared layout, within the constraints of L1.1.

| Name | What | Source | Size and position (board frame, mm) | Datums |
|---|---|---|---|---|
| **M-PERF** | 70 × 50 perfboard | catalogue `perfboard` (the 70 × 50 specimen of E1-01 A7) | 70.0 × 50.0 × 1.6; X 0 to 70, Y 0 to 50, Z −1.6 to 0; four holes Ø2.0 at (2.0, 2.0), (68.0, 2.0), (2.0, 48.0), (68.0, 48.0) (pitch 66.0 × 46.0); hole grid 24 × 18 at 2.54, hole (i, j) at X 5.79 + 2.54·i, Y 3.41 + 2.54·j | `PERF_TOP`, `PERF_BOTTOM`, `PERF_HOLE_1..4`, `PERF_GRID` |
| **M-BTN-k** (k = 1..4) | 6 mm tactile switch | catalogue `button_tact_6mm` | body 6.0 × 6.0 × 3.8 on the board top (Z 0 to 3.8); actuator Ø3.5 × 0.5 above the body (top Z 4.3); legs 3.0 below, 4.5 × 6.5 pattern; centres X 25.475 and 44.525, Y 5.0 and 24.05 (19.05 pitch) | `BODY_TOP` (3.8), `PLUNGER_TOP` / `ACTUATOR_AXIS` (4.3), `PINS` |
| **M-SOCK** | two 1 × 20 female sockets under the Pico | catalogue `header_female_2p54` | pitch 2.54, spacer 2.5 wide × 8.5 tall; rows 17.78 apart at Y 28.81 and 46.59 (grid rows j = 10 and 17); pin i at X 5.79 + 2.54·(2 + i), i = 0 to 19 | `STACK_TOP` (Z 8.5), `PINS` |
| **M-PICO2** | Raspberry Pi Pico 2 | catalogue `rpi_pico2` | PCB 51.0 × 21.0 × 1.0 at X 9.5 to 60.5, Y 27.2 to 48.2, Z 8.5 to 9.5; USB receptacle 8.0 × 5.5 × 2.8 on top at X 8.2 to 13.7, Y 33.7 to 41.7, Z 9.5 to 12.3 | `USB_MOUTH` (8.2, 37.7, 10.9), `USB_AXIS` (−X), `PINS_A`, `PINS_B` |
| **M-PLUG-USB** | micro-USB B cable plug | catalogue `plug_microusb_b` | shell 6.9 × 1.85, inserted 5.0, exposed 1.5; overmold 10.0 (Y) × 7.0 (Z) × 20 long | `PLUG_TIP`, `PLUG_AXIS`, `OVERMOLD_FACE` |
| **M-PLUNGER-k** | printed plunger (the design's own body) | the design's `plunger.stl` at the declared pose | stem Ø5 in the sketch; tip at Z 5.3 | measured: stem Ø, tip face, flange, stop face |
| **M-SCREW-M2**, **M-SCREW-M3** | board and lid screws | catalogue `screw_m2_selftap`, `screw_m3_selftap` | M2: head Ø4.0, pilot 1.6 to 1.8; M3: head Ø6.0, pilot 2.4 to 2.6, clearance Ø3.4 | `AXIS` |
| **M-BOARD-ASSY** | M-PERF ∪ M-BTN-1..4 ∪ M-SOCK ∪ M-PICO2 at the declared layout | assembled | as above | all of the above |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Definition (board frame, mm) |
|---|---|---|
| **V-KO-TOP** | component keep-out above the board | board footprint X 0 to 70, Y 0 to 50, Z 0 to 13.3 (A4: tallest part the USB receptacle top at 12.3, plus 1.0); applies to BASE ∪ LID |
| **V-KO-BOT** | solder-side keep-out | board footprint, Z −1.6 to −5.6 (4.0 below `PERF_BOTTOM`, A4), minus the V-SEAT columns |
| **V-SEAT-k** | where a standoff may touch the board | Ø7.0 column on `PERF_HOLE_k`, from the floor up to `PERF_BOTTOM` |
| **V-HOLE-KO-k** | screw-head room above each board hole | Ø6.0 column on `PERF_HOLE_k`, Z 0 to 13.3 |
| **V-PICO** | the Pico and its receptacle | M-PICO2 ∪ M-SOCK |
| **V-USB-PLUG** | micro-USB plug at full mate plus its path | shell 6.9 × 1.85 from 5.0 inside `USB_MOUTH` to 1.5 outside it (X 13.2 to 6.7); overmold 10.0 × 7.0 from X 6.7 outward to X −13.3 (past the wall), axis (Y 37.7, Z 10.9): the overmold spans Z 7.4 to 14.4 |
| **V-INSTALL** | board installation path | M-BOARD-ASSY's plan silhouette swept +Z from the seated pose to 5.0 above the base rim, minus the V-SEAT columns |
| **V-DRIVER-k** | screwdriver access to a board screw | Ø6.0 column on `PERF_HOLE_k` from `PERF_TOP` to 50 above the base rim, lid off |
| **V-LIDDRIVER-j** | screwdriver access to a lid screw | Ø6.0 column on each lid-screw axis from the lid top to 50 above it |
| **V-PLUNGER-INSTALL-k** | plunger load path | M-PLUNGER-k swept straight down 20 below its rest pose (lid alone, inverted pose equivalent), i.e. the path of loading it from below |
| **V-LID-CLOSE** | lid with plungers closing | LID ∪ PLUNGERS swept from 20 above the closed pose straight down to it |
| **V-CAVITY**, **V-AP-USB**, **V-AP-OTHER** | cavity and apertures | as E1-01 section 2.3: V-CAVITY = hull(BASE ∪ LID) minus (BASE ∪ LID), the component containing the board centroid; V-AP-USB = the −X wall slab minus (BASE ∪ LID); V-AP-OTHER = every other through-path into V-CAVITY (the plunger holes and screw holes are listed, not unlisted) |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-PERF, M-PICO2 | units and size | board 70.0 × 50.0 × 1.6 ± 0.2; Pico PCB 51.0 × 21.0 ± 0.2 |
| R2 | M-BTN | body, actuator, travel | 6.0 × 6.0 × 3.8 ± 0.1; actuator Ø3.5, top 4.3 ± 0.1; travel 0.25; `pusher_overtravel` 0.5 |
| R3 | M-SOCK | pitch, height, row spacing | 2.54 ± 0.02; 8.5 ± 0.1; 17.78 ± 0.05 |
| R4 | M-PICO2 | orientation | components on +Z, receptacle at the −X end, `USB_AXIS` along −X |
| R5 | M-BOARD-ASSY | parts do not collide | intersections ≤ 0.01 mm³ |
| R6 | every V- envelope | datums equal the model datums it came from | ≤ 0.01 |

**Seating rule.** The assembly is placed at the pose in `layout.json`. The grader then verifies: M-PERF's underside on the standoff tops (≤ 0.10), `PERF_HOLE_1..4` coaxial with the standoff pilots (residual ≤ 0.25), each plunger's stop face on the lid underside (≤ 0.10). If a declaration is missing or fails, the board is seated by fit instead and the dependent L3s stay failed.

---

## 3. Assumptions, fixed decisions and open questions

### 3.1 Assumptions (derived, with their uncertainty)

| # | Question | Value chosen | Why, and uncertainty |
|---|---|---|---|
| A1 | "A Pico 2 above them"? | Above in plan view: the Pico lies along X on the +Y side, behind the 2 × 2 buttons. | The 2 × 2 group at 19.05 pitch is 25 mm square; the Pico (51 × 21) beside it in Y gives 46 mm of the 50 mm board, and stacked above the switches it would hide the plungers. **Alternative:** stacked above, not graded. Medium uncertainty. |
| A2 | "Rear"? | The short end wall the Pico's USB faces (−X). | A Pico lying along X has its USB on a short end; it cannot face a long wall. Medium uncertainty. |
| A3 | How is the Pico mounted? | On female sockets (catalogue `header_female_2p54`, 8.5 tall): PCB underside 8.5 above the board top, USB axis 10.9 above it. | The plan lists a female header. Soldered flat or male headers would give a lower USB axis. |
| A4 | Clearances? | 13.3 above the board top (receptacle top 12.3 + 1.0); 4.0 below the underside (switch legs 3.0 + 1.0). | Catalogue values. The lid's real height is set by the USB plug overmold top (14.4) plus the clearance and ligament. |
| A5 | What is the "plunger"? | A printed part: stem, a retaining flange under the plate, a tip on the switch actuator. It is not the switch's own 0.5 mm actuator. | The switch's actuator protrudes only 0.5 mm and travels 0.25, so it cannot be "1.5 mm travel before bottoming" through a plate. Medium uncertainty. |
| A6 | "0.4 mm clearance"? | 0.4 on every side (radial): hole Ø = stem Ø + 0.8, band 0.3 to 0.5 per side. | The brief says "with 0.4 mm clearance" about a plunger in a hole; radial is the usual reading. **Alternative:** diametral 0.4 (0.2 per side), not graded. Medium uncertainty. |
| A7 | "Travel before bottoming"? | The distance from rest to first hard contact: the plunger tip on the switch body top (or any other stop). The catalogue switch's actuation point is 0.25 below the actuator top. | Gives z_b in [3.8, 4.05] (L1.7). Low uncertainty. |
| A8 | Board? | The 70 × 50 specimen of E1-01 A7: holes Ø2.0 at 2.0 from each edge, 24 × 18 grid, 1.6 thick. | Same board family as the owner's keyer; M2 screws pass Ø2.0. |
| A9 | Plug sizes? | Micro-USB overmold 10.0 × 7.0, shell 6.9 × 1.85. | Typical cables (catalogue). **Measure the owner's.** |
| A10 | Printing and size? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed; overhang limit 45°; walls 2.0 to 4.0; closed size ≤ 95 × 70 × 35. | Common printers; a tight design is 90 × 58.4 × 29.6 (section 6). |
| A11 | Press load and mass? | Press force 1.6 N (catalogue `actuation_force`), total mass 150 g. | Used only for the stability check. |

### 3.2 Fixed decisions (a choice that would otherwise be ambiguous)

| # | Decision |
|---|---|
| F1 | The plunger is retained by a flange under the plate and loaded from below with the lid inverted; the finger end is the stem top, proud of the plate. |
| F2 | **Lid form (not open to alternatives):** one flat plate that drops into a rebate in the wall tops, resting on the rebate floor and on four bosses, held by four M3 self-tapping screws. The board fills the footprint, so the bosses sit outside it. |
| F3 | The USB opening is the only opening in the rear wall; no switch or plunger is mounted in a wall. |
| F4 | The four plungers are identical: one `plunger.stl`, four poses in `layout.json`. |
| F5 | The top plate is the lid: the plunger holes are in the lid, not in a separate plate. |

---

## 4. Requirements tree

### L1.1 Layout declared: 2 x 2 buttons at 19.05 mm pitch, Pico 2 behind them on sockets, USB at the rear

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares the pose of each reference part (catalogue id, X, Y, Z, rotation about Z) in the board frame. | inspection | `layout.json` present, parses, names the perfboard, four `button_tact_6mm`, `rpi_pico2` and two `header_female_2p54` parts and four plunger instances | 3 |  |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | parse errors = 0; unknown ids = 0; plunger instances = 4 | 3 | G0 |
| L2.1.2 | Four buttons in a 2 × 2 array at 19.05 pitch, axes vertical. | inspection | `ACTUATOR_AXIS` within 1.0° of +Z; centres on a rectangle 19.05 ± 0.10 in X and 19.05 ± 0.10 in Y; sides parallel to X and Y within 0.5° | 3 |  |
| L3.1.2.1 | Button pitch along X. | inspection | 19.05 ± 0.10 (+ε) | 3 | G5 |
| L3.1.2.2 | Button pitch along Y. | inspection | 19.05 ± 0.10 (+ε) | 3 | G5 |
| L3.1.2.3 | Array squareness and axis direction. | inspection | ≤ 0.5°; axes ≤ 1.0° | 2 |  |
| L2.1.3 | The Pico lies along X on two female sockets, behind the buttons, with its USB port facing −X (the rear). | inspection | `USB_AXIS` within 1.0° of −X; Pico PCB Y minimum at least 0.5 above every button axis Y; Pico PCB underside 8.5 ± 0.1 above the board top; `USB_MOUTH` X ≤ 12.0 | 3 |  |
| L3.1.3.1 | USB direction and Pico orientation. | inspection | ≤ 1.0° of −X; Pico long axis along X ≤ 1.0° | 3 | G3 |
| L3.1.3.2 | Pico behind the buttons. | inspection | Pico Y min − max button axis Y ≥ 0.5 | 2 |  |
| L3.1.3.3 | Pico height on its sockets. | inspection | 8.5 ± 0.1 | 2 |  |
| L2.1.4 | The Pico's header pins land on the perfboard's 2.54 mm grid. The switch legs (4.5 × 6.5 pattern) are exempt: they go through enlarged holes. | inspection | every Pico socket pin axis within 0.15 of a `PERF_GRID` hole | 1 |  |
| L3.1.4.1 | Pin-to-grid residuals (switches exempt). | inspection | max ≤ 0.15 | 1 |  |
| L2.1.5 | The parts fit on the board without colliding, stay on it, and leave the four corner screws free. | analysis | pairwise interference ≤ 0.01 mm³; plan outline inside X −2.0 to 72.0, Y 0 to 50 (the Pico's USB overhang excepted); clear_of(buttons ∪ Pico ∪ sockets, V-HOLE-KO-1..4, 0.0) | 3 |  |
| L3.1.5.1 | Pairwise interference of the reference parts. | analysis | each pair ≤ 0.01 mm³ | 3 |  |
| L3.1.5.2 | No part on a screw column. | analysis | d ≥ 0.0 | 3 |  |

### L1.2 Board fits inside with 0.5 mm clearance

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | With the board seated and the lid closed, no printed body (base, lid or plunger) comes within 0.5 of the board, except the standoff tops under its holes. | analysis | clear_of(ALL, M-PERF minus the V-SEAT columns grown by 0.5, 0.5) | 3 |  |
| L3.2.1.1 | Board-edge clearance, all four edges and both faces. | analysis | d ≥ 0.50 | 3 | G2 |
| L3.2.1.2 | A 70 × 50 × 1.6 box fits the base with 0.5 clearance (own-model proxy). | demonstration | the box's margin to the base cavity walls ≥ 0.50 on all four sides | 2 |  |
| L2.2.2 | Along X the cavity takes the board plus the USB overhang. | analysis | inside(V-PICO, V-CAVITY, 0.2); inside(M-PERF, V-CAVITY, 0.5) | 3 |  |
| L3.2.2.1 | Pico with receptacle inside the cavity. | analysis | d ≥ 0.20 | 3 | G2 |

### L1.3 Four standoffs under the corner holes, with M2 pilots

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Four standoffs, one under each board hole, centred on the 66.0 × 46.0 pattern. | inspection | count = 4; each axis within 0.25 of its `PERF_HOLE_k` | 3 |  |
| L3.3.1.1 | Exactly 4 standoffs. | inspection | count = 4 | 3 | G4 |
| L3.3.1.2 | Standoff pitch. | inspection | 66.0 ± 0.25 along X; 46.0 ± 0.25 along Y | 3 | G4 |
| L3.3.1.3 | Standoff axes versus the seated board's holes. | analysis | each offset ≤ 0.25 | 3 | G4 |
| L2.3.2 | Standoff OD 5.0 to 7.0; tops coplanar; each top touches the board only inside its V-SEAT column. | inspection | OD in [5.0, 7.0]; top-Z spread ≤ 0.10 | 2 |  |
| L3.3.2.1 | Standoff OD. | inspection | 5.0 to 7.0 | 2 |  |
| L3.3.2.2 | Top-plane spread. | inspection | ≤ 0.10 | 2 |  |
| L2.3.3 | Each standoff has a pilot for an M2 self-tapping screw (catalogue `screw_m2_selftap`: pilot 1.6 to 1.8), coaxial, deep enough. | inspection | Ø 1.6 to 1.8; depth ≥ 5.0; coaxial ≤ 0.1 | 3 |  |
| L3.3.3.1 | Pilot diameter. | inspection | 1.6 to 1.8 | 3 | G4 |
| L3.3.3.2 | Pilot depth. | inspection | ≥ 5.0 | 2 |  |
| L2.3.4 | Standoffs are fused to the floor and the base is one body; nothing but the screws enters the board holes. | analysis | contact per standoff ≥ 15 mm²; BASE 1 shell; clear_of(ALL, V-HOLE-KO-k, 0.0) | 2 |  |
| L3.3.4.1 | Standoff-to-floor contact. | analysis | ≥ 15 mm² | 2 |  |
| L3.3.4.2 | Base is one shell. | analysis | 1 shell | 3 | G1 |
| L3.3.4.3 | Screw-head columns clear. | analysis | d ≥ 0.0 | 2 |  |

### L1.4 Clearance above and below the board

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Lid closed: base and lid keep out of the component zone above the board (the plungers pass through it by design; they have their own checks). | analysis | clear_of(BASE ∪ LID, V-KO-TOP, 0.0) | 3 |  |
| L3.4.1.1 | Top keep-out clear. | analysis | d ≥ 0.0 | 3 | G2 |
| L3.4.1.2 | Lid underside minus board top (own-model proxy). | inspection | ≥ 13.3 | 2 |  |
| L2.4.2 | No body enters the solder-side zone (except the standoffs in their V-SEAT columns). | analysis | clear_of(ALL, V-KO-BOT, 0.0) | 3 |  |
| L3.4.2.1 | Bottom keep-out clear. | analysis | d ≥ 0.0 | 3 | G2 |
| L3.4.2.2 | Standoff height above the floor top (own-model proxy). | inspection | 4.0 to 10.0 | 2 |  |
| L2.4.3 | Every board part is enclosed with clearance. | analysis | inside(sockets ∪ buttons, V-CAVITY, 0.3); inside(V-PICO, V-CAVITY, 0.2) | 3 |  |
| L3.4.3.1 | Sockets and buttons inside the cavity. | analysis | d ≥ 0.30 | 3 |  |

### L1.5 Micro-USB cable plugs in through the rear end wall with the lid on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Lid closed: the plug pushes in to full mate and pulls out without touching the enclosure. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 |  |
| L3.5.1.1 | USB plug envelope clear. | test | d ≥ 0.30 | 3 | G3 |
| L3.5.1.2 | Physical: print, close, plug in a real cable. | test | clicks in fully, 3 of 3 tries (optional) | 2 |  |
| L2.5.2 | The USB opening is not oversized: within 1.5 of the plug envelope on every side. | analysis | inside(V-AP-USB, V-USB-PLUG offset by 1.5, 0.0) | 2 |  |
| L3.5.2.1 | Opening within the grown plug envelope. | analysis | d ≥ 0.0 (with defaults: opening ≤ 13.0 × 10.0, ≥ 10.6 × 7.6) | 2 |  |
| L2.5.3 | Exactly one USB opening, in the rear end wall only. | inspection | V-AP-USB has 1 connected region; no other wall has an opening the plug envelope passes through | 2 |  |
| L3.5.3.1 | Opening count in the rear wall. | inspection | 1 | 2 |  |

### L1.6 Each plunger comes up through a hole in the top plate with 0.4 mm clearance

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Four round holes in the lid plate, coaxial with the four switch axes. | inspection | count = 4; hole centre within 0.20 of the `ACTUATOR_AXIS` of its switch (lid in the closed pose) | 3 |  |
| L3.6.1.1 | Plunger-hole count. | inspection | 4 | 3 | G5 |
| L3.6.1.2 | Hole-to-switch alignment. | analysis | each ≤ 0.20 | 3 | G5 |
| L2.6.2 | The plunger is one printed body with a round stem, the same four instances (one STL, four declared poses), and the clearance round the stem is 0.4 per side. | inspection | stem Ø in [4.0, 5.6]; plate hole Ø − stem Ø in [0.6, 1.0] (0.3 to 0.5 per side) at the narrowest point of the hole; plunger–hole coaxial within 0.10 | 3 |  |
| L3.6.2.1 | Stem diameter. | inspection | 4.0 to 5.6 | 2 |  |
| L3.6.2.2 | Radial clearance between stem and hole. | inspection | 0.40 ± 0.10 per side (+ε) | 3 | G5 |
| L3.6.2.3 | Plunger and hole coaxial at rest. | analysis | ≤ 0.10 | 2 |  |
| L2.6.3 | The plungers clear the Pico, the sockets, the board and each other. | analysis | clear_of(PLUNGERS, M-PICO ∪ M-SOCKETS ∪ M-PERF, 0.5); plungers pairwise ≥ 2.0 apart | 2 |  |
| L3.6.3.1 | Plunger to Pico, sockets and board. | analysis | d ≥ 0.50 | 2 |  |
| L3.6.3.2 | Plunger to plunger. | analysis | d ≥ 2.0 | 1 |  |
| L2.6.4 | The plunger tip centres on the switch actuator and is no wider than the switch body. | inspection | tip face Ø ≥ 3.5 (covers the Ø3.5 actuator) and ≤ 5.6; tip axis offset to `ACTUATOR_AXIS` ≤ 0.20 | 2 |  |
| L3.6.4.1 | Tip diameter and alignment. | inspection | 3.5 to 5.6; ≤ 0.20 | 2 |  |

### L1.7 Plunger has 1.5 mm of travel, presses the switch, and cannot fall out

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Travel before bottoming: sliding the plunger straight down from its rest pose, the first hard contact (any printed or switch-body surface; the Ø3.5 actuator is soft) comes after 1.5 mm. | test | travel T = 1.5 ± 0.15 (+ε), measured by sweeping the plunger down along its axis until intersection > 0.01 mm³ | 3 |  |
| L3.7.1.1 | Travel before bottoming, each plunger. | test | 1.5 ± 0.15 (+ε) | 3 | G5 |
| L2.7.2 | At rest the plunger sits above the actuator with a gap, and at bottoming it has pressed the actuator beyond its actuation point but not past the switch body. | analysis | tip height at rest z_r above the board top; bottoming tip height z_b = z_r − T must lie in [3.8, 4.05] (body top 3.8; actuation at 4.3 + 0.0 − 0.25 = 4.05); rest gap to the actuator top (4.3) ≥ 0.5; overtravel 4.05 − z_b in [0.0, 0.5] | 3 |  |
| L3.7.2.1 | Bottoming tip height. | analysis | 3.8 to 4.05 | 3 | G5 |
| L3.7.2.2 | Idle gap above the actuator. | analysis | ≥ 0.5 | 2 |  |
| L3.7.2.3 | Overtravel beyond actuation. | analysis | 0.0 to 0.5 (catalogue `pusher_overtravel` 0.5) | 2 |  |
| L2.7.3 | The plunger is retained: a flange or hook under the plate stops it, at rest it touches the plate underside, and it cannot be pulled out upward. | analysis | flange (or hook) Ø ≥ hole Ø + 2.0; gap between its stop face and the plate underside ≤ 0.10 at rest; flange cannot pass the hole (min flange width > hole Ø) | 3 |  |
| L3.7.3.1 | Retention geometry. | analysis | flange Ø ≥ hole Ø + 2.0 | 3 | G5 |
| L3.7.3.2 | Rest position against the stop. | analysis | gap ≤ 0.10 | 2 |  |
| L2.7.4 | The plunger end the finger presses stays proud of the plate at bottoming. | inspection | plunger top above the plate top at bottoming ≥ 0.5; top face flat Ø ≥ 4.0 | 2 |  |
| L3.7.4.1 | Proud height at bottoming. | inspection | ≥ 0.5 | 2 |  |
| L2.7.5 | The plunger moves freely: no printed surface touches it between rest and bottoming. | analysis | swept volume of the plunger over its travel: ∩ BASE ∪ LID ≤ 0.01 mm³ except the stop contact at the ends | 2 |  |
| L3.7.5.1 | Free travel. | analysis | ≤ 0.01 mm³ | 2 |  |

### L1.8 The top plate is a removable lid held by four M3 screws

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Base and lid are separate bodies, each one connected body, not interpenetrating when closed. | analysis | BASE 1 shell; LID 1 shell; BASE ∩ LID ≤ 1.0 mm³ | 3 |  |
| L3.8.1.1 | Base and lid each connected. | analysis | 1 shell each | 3 | G1 |
| L3.8.1.2 | Base and lid do not interpenetrate. | analysis | ≤ 1.0 mm³ | 3 | G1 |
| L2.8.2 | Lid form: one flat plate 2.0 to 3.0 thick, in a rebate in the wall tops: upstand at least 1.0, rebate depth equal to the plate thickness within 0.3, fit 0.15 to 0.35 per side, plate top flush with the upstand within 0.3. | inspection | every number met | 3 |  |
| L3.8.2.1 | Plate thickness and rebate depth. | inspection | 2.0 to 3.0; depth = thickness ± 0.3 | 3 |  |
| L3.8.2.2 | Fit clearance on all four sides. | inspection | 0.15 to 0.35 per side | 2 |  |
| L3.8.2.3 | Upstand thickness and flushness. | inspection | ≥ 1.0; flush within 0.3 | 2 |  |
| L2.8.3 | Exactly four lid bosses, outside the board footprint and its keep-outs, each with an M3 pilot, tops at the rebate floor plane. | inspection | count = 4; pilot Ø 2.4 to 2.6, depth ≥ 10.0 − lid plate thickness (never below 6.0); OD ≥ 6.0; top within 0.10 of the rebate floor plane; boss ∩ V-KO-TOP, V-INSTALL ≤ 0.01 mm³; boss to board ≥ 0.5; fused to the floor | 3 |  |
| L3.8.3.1 | Boss count. | inspection | 4 | 3 | G6 |
| L3.8.3.2 | Boss pilot diameter, depth and OD. | inspection | Ø 2.4 to 2.6; depth ≥ 10.0 − lid plate thickness (7.0 to 8.0, never below 6.0, so the length-10 catalogue screw does not bottom); OD ≥ 6.0 | 3 | G6 |
| L3.8.3.3 | Bosses clear of the board and its volumes. | analysis | d ≥ 0.5 to the board; ≤ 0.01 mm³ into V-KO-TOP, V-INSTALL | 3 |  |
| L2.8.4 | The lid has four plain M3 holes, coaxial with the pilots, and the screw heads can be driven. | inspection | Ø 3.4 ± 0.10; axis offset ≤ 0.3; clear_of(ALL, V-LIDDRIVER-1..4, 0.0) | 3 |  |
| L3.8.4.1 | Lid hole diameter. | inspection | 3.4 ± 0.10 | 3 | G6 |
| L3.8.4.2 | Lid-hole and pilot alignment. | inspection | ≤ 0.3 | 3 | G6 |
| L3.8.4.3 | Lid-screw driver columns. | analysis | d ≥ 0.0 | 1 |  |
| L2.8.5 | The seam is tight and the outer faces flush. | inspection | seam gap ≤ 0.5; step ≤ 0.5 | 1 |  |
| L3.8.5.1 | Seam gap and flushness. | inspection | ≤ 0.5; ≤ 0.5 | 1 |  |

### L1.9 Closed except the USB opening, the plunger holes and the screw holes; walls 2 to 4 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The only openings are the USB opening, the plunger holes and the screw holes. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into V-CAVITY other than the plunger holes and screw holes | 2 |  |
| L3.9.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 |  |
| L2.9.2 | Walls, floor and lid plate are 2.0 to 4.0 thick (away from ports, rebates and bosses). | inspection | each in [2.0, 4.0] (median) | 2 |  |
| L3.9.2.1 | Side wall thickness. | inspection | 2.0 to 4.0 | 2 |  |
| L3.9.2.2 | Floor thickness. | inspection | 2.0 to 4.0 | 2 |  |
| L3.9.2.3 | Lid plate thickness. | inspection | 2.0 to 3.0 | 2 |  |
| L2.9.3 | At least 1.5 of material round the USB opening and round each plunger hole. | analysis | min ligament ≥ 1.5 (USB opening to wall edges, floor top, rebate floor; plunger holes to each other, to the lid edge and screw holes) | 1 |  |
| L3.9.3.1 | Minimum ligament per opening. | analysis | ≥ 1.5 | 1 |  |
| L2.9.4 | Each wall joins the floor along its length. | analysis | contact ≥ 90% of wall length × thickness | 2 |  |
| L3.9.4.1 | Wall-to-floor contact. | analysis | ≥ 0.9 × L × t | 2 |  |

### L1.10 Prints without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | In its stated print orientation (default: base open side up, lid outer face down, plunger tip down) no part has an unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12.0 in vertical walls and bridges ≤ 15.0. | analysis | 0 offending faces (area > 1 mm²) per body | 2 |  |
| L3.10.1.1 | Overhang and bridge scan per body (base, lid, plunger). | analysis | 0 faces steeper than 45° with area > 1 mm²; every bridge ≤ 15.0; every round hole in a vertical wall Ø ≤ 12.0 | 2 |  |
| L2.10.2 | Each body is manifold and one shell. | analysis | 1 shell; manifold3d accepts it | 3 |  |
| L3.10.2.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.10.3 | Each body rests on a flat face in its print orientation. | analysis | bed contact ≥ 50% of the plan bounding box (base, lid); ≥ 20% (plunger) | 1 |  |
| L3.10.3.1 | Bed-contact area per body. | analysis | ≥ 50% of the plan bounding box (base, lid); ≥ 20% (plunger) | 1 |  |
| L2.10.4 | No feature thinner than 0.8; mating clearances ≥ 0.15 (the plunger-hole clearance is 0.30 to 0.50 per side); each body fits a 200 × 200 × 200 build volume. | analysis | min thickness ≥ 0.8; other gaps ≥ 0.15; bounding box ≤ 200 | 1 |  |
| L3.10.4.1 | Thin-feature and mating-gap scan. | analysis | min thickness ≥ 0.8; other mating gaps ≥ 0.15; bounding box ≤ 200 per axis | 1 |  |

### L1.11 Sits on a desk: compact and stable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Closed outside size ≤ 95 × 70 × 35 (plungers at rest included), longest plan side along X. | inspection | X ≤ 95.0, Y ≤ 70.0, Z ≤ 35.0; X > Y | 1 |  |
| L3.11.1.1 | Assembly bounding box. | inspection | X ≤ 95.0, Y ≤ 70.0, Z ≤ 35.0; X − Y > 0 | 1 |  |
| L2.11.2 | It stands on its base without tipping, also when a button is pressed. | analysis | stable at 5° table tilt; a 1.6 N press (actuation force of the catalogue switch) at the button farthest from the centre does not tip it (mass 150 g) | 1 |  |
| L3.11.2.1 | `stable` at 5°. | analysis | centre-of-mass projection inside the support polygon with margin ≥ 0.0 mm at 5° tilt | 1 |  |
| L3.11.2.2 | Tipping margin under a 1.6 N press. | analysis | margin > 0 | 1 |  |
| L2.11.3 | Flat underside; nothing below the floor except optional equal feet ≤ 3.0. | inspection | flatness ≤ 0.2; feet equal within 0.1 | 1 |  |
| L3.11.3.1 | Underside flatness and protrusions. | inspection | flatness ≤ 0.2; feet (if any) ≤ 3.0 high and equal within 0.1 | 1 |  |

### L1.12 It goes together: plungers in the lid from below, board in with the lid off, every screw reachable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | Each plunger loads into the lid from below: the stem goes up through the hole until the stop meets the plate underside, touching nothing on the way. | test | clear_of(LID, V-PLUNGER-INSTALL-k, 0.0); the final stop contact is designed contact | 2 |  |
| L3.12.1.1 | Plunger installation path. | test | d ≥ 0.0 | 2 | G5 |
| L2.12.2 | Lid off: the board assembly drops straight down onto the standoffs without hitting anything. | test | clear_of(BASE, V-INSTALL, 0.2), V-INSTALL excluding the V-SEAT columns | 2 |  |
| L3.12.2.1 | Installation path clear. | test | d ≥ 0.20 | 2 |  |
| L2.12.3 | The lid with its plungers closes straight down over the populated board without the plungers touching it. | test | clear_of(M-BOARD-ASSY ∪ BASE, V-LID-CLOSE, 0.0): the plungers and lid swept from 20 above the closed pose; rebate and boss contact at the end is designed contact | 2 |  |
| L3.12.3.1 | Lid-closing sweep. | test | d ≥ 0.0 | 2 |  |
| L2.12.4 | A screwdriver reaches every board screw (lid off) and the lid and board screws are separate. | analysis | clear_of(BASE, V-DRIVER-1..4, 0.0); no shared fastener | 1 |  |
| L3.12.4.1 | Driver columns clear. | analysis | d ≥ 0.0 | 1 |  |
| L3.12.4.2 | Judge confirms no fastener is shared. | inspection | shared fasteners = 0 | 1 |  |

### L1.13 Package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | The package holds `base.stl`, `lid.stl`, `plunger.stl` (closed pose, plungers at rest, mm), the `.scad` source, `layout.json` (poses, four plunger instances, print orientations) and `report.json` (the agent's own checks). | inspection | all present and readable; each STL's largest bounding-box axis within 5 to 200 | 3 |  |
| L3.13.1.1 | Files present and parse; units are mm. | inspection | 6 of 6 files present; each STL's largest bounding-box axis within 5 to 200 | 3 | G0 |
| L3.13.1.2 | The declared layout verifies under the seating rule. | analysis | board underside on standoff tops ≤ 0.10; hole-axis residual ≤ 0.25; each plunger's stop on the plate underside ≤ 0.10 | 3 |  |
| L2.13.2 | The agent's own clearance report agrees with the judge's measurements. | analysis | for every clear_of / inside L3 the agent reports, same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 |  |
| L3.13.2.1 | Self-report versus judge. | analysis | 100% agreement within 0.10 | 1 |  |

---

## 5. Counts

| Level | Count |
|---|---|
| L1 | 13 |
| L2 | 48 |
| L3 | 82 (weight 3: 34, weight 2: 34, weight 1: 14; total weight 184) |


Gates (a failure makes a design WRONG regardless of score; section 8): **G0** package (L3.1.1.1, L3.13.1.1); **G1** manifold, separate bodies (L3.3.4.2, L3.8.1.1, L3.8.1.2, L3.10.2.1); **G2** board fit and keep-outs (L3.2.1.1, L3.2.2.1, L3.4.1.1, L3.4.2.1); **G3** USB plug seats through the rear wall (L3.1.3.1, L3.5.1.1); **G4** board fixed on four pilot standoffs (L3.3.1.1, L3.3.1.2, L3.3.1.3, L3.3.3.1); **G5** buttons: array, plunger hole clearance, travel, actuation, retention, install (L3.1.2.1, L3.1.2.2, L3.6.1.1, L3.6.1.2, L3.6.2.2, L3.7.1.1, L3.7.2.1, L3.7.3.1, L3.12.1.1); **G6** lid screws: four bosses and holes (L3.8.3.1, L3.8.3.2, L3.8.4.1, L3.8.4.2).

---

## 6. Feasibility: a design that meets every number

A concrete design in the board frame, checked with a `manifold3d` model (base and lid one shell each; board parts, keep-outs, plug envelope, bosses, bottomed plungers clear; board clearance 0.5).

| Feature | Value |
|---|---|
| Buttons | centres X 25.475, 44.525; Y 5.0, 24.05 (19.05 pitch); body Z 0 to 3.8, actuator top 4.3 |
| Pico | on sockets (Z 8.5), PCB X 9.5 to 60.5, Y 27.2 to 48.2; pins on grid columns 2 to 21 and rows 10 and 17; USB mouth (8.2, 37.7, 10.9) |
| Cavity | X −7.0 to 77.0, Y −1.2 to 51.2 (board clearance 1.2 at the Y sides, so the Ø6.0 head columns of the corner holes, which reach 1.0 past the board edge, stay clear of the walls); floor top Z −5.6 (standoff height 4.0), floor 2.5 thick |
| Walls | 3.0 thick; outer X −10.0 to 80.0, Y −4.2 to 54.2, Z −8.1 to 19.0 |
| Standoffs | Ø6.0 under the four board holes (pitch 66.0 × 46.0), pilot Ø1.7, 6.0 deep |
| Rebate | upstand 1.5 from Z 16.5 to 19.0; rebate floor Z 16.5 |
| Lid | plate Z 16.5 to 19.0 (2.5); outline inset 1.75 from the outer faces; four M3 holes Ø3.4 |
| Lid bosses | Ø6.0 at (−3.5, 12.0), (−3.5, 47.0), (73.5, 8.0), (73.5, 42.0) from the floor to Z 16.5, pilot Ø2.5, 8 deep; gap to the board 0.5 |
| Plunger holes | four Ø5.8 (stem Ø5 + 2 × 0.4) at the button axes; ligament to each other 13.2 |
| Plunger | stem Ø5.0 from the tip (Z 5.3) up to Z 21.5; flange Ø9.0 (40° cone Z 13.1 to 15.5, ring to 16.5) stopping on the plate underside (Z 16.5); proud 2.5 at rest, 1.0 at bottoming |
| Travel | tip to body top 1.5 (T = 1.5); z_r = 5.3; z_b = 3.8 (in [3.8, 4.05]); idle gap above the actuator 1.0; overtravel 0.25 |
| USB opening | −X wall, Y 32.4 to 43.0, Z 7.1 to 14.7 (10.6 × 7.6); ligament to the rebate floor 1.8 |
| Margins | V-KO-TOP gap 0.5; head columns to the walls 0.2; USB plug to the enclosure 0.30; plungers to Pico 0.65; bosses to board 0.5 |
| Outside size | 90.0 × 58.4 × 29.6 with the plungers at rest, Z −8.1 to 21.5 (limit 95 × 70 × 35) |
| Print | base open side up, lid outer face down, plunger tip down (bed contact 24%); no overhang |

The lid is loaded with its plungers from below, then lowered straight over the populated board: the flange (Ø9.0 at Z 13.1 to 16.5) clears the Pico top (9.5) by 3.6.

---

## 7. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 (design.json) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout declared: 2 x 2 buttons at 19.05 mm pitch, Pico 2 behind them on sockets, USB at the rear | L2.1.1 to L2.1.5 | L3.1.1.1, L3.1.2.1, L3.1.2.2, L3.1.2.3, L3.1.3.1, L3.1.3.2, L3.1.3.3, L3.1.4.1, L3.1.5.1, L3.1.5.2 | L1.1 | inspection | "four 6 mm tactile switches on a 70 x 50 perfboard at 19.05 mm pitch with a Pico 2 above them", "Micro-USB opens at the rear" |
| L1.2 | Board fits inside with 0.5 mm clearance | L2.2.1 to L2.2.2 | L3.2.1.1, L3.2.1.2, L3.2.2.1 | L1.2 | analysis | "a 70 x 50 perfboard" |
| L1.3 | Four standoffs under the corner holes, with M2 pilots | L2.3.1 to L2.3.4 | L3.3.1.1, L3.3.1.2, L3.3.1.3, L3.3.2.1, L3.3.2.2, L3.3.3.1, L3.3.3.2, L3.3.4.1, L3.3.4.2, L3.3.4.3 | L1.3 | inspection | a board with a hole in each corner (as the 70 x 50 specimen), held in the case |
| L1.4 | Clearance above and below the board | L2.4.1 to L2.4.3 | L3.4.1.1, L3.4.1.2, L3.4.2.1, L3.4.2.2, L3.4.3.1 | L1.4 | analysis | "a Pico 2 above them" on sockets, switches with legs |
| L1.5 | Micro-USB cable plugs in through the rear end wall with the lid on | L2.5.1 to L2.5.3 | L3.5.1.1, L3.5.1.2, L3.5.2.1, L3.5.3.1 | L1.5 | test | "Micro-USB opens at the rear" |
| L1.6 | Each plunger comes up through a hole in the top plate with 0.4 mm clearance | L2.6.1 to L2.6.4 | L3.6.1.1, L3.6.1.2, L3.6.2.1, L3.6.2.2, L3.6.2.3, L3.6.3.1, L3.6.3.2, L3.6.4.1 | L1.6 | inspection | "Each button plunger comes up through a top plate hole with 0.4 mm clearance" |
| L1.7 | Plunger has 1.5 mm of travel, presses the switch, and cannot fall out | L2.7.1 to L2.7.5 | L3.7.1.1, L3.7.2.1, L3.7.2.2, L3.7.2.3, L3.7.3.1, L3.7.3.2, L3.7.4.1, L3.7.5.1 | L1.7 | test | "1.5 mm travel before bottoming" |
| L1.8 | The top plate is a removable lid held by four M3 screws | L2.8.1 to L2.8.5 | L3.8.1.1, L3.8.1.2, L3.8.2.1, L3.8.2.2, L3.8.2.3, L3.8.3.1, L3.8.3.2, L3.8.3.3, L3.8.4.1, L3.8.4.2, L3.8.4.3, L3.8.5.1 | L1.8 | inspection | "base and a removable lid" (implied by a board that comes out) |
| L1.9 | Closed except the USB opening, the plunger holes and the screw holes; walls 2 to 4 mm | L2.9.1 to L2.9.4 | L3.9.1.1, L3.9.2.1, L3.9.2.2, L3.9.2.3, L3.9.3.1, L3.9.4.1 | L1.9 | analysis | "enclosure" |
| L1.10 | Prints without supports | L2.10.1 to L2.10.4 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1 | L1.10 | analysis | "printed on an FDM printer" (added) |
| L1.11 | Sits on a desk: compact and stable | L2.11.1 to L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.2.2, L3.11.3.1 | L1.11 | analysis | "macro pad" (desk use implied) |
| L1.12 | It goes together: plungers in the lid from below, board in with the lid off, every screw reachable | L2.12.1 to L2.12.4 | L3.12.1.1, L3.12.2.1, L3.12.3.1, L3.12.4.1, L3.12.4.2 | L1.12 | test | implied by a case with a removable lid and printed plungers |
| L1.13 | Package says what was built and its claims are true | L2.13.1 to L2.13.2 | L3.13.1.1, L3.13.1.2, L3.13.2.1 | L1.13 | inspection | needed by the judge (not in the brief) |

---

## 8. Judging this design

> `benchmarks/generalize/rubric.md` was not present when this file was written, so this
> section is the design-specific rubric for G13. It follows `benchmarks/enclosure/rubric.md`
> (sections 2 to 5 and the recipes of its section 3: load, `clear_of`, `inside`, apertures,
> distances, printability, stability) and adds what this design needs. When the generic rubric
> exists, it governs the procedure and report format and this section governs the numbers.

### 8.1 Inputs

| Input | Where | Used for |
|---|---|---|
| `base.stl`, `lid.stl`, `plunger.stl` | the design package (closed pose, plungers at rest, mm) | **every measurement** |
| `.scad` source | package | naming features; never for measuring |
| `layout.json` | package | declared poses, the four plunger instances and print orientations |
| `report.json` | package | L1.13 self-report check only |
| renders | package `views/*.png` | locating defects |
| `requirements.md`, `parts/*/part.json` | this folder and the parts folders | criteria and reference models |

The judge does **not** use the agent's code or transcript, earlier verdicts, `benchmarks/heldout.json`,
or any private design of Robin's. Renders locate defects; they never make a check pass.

### 8.2 Procedure

1. **Package gate (G0).** The files above exist and load; if the STLs are missing or unreadable, stop: DOES NOT MEET, one defect on the package L3.
2. **Units.** Load each STL with trimesh and build a `manifold3d.Manifold` (recipe 3.1 of the enclosure rubric). A body whose bounding-box maximum is not plausible in mm (outside 5 to 200) is a defect, never silently rescaled.
3. **Normalise the frame.** Put the closed enclosure in the enclosure frame (section 1.1): floor underside lowest, the USB end wall at −X. Use rotations by multiples of 90° and mirroring only; record the transform. Place the four plungers from `plunger.stl` and the declared poses; the plunger STL is graded once and each instance is graded in its place.
4. **Build the references independently** from `parts/*/part.json` at the declared poses (section 2), run the sanity checks R1 to R6, then verify the seating rule.
5. **Run every applicable L3** with Python, in order. Record the measured value, the limit, the signed margin (negative = fail) and PASS / FAIL / UNVERIFIED / N/A. **UNVERIFIED counts as FAIL.** N/A only for physical tests (unless a print was made) and checks the section 3 fixed decisions switch off.
6. **Look at the renders** after measuring, to confirm where each failure is and to catch defects no L3 covers (a floating fragment, a feature on the wrong side). Report those as observations; they change the verdict only if a re-measurement makes an L3 fail.
7. **Decide** (8.4) and **report** (8.5).

### 8.3 Measurement recipes specific to this design

- **Plunger measurements:** slice `plunger.stl` at mid-stem for the stem Ø (smallest enclosing circle); slice the lid at mid-plate for each hole (largest inscribed circle); clearance per side = (hole Ø − stem Ø) / 2 measured on the same axis. Tip face, flange width and stop face from slices every 0.25 mm along the axis.
- **Travel:** translate the plunger instance straight down in 0.05 steps, then bisect, until `pen(plunger, BASE ∪ LID ∪ M-BTN body)` > 0.01 mm³; T = the distance moved. The switch actuator (Ø3.5, top 4.3) is soft and is excluded from this sweep; the switch body is hard.
- **Tip heights:** z_r and z_b from the plunger's lowest point above the board top at rest and after the sweep; idle gap = z_r − 4.3; overtravel = 4.05 − z_b.
- **Retention:** the stop face is the largest downward-facing annulus above the tip; its Ø from the section; rest gap by `min_gap` to the plate underside.
- **Pattern:** button and hole centres from slices; pitch from the centre distances.
- **Apertures:** enclosure rubric recipe 3.4 on the −X wall; plunger holes and screw holes are listed openings.
- **Sweeps:** V-LID-CLOSE and V-PLUNGER-INSTALL by extruding the instance's silhouette along its path and using `clear_of`.
- **Rebate, lid fit, thickness, ligament, stability, printability:** enclosure rubric recipes 3.5 to 3.7.

### 8.4 Verdict

Gates: G0 package, G1 manifold and separate bodies, G2 board fit and keep-outs, G3 USB plug seats through the rear wall, G4 board fixed on four pilot standoffs, G5 buttons (array, plunger hole clearance, travel, actuation, retention, install), G6 lid screws.

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
| Board clearance to any surface (L3.2.1.1), mm | ≥ 0.5 |  |
| Pico in cavity (L3.2.2.1), mm | ≥ 0.2 |  |
| Standoff count, pitch X / Y, axis offset, mm | 4; 66.0 / 46.0 ± 0.25; ≤ 0.25 |  |
| Standoff OD, pilot Ø, depth, mm | 5.0 to 7.0; 1.6 to 1.8; ≥ 5.0 |  |
| Top / bottom keep-out d, mm | ≥ 0 / ≥ 0 |  |
| Button pitch X / Y, mm | 19.05 ± 0.10 |  |
| Pico height on sockets; USB direction | 8.5 ± 0.1; within 1° of −X |  |
| USB plug d; USB opening oversize d, mm | ≥ 0.3; ≥ 0 |  |
| USB opening W × H and centre, mm | ≤ 13.0 × 10.0; ≥ 10.6 × 7.6 |  |
| Plunger holes: count; centre offset to switch axis, mm | 4; ≤ 0.20 |  |
| Stem Ø; clearance per side, mm | 4.0 to 5.6; 0.40 ± 0.10 |  |
| Travel T per plunger, mm | 1.5 ± 0.15 |  |
| z_b; idle gap; overtravel, mm | 3.8 to 4.05; ≥ 0.5; 0.0 to 0.5 |  |
| Flange Ø − hole Ø; rest gap, mm | ≥ 2.0; ≤ 0.10 |  |
| Proud at bottoming, mm | ≥ 0.5 |  |
| Free travel intersection, mm³ | ≤ 0.01 |  |
| Lid plate; rebate fit per side; upstand | 2.0 to 3.0; 0.15 to 0.35; ≥ 1.0 |  |
| Lid bosses: count, pilot Ø, depth, OD; lid hole Ø; alignment | 4; 2.4 to 2.6, ≥ 10.0 − plate (≥ 6.0), ≥ 6.0; 3.4 ± 0.1; ≤ 0.3 |  |
| Opening counts: USB / plunger holes / unlisted | 1 / 4 / 0 |  |
| Wall / floor / lid thickness | 2.0 to 4.0 |  |
| Overhang patches; bed contact (base, lid / plunger) | 0; ≥ 50% / ≥ 20% |  |
| Shells base / lid / plunger | 1 / 1 / 1 |  |
| Closed envelope X × Y × Z | ≤ 95 × 70 × 35 |  |
| Install sweeps (plunger, board, lid) d | ≥ 0; ≥ 0.2; ≥ 0 |  |
| Self-report agreement | 100% within 0.10 |  |

---

## Audit

Adversarial audit (2026-10-24). Part ids checked with `parts.py` (all seven load and pass the gate; the five plan parts plus the two screws). Counts recomputed: L1 13 in `design.json` and in section 4, L2 48, L3 82, weights 34 / 34 / 14, total 184, matching section 5. Derived numbers recomputed from the instantiated `part.json` files: Pico PCB 51 × 21 at X 9.5 to 60.5 and Y 27.2 to 48.2, pin rows at Y 28.81 and 46.59 (grid rows 10 and 17 of the 70 × 50 specimen), pin X 10.87 to 59.13 on grid columns 2 to 21, USB mouth (8.2, 37.7, 10.9), button centres at 19.05 pitch, V-USB-PLUG overmold Z 7.4 to 14.4 and the 10.6 × 7.6 opening limits, plunger z_r 5.3, z_b 3.8, actuation 4.05, overtravel 0.25.

Fixes made in place:

1. **Feasibility failed L3.3.4.3.** The corner holes are 2.0 from the board edges and the head column V-HOLE-KO-k is Ø6.0, so it reaches 1.0 beyond the board edge; section 6's cavity had only 0.5 clearance at the Y sides, so the base wall entered the column (interference, d < 0). The cavity is now Y −1.2 to 51.2 (outer Y −4.2 to 54.2); outside size 90.0 × 58.4 × 29.6; A10 and the margins row updated. The driver columns V-DRIVER-k are covered by the same change. All other numbers of section 6 were re-walked (bosses to board 0.5, plunger to Pico 0.65, flange to Pico top 3.6, opening ligament 1.8, plunger bed contact 24%) and hold.
2. **Screw seating for the lid bosses.** L2.8.3 / L3.8.3.2 now require pilot depth ≥ 10.0 − lid plate thickness (section 6 has 8, needs 7.5), so the length-10 catalogue screw does not bottom before the lid clamps. The M2 board pilots keep the E1-01 limit (≥ 5.0): the length-6 screw reaches 4.4 below the 1.6 board, so a 5.0 pilot does not bottom. Note: the catalogue `screw_m2_selftap` gives only 4.4 engagement against its own `min_engagement` 5.0 (a catalogue property E1-01 shares); left as is.
3. **Hidden numbers moved into L1** (the text the agent gets): standoff OD 5 to 7 and coplanar tops (L1.3), 0.3 mm plug clearance (L1.5), plunger-hole alignment 0.2, stem Ø 4.0 to 5.6 and tip face ≥ 3.5 (L1.6), proud ≥ 0.5 at bottoming and flange ≥ 2 wider than the hole resting on the plate underside (L1.7), plate 2 to 3, fit 0.15 to 0.35, upstand ≥ 1 (L1.8), 45° and 15 mm print rule (L1.10).
4. **L3 rows with no number** (L3.1.1.1, L3.2.1.2, L3.10.1.1, L3.10.3.1, L3.10.4.1, L3.11.1.1, L3.11.2.1, L3.11.3.1, L3.12.4.2, L3.13.1.1) now carry a numeric band or count.

Checked and left alone: the z_b band [3.8, 4.05] is consistent with the catalogue (body top 3.8, actuation 4.05, `pusher_overtravel` 0.5); stem, hole, flange and travel numbers are mutually satisfiable; "above them" and "rear" are fixed as A1 and A2; no L2 contradicts another; the request text carries no number the judge needs that L1 lacks.
