# G18 608 bearing split pillow block: requirements (L1 / L2 / L3)

A generalisation design for the OpenSCAD assembly agent, modelled on E1-01
(`benchmarks/enclosure/requirements.md`): catalogue parts (a bearing, M3 and M4 bolts, an M3 nut)
placed from datums, two printed bodies that close on a split plane, a press/clamp fit judged on the
closed bore, captive nuts, a mounting pattern, and interference and clearance checks against
reference models. The machine-readable request (L1 only, `dev.json` format) is `design.json` next
to this file. How a blind judge applies this document is in section 7.

**Plan brief (verbatim):** "A two-piece pillow block for a 608 bearing (8 x 22 x 7 mm) that is
clamped, not glued. Two M3 bolts with captive hex nuts pull the halves together, and the bearing bore
pocket should be about 0.1 mm under 22 mm so the clamp holds it. The base has two M4 mounting holes
40 mm apart."

**How to read this.** L1 says what the owner needs, L2 turns it into an engineering requirement with
numbers, L3 is a concrete check Python can run on the delivered STLs. Every row has a method
(inspection, analysis, demonstration, test, human, as in `design.json`), a pass/fail criterion with a
number and a tolerance, and a weight (3 = critical, 2 = major, 1 = minor). A `G<n>` after the weight
marks a gate: a failed gate makes the design WRONG (section 5). Every number that comes from an
assumption (section 3) is provisional until the owner confirms it. Do not relax a criterion because
the agent fails it.

---

## 1. Frames, tolerances and the two interference checks

### 1.1 Frame

- **Block frame:** the bearing axis is **Y**. The **split plane is Z = 0** and contains the axis:
  the **base is below** it (Z <= 0) and the **cap above** (Z >= 0). X is across the block. The origin
  is on the bearing axis at the middle of the pocket (Y = 0). The base's underside, the mounting
  face, is its lowest Z (about -14).
- STLs are delivered in this closed pose, mm. A design delivered mirrored or rotated by multiples of
  90 degrees is normalised into this frame before grading; that is never penalised. The judge
  records the transform.

### 1.2 Measurement tolerances

| Quantity | Tolerance e | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within e |
| angle | 0.5 degrees | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3, except where a row gives a designed-interference band |
| hole / pocket diameter | largest inscribed circle of the section (what the bolt or bearing sees) | |
| bore diameter | mean of the radial distance to the surface, 72 rays at 5 degree steps at Y = 0 in the closed pose, times 2 | |

### 1.3 The two interference checks

- **`clear_of(bodies, volume, clearance)`**: the minimum distance between every printed body in
  `bodies` and `volume` is >= `clearance`; reported as the signed minimum distance d (negative =
  penetration, with the volume). Pass: d >= clearance - e.
- **`inside(volume, solid, clearance)`**: `volume` lies in the region and is >= `clearance` from its
  boundary.

`bodies` is **ALL** (base and cap closed), **BASE** or **CAP**. A design never builds or edits the
reference volumes: the grader builds them from the catalogue and the declared hardware layout.

**Designed contact for this design.** Parts that are meant to touch are excluded from every
interference and clearance check; for these pairs only a penetration above the stated band counts:
- **the bearing in the closed bore**: a designed radial interference of about 0.05 per side. The
  intersection of M-BRG with BASE and CAP together must lie in the band of L3.2.1.2 (about 24 mm3 for
  the nominal 21.9 pocket); any intersection outside the bore (lips, bolt holes) is interference;
- the bearing's end faces against the lip faces;
- the base and the cap on the split plane (D1);
- a bolt in its clearance holes (none expected) and its thread in the nut; the bolt head on its
  counterbore floor;
- a nut on its pocket floor and against the pocket walls; the nut under the cap;
- an M4 bolt in its hole and on its bearing face.

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue** (`benchmarks/generalize/parts/`): `bearing_608`, `bolt_m3_iso4762`, `nut_m3`,
  `bolt_m4_iso4762`. These are the only place part numbers may live.
- **envelope:** swept or offset volumes made by Python from datums. Never drawn by hand.
- **computed:** surfaces and regions measured on the delivered STLs (closed bore, pockets).

### 2.2 Reference models (M-)

Placed by the grader from the layout the design declares and cross-checked against the STLs.
Block frame, mm.

| Name | What | Source | Size and default position | Datums |
|---|---|---|---|---|
| **M-BRG** | 608 bearing | `bearing_608` | cylinder 22.0 outer, 8.0 bore, 7.0 wide, axis along Y, centred at the pocket centre (0, 0, 0), faces at Y -3.5 and +3.5 | `AXIS`, `FACE_A`, `FACE_B`, `CENTRE` |
| **M-BOLT-k** (k = 1, 2) | M3 clamp bolt | `bolt_m3_iso4762` | head dia 5.5 x 3.0, shank 3.0, length declared in the layout (stock length, A4); axis along Z, head up, head bearing on the counterbore floor | `AXIS`, `HEAD_BEARING`, `HEAD_TOP`, `TIP` |
| **M-NUT-k** | M3 hex nut | `nut_m3` | true hexagonal prism, 5.5 across flats, clipped by a dia 6.01 circle, 2.4 thick, seated on the pocket floor, axis on the bolt axis, rotated to the pocket's hexagon | `AXIS`, `SEAT`, `TOP` |
| **M-M4-j** (j = 1, 2) | M4 mounting bolt | `bolt_m4_iso4762` | head dia 7.0 x 4.0, shank 4.0, length declared; axis along Z, head up, head bearing on the counterbore floor or the plate top | as M-BOLT |
| **RBA** | reference block assembly = M-BRG, M-BOLT-1..2, M-NUT-1..2, M-M4-1..2 | assembled | as above | all |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Definition (block frame, mm) |
|---|---|---|
| **V-BORE** | free bore for the shaft and the inner ring | dia 13.0 cylinder along Y from Y = -30 to +30, centred on the bearing axis (inner ring about dia 12.6, A2) |
| **V-HEX3-k** | hex-key column over each M3 head | dia 5.5 from the head top to 25 above it |
| **V-TOOL4-j** | hex-key column over each M4 head | dia 7.0 from the head top to 25 above it (the catalogue `tool_access`) |
| **V-NUT-PATH-k** | nut drop-in path | the nut's hexagonal outline swept straight down (-Z) from 40 above the split plane to the seated pose |
| **V-BRG-PATH** | bearing drop-in path | M-BRG swept straight down from 40 above to the seated pose (axis pressed to Z = +0.05; unpressed it would rest on the trough edges at about Z = +1.05) |
| **V-BOLT-k** | bolt shank path | dia 3.0 shank from the head bearing to the tip |
| **V-CLAMP** | the clamp region | the pocket section at Y = 0 in the closed pose (computed) |
| **V-SPLIT** | the split-plane contact region | the faces of BASE and CAP within 0.10 of Z = 0 |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-BRG | units and size | 22.0 x 22.0 x 7.0 +/-0.1; bore 8.0 |
| R2 | M-NUT | size | across flats 5.5, thickness 2.4 +/-0.1 |
| R3 | M-BOLT, M-M4 | head and shank sizes | M3: 5.5 x 3.0, 3.0; M4: 7.0 x 4.0, 4.0 (+/-0.2) |
| R4 | RBA | models do not collide with each other | intersection <= 0.01 mm3 |
| R5 | V- envelopes | datums equal the model datums | <= 0.01 |

**Seating rule.** Each reference part is placed at the pose declared in the layout. The grader
verifies it: every `HEAD_BEARING` lies on its counterbore floor or its seat face (distance <= 0.10),
every nut `SEAT` on its pocket floor (<= 0.10), and each bolt axis is coaxial with its holes
(residual <= 0.20). If the declaration is missing or fails, the parts are seated by that fit instead.

---

## 3. Assumptions (A) and fixed decisions (D)

Each A-row gives the value chosen and the uncertainty. **A1, A2 and A3 matter most.**

| # | Question | Value chosen | Why / uncertainty |
|---|---|---|---|
| **A1** | What does "bore pocket about 0.1 under 22" mean for a split block? | (The catalogue's `HOUSING_BORE` datum is 22.1, a drop-in convention; the request says 0.1 under, which wins here.) The pocket's diameter, measured with the halves **closed on the split plane**, is **21.9** (band 21.85 to 21.95). The 22.0 bearing is squeezed by 0.10 across (0.05 per side). | The clamp holds because the closed bore is smaller than the bearing. **Uncertainty: medium.** A printed bore comes out 0.1 to 0.2 small or large; print a test ring. |
| **A2** | What must the pocket do besides squeeze? | Hold the bearing axially with two lips on the **outer ring** and leave the **inner ring free**. Inner ring about dia 12.6 and outer-ring inner edge about dia 17.4 (608 catalogue, +/-0.5); lips have inner dia 15.0 to 17.0. Axial pocket length 7.0 to 7.4. | `bearing_608` notes: the shoulder must sit on the outer ring and nothing printed may enter the bore. The catalogue's shoulder rule (radius at least 4 + (22 - 8) / 4 = 7.5, i.e. dia 15.0; read as dia 11.5 it is weaker) is met under either reading by the 15.0 floor. **Uncertainty: medium.** |
| **A3** | What is the split plane and how do the halves go together? | The plane contains the bearing axis; the base is the lower half and carries the mounting plate; the cap is the upper half; two M3 bolts, **one on each side of the bearing**, go from the cap down into nuts in the base. | The usual pillow-block form; the brief's "base" implies it. **Uncertainty: low.** |
| **A4** | Bolt lengths? | Declared by the design in the layout (stock length). M3 tip must pass the nut's far face by 0.5 to 4.0; the M4 length is declared and graded only for fit (L3.12.1.2). | The request gives no length; the catalogue says lengths are chosen per design. **Uncertainty: low.** |
| **A5** | Nut pocket sizes? | Hexagon across flats 5.70 to 5.95 (nut 5.5 + 0.2 to 0.45 slip clearance), depth 2.4 to 2.8 (nut 2.4 + up to 0.4), open to the split face. | `nut_m3` `trap_clearance` 0.2, `pocket_depth` 2.6; the 5.95 upper limit keeps the nut from spinning (it is blocked within 20 degrees). **Uncertainty: medium** (printer). |
| **A6** | Bolt hole and counterbore sizes? | M3 clearance dia 3.3 to 3.5 (ISO 273 medium 3.4); counterbore dia 5.7 to 6.1 and depth 3.0 to 3.4 (head dia 5.5 + 0.4, head 3.0 + 0.2). M4 clearance dia 4.4 to 4.7 (ISO 273 4.5); optional counterbore dia 7.2 to 7.8, depth 4.0 to 4.6. | Catalogue `clearance_diameter`, `counterbore_*` (assumed +/-0.2). **Uncertainty: low.** |
| **A7** | Load? | 100 N radial on the bearing, taken as a pull up and out (worst case for the mounting bolts); PLA allowable bending stress for the plate section 10 MPa (layer adhesion, with margin). | A 608 on a small shaft carries tens of N. **Uncertainty: high;** confirm the real load. |
| **A8** | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed, no supports. Orientation stated by the design. A clamp block with the parting face up prints best for the cap. | Common printers. |
| **A9** | Maximum size? | Closed block <= 60 x 60 x 32 (X x Y x Z). | A tight design is about 45 x 52 x 28. |
| A10 | Wall thickness? | At least 2.0 on every ligament; at least 2.5 between the bore and any outer surface. | 5 perimeters at 0.4 line width. |
| A11 | Bearing and shaft details? | The shaft is free (not modelled), bore dia 8, retained by nothing here. | Not in the brief. |

| # | Fixed decision (a choice that would otherwise be ambiguous) |
|---|---|
| **D1** | **Closed pose:** the base's split face and the cap's split face meet on Z = 0 (gap 0 to 0.05). The bearing's axis lies on that plane. |
| **D2** | The pocket diameter (A1) is measured in the closed pose; the bearing's resting height in the base alone (axis at Z = +0.05 pressed, +1.05 unpressed) is not graded. |
| **D3** | **The two M4 mounting holes are 40.0 apart along the bearing axis (Y)**, symmetric about the pocket centre (Y = +/-20.0), at X = 0 (+/-0.5) in the base's mounting plate, vertical (parallel to Z). |
| **D4** | The nuts sit in hex pockets in the base, **open to the split face**; the cap closes them. The nut is inserted from above before the cap is placed. |
| **D5** | The M3 bolts go **downward**: head in a counterbore in the cap's top face, thread into the nut in the base. Both are at Y = 0. |
| **D6** | Print orientation is stated in the layout. Default: base mounting face down; cap flipped, top face down, split face up. |

---

## 4. Requirements tree

### L1.1 Two separate bodies, split along a plane through the bearing axis

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.1.1 | Exactly two printed bodies, base and cap. | inspection | 2 STLs; 1 shell each | 3 G1 |
| L3.1.1.1 | Body count and shells per body. | inspection | 2; 1 shell each | 3 G1 |
| L2.1.2 | The split plane contains the bearing axis (D1). | inspection | plane offset from the pocket axis <= 0.3; plane normal perpendicular to the axis within 1.0 degrees | 3 |
| L3.1.2.1 | Distance from the bearing axis to the split plane; angle between the axis and the plane. | inspection | <= 0.3; <= 1.0 degrees | 3 |
| L3.1.2.2 | Each body lies on its own side of the plane. | inspection | base max Z <= +0.05; cap min Z >= -0.05 | 2 |
| L2.1.3 | Closed, the bodies meet on the plane without overlapping. | analysis | BASE and CAP intersection <= 0.01 mm3 | 3 |
| L3.1.3.1 | Base and cap do not interpenetrate when closed. | analysis | <= 0.01 mm3 | 3 G1 |

### L1.2 Closed, the pocket is 21.9 mm across, round and centred

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.2.1 | Closed bore diameter 21.9 (A1). | analysis | mean bore diameter at Y = 0 | 3 G2 |
| L3.2.1.1 | Closed bore diameter (72 rays, 5 degree steps; mean radius x 2). | analysis | 21.85 to 21.95 | 3 G2 |
| L3.2.1.2 | Designed interference: M-BRG intersected with BASE and CAP together. | analysis | 10 to 40 mm3 (nominal 24 for 21.9); no intersection outside the bore | 2 |
| L2.2.2 | The pocket is round and on the axis. | analysis | out of round <= 0.10; axis offset <= 0.15 | 3 |
| L3.2.2.1 | Offset of the pocket axis from the declared bearing axis (X and Z). | analysis | <= 0.15 | 3 |
| L3.2.2.2 | Out of round: max radius - min radius over the 72 rays. | analysis | <= 0.10 | 2 |
| L2.2.3 | The pocket holds the 7 mm bearing axially (A2). | inspection | axial length between the lip faces 7.0 to 7.4; lips coplanar in both halves | 3 |
| L3.2.3.1 | Axial pocket length (distance between the two lip faces, mid-height). | inspection | 7.0 <= L <= 7.4 | 3 |
| L3.2.3.2 | Lip faces of base and cap coplanar. | inspection | each lip face's Y within 0.10 between the halves | 2 |
| L3.2.3.3 | Pocket centred on the block. | inspection | pocket centre Y within 0.3 of the block's centre Y | 1 |

### L1.3 The bearing's outer ring is held by lips; the inner ring and the bore are free

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.3.1 | Two lips, one at each end of the pocket, on the outer ring (A2). | inspection | lip inner dia 15.0 to 17.0; lip thickness 1.5 to 3.0; in both halves | 3 |
| L3.3.1.1 | Lip inner diameter (closed, both ends). | inspection | 15.0 to 17.0 | 3 |
| L3.3.1.2 | Lip thickness along the axis (both ends). | inspection | 1.5 to 3.0 | 2 |
| L2.3.2 | Nothing printed enters the bore volume. | analysis | clear_of(ALL, V-BORE, 0.0) | 3 |
| L3.3.2.1 | Free bore. | analysis | d >= 0.0 | 3 |
| L2.3.3 | The bearing does not touch the printed block except on its outer cylinder and end faces. | analysis | M-BRG intersection with ALL outside the bore pocket and lip end faces <= 0.01 mm3 | 2 |
| L3.3.3.1 | Bearing intersection outside the designed contact. | analysis | <= 0.01 mm3 | 2 |

### L1.4 The halves touch on the split plane, so the bolts clamp onto the bearing

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.4.1 | Closed gap on the split plane. | analysis | median over V-SPLIT <= 0.05; max <= 0.10 | 3 G3 |
| L3.4.1.1 | Gap between base and cap split faces, 1 mm grid. | analysis | median <= 0.05; max <= 0.10 | 3 G3 |
| L2.4.2 | The contact area is real. | analysis | contact area (faces within 0.05) | 2 |
| L3.4.2.1 | Split-face contact area. | analysis | >= 100 mm2 | 2 |

### L1.5 Two M3 bolts pass through counterbored holes in the cap into the base

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.5.1 | Two bolt axes, one on each side of the bearing, vertical (D5). | inspection | perpendicular to the split plane within 1.0 degrees; symmetric about the pocket axis | 3 |
| L3.5.1.1 | Bolt axis direction. | inspection | within 1.0 degrees of Z | 2 |
| L3.5.1.2 | Symmetry and pitch. | inspection | sum of the two X offsets <= 0.3; both at Y = 0 +/-0.3; pitch 28.0 to 40.0 | 3 |
| L2.5.2 | Clearance holes and counterbores in the cap (A6). | inspection | as the rows | 3 |
| L3.5.2.1 | Clearance hole diameter, each, through the cap. | inspection | 3.3 to 3.5 | 3 |
| L3.5.2.2 | Counterbore diameter and depth, each. | inspection | dia 5.7 to 6.1; depth 3.0 to 3.4 | 2 |
| L3.5.2.3 | Head top against the cap top surface. | analysis | M-BOLT `HEAD_TOP` at or below the cap's top surface (offset -0.4 to 0.0) | 2 |
| L2.5.3 | Material round the holes (A10). | analysis | ligament from every hole, counterbore and nut pocket to the bore, to outer faces and to each other >= 2.0 | 2 |
| L3.5.3.1 | Minimum ligament round the bolt features. | analysis | >= 2.0 | 2 |
| L2.5.4 | The bolt lies in its holes and reaches the nut. | analysis | M-BOLT intersection with BASE and CAP; tip beyond the nut | 3 |
| L3.5.4.1 | Bolt shank intersection with the printed bodies outside the nut. | analysis | <= 0.01 mm3 | 3 |
| L3.5.4.2 | Tip position: beyond the nut's far face and inside the base hole. | analysis | tip 0.5 to 4.0 beyond the nut's far face; hole floor below the tip >= 0 | 2 |

### L1.6 Each bolt threads into an M3 hex nut held captive in a pocket in the base

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.6.1 | Two hex pockets in the base, open to the split face, coaxial with the bolts (D4, A5). | inspection | as the rows | 3 |
| L3.6.1.1 | Pocket count. | inspection | 2 (one per bolt) | 3 |
| L3.6.1.2 | Pocket across flats. | inspection | 5.70 to 5.95 | 3 |
| L3.6.1.3 | Pocket depth from the split plane. | inspection | 2.4 to 2.8 | 3 |
| L3.6.1.4 | Pocket axis against the bolt axis. | inspection | <= 0.2 | 3 |
| L2.6.2 | The nut is held: seated, cannot fall out, cannot turn. | test | as the rows | 3 G5 |
| L3.6.2.1 | M-NUT in its pocket: intersection with BASE, and nut top against the split plane. | analysis | <= 0.01 mm3; nut top Z <= +0.05 | 3 |
| L3.6.2.2 | Captive: `slide(nut, +0.5 along Z)` with the cap on intersects the cap; `slide(nut, 1.0)` in each of +X, -X, +Y, -Y and -Z intersects the base. | test | all six intersect (> 0.01 mm3) | 3 G5 |
| L3.6.2.3 | No spin: rotate the nut about its axis by 20 degrees in each sense. | test | both intersect the pocket walls | 2 |
| L2.6.3 | The nut drops into its pocket from above with the cap off. | test | clear_of(BASE, V-NUT-PATH-k, 0.0) | 2 |
| L3.6.3.1 | Nut drop-in path clear. | test | d >= 0.0 | 2 |

### L1.7 The base has two M4 mounting holes 40.0 mm apart

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.7.1 | Two holes through the mounting plate, vertical, 40.0 apart along the bearing axis (D3). | inspection | as the rows | 3 G4 |
| L3.7.1.1 | Hole count and axis direction. | inspection | 2; within 1.0 degrees of Z | 3 |
| L3.7.1.2 | Hole pitch. | inspection | 40.0 +/-0.2 | 3 G4 |
| L3.7.1.3 | Symmetry about the pocket centre. | inspection | centre of the pair within 0.3 of Y = 0 and 0.5 of X = 0 | 2 |
| L2.7.2 | The holes pass an M4 bolt, with room for its head (A6). | inspection | as the rows | 3 |
| L3.7.2.1 | Hole diameter (through section). | inspection | 4.4 to 4.7 | 3 |
| L3.7.2.2 | Counterbore, if present. | inspection | dia 7.2 to 7.8; depth 4.0 to 4.6 | 1 |
| L2.7.3 | Hex-key access and material under the head. | analysis | as the rows | 2 |
| L3.7.3.1 | Tool columns clear: clear_of(ALL, V-TOOL4-1..2, 0.0). | analysis | d >= 0.0 | 2 |
| L3.7.3.2 | Material under each M4 head (head bearing face to the plate underside). | analysis | >= 2.0 | 2 |

### L1.8 With the cap off the bearing and nuts drop in; with it on every bolt is reachable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.8.1 | The bearing drops into the base half. | test | V-BRG-PATH against BASE | 2 |
| L3.8.1.1 | Bearing drop-in path: intersection of V-BRG-PATH with BASE. | test | <= 40 mm3 in the pocket (designed interference); 0 elsewhere (<= 0.01 mm3 on the lips) | 2 |
| L2.8.2 | Every bolt can be turned with a hex key. | analysis | clear_of(ALL, V-HEX3-1..2, 0.0) | 2 |
| L3.8.2.1 | M3 key columns clear. | analysis | d >= 0.0 | 2 |
| L2.8.3 | The cap comes off by lifting it after the M3 bolts are out. | test | slide(cap, +40 along Z) against BASE | 2 |
| L3.8.3.1 | Cap lift path clear. | test | intersection <= 0.01 mm3 at every 1 mm step | 2 |

### L1.9 The load reaches the mounting holes through solid material

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.9.1 | Walls round the bore (A10). | inspection | at least 2.5 between the bore and any outer surface of either body | 2 |
| L3.9.1.1 | Minimum wall between the closed bore (at Y = 0) and the outside, rays every 5 degrees, excluding the bolt zones. | inspection | >= 2.5 | 2 |
| L3.9.1.2 | Ligament round every M4 hole or counterbore, to the plate edges. | analysis | >= 2.0 | 2 |
| L2.9.2 | The path from the bearing block to the mounting holes is solid. | analysis | section area along the base | 3 |
| L3.9.2.1 | Minimum cross-section area of the base on planes Y = const between the block's end face and each M4 hole. | analysis | >= 100 mm2 | 3 |
| L3.9.2.2 | Bending: 100 N upward at the bearing centre, reacted equally at the two M4 holes (50 N each); bending moment at the block's end face = 50 N x (hole Y - block half-length); section modulus of the base section 1 mm outside the block. | analysis | stress <= 10 MPa | 2 |
| L2.9.3 | The base is one connected body. | analysis | 1 shell | 3 |
| L3.9.3.1 | Base connected. | analysis | 1 shell | 3 |

### L1.10 Both bodies print on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.10.1 | Each body is manifold and one shell. | analysis | manifold3d accepts it; 1 shell | 3 G1 |
| L3.10.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 G1 |
| L2.10.2 | In its stated orientation (D6) no body has an unsupported overhang steeper than 45 degrees from vertical, except round holes <= 12.0 in vertical walls and bridges <= 15.0. | analysis | 0 offending faces (area > 1 mm2) | 2 |
| L3.10.2.1 | Overhang and bridge scan per body. | analysis | as L2.10.2 | 2 |
| L2.10.3 | Each body rests on a flat face. | analysis | bed contact >= 50% of the plan bounding box | 1 |
| L3.10.3.1 | Bed contact per body. | analysis | >= 50% | 1 |
| L2.10.4 | No feature thinner than 0.8; mating clearances >= 0.15 (except the designed pocket interference). | analysis | thin-feature scan | 1 |
| L3.10.4.1 | Thin features and gaps. | analysis | min wall >= 0.8 | 1 |
| L2.10.5 | Each body fits 200 x 200 x 200. | inspection | bbox <= 200 per axis | 1 |
| L3.10.5.1 | Bounding box per body. | inspection | <= 200 | 1 |

### L1.11 Compact, with a flat mounting face, stable on a bench

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.11.1 | Closed outside size <= 60 x 60 x 32. | inspection | X <= 60.0, Y <= 60.0, Z <= 32.0 | 1 |
| L3.11.1.1 | Assembly bounding box. | inspection | as L2.11.1 | 1 |
| L2.11.2 | The mounting face is flat. | inspection | flatness <= 0.2; contact area >= 50% of the plan bounding box | 1 |
| L3.11.2.1 | Underside planarity and contact. | inspection | as L2.11.2 | 1 |
| L2.11.3 | It rests on the mounting face without tipping. | analysis | stable at 5 degrees tilt, mass = volume x 0.45 g/cm3 plus 12 g for the bearing | 1 |
| L3.11.3.1 | Centre of mass inside the support polygon at 5 degrees tilt in every direction. | analysis | margin >= 0 | 1 |

### L1.12 The package says what was built and where, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.12.1 | The package holds `base.stl`, `cap.stl` (closed pose, block frame, mm), the `.scad` source, the layout file (bolt, nut and M4 poses and lengths, bearing pose, each body's print orientation) and the agent's own report. | inspection | all present and readable | 3 G0 |
| L3.12.1.1 | Files present and parse; each STL's largest bounding-box axis is within 20 to 200 mm (units check). | inspection | true | 3 G0 |
| L3.12.1.2 | The declared hardware verifies under the seating rule (2.4). | analysis | heads on floors <= 0.10; nuts on pocket floors <= 0.10; axis residual <= 0.20 | 3 |
| L2.12.2 | The agent's own report agrees with the judge. | analysis | every clear_of and inside value it reports: same pass/fail, difference at most 0.10 | 1 |
| L3.12.2.1 | Self-report against judge. | analysis | 100% within 0.10 | 1 |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 37 |
| L3 | 59 |

**Gates** (a failure makes a design WRONG regardless of score): G0 package (L3.12.1.1); G1 two
manifold bodies that do not overlap (L3.1.1.1, L3.1.3.1, L3.10.1.1); G2 pocket diameter (L3.2.1.1);
G3 the halves close (L3.4.1.1); G4 mounting pitch (L3.7.1.2); G5 the nuts are captive (L3.6.2.2).

---

## 6. Feasibility

A concrete design that meets every row exists. Block frame, mm.

**Block.** Base: clamp block X -22.5..22.5, Y -5.1..5.1, Z -14..0, plus a mounting plate X -14..14,
Y -26..26, Z -14..-7 (7.0 thick). Cap: X -22.5..22.5, Y -5.1..5.1, Z 0..14. Closed size 45.0 x 52.0 x
28.0 (<= 60 x 60 x 32).

**Pocket.** Closed bore dia **21.9** for |Y| <= 3.6 (axial length 7.2, within 7.0..7.4); lips for
3.6 < |Y| <= 5.1 (1.5 thick) with inner dia 15.5 (within 15.0..17.0). Designed interference
pi x (11.0^2 - 10.95^2) x 7.0 = 24 mm3 (within 10..40). Free-bore dia 13.0 clears the lips (15.5).
Wall above and below the bore 14 - 10.95 = 3.05 (>= 2.5), sideways 22.5 - 10.95 = 11.55.

**Clamp bolts.** Axes X = +/-17.0, Y = 0 (pitch 34.0). Cap: hole dia 3.4, counterbore dia 5.9 x 3.2
deep (Z 10.8..14.0); bolt M3 x 16 head bearing at Z = 10.8, head top at 13.8 (0.2 below the cap top).
Base: hex pocket across flats 5.9, flats facing Y, depth 2.6 (Z -2.6..0), nut sits on the pocket floor
(Z -2.6..-0.2); dia 3.4 hole continues to Z = -8.0. Bolt tip at 10.8 - 16 = -5.2, **2.6 beyond the nut's
far face** (0.5..4.0), inside the hole (2.8 above its floor). Ligaments: nut pocket to the end face
5.1 - 2.95 = 2.15, to the side face 22.5 - (17 + 3.41) = 2.09, to the bore 17 - 3.41 - 10.95 = 2.64;
cap counterbore to the end face 2.15, to the bore 3.1 (all >= 2.0). A nut turned 20 degrees hits the
pocket walls (the nut's corner support reaches 2.95 at about 13 degrees), and with the cap on, the nut
(top at Z = -0.2) cannot rise 0.5.

**Mounting holes.** Dia 4.5 at (0, +/-20), pitch 40.0, counterbore dia 7.4 x 4.2 from the plate top
(Z -7.0 to -11.2), 2.8 of material under each head (>= 2.0); ligament to the plate end 26 - 23.7 = 2.3.
Key columns over the M4 heads (Y = 20 +/- 3.5) lie outside the cap's Y extent (+/-5.1).

**Load path.** Plate section 28 x 7 = 196 mm2 (>= 100). 100 N pull, 50 N per hole: moment at the
block face 50 x (20 - 5.1) = 745 N.mm, section modulus 28 x 7^2 / 6 = 229 mm3, stress **3.3 MPa**
(<= 10).

**Printing.** Base mounting face down: the bearing half-bore is an upward trough, the nut pockets and
counterbores open upward, so no overhang; bed contact (28 x 41.8 + 45 x 10.2) / (45 x 52) = 70%. Cap
flipped (top face down, split face up): the half-bore is a trough, the counterbores are shallow
recesses with a 5.9 bridge; bed contact 100%.

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
4. **Build the references independently** from the catalogue at the declared layout, sanity checks
   R1 to R5 and the seating rule, then every applicable L3 in requirement order. Record the measured
   value, the limit, the signed margin (negative = fail) and PASS, FAIL or UNVERIFIED. UNVERIFIED
   counts as FAIL.
5. **Recipes.** Closed bore: slice the closed assembly at Y = 0 (`Manifold.slice`), cast 72 rays from
   the declared axis, mean radius times 2. Nut pocket: slice at mid-depth, hexagon across flats from
   opposite edges. Slides and rotations: `Manifold.translate` / `rotate` of the reference part and
   `(a ^ b).volume()`. Cross-section: slice the base at Y = const and take the polygon area and
   second moment about its centroid. Overhang, bed contact, thin features, wall thickness, tool
   columns: `benchmarks/enclosure/rubric.md` sections 3.2 to 3.7.
6. **Verdict.** WRONG: any gate fails. MINOR: no gate fails but a weight-3 L3 fails. CORRECT: no
   gate fails and every weight-3 L3 passes. **MEETS** = CORRECT and every applicable non-physical L3
   of weight 1 and 2 passes. Report also the weighted score and the worst normalised margin among
   weight-3 rows.
7. **Precedence.** Numbers in this document beat any number in a part.json (for example the
   catalogue's nut-pocket convention). Designed contact (1.3) is never interference, but the bearing
   interference is graded against its band, not ignored. An unlisted alternative is graded on the
   default numbers and noted as an observation for the owner.
8. **Where a defect is.** One entry per failed or UNVERIFIED L3 with `req`, `status`, `body` (base,
   cap, both, layout), `feature` (by function and SCAD name), `face` (surface and outward normal),
   `location` (mm, block frame, point or box), `measured` / `limit` / `margin`, `reference`,
   `render`, `evidence`, and `needed` (a verifiable number, never a design instruction). Group L3s
   that fail for one geometric reason.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | Words in the request it comes from |
|---|---|---|---|---|
| L1.1 | Two pieces | L2.1.1-L2.1.3 | L3.1.1.1, L3.1.2.1-2, L3.1.3.1 | "two-piece pillow block", "split along the bearing axis into a base and a cap" |
| L1.2 | Pocket size | L2.2.1-L2.2.3 | L3.2.1.1-2, L3.2.2.1-2, L3.2.3.1-3 | "about 0.1 mm under 22 mm across when the halves are closed" |
| L1.3 | Bearing retained, shaft free | L2.3.1-L2.3.3 | L3.3.1.1-2, L3.3.2.1, L3.3.3.1 | "608 bearing (8 x 22 x 7 mm)" |
| L1.4 | Clamp, not glued | L2.4.1-L2.4.2 | L3.4.1.1, L3.4.2.1 | "clamped, not glued", "so the clamp holds the bearing" |
| L1.5 | M3 bolts | L2.5.1-L2.5.4 | L3.5.1.1-2, L3.5.2.1-3, L3.5.3.1, L3.5.4.1-2 | "Two M3 bolts ... pull the halves together" |
| L1.6 | Captive nuts | L2.6.1-L2.6.3 | L3.6.1.1-4, L3.6.2.1-3, L3.6.3.1 | "captive hex nuts" |
| L1.7 | Mounting holes | L2.7.1-L2.7.3 | L3.7.1.1-3, L3.7.2.1-2, L3.7.3.1-2 | "two M4 mounting holes 40 mm apart" |
| L1.8 | Assembly and access | L2.8.1-L2.8.3 | L3.8.1.1, L3.8.2.1, L3.8.3.1 | implied |
| L1.9 | Load path | L2.9.1-L2.9.3 | L3.9.1.1-2, L3.9.2.1-2, L3.9.3.1 | implied (a bearing mount carries load) |
| L1.10 | Printable | L2.10.1-L2.10.5 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1, L3.10.5.1 | "printed on an FDM printer without supports" |
| L1.11 | Compact, stable | L2.11.1-L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | implied |
| L1.12 | Evidence | L2.12.1-L2.12.2 | L3.12.1.1-2, L3.12.2.1 | needed by the judge (not in the request) |

---

## Audit

Adversarial audit. Re-derived by hand and checked against `bearing_608`, `nut_m3`, `bolt_m3_iso4762` and
`bolt_m4_iso4762` (all load, pass `parts.validate` and `parts.gate`). L1 12 (also in `design.json`), L2 37, L3 59 recounted.

1. **Hidden numbers in L1.9 and L1.4.** L1.9 said "at least as thick as stated" but stated nothing; the judge used 2.5 (bore wall),
   100 mm2 (section) and a 100 N / 10 MPa bending check that the agent was never told. L1.9 now carries those numbers (in `design.json` too),
   and L1.4 now says "at least 100 mm2" for the split contact area (L3.4.2.1).
2. **Lip diameter vs the catalogue.** `bearing_608` keeps printed shoulders outside radius 4 + (22 - 8) / 4 = 7.5 (dia 15.0);
   the band 14.0 to 17.0 allowed a 14.0 lip that breaks that rule. Band now 15.0 to 17.0 (A2, L2.3.1, L3.3.1.1) and the Feasibility lip is 15.5
   (it was exactly at the new floor). A2's claim about the catalogue was wrong ("outside dia 11.5") and is corrected.
3. **Bearing seating height.** The bearing dropped into the base rests on the trough edges at Z = +1.05 (sqrt(11.0^2 - 10.95^2)), not +0.05;
   +0.05 is the pressed pose that V-BRG-PATH uses (designed interference about 12 mm3, inside the 40 mm3 limit). Wording of V-BRG-PATH and D2 fixed, numbers unchanged.
4. **Catalogue vs request.** `bearing_608` has `housing_allowance` 0.1 (HOUSING_BORE 22.1); the request's 0.1 under wins. Recorded in A1.
5. Checked, no change: interference volume pi x (11^2 - 10.95^2) x 7 = 24.1 mm3 and the 10 to 40 band holds over the 21.85 to 21.95 bore
   (12.1 to 35.7); nut pocket 5.9 across flats keeps the nut from turning (support 2.998 at 20 degrees against 2.95); nut tip 2.6 beyond the far face;
   ligaments 2.09 / 2.15 / 2.64 (>= 2.0); plate section 196 mm2, 3.3 MPa; bed contact 70%; M4 key columns outside the cap; closed 45 x 52 x 28;
   every request number matches L1 and the L2/L3 numbers; the nut, bolt and counterbore sizes equal `part.json`.
