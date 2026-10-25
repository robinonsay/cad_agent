# G29 40 mm fan to 25 mm round duct: requirements (L1 / L2 / L3)

Design G29 is a printed fan-to-duct transition. It is graded on the fan mounting (four pilots on
the fan's 32 mm hole pattern, four M3 bolts that really reach into them), on the shape of the
transition (smooth, below 45 degrees, no wall under 1.6 mm), on the spigot that a 25.4 mm tube
slips over, and on supportless printability. It is a training design for the generalisation
set; the method (declared layout, catalogue parts placed by datums, numbers only in the request and the
catalogue) is the same as the enclosure benchmark.

**Request (as given to the agent):** I need a shroud that mounts a 40 x 40 x 10 mm axial fan (mounting holes 3.2 mm on a 32 mm pitch) on its blowing side and tapers smoothly into a round spigot of 25 mm outer diameter and 40 mm straight length. A plain 60 mm long tube of 25.4 mm inside diameter and 2 mm wall slips over the spigot as the duct. The transition must stay below 45 degrees from the airflow axis so the shroud prints without supports, flange side down, and every wall must be at least 1.6 mm thick. Four M3 socket-head bolts, put in from the fan's intake side, hold the fan on and screw into the shroud. It is printed on an FDM printer in PLA.

**Plan brief (verbatim):** "A shroud that mounts a 40 x 40 x 10 mm fan (hole pitch 32 mm) and tapers smoothly into a 25 mm OD spigot of 40 mm length. The transition should stay below 45 degrees so it prints without supports, and the wall stays at least 1.6 mm. Four M3 bolts hold it on."

**Split:** train. **Family:** housing_assembly. **Capabilities exercised:** duct_transition, bolt_pattern, thermal_airflow, concentric_step, multi_body_assembly.

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check Python can run on the delivered STLs. Every L3
row has a method (inspection, analysis, demonstration, test, human; see `design.json`), a pass/fail
criterion with a number and a tolerance, a weight (3 = critical, 2 = major, 1 = minor) and a gate
mark where a failure makes the design WRONG. Every number that comes from an assumption (section
3.1) is provisional until Robin confirms it. No number here may appear in agent logic: target
numbers live in the request text, in `part.json` catalogue data and in this file only.
Where this file and a `part.json` disagree, this file wins (section 7.3).

---

## 1. Frames, tolerances and the checks

### 1.1 Frames

- **Shroud frame (all tables below):** Z is the airflow axis, pointing from the fan toward the
  spigot; the origin is on the axis at the fan's exhaust plane, which is also the underside of the
  shroud flange. So the fan occupies Z −10.0 to 0, X and Y −20 to 20, and its four holes are at
  (±16.0, ±16.0). The shroud occupies Z ≥ 0. A shroud delivered rotated or mirrored is
  normalised into this frame before grading (7.2 step 3): the flange underside on Z = 0, axis on
  the Z axis through the centre of the four pilots; that is never penalised.
- **Fan frame:** the catalogue `fan_40x40x10` frame (origin at the frame min corner, inlet on Z = 0, airflow +Z). Placed in the shroud frame by translating (−20, −20, −10).
- **Bolt frame:** the catalogue `bolt_m3_iso4762` frame (origin on the head bearing face, shank toward −Z, so for this design each bolt is placed turned over: axis +Z in the shroud frame, head bearing on the fan's inlet face Z = −10.0).

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered meshes, never by eye.

| Quantity | Measurement tolerance ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within ε (e.g. "≥ 0.50" passes at 0.48) |
| angle | 0.5° | same |
| interference volume | 0.01 mm³ | "no interference" means intersection volume ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the hole's section (what a screw or pin sees) | |
| boss / pin / spigot OD | smallest enclosing circle of the section | |

Where a criterion is written "nominal ± t", t is the design tolerance and ε is added to it. A mesh
is tessellated: a circle of nominal diameter D measures D·cos(π/N) at worst, so compare diameters
with ε = 0.05 for holes and bosses (the grader fits circles to the section, it does not read vertices).

### 1.3 The checks and designed contact

- **`clear_of(bodies, volume, clearance)`**: the minimum Euclidean distance between every printed
  body in `bodies` and `volume` is ≥ `clearance`. Reported value: the signed minimum distance d
  (negative = penetration; the penetration volume is reported too). Pass: d ≥ clearance − ε.
- **`inside(volume, solids, clearance)`**: `volume` lies entirely inside the convex hull of `solids`
  (or inside the named cavity) and every point of it is ≥ `clearance` from the boundary. Pass:
  d ≥ clearance − ε.
- **`sweep(model, path, bodies)`**: the model is moved along `path` in steps of at most 1.0 mm
  (and the swept union is also tested); pass when the penetration volume with `bodies` stays
  ≤ 0.01 mm³ at every step.

`bodies` is **ALL** (every printed body, closed or in the assembly pose), or one named body. A
design never builds or edits the reference volumes: the grader generates them independently from
the catalogue and the design's declared layout. The agent may generate the same volumes for its
own checks, but its copies are not trusted for grading.

**Designed contact for this design (is never interference).** Parts that are meant to touch are excluded from every interference and clearance check; for these pairs only penetration counts (intersection volume above 0.01 mm³; a distance of zero is a pass):

- the shroud flange underside resting on the fan's exhaust face (Z = 0)
- an M3 bolt head on the fan's inlet face
- an M3 bolt thread in its pilot hole (the thread is formed in the pilot; the model is the 3.0 shank inside the 2.5 pilot, so up to the thread overlap) and the shank in the fan's 3.2 hole
- the duct's end face against the shroud's outer cone, when the duct is slid on to its stop

---

## 2. Reference models, envelopes and datums

### 2.1 Sources

- **catalogue**: built by Python from `part.json` in `benchmarks/generalize/parts/<id>/` (`fan_40x40x10`, `bolt_m3_iso4762`, `generic_tube`). These are the only places target-specific part numbers may live.
- **envelope**: a keep-out or access volume generated by Python from datums. Never drawn by hand.
- **computed**: derived from the delivered STL (the radial profile r_in(Z), r_out(Z), apertures, local thickness).

### 2.2 Reference models (M-)

| Name | What | Source | Size and default position (shroud frame, mm) | Datums |
|---|---|---|---|---|
| **M-FAN** | 40 × 40 × 10 axial fan | catalogue `fan_40x40x10` | X −20 to 20, Y −20 to 20, Z −10.0 to 0; holes Ø3.2 at (±16.0, ±16.0); bore Ø38 (airflow); exhaust plane Z = 0 | `AIRFLOW` (axis Z through (0,0)), `HOLE_1..4`, `EXHAUST` (plane Z = 0), `INLET` (plane Z = −10) |
| **M-BOLT-k** (k = 1..4) | M3 socket-head bolt, length L declared by the design (A3: 16.0 expected) | catalogue `bolt_m3_iso4762` | shank Ø3.0 from Z = −10.0 (head bearing) to Z = −10.0 + L; head Ø5.5 × 3.0 below the bearing plane (Z −13.0 to −10.0); axis on `HOLE_k` | `AXIS`, `HEAD_BEARING`, `TIP` |
| **M-DUCT** | plain tube, ID 25.4, OD 29.4, length 60.0 | catalogue `generic_tube` (outer_diameter 29.4, inner_diameter 25.4, length 60.0 from the request) | axis Z through (0,0); start face at the Z where it stops against the shroud (slid on from +Z; default stop computed by sweep) | `AXIS`, `BORE`, `END_START` |
| **RSA** | reference shroud assembly = M-FAN ∪ M-BOLT-1..4 ∪ M-DUCT at the declared (or default) layout | assembled | as above | all of the above |

### 2.3 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-BORE** | the airflow path inside the shroud | computed: the connected void inside the shroud from the flange underside (Z = 0) to the spigot's open end, around the Z axis |
| **V-PILOT-k** | pilot hole k | computed: the blind hole opening on the flange underside (Z = 0) at `HOLE_k` |
| **V-HEAD-k** | bolt head and tool access | envelope: Ø5.5 column from Z = −13.0 to Z = −10.0, plus the part's tool-access column of Ø5.5 up to 25 above it (toward −Z) |
| **V-FAN-FRAME** | the fan frame as the flange's support | M-FAN, Z −10 to 0 |
| **V-SLIDE** | the duct's sliding path | envelope: M-DUCT swept along −Z from Z = +80 (start face) down to its stop |
| **V-SPIGOT** | the spigot | computed: the Z interval where the outer radius r_out(Z) = 12.5 ± 0.05, i.e. the straight OD portion |
| **V-TRANS** | the transition | computed: the Z interval between the flange top and the start of the spigot; its radial profile r_in(Z), r_out(Z) is taken in the angular sectors away from the four corner bosses (±15° round each diagonal excluded) |

### 2.4 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-FAN | units | frame 40.0 × 40.0 × 10.0 ± 0.2 |
| R2 | M-FAN | hole pattern | pitch 32.0 ± 0.1 both ways; Ø3.2 ± 0.1 |
| R3 | M-FAN | airflow direction | `AIRFLOW` along +Z in the shroud frame |
| R4 | M-BOLT | head and shank | head Ø5.5 × 3.0; shank Ø3.0 ± 0.1 |
| R5 | M-DUCT | bore | ID 25.4 ± 0.05, OD 29.4 ± 0.05 |
| R6 | RSA | models do not collide with each other | intersection ≤ 0.01 mm³ |

**Seating rule.** The RSA is placed at the pose declared in `layout.json`. The grader verifies the declaration: `EXHAUST` lies on the flange underside (≤ 0.10) and `HOLE_1..4` are coaxial with the pilot axes (least-squares residual ≤ 0.10). If the declaration is missing or fails, the RSA is seated by that fit (and the fan axis is taken as the spigot axis); the L3 rows for pose then fail.
---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (with uncertainty)

Each line gives the value chosen and why. Robin may correct any of them; a correction changes this file and the catalogue, and earlier scores become stale.

| # | Question | Value chosen | Why and uncertainty |
|---|---|---|---|
| A1 | Fan numbers? | Frame 40 × 40 × 10, holes Ø3.2 on a 32.0 pitch, airflow bore about Ø38, airflow +Z (blowing out of the exhaust face). | Datasheet class of Sunon/Delta 4010 fans (catalogue `fan_40x40x10`). The bore is approximate (±1). The cable exits a frame corner (not modelled); the flange stays inside the fan outline so it does not trap the cable. The part's `exhaust_air` keep-out (5 mm above the exhaust face) is the shroud's own place and does not apply; only `inlet_air` is checked (L2.4.3). |
| A2 | Fan direction? | The shroud sits on the exhaust (blowing) side. The fan's inlet side is free. | The brief says the shroud tapers into a duct; a blowing fan feeds a duct. On a sucking arrangement the same geometry is mirrored in flow only. |
| A3 | How is the fan held? | Four M3 ISO 4762 socket-head bolts of length 16.0, head on the fan's intake face, shank through the 3.2 fan hole, thread forming into a printed pilot Ø2.5 (depth 6.5, band 6.3 to 7.0: 6.0 engagement + 0.3 floor gap) in a corner boss of the shroud. | `bolt_m3_iso4762` tap diameter 2.5. 16.0 = 10.0 (fan) + 6.0 of engagement (2 × the thread diameter). Uncertainty: thread engagement 5–7; Ø2.5 pilot ±0.1 (FDM prints small). |
| A4 | Duct? | Plain tube ID 25.4, OD 29.4, 60 long; slips over the spigot (0.2 radial clearance). | The request. A hose or a printed sleeve with 0.2 clearance is the same geometry. Uncertainty ±0.1 on the ID. |
| A5 | Wall thickness? | At least 1.6 everywhere; nominal spigot wall 2.0 (ID 21.0), flange 3.0, cone wall 1.7 measured normal to the surface. | The request gives the 1.6 minimum; 2.0 is the common 5-perimeter wall. The cone's normal wall is the horizontal wall times the cosine of its angle. |
| A6 | Printing? | FDM, PLA, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. Flange underside on the bed, spigot pointing up. | Common printers. Overhang limit 45° from vertical; bridges ≤ 15; round holes ≤ 12 in vertical walls. |
| A7 | Airflow area? | The spigot's bore must be at least Ø19.0 (area ≥ 283 mm²); mouth bore at least Ø34.0. | The spigot's outside is fixed at 25.0 and its wall at least 1.6, so ID ≤ 21.8. A bore below Ø19.0 would pass less than half the area a fan of this size needs. Uncertainty ±1.0 on the Ø19.0 floor. |
| A8 | Corner bosses? | Boss OD 7.0 (6.0–8.0), height 7.5 above the flange underside, on each fan hole; they stand on the flange. | 6.0 to 8.0 gives a wall of at least 1.75 round a Ø2.5 pilot. Height 7.5 = 6.5 pilot + 1.0 closed floor. |
| A9 | Flange outline? | The flange is a 40 × 40 square (39.0 to 40.0) with corner radius at most 3.0, 3.0 thick (2.5 to 4.0). | It rests on the fan frame, which is 40 × 40, and the request says it stays within that outline. A flange larger than 40.0 overhangs and is not supported by the fan. |

### 3.2 Fixed decisions (one choice, no alternatives graded)

| # | Ambiguity | Decision | Reason |
|---|---|---|---|
| FD1 | Which side of the fan? | The **exhaust** side (A2); the fan's Z = 0 exhaust plane is the flange underside. | The brief has the shroud taper into a duct, so air leaves the fan into it. |
| FD2 | Bolt direction? | From the fan's **intake** side, head on the intake face, into pilot holes in the shroud (A3). | 'Four M3 bolts hold it on': holding the fan on with bolts that pass through the fan frame needs no nuts. The pilot opens on the flange underside. |
| FD3 | Spigot bore? | ID **21.0** nominal (band 19.0–21.8): wall 2.0. | Satisfies 'wall at least 1.6' with margin; a single nominal so the feasibility sketch is exact. |
| FD4 | What is 'below 45 degrees'? | The half-angle between the transition wall and the airflow axis (Z), measured on both the inner and the outer surface: **at most 45.0°** at every point of the profile (nominal 32.0°). | The roof of a printed cone is steepest from the vertical; ≤ 45° from the vertical is the supportless rule. |
| FD5 | What is 'spigot of 40 mm length'? | The straight Ø25.0 portion from the end of the taper to the open end: **40.0 ± 0.3**. | The taper length is a separate design number (band 7.5–17.5, nominal 12.0; the 60.0 height limit caps it). |
| FD6 | Duct fit? | Slip fit: radial clearance **0.2** (band 0.10–0.30) between spigot OD and duct ID. | Typical FDM slip fit. |
| FD7 | Print orientation? | Flange underside on the bed, axis vertical, spigot up. Declared in `layout.json`. | The only orientation without supports (the cone's inner roof is 32° from vertical). |

---

## 4. Requirements tree

### L1.1 The fan, the four bolts and the duct are placed on the shroud by their datums

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: the pose of the fan, each bolt (with its length) and the duct. | inspection | `layout.json` present, parses, names `fan_40x40x10`, four `bolt_m3_iso4762` (with length) and `generic_tube` (OD 29.4, ID 25.4, length 60.0) | 3 | |
| L3.1.1.1 | Layout file parses and every catalogue id exists. | inspection | true | 3 |  |
| L3.1.1.2 | The declared pose verifies under the seating rule (EXHAUST on the flange underside, holes coaxial). | analysis | plane ≤ 0.10; residual ≤ 0.10 | 3 |  |
| L2.1.2 | The fan blows into the shroud, coaxially. | inspection | `AIRFLOW` direction within 0.5° of +Z; fan axis within 0.20 of the shroud axis | 3 | |
| L3.1.2.1 | Fan airflow direction and axis offset to the shroud axis. | inspection | ≤ 0.5° and ≤ 0.20 | 3 |  |
| L2.1.3 | The assembled parts do not collide. | analysis | each pair of RSA parts and the shroud has intersection ≤ 0.01 mm³ outside the designed contact | 3 | |
| L3.1.3.1 | Pairwise interference of M-FAN, M-BOLT-k, M-DUCT and the shroud. | analysis | ≤ 0.01 mm³ each pair | 3 |  |

### L1.2 Four pilot holes on the fan's 32 mm pattern

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | Four pilots at the fan holes. | inspection | count = 4; axes at (±16.0, ±16.0) within 0.10; pitch 32.0 ± 0.10 both ways | 3 | |
| L3.2.1.1 | Number of pilot holes opening on the flange underside. | inspection | count = 4 | 3 | G3 |
| L3.2.1.2 | Pilot axes against the fan `HOLE` datums. | analysis | each offset ≤ 0.10 | 3 | G3 |
| L3.2.1.3 | Pilot pitch along X and along Y. | inspection | 32.0 ± 0.10 | 3 |  |
| L2.2.2 | Pilot diameter and depth suit an M3 thread-forming bolt. | inspection | Ø2.5 ± 0.10 (bolt `tap_diameter`); depth ≥ 6.3 and ≤ 7.0, blind, closed floor ≥ 0.8 | 3 | |
| L3.2.2.1 | Pilot inscribed diameter at mid-depth. | inspection | 2.5 ± 0.10 | 3 |  |
| L3.2.2.2 | Pilot depth and closed floor above it. | inspection | 6.3 ≤ depth ≤ 7.0; floor ≥ 0.8 | 2 |  |
| L2.2.3 | Each pilot is in a boss that is fused to the flange and stiff enough. | analysis | boss OD 6.0–8.0; wall round the pilot ≥ 1.5; shroud is one connected body | 2 | |
| L3.2.3.1 | Boss outer diameter and wall round the pilot. | inspection | 6.0 ≤ OD ≤ 8.0; wall ≥ 1.5 | 2 |  |
| L3.2.3.2 | Bosses are connected to the shroud. | analysis | one shell (see the printability L1) | 2 |  |

### L1.3 The bolts really hold the fan on

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Stack: head on the intake face, shank through the fan, engagement in the pilot. | analysis | tip Z (shroud frame) = −10.0 + L; engagement = tip Z ≥ 6.0; tip ≤ pilot depth − 0.3 | 3 | |
| L3.3.1.1 | Bolt tip position and thread engagement for each bolt. | analysis | engagement ≥ 6.0; gap to the pilot floor ≥ 0.3 | 3 | G5 |
| L3.3.1.2 | Bolt axes against the fan holes and the pilots. | analysis | coaxial within 0.10 | 2 |  |
| L2.3.2 | A bolt never enters the bore or leaves the boss. | analysis | clear_of(M-BOLT-k, V-BORE, 0.8); tip at least 0.8 below the boss top | 2 | |
| L3.3.2.1 | Bolt to bore clearance and tip-to-boss-top distance. | analysis | ≥ 0.8 and ≥ 0.8 | 2 |  |
| L2.3.3 | Every bolt can be turned with a hex key. | analysis | clear_of(ALL, V-HEAD-k, 0.0) for k = 1..4 | 2 | |
| L3.3.3.1 | Head and tool-access columns are clear of every printed body. | analysis | penetration ≤ 0.01 mm³ | 2 |  |

### L1.4 The flange sits flat on the fan and lets the air through

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The flange is flat and supported by the fan frame. | inspection | underside flatness ≤ 0.10; flange outline in X and Y 39.0–40.0; thickness 2.5–4.0 | 3 | |
| L3.4.1.1 | Flatness of the flange underside. | inspection | ≤ 0.10 | 3 |  |
| L3.4.1.2 | Flange outline and thickness. | inspection | 39.0–40.0 in X and Y; 2.5–4.0 | 2 |  |
| L2.4.2 | The bore at the flange. | inspection | mouth inscribed diameter 34.0–36.8 (nominal 36.0), centred on the axis within 0.20 | 3 | |
| L3.4.2.1 | Mouth diameter at Z = 1.0 and its centre. | inspection | 34.0–36.8; offset ≤ 0.20 | 3 |  |
| L2.4.3 | Nothing is printed on the fan's inlet side or in front of it. | analysis | clear_of(ALL, M-FAN inlet keep-out, 0.0) | 1 | |
| L3.4.3.1 | The inlet keep-out (frame_size × frame_size × inlet_gap) is free of printed bodies. | analysis | penetration ≤ 0.01 mm³ | 1 |  |

### L1.5 A smooth transition below 45 degrees

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Profile slope. | analysis | max \|dr/dZ\| of r_in(Z) and r_out(Z) over the transition ≤ tan 45° = 1.0 (nominal 0.625: 32°) | 3 | |
| L3.5.1.1 | Maximum half-angle of the inner profile over V-TRANS. | analysis | ≤ 45.0° (measured from slices every 0.5 mm, outside the corner-boss sectors) | 3 | G6 |
| L3.5.1.2 | Maximum half-angle of the outer profile over V-TRANS. | analysis | ≤ 45.0° (outside the corner-boss sectors) | 2 |  |
| L2.5.2 | Profile is smooth and monotone. | analysis | no radial step larger than 0.3 anywhere; r_in(Z) non-increasing from the mouth to the spigot; transition axial length 7.5–17.5 | 2 | |
| L3.5.2.1 | Largest radial step and monotonicity of r_in(Z) and r_out(Z). | analysis | step ≤ 0.30; monotone | 2 |  |
| L3.5.2.2 | Transition axial length (flange top to start of the spigot). | inspection | 7.5–17.5 (nominal 12.0; 17.5 = 60.0 − 40.0 − 2.5 flange) | 1 |  |
| L2.5.3 | The profile is axisymmetric. | analysis | for each Z slice of the transition and spigot the section is a circle: max − min radius ≤ 0.2, measured outside the corner-boss sectors (±15° round each diagonal; the bosses stand on the cone up to Z 7.5) | 2 | |
| L3.5.3.1 | Roundness of the inner and outer section at 1 mm steps, boss sectors excluded. | analysis | ≤ 0.2 | 2 |  |

### L1.6 A 25 mm spigot of 40 mm length

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Spigot outer diameter and straight length. | inspection | OD 25.0 ± 0.10; straight length 40.0 ± 0.3 | 3 | |
| L3.6.1.1 | Spigot outer diameter (enclosing circle, mid-length). | inspection | 25.0 ± 0.10 | 3 | G4 |
| L3.6.1.2 | Length of V-SPIGOT (r_out = 12.5 ± 0.05). | inspection | 40.0 ± 0.3 | 3 |  |
| L2.6.2 | Spigot bore. | inspection | inscribed diameter 19.0–21.8 (nominal 21.0), constant over the spigot to within 0.2 | 3 | |
| L3.6.2.1 | Spigot bore diameter at three Z. | inspection | 19.0–21.8; spread ≤ 0.2 | 3 |  |
| L2.6.3 | The spigot is concentric with the fan axis. | analysis | spigot axis within 0.20 of the fan axis, parallel within 0.5° | 3 | |
| L3.6.3.1 | Spigot axis against `AIRFLOW`. | analysis | ≤ 0.20 and ≤ 0.5° | 3 |  |

### L1.7 No wall thinner than 1.6 mm

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Minimum local thickness of the whole shroud. | analysis | ≥ 1.6 away from edges (excluding the blind pilots' own floor) | 3 | |
| L3.7.1.1 | Minimum wall thickness over the cone, spigot and flange (medial-sphere or inward ray scan). | analysis | ≥ 1.6 | 3 | G7 |
| L2.7.2 | Wall thickness at the places that thin out. | analysis | cone normal wall ≥ 1.6; flange at the flat sides (flange half-width minus bore radius) ≥ 1.6; spigot wall (25.0 − ID)/2 ≥ 1.6 | 2 | |
| L3.7.2.1 | Cone wall measured normal to the surface at five Z. | analysis | ≥ 1.6 | 2 |  |
| L3.7.2.2 | Flange material between the bore and the flange's flat edges. | analysis | ≥ 1.6 | 2 |  |
| L3.7.2.3 | Spigot wall at three Z. | analysis | ≥ 1.6 | 2 |  |

### L1.8 The duct slips over the spigot

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The duct slides on without touching. | test | sweep(M-DUCT, V-SLIDE, shroud): penetration ≤ 0.01 up to the stop; radial clearance 0.10–0.30 | 3 | |
| L3.8.1.1 | Duct sweep along −Z from Z = +80 to the stop. | test | penetration ≤ 0.01 mm³ until the end face touches the cone | 3 |  |
| L3.8.1.2 | Radial gap between spigot OD and duct ID. | analysis | 0.10 ≤ gap ≤ 0.30 | 2 |  |
| L2.8.2 | The duct overlaps the spigot far enough. | analysis | overlap = spigot end Z − stop Z ≥ 35.0 | 2 | |
| L3.8.2.1 | Overlap length of the duct on the spigot at the stop. | analysis | ≥ 35.0 (nominal 40.3) | 2 |  |
| L2.8.3 | Nothing else stops the duct early. | analysis | clear_of(shroud outside the cone, M-DUCT, 0.5) for the corner bosses and the flange | 1 | |
| L3.8.3.1 | Duct to bosses and flange clearance. | analysis | ≥ 0.5 | 1 |  |

### L1.9 A continuous airflow path, closed except the ends

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The bore is continuous and open at both ends. | analysis | V-BORE is one connected region with an opening at Z = 0 and one at the spigot end; nothing blocks the section | 3 | |
| L3.9.1.1 | Connectivity of V-BORE and the two openings. | analysis | 1 region; 2 openings | 3 | G8 |
| L3.9.1.2 | Minimum flow area along the bore. | analysis | ≥ 283 mm² (nominal 346) | 2 |  |
| L2.9.2 | No unlisted openings (the pilots are blind). | analysis | no path from the outside into V-BORE other than the two ends: 0 unlisted paths by ray scan | 2 | |
| L3.9.2.1 | Leak-path probe from every outside face into V-BORE. | analysis | 0 unlisted paths (a Ø2.0 sphere does not pass) | 2 |  |

### L1.10 Printable on an FDM printer without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | One manifold body. | analysis | 1 shell; manifold3d accepts it | 3 | |
| L3.10.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.10.2 | No unsupported overhang in the declared orientation. | analysis | 0 offending faces (area > 1 mm²) steeper than 45° from vertical, except round holes Ø ≤ 12 in vertical walls and bridges ≤ 15 | 3 | |
| L3.10.2.1 | Overhang and bridge scan per patch. | analysis | as L2 | 3 | G9 |
| L3.10.2.2 | Bed contact area of the flange underside (a ring: see section 6). | analysis | ≥ 30% of the plan bounding box | 1 |  |
| L2.10.3 | No feature thinner than 0.8; build volume. | analysis | min thickness ≥ 0.8; bounding box ≤ 200 per axis | 1 | |
| L3.10.3.1 | Thin-feature scan. | analysis | ≥ 0.8 | 1 |  |
| L3.10.3.2 | Bounding box. | inspection | ≤ 200 per axis | 1 |  |

### L1.11 Compact and stable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Bounding box limit. | inspection | X ≤ 42.0, Y ≤ 42.0, Z ≤ 60.0 | 1 | |
| L3.11.1.1 | Bounding box of the shroud. | inspection | as L2 (nominal 40.0 × 40.0 × 55.0) | 1 |  |
| L2.11.2 | It stands on the flange. | analysis | stable at 5° tilt on the flange underside | 1 | |
| L3.11.2.1 | Centre of mass inside the flange support polygon at 5° tilt. | analysis | passes | 1 |  |

### L1.12 The delivered package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.12.1 | The package holds `shroud.stl`, the `.scad` source, `layout.json` and the agent's report. | inspection | all present and readable | 3 | |
| L3.12.1.1 | Files present and parse; STL in mm: largest bounding-box axis within 20–200. | inspection | true | 3 | G0 |
| L2.12.2 | The agent's report agrees with the judge. | analysis | for every clear_of / engagement / slope number reported: pass/fail the same and \|d_agent − d_judge\| ≤ 0.10 | 1 | |
| L3.12.2.1 | Self-report against the judge. | analysis | 100% within 0.10 | 1 |  |

---

## 5. Counts and gates

L1: 12. L2: 32. L3: 48.

Gates (a failing gate makes the design WRONG regardless of score):

- **G0** package present and readable: L3.12.1.1
- **G1** one manifold body: L3.10.1.1
- **G3** four pilots on the 32 mm pattern: L3.2.1.1, L3.2.1.2
- **G4** spigot OD 25.0 ± 0.1: L3.6.1.1
- **G5** bolts reach at least 6.0 mm into the pilots: L3.3.1.1
- **G6** transition at most 45°: L3.5.1.1
- **G7** no wall under 1.6: L3.7.1.1
- **G8** continuous bore: L3.9.1.1
- **G9** no unsupported overhang: L3.10.2.1

---

## 6. Feasibility

A concrete design exists (shroud frame, mm; revolved about Z):

- Flange: 40.0 × 40.0 square, Z 0 to 3.0, corner radius 2.0. Inner bore Ø36.0 from Z 0 to 3.0 (flat-side material (40 − 36)/2 = 2.0 ≥ 1.6).
- Transition: Z 3.0 to 15.0 (length 12.0). Inner radius 18.0 → 10.5; outer radius 20.0 → 12.5. Inner half-angle atan(7.5 / 12.0) = 32.0° (below 45°); same for the outer. Normal wall (20.0 − 18.0) × cos 32.0° = 1.70 ≥ 1.6.
- Spigot: Z 15.0 to 55.0 (40.0 straight), OD 25.0, ID 21.0 (wall 2.0). Flow area π × 10.5² = 346 mm² ≥ 283.
- Corner bosses Ø7.0, Z 0 to 7.5, centred on (±16.0, ±16.0) (they reach ±19.5, inside the 40 square; the nearest bore point is 22.6 − 3.5 − 18.0 = 1.1 from a boss). Pilot Ø2.5 from Z 0 to 6.5 (closed floor 1.0). Pitch 32.0 exactly.
- Bolts: M3 × 16.0, head bearing on the fan's inlet face (Z −10.0), tip at Z = −10.0 + 16.0 = +6.0: engagement 6.0 ≥ 6.0, gap to the pilot floor 0.5 ≥ 0.3, tip 1.5 below the boss top (7.5) ≥ 0.8.
- Duct: ID 25.4 over OD 25.0 (0.2 per side). It stops where the outer cone radius equals 12.7: Z = 3.0 + (20.0 − 12.7) × 12.0 / 7.5 = 14.68, so overlap = 55.0 − 14.68 = 40.3 ≥ 35. The duct's OD (29.4) clears the bosses (top at Z 7.5, below Z 14.68).
- Print: flange underside on the bed (40 × 40 outline minus the Ø36 bore and four Ø2.5 pilots: about 562 mm² of the 1600 mm² plan box, 35%, see the note); the inner cone's roof is 32° from vertical, so no support is needed.

Note on bed contact: the flange underside is a ring (40 × 40 outline, Ø36 bore): its area is 1600 − π × 18² = 582 mm², 36% of the plan box. L3 bed contact for this design is therefore a ring-contact check, set to **≥ 30% of the plan bounding box** (see the L3 row; the generic 50% of the enclosure benchmark applies to compact bodies, not to a ring). A design that adds a wider flange would give more but the flange must stay within 41.0.

Every number is within the bands of section 4; the request, the L1s and the catalogue (`fan_40x40x10` 40 × 40 × 10, pitch 32.0, Ø3.2; `bolt_m3_iso4762` Ø3.0, tap 2.5, head Ø5.5 × 3.0; `generic_tube` from the request) agree.
---

## 7. Grading procedure (design-specific rubric)

`benchmarks/generalize/rubric.md` (the generic rubric) did not exist when this file was written,
so the procedure is given here. When that file exists it governs the procedure and this section
governs only the numbers: **requirements numbers beat `part.json` numbers, and this section beats the
generic rubric where they differ.** The recipes for loading, `clear_of`, `inside`, apertures,
thicknesses, overhangs and bed contact are those of `benchmarks/enclosure/rubric.md` section 3
(Python at `/Users/robinonsay/python/llm-bt/venv/bin/python`, `trimesh`, `manifold3d`; count shells
with `manifold3d` `decompose()`, not `trimesh.split()`).

### 7.1 Inputs

STLs of every printed body in the assembly pose (mm), the `.scad` source (for naming features,
never for measuring), the declared layout file (`layout.json`: the pose of each catalogue part
and each body's print orientation) and the agent's own clearance report (graded only by the
evidence L3, never trusted elsewhere). The judge also gets `requirements.md` and `parts/*/part.json`
and nothing from the agent's code or transcript. The judge never opens `benchmarks/heldout.json`.

### 7.2 Procedure

1. **Package gate.** The listed files exist and load; otherwise stop with DOES NOT MEET and one
   defect on the package L3.
2. **Units.** Each body's largest bounding-box axis must be of the order stated in the package L3;
   if it looks like inches or metres record a defect and do not rescale silently.
3. **Normalise the frame.** Put the shroud in the shroud frame (1.1): flange underside on Z = 0, spigot toward +Z, axis through the centre of the four pilots. Rotations by multiples of 90° and mirroring only; record the transform.
4. **Build the references independently** from `part.json` and section 2 of this file at the
   declared layout (or the default layout where this file gives one), then run the sanity checks
   R1..Rn of section 2. A failing sanity check is fixed before grading.
5. **Run every applicable L3** with Python. Record measured value, limit, margin (measured minus
   limit, signed so that negative = fail) and PASS / FAIL / UNVERIFIED / N/A. **UNVERIFIED counts as
   FAIL.** N/A only for physical tests (unless a print was made).
6. **Look at the renders** after measuring, to confirm where a failure is and to catch defects
   no L3 covers (report those as observations; they do not change the verdict).
7. **Decide** and **report**.

### 7.3 Verdict classes

Gates: G0 package present and readable; G1 one manifold body; G3 four pilots on the 32 mm pattern; G4 spigot OD 25.0 ± 0.1; G5 bolts reach at least 6.0 mm into the pilots; G6 transition at most 45°; G7 no wall under 1.6; G8 continuous bore; G9 no unsupported overhang.

| Class | Rule |
|---|---|
| **WRONG** | any gate fails |
| **MINOR** | no gate fails, but some weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |
| **MEETS** | CORRECT and every applicable non-physical L3 of weight 1 and 2 passes (the loop's zero-error state) |

Anything that is not MEETS is DOES NOT MEET. Also report the weighted score Σ(weight × pass) /
Σ(weight) over applicable L3s, and the worst normalised margin among weight-3 L3s (margin divided
by the criterion's tolerance or, for one-sided limits, by 0.5 mm).

Precedence:
- A functional check outranks the size check that serves it (plug seats, bolt reaches, part fits
  beat opening size and wall size), as long as the size check still passes on its own numbers.
- **Designed contact is not interference** (section 1.3). Only penetration above 0.01 mm³ counts for the listed pairs.
- The numbers in this file are authoritative. If `parts/*/part.json` disagrees, build the reference from this file and record a defect on the L3 that the stale catalogue data breaks, with `where` = the part.json field.
- Fixed decisions (section 3.2) admit no alternative. Any unlisted alternative is graded on the default numbers and noted as an observation.
- Never relax a criterion, never round in the design's favour beyond ε, never infer a pass from a render.

### 7.4 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first (gates, then weight 3, 2, 1).
Each entry has: `req` (L3 with its L2 and L1), `status`, `body`, `feature` (by function and, if
it exists, by its SCAD name), `face` (surface with its outward normal), `location` (coordinates in
mm in the normalised frame, a point or a box `[xmin, ymin, zmin]–[xmax, ymax, zmax]`),
`measured` / `limit` / `margin` with units, `reference` (the reference model or envelope and its
datum), `render` (which view and where in the image), `evidence` (saved file, e.g. the
intersection solid `defect_<L3>.stl`) and `needed` (the geometric change that would make the
check pass, as numbers, never as a design instruction). Coordinates come from the measurement,
not from the SCAD source. Group L3s that fail for one geometric reason under the first and list
the rest in `also_fails`, keeping every L3 id. Keep observations separate from defects. Save the
report as `judge.md` and `defects.json`.

### 7.5 Measured-values table (always filled in, pass or fail)

| Quantity | Limit | Measured |
|---|---|---|
| Pilot count, pitch X / Y, axis offset (L3.2.1.x), mm | 4; 32.0 ± 0.10; ≤ 0.10 | |
| Pilot Ø, depth, floor (L3.2.2.x), mm | 2.5 ± 0.10; 6.0–7.0; ≥ 0.8 | |
| Bolt engagement, gap to pilot floor (L3.3.1.1), mm | ≥ 6.0; ≥ 0.3 | |
| Flange flatness, outline, mouth Ø (L3.4.x), mm | ≤ 0.10; 39.0–41.0; 34.0–36.8 | |
| Max inner / outer half-angle (L3.5.1.x) | ≤ 45.0° | |
| Largest radial step (L3.5.2.1), mm | ≤ 0.30 | |
| Spigot OD, straight length, ID (L3.6.x), mm | 25.0 ± 0.10; 40.0 ± 0.3; 19.0–21.8 | |
| Minimum wall (L3.7.1.1), mm | ≥ 1.6 | |
| Duct gap, overlap (L3.8.x), mm | 0.10–0.30; ≥ 35.0 | |
| Bore regions / flow area (L3.9.1.x) | 1; ≥ 283 mm² | |
| Shells; overhang patches; bed contact (L3.10.x) | 1; 0; ≥ 30% | |
| Bounding box (L3.11.1.1), mm | ≤ 42 × 42 × 60 | |
| Self-report agreement (L3.12.2.1) | 100% within 0.10 | |

---

## 8. Traceability

| L1 | Owner need | L2 | L3 | JSON L1 (`design.json`) | L1 method | Words in the request it comes from |
|---|---|---|---|---|---|---|
| L1.1 | Layout | L2.1.1–L2.1.3 | L3.1.1.1, L3.1.1.2, L3.1.2.1, L3.1.3.1 | L1.1 | inspection | "mounts a 40 x 40 x 10 mm fan", "Four M3 bolts", "25 mm round duct" |
| L1.2 | Fan bolt pattern | L2.2.1–L2.2.3 | L3.2.1.1, L3.2.1.2, L3.2.1.3, L3.2.2.1, L3.2.2.2, L3.2.3.1, L3.2.3.2 | L1.2 | inspection | "hole pitch 32 mm", "Four M3 bolts" |
| L1.3 | Bolt stack | L2.3.1–L2.3.3 | L3.3.1.1, L3.3.1.2, L3.3.2.1, L3.3.3.1 | L1.3 | analysis | "Four M3 bolts hold it on" |
| L1.4 | Flange | L2.4.1–L2.4.3 | L3.4.1.1, L3.4.1.2, L3.4.2.1, L3.4.3.1 | L1.4 | analysis | "mounts a 40 x 40 x 10 mm fan" |
| L1.5 | Transition | L2.5.1–L2.5.3 | L3.5.1.1, L3.5.1.2, L3.5.2.1, L3.5.2.2, L3.5.3.1 | L1.5 | analysis | "tapers smoothly", "below 45 degrees" |
| L1.6 | Spigot | L2.6.1–L2.6.3 | L3.6.1.1, L3.6.1.2, L3.6.2.1, L3.6.3.1 | L1.6 | inspection | "25 mm OD spigot of 40 mm length" |
| L1.7 | Wall thickness | L2.7.1–L2.7.2 | L3.7.1.1, L3.7.2.1, L3.7.2.2, L3.7.2.3 | L1.7 | analysis | "the wall stays at least 1.6 mm" |
| L1.8 | Duct fit | L2.8.1–L2.8.3 | L3.8.1.1, L3.8.1.2, L3.8.2.1, L3.8.3.1 | L1.8 | test | "25 mm round duct", "25 mm OD spigot" |
| L1.9 | Airflow | L2.9.1–L2.9.2 | L3.9.1.1, L3.9.1.2, L3.9.2.1 | L1.9 | analysis | "thermal_airflow" (a fan feeding a duct) |
| L1.10 | Printable | L2.10.1–L2.10.3 | L3.10.1.1, L3.10.2.1, L3.10.2.2, L3.10.3.1, L3.10.3.2 | L1.10 | analysis | "prints without supports" |
| L1.11 | Size | L2.11.1–L2.11.2 | L3.11.1.1, L3.11.2.1 | L1.11 | inspection | (implied: a compact adapter) |
| L1.12 | Evidence | L2.12.1–L2.12.2 | L3.12.1.1, L3.12.2.1 | L1.12 | inspection | (not the owner's words; needed by the judge) |

---

## Audit

Adversarial audit (second agent). Recomputed: fan holes at (±16.0, ±16.0) from the part (offset (40 − 32)/2 = 4), flange and boss geometry (boss edge 19.5 inside 20; bore to boss gap 1.13), the cone (18 → 10.5 and 20 → 12.5 over 12.0, 32.0°, normal wall 1.696), spigot Z 15 to 55, flow area 346 mm², duct stop Z = 14.68 and overlap 40.32, bolt stack (tip Z 6.0, engagement 6.0, gap 0.5, 1.5 below the boss top), bed contact 35%, bounding box 40 x 40 x 55. The three parts load once `length`, `outer_diameter`/`inner_diameter` come from the request or layout (`bolt_m3_iso4762` length 16, `generic_tube` 29.4 / 25.4 / 60); L1 = 12, L2 = 32, L3 = 48 match section 5 and the traceability.

| # | Defect found | Fix |
|---|---|---|
| 1 | The duct length (60.0) was needed by the grader (`generic_tube` takes it from the request, V-SLIDE, the overlap test) but the request never gave it. | Request now says "A plain 60 mm long tube ..." (design.json and here). |
| 2 | Pilot depth band 6.0 to 7.0 contradicted G5: with the minimum 6.0 engagement the tip is at Z 6.0, and L3.3.1.1 needs 0.3 to the pilot floor, so a 6.0 deep pilot fails. | Pilot depth band is 6.3 to 7.0 (A3, L2.2.2, L3.2.2.2) and L1.2 now says so. Nominal 6.5 unchanged. |
| 3 | Flange outline band 39.0 to 41.0 contradicted L1.4 "stay within the fan's 40 mm outline" and A9's own reason. | Band is 39.0 to 40.0 (A9, L2.4.1, L3.4.1.2) and L1.4 states it with the thickness. |
| 4 | Transition length band 7.5 to 25.0 cannot be met together with the 60.0 height limit (2.5 flange + 25 + 40 = 67.5). | Band is 7.5 to 17.5 (FD5, L2.5.2, L3.5.2.2). |
| 5 | The roundness, slope and step checks (L2.5.1, L2.5.2, L2.5.3) are taken on r(Z) of the whole section, but the four corner bosses stand free on the cone up to Z 7.5 (boss edge at radius 19.13, cone radius 20.0 at Z 3.0), so the nominal design failed its own roundness check. | The profile is measured outside the corner-boss sectors (±15° round each diagonal): V-TRANS definition, L2.5.3, L3.5.1.1/2, L3.5.3.1 and L1.5. |
| 6 | L1.5 hard-coded "the Ø36 flange bore" while L1.4 allows 34.0 to 36.8. | L1.5 says "the flange bore"; L1.4 gives the 34.0 to 36.8 band (36.8 = 40 − 2 x 1.6). |
| 7 | Numbers the judge uses but the agent was never told: boss OD band, gap to the pilot floor, bolt to bore 0.8, tip below boss top 0.8, flange thickness, transition length, step 0.3. | Added to L1.2 to L1.5 in `design.json`. |
| 8 | The fan part's `exhaust_air` keep-out (40 x 40 x 5 above the exhaust face) is exactly where the shroud sits. | Noted in A1: only `inlet_air` applies (L2.4.3 already said so). |

Noted, not changed: the minimum engagement is met with zero margin by the only stock length that works (M3 x 16, tip at 6.0; limit is "at least 6.0"); the gate list has no G2 (numbering gap, no effect).
