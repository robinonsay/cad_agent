# G23 RPi camera pocket mount with 1/4-20 base: requirements (L1 / L2 / L3)

Generalisation design G23 (train split). It is the error signal for the control loop on a
mechanical-mount family: one board in a pocket, a window and a field of view kept clear, a ribbon
slot, a captive hex nut, one printed body printed without supports. The machine-readable request
(L1 only, `dev.json` format) is `design.json` next to this file. It is graded the way
`benchmarks/enclosure/requirements.md` grades E1-01: Python measures the delivered STL against
reference models built from the catalogue (`benchmarks/generalize/parts/*/part.json`).

**Request (owner's words):** "A holder for a Raspberry Pi camera v2 (25 x 24 x 9 mm, holes
21 x 12.5 mm) with the lens window clear of any wall at 8 mm diameter. The base has a 1/4-20 hex
nut pocket so I can put it on a tripod. The ribbon cable exits the back through a 17 mm wide
slot." The expanded request in `design.json` adds only what section 3 derives.

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check on the geometry. Every row has a verification
method (`dev.json` definitions), a pass/fail criterion with a number and tolerance, a weight
(3 = critical, 2 = major, 1 = minor) and a gate mark (G0 to G5) where failing it makes the design
WRONG. Do not relax a criterion because the agent fails it; change a number only when the owner
corrects an assumption (section 3).

**Grading procedure.** `benchmarks/generalize/rubric.md` holds the generic judge procedure. If that
file is missing, use section 9 of this document, which is self-sufficient.

---

## 1. Frames, tolerances and the checks

### 1.1 Frames

- **Camera frame (all tables below):** the catalogue frame of the camera part: origin at the PCB's
  min corner, PCB bottom at Z = 0 (PCB Z 0 to 1.0), X across the 25 mm side, Y along the 24 mm side
  with the ribbon-connector edge at Y = 0, the lens looking along **+Z** (the front is +Z; the back
  is -Z).
- **Base side:** the base face is on the **-Y** side, so the tripod stud enters along **+Y**. A
  design delivered rotated about Z by multiples of 90 degrees or mirrored is normalised into this
  frame before grading (the camera pose in `layout.json` is transformed with it); that is never
  penalised.
- **Print frame:** the stated print orientation; default is the back (-Z) face down, so Z is up.

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, distance, clearance, travel | 0.02 mm | a value passes if it meets the limit to within e |
| angle | 0.5 deg | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole diameter | largest inscribed circle of the hole's section | what a stud sees |
| hex pocket across flats | distance between opposite flat faces, median along the flat | |

### 1.3 The checks

- **`clear_of(bodies, volume, clearance)`**: minimum distance between the printed body and `volume`
  is >= `clearance` (negative = penetration; volume reported). Pass: d >= clearance - e.
- **`travel(part, axis)`**: free rigid travel. Slide the reference part (rigid translation) along
  `axis` in both directions from its declared pose until the first printed contact (a penetration
  above 0.01 mm3); the value is the total range, contact to contact. Unbounded within 100 mm fails
  any limit.
- **`sweep(part, direction)`**: translate the part along `direction` from 40 mm outside the holder to
  its seated pose in 0.5 mm steps; the union of the positions is the swept volume; pass if the
  holder, excluding the allowed regions, has intersection <= 0.01 mm3 and distance >= the stated
  clearance with it.

**Designed contact is not interference (owner rule, 2026-10-24).** For G23 the designed contacts are:
- the camera PCB's underside resting on the edge supports (inside the support footprint);
- a retaining lip's tip over the PCB's front face at the gap in L2.3.2;
- the tripod stud in its through hole, the hex nut seated on its seat face and against its flats.

For these pairs only penetration counts (intersection above 0.01 mm3); a distance of zero is a pass.

**Allowed region in `sweep` for the board: the retaining lips.** A lip may flex (A8), so printed
material in the slab Z from the PCB's top plane (Z 1.0) to 2.0 above it, whose plan lies within
1.5 mm of the PCB outline on the inside, is excluded from the board's install sweep. Nothing else is.

---

## 2. Reference models, envelopes and datums

### 2.1 Reference models (M-)

| Name | What | Source | Size and datums (camera frame, mm) |
|---|---|---|---|
| **M-CAM** | Raspberry Pi camera v2 | `rpi_camera_v2` | PCB 25.0 x 24.0 x 1.0 (Z 0 to 1.0); lens barrel Ø8.0, Z 1.0 to 9.0 at X 12.5, Y 14.5; ribbon connector 21.0 x 5.5 x 2.0 at X 2.0 to 23.0, Y 0 to 5.5, Z -2.0 to 0; four holes Ø2.2 at (2.0, 2.0), (23.0, 2.0), (2.0, 14.5), (23.0, 14.5). Datums `LENS_AXIS`, `LENS_POINT` (Z 9.0), `PCB_BOTTOM`, `PCB_TOP`, `HOLE` |
| **M-STUD** | tripod stud 1/4-20 | `camera_screw_1_4_20` | shank Ø6.35, length 10.0 (request) inserted along +Y from the base face; hex nut 11.1 across flats (across corners 12.8) x 5.6 thick |

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-LENS-CLEAR** | lens window | cylinder Ø9.0 (8.0 + 2 x 0.5) on `LENS_AXIS` from Z 1.0 to 9.0, plus cylinder Ø10.0 (the catalogue `fov_aperture`, margin 1.0) from Z 9.0 to 19.0 (10.0 deep) |
| **V-LENS-BARREL** | the lens barrel | M-CAM's cylinder Ø8.0, Z 1.0 to 9.0 |
| **V-FOV** | field of view | the frustum from `LENS_POINT` (Z 9.0): half-width 4.0 at Z 9.0 growing at tan 31.1 degrees to Z 19.0, on both X and Y (A4: the larger half-angle on both axes) |
| **V-RIBBON** | ribbon path | box X 4.5 to 20.5 (16.0 wide, centred on the connector, A5), Y 2.25 to 3.25, Z from -2.0 to -22.0 (a 20 mm straight run behind the connector) |
| **V-STUD** | stud and its path | cylinder Ø6.35, 10.0 long, on the stud axis, from the base face (outside) inward along +Y |
| **V-NUT** | seated nut | hex prism 11.1 across flats x 5.6 thick, on the stud axis, its back face on the seat |
| **V-NUT-SWEEP** | nut insertion | V-NUT swept straight from 40 mm outside its pocket to its seat, along one axis |
| **V-CAM-SWEEP** | board installation | M-CAM swept from 40 mm outside along the declared `INSTALL_DIR` to its seated pose |
| **V-AP-SLOT** | the opening(s) in the back wall | the wall's slab (inner to outer face), full X and Y extent, minus the printed body; regions under 1 mm3 ignored |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Check | Pass |
|---|---|---|
| R1 | units: bounding box in mm | M-CAM PCB 25.0 x 24.0 +-0.2; total height with the lens 9.0 +-0.3 above the PCB bottom |
| R2 | M-CAM holes | Ø2.2 +-0.1; pattern 21.0 x 12.5 +-0.1 |
| R3 | M-STUD | shank Ø6.35 +-0.05; nut 11.1 +-0.1 across flats; 5.6 +-0.1 thick |
| R4 | every V- envelope's datums equal its model's datums | <= 0.01 |

**Seating rule.** The grader places M-CAM at the pose in `layout.json`, then verifies the declaration:
`PCB_BOTTOM` lies on the supports (distance <= 0.10) and the PCB's edges are within the pocket. If
the declaration is missing or fails, the camera is seated by that fit instead; if there are no
supports it is placed with its underside 2.0 above the lowest internal face, and L3.2.2.1 fails.

---

## 3. Assumptions, uncertainty and fixed decisions

| # | Question | Value chosen | Uncertainty and why |
|---|---|---|---|
| A1 | Board and lens | PCB 25 x 24 x 1.0; lens Ø8 centred across at Y 14.5; total height 9.0 | PCB thickness +-0.1; lens Y +-0.5 (assumed level with the upper hole row). Datasheet drawing |
| A2 | Mounting holes | four Ø2.2 at 2.0 from the edges (21 x 12.5 pattern) | 2.0 from the edges is assumed (+-0.3). Not used for a fastener here (A8); only to keep screw-head access free if a design uses them |
| A3 | "Lens window clear of any wall at 8 mm" | no printed surface within 0.5 of the lens barrel (Ø9.0 free), plus the catalogue's Ø10.0 x 10.0 keep-out in front of the lens | the owner's 8 mm is the barrel; zero clearance would touch. 0.5 is the usual FDM margin; +-0.2 |
| A4 | Field of view | 62.2 degrees horizontal x 48.8 vertical (datasheet) | which sensor axis is along the 25 mm side is not given; the larger half-angle (31.1 degrees) is used on both axes (conservative) |
| A5 | Ribbon | 15-way 1.0 pitch FFC: 16.0 wide, 1.0 thick envelope, leaving the connector straight back (-Z) at Y 2.25 to 3.25, a 20 mm straight run | +-1.0 on width, +-0.5 on position. The slot is 17.0 (the owner) = 16.0 + 2 x 0.5. The catalogue's 21 x 8.5 `ffc_cable` box is a generic estimate and is superseded here by V-RIBBON; the slot, not that box, is graded |
| A6 | Nut | 1/4-20 UNC hex 11.1 across flats x 5.6 thick (ASME B18.2.2); pocket across flats 11.3 to 11.7 (0.1 to 0.3 per flat); stud hole Ø6.4 to 6.8 (ASME clearance 6.6 +-0.2) | FDM hole shrinkage +-0.1 |
| A7 | Tripod stud | 10.0 mm long, Ø6.35; the stud must pass through the whole nut (5.6) and show at least 0.75 beyond it, so the seat is at most 10.0 - 5.6 - 0.75 = 3.65 thick (the usual one-diameter, 6.35, thread engagement cannot exceed the 5.6 nut) | the owner did not give a stud length; typical tripod studs are 5 to 10 mm, and 10.0 is the longest common, so the check is conservative. Seat at least 2.0 for stiffness (A11) |
| A8 | Retention | no screws; supports under two opposite edges, at least two lips over the front face, each reaching 0.6 to 1.15 over the board; travel limits 0.8 sideways, 1.0 out | the board does not flex (1.0 mm FR4), so a lip must flex to let it in: install deflection per lip = overlap - edge clearance, at most 1.15 - 0.15 = 1.0, which a printed lip at 1.2 or more thick can give by the spring of its wall. The flex itself is not graded (the sweep excludes the lip slab); only the geometry that makes it possible is. +-0.3 |
| A9 | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed; pocket per-edge clearance 0.15 to 0.35; round holes up to Ø12 and bridges up to 15 print without support; a hex pocket prints without support when a vertex points up; a downward-facing ledge no deeper than 1.5 beyond the wall that carries it prints without support (a short cantilever of about 8 layers; the retaining lips are such ledges: edge clearance 0.35 + overlap 1.15 = 1.5 at most) | common printers; the clearance band is the standard FDM sliding fit |
| A10 | Size limit | 45 x 45 x 30 | about 31 x 39 x 22 is the tight design (section 6); stops oversized holders |
| A11 | Wall thickness | 2.0 to 4.0 for the pocket walls and the back wall; at least 1.6 of printed material around the nut pocket and the stud hole | 5 perimeters; 4 perimeters around a pocket |
| A12 | Tripod orientation | the stud axis is in the PCB plane (perpendicular to the lens axis), on the ribbon-connector side, centred across the board | a camera on a tripod looks horizontally and its image "up" is away from the connector edge; a stud under the centre keeps it balanced. +-1.0 |
| A13 | Mass and load | board 3 g; not graded for strength | the holder supports only the board; the nut and stud are steel |

### Fixed decisions

| # | Decision |
|---|---|
| FD1 | Camera frame as in 1.1; the base is on the -Y side. A holder with the base on another side is rotated or mirrored before grading. |
| FD2 | One printed body. A separate cover, clip or screw is not accepted. |
| FD3 | The back wall has one slot only for the ribbon; the front (+Z) side has no wall that crosses the lens window, so the "window" is the open front or a hole of at least Ø10.0. Either is graded by V-LENS-CLEAR and V-FOV. |
| FD4 | The board installs along one axis direction (declared as `INSTALL_DIR` in `layout.json`, any of +-X, +-Y, +-Z). |
| FD5 | "Designed contact" includes the hex nut seated on its seat and against its flats, nothing else printed touches M-CAM except the supports and lips. |

---

## 4. Requirements tree

### L1.1 The camera is placed and the layout is declared

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: the pose of M-CAM, `INSTALL_DIR`, the stud axis (point and direction) and the print orientation. | inspection | `layout.json` present, parses, catalogue ids exist | 3 | |
| L3.1.1.1 | Layout file parses and ids exist. | inspection | true | 3 | |
| L2.1.2 | The lens looks along +Z; the stud axis is perpendicular to it; the base is on -Y. | inspection | lens axis within 1.0 deg of +Z; stud axis within 2.0 deg of +Y; stud enters from the -Y face | 2 | |
| L3.1.2.1 | Datum directions in the declared layout. | inspection | as L2.1.2 | 2 | |

### L1.2 The board sits in a pocket on supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | No printed surface touches the board except its supports and lips: the PCB, lens and connector all clear. | analysis | clear_of(BODY, M-CAM, 0.15), the PCB-bottom support contact and the lip tips excluded | 3 | G2 |
| L3.2.1.1 | Clearance of M-CAM to every printed surface other than the supports and lips. | analysis | d >= 0.15 | 3 | G2 |
| L3.2.1.2 | Clearance per PCB edge (four edges, median along the edge). | inspection | 0.15 <= gap <= 0.35 | 2 | |
| L2.2.2 | The PCB's underside rests on printed supports under two opposite edges. | analysis | contact area (printed within 0.10 below the PCB bottom) >= 40 mm2; the support centroids at least 12.0 apart; the support top faces coplanar within 0.10 | 2 | |
| L3.2.2.1 | Support area and spread. | analysis | area >= 40; centroid distance >= 12.0 | 2 | |
| L3.2.2.2 | Support top planarity and PCB bottom seating. | inspection | top-plane spread <= 0.10; `PCB_BOTTOM` within 0.10 of the support tops | 2 | |
| L2.2.3 | The ribbon connector clears the holder. | analysis | clear_of(BODY, connector body, 0.2) | 3 | |
| L3.2.3.1 | Connector clearance. | analysis | d >= 0.20 | 3 | |

### L1.3 The board is held without screws

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Rigid free travel of M-CAM against the body: across X and across Y each <= 0.8, out of the pocket (+Z) <= 1.0. | analysis | `travel` as stated | 3 | G2 |
| L3.3.1.1 | Travel along X and along Y (each axis, total range). | analysis | each <= 0.80 | 3 | G2 |
| L3.3.1.2 | Travel toward the front (+Z) from the seat. | analysis | <= 1.00 | 3 | |
| L2.3.2 | At least two retaining lips over the PCB's front face, on opposite halves of the board. | inspection | count >= 2; overlap with the PCB outline 0.6 to 1.15 each; gap from lip underside to PCB top <= 0.4; lip thickness >= 1.2; centroids on opposite sides of the PCB centre | 2 | |
| L3.3.2.1 | Lip count, overlap, gap, thickness. | inspection | as L2.3.2 | 2 | |
| L3.3.2.2 | Opposed lip centroids. | inspection | on opposite sides of the PCB's centre along X or along Y | 1 | |

### L1.4 The lens window is clear

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Nothing printed inside the lens keep-out. | analysis | clear_of(BODY, V-LENS-CLEAR, 0.0) | 3 | G3 |
| L3.4.1.1 | Lens keep-out free. | analysis | d >= 0.0 | 3 | G3 |
| L2.4.2 | Nothing printed inside the field of view. | analysis | clear_of(BODY, V-FOV, 0.0) | 3 | G3 |
| L3.4.2.1 | Field-of-view pyramid free. | analysis | d >= 0.0 | 3 | G3 |
| L2.4.3 | The lens barrel has at least 0.5 to every printed surface. | analysis | clear_of(BODY, V-LENS-BARREL, 0.5) | 2 | |
| L3.4.3.1 | Barrel clearance. | analysis | d >= 0.50 | 2 | |

### L1.5 The ribbon cable leaves through a 17 mm slot in the back

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | A slot through the back wall, 17.0 wide. | inspection | V-AP-SLOT has one region over the connector; its width across X (largest inscribed rectangle) is 17.0 +-0.3 | 3 | G4 |
| L3.5.1.1 | Slot width. | inspection | 16.7 to 17.3 | 3 | G4 |
| L3.5.1.2 | One slot only in the back wall. | inspection | 1 region | 2 | |
| L2.5.2 | The ribbon's straight path behind the connector is clear. | test | clear_of(BODY, V-RIBBON, 0.4) | 3 | G4 |
| L3.5.2.1 | Ribbon envelope clear. | test | d >= 0.40 | 3 | G4 |
| L2.5.3 | The slot is no bigger than needed and has material around it. | analysis | slot length along Y <= 10.0; ligament from the slot edge to any other opening, the wall edge or a wall >= 1.5 | 1 | |
| L3.5.3.1 | Slot length along Y. | inspection | <= 10.0 | 1 | |
| L3.5.3.2 | Ligament around the slot. | analysis | >= 1.5 | 1 | |

### L1.6 The base holds a captive 1/4-20 nut

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | A hex pocket sized to the nut: across flats 11.3 to 11.7, depth 6.35 to 9.0 measured from the seat. | inspection | as stated | 3 | G5 |
| L3.6.1.1 | Pocket across flats (median over the bounded flats). | inspection | 11.30 to 11.70 | 3 | G5 |
| L3.6.1.2 | Pocket depth from the seat to its far end. | inspection | >= 10.0 minus the seat thickness (so the stud tip is free) and <= 9.0 | 2 | |
| L2.6.2 | The stud hole, coaxial with the pocket. | inspection | Ø 6.4 to 6.8; axis offset from the pocket axis <= 0.2 | 3 | |
| L3.6.2.1 | Stud-hole diameter and coaxiality. | inspection | as L2.6.2 | 3 | |
| L2.6.3 | The seat (the wall between the base face and the pocket) is thick enough to carry the nut and thin enough for the stud to engage it. | inspection | seat thickness in [2.0, 3.65] | 3 | |
| L3.6.3.1 | Seat thickness (base face to the nut's seat face). | inspection | 2.0 to 3.65 | 3 | |
| L2.6.4 | The stud passes through the nut to its tip with nothing in the way. | test | clear_of(BODY, V-STUD, 0.0) | 3 | G5 |
| L3.6.4.1 | Stud envelope free of printed material. | test | d >= 0.0 | 3 | G5 |
| L2.6.5 | The nut cannot turn, and the material around the pocket is at least 1.6 thick. | analysis | at least four of the six flats bounded by printed faces at 0.1 to 0.3 gap; material around the pocket and the hole, outside the insertion slot, >= 1.6 | 2 | |
| L3.6.5.1 | Bounded flats and gap. | analysis | >= 4 flats; gaps in [0.1, 0.3] | 2 | |
| L3.6.5.2 | Material around the nut pocket. | analysis | >= 1.6 | 2 | |

### L1.7 The tripod stud is square to the lens and centred

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The stud axis is perpendicular to the lens axis. | inspection | angle between them 90 +-2.0 deg | 2 | |
| L3.7.1.1 | Perpendicularity. | inspection | as L2.7.1 | 2 | |
| L2.7.2 | The stud axis is centred across the board. | inspection | stud axis X within 1.0 of the lens axis X (12.5) | 2 | |
| L3.7.2.1 | Stud axis X offset. | inspection | <= 1.0 | 2 | |
| L2.7.3 | The base face is flat and wide enough for a tripod plate. | inspection | a planar disc Ø20.0 around the stud axis, flatness <= 0.2, no feature but the stud hole | 2 | |
| L3.7.3.1 | Base face planarity and extent. | inspection | disc Ø20.0 planar within 0.2 | 2 | |

### L1.8 The board and the nut install by one straight movement

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The board installs along `INSTALL_DIR` without touching the holder, the lips excepted. | test | clear_of(BODY minus the lip region, V-CAM-SWEEP, 0.10), the final seating contact excluded | 3 | |
| L3.8.1.1 | Board install sweep. | test | d >= 0.10 | 3 | |
| L2.8.2 | The nut installs along one axis into its pocket and seats. | test | clear_of(BODY, V-NUT-SWEEP, 0.0) along at least one of +-X, +-Y, +-Z; V-NUT at the seat has penetration <= 0.01 mm3 | 2 | |
| L3.8.2.1 | Nut install sweep. | test | d >= 0.0 | 2 | |

### L1.9 It prints as one body without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | In its stated print orientation, no unsupported overhang steeper than 45 degrees from vertical, except round holes up to Ø12.0 in vertical walls, bridges up to 15.0 and ledges (a downward face whose depth from the wall that carries it is <= 1.5: the retaining lips, A9). | analysis | 0 offending faces (area > 1 mm2) | 2 | |
| L3.9.1.1 | Overhang and bridge scan, including the hex pocket, the stud hole, the lips and the ribbon slot. | analysis | as L2.9.1 | 2 | |
| L2.9.2 | The mesh is manifold and one shell. | analysis | 1 shell; manifold3d accepts it | 3 | G1 |
| L3.9.2.1 | Shell count and manifold status. | analysis | shells = 1; manifold true | 3 | G1 |
| L2.9.3 | It rests on a flat face. | analysis | bed contact >= 50 % of the plan bounding box | 1 | |
| L3.9.3.1 | Bed-contact area. | analysis | >= 50 % | 1 | |
| L2.9.4 | No feature thinner than 0.8; lips and the material around the nut pocket at least 1.2 / 1.6. | analysis | min wall >= 0.8 elsewhere | 1 | |
| L3.9.4.1 | Thin-feature scan. | analysis | as L2.9.4 | 1 | |
| L2.9.5 | It fits a 200 x 200 x 200 bed. | inspection | bounding box <= 200 per axis | 1 | |
| L3.9.5.1 | Bounding box. | inspection | <= 200 per axis | 1 | |

### L1.10 It is compact with 2 to 4 mm walls

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Outside size <= 45 x 45 x 30. | inspection | X <= 45.0, Y <= 45.0, Z <= 30.0 in the camera frame | 1 | |
| L3.10.1.1 | Bounding box. | inspection | X <= 45, Y <= 45, Z <= 30 | 1 | |
| L2.10.2 | The pocket walls and the back wall are 2.0 to 4.0 thick. | inspection | each in [2.0, 4.0] | 2 | |
| L3.10.2.1 | Wall and back-wall thickness (median, away from features). | inspection | 2.0 to 4.0 | 2 | |

### L1.11 The package says what was built, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | The package holds the STL (camera frame or any frame; the grader normalises), the `.scad` source, `layout.json` and the agent's own report. | inspection | all present and readable | 3 | G0 |
| L3.11.1.1 | Files present and parse; the body's largest bounding-box axis is within 20 to 200. | inspection | true | 3 | G0 |
| L3.11.1.2 | The declared layout verifies under the seating rule. | analysis | `PCB_BOTTOM` on the supports <= 0.10; camera inside the pocket | 3 | |
| L2.11.2 | The agent's own report agrees with the judge's measurements. | analysis | same pass / fail and abs(d_agent - d_judge) <= 0.10 for every `clear_of`, `travel`, `sweep` L3 reported | 1 | |
| L3.11.2.1 | Self-report versus judge. | analysis | 100 % agreement within 0.10 | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 11 |
| L2 | 32 |
| L3 | 41 |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.11.1.1); **G1**
manifold, one body (L3.9.2.1); **G2** the board fits and is held (L3.2.1.1, L3.3.1.1); **G3** the lens
window and field of view are clear (L3.4.1.1, L3.4.2.1); **G4** the ribbon exits (L3.5.1.1,
L3.5.2.1); **G5** the tripod mount works (L3.6.1.1, L3.6.4.1).

---

## 6. Feasibility

A holder exists that meets every number above. It was built in `manifold3d` and the checks below
were run on it (clearances read from the model, not estimated). Camera frame, mm:

- **Pocket:** X -0.25 to 25.25 (25.5 wide, 0.25 per side), Y -0.25 to 24.25 (24.5, 0.25 per end),
  side walls 2.4 thick, +Y wall 2.4 thick (to Y 26.65), walls up to Z 2.6. Outside X -2.65 to 27.65.
- **Back wall:** Z -4.8 to -2.4 (2.4 thick), 0.4 below the connector (Z -2.0). **Slot:** X 4.0 to 21.0
  (17.0 wide, centred on the connector), Y 1.0 to 5.0 (4.0 long). The V-RIBBON box (X 4.5 to 20.5)
  clears it by 0.5 each side.
- **Supports:** the lower side walls step in to X 1.2 and X 23.8 for Z -2.4 to 0.0: contact
  2 x 1.2 x 24.0 = 57.6 mm2 (>= 40), centroids 23.8 apart, tops coplanar at Z 0.0 (side wall there 2.4 + 1.45 = 3.85 thick, in [2.0, 4.0]). The connector
  (X 2.0 to 23.0) clears them by 0.8, and clears the -Y face by 0.25.
- **Lips:** two, on the side walls, Y 8 to 20, Z 1.3 to 2.6 (1.3 thick), overlap 1.0 on the PCB's front
  face (X 0 to 1.0 and 24.0 to 25.0), gap 0.3 to the PCB top (Z 1.0). Each lip is a ledge 1.25 deep (0.25 edge gap + 1.0 overlap, <= 1.5) and flexes 0.75 on install. Measured travel: X and Y
  0.5 total, +Z 0.3.
- **Lens and field of view:** the walls are no higher than Z 2.6, lens barrel Z 1.0 to 9.0; measured
  distance from the lens barrel to the body 3.4 (the back wall's top face, 3.4 below the barrel's foot; >= 0.5); V-LENS-CLEAR and V-FOV: no contact.
- **Base block:** -Y of the pocket, X -2.65 to 27.65, Y -12.1 to -0.25, Z -4.8 to 17.2 (22 tall; its
  bottom is level with the back wall, so the part prints flat). Flat -Y face 30.3 x 22, Ø20 disc about the
  stud axis (X 12.5, Z 6.2) with 1.0 to the top and bottom edges. **Nut pocket:** hex pocket 11.5 across flats (vertices up and down in
  Z), seat at Y -9.7 (seat thickness 2.4, in [2.0, 3.65]), depth 7.8 to Y -1.9, far wall 1.65
  thick (>= 1.6); an insertion slot 11.5 wide open to the top of the block. Stud hole Ø6.6.
  V-STUD (Ø6.35, Y -12.1 to -2.1) leaves 0.125 around the hole and ends 0.2 short of the pocket's end:
  no contact. The nut (11.1 across flats) passes down the slot to its seat with no penetration.
- **Installation:** the board installs along -Z from the front: swept with the lips excluded, no
  penetration, and a gap of 0.25 to the walls.
- **Size:** X 30.3, Y 38.75, Z 22.0 (limit 45 x 45 x 30). Print with the back face down (Z up):
  the hex pocket's vertices point up and down, the slot and stud hole are round or open to the top,
  the only down-facing faces are the 1.25 deep lip ledges (A9) and the top arc of the Ø6.6 stud hole
  (exempt). The audit rebuilt this holder in manifold3d (section Audit) and read the numbers above from it.

---

## 7. Where this stresses the agent (beyond_library)

1. Subtraction: the pocket, the slot, the hex pocket and stud hole, the lens window.
2. Catalogue datums: the camera's lens axis, holes and connector, the stud and nut.
3. Retention without fasteners from travel limits (supports, lips).
4. A hex pocket sized from across-flats with a per-flat clearance, in a print orientation that
   needs no support.
5. Envelope generation: lens keep-out, field-of-view frustum, ribbon path, nut and board sweeps.

---

## 8. Traceability

| L1 | Owner need | L2 | L3 | Words in the request it comes from |
|---|---|---|---|---|
| L1.1 | Layout | L2.1.1-L2.1.2 | L3.1.1.1, L3.1.2.1 | "holder for a Raspberry Pi camera v2" |
| L1.2 | Board pocket | L2.2.1-L2.2.3 | L3.2.1.1-2, L3.2.2.1-2, L3.2.3.1 | "pocket" (25 x 24 x 9 mm, holes 21 x 12.5 mm) |
| L1.3 | Board held | L2.3.1-L2.3.2 | L3.3.1.1-2, L3.3.2.1-2 | "holder" |
| L1.4 | Lens window | L2.4.1-L2.4.3 | L3.4.1.1, L3.4.2.1, L3.4.3.1 | "lens window clear of any wall at 8 mm diameter" |
| L1.5 | Ribbon slot | L2.5.1-L2.5.3 | L3.5.1.1-2, L3.5.2.1, L3.5.3.1-2 | "ribbon cable exits the back through a 17 mm wide slot" |
| L1.6 | Nut pocket | L2.6.1-L2.6.5 | L3.6.1.1-2, L3.6.2.1, L3.6.3.1, L3.6.4.1, L3.6.5.1-2 | "1/4-20 hex nut pocket" |
| L1.7 | Tripod geometry | L2.7.1-L2.7.3 | L3.7.1.1, L3.7.2.1, L3.7.3.1 | "so I can put it on a tripod" |
| L1.8 | Installation | L2.8.1-L2.8.2 | L3.8.1.1, L3.8.2.1 | implied |
| L1.9 | Printable | L2.9.1-L2.9.5 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1, L3.9.5.1 | implied (OpenSCAD to FDM) |
| L1.10 | Compact, walls | L2.10.1-L2.10.2 | L3.10.1.1, L3.10.2.1 | implied |
| L1.11 | Evidence | L2.11.1-L2.11.2 | L3.11.1.1-2, L3.11.2.1 | needed by the judge |

---

## 9. Grading rules (self-contained fallback for `generalize/rubric.md`)

Use `/Users/robinonsay/python/llm-bt/venv/bin/python` with `manifold3d` and `trimesh`; count shells with
`Manifold.decompose()`.

1. **Package (G0), units.** Load the STL; its largest axis must be 20 to 200 mm.
2. **Normalise** into the camera frame (rotations by multiples of 90 degrees about the lens axis, and
   mirroring only; the layout is transformed with the body).
3. **Build references** from the catalogue and `layout.json`; run R1-R4; verify the seating rule.
4. **Measure every L3** in order: measured value, limit, signed margin (negative = fail), PASS / FAIL /
   UNVERIFIED. UNVERIFIED counts as FAIL.
5. **Recipes.** `clear_of`: volume of the intersection; above 0.01 report it, else d = min gap. `travel`: bisect
   along each axis until the intersection exceeds 0.01 mm3 (0.02 resolution). `sweep`: union of
   translated copies in 0.5 steps, intersect and gap against the body minus the allowed region. Slot
   width: slice the back wall's mid-plane, largest inscribed rectangle across X. Hex pocket: slice
   at mid-depth, distance between opposite flat faces. Thickness: ray casting on a 2 mm grid, median,
   3 mm clear of edges. Holes: largest inscribed circle of a mid-depth slice. Overhang: faces with
   n_z < -cos 45 degrees not on the bed, minus holes up to Ø12, bridges up to 15 and ledges no deeper than 1.5 from their carrying wall.
6. **Class.** WRONG: any gate fails. MINOR: no gate fails but a weight-3 L3 fails. CORRECT: no gate
   fails and all weight-3 L3s pass. **MEETS** = CORRECT and every applicable non-physical weight-1 and
   weight-2 L3 passes. Also report the weighted score and the worst normalised margin among weight-3 L3s.
7. **Precedence.** The numbers in this document beat `part.json`; if they disagree, build the references from
   this document and record a defect against the requirement that the stale catalogue number breaks (where =
   the `part.json` field). Designed contact (1.3) is never interference. The slot width, the ribbon clearance
   and the stud clearance outrank every size-limit L3.
8. **Where.** One entry per failed or UNVERIFIED L3: `req`, `status`, `body`, `feature`, `face` (with outward
   normal), `location` (camera-frame bounding box in mm), `measured` / `limit` / `margin`, `reference` (model or
   envelope and datum), `needed` (a numeric target the next agent can verify, never a design instruction),
   `evidence` (saved defect STL). Separate observations (render-only) from defects.

---

## Audit

Adversarial audit (2026-10-24). Checked: part ids exist and pass `parts.gate`; L1 count 11; counts in
section 5 (11 / 32 / 41) match the tables; every L2 has an L3. The Feasibility holder was rebuilt in
`manifold3d` from the numbers below (with the fixes) and measured: one shell and manifold; barrel gap 3.4
(the back wall's top face is the nearest surface, not a side wall); FOV, lens keep-out, ribbon (0.5 from the
slot edges), stud (0.125 radial, 0.2 at the tip) and nut seat and +Z nut sweep all free; travel X 0.5, Y 0.5,
+Z 0.3; board install sweep along -Z with the lip slab removed has no penetration. `benchmarks/generalize/rubric.md`
does not exist, so section 9 is the procedure. Fixes, all in place:

1. **Printability contradiction.** The lips were claimed to have a 45 degree underside, but a lip with gap
   <= 0.4 and overlap >= 0.6 cannot (the underside plane would cut the board: tip underside >= 1.0 + overlap).
   The rebuilt model has 30 mm2 of flat down-facing lip underside, which L2.9.1 counted as an overhang, so the
   design failed its own L3.9.1.1. Added the convention of a short ledge (down-facing, at most 1.5 deep from
   its carrying wall) to A9, L2.9.1 and the grading recipe; narrowed the lip overlap band to 0.6 to 1.15 (L2.3.2,
   A8) so that edge gap 0.35 + overlap 1.15 = 1.5 stays a ledge and the install flex (overlap - gap) stays
   at most 1.0, the flex A8 allows. Feasibility lips are ledges 1.25 deep.
2. **Support walls too thick.** The 1.6 wide supports made the lower side wall 2.4 + 1.85 = 4.25 thick,
   over the 4.0 limit (L2.10.2). Supports now 1.2 wide (wall 3.85), contact 57.6 mm2 >= 40, centroids 23.8
   apart, connector clearance 0.8.
3. **Zero margin on the base face.** The Ø20 disc (L2.7.3) exactly filled the 20.0 tall face. Block now 22
   tall (Z -4.8 to 17.2), stud axis Z 6.2, 1.0 spare top and bottom; size 30.3 x 38.75 x 22.0; A10 updated.
4. **A7 reasoning.** "Engagement at least 6.35" cannot happen in a 5.6 nut. Reworded to what the seat band
   really guarantees: the stud passes through the nut and shows >= 0.75 beyond it (10.0 - 5.6 - 0.75 = 3.65).
5. **Hidden numbers.** The judge used a field of view with 31.1 degrees on both axes (A4), a slot length limit
   of 10, a nut pocket band (0.1 to 0.3 per flat), a stud hole band, a seat band, and a lip overlap band, none
   of which the agent was told. All now in the request and the L1 texts of `design.json`.
6. **Catalogue conflict recorded, not edited.** `rpi_camera_v2` `ffc_cable` (21.0 wide, 8.0 deep box) disagrees
   with the 16.0 ribbon and V-RIBBON; the document already outranks it, and the same part file feeds G49, so
   the part was left alone.

Known limit: the grader does not test that the walls can really spring 0.75 mm; the install sweep excludes
the lip slab by design (A8).
