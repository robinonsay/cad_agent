# G02 Arduino Uno R3 case with vented screw lid: requirements (L1 / L2 / L3)

A training entry of the generalization benchmark (`benchmarks/generalize/`), modelled on E1-01
(`benchmarks/enclosure/requirements.md`). The machine-readable request (L1 only, `dev.json` format) is
`design.json` next to this file. This file holds the L2/L3 tree, the reference models, the
assumptions, the fixed decisions, a feasibility sketch, the traceability and the design-specific judging rules (section 8). Catalogue parts:
`benchmarks/generalize/parts/` (`arduino_uno_r3`, `plug_usb_b`, `plug_dc_barrel_5p5`) and
`benchmarks/enclosure/parts/screw_m3_selftap`. No number here may appear in agent logic: they live in the request, this file, `design_rules.json` generic values and `part.json` data.

**Request (plan brief, verbatim):** "Please design a case for an Arduino Uno R3 that sits on four standoffs at the board's own mounting holes. The USB-B and the 5.5 mm barrel jack are on the same short side and must both be pluggable with their cables attached. Put a row of ventilation slots over the ATmega and screw the lid down with four M3 screws."

**Expanded request** (the text the agent gets, `design.json`): A case for an Arduino Uno R3 (68.6 x 53.3 mm, four 3.2 mm mounting holes) that sits on four standoffs at the board's own mounting holes. The USB-B receptacle and the 5.5 mm barrel jack are on the same short edge of the board; both must be pluggable with the lid on and their cables attached, so each plug body (the moulded handle as well as the metal) has to fit through the wall. Put a row of ventilation slots in the lid over the ATmega328P, and screw the lid down with four M3 self-tapping screws. The case is a base and a removable lid, printed on an FDM printer in PLA without supports, and the board has to come out for service.

**How to read this.** L1 says what the owner needs; L2 turns it into an engineering requirement with numbers; L3 is a concrete check Python can run on the delivered STLs. Each row has a method, a pass/fail criterion with a number and tolerance, a weight (3 critical, 2 major, 1 minor) and, for must-pass rows, a gate mark. Numbers that come from an assumption (section 3) are provisional until Robin confirms them. Do not relax a criterion because a design fails it.

---

## 1. Frames, tolerances and the interference checks

### 1.1 Frames

- **Board frame (all tables below):** the catalogue module frame of `arduino_uno_r3`: origin at the PCB's min corner, **X along the 68.6 mm side, Y along the 53.3 mm side, Z up with the PCB underside at Z = 0**; the PCB occupies Z 0 to 1.6. The USB-B receptacle and the DC jack are on the **−X** short edge, overhanging it. The closed case is graded in this frame; a case delivered mirrored or rotated by 90° multiples is normalised into it first (rubric step 3) and never penalised.
- **Case frame:** the same axes, floor underneath (Z < 0).

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
- the board's underside on the standoff tops, inside the V-SEAT-k columns
- an M3 screw in its pilot hole (board screw in a standoff, lid screw in a boss), and its head on the board top or the lid top
- the lid plate's underside resting on the rebate floor and on the four boss tops
- the lid plate's edge against the rebate upstand, at the fit the lid requirements set (0.15 to 0.35 per side)
- a plug in its receptacle at full mate (the shell inside the receptacle; the plug is an envelope, not part of the case)

For these pairs only penetration counts (an intersection volume above 0.01 mm³, unless the pair
is given a larger allowance below). A distance of zero is a pass.

`bodies` is **ALL** (base and lid, closed), **BASE** or **LID**.

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` in `benchmarks/generalize/parts/<part_id>/` (and `benchmarks/enclosure/parts/screw_m3_selftap`). The only place part numbers may live.
- **envelope**: a keep-out or access volume generated by Python from the datums. Never drawn by hand.
- **computed**: derived from the design (cavity, apertures).

### 2.2 Reference models (M-)

The board has no free placement (its parts are fixed on the PCB), so the pose is the board frame itself plus the translation and 90° rotation the design declares.

| Name | What | Source | Size and position (board frame, mm) | Datums |
|---|---|---|---|---|
| **M-PCB** | Uno R3 PCB | catalogue `arduino_uno_r3` | 68.6 × 53.3 × 1.6; X 0 to 68.6, Y 0 to 53.3, Z 0 to 1.6; four holes Ø3.2 at (14.0, 2.5), (15.3, 50.7), (66.1, 7.6), (66.1, 35.5) | `PCB_TOP`, `PCB_BOTTOM`, `HOLE` (4 axes, keep-out Ø7.0) |
| **M-USB** | USB-B receptacle | same | 12.0 (Y) × 16.0 (X) × 11.0 (Z) on the PCB; X −6.0 to 10.0, Y 32.1 to 44.1, Z 1.6 to 12.6; centre Y 38.1, axis height Z 7.1 | `USB_MOUTH` (−6.0, 38.1, 7.1), `USB_AXIS` (−X) |
| **M-DC** | DC jack | same | 9.0 (Y) × 14.0 (X) × 11.0 (Z); X −2.0 to 12.0, Y 3.1 to 12.1, Z 1.6 to 12.6; centre Y 7.6, axis height Z 7.1 | `JACK_MOUTH` (−2.0, 7.6, 7.1), `JACK_AXIS` (−X) |
| **M-UNO** | the whole board = M-PCB ∪ M-USB ∪ M-DC | assembled | top parts up to 8.5 above the PCB top besides the two receptacles; solder tails 2.0 below | all of the above, `MCU` (48.0, 18.0, 1.6) |
| **M-PLUG-USB** | USB-B cable plug (with handle) | catalogue `plug_usb_b` | metal shell 12.0 × 10.9, inserted depth 10.0, exposed shell 1.5; overmold 16.0 × 13.0 × 30 long | `PLUG_TIP`, `PLUG_AXIS`, `OVERMOLD_FACE` |
| **M-PLUG-DC** | 5.5 × 2.1 DC barrel plug (with handle) | catalogue `plug_dc_barrel_5p5` | barrel Ø5.5 × 14.0; overmold Ø11.0 × 16 long; stop gap at full mate 1.0 | `PLUG_TIP`, `PLUG_AXIS`, `SEAT`, `OVERMOLD_FACE` |
| **M-SCREW-M3** | M3 pan-head self-tapper (board and lid) | catalogue `screw_m3_selftap` | head Ø6.0 × 2.4, thread Ø3.0, length 10, pilot Ø2.5 (2.4 to 2.6), clearance Ø3.4, min engagement 6.0, min boss OD 6.0 | `AXIS` |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Source | Definition (board frame, mm) |
|---|---|---|---|
| **V-KO-TOP** | component keep-out above the board | envelope | board footprint X 0 to 68.6, Y 0 to 53.3, Z 1.6 to 13.6 (12.0 above `PCB_TOP`, A3) |
| **V-KO-BOT** | solder-side keep-out | envelope | board footprint, Z −4.0 to 0 (A3), minus the four V-SEAT columns |
| **V-SEAT-k** | where a standoff may touch the board | envelope | Ø7.0 column on `HOLE_k`, from the floor up to `PCB_BOTTOM` |
| **V-HOLE-KO-k** | screw-head room above each board hole | envelope | Ø6.0 column on `HOLE_k`, Z 1.6 to 13.6 |
| **V-PCB-EDGE** | lateral clearance zone of the board | envelope | M-PCB (clearance 0.5, V-SEAT excluded) |
| **V-USB-PLUG** | USB-B plug at full mate plus its path | envelope | shell 12.0 × 10.9 from 10.0 inside `USB_MOUTH` to 1.5 outside it (X +4.0 to −7.5); overmold 16.0 × 13.0 from X −7.5 outward to −37.5; axis (Y 38.1, Z 7.1) |
| **V-DC-PLUG** | DC plug at full mate plus its path | envelope | barrel Ø5.5 from 13.0 inside `JACK_MOUTH` to 1.0 outside it (X +11.0 to −3.0); overmold Ø11.0 from X −3.0 to −19.0; axis (Y 7.6, Z 7.1) |
| **V-INSTALL** | board installation path | envelope | M-UNO's plan silhouette swept +Z from its seated pose to 5.0 above the base rim, minus the V-SEAT columns |
| **V-DRIVER-k** | screwdriver access to a board screw | envelope | Ø6.0 column on `HOLE_k` from `PCB_TOP` to 50 above the base rim, lid off |
| **V-LIDDRIVER-j** | screwdriver access to a lid screw | envelope | Ø6.0 column on each lid-screw axis from the lid top to 50 above it |
| **V-VENT** | the zone a vent slot must lie inside | envelope | the ATmega328P DIP-28 footprint (A4: 35.6 along X × 7.6 across, centred on `MCU`) grown 3.0 across: X 30.2 to 65.8, Y 11.2 to 24.8 |
| **V-CAVITY** | the closed case's internal void | computed | convex hull of (BASE ∪ LID, closed) minus (BASE ∪ LID), the connected component containing the board centroid |
| **V-AP-USB**, **V-AP-DC** | the openings actually present in the −X end wall | computed | the wall's slab (between its inner and outer faces, full Y and Z extent) minus (BASE ∪ LID), split into connected regions |
| **V-AP-OTHER** | every other opening | computed | every through-path from outside into V-CAVITY, as connected regions, outside the −X wall openings |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-PCB | units and size | 68.6 × 53.3 × 1.6 ± 0.2 |
| R2 | M-PCB | hole pattern and diameter | holes Ø3.2 ± 0.1 at the four coordinates ± 0.05 |
| R3 | M-USB, M-DC | orientation and overhang | components on +Z; axes −X; overhang 6.0 ± 0.3 and 2.0 ± 0.3 |
| R4 | M-PLUG-USB, M-PLUG-DC | sizes | overmold 16.0 × 13.0 ± 0.1; Ø11.0 ± 0.1; barrel Ø5.5 ± 0.05 |
| R5 | M-UNO ∪ V-PLUGs | plugs do not collide with each other; each mates its receptacle | intersection ≤ 0.01 mm³ (mating excluded) |
| R6 | every V- envelope | datums equal the model datums it came from | ≤ 0.01 |

**Seating rule.** The board is placed at the pose in `layout.json`. The grader then verifies: M-PCB's underside lies on the standoff tops (distance ≤ 0.10) and `HOLE_1..4` are coaxial with the standoff pilots (least squares, residual ≤ 0.25). If the declaration is missing or fails, the board is seated by that fit instead; if there are no standoffs it is centred in the cavity with its underside 4.0 above the floor, and every L1.3 check fails.

---

## 3. Assumptions, fixed decisions and open questions

### 3.1 Assumptions (derived, with their uncertainty)

| # | Question | Value chosen | Why, and uncertainty |
|---|---|---|---|
| A1 | What is "the same short side"? | The −X short edge (53.3 mm) of the catalogue frame, where the board's USB-B and DC jack sit. | They are fixed on the board; only the case end is a choice. Low uncertainty. |
| A2 | Port positions along the edge? | USB-B centre Y 38.1 and DC jack centre Y 7.6, axes at Z 7.1; USB overhang 6.0, jack overhang 2.0. | Catalogue values read from reference photographs (±1.5 on the Y centres). **Measure the owner's board.** |
| A3 | Clearance above and below? | 12.0 above the board top (tallest part the 11.0 receptacles, plus 1.0 margin); 4.0 below (solder tails 2.0 plus 2.0). | Top parts height 8.5 and receptacles 11.0 (catalogue). Low uncertainty. |
| A4 | Where is the ATmega? | The DIP-28 footprint 35.6 × 7.6 along X, centred on the catalogue `MCU` datum (48.0, 18.0). | Datasheet DIP-28 300 mil outline; the real chip position may differ by ±2 mm in X and Y; the V-VENT zone is grown 3.0 across to absorb it. Medium uncertainty. |
| A5 | How is the board held? | Four M3 self-tapping screws (catalogue `screw_m3_selftap`, length 10) through the board's Ø3.2 holes into standoff pilots Ø2.4 to 2.6. | "sits on four standoffs at the board's own mounting holes"; M3 fits Ø3.2. Low uncertainty. |
| A6 | Plug sizes? | USB-B overmold 16.0 × 13.0, shell 12.0 × 10.9; DC handle Ø11.0, barrel Ø5.5 × 14.0. | Typical cables (catalogue). **Measure the owner's cables.** Medium uncertainty. |
| A7 | Opening tolerance? | Each opening at least 0.3 bigger than its plug on every side (clear_of 0.3) and at most 1.5 bigger. | Printing tolerance and the owner's "no more than 1.5". |
| A8 | Wall thickness and size limit? | Walls, floor and lid plate 2.0 to 4.0; closed outside size ≤ 100 × 70 × 35. | A tight design is 90.6 × 60.5 × 29.5 (section 6). |
| A9 | Printing? | FDM, PLA, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed; overhang limit 45° from vertical; bridges ≤ 15. | Common printers. |
| A10 | Vents? | 5 to 9 slots 1.5 to 3.0 × 8.0 to 12.0, total area ≥ 100 mm², in the lid only. | An Uno dissipates about 0.5 W; passive slots over the hottest chip. Low uncertainty. |
| A11 | Cable pull and mass? | 0.5 N sideways at a plug centre, total mass 120 g. | A tugging cable on a desk; board 25 g plus printed parts. |
| A12 | Service? | The board comes out lid-off, straight up; no tilting past the receptacles. | Lets the owner reflash or swap boards. |

### 3.2 Fixed decisions (a choice that would otherwise be ambiguous)

| # | Decision |
|---|---|
| F1 | The USB-B and DC openings are both in the −X end wall; no port is opened elsewhere. |
| F2 | **Lid form (not open to alternatives):** one flat plate that drops into a rebate in the wall tops, resting on the rebate floor and on four bosses, held by four M3 self-tapping screws through plain lid holes into boss pilots. Reason: the board fills the footprint, so bosses must sit outside it, and a lip that fits inside the walls would collide with them. No snap, sliding or lip-in-wall lid. |
| F3 | The board is fixed with its own four M3 screws; the lid screws are separate (L2.12.3). |
| F4 | Vent slots are in the lid only; the slot row axis is parallel to X (the chip's long axis). |
| F5 | The plug envelopes, not fixed hole sizes, set the openings: each plug handle must enter its opening for the plug to seat. |

---

## 4. Requirements tree

### L1.1 Board placed and its pose declared; both ports at one short end

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares the board's pose (catalogue id, position, rotation about Z in multiples of 90°) in the design frame. | inspection | `layout.json` present, parses, names `arduino_uno_r3` with a pose | 3 |  |
| L3.1.1.1 | Layout file parses and the catalogue id exists. | inspection | parse errors = 0; unknown ids = 0 | 3 | G0 |
| L2.1.2 | The USB and DC ports face the same short end: the `USB_AXIS` and `JACK_AXIS` datums both point out through one end wall. | inspection | both axes within 1.0° of −X in the normalised frame; `USB_MOUTH` X and `JACK_MOUTH` X both within 0.1 of the catalogue values | 3 |  |
| L3.1.2.1 | Port axis directions. | inspection | each within 1.0° of −X (±0.5° measurement) | 3 |  |
| L2.1.3 | The board sits level: its plane is horizontal and its pose is a pure translation plus a 90° multiple. | inspection | PCB normal within 0.5° of +Z | 2 |  |
| L3.1.3.1 | Board tilt. | inspection | ≤ 0.5° | 2 |  |

### L1.2 Board fits inside with 0.5 mm clearance

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | With the board seated and the lid closed, no printed body comes within 0.5 of the board, except the standoff tops under its holes. | analysis | clear_of(ALL, M-PCB minus the V-SEAT columns grown by 0.5, 0.5) | 3 |  |
| L3.2.1.1 | Board-edge clearance, all four edges and both faces. | analysis | d ≥ 0.50 | 3 | G2 |
| L3.2.1.2 | A 68.6 × 53.3 × 1.6 box fits the base with 0.5 clearance (own-model proxy). | demonstration | the box's margin to the base cavity walls ≥ 0.50 on all four sides | 2 |  |
| L2.2.2 | Along X the cavity takes the board plus the overhanging USB and jack bodies. | analysis | inside(M-UNO (PCB, USB-B, DC jack), V-CAVITY, 0.2) | 3 |  |
| L3.2.2.1 | Whole board inside the cavity. | analysis | d ≥ 0.20 | 3 | G2 |

### L1.3 Four standoffs at the board's mounting holes, with M3 pilots

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Four standoffs, one under each board hole, on the board's own hole pattern. | inspection | count = 4; each axis within 0.25 of its `HOLE` datum | 3 |  |
| L3.3.1.1 | Exactly 4 standoffs. | inspection | count = 4 | 3 | G4 |
| L3.3.1.2 | Standoff axes versus the seated board's holes. | analysis | each offset ≤ 0.25 | 3 | G4 |
| L3.3.1.3 | Standoff pattern. | inspection | pairwise distances within 0.25 of the hole datums' distances | 2 |  |
| L2.3.2 | Standoff OD 5.0 to 7.0; tops coplanar; each top touches the board only inside its V-SEAT column. | inspection | OD in [5.0, 7.0]; top-Z spread ≤ 0.10; each standoff inside V-SEAT up to the board underside | 2 |  |
| L3.3.2.1 | Standoff OD. | inspection | 5.0 to 7.0 | 2 |  |
| L3.3.2.2 | Top-plane spread. | inspection | ≤ 0.10 | 2 |  |
| L2.3.3 | Each standoff has a pilot for an M3 self-tapping screw (catalogue `screw_m3_selftap`: pilot 2.4 to 2.6), coaxial, deep enough for the screw to seat. | inspection | Ø 2.4 to 2.6; depth from the top ≥ 8.4 (length 10.0 − board 1.6); coaxial ≤ 0.1 | 3 |  |
| L3.3.3.1 | Pilot diameter. | inspection | 2.4 to 2.6 | 3 | G4 |
| L3.3.3.2 | Pilot depth. | inspection | ≥ 8.4 (= catalogue screw length 10.0 − board 1.6, so the head seats on the board; this also meets the 6.0 minimum engagement) | 2 |  |
| L2.3.4 | Standoffs are fused to the floor and the base is one body. | analysis | contact per standoff ≥ 15 mm²; BASE 1 shell | 2 |  |
| L3.3.4.1 | Standoff-to-floor contact. | analysis | ≥ 15 mm² | 2 |  |
| L3.3.4.2 | Base is one shell. | analysis | 1 shell | 3 | G1 |
| L2.3.5 | Nothing except the screws enters the board holes or blocks a screw head. | analysis | clear_of(ALL, V-HOLE-KO-k, 0.0) for k = 1..4 (Ø6.0 head column from the board top to +12) | 2 |  |
| L3.3.5.1 | Screw-head columns clear. | analysis | d ≥ 0.0 | 2 |  |

### L1.4 Clearance above and below the board

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Lid closed: no body enters the component zone above the board. | analysis | clear_of(ALL, V-KO-TOP, 0.0) | 3 |  |
| L3.4.1.1 | Top keep-out clear. | analysis | d ≥ 0.0 | 3 | G2 |
| L3.4.1.2 | Lid underside minus board top (own-model proxy). | inspection | ≥ 12.0 | 2 |  |
| L2.4.2 | No body enters the solder-side zone (except the standoffs in their V-SEAT columns). | analysis | clear_of(ALL, V-KO-BOT, 0.0) | 3 |  |
| L3.4.2.1 | Bottom keep-out clear. | analysis | d ≥ 0.0 | 3 | G2 |
| L3.4.2.2 | Standoff height above the floor top (own-model proxy). | inspection | 4.0 to 10.0 | 2 |  |

### L1.5 USB-B plug fits through the end wall with its cable attached

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Lid closed: the plug pushes in to full mate and pulls out without touching the case. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 |  |
| L3.5.1.1 | USB plug envelope clear. | test | d ≥ 0.30 | 3 | G3 |
| L3.5.1.2 | Physical: print, close, plug in a real cable. | test | clicks in fully, 3 of 3 tries (optional) | 2 |  |
| L2.5.2 | The USB opening is not oversized: within 1.5 of the plug envelope on every side. | analysis | inside(V-AP-USB, V-USB-PLUG offset by 1.5, 0.0) | 2 |  |
| L3.5.2.1 | Opening within the grown plug envelope. | analysis | d ≥ 0.0 (opening ≤ 19.0 × 16.0, ≥ 16.6 × 13.6) | 2 |  |
| L2.5.3 | Exactly one USB opening, in the end wall that faces the receptacle. | inspection | V-AP-USB has 1 connected region, centred within 1.0 of the `USB_MOUTH` Y and Z | 2 |  |
| L3.5.3.1 | Opening count and position in the USB wall. | inspection | 1 region; centre offset ≤ 1.0 | 2 |  |

### L1.6 5.5 mm barrel plug fits through its own opening, at the same time

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Lid closed: the barrel plug reaches full mate (handle face ≤ 1.0 from the jack mouth) without touching the case or the USB plug. | test | clear_of(ALL, V-DC-PLUG, 0.3); V-DC-PLUG ∩ V-USB-PLUG ≤ 0.01 mm³ | 3 |  |
| L3.6.1.1 | DC plug envelope clear. | test | d ≥ 0.30 | 3 | G3 |
| L3.6.1.2 | The two plug envelopes do not touch. | test | distance ≥ 0.0; ligament between the two openings ≥ 1.5 | 3 | G3 |
| L2.6.2 | The DC opening is not oversized. | analysis | inside(V-AP-DC, V-DC-PLUG offset by 1.5, 0.0) | 2 |  |
| L3.6.2.1 | Opening within the grown plug envelope. | analysis | d ≥ 0.0 (opening ≤ Ø14.0, ≥ Ø11.6) | 2 |  |
| L2.6.3 | Exactly one DC opening, in the same end wall. | inspection | V-AP-DC has 1 connected region, centred within 1.0 of the `JACK_MOUTH` Y and Z | 2 |  |
| L3.6.3.1 | Opening count and position in the DC jack wall. | inspection | 1 region; centre offset ≤ 1.0 | 2 |  |

### L1.7 Row of ventilation slots in the lid over the ATmega

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | A row of 5 to 9 slots, each 1.5 to 3.0 wide across the row and 8.0 to 12.0 long, at a pitch of 3.5 to 6.5. | inspection | count N in [5, 9]; width in [1.5, 3.0]; length in [8.0, 12.0]; pitch in [3.5, 6.5] (all within ε) | 3 |  |
| L3.7.1.1 | Slot count. | inspection | 5 to 9 | 3 | G5 |
| L3.7.1.2 | Slot width and length. | inspection | width 1.5 to 3.0; length 8.0 to 12.0 (each slot, from the largest inscribed rectangle) | 2 |  |
| L3.7.1.3 | Slot pitch. | inspection | 3.5 to 6.5 between neighbours | 2 |  |
| L2.7.2 | The row lies over the chip: every slot outline is inside V-VENT (the ATmega footprint plus 3.0 each side across), the row is straight and parallel to X, and it spans most of the chip. | analysis | each slot inside V-VENT; slot centres collinear within 0.3, row within 1° of X, row centreline Y within 3.0 of the `MCU` datum Y; first-to-last centre span ≥ 21.4 | 3 |  |
| L3.7.2.1 | Slots inside V-VENT. | analysis | every slot outline inside V-VENT (margin ≥ 0.0) | 3 | G5 |
| L3.7.2.2 | Row straightness and span. | inspection | collinear ≤ 0.3; ≤ 1°; span ≥ 21.4 | 2 |  |
| L2.7.3 | Total open area of the slots (through the lid plate) is enough to breathe. | analysis | sum of slot areas ≥ 100 mm² | 2 |  |
| L3.7.3.1 | Total vent area. | analysis | ≥ 100 mm² | 2 |  |
| L2.7.4 | The slots go through the lid only and keep material round them. | analysis | vent regions are through-holes of the lid; ligament to the lid edge, lid screw holes and neighbouring slots ≥ 1.5; no vent in the base | 1 |  |
| L3.7.4.1 | Slot ligaments. | analysis | ≥ 1.5 | 1 |  |

### L1.8 Lid is a separate plate in a rebate, held by four M3 screws

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Base and lid are separate bodies, each one connected body, not interpenetrating when closed. | analysis | BASE 1 shell; LID 1 shell; BASE ∩ LID ≤ 1.0 mm³ | 3 |  |
| L3.8.1.1 | Base and lid each connected. | analysis | 1 shell each | 3 | G1 |
| L3.8.1.2 | Base and lid do not interpenetrate. | analysis | ≤ 1.0 mm³ | 3 | G1 |
| L2.8.2 | Lid form: one flat plate 2.0 to 3.0 thick, dropping into a rebate in the wall tops: upstand at least 1.0 thick, rebate depth equal to the plate thickness within 0.3, fit clearance 0.15 to 0.35 per side on all four sides, plate top flush with the upstand top within 0.3. | inspection | every number met | 3 |  |
| L3.8.2.1 | Plate thickness and rebate depth. | inspection | 2.0 to 3.0; depth = thickness ± 0.3 | 3 |  |
| L3.8.2.2 | Fit clearance on all four sides. | inspection | 0.15 to 0.35 per side | 2 |  |
| L3.8.2.3 | Upstand thickness and flushness. | inspection | ≥ 1.0; flush within 0.3 | 2 |  |
| L2.8.3 | Exactly four lid bosses, outside the board footprint and its keep-outs, each with a pilot for an M3 self-tapping screw, tops at the rebate floor plane. | inspection | count = 4; pilot Ø 2.4 to 2.6, depth ≥ 10.0 − lid plate thickness (never below 6.0); OD ≥ 6.0; boss top within 0.10 of the rebate floor plane; boss ∩ V-KO-TOP, V-INSTALL ≤ 0.01 mm³; boss to board ≥ 0.5; fused to the floor | 3 |  |
| L3.8.3.1 | Boss count. | inspection | 4 | 3 | G6 |
| L3.8.3.2 | Boss pilot diameter, depth and OD. | inspection | Ø 2.4 to 2.6; depth ≥ 10.0 − lid plate thickness (7.0 to 8.0, never below 6.0); OD ≥ 6.0 | 3 | G6 |
| L3.8.3.3 | Boss tops on the lid's resting plane. | inspection | ≤ 0.10 | 2 |  |
| L3.8.3.4 | Bosses clear of the board and its volumes. | analysis | d ≥ 0.5 to the board; ≤ 0.01 mm³ into V-KO-TOP and V-INSTALL | 3 |  |
| L2.8.4 | The lid has four plain holes for M3, coaxial with the boss pilots. | inspection | Ø 3.4 ± 0.10; axis offset to the boss axis ≤ 0.3 | 3 |  |
| L3.8.4.1 | Lid hole diameter. | inspection | 3.4 ± 0.10 | 3 | G6 |
| L3.8.4.2 | Lid-hole and pilot alignment. | inspection | ≤ 0.3 | 3 | G6 |
| L2.8.5 | The lid-screw heads can be driven: nothing above the lid screws. | analysis | clear_of(ALL, V-LIDDRIVER-1..4, 0.0) | 1 |  |
| L3.8.5.1 | Lid-screw driver columns. | analysis | d ≥ 0.0 | 1 |  |
| L2.8.6 | The lid stays on: held upside down it does not fall off, and the seam is tight. | test | seam gap ≤ 0.5; step between lid and base outer faces ≤ 0.5; upside-down test (optional, physical) | 1 |  |
| L3.8.6.1 | Seam gap and flushness. | inspection | ≤ 0.5; ≤ 0.5 | 1 |  |
| L3.8.6.2 | Physical: hold upside down and shake; open and close 10 times. | test | lid stays on through a 5 s shake and 10 open-close cycles; 0 cracks or stripped pilots (optional) | 1 |  |

### L1.9 Closed against dust: no openings but the ports, the vents and the screw holes, walls 2 to 4 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The only openings are the USB opening, the DC opening, the vents and the screw holes. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into V-CAVITY other than the vents and screw holes | 2 |  |
| L3.9.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 |  |
| L2.9.2 | Walls, floor and lid plate are 2.0 to 4.0 thick (away from ports, rebates and bosses). | inspection | each in [2.0, 4.0] (median over the wall) | 2 |  |
| L3.9.2.1 | Side wall thickness. | inspection | 2.0 to 4.0 | 2 |  |
| L3.9.2.2 | Floor thickness. | inspection | 2.0 to 4.0 | 2 |  |
| L3.9.2.3 | Lid plate thickness. | inspection | 2.0 to 3.0 (see L1.8) | 2 |  |
| L2.9.3 | At least 1.5 of material round every port opening (to wall edges, the floor top, the rebate floor and the neighbouring opening). | analysis | min ligament ≥ 1.5 | 1 |  |
| L3.9.3.1 | Minimum ligament per opening. | analysis | ≥ 1.5 | 1 |  |
| L2.9.4 | Each wall joins the floor along its length. | analysis | contact ≥ 90% of wall length × thickness | 2 |  |
| L3.9.4.1 | Wall-to-floor contact. | analysis | ≥ 0.9 × L × t | 2 |  |

### L1.10 Prints without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | In its stated print orientation (default: base open side up, lid outer face down) no part has an unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12.0 in vertical walls and bridges ≤ 15.0 (an opening wider than 15.0 needs a 45° roof). | analysis | 0 offending faces (area > 1 mm²) | 2 |  |
| L3.10.1.1 | Overhang and bridge scan per body. | analysis | 0 faces steeper than 45° with area > 1 mm²; every bridge ≤ 15.0; every round hole in a vertical wall Ø ≤ 12.0 | 2 |  |
| L2.10.2 | Each body is manifold and one shell. | analysis | 1 shell; manifold3d accepts it | 3 |  |
| L3.10.2.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.10.3 | Each body rests on a flat face in its print orientation. | analysis | bed contact ≥ 50% of the plan bounding box | 1 |  |
| L3.10.3.1 | Bed-contact area per body. | analysis | ≥ 50% | 1 |  |
| L2.10.4 | No feature thinner than 0.8; mating clearances ≥ 0.15; each body fits a 200 × 200 × 200 build volume. | analysis | min thickness ≥ 0.8; gaps ≥ 0.15; bounding box ≤ 200 per axis | 1 |  |
| L3.10.4.1 | Thin-feature and mating-gap scan. | analysis | min thickness ≥ 0.8; mating gaps ≥ 0.15; bounding box ≤ 200 per axis | 1 |  |

### L1.11 Sits on a desk: compact and stable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Closed outside size ≤ 100 × 70 × 35, longest plan side along X. | inspection | X ≤ 100.0, Y ≤ 70.0, Z ≤ 35.0; X > Y | 1 |  |
| L3.11.1.1 | Assembly bounding box. | inspection | X ≤ 100.0, Y ≤ 70.0, Z ≤ 35.0; X − Y > 0 | 1 |  |
| L2.11.2 | It stands on its base without tipping. | analysis | stable at 5° table tilt; no tip under a 0.5 N sideways pull at a plug centre (total mass 120 g) | 1 |  |
| L3.11.2.1 | `stable` at 5°. | analysis | centre-of-mass projection inside the support polygon with margin ≥ 0.0 mm at 5° tilt | 1 |  |
| L3.11.2.2 | Tipping-moment margin at each port. | analysis | margin > 0 | 1 |  |
| L2.11.3 | Flat underside; nothing below the floor except optional equal feet ≤ 3.0. | inspection | flatness ≤ 0.2; feet equal within 0.1 | 1 |  |
| L3.11.3.1 | Underside flatness and protrusions. | inspection | flatness ≤ 0.2; feet (if any) ≤ 3.0 high and equal within 0.1 | 1 |  |

### L1.12 The board goes in and out with the lid off, and every screw can be reached

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | Lid off: the board (with the USB and DC bodies overhanging the PCB edge) drops straight down onto the standoffs without hitting anything. | test | clear_of(BASE, V-INSTALL, 0.2), V-INSTALL excluding the V-SEAT columns | 2 |  |
| L3.12.1.1 | Installation path clear. | test | d ≥ 0.20 | 2 |  |
| L2.12.2 | A screwdriver reaches every board screw. | analysis | clear_of(BASE, V-DRIVER-1..4, 0.0) | 1 |  |
| L3.12.2.1 | Driver columns clear. | analysis | d ≥ 0.0 | 1 |  |
| L2.12.3 | Removing the lid does not release the board: no fastener is shared. | inspection | no shared fastener | 1 |  |
| L3.12.3.1 | Judge confirms no fastener is shared. | inspection | shared fasteners = 0 | 1 |  |

### L1.13 Package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | The package holds `base.stl`, `lid.stl` (closed pose, mm), the `.scad` source, `layout.json` (board pose, print orientations) and `report.json` (the agent's own clear_of / inside results). | inspection | all present and readable; each STL's largest bounding-box axis within 20 to 200 | 3 |  |
| L3.13.1.1 | Files present and parse; units are mm. | inspection | 5 of 5 files present; each STL's largest bounding-box axis within 20 to 200 | 3 | G0 |
| L3.13.1.2 | The declared board pose verifies under the seating rule. | analysis | board underside on standoff tops ≤ 0.10; hole-axis residual ≤ 0.25 | 3 |  |
| L2.13.2 | The agent's own clearance report agrees with the judge's measurements. | analysis | for every clear_of / inside L3 the agent reports, same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 |  |
| L3.13.2.1 | Self-report versus judge. | analysis | 100% agreement within 0.10 | 1 |  |

---

## 5. Counts

| Level | Count |
|---|---|
| L1 | 13 |
| L2 | 44 |
| L3 | 69 (weight 3: 26, weight 2: 29, weight 1: 14; total weight 150) |


Gates (a failure makes a design WRONG regardless of score; section 8): **G0** package (L3.1.1.1, L3.13.1.1); **G1** manifold, two bodies (L3.3.4.2, L3.8.1.1, L3.8.1.2, L3.10.2.1); **G2** board fit and keep-outs (L3.2.1.1, L3.2.2.1, L3.4.1.1, L3.4.2.1); **G3** USB and DC plugs seat at the same time (L3.5.1.1, L3.6.1.1, L3.6.1.2); **G4** board fixed on four pilot standoffs (L3.3.1.1, L3.3.1.2, L3.3.3.1); **G5** vent slots over the ATmega (L3.7.1.1, L3.7.2.1); **G6** lid screws: four bosses and holes (L3.8.3.1, L3.8.3.2, L3.8.4.1, L3.8.4.2).

---

## 6. Feasibility: a design that meets every number

A concrete design in the board frame, checked with a `manifold3d` model (base and lid one shell each; board, keep-outs, plugs, bosses and head columns clear; board clearance 0.6).

| Feature | Value |
|---|---|
| Cavity | X −8.5 to 76.1, Y −0.6 to 53.9 (board clearance 0.6 at the Y sides); floor top Z −7.0 (standoff height 7.0), floor 3.0 thick |
| Walls | 3.0 thick; outer X −11.5 to 79.1, Y −3.6 to 56.9, Z −10.0 to 19.5 |
| Standoffs | Ø6.0 at the four hole datums, Z −7.0 to 0; pilot Ø2.5, 8.5 deep (the length-10 screw through the 1.6 board needs 8.4; 1.5 of solid stays under the pilot) |
| Rebate | upstand 1.5 thick from Z 17.0 to 19.5; rebate floor Z 17.0 |
| Lid | plate Z 17.0 to 19.5 (2.5), outline inset 1.75 from the outer faces (1.5 upstand + 0.25 fit); four Ø3.4 holes |
| Lid bosses | Ø6.0 at (−5.0, 21.0), (−5.0, 50.5), (72.6, 5.0), (72.6, 49.0), from the floor to Z 17.0, pilot Ø2.5, 8 deep (needs 10.0 − 2.5 = 7.5); gap to the board ≥ 1.0 |
| USB opening | −X wall, Y 29.8 to 46.4, rectangular from Z 0.3 to 13.9 (16.6 × 13.6) with a 45° roof above it narrowing to a 14.4-wide flat top at Z 15.0 (16.6 × 14.7 overall, inside the 19.0 × 16.0 limit; the flat top bridges 14.4 ≤ 15.0); ligament to the rebate floor 2.0, to the floor top 7.3 |
| DC opening | −X wall, Ø11.6 centred (Y 7.6, Z 7.1); ligament to the side wall 2.4; gap to the USB opening 16.4 |
| Vents | 7 slots 2.0 × 10.0 at X = 33, 38, ... 63, Y 13.0 to 23.0 (area 140 mm², pitch 5.0, span 30) |
| Outside size | 90.6 × 60.5 × 29.5 (limit 100 × 70 × 35) |
| Margins | V-KO-TOP gap 0.6; plug envelopes to the case 0.30; head columns 0.1 to 1.6; board to bosses 1.0 |
| Print | base open side up, lid outer face down; no overhangs (bores vertical, rebate and bosses vertical; the USB roof is 45°, the DC hole is Ø11.6 ≤ 12.0) |

---

## 7. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 (design.json) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Board placed and its pose declared; both ports at one short end | L2.1.1 to L2.1.3 | L3.1.1.1, L3.1.2.1, L3.1.3.1 | L1.1 | inspection | "a case for an Arduino Uno R3", "the USB-B and the 5.5 mm barrel jack are on the same short side" |
| L1.2 | Board fits inside with 0.5 mm clearance | L2.2.1 to L2.2.2 | L3.2.1.1, L3.2.1.2, L3.2.2.1 | L1.2 | analysis | "a case for an Arduino Uno R3" |
| L1.3 | Four standoffs at the board's mounting holes, with M3 pilots | L2.3.1 to L2.3.5 | L3.3.1.1, L3.3.1.2, L3.3.1.3, L3.3.2.1, L3.3.2.2, L3.3.3.1, L3.3.3.2, L3.3.4.1, L3.3.4.2, L3.3.5.1 | L1.3 | inspection | "sits on four standoffs at the board's own mounting holes" |
| L1.4 | Clearance above and below the board | L2.4.1 to L2.4.2 | L3.4.1.1, L3.4.1.2, L3.4.2.1, L3.4.2.2 | L1.4 | analysis | "a case for an Arduino Uno R3" (tall parts: USB-B, jack, capacitors, headers) |
| L1.5 | USB-B plug fits through the end wall with its cable attached | L2.5.1 to L2.5.3 | L3.5.1.1, L3.5.1.2, L3.5.2.1, L3.5.3.1 | L1.5 | test | "USB-B ... pluggable with their cables attached" |
| L1.6 | 5.5 mm barrel plug fits through its own opening, at the same time | L2.6.1 to L2.6.3 | L3.6.1.1, L3.6.1.2, L3.6.2.1, L3.6.3.1 | L1.6 | test | "the 5.5 mm barrel jack ... pluggable with their cables attached" |
| L1.7 | Row of ventilation slots in the lid over the ATmega | L2.7.1 to L2.7.4 | L3.7.1.1, L3.7.1.2, L3.7.1.3, L3.7.2.1, L3.7.2.2, L3.7.3.1, L3.7.4.1 | L1.7 | inspection | "a row of ventilation slots over the ATmega" |
| L1.8 | Lid is a separate plate in a rebate, held by four M3 screws | L2.8.1 to L2.8.6 | L3.8.1.1, L3.8.1.2, L3.8.2.1, L3.8.2.2, L3.8.2.3, L3.8.3.1, L3.8.3.2, L3.8.3.3, L3.8.3.4, L3.8.4.1, L3.8.4.2, L3.8.5.1, L3.8.6.1, L3.8.6.2 | L1.8 | inspection | "screw the lid down with four M3 screws" |
| L1.9 | Closed against dust: no openings but the ports, the vents and the screw holes, walls 2 to 4 mm | L2.9.1 to L2.9.4 | L3.9.1.1, L3.9.2.1, L3.9.2.2, L3.9.2.3, L3.9.3.1, L3.9.4.1 | L1.9 | analysis | "a case for an Arduino Uno R3" |
| L1.10 | Prints without supports | L2.10.1 to L2.10.4 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1 | L1.10 | analysis | "printed on an FDM printer" (added) |
| L1.11 | Sits on a desk: compact and stable | L2.11.1 to L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.2.2, L3.11.3.1 | L1.11 | analysis | "a case" (desk use implied) |
| L1.12 | The board goes in and out with the lid off, and every screw can be reached | L2.12.1 to L2.12.3 | L3.12.1.1, L3.12.2.1, L3.12.3.1 | L1.12 | test | implied by a case that must hold a board and a removable lid |
| L1.13 | Package says what was built and its claims are true | L2.13.1 to L2.13.2 | L3.13.1.1, L3.13.1.2, L3.13.2.1 | L1.13 | inspection | needed by the judge (not in the brief) |

---

## 8. Judging this design

> `benchmarks/generalize/rubric.md` was not present when this file was written, so this
> section is the design-specific rubric for G02. It follows `benchmarks/enclosure/rubric.md`
> (sections 2 to 5 and the recipes of its section 3: load, `clear_of`, `inside`, apertures,
> distances, printability, stability) and adds what this design needs. When the generic rubric
> exists, it governs the procedure and report format and this section governs the numbers.

### 8.1 Inputs

| Input | Where | Used for |
|---|---|---|
| `base.stl`, `lid.stl` | the design package (closed pose, mm) | **every measurement** |
| `.scad` source | package | naming features; never for measuring |
| `layout.json` | package | the declared board pose and print orientations |
| `report.json` | package | L1.13 self-report check only |
| renders | package `views/*.png` | locating defects |
| `requirements.md`, `parts/*/part.json` | this folder and `benchmarks/generalize/parts/` | criteria and reference models |

The judge does **not** use the agent's code or transcript, earlier verdicts, `benchmarks/heldout.json`,
or any private design of Robin's. Renders locate defects; they never make a check pass.

### 8.2 Procedure

1. **Package gate (G0).** The files above exist and load; if the STLs are missing or unreadable, stop: DOES NOT MEET, one defect on the package L3.
2. **Units.** Load each STL with trimesh and build a `manifold3d.Manifold` (recipe 3.1 of the enclosure rubric). A body whose bounding-box maximum is not plausible in mm (outside 20 to 200) is a defect, never silently rescaled.
3. **Normalise the frame.** Put the closed case in the board frame (section 1.1): floor underside lowest, the end wall that has the openings at −X. Use rotations by multiples of 90° and mirroring only; record the transform.
4. **Build the references independently** from `parts/*/part.json` at the declared poses (section 2), run the sanity checks R1 to R6, then verify the seating rule.
5. **Run every applicable L3** with Python, in order. Record the measured value, the limit, the signed margin (negative = fail) and PASS / FAIL / UNVERIFIED / N/A. **UNVERIFIED counts as FAIL.** N/A only for physical tests (unless a print was made) and checks the section 3 fixed decisions switch off.
6. **Look at the renders** after measuring, to confirm where each failure is and to catch defects no L3 covers (a floating fragment, a feature on the wrong side). Report those as observations; they change the verdict only if a re-measurement makes an L3 fail.
7. **Decide** (8.4) and **report** (8.5).

### 8.3 Measurement recipes specific to this design

- **Standoffs, bosses, pilots, holes:** slice at mid-height or mid-depth; smallest enclosing circle for standoffs and bosses, largest inscribed circle for holes; depth by ray casting down the axis.
- **Apertures:** enclosure rubric recipe 3.4 on the −X end wall; report each opening's bounding box, centre and (for DC) inscribed circle in board-frame coordinates.
- **Vent slots:** slice the lid at mid-thickness; each connected hole polygon is a slot; length and width from the minimal-area bounding rectangle; centres, pitch and span from the rectangle centres; open area as the sum of polygon areas; V-VENT is a rectangle test on the polygon vertices.
- **Rebate and lid fit:** at six points on each side, ray cast across the rebate from the lid plate edge to the upstand (min, median, max); rebate depth from the rebate floor and the upstand top; flushness from the plate top and the upstand top Z.
- **Wall, floor, lid thickness; ligaments:** enclosure rubric recipe 3.5; ligament = minimum distance from an opening's polygon to the nearest edge or neighbouring opening.
- **Stability:** enclosure rubric recipe 3.7 with 120 g total.
- **Printability:** enclosure rubric recipe 3.6.

### 8.4 Verdict

Gates: G0 package, G1 manifold and two bodies, G2 board fit and keep-outs, G3 USB and DC plugs seat at the same time, G4 board fixed on four pilot standoffs, G5 vent slots over the ATmega, G6 lid screws (four bosses and holes).

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
| Board clearance to any surface (L3.2.1.1), mm | ≥ 0.5 |  |
| Board in cavity (L3.2.2.1), mm | ≥ 0.2 |  |
| Standoff count, axis offset (L3.3.1.x), mm | 4; ≤ 0.25 |  |
| Standoff OD, pilot Ø, depth, mm | 5.0 to 7.0; 2.4 to 2.6; ≥ 6.0 |  |
| Top / bottom keep-out d, mm | ≥ 0 / ≥ 0 |  |
| USB plug d; opening oversize d, mm | ≥ 0.3; ≥ 0 |  |
| USB opening W × H and centre, mm | 16.6 × 13.6 to 19.0 × 16.0 |  |
| DC plug d; opening oversize d, mm | ≥ 0.3; ≥ 0 |  |
| DC opening Ø and centre, mm | 11.6 to 14.0 |  |
| Plug envelopes mutual distance; ligament between openings, mm | ≥ 0; ≥ 1.5 |  |
| Vent slots: count, width × length, pitch, area | 5 to 9; 1.5 to 3.0 × 8 to 12; 3.5 to 6.5; ≥ 100 mm² |  |
| Vent slots inside V-VENT; span | yes; ≥ 21.4 |  |
| Lid plate; rebate fit per side; upstand | 2.0 to 3.0; 0.15 to 0.35; ≥ 1.0 |  |
| Lid bosses: count, pilot Ø, depth, OD; lid hole Ø; alignment | 4; 2.4 to 2.6, ≥ 6.0, ≥ 6.0; 3.4 ± 0.1; ≤ 0.3 |  |
| Opening counts: USB / DC / unlisted | 1 / 1 / 0 |  |
| Wall / floor / lid thickness | 2.0 to 4.0 |  |
| Overhang patches; bed contact per body | 0; ≥ 50% |  |
| Shells base / lid | 1 / 1 |  |
| Closed envelope X × Y × Z | ≤ 100 × 70 × 35 |  |
| Install sweep d; driver columns d | ≥ 0.2; ≥ 0 |  |
| Self-report agreement | 100% within 0.10 |  |

---

## Audit

Adversarial audit (2026-10-24). Part ids checked against `benchmarks/enclosure/parts` and `benchmarks/generalize/parts` with `parts.py` (all four load and pass the gate); counts recomputed (L1 13 in `design.json` and in section 4, L2 44, L3 69, weights 26 / 29 / 14, total 150, matching section 5); derived numbers recomputed from `part.json` (hole pattern, receptacle boxes X −6.0 / −2.0 to 10.0 / 12.0, plug envelopes, V-VENT = 35.6 × 7.6 grown 3.0 across, span 0.6 × 35.6 = 21.4).

Fixes made in place:

1. **Feasibility could not print.** The 16.6-wide rectangular USB opening is a 16.6 mm bridge, over the 15.0 bridge limit of L2.10.1, so section 6's claim of "no overhangs" was false. L2.10.1 now allows an opening wider than 15.0 with a 45° roof (stated in L1.10 and L3.10.1.1 too); section 6 gives the USB opening a 45° roof (flat top 14.4 ≤ 15.0, opening 16.6 × 14.7, still inside the 19.0 × 16.0 limit, ligament to the rebate floor 2.0).
2. **Screw could not seat.** Section 6 gave pilots 6.5 deep for a length-10 screw through a 1.6 board (tip depth 8.4), so the screw would bottom before the head seated. L2.3.3 / L3.3.3.2 now require depth ≥ 8.4 (10.0 − 1.6), L3.8.3.2 requires ≥ 10.0 − lid thickness (never below 6.0). Section 6 now has standoff height 7.0, floor 3.0, pilot 8.5 deep (1.5 solid left), boss pilots 8 deep (7.5 needed), rebate floor Z 17.0, outer Z −10.0 to 19.5. Outside size is now 90.6 × 60.5 × 29.5 (limit 35); A8 updated. Every gate was re-walked against the new numbers (ligaments, V-KO-BOT, V-KO-TOP 13.6 vs lid underside 17.0, bosses to board 1.0).
3. **Hidden numbers.** Judge limits that were only in L2/L3 are now in the L1 text the agent gets: standoff OD 5 to 7 and coplanar tops, pilot depth to seat a 10 mm screw (L1.3), 0.3 mm plug clearance (L1.5, L1.6), vent count / slot size / pitch (L1.7), lid plate 2 to 3 mm, fit gap 0.15 to 0.35 per side, upstand ≥ 1 (L1.8), the 45° / 15 mm print rule (L1.10).
4. **L3 rows with no number** (L3.1.1.1, L3.2.1.2, L3.10.1.1, L3.10.4.1, L3.11.1.1, L3.11.2.1, L3.11.3.1, L3.12.3.1, L3.13.1.1) now carry a numeric band or count.
5. **Inconsistent unit-plausibility limit:** L3.13.1.1 said 20 to 200, section 8.2 said 5 to 200. Both now 20 to 200.

Checked and left alone: no contradiction among the requirements (the section 6 design meets every gate after the fixes); designed contact pairs are listed in 1.3 and not treated as interference; the request text states no number the judge needs that the L1 does not.
