# G47 Gearmotor and ultrasonic sensor bracket: requirements (L1 / L2 / L3)

A generalisation design for the OpenSCAD assembly agent, modelled on E1-01
(`benchmarks/enclosure/requirements.md`): catalogue parts (a gearmotor, an ultrasonic sensor module, a
magnet, M3 bolts) placed from datums into one printed bracket, with keep-out volumes, pockets,
windows and interference and clearance checks against reference models. The machine-readable request
(L1 only, `dev.json` format) is `design.json` next to this file. How a blind judge applies this
document is in section 7.

**Plan brief (verbatim):** "A robot-base bracket holding an N20 gearmotor (12 x 10 mm body, 3 mm D
shaft) in a clamp pocket and an HC-SR04 ultrasonic sensor (45 x 20 mm, 16 mm transducers at 26 mm
pitch) 40 mm forward. A 6 x 3 mm magnet pocket at the shaft end for an encoder. Two M3 bolts fix the
whole bracket to the chassis."

**How to read this.** L1 says what the owner needs, L2 turns it into an engineering requirement with
numbers, L3 is a concrete check Python can run on the delivered STL. Every row has a method
(inspection, analysis, demonstration, test, human, as in `design.json`), a pass/fail criterion with a
number and a tolerance, and a weight (3 = critical, 2 = major, 1 = minor). A `G<n>` after the weight
marks a gate: a failed gate makes the design WRONG (section 5). Every number that comes from an
assumption (section 3) is provisional until the owner confirms it. Do not relax a criterion because
the agent fails it.

---

## 1. Frames, tolerances and the two interference checks

### 1.1 Frames

- **Bracket frame:** **Z is up**, normal to the chassis; the bracket's **chassis face** (underside)
  is **Z = 0**. **Y is forward** (the sensor faces +Y). **X is along the motor's shaft axis, +X
  towards the shaft tip.** X = 0 is the gearbox output face, Y = 0 is the shaft axis (D1). The shaft
  axis is at (Y = 0, Z = z_m), with z_m declared by the design (band 8.0 to 30.0).
- The STL is delivered in this pose, mm. A design delivered mirrored or rotated by multiples of 90
  degrees is normalised into this frame before grading (the judge records the transform); that is
  never penalised.

### 1.2 Measurement tolerances

| Quantity | Tolerance e | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within e |
| angle | 0.5 degrees | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole / window / pocket diameter | largest inscribed circle of the section | |

### 1.3 The two interference checks

- **`clear_of(body, volume, clearance)`**: the minimum distance between the printed body and `volume`
  is >= `clearance`; reported as the signed minimum distance d (negative = penetration, with the
  volume). Pass: d >= clearance - e.
- **`slide(part, dx, dy, dz)`**: translate a reference part rigidly and report its intersection
  volume with the bracket.

A design never builds or edits the reference volumes: the grader generates them independently from
the catalogue and the declared layout. The agent may generate the same volumes for its own checks, but
its copies are not trusted.

**Designed contact for this design.** Parts that are meant to touch are excluded from every
interference and clearance check; for these only penetration (> 0.01 mm3) counts, and a distance of
zero is a pass:
- the motor's gearbox face on the stop wall's rear face;
- the motor body in its pocket (light clearance; a touch is allowed);
- the sensor board's lower edge on the slot floor, and its faces against the slot walls if they touch;
- the magnet seated on its pocket floor and in its pocket walls;
- an M3 chassis bolt's head on its counterbore floor, and its shank in the hole (a touch is allowed).

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue** (`benchmarks/generalize/parts/`): `n20_gearmotor`, `hc_sr04`, `magnet_disc_6x3`,
  `bolt_m3_iso4762`. These are the only place part numbers may live.
- **envelope:** swept or offset volumes made by Python from datums. Never drawn by hand.
- **computed:** surfaces and regions measured on the delivered STL.

### 2.2 Reference models (M-)

Placed by the grader from the layout the design declares and cross-checked against the STL. Bracket
frame, mm; the defaults below are the feasibility sketch's pose (section 6), not requirements.

| Name | What | Source | Size and pose | Datums |
|---|---|---|---|---|
| **M-MOTOR** | N20 gearmotor | `n20_gearmotor` | body 12 x 10, gearbox 9 long, can 15 long (24 in all), shaft dia 3.0 x 10.0; shaft along +X on (Y = 0, Z = z_m), gearbox face at X = x_f (declared; sketch 0); the 12 mm side along Y (declared orientation) | `SHAFT_AXIS`, `FACE`, `BACK`, `SHAFT_TIP`, `HOLE` |
| **M-HC** | HC-SR04 module | `hc_sr04` | PCB 45 x 20 x 1.2, cans dia 16.0 up to 15.0 (PCB bottom to can front), header body 2.5 on the back; transducers face +Y; pose declared (sketch: PCB bottom plane at Y = 40.0, board lower edge at Z = 7.0, board centre X = -1.0) | `PCB_BOTTOM`, `PCB_TOP`, `TX_AXIS`, `RX_AXIS`, `TRANSDUCERS`, `FRONT`, `PINS` |
| **M-MAG** | encoder magnet | `magnet_disc_6x3` | dia 6.0 x 3.0, axis along X, seated on its pocket floor | `AXIS`, `BOTTOM`, `TOP` |
| **M-BOLT-k** (k = 1, 2) | M3 chassis bolt | `bolt_m3_iso4762` | head dia 5.5 x 3.0, shank 3.0, length declared; axis along Z, head up, head bearing on the counterbore floor, shank down through the plate | `AXIS`, `HEAD_BEARING`, `HEAD_TOP`, `TIP` |
| **RBA** | reference bracket assembly = M-MOTOR, M-HC, M-MAG, M-BOLT-1..2 | assembled | as above | all |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Definition (bracket frame, mm; at the declared pose) |
|---|---|---|
| **V-SHAFT** | the free shaft path | dia 3.5 cylinder on `SHAFT_AXIS` from `FACE` to `SHAFT_TIP` (shaft 3.0 + 0.25 radial) |
| **V-TERM** | the motor's rear terminals | the 12 x 10 section behind `BACK`, 4.0 long (catalogue `rear_terminals`) |
| **V-MOTOR-INSTALL** | motor installation path | M-MOTOR's body swept straight back (-X) from its seated pose by 60, minus the seated pose |
| **V-BEAM-TX**, **V-BEAM-RX** | the sound beam | dia 18.0 cylinder (16.0 + 2 x 1.0, the catalogue `transducer_clear_margin`) on `TX_AXIS` / `RX_AXIS` from `PCB_TOP` forward to 40 beyond `FRONT` |
| **V-WIRES** | header connector and wires | the catalogue `header_wires` box behind the board: 12.16 (along the header) x 4.54 x 12.0, behind `PCB_BOTTOM` minus the 2.5 header body |
| **V-HC-INSTALL** | sensor drop-in path | M-HC (PCB, cans and header) swept straight up (+Z) from its seated pose by 60, minus the seated pose |
| **V-BOLT-TOOL-k** | hex-key column over each chassis bolt | dia 5.5 from the head top to 25 above it (the catalogue `tool_access`) |
| **V-PLATE** | the base plate | the bracket's material between Z = 0 and its plate top (computed: the largest horizontal slab) |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-MOTOR | size | 12 x 10 +/-0.2; total body 24 +/-0.2; shaft 3.0 x 10.0 |
| R2 | M-HC | size and pitch | 45 x 20 PCB; cans dia 16; pitch 26.0 +/-0.1; height 15.0 |
| R3 | M-HC | `TX_AXIS`, `RX_AXIS` along +Y | within 1.0 degrees |
| R4 | M-BOLT | head and shank | 5.5 x 3.0 and 3.0 (+/-0.2) |
| R5 | RBA | models do not collide with each other | intersection <= 0.01 mm3 |
| R6 | V- envelopes | datums equal the model datums | <= 0.01 |

**Seating rule.** Each reference part is placed at the pose declared in the layout. The grader
verifies it: `FACE` lies on the stop wall (distance <= 0.10); the board's lower edge lies on the slot
floor (<= 0.10); `SHAFT_AXIS` is coaxial with the shaft hole and the magnet pocket (residual <= 0.15
and <= 0.30); each `HEAD_BEARING` lies on its counterbore floor (<= 0.10). If the declaration is
missing or fails, the parts are seated by that fit instead.

---

## 3. Assumptions (A) and fixed decisions (D)

Each A-row gives the value chosen and the uncertainty. **A1, A3 and A5 matter most.**

| # | Question | Value chosen | Why / uncertainty |
|---|---|---|---|
| **A1** | What does "40 mm forward" measure, and which way does the shaft point? | The sensor faces **forward (+Y)**; the motor's shaft axis is **horizontal and sideways (X)**, as in a differential-drive base; **40.0 mm** is the distance along Y from the shaft axis to the **sensor board's rear face** (`PCB_BOTTOM`). | A wheel motor's shaft is lateral. **Uncertainty: high.** Other readings (to the transducer fronts, to the board centre, from the motor body's front) would shift the number by 6 to 15 mm. Confirm. |
| **A2** | Motor section and clamp pocket? | Body 12.0 x 10.0 (datasheet); the "clamp pocket" is a pocket 0.10 to 0.30 larger than the body on **each of its two dimensions** (0.05 to 0.15 per side), light press by printing tolerance, at least 15.0 long, open at the rear. | `n20_gearmotor` mount note: a pocket round the 12 x 10 body, body in the pocket is designed contact. **Uncertainty: medium** (printer; real motors have rounded corners and 0.2 mm variation). |
| **A3** | What is "a magnet pocket at the shaft end for an encoder"? | One pocket dia 6.10 to 6.30, depth 3.15 to 3.35, in a wall facing the shaft tip, **coaxial with the shaft axis**, mouth towards the shaft; with the magnet seated on the pocket floor its face is **2.0 mm (1.5 to 2.5)** from the shaft tip and recessed 0.0 to 0.6 below the wall face. | An axially magnetised disc seen by a hall sensor on the shaft's end; the recess keeps the wall clear. **Uncertainty: high.** The magnet may instead belong on the shaft tip, with the pocket in a rotor part the brief does not describe. Confirm. |
| **A4** | Gearbox and motor dimensions? | Gearbox 9.0, can 15.0, shaft dia 3.0 x 10.0, shaft centred on the 12 x 10 section (+/-0.5), rear terminals 4.0 deep (catalogue). | `n20_gearmotor`; the gearbox length depends on the reduction ratio. **Uncertainty: medium.** |
| **A5** | HC-SR04 details? | PCB 45 x 20 x 1.2, cans dia 16.0 at 26.0 pitch (symmetric about the board centre), 15.0 overall to the can fronts, 4-pin header 2.54 pitch on the back at the -Y edge (2.0 in), no mounting holes. | `hc_sr04` datasheet note. **Uncertainty: medium.** The header side and the PCB thickness vary between clones; check the owner's unit. |
| **A6** | Sound beam? | A straight dia 18.0 cylinder in front of each can, from the board's front face outward 40 mm, must be free of printed material. | The cone is about 15 degrees; the catalogue margin is 1.0. **Uncertainty: medium.** |
| **A7** | How is the sensor held? | In a slot: a front plate with two windows, a rear wall with a notch for the header, side walls, a floor; the board drops in from above. The slot is 1.3 to 1.8 deep (board 1.2 + 0.1 to 0.6) and 0.2 to 0.6 wider than the board (45.2 to 45.6). Windows are round (largest inscribed circle dia 18.0 to 19.0) with a straight channel of the same width up to the plate's top edge (a keyhole open at the top): the sensor drops in from above with its cans in the windows, which a closed round window forbids. | No mounting holes on the board; plate coverage and a slot hold it. **Uncertainty: medium.** |
| **A8** | Chassis bolts? | Two M3 bolts, vertical, in a flat base plate 4.0 to 8.0 thick: clearance dia 3.3 to 3.5, counterbore dia 5.7 to 6.1 and 3.0 to 3.4 deep, axes 20.0 to 60.0 apart; length declared, tip 5.0 to 15.0 below the chassis face. The chassis hole pattern is not given. | Catalogue `clearance_diameter`, `counterbore_*`. **Uncertainty: high** (hole pitch and chassis thickness are the owner's). |
| **A9** | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed, no supports, chassis face on the bed. Round holes up to dia 20.0 in vertical walls are exempt from the overhang rule here (the dia 18 sensor windows cannot be oriented otherwise); bridges up to 15.0. | Common printers. **Uncertainty: low.** |
| **A10** | Size? | Bracket no larger than 60 x 60 x 35 (X x Y x Z). | A tight design is about 50 x 52 x 30. |
| **A11** | Strength? | Every wall and ligament at least 2.0; base plate 4.0 to 8.0; at least 2.0 of material round every bolt hole and counterbore. | 5 perimeters at 0.4. |
| A12 | Mass for stability? | Volume x 0.45 g/cm3 + motor 10 g + sensor 8 g + magnet 1 g. | PLA at about 35% infill. |
| A13 | Wire exits, strain relief, a cover? | None needed. | Not in the brief. |

| # | Fixed decision (a choice that would otherwise be ambiguous) |
|---|---|
| **D1** | Frame as in 1.1. The bracket is **one printed body**, chassis face down. |
| **D2** | The motor is installed from the rear (-X), sliding in until its gearbox face meets the stop wall; nothing is behind the motor for 4.0 (terminals). |
| **D3** | The motor's shaft passes through a hole in the stop wall and its free end faces an encoder wall carrying the magnet pocket (A3). |
| **D4** | The sensor's transducers face +Y; the line through them is horizontal (within 1 degree). The module may be mounted header-up or header-down. |
| **D5** | The sensor is held at its **rear** face's plane `PCB_BOTTOM` = 40.0 +/-0.5 in front of the shaft axis (A1). |
| **D6** | Print orientation: chassis face on the bed (Z up as delivered). |

---

## 4. Requirements tree

### L1.1 Motor and sensor placed from the catalogue, the sensor 40 mm forward of the shaft

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.1.1 | The design declares the poses of the motor and sensor, the magnet, the two bolts (with lengths) and the print orientation in a layout file. | inspection | file present, parses, names the catalogue parts | 3 |
| L3.1.1.1 | Layout parses and every catalogue id exists. | inspection | true | 3 |
| L2.1.2 | Orientations. | inspection | `SHAFT_AXIS` horizontal and within 1.0 degrees of X; `TX_AXIS`, `RX_AXIS` within 1.0 degrees of +Y; the line through the two transducers within 1.0 degrees of horizontal | 3 |
| L3.1.2.1 | Axis directions in the declared layout. | inspection | as L2.1.2 | 3 |
| L2.1.3 | The sensor is 40 mm forward (A1, D5). | inspection | distance along Y from `SHAFT_AXIS` to `PCB_BOTTOM` | 3 G2 |
| L3.1.3.1 | Forward distance. | inspection | 39.5 to 40.5 | 3 G2 |
| L2.1.4 | The parts do not collide. | analysis | pairwise intersections of M-MOTOR, M-HC and M-MAG | 3 |
| L3.1.4.1 | Pairwise interference of the reference parts. | analysis | each <= 0.01 mm3 | 3 |
| L3.1.4.2 | Shaft axis height z_m. | inspection | 8.0 to 30.0 | 1 |

### L1.2 The motor's 12 x 10 body sits in a clamp pocket, a little bigger than the body

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.2.1 | Pocket section and length (A2). | inspection | each of the two section dimensions = body dimension + 0.10 to 0.30; length >= 15.0 | 3 |
| L3.2.1.1 | Pocket section, both dimensions (measured on a slice at mid-length, parallel sides). | inspection | 12.1 to 12.3 and 10.1 to 10.3 (for the declared orientation) | 3 |
| L3.2.1.2 | Pocket length from the stop wall's rear face. | inspection | >= 15.0 | 3 |
| L2.2.2 | The pocket is coaxial with the shaft and parallel to it. | analysis | axis offset <= 0.15; angle <= 0.5 degrees | 3 |
| L3.2.2.1 | Pocket axis against `SHAFT_AXIS`. | analysis | <= 0.15 | 3 |
| L3.2.2.2 | Pocket axis direction against the shaft. | analysis | <= 0.5 degrees | 2 |
| L2.2.3 | The motor fits the pocket. | analysis | M-MOTOR body against BRACKET | 3 G3 |
| L3.2.3.1 | Intersection of the M-MOTOR body with the bracket, gearbox face contact excluded. | analysis | <= 0.01 mm3 | 3 G3 |
| L2.2.4 | The pocket holds the motor. | test | `slide(M-MOTOR, 0.5)` in +Y, -Y, +Z, -Z and +X | 2 |
| L3.2.4.1 | Each of the five slides intersects the bracket. | test | > 0.01 mm3 in all 5 | 2 |
| L2.2.5 | Material round the pocket (A11). | analysis | wall between the pocket and any outer surface | 2 |
| L3.2.5.1 | Minimum pocket wall thickness (roof and sides). | analysis | >= 2.0 | 2 |

### L1.3 The gearbox face rests on a stop wall; the shaft turns free; the motor slides in from the rear

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.3.1 | A stop wall at the gearbox face (D2, D3). | inspection | distance from `FACE` to the wall's rear face; wall area on the face; wall thickness | 3 |
| L3.3.1.1 | `FACE` against the stop wall's rear face, and the wall's area on the gearbox face (face area 120 minus the shaft hole). | inspection | distance <= 0.10; wall area >= 60 mm2 | 3 |
| L3.3.1.2 | Stop wall thickness along X. | inspection | 2.0 to 6.0 | 2 |
| L2.3.2 | The shaft passes through the wall and turns free. | analysis | hole dia; V-SHAFT | 3 |
| L3.3.2.1 | Shaft hole diameter (largest inscribed circle) and axis offset. | inspection | dia 3.6 to 4.6; offset <= 0.15 | 3 |
| L3.3.2.2 | Shaft path clear: clear_of(BRACKET, V-SHAFT, 0.0). | analysis | d >= 0.0 | 3 |
| L2.3.3 | The motor installs from the rear and its terminals are clear. | test | clear_of(BRACKET, V-MOTOR-INSTALL, 0.0); clear_of(BRACKET, V-TERM, 0.0) | 3 G3 |
| L3.3.3.1 | Motor install path clear. | test | d >= 0.0 | 3 G3 |
| L3.3.3.2 | Rear terminal volume clear. | analysis | d >= 0.0 | 2 |

### L1.4 A 6 x 3 mm magnet pocket faces the shaft tip, coaxial with the shaft, 2 mm away

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.4.1 | One round magnet pocket (A3). | inspection | count 1; dia 6.10 to 6.30; depth 3.15 to 3.35 | 3 |
| L3.4.1.1 | Pocket count. | inspection | 1 | 3 |
| L3.4.1.2 | Pocket diameter (largest inscribed circle at mid-depth). | inspection | 6.10 to 6.30 | 3 |
| L3.4.1.3 | Pocket depth along its axis. | inspection | 3.15 to 3.35 | 3 |
| L2.4.2 | The pocket lines up with the shaft and opens towards it. | analysis | axis against `SHAFT_AXIS`; mouth direction | 3 |
| L3.4.2.1 | Pocket axis against `SHAFT_AXIS`. | analysis | offset <= 0.30; angle <= 1.0 degrees | 3 |
| L3.4.2.2 | Pocket mouth beyond the shaft tip, facing it. | analysis | the mouth plane is at +X of `SHAFT_TIP`, its outward normal -X (within 1.0 degrees) | 3 |
| L2.4.3 | The seated magnet is 2.0 mm from the shaft tip and recessed. | analysis | M-MAG seated on the pocket floor | 3 G4 |
| L3.4.3.1 | `gap(SHAFT_TIP, M-MAG face)` along X. | analysis | 1.5 to 2.5 | 3 G4 |
| L3.4.3.2 | Recess of the magnet face below the surrounding wall face. | analysis | 0.0 to 0.6 | 2 |
| L3.4.3.3 | Material behind the pocket floor along X. | analysis | >= 1.0 | 2 |
| L3.4.3.4 | Ligament from the pocket rim to the nearest wall edge. | analysis | >= 1.5 | 2 |
| L3.4.3.5 | The shaft does not touch the encoder wall. | analysis | clear_of(BRACKET, shaft cylinder dia 3.0 from `FACE` to `SHAFT_TIP` + 1.0, 0.0) | 2 |

### L1.5 The HC-SR04 sits in a slot behind a front plate and drops in from above

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.5.1 | Slot dimensions (A7). | inspection | depth 1.3 to 1.8; width 45.2 to 45.6; floor at the board's lower edge | 3 |
| L3.5.1.1 | Slot depth (the distance between the rear wall's front face and the plate's rear face, at mid-height). | inspection | 1.3 to 1.8 | 3 |
| L3.5.1.2 | Slot width between the side walls. | inspection | 45.2 to 45.6 | 2 |
| L3.5.1.3 | Slot floor height against the board's lower edge. | inspection | within 0.10 of it (the board rests on the floor) | 2 |
| L2.5.2 | The front plate and the rear wall hold the board. | analysis | area of the board's faces covered by printed material | 3 |
| L3.5.2.1 | Front plate coverage of the board's front face (area of the face under plate material, windows and their channels excluded). | analysis | >= 200 mm2 | 3 |
| L3.5.2.2 | Rear wall coverage of the board's rear face. | analysis | >= 400 mm2 | 2 |
| L2.5.3 | The board drops in from above. | test | clear_of(BRACKET, V-HC-INSTALL, 0.05) | 3 |
| L3.5.3.1 | Drop-in path clear. | test | d >= 0.05 | 3 |
| L2.5.4 | The module fits the slot. | analysis | M-HC against BRACKET | 3 G5 |
| L3.5.4.1 | Intersection of M-HC with the bracket, floor and wall contact excluded. | analysis | <= 0.01 mm3 | 3 G5 |

### L1.6 Two windows 18 to 19 mm across, coaxial with the transducers, beams free

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.6.1 | One window per transducer in the front plate, round with an open top channel (A6, A7). | inspection | count 2; round part dia 18.0 to 19.0 (largest inscribed circle); axes within 0.30 of `TX_AXIS`, `RX_AXIS`; pitch 26.0 +/-0.3 | 3 |
| L3.6.1.1 | Window count and coaxiality. | inspection | 2; offsets <= 0.30 | 3 |
| L3.6.1.2 | Window diameter (largest inscribed circle; the channel has the same width), each. | inspection | 18.0 to 19.0 | 3 |
| L3.6.1.3 | Window pitch. | inspection | 26.0 +/-0.3 | 2 |
| L2.6.2 | The beams are free. | analysis | clear_of(BRACKET, V-BEAM-TX and V-BEAM-RX, 0.0) | 3 G5 |
| L3.6.2.1 | Beam volumes clear. | analysis | d >= 0.0 | 3 G5 |
| L2.6.3 | Material round the windows. | analysis | ligament from each window to the plate sides and bottom and to the other window (the open top excepted) | 1 |
| L3.6.3.1 | Minimum ligament round the windows (open top excepted). | analysis | >= 1.5 | 1 |

### L1.7 Header and wires have room; the rear wall lets the header through

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.7.1 | The header-wire volume behind the board is free (A5). | analysis | clear_of(BRACKET, V-WIRES, 0.0) | 3 |
| L3.7.1.1 | Wire volume clear. | analysis | d >= 0.0 | 3 |
| L2.7.2 | The header body clears the rear wall by 0.2. | analysis | clear_of(BRACKET, the header body and pins of M-HC, 0.2) | 2 |
| L3.7.2.1 | Header clearance. | analysis | d >= 0.20 | 2 |

### L1.8 Two M3 bolts fix the bracket to the chassis through a flat base plate

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.8.1 | Two vertical holes (A8). | inspection | count 2; axes perpendicular to the chassis face within 1.0 degrees; 20.0 to 60.0 apart | 3 G6 |
| L3.8.1.1 | Hole count and direction. | inspection | 2; within 1.0 degrees of Z | 3 G6 |
| L3.8.1.2 | Distance between the two hole axes. | inspection | 20.0 to 60.0 | 2 |
| L2.8.2 | Hole and counterbore sizes. | inspection | as the rows | 3 |
| L3.8.2.1 | Hole diameter, each, through the plate. | inspection | 3.3 to 3.5 | 3 |
| L3.8.2.2 | Counterbore diameter and depth, each. | inspection | dia 5.7 to 6.1; depth 3.0 to 3.4 | 2 |
| L3.8.2.3 | Material under each head (counterbore floor to the chassis face). | inspection | >= 2.0 | 2 |
| L2.8.3 | The bolts reach through. | analysis | M-BOLT against BRACKET and the chassis face | 2 |
| L3.8.3.1 | Tip below the chassis face. | analysis | 5.0 to 15.0 | 2 |
| L3.8.3.2 | Bolt shank intersection with the bracket. | analysis | <= 0.01 mm3 | 2 |
| L2.8.4 | A hex key reaches each head. | analysis | clear_of(BRACKET, V-BOLT-TOOL-1..2, 0.0) | 2 |
| L3.8.4.1 | Key columns clear. | analysis | d >= 0.0 | 2 |
| L2.8.5 | Material round the holes (A11). | analysis | ligament from each hole and counterbore to the plate edges and to other features | 2 |
| L3.8.5.1 | Minimum ligament. | analysis | >= 2.0 | 2 |

### L1.9 Strong enough: walls, plate and load path

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.9.1 | Local thickness and plate (A11). | analysis | ray cast inward from sampled surface points | 2 |
| L3.9.1.1 | Minimum local thickness of every printed feature. | analysis | >= 2.0 | 2 |
| L3.9.1.2 | Base plate thickness. | inspection | 4.0 to 8.0 | 2 |
| L2.9.2 | The bracket is one connected body and its load path to the bolts is solid. | analysis | shells; section areas | 3 G1 |
| L3.9.2.1 | Shell count. | analysis | 1 | 3 G1 |
| L3.9.2.2 | Minimum section area of the plate on planes Y = const between the motor pocket and the sensor slot. | analysis | >= 150 mm2 | 2 |
| L3.9.2.3 | The encoder wall's attachment to the plate. | analysis | contact area >= 40 mm2 | 2 |

### L1.10 The bracket prints on an FDM printer without supports, chassis face down

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.10.1 | The mesh is manifold and one shell. | analysis | manifold3d accepts it; 1 shell | 3 G1 |
| L3.10.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 G1 |
| L2.10.2 | In its stated orientation (D6) no part has an unsupported overhang steeper than 45 degrees from vertical, except round holes <= 20.0 in vertical walls (A9) and bridges <= 15.0. | analysis | 0 offending faces (area > 1 mm2) | 2 |
| L3.10.2.1 | Overhang and bridge scan. | analysis | as L2.10.2 | 2 |
| L2.10.3 | The chassis face is flat on the bed. | analysis | bed contact >= 50% of the plan bounding box; lowest Z = 0 +/-0.05 | 1 |
| L3.10.3.1 | Bed contact and lowest Z. | analysis | as L2.10.3 | 1 |
| L2.10.4 | No feature thinner than 0.8; clearances >= 0.1. | analysis | thin-feature scan | 1 |
| L3.10.4.1 | Thin features. | analysis | min feature >= 0.8 | 1 |
| L2.10.5 | The part fits 200 x 200 x 200. | inspection | bbox <= 200 per axis | 1 |
| L3.10.5.1 | Bounding box. | inspection | <= 200 | 1 |

### L1.11 Compact and stable: at most 60 x 60 x 35 mm, flat on the chassis

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.11.1 | Size. | inspection | X <= 60.0, Y <= 60.0, Z <= 35.0 | 1 |
| L3.11.1.1 | Bounding box. | inspection | as L2.11.1 | 1 |
| L2.11.2 | The chassis face is flat. | inspection | flatness <= 0.2; nothing below Z = 0 | 1 |
| L3.11.2.1 | Underside planarity and lowest Z. | inspection | as L2.11.2 | 1 |
| L2.11.3 | It stands on its chassis face without tipping. | analysis | stable at 5 degrees tilt with the motor, sensor and magnet fitted (A12) | 1 |
| L3.11.3.1 | Centre of mass inside the support polygon at 5 degrees tilt in every direction. | analysis | margin >= 0 | 1 |

### L1.12 The package says what was built and where, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.12.1 | The package holds `bracket.stl` (chassis face at Z = 0, bracket frame, mm), the `.scad` source, the layout file (L2.1.1) and the agent's own clearance report. | inspection | all present and readable | 3 G0 |
| L3.12.1.1 | Files present and parse; the STL's largest bounding-box axis is within 20 to 200 mm (units check). | inspection | true | 3 G0 |
| L3.12.1.2 | The declared layout verifies under the seating rule (2.4). | analysis | `FACE` on the stop wall <= 0.10; board lower edge on the floor <= 0.10; shaft and pocket coaxial <= 0.15 and <= 0.30; heads on floors <= 0.10 | 3 |
| L2.12.2 | The agent's own report agrees with the judge. | analysis | every clear_of value it reports: same pass/fail, difference at most 0.10 | 1 |
| L3.12.2.1 | Self-report against judge. | analysis | 100% within 0.10 | 1 |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 41 |
| L3 | 67 |

**Gates** (a failure makes a design WRONG regardless of score): G0 package (L3.12.1.1); G1 one
manifold body (L3.9.2.1, L3.10.1.1); G2 the sensor is 40 mm forward (L3.1.3.1); G3 the motor fits and
installs (L3.2.3.1, L3.3.3.1); G4 the magnet is 2 mm from the shaft tip (L3.4.3.1); G5 the sensor
fits and its beams are free (L3.5.4.1, L3.6.2.1); G6 two chassis bolts (L3.8.1.1).

---

## 6. Feasibility

A concrete design that meets every row exists. Bracket frame, mm (X = 0 at the gearbox face, Y = 0 on
the shaft axis, Z = 0 the chassis face).

**Plate.** X -26.1..24.1 (50.2), Y -8.5..43.8 (52.3), Z 0..5.5 (5.5 thick, within 4.0..8.0).
Closed envelope 50.2 x 52.3 x 29.4 (<= 60 x 60 x 35). Section on Y = 25: 50.2 x 5.5 = 276 mm2
(>= 150).

**Motor.** Shaft axis at Y = 0, Z = 12.0. Body 12 (Y) x 10 (Z) in a tunnel 12.2 x 10.2 (Y +/-6.1, Z
6.9..17.1, clearance 0.1 per side), X -18.0..0 (length 18.0 >= 15), open at the rear, walls 2.4 (outer
Y +/-8.5), roof top Z = 19.5; floor under the motor solid up to Z = 6.9. Stop wall X 0..3.0 with a dia
4.0 hole on the axis; the gearbox face (X = 0) rests on it (wall area on the face 120 - 12.6 = 107
mm2). The motor's back is at X = -24, 6 mm behind the tunnel; the terminal volume X -28..-24 is empty
(the plate top, Z 5.5, is below Z 7.0). Install sweep: free, since nothing is behind the tunnel above
Z 5.5. Shaft: X 0..10, V-SHAFT dia 3.5 fits the 4.0 hole.

**Encoder.** Wall X 11.75..16.5 (4.75), Y +/-8.5, Z 0..19.5, fused to the plate (contact 81 mm2).
Pocket dia 6.15, depth 3.25 from X = 11.75 to 15.0, on the axis. Magnet X 12.0..15.0: face **2.0**
from the tip (X = 10), recessed 0.25, material behind it 1.5, pocket rim to the wall's Y edge 5.4.

**Sensor.** Board centre X = -1.0: PCB X -23.5..21.5, Y 40.0..41.2, Z 7.0..27.0 (lower edge on the
slot floor, Z 7.0; floor over a pedestal from the plate top). `PCB_BOTTOM` at Y = **40.0** (forward
distance 40.0). Slot: Y 39.9..41.4 (depth 1.5), X -23.65..21.65 (width 45.3), walls to Z 29.4 (side
walls 2.45 thick). Front plate Y 41.4..43.8 with two keyhole windows, round dia 18.5 at X = -14.0 and 12.0, Z = 17.0 (pitch 26.0; beam dia 18.0 clear by 0.25), each with an 18.5 wide channel from Z = 17.0 up to the plate top (Z 29.4). Plate coverage of the front face 900 - 2 x (pi x 9.25^2 + 18.5 x 10 - pi x 9.25^2 / 2) = 900 - 2 x 319.4 = 261 mm2 (>= 200). Ligaments: sides 2.85, bottom 7.75, between the windows 7.5. Rear wall Y 37.5..39.9 with a notch X -8.0..6.0 from the floor to the top (open top so
the header drops in): coverage 900 - 14 x 20 = 620 (>= 400). Header body X -6.08..4.08, Y 37.5..40.0,
Z 7.73..10.27, inside the notch with 1.9 each side. V-WIRES X -7.08..5.08, Y 25.5..37.5, Z
6.73..11.27 is empty (plate top Z 5.5). Drop-in: gaps 0.1 behind, 0.2 in front, 0.15 each side,
the cans (dia 16) go down the 18.5 wide channels. The rebuilt model gives 0 mm3 for the sweep; with closed round windows it gives 345 mm3.

**Chassis bolts.** M3 holes dia 3.4 at (X, Y) = (-11.0, 22.0) and (11.0, 22.0), pitch 22.0 (20..60);
counterbore dia 5.9 x 3.2 deep (Z 2.3..5.5); 2.3 of material under each head (>= 2.0). M3 x 10: head
bearing at Z = 2.3, tip at -7.7, **7.7 below** the chassis face (5..15). Key columns (Y 19.25..24.75)
clear the tunnel (Y <= 8.5) and the slot (Y >= 37.5). Ligaments >= 10 to the plate edges.

**Printing.** Chassis face down, 100% bed contact (plate is a full rectangle). The tunnel roof bridges
12.2 (<= 15); the notch is open at the top; magnet pocket and shaft hole are horizontal round holes;
the windows' round bottoms face up and their channels are vertical, so there is no overhang. Mass 28.7 g with parts (bracket 21.5 cm3 = 9.7 g); centre of mass (-4.3, 17.4, 11.6), more than 20 inside the plate outline; a 5 degree tilt moves it about 1.0.

---

## 7. Grading notes (design-specific rubric)

`benchmarks/generalize/rubric.md` did not exist when this file was written, so the grading
procedure is given here. It follows `benchmarks/enclosure/rubric.md` (recipes in its section 3) and
should become a pointer to the generic rubric when that exists.

1. **Package gate (G0).** Files in L2.12.1 exist and load, else DOES NOT MEET with one defect on
   L3.12.1.1.
2. **Load and units.** trimesh, then manifold3d `Manifold`; `status()` must be NoError; shells by
   `decompose()`. A largest axis outside 20 to 200 mm is a units defect; record, do not rescale.
3. **Normalise the frame** (1.1) with 90 degree rotations and mirroring only; record the transform.
4. **Build the references independently** from the catalogue at the declared layout, run R1 to R6
   and the seating rule, then every applicable L3 in requirement order. Record the measured value,
   the limit, the signed margin (negative = fail) and PASS, FAIL or UNVERIFIED. UNVERIFIED counts as
   FAIL.
5. **Recipes.** Pocket sections, hole and window diameters: slice perpendicular to the axis at
   mid-depth and take the largest inscribed circle. Slides and sweeps: `Manifold.translate` of the
   reference part and `(a ^ b).volume()`. Coverage areas: project the plate (or wall) material onto the
   board's face plane and intersect with the board outline. Overhang (with the A9 exemption of round
   holes up to dia 20 in vertical walls), bed contact, thin features, wall thickness, tool columns,
   stability: `benchmarks/enclosure/rubric.md` sections 3.2 to 3.7.
6. **Verdict.** WRONG: any gate fails. MINOR: no gate fails but a weight-3 L3 fails. CORRECT: no
   gate fails and every weight-3 L3 passes. **MEETS** = CORRECT and every applicable non-physical L3
   of weight 1 and 2 passes. Report also the weighted score and the worst normalised margin among
   weight-3 rows.
7. **Precedence.** Numbers in this document beat any number in a part.json. Designed contact (1.3) is
   never interference. The forward distance (L3.1.3.1) and the plug/beam clearances outrank every
   statement about how the slot or windows are built. An unlisted alternative is graded on the
   default numbers and noted as an observation for the owner (A1 and A3 especially).
8. **Where a defect is.** One entry per failed or UNVERIFIED L3 with `req`, `status`, `body`
   (bracket, layout), `feature` (by function and SCAD name), `face` (surface and outward normal),
   `location` (mm, bracket frame, point or box), `measured` / `limit` / `margin`, `reference` (model
   or envelope and datum), `render`, `evidence`, and `needed` (a verifiable number, never a design
   instruction). Group L3s that fail for one geometric reason.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | Words in the request it comes from |
|---|---|---|---|---|
| L1.1 | Placement, forward distance | L2.1.1-L2.1.4 | L3.1.1.1, L3.1.2.1, L3.1.3.1, L3.1.4.1-2 | "40 mm forward of the motor's shaft axis", "N20 gearmotor", "HC-SR04" |
| L1.2 | Motor clamp pocket | L2.2.1-L2.2.5 | L3.2.1.1-2, L3.2.2.1-2, L3.2.3.1, L3.2.4.1, L3.2.5.1 | "12 x 10 mm body ... in a clamp pocket" |
| L1.3 | Shaft and installation | L2.3.1-L2.3.3 | L3.3.1.1-2, L3.3.2.1-2, L3.3.3.1-2 | "3 mm D shaft" |
| L1.4 | Encoder magnet | L2.4.1-L2.4.3 | L3.4.1.1-3, L3.4.2.1-2, L3.4.3.1-5 | "A 6 x 3 mm magnet pocket sits at the shaft end for an encoder" |
| L1.5 | Sensor held | L2.5.1-L2.5.4 | L3.5.1.1-3, L3.5.2.1-2, L3.5.3.1, L3.5.4.1 | "ultrasonic sensor (45 x 20 mm board ...) facing forward" |
| L1.6 | Transducer windows | L2.6.1-L2.6.3 | L3.6.1.1-3, L3.6.2.1, L3.6.3.1 | "two 16 mm transducers at 26 mm pitch" |
| L1.7 | Header and wires | L2.7.1-L2.7.2 | L3.7.1.1, L3.7.2.1 | implied (the sensor is wired) |
| L1.8 | Chassis bolts | L2.8.1-L2.8.5 | L3.8.1.1-2, L3.8.2.1-3, L3.8.3.1-2, L3.8.4.1, L3.8.5.1 | "Two M3 bolts fix the whole bracket to the chassis" |
| L1.9 | Strength | L2.9.1-L2.9.2 | L3.9.1.1-2, L3.9.2.1-3 | implied |
| L1.10 | Printable | L2.10.1-L2.10.5 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1, L3.10.5.1 | "printed ... without supports, flat on its chassis face" |
| L1.11 | Compact, stable | L2.11.1-L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | implied (robot base) |
| L1.12 | Evidence | L2.12.1-L2.12.2 | L3.12.1.1-2, L3.12.2.1 | needed by the judge (not in the request) |

---

## Audit

Adversarial audit. The Feasibility design was rebuilt in manifold3d and every volume check run on it (1 shell, manifold; motor, sensor, magnet
and bolts 0 mm3 against the bracket; motor install sweep 0; sensor drop-in sweep 0; beams, wires, terminals, shaft and key columns clear; the five
motor slides intersect 54 to 86 mm3; header with 0.2 growth clear). `n20_gearmotor`, `hc_sr04`, `magnet_disc_6x3` and `bolt_m3_iso4762` load and pass
`parts.validate` and `parts.gate`. L1 12 (also in `design.json`), L2 41, L3 67 recounted.

1. **Infeasible: drop-in from above vs closed round windows.** The Feasibility said the cans pass "through the windows", but a straight-up
   sweep of the sensor (L2.5.3, V-HC-INSTALL) hits the plate above each closed window: 345 mm3 of intersection in the rebuilt model, so L3.5.3.1 (weight 3) and
   the Feasibility contradicted each other. Windows are now keyholes (round dia 18.0 to 19.0, open channel up to the plate top). Changed A7, L2.6.1, L3.6.1.2, L2.6.3, L3.6.3.1, L3.5.2.1
   (coverage limit 250 to 200, the keyhole channel takes 25 mm2: Feasibility gives 261), the Feasibility sensor and printing paragraphs, and L1.5 / L1.6 (also in `design.json`).
2. **Hidden numbers.** The agent receives only the request and the L1 texts. The judge used numbers that were in neither: shaft height 8 to 30 (L3.1.4.2), magnet pocket 0.1 to 0.3 / 0.15 to 0.35 oversize
   (L3.4.1.2, L3.4.1.3, weight 3), slot 0.1 to 0.6 deeper and 0.2 to 0.6 wider than the board and the plate coverage (L3.5.1.x, L3.5.2.1), bolt pitch 20 to 60 and tip 5 to 15 (L3.8.1.2, L3.8.3.1),
   and the plate section 150 mm2 (L3.9.2.2). They are now in L1.1, L1.4, L1.5, L1.8 and L1.9.
3. **No margin behind the magnet.** Material behind the pocket floor was 1.0, exactly the limit; the encoder wall is 4.75 thick (X 11.75..16.5), 1.5 behind the magnet, contact 81 mm2.
4. **Mass.** Feasibility said 33 g; the rebuilt bracket is 9.7 g, 28.7 g with parts; centre of mass recomputed. Stability still passes.
5. Checked, no change: forward distance 40.0 (A1 states which face); pocket 12.2 x 10.2 against 12 x 10 (0.1 per side); shaft hole 4.0 against V-SHAFT 3.5; bridge 12.2 <= 15; plate section 276 (222 at the
   bolt plane) against 150; bolt tip 7.7 below; ligaments 2.3 to 10; every request number matches L1, the L2/L3 numbers and the catalogue (12 x 10 x 9 + 15, 3 x 10 shaft, 45 x 20 x 1.2, 16 at 26, 6 x 3 magnet with `pocket_clearance` 0.15).
