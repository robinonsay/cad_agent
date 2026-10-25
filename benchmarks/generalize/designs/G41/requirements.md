# G41 Pico header soldering jig: requirements (L1 / L2 / L3)

A training entry of the generalization benchmark (`benchmarks/generalize/`), modelled on E1-01
(`benchmarks/enclosure/requirements.md`). The machine-readable request (L1 only, `dev.json` format) is
`design.json` next to this file. This file holds the L2/L3 tree, the reference models, the assumptions, the fixed decisions, a feasibility sketch, the traceability and the design-specific judging rules (section 8). Catalogue parts:
`benchmarks/enclosure/parts/` (`rpi_pico2`, `header_male_2p54`, `perfboard`). No number here may appear in agent logic: they live in the request, this file, `design_rules.json` generic values and `part.json` data.

**Request (plan brief, verbatim):** "A jig that holds two 20-pin male headers vertical (2.54 mm pitch, 17.78 mm between rows) while I solder a Pico onto them. Pin guide holes are 1.0 mm and the Pico rests on a shelf at the correct standoff height. The jig also has a 70 x 50 perfboard cradle."

**Expanded request** (the text the agent gets, `design.json`): A soldering jig for a Raspberry Pi Pico 2. It holds two 20-pin male headers (2.54 mm pitch, 17.78 mm between the rows) vertical, long pin tails down, while I solder the Pico onto them: the pin guide holes are 1.0 mm, the headers' plastic spacers sit on a flat seat, and the Pico drops on from above onto the pins and rests on a shelf at the right standoff height (the height of the header spacer) with a little room to lift it off afterwards. The jig also has a cradle for a 70 x 50 mm perfboard (1.6 mm thick), a pocket where the board lies flat, with finger notches to lift it out. The jig is one piece printed on an FDM printer in PLA without supports, and I must be able to get a soldering iron to every pin from above.

**How to read this.** L1 says what the owner needs; L2 turns it into an engineering requirement with numbers; L3 is a concrete check Python can run on the delivered STL. Each row has a method, a pass/fail criterion with a number and tolerance, a weight (3 critical, 2 major, 1 minor) and, for must-pass rows, a gate mark. Numbers that come from an assumption (section 3) are provisional until Robin confirms them. Do not relax a criterion because a design fails it.

---

## 1. Frames, tolerances and the interference checks

### 1.1 Frames

- **Jig frame:** Z up, the jig's underside at Z = 0 (the print bed), X along the header rows and the 70 mm side of the cradle. The **seat plane** (Z_s) is the plane of the header spacer bottoms, declared in `layout.json`. A jig delivered rotated by 90° multiples or mirrored is normalised into this frame before grading (rubric step 3).
- **Header frame:** the catalogue frame of `header_male_2p54`: origin at pin 0 on the spacer bottom, pins along +X, spacer centred on Y = 0; in the jig the pin tails point −Z (down), as the catalogue `PINS` datum.
- **Pico frame:** the catalogue module frame of `rpi_pico2`: origin at the PCB min corner, PCB bottom at Z = 0 (in the jig, at Z_s + 2.5), components on +Z, USB end at −X.

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within ε (a "≥ 0.50" limit passes at 0.48) |
| angle | 0.5° | same |
| interference volume | 0.01 mm³ | "no interference" means intersection volume ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the hole's section (what a screw or pin sees) | |
| boss / standoff / stem OD | smallest enclosing circle of the section | |
| fitted circle (a bore) | least-squares circle through the section points of the arc | |

Where a criterion is written "nominal ± t", t is the design tolerance and ε is added to it.

### 1.3 The two interference checks

Fit, access and clearance requirements are written, wherever possible, as one of two checks
against named reference models (M-) and envelope volumes (V-) from section 2. The grader runs
its own implementation (section 8); a design may and should generate the same volumes for its own
checks, but its copies are not trusted for grading.

- **`clear_of(bodies, volume, clearance)`**: the minimum Euclidean distance between every printed
  body in `bodies` and `volume` is ≥ `clearance`. Reported value: the signed minimum distance d
  (negative = the body penetrates the volume; the penetration volume is reported too). Pass:
  penetration ≤ 0.01 mm³ and d ≥ clearance − ε.
- **`inside(volume, cavity, clearance)`**: `volume` lies entirely in `cavity`, and every point of it
  is ≥ `clearance` from the cavity's boundary. Pass: d ≥ clearance − ε.

**Designed contact is not interference (Robin's rule, 2026-10-24).** Parts that are meant to touch
are excluded from every interference and clearance check. For this design the designed-contact
pairs are:
- a header's spacer bottom on the seat plane
- a header pin in its guide hole (a clearance fit: the pin envelope must not penetrate the hole walls; the radial slack is (Ø − 0.905)/2)
- the Pico's underside on the shelf top and on the spacer tops
- a header pin through the Pico's hole (the Pico model carries the pin datums, not drilled holes: the pin ∩ PCB intersection is designed contact)
- the perfboard on the cradle floor

For these pairs only penetration counts (an intersection volume above 0.01 mm³, unless the pair
is given a larger allowance below). A distance of zero is a pass.

`bodies` is the jig (the only printed body); the reference parts are not printed.

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` in `benchmarks/enclosure/parts/<part_id>/`. The only place part numbers may live.
- **envelope**: a keep-out, sweep or access volume generated by Python from datums. Never drawn by hand.
- **computed**: derived from the design (holes, pocket, shelf).

### 2.2 Reference models (M-)

Positions are the **declared layout** (the sketch's values are in section 6); jig frame, mm.

| Name | What | Source | Size and pose | Datums |
|---|---|---|---|---|
| **M-HDR-A, -B** | 1 × 20 male header, long tails down | catalogue `header_male_2p54` (pins 20) | plastic spacer 50.8 × 2.5 × 2.5 (X, Y, Z); pins at 2.54 pitch from pin 0; spacer bottom on the seat plane Z_s; rows 17.78 apart in Y | `STACK_BOTTOM` (Z_s), `STACK_TOP` (Z_s + 2.5), `PINS` (40 axes in total) |
| **V-PIN-k** | the pin as a solid | derived (A4) | Ø0.905 (0.64 mm square, diagonal) × 6.0 below the spacer bottom (the long tail); 3.0 above the spacer top (the short end, through the Pico) | pin axis |
| **M-PICO2** | Raspberry Pi Pico 2 | catalogue `rpi_pico2` | PCB 51.0 × 21.0 × 1.0 at Z_s + 2.5 to Z_s + 3.5; USB receptacle 8.0 × 5.5 × 2.8 on top overhanging the −X edge by 1.3; pins `PINS_A/B` 1.37 from the PCB end, rows 17.78 apart | `PCB_BOTTOM`, `PCB_TOP`, `PINS_A`, `PINS_B`, `USB_MOUTH` |
| **M-PERF** | 70 × 50 perfboard | catalogue `perfboard` (70 × 50 specimen) | 70.0 × 50.0 × 1.6; lies on the cradle floor; four holes Ø2.0 (not used by the jig) | `PERF_TOP`, `PERF_BOTTOM` |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Definition (jig frame) |
|---|---|---|
| **V-PIN-k** (k = 1..40) | pin envelope in its hole | Ø0.905 cylinder, 6.0 long, below the spacer bottom on each pin axis |
| **V-PICO-INSTALL** | Pico drop | M-PICO2's solid (PCB and receptacle) swept straight down from 15 above its seat to the seat |
| **V-HDR-INSTALL-k** | header drop | M-HDR-k (spacer and the 6.0 tails) swept straight down from 15 above to the seat |
| **V-HDR-LIFT-k** | soldered lift-off | M-HDR-k with its pins swept straight up 15 from the seat |
| **V-SOLDER-ACCESS** | iron access | the Pico's PCB footprint grown 8.0 on every side, from the PCB top (Z_s + 3.5) up 25 |
| **V-PIN-COL-k** | one pin's top | Ø6.0 column on each pin axis from the PCB top up 25 |
| **V-BOARD** | perfboard proxy | 70.0 × 50.0 × 1.6 box on the cradle floor, centred in the pocket |
| **V-SEAT-FOOT-A, -B** | header footprints | the 50.8 × 2.5 rectangle of each spacer on the seat plane |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-PICO2, M-PERF | units and size | PCB 51.0 × 21.0 ± 0.2; board 70.0 × 50.0 × 1.6 ± 0.2 |
| R2 | M-PICO2 | pin pattern | `PINS_A/B` 20 each at 2.54 ± 0.02, rows 17.78 ± 0.05, 1.37 from the end |
| R3 | M-HDR | pitch, spacer height, rows | 2.54 ± 0.02; 2.5 ± 0.1; 17.78 ± 0.05 between the two headers' rows |
| R4 | M-PICO2 on M-HDR | pins coincide | each `PINS_A/B` axis within 0.05 of a header pin axis |
| R5 | every V- envelope | datums equal the model datums it came from | ≤ 0.01 |

**Seating rule.** The grader verifies the declaration: each header pin axis coaxial with a guide hole within 0.10 (least squares), the spacer bottoms on the seat plane (≤ 0.10), the Pico underside on the shelf (≤ 0.10). If the declaration is missing or fails, the headers are seated by the hole fit and the failing L3s stay failed.

---

## 3. Assumptions, fixed decisions and open questions

### 3.1 Assumptions (derived, with their uncertainty)

| # | Question | Value chosen | Why, and uncertainty |
|---|---|---|---|
| A1 | How are the headers held? | Long tails down in the 1.0 mm guide holes, spacer bottoms on a flat seat, short ends up through the Pico. | The usual way a jig holds a header while a board is soldered on; pins down is the catalogue `PINS` direction (−Z). Low uncertainty. |
| A2 | Which side is soldered? | The Pico's top: the short pin ends protrude 2.0 above it. | A Pico is soldered from the component side onto the pin tops. Medium uncertainty. |
| A3 | "Correct standoff height"? | The header spacer height: the Pico underside sits 2.5 above the seat plane, on the spacer tops and the shelf. | The same convention as E1-01 (A3). Low uncertainty. |
| A4 | Pin dimensions? | 0.64 mm square (diagonal 0.905); tail below the spacer 6.0, short end above 3.0 (an 11.5 mm header); the catalogue holds the spacer only. | Common 2.54 mm header (Samtec TSW class). ±1 mm on the tails; the hole depth ≥ 6.5 gives 0.5 margin. |
| A5 | Pico locating? | Walls round the PCB with 0.15 to 0.50 per side, up to 0.4 to 0.9 above the PCB underside (below the PCB top, so the USB receptacle overhang clears). | The pins locate the Pico; the walls only keep it square. |
| A6 | Shelf? | Between the header rows, at least 200 mm², top at the spacer height, 0.3 from the spacers, 0.5 from the pins. | Supports the Pico's middle so it does not rock on two thin spacers. |
| A7 | Cradle? | Pocket 0.3 bigger per side (0.2 to 0.4), depth 2.5 to 6.0, flat floor, two finger notches. | FDM sliding-fit convention; the board is 70.0 × 50.0 × 1.6 (E1-01 specimen). |
| A8 | Iron access? | Nothing above the Pico's top within 8.0 round it, 25 up. | A soldering iron tip needs a clear column and a lateral approach. |
| A9 | Printing? | FDM, PLA, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed, seat plane up; overhang limit 45°; bridges ≤ 15; Ø1.0 vertical holes exempt as round holes. | Common printers. Ø1.0 holes print marginally; the band 0.95 to 1.10 allows for it. |
| A10 | Size? | ≤ 100 × 90 × 20. | A tight jig is 78.6 × 84.2 × 13.3 (section 6). |
| A11 | Mass? | Jig plus loaded parts 120 g. | Stability check only. |

### 3.2 Fixed decisions (a choice that would otherwise be ambiguous)

| # | Decision |
|---|---|
| F1 | The jig is one printed body (the Pico zone and the cradle are zones of the same piece). |
| F2 | The headers are loaded before the Pico, from above; the Pico drops on straight down and lifts off straight up. |
| F3 | The shelf height is the catalogue spacer height; the pin tail length is declared in `layout.json`. |
| F4 | The Pico lies along X with its USB end at −X, as in the catalogue frame. |
| F5 | The cradle's board is the perfboard of the catalogue (70 × 50 specimen); the jig does not use its holes. |

---

## 4. Requirements tree

### L1.1 Layout declared: two headers, the Pico on them, the perfboard in its cradle

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares the pose of both headers, the Pico and the perfboard (catalogue id, position, orientation) in the jig frame. | inspection | `layout.json` present, parses, names two `header_male_2p54` (pins 20), `rpi_pico2`, the 70 × 50 `perfboard`, with the seat plane Z | 3 |  |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | parse errors = 0; unknown ids = 0; header entries = 2 | 3 | G0 |
| L2.1.2 | The two headers are parallel rows on the Pico's pin pattern: pins at 2.54 pitch along X, rows 17.78 apart in Y, pins vertical. | inspection | row spacing 17.78 ± 0.05; pitch 2.54 ± 0.02; pin axes within 0.5° of vertical; 20 pins each | 3 |  |
| L3.1.2.1 | Row spacing and pitch of the declared headers. | inspection | 17.78 ± 0.05; 2.54 ± 0.02 | 3 | G2 |
| L2.1.3 | The Pico sits on the headers: each of its 40 pin positions (`PINS_A`, `PINS_B`) coincides with a header pin axis, its PCB underside rests on the header spacer tops, and it lies along X. | analysis | `PINS_A/B` axes within 0.15 of the header pin axes; Pico underside plane within 0.05 of the spacer tops; Pico long axis within 0.5° of X | 3 |  |
| L3.1.3.1 | Pico pins on header pins. | analysis | max residual ≤ 0.15 | 3 | G4 |
| L3.1.3.2 | Pico height on the spacers. | analysis | ≤ 0.05 | 2 |  |
| L2.1.4 | No two reference parts collide, and the perfboard lies in the cradle, not over the Pico zone. | analysis | pairwise intersection of headers, Pico, perfboard ≤ 0.01 mm³ (pins through the Pico's holes are designed contact); perfboard plan outline disjoint from the Pico's by ≥ 3.0 | 2 |  |
| L3.1.4.1 | Pairwise interference of the reference parts. | analysis | each pair ≤ 0.01 mm³ | 2 |  |

### L1.2 Pin guide holes: 2 rows of 20 holes of 1.0 mm on the header pattern

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Exactly 40 round guide holes, Ø 1.0 (−0.05, +0.10) (inscribed circle, what a pin sees). | inspection | count = 40; each Ø in [0.95, 1.10] | 3 |  |
| L3.2.1.1 | Guide-hole count. | inspection | 40 | 3 | G2 |
| L3.2.1.2 | Guide-hole diameter (each). | inspection | 0.95 to 1.10 | 3 | G2 |
| L2.2.2 | The holes are on the header pin pattern: two rows of 20, 2.54 pitch, 17.78 apart. | inspection | hole axes within 0.10 of the declared header pin axes; row spacing 17.78 ± 0.05; end-to-end distance 48.26 ± 0.10 | 3 |  |
| L3.2.2.1 | Hole-to-pin axis residual. | analysis | max ≤ 0.10 | 3 | G2 |
| L3.2.2.2 | Row spacing of the holes. | inspection | 17.78 ± 0.05 | 3 | G2 |
| L3.2.2.3 | Pitch along each row. | inspection | 2.54 ± 0.03 between neighbours; end-to-end 48.26 ± 0.10 | 3 | G2 |
| L2.2.3 | The holes are deep enough for the pin tails: depth at least the 6.0 tail plus 0.5. | inspection | depth from the seat plane ≥ 6.5 (blind, or through) | 3 |  |
| L3.2.3.1 | Guide-hole depth. | inspection | ≥ 6.5 | 3 | G2 |
| L2.2.4 | The holes are open and straight: a pin envelope Ø0.905 × 6.0 below each spacer bottom fits in its hole. | analysis | clear_of(jig, V-PIN-k, 0.0) for k = 1..40 | 3 |  |
| L3.2.4.1 | Pins fit their holes. | analysis | d ≥ 0.0 for all 40 | 3 | G2 |

### L1.3 Headers held vertical on a flat seat

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The spacer bottoms rest on a seat plane: one plane under both headers, flat, covering the spacer footprints. | inspection | seat flatness ≤ 0.10 over each 50.8 × 2.5 footprint; the two seats coplanar within 0.10; seat area under each spacer ≥ 90% | 3 |  |
| L3.3.1.1 | Seat flatness and coplanarity. | inspection | ≤ 0.10; ≤ 0.10 | 3 | G3 |
| L3.3.1.2 | Seat coverage under the spacers. | analysis | ≥ 90% | 2 |  |
| L2.3.2 | The headers cannot lean more than 2° in the holes. | analysis | tilt bound = atan((Ø_hole,max − 0.905) / min(depth, 6.0)) over the measured holes ≤ 2.0° | 2 |  |
| L3.3.2.1 | Header tilt bound. | analysis | ≤ 2.0° | 2 |  |
| L2.3.3 | The spacers touch only the seat: the headers stand without pressing on the shelf or the walls. | analysis | header spacer ∩ jig ≤ 0.01 mm³; spacer distance to shelf side and locating walls ≥ 0.3 | 2 |  |
| L3.3.3.1 | Spacer clearance to the shelf and the walls. | analysis | d ≥ 0.30 (the seat contact is designed contact) | 2 |  |

### L1.4 Shelf at the correct standoff height

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The shelf top is one flat plane at the spacer height above the seat plane. | inspection | shelf top − seat plane = 2.5 ± 0.10; flatness ≤ 0.10 | 3 |  |
| L3.4.1.1 | Shelf height above the seat plane. | inspection | 2.5 ± 0.10 (+ε) | 3 | G3 |
| L3.4.1.2 | Shelf flatness. | inspection | ≤ 0.10 | 2 |  |
| L2.4.2 | The shelf is under the Pico, between the header rows, big enough to carry it, clear of the spacers and the pins. | analysis | shelf plan area ≥ 200 mm²; shelf outline inside the Pico's PCB footprint and between the rows; distance to the spacers ≥ 0.3 and to every pin axis ≥ 0.5 | 3 |  |
| L3.4.2.1 | Shelf area and position. | inspection | ≥ 200 mm²; inside the footprint | 2 |  |
| L3.4.2.2 | Shelf clearance to spacers and pins. | analysis | ≥ 0.3; ≥ 0.5 | 3 |  |
| L2.4.3 | The Pico rests level: its underside touches the shelf and the spacer tops, and the shelf supports it within 0.1 of the spacer tops. | analysis | Pico underside to shelf top gap ≤ 0.10 in the seated pose; Pico tilt ≤ 0.5° | 3 |  |
| L3.4.3.1 | Pico on the shelf. | analysis | gap ≤ 0.10 | 3 | G3 |

### L1.5 Pico located and free to lift off

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Locating walls round the PCB: on all four sides, clearance 0.15 to 0.5 per side, low enough not to touch the USB receptacle overhang. | inspection | wall faces on four sides; clearance to the PCB edge 0.15 to 0.50 on each side; wall top 0.4 to 0.9 above the PCB underside; clear_of(jig, receptacle, 0.2) | 3 |  |
| L3.5.1.1 | Clearance on each side of the PCB. | inspection | 0.15 to 0.50 (each of 4 sides) | 3 | G4 |
| L3.5.1.2 | Locating wall top height. | inspection | 0.4 to 0.9 above the Pico underside | 2 |  |
| L3.5.1.3 | Wall clearance to the USB receptacle. | analysis | d ≥ 0.20 | 2 |  |
| L2.5.2 | Dropping on: the Pico's solid swept straight down 15 to its seat touches nothing until it lands on the shelf and spacers. | test | clear_of(jig, V-PICO-INSTALL, 0.0), the shelf and spacer contact at the end excluded | 3 |  |
| L3.5.2.1 | Pico installation path. | test | d ≥ 0.0 | 3 | G4 |
| L2.5.3 | Lifting off: the Pico, with the soldered headers, lifts straight up: the pin tails leave the holes without catching. | test | V-HDR-LIFT-k (each header with its pins swept 15 up): clear_of(jig, sweep, 0.0) excluding the pins in their holes | 2 |  |
| L3.5.3.1 | Soldered assembly lift-off. | test | d ≥ 0.0 | 2 |  |
| L2.5.4 | The headers drop into the holes from above before the Pico goes on. | test | V-HDR-INSTALL-k (header with pins swept from 15 above to seat): clear_of(jig, sweep, 0.0), seat contact excluded | 2 |  |
| L3.5.4.1 | Header installation path. | test | d ≥ 0.0 | 2 |  |

### L1.6 A soldering iron reaches every pin from above

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | The zone above the Pico and 8 mm round it, from the PCB top up 25, is free of the jig. | test | clear_of(jig, V-SOLDER-ACCESS, 0.0) | 3 |  |
| L3.6.1.1 | Solder-access zone clear. | test | d ≥ 0.0 | 3 | G4 |
| L2.6.2 | The pin tips stand clear above the PCB top: the jig does not hide the pins' upper 2.0. | analysis | jig ∩ (Ø6.0 column on each pin axis from the PCB top up 25) ≤ 0.01 mm³ | 2 |  |
| L3.6.2.1 | Pin columns clear. | analysis | ≤ 0.01 mm³ for all 40 | 2 |  |

### L1.7 Perfboard cradle: a 70 x 50 pocket where the board lies flat

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The pocket is rectangular, 0.3 bigger than the board on every side, with a flat floor. | inspection | pocket 70.6 ± 0.2 × 50.6 ± 0.2 (clearance 0.2 to 0.4 per side); floor flatness ≤ 0.2; floor area continuous (no hole wider than 3.0) | 3 |  |
| L3.7.1.1 | Pocket size. | inspection | 70.6 ± 0.2 × 50.6 ± 0.2 (+ε) | 3 | G5 |
| L3.7.1.2 | Clearance per side. | inspection | 0.2 to 0.4 on all four sides | 2 | G5 |
| L3.7.1.3 | Floor flatness. | inspection | ≤ 0.2 | 2 |  |
| L2.7.2 | The pocket is deep enough to retain the board and shallow enough to reach in. | inspection | depth in [2.5, 6.0] (board 1.6 plus at least 0.9) | 3 |  |
| L3.7.2.1 | Pocket depth. | inspection | 2.5 to 6.0 | 3 | G5 |
| L2.7.3 | The board lies in the pocket without touching the walls and sits flat on the floor. | demonstration | a 70.0 × 50.0 × 1.6 box centred in the pocket on the floor: ∩ jig ≤ 0.01 mm³ (the floor contact is designed contact); gap to walls ≥ 0.2 | 3 |  |
| L3.7.3.1 | Board proxy in the cradle. | demonstration | proxy ∩ jig ≤ 0.01 mm³ (floor contact excluded); gap to every wall ≥ 0.2 | 3 | G5 |
| L2.7.4 | Finger notches let the board be lifted out: at least two, each at least 10 wide, reaching at least 2.0 beyond the pocket outline down to the floor, with a ligament of at least 1.0 left outside. A notch is part of the cradle for L2.8.1, so a notch in the wall facing the Pico zone must also keep 3.0 from the Pico-zone features. | inspection | count ≥ 2 on opposite walls; width ≥ 10.0; reach ≥ 2.0; floor depth reached; outside ligament ≥ 1.0 | 2 |  |
| L3.7.4.1 | Notch count, width and reach. | inspection | ≥ 2; ≥ 10.0; ≥ 2.0 | 2 |  |
| L3.7.4.2 | Notch outside ligament. | analysis | ≥ 1.0 | 2 |  |

### L1.8 Zones apart and walls thick enough

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The Pico zone and the cradle do not overlap and are separated by a wall. | analysis | distance between the cradle pocket and the nearest Pico-zone feature (locating wall, shelf, hole) ≥ 3.0 | 3 |  |
| L3.8.1.1 | Zone separation. | analysis | ≥ 3.0 | 3 |  |
| L2.8.2 | Material round the cradle and under the pocket floor. | analysis | wall round the pocket ≥ 2.0 (except at the notches, ≥ 1.0); material under the floor ≥ 2.0 | 2 |  |
| L3.8.2.1 | Cradle walls. | analysis | ≥ 2.0 | 2 |  |
| L3.8.2.2 | Material under the cradle floor. | analysis | ≥ 2.0 | 2 |  |
| L2.8.3 | The guide holes keep material between them and round the zone. | analysis | ligament between neighbouring holes ≥ 0.8 (pitch 2.54 − Ø); to the plate edge ≥ 2.0; plate thickness at the seat ≥ guide-hole depth + 1.0 | 2 |  |
| L3.8.3.1 | Hole ligaments. | analysis | ≥ 0.8; ≥ 2.0; plate thickness ≥ depth + 1.0 | 2 |  |

### L1.9 One piece that prints without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The jig is one connected body, manifold. | analysis | 1 shell; manifold3d accepts it | 3 |  |
| L3.9.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.9.2 | In its stated print orientation (default: seat plane up) no part has an unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12.0 and bridges ≤ 15.0. | analysis | 0 offending faces (area > 1 mm²) | 2 |  |
| L3.9.2.1 | Overhang and bridge scan. | analysis | 0 faces steeper than 45° with area > 1 mm²; every bridge ≤ 15.0; every round hole Ø ≤ 12.0 | 2 |  |
| L2.9.3 | The jig rests on a flat underside. | analysis | bed contact ≥ 80% of the plan bounding box; underside flatness ≤ 0.2 | 1 |  |
| L3.9.3.1 | Bed contact. | analysis | ≥ 80% of the plan bounding box; underside flatness ≤ 0.2 | 1 |  |
| L2.9.4 | No feature thinner than 0.8 (the locating walls included); fits a 200 × 200 × 200 build volume. | analysis | min thickness ≥ 0.8; bounding box ≤ 200 | 1 |  |
| L3.9.4.1 | Thin-feature scan and bounding box. | analysis | min thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 |  |

### L1.10 Compact and stable on the bench

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Outside size. | inspection | X ≤ 100.0, Y ≤ 90.0, Z ≤ 20.0 | 1 |  |
| L3.10.1.1 | Bounding box. | inspection | X ≤ 100.0, Y ≤ 90.0, Z ≤ 20.0 | 1 |  |
| L2.10.2 | It stands on its underside without tipping, also with the Pico and the board loaded. | analysis | stable at 10° tilt; centre of mass (jig plus Pico, headers and board, 120 g total) inside the support polygon | 1 |  |
| L3.10.2.1 | `stable` at 10°. | analysis | centre-of-mass projection inside the support polygon with margin ≥ 0.0 mm at 10° tilt | 1 |  |

### L1.11 Datum pose is derivable: Pico height above the seat matches the header spacer

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | The shelf height equals the catalogue spacer height. | analysis | shelf top − seat = `header_male_2p54` `spacer_height` (2.5) ± 0.10 | 3 |  |
| L3.11.1.1 | Shelf height versus the catalogue spacer height. | analysis | \|difference\| ≤ 0.10 | 3 | G3 |
| L2.11.2 | The pin tail length used for the hole depth is stated in the layout and agrees with the catalogue assumption. | inspection | `layout.json` states the tail length used; hole depth ≥ tail + 0.5 | 1 |  |
| L3.11.2.1 | Stated tail length and depth. | inspection | depth ≥ tail + 0.5 | 1 |  |

### L1.12 Package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds `jig.stl` (mm), the `.scad` source, `layout.json` (poses, seat plane, tail length, print orientation) and `report.json` (the agent's own checks). | inspection | all present and readable; the STL's largest bounding-box axis within 20 to 200 | 3 |  |
| L3.12.1.1 | Files present and parse; units are mm. | inspection | 4 of 4 files present; the STL's largest bounding-box axis within 20 to 200 | 3 | G0 |
| L3.12.1.2 | The declared layout verifies under the seating rule. | analysis | pin axes coaxial with holes ≤ 0.10; spacer bottoms on the seat ≤ 0.10; Pico underside on the shelf ≤ 0.10 | 3 |  |
| L2.12.2 | The agent's own clearance report agrees with the judge's measurements. | analysis | for every clear_of / inside L3 the agent reports, same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 |  |
| L3.12.2.1 | Self-report versus judge. | analysis | 100% agreement within 0.10 | 1 |  |

---

## 5. Counts

| Level | Count |
|---|---|
| L1 | 12 |
| L2 | 37 |
| L3 | 51 (weight 3: 25, weight 2: 20, weight 1: 6; total weight 121) |


Gates (a failure makes a design WRONG regardless of score; section 8): **G0** package (L3.1.1.1, L3.12.1.1); **G1** manifold, one body (L3.9.1.1); **G2** guide holes: 40, Ø, pattern, depth, fit (L3.1.2.1, L3.2.1.1, L3.2.1.2, L3.2.2.1, L3.2.2.2, L3.2.2.3, L3.2.3.1, L3.2.4.1); **G3** seat flat and shelf at the spacer height (L3.3.1.1, L3.4.1.1, L3.4.3.1, L3.11.1.1); **G4** Pico seats, installs and can be soldered (L3.1.3.1, L3.5.1.1, L3.5.2.1, L3.6.1.1); **G5** perfboard cradle fits the board (L3.7.1.1, L3.7.1.2, L3.7.2.1, L3.7.3.1).

---

## 6. Feasibility: a design that meets every number

A concrete design in the jig frame, checked with a `manifold3d` model (one shell; the headers, Pico, pins, board proxy, soldering zone all clear; Pico on the shelf; receptacle 0.2 above the locating walls).

| Feature | Value |
|---|---|
| Plate | X 0 to 78.6, Y 0 to 84.2, Z 0 to 10.0; seat plane Z_s = 10.0 |
| Pico zone | PCB footprint X 12.8 to 63.8, Y 60.9 to 81.9; PCB underside Z 12.5 (Z_s + 2.5) |
| Guide holes | 40 × Ø1.0 on the pin axes (X = 14.17 + 2.54·i, Y = 62.51 and 80.29), from Z 10.5 down to Z 2.0 (depth 8.0); pin envelope Ø0.905 gap 0.047 |
| Shelf | X 16.8 to 59.8, Y 64.26 to 78.54 (43 × 14.28 = 614 mm²), Z 10.0 to 12.5 (2.5 high); 0.5 from the spacers |
| Locating ring | pocket X 12.5 to 64.1, Y 60.6 to 82.2 (0.30 per side), ring 2.0 thick, top Z 13.3 (0.8 above the Pico underside); receptacle 0.20 above the ring |
| Cradle | pocket X 4.0 to 74.6, Y 4.0 to 54.6 (70.6 × 50.6, 0.30 per side), floor Z 6.0 (depth 4.0), walls 4.0; two notches 12 wide centred at Y 29.3 (Y 23.3 to 35.3), one in each short end wall (X 0 to 4.0 and 74.6 to 78.6), reaching 2.5 into the wall down to the floor Z 6.0 (1.5 left outside); the notches are far from the Pico zone, so L2.8.1 is untouched |
| Divider | 4.0 between the cradle and the Pico zone (Y 54.6 to 58.6) |
| Size | 78.6 × 84.2 × 13.3 (limit 100 × 90 × 20) |
| Checks | headers and Pico no intersection; soldering zone clear; Pico gap to the shelf 0; board proxy in the cradle clear |
| Print | seat plane up, flat underside (bed contact 100%); the guide holes are vertical blind Ø1.0 (round holes, exempt) |

---

## 7. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 (design.json) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout declared: two headers, the Pico on them, the perfboard in its cradle | L2.1.1 to L2.1.4 | L3.1.1.1, L3.1.2.1, L3.1.3.1, L3.1.3.2, L3.1.4.1 | L1.1 | inspection | "two 20-pin male headers vertical (2.54 mm pitch, 17.78 mm between rows)", "a Pico onto them", "a 70 x 50 perfboard cradle" |
| L1.2 | Pin guide holes: 2 rows of 20 holes of 1.0 mm on the header pattern | L2.2.1 to L2.2.4 | L3.2.1.1, L3.2.1.2, L3.2.2.1, L3.2.2.2, L3.2.2.3, L3.2.3.1, L3.2.4.1 | L1.2 | inspection | "Pin guide holes are 1.0 mm" |
| L1.3 | Headers held vertical on a flat seat | L2.3.1 to L2.3.3 | L3.3.1.1, L3.3.1.2, L3.3.2.1, L3.3.3.1 | L1.3 | analysis | "holds two 20-pin male headers vertical" |
| L1.4 | Shelf at the correct standoff height | L2.4.1 to L2.4.3 | L3.4.1.1, L3.4.1.2, L3.4.2.1, L3.4.2.2, L3.4.3.1 | L1.4 | inspection | "the Pico rests on a shelf at the correct standoff height" |
| L1.5 | Pico located and free to lift off | L2.5.1 to L2.5.4 | L3.5.1.1, L3.5.1.2, L3.5.1.3, L3.5.2.1, L3.5.3.1, L3.5.4.1 | L1.5 | test | "while I solder a Pico onto them" (the Pico must stay put and come off after) |
| L1.6 | A soldering iron reaches every pin from above | L2.6.1 to L2.6.2 | L3.6.1.1, L3.6.2.1 | L1.6 | test | "while I solder a Pico onto them" |
| L1.7 | Perfboard cradle: a 70 x 50 pocket where the board lies flat | L2.7.1 to L2.7.4 | L3.7.1.1, L3.7.1.2, L3.7.1.3, L3.7.2.1, L3.7.3.1, L3.7.4.1, L3.7.4.2 | L1.7 | inspection | "a 70 x 50 perfboard cradle" |
| L1.8 | Zones apart and walls thick enough | L2.8.1 to L2.8.3 | L3.8.1.1, L3.8.2.1, L3.8.2.2, L3.8.3.1 | L1.8 | analysis | "The jig also has a ... cradle" |
| L1.9 | One piece that prints without supports | L2.9.1 to L2.9.4 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1 | L1.9 | analysis | "printed ... without supports" (added) |
| L1.10 | Compact and stable on the bench | L2.10.1 to L2.10.2 | L3.10.1.1, L3.10.2.1 | L1.10 | inspection | "jig" (bench use implied) |
| L1.11 | Datum pose is derivable: Pico height above the seat matches the header spacer | L2.11.1 to L2.11.2 | L3.11.1.1, L3.11.2.1 | L1.11 | analysis | "the correct standoff height" |
| L1.12 | Package says what was built and its claims are true | L2.12.1 to L2.12.2 | L3.12.1.1, L3.12.1.2, L3.12.2.1 | L1.12 | inspection | needed by the judge (not in the brief) |

---

## 8. Judging this design

> `benchmarks/generalize/rubric.md` was not present when this file was written, so this
> section is the design-specific rubric for G41. It follows `benchmarks/enclosure/rubric.md`
> (sections 2 to 5 and the recipes of its section 3: load, `clear_of`, `inside`, apertures,
> distances, printability, stability) and adds what this design needs. When the generic rubric
> exists, it governs the procedure and report format and this section governs the numbers.

### 8.1 Inputs

| Input | Where | Used for |
|---|---|---|
| `jig.stl` | the design package (jig frame, mm) | **every measurement** |
| `.scad` source | package | naming features; never for measuring |
| `layout.json` | package | declared poses, seat plane Z, pin tail length, print orientation |
| `report.json` | package | L1.12 self-report check only |
| renders | package `views/*.png` | locating defects |
| `requirements.md`, `parts/*/part.json` | this folder and `benchmarks/enclosure/parts/` | criteria and reference models |

The judge does **not** use the agent's code or transcript, earlier verdicts, `benchmarks/heldout.json`,
or any private design of Robin's. Renders locate defects; they never make a check pass.

### 8.2 Procedure

1. **Package gate (G0).** The files above exist and load; if the STLs are missing or unreadable, stop: DOES NOT MEET, one defect on the package L3.
2. **Units.** Load each STL with trimesh and build a `manifold3d.Manifold` (recipe 3.1 of the enclosure rubric). A body whose bounding-box maximum is not plausible in mm (outside 20 to 200) is a defect, never silently rescaled.
3. **Normalise the frame.** Put the jig in the jig frame (section 1.1): underside at Z = 0, rows along X, the Pico zone's USB end at −X. Use rotations by multiples of 90° and mirroring only; record the transform.
4. **Build the references independently** from `parts/*/part.json` at the declared poses (section 2), run the sanity checks R1 to R5, then verify the seating rule.
5. **Run every applicable L3** with Python, in order. Record the measured value, the limit, the signed margin (negative = fail) and PASS / FAIL / UNVERIFIED / N/A. **UNVERIFIED counts as FAIL.** N/A only for physical tests (unless a print was made) and checks the section 3 fixed decisions switch off.
6. **Look at the renders** after measuring, to confirm where each failure is and to catch defects no L3 covers (a floating fragment, a feature on the wrong side). Report those as observations; they change the verdict only if a re-measurement makes an L3 fail.
7. **Decide** (8.4) and **report** (8.5).

### 8.3 Measurement recipes specific to this design

- **Guide holes:** slice the jig at 0.5 below the seat plane; each small circular hole polygon is a hole (count them; ignore polygons larger than Ø3); inscribed circle for Ø, centre for the axis; pattern from the centres (row spacing from the two Y clusters, pitch from sorted X); depth by ray casting down each axis from the seat plane to the first solid (a through hole counts as the plate thickness).
- **Pin fit:** build V-PIN-k as cylinders and `pen` against the jig; `min_gap` as the slack.
- **Seat and shelf:** from the slice just above the seat plane, take the flat top faces (n_z > 0.999); flatness from the vertex heights; shelf height = shelf top − seat Z; areas from the polygons.
- **Locating walls:** at the PCB edge midpoints cast rays outward from the Pico's edge to the nearest wall face (four sides, min and max along each); wall top height from the ring's top face Z.
- **Cradle:** slice at mid-depth; the pocket rectangle is the four half-planes fitted to the straight wall faces, using only the parts of each face more than 1.0 away from a notch, so the notches do not enlarge the pocket size or the clearance per side; clearance to the declared board from that rectangle; floor Z by ray casting down; depth = rim Z − floor Z; notches are the polygon lobes outside that rectangle.
- **Sweeps and columns:** extrude the Pico, header and pin silhouettes along their paths; `clear_of` with the seat and shelf contact at the end excluded.
- **Thickness, ligaments, stability, printability:** enclosure rubric recipes 3.5 to 3.7 (the Ø1.0 holes are exempt from the overhang scan as round holes).

### 8.4 Verdict

Gates: G0 package, G1 one manifold body, G2 guide holes (40, Ø, pattern, depth, pin fit), G3 seat flat and shelf at the spacer height, G4 Pico seats, installs and can be soldered, G5 perfboard cradle fits the board.

| Class | Rule |
|---|---|
| **WRONG** | any gate fails |
| **MINOR** | no gate fails, but some weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |

**MEETS requirements** (the zero-error state) = CORRECT **and** every applicable non-physical L3 of weight 1 and 2 passes. Anything else is **DOES NOT MEET**. Also report the weighted score Σ(weight × pass) / Σ(weight) over applicable L3s and the worst normalised margin among weight-3 L3s (margin ÷ the criterion's tolerance or, for one-sided limits, ÷ 0.5 mm), so a loop can tell progress inside DOES NOT MEET.

Precedence rules:
- **The numbers in this file beat `part.json`.** If a catalogue file disagrees with section 2 or 3 here, build the references from this file and record a defect on the requirement the stale data breaks, with `where` = the part.json field.
- **Designed contact is not interference** (section 1.3). Only penetration above 0.01 mm³ counts for the listed pairs.
- A clearance or fit check outranks a size or tidiness check when the two conflict.
- Never relax a criterion, never round in the design's favour beyond ε, never infer a pass from a render.

### 8.5 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first (gates, then weight 3, 2, 1). Fields: `req` (L3 id with its L2 and L1), `status` (FAIL or UNVERIFIED), `body` (name of the printed body, or `layout`), `feature` (by function and, if present, SCAD name), `face` (surface, side and outward normal), `location` (coordinates in mm in the design frame: a point or a bounding box), `measured` / `limit` / `margin` (numbers with units), `reference` (the reference model or envelope and datum), `render`, `evidence` (saved file, e.g. the intersection solid as `defect_<L3>.stl`), `needed` (the change that would make the check pass, as numbers, never as a design instruction). Coordinates come from the measurement, not from the SCAD source. Group L3s that fail for one geometric reason under the first and list the others in `also_fails`. Keep observations separate from defects. Save the report as `judge.md` and `defects.json`.

### 8.6 Measured-values table (always filled in, pass or fail)

| Quantity | Limit | Measured |
|---|---|---|
| Guide holes: count; Ø each; axis residual; depth | 40; 0.95 to 1.10; ≤ 0.10; ≥ 6.5 |  |
| Row spacing; pitch; end-to-end | 17.78 ± 0.05; 2.54 ± 0.03; 48.26 ± 0.10 |  |
| Pins fit holes d | ≥ 0.0 |  |
| Header tilt bound | ≤ 2.0° |  |
| Seat flatness; coplanar; coverage | ≤ 0.10; ≤ 0.10; ≥ 90% |  |
| Shelf height above the seat; flatness | 2.5 ± 0.10; ≤ 0.10 |  |
| Shelf area; clearance to spacers / pins | ≥ 200 mm²; ≥ 0.3 / ≥ 0.5 |  |
| Pico on the shelf gap | ≤ 0.10 |  |
| Locating wall clearance per side; top height | 0.15 to 0.50; 0.4 to 0.9 |  |
| Wall to receptacle d | ≥ 0.20 |  |
| Pico install / header install / lift-off d | ≥ 0 / ≥ 0 / ≥ 0 |  |
| Solder-access zone d | ≥ 0 |  |
| Pocket size; clearance per side; depth | 70.6 ± 0.2 × 50.6 ± 0.2; 0.2 to 0.4; 2.5 to 6.0 |  |
| Notches: count, width, reach, outside ligament | ≥ 2; ≥ 10; ≥ 2.0; ≥ 1.0 |  |
| Zone separation; cradle walls; floor material | ≥ 3.0; ≥ 2.0; ≥ 2.0 |  |
| Shells; overhang patches; bed contact | 1; 0; ≥ 80% |  |
| Bounding box X × Y × Z | ≤ 100 × 90 × 20 |  |
| Self-report agreement | 100% within 0.10 |  |

---

## Audit

Adversarial audit (2026-10-24). Part ids checked with `parts.py` (`rpi_pico2`, `header_male_2p54`, `perfboard` load and pass the gate). Counts recomputed: L1 12 in `design.json` and section 4, L2 37, L3 51, weights 25 / 20 / 6, total 121, matching section 5. Section 6 re-derived from the instantiated catalogue: Pico pin axes X 14.17 + 2.54 i (pin 0 at 1.37 from the PCB end), Y 62.51 and 80.29 (rows 17.78 apart), spacer 50.8 × 2.5 centred on each row, spacer X 12.9 to 63.7, Pico underside Z 12.5, receptacle underside Z 13.5, locating ring top Z 13.3 (receptacle 0.2 above it, wall top 0.8 above the underside), shelf 0.5 from the spacers and 1.75 from the pin axes, spacers 0.4 from the ring at the X ends, plate 10.0 ≥ hole depth 8.0 + 1.0.

Fixes made in place:

1. **Hidden requirement.** L2.7.4 (finger notches, weight 2) appeared in neither the request text nor any L1. Notches are now in the request text and in L1.7 (at least two, 10 mm wide or more, on opposite walls), and `request_notes` already named them.
2. **Notch placement contradicted other rows.** Section 6 put the notches in the long walls, one of which is the 4.0 divider to the Pico zone: reaching 2.5 into it leaves 1.5, below the 3.0 zone separation of L2.8.1 if a notch counts as part of the cradle. They are now one in each short end wall (far from the Pico zone). L2.7.4 states that a notch counts as cradle for L2.8.1.
3. **Pocket size could not be measured.** Recipe 8.3 took the pocket polygon's bounding box, which any notch enlarges (70.6 → 75.6), failing L3.7.1.1 (gate G5) for a correct design. The pocket rectangle is now fitted to the straight wall faces, ignoring the first 1.0 around a notch.
4. **Hidden numbers moved into L1** (the text the agent gets): hole Ø band 0.95 to 1.10 and depth ≥ 6.5 (L1.2), seat flatness, coverage and the 2° lean limit (L1.3), shelf ≥ 200 mm² with 0.3 / 0.5 clearances (L1.4), wall clearance 0.15 to 0.5 per side and top 0.4 to 0.9 above the underside (L1.5), pocket clearance band 0.2 to 0.4 and depth 2.5 to 6.0 (L1.7), print rule 45° / 15 mm (L1.9).
5. **L3 rows with no number** (L3.1.1.1, L3.7.3.1, L3.9.2.1, L3.9.3.1, L3.9.4.1, L3.10.1.1, L3.10.2.1, L3.12.1.1) now carry numbers; unit limit made 20 to 200 in section 8.2 to match L3.12.1.1.
6. **Table syntax.** `|difference|` and `|d_agent − d_judge|` contained bare pipes that split table cells; escaped as in E1-01.

Checked and left alone: the header tilt bound (1.86° at Ø1.10, depth 6.0) is within 2.0°; pin Ø0.905 in a Ø1.0 hole (slack 0.047 per side) passes L2.2.4; tail 6.0 + 3.0 above the spacer top leaves 2.0 above the PCB; the 8.0 soldering zone is clear because every jig surface (ring top 13.3, plate 10.0) is below the PCB top 13.5; no L2 contradicts another after fixes 2 and 3.
