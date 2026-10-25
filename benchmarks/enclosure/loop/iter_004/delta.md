# Iteration 004: gap analysis and delta design

Author: gap analyst / delta designer, iteration 004. I did not edit any code.
Tooling: the claude-context MCP server failed to connect in this session ("configured MCP servers failed to
connect: claude-context"). This analysis used reads of known paths and targeted grep only.

## 1. What the error signal says

| Run | rc | Status | Minutes | Package |
|---|---|---|---|---|
| E1-01 `target_s0` (assembly, seed 0) | 0 (inferred) | verified, 25/25 of the agent's own checks | 1.3 | `iter_004/target_s0/20261024-091709/` |

This is the first judgeable assembly package. The 9B controller answered every question correctly: spec
after one re-ask, contents, stack, edges, and arrangement by vote plus rank. Both judges measured the same
geometry: 82.25 x 60.95 x 24.40 mm, walls 2.40, all plugs seat, openings counted correctly, standoffs on
the 65 x 45 pattern. Self-report agreement was within 0.10.

| Defect | L3 (weight) | Judge 1 | Judge 2 | Whose problem |
|---|---|---|---|---|
| D1 | L3.3.5.1 (2): base walls cut 0.50 mm into the Ø7 screw-head columns at all 4 holes, 87.66 mm³ in total | FAIL | FAIL | **agent** |
| D2 | L3.1.6.1 (1): Pico pins are 1.13 mm off the grid in X; jack pins are not modelled | FAIL | FAIL | **requirements conflict** with L3.1.3.1 under the catalogue's hole-1 grid assumption, plus a data gap (jack pins) |
| D3 | L3.12.1.1 (3, gate G0): lid bbox Z is 4.40, under "20–200 per axis" | FAIL (literal) | PASS (read as a units check) | **requirements** (not in the agent's inputs; a flat lid can never meet it) |
| O1 | (observation, both judges) many passes at exactly zero margin: board 0.500, USB plug 0.300, KO-top/bottom 0.000, driver columns 0.000. The jack plug measured d = 0.2948 (64-gon), which gives the worst w3 margin −0.010 | — | — | agent robustness / sensor honesty |

The agent's self-verdict was **verified** while both judges said DOES NOT MEET. That disagreement is the
main finding. Every defect above is a requirement that Python **did not sense**. It is not a controller
mistake: the LLM's choices were all correct.

## 2. Root causes (in the agent)

### RC-401 (D1, and the zero-margin driver columns in O1): keep-out envelopes are built but never used

`BuildEnvelopes` (`assembly.py:782`) creates `hole_ko_0..3` (Ø = board screw head + 2 x driver_clearance,
board TOP to TOP + keepout_above). Two places should use them, and neither does:

1. **Derivation.** `derive_cavity` (`assembly.py:853`) bounds the cavity in plan by the AABB of the
   references plus `spec.board_clearance` only. ARCHITECTURE.md section 4 says
   `CavityFromContents: cavity = hull(references ∪ keepouts) + clearances`, so the code dropped the
   keepouts. A corner hole sits 2.5 mm in from the board edge (from part data). Its Ø7 column therefore
   reaches 1.0 mm beyond the board edge, but the wall sits only 0.5 mm beyond it. On the -X end the USB
   overhang happens to push the wall out far enough (1.8 mm gap). The other three walls miss by 0.5 mm.
2. **Sensing.** `build_plan` (`assembly.py:1116`) only measures volumes whose role is `keepout_top`,
   `keepout_bottom`, `module_envelope`, the plug sweeps and the board. `hole_keepout` has no `clear_of`
   consumer, so the agent could not see the intrusion. The same is true of V-DRIVER: the rule
   `driver_diameter` exists, but no column is built from it and nothing checks it. The judges found the
   walls exactly tangent to the Ø6 driver columns.

The class of bug is a "dead envelope": a generated volume that neither bounds a derivation nor feeds a check.
No test catches that class today.

### RC-402 (O1): clearance targets equal their limits

Every one-sided clearance is derived at exactly its limit: `spec.board_clearance`, `rules.plug_to_opening`,
`cavity.z1 = TOP + keepout_above`, `cavity.z0 = BOTTOM - keepout_below`. The judge passes a value within
ε = 0.02, so these pass today. But any tessellation or rounding change flips them, and three seeds are
needed for convergence. A controller designs to a setpoint inside the band, not on its edge. The design has
no generic setpoint offset.

### RC-403 (O1, worst w3 margin): round cuts and envelopes are inscribed polygons

`feature_graph._cyl` / `_scad_cyl` (`feature_graph.py:737`, `:866`) emit a `$fn`-gon whose *vertices* lie
on d/2. The jack cut Ø8.6 therefore has an inscribed radius of 4.2948, so the true clearance to the Ø8
plug is 0.2948. The agent's own sensor also polygonises the plug envelope. Both shrink, so the agent
reported 0.2996 against the judge's 0.2948. This is a sensor that errs in the design's favour.
A hole must be at least nominal, and an envelope must be at least as large as what it bounds. Both must be
circumscribed: vertex radius = (d/2)/cos(π/fn).

### RC-404 (D2): grid conformance is not a check, and the jack has no pin data

- `Placer.grid_residual` (`layout.py:316`) is computed and written to `layout.json` (1.13), but it never
  becomes a `CheckResult`. The package says "verified" with a known 1.13 mm residual.
- Only parts with `mount.stack_pins` (modules) are snapped and measured. `jack_3p5_pj320a/part.json` has
  no pin datum ("footprint pins are not modelled yet"), so the judges can only mark its half UNVERIFIED.
- Snapping the Pico normal to the edge cannot help. The tangential-only rule (ARCHITECTURE.md 7.5) chose
  the flush port (L2.1.3, weight 2) over grid conformance (weight 1). Both judges confirm that with a
  hole-1 grid the two cannot hold together: the best residual inside L3.1.3.1's band is 0.63. The rule is
  therefore right and is **kept**, which avoids oscillation. What is missing is that the agent reports the
  failure, with the conflict as its reason, instead of hiding it.

### D3 is not an agent defect

The agent receives only the request and the L1 text (`iter_004/inputs/E1-01.l1.json`). L1.12 lists the
files but states no bounding-box band. The "20–200 mm per axis" band exists only in requirements.md
L3.12.1.1, which the agent never sees. No change to the agent's sensing or derivation can make that rule
visible to it without hard-coding a judge-side number. That is forbidden, so this goes to Robin (section 5).
If Robin keeps the rule, the agent change is a new archetype (a deep cap lid, so the split plane moves
down, the port cuts belong to the lid, and the lid is about 20 mm tall). That is ARCHITECTURE.md 4.3 work
for a later iteration, and only if Robin confirms the rule.

## 3. Delta (implement in this order; C1 to C4 are required, C5 is time-boxed)

All new numbers go in `design_rules.json` (generic, with a source) or in part.json. No literal goes in the
code. `test_no_hardcoding` must stay green.

### C1: keep-out envelopes bound the cavity and are checked (RC-401, closes D1)

**`parts.column`** (`parts.py:648`): add an optional `anchor` (a datum ref string such as
`"board.HOLE[2]"`). With an anchor, the node is posed `Pose(at=anchor, offset=(0, 0, z_from - <datum z>))`,
not at frozen floats. The column then follows the board when the board's params change (ARCHITECTURE.md
3.3: envelopes come from datums only). If no anchor is given, the current behaviour is unchanged.

**`BuildEnvelopes`** (`assembly.py:782`):
- Pass `anchor=f"board.HOLE[{i}]"` for the `seat_*` and `hole_ko_*` columns.
- Add **V-DRIVER** columns: `driver_<i>` with role `driver`, Ø `rules.driver_diameter`, from board TOP up
  to `base.split + rules.driver_reach`. The height is an expression, so this node depends on `base`. Do not
  let the cavity reference the driver nodes, or the dependencies form a cycle (see below).
- New rule `driver_reach` = 50 mm in design_rules.json: the length of driver shaft that must clear above
  the base rim with the lid off. Source: "screwdriver shaft length above the rim, requirements.md V-DRIVER". Hand
  review. It is a generic tool length, not a box number.

**New module constant `KEEP_OUTS`** in `assembly.py`: one table that says, for each envelope role, how it
is consumed. This is the single place that defines "what an envelope means":

| role | bounds cavity in plan | bounds cavity in Z | check | bodies | minus |
|---|---|---|---|---|---|
| `keepout_top` | no | yes (z1) | `clear_of`, clearance 0 | all | — |
| `keepout_bottom` | no | yes (z0) | `clear_of`, clearance 0 | all | `seats` |
| `hole_keepout` | **yes** | no | `clear_of`, clearance 0 | all | — |
| `driver` | **yes** (by the plan radius `max(hole_ko.d, rules.driver_diameter)/2` on the same HOLE axis, never by referencing the driver node) | no | `clear_of`, clearance 0 | **base only** (lid off) | — |
| `module_envelope` | via its parts' bboxes (as today) | no | `clear_of`, `rules.part_to_wall` | all | — |
| `seat` | no | no | used as `minus` only | — | — |
| plug sweeps (`*_plug_*`) | no | no | `clear_of`, `rules.plug_to_opening` | all | — |
| `cavity` | (is the cavity) | | | | |

**`derive_cavity`** (`assembly.py:853`): each plan bound becomes
`min/max(<reference term as today> ∓ spec.board_clearance ∓ rules.design_margin,
board.HOLE[i].x ∓ R_i ∓ rules.design_margin for every hole i)`. Here
`R_i = max(hole_ko_i.d, rules.driver_diameter)/2`, and the Y bounds are built the same way. The reference
terms keep `spec.board_clearance`, because that is the board-to-wall requirement. The keep-out terms take
no clearance, because their limit is d ≥ 0. Build the terms by iterating the envelope nodes whose
`KEEP_OUTS` row says "bounds cavity in plan". Never special-case a side or a hole index.

On E1-01 (design_margin 0.1) this gives a cavity of X −1.9 to 71.1 and Y −1.1 to 51.1, against
−1.8..70.5 and −0.5..50.5 today. The judges required Y ≤ −1.0, Y ≥ 51.0 and X ≥ 71.0. The corner pilaster
rule (7.4) is unchanged, so the bosses move out with the cavity corners.

**`run_plan` / `clear_of` dispatch** (`assembly_checks.py:275`): honour an optional `bodies` arg, a list of
body names (default all). The driver check needs it.

**`build_plan`** (`assembly.py:1116`): build the `clear_of` checks from `KEEP_OUTS`, one per envelope
node (`clear_hole_ko_k`, `clear_driver_k`), not from the hand list of roles it uses today. Keep the
existing check ids so `checks.json` stays comparable.

**Tests (fake LLMs only):**
- `test_assembly.TestDeriveFeatures.test_cavity_clears_the_hole_keepout_columns`. Derive E1-01 with the
  scripted controller. For every hole k and every wall, compute the distance from the hole axis to the
  wall's inner face from `res.params["cavity"]` and the HOLE datum. Assert that each distance is at least
  `hole_ko.d/2 + design_margin − 1e-9`. Repeat for V1 (80 x 60), so the rule is shown to be generic.
- `test_assembly.TestDeriveFeatures.test_no_dead_envelopes`. After `BuildEnvelopes` and `build_plan` on
  E1-01 and V1, every envelope node's role must appear in `KEEP_OUTS`. Every envelope must also either
  bound the cavity, feed at least one plan check (as `volume` or `minus`), or be a plug sweep consumed by
  its port cut. This is the regression test for the class of bug.
- `test_assembly.TestDeriveFeatures.test_hole_keepout_check_is_not_vacuous` (sensor non-vacuity). Build
  the package once with the hole terms removed from the cavity (monkeypatch `KEEP_OUTS["hole_keepout"]`
  so it does not bound the cavity, which is the iteration 004 behaviour). Assert that `clear_hole_ko_*`
  fails with penetration > 0 and a typed evidence bbox. With the real table, assert that it passes with
  margin ≥ design_margin − measure_tol.
- `test_assembly.TestDeriveFeatures.test_sizes_are_derived_not_filled_in` is unchanged and must still pass.
  Board width +5 moves base.x by exactly 5, because the columns are now datum-anchored.
- `test_assembly_checks`: `clear_of` with `bodies=["base"]` ignores an intruding lid and catches an
  intruding base.
- `test_parts.TestEnvelopes`: an anchored column re-resolves to the moved hole when the board width
  changes. An unanchored column keeps its old floats, so the existing behaviour is pinned.
- `TestReplayIter004.test_replay_iter004_answers_end_to_end`, a new replay test (rule 7.6). Script the
  recorded answers from `iter_004/target_s0/20261024-091709/llm/001-021`. Expect rc 0, verified,
  `clear_hole_ko_0..3` and `clear_driver_0..3` all passing, and an independent rubric-3.2 re-measurement
  (`rubric_clear_of`, which is not `assembly_checks`) of base ∪ lid against Ø(hole_ko.d) columns giving
  penetration ≤ 0.01 mm³.

**Expected judge effect:** L3.3.5.1 PASS (L1.3 PASS) and L3.11.2.1 driver d about 0.6 instead of 0. The
size grows to about 82.95 x 62.15 x 24.6, still inside 90 x 70 x 35.

### C2: a generic design margin on every one-sided clearance (RC-402)

- New rule `design_margin` = 0.1 mm. Source: "setpoint offset inside one-sided clearance limits: 5 x the
  judge's 0.02 mm measurement ε, so tessellation and rounding never flip a pass." The checks keep their
  limits (spec/rules values). Only the derivation targets move.
- Apply it in the derivation only:
  - cavity plan bounds (C1);
  - `cavity.z1 = max(board.TOP.z + spec.keepout_above + rules.design_margin, tallest + spec.headroom + rules.design_margin)`;
  - `cavity.z0 = board.BOTTOM.z - spec.keepout_below - rules.design_margin`;
  - port-cut cross-sections `cw + 2*(rules.plug_to_opening + rules.design_margin)` in `derive_port_cut`
    (`assembly.py:882`).
- Leave alone the "≥ minimum" sizes the judges measured at their nominal values (pilot depth, lip
  engagement, boss OD). They are exact in both OpenSCAD and the mesh, so tessellation cannot flip them.
- Opening oversize becomes 0.4 per side, still ≤ `spec.opening_oversize_max` (1.5). The existing
  `aperture_oversize` check guards this.
- **Tests:** `TestDeriveFeatures.test_clearances_have_the_design_margin`. Every rule-derived `clear_of` /
  `inside` result on the E1-01 and V1 packages has raw gap ≥ limit + design_margin − measure_tol. A rules
  file with `design_margin = 0` reproduces today's zero-margin gaps (within 1e-6), which proves the rule is
  the only cause. Every `TestEndToEnd` test must keep passing unchanged. If an exact-size assertion breaks,
  change it to the new expression with a ledger line ("behaviour intentionally changed: design margin").

### C3: circumscribed polygons for holes and envelopes (RC-403)

- `feature_graph._local_solid` / `_scad_local` (and the `tube` inner bore): a cylinder belonging to a node
  of kind `cut` or `envelope` uses diameter `d / cos(π/seg)`, the same number in manifold and in SCAD, so
  parity holds. `add`/`body` cylinders keep d (inscribed), so the outside never grows. Use one helper,
  `_poly_d(node, d, seg)`. Write π as `math.pi` (no literal).
- **Tests:** `test_feature_graph`: the inscribed radius of a cut cylinder at `fn = 24` and at 64 is
  d/2 within 1e-9, measured as the min distance from the axis to the hole's mesh vertices. An add cylinder
  keeps its vertices on d/2. OpenSCAD parity still passes on a shell with a round port cut. In
  `TestEndToEnd`, the self-report jack-plug gap equals the independent rubric re-measurement against an
  exact (high-`fn`) Ø8 envelope within 0.02. Today they differ by 0.005 in the design's favour.
- **Expected judge effect:** jack d = 0.40 (0.3 + design_margin, exact), so the worst w3 margin is
  positive.

### C4: grid conformance is sensed and reported, with the conflict as its reason (RC-404, D2)

This changes no placement: the 7.5 tangential-only snap and the 7.6 soft grid are kept.
- **Data:** a part may declare a `PINS` datum (axis_list). Add one to `jack_3p5_pj320a/part.json`
  **only** from a footprint drawing the implementer can actually read and cite (for example the LCSC
  C18438 drawing named in its source), with a self_check that the pins lie inside the body footprint.
  If no such drawing can be read, do not invent the pins. Leave the note, and C4 reports the jack as
  "no pin data".
- **`layout.Placer`:**
  - `grid_shift` / `grid_residual` read the pins of any placed part, `mount.stack_pins` or a `PINS`
    datum. Connectors with pins are then snapped tangentially too, inside the existing collision and
    spacing guards.
  - New `grid_report(placed)` returns, per part: the max residual, its tangential and normal components,
    and, for an edge-placed part, `normal_fix`, the normal shift that would zero it. Each part with a
    connector but no pin data is listed as `no_pin_data`.
- **`build_plan`:** a new design-level check `grid_conformance`. It uses `value_at_most` with value = the
  max residual and limit = new rule `grid_residual_max` (0.15 mm). Source: "a 0.64 mm square pin in a
  ~1.0 mm plated hole: lateral slack, requirements.md A7"; hand review. Its evidence gives each part's
  residual, `no_pin_data` parts (these count as failing, as the rubric counts UNVERIFIED), and, when the
  residual is normal to an edge, `conflict: "fixing it moves <part>.<connector mouth> off its flush edge
  position by <normal_fix> mm (rule flush_to_edge, ARCHITECTURE.md 7.5)"`. If the board's grid is
  `soft`, the check carries `soft: true`.
- **`finalize`** (`assembly.py:1336`): the outcome stays `verified` only when every check passes. A failing
  check whose evidence carries a `conflict` is also listed under `design.json.assembly.conflicts`, with
  the check id, the competing rule and the numbers, so Robin and the judge see a typed requirement
  conflict, not a silent pass. This is the first concrete instance of the "requirement" route in
  ARCHITECTURE.md 4.4. The exit code for unsatisfied (3) is unchanged. RUN.md 3.4 already treats a
  package with rc 3 as judgeable. Update RUN.md section 4's "Expected now" to say that E1-01 is
  expected to end `unsatisfied` with one conflict (grid) until Robin decides.
- **Tests:**
  - `TestArrange.test_grid_report_names_the_normal_conflict`: on E1-01 the Pico residual is normal to −X
    and equals 1.13 within 0.01, computed from part data in the test, not typed in. `normal_fix` is
    reported. With the jack pins absent, `no_pin_data` lists the jacks.
  - `TestEndToEnd.test_grid_conflict_is_reported_not_hidden`: E1-01 ends `unsatisfied` with exactly
    `grid_conformance` failing and one entry in `assembly.conflicts`. V1 is the same, or verified if its
    layout happens to land on grid. Assert whichever the part data implies, computed in the test.
  - `test_parts`: a fixture part with a `PINS` datum is snapped tangentially by the placer, and the
    residual drops to ≤ 1e-6 along the edge.
  - **Changed tests (ledger line each, "behaviour intentionally changed: grid conformance is now a
    check"):** any `TestEndToEnd` / `TestReplayIter003` assertion of `verified` / rc 0 for E1-01. Each
    must keep every other assertion and add `failed == ["grid_conformance"]`. Never drop the
    other-checks-pass assertions.
- **Expected judge effect:** none on L3.1.6.1 until Robin decides (section 5). The agent's self-verdict
  now agrees with the judges'. If the jack pins are added from a real drawing, the jack half becomes
  verifiable.

### C5 (time-boxed, after C1 to C4 are green): offline end-to-end for V2 and V3; run the variants next

Convergence also needs V1, V2 and V3 to be CORRECT. Only E1-01 and V1 have offline end-to-end tests today
(`TestEndToEnd`). Add `TestEndToEnd` cases for V2 (three jacks on a long side) and V3 (socket stack, the
request-sized capacitor, keepout_above 23, max_z 45) using their scripted controllers (`script_for`). Each
asserts a package plus aperture counts per wall from the layout: V2 −X 1 / +Y 3 (or the symmetric side),
V3 −X 1 / +X 1.
- If a variant fails offline on a generic gap that a fix of about 100 lines or less closes, fix it.
- Otherwise record it as `G-004-5` in the ledger for iteration 005. Do not add a skipped or
  expected-failure test.

**Run step for iteration 005:** E1-01 with SEED = 5 (the iteration number, RUN.md 1), plus `run_one V1;
run_one V2; run_one V3`. The E1-01 package is now judgeable, so the variants are the cheapest new error
signal.

### Explicitly not in this delta (and why)

- **M9 Solve / M11 Correct.** C1 fixes D1 by construction. A numeric correction loop is not what blocks
  the verdict now, and the sensors it needs are what C1 and C4 add.
- **M10 translation of L1s.** The verification matrix shows every L1 as "no check covers this
  requirement", which both judges noted. That is real but not graded. It stays next on the milestone list.
- **Deep-lid archetype for D3.** Only if Robin keeps the 20 mm rule (section 5).
- **Grid snap normal to the edge.** Rejected. It would trade a weight-2 pass for a weight-1 pass and
  reverse the 7.5 decision, which is oscillation. The conflict goes to Robin.

## 4. How the verdict should move (E1-01, next Run)

| L3 | iter 004 | expected after delta |
|---|---|---|
| L3.3.5.1 (w2) | FAIL (both) | PASS |
| L3.11.2.1 driver (w1) | PASS at d = 0 | PASS at about 0.6 |
| L3.5.1.1 / L3.6.1.1 / KO-top / KO-bottom / board clearance | PASS at zero margin | PASS with ≥ 0.1 margin; worst w3 margin positive |
| L3.1.6.1 (w1) | FAIL (both) | FAIL; the agent now reports it as a typed conflict (needs Robin) |
| L3.12.1.1 (w3, G0) | judge 1 FAIL / judge 2 PASS | unchanged (needs Robin) |

Judge 2: score 131/134 → 133/134, class CORRECT, worst w3 margin about +0.2. The verdict stays DOES NOT
MEET only because of the two requirement items. Once Robin rules on them, E1-01 can reach MEETS without
another agent change.

## 5. Questions for Robin (requirements, never relaxed by the loop)

1. **L3.12.1.1, "bounding boxes within 20–200 per axis".** A flat lid that meets L2.7.4 is about 4.4 mm
   tall, so the rule fails every flat-lid design. Should it read "the largest axis within 20–200" (a
   units sanity check), or do you want a deep cap lid at least 20 mm tall? The second needs a new
   archetype.
2. **L3.1.6.1 against L3.1.3.1.** With the perfboard grid registered to hole 1 (an assumption in
   `perfboard/part.json`, marked `soft`), no Pico position satisfies both. What is your board's real grid
   registration? Alternatively, should the USB mouth band follow the grid? The fix goes in part.json or
   requirements.md, not in agent code.
3. **PJ-320A footprint pins.** If you have the footprint you actually use, its pin positions belong in
   `jack_3p5_pj320a/part.json`.
4. **L3.11.1.1** (judge 2): as written, V-INSTALL always touches the standoff tops (d = 0). Exclude V-SEAT
   from V-INSTALL?
5. **New rule values to review by hand:** `design_margin` 0.1, `driver_reach`, `grid_residual_max` 0.15.
