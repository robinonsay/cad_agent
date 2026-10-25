# G08 Pico battery node with sliding battery door: requirements (L1 / L2 / L3)

A generalization design (train split) in the style of E1-01 (`benchmarks/enclosure/requirements.md`).
The machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file.
`benchmarks/generalize/rubric.md` did not exist when this file was written, so section 9 holds the
design-specific grading rules; measuring recipes are those of `benchmarks/enclosure/rubric.md` section 3
(load, `clear_of`, `inside`, apertures, slices, ray casting, overhang scan, stability).

**Owner's request (verbatim):** "Weatherproof-ish sensor node with a Pico 2 and one 18650 cell
(18.6 x 65.2 mm). The battery sits in a printed cradle with a sliding door on the bottom that retains
it, the SK12D slide switch pokes through the side, and the micro-USB opens at one end. Door clearance
should be about 0.3 mm per side."

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete Python check on the delivered STLs. Every row has a method
(inspection, analysis, demonstration, test, human), a pass/fail criterion with a number and a
tolerance, a weight (3 = critical, 2 = major, 1 = minor) and a gate mark (G0 to G5) where a failure
makes the design WRONG. Numbers that come from an assumption (section 3) are provisional until the
owner confirms them. Do not relax a criterion because the agent fails it.

---

## 1. Frame, tolerances and designed contact

- **Enclosure frame:** X along the cell axis, Y across with the cell axis at Y = 0, Z up. The Pico's USB
  end is **−X**; the door leaves toward **+X** (FD1); the switch handle faces **+Y** (FD2). Z = 0 is the lowest
  plane of the closed enclosure (the bottom rim of the base). A delivery mirrored or rotated is normalised
  into this frame by rotations by multiples of 90 degrees and mirroring only (rubric: the end wall with the
  USB opening at −X, the door's exit at +X); that is never penalised. Units mm.
- **Measurement tolerances ε:** length, distance and clearance 0.02; diameter 0.03 (largest inscribed circle
  for holes, smallest enclosing circle for bosses); angle 0.5 degrees; volume 0.01 mm³. A value passes if it
  meets its limit to within ε.
- **Designed contact (this design).** These pairs are never interference (only penetration above 0.01 mm³
  counts; a distance of zero is a pass):
  1. the cell resting on the door and touching the cradle surfaces;
  2. the Pico's underside on the four post tops, and an M2 screw in its pilot hole;
  3. the switch body on the shelf, the side wall and the retaining ribs;
  4. the door against its end stop and its detent (the detent may overlap the base by the stated amount, L3.4.4.2);
  5. the lid lip on its locating faces, and the lid on the rim;
  6. an M3 screw in its boss pilot.
  Not designed contact (must stay free): the cell's 3.0 mm contact reserves, the Pico keep-out zones, the switch
  terminal zone, the USB plug and the handle sweep.
- **Checks used** (`enclosure/requirements.md` 1.3, recipes in `enclosure/rubric.md` 3.2 to 3.4):
  `clear_of(bodies, volume, clearance)` (pass: penetration ≤ 0.01 mm³ and d ≥ clearance − ε), `inside(volume,
  cavity, clearance)`, aperture enumeration and the 2.0 mm probe. `ALL` = base ∪ lid ∪ door in the closed pose;
  `BASE`, `LID`, `DOOR` as named. `inside` is measured to the walls, shelf underside and rim faces; posts, ribs and bosses are supports and are
  excluded, so the Pico resting on its posts is not failed for touching them. The grader builds all reference models and volumes itself from the catalogue and
  the declared layout; a design never builds or edits them for grading.

## 2. Reference models and envelopes

Positions are those the design declares in `layout.json` (L3.13.1.2 verifies them); the sketch values of
section 7 are one valid layout. Datums come from the catalogue `part.json` files.

| Name | What | Source | Definition (enclosure frame, mm) | Datums |
|---|---|---|---|---|
| **M-CELL** | the 18650 cell | catalogue `cell_18650` (Ø18.6, length 65.2 with a 1.0 button of Ø7.0 at the positive end; worst case) | axis along X at Y = 0; sketch: X 5.4 to 70.6, axis Z 13.2 | `AXIS`, `NEG_TERMINAL`, `POS_TERMINAL`, `CRADLE` (lowest line), `RETAIN_TOP` |
| **V-CONTACT-N, -P** | contact-hardware reserve at each cell end | catalogue keep-outs `neg_contact`, `pos_contact` | cylinder of the cell diameter (Ø18.6) × 3.0 long on the axis, beyond each end of M-CELL (`contact_clearance`, A2) | cell terminals |
| **M-PICO** | the Pico 2 | catalogue `rpi_pico2` (PCB 51 × 21 × 1, receptacle 8.0 × 5.5 × 2.8 overhanging 1.3, holes Ø2.1 at 47.0 × 11.4) | components up, `USB_AXIS` along −X, lying lengthwise above the cell; sketch PCB X 4.05 to 55.05, Y ±10.5, Z 28.8 to 29.8 | `USB_MOUTH`, `USB_AXIS`, `PCB_BOTTOM`, `PCB_TOP`, `HOLE` |
| **V-PICO** | Pico with receptacle | envelope | M-PICO bounding solids including the receptacle outside the board edge | `USB_MOUTH` |
| **V-KO-PICO-TOP** | clear space above the Pico | envelope | PCB outline (without the receptacle overhang) from `PCB_TOP` up 4.0 (A6) | `PCB_TOP` |
| **V-KO-PICO-BOT** | clear space below the Pico | envelope | PCB outline from `PCB_BOTTOM` down 2.0 (A6), minus Ø7.0 columns on the four hole axes | `PCB_BOTTOM`, `HOLE` |
| **M-SW** | slide switch | catalogue `slide_sk12d` (body 12.5 × 6.0 × 5.5, handle 3.0 × 3.0 × 4.0, travel 3.5, pins 3.0) | handle toward +Y (`ACTUATOR_AXIS`), travel along X (`TRAVEL_AXIS`); sketch body X 55.9 to 68.4, Y 5.5 to 11.0, Z 25.8 to 31.8 | `ACTUATOR_AXIS`, `TRAVEL_AXIS`, `HANDLE_CENTER`, `BODY_BOTTOM` |
| **V-SW-SWEEP** | handle swept area | envelope | the handle's 3.0 × 3.0 section translated ±1.75 along `TRAVEL_AXIS` and extended along `ACTUATOR_AXIS` from the body face to 5.0 beyond the wall's outer face | `HANDLE_CENTER`, `TRAVEL_AXIS` |
| **V-SW-TERM** | switch terminal and wire zone | envelope | the body's 12.5 × 6.0 footprint from `BODY_BOTTOM` inward 5.0 (A7: pins 3.0 + wires 2.0) | `BODY_BOTTOM` |
| **M-PLUG-USB** and **V-USB-PLUG** | micro-USB cable plug and its path | catalogue `plug_microusb_b` | shell 6.9 × 1.85 from 5.0 inside `USB_MOUTH` to 1.5 outside it; overmold 10.0 × 7.0, swept out along `USB_AXIS` to 40 beyond the wall | `USB_MOUTH`, `USB_AXIS` |
| **V-CAVITY** | the closed enclosure's internal void | computed | convex hull of ALL minus ALL, the connected component holding the Pico | none |
| **V-AP-USB**, **V-AP-OTHER** | openings in the −X wall; every other through-path into V-CAVITY | computed | as `enclosure/rubric.md` 3.4 | wall faces |
| **V-CELL-DROP** | cell removal path | envelope | M-CELL swept along −Z by 30.0 from its seated pose | `AXIS` |
| **V-DOOR-SWEEP** | the door's travel | computed | the door translated along +X from its closed pose by 0 to 100.0 in 1.0 steps | door |
| **V-INSTALL-PICO** | Pico installation path | envelope | the PCB plan silhouette plus receptacle, swept +Z from the seated pose to 10.0 above the base rim, minus the four post columns (the Pico on the post tops is designed contact) | M-PICO pose |
| **V-INSTALL-SW** | switch installation path | envelope | M-SW moved 4.0 inward from its seat (so the handle tip is at the wall's inner face), swept down −Z from 10.0 above the rim to its seat height, then slid 4.0 toward the wall (+Y) | M-SW pose |
| **V-DRIVER-k** | screwdriver access to a Pico screw | envelope | Ø6.0 column on each hole axis from `PCB_TOP` to 50 above the base rim, lid off | `HOLE` |
| **V-LIDDRIVER-j** | screwdriver access to a lid screw | envelope | Ø6.0 column on each lid-screw axis from the lid top to 50 above it | lid-screw axes |

Sanity checks before grading (not L3s): R1 units (cell Ø18.6 ± 0.2, Pico PCB 51.0 × 21.0 ± 0.2); R2 models do not
collide with each other (L3.1.3.1); R3 the Pico lies above the cell with its USB toward −X; R4 every V- envelope's
datums equal the model datums it was built from.

**Seating rule (Pico).** The grader places M-PICO at the declared pose and verifies it: `PCB_BOTTOM` lies on the post
tops (distance ≤ 0.10) and the hole axes are coaxial with the pilots (least-squares residual ≤ 0.25). If the
declaration fails, M-PICO is seated by that fit; if there are no posts, it is centred in the cavity.

## 3. Assumptions and open questions for the owner

| # | Question | Value chosen | Why / uncertainty |
|---|---|---|---|
| **A1** | How are the parts arranged? | Pico above the cell, both lengthwise (a two-storey box): cell and door below, a shelf, then the Pico, then the lid. | Compact (about 80 × 27 × 38) and lets the door sit on the bottom as the owner says. Alternative: Pico beside the cell (wider, lower). Uncertainty medium. |
| **A2** | Cell contacts | The cell needs 3.0 mm of free space at each end for spring or plate contacts (`cell_18650` `contact_clearance`); contact hardware is bought-in and not modelled; the reserve is the catalogue keep-out cylinder (cell diameter Ø18.6 × 3.0). | Typical holder hardware. Uncertainty medium; the owner's holder may be thicker. |
| **A3** | Cell size | Ø18.6 × 65.2 with a button top (worst case for length), from `cell_18650/part.json` (IEC 61960 limits). | Flat-top cells are shorter. Uncertainty low. |
| **A4** | Door clearance "about 0.3 mm per side" | Lateral clearance in the grooves and vertical clearance above and below the door are each 0.25 to 0.35. | Common FDM sliding fit. Uncertainty low. |
| **A5** | "Weatherproof-ish" | Closed on all sides except the USB opening, the switch slot, the door seam and screw holes; no IP rating, no gasket. | The owner's words do not ask for a number. Uncertainty medium. A seam gap above 0.4 would be an observation. |
| **A6** | Pico mounting and clearances | Four posts under the four holes, M2 self-tapping screws (`screw_m2_selftap`: pilot 1.6 to 1.8, engagement 5.0, post OD ≥ 5.0). 4.0 clear above the PCB top (receptacle 2.8 plus 1.2), 2.0 clear below the PCB (solder and leads). | The request says nothing; derived from `rpi_pico2` and the E1-01 convention. Uncertainty medium. |
| **A7** | Switch | SK12D (`slide_sk12d`): body 12.5 × 6.0 × 5.5, handle 3.0 × 3.0 × 4.0 above the body, travel 3.5, pins 3.0 long; plus 2.0 for wires. Slot clearance 0.25 to 0.5 per side. | Datasheet and `part.json`; the handle height varies 2 to 6 between variants. Uncertainty medium. |
| **A8** | Lid | A plate with a continuous locating lip (fit 0.15 to 0.35 per side, engagement 2.0 to 3.0, plate 2.0 to 3.0, total lid height ≤ 6.0) held by **two** M3 self-tapping screws (`screw_m3_selftap`: pilot 2.4 to 2.6, engagement 6.0, boss OD ≥ 6.0; screw length ≥ plate + free gap + engagement, 12 in the sketch) into bosses at the end away from the USB, where the Pico leaves room. | Same family as E1-01 L2.7.5, with two screws because the Pico fills the other end. Uncertainty medium. |
| A9 | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed, no supports. Overhang rule 45°, bridges up to 15.0, round holes up to Ø12 exempt. Bed contact at least 50% for the lid and door, at least 25% for the base (a frame-like body with open top and bottom). | Common printer. The 25% is a derived concession for the open-ended base (FD5). |
| A10 | Wall thickness | Walls, shelf and lid plate 2.0 to 4.0; door 2.0 to 3.0. | 5 perimeters at 0.4 nozzle. |
| A11 | Plug size | micro-USB overmold 10.0 × 7.0 (`plug_microusb_b`). | Typical cable. Measure the owner's cable. |
| A12 | Size limit | Closed enclosure including the door grip at most 85 × 40 × 40. | Stops oversized designs. A tight design is about 80 × 27 × 38. |
| A13 | Battery protection, wiring | A protection circuit is part of the cell or the owner's wiring; wires are routed through passages (L3.6.4.1) and not modelled. | Not stated. |
| A14 | Pico USB | Used for data and power; only the USB opening is cut. BOOTSEL is reached with the lid off. | Not stated. |

## 4. Fixed decisions (a choice was ambiguous; this is the one graded)

- **FD1 Door exit.** The door slides along +X, away from the USB end, and leaves through a slot in the +X end wall.
- **FD2 Switch side.** The handle points out of the +Y side wall. A mirror image is normalised first.
- **FD3 Retention test.** A part is "captured within d" in a direction if translating its reference model by d along that axis
  direction makes it intersect the printed bodies of the closed assembly by more than 0.01 mm³. A direction in which the part rests
  (contact) counts as captured at 0.
- **FD4 Screws.** Two lid screws; four Pico screws; the cell, the switch and the door have no screws.
- **FD5 Bed contact.** The base's threshold is 25% (A9); the lid's and the door's are 50%.
- **FD6 Frame of the door.** The door's closed pose is the one it is delivered in; sliding is along +X.

## 5. Requirements tree

### L1.1 Layout declared: Pico above the cell, lengthwise, USB at one end; switch on a side

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The layout is declared. | inspection | `layout.json` present, parses, names the Pico, cell, switch and plug from the catalogue and gives each pose; screws named (`screw_m2_selftap`, `screw_m3_selftap`) | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 | |
| L2.1.2 | Orientation of the parts. | inspection | `USB_AXIS` within 1.0° of −X; cell `AXIS` within 1.0° of X; switch `ACTUATOR_AXIS` within 1.0° of +Y and `TRAVEL_AXIS` along X; the Pico's PCB bottom above the cell's top line by at least 2.0 | 3 | |
| L3.1.2.1 | Pico and cell directions. | inspection | as L2.1.2 | 3 | |
| L3.1.2.2 | Switch directions. | inspection | as L2.1.2 | 2 | |
| L3.1.2.3 | Pico above the cell. | inspection | (`PCB_BOTTOM` Z) − (cell top Z) ≥ 2.0 (sketch: 6.3) | 2 | |
| L2.1.3 | The parts do not collide. | analysis | M-CELL, M-PICO, M-SW pairwise intersection ≤ 0.01 mm³ | 3 | |
| L3.1.3.1 | Pairwise interference of the reference models. | analysis | each pair ≤ 0.01 mm³ | 3 | |

### L1.2 The cell lies in a cradle without penetrating anything, with its contact reserves free

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The cell does not penetrate any printed surface. | analysis | clear_of(ALL, M-CELL, 0.0): penetration ≤ 0.01 mm³ (touching the cradle is designed contact) | 3 | G2 |
| L3.2.1.1 | Cell vs enclosure. | analysis | penetration ≤ 0.01 mm³ | 3 | G2 |
| L2.2.2 | The contact reserves stay free. | analysis | clear_of(ALL, V-CONTACT-N ∪ V-CONTACT-P, 0.0) | 2 | |
| L3.2.2.1 | Reserve zones clear. | analysis | penetration ≤ 0.01 mm³ for both | 2 | |
| L3.2.2.2 | Free length along the cell axis between the printed surfaces beyond the two cell ends, at cell height. | analysis | ≥ 71.2 (65.2 + 2 × 3.0) | 2 | |
| L2.2.3 | Side clearance at the widest point. | analysis | gap between the cell surface and the printed surface on each side (±Y), in the plane through the axis: 0.3 to 1.0 | 2 | |
| L3.2.3.1 | Side gaps. | analysis | each of the two in [0.30, 1.00] (sketch: 0.50) | 2 | |

### L1.3 With the door closed the cell is held and rests on the door

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The cell cannot move more than 1.0 mm sideways or up (FD3). | demonstration | translating M-CELL by 1.0 along +Y, −Y and +Z each intersects ALL by > 0.01 mm³ | 3 | G2 |
| L3.3.1.1 | Capture in ±Y and +Z. | demonstration | all three hit | 3 | G2 |
| L2.3.2 | The cell rests on the door. | demonstration | gap between the cell's lowest line and the door's upper face ≤ 0.3, no penetration | 2 | |
| L3.3.2.1 | Cell on the door. | demonstration | 0 ≤ gap ≤ 0.3 | 2 | |
| L2.3.3 | The cell cannot move far along its axis. | demonstration | translating M-CELL by 4.0 along +X and along −X each intersects ALL by > 0.01 mm³ (the 3.0 contact reserve plus 1.0) | 2 | |
| L3.3.3.1 | Capture along X. | demonstration | both hit | 2 | |

### L1.4 The door: separate, 0.30 mm sliding fit, detent, stop, grip

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Door thickness and position. | inspection | plate thickness 2.0 to 3.0; its outer face lies 0.3 to 3.0 above the base's bottom plane (the enclosure stands on the base rim) | 2 | |
| L3.4.1.1 | Door plate thickness. | inspection | 2.0 ≤ t ≤ 3.0 (sketch: 2.4) | 2 | |
| L3.4.1.2 | Door recess above the rim plane. | inspection | 0.3 ≤ r ≤ 3.0 (sketch: 1.5) | 2 | |
| L2.4.2 | The door slides along +X without touching the base. | test | for the door translated 0 to 100.0 along +X in 1.0 steps: at every step intersection with BASE ≤ 10.0 mm³ (the maximum over the steps, not their sum), only in the detent (patches ≤ 0.8 thick); everywhere else distance ≥ 0.25, except the end-stop contact of the closed pose (designed contact, distance 0) | 3 | G5 |
| L3.4.2.1 | Door sweep. | test | per-step intersection ≤ 10.0 mm³ (maximum over the steps) and each patch ≤ 0.8 thick | 3 | G5 |
| L3.4.2.2 | Lateral clearance per side (door at 1.0 mm off its stop). | test | each side 0.25 to 0.35 (sketch: 0.30) | 3 | |
| L3.4.2.3 | Vertical clearance above and below the door in the grooves. | test | each 0.25 to 0.35 (sketch: 0.30) | 2 | |
| L2.4.3 | The door engages the walls. | inspection | the door's width exceeds the cradle's bottom opening so that it overlaps each side wall by ≥ 1.0 over at least 60% of its length | 2 | |
| L3.4.3.1 | Groove engagement. | inspection | overlap per side ≥ 1.0 (sketch: 1.2), length fraction ≥ 60% | 2 | |
| L2.4.4 | Stop, detent and grip. | test | closed pose: translating the door by 1.0 along −X hits BASE (stop). Translating by 2.0 along +X intersects BASE by 0.3 to 10.0 mm³ with penetration depth 0.3 to 0.8 (detent). The door protrudes 1.0 to 5.0 beyond the base's +X outer face | 2 | |
| L3.4.4.1 | End stop. | test | hit > 0.01 mm³ at −1.0 | 2 | |
| L3.4.4.2 | Detent. | test | volume 0.3 to 10.0 mm³, depth 0.3 to 0.8 | 2 | |
| L3.4.4.3 | Grip. | inspection | 1.0 ≤ protrusion ≤ 5.0 (sketch: 1.5) | 1 | |

### L1.5 With the door removed the cell drops straight out

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The cell can leave downward. | test | clear_of(BASE ∪ LID, V-CELL-DROP, 0.0), door removed | 3 | |
| L3.5.1.1 | V-CELL-DROP clear. | test | penetration ≤ 0.01 mm³ | 3 | |
| L2.5.2 | The bottom opening is wide enough. | analysis | the opening between the base's lower edges, at the cell's widest, ≥ 18.6 + 2 × 0.3 = 19.2 | 2 | |
| L3.5.2.1 | Bottom opening width. | analysis | ≥ 19.2 (sketch: 19.6) | 2 | |

### L1.6 The Pico: four posts, keep-outs, wall clearance, wire passages

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Four posts under the Pico's holes, each with an M2 pilot. | inspection | count = 4; axis within 0.25 of each `HOLE` axis; OD 5.0 to 7.0; pilot Ø 1.6 to 1.8, depth ≥ 5.0 from the post top; tops coplanar within 0.10 and `PCB_BOTTOM` on them within 0.10 | 3 | |
| L3.6.1.1 | Post count and axes. | inspection | 4; each ≤ 0.25 | 3 | |
| L3.6.1.2 | Post OD. | inspection | 5.0 ≤ OD ≤ 7.0 (sketch: 5.4) | 2 | |
| L3.6.1.3 | Pilot diameter and depth. | inspection | 1.6 ≤ Ø ≤ 1.8; depth ≥ 5.0 | 3 | |
| L3.6.1.4 | Post tops and seating. | inspection | top spread ≤ 0.10; PCB underside on tops ≤ 0.10 | 2 | |
| L2.6.2 | Space above and below the Pico, and room at the sides. | analysis | clear_of(ALL, V-KO-PICO-TOP, 0.0); clear_of(ALL, V-KO-PICO-BOT, 0.0); inside(V-PICO, V-CAVITY, 0.3) | 3 | |
| L3.6.2.1 | Top keep-out. | analysis | d ≥ 0 | 3 | |
| L3.6.2.2 | Bottom keep-out. | analysis | d ≥ 0 | 3 | |
| L3.6.2.3 | Pico inside the cavity. | analysis | d ≥ 0.30 | 3 | |
| L2.6.3 | The Pico can be installed and screwed down with the lid off. | test | clear_of(BASE, V-INSTALL-PICO, 0.2); clear_of(BASE, V-DRIVER-k, 0.0) for k = 1..4 | 2 | |
| L3.6.3.1 | Install path. | test | d ≥ 0.2 | 2 | |
| L3.6.3.2 | Driver columns. | test | d ≥ 0 | 2 | |
| L2.6.4 | A passage for the cell wires at each cell end. | inspection | an opening through the shelf (between the cell's chamber and the Pico's storey), largest inscribed circle ≥ 4.0, its centre within 1.0 of the X range of the contact reserve, one at each end; not an opening to the outside | 1 | |
| L3.6.4.1 | Wire passages. | inspection | both present, Ø ≥ 4.0 (sketch: 4.0 at X 4.6 and X 72.0) | 1 | |

### L1.7 A micro-USB plug seats through the −X end wall with the lid on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The plug can go in to full mate without touching the enclosure. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 | G3 |
| L3.7.1.1 | USB plug envelope clear. | test | d ≥ 0.30 (sketch: 0.30) | 3 | G3 |
| L2.7.2 | The opening is not oversized. | analysis | inside(V-AP-USB, V-USB-PLUG offset by 1.5, 0.0) | 2 | |
| L3.7.2.1 | Opening within the grown plug envelope. | analysis | d ≥ 0 (with the default plug: opening ≤ 13.0 × 10.0) | 2 | |
| L2.7.3 | Exactly one opening in the −X wall. | inspection | V-AP-USB has 1 connected region | 2 | |
| L3.7.3.1 | Opening count. | inspection | 1 | 2 | |

### L1.8 The slide switch: captive, handle through a slot with its full throw

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The handle moves through its throw without touching the slot. | test | clear_of(ALL, V-SW-SWEEP, 0.25) | 3 | G4 |
| L3.8.1.1 | Handle sweep clear. | test | d ≥ 0.25 (sketch: 0.40) | 3 | G4 |
| L3.8.1.2 | Handle protrusion beyond the wall's outer face at mid-travel. | inspection | 1.0 ≤ p ≤ 3.0 (sketch: 1.5) | 2 | |
| L3.8.1.3 | Slot not oversized. | analysis | the slot's section inside V-SW-SWEEP offset by 1.0 (sketch: 7.3 × 3.8 vs sweep 6.5 × 3.0) | 2 | |
| L2.8.2 | The switch is held and does not penetrate. | demonstration | M-SW ∩ ALL ≤ 0.01 mm³; translating M-SW by 1.0 along +X, −X, +Z, −Z and +Y each hits ALL (the −Y direction is not required: wires pull that way) | 3 | |
| L3.8.2.1 | No penetration of the switch body. | demonstration | ≤ 0.01 mm³ | 3 | |
| L3.8.2.2 | Capture in five directions. | demonstration | all five hit (sketch: +X 16, −X 16, +Z 4.5 (slot), −Z 73, +Y 47 mm³) | 2 | |
| L2.8.3 | The terminals and wires have room. | analysis | clear_of(ALL, V-SW-TERM, 0.0) | 2 | |
| L3.8.3.1 | Terminal zone clear. | analysis | d ≥ 0 | 2 | |
| L2.8.4 | The switch can be installed with the lid off. | test | clear_of(BASE, V-INSTALL-SW, 0.0) | 2 | |
| L3.8.4.1 | Install path. | test | penetration ≤ 0.01 mm³ | 2 | |

### L1.9 Base, lid and screws

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | Base, lid and door are separate bodies that do not interpenetrate. | analysis | BASE ∩ LID ≤ 1.0 mm³; LID ∩ DOOR ≤ 0.01; BASE ∩ DOOR as L2.4.2 | 3 | |
| L3.9.1.1 | Base and lid closed. | analysis | BASE ∩ LID ≤ 1.0 mm³ | 3 | |
| L2.9.2 | A lip locates the lid with a sliding fit; the lid is a plate over the base outline (A8). | inspection | lip clearance 0.15 to 0.35 per side; engagement 2.0 to 3.0; plate 2.0 to 3.0; plate outline = base outline ± 0.5; total lid height ≤ 6.0 | 3 | |
| L3.9.2.1 | Lip-to-wall gap. | inspection | 0.15 ≤ gap ≤ 0.35, all locating faces (sketch: 0.25) | 2 | |
| L3.9.2.2 | Lip engagement. | inspection | 2.0 ≤ h ≤ 3.0 (sketch: 2.0) | 1 | |
| L3.9.2.3 | Plate thickness, outline match and total height. | inspection | 2.0 to 3.0; ± 0.5; ≤ 6.0 (sketch: 2.0, 0.0, 4.0) | 2 | |
| L2.9.3 | Two M3 screws hold the lid (FD4). | inspection | 2 bosses in the cavity: pilot Ø 2.4 to 2.6, depth ≥ 6.0, OD ≥ 6.0; lid holes Ø 3.3 to 3.5 coaxial within 0.3; clear_of(ALL, V-LIDDRIVER-j, 0.0) | 2 | |
| L3.9.3.1 | Bosses. | inspection | count 2; pilot, depth, OD as above | 2 | |
| L3.9.3.2 | Lid holes. | inspection | Ø and coaxial offset as above | 2 | |
| L3.9.3.3 | Lid-screw driver access. | analysis | d ≥ 0 | 1 | |

### L1.10 Closed except the listed openings; thickness 2.0 to 4.0

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | No unlisted opening. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into V-CAVITY, other than the switch slot, the door seam (gaps ≤ 0.4) and the lid screw holes | 2 | |
| L3.10.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths; seam gaps ≤ 0.4 | 2 | |
| L2.10.2 | Wall, shelf and lid thickness. | inspection | each in [2.0, 4.0] (median over a 2 mm grid at least 3 mm from edges and features; the cradle's internal cheeks and ribs are features, not walls) | 2 | |
| L3.10.2.1 | End and side walls. | inspection | 2.0 ≤ t ≤ 4.0 (sketch: 2.4 / 2.5 / 3.7) | 2 | |
| L3.10.2.2 | Shelf and lid plate. | inspection | 2.0 ≤ t ≤ 4.0 (sketch: 3.0 / 2.0) | 2 | |
| L2.10.3 | Material round every opening. | analysis | ligament ≥ 1.0 to wall edges, the shelf and the rim | 1 | |
| L3.10.3.1 | Minimum ligament. | analysis | ≥ 1.0 (sketch: 1.1 at the switch slot, 1.5 at the USB opening) | 1 | |

### L1.11 Three bodies that print without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Each body is one manifold shell. | analysis | shells = 1 and manifold3d NoError, for base, lid and door | 3 | G1 |
| L3.11.1.1 | Shells and manifold status. | analysis | 1 and NoError for all three | 3 | G1 |
| L2.11.2 | No unsupported overhang in the declared orientation. | analysis | faces with n_z < −cos 45° (patch > 1 mm²) = 0, except round holes up to Ø12 and bridges up to 15.0 | 2 | |
| L3.11.2.1 | Overhang and bridge scan per body. | analysis | 0 offending patches | 2 | |
| L2.11.3 | Bed contact (FD5). | analysis | base ≥ 25%, lid ≥ 50%, door ≥ 50% of the plan bounding box | 1 | |
| L3.11.3.1 | Bed contact per body. | analysis | as L2.11.3 (sketch: base 32%) | 1 | |
| L2.11.4 | No thin feature; fits the bed. | analysis | local thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 | |
| L3.11.4.1 | Thin features and build volume. | analysis | as L2.11.4 | 1 | |

### L1.12 Compact and stable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | Closed outside size. | inspection | ALL bounding box ≤ 85.0 × 40.0 × 40.0 (X × Y × Z, door grip included), X longest | 1 | |
| L3.12.1.1 | Assembly bounding box. | inspection | as L2.12.1 (sketch: 80.3 × 27.0 × 38.5) | 1 | |
| L2.12.2 | It stands on its base rim. | analysis | stable at 5° table tilt, support polygon = the base rim's bottom | 1 | |
| L3.12.2.1 | `stable`, tilt 5°. | analysis | passes (the centre of mass of the closed enclosure plus cell 45 g, Pico 3 g and switch 1 g) | 1 | |

### L1.13 The package says what was built and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | The package holds `base.stl`, `lid.stl`, `door.stl` (closed pose, enclosure frame, mm), the `.scad` source, `layout.json` (the poses of cell, Pico, switch, and each body's print orientation) and the agent's own interference report. | inspection | all present and readable; each body's largest axis 20 to 100 | 3 | G0 |
| L3.13.1.1 | Files present and parse; units. | inspection | true | 3 | G0 |
| L3.13.1.2 | The declared layout verifies. | analysis | Pico seating rule (section 2); cell and switch poses within 0.2 of a pose that satisfies L3.2.1.1 and L3.8.2.1 | 3 | |
| L2.13.2 | The agent's report agrees with the grader. | analysis | for every `clear_of` / `inside` L3 the agent reports: same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 | |
| L3.13.2.1 | Self-report vs judge. | analysis | 100% within 0.10 | 1 | |

## 6. Gates and counts

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.13.1.1), **G1** three manifold
bodies (L3.11.1.1), **G2** the cell fits and is held (L3.2.1.1, L3.3.1.1), **G3** the USB plug seats (L3.7.1.1),
**G4** the switch handle moves freely through its slot (L3.8.1.1), **G5** the door slides (L3.4.2.1). Classes: WRONG
(a gate fails), MINOR (no gate fails, a weight-3 L3 fails), CORRECT (all weight-3 pass), MEETS (CORRECT and every
non-physical L3 of weight 1 and 2 passes).

| Level | Count |
|---|---|
| L1 | 13 |
| L2 | 40 |
| L3 | 63 |

## 7. Feasibility (a design exists)

A concrete layout, modelled and checked with `manifold3d` (base one shell, NoError, volume 30 146 mm³; door one
shell). Numbers in mm, enclosure frame:

| Feature | Value |
|---|---|
| outside | X 0 to 78.8, Y ±13.5, Z 0 to 36.5 (base rim) plus lid plate to 38.5; door grip to X 80.3; closed box 80.3 × 27.0 × 38.5 |
| walls | −X and +X end walls 2.4; lower side walls 3.7 (Y 9.8 to 13.5); upper side walls 2.5 (Y 11.0 to 13.5); shelf 3.0 (Z 22.8 to 25.8); lid plate 2.0 (Z 36.5 to 38.5); lid lip Z 34.5 to 36.5, 1.2 thick, 0.25 inside the cavity |
| cell and cradle | axis Y 0, Z 13.2, X 5.4 to 70.6; channel Y ±9.8 up to Z 16.55, then 45° to a flat roof at Z 22.8 (7.1 wide); contact reserves X 2.4 to 5.4 and 70.6 to 73.6; cross-block X 73.6 to 76.4; side gap 0.5 each; cell top 22.5 (0.3 under the roof) |
| door | X 2.4 to 80.3, Y ±11.0, Z 1.5 to 3.9 (2.4 thick, 1.5 above the rim plane); grooves Y to ±11.3, Z 1.2 to 4.2 (0.3 all round, measured 0.2996); lower lips Z 0 to 1.2 leave a 19.6 bottom opening; a gable-shaped plug on the door (to Z 7.7, X 76.4 to 78.8) fills a matching gable slot (flat 15.0 wide at Z 8.0, 45° sides from Y ±11.3 at Z 4.2) that runs through the cross-block and the +X wall (X 73.6 to 78.8), so that no bridge exceeds 15.0; two detent bumps 0.7 high on the door rails; grip 1.5 beyond the +X face |
| Pico | PCB X 4.05 to 55.05, Y ±10.5, Z 28.8 to 29.8; receptacle X 2.75 to 8.25, top Z 32.6; `USB_MOUTH` (2.75, 0, 31.2); four posts OD 5.4, Z 25.8 to 28.8 at X 6.05 and 53.05, Y ±5.7, pilots Ø1.7 depth 5.0; keep-out above to Z 33.8 (lid lip at 34.5), below to Z 26.8 (shelf top 25.8) |
| USB opening | X 0 to 2.4, Y ±5.3, Z 27.4 to 35.0 (10.6 × 7.6; plug overmold 10.0 × 7.0 plus 0.3 each side; measured plug gap 0.30; ligament to the rim 1.5) |
| switch | body X 55.9 to 68.4, Y 5.5 to 11.0, Z 25.8 to 31.8; handle X 60.65 to 63.65, Y 11.0 to 15.0 (1.5 beyond the wall), Z 27.3 to 30.3; slot X 58.5 to 65.8, Z 26.9 to 30.7 (measured handle-sweep gap 0.40); ribs at X 55.4 to 55.8 and 68.5 to 69.0 up to Z 29.7; terminal zone Y 0.5 to 5.5 empty |
| lid screws | two bosses OD 6.0 at X 72.4, Y ±6.0, Z 25.8 to 34.2, pilots Ø2.5 depth 8.0 (Z 26.2 to 34.2); M3 × 12 (tip at Z 26.5) |
| wire passages | Ø4.0 through the shelf at (4.6, 0) and (72.0, 0) |
| checks run | cell penetration ≤ 0.01 mm³ (tangent to the 45° faces); capture hits: +Y/−Y 345 mm³, +Z 644, −Z 362 (1.0 translations), +X 38, −X 272 (4.0 translations); cell drop-out path clear; reserves 0.0; Pico, keep-outs and driver columns 0.0 (rib top kept at Z 29.7 for the driver columns); switch install path 0.0; door sweep intersection 0.0006 mm³ (detent bumps not modelled in this check); overhang scan: only bridges (groove ceilings 1.5, roof 7.1, gable 15.0, switch slot 7.3, USB opening 10.6); base bed contact 32% |

## 8. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 | Method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1–L2.1.3 | L3.1.1.1, L3.1.2.1–3, L3.1.3.1 | L1.1 | inspection | "a Pico 2 and one 18650 cell" |
| L1.2 | Cell housed | L2.2.1–L2.2.3 | L3.2.1.1, L3.2.2.1–2, L3.2.3.1 | L1.2 | analysis | "18650 cell (18.6 x 65.2 mm)", "printed cradle" |
| L1.3 | Cell retained | L2.3.1–L2.3.3 | L3.3.1.1, L3.3.2.1, L3.3.3.1 | L1.3 | demonstration | "door ... that retains it" |
| L1.4 | Door | L2.4.1–L2.4.4 | L3.4.1.1–2, L3.4.2.1–3, L3.4.3.1, L3.4.4.1–3 | L1.4 | test | "sliding door on the bottom", "0.3 mm per side" |
| L1.5 | Cell removal | L2.5.1–L2.5.2 | L3.5.1.1, L3.5.2.1 | L1.5 | test | "door on the bottom that retains it" |
| L1.6 | Pico mounting | L2.6.1–L2.6.4 | L3.6.1.1–4, L3.6.2.1–3, L3.6.3.1–2, L3.6.4.1 | L1.6 | analysis | "a Pico 2" |
| L1.7 | USB | L2.7.1–L2.7.3 | L3.7.1.1, L3.7.2.1, L3.7.3.1 | L1.7 | test | "the micro-USB opens at one end" |
| L1.8 | Switch | L2.8.1–L2.8.4 | L3.8.1.1–3, L3.8.2.1–2, L3.8.3.1, L3.8.4.1 | L1.8 | test | "SK12D slide switch pokes through the side" |
| L1.9 | Lid | L2.9.1–L2.9.3 | L3.9.1.1, L3.9.2.1–3, L3.9.3.1–3 | L1.9 | inspection | implied (the Pico must be installable) |
| L1.10 | Closed, walls | L2.10.1–L2.10.3 | L3.10.1.1, L3.10.2.1–2, L3.10.3.1 | L1.10 | analysis | "Weatherproof-ish" |
| L1.11 | Printable | L2.11.1–L2.11.4 | L3.11.1.1, L3.11.2.1, L3.11.3.1, L3.11.4.1 | L1.11 | analysis | implied (FDM) |
| L1.12 | Compact, stable | L2.12.1–L2.12.2 | L3.12.1.1, L3.12.2.1 | L1.12 | analysis | "sensor node" |
| L1.13 | Evidence | L2.13.1–L2.13.2 | L3.13.1.1–2, L3.13.2.1 | L1.13 | inspection | needed by the judge |

## 9. Grading (design-specific; used because `generalize/rubric.md` is missing)

- **Verdict:** WRONG (any gate G0 to G5 fails), MINOR (no gate fails, some weight-3 L3 fails), CORRECT (every
  weight-3 L3 passes), MEETS (CORRECT and every L3 of weight 1 and 2 passes). UNVERIFIED counts as FAIL. Report
  also the weighted score Σ(weight × pass)/Σ(weight) and the worst normalised margin among weight-3 L3s.
- **Precedence:** numbers in this document beat `part.json`. The plug and sweep checks (L3.7.1.1, L3.8.1.1) outrank
  everything about opening size. Designed contact is never interference. Never relax a criterion or round in the
  design's favour beyond ε.
- **WHERE a defect is:** one entry per failed or UNVERIFIED L3, gates first then weight 3, 2, 1, with: `req` (L3 with
  L2 and L1), `status`, `body` (`base`, `lid`, `door`, `both` or `layout`), `feature` (named by function, for example
  "switch slot in the +Y wall" or "cell cradle roof"), `face` (surface and outward normal), `location` (point or
  bounding box in the enclosure frame), `measured` / `limit` / `margin`, `reference` (M-CELL, V-USB-PLUG and so on, with
  the datum), `needed` (the geometric target as numbers, for example "roof must be within 1.0 above the cell top, now 2.3")
  and `evidence` (saved defect STL). `needed` never says how to build it.
- **Measured-values table (always filled in):** cell penetration, side gaps, capture hits and distances; free length at the
  contact reserves; door thickness, recess, lateral and vertical clearance, sweep intersection, detent depth, grip;
  bottom opening width; post count, OD, pilot, seating; keep-out d; Pico-in-cavity d; wire passages; USB plug d and opening
  size; switch sweep d, protrusion, slot size, capture hits, terminal d; lid lip gap, engagement, plate; boss and hole data;
  unlisted openings; wall, shelf, lid thickness; shells; overhang patches; bed contact; bounding box; self-report agreement.

## Audit

Adversarial audit of this entry against `benchmarks/enclosure/rubric.md` (the generalize rubric is absent), the catalogue
parts and the L1 text in `design.json`. The feasibility sketch of section 7 was rebuilt in `manifold3d` (base, door, cell,
reserves) and the claims below were re-measured; the part ids (`rpi_pico2`, `cell_18650`, `slide_sk12d`, `plug_microusb_b`,
`screw_m2_selftap`, `screw_m3_selftap`) all load through `parts.Catalog` and pass `parts.validate`. L1 count 13 (E1-01 has 12),
L2 40, L3 63 (E1-01: 45, 69); the counts in section 6 match the tables.

| # | Finding | Fix |
|---|---|---|
| 1 | The contact-reserve cylinder was Ø16.0 (A2, section 2), but `cell_18650/part.json` defines `neg_contact` and `pos_contact` as cylinders of the cell diameter (Ø18.6) and 3.0 long. The number was nowhere derived. | V-CONTACT-N and -P are now Ø18.6 x 3.0 from the catalogue keep-outs. Re-measured: with the sketch, penetration of both reserves is 0.0006 mm³ (tangent faceting), so the sketch still passes. |
| 2 | Sketch bridge: the door slot under the cross-block (X 73.6 to 76.4) had a 22.6 mm wide ceiling at Z 4.2, an unsupported bridge above the 15.0 limit of L2.11.2 (re-measured: two overhang patches of 27 and 23 mm², 22.6 wide). The sketch claimed "no bridge exceeds 15.0" but only gabled the end wall. | Section 7: the gable-shaped slot (flat 15.0 at Z 8.0, 45 degree sides from Y ±11.3 at Z 4.2) runs through the cross-block and the +X wall, X 73.6 to 78.8; the door's plug stays in the wall (X 76.4 to 78.8). Re-measured: the only overhang patches left are bridges of 1.5 (groove ceilings), 7.1 (roof), 15.0 (gable), 10.6 and 7.3 (openings). |
| 3 | Sketch lid screws: bosses with pilot depth 6.0 and an M3 x 12 screw cannot both be true (screw tip 1.7 below the pilot floor with the head 1.7 off the plate); M3 x 10 gives 5.7 of engagement, below the 6.0 minimum of `screw_m3_selftap`. | Pilot depth 8.0 (Z 26.2 to 34.2), screw M3 x 12 (tip at Z 26.5, engagement 7.7); L3.9.3.1 still asks for a depth of at least 6.0. A8 now states the length rule (plate + gap + engagement >= 10.3). |
| 4 | L2.4.2 / L3.4.2.1: the sweep criterion mixed "total" intersection with "distance >= 0.25 everywhere else", although the closed door touches its end stop (distance 0, designed contact) and a detent bump rides the groove ceiling at every step, so a sum over 100 steps is unbounded. | The criterion is the maximum over the 1.0 mm steps (not a sum), the end-stop contact and the detent are named exceptions. |
| 5 | A13 cited L3.6.5.1, which does not exist. | Now L3.6.4.1. |
| 6 | Sketch numbers: base bed contact was quoted as 34%; re-measured 32% (677 of 2 128 mm²). Capture hits "+X 38, -X 269" are for the 4.0 mm translation of L3.3.3.1 (re-measured 38.4 and 271.6); +Y/-Y 345, +Z 644, -Z 362 for 1.0 mm (quoted 344, 643, 361). | Text corrected. |
| 7 | Numbers the judge uses that the agent was never told: cell rests within 0.3 of the door; detent depth 0.3 to 0.8, grip 1.0 to 5.0, door overlap 1.0 over 60% and recess 0.3 to 3.0; bottom opening 0.3 wider than the cell; wire passages 4.0; plug envelope 0.3; switch capture 1.0 and terminal room 5.0; lid fit, engagement, plate and height; install paths and screwdriver access; seam gap 0.4; ligament 1.0; bed contact 25% / 50%. | Added to the L1 texts in `design.json` (ids and count unchanged). The request text itself is unchanged and states only the owner's words plus the layout decisions. |

Checked and found consistent (no change): cell at X 5.4 to 70.6, axis Z 13.2, door top 3.9 (cell rests, gap 0); side gaps 0.5; 45 degree
faces tangent to the cell (distance 9.298 vs radius 9.3); free length 71.2; door clearances 0.30; Pico, posts, keep-outs and
USB opening (plug margins 0.30, ligament 1.5); switch geometry (handle sweep gap 0.40, slot 7.3 x 3.8, terminal zone, ribs);
wire passages clear of posts and bosses; envelope 80.3 x 27.0 x 38.5.

Observations (not changed): (a) the switch body's corner (X 55.9 to 56.05) lies inside the Ø6.0 driver column of the Pico hole at
X 53.05; the column is only checked against BASE, so this is not graded; a design that wants real finger room should keep the
switch 0.2 further along X. (b) The detent is a rigid interference of up to 0.8; a flexing detent is a design choice the checks do
not distinguish. (c) A11 numbers (plug 10.0 x 7.0, handle 4.0) are catalogue values; the L1 text still says "SK12D type".
