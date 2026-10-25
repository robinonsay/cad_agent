# G46 Handheld Pico game console: requirements (L1 / L2 / L3) — HELD-OUT

A generalization design (held-out split) in the style of E1-01 (`benchmarks/enclosure/requirements.md`).
It is a **combination** design: it uses abilities that the train designs exercise one at a time (windows,
button actuation, battery retention, stacked boards, plug openings, snap fits, multi-body assembly, datum
placement, a panel-mount switch). Do not train or tune on it. The machine-readable request (L1 only,
`dev.json` format) is `design.json` next to this file. `benchmarks/generalize/rubric.md` did not exist
when this file was written, so section 9 holds the design-specific grading rules; measuring recipes are those of
`benchmarks/enclosure/rubric.md` section 3 (load, `clear_of`, `inside`, apertures, slices, ray casting, overhang
scan).

**Owner's request (verbatim):** "A handheld device 110 x 60 x 22 mm: Pico 2 on top of a 5 x 34 x 50 mm
LiPo and TP4056 board, an OLED window in front, six tactile buttons around it, a slide power switch and a
USB-C port on the bottom end. The two halves snap together and the battery must not press on any solder joints."

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering requirement with
numbers. L3 is a concrete Python check on the delivered STLs. Every row has a method (inspection, analysis,
demonstration, test, human), a pass/fail criterion with a number and a tolerance, a weight (3 = critical, 2 =
major, 1 = minor) and a gate mark (G0 to G5) where a failure makes the design WRONG. Numbers that come from an
assumption (section 3) are provisional until the owner confirms them. Do not relax a criterion because the agent
fails it.

---

## 1. Frame, tolerances and designed contact

- **Console frame:** X along the 110 mm length, Y across the 60 mm width, Z through the 22 mm thickness. **The bottom
  end is −X** (the short end with the USB-C opening and the switch). **The front face is +Z** (the face with the
  window and the buttons); the back face is Z = 0. A delivery mirrored or rotated is normalised into this frame by
  rotations by multiples of 90 degrees and mirroring only (rubric: the end wall with the USB-C opening at −X, the
  window face at +Z); that is never penalised. Units mm. The two shells are the **FRONT** half (window, button holes,
  posts) and the **BACK** half (floor, end and side walls); CAPS are the six button caps; ALL = FRONT ∪ BACK ∪ CAPS in the closed pose.
- **Measurement tolerances ε:** length, distance and clearance 0.02; diameter 0.03 (largest inscribed circle for
  holes, smallest enclosing circle for bosses and posts); angle 0.5 degrees; volume 0.01 mm³. A value passes if it
  meets its limit to within ε.
- **Designed contact (this design).** These pairs are never interference (only penetration above 0.01 mm³ counts;
  a distance of zero is a pass):
  1. the OLED glass against the front face's inner side, and the OLED PCB in its pocket and hooks;
  2. each button body on its seat and in its pocket walls; each cap's flange on the front face's inner side;
  3. the Pico's top face on the post bottoms, an M2 screw in its pilot, and the Pico's underside on the support
     ledges at its USB-end corners (A5: those two small squares are joint-free);
  4. the TP4056 board on its rails and ribs; the LiPo on the floor and its ribs; the switch body on the floor, wall and ribs;
  5. a snap hook on the catch it engages; the lap tongue in the lap rebate (a clearance is required, L3.10.2.1); FRONT on BACK at the seam plane;
  6. the plug and the handle sweep, the solder zones, the pin zone, the keep-outs are **not** designed contact: they must stay free.
- **Checks used** (`enclosure/requirements.md` 1.3, recipes in `enclosure/rubric.md` 3.2 to 3.4): `clear_of(bodies,
  volume, clearance)` (pass: penetration ≤ 0.01 mm³ and d ≥ clearance − ε), `inside(volume, cavity, clearance)`,
  aperture enumeration and the 2.0 mm probe. The grader builds all reference models and volumes itself from the
  catalogue and the declared layout; a design never builds or edits them for grading.
- **`inside` and supports.** `inside(volume, cavity, clearance)` is measured to the cavity's wall and face surfaces (end walls, side walls, front
  face, floor); posts, ledges, ribs, rails and hooks are supports and are excluded, so a part resting on them is not failed for touching them.
- **Capture** (FD2): a part is "captured within d" in a direction if translating its reference model by d along that axis
  direction makes it intersect the printed bodies of the closed assembly (excluding itself) by more than 0.01 mm³.
  Resting on a support counts as captured at 0.

## 2. Reference models and envelopes

Positions are those the design declares in `layout.json` (L3.14.1.2 verifies them); section 7 gives one valid layout.
Datums come from the catalogue `part.json` files.

| Name | What | Source | Definition (console frame, mm) | Datums |
|---|---|---|---|---|
| **M-TP** | TP4056 USB-C charger board | catalogue `tp4056_usbc_module` (PCB 26.0 × 17.0 × 1.0, receptacle 8.94 × 7.3 × 3.26 overhanging 1.0, four corner pads 2.0 from the edges) | USB end toward −X (`USB_AXIS` along −X), components up | `USB_MOUTH`, `USB_AXIS`, `PADS`, `PCB_BOTTOM`, `PCB_TOP` |
| **M-LIPO** | LiPo pouch cell | catalogue `lipo_503450` (50 × 34 × 5.0, tabs 4.0 long, 10.0 wide on a short edge) | long side along X, tabs toward −X (the charger) | `TABS`, `TAB_DIR`, `BOTTOM`, `TOP`, `SWELL_TOP` |
| **V-SWELL** | the swollen cell's extra layer | envelope | the pouch footprint from `TOP` up to `SWELL_TOP` (swell fraction 0.10 on the top face only, A4) | `TOP`, `SWELL_TOP` |
| **M-PICO** | the Pico 2 | catalogue `rpi_pico2` (PCB 51 × 21 × 1, receptacle 8.0 × 5.5 × 2.8 overhanging 1.3, holes Ø2.1 at 47.0 × 11.4, parts up to 1.5) | components up, stacked above the LiPo and TP4056 | `PCB_BOTTOM`, `PCB_TOP`, `HOLE` |
| **V-PICO** | Pico with receptacle | envelope | M-PICO bounding solids | `USB_MOUTH` |
| **V-PICO-TOP** | the Pico's top parts | envelope | PCB footprint minus Ø7.0 columns on the hole axes, from `PCB_TOP` up 1.5 (`top_parts_height`) | `PCB_TOP` |
| **M-OLED** | 0.96 inch OLED module | catalogue `oled_ssd1306_096` (PCB 27.3 × 27.8 × 1.2, glass 26.7 × 19.3 × 1.4 offset 5.0 from the header edge, holes Ø2.0, 4-pin header) | glass toward +Z, in front of the Pico; any 90° rotation about Z | `GLASS_TOP`, `ACTIVE_CENTER`, `VIEW_AXIS`, `PCB_BOTTOM`, `PINS` |
| **V-OLED-VIEW** | the viewing area | envelope | a 25.0 × 14.0 rectangle (`view_width` × `view_height`) centred on `ACTIVE_CENTER` in the `GLASS_TOP` plane, long side along the glass's long side, extruded 10.0 toward +Z | `ACTIVE_CENTER`, `GLASS_TOP` |
| **V-OLED-PINS** | header and solder zone | envelope | the 4-pin header footprint (4 × 2.54 by 2.5) centred on the `PINS` axes, from `PCB_BOTTOM` down 5.0 (pins 3.0 + solder 2.0, A6) | `PINS` |
| **M-BTN-1..6** | six tactile buttons | catalogue `button_tact_6mm` (body 6.0 × 6.0 × 3.8, plunger Ø3.5 × 0.5, travel 0.25, force 1.6 N) | plunger toward +Z | `BODY_TOP`, `PLUNGER_TOP`, `ACTUATOR_AXIS` |
| **M-SW** | slide switch | catalogue `slide_sk12d` (body 12.5 × 6.0 × 5.5, handle 3.0 × 3.0 × 4.0, travel 3.5, pins 3.0) | handle toward −X (`ACTUATOR_AXIS`), travel along Y (`TRAVEL_AXIS`) | `ACTUATOR_AXIS`, `TRAVEL_AXIS`, `HANDLE_CENTER`, `BODY_BOTTOM` |
| **V-SW-SWEEP** | handle swept area | envelope | the 3.0 × 3.0 handle section translated ±1.75 along `TRAVEL_AXIS` and extended along `ACTUATOR_AXIS` from the body face to 5.0 beyond the wall's outer face | `HANDLE_CENTER` |
| **V-SW-TERM** | switch terminal zone | envelope | the body's 12.5 × 6.0 footprint from `BODY_BOTTOM` inward 5.0 (A7) | `BODY_BOTTOM` |
| **M-PLUG-USBC**, **V-USB-PLUG** | USB-C cable plug and path | catalogue `plug_usbc` (shell 8.25 × 2.4, mated depth 6.65, exposed 1.0, overmold 12.4 × 6.5) | shell from 6.65 inside `USB_MOUTH` to 1.0 outside it; overmold swept out along `USB_AXIS` to 40 beyond the wall | `USB_MOUTH`, `USB_AXIS` |
| **V-SOLDER-TP** | charger pad zone | envelope | four Ø5.0 cylinders on the `PADS` axes from `PCB_BOTTOM` − 2.0 to `PCB_TOP` + 2.0 (`wire_clear` 2.0) | `PADS` |
| **V-SOLDER-TAB** | cell tab joint zone | envelope | a box along `TAB_DIR` from 2.0 beyond the pouch edge outward 6.0, 14.0 wide (tab 10.0 + 2 × 2.0) centred on `TABS`, from `BOTTOM` up to `SWELL_TOP` + 2.0 | `TABS`, `TAB_DIR` |
| **V-SOLDER-PICO** | Pico underside solder zone | envelope | the PCB footprint from `PCB_BOTTOM` down 1.5 (leads and fillets, A5), minus the two joint-free support squares | `PCB_BOTTOM` |
| **V-CAVITY**, **V-AP-USB**, **V-AP-OTHER** | internal void; openings in the −X wall; every other through-path into the void | computed | as `enclosure/rubric.md` 3.4; the window and the six button holes are listed openings | wall faces |
| **V-INSTALL-k** | install paths with the case open | envelope | for the Pico: its silhouette swept +Z from 12.0 below its seat to seated (FRONT only); for the cell and the TP4056: swept −Z from 15.0 above to seated (BACK only); for the switch: moved 4.0 inward, swept −Z from 15.0 above, then slid 4.0 toward the wall (BACK only); for the OLED: swept +Z from 8.0 below to seated (FRONT only) | each part's pose |
| **V-DRIVER-k** | screwdriver access to a Pico screw | envelope | Ø6.0 column on each post-hole axis from `PCB_BOTTOM` down 40, BACK removed | `HOLE` |

Sanity checks before grading (not L3s): R1 units (Pico PCB 51.0 × 21.0 ± 0.2; cell 50 × 34 × 5 ± 0.3; OLED PCB 27.3 × 27.8
± 0.3); R2 reference models do not collide with each other (L3.1.3.1); R3 the Pico lies above the cell and the OLED
above the Pico; R4 every V- envelope's datums equal the model datums it was built from.

**Seating rule (Pico).** The grader places M-PICO at the declared pose and verifies it: `PCB_TOP` lies on the post bottoms
(distance ≤ 0.10) and the posts' pilot axes are coaxial with the `HOLE` axes they serve (residual ≤ 0.25). If the declaration
fails, M-PICO is seated by that fit; if there are no posts, it is centred in the cavity above the cell.

## 3. Assumptions and open questions for the owner

| # | Question | Value chosen | Why / uncertainty |
|---|---|---|---|
| **A1** | Which end is "the bottom end"? | The −X short end (the one where the charger's USB-C and the switch are). The console is held with its long axis up; the front face (screen) is +Z. | "bottom end" of a handheld held upright. Uncertainty low: only X is renamed. |
| **A2** | Is the Pico's own micro-USB exposed? | **No.** Only the charger's USB-C is exposed. The Pico is programmed before the case is closed (BOOTSEL, lid off) or over its debug pins. | The request names one USB-C port. Uncertainty **medium**: if both ports are wanted, a second opening is needed. |
| **A3** | TP4056 board dimensions | PCB 26.0 × 17.0 × 1.0, USB-C receptacle 8.94 × 7.3 × 3.26 overhanging 1.0, pads 2.0 in from the corners, parts up to 1.8 above the PCB. | `tp4056_usbc_module/part.json`; vendors vary by ±1 mm. Uncertainty **high**: measure the owner's board. |
| **A4** | LiPo and swelling | 503450: 5.0 × 34 × 50 maximum, tabs 4.0 long and 10.0 wide on a short edge, pointing toward the charger. Swelling 10 percent, taken on the top face only, so `SWELL_TOP` is 0.5 above `TOP`. | `lipo_503450/part.json` and general LiPo guidance. Uncertainty medium. |
| **A5** | Where are the solder joints? | Charger pads: Ø5.0 zones, 2.0 above and below (the Ø5.0 is told in L1.9; the request text states the other zones). Cell tab joints: a zone from 2.0 beyond the pouch edge, 6.0 long, 14.0 wide. Pico: leads and fillets within 1.5 under the PCB (castellations along the long edges, receptacle legs). Two 3.0 × 1.6 squares at the Pico's USB-end corners are joint-free and may carry support ledges. The battery must keep 0.5 clear of these zones. | Not given. Uncertainty **high**; the owner should say where the wires go. |
| **A6** | OLED details | Hole inset and glass outline are from the notes in `oled_ssd1306_096/part.json` (assumed ±0.3); header pins 3.0 long plus 2.0 of solder below the PCB; viewing area 25.0 × 14.0. | Vendor drawing gives board, holes and active area only. Uncertainty medium. |
| **A7** | Buttons and switch | Six 6 × 6 tactile switches soldered with flying leads (wires are not graded), each pressed by a printed cap. SK12D switch with a 4.0 handle (variants 2 to 6), 2.0 of wire room behind its 3.0 pins. | `button_tact_6mm` and `slide_sk12d` part.json. Uncertainty medium. |
| **A8** | How is the Pico held? | At least two M2 self-tapping screws (`screw_m2_selftap`: pilot 1.6 to 1.8, engagement 5.0, post OD ≥ 5.0) from below into posts that hang from the front half, plus supports at its USB-end corners and ribs round its edges (captured within 1.0). The two holes beside its receptacle cannot take a post. | The Pico's holes at the USB end sit under its receptacle. Uncertainty medium. |
| **A9** | Snap fits | Cantilever hooks, strain limit 2.0 percent for PLA or PETG (strain = 1.5 · t · y / L²), engagement 0.3 to 0.8, arm length at least 6.0, root thickness at least 0.8. | Common FDM snap-fit guidance. Uncertainty medium. |
| **A10** | Walls | 2.0 to 3.0 for walls, floor and front face (about 5 perimeters at 0.4); the lap parts of the seam (the thinned halves) may be as thin as 0.85. | Handheld, so thinner than a desk box. Uncertainty low. |
| A11 | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed, no supports. Overhang rule 45°, bridges up to 15.0, round holes up to Ø12 and horizontal ledges up to 1.0 are exempt. FRONT is printed front face down, BACK floor down, caps flange down. | Common printer. |
| A12 | Wiring, protection | Wires are not modelled; the cell has its own protection or the owner's wiring has; no battery holder hardware. | Not stated. |
| A13 | Size | 110 × 60 × 22 means the two shells; caps stand proud on top of that (L3.4.2.3). Allowed 108.0 to 110.3 × 58.0 to 60.3 × 20.0 to 22.3. | The request gives one size. Uncertainty low. |
| A14 | Heat, vents | None needed (Pico plus OLED, well under 1 W). | Not stated. |

## 4. Fixed decisions (a choice was ambiguous; this is the one graded)

- **FD1 Frame.** As section 1: bottom end −X, front +Z, switch handle toward −X.
- **FD2 Capture.** As the Capture paragraph in section 1, with the 1.0 mm distance named in each row.
- **FD3 Stack order.** From the back: back wall, the LiPo and charger board (lower layer, side by side along X), the Pico stacked above the LiPo (it overlaps the charger board's plan only if the design chooses), the OLED, the front face.
- **FD4 Assembly order.** The front half carries the OLED, the caps and buttons and the Pico (assembled with the front half inner side up); the back half carries the cell, the charger board and the switch; the halves then snap together.
- **FD5 Seam.** A lap seam: a thin outer lap on one half and an inner tongue on the other, with the hooks on tabs inside the cavity.
- **FD6 Openings in the −X wall.** Exactly two: the USB-C opening and the switch slot.
- **FD7 Which half is which.** FRONT = the half holding the window; BACK = the other. Caps are separate bodies.

## 5. Requirements tree

### L1.1 Layout declared: lower layer (LiPo, charger), Pico above, OLED in front

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The layout is declared. | inspection | `layout.json` present, parses, names the TP4056, LiPo, Pico, OLED, six buttons, switch and USB-C plug (and `screw_m2_selftap`) from the catalogue with poses | 3 | |
| L3.1.1.1 | Layout parses and every catalogue id exists. | inspection | true | 3 | |
| L2.1.2 | The stack order is as FD3 and the Pico really lies over the cell. | inspection | Z order: `SWELL_TOP` of the LiPo < Pico `PCB_BOTTOM`; Pico top parts < OLED `PCB_BOTTOM`; Pico plan overlaps the LiPo plan by ≥ 50% of the Pico's area; the OLED plan overlaps the Pico plan by ≥ 25% of the OLED's | 3 | |
| L3.1.2.1 | Layer order along Z. | inspection | as L2.1.2 | 3 | |
| L3.1.2.2 | Plan overlaps. | inspection | as L2.1.2 | 2 | |
| L2.1.3 | The parts do not collide. | analysis | all reference models (including the six buttons) pairwise ≤ 0.01 mm³ | 3 | |
| L3.1.3.1 | Pairwise interference. | analysis | each pair ≤ 0.01 mm³ | 3 | |
| L2.1.4 | Directions. | inspection | `USB_AXIS` of M-TP within 1.0° of −X; switch `ACTUATOR_AXIS` within 1.0° of −X and `TRAVEL_AXIS` along Y; button plungers within 1.0° of +Z; OLED `VIEW_AXIS` within 1.0° of +Z | 2 | |
| L3.1.4.1 | Port and handle directions. | inspection | as L2.1.4 | 2 | |

### L1.2 Size and shape: 110 × 60 × 22, rounded corners

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Outside size of the shells (A13). | inspection | FRONT ∪ BACK bounding box: X 108.0 to 110.3, Y 58.0 to 60.3, Z 20.0 to 22.3 | 3 | |
| L3.2.1.1 | Shell bounding box. | inspection | as L2.2.1 (sketch: 110.0 × 60.0 × 22.0) | 3 | |
| L2.2.2 | Rounded vertical corners. | inspection | smallest enclosing arc radius of each outer vertical corner, slice at Z = 11: ≥ 3.0 | 1 | |
| L3.2.2.1 | Corner radius. | inspection | ≥ 3.0 at all four | 1 | |
| L2.2.3 | A flat back. | inspection | the back face (Z = 0) planarity ≤ 0.3 over at least 80% of its area | 1 | |
| L3.2.3.1 | Back-face planarity. | inspection | ≤ 0.3 | 1 | |

### L1.3 OLED window, seat and hold

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The window contains the viewing area, is centred, and is smaller than the glass. | inspection | the window outline (largest hole in the front face over the OLED) contains V-OLED-VIEW's section with margin ≥ 0.0; its centre is within 0.5 of `ACTIVE_CENTER` (in plan); in each direction it is at least 1.0 smaller than the glass outline (each side overlaps the glass by ≥ 0.5) | 3 | G4 |
| L3.3.1.1 | Window contains the viewing area, centred. | inspection | margin ≥ 0.0; offset ≤ 0.5 | 3 | G4 |
| L3.3.1.2 | Window smaller than the glass. | inspection | overlap ≥ 0.5 on all four sides | 2 | |
| L2.3.2 | The glass sits against the front face. | demonstration | distance between `GLASS_TOP` and the front face's inner side ≤ 0.3, with no penetration | 2 | |
| L3.3.2.1 | Glass seat. | demonstration | 0 ≤ gap ≤ 0.3 | 2 | |
| L2.3.3 | The OLED is held and does not penetrate. | demonstration | M-OLED ∩ ALL ≤ 0.01 mm³; captured within 1.0 in ±X, ±Y, −Z (+Z is the front face) | 3 | |
| L3.3.3.1 | No penetration of the OLED. | demonstration | ≤ 0.01 mm³ | 3 | |
| L3.3.3.2 | Capture of the OLED. | demonstration | all five hit | 2 | |
| L2.3.4 | The header zone and the Pico's top parts stay clear of the OLED. | analysis | clear_of(ALL, V-OLED-PINS, 0.0); clear_of(V-PICO-TOP, M-OLED ∪ V-OLED-PINS, 0.3) | 2 | |
| L3.3.4.1 | Pin zone clear of printed bodies. | analysis | d ≥ 0 (sketch: 1.05) | 2 | |
| L3.3.4.2 | Pico top parts to OLED and pin zone. | analysis | d ≥ 0.3 (sketch: 0.4 to the pin zone, 5.4 to the OLED) | 2 | |

### L1.4 Six buttons with printed caps

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The buttons are around the display and well spaced. | inspection | 6 distinct `ACTUATOR_AXIS` positions; each ≥ 8.0 from the window outline; centre-to-centre spacing ≥ 9.0; buttons on at least two sides of the window | 2 | |
| L3.4.1.1 | Button positions. | inspection | as L2.4.1 | 2 | |
| L2.4.2 | One cap per button, through the front face with a clearance. | inspection | 6 caps; stem axis within 0.3 of the `ACTUATOR_AXIS`; stem-to-hole clearance 0.2 to 0.4 per side; cap flange ≥ 1.5 larger than the hole (captive); stem top 0.3 to 1.0 above the front face | 3 | |
| L3.4.2.1 | Cap count and axis alignment. | inspection | 6; offset ≤ 0.3 each | 3 | |
| L3.4.2.2 | Stem clearance. | inspection | each 0.20 to 0.40 per side (sketch: 0.30) | 2 | |
| L3.4.2.3 | Stem standing proud. | inspection | 0.3 to 1.0 (sketch: 0.8) | 1 | |
| L3.4.2.4 | Cap captive. | inspection | flange Ø − hole Ø ≥ 1.5 (sketch: 8.0 − 5.6 = 2.4) | 2 | |
| L2.4.3 | A cap presses its plunger through its full travel. | test | rest gap from the cap's underside (the part that meets the plunger) to `PLUNGER_TOP`: 0.0 to 0.5; stroke from rest to the cap's hard stop S: gap + 0.25 ≤ S ≤ gap + 0.25 + 0.5 (travel plus `pusher_overtravel`); the cap does not touch the plunger side walls | 3 | G5 |
| L3.4.3.1 | Rest gap. | test | 0.0 ≤ gap ≤ 0.5 for all six (sketch: 0.30) | 3 | G5 |
| L3.4.3.2 | Stroke to the hard stop. | test | gap + 0.25 ≤ S ≤ gap + 0.75 for all six (sketch: 0.80 against 0.55 to 1.05) | 3 | G5 |
| L2.4.4 | Each button body is held and not penetrated. | demonstration | M-BTN-k ∩ ALL ≤ 0.01 mm³; captured within 1.0 in ±X, ±Y, −Z | 2 | |
| L3.4.4.1 | No penetration of the button bodies. | demonstration | ≤ 0.01 mm³ for all six | 3 | |
| L3.4.4.2 | Capture of the button bodies. | demonstration | all five hit for all six | 2 | |

### L1.5 USB-C plug seats through the −X end wall

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The plug can go in to full mate without touching the case. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 | G2 |
| L3.5.1.1 | USB-C plug envelope clear. | test | d ≥ 0.30 (sketch: 0.30) | 3 | G2 |
| L2.5.2 | The opening is not oversized. | analysis | inside(V-AP-USB, V-USB-PLUG offset by 1.5, 0.0) | 2 | |
| L3.5.2.1 | Opening within the grown plug envelope. | analysis | d ≥ 0 (with the default plug: opening ≤ 15.4 × 9.5) | 2 | |
| L2.5.3 | The −X wall has exactly two openings (FD6). | inspection | V-AP-USB has 2 connected regions: one around `USB_AXIS`, one around the switch handle | 2 | |
| L3.5.3.1 | Opening count in the −X wall. | inspection | 2 | 2 | |

### L1.6 Slide switch: captive, handle through a slot with its full throw

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | The handle moves through its throw without touching the slot. | test | clear_of(ALL, V-SW-SWEEP, 0.25) | 3 | |
| L3.6.1.1 | Handle sweep clear. | test | d ≥ 0.25 (sketch: 0.40) | 3 | |
| L3.6.1.2 | Handle protrusion beyond the wall's outer face. | inspection | 1.0 ≤ p ≤ 3.0 (sketch: 2.0) | 2 | |
| L3.6.1.3 | Slot not oversized. | analysis | the slot section lies inside V-SW-SWEEP offset by 1.0 (sketch: 7.3 × 3.8 vs sweep 6.5 × 3.0) | 2 | |
| L2.6.2 | The switch is held and does not penetrate. | demonstration | M-SW ∩ ALL ≤ 0.01 mm³; captured within 1.0 in ±Y, ±Z and −X (+X is the wire side and is not required) | 3 | |
| L3.6.2.1 | No penetration of the switch. | demonstration | ≤ 0.01 mm³ | 3 | |
| L3.6.2.2 | Capture of the switch. | demonstration | all five hit | 2 | |
| L2.6.3 | The terminals and wires have room. | analysis | clear_of(ALL, V-SW-TERM, 0.0) | 2 | |
| L3.6.3.1 | Terminal zone clear. | analysis | d ≥ 0 | 2 | |

### L1.7 The LiPo is held, has room to swell, and stays off every solder joint

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The cell is held and does not penetrate. | demonstration | M-LIPO ∩ ALL ≤ 0.01 mm³; captured within 1.0 in ±X, ±Y; it rests on the floor (−Z at 0) | 3 | |
| L3.7.1.1 | No penetration of the cell. | demonstration | ≤ 0.01 mm³ | 3 | |
| L3.7.1.2 | Capture of the cell. | demonstration | ±X, ±Y hit; floor contact | 2 | |
| L2.7.2 | Nothing presses on the swollen cell. | analysis | clear_of(ALL, V-SWELL, 0.0): no printed body in the swell layer above the pouch | 3 | |
| L3.7.2.1 | Swell layer free. | analysis | penetration ≤ 0.01 mm³ | 3 | |
| L2.7.3 | The cell keeps 0.5 clear of every solder joint zone, and the zones are free of printed bodies. | analysis | clear_of(M-LIPO ∪ V-SWELL, V-SOLDER-TP ∪ V-SOLDER-TAB ∪ V-SOLDER-PICO, 0.5); clear_of(ALL, V-SOLDER-TP ∪ V-SOLDER-TAB, 0.0) | 3 | G3 |
| L3.7.3.1 | Cell to solder zones. | analysis | d ≥ 0.50 (sketch: Pico zone 0.50, charger pad zone 11.9, tab zone 2.0) | 3 | G3 |
| L3.7.3.2 | Printed bodies out of the charger and tab zones. | analysis | penetration ≤ 0.01 mm³ | 2 | |
| L3.7.3.3 | Printed bodies out of the Pico underside zone except at the two support squares. | analysis | penetration ≤ 0.01 mm³ outside the squares; each square ≤ 3.0 × 1.6 | 2 | |

### L1.8 The Pico: posts, supports, capture, clearances

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | At least two posts under Pico holes, each with an M2 pilot (A8). | inspection | count ≥ 2; axis within 0.25 of its `HOLE` axis; OD 5.0 to 7.0; pilot Ø 1.6 to 1.8, depth ≥ 5.0; `PCB_TOP` on the post bottoms within 0.10 | 3 | |
| L3.8.1.1 | Post count and axes. | inspection | ≥ 2; each ≤ 0.25 | 3 | |
| L3.8.1.2 | Post OD, pilot diameter and depth. | inspection | 5.0 ≤ OD ≤ 7.0; 1.6 ≤ Ø ≤ 1.8; depth ≥ 5.0 | 3 | |
| L3.8.1.3 | Post seating. | inspection | PCB top on post bottoms ≤ 0.10 | 2 | |
| L2.8.2 | The Pico is held and does not penetrate. | demonstration | M-PICO ∩ ALL ≤ 0.01 mm³; captured within 1.0 in all six directions | 3 | |
| L3.8.2.1 | No penetration of the Pico. | demonstration | ≤ 0.01 mm³ | 3 | |
| L3.8.2.2 | Capture of the Pico. | demonstration | all six hit | 3 | |
| L2.8.3 | Room round the Pico. | analysis | clear_of(ALL, V-PICO-TOP, 0.0); gap between `PCB_BOTTOM` and the cell's `SWELL_TOP` ≥ 2.0; inside(V-PICO, V-CAVITY, 0.3) | 3 | |
| L3.8.3.1 | Top parts clear. | analysis | d ≥ 0 | 3 | |
| L3.8.3.2 | Pico over the swollen cell. | analysis | ≥ 2.0 (sketch: 2.0) | 3 | |
| L3.8.3.3 | Pico inside the cavity. | analysis | d ≥ 0.30 to every wall and face (sketch: 17.5 to the side walls, 6.7 to the front face) | 3 | |

### L1.9 The TP4056 board: held, mouth at the end wall, pads with room

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The board is held and does not penetrate. | demonstration | M-TP ∩ ALL ≤ 0.01 mm³; captured within 1.0 in ±X, ±Y, −Z | 3 | |
| L3.9.1.1 | No penetration of the board. | demonstration | ≤ 0.01 mm³ | 3 | |
| L3.9.1.2 | Capture of the board. | demonstration | all five hit | 2 | |
| L2.9.2 | The USB-C mouth faces the end wall. | inspection | `USB_MOUTH` is 0.3 to 2.0 inside the −X end wall's inner face; `USB_AXIS` within 1.0° of the wall normal; the opening's centre within 0.5 of `USB_MOUTH` in Y and Z | 2 | |
| L3.9.2.1 | Mouth distance and alignment. | inspection | as L2.9.2 (sketch: 0.6) | 2 | |
| L2.9.3 | Board inside the cavity with room. | analysis | inside(M-TP, V-CAVITY, 0.3) | 2 | |
| L3.9.3.1 | Board in the cavity. | analysis | d ≥ 0.30 (sketch: 0.6 at the mouth) | 2 | |

### L1.10 Snap-together halves

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | FRONT and BACK are separate and do not interpenetrate; no screws. | analysis | FRONT ∩ BACK ≤ 1.0 mm³; no hole in the closed case other than those listed in L1.11 | 3 | |
| L3.10.1.1 | Halves closed. | analysis | ≤ 1.0 mm³ | 3 | |
| L2.10.2 | A lap seam locates the halves. | inspection | lap and tongue clearance 0.10 to 0.30 per side; overlap (engagement) 1.5 to 3.0; thinned halves ≥ 0.85; FRONT translated 1.0 along ±X and ±Y each hits BACK > 0.01 mm³ | 2 | |
| L3.10.2.1 | Lap clearance and engagement. | inspection | 0.10 to 0.30; 1.5 to 3.0 (sketch: 0.15; 1.5) | 2 | |
| L3.10.2.2 | Lateral location. | inspection | all four directions hit (sketch: 74, 74, 150, 150 mm³) | 2 | |
| L2.10.3 | At least four hooks hold the halves together. | demonstration | ≥ 4 cantilever hooks; per hook: engagement (overlap of hook and catch along the hook's depth direction) 0.3 to 0.8; arm length ≥ 6.0; root thickness ≥ 0.8; strain 1.5 · t · y / L² ≤ 0.02 with y = the engagement (the deflection that clears the catch); FRONT translated +Z by 1.0 hits BACK > 0.01 mm³ | 3 | |
| L3.10.3.1 | Hook count and engagement. | demonstration | ≥ 4; each in [0.3, 0.8] (sketch: 4 hooks, 0.4) | 3 | |
| L3.10.3.2 | Arm length, thickness, strain. | analysis | L ≥ 6.0; t ≥ 0.8; ε ≤ 0.02 (sketch: 12.2, 1.0, 0.0040) | 2 | |
| L3.10.3.3 | Halves held against pulling apart. | demonstration | hit > 0.01 mm³ at +1.0 | 3 | |
| L2.10.4 | A tight, flush seam. | inspection | seam gap ≤ 0.4; outer step between FRONT and BACK ≤ 0.3, all four sides | 2 | |
| L3.10.4.1 | Seam gap and step. | inspection | ≤ 0.4; ≤ 0.3 | 2 | |

### L1.11 Closed except the listed openings; walls 2.0 to 3.0

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | No unlisted opening. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into V-CAVITY, other than the window, the six button holes, the USB-C opening, the switch slot (and the seam if its gap ≤ 0.4) | 2 | |
| L3.11.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 | |
| L2.11.2 | Wall thickness. | inspection | side walls, end walls, floor and front face each in [2.0, 3.0] (median over a 2 mm grid at least 3 mm from edges and features; lap, tongue, ribs, hooks and posts are features) | 2 | |
| L3.11.2.1 | Wall, floor and front-face thickness. | inspection | 2.0 ≤ t ≤ 3.0 | 2 | |
| L2.11.3 | Material round every opening. | analysis | ligament ≥ 1.0 to the outer wall faces and edges, the seam plane and neighbouring openings (the internal rebate step of the lap is not an edge) | 1 | |
| L3.11.3.1 | Minimum ligament. | analysis | ≥ 1.0 (sketch: 1.8 at the USB-C opening to the seam) | 1 | |

### L1.12 Printable without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | Each body is one manifold shell. | analysis | FRONT 1 shell, BACK 1 shell, each cap 1 shell (6 caps); manifold3d NoError | 3 | G1 |
| L3.12.1.1 | Shells and manifold status. | analysis | all eight bodies: 1 and NoError | 3 | G1 |
| L2.12.2 | No unsupported overhang in the declared orientation (A11). | analysis | faces with n_z < −cos 45° (patch > 1 mm²) = 0 except round holes up to Ø12, bridges up to 15.0 and horizontal ledges up to 1.0 | 2 | |
| L3.12.2.1 | Overhang and bridge scan per body. | analysis | 0 offending patches | 2 | |
| L2.12.3 | Bed contact and thin features. | analysis | bed contact ≥ 50% of the plan bounding box for each body (FRONT front-face down, BACK floor down, caps flange down); local thickness ≥ 0.8; each bounding box ≤ 200 | 1 | |
| L3.12.3.1 | Bed contact. | analysis | ≥ 50% (sketch: FRONT about 92%, BACK about 99%, caps 78%) | 1 | |
| L3.12.3.2 | Thin features and build volume. | analysis | ≥ 0.8; ≤ 200 | 1 | |

### L1.13 Assembly: parts install along their own axes; screws reachable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | The Pico installs into FRONT. | test | clear_of(FRONT, V-INSTALL-PICO, 0.0) (the Pico meeting the post bottoms is designed contact) | 2 | |
| L3.13.1.1 | Pico install path. | test | penetration ≤ 0.01 mm³ | 2 | |
| L2.13.2 | The cell, the board and the switch install into BACK. | test | clear_of(BACK, V-INSTALL-LIPO ∪ V-INSTALL-TP ∪ V-INSTALL-SW, 0.0) | 2 | |
| L3.13.2.1 | Back-half install paths. | test | penetration ≤ 0.01 mm³ for all three | 2 | |
| L2.13.3 | The OLED snaps into FRONT. | test | V-INSTALL-OLED meets FRONT only at its hooks, penetration depth ≤ 0.8 | 1 | |
| L3.13.3.1 | OLED install path. | test | intersection only at hooks, depth ≤ 0.8 (sketch: 6.2 mm³ at the four hooks) | 1 | |
| L2.13.4 | A screwdriver reaches each Pico screw with BACK removed. | test | clear_of(FRONT, V-DRIVER-k, 0.0) for every post | 2 | |
| L3.13.4.1 | Driver columns clear. | test | d ≥ 0 | 2 | |

### L1.14 The package says what was built and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.14.1 | The package holds `front.stl`, `back.stl`, `caps.stl` (six caps as six shells, closed pose, console frame, mm), the `.scad` source, `layout.json` (poses of every reference part and each body's print orientation) and the agent's own interference report. | inspection | all present and readable; the largest axis of `front.stl` and `back.stl` is 100 to 120 | 3 | G0 |
| L3.14.1.1 | Files present and parse; units. | inspection | true | 3 | G0 |
| L3.14.1.2 | The declared layout verifies. | analysis | Pico seating rule (section 2); every other part's pose within 0.2 of a pose that satisfies its no-penetration L3 | 3 | |
| L2.14.2 | The agent's report agrees with the grader. | analysis | for every `clear_of` / `inside` L3 the agent reports: same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 | |
| L3.14.2.1 | Self-report vs judge. | analysis | 100% within 0.10 | 1 | |

## 6. Gates and counts

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.14.1.1), **G1** all eight bodies
manifold single shells (L3.12.1.1), **G2** the USB-C plug seats (L3.5.1.1), **G3** the cell stays off every solder
joint (L3.7.3.1), **G4** the display window contains the viewing area, centred (L3.3.1.1), **G5** every button is
actuated by its cap (L3.4.3.1 and L3.4.3.2). Classes: WRONG (a gate fails), MINOR (no gate fails, a weight-3 L3 fails),
CORRECT (all weight-3 pass), MEETS (CORRECT and every non-physical L3 of weight 1 and 2 passes).

| Level | Count |
|---|---|
| L1 | 14 |
| L2 | 46 |
| L3 | 72 |

## 7. Feasibility (a design exists)

A concrete layout, modelled and checked with `manifold3d`: FRONT and BACK each one shell and NoError (FRONT volume
19 449 mm³, BACK 19 975 mm³). Numbers in mm, console frame (X 0 to 110, Y 0 to 60, Z 0 to 22; seam at Z 12.0; walls 2.0).

| Feature | Value |
|---|---|
| shells | BACK: floor Z 0 to 2, walls to Z 12 with the inner half of the top 1.7 removed (outer lap 1.0 thick, Z 10.3 to 12). FRONT: front face Z 20 to 22, skirt Z 12 to 22, inner tongue 0.85 thick at Z 10.5 to 12 (0.15 from the lap) |
| TP4056 | PCB X 3.6 to 29.6, Y 21.5 to 38.5, Z 4.0 to 5.0 on a rail (X 14 to 16) and side ribs; receptacle X 2.6 to 9.9, Z 5.0 to 8.26; `USB_MOUTH` (2.6, 30.0, 6.63), 0.6 inside the wall; pad zones Z 2.0 to 7.0 (floor top at Z 2.0: d = 0) |
| USB-C opening | −X wall, Y 23.5 to 36.5, Z 3.08 to 10.18 (13.0 × 7.1); plug overmold 12.4 × 6.5, measured plug gap 0.30; ligament to the seam 1.8 |
| switch | body X 2.0 to 7.5, Y 41.75 to 54.25, Z 2.0 to 8.0; handle X −2.0 to 2.0 (protrudes 2.0), Y 46.5 to 49.5, Z 3.5 to 6.5; slot Y 44.35 to 51.65, Z 3.1 to 6.9 (measured sweep gap 0.40); ribs at Y 41.35 to 41.65 and 54.35 to 54.65; terminal zone X 7.5 to 12.5 free |
| LiPo | X 42 to 92, Y 13 to 47, Z 2 to 7 (swollen top 7.5); tabs X 38 to 42, Y 25 to 35 toward the charger; ribs 0.3 to 0.4 round it (X 41.6 ledge columns, X 92.4, Y 12.4 to 12.7 and 47.3 to 47.6) |
| solder zones | charger pads Ø5.0, Z 2.0 to 7.0; tab zone X 34 to 40, Y 23 to 37, Z 2.0 to 9.5; Pico zone Z 8.0 to 9.5 under X 40 to 91, Y 19.5 to 40.5. Cell to Pico zone 0.50, to the charger pad zones 11.9, to tab zone 2.0 |
| Pico | PCB X 40 to 91, Y 19.5 to 40.5, Z 9.5 to 10.5 (2.0 above the swollen cell); receptacle X 38.7 to 44.2, top Z 13.3; top parts to Z 12.0; two posts (OD 5.4, Z 10.5 to 20, pilots Ø1.7 depth 5.0 from the bottom) at (89.0, 24.3) and (89.0, 35.7); two support ledge columns X 40.0 to 41.6, Y 19.5 to 22.5 and 37.5 to 40.5, Z 2 to 9.5 under the USB-end corners; ribs from the front face at X 37.4 to 38.4 (USB end stop), X 91.4 to 92.4 (Y 28 to 32), and Y 18.7 to 19.2 and 40.8 to 41.3 (X 76 to 86); screw heads Z 7.9 to 9.5 (0.4 above the cell) |
| OLED | PCB X 46.1 to 73.9, Y 16.35 to 43.65, Z 17.4 to 18.6 (turned 90°, header edge toward −X); glass X 51.1 to 70.4, Y 16.65 to 43.35, Z 18.6 to 20.0 against the front face; `ACTIVE_CENTER` (60.75, 30.0); window X 53.35 to 68.15, Y 17.2 to 42.8 (25.6 × 14.8: contains 25.0 × 14.0, overlaps the glass by 2.25 and 0.55); pin zone X 46.85 to 49.35, Y 24.9 to 35.1, Z 12.4 to 17.4 (1.05 from printed, 1.9 from the Pico PCB); frame ribs 0.15 round the PCB and four hooks 0.65 under its long edges; Pico top parts to the OLED 5.4 |
| buttons | bodies Z 14.6 to 18.4, plunger tip 18.9, at (17,40), (17,20), (7,30), (27,30), (96,36), (104,26) (min spacing 12.8 centre to centre, nearest body to the window outline 23.4); seat floors Z 13.4 to 14.6 (±4.4) with pocket walls and corner pillars to the front face |
| caps | stem Ø5.0 through Ø5.6 holes (0.30 per side), Z 19.2 to 22.8 (0.8 proud); flange Ø8.0, Z 19.2 to 20.0 on the front face's inner side; rest gap to the plunger 0.30; hard stop on the body top (stroke 0.80 within 0.55 to 1.05); measured cap-to-printed penetration 0.0 |
| snaps | four tabs hanging from the front face (X 27 to 33 and 77 to 83, at Y 3.4 to 4.4 and 55.6 to 56.6), arm length 12.2, thickness 1.0, hook 0.8 deep with 0.4 engagement on catch blocks at Z 7.8 to 8.8; strain 1.5 · 1.0 · 0.4 / 12.2² = 0.40%; FRONT lifted by 1.0 hits BACK by 9.6 mm³ |
| capture (translation by 1.0, mm³ hit) | TP4056 +X 1.6, −X 2.0, ±Y 4.8, −Z 34; LiPo +X 40, −X 18, ±Y 45; Pico all six (+X 1.2, −X 15.7, ±Y 2.5, +Z 37.7, −Z 9.6); OLED +X/−X 14.7, ±Y 18.1, −Z 6.2; switch −X 47, ±Y 9.9, +Z 3.6 (slot), −Z 72; button bodies ±X, ±Y 6.8, −Z 36 |
| other checks run | reference-model penetration into the printed bodies 0.0 for every part; plug and handle sweeps 0.30 and 0.40 clear; install paths of the Pico (FRONT) and of the cell, board and switch (BACK) 0.0; OLED install path meets only the hooks (6.2 mm³); screw driver columns clear of FRONT; FRONT and BACK overlap 0.0 |
| not modelled in the check | the vertical corner radius 3.0 and the print-overhang scan; the hooks' lower faces are 45° ramps and the horizontal ledges are at most 1.0 |

The D-pad of four buttons sits at the bottom end beside the charger and the A and B buttons at the top end, which satisfies "around" the
display on two sides.

## 8. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 | Method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1–L2.1.4 | L3.1.1.1, L3.1.2.1–2, L3.1.3.1, L3.1.4.1 | L1.1 | inspection | "Pico 2 on top of a ... LiPo and TP4056 board" |
| L1.2 | Size | L2.2.1–L2.2.3 | L3.2.1.1, L3.2.2.1, L3.2.3.1 | L1.2 | inspection | "110 x 60 x 22 mm" |
| L1.3 | Display window | L2.3.1–L2.3.4 | L3.3.1.1–2, L3.3.2.1, L3.3.3.1–2, L3.3.4.1–2 | L1.3 | demonstration | "an OLED window in front" |
| L1.4 | Buttons | L2.4.1–L2.4.4 | L3.4.1.1, L3.4.2.1–4, L3.4.3.1–2, L3.4.4.1–2 | L1.4 | test | "six tactile buttons around it" |
| L1.5 | USB-C | L2.5.1–L2.5.3 | L3.5.1.1, L3.5.2.1, L3.5.3.1 | L1.5 | test | "a ... USB-C port on the bottom end" |
| L1.6 | Switch | L2.6.1–L2.6.3 | L3.6.1.1–3, L3.6.2.1–2, L3.6.3.1 | L1.6 | test | "a slide power switch" |
| L1.7 | Battery | L2.7.1–L2.7.3 | L3.7.1.1–2, L3.7.2.1, L3.7.3.1–3 | L1.7 | analysis | "the battery must not press on any solder joints" |
| L1.8 | Pico | L2.8.1–L2.8.3 | L3.8.1.1–3, L3.8.2.1–2, L3.8.3.1–3 | L1.8 | analysis | "Pico 2 on top of" |
| L1.9 | Charger board | L2.9.1–L2.9.3 | L3.9.1.1–2, L3.9.2.1, L3.9.3.1 | L1.9 | analysis | "TP4056 board", "USB-C port" |
| L1.10 | Snap closure | L2.10.1–L2.10.4 | L3.10.1.1, L3.10.2.1–2, L3.10.3.1–3, L3.10.4.1 | L1.10 | inspection | "The two halves snap together" |
| L1.11 | Closed, walls | L2.11.1–L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | L1.11 | analysis | implied (handheld device) |
| L1.12 | Printable | L2.12.1–L2.12.3 | L3.12.1.1, L3.12.2.1, L3.12.3.1–2 | L1.12 | analysis | implied (FDM) |
| L1.13 | Assembly | L2.13.1–L2.13.4 | L3.13.1.1, L3.13.2.1, L3.13.3.1, L3.13.4.1 | L1.13 | test | implied |
| L1.14 | Evidence | L2.14.1–L2.14.2 | L3.14.1.1–2, L3.14.2.1 | L1.14 | inspection | needed by the judge |

## 9. Grading (design-specific; used because `generalize/rubric.md` is missing)

- **Verdict:** WRONG (any gate G0 to G5 fails), MINOR (no gate fails, some weight-3 L3 fails), CORRECT (every weight-3 L3
  passes), MEETS (CORRECT and every non-physical L3 of weight 1 and 2 passes). UNVERIFIED counts as FAIL. Report also the weighted
  score Σ(weight × pass)/Σ(weight) and the worst normalised margin among weight-3 L3s.
- **Precedence:** numbers in this document beat `part.json`. The plug, sweep and solder-zone checks (L3.5.1.1, L3.6.1.1, L3.7.3.1)
  outrank everything about opening size. Designed contact is never interference. Never relax a criterion or round in the design's
  favour beyond ε.
- **WHERE a defect is:** one entry per failed or UNVERIFIED L3, gates first then weight 3, 2, 1, with: `req` (L3 with L2 and L1),
  `status`, `body` (`front`, `back`, `cap_k`, `both` or `layout`), `feature` (named by function, for example "window in the front face" or
  "cap 3 stem hole"), `face` (surface and outward normal), `location` (point or bounding box in the console frame), `measured` / `limit` /
  `margin`, `reference` (M-LIPO, V-SOLDER-PICO and so on, with the datum), `needed` (the geometric target as numbers, for example "window
  must contain 25.0 × 14.0 around (60.75, 30.0), now 24.2 wide") and `evidence` (saved defect STL). `needed` never says how to build it.
- **Measured-values table (always filled in):** outer size and corner radius; window size, offset and overlap; glass gap; capture hits for
  OLED, buttons, switch, cell, board, Pico; cap clearance, rest gap and stroke for all six buttons; USB-C plug d and opening size; switch sweep d,
  protrusion and slot size; swell layer; cell-to-solder-zone d for each zone; Pico posts, seating, gap to the cell; board mouth distance; lap
  clearance and engagement; hook count, engagement, arm length, strain; seam gap and step; unlisted openings; wall thickness; shells; overhang
  patches; bed contact; install paths; driver columns; self-report agreement.

## Audit

Adversarial audit against `benchmarks/enclosure/rubric.md` (the generalize rubric is absent), the catalogue and the L1 text in
`design.json`. The reference-model part of the sketch in section 7 (TP4056, LiPo and swell layer, Pico, OLED, six buttons, switch,
plug margins, solder zones, pin zone) was rebuilt in `manifold3d` and re-measured; all seven catalogue ids plus
`screw_m2_selftap` load through `parts.Catalog` and pass `parts.validate`. The printed shells themselves were not rebuilt in
full (they hold about forty features); their dimensional claims were recomputed by hand from the listed coordinates. L1 14
(E1-01: 12), L2 46 (45), L3 72 (69): comparable to E1-01; counts match section 6.

| # | Finding | Fix |
|---|---|---|
| 1 | The request did not say where the solder joints are, yet G3 (L3.7.3.1) and L3.7.3.2/3 grade the cell against zones that exist only in A5 and section 2 (Pico underside 1.5, tab strip 2.0 to 8.0 and 14.0 wide, joint-free squares 3.0 x 1.6). `rpi_pico2/part.json` has no underside keep-out and `lipo_503450` / `tp4056_usbc_module` have different ones (tab zone 7.0 x 10.0 x 1.5 from the pouch edge; far-end pad boxes 5.0 x 17.0 x 2.0), so the agent could not derive the numbers. | The request text now defines the three zones (an engineer's sentence), L1.7 refers to it, L1.9 states the Ø5.0 pad circle. Section 2 keeps precedence over the catalogue numbers (A5, uncertainty high; the catalogue keep-outs are shared with other entries and the converged enclosure). `request_notes` updated. |
| 2 | Sketch numbers wrong when re-measured: cell to charger pad zone is 11.9 (quoted 2.0); Pico top parts to the OLED is 5.4 (quoted 3.0; to the pin zone 0.40 is right); button spacing minimum is 12.8 centre to centre (quoted 10.0) and the nearest button body to the window is 23.4 (quoted 26, a centre distance); OLED pin zone is X 46.85 to 49.35 from the datums (quoted 47.0 to 49.5). | Corrected in L3.3.4.2, L3.7.3.1 and section 7. |
| 3 | L1.1 said the Pico is stacked "above them" (LiPo and charger), but L2.1.2 only requires overlap with the LiPo (96% in the sketch; the charger lies beside the LiPo, FD3) and the plan cannot cover both (50 + 26 mm of boards against a 51 mm Pico). | L1.1 and FD3 now say: side by side in the lower layer, Pico stacked above the LiPo. |
| 4 | L2.10.3: the strain formula used an undefined `y`; the sketch used the engagement (0.4), not the hook depth (0.8). Both pass (0.40% and 0.81% against 2%). | `y` is defined as the engagement, the deflection needed to clear the catch. |
| 5 | L2.11.3: the wall above the −X openings is only the 1.0 thick outer lap above Z 10.3 (the inner half is the rebate), so the USB-C opening (top Z 10.18) is 0.12 from the rebate step although 1.8 from the seam. | Ligament is defined to outer wall faces and edges, the seam plane and other openings; the internal rebate step is not an edge (the outer lap keeps its full 1.0 above the opening). |
| 6 | Numbers the judge uses that the agent was never told: cap flange >= 1.5 wider than the hole; buttons >= 8.0 from the window and on two sides; lap overlap 1.5 to 3.0 and thinned parts >= 0.85; outer step <= 0.3; ligament >= 1.0; bed contact >= 50%; pad circle 5.0. | Added to the L1 texts in `design.json` (ids and count unchanged). |

Re-measured and confirmed (reference models at the sketch poses): no pair of the ten reference solids interferes (closest: LiPo to Pico 2.50, TP to switch 3.25);
cell with swell to the Pico underside zone 0.50 and to the tab zone 2.00, pen 0; Pico bottom to swell top 2.00; plug overmold margins to the USB-C opening 0.30 on all four sides
(opening 13.0 x 7.1; 15.4 x 9.5 limit); OLED window contains the 25.0 x 14.0 view and overlaps the glass by 2.25 / 0.55; OLED stack, switch (slot 7.3 x 3.8, −X capture 47 mm³
= 12.5 x 6.0 minus the slot), TP rail capture (34 mm³ = 2.0 x 17 x 1.0), Pico −Z capture (9.6 mm³ = two 1.6 x 3.0 ledges x 1.0), cap rest gap 0.30 and stroke 0.80; screw tip reaches 5.0 into the posts
(M2 x 6 through the 1.0 board); strain 0.40% / 0.81%.

Observation (not changed): the switch handle protrudes 2.0 from the bottom wall while the case outer size is 110.0; the L3.2.1.1 box is of the two shells (A13), so the handle does not count against it.
