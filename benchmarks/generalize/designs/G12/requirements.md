# G12 Wall-mount ESP32 box with LED light pipes: requirements (L1 / L2 / L3)

Design G12 is a wall-mount ESP32 box. It is graded on the board's placement and support (it has no
mounting holes), on the antenna keep-out and header keep-outs, on the micro-USB plug that
must seat through one short end, on three LEDs held flush in the lid, on two countersunk mounting slots
100 mm apart with a 3 mm edge distance, and on the usual printability and evidence rows. It is a
training design for the generalisation set; the method (declared layout, catalogue parts placed by
datums, interference and clearance against keep-out volumes, numbers only in the request and the
catalogue) is the same as the enclosure benchmark.

**Request (as given to the agent):** I need a wall-mounted enclosure for an ESP32 DevKitC V4 board (54.4 x 27.9 mm, no mounting holes, micro-USB at one short end, PCB antenna at the other). It has two mounting ears that take 4.2 mm countersunk wood screws, the two screw slots 100 mm apart, and every slot must leave at least 3 mm to the edge of its ear and to the box. Three 5 mm LEDs shine through the lid: the LEDs sit flush with the outside of the lid and must not fall out. The micro-USB cable must plug in through one short end with the lid on. Keep the antenna end of the board free: no wall or lid over the antenna and at least 8 mm of free space beyond the end of the board. The lid is held by M3 self-tapping screws. It is printed on an FDM printer in PLA, back face down.

**Plan brief (verbatim):** "A wall-mounted ESP32 enclosure with two mounting ears taking 4.2 mm countersunk wood screws, 100 mm apart. Three 5 mm LEDs shine through the lid; the LEDs sit flush with the outside and must not fall out. The ear slots must leave at least 3 mm to the box edge."

**Split:** train. **Family:** electronics_enclosure. **Capabilities exercised:** wall_mount, led_lightpipe, counterbore, datum_placement, plug_envelope_opening, standoffs.

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check Python can run on the delivered STLs. Every L3
row has a method (inspection, analysis, demonstration, test, human; see `design.json`), a pass/fail
criterion with a number and a tolerance, a weight (3 = critical, 2 = major, 1 = minor) and a gate
mark where a failure makes the design WRONG. Every number that comes from an assumption (section
3.1) is provisional until Robin confirms it. No number here may appear in agent logic: target
numbers live in the request text, in `part.json` catalogue data and in this file only.
Where this file and a `part.json` disagree, this file wins (section 7.3).

---

## 1. Frames, tolerances and the checks

### 1.1 Frames

- **Box frame (all tables below):** the ESP32's own frame: X along the board's 54.4 mm side with the micro-USB end at **−X** and the antenna end at **+X**,
  Y along the 27.9 mm side, **Z = 0 at the PCB's underside**, Z up (away from the wall). The PCB occupies Z 0 to 1.6, X 0 to 54.4, Y 0 to 27.9. The box's back face
  (the face against the wall) is the lowest plane. A box delivered mirrored or rotated is normalised into this frame before grading (7.2 step 3); that is never penalised.
- **Part frames:** `esp32_devkitc_v4` is placed at the identity pose unless the layout declares another; `led_5mm` (origin on the lens axis at the flange bottom plane, dome toward +Z) at each declared LED position with its axis along +Z; `plug_microusb_b` (origin at the tip, body along +X, inserted along −X) is placed at full mate by the grader; `screw_m3_selftap` (head bearing face at the origin, shank toward −Z) in each lid screw.

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered meshes, never by eye.

| Quantity | Measurement tolerance ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within ε (e.g. "≥ 0.50" passes at 0.48) |
| angle | 0.5° | same |
| interference volume | 0.01 mm³ | "no interference" means intersection volume ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the hole's section (what a screw or pin sees) | |
| boss / pin / spigot OD | smallest enclosing circle of the section | |

Where a criterion is written "nominal ± t", t is the design tolerance and ε is added to it. A mesh
is tessellated: a circle of nominal diameter D measures D·cos(π/N) at worst, so compare diameters
with ε = 0.05 for holes and bosses (the grader fits circles to the section, it does not read vertices).

### 1.3 The checks and designed contact

- **`clear_of(bodies, volume, clearance)`**: the minimum Euclidean distance between every printed
  body in `bodies` and `volume` is ≥ `clearance`. Reported value: the signed minimum distance d
  (negative = penetration; the penetration volume is reported too). Pass: d ≥ clearance − ε.
- **`inside(volume, solids, clearance)`**: `volume` lies entirely inside the convex hull of `solids`
  (or inside the named cavity) and every point of it is ≥ `clearance` from the boundary. Pass:
  d ≥ clearance − ε.
- **`sweep(model, path, bodies)`**: the model is moved along `path` in steps of at most 1.0 mm
  (and the swept union is also tested); pass when the penetration volume with `bodies` stays
  ≤ 0.01 mm³ at every step.

`bodies` is **ALL** (every printed body, closed or in the assembly pose), or one named body. A
design never builds or edits the reference volumes: the grader generates them independently from
the catalogue and the design's declared layout. The agent may generate the same volumes for its
own checks, but its copies are not trusted for grading.

**Designed contact for this design (is never interference).** Parts that are meant to touch are excluded from every interference and clearance check; for these pairs only penetration counts (intersection volume above 0.01 mm³; a distance of zero is a pass):

- the PCB's underside resting on the four pad tops
- the LED flange against the shoulder of its collar, and the lens in its hole (only the radial play of L2.5.1 applies to the lens)
- a lid screw in its pilot, and its head on the lid tab
- the lid lip against the base's locating faces, at the fit of L2.8.2
- the lid resting on the base rim
- the 4.2 wood screw's head in the countersink (a reference cone, see 2.2)

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` in `benchmarks/generalize/parts/<id>/` (`esp32_devkitc_v4`, `led_5mm`) and `benchmarks/enclosure/parts/<id>/` (`plug_microusb_b`, `screw_m3_selftap`). These are the only places target-specific part numbers may live. There is no catalogue part for the 4.2 mm wood screw; its numbers are in the request and in assumption A4.
- **envelope**: a keep-out or access volume generated by Python from datums. Never drawn by hand.
- **computed**: derived from the delivered STLs (cavity, apertures, ear and slot geometry).

### 2.2 Reference models (M-)

Default layout when a design declares none: the ESP32 at the identity pose, LEDs at X = 12.0, 22.0, 32.0, Y = 13.95.

| Name | What | Source | Size and default position (box frame, mm) | Datums |
|---|---|---|---|---|
| **M-ESP** | ESP32 DevKitC V4 with module, headers and micro-USB | catalogue `esp32_devkitc_v4` | PCB 54.4 × 27.9 × 1.6, Z 0 to 1.6; micro-USB receptacle 5.9 (X) × 7.5 (Y) × 2.9 (Z) at X −1.0 to 4.9, Y 10.2 to 17.7, Z 1.6 to 4.5; ESP32 module 25.5 × 18.0 × 3.1 at X 28.9 to 54.4, Y 4.95 to 22.95, Z 1.6 to 4.7; header bodies on top, X 3.07 to 51.33, rows at Y 1.25 and 26.65, 2.54 wide, Z 1.6 to 4.1 | `USB_MOUTH` (−1.0, 13.95, 3.05), `USB_AXIS` (−X), `EDGE_LONG_A/B`, `EDGE_USB`, `EDGE_ANTENNA`, `PINS_A/B` |
| **M-KEEP** | the part's keep-outs | catalogue `esp32_devkitc_v4` `keepouts` | `component_side`: X 0 to 28.9, Y 0 to 27.9, Z 1.6 to 5.2 (3.6 above the PCB top); `antenna_zone`: X 48.4 to 62.4, Y 0 to 27.9, Z 1.6 to 9.7 (3.1 + 5.0 above the PCB top); `header_pins_a/b`: the header footprints, Z 1.6 to 10.1 (8.5 above); header tails: the header footprints, Z −3.0 to 0 | |
| **M-LED-k** (k = 1..3) | 5 mm LED | catalogue `led_5mm` | flange Ø5.8 × 1.0, lens Ø5.0 up to the dome top 8.6 above the seat; default seat Z 6.9, so the dome top is at Z 15.5 | `AXIS`, `SEAT`, `PANEL_SEAT`, `DOME_TOP` |
| **M-PLUG-USB** | micro-USB B plug | catalogue `plug_microusb_b` | shell 6.9 (Y) × 1.85 (Z), mated depth 5.0, exposed shell 1.5; overmold 10.0 (Y) × 7.0 (Z) × 20 long | `PLUG_TIP`, `PLUG_AXIS`, `OVERMOLD_FACE` |
| **M-WSCREW-k** (k = 1, 2) | 4.2 mm countersunk wood screw, a reference cone | request / A4 | shank Ø4.2; head 90° countersunk Ø8.4 (height 2.1), axis on slot k's centre, head top flush with the ear top | slot-centre point |
| **RGA** | reference assembly = M-ESP ∪ M-LED-1..3 ∪ M-WSCREW-1, 2 | assembled | as above | all of the above |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Definition (default layout, box frame, mm) |
|---|---|---|
| **V-KO** | the board's keep-out set | M-KEEP, each volume used as listed |
| **V-KO-BOT** | tails and header footprint below the board | header footprints, Z −3.3 to 0 (tails 3.0 + 0.3), the pad columns excluded |
| **V-ANT-FREE** | free space beyond the antenna end | X 54.4 to 62.4, Y 0 to 27.9, Z 1.6 to 9.7 |
| **V-SEAT-k** | where a pad may touch the board | the pad footprint under the PCB (the pad tops) |
| **V-USB-PLUG** | micro-USB plug at full mate and its withdrawal path | shell 6.9 × 1.85 from X 4.0 (tip, 5.0 inside the mouth) to X −2.5 (1.5 exposed), overmold 10.0 × 7.0 from X −2.5 outward to X −42.5, centred on (Y 13.95, Z 3.05) |
| **V-LED-VIEW-k** | the LED's view zone | the part's `view_zone`: Ø5.0 × 2.0 above `DOME_TOP` |
| **V-CHUCK-k** (k = 1, 2) | wood-screw access | Ø8.4 column on slot k's centre from the ear top up to +30 |
| **V-DRIVER-j** (j = 1..4) | access to a lid screw | Ø6.0 column on each lid screw axis from the lid top to +50 |
| **V-CAVITY** | the closed box's inner void | computed: convex hull of (BASE ∪ LID, closed) minus (BASE ∪ LID), the component holding the board centroid |
| **V-AP-USB** | the openings present in the −X end wall | computed: wall slab minus (BASE ∪ LID) |
| **V-AP-OTHER** | every other opening | computed: every through path from outside into V-CAVITY, as connected regions |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-ESP | units | PCB 54.4 × 27.9 ± 0.2 |
| R2 | M-ESP | header rows | 25.4 ± 0.05 apart, 2.54 pitch |
| R3 | M-ESP | USB direction | `USB_AXIS` along −X; antenna at +X |
| R4 | M-LED | size | flange Ø5.8 ± 0.1, lens Ø5.0 ± 0.1, height 8.6 ± 0.3 |
| R5 | M-PLUG-USB | overmold | 10.0 × 7.0 ± 0.2 |
| R6 | M-KEEP | each keep-out is generated from the part's datums | equal to the part.json boxes ≤ 0.01 |
| R7 | RGA | models do not collide | intersection ≤ 0.01 mm³ |

**Seating rule.** The RGA is placed at the pose declared in `layout.json`. The grader verifies: `PCB_BOTTOM` lies on the pad tops (≤ 0.10), the board's X/Y position lies within 1.0 of the box frame's centred position (the stops allow at most 1.0), and each LED's `PANEL_SEAT` lies on its collar's shoulder (≤ 0.10) with its axis on the hole axis (≤ 0.15). If the declaration is missing or fails, the board is seated on the pads and centred between the stops, and the L3 rows for the pose fail.
---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (with uncertainty)

Each line gives the value chosen and why. Robin may correct any of them; a correction changes this file and the catalogue, and earlier scores become stale.

| # | Question | Value chosen | Why and uncertainty |
|---|---|---|---|
| A1 | ESP32 numbers? | PCB 54.4 × 27.9 × 1.6; no mounting holes; micro-USB 7.5 × 5.9 × 2.9 overhanging by 1.0; module 25.5 × 18.0 × 3.1 at the antenna end; headers 2 × 19, rows 25.4 apart; tallest other top part 3.6. | Espressif ESP32-DevKitC V4 guide and the catalogue. The overhang, thickness and first-pin offset are ±0.5; measure the owner's board. |
| A2 | Header pins? | Pins point **up**: tips 8.5 above the PCB top, tails 3.0 below the PCB bottom (the catalogue `header_pins` and tail keep-outs). | Dupont-wire envelope as supplied. If the pins are cut, the ceiling and the pad height may shrink (not graded). Uncertainty ±1.0 on both. |
| A3 | Mounting position? | The back face on a vertical wall (gravity acts in the board's plane) or on a horizontal surface that is below the box. Not on a ceiling. | The board rests on pads and is located by stops and walls, not clamped from above: a ceiling mount would let it fall. The brief says wall-mounted. |
| A4 | The 4.2 mm wood screw? | Countersunk, 90° head Ø8.4 (≈ 2 × 4.2), head height 2.1, shank Ø4.2; the hole is Ø4.5 (shank + 0.3). | No catalogue part. DIN 7997 / #8 class; the head diameter is ±0.5. The slot is a stadium Ø4.5 with centres 4.0 apart (overall 8.5 long) so the owner can adjust the 100 mm spacing by ±2.0. |
| A5 | Micro-USB plug? | Overmold 10.0 × 7.0, shell 6.9 × 1.85, mated depth 5.0, 1.5 exposed shell. | `plug_microusb_b`. Typical cables; measure the owner's. The 2.5 end wall is thicker than the 1.5 exposed shell, so the overmold must enter the opening for the plug to seat. |
| A6 | LED numbers? | Lens Ø5.0, flange Ø5.8 × 1.0, height 8.6 to the dome. | `led_5mm`. Flange ±0.3, height 8.4–9.0, so the dome ends within ±0.3 of the lid face: that is the flush tolerance. |
| A7 | Printing? | FDM, PLA, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. Base: back face (ears) on the bed, open side up. Lid: outer face on the bed. A downward-facing step of at most 1.0 deep (an LED shoulder or lip) is not an overhang. | Common printers. The exemption covers the collar's snap lip (0.35 step; the shoulder step is 0.4 but recedes outward in the lid-down print, so it is not an overhang). Sliding fit 0.15–0.35 per side. |
| A8 | Wall thickness? | Walls 2.5; floor 3.0; lid plate 3.0; ear thickness 4.0 (3.5–5.0). All 2.0–4.0 (the ears 3.5–5.0). | Five to six perimeters; 4.0 under a countersink of depth 1.95 leaves 2.05 of shank land. |
| A9 | Maximum size? | Closed bodies at most 125 × 50 × 26 (X × Y × Z) including ears and tabs, excluding the LED domes. | The sketch is 119.0 × 47.9 × 22.0. |
| A10 | Antenna keep-out? | No material in `antenna_zone` (X 48.4–62.4, Y 0–27.9, Z 1.6–9.7) and the cavity extends at least 8.0 beyond the board end. | The part's keep-out; the request says 8 mm beyond. Espressif's own guidance is at least 15 mm of free board; the part is the arbiter here (uncertainty ±3 mm). |

### 3.2 Fixed decisions (one choice, no alternatives graded)

| # | Ambiguity | Decision | Reason |
|---|---|---|---|
| FD1 | How is the lid held? | By **four M3 self-tapping screws** (`screw_m3_selftap`, length 10.0) in four **tabs outside the cavity**: a base tab on the outside of each long wall (8.0 along X, 7.0 outward, from the back plane up to the rim, pilot Ø2.5 ≥ 6.0 deep from the rim) and a lid tab (an extension of the lid plate, 3.0 thick, hole Ø3.4). No snap, no inner bosses. | The antenna zone and the pin keep-outs fill the cavity corners; tabs outside the cavity cannot enter any keep-out. |
| FD2 | How is the board held? | On **four pads** under the PCB in the clear end regions (X 0 to 2.77 and X 51.63 to 54.4; each pad ≥ 10 mm², top at the PCB bottom, tops coplanar within 0.10), located by the walls (0.2–1.0 clearance on every side) and **two stops** at the antenna end (0.2–1.0 from the PCB end, up to Z 0.8 only). | The board has no holes. The stops stay below the PCB top (Z 1.6), so they never enter the keep-outs. |
| FD3 | What is '100 mm apart'? | The distance between the two slot **centres** (mid-points of the stadium centre-line): **100.0 ± 0.2**, symmetric about the box centre within 0.5. | The brief's wording; the slot's adjustment range is ±2.0 on top of that. |
| FD4 | What is 'the box edge' for the 3 mm? | Both: from the **countersink outline** (the largest feature, Ø8.4) to every free edge of the ear (≥ 3.0) and to the box's outer wall face (≥ 3.0). | Both readings are checked so the design needs only one choice; the sketch has 3.3 and 9.05. |
| FD5 | What is an LED 'light pipe' here? | Each LED sits in a **collar** on the lid underside: through hole Ø5.3 (5.2–5.4), a flange pocket Ø6.1 (6.0–6.2) 1.0–1.3 deep (from the snap lip's top face to the shoulder), and a **snap lip** (opening Ø5.4, 5.3–5.6; 0.6–1.0 thick) with ≥ 2 relief slits. The dome ends within ±0.3 of the lid's outer face. | The LED is pushed in from the inside and cannot fall out of the front (flange on the shoulder) or the back (snap lip). Flange 5.8 > lip 5.6. |
| FD6 | Print orientation? | Base: back face on the bed (ears and floor underside coplanar). Lid: outer face on the bed. Declared in `layout.json`. | Matches 'back face down' in the request. |
| FD7 | Seam height? | The seam (base rim) at Z = **12.5** in the sketch (band 10.4–16.5). | Lid underside at least 0.3 above the header pin tips (Z 10.1; L3.2.3.1) and at most the size limit (L3.11.1.1: seam ≤ 16.5 for Z ≤ 26 with the plate 3.0 and the back at −6.5); the LED collars' bottom stays 0.3 above the component keep-out. |

---

## 4. Requirements tree

### L1.1 The ESP32 and the three LEDs are laid out by their datums

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: the board's pose, each LED's position and each body's print orientation. | inspection | `layout.json` present, parses, names `esp32_devkitc_v4`, three `led_5mm` | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 |  |
| L3.1.1.2 | The declared pose verifies under the seating rule. | analysis | PCB bottom on the pad tops ≤ 0.10; LED seat on the collar shoulder ≤ 0.10; axis ≤ 0.15 | 3 |  |
| L2.1.2 | USB faces −X, the antenna faces +X. | inspection | `USB_AXIS` within 1.0° of −X; `USB_MOUTH` X in [−1.5, −0.5] | 3 | |
| L3.1.2.1 | USB axis direction and mouth position in the declared layout. | inspection | ≤ 1.0°; X in [−1.5, −0.5] | 3 |  |
| L2.1.3 | The LEDs are in a row on the lid clear of the header rows and the antenna. | inspection | three LED axes; pitch ≥ 10.0; each axis ≥ 4.5 in plan from the `header_pins_a/b` and `antenna_zone` boxes (collar radius 3.85 minimum + 0.3 clearance, rounded up) | 2 | |
| L3.1.3.1 | LED axis positions and pitch. | inspection | as L2 | 2 |  |

### L1.2 The board is held on four pads and located by the walls, with the keep-outs clear

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Four pads in the clear end regions. | inspection | count = 4; X in [0, 2.77] or [51.63, 54.4]; each area ≥ 10 mm²; top-plane spread ≤ 0.10; tops on the PCB bottom within 0.10 | 3 | |
| L3.2.1.1 | Number of pads. | inspection | count = 4 | 3 | G2 |
| L3.2.1.2 | Pad position, area and top-plane spread. | inspection | as L2 | 3 |  |
| L3.2.1.3 | Pads fused to the floor; base is one connected body. | analysis | contact ≥ 10 mm² each; 1 shell | 2 |  |
| L2.2.2 | The walls and stops locate the board. | analysis | clearance to M-ESP (PCB, headers, receptacle) on the two long sides and the USB end 0.2–1.0; PCB end to the nearest stop 0.2–1.0; stops reach Z ≥ 0.8 and stay below Z 1.6 | 3 | |
| L3.2.2.1 | Lateral clearance, four sides. | analysis | 0.2 ≤ c ≤ 1.0 | 3 |  |
| L3.2.2.2 | Number and height of antenna-end stops. | inspection | ≥ 2; top Z between 0.8 and 1.6 | 2 |  |
| L2.2.3 | No printed body enters a keep-out of the board. | analysis | clear_of(ALL, component_side ∪ header_pins_a/b, 0.3); clear_of(ALL, V-KO-BOT, 0.0) | 3 | |
| L3.2.3.1 | Top keep-outs clear (component side, header pins). | analysis | d ≥ 0.30 for the lid; ≥ 0.0 for every body | 3 | G2 |
| L3.2.3.2 | Tail zone below the header footprint clear. | analysis | d ≥ 0.0 | 3 | G2 |
| L3.2.3.3 | Floor top to PCB bottom (pad height). | inspection | 3.3 ≤ h ≤ 6.0 | 2 |  |

### L1.3 The antenna end is free

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Nothing in the antenna zone. | analysis | clear_of(ALL, antenna_zone, 0.0) | 3 | |
| L3.3.1.1 | Antenna keep-out free of printed bodies. | analysis | penetration ≤ 0.01 mm³ | 3 | G6 |
| L2.3.2 | The cavity extends past the board end. | analysis | inside(V-ANT-FREE, V-CAVITY, 0.0); inner wall to the PCB end ≥ 8.0 | 3 | |
| L3.3.2.1 | V-ANT-FREE inside the cavity. | analysis | d ≥ 0.0 | 3 | G6 |
| L3.3.2.2 | Inner X length from the PCB end to the +X wall inner face. | inspection | ≥ 8.0 | 2 |  |

### L1.4 A micro-USB plug seats through the −X end wall with the lid on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The plug reaches full mate and can be withdrawn. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 | |
| L3.4.1.1 | USB plug envelope clear. | test | d ≥ 0.30 | 3 | G3 |
| L2.4.2 | The opening is not oversized. | analysis | inside(V-AP-USB, V-USB-PLUG offset by 1.5, 0.0): opening ≥ 10.6 × 7.6 and ≤ 13.0 × 10.0 | 2 | |
| L3.4.2.1 | Opening width × height and centre. | analysis | between 10.6 × 7.6 and 13.0 × 10.0; centre within 0.5 of Y 13.95, Z 3.05 | 2 |  |
| L2.4.3 | Exactly one opening in the −X wall, with material round it. | inspection | V-AP-USB has 1 region; ligament to the seam, the floor and the corners ≥ 1.5 | 2 | |
| L3.4.3.1 | Opening count and ligament. | inspection | 1; ≥ 1.5 | 2 |  |

### L1.5 Three LEDs sit flush in the lid and cannot fall out

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Three holes of the right size. | inspection | count = 3 through the lid top; inscribed Ø 5.2–5.4; axis within 0.15 of the LED axis | 3 | |
| L3.5.1.1 | Number of LED holes through the lid. | inspection | count = 3 | 3 | G5 |
| L3.5.1.2 | Hole inscribed diameter and axis offset. | inspection | 5.2 ≤ Ø ≤ 5.4; offset ≤ 0.15 | 3 | G5 |
| L2.5.2 | Each dome is flush with the outside. | analysis | DOME_TOP minus the lid's outer-face plane within ±0.3 | 3 | |
| L3.5.2.1 | Dome height relative to the lid's outer face, each LED. | analysis | −0.3 ≤ Δ ≤ +0.3 | 3 | G5 |
| L2.5.3 | Each LED is captured in both directions. | analysis | front: flange overlap on the shoulder ≥ 0.2 per side; back: lip opening Ø5.3–5.6 (< flange 5.8) with ≥ 2 relief slits; flange pocket Ø6.0–6.2 | 3 | |
| L3.5.3.1 | Flange overlap on the shoulder and PANEL_SEAT on it. | analysis | ≥ 0.2 per side; seat ≤ 0.10 | 3 | G5 |
| L3.5.3.2 | Snap lip: opening, thickness and slit count. | inspection | Ø 5.3–5.6; 0.6–1.0; ≥ 2 slits | 2 |  |
| L3.5.3.3 | Flange pocket diameter and depth (lip top face to shoulder). | inspection | Ø 6.0–6.2; 1.0–1.3 | 2 |  |
| L2.5.4 | The LED parts clear everything else. | analysis | M-LED-k ∩ (BASE ∪ LID) ≤ 0.01 mm³ outside the lens-in-hole play; clear_of(collar, M-ESP ∪ component_side ∪ header_pins, 0.3); view zones clear | 2 | |
| L3.5.4.1 | Collar bottom to the board's keep-outs. | analysis | d ≥ 0.30 | 2 |  |
| L3.5.4.2 | View zones clear of printed bodies. | analysis | penetration ≤ 0.01 mm³ | 2 |  |

### L1.6 Two mounting ears with countersunk slots 100 mm apart

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Two slots 100.0 apart. | inspection | count = 2; slot-centre distance 100.0 ± 0.2; symmetric about the box centre within 0.5; slot axes parallel to Z | 3 | |
| L3.6.1.1 | Number of ear slots. | inspection | count = 2 | 3 | G4 |
| L3.6.1.2 | Distance between the slot centres. | inspection | 100.0 ± 0.2 | 3 | G4 |
| L2.6.2 | Slot and countersink size. | inspection | slot width Ø 4.5 ± 0.15 (stadium); centre-line length 4.0 ± 0.3; countersink 90° ± 5°, Ø 8.4 ± 0.3 at the ear top; ear thickness 3.5–5.0 | 3 | |
| L3.6.2.1 | Slot width and length. | inspection | 4.5 ± 0.15; 4.0 ± 0.3 | 3 |  |
| L3.6.2.2 | Countersink diameter and angle. | inspection | 8.4 ± 0.3; 90° ± 5° | 3 |  |
| L3.6.2.3 | Ear thickness. | inspection | 3.5 ≤ t ≤ 5.0 | 2 |  |
| L2.6.3 | At least 3.0 of material round each countersink. | analysis | distance from the countersink outline to every free edge of the ear ≥ 3.0 and to the box's outer wall face ≥ 3.0 | 3 | |
| L3.6.3.1 | Countersink to the ear's free edges. | analysis | ≥ 3.0 | 3 | G4 |
| L3.6.3.2 | Countersink to the box's outer wall. | analysis | ≥ 3.0 | 3 | G4 |
| L2.6.4 | A screw and its driver reach each slot. | analysis | clear_of(ALL, V-CHUCK-k, 0.0) for k = 1, 2; M-WSCREW-k inside the countersink with the head top flush within 0.3 | 2 | |
| L3.6.4.1 | Screw-head columns clear of every printed body. | analysis | penetration ≤ 0.01 mm³ | 2 |  |
| L3.6.4.2 | Ears fused to the box (one shell each body). | analysis | contact ≥ 40 mm² per ear | 2 |  |

### L1.7 The back is flat for the wall

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The back plane. | inspection | back-face flatness ≤ 0.3 over the floor and the ears; ears' back faces on the same plane within 0.2; nothing below it | 2 | |
| L3.7.1.1 | Flatness of the back face including the ears. | inspection | ≤ 0.3 | 2 |  |
| L3.7.1.2 | Ear back faces against the floor underside. | inspection | ≤ 0.2 apart | 2 |  |
| L2.7.2 | It stands on its back without tipping. | analysis | stable at 5° tilt on the back face | 1 | |
| L3.7.2.1 | Centre of mass inside the support polygon at 5° tilt. | analysis | passes | 1 |  |

### L1.8 The lid is a separate body held by four M3 screws

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Base and lid are separate bodies, one shell each, not interpenetrating. | analysis | BASE 1 shell; LID 1 shell; BASE ∩ LID ≤ 1.0 mm³ | 3 | |
| L3.8.1.1 | Shells per body and closed interpenetration. | analysis | 1; 1; ≤ 1.0 mm³ | 3 | G1 |
| L2.8.2 | A lip locates the lid with a sliding fit. | inspection | lip engagement ≥ 2.0; clearance 0.15–0.35 per side on all locating faces | 2 | |
| L3.8.2.1 | Lip-to-wall gap on all locating faces. | inspection | 0.15 ≤ g ≤ 0.35 | 2 |  |
| L3.8.2.2 | Lip engagement depth. | inspection | ≥ 2.0 | 1 |  |
| L2.8.3 | Four screws in tabs outside the cavity. | inspection | count = 4, two on each long side, axis 3.5–5.0 beyond the wall's outer face; pilot Ø 2.4–2.6, depth ≥ 6.0; lid hole Ø 3.4 ± 0.1, coaxial ≤ 0.3; pair spacing along X ≥ 25.0 | 3 | |
| L3.8.3.1 | Number and position of lid screws. | inspection | 4; as L2 | 3 |  |
| L3.8.3.2 | Pilot diameter and depth. | inspection | 2.4 ≤ Ø ≤ 2.6; depth ≥ 6.0 | 3 |  |
| L3.8.3.3 | Lid holes coaxial with the pilots. | inspection | Ø 3.3–3.5; offset ≤ 0.3 | 2 |  |
| L3.8.3.4 | Screw axes outside V-CAVITY; driver columns clear. | analysis | axis ≥ 1.0 outside the cavity; clear_of(ALL, V-DRIVER-j, 0.0) | 2 |  |
| L2.8.4 | The seam is tight. | inspection | seam gap ≤ 0.5; step between lid and base outer faces ≤ 0.5 | 1 | |
| L3.8.4.1 | Seam gap and flushness. | inspection | ≤ 0.5; ≤ 0.5 | 1 |  |

### L1.9 The box is closed except for the USB opening, the LED holes, the screw holes and the ear slots

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The only openings are the listed ones. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into V-CAVITY, other than the LED holes and the screw holes | 2 | |
| L3.9.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 |  |
| L2.9.2 | Wall, floor and lid thickness. | inspection | each 2.0–4.0 (median over the wall, away from features) | 2 | |
| L3.9.2.1 | Side wall, end wall, floor and lid plate thickness. | inspection | 2.0 ≤ t ≤ 4.0 | 2 |  |
| L2.9.3 | Material round every opening; walls join the floor. | analysis | min ligament ≥ 1.5; wall-to-floor contact ≥ 90% | 1 | |
| L3.9.3.1 | Ligament per opening and wall-to-floor contact. | analysis | ≥ 1.5; ≥ 90% | 1 |  |

### L1.10 Printable on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Each body is one manifold shell. | analysis | 1 shell each; manifold3d accepts it | 3 | |
| L3.10.1.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.10.2 | No unsupported overhang in the declared orientations. | analysis | 0 offending faces (area > 1 mm²) steeper than 45° from vertical, except round holes Ø ≤ 12 in vertical walls, bridges ≤ 15 and downward steps ≤ 1.0 (A7) | 2 | |
| L3.10.2.1 | Overhang and bridge scan per body. | analysis | as L2 | 2 |  |
| L3.10.2.2 | Bed contact per body. | analysis | ≥ 50% of the plan bounding box | 1 |  |
| L2.10.3 | Feature size and build volume. | analysis | min thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 | |
| L3.10.3.1 | Thin-feature scan. | analysis | ≥ 0.8 | 1 |  |
| L3.10.3.2 | Bounding box per body. | inspection | ≤ 200 per axis | 1 |  |

### L1.11 Within a size limit

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Size limit. | inspection | X ≤ 125.0, Y ≤ 50.0, Z ≤ 26.0 (domes excluded); X > Y | 1 | |
| L3.11.1.1 | Assembly bounding box. | inspection | as L2 | 1 |  |

### L1.12 The delivered package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds `base.stl`, `lid.stl` (closed pose, box frame, mm), the `.scad` source, `layout.json` and the agent's report. | inspection | all present and readable | 3 | |
| L3.12.1.1 | Files present and parse; STLs in mm: largest bounding-box axis within 20–200. | inspection | true | 3 | G0 |
| L2.12.2 | The agent's report agrees with the judge. | analysis | every clear_of / inside / distance number reported: pass/fail the same and \|d_agent − d_judge\| ≤ 0.10 | 1 | |
| L3.12.2.1 | Self-report against the judge. | analysis | 100% within 0.10 | 1 |  |

---

## 5. Counts and gates

L1: 12. L2: 34. L3: 57.

Gates (a failing gate makes the design WRONG regardless of score):

- **G0** package present and readable: L3.12.1.1
- **G1** two separate manifold bodies: L3.8.1.1, L3.10.1.1
- **G2** four pads and the board's keep-outs clear: L3.2.1.1, L3.2.3.1, L3.2.3.2
- **G3** micro-USB plug seats: L3.4.1.1
- **G4** two ear slots 100.0 ± 0.2 apart with at least 3.0 to every edge: L3.6.1.1, L3.6.1.2, L3.6.3.1, L3.6.3.2
- **G5** three LED holes, domes flush, flanges captured: L3.5.1.1, L3.5.1.2, L3.5.2.1, L3.5.3.1
- **G6** antenna keep-out free: L3.3.1.1, L3.3.2.1

---

## 6. Feasibility

A concrete design exists (box frame, Z = 0 at the PCB bottom, mm; every number is arithmetic-checked):

- **Cavity:** inner X −1.5 to 63.0 (64.5), Y −0.5 to 28.4 (28.9); walls 2.5, so outer X −4.0 to 65.5 (69.5), Y −3.0 to 30.9 (33.9). Floor 3.0: top Z −3.5, back face Z −6.5. Rim (seam) Z 12.5; lid plate Z 12.5 to 15.5.
- **Board:** edges 0.5 from the long walls; receptacle front X −1.0 is 0.5 from the −X wall (inner −1.5); PCB end at X 54.4 is 8.6 from the +X wall (inner 63.0): the antenna zone (X 48.4 to 62.4) lies inside the cavity with 0.6 spare.
- **Pads:** four, 2.0 × 6.0 (12 mm²): X 0.6 to 2.6 and 52.0 to 54.0, Y 1.0 to 7.0 and 20.9 to 26.9, tops at Z 0 (the PCB bottom). Header bodies start at X 3.07 and end at 51.33: gaps 0.47 and 0.67. Floor top −3.5 is 0.5 below the tails (Z −3.0). Two stops at X 54.9 to 56.9 (0.5 from the PCB end), 3.0 wide, up to Z 0.8.
- **USB opening:** in the −X wall (X −4.0 to −1.5), centre (Y 13.95, Z 3.05), nominal 11.0 × 8.0 (band 10.6 × 7.6 to 13.0 × 10.0): bottom Z −0.95 is 2.55 above the floor top, top Z 7.05 is 5.45 below the seam. The overmold face (X −2.5) is inside the wall, so the overmold enters 1.5 and the plug seats.
- **Header pins** top at Z 10.1; the seam/ceiling at 12.5 leaves 2.4 ≥ 0.3.
- **LEDs:** holes Ø5.3 at X 12.0, 22.0, 32.0, Y 13.95 (pitch 10.0). Collars OD 9.0 from the lid underside (Z 12.5) down to Z 6.0; seat Z 6.9 (flange 6.9 to 7.9 in a Ø6.1 pocket 1.2 deep, Z 6.7 to 7.9, so the flange floats 0.2 above the lip), through hole Ø5.3 from the shoulder at Z 7.9 to the lid top: 7.6 long, equal to the lens above the flange, so the dome top (6.9 + 8.6 = 15.5) is flush with the lid top (15.5). Snap lip Z 6.0 to 6.7 (0.7 thick), opening Ø5.4, with 3 slits. Collar bottom Z 6.0 is 0.8 above the component keep-out top (5.2). Flange overlap (5.8 − 5.3) / 2 = 0.25 per side. The collars' plan (Y 9.45 to 18.45) stays clear of the header rows (Y ≤ 2.52 and ≥ 25.38, 6.9 away) and X ≤ 36.5 < 48.4; each LED axis is 11.4 from the header-pin keep-outs (≥ 4.5) and 16.4 from the antenna zone.
- **Ears:** the box centre is X 30.75, so slot centres at X −19.25 and 80.75 (100.0 apart); stadium Ø4.5, centre-line 4.0 along X; countersink Ø8.4 (90°, depth 1.95, ear 4.0 thick: 2.05 land) so its outline spans X −25.45 to −13.05 and 74.55 to 87.15. Ears Z −6.5 to −2.5, Y 6.45 to 21.45 (15.0 wide, centred on 13.95), outer edges at X −28.75 and 90.25: countersink to the free edge 3.3, to the box wall 9.05 (−13.05 to −4.0; 74.55 to 65.5), across Y (15.0 − 8.4) / 2 = 3.3. Ear-to-wall contact 15.0 × 4.0 = 60 mm².
- **Lid screws:** four tabs on the long walls at X 15.0 and 50.0, axis 3.5 outside the wall (Y −6.5 and 34.4), tabs 8.0 × 7.0, pilots Ø2.5 × 8.0 deep from the rim; lid tabs 3.0 thick, holes Ø3.4; M3 × 10: engagement 10.0 − 3.0 = 7.0 ≥ 6.0. Hole edge to tab edge 3.5 − 1.7 = 1.8 ≥ 1.5.
- **Size:** X −28.75 to 90.25 = 119.0, Y −10.0 to 37.9 = 47.9, Z −6.5 to 15.5 = 22.0: within 125 × 50 × 26.
- **Print:** base back-face down (floor, ears and tabs flat; the USB opening's 11.0 top edge is a bridge ≤ 15); lid outer face down (plate and tabs flat, collars rising; the shoulder and lip are 0.4 and 0.35 steps).

The request, the L1s and the catalogue (`esp32_devkitc_v4`, `led_5mm`, `plug_microusb_b`, `screw_m3_selftap`) agree.
---

## 7. Grading procedure (design-specific rubric)

`benchmarks/generalize/rubric.md` (the generic rubric) did not exist when this file was written,
so the procedure is given here. When that file exists it governs the procedure and this section
governs only the numbers: **requirements numbers beat `part.json` numbers, and this section beats the
generic rubric where they differ.** The recipes for loading, `clear_of`, `inside`, apertures,
thicknesses, overhangs and bed contact are those of `benchmarks/enclosure/rubric.md` section 3
(Python at `/Users/robinonsay/python/llm-bt/venv/bin/python`, `trimesh`, `manifold3d`; count shells
with `manifold3d` `decompose()`, not `trimesh.split()`).

### 7.1 Inputs

STLs of every printed body in the assembly pose (mm), the `.scad` source (for naming features,
never for measuring), the declared layout file (`layout.json`: the pose of each catalogue part
and each body's print orientation) and the agent's own clearance report (graded only by the
evidence L3, never trusted elsewhere). The judge also gets `requirements.md` and `parts/*/part.json`
and nothing from the agent's code or transcript. The judge never opens `benchmarks/heldout.json`.

### 7.2 Procedure

1. **Package gate.** The listed files exist and load; otherwise stop with DOES NOT MEET and one
   defect on the package L3.
2. **Units.** Each body's largest bounding-box axis must be of the order stated in the package L3;
   if it looks like inches or metres record a defect and do not rescale silently.
3. **Normalise the frame.** Put the box in the box frame (1.1): back face lowest, the USB-opening end wall at −X. Rotations by multiples of 90° and mirroring only; record the transform.
4. **Build the references independently** from `part.json` and section 2 of this file at the
   declared layout (or the default layout where this file gives one), then run the sanity checks
   R1..Rn of section 2. A failing sanity check is fixed before grading.
5. **Run every applicable L3** with Python. Record measured value, limit, margin (measured minus
   limit, signed so that negative = fail) and PASS / FAIL / UNVERIFIED / N/A. **UNVERIFIED counts as
   FAIL.** N/A only for physical tests (unless a print was made).
6. **Look at the renders** after measuring, to confirm where a failure is and to catch defects
   no L3 covers (report those as observations; they do not change the verdict).
7. **Decide** and **report**.

### 7.3 Verdict classes

Gates: G0 package present and readable; G1 two separate manifold bodies; G2 four pads and the board's keep-outs clear; G3 micro-USB plug seats; G4 two ear slots 100.0 ± 0.2 apart with at least 3.0 to every edge; G5 three LED holes, domes flush, flanges captured; G6 antenna keep-out free.

| Class | Rule |
|---|---|
| **WRONG** | any gate fails |
| **MINOR** | no gate fails, but some weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |
| **MEETS** | CORRECT and every applicable non-physical L3 of weight 1 and 2 passes (the loop's zero-error state) |

Anything that is not MEETS is DOES NOT MEET. Also report the weighted score Σ(weight × pass) /
Σ(weight) over applicable L3s, and the worst normalised margin among weight-3 L3s (margin divided
by the criterion's tolerance or, for one-sided limits, by 0.5 mm).

Precedence:
- A functional check outranks the size check that serves it (plug seats, bolt reaches, part fits
  beat opening size and wall size), as long as the size check still passes on its own numbers.
- **Designed contact is not interference** (section 1.3). Only penetration above 0.01 mm³ counts for the listed pairs.
- The numbers in this file are authoritative. If `parts/*/part.json` disagrees, build the reference from this file and record a defect on the L3 that the stale catalogue data breaks, with `where` = the part.json field.
- Fixed decisions (section 3.2) admit no alternative. Any unlisted alternative is graded on the default numbers and noted as an observation.
- Never relax a criterion, never round in the design's favour beyond ε, never infer a pass from a render.

### 7.4 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first (gates, then weight 3, 2, 1).
Each entry has: `req` (L3 with its L2 and L1), `status`, `body`, `feature` (by function and, if
it exists, by its SCAD name), `face` (surface with its outward normal), `location` (coordinates in
mm in the normalised frame, a point or a box `[xmin, ymin, zmin]–[xmax, ymax, zmax]`),
`measured` / `limit` / `margin` with units, `reference` (the reference model or envelope and its
datum), `render` (which view and where in the image), `evidence` (saved file, e.g. the
intersection solid `defect_<L3>.stl`) and `needed` (the geometric change that would make the
check pass, as numbers, never as a design instruction). Coordinates come from the measurement,
not from the SCAD source. Group L3s that fail for one geometric reason under the first and list
the rest in `also_fails`, keeping every L3 id. Keep observations separate from defects. Save the
report as `judge.md` and `defects.json`.

### 7.5 Measured-values table (always filled in, pass or fail)

| Quantity | Limit | Measured |
|---|---|---|
| Pad count, area, top spread (L3.2.1.x) | 4; ≥ 10 mm²; ≤ 0.10 | |
| Lateral clearance to the board, four sides (L3.2.2.1), mm | 0.2–1.0 | |
| Top keep-out d (lid); tail zone d; pad height (L3.2.3.x), mm | ≥ 0.30; ≥ 0.0; 3.3–6.0 | |
| Antenna zone penetration; free length beyond the PCB (L3.3.x) | ≤ 0.01 mm³; ≥ 8.0 mm | |
| USB plug d; opening W × H (L3.4.x), mm | ≥ 0.30; 10.6 × 7.6 to 13.0 × 10.0 | |
| LED holes: count; Ø; dome flush Δ; flange overlap (L3.5.x), mm | 3; 5.2–5.4; ±0.3; ≥ 0.2 | |
| Ear slots: count; centre distance (L3.6.1.x), mm | 2; 100.0 ± 0.2 | |
| Slot width × length; countersink Ø, angle (L3.6.2.x), mm | 4.5 ± 0.15 × 4.0 ± 0.3; 8.4 ± 0.3, 90° ± 5° | |
| Countersink to ear edge; to box wall (L3.6.3.x), mm | ≥ 3.0; ≥ 3.0 | |
| Back-face flatness; ear coplanarity (L3.7.1.x), mm | ≤ 0.3; ≤ 0.2 | |
| Lip gap per side; engagement (L3.8.2.x), mm | 0.15–0.35; ≥ 2.0 | |
| Lid screws: count; pilot Ø, depth; lid hole Ø (L3.8.3.x), mm | 4; 2.4–2.6, ≥ 6.0; 3.4 ± 0.1 | |
| Opening count; wall thickness (L3.9.x), mm | listed only; 2.0–4.0 | |
| Shells; overhang patches; bed contact (L3.10.x) | 1 / 1; 0; ≥ 50% | |
| Envelope X × Y × Z (L3.11.1.1), mm | ≤ 125 × 50 × 26 | |
| Self-report agreement (L3.12.2.1) | 100% within 0.10 | |

---

## 8. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 (`design.json`) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1–L2.1.3 | L3.1.1.1, L3.1.1.2, L3.1.2.1, L3.1.3.1 | L1.1 | inspection | "ESP32 enclosure", "Three 5 mm LEDs shine through the lid" |
| L1.2 | Board support and keep-outs | L2.2.1–L2.2.3 | L3.2.1.1, L3.2.1.2, L3.2.1.3, L3.2.2.1, L3.2.2.2, L3.2.3.1, L3.2.3.2, L3.2.3.3 | L1.2 | analysis | "ESP32 enclosure" (a board with no mounting holes) |
| L1.3 | Antenna | L2.3.1–L2.3.2 | L3.3.1.1, L3.3.2.1, L3.3.2.2 | L1.3 | analysis | "ESP32" (a board with a PCB antenna) |
| L1.4 | USB access | L2.4.1–L2.4.3 | L3.4.1.1, L3.4.2.1, L3.4.3.1 | L1.4 | test | "micro-USB" (the board's only connector) reachable with the lid on |
| L1.5 | LED light pipes | L2.5.1–L2.5.4 | L3.5.1.1, L3.5.1.2, L3.5.2.1, L3.5.3.1, L3.5.3.2, L3.5.3.3, L3.5.4.1, L3.5.4.2 | L1.5 | inspection | "the LEDs sit flush with the outside and must not fall out" |
| L1.6 | Wall mounting | L2.6.1–L2.6.4 | L3.6.1.1, L3.6.1.2, L3.6.2.1, L3.6.2.2, L3.6.2.3, L3.6.3.1, L3.6.3.2, L3.6.4.1, L3.6.4.2 | L1.6 | inspection | "two mounting ears taking 4.2 mm countersunk wood screws, 100 mm apart", "leave at least 3 mm to the box edge" |
| L1.7 | Flat back | L2.7.1–L2.7.2 | L3.7.1.1, L3.7.1.2, L3.7.2.1 | L1.7 | inspection | "wall-mounted" |
| L1.8 | Lid | L2.8.1–L2.8.4 | L3.8.1.1, L3.8.2.1, L3.8.2.2, L3.8.3.1, L3.8.3.2, L3.8.3.3, L3.8.3.4, L3.8.4.1 | L1.8 | inspection | "The lid" (a removable lid) |
| L1.9 | Protection | L2.9.1–L2.9.3 | L3.9.1.1, L3.9.2.1, L3.9.3.1 | L1.9 | analysis | "enclosure" |
| L1.10 | Printable | L2.10.1–L2.10.3 | L3.10.1.1, L3.10.2.1, L3.10.2.2, L3.10.3.1, L3.10.3.2 | L1.10 | analysis | "printed ... back face down" |
| L1.11 | Size | L2.11.1–L2.11.1 | L3.11.1.1 | L1.11 | inspection | (implied) |
| L1.12 | Evidence | L2.12.1–L2.12.2 | L3.12.1.1, L3.12.2.1 | L1.12 | inspection | (not the owner's words; needed by the judge) |

---

## Audit

Adversarial audit (second agent). Recomputed: header positions from the part (X 3.07 to 51.33, rows Y −0.02 to 2.52 and 25.38 to 27.92), keep-outs (component side Z to 5.2, antenna zone X 48.4 to 62.4 and Z to 9.7, header pins to 10.1, tails to −3.0), USB plug stack (tip X 4.0, face −2.5, wall −4.0 to −1.5), cavity and outer sizes (64.5 x 28.9 inner, 69.5 x 33.9 outer), ear and slot geometry (centres −19.25 and 80.75, countersink outlines, edge distances 3.3 and 9.05), tabs and screws (engagement 7.0, edge 1.8), LED stack (dome top 15.5 equals lid top) and the bounding box 119.0 x 47.9 x 22.0. Parts load (`esp32_devkitc_v4`, `led_5mm`, `plug_microusb_b`; `screw_m3_selftap` is in the enclosure catalogue and its pilot 2.4 to 2.6, clearance 3.4, length 10.0, min engagement 6.0 agree with L3.8.3). L1 = 12, L2 = 34, L3 = 57 match section 5 and the traceability.

| # | Defect found | Fix |
|---|---|---|
| 1 | Feasibility put the LED snap lip at Z 6.1 to 6.9 (0.8) and the flange pocket 1.2 deep: the stack does not close (lip top 6.9 and pocket floor at 7.9 give 1.0; the 1.2 pocket needs the lip top at 6.7). | Lip Z 6.0 to 6.7 (0.7, band 0.6 to 1.0), pocket Z 6.7 to 7.9 (1.2, band 1.0 to 1.3), collar bottom 6.0 (0.8 above the keep-out). Pocket depth is now defined (lip top face to shoulder). All gates still pass; dome flush unchanged. |
| 2 | Feasibility quoted the +Y header row start as 26.38; the part gives 25.38. | Corrected (the margin to the collars is 6.9, still clear). |
| 3 | L2.1.3 LED window (Y 8.0 to 19.9, X 6.0 to 43.0) was an arbitrary hidden range duplicating L2.5.4. | Replaced by the derived rule: pitch >= 10.0 and each axis >= 4.5 in plan from the header-pin and antenna keep-outs (3.85 collar radius minimum + 0.3). Default layout satisfies it with 11.4 and 16.4. |
| 4 | FD7 seam band 10.6 to 13.5 contradicted the 0.3 lid clearance of L3.2.3.1 and was tighter than the size limit needs. | Band 10.4 to 16.5, with the reasons. |
| 5 | A7 said the collar shoulder is a 0.4 step overhang; in the lid-down print it recedes outward and is not an overhang (the lip, 0.35, is the exempt step). | Text corrected; no L3 change. |
| 6 | Numbers the judge uses but the agent was never told: LED hole 5.2 to 5.4, flange overlap, flush 0.3, snap-lip opening and slit count, LED pitch (G5); USB 0.3 clearance and 1.5 ligament (G3); pad area, wall and stop clearances (G2); slot Ø4.5 stadium 4.0, countersink Ø8.4, ear 3.5 to 5.0 (G4); screw axis, pilot, lid hole, lip fit; antenna zone height 5.0. | Added to L1.2, L1.3, L1.4, L1.5, L1.6, L1.7, L1.8, L1.9 in `design.json`. No L3 number changed. |

Noted, not changed: header body A starts 0.02 below the PCB edge (part datum), harmless against the 0.5 wall clearance; the 4.2 mm countersunk screw has no catalogue part (numbers are in the request and A4); the 15 mm antenna guidance of Espressif is not used (the part and the request say 8 mm).
