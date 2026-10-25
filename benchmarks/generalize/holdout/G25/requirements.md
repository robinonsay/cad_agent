# G25 PVC pipe clamp to 2020 profile: requirements (L1 / L2 / L3)

A held-out entry of the generalization benchmark (`benchmarks/generalize/`). It is modelled on E1-01
(`benchmarks/enclosure/requirements.md`): the machine-readable request (L1 only, `dev.json`
format) is `design.json` next to this file, this file holds the L2/L3 tree, the reference models,
the assumptions, the fixed decisions, a feasibility sketch, the traceability and the design-specific
judging rules (section 8). The catalogue parts are in `benchmarks/generalize/parts/` (`generic_tube`,
`extrusion_2020`, `bolt_m4_iso4762`, `nut_m4`, `bolt_m5_iso7380`, `tnut_2020_m5`). No number here
may appear in agent logic: they live in the request, this file, `design_rules.json` generic values
and `part.json` data.

**Request (plan brief, verbatim):** "A clamp holds a 32 mm outside diameter PVC pipe to the face
of a 2020 extrusion. It is a two-piece strap with M4 bolts and captive nuts, and the clamp ID
should be 32.3 mm so the bolts close a 0.5 mm gap. A back plate takes two M5 bolts into the T-slot."

**Expanded request** (the text the agent gets, `design.json`): A clamp holds a 32 mm outside diameter PVC pipe to the face of a 2020 aluminium extrusion. The pipe runs parallel to the extrusion, with its axis 18 to 30 mm out from the face the clamp is mounted on (the extrusion is 100 mm long and I treat the pipe as a solid rod for the design). The clamp is a two-piece strap: a saddle with a back plate, and a cap, printed separately and joined by two M4 bolts that thread into captive hex nuts. The clamp bore is 32.3 mm so that the bolts close a 0.5 mm gap between the two pieces and squeeze the pipe. The back plate takes two M5 bolts into drop-in T-nuts in the slot of that extrusion face. It is printed on an FDM printer in PLA or PETG without supports, no bigger than 80 mm along the extrusion, 70 mm across it and 60 mm out from its face, and I need to reach every bolt with a hex key.

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check Python can run on the delivered STLs. Every row has a
verification method, a pass/fail criterion with a number and a tolerance, a weight (3 = critical,
2 = major, 1 = minor) and, for must-pass rows, a gate mark. Numbers that come from an assumption
(section 3) are provisional until Robin confirms them. Do not relax a criterion because a design
fails it.

---

## 1. Frames, tolerances and the interference checks

### 1.1 Frames

- **Clamp frame = extrusion frame (all tables below):** origin at the centre of the extrusion's start end face; **Z along the extrusion** (0 to 100); the clamp is mounted on the **+X face** (plane X = 10) whose slot faces +X, centred on Y = 0. **u = +X** is the clamp direction (away from the face): the saddle is on the face side and the cap on the outer side. A design delivered mirrored or rotated is normalised into this frame before grading (rubric step 3); that is never penalised.
- **Delivered pose = relaxed pose:** saddle and cap as two STLs with the 0.5 mm gap open. The **closed pose** is the cap translated by −(measured gap) along u (so the split faces touch). The agent's `layout.json` states the translation; the grader measures its own.

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
- the plate underside on the extrusion face (X = 10)
- a T-nut's bearing face against the slot lips (inner lip surface, X = 8.2) and its body in the slot
- an M5 bolt in its T-nut and its head bearing on the plate top face
- an M4 bolt in its nut, its head bearing on the cap top face (closed pose), and a nut on its pocket floor and against the pocket walls
- the cap's split face on the saddle's split face in the closed pose
- the pipe in the bore: resting on the saddle's bore surface in the relaxed pose, and in the closed pose up to 0.175 radial interference per side (preload)

For these pairs only penetration counts (an intersection volume above 0.01 mm³, unless the pair
is given a larger allowance below). A distance of zero is a pass.

`bodies` is **ALL** (saddle and cap in the pose named by the check), **SADDLE** or **CAP**.

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` in `benchmarks/generalize/parts/<part_id>/`. The only place target-specific part numbers may live.
- **envelope**: a keep-out, sweep or access volume generated by Python from datums. Never drawn by hand.
- **computed**: derived from the design (bore fit, gap, pocket, closed pose).

### 2.2 Reference models (M-)

Positions are in the clamp frame. The pipe and the fasteners are placed at the poses the design declares in `layout.json`; the table gives the constraint each pose must meet and, where it helps the grader, the pose of the feasibility sketch (section 6).

| Name | What | Source | Size and pose | Datums it carries |
|---|---|---|---|---|
| **M-EXT** | 2020 extrusion, length 100 | catalogue `extrusion_2020` (length from the request) | 20 × 20 × 100; X, Y ±10, Z 0 to 100; slot +X: opening 6.2, lips 1.8, inner width 11.0, depth 6.1 (floor X = 3.9); bore Ø4.2. **M-EXT-BOX** = the full 20 × 20 × 100 body; **M-EXT-SOLID** = M-EXT-BOX minus the four slot channels rebuilt from the part's `slot_*` params | `FACE_PX` (plane X = 10), `SLOT_PX`, `SLOT_FLOOR_PX`, `AXIS` |
| **M-PIPE** | PVC pipe as a solid rod | catalogue `generic_tube` (outer_diameter 32, inner 0, length 100, A3) | Ø32 × 100 along Z, Z 0 to 100; axis at (X_p, 0); X_p declared, X_p − 10 in [18, 30] | `AXIS` |
| **M-TNUT-1, -2** | drop-in M5 T-nut | catalogue `tnut_2020_m5` | 10.0 (along Y, across the slot) × 9.7 (along Z) × 3.5; bearing plane on the lip inner surface X = 8.2, body to X = 4.7; thread axis −X; centres at (Y = 0, Z = Z_k), Z_k declared | `BEARING`, `AXIS` |
| **M-BOLT5-1, -2** | M5 button-head bolt | catalogue `bolt_m5_iso7380` (length declared, L5) | shank Ø5.0, head Ø9.5 × 2.75; head bearing on the plate top face; axis −X on the T-nut axis | `HEAD_BEARING`, `HEAD_TOP`, `TIP`, `AXIS` |
| **M-BOLT4-1, -2** | M4 socket-head bolt | catalogue `bolt_m4_iso4762` (length declared, L4) | shank Ø4.0, head Ø7.0 × 4.0; head bearing on the cap top face (closed pose); axis −X | `HEAD_BEARING`, `TIP`, `AXIS` |
| **M-NUT4-1, -2** | M4 hex nut | catalogue `nut_m4` | AF 7.0, AC 7.66, thickness 3.2; bearing face on the pocket floor, axis along X, flats across Y | `SEAT`, `TOP`, `AXIS` |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Definition (clamp frame, mm) |
|---|---|---|
| **V-CLOSED-CAP** | cap in the closed pose | CAP translated by (−gap, 0, 0) |
| **V-PIPE-INSTALL** | pipe laid into the saddle | M-PIPE (centred on the bore axis) swept along +X from its seat to 60 above it (cap removed) |
| **V-DRIVER-M4-k** | hex key on an M4 head | Ø6.0 column on the M4 axis from the head top (`HEAD_BEARING` + 4.0) up 25 (catalogue `tool_access_height`) |
| **V-DRIVER-M5-k** | hex key on an M5 head | Ø6.0 column on the M5 axis from `HEAD_TOP` up 25, cap and pipe removed |
| **V-NUT-INSTALL-k** | nut drop path | M-NUT4 (AF 7.0 hex prism) swept from its seat along +X to 20 above the saddle split face |
| **V-BORE-FIT** | computed | least-squares circle through the arc of each half, sliced at mid grip length |
| **V-SPAN** | computed | ray cast along ±X from the bore axis in the closed pose: free distance to the cap surface and the saddle surface |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-EXT, M-PIPE | units and size | 20.0 × 20.0 × 100 ± 0.1; pipe Ø32 ± 0.05 |
| R2 | M-EXT | slot datums | opening 6.2, lip 1.8, depth 6.1 ± 0.05 |
| R3 | M-TNUT, M-BOLT5 | sizes | nut 10.0 × 9.7 × 3.5; M5 head Ø9.5 × 2.75 ± 0.05 |
| R4 | M-BOLT4, M-NUT4 | sizes | M4 head Ø7.0 × 4.0; nut AF 7.0, AC 7.66, t 3.2 ± 0.05 |
| R5 | all M- at the declared poses | no collisions | intersections ≤ 0.01 mm³ (designed-contact pairs excluded) |
| R6 | every V- envelope | datums equal the model datums it came from | ≤ 0.01 |

**Seating rule.** The grader verifies the declaration: every bolt's head-bearing plane lies on its seat (plate top, cap top in the closed pose) within 0.10; each T-nut axis is coaxial with its plate hole within 0.25 (least squares); each nut sits on its pocket floor within 0.10. If the declaration fails, the references are placed by that fit instead and the failing L3s stay failed.

---

## 3. Assumptions, fixed decisions and open questions

### 3.1 Assumptions (derived, with their uncertainty)

| # | Question | Value chosen | Why, and uncertainty |
|---|---|---|---|
| A1 | How does the pipe lie? | Parallel to the extrusion, on the slot-face plane through the extrusion axis, 18 to 30 mm out from the face. | "to the face of a 2020 extrusion" with a back plate over the slot and two bolts along the profile is most naturally a pipe running along it. **Alternative:** across the extrusion; not graded. High uncertainty. |
| A2 | Extrusion length? | 100 mm; the clamp sits at least 5 mm from each end. | None given. Only the end margins use it (L2.6.2, M5 positions). Low uncertainty. |
| A3 | Pipe model? | A solid rod Ø32, length 100 (catalogue `generic_tube`, inner diameter 0). | The brief gives only the outside diameter. A hollow PVC pipe would deform slightly under the preload; not modelled. Real pipe OD tolerance is about ±0.2 and is ignored. |
| A4 | How do the M5 bolts hold? | Into drop-in T-nuts (catalogue `tnut_2020_m5`), 3.5 mm thick, behind 1.8 mm lips. | "takes two M5 bolts into the T-slot". The lip thickness is ±0.3 (catalogue). |
| A5 | What does "ID 32.3 so the bolts close a 0.5 mm gap" mean? | The bore is one circle Ø32.3 cut across both halves while they are 0.5 mm apart (relaxed pose). Closing the gap lowers the cap by 0.5, so the bore span along u becomes 31.8, 0.2 less than the pipe: a preload of 0.10 per side along u. | **Alternative reading:** the bore is Ø32.3 when closed, leaving 0.15 per side and no grip. Rejected: a clamp must grip. Medium uncertainty. |
| A6 | Plate and cap thickness? | Plate 4.0 to 8.0 mm; wall round the bore at least 3.0 mm. | Engineering convention for PLA/PETG clamps (about 8 perimeters). Low uncertainty. |
| A7 | M4 nut pocket? | Across flats 7.4 (nut 7.0 + 0.2 trap clearance each side), depth 3.4 (catalogue `trap_clearance`, `pocket_depth`). | Catalogue values; print convention. |
| A8 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed; overhang limit 45° from vertical, bridges ≤ 15. | Common printers. |
| A9 | Hex-key access? | A Ø6.0 column, 25 mm long, along the bolt axis (catalogue `tool_access_height`). | Hex keys for M4 (3.0) and M5 (3.0) with a handle. |
| A10 | Bolt engagement? | M5: at least 3.0 mm of the 3.5 mm nut engaged and 0.5 mm clear of the slot floor (tip X in [4.4, 5.2]). M4: tip beyond the nut back face by 0.0 to 3.0. | One full thread past the nut is the convention; more is wasted. |
| A11 | Load? | Not specified; no load is graded. Ligament and wall minima stand in for strength (L1.10). | The brief gives none. Flag for Robin if the pipe carries weight. |
| A12 | Size limit? | Printed clamp ≤ 80 mm along the extrusion, 70 across, 60 out from the face. | A tight design is 70 × 55 × 45 (section 6). Low uncertainty. |

### 3.2 Fixed decisions (a choice that would otherwise be ambiguous)

| # | Decision |
|---|---|
| F1 | The split plane is parallel to the face and contains the bore axis; the saddle (with the plate) is on the face side, the cap outside. The bolts therefore run along X. |
| F2 | The delivered STLs are in the relaxed pose with the 0.5 mm gap; closing is a pure translation of the cap by −gap along X. |
| F3 | The M4 nuts sit in the saddle; the M4 bolts pass through the cap. |
| F4 | No tongue or key enters the slot: the only things in the slot are the two T-nuts and the M5 shanks. |
| F5 | The two M5 bolts are on the slot centreline (Y = 0), beyond the ends of the bore along Z, so that the pipe does not hide them; the pipe and the cap come off for M5 access (L1.9). |
| F6 | The pipe is installed along −X after the saddle is bolted on and before the cap goes on. |

---

## 4. Requirements tree

### L1.1 Layout declared, parts placed from the catalogue

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares the pose of every reference part (catalogue id, position, axis direction, length where the part has one) in the extrusion frame. | inspection | `layout.json` present, parses, names M-PIPE, M-EXT, two M-TNUT, two M-BOLT5, two M-BOLT4, two M-NUT4 from the catalogue | 3 |  |
| L3.1.1.1 | Layout file parses, every catalogue id exists, every part has a pose. | inspection | parse errors = 0; unknown ids = 0; parts without a pose = 0; 11 parts named | 3 | G0 |
| L2.1.2 | The pipe lies parallel to the extrusion, in the slot-face plane through the extrusion axis, at a distance that clears the plate and the M5 heads. | inspection | pipe axis within 0.5° of +Z; pipe axis in the plane Y = 0 ± 0.5; distance from the face plane X = 10 to the pipe axis in [18, 30] | 3 |  |
| L3.1.2.1 | Pipe axis direction and offset. | inspection | axis within 0.5° of +Z; axis plane Y = 0 ± 0.5; X_p − 10 in [18, 30] | 3 |  |
| L2.1.3 | No two reference parts collide, and no part sits on a fastener axis it does not use. | analysis | pairwise intersection of M-PIPE, M-EXT (slot channels subtracted), T-nuts, bolts, nuts ≤ 0.01 mm³ except the designed-contact pairs | 2 |  |
| L3.1.3.1 | Pairwise interference of the declared reference parts. | analysis | each pair ≤ 0.01 mm³ (designed-contact pairs excluded) | 2 |  |
| L2.1.4 | The fastener stack is declared: each M5 and M4 bolt names its catalogue length, head-bearing plane and tip. | inspection | bolt length matches the catalogue length parameter; tip = head bearing − length | 2 |  |
| L3.1.4.1 | Declared bolt lengths agree with the poses. | inspection | tip position within 0.05 of the declared length | 2 |  |

### L1.2 Round bore of 32.3 mm round the pipe

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The two halves together form one round bore of 32.3 mm, on the pipe axis. | inspection | fitted circle diameter of each half's arc = 32.3 ± 0.10; arc centre within 0.10 of the declared pipe axis (relaxed pose) | 3 |  |
| L3.2.1.1 | Bore diameter of the saddle arc. | inspection | 32.3 ± 0.10 (+ε) | 3 | G2 |
| L3.2.1.2 | Bore diameter of the cap arc. | inspection | 32.3 ± 0.10 (+ε) | 3 | G2 |
| L3.2.1.3 | Bore axis versus the declared pipe axis. | analysis | centre offset ≤ 0.10 and direction ≤ 0.5° for both arcs | 2 |  |
| L2.2.2 | The bore is long enough to hold the pipe square. | inspection | grip length (bore extent along the pipe axis) in [20.0, 40.0]; both halves equal within 0.2 | 2 |  |
| L3.2.2.1 | Bore length per half. | inspection | 20.0 to 40.0; saddle length − cap length ≤ 0.2 | 2 |  |
| L2.2.3 | The bore surface is a clean cylinder: no step or rib in it other than the split. | analysis | radial deviation of the bore surface from the fitted circle ≤ 0.15 over ≥ 90% of the grip length, away from the split lines (±1.0) | 1 |  |
| L3.2.3.1 | Bore roundness. | analysis | max radial deviation ≤ 0.15 | 1 |  |

### L1.3 Two printed pieces, saddle and cap, with a 0.5 mm gap

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The delivered STLs are the relaxed pose: saddle and cap are separate bodies, one connected shell each, not touching each other. | analysis | saddle 1 shell; cap 1 shell; saddle ∩ cap ≤ 0.01 mm³; saddle ∪ cap has 2 shells | 3 |  |
| L3.3.1.1 | Shell count and manifold status of saddle and cap. | analysis | shells = 1 each; manifold3d accepts both | 3 | G1 |
| L3.3.1.2 | Saddle and cap are separate in the delivered pose. | analysis | intersection ≤ 0.01 mm³ and min distance > 0 | 3 | G1 |
| L2.3.2 | The split faces are flat, parallel to each other and to the plate, and 0.5 mm apart; the bore axis lies in the mid-plane between them. | inspection | gap measured on both sides of the bore = 0.5 ± 0.10; split-face flatness ≤ 0.10; faces parallel within 0.5°; mid-plane to bore axis ≤ 0.15 | 3 |  |
| L3.3.2.1 | Split gap on the −Y side of the bore. | inspection | 0.5 ± 0.10 (+ε) | 3 | G2 |
| L3.3.2.2 | Split gap on the +Y side of the bore. | inspection | 0.5 ± 0.10 (+ε) | 3 | G2 |
| L3.3.2.3 | Split-face flatness, parallelism and mid-plane position. | inspection | flatness ≤ 0.10; angle ≤ 0.5°; mid-plane within 0.15 of the bore axis | 2 |  |
| L2.3.3 | The cap and the saddle have the same plan outline where they meet, so the closed clamp looks like one piece. | inspection | plan outline of the cap's split face within ±0.5 of the saddle's split-face outline on every side | 1 |  |
| L3.3.3.1 | Plan outline match at the split. | inspection | max side offset ≤ 0.5 | 1 |  |

### L1.4 Two M4 bolts into captive hex nuts

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Exactly two M4 bolt axes, parallel to the clamp direction, one each side of the bore, symmetric about the pipe's centre plane. | inspection | count = 2; axes within 1° of +X; offsets from the bore axis 21.3 to 30.0 on opposite sides, differing by ≤ 0.5 | 3 |  |
| L3.4.1.1 | Bolt-axis count, direction and offset. | inspection | count = 2; axes within 1° of +X; offsets 21.3 to 30.0 on opposite sides, differing ≤ 0.5 | 3 | G3 |
| L2.4.2 | The cap holes are plain clearance holes for M4 (catalogue clearance diameter), through the whole cap, coaxial with the pockets. | inspection | hole Ø 4.5 ± 0.10; through the cap; axis offset to the saddle pocket axis (closed pose) ≤ 0.20 | 3 |  |
| L3.4.2.1 | Cap hole diameter. | inspection | 4.5 ± 0.10 (+ε) | 3 | G3 |
| L3.4.2.2 | Cap hole and pocket coaxial in the closed pose. | analysis | ≤ 0.20 | 3 | G3 |
| L2.4.3 | Each saddle pocket holds an M4 hex nut captive: a hex pocket open only at the split face, nut flats across the pocket, nut cannot turn or fall out with the cap on. | analysis | pocket across flats 7.4 ± 0.15; depth from the split face 3.4 ± 0.2; nut (AF 7.0, thickness 3.2) seated on the pocket floor lies inside the pocket with ≤ 0.01 mm³ penetration and its top below the split face; the cap's underside covers the pocket mouth | 3 |  |
| L3.4.3.1 | Pocket across flats. | inspection | 7.4 ± 0.15 (+ε) | 3 | G3 |
| L3.4.3.2 | Pocket depth. | inspection | 3.4 ± 0.2 (+ε) | 2 |  |
| L3.4.3.3 | Nut in pocket. | analysis | penetration ≤ 0.01 mm³; nut top ≥ 0.0 below the split face | 3 | G3 |
| L3.4.3.4 | Pocket is blind towards the plate and open only at the split face. | analysis | aperture scan: 1 opening of the pocket, at the split face | 2 |  |
| L2.4.4 | The bolt stack is consistent: the closed clamp lets the bolt pass the cap, reach through the nut and stop in free space, and the head sits flat on the cap. | analysis | M4 bolt solid at its declared pose (closed pose): ∩ cap and saddle ≤ 0.01 mm³; tip beyond the nut's back face by 0.0 to 3.0; head footprint (Ø7.0) lies on the cap's top face with ≥ 0.5 margin; top-face flatness ≤ 0.2 | 3 |  |
| L3.4.4.1 | Bolt versus printed bodies, closed pose. | analysis | ≤ 0.01 mm³ each | 3 | G3 |
| L3.4.4.2 | Tip protrusion beyond the nut. | analysis | 0.0 to 3.0 | 2 |  |
| L3.4.4.3 | Head seat on the cap top face. | inspection | margin ≥ 0.5; flatness ≤ 0.2 | 2 |  |
| L2.4.5 | Closing is possible: translating the cap by the gap along −X brings the split faces into contact with no other part touching. | test | after translating the cap by −(measured gap) along the clamp direction: cap ∩ saddle ≤ 0.01 mm³; split faces within 0.05 of coplanar contact; no other printed part pair touches | 3 |  |
| L3.4.5.1 | Closed pose reachable. | test | penetration ≤ 0.01 mm³; contact distance ≤ 0.05 | 3 | G2 |

### L1.5 Closing squeezes the pipe by 0.2 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | In the closed pose, the free span of the bore along the clamp direction, through the pipe axis, is the bore diameter less the gap. | analysis | span = 31.8 ± 0.15 (ray cast along +X through the bore axis) | 3 |  |
| L3.5.1.1 | Closed-pose bore span. | analysis | 31.8 ± 0.15 (+ε) | 3 | G2 |
| L2.5.2 | The preload on the pipe stays small enough not to crush a PVC pipe and large enough to grip. | analysis | in the closed pose with the pipe centred between the arcs, the radial interference of the pipe into the saddle and into the cap is 0.10 each (band 0.025 to 0.175); total 0.20 (band 0.05 to 0.35); penetration volume is designed contact | 2 |  |
| L3.5.2.1 | Radial interference, saddle side. | analysis | 0.025 to 0.175 | 2 |  |
| L3.5.2.2 | Radial interference, cap side. | analysis | 0.025 to 0.175 | 2 |  |
| L2.5.3 | In the delivered (relaxed) pose the pipe is not gripped: it slides in with clearance. | analysis | pipe Ø32.0 centred on the bore axis: min distance to saddle ∪ cap ≥ 0.10 | 2 |  |
| L3.5.3.1 | Relaxed-pose pipe clearance. | analysis | d ≥ 0.10 | 2 |  |

### L1.6 Back plate flat on the extrusion face

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | The plate underside is one plane, on the face plane, with enough area on the face to carry the clamp. | inspection | underside flatness ≤ 0.20; plane within 0.05 of X = 10; contact area on the face ≥ 600 mm² | 3 |  |
| L3.6.1.1 | Plate underside flatness and position. | inspection | ≤ 0.20; offset ≤ 0.05 | 3 | G4 |
| L3.6.1.2 | Contact area on the face. | analysis | ≥ 600 mm² | 2 |  |
| L2.6.2 | The plate sits inside the extrusion's length with an end margin. | inspection | plate extent along Z within [5, 95]; margin to each end ≥ 5.0 | 2 |  |
| L3.6.2.1 | Plate extent along the extrusion. | inspection | min 5.0 from each end | 2 |  |
| L2.6.3 | No printed material enters the extrusion's 20 × 20 section or any of its slots. | analysis | clear_of(ALL, M-EXT-BOX, 0.0) where M-EXT-BOX is the full 20 × 20 × 100 envelope; plate underside touching the face is designed contact | 3 |  |
| L3.6.3.1 | Printed bodies outside the extrusion envelope. | analysis | penetration ≤ 0.01 mm³ | 3 | G4 |
| L2.6.4 | Plate thickness is enough for the M5 heads and the bending load. | inspection | plate thickness (X) in [4.0, 8.0] | 1 |  |
| L3.6.4.1 | Plate thickness. | inspection | 4.0 to 8.0 | 1 |  |

### L1.7 Two M5 bolts into drop-in T-nuts in the slot

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Two plain M5 clearance holes in the plate, on the slot centreline, spaced along the extrusion. | inspection | count = 2; Ø 5.5 ± 0.10; axes along X within 1°; axis offset from the slot centreline Y = 0 ≤ 0.3; spacing along Z in [40, 70]; each ≥ 10 from the extrusion ends | 3 |  |
| L3.7.1.1 | M5 hole count and diameter. | inspection | 2; 5.5 ± 0.10 (+ε) | 3 | G4 |
| L3.7.1.2 | M5 hole centreline offset and spacing. | inspection | ≤ 0.3; spacing 40 to 70 | 3 | G4 |
| L2.7.2 | Each T-nut sits in the slot, behind the lips, coaxial with its plate hole. | analysis | T-nut bearing plane at the lip inner surface (X = 8.2 ± 0.3); nut body ∩ M-EXT with the slot subtracted ≤ 0.01 mm³; T-nut axis to plate-hole axis offset ≤ 0.3 | 3 |  |
| L3.7.2.1 | T-nut in the slot channel. | analysis | penetration ≤ 0.01 mm³ | 3 | G4 |
| L3.7.2.2 | T-nut and hole coaxial. | analysis | offset ≤ 0.3 | 3 | G4 |
| L2.7.3 | Each M5 bolt engages its T-nut and clears the slot floor. | analysis | bolt tip position X in [4.4, 5.2] for the catalogue slot (derived: engagement ≥ 3.0 in the 3.5 nut means tip ≤ 8.2 − 3.0; clearance ≥ 0.5 above the slot floor at X = 3.9); bolt ∩ extrusion with slot subtracted ≤ 0.01 mm³; head bearing on the plate top face within 0.10 | 3 |  |
| L3.7.3.1 | M5 tip within the engagement window. | analysis | 4.4 to 5.2 | 3 | G4 |
| L3.7.3.2 | M5 bolt versus the extrusion. | analysis | ≤ 0.01 mm³ each | 2 |  |
| L3.7.3.3 | M5 head seat. | inspection | bearing plane on the plate top face ≤ 0.10 | 2 |  |

### L1.8 Pipe clears everything but the bore

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The pipe (relaxed pose, centred in the bore) clears the extrusion and the M5 heads. | analysis | clear_of(M-PIPE, M-EXT ∪ M-BOLT5 heads, 0.5) | 3 |  |
| L3.8.1.1 | Pipe to extrusion. | analysis | d ≥ 0.50 | 3 | G5 |
| L3.8.1.2 | Pipe to each M5 head. | analysis | d ≥ 0.50 | 3 | G5 |
| L2.8.2 | The pipe touches printed material only inside the bore: the plate, the ears and the rest of the clamp keep clear. | analysis | clear_of(M-PIPE, saddle ∪ cap minus the bore surface and everything within 1.5 of it, 0.5); the 1.5 band is excluded because the split faces and bore edges lie 0.15 from the pipe by design (bore 32.3 against pipe 32.0) | 2 |  |
| L3.8.2.1 | Pipe to non-bore surfaces. | analysis | d ≥ 0.50 (outside the 1.5 band round the bore) | 2 |  |
| L2.8.3 | The M4 heads and the cap leave the pipe's side free: M4 heads clear the pipe. | analysis | clear_of(M-PIPE, M-BOLT4 heads and shanks, 0.5) | 2 |  |
| L3.8.3.1 | Pipe to M4 bolts. | analysis | d ≥ 0.50 | 2 |  |

### L1.9 Hex-key access and a workable assembly order

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | A Ø6.0 hex-key column along each M4 axis, from the head top up 25 mm, is clear with the pipe in place and the clamp closed. | test | clear_of(ALL ∪ M-PIPE ∪ M-EXT, V-DRIVER-M4-1..2, 0.0) | 2 |  |
| L3.9.1.1 | M4 driver columns. | test | d ≥ 0.0 each | 2 |  |
| L2.9.2 | A Ø6.0 hex-key column along each M5 axis, from the head top up 25 mm, is clear with the cap and the pipe removed. | test | clear_of(saddle ∪ M-EXT, V-DRIVER-M5-1..2, 0.0) | 2 |  |
| L3.9.2.1 | M5 driver columns. | test | d ≥ 0.0 each | 2 |  |
| L2.9.3 | Each nut drops into its pocket from the split face (cap removed) without touching anything. | test | clear_of(saddle, V-NUT-INSTALL-1..2, 0.0) excluding the pocket walls the nut ends against | 2 |  |
| L3.9.3.1 | Nut installation path. | test | d ≥ 0.0 | 2 |  |
| L2.9.4 | The pipe lays into the saddle along −X (cap removed) without touching the saddle until it reaches its seat. | test | clear_of(saddle, V-PIPE-INSTALL, 0.10); the pipe resting on the saddle's bore surface at the seat is designed contact | 2 |  |
| L3.9.4.1 | Pipe installation path. | test | d ≥ 0.10 | 2 | G5 |

### L1.10 Strong enough round the bore, the pockets and the holes

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Wall between the bore and the nearest outside surface. | analysis | min wall ≥ 3.0 over the grip length, excluding the ear regions beyond the bolt holes | 3 |  |
| L3.10.1.1 | Wall around the bore, saddle. | analysis | ≥ 3.0 | 3 |  |
| L3.10.1.2 | Wall around the bore, cap. | analysis | ≥ 3.0 | 3 |  |
| L2.10.2 | Ligaments round each nut pocket, bolt hole and M5 hole. | analysis | pocket to bore ≥ 1.5; pocket to outside faces ≥ 1.5; M4 hole to bore ≥ 2.0; M5 hole to plate edge ≥ 3.0 | 2 |  |
| L3.10.2.1 | Pocket ligaments. | analysis | ≥ 1.5 | 2 |  |
| L3.10.2.2 | Hole ligaments. | analysis | M4 hole to bore ≥ 2.0; M5 hole to plate edge ≥ 3.0 | 2 |  |
| L2.10.3 | The saddle is one body fused to its plate: the load path from the pocket to the plate is solid. | analysis | saddle 1 shell; cross-section of the saddle on the plane through the pocket axes and the plate, no void other than the pocket, hole and relief ≥ 60% of the plan section | 2 |  |
| L3.10.3.1 | Load-path section. | analysis | solid ≥ 60% of the section | 2 |  |

### L1.11 Prints without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | In its stated print orientation (saddle plate-down; cap outer face down) no part has an unsupported overhang steeper than 45° from vertical, except round holes Ø ≤ 12.0 in vertical walls and bridges ≤ 15.0. | analysis | 0 offending faces (area > 1 mm²) per body | 2 |  |
| L3.11.1.1 | Overhang and bridge scan per body. | analysis | 0 faces steeper than 45° with area > 1 mm²; every bridge ≤ 15.0; every round hole in a vertical wall Ø ≤ 12.0 | 2 |  |
| L2.11.2 | Each body rests on a flat face in its print orientation. | analysis | bed contact ≥ 40% of the plan bounding box (saddle) and ≥ 80% (cap) | 1 |  |
| L3.11.2.1 | Bed-contact area per body. | analysis | saddle ≥ 40%; cap ≥ 80% | 1 |  |
| L2.11.3 | No feature thinner than 0.8; mating clearances not below 0.15 except the designed split gap. | analysis | min local thickness ≥ 0.8; any other mating gap ≥ 0.15 | 1 |  |
| L3.11.3.1 | Thin-feature scan. | analysis | ≥ 0.8 | 1 |  |
| L2.11.4 | Each body fits a 200 × 200 × 200 build volume. | inspection | bounding box ≤ 200 per axis | 1 |  |
| L3.11.4.1 | Bounding box per body. | inspection | ≤ 200 | 1 |  |

### L1.12 Compact

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | Printed envelope of the delivered (relaxed) pose. | inspection | Z extent ≤ 80.0; Y extent ≤ 70.0; X extent above the face (X − 10) ≤ 60.0 | 1 |  |
| L3.12.1.1 | Assembly bounding box. | inspection | Z ≤ 80.0, Y ≤ 70.0, X above the face ≤ 60.0 | 1 |  |
| L2.12.2 | The clamp does not make the pipe stick out sideways past the extrusion by more than the clamp's own width. | inspection | pipe axis offset from the extrusion centreline ≤ 0.5 (already L2.1.2); clamp Y extent symmetric about Y = 0 within 1.0 | 1 |  |
| L3.12.2.1 | Symmetry about the extrusion centreline. | inspection | abs(Y_max + Y_min) ≤ 1.0 | 1 |  |

### L1.13 Package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.13.1 | The package holds `saddle.stl`, `cap.stl`, the `.scad` source, `layout.json` (poses, bolt lengths, closing translation, print orientations) and `report.json` (the agent's own clear_of / inside results). | inspection | all present and readable; each STL's largest bounding-box axis within 20 to 200 | 3 |  |
| L3.13.1.1 | Files present and parse; units are mm. | inspection | 5 of 5 files present; each STL's largest bounding-box axis within 20 to 200 | 3 | G0 |
| L3.13.1.2 | The declared layout verifies under the seating rule. | analysis | M5 and M4 head-bearing planes on their seats ≤ 0.10; T-nut hole axes coaxial ≤ 0.25; nut on pocket floor ≤ 0.10 | 3 |  |
| L2.13.2 | The agent's own clearance report agrees with the judge's measurements. | analysis | for every clear_of / inside L3 the agent reports, same pass/fail and \|d_agent − d_judge\| ≤ 0.10 | 1 |  |
| L3.13.2.1 | Self-report versus judge. | analysis | 100% agreement within 0.10 | 1 |  |

---

## 5. Counts

| Level | Count |
|---|---|
| L1 | 13 |
| L2 | 43 |
| L3 | 64 (weight 3: 29, weight 2: 26, weight 1: 9; total weight 148) |


Gates (a failure makes a design WRONG regardless of score; section 8): **G0** package (L3.1.1.1, L3.13.1.1); **G1** manifold, separate bodies (L3.3.1.1, L3.3.1.2); **G2** bore, gap, closing and preload (L3.2.1.1, L3.2.1.2, L3.3.2.1, L3.3.2.2, L3.4.5.1, L3.5.1.1); **G3** M4 bolts and captive nuts fit (L3.4.1.1, L3.4.2.1, L3.4.2.2, L3.4.3.1, L3.4.3.3, L3.4.4.1); **G4** back plate on the face, no material in the slot, M5 into the T-nuts (L3.6.1.1, L3.6.3.1, L3.7.1.1, L3.7.1.2, L3.7.2.1, L3.7.2.2, L3.7.3.1); **G5** pipe clearances and install path (L3.8.1.1, L3.8.1.2, L3.9.4.1).

---

## 6. Feasibility: a design that meets every number

A concrete design in the clamp frame, checked with a `manifold3d` model (saddle and cap each one
shell; no interference between any reference parts; bolts clear; nuts inside their pockets).

| Feature | Value |
|---|---|
| Saddle plate | X 10.0 to 15.0 (5.0 thick); tails Y ±10, Z 15 to 85 (70 long); centre block Y ±27.55, Z 38 to 62 (24 grip length) |
| Bore | Ø32.3, axis (X 35.15, Y 0), along Z; bore bottom X 19.0 |
| Split faces | saddle at X 34.9, cap at X 35.4 (gap 0.50); mid-plane X 35.15 on the bore axis |
| Cap | X 35.4 to 55.3 (4.0 above the bore top), same plan outline as the saddle block |
| M4 bolts | axes Y = ±22, Z = 50 (offset 22 in [21.3, 30.0]); cap holes Ø4.5; length 25, head bearing X 54.8 (closed), tip X 29.8 |
| Nut pockets | across flats 7.4, floor X 31.5 (depth 3.4), blind below with a Ø4.5 relief down to X 26; ligament to the bore 2.15, to the outside 1.85 |
| M5 bolts | holes Ø5.5 at Z = 24 and 76 on Y = 0 (spacing 52, 24 from each end); bolts length 10, head bearing X 15, tip X 5.0 (in [4.4, 5.2]) |
| T-nuts | bearing X 8.2, body X 4.7 to 8.2, at Z = 24 and 76 |
| Pipe | Ø32.0 resting in the saddle: axis X 35.0 (X_p − 10 = 25.0); pipe to M5 head gap 1.25 (pipe bottom X 19.0, head top X 17.75); pipe to extrusion 9.0 |
| Closed pose | span 31.8; pipe centred at X 34.9: radial interference 0.10 each side |
| Envelope | Z 70, Y 55.1, X 45.3 above the face (limits 80 / 70 / 60) |
| Print | saddle plate-down (bed contact 58%), cap outer face down (100%); no overhang: bores concave up, hex pockets and holes vertical |

The pipe is laid in along −X before the cap goes on (nothing in the way: the ears sit at |Y| ≥ 18.3 beyond the bore's ±16.15), nuts drop into the pockets from the split face, and the M4 hex-key columns at |Y| = 22 miss the pipe (|Y| ≤ 16). The M5 columns are only clear with pipe and cap removed (F5, L2.9.2).

---

## 7. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 (design.json) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout declared, parts placed from the catalogue | L2.1.1 to L2.1.4 | L3.1.1.1, L3.1.2.1, L3.1.3.1, L3.1.4.1 | L1.1 | inspection | "a 32 mm outside diameter PVC pipe", "the face of a 2020 extrusion", "M4 bolts and captive nuts", "two M5 bolts into the T-slot" |
| L1.2 | Round bore of 32.3 mm round the pipe | L2.2.1 to L2.2.3 | L3.2.1.1, L3.2.1.2, L3.2.1.3, L3.2.2.1, L3.2.3.1 | L1.2 | inspection | "the clamp ID should be 32.3 mm" |
| L1.3 | Two printed pieces, saddle and cap, with a 0.5 mm gap | L2.3.1 to L2.3.3 | L3.3.1.1, L3.3.1.2, L3.3.2.1, L3.3.2.2, L3.3.2.3, L3.3.3.1 | L1.3 | inspection | "two-piece strap", "the bolts close a 0.5 mm gap" |
| L1.4 | Two M4 bolts into captive hex nuts | L2.4.1 to L2.4.5 | L3.4.1.1, L3.4.2.1, L3.4.2.2, L3.4.3.1, L3.4.3.2, L3.4.3.3, L3.4.3.4, L3.4.4.1, L3.4.4.2, L3.4.4.3, L3.4.5.1 | L1.4 | inspection | "M4 bolts and captive nuts" |
| L1.5 | Closing squeezes the pipe by 0.2 mm | L2.5.1 to L2.5.3 | L3.5.1.1, L3.5.2.1, L3.5.2.2, L3.5.3.1 | L1.5 | analysis | "so the bolts close a 0.5 mm gap" |
| L1.6 | Back plate flat on the extrusion face | L2.6.1 to L2.6.4 | L3.6.1.1, L3.6.1.2, L3.6.2.1, L3.6.3.1, L3.6.4.1 | L1.6 | analysis | "to the face of a 2020 extrusion" |
| L1.7 | Two M5 bolts into drop-in T-nuts in the slot | L2.7.1 to L2.7.3 | L3.7.1.1, L3.7.1.2, L3.7.2.1, L3.7.2.2, L3.7.3.1, L3.7.3.2, L3.7.3.3 | L1.7 | analysis | "A back plate takes two M5 bolts into the T-slot" |
| L1.8 | Pipe clears everything but the bore | L2.8.1 to L2.8.3 | L3.8.1.1, L3.8.1.2, L3.8.2.1, L3.8.3.1 | L1.8 | analysis | "holds a 32 mm outside diameter PVC pipe to the face" |
| L1.9 | Hex-key access and a workable assembly order | L2.9.1 to L2.9.4 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1 | L1.9 | test | "I need to reach every bolt with a hex key" (added) and the two-piece strap |
| L1.10 | Strong enough round the bore, the pockets and the holes | L2.10.1 to L2.10.3 | L3.10.1.1, L3.10.1.2, L3.10.2.1, L3.10.2.2, L3.10.3.1 | L1.10 | analysis | "two-piece strap", "bolts close a 0.5 mm gap" (the clamp carries the bolt tension) |
| L1.11 | Prints without supports | L2.11.1 to L2.11.4 | L3.11.1.1, L3.11.2.1, L3.11.3.1, L3.11.4.1 | L1.11 | analysis | "printed on an FDM printer in PLA or PETG without supports" (added) |
| L1.12 | Compact | L2.12.1 to L2.12.2 | L3.12.1.1, L3.12.2.1 | L1.12 | inspection | "a clamp holds a 32 mm outside diameter PVC pipe" (a compact clamp is implied) |
| L1.13 | Package says what was built and its claims are true | L2.13.1 to L2.13.2 | L3.13.1.1, L3.13.1.2, L3.13.2.1 | L1.13 | inspection | needed by the judge (not in the brief) |

---

## 8. Judging this design

> `benchmarks/generalize/rubric.md` was not present when this file was written, so this
> section is the design-specific rubric for G25. It follows `benchmarks/enclosure/rubric.md`
> (sections 2 to 5 and the recipes of its section 3: load, `clear_of`, `inside`, apertures,
> distances, printability, stability) and adds what this design needs. When the generic rubric
> exists, it governs the procedure and report format and this section governs the numbers.

### 8.1 Inputs

| Input | Where | Used for |
|---|---|---|
| `saddle.stl`, `cap.stl` | the design package (relaxed pose, clamp frame, mm) | **every measurement** |
| `.scad` source | package | naming features; never for measuring |
| `layout.json` | package | declared poses, bolt lengths, closing translation, print orientations |
| `report.json` | package | L1.13 self-report check only |
| renders | package `views/*.png` | locating defects |
| `requirements.md`, `parts/*/part.json` | this folder and `benchmarks/generalize/parts/` | criteria and reference models |

The judge does **not** use the agent's code or transcript, earlier verdicts, `benchmarks/heldout.json`,
or any private design of Robin's. Renders locate defects; they never make a check pass.

### 8.2 Procedure

1. **Package gate (G0).** The files above exist and load; if the STLs are missing or unreadable, stop: DOES NOT MEET, one defect on the package L3.
2. **Units.** Load each STL with trimesh and build a `manifold3d.Manifold` (recipe 3.1 of the enclosure rubric). A body whose bounding-box maximum is not plausible in mm (outside 20 to 200) is a defect, never silently rescaled.
3. **Normalise the frame.** Put the delivered pose in the clamp frame (section 1.1): extrusion axis along Z, clamp on the +X face. Use rotations by multiples of 90° and mirroring only; record the transform. Then build the closed pose by translating the cap by −(measured gap) along +X.
4. **Build the references independently** from `parts/*/part.json` at the declared poses (section 2), run the sanity checks R1 to R6, then verify the seating rule.
5. **Run every applicable L3** with Python, in order. Record the measured value, the limit, the signed margin (negative = fail) and PASS / FAIL / UNVERIFIED / N/A. **UNVERIFIED counts as FAIL.** N/A only for physical tests (unless a print was made) and checks the section 3 fixed decisions switch off.
6. **Look at the renders** after measuring, to confirm where each failure is and to catch defects no L3 covers (a floating fragment, a feature on the wrong side). Report those as observations; they change the verdict only if a re-measurement makes an L3 fail.
7. **Decide** (8.4) and **report** (8.5).

### 8.3 Measurement recipes specific to this design

- **Bore fit and gap:** slice each body at mid grip length (Z of the bore centre) with `Manifold.slice(z)`; take the polygon vertices within 2.0 of the bore, fit a circle by least squares (diameter, centre). Gap: ray cast along +X at Y = ±(bore radius + 3) from the saddle's split face to the cap's split face (min, median, max).
- **Closed-pose span:** after translating the cap, cast a ray along +X through the bore axis from the saddle surface to the cap surface; the distance is the span. Preload per side: place the pipe centred between the arcs (closed pose), sample its surface and take the largest penetration depth into each body (signed distance, negative inside).
- **Pocket and hole sizes:** slice at mid-depth; inscribed circle for round holes, across-flats from the polygon's minimal bounding width for hexes; depth by ray casting down the axis.
- **M5 / M4 stack:** build each bolt as a cylinder pair (shank + head) at the declared pose; `pen` against the printed bodies and, for M5, against M-EXT-SOLID.
- **Wall around the bore:** ray cast radially from the bore axis on a 10° grid at mid grip length, excluding rays within the ear zone (|Y| > bore radius + 1.5), and report the minimum.
- **Sweeps:** build V-PIPE-INSTALL, V-NUT-INSTALL and driver columns as extruded cylinders / prisms and use `clear_of`.
- **Printability, bed contact, thin features, overhang:** enclosure rubric recipe 3.6 with the stated print orientations.

### 8.4 Verdict

Gates: G0 package, G1 manifold and separate bodies, G2 bore, gap, closing and preload, G3 M4 bolts and captive nuts fit, G4 back plate on the face, nothing in the slot and M5 into the T-nuts, G5 pipe clearances and install path.

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
| Bore Ø of saddle arc and cap arc | 32.3 ± 0.10 |  |
| Split gap (−Y, +Y) | 0.5 ± 0.10 |  |
| Closed-pose bore span | 31.8 ± 0.15 |  |
| Radial interference, saddle / cap | 0.025 to 0.175 |  |
| Relaxed pipe clearance | ≥ 0.10 |  |
| Plate flatness, face offset, contact area | ≤ 0.20; ≤ 0.05; ≥ 600 mm² |  |
| Penetration into M-EXT-BOX | ≤ 0.01 mm³ |  |
| M5 hole Ø, offset, spacing | 5.5 ± 0.10; ≤ 0.3; 40 to 70 |  |
| M5 tip X | 4.4 to 5.2 |  |
| T-nut coaxial offset | ≤ 0.3 |  |
| M4 hole Ø, pocket AF, depth | 4.5 ± 0.10; 7.4 ± 0.15; 3.4 ± 0.2 |  |
| M4 axis offsets | 21.3 to 30.0, differ ≤ 0.5 |  |
| M4 tip beyond nut | 0.0 to 3.0 |  |
| Pipe to extrusion / M5 heads / non-bore surfaces | ≥ 0.50 / ≥ 0.50 / ≥ 0.50 |  |
| Driver columns M4 / M5 | d ≥ 0 |  |
| Install paths nut / pipe | d ≥ 0 / ≥ 0.10 |  |
| Wall round the bore (saddle, cap) | ≥ 3.0 |  |
| Overhang patches; bed contact | 0; saddle ≥ 40%, cap ≥ 80% |  |
| Envelope Z × Y × X-above-face | ≤ 80 × 70 × 60 |  |
| Self-report agreement | 100% within 0.10 |  |

---

## Audit

Adversarial audit (2026-10-24). Part ids checked with `parts.py` (all four plan parts load and pass the gate, plus `bolt_m5_iso7380` and `tnut_2020_m5`). Counts recomputed: L1 13 in `design.json` and section 4, L2 43, L3 64, weights 29 / 26 / 9, total 148, matching section 5. Section 6 was rebuilt as a `manifold3d` model (saddle with plate, block, bore, pockets, reliefs and M5 holes; cap; extrusion box; pipe in relaxed and closed pose; nuts and bolts) and measured: saddle and cap one shell each; closed-pose saddle ∩ cap 0; plate ∩ extrusion box 0; relaxed pipe gap to the cap 0.154 and resting on the saddle; closed-pose pipe interference 0.10 per side; nuts and bolts do not penetrate either body; pocket to bore 2.155, to the outside 1.85; M5 head to pipe 1.25 relaxed, 1.15 closed; M4 shank to pipe 4.0.

Fixes made in place:

1. **L3.8.2.1 was unsatisfiable.** It required the pipe to be 0.3 from every printed surface except the bore surface, but the bore (Ø32.3 against Ø32.0) puts the split-face edges and the strips beside the bore 0.15 from the pipe in every correct design. It now excludes the bore surface and everything within 1.5 of it, and uses 0.5 to match L1.8 (which already said 0.5 for the plate; L2.8.2 said 0.3). Section 6 passes (the nearest non-bore surface is the plate, 4.0 away). 8.6 table updated.
2. **Section 6 number.** "pipe to M5 head gap 1.10" matched no pose; measured 1.25 (relaxed, resting), 1.15 (closed). Corrected.
3. **L3 rows pointing at the wrong or no limit:** L3.11.1.1 and L3.12.1.1 said "as L2.10.1" / "as L2.11.1" (wrong rows: the envelope is L2.12.1); L3.1.2.1 and L3.4.1.1 said "as L2.x"; L3.1.1.1 and L3.13.1.1 said "true". Each now states its own number. The unit-plausibility limit in section 8.2 (5 to 200) disagreed with L3.13.1.1 (20 to 200); both now 20 to 200. `|Y_max + Y_min|` in L3.12.2.1 had bare pipes that split the table cell; now `abs(...)`.
4. **Hidden numbers moved into L1** (the text the agent gets): grip length 20 to 40 (L1.2), M4 axis offsets 21.3 to 30, equal within 0.5, and the 0 to 3 mm tip past the nut (L1.4), plate end margin 5, thickness 4 to 8 and 600 mm² contact (L1.6), M5 spacing 40 to 70 and 10 from the ends (L1.7), 0.5 mm clear of the pipe elsewhere (L1.8), M4-hole-to-bore 2.0 and M5-hole-to-edge 3.0 (L1.10), 45° / 15 mm print rule (L1.11).

Checked and left alone: the preload band 0.025 to 0.175 follows from span 31.8 ± 0.15 and the 0.5 ± 0.10 gap; the M4 tip window 0.0 to 3.0 needs a relief hole under the nut pocket (the sketch has one, Ø4.5 down to X 26; L2.10.3 already allows "relief"); M5 engagement 3.0 to 3.8 of the 3.5 nut is a requirement of this file that overrides the catalogue's `min_engagement` 5.0 on `tnut_2020_m5` (a 3.5 thick nut cannot give 5.0; section 8.4 precedence applies, recorded here as a catalogue inconsistency, not edited); pipe distance 18 to 30 is a stated decision in the request text; the L1 count is 13.
