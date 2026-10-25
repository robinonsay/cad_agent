# G37 Motor pinion and idler gear carrier: requirements (L1 / L2 / L3)

A training design of the generalisation set (`benchmarks/generalize/designs/G37`). The
machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file. It is
modelled on `benchmarks/enclosure/requirements.md` (E1-01): same tree, same two interference checks,
same grading classes, with a centre-distance check, a gear-gap check and a stub-stress check added.
The agent sees only the request text and the parts catalogue (`benchmarks/generalize/parts/*/part.json`);
never this file.

**Brief (plan.json G37):** "A carrier plate that mounts a NEMA 17 on its 31 mm pattern, with a 16
tooth module 1.5 pinion on the shaft driving a 32 tooth idler on a 608 bearing. Set the idler center
distance from the gear parameters plus 0.2 mm, and include a 0.5 mm gap between gears and plate."

**How to read this.** L1 says what the owner needs; L2 turns it into an engineering requirement with
numbers; L3 is a concrete check on the delivered geometry. Every row has a method, a pass/fail
criterion with a tolerance, a weight (3 critical, 2 major, 1 minor) and a gate mark where a failure
makes the design WRONG. Every number that comes from an assumption (section 3) is provisional. Do
not relax a criterion because the agent fails it. The only printed body is the carrier; the motor,
both gears and the bearing are bought parts that the grader places from the catalogue.

---

## 1. Frames, tolerances and the generic checks

### 1.1 Frames

- **Carrier frame:** Z up with the plate's front face (the gear side) at **Z = 0**; the plate occupies
  Z −T to 0, the motor behind it (Z < −T), the shaft pointing **+Z** through the plate. The motor
  axis is X = Y = 0. The idler's axis is parallel to Z through the point at distance C (the centre
  distance) from the motor axis and at angle φ about it; φ is chosen by the design and declared. A design
  delivered rotated or mirrored is normalised into this frame (rotations by multiples of 90° and
  mirroring only): the plate is the broad flat body, its face with the stub is the front.
- **Part frames:** those of the catalogue part files at the declared poses. `nema17_motor` and
  `gear_spur_generic` and `bearing_608` all have their axis along part Z, mapped to carrier +Z.

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

- the motor's face on the plate's back face, its 22 mm pilot in the register hole, its shaft in the
  gear's bore, and an M3 screw in its clearance hole, its head on the counterbore floor and its
  thread in the motor;
- the bearing's inner ring on the stub's shoulder and on the stub (the bearing in its idler gear's
  hub bore is the press fit of the catalogue's `HOUSING_BORE`);
- the mesh of the two gears: the pinion and the idler overlap in their tip circles by design, and
  that overlap is never an interference (the mesh is checked by the centre distance, section 4 F3).

---

## 2. Reference models, envelopes and datums

### 2.1 Reference models (M-)

| Name | What | Source | Size and datums (carrier frame, mm) |
|---|---|---|---|
| **M-MOTOR** | NEMA 17 stepper, body 40 long | `nema17_motor` (body_length 40) | body 42.3 × 42.3 × 40 behind the face; face `FACE` on the plate's back face; pilot Ø22.0 × 2.0 on `PILOT_AXIS`; shaft Ø5.0 × 24 on `SHAFT_AXIS`; `HOLE`: four axes on a 31.0 square, M3, thread depth 4.5. Placed with the shaft toward +Z, axis X = Y = 0. |
| **M-PINION** | 16 tooth, module 1.5 pinion | `gear_spur_generic` (module 1.5, teeth 16, face width 8) | tip circle Ø27.0 (= 1.5 × (16 + 2)), pitch Ø24.0, root Ø20.25, face width 8.0, hub bore Ø5.0 (the shaft). |
| **M-IDLER** | 32 tooth, module 1.5 gear | `gear_spur_generic` (module 1.5, teeth 32, face width 8) | tip circle Ø51.0, pitch Ø48.0, root Ø44.25, face width 8.0, hub bore Ø22.1 (the bearing's `HOUSING_BORE`). |
| **M-BEARING** | 608 bearing | `bearing_608` | Ø22.0 × 7.0, bore Ø8.0; `AXIS`, `FACE_A`, `FACE_B`, `CENTRE`; `HOUSING_BORE` Ø22.1. |
| **M-BOLT-M3** | M3 socket-head screw | `bolt_m3_iso4762` | head Ø5.5 × 3.0, thread Ø3.0, clearance Ø3.4. Four, one per `HOLE`, length declared. |
| **RA** | reference assembly | M-MOTOR ∪ M-PINION ∪ M-IDLER ∪ M-BEARING ∪ 4 × M-BOLT-M3 at the declared poses | no printed geometry |

The catalogue gear is the tip-diameter blank (the envelope a housing must clear); its hub bore is
not modelled there, so the grader subtracts the bore named above from each blank (M-PINION minus
the Ø5.0 shaft, M-IDLER minus the Ø22.1 bearing seat).

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-PINION** | the pinion's rotating envelope | the Ø27.0 × 8.0 cylinder of M-PINION at its declared pose, minus the Ø5.0 hub bore. |
| **V-IDLER** | the idler's rotating envelope | the Ø51.0 × 8.0 cylinder of M-IDLER at its declared pose, minus the Ø22.1 hub bore. |
| **V-SHAFT** | the shaft | Ø5.0 cylinder from the motor face along `SHAFT_AXIS`, 24 long. |
| **V-PILOT** | the pilot | Ø22.0 × 2.0 cylinder on `PILOT_AXIS` against the motor face (toward +Z). |
| **V-MOTOR-BODY** | the motor's body | the box 42.3 × 42.3 × 40 behind the face. |
| **V-STUB-ZONE** | the stub's bearing seat | Ø8.0 cylinder (the bearing's bore) from the shoulder top (Z 1.0) to the bearing's top face at the declared pose. |
| **V-HEAD3-k** | M3 head | Ø5.5 × 3.0 cylinder on `HOLE`k, bearing face on the counterbore floor. |
| **V-TOOL3-k** | hex-key access | Ø5.5 cylinder from the head's top along +Z, 25 long. |
| **V-INSTALL-MOTOR** | motor assembly path | M-MOTOR swept along +Z from 60 mm behind its seat to the seat, minus the seating contact (face on plate, pilot in register). |
| **V-INSTALL-GEARS** | gear and bearing assembly path | M-PINION, M-IDLER and M-BEARING each swept along −Z from 40 mm in front (+Z) of their seat to the seat, minus the seating contact. |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-MOTOR | units; body 42.3 × 42.3 × 40; shaft Ø5.0 × 24 | ± 0.2 |
| R2 | M-MOTOR | hole square and pilot | 31.0 ± 0.1; Ø22.0 ± 0.1 |
| R3 | M-PINION, M-IDLER | tip diameters | 27.0 ± 0.05; 51.0 ± 0.05 |
| R4 | M-BEARING | Ø22 × 7, bore Ø8 | ± 0.1 |
| R5 | RA | no collision other than the mesh and the designed contacts | intersection ≤ 0.01 mm³ |
| R6 | every V- envelope | its datums equal the model datums it came from | ≤ 0.01 |

**Seating rule.** The grader places the models at the poses in `layout.json` and verifies: M-MOTOR's
`FACE` lies on the plate's back face (distance ≤ 0.10); its `HOLE` axes are coaxial with the plate's
four holes (residual ≤ 0.25) and `PILOT_AXIS` with the register (≤ 0.15); M-BEARING's `FACE_A` is
within 0.10 of the stub's shoulder top and its axis within 0.10 of the stub's axis; the idler's and
the bearing's axes coincide (≤ 0.05). If a declaration fails, the part is re-seated by fitting to
the printed plate and every L3 that needed the declaration fails.

---

## 3. Assumptions and open questions

| # | Question | Value chosen | Uncertainty / why |
|---|---|---|---|
| A1 | Gear parameters? | module 1.5, 16 and 32 teeth (the brief), 20° pressure angle, profile shift 0, **face width 8.0 both** (given in the request) | face width 6-9 is typical for module 1.5; the brief does not give it, the request does. |
| A2 | Centre distance? | C = m (z₁ + z₂) / 2 + 0.2 = 1.5 × 48 / 2 + 0.2 = 36.2, ± 0.05 | brief. The 0.2 is the backlash allowance; the implied circumferential backlash is 2 × 0.2 × tan 20° = 0.146 mm, ± 0.04. |
| A3 | Tip-to-root clearance? | derived: C − (tip radius of one gear + root radius of the other) = 36.2 − (13.5 + 22.125) = 0.575 for both pairs; the standard 0.25 m = 0.375 plus the 0.2 allowance | ± 0.05 with C. |
| A4 | Gap to the plate? | 0.5 between each gear's near face and the plate's front face (brief), measured as the least distance from the gear's rotating envelope to any printed surface; the band is 0.48-0.70 | FDM first layers vary by 0.1; the upper limit stops a loose carrier. |
| A5 | Motor? | 17HS4401 class: body 42.3 square × 40 long, shaft Ø5 × 24, 31.0 pattern, pilot Ø22 × 2 (catalogue) | body length 34 / 40 / 48 exists; 40 is the catalogue default and changes no L3. |
| A6 | Motor torque, tooth load? | peak motor torque 0.4 N·m (17HS4401 holding torque); tooth force F_t = 400 / 12 = 33.3 N at the pinion's pitch radius (12.0), normal force F_n = F_t / cos 20° = 35.5 N | ± 25 %. Static, no shock, no fatigue. |
| A7 | Allowable stress? | 5.0 MPa on the bending stress at the stub's root = 15 MPa (inter-layer strength of PLA, the stub is printed standing) ÷ safety factor 3 | PLA across-layer strength 15-25 MPa; ± 5. |
| A8 | Stub size? | Ø7.9 ± 0.05 (the bearing's bore 8.0 minus the catalogue shaft clearance 0.1) | printers vary by 0.1; print a test pin. |
| A9 | Inner-ring shoulder? | Ø9.5-11.5 and 1.0 ± 0.1 high, so it bears on the inner ring only and the bearing sits at Z 1.0-8.0 (the inner ring's outside diameter is about 12) | ± 0.5; same convention as the catalogue's outer-ring shoulder note. |
| A10 | Register fit? | register Ø22.5 on a Ø22.0 pilot (0.25 per side, the generic sliding fit; band 0.15-0.35) | FDM holes print 0.1 small. |
| A11 | Plate thickness? | 5.0-8.0 | stiff enough for a counterbore (3.2-4.0 deep) and a 2.0 web. |
| A12 | How is the carrier held? | not modelled (no mounting holes asked for) | the owner must supply them; flagged to the owner, not graded. |
| A13 | Axial retention of the bearing? | not modelled (the stub's top and a clip or screw are the owner's) | the stub length range leaves room (L2.5.3). |
| A14 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed | typical FDM tolerances. |
| A15 | Size limit? | plate within 120 × 80 in plan, whole carrier ≤ 30 high | the layout in section 7 is 67 × 44 × 16. |

---

## 4. Fixed decisions (a choice would otherwise be ambiguous)

| # | Decision | Why |
|---|---|---|
| F1 | One printed body: the plate with an integral stub (the idler's axle) and its inner-ring shoulder. | the brief's carrier plate; the idler is on a bought bearing, which needs a stub. |
| F2 | The motor is behind the plate (back face), the shaft passes through a register hole to the gear side; the gears and the bearing are in front (+Z). The four M3 screws go in from the front, heads counterbored. | "the shaft passes through" the carrier; gears and plate gap are on the same side. |
| F3 | The idler sits on the plate at centre distance C = 36.2 ± 0.05 from the motor axis, at any angle φ the design chooses. Both gears and the bearing are coaxial pairs: the idler's gear and bearing share an axis; the pinion shares the motor's. Both gears lie in the same plane: their mid-planes agree within 0.25. | brief; the mesh is checked by C and the planes, not by a tooth profile (the catalogue gear has none). |
| F4 | Both gears' near faces are at 0.5 (band 0.48-0.70) from the plate's front face. | brief. |
| F5 | The bearing sits on the shoulder with its mid-plane within 0.25 of the idler gear's mid-plane. | the gear is pressed on the bearing's outer ring. |
| F6 | Print orientation: the plate's back face on the bed, the stub standing up (bed normal within 5° of the stub axis); stated in `layout.json`. | flat plate on the bed. |
| F7 | `layout.json` declares the motor pose, the pinion pose (Z of its start face), the idler pose (C, φ, Z), the bearing pose (Z of face A), the four M3 lengths (standard ISO 4762 lengths 6, 8, 10, 12, 16, 20, 25) and the print orientation. | needed by the seating rule and L2.2.4. |

---

## 5. Requirements tree

Columns: ID, requirement, method, pass/fail (with tolerance), weight, gate.

### L1.1 The motor, both gears and the bearing are laid out coaxially in parallel planes without collisions

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout (F7). | inspection | `layout.json` parses; names `nema17_motor`, `gear_spur_generic` (twice, with teeth 16 and 32), `bearing_608`, each with a pose | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 | |
| L2.1.2 | Pinion on the shaft, idler and bearing on one axis, all axes parallel. | inspection | pinion axis = `SHAFT_AXIS` (offset ≤ 0.05); idler axis = bearing axis = stub axis (offset ≤ 0.05); stub axis within 0.3° of `SHAFT_AXIS` | 3 | |
| L3.1.2.1 | Axes coincide. | inspection | offsets ≤ 0.05 | 3 | |
| L3.1.2.2 | Axes parallel. | inspection | ≤ 0.3° | 3 | |
| L2.1.3 | The assembly has no interference other than the designed contact and the mesh. | analysis | RA pairs ≤ 0.01 mm³ except M-PINION/M-IDLER (mesh), M-IDLER/M-BEARING and M-BEARING/stub (designed fits) | 3 | |
| L3.1.3.1 | Pairwise interference of RA and the carrier. | analysis | each pair ≤ 0.01 mm³ except the listed ones | 3 | |
| L2.1.4 | The two gears lie in the same plane. | inspection | mid-plane Z of M-PINION and M-IDLER within 0.25 | 3 | |
| L3.1.4.1 | Gear mid-planes. | inspection | \|Z_pinion − Z_idler\| ≤ 0.25 | 3 | |

### L1.2 The motor seats on the plate with its pilot in a register and four M3 screws

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The motor face seats on the plate's back face. | analysis | `FACE` within 0.10 of the back face; contact patch ≥ 600 mm² | 3 | G2 |
| L3.2.1.1 | Face-to-plate distance. | analysis | ≤ 0.10 | 3 | G2 |
| L3.2.1.2 | Back-face flatness over the 42.3 square. | inspection | ≤ 0.20 | 2 | |
| L2.2.2 | A register hole locates the pilot, the shaft passes through. | inspection | register inscribed Ø in [22.3, 22.7] (radial gap to the pilot 0.15-0.35); axis within 0.10 of the pattern's centre; clear_of(PLATE, V-SHAFT, 3.0) | 3 | G2 |
| L3.2.2.1 | Register diameter and gap. | inspection | Ø in [22.3, 22.7] | 3 | G2 |
| L3.2.2.2 | Register axis vs the pattern centre. | inspection | ≤ 0.10 | 3 | |
| L3.2.2.3 | Pilot inside the register, shaft clear. | analysis | V-PILOT ≥ 0.10 from the hole wall; shaft d ≥ 3.0 | 3 | |
| L2.2.3 | Four holes on the motor's 31.0 square. | inspection | count 4; each axis within 0.15 of `HOLE`k; square 31.0 ± 0.15; Ø3.4 ± 0.15 | 3 | G2 |
| L3.2.3.1 | Hole count and axis offsets. | inspection | 4; each ≤ 0.15 | 3 | G2 |
| L3.2.3.2 | Pattern square and hole diameter. | inspection | 31.0 ± 0.15; Ø in [3.25, 3.55] | 3 | |
| L2.2.4 | Counterbores from the front face, the declared screws fit. | analysis | counterbore Ø5.9-6.4, depth 3.2-4.0, web ≥ 2.0; head recess = depth − 3.0 in [0.2, 1.0]; engagement = L − web in [3.0, 4.5] | 2 | |
| L3.2.4.1 | Counterbore diameter, depth, web. | inspection | as L2.2.4 | 2 | |
| L3.2.4.2 | Thread engagement of the declared screws. | analysis | in [3.0, 4.5] (L = 6 gives 3.4 with a 3.4 counterbore) | 2 | |
| L2.2.5 | Edge distances and tool access. | analysis | ≥ 2.0 of material from each counterbore to the plate edges; clear_of(PLATE, V-TOOL3-1..4, 0.0) | 2 | |
| L3.2.5.1 | Edge distances. | analysis | ≥ 2.0 | 2 | |
| L3.2.5.2 | Tool columns clear. | analysis | d ≥ 0.0 | 1 | |
| L2.2.6 | The motor installs from behind without hitting the carrier. | test | clear_of(PLATE, V-INSTALL-MOTOR, 0.0) | 2 | |
| L3.2.6.1 | Installation path clear. | test | d ≥ 0.0 | 2 | |

### L1.3 The pinion sits on the shaft clear of the plate and inside the shaft's length

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The pinion lies on the shaft with at least 2.0 of shaft showing beyond it. | inspection | the shaft projects 24.0 − T beyond the front face (T = plate thickness); pinion top Z ≤ 22.0 − T in the carrier frame | 3 | |
| L3.3.1.1 | Pinion top vs shaft tip. | inspection | Z_top ≤ 22 − T (T = 6 gives 16.0) | 3 | |
| L2.3.2 | The pinion does not touch the carrier or the motor. | analysis | clear_of(PLATE, V-PINION, 0.45) and V-PINION ∩ M-MOTOR ≤ 0.01 mm³ | 3 | |
| L3.3.2.1 | Pinion clear of the carrier. | analysis | d ≥ 0.45 | 3 | |
| L2.3.3 | The pinion has the right size. | inspection | the declared pinion has teeth 16, module 1.5, face width 8.0 (tip Ø27.0 ± 0.05) | 2 | |
| L3.3.3.1 | Pinion parameters. | inspection | as L2.3.3 | 2 | |
| L2.3.4 | The pinion and the screw heads do not meet. | analysis | clear_of(V-PINION, V-HEAD3-1..4 ∪ counterbores' heads, 0.0) | 1 | |
| L3.3.4.1 | Heads clear of the pinion. | analysis | d ≥ 0.0 | 1 | |

### L1.4 The idler's centre distance is the gear parameters plus 0.2 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The idler axis is at C = m (z₁ + z₂) / 2 + 0.2 from the motor axis. | inspection | distance between the stub's axis (fit to the printed stub) and `SHAFT_AXIS` = 36.2 ± 0.05 | 3 | G3 |
| L3.4.1.1 | Centre distance. | inspection | 36.2 ± 0.05 (+ ε) | 3 | G3 |
| L3.4.1.2 | The declared C agrees with the printed stub. | inspection | \|C_declared − C_measured\| ≤ 0.05 | 2 | |
| L2.4.2 | The tooth clearance that follows is right. | analysis | for each pair, C − (tip radius + root radius) in [0.50, 0.65] (0.575 ± 0.075 from the 0.05 tolerance) | 2 | |
| L3.4.2.1 | Tip-to-root clearance, both pairs. | analysis | in [0.50, 0.65] | 2 | |
| L2.4.3 | The declared idler has the right size. | inspection | teeth 32, module 1.5, face width 8.0 (tip Ø51.0 ± 0.05) | 2 | |
| L3.4.3.1 | Idler parameters. | inspection | as L2.4.3 | 2 | |

### L1.5 The idler turns on a 608 bearing that seats on a printed stub

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The stub fits the bearing's bore. | inspection | stub Ø 7.9 ± 0.05 (the bearing's bore Ø8.0 less the 0.1 shaft clearance); round ≤ 0.10 | 3 | G5 |
| L3.5.1.1 | Stub diameter. | inspection | Ø in [7.85, 7.95] | 3 | G5 |
| L3.5.1.2 | Stub roundness. | inspection | ≤ 0.10 | 2 | |
| L2.5.2 | The bearing sits on a shoulder that bears on its inner ring only. | analysis | shoulder Ø in [9.5, 11.5], height 1.0 ± 0.1; `FACE_A` within 0.10 of the shoulder top; clear_of(PLATE minus shoulder, M-BEARING, 0.4) | 3 | G5 |
| L3.5.2.1 | Bearing seat: shoulder size and face contact. | analysis | as L2.5.2 | 3 | G5 |
| L3.5.2.2 | Bearing clear of the plate (shoulder contact excluded). | analysis | d ≥ 0.40 | 3 | |
| L2.5.3 | The stub carries the whole bearing and leaves room for a retainer. | inspection | stub top above the front face in [bearing top Z, bearing top Z + 3.0] (L = Z 1.0 + 7.0 = 8.0, so [8.0, 11.0]) | 2 | |
| L3.5.3.1 | Stub length. | inspection | in [8.0, 11.0] | 2 | |
| L2.5.4 | The bearing and the idler's gear are coaxial and centred. | inspection | bearing mid-plane within 0.25 of the idler gear mid-plane | 2 | |
| L3.5.4.1 | Bearing vs gear mid-plane. | inspection | ≤ 0.25 | 2 | |

### L1.6 The gears keep 0.5 mm from the plate and from everything printed

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Each gear's near face is 0.5 from the plate's front face (F4). | analysis | gap(V-PINION, PLATE) and gap(V-IDLER, PLATE) both in [0.48, 0.70] | 3 | G4 |
| L3.6.1.1 | Gear-to-plate gap, both gears. | analysis | each in [0.48, 0.70] | 3 | G4 |
| L2.6.2 | Nothing else printed enters a gear's rotating envelope. | analysis | clear_of(PLATE, V-PINION ∪ V-IDLER, 0.45) (the stub and its shoulder lie inside the idler's bore, not in V-IDLER) | 3 | |
| L3.6.2.1 | Envelopes clear. | analysis | d ≥ 0.45 | 3 | |
| L2.6.3 | The idler's bore leaves the stub free. | analysis | clear_of(stub and shoulder, V-IDLER, 0.0) with the shoulder Ø ≤ 11.5 inside the Ø22.1 bore | 2 | |
| L3.6.3.1 | Stub clear of the idler ring. | analysis | d ≥ 0.0 | 2 | |
| L2.6.4 | The gears can be put on from the front. | test | clear_of(PLATE, V-INSTALL-GEARS, 0.0) | 2 | |
| L3.6.4.1 | Gear installation path clear. | test | d ≥ 0.0 | 2 | |

### L1.7 The stub carries the tooth load

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The bending stress at the stub's root is below the allowable (A6, A7). | analysis | σ = F_n · h / S ≤ 5.0 MPa with F_n = 35.5 N, h = the measured distance from the plate's front face to the bearing's mid-plane (4.5 for the layout in section 7), S = π d³ / 32 from the measured stub diameter d | 3 | |
| L3.7.1.1 | Stub root stress. | analysis | ≤ 5.0 MPa (+ 2 % ε) | 3 | |
| L2.7.2 | The plate is thick enough to carry the motor's torque and the stub. | inspection | thickness in [5.0, 8.0]; the plate under the stub and shoulder is not interrupted by any hole within 3.0 | 2 | |
| L3.7.2.1 | Plate thickness. | inspection | in [5.0, 8.0] | 2 | |
| L3.7.2.2 | Material round the stub. | inspection | ≥ 3.0 from the shoulder's edge to the plate's edge and to any hole | 2 | |

### L1.8 It prints on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The plate lies on its back face with the stub up (F6). | inspection | angle between the declared bed normal and the stub axis ≤ 5.0° | 2 | |
| L3.8.1.1 | Orientation angle. | inspection | ≤ 5.0° | 2 | |
| L2.8.2 | No unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12 and bridges ≤ 15.0. | analysis | 0 offending faces of area > 1 mm² | 2 | |
| L3.8.2.1 | Overhang and bridge scan. | analysis | as L2.8.2 | 2 | |
| L2.8.3 | The body rests on a flat face. | analysis | bed contact ≥ 50 % of the plan bounding box | 1 | |
| L3.8.3.1 | Bed contact. | analysis | ≥ 50 % | 1 | |
| L2.8.4 | No feature thinner than 0.8; the body fits a 200 × 200 × 200 bed. | analysis | min thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 | |
| L3.8.4.1 | Thin features. | analysis | ≥ 0.8 | 1 | |
| L3.8.4.2 | Bounding box. | inspection | ≤ 200 per axis | 1 | |

### L1.9 It is one clean printable solid of reasonable size

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The mesh is manifold and one shell. | analysis | 1 shell; manifold3d accepts it; no fragment | 3 | G1 |
| L3.9.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.9.2 | Size (A15). | inspection | plan X ≤ 120.0, Y ≤ 80.0; height ≤ 30.0 | 1 | |
| L3.9.2.1 | Bounding box. | inspection | as L2.9.2 | 1 | |

### L1.10 The package says what was built and where, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | The package holds `carrier.stl` (carrier frame, mm), the OpenSCAD source, `layout.json` (F7) and the agent's own report of the checks above. | inspection | all present and readable | 3 | G0 |
| L3.10.1.1 | Files present and parse; the body's largest bounding-box axis in 20-200 mm. | inspection | true | 3 | G0 |
| L3.10.1.2 | The declared poses verify under the seating rule (section 2.3). | analysis | motor face ≤ 0.10; hole residual ≤ 0.25; register ≤ 0.15; bearing face A ≤ 0.10; axes ≤ 0.10 | 3 | |
| L2.10.2 | The agent's own report agrees with the judge. | analysis | for every `clear_of` / gap / stress L3 the agent reports: same pass/fail and \|d_agent − d_judge\| ≤ 0.10 (stress within 10 %) | 1 | |
| L3.10.2.1 | Self-report vs judge. | analysis | 100 % agreement | 1 | |

---

## 6. Counts and gates

| Level | Count |
|---|---|
| L1 | 10 |
| L2 | 35 |
| L3 | 48 (weight 3: 23, weight 2: 18, weight 1: 7; 0 physical or human, optional) |

Every L3 is a measurement a Python script can make on the delivered STL (or on the declared
`layout.json` against the catalogue), except the rows marked physical or human.

Gates (a failure makes a design WRONG regardless of score): see section 9.

---

## 7. Feasibility

One design exists that meets every L3 above (carrier frame, mm):

- **Plate:** X −22 to 45, Y −22 to 22, Z −6 to 0 (67 × 44 × 6; T = 6 ∈ [5.0, 8.0]); the back face is flat
  at Z −6 with the motor on it (motor body Z −46 to −6).
- **Motor:** axis at X = Y = 0; register Ø22.5 through the plate (gap to the Ø22.0 pilot 0.25); four Ø3.4
  holes at (±15.5, ±15.5) with Ø6.0 counterbores 3.4 deep from the front face (web 6 − 3.4 = 2.6 ≥ 2.0;
  head Ø5.5 × 3.0 recessed 0.4); M3 × 6 screws give engagement 6 − 2.6 = 3.4 ∈ [3.0, 4.5]. Edge
  distances: counterbore edge at 18.5 from the axis to the plate's edges at X −22 (3.5) and at Y ±22
  (3.5), all ≥ 2.0. The shaft (Ø5, tip at Z 18) has 8.75 around it in the register (≥ 3.0).
- **Pinion:** Ø27 × 8 at Z 0.5-8.5 on the shaft; its top Z 8.5 ≤ 22 − 6 = 16.0; gap to the plate
  0.5.
- **Idler:** axis at (36.2, 0) (C = 1.5 × 48 / 2 + 0.2); gear Ø51 × 8 at Z 0.5-8.5 (gap 0.5; mid-plane
  4.5 = the pinion's); hub bore Ø22.1; bearing 608 at Z 1.0-8.0 (mid-plane 4.5, 0.0 from the
  gear's). Tip-to-root clearance 36.2 − (13.5 + 22.125) = 0.575 ∈ [0.50, 0.65].
- **Stub:** Ø7.9 from the plate's front face to Z 10.0 (in [8.0, 11.0]); a shoulder Ø11.0 × 1.0 at Z 0-1.0
  bears on the inner ring (Ø11 ≤ 11.5, ≥ 9.5), and its edge is 11.0/2 = 5.5 from the axis, 8.8 − 5.5 =
  3.3 ≥ 3.0 from the plate's edge at X 45; the plate under the stub has no hole. The bearing is
  0.4+ clear of the plate beyond the shoulder (its face A at Z 1.0 is 1.0 above the plate).
- **Stress:** F_n = 33.3 / cos 20° = 35.5 N; h = 4.5; M = 160 N·mm; S = π × 7.9³ / 32 = 48.4 mm³;
  σ = 3.3 MPa ≤ 5.0 (margin 1.5×).
- **Gear envelopes:** V-PINION and V-IDLER lie in Z 0.5-8.5 and no printed body is there (the stub and
  its shoulder, which end or stay inside the idler's Ø22.1 bore, are not in V-IDLER; the counterbored
  heads are at or below Z 0); the clearance of both envelopes is 0.5, to the plate's front face.
- **Printing:** plate back face on the bed (about 2530 mm², 86 % of the 67 × 44 plan), stub up
  (bed normal along the stub axis); every hole is vertical; nothing overhangs; the shoulder's
  underside is the plate.
- **Size:** 67 × 44 × 16 (limits 120 × 80 × 30).

This sketch is one satisfiable design; it is not the only one and is never given to the agent.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 (`design.json`) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1-L2.1.4 | L3.1.1.1, L3.1.2.1-2, L3.1.3.1, L3.1.4.1 | L1.1 | inspection | "pinion on the motor shaft driving a 32 tooth idler" |
| L1.2 | Motor mount | L2.2.1-L2.2.6 | L3.2.1.1-2, L3.2.2.1-3, L3.2.3.1-2, L3.2.4.1-2, L3.2.5.1-2, L3.2.6.1 | L1.2 | analysis | "NEMA 17 on its 31 mm pattern", "shaft passes through" |
| L1.3 | Pinion | L2.3.1-L2.3.4 | L3.3.1.1, L3.3.2.1, L3.3.3.1, L3.3.4.1 | L1.3 | inspection | "16 tooth module 1.5 pinion" |
| L1.4 | Centre distance | L2.4.1-L2.4.3 | L3.4.1.1-2, L3.4.2.1, L3.4.3.1 | L1.4 | inspection | "idler centre distance from the gear parameters plus 0.2 mm" |
| L1.5 | Idler bearing | L2.5.1-L2.5.4 | L3.5.1.1-2, L3.5.2.1-2, L3.5.3.1, L3.5.4.1 | L1.5 | analysis | "idler gear that turns on a 608 bearing" |
| L1.6 | Gear gap | L2.6.1-L2.6.4 | L3.6.1.1, L3.6.2.1, L3.6.3.1, L3.6.4.1 | L1.6 | analysis | "0.5 mm gap between the gears and the plate" |
| L1.7 | Stub load | L2.7.1-L2.7.2 | L3.7.1.1, L3.7.2.1-2 | L1.7 | analysis | implied (the tooth load) |
| L1.8 | Printable | L2.8.1-L2.8.4 | L3.8.1.1, L3.8.2.1, L3.8.3.1, L3.8.4.1-2 | L1.8 | analysis | "printed in PLA on an FDM printer" |
| L1.9 | Clean solid | L2.9.1-L2.9.2 | L3.9.1.1, L3.9.2.1 | L1.9 | analysis | "as one part" |
| L1.10 | Evidence | L2.10.1-L2.10.2 | L3.10.1.1-2, L3.10.2.1 | L1.10 | inspection | needed by the judge |

## 9. Grading procedure for G37

`benchmarks/generalize/rubric.md` did not exist when this file was written, so this section is the design-specific rubric (units, frames, recipes, classes, defect reports). If a generic rubric.md appears later it governs generic rules; this section still governs everything specific to G37.

1. **Package gate (G0).** The files of the last L1 must exist and load. If a delivered STL is
   missing or unreadable, stop: verdict DOES NOT MEET, one defect on the G0 L3.
2. **Units.** Load each STL; the largest bounding-box axis of carrier.stl must be 20-200 mm
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

Gates: G0 package (L3.10.1.1); G1 manifold and one shell (L3.9.1.1); G2 motor seats on the plate with its register and four M3 holes (L3.2.1.1, L3.2.2.1, L3.2.3.1); G3 idler centre distance (L3.4.1.1); G4 gap between the gears and the plate (L3.6.1.1); G5 the bearing seats on the idler's stub (L3.5.1.1, L3.5.2.1).

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

Adversarial audit of this entry, 2026-10-24. Derived numbers recomputed from `gear_spur_generic`
(pitch m z, tip m (z + 2), root m (z − 2.5)): pinion 24.0 / 27.0 / 20.25, idler 48.0 / 51.0 / 44.25; C =
36 + 0.2 = 36.2; tip-to-root both pairs 36.2 − (13.5 + 22.125) = 36.2 − (25.5 + 10.125) = 0.575; shaft tip
at Z 24 − 6 = 18, pinion top 8.5 against 16.0; bearing 22.0 in a 22.1 bore; F_t = 400 / 12 = 33.3 N, F_n =
35.5 N, M = 160 N mm, S = π 7.9³ / 32 = 48.4 mm³, σ = 3.3 MPa; stub edge to plate edge 45 − 36.2 − 5.5 =
3.3; bed contact about 2515 mm² = 85 %; size 67 × 44 × 16. The sketch satisfies every gate and L3. All
catalogue ids load. L1 count 10; L2 35, L3 48 with weights 23 / 18 / 7.

| # | Finding | Fix |
|---|---|---|
| 1 | `bolt_m3_iso4762` takes `length` from the request and "M3" ties with `screw_m3_selftap`; the request named neither screw type nor lengths (F7 was hidden). | Request now names ISO 4762 M3 socket-head screws and the stock lengths 6, 8, 10, 12, 16, 20, 25 mm. |
| 2 | The motor torque (0.4 N m, A6) that sets the stub load appeared in L1.7 but not in the request. | Request now says "The motor's peak torque is 0.4 N m". |
| 3 | "Motor behind the plate, gears in front" (F2) was implicit. | Request now says "the motor behind the plate". |
| 4 | Judge-needed numbers appeared only in L2/L3: counterbore web and edge 2.0, head recess 0.2-1.0 (L1.2), shoulder height 1.0 plus or minus 0.1 (L1.5), 3.0 mm of plate round the shoulder (L1.7), bed contact 50 % (L1.8). | Added to the matching L1 texts in `design.json`. |
| 5 | With plate thickness 5.0, the cheapest legal counterbore (3.2) leaves a 1.8 web, below 2.0, so the lower end of 5.0-8.0 is not reachable with the other L3s. | Left as written (the band is the owner's, the sketch uses 6.0); thickness 5.2 or more satisfies every L3. |
| 6 | Hex-key access is graded against printed material only (L2.2.5). With the idler at angle 0 the two screws nearer the idler are under the idler gear's envelope once it is fitted. | Assumption recorded: assembly order is motor and screws first, then pinion and idler (L2.6.4 sweeps the gears in from the front). Not graded. |

Observation: the tolerance quoted in A3 is 0.575 plus or minus 0.075 but the 0.05 centre-distance tolerance
gives plus or minus 0.05; L3.4.2.1 uses [0.50, 0.65], which is the looser band.
