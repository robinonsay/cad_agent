# G32 NEMA17 pulley belt guard: requirements (L1 / L2 / L3)

Training design of the generalisation set (family housing_assembly; capabilities belt_geometry, keepout_clearance,
rotation_clearance, multi_body_assembly, bolt_pattern). The machine-readable request (L1 only, `dev.json` format) is
`design.json` next to this file. It is modelled on `benchmarks/enclosure/requirements.md` (E1-01) and uses the same
conventions: tolerances (1.2), `clear_of` and designed contact (1.3), reference models and envelopes (2), assumptions with
uncertainty and fixed decisions (3), a tree whose every L3 is measured by Python on the delivered STL (4), gates (5), a
feasibility sketch (7) and traceability (8).

**Brief (plan.json, verbatim):** "A guard housing over a 20 tooth GT2 pulley (16 mm tooth OD) on a NEMA 17 shaft. The guard
must clear the pulley by 2 mm all around while leaving a slot for the 6 mm belt on one side. Fasten it with two of the
motor's M3 face holes on the 31 mm pattern."

**Rubric note.** The generic file `benchmarks/generalize/rubric.md` did not exist when this entry was written, so
section 6 below is the design-specific rubric (recipes, classes, how to report where a defect is). If the generic
rubric appears later it applies on top of this file; where they disagree the numbers in this file win.

**How to read the tree.** L1 is what the owner needs, L2 an engineering requirement, L3 a check on the geometry. Each
L3 has a method (inspection, analysis, demonstration, test, human; as in `design.json`), a pass/fail criterion with a
number and tolerance, a weight (3 critical, 2 major, 1 minor) and a gate mark (G0..G4) on must-pass rows. Numbers that
come from an assumption (section 3) are provisional until the owner confirms them. Never relax a criterion because the
agent fails it.

---

## 1. Frames, tolerances, designed contact

### 1.1 Frame

- **Motor frame** (catalogue `nema17_motor`): Z along the shaft axis, origin on the motor mounting face at the shaft axis,
  motor body toward −Z, pilot and shaft toward +Z. The belt leaves toward **+X**. The guard is delivered in this frame
  (assembly pose). The grader normalises a design delivered rotated by multiples of 90° about Z or mirrored so that the
  belt slot is on +X; never penalised.
- Motor hole axes (catalogue `HOLE`): (±15.5, ±15.5), direction −Z, Ø3.0, thread depth 4.5.
- Lengths in mm, angles in degrees.

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered mesh, never by eye.

| Quantity | ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm | a value passes if it meets the limit within ε |
| angle | 0.5° | same |
| intersection volume | 0.01 mm³ | "no interference" means ≤ 0.01 mm³ |
| hole / bore diameter | largest inscribed circle of the section | what a bolt or pin sees |

### 1.3 Interference checks and designed contact

- **`clear_of(bodies, volume, c)`**: minimum distance between the guard and `volume` is ≥ c − ε, penetration ≤ 0.01 mm³.
- **`inside(volume, void, c)`**: `volume` lies in `void` with every point ≥ c − ε from the boundary.

The guard is the only printed body. The motor, pulley, belt and bolts are reference models built by the grader from the
catalogue and the declared layout; the agent's copies are not trusted for grading.

**Designed contact for this design (never interference; only penetration > 0.01 mm³ counts for these pairs):**
1. the guard underside (shell and ears) lying on the motor mounting face (Z = 0),
2. an M3 bolt shank in its clearance hole and in the motor thread; a bolt head on the ear top,
3. the motor pilot in the guard bore (radial gap 0.15 to 0.35 by L2.5.2; a gap is not contact, but contact would be allowed).

A distance of zero is a pass for these pairs.

---

## 2. Reference models, envelopes, datums

### 2.1 Reference models (M-)

Built from the catalogue (`benchmarks/generalize/parts/<part>/part.json`) at the pose declared in `layout.json`.

| Name | What | Source | Size and datums used |
|---|---|---|---|
| **M-MOTOR** | NEMA 17 motor | `nema17_motor` | body 42.3 × 42.3 × 40.0 below Z = 0; pilot Ø22.0 × 2.0 above the face; shaft Ø5.0 × 24.0; `FACE` (Z = 0), `SHAFT_AXIS`, `PILOT_AXIS`, `HOLE` (4 axes), `SHAFT_TIP` (0, 0, 24), screw-head keep-out Ø5.5 |
| **M-PULLEY** | 20-tooth GT2 pulley | `gt2_pulley_20t` | hub Ø16.0 × 8.0, lower flange Ø18.0 × 1.0, teeth Ø16.0 × 7.0, upper flange Ø18.0 × 1.0; total 17.0; hub entry plane at Z = 3.0 (A1); `rotation_envelope` Ø18.0 × 17.0; `BELT_PLANE` at Z = 15.5; band Z 12.0 to 19.0 |
| **M-BELT** | GT2 belt, 6 mm wide | `gt2_belt_6mm` | width 6.0, thickness 1.38, tooth height 0.75; two straight runs of length 100.0 (request) |
| **M-BOLT3-j** (j = 1, 2) | M3 socket bolt | `bolt_m3_iso4762` | thread Ø3.0, head Ø5.5 × 3.0, clearance Ø3.4; length declared in `layout.json` (stock 6, 8, 10, 12) |

### 2.2 Envelopes (V-) and computed volumes

| Name | Definition | Used by |
|---|---|---|
| **V-ROT** | the rotating parts: pulley `rotation_envelope` (Ø18.0, Z 3.0 to 20.0) ∪ shaft Ø5.0 from the face to Z 24.0 | L2.2.1 |
| **V-BELT-ZONE** | the wrapped belt: cylinder Ø17.26 (= 2 × R_b, R_b = 8.0 + (1.38 − 0.75) = 8.63, A2) from Z 12.5 to 18.5 | L2.2.2 |
| **V-BELT-RUNS** | the two straight belt runs leaving tangentially along +X: boxes X 0 to 100.0, |Y| 7.25 to 8.63 (outer face at R_b, thickness 1.38), Z 12.5 to 18.5 | L2.3.1, L2.3.2 |
| **V-DRIVER-j** | Ø6.0 column on the axis of bolt j from the head top (Z = ear top + 3.0) along +Z, 50 long | L2.4.3 |
| **V-SWEEP** | the guard translated along +Z by 60 (the removal path) | L2.7.1 |
| **V-SHELL-IN** | the guard's internal void: the connected component of (convex hull of GUARD) − GUARD containing the shaft axis point at Z 10 | L2.2.1, L2.6.1 |
| **V-AP-BELT** | the opening(s) actually present in the +X side of the shell: the slab between its inner and outer faces minus GUARD, regions larger than 1 mm³ | L2.3.1 to L2.3.3 |

### 2.3 Sanity checks and seating rule

| ID | Check | Pass |
|---|---|---|
| R1 | M-MOTOR bounding box | 42.3 × 42.3 × 64.0 ± 0.2 (body + shaft) |
| R2 | M-PULLEY total length and flange Ø | 17.0 ± 0.2; 18.0 ± 0.2 |
| R3 | M-MOTOR hole pattern | 31.0 ± 0.1, Ø3.0 ± 0.1 |
| R4 | V-BELT-RUNS tangent to V-BELT-ZONE | outer face at R_b ± 0.01 |

**Seating rule.** M-PULLEY is placed with the hub entry plane at the declared Z (A1); M-BOLT3-j on the axes of the two used
motor holes. The grader verifies the declaration: the guard's two bolt holes are coaxial with two distinct motor `HOLE` axes
(residual ≤ 0.25) and the guard underside lies on `FACE` (distance ≤ 0.10). If the declaration is missing or fails the
grader seats the guard by fitting its bore to `PILOT_AXIS` and its two holes to the nearest `HOLE` axes.

---

## 3. Assumptions, fixed decisions and open questions for the owner

Each line gives the value chosen and why. All derived from the brief, the catalogue or convention; none asked.

| # | Question | Value chosen | Why and uncertainty |
|---|---|---|---|
| A1 | Where does the pulley sit on the shaft? | Hub entry plane 3.0 above the motor face (±1.0): the pilot is 2.0 high, plus 1.0 clearance. Pulley top Z = 20.0; the shaft tip at Z 24.0 stands 4.0 above the pulley. | The brief gives no height. `nema17_motor` and `gt2_pulley_20t` part.json (hub 8.0, flange 1.0, teeth 7.0 assumed ±1). The request carries the 3 mm. |
| A2 | Belt envelope? | The catalogue tooth OD 16.0 is taken as given (it does not agree with a real 20T GT2 pitch diameter of 12.73; part.json gives both). The belt wraps with its back at R_b = tooth OD / 2 + (belt thickness − tooth height) = 8.0 + 0.63 = 8.63. Two straight runs leave tangentially along +X, |Y| from R_b − 1.38 = 7.25 to 8.63, Z 12.5 to 18.5 (belt width 6.0 centred on `BELT_PLANE`), length 100.0 to a second pulley. Belt clearance to the guard is at least 0.5. | Conservative envelope: the real belt is inside it. The 100 mm span is in the request. ±0.5 on the belt thickness. |
| A3 | What is "clear the pulley by 2 mm all around"? | Every point of the rotating parts (pulley flange envelope Ø18.0 × 17.0 and the shaft out to Z 24.0) is at least 2.0 from every point of the guard, and at most 3.0 laterally and 3.5 at the shaft tip (so the guard is not oversized). | "all around" read as sides, over the pulley and over the shaft tip. |
| A4 | Shaft flat and set screw? | Not modelled; the shaft cylinder is the envelope. | part.json notes (flat 0.5 deep). |
| A5 | Motor details? | 42.3 square, body 40.0 long, pilot Ø22.0 × 2.0, hole thread depth 4.5, corner chamfers ignored. The rear cable is not part of the guard. | part.json (datasheet 17HS4401). Thread depth is the maximum engagement; a longer bolt bottoms in the motor. |
| A6 | Bolts? | Two M3 socket-head bolts through clearance holes (Ø3.4) in the guard's ears into two of the four motor holes; any two distinct holes are accepted. Engagement = bolt length − ear thickness must be 3.0 to 4.5. | Brief: "two of the motor's M3 face holes". 3.0 = one thread diameter; 4.5 = motor thread depth. |
| A7 | Belt direction and belt fitting? | The belt leaves along +X (the request says "one side"); the guard is installed before the belt is slipped through the slot. | Typical. The grader mirrors X if needed. |
| A8 | Belt tension load on the guard? | None: the guard never touches the belt. | The 0.5 clearance keeps the belt free. |
| A9 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. Wall, cap 2.0 to 4.0 (rule `wall_default` 2.4). No face steeper than 45° from vertical; round holes Ø ≤ 12.0 and bridges ≤ 15.0 exempt. **Bed contact threshold for this design is 40 percent**, not 50, because the plan bounding box is dominated by the two ears. | design_rules.json values. The ears must reach the motor holes at 21.9 from the axis. |
| A10 | Size? | At most 45 × 45 × 35. | Compact guard; the sketch is 33.6 × 40.0 × 28.6. |
| A11 | Cable, label, ventilation? | None required. | Not in the brief. |

### Fixed decisions (one choice, no alternatives accepted)

| # | Decision | Why |
|---|---|---|
| FD1 | The guard is one printed body: a cylindrical shell open toward the motor, a flat cap on top, two ears at the motor face, ribs under the ears, and one belt slot on +X. | Single piece. |
| FD2 | The shell's bore is one straight bore from the motor face to the cap, and it locates on the motor pilot (bore Ø = pilot Ø + 2 × 0.15 to 0.35). | A locating fit gives the clearances coaxiality. |
| FD3 | The guard underside (shell and ears) is one plane on the motor face (Z = 0). | The pilot is 2.0 high; the guard sits on the face. |
| FD4 | Print pose: cap down on the bed (the assembly pose rotated 180° about X); ears at the top of the print on 45° ribs. The layout declares it. | A flat cap prints without a bridge over the bore. |
| FD5 | The belt slot is a single opening in the +X side of the shell whose **floor** (its lower edge in the assembly pose) is stepped by 45° corbels so that no flat bridge exceeds 15.0; its roof is flat and full width. | The two belt runs need a slot 18.3 or more wide. In the print pose (FD4, cap down) the assembly floor of the slot is the face that hangs over the opening, so the corbels belong on the floor; the roof prints as an upward face. |

---

## 4. Requirements tree

### L1.1 Placement from the catalogue and layout declared

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares the layout: pulley hub entry Z, belt direction and run length, the two used motor holes and bolt lengths, print pose. | inspection | `layout.json` present, parses, names the catalogue ids | 3 | |
| L3.1.1.1 | Layout parses and every catalogue id exists. | inspection | true | 3 | G0 |
| L2.1.2 | The pulley sits 3.0 above the face and fits the shaft. | inspection | hub entry Z = 3.0 ± 0.1; pulley top ≤ shaft tip Z (24.0) | 2 | |
| L3.1.2.1 | Hub entry height. | inspection | 2.9 ≤ Z ≤ 3.1 | 2 | |
| L3.1.2.2 | Pulley top vs shaft tip. | inspection | 20.0 ≤ 24.0 | 1 | |
| L2.1.3 | The reference models do not collide. | analysis | M-PULLEY ∩ M-MOTOR ≤ 0.01 mm³; pulley hub to the pilot top ≥ 0.5 | 3 | |
| L3.1.3.1 | Pulley / motor interference and gap. | analysis | ≤ 0.01 mm³; gap ≥ 0.5 | 3 | |

### L1.2 The guard clears the rotating parts by 2 mm all around

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Every point of V-ROT is at least 2.0 from the guard. | analysis | clear_of(GUARD, V-ROT, 2.0) | 3 | |
| L3.2.1.1 | Overall clearance to the rotating parts. | analysis | d ≥ 2.0, penetration ≤ 0.01 mm³ | 3 | G2 |
| L3.2.1.2 | Radial clearance to the flange envelope (bore radius − 9.0, min over Z 3.0 to 20.0). | analysis | 2.0 ≤ g ≤ 3.0 | 3 | G2 |
| L3.2.1.3 | Clearance over the shaft tip (inner cap Z − 24.0). | analysis | 2.0 ≤ g ≤ 3.5 | 3 | G2 |
| L3.2.1.4 | Clearance over the pulley top (inner cap Z − 20.0). | analysis | ≥ 2.0 | 2 | |
| L2.2.2 | The guard does not touch the wrapped belt. | analysis | clear_of(GUARD, V-BELT-ZONE, 0.5) | 2 | |
| L3.2.2.1 | Wrapped-belt zone clear. | analysis | d ≥ 0.5 | 2 | |

### L1.3 One slot on the belt side lets both belt runs out

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Exactly one opening in the shell, on +X. | inspection | V-AP-BELT has 1 connected region on the +X side; no other opening except the two bolt holes | 3 | |
| L3.3.1.1 | Belt-side opening count. | inspection | = 1 | 3 | |
| L3.3.1.2 | Both belt runs leave without touching the guard. | test | clear_of(GUARD, V-BELT-RUNS, 0.5) | 3 | |
| L3.3.1.3 | Belt-run envelope clear. | test | d ≥ 0.5, penetration ≤ 0.01 mm³ | 3 | G3 |
| L2.3.2 | The slot is sized from the belt, not oversized. | analysis | in the slot plane: width (Y) 18.3 to 22.0; height (Z) 7.0 to 9.0, bottom edge at Z 10.0 to 12.0; inside(V-AP-BELT, V-BELT-RUNS offset by 3.0, 0.0) | 2 | |
| L3.3.2.1 | Slot width and height (bounding box of V-AP-BELT in the wall plane). | inspection | width 18.3 to 22.0; height 7.0 to 9.0 | 2 | |
| L3.3.2.2 | Slot bottom edge height (the floor is stepped, so the slot is not centred on the belt plane). | inspection | 10.0 ≤ Z ≤ 12.0 | 2 | |
| L3.3.2.3 | Opening within the grown belt envelope. | analysis | d ≥ 0.0 | 2 | |
| L2.3.3 | Material round the slot. | analysis | ligament from the slot to the shell bottom edge and to the cap inner face ≥ 1.5 | 1 | |
| L3.3.3.1 | Slot ligament. | analysis | ≥ 1.5 | 1 | |

### L1.4 Fastened to two of the motor's M3 holes, bolts that engage and can be reached

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Exactly two clearance holes in the ears, each on a distinct motor hole axis. | inspection | count = 2; Ø 3.4 ± 0.1; axes within 0.25 of two distinct `HOLE` axes; axis within 1.0° of Z | 3 | |
| L3.4.1.1 | Bolt-hole count. | inspection | = 2 | 3 | G4 |
| L3.4.1.2 | Bolt-hole diameter. | inspection | 3.3 ≤ Ø ≤ 3.5 | 3 | G4 |
| L3.4.1.3 | Offset of each hole axis to its motor `HOLE` axis; the two holes use different axes. | analysis | ≤ 0.25 each; distinct | 3 | G4 |
| L3.4.1.4 | Hole axis direction. | inspection | ≤ 1.0° from Z | 2 | |
| L2.4.2 | The bolts engage the motor thread without bottoming and sit on the ears. | analysis | engagement = declared bolt length − ear thickness at the hole in [3.0, 4.5]; head Ø5.5 lies fully on the ear top (ear flat radius ≥ 2.75 round the hole) | 3 | |
| L3.4.2.1 | Thread engagement. | analysis | 3.0 ≤ e ≤ 4.5 | 3 | G4 |
| L3.4.2.2 | Head seat on the ear. | analysis | head footprint inside the ear top: 100 percent | 2 | |
| L2.4.3 | A screwdriver reaches each bolt with the pulley and shaft in place. | test | clear_of(GUARD ∪ M-PULLEY ∪ shaft, V-DRIVER-j, 0.0) | 2 | |
| L3.4.3.1 | Driver columns clear. | test | d ≥ 0.0 for both | 2 | |

### L1.5 The guard sits flat on the face, locates on the pilot, stays inside the outline

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The underside is one plane on the motor face. | analysis | lowest point Z ≥ −0.02; shell and ear undersides coplanar within 0.10 and within 0.10 of Z = 0 | 3 | |
| L3.5.1.1 | Underside seating on `FACE`. | analysis | 0 ≤ g ≤ 0.10; penetration of M-MOTOR ≤ 0.01 mm³ | 3 | G4 |
| L3.5.1.2 | Coplanarity of shell and ear undersides. | inspection | ≤ 0.10 | 2 | |
| L2.5.2 | The bore locates on the 22 mm pilot with a sliding fit. | analysis | bore Ø in [22.3, 22.7] (pilot Ø22.0 + 2 × 0.15 to 0.35); bore axis within 0.25 of `PILOT_AXIS`; pilot-to-bore gap 0.15 to 0.35 per side | 3 | |
| L3.5.2.1 | Bore diameter at the pilot (Z 0 to 2.0). | inspection | 22.3 ≤ Ø ≤ 22.7 | 3 | |
| L3.5.2.2 | Bore axis vs `PILOT_AXIS`. | analysis | ≤ 0.25 | 3 | |
| L3.5.2.3 | Radial gap pilot to bore. | analysis | 0.15 ≤ g ≤ 0.35 | 2 | |
| L2.5.3 | The plan footprint stays inside the motor face outline. | inspection | plan bounding box within X, Y ∈ [−21.15, 21.15] | 2 | |
| L3.5.3.1 | Plan bounding box vs the 42.3 square. | inspection | inside | 2 | |

### L1.6 Closed except the slot and the bolt holes; wall thicknesses

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | No unlisted openings. | analysis | no region admits a Ø2.0 sphere from outside into V-SHELL-IN other than the belt slot and the two bolt holes (the open motor end is closed by the motor face) | 2 | |
| L3.6.1.1 | Probe for unlisted openings (rays 1 mm over the hull faces; the motor-end annulus is excluded). | analysis | 0 unlisted paths | 2 | |
| L2.6.2 | Thicknesses. | inspection | shell wall and cap 2.0 to 4.0; ears 2.0 to 5.0 | 2 | |
| L3.6.2.1 | Shell wall thickness (median, away from the slot and ribs). | inspection | 2.0 ≤ t ≤ 4.0 | 2 | |
| L3.6.2.2 | Cap thickness. | inspection | 2.0 ≤ t ≤ 4.0 | 2 | |
| L3.6.2.3 | Ear thickness at the holes. | inspection | 2.0 ≤ t ≤ 5.0 | 2 | |
| L2.6.3 | The ears are fused to the shell. | analysis | one body; contact area of each ear web with the shell ≥ 30 mm² | 2 | |
| L3.6.3.1 | Ear-to-shell joint. | analysis | shells = 1; each ≥ 30 mm² | 2 | |

### L1.7 The guard goes on and off along the shaft axis

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Removal path: translating the guard 60 along +Z never touches the pulley, the shaft or the pilot. | test | clear_of(V-SWEEP, M-PULLEY ∪ shaft ∪ pilot, 0.15); the cap does not meet the shaft tip | 2 | |
| L3.7.1.1 | Removal sweep clear. | test | d ≥ 0.15 | 2 | |

### L1.8 One manifold body that prints without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | One manifold shell. | analysis | 1 shell; manifold3d accepts it | 3 | |
| L3.8.1.1 | Shell and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.8.2 | No unsupported overhang in the print pose (FD4). | analysis | 0 offending faces (area > 1 mm²); round holes Ø ≤ 12.0 and bridges ≤ 15.0 exempt | 2 | |
| L3.8.2.1 | Overhang and bridge scan (the flat slot floor span ≤ 15.0 with 45° corbels, ears on 45° ribs). | analysis | 0 patches | 2 | |
| L2.8.3 | It rests on a flat face. | analysis | bed contact ≥ 40 percent of the plan bounding box (A9) | 1 | |
| L3.8.3.1 | Bed-contact area. | analysis | ≥ 40 percent | 1 | |
| L2.8.4 | No thin features. | analysis | min local thickness ≥ 0.8 | 1 | |
| L3.8.4.1 | Thin-feature scan. | analysis | ≥ 0.8 | 1 | |
| L2.8.5 | It fits the bed. | inspection | bounding box ≤ 200 per axis | 1 | |
| L3.8.5.1 | Bounding box. | inspection | ≤ 200 | 1 | |

### L1.9 Size

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | Overall size. | inspection | X ≤ 45.0, Y ≤ 45.0, Z ≤ 35.0 | 1 | |
| L3.9.1.1 | Bounding box. | inspection | as L2.9.1 | 1 | |

### L1.10 The package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Package: `guard.stl` (assembly pose, motor frame, mm), the `.scad`, `layout.json` (L2.1.1 plus the print pose) and the agent's own report. | inspection | all present and readable | 3 | |
| L3.10.1.1 | Files parse; the STL is in mm (largest bounding-box axis 20 to 200). | inspection | true | 3 | G0 |
| L3.10.1.2 | Declared layout verifies under the seating rule (2.3). | analysis | hole residual ≤ 0.25; underside on `FACE` ≤ 0.10 | 3 | |
| L2.10.2 | Self-report agrees with the judge. | analysis | every `clear_of` d within 0.10, same pass/fail | 1 | |
| L3.10.2.1 | Self-report vs judge. | analysis | 100 percent agreement within 0.10 | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 10 |
| L2 | 26 |
| L3 | 44 (all measured by Python on the STL) |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.1.1.1, L3.10.1.1); **G1** one manifold
shell (L3.8.1.1); **G2** rotation clearance (L3.2.1.1, L3.2.1.2, L3.2.1.3); **G3** the belt runs leave freely
(L3.3.1.3); **G4** fastening and seating (L3.4.1.1, L3.4.1.2, L3.4.1.3, L3.4.2.1, L3.5.1.1).

---

## 6. Design-specific rubric (the generic rubric was absent when this was written)

### 6.1 Procedure

1. G0: the files in L2.10.1 exist and load; if the STL is missing or unreadable stop (DOES NOT MEET, one defect on L3.10.1.1).
2. Units: largest bounding-box axis within 20 to 200; if inches or metres record a defect, do not rescale.
3. Normalise the frame (1.1), rotations by multiples of 90° and X mirroring only; record the transform.
4. Build M-MOTOR, M-PULLEY, M-BELT, M-BOLT3 and every V- envelope independently from `parts/*/part.json`, the request numbers and
   the declared layout; run R1 to R4 and verify the seating rule (2.3).
5. Run every applicable L3 with Python in order; record value, limit, signed margin (negative = fail), PASS / FAIL /
   UNVERIFIED (counts as FAIL).
6. Look at renders afterwards; render-only findings are observations.
7. Decide (6.3), report (6.4).

### 6.2 Measurement recipes (trimesh 5.1, manifold3d 3.5; count shells with `decompose()`)

```python
import numpy as np, trimesh, manifold3d as m3d
M = m3d.Manifold
def load(p):
    tm = trimesh.load(p, force="mesh")
    return tm, M(m3d.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                          tri_verts=np.asarray(tm.faces, np.uint32)))
def clear_of(bodies, vol, c):
    pen = (bodies ^ vol).volume()
    if pen > 0.01: return {"d": None, "pen": pen, "where": (bodies ^ vol).bounding_box()}
    return {"d": bodies.min_gap(vol, c + 5.0), "pen": 0.0}   # PASS: pen <= 0.01 and d >= c - 0.02
```

- **Envelopes:** `M.cylinder(h, r, r, 128)` for V-ROT (flange Ø18, Z 3 to 20; shaft Ø5, Z 0 to 24) and V-BELT-ZONE; boxes for
  V-BELT-RUNS (`M.cube`, then translate); V-SWEEP = the guard unioned over a few copies translated 0 to 60 along +Z.
- **Bore and radial clearance:** slice the guard at Z = 1.0 (pilot zone) and at Z = 11.5 (flange zone); the inner contour is
  the bore; the largest inscribed circle is the bore Ø; centre vs `PILOT_AXIS`. Radial clearance = bore radius − 9.0.
- **Cap clearance:** ray cast down the shaft axis from above the guard to the cap's inner face; clearance = inner cap Z − 24.0.
- **Slot:** slice the shell at the radius mid-wall along the +X side (a plane normal to X at X = (R_i + R_o)/2); the
  through-region polygon gives the bounding box (width Y, height Z) and the centre; the roof step by its polygon edges;
  ligaments by polygon-to-edge distance.
- **Holes and engagement:** slice at mid-ear for the largest inscribed circle and the centre; ear thickness by a ray cast along
  Z at the hole; engagement = declared bolt length − ear thickness (stock lengths 6, 8, 10, 12).
- **Probe:** a ray grid of 1 mm over the faces of the hull, keep rays reaching V-SHELL-IN without hitting a solid, cluster,
  confirm a Ø2.0 sweep passes; exclude the open annulus at the motor face and the belt slot and bolt holes.
- **Printability:** transform to the print pose (180° about X); a face with normal n overhangs if n_z < −cos 45° and z > 0.05,
  minus round holes Ø ≤ 12 in vertical walls and bridges (a downward face whose ends rest on material at most 15 apart).
  Bed contact: area of faces with n_z < −0.999 at z < 0.05 over the plan bounding-box area. Thin features: inward ray cast.

### 6.3 Classes

| Class | Rule |
|---|---|
| **WRONG** | any gate G0..G4 fails |
| **MINOR** | no gate fails but a weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |
| **MEETS requirements** | CORRECT and every applicable weight-1 and weight-2 L3 passes |

Also report the weighted score Σ(weight × pass)/Σ(weight) over applicable L3s and the worst normalised margin among
weight-3 L3s. Precedence: the clearance and belt checks outrank opening size; numbers in this file beat `part.json` (record a
defect on the L3 it breaks, where = the part.json field); designed contact (1.3) is never interference; never relax a
criterion; never infer a pass from a render.

### 6.4 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first (gates, then weight 3, 2, 1). Fields: `req` (L3, L2,
L1), `status`, `feature` (by function and SCAD name, e.g. "belt slot roof", "ear at (−15.5, +15.5)"), `face` (surface and
outward normal), `location` (motor-frame coordinates, a point or a box), `measured / limit / margin`, `reference` (the model or
envelope and its datum), `render`, `evidence` (saved files), `needed` (a numeric target, never a design instruction). Group L3s
with one geometric cause under the first and list the others in `also_fails`; separate observations from defects.

---

## 7. Feasibility (a concrete design that meets every L3)

Motor frame, mm; one body; bolts in the holes at (−15.5, ±15.5).

| Feature | Value |
|---|---|
| Shell | bore Ø22.4 (R_i 11.2) straight from Z 0 to 26.2, outer Ø27.2 (R_o 13.6, wall 2.4) |
| Cap | Z 26.2 to 28.6 (2.4), Ø27.2 |
| Pilot fit | pilot Ø22.0, bore Ø22.4: gap 0.20 per side |
| Ears | two plan circles R 4.5 at (−15.5, ±15.5) joined to the shell by 9.0 wide webs, Z 0 to 4.0; clearance holes Ø3.4; bolts M3 × 8 (engagement 4.0) |
| Ribs | two 1.2 thick 45° ribs per ear on the ear top, centred ±3.9 from the ear axis line (inner faces at ±3.3, outer at ±4.5 = the web edge), trimmed to the ear and web outline, from the ear tip (Z 4.0 at R 26.4) up to the shell wall (Z 16.8 at R 13.6) |
| Belt slot | in the +X wall: flat floor at Z 10.5 for |Y| ≤ 7.4 (14.8), 45° corbels up to Z 12.25 at |Y| 9.15, vertical sides |Y| = 9.15 up to Z 19.0, flat roof at Z 19.0 (18.3 wide, prints as an upward face) |
| Pose of M-PULLEY | hub entry Z 3.0, top Z 20.0, flange Z 11.0 to 12.0 and 19.0 to 20.0, belt band Z 12.0 to 19.0, belt Z 12.5 to 18.5 |
| Print pose | rotated 180° about X: cap down, ears up on the ribs |

Checks by hand:
- Rotation clearance: radial 11.2 − 9.0 = 2.2 (band 2.0 to 3.0); shaft tip 26.2 − 24.0 = 2.2 (band 2.0 to 3.5); pulley top 26.2 − 20.0 = 6.2;
  the hub (R 8.0) to the bore 3.2. So clear_of(GUARD, V-ROT, 2.0) gives d = 2.2.
- Belt: wrapped zone R 8.63 to the bore 2.57 ≥ 0.5. Runs |Y| 7.25 to 8.63, Z 12.5 to 18.5; slot |Y| ≤ 9.15 gives 0.52 clearance
  (≥ 0.5), Z 12.0 to 19.0 gives 0.5 each side (≥ 0.5). Slot width 18.3 (band 18.3 to 22.0), height 8.5 (band 7.0 to 9.0), bottom edge
  Z 10.5 (band 10.0 to 12.0). The corbel line z − |Y| = 3.1 passes 0.54 from the belt's lower corner (8.63, 12.5), the corbel's top corner is 0.58 from it. The slot lies inside V-BELT-RUNS grown by 3.0 (Z 9.5 to 21.5 contains 10.5 to 19.0; |Y| ≤ 11.63 contains 9.15).
  Ligaments: below the slot 10.5 (to the shell bottom edge), above it 26.2 − 19.0 = 7.2 (≥ 1.5).
- Fastening: hole circle R = √(15.5² + 15.5²) = 21.92 from the axis; ear circle edge at 20.0 from the axis in X and Y (inside the motor
  outline ±21.15); engagement 8 − 4.0 = 4.0 (band 3.0 to 4.5). Head Ø5.5 on an ear of R 4.5: fully supported. Head edge to the
  shell: 21.92 − 2.75 − 13.6 = 5.57. Driver columns Ø6 at the holes clear the shell by 5.32 and the ribs (inner faces ±3.3 from the
  axis line, column radius 3.0: gap 0.3).
- Seating: underside Z 0. Bore Ø22.4 (band 22.3 to 22.7), gap 0.20 (band 0.15 to 0.35), concentric with the shaft axis.
- Plan bounding box: X −20.0 to +13.6 (33.6), Y ±20.0 (40.0), Z 0 to 28.6 (limits 45, 45, 35). Cap disc area π × 13.6² = 581 mm²;
  bed contact 581 / (33.6 × 40.0 = 1344) = 43.2 percent ≥ 40.
- Printing (cap down): bore and shell walls vertical; ears on 45° ribs (overhang exactly 45°, not steeper); the slot's flat
  floor (hanging in the print pose) 14.8 ≤ 15.0 with 45° corbels, its roof is an upward face; the bolt holes are round Ø3.4 vertical holes.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 | Method | Words in the request |
|---|---|---|---|---|---|---|
| L1.1 | placement | L2.1.1-3 | L3.1.1.1, L3.1.2.1-2, L3.1.3.1 | L1.1 | inspection | "NEMA 17", "20-tooth GT2 pulley", "hub sits 3 mm above the motor face" |
| L1.2 | rotation clearance | L2.2.1-2 | L3.2.1.1-4, L3.2.2.1 | L1.2 | analysis | "clear the pulley and the shaft by 2 mm all around" |
| L1.3 | belt slot | L2.3.1-3 | L3.3.1.1-3, L3.3.2.1-3, L3.3.3.1 | L1.3 | test | "one slot ... for the 6 mm GT2 belt" |
| L1.4 | fastening | L2.4.1-3 | L3.4.1.1-4, L3.4.2.1-2, L3.4.3.1 | L1.4 | inspection | "M3 bolts in two of the motor's four M3 face holes" |
| L1.5 | seating | L2.5.1-3 | L3.5.1.1-2, L3.5.2.1-3, L3.5.3.1 | L1.5 | analysis | "22 mm pilot", "42.3 mm square" |
| L1.6 | closed guard | L2.6.1-3 | L3.6.1.1, L3.6.2.1-3, L3.6.3.1 | L1.6 | analysis | "guard housing" |
| L1.7 | install path | L2.7.1 | L3.7.1.1 | L1.7 | test | implied (the guard slides over the shaft) |
| L1.8 | printable | L2.8.1-5 | L3.8.1.1, L3.8.2.1, L3.8.3.1, L3.8.4.1, L3.8.5.1 | L1.8 | analysis | "printed in PLA on an FDM printer without supports" |
| L1.9 | compact | L2.9.1 | L3.9.1.1 | L1.9 | inspection | implied (limit is an assumption) |
| L1.10 | evidence | L2.10.1-2 | L3.10.1.1-2, L3.10.2.1 | L1.10 | inspection | needed by the judge (not the owner's words) |

---

## Audit

Adversarial audit (second agent). Method: catalogue parts load and pass `parts.validate` (the `length` parameters of the belt and
bolt come from the request, as the catalogue requires); every number of section 7 was recomputed, and the feasibility design
was built as one solid with the reference envelopes (manifold3d) and scanned for the geometric L3s and for overhangs in the
declared print pose. `claude-context` was unavailable (server failed to connect), so targeted grep was used. The generic
`generalize/rubric.md` still does not exist; section 6 is this entry's rubric (it follows `benchmarks/enclosure/rubric.md`).

Fixes made (all in place):
1. **Slot corbels on the wrong face (printability contradiction).** FD4 prints cap down (assembly Z flipped), so the slot's
   assembly floor (Z 12.0, normal +Z) is the face that hangs over the 18.3 mm opening, a flat bridge wider than 15 (L3.8.2.1
   would fail); the stepped roof of the sketch printed as an upward face and fixed nothing. FD5 and the sketch now put the
   45° corbels on the floor: flat floor Z 10.5 for |Y| ≤ 7.4 (14.8 wide), corbels to (9.15, 12.25), sides to Z 19.0, flat
   roof Z 19.0. Belt clearance rechecked: corbel line 0.54 from the belt's lower corner, side 0.52, roof 0.5. Slot height is
   8.5 (band 7 to 9). L3.3.2.2 band changed from 11.0 to 12.0 to **10.0 to 12.0** (the lowest corbel-compatible edge is 10.56
   at the 0.5 clearance; the sketch uses 10.5).
2. **Ribs hit the driver columns.** Ribs 1.6 thick centred ±3.75 had inner faces at ±2.95, inside the Ø6.0 driver column
   (0.036 mm³ of penetration, L3.4.3.1 fails). Ribs are now 1.2 thick centred ±3.9 (inner ±3.3, gap 0.30) on ears of R 4.5 and
   webs 9.0 wide (the ribs must sit on the web).
3. **Plan outline.** The ribs' tip corners stuck out of the ear circle to X −21.19, beyond the motor outline ±21.15
   (L3.5.3.1), while the sketch claimed −19.0. Ribs are trimmed to the ear and web outline; measured bounding box now
   X −20.0 to 13.6, Y ±20.0 (33.6 × 40.0 × 28.6), bed contact 43.2 percent (was written 46.9).
4. **Hidden numbers moved into the L1 text the agent receives:** the 3.0 / 3.5 upper bounds on clearance (L1.2), the wrapped-belt
   envelope convention (tooth radius + belt thickness − tooth height, A2) and the 0.5 mm belt clearance (L1.2, L1.3),
   the slot not more than 3 mm oversize (L1.3), the 0.15 to 0.35 sliding fit (L1.5) and the 40 percent bed-contact threshold (L1.8).
5. Sketch figures corrected to the rebuilt solid (ear, rib and slot rows, ligaments, size).

Measured on the rebuilt feasibility solid: 1 shell, rotating-part clearance 2.10 (bore Ø22.4 against the Ø18 envelope), belt
runs gap 0.50, no motor penetration, both driver columns clear (gap 0.30), removal sweep clear of pilot, pulley and shaft, overhang
scan finds only the two flat bridges (slot floor 14.8 wide, ear undersides between ribs), and the 45° faces at exactly the
limit. Checked and left unchanged: counts (10 / 26 / 44), L1 count 10, no duplicate ids, the radial clearance band (pilot
Ø22.0 equals flange Ø18 plus 2 × 2.0, so the pilot bore also gives the 2 mm clearance), engagement band, request numbers vs part.json.
