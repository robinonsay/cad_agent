# G35 Cable chain link pair: requirements (L1 / L2 / L3)

Generalisation design G35 (train split). It is the error signal for the control loop on a
mechanism family: two printed links joined by a print-in-place pivot, graded by swept rotation, stop
angles, printed clearances and a cable envelope through the bend. The machine-readable request
(L1 only, `dev.json` format) is `design.json` next to this file. It is graded the way
`benchmarks/enclosure/requirements.md` grades E1-01: Python measures the delivered STL against
reference models (here only a stand-in cable from `benchmarks/generalize/parts/generic_tube`) and
envelopes derived from the design's declared layout.

**Request (owner's words):** "Two links of a cable chain for a 6.5 mm cable, printed in place with
0.35 mm clearance on the pivot. Each link has an inner section 12 x 10 mm and bends 30 degrees either
way before a stop. Print flat without supports." The expanded request in `design.json` adds only what
section 3 derives.

**How to read this.** L1 says what the owner needs. L2 turns each need into an engineering
requirement with numbers. L3 is a concrete check on the geometry. Every row has a verification
method (`dev.json` definitions), a pass/fail criterion with a number and tolerance, a weight
(3 = critical, 2 = major, 1 = minor) and a gate mark (G0 to G5) where failing it makes the design
WRONG. Do not relax a criterion because the agent fails it; change a number only when the owner
corrects an assumption (section 3).

**Grading procedure.** `benchmarks/generalize/rubric.md` holds the generic judge procedure. If that
file is missing, use section 9 of this document, which is self-sufficient.

---

## 1. Frames, tolerances and the checks

### 1.1 Frames

- **Pair frame:** the pair in its straight pose (angle 0), in its print orientation. **Z is up and
  is the pivot axis**; X runs along the chain (link A at -X, link B at +X); Y is across the chain, in
  the bend plane. The origin is on the pivot axis at the pin's centre, on the bed plane Z = 0. A
  design delivered rotated about Z by multiples of 90 degrees, mirrored, or with A and B swapped is
  normalised into this frame before grading (rubric step 2); that is never penalised.
- **Angle:** the rotation of link B about the pivot axis relative to link A, positive counter-
  clockwise seen from +Z. Angle 0 is the straight pose, the channel centrelines collinear.
- **Link frame:** the pair frame with the link's own shell identified by `layout.json` (A is the
  shell fixed in the sweeps; B is the shell rotated).

### 1.2 Measurement tolerances

| Quantity | Measurement tolerance e | Rule |
|---|---|---|
| length, distance, clearance, travel | 0.02 mm | a value passes if it meets the limit to within e |
| angle | 0.1 deg for stop angles, 0.5 deg otherwise | same |
| interference volume | 0.01 mm3 | "no interference" means intersection volume <= 0.01 mm3 |
| hole diameter | largest inscribed circle of the hole's section | what a pin sees |
| pin / head diameter | smallest enclosing circle of the section | |

### 1.3 The checks

- **`clear_of(bodies, volume, clearance)`**: minimum distance between the printed bodies and `volume`
  is >= `clearance` (negative = penetration; volume reported). Pass: d >= clearance - e.
- **`swing(set, range, step)`**: rotate link B (a rigid shell) about the pivot axis through `range`
  in `step` increments; at each angle intersect it with link A. Reported: the largest intersection
  volume and its angle, and the **stop angle**: the smallest |angle| (searched in 0.1 degree steps up
  to 40 degrees, each direction) at which the intersection exceeds 0.01 mm3.
- **`gap(A, B)`**: minimum distance between the two links (`Manifold.min_gap`), at a given angle.
- **`travel(B, axis)`**: rigid free travel of link B in a straight line along `axis` (both
  directions) from its pose, until it first penetrates A by more than 0.01 mm3; the value is the total
  range.

**Designed contact is not interference (owner rule, 2026-10-24).** For G35 the designed contact is
only the **stop**: at and beyond the stop angle, the two stop faces (the link end faces) touch or
penetrate. Nothing else is designed contact: the pin does not touch the bore, and the links do not
touch at any angle below the stop angle (the 0.35 clearance exists for that). Stop contact is
graded only through L3.5.x.

`ALL` means both links together at angle 0.

---

## 2. Reference models, envelopes and datums

### 2.1 Reference models (M-)

| Name | What | Source | Size and datums |
|---|---|---|---|
| **M-CABLE** | the 6.5 mm cable | `generic_tube`, solid (inner diameter 0) | Ø6.5, length 60.0 each side of the joint (A1: an envelope length, any length that runs past the link gives the same result); axis along the channel centreline; datums `AXIS`, `END_START`, `END_FAR` |

The links themselves are the design; there is no catalogue link.

### 2.2 Envelopes (V-) and computed volumes

| Name | What | Definition |
|---|---|---|
| **V-CABLE(theta)** | the cable through the bend at angle theta | two straight Ø6.5 cylinders along the channel centrelines, one in A's frame (from the pivot axis out to 60 beyond A's far end) and one in B's frame (from the pivot axis out to 60 beyond B's far end), meeting at a Ø6.5 sphere on the pivot axis, with B's piece rotated by theta about the pivot axis. The channel centreline of a link is the centre of its inner section, declared in `layout.json` (height Z and Y offset) and verified within 0.3 against the measured inner section. |
| **V-SECTION** | a link's inner section | the empty space inside a link over its straight length, measured by ray casting (the largest axis-aligned rectangle in the YZ section that is free of material, at X stations 1 mm apart along the link) |
| **V-POSE(theta)** | link B rotated | link B rotated about the pivot axis by theta |

### 2.3 Sanity checks on the reference models (grader prerequisites, not L3s)

| ID | Check | Pass |
|---|---|---|
| R1 | M-CABLE: Ø and units | 6.5 +-0.05; length 120 +-0.5 |
| R2 | the pair has exactly two shells | 2 (otherwise L3.1.2.1 fails and the sweeps are skipped) |
| R3 | `layout.json` pivot axis is vertical and passes through both links' bores | axis within 1.0 deg of Z; axis within 0.2 of both bore axes |

**Seating rule.** The pose is the delivered STL at angle 0; the declared pivot axis is verified by R3.
If the declaration fails, the pivot axis is fitted as the common axis of the two links' round bore
and pin features; a design with no round pivot feature fails L3.3.1.1.

---

## 3. Assumptions, uncertainty and fixed decisions

| # | Question | Value chosen | Uncertainty and why |
|---|---|---|---|
| A1 | The cable | a solid Ø6.5 cylinder, flexible enough to follow the polyline of V-CABLE, run 60 mm past each link's far end (the envelope only needs to leave the link) | the owner gave only the diameter; real cables vary +-0.3 and have a minimum bend radius, which is not graded |
| A2 | "Inner section 12 x 10" | 12.0 along the pivot axis (the width between the two plates) by 10.0 across the bend plane (between the two walls) | the owner did not say which is which. If the owner meant 12 across the bend plane, swap the two numbers in L3.2.1.1 / L3.2.1.2; the stop geometry (A9) then changes. Tolerance +-0.2 |
| A3 | Bending plane | the links bend in the plane they are printed in, about a vertical pin | "print flat without supports" with a print-in-place pivot is only possible with a vertical pin; pins with a horizontal axis would need support |
| A4 | Separate bodies | exactly two shells, not touching (gap >= 0.30 at angle 0) | "printed in place" means two parts assembled by printing; any fused joint is a defect |
| A5 | Link length | 20.0 to 40.0 each (the bounding box along X of one link, pivot features included); the straight inner section at least 20 mm long | the owner gave no length; this keeps the pair meaningful and printable. Not from datasheets |
| A6 | Pivot clearance | 0.35 radial (the owner's number, +-0.05) and 0.35 axial (+-0.05) | FDM print-in-place practice: 0.3 to 0.4; +-0.05 is the tolerance |
| A7 | Pin | at least Ø3.0; the pin carries a head that overlaps the bore by at least 0.4 per side; the head's underside is flat at the axial clearance above the tongue (a 45 degree cone is not allowed: its distance to the bore edge is only 0.707 of its vertical gap, so it cannot meet both the 0.30 gap of L3.1.2.2 and the 0.30 to 0.40 axial gap of L3.3.2.1); the pin is fused to one link | the owner did not give a pin size; 3.0 is the smallest printable pin that survives |
| A8 | Printing | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 x 200 x 200 bed; print flat with Z up | common printers. **Print-in-place gap exemption:** a downward face is exempt from the overhang rule when an upward face of either link lies within 0.5 mm (straight-line distance) below it (the printed clearance gap and the 0.35 ring beyond a mating disc) |
| A9 | Stop | the links' end faces stop the bend: the stop angle is the first angle at which the two end faces interfere; target 30 degrees, band 30.0 to 31.0 on each side | the owner says "30 degrees either way before a stop". Printed clearances make 30.0 the lower bound (no stop before 30). The 1.0 band is the tolerance on the stack |
| A10 | Wall and plate thickness | at least 1.6 everywhere except printed gaps; at least 2.0 around the pivot bore on the thinner link plate | 4 perimeters; 5 perimeters around the bore |
| A11 | Play | lateral free travel of B <= 0.8 (the bore clearance gives about 0.7); axial free travel <= 1.2 (the two 0.35 axial gaps give 0.7) | the clearances above set it; +-0.1 |
| A12 | Size limits | each link <= 20 across the bend plane and <= 25 along the pivot axis | keeps the part a chain link, not a block |
| A13 | Material | PLA / PETG; strength is not graded | the pair is a demonstrator |

### Fixed decisions

| # | Decision |
|---|---|
| FD1 | Pair frame as in 1.1. Link A is the one at -X after normalising; it carries the pin (the pin is fused to A). If the pin is on B, swap A and B before grading. |
| FD2 | The 12 mm dimension is along the pivot axis (Z) and the 10 mm dimension is across the bend plane (Y); the channel runs along X. |
| FD3 | Exactly one pivot, on the channel's axis; the two links share one pin. |
| FD4 | The cable passes through the joint along the channel centreline, crossing the pivot axis; nothing printed crosses the cable's path at the pivot (the pin and its head sit below the cable). |
| FD5 | The stop is formed by the links' own faces; no third body. |

---

## 4. Requirements tree

### L1.1 Two separate links in one print, layout declared

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares its layout: the pivot axis (point and direction), the angle-0 pose, which shell is A and which is B, each channel centreline, and the print orientation. | inspection | `layout.json` present, parses, names both shells | 3 | |
| L3.1.1.1 | Layout file parses and names two shells. | inspection | true | 3 | |
| L2.1.2 | Exactly two shells, each one manifold body, and not fused to each other. | analysis | shells = 2; each manifold3d-valid; intersection of A and B <= 0.01 mm3 | 3 | G1 |
| L3.1.2.1 | Shell count and manifold status. | analysis | shells = 2; manifold true | 3 | G1 |
| L3.1.2.2 | The links are separate: no contact at angle 0. | analysis | gap(A, B) >= 0.30 | 3 | G5 |
| L2.1.3 | At angle 0 the two channel centrelines are collinear and the channel is straight. | inspection | centrelines parallel within 1.0 deg and offset <= 0.3 | 2 | |
| L3.1.3.1 | Centreline alignment at angle 0. | inspection | as L2.1.3 | 2 | |

### L1.2 Each link has a straight 12 x 10 inner section with room for the cable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | The inner section is 12.0 along the pivot axis and 10.0 across the bend plane, at least 20 mm long in each link. | analysis | each in tolerance over at least 20 mm of each link's length | 3 | G2 |
| L3.2.1.1 | Inner section height along Z (V-SECTION). | analysis | 12.0 +-0.2 | 3 | G2 |
| L3.2.1.2 | Inner section width along Y (V-SECTION). | analysis | 10.0 +-0.2 | 3 | G2 |
| L3.2.1.3 | Length over which the section holds. | analysis | >= 20.0 per link | 2 | |
| L2.2.2 | The straight 6.5 mm cable passes both links. | test | clear_of(ALL, V-CABLE(0), 0.5) | 3 | G2 |
| L3.2.2.1 | Cable envelope at angle 0. | test | d >= 0.50 | 3 | G2 |

### L1.3 The pivot: 0.35 clearance, captive pin, little play

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | The pin sits in a bore with 0.35 clearance all round; the pin is at least Ø3.0. | inspection | (bore Ø - pin Ø) / 2 = 0.35 +-0.05; pin Ø >= 3.0 | 3 | G5 |
| L3.3.1.1 | Radial pivot clearance. | inspection | 0.30 to 0.40 | 3 | G5 |
| L3.3.1.2 | Pin diameter. | inspection | >= 3.0 | 2 | |
| L2.3.2 | The axial clearances are 0.35 on every face where one link's plate faces the other's (below and above the tongue). | inspection | each in [0.30, 0.40] | 2 | |
| L3.3.2.1 | Axial gaps at the pivot. | inspection | each in [0.30, 0.40] | 2 | |
| L2.3.3 | The pin cannot come out: its head overlaps the bore. | analysis | head Ø - bore Ø >= 0.8 (overlap >= 0.4 per side); free lift of B along +Z (the pin's direction out) <= 1.0 | 2 | |
| L3.3.3.1 | Head overlap. | inspection | >= 0.4 per side | 2 | |
| L3.3.3.2 | Free lift of B off the pin. | analysis | `travel(B, +Z)` positive side <= 1.00 | 2 | |
| L2.3.4 | Tolerance stack: the joint's total play is small. | analysis | lateral `travel(B, X)` and `travel(B, Y)` each <= 0.8; axial `travel(B, Z)` total <= 1.2 | 2 | |
| L3.3.4.1 | Lateral play, along X and along Y. | analysis | each <= 0.80 | 2 | |
| L3.3.4.2 | Axial play, down and up combined. | analysis | <= 1.20 | 2 | |
| L2.3.5 | The material around the bore and the pin is at least 1.6 thick. | analysis | wall around the bore >= 1.6; wall around the pin >= 1.6 where it joins its plate | 2 | |
| L3.3.5.1 | Wall around the bore and pin. | analysis | >= 1.6 | 2 | |

### L1.4 The pair bends freely through 30 degrees either way

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | Swinging B from -29.5 to +29.5 degrees (0.5 steps), the links never touch. | analysis | max intersection <= 0.01 mm3 at every angle | 3 | G3 |
| L3.4.1.1 | Swing interference. | analysis | <= 0.01 mm3 | 3 | G3 |
| L2.4.2 | The links keep at least 0.30 between them for angles up to 20 degrees either way. | analysis | gap(A, V-POSE(theta)) >= 0.30 for theta = -20 to +20 in 5 degree steps | 2 | |
| L3.4.2.1 | Gap over the free range. | analysis | >= 0.30 | 2 | |

### L1.5 Stops block the bend at 30 degrees either way

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The stop angle is 30 degrees each way. | analysis | stop angle in [30.0, 31.0] for each direction | 3 | G4 |
| L3.5.1.1 | Stop angle, positive direction. | analysis | 30.0 to 31.0 deg | 3 | G4 |
| L3.5.1.2 | Stop angle, negative direction. | analysis | 30.0 to 31.0 deg | 3 | G4 |
| L2.5.2 | The stops are symmetric. | analysis | abs(positive stop angle - negative stop angle) <= 1.0 | 2 | |
| L3.5.2.1 | Stop symmetry. | analysis | <= 1.0 deg | 2 | |
| L2.5.3 | The stop faces carry a real load: at 0.5 degrees past the stop, the contact (intersection) region spans at least 10 mm along the pivot axis. | analysis | bounding box of the intersection along Z >= 10.0 | 1 | |
| L3.5.3.1 | Stop contact extent along Z. | analysis | >= 10.0 | 1 | |

### L1.6 The cable passes through the bend

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | At every bend angle in a fan, the cable clears both links. | test | clear_of(A union V-POSE(theta), V-CABLE(theta), 0.2) for theta = -30, -15, 0, 15, 30 | 3 | |
| L3.6.1.1 | Cable envelope through the bend. | test | d >= 0.20 at each angle | 3 | |

### L1.7 Link size and wall thickness

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | Each link is 20 to 40 long, at most 20 across the bend plane and 25 along the pivot axis. | inspection | bounding box of each shell: X extent in [20.0, 40.0]; Y <= 20.0; Z <= 25.0 | 1 | |
| L3.7.1.1 | Link length. | inspection | 20.0 to 40.0 | 1 | |
| L3.7.1.2 | Link width and height. | inspection | Y <= 20.0; Z <= 25.0 | 1 | |
| L2.7.2 | Every wall and plate is at least 1.6 thick (the printed gaps excepted). | analysis | min thickness >= 1.6 | 2 | |
| L3.7.2.1 | Minimum wall or plate thickness. | analysis | >= 1.6 | 2 | |

### L1.8 It prints flat, in one go, without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | In its stated print orientation (the pivot axis vertical within 1.0 deg), no unsupported overhang steeper than 45 degrees from vertical, except round holes up to Ø12.0 in vertical walls, bridges up to 15.0, and the print-in-place gap exemption (A8). | analysis | 0 offending faces (area > 1 mm2) | 2 | |
| L3.8.1.1 | Overhang and bridge scan per link, with the gap exemption. | analysis | as L2.8.1 | 2 | |
| L3.8.1.2 | Print orientation: the pivot axis is vertical. | inspection | within 1.0 deg of Z | 2 | |
| L2.8.2 | Each link rests on a flat face. | analysis | bed contact >= 50 % of the link's plan bounding box | 1 | |
| L3.8.2.1 | Bed-contact area per link. | analysis | >= 50 % | 1 | |
| L2.8.3 | No feature thinner than 0.8 other than the printed gaps; the pin neck at least 1.6. | analysis | min feature >= 0.8 | 1 | |
| L3.8.3.1 | Thin-feature scan. | analysis | as L2.8.3 | 1 | |
| L2.8.4 | The pair fits a 200 x 200 x 200 bed. | inspection | bounding box of both links <= 200 per axis | 1 | |
| L3.8.4.1 | Bounding box. | inspection | <= 200 per axis | 1 | |

### L1.9 The package says what was built, and its own claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | The package holds `pair.stl` (pair frame, mm, two shells), the `.scad` source, `layout.json` and the agent's own report. | inspection | all present and readable | 3 | G0 |
| L3.9.1.1 | Files present and parse; the pair's largest bounding-box axis is within 20 to 200. | inspection | true | 3 | G0 |
| L3.9.1.2 | The declared layout verifies under the seating rule. | analysis | pivot axis within 1.0 deg of Z and within 0.2 of both bores; centrelines within 0.3 of the measured section centres | 3 | |
| L2.9.2 | The agent's own report agrees with the judge's measurements. | analysis | same pass / fail and abs(d_agent - d_judge) <= 0.10 (angles <= 0.5 deg) for every `clear_of`, `swing`, `gap`, `travel` L3 reported | 1 | |
| L3.9.2.1 | Self-report versus judge. | analysis | 100 % agreement within the stated tolerance | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 9 |
| L2 | 24 |
| L3 | 34 |

Gates (a failure makes a design WRONG regardless of score): **G0** package (L3.9.1.1); **G1** two
manifold shells (L3.1.2.1); **G2** the inner section and the cable pass (L3.2.1.1, L3.2.1.2,
L3.2.2.1); **G3** free swing through 29.5 degrees each way (L3.4.1.1); **G4** the stops at 30
degrees (L3.5.1.1, L3.5.1.2); **G5** the pivot clearance and no fusing (L3.3.1.1, L3.1.2.2).

---

## 6. Feasibility

A link pair exists that meets every number above. It was built in `manifold3d` and measured (the
numbers below are readings from the model). Pair frame, mm, pivot axis at the origin, Z up:

- **Each link:** a floor 4.35 thick (Z 0 to 4.35), two side walls 2.0 thick (Y 5 to 7 and -7 to -5),
  a top plate 2.0 thick (Z 16.35 to 18.35) bridging the 10.0 gap, so the inner section is
  **10.0 (Y) x 12.0 (Z)** (Z 4.35 to 16.35). Link A body: X -25.875 to -1.875 (24.0 long); link B
  body: X 1.875 to 25.875. Outer width 14.0, height 18.35.
- **Stop faces:** each link's end faces (walls and top plate) at X = -1.875 (A) and +1.875 (B), a
  3.75 gap at angle 0. Rotating B about the origin, its wall corner (1.875, 7.0) reaches A's end face
  when 1.875 cos(t) - 7.0 sin(t) = -1.875, which gives t = 30.0 degrees. The model reads free through
  30.0 degrees (intersection 0.0), 0.0128 mm3 at 30.2, 0.075 mm3 at 30.5, 0.29 mm3 at 31.0: stop angle
  30.2 degrees on each side (L3.5.1.1/2 pass, symmetric), contact along the full 18 mm wall height.
- **Pivot:** link A has a thin plate (Z 0 to 2.0, radius 4.5 about the axis plus a strip toward A's body)
  carrying a pin Ø4.0 (Z 2.0 to 4.7) and a flat-underside head Ø5.7 (Z 4.7 to 5.9, 1.2 thick). Link B has a tongue plate (Z 2.35 to 4.35, radius 4.5 plus a strip toward
  B's body) with a bore Ø4.7. Radial clearance (4.7 - 4.0) / 2 = 0.35; axial gaps 2.35 - 2.0 = 0.35 below the
  tongue and 4.70 - 4.35 = 0.35 above it (flat head underside, so the vertical and the straight-line gap agree); head overlap (5.7 - 4.7) / 2 = 0.5 per side.
- **Reliefs:** B's floor is cut away (Z 0 to 2.35) inside radius 4.85 about the axis, so A's thin plate
  (radius 4.5) turns inside it with 0.35; A's floor is cut away (Z 2.0 to 4.7) inside radius 4.85, so
  B's tongue (radius 4.5) turns inside it with 0.35. B's tongue strip is 9 wide (|y| <= 4.5), so it stays within radius
  4.5 of the axis at the strip's inner end.
- **Measured (the audit rebuilt this pair in manifold3d and read all of these from it):** shells 1 + 1, intersection 0.0, gap at angle 0 0.350; no interference at any angle from
  -30 to +30 in 0.5 steps (the stop contact starts at 30.2); gap 0.348 at 20 degrees; B's free travel
  0.70 along X and Y (contact at 0.35 each side), lift 0.35 above the pin, 0.35 down
  (axial total 0.70); cable Ø6.5 on the channel centreline (Z 10.35, Y 0) clears both links by 1.2
  at -30, 0 and +30 degrees (the head top is Z 5.9; the cable's underside is Z 7.1). The straight 10.0 x 12.0
  section holds from X -25.875 to -4.85 in link A (21.0 long, over 20) and from 4.85 to 25.875 in B; the 3 mm
  next to the pivot has the thinned floor (relief).
- **Print:** floors on the bed, pivot axis vertical, the tongue's underside is 0.35 above A's thin
  plate (gap exemption), the pin head has a flat underside 0.35 above the tongue (gap exemption), the top plates bridge 10.0.

---

## 7. Where this stresses the agent (beyond_library)

1. A print-in-place joint in two bodies with gaps of 0.35 on every face.
2. Swept rotation, and stop geometry derived from an angle limit and the link's width.
3. Relief cuts so two bodies share a pivot region without touching.
4. A cable envelope bent through the joint.
5. A print-orientation analysis with a gap exemption.

---

## 8. Traceability

| L1 | Owner need | L2 | L3 | Words in the request it comes from |
|---|---|---|---|---|
| L1.1 | Two links, separate | L2.1.1-L2.1.3 | L3.1.1.1, L3.1.2.1-2, L3.1.3.1 | "Two links of a cable chain", "printed in place" |
| L1.2 | Inner section | L2.2.1-L2.2.2 | L3.2.1.1-3, L3.2.2.1 | "6.5 mm cable", "inner section 12 x 10 mm" |
| L1.3 | Pivot clearance | L2.3.1-L2.3.5 | L3.3.1.1-2, L3.3.2.1, L3.3.3.1-2, L3.3.4.1-2, L3.3.5.1 | "0.35 mm clearance on the pivot" |
| L1.4 | Free bend | L2.4.1-L2.4.2 | L3.4.1.1, L3.4.2.1 | "bends 30 degrees either way" |
| L1.5 | Stops | L2.5.1-L2.5.3 | L3.5.1.1-2, L3.5.2.1, L3.5.3.1 | "before a stop" |
| L1.6 | Cable through bend | L2.6.1 | L3.6.1.1 | "for a 6.5 mm cable" |
| L1.7 | Link size | L2.7.1-L2.7.2 | L3.7.1.1-2, L3.7.2.1 | implied |
| L1.8 | Printable | L2.8.1-L2.8.4 | L3.8.1.1-2, L3.8.2.1, L3.8.3.1, L3.8.4.1 | "Print flat without supports" |
| L1.9 | Evidence | L2.9.1-L2.9.2 | L3.9.1.1-2, L3.9.2.1 | needed by the judge |

---

## 9. Grading rules (self-contained fallback for `generalize/rubric.md`)

Use `/Users/robinonsay/python/llm-bt/venv/bin/python` with `manifold3d` and `trimesh`; count shells with
`Manifold.decompose()`.

1. **Package (G0), units.** Load `pair.stl`; its largest axis must be 20 to 200 mm.
2. **Normalise** into the pair frame (rotations by multiples of 90 degrees about Z, mirroring, A / B swap).
3. **Split** the shells with `decompose()`; identify A and B from `layout.json` (the shell with the pin is A).
4. **Measure every L3** in order: measured value, limit, signed margin (negative = fail), PASS / FAIL /
   UNVERIFIED. UNVERIFIED counts as FAIL.
5. **Recipes.** `swing`: rotate B about the declared pivot axis (`Manifold.rotate` about Z after translating the
   axis to the origin), intersect with A, record the volume; stop angle by stepping 0.1 degrees up to 40.
   `gap`: `A.min_gap(B_rotated, 1.0)`. `travel`: translate B along an axis in 0.02 steps until the intersection
   exceeds 0.01 mm3, both directions. V-CABLE: two cylinders and a sphere, B's rotated. Inner section:
   cast rays along Y and Z from the channel centre at 1 mm X stations and report the free
   width and height; L3.2.1.1 and L3.2.1.2 use the median over the stations, and L3.2.1.3 is the length
   of the stations (each 1 mm) at which both are within tolerance (the stations over the pivot relief and
   the pin head do not count). Bore and pin diameters: largest inscribed / smallest enclosing circle of a slice at
   mid-height of the feature. Overhang: faces with n_z < -cos 45 degrees not on the bed, minus holes up to
   Ø12, bridges up to 15, and downward faces with an upward face of either link within 0.5 below them.
6. **Class.** WRONG: any gate fails. MINOR: no gate fails but a weight-3 L3 fails. CORRECT: no gate
   fails and all weight-3 L3s pass. **MEETS** = CORRECT and every applicable non-physical weight-1 and
   weight-2 L3 passes. Also report the weighted score and the worst normalised margin among weight-3 L3s.
7. **Precedence.** The numbers in this document beat `part.json`; if they disagree, build the references from
   this document and record a defect against the requirement that the stale catalogue number breaks. The
   stop is the only designed contact. The cable envelope (L3.2.2.1, L3.6.1.1) and the swing (L3.4.1.1)
   outrank every size L3.
8. **Where.** One entry per failed or UNVERIFIED L3: `req`, `status`, `body` (A / B / both / layout), `feature`,
   `face` (with outward normal), `location` (pair-frame bounding box in mm), `measured` / `limit` / `margin`
   (with the angle), `reference` (model or envelope), `needed` (a numeric target the next agent can verify,
   never a design instruction), `evidence` (saved defect STL). Separate observations from defects.

---

## Audit

Adversarial audit (2026-10-24). Checked: `generic_tube` exists and passes `parts.gate`; L1 count 9 (in 8 to 14);
counts in section 5 (9 / 24 / 34) match the tables; every L2 has an L3. `benchmarks/generalize/rubric.md` does not
exist, so section 9 is the procedure. The Feasibility pair was rebuilt in `manifold3d` from section 6
(it reproduced the stated 0.0128 / 0.075 / 0.29 mm3 stop volumes and 0.70 play exactly) and every L3 that
can be run was run on it: two shells, gap 0.350, swing free to 29.5 each way, stop 30.2 each way with contact
over 18.35 along Z, gap >= 0.347 for -20 to +20, free travel, cable clearance at -30 to +30, inner section,
overhang scan with the exemptions. Fixes, all in place:

1. **Axial gap above the tongue was not 0.35.** The conical head made the vertical gap from the tongue top to
   the head 0.70 at the bore edge (0.495 straight-line), so L3.3.2.1 (each axial gap in 0.30 to 0.40) failed on
   the feasibility pair, and the "4.70 - 4.35" arithmetic measured to a surface that is not above the tongue.
   A 45 degree cone cannot satisfy this and L3.1.2.2 / L2.4.2 (gap >= 0.30) together (straight-line gap = 0.707
   x vertical gap: vertical 0.35 gives 0.247, which the rebuilt pair showed). The head now has a flat underside
   0.35 above the tongue (Z 4.70, head Ø5.7, top Z 5.9, 1.2 thick, was a 0.65 thick rim). Result: both axial gaps
   0.35, straight-line gap 0.350, axial play 0.70 (was claimed 1.1), lift 0.35, cable clearance 1.2.
   A7, A11, L2.3.3 text and the Feasibility numbers updated.
2. **Print-in-place exemption was too narrow.** "Within 0.5 above an upward face of the other link" left the
   0.35 ring of the tongue underside beyond A's disc and the head underside above the bore void flagged
   (about 4 and 2 mm2, over the 1 mm2 limit). A8 and the recipe now say: exempt when an upward face of either
   link lies within 0.5 straight-line below. With that, the only unexempt down-facing faces are the two 10.0
   top-plate bridges (allowed, <= 15).
3. **Section-length ambiguity (L3.2.1.1 to 3).** Near the pivot the floor is thinned, so the free height there is
   14.35, not 12.0. The recipe now says medians for the two sizes and that L3.2.1.3 counts the stations that
   hold (21.0 in the feasibility pair, over 20).
4. **Hidden numbers.** Pin diameter and head overlap (A7, L2.3.3) and the 1.2 axial play (A11) were judged but
   never given to the agent: added to the request and L1.3 in `design.json`. The 60 mm cable length in M-CABLE
   was labelled "(request)" but is not in the request; relabelled as an envelope length (A1).

Checked and left unchanged: stop geometry (14 wide, 3.75 gap gives contact at 29.99 degrees, intersection
above 0.01 mm3 from 30.2, inside the 30.0 to 31.0 band), lateral play 0.70, bed contact (A 90 %, B 75 %), link
size (30.4 x 14 x 18.35), tongue and plate thickness 2.0, cable envelope at -30, -15, 0, 15, 30.
