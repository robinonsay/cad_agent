# G01 Arduino Nano box with snap lid: requirements (L1 / L2 / L3)

Design G01 is a small Arduino Nano box with a snap lid. It is graded on the board's placement and
support, on the mini-USB plug that must seat through one short end, on three LEDs in the lid, and
on a screwless snap closure with a strain limit, plus the usual printability and evidence rows.
It is a training design for the generalisation set; the method (declared layout, catalogue parts placed by
datums, interference and clearance against swept envelopes, numbers only in the request and the
catalogue) is the same as the enclosure benchmark.

**Request (as given to the agent):** I need a small box for an Arduino Nano (board 45 x 18 mm) that I will leave on a shelf. The Nano's mini-USB port has to be reachable through one short end of the box with the lid on, so I can plug a cable in. Three 5 mm status LEDs, separate parts wired to the Nano, sit in the top face of the lid and must be visible from outside. The lid snaps on without screws, so the box has no fasteners at all. The Nano keeps its header pins pointing down (they stick out of the underside), so the board has to stand clear of the floor. The base is printed flat on the bed in PLA, with no supports.

**Plan brief (verbatim):** "I need a small box for an Arduino Nano that I will leave on a shelf. The mini-USB port has to be reachable through one short end with the lid on, and three 5 mm status LEDs on the top face should be visible. The lid snaps on without screws and the base is printed flat in PLA."

**Split:** train. **Family:** electronics_enclosure. **Capabilities exercised:** datum_placement, plug_envelope_opening, snap_fit, window, standoffs.

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

- **Box frame (all tables below):** the Nano's own frame: X along the board's 45 mm side with the
  mini-USB end at **−X**, Y along the 18 mm side, **Z = 0 at the PCB's underside**, Z up. The PCB occupies Z 0 to
  1.6 and X 0 to 45.0, Y 0 to 18.0. A box delivered mirrored or rotated is normalised into this frame before grading (7.2 step 3): floor underside at the lowest Z, the end wall with the USB opening at −X; that is never penalised.
- **Part frames:** `arduino_nano` is placed with its own frame equal to the box frame (identity pose) unless the layout declares another; `led_5mm` (origin on the lens axis at the flange bottom plane, dome toward +Z) is placed at each declared LED position with its axis along +Z; `plug_miniusb_b` (origin at the tip, body runs along +X, inserted along −X) is placed at full mate by the grader.

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

- the board's underside resting on the post tops (inside the Ø4.0 seat column on each hole)
- a locating pin in its PCB hole
- the LED flange against the lid underside, the lens in its hole (only the radial play of L2.6.1 applies to the lens)
- the lid lip against the base's locating faces, at the fit of L2.8.2
- the lid resting on the base rim
- a snap hook in its groove, at the clearance and engagement of L2.7.x

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` in `benchmarks/generalize/parts/<id>/` (`arduino_nano`, `led_5mm`, `plug_miniusb_b`). These are the only places target-specific part numbers may live.
- **envelope**: a keep-out or access volume generated by Python from datums (offsets, sweeps). Never drawn by hand.
- **computed**: derived from the delivered STLs (cavity, apertures, hook geometry).

### 2.2 Reference models (M-)

Default layout (assumption A1) when a design declares none: the Nano at the identity pose of the box frame, LEDs at X = 12.0, 22.0, 32.0, Y = 9.0 on the lid.

| Name | What | Source | Size and default position (box frame, mm) | Datums |
|---|---|---|---|---|
| **M-NANO** | Arduino Nano with mini-USB receptacle and underside headers | catalogue `arduino_nano` | PCB 45.0 × 18.0 × 1.6, Z 0 to 1.6; receptacle 9.0 (X) × 7.7 (Y) × 3.9 (Z) on top at X −0.7 to 8.3, Y 5.15 to 12.85, Z 1.6 to 5.5; header bodies on the underside, X 3.45 to 41.55, rows at Y 1.38 and 16.62 (bodies 2.54 wide), Z −2.5 to 0; four holes Ø1.7 at (0.9, 1.38), (44.1, 1.38), (0.9, 16.62), (44.1, 16.62) | `USB_MOUTH` (−0.7, 9.0, 3.55), `USB_AXIS` (−X), `HOLE_1..4`, `PCB_BOTTOM`, `PCB_TOP` |
| **M-TAILS** | the header pin tails | catalogue `arduino_nano` keep-outs `pin_tails_a/b` | the header footprint boxes, Z −8.5 to −2.5 (A2) | |
| **M-LED-k** (k = 1..3) | 5 mm LED | catalogue `led_5mm` | flange Ø5.8 × 1.0 (Z 9.0 to 10.0 at the default seat), lens Ø5.0 up to the dome top 8.6 above the seat | `AXIS`, `SEAT` (flange bottom), `PANEL_SEAT` (flange top), `DOME_TOP` |
| **M-PLUG-USB** | mini-USB B plug | catalogue `plug_miniusb_b` | shell 6.8 (Y) × 3.0 (Z), mated depth 6.9, exposed shell 1.5; overmold 11.0 (Y) × 8.0 (Z) × 20 long | `PLUG_TIP`, `PLUG_AXIS`, `OVERMOLD_FACE` |
| **RNA** | reference Nano assembly = M-NANO ∪ M-LED-1..3 | assembled | as above | all of the above |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Definition (default layout, box frame, mm) |
|---|---|---|
| **V-KO-TOP** | component keep-out above the board | board footprint X 0 to 45, Y 0 to 18, Z 1.6 to 6.6 (top parts 3.5 + 1.5 margin, A3) |
| **V-KO-BOT** | header and tail keep-out below the board | M-NANO header bodies ∪ M-TAILS, grown by 0.3 (the gap), Z −8.8 up to 0; the post columns (V-SEAT) are excluded |
| **V-SEAT-k** (k = 1..4) | where a post may touch the board | Ø4.0 column on `HOLE_k` (the part's keep-out diameter), from the floor up to Z = 0 |
| **V-PCB-EDGE** | lateral clearance zone of the board | M-NANO PCB ∪ headers ∪ receptacle (used with clearance 0.5 for the PCB, 0.3 for the receptacle) |
| **V-USB-PLUG** | mini-USB plug at full mate and its withdrawal path | M-PLUG-USB with its tip at `USB_MOUTH` X + 6.9 = X 6.2, shell out to X −2.2 (1.5 exposed), overmold 11.0 × 8.0 from X −2.2 outward to X −42.2 |
| **V-LED-VIEW-k** | the LED's view zone | the part's `view_zone`: Ø5.0 × 2.0 above `DOME_TOP` |
| **V-INSTALL** | board installation path | the RNA's board silhouette swept +Z from its seat to 5.0 above the base rim (lid off), minus the V-SEAT columns |
| **V-CAVITY** | the closed box's inner void | computed: convex hull of (BASE ∪ LID, closed) minus (BASE ∪ LID), the component containing the board centroid |
| **V-AP-USB** | the openings actually present in the −X end wall | computed: wall slab between the inner and outer end faces minus (BASE ∪ LID) |
| **V-AP-OTHER** | every other opening | computed: every through path from outside into V-CAVITY, as connected regions |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-NANO | units | PCB 45.0 × 18.0 ± 0.2 |
| R2 | M-NANO | hole pattern | Ø1.7 ± 0.1; 43.2 × 15.2 ± 0.1 centre pitch |
| R3 | M-NANO | USB direction | `USB_AXIS` along −X |
| R4 | M-LED | size | flange Ø5.8 ± 0.1, lens Ø5.0 ± 0.1, height 8.6 ± 0.3 |
| R5 | M-PLUG-USB | overmold | 11.0 × 8.0 ± 0.2 |
| R6 | RNA | models do not collide | intersection ≤ 0.01 mm³ |

**Seating rule.** The RNA is placed at the pose declared in `layout.json`. The grader verifies: `PCB_BOTTOM` lies on the post tops (≤ 0.10) and `HOLE_1..4` are coaxial with the locating pins (residual ≤ 0.20), and each LED's `PANEL_SEAT` lies on the lid underside (≤ 0.10) with its axis on the hole axis (≤ 0.15). If the declaration is missing or fails, the board is seated by the post fit instead and the L3 rows for the pose fail.
---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (with uncertainty)

Each line gives the value chosen and why. Robin may correct any of them; a correction changes this file and the catalogue, and earlier scores become stale.

| # | Question | Value chosen | Why and uncertainty |
|---|---|---|---|
| A1 | Where do the board and LEDs sit? | Nano at the identity pose (X 0–45, Y 0–18). LEDs in a row over the board footprint, pitch ≥ 9.0, each axis ≥ 4.0 from the cavity edge; default X = 12.0, 22.0, 32.0 at Y = 9.0. | The design chooses and declares; the default is used when none is declared. Uncertainty: the owner may want another order; not graded. |
| A2 | Header tails? | Pins as supplied: plastic body 2.5 under the board, pins 6.0 below that (tail to Z −8.5). | Stock Nano with pins pointing down; the catalogue `pin_tails` keep-outs. If the owner cuts them, standoffs may be shorter (not graded). Uncertainty ±1.5 on the tail length; the 0.3 gap covers 0.3 of it only. Measure the owner's board. |
| A3 | Clearance above the board? | The lid underside is at least 5.0 above the PCB top (V-KO-TOP 6.6 above the PCB bottom). | The tallest top part is the receptacle (3.9, top at 5.5) and the reset switch (3.5). 5.0 gives 1.5 above the reset switch, 1.1 above the receptacle top (5.5), and room for the LED flange (1.0) beneath the lid. |
| A4 | Mini-USB plug? | Overmold 11.0 × 8.0, shell 6.8 × 3.0, mated depth 6.9, 1.5 exposed shell. | `plug_miniusb_b`. Typical cables; measure the owner's. The end wall is 2.0 thick, so the overmold must enter the opening for the plug to seat. |
| A5 | Nano numbers? | PCB 45 × 18 × 1.6; holes Ø1.7 on 43.2 × 15.2 at 0.9 / 1.38 from the edges; receptacle 7.7 × 9.0 × 3.9 overhanging by 0.7. | The Arduino Nano datasheet and the catalogue. The overhang and the receptacle height are assumed (±0.5); clone boards differ. |
| A6 | LED numbers? | Lens Ø5.0, flange Ø5.8 × 1.0, height 8.6 to the dome. | `led_5mm`. The flange thickness is ±0.3, the height 8.4–9.0. The dome stands about 5.6 above the lid. |
| A7 | Printing? | FDM, PLA, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. Base: floor on the bed, open side up. Lid: outer face on the bed. A downward-facing step of at most 1.0 deep (a snap catch or a groove top) is not an overhang. | Common printers. The exemption covers the snap catches (0.8 deep) and the grooves. Sliding fit 0.15–0.35 per side. PLA allows 2% strain in a snap arm (1–3% in practice). |
| A8 | Wall thickness? | Walls, floor and lid plate 2.0–3.0. | Five perimeters at 0.4. Stiff enough for a shelf box and for the snap arms to bear on. |
| A9 | Maximum size? | Closed bodies at most 60 × 30 × 26 (X × Y × Z), excluding the LEDs' domes (L1.11 says so). | Stops oversized designs. A tight design is about 51 × 26 × 23. |
| A10 | Shelf use? | The box stands on its floor; no wall mount, no vents (the Nano draws well under 1 W). | The brief says 'on a shelf'. A vent would add an opening (not wanted). |

### 3.2 Fixed decisions (one choice, no alternatives graded)

| # | Ambiguity | Decision | Reason |
|---|---|---|---|
| FD1 | How is the board held? | On **four posts** under the mounting holes: post Ø3.2 (3.0–4.0), top at the PCB bottom, each with a **locating pin** Ø1.5 (1.4–1.6) rising to Z 1.4 (1.2–1.6) through the PCB's Ø1.7 hole (radial play 0.1). | The Nano's holes are 0.9 from the short edges: a boss as wide as a standoff would cross the board edge, so a pin and a small post are used. The part's notes suggest posts through the holes. |
| FD2 | Where is 'the top face'? | The **lid's outer (upper) face**, which is parallel to the board. | The brief says three LEDs on the top face; the board lies flat so the top is the lid. |
| FD3 | How are the LEDs mounted? | Separate 5 mm LEDs, flange against the lid **underside**, lens through a hole Ø5.3 (5.2–5.4) in the lid, dome protruding. Flange overlap on the hole (5.8 − 5.3)/2 = 0.25 ≥ 0.2. | The catalogue LED has a flange; this is the usual panel mounting. The leads are wired to the Nano (not modelled). |
| FD4 | What snap? | **Cantilever hooks on the lid's skirt** on the two long sides, engaging grooves in the base's outer walls: at least 2 hooks on each long side (4 in the sketch), 12.0 arm length, 1.5 arm thickness, 0.8 engagement. No hooks at the short ends (the USB end has the opening). | The simplest printable snap that has a strain limit; hooks on the long sides leave both end walls plain. |
| FD5 | Where is the seam? | At the base rim, Z = **10.0** in the sketch (the base wall top; band 9.35–12.0). | The USB opening must stay in the base wall with 1.5 of material above it (opening top at Z 7.85 + 1.5 = 9.35). |
| FD6 | Print orientations? | Base: floor underside on the bed. Lid: outer face on the bed (plate down, skirt and lip up). Declared in `layout.json`. | Matches 'the base is printed flat'. |

---

## 4. Requirements tree

### L1.1 The Nano and the three LEDs are laid out by their datums

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: the Nano's pose, each LED's position, and each body's print orientation. | inspection | `layout.json` present, parses, names `arduino_nano` and three `led_5mm` | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 |  |
| L3.1.1.2 | The declared pose verifies under the seating rule. | analysis | PCB bottom on the post tops ≤ 0.10; hole residual ≤ 0.20; LED seat on the lid underside ≤ 0.10 | 3 |  |
| L2.1.2 | The mini-USB port faces the −X short end. | inspection | `USB_AXIS` within 1.0° of −X; `USB_MOUTH` X in [−1.2, −0.2] | 3 | |
| L3.1.2.1 | USB axis direction and mouth position in the declared layout. | inspection | ≤ 1.0°; X in [−1.2, −0.2] | 3 |  |
| L2.1.3 | The LEDs are in a row on the lid with room for each. | inspection | three LED axes in a row over the board footprint (X 0 to 45, Y 0 to 18); pitch between neighbours ≥ 9.0; each axis ≥ 4.0 from the cavity edge (flange radius 2.9 + lip gap 0.2 + minimum lip thickness 0.8 = 3.9) | 2 | |
| L3.1.3.1 | LED axis positions and pitch. | inspection | as L2 | 2 |  |

### L1.2 The board fits with at least 0.5 mm clearance at its edges

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | No printed body comes within 0.5 of the PCB, except the post tops. | analysis | clear_of(ALL, M-NANO PCB minus V-SEAT columns, 0.5) | 3 | |
| L3.2.1.1 | PCB-edge and PCB-face clearance, all four edges and both faces. | analysis | d ≥ 0.50 | 3 | G2 |
| L2.2.2 | The receptacle and headers lie inside the cavity. | analysis | inside(M-NANO receptacle ∪ headers, V-CAVITY, 0.3) | 3 | |
| L3.2.2.1 | Receptacle and header bodies inside the cavity. | analysis | d ≥ 0.30 | 3 |  |
| L3.2.2.2 | Inner X length at board height (end wall to end wall). | inspection | ≥ 46.5 (0.3 receptacle clearance + 0.7 overhang + 45.0 + 0.5 far-end PCB clearance, recomputed from the declared layout) | 2 |  |

### L1.3 The board is held on four posts with locating pins

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Four posts under the holes. | inspection | count = 4; each axis within 0.25 of its `HOLE_k`; post Ø 3.0–4.0; tops coplanar within 0.10 | 3 | |
| L3.3.1.1 | Number of posts. | inspection | count = 4 | 3 | G2 |
| L3.3.1.2 | Post axes against the Nano's `HOLE` datums. | analysis | each offset ≤ 0.25 | 3 |  |
| L3.3.1.3 | Post outer diameter and top-plane spread. | inspection | 3.0 ≤ Ø ≤ 4.0; spread ≤ 0.10 | 2 |  |
| L2.3.2 | Each post has a locating pin that engages the hole. | inspection | pin Ø1.4–1.6, top at Z 1.2–1.6, axis within 0.10 of the hole | 3 | |
| L3.3.2.1 | Pin diameter, height and coaxiality with the hole. | inspection | Ø 1.4–1.6; top Z 1.2–1.6; offset ≤ 0.10 | 3 |  |
| L2.3.3 | Posts are fused to the floor and the base is one body. | analysis | contact per post ≥ 8 mm²; BASE one connected body | 2 | |
| L3.3.3.1 | Post-to-floor contact and base connectivity. | analysis | ≥ 8 mm² each; 1 shell | 2 |  |

### L1.4 The parts on the board clear the box above and below

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Lid closed: no body in the component zone above the board. | analysis | clear_of(ALL, V-KO-TOP, 0.0) | 3 | |
| L3.4.1.1 | Top keep-out clear. | analysis | d ≥ 0.0 | 3 | G2 |
| L3.4.1.2 | Lid underside minus PCB top. | inspection | ≥ 5.0 | 2 |  |
| L2.4.2 | No body in the header and tail zone. | analysis | clear_of(ALL, V-KO-BOT, 0.0), the posts excluded | 3 | |
| L3.4.2.1 | Bottom keep-out clear. | analysis | d ≥ 0.0 | 3 | G2 |
| L3.4.2.2 | Floor top to PCB bottom (post height). | inspection | 8.8 ≤ h ≤ 10.5 | 2 |  |

### L1.5 A mini-USB plug seats through the −X end wall with the lid on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The plug reaches full mate and can be withdrawn. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 | |
| L3.5.1.1 | USB plug envelope clear. | test | d ≥ 0.30 | 3 | G3 |
| L2.5.2 | The opening is not oversized. | analysis | inside(V-AP-USB, V-USB-PLUG offset by 1.5, 0.0): opening ≥ 11.6 × 8.6 and ≤ 14.0 × 11.0 | 2 | |
| L3.5.2.1 | Opening width × height and centre (box frame). | analysis | between 11.6 × 8.6 and 14.0 × 11.0; centre within 0.5 of Y 9.0, Z 3.55 | 2 |  |
| L2.5.3 | Exactly one opening in the −X wall, away from the seam. | inspection | V-AP-USB has 1 connected region; ligament to the seam, floor and corners ≥ 1.5 | 2 | |
| L3.5.3.1 | Opening count and ligament. | inspection | 1; ≥ 1.5 | 2 |  |

### L1.6 Three LEDs sit in the lid and are visible

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Three holes of the right size. | inspection | count = 3 in the lid top; inscribed Ø 5.2–5.4; axis within 0.15 of the LED axis | 3 | |
| L3.6.1.1 | Number of LED holes in the lid. | inspection | count = 3 | 3 | G4 |
| L3.6.1.2 | Hole inscribed diameter and axis offset to the declared LED. | inspection | 5.2 ≤ Ø ≤ 5.4; offset ≤ 0.15 | 3 | G4 |
| L2.6.2 | The flange is captured and the dome is clear. | analysis | flange overlap on the hole ≥ 0.2 per side; PANEL_SEAT within 0.10 of the lid underside; clear_of(ALL, V-LED-VIEW-k, 0.0) | 3 | |
| L3.6.2.1 | Flange overlap and seat on the lid underside. | analysis | ≥ 0.2 per side; ≤ 0.10 | 3 |  |
| L3.6.2.2 | View zones clear of every printed body. | analysis | penetration ≤ 0.01 mm³ | 2 |  |
| L2.6.3 | The LED model does not collide with the box. | analysis | M-LED-k ∩ (BASE ∪ LID) ≤ 0.01 mm³ outside the lens-in-hole play; clear_of(LED flange, V-KO-TOP ∪ M-NANO, 0.3) | 2 | |
| L3.6.3.1 | LED to box and board interference. | analysis | ≤ 0.01 mm³; flange ≥ 0.3 from the board's keep-out | 2 |  |

### L1.7 The lid snaps on without screws

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Snap hooks: count, placement and engagement. | inspection | hooks ≥ 4, at least 2 on each of the two long sides; each hook width ≥ 5.0; engagement 0.6–1.0; catch face 90° ± 10° to the pull direction; lead-in 30°–60° to the pull direction | 3 | |
| L3.7.1.1 | Number and placement of hooks. | inspection | ≥ 4; ≥ 2 on each long side; none at the USB end | 3 | G5 |
| L3.7.1.2 | Hook engagement (catch overlap) for every hook. | inspection | 0.6 ≤ y ≤ 1.0 | 3 | G5 |
| L3.7.1.3 | Catch-face and lead-in angles. | inspection | catch 80°–100°; lead-in 30°–60° | 2 |  |
| L2.7.2 | The arm will not yield. | analysis | strain ε = 1.5 · t · y / L² ≤ 0.02 for every arm (t thickness, y engagement, L free length) | 3 | |
| L3.7.2.1 | Arm thickness, free length and strain. | analysis | t 1.2–2.0; L ≥ 10.0; ε ≤ 0.02 | 3 |  |
| L3.7.2.2 | Each arm is isolated by slots on both sides. | inspection | slot width ≥ 0.8 | 2 |  |
| L2.7.3 | No fasteners. | inspection | 0 screws, 0 inserts, 0 holes for them in either body | 2 | |
| L3.7.3.1 | No screw holes or bosses for fasteners. | inspection | 0 | 2 |  |

### L1.8 The lid is a separate body that locates on the base

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Base and lid are separate bodies, one shell each, not interpenetrating. | analysis | BASE 1 shell; LID 1 shell; BASE ∩ LID ≤ 1.0 mm³ | 3 | |
| L3.8.1.1 | Shells per body and closed interpenetration. | analysis | 1; 1; ≤ 1.0 mm³ | 3 | G1 |
| L2.8.2 | A lip locates the lid with a sliding fit. | inspection | lip engagement ≥ 2.0; clearance 0.15–0.35 per side on all locating faces | 2 | |
| L3.8.2.1 | Lip-to-wall gap on all locating faces. | inspection | 0.15 ≤ g ≤ 0.35 | 2 |  |
| L3.8.2.2 | Lip engagement depth. | inspection | ≥ 2.0 | 1 |  |
| L2.8.3 | The seam is tight and flush. | inspection | seam gap ≤ 0.5; outer-face step between lid and base ≤ 0.5 at the ends (the skirt overlap on the long sides is the snap design) | 1 | |
| L3.8.3.1 | Seam gap and flushness at the short ends. | inspection | ≤ 0.5; ≤ 0.5 | 1 |  |

### L1.9 The box is closed except for the USB opening and the LED holes

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The only openings are the USB opening and the three LED holes. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into V-CAVITY, other than the three LED holes | 2 | |
| L3.9.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 |  |
| L2.9.2 | Wall, floor and lid thickness. | inspection | each 2.0–3.0 (median over the wall, away from features) | 2 | |
| L3.9.2.1 | Side wall, end wall, floor and lid plate thickness. | inspection | 2.0 ≤ t ≤ 3.0 | 2 |  |
| L2.9.3 | Material round every opening and each wall joins the floor. | analysis | min ligament ≥ 1.5; wall-to-floor contact ≥ 90% | 1 | |
| L3.9.3.1 | Ligament per opening and wall-to-floor contact. | analysis | ≥ 1.5; ≥ 90% | 1 |  |

### L1.10 Printable on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Each body is one manifold shell. | analysis | 1 shell each; manifold3d accepts it | 3 | |
| L3.10.1.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.10.2 | No unsupported overhang in the declared orientations. | analysis | 0 offending faces (area > 1 mm²) steeper than 45° from vertical, except round holes Ø ≤ 12 in vertical walls, bridges ≤ 15 and downward steps ≤ 1.0 (A7) | 2 | |
| L3.10.2.1 | Overhang and bridge scan per body. | analysis | as L2 | 2 |  |
| L3.10.2.2 | Bed contact per body (base floor; lid plate). | analysis | ≥ 50% of the plan bounding box | 1 |  |
| L2.10.3 | Feature size and build volume. | analysis | min thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 | |
| L3.10.3.1 | Thin-feature scan. | analysis | ≥ 0.8 | 1 |  |
| L3.10.3.2 | Bounding box per body. | inspection | ≤ 200 per axis | 1 |  |

### L1.11 A compact shelf box that stands flat

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Size limit. | inspection | X ≤ 60.0, Y ≤ 30.0, Z ≤ 26.0 (domes excluded, as in L1.11); X > Y | 1 | |
| L3.11.1.1 | Assembly bounding box. | inspection | as L2 | 1 |  |
| L2.11.2 | It stands on its floor. | analysis | flat underside (flatness ≤ 0.2); stable at 5° tilt | 1 | |
| L3.11.2.1 | Underside flatness and tilt stability. | analysis | ≤ 0.2; passes | 1 |  |

### L1.12 The delivered package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds `base.stl`, `lid.stl` (closed pose, box frame, mm), the `.scad` source, `layout.json` and the agent's report. | inspection | all present and readable | 3 | |
| L3.12.1.1 | Files present and parse; STLs in mm: largest bounding-box axis within 20–200. | inspection | true | 3 | G0 |
| L2.12.2 | The agent's report agrees with the judge. | analysis | every clear_of / inside / hook number reported: pass/fail the same and \|d_agent − d_judge\| ≤ 0.10 | 1 | |
| L3.12.2.1 | Self-report against the judge. | analysis | 100% within 0.10 | 1 |  |

---

## 5. Counts and gates

L1: 12. L2: 32. L3: 46.

Gates (a failing gate makes the design WRONG regardless of score):

- **G0** package present and readable: L3.12.1.1
- **G1** two separate manifold bodies: L3.8.1.1, L3.10.1.1
- **G2** board fits with clearance, four posts, keep-outs clear: L3.2.1.1, L3.3.1.1, L3.4.1.1, L3.4.2.1
- **G3** mini-USB plug seats: L3.5.1.1
- **G4** three LED holes seat the LEDs: L3.6.1.1, L3.6.1.2
- **G5** snap hooks hold the lid: L3.7.1.1, L3.7.1.2

---

## 6. Feasibility

A concrete design exists (box frame, Z = 0 at the PCB bottom, mm; every number is arithmetic-checked):

- **Cavity:** inner X −1.2 to 45.5 (46.7), inner Y −0.5 to 18.5 (19.0); walls 2.0, so outer X −3.2 to 47.5 (50.7), Y −2.5 to 20.5 (23.0). Floor 2.0: top Z −9.0, underside Z −11.0. Base rim (seam) Z 10.0.
- **Board:** PCB edge to side walls 0.5; USB end: receptacle front X −0.7, wall inner −1.2 (0.5); far end 45.0 to 45.5 (0.5).
- **Posts:** four Ø3.2 posts from Z −9.0 to 0 at the hole axes (0.9, 1.38) …; post height 9.0 (band 8.8–10.5); tails reach Z −8.5, floor top −9.0: gap 0.5 ≥ 0.3. Pins Ø1.5 to Z 1.4 in the Ø1.7 holes. Post to header body: 3.45 − (0.9 + 1.6) = 0.95. Post to wall: Y 1.38 − 1.6 = −0.22 vs wall −0.5: 0.28; X 0.9 − 1.6 = −0.7 vs −1.2: 0.5.
- **USB opening** in the −X wall (X −3.2 to −1.2), centre (Y 9.0, Z 3.55), 11.6 × 8.6 up to 14.0 × 11.0: with the nominal 12.0 × 9.0 the top at Z 8.05 leaves 10.0 − 8.05 = 1.95 ≥ 1.5 to the seam and the bottom at −0.95 is 8.05 above the floor top. The overmold face (X −2.2) is inside the wall thickness, so the overmold enters the opening 1.0 and the plug seats.
- **Lid:** plate Z 10.0 to 12.0 (2.0); lip down to Z 8.0 (engagement 2.0) at 0.2 per side inside the walls. Skirt on the two long sides, outside the base walls at a 0.2 gap, 1.5 thick, from Z 10.0 down to Z −2.0 (arm length 12.0). Hooks (4: two per side, 8.0 wide) protrude 1.0 at the tip into grooves of depth 0.8 in the base's outer walls: engagement 0.8, strain 1.5 × 1.5 × 0.8 / 12.0² = 0.0125 ≤ 0.02. Slots 1.0 wide isolate each arm.
- **LEDs:** holes Ø5.3 at X 12.0, 22.0, 32.0, Y 9.0 (pitch 10.0). Flange Z 9.0 to 10.0 against the lid underside, overlap 0.25 per side; flange bottom Z 9.0 is 9.0 − 5.1 = 3.9 above the component keep-out (top 5.1) and 2.4 above V-KO-TOP (6.6). Dome top Z 17.6: 5.6 above the lid.
- **Size:** lid X 50.7, Y 26.4 (skirt 22.0 + 2 × 0.2 + 2 × 1.5), Z −11.0 to 12.0 = 23.0: within 60 × 30 × 26.
- **Print:** base floor on the bed (open side up, no overhang but the USB opening's top edge: a 12.0 bridge ≤ 15 and the grooves' top faces, 0.8 deep steps); lid plate on the bed, skirt, lip and hooks up (catch faces are 0.8-deep steps).

The request, the L1s and the catalogue (`arduino_nano` 45 × 18 × 1.6, holes 1.7, tails 6.0, receptacle 7.7 × 3.9; `led_5mm` Ø5.0, flange Ø5.8 × 1.0, 8.6; `plug_miniusb_b` 11 × 8, 6.8 × 3.0, 6.9, 1.5) agree.
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
3. **Normalise the frame.** Put the box in the box frame (1.1): floor underside lowest, the USB-opening end wall at −X. Rotations by multiples of 90° and mirroring only; record the transform.
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

Gates: G0 package present and readable; G1 two separate manifold bodies; G2 board fits with clearance, four posts, keep-outs clear; G3 mini-USB plug seats; G4 three LED holes seat the LEDs; G5 snap hooks hold the lid.

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
| Board clearance to any surface (L3.2.1.1), mm | ≥ 0.5 | |
| Receptacle and headers in the cavity (L3.2.2.1), mm | ≥ 0.3 | |
| Post count; axis offset; Ø; pin Ø, height (L3.3.x), mm | 4; ≤ 0.25; 3.0–4.0; 1.4–1.6, 1.2–1.6 | |
| Top / bottom keep-out d; lid above PCB; post height (L3.4.x), mm | ≥ 0 / ≥ 0; ≥ 5.0; 8.8–10.5 | |
| USB plug d; opening W × H, centre (L3.5.x), mm | ≥ 0.3; 11.6 × 8.6 to 14.0 × 11.0 | |
| LED holes: count; Ø; flange overlap (L3.6.x), mm | 3; 5.2–5.4; ≥ 0.2 | |
| Hooks: count; engagement; strain (L3.7.x) | ≥ 4; 0.6–1.0; ≤ 0.02 | |
| Lip gap per side; engagement (L3.8.x), mm | 0.15–0.35; ≥ 2.0 | |
| Opening count; wall thickness (L3.9.x), mm | 3 LED + 1 USB; 2.0–3.0 | |
| Shells; overhang patches; bed contact (L3.10.x) | 1 / 1; 0; ≥ 50% | |
| Envelope X × Y × Z (L3.11.1.1), mm | ≤ 60 × 30 × 26 | |
| Self-report agreement (L3.12.2.1) | 100% within 0.10 | |

---

## 8. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 (`design.json`) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1–L2.1.3 | L3.1.1.1, L3.1.1.2, L3.1.2.1, L3.1.3.1 | L1.1 | inspection | "a small box for an Arduino Nano", "mini-USB port ... through one short end", "three 5 mm status LEDs on the top face" |
| L1.2 | Board fit | L2.2.1–L2.2.2 | L3.2.1.1, L3.2.2.1, L3.2.2.2 | L1.2 | analysis | "a small box for an Arduino Nano" |
| L1.3 | Board support | L2.3.1–L2.3.3 | L3.3.1.1, L3.3.1.2, L3.3.1.3, L3.3.2.1, L3.3.3.1 | L1.3 | inspection | "Arduino Nano ... header pins pointing down" |
| L1.4 | Clearances | L2.4.1–L2.4.2 | L3.4.1.1, L3.4.1.2, L3.4.2.1, L3.4.2.2 | L1.4 | analysis | "leave on a shelf" (parts must not touch the box) |
| L1.5 | USB access | L2.5.1–L2.5.3 | L3.5.1.1, L3.5.2.1, L3.5.3.1 | L1.5 | test | "The mini-USB port has to be reachable through one short end with the lid on" |
| L1.6 | LED windows | L2.6.1–L2.6.3 | L3.6.1.1, L3.6.1.2, L3.6.2.1, L3.6.2.2, L3.6.3.1 | L1.6 | inspection | "three 5 mm status LEDs on the top face should be visible" |
| L1.7 | Snap fit | L2.7.1–L2.7.3 | L3.7.1.1, L3.7.1.2, L3.7.1.3, L3.7.2.1, L3.7.2.2, L3.7.3.1 | L1.7 | inspection | "The lid snaps on without screws" |
| L1.8 | Lid and seam | L2.8.1–L2.8.3 | L3.8.1.1, L3.8.2.1, L3.8.2.2, L3.8.3.1 | L1.8 | analysis | "The lid snaps on" (a separate lid) |
| L1.9 | Protection | L2.9.1–L2.9.3 | L3.9.1.1, L3.9.2.1, L3.9.3.1 | L1.9 | analysis | "a small box" |
| L1.10 | Printable | L2.10.1–L2.10.3 | L3.10.1.1, L3.10.2.1, L3.10.2.2, L3.10.3.1, L3.10.3.2 | L1.10 | analysis | "the base is printed flat in PLA" |
| L1.11 | Size and stability | L2.11.1–L2.11.2 | L3.11.1.1, L3.11.2.1 | L1.11 | analysis | "leave on a shelf" |
| L1.12 | Evidence | L2.12.1–L2.12.2 | L3.12.1.1, L3.12.2.1 | L1.12 | inspection | (not the owner's words; needed by the judge) |

---

## Audit

Adversarial audit (second agent). Recomputed every derived number; all three parts load and pass `parts.validate`; L1 = 12, L2 = 32, L3 = 46 match section 5 and the traceability table; every L3 has a numeric band and a measuring recipe. Feasibility section re-checked line by line against every gate (arithmetic held except where noted below).

| # | Defect found | Fix |
|---|---|---|
| 1 | L3.2.2.2 asked for inner X length >= 46.4 (45.0 + 0.7 + 0.5 + 0.2). A design at 46.4 with the 0.3 receptacle clearance leaves 0.4 at the far PCB end and fails the gate L3.2.1.1: the stated minimum was not sufficient. | Minimum is now 46.5 = 0.3 + 0.7 + 45.0 + 0.5. Feasibility (46.7) still satisfies it. |
| 2 | L3.11.1.1 excluded the LED domes (dome top Z 17.6 would make the box 28.6 high) but L1.11 in `design.json` did not say so, so the agent could be failed on a height it was never allowed to ignore. | L1.11 now says "not counting the LED domes". |
| 3 | L2.1.3 LED placement (Y within 9.0 +/- 3.0, X in 8.0 to 40.0) was an arbitrary hidden window. The "3.0 from the cavity edge" rule also contradicted the lid lip: flange radius 2.9 + lip gap 0.2 + 0.8 lip leaves 3.9. | Replaced by derived rules: row over the board footprint, pitch >= 9.0, axis >= 4.0 from the cavity edge. Default positions still satisfy them. |
| 4 | Numbers a gate or weight-3 row needs but the agent was never told: post and pin diameters (L3.3.1.3, L3.3.2.1), USB clearance 0.3 and 1.5 ligament (L3.5.1.1, L3.5.3.1), flange overlap, LED pitch, hook count, width and engagement, strain limit (G5), lip depth and fit. | Added to the L1 texts in `design.json` (L1.3, L1.5, L1.6, L1.7, L1.8, L1.9). No L3 number changed. |
| 5 | A3 claimed 1.5 mm above the top parts; the receptacle top (Z 5.5) leaves 1.1 to V-KO-TOP (6.6). | A3 text corrected (the check itself, clear_of V-KO-TOP at 0.0, was already right). |
| 6 | Noted, not changed: the USB opening upper bound 14.0 x 11.0 cannot be reached together with the 1.5 ligament to a seam at Z 10.0 (opening top would be 9.05). | Not a contradiction (a feasible design exists: 12.0 x 9.0, top 8.05, ligament 1.95); the 1.5 ligament governs. Recorded as an assumption note. |

Residual uncertainty: the lip thickness is not constrained (0.8 minimum feature only); the hook groove depth equals the hook engagement (0.8), a zero-clearance designed contact. The generic `benchmarks/generalize/rubric.md` does not exist; section 7 governs.
