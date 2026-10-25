# G06 Pico clock with sloped 1602 LCD: requirements (L1 / L2 / L3)

Training design of the generalisation set (family electronics_enclosure; capabilities window, angled_face,
stacked_boards, datum_placement, plug_envelope_opening, standoffs). The machine-readable request (L1 only,
`dev.json` format) is `design.json` next to this file. It is modelled on `benchmarks/enclosure/requirements.md`
(E1-01) and uses the same conventions: tolerances (1.2), `clear_of`, `inside` and designed contact (1.3),
reference models and envelopes (2), assumptions with uncertainty and fixed decisions (3), a tree whose every L3 is
measured by Python on the delivered STLs (4), gates (5), a feasibility sketch (7) and traceability (8).

**Brief (plan.json, verbatim):** "I want a desk clock: a 1602 LCD module (80 x 36 mm, viewport 64.5 x 14 mm) tilted
30 degrees from the table, with a Pico 2 mounted behind it. The front face is sloped, the LCD is fixed on its four
2.5 mm holes, and the Pico's micro-USB must open through the back. It prints without supports."

**Rubric note.** The generic file `benchmarks/generalize/rubric.md` did not exist when this entry was written, so
section 6 below is the design-specific rubric (recipes, classes, how to report where a defect is). If the generic
rubric appears later it applies on top of this file; where they disagree the numbers in this file win.

**How to read the tree.** L1 is what the owner needs, L2 an engineering requirement, L3 a check on the geometry. Each
L3 has a method (inspection, analysis, demonstration, test, human; as in `design.json`), a pass/fail criterion with a
number and tolerance, a weight (3 critical, 2 major, 1 minor) and a gate mark (G0..G5) on must-pass rows. Numbers that
come from an assumption (section 3) are provisional until the owner confirms them. Never relax a criterion because the
agent fails it.

---

## 1. Frames, tolerances, designed contact

### 1.1 Frames

- **Case frame:** X across the clock's width, Y from the front (low end of the slope) to the back (the wall with the
  USB opening, +Y), Z up, Z = 0 on the underside of the base standing on the table. The grader normalises a design
  delivered rotated by multiples of 90 degrees about Z or mirrored in X into this frame (the back wall is the one with the
  USB opening; the LCD leans toward the opposite wall); never penalised.
- **LCD frame** (catalogue `lcd1602_hd44780`): origin at the PCB min corner, PCB bottom Z = 0, bezel and glass on +Z;
  80 along X_L, 36 along Y_L. Its pose in the case frame is declared in `layout.json`. With tilt θ = 30° about X:
  `VIEW_AXIS` (the module +Z) = (0, −sin θ, cos θ), the module +Y_L runs up the slope along u = (0, cos θ, sin θ).
- **Pico frame** (catalogue `rpi_pico2`): origin at the PCB min corner, PCB bottom Z = 0, components on +Z, USB end at −X;
  `USB_AXIS` must point along case +Y.
- Lengths in mm, angles in degrees.

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered meshes, never by eye.

| Quantity | ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm | a value passes if it meets the limit within ε |
| angle | 0.5° | same |
| intersection volume | 0.01 mm³ | "no interference" means ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the section | what a screw sees |
| boss / standoff OD | smallest enclosing circle of the section | |

### 1.3 Interference checks and designed contact

- **`clear_of(bodies, volume, c)`**: minimum distance between the printed bodies and `volume` is ≥ c − ε, penetration ≤ 0.01 mm³.
- **`inside(volume, void, c)`**: `volume` lies in `void` and every point is ≥ c − ε from the void boundary.

`bodies` is ALL (base and panel, closed), BASE or PANEL. The grader builds every reference model and envelope itself from
the catalogue and the declared layout; the agent's copies are not trusted for grading.

**Designed contact for this design (never interference; only penetration > 0.01 mm³ counts for these pairs):**
1. the LCD PCB underside resting on its four standoff tops, and the Pico PCB underside on its four standoff tops,
2. a screw in its pilot hole and a screw head on the surface it clamps,
3. the bezel front face against the panel underside (gap 0 to 0.3 allowed),
4. the panel lip against its locating faces (fit set by L2.7.2) and the panel underside resting on the wall tops (rim).

A distance of zero is a pass for these pairs.

---

## 2. Reference models, envelopes, datums

### 2.1 Reference models (M-)

Poses are the ones the design declares in `layout.json`; the feasibility sketch in 7 is one valid layout.

| Name | What | Source | Size and datums used |
|---|---|---|---|
| **M-LCD** | 1602 LCD module | catalogue `lcd1602_hd44780` | PCB 80.0 × 36.0 × 1.6; bezel 71.2 × 24.2 up to overall height 13.0 (module Z); holes Ø2.5 at 2.5 from each edge (pitch 75.0 × 31.0); datums `PCB_BOTTOM`, `FACE_TOP` (Z = 13.0), `VIEW_AXIS`, `HOLE` (4 axes), keep-out `view_zone` 64.5 × 14.0 × 3.0 centred on the PCB, starting at `FACE_TOP` |
| **M-PICO2** | Raspberry Pi Pico 2 | catalogue `rpi_pico2` | PCB 51.0 × 21.0 × 1.0; receptacle 5.5 (X) × 8.0 (Y) × 2.8 (Z) on top, overhanging the short edge by 1.3; holes Ø2.1 on a 47.0 × 11.4 pattern; datums `USB_MOUTH`, `USB_AXIS`, `PICO_HOLE` (4), `PCB_BOTTOM`; tallest other top part 1.5 above the PCB |
| **M-PLUG-USB** | micro-USB B plug | catalogue `plug_microusb_b` | shell 6.9 × 1.85, inserted 5.0, exposed 1.5; overmold 10.0 × 7.0 × 20 |
| **M-SCREW** | M2 self-tapping screw | catalogue `screw_m2_selftap` | thread Ø2.0, head Ø4.0 × 1.6, clearance Ø2.4, pilot Ø1.6 to 1.8; length declared in `layout.json`, a stock length (4, 5, 6, 8, 10, 12) |

### 2.2 Envelopes (V-) and computed volumes

| Name | Definition | Used by |
|---|---|---|
| **V-VIEW** | the LCD `view_zone` prism: 64.5 × 14.0 × 3.0, base on the bezel face (`FACE_TOP`), extruded along +`VIEW_AXIS` | L2.3.2 |
| **V-LCD-BACK** | the back-side component zone of the LCD (A3): 80.0 × 36.0 × 2.0 below the PCB underside, minus a Ø5.0 column on each `HOLE` axis (the standoff tops) | L2.5.2 |
| **V-PICO** | M-PICO2 plus its receptacle (including the part beyond the PCB edge) | L2.5.3 |
| **V-PICO-TOP** | the Pico top-side zone: PCB footprint from the PCB top to 1.5 above it, plus the receptacle solid | L2.5.2 |
| **V-USB-PLUG** | M-PLUG-USB at full mate on `USB_MOUTH`, overmold swept along `USB_AXIS` to 40 beyond the back wall | L2.6.1, L2.6.2 |
| **V-DRIVER-LCD-k** | Ø6.0 column on the axis of LCD screw k from the PCB top along +`VIEW_AXIS`, 50 long, panel off | L2.11.3 |
| **V-DRIVER-PICO-k** | Ø6.0 column on each Pico screw axis from the PCB top, 50 up, panel off | L2.11.3 |
| **V-DRIVER-PANEL-k** | Ø6.0 column on each panel-screw axis from the panel outer face, 50 along the panel normal | L2.7.4 |
| **V-EXTRACT-LCD** | M-LCD with its screws, swept along +`VIEW_AXIS` by 40, standoff-top contact excluded | L2.11.1 |
| **V-EXTRACT-PICO** | M-PICO2 swept along +Z by 40 (the receptacle sweeps out through the opening region of the back wall plane, not needed to exit) | L2.11.2 |
| **V-CAVITY** | the closed case's internal void: convex hull of BASE ∪ PANEL minus BASE ∪ PANEL, component containing the Pico centroid | L2.5.3, L2.8.1 |
| **V-AP-USB** | the opening actually present in the back wall: the slab between its inner and outer faces over its full X and Z extent minus BASE ∪ PANEL | L2.6.2, L2.6.3 |
| **V-AP-WIN** | the window actually present in the panel: the panel slab minus PANEL, regions through the panel | L2.3.1 |

### 2.3 Sanity checks and seating rule

| ID | Check | Pass |
|---|---|---|
| R1 | M-LCD bounding box in mm | 80.0 × 36.0 × 13.0 ± 0.3; PCB 80 × 36 × 1.6 ± 0.1 |
| R2 | M-LCD hole pattern | Ø2.5 ± 0.1; pitch 75.0 × 31.0 ± 0.1 |
| R3 | M-PICO2 PCB, holes, USB axis along −X in its own frame | 51.0 × 21.0 × 1.0 ± 0.2; holes Ø2.1, 47.0 × 11.4 ± 0.1 |
| R4 | every V- envelope's datums equal its model's | ≤ 0.01 |

**Seating rule.** M-LCD and M-PICO2 are placed at the poses in `layout.json`. The grader verifies the declaration: each
PCB underside lies on its standoff tops (distance ≤ 0.10) and each model's hole axes are coaxial with the standoff pilots
(least-squares residual ≤ 0.25). If the declaration is missing or fails, the models are seated by that fit instead; with
no standoffs, every L1.4 and L1.5 check fails.

---

## 3. Assumptions, fixed decisions and open questions for the owner

Each line gives the value chosen and why. All derived from the brief, the catalogue or convention; none asked.

| # | Question | Value chosen | Why and uncertainty |
|---|---|---|---|
| A1 | What does "tilted 30 degrees from the table" mean? | The angle between the LCD plane and the horizontal table is 30.0°; the display faces up and toward the viewer (front). | Literal reading. Alternative (30° from vertical) is not graded. |
| A2 | What does "a Pico 2 mounted behind it" mean? | Behind and below the LCD, lying flat on the base, partly under the rear of the LCD, with its long axis along the case depth (Y) and USB toward the back wall. | The sloped roof leaves a wedge of space below and behind the LCD; the Pico must fit there with the USB at the back wall. |
| A3 | What is on the back of the LCD? | A back-side component zone 2.0 thick (driver epoxy blob, backlight pins; ±1.0) over the whole 80 × 36 PCB, except the Ø5.0 standoff columns. | The catalogue models only the PCB and the bezel; real modules carry a COB driver and solder joints on the back. |
| A4 | Window margin? | The viewport (64.5 × 14.0) is not clipped; the window exceeds it by 0.5 to 2.0 per side. Window upper bound is also 1.5 inside the bezel outline (ligament over the bezel). | A viewport that is bigger than needed hides the bezel edge. Module viewport offsets of up to 1.5 mm exist (part.json notes), so the minimum margin is 0.5 per side. |
| A5 | LCD dimensions? | PCB 80 × 36 × 1.6; bezel 71.2 × 24.2; overall height 13.0; holes at 2.5 from the edges. | part.json, with the stated uncertainty (bezel ± 0.5, height 11.5 to 14). Measure the owner's module. |
| A6 | Pico mounting? | Four standoffs at the Pico's own holes; M2 self-tapping screws (pilot 1.6 to 1.8) through the Ø2.1 holes; no headers. Standoff height 3.0 to 8.0 (solder side ≥ 3.0, rule `solder_side_default`). | Castellated Pico soldered flat is possible; the screws keep it removable. |
| A7 | Screw engagement rule? | Engagement = screw length − thickness of the clamped plate (PCB or panel); it must be ≥ 5.0 (rule `min_engagement` of `screw_m2_selftap`) and ≤ pilot depth − 0.5. | Self-tapping M2 in PLA needs about 2.5 × d of thread. |
| A8 | Plug sizes? | Micro-USB overmold 10.0 × 7.0 (catalogue). | Typical cable. Measure the owner's cable. |
| A9 | Panel closure? | Two M2 self-tapping screws at the rear corners of the panel (FD2). | Robust, easy to print; the front edge is held by the lip. |
| A10 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. Sliding fit 0.15 to 0.35 per side. Wall, floor and panel 2.0 to 4.0. No face steeper than 45° from vertical; round holes Ø ≤ 12.0 and bridges ≤ 15.0 exempt. | Common printers; rules in design_rules.json. |
| A11 | Size and stability? | Closed outside ≤ 100 × 80 × 70; stable at 5° table tilt. | A desk clock; the tight design is about 86 × 71 × 63. |
| A12 | Buttons, vents, labels? | None. | A Pico and an LCD draw well under 1 W. A RTC, buttons or a buzzer would add openings; not in the brief. |
| A13 | Electrical hookup? | LCD header and Pico wiring by loose leads; no connector or PCB inside is modelled. | Not a mechanical concern. |

### Fixed decisions (one choice, no alternatives accepted)

| # | Decision | Why |
|---|---|---|
| FD1 | The LCD long side (80) lies along case X; the module's top edge (the 36 side, +Y_L) is the high edge of the slope; the display faces front and up. | One reading of "tilted from the table" and "front face is sloped". |
| FD2 | Two printed bodies: a BASE (floor, four walls, all standoffs, both closure bosses) and a PANEL (a flat sloped slab with the window, a locating lip and two screw holes). The panel's underside plane is the plane the wall tops lie in. The panel is held by 2 × M2 self-tapping screws along the panel normal into two base bosses at the rear corners. | Removable panel so the LCD and Pico can be installed; a sloped roof printed as a flat slab needs no supports. |
| FD3 | The Pico's USB axis points along case +Y (to the back wall); the Pico stands on four vertical standoffs. | "micro-USB must open through the back". |
| FD4 | The LCD is held by four M2 self-tapping screws through its holes from the component side, into four standoffs whose axes lie along the tilted normal (`VIEW_AXIS`). | "fixed on its four 2.5 mm holes". |
| FD5 | The panel underside rests on the wall tops and touches (gap 0 to 0.3) the bezel front face; the lip locating faces are vertical. | The bezel face positions the glass behind the window. |
| FD6 | Print poses: BASE floor down; PANEL outer face down on the bed (rotated by 30° about X from its assembly pose), lip up. The layout declares them. | Sloped face prints flat; no overhang beyond 45°. |

---

## 4. Requirements tree

### L1.1 The LCD and the Pico are placed from the catalogue, declared, and do not collide

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares the layout: pose of M-LCD (origin, tilt), M-PICO2 (origin, rotation about Z), each screw (axis, length), print pose of each body. | inspection | `layout.json` present, parses, names the catalogue ids | 3 | |
| L3.1.1.1 | Layout parses and every catalogue id exists. | inspection | true | 3 | G0 |
| L2.1.2 | The Pico's USB faces the back wall. | inspection | `USB_AXIS` within 1.0° of +Y | 3 | |
| L3.1.2.1 | USB axis direction in the case frame. | inspection | angle to +Y ≤ 1.0° | 3 | |
| L2.1.3 | The two models do not collide and the Pico is partly under the LCD. | analysis | M-LCD ∩ M-PICO2 ≤ 0.01 mm³; plan overlap of the Pico and the LCD silhouette ≥ 100 mm² | 3 | |
| L3.1.3.1 | Interference between the reference models. | analysis | ≤ 0.01 mm³ | 3 | |
| L3.1.3.2 | Stacking overlap in plan. | analysis | ≥ 100 mm² | 1 | |

### L1.2 The LCD is tilted 30 degrees and the front panel is a sloped flat face parallel to it

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The LCD plane is 30° from the table, facing up and toward the front. | inspection | angle between `VIEW_AXIS` and +Z = 30.0 ± 0.5; `VIEW_AXIS` Y component < 0; long axis (X_L) within 1.0° of case X | 3 | |
| L3.2.1.1 | Tilt angle of `VIEW_AXIS` from +Z. | inspection | 29.5 ≤ θ ≤ 30.5 | 3 | G2 |
| L3.2.1.2 | Facing direction and long-axis alignment. | inspection | `VIEW_AXIS`.y < 0; X_L within 1.0° of X | 3 | |
| L2.2.2 | The panel's outer face is flat, sloped, and parallel to the LCD. | inspection | outer-face normal within 1.0° of `VIEW_AXIS`; planarity ≤ 0.2 (window excluded) | 3 | |
| L3.2.2.1 | Outer-face normal vs `VIEW_AXIS`. | inspection | ≤ 1.0° | 3 | G2 |
| L3.2.2.2 | Outer-face planarity. | inspection | ≤ 0.2 | 2 | |
| L2.2.3 | The panel is a plate 2.0 to 4.0 thick that rests on the bezel face. | inspection | thickness along the normal 2.0 to 4.0; gap from `FACE_TOP` to the panel underside 0 to 0.3, no penetration (> 0.01 mm³) | 2 | |
| L3.2.3.1 | Panel thickness (ray cast along the normal, away from window and lip). | inspection | 2.0 ≤ t ≤ 4.0 | 2 | |
| L3.2.3.2 | Bezel-to-panel gap. | analysis | 0 ≤ g ≤ 0.3 (+ε); penetration ≤ 0.01 mm³ | 2 | |

### L1.3 The window shows the whole viewport and is not oversized (0.5 to 2.0 mm margin per side)

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The window is a through opening in the panel sized from the viewport (A4). | inspection | in the panel plane, window bounding box X in [65.5, 68.0], height in [15.0, 18.0]; centre within 0.5 of `VIEW_AXIS` | 2 | |
| L3.3.1.1 | Window size (panel-plane bounding box of V-AP-WIN). | inspection | as L2.3.1 | 2 | |
| L3.3.1.2 | Window centre vs `VIEW_AXIS`. | inspection | ≤ 0.5 | 2 | |
| L2.3.2 | No printed material inside the view zone. | analysis | clear_of(ALL, V-VIEW, 0.0) | 3 | |
| L3.3.2.1 | View-zone prism clear. | analysis | d ≥ 0.0, penetration ≤ 0.01 mm³ | 3 | G2 |
| L2.3.3 | Material around the window. | analysis | ligament from the window to the panel outer edge ≥ 1.5 and to the bezel outline (panel overlapping the bezel) ≥ 1.5 | 1 | |
| L3.3.3.1 | Window-to-edge ligament. | analysis | ≥ 1.5 | 1 | |
| L3.3.3.2 | Window inside the bezel outline. | analysis | each window edge ≥ 1.5 inside the 71.2 × 24.2 outline | 1 | |

### L1.4 The LCD is fixed on four standoffs at its holes, at least 0.5 mm clear of the walls

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Four standoffs, one under each LCD hole, axes along `VIEW_AXIS`. | inspection | count = 4; each axis within 0.25 of its `HOLE` axis at the PCB underside; axis direction within 1.0° of `VIEW_AXIS` | 3 | |
| L3.4.1.1 | LCD standoff count. | inspection | = 4 | 3 | G3 |
| L3.4.1.2 | Axis offset to the `HOLE` axes. | analysis | ≤ 0.25 each | 3 | G3 |
| L3.4.1.3 | Axis direction. | inspection | ≤ 1.0° | 2 | |
| L2.4.2 | Standoff tops are one plane and the PCB rests on them. | analysis | top-plane spread ≤ 0.10; `PCB_BOTTOM` within 0.10 of the tops | 3 | |
| L3.4.2.1 | Standoff top spread. | inspection | ≤ 0.10 | 2 | |
| L3.4.2.2 | PCB seating on the tops. | analysis | distance ≤ 0.10, penetration ≤ 0.01 mm³ | 3 | |
| L2.4.3 | Standoff geometry for an M2 self-tapping screw (A7). | inspection | OD 5.0 to 7.0; pilot Ø 1.6 to 1.8; pilot depth along the axis ≥ engagement + 0.5 and ≥ 5.0; at least 0.8 of material below the pilot tip; wall round the pilot ≥ 1.6 | 3 | |
| L3.4.3.1 | Standoff OD. | inspection | 5.0 ≤ OD ≤ 7.0 | 2 | |
| L3.4.3.2 | Pilot diameter. | inspection | 1.6 ≤ Ø ≤ 1.8 | 3 | G3 |
| L3.4.3.3 | Pilot depth, engagement (screw length − 1.6) and floor below the tip. | inspection | depth ≥ max(5.0, engagement + 0.5); tip material ≥ 0.8; engagement ≥ 5.0 | 2 | |
| L2.4.4 | The LCD edges and bezel are clear of the walls and the panel stays off the PCB. | analysis | clear_of(ALL, M-LCD, 0.5) with the standoff tops, screws and the bezel-to-panel contact excluded | 2 | |
| L3.4.4.1 | LCD-to-wall clearance. | analysis | d ≥ 0.50 | 2 | |

### L1.5 The Pico is mounted on four standoffs, inside, at least 1.0 mm clear of the back of the LCD

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Four vertical standoffs, one under each Pico hole; M2 geometry (A6, A7). | inspection | count = 4; axes within 0.25 of `PICO_HOLE`; axes within 1.0° of Z; OD 5.0 to 7.0; pilot Ø 1.6 to 1.8, depth ≥ max(5.0, engagement + 0.5), engagement = screw length − 1.0 ≥ 5.0; tips ≥ 0.8 above the underside; tops coplanar ≤ 0.10; `PCB_BOTTOM` within 0.10 of the tops | 3 | |
| L3.5.1.1 | Pico standoff count. | inspection | = 4 | 3 | G4 |
| L3.5.1.2 | Axis offset to `PICO_HOLE`. | analysis | ≤ 0.25 each | 3 | G4 |
| L3.5.1.3 | Pilot diameter, depth, engagement, standoff OD, tops. | inspection | as L2.5.1 | 2 | |
| L2.5.2 | Stacking: the Pico stays clear of the back of the LCD. | analysis | clear_of(V-PICO-TOP, V-LCD-BACK ∪ M-LCD PCB, 1.0) | 3 | |
| L3.5.2.1 | Pico top to the LCD back zone. | analysis | d ≥ 1.0 | 3 | G4 |
| L2.5.3 | The Pico is inside the case with room. | analysis | inside(V-PICO, V-CAVITY, 0.2); PCB edges (except the USB end) ≥ 0.5 from every wall | 3 | |
| L3.5.3.1 | V-PICO in the cavity. | analysis | d ≥ 0.20 | 3 | |
| L3.5.3.2 | Pico PCB edge to the walls (not the USB end). | analysis | ≥ 0.50 | 2 | |
| L2.5.4 | Solder side clearance. | inspection | PCB underside to the floor top 3.0 to 8.0 | 2 | |
| L3.5.4.1 | Standoff height. | inspection | 3.0 ≤ h ≤ 8.0 | 2 | |

### L1.6 A micro-USB cable plugs into the Pico through the back wall with the case closed

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Closed: the plug pushes to full mate and pulls out without touching the case. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 | |
| L3.6.1.1 | USB plug envelope clear. | test | d ≥ 0.30 | 3 | G5 |
| L3.6.1.2 | Physical: print, close, plug in the cable. | test | clicks in fully, 3 of 3 tries | 2 | physical, optional |
| L2.6.2 | The opening is not oversized. | analysis | inside(V-AP-USB, V-USB-PLUG offset by 1.5, 0.0) | 2 | |
| L3.6.2.1 | Opening within the grown envelope. | analysis | d ≥ 0.0 (opening ≤ 13.0 × 10.0 with the catalogue plug) | 2 | |
| L2.6.3 | Exactly one USB opening, in the back wall, with material round it. | inspection | V-AP-USB has 1 connected region; ligament to the floor line, panel seam and wall edges ≥ 1.5 | 2 | |
| L3.6.3.1 | Opening count in the back wall. | inspection | = 1 | 2 | |
| L3.6.3.2 | Ligament round the opening. | analysis | ≥ 1.5 | 1 | |

### L1.7 Base and removable sloped panel, located and held by two M2 screws at the rear corners

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Two separate bodies, each one connected shell, not fused, not interpenetrating. | analysis | BASE 1 shell; PANEL 1 shell; BASE ∩ PANEL ≤ 1.0 mm³ | 3 | |
| L3.7.1.1 | Shells per body. | analysis | = 1 each | 3 | G1 |
| L3.7.1.2 | Base and panel do not interpenetrate when closed. | analysis | ≤ 1.0 mm³ | 3 | G1 |
| L2.7.2 | A lip on the panel underside locates it on the base with a sliding fit. | inspection | lip engagement (vertical) 2.0 to 3.0; clearance 0.15 to 0.35 per side on every locating face | 2 | |
| L3.7.2.1 | Lip-to-wall gap. | inspection | 0.15 ≤ gap ≤ 0.35 | 2 | |
| L3.7.2.2 | Lip engagement. | inspection | 2.0 ≤ e ≤ 3.0 | 1 | |
| L2.7.3 | The panel's plan outline matches the base's outer outline. | inspection | outline equal ± 0.5 on all four sides; seam gap ≤ 0.5 | 1 | |
| L3.7.3.1 | Outline match and seam. | inspection | as L2.7.3 | 1 | |
| L2.7.4 | Closure: 2 bosses at the rear corners, axes along the panel normal; panel holes coaxial; driver access. | inspection | boss count = 2; OD ≥ 6.0; pilot Ø 1.6 to 1.8; depth ≥ max(5.0, engagement + 0.5), engagement = screw length − panel thickness ≥ 5.0; panel holes Ø 2.4 ± 0.1, coaxial ≤ 0.3; axis within 1.0° of the panel normal; clear_of(ALL, V-DRIVER-PANEL-k, 0.0) | 2 | |
| L3.7.4.1 | Closure boss count and OD. | inspection | = 2; OD ≥ 6.0 | 2 | |
| L3.7.4.2 | Boss pilot Ø, depth, engagement. | inspection | as L2.7.4 | 2 | |
| L3.7.4.3 | Panel holes Ø and coaxiality with the boss pilots. | inspection | Ø 2.3 to 2.5; offset ≤ 0.3 | 2 | |
| L3.7.4.4 | Panel-screw driver columns. | analysis | d ≥ 0.0 | 1 | |
| L3.7.4.5 | Physical: hold upside down, open and close 10 times. | test | panel stays on; nothing strips | 1 | physical, optional |

### L1.8 Protection: only the window, the USB opening and screw holes; 2 to 4 mm walls

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | No unlisted openings. | analysis | no region admits a Ø2.0 sphere from outside into V-CAVITY other than the window, the USB opening and the screw holes | 2 | |
| L3.8.1.1 | Probe for unlisted openings (ray grid 1 mm over the hull faces). | analysis | 0 unlisted paths | 2 | |
| L2.8.2 | Wall, floor and panel thicknesses. | inspection | each in [2.0, 4.0] (panel measured along its normal) | 2 | |
| L3.8.2.1 | Wall thickness (median, away from features). | inspection | 2.0 ≤ t ≤ 4.0, all four walls | 2 | |
| L3.8.2.2 | Floor thickness. | inspection | 2.0 ≤ t ≤ 4.0 | 2 | |
| L2.8.3 | Walls join the floor. | analysis | contact ≥ 90 percent of wall length × thickness | 2 | |
| L3.8.3.1 | Wall-to-floor contact. | analysis | ≥ 90 percent | 2 | |

### L1.9 Both parts print without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | In the declared print pose (FD6) no part has an unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12.0 and bridges ≤ 15.0. | analysis | 0 offending faces (area > 1 mm²) per body | 2 | |
| L3.9.1.1 | Overhang and bridge scan per body, in its pose. | analysis | 0 patches | 2 | |
| L2.9.2 | Each mesh is manifold and a single shell. | analysis | 1 shell; manifold3d accepts it | 3 | |
| L3.9.2.1 | Shell and manifold status per body. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.9.3 | Each part rests on a flat face in its pose. | analysis | bed contact ≥ 50 percent of the plan bounding box | 1 | |
| L3.9.3.1 | Bed-contact area per body. | analysis | ≥ 50 percent | 1 | |
| L2.9.4 | No thin features; mating gaps ≥ 0.15. | analysis | min local thickness ≥ 0.8; min mating gap ≥ 0.15 | 1 | |
| L3.9.4.1 | Thin-feature scan. | analysis | as L2.9.4 | 1 | |
| L2.9.5 | Each part fits the bed. | inspection | bounding box in its pose ≤ 200 per axis | 1 | |
| L3.9.5.1 | Bounding box per body in its pose. | inspection | ≤ 200 | 1 | |

### L1.10 Size and stability

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Closed outside size. | inspection | X ≤ 100.0, Y ≤ 80.0, Z ≤ 70.0 | 1 | |
| L3.10.1.1 | Assembly bounding box. | inspection | as L2.10.1 | 1 | |
| L2.10.2 | It stands without tipping, on a flat underside. | analysis | stable at 5° table tilt in every direction; underside flatness ≤ 0.2 | 1 | |
| L3.10.2.1 | Support-polygon test with the closed assembly, the LCD and the Pico (mass 60 g, centre of mass at their centroids). | analysis | passes | 1 | |
| L3.10.2.2 | Underside flatness. | inspection | ≤ 0.2 | 1 | |

### L1.11 Service: the LCD and the Pico lift out, every board screw is reachable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Panel off: the LCD lifts out along +`VIEW_AXIS` without touching the base. | test | clear_of(BASE, V-EXTRACT-LCD, 0.2) (standoff-top contact excluded) | 2 | |
| L3.11.1.1 | LCD extraction path. | test | d ≥ 0.20 | 2 | |
| L2.11.2 | Panel off: the Pico lifts out along +Z. | test | clear_of(BASE, V-EXTRACT-PICO, 0.2) | 2 | |
| L3.11.2.1 | Pico extraction path. | test | d ≥ 0.20 | 2 | |
| L2.11.3 | A screwdriver reaches every LCD and Pico screw with the panel off. | analysis | clear_of(BASE, V-DRIVER-LCD-k ∪ V-DRIVER-PICO-k, 0.0) | 1 | |
| L3.11.3.1 | Driver columns clear. | analysis | d ≥ 0.0 for all eight | 1 | |
| L2.11.4 | Panel screws are separate from board screws. | inspection | no shared fastener | 1 | |
| L3.11.4.1 | Judge confirms no fastener is shared. | inspection | true | 1 | human |

### L1.12 The package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | Package: `base.stl`, `panel.stl` (closed pose, case frame, mm), the `.scad`, `layout.json` (L2.1.1 plus print poses), the agent's own report. | inspection | all present and readable | 3 | |
| L3.12.1.1 | Files parse; STLs in mm (largest bounding-box axis of each body 20 to 200). | inspection | true | 3 | G0 |
| L3.12.1.2 | Declared layout verifies under the seating rule (2.3). | analysis | LCD and Pico PCB distance to standoff tops ≤ 0.10; hole-axis residual ≤ 0.25 | 3 | |
| L2.12.2 | Self-report agrees with the judge. | analysis | every `clear_of` and `inside` d within 0.10, same pass/fail | 1 | |
| L3.12.2.1 | Self-report vs judge. | analysis | 100 percent agreement within 0.10 | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 40 |
| L3 | 65 (3 physical or human, the rest measured by Python on the STLs) |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.1.1.1, L3.12.1.1); **G1** manifold and two
bodies (L3.9.2.1, L3.7.1.1, L3.7.1.2); **G2** tilt and window (L3.2.1.1, L3.2.2.1, L3.3.2.1); **G3** the LCD is fixed
(L3.4.1.1, L3.4.1.2, L3.4.3.2); **G4** the Pico is fixed and clear of the LCD (L3.5.1.1, L3.5.1.2, L3.5.2.1);
**G5** the USB plug seats (L3.6.1.1).

---

## 6. Design-specific rubric (the generic rubric was absent when this was written)

### 6.1 Procedure

1. G0: check the files in L2.12.1 exist and load; if the STLs are missing or unreadable stop (DOES NOT MEET, one defect on L3.12.1.1).
2. Units: each body's largest bounding-box axis within 20 to 200; if inches or metres, record a defect, do not rescale.
3. Normalise the frame (1.1) with rotations by multiples of 90° and X mirroring only; record the transform.
4. Build M-LCD, M-PICO2 and every V- envelope independently from `parts/*/part.json` and the declared layout; run R1 to R4 and verify the seating rule (2.3).
5. Run every applicable L3 with Python, in order. Record value, limit, signed margin (negative = fail), PASS / FAIL /
   UNVERIFIED (counts as FAIL). N/A only for the physical tests with no print.
6. Look at renders afterwards; render-only findings are observations and do not change the verdict.
7. Decide (6.3) and report (6.4).

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

- **Tilted poses:** build the LCD by transforming the catalogue solids with a 4 × 4 matrix (rotation about X by θ, then
  translation to the declared origin); `Manifold.transform`. Angles between axes by `arccos` of the dot product.
- **Standoff and boss axes:** slice by a plane normal to the claimed axis at mid-height; smallest enclosing circle centre =
  axis point, two slices give the direction; pilot: largest inscribed circle of the hole polygon in the same slice; depth by
  ray cast along the axis from the top plane.
- **Panel plane and thickness:** fit a plane to the outer-face vertices (largest facets); thickness by ray cast along the
  normal on a 2 mm grid, away from the window, the lip and edges (median).
- **Window:** slice the panel at mid-thickness along the normal; the through-hole polygon bounding box in the panel plane
  and its centre; ligament = distance from the polygon to the panel outline.
- **Apertures and probe:** as in the enclosure rubric (end-wall slab minus bodies, `decompose()`, ignore regions under
  1 mm³; ray grid of 1 mm over the hull faces for unlisted openings, then a Ø2.0 sweep to confirm).
- **Thickness, gap and ligament:** ray casting on a 2 mm grid at least 3 mm from edges, openings and bosses; median is the
  value, a range wider than 0.5 is noted.
- **Printability:** transform each body into its declared print pose; a face with normal n overhangs if n_z < −cos 45° and
  z > 0.05, minus round holes Ø ≤ 12 in vertical walls and bridges ≤ 15 between supports. Bed contact: area of faces with
  n_z < −0.999 at z < 0.05 divided by the plan bounding-box area. Thin features: inward ray cast.
- **Stability:** centre of mass of the closed assembly plus 60 g at the model centroids, projected on the table at 5° tilt in
  every direction, must stay inside the support polygon of the underside.

### 6.3 Classes

| Class | Rule |
|---|---|
| **WRONG** | any gate G0..G5 fails |
| **MINOR** | no gate fails but a weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |
| **MEETS requirements** | CORRECT and every applicable non-physical weight-1 and weight-2 L3 passes |

Also report the weighted score Σ(weight × pass)/Σ(weight) over applicable L3s and the worst normalised margin among
weight-3 L3s. Precedence: the plug-seating check outranks opening size; numbers in this file beat `part.json` (a
disagreement is a defect on the L3 it breaks, with where = the part.json field); designed contact (1.3) is never
interference; never relax a criterion; never infer a pass from a render.

### 6.4 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first (gates, then weight 3, 2, 1). Fields: `req` (L3, L2,
L1), `status`, `body` (base, panel, both, layout), `feature` (by function and SCAD name), `face` (surface and outward
normal), `location` (case-frame coordinates, a point or a box; also LCD frame where clearer), `measured / limit / margin`,
`reference` (the model or envelope and its datum), `render`, `evidence` (saved files), `needed` (a numeric target, never a
design instruction). Group L3s with one geometric cause under the first and list the others in `also_fails`; separate
observations from defects.

---

## 7. Feasibility (a concrete design that meets every L3)

Case frame, mm. Wall, floor and panel 2.4. θ = 30°, tan θ = 0.5774.

| Feature | Value |
|---|---|
| Base outer | X ±42.9 (85.8 wide), Y 0 to 71.2, floor Z 0 to 2.4; inner X ±40.5, inner Y 2.4 to 68.8 |
| Panel plane | outer face z = 21.51 + 0.5774·y (front 21.5, back 62.6); underside z = 18.74 + 0.5774·y; panel normal = `VIEW_AXIS` |
| Walls | tops follow the underside plane (front wall 18.7 to 20.1 high, back wall about 59.8) |
| M-LCD pose | PCB min corner at X −40.0, y 10.0, z 9.5, rotated 30° about X (`VIEW_AXIS` = (0, −0.5, 0.866)); PCB X ±40, y 10.0 to 41.2 |
| LCD standoffs | 4, OD 5.0, axes along `VIEW_AXIS`, tops at the hole axes: front (X ±37.5, y 12.17, z 10.75), rear (X ±37.5, y 39.01, z 26.25); lengths along the axis to the floor top 9.6 and 27.5; pilot Ø1.7, depth 7.0; screws M2 × 8 (engagement 6.4); tip height of the front pilot 4.69 |
| M-PICO2 pose | PCB X ±10.5, y 16.0 to 67.0, z 6.9 to 7.9; `USB_MOUTH` (0, 68.3, 9.3); `USB_AXIS` +Y |
| Pico standoffs | 4 vertical, height 4.5 (floor top to 6.9), OD 6.0, at X ±5.7, y 18.0 and 65.0; pilot Ø1.7 depth 5.8 (tip 1.1 above the underside); screws M2 × 6 (engagement 5.0) |
| USB opening | back wall, X ±5.3 (10.6), z 5.5 to 13.1 (7.6): plug 10.0 × 7.0 at z 5.8 to 12.8, so d = 0.3, oversize 0.3 ≤ 1.5; ligament to the floor top 3.1 |
| Window | 66.5 × 16.0 in the panel plane, centred on `VIEW_AXIS` through the bezel centre |
| Panel | plan 85.8 × 71.2; lip wall 1.2, vertical, engagement 2.5, 0.25 off the inner wall faces; 2 holes Ø2.4 along the normal at X ±35.0, panel-plane y 44 |
| Closure bosses | 2 at X ±35.0 (the OD 6.0 boss then spans X 32 to 38, 1.05 clear of the side lip's inner face at 39.05), axis along `VIEW_AXIS`, top on the panel underside at y 44 (z 44.1), OD 6.0, length 48.2, foot fused into the back wall and floor; pilot Ø1.7 depth 6.2; screws M2 × 8 (engagement 5.6) |
| Print poses | BASE floor down; PANEL outer face down (rotated 30°), lip up |

Checks by hand:
- Tilt 30.0°; panel normal = `VIEW_AXIS`; thickness 2.4 along the normal. Bezel face is at 13.0 above the PCB underside and the
  panel underside is 13.0 above it: gap 0 (contact). Bezel top front edge at y 8.61, z 23.7 lies in the underside plane and
  is 6.2 from the front wall inner face (≥ 0.5) and 4.8 from the front lip's inner face.
- View zone: window 66.5 × 16.0 contains the 64.5 × 14.0 prism with margin 1.0 per side (band 0.5 to 2.0 each side); bezel
  overlap 2.35 (X) and 4.1 (Y) per side (≥ 1.5).
- Stacking: the LCD back zone bottom at the Pico's front edge (y 16.0): z = 9.5 + 6.0 × 0.5774 − 2.0 / cos 30° = 10.65
  (the PCB underside is 12.96); the highest Pico top part there is z = 6.9 + 1.0 + 1.5 = 9.4: vertical gap 1.25, perpendicular
  distance 1.08 ≥ 1.0. The Pico is under the LCD for y 16.0 to 41.2 (plan overlap 21 × 25.2 = 529 mm²).
- Pico in the cavity: mouth at y 68.3, back wall inner face y 68.8, so d = 0.5 ≥ 0.2; side clearance 40.5 − 10.5 = 30.
- Closure bosses: foot y = 44 + 48.2 × 0.5 = 68.1 (the foot disc reaches y 70.7, 0.5 inside the outer face); the Pico and the LCD standoffs are at other X or
  other y (the boss axis is 13.3 beyond the rear LCD screw axis measured in the LCD plane; parallel columns do not meet);
  the OD 6.0 boss spans X 32 to 38, clear of the side lip (inner face X 39.05).
- Service: the front LCD screw's Ø6 driver column along `VIEW_AXIS` leaves the case over the front wall (it crosses the wall's
  inner plane y 2.4 at z 21.7, above the wall top 20.1); the LCD lifts out along `VIEW_AXIS` and the Pico along +Z with no contact
  (checked by sweeping the reference solids, minimum gap above 0.2).
- Size 85.8 × 71.2 × 62.6 (limits 100, 80, 70). Stability: centre of mass about (0, 34, 22) lies far inside the 85.8 × 71.2
  support polygon; a 5° tilt moves it 2 mm.
- Printing: base walls vertical; tilted standoffs and bosses lean 30° from vertical (≤ 45°); the wall tops follow the sloped
  plane (top faces, no overhang); the USB opening is a 10.6 × 7.6 rectangle in a vertical wall (bridge 10.6 ≤ 15). Panel face
  down: window edges normal to the bed, the vertical-faced lip leans 30° from vertical (≤ 45°), bed contact about 95 percent.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 | Method | Words in the request |
|---|---|---|---|---|---|---|
| L1.1 | layout of LCD and Pico | L2.1.1-3 | L3.1.1.1, L3.1.2.1, L3.1.3.1-2 | L1.1 | inspection | "1602 LCD module", "Raspberry Pi Pico 2", "behind and below" |
| L1.2 | 30° tilt, sloped front | L2.2.1-3 | L3.2.1.1-2, L3.2.2.1-2, L3.2.3.1-2 | L1.2 | inspection | "tilted 30 degrees from the table", "front face ... sloped" |
| L1.3 | window | L2.3.1-3 | L3.3.1.1-2, L3.3.2.1, L3.3.3.1-2 | L1.3 | analysis | "viewport 64.5 x 14 mm", "window for the LCD" |
| L1.4 | LCD fixed | L2.4.1-4 | L3.4.1.1-3, L3.4.2.1-2, L3.4.3.1-3, L3.4.4.1 | L1.4 | inspection | "fixed on its four mounting holes" |
| L1.5 | Pico mounted and clear | L2.5.1-4 | L3.5.1.1-3, L3.5.2.1, L3.5.3.1-2, L3.5.4.1 | L1.5 | analysis | "Pico 2 is mounted behind and below the LCD" |
| L1.6 | USB through the back | L2.6.1-3 | L3.6.1.1-2, L3.6.2.1, L3.6.3.1-2 | L1.6 | test | "micro-USB port must open through the back wall" |
| L1.7 | base and panel | L2.7.1-4 | L3.7.1.1-2, L3.7.2.1-2, L3.7.3.1, L3.7.4.1-5 | L1.7 | inspection | "a base and a removable sloped front panel" |
| L1.8 | protection | L2.8.1-3 | L3.8.1.1, L3.8.2.1-2, L3.8.3.1 | L1.8 | analysis | "case" (implied) |
| L1.9 | printable | L2.9.1-5 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1, L3.9.5.1 | L1.9 | analysis | "printed on an FDM printer without supports" |
| L1.10 | desk use | L2.10.1-2 | L3.10.1.1, L3.10.2.1-2 | L1.10 | analysis | "desk clock", "stands on a desk" |
| L1.11 | service | L2.11.1-4 | L3.11.1.1, L3.11.2.1, L3.11.3.1, L3.11.4.1 | L1.11 | test | implied (removable panel) |
| L1.12 | evidence | L2.12.1-2 | L3.12.1.1-2, L3.12.2.1 | L1.12 | inspection | needed by the judge (not the owner's words) |

---

## Audit

Adversarial audit (second agent). Method: all five catalogue parts load and pass `parts.validate`/`parts.gate`; the
derived numbers were recomputed by hand and the Feasibility design was then built as solids (manifold3d) and run
against the gates, which found real contradictions. `claude-context` was unavailable (server failed to connect), so
targeted grep was used. The generic `benchmarks/generalize/rubric.md` still does not exist; section 6 of this file is the
rubric for this entry (it follows `benchmarks/enclosure/rubric.md`).

Fixes made (all in place):
1. **Feasibility, front lip hit the LCD, and the LCD driver columns hit the front wall.** With the LCD at y 5.0 the front
   screws' 50 mm driver columns along `VIEW_AXIS` crossed the front wall at z 10.5 (wall top 20.5) and the LCD could not lift
   out along `VIEW_AXIS` (1197 mm³ of sweep inside the front wall), so L3.11.1.1 and L3.11.3.1 failed; the front lip (inner face
   y 3.85) also cut into the bezel's front edge (4.8 mm³), failing L2.4.4 and G1. Fix: LCD origin moved to y 10.0, z 9.5
   (z raised so that the stacking gap to the Pico still holds, perpendicular 1.08 mm). Recomputed: panel plane, wall heights,
   standoff lengths (front 9.6, rear 27.5; the old "4.4" was wrong), front pilot tip (4.69), stacking (1.08), plan overlap
   (529 mm²), bezel-to-wall distances, size 85.8 × 71.2 × 62.6. Rebuilt and measured: base and panel 1 shell each, interference
   0, view zone clear, LCD and Pico extraction clear, all eight driver columns clear, plug gap 0.30, LCD to wall 0.50.
2. **Feasibility, closure bosses at X ±38 collided with the side lip** (25 mm³ of BASE ∩ PANEL, a G1 failure). Bosses and
   panel holes moved to X ±35.0 (boss spans X 32 to 38, lip inner face at 39.05); the rebuilt solids have 0 interference.
3. **Hidden numbers moved into the L1 text the agent receives:** window margin 0.5 to 2.0 (L1.3), LCD to wall 0.5 (L1.4),
   Pico to LCD back 1.0 with a 2.0 mm back-side component zone (L1.5), plan overlap at least 100 mm² (L1.1), two M2
   screws at the rear corners along the panel normal (L1.7). The matching L1 headings in this file were updated.
4. Corrected the USB opening ligament line (3.1 mm to the floor top, was written as the height 5.5).

Checked and left unchanged: counts (12 / 40 / 65, matches the tree), L1 count 12, no duplicate ids, no contradiction
between thickness 2 to 4, size 100 × 80 × 70 and the design, USB opening 10.6 × 7.6 within the 13 × 10 cap, overhang
poses (panel printed face down: lip faces at n_z of −0.5), parts references. Residual uncertainty: LCD side clearance is
exactly 0.50 (the limit) in the feasibility design, bezel and viewport offsets are assumed (part.json notes).
