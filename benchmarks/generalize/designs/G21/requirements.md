# G21 MG996R servo mount with gussets: requirements (L1 / L2 / L3)

Training design of the generalisation set (family mechanical_mount; capabilities load_path, pocket_fit, bolt_pattern,
tolerance_stack, slot_engagement). The machine-readable request (L1 only, `dev.json` format) is `design.json` next to
this file. It is modelled on `benchmarks/enclosure/requirements.md` (E1-01) and uses the same conventions: tolerances
(1.2), `clear_of` and designed contact (1.3), reference models and envelopes (2), assumptions with uncertainty and
fixed decisions (3), a tree whose every L3 is measured by Python on the delivered STL (4), gates (5), a feasibility
sketch (7) and traceability (8).

**Brief (plan.json, verbatim):** "A heavy-duty mount for an MG996R servo (40.7 x 19.7 x 42.9 mm, tab hole spacing 49.5 mm)
onto a 2020 extrusion, with two gussets to resist a 1.5 N m torque reaction. The servo drops in a pocket with 0.3 mm
clearance and is fixed with four M4 bolts. Show the load path to the extrusion bolts."

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

### 1.1 Frame

- **Mount frame:** X along the extrusion axis, Y across it, Z up, Z = 0 on the extrusion's top face (the face that carries
  the flange); the extrusion occupies Z −20 to 0 and Y ±10. The cable end of the servo is +X. The grader normalises a
  design delivered rotated by multiples of 90° about Z or mirrored in X; never penalised.
- **Servo frame** (catalogue `servo_mg996r`): origin at the tab-end min corner on the bottom face; X along the tabs, Y across,
  output spline on +Z at the low-X end. In the mount frame servo Z = mount +Z (shaft up) and servo X = mount X.
- Lengths in mm, angles in degrees, forces in N, stresses in MPa, moments in N·mm.

### 1.2 Measurement tolerances

All measurements are made by Python on the delivered mesh, never by eye.

| Quantity | ε | Rule |
|---|---|---|
| length, distance, clearance | 0.02 mm | a value passes if it meets the limit within ε |
| angle | 0.5° | same |
| intersection volume | 0.01 mm³ | "no interference" means ≤ 0.01 mm³ |
| hole diameter | largest inscribed circle of the hole section | what a bolt sees |
| boss OD | smallest enclosing circle | |
| depth | ray cast along the axis from the top plane | |

### 1.3 Interference checks and designed contact

- **`clear_of(bodies, volume, c)`**: minimum distance between the printed body and `volume` is ≥ c − ε, penetration ≤ 0.01 mm³.
- **`inside(volume, void, c)`**: `volume` lies in `void` with every point ≥ c − ε from the boundary.

`bodies` is ALL (the one printed body) or BASE (the same body); the extrusion, nuts, bolts and servo are reference models
that the grader builds itself from the catalogue and the declared layout.

**Designed contact for this design (never interference; only penetration > 0.01 mm³ counts for these pairs):**
1. the servo tab undersides resting on the block top; M4 bolt shank in a tab hole and in its pilot; bolt head on the tab top,
2. the flange underside lying on the extrusion top face, including while the mount slides along the slot,
3. M5 bolt shank in its flange hole and head on the flange top; T-nut top against the lip underside; bolt thread in the nut.

A distance of zero is a pass for these pairs.

---

## 2. Reference models, envelopes, datums

### 2.1 Reference models (M-)

Built from the catalogue (`benchmarks/generalize/parts/<part>/part.json`, `generic` numbers from the request) at the
pose declared in `layout.json`.

| Name | What | Source | Size and datums used |
|---|---|---|---|
| **M-SERVO** | MG996R servo | `servo_mg996r` | body 40.7 × 19.7 × 42.9; tabs 53.6 × 19.7 × 2.6 at 26.5 above the bottom; spline Ø5.8 × 4.0 at 10.0 from the low-X body end; tab holes Ø4.0 (A2); datums `BOTTOM`, `TAB_BOTTOM`, `TAB_TOP`, `HOLE` (4 catalogue axes: X ±24.75, Y ±5.0 about the tab centre, A2), `SPLINE_AXIS`, `SPLINE_TIP`, keep-outs `horn_sweep` (Ø50.0 × 2.0 on the spline axis, 2.0 below the spline tip) and `cable_exit` (10.0 × 19.7 × 6.0 beyond the high-X body end, from the bottom) |
| **M-EXTR** | 2020 extrusion, length ≥ 300 | `extrusion_2020` (length from the request) | 20 × 20 section, four slots: opening 6.2, depth 6.1, lip 1.8, inner width 11.0, bore Ø4.2; the slot cavities are built from these parameters (2.2) |
| **M-TNUT-j** (j = 1, 2) | M5 T-nut | `tnut_2020_m5` | plate 10.0 (across the slot) × 9.7 (along it) × 3.5; bearing face against the lip underside; thread M5; `AXIS` |
| **M-BOLT5-j** | M5 button-head bolt | `bolt_m5_iso7380` | thread Ø5.0, head Ø9.5 × 2.75, clearance Ø5.5; length declared in `layout.json` (stock 8, 10, 12, 16, 20) |
| **M-BOLT4-i** (i = 1..4) | M4 socket bolt | `bolt_m4_iso4762` | thread Ø4.0, head Ø7.0 × 4.0, tap Ø3.3, clearance Ø4.5; length declared (stock 8, 10, 12, 16, 20) |

### 2.2 Envelopes (V-) and computed volumes

| Name | Definition | Used by |
|---|---|---|
| **V-SLOT** | the T-slot cavity of the top slot of M-EXTR: neck 6.2 wide from the top face to 1.8 deep, then cavity 11.0 wide from 1.8 to 6.1 deep, full length | L2.5.3 |
| **V-DROP** | M-SERVO body and tabs swept along +Z from the seated pose to 60 above it | L2.2.4 |
| **V-CABLE** | the servo `cable_exit` keep-out at the seated pose | L2.4.1 |
| **V-HORN** | the servo `horn_sweep` disc at the seated pose (horn off for L2.3.4) | L2.4.2 |
| **V-SPLINE** | cylinder Ø5.8 along the spline axis from the servo top to 4.0 above it (the output spline) | L2.4.2 |
| **V-DRIVER4-i** | Ø6.0 column on the axis of M4 bolt i from the head top, 50 up, horn and cable off | L2.3.4 |
| **V-DRIVER5-j** | Ø6.0 column on the axis of M5 bolt j from the head top, 50 up | L2.8.3 |
| **V-SLIDE** | the printed body translated along X by ±100 (the mount sliding with the bolts loosened) | L2.8.2 |
| **V-SECTION** | the section of the delivered body by the plane Z = flange top + 0.1 (block plus gusset roots, from the mesh) | L2.6.2, L2.7.2, L2.7.3 |

### 2.3 Seating rule

M-SERVO is seated at the pose in `layout.json`; the grader verifies it: `TAB_BOTTOM` lies on the block top (distance ≤ 0.10),
servo tab-hole axes are coaxial with the four pilots (residual ≤ 0.25 at the block top plane). M-TNUT-j and M-BOLT5-j are
seated on the flange hole axes (nut bearing face against the lip underside). If the layout is missing or fails, the
grader seats by that fit; with no pocket and no pilots every L1.2 and L1.3 check fails.

---

## 3. Assumptions, fixed decisions and open questions for the owner

Each line gives the value chosen and why. All derived from the brief, the catalogue or convention; none asked.

| # | Question | Value chosen | Why and uncertainty |
|---|---|---|---|
| A1 | Servo dimensions? | Body 40.7 × 19.7 × 42.9; tabs 53.6 long, 2.6 thick (±0.4), tab underside 26.5 above the bottom (±1); spline at 10.0 (±1.5), Ø5.8, 4.0 high; horn reach 25.0. | Brief and `servo_mg996r` part.json. Specimens differ by about 0.5 mm: measure the owner's servo. |
| A2 | Four tab holes? | Two holes per tab, 49.5 apart along X and 10.0 apart across the tab (`hole_row_spacing`, ±1.0), so the four holes are at X ±24.75, Y ±5.0 (servo-centre frame). The request states the two spacings and `servo_mg996r/part.json` carries the four-hole datum `HOLE`. Hole Ø4.0 (part.json, ±0.5); an M4 shank in a tab hole is designed contact. | Real MG996R tabs carry two holes each. Audit change: the catalogue previously held only two centreline axes, which left the cross-tab spacing hidden. |
| A3 | Torque reaction and horn load? | M = 1.5 N·m = 1500 N·mm about the servo output axis. It is the stated reaction and is taken as the design load; the horn side force is F_h = M / 25.0 = 60 N (horn reach from part.json) at the horn plate mid-height, in the worst horizontal direction (across the extrusion). | Brief; horn geometry from part.json (reach ±4). |
| A4 | Extrusion and T-nut? | Generic 2020 (HFS5-2020 drawing values): opening 6.2, slot depth 6.1, lip 1.8 (±0.3), inner width 11.0 (±0.5); T-nut 10.0 × 9.7 × 3.5 (±0.3), M5. The top slot (+Z) is used. | part.json of `extrusion_2020`, `tnut_2020_m5`. Lip and inner width are assumed from drawings. |
| A5 | Printed-material allowables? | PLA, layers horizontal. Thread shear 4.0 MPa on the pilot's cylinder (π · pilot Ø · engagement); junction shear 2.0; junction bending 3.0; bearing under a bolt head 5.0. | PLA is 40 to 50 MPa in-layer and 10 to 20 across layers; the figures include a factor of about 4 for layer lines and creep. ±30 percent. |
| A6 | Extrusion-side rating and factors? | T-nut and lip pull-out rating 1000 N per nut; the design limit is 500 N (safety factor 2). Tab-bolt thread strength must be ≥ 3 times the bolt shear. | Typical 2020 vendor figures are 1 to 2 kN; 1000 N is conservative. ±50 percent. |
| A7 | Assembly order? | The horn and the cable are fitted after the M4 bolts are tightened, so the M4 driver columns are graded without the horn. | The horn is screwed on the spline last. |
| A8 | Self-tapping into printed pilots? | M4 into a Ø3.3 pilot (catalogue `tap_diameter`); engagement = bolt length − 2.6 (tab thickness) must be ≥ 8.0 (two thread diameters) and ≤ pilot depth − 0.5. | PLA threads need about 2 × d. |
| A9 | Printing? | FDM, PLA or PETG, 0.4 nozzle, 0.2 layers, 200 × 200 × 200 bed. Wall and floor ≥ 2.4. Round holes Ø ≤ 12.0 and bridges ≤ 15.0 print unsupported; no face steeper than 45° from vertical. | design_rules.json values. |
| A10 | Servo mass? | 55 g, ignored (below 2 percent of the horn load). | Datasheet figure. |
| A11 | Extrusion length and nut placement? | At least 300 (request); each nut centre at least 5.0 from an extrusion end; nuts at least 2.0 apart. | The mount sits far from the ends. |
| A12 | Wire strain relief, labels, fillets? | None required or graded. | Not in the brief. |

### Fixed decisions (one choice, no alternatives accepted)

| # | Decision | Why |
|---|---|---|
| FD1 | One printed body: a flange on the extrusion's top face, a block on the flange with an upward-opening pocket, two gussets. The servo's output axis is vertical (+Z); the tabs rest on the block top; servo X is along the extrusion; the cable end is +X. | "The servo drops in a pocket". |
| FD2 | The flange's underside is flat and lies on the extrusion's top face (Z = 0); two M5 bolts go down through the flange into two T-nuts in the single top slot, on the slot centreline, heads on the flange top (no counterbore). Nothing of the mount is below Z = 0. | "Bolt into a T-nut ... slides along the slot". |
| FD3 | The gussets lie in YZ planes, one on the +Y face and one on the −Y face of the block, centred on the block's X centre, each a right triangle on the flange. | They resist overturning across the extrusion (the worst direction, A3). |
| FD4 | The cable channel is a cut through the block's high-X end wall from the pocket to the outside, covering `cable_exit`. | The keep-out must be free of material. |
| FD5 | Print pose = assembly pose (flange underside on the bed). | Pocket opens upward; no bridging. |

---

## 4. Requirements tree

### L1.1 Placement from the catalogue and layout declared

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.1.1 | The design declares the layout: pose of M-SERVO, M-EXTR, each M-TNUT (X position), each bolt (axis, length), print pose. | inspection | `layout.json` present, parses, names the catalogue ids | 3 | |
| L3.1.1.1 | Layout parses and every catalogue id exists. | inspection | true | 3 | G0 |
| L2.1.2 | The servo's output shaft is vertical. | inspection | `SPLINE_AXIS` within 1.0° of +Z | 3 | |
| L3.1.2.1 | Spline axis direction. | inspection | ≤ 1.0° | 3 | |
| L2.1.3 | The reference models do not collide (designed contact aside). | analysis | pairwise intersection of M-SERVO, M-EXTR, M-TNUT, M-BOLT4, M-BOLT5 ≤ 0.01 mm³ | 3 | |
| L3.1.3.1 | Pairwise interference of the reference models. | analysis | ≤ 0.01 mm³ each pair | 3 | |
| L2.1.4 | The extrusion lies along X and the top slot faces +Z. | inspection | extrusion axis within 1.0° of X; top slot axis +Z | 2 | |
| L3.1.4.1 | Extrusion axis and slot direction. | inspection | ≤ 1.0° | 2 | |

### L1.2 The servo drops into the pocket with 0.3 clearance and its tabs rest on the block

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.2.1 | 0.3 mm clearance per side round the servo body. | analysis | min distance from the body (40.7 × 19.7 prism) to each pocket wall in [0.25, 0.35] | 3 | |
| L3.2.1.1 | Body-to-wall clearance on all four sides. | analysis | 0.25 ≤ g ≤ 0.35 | 3 | G2 |
| L3.2.1.2 | Pocket inside size at mid-depth. | inspection | X 41.3 ± 0.10; Y 20.3 ± 0.10 | 2 | |
| L2.2.2 | The servo does not bottom out. | analysis | pocket floor to the servo bottom 0.3 to 2.5; material under the floor to the flange underside ≥ 2.4 | 3 | |
| L3.2.2.1 | Floor-to-servo-bottom gap (pocket depth − 26.5). | analysis | 0.3 ≤ g ≤ 2.5 | 3 | G2 |
| L3.2.2.2 | Material under the pocket floor. | inspection | ≥ 2.4 | 2 | |
| L2.2.3 | The tabs rest on the block top. | analysis | `TAB_BOTTOM` within 0.10 of the block top, no penetration; the block top is flat across the tab footprint | 3 | |
| L3.2.3.1 | Tab-to-top gap and penetration. | analysis | 0 ≤ g ≤ 0.10; penetration ≤ 0.01 mm³ | 3 | |
| L3.2.3.2 | Block-top flatness over the tab footprint. | inspection | ≤ 0.10 | 2 | |
| L2.2.4 | The servo drops straight down without touching the block. | test | clear_of(BASE, V-DROP, 0.2) with the tab-underside contact excluded | 3 | |
| L3.2.4.1 | Drop-in sweep clear. | test | d ≥ 0.20 | 3 | G2 |

### L1.3 Four M4 bolts through the tab holes into pilots, reachable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.3.1 | Four pilot holes under the four tab holes. | inspection | count = 4; each axis within 0.25 of its tab-hole axis at the block top plane; axis within 1.0° of Z | 3 | |
| L3.3.1.1 | Pilot count. | inspection | = 4 | 3 | G3 |
| L3.3.1.2 | Pilot-to-tab-hole axis offset. | analysis | ≤ 0.25 each | 3 | G3 |
| L3.3.1.3 | Pilot axis direction. | inspection | ≤ 1.0° | 2 | |
| L2.3.2 | Pilot geometry for a self-tapping M4 (A8). | inspection | Ø 3.3 ± 0.15; depth ≥ max(8.0, engagement + 0.5), engagement = bolt length − 2.6 ≥ 8.0; wall from a pilot to the pocket, the outer faces and the channel ≥ 1.6 | 3 | |
| L3.3.2.1 | Pilot diameter. | inspection | 3.15 ≤ Ø ≤ 3.45 | 3 | G3 |
| L3.3.2.2 | Pilot depth and engagement. | inspection | depth ≥ engagement + 0.5; engagement ≥ 8.0 | 2 | |
| L3.3.2.3 | Wall round each pilot. | analysis | ≥ 1.6 | 2 | |
| L2.3.3 | The M4 bolts fit with the servo: nothing printed touches a bolt head or shank except the pilot. | analysis | clear_of(ALL ∪ M-SERVO, M-BOLT4 heads, 0.0) with head-on-tab contact excluded; no penetration of the shank other than the pilot and the tab hole | 2 | |
| L3.3.3.1 | M4 bolt interference. | analysis | ≤ 0.01 mm³ | 2 | |
| L2.3.4 | A screwdriver reaches every M4 bolt (horn off, A7). | test | clear_of(ALL ∪ M-SERVO, V-DRIVER4-i, 0.0), i = 1..4 | 2 | |
| L3.3.4.1 | M4 driver columns clear. | test | d ≥ 0.0 for all four | 2 | |

### L1.4 The servo's keep-outs are free of material

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.4.1 | The cable exit is free. | analysis | clear_of(ALL, V-CABLE, 0.0) | 3 | |
| L3.4.1.1 | Cable keep-out clear. | analysis | d ≥ 0.0, penetration ≤ 0.01 mm³ | 3 | |
| L2.4.2 | The horn sweep and the spline are free. | analysis | clear_of(ALL, V-HORN ∪ V-SPLINE, 0.0) | 2 | |
| L3.4.2.1 | Horn sweep and spline zone clear. | analysis | d ≥ 0.0 | 2 | |

### L1.5 The flange is bolted into the T-slot of the extrusion by two M5 bolts

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.5.1 | The flange sits flat on the extrusion top face. | analysis | flange underside within 0.10 of Z = 0; flatness ≤ 0.2; penetration of M-EXTR ≤ 0.01 mm³ | 3 | |
| L3.5.1.1 | Flange underside seating. | analysis | 0 ≤ g ≤ 0.10; penetration ≤ 0.01 mm³ | 3 | G4 |
| L3.5.1.2 | Flange underside flatness. | inspection | ≤ 0.2 | 2 | |
| L2.5.2 | Exactly two M5 clearance holes on the slot centreline. | inspection | count = 2; Ø 5.5 ± 0.2; axis within 1.0° of Z and within 0.5 of the slot centreline in Y; spacing along X in [60, 110] | 3 | |
| L3.5.2.1 | M5 hole count. | inspection | = 2 | 3 | G4 |
| L3.5.2.2 | M5 hole diameter. | inspection | 5.3 ≤ Ø ≤ 5.7 | 3 | G4 |
| L3.5.2.3 | Hole axis direction and offset from the slot centreline. | analysis | ≤ 1.0°; ≤ 0.5 | 2 | |
| L3.5.2.4 | Hole spacing along X. | inspection | 60.0 ≤ s ≤ 110.0 | 2 | |
| L2.5.3 | The T-nuts sit in the slot, coaxial with the holes. | analysis | M-TNUT-j inside V-SLOT with 0.3 clearance to the cavity walls (the lip-underside contact excluded); nut axis coaxial with its hole ≤ 0.3; nuts ≥ 5.0 from the ends and ≥ 2.0 apart | 3 | |
| L3.5.3.1 | Nut in the slot cavity. | analysis | penetration of M-EXTR ≤ 0.01 mm³; side clearance ≥ 0.30 | 3 | |
| L3.5.3.2 | Nut-to-hole coaxiality. | analysis | ≤ 0.3 | 3 | |
| L3.5.3.3 | Nut placement along the slot. | inspection | ≥ 5.0 from the ends; ≥ 2.0 apart | 1 | |
| L2.5.4 | Tolerance stack: each M5 bolt reaches its nut and clears the slot floor. | analysis | tip depth below Z = 0 is t_tip = bolt length − flange thickness at the hole; nominal window 5.3 ≤ t_tip ≤ 5.8 (nut back at lip 1.8 + nut 3.5 = 5.3; slot floor 6.1 − 0.3); worst-case engagement min(t_tip − 2.1, 3.2) ≥ 3.0 | 3 | |
| L3.5.4.1 | Tip depth window (declared bolt length, measured flange thickness). | analysis | 5.3 ≤ t_tip ≤ 5.8 | 3 | G4 |
| L3.5.4.2 | Worst-case thread engagement in the nut. | analysis | ≥ 3.0 | 2 | |
| L3.5.4.3 | Bolt head clear: flange ligament round the head and distance to the block and gussets. | analysis | head Ø9.5 edge ≥ 3.0 from the flange edges; head to block and gussets ≥ 1.0 | 2 | |

### L1.6 Two gussets stiffen the block

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.6.1 | Exactly two gussets, on opposite sides of the block. | inspection | count = 2; one on +Y and one on −Y; centred on the block X centre within 1.0 | 3 | |
| L3.6.1.1 | Gusset count and sides. | inspection | = 2, opposite | 3 | |
| L3.6.1.2 | Gusset thickness. | inspection | 3.0 ≤ t ≤ 8.0 | 2 | |
| L3.6.1.3 | Gusset size. | inspection | root length along the flange ≥ 10.0; height up the block ≥ 15.0 | 2 | |
| L3.6.1.4 | Gusset fused to block and flange. | analysis | contact area with the block ≥ 60 mm²; with the flange ≥ 40 mm² | 2 | |
| L2.6.2 | The gussets raise the junction's bending stiffness. | analysis | I_x(V-SECTION) ≥ 1.25 × I_x(block footprint alone) | 2 | |
| L3.6.2.1 | Stiffness ratio at the junction. | analysis | ≥ 1.25 | 2 | |
| L2.6.3 | The gussets do not crowd the M5 bolts. | analysis | clear_of(gussets, M-BOLT5 heads ∪ V-DRIVER5-j, 0.0) | 2 | |
| L3.6.3.1 | Gusset-to-bolt clearance. | analysis | d ≥ 0.0 | 2 | |

### L1.7 The 1.5 N·m torque reaction: the load path to the extrusion bolts

Load path to be stated in `load_path.json` and recomputed by the grader. Symbols from the measured mesh and the
declared layout: M = 1500; tab holes at radii r_i from the centroid of the four tab-hole axes; pilot Ø_p and
engagement e (L2.3.2); J_p the polar moment of the block footprint in V-SECTION; r_max its farthest point; F_h = M/25.0
= 60; h the height above Z = 0 of the horn plate mid-height (servo bottom Z + 45.9); the pivot is the extrusion edge, bolt line
to edge y_p = 10.0; x_L the spline X; bolts at x1 and x2; I_x and c the section inertia about its centroid axis parallel to X
and its largest Y distance for V-SECTION; D_h the measured M5 hole Ø.

- Tab bolt shear: V_i = M · r_i / Σ r²; thread strength F_thr = 4.0 · π · Ø_p · e.
- Junction torsion: τ = M · r_max / J_p.
- Overturning: M_o = F_h · h; T_tot = M_o / y_p; lever rule on X: T_1 = T_tot (x2 − x_L)/(x2 − x1), T_2 = T_tot − T_1.

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.7.1 | The tab bolts carry the torque. | analysis | F_thr ≥ 3 · max V_i | 3 | |
| L3.7.1.1 | Tab-bolt thread strength ratio. | analysis | F_thr / max V_i ≥ 3.0 | 3 | G5 |
| L2.7.2 | The block-to-flange junction carries the torque. | analysis | τ ≤ 2.0 | 2 | |
| L3.7.2.1 | Junction shear stress. | analysis | ≤ 2.0 | 2 | |
| L2.7.3 | The extrusion bolts carry the overturning load. | analysis | max T_j ≤ 500; head bearing σ_b = T_j / (π/4 (9.5² − D_h²)) ≤ 5.0; junction bending σ = M_o · c / I_x ≤ 3.0; x1 ≤ x_L ≤ x2 | 3 | |
| L3.7.3.1 | M5 bolt tension. | analysis | max T_j ≤ 500 | 3 | G5 |
| L3.7.3.2 | Head bearing stress on the flange. | analysis | ≤ 5.0 | 3 | |
| L3.7.3.3 | Junction bending stress. | analysis | ≤ 3.0 | 2 | |
| L3.7.3.4 | The spline lies between the two bolts in X. | analysis | x1 ≤ x_L ≤ x2 | 2 | |
| L2.7.4 | The load path is continuous. | analysis | one connected body; V-SECTION a single connected region | 2 | |
| L3.7.4.1 | Continuity of the path from the block top to the flange underside. | analysis | shells = 1; V-SECTION regions = 1 | 2 | |

### L1.8 It slides on the slot and the M5 bolts are reachable

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.8.1 | Nothing of the printed body is below the extrusion top face. | inspection | min Z of the body ≥ −0.02 | 2 | |
| L3.8.1.1 | Lowest point of the body. | inspection | ≥ −0.02 | 2 | |
| L2.8.2 | With the bolts loosened the mount slides along X without hitting the extrusion. | test | V-SLIDE ∩ M-EXTR ≤ 0.01 mm³ (flange-on-top contact is designed) | 2 | |
| L3.8.2.1 | Slide sweep. | test | ≤ 0.01 mm³ | 2 | |
| L2.8.3 | A screwdriver reaches each M5 bolt. | test | clear_of(ALL ∪ M-SERVO, V-DRIVER5-j, 0.0) for j = 1, 2 | 2 | |
| L3.8.3.1 | M5 driver columns clear. | test | d ≥ 0.0 | 2 | |

### L1.9 One manifold body that prints without supports

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.9.1 | One manifold shell. | analysis | 1 shell; manifold3d accepts it | 3 | |
| L3.9.1.1 | Shell count and manifold status. | analysis | shells = 1; manifold = true | 3 | G1 |
| L2.9.2 | No unsupported overhang in the print pose (FD5). | analysis | 0 offending faces (area > 1 mm²); round holes Ø ≤ 12.0 and bridges ≤ 15.0 exempt | 2 | |
| L3.9.2.1 | Overhang and bridge scan. | analysis | 0 patches | 2 | |
| L2.9.3 | It rests on a flat face. | analysis | bed contact ≥ 50 percent of the plan bounding box | 1 | |
| L3.9.3.1 | Bed-contact area. | analysis | ≥ 50 percent | 1 | |
| L2.9.4 | No thin features. | analysis | min local thickness ≥ 0.8 | 1 | |
| L3.9.4.1 | Thin-feature scan. | analysis | ≥ 0.8 | 1 | |
| L2.9.5 | It fits the bed. | inspection | bounding box ≤ 200 per axis | 1 | |
| L3.9.5.1 | Bounding box. | inspection | ≤ 200 | 1 | |

### L1.10 Size

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.10.1 | Overall size. | inspection | X ≤ 130.0, Y ≤ 70.0, Z ≤ 45.0 | 1 | |
| L3.10.1.1 | Bounding box. | inspection | as L2.10.1 | 1 | |

### L1.11 The package says what was built and its claims are true

| ID | Requirement | Method | Pass/fail (tolerance) | Wt | Gate |
|---|---|---|---|---|---|
| L2.11.1 | Package: `mount.stl` (assembly pose, mount frame, mm), the `.scad`, `layout.json`, `load_path.json` (M, r_i, V_i, F_thr, F_h, h, M_o, T_j, σ values) and the agent's own report. | inspection | all present and readable | 3 | |
| L3.11.1.1 | Files parse; the STL is in mm (largest bounding-box axis 50 to 200). | inspection | true | 3 | G0 |
| L3.11.1.2 | Declared layout verifies under the seating rule (2.3). | analysis | tab bottom on the block top ≤ 0.10; pilot residual ≤ 0.25; flange on the extrusion ≤ 0.10; nut coaxiality ≤ 0.3 | 3 | |
| L2.11.2 | The agent's own reports agree with the judge. | analysis | each `clear_of` d within 0.10; each load-path number within 10 percent | 1 | |
| L3.11.2.1 | Self-report clearances vs judge. | analysis | same pass/fail, \|Δd\| ≤ 0.10 | 1 | |
| L3.11.2.2 | `load_path.json` numbers vs judge. | analysis | within 10 percent | 1 | |

---

## 5. Counts and gates

| Level | Count |
|---|---|
| L1 | 11 |
| L2 | 36 |
| L3 | 59 (all measured by Python on the STL) |

Gates (a failure makes the design WRONG regardless of score): **G0** package (L3.1.1.1, L3.11.1.1); **G1** one manifold
shell (L3.9.1.1); **G2** the pocket fit and the drop-in (L3.2.1.1, L3.2.2.1, L3.2.4.1); **G3** the M4 pilots
(L3.3.1.1, L3.3.1.2, L3.3.2.1); **G4** the extrusion mount (L3.5.1.1, L3.5.2.1, L3.5.2.2, L3.5.4.1);
**G5** the load path (L3.7.1.1, L3.7.3.1).

---

## 6. Design-specific rubric (the generic rubric was absent when this was written)

### 6.1 Procedure

1. G0: files exist and load; if the STL is missing or unreadable stop (DOES NOT MEET, one defect on L3.11.1.1).
2. Units: largest bounding-box axis within 50 to 200; if inches or metres record a defect, do not rescale.
3. Normalise the frame (1.1) with rotations by multiples of 90° and X mirroring only; record the transform.
4. Build the models and V- envelopes independently (2); verify the seating rule (2.3).
5. Run every applicable L3 with Python in order; record value, limit, signed margin (negative = fail), PASS / FAIL /
   UNVERIFIED (counts as FAIL).
6. Look at renders afterwards; render-only findings are observations.
7. Decide (6.3), report (6.4).

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

- **Pocket:** slice at Z = block top − depth/2; polygon bounding box = pocket X × Y; wall gaps = pocket polygon edges to the
  servo body rectangle; floor Z by a downward ray cast; V-DROP = the body and tab solids extruded along +Z by 60.
- **Pilots and holes:** slice at mid-depth for the largest inscribed circle (Ø) and the centre (axis point); depth by ray
  cast along the axis; direction from slices at two heights. M5 holes: slice at mid-thickness of the flange.
- **V-SLOT and nuts:** build the neck and cavity boxes from the part.json parameters; `inside(M-TNUT, V-SLOT, 0.3)` ignoring
  the lip contact (the nut top face on the lip underside is a zero-distance pair).
- **Tip depth:** t_tip = declared bolt length − (flange top Z − 0); check the declared length against the stock list.
- **Gussets and section:** slice at Z = flange top + 0.1; polygon union; `connected` by the number of regions; I_x about the
  centroid axis (sum over triangles); block footprint alone = the rectangle of the block cross-section without the gussets.
  Gusset contact areas: the area of coincident faces of the gusset solid with the block and the flange (intersection of
  the gusset solid grown by 0.01).
- **Load path:** compute r_i, Ø_p, e, J_p, r_max, h, x1, x2, x_L, D_h from the mesh and layout; apply the formulas of L1.7.
- **Apertures and bridging:** as in the enclosure rubric (ray grid of 1 mm; bridge = a downward face whose ends rest on
  material at most 15 apart).
- **Printability:** transform to the print pose; a face with normal n overhangs if n_z < −cos 45° and z > 0.05, minus round
  holes Ø ≤ 12 and bridges ≤ 15. Bed contact: area of faces with n_z < −0.999 at z < 0.05 over the plan bounding-box area.
  Thin features: inward ray cast.

### 6.3 Classes

| Class | Rule |
|---|---|
| **WRONG** | any gate G0..G5 fails |
| **MINOR** | no gate fails but a weight-3 L3 fails |
| **CORRECT** | no gate fails and every weight-3 L3 passes |
| **MEETS requirements** | CORRECT and every applicable non-physical weight-1 and weight-2 L3 passes |

Also report the weighted score Σ(weight × pass)/Σ(weight) over applicable L3s and the worst normalised margin among
weight-3 L3s. Precedence: numbers in this file beat `part.json` (record a defect on the L3 it breaks, where = the
part.json field); designed contact (1.3) is never interference; never relax a criterion; never infer a pass from a render.

### 6.4 How to say WHERE a defect is

One entry per failed or UNVERIFIED L3 (all of them), most severe first (gates, then weight 3, 2, 1). Fields: `req` (L3, L2,
L1), `status`, `feature` (by function and SCAD name, e.g. "pilot under tab hole (+24.75, +5.0)"), `face` (surface and outward
normal), `location` (mount-frame coordinates, a point or a box), `measured / limit / margin`, `reference` (the model or
envelope and its datum), `render`, `evidence` (saved files), `needed` (a numeric target, never a design instruction).
Group L3s with one geometric cause under the first and list the others in `also_fails`; separate observations from defects.

---

## 7. Feasibility (a concrete design that meets every L3)

Mount frame, mm; one body, print pose = assembly pose.

| Feature | Value |
|---|---|
| Flange | X ±58 (116), Y ±28 (56), Z 0 to 6.5, flat underside on the extrusion top (Y ±10) |
| Block | X ±28.5 (57), Y ±15 (30), Z 6.5 to 36.5 (height 30.0) |
| Pocket | X ±20.65 (41.3), Y ±10.15 (20.3), Z 9.5 to 36.5 (depth 27.0, floor 3.0 over the flange top) |
| M-SERVO | centred at X 0, Y 0; bottom Z 10.0 (36.5 − 26.5); tab underside on the block top; spline X −10.35, tip Z 56.9; cable end +X |
| Tab holes and pilots | (±24.75, ±5.0), pilot Ø3.3, depth 10.5 (Z 36.5 to 26.0), bolts M4 × 12 (engagement 9.4) |
| Cable channel | through the +X end wall, X 20.65 to 28.5, Y ±10.15, Z 9.5 to 16.5 with a 45° gable roof to Z 26.65 at Y 0; `cable_exit` box (X 20.35 to 30.35, Y ±9.85, Z 10.0 to 16.0) inside it |
| Gussets | 2, in YZ planes at X ±2.5 (5.0 thick), on the ±Y block faces (Y 15 to 27 on the flange, up to Z 26.5 on the block); right triangles 12 × 20 |
| M5 holes | (±50, 0), Ø5.5 through the 6.5 flange; M5 × 12 bolts, heads on the flange top; T-nuts at X ±50 in the top slot |

Checks by hand:
- Pocket: gaps 0.30 each side; floor Z 9.5 under the servo bottom Z 10.0 gives 0.5 (in [0.3, 2.5]); material under the floor 9.5
  (≥ 2.4). Tabs rest on Z 36.5. Pilot wall to the pocket end: 24.75 − 1.65 − 20.65 = 2.45 ≥ 1.6; pilot tip Z 26.0 is above
  the channel gable at |Y| 5 (Z 21.65): 4.35 of material.
- Keep-outs: `cable_exit` inside the channel by 0.3 (Y) and 0.5 (Z); the horn disc (Z 54.9 to 56.9, radius 25 about X −10.35)
  is 18 above the block top and 28 above the gusset tops, nothing printed is near it.
- Extrusion mount: M5 tip depth t_tip = 12 − 6.5 = 5.5, window 5.3 to 5.8 (0.2 past the nut back at 5.3, 0.6 short of the
  slot floor at 6.1); worst-case engagement min(5.5 − 2.1, 3.2) = 3.2 ≥ 3.0. Nut Y ±5.0 in the cavity ±5.5: 0.5 ≥ 0.3. Head
  edge 3.25 from the flange end (≥ 3.0); head to the gusset toe at X 2.5, Y 27 is 47 away.
- Gussets: thickness 5.0; root 12.0 ≥ 10; height 20.0 ≥ 15; contact with the block 20 × 5 = 100 mm² ≥ 60, with the flange
  12 × 5 = 60 mm² ≥ 40. I_x: block 57 × 30³ / 12 = 128 250; gussets 2 × (5 × 12³ / 12 + 60 × 21²) = 54 360; total 182 610;
  ratio 1.42 ≥ 1.25.
- Load path: r_i = √(24.75² + 5²) = 25.25; Σ r² = 2550; V_i = 1500 / (4 × 25.25) = 14.85 N; F_thr = 4.0 · π · 3.3 · 9.4 = 390 N;
  ratio 26.2 ≥ 3. J_p = (57 × 30³ + 30 × 57³)/12 = 5.91 × 10⁵; τ = 1500 × 32.2 / 5.91 × 10⁵ = 0.08 ≤ 2.0. Horn: F_h = 60;
  h = 10.0 + 45.9 = 55.9; M_o = 3354; T_tot = 335.4; x_L = −10.35, x1 = −50, x2 = +50: T_1 = 335.4 × 60.35 / 100 = 202.4,
  T_2 = 133.0; max 202.4 ≤ 500. Bearing 202.4 / 47.1 = 4.30 ≤ 5.0. Bending σ = 3354 × 27 / 182 610 = 0.50 ≤ 3.0.
- Slide: nothing below Z = 0; the flange sliding on the top face is designed contact. Driver columns at (±50, 0) and at the
  four tab holes are clear (the horn is off).
- Size 116 × 56 × 36.5 (limits 130, 70, 45). Print: flange underside on the bed (bed contact 100 percent); pocket and pilots
  vertical; gable roof 45°; gusset slope 31° from vertical; holes are round Ø ≤ 12.

---

## 8. Traceability

| L1 | Owner need (from the request) | L2 | L3 | JSON L1 | Method | Words in the request |
|---|---|---|---|---|---|---|
| L1.1 | placement | L2.1.1-4 | L3.1.1.1, L3.1.2.1, L3.1.3.1, L3.1.4.1 | L1.1 | inspection | "MG996R servo", "2020 aluminium extrusion", "output shaft up" |
| L1.2 | pocket fit | L2.2.1-4 | L3.2.1.1-2, L3.2.2.1-2, L3.2.3.1-2, L3.2.4.1 | L1.2 | test | "drops straight down into a pocket ... 0.3 mm clearance per side" |
| L1.3 | four M4 bolts | L2.3.1-4 | L3.3.1.1-3, L3.3.2.1-3, L3.3.3.1, L3.3.4.1 | L1.3 | inspection | "four M4 socket-head bolts fix it through the tab holes" |
| L1.4 | servo keep-outs | L2.4.1-2 | L3.4.1.1, L3.4.2.1 | L1.4 | analysis | implied (cable, spline, horn) |
| L1.5 | extrusion mount | L2.5.1-4 | L3.5.1.1-2, L3.5.2.1-4, L3.5.3.1-3, L3.5.4.1-3 | L1.5 | inspection | "bolted into the T-slot ... two M5 bolts and T-nuts" |
| L1.6 | gussets | L2.6.1-3 | L3.6.1.1-4, L3.6.2.1, L3.6.3.1 | L1.6 | inspection | "two gussets stiffen the block" |
| L1.7 | torque and load path | L2.7.1-4 | L3.7.1.1, L3.7.2.1, L3.7.3.1-4, L3.7.4.1 | L1.7 | analysis | "torque reaction of 1.5 N m", "Show the load path" |
| L1.8 | slide and reach | L2.8.1-3 | L3.8.1.1, L3.8.2.1, L3.8.3.1 | L1.8 | test | "T-slot" (slides until tightened), implied reach |
| L1.9 | printable | L2.9.1-5 | L3.9.1.1, L3.9.2.1, L3.9.3.1, L3.9.4.1, L3.9.5.1 | L1.9 | analysis | "printed in PLA on an FDM printer without supports" |
| L1.10 | compact | L2.10.1 | L3.10.1.1 | L1.10 | inspection | "heavy-duty mount" (limit is an assumption) |
| L1.11 | evidence | L2.11.1-2 | L3.11.1.1-2, L3.11.2.1-2 | L1.11 | inspection | needed by the judge (not the owner's words) |

---

## Audit

Adversarial audit (second agent). Method: the catalogue parts load and pass `parts.validate` / `parts.gate`; every number of
section 7 was recomputed (pilot and nut geometry, tip depth, I_x ratio 1.42, J_p, tab-bolt shear 14.85 N, thread strength
390 N, bolt tensions 202.4 / 133.0 N, bearing 4.30 MPa, bending 0.50 MPa: all confirmed); the feasibility design was then
built as one solid with the reference solids (manifold3d) and run against the geometric L3s: 1 shell, servo to block
interference 0, pocket gaps 0.30, drop-in sweep clear, cable keep-out gap 0.30, horn disc 18.4 above the block, all
four M4 and both M5 driver columns clear, slide sweep 0, V-SECTION 1 region, size 116 × 56 × 36.5. No geometric
contradiction was found. `claude-context` was unavailable (server failed to connect), so targeted grep was used. The generic
`generalize/rubric.md` still does not exist; section 6 is this entry's rubric (it follows `benchmarks/enclosure/rubric.md`).

Fixes made (all in place):
1. **Hidden hole spacing.** The four tab holes at Y ±5.0 were a judge number that neither the request nor
   `servo_mg996r/part.json` gave (the catalogue held two centreline axes). Fixed in the catalogue: new param
   `hole_row_spacing` (10.0, assumed ±1.0) and a four-axis `HOLE` datum (HOLE[0], HOLE[1] stay the pitch pair, so the old
   self-check still holds; two new self-checks); the request now says "two holes per tab, 49.5 mm apart along the tab
   and 10 mm apart across it". A2 and the M-SERVO row were rewritten to match. The part still gates clean.
2. **Hidden allowables and model in L1.7.** The judge's PLA allowables (4 / 2 / 3 / 5 MPa), 500 N per T-nut, the factor 3,
   the horn-force model (torque over the 25 mm reach, tipping about the extrusion edge, lever rule on X) and the
   bolt-share rule were only in section 3 and L1.7's table. They are now in the L1.7 text the agent receives.
3. **Other hidden numbers moved into L1:** pocket floor gap 0.3 to 2.5 (L1.2); bolts on the slot centreline, 60 to 110 apart,
   spline between them (L1.5); 3 mm of flange round each head (L1.5); gusset thickness 3 to 8, root at least 10, height at
   least 15, stiffness ratio at least 1.25 (L1.6).

Checked and left unchanged: counts (11 / 36 / 59), L1 count 11, no duplicate ids, units, gates, load-path arithmetic, the
extrusion and T-nut parts (`length` parameters come from the request, as the catalogue requires). Residual uncertainty:
tab thickness, tab height, hole Ø and cross-tab spacing are assumed (part.json notes); the tab hole's edge ligament to the
tab end is only 0.05 mm with Ø4.0 at 49.5 pitch on a 53.6 tab (a consequence of the brief's numbers, not graded).
