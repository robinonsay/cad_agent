# E1-01 Pico 2 CW keyer enclosure: requirements (L1 / L2 / L3)

The "ultimate test" request for the OpenSCAD agent, the error signal of the enclosure control
loop (`loop/`), and the yardstick for an A/B comparison against the design Robin already made
with another LLM. The machine-readable request (L1 only, `dev.json` format) is `enclosure.json`
next to this file; three sibling requests that guard against over-fitting are in `variants.json`;
how a blind judge applies this document is in `rubric.md`.

**Robin's request (verbatim):** "An enclosure for a perfboard that will hold a RPi pico2 CW Radio
keyer with two aux ports on one side and the usb port exposed on the other (long ways). The perf
board is 70x50mm."

**Photo** (`perfboard_photo.png`): a bare green double-sided perfboard, 2.54 mm grid, one
mounting hole in each corner, no parts fitted yet; a micro-USB cable lies next to it (so the
Pico 2's port is micro-USB B, not USB-C). Because the board is still bare, **where the Pico and
the jacks sit on the board is part of the design**, not a hidden fact. The design must declare
that layout (L1.1, L1.12) and every port check is graded against the declared layout.

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check on the geometry. Every row has a verification
method (inspection, analysis, demonstration, test, human; as defined in `dev.json`), a pass/fail
criterion with a number and a tolerance, and a weight (3 = critical, 2 = major, 1 = minor). The
"Check" column says whether an existing `cad_checks.py` check type can run it on the agent's own
design model (**today: `<type>`**), or which **new check** it needs. Every number that comes from
an assumption (section 3) is provisional until Robin confirms it.

**This is meant to be hard.** Most L3s cannot be checked by the agent today and many need
geometry the shape library cannot make (section 6). That is the point: the loop must grow the
agent until these pass. Do not relax a criterion because the agent fails it; change a number only
when Robin corrects an assumption.

---

## 1. Frames, tolerances and the two interference checks

### 1.1 Frames

- **Enclosure frame:** X along the board's 70 mm side, Y along its 50 mm side, Z up. The USB end
  is **−X**, the aux end is **+X**. A design delivered mirrored or rotated is normalised into this
  frame before grading (rubric step 1); that is never penalised.
- **Board frame (all tables below):** origin at the perfboard's top-surface corner at min X, min
  Y. Z = 0 is the board's top surface; the board occupies Z −1.6 to 0.

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered meshes (STL/3MF), never by eye (see
`rubric.md` section 3).

| Quantity | Measurement tolerance ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within ε (e.g. "≥ 0.50" passes at 0.48) |
| angle | 0.5° | same |
| interference volume | 0.01 mm³ | "no interference" means intersection volume ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the hole's section (what a screw or pin sees) | |
| boss / standoff OD | smallest enclosing circle of the section | |

Where a criterion is written "nominal ± t", t is the design tolerance and ε is added to it.

### 1.3 The two interference checks

Fit, access and port requirements are written, wherever possible, as one of two checks against
named reference models (M-) and envelope volumes (V-) from section 2. Both are proposed new
checks for `cad_checks.py`; the grader runs its own implementation (rubric section 3).

- **`clear_of(bodies, volume, clearance)`**: the minimum Euclidean distance between every printed
  body in `bodies` and `volume` is ≥ `clearance`. Equivalently: no body intersects `volume`
  offset outward by `clearance`. Reported value: the signed minimum distance d (negative = the
  body penetrates the volume; the penetration volume is reported too). Pass: d ≥ clearance − ε.
- **`inside(volume, cavity, clearance)`**: `volume` lies entirely in `cavity`, and every point of
  it is ≥ `clearance` from the cavity's boundary. Reported value: the signed minimum distance
  from `volume` to the cavity boundary (negative = part of the volume is outside the cavity).
  Pass: d ≥ clearance − ε.

`bodies` is **ALL** (base and lid, closed), **BASE**, or **LID**. A design never builds or edits the
reference volumes: the grader generates them independently from the catalogue and the design's
declared layout (section 2.3). The agent may and should generate the same volumes for its own
checks, but its copies are not trusted for grading.

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from a `part.json` in `benchmarks/enclosure/parts/<part_id>/`
  (numbers from datasheets, section 3). These are the only place target-specific part numbers
  may live. The primary arm of every comparison uses only these.
- **imported**: a vendor 3D model (STEP converted to STL/3MF, or STL), placed by mapping its
  datums onto the catalogue datums. Used only in the optional second arm (section 7) and for the
  sanity checks in 2.4.
- **envelope**: a keep-out or access volume generated by Python from the datums of catalogue or
  imported models (offsets, sweeps, columns). Never drawn by hand.
- **computed**: derived from the design itself (cavity, apertures).

### 2.2 Reference models (M-)

Positions are the **default layout** (assumption A2), used when a design declares none and for
the A/B when Robin confirms it. Otherwise each model is placed at the pose the design declares in
`layout.json` (L3.12.1.2).

| Name | What | Source | Size and default position (board frame, mm) | Datums it must carry |
|---|---|---|---|---|
| **M-PERF** | 70 × 50 perfboard | catalogue `perfboard_70x50` | 70.0 × 50.0 × 1.6; X 0–70, Y 0–50, Z −1.6–0; 4 holes Ø3.0 at (2.5, 2.5), (67.5, 2.5), (2.5, 47.5), (67.5, 47.5); 2.54 mm hole grid | `PERF_TOP` (plane Z = 0), `PERF_BOTTOM` (plane Z = −1.6), `PERF_HOLE_1..4` (axes), `PERF_EDGE_X0`, `PERF_EDGE_X70`, `PERF_GRID` (origin + pitch) |
| **M-HDR** | 2 × 20-pin male headers under the Pico | catalogue `header_male_2p54` | 2.54 mm pitch, plastic spacer 2.5 mm tall, rows 17.78 mm apart at Y 16.11 and 33.89, pins at X 1.37 + 2.54·i (i = 0..19) | `HDR_TOP` (plane Z = 2.5): sets the Pico's height; `HDR_PIN_r_i` (axes, must land on `PERF_GRID`) |
| **M-PICO2** | Raspberry Pi Pico 2 with micro-USB B receptacle | catalogue `rpi_pico2` (imported alternative: official Raspberry Pi Pico 2 STEP) | PCB 51.0 × 21.0 × 1.0 at X 0–51, Y 14.5–35.5, Z 2.5–3.5; receptacle 8.0 (Y) × 5.5 (X) × 2.8 (Z) on top at X −1.3–4.2, Y 21.0–29.0, Z 3.5–6.3; tallest other top part ≤ 1.5 above the PCB | `USB_MOUTH` (point, centre of the receptacle opening: (−1.3, 25.0, 4.9)), `USB_AXIS` (−X), `PICO_HOLE_1..4` (Ø2.1, pitch 47.0 × 11.4), `PICO_PCB_BOTTOM` (plane) |
| **M-JACK-1, -2** | 3.5 mm TRS PCB jack, PJ-320A type | catalogue `jack_3p5_pj320a` (imported alternative: vendor STEP) | body 12.0 (X) × 6.0 (Y) × 5.0 (Z) at X 58.0–70.0, centred Y 17.5 / 32.5, Z 0–5.0; barrel bore Ø3.6, mouth face at X 70.0; axis Z 2.5 | `JACK_MOUTH_k` (point (70.0, Y_k, 2.5)), `JACK_AXIS_k` (+X), footprint pins |
| **M-PLUG-USB** | micro-USB B cable plug | catalogue `plug_microusb_b` | metal shell 6.9 (Y) × 1.85 (Z), inserted depth 5.0, exposed shell 1.5; overmold 10.0 (Y) × 7.0 (Z) × 20 long | `PLUG_TIP`, `PLUG_AXIS`, `OVERMOLD_FACE` |
| **M-PLUG-TRS** | 3.5 mm TRS cable plug | catalogue `plug_trs_3p5` | shaft Ø3.5 × 14.0; overmold Ø8.0 × 25 long; stop gap at full mate ≤ 1.0 | `PLUG_TIP`, `PLUG_AXIS`, `OVERMOLD_FACE` |
| **RBA** | reference board assembly = M-PERF ∪ M-HDR ∪ M-PICO2 ∪ M-JACK-1 ∪ M-JACK-2 at the declared (or default) layout | assembled | as above | all of the above |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Source | Definition (default layout, board frame, mm) | Datums used |
|---|---|---|---|---|
| **V-KO-TOP** | component keep-out above the board | envelope | board footprint X 0–70, Y 0–50, Z 0 to +12.0 (A8) | `PERF_TOP` |
| **V-KO-BOT** | solder-side keep-out | envelope | board footprint, Z −1.6 to −5.6 (4.0 below `PERF_BOTTOM`, A8), minus the four V-SEAT columns | `PERF_BOTTOM`, `PERF_HOLE_k` |
| **V-SEAT-k** (k = 1..4) | where a standoff may touch the board | envelope | Ø7.0 column on `PERF_HOLE_k`, from the floor up to `PERF_BOTTOM` | `PERF_HOLE_k` |
| **V-HOLE-KO-k** | screw-head and driver room above each board hole | envelope | Ø7.0 column on `PERF_HOLE_k`, Z 0 to +12.0 | `PERF_HOLE_k` |
| **V-PERF-EDGE** | lateral clearance zone of the board | envelope | M-PERF itself (used with clearance 0.5, excluding V-SEAT) | M-PERF |
| **V-PICO** | the Pico and its receptacle (including the part outside the board edge) | envelope | M-PICO2 ∪ M-HDR bounding solids | `USB_MOUTH`, `PICO_PCB_BOTTOM` |
| **V-USB-PLUG** | micro-USB plug at full mate plus its withdrawal path | envelope: M-PLUG-USB placed at full mate, overmold swept out along `USB_AXIS` | shell 6.9 × 1.85 from 5.0 inside `USB_MOUTH` to 1.5 outside it (X 3.7 to −2.8); overmold 10.0 × 7.0 from X −2.8 outward to X −42.8 (past any wall) | `USB_MOUTH`, `USB_AXIS` |
| **V-JACK-PLUG-k** | 3.5 mm plug at full mate plus its path | envelope: M-PLUG-TRS at full mate, swept out along `JACK_AXIS_k` | shaft Ø3.5 from `JACK_MOUTH_k` to 1.0 outside it (X 70.0–71.0); overmold Ø8.0 from X 71.0 to 111.0 | `JACK_MOUTH_k`, `JACK_AXIS_k` |
| **V-INSTALL** | board installation path | envelope | the RBA's plan silhouette (Z-projection) swept +Z from its seated pose to 5.0 above the base rim | RBA pose |
| **V-DRIVER-k** | screwdriver access to a board screw | envelope | Ø6.0 column on `PERF_HOLE_k` from `PERF_TOP` to 50 above the base rim, lid off | `PERF_HOLE_k` |
| **V-LIDDRIVER-j** | screwdriver access to a lid screw (screw closure only) | envelope | Ø6.0 column on each lid-screw axis from the lid top to 50 above it | lid-screw axes |
| **V-CAVITY** | the closed enclosure's internal void | computed | convex hull of (BASE ∪ LID, closed) minus (BASE ∪ LID), connected component containing the RBA centroid | none |
| **V-AP-USB**, **V-AP-AUX** | the openings actually present in the −X and +X end walls | computed | for each end wall: the slab between its inner and outer faces, spanning the wall's full Y and Z extent, minus (BASE ∪ LID) | wall faces |
| **V-AP-OTHER** | every other opening | computed | (convex hull of ALL) minus ALL minus V-CAVITY's interior core, i.e. every through-path from outside into V-CAVITY, as connected regions | none |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

A model or envelope that fails one is fixed before grading.

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | every catalogue and imported model | units: bounding box in mm (not ×25.4 or ×1000) | M-PICO2 PCB 51.0 × 21.0 ± 0.2; M-JACK body 12.0 × 6.0 × 5.0 ± 0.5 |
| R2 | M-PICO2 | PCB thickness and hole pattern | 1.0 ± 0.1; holes Ø2.1 ± 0.1, pitch 47.0 × 11.4 ± 0.1 |
| R3 | M-PICO2 | orientation: components on +Z, receptacle at the −X end, `USB_AXIS` along −X | all true |
| R4 | M-PICO2 | receptacle overhang beyond the PCB edge | 1.3 ± 0.3 (or the imported model's value; see A4) |
| R5 | M-JACK-k | bore Ø and axis height above `PERF_TOP` | Ø3.6 ± 0.2; 2.5 ± 0.3 (or the part's datasheet value) |
| R6 | M-HDR | pitch, spacer height, row spacing | 2.54 ± 0.02; 2.5 ± 0.1; 17.78 ± 0.05 |
| R7 | RBA | models do not collide with each other | intersection ≤ 0.01 mm³ |
| R8 | every V- envelope | its datums equal the model datums it was generated from | ≤ 0.01 |
| R9 | imported vs catalogue (second arm only) | the imported model's bounding box and datums match the catalogue part | ≤ 0.3 per axis; datums ≤ 0.2 |

**Seating rule.** The RBA is placed at the pose declared in `layout.json`, expressed in the
design's frame. The grader then verifies the declaration: the RBA's `PERF_BOTTOM` lies on the
standoff tops (distance ≤ 0.10) and `PERF_HOLE_1..4` are coaxial with the standoff pilot holes
(least-squares fit, residual ≤ 0.25). If the declaration is missing or fails verification, the RBA
is seated by that fit instead; if there are no standoffs, it is centred in the cavity with its
underside 4.0 above the floor, and every L1.3 check fails.

---

## 3. Assumptions and open questions for Robin

Each line gives the value chosen and why. **A1 to A5 matter most; please confirm them.** For the
A/B to be fair, both designs must be judged against Robin's real parts. Wrong values here would
penalise Robin's design for being right.

| # | Question | Value chosen | Why |
|---|---|---|---|
| **A1** | What does "long ways" mean? | The Pico lies along the 70 mm axis. The USB port is in one **50 mm end wall** (−X). Both aux jacks are in the **opposite 50 mm end wall** (+X). The ports face out along the long axis. | The Pico (51 mm) plus a jack body (12 mm) fits along 70 mm with room to spare. The Pico's USB is on its short edge, so a Pico lying "long ways" points its USB at a short end. **Alternative:** the ports are in the two **70 mm long walls**. If so, swap X and Y in L1.1, L1.5 and L1.6, and the board's long edges become the port faces. |
| **A2** | Where do the parts sit on the board? | The design chooses (the board is bare in the photo) and declares it. **Default layout** (used when a design declares none): Pico centred across the board (centreline Y 25.0), its PCB end flush with the −X board edge; jacks' mouths at the +X edge, at Y 17.5 and 32.5. | A symmetric common layout. If Robin has already populated a board, he should give the real coordinates, and the A/B will use them. |
| **A3** | How is the Pico mounted? | Soldered on 2.54 mm male headers (2.5 mm plastic spacer). Pico PCB underside 2.5 above the board, so the USB axis is **4.9 above the board top**. | The lowest common method. **Female sockets** (about 8.5 mm): USB axis about **10.9**, and the top keep-out grows to at least 18. **Soldered flat** (castellated): axis about 2.4. Variant V3 exercises the socket case. |
| **A4** | Pico 2 dimensions? | PCB 51.0 × 21.0 × 1.0. Micro-USB B receptacle on top, centred on the short edge, about 8.0 wide × 2.8 tall × 5.5 deep, overhanging the PCB edge by about **1.3**. Mounting holes Ø2.1, pitch 47.0 × 11.4. | Raspberry Pi Pico 2 datasheet (same outline as the Pico). The overhang and receptacle height are approximate: measure one, or read them from the official STEP. The photo confirms micro-USB. |
| **A5** | Aux jack type and position? | PCB-mount 3.5 mm TRS jack, PJ-320A type: body 12 × 6 × 5, axis 2.5 above the board, mouth at the board edge. One for the paddle, one for the key line to the radio. | The commonest hobby part. **Alternative:** panel-mount jacks (Ø6.0–6.5 hole and a nut, wall ≤ 3.0 thick at the jack). If so, the jacks are fixed to the wall, L2.6.1 changes to a Ø6.0–6.5 hole, and L2.8.2's wall-thickness limit at the jack becomes ≤ 3.0. |
| A6 | Plug sizes? | Micro-USB overmold 10.0 × 7.0; 3.5 mm plug overmold Ø8.0 with a 14.0 shaft. | Typical cables. With 2 mm walls, each overmold must enter its opening for the plug to seat, so plug envelopes, not fixed hole sizes, set the openings. **Measure Robin's own cables.** |
| A7 | Board details? | 1.6 thick; corner holes Ø3.0, centres 2.5 in from each edge (pitch 65.0 × 45.0); 2.54 mm grid. | Typical for green 50 × 70 double-sided proto boards. The photo shows holes about 2–2.5 mm from the corners. Some boards have Ø2.0 holes 2.0 in. **Measure.** |
| A8 | Clearance above and below? | At least 12.0 above the board top (the keep-out V-KO-TOP); at most 3.0 of solder and clipped leads below, plus 1.0 margin, so a 4.0 floor gap (V-KO-BOT goes 4.0 down from the board underside). | The tallest assumed part is the receptacle top (6.3). The rest covers wire loops and keyer parts (transistor, optocoupler, resistors, a small speed potentiometer without knob). Solder fillets plus clipped leads are about 2–3. |
| A9 | Board fastening? | 4 × M2.5 self-tapping screws into printed standoffs (pilot Ø2.0–2.2). | M2.5 passes a Ø3.0 hole. **Alternative:** heat-set inserts (hole Ø3.5–3.6, standoff OD ≥ 6.5), accepted by L2.3.2. |
| A10 | Lid closure? | Separate lid with a locating lip, 4 × M3 self-tapping screws into bosses (pilot Ø2.5). | Robust and easy to print. **Alternative:** at least 2 snap latches, or a sliding lid; L2.7.3 lists the numbers for each. Robin's earlier design may use any. |
| A11 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. Sliding fit 0.15–0.35 per side. Board-to-wall ≥ 0.5. | Common printers and typical FDM tolerances. |
| A12 | Wall thickness? | Walls, floor and lid 2.0–4.0. | 5 perimeters at 0.4 line width: stiff enough for bosses and plugging cables in and out. |
| A13 | Maximum size? | Closed outside ≤ 90 × 70 × 35 (X × Y × Z). | Stops oversized designs. A tight design is about 76 × 55 × 22, or about 76 × 67 × 22 with corner lid bosses outside the board footprint. |
| A14 | Vents, buttons, LED window, labels? | None needed. | Pico plus keyer draws well under 1 W. BOOTSEL is used rarely, lid off. Labels ("PADDLE", "KEY") are welcome but not graded. **Confirm** (e.g. a speed knob or a sidetone buzzer would add an opening). |
| A15 | Cable pull? | 0.5 N sideways pull at a port centre, total mass 40 g. | A cable tugging the keyer on a desk. Rubber feet are optional. |
| A16 | Which part is which? | Base holds the board; lid is a separate printed part. Both delivered as separate bodies in the closed assembly pose, with their print orientation stated. | Needed to grade each part's printability and the closed fit. |
| A17 | Which jack is which? | Not graded: the two jacks are interchangeable for the enclosure. | The enclosure does not care which is paddle and which is key. |

---

## 4. Requirements tree

### L1.1 The Pico and the two jacks are laid out on the board so the USB faces one short end and both jacks face the other

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its board layout: the pose of each RBA part (catalogue id, X, Y, Z, rotation about Z) in the board frame. | inspection | `layout.json` present, parses, names M-PERF, M-PICO2 (with its headers) and two M-JACK parts from the catalogue | 3 | new check: layout declaration (part of the evidence package, L1.12) |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 | new check |
| L2.1.2 | The Pico points its USB out of the −X end; both jacks point out of the +X end. | inspection | `USB_AXIS` within 1.0° of −X; each `JACK_AXIS_k` within 1.0° of +X | 3 | |
| L3.1.2.1 | Port axis directions in the declared layout. | inspection | as L2.1.2 (±0.5° measurement) | 3 | new check: datum direction |
| L2.1.3 | The ports reach the board edges, so the plugs can reach them through the walls. | inspection | `USB_MOUTH` X in [−1.8, −0.8] (PCB flush with the −X edge ± 0.5); each `JACK_MOUTH_k` X in [69.5, 71.0] | 2 | |
| L3.1.3.1 | Port mouth positions along X. | inspection | as L2.1.3 | 2 | new check: datum position |
| L2.1.4 | The parts fit on the board without colliding, and they leave the corner screws free. | analysis | RBA parts mutually interference-free; clear_of(RBA parts except M-PERF, V-HOLE-KO-1..4, 0.0) | 3 | |
| L3.1.4.1 | Pairwise interference of RBA parts. | analysis | each pair ≤ 0.01 mm³ | 3 | new check: interference between catalogue models |
| L3.1.4.2 | No part on a screw column. | analysis | clear_of(M-PICO2 ∪ M-HDR ∪ M-JACK-1 ∪ M-JACK-2, V-HOLE-KO-1..4, 0.0) | 3 | new check: `clear_of` |
| L3.1.4.3 | Every part's plan outline lies on the board, except the port overhangs. | inspection | plan projection within X [−2.0, 71.0], Y [0, 50] | 2 | new check: plan bounds of declared models |
| L2.1.5 | The two jacks are far enough apart for two plugs and a wall ligament between their openings. | inspection | jack axis spacing ≥ 11.0 (8.0 overmold + 2 × 0.3 clearance + ≥ 1.5 ligament, plus margin) | 2 | |
| L3.1.5.1 | Distance between `JACK_AXIS_1` and `JACK_AXIS_2`. | inspection | ≥ 11.0 | 2 | new check: datum distance |
| L2.1.6 | The Pico's header pins and the jacks' pins land on the perfboard's 2.54 mm grid. | inspection | every pin axis within 0.15 of a `PERF_GRID` hole | 1 | |
| L3.1.6.1 | Pin-to-grid residuals. | inspection | max residual ≤ 0.15 | 1 | new check: grid conformance |

### L1.2 The perfboard fits inside the enclosure with at least 0.5 mm clearance at its edges

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.2.1 | With the RBA seated and the lid closed, no printed body comes within 0.5 of the perfboard, except the standoff tops under its holes. | analysis | clear_of(ALL, M-PERF minus Ø8.0 columns on `PERF_HOLE_1..4` (V-SEAT grown by the 0.5 clearance, so a standoff top may touch), 0.5) | 3 | |
| L3.2.1.1 | Board-edge clearance, all four edges and both faces. | analysis | d ≥ 0.50 | 3 | new check: `clear_of` with an external reference solid |
| L3.2.1.2 | A 70 × 50 × 1.6 box lying flat fits into the base with 0.5 clearance (the agent's own-model proxy). | demonstration | `fits` passes (object box, size [70, 50, 1.6], orientation flat, clearance 0.5, into BASE parts) | 2 | today: `fits` |
| L2.2.2 | Along X, the cavity takes the board plus the USB overhang: the receptacle mouth and the board's +X edge are each ≥ 0.2 from the end walls' inner faces. | analysis | inside(V-PICO, V-CAVITY, 0.2) and clear_of(ALL, M-PERF, 0.2) along X | 3 | |
| L3.2.2.1 | Pico (with receptacle) inside the cavity. | analysis | inside(V-PICO, V-CAVITY, 0.2): d ≥ 0.20 | 3 | new check: `inside` |
| L3.2.2.2 | Inner X length between the end walls at board height. | inspection | ≥ 71.7 (70.0 + 1.3 + 0.2 + 0.2; recomputed from the declared layout) | 2 | new check: `gap` (face-to-face distance) |

### L1.3 The board is held on four standoffs by screws through its corner holes

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.3.1 | Four standoffs, one under each board hole, centred on a 65.0 × 45.0 rectangle (the catalogue hole pattern). | inspection | count = 4; each axis within 0.25 of its `PERF_HOLE_k` | 3 | |
| L3.3.1.1 | Exactly 4 standoffs. | inspection | count = 4 | 3 | today: `count` |
| L3.3.1.2 | Standoffs at the corners of the board area. | inspection | `arrangement` corners passes | 2 | today: `arrangement` |
| L3.3.1.3 | Standoff pitch. | inspection | 65.0 ± 0.25 along X; 45.0 ± 0.25 along Y | 3 | new check: `pitch` (centre distance between copies) |
| L3.3.1.4 | Standoff axes vs the seated RBA's holes. | analysis | each offset ≤ 0.25 | 3 | new check: datum alignment |
| L2.3.2 | Standoff OD 5.0–7.0; tops coplanar; each top touches the board only inside its V-SEAT column. | inspection | OD in [5.0, 7.0]; top-Z spread ≤ 0.10; standoffs ⊂ V-SEAT-k up to `PERF_BOTTOM` | 2 | |
| L3.3.2.1 | Standoff OD. | inspection | 5.0 ≤ OD ≤ 7.0 | 2 | today: `dimension` diameter ge + le |
| L3.3.2.2 | Top-plane spread of the four standoffs. | inspection | max − min top Z ≤ 0.10 | 2 | today for the agent's model (copies share a height); new check for STL: top-plane spread |
| L2.3.3 | Each standoff has a pilot hole for an M2.5 self-tapping screw (or a heat-set insert, A9). | inspection | screw: Ø2.0–2.2, depth ≥ 5.0 from the top, coaxial ≤ 0.1; insert: Ø3.5–3.6, depth ≥ 4.0, OD ≥ 6.5 | 3 | |
| L3.3.3.1 | Pilot hole diameter. | inspection | in the chosen variant's range | 3 | today: `dimension` inner_diameter on a tube standoff |
| L3.3.3.2 | Pilot hole depth (blind or through to the floor). | inspection | ≥ 5.0 (screw) / ≥ 4.0 (insert) | 2 | today for tube standoffs (`dimension` height); new check for STL: blind-hole depth |
| L2.3.4 | Standoffs are fused to the floor; the base is one body. | analysis | contact per standoff ≥ 15 mm²; BASE connected | 2 | |
| L3.3.4.1 | Standoff-to-floor contact. | analysis | `touches` min_area 15 mm² | 2 | today: `touches` |
| L3.3.4.2 | Base is one connected body. | analysis | `connected` passes; STL: 1 shell | 3 | today: `connected` |
| L2.3.5 | Nothing except the screws enters the board holes from above or blocks a screw head. | analysis | clear_of(ALL, V-HOLE-KO-k minus a Ø2.9 core, 0.0) for k = 1..4 | 2 | |
| L3.3.5.1 | Screw-head columns clear. | analysis | d ≥ 0.0 (no interference) | 2 | new check: `clear_of` |

### L1.4 The parts on the board clear the enclosure: at least 12 mm above the board and 4 mm below it

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.4.1 | Lid closed: no body enters the component zone above the board. | analysis | clear_of(ALL, V-KO-TOP, 0.0) | 3 | |
| L3.4.1.1 | Top keep-out clear. | analysis | d ≥ 0.0 | 3 | new check: `clear_of` |
| L3.4.1.2 | Lid underside minus board top (the agent's own-model proxy). | inspection | ≥ 12.0 | 2 | new check: relative vertical gap between parts |
| L2.4.2 | No body enters the solder-side zone (except the standoffs in their V-SEAT columns). | analysis | clear_of(ALL, V-KO-BOT, 0.0) | 3 | |
| L3.4.2.1 | Bottom keep-out clear. | analysis | d ≥ 0.0 | 3 | new check: `clear_of` |
| L3.4.2.2 | Standoff height above the floor top (own-model proxy). | inspection | ≥ 4.0 and ≤ 10.0 | 2 | today: `dimension` height ge + le |
| L2.4.3 | Every board part is enclosed: the Pico, headers and jacks lie inside the cavity with clearance. | analysis | inside(M-HDR ∪ M-JACK-1 ∪ M-JACK-2, V-CAVITY, 0.3); inside(V-PICO, V-CAVITY, 0.2) (L3.2.2.1) | 3 | |
| L3.4.3.1 | Headers and jacks inside the cavity. | analysis | d ≥ 0.30 | 3 | new check: `inside` |

### L1.5 A micro-USB cable plugs into the Pico through the −X end wall with the lid on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.5.1 | Lid closed: the plug can be pushed in to full mate and pulled out without touching the enclosure. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 | |
| L3.5.1.1 | USB plug envelope clear. | test | d ≥ 0.30 | 3 | new check: `clear_of` with a swept envelope |
| L3.5.1.2 | Physical: print, close, plug in Robin's cable. | test | clicks in fully, 3 of 3 tries | 2 | physical, optional (human grader) |
| L2.5.2 | The USB opening is not oversized: it stays within 1.5 of the plug envelope on every side. | analysis | inside(V-AP-USB, V-USB-PLUG offset by 1.5, 0.0) | 2 | |
| L3.5.2.1 | Opening within the grown plug envelope. | analysis | d ≥ 0.0 (with defaults: opening ≤ 13.0 × 10.0) | 2 | new check: `aperture` (computed opening) + `inside` |
| L2.5.3 | Exactly one USB opening, in the −X end wall only. | inspection | V-AP-USB has 1 connected region; no other wall has an opening the USB envelope passes through | 2 | |
| L3.5.3.1 | Opening count in the −X wall. | inspection | 1 | 2 | new check: `aperture` enumeration |

### L1.6 Two 3.5 mm plugs fit into the two jacks through the +X end wall with the lid on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.6.1 | Lid closed: both plugs, inserted at the same time, reach full mate (overmold face ≤ 1.0 from the jack mouth) without touching the enclosure or each other. | test | clear_of(ALL, V-JACK-PLUG-1 ∪ V-JACK-PLUG-2, 0.3); the two envelopes do not intersect | 3 | |
| L3.6.1.1 | Jack plug envelopes clear. | test | d ≥ 0.30 for each | 3 | new check: `clear_of` with swept envelopes |
| L3.6.1.2 | Physical: insert two real 3.5 mm plugs at once. | test | both seat fully; the keyer responds (paddle read, key line switches) | 2 | physical, optional |
| L2.6.2 | The jack openings are not oversized. | analysis | inside(V-AP-AUX, (V-JACK-PLUG-1 ∪ V-JACK-PLUG-2) offset by 1.5, 0.0) | 2 | |
| L3.6.2.1 | Openings within the grown envelopes. | analysis | d ≥ 0.0 (with defaults: each ≤ Ø11.0) | 2 | new check: `aperture` + `inside` |
| L2.6.3 | Exactly two jack openings, both in the +X end wall. | inspection | V-AP-AUX has 2 connected regions, one per jack axis | 2 | |
| L3.6.3.1 | Opening count in the +X wall. | inspection | 2 | 2 | new check: `aperture` enumeration |

### L1.7 A removable lid closes the enclosure and stays on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.7.1 | Base and lid are separate bodies, each one connected body, not fused, not interpenetrating when closed. | analysis | BASE 1 shell; LID 1 shell; BASE ∩ LID ≤ 1.0 mm³ | 3 | |
| L3.7.1.1 | Base and lid each connected. | analysis | `connected` per body; STL: 1 shell each | 3 | today: `connected` |
| L3.7.1.2 | Base and lid do not interpenetrate when closed. | analysis | `no_overlap` ≤ 1.0 mm³ | 3 | today: `no_overlap` |
| L2.7.2 | A lip, rebate or rail locates the lid on the base with a sliding fit. | inspection | engagement ≥ 2.0; clearance 0.15–0.35 per side | 2 | |
| L3.7.2.1 | Lip-to-wall gap, all locating faces. | inspection | 0.15 ≤ gap ≤ 0.35 | 2 | new check: `gap` (mating clearance) |
| L3.7.2.2 | Lip engagement depth. | inspection | ≥ 2.0 | 1 | today: `dimension` height on lip parts |
| L2.7.3 | The lid is retained. **Screws (default):** 4 bosses, pilot Ø2.5 ± 0.1, depth ≥ 6.0, OD ≥ 6.0; lid holes Ø3.4 ± 0.1 coaxial ≤ 0.3; bosses clear of V-KO-TOP and V-INSTALL. **Snap:** ≥ 2 latches on opposite walls, engagement 0.5–1.0, beam ≥ 8.0. **Slide:** rails on two opposite walls, engagement ≥ 1.5, an end stop. | inspection / test | every number of the chosen variant met; the lid stays on when the closed box is held upside down | 2 | |
| L3.7.3.1 | (screws) Exactly 4 bosses. | inspection | count = 4 | 2 | today: `count` |
| L3.7.3.2 | (screws) Boss pilot ID, depth, OD. | inspection | 2.4 ≤ ID ≤ 2.6; depth ≥ 6.0; OD ≥ 6.0 | 2 | today: `dimension` on tube bosses |
| L3.7.3.3 | (screws) Lid holes coaxial with the boss pilots. | inspection | Ø3.3–3.5; axis offset ≤ 0.3 | 2 | new check: hole alignment between bodies |
| L3.7.3.4 | (screws) Lid-screw driver access. | analysis | clear_of(ALL, V-LIDDRIVER-1..4, 0.0) | 1 | new check: `clear_of` |
| L3.7.3.5 | (snap / slide) Latch or rail numbers. | inspection | as L2.7.3 | 2 | new check: snap/slide geometry |
| L3.7.3.6 | Physical: hold upside down and shake; open and close 10 times. | test | lid stays on; nothing cracks or strips | 2 | physical, optional |
| L2.7.4 | The closed seam is tight and the outer faces are flush. | inspection | seam gap ≤ 0.5; step between lid and base outer faces ≤ 0.5 (or a uniform overhang ≤ 1.0) | 1 | |
| L3.7.4.1 | Seam gap and flushness on all 4 sides. | inspection | as L2.7.4 | 1 | new check: `gap` / flushness |

### L1.8 The enclosure protects the board: closed on all sides except the ports and screw holes, with 2–4 mm walls

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.8.1 | The only openings are the USB opening, the two jack openings and the screw holes. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into V-CAVITY, other than the screw holes | 2 | |
| L3.8.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 | new check: aperture enumeration / watertight-except-ports |
| L2.8.2 | Walls, floor and lid plate are 2.0–4.0 thick (at a port, the wall must still let the plug seat: L2.5.1, L2.6.1 outrank this). | inspection | each in [2.0, 4.0] | 2 | |
| L3.8.2.1 | Each side wall's thickness (median over the wall, away from features). | inspection | 2.0 ≤ t ≤ 4.0 | 2 | today: `dimension` thickness |
| L3.8.2.2 | Floor thickness. | inspection | 2.0 ≤ t ≤ 4.0 | 2 | today: `dimension` height |
| L3.8.2.3 | Lid plate thickness. | inspection | 2.0 ≤ t ≤ 4.0 | 2 | today: `dimension` height |
| L2.8.3 | At least 1.5 of material around every opening (to wall edges, the floor top, the seam and neighbouring openings). | analysis | min ligament ≥ 1.5 | 1 | |
| L3.8.3.1 | Minimum ligament per opening. | analysis | ≥ 1.5 | 1 | new check: ligament width |
| L2.8.4 | Each wall joins the floor along its length. | analysis | contact ≥ 90% of wall length × thickness (less any opening that reaches the floor) | 2 | |
| L3.8.4.1 | Wall-to-floor contact. | analysis | `touches` min_area ≥ 0.9 × L × t | 2 | today: `touches` |

### L1.9 Both parts print on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.9.1 | In its stated print orientation (default: base open side up, lid outer face down), no part has an unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12.0 in vertical walls and bridges ≤ 15.0. | analysis | 0 offending faces (area > 1 mm²) | 2 | |
| L3.9.1.1 | Overhang and bridge scan per part. | analysis | as L2.9.1 | 2 | new check: overhang/bridge analysis |
| L2.9.2 | Each part's mesh is manifold and a single shell. | analysis | 1 shell; manifold3d accepts it; no self-intersection | 3 | |
| L3.9.2.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold = true | 3 | today: cad_agent mesh shell count + manifold3d build |
| L2.9.3 | Each part rests on a flat face in its print orientation. | analysis | bed contact ≥ 50% of the plan bounding box | 1 | |
| L3.9.3.1 | Bed-contact area per part. | analysis | ≥ 50% | 1 | new check: bed contact |
| L2.9.4 | No feature thinner than 0.8; mating clearances ≥ 0.15. | analysis | min wall ≥ 0.8; min mating gap ≥ 0.15 | 1 | |
| L3.9.4.1 | Thin-feature and mating-gap scan. | analysis | as L2.9.4 | 1 | new check: thin-feature analysis |
| L2.9.5 | Each part fits a 200 × 200 × 200 build volume. | inspection | bounding box ≤ 200 per axis | 1 | |
| L3.9.5.1 | Bounding box per part. | inspection | ≤ 200 per axis | 1 | new check: per-body bounding box |

### L1.10 It sits on a desk: flat, stable and compact (closed outside size at most 90 × 70 × 35 mm)

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.10.1 | Closed outside size ≤ 90 × 70 × 35, longest plan side along X (the port ends are the short ends). | inspection | X ≤ 90.0, Y ≤ 70.0, Z ≤ 35.0; X > Y | 1 | |
| L3.10.1.1 | Assembly bounding box. | inspection | as L2.10.1 | 1 | today per part (`dimension` le); new check: assembly bounding box |
| L2.10.2 | It stands on its base without tipping. | analysis | stable at 5° table tilt | 1 | |
| L3.10.2.1 | `stable` with tilt_deg 5. | analysis | passes | 1 | today: `stable` |
| L2.10.3 | It does not tip under a 0.5 N sideways pull at any port centre (mass 40 g). | analysis | restoring moment > tipping moment | 1 | |
| L3.10.3.1 | Tipping-moment margin per port. | analysis | margin > 0 | 1 | new check: `stable` with a horizontal force |
| L2.10.4 | Flat underside; nothing below the floor except optional feet ≤ 3.0 tall, all equal. | inspection | flatness ≤ 0.2; feet equal within 0.1 | 1 | |
| L3.10.4.1 | Underside planarity and protrusions. | inspection | as L2.10.4 | 1 | new check: underside flatness |

### L1.11 The board goes in and comes out with the lid off, using a screwdriver

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.11.1 | Lid off: the RBA drops straight down (−Z) from above the rim onto the standoffs without hitting anything; no tilting is needed to pass the jacks or the USB receptacle over the walls. | test | clear_of(BASE, V-INSTALL, 0.2) | 2 | |
| L3.11.1.1 | Installation path clear. | test | d ≥ 0.20 | 2 | new check: `clear_of` with a swept envelope |
| L2.11.2 | A screwdriver reaches every board screw. | analysis | clear_of(BASE, V-DRIVER-1..4, 0.0) | 1 | |
| L3.11.2.1 | Driver columns clear. | analysis | d ≥ 0.0 | 1 | new check: `clear_of` |
| L2.11.3 | Removing the lid does not release the board: lid fasteners are separate from board fasteners. | inspection | no shared fastener | 1 | |
| L3.11.3.1 | Judge confirms no fastener is shared. | inspection | true | 1 | human |

### L1.12 The design package says what was built and where, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Check |
|---|---|---|---|---|---|
| L2.12.1 | The package holds: `base.stl`, `lid.stl` (closed assembly pose, enclosure frame, mm), the `.scad` source, `layout.json` (L2.1.1, plus each body's print orientation) and the agent's own interference report. | inspection | all present and readable | 3 | |
| L3.12.1.1 | Files present and parse; STLs in mm (bounding boxes within 20–200 per axis). | inspection | true | 3 | new check: package manifest |
| L3.12.1.2 | The declared layout verifies under the seating rule (section 2.4). | analysis | board on standoff tops ≤ 0.10; hole-axis residual ≤ 0.25 | 3 | new check: seating verification |
| L2.12.2 | The agent's own interference report agrees with the judge's measurements. | analysis | for every `clear_of`/`inside` L3 the agent reports, same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 | |
| L3.12.2.1 | Self-report vs judge. | analysis | 100% agreement within 0.10 | 1 | new check: report comparison |

---

## 5. Counts

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 44 |
| L3 | 68 (20 runnable today on the agent's own design model, 2 more only on its own model (an external STL needs a new check), 42 need a new check, 4 physical or human). None of the `clear_of` / `inside` L3s runs today. |

Gates (a failure makes a design WRONG regardless of score; rubric section 4): G0 package
(L3.12.1.1), G1 manifold and two bodies (L3.9.2.1, L3.7.1.1), G2 board fit (L3.2.1.1, L3.4.1.1,
L3.4.2.1), G3 USB plug seats (L3.5.1.1), G4 both jack plugs seat (L3.6.1.1), G5 the board is
fixed (L3.3.1.1 and L3.3.3.1).

---

## 6. What the agent cannot do today (beyond_library)

The shape library is `box, panel, wedge, cylinder, tube, sphere`, placed on a parent's outside
face, with no subtraction. This request needs:

1. **Subtraction:** openings through walls (the USB opening, the two jack holes, lid screw holes)
   and blind pilot holes in solid bosses. A rectangular opening can be faked with four wall
   segments round a gap; round holes cannot.
2. **Interior placement:** parts placed inside a parent's footprint, at an inset (the lid lip
   ring, bosses in the cavity corners, standoffs on the floor at catalogue coordinates).
3. **A shell / cavity primitive** (box minus inset box), or an equivalent made of walls on a
   floor, with the cavity known to the checks.
4. **Two printable bodies** with their own print orientation (the lid flipped).
5. **Catalogue models and datums:** loading `part.json` parts, placing them by datums (USB mouth,
   jack axes, hole axes) and deriving numbers from them, instead of the LLM inventing sizes.
6. **Envelope generation:** keep-outs, plug sweeps, driver columns and the install sweep from
   datums.
7. **Interference checks against external solids:** `clear_of`, `inside`, aperture finding,
   `gap`, `pitch`, seating verification.
8. **Snap latches** (only if that closure is chosen): hooked cantilevers.
9. **Optional:** importing vendor STEP/STL models and mapping their datums (second arm only).

---

## 7. A/B and loop fairness

- **Primary arm (the one the loop optimises and the A/B reports first):** the agent gets only
  Robin's request text (`enclosure.json`) and the parts catalogue (`parts/*/part.json`, built
  from public datasheets). It does not get the photo's pixels, imported vendor models, this
  document's default layout, or any number from Robin's own design.
- **Optional second arm:** the same, plus imported vendor models (official Pico 2 STEP, jack
  STEP) mapped to the catalogue datums (sanity check R9). Report it separately; never mix its
  scores with the primary arm.
- **Robin's design** is graded on exactly the same L3s, in the same frame, with the RBA built
  from its own implied layout (Robin's coordinates, or extracted from the design by the judge
  and stated in the report). It is not required to supply `layout.json` or a self-report: for
  Robin's design, L3.1.1.1, L3.12.1.1 (beyond the STLs), L3.12.1.2 and L3.12.2.1 are scored
  N/A, and the layout L3s are scored on the extracted layout.
- **Same reference parts for both:** when Robin confirms A3–A7, the catalogue is updated and
  **both** designs are re-graded; the loop's earlier scores are then stale and marked so.
- **No over-fitting:** a loop iteration counts as converged only if the agent also passes the
  gates of every request in `variants.json` (rubric section 6). Target-specific numbers may live
  only in the catalogue and in the request text, never in agent logic.
- **Judge blindness:** the judge sees designs as "A" and "B" with names and source comments
  stripped; the judge never sees which loop iteration produced a design.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 (`enclosure.json`) | L1 method | Words in Robin's request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1–L2.1.6 | L3.1.1.1, L3.1.2.1, L3.1.3.1, L3.1.4.1–3, L3.1.5.1, L3.1.6.1 | L1.1 | inspection | "hold a RPi pico2", "two aux ports on one side and the usb port … on the other (long ways)" |
| L1.2 | Board fits | L2.2.1–L2.2.2 | L3.2.1.1–2, L3.2.2.1–2 | L1.2 | analysis | "perfboard", "70x50mm" |
| L1.3 | Board fixed | L2.3.1–L2.3.5 | L3.3.1.1–4, L3.3.2.1–2, L3.3.3.1–2, L3.3.4.1–2, L3.3.5.1 | L1.3 | inspection | "hold" + photo (corner holes) |
| L1.4 | Component clearance | L2.4.1–L2.4.3 | L3.4.1.1–2, L3.4.2.1–2, L3.4.3.1 | L1.4 | analysis | "will hold a … keyer" |
| L1.5 | USB access | L2.5.1–L2.5.3 | L3.5.1.1–2, L3.5.2.1, L3.5.3.1 | L1.5 | test | "the usb port exposed on the other" |
| L1.6 | Aux access | L2.6.1–L2.6.3 | L3.6.1.1–2, L3.6.2.1, L3.6.3.1 | L1.6 | test | "two aux ports on one side" |
| L1.7 | Lid | L2.7.1–L2.7.4 | L3.7.1.1–2, L3.7.2.1–2, L3.7.3.1–6, L3.7.4.1 | L1.7 | inspection | "enclosure" (implied: it must open to fit the board) |
| L1.8 | Protection | L2.8.1–L2.8.4 | L3.8.1.1, L3.8.2.1–3, L3.8.3.1, L3.8.4.1 | L1.8 | analysis | "enclosure" |
| L1.9 | Printable | L2.9.1–L2.9.5 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1, L3.9.5.1 | L1.9 | analysis | implied (OpenSCAD → FDM print) |
| L1.10 | Desk use, compact | L2.10.1–L2.10.4 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1 | L1.10 | analysis | "CW Radio keyer" (desk accessory with cables) |
| L1.11 | Assembly and service | L2.11.1–L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | L1.11 | test | implied |
| L1.12 | Evidence | L2.12.1–L2.12.2 | L3.12.1.1–2, L3.12.2.1 | L1.12 | inspection | needed by the judge (not Robin's words) |

The judging procedure, the measurement recipes and the defect-report format are in `rubric.md`.
