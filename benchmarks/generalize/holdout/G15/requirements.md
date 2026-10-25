# G15 LiPo charger pocket box with USB-C: requirements (L1 / L2 / L3)

Held-out design of the generalisation set (`benchmarks/generalize/holdout/G15`). The machine-readable
request (L1 only, `dev.json` format) is `design.json` next to this file. It is modelled on
`benchmarks/enclosure/requirements.md` (E1-01) and uses the same tree, the same two interference
checks and the same grading classes. The agent never sees this file's numbers except through the
request text and the parts catalogue (`benchmarks/generalize/parts/*/part.json`).

**Brief (plan.json G15):** "A compact box for a 5 x 34 x 50 mm LiPo, a TP4056 USB-C charger board
(26 x 17 mm) and a slide switch. The battery sits in a pocket with 0.5 mm side clearance and cannot
press on the charger board. The USB-C plug overmold (12.4 x 6.5 mm) must reach the port, and the lid
is a snap fit."

**How to read this.** L1 says what the owner needs, L2 turns it into an engineering requirement with
numbers, L3 is a concrete check on the delivered geometry. Every row has a method (inspection,
analysis, demonstration, test, human), a pass/fail criterion with a tolerance, a weight (3 critical,
2 major, 1 minor) and a gate mark where a failure makes the design WRONG. Every number that comes
from an assumption (section 3) is provisional. Do not relax a criterion because the agent fails it.

---

## 1. Frames, tolerances and the generic checks

### 1.1 Frames

- **Box frame:** X along the box's longer plan side, Z up, floor underside at Z = 0. The end wall
  with the USB-C opening is **−X**; the end wall with the switch opening is **+X**. A design
  delivered mirrored or rotated is normalised into this frame before grading; that is never
  penalised.
- **Part frames** are those of the catalogue part files, each placed by the pose the design
  declares in `layout.json` (section 4, F8): `tp4056_usbc_module` (origin at the PCB min corner,
  PCB bottom at Z = 0, USB-C end at −X), `lipo_503450` (origin at the pouch min corner, tabs on
  the +X short edge), `slide_sk12d` (origin at the body min corner, handle toward +Z, travel along
  X), `plug_usbc` (origin at the tip, body toward +X).

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered meshes (STL), never by eye.

| Quantity | Measurement tolerance ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within ε (a limit "≥ 0.50" passes at 0.48) |
| angle | 0.5° | same |
| interference volume | 0.01 mm³ | "no interference" means intersection volume ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the hole's section (what a screw or pin sees) | |
| boss / post OD | smallest enclosing circle of the section | |
| stress / strain | 2% of the limit | hand calculations use the measured section, not the nominal one |

Where a criterion is written "nominal ± t", t is the design tolerance and ε is added to it.


### 1.3 The generic checks

- **`clear_of(bodies, volume, clearance)`**: the minimum Euclidean distance between every printed
  body in `bodies` and `volume` is ≥ `clearance`. Reported: signed minimum distance d (negative =
  penetration; the penetration volume is reported too). Pass: d ≥ clearance − ε.
- **`inside(volume, solids, clearance)`**: `volume` lies entirely inside the convex hull of `solids`
  and every point of it is ≥ `clearance` from that hull's boundary and from the solids. Pass:
  d ≥ clearance − ε.
- **`gap(A, B)`**: the minimum distance between two named regions, by `min_gap` or ray casting on a
  1 mm grid (report min, median, max).
- **`play(body, axis)`**: translate the body's solid along ±axis in 0.05 mm steps (to 10 mm) until
  it first intersects a printed body by more than 0.01 mm³; report the free travel in each
  direction (sum = play along the axis).

Both checks exclude designed-contact pairs from the solids they measure against (so `inside` of a part that rests on its support passes). Generic recipes (loading, shells with `decompose()`, apertures, thickness, hole diameter,
overhang scan) are those of `benchmarks/enclosure/rubric.md` section 3, unchanged.

**Designed contact is not interference.** Pairs that are meant to touch are excluded from every
interference and clearance check; for them only penetration counts (intersection volume above
0.01 mm³; a distance of zero is a pass). For this design the designed-contact pairs are:

- the charger PCB's underside resting on its supports (support tops, inside the PCB footprint);
- the LiPo pouch's underside resting on the floor or its pocket ribs;
- the switch body against its cradle and against the +X wall's inner face;
- the lid's locating lip against the base's inner wall faces, at the fit L2.7.2 sets;
- a snap hook inside its catch (hook flank against catch ledge);
- the lid resting on the base rim.

---

## 2. Reference models, envelopes and datums

### 2.1 Reference models (M-)

All built by Python from the catalogue at the declared pose. A design never builds or edits them;
the grader generates them independently.

| Name | What | Source | Size and datums (part frame, mm) |
|---|---|---|---|
| **M-TP** | TP4056 USB-C charger board | `tp4056_usbc_module` | PCB 26.0 × 17.0 × 1.0 at X 0-26, Y 0-17, Z 0-1.0; USB-C receptacle 7.3 (X) × 8.94 (Y) × 3.26 (Z) at X −1.0 to 6.3, Y centred, Z 1.0-4.26; top parts up to 1.8 above the PCB (Z 1.0-2.8). Datums `USB_MOUTH` (−1.0, 8.5, 2.63), `USB_AXIS` (−X), `PCB_TOP`, `PCB_BOTTOM`, `PADS` (4 axes at (24, 2), (24, 15), (2, 2), (2, 15)). No mounting holes. |
| **M-CELL** | 503450 LiPo pouch | `lipo_503450` | 50.0 (X) × 34.0 (Y) × 5.0 (Z); tabs on the +X short edge. Datums `TABS` (54.0, 17.0, 2.5), `TAB_DIR` (+X), `BOTTOM`, `TOP`, `SWELL_TOP` (Z 5.5). |
| **M-SW** | SK12D slide switch | `slide_sk12d` | body 12.5 × 6.0 × 5.5, handle 3.0 × 3.0 × 4.0 on top, travel 3.5 along X. Datums `BODY_TOP`, `ACTUATOR_AXIS` (+Z, from the body top centre), `HANDLE_CENTER` (Z 9.5), `TRAVEL_AXIS` (X). |
| **M-PLUG-USBC** | USB-C cable plug | `plug_usbc` | shell 8.25 × 2.4, inserted depth 6.65, exposed shell 1.0; overmold 12.4 × 6.5 × 20. Datums `PLUG_TIP`, `PLUG_AXIS`, `SEAT` (6.65 from the tip), `OVERMOLD_FACE`. |
| **RA** | reference assembly | M-TP ∪ M-CELL ∪ M-SW at the declared poses | no printed geometry |

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-USB-PLUG** | the plug at full mate plus its path | M-PLUG-USBC with `SEAT` on `USB_MOUTH` and `PLUG_AXIS` along `USB_AXIS`: shell 8.25 × 2.4 from 6.65 inside the mouth to 1.0 outside it; overmold 12.4 × 6.5 from 1.0 outside the mouth outward 20 + 40 (the 40 is the generic plug travel). Centred on `USB_MOUTH`. |
| **V-SWELL** | the cell with 10 % thickness swell | the `swell` keep-out of `lipo_503450`: 50.0 × 34.0 × 5.5 on the cell pose. |
| **V-TAB** | tab and bend zone | the `tab_zone` keep-out of `lipo_503450`: 7.0 (X, from the pouch edge) × 10.0 (Y, centred) × 1.5 (Z, centred in the thickness), on `TAB_DIR`. |
| **V-COMP-TOP** | component side of the charger board | the `component_side` keep-out: 26 × 17 × 1.8 on `PCB_TOP`. |
| **V-WIRE-TOP / V-WIRE-BOT** | solder wire room at the pad end | the `wire_pads_top` and `wire_pads_bottom` keep-outs: 5.0 (X 21-26) × 17.0 × 2.0 above `PCB_TOP` and 2.0 below `PCB_BOTTOM`. |
| **V-SW-SWEEP** | the handle through its travel | the `handle_sweep` keep-out of `slide_sk12d`: 6.5 (travel + handle) × 3.0 × 4.0 on `BODY_TOP`, extended outward along `ACTUATOR_AXIS` past the wall (to 4.0 above the body top, the handle tip). |
| **V-INSTALL-CELL / -TP** | drop-in paths | M-CELL (pouch plus tab zone) and M-TP (PCB plus receptacle), each swept +Z from the seated pose to 5.0 above the base rim, lid off. |
| **V-INSTALL-SW** | switch insertion path | M-SW swept −X (away from the +X wall) by 15.0 from its seated pose, lid off (it is slid outward into its cradle with the handle through the slot). |
| **V-CAVITY** | the closed box's internal void | convex hull of (BASE ∪ LID, closed) minus (BASE ∪ LID), the connected component containing M-CELL's centroid. |
| **V-AP-USB**, **V-AP-SW**, **V-AP-OTHER** | the openings actually present in the −X wall, the +X wall and elsewhere | computed as in `benchmarks/enclosure/rubric.md` 3.4. |
| **V-WIRE-PATH** | wire passage | the free air in V-CAVITY (minus printed bodies and minus M-TP, M-CELL, M-SW) eroded by 1.0 (a Ø2.0 wire), on a 0.5 mm voxel grid. |
| **CONTACT-SET** | printed features that hold the PCB | printed supports under it, hold-downs over it and free-standing stops beside it, i.e. printed material within 0.3 of M-TP's PCB faces or edges. The pocket partition and the outer walls are structure, not part of the set, even where they stand 0.3 from an edge (they must also separate the cell from the board, L2.4.3, so they cannot be 1.0 from V-SWELL). |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | every model | units: bounding boxes in mm | M-TP PCB 26.0 × 17.0 ± 1.0; M-CELL 50 × 34 × 5 ± 0.3; M-SW body 12.5 × 6 × 5.5 ± 0.3 |
| R2 | M-TP | components on +Z, receptacle at −X, `USB_AXIS` along −X | all true |
| R3 | M-CELL | tabs on +X, `TAB_DIR` along +X | true |
| R4 | M-SW | handle toward +Z, `ACTUATOR_AXIS` along +Z | true |
| R5 | RA | models do not collide | intersection ≤ 0.01 mm³ |
| R6 | every V- envelope | its datums equal the model datums it came from | ≤ 0.01 |

**Seating rule.** The grader places M-TP, M-CELL and M-SW at the declared poses and verifies them:
M-TP's `PCB_BOTTOM` lies on the support tops (distance ≤ 0.10); M-CELL's `BOTTOM` is within 0.3 of
the printed floor or ribs under it; M-SW's `BODY_TOP` is within 0.5 of the +X wall's inner face.
If a declaration fails, the part is re-seated by the nearest printed support and the L3 that
needed the declaration fails.

---

## 3. Assumptions and open questions

Each line gives the value chosen and why, with its uncertainty. The part dimensions are the
catalogue's; where the owner's real part differs, the catalogue is updated and the design re-graded.

| # | Question | Value chosen | Uncertainty / why |
|---|---|---|---|
| A1 | Cell size? | 5.0 × 34.0 × 50.0 (the brief), pouch is the maximum size; 10 % thickness swell in service | swell 5-15 %; 10 % is general LiPo guidance. A real 503450 can be 0.3 under size. |
| A2 | Tabs? | on the +X short edge, 4 mm long, 10 mm wide, 1.5 thick, 3 mm bend room (7.0 zone) | ± 2 mm; vendor leads vary. Zone orientation is free: the cell may be turned 180° or 90° about Z. |
| A3 | Charger board? | PCB 26.0 × 17.0 × 1.0, receptacle overhang 1.0, top parts 1.8, pads 2.0 in from the edges | ± 1.0 mm between vendors (catalogue note). No mounting holes: held by supports, stops and hold-downs (F4). |
| A4 | Plug sizes? | USB-C overmold 12.4 × 6.5 × 20 (brief), shell 8.25 × 2.4, mated depth 6.65 | overmold length ± 5; shell per USB-IF. Measure the owner's cable. |
| A5 | Switch? | SK12D body 12.5 × 6.0 × 5.5, handle 3 × 3 × 4.0 high, travel 3.5 | handle height ± 1.0 (options 2-6): L3.6.3.1 uses the catalogue value. |
| A6 | Wires? | cell leads reach at most 50.0 straight-line from `TABS` to a pad (60 mm leads, 10 mm slack) | ± 20 mm. Which pad is B+ is vendor-specific and not graded: any two of the four pads. |
| A7 | Printing? | FDM, PLA, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed; sliding fit 0.15-0.35 per side | typical FDM tolerances. |
| A8 | Wall thickness? | outer walls, floor and lid plate 2.0-3.0; internal partitions and ribs ≥ 0.8 | 2.0 min keeps 5 perimeters; 3.0 max keeps the switch handle 1.0 proud (L2.6.3). |
| A9 | Size limit? | closed box ≤ 70 × 60 × 25 (X × Y × Z), X > Y | compact box: the layout of section 7 is about 63 × 59 × 15. A side-by-side layout along X (about 90 long) fails. |
| A10 | Board clearance? | ≥ 0.2 to every printed surface apart from the contact set; stops within 0.5 per side | 0.2 is the generic part-to-wall allowance; 0.5 would defeat the stops. |
| A11 | Snap geometry? | hook engagement 0.4-1.0, catch clearance 0.1-0.4, beam strain ≤ 2.0 % | PLA yields near 2 % strain; 0.4 is the smallest engagement that holds a 15 g lid inverted. |
| A12 | Load? | the cell, board and switch weigh under 40 g together; no cable pull is graded | the box rests on a desk or in a pocket. |
| A13 | Venting, LEDs, labels? | none | a 1 A charger dissipates under 1 W; the board's own LEDs are not required to be visible (confirm). |

---

## 4. Fixed decisions (a choice would otherwise be ambiguous)

| # | Decision | Why |
|---|---|---|
| F1 | The USB-C opening is in one short end wall (−X) and nowhere else. | the brief says the plug must reach the port; one port, one opening. |
| F2 | The switch handle exits through the opposite short end wall (+X), travelling along the wall's long dimension (`TRAVEL_AXIS` within 1° of ±Y or ±Z, tangent to the wall). | the handle must be operable with the lid on; a tangential travel keeps the slot a flat rectangle. |
| F3 | Closed pose: base holds everything; the lid is a flat plate over the base's outline with a locating lip inside the walls and snap hooks; nothing else is printed. | two printed bodies, as the brief ("the lid is a snap fit"). |
| F4 | The charger board is held by supports under it, stops at its edges and hold-downs above it. No screws, no glue. | the board has no mounting holes. |
| F5 | The lid closure is snap-fit only: no screws, bosses or screw holes anywhere. | brief. |
| F6 | Print orientation: base open side up, lid outer face down; the design states both in `layout.json`. | needed to grade printability. |
| F7 | The battery pocket is a pocket in the base, bounded by printed walls on its three non-tab sides; the tab side is open to the wire space. | tabs need room (A2). |
| F8 | `layout.json` declares the pose of M-TP, M-CELL and M-SW (catalogue id, X, Y, Z, rotation about Z in 90° steps), each body's print orientation and the closure type. | needed by the seating rule. |

---

## 5. Requirements tree

Columns: ID, requirement, method, pass/fail (with tolerance), weight, gate.

### L1.1 The parts are laid out so the USB-C port faces one short end and the switch handle faces the other

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout (F8). | inspection | `layout.json` parses and names M-TP, M-CELL, M-SW by catalogue id with a pose each | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 | |
| L2.1.2 | The USB-C port faces −X and the switch handle +X. | inspection | `USB_AXIS` within 1.0° of −X; `ACTUATOR_AXIS` within 1.0° of +X | 3 | |
| L3.1.2.1 | USB axis direction. | inspection | angle ≤ 1.0° (+ 0.5° ε) | 3 | |
| L3.1.2.2 | Switch actuator direction and travel tangent to the wall (F2). | inspection | actuator ≤ 1.0° off +X; `TRAVEL_AXIS` within 1.0° of ±Y or ±Z | 3 | |
| L2.1.3 | The parts do not collide and their keep-outs are respected. | analysis | R5 pairs ≤ 0.01 mm³; V-TAB, V-WIRE-TOP, V-WIRE-BOT do not intersect M-TP, M-SW (V-TAB vs M-CELL is designed contact) | 3 | |
| L3.1.3.1 | Pairwise interference of M-TP, M-CELL, M-SW. | analysis | each pair ≤ 0.01 mm³ | 3 | |
| L3.1.3.2 | Keep-outs against other parts. | analysis | V-TAB ∩ (M-TP ∪ M-SW) ≤ 0.01 mm³; V-WIRE-TOP/BOT ∩ (M-CELL ∪ M-SW) ≤ 0.01 mm³ | 2 | |
| L2.1.4 | The cell's leads can reach the board. | inspection | at least 2 of the 4 `PADS` datums within 50.0 of `TABS` (A6) | 1 | |
| L3.1.4.1 | Tab-to-pad distances. | inspection | count of pads with distance ≤ 50.0 is ≥ 2 | 1 | |
| L2.1.5 | The board and cell lie flat. | inspection | PCB normal and cell thickness axis within 2.0° of +Z | 2 | |
| L3.1.5.1 | Orientation of M-TP and M-CELL. | inspection | both ≤ 2.0° | 2 | |

### L1.2 The charger board sits in the closed box held against moving, with room around it and its solder pads free

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | No printed surface within 0.2 of the board, receptacle or its parts, except the contact set under the PCB. | analysis | clear_of(ALL minus CONTACT-SET support tops, M-TP, 0.2) | 3 | |
| L3.2.1.1 | Board clearance, all edges and faces. | analysis | d ≥ 0.20 | 3 | |
| L2.2.2 | The whole board is inside the closed cavity. | analysis | inside(M-TP, V-CAVITY, 0.2), the support contact excluded | 3 | |
| L3.2.2.1 | Board and receptacle inside the cavity. | analysis | d ≥ 0.20 | 3 | |
| L2.2.3 | The PCB rests on at least two supports, all coplanar, none under the pad end's wire zone. | inspection | ≥ 2 support patches under the PCB; each ≥ 6 mm²; support tops within 0.10 of `PCB_BOTTOM`, spread ≤ 0.10 | 2 | |
| L3.2.3.1 | Support count, area, top-plane spread. | inspection | as L2.2.3 | 2 | |
| L3.2.3.2 | Wire and component zones clear. | analysis | clear_of(ALL minus contact tops, V-COMP-TOP ∪ V-WIRE-TOP ∪ V-WIRE-BOT, 0.0) | 3 | |
| L2.2.4 | The board cannot shift or lift out. | analysis | `play(PCB solid, X)` ≤ 1.0, `play(PCB solid, Y)` ≤ 1.0; upward free travel (closed, lid on) ≤ 4.0 | 2 | |
| L3.2.4.1 | Lateral play. | analysis | X and Y totals ≤ 1.0 | 2 | |
| L3.2.4.2 | Lift before a printed surface blocks it. | analysis | free travel +Z ≤ 4.0 | 2 | |

### L1.3 The LiPo sits in a pocket with 0.5 mm side clearance, room to swell and its tabs free

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | On its three non-tab sides the pouch has 0.5 mm clearance to the pocket walls. | analysis | median gap per side from the pouch edge to the first printed surface at mid-thickness (1 mm ray grid) in [0.40, 0.70] | 3 | G3 |
| L3.3.1.1 | Side clearance per side (three values). | analysis | each median in [0.40, 0.70]; max − min on a side ≤ 0.6 | 3 | G3 |
| L2.3.2 | The pouch does not touch the pocket and is contained by it. | analysis | clear_of(ALL, M-CELL pouch minus its bottom face, 0.40); pocket wall at least 3.0 high above the pouch bottom on the three sides | 3 | G3 |
| L3.3.2.1 | Pouch clear of printed surfaces (floor contact excluded). | analysis | d ≥ 0.40 | 3 | G3 |
| L3.3.2.2 | Pocket wall height on the three non-tab sides. | inspection | ≥ 3.0 above `BOTTOM`, over ≥ 80 % of each side | 2 | |
| L2.3.3 | Room above the cell for swelling, without letting it float. | analysis | the lowest printed surface above the cell's plan lies [0.2, 1.5] above `SWELL_TOP` | 2 | |
| L3.3.3.1 | Swell room. | analysis | 0.2 ≤ gap ≤ 1.5 (closed) | 2 | |
| L2.3.4 | The tab zone is free of printed material. | analysis | clear_of(ALL, V-TAB, 0.0) | 3 | G3 |
| L3.3.4.1 | Tab zone clear. | analysis | d ≥ 0.0 | 3 | G3 |
| L2.3.5 | The cell rests on the floor or ribs. | inspection | `BOTTOM` within 0.3 above a printed surface | 1 | |
| L3.3.5.1 | Cell seat. | inspection | gap in [0, 0.3] | 1 | |

### L1.4 The battery cannot press on the charger board

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The swollen cell stays away from the board. | analysis | gap(V-SWELL, M-TP) ≥ 1.5 | 3 | G4 |
| L3.4.1.1 | Distance from the swell envelope to the charger board (PCB, receptacle, parts). | analysis | d ≥ 1.50 | 3 | G4 |
| L2.4.2 | No printed feature that touches the board is near the cell. | analysis | clear_of(CONTACT-SET, V-SWELL, 1.0) | 2 | |
| L3.4.2.1 | Board supports and stops clear of the swell envelope. | analysis | d ≥ 1.00 | 2 | |
| L2.4.3 | A printed wall stands between the cell and the board. | inspection | on the shortest line from V-SWELL to the PCB there is at least 0.8 of printed material, or the gap exceeds 5.0 | 1 | |
| L3.4.3.1 | Separating wall or gap. | inspection | wall ≥ 0.8 or gap > 5.0 | 1 | |

### L1.5 A USB-C cable plugs into the charger through one opening in the −X end wall with the lid on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Lid closed: the plug pushes in to full mate and pulls out without touching the box. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 | G2 |
| L3.5.1.1 | Plug envelope clear. | test | d ≥ 0.30 | 3 | G2 |
| L3.5.1.2 | Physical: print, close, plug in a real cable. | test | seats fully, 3 of 3 tries | 2 | physical, optional |
| L2.5.2 | The opening is not oversized. | analysis | inside(V-AP-USB, V-USB-PLUG grown 1.5 on each side, 0.0) | 2 | |
| L3.5.2.1 | Opening within the grown envelope. | analysis | d ≥ 0.0 (opening ≤ 15.4 × 9.5 and ≥ 13.0 × 7.1) | 2 | |
| L2.5.3 | Exactly one USB opening, in the −X wall. | inspection | V-AP-USB has 1 region of area > 1 mm³; no other wall passes the plug envelope | 2 | |
| L3.5.3.1 | Opening count in the −X wall. | inspection | 1 | 2 | |
| L2.5.4 | The port mouth is close to the wall's inner face. | inspection | `USB_MOUTH` lies 0.0-4.0 inside the −X wall's inner face | 2 | |
| L3.5.4.1 | Mouth depth behind the wall. | inspection | in [0.0, 4.0] | 2 | |

### L1.6 The slide switch's handle comes out through the +X end wall and can be operated with the lid on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | The handle moves through its whole travel without touching the box. | test | clear_of(ALL, V-SW-SWEEP, 0.3) | 3 | G5 |
| L3.6.1.1 | Handle sweep clear. | test | d ≥ 0.30 | 3 | G5 |
| L2.6.2 | One opening, not oversized. | analysis | V-AP-SW has 1 region; inside(V-AP-SW, V-SW-SWEEP grown 1.0 on each side, 0.0) | 2 | |
| L3.6.2.1 | Opening within the grown sweep. | analysis | d ≥ 0.0 (opening ≤ 8.5 × 5.0 and ≥ 7.1 × 3.6) | 2 | |
| L3.6.2.2 | Opening count in the +X wall. | inspection | 1 | 2 | |
| L2.6.3 | The handle stands proud of the outer face. | inspection | handle tip (4.0 above `BODY_TOP`) beyond the +X wall's outer face by 1.0-3.0 | 2 | |
| L3.6.3.1 | Handle protrusion. | inspection | in [1.0, 3.0] | 2 | |
| L2.6.4 | The switch body is held. | analysis | `play(M-SW body, Y)` and `play(M-SW body, Z)` ≤ 1.0 each; inward free travel (−X, lid on) ≤ 3.0; body fully inside V-CAVITY (touching walls allowed) | 2 | |
| L3.6.4.1 | Body play in the wall plane. | analysis | both ≤ 1.0 | 2 | |
| L3.6.4.2 | Inward travel and containment. | analysis | ≤ 3.0; inside d ≥ 0.0 | 2 | |

### L1.7 The lid is a snap fit: separate, removable by hand, and it stays on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Base and lid are separate single-shell bodies that do not interpenetrate. | analysis | BASE 1 shell; LID 1 shell; BASE ∩ LID ≤ 1.0 mm³ | 3 | G1 |
| L3.7.1.1 | One shell each. | analysis | `decompose()` count 1 per body | 3 | G1 |
| L3.7.1.2 | Closed overlap. | analysis | ≤ 1.0 mm³ | 3 | |
| L2.7.2 | A lip locates the lid with a sliding fit. | inspection | engagement ≥ 2.0; clearance 0.15-0.35 per side on all locating faces | 2 | |
| L3.7.2.1 | Lip-to-wall gap. | inspection | 0.15 ≤ gap ≤ 0.35 | 2 | |
| L3.7.2.2 | Lip engagement depth. | inspection | ≥ 2.0 | 1 | |
| L2.7.3 | At least two snap hooks hold the lid. | inspection | hooks ≥ 2; engagement (hook-to-catch overlap along the closing direction, measured in a section normal to the wall) 0.4-1.0; catch clearance 0.1-0.4; beam strain ε = 1.5·t·δ / L² ≤ 2.0 % with t = beam thickness, L = beam length, δ = engagement | 3 | |
| L3.7.3.1 | Hook count. | inspection | ≥ 2, on at least two different walls or two ends of one wall ≥ 20 apart | 2 | |
| L3.7.3.2 | Engagement and catch clearance. | inspection | engagement in [0.4, 1.0]; clearance in [0.1, 0.4] | 3 | |
| L3.7.3.3 | Beam strain. | analysis | ε ≤ 2.0 % | 2 | |
| L2.7.4 | No fasteners: no screw holes, bosses or loose parts (F5). | inspection | through holes in the lid: 0; screw bosses in the base: 0 | 1 | |
| L3.7.4.1 | Closure count. | inspection | 0 holes, 0 bosses | 1 | |
| L2.7.5 | The closed seam is tight and flush. | inspection | seam gap ≤ 0.5; outer-face step ≤ 0.5 on all four sides | 1 | |
| L3.7.5.1 | Seam gap and flushness. | inspection | as L2.7.5 | 1 | |
| L3.7.5.2 | Physical: hold the closed box upside down and shake; open and close 10 times by hand. | test | lid stays on; opens by hand; no cracking | 2 | physical, optional |

### L1.8 The box is closed except for the two openings, with 2-3 mm walls

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The only openings are the USB opening and the switch opening. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere into V-CAVITY | 2 | |
| L3.8.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 | |
| L2.8.2 | Outer walls, floor and lid plate are 2.0-3.0 thick (A8). | inspection | each median in [2.0, 3.0] | 2 | |
| L3.8.2.1 | Wall thickness (median over each wall away from features). | inspection | 2.0 ≤ t ≤ 3.0 | 2 | |
| L3.8.2.2 | Floor thickness. | inspection | 2.0 ≤ t ≤ 3.0 | 2 | |
| L3.8.2.3 | Lid plate thickness. | inspection | 2.0 ≤ t ≤ 3.0 | 2 | |
| L2.8.3 | At least 1.5 of material around every opening (to wall edges, the floor top, the seam and the other opening). | analysis | min ligament ≥ 1.5 | 1 | |
| L3.8.3.1 | Minimum ligament per opening. | analysis | ≥ 1.5 | 1 | |
| L2.8.4 | Walls join the floor; internal partitions are thick enough to print. | analysis | wall-to-floor contact ≥ 90 % of length × thickness; every partition and rib ≥ 0.8 | 2 | |
| L3.8.4.1 | Wall-to-floor contact. | analysis | ≥ 90 % | 2 | |
| L3.8.4.2 | Thinnest partition or rib. | analysis | ≥ 0.8 | 1 | |

### L1.9 Both parts print on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | In the stated orientation (F6) no unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12 in vertical walls and bridges ≤ 15.0 (the snap hooks and catches have 45° flanks). | analysis | 0 offending faces of area > 1 mm² | 2 | |
| L3.9.1.1 | Overhang and bridge scan per body. | analysis | as L2.9.1 | 2 | |
| L2.9.2 | Each body is manifold and one shell. | analysis | 1 shell; manifold3d accepts it | 3 | G1 |
| L3.9.2.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.9.3 | Each body rests on a flat face. | analysis | bed contact ≥ 50 % of the plan bounding box | 1 | |
| L3.9.3.1 | Bed contact per body. | analysis | ≥ 50 % | 1 | |
| L2.9.4 | No feature thinner than 0.8; mating gaps ≥ 0.15. | analysis | min thickness ≥ 0.8; min mating gap ≥ 0.15 | 1 | |
| L3.9.4.1 | Thin-feature and mating-gap scan. | analysis | as L2.9.4 | 1 | |
| L2.9.5 | Each body fits a 200 × 200 × 200 bed. | inspection | ≤ 200 per axis | 1 | |
| L3.9.5.1 | Bounding box per body. | inspection | ≤ 200 per axis | 1 | |

### L1.10 It is compact (closed outside size at most 70 × 60 × 25 mm) and stands flat

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Closed outside size (A9). | inspection | X ≤ 70.0, Y ≤ 60.0, Z ≤ 25.0; X > Y | 2 | |
| L3.10.1.1 | Assembly bounding box. | inspection | as L2.10.1 | 2 | |
| L2.10.2 | It stands on its base without tipping. | analysis | stable at 5° table tilt (mass 40 g at the cell's centroid plus the shell) | 1 | |
| L3.10.2.1 | Tilt stability. | analysis | centre of mass inside the support polygon at 5° in every direction | 1 | |
| L2.10.3 | Flat underside, nothing below the floor. | inspection | flatness ≤ 0.2; no protrusion below the floor | 1 | |
| L3.10.3.1 | Underside planarity. | inspection | as L2.10.3 | 1 | |

### L1.11 It can be assembled and wired with the lid off

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | The cell drops straight down into its pocket. | test | clear_of(BASE, V-INSTALL-CELL, 0.2) excluding the floor seat | 2 | |
| L3.11.1.1 | Cell drop-in path clear. | test | d ≥ 0.20 | 2 | |
| L2.11.2 | The charger board drops straight down onto its supports. | test | clear_of(BASE, V-INSTALL-TP, 0.1) excluding the support tops | 2 | |
| L3.11.2.1 | Board drop-in path clear. | test | d ≥ 0.10 | 2 | |
| L2.11.3 | The switch slides into its cradle with the handle through the slot. | test | clear_of(BASE, V-INSTALL-SW, 0.1) excluding the seat contact | 2 | |
| L3.11.3.1 | Switch insertion path clear. | test | d ≥ 0.10 | 2 | |
| L2.11.4 | The cell's leads can run from the tabs to the board. | analysis | V-WIRE-PATH connects `TABS` to at least 2 pads | 2 | |
| L3.11.4.1 | Wire passage exists (Ø2.0, voxel search). | analysis | connected to ≥ 2 pads | 2 | |

### L1.12 The package says what was built and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds `base.stl`, `lid.stl` (closed pose, box frame, mm), the OpenSCAD source, `layout.json` (F8) and the agent's own clearance report. | inspection | all present and readable | 3 | G0 |
| L3.12.1.1 | Files present and parse; each body's largest bounding-box axis in 20-200 mm. | inspection | true | 3 | G0 |
| L3.12.1.2 | The declared layout verifies under the seating rule (section 2.3). | analysis | PCB on support tops ≤ 0.10; cell bottom within 0.3 of its seat; switch body top within 0.5 of the +X wall | 3 | |
| L2.12.2 | The agent's own clearance report agrees with the judge. | analysis | for every `clear_of` / `inside` L3 the agent reports: same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 | |
| L3.12.2.1 | Self-report vs judge. | analysis | 100 % agreement within 0.10 | 1 | |

---

## 6. Counts and gates

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 48 |
| L3 | 65 (weight 3: 19, weight 2: 32, weight 1: 14; 2 physical or human, optional) |

Every L3 is a measurement a Python script can make on the delivered STL (or on the declared
`layout.json` against the catalogue), except the rows marked physical or human.

Gates (a failure makes a design WRONG regardless of score): see section 9.

---

## 7. Feasibility

One design exists that meets every L3 above (box frame, mm, outer min corner at the origin; the
battery pocket and the board strip sit side by side across Y, so the box is about 63 long):

- **Walls 2.4, floor 2.4 (Z 0-2.4), base wall top (seam) Z = 13.0, lid plate 2.0 (Z 13.0-15.0).**
  Outer size 62.8 × 58.6 × 15.0 (limit 70 × 60 × 25; X > Y). Cavity X 2.4-60.4, Y 2.4-56.2.
- **Cell pocket:** cell at X 2.9-52.9, Y 2.9-36.9, Z 2.4-7.4 (tabs on +X). Side clearance 0.5 on −X,
  −Y and +Y (the pocket's −Y wall is the outer wall, its +Y wall a partition Y 37.4-38.6, 1.2
  thick, up to Z 7.4, so 5.0 above the floor). `V-TAB`: X 52.9-59.9, Y 14.9-24.9, Z 4.15-5.65,
  free (the +X wall's inner face is at 60.4). Lid hold-down posts over the cell end at Z 8.4, 0.5
  above `SWELL_TOP` (7.9).
- **Charger board:** PCB X 3.8-29.8, Y 38.9-55.9, bottom at Z 5.0 on two rails along its long
  edges (Y 38.9-40.1 and 54.7-55.9, X 3.8-21.0, tops at Z 5.0, 2.6 above the floor, each 20 mm²
  under the PCB). The pad end (X 24.8-29.8) has nothing above or below it. Stops leave 0.3 on
  each side: the partition (Y 38.6) and the +Y wall (inner face Y 56.2) in Y; −X stops at X 2.4-3.5
  on the two flanks beside the receptacle (Y 38.9-42.0 and 52.6-55.9); +X stops at X 30.1-31.3,
  Y 38.9-40.1 and 54.7-55.9. Lateral play 0.6 per axis. Lid hold-down posts over the PCB flanks
  (Y 39.0-41.0 and Y 53.8-55.8, X 14-16) end at Z 8.1 (PCB top 6.0, keep-out top 7.8, plus 0.3), so the lift is
  2.1 (≤ 4.0).
- **Separation:** cell swell envelope Y ≤ 36.9, PCB Y ≥ 38.9: gap 2.0 (≥ 1.5); the 1.2 partition
  stands between them; the rails (Y ≥ 38.9) are 2.0 from `V-SWELL` (≥ 1.0).
- **USB-C:** `USB_MOUTH` at X 2.8 (0.4 inside the wall's inner face), Y 47.4, Z 7.63. Opening in the
  −X wall: Y 40.9-53.9 (13.0), Z 4.08-11.18 (7.1): the plug overmold 12.4 × 6.5 with 0.3 per
  side (oversize 0.3, limit 1.5). Ligaments: floor top 4.08 − 2.4 = 1.68, seam 13.0 − 11.18 =
  1.82, corner 4.7 (all ≥ 1.5). The overmold's front face is at X 1.8, inside the wall's
  thickness, and the stops (X ≥ 2.4) are 0.6 behind it.
- **Switch:** body X 54.7-60.2 (top 0.2 from the +X inner face), Y 41.15-53.65, Z 4.0-10.0, on a
  cradle (floor block to Z 4.0, side ribs 0.25 from the body; open toward −X); handle tip at X
  64.2, 1.4 beyond the outer face 62.8. Slot in the +X wall: Y 43.85-50.95 (7.1), Z 5.2-8.8 (3.6),
  i.e. the 6.5 × 3.0 sweep with 0.3 per side (oversize 0.3, limit 1.0). Ligament to the floor top
  2.8. A lid post (X 51.0-52.0, Y 41-53, Z 9-13) stands 2.7 behind the body's back face (X 54.7):
  inward travel 2.7 (≤ 3.0). The insertion path along −X is free of base material.
- **Wires:** the partition ends at X 52.9; X 52.9-60.4 is open and the cavity above the switch
  (Z > 10) is free, so a Ø2.0 wire runs from `TABS` (56.9, 19.9, 4.9) to the pads at (27.8, 40.9,
  5.0) and (27.8, 53.9, 5.0), straight-line 35.9 and 44.8 (≤ 50).
- **Snap:** lip 1.2 thick and 3.0 deep (Z 10-13), 0.25 inside the walls (fit 0.25 per side). Three
  hooks: one on the +X wall (Y 29-37) and two on the +Y wall (X 34-42 and X 44-52, each 8 wide),
  where nothing stands inside. Each hook is an arm
  descending from the lip to Z 5.0 (beam length 8.0, thickness 1.2, width 8) with a bead 0.6 past
  the wall's inner face into a blind recess 0.8 deep (45° flanks, catch clearance 0.2). Strain
  ε = 1.5 × 1.2 × 0.6 / 8.0² = 1.69 % (≤ 2.0 %). The +X hook is 4+ clear of `V-TAB` in Y; the
  hooks sit on two different walls, 20+ apart (the +X hook to the nearer +Y hook is about 25).
- **Printability:** base open side up, lid outer face down (arms and posts point up, bead
  undersides are 45° flanks); every opening is a rectangle (widths 13.0 and 7.1 ≤ 15.0).

This sketch is one satisfiable design; it is not the only one and is never given to the agent.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 (`design.json`) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1-L2.1.5 | L3.1.1.1, L3.1.2.1-2, L3.1.3.1-2, L3.1.4.1, L3.1.5.1 | L1.1 | inspection | "USB-C plug ... through one end", "slide switch ... opposite end" |
| L1.2 | Board held, room, pads free | L2.2.1-L2.2.4 | L3.2.1.1, L3.2.2.1, L3.2.3.1-2, L3.2.4.1-2 | L1.2 | analysis | "TP4056 USB-C charger board (26 x 17 mm)" |
| L1.3 | Battery pocket | L2.3.1-L2.3.5 | L3.3.1.1, L3.3.2.1-2, L3.3.3.1, L3.3.4.1, L3.3.5.1 | L1.3 | analysis | "5 x 34 x 50 mm LiPo", "pocket with 0.5 mm side clearance" |
| L1.4 | Battery does not press the board | L2.4.1-L2.4.3 | L3.4.1.1, L3.4.2.1, L3.4.3.1 | L1.4 | analysis | "cannot press on the charger board" |
| L1.5 | USB-C access | L2.5.1-L2.5.4 | L3.5.1.1-2, L3.5.2.1, L3.5.3.1, L3.5.4.1 | L1.5 | test | "USB-C plug overmold (12.4 x 6.5 mm) must reach the port" |
| L1.6 | Switch access | L2.6.1-L2.6.4 | L3.6.1.1, L3.6.2.1-2, L3.6.3.1, L3.6.4.1-2 | L1.6 | test | "a slide switch" |
| L1.7 | Snap lid | L2.7.1-L2.7.5 | L3.7.1.1-2, L3.7.2.1-2, L3.7.3.1-3, L3.7.4.1, L3.7.5.1-2 | L1.7 | inspection | "the lid is a snap fit" |
| L1.8 | Protection | L2.8.1-L2.8.4 | L3.8.1.1, L3.8.2.1-3, L3.8.3.1, L3.8.4.1-2 | L1.8 | analysis | "box" (implied) |
| L1.9 | Printable | L2.9.1-L2.9.5 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1, L3.9.5.1 | L1.9 | analysis | "printed in PLA on an FDM printer" |
| L1.10 | Compact, stable | L2.10.1-L2.10.3 | L3.10.1.1, L3.10.2.1, L3.10.3.1 | L1.10 | analysis | "compact box" |
| L1.11 | Assembly and wiring | L2.11.1-L2.11.4 | L3.11.1.1, L3.11.2.1, L3.11.3.1, L3.11.4.1 | L1.11 | test | "tabs must have room to be wired" (implied service) |
| L1.12 | Evidence | L2.12.1-L2.12.2 | L3.12.1.1-2, L3.12.2.1 | L1.12 | inspection | needed by the judge |

## 9. Grading procedure for G15

`benchmarks/generalize/rubric.md` did not exist when this file was written, so this section is the design-specific rubric (units, frames, recipes, classes, defect reports). If a generic rubric.md appears later it governs generic rules; this section still governs everything specific to G15.

1. **Package gate (G0).** The files of the last L1 must exist and load. If a delivered STL is
   missing or unreadable, stop: verdict DOES NOT MEET, one defect on the G0 L3.
2. **Units.** Load each STL; the largest bounding-box axis of base.stl and lid.stl must be 20-200 mm
   (a thin axis is expected). If it looks like inches or metres record a defect, do not rescale.
3. **Normalise the frame** (section 1.1) with rotations by multiples of 90° and mirroring only;
   record the transform; never penalise it.
4. **Build the references independently** from `part.json` and the declared `layout.json`
   (sections 2 and 3), run the sanity checks, then verify the seating rule.
5. **Run every L3** in order. Record measured value, limit, signed margin (negative = fail),
   PASS / FAIL / UNVERIFIED / N/A. UNVERIFIED counts as FAIL; N/A only for physical tests (unless
   a print was made) and the closure/variant the design does not use.
6. **Look at renders after measuring**; they locate defects and catch what no L3 covers
   (observations; they never make a check pass).

**Classes.** WRONG = any gate fails. MINOR = no gate fails but a weight-3 L3 fails. CORRECT = no
gate fails and every weight-3 L3 passes. **MEETS** = CORRECT and every applicable non-physical L3
of weight 1 and 2 passes; anything else is DOES NOT MEET. Also report the weighted score
Σ(weight × pass) / Σ(weight) over applicable L3s and the worst normalised margin among weight-3
L3s (margin ÷ the criterion's tolerance, or ÷ 0.5 mm for one-sided limits).

Gates: G0 package (L3.12.1.1); G1 manifold, one shell per body, two bodies (L3.9.2.1, L3.7.1.1); G2 USB-C plug seats (L3.5.1.1); G3 battery pocket and tab zone (L3.3.1.1, L3.3.2.1, L3.3.4.1); G4 battery clear of the charger board (L3.4.1.1); G5 switch handle operable through its opening (L3.6.1.1).

**Precedence.** (1) The numbers in this requirements.md beat `part.json` wherever they differ: build
the reference from requirements.md and record a defect on the requirement the stale catalogue
data breaks, with where = the part.json field. (2) Plug-seating, fit and clearance checks outrank
anything about opening or feature size. (3) Designed contact is never interference (section 1.3).
(4) Never relax a criterion, never round in the design's favour beyond ε, never infer a pass from
a render. (5) A requirement that looks impossible or self-contradicting is reported as an
observation with its numbers and still graded as written.

**Where a defect is.** One entry per failed or UNVERIFIED L3, most severe first (gates, weight 3,
2, 1), with the fields: `req` (L3 with its L2 and L1), `status`, `body`, `feature` (by function
and SCAD name), `face` (surface, side, outward normal), `location` (mm, in the graded frame: a
point or a bounding box), `measured` / `limit` / `margin`, `reference` (the M- or V- object and its
datum), `render`, `evidence` (saved file such as `defect_<L3>.stl`), `needed` (the geometric target
as numbers, never "use a difference()"). Coordinates come from measurement, not from the SCAD
source. Group L3s that fail for one geometric reason under the first and list the rest in
`also_fails`. Render-only findings are observations, listed apart.

Never open or use `benchmarks/heldout.json`.

## Audit

Adversarial audit of this entry, 2026-10-24. Recomputed from the part files and the section 7 sketch:
tab zone 7.0 × 10.0 × 1.5 at X 52.9-59.9, Y 14.9-24.9, Z 4.15-5.65; opening 13.0 × 7.1 = 12.4 × 6.5 plus
0.3 per side; slot 7.1 × 3.6 = 6.5 × 3.0 plus 0.3; handle tip 64.2 against the outer face 62.8 (1.4
proud); strain 1.5 × 1.2 × 0.6 / 8.0² = 1.69 %; swell gap 2.0 and 0.5 above `SWELL_TOP`; wire distances
35.9 and 44.8 against 50.0; outer 62.8 × 58.6 × 15.0. The sketch satisfies every gate and L3 once fix 1
is applied. All catalogue ids load (`parts.gate`). L1 count 12; L2 48, L3 65 with weights 19 / 32 / 14.

| # | Finding | Fix |
|---|---|---|
| 1 | Contradiction between L2.4.2 and the sketch. CONTACT-SET was "printed material within 0.3 of the PCB". The pocket partition (Y 37.4-38.6) and the +Y wall stand exactly 0.3 from the PCB edge, so they fell in the set, and `clear_of(CONTACT-SET, V-SWELL, 1.0)` failed: the partition is 0.5 from the swell envelope. The partition cannot be 1.0 away because it must separate cell and board (L2.4.3) and keep 0.5 side clearance (L2.3.1). L1.4 ("nothing that holds the board") had the same problem. | CONTACT-SET redefined as supports under, hold-downs over and free-standing stops beside the PCB; the pocket partition and outer walls are structure and excluded. L1.4 in `design.json` now reads "no support, hold-down or stop of the board" and names the partition's 0.8 mm / 5 mm rule. |
| 2 | Judge-needed numbers appeared only in L2/L3: at least two supports (L1.2), pocket wall at least 3 mm high (L1.3), mouth at most 4 mm behind the wall (L1.5), switch body held within 1.0 sideways and 3.0 inward (L1.6), lip engagement 2 mm, catch clearance 0.1-0.4 and strain 2 % (L1.7), tilt 5 degrees (L1.10). | Added to the matching L1 texts in `design.json`. |
| 3 | A9 pointed at "the tight layout of F3", but F3 is the closure decision. | Now "the layout of section 7". |
| 4 | Section 7 named hold-down posts "over the PCB flanks" with only one Y range. | Both flanks given: Y 39.0-41.0 and Y 53.8-55.8. |
| 5 | Catalogue lookups: "LiPo cell", "TP4056 USB-C charger board", "slide switch" and "USB-C plug" each rank the intended part first. | None needed. |
| 6 | Hidden numbers that live in part files or `design_rules.json` (tab zone, swell 10 %, wire zones, keep-out heights, sliding fit, ligament 1.5, overhang rules) agree with them. | None needed. |

Observation: the switch handle height (4.0, assumed, +/- 1.0) fixes the proud range (L2.6.3) only with the
2.4 mm wall; with a 2.0 mm wall it is 2.0 proud, still within 1.0-3.0.

