# G48 NEMA17 belt carriage with limit switch: requirements (L1 / L2 / L3)

Generalisation design G48 (**held out**). It is the error signal for the control loop on a
combination family: one printed plate that joins a stepper, a pulley with a belt, a micro switch and
a T-slot extrusion with T-nuts and bolts. It is never used to tune the agent; nothing in agent logic
may depend on it (`benchmarks/heldout.json` is a different file and is not touched). The
machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file. It is graded
the way `benchmarks/enclosure/requirements.md` grades E1-01: Python measures the delivered STL against
reference models built from the catalogue (`benchmarks/generalize/parts/*/part.json`).

**Request (owner's words):** "A drive end plate for a 2020 axis: NEMA 17 on the 31 mm pattern with a
20-tooth GT2 pulley, 6 mm belt, and a microswitch (KW12) limit trigger. The plate bolts to the
extrusion with two M5 bolts into T-nuts. The switch actuator must clear the belt by 3 mm and trip at
1.0 mm over-travel." The expanded request in `design.json` adds only what section 3 derives.

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check on the geometry. Every row has a verification
method (`dev.json` definitions), a pass/fail criterion with a number and tolerance, a weight
(3 = critical, 2 = major, 1 = minor) and a gate mark (G0 to G5) where failing it makes the design
WRONG. Do not relax a criterion because the agent fails it; change a number only when the owner
corrects an assumption (section 3).

**Grading procedure.** `benchmarks/generalize/rubric.md` holds the generic judge procedure. If that
file is missing, use section 9 of this document, which is self-sufficient.

---

## 1. Frames, tolerances and the checks

### 1.1 Frames

- **Drive frame W (all tables below):** the extrusion's axis is **X**. The extrusion's end face is
  the plane X = 0 and the extrusion occupies X from -100 to 0. Its section is Y, Z in [-10, 10]. Its
  T-slot faces **+Z** (the slot opening is at Z = 10). The plate lies on the +Z face, overhangs the end
  (X > 0), and prints with its underside on the bed, so **Z is up in the print too**. A design
  delivered rotated about Z by multiples of 90 degrees or mirrored is normalised into this frame before
  grading by the declared extrusion pose (`layout.json`); that is never penalised.
- **Catalogue mapping.** The extrusion part (axis Z, slots toward +-X, +-Y, start end face at Z = 0)
  is placed with its Z along -X and its +X slot toward +Z. The motor, pulley and bolt parts (axis Z)
  keep their Z along W's Z. The T-nut and bolt parts use their frames (origin on the bearing face).
  The switch part is rotated so its +Z is W's -X, its +Y is W's +Z and its +X is W's -Y.

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm | a value passes if it meets the limit to within e |
| angle | 0.5 deg | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole diameter | largest inscribed circle of the hole's section | what a bolt or pilot sees |
| counterbore | largest inscribed circle; depth by ray casting from the plate top | |
| area | 0.5 mm2 | |

### 1.3 The checks

- **`clear_of(bodies, volume, clearance)`**: minimum distance between the printed body and `volume`
  is >= `clearance` (negative = penetration; volume reported). Pass: d >= clearance - e.
- **`dist(a, b)`**: minimum distance between two volumes (reference models or envelopes).
- **`plane_gap(face, point, axis)`**: the distance from a point to a printed planar face, measured along
  `axis` (ray casting), together with the face's angle to the axis's normal and its area.
- **`neck(x0, x1)`**: the smallest area of the plate's section on a plane X = const for X in [x0, x1]
  (the printed material only, counterbores and holes subtracted).

**Designed contact is not interference (owner rule, 2026-10-24).** For G48 the designed contacts are:
- the plate's underside lying on the extrusion's top face (X from -38.5 to 0);
- the motor's face against the plate's underside, its pilot in the pilot hole (at the fit in L3.3.1.1);
- each bolt's head bearing face on its counterbore floor, its shank in its T-nut's thread bore and through its hole;
- the motor shaft in the pulley's bore;
- each T-nut's bearing face against the underside of the extrusion's lips, behind the lips;
- the switch's body resting on the plate's top face, its screws in its holes;
- the stop face against the carriage dog (the dog is not part of this design; the contact is the stop
  plane in L3.7.3.1).

For these pairs only penetration counts (intersection above 0.01 mm3); a distance of zero is a pass.
Nothing else is designed contact: the belt, the pulley and the actuator zone touch nothing.

`BODY` means the printed plate.

---

## 2. Reference models, envelopes and datums

### 2.1 Reference models (M-)

All poses come from `layout.json` (default numbers are catalogue values).

| Name | What | Source | Size and datums used |
|---|---|---|---|
| **M-EXT** | 2020 extrusion, 100 long | `extrusion_2020` (length 100, request) | solid 20 x 20 envelope; keep-outs `slot_*`: opening 6.2 wide, depth 6.1 from the face, lip thickness 1.8 (the lip's underside is at Z 8.2), slot interior 11.0 wide; datums `SLOT_PX` (the +Z slot), `FACE_PX` (the top face, Z = 10), `END_START` |
| **M-TNUT-i** (i = 1, 2) | M5 drop-in T-nut | `tnut_2020_m5` | plate 10.0 (across the slot, Y) x 9.7 (along X) x 3.5; bearing face against the lip underside (Z 8.2), body Z 4.7 to 8.2; axis down |
| **M-BOLT-i** | M5 ISO 7380 button-head bolt, length 8.0 | `bolt_m5_iso7380` (length 8, request) | shank Ø5.0; head Ø9.5 x 2.75 on the bearing face; `HEAD_BEARING` at Z = z_b; tip at z_b - 8.0 |
| **M-MOTOR** | NEMA 17 stepper, 40 long | `nema17_motor` (body 40, request) | body 42.3 x 42.3 x 40 behind the face; face on the plate underside (Z 10); pilot Ø22.0 x 2.0; shaft Ø5.0 x 24.0 (tip at face + 24.0); `HOLE` datums on a 31.0 square; rear cable keep-out 10.0 behind the body |
| **M-PULLEY** | GT2 20-tooth pulley | `gt2_pulley_20t` | hub Ø16 x 8, flange Ø18 x 1, toothed band Ø16 x 7, flange Ø18 x 1; total 17.0; bore 5.0; `SHAFT_ENTRY` plane, `BELT_PLANE` (band middle, 12.5 above the entry plane) |
| **M-BELT** | GT2 belt, 6 wide | `gt2_belt_6mm` | width 6.0, thickness 1.38; two straight runs of 100 along -X tangent to the pulley's toothed band, plus the half wrap on the +X side (A4) |
| **M-SW** | KW12 micro limit switch | `microswitch_kw12` | body 20.0 x 6.4 x 10.2; holes Ø2.0 on a 9.5 pitch at mid-height; `ACTUATOR` point 17.0 along the body, mid-thickness, 1.5 above the top face; `PRESS_AXIS` (-Z of the part); lever travel 1.0; lever keep-out `lever_zone` |

**Solids used for every interference, clearance and distance check.** `part.json` models bores and
channels only as datums, so the grader builds the reference solids as follows. **M-EXT** is the solid
20 x 20 x 100 box minus the +Z slot channel (opening Y +-3.1 from the lip underside Z 8.2 to the top face
Z 10; interior Y +-5.5 from the slot floor Z 3.9 to Z 8.2); the other three slots are left solid, which is
conservative. **M-TNUT-i** is its 10.0 x 9.7 x 3.5 box minus the Ø5.0 thread bore along its axis.
**M-PULLEY** is its four cylinders minus the Ø5.0 bore through its full length. All other models are
their primitives as listed. Without these three, the bolt in the nut, the shaft in the pulley and the nut in
the slot would all read as interference on every design.

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-ACT** | actuator zone | M-SW's `lever_zone`: box 6.0 (along the body) x 6.4 (thickness) x 2.5 (lever rise 1.5 + travel 1.0), on the body's top (the +Z face of the part), centred on the actuator along the body |
| **V-PULLEY-ROT** | pulley rotation envelope | cylinder Ø18.0 (flange), 17.0 tall, on the shaft axis from `SHAFT_ENTRY` (the catalogue `rotation_envelope`) |
| **V-HEAD-k** (k = 1..4) | motor screw heads | cylinder Ø5.5 (head keep-out), 4.0 tall, on each motor hole axis, from the plate's top face up |
| **V-MOTOR-REAR** | motor rear cable zone | M-MOTOR's `rear_cable`: 42.3 x 42.3 x 10.0 box behind the body |
| **V-M2HEAD-j** (j = 1, 2) | switch screw heads below the plate | cylinder Ø4.4, 2.0 tall, on each switch hole axis, from the plate's underside down |
| **V-DOG-PATH** | carriage dog approach | box spanning the lateral (Y) extent from the edge of the stop face farthest from the actuator zone to the edge of the actuator zone farthest from the stop face (a dog that must reach both), Z from 0.5 above the plate top to 2.5 above the `ACTUATOR` point, swept along -X to +X from 60 mm out to the stop plane |
| **V-STOP-PLANE** | where the dog stops | the plane perpendicular to `PRESS_AXIS` at `ACTUATOR` + 1.0 along `PRESS_AXIS` (the lever travel) |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Check | Pass |
|---|---|---|
| R1 | units: bounding boxes in mm | M-MOTOR body 42.3 x 42.3 x 40 +-0.3; M-SW 20.0 x 6.4 x 10.2 +-0.2; M-PULLEY 17.0 tall +-0.5 |
| R2 | M-MOTOR holes and pilot | 31.0 square +-0.05; pilot Ø22.0 +-0.1 |
| R3 | M-BELT width and thickness | 6.0 +-0.05; 1.38 +-0.05 |
| R4 | reference parts do not collide with each other, designed contact excluded | intersection <= 0.01 mm3 |
| R5 | every V- envelope's datums equal the model datums it came from | <= 0.01 |

**Seating rule.** The grader places every reference part at the pose in `layout.json`, then verifies:
the plate's underside lies on `FACE_PX` (distance <= 0.10); the motor face on the plate underside
(<= 0.10); the pilot hole coaxial with `PILOT_AXIS` (<= 0.25); the plate bolt holes coaxial with the
bolts (<= 0.20); the switch body on the plate top (<= 0.10) and its holes coaxial with the plate's
(<= 0.30). A declaration that is missing or fails is replaced by this fit.

---

## 3. Assumptions, uncertainty and fixed decisions

| # | Question | Value chosen | Uncertainty and why |
|---|---|---|---|
| A1 | Extrusion | 2020 T-slot profile: opening 6.2, slot depth 6.1, lip 1.8, interior 11.0, modelled 100 long | opening +-0.2, lip +-0.3, interior +-0.5 between vendors (Misumi HFS5-2020 drawing and catalogue) |
| A2 | T-nut | drop-in 10.0 x 9.7 x 3.5, M5; the long side turned across the slot, behind the lips | thickness +-0.3 between vendors |
| A3 | Bolt | ISO 7380 M5, length 8.0 (nominal under the head); head Ø9.5 x 2.75; hole Ø5.5; counterbore Ø9.9 x 2.95 | counterbore +-0.2 (FDM slack); length is a request value |
| A4 | Belt geometry | the belt wraps the pulley's toothed band, inner surface at the band's outer radius 8.0 (the catalogue band Ø16.0) and runs tangent on both sides along -X, thickness 1.38 outward (outer 9.38) | the real pitch circle is Ø12.73 (the catalogue band is a conservative envelope); using 8.0 keeps the belt envelope outside any real belt. +-0.5 |
| A5 | Belt tension | 40 N in each run, both runs pulling the pulley toward -X (total 80 N) | typical GT2 6 mm tension 20 to 50 N; +-20 N. Sets the load-path numbers |
| A6 | Bolts | two, on the slot's centre line, at least 20.0 apart; nut edge to the extrusion's end >= 3.0 | spreading the bolts by two nut lengths limits the bolt load; 20 is the owner-confirmable choice |
| A7 | Motor and pulley mounting | the motor is bolted from above through the plate's M3 holes into its face, under the overhang; screws M3, heads Ø5.5; the pulley sits on the shaft with its hub at least 1.0 above the plate | the shaft is 24.0 long and the plate is 4.0 to 6.0 thick, which leaves a 1.0 to 3.0 window for the pulley's 17.0 height. Set screw and shaft flat are not modelled; +-1 on pulley hub length |
| A8 | "Trip at 1.0 mm over-travel" | the KW12's lever travel is 1.0 (datasheet); the hard stop stands 1.0 beyond the actuator's free position along the press axis, so a dog that stops against it has depressed the lever by its whole travel (1.0), which is the over-travel limit | the owner's wording could mean the switch trips earlier and the extra is over-travel; the stop position is graded either way, from the catalogue's `ACTUATOR` and lever travel. Actuator inset 3.0 +-2.0, rise 1.5 +-1.0, hole height 5.1 +-1.0 are assumed in the catalogue: measure the owner's switch |
| A9 | Carriage dog | not part of this design; it approaches along +X from the belt side, in the lateral band between the stop face and the actuator zone, in the height band 0.5 above the plate top to 2.5 above the actuator point | the dog must reach both the stop face and the lever. Not a catalogue part |
| A10 | Switch screws | M2, from below through plate holes Ø2.2 to 2.6 into the switch's threaded 2.0 holes; heads below the plate in free air | catalogue notes: the 2.0 holes are thread pilots, so the screw enters from the plate side |
| A11 | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed; print flat, underside down; round holes up to Ø12 and bridges up to 15 print without support | common printers |
| A12 | Size limit | 100 x 70 x 15 | about 82.5 x 55 x 11 is the tight design (section 6); stops oversized plates |
| A13 | Plate thickness | 4.0 to 6.0, with (thickness - counterbore depth) in [2.0, 2.7] so the 8.0 bolt's tip passes through the T-nut (Z 4.0 to 4.7) and stops short of the slot floor (Z 3.9) | derived from the extrusion, T-nut and bolt numbers; see L2.2.3 |
| A14 | Allowable stress | 10 MPa on the printed plate (PLA about 40 MPa, factor 4) | the loads are small; the neck limit has a factor of more than 3 |
| A15 | Plate in the slot | no tongue is required; the T-nuts and the bolts' fit in the slot opening locate the plate | a tongue on the underside would hold the plate off the bed in the print orientation; optional and not graded |

### Fixed decisions

| # | Decision |
|---|---|
| FD1 | Drive frame W as in 1.1: extrusion axis X, end face at X = 0, slot up, plate on top, overhang at X > 0. |
| FD2 | The motor is under the overhang with its shaft pointing up; the pulley and belt are above the plate. The shaft axis lies in the extrusion's centre plane (Y = 0). |
| FD3 | The belt runs along -X from the pulley, over the extrusion, parallel to its axis. |
| FD4 | The switch sits on the plate's top face with its lever toward -X; its `PRESS_AXIS` points along +X (the carriage's motion); the hard stop is a printed face with its normal toward -X. |
| FD5 | One printed body; no insert, tongue or separate bracket. |
| FD6 | Motor screws are M3 and enter from above; the motor holes in the plate are clearance holes (Ø3.2 to 3.6). |

---

## 4. Requirements tree

### L1.1 The parts are laid out and the layout is declared

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: pose of M-EXT, M-TNUT-1, 2, M-BOLT-1, 2, M-MOTOR, M-PULLEY (shaft-entry height), M-BELT (plane, run direction), M-SW, plus the print orientation. | inspection | `layout.json` present, parses, catalogue ids exist | 3 | |
| L3.1.1.1 | Layout file parses and ids exist. | inspection | true | 3 | |
| L2.1.2 | Orientations: shaft vertical; belt parallel to the extrusion; switch press axis along +X. | inspection | shaft axis within 1.0 deg of Z; belt runs within 0.5 deg of X; `PRESS_AXIS` within 2.0 deg of +X | 2 | |
| L3.1.2.1 | Datum directions from the declared layout. | inspection | as L2.1.2 | 2 | |
| L2.1.3 | The reference parts do not collide with each other (designed contact excluded). | analysis | pairwise intersection <= 0.01 mm3 over M-EXT, T-nuts, bolts, motor, pulley, belt, switch | 3 | |
| L3.1.3.1 | Pairwise interference of the reference parts. | analysis | each pair <= 0.01 mm3 | 3 | |
| L2.1.4 | The shaft is on the extrusion's centre plane and the motor is clear of the extrusion. | analysis | shaft axis Y within 0.5 of 0; clear_of(M-EXT, M-MOTOR body, 1.0) | 3 | |
| L3.1.4.1 | Shaft axis offset from the extrusion's centre plane. | inspection | <= 0.5 | 2 | |
| L3.1.4.2 | Motor body to extrusion. | analysis | d >= 1.00 | 3 | G3 |

### L1.2 The plate bolts into the slot with two M5 bolts

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The two bolts are on the slot's centre line, at least 20.0 apart, with the T-nuts clear of the extrusion's end. | inspection | each bolt axis Y within 0.5 of the slot centre line (0); pitch >= 20.0; each T-nut's end within the extrusion by >= 3.0 | 3 | G2 |
| L3.2.1.1 | Bolt axis offset from the slot centre line. | inspection | <= 0.50 | 3 | G2 |
| L3.2.1.2 | Bolt pitch. | inspection | >= 20.0 | 2 | |
| L3.2.1.3 | T-nut end distance to the extrusion's end face. | inspection | >= 3.0 | 2 | |
| L2.2.2 | The plate holes: Ø5.4 to 5.8 coaxial with the bolts; counterbores Ø9.7 to 10.3, 2.75 to 3.3 deep. | inspection | as stated; coaxial <= 0.2 | 3 | |
| L3.2.2.1 | Bolt hole diameter and coaxiality (two holes). | inspection | Ø5.4 to 5.8; offset <= 0.20 | 3 | |
| L3.2.2.2 | Counterbore diameter and depth. | inspection | Ø9.7 to 10.3; depth 2.75 to 3.30 | 2 | |
| L2.2.3 | The bolt's tip passes through the T-nut and stops short of the slot floor. | analysis | the plate thickness t in [4.0, 6.0]; the bolt tip Z = (10 + t - counterbore depth) - 8.0 lies in [4.0, 4.7], i.e. (t - counterbore depth) in [2.0, 2.7] | 3 | G2 |
| L3.2.3.1 | Bolt tip window (two bolts). | analysis | tip Z in [4.00, 4.70] | 3 | G2 |
| L3.2.3.2 | Plate thickness. | inspection | 4.0 to 6.0 | 2 | |
| L2.2.4 | The bolts and T-nuts sit in the slot without touching the extrusion's walls or the plate's other faces. | analysis | clear_of(M-EXT, M-BOLT, 0.0), bearing and slot-floor excluded; clear_of(BODY, M-TNUT, 0.0); head top (z_b + 2.75) <= plate top | 2 | |
| L3.2.4.1 | Bolt and T-nut clearances. | analysis | d >= 0.0; head top at or below the plate top | 2 | |
| L2.2.5 | The plate's underside is flat on the extrusion's top face. | inspection | underside plane within 0.10 of `FACE_PX` over X from -38.5 to 0; flatness <= 0.15 | 3 | |
| L3.2.5.1 | Underside seating and flatness. | inspection | <= 0.10; <= 0.15 | 3 | |

### L1.3 The motor is bolted under the plate

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | A pilot hole for the 22 mm pilot, through the plate (the shaft passes it). | inspection | Ø22.2 to 22.8, through the whole plate; coaxial with `PILOT_AXIS` <= 0.2 | 3 | G3 |
| L3.3.1.1 | Pilot hole diameter and coaxiality. | inspection | as stated | 3 | G3 |
| L2.3.2 | Four M3 clearance holes on the 31.0 square pattern. | inspection | Ø3.2 to 3.6; each coaxial with its `HOLE` datum <= 0.3 | 3 | |
| L3.3.2.1 | Motor hole diameter (four). | inspection | 3.20 to 3.60 | 2 | |
| L3.3.2.2 | Motor hole pattern offset (four). | inspection | <= 0.30 | 3 | |
| L2.3.3 | The motor's face is against the plate's underside. | inspection | `FACE` plane within 0.10 of the plate's underside plane | 2 | |
| L3.3.3.1 | Face seating. | inspection | <= 0.10 | 2 | |
| L2.3.4 | The screw heads and the motor's rear zone are free. | analysis | clear_of(BODY, V-HEAD-k, 0.0) for k = 1..4; clear_of(BODY union M-EXT, V-MOTOR-REAR, 0.0) | 2 | |
| L3.3.4.1 | Screw-head zones free. | analysis | d >= 0.0 | 2 | |
| L3.3.4.2 | Motor rear zone free. | analysis | d >= 0.0 | 2 | |

### L1.4 The pulley sits on the shaft

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The pulley is wholly on the 24 mm shaft and clear of the plate's top. | analysis | `SHAFT_ENTRY` Z - plate top >= 1.0; pulley top <= shaft tip; engagement of the bore on the shaft >= 12.0 | 3 | |
| L3.4.1.1 | Hub-to-plate gap. | analysis | >= 1.00 | 3 | |
| L3.4.1.2 | Pulley top to shaft tip. | analysis | tip - top >= 0.0 | 3 | |
| L3.4.1.3 | Bore engagement. | analysis | >= 12.0 | 2 | |
| L2.4.2 | The rotation envelope is free of printed material. | analysis | clear_of(BODY, V-PULLEY-ROT, 0.5) | 3 | |
| L3.4.2.1 | Pulley rotation envelope. | analysis | d >= 0.50 | 3 | |

### L1.5 The belt runs clear of everything

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The belt is in the pulley's belt plane and parallel to the extrusion. | inspection | belt-plane Z within 0.5 of `BELT_PLANE`; run direction within 0.5 deg of X | 2 | |
| L3.5.1.1 | Belt plane and direction. | inspection | as stated | 2 | |
| L2.5.2 | The belt is clear of every printed surface. | analysis | clear_of(BODY, M-BELT, 2.0) | 3 | G5 |
| L3.5.2.1 | Belt to the plate (both runs and the wrap). | analysis | d >= 2.00 | 3 | G5 |
| L2.5.3 | The belt is clear of the extrusion, the bolts and the switch. | analysis | dist(M-BELT, M-EXT) >= 3.0; dist(M-BELT, M-BOLT-i) >= 3.0; dist(M-BELT, M-SW) >= 3.0 | 2 | |
| L3.5.3.1 | Belt to the other parts. | analysis | each >= 3.00 | 2 | |

### L1.6 The switch is fixed on the plate

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | The plate has two holes in line with the switch's two holes. | inspection | Ø2.2 to 2.6; each coaxial with a `HOLE` datum <= 0.3; hole pitch 9.5 +-0.2 | 3 | |
| L3.6.1.1 | Plate hole diameter and coaxiality (two). | inspection | as stated | 3 | |
| L3.6.1.2 | Plate hole pitch. | inspection | 9.3 to 9.7 | 2 | |
| L2.6.2 | The switch body rests on the plate and touches nothing else printed. | analysis | body's bottom face within 0.10 of the plate's top face (or a pad); clear_of(BODY minus the seat, M-SW body, 0.2) | 2 | |
| L3.6.2.1 | Body seating. | inspection | <= 0.10 | 2 | |
| L3.6.2.2 | Body clearance to every other printed surface. | analysis | d >= 0.20 | 2 | |
| L3.6.2.3 | Screw-head zones below the plate free of printed material and the extrusion. | analysis | clear_of(BODY union M-EXT, V-M2HEAD-j, 0.0) | 1 | |

### L1.7 The actuator is free, clears the belt and stops at 1.0 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The actuator zone is free of printed material. | analysis | clear_of(BODY, V-ACT, 0.0) | 3 | G4 |
| L3.7.1.1 | Actuator zone free. | analysis | d >= 0.0 | 3 | G4 |
| L2.7.2 | The actuator zone is at least 3.0 from the belt. | analysis | dist(V-ACT, M-BELT) >= 3.0 | 3 | G5 |
| L3.7.2.1 | Actuator-to-belt distance. | analysis | >= 3.00 | 3 | G5 |
| L2.7.3 | A hard stop 1.0 beyond the actuator's free position. | analysis | a printed planar face, normal within 2.0 deg of -`PRESS_AXIS`, lies on V-STOP-PLANE within 0.15 (the face plane is 1.0 +-0.15 from the `ACTUATOR` point along `PRESS_AXIS`); its area >= 8 mm2; it lies within the lateral band of the dog path and its height range covers the actuator point +-2.5 | 3 | G4 |
| L3.7.3.1 | Stop-face distance from the actuator along the press axis. | analysis | 0.85 to 1.15 | 3 | G4 |
| L3.7.3.2 | Stop-face area. | analysis | >= 8.0 mm2 | 2 | |
| L3.7.3.3 | Stop-face lateral and height coverage. | analysis | as stated | 1 | |
| L2.7.4 | The dog's approach path is clear. | test | clear_of(BODY minus the stop face contact, V-DOG-PATH, 0.5) | 2 | |
| L3.7.4.1 | Dog path clear. | test | d >= 0.50 | 2 | |

### L1.8 The belt pull reaches the bolts through the plate

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | One connected plate carries the pull; its neck cross-section between the pilot and the bolts is at least 60 mm2. | analysis | `neck(X from the nearer bolt to the pilot hole's edge)` >= 60; stress 80 N / area <= 10 MPa | 3 | |
| L3.8.1.1 | Neck cross-section. | analysis | >= 60.0 mm2 | 3 | |
| L2.8.2 | The bolt load from the belt's moment is small. | analysis | 2 x 40 N x (belt plane Z - plate underside Z) / bolt pitch <= 150 N | 2 | |
| L3.8.2.1 | Computed bolt tension. | analysis | <= 150 | 2 | |
| L2.8.3 | At least 3.0 of material between every hole or counterbore and the plate's edge. | analysis | min ligament >= 3.0 | 2 | |
| L3.8.3.1 | Edge ligament (all holes). | analysis | >= 3.0 | 2 | |

### L1.9 It prints flat in one piece without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | In its stated print orientation (underside down), no unsupported overhang steeper than 45 degrees from vertical, except round holes up to Ø12.0 in vertical walls and bridges up to 15.0. | analysis | 0 offending faces (area > 1 mm2) | 2 | |
| L3.9.1.1 | Overhang and bridge scan. | analysis | as L2.9.1 | 2 | |
| L2.9.2 | The mesh is manifold and one shell. | analysis | 1 shell; manifold3d accepts it | 3 | G1 |
| L3.9.2.1 | Shell count and manifold status. | analysis | shells = 1; manifold true | 3 | G1 |
| L2.9.3 | It rests on a flat face. | analysis | bed contact >= 50 % of the plan bounding box | 1 | |
| L3.9.3.1 | Bed-contact area. | analysis | >= 50 % | 1 | |
| L2.9.4 | No feature thinner than 0.8; the stop block at least 1.6 thick. | analysis | min wall >= 0.8; stop block >= 1.6 | 1 | |
| L3.9.4.1 | Thin-feature scan. | analysis | as L2.9.4 | 1 | |
| L2.9.5 | It fits a 200 x 200 x 200 bed. | inspection | bounding box <= 200 per axis | 1 | |
| L3.9.5.1 | Bounding box. | inspection | <= 200 per axis | 1 | |

### L1.10 It is compact

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Outside size <= 100 x 70 x 15, longest side along X. | inspection | X <= 100.0, Y <= 70.0, Z <= 15.0; X > Y | 1 | |
| L3.10.1.1 | Bounding box. | inspection | as L2.10.1 | 1 | |

### L1.11 The package says what was built, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | The package holds the STL (mm), the `.scad` source, `layout.json` and the agent's own report. | inspection | all present and readable | 3 | G0 |
| L3.11.1.1 | Files present and parse; the body's largest bounding-box axis is within 20 to 200. | inspection | true | 3 | G0 |
| L3.11.1.2 | The declared layout verifies under the seating rule. | analysis | underside on the extrusion <= 0.10; motor face <= 0.10; pilot <= 0.25; bolt holes <= 0.20; switch seat <= 0.10, holes <= 0.30 | 3 | |
| L2.11.2 | The agent's own report agrees with the judge's measurements. | analysis | same pass / fail and abs(d_agent - d_judge) <= 0.10 for every `clear_of`, `dist`, `plane_gap`, `neck` L3 reported | 1 | |
| L3.11.2.1 | Self-report versus judge. | analysis | 100 % agreement within 0.10 | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 11 |
| L2 | 35 |
| L3 | 50 |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.11.1.1); **G1**
manifold, one shell (L3.9.2.1); **G2** the bolts engage the slot (L3.2.1.1, L3.2.3.1); **G3** the motor
mounts (L3.3.1.1, L3.1.4.2); **G4** the actuator and the hard stop (L3.7.1.1, L3.7.3.1); **G5** the
belt is clear (L3.5.2.1, L3.7.2.1).

---

## 6. Feasibility

A plate exists that meets every number above. It was rebuilt in `manifold3d` by the audit together with
the reference solids (section 2.1) and the checks below were run on it (distances read from the model). Drive frame W, mm:

- **Plate:** a slab X -38.5 to 44.0, Y -21 to 34, Z 10 to 15 (5.0 thick; underside on the extrusion's top
  face at Z 10 for X <= 0 and on the motor face for X >= 1.35). Size with the stop block: **82.5 x 55 x 11**.
- **Bolts:** at X = -10.0 and -30.0, Y = 0. Plate holes Ø5.5, counterbores Ø9.9 x 2.95 (Z 12.05 to 15).
  Bearing face Z 12.05, tip Z 4.05 (window [4.0, 4.7], so t - depth = 2.05 in [2.0, 2.7]), head top 14.8
  (below the plate top). T-nuts X -14.85 to -5.15 and -34.85 to -25.15, Z 4.7 to 8.2 (end distance 5.15,
  gap between nuts 10.3). Measured: bolt to extrusion 0.15 (tip to slot floor), no penetration. Pitch 20.0.
- **Motor:** shaft axis (22.5, 0); face Z 10; body X 1.35 to 43.65, Y +-21.15, Z -30 to 10: gap to the
  extrusion end 1.35. Pilot hole Ø22.4 (0.2 radial gap), through the plate so the shaft passes. Motor holes Ø3.4 at (7.0, +-15.5) and
  (38.0, +-15.5); head zones above the plate are free.
- **Pulley:** `SHAFT_ENTRY` Z 16.5 (1.5 above the plate top), top Z 33.5 (shaft tip Z 34.0), engagement
  17.0 >= 12.0. Nearest printed surface to the rotation envelope 2.7 (the pilot hole's rim; >= 0.5).
- **Belt:** `BELT_PLANE` Z 16.5 + 12.5 = 29.0; the belt occupies Z 26.0 to 32.0, Y 8.0 to 9.38 and
  -9.38 to -8.0, X from -100 to 22.5, plus the wrap. Measured: 5.0 to the plate (the top of the stop block), 16.0 to the extrusion
  and 11.7 to the bolt heads.
- **Switch:** mounted with its part +Z along -X, +Y up, +X along -Y: body X -34.2 to -24.0, Y 12.0 to
  32.0, Z 15.0 to 21.4. Holes at (-29.1, 26.75) and (-29.1, 17.25) (pitch 9.5), plate holes Ø2.4.
  `ACTUATOR` at (-35.7, 15.0, 18.2); `PRESS_AXIS` along +X. V-ACT: X -36.7 to -34.2, Y 12 to 18,
  Z 15 to 21.4: free (touches only the plate's top plane); 5.3 from the belt (>= 3.0).
- **Hard stop:** a block X -34.7 to -31.0, Y 6.0 to 9.0, Z 15 to 21, its face at X = -34.7 = the actuator's
  free X + 1.0, area 3.0 x 6.0 = 18 mm2; the block is 3.0 from the switch body in Y and clears the
  bolt counterbore. V-DOG-PATH (Y 6 to 18, Z 15.5 to 20.7) clears the plate by 0.5.
- **Load path:** the section at X = -10 (through a counterbore) is 234 mm2; at X = 7 (through a motor hole)
  about 241 mm2 (>= 60). Bolt tension 2 x 40 x (29.0 - 10.0) / 20 = 76 N (<= 150). Edge distances: counterbore
  to the plate's -X edge 3.55, motor hole to the +X edge 4.3 and to the -Y edge 3.8.
- **Print:** underside on the bed; counterbores open upward; the stop block rises from the top.

---

## 7. Where this stresses the agent (beyond_library)

1. A shared frame for six catalogue parts, with a bolt tip window derived from plate thickness,
   counterbore depth and the T-nut's position.
2. Slot engagement: a bolt through a 6.2 opening into a T-nut behind the lips.
3. Belt geometry from the pulley's band and the belt's thickness, kept clear of the plate.
4. Keep-out volumes: motor rear, screw heads, pulley rotation, actuator zone, dog path.
5. A hard stop positioned from the switch's `ACTUATOR` datum and lever travel (1.0).
6. A load path: connectivity, neck cross-section, bolt tension from a moment.

---

## 8. Traceability

| L1 | Owner need | L2 | L3 | Words in the request it comes from |
|---|---|---|---|---|
| L1.1 | Layout | L2.1.1-L2.1.4 | L3.1.1.1, L3.1.2.1, L3.1.3.1, L3.1.4.1-2 | "drive end plate for a 2020 axis" |
| L1.2 | Bolted to the extrusion | L2.2.1-L2.2.5 | L3.2.1.1-3, L3.2.2.1-2, L3.2.3.1-2, L3.2.4.1, L3.2.5.1 | "bolts to the extrusion with two M5 bolts into T-nuts" |
| L1.3 | Motor mount | L2.3.1-L2.3.4 | L3.3.1.1, L3.3.2.1-2, L3.3.3.1, L3.3.4.1-2 | "NEMA 17 on the 31 mm pattern" |
| L1.4 | Pulley | L2.4.1-L2.4.2 | L3.4.1.1-3, L3.4.2.1 | "20-tooth GT2 pulley" |
| L1.5 | Belt | L2.5.1-L2.5.3 | L3.5.1.1, L3.5.2.1, L3.5.3.1 | "6 mm belt" |
| L1.6 | Switch fixed | L2.6.1-L2.6.2 | L3.6.1.1-2, L3.6.2.1-3 | "microswitch (KW12) limit trigger" |
| L1.7 | Actuator, stop | L2.7.1-L2.7.4 | L3.7.1.1, L3.7.2.1, L3.7.3.1-3, L3.7.4.1 | "actuator must clear the belt by 3 mm and trip at 1.0 mm over-travel" |
| L1.8 | Load path | L2.8.1-L2.8.3 | L3.8.1.1, L3.8.2.1, L3.8.3.1 | implied (a drive plate carries the belt) |
| L1.9 | Printable | L2.9.1-L2.9.5 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1, L3.9.5.1 | implied (OpenSCAD to FDM) |
| L1.10 | Compact | L2.10.1 | L3.10.1.1 | implied |
| L1.11 | Evidence | L2.11.1-L2.11.2 | L3.11.1.1-2, L3.11.2.1 | needed by the judge |

---

## 9. Grading rules (self-contained fallback for `generalize/rubric.md`)

Use `/Users/robinonsay/python/llm-bt/venv/bin/python` with `manifold3d` and `trimesh`; count shells with
`Manifold.decompose()`.

1. **Package (G0), units.** Load the STL; its largest axis must be 20 to 200 mm.
2. **Normalise** into drive frame W by the declared extrusion pose (rotations by multiples of 90
   degrees about Z, mirroring); transform `layout.json` with the body.
3. **Build references** from the catalogue and `layout.json`; run R1-R5; verify the seating rule.
4. **Measure every L3** in order: measured value, limit, signed margin (negative = fail), PASS / FAIL /
   UNVERIFIED. UNVERIFIED counts as FAIL.
5. **Recipes.** `clear_of`: volume of the intersection; above 0.01 report it, else d = `Manifold.min_gap` (parts touching by
   design are measured with their contact face excluded or the part raised 0.5). `dist`: `min_gap`
   between two reference volumes. Belt: two boxes (width 6, thickness 1.38) tangent to the pulley's band
   plus the half annulus. `plane_gap`: ray cast from the `ACTUATOR` point along `PRESS_AXIS`, the first
   printed face hit that is square to the axis; report distance, angle, area. `neck`: slice the plate with
   planes X = const, 0.5 apart, and take the smallest section area. Holes: largest inscribed circle of a
   mid-depth slice; counterbore depth by ray casting from the top. Overhang: faces with n_z < -cos 45
   degrees not on the bed, minus holes up to Ø12 and bridges up to 15.
6. **Class.** WRONG: any gate fails. MINOR: no gate fails but a weight-3 L3 fails. CORRECT: no gate
   fails and all weight-3 L3s pass. **MEETS** = CORRECT and every applicable non-physical weight-1 and
   weight-2 L3 passes. Also report the weighted score and the worst normalised margin among weight-3 L3s.
7. **Precedence.** The numbers in this document beat `part.json`; if they disagree (for example the belt
   radius, A4, or the bolt tip window), build the references from this document and record a defect against the
   requirement that the stale catalogue number breaks (where = the `part.json` field). Designed contact
   (1.3) is never interference. The bolt, motor and stop L3s outrank the size L3s.
8. **Where.** One entry per failed or UNVERIFIED L3: `req`, `status`, `body`, `feature`, `face` (with outward
   normal), `location` (W-frame bounding box in mm), `measured` / `limit` / `margin`, `reference` (model or
   envelope and datum), `needed` (a numeric target the next agent can verify, never a design instruction),
   `evidence` (saved defect STL). Separate observations (render-only) from defects.

---

## Audit

Adversarial audit (2026-10-24). Checked: every catalogue part named here exists and passes `parts.gate`
(`extrusion_2020`, `tnut_2020_m5`, `bolt_m5_iso7380`, `nema17_motor`, `gt2_pulley_20t`, `gt2_belt_6mm`,
`microswitch_kw12`; note `plan.json` omits `gt2_belt_6mm` from this design's part list although M-BELT uses it);
L1 count 11 (in 8 to 14); counts in section 5 (11 / 35 / 50) match the tables; every L2 has an L3.
`benchmarks/generalize/rubric.md` does not exist, so section 9 is the procedure. The switch mapping
(part +Z to W -X, +Y to +Z, +X to -Y) was re-derived: body, holes, `ACTUATOR` and `lever_zone` come out as
stated. The Feasibility plate was rebuilt in `manifold3d` from section 6 with the reference solids and
measured: one shell, motor to extrusion 1.35, belt to plate 5.0, bolt tip to slot floor 0.15, stop at X -34.7
touching the dog path end with the dog path 0.5 clear of the plate, neck 234.5 mm2 (at X = -10) and 241.0 (at the
motor holes), bolt tension 76 N, no down-facing faces above the bed, bed contact 89 percent. Fixes, all in place:

1. **Interference checks failed on every design.** `part.json` models the T-nut thread bore, the pulley bore and
   the extrusion's slot only as datums, so by the document's own definitions M-BOLT intersected M-TNUT
   (68.7 mm3 each), M-MOTOR's shaft intersected M-PULLEY (333.6 mm3), and the T-nuts and bolts lay inside the
   solid M-EXT. L3.1.3.1 (weight 3), L3.2.4.1 and the seating checks could not pass. Added the reference-solids
   paragraph to section 2.1 (T-nut and pulley with their bores subtracted; M-EXT with the +Z slot channel cut) and the
   shaft-in-bore to the designed contacts. With them the rebuilt plate has zero penetration everywhere.
2. **Pilot hole depth.** The shaft passes the plate, so the pilot hole must go through; the plate with a 2 mm
   deep pilot hole intersects the shaft by 58.9 mm3. L2.3.1 and the Feasibility now say "through".
3. **V-DOG-PATH was ambiguous** ("the stop face's nearest edge"): defined symmetrically as the edge of the stop face
   farthest from the zone to the edge of the zone farthest from the stop face (Y 6 to 18 here).
4. **Hidden numbers.** The judge used a dog path box (0.5 above the plate to 2.5 above the actuator point, 60 mm
   run-in), a stop-face area of 8 mm2 and the 3.0 T-nut end distance without telling the agent: added to L1.7, L1.2
   and the request in `design.json`.
5. **Wrong feasibility readings corrected:** belt to extrusion is 16.0 and to the bolt heads 11.7 (was "8.0"),
   nearest surface to the pulley rotation envelope is 2.7 at the pilot hole's rim (was "3.5"); all still pass.

Catalogue conflicts recorded, not edited (this document outranks them, section 9 rule 7): `tnut_2020_m5`
`min_engagement` 5.0 and its `screw_tip` keep-out reach 5.0 below the nut, more than the 0.8 between the nut
back (Z 4.7) and the slot floor (3.9); thread engagement is limited to the 3.5 nut thickness.
