# Iteration 003: gap analysis and delta 003

Analyst step, 2026-10-25. Code at run time: `de77b7ab88b1` (sha1 of `iter_003/code_sha1.txt`). `shasum -c` matched every
file at analysis time, so the code has not changed since the Run. claude-context failed to connect in this step (the MCP
server did not start), so files were found with targeted reads and grep. Nothing under `../holdout/` or
`holdout_results/` was opened, listed or searched. No agent code was edited.

**Correction to the loop record (P-3, data only, done in this step).** The orchestrator wrote `verdicts.json` with a
boolean `meets` and no `verdict` string. `run_suite.verdict_flags` reads only `verdict`, so `summary.json` counted the
regression set as MEETS 0 and reported **regression `fail`**, although all four regression judges wrote MEETS. A normalised
copy, `iter_003/verdicts_normalised.json` (adds `"verdict": "MEETS" | "DNM"` from `meets`; the original file is unchanged),
was re-cached with `cache_verdicts.py 003`. `summary.json` now reads **regression `pass`** (meets 4, correct 4) and train
MEETS 0 / CORRECT 1. Backups of the cache and summary from before the re-cache are in the session scratchpad. The tooling
fix that stops this from recurring is C0 below.

---

## 1. Measured error signal

| Run | rc | Verdict | Score | Gates failed (judge) and other defects |
|---|---|---|---|---|
| E1-01, V1, V2, V3 | 0 | **MEETS** ×4 | 1.0 | none. V1 is fixed (both ports on −X), as delta 002 forecast |
| G04 | 3 | DNM / **CORRECT** | 0.99 | none. One w1 miss: Y 42.22 > 40.0, because the corner lid bosses sit outside the walls (the agent's only failing check, `bbox` −2.21) |
| G02 | 0 | WRONG | 0.84 | **G5** no vent slots in the lid. Also w3: lip lid, not the plate-in-rebate that L1.8 asks for. w2: the USB-B opening has a flat 16.8 mm roof (bridge > 15.0). 78/78 agent checks pass, so none of the three was sensed |
| G06 | 3 | WRONG | 0.51 | G2 no 30° tilt or sloped panel; G4 Pico unplaced; G5 no USB opening. w2: 4 bosses where the text says 2 at the rear corners; no window |
| G08 | 0 | WRONG | 0.41 | G0/G1 no door body; G2 no cell or cradle; G4 no switch slot; G5 no door. w2: 4 bosses where the text says 2; no shelf |
| G11 | 0 | WRONG | 0.35 | **G5** no exhaust slots on the end wall opposite the jack; G4 no fan, fan pilots or lid opening. w3: heatsink missing; lid 2.4 thick where the text says 4.8–6 |
| G13 | 3 | WRONG | 0.30 | G0/G5 no buttons, plungers or plunger holes; no plunger body. w2: lip lid, not a rebate. (Agent: `bbox` Z 37.8 > 35, grid conflict for the Pico) |
| G50 | 3 | WRONG | 0.30 | G3 no fan or vents; G4 no OLED window or encoder hole; G5 no snap latches |

Train: **MEETS 0 / CORRECT 1 (G04) / no-output 33 of 40.** rc: 0 ×3 (G02 G08 G11), 3 ×4 (G04 G06 G13 G50), 1 ×33. No
timeouts. 54 run rows: the first ten designs ran twice because the Run step restarted. Both runs used the same code, and
all ten pairs agree in rc, stop and **canonical geometry hash**. This is the first evidence that delta 002's C3 hash is
stable across runs.

No-output stops (33):
- contents 28:
  - `nothing to design around` 17: G16 G17 G18 G20 G21 G22 G24 G27 G30 G31 G32 G33 G35 G36 G38 G40 G45.
  - `primary <id> has no mount_holes interface` 6: G03 G10 G12 (generic_box), G05 (esp32), G09 (dc jack), G47 (hc_sr04).
  - `no number in the text` 5: G26 G29 G42 G43 (generic_tube), G37 (gear).
- choose_archetype 3: G23 G41 G49 (no shell evidence, as designed).
- arrange_contents 2: G01 G14 (no catalogue screw passes the Nano's holes).

The changes since iteration 002 come from controller variance across seeds, not from code. G08 now gives a package (the
cell is not listed at all, so the Pico is the primary). G40 moved from choose_archetype to contents, and G42 and G43 moved
from "nothing to design around" to "generic_tube: no number".

**Delta 002 did what it forecast.** The regression set is fixed (V1 MEETS). G04 is CORRECT 0.99, and its only defect is
the w1 bbox miss that delta 002 predicted. G02 went from 3 failed gates to 1 (vents). G11 went from 3 to 2. Board pilots
are now right in every judged package: G02 Ø2.5 × 8.5, G04 Ø2.1 × 6.7, E1-01 boss pilots 7.7.

## 2. Defects → root causes (traced to the agent, not to the design)

| Defect (designs, rows) | Root cause in the agent | Class | Milestone |
|---|---|---|---|
| **D-BOSS-OUT**: lid bosses outside the walls push the closed size past the limit (G04 L3.11.1.1 w1, the only defect; G13's bbox fails too, but on Z) | `derive_features` has **one** boss layout: four diagonal corner pilasters outside the cavity (`rule:lid_to_fastening.corner_pilaster`). The `bbox` sensor sees the failure (−2.21), but no derivation choice can act on it. Prescore varies only the arrangement, and every arrangement has the same pilasters. **The sensor has no actuator.** | missing discrete alternative (derive level) | GM3 (screw closure through the generic rule) |
| **D-LID-FORM**: lip lid where the text asks for a plate in a wall rebate (G02 L3.8.2.x w3, fixed decision F2; G13 L3.8.2.1 w2) | The only closure is `lid` plate + `lid_lip`. No closure vocabulary exists, and no rule reads "rebate". The rebate form also needs bosses **under** the plate, inside the walls, which the D-BOSS-OUT layout cannot give. | missing rule + evidence vocabulary | GM9 (shell closures), first slice |
| **D-VENT**: no vent slots (G02 gate G5 + L3.7.x; G11 gate G5 L3.7.2.1; G50 gate G3, partly) | No vent capability exists. The vent numbers in the text (G02 L1.7: 5–9 slots, 1.5–3.0 × 8–12, pitch 3.5–6.5, ≥ 100 mm²; G11 L1.7: ≥ 8 slots, 2–4 wide, ≥ 10 tall, ≥ 567 mm²) are left unmapped. Nothing knows where "over the ATmega328P" is: the Uno has a point datum `MCU`, but no footprint and no name for it. The verification matrix lists G02 L1.7 as UNLINKED. | missing capability + catalogue datum | GM4 (vent slice; ARCHITECTURE 1b refinement 5) |
| **D-BRIDGE**: a box opening wider than the bridge limit gets a flat roof (G02 L3.10.1.1 w2: 16.8 > 15.0) | `derive_port_cut` always emits a flat-topped box. `rules.bridge_max` (15.0) exists, but **no sensor reads it**: nothing in assembly.py or assembly_checks.py mentions bridge or overhang. G02 passed 78/78 of its own checks. By the audit rule, the sensor comes first, then the derivation term (a 45° roof). Note: G04's HDMI opening is 17.8, and G04's requirements raise its bridge limit to 20 because a roof cannot fit inside its oversize band. A roof rule must therefore yield to the stated oversize. | missing sensor + derivation term | GM5 (`printable`), first slice |
| **D-SECONDARY**: named parts unplaced or never listed (G06 Pico; G08 cell, switch; G11 fan, heatsink; G13 buttons; G50 fan, OLED, encoder) | RC-C of iteration 002, unchanged. Contents offers four kinds, and a non-carrier primary carries nothing. | missing capability | GM2b |
| D-CLOSE-COUNT: 4 bosses where the text says 2 (G06, G08 w2) | The boss count is fixed at 4. The quantity word before the lid-role screw ("two M3 screws") is not read. | missing rule | GM3 / GM2b (named fastener with a quantity) |
| D-LID-T: lid 2.4 thick where the text says 4.8–6 (G11 w3) | The lid thickness is `cavity.wall`, and no slot reads a lid-plate band. | missing slot | with the fan-on-lid pilots (GM2b + GM3) |
| Single-design capabilities: G06 tilt and window, G08 door and third body, G13 plunger body, G50 snaps, G50 side vents split at the fan mid-plane | not implemented | — | GM4/GM5, GM7, GM9 |
| P-3: regression mis-scored `fail` | `verdict_flags` ignores a boolean `meets`. The orchestrator's verdict form differs from RUN.md 5. | Run tooling | — (C0) |

**Benchmark data.** No contradiction and no impossible band was found in the judged designs. G04's bridge exception (20.0)
is already in its requirements and is consistent with the plug data (17.0 overmold + 0.8). G02's USB-B roof is feasible
inside its 1.5 oversize: 16.0 + 0.8 = 16.8, roof rise (16.8 − 14.9)/2 = 0.95, top excess 0.4 + 0.95 = 1.35 ≤ 1.5. No
benchmark file was changed. One controller observation, not a defect: G02 mapped `headroom` to "within 0.1 mm" (L1.3). It
is harmless, because `keepout_above` 12 dominates.

## 3. Clustering and choice

What each candidate change would move, counted on the judged packages:

| Candidate | Designs touched (rows) | Verdicts moved alone | Verdicts moved together |
|---|---|---|---|
| C1 boss layout as a plant-scored choice | G04 (w1), G02 and G13 (needed by the rebate) | **G04 → MEETS** | — |
| C2 rebate closure | G02 (w3), G13 (w2) | none | **G02 → MEETS** (needs C1, C3 and C4) |
| C3 vent slot rows | G02 (gate), G11 (gate), G50 (partly) | none (G02 WRONG → DNM) | |
| C4 bridge sensor + 45° roof | G02 (w2); every shell with a wide opening | none | |
| GM2b secondary placement | G06 G08 G11 G13 G50 (all gates), plus 17 contents stops | **none**: every one of these also needs an aperture or body that does not exist yet (fan opening, window, plunger holes and body, cradle and door), and the 17 stops then stop at choose_archetype | — |

**Chosen: delta 003 = "the shell closes and breathes as the text says"** (C1 to C4, plus the tooling fix C0). It is the
only cluster that moves verdicts this iteration: train **MEETS 0 → 2** (G02, G04) and **CORRECT 1 → 2**. Each piece is
a capability that two or more train designs need, and each is triggered by part data, plant error or a generic evidence
word, never by a design:
- the boss layout choice: G02, G04, G13, and every future size-limited shell;
- the rebate closure: G02, G13;
- vents: G02, G11, G14 (sound holes later), G50 (side vents after the fan), and the `vent_pattern` tag on 4 train designs;
- the bridge sensor: every printed body with an opening.

GM2b stays the next structural step (section 7). It is the biggest gap by count, but alone it moves no verdict.

**Priority inside the delta**, in case the implementer must split it: C0 → C1 → C4 → C2 → C3. C0 + C1 + C4 alone already
give G04 MEETS with no regression risk. C2 and C3 bring G02.

## 4. Delta 003

### C0 (P-3, Run tooling, not agent code): accept the boolean verdict form

- `run_suite.verdict_flags`: `meets = verdict == "MEETS" or v.get("meets") is True`. `cache_verdicts.parse_verdicts`
  accepts a verdict object with `meets` (bool) and/or `class`, and stores a normalised `verdict` string next to it.
- RUN.md section 5 says that both forms are accepted, and that the stored form is normalised.

### C1 (D-BOSS-OUT; prerequisite of C2): closure bosses as an enumerated, plant-scored derivation choice

- **Layouts** (Python enumerates; generic):
  - `outside_corners`: today's diagonal pilasters, byte-identical, and always first.
  - `inside_band_x`, `inside_band_y`: the cavity grows along one axis by a **boss band** at each end (band width =
    boss `d` + `spec.board_clearance` + `rules.design_margin`). The four bosses stand inside the walls in those bands, fused
    to the floor and to the end wall. Their tops are at `base.split`.
- **Placement in a band** (a 1-D interval solve, no LLM): each boss starts at its band corner. The forbidden intervals
  along the band are the projections of every plug sweep, port cut (+ `rules.min_ligament`), keep-out column and reference
  bbox (+ clearance) that enters the band. The boss slides to the nearest free position towards the band's middle. If no
  free position exists, the layout is infeasible and is dropped, with a note.
- **Choice** (enclosure 7.11 pattern, at derive level): DeriveFeatures derives `outside_corners`. When it is feasible and
  no controllable check that the boss layout affects fails (`bbox`, `clear_*` that name a boss), it is kept. Nothing else
  is evaluated, so E1-01–V3 stay byte-identical. Otherwise each feasible layout is derived on a scratch state (manifold
  solids, `build_plan`, `run_plan`, as `prescore` does), and the strictly smallest controllable error wins. A tie keeps
  enumeration order. The choice is recorded as `choices.boss_layout` with `by: prescore:derive` and the per-layout error
  keys in design.json. If the closure makes `outside_corners` infeasible (C2), the scored set starts at the inside layouts.
- **Lid side of an inside layout:** no pads (the plate already covers the bosses). Clearance holes go through the plate.
  The lip is notched at each boss, as today.
- **Sensor (review N5 of delta 002):** `pilot_depth_boss_<k>` checks that the pilot depth is at most boss height + floor −
  `rules.min_feature`, the same as `pilot_depth_standoff_*`. Inside bosses and C2 make boss pilots relative to new planes,
  so this is the right time to add it.

### C2 (D-LID-FORM): the rebate closure, evidence-gated

- **Vocabulary** (design_rules.json, new block `closures`):
  `{"lip": {"default": true, ...}, "rebate": {"evidence": ["rebate", "rebated"], "source": ...}}`. A closure other than
  the default is chosen only when one sentence of the request or an L1 has its evidence word (text_evidence token runs)
  and a lid word (the `tray_lid` evidence words that name the lid). No controller question is needed: the word is
  unambiguous, and the form is a rule.
- **Geometry** (generic expressions):
  - The base walls rise by the plate thickness `lid.z` above `base.split`.
  - A rebate cut `x = base.x − 2·rules.rebate_upstand`, `y` likewise, height `lid.z + cut_overrun` from `base.split`,
    leaves an upstand `rules.rebate_upstand` thick.
  - The lid is a plate `x = base.x − 2·(rules.rebate_upstand + rules.sliding_fit)` (y likewise), `z = lid.z`, at
    `base.split`. It has no lip and no pads, and its top is flush with the upstand top.
  - The bosses (inside layouts only) end at `base.split`, the rebate floor.
  - New rule `rebate_upstand` = 1.5 mm (source: 4 perimeters at 0.4, the same printed-ligament basis as `min_ligament`;
    G02 asks ≥ 1.0).
- **Sensors:** `lid_fit` (per-side gap between plate and upstand inside the sliding-fit band), `rebate_upstand`
  (≥ the rule), `lid_flush` (plate top vs upstand top ≤ `rules.design_margin`), `boss_top_plane` (boss tops on the rebate
  floor ≤ `rules.seat_gap_max`). The existing `separable`, `ligament` (port tops to the rebate floor through the split
  terms) and `bbox` checks apply unchanged.
- `print_orientation` is unchanged: the base prints open side up (the rebate is a vertical step), and the lid prints flat.

### C3 (D-VENT): vent slot rows through a lid or a wall

- **Evidence** (design_rules.json `vents`): `["vent", "vents", "ventilation", "vent slots", "exhaust slots",
  "exhaust slot", "louvre", "louvres", "louver", "louvers"]`. Bare "exhaust" (a fan's exhaust side) and bare "slot" (a
  microSD slot) are not evidence. A vent sentence is a sentence that contains one of these words.
- **Where the row goes** (in order; the first that resolves wins):
  1. **A named zone:** a content part's new `zone` interface whose `names` appear in a vent sentence. The row lies in the
     lid plate, over the zone: centred on the zone's centre line, running along its long axis, with every slot outline
     inside the zone's long extent.
  2. **A wall related to an exposed item:** a vent sentence that names a relation word (`face_relations`: opposite /
     same). The controller reads the relation as in C0 of delta 002. One voted enum question per run, label
     `assy_vent_relation`, quotes the vent sentences. Its options are {(exposed member, relation)} ∪ {not_stated}, and only
     a unanimous reading counts. The vent wall is that member's wall, or the wall opposite it, after the arrangement is
     fixed.
  3. **Otherwise:** the typed note `vent: face not resolved (face words only)` and an uncontrollable failing `vent_placed`
     check (it carries `conflict`, so prescore ignores it). No geometry is guessed. This is G50 today.
- **Sizes from the text** (one voted mapping question, label `assy_vent_spec`, asked only after the face resolves):
  - The question offers only the numbers in the vent sentences that no spec slot owns. The cross-stage owner question of
    delta 001 C3 applies.
  - Its generated slots are `vent_count_min/max`, `vent_width_min/max`, `vent_length_min/max`, `vent_pitch_min/max` and
    `vent_area_min`, each with a meaning and a unit, and each may be `none`.
  - Violations get one re-ask: lo > hi, and a count that is not a whole number.
  - Rules defaults (new, each with a source) fill the silent ends and are flagged as assumptions: `vent_slot_width` 2.0
    (5 extrusion lines) and `vent_slot_length` 10.0.
- **Python solve** (no LLM; setpoints inside the bands):
  - width w = middle of the width band;
  - length l = middle of the length band when both ends are stated, else the available extent across the row
    (zone: the stated band; wall: wall height between the floor top and `base.split` minus 2·`min_ligament`), clamped to
    the stated end;
  - pitch p = middle of the pitch band, or w + max(`min_ligament`, w) when none is stated, and never below
    w + `min_ligament`;
  - count N = the largest count in the band that fits (N − 1)·p + w ≤ the row extent (zone: its long extent; wall: the
    inner span minus 2·`min_ligament`, minus the band of any boss or port cut + ligament on that wall). While
    N·w·l < `vent_area_min`, N grows (p down to its floor), then w, then l, within their bands.
  - Infeasible → `vent_area` fails with a typed `conflict` naming the binding band.
  - Worked: G02 → w 2.25, l 10, p 5.0, N 7, area 157.5, span 30.0. G11 → w 3, l ≈ wall height − 3, N ≥ 10, area ≥ 567.
- **Nodes:** one `cut` box per slot, role `vent_cut`, with `wall` set for wall rows. Body `lid` or `base`. Source
  `rule:vent_row(<zone or wall>)`. `vent_cut` joins `APERTURE_CUT_ROLES`, so `ligament_*` covers each slot (neighbours,
  lid holes, edges), and wall slots join that wall's expected `aperture_count`.
- **Sensors** (each linked to its L1 through slot provenance, so L1.7 is no longer UNLINKED): `vent_count`, `vent_width`,
  `vent_length`, `vent_pitch` (bands, stated ends only), `vent_area` (≥), `vent_zone_<zone>` (every slot outline inside the
  zone's long extent, the row centred across within `design_margin`), and `ligament_<slot>_<body>`.
- **Data D1** (catalogue): `parts.py` accepts a new interface kind `zone`:
  `{"id", "kind": "zone", "at": <point datum>, "size": [<long expr>, <short expr>], "long_axis": [x, y, z], "names":
  [...]}`. The R-gate checks that the datum exists, that the size exprs resolve > 0, and that the names are non-empty
  and are not archetype evidence words.
  - `arduino_uno_r3` gets `{"id": "mcu", "kind": "zone", "at": "MCU", "size": ["mcu_length", "mcu_width"],
    "long_axis": [1, 0, 0], "names": ["atmega328p", "atmega328", "atmega", "microcontroller", "mcu"]}`.
  - New params `mcu_length` 35.6 and `mcu_width` 7.6 (DIP-28 300 mil body outline, Microchip ATmega328P datasheet
    package drawing; uncertainty ±2 mm in position, as in G02 A4).

### C4 (D-BRIDGE): bridge sensor first, then the 45° roof

- **Sensor:** `bridge_<cut>` for every box opening in a vertical wall (port cuts and C3 wall slots). Its value is the flat
  roof span: the opening's top width along the wall. The limit is `rules.bridge_max`. Round openings up to
  `rules.round_hole_exempt_max` are exempt, as the rubric exempts them.
- **Derivation term:** when the opening width `w_o > rules.bridge_max − rules.design_margin`, a 45° roof is added. It is a
  trapezoid prism on the opening top: bottom width `w_o`, top width `b = rules.bridge_max − rules.design_margin`, rise
  `(w_o − b)/2`.
  - This happens only if the roofed opening still keeps its top oversize ≤ `spec.opening_oversize_max −
    rules.design_margin`.
  - Otherwise the roof stays flat, and `bridge_<cut>` fails with a typed `conflict` ("stated oversize vs bridge limit").
    That makes it uncontrollable, so it is reported and never steers prescore. This is G04's HDMI case: 17.8 wide, roof
    rise 1.45, excess 1.85 > 1.5. G04's requirements accept 20 there, so G04's geometry does not change.
  - The cut's `top` includes the rise, so the split ligament term and `below_split_*` hold. `oversize_*` measures the
    roofed region.
- **Primitive:** `feature_graph` gains `prism`, a convex polygon in a local plane extruded along the local normal. It has
  a SCAD emitter (`linear_extrude(polygon)`) and a manifold3d emitter (`CrossSection(...).extrude`), and the
  volume/bbox parity check covers it. It is generic: GM5's gussets, chamfers and teardrop holes reuse it.

## 5. Tests (each fails on `de77b7ab88b1`, passes after, unless marked guard)

| # | Test (capability-keyed) | What it asserts |
|---|---|---|
| T1 | `test_generalize_suite.TestVerdicts.test_boolean_meets_form` | `verdict_flags({"meets": true, "class": "CORRECT"})` gives meets; iteration 003's original `verdicts.json` form gives regression `pass` |
| T2 | `test_assembly.TestBossLayout.test_size_limit_moves_bosses_inside` | Replay of iteration 003's recorded G04_s3 answers: `bbox` passes, `choices.boss_layout` is an inside band, every boss is ≥ `board_clearance` from the board and connectors, `clear_*` all pass. Before: `bbox` −2.21 |
| T3 | `TestBossLayout.test_band_slides_past_plug_sweeps` | A synthetic primary with a connector at a band corner: the boss slides to the nearest free interval, and its plug sweep clearance passes |
| T4 | `TestBossLayout.test_default_kept_when_passing` (guard) | E1-01, V1, V2, V3 recorded answers: `outside_corners`, no scratch derivations, geometry (poses, base and lid volumes) equal to iteration 003 within 1e-6 |
| T5 | `TestBossLayout.test_boss_pilot_floor_sensor` | `pilot_depth_boss_*` exists, passes on the regression set, and fails on a mutant with the floor raised |
| T6 | `test_assembly.TestRebate.test_rebate_closure_from_text` | G02's text, scripted answers: lid has no lip; plate fit 0.25 per side; upstand 1.5; plate top flush; boss tops on the rebate floor; inside layout; all new checks pass. Before: a `lid_lip` node exists |
| T7 | `TestRebate.test_no_evidence_keeps_lip` (guard) | Texts without "rebate" (the four regression texts, G04, G11) keep `lid_lip` |
| T8 | `test_assembly.TestVents.test_zone_row_in_lid` | G02's text, scripted `assy_vent_spec`: 7 slots 2.25 × 10, pitch 5.0, inside the Uno `mcu` zone's long extent, centred across within `design_margin`; area ≥ 100; vent checks pass and link to L1.7. Before: no `vent_cut` |
| T9 | `TestVents.test_wall_row_opposite_exposed_item` | G11's text, scripted relation `opposite`: slots on the wall opposite the jack's wall, area ≥ 567, that wall's `aperture_count` includes them, ligaments pass |
| T10 | `TestVents.test_unresolved_face_is_typed` | G50's text: a note, `vent_placed` failing with `conflict`, no `vent_cut`, no `assy_vent_spec` asked |
| T11 | `TestVents.test_prompts_unchanged_without_vent_words` (guard) | The four regression texts: the question labels and prompts equal iteration 003's |
| T12 | `test_assembly.TestBridge.test_wide_opening_gets_roof` / `test_roof_yields_to_oversize` | A USB-B opening (16.8) gets a roof with top width ≤ 14.9, and `bridge_*` and `oversize_*` pass. A mini-HDMI opening (17.8) under oversize 1.5 stays flat, and `bridge_*` fails with `conflict` |
| T13 | `test_feature_graph.TestPrism.test_prism_parity` | Prism SCAD and manifold volume and bbox agree within the parity rules |
| T14 | `test_parts.TestInterfaces.test_zone_kind` | The `zone` interface gate: a good one loads, a missing datum or empty names is rejected; the Uno `mcu` zone resolves 35.6 × 7.6 |
| T15 | `test_no_hardcoding` (guard) | Green: every new word lives in design_rules.json, every number in rules or part.json |

The full RUN.md 2 suite must stay green. Tests that change because the behaviour changes on purpose must be marked
"changed in generalize delta 003". The ones expected are any test that counts check ids, which now include `bridge_*` and
`pilot_depth_boss_*`.

## 6. Expected effect (next Run, SEED 4)

| Design | Iteration 003 | Expected | Why / risk |
|---|---|---|---|
| E1-01, V1, V2, V3 | MEETS ×4 | MEETS ×4, same geometry hash (cache hits) | no evidence words, openings ≤ 10.8 wide, default boss layout passes (T4, T7, T11). New check ids only |
| **G04** | CORRECT 0.99 | **MEETS** | C1: inside X bands, outside about 85 × 37 × 19 (feasibility 85.8 × 36.6). Risk low to medium: the SD sweep at −X must leave a free band position (T3) |
| **G02** | WRONG 0.84 | **MEETS** | C3 vents (gate G5 + 6 rows), C2 rebate (3 rows), C1 inside bands (about 95 × 61, limit 100 × 70), C4 roof (1 row). Risk medium: the 9B must map 9 vent numbers. A slot it misses falls to a rules default, and a stated band end that is lost can push a row out of its band |
| G11 | WRONG 0.35 | WRONG, about 0.45 | gate G5 passes (exhaust slots opposite the jack). G4 (fan) stays |
| G13 | WRONG 0.30 | WRONG, about 0.33 | rebate row passes; buttons and plungers stay. Z bbox stays (stacked Pico) |
| G06, G08, G50 | WRONG | WRONG, unchanged | G50 gets the typed vent note only |
| 33 no-output | — | unchanged | not touched by this delta |

Train forecast: **MEETS 2 / CORRECT 2 / no-output 33.** Each changed package must be judged. The regression packages
should be cache hits.

## 7. Deferred, and why

1. **GM2b secondary placement** (G06 G08 G11 G13 G50, plus 17 contents stops). It is the biggest structural gap, but it
   moves no verdict alone. Each judged design also needs an aperture or body that does not exist. **Next delta's first
   candidate**, together with the lid apertures for its items:
   - any-kind Contents with quantities (fans, buttons, switches, cells, named fasteners);
   - placement on a carrier for board-mounted parts (G13 buttons, G11 heatsink);
   - an `against` relation for a part on the lid (G11 fan);
   - the GM4 actuator, airflow and view apertures through the lid (plunger holes, fan opening, window).
2. **Closure screw count and position from the text** (G06, G08 w2). Moves no verdict. It belongs with GM2b's "a named
   fastener with a quantity is content". Diagonal corners would be the derived default for two screws.
3. **Lid plate thickness band** (G11 w3). G11 stays WRONG without the fan. It lands with the fan-on-lid pilots, which are
   the reason for the band.
4. **Side-wall vents split at a fan mid-plane** (G50). Needs the fan placed (GM2b). G14's sound-hole ring is a hole-ring
   variant of C3 (GM4) and waits for G14's locating pins (GM3).
5. **Snaps (G01 G03 G50), hinge (G09), door and third bodies (G08, G13 plungers), tilt and window (G06).** GM9, GM7, GM4
   and GM5 in the plan's order.
6. **Delta 002 review N1, N2, N3, N4, N6, N7.** No iteration 003 defect traces to them. N5 is taken into C1.
7. **`../rubric.md` (P-1)** is still missing. The judges keep using the enclosure rubric plus each requirements.md. It
   must exist before the first held-out measurement.
