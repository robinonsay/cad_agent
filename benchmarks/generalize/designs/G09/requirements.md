# G09 9V battery box with hinged lid and toggle: requirements (L1 / L2 / L3)

Generalisation design G09 (train split). It is the error signal for the control loop on a different
product family from the Pico enclosure (E1-01): a hinged two-body box with a retained battery, a
panel toggle switch, a panel DC jack, a hinge pin and a snap latch. The machine-readable request
(L1 only, `dev.json` format) is `design.json` next to this file. It is graded the way
`benchmarks/enclosure/requirements.md` grades E1-01: Python measures the delivered STLs against
reference models built from the catalogue (`benchmarks/generalize/parts/*/part.json`, plus
`benchmarks/enclosure/parts/generic_cylinder` where named).

**Request (owner's words):** "A pocket box for a 9V PP3 battery (26.5 x 17.5 x 48.5 mm) with a
toggle switch on top and a panel DC jack on one end. The lid is hinged with a 3 mm steel pin and
closes with a snap latch. The battery must be retained, and the DC plug body has to fit when the
jack is used." The expanded request in `design.json` adds only what section 3 derives.

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check on the geometry. Every row has a verification
method (`dev.json` definitions), a pass/fail criterion with a number and tolerance, a weight
(3 = critical, 2 = major, 1 = minor) and a gate mark (G0 to G5) where failing it makes the design
WRONG. Do not relax a criterion because the agent fails it; change a number only when the owner
corrects an assumption (section 3).

**Grading procedure.** `benchmarks/generalize/rubric.md` holds the generic judge procedure
(units, frames, measuring recipes, MEETS / CORRECT / MINOR / WRONG, how to report WHERE a defect is,
precedence). If that file is missing, use section 9 of this document, which is self-sufficient.

---

## 1. Frames, tolerances and the checks

### 1.1 Frames

- **Box frame:** X along the battery's 48.5 mm axis, Y across the box, Z up. The jack's end wall is
  **-X**; the hinge is on the **-Y** long side; the lid is on top (**+Z**). The floor's underside is
  Z = 0 in the closed pose. A design delivered mirrored or rotated by multiples of 90 degrees is
  normalised into this frame before grading; that is never penalised (FD1).
- **Part frames:** each catalogue part keeps its own frame (`part.json` `frame`) and is placed by
  the pose in `layout.json`: the battery's long axis (its +Z) lies along X; the toggle's +Z is
  box +Z; the jack's `AXIS` points out of the box, along -X; the pin axis is along X.
- **Hinge frame:** origin on the pin axis. The lid's closed pose is angle 0; opening rotates the lid
  about that axis so that its +Y edge rises (the angle is positive when the lid is open).

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, distance, clearance, travel | 0.02 mm | a value passes if it meets the limit to within e |
| angle | 0.5 deg | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole diameter | largest inscribed circle of the hole's section | what a pin or bushing sees |
| boss / knuckle OD | smallest enclosing circle of the section | |

### 1.3 The checks

- **`clear_of(bodies, volume, clearance)`**: minimum distance between the printed bodies and
  `volume` is >= `clearance` (negative = penetration; volume reported). Pass: d >= clearance - e.
- **`inside(volume, cavity, clearance)`**: `volume` lies inside `cavity`, every point >= `clearance`
  from its boundary.
- **`travel(part, axis)`**: free rigid travel. Slide the reference part (rigid translation, no
  rotation) along `axis` in both directions from its declared pose until the first printed contact
  (a penetration above 0.01 mm3); the reported value is the total range, from contact to contact. A
  part with no contact within 100 mm has travel "unbounded" (fails any limit).
- **`swing(theta_max, step)`**: rotate the lid, with everything fixed to it, about the hinge axis from 0 to
  `theta_max` in `step` increments; at every angle after 0, intersect the moving set with the fixed
  set. Reported: the largest intersection volume and its angle.

**Designed contact is not interference (owner rule, 2026-10-24).** For G09 the designed contacts are:
- the battery's underside resting on the floor top or on support pads;
- the toggle's shoulder seated against the lid plate's underside, and its bushing in the panel hole
  (the bushing may touch the hole wall at the fit's lower bound);
- the jack's body resting on its platform and against its pocket faces and the end wall's inner face;
- the hinge pin in its bores, a knuckle against the neighbouring knuckle face at the axial gap, the
  closed lid's plate on the base rim and its lip or skirt on the locating faces (fit 0.15 to 0.35);
- the latch hook on its catch in the closed pose.

For these pairs only penetration counts (intersection above 0.01 mm3); a distance of zero is a pass.
The swing test starts at angle 0 with the closed-pose contacts allowed, and excludes the pin and
the hinge knuckle faces (a knuckle turning on the pin is designed contact); every other contact at
an angle above 0 counts. It also excludes the latch pair: a snap latch opens by flexing its cantilever
(up to the hook overlap e, A11), so a rigid swing must interfere there. The excluded lid volume is the
lid material that intersects the base in the rigid 3-degree rotation of L3.7.3.1 (the hook), the excluded
base volume is the base material it meets (the catch), each grown by 0.5; the hook and catch may touch
each other at any angle, nothing else of them may touch anything.

`ALL` is base and lid together, closed. The grader builds every reference model and envelope
independently from the catalogue and the declared layout; the agent's copies are not trusted.

---

## 2. Reference models, envelopes and datums

### 2.1 Reference models (M-)

All poses come from `layout.json`. Default numbers are catalogue values.

| Name | What | Source | Size / datums used (box frame, mm) |
|---|---|---|---|
| **M-BATT** | 9 V PP3 battery | `battery_9v_pp3` | 26.5 x 17.5 x 48.5 body; `TERMINALS` on the end face; `BOTTOM` plane; keep-out `clip_zone` 26.5 x 17.5 x 10.0 on the terminal end face |
| **M-TOG** | MTS-102 toggle switch | `toggle_mts102` | body 13 x 8 x 10; bushing Ø6.0 x 8.0 above the body; lever Ø3.0, 12.0 above the bushing top; datums `SHOULDER` (z 10), `BUSHING_TOP` (z 18), `AXIS`, `LEVER_TIP`, `PINS` (3 lugs, 4.7 pitch, 4.0 long below the body) |
| **M-JACK** | PJ-002A DC jack | `dc_jack_pj002a` | body 14 x 9 x 11; `AXIS` height 5.5 above the body bottom; `MOUTH` on the +X face of the part frame (faces -X here); plug bore 5.5 |
| **M-PLUG-DC** | 5.5 x 2.1 DC barrel plug | `plug_dc_barrel_5p5` | barrel Ø5.5 x 14.0; overmold Ø11.0 x 16.0; stop gap at full mate 1.0; `PLUG_TIP`, `PLUG_AXIS`, `OVERMOLD_FACE` |
| **M-PIN** | 3 mm steel dowel pin | `dowel_pin_generic` | Ø3.0, length 24.0 (request); press-fit hole Ø3.0, clearance hole Ø3.2, minimum engagement 4.5 |

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-CLIP** | snap-clip zone | M-BATT's `clip_zone`: 26.5 x 17.5 x 10.0 box on the terminal end face |
| **V-LEVER** | lever swing | M-TOG's `lever_swing`: cylinder Ø8.0 (twice the 4.0 swing radius), 12.0 tall, starting at `BUSHING_TOP`, on `AXIS` |
| **V-NUT** | nut zone | cylinder Ø9.0 on `AXIS`, from the lid plate's outer face at the hole (measured, L3.4.1.2; the plate face itself is designed contact) up to `BUSHING_TOP`; it is at least 4.0 tall because the plate is at most 4.0 thick (the nut and its thread room; `part.json` `nut_zone` is its top 3.0) |
| **V-LUGS** | solder-lug room | box 13.0 x 8.0 footprint of the toggle body, 4.0 tall, directly under the body |
| **V-PLUG-DC** | plug at full mate plus path | M-PLUG-DC placed with its barrel in the jack bore, overmold face 1.0 outside `MOUTH`; overmold swept 40.0 outward (past any wall) along the jack's outward axis; barrel Ø5.5 from the overmold face to 13.0 inside `MOUTH` |
| **V-BATT-INSTALL** | install / removal path | (M-BATT union V-CLIP) swept straight +Z from its seated pose to 60 above the base rim |
| **V-CAVITY** | closed internal void | convex hull of ALL minus ALL, connected component containing M-BATT's centroid |
| **V-AP-JACK** | opening(s) in the -X end wall | the end wall's slab (between its inner and outer faces, full Y and Z extent) minus ALL; sliced at 0.2 steps across the wall |
| **V-AP-OTHER** | every other through-path | as E1-01: rays from outside to V-CAVITY on a 1 mm grid, minus the listed openings |
| **V-SWING(theta)** | lid and parts rotated | (LID union M-TOG) rotated about the hinge axis by theta, theta = 5, 10, ... 100 degrees |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Check | Pass |
|---|---|---|
| R1 | units: bounding boxes in mm | M-BATT 26.5 x 17.5 x 48.5 +-0.3; M-JACK 14 x 9 x 11 +-0.4; M-TOG body 13 x 8 x 10 +-0.2 |
| R2 | M-TOG: bushing Ø and lever above bushing | 6.0 +-0.05; 12.0 +-0.05 |
| R3 | M-PLUG-DC: barrel Ø, overmold Ø, total | 5.5 +-0.1; 11.0 +-0.3; 30.0 +-0.3 |
| R4 | M-PIN length and Ø | 24.0 +-0.05; 3.0 +-0.05 |
| R5 | reference parts do not collide with each other | intersection <= 0.01 mm3 |
| R6 | every V- envelope's datums equal the model datums it came from | <= 0.01 |

**Seating rule.** The grader places the reference parts at the pose in `layout.json`. It then
verifies the declaration: M-BATT's `BOTTOM` plane lies on the floor top or its pads (distance
<= 0.10); M-TOG's `AXIS` is coaxial with the lid hole (residual <= 0.25); M-JACK's `MOUTH` lies on
the end-wall opening's axis (residual <= 0.25); M-PIN's axis is coaxial with the hinge bores
(residual <= 0.20). If a declaration is missing or fails, the part is seated by that fit instead.
If there is no floor under the battery, it is placed with its underside 2.0 above the lowest
internal face, and L3.2.1.3 fails.

---

## 3. Assumptions, uncertainty and fixed decisions

Each line gives the value chosen and why; uncertainty is the range within which the real part or
convention may differ. A values are provisional until the owner confirms them.

| # | Question | Value chosen | Uncertainty and why |
|---|---|---|---|
| A1 | Battery size | 26.5 x 17.5 x 48.5 maximum (IEC 6LR61); real cells are 0.3 to 0.5 smaller | +-0 (maximum used, so the pocket never binds) |
| A2 | Terminal stud and spacing | spacing 12.7, stud 1.5 | +-0.5; not graded directly: the clip zone covers them |
| A3 | Snap-clip zone | 10.0 high over the full end face (catalogue `clip_zone`) | +-2.0 mm in height; real clips vary. The height only sets the X-travel band (L3.3.1.2) |
| A4 | Toggle switch | MTS-102 class: body 13 x 8 x 10, bushing Ø6.0 x 8.0, panel up to 4.0, nut 9.0 across corners x 3.0, lever 12.0 above the bushing top, swing Ø8.0 (+-20 deg), 3 lugs at 4.7 pitch, 4.0 long | bushing length +-1.0; nut +-0.5; swing radius +-1.0; lug length and pitch assumed. Measure the owner's switch |
| A5 | DC jack and plug | PJ-002A class body 14 x 9 x 11, axis 5.5 up; plug barrel Ø5.5 x 14 long, overmold Ø11 x 16 | axis height +-0.5; overmold Ø +3 / -1 (adapters vary 9 to 14); tag positions not graded. The plug opening comes from the plug envelope, not the 6.3 jack shell |
| A6 | Pin length | 24.0 mm, 3.0 mm ISO 2338 h8 | the owner gave only Ø3; 24 is chosen so the hinge (about 25 mm along the long wall) can use it. Stock lengths 6 to 30 are all valid; the pin length must come from the request text (it is 24) |
| A7 | Hinge geometry | pin axis parallel to X on the -Y side; knuckle OD >= 6.4 (largest bore 3.2 + 2 x 1.6 wall); press fit Ø3.0 in one body, clearance Ø3.2 in the other; axial gap between neighbouring knuckles 0.3 to 0.8 | FDM convention (`dowel_pin_generic`); +-0.05 on holes |
| A8 | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed; base open side up, lid outer face down; sliding fit 0.15 to 0.35 per side | common printers; round holes up to Ø12 and bridges up to 15 print without support |
| A9 | Wall band | walls, floor and lid plate 2.0 to 4.0 | the toggle panel is at most 4.0 thick (datasheet) and 5 perimeters is stiff; the band is the same as E1-01 |
| A10 | Size limit | closed box (printed bodies only; pin ends and switch lever excluded) <= 90 x 45 x 30 | about 80 x 42 x 24 is the tight design (section 6); the limit stops oversized boxes |
| A11 | Snap latch | PLA / PETG allowable strain 0.02 (2 %), cantilever hook, hook overlap 0.4 to 1.2 | +-0.005 on strain. A tab on the lid's +Y edge hooking a ledge on the base is typical. Strain e = 1.5 t d / L^2 (t thickness, d deflection = overlap, L length) |
| A12 | Battery retention | "retained" means rigid free travel when the lid is closed: <= 1.0 across width and thickness, <= clip zone + 1.5 along the length | a battery that can move 1.0 mm does not rattle audibly; the X band accounts for the clip. Not a force test |
| A13 | Wiring and removal | wires between jack, switch and clip are not modelled; the battery is removed by lifting (pull-tab or finger path is a design choice, not graded) | the catalogue notes list it as design choice; no number to grade |
| A14 | Open angle | 100 degrees from closed, lid and switch swinging as one rigid set | 90 is vertical; 10 degrees more keeps the lid from falling shut; +-10 |
| A15 | Switch mounting direction | mounted from below, nut on the outside of the lid plate; the shoulder seats on the plate's underside | the datasheet panel range (up to 4.0) and the nut zone above the plate require it |
| A16 | Stability | the stability test tilts the closed box 5 degrees about each floor edge with the battery in place (60 g total; the centre of mass is computed from the layout) | an ordinary desk is flat to a few degrees; with an 80 x 32 mm footprint any sane layout passes, so this is a low weight check |

### Fixed decisions (a choice that would otherwise be ambiguous; pick one and stick to it)

| # | Decision |
|---|---|
| FD1 | Box frame as in 1.1: jack end -X, hinge side -Y, lid on top. A design with the jack on +X, or the hinge on +Y, is mirrored before grading. |
| FD2 | The toggle is mounted in the lid (its top face is the "top" of the box). A switch in the base wall is not accepted. |
| FD3 | The hinge axis is parallel to X, on the long wall, outside the box's inner cavity. A hinge on the jack end wall is not accepted. |
| FD4 | The latch is on the long wall opposite the hinge. |
| FD5 | The battery lies with its 48.5 mm axis along X. Width (26.5) along Y and thickness (17.5) along Z is the default orientation; the rotated orientation (26.5 vertical) is also accepted and graded on the same L3s, with the limits recomputed from the declared layout. |
| FD6 | The pin is a catalogue part (steel), not a printed body. The package holds exactly two printed bodies: base and lid. |
| FD7 | The plug opening is graded against V-PLUG-DC, with the overmold allowed to enter a counterbore in the wall. A flush or stepped opening are both accepted. |

---

## 4. Requirements tree

### L1.1 The parts are laid out and the layout is declared

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: pose of M-BATT, M-TOG, M-JACK, M-PIN, plus each body's print orientation. | inspection | `layout.json` present, parses, every catalogue id exists | 3 | |
| L3.1.1.1 | Layout file parses and ids exist. | inspection | true | 3 | |
| L2.1.2 | Orientations: battery axis along X; jack axis along -X; toggle axis along +Z; pin axis along X on the -Y side. | inspection | each within 1.0 deg (pin 2.0 deg); pin axis Y < the cavity's mid Y | 2 | |
| L3.1.2.1 | Datum directions from the declared layout. | inspection | as L2.1.2 | 2 | |
| L2.1.3 | The reference parts do not collide with each other, and the clip zone is free. | analysis | pairwise intersection of M-BATT, M-TOG, M-JACK <= 0.01 mm3; V-CLIP clear of M-TOG and M-JACK (d >= 0) | 3 | |
| L3.1.3.1 | Pairwise interference of reference parts. | analysis | each pair <= 0.01 mm3 | 3 | |
| L3.1.3.2 | Clip zone free of the other parts. | analysis | clear_of(M-TOG union M-JACK, V-CLIP, 0.0) | 3 | |
| L2.1.4 | The toggle's axis lies on the lid plate with room for the hole and a ligament. | inspection | the axis, projected on the lid's plan, is >= 5.0 from every lid edge (3.4 hole radius + 1.5 ligament, rounded) | 2 | |
| L3.1.4.1 | Switch axis position on the lid. | inspection | distance to lid outline >= 5.0 | 2 | |

### L1.2 The battery sits in a pocket with room for its clip

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Closed: no printed surface comes within 0.2 of the battery, apart from the floor it rests on. | analysis | clear_of(ALL, M-BATT excluding its BOTTOM face contact, 0.2) | 3 | G2 |
| L3.2.1.1 | Battery clearance to every printed surface except the floor / pads under it. | analysis | d >= 0.20 | 3 | G2 |
| L3.2.1.2 | Clip zone inside the closed box. | analysis | inside(V-CLIP, V-CAVITY, 0.0): d >= 0 | 3 | |
| L3.2.1.3 | Battery rests on the floor. | analysis | M-BATT `BOTTOM` within 0.10 of the floor top (or of its support pads) | 2 | |
| L2.2.2 | The pocket is no looser than needed: each of the three faces of the battery that are not on the floor (two across the width, one on top) has a gap of 0.2 to 0.5 to the nearest printed surface (median over the face). | inspection | 0.20 <= gap <= 0.50, all three faces | 2 | |
| L3.2.2.1 | Gap per face (two across width, one top, floor excluded). | inspection | in [0.20, 0.50] | 2 | |

### L1.3 With the lid closed the battery is held

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Rigid free travel of M-BATT against printed bodies, lid closed: across width <= 1.0, across thickness <= 1.0, along the length <= clip height + 1.5 (= 11.5). | analysis | `travel` values as stated | 3 | G2 |
| L3.3.1.1 | Travel across width and across thickness. | analysis | each <= 1.00 | 3 | G2 |
| L3.3.1.2 | Travel along the length. | analysis | <= 11.5 | 2 | |
| L2.3.2 | A printed stop at the non-terminal end of the battery. | analysis | a printed face within 0.5 of the battery's non-terminal end face, with at least 100 mm2 of overlap in projection | 2 | |
| L3.3.2.1 | Stop distance and projected overlap area. | analysis | gap <= 0.5; area >= 100 mm2 | 2 | |

### L1.4 The toggle switch goes through the lid and is clear of the box

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The lid plate is 2.0 to 4.0 thick at the switch, with a hole for the bushing coaxial with `AXIS`. | inspection | plate thickness in [2.0, 4.0]; hole Ø in [6.2, 6.8]; axis offset <= 0.2 | 3 | G4 |
| L3.4.1.1 | Hole diameter and coaxiality. | inspection | Ø6.2 to 6.8; offset <= 0.20 | 3 | G4 |
| L3.4.1.2 | Plate thickness at the switch. | inspection | 2.0 to 4.0 | 2 | |
| L2.4.2 | Seating and free zones: the plate's underside meets the shoulder; the nut zone and the lever swing are free. | analysis | underside within 0.3 of `SHOULDER`; clear_of(ALL, V-NUT, 0.0); clear_of(ALL, V-LEVER, 0.0) | 3 | G4 |
| L3.4.2.1 | Plate underside versus `SHOULDER`. | inspection | abs(difference) <= 0.30 | 2 | |
| L3.4.2.2 | Nut zone free. | analysis | d >= 0.0 | 3 | G4 |
| L3.4.2.3 | Lever swing free. | analysis | d >= 0.0 | 3 | G4 |
| L2.4.3 | The switch body and its lug room are clear of the box, apart from its seat against the plate. | analysis | clear_of(ALL, M-TOG body union V-LUGS, 0.2), the plate-underside contact excluded | 2 | |
| L3.4.3.1 | Body and lug clearance. | analysis | d >= 0.20 | 2 | |
| L2.4.4 | At least 1.5 of material between the switch hole and any edge, seam or other opening. | analysis | min ligament >= 1.5 | 1 | |
| L3.4.4.1 | Ligament around the switch hole. | analysis | >= 1.5 | 1 | |

### L1.5 A DC plug seats through one opening, and the jack is held

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Lid closed: the plug pushes to full mate and pulls out without touching the box. | test | clear_of(ALL, V-PLUG-DC, 0.3) | 3 | G3 |
| L3.5.1.1 | Plug envelope clear. | test | d >= 0.30 | 3 | G3 |
| L3.5.1.2 | Physical: plug in the owner's adapter. | test | clicks in fully 3 of 3 | 2 | physical, optional |
| L2.5.2 | The opening is not oversized and there is exactly one. | analysis | every slice of V-AP-JACK across the wall lies within V-PLUG-DC grown by 1.5; 1 connected region | 2 | |
| L3.5.2.1 | Opening within the grown envelope (both a counterbored and a straight opening: the slice at each depth). | analysis | d >= 0.0 | 2 | |
| L3.5.2.2 | Opening count in the end wall. | inspection | 1 | 2 | |
| L2.5.3 | The jack is held: its body does not penetrate the printed parts, and free travel is small. | analysis | M-JACK vs printed: intersection <= 0.01 mm3; `travel` along each axis <= 1.0 (total range, lid closed) | 2 | |
| L3.5.3.1 | Jack body interference with printed bodies. | analysis | <= 0.01 mm3 | 3 | |
| L3.5.3.2 | Jack free travel along X, Y and Z. | analysis | each <= 1.00 | 2 | |
| L2.5.4 | The mouth sits close to the outer face of the end wall so the plug's overmold can reach it. | inspection | `MOUTH` X, measured from the end wall's outer face, in [0.0, 3.0] | 2 | |
| L3.5.4.1 | Mouth depth from the outer face. | inspection | 0.0 to 3.0 | 2 | |

### L1.6 The lid is hinged on a 3 mm pin and swings open to 100 degrees

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | The pin bores: a press fit in one body, a clearance fit in the other. | inspection | press bore Ø in [2.9, 3.1]; clearance bore Ø in [3.1, 3.3]; engagement in the press-fit body >= 4.5 (total over its knuckles) | 3 | |
| L3.6.1.1 | Bore diameters. | inspection | as L2.6.1 | 3 | |
| L3.6.1.2 | Pin engagement in the press-fit body. | inspection | >= 4.5 | 2 | |
| L2.6.2 | The pin is captive and fully housed. | analysis | the bores, taken together, span >= 23.0 of the pin's 24.0 along X; no pin end protrudes beyond a printed face by more than 0.5; the pin is not exposed at either end by an open bore wider than Ø3.6 | 2 | |
| L3.6.2.1 | Bore span and pin protrusion. | analysis | span >= 23.0; protrusion <= 0.5 | 2 | |
| L2.6.3 | The lid swings to 100 degrees without anything hitting. | analysis | `swing(100, 5)` of (LID union M-TOG) against (BASE union M-BATT union M-JACK), the pin, knuckle faces and latch hook / catch pair excluded (section 1.3): max intersection <= 0.01 mm3 at every angle | 3 | G5 |
| L3.6.3.1 | Swing interference. | analysis | max intersection <= 0.01 mm3 | 3 | G5 |
| L3.6.3.2 | Axial gap between neighbouring lid and base knuckles. | inspection | in [0.3, 0.8] | 2 | |
| L2.6.4 | The bores are straight and the knuckles strong enough. | inspection | all bores coaxial within 0.2; printed wall around each bore >= 1.6 | 2 | |
| L3.6.4.1 | Bore coaxiality and wall around the bores. | inspection | offset <= 0.2; wall >= 1.6 | 2 | |

### L1.7 The lid is held closed by a snap latch and sits on the base without fusing

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Base and lid are separate bodies, each one shell, not fused, not interpenetrating when closed. | analysis | BASE 1 shell; LID 1 shell; BASE intersect LID <= 1.0 mm3 | 3 | G1 |
| L3.7.1.1 | Base and lid each one connected shell. | analysis | 1 shell each | 3 | G1 |
| L3.7.1.2 | Base and lid do not interpenetrate when closed. | analysis | <= 1.0 mm3 | 3 | |
| L2.7.2 | A snap latch on the long side opposite the hinge: a cantilever with a hook and a catch. | inspection | hook overlap with the catch e in [0.4, 1.2]; cantilever free length L >= 8.0; cantilever thickness t in [1.2, 2.5]; strain 1.5 t e / L^2 <= 0.02 | 2 | |
| L3.7.2.1 | Hook overlap with the catch. | inspection | 0.4 to 1.2 | 2 | |
| L3.7.2.2 | Cantilever length and thickness. | inspection | L >= 8.0; t in [1.2, 2.5] | 2 | |
| L3.7.2.3 | Snap strain. | analysis | 1.5 t e / L^2 <= 0.02 | 2 | |
| L2.7.3 | The latch holds the lid: with the lid rotated rigidly 3 degrees from closed, the hook and catch (or their neighbours) interfere on the latch side. | analysis | at theta = 3 deg the intersection of LID and BASE is > 0.01 mm3 and its centroid lies on the latch's half of the box (Y > mid Y) | 3 | |
| L3.7.3.1 | Rigid-rotation test at 3 degrees. | analysis | intersection > 0.01 mm3, latch side | 3 | |
| L2.7.4 | Lid form: a flat plate covering the base's outer outline, with a locating lip or skirt; the seam is tight. | inspection | plate thickness 2.0 to 4.0; plate outline = base wall outline +-0.5 on each side (hinge knuckles, latch tab and ledge are not part of either outline); lip engagement 2.0 to 3.0; fit 0.15 to 0.35 per side on every locating face; seam gap <= 0.5; step between lid and base outer faces <= 0.5 | 2 | |
| L3.7.4.1 | Plate thickness, outline match, lip engagement. | inspection | as L2.7.4 | 2 | |
| L3.7.4.2 | Lip fit per side, seam gap, outer step. | inspection | fit in [0.15, 0.35]; seam <= 0.5; step <= 0.5 | 2 | |

### L1.8 The box is closed except for the listed openings, with 2 to 4 mm walls

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The only openings are the switch hole, the jack opening, the hinge bores and the seam. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into V-CAVITY, other than those four | 2 | |
| L3.8.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 | |
| L2.8.2 | Walls, floor and lid plate are 2.0 to 4.0 thick. | inspection | each in [2.0, 4.0] | 2 | |
| L3.8.2.1 | Each side wall's thickness (median, away from features). | inspection | 2.0 to 4.0 | 2 | |
| L3.8.2.2 | Floor and lid plate thickness. | inspection | 2.0 to 4.0 | 2 | |
| L2.8.3 | At least 1.5 of material around the jack opening (to wall edges, floor top, seam and the hinge) and between any two openings. | analysis | min ligament >= 1.5 | 1 | |
| L3.8.3.1 | Ligament per opening. | analysis | >= 1.5 | 1 | |
| L2.8.4 | Each wall joins the floor along its length. | analysis | contact >= 90 % of wall length x thickness | 2 | |
| L3.8.4.1 | Wall-to-floor contact. | analysis | >= 0.9 L t | 2 | |

### L1.9 Both parts print on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | In its stated print orientation (default: base open side up, lid outer face down), no part has an unsupported overhang steeper than 45 degrees from vertical, except round holes up to Ø12.0 in vertical walls and bridges up to 15.0. | analysis | 0 offending faces (area > 1 mm2) | 2 | |
| L3.9.1.1 | Overhang and bridge scan per part, including the hinge bores, the latch hook and the jack pocket. | analysis | as L2.9.1 | 2 | |
| L2.9.2 | Each part's mesh is manifold and a single shell. | analysis | 1 shell; manifold3d accepts it | 3 | G1 |
| L3.9.2.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold true | 3 | G1 |
| L2.9.3 | Each part rests on a flat face. | analysis | bed contact >= 50 % of the plan bounding box | 1 | |
| L3.9.3.1 | Bed-contact area per part. | analysis | >= 50 % | 1 | |
| L2.9.4 | No feature thinner than 0.8; the latch cantilever and the knuckles at least 1.2. | analysis | min wall >= 0.8 elsewhere; >= 1.2 on the cantilever and around the bores | 1 | |
| L3.9.4.1 | Thin-feature scan. | analysis | as L2.9.4 | 1 | |
| L2.9.5 | Each part fits a 200 x 200 x 200 bed. | inspection | bounding box <= 200 per axis | 1 | |
| L3.9.5.1 | Bounding box per part. | inspection | <= 200 per axis | 1 | |

### L1.10 It is compact and stands on a desk

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Closed outside size of the printed bodies <= 90 x 45 x 30, longest side along X. | inspection | X <= 90.0, Y <= 45.0, Z <= 30.0; X > Y | 1 | |
| L3.10.1.1 | Assembly bounding box (pin ends and switch lever excluded). | inspection | as L2.10.1 | 1 | |
| L2.10.2 | It stands on its floor without tipping. | analysis | stable at 5 degrees table tilt with the battery in place (mass 60 g total, centre from the layout) | 1 | |
| L3.10.2.1 | Stability at 5 degrees. | analysis | passes | 1 | |
| L2.10.3 | Flat underside; nothing below the floor except equal feet <= 3.0 tall. | inspection | flatness <= 0.2; feet equal within 0.1 | 1 | |
| L3.10.3.1 | Underside planarity. | inspection | as L2.10.3 | 1 | |

### L1.11 The battery goes in and comes out with the lid open

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Lid open at 100 degrees: the battery, with its clip zone, drops straight down into the pocket and lifts straight out. | test | clear_of(BASE union V-SWING(100) union M-JACK, V-BATT-INSTALL, 0.2), the seat on the floor excluded | 3 | |
| L3.11.1.1 | Install / removal sweep clear. | test | d >= 0.20 | 3 | |
| L2.11.2 | The open lid stays open without a stop in the way of the sweep; it does not need to rest on the table. | analysis | angle 100 reached (L2.6.3 passes) | 1 | |
| L3.11.2.1 | Open angle reached. | analysis | 100 degrees without penetration | 1 | |

### L1.12 The package says what was built, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds `base.stl`, `lid.stl` (closed pose, box frame, mm), the `.scad` source, `layout.json` and the agent's own report. | inspection | all present and readable | 3 | G0 |
| L3.12.1.1 | Files present and parse; each body's largest bounding-box axis is within 20 to 200. | inspection | true | 3 | G0 |
| L3.12.1.2 | The declared layout verifies under the seating rule. | analysis | battery on floor <= 0.10; switch axis <= 0.25; jack mouth <= 0.25; pin axis <= 0.20 | 3 | |
| L2.12.2 | The agent's own report agrees with the judge's measurements. | analysis | same pass / fail and abs(d_agent - d_judge) <= 0.10 for every `clear_of`, `inside`, `travel`, `swing` L3 reported | 1 | |
| L3.12.2.1 | Self-report versus judge. | analysis | 100 % agreement within 0.10 | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 40 |
| L3 | 58 (1 physical item, L3.5.1.2, is optional) |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.12.1.1); **G1**
manifold and two bodies (L3.9.2.1, L3.7.1.1); **G2** battery fits and is held (L3.2.1.1,
L3.3.1.1); **G3** DC plug seats (L3.5.1.1); **G4** toggle mounts (L3.4.1.1, L3.4.2.2, L3.4.2.3);
**G5** the hinge swings clear (L3.6.3.1).

---

## 6. Feasibility

A design exists that meets every number above. It was checked by arithmetic and, for the swing, by placing points through the rotation (the toggle body's worst corner clears the +Y wall by about
2.0). Key dimensions, box frame, mm, floor underside Z = 0, walls and floor 2.4, lid plate 3.0:

- **Cavity:** inner X 2.4 to 77.5, inner Y 2.4 to 29.5 (27.1 wide = 26.5 + 2 x 0.3), inner Z 2.4 to
  20.4 (18.0 high). Outer 79.9 x 31.9 x 20.4 for the base; with the lid 23.4 high. Hinge knuckles
  (OD 7.0, axis y = -3.5, z = 19.9, so the knuckle top is flush with the lid's outer face at z = 23.4 and the lid still rests flat) add 7.0 on -Y, the latch tab adds about 3 on +Y: **about
  79.9 x 42 x 23.4**, inside 90 x 45 x 30.
- **Battery:** long axis along X, x 18.5 to 67.0, y 2.7 to 29.2, z 2.4 to 19.9 (resting on the floor,
  top gap 0.5 to the lid underside; across the width 0.3 per side). Clip zone x 67.0 to 77.0 (free,
  end wall inner face at 77.5): X travel = 0.3 + 10.5 = 10.8 <= 11.5. Stop rib x 16.6 to 18.2
  (1.6 thick) gives a 0.3 gap at the non-terminal end; rib area on the end face is 17.5 x 14 >= 100.
- **Jack:** on a 3.5 high platform, so its body is z 5.9 to 16.9 and its axis z = 11.4, at y 4.0 to
  13.0, body x 2.4 to 16.4, mouth at x = 2.4 (at the end wall's inner face), mouth depth from the
  outer face 2.4 (in [0.0, 3.0]). Plug: overmold face at x = 1.4 (1.0 outside the mouth), barrel
  x 1.4 to 15.4. Opening: a Ø11.8 counterbore x 0 to 1.4 (0.4 clear of the overmold's Ø11.0, within
  the 1.5 oversize) and a Ø6.5 hole x 1.4 to 2.4 (0.5 clear of the Ø5.5 barrel). Ligaments: 2.6 to
  the -Y wall edge, 3.1 to the floor top, 3.1 to the seam. A lid hold-down rib (2.5 tall, over the
  jack) leaves a 1.0 gap, so the jack's Z travel is 1.0 and its side travel is 0.2 per side.
- **Toggle:** in the lid, axis x = 9.5, y = 22.0; body z 10.4 to 20.4 (13 x 8 footprint at x 3.0
  to 16.0, y 18.0 to 26.0), shoulder on the plate underside (z 20.4), plate 3.0 thick (to z 23.4),
  bushing top z 28.4 (5.0 above the plate; V-NUT z 23.4 to 28.4 free), lever swing z 28.4 to
  40.4 free. Hole Ø6.5. Lug room z 6.4 to 10.4, 4.0 above the floor top. The toggle (y 18 to 26)
  and jack (y 4 to 13) are 5.0 apart in Y, so they do not interfere.
- **Hinge:** three knuckles along the -Y wall over x 25 to 50 (25 long), 7.0 OD, axis y = -3.5,
  z = 19.9 (0.5 below the lid plate underside, 3.5 below its outer face), pin x 25.5 to 49.5 (24.0). The lid knuckles are
  fused to the plate edge through a web that fills up to the outer face; the base knuckles hang on a 45 degree gusset
  down to the -Y wall (the wall is tangent to the knuckle at y = 0). Lid knuckle bores Ø3.2, base knuckle bores Ø3.0 (press),
  axial gaps 0.5, press-fit engagement 2 x 5.0 = 10.0. Lid skirt (outside the base's stepped rim,
  1.2 thick, engagement 2.0, fit 0.25 per side) except at the hinge side. Because every lid point
  below the axis (the skirt, the plate underside) has positive Y distance from it, those points
  rise from the first degree of rotation; the toggle body's worst corner (13 x 8 body, 29.5 from the axis in Y and
  9.5 below it) reaches y = -3.5 + sqrt(29.5^2 + 9.5^2) = 27.5 at most, 2.0 inside the +Y wall's inner face (29.5), so it
  never touches the wall; the lid's own skirt and rib rise away from the base from the first degree.
- **Latch:** a tab on the lid's +Y edge: cantilever L = 10.0, t = 1.6, hook overlap e = 0.8:
  strain 1.5 x 1.6 x 0.8 / 100 = 0.019 <= 0.02. At 3 degrees the hook, about 36 from the axis, sweeps 36 x sin 3 = 1.9 > 0.8 into
  the ledge, so L3.7.3.1 reads the interference on the +Y side.
- **Print:** base open side up; lid outer face down, with the hold-down rib and the toggle plate
  upward. Hinge bores are horizontal round holes (exempt); the latch hook's catching face is inclined 45 degrees so that it prints without support (it still interferes in the 3 degree test), and the lid knuckles' lower arcs are flattened to the bed.

---

## 7. Where this stresses the agent (beyond_library)

1. Subtraction: the toggle hole, the stepped jack opening, hinge bores, a jack pocket.
2. A hinge: knuckles on two bodies on a shared axis, a catalogue pin, and a swept-rotation check.
3. A snap latch sized by an elastic strain limit.
4. Retention by travel limits derived from catalogue datums (battery, jack).
5. Envelopes from datums: clip zone, lever swing, nut zone, plug sweep, install sweep.
6. A lid that carries a part (the toggle), so the swing check moves the toggle with it.

---

## 8. Traceability

| L1 | Owner need | L2 | L3 | Words in the request it comes from |
|---|---|---|---|---|
| L1.1 | Layout | L2.1.1-L2.1.4 | L3.1.1.1, L3.1.2.1, L3.1.3.1-2, L3.1.4.1 | "toggle switch on top and a panel DC jack on one end" |
| L1.2 | Battery pocket | L2.2.1-L2.2.2 | L3.2.1.1-3, L3.2.2.1 | "pocket box for a 9V PP3 battery (26.5 x 17.5 x 48.5 mm)" |
| L1.3 | Battery held | L2.3.1-L2.3.2 | L3.3.1.1-2, L3.3.2.1 | "The battery must be retained" |
| L1.4 | Toggle | L2.4.1-L2.4.4 | L3.4.1.1-2, L3.4.2.1-3, L3.4.3.1, L3.4.4.1 | "a toggle switch on top" |
| L1.5 | DC plug and jack | L2.5.1-L2.5.4 | L3.5.1.1-2, L3.5.2.1-2, L3.5.3.1-2, L3.5.4.1 | "the DC plug body has to fit when the jack is used" |
| L1.6 | Hinge | L2.6.1-L2.6.4 | L3.6.1.1-2, L3.6.2.1, L3.6.3.1-2, L3.6.4.1 | "hinged with a 3 mm steel pin" |
| L1.7 | Latch and lid | L2.7.1-L2.7.4 | L3.7.1.1-2, L3.7.2.1-3, L3.7.3.1, L3.7.4.1-2 | "closes with a snap latch" |
| L1.8 | Protection | L2.8.1-L2.8.4 | L3.8.1.1, L3.8.2.1-2, L3.8.3.1, L3.8.4.1 | "box" (implied) |
| L1.9 | Printable | L2.9.1-L2.9.5 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1, L3.9.5.1 | implied (OpenSCAD to FDM) |
| L1.10 | Compact, stable | L2.10.1-L2.10.3 | L3.10.1.1, L3.10.2.1, L3.10.3.1 | "pocket box" |
| L1.11 | Battery change | L2.11.1-L2.11.2 | L3.11.1.1, L3.11.2.1 | implied (battery is replaceable) |
| L1.12 | Evidence | L2.12.1-L2.12.2 | L3.12.1.1-2, L3.12.2.1 | needed by the judge |

---

## 9. Grading rules (self-contained fallback for `generalize/rubric.md`)

Use `/Users/robinonsay/python/llm-bt/venv/bin/python` with `manifold3d` and `trimesh`; count shells with
`Manifold.decompose()`.

1. **Package (G0), units.** Load `base.stl`, `lid.stl`; each body's largest axis must be 20 to 200 mm.
2. **Normalise** into the box frame (rotations by multiples of 90 degrees and mirroring only).
3. **Build references** from the catalogue and `layout.json`; run R1-R6; verify the seating rule.
4. **Measure every L3** in order: record measured value, limit, signed margin (negative = fail),
   PASS / FAIL / UNVERIFIED. UNVERIFIED counts as FAIL.
5. **Recipes.** `clear_of`: penetration = volume of intersection; if > 0.01 report it, else d = min gap of the two
   manifolds. `inside`: hull test plus min gap to the hull's outside. `travel`: bisect along the axis
   until the intersection exceeds 0.01 mm3 (0.02 resolution), both directions. `swing`: rotate the moving set
   about the pin axis and intersect at each step. Thickness and gaps: ray casting on a 2 mm grid, median
   over the face, 3 mm clear of edges. Holes: largest inscribed circle of a mid-depth slice.
6. **Class.** WRONG: any gate fails. MINOR: no gate fails but a weight-3 L3 fails. CORRECT: no gate
   fails and all weight-3 L3s pass. **MEETS** = CORRECT and every applicable non-physical weight-1 and
   weight-2 L3 passes. Also report the weighted score and the worst normalised margin among weight-3 L3s.
7. **Precedence.** The numbers in this document beat `part.json`; if they disagree, build the references from
   this document and record a defect against the requirement that the stale catalogue number breaks (where =
   the `part.json` field). Plug-seating and clearance L3s outrank opening-size L3s. Designed contact (section 1.3)
   is never interference.
8. **Where.** One entry per failed or UNVERIFIED L3: `req`, `status`, `body` (base / lid / both / layout), `feature`,
   `face` (with outward normal), `location` (box-frame bounding box in mm), `measured` / `limit` / `margin`,
   `reference` (model or envelope and datum), `needed` (a numeric target the next agent can verify, never a
   design instruction), `evidence` (saved defect STL). Separate observations (render-only) from defects.

---

## Audit

Adversarial audit (2026-10-24). Checked: every part id in the plan exists in `benchmarks/generalize/parts`
and passes `parts.gate` (all 54 + 12 catalogue parts load); L1 count 12 (in 8 to 14) and the counts in
section 5 (12 / 40 / 58) match the tables; every L2 has an L3 and every L3 a parent; the Feasibility numbers
were recomputed (cavity, battery, jack, plug, toggle, hinge swing by sampling every degree 0 to 100, latch
rise). `benchmarks/generalize/rubric.md` does not exist, so section 9 is the grading procedure (as this
document already says). Fixes, all in place:

1. **Swing versus snap latch contradiction.** L2.7.3 requires the hook to interfere under a rigid 3 degree
   rotation, while L2.6.3 / L3.6.3.1 required no intersection at every angle from 5 degrees, so no snap latch
   could pass both. Section 1.3 now excludes the latch pair from the swing sets (lid material that meets the
   base in the 3 degree rotation, and the base material it meets, grown by 0.5); L2.6.3 refers to it.
2. **Hinge height made the lid unprintable.** The feasibility hinge axis z = 21.9 put the knuckles 2.0 above
   the lid's outer face (z 23.4), so the lid printed outer-face-down would not rest on its face (L2.9.3,
   L3.9.3.1) and the closed height was 25.4, not 23.4. Axis moved to z = 19.9 (knuckle top flush with the
   outer face). Swing recomputed: the toggle body's worst corner now reaches y = 27.5 against the wall at
   29.5 (margin 2.0, was claimed 1.0); every skirt, plate and rib point rises from the first degree.
3. **Latch print claim.** The "45 degree underside" was ambiguous; the catching face is now stated as inclined
   45 degrees (still interferes in the 3 degree test), and the lid knuckles' lower arcs are flattened.
4. **L2.2.2 said "four long faces"** but L3.2.2.1 and the geometry have three free faces (floor excluded):
   made three in both.
5. **V-NUT** was defined as ending at `BUSHING_TOP` with a fixed 3.0 height (the part.json `nut_zone`), which
   floats above a 3.0 plate and contradicted "the nut sits on the panel's outer face". It now starts at the
   measured outer face of the plate and runs to `BUSHING_TOP`; A15 reworded. The feasibility design still
   passes (nothing printed above the plate near the toggle).
6. **A7 knuckle OD** was `>= 6.2` from the 3.0 bore, but the clearance bore is 3.2: now `>= 6.4`
   (7.0 used, wall 1.9 >= 1.6).
7. **Outline ambiguity (L2.7.4, L3.10.1.1).** The plate must equal the base outline +-0.5, but hinge knuckles
   (-Y) and the latch tab/ledge (+Y) lie outside the base wall: both are now excluded from the outlines.
8. **Stability numbers (5 degrees, 60 g)** in L2.10.2 had no assumption: added A16.
9. **Hidden numbers.** The judge needed bands the agent was never told. Added to the request and the L1
   texts in `design.json`: pocket gap 0.2 to 0.5 on the two sides and top (L1.2), toggle hole 0.2 to 0.8 over
   the bushing (L1.4), latch cantilever limits and 2 percent strain (L1.7 and request), open angle 100 in the
   request (already in L1.6). Request notes updated.
10. Table formatting: `|d_agent - d_judge|` inside a table row split the cell; now `abs(...)`.

Checked and left unchanged: jack plug opening and ligaments (3.1, 3.1, 2.6), jack travel 1.0 (exactly at the
limit, passes within e), battery travel (0.6 / 0.5 / 10.8), clip zone inside the cavity, install sweep with the
lid open (toggle at x 3 to 16 is clear of the battery column at x >= 18.5), strain 0.019, overall size
79.9 x 42 x 23.4.

Not fixable here: the optional physical tests need a print.
