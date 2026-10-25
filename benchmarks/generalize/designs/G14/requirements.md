# G14 Nano buzzer box with dovetail slide lid: requirements (L1 / L2 / L3)

A training design of the generalisation benchmark (`benchmarks/generalize/plan.json`, family
electronics_enclosure). Modelled on E1-01 (`benchmarks/enclosure/requirements.md`): the same L1/L2/L3
structure, reference models built from catalogue parts, designed-contact rule, gates and
traceability. The machine-readable request (L1 only, `dev.json` format) is `design.json` next to this
file. Generic grading rules would live in `benchmarks/generalize/rubric.md`; when this file was
written that file did not exist yet, so **section 8 is a design-specific rubric supplement** (it
follows `benchmarks/enclosure/rubric.md`; if `generalize/rubric.md` exists later it governs the
generic parts and section 8 only adds the G14 specifics).

**Owner's request (brief, verbatim):** "An alarm box with an Arduino Nano and a 12 mm piezo buzzer in
a base with a dovetail rail; the lid slides on along the long axis with 0.25 mm fit clearance. A ring
of sound holes on the lid sits over the buzzer. The mini-USB end stays open."

**How to read this.** L1 says what the owner needs. L2 is an engineering requirement with numbers. L3 is a
concrete check Python can run on the delivered STLs. Every L3 has a method, a pass band with a tolerance,
a weight (3 = critical, 2 = major, 1 = minor) and, where it is a must-pass, a gate mark (G0 to G5,
section 5). Numbers that come from an assumption (section 3) are provisional until the owner confirms
them. Do not relax a criterion because the agent fails it.

---

## 1. Frames, tolerances, checks and designed contact

### 1.1 Frames

- **Box frame = Nano board frame:** the catalogue frame of `arduino_nano`: origin at the PCB's min
  corner, X along the 45 mm length with the mini-USB end at **-X** (the open end of the box) and the far
  end at **+X**, Y across the 18 mm width, Z up with the PCB underside at Z = 0 (the PCB occupies Z 0 to
  1.6; the header bodies hang below it). The floor is at negative Z. The buzzer lies beyond the Nano's
  far end (F8). A design delivered mirrored or rotated is normalised into this frame by multiples of 90
  degrees and mirroring only; that is never penalised.
- Lengths in mm, angles in degrees. "Closed" = base and lid in the assembly pose; "slide direction" = X.

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within e |
| angle | 0.5 degrees | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole diameter | largest inscribed circle of the hole's section (what a pin or buzzer sees) | |
| standoff / sleeve OD | smallest enclosing circle of the section | |

Where a criterion is written "nominal +/- t", t is the design tolerance and e is added to it.

### 1.3 The checks

- **`clear_of(bodies, volume, c)`**: minimum distance between the printed bodies and the volume is >= c.
  Reported: signed minimum distance d (negative = penetration; penetration volume too). Pass: d >= c - e.
- **`inside(volume, cavity, c)`**: the volume lies entirely in the cavity, every point >= c from its
  boundary. Pass: d >= c - e.
- **`slide(body, axis, travel)`**: the body is translated along the axis in 1.0 mm steps; at each step
  the intersection volume with the named solids is recorded (pass: <= 0.01 mm3 at every step) and the
  minimum gap (pass: as the requirement states). Resting contact (zero penetration) is allowed.
- **`float(axis)`**: the board model translated along an axis from its seated pose: total free travel
  (positive plus negative) before penetrating a printed body by more than 0.01 mm3, by bisection to 0.02.
- Count, dimension, thickness and gap checks as in E1-01 rubric section 3.5.

`ALL` = base and lid, closed. The grader builds every reference model and envelope itself from the
catalogue and the declared layout; the agent's copies are not trusted.

### 1.4 Designed contact is not interference

Parts meant to touch are excluded from every interference and clearance check; only penetration counts
(volume above 0.01 mm3), a distance of zero passes:

- the Nano's underside resting on the four standoff tops, inside the V-SEAT columns
- a locator pin in its board hole (radial gap 0.05 to 0.15, may be zero)
- the buzzer's base on the pocket ledge ring, and its side in the pocket (radial gap 0.1 to 0.3)
- the lid's underside resting on the wall tops and rail tops (the rim), and the lid sliding over them
- the lid's end face meeting the travel stop (the far wall), within the gap L2.7.3 sets

---

## 2. Reference models, envelopes and sanity checks

### 2.1 Reference models (M-)

Built by Python from `benchmarks/generalize/parts/<id>/part.json`. Positions are the **default layout**
(assumption A4), used when a design declares none; otherwise each model sits where `layout.json` declares
it (L3.1.1.1).

| Name | What | Source | Size and default position (box frame, mm) | Datums |
|---|---|---|---|---|
| **M-NANO** | Arduino Nano | catalogue `arduino_nano` | PCB 45.0 x 18.0 x 1.6 at X 0 to 45, Y 0 to 18, Z 0 to 1.6; mini-USB receptacle 9.0 (X) x 7.7 (Y) x 3.9 (Z) at X -0.7 to 8.3, Y 5.15 to 12.85, Z 1.6 to 5.5; header bodies on the underside 38.1 x 2.54 x 2.5 at X 3.45 to 41.55, Y 0.11 to 2.65 and 15.35 to 17.89, Z -2.5 to 0; pin tails Z -8.5 to -2.5 in the same strips; top parts up to Z 5.1 (component side) and 5.5 (receptacle); four holes Ø1.7 at (0.9, 1.38), (44.1, 1.38), (0.9, 16.62), (44.1, 16.62) | `USB_MOUTH` (-0.7, 9.0, 3.55), `USB_AXIS` (-X), `HOLE` (4 axes, Ø1.7, keep-out Ø4.0), `PCB_BOTTOM`, `PCB_TOP`, `PINS_A/B` |
| **M-BUZZ** | 12 mm piezo buzzer | catalogue `buzzer_12mm` | cylinder Ø12.0 x 8.5, axis +Z; default axis at (54.0, 9.0), base at Z -1.6, top at Z 6.9 | `AXIS`, `SOUND_PORT` (Ø1.5, on the top face), `PINS` (two leads at +/-3.25 along the buzzer's X, pointing -Z), `BOTTOM`, `TOP` |
| **M-PLUG-USB** | mini-USB B cable plug | catalogue `plug_miniusb_b` | metal shell 6.8 (Y) x 3.0 (Z), inserted depth 6.9, exposed shell 1.5; overmold 11.0 (Y) x 8.0 (Z) x 20.0 long | `PLUG_TIP`, `PLUG_AXIS`, `OVERMOLD_FACE` |
| **RBA** | reference board assembly = M-NANO and M-BUZZ at the declared (or default) layout | assembled | as above | all of the above |

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition (box frame, mm) | Used by |
|---|---|---|---|
| **V-KO-TOP** | component keep-out above the Nano | X -0.7 to 45, Y 0 to 18, Z 1.6 to 6.5 (tallest part 5.5 plus 1.0) | L2.3.1 |
| **V-KO-BOT** | header-and-tail keep-out under the Nano | the two header strips grown 0.3 sideways: X 3.15 to 41.85, Y -0.19 to 2.95 and 15.05 to 18.19, Z -8.8 (tails to -8.5 plus 0.3) to 0 | L2.2.4 |
| **V-SEAT-k** (k = 1..4) | where a standoff may touch the board | Ø4.0 column on `HOLE`-k from the floor up to `PCB_BOTTOM` | L2.2.1, L2.2.2 |
| **V-HOLECOL-k** | the pin's column through the board | Ø4.0 column on `HOLE`-k from `PCB_BOTTOM` to the pin tip | L2.12.1 |
| **V-USB-PLUG** | mini-USB plug at full mate plus its withdrawal path | shell 6.8 x 3.0 from X 6.2 (inside the receptacle) to X -2.2; overmold 11.0 x 8.0 from X -2.2 outward to X -60; centred on `USB_AXIS` (Y 9.0, Z 3.55) | L2.5.1, L2.7.2 |
| **V-LEAD-1,2** | buzzer lead zone | Ø1.0 cylinders on `PINS`, from the buzzer base down 4.0 (assumed lead length, A5) | L2.4.2 |
| **V-SOUND-GAP** | the air above the buzzer's sound port | Ø12.0 cylinder from `TOP` up 1.0 | L2.8.4 |
| **V-INSTALL-N** | Nano installation path | M-NANO plan silhouette (receptacle included) swept +Z from its seated pose to 5.0 above the base rim, minus V-SEAT and V-HOLECOL | L2.12.1 |
| **V-INSTALL-B** | buzzer installation path | M-BUZZ cylinder swept +Z from its seated pose to 5.0 above the base rim | L2.12.2 |
| **V-CAVITY** | the closed box's internal void | convex hull of ALL (ignoring the open end) minus ALL, connected component containing the Nano centroid | L2.1.3 |
| **V-AP-OTHER** | every other through-path from outside into V-CAVITY | rays from outside the hull reaching V-CAVITY without hitting a solid, as clusters, other than through the open -X end and the sound holes | L2.9.1 |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-NANO | units and outline | PCB 45.0 x 18.0 +/- 0.2; thickness 1.6 +/- 0.1 |
| R2 | M-NANO | orientation | components on +Z, receptacle at -X, header body on -Z, `USB_AXIS` along -X |
| R3 | M-NANO | holes | Ø1.7 +/- 0.2 at the four positions +/- 0.1 |
| R4 | M-BUZZ | diameter, height, orientation | 12.0 +/- 0.1; 8.5 +/- 0.1; `SOUND_PORT` on +Z |
| R5 | M-PLUG-USB | shell and overmold | 6.8 x 3.0 and 11.0 x 8.0, each +/- 0.1 |
| R6 | RBA | models do not collide | intersection <= 0.01 mm3 |
| R7 | every V- envelope | its datums equal the model datums it was built from | <= 0.01 |

**Seating rule.** The RBA is placed at the pose declared in `layout.json`. The grader verifies it:
`PCB_BOTTOM` lies on the standoff tops (distance <= 0.10), `HOLE`-k are coaxial with the locator pins
(least-squares residual <= 0.25), and the buzzer base lies on the ledge (distance <= 0.10) with its axis
coaxial with the pocket (<= 0.25). If the declaration is missing or fails verification, the RBA is seated
by that fit and L3.13.1.2 fails; if there are no standoffs, the Nano is centred in the cavity with its
underside 9.0 above the floor and every L1.2 check fails.

---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (A-rows, with uncertainty)

| # | Question | Value chosen | Why, and how uncertain |
|---|---|---|---|
| **A1** | How is the Nano located? | Four pins through the four holes (pin Ø1.4 to 1.6 in the Ø1.7 hole), on four standoffs of OD 3.0 to 4.0 under the holes; the holes are 0.9 from the short edges, so a standoff overlaps the PCB edge by up to 1.0 (as the catalogue says) | The official drawing gives 1.8 mm holes; the task sheet 1.7. Uncertainty +/-0.1 on the hole, +/-0.5 on clone boards. |
| **A2** | What does "the mini-USB end stays open" mean? | There is **no end wall** at -X: the cavity is open over the whole end, so the plug (and the lid) pass freely. | An opening in a wall would stop the lid sliding off along that end. Uncertainty: low. |
| **A3** | Header pins and tails | The header bodies (2.5) sit under the board; the pin tails reach 6.0 below the plastic (Z -8.5): both are a keep-out with 0.3 clearance, so the standoffs are at least 8.8 tall. If the owner's pins are cut short the box could be lower | Catalogue value (`pin_tail_length`, "Nano ships with the long pins down"). Uncertainty: +/-3 on tail length. |
| **A4** | Default layout (used only if none declared) | Nano at the origin; buzzer axis at (54.0, 9.0) with its base at Z -1.6 | A symmetric simple layout; the design may choose its own and declare it. |
| **A5** | Buzzer leads and sound | Leads 4.0 long below the buzzer base (assumed); lead pitch 6.5 (catalogue); acoustic gap 1.0 +/-0.5 over the top; total hole area in the lid over the buzzer >= 15 mm2 | Vendor drawings differ by +/-0.5; sound pressure is not graded. |
| **A6** | Plug | mini-USB overmold 11.0 x 8.0 x 20.0, shell 6.8 x 3.0, exposed 1.5 (`plug_miniusb_b`); the plug stays in while the lid slides, so the lid plate underside is above the overmold top (7.55) | Typical cables; measure the owner's. |
| **A7** | Lid retention against sliding off | Not required: no detent or latch; the lid is held by the dovetail and the far end stop, and can slide off the open end when tilted. A detent bump is welcome but not graded. | The owner did not ask; confirm if the box will be carried. |
| **A8** | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed. Base prints open side up; lid prints plate down (F6). Dovetail flank 60 degrees from horizontal prints without support. | Common printers. Uncertainty +/-0.1 on every fit; print a test rail. |
| **A9** | Maximum size | Closed outside <= 80 x 40 x 30 (X x Y x Z) | Stops oversized designs; a tight design is about 67.2 x 32.8 x 21.7 (section 6). Not in the owner's words; confirm. |
| **A10** | Walls | Walls, floor and lid plate 2.0 to 4.0; sleeve and skirt >= 1.6 | 5 perimeters at 0.4 mm. |
| **A11** | Dovetail | Standard 60 degree flank (from horizontal), rail height 3.0 to 4.0, overhang beyond the wall >= 1.2, fit measured as the horizontal (Y) gap between mating flank faces | 60 degrees is the usual dovetail angle and the steepest an FDM overhang allows (45 degrees is the limit). Uncertainty: +/-5 degrees. |
| **A12** | Active or passive buzzer, wiring | Not graded; the Nano is wired to the buzzer by flying leads | The outline is the same. |
| **A13** | Cable pull | 0.5 N sideways at the USB axis, total mass 60 g | A cable tugging a desk device. |

### 3.2 Fixed decisions (not open to alternatives)

| # | Decision |
|---|---|
| **F1** | The USB end has no end wall (A2); the lid and plug use that end. |
| **F2** | The Nano rests on four standoffs and is located by four pins through its holes; the lid does not clamp it. |
| **F3** | The dovetail rails are on the **outside** of the two long walls (undercut outward); the lid has a skirt on each side with the matching groove. |
| **F4** | The lid slides in from the open end (-X) along X and stops against the far end wall. |
| **F5** | The sound holes are a **ring of N >= 6 holes plus one central hole** over the buzzer's sound port (the port must not be covered, `buzzer_12mm` notes). |
| **F6** | Print orientation: base open side up; lid plate (outer face) down. |
| **F7** | Box frame as in 1.1 (the grader normalises). |
| **F8** | The buzzer stands upright (axis +Z) beside the Nano's far end (+X side). |

---

## 4. Requirements tree

Column "Gate" names the must-pass groups of section 5; blank = scored only.

### L1.1 Nano and buzzer are laid out with USB at the open end and the buzzer beside the far end

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: the pose of M-NANO, M-BUZZ and each body's print orientation. | inspection | `layout.json` present, parses, names `arduino_nano` and `buzzer_12mm` | 3 | G0 |
| L3.1.1.1 | Layout parses; catalogue ids exist. | inspection | true | 3 | G0 |
| L2.1.2 | The Nano's USB port faces the open end of the box. | inspection | `USB_AXIS` within 1.0 degree of -X; no wall at -X | 3 | |
| L3.1.2.1 | Direction of `USB_AXIS`; presence of a wall across the -X end (V-USB-PLUG footprint). | inspection | <= 1.0 degree; no wall | 3 | |
| L2.1.3 | The buzzer lies beside the Nano's far end, clear of it, inside the cavity. | analysis | buzzer plan outline X >= 47.0 (Nano far edge 45.0 plus 2.0); inside(M-BUZZ, V-CAVITY, 0.5); no collision (R6) | 2 | |
| L3.1.3.1 | Distance from the buzzer to the Nano's component keep-out. | analysis | >= 2.0 | 2 | |
| L3.1.3.2 | The buzzer inside the cavity. | analysis | d >= 0.5 | 2 | |

### L1.2 The Nano rests on four standoffs, located by pins, with the tails clear

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Four standoffs, one under each board hole, OD 3.0 to 4.0, tops coplanar, each touching the board only inside its V-SEAT column. | inspection | count = 4; each axis within 0.25 of its `HOLE`-k; OD 3.0 to 4.0; top-Z spread <= 0.10; top within 0.10 of `PCB_BOTTOM` | 3 | G2 |
| L3.2.1.1 | Exactly 4 standoffs. | inspection | count = 4 | 3 | G2 |
| L3.2.1.2 | Standoff axes vs the seated RBA's holes. | analysis | each offset <= 0.25 | 3 | G2 |
| L3.2.1.3 | Standoff OD (smallest enclosing circle). | inspection | 3.0 <= OD <= 4.0 | 2 | |
| L3.2.1.4 | Top-plane spread and height of the four tops. | inspection | spread <= 0.10; each within 0.10 of `PCB_BOTTOM` | 2 | |
| L2.2.2 | A locator pin on each standoff passes through the hole. | inspection | pin Ø 1.4 to 1.6; pin top at least 3.0 above `PCB_TOP`; radial gap to the hole 0.05 to 0.15 | 3 | |
| L3.2.2.1 | Pin diameter (largest inscribed circle of the section at mid-height). | inspection | 1.4 <= Ø <= 1.6 | 3 | |
| L3.2.2.2 | Pin height above `PCB_TOP`; pin tip below the lid underside. | inspection | height >= 3.0; tip >= 0.5 below the lid underside | 2 | |
| L3.2.2.3 | The pin stays engaged if the Nano lifts until it touches the lid: pin height above `PCB_TOP` >= (lid underside Z - 5.5) + 0.5. | analysis | true | 2 | |
| L3.2.2.4 | float(X) and float(Y) with the pins (lid closed). | analysis | <= 0.4 each | 2 | |
| L2.2.3 | The standoffs are fused to the floor; the base is one body. | analysis | contact per standoff >= 8 mm2; base connected | 2 | |
| L3.2.3.1 | Standoff-to-floor contact. | analysis | >= 8.0 mm2 each | 2 | |
| L2.2.4 | The header bodies and pin tails are clear of the base: standoffs at least as tall as the tail zone. | analysis | clear_of(ALL, V-KO-BOT, 0.0); standoff height above the floor top >= 8.8 and <= 12.0 | 3 | G2 |
| L3.2.4.1 | Tail keep-out clear. | analysis | d >= 0.0 | 3 | G2 |
| L3.2.4.2 | Standoff height above the floor top (own-model proxy). | inspection | 8.8 <= h <= 12.0 | 2 | |

### L1.3 The Nano fits with 0.5 mm clearance and 1.0 mm below the lid

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Closed: no body enters the zone above the Nano's tallest part (5.5) plus 1.0, except the locator pins. | analysis | clear_of(ALL minus the pins, V-KO-TOP, 0.0) | 3 | G2 |
| L3.3.1.1 | Top keep-out clear. | analysis | d >= 0.0 | 3 | G2 |
| L3.3.1.2 | Lid plate underside above the PCB top (own-model proxy). | inspection | Z >= 6.5 | 2 | |
| L2.3.2 | Closed: no printed body comes within 0.5 of the Nano except its standoffs and pins. | analysis | clear_of(ALL minus standoffs and pins, M-NANO, 0.5) | 3 | G2 |
| L3.3.2.1 | Nano clearance, all faces. | analysis | d >= 0.50 | 3 | G2 |
| L3.3.2.2 | A 45 x 18 x 1.6 box fits the base cavity with 0.5 clearance (own-model proxy). | demonstration | `fits` passes | 2 | |
| L2.3.3 | Along Y the cavity takes the board with margin. | inspection | inner Y width >= 18.0 + 2 x 0.5 = 19.0 | 2 | |
| L3.3.3.1 | Inner Y width between the long walls at board height. | inspection | >= 19.0 | 2 | |

### L1.4 The buzzer sits in a pocket on a ledge ring

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | A pocket takes the buzzer with a small radial clearance. | inspection | pocket Ø 12.4 +/- 0.2 (radial gap 0.1 to 0.3); depth from the ledge 2.5 to 4.0; coaxial with the declared buzzer <= 0.25 | 3 | |
| L3.4.1.1 | Pocket diameter (largest inscribed circle, mid-depth). | inspection | 12.2 <= Ø <= 12.6 | 3 | |
| L3.4.1.2 | Pocket depth above the ledge. | inspection | 2.5 <= depth <= 4.0 | 2 | |
| L2.4.2 | A ledge ring carries the buzzer rim and leaves the leads free. | analysis | ledge ID 8.0 to 10.0; ledge top within 0.10 of the buzzer base; clear_of(ALL, V-LEAD-1 and V-LEAD-2, 0.0) | 3 | |
| L3.4.2.1 | Ledge inner diameter. | inspection | 8.0 <= ID <= 10.0 | 2 | |
| L3.4.2.2 | Ledge top vs the declared buzzer base (seating rule). | analysis | <= 0.10 | 3 | |
| L3.4.2.3 | Lead zones clear. | analysis | d >= 0.0 | 3 | |
| L2.4.3 | The buzzer is seated: no collision with the printed bodies. | analysis | intersection of M-BUZZ with ALL <= 0.01 mm3; float(X), float(Y) <= 0.6 | 3 | |
| L3.4.3.1 | Penetration of M-BUZZ into ALL. | analysis | <= 0.01 mm3 | 3 | |
| L2.4.4 | Material around the pocket. | analysis | sleeve wall (pocket to outer surface or any hole) >= 1.6 | 1 | |
| L3.4.4.1 | Minimum sleeve wall. | analysis | >= 1.6 | 1 | |

### L1.5 The USB end is open: a mini-USB plug seats, also while the lid slides

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Lid closed: the plug pushes in to full mate and pulls out without touching the box. | test | clear_of(ALL, V-USB-PLUG, 0.3) | 3 | G3 |
| L3.5.1.1 | USB plug envelope clear. | test | d >= 0.30 | 3 | G3 |
| L3.5.1.2 | Physical: print, close, plug in the owner's cable. | test | clicks in fully, 3 of 3 tries | 2 | optional |
| L2.5.2 | The end is open: no wall or lid material crosses the plug footprint at -X, and the base ends no more than 3.3 beyond the receptacle front. | inspection | V-USB-PLUG footprint (Y 3.5 to 14.5, Z -0.45 to 7.55, X < -0.7) free of printed material; the base's -X edge at X >= -4.0 (receptacle front -0.7 minus 3.3) | 2 | |
| L3.5.2.1 | Base -X edge position; free footprint. | inspection | edge X >= -4.0; footprint free | 2 | |
| L2.5.3 | Lid closed: the lid's -X end stays clear of the plug overmold's face. | analysis | gap from the lid's -X end face to X = -2.2 (the overmold face) >= 0.3 | 2 | |
| L3.5.3.1 | Lid -X end vs the overmold face. | analysis | X_lid >= -1.9 | 2 | |

### L1.6 Dovetail rails on the base, matching grooves in the lid, 0.25 mm fit clearance

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | One dovetail rail on the outside of each long wall, running at least 40.0 along X. | inspection | count 2, one per long wall; length >= 40.0 | 3 | |
| L3.6.1.1 | Rail count and walls. | inspection | 2; one per long wall | 3 | |
| L3.6.1.2 | Rail length along X. | inspection | >= 40.0 | 2 | |
| L2.6.2 | Profile: flank 60 degrees from horizontal, rail 3.0 to 4.0 tall, overhanging the wall by at least 1.2 at the top. | inspection | angle 60 +/- 5; height 3.0 to 4.0; overhang >= 1.2 | 3 | |
| L3.6.2.1 | Flank angle of each rail (slice in the Y-Z plane at mid-length, fit the undercut face). | inspection | 55 to 65 | 3 | |
| L3.6.2.2 | Rail height. | inspection | 3.0 <= h <= 4.0 | 2 | |
| L3.6.2.3 | Overhang of the rail top beyond the wall's outer face. | inspection | >= 1.2 | 2 | |
| L2.6.3 | Fit: the horizontal gap between each rail flank and the lid groove flank is 0.25 per flank, and no other gap between rail and lid (resting contact excepted) is below 0.15. | analysis | 0.25 +/- 0.05 on all four flanks; min other gap >= 0.15 | 3 | G4 |
| L3.6.3.1 | Flank gap along Y by ray casting at mid-flank, every 5 mm of rail length (min, median, max). | analysis | 0.20 <= gap <= 0.30 | 3 | G4 |
| L3.6.3.2 | Minimum gap between lid and base outside the rim contact. | analysis | >= 0.15 | 2 | |
| L2.6.4 | The dovetail locks the lid vertically: lifting the lid straight up makes each rail collide with its groove. | analysis | lift LID +Z 1.0: penetration >= 0.5 mm3 at each rail | 3 | G4 |
| L3.6.4.1 | Lift test per rail. | analysis | each >= 0.5 mm3 | 3 | G4 |
| L2.6.5 | Thin-section limits: the lid skirt and the base wall under the rail are not thin. | analysis | thinnest lid skirt section >= 1.6; wall under the rail >= 2.0 | 1 | |
| L3.6.5.1 | Skirt and wall thickness by ray casting. | analysis | >= 1.6; >= 2.0 | 1 | |

### L1.7 The lid is a separate body that slides on and off along X and stops at the far wall

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Base and lid are separate bodies, each one connected body, not interpenetrating when closed. | analysis | BASE 1 shell; LID 1 shell; BASE and LID intersection <= 1.0 mm3 | 3 | G1 |
| L3.7.1.1 | Shell count per body. | analysis | 1; 1 | 3 | G1 |
| L3.7.1.2 | Base-lid intersection, closed (penetration only). | analysis | <= 1.0 mm3 | 3 | G1 |
| L2.7.2 | The lid slides off to -X by 70.0 without hitting the base, the Nano, the buzzer or a plugged-in cable. | test | slide(LID, -X, 70): BASE penetration <= 0.01 mm3 at every step, min gap >= 0.15 outside the rim contact; clear_of(LID path, RBA and V-USB-PLUG, 0.3) | 3 | G4 |
| L3.7.2.1 | Slide sweep against BASE. | test | every step <= 0.01 mm3; gap >= 0.15 | 3 | G4 |
| L3.7.2.2 | Slide sweep against the RBA and the plug envelope. | test | d >= 0.30 at every step | 3 | |
| L2.7.3 | A travel stop: the far end wall stops the lid. | analysis | closed-pose gap from the lid end face to the stop <= 0.3; slide(LID, +X, 1.0) penetrates the stop >= 0.05 mm3 | 2 | |
| L3.7.3.1 | Gap lid end face to stop face. | analysis | 0.0 <= gap <= 0.3 | 2 | |
| L3.7.3.2 | +X slide test. | analysis | >= 0.05 mm3 | 2 | |
| L2.7.4 | The lid covers the Nano and the buzzer in plan. | analysis | lid plan outline contains the Nano footprint and the buzzer footprint with 1.0 margin | 2 | |
| L3.7.4.1 | Plan containment margin. | analysis | >= 1.0 each | 2 | |
| L2.7.5 | The lid rests on the walls: underside within 0.3 of the wall tops. | inspection | lid underside Z minus rim top Z in [0.0, 0.3] | 1 | |
| L3.7.5.1 | Rim gap. | inspection | 0.0 <= gap <= 0.3 | 1 | |

### L1.8 Sound holes over the buzzer, and the sound port uncovered

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | A central hole over the buzzer's sound port. | inspection | Ø 2.0 to 3.5, axis within 0.3 of `SOUND_PORT` | 3 | G5 |
| L3.8.1.1 | Central hole diameter and position (largest inscribed circle; axis vs `SOUND_PORT`). | inspection | 2.0 <= Ø <= 3.5; offset <= 0.3 | 3 | G5 |
| L2.8.2 | A ring of at least six equal holes centred on the buzzer axis. | inspection | N >= 6; each Ø 1.5 to 2.5; ring circle Ø 7.0 to 10.0, centred on the buzzer axis within 0.3; every hole inside the buzzer's Ø12 plan outline; angular spacing within 3 degrees of 360/N | 3 | G5 |
| L3.8.2.1 | Ring hole count. | inspection | N >= 6 | 3 | G5 |
| L3.8.2.2 | Ring hole diameters. | inspection | 1.5 <= Ø <= 2.5 | 2 | |
| L3.8.2.3 | Ring circle diameter and centring. | inspection | 7.0 <= D <= 10.0; offset <= 0.3 | 2 | |
| L3.8.2.4 | Angular spacing error. | inspection | <= 3 degrees | 1 | |
| L2.8.3 | Material between the holes. | analysis | ligament between neighbouring holes and to the central hole >= 1.0 | 2 | |
| L3.8.3.1 | Minimum ligament in the hole pattern. | analysis | >= 1.0 | 2 | |
| L2.8.4 | The lid underside sits 0.5 to 1.5 above the buzzer top (acoustic gap), with nothing else in the air above the port. | analysis | 0.5 <= (lid underside Z - `TOP`) <= 1.5; clear_of(ALL minus the lid plate, V-SOUND-GAP, 0.0) | 3 | G5 |
| L3.8.4.1 | Lid underside minus buzzer top. | analysis | 0.5 <= g <= 1.5 | 3 | G5 |
| L3.8.4.2 | The gap volume is empty. | analysis | d >= 0.0 | 2 | |
| L2.8.5 | Enough open area. | analysis | total area of the holes in the lid within the buzzer's plan >= 15 mm2 | 1 | |
| L3.8.5.1 | Open area. | analysis | >= 15 mm2 | 1 | |

### L1.9 Closed except the open end and the sound holes, with 2.0 to 4.0 mm walls

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The only openings are the open -X end, the sound holes and the lid's sliding seam (the dovetail gaps). | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into V-CAVITY other than through the open end, the sound holes and the 0.25 dovetail seam (a sphere does not fit the seam) | 2 | |
| L3.9.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 | |
| L2.9.2 | Walls, floor, far wall and lid plate are 2.0 to 4.0 thick. | inspection | each in [2.0, 4.0] | 2 | |
| L3.9.2.1 | Each side wall's median thickness (ray casting away from features). | inspection | 2.0 <= t <= 4.0 | 2 | |
| L3.9.2.2 | Floor thickness; far wall thickness. | inspection | 2.0 <= t <= 4.0 | 2 | |
| L3.9.2.3 | Lid plate thickness. | inspection | 2.0 <= t <= 4.0 | 2 | |
| L2.9.3 | Each wall joins the floor along its length. | analysis | contact >= 90 percent of wall length x thickness | 2 | |
| L3.9.3.1 | Wall-to-floor contact. | analysis | >= 0.9 x L x t | 2 | |

### L1.10 Both parts print without supports

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | In its stated print orientation (F6), no unsupported overhang steeper than 45 degrees from vertical, except round holes Ø <= 12 in vertical walls and bridges <= 15. | analysis | 0 offending faces (area > 1 mm2) | 2 | |
| L3.10.1.1 | Overhang and bridge scan per part (E1 rubric 3.6); the dovetail flanks are the faces most at risk. | analysis | 0 patches | 2 | |
| L2.10.2 | Each part's mesh is manifold and a single shell. | analysis | 1 shell; manifold3d accepts it | 3 | G1 |
| L3.10.2.1 | Shell count and manifold status per body. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.10.3 | Each part rests on a flat face. | analysis | bed contact >= 50 percent of the plan bounding box | 1 | |
| L3.10.3.1 | Bed contact per part. | analysis | >= 50 percent | 1 | |
| L2.10.4 | No feature thinner than 0.8; mating clearances >= 0.15. | analysis | min thickness >= 0.8; min mating gap >= 0.15 | 1 | |
| L3.10.4.1 | Thin-feature and mating-gap scan. | analysis | as stated | 1 | |
| L2.10.5 | Each part fits a 200 x 200 x 200 build volume. | inspection | bounding box <= 200 per axis | 1 | |
| L3.10.5.1 | Bounding box per part. | inspection | <= 200 per axis | 1 | |

### L1.11 Compact and stable: at most 80 x 40 x 30, flat on a table

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Closed outside size. | inspection | X <= 80.0, Y <= 40.0, Z <= 30.0 (X the slide axis) | 1 | |
| L3.11.1.1 | Assembly bounding box. | inspection | as stated | 1 | |
| L2.11.2 | It stands on its base without tipping, also under a 0.5 N sideways pull at the USB axis. | analysis | stable at 5 degrees tilt; restoring moment > tipping moment (mass 60 g) | 1 | |
| L3.11.2.1 | `stable` at 5 degrees; tipping margin at the USB axis. | analysis | passes; margin > 0 | 1 | |
| L2.11.3 | Flat underside. | inspection | flatness <= 0.2; nothing below the floor except equal feet <= 3.0 | 1 | |
| L3.11.3.1 | Underside planarity. | inspection | as stated | 1 | |

### L1.12 The Nano and the buzzer drop in with the lid off

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | Lid off: the Nano drops straight down (-Z) onto its standoffs, the pins entering the holes, without touching anything. | test | clear_of(BASE, V-INSTALL-N, 0.2) with V-SEAT and V-HOLECOL excluded | 2 | |
| L3.12.1.1 | Nano installation path clear. | test | d >= 0.20 | 2 | |
| L2.12.2 | Lid off: the buzzer drops straight down into its pocket. | test | clear_of(BASE, V-INSTALL-B, 0.1) with the pocket-and-ledge seat excluded | 2 | |
| L3.12.2.1 | Buzzer installation path clear. | test | d >= 0.10 | 2 | |
| L2.12.3 | The lid is not needed to hold the Nano: with the lid off the Nano still sits on its standoffs, located by the pins. | inspection | seated; float(X), float(Y) <= 0.4 | 1 | |
| L3.12.3.1 | float(X), float(Y), lid off. | analysis | <= 0.4 each | 1 | |

### L1.13 The design package says what was built, and its own claims are true

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | The package holds: `base.stl`, `lid.stl` (closed assembly pose, mm), the `.scad` source, `layout.json` (L2.1.1) and the agent's own clearance report. | inspection | all present and readable | 3 | G0 |
| L3.13.1.1 | Files present and parse; STLs in mm: each part's largest bounding-box axis is 20 to 200. | inspection | true | 3 | G0 |
| L3.13.1.2 | The declared layout verifies under the seating rule (section 2.3). | analysis | board on standoff tops <= 0.10; hole-axis residual <= 0.25; buzzer on the ledge <= 0.10 | 3 | |
| L2.13.2 | The agent's own report agrees with the judge's measurements. | analysis | for every clear_of / inside L3 the agent reports, same pass/fail and \|d_agent - d_judge\| <= 0.10 | 1 | |
| L3.13.2.1 | Self-report vs judge. | analysis | 100 percent agreement within 0.10 | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 13 |
| L2 | 48 |
| L3 | 76 (1 physical) |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.1.1.1, L3.13.1.1);
**G1** manifold and two separate bodies (L3.10.2.1, L3.7.1.1, L3.7.1.2); **G2** the Nano is seated
and clear (L3.2.1.1, L3.2.1.2, L3.2.4.1, L3.3.1.1, L3.3.2.1); **G3** the USB plug seats (L3.5.1.1);
**G4** the dovetail fits and the lid slides (L3.6.3.1, L3.6.4.1, L3.7.2.1); **G5** the sound path is
open (L3.8.1.1, L3.8.2.1, L3.8.4.1).

---

## 6. Feasibility: a design that meets every number

One concrete design, hand-checked against the bands (box frame, mm; the loop does not get it).

**Base.** X -3.0 to 64.2, Y -3.4 to 21.4. Floor Z -11.4 to -9.0 (2.4). Long walls 2.4 thick (Y -3.4 to -1.0
and 19.0 to 21.4), top at Z 7.9. Cavity Y -1.0 to 19.0 (inner width 20.0 >= 19.0, gap 1.0 each side to the
board), open at -X over the whole end, closed by a far wall X 61.8 to 64.2 rising to Z 10.3 (the travel stop).
No end wall at -X.

**Nano.** Four standoffs OD 3.8 from the floor top (Z -9.0) to Z 0 (height 9.0 in 8.8 to 12.0; 0.5 clear of the tail
bottom at Z -8.5) at (0.9, 1.38), (44.1, 1.38), (0.9, 16.62), (44.1, 16.62): X to 2.8 (header strip starts
3.45, strip + 0.3 starts 3.15) and from 42.2 (strip ends 41.55, +0.3 = 41.85). Pins Ø1.5 (hole 1.7, gap 0.1) up to
Z 5.1 (3.5 above `PCB_TOP`; lift limit before the lid: 7.9 - 5.5 = 2.4, so 3.5 >= 2.4 + 0.5). Lid underside
at Z 7.9: above V-KO-TOP (6.5) by 1.4, and 0.35 above the plug overmold top (7.55).

**Buzzer.** Axis (54.0, 9.0): X 48.0 to 60.0, 3.0 beyond the Nano keep-out (>= 2.0). Sleeve OD 16.4 (wall 2.0)
from the floor to Z 1.4, pocket Ø12.4 (gap 0.2) from the ledge at Z -1.6 up to Z 1.4 (depth 3.0), ledge ring
Ø9.0 to Ø12.4 on a tube of ID 9.0 down to the floor (the leads at X 50.75 and 57.25 sit 3.25 from the axis, inside Ø9.0).
Buzzer base Z -1.6, top Z 6.9; lid underside 7.9 gives the 1.0 acoustic gap. The sleeve starts at X 45.8
(0.8 from the PCB edge) and merges with the far wall (sleeve to X 62.2, 0.4 into the wall).

**Dovetail.** Each long wall carries a rail Z 4.9 to 7.9 (3.0 tall) with the undercut flank at 60 degrees from horizontal:
the top overhangs the wall's outer face by 3.0 / tan 60 = 1.73 (>= 1.2). Lid: plate Z 7.9 to 10.3 (2.4), X -1.9
to 61.6, Y -7.38 to 25.38; skirts hang outside each wall to Z 4.6 with the groove flank offset 0.25
horizontally from the rail flank (inner face +0.25 from the wall below the rail, +1.98 at the top; skirt
outer face 3.98 from the wall, thinnest section 2.0 at the top). Rail length X -3.0 to 61.8 = 64.8 (>= 40.0). Stop gap 0.2
(lid ends at 61.6, wall at 61.8). Lid plan margin to the buzzer (X to 60.0): 1.6 >= 1.0; to the Nano's receptacle front (-0.7): 1.2. Lid -X end at -1.9: 0.3 from the overmold face (-2.2).

**Sound holes.** Central Ø2.5 at (54.0, 9.0); ring of 8 holes Ø2.0 on a Ø8.0 circle (45 degrees apart); hole
ligament 3.06 - 2.0 = 1.06 >= 1.0; central to ring 4.0 - 1.0 - 1.25 = 1.75; holes stay within the Ø12 plan (4.0 + 1.0 = 5.0 < 6.0);
total area 4.9 + 8 x 3.14 = 30 mm2 >= 15.

**Size and print.** Closed bounding box X -3.0 to 64.2 (67.2), Y -7.38 to 25.38 (32.8), Z -11.4 to 10.3 (21.7):
within 80 x 40 x 30. Base prints open side up: rail undersides 60 degrees, sleeve and tube vertical, far
wall vertical. Lid prints plate down: skirts rise; the groove flank faces downward at 60 degrees from horizontal.
Bed contact about 90 percent each.

---

## 7. Traceability

| L1 | Owner need (from the brief) | L2 | L3 | JSON L1 | Words in the brief it comes from |
|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1-L2.1.3 | L3.1.1.1, L3.1.2.1, L3.1.3.1-2 | L1.1 | "Arduino Nano and a 12 mm piezo buzzer", "mini-USB end" |
| L1.2 | Nano seated | L2.2.1-L2.2.4 | L3.2.1.1-4, L3.2.2.1-4, L3.2.3.1, L3.2.4.1-2 | L1.2 | "standoffs" (capability list), implied |
| L1.3 | Nano fits | L2.3.1-L2.3.3 | L3.3.1.1-2, L3.3.2.1-2, L3.3.3.1 | L1.3 | "Arduino Nano" |
| L1.4 | Buzzer seat | L2.4.1-L2.4.4 | L3.4.1.1-2, L3.4.2.1-3, L3.4.3.1, L3.4.4.1 | L1.4 | "12 mm piezo buzzer" |
| L1.5 | USB open end | L2.5.1-L2.5.3 | L3.5.1.1-2, L3.5.2.1, L3.5.3.1 | L1.5 | "The mini-USB end stays open" |
| L1.6 | Dovetail | L2.6.1-L2.6.5 | L3.6.1.1-2, L3.6.2.1-3, L3.6.3.1-2, L3.6.4.1, L3.6.5.1 | L1.6 | "a base with a dovetail rail", "0.25 mm fit clearance" |
| L1.7 | Sliding lid | L2.7.1-L2.7.5 | L3.7.1.1-2, L3.7.2.1-2, L3.7.3.1-2, L3.7.4.1, L3.7.5.1 | L1.7 | "the lid slides on along the long axis" |
| L1.8 | Sound holes | L2.8.1-L2.8.5 | L3.8.1.1, L3.8.2.1-4, L3.8.3.1, L3.8.4.1-2, L3.8.5.1 | L1.8 | "A ring of sound holes on the lid sits over the buzzer" |
| L1.9 | Protection | L2.9.1-L2.9.3 | L3.9.1.1, L3.9.2.1-3, L3.9.3.1 | L1.9 | "box" |
| L1.10 | Printable | L2.10.1-L2.10.5 | L3.10.1.1, L3.10.2.1, L3.10.3.1, L3.10.4.1, L3.10.5.1 | L1.10 | implied (OpenSCAD -> FDM) |
| L1.11 | Compact, stable | L2.11.1-L2.11.3 | L3.11.1.1, L3.11.2.1, L3.11.3.1 | L1.11 | implied (A9) |
| L1.12 | Assembly | L2.12.1-L2.12.3 | L3.12.1.1, L3.12.2.1, L3.12.3.1 | L1.12 | implied |
| L1.13 | Evidence | L2.13.1-L2.13.2 | L3.13.1.1-2, L3.13.2.1 | L1.13 | needed by the judge |

---

## 8. Grading supplement (design-specific; `generalize/rubric.md` did not exist when this was written)

Procedure, recipes and report format are those of `benchmarks/enclosure/rubric.md` (sections 2, 3 and 5),
applied to the base and lid STLs, with these specifics:

1. **Inputs.** `base.stl`, `lid.stl` (closed pose, mm), `.scad`, `layout.json`, self-report, renders. The
   judge does not use the agent's code or transcript, earlier verdicts, or `benchmarks/heldout.json`.
2. **Normalise the frame** (1.1): USB end at -X, floor below Z = 0, the lid above the base. Record the transform.
3. **Build references independently** from the catalogue (M-NANO, M-BUZZ, M-PLUG-USB), then the V-
   envelopes (2.2), sanity checks R1 to R7 and the seating rule (2.3).
4. **Recipes.** `clear_of`, `inside` and apertures as E1 rubric 3.2 to 3.4. `slide`: translate the LID
   mesh in 1.0 mm steps; at each step take `(LID ^ BASE).volume()` and `LID.min_gap(BASE, 1.0)`. The dovetail
   flank gap: slice the closed pose at X = mid-lid in the Y-Z plane, then ray cast along Y from the rail flank to
   the groove flank at five heights; the flank angle from the slice polygon's undercut edge. Pin, pocket,
   sleeve and standoff diameters: slice at mid-height and fit circles (largest inscribed for holes, smallest
   enclosing for bosses). Ring holes: slice the lid plate at mid-thickness, take each hole polygon's centroid and
   inscribed circle, then the ring circle and angular spacing about the buzzer axis.
5. **Classes.** WRONG = any gate (G0 to G5) fails. MINOR = no gate fails but a weight-3 L3 fails. CORRECT =
   no gate fails and every weight-3 L3 passes. **MEETS** = CORRECT and every applicable non-physical L3 of
   weight 1 and 2 passes. UNVERIFIED counts as FAIL; physical L3s are N/A unless a print was made. Report the
   weighted score and the worst normalised margin among weight-3 L3s.
6. **Precedence.** The plug-seating and slide checks (L3.5.1.1, L3.7.2.1) outrank everything about opening
   size and compactness. The numbers in this file beat `part.json`: if a catalogue value disagrees, build from
   this file and record a defect on the requirement the stale value breaks, with where = the part.json field.
   Designed contact (1.4) is never interference. Never relax a criterion, never round in the design's favour
   beyond e, never infer a pass from a render.
7. **WHERE a defect is.** One entry per failed or UNVERIFIED L3, most severe first (gates, then weight 3, 2, 1):
   `req` (L3, L2, L1), `status`, `body` (base, lid, both, layout), `feature` (named by function and SCAD name,
   for example "dovetail rail on the +Y wall (`rail_pos`)"), `face` (surface and outward normal), `location`
   (box-frame coordinates, a point or a box), `measured` / `limit` / `margin`, `reference` (the M- or V- involved
   and its datum), `render`, `evidence` (saved defect STL), `needed` (a numeric target, never a design
   instruction). Group L3s that fail for one geometric reason, keeping every id.
8. **Measured-values table (always filled in).**

| Quantity | Limit | Measured |
|---|---|---|
| Standoff count; axis offset; OD; height (L3.2.1.x, L3.2.4.2) | 4; <= 0.25; 3.0 to 4.0; 8.8 to 12.0 | |
| Pin Ø; height above PCB top; float X / Y (L3.2.2.x) | 1.4 to 1.6; >= 3.0; <= 0.4 | |
| Tail keep-out d; top keep-out d (L3.2.4.1, L3.3.1.1), mm | >= 0; >= 0 | |
| Nano clearance to any surface (L3.3.2.1), mm | >= 0.5 | |
| Buzzer pocket Ø; depth; ledge ID; lead zone d (L3.4.x) | 12.2 to 12.6; 2.5 to 4.0; 8.0 to 10.0; >= 0 | |
| USB plug d (L3.5.1.1), mm; base -X edge; lid -X end | >= 0.3; >= -4.0; >= -1.9 | |
| Rails: count; length; angle; height; overhang (L3.6.1.x, L3.6.2.x) | 2; >= 40.0; 55 to 65; 3.0 to 4.0; >= 1.2 | |
| Flank gap min / median / max (L3.6.3.1), mm | 0.20 to 0.30 | |
| Lift-test intersection per rail (L3.6.4.1), mm3 | >= 0.5 | |
| Slide sweep: max intersection; min gap; d to RBA and plug (L3.7.2.x) | <= 0.01; >= 0.15; >= 0.30 | |
| Stop gap; +X test (L3.7.3.x) | 0.0 to 0.3; >= 0.05 mm3 | |
| Central hole Ø and offset; ring N, Ø, circle, spacing (L3.8.x) | 2.0 to 3.5, <= 0.3; >= 6, 1.5 to 2.5, 7.0 to 10.0, <= 3 degrees | |
| Acoustic gap; ligament; open area (L3.8.3.1, L3.8.4.1, L3.8.5.1) | 0.5 to 1.5; >= 1.0; >= 15 mm2 | |
| Unlisted openings (L3.9.1.1) | 0 | |
| Wall / floor / far wall / lid plate thickness (L3.9.2.x), mm | 2.0 to 4.0 | |
| Shells base / lid (L3.10.2.1) | 1 / 1 | |
| Overhang patches; bed contact (L3.10.x) | 0; >= 50 percent | |
| Closed envelope X x Y x Z (L3.11.1.1), mm | <= 80 x 40 x 30 | |
| Install sweep d: Nano / buzzer (L3.12.x), mm | >= 0.2 / >= 0.1 | |
| Self-report agreement (L3.13.2.1) | 100 percent within 0.10 | |

---

## Audit

Adversarial audit (second agent). `arduino_nano`, `buzzer_12mm` and `plug_miniusb_b` load and pass `parts.gate`. L1 = 13, L2 = 48, L3 = 76 recounted from the tables (match section 5 and the traceability table). Recomputed from `part.json`: receptacle X -0.7 to 8.3 / Y 5.15 to 12.85 / Z to 5.5; header strips X 3.45 to 41.55, Y 0.11 to 2.65 and 15.35 to 17.89; tails to Z -8.5; V-KO-TOP to 6.5; V-KO-BOT strips 3.15 to 41.85; overmold face X -2.2 and top Z 7.55; standoff and sleeve positions; dovetail overhang 3.0 / tan 60 = 1.73; lift-test wedge volume about 5.9 mm3 (>= 0.5). Section 6 was walked against every gate and band.

| # | Defect found | Fix |
|---|---|---|
| 1 | Feasibility design failed L3.7.4.1 (lid plan margin >= 1.0 around the buzzer): lid ended at X 60.8 and the buzzer reaches X 60.0, a margin of 0.8. The section 6 design therefore did not satisfy every row. | Far wall moved to X 61.8 to 64.2 and lid end to 61.6 (stop gap still 0.2; margin 1.6); rail length 64.8; closed size 67.2 x 32.8 x 21.7 and A9's "tight design" text updated. The default buzzer position (A4) is unchanged. |
| 2 | Numbers a gate or weight 2-3 row needs but the agent was never told: plug clearance 0.3 (G3) and the lid-vs-overmold 0.3 (G4), standoff OD and height band, pin diameter and height, float 0.4, Y width 19.0, pocket depth, ledge ID, sleeve 1.6, base -X limit, lid stop 0.3 / covers 1.0 / rim 0.3, rail length / height / overhang / flank angle / flank gap band / other gap 0.15 / skirt 1.6, sound-hole diameters, ring circle, ligament 1.0, open area 15, install clearances 0.2 and 0.1, 0.10 self-report. | Added to the L1 texts in `design.json` (L1.2 to L1.8, L1.12, L1.13). No L3 band changed. |
| 3 | Noted, not changed: the lid plate underside (7.9) is only 0.35 above the overmold top (7.55) while the slide test needs 0.3, so the lid height is nearly forced; the L1.5 text now states the 0.3 so the agent can derive it from the plug part. | None needed. |

Residual uncertainty: the plug overmold size and the buzzer lead length are catalogue assumptions (cables and buzzers vary); standoffs overlap the Nano's short edge by 1.0 mm (A1), as the catalogue states.
