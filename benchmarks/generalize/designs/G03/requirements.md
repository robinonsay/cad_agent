# G03 ESP32 DevKitC box with antenna end: requirements (L1 / L2 / L3)

A training design of the generalisation benchmark (`benchmarks/generalize/plan.json`, family
electronics_enclosure). Modelled on E1-01 (`benchmarks/enclosure/requirements.md`): the same L1/L2/L3
structure, reference models built from catalogue parts, designed-contact rule, gates and
traceability. The machine-readable request (L1 only, `dev.json` format) is `design.json` next to this
file. Generic grading rules would live in `benchmarks/generalize/rubric.md`; when this file was
written that file did not exist yet, so **section 8 is a design-specific rubric supplement** (it
follows `benchmarks/enclosure/rubric.md`; if `generalize/rubric.md` exists later it governs the
generic parts and section 8 only adds the G03 specifics).

**Owner's request (brief, verbatim):** "I have an ESP32-DevKitC V4 (54.4 x 27.9 mm) that has no
mounting holes, so the box must hold it with ribs or clips. The micro-USB end must be open for a
cable, and the antenna end needs 8 mm of empty space with no wall material above the module. Lid is
removable and printed separately."

**How to read this.** L1 says what the owner needs. L2 is an engineering requirement with numbers.
L3 is a concrete check Python can run on the delivered STLs. Every L3 has a method, a pass band
with a tolerance, a weight (3 = critical, 2 = major, 1 = minor) and, where it is a must-pass, a gate
mark (G0 to G6, section 5). Numbers that come from an assumption (section 3) are provisional until
the owner confirms them. Do not relax a criterion because the agent fails it.

---

## 1. Frames, tolerances, checks and designed contact

### 1.1 Frames

- **Board frame (all tables below and the box frame):** the catalogue frame of `esp32_devkitc_v4`:
  origin at the PCB's min corner (USB end, long edge A), X along the 54.4 mm length with the USB end at
  **-X** and the antenna end at **+X**, Y along the 27.9 mm width, Z up with the PCB underside at Z = 0
  (the PCB occupies Z 0 to 1.6). The box is graded in this frame, so its floor is at negative Z. A design
  delivered mirrored or rotated is normalised into this frame by multiples of 90 degrees and mirroring
  only; that is never penalised.
- Lengths in mm, angles in degrees. "Closed" = base and lid in the assembly pose.

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within e |
| angle | 0.5 degrees | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole / opening size | largest inscribed circle, or the bounding box of the opening polygon at mid-wall | |
| boss OD | smallest enclosing circle of the section | |

Where a criterion is written "nominal +/- t", t is the design tolerance and e is added to it.

### 1.3 The checks

- **`clear_of(bodies, volume, c)`**: minimum distance between the printed bodies and the volume is
  >= c. Reported: signed minimum distance d (negative = penetration; penetration volume too). Pass:
  d >= c - e.
- **`inside(volume, cavity, c)`**: the volume lies entirely in the cavity, every point >= c from its
  boundary. Pass: d >= c - e.
- **`float(axis)`**: with the board model translated along an axis from its seated pose, the total
  travel (positive free travel plus negative free travel) before it penetrates a printed body by more
  than 0.01 mm3, found by bisection to 0.02. Seated contact (zero penetration) is allowed.
- Count, dimension, thickness and gap checks as in E1-01 rubric section 3.5.

`ALL` = base and lid, closed. The grader builds every reference model and envelope itself from the
catalogue and the declared layout; the agent's copies are not trusted.

### 1.4 Designed contact is not interference

Parts meant to touch are excluded from every interference and clearance check; only penetration
counts (volume above 0.01 mm3), a distance of zero passes:

- the PCB underside resting on the support pads (inside the H-SUP zones)
- a retention rib on the PCB top, a side stop or an end stop against a board edge, inside their hold
  zones (a gap of 0.2 or more is required by L2.3.2, but touching is not penetration)
- the lid lip against the base cavity faces at the fit L2.7.2 sets, and the lid resting on the base rim
- a snap hook tooth against its catch ridge in the closed pose (the engagement is required by L2.8.2)

---

## 2. Reference models, envelopes and sanity checks

### 2.1 Reference models (M-)

Built by Python from `benchmarks/generalize/parts/esp32_devkitc_v4/part.json` and the plug part
`plug_microusb_b` (`benchmarks/generalize/parts/plug_microusb_b/part.json`, an identical copy of the enclosure catalogue's part so that `esp32_devkitc_v4`'s `mates` reference resolves from one catalogue). Positions
are the board frame; the board sits at the origin (it is the reference, the design builds around it:
the layout declares the transform from the design's frame, L2.1.1).

| Name | What | Source | Size and position (board frame, mm) | Datums |
|---|---|---|---|---|
| **M-ESP** | ESP32-DevKitC V4 | catalogue `esp32_devkitc_v4` | PCB 54.4 x 27.9 x 1.6 at X 0 to 54.4, Y 0 to 27.9, Z 0 to 1.6; micro-USB receptacle 5.9 (X) x 7.5 (Y) x 2.9 (Z) at X -1.0 to 4.9, Y 10.2 to 17.7, Z 1.6 to 4.5; WROOM module 25.5 x 18.0 x 3.1 at X 28.9 to 54.4, Y 4.95 to 22.95, Z 1.6 to 4.7; header bodies 45.72 + 2.54 long x 2.54 x 2.5 at X 3.07 to 51.33, Y -0.02 to 2.52 and 25.38 to 27.92, Z 1.6 to 4.1 | `USB_MOUTH` (-1.0, 13.95, 3.05), `USB_AXIS` (-X), `PCB_BOTTOM`, `PCB_TOP`, `EDGE_LONG_A/B`, `EDGE_USB`, `EDGE_ANTENNA` (X 54.4), `ANTENNA_END`, `PINS_A/B` |
| **M-PLUG-USB** | micro-USB B cable plug | catalogue `plug_microusb_b` | metal shell 6.9 (Y) x 1.85 (Z), inserted depth 5.0, exposed shell 1.5; overmold 10.0 (Y) x 7.0 (Z) x 20.0 long | `PLUG_TIP`, `PLUG_AXIS`, `OVERMOLD_FACE` |

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition (board frame, mm) | Used by |
|---|---|---|---|
| **V-KO-TOP** | component and pin keep-out above the board | X 0 to 54.4, Y 0 to 27.9, Z 1.6 to 10.6 (header pins 8.5 above the board top = Z 10.1, plus 0.5), minus the H-TOP zones | L2.4.1 |
| **V-KO-BOT** | solder-side keep-out | X 0 to 54.4, Y 0 to 27.9, Z -3.3 to 0 (pin tails 3.0 plus 0.3), minus the H-SUP zones | L2.4.2 |
| **V-ANT** | the antenna free space | the catalogue `antenna_zone`: X 48.4 to 62.4 (the 6.0 mm module antenna end plus 8.0 beyond the board end), Y 0 to 27.9, Z 1.6 to 9.7 (module top 4.7 plus 5.0 free above) | L2.6.1 |
| **V-USB-PLUG** | micro-USB plug at full mate plus its withdrawal path | shell 6.9 x 1.85 from X 4.0 (inside the receptacle) to X -2.5; overmold 10.0 x 7.0 from X -2.5 outward to X -60; centred on `USB_AXIS` (Y 13.95, Z 3.05) | L2.5.1, L2.5.2 |
| **V-INSTALL** | board installation path | M-ESP plan silhouette (receptacle included) swept +Z from its seated pose to 5.0 above the base rim, minus the H-SUP columns | L2.12.1 |
| **V-CAVITY** | the closed box's internal void | convex hull of ALL minus ALL, connected component containing M-ESP's centroid | L2.1.3, L2.9.1 |
| **V-AP-USB** | the opening actually present in the end wall at -X | the slab between the end wall's inner and outer faces over its full Y and Z extent, minus ALL | L2.5.2, L2.5.3 |
| **V-AP-OTHER** | every other through-path from outside into V-CAVITY | rays from outside the hull reaching V-CAVITY without hitting a solid, as clusters | L2.9.1 |

**Hold zones** (the only places printed material may come near the board; allowed volumes, not
required material). They are derived from the catalogue (the header strips occupy X 3.07 to 51.33 on
both long edges, top and bottom, so every hold feature sits outside that span, or in the central
region between the pin tail strips):

| Zone | Where (board frame, mm) | What may be there |
|---|---|---|
| **H-SUP-1..4** | X 0.2 to 2.8 or 51.6 to 54.4; Y 0 to 2.5 or 25.4 to 27.9; Z -3.5 to 0 | support pads under the PCB; top plane within 0.10 of `PCB_BOTTOM` |
| **H-TOP-1, 2** | X 0.3 to 2.8; Y 0 to 2.0 or 25.9 to 27.9; Z 1.6 to 11.7 | retention ribs above the PCB top (rib underside 0.1 to 0.3 above it) |
| **H-SIDE** | X 0.2 to 2.8 or 51.6 to 54.4; Y -2.0 to 0 or 27.9 to 29.9; Z -3.5 to 1.5 | side stops against the long edges |
| **H-END-USB** | X -1.5 to 0; Y -2.0 to 5.5 or 22.4 to 29.9; Z -3.5 to 1.5 | end stops against the USB-end board edge (corner blocks, clear of the receptacle) |
| **H-END-FAR** | X 54.4 to 57.0; Y 0 to 2.5 or 25.4 to 27.9; Z -3.5 to 1.5 | end stops against the antenna-end board edge (below the antenna zone, which starts at Z 1.6) |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-ESP | units and outline | PCB 54.4 x 27.9 +/- 0.2; thickness 1.6 +/- 0.1 |
| R2 | M-ESP | orientation | components on +Z, receptacle at -X, `USB_AXIS` along -X |
| R3 | M-ESP | receptacle overhang beyond the PCB edge | 1.0 +/- 0.5 (A4) |
| R4 | M-ESP | header strip extents | X 3.07 to 51.33 +/- 0.05; strips on both long edges |
| R5 | M-PLUG-USB | shell and overmold | 6.9 x 1.85 and 10.0 x 7.0, each +/- 0.1 |
| R6 | every V- envelope | its datums equal the model datums it was built from | <= 0.01 |

**Seating rule.** The board is placed at the pose declared in `layout.json` (the transform from the
design's frame to the board frame). The grader verifies it: `PCB_BOTTOM` lies on the support pad tops
(distance <= 0.10) and the board's edges are within the hold zones' stop faces (the float rule,
L2.3.2). If the declaration is missing or fails, the board is placed by a best fit to the pad tops and
L3.13.1.2 fails; if there are no pads, the board is centred in the cavity at Z = 0.5 above the floor and
every L1.3 check fails.

---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (A-rows, with uncertainty)

| # | Question | Value chosen | Why, and how uncertain |
|---|---|---|---|
| **A1** | Header orientation and board numbers | Male pins point **up**: plastic 2.5, pin tips 8.5 above the PCB top; tails 3.0 below; PCB 1.6; USB receptacle 7.5 x 5.9 x 2.9, overhang 1.0; module 25.5 x 18.0 x 3.1 | Taken from the catalogue part (Espressif getting-started guide plus assumptions flagged there). Uncertain by +/-0.5 on overhang and header offsets. If the headers are fitted down, swap the top and bottom keep-outs. |
| **A2** | What does "open for a cable" mean? | One rectangular opening in the USB end wall, sized from the plug envelope, with the lid on; the box is otherwise closed (F1) | A fully open end would not protect the board and cannot hold it. Uncertainty: low. |
| **A3** | What does "8 mm of empty space ... with no wall material above the module" mean? | The keep-out is the catalogue `antenna_zone` (V-ANT): the 6.0 mm antenna end of the module, 8.0 mm beyond the board end, the full board width, Z 1.6 to 9.7. The end wall's inner face is at X >= 62.4 and nothing (lid, rib, lip) enters V-ANT. Lateral clearance to the side walls beyond the board edge is not required (the walls lie outside V-ANT's Y span). | Espressif recommends at least 15 mm of free board and no metal near the antenna; the owner's 8 mm is taken as stated. Uncertainty: medium; a wider free zone would be a stricter requirement (confirm). |
| **A4** | Which board areas may carry hold features? | The strips outside the header span (X < 3.07 and X > 51.33) and the central region; no component sits within the H-TOP, H-SUP zones (about 3 mm from the board corners) | The DevKitC V4 has no parts in the corners (Espressif drawing). Uncertainty: low-medium; clones differ. |
| **A5** | Plug | Micro-USB overmold 10.0 x 7.0 x 20.0, shell 6.9 x 1.85, exposed shell 1.5 (`plug_microusb_b`) | Typical cables; measure the owner's. Plug envelopes set the opening, not a fixed hole size. |
| **A6** | Wires on the header | Not required: no Dupont wires or sockets on the pins (the pins are clearance only) | The brief names only the USB cable. If wires are needed the lid height rises by about 10; confirm. |
| **A7** | Buttons, LEDs, vents | None; the EN and BOOT buttons are reached with the lid off | The module draws well under 1 W. Confirm if a button hole is wanted. |
| **A8** | Material strain limit for snaps | Allowable strain 2.0 percent (PLA, conservative; PETG tolerates about 4 percent). Strain of a straight cantilever: eps = 1.5 t y / L^2, with t the arm thickness, y the deflection (undercut plus 0.1) and L the free length | Standard cantilever snap-fit formula; PLA fatigue is poorer than the table value, so the limit is conservative. Uncertainty: +/-0.5 percent. |
| **A9** | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed; sliding fit 0.15 to 0.35 per side; walls 2.0 to 4.0 | Common printers and typical tolerances. Base prints open side up; lid prints outer face down (F5). |
| **A10** | Maximum size | Closed outside <= 75 x 45 x 25 (X x Y x Z) | Stops oversized designs; a tight design is about 68.7 x 41.3 x 20.0 (section 6). Not in the owner's words; confirm. |
| **A11** | Pull on the cable | 0.5 N sideways at the port, total mass 40 g, no tipping | A cable tugging a desk device. |
| **A12** | Which side is the lid | The lid is the top part (Z large); the base holds the board | Needed to grade each part's printability and fit. |

### 3.2 Fixed decisions (not open to alternatives)

| # | Decision |
|---|---|
| **F1** | The USB opening is **one rectangular opening** in the -X end wall; no other opening exists in the closed box. |
| **F2** | The board is held by: >= 3 support pads under it (outside the pin-tail strips), >= 2 top retention ribs on the lid at the USB end, side stops on both long edges and end stops at both short edges. No screws, glue or board holes. |
| **F3** | The lid is held by **cantilever snap hooks**, not screws or a sliding closure. |
| **F4** | The lid has a continuous locating lip fitting inside the base cavity faces. |
| **F5** | Print orientation: base open side up; lid outer face down. |
| **F6** | Board frame as in 1.1 (the grader normalises). |
| **F7** | The antenna keep-out is V-ANT exactly as in 2.2 (catalogue `antenna_zone`). |

---

## 4. Requirements tree

Column "Gate" names the must-pass groups of section 5; blank = scored only.

### L1.1 The board is placed with USB at one end and the antenna at the other

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: the pose of M-ESP (the transform from the design's frame to the board frame) and each body's print orientation. | inspection | `layout.json` present, parses, names `esp32_devkitc_v4` | 3 | G0 |
| L3.1.1.1 | Layout parses; catalogue id exists. | inspection | true | 3 | G0 |
| L2.1.2 | The USB end faces one short end of the box and the antenna end the opposite short end. | inspection | `USB_AXIS` within 1.0 degree of -X in the box frame; the end wall with the opening is at -X | 3 | |
| L3.1.2.1 | Direction of `USB_AXIS`; side of the opening. | inspection | <= 1.0 degree; opening in the -X wall | 3 | |
| L2.1.3 | The receptacle is close to its wall, so the plug reaches it, and inside the cavity. | analysis | gap from `USB_MOUTH` to the inner face of the end wall: 0.5 to 3.0; inside(M-ESP minus the support contact, V-CAVITY, 0.2) | 2 | |
| L3.1.3.1 | Mouth-to-wall gap along X. | inspection | 0.5 <= gap <= 3.0 | 2 | |
| L3.1.3.2 | The whole board and receptacle inside the cavity. | analysis | d >= 0.2 outside the hold zones | 2 | |

### L1.2 The board fits with at least 0.5 mm clearance to the printed surfaces

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Closed: no printed body comes within 0.5 of the board, except the hold features in the hold zones (which are checked separately: >= 0.2, L2.3.2). | analysis | clear_of(ALL minus the hold zones, M-ESP, 0.5); clear_of(ALL inside the hold zones, M-ESP, 0.2) | 3 | G2 |
| L3.2.1.1 | Board clearance, all faces, outside the hold zones. | analysis | d >= 0.50 | 3 | G2 |
| L3.2.1.2 | Board clearance to material inside the hold zones. | analysis | d >= 0.20 (contact on the pad tops is exempt) | 2 | |
| L3.2.1.3 | A 54.4 x 27.9 x 1.6 box fits the base cavity with 0.5 clearance (own-model proxy). | demonstration | `fits` passes | 2 | |
| L2.2.2 | Along X, the cavity takes the board plus the receptacle overhang and the antenna free space. | inspection | inner X length between the end walls at board height >= 54.4 + 1.0 + 0.5 + 8.0 = 63.9 (recomputed from the declared layout) | 2 | |
| L3.2.2.1 | Inner X length. | inspection | >= 63.9 | 2 | |

### L1.3 The board is held without screws, with limited float

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | At least three support pads under the PCB, outside the pin-tail strips, their tops coplanar and under the board. | inspection | count >= 3; each patch area >= 4.0 mm2; top-plane spread <= 0.10; pad tops within 0.10 of `PCB_BOTTOM`; the support polygon contains the board centroid | 3 | G5 |
| L3.3.1.1 | Number and patch area of pads in the H-SUP zones. | inspection | >= 3; each >= 4.0 mm2 | 3 | G5 |
| L3.3.1.2 | Pad top planarity and height. | inspection | spread <= 0.10; within 0.10 of `PCB_BOTTOM` | 2 | |
| L3.3.1.3 | The board's centroid projects inside the polygon through the pad centres. | analysis | true | 3 | G5 |
| L2.3.2 | Float limits (the board is captured, not loose): along X, across Y, and along Z. | analysis | float(X) <= 1.0; float(Y) <= 0.6; float(Z) <= 0.5 | 3 | G5 |
| L3.3.2.1 | float(X) from the seated pose, lid closed. | analysis | <= 1.0 | 3 | G5 |
| L3.3.2.2 | float(Y), lid closed. | analysis | <= 0.6 | 3 | G5 |
| L3.3.2.3 | float(Z), lid closed. | analysis | <= 0.5 | 3 | G5 |
| L2.3.3 | At least two retention ribs press down over the PCB top at the USB end, inside the H-TOP zones, on both long edges. | inspection | count >= 2, one per long edge; rib underside 0.1 to 0.3 above `PCB_TOP`; each patch >= 2.0 mm2 | 2 | |
| L3.3.3.1 | Retention rib count, position and height above the PCB top. | inspection | as stated | 2 | |
| L2.3.4 | Side stops on both long edges and end stops at both short edges, inside their hold zones. | inspection | gap to the board edge 0.1 to 0.3 on each; at least one stop per edge | 2 | |
| L3.3.4.1 | Gap from the board edge to its nearest stop: -Y, +Y, -X, +X. | inspection | 0.1 <= gap <= 0.3 each (the float limits of L2.3.2 follow) | 2 | |
| L2.3.5 | No feature passes through the board and nothing but the pads touches the PCB underside. | analysis | penetration of ALL into the PCB volume <= 0.01 mm3; contact with M-ESP only on pad tops | 2 | |
| L3.3.5.1 | Penetration into M-ESP. | analysis | <= 0.01 mm3 | 2 | |

### L1.4 Clearance above and below the board

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Lid closed: no body enters the zone above the board (pins 8.5 plus 0.5), except the retention ribs in H-TOP. | analysis | clear_of(ALL, V-KO-TOP, 0.0) | 3 | G2 |
| L3.4.1.1 | Top keep-out clear. | analysis | d >= 0.0 | 3 | G2 |
| L3.4.1.2 | Lid plate underside height (own-model proxy; the lip and the ribs excluded). | inspection | Z >= 10.6 | 2 | |
| L2.4.2 | No body enters the solder-side zone (pin tails 3.0 plus 0.3), except the pads in H-SUP. | analysis | clear_of(ALL, V-KO-BOT, 0.0) | 3 | G2 |
| L3.4.2.1 | Bottom keep-out clear. | analysis | d >= 0.0 | 3 | G2 |
| L3.4.2.2 | Floor top below the PCB underside. | inspection | 3.3 <= distance <= 10.0 | 2 | |

### L1.5 A micro-USB plug seats through the end-wall opening with the lid on

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Lid closed: the plug pushes in to full mate and pulls out without touching the box. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 | G3 |
| L3.5.1.1 | USB plug envelope clear. | test | d >= 0.30 | 3 | G3 |
| L3.5.1.2 | Physical: print, close, plug in the owner's cable. | test | clicks in fully, 3 of 3 tries | 2 | optional |
| L2.5.2 | The opening is not oversized: it stays within 1.5 of the plug envelope on every side. | analysis | inside(V-AP-USB, V-USB-PLUG offset 1.5, 0.0) | 2 | |
| L3.5.2.1 | Opening within the grown envelope (defaults: opening <= 13.0 x 10.0). | analysis | d >= 0.0 | 2 | |
| L2.5.3 | Exactly one opening in the end wall at -X, and none in any other wall. | inspection | V-AP-USB has 1 connected region | 2 | |
| L3.5.3.1 | Opening count in the -X wall. | inspection | 1 | 2 | |
| L2.5.4 | Enough wall around the opening. | analysis | ligament to the wall edges, floor top, rim and seam >= 1.5 | 1 | |
| L3.5.4.1 | Minimum ligament around the opening. | analysis | >= 1.5 | 1 | |

### L1.6 The antenna end has 8 mm of free space and no material above the module

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | No printed body (wall, lid plate, lip, rib or stop) enters V-ANT. | analysis | clear_of(ALL, V-ANT, 0.0) | 3 | G4 |
| L3.6.1.1 | Antenna free space clear. | analysis | d >= 0.0 (penetration <= 0.01 mm3) | 3 | G4 |
| L2.6.2 | At least 8.0 of free length beyond the board end. | inspection | first printed surface at X > 54.4 within Y 0 to 27.9, Z 1.6 to 9.7 is at X >= 62.4 | 3 | G4 |
| L3.6.2.1 | Free length from `EDGE_ANTENNA` to the nearest surface above the board top level. | inspection | >= 8.0 | 3 | G4 |
| L2.6.3 | Nothing above the module: the lid underside over X 48.4 to 62.4 is higher than the antenna zone. | analysis | lid underside (outside the lip) at Z >= 9.7 over V-ANT's plan | 2 | |
| L3.6.3.1 | Lid underside height over the antenna zone. | analysis | >= 9.7 | 2 | |
| L2.6.4 | The free space is not wastefully long. | inspection | free length from the board end to the end wall <= 12.0 | 1 | |
| L3.6.4.1 | Free length. | inspection | 8.0 <= L <= 12.0 | 1 | |

### L1.7 A removable lid, locating on the base with a sliding fit

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Base and lid are separate bodies, each one connected body, not interpenetrating when closed. | analysis | BASE 1 shell; LID 1 shell; BASE and LID intersection <= 1.0 mm3 | 3 | G1 |
| L3.7.1.1 | Shell count per body. | analysis | 1; 1 | 3 | G1 |
| L3.7.1.2 | Base-lid intersection, closed (penetration only). | analysis | <= 1.0 mm3 | 3 | G1 |
| L2.7.2 | A continuous lip on the lid underside fits inside the base cavity faces. | inspection | lip-to-wall gap 0.15 to 0.35 on all four sides; lip height (engagement) 1.0 to 2.0; lip thickness >= 0.8 | 2 | |
| L3.7.2.1 | Lip-to-wall gap, all locating faces. | inspection | 0.15 <= gap <= 0.35 | 2 | |
| L3.7.2.2 | Lip engagement depth. | inspection | 1.0 <= h <= 2.0 | 1 | |
| L2.7.3 | The lid plate covers the base outline. | inspection | lid plan outline contains the base outline minus 0.5; overhang <= 3.0 on every side | 2 | |
| L3.7.3.1 | Outline containment and overhang per side. | inspection | as stated | 2 | |
| L2.7.4 | The closed seam is tight. | inspection | seam gap <= 0.5 on all four sides | 1 | |
| L3.7.4.1 | Seam gap. | inspection | <= 0.5 | 1 | |

### L1.8 The lid snaps on and can be removed by hand

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | At least two snap hooks, on two opposite walls, at least one on each. | inspection | count >= 2; hooks on both of two opposite walls | 3 | G6 |
| L3.8.1.1 | Hook count and walls. | inspection | >= 2; two opposite walls | 3 | G6 |
| L2.8.2 | Hook geometry: engagement (undercut overlap in plan), arm thickness, free length, hook width. | inspection | undercut 0.4 to 1.0; arm thickness 1.2 to 2.0; arm free length >= 9.0; hook width >= 5.0 | 2 | |
| L3.8.2.1 | Undercut overlap of each tooth with its catch. | inspection | 0.4 <= u <= 1.0 | 2 | |
| L3.8.2.2 | Arm thickness and free length. | inspection | 1.2 <= t <= 2.0; L >= 9.0 | 2 | |
| L2.8.3 | Faces printable and removable: retention face inclined 45 to 65 degrees from horizontal; lead-in face 20 to 40 degrees. | inspection | as stated | 2 | |
| L3.8.3.1 | Face angles of tooth and ridge. | inspection | retention 45 to 65; lead-in 20 to 40 | 2 | |
| L2.8.4 | Flex within the strain limit (A8). | analysis | eps = 1.5 t (u + 0.1) / L^2 <= 0.020 | 3 | |
| L3.8.4.1 | Strain per hook, from the measured t, u and L. | analysis | <= 2.0 percent | 3 | |
| L2.8.5 | The hooks are engaged in the closed pose: lifting the lid by 0.3 along +Z makes every tooth penetrate its catch. | analysis | lift LID +Z 0.3: penetration >= 0.05 mm3 at every hook | 3 | G6 |
| L3.8.5.1 | Lift-engagement test at each hook. | analysis | every hook >= 0.05 mm3 | 3 | G6 |
| L3.8.5.2 | Physical: hold the closed box upside down, shake, open and close 10 times. | test | lid stays on; nothing cracks | 2 | optional |

### L1.9 Closed, with 2.0 to 4.0 mm walls

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The only opening is the USB opening (the lid seam and the catch recesses are not openings). | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into V-CAVITY | 2 | |
| L3.9.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 | |
| L2.9.2 | Walls, floor and lid plate are 2.0 to 4.0 thick. | inspection | each in [2.0, 4.0] | 2 | |
| L3.9.2.1 | Each side wall's median thickness (ray casting away from features). | inspection | 2.0 <= t <= 4.0 | 2 | |
| L3.9.2.2 | Floor thickness. | inspection | 2.0 <= t <= 4.0 | 2 | |
| L3.9.2.3 | Lid plate thickness. | inspection | 2.0 <= t <= 4.0 | 2 | |
| L2.9.3 | Each wall joins the floor along its length. | analysis | contact >= 90 percent of wall length x thickness (less the opening that reaches the floor) | 2 | |
| L3.9.3.1 | Wall-to-floor contact. | analysis | >= 0.9 x L x t | 2 | |

### L1.10 Both parts print without supports

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | In its stated print orientation (F5), no unsupported overhang steeper than 45 degrees from vertical, except round holes Ø <= 12 in vertical walls and bridges <= 15. | analysis | 0 offending faces (area > 1 mm2) | 2 | |
| L3.10.1.1 | Overhang and bridge scan per part (E1 rubric 3.6). | analysis | 0 patches | 2 | |
| L2.10.2 | Each part's mesh is manifold and a single shell. | analysis | 1 shell; manifold3d accepts it | 3 | G1 |
| L3.10.2.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.10.3 | Each part rests on a flat face. | analysis | bed contact >= 50 percent of the plan bounding box | 1 | |
| L3.10.3.1 | Bed contact per part. | analysis | >= 50 percent | 1 | |
| L2.10.4 | No feature thinner than 0.8; mating clearances >= 0.15. | analysis | min thickness >= 0.8; min mating gap >= 0.15 | 1 | |
| L3.10.4.1 | Thin-feature and mating-gap scan. | analysis | as stated | 1 | |
| L2.10.5 | Each part fits a 200 x 200 x 200 build volume. | inspection | bounding box <= 200 per axis | 1 | |
| L3.10.5.1 | Bounding box per part. | inspection | <= 200 per axis | 1 | |

### L1.11 Compact and stable: at most 75 x 45 x 25, flat on a table

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Closed outside size. | inspection | X <= 75.0, Y <= 45.0, Z <= 25.0 (X the board's long axis) | 1 | |
| L3.11.1.1 | Assembly bounding box. | inspection | as stated | 1 | |
| L2.11.2 | It stands on its base without tipping, also under a 0.5 N sideways pull at the port. | analysis | stable at 5 degrees tilt; restoring moment > tipping moment (mass 40 g) | 1 | |
| L3.11.2.1 | `stable` at 5 degrees; tipping margin at the USB opening centre. | analysis | passes; margin > 0 | 1 | |
| L2.11.3 | Flat underside. | inspection | flatness <= 0.2; nothing below the floor except equal feet <= 3.0 | 1 | |
| L3.11.3.1 | Underside planarity. | inspection | as stated | 1 | |

### L1.12 The board drops in and the lid closes

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | Lid off: the board (receptacle included) drops straight down (-Z) onto the pads without touching anything. | test | clear_of(BASE, V-INSTALL, 0.2) with the H-SUP columns excluded | 2 | |
| L3.12.1.1 | Installation path clear. | test | d >= 0.20 | 2 | |
| L2.12.2 | The lid lowers straight onto the base from 10.0 above: only the hook teeth and the catch ridges meet (they flex), and the ribs clear the board top. | test | lid sweep -Z, 1.0 mm steps: penetration outside the hook teeth and catch ridges <= 0.01 mm3; clear_of(LID, M-ESP, 0.1) | 2 | |
| L3.12.2.1 | Lid lowering sweep. | test | as stated | 2 | |
| L2.12.3 | Removing the lid does not release the board's retention in a way that lets it fall out: with the lid off the board still sits on the pads and stops. | inspection | board seated on pads with float(X), float(Y) within L2.3.2 (lid off) | 1 | |
| L3.12.3.1 | float(X), float(Y), lid off. | analysis | X <= 1.0; Y <= 0.6 | 1 | |

### L1.13 The design package says what was built, and its own claims are true

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | The package holds: `base.stl`, `lid.stl` (closed assembly pose, mm), the `.scad` source, `layout.json` (L2.1.1) and the agent's own clearance report. | inspection | all present and readable | 3 | G0 |
| L3.13.1.1 | Files present and parse; STLs in mm: each part's largest bounding-box axis is 20 to 200. | inspection | true | 3 | G0 |
| L3.13.1.2 | The declared layout verifies under the seating rule (section 2.3). | analysis | board on pad tops <= 0.10; stops within the hold zones | 3 | |
| L2.13.2 | The agent's own report agrees with the judge's measurements. | analysis | for every clear_of / inside L3 the agent reports, same pass/fail and \|d_agent - d_judge\| <= 0.10 | 1 | |
| L3.13.2.1 | Self-report vs judge. | analysis | 100 percent agreement within 0.10 | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 13 |
| L2 | 45 |
| L3 | 62 (2 physical) |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.1.1.1, L3.13.1.1);
**G1** manifold and two separate bodies (L3.10.2.1, L3.7.1.1, L3.7.1.2); **G2** board fit and
keep-outs (L3.2.1.1, L3.4.1.1, L3.4.2.1); **G3** the USB plug seats (L3.5.1.1); **G4** the antenna
space is free (L3.6.1.1, L3.6.2.1); **G5** the board is held (L3.3.1.1, L3.3.1.3, L3.3.2.1, L3.3.2.2,
L3.3.2.3); **G6** the lid snaps (L3.8.1.1, L3.8.5.1).

---

## 6. Feasibility: a design that meets every number

One concrete design, hand-checked against the bands (board frame, mm; the loop does not get it).

**Base.** Outer X -3.9 to 64.8, Y -4.2 to 32.1, Z -5.9 to 11.7. Walls 2.4, floor 2.4 (Z -5.9 to -3.5).
Cavity X -1.5 to 62.4 (inner length 63.9 = the L3.2.2.1 minimum), Y -1.8 to 29.7, floor top Z -3.5, rim at
Z 11.7. Board clearance to the side walls 1.8 and to the USB wall 0.5 at the receptacle front; 8.0 to the
far wall (62.4 - 54.4), the free length of L3.6.2.1. The floor top is 3.5 below the PCB underside (>= 3.3).

**USB opening.** In the wall X -3.9 to -1.5: Y 8.65 to 19.25 (10.6 wide), Z -0.75 to 6.85 (7.6 high),
centred on `USB_MOUTH` (Y 13.95, Z 3.05): the overmold (10.0 x 7.0, Y 8.95 to 18.95, Z -0.45 to 6.55)
clears every edge by 0.3, so d = 0.30; the opening is 3.0 wider and 3.0 higher than the plug, so it is
inside the plug envelope grown by 1.5. Ligament below the opening 2.75, above it 4.85 (to the rim).

**Holding.** Four pads 2.6 x 2.5 (6.5 mm2) at X 0.2 to 2.8 / 51.6 to 54.4, Y 0 to 2.5 / 25.4 to 27.9, tops
at Z 0 (outside the tail strips X 3.07 to 51.33); the support polygon is 54.2 x 27.9 and contains the
centroid. Side stops: ribs Z -3.5 to 1.4 at the same X ranges, at Y -1.8 to -0.25 and 28.15 to 29.7 (gap
0.25 each side, float(Y) = 0.5 <= 0.6). End stops: USB-end corner blocks X -1.5 to -0.25 at Y -1.8 to 5.0
and 22.9 to 29.7 (gap 0.25); antenna-end blocks X 54.65 to 56.6, Y 0 to 2.5 and 25.4 to 27.9, Z to 1.4
(gap 0.25, below V-ANT's Z 1.6): float(X) = 0.5 <= 1.0. Retention: two lid ribs X 0.3 to 2.8, Y 0.2
to 1.8 and 26.1 to 27.7, Z 1.8 to 11.7 (underside 0.2 above `PCB_TOP`, so float(Z) = 0.2 <= 0.5). Ribs clear
the header body (starts X 3.07) by 0.27. Install sweep gaps are 0.25 >= 0.2.

**Lid.** Plate Z 11.7 to 14.1 (2.4 thick), plan X -3.9 to 64.8, Y -6.7 to 34.6 (the hook arms stand
outside the base). Lip: Z 9.9 to 11.7 (engagement 1.8), 1.0 thick, outer faces 0.25 inside the cavity
faces: X -1.25 to 62.15, Y -1.55 to 29.45; inner faces X -0.25 / 61.15, Y -0.55 / 28.45, so the lip stays
off the board footprint (X 0 to 54.4, Y 0 to 27.9) and stays 0.2 above V-ANT's top plane Z 9.7 (d = 0.2).
Lid underside Z 11.7 >= 10.6 (pins) and >= 9.7 (antenna). Closed height 20.0.

**Snap hooks.** Four hooks, two per long wall, at X 10 to 18 and 41 to 49 (8 wide): arm 1.5 thick, 10.0
free length (Z 11.7 down to 1.7), outside the base walls with the arm inner face 1.0 outside the wall
(Y -5.2; wall face Y -4.2); a tooth protrudes 0.75 inward over Z 1.7 to 3.2 (retention face 50 degrees from
horizontal, lead-in face 30 degrees); catch ridge on the wall outside, protruding 0.7 (to Y -4.9) with
its underside at 50 degrees and top at 30 degrees. Tooth tip at Y -4.45: undercut u = 0.45 (in 0.4 to 1.0),
strain 1.5 x 1.5 x (0.45 + 0.1) / 10^2 = 1.24 percent <= 2.0. Lift 0.3 makes each tooth penetrate its
ridge.

**Size and print.** Closed bounding box X -3.9 to 64.8 (68.7), Y -6.7 to 34.6 (41.3), Z -5.9 to 14.1
(20.0): within 75 x 45 x 25. Base prints open side up (the USB opening is a 10.6 wide bridge, <= 15; the
ridge undersides are 50 degrees); lid prints outer face down (arms, ribs, lip rise; tooth retention face
50 degrees). Bed contact: base about 85 percent, lid about 95 percent.

---

## 7. Traceability

| L1 | Owner need (from the brief) | L2 | L3 | JSON L1 | Words in the brief it comes from |
|---|---|---|---|---|---|
| L1.1 | Board orientation | L2.1.1-L2.1.3 | L3.1.1.1, L3.1.2.1, L3.1.3.1-2 | L1.1 | "micro-USB end", "antenna end" |
| L1.2 | Board fits | L2.2.1-L2.2.2 | L3.2.1.1-3, L3.2.2.1 | L1.2 | "54.4 x 27.9 mm" |
| L1.3 | Held without holes | L2.3.1-L2.3.5 | L3.3.1.1-3, L3.3.2.1-3, L3.3.3.1, L3.3.4.1, L3.3.5.1 | L1.3 | "no mounting holes, so the box must hold it with ribs or clips" |
| L1.4 | Component clearance | L2.4.1-L2.4.2 | L3.4.1.1-2, L3.4.2.1-2 | L1.4 | implied (pin headers) |
| L1.5 | USB access | L2.5.1-L2.5.4 | L3.5.1.1-2, L3.5.2.1, L3.5.3.1, L3.5.4.1 | L1.5 | "micro-USB end must be open for a cable" |
| L1.6 | Antenna space | L2.6.1-L2.6.4 | L3.6.1.1, L3.6.2.1, L3.6.3.1, L3.6.4.1 | L1.6 | "8 mm of empty space with no wall material above the module" |
| L1.7 | Removable lid | L2.7.1-L2.7.4 | L3.7.1.1-2, L3.7.2.1-2, L3.7.3.1, L3.7.4.1 | L1.7 | "Lid is removable and printed separately" |
| L1.8 | Snap closure | L2.8.1-L2.8.5 | L3.8.1.1, L3.8.2.1-2, L3.8.3.1, L3.8.4.1, L3.8.5.1-2 | L1.8 | capability list: snap_fit |
| L1.9 | Protection | L2.9.1-L2.9.3 | L3.9.1.1, L3.9.2.1-3, L3.9.3.1 | L1.9 | "box" |
| L1.10 | Printable | L2.10.1-L2.10.5 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1, L3.10.5.1 | L1.10 | "printed separately" (FDM) |
| L1.11 | Compact, stable | L2.11.1-L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | L1.11 | implied (A10) |
| L1.12 | Assembly | L2.12.1-L2.12.3 | L3.12.1.1, L3.12.2.1, L3.12.3.1 | L1.12 | implied |
| L1.13 | Evidence | L2.13.1-L2.13.2 | L3.13.1.1-2, L3.13.2.1 | L1.13 | needed by the judge |

---

## 8. Grading supplement (design-specific; `generalize/rubric.md` did not exist when this was written)

Procedure, recipes and report format are those of `benchmarks/enclosure/rubric.md` (sections 2, 3 and
5), applied to the base and lid STLs, with these specifics:

1. **Inputs.** `base.stl`, `lid.stl` (closed pose, mm), `.scad`, `layout.json`, self-report, renders. The
   judge does not use the agent's code or transcript, earlier verdicts, or `benchmarks/heldout.json`.
2. **Normalise the frame** (1.1): USB end at -X, floor below the PCB underside plane. Record the transform.
3. **Build references independently** from the catalogue (M-ESP, M-PLUG-USB), then the V- envelopes and
   hold zones (2.2), then sanity checks R1 to R6 and the seating rule (2.3).
4. **Recipes.** `clear_of`, `inside` and apertures as E1 rubric 3.2 to 3.4. `float`: translate M-ESP in
   0.05 mm steps and bisect to 0.02, summing both directions. Hook measurements: slice each hook at
   mid-width in the Y-Z plane, fit the tooth and ridge faces (angles from horizontal), take the arm's
   thickness and free length from the slice. The lift test translates LID +Z by 0.3 and reports the
   intersection volume with BASE at each hook.
5. **Classes.** WRONG = any gate (G0 to G6) fails. MINOR = no gate fails but a weight-3 L3 fails.
   CORRECT = no gate fails and every weight-3 L3 passes. **MEETS** = CORRECT and every applicable
   non-physical L3 of weight 1 and 2 passes. UNVERIFIED counts as FAIL; physical L3s are N/A unless a
   print was made. Report the weighted score and the worst normalised margin among weight-3 L3s.
6. **Precedence.** The plug-seating and antenna-space checks (L3.5.1.1, L3.6.1.1) outrank everything
   about opening size and compactness. The numbers in this file beat `part.json`: if a catalogue value
   disagrees, build from this file and record a defect on the requirement the stale value breaks, with
   where = the part.json field. Designed contact (1.4) is never interference. Never relax a criterion,
   never round in the design's favour beyond e, never infer a pass from a render.
7. **WHERE a defect is.** One entry per failed or UNVERIFIED L3, most severe first (gates, then weight
   3, 2, 1): `req` (L3, L2, L1), `status`, `body` (base, lid, both, layout), `feature` (named by
   function and SCAD name, for example "USB opening in the -X end wall (`usb_cutout`)"), `face` (surface
   and outward normal), `location` (board-frame coordinates, a point or a box), `measured` / `limit` /
   `margin`, `reference` (the M- or V- involved and its datum), `render`, `evidence` (saved defect
   STL), `needed` (a numeric target, never a design instruction). Group L3s that fail for one
   geometric reason, keeping every id.
8. **Measured-values table (always filled in).**

| Quantity | Limit | Measured |
|---|---|---|
| Board clearance outside / inside the hold zones (L3.2.1.x), mm | >= 0.5 / >= 0.2 | |
| Inner X length (L3.2.2.1), mm | >= 63.9 | |
| Pads: count; area; spread (L3.3.1.x) | >= 3; >= 4.0 mm2; <= 0.10 | |
| float X / Y / Z (L3.3.2.x), mm | <= 1.0 / <= 0.6 / <= 0.5 | |
| Retention ribs: count; height above PCB top (L3.3.3.1), mm | >= 2; 0.1 to 0.3 | |
| Top / bottom keep-out d (L3.4.1.1, L3.4.2.1), mm | >= 0 / >= 0 | |
| USB plug d; opening oversize d (L3.5.1.1, L3.5.2.1), mm | >= 0.3; >= 0 | |
| USB opening W x H and centre (board frame), mm | (<= 13 x 10 with defaults) | |
| Opening count in the -X wall (L3.5.3.1); unlisted (L3.9.1.1) | 1; 0 | |
| V-ANT d; free length; lid height over the zone (L3.6.x), mm | >= 0; >= 8.0; >= 9.7 | |
| Lip gap; engagement (L3.7.2.x), mm | 0.15 to 0.35; 1.0 to 2.0 | |
| Hooks: count; undercut; t; L; strain (L3.8.x) | >= 2; 0.4 to 1.0; 1.2 to 2.0; >= 9.0; <= 2.0 percent | |
| Hook angles: retention / lead-in (L3.8.3.1), deg | 45 to 65 / 20 to 40 | |
| Lift-test intersection per hook (L3.8.5.1), mm3 | >= 0.05 | |
| Wall / floor / lid thickness (L3.9.2.x), mm | 2.0 to 4.0 | |
| Shells base / lid (L3.10.2.1) | 1 / 1 | |
| Overhang patches; bed contact (L3.10.x) | 0; >= 50 percent | |
| Closed envelope X x Y x Z (L3.11.1.1), mm | <= 75 x 45 x 25 | |
| Install sweep d; lid lowering (L3.12.x) | >= 0.2; as stated | |
| Self-report agreement (L3.13.2.1) | 100 percent within 0.10 | |

---

## Audit

Adversarial audit (second agent). `esp32_devkitc_v4` and `plug_microusb_b` load and pass `parts.gate`. L1 = 13, L2 = 45, L3 = 62 recounted from the tables (match section 5 and the traceability table). Every derived number was recomputed from `part.json`: receptacle X -1.0 to 4.9 / Y 10.2 to 17.7; module X 28.9 to 54.4; header strips X 3.07 to 51.33, Y -0.02 to 2.52 and 25.38 to 27.92; V-KO-TOP Z to 10.6; V-KO-BOT to -3.3; V-ANT X 48.4 to 62.4, Z 1.6 to 9.7; plug envelopes. Section 6 was walked against every gate and band (cavity, USB opening ligaments and 0.30 clearance, pads, float X/Y/Z = 0.5/0.5/0.2, lip fit, hook strain 1.24 percent, lift test, install and lowering sweeps, print overhangs, 68.7 x 41.3 x 20.0 envelope); no contradiction between rows was found.

| # | Defect found | Fix |
|---|---|---|
| 1 | The esp32 part's connector mates `plug_microusb_b`, which only existed in `benchmarks/enclosure/parts`; `Catalog.cross_references()` on `benchmarks/generalize/parts` reported it missing (also for `rpi_zero2w`), so a run with `--parts benchmarks/generalize/parts` could not load the plug. | Copied the identical `plug_microusb_b/part.json` into `benchmarks/generalize/parts`; cross-references now empty. |
| 2 | Feasibility lip at Z 9.7 to 11.7 touched V-ANT's top plane (d = 0.0) and put a surface at X 61.15 inside "first printed surface beyond the board end within Z 1.6 to 9.7" (L3.6.2.1, gate G4) on the boundary plane: a measurement-dependent pass on a gate. | Lip is now Z 9.9 to 11.7 (engagement 1.8, still in 1.0 to 2.0); d to V-ANT = 0.2. |
| 3 | Numbers a gate or weight 2-3 row needs but the agent was never told: USB plug clearance 0.3 (G3), receptacle-to-wall gap 0.5 to 3.0 and 1.5 ligament, pad count and area (G5), pad level, rib height 0.1 to 0.3, stop gaps 0.1 to 0.3, antenna free length <= 12.0, lip fit 0.15 to 0.35 / 1.0 to 2.0 / 0.8, hook arm 1.2 to 2.0 / 9.0 / 5.0, undercut <= 1.0, face angles, lift-engagement (G6), install 0.2, 0.2 holding clearance, printability limits, 0.10 self-report. | Added to the L1 texts in `design.json` (L1.2, L1.3, L1.5, L1.6, L1.7, L1.8, L1.10, L1.12, L1.13). No L3 band changed. |

Residual uncertainty: the header orientation (pins up, 8.5 mm) and the receptacle overhang are catalogue assumptions, repeated in the request text so the agent is told them; the retention rib sits 0.27 mm from the first header body, a thin margin that depends on the assumed header offset (+/-0.5 per A1).
