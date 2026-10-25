# G42 16 mm hose to 25 mm pipe adapter: requirements (L1 / L2 / L3)

A training design of the generalisation benchmark (`benchmarks/generalize/plan.json`, family
fixture_adapter). Modelled on E1-01 (`benchmarks/enclosure/requirements.md`): the same L1/L2/L3 structure,
reference models built from catalogue parts, designed-contact rule, gates and traceability. The
machine-readable request (L1 only, `dev.json` format) is `design.json` next to this file. Generic grading
rules would live in `benchmarks/generalize/rubric.md`; when this file was written that file did not exist
yet, so **section 8 is a design-specific rubric supplement** (it follows `benchmarks/enclosure/rubric.md`;
if `generalize/rubric.md` exists later it governs the generic parts and section 8 only adds the G42
specifics).

**Owner's request (brief, verbatim):** "A hose adapter from a 16 mm inner diameter hose onto a 25 mm OD
pipe: a barbed 16 mm end with three ribs 0.8 mm tall, a 2 mm wall, and a socket for the 25 mm pipe 0.15 mm
loose, 20 mm deep. Overall length 60 mm and it must print upright without supports."

**How to read this.** L1 says what the owner needs. L2 is an engineering requirement with numbers. L3 is a
concrete check Python can run on the delivered STL (profile slices, sweeps, ray casting, overhang scan).
Every L3 has a method, a pass band with a tolerance, a weight (3 = critical, 2 = major, 1 = minor) and, where
it is a must-pass, a gate mark (G0 to G5, section 5). Numbers that come from an assumption (section 3) are
provisional until the owner confirms them. Do not relax a criterion because the agent fails it.

---

## 1. Frames, tolerances, checks and designed contact

### 1.1 Frame

- **Adapter frame:** the axis is **Z**; **Z = 0 is the tip of the spigot** (the hose end, the end with the
  small outside diameter and the ribs) and +Z runs toward the socket, so the socket mouth is at Z = 60.0. The
  grader finds the axis as the centre line through the slices of the bore, and normalises a delivered STL
  into this frame by rotations (multiples of 90 degrees) and mirroring only; that is never penalised.
- **Profile:** r(z) = the outer radius, and the bore radius b(z), measured from slices perpendicular to Z
  every 0.25 mm (circle fits). All lengths in mm, angles in degrees.

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, diameter, distance, clearance | 0.02 mm (mesh tessellation) | a value passes if it meets the limit to within e |
| angle | 0.5 degrees | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| diameter of a slice | circle fit (least squares, residual reported) | |
| wall thickness | ray cast along the local normal, median over the section away from features | |

Where a criterion is written "nominal +/- t", t is the design tolerance and e is added to it.

### 1.3 The checks

- **`clear_of(bodies, volume, c)`**: minimum distance between the printed body and the volume is >= c.
  Reported: signed minimum distance d (negative = penetration; penetration volume too). Pass: d >= c - e.
- **`profile(z)`**: the outer radius, the bore radius and the section centre at each Z, from slices.
- **`slope`**: angle between the outer profile and the axis, from finite differences of r(z) over 0.5 mm.
- Count, dimension, thickness and gap checks as in E1-01 rubric section 3.5.

The grader builds every reference model and envelope itself from the catalogue and the declared layout; the
agent's copies are not trusted.

### 1.4 Designed contact is not interference

Parts meant to touch are excluded from every interference and clearance check; only penetration counts
(volume above 0.01 mm3), a distance of zero passes:

- the pipe's end face on the socket shoulder (the pipe stop)
- the hose's inside against the spigot body and the ribs: **the ribs are meant to press into the hose** (the
  hose is elastic: crest 17.6 into ID 16.0 by design), so the hose model is never tested for penetration
  against the spigot
- the pipe's outside in the socket bore (radial gap 0.05 to 0.10, may be zero)

---

## 2. Reference models, envelopes and sanity checks

### 2.1 Reference models (M-)

Built by Python from `benchmarks/generalize/parts/generic_tube/part.json` (a parametric stand-in with outer
diameter, inner diameter and length from the request). Positions are the **default seating** (A4), used when a
design declares none.

| Name | What | Source | Size and default position (adapter frame, mm) | Datums |
|---|---|---|---|---|
| **M-HOSE** | the 16 mm hose | catalogue `generic_tube` (OD 22.0, ID 16.0, length 40.0) | tube coaxial with the adapter; its end face on the plane Z = 31.0 (the end of the straight spigot of the default design), running toward -Z (Z -9.0 to 31.0) | `AXIS`, `BORE` (Ø16.0), `END_FAR` |
| **M-PIPE** | the 25 mm pipe | catalogue `generic_tube` (OD 25.0, ID 21.0, length 40.0) | tube coaxial with the adapter; its end face on the socket shoulder (Z 40.0), running toward +Z (Z 40.0 to 80.0) | `AXIS` (Ø25.0), `BORE` (Ø21.0), `END_START` |

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition (adapter frame, mm) | Used by |
|---|---|---|---|
| **V-HOSE-PATH** | the hose being pushed on | M-HOSE translated along +Z from 20.0 below the tip to its seat | L2.2.1 |
| **V-PIPE-PATH** | the pipe being pushed in | M-PIPE translated along -Z from its end face 30.0 above the socket mouth to the shoulder | L2.3.5 |
| **V-BORE** | the through bore | the connected void along the axis from the tip (Z 0) to the shoulder, as measured | L2.5.2 |
| **V-VOID** | any closed internal void | the complement of the body with both bore ends plugged by discs, enclosed components of volume > 1 mm3 | L2.9.2 |
| **V-AP-OTHER** | every other through-path from outside into the bore or socket | rays from outside the hull reaching the bore without hitting a solid, as clusters, other than through the tip and the socket mouth | L2.9.1 |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Model | Check | Pass |
|---|---|---|---|
| R1 | M-HOSE | OD, ID, length | 22.0, 16.0, 40.0, each +/- 0.05 |
| R2 | M-PIPE | OD, ID, length | 25.0, 21.0, 40.0, each +/- 0.05 |
| R3 | M-PIPE | the pipe fits through the nominal socket bore with the stated clearance | socket Ø25.15 minus 25.0 = 0.15 |
| R4 | every V- envelope | its datums equal the model datums it was built from | <= 0.01 |

**Seating rule.** The adapter is placed so that its axis is Z and its tip is at Z = 0 (the declaration in
`layout.json`, L2.1.1). The grader verifies: the declared axis agrees with the fitted axis (<= 0.1), the tip
plane is at Z = 0 within 0.1, and M-PIPE's end face lies on the shoulder (distance <= 0.10, coaxial <= 0.10).
If the declaration is missing or fails, the adapter is normalised by the fit and L3.10.1.2 fails; if there is
no shoulder, the pipe is placed 20.0 into the socket mouth and every L2.3.3 check fails.

---

## 3. Assumptions and fixed decisions

### 3.1 Assumptions (A-rows, with uncertainty)

| # | Question | Value chosen | Why, and how uncertain |
|---|---|---|---|
| **A1** | What is "a barbed 16 mm end with three ribs 0.8 mm tall"? | The spigot body is Ø16.0 (the hose's inner diameter); the three ribs stand 0.8 above it, crest Ø17.6, so the hose is stretched 10 percent over a crest | A barb is oversize on the hose bore to grip. **Alternative:** 16 mm is the crest diameter (body 14.4); then L2.1.1, L2.1.2 and the bore change. Uncertainty: medium; confirm. |
| **A2** | What is "0.15 mm loose"? | A **diametral** clearance: socket bore 25.15, so 0.075 per side | "0.15 loose" is read as bore minus pipe OD. **Alternative:** 0.15 per side (bore 25.30). Uncertainty: medium; confirm. |
| **A3** | Hose and pipe walls | Hose OD 22.0 (3.0 wall); pipe ID 21.0 (2.0 wall), both only used as stand-ins (`generic_tube`) | Not in the brief. The hose OD sets the size of the stop behind the spigot; the pipe wall sets the width of the stop shoulder. Uncertainty: +/-2 on both. |
| **A4** | Default seating (used only if none declared) | Hose end face at Z 31.0; pipe end face on the shoulder at Z 40.0 | The design's own numbers; the grader reads the real ones from the STL. |
| **A5** | Why 45 degrees | Printing upright means every outside surface that faces down must be no steeper than 45 degrees from vertical; the 2 mm wall is read as 2.0 to 2.4 (a perimeter count at 0.4 mm) | Standard FDM overhang limit. |
| **A6** | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed; a brim is allowed and is not part of the model. The spigot end is on the bed (F5): bed contact is a ring | The slender first section needs the brim; the model's own bed contact is >= 80 mm2 and height / bed-face diameter <= 4.0. |
| **A7** | Flow | The bore is Ø12.0 in the spigot (wall 2.0), smaller than the hose; accepted, low flow, not graded beyond the minimum bore 11.2 | The 2 mm wall on a 16 mm spigot fixes it. Confirm if more flow is needed. |
| **A8** | Pressure, leak-tightness | Not graded. No seal groove; the pipe joint is a loose slip fit (0.15), to be sealed with sealant or tape | A hobby adapter; printed parts are not watertight without sealing. |
| **A9** | Size limit | None in the brief; the outside diameter follows from the 2.0 wall (about 29.2 at the socket) | n/a |
| **A10** | Ribs | Pitch >= 5.0; first crest >= 3.0 from the tip; last crest >= 4.0 before the end of the straight spigot; retention flank 30 to 45 degrees from the axis, lead-in flank 10 to 30 degrees | Standard barb practice limited by the 45 degree print rule. Uncertainty: +/-5 degrees. |

### 3.2 Fixed decisions (not open to alternatives)

| # | Decision |
|---|---|
| **F1** | Spigot body Ø16.0, three ribs 0.8 tall (A1). |
| **F2** | Socket bore Ø25.15 (diametral 0.15), constant over a depth of 20.0 (A2). |
| **F3** | The pipe stop is a **flat annular shoulder** perpendicular to the axis at the bottom of the socket. |
| **F4** | A single through bore runs from the spigot tip to the shoulder. |
| **F5** | Print orientation: axis vertical, **spigot end on the bed** (the flat shoulder then faces up). |
| **F6** | Adapter frame as in 1.1 (the grader normalises). |
| **F7** | Exactly three ribs. |

---

## 4. Requirements tree

Column "Gate" names the must-pass groups of section 5; blank = scored only.

### L1.1 The hose end: a 16.0 spigot with three 0.8 mm ribs

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The spigot body between the ribs is the hose's inner diameter. | inspection | core Ø 16.0 +/- 0.1 | 3 | G2 |
| L3.1.1.1 | Core diameter from slices between the ribs (median of the straight stretches). | inspection | 15.9 <= Ø <= 16.1 | 3 | G2 |
| L2.1.2 | Exactly three ribs, each 0.8 tall, spaced and placed along the spigot. | inspection | count = 3; crest height above the core 0.8 +/- 0.1; crest pitch >= 5.0; first crest >= 3.0 from the tip; last crest >= 4.0 before the end of the straight spigot | 3 | G2 |
| L3.1.2.1 | Number of ribs (local maxima of r(z) more than 0.4 above the core). | inspection | 3 | 3 | G2 |
| L3.1.2.2 | Crest height of each rib. | inspection | 0.7 <= h <= 0.9 | 3 | |
| L3.1.2.3 | Crest-to-crest pitch; first crest from the tip; last crest from the end of the straight part. | inspection | >= 5.0; >= 3.0; >= 4.0 | 2 | |
| L2.1.3 | Rib flanks: the retention flank (toward the socket) grips, the lead-in flank (toward the tip) eases the hose on, and both print without support. | inspection | retention flank 30 to 45 degrees from the axis; lead-in flank 10 to 30 degrees | 2 | |
| L3.1.3.1 | Flank angles of each rib (from the profile). | inspection | retention 30 to 45; lead-in 10 to 30 | 2 | |
| L2.1.4 | The hose is not over-stretched. | analysis | crest diameter / core diameter <= 1.15 | 1 | |
| L3.1.4.1 | Stretch ratio. | analysis | <= 1.15 | 1 | |

### L1.2 A gripping length and a stop for the hose

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The straight spigot is long enough for the hose to grip, and the hose can be pushed on along it. | analysis | length from the tip to the start of the widening 25.0 to 33.0; the hose slides along the whole length (only the ribs press into it, by design, 1.4) | 2 | |
| L3.2.1.1 | Straight spigot length (to the Z where r(z), after the last rib, first exceeds the core radius by 0.2). | inspection | 25.0 <= L <= 33.0 | 2 | |
| L3.2.1.2 | Spigot core radius constant between the ribs. | inspection | variation <= 0.1 | 1 | |
| L2.2.2 | The profile widens behind the spigot far enough to stop the hose. | inspection | outer radius >= 11.0 (half the hose OD) within 5.0 above the end of the straight spigot | 2 | |
| L3.2.2.1 | Axial distance from the end of the straight part to the Z where r(z) reaches 11.0. | inspection | <= 5.0 | 2 | |

### L1.3 The pipe end: a 20 mm deep socket, 25.15 bore, with a flat stop

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The socket bore is the pipe's outside diameter plus 0.15 (diametral). | inspection | Ø 25.15 +/- 0.05 | 3 | G3 |
| L3.3.1.1 | Socket diameter (circle fit of the bore at five depths). | inspection | 25.10 <= Ø <= 25.20 | 3 | G3 |
| L3.3.1.2 | Diametral clearance to M-PIPE (bore minus 25.0). | analysis | 0.10 <= c <= 0.20 | 2 | |
| L2.3.2 | Socket depth from the mouth to the shoulder. | inspection | 20.0 +/- 0.2 | 3 | G3 |
| L3.3.2.1 | Depth by ray casting along the axis from the mouth to the shoulder face. | inspection | 19.8 <= d <= 20.2 | 3 | G3 |
| L2.3.3 | A flat shoulder stops the pipe: perpendicular to the axis, wide enough for the pipe wall, and backed by solid material. | inspection | shoulder face within 1.0 degree of perpendicular; annulus radial width >= 3.0; solid thickness under it >= 2.0 | 2 | |
| L3.3.3.1 | Shoulder flatness and angle. | inspection | <= 1.0 degree; planarity <= 0.1 | 2 | |
| L3.3.3.2 | Shoulder annulus width (from the bore edge to the socket wall). | inspection | >= 3.0 | 2 | |
| L3.3.3.3 | Material below the shoulder (axial ray cast through the shoulder annulus). | inspection | >= 2.0 | 1 | |
| L2.3.4 | The bore is constant over the depth, so the pipe slides in the full 20.0. | inspection | bore radius variation over the depth <= 0.05; no step or rib in the socket | 2 | |
| L3.3.4.1 | Socket cylindricity from slices every 1.0 mm. | inspection | <= 0.05 | 2 | |
| L2.3.5 | The pipe pushes in and seats: no interference along the path, and its end face lands on the shoulder with the radial gap 0.05 to 0.10. | test | clear_of(ADAPTER, V-PIPE-PATH, 0.0) with the seated contact excluded; seated end face within 0.10 of the shoulder; minimum radial gap 0.05 to 0.10 | 3 | |
| L3.3.5.1 | Insertion sweep, 1.0 mm steps, to the seat. | test | every step <= 0.01 mm3 | 3 | |
| L3.3.5.2 | Seated gap: end face to the shoulder; minimum radial gap. | test | <= 0.10; 0.05 to 0.10 | 2 | |

### L1.4 A 2 mm wall, nowhere thinner

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Spigot wall and socket wall are 2.0 to 2.4 thick. | inspection | each in [2.0, 2.4] | 3 | |
| L3.4.1.1 | Spigot wall = (core Ø - bore Ø) / 2 between the ribs, median. | inspection | 2.0 <= t <= 2.4 | 3 | |
| L3.4.1.2 | Socket wall = (outer Ø - socket Ø) / 2, median over the depth. | inspection | 2.0 <= t <= 2.4 | 3 | |
| L2.4.2 | No local thickness below 2.0 anywhere (ribs and the transition are thicker). | analysis | minimum local thickness (ray cast along the inward normal, away from the end faces) >= 2.0 | 2 | |
| L3.4.2.1 | Minimum wall by the thin-feature scan. | analysis | >= 2.0 | 2 | |

### L1.5 60 mm long with a through bore on one axis

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | Overall length along the axis. | inspection | 60.0 +/- 0.3 | 3 | G4 |
| L3.5.1.1 | Bounding-box length along Z. | inspection | 59.7 <= L <= 60.3 | 3 | G4 |
| L2.5.2 | A through bore from the tip to the shoulder, with no restriction below 11.2. | analysis | a Ø11.2 cylinder along the axis from Z 0 to the shoulder lies in the void; bore Ø in the spigot 11.2 to 12.0 | 3 | G4 |
| L3.5.2.1 | Through-path of a Ø11.2 sphere sweep along the axis from the tip to the shoulder. | analysis | free | 3 | G4 |
| L3.5.2.2 | Bore diameter in the spigot and along the transition (circle fits). | inspection | 11.2 <= Ø <= 12.0 | 2 | |
| L2.5.3 | All sections are coaxial. | analysis | centre of every slice (outer, bore, socket) within 0.10 of the fitted axis | 2 | |
| L3.5.3.1 | Maximum slice-centre offset along the length. | analysis | <= 0.10 | 2 | |

### L1.6 One smooth transition, no steeper than 45 degrees

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | The outside slope never exceeds 45 degrees from the axis (the end faces excluded); there is no step. | analysis | maximum slope of r(z) <= 45.0 degrees over Z 0 to 60 (ribs and transition included) | 3 | |
| L3.6.1.1 | Maximum slope of the outer profile. | analysis | <= 45.0 degrees | 3 | |
| L2.6.2 | The transition is a gradual widening from the spigot to the socket. | inspection | transition slope between 15 and 45 degrees over its length; r(z) non-decreasing between the end of the straight spigot and the socket outside | 2 | |
| L3.6.2.1 | Transition slope and monotonicity. | inspection | 15 <= slope <= 45; non-decreasing | 2 | |
| L2.6.3 | The transition ends at the socket's outside diameter. | inspection | outer radius at the socket = bore radius + wall (L2.4.1) | 1 | |
| L3.6.3.1 | Socket outer diameter. | inspection | 29.05 <= OD <= 30.05 | 1 | |

### L1.7 Prints upright, spigot end down, without supports

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The declared print orientation is upright with the spigot end on the bed. | inspection | `layout.json` build direction within 1.0 degree of the axis; the spigot tip on the bed | 2 | |
| L3.7.1.1 | Build direction vs fitted axis; end on the bed. | inspection | <= 1.0 degree; spigot end | 2 | |
| L2.7.2 | In that orientation no unsupported overhang steeper than 45 degrees from vertical, except round holes Ø <= 12 in vertical walls and bridges <= 15. | analysis | 0 offending faces (area > 1 mm2) | 3 | G5 |
| L3.7.2.1 | Overhang and bridge scan (E1 rubric 3.6). | analysis | 0 patches | 3 | G5 |
| L2.7.3 | Enough bed contact and a stable height. | analysis | bed contact area >= 80 mm2; height / bed-face diameter <= 4.0 | 2 | |
| L3.7.3.1 | Bed-contact area (faces with n_z < -0.999 at Z < 0.05 on the bed). | analysis | >= 80 mm2 | 2 | |
| L3.7.3.2 | Height over the bed-face diameter (smallest enclosing circle). | analysis | <= 4.0 | 2 | |
| L2.7.4 | No feature thinner than 0.8; the pipe stop and the ribs are printable features. | analysis | min thickness >= 0.8 | 1 | |
| L3.7.4.1 | Thin-feature scan. | analysis | >= 0.8 | 1 | |
| L2.7.5 | The part fits a 200 x 200 x 200 build volume. | inspection | bounding box <= 200 per axis | 1 | |
| L3.7.5.1 | Bounding box. | inspection | <= 200 per axis | 1 | |

### L1.8 One manifold body

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | The mesh is manifold and a single shell. | analysis | 1 shell; manifold3d accepts it; no self-intersection | 3 | G1 |
| L3.8.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |

### L1.9 No opening other than the two bore ends, no cavity

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The only openings are the tip, the socket mouth and the bore between them. | analysis | no region of V-AP-OTHER admits a Ø2.0 sphere from outside into the bore | 2 | |
| L3.9.1.1 | Probe for unlisted openings. | analysis | 0 unlisted paths | 2 | |
| L2.9.2 | No closed internal void. | analysis | V-VOID empty | 1 | |
| L3.9.2.1 | Enclosed void volume. | analysis | <= 1.0 mm3 | 1 | |

### L1.10 The design package says what was built, and its own claims are true

| ID | Requirement / measurement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | The package holds: `adapter.stl` (adapter frame or any frame the layout explains, mm), the `.scad` source, `layout.json` (axis, tip plane, build direction and end on the bed, the declared hose and pipe parameters and seats) and the agent's own measurement report. | inspection | all present and readable | 3 | G0 |
| L3.10.1.1 | Files present and parse; STL in mm: the largest bounding-box axis is 20 to 200. | inspection | true | 3 | G0 |
| L3.10.1.2 | The declared layout verifies under the seating rule (section 2.3). | analysis | axis <= 0.1; tip plane <= 0.1; pipe end face on the shoulder <= 0.10 | 3 | |
| L2.10.2 | The agent's own report agrees with the judge's measurements. | analysis | for every dimension the agent reports (core, rib count and height, socket Ø and depth, wall, length, bore), same pass/fail and \|d_agent - d_judge\| <= 0.10 | 1 | |
| L3.10.2.1 | Self-report vs judge. | analysis | 100 percent agreement within 0.10 | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 10 |
| L2 | 29 |
| L3 | 40 |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.10.1.1); **G1** manifold single
body (L3.8.1.1); **G2** the hose end (L3.1.1.1, L3.1.2.1); **G3** the socket (L3.3.1.1, L3.3.2.1); **G4** length
and through bore (L3.5.1.1, L3.5.2.1); **G5** printable upright without supports (L3.7.2.1).

---

## 6. Feasibility: a design that meets every number

One concrete design, hand-checked against the bands (adapter frame, mm; the loop does not get it). It is a
body of revolution about Z; r is the outside radius.

| Z from to | Feature | Outside radius | Bore radius |
|---|---|---|---|
| 0.0 to 31.0 | spigot: core Ø16.0 with three ribs | 8.0 (ribs to 8.8) | 6.0 (Ø12.0, wall 2.0) |
| 3.8 to 7.2 | rib 1: lead-in flank from (Z 3.8, r 8.0) to the crest (Z 5.8, r 8.8); crest flat to Z 6.2; retention flank to (Z 7.2, r 8.0) | | |
| 11.8 to 15.2 | rib 2 (crest at Z 14.0, same profile) | | |
| 19.8 to 23.2 | rib 3 (crest at Z 22.0, same profile) | | |
| 31.0 to 38.0 | transition cone, 7.0 long | 8.0 rising to 14.575 | 6.0 |
| 38.0 to 60.0 | socket body | 14.575 (OD 29.15) | 6.0 up to Z 40.0, then 12.575 (Ø25.15) to Z 60.0 |

Checks against the bands:

- Core Ø16.0; three ribs, crest Ø17.6 (height 0.8, stretch 17.6 / 16.0 = 1.10 <= 1.15); crest pitch 8.0 (>= 5.0); first crest
  at Z 6.0 (>= 3.0 from the tip); last crest at Z 22.0, 9.2 before the end of the straight part at Z 31.2 (>= 4.0).
- Flanks: retention rise 0.8 over run 1.0 = 38.7 degrees from the axis (30 to 45); lead-in rise 0.8 over run 2.0 =
  21.8 degrees (10 to 30).
- Straight length 31.2 (the radius passes 8.2 at Z 31.0 + 0.2 x 7.0 / 6.575; band 25.0 to 33.0); the radius reaches 11.0 at
  Z 31.0 + 3.0 x 7.0 / 6.575 = 34.2, 3.0 above the end of the straight part (<= 5.0).
- Socket bore Ø25.15 (25.10 to 25.20), diametral clearance 0.15 and radial 0.075; depth 60.0 - 40.0 = 20.0; flat
  shoulder at Z 40.0 with annulus width 12.575 - 6.0 = 6.575 (>= 3.0) and solid below it (axial thickness at the shoulder's outer edge: the
  cone surface there is at Z 35.9, so 4.1; thicker nearer the bore): the pipe's end annulus (r 10.5 to 12.5) lies wholly on the shoulder.
- Walls: spigot 8.0 - 6.0 = 2.0; socket 14.575 - 12.575 = 2.0 (both in 2.0 to 2.4); minimum local thickness 2.0.
- Length 60.0; through bore Ø12.0 from Z 0 to 40.0 (>= 11.2); all sections on the same axis.
- Transition slope atan(6.575 / 7.0) = 43.2 degrees (15 to 45), the largest slope on the outside; r(z) is non-decreasing
  from Z 31.0; the socket OD 29.15 (29.05 to 30.05).
- Printing: the spigot end on the bed: the tip ring (r 6.0 to 8.0) gives pi (8.0^2 - 6.0^2) = 88.0 mm2 (>= 80) of
  bed contact; height 60 / 16 = 3.75 (<= 4.0); every lead-in flank faces down at 21.8 degrees from vertical, the cone faces
  down at 43.2 degrees from vertical (<= 45), the retention flanks and the shoulder face up: no overhang steeper than 45
  degrees, no bridge.

---

## 7. Traceability

| L1 | Owner need (from the brief) | L2 | L3 | JSON L1 | Words in the brief it comes from |
|---|---|---|---|---|---|
| L1.1 | Barbed hose end | L2.1.1-L2.1.4 | L3.1.1.1, L3.1.2.1-3, L3.1.3.1, L3.1.4.1 | L1.1 | "a barbed 16 mm end with three ribs 0.8 mm tall" |
| L1.2 | Hose grip and stop | L2.2.1-L2.2.2 | L3.2.1.1-2, L3.2.2.1 | L1.2 | "16 mm inner diameter hose" |
| L1.3 | Pipe socket | L2.3.1-L2.3.5 | L3.3.1.1-2, L3.3.2.1, L3.3.3.1-3, L3.3.4.1, L3.3.5.1-2 | L1.3 | "a socket for the 25 mm pipe 0.15 mm loose, 20 mm deep" |
| L1.4 | Wall | L2.4.1-L2.4.2 | L3.4.1.1-2, L3.4.2.1 | L1.4 | "a 2 mm wall" |
| L1.5 | Length and bore | L2.5.1-L2.5.3 | L3.5.1.1, L3.5.2.1-2, L3.5.3.1 | L1.5 | "Overall length 60 mm" (the through bore is implied: an adapter) |
| L1.6 | Smooth transition | L2.6.1-L2.6.3 | L3.6.1.1, L3.6.2.1, L3.6.3.1 | L1.6 | "print upright without supports" (A5) |
| L1.7 | Printable upright | L2.7.1-L2.7.5 | L3.7.1.1, L3.7.2.1, L3.7.3.1-2, L3.7.4.1, L3.7.5.1 | L1.7 | "it must print upright without supports" |
| L1.8 | One body | L2.8.1 | L3.8.1.1 | L1.8 | implied |
| L1.9 | Closed | L2.9.1-L2.9.2 | L3.9.1.1, L3.9.2.1 | L1.9 | implied |
| L1.10 | Evidence | L2.10.1-L2.10.2 | L3.10.1.1-2, L3.10.2.1 | L1.10 | needed by the judge |

---

## 8. Grading supplement (design-specific; `generalize/rubric.md` did not exist when this was written)

Procedure, recipes and report format are those of `benchmarks/enclosure/rubric.md` (sections 2, 3 and 5),
applied to the adapter STL, with these specifics:

1. **Inputs.** `adapter.stl` (mm), `.scad`, `layout.json`, self-report, renders. The judge does not use the
   agent's code or transcript, earlier verdicts, or `benchmarks/heldout.json`.
2. **Normalise the frame** (1.1): fit the axis from the bore slices, put the small-diameter end at Z = 0. Record
   the transform.
3. **Build references independently** from the catalogue (`generic_tube` for the hose and the pipe), then the V-
   envelopes (2.2), sanity checks R1 to R4 and the seating rule (2.3).
4. **Recipes.** Profile: slice with `Manifold.slice(z)` or `trimesh.section` at every 0.25 mm, fit the outer
   circle and the bore circle of each section (outer = the largest closed loop, bore = the inner loop),
   record r(z), b(z) and the centre; ribs are the local maxima of r(z) above the core; the flank angles are the
   least-squares slopes of the two sides of each peak; the straight-spigot length ends where r(z), after the last
   rib, first exceeds the core radius plus 0.2 and keeps rising (as L3.2.1.1). Sockets: circle fit at depths 1, 5, 10, 15, 19 mm below the mouth.
   Depth and shoulder: ray cast along Z. The pipe sweep: translate the M-PIPE mesh in 1.0 mm steps from 30.0
   above the mouth to the shoulder; `(ADAPTER ^ M-PIPE).volume()` per step and the radial gap by `min_gap` at the
   seat. The hose is never tested for penetration (1.4). Overhang scan in the declared build direction as
   E1 rubric 3.6.
5. **Classes.** WRONG = any gate (G0 to G5) fails. MINOR = no gate fails but a weight-3 L3 fails. CORRECT = no gate
   fails and every weight-3 L3 passes. **MEETS** = CORRECT and every applicable non-physical L3 of weight 1 and 2
   passes. UNVERIFIED counts as FAIL. Report the weighted score and the worst normalised margin among weight-3
   L3s.
6. **Precedence.** The numbers in this file beat `part.json`. If a catalogue value disagrees, build from this
   file and record a defect on the requirement the stale value breaks, with where = the part.json field.
   Designed contact (1.4) is never interference. Never relax a criterion, never round in the design's favour
   beyond e, never infer a pass from a render.
7. **WHERE a defect is.** One entry per failed or UNVERIFIED L3, most severe first (gates, then weight 3, 2, 1):
   `req` (L3, L2, L1), `status`, `body` (adapter or layout), `feature` (named by function and SCAD name, for
   example "rib 2 retention flank (`barb2`)"), `face` (surface and outward normal), `location` (adapter-frame
   Z range and radius, or a box), `measured` / `limit` / `margin`, `reference` (the M- or V- involved and its
   datum), `render`, `evidence` (saved profile table or defect STL), `needed` (a numeric target, never a design
   instruction). Group L3s that fail for one geometric reason, keeping every id.
8. **Measured-values table (always filled in).**

| Quantity | Limit | Measured |
|---|---|---|
| Core Ø; rib count; crest height; pitch; first / last crest (L3.1.x), mm | 15.9 to 16.1; 3; 0.7 to 0.9; >= 5.0; >= 3.0 / >= 4.0 | |
| Flank angles retention / lead-in (L3.1.3.1), deg; stretch | 30 to 45 / 10 to 30; <= 1.15 | |
| Straight spigot length; distance to r = 11.0 (L3.2.x), mm | 25.0 to 33.0; <= 5.0 | |
| Socket Ø; clearance; depth (L3.3.1.x, L3.3.2.1), mm | 25.10 to 25.20; 0.10 to 0.20; 19.8 to 20.2 | |
| Shoulder angle; width; material below; cylindricity (L3.3.3.x, L3.3.4.1) | <= 1.0 deg; >= 3.0; >= 2.0; <= 0.05 | |
| Pipe sweep max intersection; seat gap; radial gap (L3.3.5.x) | <= 0.01 mm3; <= 0.10; 0.05 to 0.10 | |
| Spigot wall; socket wall; minimum wall (L3.4.x), mm | 2.0 to 2.4; 2.0 to 2.4; >= 2.0 | |
| Length; bore Ø; through-path (L3.5.x), mm | 59.7 to 60.3; 11.2 to 12.0; free | |
| Slice-centre offset (L3.5.3.1), mm | <= 0.10 | |
| Maximum outer slope; transition slope; socket OD (L3.6.x) | <= 45 deg; 15 to 45 deg; 29.05 to 30.05 | |
| Build direction; overhang patches; bed contact; height / bed Ø (L3.7.x) | <= 1.0 deg; 0; >= 80 mm2; <= 4.0 | |
| Shells (L3.8.1.1); unlisted openings; void volume (L3.9.x) | 1; 0; <= 1.0 mm3 | |
| Self-report agreement (L3.10.2.1) | 100 percent within 0.10 | |

---

## Audit

Adversarial audit (second agent). `generic_tube` loads and passes `parts.gate`. L1 = 10, L2 = 29, L3 = 40 recounted (match section 5 and section 7). The section 6 design was built as a revolved profile with manifold3d and measured: one shell, manifold, bounding box 29.15 x 29.15 x 60.0, volume 9570 mm3, overhang area 0.0 mm2 under the rubric rule (the 43.2 degree cone has n_z = -0.684 against the limit -0.707), bed contact 87.9 mm2, and a 25.0 x 21.0 pipe end placed on the shoulder or above it intersects the body by 0.0 mm3 at every position tried. Hand numbers recomputed: crests 17.6 (stretch 1.10), flank angles 38.7 and 21.8, straight length 31.2, r = 11.0 at 3.0 after it, wall 2.0, bore 12.0, height / bed diameter 3.75. The fixed length (60.0) leaves the bands jointly satisfiable: straight >= 25.0, socket 20.0 plus >= 2.0 below the shoulder, so the transition is at most 13.0 long (slope at least 26.8 degrees, inside 15 to 45).

| # | Defect found | Fix |
|---|---|---|
| 1 | Section 8's recipe ended the straight spigot where r(z) exceeds the crest radius plus 0.2, but L3.2.1.1 says the core radius plus 0.2 after the last rib; the two give 32.1 and 31.2 for the same design, so a grader could disagree with itself. | Recipe now uses the core radius plus 0.2, as the L3. |
| 2 | Section 6 said the material under the shoulder was 2.0 thick "from Z 38.0 to 40.0"; at the shoulder's outer edge the cone is at Z 35.9, so it is 4.1. The pass was real but the number was wrong. | Text corrected. |
| 3 | Numbers a gate or weight 2-3 row needs but the agent was never told: rib pitch, first and last crest distances, flank angle bands (G2 rows), straight length 25.0 to 33.0 and the r = 11.0 within 5.0 stop rule, shoulder width, thickness and squareness, seat 0.10, coaxiality 0.10, transition 15 to 45 and monotonic, thin-feature 0.8, self-report 0.10. | Added to the L1 texts in `design.json` (L1.1, L1.2, L1.3, L1.5, L1.6, L1.7, L1.10). No L3 band changed. |
| 4 | Noted, not changed: "16 mm barbed end" (A1) and "0.15 loose" (A2) are fixed as decisions (body 16.0, crest 17.6; diametral 0.15, bore 25.15) with the alternatives recorded; the default hose seat (Z 31.0) is 0.2 before the end of the straight part (31.2) and is only a reference since the hose is never tested for penetration. | None needed. |

Residual uncertainty: the cone passes the 45 degree overhang rule by only 1.8 degrees, and the 2.0 mm walls sit on the lower limit (measurement tolerance 0.02 applies); a 0.4 mm nozzle prints a 2.0 mm wall in 5 perimeters.
