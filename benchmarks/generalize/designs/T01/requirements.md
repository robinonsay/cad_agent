# T01 SPD clip-in flat pedal adapter: requirements (L0 / L1 / L2 / L3)

T01 is **Robin's own real print request**, not a synthetic design. It is the generalisation set's *target* design, in the same role as the
enclosure E1-01 (`benchmarks/enclosure/requirements.md`): run every iteration (`run_suite.py --target`), never as a train or a held-out design,
and a change that makes it worse is a regression. The agent designs it; this file holds only the need, the acceptance checks and the
catalogue references, never a solution geometry. It is graded on the cleat fastening and its fore-aft adjustment, the SPD engagement and
crank clearances, the platform size and grip, a standing-rider load case, left/right use, printability and rounded edges, plus the usual evidence rows.
The machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file; `paraphrases.json` holds two re-wordings with the same numbers.

**L0, Robin's request (verbatim):** "I have a design I need to print. I need flat pedals that I can clip to my SPD clipless mountain bike pedals (like a conversion kit). This design would allow me to bolt on the standard shimano cleats and act as pedals with grips for my shoes"

**L0 addendum (Robin, 2026-10-27, verbatim):** "Let's add a requirement to the pedal that all edges/corners must have a minimum fillet."

**Request as given to the agent (L0 plus the derived facts of section 3, all of them from this file's assumptions and fixed decisions):** I have a design I need to print. I need flat pedals that I can clip to my SPD clipless mountain bike pedals (like a conversion kit). This design would allow me to bolt on the standard shimano cleats and act as pedals with grips for my shoes. The pedals are Shimano PD-M520-type two-sided SPD pedals and the cleat is the standard Shimano SM-SH51 two-bolt SPD cleat, fastened with M5 bolts and nuts. The cleat position has to be adjustable fore-aft like on a shoe. The platform should be about the size of an ordinary flat pedal (between 80 and 105 mm each way). It is printed on an FDM printer in PETG with no supports, and one printed adapter (or a left/right pair) goes on each pedal. All edges and corners must have a minimum fillet of 1 mm radius.

**Split:** target (Robin's own design). **Family:** mechanical_mount. **Capabilities exercised:** datum_placement, bolt_pattern, slot_adjust, captive_nut, keepout_clearance, rotation_clearance, load_path, print_orientation, pattern_array, edge_fillet.

**What is and is not verified.** Several dimensions could not be confirmed from a Shimano drawing (the research tool could not read Shimano's dealer-manual PDFs). Every
such number is marked **UNVERIFIED** in its `part.json` (`unverified` list and the `source` text) and in section 3.1 below, with a "Robin to measure" note; none is presented as sourced. The list for Robin is in section 3.3.

**How to read this.** L1 says what Robin needs. L2 turns each need into an engineering requirement with numbers. L3 is a concrete check Python can run on the delivered
STL(s). Every L3 row has a method (inspection, analysis, demonstration, test, human; see `design.json`), a pass/fail criterion with a number and a tolerance, a
weight (3 = critical, 2 = major, 1 = minor) and a gate mark (G0 to G5) where a failure makes the design WRONG. Every number that comes from an assumption (section 3.1)
is provisional until Robin confirms it; a correction changes this file and the catalogue, and earlier scores become stale. No number here may appear in agent logic:
target numbers live in the request text, in `part.json` catalogue data and in this file only. Where this file and a `part.json` disagree, this file wins (section 7.3).

---

## 1. Frames, tolerances and the checks

### 1.1 Frames

- **Pedal frame (all tables below):** the catalogue `pedal_shimano_pd_m520` frame. **Y** along the pedal spindle, **+Y outboard** (away from the crank arm), **X** fore-aft
  (travel direction), **Z** from the pedal toward the shoe. The origin is on the spindle axis at the pedal centre (the cleat centre line). The shoe sole plane (`SOLE_PLANE`) is
  at Z = 17.0 (stack height). The crank arm's inner face is the plane Y = -55 (`CRANK_FACE`). The adapter lies above Z = 17.0 (its pedal-side face on the sole plane); the
  cleat protrudes from it toward -Z into the pedal's binding. A delivered STL in another frame is normalised with the transform declared in `layout.json` (print-to-pedal pose) and
  by the rotation/mirror rules of 7.2 step 3; that is never penalised.
- **Part frames:** `cleat_shimano_sm_sh51` (origin at the centre of its footprint on its `MOUNT_FACE`, body toward -Z, `BOLT` axes toward +Z) is placed so that its `SOLE_PLANE`
  coincides with the pedal's `SOLE_PLANE` (mount face at Z = 17.0 + 3.0 = 20.0 with the catalogue defaults) with its axis on the declared cleat position. `bolt_m5_iso4762` and `nut_m5`
  (axis along Z, origin on the head-bearing / seat face) are placed by the layout; the head bears on the cleat's `BOLT_SEAT`, the shank runs +Z into the adapter.
- **Adjustment poses.** The cleat is fixed in the pedal; the adapter moves. The nominal pose is the declared cleat position. The **pose set** P is every adapter shift
  (dx, dy) with dx in {-10, 0, +10} and dy in {-2.5, 0, +2.5} relative to the nominal pose (half of the 20 mm and 5 mm ranges of A6 each way, so the declared pose is the middle of the range), crossed with a twist about the vertical
  line through the cleat centre of {-15, 0, +15} degrees (the release angle of A11). 27 poses.

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered meshes, never by eye.

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within e (e.g. ">= 2.00" passes at 1.98) |
| angle | 0.5 degrees | same |
| area | 1.0 mm2 | same |
| stress | 0.1 MPa | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole / pocket width | largest inscribed circle (holes) or the flat-to-flat gap (hex pockets) of the section | |
| pin / boss OD | smallest enclosing circle of the section | |

Where a criterion is written "nominal +/- t", t is the design tolerance and e is added to it. A mesh is tessellated: a circle of nominal diameter D measures D cos(pi/N) at worst, so
compare diameters with e = 0.05 for holes and bosses.

### 1.3 The checks and designed contact

- **`clear_of(bodies, volume, clearance)`**: the minimum Euclidean distance between every printed body in `bodies` and `volume` is >= `clearance`. Reported value: the signed minimum
  distance d (negative = penetration; the penetration volume is reported too). Pass: d >= clearance - e. Over the pose set P the **worst pose** is reported.
- **`sweep(model, poses, bodies)`**: the model is placed at each pose of a set (and at steps of at most 1.0 mm between the extremes for the bolt travel); pass when the penetration volume with
  `bodies` stays <= 0.01 mm3 at every pose.
- **`inside(volume, solids, clearance)`**: as in `benchmarks/enclosure/requirements.md` 1.3.

`bodies` is **ALL** (every printed body, in the assembly pose) or one named body. A design never builds or edits the reference volumes: the grader generates them independently from the
catalogue and the design's declared layout. The agent may generate the same volumes for its own checks, but its copies are not trusted for grading.

**Designed contact for this design (is never interference).** Parts meant to touch are excluded from interference and clearance checks; for these pairs only penetration counts (intersection volume above 0.01 mm3; a distance of zero is a pass):

- the adapter's pedal-side face on the pedal's sole plane (`SOLE_PLANE`, Z = 17.0), and the cleat's mount face against the adapter's cleat seat
- a bolt shank in its hole or slot and in its nut's thread; a bolt head on the cleat's `BOLT_SEAT`; a nut on its pocket floor and its walls (the trap clearance of L2.2.3)
- the cleat body inside the recess volume V-RECESS (it is what the recess is for) and inside the binding cage V-CAGE
- a grip pin screwed (catalogue `grub_m4_iso4026`) or printed into the platform

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` in `benchmarks/generalize/parts/<id>/`: `cleat_shimano_sm_sh51`, `pedal_shimano_pd_m520`, `bolt_m5_iso4762`, `nut_m5`, and optionally `grub_m4_iso4026`. These are the only places target-specific part numbers may live.
- **envelope**: a keep-out or access volume generated by Python from datums (offsets, sweeps). Never drawn by hand.
- **computed**: derived from the delivered STLs (sections, bearing areas, feature counts).

### 2.2 Reference models (M-) and envelopes (V-)

| Name | What | Source | Definition (pedal frame, mm, catalogue defaults) |
|---|---|---|---|
| **M-PEDAL** | pedal body and spindle | catalogue `pedal_shimano_pd_m520` | body 100.0 (X) x 70.0 (Y) x 34.0 (Z -17 to +17) plain box (conservative, closed), spindle Ø14.29 from Y = -55 to the body; `SOLE_PLANE` Z = 17.0, `CRANK_FACE` Y = -55 |
| **M-CLEAT** | Shimano SM-SH51 cleat | catalogue `cleat_shimano_sm_sh51` | box 36.0 (X) x 34.0 (Y) x 7.0 (Z) with its mount face at Z = 20.0, bottom at Z = 13.0, so 4.0 below the sole plane; two bolt axes 15.0 apart in X; `BOLT`, `BOLT_SEAT` 2.0 below the mount face |
| **M-BOLT-k** (k = 1, 2) | M5 socket-head bolt | catalogue `bolt_m5_iso4762` (length declared in `layout.json`) | head Ø8.5 x 5.0 on `BOLT_SEAT`, shank Ø5.0 along +Z; `HEAD_BEARING`, `HEAD_TOP`, `TIP` |
| **M-NUT-k** | M5 hex nut | catalogue `nut_m5` | 8.0 across flats (8.79 across corners) x 4.7 thick on its pocket floor; trap clearance 0.2 per flat side (A4) |
| **V-RECESS** | the cleat recess | `cleat` keepout `recess` | plan (36.0 + 2 x 2.0) x (34.0 + 2 x 2.0) = 40.0 x 38.0, Z 17.0 to 20.0 (the recess depth 3.0), centred on the cleat; swept over every dx, dy of P |
| **V-CAGE** | pedal binding cage | `pedal` keepout `binding_cage` | plan 44.0 (X) x 40.0 (Y), Z 9.0 to 17.0 (below the sole plane, depth 8.0), centred on the pedal centre |
| **V-CRANK** | crank-side slab | `pedal` keepout `crank_side` | the slab Y <= -53.0 (the crank face -55 plus the 2.0 margin), X and Z within +/-80 |
| **V-HEXKEY-k** | 4 mm hex key access | `bolt` keepout `tool_access` | the cylinder Ø8.5 and 25.0 long on the bolt axis, from the bolt head's top toward -Z (the pedal side), for every shift dx, dy of P; evaluated with the adapter off the pedal and the cleat removed, so it also must stay free of any adapter material that hangs below the cleat seat |
| **V-TRAVEL** | bolt travel | `cleat` keepout `bolt_travel` | plan (15.0 + 20.0 + 8.5) x (5.0 + 8.5) = 43.5 x 13.5 around the cleat centre, swept by the two bolt axes and heads over the adjustment range |
| **V-LOAD-n** (n = 1..4) | standing load patch | this file (A10) | a 30.0 x 30.0 mm patch on the top face, one edge flush with the platform's outer edge, centred on the edge's middle; n = fore, aft, inboard, outboard |
| **V-SUPPORT** | the cleat clamp footprint | `cleat` footprint | 36.0 x 34.0 on the cleat seat, at the extreme dx of P that is nearest the loaded edge |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-CLEAT | bolt pattern | two axes 15.0 +/- 1.1 apart, Ø5.0 +/- 0.05 |
| R2 | M-CLEAT | seating | `SOLE_PLANE` coplanar with M-PEDAL `SOLE_PLANE` within 0.01 in the nominal pose |
| R3 | M-PEDAL | frame | spindle along +Y, crank face at Y = -55 |
| R4 | M-BOLT / M-NUT | size | head Ø8.5 x 5.0 +/- 0.1; nut 8.0 x 4.7 +/- 0.1 |
| R5 | M-CLEAT, M-PEDAL | models do not collide | the cleat's bottom (Z 13.0) lies inside the pedal body box; the intersection with V-CAGE is designed contact |

**Seating rule.** The reference assembly is placed at the pose declared in `layout.json`. The grader verifies: the cleat `MOUNT_FACE` lies on the adapter's seat face (<= 0.10), each cleat `BOLT` axis is coaxial with its bolt
(<= 0.20 at the nominal pose), and each nut lies on a pocket floor. If the declaration is missing or fails, the cleat is seated by the seat face and the pedal-side face instead and the L3 rows for the pose fail.

---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (with uncertainty and source status)

Each line gives the value chosen, where it comes from, and whether it is **sourced** or **UNVERIFIED**. "Robin to measure" means: measure it on your own cleat or pedal and tell us; the number is a placeholder until then.

| # | Question | Value chosen | Source status and uncertainty |
|---|---|---|---|
| A1 | Which pedal? | Shimano PD-M520-type two-sided SPD pedal, modelled by `pedal_shimano_pd_m520`. Stack height 17.0, pedal centre to crank arm 55.0. | **Sourced (retailer spec tables, bike-components / Reid Cycles):** stack height 17.0 mm, centre to crank 55 mm. **UNVERIFIED:** that "stack height" is axle centre to the sole plane (Robin to measure with calipers), and the crank distance on his crank (washers and spacers change it). Robin to confirm his pedal model. |
| A2 | The cleat? | Shimano SM-SH51 single-release two-bolt SPD cleat, modelled as a plain box 36.0 x 34.0 x 7.0 (`cleat_shimano_sm_sh51`). | **UNVERIFIED:** the 36 x 34 x 7 envelope is aggregated retailer text, which of the plan sizes lies along travel is not known, and the engagement hooks are not modelled. Robin to measure his cleat (length, width, height, and which way it points). |
| A3 | Bolt pattern? | Two cleat bolts 15.0 mm centre to centre, on a line along the travel direction X, M5 thread. | **Partly sourced:** M5 thread (Shimano cleat bolts are listed as M5 x 10 mm, 4 mm hex key, torque 5 to 6 N m final from Shimano's PD-M520 dealer text). The **15 mm spacing is a forum value** (Cycling UK forum, two posters; a second source says 14 mm), **not a Shimano drawing: UNVERIFIED, Robin to measure** the distance between the two bolt holes on his cleat and which way that line runs. The catalogue self-check tolerates +/-1.1. |
| A4 | Hardware? | Standard M5 socket-head bolts (`bolt_m5_iso4762`, ISO 4762) and M5 hex nuts (`nut_m5`, ISO 4032: 8.0 across flats, 4.7 thick), one pair per cleat bolt; bolt length chosen by the design from stock lengths. Nut trap clearance 0.2 per flat side. | **Sourced:** ISO 4762 / ISO 4032 / ISO 273 dimensions (clearance hole 5.5). The trap clearance, counterbore slack and the cleat's bolt-seat depth (2.0 below the mount face) are assumptions: **UNVERIFIED seat depth, Robin to measure** how deep his cleat bolt heads sit and what the head looks like (the Shimano cleat bolt head is flatter than ISO 4762, so the catalogue head is a conservative stand-in). The Shimano cleat nut plate is not used. |
| A5 | Pedal body size? | Body 100.0 x 70.0 x 34.0 plain box, binding cage 44.0 x 40.0 and 8.0 deep below the sole plane. | **UNVERIFIED** (approximate from product photos; no drawing was reachable). Conservative: the closed box is bigger than the real open body. Robin to measure the pedal body length and width and the cage footprint. |
| A6 | Cleat adjustment? | At least 20 mm fore-aft and 5 mm sideways, clamped anywhere in the range. | **Sourced (Shimano PD-M520 dealer text):** "20 mm front to back and 5 mm right to left". |
| A7 | Platform size? | Each plan dimension 80 to 105 mm; thickness above the pedal-side face 8 to 14 mm excluding grip features. | **Sourced:** Redshift Sports Mousetrap SPD-to-flat adapter 80 x 105 x 10 mm, 176 g per pair, glass-filled nylon (redshiftsports.com); Problem Solvers Deckster 85 x 95 x 10 mm (retailer listings). The 8 to 14 mm band is a tolerance round the 10 mm products (assumption, +/-4). |
| A8 | Grip? | At least 8 pins or ridges, 1.5 to 5.0 tall, over >= 60 % of the plan area, >= 3 mm from the edge. | Assumption from typical flat pedals (8 to 10 pins a side; no single source). Optional pins are catalogue M4 grub screws (ISO 4026; tap drill 3.3 per ISO 261). Uncertainty +/-3 on the count. |
| A9 | Printing? | FDM, PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed. In-plane flexural strength 25 MPa (conservative; printed PETG datasheets give higher in-plane, lower across layers). | **UNVERIFIED allowable:** 25 MPa is a conservative engineering assumption for printed PETG (uncertainty +/-10 MPa); Robin to say which filament he will print in. A downward-facing step of at most 1.0 deep is not an overhang; bridges <= 15; round holes <= 12 in vertical walls. |
| A10 | Rider load? | 2500 N on a 30 x 30 mm patch at the outer edge of the platform, supported only by the cleat clamp footprint (no credit for the pedal body), safety factor 1.5 on the 25 MPa strength: bending stress <= 16.67 MPa. | **Assumption:** a 100 kg rider standing on one pedal is 981 N; a dynamic peak factor of 2.5 (standing out of the saddle, bumps; **factor UNVERIFIED**) gives about 2450 N, rounded to 2500 N. ISO 4210-8 (bicycle pedal tests) specifies a static proof load recalled as about 1500 N (**UNVERIFIED**); it is not graded here. Ignoring the pedal body's support is deliberately conservative. Robin to give his weight and riding (jumps, drops). |
| A11 | Release twist? | The cleat releases by twisting the heel out through 15 degrees about the cleat's vertical axis. | **UNVERIFIED** (Shimano's release angle was not reachable). Robin to confirm; the crank check scales with it. |
| A12 | Crank margin? | 2.0 mm between any adapter point and the crank arm's inner face. | Assumption for crank flex, washers and print tolerance (+/-1). |
| A13 | Recess depth? | The cleat's mount face is 3.0 above the sole plane, so the cleat protrudes 4.0 below it. | **UNVERIFIED** (assumed; Robin to measure how far his cleat sticks out below the sole of his shoe). It fixes the depth of the adapter's cleat seat above the sole plane. |
| A15 | Minimum fillet? | 1.0 mm radius on every edge and corner of every printed body, convex and concave. Exempt: the hex flats and corners of a nut trap (their shape is set by the catalogue nut, section 1.3) and the edges where a bore or slot wall runs along its own axis (they are not edges). Catalogue parts (bolts, nuts, cleat, grub screws) are not printed and are not checked. | **Assumption:** Robin asked for "a minimum fillet" without a number. 1.0 mm is the smallest radius that a 0.4 mm nozzle reproduces as a curve and that removes a sharp edge to the touch; it equals the 1.0 mm downward-step allowance of A9, so a fillet on a bed-face edge is not an overhang. Robin to give a larger radius if he wants softer edges (e.g. for shins). |
| A14 | Stand-in for shoes? | A flat shoe (rubber sole) stands on the top face; the shoe is wider than the platform's grip region. | Context only; no check uses a shoe model. |

### 3.2 Fixed decisions (one choice, no alternatives graded)

| # | Ambiguity | Decision | Reason |
|---|---|---|---|
| FD1 | Which frame? | The pedal frame of 1.1. The adapter sits above the sole plane, the foot on its top face. | One frame for the cleat, the pedal and the loads. |
| FD2 | How does the cleat attach? | By its own two bolt positions to standard M5 hardware from the catalogue (bolts from the cleat side, nuts in the adapter). The adapter's way of holding the nuts and the arrangement of seat, slots and pockets are the design's. | The brief says "bolt on the standard shimano cleats". The cleat standard fixes the bolt pattern, nothing else. |
| FD3 | How is it adjusted? | Fore-aft by at least 20 mm and sideways by at least 5 mm, clamped at any position. The mechanism is the design's. | "like a shoe": the SPD standard adjustment range. |
| FD4 | One part or a pair? | Either one part whose mirror image also passes, or a declared left/right pair of mirror images; both are acceptable and graded on the same checks. | Section 6 shows that with the default numbers a symmetric part cannot meet both the size range and the crank clearance, so a pair is the expected outcome; this is derived, not prescribed. |
| FD5 | How is strength judged? | By the cantilever hand calculation of 7.2 step 5 on the delivered cross-section (no FEA). | Cheap, repeatable, conservative; the agent can run the same calculation. |
| FD6 | Which side is the foot side? | +Z (the top face). The pedal side is -Z. | The adapter is used the right way up. |

### 3.3 What Robin should measure (UNVERIFIED items)

1. His cleat: overall length, width and height; the distance between the two bolt holes (15 mm?) and which way the bolt line runs relative to the cleat's long axis; how deep the bolt heads sit and the bolt head diameter.
2. How far the cleat protrudes below the sole of one of his shoes (the recess depth, 3.0 assumed) and the cleat's thickness at the bolt holes.
3. His pedal: confirm the model (PD-M520?), measure from the spindle centre to the plane a flat sole touches (stack height, 17 assumed), the body length and width, and the footprint of the binding cage.
4. His crank: the distance from the pedal's centre line to the crank arm's inner face with his washers (55 assumed).
5. The cleat release angle (15 degrees assumed) and which filament he prints in (PETG assumed); his weight and riding style for the load case.

---

## 4. Requirements tree

### L1.1 The adapter carries the SM-SH51 cleat on standard M5 hardware

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: the cleat's pose, each bolt and nut, the grip features, each body's print orientation and the hand(s). | inspection | `layout.json` present, parses, names `cleat_shimano_sm_sh51`, two `bolt_m5_iso4762`, two `nut_m5`, and `hands` = "single" or "pair" | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 | G0 |
| L3.1.1.2 | The declared pose verifies under the seating rule. | analysis | cleat mount face on the seat <= 0.10; bolt/cleat axis residual <= 0.20; each nut on a pocket floor | 3 | G2 |
| L2.1.2 | The cleat sits at the right height for the pedal. | analysis | cleat `SOLE_PLANE` coplanar with the pedal's `SOLE_PLANE` within 0.30 in the nominal pose, i.e. the cleat protrudes 4.0 +/- 0.3 below the adapter's pedal-side face | 3 | |
| L3.1.2.1 | Cleat protrusion below the pedal-side face. | analysis | 4.0 +/- 0.3 (A13) | 3 | G3 |
| L2.1.3 | Only standard M5 hardware. | inspection | exactly 2 catalogue bolts and 2 catalogue nuts; no other fastener or insert, unless catalogue `grub_m4_iso4026` pins | 2 | |
| L3.1.3.1 | Fastener count and kind. | inspection | 2 and 2 | 2 | |

### L1.2 The cleat adjusts fore-aft and sideways and clamps anywhere

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The bolts travel the full range inside the adapter. | analysis | sweep(M-BOLT-1, M-BOLT-2 shank Ø5.0, V-TRAVEL, ALL): penetration <= 0.01 mm3 at every position of the range | 3 | |
| L3.2.1.1 | Fore-aft travel of the bolt axes. | analysis | >= 20.0 mm | 3 | G2 |
| L3.2.1.2 | Sideways travel of the bolt axes. | analysis | >= 5.0 mm | 3 | G2 |
| L2.2.2 | The cleat is clamped on a flat seat at every position. | analysis | contact between the cleat's mount face and the adapter's seat >= 70 % of the 36.0 x 34.0 footprint (>= 857 mm2) at the nominal and at both fore-aft extremes | 2 | |
| L3.2.2.1 | Seat contact area at the three positions. | analysis | >= 857 mm2 each | 2 | |
| L2.2.3 | Each nut is held captive against turning, and holds in the adapter. | inspection | hex pocket (or track) flat-to-flat width = 8.0 + 0.1 to + 0.6; the nut cannot leave its pocket when the bolt is removed in the clamped pose | 2 | |
| L3.2.3.1 | Nut pocket / track width and containment. | inspection | 8.1 to 8.6; true | 2 | |

### L1.3 The M5 hardware fits at every cleat position

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Each bolt reaches its nut and stays below the top face. | analysis | tip beyond the nut's far face 0.8 to 5.0 mm (at least one pitch of thread, at most 5); tip at least 1.0 below the platform's top face; declared length is a stock length | 3 | |
| L3.3.1.1 | Thread engagement through the nut thickness. | analysis | tip beyond the nut face: 0.8 <= t <= 5.0 | 3 | G2 |
| L3.3.1.2 | Bolt tip to the top face. | analysis | >= 1.0 | 3 | G2 |
| L2.3.2 | A 4 mm hex key reaches each head with the adapter off the pedal, and each nut can be placed in its pocket. | test | clear_of(ALL, V-HEXKEY-k, 0.0) at the nominal and extreme positions; each nut reaches its seat along one straight path with no penetration | 2 | |
| L3.3.2.1 | Hex-key column clear. | test | d >= 0.0 | 2 | |
| L3.3.2.2 | Nut insertion path. | test | penetration <= 0.01 mm3 | 2 | |
| L2.3.3 | Wall left round every slot and pocket. | analysis | >= 1.5 mm of material between any slot, pocket or hole and another or the platform's edge | 2 | |
| L3.3.3.1 | Ligament round slots, pockets and holes. | analysis | >= 1.5 | 2 | |

### L1.4 The cleat clips into the SPD pedal

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Only the cleat enters the binding cage and the recess. | analysis | clear_of(ALL, V-CAGE, 0.0) and clear_of(ALL, V-RECESS, 0.0), the cleat excluded, over the whole pose set P | 3 | |
| L3.4.1.1 | Binding cage clear. | analysis | penetration <= 0.01 mm3, d >= 0.0 | 3 | G3 |
| L3.4.1.2 | Cleat recess clear over the whole adjustment range. | analysis | penetration <= 0.01 mm3, d >= 0.0 | 3 | G3 |
| L2.4.2 | The cleat's lower (engagement) faces stay free. | analysis | no adapter material within 0.5 mm of the cleat's lower faces below the sole plane (the cleat body from Z 13.0 to 17.0 in the pedal frame) | 2 | |
| L3.4.2.1 | Clearance to the cleat's engagement faces. | analysis | d >= 0.5 | 2 | |

### L1.5 The pedal-side face sits on the sole plane

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Nothing of the adapter is below the sole plane. | analysis | clear_of(ALL, M-PEDAL, 0.0), the cleat excluded: penetration <= 0.01 mm3; lowest adapter point >= Z 17.0 - 0.3 | 3 | |
| L3.5.1.1 | Adapter against the pedal body envelope. | analysis | penetration <= 0.01 mm3 | 3 | G3 |
| L2.5.2 | A flat bearing area lies on the sole plane. | analysis | adapter material within 0.3 mm of Z = 17.0 outside V-RECESS: area >= 600 mm2 | 2 | |
| L3.5.2.1 | Bearing area on the sole plane. | analysis | >= 600 | 2 | |

### L1.6 The adapter clears the crank arm in every pose

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | No adapter point comes within 2.0 mm of the crank arm's inner face. | analysis | clear_of(ALL, V-CRANK, 0.0) over all 27 poses of P (V-CRANK already includes the 2.0 margin) | 3 | |
| L3.6.1.1 | Worst-pose clearance to the crank-side slab. | analysis | penetration <= 0.01 mm3 and d >= 0.0 | 3 | G4 |
| L3.6.1.2 | Worst-pose distance of any adapter point to the plane Y = -55. | analysis | >= 2.0 | 3 | G4 |
| L2.6.2 | The twist and travel do not hit the pedal body or the spindle. | analysis | clear_of(ALL, M-PEDAL, 0.0), cleat excluded, over P | 2 | |
| L3.6.2.1 | Clearance to the pedal over P. | analysis | penetration <= 0.01 mm3 | 2 | |

### L1.7 The platform is sized like a commercial flat pedal

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Both plan dimensions are in the range of commercial adapters. | inspection | the platform's plan bounding rectangle (X and Y extents of the foot plate, grip features excluded): each 80.0 to 105.0 | 2 | |
| L3.7.1.1 | Plan extents. | inspection | 80.0 <= each <= 105.0 | 2 | |
| L2.7.2 | The platform has the thickness of a commercial adapter. | inspection | median top-face height above the pedal-side face, grip features excluded: 8.0 to 14.0 | 2 | |
| L3.7.2.1 | Platform thickness. | inspection | 8.0 <= t <= 14.0 | 2 | |
| L2.7.3 | The top face is usable as a standing surface. | analysis | the top face is within 1.0 mm of one plane over >= 60 % of the plan area (grip features excluded) | 1 | |
| L3.7.3.1 | Top-face flatness and coverage. | analysis | flat within 1.0 over >= 60 % | 1 | |

### L1.8 The top face has grip features for shoes

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Enough raised grip features of a useful height. | inspection | count >= 8 raised pins or ridges, each 1.5 to 5.0 above the top face | 2 | |
| L3.8.1.1 | Number of grip features. | inspection | >= 8 | 2 | |
| L3.8.1.2 | Height of every grip feature. | inspection | 1.5 <= h <= 5.0 | 2 | |
| L2.8.2 | They are spread over the platform and kept off the edge. | analysis | convex hull of the feature centres >= 60 % of the plan bounding rectangle; every feature >= 3.0 from the platform edge | 1 | |
| L3.8.2.1 | Spread and edge distance. | analysis | >= 60 %; >= 3.0 | 1 | |
| L2.8.3 | Each feature is printable and not a blade. | analysis | smallest section of a pin tip >= 0.8 across (Ø or width); a screwed M4 pin has >= 6.0 thread engagement and a 3.3 pilot | 1 | |
| L3.8.3.1 | Grip tip size and (if screwed) engagement. | analysis | >= 0.8; >= 6.0; pilot 3.3 +/- 0.1 | 1 | |

### L1.9 The platform carries a standing rider

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | Bending stress under the load case stays within the allowable with a margin. | analysis | for each of V-LOAD-1..4 (2500 N on the patch, support = V-SUPPORT at the nearest extreme position): sigma = M c / I from the delivered cross-section at the support edge, M = 2500 x lever arm (support edge to the patch centre), whole cut width, voids excluded; sigma <= 25 / 1.5 = 16.67 MPa | 3 | |
| L3.9.1.1 | Worst bending stress over the four loads. | analysis | <= 16.67 MPa | 3 | G5 |
| L3.9.1.2 | Margin (allowable / stress) and worst edge reported. | analysis | >= 1.5 | 3 | G5 |
| L2.9.2 | The layers lie along the bending stress. | inspection | the declared print orientation puts the platform plate flat on the bed (pedal-side or top face down) | 2 | |
| L3.9.2.1 | Print orientation vs the load path. | inspection | plate parallel to the bed within 5 degrees | 2 | |

### L1.10 One part serves both pedals, or a mirror pair does

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | `hands` = "single": the part and its mirror image (Y -> -Y through the cleat axis) both pass the crank, engagement and bolt checks. `hands` = "pair": the second STL is the first mirrored and each passes on its own pedal. | analysis | single: L3.4.1.1, L3.4.1.2, L3.5.1.1, L3.6.1.1 and L3.6.1.2 pass on the mirrored copy too; pair: volume of the symmetric difference of the mirror of body A and body B <= 2 % of the volume of A | 3 | |
| L3.10.1.1 | Mirror test or pair test. | analysis | as L2 | 3 | G4 |

### L1.11 Printable on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Each body is one manifold shell. | analysis | 1 shell each; manifold3d accepts it | 3 | |
| L3.11.1.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.11.2 | No unsupported overhang in the declared orientation. | analysis | 0 offending faces (area > 1 mm2) steeper than 45 degrees from vertical, except round holes Ø <= 12 in vertical walls, bridges <= 15 and downward steps <= 1.0 (A9) | 2 | |
| L3.11.2.1 | Overhang and bridge scan per body. | analysis | as L2 | 2 | |
| L3.11.2.2 | Bed contact per body. | analysis | >= 50 % of the plan bounding box | 1 | |
| L2.11.3 | Feature size and build volume. | analysis | min thickness >= 0.8; bounding box <= 200 per axis | 1 | |
| L3.11.3.1 | Thin-feature scan and bounding box. | analysis | >= 0.8; <= 200 | 1 | |

### L1.12 The delivered package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds the STL of each printed body, the `.scad` source, `layout.json` and `self_report.json`. | inspection | all present and readable | 3 | |
| L3.12.1.1 | Files present and parse; STLs in mm: largest bounding-box axis within 80 to 200. | inspection | true | 3 | G0 |
| L2.12.2 | The agent's report agrees with the judge, including the strength number. | analysis | every clear_of / sweep number reported: pass/fail the same and \|d_agent - d_judge\| <= 0.10; the reported worst stress within 10 % of the judge's | 1 | |
| L3.12.2.1 | Self-report against the judge. | analysis | 100 % within 0.10 mm and 10 % stress | 1 | |

### L1.13 Every edge and corner has a minimum fillet

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | Every edge and corner of each printed body, convex and concave, is rounded with a radius of at least 1.0 mm (A15, its exemptions apply). | analysis | no sharp edge: no mesh edge outside the exemptions where the surface turns by more than 30 degrees; every band of faces that turns by more than 30 degrees in total has a radius (arc length / turn angle) >= 1.0 - 0.05 | 2 | |
| L3.13.1.1 | Sharp-edge scan per body. | analysis | 0 mesh edges with a turn > 30 degrees outside the exemptions | 2 | |
| L3.13.1.2 | Smallest fillet radius per body, and where it is. | analysis | >= 0.95 mm | 2 | |

---

## 5. Counts and gates

L1: 13. L2: 30. L3: 40.

Gates (a failing gate makes the design WRONG regardless of score):

- **G0** package present and readable, layout parses: L3.1.1.1, L3.12.1.1
- **G1** every printed body is one manifold shell: L3.11.1.1
- **G2** the cleat is fastened and adjustable with standard M5 hardware: L3.1.1.2, L3.2.1.1, L3.2.1.2, L3.3.1.1, L3.3.1.2
- **G3** the cleat engages the SPD pedal: L3.1.2.1, L3.4.1.1, L3.4.1.2, L3.5.1.1
- **G4** the adapter clears the crank arm and serves both pedals: L3.6.1.1, L3.6.1.2, L3.10.1.1
- **G5** the platform carries the standing load: L3.9.1.1, L3.9.1.2

---

## 6. Feasibility

This benchmark gives no solution geometry. The arithmetic below only shows that the requirements are mutually consistent with the catalogue defaults (pedal frame, mm); every line depends on the UNVERIFIED values of 3.1 and changes if Robin's measurements differ.

- **Height stack.** Pedal-side face on the sole plane Z = 17.0; cleat seat face at Z = 20.0 (recess 3.0); with a platform 10.0 thick the top face is Z = 27.0. An M5 nut (4.7) in a pocket whose floor is the seat plane sits at Z 20.0 to 24.7; a bolt whose head bears on the cleat's `BOLT_SEAT` (Z = 18.0) and is 8 mm long (a stock length; Shimano lists M5 x 8 and x 10 cleat bolts) ends at Z = 26.0: 1.3 past the nut (>= 0.8), 1.0 below the top face (>= 1.0). At 12 mm thickness the margins grow by 2.0. So 8 to 14 mm is workable and 10 mm is the lower end for this hardware.
- **Adjustment.** Bolt travel footprint 43.5 x 13.5 (bolt axes 15.0 apart + 20.0 fore-aft travel + head Ø8.5; 5.0 sideways + 8.5): fits inside a platform of 80 x 85 with 1.5 mm ligaments: (85 - 43.5)/2 = 20.8 and (80 - 13.5)/2 = 33.3 per side before the recess; the recess V-RECESS itself is 40.0 x 38.0 centred on the cleat and swept over the same shifts, so the swept recess is (40 + 20) x (38 + 5) = 60.0 x 43.0, which leaves (85 - 60)/2 = 12.5 mm and (80 - 43)/2 = 18.5 mm of platform beyond it per side. Consistent.
- **Crank clearance and left/right.** The crank slab starts at Y = -53.0. Worst pose: sideways shift 2.5 toward the crank, a 15-degree twist, a corner 52.5 mm from the cleat axis along X (half of an 85 mm platform plus the 10 mm fore-aft shift): y' = -(0.966 e) - 52.5 x 0.259 - 2.5 >= -53.0, so the inboard extent e <= 38.2 mm. A symmetric part would then be at most 2 x 38.2 = 76.4 mm wide, **below the 80 mm minimum of A7**; an asymmetric part with 38.2 inboard and 41.8 outboard reaches 80.0 but is not its own mirror image. So with these numbers the expected outcome is a left/right mirror pair (FD4); the design may also pick `hands` = "single" only if it finds a symmetric answer within 80 mm, which this arithmetic says is not possible for the default numbers. If Robin's crank is farther out or the release angle is smaller, a single symmetric part becomes possible.
- **Strength.** Platform 85 x 80 x 10, cut through the full width 85: I = 85 x 10^3 / 12 = 7083 mm4, c = 5. Outboard load: support edge at 17.0 + 2.5 = 19.5, patch centre at 41.8 - 15.0 = 26.8, lever 7.3 mm, M = 2500 x 7.3 = 18 250 N mm, sigma = 18 250 x 5 / 7083 = 12.9 MPa <= 16.67: margin 1.9. At 8 mm thickness I = 3627, sigma = 18 250 x 4 / 3627 = 20.1 MPa (fails), so the load case bites below about 10 mm.
- **Bearing and sizes.** 600 mm2 of bearing area on the sole plane is 8.8 percent of an 80 x 85 platform's 6800 mm2 (outside the recess). Commercial adapters: Mousetrap 80 x 105 x 10, Deckster 85 x 95 x 10, both in the 80 to 105 range.
- **Fillets.** A 1.0 mm radius fits every feature: the smallest printed widths are the 1.5 mm ligaments of L2.3.3 and the 0.8 mm thin-feature limit, and a concave 1.0 mm fillet in a hex trap corner is exempt (A15). A convex 1.0 mm fillet on the outer edge of a 10 mm plate removes (1 - pi/4) x 1.0^2 = 0.21 mm2 per corner of the section, under 0.5 % of I, so the strength line below is unchanged; rounding the plan corners also moves the worst crank-clearance corner inward.
- **Print.** Platform plate flat on the bed (pedal-side down or top down), the nut pocket is open on the seat face (pedal side down) or bridged (<= 15, nut across corners 8.79 + 0.4 = 9.2 when top-down); grip pins vertical, or M4 grub pins in 3.3 mm pilots.

The request, the L1s and the catalogue (`cleat_shimano_sm_sh51` 36 x 34 x 7, bolts 15.0; `pedal_shimano_pd_m520` stack 17.0, crank 55.0; `bolt_m5_iso4762`, `nut_m5`, `grub_m4_iso4026`) agree.

---

## 7. Grading procedure (design-specific rubric)

`benchmarks/generalize/rubric.md` (the generic rubric) does not exist yet, so the procedure and the T01-specific rubric rows are given here, as in the train designs. When that file exists it
governs the procedure and this section governs only the numbers: **requirements numbers beat `part.json` numbers, and this section beats the generic rubric where they differ.** The recipes
for loading, `clear_of`, `inside`, sections, thickness, overhangs and bed contact are those of `benchmarks/enclosure/rubric.md` section 3 (Python at
`/Users/robinonsay/python/llm-bt/venv/bin/python`, `trimesh`, `manifold3d`; count shells with `manifold3d` `decompose()`, not `trimesh.split()`).

**Rows this design adds to the generic rubric (the generic rubric has no recipe for them):**

| Row | Recipe |
|---|---|
| pose set P | build the 27 adapter poses of 1.1 with a rigid transform (shift, then twist about the vertical line through the cleat centre); evaluate `clear_of` at each, report the worst |
| cantilever stress (L3.9.1.x) | for each V-LOAD-n: cut the adapter's mesh with the plane through the support edge perpendicular to the load direction; take the 2-D cross-section (voids excluded); I about its neutral axis; M = F x lever arm; sigma = M c / I; report max over n and the margin 25 / sigma |
| bearing area (L3.5.2.1) | triangles of the adapter within 0.3 mm of Z = 17.0 and facing -Z, outside V-RECESS, summed |
| grip count and height (L3.8.x) | connected raised components above the top-face plane (z_top is the median height of the plate): count, height = max z minus z_top |
| bolt/nut stack (L3.3.1.x) | from the declared bolt length and the layout: tip Z = head-bearing Z + length; nut far face Z; top-face Z |
| fillet scan (L3.13.1.x) | per printed body: for each mesh edge, the turn angle between its two face normals; drop the exempt edges (nut-trap faces, bore and slot walls along their axis); fail on any single edge turning > 30 degrees; group adjacent edges turning > 5 degrees into bands across the edge direction and report radius = arc length / total turn, smallest first, with its location |
| mirror test (L3.10.1.1) | reflect the mesh in Y through the cleat axis plane; for `pair`, boolean symmetric difference volume |

### 7.1 Inputs

STLs of every printed body in the assembly pose (mm) or with the declared transform, the `.scad` source (for naming features, never for measuring), the declared layout file (`layout.json`: the pose
of the cleat, bolts and nuts, the grip features, `hands`, each body's print orientation) and the agent's own report (graded only by the evidence L3, never trusted elsewhere). The judge also gets
`requirements.md` and `parts/*/part.json` and nothing from the agent's code or transcript. The judge never opens `benchmarks/heldout.json`.

### 7.2 Procedure

1. **Package gate.** The listed files exist and load; otherwise stop with DOES NOT MEET and one defect on the package L3.
2. **Units.** Each body's largest bounding-box axis must be of the order stated in the package L3; if it looks like inches or metres record a defect and do not rescale silently.
3. **Normalise the frame.** Put the adapter in the pedal frame (1.1) using the declared transform: pedal-side face on Z = 17.0, foot side +Z. Rotations by multiples of 90 degrees and mirroring only; record the transform.
4. **Build the references independently** from `part.json` and section 2 of this file at the declared layout, then run the sanity checks R1..R5. A failing sanity check is fixed before grading.
5. **Run every applicable L3** with Python. Record measured value, limit, margin (measured minus limit, signed so that negative = fail) and PASS / FAIL / UNVERIFIED / N/A. **UNVERIFIED counts as FAIL.** N/A only for physical tests (no print was made).
6. **Look at the renders** after measuring, to confirm where a failure is and to catch defects no L3 covers (report those as observations; they do not change the verdict).
7. **Decide** and **report**.

### 7.3 Verdict classes

Gates: G0 package; G1 one manifold shell per body; G2 cleat fastening and adjustment; G3 cleat engagement; G4 crank clearance and left/right; G5 load case.

| Class | Rule |
|---|---|
| **WRONG** | any gate fails |
| **MINOR** | no gate fails, but some weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |
| **MEETS** | CORRECT and every applicable non-physical L3 of weight 1 and 2 passes (the loop's zero-error state) |

Anything that is not MEETS is DOES NOT MEET. Also report the weighted score sum(weight x pass) / sum(weight) over applicable L3s, and the worst normalised margin among weight-3 L3s (margin divided by the
criterion's tolerance or, for one-sided limits, by 0.5 mm; stress margins by 1 MPa).

Precedence:
- A functional check outranks the size check that serves it (cleat engages, bolt reaches its nut, crank clears beat platform size and thickness), as long as the size check still passes on its own numbers.
- **Designed contact is not interference** (section 1.3). Only penetration above 0.01 mm3 counts for the listed pairs.
- The numbers in this file are authoritative. If `parts/*/part.json` disagrees, build the reference from this file and record a defect on the L3 that the stale catalogue data breaks, with `where` = the part.json field.
- UNVERIFIED inputs (3.1) are graded on the default numbers and noted as observations; a correction from Robin changes this file first.
- Fixed decisions (section 3.2) admit no alternative. Never relax a criterion, never round in the design's favour beyond e, never infer a pass from a render.

### 7.4 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first (gates, then weight 3, 2, 1). Each entry has: `req` (L3 with its L2 and L1), `status`, `body`, `feature` (by function and, if it
exists, by its SCAD name), `face` (surface with its outward normal), `location` (coordinates in mm in the normalised frame, a point or a box `[xmin, ymin, zmin]-[xmax, ymax, zmax]`), `measured` / `limit` /
`margin` with units, `pose` (which element of P, for pose-dependent checks), `reference` (the reference model or envelope and its datum), `render` (which view and where in the image), `evidence` (saved
file, e.g. the intersection solid `defect_<L3>.stl`) and `needed` (the geometric change that would make the L3 pass).

### 7.5 Package and run

`run_suite.py --target` runs T01 alone or with the other target designs (`--iter NNN --seed S T01`); the package needs `design.json`, `layout.json`, `self_report.json` and at least one STL.
