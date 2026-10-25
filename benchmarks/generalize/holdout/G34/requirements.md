# G34 Sliding drawer with dovetail rails and magnet detent: requirements (L1 / L2 / L3)

A held-out generalisation target for the OpenSCAD assembly agent. It is modelled on E1-01
(`benchmarks/enclosure/requirements.md`) and uses the same ideas: catalogue parts placed from
datums, interference and clearance checks against reference models, numeric acceptance bands,
weights and gates. The machine-readable request (L1 only, `dev.json` format) is `design.json`
next to this file. How a blind judge applies this document is in section 7.

**Plan brief (verbatim):** "A small parts drawer 80 x 60 x 25 mm that slides in a housing on two
dovetail rails with 0.3 mm clearance per side. A 6 x 3 mm neodymium magnet pocket in the drawer and
another in the housing hold it closed with the magnets 0.5 mm apart. Stop the drawer at 70 mm
travel."

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check Python can run on the delivered STLs. Every row has
a method (inspection, analysis, demonstration, test, human, as in `design.json`), a pass/fail
criterion with a number and a tolerance, and a weight (3 = critical, 2 = major, 1 = minor). A `G<n>`
mark after the weight means the row is a gate: a failed gate makes the design WRONG (section 5).
Every number that comes from an assumption (section 3) is provisional until the owner confirms it.
Do not relax a criterion because the agent fails it; change a number only when the owner corrects an
assumption.

---

## 1. Frames, tolerances and the checks

### 1.1 Frame

- **Assembly frame:** X is the sliding axis and **+X is the pull-out direction**. Y is across the
  drawer, Z is up. In the **closed pose** the drawer's rear face is at X = 0, the drawer is centred
  on Y = 0 (rail tip to rail tip, Y = -30 to +30) and its underside is at Z = 0 (top at Z = 25). The
  housing's back wall inner face is at X = 0 as well (D3).
- The three STLs are delivered in this closed pose. A design delivered mirrored or rotated by
  multiples of 90 degrees is normalised into this frame before grading; that is never penalised. The
  judge records the transform.
- **Travel t** is the +X displacement of the drawer from the closed pose, in mm. The stop is in its
  delivered position for every sweep unless the row says "stop removed".

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered meshes, never by eye.

| Quantity | Tolerance e | Rule |
|---|---|---|
| length, distance, clearance, travel | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within e (for example "0.30 +/- 0.05" passes at 0.352) |
| angle | 0.5 degrees | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole / pocket diameter | largest inscribed circle of the section (what the magnet sees) | |
| sweep step | 1.0 mm travel (0.1 mm within 3 mm of a first contact) | first contact is reported to 0.1 mm |

### 1.3 The checks

- **`gap(A, B)`**: minimum Euclidean distance between bodies or regions A and B (0 when they touch,
  negative with the penetration volume reported when they overlap).
- **`slide(body, dx, dy, dz)`**: translate a body rigidly and report the intersection volume with
  every other body. **`sweep(t0, t1)`** is a series of `slide` calls along +X.
- **`first_contact(drawer, direction)`**: the smallest displacement along `direction` at which the
  drawer's intersection volume with any other body exceeds 0.01 mm3.

**Designed contact is not interference.** The pairs that are meant to touch are excluded from every
penetration and clearance check. For these only a penetration above 0.01 mm3 counts, and a distance
of zero is a pass:
- the drawer's rear face on the housing's back wall at the closed pose (the closed stop, D3);
- the stop in the housing hole it is seated in, and its head on the housing surface;
- the stop on the drawer at the stop position (the first-contact pair at t = 70);
- each magnet seated on its pocket floor, and each magnet in its pocket walls.

The rails and grooves are **not** designed contact: they run with a clearance (L2.2.4), so a rail
touching its groove is a defect.

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue:** `benchmarks/generalize/parts/magnet_disc_6x3/part.json` (N35 disc, 6.0 diameter x
  3.0 thick, +/-0.1 on both, axis `AXIS`, `BOTTOM` and `TOP` planes, `pocket_clearance` 0.15). It is
  the only catalogue part. All other numbers come from this document and the request text.
- **computed:** surfaces and regions measured on the delivered STLs.
- **envelope:** swept or offset volumes made by Python from the delivered bodies. The agent may
  generate the same volumes for its own checks, but its copies are not trusted for grading.

### 2.2 Reference models (M-) and bodies

| Name | What | Source | Size and position (assembly frame, mm, closed pose) |
|---|---|---|---|
| **DRAWER** | the drawer STL | design | bbox X 0..80, Y -30..30, Z 0..25 (L3.1.1.1) |
| **HOUSING** | the housing STL | design | back wall inner face X = 0; front face X = 80 (+/-0.5) |
| **STOP** | the stop STL | design | seated as delivered |
| **M-MAG-D** | disc magnet in the drawer pocket | catalogue `magnet_disc_6x3` | cylinder 6.0 x 3.0, axis along X through the drawer pocket's axis, seated on the pocket floor, magnet face towards -X |
| **M-MAG-H** | disc magnet in the housing pocket | catalogue `magnet_disc_6x3` | cylinder 6.0 x 3.0, axis through the housing pocket's axis, seated on the pocket floor, magnet face towards +X |
| **RAILS** | each drawer rail: the drawer's faces outside the tray body | computed | two solids, one per side; flank faces are the four planar faces joining the tray wall to the rail tip |
| **GROOVES** | each housing groove: the void the rails run in | computed | two regions open at the housing front |

M-MAG-D and M-MAG-H are placed by the grader from the pocket axes it measures in the STLs (and cross
checked against the manifest, L3.12.1.2). Nothing is placed by the design.

### 2.3 Envelopes (V-)

| Name | What | Definition |
|---|---|---|
| **V-TRAVEL(t)** | the drawer at travel t | DRAWER translated by (t, 0, 0) |
| **V-FLANK-k** (k = 1..4) | one rail flank and the groove flank facing it | the planar flank face of a rail (a patch with normal within 2 degrees of the section's flank normal) and the housing faces within 1.0 mm of it |
| **V-STOPPATH** | the stop's removal path | STOP translated along its removal axis (+Z, -Z, +/-X or +/-Y, whichever the manifest declares) by 0..100 mm |
| **V-ENGAGE(t)** | the rail length in the groove | length along X over which each RAIL has a GROOVE face within 1.0 mm of its flank at travel t |

---

## 3. Assumptions (A) and fixed decisions (D)

Every row is a decision the judge needs and the owner did not state. The value chosen is graded.
"Uncertainty" says what would change the number.

| # | Question | Value chosen | Why / uncertainty |
|---|---|---|---|
| **A1** | Which way does the drawer slide, and what are 80, 60 and 25? | 80 mm is the length along the sliding axis (X), 60 mm the width (Y), 25 mm the height (Z). | The only reading where a "drawer" 80 deep slides 70 and stops with 10 mm still inside. **Uncertainty: low.** |
| **A2** | Is 60 mm the width with or without the rails? | **With** the rails (D2): the drawer's overall box is 80 x 60 x 25. | The brief names one size for "a small parts drawer". If the owner meant the tray alone, the bands in L3.1.1.1 widen to 60 + 2 x rail protrusion. **Uncertainty: medium.** |
| **A3** | What does "0.3 mm clearance per side" mean for a dovetail? | The gap, measured **normal to the flank**, between each of the four rail flanks and its groove flank is 0.30 mm +/- 0.05 mm. The gap between the rail tip face and the groove bottom is 0.30 to 0.60 mm. | A flank-normal gap is what a printer's tolerance acts on. The side-to-side play follows from it (0.30 / sin(flank angle) = 0.33 to 0.40 mm). **Uncertainty: medium** (a side-to-side reading would give a flank gap 0.2 to 0.27). |
| **A4** | What does "magnets 0.5 mm apart" measure? | The distance between the two **facing magnet faces**, with each magnet seated on its pocket floor and the drawer shut (D3). Magnets are flush-recessed: each sits 0.25 mm below its wall surface. | Gap = recess in the drawer (0.25) + recess in the housing (0.25) with the surfaces touching. Pocket diameter = 6.0 + 0.15 (catalogue `pocket_clearance`); depth 3.25. **Uncertainty: medium** (magnet +/-0.1 mm thickness, printer). |
| **A5** | How is the 70 mm stop made, and how is the drawer assembled? | The stop is a **separate removable printed part** (a square pin from above through a square hole in the housing roof, hanging in the tray, bearing on the drawer's rear wall). With it removed the drawer slides straight out. | A printed drawer with a fixed stop cannot be assembled without a flexing latch. A flexing latch would show as interference. The owner can accept any other removable stop: the measured L3s (first contact, removal path, removal) do not depend on the pin. **Uncertainty: medium.** |
| **A6** | How steep must the dovetail flank be? | Each flank is **48 to 65 degrees** from the drawer's Y axis (horizontal). Rail protrusion 2.0 to 5.0 mm; the rail is narrower at its root than at its tip. | A flank at 45 degrees or less from the horizontal prints as an overhang. 48 degrees is the printable minimum with margin; 65 degrees is still a dovetail. **Uncertainty: low.** |
| **A7** | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed. Mating clearances 0.15 mm and more. No supports. | Common printers. **Uncertainty: low.** |
| **A8** | Wall thickness? | Housing roof, floor and back wall 2.0 to 5.5 mm; housing side walls 2.0 to 7.0 mm (they are thick on purpose: they hold the grooves). Drawer walls and floor 1.6 to 5.0 mm, back wall up to 6.0 mm (it carries the magnet pocket). | 4 to 5 perimeters at 0.4 line width. **Uncertainty: low.** |
| **A9** | Maximum size? | Housing outside <= 90 x 70 x 35 mm. | Stops oversized designs. A tight design is about 85 x 67 x 31. **Uncertainty: low.** |
| **A10** | Strength of the stop? | The stop's smallest section in the force path is at least 6.0 mm2; a 5 N pull is the design load. | 5 N / 6 mm2 = 0.8 MPa. **Uncertainty: low.** |
| **A11** | Tipping with the drawer out? | Not required. Only the closed assembly must be stable (L2.11.3). | A drawer pulled 70 mm out with a load can tip any lightweight housing. The owner did not ask. **Uncertainty: medium; confirm.** |
| A12 | Finger pull, label, lid for the drawer? | None needed. | Not in the brief. |
| A13 | Magnet polarity and glue? | Not modelled and not graded; the pockets are for glued magnets. | A reference magnet is an axis-symmetric cylinder. |

| # | Fixed decision (a choice that would otherwise be ambiguous) |
|---|---|
| **D1** | Frame as in 1.1. Sliding axis X, pull-out +X. |
| **D2** | The drawer's overall box (tray plus rails) is 80.0 x 60.0 x 25.0 mm, tolerance +/-0.3 on each. |
| **D3** | **Closed pose** = the drawer's rear face resting on the housing's back wall inner face (gap 0 to 0.10 at the delivered pose). Both magnets are recessed so that the magnet-to-magnet gap is 0.5 mm. |
| **D4** | Exactly **three** printed bodies: drawer, housing, stop. No screws, no glue geometry. |
| **D5** | **Travel** = the drawer's +X displacement from the closed pose to the first contact with the stop. |
| **D6** | The drawer carries the **male** dovetail rails; the housing holds the **female** grooves. (The rails are narrow at the root, wide at the tip, so the groove holds the drawer in Y and Z.) |
| **D7** | Each body's print orientation is stated in the manifest. Drawer: floor down. Housing: standing on its back wall (the cavity axis vertical); roof-down or floor-down fails L2.10.2 because the opposite wall bridges the 54 mm cavity. Stop: any. |
| **D8** | The stop's removal axis is one of +Z, -Z, +X, -X, +Y, -Y, declared in the manifest, and checked by sweeping. |

---

## 4. Requirements tree

### L1.1 The drawer is an open tray, 80 x 60 x 25 mm overall

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.1.1 | The drawer's overall box, rails included, is 80 x 60 x 25 mm (D2). | inspection | bbox X, Y, Z = 80.0, 60.0, 25.0, each +/-0.3 | 3 G2 |
| L3.1.1.1 | Drawer bounding box. | inspection | as L2.1.1 | 3 G2 |
| L2.1.2 | The drawer is an open-top tray that can hold parts. | analysis | cavity volume >= 40 cm3; a ray from the cavity centre along +Z leaves the drawer | 2 |
| L3.1.2.1 | Tray cavity volume (the enclosed void connected to the open top, between its walls and floor). | analysis | >= 40.0 cm3 | 2 |
| L3.1.2.2 | The cavity is open to +Z. | inspection | true | 2 |
| L2.1.3 | The drawer is symmetric about its centre plane. | inspection | the drawer's bbox centre Y = 0.0 +/-0.3 and the two rails mirror each other (section areas within 2%) | 1 |
| L3.1.3.1 | Drawer centre Y and rail mirror check. | inspection | as L2.1.3 | 1 |

### L1.2 Two dovetail rails run in two grooves with 0.3 mm clearance per side

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.2.1 | Two rails, one on each side of the drawer, running along X. | inspection | count = 2, one at +Y, one at -Y; each runs 72.0 to 80.0 mm along X | 3 |
| L3.2.1.1 | Rail count and side. | inspection | 2 (one per side) | 3 |
| L3.2.1.2 | Rail length along X. | inspection | 72.0 <= L <= 80.0 | 2 |
| L2.2.2 | The rail is a dovetail: protrusion 2.0 to 5.0 mm, flanks 48 to 65 degrees from Y, narrower at the root (A6, D6). | inspection | measured on a section at X = 40 | 3 |
| L3.2.2.1 | Rail protrusion beyond the tray wall (root to tip face). | inspection | 2.0 to 5.0 mm | 2 |
| L3.2.2.2 | Flank angle from the Y axis, all four flanks. | inspection | 48 to 65 degrees (+/-0.5) | 3 |
| L3.2.2.3 | Undercut: tip height minus neck height. | inspection | >= 2.0 mm | 2 |
| L3.2.2.4 | The section is constant along the rail. | inspection | section area at X = 10, 40, 70 within 2% of each other | 1 |
| L2.2.3 | The housing has two matching grooves open at its front face. | inspection | each groove flank within 1.0 degrees of the rail flank it faces; each groove runs >= 75 mm along X from the front face | 2 |
| L3.2.3.1 | Groove flank angle against rail flank angle. | inspection | difference <= 1.0 degrees | 2 |
| L3.2.3.2 | Groove length along X from the front face. | inspection | >= 75.0 mm | 2 |
| L2.2.4 | Clearance 0.3 mm per side (A3). | analysis | see rows | 3 G3 |
| L3.2.4.1 | Flank-normal gap, each of the four rail/groove flank pairs, at the closed pose: the median over a 1 mm grid of normal distances from points on the rail flank to the housing, over the engaged length. | analysis | median 0.25 to 0.35 mm for each pair; range (max - min) over each flank <= 0.10 mm | 3 G3 |
| L3.2.4.2 | Gap between each rail tip face and the groove bottom. | analysis | 0.30 to 0.60 mm | 2 |
| L3.2.4.3 | Side play: `slide(drawer, 0, +s, 0)` and `(0, -s, 0)`, smallest s with intersection above 0.01 mm3, at t = 35. | test | each direction 0.30 to 0.45 mm | 2 |

### L1.3 The drawer slides freely from closed to 70 mm, with at least 8 mm of rail still engaged

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.3.1 | Free travel: nothing touches the drawer on its way out. | test | `sweep(0, 69.0)`: intersection of V-TRAVEL(t) with HOUSING and with STOP <= 0.01 mm3 at every step | 3 G4 |
| L3.3.1.1 | Sweep clear from t = 0 to 69.0 (the closed contact with the back wall at t = 0 is designed). | test | 0 steps with penetration | 3 G4 |
| L2.3.2 | Running clearance everywhere except the rails. | analysis | gap(DRAWER without RAILS, HOUSING) >= 0.30 over `sweep(0, 70)`; the rear-face contact at t = 0 is excluded | 2 |
| L3.3.2.1 | Minimum gap, drawer tray (no rails) to housing, over the sweep, excluding the drawer rear face / back wall pair. | analysis | >= 0.30 mm | 2 |
| L3.3.2.2 | Vertical gaps at the closed pose: drawer top to housing roof underside, and drawer underside to housing floor top. | analysis | each 0.30 to 0.60 mm | 2 |
| L2.3.3 | Engagement and tilt at full travel. | test | rail engagement >= 8.0 mm; tilt bound | 3 |
| L3.3.3.1 | `V-ENGAGE(70.0)` for each rail. | analysis | >= 8.0 mm | 3 |
| L3.3.3.2 | Rotation clearance at t = 70.0: rotate the drawer about the Y axis through the middle of the engaged rail length (X = 75.0 at t = 70) at the drawer's mid-height (Z = 12.5), in both senses, and report the smallest angle at which it touches the housing. | test | 1.0 to 8.0 degrees | 2 |

### L1.4 With the stop in place the drawer stops at 70 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.4.1 | Travel to first contact with the stop is 70 mm (D5). | test | `first_contact(drawer, +X)` with STOP in place | 3 G5 |
| L3.4.1.1 | First contact distance t_stop. | test | 69.5 <= t_stop <= 70.5 (reported to 0.1) | 3 G5 |
| L3.4.1.2 | The first-contact pair is {drawer, stop}, not the drawer on the housing. | inspection | true | 2 |
| L2.4.2 | The stop bears on the drawer over a real area, and the housing holds the stop. | analysis | contact area at t_stop; the stop cannot be pushed out | 2 |
| L3.4.2.1 | Contact area between the drawer and the stop at t = t_stop (faces within 0.05 mm of each other, projected on the plane normal to X). | analysis | >= 6.0 mm2 | 2 |
| L3.4.2.2 | `slide(stop, +1.0, 0, 0)` with the drawer at t_stop intersects the housing (the housing carries the stop's load). | test | intersection > 0.01 mm3 | 2 |

### L1.5 The drawer and housing each have a magnet pocket; seated magnets are 0.5 mm apart

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.5.1 | One round pocket in the drawer's rear face and one in the housing's back wall, each for the 6 x 3 mm disc (A4). | inspection | count 1 + 1; axis within 1 degree of X | 3 |
| L3.5.1.1 | Pocket count and location (one in each of the two named faces). | inspection | 1 + 1 | 3 |
| L3.5.1.2 | Pocket diameter (largest inscribed circle at mid-depth), each. | inspection | 6.10 to 6.30 mm | 3 |
| L3.5.1.3 | Pocket depth along its axis, each. | inspection | 3.15 to 3.35 mm | 3 |
| L2.5.2 | The two pockets line up and have material around and behind them. | analysis | see rows | 3 |
| L3.5.2.1 | Pocket axes at the closed pose: distance between the two axes in the YZ plane, and angle to X. | analysis | <= 0.30 mm; <= 1.0 degrees | 3 |
| L3.5.2.2 | Ligament from each pocket's rim to the nearest edge of its wall face. | analysis | >= 1.5 mm | 2 |
| L3.5.2.3 | Material behind each pocket floor (the pocket floor to the body's far face along X). | analysis | >= 1.0 mm | 2 |
| L2.5.3 | The seated magnets are 0.5 mm apart (A4). | analysis | M-MAG-D and M-MAG-H seated on the pocket floors | 3 G6 |
| L3.5.3.1 | `gap(M-MAG-D, M-MAG-H)` at the delivered closed pose. | analysis | 0.40 to 0.60 mm | 3 G6 |
| L3.5.3.2 | Tolerance stack: worst-case gap = measured gap +/-0.4 (each pocket depth +/-0.10 and each magnet thickness +/-0.10). | analysis | measured gap - 0.4 >= 0.0 and measured gap + 0.4 <= 1.0 | 2 |
| L2.5.4 | Each magnet is recessed, not proud of its wall. | analysis | magnet face is below the wall surface | 2 |
| L3.5.4.1 | Recess of each seated magnet face below the surrounding wall surface (drawer rear face; housing back wall inner face). | analysis | 0.0 to 0.6 mm | 2 |
| L3.5.4.2 | Magnets lie inside their pockets. | analysis | M-MAG outside its body's pocket <= 0.01 mm3 and M-MAG vs the body's solid <= 0.01 mm3 beyond designed contact | 2 |

### L1.6 Shut, the drawer rests on the back wall, flush at the front, no interference

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.6.1 | Closed pose is the drawer's rear face on the back wall (D3). | analysis | gap between the two faces | 3 |
| L3.6.1.1 | Gap between the drawer rear face (outside the pocket) and the housing back wall inner face at the delivered pose. | analysis | 0.00 to 0.10 mm | 3 |
| L3.6.1.2 | Intersection of DRAWER with HOUSING and with STOP at the delivered pose. | analysis | <= 0.01 mm3 | 3 G3 |
| L2.6.2 | The front faces are flush. | inspection | drawer front face X minus housing front face X | 1 |
| L3.6.2.1 | Front face offset. | inspection | -0.5 to +0.5 mm | 1 |

### L1.7 The rails hold the drawer; play stays bounded

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.7.1 | The drawer cannot be lifted or moved sideways by 1 mm at any travel. | test | `slide` by 1.0 mm in each of +Z, -Z, +Y, -Y at t = 0, 35 and 70 | 3 |
| L3.7.1.1 | Each of the 12 slides (4 directions x 3 travels) intersects the housing. | test | intersection > 0.01 mm3 in all 12 | 3 |
| L2.7.2 | Vertical play is bounded. | test | total vertical play at t = 35 | 1 |
| L3.7.2.1 | Smallest +Z slide with contact plus smallest -Z slide with contact, at t = 35. | test | 0.40 to 1.20 mm | 1 |

### L1.8 Three separate parts go together by hand; with the stop removed the drawer slides out

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.8.1 | Exactly three printed bodies and no fasteners (D4). | inspection | 3 STLs: drawer, housing, stop | 3 G1 |
| L3.8.1.1 | Body count and no extra files carrying geometry. | inspection | 3 | 3 G1 |
| L2.8.2 | With the stop removed the drawer comes out; the stop comes out. | test | see rows | 3 G7 |
| L3.8.2.1 | Stop removed: `sweep(0, 200)` of the drawer against the housing. | test | 0 steps with penetration | 3 G7 |
| L3.8.2.2 | V-STOPPATH: STOP slid 0..100 mm along its declared removal axis with the drawer closed, against HOUSING and DRAWER. | test | intersection <= 0.01 mm3 at every step | 2 |
| L2.8.3 | The stop is not a fastener: it is held by its geometry. | inspection | no screws, nuts or glue geometry in the delivered set | 1 |
| L3.8.3.1 | Manifest lists no hardware other than the two magnets. | inspection | true | 1 |

### L1.9 Walls, rails and the stop are strong enough

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.9.1 | Housing roof, floor and back wall are 2.0 to 5.5 mm thick; its side walls 2.0 to 7.0 mm. | inspection | median thickness by ray casting on a 2 mm grid, 3 mm away from edges, openings and the stop hole | 2 |
| L3.9.1.1 | Housing thickness: left wall, right wall, roof, floor, back wall (each; side walls measured from the cavity face between the grooves). | inspection | roof, floor, back 2.0 to 5.5 mm; side walls 2.0 to 7.0 mm | 2 |
| L3.9.1.2 | Drawer thickness: side walls, front, floor (each) and the back wall. | inspection | 1.6 to 5.0 mm; back wall 1.6 to 6.0 mm | 2 |
| L2.9.2 | Rail necks and the material around the groove hold. | analysis | see rows | 2 |
| L3.9.2.1 | Rail neck height (the rail's section height at the tray wall). | analysis | >= 3.0 mm | 2 |
| L3.9.2.2 | Housing material above and below each groove (wall height beyond the groove's tip corners). | analysis | >= 2.0 mm | 2 |
| L3.9.2.3 | Ligament from the stop hole to the housing front face and roof edges. | analysis | >= 1.5 mm | 1 |
| L2.9.3 | The stop is strong enough for a 5 N pull (A10). | analysis | smallest section of the stop between its bearing face and its seat | 2 |
| L3.9.3.1 | Minimum cross-section area of the stop along its removal axis. | analysis | >= 6.0 mm2 | 2 |

### L1.10 All three bodies print on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.10.1 | Each body is one manifold shell. | analysis | 1 shell each; manifold3d builds it | 3 G1 |
| L3.10.1.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold = true | 3 G1 |
| L2.10.2 | In its stated print orientation (D7) no body has an unsupported overhang steeper than 45 degrees from vertical, except round holes of 12.0 mm or less in vertical walls and bridges of 15.0 mm or less. | analysis | 0 offending patches (area > 1 mm2) | 2 |
| L3.10.2.1 | Overhang and bridge scan per body. | analysis | as L2.10.2 | 2 |
| L2.10.3 | Drawer and housing rest on a flat face. | analysis | bed contact >= 50% of the plan bounding box (not applied to the stop) | 1 |
| L3.10.3.1 | Bed contact per body (drawer and housing). | analysis | >= 50% | 1 |
| L2.10.4 | No feature thinner than 0.8 mm; mating clearances 0.15 mm or more. | analysis | thin-feature scan; smallest running gap | 1 |
| L3.10.4.1 | Thin features and mating gaps. | analysis | min wall >= 0.8; min mating gap >= 0.15 | 1 |
| L2.10.5 | Each body fits a 200 x 200 x 200 build volume. | inspection | bbox <= 200 per axis | 1 |
| L3.10.5.1 | Bounding box per body. | inspection | <= 200 | 1 |

### L1.11 The housing is compact, has a flat underside and stands without tipping

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.11.1 | Housing outside size <= 90 x 70 x 35 mm, sliding axis the longest. | inspection | X <= 90.0, Y <= 70.0, Z <= 35.0; X > Y | 1 |
| L3.11.1.1 | Housing bounding box (STOP head included). | inspection | as L2.11.1 | 1 |
| L2.11.2 | The housing has a flat underside. | inspection | flatness <= 0.2; contact area >= 50% of the plan bounding box | 1 |
| L3.11.2.1 | Underside planarity and contact. | inspection | as L2.11.2 | 1 |
| L2.11.3 | The closed assembly stands without tipping (A11). | analysis | stable at 5 degrees of table tilt, mass = volume x 0.45 g/cm3 for the three bodies plus 60 g of drawer contents at the drawer's centre | 1 |
| L3.11.3.1 | Centre of mass inside the support polygon at 5 degrees tilt in every direction. | analysis | margin >= 0 | 1 |

### L1.12 The package says what was built and where, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt |
|---|---|---|---|---|
| L2.12.1 | The package holds `drawer.stl`, `housing.stl`, `stop.stl` (closed pose, assembly frame, mm), the `.scad` source, `manifest.json` (magnet axes and depths, stop removal axis, each body's print orientation) and the agent's own report. | inspection | all present and readable | 3 G0 |
| L3.12.1.1 | Files present and parse; each STL's largest bounding-box axis is within 20 to 200 mm (units check). | inspection | true | 3 G0 |
| L3.12.1.2 | The manifest's magnet axes and depths, and the stop's removal axis, agree with the STLs. | analysis | axes within 0.30 mm; depths within 0.10; removal axis passes L3.8.2.2 | 3 |
| L2.12.2 | The agent's own report agrees with the judge. | analysis | every gap and travel the report states: same pass/fail, difference <= 0.10 mm | 1 |
| L3.12.2.1 | Self-report against judge. | analysis | 100% within 0.10 | 1 |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 36 |
| L3 | 60 |

**Gates** (a failure makes a design WRONG regardless of score): G0 package (L3.12.1.1); G1 three
manifold bodies (L3.8.1.1, L3.10.1.1); G2 drawer size (L3.1.1.1); G3 rail clearance and no
interference when closed (L3.2.4.1, L3.6.1.2); G4 free travel (L3.3.1.1); G5 the stop works
(L3.4.1.1); G6 magnet gap (L3.5.3.1); G7 assembly (L3.8.2.1).

---

## 6. Feasibility

A concrete design that meets every row exists. Key dimensions (assembly frame, mm):

**Drawer.** Tray outer X 0..80, Y -27..+27, Z 0..25. Side walls 2.4, front panel X 77.6..80, floor
2.4, **rear wall 4.3** (X 0..4.3). Two rails, protrusion 3.0 (Y 27..30), neck height 3.4 (Z 15.3..18.7 at the tray wall), flanks 50 degrees from Y, so the tip face is 3.4 + 2 x 3.0 x tan 50 = 10.55 tall (Z 11.73..22.27). Rails run the full 80 mm. Bounding box 80 x 60 x 25 (L3.1.1.1). Cavity volume about
(54 - 4.8) x (77.6 - 4.3) x (25 - 2.4) = 81 cm3. Magnet pocket in the rear face: diameter 6.15, depth
3.25, axis along X at Y = 0, Z = 12.5; material behind it 4.3 - 3.25 = 1.05 (>= 1.0).

**Housing.** Outer X -5.0..80.0 (85.0), Y +/-33.6 (67.2), Z -2.8..28.3 (31.1). Cavity Y +/-27.4 (0.4 from the tray walls; side walls 33.6 - 27.4 = 6.2 thick), floor
top Z = -0.3, roof underside Z = 25.3, back wall X -5.0..0 (5.0). Two grooves = the rail's two flanks shifted 0.3 mm along their normals (flank-normal gap 0.30), the groove bottom at Y = 30.4 (tip face to groove bottom 0.40), open at the front face. Wall beyond the groove tip 33.6 - 30.4 = 3.2. Magnet pocket in the back wall: diameter 6.15, depth 3.25,
axis along X at Y = 0, Z = 12.5, from X = 0 to X = -3.25; material behind it 1.75. Vertical gaps:
drawer underside to floor 0.30, drawer top to roof 0.30 (L3.3.2.2). Printed standing on its back wall (X down, 100% bed contact): the cavity is a vertical shaft, the groove flanks are vertical faces, the magnet pocket opens upward, the square stop hole is a 3.4 bridge. (Roof-down would bridge the 54.8 wide floor.)

**Magnet gap.** Each magnet sits 0.25 below its wall surface; the surfaces touch at the closed pose
(gap 0.00). Gap = 0.25 + 0.25 = **0.50** (L3.5.3.1). Tolerance stack: 0.5 +/- 0.4 gives 0.1 to 0.9
(L3.5.3.2).

**Stop.** A square pin 3.0 x 3.0 (section 9.0 mm2 >= 6.0) with a 6.0 x 6.0, 2.0 thick head, through a 3.4 x 3.4 square hole in the roof (X 74.1..77.5, 0.2 per side, so the mating gap is >= 0.15), pin centre X = 75.8, Y = 0. The pin hangs to Z = 17.0 (8 mm overlap with the drawer's
rear wall, which is 25 tall). The pin's rear face is at X = 74.3. The drawer's rear wall front face
is at X = 4.3 + t, so first contact at **t = 74.3 - 4.3 = 70.0** (L3.4.1.1). The pin's front face
(X 77.3) is 0.3 behind the drawer front panel's inner face (X 77.6), so the sweep is clear (L3.3.1.1).
Contact area: the pin's flat 3.0 wide face over the 8 mm overlap, 24 mm2 (>= 6.0; a round pin would touch along a line, about 6 mm2 inside the 0.05 band). Pin hole to housing front face 80.0 - 77.5 = 2.5 (>= 1.5).

**Engagement and tilt.** Housing groove X 0..80; rail rear end at X = 70 at t = 70, so engagement
**10.0 mm** (>= 8.0). Vertical play 0.30 up and 0.30 down (floor and roof gaps), so tilt about the
middle of the engaged length (5 mm from each end) is atan(0.30 / 5.0) = **3.4 degrees** (within 1.0 to
8.0). Side play: the flank pair closes at 0.30 / sin 50 = **0.39**, the tray wall and the tip face at 0.40 (within 0.30 to 0.45; the first Feasibility had the tray wall and tip at 0.30, on the limit). Total vertical play 0.60 (within 0.40
to 1.20).

**Assembly.** Pull the pin; the drawer slides out along +X with 0.3 clearance everywhere (L3.8.2.1);
push it in until its rear face meets the back wall (closed pose); drop the pin through the roof
hole (removal axis +Z, L3.8.2.2). Housing 85.0 x 67.2 x 31.1, 33.1 high with the stop head (<= 90 x 70 x 35).

---

## 7. Grading notes (design-specific rubric)

`benchmarks/generalize/rubric.md` did not exist when this file was written, so the grading
procedure is given here. It follows `benchmarks/enclosure/rubric.md` and should be replaced by a
pointer to the generic rubric when that exists.

1. **Package gate (G0).** The three STLs, source, manifest and report exist and load; otherwise stop:
   DOES NOT MEET with one defect on L3.12.1.1.
2. **Load and units.** Load each STL (trimesh, then manifold3d `Manifold`; recipe in
   `benchmarks/enclosure/rubric.md` section 3.1). `status()` must be NoError; count shells with
   `decompose()`. A bounding-box axis outside 20 to 200 mm is a units defect: record it, do not
   rescale.
3. **Normalise the frame** (section 1.1) with 90 degree rotations and mirroring only; record it.
4. **Build the references independently** from the pocket axes measured in the STLs, then run
   every L3 in requirement order with Python. Record the measured value, the limit, the margin
   (signed, negative = fail) and PASS, FAIL or UNVERIFIED. **UNVERIFIED counts as FAIL.**
5. **Recipes.** Sweeps: `Manifold.translate` of the drawer and `(a ^ b).volume()` for the
   intersection. Flank gap: sample the planar flank patches on a 1 mm grid and take
   `trimesh.proximity.closest_point` distances to the housing mesh. Pocket diameter and depth: slice
   perpendicular to the pocket axis at mid-depth, largest inscribed circle; ray cast along the axis
   for depth. Wall thickness: ray casting through the wall on a 2 mm grid. Overhang: faces with unit
   normal n_z < -cos 45 degrees, in the stated print orientation, exempting round holes <= 12 mm
   in vertical walls and bridges <= 15 mm. Stability: centre of mass from volumes at 0.45 g/cm3.
6. **Verdict.** WRONG: any gate fails. MINOR: no gate fails but a weight-3 L3 fails. CORRECT: no
   gate fails and every weight-3 L3 passes. **MEETS requirements** = CORRECT and every applicable
   non-physical L3 of weight 1 and 2 passes. Report also the weighted score
   sum(weight x pass) / sum(weight) and the worst normalised margin among weight-3 rows.
7. **Precedence.** The numbers in this document beat any number in a part.json. Designed contact
   (section 1.3) is never interference. The first-contact distance (L3.4.1.1) outranks every
   statement about how the stop is built.
8. **Where a defect is.** One entry per failed or UNVERIFIED L3: `req` (L3, L2, L1), `status`,
   `body` (drawer, housing, stop, layout), `feature` (named by function and SCAD name if known),
   `face` (which surface and its outward normal), `location` (mm, assembly frame, point or box),
   `measured` / `limit` / `margin`, `reference` (the sweep step, reference magnet or flank), `render`,
   `evidence` (saved defect STL), `needed` (the geometric change as a verifiable number, never a
   design instruction). Group L3s that fail for one geometric reason.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | Words in the request it comes from |
|---|---|---|---|---|
| L1.1 | Drawer size and form | L2.1.1-L2.1.3 | L3.1.1.1, L3.1.2.1-2, L3.1.3.1 | "small parts drawer", "80 mm long, 60 mm wide and 25 mm tall" |
| L1.2 | Dovetail rails, clearance | L2.2.1-L2.2.4 | L3.2.1.1-2, L3.2.2.1-4, L3.2.3.1-2, L3.2.4.1-3 | "two dovetail rails", "0.3 mm of clearance per side" |
| L1.3 | Free travel and engagement | L2.3.1-L2.3.3 | L3.3.1.1, L3.3.2.1-2, L3.3.3.1-2 | "slides", "70 mm of travel" |
| L1.4 | Stop | L2.4.1-L2.4.2 | L3.4.1.1-2, L3.4.2.1-2 | "stop at 70 mm of travel so it cannot be pulled out" |
| L1.5 | Magnet pockets and gap | L2.5.1-L2.5.4 | L3.5.1.1-3, L3.5.2.1-3, L3.5.3.1-2, L3.5.4.1-2 | "6 x 3 mm neodymium disc magnet ... pocket ... 0.5 mm apart" |
| L1.6 | Closed pose | L2.6.1-L2.6.2 | L3.6.1.1-2, L3.6.2.1 | "with the drawer shut", "hold it closed" |
| L1.7 | Rails hold the drawer | L2.7.1-L2.7.2 | L3.7.1.1, L3.7.2.1 | "slides in a printed housing on two dovetail rails" |
| L1.8 | Assembly | L2.8.1-L2.8.3 | L3.8.1.1, L3.8.2.1-2, L3.8.3.1 | "must still come out for assembly", "separate printed parts ... by hand with no screws" |
| L1.9 | Strength | L2.9.1-L2.9.3 | L3.9.1.1-2, L3.9.2.1-3, L3.9.3.1 | implied (printed parts, pulled by hand) |
| L1.10 | Printable | L2.10.1-L2.10.5 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1, L3.10.5.1 | "printed on an FDM printer without supports" |
| L1.11 | Compact, stable | L2.11.1-L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | implied (desk object) |
| L1.12 | Evidence | L2.12.1-L2.12.2 | L3.12.1.1-2, L3.12.2.1 | needed by the judge (not in the request) |

---

## Audit

Adversarial audit. The Feasibility design was rebuilt in manifold3d (drawer, housing, stop: 1 shell each, manifold) and its sweeps run: no interference closed, sweep 0 to 69 clear,
first contact with the stop at t = 70.0 (pin 74.3, rear wall 4.3), engagement 10, side play 0.40, vertical slides contact at 0.30, rotation at t = 70 first touches at 3.3 / -3.4 degrees,
stop removed sweep 0 to 200 clear, stop path clear, magnet gap 0.500, cavity 81.5 cm3. `magnet_disc_6x3` loads and passes `parts.validate` and `parts.gate`. L1 12, L2 36, L3 60 recounted (`design.json` has 12).

1. **Infeasible print orientation (L2.10.2).** The Feasibility printed the housing roof-down, which leaves the floor as a 54.8 x 80 bridge (limit 15.0); any roof- or floor-down tube fails.
   D7 and the Feasibility now stand the housing on its back wall (no bridge, 100% bed contact).
2. **Stop contact area (L3.4.2.1).** A round dia 3.0 pin touches the flat rear wall along a line: about 6 mm2 inside the 0.05 band, on the 6.0 limit, not the 24 mm2 claimed.
   The pin is now square 3.0 x 3.0 (24 mm2), with a 3.4 square hole (a 3.0 pin in a 3.0 hole broke the 0.15 mating gap of L3.10.4.1, and L3.4.2.2 needs a clearance to slide into).
3. **Margins on limits.** Side play was exactly 0.30 (the lower limit; tray wall and tip face met the housing first, not the flank pair): cavity now 0.4 from the tray, tip gap 0.4, side play 0.39 / 0.40.
   Rail neck 3.0 (the limit) is now 3.4; tip face recomputed (10.55 tall). Housing outer size with the stop head is 33.1 high, stated.
4. **Hidden numbers.** The bands for flank angle and protrusion (L3.2.2.x), play and gaps (L3.2.4.3, L3.3.2.x, L3.7.2.1), tilt (L3.3.3.2), stop contact area (L3.4.2.1), and magnet pocket size and recess (L3.5.1.x, L3.5.4.1)
   were in neither the request nor an L1. They are now in L1.2, L1.3, L1.4, L1.5 and L1.7 (and `design.json`).
5. **L3.3.3.2** left the rotation axis height open; it is now the drawer's mid-height (the result moves by under 0.5 degree, 3.1 to 3.7, over Z = 0 to 25).
6. Checked, no change: 80 x 60 x 25 includes the rails (D2), request and L1 agree; the flank-normal gap 0.30 gives side play 0.33 to 0.40 over 48 to 65 degrees; magnet gap 0.25 + 0.25 = 0.50 and the stack 0.1 to 0.9;
   groove 80 long against engagement 10 (>= 8); drawer cavity 81 cm3 (>= 40); material behind each pocket 1.05 / 1.75; wall bands 2.4 / 4.3 / 2.5 / 3.0 / 6.2.
