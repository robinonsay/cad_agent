# G24 Camera clamp for 2020 extrusion: requirements (L1 / L2 / L3)

A training design of the generalisation benchmark (`benchmarks/generalize/plan.json`, family
mechanical_mount). Modelled on E1-01 (`benchmarks/enclosure/requirements.md`): the same L1/L2/L3
structure, reference models built from catalogue parts, designed-contact rule, gates and traceability.
The machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file. Generic
grading rules would live in `benchmarks/generalize/rubric.md`; when this file was written that file did
not exist yet, so **section 8 is a design-specific rubric supplement** (it follows
`benchmarks/enclosure/rubric.md`; if `generalize/rubric.md` exists later it governs the generic parts
and section 8 only adds the G24 specifics).

**Owner's request (brief, verbatim):** "A clamp that grips a 2020 extrusion with an M5 bolt into a T-nut
and presents a 1/4-20 tripod stud on top for a small camera. The stud boss must carry a 3 N m torque
without cracking. The clamp slides along the slot until tightened."

**How to read this.** L1 says what the owner needs. L2 is an engineering requirement with numbers. L3 is a
concrete check Python can run on the delivered STL (geometry checks, sweeps and hand calculations from the
measured geometry). Every L3 has a method, a pass band with a tolerance, a weight (3 = critical, 2 = major,
1 = minor) and, where it is a must-pass, a gate mark (G0 to G6, section 5). Numbers that come from an
assumption (section 3) are provisional until the owner confirms them. Do not relax a criterion because the
agent fails it.

---

## 1. Frames, tolerances, checks and designed contact

### 1.1 Frames

- **Assembly frame = the catalogue frame of `extrusion_2020`:** origin at the centre of the section on the
  start end face, **Z along the extrusion (the slide axis)**, X and Y across; the clamp sits on face
  `FACE_PX` (plane X = +10.0) over slot `SLOT_PX` (opening centred on Y = 0, Z axis), so **+X is "up"**: the
  stud points +X. The reference extrusion is 100.0 long (Z 0 to 100). The clamp's position along Z is
  declared (default centre Z = 50.0). A design delivered in another frame is normalised into this one by
  multiples of 90 degrees and mirroring only (never penalised); for the grader the clamp STL is in the
  assembly pose (extrusion frame).
- In the tables, **s** = Z minus the clamp's centre Z (the position along the slot, relative to the block).
- Lengths in mm, angles in degrees, torque in N m (1 N m = 1000 N mm), stress in MPa (N/mm2).

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within e |
| angle | 0.5 degrees | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole diameter | largest inscribed circle of the hole's section; hex pocket: across flats | |
| boss ligament | minimum distance from the pocket or hole polygon to the outer surface | |
| computed stress, moment | 2 percent | same rule |

Where a criterion is written "nominal +/- t", t is the design tolerance and e is added to it.

### 1.3 The checks

- **`clear_of(bodies, volume, c)`**: minimum distance between the printed body and the volume is >= c.
  Reported: signed minimum distance d (negative = penetration; penetration volume too). Pass: d >= c - e.
- **`slide(assembly, axis, travel)`**: the clamp with its bolt and T-nut is translated along the axis in 1.0
  mm steps; at each step the intersection volume with the named solids is recorded (pass: <= 0.01 mm3 at
  every step) and the minimum gap (pass: as the requirement states). Contact on the seat (zero
  penetration) is allowed.
- Count, dimension, thickness and gap checks as in E1-01 rubric section 3.5.

The grader builds every reference model and envelope itself from the catalogue and the declared layout;
the agent's copies are not trusted.

### 1.4 Designed contact is not interference

Parts meant to touch are excluded from every interference and clearance check; only penetration counts
(volume above 0.01 mm3), a distance of zero passes:

- the clamp's contact face resting on the extrusion face (outside the slot opening)
- the T-nut's bearing face against the inside of the slot lips (X = 8.2), and the T-nut sliding in the slot
- the M5 bolt in its clearance hole, its head on the counterbore floor, its thread in the T-nut
- the stud shank in its hole (radial gap), the stud's hex head against the pocket ceiling and in the pocket
- the tongue in the slot opening (the 0.2 clearance per side is required, L2.2.1, but touching is not penetration)

---

## 2. Reference models, envelopes and sanity checks

### 2.1 Reference models (M-)

Built by Python from `benchmarks/generalize/parts/<id>/part.json`. Positions are the **default layout**
(A4), used when a design declares none; otherwise each model sits where `layout.json` declares it.

| Name | What | Source | Size and default position (assembly frame, mm) | Datums |
|---|---|---|---|---|
| **M-EXT** | 2020 extrusion, 100 long | catalogue `extrusion_2020` (length 100) | section 20 x 20, X and Y -10 to +10, Z 0 to 100, with the slot voids cut: for SLOT_PX the **opening** 6.2 (Y, centred) from X 10.0 down to 8.2 (lip thickness 1.8), then the **interior** 11.0 (Y) wide from X 8.2 down to 3.9 (slot depth 6.1); the other three slots likewise on their faces; centre bore Ø4.2 | `FACE_PX`, `SLOT_PX`, `SLOT_FLOOR_PX` (X 3.9), `AXIS` |
| **M-TNUT** | M5 drop-in T-nut | catalogue `tnut_2020_m5` | plate 10.0 (Y, across the slot) x 9.7 (Z) x 3.5 (X); bearing face at X 8.2, back at X 4.7; axis on the bolt axis (default Z 41.0, Y 0) | `AXIS`, `BEARING` (X 8.2), `BACK` (X 4.7) |
| **M-BOLT** | M5 button-head bolt, length l declared (default 12) | catalogue `bolt_m5_iso7380` | shank Ø5.0, head Ø9.5 x 2.75; head bearing at X 17.0, shank down to X 17.0 - l (5.0 for l = 12), head top at X 19.75; axis (X, Y 0, Z 41.0) | `AXIS`, `HEAD_BEARING`, `HEAD_TOP`, `TIP`, `tool_access` keep-out |
| **M-STUD** | 1/4-20 stud with hex head, shank length ls declared (default 15.0) | catalogue `camera_screw_1_4_20` (shank Ø6.35; hex head from the catalogue nut: 11.1 across flats x 5.6, 12.8 across corners) | shank Ø6.35 from the head bearing (the pocket ceiling, X 15.9) to X 15.9 + ls (30.9); head hex prism X 10.3 to 15.9; axis on Y 0, Z 59.0 | `AXIS`, `BEARING`, `TIP` |
| **RGA** | reference grip assembly = M-EXT, M-TNUT, M-BOLT, M-STUD at the declared (or default) layout | assembled | as above | all of the above |

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition (assembly frame, mm) | Used by |
|---|---|---|---|
| **V-SLOT-PX** | the slot's void | opening 6.2 x 1.8 plus interior 11.0 x 4.3, over the full extrusion length | L2.2.1, L2.8.1 |
| **V-DRIVER** | hex-key access to the bolt | M-BOLT `tool_access` keep-out: Ø9.5 column from the head top (X 19.75) up 25.0 | L2.9.1 |
| **V-CAM** | the camera's base | Ø28.0 cylinder on the stud axis from X = the clamp's top face up 30.0, minus the stud shank | L2.9.2 |
| **V-SWEEP** | the slide path | the clamp, M-BOLT and M-TNUT translated along Z by +/-28.0 about the declared position | L2.8.1 |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-EXT | units, section, slot numbers | 20.0 +/- 0.1; opening 6.2 +/- 0.1; lip 1.8 +/- 0.3; depth 6.1 +/- 0.2 |
| R2 | M-TNUT | plate size | 10.0 x 9.7 x 3.5, each +/- 0.2; fits V-SLOT-PX interior (10.0 < 11.0) |
| R3 | M-BOLT | head Ø x height; shank | 9.5 x 2.75 +/- 0.2; 5.0 +/- 0.1 |
| R4 | M-STUD | shank and hex | 6.35 +/- 0.1; 11.1 AF x 5.6 +/- 0.2 |
| R5 | RGA | models do not collide (designed contact excluded, 1.4) | intersection <= 0.01 mm3 |
| R6 | every V- envelope | its datums equal the model datums it was built from | <= 0.01 |

**Seating rule.** The RGA sits at the pose declared in `layout.json` (the clamp's centre Z, the bolt and stud
lengths). The grader verifies it: the clamp's contact face lies on `FACE_PX` (distance <= 0.10); the tongue's
centreline is on the slot axis (Y within 0.10); the bolt is coaxial with the M5 hole (<= 0.10) with its head on
the counterbore floor (<= 0.10); the T-nut is coaxial with the bolt (<= 0.10) with its bearing face at X 8.2
(+/- 0.10); the stud head sits in the pocket without penetration and the stud is coaxial with its hole
(<= 0.10). If the declaration is missing or fails verification, the RGA is rebuilt by fitting the bolt and the
stud to the nearest holes and the T-nut under the bolt, and L3.12.1.2 fails; if there is no M5 hole, every L1.3
check fails.

---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (A-rows, with uncertainty)

| # | Question | Value chosen | Why, and how uncertain |
|---|---|---|---|
| **A1** | What does "grips ... with an M5 bolt into a T-nut" mean? | A bolted block with a tongue in the slot, on one face of the extrusion, held by one M5 bolt into a drop-in T-nut. Not a wrap-around strap. | The brief names one bolt and one T-nut; the slot engagement is what makes it slide until tightened. Uncertainty: low. |
| **A2** | How is the stud made? | A 1/4-20 UNC stud (major Ø6.35) with a hex head held captive in a hex pocket that opens on the contact face, thread pointing up through a Ø6.6 hole; head from the catalogue nut size (11.1 across flats x 5.6, so across corners 12.8). Thread standing proud of the top face: 5.5 to 8.0 (tripod sockets are 5 to 7 deep). | The brief says "a 1/4-20 tripod stud on top". A captive hex head is the standard way to stop a printed stud turning. Uncertainty: +/-0.3 on nut AF between vendors. |
| **A3** | Extrusion and T-nut numbers | Slot opening 6.2, lip 1.8, interior 11.0 wide to depth 6.1; T-nut plate 10.0 x 9.7 x 3.5 with the bearing face on the inside of the lips | Catalogue (Misumi HFS5-2020 drawing); the interior width and lip are uncertain by +/-0.3 and +/-0.5 between vendors, T-nut thickness by +/-0.3. |
| **A4** | Default layout (used only if none declared) | Clamp centre Z 50.0; bolt axis at s = -9.0, stud axis at s = +9.0 (18.0 apart); bolt length 12; stud length 15 | A symmetric simple layout; the design may choose its own and declare it. |
| **A5** | Camera | Base about Ø28 (assumed), mass up to 0.5 kg, mounted after the clamp is tightened | The brief says "a small camera"; typical action-camera or compact base. Camera weight is not graded beyond the 3 N m torque. Uncertainty +/-6 on the base size. |
| **A6** | Allowable stresses | Wall shear across the pocket 12 MPa; bearing on the pocket flats 20 MPa; tongue key bearing 15 MPa (printed PLA/PETG, load across layers, safety factor about 2 to 2.5) | PLA layer shear and compression strengths are about 25 and 50 MPa with large scatter; the limits are conservative. Uncertainty +/-30 percent. |
| **A7** | "The clamp must not twist" | Safety factor 1.5 on the 3.0 N m of the brief: the tongue key capacity (L2.7.1) >= 4.5 N m. Friction under the bolt preload is **not** credited. | The brief gives the torque only for the stud boss; the clamp must carry the same torque into the extrusion. Uncertainty: medium. |
| **A8** | Extrusion length | 100.0 for the reference; the clamp may travel 56 along it (the clamp is 44 long) | Typical offcut. |
| **A9** | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed; the clamp prints contact face up, stud axis vertical (F5) | Layers perpendicular to the stud axis put the pocket's shear in the layer plane (strongest for torque). Common printers; +/-0.1 on every fit. |
| **A10** | Size limit | The clamp <= 60 x 30 x 30 | Stops oversized designs; a tight design is 44 x 24 x 15.6 (section 6). Not in the owner's words; confirm. |
| **A11** | T-nut thread engagement | The nut is 3.5 thick, so the bolt engages at most 3.5; the requirement is >= 3.0 and a tip protrusion beyond the nut back of at most 0.6. (The catalogue `min_engagement` 5.0 cannot be met in a 3.5 mm plate; this file wins, section 8.) | Catalogue convention vs a physical nut; uncertainty: low. |
| **A12** | Which side is "top" | The side away from the extrusion face (+X), whatever the extrusion's orientation in use | The clamp may be on any face. |

### 3.2 Fixed decisions (not open to alternatives)

| # | Decision |
|---|---|
| **F1** | One block on one face (+X) of the extrusion with a tongue in that face's slot (A1). |
| **F2** | One M5 bolt and one T-nut; the bolt hole is at one end of the block, the stud at the other (the two axes in the same plane, Y = 0). |
| **F3** | The stud head is held in a hex pocket opening on the contact face; the thread comes out of the top face (A2). |
| **F4** | The stud axis is perpendicular to the contact face. |
| **F5** | Print orientation: contact face up, stud axis vertical (the top face is on the bed). |
| **F6** | The tongue may be made of segments but leaves a window of at least 8.0 along Z around the bolt axis (so that the M5 shank does not pass through tongue material) and a window of at least 12.8 (the stud head's across-corners, from the catalogue nut size) around the stud axis, so that the hex head can be put into its pocket from the seat side: a continuous tongue under the pocket mouth would make the stud impossible to install. |
| **F7** | Assembly frame as in 1.1 (the grader normalises). |

---

## 4. Requirements tree

Column "Gate" names the must-pass groups of section 5; blank = scored only.

### L1.1 The clamp sits on one extrusion face, the tongue in its slot, the stud pointing away

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: the clamp's centre Z, the bolt length, the stud length and the print orientation. | inspection | `layout.json` present, parses, names `extrusion_2020`, `tnut_2020_m5`, `bolt_m5_iso7380`, `camera_screw_1_4_20` | 3 | G0 |
| L3.1.1.1 | Layout parses; catalogue ids exist; lengths are numbers. | inspection | true | 3 | G0 |
| L2.1.2 | The clamp is on `FACE_PX` with the stud pointing away from the face and the tongue centred on the slot axis. | analysis | stud axis within 1.0 degree of +X; tongue centreline Y within 0.10 of the slot axis | 3 | |
| L3.1.2.1 | Direction of the stud axis (fitted from the stud hole). | analysis | <= 1.0 degree from +X | 3 | |
| L3.1.2.2 | Offset of the tongue's centreline from `SLOT_PX`. | analysis | <= 0.10 | 3 | |
| L2.1.3 | The bolt axis and the stud axis lie in the slot plane and are far enough apart. | analysis | both within 0.2 of Y = 0; separation >= 14.0 (pocket circumradius 6.6 + well radius 4.95 + 2.5 ligament) | 2 | |
| L3.1.3.1 | Y offsets of the two axes. | analysis | <= 0.2 | 2 | |
| L3.1.3.2 | Distance between the bolt axis and the stud axis. | analysis | >= 14.0 | 2 | |

### L1.2 The tongue runs in the slot opening with 0.2 per side

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The tongue is the slot opening (6.2) less 2 x 0.2. | analysis | tongue width 5.8 +/- 0.1; clearance per side 0.15 to 0.25 | 3 | G2 |
| L3.2.1.1 | Tongue width (every segment, mid-height) and the gap to each lip edge. | analysis | 5.7 <= w <= 5.9; gap 0.15 to 0.25 | 3 | G2 |
| L2.2.2 | The tongue is shorter than the lip thickness and clears the T-nut top. | analysis | height above the contact face 1.2 to 1.7 (lip 1.8); gap from the tongue end to `BEARING` (X 8.2) >= 0.1 | 3 | |
| L3.2.2.1 | Tongue height. | inspection | 1.2 <= h <= 1.7 | 2 | |
| L3.2.2.2 | Gap from the tongue end face to the T-nut. | analysis | clear_of(CLAMP, M-TNUT, 0.1) | 3 | |
| L2.2.3 | The tongue is long enough, with the bolt window and the stud window. | inspection | total tongue length (sum of segments) >= 20.0; window around the bolt axis >= 8.0; window around the stud axis >= 12.8 | 2 | |
| L3.2.3.1 | Sum of the segment lengths along Z. | inspection | >= 20.0 | 2 | |
| L3.2.3.2 | Tongue-free length around the bolt axis; around the stud axis (Z extent of the gap between the segments that contains each axis). | inspection | >= 8.0; >= 12.8 | 2 | |

### L1.3 One M5 bolt into the T-nut, with engagement and a recessed head

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Clearance hole for M5 (`bolt_m5_iso7380`) through the block, with a counterbore for the head. | inspection | hole Ø 5.5 +/- 0.1; counterbore Ø 9.9 +/- 0.2; counterbore depth >= 2.95 | 3 | G3 |
| L3.3.1.1 | Clearance-hole diameter (largest inscribed circle). | inspection | 5.4 <= Ø <= 5.6 | 3 | G3 |
| L3.3.1.2 | Counterbore diameter and depth; the head top (X 19.75) below the top face. | inspection | 9.7 <= Ø <= 10.1; depth >= 2.95; head top <= top face | 2 | |
| L3.3.1.3 | Bearing ring under the head (counterbore floor between Ø5.5 and the head Ø9.5). | inspection | area >= 40 mm2 | 1 | |
| L2.3.2 | The declared bolt length gives the thread engagement and stops short of the slot floor. | analysis | engagement in the nut >= 3.0 (nut top X 8.2 minus the tip X, at most 3.5); tip protrusion beyond the nut back <= 0.6; tip >= 0.5 above `SLOT_FLOOR_PX` | 3 | G3 |
| L3.3.2.1 | Thread engagement e = 8.2 - tip X (capped at 3.5). | analysis | e >= 3.0 | 3 | G3 |
| L3.3.2.2 | Tip position relative to the nut back and the slot floor. | analysis | protrusion <= 0.6; tip >= 0.5 above X 3.9 | 2 | |
| L2.3.3 | The bolt, the hole and the T-nut are coaxial and the nut lies across the slot. | analysis | bolt-hole to T-nut axis offset <= 0.10; nut long side (10.0) across the slot within 2 degrees | 3 | |
| L3.3.3.1 | Axis offsets under the seating rule. | analysis | <= 0.10 | 3 | |
| L2.3.4 | The T-nut seats on the lips and the bolt head on the counterbore floor, with the tongue between. | analysis | `BEARING` at X 8.2 +/- 0.10; head bearing on the floor <= 0.10 | 2 | |
| L3.3.4.1 | Seating distances. | analysis | <= 0.10 each | 2 | |

### L1.4 The clamp sits flat on the face and does not penetrate the extrusion

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Flat contact on the extrusion face outside the slot opening. | analysis | contact area >= 300 mm2; contact face flatness <= 0.2 | 2 | |
| L3.4.1.1 | Area of the contact face within 0.05 of `FACE_PX` and outside the opening (Y beyond +/-3.1). | analysis | >= 300 mm2 | 2 | |
| L3.4.1.2 | Planarity of the contact face. | inspection | <= 0.2 | 2 | |
| L2.4.2 | No part of the clamp enters the extrusion except the tongue in the slot void. | analysis | clear_of(CLAMP, M-EXT, 0.0): penetration <= 0.01 mm3 (face contact exempt) | 3 | G6 |
| L3.4.2.1 | Penetration of the clamp into M-EXT. | analysis | <= 0.01 mm3 | 3 | G6 |
| L2.4.3 | The clamp does not hang far over the extrusion's sides. | inspection | block width Y <= 20.0 + 2 x 5.0 | 1 | |
| L3.4.3.1 | Block width. | inspection | <= 30.0 | 1 | |

### L1.5 The 1/4-20 stud: hex head captive, perpendicular, thread proud of the top

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | A hex pocket on the contact face takes the stud head (11.1 across flats x 5.6) with a small clearance. | inspection | 6 flats; across flats 11.4 +/- 0.15; depth 5.7 to 6.2; the clearance per flat 0.05 to 0.25 | 3 | G4 |
| L3.5.1.1 | Pocket polygon: number of sides; across flats (largest inscribed circle). | inspection | 6; 11.25 <= AF <= 11.55 | 3 | G4 |
| L3.5.1.2 | Pocket depth from the contact face to the ceiling. | inspection | 5.7 <= depth <= 6.2 | 2 | |
| L3.5.1.3 | The head hex in the pocket: penetration and flat gaps (seating rule). | analysis | penetration <= 0.01 mm3; flat gap 0.05 to 0.25 | 2 | |
| L2.5.2 | A stud hole Ø6.6 from the pocket ceiling through the top face, coaxial with the pocket. | inspection | Ø 6.6 +/- 0.15; coaxial with the pocket <= 0.2; shank-to-hole radial gap >= 0.05 | 3 | G4 |
| L3.5.2.1 | Stud-hole diameter (largest inscribed circle). | inspection | 6.45 <= Ø <= 6.75 | 3 | G4 |
| L3.5.2.2 | Pocket-to-hole coaxiality. | inspection | <= 0.2 | 2 | |
| L2.5.3 | Thread proud of the top face. | analysis | declared stud tip X minus the top face X: 5.5 to 8.0 | 3 | G4 |
| L3.5.3.1 | Stud protrusion. | analysis | 5.5 <= p <= 8.0 | 3 | G4 |
| L2.5.4 | Enough material between the pocket ceiling and the top face, and the top face is perpendicular to the stud. | inspection | ceiling-to-top thickness >= 6.35 (one major diameter); top face within 1.0 degree of perpendicular to the stud | 2 | |
| L3.5.4.1 | Ceiling-to-top thickness. | inspection | >= 6.35 | 2 | |
| L3.5.4.2 | Top-face tilt vs the stud axis. | inspection | <= 1.0 degree | 2 | |

### L1.6 The stud boss carries 3 N m

Torque T = 3000 N mm (the brief). Notation: AF = measured pocket across-flats; d_p = measured pocket depth;
t_w = minimum ligament from the pocket polygon to any outer surface of the block; l_f = AF / sqrt(3) (flat
length); F = T / (AF / 2) (force on the flats, at the flat mid-radius).

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Material around the hex pocket. | analysis | t_w >= 4.0 | 3 | G5 |
| L3.6.1.1 | Minimum ligament from the pocket to the outer surface: the side faces and ends (slice at mid-depth), the top face (from the ceiling) and any other hole. The open mouth on the contact face and the stud hole that continues from the ceiling are excluded. | analysis | >= 4.0 | 3 | G5 |
| L2.6.2 | Wall shear at the pocket under 3 N m. | analysis | tau = F / (2 t_w d_p) <= 12 MPa | 3 | G5 |
| L3.6.2.1 | tau from the measured AF, t_w, d_p. | analysis | <= 12.0 MPa | 3 | G5 |
| L2.6.3 | Bearing on the pocket flats under 3 N m. | analysis | sigma_b = F / (2 l_f d_p) <= 20 MPa | 2 | |
| L3.6.3.1 | sigma_b from the measured AF and d_p. | analysis | <= 20.0 MPa | 2 | |
| L2.6.4 | The boss radius round the stud: distance from the stud axis to every outer surface. | analysis | >= 6.35 (half the catalogue `min_boss_od` 12.7) | 2 | |
| L3.6.4.1 | Minimum distance from the stud axis to an outer surface. | analysis | >= 6.35 | 2 | |
| L2.6.5 | The layers lie across the stud axis, so the pocket shears in the layer plane. | inspection | declared print axis within 5 degrees of the stud axis | 2 | |
| L3.6.5.1 | Angle between the declared build direction and the stud axis. | inspection | <= 5.0 degrees | 2 | |

### L1.7 The clamp does not twist at 3 N m

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Key capacity of the tongue: M_cap = p_a h_t l_min (S - l_min), with p_a = 15 MPa, h_t the tongue height, S the overall tongue span along Z (outer end to outer end) and l_min the shorter of the two end segments. | analysis | M_cap >= 4500 N mm (3.0 N m x 1.5) | 3 | |
| L3.7.1.1 | M_cap from the measured h_t, S and l_min. | analysis | >= 4500 N mm | 3 | |
| L3.7.1.2 | The span and the end segments. | inspection | S >= 30.0; l_min >= 4.0 | 2 | |
| L2.7.2 | The tongue segments are not thin. | inspection | each segment >= 4.0 long and width as L2.2.1 | 1 | |
| L3.7.2.1 | Segment lengths. | inspection | >= 4.0 each | 1 | |

### L1.8 With the bolt loose the clamp slides along the slot

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The clamp with its bolt and T-nut slides +/-28.0 about the declared position without touching M-EXT except on its seat and the T-nut's bearing. | test | slide(clamp + M-BOLT + M-TNUT, Z, +/-28.0): penetration with M-EXT <= 0.01 mm3 at every step; tongue-to-lip gap >= 0.15 | 3 | G2 |
| L3.8.1.1 | Slide sweep, both directions, 1.0 mm steps. | test | every step <= 0.01 mm3 | 3 | G2 |
| L3.8.1.2 | Minimum gap between the tongue and the lips during the sweep. | test | >= 0.15 | 2 | |
| L2.8.2 | The T-nut does not bind in the slot. | analysis | T-nut to the slot interior walls (Y) >= 0.3 each side; T-nut to the slot floor >= 0.5 | 2 | |
| L3.8.2.1 | Clearances of M-TNUT in V-SLOT-PX. | analysis | Y >= 0.3; floor >= 0.5 | 2 | |

### L1.9 A hex key reaches the bolt; a camera base sits on top

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | A hex key reaches the M5 head from above. | analysis | clear_of(CLAMP, V-DRIVER, 0.0) | 3 | |
| L3.9.1.1 | Tool-access column clear. | analysis | d >= 0.0 | 3 | |
| L2.9.2 | A camera base of about Ø28 sits on the top face with nothing printed above it. | analysis | clear_of(CLAMP, V-CAM, 0.0) | 2 | |
| L3.9.2.1 | Camera-base volume clear (stud excluded). | analysis | d >= 0.0 | 2 | |
| L2.9.3 | The top face is flat where the camera sits. | inspection | top-face planarity <= 0.2; top face covers the stud axis with >= 6.0 radius | 2 | |
| L3.9.3.1 | Planarity and radius of the flat top. | inspection | <= 0.2; >= 6.0 | 2 | |

### L1.10 One manifold body that prints without supports

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | In its stated print orientation (F5), no unsupported overhang steeper than 45 degrees from vertical, except round holes Ø <= 12 in vertical walls and bridges <= 15. | analysis | 0 offending faces (area > 1 mm2) | 2 | |
| L3.10.1.1 | Overhang and bridge scan (E1 rubric 3.6); the counterbore ring and the pocket ceiling are the faces most at risk. | analysis | 0 patches | 2 | |
| L2.10.2 | The mesh is manifold and a single shell. | analysis | 1 shell; manifold3d accepts it | 3 | G1 |
| L3.10.2.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.10.3 | The part rests on a flat face. | analysis | bed contact >= 50 percent of the plan bounding box | 1 | |
| L3.10.3.1 | Bed-contact area. | analysis | >= 50 percent | 1 | |
| L2.10.4 | No feature thinner than 0.8; mating clearances >= 0.15. | analysis | min thickness >= 0.8; min mating gap >= 0.15 (tongue, pocket, hole) | 1 | |
| L3.10.4.1 | Thin-feature and mating-gap scan. | analysis | as stated | 1 | |
| L2.10.5 | The part fits a 200 x 200 x 200 build volume. | inspection | bounding box <= 200 per axis | 1 | |
| L3.10.5.1 | Bounding box. | inspection | <= 200 per axis | 1 | |

### L1.11 Compact: at most 60 x 30 x 30

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Overall size, tongue included. | inspection | Z <= 60.0, Y <= 30.0, X <= 30.0 | 1 | |
| L3.11.1.1 | Clamp bounding box. | inspection | as stated | 1 | |

### L1.12 The design package says what was built, and its own claims are true

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds: `clamp.stl` (assembly pose, mm), the `.scad` source, `layout.json` (L2.1.1) and the agent's own clearance report. | inspection | all present and readable | 3 | G0 |
| L3.12.1.1 | Files present and parse; STL in mm: the largest bounding-box axis is 20 to 200. | inspection | true | 3 | G0 |
| L3.12.1.2 | The declared layout verifies under the seating rule (section 2.3). | analysis | contact face on `FACE_PX` <= 0.10; bolt, T-nut, stud axes <= 0.10; no penetration | 3 | |
| L2.12.2 | The agent's own report agrees with the judge's measurements. | analysis | for every clear_of / slide / strength L3 the agent reports, same pass/fail and \|d_agent - d_judge\| <= 0.10 (stresses within 5 percent) | 1 | |
| L3.12.2.1 | Self-report vs judge. | analysis | 100 percent agreement | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 37 |
| L3 | 52 |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.1.1.1, L3.12.1.1); **G1**
manifold single body (L3.10.2.1); **G2** the tongue fits and slides (L3.2.1.1, L3.8.1.1); **G3** the M5 fastening
(L3.3.1.1, L3.3.2.1); **G4** the stud (L3.5.1.1, L3.5.2.1, L3.5.3.1); **G5** the boss carries 3 N m (L3.6.1.1,
L3.6.2.1); **G6** no penetration of the extrusion (L3.4.2.1).

---

## 6. Feasibility: a design that meets every number

One concrete design, hand-checked against the bands (assembly frame, mm; the loop does not get it).

**Block.** X 10.0 to 24.0 (14.0 thick), Y -12.0 to 12.0 (24.0 wide, 2.0 over each side of the profile), Z 28.0 to 72.0
(44.0 long, centre 50.0). Contact face X 10.0. Bounding box with the tongue: X 8.4 to 24.0 (15.6), Y 24.0, Z 44.0:
within 60 x 30 x 30. Contact area: the strips Y 3.1 to 10.0 on both sides, 44.0 long: 2 x 6.9 x 44 = 607 mm2 less about
42 mm2 where the hex pocket cuts them = about 565 mm2 >= 300.

**Tongue.** X 8.4 to 10.0 (height 1.6; lip thickness 1.8; tongue end 0.2 above the nut bearing face X 8.2),
Y +/-2.9 (width 5.8, 0.2 per side). Three segments, the full 44.0 block length, with the bolt window and the stud window between them: Z 28.0 to 36.75
(s -22.0 to -13.25, 8.75 long); Z 45.25 to 52.4 (s -4.75 to +2.4, 7.15 long); Z 65.6 to 72.0 (s +15.6 to +22.0, 6.4 long);
sum 22.3 >= 20. Bolt window s -13.25 to -4.75 = 8.5 >= 8.0 (the Ø5.5 hole spans s -11.75 to -6.25); stud window s +2.4 to
+15.6 = 13.2 >= 12.8 (the pocket corners are at s 9.0 +/- 6.58), so the head goes in from the seat side. Span S = 44.0.
Key capacity M_cap = 15 x 1.6 x 6.4 x (44.0 - 6.4) = 5775 N mm >= 4500 (margin 1.28); l_min 6.4 >= 4.0; S >= 30.0.
The T-nut (Z 36.15 to 45.85) sits under the bolt window and 0.2 below the tongue ends (nut top X 8.2, tongue X 8.4).

**M5.** Bolt axis at Z 41.0 (s -9.0). Hole Ø5.5 from X 10.0 to 17.0, counterbore Ø9.9 from X 17.0 to 24.0 (floor at X 17.0,
head 9.5 x 2.75 so the head top is at X 19.75, 4.25 below the top face; bearing ring area pi/4 (9.5^2 - 5.5^2) = 47.1 >= 40).
Bolt length 12: tip at X 5.0; the T-nut occupies X 4.7 to 8.2, so engagement = 8.2 - 5.0 = 3.2 >= 3.0 and the tip is 0.3 short
of the nut back (protrusion <= 0.6); tip 1.1 above the slot floor (X 3.9). T-nut 10.0 across the 11.0 interior (0.5 each side),
back 0.8 above the floor (>= 0.5).

**Stud.** Stud axis at Z 59.0 (s +9.0), 18.0 from the bolt axis (>= 14.0). Hex pocket across flats 11.4 (head 11.1, flat gap
0.15; across corners 13.2) on the contact face, depth 5.9 (X 10.0 to 15.9; head 5.6 thick), flats facing +/-Y. Stud hole Ø6.6
from X 15.9 to 24.0 (shank 6.35, radial gap 0.125). Ceiling-to-top thickness 24.0 - 15.9 = 8.1 >= 6.35. Stud shank 15.0
long: tip at X 30.9, protrusion 6.9 (5.5 to 8.0). The stud axis is perpendicular to the face (the top face is parallel
to it).

**Strength at 3 N m.** AF 11.4, d_p 5.9, ligaments: flats toward +/-Y give 12.0 - 5.7 = 6.3 to the sides; the corners toward
+/-Z give 13.0 - 6.58 = 6.42 to the end; t_w = 6.3 >= 4.0. F = 3000 / 5.7 = 526 N. tau = 526 / (2 x 6.3 x 5.9) = 7.1 MPa <= 12.
l_f = 11.4 / sqrt(3) = 6.58; sigma_b = 526 / (2 x 6.58 x 5.9) = 6.8 MPa <= 20. Distance from the stud axis to the nearest outer
surface 12.0 >= 6.35. Print axis vertical = stud axis.

**Access.** The well Ø9.9 is open to 25 above the head (V-DRIVER Ø9.5 column clear). The top face is flat and free over a
Ø28 disc (the camera base) centred on the stud axis: the nearest printed rise is none (the top face is the highest
surface). The camera base radius 14 from the stud axis reaches 18 - 14 = 4.0 from the bolt axis, so a camera on the stud
covers part of the well: the clamp is tightened first (A5); the hex key access of L2.9.1 is checked without the camera.

**Printing.** Contact face up, top face on the bed: the well opens to the bed (the Ø5.5 above it is a 2.2 annular bridge),
the stud hole is a vertical hole open to the bed, the hex pocket opens upward, the tongue segments rise from the seat (none over the pocket): no overhang steeper
than 45 degrees; bed contact about 94 percent.

---

## 7. Traceability

| L1 | Owner need (from the brief) | L2 | L3 | JSON L1 | Words in the brief it comes from |
|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1-L2.1.3 | L3.1.1.1, L3.1.2.1-2, L3.1.3.1-2 | L1.1 | "a clamp that grips a 2020 extrusion", "on top" |
| L1.2 | Slot tongue | L2.2.1-L2.2.3 | L3.2.1.1, L3.2.2.1-2, L3.2.3.1-2 | L1.2 | "slides along the slot" |
| L1.3 | M5 into T-nut | L2.3.1-L2.3.4 | L3.3.1.1-3, L3.3.2.1-2, L3.3.3.1, L3.3.4.1 | L1.3 | "with an M5 bolt into a T-nut" |
| L1.4 | Seat | L2.4.1-L2.4.3 | L3.4.1.1-2, L3.4.2.1, L3.4.3.1 | L1.4 | "grips" |
| L1.5 | Stud | L2.5.1-L2.5.4 | L3.5.1.1-3, L3.5.2.1-2, L3.5.3.1, L3.5.4.1-2 | L1.5 | "a 1/4-20 tripod stud on top for a small camera" |
| L1.6 | Boss strength | L2.6.1-L2.6.5 | L3.6.1.1, L3.6.2.1, L3.6.3.1, L3.6.4.1, L3.6.5.1 | L1.6 | "The stud boss must carry a 3 N m torque without cracking" |
| L1.7 | No twist | L2.7.1-L2.7.2 | L3.7.1.1-2, L3.7.2.1 | L1.7 | "carry a 3 N m torque" (A7) |
| L1.8 | Slides until tightened | L2.8.1-L2.8.2 | L3.8.1.1-2, L3.8.2.1 | L1.8 | "slides along the slot until tightened" |
| L1.9 | Access | L2.9.1-L2.9.3 | L3.9.1.1, L3.9.2.1, L3.9.3.1 | L1.9 | "small camera", implied |
| L1.10 | Printable | L2.10.1-L2.10.5 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1, L3.10.5.1 | L1.10 | implied (OpenSCAD -> FDM) |
| L1.11 | Compact | L2.11.1 | L3.11.1.1 | L1.11 | implied (A10) |
| L1.12 | Evidence | L2.12.1-L2.12.2 | L3.12.1.1-2, L3.12.2.1 | L1.12 | needed by the judge |

---

## 8. Grading supplement (design-specific; `generalize/rubric.md` did not exist when this was written)

Procedure, recipes and report format are those of `benchmarks/enclosure/rubric.md` (sections 2, 3 and 5),
applied to the clamp STL, with these specifics:

1. **Inputs.** `clamp.stl` (assembly pose, mm), `.scad`, `layout.json`, self-report, renders. The judge does
   not use the agent's code or transcript, earlier verdicts, or `benchmarks/heldout.json`.
2. **Normalise the frame** (1.1): extrusion axis Z, the clamp on the +X face, the stud toward +X. Record the
   transform.
3. **Build references independently** from the catalogue (M-EXT with the T-shaped slot voids, M-TNUT, M-BOLT,
   M-STUD), then the V- envelopes (2.2), sanity checks R1 to R6 and the seating rule (2.3).
4. **Recipes.** `clear_of` as E1 rubric 3.2; `slide`: translate the clamp, bolt and T-nut meshes in 1.0 mm steps
   and take `(CLAMP ^ M-EXT).volume()` and `CLAMP.min_gap(M-EXT, 1.0)` at each. Pocket across flats: slice the
   clamp at mid-depth of the pocket (X = 13) and fit the largest inscribed circle of the hexagon (AF), count its
   sides, and take `t_w` as the minimum of the distance from the polygon to the outer boundary of the slice, the
   ceiling-to-top-face thickness and the distance to any other hole (not the open mouth on the contact face, not the
   coaxial stud hole). Pocket depth, tongue height, counterbore depth: ray cast along X. Tongue segments:
   slice at X = 9.2 and list the polygons' Z extents. Strength: compute from the measured AF, d_p, t_w, h_t, S,
   l_min with the formulas of L1.6 and L1.7 (T = 3000 N mm, p_a = 15 MPa); report every intermediate value.
5. **Classes.** WRONG = any gate (G0 to G6) fails. MINOR = no gate fails but a weight-3 L3 fails. CORRECT = no
   gate fails and every weight-3 L3 passes. **MEETS** = CORRECT and every applicable non-physical L3 of weight
   1 and 2 passes. UNVERIFIED counts as FAIL. Report the weighted score and the worst normalised margin among
   weight-3 L3s.
6. **Precedence.** The numbers in this file beat `part.json` (in particular the T-nut engagement of A11 beats the
   catalogue `min_engagement` 5.0): if a catalogue value disagrees, build from this file and record a defect on
   the requirement the stale value breaks, with where = the part.json field. Designed contact (1.4) is never
   interference. Never relax a criterion, never round in the design's favour beyond e, never infer a pass from
   a render.
7. **WHERE a defect is.** One entry per failed or UNVERIFIED L3, most severe first (gates, then weight 3, 2, 1):
   `req` (L3, L2, L1), `status`, `body` (clamp or layout), `feature` (named by function and SCAD name, for
   example "stud hex pocket (`stud_pocket`)"), `face` (surface and outward normal), `location` (assembly-frame
   coordinates, a point or a box), `measured` / `limit` / `margin`, `reference` (the M- or V- involved and its
   datum), `render`, `evidence` (saved defect STL), `needed` (a numeric target, never a design instruction).
   Group L3s that fail for one geometric reason, keeping every id.
8. **Measured-values table (always filled in).**

| Quantity | Limit | Measured |
|---|---|---|
| Stud axis tilt; tongue offset; axis separation (L3.1.x), deg / mm | <= 1.0; <= 0.10; >= 14.0 | |
| Tongue width; side gap; height; total length; bolt window; stud window (L3.2.x), mm | 5.7 to 5.9; 0.15 to 0.25; 1.2 to 1.7; >= 20.0; >= 8.0; >= 12.8 | |
| Hole Ø; counterbore Ø and depth; engagement; tip (L3.3.x), mm | 5.4 to 5.6; 9.7 to 10.1, >= 2.95; >= 3.0; <= 0.6 past the nut, >= 0.5 above the floor | |
| Contact area; penetration of M-EXT (L3.4.x) | >= 300 mm2; <= 0.01 mm3 | |
| Pocket sides; AF; depth; hole Ø; protrusion; ceiling (L3.5.x), mm | 6; 11.25 to 11.55; 5.7 to 6.2; 6.45 to 6.75; 5.5 to 8.0; >= 6.35 | |
| t_w; tau; sigma_b; boss radius; build angle (L3.6.x) | >= 4.0 mm; <= 12 MPa; <= 20 MPa; >= 6.35 mm; <= 5 degrees | |
| M_cap; span; l_min (L3.7.x) | >= 4500 N mm; >= 30.0; >= 4.0 | |
| Slide sweep: max intersection; min gap (L3.8.1.x) | <= 0.01 mm3; >= 0.15 mm | |
| Driver column d; camera volume d (L3.9.x), mm | >= 0; >= 0 | |
| Shells (L3.10.2.1) | 1 | |
| Overhang patches; bed contact (L3.10.x) | 0; >= 50 percent | |
| Bounding box Z x Y x X (L3.11.1.1), mm | <= 60 x 30 x 30 | |
| Self-report agreement (L3.12.2.1) | 100 percent | |

---

## Audit

Adversarial audit (second agent). `extrusion_2020`, `tnut_2020_m5`, `bolt_m5_iso7380`, `camera_screw_1_4_20` load and pass `parts.gate` (the plan lists `tnut_2020_m5`; it exists in `benchmarks/generalize/parts`). L1 = 12, L2 = 37, L3 = 52 recounted (match section 5 and section 7; the window edit changed row text, not counts). Recomputed: slot geometry (lip 1.8, interior 11.0, T-nut X 4.7 to 8.2, 0.5 side and 0.8 floor margins), hex pocket section (AF 11.4, across corners 13.16, strip cut about 42 mm2, contact area about 565 mm2), shear 7.1 MPa, bearing 6.8 MPa, bolt engagement 3.2 and tip clearances, stud protrusion 6.9, M_cap.

| # | Defect found | Fix |
|---|---|---|
| 1 | The stud could not be installed. Its hex head enters the pocket from the seat side (the pocket opens on the contact face), but the Feasibility tongue (Z 45.25 to 70.0, Y +/-2.9, X 8.4 to 10.0) ran continuously under the whole pocket mouth (Z 52.4 to 65.6), so the head (11.1 AF) could not reach the pocket; it also left a 13.2 mm bridge in the print. No row checked this. | F6, L2.2.3, L3.2.3.2 and L1.2 now require a tongue-free window of at least 12.8 around the stud axis as well as 8.0 around the bolt axis. Section 6 tongue redone as three segments over the full 44.0 block (8.75, 7.15, 6.4 long; windows 8.5 and 13.2); M_cap = 5775 N mm (was 5386), l_min 6.4, S 44.0; default axes (A4) unchanged. |
| 2 | L3.6.1.1 and the section 8 recipe measured t_w to "the top and contact faces", but the pocket opens on the contact face (distance 0) and the stud hole continues from its ceiling, so the gate G5 row could never pass as written. | Wording now excludes the open mouth and the coaxial stud hole and measures ceiling-to-top thickness (8.1), sides (6.3) and ends (6.42). Feasibility value t_w = 6.3 unchanged. |
| 3 | Numbers a gate or weight 2-3 row needs but the agent was never told: the formulas behind the 12 / 20 MPa and 4.5 N m limits (F = T / (AF / 2), shear, bearing, M_cap with p_a = 15 MPa, S, l_min), pocket AF 11.25 to 11.55 and depth 5.7 to 6.2, stud-hole band, head size 11.1 x 5.6, tongue height 1.2 to 1.7 and 0.1 to the T-nut, tip clearances, T-nut clearances, axis separation 14.0, seat flatness, ceiling thickness, boss radius, build direction, span and segment minima, top-face flatness. | Added to the L1 texts in `design.json` (L1.1 to L1.9, L1.12). No L3 band changed. |
| 4 | Noted, not changed: A11 (engagement 3.0 in a 3.5 plate) deliberately overrides the catalogue `min_engagement` 5.0; section 8 item 6 already gives this file precedence. The camera base covers the bolt well (A5: clamp tightened first). | None needed. |

Residual uncertainty: the key-capacity formula is a convention of this benchmark, not a standard; slot lip and interior width vary by vendor (+/-0.3, +/-0.5), so 0.5 side margin of the T-nut is the least robust fit.
