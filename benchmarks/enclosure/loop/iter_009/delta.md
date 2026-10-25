# Iteration 009: gap analysis and delta design

Tooling: the claude-context MCP server failed to connect in this session (ToolSearch: "configured MCP servers
failed to connect: claude-context"). I read known paths and used targeted grep only.

## 0. What the run tells us

One run: target_s0 (E1-01, seed 0), rc 3 (`unsatisfied`), 78 s. The iteration 008 run plan also asked for
E1-01 seed 9 and V1–V3 seed 9 with judged variants. Those runs were not made, so the variants are still
unjudged (section 5).

| Judge | Verdict | Class | Score | Failing L3s |
|---|---|---|---|---|
| 1 | DOES NOT MEET | CORRECT | 133/134 | L3.1.6.1 (w1, grid) |
| 2 | DOES NOT MEET | CORRECT | 132/134 | L3.1.6.1 (w1, grid), **L3.8.3.1 (w1, lid screw-hole ligament 1.346 < 1.5)** |

- **Iteration 008's C1 worked.** E1-01 is back to CORRECT. The USB is exposed by `rule:text_coverage` with no
  question, and every gate and every weight-3 L3 passes. The self-report agrees with both judges within 0.005 mm.
- **The judges disagree on L3.8.3.1.** Judge 1 did not measure the ligament round the lid screw holes. Judge 2
  ray-cast every 2° round each hole at mid-plate (Z 15.4) and measured 1.346. Judge 2's reading is the
  literal one:
  - L1.8 says "closed on all sides except the ports and screw holes", and L2.8.1 lists the screw holes as
    openings, so L2.8.3's "every opening" includes them.
  - I treat it as a real defect.
- **The agent's own checks are blind to it.** `checks.json` has no ligament check: 14 clear_of, 8
  pilot_engagement, 8 boss_od, 4 aperture_count, 4 pilot_depth, 3 inside, 3 aperture_oversize,
  3 port_below_split, separable, seated, bbox_within, lip_engagement, grid_conformance and coverage.

## 1. Defects → root causes

| Id | Defect | Root cause in the agent | Class |
|---|---|---|---|
| D1 | L3.8.3.1: each lid screw hole (`boss_k_lid_hole`, Ø3.4, the M3 `clearance_diameter`) sits in a pad (`boss_k_pad`) of Ø6.1, so the ring outside the lid plate is (6.1 − 3.4)/2 = 1.35 < 1.5 | **RC-901 (missing sensor).** No check measures L2.8.3 ("≥ 1.5 of material round every opening, to wall edges, floor top, seam and neighbouring openings"). `rules.min_ligament` is used only as derivation terms: the split above port tops (`derive_features`) and port spacing (`layout.Placer` `ports_do_not_fit`). There is no measured error signal for it, so the self-report says PASS and the agent cannot see or correct the defect. The section 5 check table in ARCHITECTURE has no ligament row either: the target design itself left out an L2. | missing check / error signal |
| D1′ | Same defect, derivation side | **RC-902 (wrong derivation input).** `boss_k.d = max(setpoint(fastener.lid.min_boss_od), fastener.lid.pilot_diameter + 2·rules.boss_wall_min)` sizes the corner column for the **base pilot** only. The lid pad copies that diameter (`boss_k_pad.d = boss_k.d`), but the pad carries a different, larger opening: the lid clearance hole. No term relates the pad to the hole it surrounds, so a catalogue screw whose `clearance_diameter + 2·min_ligament` exceeds its `min_boss_od` (M3: 6.4 against 6.0) always under-sizes the pad. The rule is generic, so this is not specific to the box: the same geometry would fail with any lid screw of that kind. | derivation omits a constraint |
| D1″ | Latent, same family: the split term `<cut>.top + rules.min_ligament` sits exactly on the limit (7.9 says every one-sided minimum the derivation sets gets the setpoint margin). Not judged as failing (E1-01's split is set by the cavity term), but it would sit at 1.500 on any request where a port cut sets the split (for example V3 on sockets). The new sensor would then pass or fail on tessellation noise. | **RC-903.** One one-sided minimum was missed when 7.9 extended `setpoint` to all derived minimums. | setpoint rule not applied |
| D2 | L3.1.6.1: pins off the 2.54 grid (w1) | **Not an agent gap.** The agent already reports it as typed conflicts: `flush_to_edge` for module_1_1 and `pin_pattern` for both jacks, as in iterations 006–008. Both judges say it is a requirement/catalogue conflict: the Pico's best residual inside the USB_MOUTH window is 0.63, and the PJ-320A terminals can get no closer than 0.54 anywhere. | Robin, questions 2/3 (unchanged) |

**Grouping.** D1, D1′ and D1″ are one gap: L2.8.3 has no sensor, and the derivation sets two of its terms
incompletely. RC-901 is the high-leverage cause. With a measured ligament check on every opening:

- the prescore (7.11) and the self-report see any future ligament violation, in any archetype and with any
  fastener;
- the controllable error then covers L1.8.

RC-902 and RC-903 move the setpoint inside the band, so the new check passes with the design margin.

**Ledger check (no repeated idea, oscillation watch):**

- No earlier iteration added a ligament check. Iteration 002 introduced `min_ligament` as derivation terms
  only (LEDGER, C6). This is new, not a repeat.
- **No oscillation risk from prompts.** Nothing here touches a prompt or an LLM decision. The change is a
  sensor plus a derivation term.
- **Side effect, measured by formula:**
  - The corner columns grow from Ø6.1 to Ø6.5 (M3: 3.4 + 2·1.5 + 0.1).
  - Each column sits on the corner diagonal with `ax = corner − √½·(d/2 + c)`, so its outer extent grows by
    0.2·(1 + √½) ≈ 0.34 mm per side, about 0.7 mm per axis.
  - E1-01 goes to about 83.8 × 63.0 (max 90 × 70). V2_s8 goes to about 103.8 × 58.0 (max 110 × 65).
  - V1 (92.3 × 72.3 → 93.0 × 73.0, max 100 × 80) and V3 with the Pico on a short end (board depth 40, Y about 53, max 60) stay inside.
  - The prescore re-checks `bbox` per candidate anyway, so no candidate that the growth pushes out can be chosen silently.

## 2. Delta (one pass; no cad_agent.py / cascade.py / cad_checks.py / layout.py / part.json change)

### C1 (RC-901): a measured `ligament` check on every opening

**New function `assembly_checks.ligament(body, cut, axis, plane, minimum, tol, check_id, floor_z=None,
neighbours=None)`.** It returns a `cc.CheckResult` of type `ligament`, in mm.

Recipe (2-D, in the plane normal to the opening's axis, at the middle of the material the opening passes
through):

1. Rotate so `axis` maps to Z (identity for axis 2; for X or Y use a fixed rotation), then
   `S = body.slice(plane)` and `C = cut.slice(plane)`, both as `CrossSection`, using `to_polygons()`.
2. **Rim samples.** Sample C's boundary, polygon vertices plus subdivision so no gap is longer than
   `tol.measure · 10`. Keep the samples that lie on S's boundary within `FACE_TOUCH`: these are the points
   where the opening has a wall. Samples of C's boundary that lie in air, outside S, are dropped. For a lid
   hole that crosses the plate edge, the whole hole wall lies in the pad, so every sample is kept.
3. **Other boundary.** These are the edges of S's polygons whose midpoints are farther than `FACE_TOUCH`
   from C's boundary: outer edges, other openings, the seam.
4. **Ligament.** The minimum distance from a rim sample to any other-boundary edge: numpy point-to-segment,
   vectorised.
   - This is the 2-D minimum distance between the hole and every other boundary. It is never larger than
     the judge's outward ray length, so the agent errs against the design (7.7).
   - With `floor_z`, the ligament is also `min(z of rim samples) − floor_z`, the "floor top" clause of
     L2.8.3. The minimum of the two is reported.
5. **Pass and margin.** Pass at `ligament ≥ minimum − tol.measure`, margin `(ligament − minimum + tol.measure)
   / tol.scale`: the same convention as `value_at_least`.
6. **Evidence:**
   - `ligament`, `minimum`, `plane`, `axis`;
   - `where`: the 3-D point of the worst rim sample and the 3-D point on the nearest other boundary;
   - `toward`: `outer`, `floor_top`, or the id of the neighbouring cut, found by testing which plan cut
     volume's slice the nearest edge lies on;
   - `needed`: "material radius at that point ≥ hole edge + `minimum`";
   - `detail`.
   - An empty slice, or no rim samples, fails with margin −1 and `detail` "no material round <cut> at
     <plane>". It never passes vacuously.

**`run_plan`:** a new branch, `elif typ == "ligament": out.append(ligament(bodies[a["body"]], vols[a["cut"]],
a["axis"], a["plane"], a["min"], plan.tol, cid, a.get("floor_z"), {c: vols[c] for c in a.get("neighbours",
[])}))`. `measure_package` needs no change, because the self-report re-measures it on the delivered STLs.

**`assembly.build_plan`: one generic loop** after the aperture block, `add_ligament_checks(st, plan)`.

- For every cut node `n` with `n.role in APERTURE_CUT_ROLES` (port_cut, pilot, screw_hole) and every body
  `b in BODIES` with `vol(fg.solid(n) ^ body_solid[b]) > tol.pen`:
  - **axis:**
    - a `port_cut` uses its wall's normal axis (`SIDE_BOUND[n.wall][1]`);
    - any other cut uses the world axis nearest the cut node pose's local Z (`argmax |res.poses[n.id][:3, 2]|`).
    - No role is mapped to a hard-coded axis beyond what the node already says.
  - **plane:** the midpoint, along that axis, of the bounding box of `solid(n) ^ body_solid[b]` on the
    resolved manifold solids. It is computed once at plan time and stored, so the STL re-measure slices at
    the same plane.
  - **floor_z:** for a `port_cut` on the tray body, `cavity.z0` (the floor top). Otherwise none.
  - **check:** id `ligament_<cut>_<body>`, `min = rules.min_ligament`, text "at least <min> mm of material
    round <cut> in <body> (to the outer edges, the floor top, the seam and the neighbouring openings)".
  - The cut solid is already a plan volume for the slabs (`vols[n.id]`); reuse it.
- **Body solids** come from `st.solids` when present (Build), else are built, as the slab block does.
  `prescore` already builds them, so the ligament checks enter the controllable error with no extra plumbing.
- **Cost:** two slices and one vectorised distance per check. About 20 checks on E1-01 (4 standoff pilots,
  4 boss pilots, 4 lid holes, 3 port cuts, plus any second body hit). Expected under 0.1 s, well inside the
  7.11 bound. The implementer measures it and writes the figure in the ledger.
- **Trace:** no `slots` or `parts`, so it stays in the matrix's `rules` row until M10. That is the same
  status as the other value checks, and is acceptable.

**ARCHITECTURE:** section 5 gains the row (done in this iteration, see 7.12).

### C2 (RC-902): the material round an opening is derived from that opening

In `derive_features`, the corner column's diameter takes every opening it carries:

```
"d": max(setpoint(fastener.lid.min_boss_od),
         fastener.lid.pilot_diameter + 2*rules.boss_wall_min,
         setpoint(fastener.lid.clearance_diameter + 2*rules.min_ligament))
```

- **The pad keeps `d = boss_k.d`**, so the lid's pads stay flush with the base columns (L2.7.4 flushness)
  and the lip notches (`boss_k.d + 2·sliding_fit`) follow automatically.
- **Values:**
  - for the M3 lid screw from part.json: 3.4 + 3.0 + 0.1 = 6.5, so the ligament is 1.6 nominal and about
    1.594 after the inscribed-pad / circumscribed-hole polygon allowance at fn 64;
  - the base pilot ring becomes (6.5 − 2.5)/2 = 2.0.
- **Standoffs are unchanged.** Their pilot is not a through opening, and `pilot + 2·standoff_wall_min`
  already gives a 1.6 ring.
- **No numbers in code:** every term reads part.json or `design_rules.json`. The `lid_screw` docstring is
  updated to the new formula.

### C3 (RC-903): the seam term gets the setpoint margin

In `derive_features`, change the split terms to `f"{n.id}.top + {setpoint('rules.min_ligament')}"`.

- `port_below_split` keeps its limit `top + rules.min_ligament ≤ split`, now with margin ≥ `design_margin`.
- E1-01's split is unchanged, because the cavity term dominates. Assert this in the test below.
- This completes 7.9's "every one-sided minimum the derivation sets".

### Not in this delta (and why)

- **L3.1.6.1 grid.** This is a requirement/catalogue conflict that the agent already reports as typed
  conflicts. Changing placement to chase it would break L3.1.3.1 (w2) to fix a w1, which the conflict rule
  of 7.7 forbids. E1-01 cannot MEET until Robin answers questions 2/3.
- **M9 inner loop (Solve with deadbeat on free params).** The ligament margin is invertible in `boss.d`, so
  a Solve step could close it numerically. But the setpoint pattern (7.7, 7.9) already closes every
  one-sided minimum at derivation, and M9 is a larger change with no judged defect that needs it yet. With
  C1 in place, M9 now has a real sensor to act on. It stays the next milestone once a judged defect needs a
  continuous correction that derivation cannot set directly.
- **A full L2 → sensor audit** (L3.7.4.1 seam flushness, L3.8.2.x thickness, L3.8.4.1 wall-floor contact,
  L3.9.x printability, L3.10.x stability, L3.11.1.1 install path).
  - Both judges measured these as passing with margin.
  - Adding sensors for them is M10/M5 work, best done one judged defect at a time, as here.
  - Note for the next analyst: the judges found this defect because the agent had no sensor, not because the derivation was wrong for the box. The audit list above is where the next "agent's checks miss this" will come from.
- **Bosses protruding beyond the walls** (judge 2, O3). This is cosmetic and inside every limit. C2 makes
  them 0.34 mm per side larger. Moving the columns inside the cavity corner would change V-HOLE-KO and
  V-DRIVER clearances and the cavity, which is not needed for any judged defect.

## 3. Unit tests (fake LLMs, no Ollama)

New tests in `test_assembly_checks.py`, class `TestLigament` (pure geometry, no LLM):

1. `test_round_hole_in_pad_matches_the_judge_case`.
   - Setup: a 20 × 20 × 2.4 plate, a Ø6.1 inscribed pad cylinder whose axis sits 0.39 inside the plate edge,
     and a circumscribed Ø3.4 hole on that axis (fn 64), the geometry judge 2 measured.
   - Expected: the ligament is 1.344 ± 0.01 (fails, margin < 0), `toward == "outer"`, and the worst point lies
     on the pad side, outside the plate.
   - With pad Ø6.5 the ligament is 1.594 ± 0.01 and the check passes.
2. `test_agrees_with_ray_cast_recipe`. On the same two cases, an independent trimesh ray cast (judge 2's
   recipe: rays every 2° outward from the hole wall at mid-plate, material length until exit) gives a minimum
   ≥ the agent's ligament and within 0.02 of it. The agent is never more lenient.
3. `test_neighbouring_openings`. Two Ø3 holes whose edges are 1.2 apart in a plate: fails with
   `toward` = the other hole's volume name. At 1.8 apart it passes.
4. `test_wall_opening_seam_and_floor_top`. A wall slab (axis X) with a rectangular opening whose top edge
   is 1.0 below the slab top fails, toward `outer`. With `floor_z` set 1.2 below the opening's bottom edge
   and the top fixed, it fails with `toward == "floor_top"`. With both at 2.0 it passes.
5. `test_no_material_is_a_failure`. A plane that misses the body gives margin −1. It never passes.

New and changed tests in `test_assembly.py`:

6. `TestDerive.test_every_opening_has_a_ligament_check` (E1-01 and V1, scripted, manifold only).
   - Every cut with a role in `APERTURE_CUT_ROLES` has at least one `ligament_<cut>_<body>` spec.
   - The set of (cut, body) pairs equals the pairs with intersection volume > `pen`.
   - Lid holes are on `lid`; pilots and port cuts are on `base`.
   - Each port cut on the tray has `floor_z == cavity.z0`.
7. `TestDerive.test_ligament_checks_pass_with_margin` (E1-01, V1, V2, V3 scripted, manifold).
   - Every ligament check passes with margin ≥ `design_margin − 0.01` (polygon allowance).
   - The lid-hole rows have `toward == "outer"`.
   - The boss diameter equals `clearance_diameter + 2·min_ligament + design_margin`, computed from
     `st.fasteners` and the rules, never typed.
8. `TestDerive.test_ligament_is_non_vacuous` (mutant).
   - With `design_margin = −0.2` (the existing `neg_rules` helper), boss d is 6.2, so the four
     `ligament_boss_k_lid_hole_lid` checks fail with ligament ≈ 1.4.
   - Separately, patch the derivation to drop the C2 term (monkeypatch the boss "d" expression back to the
     iteration 008 formula). The four lid-hole checks then fail at 1.344 ± 0.01. **This reproduces the
     judged defect and fails on the pre-delta code**, because the pre-delta code has no check to fail.
9. `TestEndToEnd.test_self_report_has_ligaments` (E1-01, OpenSCAD present, else skipped).
   - The self-report on the delivered STLs lists every ligament check.
   - Each result agrees with the manifold result within 0.02.
   - `all_passed` is true except grid.
10. `TestDerive.test_split_ligament_has_the_design_margin` (C3).
    - With a scripted V3 socket case, or a spec with `keepout_above` set to 0 so that a port cut sets the
      split, `split − (cut.top + min_ligament) = design_margin` ± 1e-9.
    - On E1-01 the split is unchanged from the pre-delta value (the cavity term dominates).
11. Prescore: `TestArrange.test_prescore_is_pure` and the V3 filter test stay green unchanged. They now run
    the ligament checks too. Add one assertion to `test_prescore_is_pure`: the ligament results appear in
    the prescore's checked ids.

**Changed tests (behaviour intentionally changed, RC-902):**

- `TestDerive.test_one_sided_minimums_have_the_design_margin`:
  - the boss diameter's expected value becomes `max(lim + m, pilot + 2·wall, clearance + 2·min_ligament + m)`;
  - the "boss OD is the catalogue minimum + margin" loop becomes "boss OD is the ligament term + margin",
    with a difference of m between the margin and zero-margin runs, unchanged.
  - Justification: the lid boss is now sized by the opening it carries.
- `TestDerive.test_minimum_checks_pass_with_margin_and_fail_on_a_mutant`:
  - with `design_margin = −0.2`, `boss_od_boss_k` now passes (6.2 ≥ 6.0), because the ligament term sets d.
  - So `must_fail` loses the four `boss_od_boss_*` ids and gains the four `ligament_boss_*_lid_hole_lid` ids.
    The count stays 13.
  - Justification: the binding minimum of the lid boss moved from `min_boss_od` to the ligament. The test
    stays non-vacuous on the binding constraint.

**Hard-coding guard:** `test_no_hardcoding` must stay green. The only new literals are the check type
name, role names already in `APERTURE_CUT_ROLES`, and the rotation indices.

**Full suite:** `venv/bin/python -m unittest test_cascade test_cad_checks test_review_fixes test_cad_agent
test_benchmark_runner test_parts test_feature_graph test_assembly test_assembly_checks test_no_hardcoding`.

## 4. Expected effect on the judges' verdict

- **E1-01 target_s0:**
  - L3.8.3.1 passes: lid-hole ligament about 1.59, every port and pilot at least 1.6.
  - The judge's ray cast then agrees with the self-report's new `ligament` rows, so L3.12.2.1 stays PASS.
  - Verdict: DOES NOT MEET / CORRECT, 133/134 for both judges, with only L3.1.6.1 left (Robin).
  - Bbox about 83.8 × 63.0 × 24.7. The worst weight-3 margins are unchanged (0.10 by design).
- **V1–V3:** no expected change of class from C1–C3, since ligaments pass by construction. But they have
  never been judged, and convergence (ARCHITECTURE 8) needs each to be CORRECT once.
- **Convergence:** still blocked on L3.1.6.1 for E1-01 MEETS, which only Robin can unblock. The agent now
  has nothing judged against it except that conflict.

## 5. Run-step instructions for iteration 010

- Run `( SEED=0; run_one E1-01 target_s0 ); run_one E1-01; run_one V1; run_one V2; run_one V3` with
  SEED = 10.
- **The judges must grade V1, V2 and V3, as well as target_s0 and E1-01.** Iterations 008 and 009 both
  skipped the variant judging. The orchestrator should check `runs.jsonl` has five rows before judging.
- **Judges should measure L3.8.3.1 round every opening, screw holes included** (judge 1 did not this
  iteration).

## 6. Questions for Robin

- **Q7 (new):** does L2.8.3's "every opening" include the lid screw holes? L2.8.1 says they are openings.
  The agent now treats them as openings (C1/C2). The cost is about 0.7 mm per axis of outside size.
- Q1–Q6 are carried over unchanged:
  - Q1: L3.12.1.1 units heuristic (the lid's 4.5 mm Z);
  - Q2: perfboard grid registration;
  - Q3: PJ-320A footprint against the 2.54 grid;
  - Q4: V-SEAT inside V-INSTALL (L3.11.1.1, which judge 2 also raised as O2);
  - Q5: rubric 3.4 slab inset;
  - Q6: does a named plug always mean "reachable from outside".
- **Q2/Q3 are the only thing between the agent and E1-01 MEETS.**
