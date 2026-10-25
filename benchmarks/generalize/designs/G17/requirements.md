# G17 NEMA17 L-bracket with pilot register: requirements (L1 / L2 / L3)

A training design of the generalisation set (`benchmarks/generalize/designs/G17`). The
machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file. It is
modelled on `benchmarks/enclosure/requirements.md` (E1-01): same tree, same two interference checks,
same grading classes, with a structural check and a print-orientation check added. The agent sees
only the request text and the parts catalogue (`benchmarks/generalize/parts/*/part.json`); never
this file.

**Brief (plan.json G17):** "An L-shaped NEMA 17 motor bracket: vertical face takes the motor on the
31 mm pattern with a 22.5 mm pilot register, horizontal flange has two M4 holes 40 mm apart. The
motor shaft end passes through the face, and the bracket should survive about 20 N at the shaft.
Orient it so layers do not split at the bend."

**How to read this.** L1 says what the owner needs; L2 turns it into an engineering requirement with
numbers; L3 is a concrete check on the delivered geometry. Every row has a method, a pass/fail
criterion with a tolerance, a weight (3 critical, 2 major, 1 minor) and a gate mark where a failure
makes the design WRONG. Every number that comes from an assumption (section 3) is provisional. Do
not relax a criterion because the agent fails it.

---

## 1. Frames, tolerances and the generic checks

### 1.1 Frames

- **Bracket frame:** Z up, the flange's underside (the mounting plane) at Z = 0. The motor's shaft
  points **+X**; the vertical face (plate) has its normal along X, the motor on its −X side; the
  flange extends toward +X. The bend axis (the line of the inside corner) is **Y**. A design
  delivered rotated or mirrored is normalised into this frame (rotations by multiples of 90° and
  mirroring only): the mounting plane is the plane of the exits of the two Ø4.5 flange holes, the
  motor side of the plate is the face that carries the 31 mm pattern's register hole. The motor
  axis is taken as Y = 0.
- **Motor frame:** that of `nema17_motor` (axis along Z, origin on the mounting face at the shaft
  axis, body toward −Z, pilot and shaft toward +Z). The design's declared pose maps motor +Z to
  bracket +X.

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

- the motor's face resting on the plate's motor-side face (inside the plate's plan; face contact);
- the motor's 22 mm pilot inside the register hole, at the fit L2.3.1 sets;
- an M3 screw in its clearance hole, its head on the counterbore floor, its thread in the motor's
  tapped hole;
- an M4 screw in its flange hole, its head on the counterbore floor;
- the flange's underside on the mounting surface (outside the part).

---

## 2. Reference models, envelopes and datums

### 2.1 Reference models (M-)

| Name | What | Source | Size and datums (bracket frame, mm) |
|---|---|---|---|
| **M-MOTOR** | NEMA 17 stepper, body 40 long | `nema17_motor` (body_length 40) | body 42.3 × 42.3 × 40; face plane `FACE`; pilot Ø22.0 × 2.0 high on `PILOT_AXIS`; shaft Ø5.0 × 24 on `SHAFT_AXIS`; `HOLE`: 4 axes on a 31.0 square, M3, thread depth 4.5, keep-out Ø5.5 for the screw head; `SHAFT_TIP` 24 from the face. Placed at the declared pose (shaft toward +X). |
| **M-BOLT-M3** | M3 socket-head screw | `bolt_m3_iso4762` | head Ø5.5 × 3.0, thread Ø3.0, clearance Ø3.4, counterbore Ø5.9 × 3.2, tap Ø2.5. Four, one per `HOLE`, length declared. |
| **M-BOLT-M4** | M4 socket-head screw | `bolt_m4_iso4762` | head Ø7.0 × 4.0, thread Ø4.0, clearance Ø4.5, counterbore Ø7.4 × 4.2. Two, one per flange hole. |
| **RA** | reference assembly | M-MOTOR ∪ 4 × M-BOLT-M3 at the declared poses | no printed geometry |

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-SHAFT** | the shaft through the bracket | the `shaft_path` keep-out: Ø5.0 cylinder from the face along `SHAFT_AXIS` to the tip (24 long). |
| **V-PILOT** | the pilot | Ø22.0 cylinder, 2.0 high, on `PILOT_AXIS` against the face (toward +X). |
| **V-MOTOR-BODY** | the motor's body | the box 42.3 × 42.3 × 40 behind the face. |
| **V-HEAD3-k** | M3 head | Ø5.5 × 3.0 cylinder on `HOLE`k with its bearing face on the counterbore floor (the declared length sets its depth). |
| **V-TOOL3-k** | hex-key access to an M3 screw | Ø5.5 cylinder from the head's top along +X, 25 long (the bolt's `tool_access` keep-out). |
| **V-TOOL4-j** | hex-key access to an M4 screw | Ø7.0 cylinder from the head's top along +Z, 25 long. |
| **V-INSTALL-MOTOR** | motor assembly path | M-MOTOR (body, pilot, shaft) swept along +X from 60 mm in front (−X) of its seated pose to the seat, minus the seating contact (face on plate, pilot in register). |
| **V-HOLE-AXES** | the printed holes | computed: through-holes of the delivered mesh found by slicing; axis, inscribed diameter, depth, counterbore. |
| **V-ROOT** | the bend's root section | the horizontal slice of the bracket at Z = (flange top) + R + 1.0 over the plate (R = the measured inside bend radius), giving area, centroid and moments of inertia. |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-MOTOR | units; body 42.3 × 42.3 × 40; shaft Ø5.0 × 24 | ± 0.2 |
| R2 | M-MOTOR | hole square and pilot | 31.0 ± 0.1; Ø22.0 ± 0.1 |
| R3 | M-MOTOR | shaft toward +X in the bracket frame | true |
| R4 | M-BOLT-M3/M4 | head and clearance diameters | as the catalogue ± 0.1 |
| R5 | RA | parts do not collide | intersection ≤ 0.01 mm³ |

**Seating rule.** The grader places M-MOTOR at the pose in `layout.json` and verifies: `FACE` lies
on the plate's motor-side face (distance ≤ 0.10, face covering the whole 42.3 square within the
plate's plan, or at least the four holes' neighbourhood), the four `HOLE` axes are coaxial with the
plate's four clearance holes (least-squares residual ≤ 0.25) and `PILOT_AXIS` is coaxial with the
register hole (≤ 0.15). If the declaration fails, the motor is re-seated by fitting its `FACE` and
`HOLE`s to the printed plate, and every L3 that needed the declaration fails.

---

## 3. Assumptions and open questions

| # | Question | Value chosen | Uncertainty / why |
|---|---|---|---|
| A1 | Which motor? | 17HS4401 class, body 42.3 square × 40 long, shaft Ø5 × 24 with a D flat, 31.0 pattern, pilot Ø22 × 2 (catalogue) | body length 34 / 40 / 48 exists; the request gives no length, so 40 (the catalogue default). Does not change any L3 except V-MOTOR-BODY. |
| A2 | Mass of the motor? | 0.35 kg | ± 0.1 kg. Used only for the dead-weight moment. |
| A3 | What does "survive about 20 N at the shaft" mean? | a static force of 20.0 N at `SHAFT_TIP`, radial (in any direction perpendicular to the shaft), plus the motor's weight; evaluated in the three axis directions, the worst counts | no fatigue, no impact. Axial pushes are smaller than the radial lever and are covered by the Z case. |
| A4 | Allowable stress? | 5.0 MPa on the bending stress at the bend's root = 15 MPa (the weaker, inter-layer strength of PLA) ÷ safety factor 3; stress concentration is covered by the factor | PLA tensile 40-60 MPa in-layer, 15-25 MPa across layers; ± 5 MPa. Uses the weak value whatever the orientation, so a wrong orientation cannot hide behind it. |
| A5 | Fit of the pilot in the register? | the register is Ø22.5 (given) on a Ø22.0 pilot, 0.25 per side; the band 0.15-0.35 per side is the generic sliding fit | FDM holes print 0.1 small; the band is the generic rule. |
| A6 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed | typical FDM tolerances. |
| A7 | Screw sizes? | M3 socket-head into the motor's tapped holes, heads counterbored; M4 socket-head through the flange, heads counterbored | brief names M4 for the flange; the motor holes are M3 (catalogue). |
| A8 | Where are the M4 holes? | on a line parallel to the bend axis, 40.0 apart, symmetric about the motor axis | brief: "two M4 holes 40 mm apart". |
| A9 | What bolts the flange down? | a flat base; the flange's underside is the mounting surface | not modelled. |
| A10 | Shaft room? | nothing printed within 3.0 of the shaft beyond the plate | a coupler or pulley fits over the shaft; its own envelope is the caller's part (catalogue note). |
| A11 | Edge distance? | at least 2.0 of material around every hole or counterbore | about 5 perimeters at 0.4 mm. |
| A12 | Print orientation for strength? | lying on a Y face, so the L profile is in the layer plane and the bend is one continuous layer; bed normal within 5° of Y | the common FDM rule for a bent load path. |

---

## 4. Fixed decisions (a choice would otherwise be ambiguous)

| # | Decision | Why |
|---|---|---|
| F1 | The flange extends toward the shaft side (+X); the motor body is on the other side of the plate. | keeps the motor's body away from the flange bolts and their tools. |
| F2 | The M3 screws go in from the shaft side (+X), heads counterbored; the motor is installed from −X. | the shaft passes through the face (brief). |
| F3 | One printed body; its flange underside is the mounting plane (Z = 0). | an L bracket is one part. |
| F4 | The M4 holes are counterbored from the flange's top face, so the heads do not stand proud. | lets another part rest on the flange; capability `counterbore`. |
| F5 | Print orientation: the bed normal is the bend axis (Y) within 5°; stated in `layout.json`. | brief: "so layers do not split at the bend". |
| F6 | The register may be a plain circle or a teardrop / diamond with its pointed side up in the print orientation; its largest inscribed circle is what counts. | a horizontal Ø22.5 hole would need support. |
| F7 | (the stock lengths are stated in the request) `layout.json` declares the motor pose (a 3 × 3 rotation sending motor +Z to +X and the origin of the motor frame), the lengths of the four M3 and two M4 screws (standard ISO 4762 lengths 6, 8, 10, 12, 16, 20, 25) and the print orientation. | needed by the seating rule and L2.4.3. |

---

## 5. Requirements tree

Columns: ID, requirement, method, pass/fail (with tolerance), weight, gate.

### L1.1 The motor, its screws and the load are declared against the bracket

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its motor pose, screw lengths and print orientation (F7). | inspection | `layout.json` parses; names `nema17_motor`, its pose, four M3 lengths, two M4 lengths | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 | |
| L2.1.2 | The shaft points through the face toward the flange side. | inspection | `SHAFT_AXIS` within 1.0° of +X; the motor body entirely on the −X side of the plate's motor-side face | 3 | |
| L3.1.2.1 | Shaft direction and body side. | inspection | angle ≤ 1.0° (+ 0.5° ε); body max X ≤ plate face X + 0.02 | 3 | |
| L2.1.3 | The motor axis lies on the bracket's mid-plane. | inspection | `SHAFT_AXIS` Y within 0.5 of the plate's Y mid-plane and of the flange hole pair's mid-point | 2 | |
| L3.1.3.1 | Motor axis offset in Y. | inspection | ≤ 0.5 | 2 | |

### L1.2 The vertical face takes the motor flat and without interference

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The motor face seats on the plate's motor-side face. | analysis | `FACE` within 0.10 of the plate face; contact patch ≥ 600 mm² (the face minus the register and the holes' neighbourhood) | 3 | G2 |
| L3.2.1.1 | Face-to-plate distance. | analysis | ≤ 0.10 | 3 | G2 |
| L3.2.1.2 | Plate-face flatness over the 42.3 square. | inspection | ≤ 0.20 | 2 | |
| L2.2.2 | Nothing else touches or enters the motor. | analysis | clear_of(BRACKET, V-MOTOR-BODY, 0.0) and clear_of(BRACKET, V-PILOT, 0.0) outside the register's wall (the pilot in the register is designed contact) | 3 | |
| L3.2.2.1 | Bracket clear of the motor body. | analysis | penetration ≤ 0.01 mm³ | 3 | |
| L2.2.3 | The plate's plan covers the motor's four holes and their screw keep-outs. | inspection | each `HOLE` keep-out Ø5.5 (and its counterbore) lies inside the plate outline with ≥ 2.0 of material to every edge | 2 | |
| L3.2.3.1 | Edge distances around the four holes. | inspection | ≥ 2.0 | 2 | |

### L1.3 A 22.5 mm register locates the motor's pilot

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The register hole is Ø22.5 and coaxial with the hole pattern. | inspection | largest inscribed circle Ø22.5 ± 0.15; radial gap to the pilot in [0.15, 0.35]; axis within 0.1 of the pattern's centre | 3 | |
| L3.3.1.1 | Register diameter and radial gap. | inspection | Ø in [22.35, 22.65]; gap (Ø − 22.0)/2 in [0.15, 0.35] | 3 | G2 |
| L3.3.1.2 | Register axis vs the pattern centre and the shaft axis. | inspection | offset ≤ 0.10 | 3 | |
| L2.3.2 | The pilot enters fully and the shaft passes through. | analysis | V-PILOT lies inside the register hole void (every point ≥ 0.10 from the hole's wall); clear_of(BRACKET, V-SHAFT, 3.0) | 3 | |
| L3.3.2.1 | Pilot inside the register. | analysis | d ≥ 0.10 | 3 | |
| L3.3.2.2 | Shaft clearance. | analysis | d ≥ 3.0 | 3 | |
| L2.3.3 | The register is deep enough to locate. | inspection | plate thickness at the register ≥ 2.0 (the pilot is 2.0 high) | 2 | |
| L3.3.3.1 | Register depth. | inspection | ≥ 2.0 | 2 | |

### L1.4 Four M3 holes on the 31 mm pattern fasten the motor, heads recessed

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Four holes on the motor's 31.0 square. | inspection | count 4; each axis within 0.15 of `HOLE`k; square 31.0 ± 0.15 | 3 | G2 |
| L3.4.1.1 | Hole count and axis offsets. | inspection | 4; each ≤ 0.15 | 3 | G2 |
| L3.4.1.2 | Pattern square. | inspection | 31.0 ± 0.15 along Y and Z | 3 | |
| L2.4.2 | Plain clearance holes with a counterbore from the +X face. | inspection | hole Ø3.4 ± 0.15 (inscribed); counterbore Ø 5.9-6.4; counterbore depth 3.2-4.0; web ≥ 2.0 | 2 | |
| L3.4.2.1 | Hole diameter. | inspection | in [3.25, 3.55] | 2 | |
| L3.4.2.2 | Counterbore diameter and depth. | inspection | Ø in [5.9, 6.4]; depth in [3.2, 4.0]; web = thickness − depth ≥ 2.0 | 2 | |
| L2.4.3 | The declared M3 screws fit: head recessed, thread engagement within the motor's limit. | analysis | head top recessed 0.2-1.0 below the +X face; engagement = L − web in [3.0, 4.5] | 2 | |
| L3.4.3.1 | Head recess. | analysis | counterbore depth − 3.0 in [0.2, 1.0] | 2 | |
| L3.4.3.2 | Thread engagement. | analysis | in [3.0, 4.5] | 2 | |
| L2.4.4 | Hex-key access to each M3 screw. | analysis | clear_of(BRACKET, V-TOOL3-1..4, 0.0) | 1 | |
| L3.4.4.1 | Tool columns clear. | analysis | d ≥ 0.0 | 1 | |

### L1.5 The shaft end passes through the face with room

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The shaft protrudes enough beyond the plate to carry a coupler or pulley. | inspection | free shaft length beyond the plate's +X face ≥ 15.0 (24 − plate thickness) | 2 | |
| L3.5.1.1 | Free shaft length. | inspection | ≥ 15.0 | 2 | |
| L2.5.2 | Nothing printed near the shaft beyond the plate. | analysis | clear_of(BRACKET minus the plate's own face, the shaft's Ø11 sleeve beyond the +X face, 0.0), i.e. flange top and fillet ≥ 3.0 from the shaft surface | 2 | |
| L3.5.2.1 | Sleeve clearance. | analysis | d ≥ 3.0 from the shaft's surface | 2 | |
| L2.5.3 | The motor installs from the −X side without hitting the bracket. | test | clear_of(BRACKET, V-INSTALL-MOTOR, 0.0) | 2 | |
| L3.5.3.1 | Installation path clear. | test | d ≥ 0.0 | 2 | |

### L1.6 The horizontal flange has two M4 holes 40 mm apart

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Two Ø4.5 holes, 40.0 apart, on a line parallel to the bend axis, symmetric about the motor axis. | inspection | count 2; centre distance 40.0 ± 0.2; line within 1.0° of Y; mid-point within 0.3 of the motor axis plane | 3 | G3 |
| L3.6.1.1 | Hole count and spacing. | inspection | 2; 40.0 ± 0.2 | 3 | G3 |
| L3.6.1.2 | Hole line direction and symmetry. | inspection | ≤ 1.0°; mid-point offset ≤ 0.3 | 2 | |
| L2.6.2 | Plain clearance holes with a counterbore from the top face. | inspection | hole Ø4.5 ± 0.15; counterbore Ø 7.4-7.9; counterbore depth 4.2-4.5; web ≥ 1.5 | 2 | |
| L3.6.2.1 | Hole diameter. | inspection | in [4.35, 4.65] | 2 | |
| L3.6.2.2 | Counterbore diameter, depth, web. | inspection | Ø in [7.4, 7.9]; depth in [4.2, 4.5]; web ≥ 1.5 | 2 | |
| L2.6.3 | Edge distances and tool access. | analysis | material ≥ 2.0 from each counterbore to the flange edges and the plate; clear_of(BRACKET, V-TOOL4-1..2, 0.0) | 2 | |
| L3.6.3.1 | Edge distances. | analysis | ≥ 2.0 | 2 | |
| L3.6.3.2 | Tool columns clear. | analysis | d ≥ 0.0 | 1 | |
| L2.6.4 | The flange underside is one flat plane. | inspection | flatness ≤ 0.2; nothing below it | 2 | |
| L3.6.4.1 | Underside planarity. | inspection | ≤ 0.20 | 2 | |

### L1.7 The bracket survives about 20 N at the shaft

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The bending stress at the bend's root is below the allowable (A3, A4). | analysis | σ = M / S ≤ 5.0 MPa, for F = 20 N at `SHAFT_TIP` in each of ±X, ±Y, ±Z plus the weight 0.35 kg at the body's centre; M from the measured lever (the vertical distance from `SHAFT_AXIS` to the flange top for X and Y; the horizontal distance from the section centroid to `SHAFT_TIP` for Z); S the section modulus of V-ROOT about the relevant axis | 3 | G5 |
| L3.7.1.1 | Worst root stress. | analysis | ≤ 5.0 MPa (+ 2 % ε) | 3 | G5 |
| L2.7.2 | The root has a fillet or gusset. | inspection | inside bend radius ≥ 2.0 (or a chamfer / gusset of at least 2.0) | 1 | |
| L3.7.2.1 | Inside corner radius. | inspection | ≥ 2.0 | 1 | |
| L2.7.3 | Plate and flange are thick enough to print stiff. | inspection | plate thickness 5.0-10.0; flange thickness 5.0-10.0 | 2 | |
| L3.7.3.1 | Plate and flange thickness. | inspection | in [5.0, 10.0] | 2 | |
| L2.7.4 | The flange bolts carry the lever. | analysis | bolt tension T = F · (lever) / (bolt distance from the plate's +X face) ≤ 200 N per M4 | 1 | |
| L3.7.4.1 | Bolt tension. | analysis | ≤ 200 N | 1 | |

### L1.8 It prints with layers that do not split at the bend

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The bed normal is the bend axis, so the L profile lies in the layer plane. | inspection | angle between the declared bed normal and Y ≤ 5.0° | 3 | G4 |
| L3.8.1.1 | Orientation angle. | inspection | ≤ 5.0° | 3 | G4 |
| L2.8.2 | In that orientation: no unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12 and bridges ≤ 15.0. | analysis | 0 offending faces of area > 1 mm² (the register is a circle ≤ 12 only if its Ø ≤ 12; at Ø22.5 it needs a pointed top, F6) | 2 | |
| L3.8.2.1 | Overhang and bridge scan. | analysis | as L2.8.2 | 2 | |
| L2.8.3 | The body rests on a face large enough to stand on. | analysis | bed contact ≥ 300 mm² and ≥ 30 % of the plan bounding box (an L lying on its side has about 32 %) | 1 | |
| L3.8.3.1 | Bed contact. | analysis | as L2.8.3 | 1 | |
| L2.8.4 | No feature thinner than 0.8; the body fits a 200 × 200 × 200 bed. | analysis | min thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 | |
| L3.8.4.1 | Thin features. | analysis | ≥ 0.8 | 1 | |
| L3.8.4.2 | Bounding box. | inspection | ≤ 200 per axis | 1 | |

### L1.9 The bracket is one clean printable solid

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The mesh is manifold and one shell. | analysis | 1 shell; manifold3d accepts it; no fragment | 3 | G1 |
| L3.9.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.9.2 | The body is a plate, a flange and nothing else. | inspection | no feature beyond the plate, flange, fillet, holes and counterbores that the L3s name; mass ≤ 3 × the plate-plus-flange envelope's mass | 1 | |
| L3.9.2.1 | Volume sanity. | inspection | volume ≤ 3 × (plate envelope + flange envelope) | 1 | |

### L1.10 It is small enough to use

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | The bracket's size is only what the motor and flange need. | inspection | X ≤ 40.0, Y ≤ 70.0, Z ≤ 70.0 (the motor's 42.3 square plus the flange) | 1 | |
| L3.10.1.1 | Bounding box. | inspection | as L2.10.1 | 1 | |
| L2.10.2 | The plate is tall enough to hold all four screws but not taller than the motor body plus 10. | inspection | plate height in [H_hole_top + 2.0, 42.3 + 10], H_hole_top = the highest point of any M3 counterbore (46.5 in the sketch) | 1 | |
| L3.10.2.1 | Plate height. | inspection | in range, from the measured hole positions | 1 | |

### L1.11 The package says what was built and where, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | The package holds `bracket.stl` (bracket frame, mm), the OpenSCAD source, `layout.json` (F7) and the agent's own report of the checks above. | inspection | all present and readable | 3 | G0 |
| L3.11.1.1 | Files present and parse; the body's largest bounding-box axis in 20-200 mm. | inspection | true | 3 | G0 |
| L3.11.1.2 | The declared motor pose verifies under the seating rule (section 2.3). | analysis | face ≤ 0.10; hole residual ≤ 0.25; pilot axis ≤ 0.15 | 3 | |
| L2.11.2 | The agent's own report agrees with the judge. | analysis | for every `clear_of` / `inside` / stress L3 the agent reports: same pass/fail and \|d_agent − d_judge\| ≤ 0.10 (stress within 10 %) | 1 | |
| L3.11.2.1 | Self-report vs judge. | analysis | 100 % agreement | 1 | |

---

## 6. Counts and gates

| Level | Count |
|---|---|
| L1 | 11 |
| L2 | 34 |
| L3 | 45 (weight 3: 16, weight 2: 18, weight 1: 11; 0 physical or human, optional) |

Every L3 is a measurement a Python script can make on the delivered STL (or on the declared
`layout.json` against the catalogue), except the rows marked physical or human.

Gates (a failure makes a design WRONG regardless of score): see section 9.

---

## 7. Feasibility

One design exists that meets every L3 above (bracket frame, mm):

- **Plate:** X 0-6, Y −26 to +26, Z 0-50 (52 wide, 6 thick, 50 tall). **Flange:** X 0-26, Y ±26,
  Z 0-6. **Inside corner** (X 6, Z 6): fillet R3. One body, volume about 52 × (6 × 50 + 20 × 6)
  ≈ 21.8 cm³ minus holes.
- **Motor pose:** `SHAFT_AXIS` through (X 0, Y 0, Z 28), shaft toward +X, face on X = 0. Body X −40 to
  0, Y ±21.15, Z 6.85-49.15 (under the plate's 50 top; nothing of the bracket is at X < 0).
- **Register:** through the plate at (Y 0, Z 28), inscribed Ø22.5 (gap to the pilot 0.25 per side),
  a circle with a pointed side toward +Y (45° flanks, apex 15.9 from the axis along +Y) so it prints
  without support: the bed normal is Y, so +Y is "up" in the print and the hole axis X is horizontal; depth 6 ≥ 2.0.
- **M3 holes:** Ø3.4 at (Y ±15.5, Z 12.5 and 43.5), with Ø6.0 counterbores 3.4 deep from the +X
  face (head 3.0, recess 0.4; web 2.6). Declared screws M3 × 6: engagement 6 − 2.6 = 3.4 ∈ [3.0,
  4.5]. Edge distances: lowest cb edge Z 9.5 (fillet ends at Z 9), side edge 26 − 18.5 = 7.5, top
  edge 50 − 46.5 = 3.5 (all ≥ 2.0). Tool columns run along +X from the face at Z ≥ 9.75: above the
  flange top (Z 6) and its fillet, so clear.
- **Flange holes:** Ø4.5 at (X 20, Y ±20), spacing 40.0; counterbores Ø7.6 × 4.3 deep from the top
  (web 1.7 ≥ 1.5); edge distances: to the flange end 26 − 23.8 = 2.2, to the side 26 − 23.8 = 2.2,
  to the plate's +X face 20 − 6 − 3.8 = 10.2 (all ≥ 2.0). Tool columns run up along +Z and are
  clear (the shaft is at Y 0, 14 away from them).
- **Shaft:** free length 24 − 6 = 18 ≥ 15; the flange top (Z 6) is 28 − 2.5 − 6 = 19.5 below the
  shaft's surface (≥ 3.0); the fillet's end (X 9, Z 6) is farther.
- **Load:** root section at Z = 6 + 3 + 1 = 10: gross 52 × 6, S = 52 × 6² / 6 = 312 mm³ about Y; the
  lower counterbores cut that slice with two notches 3.3 wide and 3.4 deep, so the net S is about
  290 mm³. For F = 20 N along X at the tip: lever 28 − 6 = 22 mm → M = 440 N·mm; the weight 3.4 N at
  the body's centre (X −20): 68 N·mm, same sense in the worst case; M = 508 N·mm; σ = 1.75 MPa
  ≤ 5.0 (margin 2.9×). Along Z: 20 N × (24 − 3) = 420 N·mm plus 68: 1.68 MPa. Along Y: in-plane bending, S = 6 × 52² / 6
  = 2704 mm³, M = 440: 0.16 MPa. Bolt tension: 20 × 22 / 14 = 31 N ≤ 200.
- **Printing:** bed normal Y (bed on the Y = −26 face): footprint = the L, 6 × 50 + 20 × 6 = 420 mm²
  (32.3 % of the 26 × 50 bounding box ≥ 30 %, ≥ 300 mm²); every hole axis is horizontal: Ø3.4,
  Ø6.0, Ø4.5 and Ø7.6 are ≤ 12, the register has its pointed top; the fillet and the flat faces
  have no overhang; the layers are L-shaped slices, so nothing splits at the bend.
- **Size:** 26 × 52 × 50 (limits 40, 70, 70).

This sketch is one satisfiable design; it is not the only one and is never given to the agent.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 (`design.json`) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Declared pose | L2.1.1-L2.1.3 | L3.1.1.1, L3.1.2.1, L3.1.3.1 | L1.1 | inspection | "shaft end passes through the face" |
| L1.2 | Motor seats on the face | L2.2.1-L2.2.3 | L3.2.1.1-2, L3.2.2.1, L3.2.3.1 | L1.2 | analysis | "vertical face takes the motor" |
| L1.3 | Pilot register | L2.3.1-L2.3.3 | L3.3.1.1-2, L3.3.2.1-2, L3.3.3.1 | L1.3 | inspection | "22.5 mm pilot register" |
| L1.4 | M3 pattern | L2.4.1-L2.4.4 | L3.4.1.1-2, L3.4.2.1-2, L3.4.3.1-2, L3.4.4.1 | L1.4 | inspection | "31 mm pattern" |
| L1.5 | Shaft through | L2.5.1-L2.5.3 | L3.5.1.1, L3.5.2.1, L3.5.3.1 | L1.5 | analysis | "motor shaft end passes through the face" |
| L1.6 | Flange holes | L2.6.1-L2.6.4 | L3.6.1.1-2, L3.6.2.1-2, L3.6.3.1-2, L3.6.4.1 | L1.6 | inspection | "horizontal flange has two M4 holes 40 mm apart" |
| L1.7 | Strength | L2.7.1-L2.7.4 | L3.7.1.1, L3.7.2.1, L3.7.3.1, L3.7.4.1 | L1.7 | analysis | "survive about 20 N at the shaft" |
| L1.8 | Print orientation | L2.8.1-L2.8.4 | L3.8.1.1, L3.8.2.1, L3.8.3.1, L3.8.4.1-2 | L1.8 | analysis | "orient it so layers do not split at the bend" |
| L1.9 | Clean solid | L2.9.1-L2.9.2 | L3.9.1.1, L3.9.2.1 | L1.9 | analysis | implied (OpenSCAD to STL) |
| L1.10 | Size | L2.10.1-L2.10.2 | L3.10.1.1, L3.10.2.1 | L1.10 | inspection | implied |
| L1.11 | Evidence | L2.11.1-L2.11.2 | L3.11.1.1-2, L3.11.2.1 | L1.11 | inspection | needed by the judge |

## 9. Grading procedure for G17

`benchmarks/generalize/rubric.md` did not exist when this file was written, so this section is the design-specific rubric (units, frames, recipes, classes, defect reports). If a generic rubric.md appears later it governs generic rules; this section still governs everything specific to G17.

1. **Package gate (G0).** The files of the last L1 must exist and load. If a delivered STL is
   missing or unreadable, stop: verdict DOES NOT MEET, one defect on the G0 L3.
2. **Units.** Load each STL; the largest bounding-box axis of bracket.stl must be 20-200 mm
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

Gates: G0 package (L3.11.1.1); G1 manifold and one shell (L3.9.1.1); G2 motor seats on its face with the register and the four M3 holes (L3.2.1.1, L3.3.1.1, L3.4.1.1); G3 flange holes (L3.6.1.1); G4 print orientation (L3.8.1.1); G5 the bracket survives the 20 N load (L3.7.1.1).

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

Adversarial audit of this entry, 2026-10-24. Recomputed from `nema17_motor`, `bolt_m3_iso4762`,
`bolt_m4_iso4762` and the section 7 sketch: holes at Y ±15.5, Z 12.5 / 43.5 about the axis at Z 28 (31.0
square); web 6 − 3.4 = 2.6 and engagement 6 − 2.6 = 3.4; recess 3.4 − 3.0 = 0.4; flange web 6 − 4.3 =
1.7; edge distances 3.5 / 7.5 / 2.2; shaft free length 24 − 6 = 18; root stress for F = 20 N plus 3.43 N
about 1.8 MPa (X, worst), 1.7 MPa (Z), 0.2 MPa (Y) against 5.0, bolt tension 31 N against 200; bed
contact about 420 mm² = 32 % of 26 × 50. The sketch satisfies every gate and L3 once fix 1 is applied.
All catalogue ids load. L1 count 11; L2 34, L3 45 with weights 16 / 18 / 11.

| # | Finding | Fix |
|---|---|---|
| 1 | The register was drawn with its pointed side at +Z, but the stated print orientation has the bed normal along Y with the hole axis X horizontal, so "up" in the print is +Y. A teardrop pointing +Z would still overhang. | Section 7 now puts the apex 15.9 from the axis along +Y (45 degree flanks, clear of the M3 holes by more than 7 mm). F6 already said "pointed side up in the print orientation". |
| 2 | The motor's mass (0.35 kg, A2) is needed for "plus the motor's weight" but was not in the request or any L1. | Request now says "The motor weighs 0.35 kg". |
| 3 | `bolt_m3_iso4762` and `bolt_m4_iso4762` take `length` from the request, which gave no screw lengths; F7's stock lengths were hidden. | Request names the ISO 4762 screws and the stock lengths 6, 8, 10, 12, 16, 20, 25 mm. |
| 4 | "Two M4 holes 40 mm apart" did not say on which line; L2.6.1 grades "within 1.0 degree of Y" (parallel to the bend, A8). Also the motor's square orientation (axis-aligned, L3.4.1.2) was implicit. | Request and L1.6 now say "on a line parallel to the bend"; L1.1 says the motor's square faces are parallel and perpendicular to the flange. |
| 5 | Judge-needed numbers appeared only in L2/L3: recess 0.2-1.0 (L1.4), plate and flange thickness 5-10 and bolt tension 200 N (L1.7), bed contact 300 mm² and 30 % (L1.8), no extra features (L1.9), plate height limits (L1.10). | Added to the matching L1 texts in `design.json`. |
| 6 | L2.10.2 used `H_hole_top` without defining it. | Defined as the highest point of any M3 counterbore (46.5 in the sketch; the plate 50 is within [48.5, 52.3]). |

Observation: the weight moment uses the 20 mm lever to the motor's centre in the sketch (68 N mm); with the
23 mm lever from the section centroid it is 79 N mm and the worst stress is 1.84 MPa, still far below 5.0.
