# G28 Spur gear pair housing, 1 mm module: requirements (L1 / L2 / L3)

A held-out design of the generalisation benchmark (`benchmarks/generalize/plan.json`, family
housing_assembly). It is modelled on E1-01 (`benchmarks/enclosure/requirements.md`): the same
L1/L2/L3 structure, reference models built from catalogue parts, designed-contact rule, gates and
traceability. The machine-readable request (L1 only, `dev.json` format) is `design.json` next to
this file. Generic grading rules would live in `benchmarks/generalize/rubric.md`; when this file
was written that file did not exist yet, so **section 8 is a design-specific rubric supplement**
(it follows `benchmarks/enclosure/rubric.md`; if `generalize/rubric.md` exists later, it governs the
generic parts and section 8 only adds the G28 specifics).

**Owner's request (brief, verbatim):** "A two-half housing for a 20 tooth and a 40 tooth module 1
spur gear pair, 6 mm face width. Center distance should come out at the pitch value plus 0.15 mm
backlash allowance, each shaft carried by two 625 bearings. The gears must clear the housing walls
by 2 mm and the halves are held by four M3 bolts."

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check Python can run on the delivered STLs. Every L3 has a
method, a pass band with a tolerance, a weight (3 = critical, 2 = major, 1 = minor) and, where it is
a must-pass, a gate mark (G0 to G5, section 5). Every number that comes from an assumption (section
3) is provisional until the owner confirms it. Do not relax a criterion because the agent fails it.

---

## 1. Frames, tolerances, checks and designed contact

### 1.1 Frame

- **Housing frame:** Z along the shaft axes, the split plane at Z = 0, X along the line of centres,
  Y across. The pinion (20 teeth) axis is the line X = 0, Y = 0; the wheel (40 teeth) axis is the
  line X = +30.15, Y = 0 (the centre distance, F5). The **lower half** (the one with Z < 0) and the
  **upper half** (Z > 0) are the two printed bodies. A design delivered mirrored or rotated is
  normalised into this frame before grading (by multiples of 90 degrees and mirroring only); that is
  never penalised. In the normalised frame the grader places the origin on the pinion axis at the
  split plane, using the declared layout (L2.1.1).
- All lengths in mm, angles in degrees. A "closed" housing has the two halves in the assembly pose.

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within e |
| angle | 0.5 degrees (axes: 0.1 degrees when fitted from two bearing pockets) | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole diameter | largest inscribed circle of the hole's section (what a bolt or bearing sees) | |
| boss OD | smallest enclosing circle of the section | |

Where a criterion is written "nominal +/- t", t is the design tolerance and e is added to it.

### 1.3 The checks

- **`clear_of(bodies, volume, c)`**: minimum Euclidean distance between the printed bodies and the
  volume is >= c. Reported: the signed minimum distance d (negative = penetration; penetration volume
  too). Pass: d >= c - e.
- **`inside(volume, cavity, c)`**: the volume lies entirely in the cavity and every point is >= c from
  the cavity boundary. Pass: d >= c - e.
- **`gap(A, B)`**: minimum distance between two named faces or regions, by `min_gap` or ray casting.
- Count, dimension and thickness checks as in E1-01 rubric section 3.5.

`HOUSING` = LOWER and UPPER, closed. The grader builds every reference model and envelope itself
from the catalogue and the declared layout; the agent's copies are not trusted for grading.

### 1.4 Designed contact is not interference

Parts that are meant to touch are excluded from every interference and clearance check. For these
pairs only penetration counts (intersection volume above 0.01 mm3); a distance of zero passes:

- a bearing's outer ring in its pocket (nominal radial gap 0.05, may be zero) and its inner face
  resting on the shoulder
- a shaft in a bearing bore (shaft OD 5.0 = bore 5.0)
- a gear on its shaft (the bore and hub are not modelled; the shaft passes through the gear blank)
- **the two gear tip-envelope blanks overlapping each other in the mesh zone.** Tip diameters 22 and
  42 at centre distance 30.15 overlap by 1.85 mm radially; this lens is where the teeth interleave.
  Gear-to-gear mesh is graded by centre distance and root clearance (L3.1.2.1, L3.1.2.3), never by
  blank interference
- a bolt in its clearance hole, its pilot, and its head on the counterbore floor
- the two halves meeting face to face at the split plane (boss faces and rim faces), and the lap
  fit at the clearance the locating requirement sets (L2.5.3)

---

## 2. Reference models, envelopes and sanity checks

### 2.1 Reference models (M-)

All built by Python from `benchmarks/generalize/parts/<id>/part.json`. Positions are the **default
layout** (assumption A4), used when a design declares none; otherwise each model sits where
`layout.json` declares it (L3.1.1.1).

| Name | What | Source | Size and default position (housing frame, mm) | Datums |
|---|---|---|---|---|
| **M-GEAR-A** | 20 tooth pinion, module 1, face 6.0 | catalogue `gear_spur_generic` (module 1.0, teeth 20, face_width 6.0) | tip blank cylinder Ø22.0 x 6.0 (m(z+2)); pitch Ø20.0; root Ø17.5; axis (0, 0), Z -3.0 to +3.0 | `AXIS`, `PITCH_CIRCLE`, `TIP_CIRCLE` (Ø22), `ROOT_CIRCLE` (Ø17.5), `FACE_START`, `FACE_END` |
| **M-GEAR-B** | 40 tooth wheel, module 1, face 6.0 | catalogue `gear_spur_generic` (module 1.0, teeth 40, face_width 6.0) | tip blank Ø42.0 x 6.0; pitch Ø40.0; root Ø37.5; axis (30.15, 0), Z -3.0 to +3.0 | as above (Ø42, Ø37.5) |
| **M-BRG-A1, A2** | the two 625 bearings of the pinion shaft | catalogue `bearing_625` | Ø16.0 x 5.0 with Ø5.0 bore; axis (0, 0); A1 Z -11.5 to -6.5, A2 Z +6.5 to +11.5 | `AXIS`, `HOUSING_BORE` (Ø16.1), `FACE_A`, `FACE_B` |
| **M-BRG-B1, B2** | the two 625 bearings of the wheel shaft | catalogue `bearing_625` | same, axis (30.15, 0) | as above |
| **M-SHAFT-A, B** | 5 mm round shaft through each bearing pair | catalogue `generic_tube` (OD 5.0, ID 0 = solid, length declared) | Ø5.0, axes as the bearings; default Z -11.5 to +11.5 (flush with the outer bearing faces) | `AXIS` |
| **M-BOLT-1..4** | four M3 socket-head bolts, length l from the declared layout | catalogue `bolt_m3_iso4762` | shank Ø3.0, head Ø5.5 x 3.0; positions as declared (default: see section 6) | `AXIS`, `HEAD_BEARING`, `HEAD_TOP`, `TIP`, `tool_access` keep-out |
| **RGA** | reference gear assembly = M-GEAR-A,B, M-BRG-*, M-SHAFT-*, M-BOLT-* at the declared (or default) layout | assembled | as above | all of the above |

Derived numbers (computed by the grader from the gear parameters, never typed into a design): pitch
centre distance (m z1 + m z2)/2 = (20 + 40)/2 = **30.000**; design centre distance = 30.000 + 0.15 =
**30.150**.

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition (housing frame) | Used by |
|---|---|---|---|
| **V-GEAR-A / V-GEAR-B** | the gear's rotation envelope | M-GEAR-A / M-GEAR-B tip blank (Ø22 / Ø42, face 6.0, at the declared Z) | L2.4.1 |
| **V-SHAFT-A / V-SHAFT-B** | the shaft's path | Ø5.0 cylinder on each shaft axis from Z -30 to +30 | L2.7.1 |
| **V-DRIVER-j** (j = 1..4) | hex-key access to a bolt | M-BOLT-j `tool_access` keep-out: Ø5.5 column from the head top up 25.0 | L2.6.7 |
| **V-INSTALL-A / -B** | gear installation path | M-GEAR-A / -B tip blank swept +Z from its seated pose to 30.0 above the lower half's rim | L2.11.1 |
| **V-CAVITY** | the closed housing's internal void | convex hull of (LOWER and UPPER, closed) minus (LOWER and UPPER), the connected component containing the gears' centroid | L2.4.4, L2.8.1 |
| **V-SEAL-OPEN** | any through-path from outside into V-CAVITY | rays from outside the hull reaching V-CAVITY with the RGA bearings and shafts present as solids | L2.8.1 |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-GEAR-A, M-GEAR-B | tip blank diameter = m(z+2); face width | 22.0 +/- 0.05; 42.0 +/- 0.05; 6.0 +/- 0.05 |
| R2 | M-BRG-* | bore, OD, width | 5.0 / 16.0 / 5.0, each +/- 0.1 |
| R3 | M-BOLT-* | head Ø x height; shank Ø | 5.5 x 3.0 +/- 0.2; 3.0 +/- 0.2 |
| R4 | derived numbers | pitch centre distance from the gear parameters | 30.000 +/- 0.001 |
| R5 | RGA | parts do not collide (bearing/shaft/gear contact excluded, 1.4) | intersection <= 0.01 mm3 |
| R6 | every V- envelope | its datums equal the model datums it was built from | <= 0.01 |

**Seating rule.** The RGA sits at the pose declared in `layout.json`. The grader verifies the
declaration: each declared bearing's axis is within 0.15 of the fitted axis of the pocket it claims
(least squares on the pocket circle at mid-depth), and its cavity-side face lies on the shoulder
face (distance <= 0.10); each declared shaft is coaxial with its two bearings (<= 0.10); each gear
axis is coaxial with its shaft (<= 0.05). If the declaration is missing or fails verification, the
RGA is rebuilt by fitting each bearing to its nearest pocket and each gear to the axis through the
bearing pair that is nearest it, and L3.12.1.2 fails. If there are no pockets, every bearing check
(L2.3.x, G4) fails.

---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (A-rows, with uncertainty)

| # | Question | Value chosen | Why, and how uncertain |
|---|---|---|---|
| **A1** | Pressure angle? | 20 degrees, standard ISO 53 rack: addendum 1.0 m, dedendum 1.25 m; profile shift 0 | Brief gives only the module. 20 degrees is the standard; no undercut for z >= 17 (z = 20 passes). Uncertainty: none for the envelope; a 14.5 degree gear would change only the backlash, not the blanks. |
| **A2** | What is "0.15 mm backlash allowance"? | Added to the **centre distance** (30.000 -> 30.150), not to the tooth thickness. Resulting circumferential backlash is about 2 x 0.15 x tan 20 = 0.11 mm (derived, not graded). | The brief says "Center distance should come out at the pitch value plus 0.15". Uncertainty: low. |
| **A3** | Shaft size? | 5.0 mm steel shaft, equal to the 625 bore; not printed; length chosen by the design and declared; default flush with the outer bearing faces (23.0) | The 625 bore fixes it. Uncertainty: none. |
| **A4** | Default layout (used only if no layout is declared) | Gears centred on the split plane (Z -3 to +3), pinion axis at X 0, wheel axis at X +30.15, bearings at Z +/-(6.5 to 11.5), bolts at the section 6 positions | A symmetric common layout; the design may choose its own and declare it. |
| **A5** | Bearing pocket diameter and retention | Pocket Ø16.1 (16.0 + 0.1 FDM housing allowance, `bearing_625` part.json), depth 5.0 to 5.3, shoulder on the cavity side with a hole Ø10.5 to 14.0 and thickness >= 1.5. Shoulder inner radius >= 5.25 (= bore/2 + (D - d)/4 from part.json) so it bears on the outer ring only. | Part.json states these as FDM conventions uncertain by about 0.1 mm per printer; the numbers here are authoritative (precedence, section 8). |
| **A6** | Wall thickness | Side walls 2.4 to 5.0; bearing end plates (outer face to cavity face) 6.5 to 8.5 | 6 perimeters at 0.4 mm is stiff; the end plate holds a 5.0 pocket plus a >= 1.5 shoulder, so it cannot be thinner than 6.5. |
| **A7** | Bolt length | The design picks a stock length (8, 10, 12, 16, 20, 25 or 30 mm) and declares it; the engagement rule (L3.6.3.1) fixes what is acceptable | The brief gives no length; stock lengths are standard. |
| **A8** | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed; sliding fit 0.15 to 0.35 per side; each half prints with its outer (bearing) face on the bed | Common printers. Uncertainty +/-0.1 on every fit; print a test ring. |
| **A9** | Size limit | Closed outside size <= 85 x 65 x 30 (X x Y x Z) | Stops oversized designs; a tight design is about 74 x 54 x 23 (section 6). Not in the owner's words: confirm. |
| **A10** | Gear lubrication, noise, load | Not graded. Light-duty (under 1 N m); no seal or grease port. | Typical hobby gearbox; confirm if a seal is wanted. |
| **A11** | Gears fixed on the shafts | Not graded (set screw, press or keyed: the design's choice); no axial retention requirement beyond the 2.0 clearance to the shoulders | The brief does not specify. Uncertainty: medium; a gear that slides axially by 2.0 stays clear of everything. |
| **A12** | Service sequence | Shafts and gears come out before the halves separate (L2.11.2 is graded with gears and shafts removed; the bearings stay pressed in their halves) | Natural for a bearing-supported shaft line. |

### 3.2 Fixed decisions (choices that would otherwise be ambiguous; not open to alternatives)

| # | Decision |
|---|---|
| **F1** | The split plane is **perpendicular to the shafts** and passes between the two bearings of each shaft: one bearing of every shaft in each half. (Reads "each shaft carried by two bearings, a half holding one of each".) Alternatives (bearings both in one half) are graded N/A on L2.3.1 only if the design states it; they then fail L1.2/L2.5.2. |
| **F2** | Bearing pockets open to the **outside** faces of the housing; the shoulder faces the cavity. |
| **F3** | The four bolts have their clearance holes and counterbores in the **upper** half and their pilot holes in the **lower** half. |
| **F4** | Tooth form is not modelled: a gear is its tip-diameter blank (`gear_spur_generic`). The blank overlap of the two gears in the mesh zone is designed contact (1.4). |
| **F5** | Design centre distance is exactly **30.15** (= pitch 30.00 + 0.15); band 30.10 to 30.20. |
| **F6** | The gear face centres are declared; both gears' face Z ranges must overlap by >= 5.5 (of 6.0), and both lie inside the cavity. |
| **F7** | Closure is bolts only (no snaps, no sliding lid). |
| **F8** | Housing frame as in 1.1 (the grader normalises). |

---

## 4. Requirements tree

Column "Gate" names the must-pass groups of section 5; blank = scored only.

### L1.1 The gear pair is laid out on parallel shafts at centre distance 30.15

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: for each gear its module, tooth count, face width and pose; each bearing, shaft and bolt (catalogue id, pose, bolt length), and each half's print orientation. | inspection | `layout.json` present, parses, names 2 `gear_spur_generic`, 4 `bearing_625`, 2 shafts, 4 `bolt_m3_iso4762` | 3 | G0 |
| L3.1.1.1 | Layout parses and every catalogue id exists; declared gear parameters equal the request: module 1.0, teeth 20 and 40, face 6.0. | inspection | true | 3 | G0 |
| L2.1.2 | The centre distance is the pitch value plus 0.15. | analysis | 30.15 +/- 0.05 | 3 | G2 |
| L3.1.2.1 | Distance between the fitted axis of the pinion bearing pockets and that of the wheel bearing pockets, measured on the delivered STLs. | analysis | 30.10 <= CD <= 30.20 | 3 | G2 |
| L3.1.2.2 | The declared gear axes agree with the measured pocket axes. | analysis | declared CD within 0.05 of the measured CD | 2 | |
| L3.1.2.3 | Root clearance both ways, computed from the measured CD and the gear parameters: CD - r_tip(A) - r_root(B) and CD - r_tip(B) - r_root(A) (nominal 0.40 each, standard bottom clearance is 0.25 m). | analysis | both >= 0.25 | 2 | |
| L2.1.3 | The two gears run in one plane. | inspection | declared face-centre Z of A and B differ by <= 0.5 (face overlap >= 5.5 of 6.0) | 2 | |
| L3.1.3.1 | Z offset between the two gear face centres. | inspection | <= 0.5 | 2 | |

### L1.2 The shafts are parallel and each bearing pair is coaxial

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | All four bearing pocket axes are perpendicular to the split plane. | analysis | each within 0.3 degrees of Z | 3 | |
| L3.2.1.1 | Angle between each pocket axis (fitted from the pocket wall) and the split-plane normal; angle between the two shaft lines. | analysis | <= 0.3 degrees; <= 0.3 degrees | 3 | |
| L2.2.2 | The two pockets of one shaft, one in each half, are coaxial when the housing is closed. | analysis | axis offset <= 0.10 for each shaft | 3 | G4 |
| L3.2.2.1 | Offset between the pocket axes of A1 and A2, and of B1 and B2, in the closed pose (fitted circles at mid-depth). | analysis | <= 0.10 each | 3 | G4 |

### L1.3 Four 625 bearings, pressed into pockets and seated on shoulders

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Four bearing pockets, two in each half, one on each side of each gear. | inspection | count 4; per half 2; one per shaft per half | 3 | G4 |
| L3.3.1.1 | Pocket count and distribution. | inspection | 4; 2 + 2; each shaft has one in each half | 3 | G4 |
| L2.3.2 | Pocket size is the 625 outside diameter plus the 0.1 housing allowance, and the depth takes the 5.0 bearing. | inspection | Ø16.1 +/- 0.1; depth 5.0 to 5.3 | 3 | G4 |
| L3.3.2.1 | Pocket diameter (largest inscribed circle, mid-depth). | inspection | 16.0 <= Ø <= 16.2 | 3 | G4 |
| L3.3.2.2 | Pocket depth (ray cast from the outer face to the shoulder face). | inspection | 5.0 <= depth <= 5.3 | 2 | |
| L2.3.3 | Each pocket ends in a shoulder on the cavity side that retains the outer ring and leaves the inner ring free. | inspection | hole Ø 10.5 to 14.0; thickness >= 1.5; coaxial with the pocket <= 0.10 | 2 | |
| L3.3.3.1 | Shoulder hole diameter (largest inscribed circle). | inspection | 10.5 <= Ø <= 14.0 | 2 | |
| L3.3.3.2 | Shoulder thickness (ray cast along the axis). | inspection | >= 1.5 | 2 | |
| L3.3.3.3 | Shoulder hole to pocket coaxiality. | inspection | <= 0.10 | 1 | |
| L2.3.4 | Each declared bearing seats: pressed into its pocket, inner face on its shoulder, no collision. | analysis | cavity-side face <= 0.10 from the shoulder; axis within 0.15 of the pocket axis; intersection with the printed bodies <= 0.01 mm3 | 3 | G4 |
| L3.3.4.1 | Seating verification (the seating rule, section 2.3). | analysis | all 4 pass | 3 | G4 |
| L3.3.4.2 | Intersection of each M-BRG with HOUSING. | analysis | <= 0.01 mm3 | 3 | |
| L2.3.5 | Material around each pocket. | analysis | ligament from the pocket wall to the outer surface and to any other hole >= 2.0; to the cavity >= 1.5 (the shoulder, L2.3.3) | 1 | |
| L3.3.5.1 | Minimum ligament around each pocket: to the outer surface and other holes; to the cavity. | analysis | >= 2.0; >= 1.5 | 1 | |

### L1.4 The gears clear the housing by 2.0, radially and along the shaft

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Closed: no housing surface comes within 2.0 of either gear's tip envelope (bolt bosses, walls, shoulders, lap leaves all count). | analysis | clear_of(HOUSING, V-GEAR-A, 2.0) and clear_of(HOUSING, V-GEAR-B, 2.0) | 3 | G3 |
| L3.4.1.1 | Minimum distance from each gear envelope to HOUSING (radial and axial; the report states which face is nearest). | analysis | d >= 2.0 for each | 3 | G3 |
| L2.4.2 | The housing is not wastefully large: the nearest surface to each gear is within 4.0. | analysis | min distance from each envelope to HOUSING <= 4.0 | 1 | |
| L3.4.2.1 | Nearest-surface distance per gear. | analysis | 2.0 <= d <= 4.0 | 1 | |
| L2.4.3 | The cavity is as tall as the gears need: shoulder-to-shoulder distance is the 6.0 face plus 2 x 2.0, up to 4.0 more. | inspection | 10.0 <= H <= 14.0 | 2 | |
| L3.4.3.1 | Distance between the two shoulder faces of one shaft (ray cast along the axis). | inspection | 10.0 <= H <= 14.0 | 2 | |
| L2.4.4 | Both gears lie inside the closed housing. | analysis | inside(V-GEAR-A and V-GEAR-B, V-CAVITY, 2.0) | 2 | |
| L3.4.4.1 | Gears in the cavity. | analysis | d >= 2.0 | 2 | |

### L1.5 Two halves, split across the shafts, locating and not fused

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Lower and upper are separate bodies, each one connected body, not interpenetrating when closed. | analysis | LOWER 1 shell; UPPER 1 shell; LOWER and UPPER intersection <= 1.0 mm3 | 3 | G1 |
| L3.5.1.1 | One shell each (decompose count). | analysis | 1; 1 | 3 | G1 |
| L3.5.1.2 | Intersection of the halves, closed (faces in contact excluded: penetration only). | analysis | <= 1.0 mm3 | 3 | G1 |
| L2.5.2 | The split plane is perpendicular to the shafts and each half carries one pocket of each shaft. | inspection | seam normal within 1.0 degree of the shaft axis; 2 pockets per half | 2 | |
| L3.5.2.1 | Seam normal vs shaft axis; pockets per half. | inspection | <= 1.0 degree; 2 | 2 | |
| L2.5.3 | A lap, rabbet or tongue-and-groove locates the halves on each other with a sliding fit. | inspection | clearance 0.15 to 0.35 per side; engagement >= 2.0; thinnest leaf >= 0.8 | 2 | |
| L3.5.3.1 | Gap between the mating locating faces, all of them (min, median, max). | inspection | 0.15 <= gap <= 0.35 | 2 | |
| L3.5.3.2 | Engagement depth of the lap (Z overlap of the leaves). | inspection | >= 2.0 | 2 | |
| L3.5.3.3 | Thinnest locating leaf. | inspection | >= 0.8 | 1 | |
| L2.5.4 | The closed seam is tight and the outer outlines are flush. | inspection | seam gap <= 0.5; the two halves' plan outlines agree within 0.5 | 1 | |
| L3.5.4.1 | Seam gap on all four sides; outline match. | inspection | <= 0.5; <= 0.5 | 1 | |

### L1.6 Four M3 socket-head bolts hold the halves together

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Exactly four bolt axes, parallel to Z, all outside V-CAVITY and outside the bearing pockets. | inspection | count 4; angle to Z <= 0.5 degrees; each hole wall >= 1.5 from V-CAVITY and from every pocket | 3 | G5 |
| L3.6.1.1 | Number of bolt holes (distinct axes through both halves); axis direction. | inspection | 4; <= 0.5 degrees | 3 | G5 |
| L2.6.2 | Hole sizes for M3 (`bolt_m3_iso4762`): 3.4 clearance holes with counterbores in the upper half, 2.5 pilots in the lower half (F3). | inspection | clearance Ø 3.4 +/- 0.1; counterbore Ø 5.9 +/- 0.2 deep 3.2 +/- 0.2; pilot Ø 2.5 +/- 0.1 | 3 | G5 |
| L3.6.2.1 | Clearance-hole diameter, all four. | inspection | 3.3 <= Ø <= 3.5 | 3 | G5 |
| L3.6.2.2 | Counterbore diameter and depth, all four (head sits below the surface: depth >= head height 3.0). | inspection | 5.7 <= Ø <= 6.1; 3.0 <= depth <= 3.4 | 1 | |
| L3.6.2.3 | Pilot diameter, all four. | inspection | 2.4 <= Ø <= 2.6 | 3 | G5 |
| L2.6.3 | Engagement: the declared bolt length reaches into the pilot far enough, and stops short of its bottom. | analysis | engagement >= 6.0 (2 x thread diameter); tip >= 0.5 above the pilot bottom; >= 1.5 of material under the pilot | 2 | |
| L3.6.3.1 | Thread engagement = declared length minus (clearance-hole length plus the counterbore floor height above the split plane). | analysis | >= 6.0 | 2 | |
| L3.6.3.2 | Pilot depth minus engagement; floor under the pilot. | analysis | >= 0.5; >= 1.5 | 1 | |
| L2.6.4 | The hole in the upper half and the pilot in the lower half are coaxial. | inspection | axis offset <= 0.2 | 3 | G5 |
| L3.6.4.1 | Axis offset per bolt, closed pose. | inspection | <= 0.2 each | 3 | G5 |
| L2.6.5 | The bolts are spread, so the halves close evenly. | inspection | bolt-axis bounding rectangle >= 60 percent of the housing plan extent in X and in Y | 1 | |
| L3.6.5.1 | Bolt rectangle vs housing plan extent. | inspection | >= 60 percent; >= 60 percent | 1 | |
| L2.6.6 | Material around the bolt holes. | analysis | ligament from every hole or counterbore to V-CAVITY, the outer surface and the pockets >= 1.5 | 2 | |
| L3.6.6.1 | Minimum ligament around each bolt hole and counterbore. | analysis | >= 1.5 | 2 | |
| L2.6.7 | A hex key reaches every bolt head. | analysis | clear_of(HOUSING, V-DRIVER-j, 0.0), j = 1..4 | 2 | |
| L3.6.7.1 | Driver columns clear. | analysis | d >= 0.0 | 2 | |

### L1.7 Shafts pass freely and the gears sit on the shaft axes

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Closed: a 5 mm shaft inserts along each shaft line through both bearings and both shoulder holes without touching a printed surface. | test | clear_of(HOUSING, V-SHAFT-A and V-SHAFT-B, 0.0) | 3 | G4 |
| L3.7.1.1 | Shaft path clear (bearings present as solids; shaft-bearing contact excluded). | test | penetration <= 0.01 mm3 for each shaft, in the closed pose | 3 | G4 |
| L2.7.2 | Each gear axis coincides with its shaft and bearing axis. | analysis | <= 0.05 | 2 | |
| L3.7.2.1 | Offset between each declared gear axis and the fitted pocket-pair axis. | analysis | <= 0.05 | 2 | |

### L1.8 Closed housing: no other openings, walls 2.4 to 5.0

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The only openings into the cavity are the four shoulder holes (closed by the bearings and shafts) and the bolt holes. | analysis | no ray path of a Ø2.0 sphere from outside reaches V-CAVITY, with bearings and shafts as solids, other than through bolt holes | 2 | |
| L3.8.1.1 | Probe for unlisted openings (rubric method, E1 3.4). | analysis | 0 unlisted paths | 2 | |
| L2.8.2 | Wall thickness. | inspection | side walls 2.4 to 5.0; bearing end plates 6.5 to 8.5 | 2 | |
| L3.8.2.1 | Median side-wall thickness, each wall (ray casting away from features). | inspection | 2.4 <= t <= 5.0 | 2 | |
| L3.8.2.2 | End-plate thickness (outer face to cavity face at the shoulder), each half. | inspection | 6.5 <= t <= 8.5 | 2 | |
| L2.8.3 | Each wall joins its end plate along its length. | analysis | contact >= 90 percent of wall length x thickness; one connected body per half | 2 | |
| L3.8.3.1 | Wall-to-plate contact area. | analysis | >= 0.9 x L x t | 2 | |

### L1.9 Both halves print on an FDM printer without supports

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | In its declared print orientation (default: outer bearing face on the bed), no overhang steeper than 45 degrees from vertical, except round holes Ø <= 12 in vertical walls and bridges <= 15. | analysis | 0 offending faces (area > 1 mm2) | 2 | |
| L3.9.1.1 | Overhang and bridge scan per half (E1 rubric 3.6). | analysis | 0 patches | 2 | |
| L2.9.2 | Each half's mesh is manifold and a single shell. | analysis | 1 shell; manifold3d accepts it | 3 | G1 |
| L3.9.2.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.9.3 | Each half rests on a flat face in its print orientation. | analysis | bed contact >= 50 percent of the plan bounding box | 1 | |
| L3.9.3.1 | Bed-contact area per half. | analysis | >= 50 percent | 1 | |
| L2.9.4 | No feature thinner than 0.8; mating clearances >= 0.15. | analysis | min thickness >= 0.8; min mating gap >= 0.15 | 1 | |
| L3.9.4.1 | Thin-feature and mating-gap scan. | analysis | as stated | 1 | |
| L2.9.5 | Each half fits a 200 x 200 x 200 build volume. | inspection | bounding box <= 200 per axis | 1 | |
| L3.9.5.1 | Bounding box per half. | inspection | <= 200 per axis | 1 | |

### L1.10 Compact and stable: at most 85 x 65 x 30, flat on the table

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Closed outside size. | inspection | X <= 85.0, Y <= 65.0, Z <= 30.0 (X the line of centres) | 1 | |
| L3.10.1.1 | Assembly bounding box. | inspection | as stated | 1 | |
| L2.10.2 | It stands on a flat outer bearing face without tipping. | analysis | underside flatness <= 0.2; stable at 5 degrees tilt | 1 | |
| L3.10.2.1 | Underside planarity; `stable` at 5 degrees with the RGA mass (estimated 60 g). | analysis | <= 0.2; passes | 1 | |

### L1.11 Assembly and service: the gears drop in, the halves lift off

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Upper half off: each gear drops straight down (-Z) into the lower half from above its rim onto its seat without touching it. | test | clear_of(LOWER, V-INSTALL-A and V-INSTALL-B, 0.5) | 2 | |
| L3.11.1.1 | Installation path clear. | test | d >= 0.5 | 2 | |
| L2.11.2 | With the bolts, gears and shafts out, the upper half lifts straight off (+Z, 30.0) from the lower half. | test | sweep of UPPER along +Z: no penetration with LOWER (the lap clears) | 2 | |
| L3.11.2.1 | Lift-off sweep, 1.0 mm steps. | test | every step <= 0.01 mm3 | 2 | |
| L2.11.3 | Removing the upper half does not release the bearings of the lower half: bearing retention does not depend on the bolts. | inspection | lower bearings sit in pockets with shoulders (L2.3.3) | 1 | |
| L3.11.3.1 | Judge confirms. | inspection | true | 1 | |

### L1.12 The design package says what was built, and its own claims are true

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds: `lower.stl`, `upper.stl` (closed assembly pose, housing frame, mm), the `.scad` source, `layout.json` (L2.1.1, plus each half's print orientation) and the agent's own clearance report. | inspection | all present and readable | 3 | G0 |
| L3.12.1.1 | Files present and parse; STLs in mm: each half's largest bounding-box axis is 20 to 200. | inspection | true | 3 | G0 |
| L3.12.1.2 | The declared layout verifies under the seating rule (section 2.3). | analysis | bearing faces on shoulders <= 0.10; pocket-axis residual <= 0.15; gear axis residual <= 0.05 | 3 | |
| L2.12.2 | The agent's own report agrees with the judge's measurements. | analysis | for every clear_of / inside L3 the agent reports, same pass/fail and \|d_agent - d_judge\| <= 0.10 | 1 | |
| L3.12.2.1 | Self-report vs judge. | analysis | 100 percent agreement within 0.10 | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 42 |
| L3 | 56 |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.1.1.1, L3.12.1.1);
**G1** manifold and two separate bodies (L3.9.2.1, L3.5.1.1, L3.5.1.2); **G2** centre distance
(L3.1.2.1); **G3** gear clearance 2.0 (L3.4.1.1); **G4** bearings (L3.2.2.1, L3.3.1.1, L3.3.2.1,
L3.3.4.1, L3.7.1.1); **G5** the halves are bolted (L3.6.1.1, L3.6.2.1, L3.6.2.3, L3.6.4.1).

---

## 6. Feasibility: a design that meets every number

This is one concrete design, hand-checked against the bands (the loop does not get it).

**Gear layout.** Pinion axis (0, 0); wheel axis (30.15, 0) (= (20 + 40)/2 + 0.15). Both gears Z -3.0 to
+3.0. Tip radii 11.0 and 21.0. Root clearance: 30.15 - 11.0 - 18.75 = 0.40 and 30.15 - 21.0 - 8.75 =
0.40, both >= 0.25.

**Cavity.** Rectangle X -13.0 to +53.15, Y -23.0 to +23.0 (gear tip circles plus 2.0: pinion x
-11 - 2 = -13; wheel x 30.15 + 21 + 2 = 53.15 and y +/-(21 + 2) = +/-23), Z -5.0 to +5.0 (face +/-3.0
plus 2.0). Shoulder-to-shoulder H = 10.0.

**Bearings.** On each shaft one pocket per half, Ø16.1 x 5.0 deep from the outer faces (pocket Z
+/-11.5 to +/-6.5), shoulder Z +/-6.5 to +/-5.0 (thickness 1.5), shoulder hole Ø12.0. End-plate
thickness 6.5, bearing flush with the outer face. Pocket diameter 16.1 is in 16.0 to 16.2; shoulder hole
Ø12.0 is in 10.5 to 14.0 and its inner radius 6.0 >= 5.25, so the shoulder bears on the outer ring only
(the 625 inner ring is about Ø9.3, well inside the hole).

**Walls and outline.** Side walls 4.0. Outer outline X -17.0 to +57.15 (74.15), Y -27.0 to +27.0
(54.0), Z -11.5 to +11.5 (23.0): within 85 x 65 x 30. Lap joint in the walls: the lower half has an inner
leaf 1.875 thick rising 2.0 above Z = 0, the upper half has an outer leaf 1.875 thick hanging 2.0
below it; leaf-to-leaf gap 0.25 in plan, 0.2 in Z, so fit 0.2 to 0.25 (band 0.15 to 0.35) and
engagement 2.0.

**Bolts.** Four bosses of radius 5.0 in the cavity corners at (-9.0, +/-19.0) and (50.5, +/-20.5),
merged with the walls. Gear clearance to the bosses: pinion side distance from the pinion axis to
the boss centre sqrt(81 + 361) = 21.0, minus 5.0, minus 11.0 = 5.0 >= 2.0; wheel side sqrt(20.35^2 +
20.5^2) = 28.9, minus 5.0, minus 21.0 = 2.9 >= 2.0. Clearance holes Ø3.4 through the upper half
with Ø5.9 counterbores 3.2 deep (floor at Z +8.3); pilots Ø2.5, 8.4 deep (to Z -8.4). Bolt length 16:
tip at Z -7.7, engagement 7.7 >= 6.0, pilot margin 0.7 >= 0.5, floor under the pilot 3.1 >= 1.5. Ligament:
boss radius 5.0 - counterbore radius 2.95 = 2.05 >= 1.5. Bolt rectangle 59.5 x 41.0 (Y span is the wheel-side pair at +/-20.5) = 80 percent
and 76 percent of 74.15 x 54: >= 60 percent.

**Printing.** Each half prints with its outer face on the bed: pockets open to the bed (shoulder
annulus 2.0 wide bridges), counterbores open to the bed (1.25 wide annulus bridges), lap leaves and
pilots open upward: no overhang steeper than 45 degrees; bed contact about 90 percent.

**Mass and stability.** Lower half about 52 cm3 of PLA; outer face flat; stable.

---

## 7. Traceability

| L1 | Owner need (from the brief) | L2 | L3 | JSON L1 | Words in the brief it comes from |
|---|---|---|---|---|---|
| L1.1 | Gear pair and centre distance | L2.1.1-L2.1.3 | L3.1.1.1, L3.1.2.1-3, L3.1.3.1 | L1.1 | "20 tooth and a 40 tooth module 1 spur gear pair, 6 mm face width", "Center distance ... pitch value plus 0.15 mm" |
| L1.2 | Parallel shafts, coaxial bearings | L2.2.1-L2.2.2 | L3.2.1.1, L3.2.2.1 | L1.2 | "each shaft" |
| L1.3 | Bearings | L2.3.1-L2.3.5 | L3.3.1.1, L3.3.2.1-2, L3.3.3.1-3, L3.3.4.1-2, L3.3.5.1 | L1.3 | "each shaft carried by two 625 bearings" |
| L1.4 | Gear clearance | L2.4.1-L2.4.4 | L3.4.1.1, L3.4.2.1, L3.4.3.1, L3.4.4.1 | L1.4 | "gears must clear the housing walls by 2 mm" |
| L1.5 | Two halves | L2.5.1-L2.5.4 | L3.5.1.1-2, L3.5.2.1, L3.5.3.1-3, L3.5.4.1 | L1.5 | "two-half housing" |
| L1.6 | Bolts | L2.6.1-L2.6.7 | L3.6.1.1, L3.6.2.1-3, L3.6.3.1-2, L3.6.4.1, L3.6.5.1, L3.6.6.1, L3.6.7.1 | L1.6 | "halves are held by four M3 bolts" |
| L1.7 | Shaft path, gear axes | L2.7.1-L2.7.2 | L3.7.1.1, L3.7.2.1 | L1.7 | "each shaft carried by two ... bearings" |
| L1.8 | Closed and sturdy | L2.8.1-L2.8.3 | L3.8.1.1, L3.8.2.1-2, L3.8.3.1 | L1.8 | "housing" |
| L1.9 | Printable | L2.9.1-L2.9.5 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1, L3.9.5.1 | L1.9 | implied (OpenSCAD -> FDM) |
| L1.10 | Compact | L2.10.1-L2.10.2 | L3.10.1.1, L3.10.2.1 | L1.10 | implied (A9) |
| L1.11 | Assembly and service | L2.11.1-L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | L1.11 | implied |
| L1.12 | Evidence | L2.12.1-L2.12.2 | L3.12.1.1-2, L3.12.2.1 | L1.12 | needed by the judge |

---

## 8. Grading supplement (design-specific; `generalize/rubric.md` did not exist when this was written)

Procedure, recipes and report format are those of `benchmarks/enclosure/rubric.md` (sections 2, 3 and
5), applied to the lower and upper STLs, with these specifics:

1. **Inputs.** `lower.stl`, `upper.stl` (closed pose, mm), `.scad`, `layout.json`, self-report,
   renders. The judge does not use the agent's code or transcript, earlier verdicts, or
   `benchmarks/heldout.json`.
2. **Normalise the frame** (section 1.1): pinion axis at the origin, wheel at +X, lower half below
   Z = 0. Record the transform.
3. **Build references independently** from the catalogue parts at the declared layout, then V-
   envelopes (2.2), then sanity checks R1 to R6 and the seating rule (2.3).
4. **Recipes.** `clear_of`, `inside` and apertures exactly as E1 rubric 3.2 to 3.4. Axes and
   diameters: slice each pocket, hole and boss at mid-depth and fit circles (largest inscribed for
   holes, smallest enclosing for bosses). Centre distance: fit one line through each shaft's two
   pocket circles and measure the line-to-line distance. Shaft path: Ø5.0 `V-SHAFT` swept through the
   closed housing with the bearings as solids.
5. **Classes.** WRONG = any gate (G0 to G5) fails. MINOR = no gate fails but a weight-3 L3 fails.
   CORRECT = no gate fails and every weight-3 L3 passes. **MEETS** = CORRECT and every applicable
   non-physical L3 of weight 1 and 2 passes. UNVERIFIED counts as FAIL. Report the weighted score
   and the worst normalised margin among weight-3 L3s.
6. **Precedence.** The numbers in this file (sections 2, 3, 4) beat `part.json`. If a catalogue
   value disagrees, build from this file and record a defect on the requirement the stale value
   breaks, with where = the part.json field. Designed contact (1.4) is never interference.
   Never relax a criterion, never round in the design's favour beyond e, never infer a pass from a
   render.
7. **WHERE a defect is.** One entry per failed or UNVERIFIED L3, most severe first (gates, then
   weight 3, 2, 1): `req` (L3, L2, L1), `status`, `body` (lower, upper, both, layout), `feature`
   (named by function and SCAD name, for example "pinion bearing pocket in the upper half
   (`pocket_a_up`)"), `face` (surface and outward normal), `location` (coordinates in the housing
   frame, a point or a box), `measured` / `limit` / `margin`, `reference` (the M- or V- involved and
   its datum), `render`, `evidence` (saved defect STL), `needed` (a numeric target, never a design
   instruction). Group L3s that fail for one geometric reason, keeping every id.
8. **Measured-values table (always filled in).**

| Quantity | Limit | Measured |
|---|---|---|
| Centre distance (L3.1.2.1), mm | 30.10 to 30.20 | |
| Root clearance both ways (L3.1.2.3), mm | >= 0.25 | |
| Axis parallelism; pocket-pair offsets (L3.2.x), deg / mm | <= 0.3; <= 0.10 | |
| Pocket count; Ø; depth (L3.3.1.1, L3.3.2.x), mm | 4; 16.0 to 16.2; 5.0 to 5.3 | |
| Shoulder hole Ø; thickness (L3.3.3.x), mm | 10.5 to 14.0; >= 1.5 | |
| Gear to housing d, each gear (L3.4.1.1), mm | >= 2.0 | |
| Cavity height H (L3.4.3.1), mm | 10.0 to 14.0 | |
| Shells lower / upper; halves intersection (L3.5.1.x) | 1 / 1; <= 1.0 mm3 | |
| Lap gap; engagement (L3.5.3.x), mm | 0.15 to 0.35; >= 2.0 | |
| Bolt holes: count; clearance Ø; pilot Ø (L3.6.x) | 4; 3.3 to 3.5; 2.4 to 2.6 | |
| Engagement; coaxial offset (L3.6.3.1, L3.6.4.1), mm | >= 6.0; <= 0.2 | |
| Shaft path clear (L3.7.1.1) | <= 0.01 mm3 | |
| Unlisted openings (L3.8.1.1) | 0 | |
| Wall; end plate thickness (L3.8.2.x), mm | 2.4 to 5.0; 6.5 to 8.5 | |
| Overhang patches; bed contact (L3.9.x) | 0; >= 50 percent | |
| Closed envelope X x Y x Z (L3.10.1.1), mm | <= 85 x 65 x 30 | |
| Install sweep d; lift-off sweep (L3.11.x) | >= 0.5; <= 0.01 mm3 | |
| Self-report agreement (L3.12.2.1) | 100 percent within 0.10 | |

---

## Audit

Adversarial audit (second agent). Parts `gear_spur_generic`, `bearing_625`, `bolt_m3_iso4762`, `generic_tube` all load and pass `parts.gate` (catalogue `benchmarks/generalize/parts`). Counts re-derived from the tables: L1 = 12, L2 = 42, L3 = 56 (match section 5). The derived numbers (pitch CD 30.000, design CD 30.150, tip/root diameters 22/17.5 and 42/37.5, root clearance 0.40 both ways, cavity 66.15 x 46 x 10, outline 74.15 x 54 x 23) were recomputed and hold. The Feasibility design was walked through every gate and weight-3 row (bolt geometry, ligaments, overhangs, lap fit, install and lift-off sweeps).

| # | Defect found | Fix |
|---|---|---|
| 1 | L3.3.5.1 asked for >= 2.0 ligament from the pocket wall to the cavity, but the shoulder is only >= 1.5 thick (L3.3.3.2) and the Feasibility design has 1.5 (pocket wall edge at Z 6.5 to cavity ceiling at Z 5.0). The two rows contradicted each other. | Cavity-side ligament is now >= 1.5 (the shoulder); 2.0 kept for the outer surface and other holes. |
| 2 | Feasibility bolt rectangle said "40 or 41" and 70 percent; the pairs are at Y +/-19.0 and +/-20.5, so the rectangle is 41.0 = 76 percent. | Text corrected (still >= 60). |
| 3 | Numbers a gate or weight 2-3 row needs but the request and L1s never told the agent: coaxiality 0.10 and axis angle 0.3 (G4), CD tolerance, gear plane offset 0.5, root clearance 0.25, pocket depth and shoulder hole and thickness, nearest-surface 4.0 and cavity height 10 to 14, lap fit 0.15 to 0.35 / 2.0 / 0.8, bolt spread, 1.5 ligament, hex-key access, end plates 6.5 to 8.5, bed contact, 0.5 install clearance, 0.10 self-report agreement. | Added to the L1 texts in `design.json` (L1.1 to L1.6, L1.8, L1.9, L1.11, L1.12). No L3 band changed. |
| 4 | Noted, not changed: the Feasibility lap leaves leave the upper and lower rims touching only at the bolt bosses (outer leaf bottom 0.2 above the lower rebate floor); this is designed contact (1.4) and the seam gap stays <= 0.5. L3.4.2.1 (nearest surface <= 4.0) is satisfied at exactly 2.0. | None needed. |

Residual uncertainty: gears are tip-diameter blanks (no teeth), so mesh quality is graded only by centre distance and root clearance; the generic `benchmarks/generalize/rubric.md` does not exist, so section 8 governs.
