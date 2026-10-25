# G50 Fan-cooled Pi Zero 2 W console with OLED and encoder: requirements (L1 / L2 / L3)

Training design of the generalisation set (family combination; capabilities vent_pattern, thermal_airflow, window,
panel_mount_bushing, stacked_boards, snap_fit, plug_envelope_opening, datum_placement). The machine-readable request
(L1 only, `dev.json` format) is `design.json` next to this file. It is modelled on
`benchmarks/enclosure/requirements.md` (E1-01) and uses the same conventions: tolerances (1.2), `clear_of`, `inside` and
designed contact (1.3), reference models and envelopes (2), assumptions with uncertainty and fixed decisions (3), a tree whose
every L3 is measured by Python on the delivered STLs (4), gates (5), a feasibility sketch (7) and traceability (8).

**Brief (plan.json, verbatim):** "A desktop console: Pi Zero 2 W with a 40 mm fan above it on 32 mm pitch, OLED window and
EC11 encoder on the front panel, and both micro-USB ports exposed at the rear. Vents on the sides, and the Pi's heat must
have an exhaust path. The case closes with snap latches."

**Rubric note.** The generic file `benchmarks/generalize/rubric.md` did not exist when this entry was written, so
section 6 below is the design-specific rubric (recipes, classes, how to report where a defect is). If the generic rubric
appears later it applies on top of this file; where they disagree the numbers in this file win.

**How to read the tree.** L1 is what the owner needs, L2 an engineering requirement, L3 a check on the geometry. Each L3 has
a method (inspection, analysis, demonstration, test, human; as in `design.json`), a pass/fail criterion with a number and
tolerance, a weight (3 critical, 2 major, 1 minor) and a gate mark (G0..G5) on must-pass rows. Numbers that come from an
assumption (section 3) are provisional until the owner confirms them. Never relax a criterion because the agent fails it.

---

## 1. Frames, tolerances, designed contact

### 1.1 Frames

- **Case frame:** X across the console's width, Y from the front panel (Y small) to the rear wall (Y large, the USB
  openings), Z up, Z = 0 on the underside of the base. The grader normalises a design delivered rotated by multiples of 90°
  about Z or mirrored in X so that the wall with the two USB openings is at +Y; never penalised.
- **Pi frame** (catalogue `rpi_zero2w`): origin at the PCB min corner, PCB bottom Z = 0, components on +Z, the three cabled
  ports on the −Y long edge, microSD on the −X short edge. Its pose in the case frame is declared in `layout.json`; the USB
  axes must point along case +Y.
- **Fan frame** (catalogue `fan_40x40x10`): airflow along module +Z; in this design the airflow is along case −Z (blowing down).
- Lengths in mm, angles in degrees, areas in mm².

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered meshes, never by eye.

| Quantity | ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm | a value passes if it meets the limit within ε |
| angle | 0.5° | same |
| intersection volume | 0.01 mm³ | "no interference" means ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the section | what a screw or pin sees |
| boss / post OD | smallest enclosing circle | |
| area | 1 mm² | open areas are computed from sections (6.2) |

### 1.3 Interference checks and designed contact

- **`clear_of(bodies, volume, c)`**: minimum distance between the printed bodies and `volume` is ≥ c − ε, penetration ≤ 0.01 mm³.
- **`inside(volume, void, c)`**: `volume` lies in `void` with every point ≥ c − ε from the void boundary.

`bodies` is ALL (base and lid, closed), BASE or LID. The grader builds all reference models and envelopes itself from the
catalogue and the declared layout; the agent's copies are not trusted for grading.

**Designed contact for this design (never interference; only penetration > 0.01 mm³ counts for these pairs):**
1. the Pi PCB underside on its four standoff tops; a screw in its pilot and a screw head on the surface it clamps,
2. the fan's top face against the four lid post ends, and a fan screw through a fan hole into a post pilot,
3. the OLED PCB top face (the glass side) against its two screw-post ends, and an OLED pin in its PCB hole,
4. the encoder shoulder against the panel's inner face, and the encoder bushing in its panel hole,
5. the lid lip against its locating faces (fit set by L2.10.2), the lid plate resting on the wall tops, and a snap hook in its catch.

A distance of zero is a pass for these pairs.

---

## 2. Reference models, envelopes, datums

### 2.1 Reference models (M-)

Poses are the ones the design declares in `layout.json`; the feasibility sketch in 7 is one valid layout.

| Name | What | Source | Size and datums used |
|---|---|---|---|
| **M-PI** | Raspberry Pi Zero 2 W | `rpi_zero2w` | PCB 65.0 × 30.0 × 1.4; holes Ø2.75 at 3.5 from the edges (58 × 23 pattern); mini-HDMI 11.2 × 7.5 × 3.2 at x 12.4 (overhang 0.5); micro-USB receptacles 7.5 × 5.9 × 2.6 at x 41.4 (data) and x 54.0 (power), overhang 0.9; microSD cage 14.0 × 12.0 × 1.4, overhang 1.0; tallest top part 3.2 above the PCB top; datums `USB_DATA_MOUTH`/`AXIS`, `USB_POWER_MOUTH`/`AXIS`, `HOLE` (4), `PCB_BOTTOM`, `PCB_TOP` |
| **M-FAN** | 40 mm fan | `fan_40x40x10` | frame 40.0 × 40.0 × 10.0; holes Ø3.2 on a 32.0 pitch; bore Ø38.0; hole keep-out Ø7.0; inlet and exhaust air gaps 5.0; datums `AIRFLOW`, `HOLE`, `INLET`, `EXHAUST` |
| **M-OLED** | 0.96 in SSD1306 module | `oled_ssd1306_096` | PCB 27.3 × 27.8 × 1.2; glass 26.7 × 19.3 × 1.4 with its lower edge 5.0 from the header edge; holes Ø2.0 at 1.9 (X) and 2.0 (Y) from the edges (23.5 × 23.8 pattern); active area 21.74 × 10.86; view zone 25.0 × 14.0 × 3.0 in front of the glass; datums `ACTIVE_CENTER`, `VIEW_AXIS`, `HOLE` (4), `PCB_TOP` |
| **M-ENC** | EC11 encoder | `encoder_ec11` | body 12.0 × 13.4 × 6.5; M7 bushing Ø7.0 × 7.0; shaft Ø6.0 × 15.0; nut zone Ø11.0 × 3.0; max panel thickness 3.0; terminals 3.5 behind the body; datums `SHOULDER`, `BUSHING_TOP`, `AXIS`, `SHAFT_AXIS` |
| **M-PLUG-USB-k** (k = 1, 2) | micro-USB B plug | `plug_microusb_b` | shell 6.9 × 1.85, inserted 5.0, exposed 1.5; overmold 10.0 × 7.0 × 20 |
| **M-SCREW25** | M2.5 self-tapping screw | `screw_m2p5_selftap` | thread Ø2.5, head Ø5.0 × 1.75, pilot Ø2.0 to 2.2, stock lengths 6, 8, 10 (declared) |
| **M-SCREW2** | M2 self-tapping screw | `screw_m2_selftap` | thread Ø2.0, head Ø4.0 × 1.6, pilot Ø1.6 to 1.8, stock lengths 4, 5, 6, 8, 10 |
| **M-BOLT3** | M3 socket bolt (fan screws) | `bolt_m3_iso4762` | thread Ø3.0, head Ø5.5 × 3.0, tap Ø2.5, stock lengths 10, 12, 14, 16, 20 |

### 2.2 Envelopes (V-) and computed volumes

| Name | Definition | Used by |
|---|---|---|
| **V-PI** | M-PI including the receptacles, the HDMI body and the SD cage (the parts beyond the PCB edge) | L2.2.3 |
| **V-USB-PLUG-k** | M-PLUG-USB-k at full mate on `USB_DATA_MOUTH` / `USB_POWER_MOUTH`, overmold swept along the port axis to 40 beyond the rear wall | L2.3.1, L2.3.2 |
| **V-FAN-IN** | the inlet air box: 40.0 × 40.0 × 5.0 on the inlet face (above the fan, the side the air enters), minus the four Ø7.0 hole columns | L2.4.3 |
| **V-FAN-EX** | the exhaust air box: 40.0 × 40.0 × 5.0 on the exhaust face (below the fan), minus the four Ø7.0 hole columns | L2.4.3 |
| **V-FAN-BORE** | the Ø38.0 column on `AIRFLOW` through the fan thickness plus 5.0 on each side | L2.6.2 |
| **V-OLED-VIEW** | the OLED view zone: 25.0 × 14.0 × 3.0 prism centred on `ACTIVE_CENTER`, base on the glass top, extruded toward the front | L2.7.2 |
| **V-OLED-BACK** | the zone behind the OLED PCB: PCB footprint × 3.0 behind the back face (header pins and wires, A5) | L2.8.3 |
| **V-ENC-NUT** | the encoder nut zone Ø11.0 × 3.0 on the outer face of the panel along `AXIS` | L2.9.3 |
| **V-DRIVER-FAN-k** | Ø6.0 column on the axis of fan screw k from the head, 50 long, away from the fan, lid inverted | L2.4.4 |
| **V-CAVITY** | the closed case's internal void: convex hull of BASE ∪ LID minus BASE ∪ LID, component containing the Pi centroid | L2.2.3, L2.11.1 |
| **V-AP-USB** | the openings actually present in the rear wall at the USB height | L2.3.2, L2.3.3 |
| **V-AP-WIN** | the window actually present in the front panel at the OLED | L2.7.1 |
| **V-AP-VENT-i** | each through-region of a lateral wall (±X, rear) other than the USB openings, with the section area at mid-wall | L2.5.x |
| **V-SPHERE-PATH** | free space = V-CAVITY − (M-PI ∪ M-FAN (minus V-FAN-BORE) ∪ M-OLED ∪ V-OLED-BACK ∪ M-ENC ∪ posts ∪ all printed solids), voxelised at 0.5 and eroded by 2.5 (the centre space of a Ø5.0 sphere). The inner mouth of a vent is the part of this space within 3.5 of the vent's cavity-side face; the sphere does not have to pass through the slot itself (2.0 to 3.0 wide, set by L2.5.4) | L2.6.1 |

### 2.3 Sanity checks and seating rule

| ID | Check | Pass |
|---|---|---|
| R1 | M-PI PCB, hole pattern | 65.0 × 30.0 × 1.4 ± 0.2; pitch 58.0 × 23.0 ± 0.1 |
| R2 | M-FAN frame and hole pitch | 40.0 × 40.0 × 10.0 ± 0.2; 32.0 ± 0.1 |
| R3 | M-OLED PCB, hole pattern | 27.3 × 27.8 × 1.2 ± 0.2; 23.5 × 23.8 ± 0.6 |
| R4 | M-ENC body, bushing | 12.0 × 13.4 × 6.5 ± 0.2; Ø7.0 ± 0.1 |
| R5 | every V- envelope's datums equal its model's | ≤ 0.01 |

**Seating rule.** Each reference model is placed at its pose in `layout.json`. The grader verifies the declaration: the Pi PCB
underside lies on the standoff tops (distance ≤ 0.10) and the Pi hole axes are coaxial with the standoff pilots (residual
≤ 0.25); the fan's hole axes with the post pilots (≤ 0.25) and its top face on the post ends (≤ 0.10); the OLED header-side holes with the
screw-post pilots (≤ 0.25) and its glass-side holes with the pins (≤ 0.10); the encoder shoulder on the panel inner face (≤ 0.30) and its axis with the panel hole (≤ 0.25). If the
declaration is missing or fails the grader seats by those fits; with no standoffs or posts the dependent checks fail.

---

## 3. Assumptions, fixed decisions and open questions for the owner

Each line gives the value chosen and why. All derived from the brief, the catalogue or convention; none asked.

| # | Question | Value chosen | Why and uncertainty |
|---|---|---|---|
| A1 | How does the Pi lie? | Flat on four standoffs, long axis along X, the −Y edge (the ports) facing the rear wall (so the Pi is rotated 180° about Z). | "both micro-USB ports exposed at the rear". |
| A2 | Which micro-USB is which? | Not graded: the two ports are interchangeable for the case. | The enclosure does not care. |
| A3 | HDMI and microSD? | Neither is exposed. The HDMI body (overhang 0.5) and the SD cage (overhang 1.0) stay inside the cavity. The SD card stays in. | Not in the brief. Their bodies are part of V-PI. |
| A4 | Fan direction and height? | The fan blows down onto the Pi (inlet on top). Its exhaust face is at least 5.0 above the tallest Pi top part (HDMI, 3.2 above the PCB top) and its inlet face at least 5.0 below the ceiling. Fan axis within 6.0 of the Pi PCB centre in plan (the SoC location is not in part.json; ±8). | `fan_40x40x10` inlet and exhaust gaps (assumed 5.0, ±3). "40 mm fan above it". |
| A5 | OLED back? | Header pins and wires occupy 3.0 behind the OLED PCB (V-OLED-BACK); the fan and the Pi keep at least 0.5 from it. | part.json models the PCB and the glass only. ±1.5. |
| A6 | OLED dimensions? | As `oled_ssd1306_096` part.json: PCB 27.3 × 27.8 × 1.2; glass 26.7 × 19.3 × 1.4; the active-area centre assumed at the glass centre (it may be about 1 mm off on real modules). | Brief gives only the 25 × 14 viewing area. Measure the owner's module. |
| A7 | Screw rules? | Engagement = screw length − thickness of the clamped plate (PCB 1.4 for the Pi, PCB 1.2 for the OLED, fan frame 10.0); it must be ≥ 5.0 for M2 and M2.5 (rule `min_engagement`) and ≥ 6.0 (two thread diameters) for the M3 fan screws, and ≤ pilot depth − 0.5; at least 0.8 of material must remain beyond the pilot tip. | Self-tapping screws in PLA. |
| A8 | Vent free area? | Intake (openings whose area-weighted centroid is above the fan mid-plane) ≥ 300 in total; exhaust (centroid at or below the fan exhaust face) ≥ 300 in total; slot width 2.0 to 3.0; ligament between slots ≥ 1.5. About 26 percent of the fan's bore area (1134) each. | A passive-restriction rule of thumb for a 2 W board and a 40 mm fan; ±40 percent. Slots 2 to 3 wide keep fingers and dust out. |
| A9 | Heat of the Pi? | About 2 W. No heat sink. | Pi Zero 2 W under load. |
| A10 | Encoder panel hole? | Ø7.4 ± 0.1 (M7 bushing + 0.4); panel thickness at the hole 2.0 to 3.0 (`max_panel_thickness` 3.0, ±1.0); the nut and the shaft are on the outside. | `encoder_ec11` part.json. |
| A11 | Plug sizes? | Micro-USB overmold 10.0 × 7.0 (catalogue). | Typical cable. Measure the owner's cable. |
| A12 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. Sliding fit 0.15 to 0.35 per side. Wall, floor and lid 2.0 to 4.0. No face steeper than 45° from vertical; round holes Ø ≤ 12.0 and bridges ≤ 15.0 exempt. **A horizontal step (a ledge) no deeper than 1.2 is exempt** (the return face of a snap hook, three line widths). | design_rules.json values; the 1.2 step rule is added here for snap hooks. |
| A13 | Snap hook rules? | Cantilever hook: free length L 10 to 20, thickness t 1.2 to 2.0, width ≥ 4.0; engagement 0.6 to 1.2 (deflection y = engagement); strain ε = 1.5 · t · y / L² ≤ 1.5 percent; lead-in face 20° to 35° from the insertion direction, return face 70° to 90°; the wall behind a catch recess ≥ 1.5. | FDM snap-fit practice: PLA tolerates about 2 percent strain once; 1.5 percent allows layer-line weakness. ±30 percent. |
| A14 | Size and stability? | Closed outside ≤ 90 × 70 × 45; stable at 5° tilt. Mass of the Pi, fan, OLED and encoder 60 g. | A desktop box; the sketch is 72.8 × 56.5 × 39.5. |
| A15 | Wiring? | The OLED (4 wires), the encoder (5 terminals) and the fan (2 wires) connect to the Pi by loose leads; no connector or harness is modelled. | Not a mechanical concern. |
| A16 | How is the OLED fixed? | Screws only at the two header-side holes (posts OD 5.0 reaching the PCB top face). The two glass-side holes lie 1.5 from the glass edge (hole at module y 25.8, glass to y 24.3), so a post of OD 5.0 (radius 2.5) or an M2 head (radius 2.0) would overlap the glass; they carry locating pins Ø1.8 (hole Ø2.0) on pin posts that stop 0.5 before the glass front face. The pins leave the PCB back face 0.6 clear, so V-OLED-BACK stays free. | Derived from `oled_ssd1306_096` (hole inset 1.9 × 2.0, glass 19.3 at y0 5.0, ±1.0). The header-side holes are 3.0 from the glass: post radius 2.5 clears it by 0.5. Pin retention is by the two screws and the pins; the module weighs a few grams. |

### Fixed decisions (one choice, no alternatives accepted)

| # | Decision | Why |
|---|---|---|
| FD1 | Two printed bodies: BASE (floor, four walls, Pi standoffs, OLED posts, catch recesses) and LID (a flat plate with a locating lip, four snap hooks and the four fan posts). The seam is a plane at the wall tops. | Fan carried from the lid; separate bodies for printing. |
| FD2 | The front wall is the front panel: the OLED window and the encoder hole are in it. The OLED faces −Y (the glass toward the front), its PCB in an XZ plane, header edge down. The encoder axis is along −Y (shaft out), shoulder on the panel's inner face. | "front panel". |
| FD3 | The fan blows down. The fan stands on nothing: it hangs from four lid posts (OD 7.0, the fan top face against the post ends) by four M3 screws entering from below through the fan holes. | The fan hole pitch (32) is wider than the Pi (30), so floor posts would collide with the Pi. |
| FD4 | Snap hooks hang from the lid and engage blind recesses in the inner faces of the two lateral walls; there are no through windows. | Keeps the closed case free of unlisted openings. |
| FD5 | Vents are slots in the lateral walls (the two ±X walls and the rear wall) only, never in the floor, lid or front panel. | "Vents on the sides". |
| FD6 | Print poses: BASE floor down; LID plate down (outer face on the bed, posts, lip and hooks up). The layout declares them. | No overhang beyond the ledge rule. |

---

## 4. Requirements tree

### L1.1 Placement from the catalogue, USB at the rear, no collisions, layout declared

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares the layout: pose of M-PI, M-FAN, M-OLED, M-ENC, each screw and bolt (axis, length), print pose of each body. | inspection | `layout.json` present, parses, names the catalogue ids | 3 | |
| L3.1.1.1 | Layout parses and every catalogue id exists. | inspection | true | 3 | G0 |
| L2.1.2 | The Pi's two micro-USB ports face the rear wall. | inspection | `USB_DATA_AXIS` and `USB_POWER_AXIS` within 1.0° of +Y | 3 | |
| L3.1.2.1 | USB axis directions in the case frame. | inspection | ≤ 1.0° | 3 | |
| L2.1.3 | The reference models do not collide (designed contact aside) and keep their gaps. | analysis | pairwise intersection of M-PI, M-FAN, M-OLED, M-ENC ≤ 0.01 mm³; M-FAN to M-OLED, M-ENC and V-OLED-BACK ≥ 0.5 | 3 | |
| L3.1.3.1 | Pairwise interference of the reference models. | analysis | ≤ 0.01 mm³ | 3 | |
| L3.1.3.2 | Fan to OLED, encoder and OLED back zone. | analysis | ≥ 0.5 | 2 | |

### L1.2 The Pi is held on four standoffs inside the case

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Four vertical standoffs, one under each Pi hole. | inspection | count = 4; each axis within 0.25 of its `HOLE` axis; axis within 1.0° of Z | 3 | |
| L3.2.1.1 | Pi standoff count. | inspection | = 4 | 3 | G2 |
| L3.2.1.2 | Axis offset to the Pi `HOLE` axes. | analysis | ≤ 0.25 each | 3 | G2 |
| L3.2.1.3 | Axis direction. | inspection | ≤ 1.0° | 2 | |
| L2.2.2 | Tops coplanar; the PCB rests on them; M2.5 geometry (A7). | inspection | top spread ≤ 0.10; PCB underside within 0.10 of the tops; OD 5.0 to 7.0; pilot Ø2.0 to 2.2; pilot depth ≥ engagement + 0.5 with engagement = screw length − 1.4 ≥ 5.0; ≥ 0.8 of material below the tip; wall round the pilot ≥ 1.6; standoff height 3.0 to 8.0 | 3 | |
| L3.2.2.1 | Standoff top spread and PCB seating. | analysis | ≤ 0.10; ≤ 0.10, penetration ≤ 0.01 mm³ | 3 | |
| L3.2.2.2 | Pilot Ø, depth, engagement, tip material. | inspection | as L2.2.2 | 3 | |
| L3.2.2.3 | Standoff OD and height. | inspection | 5.0 ≤ OD ≤ 7.0; 3.0 ≤ h ≤ 8.0 | 2 | |
| L2.2.3 | The Pi and its overhanging parts lie inside the cavity with clearance. | analysis | inside(V-PI, V-CAVITY, 0.2); PCB edges (except the rear) ≥ 0.5 from every wall; V-PI to the OLED and encoder terminals ≥ 0.5 | 3 | |
| L3.2.3.1 | V-PI in the cavity. | analysis | d ≥ 0.20 | 3 | |
| L3.2.3.2 | Pi PCB edge to the walls. | analysis | ≥ 0.50 | 2 | |
| L3.2.3.3 | Pi to the encoder body and terminals and to V-OLED-BACK. | analysis | ≥ 0.50 | 2 | |

### L1.3 Two micro-USB plugs fit through the rear wall with the lid closed

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Lid closed: both plugs, inserted at the same time, reach full mate without touching the case or each other. | test | clear_of(ALL, V-USB-PLUG-1 ∪ V-USB-PLUG-2, 0.3); the two envelopes do not intersect | 3 | |
| L3.3.1.1 | Plug envelopes clear. | test | d ≥ 0.30 for each; plug-to-plug intersection ≤ 0.01 mm³ | 3 | G2 |
| L3.3.1.2 | Physical: print, close, plug in two cables. | test | both click in fully | 2 | physical, optional |
| L2.3.2 | The openings are not oversized. | analysis | inside(V-AP-USB, (V-USB-PLUG-1 ∪ V-USB-PLUG-2) offset by 1.5, 0.0) | 2 | |
| L3.3.2.1 | Openings within the grown envelopes. | analysis | d ≥ 0.0 (each ≤ 13.0 × 10.0 with the catalogue plug) | 2 | |
| L2.3.3 | One opening per port or one merged opening, all in the rear wall, with material round them. | inspection | 1 or 2 connected regions at the USB height; if 2, ligament between them ≥ 1.5; ligament to the floor line, the seam and the wall edges ≥ 1.5 | 2 | |
| L3.3.3.1 | Opening count in the rear wall at the USB height. | inspection | 1 or 2 | 2 | |
| L3.3.3.2 | Ligaments round and between the openings. | analysis | ≥ 1.5 | 1 | |

### L1.4 The fan hangs above the Pi on its four holes, blowing down, with 5 mm gaps

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The fan is above the Pi, blowing down. | inspection | `AIRFLOW` within 1.0° of −Z; fan axis within 6.0 of the Pi PCB centre in plan; fan bottom above every Pi top part | 3 | |
| L3.4.1.1 | Airflow direction. | inspection | ≤ 1.0° from −Z | 3 | |
| L3.4.1.2 | Plan offset of the fan axis to the Pi centre. | inspection | ≤ 6.0 | 2 | |
| L2.4.2 | Four lid posts at the fan holes carry the fan. | inspection | count = 4; each axis within 0.25 of a fan `HOLE` axis; axis within 1.0° of Z; post end plane within 0.10 of the fan top face; post OD 7.0 ± 0.2 (the hole keep-out); pilot Ø2.4 to 2.6, depth ≥ 6.5 (engagement = screw length − 10.0 ≥ 6.0, depth ≥ engagement + 0.5), ≥ 0.8 of material beyond the tip; screws M-BOLT3 | 3 | |
| L3.4.2.1 | Fan post count and axis offsets. | analysis | = 4; ≤ 0.25 each | 3 | G3 |
| L3.4.2.2 | Post OD, end plane, pilot Ø, depth, engagement, tip material. | inspection | as L2.4.2 | 2 | |
| L3.4.2.3 | Post axis direction. | inspection | ≤ 1.0° | 1 | |
| L2.4.3 | The inlet and exhaust air boxes are free of printed material. | analysis | clear_of(ALL, V-FAN-IN, 0.0) and clear_of(ALL, V-FAN-EX, 0.0); fan exhaust face to the highest Pi top part ≥ 5.0; fan inlet face to the ceiling inner face ≥ 5.0 | 3 | |
| L3.4.3.1 | Inlet air box clear. | analysis | d ≥ 0.0; inlet face to the ceiling ≥ 5.0 | 3 | G3 |
| L3.4.3.2 | Exhaust air box clear. | analysis | d ≥ 0.0; exhaust face to the highest Pi top ≥ 5.0 | 3 | G3 |
| L2.4.4 | The fan screws are reachable with the lid off (inverted) and the heads clear the Pi parts. | test | clear_of(LID ∪ M-FAN, V-DRIVER-FAN-k, 0.0); screw head to the Pi top parts ≥ 1.0 | 1 | |
| L3.4.4.1 | Fan driver columns clear. | test | d ≥ 0.0 for all four | 1 | |
| L3.4.4.2 | Fan screw heads above the Pi. | analysis | ≥ 1.0 | 2 | |

### L1.5 Vents in the lateral walls: free area, slot size, only on the sides

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Intake open area. | analysis | Σ area of vent regions with centroid above the fan mid-plane ≥ 300 | 3 | |
| L3.5.1.1 | Intake free area. | analysis | ≥ 300 | 3 | |
| L2.5.2 | Exhaust open area. | analysis | Σ area of vent regions with centroid at or below the fan exhaust face ≥ 300 | 3 | |
| L3.5.2.1 | Exhaust free area. | analysis | ≥ 300 | 3 | |
| L2.5.3 | Vents are on the sides, on at least two walls, in both zones. | inspection | all vent regions in the ±X and rear walls; none in the floor, lid, front panel; intake and exhaust vents on at least two different lateral walls | 2 | |
| L3.5.3.1 | Vent location. | inspection | no vent outside the lateral walls (not the front panel) | 2 | |
| L3.5.3.2 | Both zones on at least two walls. | inspection | true | 2 | |
| L2.5.4 | Slot size and ligaments. | inspection | slot width 2.0 to 3.0 (median); ligament between slots ≥ 1.5; ligament to the wall edges, the seam and the catch recesses ≥ 1.5 | 2 | |
| L3.5.4.1 | Slot width. | inspection | 2.0 ≤ w ≤ 3.0 | 2 | |
| L3.5.4.2 | Ligaments. | analysis | ≥ 1.5 | 1 | |

### L1.6 An air path exists through the fan to the exhaust

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | A Ø5.0 sphere can travel inside the case from the inner mouth of an intake vent to the centre of the fan inlet air box, and from the centre of the fan exhaust air box, past the Pi, to the inner mouth of an exhaust vent. | test | in V-SPHERE-PATH: connected path from an intake vent inner mouth to the centre of V-FAN-IN, and from the centre of V-FAN-EX to an exhaust vent inner mouth | 3 | |
| L3.6.1.1 | Intake path and exhaust path both exist. | test | both true | 3 | G3 |
| L2.6.2 | The fan bore is free. | analysis | clear_of(ALL, V-FAN-BORE, 0.0) | 2 | |
| L3.6.2.1 | Bore column clear of printed material. | analysis | d ≥ 0.0 | 2 | |
| L2.6.3 | The intake and exhaust paths are separate groups. | analysis | no vent region is both: every region's centroid is either above the fan mid-plane or at or below the exhaust face (none between) | 1 | |
| L3.6.3.1 | Vent zones do not straddle the fan frame. | analysis | no region's section spans the fan mid-plane | 1 | |

### L1.7 The window shows the whole viewing area, not oversized

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The window is a through opening in the front panel sized from the viewing area. | inspection | in the panel plane, bounding box width in [26.0, 29.0] and height in [15.0, 22.0]; its bottom edge 0.4 to 2.0 below the view zone; its centre in X within 0.5 of `VIEW_AXIS` | 2 | |
| L3.7.1.1 | Window size (bounding box of V-AP-WIN). | inspection | width and height as L2.7.1 | 2 | |
| L3.7.1.2 | Window position vs `VIEW_AXIS`. | inspection | X offset ≤ 0.5; bottom margin 0.4 to 2.0 | 2 | |
| L2.7.2 | No printed material in the view zone. | analysis | clear_of(ALL, V-OLED-VIEW, 0.0) | 3 | |
| L3.7.2.1 | View zone clear. | analysis | d ≥ 0.0 | 3 | G4 |
| L2.7.3 | Window edges leave material. | analysis | ligament to the panel edges, the encoder hole and the seam ≥ 1.5 | 1 | |
| L3.7.3.1 | Window ligaments. | analysis | ≥ 1.5 | 1 | |

### L1.8 The OLED is fixed behind the window: two screw posts, two pins, 3 mm free behind it

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Two screw posts under the two header-side OLED holes and two pin posts at the two glass-side holes, axes along `VIEW_AXIS` (Y). | inspection | screw posts = 2 and pins = 2; screw-post axes within 0.25 and pin axes within 0.10 of their `HOLE` axes; all axes within 1.0° of Y | 3 | |
| L3.8.1.1 | OLED screw-post and pin count. | inspection | = 2 and = 2 | 3 | |
| L3.8.1.2 | Axis offset to the OLED `HOLE` axes. | analysis | screw posts ≤ 0.25 each; pins ≤ 0.10 each | 3 | |
| L2.8.2 | Screw-post tops coplanar and the PCB resting on them; M2 geometry (A7); the pins and pin posts (A16); the glass behind the panel. | inspection | screw posts: top spread ≤ 0.10; PCB top within 0.10 of the tops; OD 5.0 to 7.0; pilot Ø1.6 to 1.8; pilot depth ≥ engagement + 0.5, engagement = screw length − 1.2 ≥ 5.0; ≥ 0.8 of material beyond the tip. Pins: Ø 1.7 to 1.9; tip 0.3 to 0.9 short of the PCB back face and at least 0.5 inside the hole; pin-post end plane 0.5 to 1.5 in front of the glass front face. Glass front to the panel inner face 0.3 to 8.0 | 3 | |
| L3.8.2.1 | Screw-post top spread and PCB seating. | analysis | ≤ 0.10; ≤ 0.10, penetration ≤ 0.01 mm³ | 3 | |
| L3.8.2.2 | Pilot Ø, depth, engagement, tip material, OD; pin Ø, tip position and pin-post end plane. | inspection | as L2.8.2 | 2 | |
| L3.8.2.3 | Glass front to the panel inner face. | analysis | 0.3 ≤ g ≤ 8.0 | 2 | |
| L2.8.3 | The OLED is clear of the Pi, fan and encoder. | analysis | clear_of(ALL ∪ M-PI ∪ M-FAN ∪ M-ENC, M-OLED ∪ V-OLED-BACK, 0.5) with the screw-post end contact and the pins in their holes excluded; the pin posts stand 0.5 clear of the glass (L2.8.2) | 2 | |
| L3.8.3.1 | OLED clearance to the others. | analysis | d ≥ 0.50 | 2 | |

### L1.9 The encoder is mounted through the front panel

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | A round hole for the bushing in the front panel, on the encoder axis. | inspection | Ø 7.4 ± 0.1; axis within 0.25 of `AXIS`; axis within 1.0° of Y | 3 | |
| L3.9.1.1 | Hole count at the encoder (exactly one). | inspection | = 1 | 2 | |
| L3.9.1.2 | Hole diameter. | inspection | 7.3 ≤ Ø ≤ 7.5 | 3 | G4 |
| L3.9.1.3 | Hole axis offset and direction. | analysis | ≤ 0.25; ≤ 1.0° | 3 | |
| L2.9.2 | The body is behind the panel and clear; the panel is thin enough. | analysis | panel thickness at the hole 2.0 to 3.0; body shoulder within 0.30 of the panel inner face, no penetration; clear_of(ALL, body and terminals, 0.0) with the shoulder contact excluded | 3 | |
| L3.9.2.1 | Encoder shoulder seating and body clearance. | analysis | gap 0 to 0.30; penetration ≤ 0.01 mm³; d ≥ 0.0 | 3 | G4 |
| L3.9.2.2 | Panel thickness at the encoder hole. | inspection | 2.0 ≤ t ≤ 3.0 | 3 | |
| L2.9.3 | The nut and the shaft side are free outside the panel. | analysis | clear_of(ALL, V-ENC-NUT, 0.0) | 2 | |
| L3.9.3.1 | Nut zone clear. | analysis | d ≥ 0.0 | 2 | |
| L2.9.4 | Material round the encoder hole. | analysis | ligament to the window, the panel edges and the seam ≥ 1.5 | 1 | |
| L3.9.4.1 | Encoder-hole ligament. | analysis | ≥ 1.5 | 1 | |

### L1.10 Base and lid, located with a sliding fit and closed by snap latches

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Two separate bodies, each one connected shell, not fused, not interpenetrating. | analysis | BASE 1 shell; LID 1 shell; BASE ∩ LID ≤ 1.0 mm³ | 3 | |
| L3.10.1.1 | Shells per body. | analysis | = 1 each | 3 | G1 |
| L3.10.1.2 | Base and lid do not interpenetrate when closed. | analysis | ≤ 1.0 mm³ | 3 | G1 |
| L2.10.2 | A lip on the lid underside locates it on the base. | inspection | lip engagement 2.0 to 3.0; clearance 0.15 to 0.35 per side on every locating face; lid plate outline = base outer outline ± 0.5; seam gap ≤ 0.5; lid plate 2.0 to 4.0 thick | 2 | |
| L3.10.2.1 | Lip-to-wall gap. | inspection | 0.15 ≤ gap ≤ 0.35 | 2 | |
| L3.10.2.2 | Lip engagement and lid plate thickness. | inspection | 2.0 ≤ e ≤ 3.0; 2.0 ≤ t ≤ 4.0 | 2 | |
| L3.10.2.3 | Outline match and seam gap. | inspection | ±0.5; ≤ 0.5 | 1 | |
| L2.10.3 | Snap latches: four or more hooks on at least two opposite lateral walls. | inspection | 4 ≤ count ≤ 8; at least two hooks on each of two opposite walls, spaced ≥ 20.0 apart along the wall; blind catch recesses (no through windows) | 3 | |
| L3.10.3.1 | Hook count and distribution. | inspection | as L2.10.3 | 3 | G5 |
| L3.10.3.2 | Catch recesses are blind; wall behind a recess. | inspection | not through; ≥ 1.5 remains | 2 | |
| L2.10.4 | Hook geometry (A13). | analysis | free length L 10 to 20; thickness t 1.2 to 2.0; width ≥ 4.0; engagement y 0.6 to 1.2; strain 1.5 · t · y / L² ≤ 1.5 percent; lead-in 20° to 35°; return face 70° to 90° | 3 | |
| L3.10.4.1 | Beam length, thickness, width. | inspection | as L2.10.4 | 2 | |
| L3.10.4.2 | Engagement and strain. | analysis | 0.6 ≤ y ≤ 1.2; ε ≤ 1.5 percent | 3 | G5 |
| L3.10.4.3 | Lead-in and return angles. | inspection | 20° to 35°; 70° to 90° | 2 | |
| L2.10.5 | The lid cannot be lifted off without flexing the hooks. | test | hook head (return face) overlaps the catch shoulder by the engagement; the lid cannot rise by more than 0.5 | 2 | |
| L3.10.5.1 | Lid play along Z. | test | ≤ 0.5 | 2 | |
| L3.10.5.2 | Physical: open and close 20 times. | test | no hook cracks | 1 | physical, optional |

### L1.11 Protection: only listed openings; wall thicknesses 2 to 4 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | No unlisted openings. | analysis | no region admits a Ø2.0 sphere from outside into V-CAVITY other than the window, the encoder hole, the USB openings, the vents and the fan/OLED/Pi screw holes (none through) | 2 | |
| L3.11.1.1 | Probe for unlisted openings (ray grid 1 mm over the hull faces). | analysis | 0 unlisted paths | 2 | |
| L2.11.2 | Wall, floor and lid thicknesses. | inspection | each in [2.0, 4.0] | 2 | |
| L3.11.2.1 | Wall thickness (median, away from features), each of four walls. | inspection | 2.0 ≤ t ≤ 4.0 | 2 | |
| L3.11.2.2 | Floor thickness. | inspection | 2.0 ≤ t ≤ 4.0 | 2 | |
| L2.11.3 | Walls join the floor. | analysis | contact ≥ 90 percent of wall length × thickness | 2 | |
| L3.11.3.1 | Wall-to-floor contact. | analysis | ≥ 90 percent | 2 | |

### L1.12 Both parts print without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | In the declared print pose (FD6) no part has an unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12.0, bridges ≤ 15.0 and steps ≤ 1.2 deep (A12). | analysis | 0 offending faces (area > 1 mm²) per body | 2 | |
| L3.12.1.1 | Overhang, bridge and step scan per body, in its pose. | analysis | 0 patches | 2 | |
| L2.12.2 | Each mesh is manifold and a single shell. | analysis | 1 shell; manifold3d accepts it | 3 | |
| L3.12.2.1 | Shell and manifold status per body. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.12.3 | Each part rests on a flat face in its pose. | analysis | bed contact ≥ 50 percent of the plan bounding box | 1 | |
| L3.12.3.1 | Bed-contact area per body. | analysis | ≥ 50 percent | 1 | |
| L2.12.4 | No thin features; mating gaps ≥ 0.15. | analysis | min local thickness ≥ 0.8; min mating gap ≥ 0.15 | 1 | |
| L3.12.4.1 | Thin-feature scan. | analysis | as L2.12.4 | 1 | |
| L2.12.5 | Each part fits the bed. | inspection | bounding box in its pose ≤ 200 per axis | 1 | |
| L3.12.5.1 | Bounding box per body in its pose. | inspection | ≤ 200 | 1 | |

### L1.13 Size and stability

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | Closed outside size. | inspection | X ≤ 90.0, Y ≤ 70.0, Z ≤ 45.0 | 1 | |
| L3.13.1.1 | Assembly bounding box. | inspection | as L2.13.1 | 1 | |
| L2.13.2 | It stands without tipping, on a flat underside. | analysis | stable at 5° table tilt in every direction; underside flatness ≤ 0.2; no part below Z = 0 | 1 | |
| L3.13.2.1 | Support-polygon test (closed assembly plus 60 g at the models' centroids). | analysis | passes | 1 | |
| L3.13.2.2 | Underside flatness. | inspection | ≤ 0.2 | 1 | |

### L1.14 The package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.14.1 | Package: `base.stl`, `lid.stl` (closed pose, case frame, mm), the `.scad`, `layout.json` (L2.1.1 plus print poses), the agent's own report. | inspection | all present and readable | 3 | |
| L3.14.1.1 | Files parse; STLs in mm (largest bounding-box axis of each body 20 to 200). | inspection | true | 3 | G0 |
| L3.14.1.2 | Declared layout verifies under the seating rule (2.3). | analysis | residuals and distances as 2.3 | 3 | |
| L2.14.2 | Self-report agrees with the judge. | analysis | every `clear_of` and `inside` d within 0.10, same pass/fail; vent areas within 5 percent | 1 | |
| L3.14.2.1 | Self-report vs judge. | analysis | 100 percent agreement within 0.10; areas within 5 percent | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 14 |
| L2 | 47 |
| L3 | 80 (2 physical, the rest measured by Python on the STLs) |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.1.1.1, L3.14.1.1); **G1** manifold and two
bodies (L3.12.2.1, L3.10.1.1, L3.10.1.2); **G2** the Pi is fixed and both USB plugs seat (L3.2.1.1, L3.2.1.2, L3.3.1.1);
**G3** the fan and the air (L3.4.2.1, L3.4.3.1, L3.4.3.2, L3.6.1.1); **G4** the window and the encoder (L3.7.2.1, L3.9.1.2,
L3.9.2.1); **G5** the latches (L3.10.3.1, L3.10.4.2).

---

## 6. Design-specific rubric (the generic rubric was absent when this was written)

### 6.1 Procedure

1. G0: check the files in L2.14.1 exist and load; if the STLs are missing or unreadable stop (DOES NOT MEET, one defect on L3.14.1.1).
2. Units: each body's largest bounding-box axis within 20 to 200; if inches or metres record a defect, do not rescale.
3. Normalise the frame (1.1) with rotations by multiples of 90° and X mirroring only; record the transform.
4. Build every M- model and V- envelope independently from `parts/*/part.json` and the declared layout; run R1 to R5 and verify
   the seating rule (2.3).
5. Run every applicable L3 with Python in order; record value, limit, signed margin (negative = fail), PASS / FAIL /
   UNVERIFIED (counts as FAIL). N/A only for the physical tests with no print.
6. Look at renders afterwards; render-only findings are observations.
7. Decide (6.3), report (6.4).

### 6.2 Measurement recipes (trimesh 5.1, manifold3d 3.5; count shells with `decompose()`)

```python
import numpy as np, trimesh, manifold3d as m3d
M = m3d.Manifold
def load(p):
    tm = trimesh.load(p, force="mesh")
    return tm, M(m3d.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                          tri_verts=np.asarray(tm.faces, np.uint32)))
def clear_of(bodies, vol, c):
    pen = (bodies ^ vol).volume()
    if pen > 0.01: return {"d": None, "pen": pen, "where": (bodies ^ vol).bounding_box()}
    return {"d": bodies.min_gap(vol, c + 5.0), "pen": 0.0}   # PASS: pen <= 0.01 and d >= c - 0.02
def inside(vol, solids, c, big=2000):
    hull = M.hull(solids); out = (vol - hull).volume()
    if out > 0.01: return {"d": None, "outside": out}
    shell = M.cube([big]*3, True) - hull
    return {"d": min(vol.min_gap(solids, c + 5.0), vol.min_gap(shell, c + 5.0))}
```

- **Rotated poses:** transform catalogue solids by 4 × 4 matrices (`Manifold.transform`); angles between axes by `arccos` of the dot product.
- **Standoffs, posts, holes:** slice by a plane normal to the claimed axis at mid-height or mid-thickness; smallest enclosing circle
  (posts) or largest inscribed circle (holes); two slices give the axis direction; depth by ray cast along the axis; the tip
  material is the distance from the pilot end to the nearest outer surface.
- **Vents and areas:** slice each lateral wall at mid-thickness (a plane normal to the wall); the through-region polygons are the
  vent regions (ignore regions under 1 mm²); area = polygon area (the open area normal to the wall); intake/exhaust by the
  area-weighted centroid height; slot width = the polygon's smaller bounding-box side (median over the slots).
- **Air path:** voxelise V-CAVITY at 0.5, remove all solids (printed bodies, M-PI, M-FAN except V-FAN-BORE, M-OLED, V-OLED-BACK, M-ENC), erode by 2.5 (distance transform ≥ 2.5), label 26-connected components of the eroded space, and test that the component containing the centre of V-FAN-IN also contains eroded-space voxels within 3.5 of the cavity-side face of an intake vent, and that the component containing the centre of V-FAN-EX contains such voxels at an exhaust vent. (A Ø5.0 sphere cannot enter a 2 to 3 wide slot; the vent rule L2.5.4 sizes the slot.)
- **Window and view zone:** slice the front panel at mid-thickness; the through-hole polygon near the OLED centre gives the
  bounding box, bottom edge and centre; V-OLED-VIEW is the 25.0 × 14.0 × 3.0 prism; `clear_of` as above.
- **Snap hooks:** isolate each hook by slicing the lid at the catch height; beam free length from the lid underside to the hook
  head, thickness from the section, y = the hook protrusion beyond the beam face minus the clearance gap to the wall; angles from
  the facet normals of the hook head against the insertion axis (Z); ε = 1.5 · t · y / L².
- **Apertures, probe, thickness, gap, ligament:** as in the enclosure rubric (end-wall slab minus bodies, ray grid of 1 mm for
  unlisted openings then a Ø2.0 sweep; ray casts on a 2 mm grid at least 3 mm from edges and openings, median is the value).
- **Printability:** transform each body into its declared print pose; a face with normal n overhangs if n_z < −cos 45° and
  z > 0.05, minus round holes Ø ≤ 12 in vertical walls, bridges ≤ 15 between supports and horizontal steps ≤ 1.2 deep.
  Bed contact: area of faces with n_z < −0.999 at z < 0.05 over the plan bounding-box area. Thin features: inward ray cast.
- **Stability:** centre of mass of the closed assembly plus 60 g at the model centroids, projected on the table at 5° tilt in every
  direction, must stay inside the support polygon of the underside.

### 6.3 Classes

| Class | Rule |
|---|---|
| **WRONG** | any gate G0..G5 fails |
| **MINOR** | no gate fails but a weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |
| **MEETS requirements** | CORRECT and every applicable non-physical weight-1 and weight-2 L3 passes |

Also report the weighted score Σ(weight × pass)/Σ(weight) over applicable L3s and the worst normalised margin among weight-3
L3s. Precedence: the plug-seating and clearance checks outrank opening size; numbers in this file beat `part.json` (a
disagreement is a defect on the L3 it breaks, with where = the part.json field); designed contact (1.3) is never interference;
never relax a criterion; never infer a pass from a render.

### 6.4 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first (gates, then weight 3, 2, 1). Fields: `req` (L3, L2,
L1), `status`, `body` (base, lid, both, layout), `feature` (by function and SCAD name), `face` (surface and outward normal),
`location` (case-frame coordinates, a point or a box), `measured / limit / margin`, `reference` (the model or envelope and its
datum), `render`, `evidence` (saved files), `needed` (a numeric target, never a design instruction). Group L3s with one
geometric cause under the first and list the others in `also_fails`; separate observations from defects.

---

## 7. Feasibility (a concrete design that meets every L3)

Case frame, mm. Wall 2.4, floor 2.4, lid plate 3.0. Inner cavity X ±34.0 (68.0), Y 2.4 to 54.1 (51.7), Z 2.4 to 36.5 (34.1).
Outer 72.8 × 56.5 × 39.5.

| Feature | Value |
|---|---|
| M-PI pose | rotated 180° about Z, Pi origin at case (32.5, 52.7): PCB X ±32.5, Y 22.7 to 52.7, Z 8.4 to 9.8; `USB_DATA_MOUTH` (−8.9, 53.6, 11.1), `USB_POWER_MOUTH` (−21.5, 53.6, 11.1), axes +Y; SD cage reaches X 33.5; HDMI mouth (20.1, 53.2) |
| Pi standoffs | 4 at (±29.0, 26.2) and (±29.0, 49.2), height 6.0 (Z 2.4 to 8.4), OD 6.0, pilot Ø2.1 depth 7.4 (tip Z 1.0); M2.5 × 8 (engagement 6.6) |
| M-FAN pose | X ±20, Y 13.6 to 53.6, Z 19.0 to 29.0; axis (0, 33.6), airflow −Z; holes (±16.0, 17.6) and (±16.0, 49.6) |
| Fan posts | on the lid, OD 7.0, Z 29.0 to 36.5 (7.5 long), pilots Ø2.5 depth 6.8 (Z 29.0 to 35.8, 3.7 of material left to the lid top); bolts M3 × 16 (engagement 6.0) |
| M-OLED pose | PCB X −31.0 to −3.7 (centre −17.35), Z 3.2 to 31.0, Y 8.4 to 9.6; glass Y 7.0 to 8.4 facing −Y; header edge down; `ACTIVE_CENTER` (−17.35, 7.0, 17.85) |
| OLED screw posts | 2 teardrop posts, OD 5.0, Y 2.4 to 8.4, at X −29.1 and −5.6, Z 5.2 (header-side holes, 3.0 from the glass edge); pilot Ø1.7 depth 7.5 (tip Y 0.9); M2 × 8 (engagement 6.8) |
| OLED pins | 2 teardrop pin posts, OD 5.0, Y 2.4 to 6.5, at X −29.1 and −5.6, Z 29.0 (glass-side holes), each with a pin Ø1.8 from Y 6.5 to Y 9.0 through the PCB hole (tip 0.6 short of the back face Y 9.6) |
| Window | in the front wall, X −17.35 ± 13.0 (26.0), bottom Z 10.35, vertical sides to Z 25.35, then 45° corbels to Z 30.95 at |ΔX| 7.4, flat roof 14.8 wide; height 20.6 |
| M-ENC pose | axis X +17.0, Z 17.85; shoulder on the panel inner face (Y 2.4); body Y 2.4 to 8.9, terminals to Y 12.4; bushing Y 2.4 to −4.6; hole Ø7.4 through the 2.4 panel |
| USB openings | rear wall, X −8.9 ± 5.3 and −21.5 ± 5.3 (ligament 2.0 between), Z 7.3 to 14.9; plug 10.0 × 7.0 at Z 7.6 to 14.6 |
| Vents | slots 2.4 wide, pitch 3.9, 5.5 tall. Intake Z 27.0 to 32.5: rear wall X ±30 (15 slots, 198), ±X walls Y 17 to 41 (6 slots each, 79 each); total 356. Exhaust Z 5.0 to 17.0: ±X walls Y 17 to 41 (6 slots each, 173 each), rear wall X 1 to 32 (7 slots, 202); total 548 |
| Lid | plate Z 36.5 to 39.5, outline 72.8 × 56.5; lip wall 1.2, Z 34.2 to 36.5 (engagement 2.3), 0.25 off the inner wall faces |
| Hooks | 4: (±X, Y 10.0) and (±X, Y 47.0); beam 6.0 wide, t 1.4, free length 14.0 (Z 22.5 to 36.5, the lip relieved beside it); head Z 22.5 to 25.25 protrudes 1.0 beyond the beam face (engagement 0.75), lead-in 25°, return face 90° (a 1.0 step); catch recess in the wall inner face, depth 0.75, Y ±3.5, Z 22.25 to 25.25 |
| Print poses | BASE floor down; LID plate down |

Checks by hand (the solids of this sketch were also built and measured, see the Audit):
- Pi: PCB to the side walls 34.0 − 32.5 = 1.5, SD cage 34.0 − 33.5 = 0.5 (≥ 0.5 and inside 0.2); rear: mouth Y 53.6, inner face 54.1 gives
  0.5 (inside ≥ 0.2); HDMI Y 53.2, 0.9 from the wall. Standoff wall: pilot tip Z 1.0 ≥ 0.8; depth 7.4 in [7.1, 7.6].
- USB: plug overmold Y from 53.6 + 1.5 = 55.1 inside the wall thickness (54.1 to 56.5), so it enters the 10.6 × 7.6 opening; clearance 0.3 on
  each side (Z 7.3 vs 7.6, 14.9 vs 14.6; X 5.3 vs 5.0); oversize 0.3 ≤ 1.5; the two overmolds are 2.6 apart; ligaments 2.0 between the
  openings, 7.3 to the floor line and 21.6 to the seam (36.5 − 14.9).
- Fan: exhaust face Z 19.0 over the highest Pi top (HDMI Z 13.0): 6.0 ≥ 5.0; inlet face 29.0 to the ceiling 36.5: 7.5 ≥ 5.0. The inlet box
  (Z 29.0 to 34.0) stops 0.2 under the lid lip's rear wall (Y 52.65 to 53.85, bottom Z 34.2) because the fan reaches Y 53.6; the air boxes are free
  except the Ø7.0 post columns (excluded). Fan X ±20 stays 14 from the side walls; plan offset of the fan axis (0, 33.6) from the
  Pi centre (0, 37.7) is 4.1 ≤ 6.0. Fan to the OLED back zone (to Y 12.6) 1.0 ≥ 0.5; to the encoder terminals 1.2. Screw head bottom
  Z 16.0 over the Pi (Z 13.0): 3.0 ≥ 1.0.
- OLED: glass front Y 7.0 to the panel inner face 2.4: 4.6 (band 0.3 to 8.0). View zone 25.0 × 14.0 × 3.0 from Y 7.0 toward the front
  (Y 4.0 to 7.0), X −17.35 ± 12.5, Z 10.85 to 24.85: inside the window (width 26.0, bottom 10.35, vertical sides to 25.35); the screw posts
  (Z 2.7 to 7.7) and the pin posts (Z 26.5 to 31.5) are outside it; the pin posts end 0.5 before the glass; window ligament to the wall top
  36.5 − 30.95 = 5.55 ≥ 1.5, to the encoder hole (X 13.3 to 20.7 against the window edge X −4.35): 17.65. Pin tip 0.6 short of the back face,
  0.6 inside the hole, Ø1.8 in the Ø2.0 hole (0.1 per side, axis offset ≤ 0.10).
- Encoder: panel 2.4 (2.0 to 3.0); hole Ø7.4 (bushing Ø7.0, 0.2 per side); bushing protrudes 4.6 outside, the nut zone Ø11 × 3 (Y −3.0 to 0) is
  free; body X 11.0 to 23.0 clears the window and the fan (Y gap 1.2).
- Vents: intake 356 ≥ 300, exhaust 548 ≥ 300; slot width 2.4 (2.0 to 3.0), ligament 1.5; intake band Z 27.0 to 32.5 is above the fan
  mid-plane (24.0), exhaust band Z 5.0 to 17.0 is below the exhaust face (19.0); no region between; the lip (Z ≥ 34.2) clears the slots
  (≤ 32.5) by 1.7. Air path (measured on the solids, 0.5 voxels, erosion 2.5): the intake inner mouths and the centre of the inlet air box are
  in one free component, and the centre of the exhaust air box is connected to the exhaust inner mouths; the Pi and the OLED leave 2.5 of free radius.
- Hooks: ε = 1.5 × 1.4 × 0.75 / 14² = 0.80 percent ≤ 1.5; wall behind the recess 2.4 − 0.75 = 1.65 ≥ 1.5; hooks 37.0 apart on each wall.
  Beam bottom Z 22.5 clears the Pi (Z 13.0) and the fan (X ±20 against the beam at X 32.35).
- Size 72.8 × 56.5 × 39.5 (limits 90, 70, 45). Printing: base walls and standoffs vertical; slots 2.4 wide; the window roof flat span 14.8
  ≤ 15.0 with 45° corbels; USB openings 10.6 wide; recess roof 7 wide; OLED posts and pins teardrop (45° lower flanks); encoder hole round Ø7.4.
  Lid plate down: posts, lip and hooks stand up; the hook return face is a 1.0 deep step (≤ 1.2).

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 | Method | Words in the request |
|---|---|---|---|---|---|---|
| L1.1 | layout | L2.1.1-3 | L3.1.1.1, L3.1.2.1, L3.1.3.1-2 | L1.1 | inspection | "Raspberry Pi Zero 2 W", "fan", "OLED", "encoder" |
| L1.2 | Pi mounted | L2.2.1-3 | L3.2.1.1-3, L3.2.2.1-3, L3.2.3.1-3 | L1.2 | inspection | "four 2.75 mm holes on a 58 x 23 mm pattern" |
| L1.3 | USB ports at the rear | L2.3.1-3 | L3.3.1.1-2, L3.3.2.1, L3.3.3.1-2 | L1.3 | test | "both micro-USB ports ... through the rear wall" |
| L1.4 | fan above the Pi | L2.4.1-4 | L3.4.1.1-2, L3.4.2.1-3, L3.4.3.1-2, L3.4.4.1-2 | L1.4 | analysis | "40 mm fan sits above the Pi ... 32 mm hole pitch ... blowing down" |
| L1.5 | side vents | L2.5.1-4 | L3.5.1.1, L3.5.2.1, L3.5.3.1-2, L3.5.4.1-2 | L1.5 | analysis | "vents in the side walls" |
| L1.6 | exhaust path | L2.6.1-3 | L3.6.1.1, L3.6.2.1, L3.6.3.1 | L1.6 | test | "the heat of the Pi must have a path out" |
| L1.7 | OLED window | L2.7.1-3 | L3.7.1.1-2, L3.7.2.1, L3.7.3.1 | L1.7 | analysis | "window ... viewing area 25 x 14 mm" |
| L1.8 | OLED mounting | L2.8.1-3 | L3.8.1.1-2, L3.8.2.1-3, L3.8.3.1 | L1.8 | inspection | "0.96 inch SSD1306 OLED (27.3 x 27.8 mm)" |
| L1.9 | encoder | L2.9.1-4 | L3.9.1.1-3, L3.9.2.1-2, L3.9.3.1, L3.9.4.1 | L1.9 | inspection | "EC11 rotary encoder beside it on the same panel" |
| L1.10 | base, lid, latches | L2.10.1-5 | L3.10.1.1-2, L3.10.2.1-3, L3.10.3.1-2, L3.10.4.1-3, L3.10.5.1-2 | L1.10 | inspection | "a base and a lid that closes with snap latches" |
| L1.11 | protection | L2.11.1-3 | L3.11.1.1, L3.11.2.1-2, L3.11.3.1 | L1.11 | analysis | "case" (implied) |
| L1.12 | printable | L2.12.1-5 | L3.12.1.1, L3.12.2.1, L3.12.3.1, L3.12.4.1, L3.12.5.1 | L1.12 | analysis | "printed on an FDM printer without supports" |
| L1.13 | desktop use | L2.13.1-2 | L3.13.1.1, L3.13.2.1-2 | L1.13 | analysis | "desktop console" |
| L1.14 | evidence | L2.14.1-2 | L3.14.1.1-2, L3.14.2.1 | L1.14 | inspection | needed by the judge (not the owner's words) |

---

## Audit

Adversarial audit (second agent). Method: all five catalogue parts load and pass `parts.validate` / `parts.gate`; every number of
section 7 was recomputed by hand, and the feasibility design was then built as solids (manifold3d: base, lid, Pi, fan, OLED, encoder,
plugs and every V- envelope) with a 0.5 mm voxel Ø5.0 sphere-path test. That found real contradictions (below). `claude-context` was
unavailable (server failed to connect), so targeted grep was used. The generic `generalize/rubric.md` still does not exist; section 6 is
this entry's rubric (it follows `benchmarks/enclosure/rubric.md`).

Fixes made (all in place):
1. **OLED posts collide with the glass (G4-adjacent, L2.8.3 and L3.8.3.1 fail).** The two glass-side OLED holes (module y 25.8) lie 1.5 mm
   from the glass edge (y 24.3), so an OD 5.0 post (radius 2.5), the catalogue's own Ø4.0 hole keep-out and an M2 head (radius 2.0) all
   overlap the glass (7.0 mm³ measured). No wall-correct screw post fits there. Decision (A16): screws and posts only at the two
   header-side holes (3.0 from the glass: post clearance 0.5), and locating pins Ø1.8 on pin posts at the two glass-side holes (pin posts end
   0.5 before the glass, pin tips 0.6 short of the PCB back face). L1.8, L2.8.1, L2.8.2, L3.8.1.x, L3.8.2.x, the seating rule, designed
   contact 3 and the sketch were rewritten; L3 ids and counts are unchanged.
2. **Inlet air box hit the lid lip.** The fan reaches Y 53.6 and the lip's rear wall stands at Y 52.65 to 53.85 down to 2.5 below the seam, inside the
   inlet box (Z 28.5 to 33.5): 54 mm³ of penetration (L3.4.3.1, a G3 gate). Fixed by raising the cavity: ceiling Z 36.5 (was 33.5), fan Z 19.0 to
   29.0, lip engagement 2.3, so the box stops 0.2 under the lip. Everything above the fan moved with it (posts 7.5 long, hooks Z 22.5 to 36.5, catch
   recess Z 22.25 to 25.25, intake band Z 27.0 to 32.5, window ligament 5.55, size 72.8 × 56.5 × 39.5 inside 90 × 70 × 45). The old design
   also left the free height above the fan exactly 5.0 and below it 5.5, equal to the sphere diameter, which no voxel test can pass reliably; they
   are now 7.5 and 6.0.
3. **L1.6 / L2.6.1 contradicted L1.5.** A Ø5 sphere cannot pass a 2 to 3 mm slot. The sphere test is now inside the case, between the vent's inner
   mouth (cavity side, within 3.5) and the centres of the two air boxes; recipe and V-SPHERE-PATH rewritten (0.5 voxels). Measured on the rebuilt
   solids: both paths exist.
4. **Hidden numbers moved into the L1 text the agent receives:** 0.5 / 0.2 mm Pi clearances (L1.2), fan axis within 6 mm of the Pi centre (L1.4), vent
   rules (1.5 mm ligament, two walls per zone, no vent in the panel, lid or floor, the intake and exhaust definitions) (L1.5), window size bands
   (L1.7), OLED 0.5 mm clearance and 3 mm free behind it (L1.8), panel 2 to 3 mm (L1.9), hook rules from A13 (L1.10), the 1.2 mm step allowance
   (L1.12).

Measured on the rebuilt solids: base and lid 1 shell each, base ∩ lid 0, all reference models free of interference, plug gaps 0.30, view zone clear,
inlet, exhaust and bore volumes clear, fan to OLED back zone 1.0, fan to Pi above 5, glass to printed parts 0.50. Checked and left unchanged: counts (14 / 47 / 80),
L1 count 14, no duplicate ids, Pi / USB geometry, hook strain 0.80 percent, vent areas 356 and 548, window corbels, size limits.
Residual uncertainty: the OLED glass offset (±1.0) and hole inset (±0.3) are assumed in the catalogue; the print-pose overhang rules for teardrop
posts, pins and the hook step were reasoned, not sliced.
