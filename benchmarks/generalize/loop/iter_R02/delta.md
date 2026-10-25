# Migration delta R02: option-ID bias out of the controller's menus

**Owner decision:** D1 (`../OWNER_DECISIONS.md`): the small local LLM is the controller; Python is the plant, the
sensors, the actuators and the guardrails. **Design:** `../ARCHITECTURE.md` section 10 (10.1, 10.3, 10.4, 10.5 and the
10.8 plan updated for R02). **Base:** commit `4c7d496` (R01), clean tree. Implemented and tested 2026-10-25.
claude-context failed to connect this session (the MCP server did not start), so files were found with targeted reads
and grep. Nothing under `../../holdout/` or `../holdout_results/` was opened, listed or searched;
`benchmarks/heldout.json` and `.mcp.json` were not touched; nothing was committed. The iteration 005 suite was running
when this delta started: the baseline audit was taken while only the (Ollama-free) stub train run was left, and no
agent code was edited before `iter_005/RUN_DONE` existed and `audit_before.json` was written.

## 1. Why

In R01 the controller chose the first menu option in 38 of 39 live votes. The menu was lettered (A, B, ...), the
sensor's corrections always came first and `stop` always last, so agreement could not be told apart from option-ID /
position bias (reviewer finding F2). The research the manager cited: selection bias in multiple-choice answers is
mainly option-ID token bias (Zheng et al., ICLR 2024); small Ollama models' verbalized confidence is nearly constant
and poorly calibrated (Shen 2026); verifier-guided search beats trusting one sampled answer (LATS, ICML 2024); LLMs are
near-random verifiers. R02 removes the letters and the fixed order, makes agreement across orderings the confidence
signal, removes the only LLM probability that gated a decision, and lets the plant's measured error decide among the
controller's alternatives.

## 2. The bias audit (item 1): before and after

`benchmarks/generalize/audit_controller.py` replays every logged controller decision in
`iter_005/*/*/` and `enclosure/loop/iter_012/target_s0/*/` (12 decisions in 9 packages; iteration 012 has no controller
step, it adds an edge vote) against the live ornith-1.5:9b, greedy (T 0, seed 0), in these formats: (a) the original
lettered prompt verbatim; (b) 3 seeded shuffles, re-lettered; (c) 3 seeded shuffles, content-keyed (a reason, then the
action id); (d) a planted wrong action: lettered at A, and content-keyed under 3 shuffles. The plant is sensor-refuted:
it closes an open connector whose plug the text names (the coverage sensor reports it failing again), else it closes an
opening no failing check asks for, else it sets a closure no failing check asks for. Answers are memoised in
`audit_cache.json`. Six edge votes were replayed too (the original plus 3 shuffles of the edge list).

| Controller decisions (12; pooled) | first-position rate | chance (mean 1/N) | consistency across orders | planted-wrong rate | sensor-best rate |
|---|---|---|---|---|---|
| (a) original lettered order | **0.917** (11 of 12) | 0.438 | — (one call each) | — | 1.000 |
| (b) lettered, 3 shuffles | 0.361 | 0.438 | 0.944 | — | 1.000 |
| (c) content-keyed, 3 shuffles | 0.417 | 0.438 | **1.000** | — | 1.000 |
| (d) planted, lettered at A | 0.000 | 0.317 | — | **0.000** (0 of 10) | 1.000 |
| (d) planted, content-keyed, 3 shuffles | 0.333 | 0.317 | 1.000 | **0.000** (0 of 30) | 1.000 |
| after R02: the controller's own vote (`menus.perm_vote`) | 0.429 | ≈0.44 | 0.972 (11 of 12 confident) | 0 of 10 | 12 of 12 |

- `audit_before.json` (before any agent code changed): rows (a)–(d). `audit_after.json` (on the R02 code): the same
  rows (cache hits: the same greedy prompts give the same answers) plus the R02 controller's own decision procedure on
  each logged menu (`agent`).
- Reading: the first-position rate of 0.92 in the logged order falls to chance as soon as the order varies, while the
  pick stays the same action in 10 of 12 decisions across all four lettered orders (never "same position, other
  action"), and the content-keyed answer is the same action in every ordering of every menu. So R01's 38/39 was mostly
  agreement with the sensor, not position bias. The model never took the planted wrong action, even at A. The one
  decision that is not consistent is G02 step 2 (two equally valid corrections, `expose:board.usb` 2 : `expose:board.dc`
  1): exactly the case R02 hands to the verifier.
- Limits: 12 decisions, all where the sensor's correction was right; the plant is generic but simple. Edge votes are
  much more order-sensitive (mean consistency 0.625 across 4 orders, first-position 0.28 vs 0.25 chance; partly because
  the board's half-turn makes -X/+X equivalent), which is why the edge vote is permutation-voted too and its
  consistency recorded (`arrange.edge_vote`).

## 3. The delta, every change classified

| # | Change | Class | Files |
|---|---|---|---|
| 1 | **Bias audit** script: replays logged decisions under original / shuffled / content-keyed / planted formats; per-menu and pooled first-position rate vs 1/N, consistency, planted-wrong rate, sensor-best agreement; optional `--agent` (the R02 vote); bounded calls (decision caps, an answer cache). | tooling (measurement; not agent code) | `benchmarks/generalize/audit_controller.py` (new), `iter_R02/audit_before.json`, `audit_after.json`, `audit_cache.json` |
| 2 | **Content-keyed, shuffled menus** (`menus.py`): an option is an id plus Python's words; the schema (Ollama `format`) is `{reason: string ≤ 240, <key>: enum of ids in Python's order}`, reason first; the model never sees the schema, so the enum order is only the stub's first option. Orderings are the cyclic rotations of one permutation seeded by sha256 of (label, run seed, request, options / state) (`menus.orderings`: with K = N every option leads once; a menu with fewer distinct orderings than K is asked fewer times). | controller-information | `menus.py` (new) |
| 2 | **Controller menu**: `- <action id>: <words>` lines, `stop` shuffled with the rest, the question asks for a one-sentence reason then the id; `Action.id` (generic `<kind>:<target>[=<value>]`, or the actuator's `ident`: `set_closure:rebate`, `stop`); `APPLIERS` (kind → applier) so a new action kind plugs in with no change to the menu, the vote or the search. The seed material is the request, the state digest, the step and the run seed. | controller-information, actuator (registry form) | `controller.py` |
| 2 | **Proposal menus**: Contents (candidate lines), stack (catalogue ids), edge vote (edge lines), face relation (value lines, not_stated included), arrangement classes (new, see 4), vent relation (not_stated no longer pinned last), archetype, the spec owner question (slot names): each shown in seeded orderings via `menus.perm_vote` / `perm_tally`. Not changed: the spec slot / part-size mapping (`assy_spec`, `assy_params`, `assy_vent_spec`): their options are number ids listed in text order with quotes (that order is information, not a menu position). | controller-information | `assembly.py` |
| 3 | **Permutation voting**: one call per ordering (`menu_orderings` 3 × `menu_samples` 1 = R01's 3 calls; 2 for a two-option menu); winner = most votes (a tie goes to the first ordering's answer); confident only when ≥ `menu_min_valid` (2) valid answers agree at ≥ `menu_consistency_min` (1.0). The controller step records `orders`, every answer (ordering, position, reason), votes, consistency, confident; proposal choices record votes / consistency / confident (`stack[...]`, `archetype`, `arrangement_confirmed.class_vote`, `arrange.edge_vote`, `arrange.relations.orders`). Inconsistent controller votes go to search (5); an inconsistent proposal choice is recorded (low confidence) and stays the controller's to correct. | controller-information | `menus.py`, `controller.py`, `assembly.py`, `design_rules.json` |
| 4 | **No LLM probability as a gate**. Audit of every p_yes / yes-no confidence use in assembly.py, controller.py and layout.py: the only decision use was ArrangeContents' p_yes ranking of the error-tied arrangement classes (with no valid edge vote, the top p_yes class was accepted alone; otherwise p_yes chose the challenger for a lettered A/B pick) plus the `EVEN_ODDS` low-confidence assumption. Replaced by one content-keyed, permutation-voted menu over the classes (`assy_arrange`, `ArrangeContents.decide`): vote and menu agree → `llm:vote+menu`; a consistent menu overrides the vote → `llm:menu`; an inconsistent menu leaves the vote → `llm:vote` (with an assumption); no valid answer → `rule:first_option[arrange]`; one class → the vote, else `rule:symmetric_class`. `EVEN_ODDS` is gone. Kept as they are: `QuestionCache.p_yes` / `StubController.p_yes` (interface forwarding, no decision); the Contents yes/no exposure (a vote count, not a probability; the text_coverage sensor corrects it); the relation unanimity rule (agreement across orderings). Out of scope and unchanged: default-mode `cad_agent.Verify` (`yes_score > 0.5`) and cascade.py's p_yes ranking (not assembly mode). No Platt mapping was fitted: the logged labelled decisions (12, all with a correct sensor action) cannot fit a calibration; agreement across orderings is the confidence. | sensor-side cleanup (nothing new to measure), controller-information | `assembly.py` |
| 5 | **Verifier-guided search** (best-of-N, depth 1): candidates = every voted action (most votes first) plus, when the vote is not confident, the next-ranked alternatives, at most `controller_search_k` (3), with at most `controller_search_max_evals` (12) plant evaluations per run (the top candidate is always measured). Each is applied on its own fork (`evaluate`: fork the checkpoint, re-apply the kept actions, apply, re-run, manifold build, sense). Among the candidates `accept` keeps (and a `stop` candidate, scored at the current error) the lowest `(hard failures, violation)` wins; the vote ranking breaks ties. A confident `stop` ends the loop. A winner no vote named is recorded `search:controller` (classified guardrail). Undone / infeasible candidates are tabu; an acceptable loser stays on the menu. `controller_search_depth` > 1 is clipped to 1 (lookahead not implemented). | guardrail (error-based selection), plant (forks), controller-information (trace) | `controller.py`, `design_rules.json` |
| 5 | **Trace schema 2** (`controller_trace.json`): per step `state_before` + `state_summary`, `error_before`, `terms_before`, `menu` (with ids), `orders`, `vote` (answers with reasons), `chosen`, `candidates` (votes, rank, outcome kept / not_selected / undone / infeasible / stop, `error_after`, `failing_after`, `state_after`, `sensor_delta`, secs), `selected`, `selected_by`, `outcome`, `evals`; trace header `vote_rules`, `search`, `evals`. | controller-information | `controller.py` |
| — | **F5**: a re-run stage or build failure of any exception type makes the action infeasible (AssertionError, a scripted test's unexpected question, still propagates). This caught a real bug during development (a TypeError in `Action.from_dict` showed up as "infeasible"), so the reason text keeps the exception type. | plant (robustness) | `controller.py` |
| — | **Registry**: `rule:first_option` split per site (`[stack]` R05, `[arrange]` R06, `[archetype]` R07); new `rule:symmetric_class` (plant); reclassifications (section 4); `rule:text_evidence[stack]` moved to R05; ARCHITECTURE.md 10.8: R02 row replaced by this delta, the stack conversion folded into R05. | registry hygiene | `controller_rules.json`, `ARCHITECTURE.md` |
| — | `design_rules.json`: `menu_orderings` 3, `menu_samples` 1, `menu_consistency_min` 1.0, `menu_min_valid` 2, `controller_search_k` 3, `controller_search_depth` 1, `controller_search_max_evals` 12 (each with a source). | plant (generic values) | `design_rules.json` |
| — | `test_no_hardcoding` and `test_controller_authority` scan `menus.py`. RUN.md section 2 runs `test_menus`. | guardrail on the development loop | tests, `RUN.md` |

No change is a semantic rule. Nothing reads the request text to decide a meaning; the seed material hashes the
request only to vary the orderings reproducibly.

**StubController** (documented in its docstring): every schema enum stays in Python's unshuffled enumeration order,
so the stub's "first offered option" is the first option of Python's enumeration under every shuffle: the same
no-information baseline as R01 (`test_menus.TestOrderings.test_stub_takes_pythons_first_option_under_every_shuffle`).

## 4. Registry re-audit (rules that decide meaning)

Honest classification, not migration. Reclassified **plant → semantic-rule (pending_migration)**:

| Name | Why it decides meaning | Delta |
|---|---|---|
| `rule:first_option[stack]` (was `rule:first_option`) | no valid stack answer → Python's first option decides the mounting | R05 |
| `rule:first_option[arrange]` (new site, R02) | no valid edge vote and no valid class answer → Python's first class decides which edges the ports face | R06 |
| `rule:first_option[archetype]` (was `rule:first_option`) | no valid answer / scratch run → Python's first archetype decides the form (unreachable while one archetype is offered) | R07 |
| `rule:catalogue_default` | applied exactly when the stack word test finds nothing, so it decides the mounting for any wording the list misses; no sensor or actuator | R05 |
| `rule:default_closure` | the controller is only offered `set_closure` when the closure word list fires (F1: 4 of 4 reworded rebate sentences got no question), so the default decides the form | R07 |
| `rule:largest_complete_screw` | the default lid screw whenever the lid word test misses; no sensor or actuator | R03 |
| `rule:smallest_thread_through_board_hole` | the default board screw whenever the board role word test and the datasheet give nothing; the fit is a guardrail, "smallest" is a choice | R03 |
| `rule:primary_reference` | reads no text, but decides which part carries the others (a non-carrier primary leaves the rest unplaced) with no actuator to correct it | R05 |

Kept **plant** after checking the code: `rule:no_exposed_connector` (with no exposed connector the candidate list is
`[{}]`, one placement: nothing is chosen), `rule:interface_thread` (the board's datasheet thread), `rule:default_layout_passes`
(the plant's own error), and the derivation rules. New: `rule:symmetric_class` (plant: the survivors are one design up
to the board's symmetry, equal error). After R02 the registry has 32 names in the code: 15 plant, 4 guardrail, 13
semantic-rule pending migration (R03 ×4, R04 ×1, R05 ×4, R06 ×1, R07 ×3 — `rule:only_feasible`, `[archetype]`,
`default_closure`), and 5 retired (R01's four plus the per-site split of `rule:first_option`). The live E1-01 run's authority audit shows what this means: 6 of its 12 recorded
decisions are now (honestly) semantic-rule decisions, where R01 counted them as plant.

## 5. Tests

New `test_menus.py` (18): orderings (deterministic, every option leads once with K = N, two options → two orders,
more seeded permutations when K > N); schema (reason first, enum canonical); the stub takes Python's first option
under every shuffle; the controller prompt is content-keyed, shuffled, reproducible, letter-free, with `orders` and
reasons in the trace; the edge vote and the Contents candidates are shown in several orders; the stack menu is
content-keyed with consistency; permutation voting (a position-biased fake splits its votes and is not confident, a
content-following fake is unanimous and confident; a tie goes to the first ordering; letters are invalid; thresholds
from the rules); `perm_tally` per-key consistency; no p_yes call in assembly.py / layout.py / controller.py outside the
forwarding wrappers (AST scan); an E1-01 run whose fake raises on p_yes designs; `ArrangeContents.decide` (vote+menu,
menu overrides a vote when consistent, an inconsistent menu leaves the vote, first-option fallback, symmetric class);
search (a position-biased controller's inconsistent vote is searched and the measured best kept, with the complete
training record; on G02 an injected failure on the closure fork makes the measured error override the vote ranking:
`expose:board.dc` kept over the 2-vote `set_closure:rebate`, `selected_by` `search_among_votes`; the eval budget and the
confident-only candidate set; depth clipped; `search:controller` is a guardrail decision); a new action kind plugs in
through `APPLIERS`; the audit's replay (decision extraction, the planted action, a position-biased fake scores
first-position 1.0 and picks the plant at A, a content fake is consistent and never picks the plant).

Changed on purpose (each marked "migration delta R02" in the file):
- `test_controller.py`: `assy_control` scripted with ids (`expose:module_1.usb`, `stop`) instead of letters; prompt
  assertions on content-keyed lines; two calls (two orderings) for an expose + stop menu; feedback line wording.
- `test_assembly.FakeLLM`: an unscripted `assy_arrange` answers its first enum entry (Python lists the classes in vote
  order, so the vote's class comes first, as when every class had equal p_yes); `RankedLLM` answers it with the class
  its recorded p_yes table scores highest.
- `TestArrange` (iter003 replay by rank → `llm:vote+menu`, high confidence, no low-confidence assumption; symmetric
  classes: one menu, one call per ordering; the comparative A/B pick rewritten as the class-menu cases; the p_yes "no"
  veto test without p_yes; prescore ties `llm:vote+menu`), `TestReplayIter003/004`, `TestFaceRelation` (`vote+menu`;
  the split relation vote is 1:1 over two orderings), call counts of two-option menus (stack, owner, controller,
  relation, vent relation: 2), T2 and T11 compare prompts up to line order (`same_question`).

Full RUN.md section 2 suite: see section 7.

## 6. Live end-to-end (E1-01, fresh seed 21)

`cad_agent.py --mode assembly --auto --seed 21 --num-ctx 8192` on E1-01 (inputs `iter_005/inputs/E1-01.*`, the
enclosure RUN.md `run_one` command, output `iter_R02/live/E1-01_s21/20261025-130053/`): **rc 0, verified, 94/94
checks pass on the delivered STLs**, 21 LLM calls, 108 s. Canonical STL hashes, the feature graph and the layout are
identical to iteration 005's E1-01_s5 package (base `90c88b8e1c90`, lid `a35daa99c30a`, graph `8b92655a7335`).
`controller_trace.json` (schema 2): initial error (1 hard, 1.0), failing `text_coverage` (the Contents vote again left
the Pico's USB closed); step 1: orderings `[stop, expose:module_1.usb]` and `[expose:module_1.usb, stop]`, both answered
`expose:module_1.usb` with a reason quoting L1.5, consistency 1.0, confident, one candidate measured (1 → 0 failing,
`sensor_delta` −1 / −1.0), kept, `selected_by` llm; stop "every check passes"; 1 plant evaluation. The arrangement: the
edge vote unanimous over 3 orderings for both items, relation `opposite` unanimous over 2 orderings, one surviving class
(`prescore+llm:vote`); no p_yes call anywhere.

## 7. Measured test counts

- Full RUN.md section 2 suite on the final R02 code (with `test_menus`): **510 tests in 1759 s, 509 pass, 1 error**.
  The error is `test_generalize_suite.TestLaunchConfig.test_commands_parse_and_cover_train_regression_stub_and_holdout`:
  another agent was adding the T01 target set (`launch_config.json`, `run_suite.py`, `test_generalize_suite.py`,
  `plan.json`, `designs/T01/`, RUN.md section 3) while the suite ran, and the launch config already named `--target`
  before the parser had it. `test_generalize_suite` re-run alone afterwards: **35 tests, OK**. R02 touches none of
  those files.
- In that run every R02-touched module passed: test_assembly 134, test_controller 18, test_menus 18 (new),
  test_controller_authority 8, test_no_hardcoding 3. R01's suite was 492; +18 test_menus = 510.
- Earlier on the final agent code: the 12 non-assembly modules 376 tests OK; the six changed test_assembly classes
  43 + the replay / vent classes OK after the test updates.

## 8. Risks and what was not done

- Contents, edge, relation and owner prompts are now shuffled per ordering, so live answers can differ from R01 runs
  on the same seed (the regression E1-01 at seed 21 came out identical; the train set was not re-run here). The judge
  cache keys on geometry, so unchanged geometry stays a hit.
- `menu_consistency_min` 1.0 makes any split vote low-confidence; with search that costs extra plant evaluations
  (bounded by `controller_search_max_evals`), not wrong decisions.
- Two-option menus get two calls (was three); the vote count of an expose + stop step is 2.
- The arrangement-class menu decides between error-tied classes only; when it is inconsistent the edge vote stands,
  so a wrong but stable edge vote is not corrected until R06 (`set_edge`).
- Not done: Platt calibration (too few labelled decisions; agreement is the confidence), depth > 1 lookahead, the
  default-mode / cascade p_yes gates (not assembly mode).
- An untracked `prints/` folder appeared in the repo root at 12:43 during this work; it is not from this delta and was
  left alone.

## 9. Revert

```sh
git checkout 4c7d496 -- assembly.py controller.py controller_rules.json design_rules.json test_assembly.py \
    test_controller.py test_controller_authority.py test_no_hardcoding.py benchmarks/generalize/loop/ARCHITECTURE.md
rm -f menus.py test_menus.py benchmarks/generalize/audit_controller.py
rm -rf benchmarks/generalize/loop/iter_R02
```

Then, by hand (these files were also edited by another agent during R02, so do not check them out): remove
` test_menus` from the unittest line in `loop/RUN.md` section 2, and the "R02" entry at the end of `loop/LEDGER.md`.

## Review fixes (2026-10-25)

Adversarial review of the uncommitted R02 + R11 changes (base `4c7d496`), fixed 2026-10-25. claude-context failed to
connect again (MCP server did not start), so files were found with targeted reads and grep. Nothing under the held-out
folders was opened; `benchmarks/heldout.json` and `.mcp.json` untouched; nothing committed.

- **B1 (blocking) infeasibility leaked into later forks' sensor typing**: `controller.run_loop` wrote
  `st.control["infeasible"]` inside the candidate loop, so later forks (copied by `fork_from`) typed text_coverage /
  closure_evidence as conflicts while `key` and `stop` did not; on G02 a rebate fork raising the violation by 1.0 was
  kept. Now every candidate forks from a pre-step snapshot (`fork_from(..., control)`, `evaluate(..., control=)`),
  infeasibility is collected locally, merged after the loop, and the current design (recorded as
  `error_before_retyped`) and every feasible fork are re-measured under the merged typing before `accept` and best-of-N.
  Test: `test_menus.TestSearch.test_infeasible_candidate_does_not_retype_later_forks` (the repro: rebate now `undone`,
  stop selected).
- **2 search budget**: `controller_search_max_evals` is a hard cap (`search_candidates` no longer guarantees one
  evaluation; the loop stops before asking once it is spent, reason "search evaluation budget spent"); a confident
  `stop` is the only candidate whatever `menu_consistency_min` is. Tests: `test_eval_budget_limits_the_candidates`
  (changed), `test_total_evaluations_never_exceed_max_evals`, `test_confident_stop_ends_the_loop_whatever_the_consistency_threshold`.
  design_rules.json source text and ARCHITECTURE.md 3a updated.
- **3 checks that could not fail**: `panel_hole` is measured on the built lid (cross-section at mid-thickness around the
  axis, nearest edge minus the through radius; runs on solids and STLs); retention free travel, snap strain, snap
  overlap and panel thickness are relabelled **design checks** (evidence `basis: design`; measured ones carry
  `basis: measured`). Tests: `test_building_blocks.TestSnapClips.test_panel_hole_is_measured_on_the_lid`, `test_value_sensors`.
- **4 tie rule**: `menus.decide` docstring now states the behaviour (earliest valid tied answer, ordering 0 first; an
  invalid answer is never a candidate); `perm_tally` moves the invalid (None) count last so `majority` never picks it
  on a tie. Tests: `test_tie_goes_to_the_earliest_valid_tied_answer`, `test_perm_tally_invalid_answer_never_wins_a_tie`.
- **5 stale param_stop**: reset after a rejected unsized part in `Contents.update`. Test:
  `test_assembly.TestNumberOwnership.test_rejected_part_does_not_leak_its_stop_reason`.
- **1b registry/docs**: `search:controller` in controller_rules.json `decision_tags` (test
  `test_every_decision_tag_the_controller_records_is_registered`); R11 section 3 row 2 re-classed as extending the
  pending semantic `rule:primary_reference` (R05), registry justification extended (documentation only);
  `bolt_m5_iso4762` already handles `length` parametrically like the other bolts (`from_request`, gate sample 16 mm), left
  as is; its tap-drill source text said M4, corrected to M5.
- **6 test quality**: `test_assembly.TestArrange.test_iter003_replay_menu_overrides_the_edge_vote` replays iteration
  003's answers with an arrangement-menu answer that differs from the edge vote's class: `llm:menu` decides.
- **Measured**: full RUN.md section 2 suite (15 modules) **544 tests, OK (1714 s)** (535 + 9 new). Offline regression
  (`scratchpad/regress.py`, fn 24, E1-01 / V1 / V2 / V3, exposed and closed-USB + scripted expose): feature graph,
  layout.json and canonical STL hashes identical to the merged tree (E1-01 graph 8b92655a7335, layout 4536c7e83718,
  STL 604a70a3c664).
