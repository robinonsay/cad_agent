# G11 Fan-cooled power module box: requirements (L1 / L2 / L3)

A training design of the generalisation set (`benchmarks/generalize/designs/G11`). The
machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file. It is
modelled on `benchmarks/enclosure/requirements.md` (E1-01): same tree, same two interference checks,
same grading classes. The agent sees only the request text and the parts catalogue
(`benchmarks/generalize/parts/*/part.json`, plus `benchmarks/enclosure/parts/perfboard` and
`generic_cylinder`); never this file.

**Brief (plan.json G11):** "Enclosure for an 80 x 60 mm perfboard power module that dissipates around
8 W. A 40 x 40 x 10 mm fan blows in through the lid on its 32 mm hole pattern and exhaust slots line
the opposite wall, with the DC input jack on the end. Keep the fan intake at least 5 mm from the
nearest tall component."

**How to read this.** L1 says what the owner needs; L2 turns it into an engineering requirement with
numbers; L3 is a concrete check on the delivered geometry. Every row has a method, a pass/fail
criterion with a tolerance, a weight (3 critical, 2 major, 1 minor) and a gate mark where a failure
makes the design WRONG. The request supplies the sizes of the extra board parts (heatsink, two
capacitors) because the brief mentions "the nearest tall component" without naming one (A2). Do not
relax a criterion because the agent fails it.

---

## 1. Frames, tolerances and the generic checks

### 1.1 Frames

- **Box frame:** X along the board's 80 mm side, Z up, floor underside at Z = 0. The DC jack end
  is **−X**; the exhaust-slot end is **+X**. A design delivered mirrored or rotated is normalised
  into this frame before grading; that is never penalised.
- **Board frame (used for the part poses):** origin at the perfboard's top-surface corner at min X,
  min Y; Z = 0 is the board's top surface; the board occupies Z −1.6 to 0.

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered meshes (STL), never by eye.

| Quantity | Measurement tolerance ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within ε (a limit "≥ 0.50" passes at 0.48) |
| angle | 0.5° | same |
| interference volume | 0.01 mm³ | "no interference" means intersection volume ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the hole's section (what a screw or pin sees) | |
| boss / post OD | smallest enclosing circle of the section | |
| stress / strain | 2% of the limit | hand calculations use the measured section, not the nominal one |

Where a criterion is written "nominal ± t", t is the design tolerance and ε is added to it.


### 1.3 The generic checks

- **`clear_of(bodies, volume, clearance)`**: the minimum Euclidean distance between every printed
  body in `bodies` and `volume` is ≥ `clearance`. Reported: signed minimum distance d (negative =
  penetration; the penetration volume is reported too). Pass: d ≥ clearance − ε.
- **`inside(volume, solids, clearance)`**: `volume` lies entirely inside the convex hull of `solids`
  and every point of it is ≥ `clearance` from that hull's boundary and from the solids. Pass:
  d ≥ clearance − ε.
- **`gap(A, B)`**: the minimum distance between two named regions, by `min_gap` or ray casting on a
  1 mm grid (report min, median, max).
- **`play(body, axis)`**: translate the body's solid along ±axis in 0.05 mm steps (to 10 mm) until
  it first intersects a printed body by more than 0.01 mm³; report the free travel in each
  direction (sum = play along the axis).

Both checks exclude designed-contact pairs from the solids they measure against (so `inside` of a part that rests on its support passes). Generic recipes (loading, shells with `decompose()`, apertures, thickness, hole diameter,
overhang scan) are those of `benchmarks/enclosure/rubric.md` section 3, unchanged.

**Designed contact is not interference.** Pairs that are meant to touch are excluded from every
interference and clearance check; for them only penetration counts (intersection volume above
0.01 mm³; a distance of zero is a pass). For this design the designed-contact pairs are:

- the board's underside resting on the standoff tops, inside the V-SEAT-k columns;
- a board screw or fan screw in its pilot hole, and its head on the board top or the fan face;
- the fan's inlet face on the lid's underside around the intake opening;
- the lid lip against the base's locating faces, at the fit L2.8.2 sets, and the lid on the base
  rim and on the boss tops;
- the jack, heatsink and capacitors resting on the board's top surface.

---

## 2. Reference models, envelopes and datums

### 2.1 Reference models (M-)

Built by Python from the catalogue at the pose the design declares in `layout.json` (F6). A design
never builds or edits them; the grader generates them independently.

| Name | What | Source | Size and datums (board frame, mm) |
|---|---|---|---|
| **M-PERF** | 80 × 60 perfboard | `perfboard` (width 80, depth 60) | 80.0 × 60.0 × 1.6, Z −1.6 to 0; holes Ø3.0 at 2.5 from each edge: (2.5, 2.5), (77.5, 2.5), (2.5, 57.5), (77.5, 57.5), pitch 75.0 × 55.0. Datums `TOP`, `BOTTOM`, `HOLE` (4 axes, keep-out Ø7.0). |
| **M-JACK** | PJ-002A DC jack | `dc_jack_pj002a` | 14.0 × 9.0 × 11.0 on the board top; bore axis 5.5 above its bottom; mouth on the end face. Datums `MOUTH`, `AXIS` (outward), `BOTTOM`. |
| **M-HS** | heatsink | `generic_box` (20 × 12 × 20, from the request) | box 20 × 12 × 20 tall, base on the board top; the design may turn it 90° about Z. |
| **M-CAP-1, -2** | electrolytic capacitors | `generic_cylinder` (Ø10 × 16, from the request) | cylinders Ø10 × 16 tall on the board top. |
| **M-FAN** | 40 × 40 × 10 axial fan | `fan_40x40x10` | frame 40 × 40 × 10, inlet face at Z 0 of the part frame, airflow +Z of the part frame; bore Ø38; holes Ø3.2 on a 32.0 pitch (4 `HOLE` axes, keep-out Ø7.0); `inlet_air` and `exhaust_air` keep-outs 5.0. |
| **M-PLUG-DC** | DC barrel plug | `plug_dc_barrel_5p5` | barrel Ø5.5 × 14.0, overmold Ø11.0 × 16.0, stop gap 1.0; `SEAT` 13.0 from the tip. |
| **M-BOLT-M3** | M3 socket-head screw | `bolt_m3_iso4762` | head Ø5.5 × 3.0, thread Ø3.0, tap Ø2.5, clearance Ø3.4. Length is declared per use. |
| **RBA** | reference board assembly | M-PERF ∪ M-JACK ∪ M-HS ∪ M-CAP-1 ∪ M-CAP-2 at the declared poses | no printed geometry |

"Tall component" = any RBA part other than M-PERF (all of them reach above 10.0 over the board:
the jack 11.0, the capacitors 16.0, the heatsink 20.0).

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-SEAT-k** (k = 1..4) | where a standoff may touch the board | Ø7.0 column on `HOLE`k, from the floor up to the board's `BOTTOM`. |
| **V-HOLE-KO-k** | screw-head room above each board hole | Ø7.0 column on `HOLE`k, Z 0 to +12.0 above the board top. |
| **V-KO-BOT** | solder-side zone | board footprint, 4.0 below `BOTTOM` (3.0 of solder and clipped leads plus 1.0 margin), minus the V-SEAT-k. |
| **V-PARTS-GROWN** | every RBA part except M-PERF grown by 0.5 | headroom zone for L2.4.1. |
| **V-DC-PLUG** | the plug at full mate plus its path | M-PLUG-DC with `SEAT` on `MOUTH`, `PLUG_AXIS` along `AXIS`: barrel from 13.0 inside the mouth to 1.0 outside it; overmold Ø11.0 from 1.0 outside the mouth outward 16 + 40 (the 40 is the generic plug travel). |
| **V-FAN-FRAME** | the fan's frame at its declared pose | the 40 × 40 × 10 block of M-FAN. |
| **V-FAN-EXH** | air room below the fan | the `exhaust_air` keep-out of M-FAN: 40 × 40 × 5 beyond the exhaust face. |
| **V-FANSCREW-k** | fan screw head | Ø5.5 × 3.0 cylinder on `HOLE`k of M-FAN against its exhaust face (the heads are on the room side). |
| **V-BORE** | the fan's intake circle | Ø38.0 circle about M-FAN's `AIRFLOW` axis, in the lid's plan. |
| **V-INSTALL** | board installation path | the RBA's plan silhouette swept +Z from its seated pose to 5.0 above the base rim, minus the V-SEAT-k columns. |
| **V-DRIVER-k** | screwdriver access to a board screw | Ø6.0 column on `HOLE`k from the board top to 50 above the base rim, lid off. |
| **V-LIDDRIVER-j** | screwdriver access to a lid screw | Ø6.0 column on each lid-screw axis from the lid top to 50 above it. |
| **V-CAVITY** | the closed box's internal void | convex hull of (BASE ∪ LID, closed) minus (BASE ∪ LID), the connected component containing the RBA centroid. |
| **V-AP-DC**, **V-AP-EXH**, **V-AP-FAN**, **V-AP-OTHER** | the openings actually present in the −X wall, the +X wall, the lid's fan region, and everywhere else | computed as in `benchmarks/enclosure/rubric.md` 3.4; regions under 1 mm³ ignored. |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | every model | units: bounding box in mm | M-PERF 80 × 60 × 1.6 ± 0.2; M-FAN 40 × 40 × 10 ± 0.2; M-JACK 14 × 9 × 11 ± 0.4 |
| R2 | M-JACK | bore axis height, mouth on the +X face of the part frame | 5.5 ± 0.3; true |
| R3 | M-FAN | hole pitch and bore | 32.0 ± 0.1; Ø38 ± 0.5 |
| R4 | RBA | parts do not collide | intersection ≤ 0.01 mm³ |
| R5 | every V- envelope | its datums equal the model datums it came from | ≤ 0.01 |

**Seating rule.** The RBA is placed at the pose declared in `layout.json`. The grader verifies:
`BOTTOM` of M-PERF lies on the standoff tops (distance ≤ 0.10) and the `HOLE` axes are coaxial
with the standoff pilots (residual ≤ 0.25). The fan's `INLET` plane must lie within 0.2 of the
lid underside and its `HOLE` axes be coaxial with the lid pilots (residual ≤ 0.25). If a
declaration fails, the part is re-seated by the nearest printed support and the L3 that needed the
declaration fails.

---

## 3. Assumptions and open questions

| # | Question | Value chosen | Uncertainty / why |
|---|---|---|---|
| A1 | Where is the fan, which way does it blow? | inside the box, on the lid's underside, airflow into the box (−Z in the box frame), inlet face on the lid over an opening in it | the brief says "blows in through the lid"; the alternative (a fan outside the lid) would not keep the intake gap against components, so it is not graded. |
| A2 | What is the "nearest tall component"? | the request names three: a 20 × 12 × 20 heatsink and two Ø10 × 16 capacitors; the DC jack (11.0) also counts. "At least 5 mm" is the gap between the fan's frame and every RBA part other than the board | stricter than checking only the intake face; satisfied by distance, not by orientation. Heights come from the request (`generic_box`, `generic_cylinder`). |
| A3 | Exhaust area needed? | total slot area ≥ 567 mm², half of the fan bore area (π × 19² = 1134 mm²) | ± 20 %; no flow simulation. A free-air fan loses most of its flow behind a small grille; half the bore is the smallest area that does not choke an 8 W box. Thermal performance is not simulated. |
| A4 | Board? | 80 × 60 × 1.6, corner holes Ø3.0 at 2.5 from each edge (catalogue family default, repeated in the request) | ± 0.3 hole position on a real board. |
| A5 | Jack? | PJ-002A body 14 × 9 × 11, axis 5.5 up, mouth on the end face | terminal positions are the least certain values (catalogue note); the enclosure does not use them. |
| A6 | Plug sizes? | barrel Ø5.5 × 14.0; overmold Ø11.0 × 16 (+3 on the diameter in the catalogue note); stop gap 1.0 | measure the owner's adapter. An overmold of Ø14 would need a Ø14.6 opening and would fail the oversize limit (L2.5.2). |
| A7 | Solder side? | 3.0 of solder and clipped leads plus 1.0 margin = 4.0 below the board | ± 1.0. |
| A8 | Headroom above parts? | 0.5 to every printed surface | the generic part-to-wall allowance. |
| A9 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed; sliding fit 0.15-0.35 per side | typical FDM tolerances. |
| A10 | Walls? | outer walls and floor 2.0-4.0; lid plate 4.8-6.0 (the fan screws need 4.0 of pilot plus 0.8 of skin); internal ribs ≥ 0.8 | M3 self-tapping wants at least 1 × the thread diameter of engagement. |
| A11 | Size limit? | closed box ≤ 100 × 80 × 40 (X × Y × Z), X > Y | the layout in section 7 is about 99 × 69 × 34. |
| A12 | Fan flow direction? | `+Z` of the part frame is the airflow; the pose flips it | arrows on real frames; flip by pose if reversed. |
| A13 | Fan screws? | M3 from the exhaust side into blind pilots in the lid (the fan holes are Ø3.2, plain) | the heads stay on the room side; the lid is flipped to fit the fan. |
| A14 | Board screws? | M3 through the Ø3.0 board holes into standoff pilots (tap Ø2.5); an M3 shank passes a Ø3.0 hole as given | the catalogue rule `given_hole_clearance_min` is 0. |

---

## 4. Fixed decisions (a choice would otherwise be ambiguous)

| # | Decision | Why |
|---|---|---|
| F1 | The DC jack is on the −X short end wall, its axis pointing out of −X. The exhaust slots are in the +X short end wall, the one opposite. | "the DC input jack on the end", "exhaust slots line the opposite wall": the ends are the short walls. |
| F2 | The fan is on the lid's underside (A1); its airflow axis is vertical. | A1. |
| F3 | The lid is a flat plate covering the base's whole outer outline (± 0.5), with a locating lip on its underside inside the base walls (continuous or segmented), held by 4 × M3 self-tapping screws through plain holes into 4 base bosses that lie outside the board's plan outline. No snap or sliding lid. | robust; the board's corners are taken by standoffs, so the bosses go at the cavity's corners outside the board. |
| F4 | The base holds the board on four standoffs under its corner holes, fixed with 4 × M3 screws. The lid screws and the board screws are different screws. | removing the lid must not release the board. |
| F5 | Print orientation: base open side up, lid outer face down; stated in `layout.json`. | needed to grade printability. |
| F6 | `layout.json` declares the pose of every RBA part (catalogue id, X, Y, Z, rotation about Z in 90° steps), the fan pose, the declared screw lengths (board screws, fan screws) and each body's print orientation. | needed by the seating rule and L2.3.4, L2.6.3. |
| F7 | Screw lengths are standard ISO 4762 M3 lengths: 6, 8, 10, 12, 14, 16, 20. | screws are bought in those lengths. |

---

## 5. Requirements tree

Columns: ID, requirement, method, pass/fail (with tolerance), weight, gate.

### L1.1 The jack, heatsink and capacitors are laid out on the 80 × 60 board, the jack at one short end, without collisions

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout (F6). | inspection | `layout.json` parses; names M-PERF, M-JACK, M-HS, M-CAP-1, M-CAP-2, M-FAN with a pose each | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 | |
| L2.1.2 | The jack faces the −X end. | inspection | `AXIS` within 1.0° of −X; `MOUTH` X in [−1.5, 3.0] of the board's −X edge | 3 | |
| L3.1.2.1 | Jack axis direction. | inspection | ≤ 1.0° (+ 0.5° ε) | 3 | |
| L3.1.2.2 | Jack mouth position. | inspection | X in [−1.5, 3.0] | 2 | |
| L2.1.3 | The parts sit on the board and do not collide. | analysis | RBA pairs ≤ 0.01 mm³; each part's bottom within 0.1 of the board's top; plan outline within X [−1.5, 80], Y [0, 60] | 3 | |
| L3.1.3.1 | Pairwise interference of RBA parts. | analysis | each pair ≤ 0.01 mm³ | 3 | |
| L3.1.3.2 | Bottoms on the board; plan outlines. | inspection | as L2.1.3 | 2 | |
| L2.1.4 | No part covers a corner screw. | analysis | clear_of(RBA parts except M-PERF, V-HOLE-KO-1..4, 0.0) | 3 | |
| L3.1.4.1 | Screw columns clear of parts. | analysis | d ≥ 0.0 | 3 | |

### L1.2 The 80 × 60 × 1.6 board fits inside with at least 0.5 mm clearance at its edges

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Lid closed: no printed body within 0.5 of the board, except the standoff tops under its holes. | analysis | clear_of(ALL, M-PERF minus Ø8.0 columns on `HOLE`1..4, 0.5) | 3 | G2 |
| L3.2.1.1 | Board-edge clearance, all four edges and both faces. | analysis | d ≥ 0.50 | 3 | G2 |
| L3.2.1.2 | An 80 × 60 × 1.6 box lying flat fits the base with 0.5 clearance (the agent's own-model proxy). | demonstration | fits passes into BASE | 2 | |
| L2.2.2 | Every board part is inside the cavity with room. | analysis | inside(RBA parts except M-PERF, V-CAVITY, 0.5) | 3 | |
| L3.2.2.1 | Jack, heatsink and capacitors inside the cavity. | analysis | d ≥ 0.50 | 3 | |

### L1.3 The board is held on four standoffs by M3 screws through its corner holes

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Four standoffs, one under each board hole, on the 75.0 × 55.0 hole rectangle. | inspection | count = 4; each axis within 0.25 of its `HOLE`k | 3 | G2 |
| L3.3.1.1 | Standoff count. | inspection | 4 | 3 | G2 |
| L3.3.1.2 | Standoff axes vs the seated board's holes. | analysis | each offset ≤ 0.25 | 3 | |
| L3.3.1.3 | Standoff pitch. | inspection | 75.0 ± 0.25 along X; 55.0 ± 0.25 along Y | 3 | |
| L2.3.2 | Standoff OD 5.7-7.0 (pilot Ø2.5 + 2 × 1.6 wall, `standoff_wall_min`, up to the Ø7.0 hole keep-out); tops coplanar; each top touches the board only inside its V-SEAT column; height 4.0-10.0 above the floor top. | inspection | OD in [5.7, 7.0]; top spread ≤ 0.10; standoffs ⊂ V-SEAT-k up to `BOTTOM`; height in [4.0, 10.0] | 2 | |
| L3.3.2.1 | Standoff OD. | inspection | 5.7 ≤ OD ≤ 7.0 | 2 | |
| L3.3.2.2 | Top-plane spread and height. | inspection | spread ≤ 0.10; height in [4.0, 10.0] | 2 | |
| L2.3.3 | Each standoff has a pilot hole for an M3 self-tapping screw. | inspection | Ø2.4-2.6, depth ≥ 5.0 from the top, coaxial ≤ 0.1 | 3 | G2 |
| L3.3.3.1 | Pilot diameter and depth. | inspection | Ø in [2.4, 2.6]; depth ≥ 5.0 | 3 | G2 |
| L2.3.4 | The declared board screws (F6, F7) bite properly. | analysis | thread engagement = L − 1.6 (board) in [4.0, pilot depth] | 2 | |
| L3.3.4.1 | Board screw engagement. | analysis | in [4.0, pilot depth] (L = 6 gives 4.4) | 2 | |
| L2.3.5 | Standoffs are fused to the floor; the base is one body. | analysis | contact per standoff ≥ 15 mm²; BASE 1 shell | 2 | |
| L3.3.5.1 | Standoff-to-floor contact area. | analysis | ≥ 15 mm² each | 2 | |
| L2.3.6 | Nothing but the screws enters the board holes' columns above the board. | analysis | clear_of(ALL, V-HOLE-KO-k minus a Ø3.4 core, 0.0) | 2 | |
| L3.3.6.1 | Screw-head columns clear. | analysis | d ≥ 0.0 | 2 | |

### L1.4 The parts clear the box: at least 0.5 mm above the tallest part, 4.0 mm below the board

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Lid closed: no printed body within 0.5 of any board part. | analysis | clear_of(ALL, V-PARTS-GROWN, 0.0) (parts grown 0.5) | 3 | |
| L3.4.1.1 | Part headroom. | analysis | d ≥ 0.0 (i.e. ≥ 0.5 to every part) | 3 | |
| L3.4.1.2 | Lid underside minus the tallest part's top (own-model proxy). | inspection | ≥ 0.5 | 2 | |
| L2.4.2 | No body enters the solder-side zone. | analysis | clear_of(ALL, V-KO-BOT, 0.0) | 3 | |
| L3.4.2.1 | Bottom keep-out clear. | analysis | d ≥ 0.0 | 3 | |

### L1.5 A 5.5 × 2.1 mm DC plug plugs into the jack through one opening in the −X end wall with the lid on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Lid closed: the plug pushes in to full mate and pulls out without touching the box. | test | clear_of(ALL, V-DC-PLUG, 0.3) | 3 | G3 |
| L3.5.1.1 | Plug envelope clear. | test | d ≥ 0.30 | 3 | G3 |
| L3.5.1.2 | Physical: print, close, plug in a real adapter. | test | seats fully, 3 of 3 tries | 2 | physical, optional |
| L2.5.2 | The opening is not oversized. | analysis | inside(V-AP-DC, V-DC-PLUG grown 1.5 on each side, 0.0) | 2 | |
| L3.5.2.1 | Opening within the grown envelope. | analysis | d ≥ 0.0 (opening Ø ≤ 14.0 and ≥ 11.6) | 2 | |
| L2.5.3 | Exactly one DC opening, in the −X wall. | inspection | V-AP-DC has 1 region of area > 1 mm³ | 2 | |
| L3.5.3.1 | Opening count in the −X wall. | inspection | 1 | 2 | |

### L1.6 The fan sits on the lid on its 32 mm pattern, blows into the box, and its intake is 5 mm from every tall part

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | The fan is on the lid's underside, airflow into the box, inlet over the lid opening. | inspection | `AIRFLOW` within 2.0° of −Z (box); `INLET` plane within 0.2 of the lid underside; the whole 40 × 40 plan lies within the lid's plan | 3 | |
| L3.6.1.1 | Fan orientation and seating. | inspection | as L2.6.1 | 3 | |
| L2.6.2 | Four lid pilots on the fan's 32.0 pattern for M3. | inspection | pilot axes within 0.25 of M-FAN `HOLE`k; Ø2.4-2.6; blind depth in [4.0, lid thickness − 0.8] | 3 | G4 |
| L3.6.2.1 | Pilot positions on the fan pattern. | inspection | each offset ≤ 0.25; pitch 32.0 ± 0.25 | 3 | G4 |
| L3.6.2.2 | Pilot diameter and depth. | inspection | Ø in [2.4, 2.6]; depth in [4.0, lid − 0.8] | 2 | |
| L2.6.3 | The declared fan screws bite properly and stay on the room side. | analysis | engagement = L − 10.0 in [3.0, pilot depth]; V-FANSCREW-k clear: clear_of(ALL ∪ parts, V-FANSCREW-k, 0.5) | 2 | |
| L3.6.3.1 | Fan screw engagement (L = 14 gives 4.0). | analysis | in [3.0, pilot depth] | 2 | |
| L3.6.3.2 | Fan screw heads clear. | analysis | d ≥ 0.50 | 2 | |
| L2.6.4 | The fan's intake is at least 5 mm from the nearest tall part (A2). | analysis | gap(V-FAN-FRAME, every RBA part except M-PERF) ≥ 5.0 | 3 | G4 |
| L3.6.4.1 | Fan-to-part gap. | analysis | min gap ≥ 5.0 | 3 | G4 |
| L2.6.5 | The lid opens to the fan's bore without leaking round it. | analysis | V-AP-FAN lies inside V-BORE grown 0.2; its open area ≥ 680 mm² (60 % of V-BORE); centre within 0.5 of `AIRFLOW`; clear of the pilot columns Ø7.0 | 3 | |
| L3.6.5.1 | Intake opening area and position. | analysis | area in [680, 1158]; offset ≤ 0.5 | 3 | |
| L3.6.5.2 | Opening within the bore, clear of the screw columns. | analysis | outside part = 0; d to the Ø7.0 columns ≥ 0.0 | 2 | |
| L2.6.6 | The air room below the fan is free. | analysis | no printed body in V-FAN-EXH | 2 | |
| L3.6.6.1 | Exhaust room clear. | analysis | clear_of(ALL except the fan's own lid seat, V-FAN-EXH, 0.0): d ≥ 0.0 | 2 | |

### L1.7 Exhaust slots line the +X end wall with enough open area

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | At least 8 slots in the +X wall, each 2.0-4.0 wide and at least 10.0 tall, with at least 1.5 of material between slots and to the wall's edges, the floor top and the seam. | analysis | slot count ≥ 8; widths in [2.0, 4.0]; heights ≥ 10.0; ligaments ≥ 1.5 | 2 | |
| L3.7.1.1 | Slot count, width, height. | analysis | as L2.7.1 | 2 | |
| L3.7.1.2 | Slot ligaments. | analysis | ≥ 1.5 | 1 | |
| L2.7.2 | Total exhaust area is at least half the fan bore. | analysis | sum of V-AP-EXH slot areas ≥ 567 mm² | 3 | G5 |
| L3.7.2.1 | Exhaust area. | analysis | ≥ 567 | 3 | G5 |
| L2.7.3 | Exhaust is on the opposite end only. | inspection | V-AP-EXH lies entirely in the +X wall; no slot in the −X wall or the long walls | 2 | |
| L3.7.3.1 | Exhaust slots all in the +X wall. | inspection | 100 % | 2 | |

### L1.8 A removable lid closes the box and stays on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Base and lid are separate single-shell bodies that do not interpenetrate. | analysis | BASE 1 shell; LID 1 shell; BASE ∩ LID ≤ 1.0 mm³ | 3 | G1 |
| L3.8.1.1 | One shell each. | analysis | `decompose()` count 1 per body | 3 | G1 |
| L3.8.1.2 | Closed overlap. | analysis | ≤ 1.0 mm³ | 3 | |
| L2.8.2 | A lip locates the lid with a sliding fit (F3). | inspection | engagement 2.0-3.0; clearance 0.15-0.35 per side on every locating face | 2 | |
| L3.8.2.1 | Lip-to-wall gap. | inspection | 0.15 ≤ gap ≤ 0.35 | 2 | |
| L3.8.2.2 | Lip engagement depth. | inspection | in [2.0, 3.0] | 1 | |
| L2.8.3 | The lid is held by exactly 4 M3 self-tapping screws into 4 bosses outside the board's plan. | inspection | bosses = 4; boss pilot Ø2.4-2.6, depth ≥ 6.0, OD ≥ 5.7; lid holes Ø3.3-3.5, coaxial ≤ 0.3; bosses clear of V-INSTALL | 2 | |
| L3.8.3.1 | Exactly 4 bosses, outside the board's plan. | inspection | count 4; plan distance to the board outline ≥ 0.5 | 2 | |
| L3.8.3.2 | Boss pilot Ø, depth, OD. | inspection | Ø in [2.4, 2.6]; depth ≥ 6.0; OD ≥ 5.7 | 2 | |
| L3.8.3.3 | Lid holes coaxial with the pilots. | inspection | Ø in [3.3, 3.5]; offset ≤ 0.3 | 2 | |
| L3.8.3.4 | Lid-screw driver columns. | analysis | clear_of(ALL, V-LIDDRIVER-1..4, 0.0) | 1 | |
| L2.8.4 | Lid form: a flat plate over the base outline with a lip. | inspection | plate thickness 4.8-6.0; plate outline = base outer outline ± 0.5 on all four sides; total lid height ≤ 9.0 | 3 | |
| L3.8.4.1 | Plate thickness, outline match, total height. | inspection | as L2.8.4 | 3 | |
| L2.8.5 | The closed seam is tight and flush. | inspection | seam gap ≤ 0.5; outer-face step ≤ 0.5 | 1 | |
| L3.8.5.1 | Seam gap and flushness on all four sides. | inspection | as L2.8.5 | 1 | |
| L3.8.5.2 | Physical: hold the closed box upside down and shake; open and close 10 times. | test | lid stays on; nothing strips | 2 | physical, optional |

### L1.9 The box is closed except for the DC opening, the exhaust slots, the fan intake and screw holes, with 2-4 mm walls

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The only openings are those four. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere into V-CAVITY, other than the screw holes | 2 | |
| L3.9.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 | |
| L2.9.2 | Walls and floor are 2.0-4.0 thick; the lid plate per L2.8.4. | inspection | each median in range | 2 | |
| L3.9.2.1 | Wall thickness (median, away from features). | inspection | 2.0 ≤ t ≤ 4.0 | 2 | |
| L3.9.2.2 | Floor thickness. | inspection | 2.0 ≤ t ≤ 4.0 | 2 | |
| L2.9.3 | At least 1.5 of material around the DC opening (to the wall's edges and the floor top). | analysis | min ligament ≥ 1.5 | 1 | |
| L3.9.3.1 | DC opening ligament. | analysis | ≥ 1.5 | 1 | |
| L2.9.4 | Each wall joins the floor along its length. | analysis | contact ≥ 90 % of length × thickness | 2 | |
| L3.9.4.1 | Wall-to-floor contact. | analysis | ≥ 90 % | 2 | |

### L1.10 Both parts print on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | In the stated orientation (F5) no unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12 in vertical walls and bridges ≤ 15.0. | analysis | 0 offending faces of area > 1 mm² | 2 | |
| L3.10.1.1 | Overhang and bridge scan per body. | analysis | as L2.10.1 | 2 | |
| L2.10.2 | Each body is manifold and one shell. | analysis | 1 shell; manifold3d accepts it | 3 | G1 |
| L3.10.2.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.10.3 | Each body rests on a flat face. | analysis | bed contact ≥ 50 % of the plan bounding box | 1 | |
| L3.10.3.1 | Bed contact per body. | analysis | ≥ 50 % | 1 | |
| L2.10.4 | No feature thinner than 0.8; mating gaps ≥ 0.15. | analysis | min thickness ≥ 0.8; min mating gap ≥ 0.15 | 1 | |
| L3.10.4.1 | Thin-feature and mating-gap scan. | analysis | as L2.10.4 | 1 | |
| L2.10.5 | Each body fits a 200 × 200 × 200 bed. | inspection | ≤ 200 per axis | 1 | |
| L3.10.5.1 | Bounding box per body. | inspection | ≤ 200 per axis | 1 | |

### L1.11 It stands flat on a desk and is no larger than 100 × 80 × 40 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Closed outside size (A11). | inspection | X ≤ 100.0, Y ≤ 80.0, Z ≤ 40.0; X > Y | 1 | |
| L3.11.1.1 | Assembly bounding box. | inspection | as L2.11.1 | 1 | |
| L2.11.2 | It stands on its base without tipping. | analysis | stable at 5° table tilt (RBA plus fan about 150 g, the shell included) | 1 | |
| L3.11.2.1 | Tilt stability. | analysis | centre of mass inside the support polygon at 5° | 1 | |
| L2.11.3 | Flat underside. | inspection | flatness ≤ 0.2; nothing below the floor | 1 | |
| L3.11.3.1 | Underside planarity. | inspection | as L2.11.3 | 1 | |

### L1.12 The board goes in and out with the lid off, using a screwdriver

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | Lid off: the RBA drops straight down onto the standoffs without hitting anything. | test | clear_of(BASE, V-INSTALL, 0.2) with V-INSTALL excluding the V-SEAT-k columns | 2 | |
| L3.12.1.1 | Installation path clear. | test | d ≥ 0.20 | 2 | |
| L2.12.2 | A screwdriver reaches every board screw. | analysis | clear_of(BASE, V-DRIVER-1..4, 0.0) | 1 | |
| L3.12.2.1 | Driver columns clear. | analysis | d ≥ 0.0 | 1 | |
| L2.12.3 | Removing the lid does not release the board (F4). | inspection | no shared fastener | 1 | |
| L3.12.3.1 | Judge confirms no fastener is shared. | inspection | true | 1 | human |

### L1.13 The package says what was built and where, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | The package holds `base.stl`, `lid.stl` (closed pose, box frame, mm), the OpenSCAD source, `layout.json` (F6) and the agent's own clearance report. | inspection | all present and readable | 3 | G0 |
| L3.13.1.1 | Files present and parse; each body's largest bounding-box axis in 20-200 mm. | inspection | true | 3 | G0 |
| L3.13.1.2 | The declared layout verifies under the seating rule (section 2.3). | analysis | board on standoff tops ≤ 0.10; hole-axis residual ≤ 0.25; fan inlet plane ≤ 0.2 from the lid underside; fan pilot residual ≤ 0.25 | 3 | |
| L2.13.2 | The agent's own clearance report agrees with the judge. | analysis | for every `clear_of` / `inside` L3 the agent reports: same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 | |
| L3.13.2.1 | Self-report vs judge. | analysis | 100 % agreement within 0.10 | 1 | |

---

## 6. Counts and gates

| Level | Count |
|---|---|
| L1 | 13 |
| L2 | 48 |
| L3 | 68 (weight 3: 24, weight 2: 30, weight 1: 14; 3 physical or human, optional) |

Every L3 is a measurement a Python script can make on the delivered STL (or on the declared
`layout.json` against the catalogue), except the rows marked physical or human.

Gates (a failure makes a design WRONG regardless of score): see section 9.

---

## 7. Feasibility

One design exists that meets every L3 above (box frame, mm; outer min corner at the origin; wall
2.4; the numbers below are the centred layout):

- **Cavity:** inner X 2.4-96.4 (94.0), Y 2.4-66.4 (64.0). Outer 98.8 × 68.8 × 34.0 (limit 100 × 80 ×
  40; X > Y). Floor Z 0-2.4, base wall top (seam) Z = 29.0, lid plate 5.0 (Z 29.0-34.0).
- **Board:** X 9.2-89.2, Y 4.4-64.4 (7.0 / 2.0 margin each side), top at Z 8.0 (standoffs 4.0 high:
  tops at 6.4). Holes at (11.7, 6.9), (86.7, 6.9), (11.7, 61.9), (86.7, 61.9). Standoffs OD 6.0
  with Ø2.5 pilots 6.0 deep, M3 × 6 board screws (engagement 6 − 1.6 = 4.4 in [4.0, 6.0]).
  Clearance to the walls: 6.8 in X, 2.0 in Y (≥ 0.5). Solder side exactly 4.0 (floor top 2.4 to
  board bottom 6.4).
- **Parts (board frame → box frame by +(9.2, 4.4, 8.0)):** jack X 0-14, Y 25.5-34.5 mouth at
  X 0 facing −X (box X 9.2-23.2, top Z 19.0); heatsink turned 90°, X 66-78, Y 20-40, top 20
  (box top Z 28.0); capacitors at (70, 10) and (70, 50), Ø10 × 16 (box top Z 24.0). The corner
  columns are clear (cap to hole (77.5, 2.5): 10.6 − 5 − 3.5 = 2.1).
- **Fan:** frame on the lid's underside, plan X 28.7-68.7, Y 14.4-54.4 (axis (48.7, 34.4)), frame
  Z 19.0-29.0; bore `V-BORE` on the lid. Gaps to parts: jack 28.7 − 23.2 = 5.5, heatsink 75.2 −
  68.7 = 6.5, capacitors 74.2 − 68.7 = 5.5 (all ≥ 5.0). Heatsink top 28.0 against the lid
  underside 29.0: headroom 1.0. Fan pilots at X 32.7 / 64.7, Y 18.4 / 50.4, Ø2.5, 4.2 deep in the
  5.0 plate (skin 0.8, the most L3.6.2.2 allows); M3 × 14 screws give 4.0 engagement with 0.2 to spare. Intake opening Ø38 with four spokes
  of 2.0 (area ≈ 1134 − 4 × 2 × 19 = 982 ≥ 680; spokes avoid the screw columns).
- **DC opening:** −X wall, Ø11.6 centred on (Y 34.4, Z 13.5): 11.6 ≥ 11.0 + 0.6; oversize 0.3 per
  side (≤ 1.5); ligament to the floor top 7.7 − 2.4 = 5.3, to the seam 29 − 19.3 = 9.7. The
  overmold front face (X 8.2) is inside the cavity, 5.8 in front of the wall's inner face; the
  plug path through the cavity is free.
- **Exhaust:** +X wall, 10 vertical slots 3.0 × 20.0 at pitch 4.5, Y 12.65-56.15, Z 7.0-27.0:
  area 600 ≥ 567; ligaments 1.5 between slots, 4.6 to the floor top, 2.0 to the seam, 10.25 to
  the wall's edge.
- **Lid closure:** four bosses OD 6.0, pilots Ø2.5 × 6.5 deep, at (5.4, 5.4), (5.4, 63.4), (93.4,
  5.4), (93.4, 63.4), reaching the seam height; plan distance to the board (X ≥ 9.2) is 0.8 ≥
  0.5. Lid holes Ø3.4. Lip 1.2 thick, 3.0 deep (Z 26-29), 0.25 inside the walls (fit 0.25), in
  segments between the bosses; plate outline 98.8 × 68.8 (equal to the base).
- **Printability:** base open side up, lid plate down; round holes ≤ 12, slot bridges 3.0 ≤ 15.0;
  the intake Ø38 has a vertical axis in the lid orientation, so it needs no support.

This sketch is one satisfiable design; it is not the only one and is never given to the agent.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 (`design.json`) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1-L2.1.4 | L3.1.1.1, L3.1.2.1-2, L3.1.3.1-2, L3.1.4.1 | L1.1 | inspection | "DC input jack on one short end" |
| L1.2 | Board fits | L2.2.1-L2.2.2 | L3.2.1.1-2, L3.2.2.1 | L1.2 | analysis | "80 x 60 mm perfboard" |
| L1.3 | Board fixed | L2.3.1-L2.3.6 | L3.3.1.1-3, L3.3.2.1-2, L3.3.3.1, L3.3.4.1, L3.3.5.1, L3.3.6.1 | L1.3 | inspection | "mounting hole in each corner" |
| L1.4 | Component clearance | L2.4.1-L2.4.2 | L3.4.1.1-2, L3.4.2.1 | L1.4 | analysis | "heatsink and two capacitors" |
| L1.5 | DC plug access | L2.5.1-L2.5.3 | L3.5.1.1-2, L3.5.2.1, L3.5.3.1 | L1.5 | test | "DC plug must plug in with the lid on" |
| L1.6 | Fan | L2.6.1-L2.6.6 | L3.6.1.1, L3.6.2.1-2, L3.6.3.1-2, L3.6.4.1, L3.6.5.1-2, L3.6.6.1 | L1.6 | inspection | "fan blows in through the lid on its 32 mm hole pattern", "intake at least 5 mm from the nearest tall component" |
| L1.7 | Exhaust | L2.7.1-L2.7.3 | L3.7.1.1-2, L3.7.2.1, L3.7.3.1 | L1.7 | analysis | "exhaust slots line the opposite end wall" |
| L1.8 | Lid | L2.8.1-L2.8.5 | L3.8.1.1-2, L3.8.2.1-2, L3.8.3.1-4, L3.8.4.1, L3.8.5.1-2 | L1.8 | inspection | "base and a removable lid" |
| L1.9 | Protection | L2.9.1-L2.9.4 | L3.9.1.1, L3.9.2.1-2, L3.9.3.1, L3.9.4.1 | L1.9 | analysis | "enclosure" (implied) |
| L1.10 | Printable | L2.10.1-L2.10.5 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1, L3.10.5.1 | L1.10 | analysis | "printed on an FDM printer" |
| L1.11 | Size, stable | L2.11.1-L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | L1.11 | analysis | "sits on a desk" (implied) |
| L1.12 | Assembly | L2.12.1-L2.12.3 | L3.12.1.1, L3.12.2.1, L3.12.3.1 | L1.12 | test | implied |
| L1.13 | Evidence | L2.13.1-L2.13.2 | L3.13.1.1-2, L3.13.2.1 | L1.13 | inspection | needed by the judge |

## 9. Grading procedure for G11

`benchmarks/generalize/rubric.md` did not exist when this file was written, so this section is the design-specific rubric (units, frames, recipes, classes, defect reports). If a generic rubric.md appears later it governs generic rules; this section still governs everything specific to G11.

1. **Package gate (G0).** The files of the last L1 must exist and load. If a delivered STL is
   missing or unreadable, stop: verdict DOES NOT MEET, one defect on the G0 L3.
2. **Units.** Load each STL; the largest bounding-box axis of base.stl and lid.stl must be 20-200 mm
   (a thin axis is expected). If it looks like inches or metres record a defect, do not rescale.
3. **Normalise the frame** (section 1.1) with rotations by multiples of 90° and mirroring only;
   record the transform; never penalise it.
4. **Build the references independently** from `part.json` and the declared `layout.json`
   (sections 2 and 3), run the sanity checks, then verify the seating rule.
5. **Run every L3** in order. Record measured value, limit, signed margin (negative = fail),
   PASS / FAIL / UNVERIFIED / N/A. UNVERIFIED counts as FAIL; N/A only for physical tests (unless
   a print was made) and the closure/variant the design does not use.
6. **Look at renders after measuring**; they locate defects and catch what no L3 covers
   (observations; they never make a check pass).

**Classes.** WRONG = any gate fails. MINOR = no gate fails but a weight-3 L3 fails. CORRECT = no
gate fails and every weight-3 L3 passes. **MEETS** = CORRECT and every applicable non-physical L3
of weight 1 and 2 passes; anything else is DOES NOT MEET. Also report the weighted score
Σ(weight × pass) / Σ(weight) over applicable L3s and the worst normalised margin among weight-3
L3s (margin ÷ the criterion's tolerance, or ÷ 0.5 mm for one-sided limits).

Gates: G0 package (L3.13.1.1); G1 manifold, one shell per body, two bodies (L3.10.2.1, L3.8.1.1); G2 board fit (L3.2.1.1) and board fixed (L3.3.1.1, L3.3.3.1); G3 DC plug seats (L3.5.1.1); G4 fan on its pattern with its 5 mm intake gap (L3.6.2.1, L3.6.4.1); G5 exhaust area (L3.7.2.1).

**Precedence.** (1) The numbers in this requirements.md beat `part.json` wherever they differ: build
the reference from requirements.md and record a defect on the requirement the stale catalogue
data breaks, with where = the part.json field. (2) Plug-seating, fit and clearance checks outrank
anything about opening or feature size. (3) Designed contact is never interference (section 1.3).
(4) Never relax a criterion, never round in the design's favour beyond ε, never infer a pass from
a render. (5) A requirement that looks impossible or self-contradicting is reported as an
observation with its numbers and still graded as written.

**Where a defect is.** One entry per failed or UNVERIFIED L3, most severe first (gates, weight 3,
2, 1), with the fields: `req` (L3 with its L2 and L1), `status`, `body`, `feature` (by function
and SCAD name), `face` (surface, side, outward normal), `location` (mm, in the graded frame: a
point or a bounding box), `measured` / `limit` / `margin`, `reference` (the M- or V- object and its
datum), `render`, `evidence` (saved file such as `defect_<L3>.stl`), `needed` (the geometric target
as numbers, never "use a difference()"). Coordinates come from measurement, not from the SCAD
source. Group L3s that fail for one geometric reason under the first and list the rest in
`also_fails`. Render-only findings are observations, listed apart.

Never open or use `benchmarks/heldout.json`.

## Audit

Adversarial audit of this entry, 2026-10-24. Numbers recomputed from `part.json` and the section 7
sketch (fan, jack, heatsink and capacitor gaps 5.5 / 6.5 / 5.5; hole-to-capacitor 2.1; opening 11.6 =
11.0 + 2 × 0.3; slot area 10 × 3.0 × 20.0 = 600 ≥ 567 = half of π × 19²; engagement 6 − 1.6 = 4.4 and
14 − 10 = 4.0; headroom 1.0; outer 98.8 × 68.8 × 34.0). The sketch satisfies every gate and every L3.
All catalogue ids load and pass the import gate (`parts.gate`). L1 count 13 (limit 8-14); L2 48, L3 68
with weights 24 / 30 / 14, as section 6 says.

| # | Finding | Fix |
|---|---|---|
| 1 | The request said the fan "sits on the lid", which a reader takes as outside the lid. The judge (A1, F2, L2.6.1) needs it on the underside, inside, blowing down. | `design.json` request now says "fixed to the underside of the lid, inside the box, and blows down into it through an opening in the lid". |
| 2 | "Keep the fan intake at least 5 mm from the nearest tall component" was graded as frame-to-every-part (A2, L2.6.4) without saying so. | Request now states the reading: "its frame stays at least 5 mm clear of every part on the board". |
| 3 | Screw type and length were hidden. `bolt_m3_iso4762` takes `length` from the request, and "M3 screws" also matches `screw_m3_selftap` (a tie in `lookup`). F7's stock lengths 6-20 were only in this file. | Request now names ISO 4762 M3 socket-head screws and the stock lengths 6, 8, 10, 12, 14, 16, 20 mm. |
| 4 | Judge-needed numbers appeared only in L2/L3: standoff height 4-10, pilot depth 5 and engagement 4.0 (L1.3), fan screw engagement 3.0 and skin 0.8 (L1.6), lid plate 4.8-6.0, lip engagement 2-3 and lid height 9.0 (L1.8), tilt 5 degrees (L1.11). | Added to the matching L1 texts in `design.json`. |
| 5 | Standoff and boss OD lower bound 6.0 was not derivable: pilot Ø2.5 plus 2 × `standoff_wall_min` 1.6 gives 5.7. | L2.3.2, L3.3.2.1, L2.8.3, L3.8.3.2 now use 5.7 (the sketch's 6.0 still passes). |
| 6 | L3.6.5.1 upper limit 1154 mm² was below the area of V-BORE grown 0.2 (π × 19.2² = 1158). | Limit set to 1158. |
| 7 | Fan pilots 4.0 deep gave engagement 4.0 = pilot depth, no spare thread length. | Sketch pilots now 4.2 deep (skin 0.8, still within L3.6.2.2). |
| 8 | Hidden numbers that stay in the generic rules or the catalogue (opening oversize 1.5, plug clearance 0.3, 0.5 board clearance, 4.0 solder side, sliding fit 0.15-0.35, ligament 1.5, overhang rules, hole Ø3.4 and tap Ø2.5, plug overmold Ø11.0) were checked against `design_rules.json` and the part files and agree with them. | None needed. |

Open and recorded, not fixable here: the jack terminal positions are the least certain catalogue
values (A5); the enclosure does not use them. Thermal performance is not simulated (A3).

