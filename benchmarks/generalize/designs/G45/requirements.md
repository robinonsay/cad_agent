# G45 Nozzle and wrench organiser with magnets: requirements (L1 / L2 / L3)

Generalisation design G45 (train split). It is the error signal for the control loop on a fixture
family: one printed tray with a pattern of pockets sized from request-given objects (six hex nozzles,
a wrench) and four disc magnets pocketed from the underside, graded by clearance, depth, ligament,
pattern and tolerance-stack checks. The machine-readable request (L1 only, `dev.json` format) is
`design.json` next to this file. It is graded the way `benchmarks/enclosure/requirements.md` grades
E1-01: Python measures the delivered STL against reference models built from the request sizes and
the catalogue (`benchmarks/generalize/parts/generic_box`, `magnet_disc_6x3`; and
`benchmarks/enclosure/parts/generic_cylinder` for the nozzle's circumscribed envelope).

**Request (owner's words):** "A tray for six M6 hotend nozzles (hex 7 mm AF, 12 mm tall, pocket
clearance 0.3 mm), a 7 mm combination wrench pocket 120 x 14 x 4 mm, and four 6 x 3 mm magnet
pockets underneath that keep the tray on a steel surface. Magnets sit 0.5 mm below the base
surface." The expanded request in `design.json` adds only what section 3 derives.

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

- **Tray frame:** the tray in its print orientation. **Z is up; the underside (the face on the bed
  and on the steel surface) is Z = 0.** X is the tray's long axis, Y the short axis. A design
  delivered rotated about Z by multiples of 90 degrees or mirrored is normalised into this frame
  before grading; that is never penalised.
- **Pocket axes:** nozzle and wrench pockets open upward (+Z); magnet pockets open downward (the
  underside, -Z).

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, distance, clearance, depth | 0.02 mm | a value passes if it meets the limit to within e |
| angle | 0.5 deg | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole diameter | largest inscribed circle of the pocket's section | what a magnet sees |
| hex pocket | across flats = distance between opposite flat faces | |

### 1.3 The checks

- **`clear_of(bodies, volume, clearance)`**: minimum distance between the printed body and `volume`
  is >= `clearance` (negative = penetration; volume reported). Pass: d >= clearance - e.
- **`ligament(void_a, void_b)`**: the minimum 3D distance between two voids (pockets), or between a
  void and the tray's outside; both measured on the printed body.
- **`sweep(part, direction)`**: translate the part along `direction` for 40 mm (a lift) or from 40 mm
  outside (an install) in 0.5 mm steps; pass if the body, excluding the seat contact, has
  intersection <= 0.01 mm3 with the swept volume.
- **`lattice_fit(points)`**: fit a lattice of equal pitch (a line, or a grid with equal pitches
  along X and Y) to the pocket centres by least squares; the value is the largest residual.

**Designed contact is not interference (owner rule, 2026-10-24).** For G45 the designed contacts are:
- each nozzle's underside resting on its pocket floor;
- the wrench's underside resting on its pocket floor;
- each magnet's top face against its pocket ceiling.

For these pairs only penetration counts (intersection above 0.01 mm3); a distance of zero is a pass.
The side clearances (0.3 per side) are never contact.

---

## 2. Reference models, envelopes and datums

### 2.1 Reference models (M-)

| Name | What | Source | Size and datums (tray frame, mm) |
|---|---|---|---|
| **M-NOZ-k** (k = 1..6) | M6 hex nozzle | request sizes (hex 7.0 across flats, 12.0 tall); circumscribed envelope from `generic_cylinder`: diameter 7.0 / cos 30 = 8.083, height 12.0 | hex prism; underside on the pocket floor; `AXIS`, `BOTTOM`, `TOP` datums |
| **M-WRENCH** | 7 mm combination wrench | `generic_box` with size 120.0 x 14.0 x 4.0 (request) | underside on the pocket floor; `BOTTOM`, `TOP`, `CENTRE` |
| **M-MAG-j** (j = 1..4) | N35 disc magnet 6 x 3 | `magnet_disc_6x3` | Ø6.0 x 3.0 (+-0.1); `AXIS`, `BOTTOM`, `TOP`; its top face against the pocket ceiling |

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-NOZ-LIFT-k** | nozzle lift path | M-NOZ-k swept straight +Z for 40 mm from its seated pose |
| **V-WRENCH-LIFT** | wrench lift path | M-WRENCH swept straight +Z for 40 mm |
| **V-MAG-INSTALL-j** | magnet install path | M-MAG-j swept from 40 mm below the underside (-Z) up to its seated pose |
| **V-POCKET-NOZ-k, V-POCKET-WR, V-POCKET-MAG-j** | the pockets as actually printed | the connected empty regions open to the top (nozzles, wrench) or the bottom (magnets), inside the tray's bounding box |
| **V-TRAY-LOADED** | loaded tray for the centre of mass | tray body (density 1.24 g/cm3) plus six nozzles (3.0 g each), the wrench (45.0 g, at its pose) and four magnets (0.64 g each) |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Check | Pass |
|---|---|---|
| R1 | units: bounding boxes in mm | M-WRENCH 120.0 x 14.0 x 4.0 +-0.05; M-MAG Ø6.0 x 3.0 +-0.1; hex nozzle 7.0 across flats +-0.05, 12.0 tall |
| R2 | the pockets in `layout.json` match the pockets measured on the STL | each pocket centre within 0.3 |
| R3 | reference parts do not collide with each other | intersection <= 0.01 mm3 |

**Seating rule.** The grader places each reference part at the pose in `layout.json`, then verifies:
each nozzle and the wrench rest on a pocket floor (distance <= 0.10), each magnet's top is against
its pocket ceiling (<= 0.10). A declaration that is missing or fails is replaced by this fit
(nozzle and wrench on the nearest floor, magnets against the nearest ceiling); a pocket with no
floor fails L3.2.2.1 / L3.4.2.1.

---

## 3. Assumptions, uncertainty and fixed decisions

| # | Question | Value chosen | Uncertainty and why |
|---|---|---|---|
| A1 | Nozzle shape | hex prism 7.0 across flats x 12.0 tall (the thread and tip are inside the 12.0). The circumscribed round envelope is Ø8.083 | across flats +-0.05 (standard 7 mm key); the 12 mm height includes the tip |
| A2 | "Pocket clearance 0.3 mm" | 0.3 mm **per side**, measured between the nozzle's flats (or its corners for a round pocket) and the pocket wall. Pocket across flats for a hex pocket 7.6. The band is 0.30 to 0.45 at the nearest point, and a pocket may not be looser than 0.90 at the flats' midpoints | the owner wrote 0.3 once. A total (0.15 per side) is the alternative; a total 0.3 would make the pocket 7.3. Per side keeps the nozzle free for printing shrinkage; +-0.05 |
| A3 | Wrench | 120 x 14 x 4 are the wrench's own dimensions (`generic_box`); the pocket gets the same 0.3 per side, in plan (pocket 120.6 x 14.6); band 0.30 to 0.45 per side | the owner wrote "wrench pocket 120 x 14 x 4"; reading the numbers as the pocket would give a wrench 0.3 smaller and the pocket exactly the wrench size, which does not print. +-0.3 |
| A4 | "Magnets sit 0.5 mm below the base surface" | recessed: the magnet's steel-facing face is 0.5 mm inside the underside plane (pocket depth 3.5 = 3.0 + 0.5; band 3.4 to 3.6). The tray itself touches the steel | the other reading, the magnet proud by 0.5, would make the tray rock on four points. +-0.1. A 0.5 air gap also lowers the pull; not graded |
| A5 | Magnet pocket | Ø6.15 (6.0 + 0.15 diametral, `magnet_disc_6x3`); band 6.1 to 6.3; open on the underside (blind from the bed side); the magnet is glued or snug | magnet +-0.1; pocket clearance +-0.05 |
| A6 | Pattern | six nozzle pockets on one line or a grid with equal pitch; "regular" = lattice residual <= 0.10; ligament between neighbours at least 1.6 for material and at least 3.0 for finger room (L2.3.2) | the owner did not give a layout; the pattern lets the nozzles be picked out one at a time |
| A7 | Depths | nozzle pocket depth 6.0 to 10.0 (the nozzle sticks out 2.0 to 6.0 for fingers); wrench pocket depth 2.5 to 4.0 (the wrench sticks out 0 to 1.5); floor under nozzle and wrench pockets at least 1.2 | the nozzle must stand without tipping (at least half its height in); fingers need 2.0 above the tray |
| A8 | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed; print flat, underside on the bed; round holes up to Ø12 and bridges up to 15 print without support; a hex pocket prints without support when its axis is vertical | common printers; the magnet pockets open to the bed so the ceiling bridges Ø6.15 |
| A9 | Size limit | 140 x 40 x 15 | the wrench (120.6) plus two walls is about 125; about 125.4 x 31.2 x 10.0 is the tight design (section 6) |
| A10 | Loaded masses | tray density 1.24 g/cm3 (PLA); nozzle 3.0 g (brass); wrench 45 g (7 mm combination, steel); magnet 0.64 g. These four numbers are given to the agent in the request (the judge and the agent must use the same masses) | +-30 % on the masses; the margin in L3.6.2.1 is 2.0 so a 30 % error does not flip it on the feasibility tray (it keeps 5.0) |
| A11 | Walls | at least 2.0 from any pocket to the outside, 1.6 between pockets, 1.2 floor and ceiling | 5, 4 and 3 perimeters |
| A12 | Steel surface | flat steel; the tray's flat underside lies on it; the pull is not graded | the owner gave no force |

### Fixed decisions

| # | Decision |
|---|---|
| FD1 | Tray frame as in 1.1: underside Z = 0, X the long axis. |
| FD2 | Magnets are recessed (A4): pocket depth 3.4 to 3.6, the underside is flat and nothing stands below Z = 0. |
| FD3 | One printed body; nothing else (no lid, no clips). |
| FD4 | Nozzles stand upright (axis along +Z) in vertical-axis pockets; the wrench lies flat. |
| FD5 | The four magnet pockets are Ø6.1 to 6.3 and open on the underside; no through hole to the top. |

---

## 4. Requirements tree

### L1.1 The objects are placed and the layout is declared

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: for each of six nozzles, the wrench and four magnets, the pocket pose; plus the print orientation. | inspection | `layout.json` present, parses, six nozzle poses, one wrench, four magnets, catalogue ids exist | 3 | |
| L3.1.1.1 | Layout file parses and counts match. | inspection | true | 3 | |
| L2.1.2 | The tray has the right number of pockets. | inspection | six nozzle pockets, one wrench pocket, four magnet pockets, counted on the STL | 3 | G5 |
| L3.1.2.1 | Pocket counts. | inspection | 6 / 1 / 4 | 3 | G5 |
| L2.1.3 | The reference parts do not collide with each other. | analysis | pairwise intersection <= 0.01 mm3 | 2 | |
| L3.1.3.1 | Pairwise interference of the reference parts. | analysis | each pair <= 0.01 mm3 | 2 | |

### L1.2 Each nozzle pocket holds its nozzle

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Every nozzle clears its pocket by at least 0.3 on every side, the floor contact excepted. | analysis | clear_of(BODY, M-NOZ-k, 0.30) for k = 1..6 | 3 | G2 |
| L3.2.1.1 | Clearance of each nozzle to the pocket wall (six values). | analysis | d >= 0.30 | 3 | G2 |
| L3.2.1.2 | The pocket is not loose: nearest distance 0.30 to 0.45 and distance at the flats' midpoints <= 0.90 (six pockets). | analysis | as stated | 2 | |
| L2.2.2 | Depth, floor, and finger room. | inspection | pocket depth in [6.0, 10.0]; the nozzle sticks out of the tray's top by >= 2.0; floor under the pocket >= 1.2 | 2 | |
| L3.2.2.1 | Pocket depth (six). | inspection | 6.0 to 10.0 | 2 | |
| L3.2.2.2 | Nozzle protrusion above the tray top (six). | inspection | >= 2.0 | 2 | |
| L3.2.2.3 | Floor thickness under each nozzle pocket (3D, to the underside and to any magnet pocket). | analysis | >= 1.2 | 2 | |
| L2.2.3 | Each nozzle lifts straight out. | test | clear_of(BODY, V-NOZ-LIFT-k, 0.0), the seat excluded | 2 | |
| L3.2.3.1 | Nozzle lift path (six). | test | d >= 0.0 | 2 | |

### L1.3 The nozzle pockets form a regular pattern

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The six pocket centres lie on a regular lattice (one row, or a grid with equal pitch). | analysis | `lattice_fit` residual <= 0.10; pitch >= the pocket's widest section + 1.6 | 2 | |
| L3.3.1.1 | Lattice residual. | analysis | <= 0.10 | 2 | |
| L3.3.1.2 | Pitch against the pocket size (tolerance stack: adjacent pockets keep 1.6 between them even at the pitch residual). | analysis | ligament between adjacent nozzle pockets >= 1.6 + 0.10 | 2 | |
| L2.3.2 | Finger room: neighbouring nozzle pockets are far enough apart for a nozzle to be picked out with the fingers. | analysis | ligament between every two adjacent nozzle pockets >= 3.0 | 1 | |
| L3.3.2.1 | Finger room between adjacent nozzle pockets. | analysis | >= 3.0 | 1 | |

### L1.4 The wrench pocket holds the 120 x 14 x 4 wrench

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The wrench clears its pocket by at least 0.3 per side, the floor contact excepted. | analysis | clear_of(BODY, M-WRENCH, 0.30) | 3 | G3 |
| L3.4.1.1 | Clearance of the wrench to the pocket wall. | analysis | d >= 0.30 | 3 | G3 |
| L3.4.1.2 | The pocket is not loose: per-side gap in plan 0.30 to 0.45 on all four sides (so the pocket is 120.6 to 120.9 x 14.6 to 14.9). | analysis | as stated | 2 | |
| L2.4.2 | Depth and floor: 2.5 to 4.0 deep; the wrench sticks out 0 to 1.5; floor >= 1.2. | inspection | as stated | 2 | |
| L3.4.2.1 | Wrench pocket depth. | inspection | 2.5 to 4.0 | 2 | |
| L3.4.2.2 | Floor thickness under the wrench pocket (3D). | analysis | >= 1.2 | 2 | |
| L2.4.3 | The wrench lifts straight out. | test | clear_of(BODY, V-WRENCH-LIFT, 0.0), the seat excluded | 2 | |
| L3.4.3.1 | Wrench lift path. | test | d >= 0.0 | 2 | |

### L1.5 Four magnet pockets under the tray, recessed 0.5

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Each magnet pocket is Ø6.1 to 6.3 and open on the underside. | inspection | Ø in [6.10, 6.30]; the opening lies in the plane Z = 0 | 3 | G4 |
| L3.5.1.1 | Magnet pocket diameter (four). | inspection | 6.10 to 6.30 | 3 | G4 |
| L2.5.2 | Each magnet sits 0.5 inside the underside: pocket depth 3.4 to 3.6 from the underside to the ceiling, so the magnet's face is 0.5 +-0.1 above Z = 0. | inspection | depth in [3.40, 3.60]; the four depths equal within 0.10 | 3 | G4 |
| L3.5.2.1 | Magnet pocket depth (four). | inspection | 3.40 to 3.60 | 3 | G4 |
| L3.5.2.2 | Depth match across the four. | inspection | max - min <= 0.10 | 2 | |
| L2.5.3 | At least 1.2 of material between each magnet pocket and the top face, the nozzle pockets and the wrench pocket. | analysis | ligament(V-POCKET-MAG-j, any other pocket or the top face) >= 1.2 | 3 | |
| L3.5.3.1 | Material above and beside each magnet pocket (four). | analysis | >= 1.2 | 3 | |
| L2.5.4 | One magnet in each quarter of the tray, spread so the tray is held at its corners. | analysis | one magnet centre in each quadrant of the plan bounding box (split at its mid X and mid Y); X spread >= 50 % of the tray length; Y spread >= 25 % of its width | 2 | |
| L3.5.4.1 | Quadrant occupancy. | analysis | 1 / 1 / 1 / 1 | 2 | |
| L3.5.4.2 | Spread in X and Y. | analysis | >= 50 % and >= 25 % | 2 | |
| L2.5.5 | Each magnet pushes into its pocket from below. | test | clear_of(BODY, V-MAG-INSTALL-j, 0.0), the ceiling contact excluded | 2 | |
| L3.5.5.1 | Magnet install path (four). | test | d >= 0.0 | 2 | |

### L1.6 The tray sits flat on steel and does not tip

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | The underside is flat: nothing below Z = 0, flatness <= 0.2 over the footprint outside the pockets. | inspection | as stated | 2 | |
| L3.6.1.1 | Underside planarity. | inspection | flatness <= 0.2; min Z = 0 | 2 | |
| L2.6.2 | The loaded tray's centre of mass lies inside the polygon of the four magnet centres with at least 2.0 margin. | analysis | distance from the centre of mass (V-TRAY-LOADED) to each edge of the magnet hull >= 2.0 | 2 | |
| L3.6.2.1 | Centre-of-mass margin. | analysis | >= 2.0 | 2 | |
| L2.6.3 | The four magnet faces are coplanar so all four touch (via the recess) at the same distance. | inspection | magnet-face planes, from the pocket depths, within 0.10 | 2 | |
| L3.6.3.1 | Magnet face coplanarity. | inspection | <= 0.10 | 2 | |

### L1.7 Material between and around the pockets

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | At least 1.6 between any two pockets (3D) and at least 2.0 from any pocket to the outside of the tray. | analysis | ligament(any two pockets) >= 1.6; ligament(pocket, outside) >= 2.0 | 2 | |
| L3.7.1.1 | Ligament between pockets (all pairs). | analysis | >= 1.6 | 2 | |
| L3.7.1.2 | Ligament to the outside (all pockets). | analysis | >= 2.0 | 2 | |

### L1.8 It prints flat in one piece without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | In its print orientation (underside on the bed), no unsupported overhang steeper than 45 degrees from vertical, except round holes up to Ø12.0 in vertical walls and bridges up to 15.0. | analysis | 0 offending faces (area > 1 mm2) | 2 | |
| L3.8.1.1 | Overhang and bridge scan: hex pockets, magnet pocket ceilings, any step. | analysis | as L2.8.1 | 2 | |
| L2.8.2 | The mesh is manifold and one shell. | analysis | 1 shell; manifold3d accepts it | 3 | G1 |
| L3.8.2.1 | Shell count and manifold status. | analysis | shells = 1; manifold true | 3 | G1 |
| L2.8.3 | It rests on a flat face. | analysis | bed contact >= 50 % of the plan bounding box (magnet pocket openings excluded from the contact) | 1 | |
| L3.8.3.1 | Bed-contact area. | analysis | >= 50 % | 1 | |
| L2.8.4 | No feature thinner than 0.8. | analysis | min wall >= 0.8 | 1 | |
| L3.8.4.1 | Thin-feature scan. | analysis | >= 0.8 | 1 | |
| L2.8.5 | It fits a 200 x 200 x 200 bed. | inspection | bounding box <= 200 per axis | 1 | |
| L3.8.5.1 | Bounding box. | inspection | <= 200 per axis | 1 | |

### L1.9 It is compact

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | Outside size <= 140 x 40 x 15, longest side along X. | inspection | X <= 140.0, Y <= 40.0, Z <= 15.0; X > Y | 1 | |
| L3.9.1.1 | Bounding box. | inspection | as L2.9.1 | 1 | |

### L1.10 The package says what was built, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | The package holds the STL (tray frame, mm), the `.scad` source, `layout.json` and the agent's own report. | inspection | all present and readable | 3 | G0 |
| L3.10.1.1 | Files present and parse; the body's largest bounding-box axis is within 20 to 200. | inspection | true | 3 | G0 |
| L3.10.1.2 | The declared layout verifies under the seating rule. | analysis | nozzles and wrench on their floors <= 0.10; magnets against their ceilings <= 0.10 | 3 | |
| L2.10.2 | The agent's own report agrees with the judge's measurements. | analysis | same pass / fail and abs(d_agent - d_judge) <= 0.10 for every `clear_of`, `ligament`, `sweep` L3 reported | 1 | |
| L3.10.2.1 | Self-report versus judge. | analysis | 100 % agreement within 0.10 | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 10 |
| L2 | 28 |
| L3 | 38 |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.10.1.1); **G1**
manifold, one shell (L3.8.2.1); **G2** the six nozzles fit their pockets (L3.2.1.1); **G3** the wrench
fits (L3.4.1.1); **G4** the magnets fit and are recessed (L3.5.1.1, L3.5.2.1); **G5** the pocket
counts are right (L3.1.2.1).

---

## 6. Feasibility

A tray exists that meets every number above. It was rebuilt in `manifold3d` by the audit and the checks below
were run on it (gaps, sweeps, centre of mass, overhang read from the model). Tray frame, mm, underside Z = 0:

- **Tray:** a block 125.4 x 31.2 x 10.0 (X x Y x Z). **Wrench pocket:** X 2.4 to 123.0, Y 2.4 to 17.0
  (120.6 x 14.6, 0.3 per side on the wrench's 120 x 14), depth 3.0 (Z 7.0 to 10.0), floor 7.0.
  Measured clearance 0.30 on all sides; the wrench protrudes 1.0. In the band [2.5, 4.0].
- **Nozzle pockets:** six hex pockets, 7.6 across flats (0.3 per flat) at X = 36, 48, 60, 72, 84, 96,
  Y = 24.4 (pitch 12.0, lattice residual 0), depth 8.0 (Z 2.0 to 10.0), floor 2.0. Measured clearance
  0.30 at the flats; the nozzle sticks out 4.0. Ligament between neighbours 4.4 (>= 3.0 finger room), to the wrench pocket
  3.0, to the outside 2.4.
- **Magnet pockets:** Ø6.15, 3.5 deep from the underside, at (14, 24.4), (112, 24.4), (20, 9.7),
  (105, 9.7): one per quadrant (tray mid X 62.7, mid Y 15.6), X spread 98 (78 %), Y spread 14.7
  (47 %). Face recess 3.5 - 3.0 = 0.5. Ceiling above the back magnets 6.5, above the front magnets to the
  wrench pocket floor 3.5 (>= 1.2); the nearest nozzle pocket is 15.1 from the magnet at X 14.
- **Centre of mass:** loaded tray mass 104 g, centre (63.2, 14.7), 5.0 inside the magnet hull's
  nearest edge (>= 2.0).
- **Size:** 125.4 x 31.2 x 10.0, inside 140 x 40 x 15. Print: underside on the bed; the magnet pockets'
  ceilings bridge Ø6.15; the hex pockets are vertical.

---

## 7. Where this stresses the agent (beyond_library)

1. Pattern arrays with a pitch derived from the pocket size and a ligament.
2. Hex pockets sized from across-flats and a per-side clearance (and the wording trap: per side).
3. Blind pockets from the underside with a recess derived from the request.
4. Tolerance stack: the clearances, depths and ligaments add up along the tray.
5. Request-sized generic parts (nozzle envelope, wrench box) and a catalogue magnet.

---

## 8. Traceability

| L1 | Owner need | L2 | L3 | Words in the request it comes from |
|---|---|---|---|---|
| L1.1 | Layout | L2.1.1-L2.1.3 | L3.1.1.1, L3.1.2.1, L3.1.3.1 | "six M6 hotend nozzles", "wrench", "four magnets" |
| L1.2 | Nozzle pockets | L2.2.1-L2.2.3 | L3.2.1.1-2, L3.2.2.1-3, L3.2.3.1 | "hex 7 mm AF, 12 mm tall, pocket clearance 0.3 mm" |
| L1.3 | Regular pattern | L2.3.1-L2.3.2 | L3.3.1.1-2, L3.3.2.1 | "tray for six ... nozzles" |
| L1.4 | Wrench pocket | L2.4.1-L2.4.3 | L3.4.1.1-2, L3.4.2.1-2, L3.4.3.1 | "7 mm combination wrench pocket 120 x 14 x 4 mm" |
| L1.5 | Magnet pockets | L2.5.1-L2.5.5 | L3.5.1.1, L3.5.2.1-2, L3.5.3.1, L3.5.4.1-2, L3.5.5.1 | "four 6 x 3 mm magnet pockets underneath", "0.5 mm below the base surface" |
| L1.6 | On steel, stable | L2.6.1-L2.6.3 | L3.6.1.1, L3.6.2.1, L3.6.3.1 | "keep the tray on a steel surface" |
| L1.7 | Material around pockets | L2.7.1 | L3.7.1.1-2 | implied |
| L1.8 | Printable | L2.8.1-L2.8.5 | L3.8.1.1, L3.8.2.1, L3.8.3.1, L3.8.4.1, L3.8.5.1 | implied (OpenSCAD to FDM) |
| L1.9 | Compact | L2.9.1 | L3.9.1.1 | implied |
| L1.10 | Evidence | L2.10.1-L2.10.2 | L3.10.1.1-2, L3.10.2.1 | needed by the judge |

---

## 9. Grading rules (self-contained fallback for `generalize/rubric.md`)

Use `/Users/robinonsay/python/llm-bt/venv/bin/python` with `manifold3d` and `trimesh`; count shells with
`Manifold.decompose()`.

1. **Package (G0), units.** Load the STL; its largest axis must be 20 to 200 mm.
2. **Normalise** into the tray frame (rotations about Z by multiples of 90 degrees, mirroring only; the underside is
   the face with the magnet pocket openings).
3. **Build references** from the request sizes, the catalogue and `layout.json`; run R1-R3; verify the seating rule.
4. **Measure every L3** in order: measured value, limit, signed margin (negative = fail), PASS / FAIL /
   UNVERIFIED. UNVERIFIED counts as FAIL.
5. **Recipes.** `clear_of`: volume of the intersection; above 0.01 report it, else d = min gap (a part seated on its floor
   is measured with the part raised 0.5 so the floor contact does not read as 0). Pockets: find the connected
   empty regions open at the top or the bottom (`hull` minus body, `decompose()`); diameter = largest inscribed
   circle of a mid-depth slice; depth by ray casting down or up the pocket axis; across flats = distance between
   opposite flat faces of a hex slice. `ligament`: `min_gap` between two pocket volumes, or between one pocket and
   the complement of the tray's bounding box. `lattice_fit`: least squares over pitch and origin. Centre of mass:
   volume centroid of the STL times density plus the point masses. Overhang: faces with n_z < -cos 45 degrees not on
   the bed, minus holes up to Ø12 and bridges up to 15.
6. **Class.** WRONG: any gate fails. MINOR: no gate fails but a weight-3 L3 fails. CORRECT: no gate
   fails and all weight-3 L3s pass. **MEETS** = CORRECT and every applicable non-physical weight-1 and
   weight-2 L3 passes. Also report the weighted score and the worst normalised margin among weight-3 L3s.
7. **Precedence.** The numbers in this document beat `part.json`; if they disagree, build the references from
   this document and record a defect against the requirement that the stale catalogue number breaks (where =
   the `part.json` field). Designed contact (1.3) is never interference. The clearance L3s outrank the
   looseness L3s.
8. **Where.** One entry per failed or UNVERIFIED L3: `req`, `status`, `body`, `feature` (name the pocket k), `face`
   (with outward normal), `location` (tray-frame bounding box in mm), `measured` / `limit` / `margin`, `reference`
   (model or envelope), `needed` (a numeric target the next agent can verify, never a design instruction),
   `evidence` (saved defect STL). Separate observations (render-only) from defects.

---

## Audit

Adversarial audit (2026-10-24). Checked: `generic_box`, `magnet_disc_6x3` (generalize) and `generic_cylinder`
(enclosure) exist and pass `parts.gate`; L1 count 10 (in 8 to 14); counts in section 5 (10 / 28 / 38) match the
tables; every L2 has an L3. `benchmarks/generalize/rubric.md` does not exist, so section 9 is the procedure.
The Feasibility tray was rebuilt in `manifold3d` from section 6 and measured: one shell and manifold, nozzle
and wrench clearance 0.300 on all sides (the recipe's 0.5 raise), lift sweeps and magnet install sweeps with no
penetration, loaded mass 104.0 g and centre of mass (63.18, 14.72) (as stated), the only down-facing faces
are the four 6.15 magnet ceilings (bridges, allowed), bed contact 97 percent. Fixes, all in place:

1. **L2.3.2 / L3.3.2.1 were vacuous.** "The pocket row lies within 5.0 of the mid-line, or the pockets are at
   least 2.0 from a long edge": the feasibility row is 8.8 off the mid-line and the second clause is already
   forced by L3.7.1.2, so the check could never fail. Replaced with a measurable finger-room check: ligament
   between adjacent nozzle pockets >= 3.0 (feasibility 4.4); A6 and the Feasibility text updated.
2. **Hidden numbers.** The judge used values the agent was never told, now in the request and L1 texts of
   `design.json`: the loaded masses behind L3.6.2.1 (tray 1.24 g/cm3, nozzle 3 g, wrench 45 g, magnet 0.64 g;
   A10 now says they are given), the centre-of-mass requirement itself (it was only in L1.6, not in the
   request), the magnet X / Y spread (50 and 25 percent, L2.5.4), nozzle pocket depth 6 to 10 (L2.2.2), the
   lattice residual 0.1 (L2.3.1) and the finger-room 3.0.
3. **Wording left as decisions, not changed:** "0.3 mm clearance" is per side (A2), the wrench's 120 x 14 x 4
   are the wrench's own size (A3), and "0.5 mm below the base surface" is a 0.5 recess inside the underside
   (A4, FD2). The request already states the recess reading.

Checked and left unchanged: hex pocket 7.6 across flats gives 0.30 flat and corner clearance, ligaments
(4.4 between nozzles, 3.0 to the wrench pocket, 2.4 outside, 3.5 under the wrench pocket to the magnets),
quadrants and spread (78 and 47 percent), tray 125.4 x 31.2 x 10.0.
