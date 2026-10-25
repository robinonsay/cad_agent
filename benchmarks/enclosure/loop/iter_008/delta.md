# Iteration 008: gap analysis and delta design

Tooling: the claude-context MCP server failed to connect in this session (ToolSearch: "configured MCP servers
failed to connect: claude-context"). I read known paths and used targeted grep only.

## 0. What the run tells us

Five runs, all rc 3 (`unsatisfied`), about 70 s each. Only target_s0 was judged.

| Run | Own checks | Contents vote, Pico exposed | `assy_expose` votes (T0, T0.7, T0.7) | Pico exposed in the end | Notes |
|---|---|---|---|---|---|
| target_s0 (E1-01, seed 0) | 48/50: grid, **text_coverage** | no (1 yes : 2 no) | **yes, no, no** | **no** | judged: DNM / **WRONG** (G3), both judges |
| E1-01_s8 | 52/53: grid only | yes | not asked | yes | would be CORRECT, like iteration 007 |
| V1_s8 | 45/47: grid, **text_coverage** | no (0:3) | **yes, no, no** | **no** | WRONG-class against L1.5 |
| V2_s8 | 55/56: grid only | no (1:2) | yes, yes, yes | yes | CORRECT-class on its own checks |
| V3_s8 | 48/50: **bbox**, grid | no (0:3) | yes, yes, yes | yes | Pico on a **long** side, so the box is 63.6 deep (max 60) |

**E1-01 regressed from CORRECT (iterations 004–007) to WRONG.**

- The judged defect is the missing USB opening: L3.5.1.1 (G3 blocker), L3.5.2.1 and L3.5.3.1.
- Everything else that failed follows from that one decision:
  - L3.1.3.1: an unexposed Pico is placed "nearest the board centre", 5.5 mm inboard.
  - L3.12.2.1: the self-report has no USB `clear_of` and expects 0 openings at −X, because its checks are derived from the same "unexposed" decision.
  - L3.1.6.1: the header half of the residual changes because the Pico moved.
- The cause is measured in the transcripts. Iteration 007 changed the Contents wording:
  - before: `usb (takes a plug_microusb_b)`, which got a greedy "yes" (iterations 004–007, seed 0);
  - after: `usb connector (takes a micro-usb plug)`, which got a greedy **"no"** (`iter_008/target_s0/.../llm/007_assy_contents.txt`).
- Iteration 007's safety net then caught it, exactly as designed:
  - ExposureCoverage sensed L1.5 naming the micro-USB plug and asked the focused question.
  - The greedy answer was **yes**. The two T = 0.7 samples said no, so the tally was 2:1 "no", the same as V1_s8.
  - The agent then delivered a design that its own sensor reports as failing (`text_coverage`, a quoted `coverage` conflict).
  - This was honest, but it was still WRONG.

## 1. Defects → root causes

| Id | Defect (judges / run outputs) | Root cause in the agent | Class |
|---|---|---|---|
| D1 | E1-01 L3.5.1.1 / L3.5.2.1 / L3.5.3.1: no USB opening (G3). V1_s8: same against its L1.5 | **RC-801.** `ExposureCoverage.update` acts on a sensed error but lets a noisy vote override it. Python already knows that "unexposed" leaves a hard check failing (`text_coverage`, margin −1) and that "exposed" closes it. It still asks a 9B yes/no and accepts a 2:1 "no" built from two T = 0.7 samples that out-vote the greedy "yes". That contradicts ARCHITECTURE 4.1: the middle loop accepts only a strict decrease of the error, and the LLM ranks only alternatives that tie on error. Here they do not tie. | wrong control logic: error-increasing choice accepted |
| D1′ | Same defect, upstream: the E1-01 regression | **RC-802.** Exposure still comes first from the open-loop Contents vote. That vote is wording-sensitive: iteration 007's `part_words` change flipped seed 0 from yes to no. A decision Python can sense (text evidence, 7.10) must not depend on prompt wording. This is the same rule 7.10 already applies to ChooseStack ("one option with evidence is chosen by rule, no question"). Exposure was left out of that rule. | evidence rule not applied to exposure |
| D2 | E1-01 L3.1.3.1: USB mouth 5.5 mm inboard | Consequence of D1: `layout.py` rule 7 puts unexposed parts at the free spot nearest the centre. It is correct for an unexposed part. | none (closes with D1) |
| D3 | E1-01 L3.12.2.1: self-report lacks USB `clear_of` and expects 0 at −X | Consequence of D1: the rule-derived checks follow the exposure decision, and `text_coverage` did report it. | none (closes with D1) |
| D4 | V3_s8 `bbox` fails: the Pico was placed on a long side, so the box is 63.6 mm deep against a 60 mm maximum (run output, L1.10 and L1.1) | **RC-803.** ConfirmArrangement ranks the feasible edge assignments only by the LLM's vote and p_yes. Every p_yes was under 0.19, so they are noise, and an A/B pick chose "Pico −Y". The Python error that each candidate would produce (here `bbox`) is measured only after the one chosen candidate is built. This is the missing piece of M11: "discrete alternatives pre-scored, LLM ranks ties". ARCHITECTURE 7.4 called ConfirmArrangement "the first piece of the middle loop". It never got the pre-score. | missing error signal at the decision point (M11 slice) |
| D5 | Both judges: `model_left`/`model_right` and `model_front`/`model_back` are byte-identical, so the end views cannot show the openings | **RC-804.** RenderViews reuses `cad_agent.VIEWS`, which are exact orthographic elevations. A wall facing the camera head-on and the inner wall seen through an opening get the same flat shade, so the openings vanish and the two opposite views coincide. | output observability |
| D6 | L3.1.6.1, pins off grid (w1) | Not an agent gap. A typed requirement/catalogue conflict (`pin_pattern` 0.54 for PJ-320A; Pico `flush_to_edge` 0.98 once it is flush). | Robin, questions 2/3 (unchanged) |

**Grouping.** D1, D1′, D2 and D3 are one decision: closing RC-801 and RC-802 removes all four. D1 and D4 share one principle: a discrete choice must be scored by Python's error before the LLM's preference is used, and the LLM only breaks ties. That is the 4.1 middle loop, applied to the two discrete choices that failed this iteration.

**Ledger check (no repeated idea, oscillation watch):**

- **Iteration 007 (C3)** added the sensor (`text_coverage`) and the focused question. The sensor worked: it found the defect in target_s0 and V1_s8. The question failed (2:1 against the greedy answer).
  - This delta keeps the sensor and removes the vote's power to increase the error. That is not a repeat: the question was the failing part, and it is gone.
- **Oscillation:** E1-01 went CORRECT (004–007) → WRONG (008) because of a prompt-wording change.
  - Fixing that by re-wording `part_words` again would be the oscillation. This delta does not touch any prompt wording.
  - It makes exposure independent of wording whenever the text names the plug.
- **Iteration 003** built vote + rank, and 006/007 refined the symmetry classes. This delta does not change them. It filters their input by measured error.

## 2. Delta (one pass; no cad_agent.py / cascade.py / cad_checks.py / layout.py change)

### C1 (RC-801, RC-802): exposure is decided by the error signal; the LLM is not asked to override a sensed requirement

**Rule:** a text that names a content connector's mating plug requires that connector to be exposed (7.10). The two alternatives are not a tie on error: "unexposed" costs one failing hard check and "exposed" costs none. The decision is therefore Python's, with no question. The LLM still decides exposure for connectors whose plug no text names (the Contents vote), and those votes can only add openings.

**`assembly.ExposureCoverage.update`:**

- Keep the sensing exactly as it is: `named_parts`, `mated`, `takers`, the note for a named plug that no content connector takes.
- For each violation (a named plug whose taker is unexposed):
  - set `it["exposed"] = True` and `items[it["id"]].exposed = True`;
  - set `it["exposed_by"] = "rule:text_coverage"`;
  - add the row with `resolved = "exposed"` and `evidence` (the quoted sentences, as now);
  - record `choice(st, f"exposed[{id}]", True, "rule:text_coverage", evidence=..., overrides={"contents_votes": <the Contents counts for that key>})`.
- To get those Contents counts, `Contents.update` keeps its `counts[f"{pid}.exposed"]` per item (`it["exposed_votes"] = dict(...)`). They are recorded only, never used to decide.
- Delete `ExposureCoverage.ask`, and with it the `assy_expose` label. It is dead code once no path asks it. Its grammar bug ("the micro-usb plug plug into") goes with it.

**Infeasible fallback (`ArrangeContents.update`):** an exposure forced by coverage must never cost the package (G0).

- When no feasible candidate exists (`not cands`) and at least one exposed item has `exposed_by == "rule:text_coverage"`:
  - revert every such item to unexposed;
  - set each matching `st.coverage` row to `resolved = "unexposed"` and `reason = "no feasible arrangement with it exposed: <pruned kinds>"`;
  - rewrite the choice with `by = "rule:coverage_infeasible"`;
  - append a note and **re-run the placement once** with the reduced exposed set.
- It runs once because the reduced set contains no coverage-forced item, so it is finite with no cap.
- `text_coverage` then fails with the existing quoted `coverage` conflict. This is the honest-failure path of iteration 007, now reached only when exposing is geometrically impossible.
- Put the placement block (from "exposed = ..." to the `cands` list) in a helper `self.candidates(st, placer)` so the retry is one call.

**Data model:** `assembly.coverage` rows gain `reason` (fallback only). The `by` values are now `rule:text_coverage` and `rule:coverage_infeasible`. `llm:coverage` disappears.

**Known limit (documented, not coded):** a sentence that names a plug in order to *deny* it ("no USB cable is needed") would be read as a requirement.

- No request or variant has one.
- The remedy belongs in the outer (requirements) loop: the M10 translator would turn that L1 into a check with the opposite sense. It does not belong in a vote.

### C2 (RC-803): pre-scored arrangement candidates, the M11 slice of the middle loop

**New function `assembly.prescore(st, cand) -> dict`** (pure; no LLM, no OpenSCAD, no files). It runs the downstream plant on a scratch copy of the state:

1. **Scratch state.** `sc = scratch_state(st)` makes `copy.copy(st)` and fresh copies of the fields that later stages mutate: `graph`, `choices`, `fasteners`, `notes`, `assumptions`, `history`, `layout`, `coverage`, `stl_source`, `solids`. `catalog` and `rules` are shared, because they are read-only.
2. **Accept the candidate.** `accept_layout(sc, cand["layout"], cand["assignment"])` is the state half of `ArrangeContents.accept`, factored out, with no logging. `accept` calls it.
3. **Run the downstream stages.** Factor the bodies of the stage `update` methods into functions on a state, so the real stages and `prescore` share one code path:
   - `build_envelopes(sc)`, from `BuildEnvelopes.update`;
   - `choose_archetype_rule(sc)`, the `rule:only_feasible` branch. When there are two or more archetypes it takes the current choice, or else the first;
   - `derive(sc)`, from `DeriveFeatures.update`: `lid_screw`, `derive_features`, `resolve`.
   - Each returns an error string or `None`, and the stage's `update` turns that string into `self.fail`.
4. **Build and measure.** `sc.solids = {b: fg.body_solid(sc.graph, b, sc.resolved) for b in bodies}`, then `plan = build_plan(sc)` and `results = ac.run_plan(plan, sc.solids)`.
5. **Return** `{"key": cc.error_key(controllable).to_dict(), "failing": [ids], "uncontrollable": [ids], "error": None | str}`.
   - `controllable` = the failing results whose `evidence` has no `conflict`.
   - A typed conflict (grid `pin_pattern`/`flush_to_edge`, `coverage`) is the requirement loop's (4.4 item 3), so it never ranks arrangements.
   - A derivation error gives `key = {hard_failures: inf}` and the message.

**`ArrangeContents.update`** (the edge vote and `assignments` stay as they are):

- After `cands` is built (capped by `arrange_rank_max`, as now), call `c["prescore"] = prescore(st, c)` for every candidate.
- **Filter:** keep the candidates whose `(hard_failures, violation)` equals the minimum. Compare violation with `cascade.ACCEPT_EPS` through `cc.strictly_better`, so near-equal floats tie. Failures are already restricted to `controllable`.
- Then run the existing `rank_candidates` / `decide` on the survivors only. They keep the vote order, so survivor index 0 is the highest-voted survivor and `voted` keeps its meaning.
- The decision string gains a prefix when the filter removed anything: `prescore+llm:vote+rank`, `prescore+llm:pick` or `prescore+llm:rank`.
- With one survivor, take it with `by = "rule:prescore"` and do not ask p_yes or A/B.
- `st.arrange` records:
  - every candidate's `prescore` (key, failing, uncontrollable);
  - `filtered` (assignments removed, with their failing ids);
  - `prescored` (count).
- Pruned candidates (`LayoutError`) are recorded as now.

**Why ties go to the LLM, not to the smallest violation:**

- Python cannot sense the request's relations, such as "the other short end" or "same end".
- If arrangements with zero controllable failures were ranked by residual size, a float difference would silently override the controller.
- E1-01 is the case that matters: "Pico −X / jacks +X" and "all on +X" may both measure clean.
- So only a *strict* difference in controllable error removes a candidate. This is the 4.1 rule: "the LLM ranks only the ones that tie on error".

**Cost:**

- One manifold build and one `run_plan` per feasible candidate, at most `arrange_rank_max` (16) of them.
- The implementer measures it on E1-01 at fn 64 and writes the number in the ledger.
- If it is over 60 s per run, add a generic rule `prescore_fn` (`design_rules.json`, provenance "segments for candidate scoring only") and use it only inside `prescore` (`sc.rules` gets a copy of the values with `fn` replaced).
- The delivered build keeps `fn`.

### C3 (RC-804): end views that show openings

- **New** `assembly.assembly_views(rules) -> Dict[str, tuple]`, built from `ca.VIEWS`:
  - `iso` and `top` unchanged;
  - each elevation (`front`, `back`, `left`, `right`) gets `rotx = ca.VIEWS[k][3] - rules["view_elevation_deg"]`, so the camera looks slightly down;
  - the floor seen through an opening is then shaded differently from the wall, and opposite views differ.
- **New generic rule** `view_elevation_deg` = 20 (deg) in `design_rules.json`, with source "camera elevation above horizontal for the elevation renders of assembly mode, so openings show".
- **`RenderViews.update`** uses `assembly_views(st.rules.values)` for `model` and `ghost`. `cad_agent.VIEWS` and the other modes are untouched.
- No literal angle goes in `assembly.py`: 90 is a guarded number in `test_no_hardcoding`, so the value is derived.

### Not in this delta (and why)

- **Prompt re-wording of Contents or edges.** That is the iteration 007 regression mechanism; see the oscillation note.
- **Sensing "same/opposite edge" relations (4.2 `group`).** This would make V3/E1-01 arrangement ties smaller, but C2 already removes V3's failing class. Next candidate if a variant lands on a same-end arrangement.
- **Reworking `tally` (greedy versus T = 0.7 votes).** No remaining decision in this iteration overrides a measured error with a vote. This is to be revisited if it reappears, with the measured flip rate.
- **Full M11 Correct selector after Verify** (re-entering stack, archetype or exposure from a failing delivered check). C2 pre-scores the one choice that failed. The post-Verify loop is the next M11 slice.
- **D6 (grid).** Robin, questions 2/3.

## 3. Unit tests (fake LLMs, no Ollama)

Generalise the `recorded_answers(run)` helper to `recorded_answers(run, iteration_dir=ITER007)`, and add `ITER008 = .../loop/iter_008`. Tests that read recorded transcripts skip when the folder is missing, as the existing ones do.

**New tests:**

1. **`TestReplayIter008.test_target_s0_exposes_the_named_usb_without_a_question`** (E1-01). It uses the recorded `iter_008/target_s0` answers: spec + re-asks, contents with the Pico "no" 2:1, edges, and the `assy_confirm` p_yes as in `iter007_llm`. It removes the `assy_expose` key from the script, so any call raises.
   - No `assy_expose` call.
   - `choices["exposed[module_1]"].by == "rule:text_coverage"`, the evidence quotes L1.5 verbatim, and `overrides.contents_votes` holds the recorded 1:2.
   - `coverage[0].resolved == "exposed"` and `text_coverage` passes.
   - Only `grid_conformance` fails. `clear_module_1_1_plug` exists and passes.
   - `apertures_-X` expects 1 and measures 1 through.
   - The Pico's USB mouth is flush with the board edge. The expected X is computed from `parts/rpi_pico2/part.json` (USB_MOUTH datum versus the PCB min-X) and the board edge; it is never typed.
   - This test **fails on today's code** (it raises on the missing `assy_expose`, or with an empty script the vote leaves the Pico unexposed).
2. **`TestReplayIter008.test_v1_s8_exposes_the_named_usb`**: the same for `V1_s8` (recorded expose votes 1:2 ignored). The USB opening is on the jack's wall, and per wall through = expected = port cuts.
3. **`TestContents.test_coverage_infeasible_is_reported`** (replaces `test_coverage_no_is_reported`). It patches `lay.Placer.place` to raise `LayoutError("collides", ...)` whenever the coverage-forced item is in the assignment, and runs V1 with the iteration 007 recorded answers.
   - Exactly one retry; the package is written (rc 3, not 1).
   - `coverage[0].resolved == "unexposed"`, with a `reason` naming "collides".
   - `by == "rule:coverage_infeasible"`.
   - `text_coverage` fails, margin −1, with one quoted `coverage` conflict naming the L1.
   - The matrix row of the naming L1 is FAIL.
4. **`TestArrange.test_prescore_removes_a_candidate_with_a_controllable_failure`** (V3). It uses the recorded `V3_s8` edge votes, and a `RankedLLM` whose p_yes is highest for "Pico on a long side", which reproduces the iteration 008 choice.
   - The chosen assignment puts the Pico on an edge whose length equals the board's short side. Edge lengths come from `placer.edges`, never typed.
   - `bbox` passes end to end.
   - `st.arrange.filtered` contains the long-side Pico assignments, each with `bbox` in `failing`.
   - The decision starts with `prescore+`.
   - **Fails on today's code** (bbox fails, as in the run).
5. **`TestArrange.test_prescore_ties_go_to_the_controller`** (E1-01): every feasible candidate has 0 controllable failures, so `filtered == []`. The decision and the chosen assignment equal today's for the iteration 003 replay. `test_iter003_replay_accepts_the_voted_arrangement_by_rank` and `test_e1_ports_on_opposite_short_ends` must stay green unchanged.
6. **`TestArrange.test_prescore_is_pure`**: on the E1-01 state after ChooseStack:
   - `prescore` leaves `st.graph is None`, and `st.choices`, `st.notes`, `st.assumptions` and `st.coverage` equal, before and after;
   - two calls on the same candidate give the same key;
   - a candidate with a typed grid conflict lists `grid_conformance` under `uncontrollable`, not `failing`.
7. **`TestArrange.test_single_survivor_is_a_rule_decision`**: a fake candidate list where only one survives. `by == "rule:prescore"` and there are no `assy_confirm` / `assy_arrange_pick` calls.
8. **`TestRender.test_assembly_views_are_derived_and_distinct`**:
   - the four elevations' rotx equals `ca.VIEWS[k][3] - rules.view_elevation_deg`, and iso/top are unchanged;
   - in `TestEndToEnd` (OpenSCAD present) `model_left.png` and `model_right.png` differ byte-wise for E1-01.

**Changed tests (behaviour intentionally changed; one-line justification each, for the ledger):**

- `TestContents.test_coverage_no_is_reported` → replaced by test 3. The LLM may no longer leave a named plug's connector unexposed. Only geometric infeasibility can (RC-801).
- `TestReplayIter007.test_replay_iter007_exposes_the_named_connector`: assert 0 `assy_expose` calls and `by == "rule:text_coverage"`, instead of 3 calls and `llm:coverage`. Everything else is unchanged (RC-801).
- Any test asserting `assy_expose` labels or `llm:coverage`: the same justification.

The guard `test_no_hardcoding` must stay green. The new literals are labels and rule keys only.

## 4. Expected effect on the judges' verdict

- **E1-01 target_s0 (seed 0):**
  - The Pico is exposed whatever Contents votes, so the −X wall gets its USB cut and the mouth is flush.
  - L3.5.1.1 / 3.5.2.1 / 3.5.3.1 / 3.1.3.1 / 3.12.2.1 return to PASS, as in iterations 004–007 when the Pico was exposed.
  - Back to **DNM / CORRECT 133/134**. Only L3.1.6.1 remains (Robin's grid question).
  - Exposure is now seed-independent, which the 3-seed MEETS criterion needs.
- **V1:** the USB opening on the jack's end wall gives CORRECT-class (it was WRONG on seed 8).
- **V2:** unchanged CORRECT-class (only grid fails).
- **V3:** the long-side-Pico classes are filtered by `bbox`, so the controller chooses among the short-end assignments.
  - With the run's p_yes, the top survivor is "Pico and jack on opposite short ends" (0.160 against 0.124 for both on −X), and a comparative pick decides.
  - CORRECT-class expected. If the 9B picks "both on one end", L1.6 still fails: the trigger for the relation sensor (not in this delta).
- **Render observation:** the elevations now show the openings, so the judges' end-view complaint closes.

## 5. Run-step instructions for iteration 009

- SEED = 9 for E1-01_s9, V1, V2 and V3. Keep **target_s0** (seed 0), because it is the regression reproducer.
- **The judges must grade V1–V3** as well as target_s0. Iteration 008 again judged only target_s0, and convergence needs variant verdicts.
- Implementers: RUN.md section 2 gets the new test count and runtime, and the `TestReplayIter008` note.

## 6. Questions for Robin

Questions 1–5 are carried over unchanged: L3.12.1.1 units, perfboard grid registration, the PJ-320A footprint (L3.1.6.1 is infeasible as written for the jacks), V-SEAT in V-INSTALL, and the rubric 3.4 slab inset.

**Question 6 (new):** should a request sentence that names a cable or plug always mean "reachable from outside"? The agent now treats it that way by rule (C1), and only geometric infeasibility overrides it. If the answer is no, which word or construction should mark the exceptions?
