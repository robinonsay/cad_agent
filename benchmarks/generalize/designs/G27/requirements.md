# G27 LM8UU linear bearing carriage: requirements (L1 / L2 / L3)

A training design of the generalisation set (`benchmarks/generalize/designs/G27`). The
machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file. It is
modelled on `benchmarks/enclosure/requirements.md` (E1-01): same tree, same two interference checks,
same grading classes, with a tie-path envelope and a nut-pocket check added. The agent sees only the
request text and the parts catalogue (`benchmarks/generalize/parts/*/part.json`); never this file.

**Brief (plan.json G27):** "A carriage block carrying one LM8UU linear bearing (8 x 15 x 24 mm) on an
8 mm smooth rod, with a flat top plate 40 x 30 mm with four M3 holes on a 30 x 20 mm pattern. The
bearing is retained by a zip-tie groove and a 0.1 mm press. The rod must slide through with the
bearing seated, no touching the block."

**How to read this.** L1 says what the owner needs; L2 turns it into an engineering requirement with
numbers; L3 is a concrete check on the delivered geometry. Every row has a method, a pass/fail
criterion with a tolerance, a weight (3 critical, 2 major, 1 minor) and a gate mark where a failure
makes the design WRONG. Every number that comes from an assumption (section 3) is provisional. Do
not relax a criterion because the agent fails it.

---

## 1. Frames, tolerances and the generic checks

### 1.1 Frames

- **Carriage frame:** Z up with the plate's flat top face normal to +Z; the rod axis (the bearing
  axis) along **Y**, parallel to the plate's 30 mm side; X across the plate's 40 mm side, origin at
  the bearing axis' X (so the plate spans X −20 to +20); Y from the plate's min-Y edge (Y 0 to 30);
  Z = 0 on the bearing axis. A design delivered rotated or mirrored is normalised into this frame
  (rotations by multiples of 90° and mirroring only): the plate is the broad flat body carrying the
  four Ø3.4 holes, its top face is the face the holes' heads would sit on.
- **Part frames:** those of the catalogue part files placed at the declared pose: `lm8uu` (axis
  along Z of the part, origin at the centre of face A; the pose maps part Z to carriage Y),
  `rod_8mm` (axis along its Z, mapped to carriage Y), `nut_m3`, `bolt_m3_iso4762`.

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

- the bearing's outer ring in the bore (radial gap 0 to 0.15, which is the press) and its face A on
  the shoulder;
- the rod inside the bearing's bore (the printed block never touches the rod);
- a zip tie (V-TIE-j) lying in its groove on the groove floor;
- a nut on its pocket floor and walls, and an M3 screw in its hole and through its nut.

---

## 2. Reference models, envelopes and datums

### 2.1 Reference models (M-)

| Name | What | Source | Size and datums (part frame, mm) |
|---|---|---|---|
| **M-LM8UU** | the linear bearing | `lm8uu` | Ø15.0 × 24.0, bore Ø8.0; `AXIS`, `HOUSING_BORE` (Ø15.1 = 15.0 + housing allowance 0.1), `FACE_A` (Z 0), `FACE_B` (Z 24), `CENTRE`; retaining-ring groove datums (not used). |
| **M-ROD** | the rod | `rod_8mm` (length 200, test length) | Ø8.0 × 200 on `AXIS`, centred on the bearing. |
| **M-NUT-k** | M3 hex nut | `nut_m3` | across flats 5.5, across corners 6.01, thickness 2.4; `pocket` keep-out Ø6.41 × 2.6; insertion height 3.4. Four, one per hole. |
| **M-BOLT-M3** | M3 screw | `bolt_m3_iso4762` | head Ø5.5 × 3.0, clearance Ø3.4; `tool_access` 25. Four, heads on the plate's top face. |
| **RA** | reference assembly | M-LM8UU ∪ M-ROD ∪ 4 × M-NUT ∪ 4 × M-BOLT-M3 at the declared poses | no printed geometry |

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-ROD** | the rod and its sweep | M-ROD: Ø8.0 cylinder, 200 long, on the bearing axis. |
| **V-BORE-OPEN** | the bearing's open core | Ø8.0 cylinder × 24 on the bearing axis (`bore_open` keep-out): nothing printed may enter it. |
| **V-BEARING-SEAT** | the pressed bearing | Ø15.0 × 24 on `AXIS` between `FACE_A` and `FACE_B` at the declared pose. |
| **V-TIE-j** (j = 1, 2) | a zip tie around the housing | annulus with inner radius = the measured median groove-floor radius, 1.2 thick radially, 3.0 wide axially, centred on groove j's axial centre, 360° around the bearing axis. |
| **V-HEAD-TOOL-k** | hex-key access to an M3 head | Ø5.5 cylinder from the plate's top face up 25 on hole axis k (the bolt's `tool_access`). |
| **V-NUT-INS-k** | nut insertion | Ø6.0 cylinder from the nut pocket's mouth on the plate's underside downward 3.4 on hole axis k (the nut's `insertion_height`). |
| **V-HOUSING-GAP** | free air round the housing | the region between the plate's underside and the housing, over the housing's tie span (computed). |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-LM8UU | units; Ø15 × 24, bore Ø8 | ± 0.1 |
| R2 | M-ROD | Ø8.0 × 200 | ± 0.05 |
| R3 | M-NUT | across flats 5.5, thickness 2.4 | ± 0.2 |
| R4 | RA | the bearing, rod and nuts do not collide with each other | intersection ≤ 0.01 mm³ |
| R5 | every V- envelope | its datums equal the model datums it came from | ≤ 0.01 |

**Seating rule.** The grader places M-LM8UU at the pose in `layout.json` (axis along Y). It
verifies: the bearing's axis is the printed bore's axis (offset ≤ 0.10, angle ≤ 0.3°), `FACE_A` is
within 0.10 of the shoulder, `FACE_B` is inside the open end by 0 to 1.0. If the declaration fails
the bearing is re-seated by fitting it into the printed bore against the shoulder, and every L3
that needed the declaration fails.

---

## 3. Assumptions and open questions

| # | Question | Value chosen | Uncertainty / why |
|---|---|---|---|
| A1 | Bearing size? | LM8UU 8 × 15 × 24 (the brief) | ISO 10285; the retaining-ring grooves (17.5 apart) are not used here: the ties clamp the housing instead. |
| A2 | What is "a 0.1 mm press"? | the housing bore is the bearing's outside diameter plus the catalogue allowance 0.1, so Ø15.1 ± 0.05; printed holes finish near 0.1 under their design size, which gives the light press, and the ties close the slit to preload it | ± 0.1 per printer (catalogue note); print a test ring. If the owner meant a diametral interference of 0.1 (bore 14.9), the bearing would not enter: the catalogue datum `HOUSING_BORE` wins (precedence rule). |
| A3 | Rod? | Ø8.0 h6 (0 / −0.009), any length; the grader tests with 200 mm | rod straightness is the rod's, not the block's. |
| A4 | What does "no touching the block" mean? | the printed block stays at least 1.0 from the rod everywhere, and nothing printed enters the bearing's Ø8 core | the bearing carries the rod; the block must not rub. |
| A5 | Zip ties? | 3.0 wide × 1.2 thick (a common 2.5-3.6 wide tie); each tie goes once round the housing in its groove | tie width 2.5-3.6 mm, thickness 1.0-1.4. |
| A6 | Shoulder size (inner-ring clear zone)? | the shoulder may bear only on the outer ring: its inner diameter ≥ 8.0 + (15.0 − 8.0) / 2 = 11.5 | the catalogue note ("outside bore_diameter + (outer_diameter − bore_diameter) / 4 radius") reads two ways, as a diameter 9.75 or as a radius that gives 11.5; the stricter, 11.5, is graded. ± 0.5. |
| A7 | Nut pocket? | across flats 5.6-6.0, across corners 6.11-6.9, depth 2.6-3.2; the nut cannot turn because the across-flats width stays below the nut's across corners (6.01) | catalogue: pocket keep-out Ø6.41 × 2.6, trap clearance 0.2; print conventions ± 0.1. |
| A8 | Plate thickness? | 4.0-6.0 | stiff enough for an M3 and the nut pocket (2.6-3.2 deep) plus a 1.5 web. |
| A9 | Load? | none graded (no cable pull, no payload) | the brief gives none. |
| A10 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed | typical FDM tolerances. |
| A11 | Size limit? | the block fits 45 × 35 × 35 (X × Y × Z) | the layout in section 7 is 40 × 30 × 28. |
| A12 | Which way does the rod run? | along the 30 mm side of the plate (Y) | the bearing is 24 long: it fits under 30 with 3 on each end; across the 40 side it would leave 8 on each end and nothing in the brief asks for it. |

---

## 4. Fixed decisions (a choice would otherwise be ambiguous)

| # | Decision | Why |
|---|---|---|
| F1 | One printed body: the plate, the bearing housing (a tube) and the webs that join them. | one carriage block. |
| F2 | The housing hangs below the plate's underside; the plate's top face is flat and free of features except the four holes. | the top plate takes a payload. |
| F3 | The M3 pattern is 30.0 along X and 20.0 along Y, centred on the plate. The nuts are captive in hex pockets in the plate's underside, so the screws go in from the top. | brief: "30 x 20 mm pattern"; capability `captive_nut`. |
| F4 | The housing is a tube joined to the plate only by two end webs (at its ends), so a zip tie can run in a groove all the way round it; the tube is split by one slit along its bottom so the ties can clamp it; one end carries a shoulder that the bearing's face A rests on. | one possible way to make "clamp preload with a tie in a groove" measurable; the L3s do not require this exact shape, only its effects. |
| F5 | Print orientation: the rod axis vertical (the bed normal within 5° of Y), the shoulder end down; stated in `layout.json`. | a vertical bore prints round, which the press fit needs. |
| F6 | `layout.json` declares the bearing pose (a rotation sending part Z to carriage Y, and the origin of face A), the four nut poses, the print orientation and the number of ties. | needed by the seating rule. |

---

## 5. Requirements tree

Columns: ID, requirement, method, pass/fail (with tolerance), weight, gate.

### L1.1 The bearing, rod and plate are laid out so the rod runs along the plate's 30 mm side, centred

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout (F6). | inspection | `layout.json` parses; names `lm8uu` with a pose and four `nut_m3` poses | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 | |
| L2.1.2 | The bearing axis runs along the plate's 30 mm side, centred across the 40 mm side. | inspection | axis within 1.0° of Y; axis X within 0.3 of the plate's X mid-line | 3 | |
| L3.1.2.1 | Axis direction. | inspection | ≤ 1.0° (+ 0.5° ε) | 3 | |
| L3.1.2.2 | Axis offset across the plate. | inspection | ≤ 0.3 | 2 | |
| L2.1.3 | The housing lies under the plate along the bearing's length. | inspection | plate Y range 0-30 covers the housing's Y range; housing Z range below the plate underside | 2 | |
| L3.1.3.1 | Housing under the plate. | inspection | true | 2 | |

### L1.2 The bearing seats in its bore with a 0.1 mm press and the inner ring stays free

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The bore is a round Ø15.1 hole the bearing presses into (A2). | inspection | largest inscribed circle at mid-depth Ø15.1 ± 0.05; roundness (max − min radius at three slices) ≤ 0.10; straight along its length ≤ 0.10 | 3 | G2 |
| L3.2.1.1 | Bore diameter. | inspection | Ø in [15.05, 15.15] | 3 | G2 |
| L3.2.1.2 | Roundness and straightness. | inspection | ≤ 0.10 and ≤ 0.10 | 2 | |
| L2.2.2 | The bearing sits in it: radial gap all round and axial seat. | analysis | radial gap between `V-BEARING-SEAT` and the bore wall in [0.00, 0.15] all round (a printed contact is the designed press); `FACE_A` within 0.10 of the shoulder; `FACE_B` inside the open end face by 0 to 1.0 | 3 | G2 |
| L3.2.2.1 | Radial gap. | analysis | in [0.00, 0.15] over ≥ 90 % of the circumference; no penetration above 0.01 mm³ except the press contact (gap ≥ −0.05) | 3 | G2 |
| L3.2.2.2 | Axial seat and end margin. | analysis | `FACE_A` gap ≤ 0.10; `FACE_B` depth in [0, 1.0] | 3 | |
| L2.2.3 | One shoulder stops the bearing and bears on the outer ring only. | inspection | shoulder inner Ø in [11.5, 13.5]; shoulder axial thickness ≥ 1.0 | 2 | |
| L3.2.3.1 | Shoulder diameter and thickness. | inspection | as L2.2.3 | 2 | |
| L2.2.4 | Nothing printed enters the bearing's Ø8 core. | analysis | clear_of(BODY, V-BORE-OPEN, 0.0) | 3 | |
| L3.2.4.1 | Core clear. | analysis | d ≥ 0.0 | 3 | |

### L1.3 Zip ties in grooves clamp the housing round the bearing

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Two grooves round the housing, over the bearing's length. | inspection | count 2; axial width 3.2-4.0; depth (land radius − floor radius) ≥ 1.0; each centre ≥ 2.0 inside the bearing's faces; centres ≥ 8.0 apart | 2 | |
| L3.3.1.1 | Groove count and positions. | inspection | 2; centres in [FACE_A + 2.0, FACE_B − 2.0]; distance ≥ 8.0 | 2 | |
| L3.3.1.2 | Groove width and depth. | inspection | width in [3.2, 4.0]; depth ≥ 1.0 | 2 | |
| L3.3.1.3 | Wall under the groove floor. | inspection | floor radius − bore radius ≥ 1.6 (i.e. floor radius ≥ 9.15) | 3 | |
| L2.3.2 | The tie can run all the way round in each groove. | analysis | clear_of(BODY, V-TIE-1 ∪ V-TIE-2, 0.0) (360°, including under the plate) | 3 | G5 |
| L3.3.2.1 | Tie envelope clear. | analysis | d ≥ 0.0 for both | 3 | G5 |
| L2.3.3 | One slit along the bottom lets the ties clamp the bearing. | inspection | exactly 1 slit through the housing wall; width 1.0-2.0; length ≥ housing length − 1.0; within 5° of straight down | 2 | |
| L3.3.3.1 | Slit count, width, length, direction. | inspection | as L2.3.3 | 2 | |
| L2.3.4 | Physical: with the ties on, the bearing resists a 10 N axial push. | test | no movement | 2 | physical, optional |
| L3.3.4.1 | Physical retention. | test | holds | 2 | physical, optional |

### L1.4 The rod slides through with the bearing seated and does not touch the block

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The block stays away from the rod. | analysis | clear_of(BODY, V-ROD, 1.0) | 3 | G3 |
| L3.4.1.1 | Rod clearance. | analysis | d ≥ 1.0 | 3 | G3 |
| L2.4.2 | The bore is coaxial with the declared bearing and parallel to the plate. | inspection | bore axis within 0.10 of the declared bearing axis; angle between bore axis and the plate's top face plane ≤ 0.5° | 3 | |
| L3.4.2.1 | Axis offset and angle. | inspection | ≤ 0.10; ≤ 0.5° | 3 | |
| L2.4.3 | Both ends of the core are open for the rod. | test | a probe line along the axis, radius ≤ 5.0 (Ø10), from −Y to +Y hits no printed surface | 2 | |
| L3.4.3.1 | Open core. | test | no hit | 2 | |
| L2.4.4 | The axial tolerance stack leaves the bearing seated. | analysis | bore length from the shoulder to the open end face in [24.0, 25.0] | 2 | |
| L3.4.4.1 | Bore length. | inspection | in [24.0, 25.0] | 2 | |

### L1.5 The flat top plate is 40 × 30 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Plate outline 40 × 30. | inspection | X 40.0 ± 0.2, Y 30.0 ± 0.2 | 3 | |
| L3.5.1.1 | Plate outline. | inspection | within ± 0.2 | 3 | |
| L2.5.2 | Plate thickness 4.0-6.0. | inspection | median in [4.0, 6.0] | 2 | |
| L3.5.2.1 | Plate thickness. | inspection | in range | 2 | |
| L2.5.3 | The top face is flat and parallel to the rod. | inspection | flatness ≤ 0.2 over the face outside the four holes; angle to the bearing axis ≤ 0.5° | 2 | |
| L3.5.3.1 | Top-face flatness. | inspection | ≤ 0.2 | 2 | |
| L3.5.3.2 | Top face parallel to the rod. | inspection | ≤ 0.5° | 2 | |
| L2.5.4 | The webs carry the housing. | analysis | each of the two webs' cross-section (slice normal to Y at its mid-length) ≥ 30 mm² | 2 | |
| L3.5.4.1 | Web area. | analysis | ≥ 30 mm² each | 2 | |

### L1.6 Four M3 holes on a 30 × 20 mm pattern

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Four Ø3.4 plain holes through the plate on a 30.0 × 20.0 rectangle, centred. | inspection | count 4; Ø3.4 ± 0.15 (inscribed); pattern 30.0 ± 0.15 (X) × 20.0 ± 0.15 (Y); pattern centre within 0.3 of the plate's centre | 3 | G4 |
| L3.6.1.1 | Hole count and diameter. | inspection | 4; Ø in [3.25, 3.55] | 3 | G4 |
| L3.6.1.2 | Pattern dimensions. | inspection | 30.0 ± 0.15; 20.0 ± 0.15 | 3 | |
| L3.6.1.3 | Pattern centring. | inspection | offset ≤ 0.3 | 2 | |
| L2.6.2 | Material round each hole. | analysis | ≥ 2.0 from every hole to the plate's edges and to other features | 2 | |
| L3.6.2.1 | Edge distances. | analysis | ≥ 2.0 | 2 | |
| L2.6.3 | Hex-key access above each screw head. | analysis | clear_of(BODY, V-HEAD-TOOL-1..4, 0.0) | 1 | |
| L3.6.3.1 | Tool columns clear. | analysis | d ≥ 0.0 | 1 | |

### L1.7 M3 nuts are captive in pockets on the plate's underside

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Four hex pockets, coaxial with the holes, that stop the nut turning. | inspection | count 4; axis within 0.15 of the hole axis; across flats (min width of the pocket's section) in [5.6, 6.0]; across corners (max width) in [6.11, 6.9]; depth in [2.6, 3.2]; web above the pocket ≥ 1.5 | 3 | |
| L3.7.1.1 | Pocket count and coaxiality. | inspection | 4; ≤ 0.15 | 3 | |
| L3.7.1.2 | Pocket width across flats and across corners. | inspection | [5.6, 6.0] and [6.11, 6.9] (the nut cannot turn: 6.0 < 6.01) | 3 | |
| L3.7.1.3 | Pocket depth and web. | inspection | depth in [2.6, 3.2]; web ≥ 1.5 | 2 | |
| L2.7.2 | A nut can be put in from below. | test | clear_of(BODY, V-NUT-INS-1..4, 0.0) | 2 | |
| L3.7.2.1 | Insertion columns clear. | test | d ≥ 0.0 | 2 | |

### L1.8 It prints on an FDM printer without supports, with a round bore

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The rod axis is vertical in the print orientation (F5). | inspection | angle between the declared bed normal and Y ≤ 5.0° | 2 | |
| L3.8.1.1 | Orientation angle. | inspection | ≤ 5.0° | 2 | |
| L2.8.2 | No unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12 and bridges ≤ 15.0. | analysis | 0 offending faces of area > 1 mm² | 2 | |
| L3.8.2.1 | Overhang and bridge scan. | analysis | as L2.8.2 | 2 | |
| L2.8.3 | The body rests on a face large enough to stand on. | analysis | bed contact ≥ 300 mm² and ≥ 30 % of the plan bounding box | 1 | |
| L3.8.3.1 | Bed contact. | analysis | as L2.8.3 | 1 | |
| L2.8.4 | No feature thinner than 0.8; the body fits a 200 × 200 × 200 bed. | analysis | min thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 | |
| L3.8.4.1 | Thin features. | analysis | ≥ 0.8 | 1 | |
| L3.8.4.2 | Bounding box. | inspection | ≤ 200 per axis | 1 | |

### L1.9 It is one clean printable solid of reasonable size

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The mesh is manifold and one shell. | analysis | 1 shell; manifold3d accepts it; no fragment | 3 | G1 |
| L3.9.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.9.2 | Size (A11). | inspection | X ≤ 45.0, Y ≤ 35.0, Z ≤ 35.0 | 1 | |
| L3.9.2.1 | Bounding box. | inspection | as L2.9.2 | 1 | |

### L1.10 The package says what was built and where, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | The package holds `carriage.stl` (carriage frame, mm), the OpenSCAD source, `layout.json` (F6) and the agent's own report of the checks above. | inspection | all present and readable | 3 | G0 |
| L3.10.1.1 | Files present and parse; the body's largest bounding-box axis in 20-200 mm. | inspection | true | 3 | G0 |
| L3.10.1.2 | The declared bearing pose verifies under the seating rule (section 2.3). | analysis | axis offset ≤ 0.10, angle ≤ 0.3°; face A ≤ 0.10; face B depth in [0, 1.0] | 3 | |
| L2.10.2 | The agent's own report agrees with the judge. | analysis | for every `clear_of` / `inside` L3 the agent reports: same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 | |
| L3.10.2.1 | Self-report vs judge. | analysis | 100 % agreement within 0.10 | 1 | |

---

## 6. Counts and gates

| Level | Count |
|---|---|
| L1 | 10 |
| L2 | 32 |
| L3 | 44 (weight 3: 18, weight 2: 20, weight 1: 6; 1 physical or human, optional) |

Every L3 is a measurement a Python script can make on the delivered STL (or on the declared
`layout.json` against the catalogue), except the rows marked physical or human.

Gates (a failure makes a design WRONG regardless of score): see section 9.

---

## 7. Feasibility

One design exists that meets every L3 above (carriage frame, mm; bearing axis on the line X 0, Z 0):

- **Plate:** X −20 to 20, Y 0 to 30, Z 12.5 to 17.5 (5.0 thick, top face at Z 17.5, flat). Holes Ø3.4 at
  (±15, 5) and (±15, 25): 30.0 × 20.0, centred (Y 15), 5 from each edge (≥ 2.0).
- **Housing:** a tube about the Y axis, Y 0.0 to 26.0 (26 long, flush with the plate's Y = 0 edge),
  outer Ø21.0 (land radius 10.5), bore Ø15.1 from Y 1.2 to 26.0 (24.8 long: in [24.0, 25.0]); a
  shoulder Y 0.0-1.2 (1.2 thick) with inner Ø12.0 (≥ 11.5). The bearing sits at Y 1.2-25.2 against
  the shoulder; face B is 0.8 inside the open end (in [0, 1.0]); radial gap (15.1 − 15.0) / 2 =
  0.05. The tube's top (Z 10.5) is 2.0 below the plate's underside (Z 12.5).
- **Webs:** two, Y 0.0-3.0 and Y 23.0-26.0, X −6 to 6, from the tube up to the plate's underside:
  cross-section about 12 × 3 ≈ 40 mm² ≥ 30; they join tube and plate. Between them (Y 3.0-23.0) the
  housing is free of the plate.
- **Ties:** two grooves, axial centres Y 8.0 and Y 19.0 (width 3.2: Y 6.4-9.6 and 17.4-20.6), floor
  radius 9.3 (depth 10.5 − 9.3 = 1.2 ≥ 1.0; wall under the floor 9.3 − 7.55 = 1.75 ≥ 1.6), 360°
  round. Centres are 6.8 and 6.2 inside the bearing's faces (≥ 2.0) and 11.0 apart (≥ 8.0). The
  tie envelope (inner radius 9.3, to 10.5, 3.0 wide) lies below the plate's underside (Z 12.5), so it
  is free all the way round.
- **Slit:** 1.5 wide along the bottom (−Z), Y 0.0 to 26.0 (the whole length).
- **Nut pockets:** hex, across flats 5.7, across corners 6.58, depth 2.8 (web 5.0 − 2.8 = 2.2 ≥ 1.5), in
  the underside at the four holes, coaxial. The nut cannot turn (5.7 < 6.01). Insertion columns Ø6.0
  below the underside at X ±15 have their inner edge at |X| 12.0, outside the tube (|X| ≤ 10.5).
- **Rod:** Ø8 through the bearing; the shoulder's Ø12.0 hole leaves 2.0 round it (≥ 1.0); the core is
  open at both ends.
- **Printing:** bed normal along Y, the Y = 0 face down. That face is the plate's end (40 × 5 = 200
  mm²), the shoulder ring (π (10.5² − 6.0²) ≈ 233 mm², less the slit) and the web's foot: about
  460 mm² against a plan bounding box 40 × 28 = 1120 (41 %). The bore and the grooves are vertical
  rings (no overhang); the tube above the gap stands on its own lower rings; the second web starts
  at Y 23 as a 2.0 bridge between the tube and the plate; the nut pockets are hex holes with
  horizontal axes, 5.7 across (a bridge ≤ 15.0); the Ø3.4 holes likewise.
- **Size:** 40 × 30 × 28 (limit 45 × 35 × 35).

This sketch is one satisfiable design; it is not the only one and is never given to the agent.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 (`design.json`) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1-L2.1.3 | L3.1.1.1, L3.1.2.1-2, L3.1.3.1 | L1.1 | inspection | "carriage block carrying one LM8UU on an 8 mm rod" |
| L1.2 | Bearing seat and press | L2.2.1-L2.2.4 | L3.2.1.1-2, L3.2.2.1-2, L3.2.3.1, L3.2.4.1 | L1.2 | inspection | "0.1 mm press", "8 x 15 x 24 mm" |
| L1.3 | Tie clamp | L2.3.1-L2.3.4 | L3.3.1.1-3, L3.3.2.1, L3.3.3.1, L3.3.4.1 | L1.3 | analysis | "retained by a zip-tie groove" |
| L1.4 | Rod slides | L2.4.1-L2.4.4 | L3.4.1.1, L3.4.2.1, L3.4.3.1, L3.4.4.1 | L1.4 | analysis | "rod must slide through ... no touching the block" |
| L1.5 | Plate | L2.5.1-L2.5.4 | L3.5.1.1, L3.5.2.1, L3.5.3.1-2, L3.5.4.1 | L1.5 | inspection | "flat top plate 40 x 30 mm" |
| L1.6 | M3 pattern | L2.6.1-L2.6.3 | L3.6.1.1-3, L3.6.2.1, L3.6.3.1 | L1.6 | inspection | "four M3 holes on a 30 x 20 mm pattern" |
| L1.7 | Captive nuts | L2.7.1-L2.7.2 | L3.7.1.1-3, L3.7.2.1 | L1.7 | inspection | "M3 nuts captive" (added: capability) |
| L1.8 | Printable | L2.8.1-L2.8.4 | L3.8.1.1, L3.8.2.1, L3.8.3.1, L3.8.4.1-2 | L1.8 | analysis | "printed on an FDM printer" |
| L1.9 | Clean solid | L2.9.1-L2.9.2 | L3.9.1.1, L3.9.2.1 | L1.9 | analysis | "one printed part" |
| L1.10 | Evidence | L2.10.1-L2.10.2 | L3.10.1.1-2, L3.10.2.1 | L1.10 | inspection | needed by the judge |

## 9. Grading procedure for G27

`benchmarks/generalize/rubric.md` did not exist when this file was written, so this section is the design-specific rubric (units, frames, recipes, classes, defect reports). If a generic rubric.md appears later it governs generic rules; this section still governs everything specific to G27.

1. **Package gate (G0).** The files of the last L1 must exist and load. If a delivered STL is
   missing or unreadable, stop: verdict DOES NOT MEET, one defect on the G0 L3.
2. **Units.** Load each STL; the largest bounding-box axis of carriage.stl must be 20-200 mm
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

Gates: G0 package (L3.10.1.1); G1 manifold and one shell (L3.9.1.1); G2 bearing seated in its bore (L3.2.1.1, L3.2.2.1); G3 the rod slides through without touching the block (L3.4.1.1); G4 the M3 pattern (L3.6.1.1); G5 the zip-tie path is free all round (L3.3.2.1).

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

Adversarial audit of this entry, 2026-10-24. Recomputed from `lm8uu`, `rod_8mm`, `nut_m3` and the
section 7 sketch: bore 15.0 + 0.1 = 15.1, radial gap 0.05; bore length 26.0 − 1.2 = 24.8 in [24, 25];
face B 0.8 inside the open end; groove floor 9.3 gives wall 9.3 − 7.55 = 1.75 and depth 10.5 − 9.3 = 1.2;
tie envelope top at radius 10.5 against the plate underside at 12.5; nut pocket across flats 5.7 gives
across corners 5.7 / cos 30 = 6.58 (inside 6.11-6.9, and 5.7 < 6.01 so the nut cannot turn); web above the
pocket 5.0 − 2.8 = 2.2; bed contact about 460 mm² = 41 % of 40 × 28; size 40 × 30 × 28. The sketch satisfies
every gate and L3. All catalogue ids load. L1 count 10; L2 32, L3 44 with weights 18 / 20 / 6.

| # | Finding | Fix |
|---|---|---|
| 1 | `rod_8mm` takes `length` from the request, which gave none (the judge used 200 mm, hidden). | Request now says "200 mm long". |
| 2 | `bolt_m3_iso4762` takes `length` from the request, which named no screw, and "M3" also matches `screw_m3_selftap`. | Request now says "ISO 4762 M3 socket-head screws, 10 mm long". |
| 3 | The zip tie (3.0 x 1.2, A5) sets V-TIE and the groove limits, but was not in the request or L1. | In the request and L1.3. |
| 4 | "A 0.1 mm press fit" can mean 0.1 mm interference (bore 14.9), which the bearing cannot enter; the judge uses the catalogue's housing bore 15.1 (A2). | Request now says the bore is the 15 mm outside diameter plus the usual 0.1 mm printing allowance, since printed holes come out about that much small. |
| 5 | The housing below the plate (F2) was implied only. | Request and L1.1 now say it hangs below the plate with the top face flat. |
| 6 | Judge-needed numbers appeared only in L2/L3: groove centres 2.0 inside the faces and 8.0 apart, slit 1.0-2.0 wide and nearly full length (L1.3), bed contact 30 % (L1.8). | Added to the matching L1 texts in `design.json`. |

Observation: the nut pockets leave 1.7 mm from the pocket corner to the plate edge (5 − 3.29); no L3 limits
it (L2.6.2 covers the holes only) and it is above the 0.8 minimum feature.
