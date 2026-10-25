# Migration delta R01: the walking skeleton of the D1 controller

**Owner decision:** D1 (`../OWNER_DECISIONS.md`, 2026-10-25): the small local LLM is the controller; Python is the plant,
the sensors, the actuators and the guardrails. Target architecture and the whole migration plan:
`../ARCHITECTURE.md` section 10 ("Controller architecture (D1)"). This delta is R01 of that plan, implemented and tested
in this step (2026-10-25). claude-context failed to connect (the MCP server did not start), so files were found with
targeted reads and grep. Nothing under `../../holdout/` or `../holdout_results/` was opened, listed or searched;
`benchmarks/heldout.json` and `.mcp.json` were not touched; nothing was committed.

**Pre-R01 version:** iteration 004's code (`../iter_004/code_sha1.txt`, delta 003). `code_before/` holds the files
this delta changed as they were (see section 9). **Post-R01 version:** `46b9530eac79` (sha1 of the code listing
`run_suite.py` writes, 78 files: iteration 004's 76 plus `controller.py` and `controller_rules.json`); the next Run's
`code_sha1.txt` should hash to it.

---

## 1. Why: what the 9B decided, and what rules decided

Measured on the packages of iterations 002–004 (`design.json` `assembly.choices`):

- In 11 of the 12 regression runs (E1-01, V1, V2, V3 × three iterations) the Contents vote said the Pico's USB is
  *not* exposed (`no` 3/3 in ten, 1:2 in one; only iteration 002's E1-01 said yes), and `rule:text_coverage` overrode it
  (`overrides.contents_votes`). The design was right because a rule read L1.5 ("a micro-USB cable shall plug ...") and
  pre-empted the controller.
- G02 and G13 got their rebate lid from `rule:text_evidence[closure]` (a word match on "rebate" in a lid sentence).
- The board screw, the lid screw, the stack and the vent face are rule decisions from word matches; the structural form
  is gated by a word list (`archetypes.tray_lid.evidence`).

Each of these passes the judges on the wording it was written for. On a paraphrase ("the USB lead must reach the Pico
with the cover on") or a new family, a word rule fails silently. D1's fix is not more rules: the same knowledge becomes
a **sensor** whose reading the controller sees as a failing check, plus an **actuator** the controller can use.

## 2. Inventory of every `rule:*` decision (the registry)

`controller_rules.json` (repo root) registers every name the agent modules use, with class, status, sites and
justification. Scan: the AST of `assembly.py`, `assembly_checks.py`, `feature_graph.py`, `layout.py`, `parts.py`,
`controller.py`, `cad_agent.py` (string literals and f-strings; docstrings and comments excluded); a name is
`rule:<identifier>[<qualifier>]`. After R01: **29 names in the code** (20 plant, 4 guardrail, 5 semantic rules pending
migration) and 4 retired.

| Name | Class | Status | Sites |
|---|---|---|---|
| `rule:board_keepout` | plant | active | parts.py:board_keepout |
| `rule:bridge_roof` | guardrail | active | assembly.py:port_roof |
| `rule:catalogue_default` | plant | active | assembly.py:ChooseStack |
| `rule:cavity_from_contents` | plant | active | assembly.py:derive_cavity |
| `rule:closure` | plant | active | assembly.py:derive_features |
| `rule:column` | plant | active | parts.py:column |
| `rule:connector_to_cut` | plant | active | assembly.py:derive_port_cut |
| `rule:content_envelope` | plant | active | parts.py:content_envelope |
| `rule:default_closure` | plant | active | assembly.py:closure_choice |
| `rule:default_layout_passes` | plant | active | assembly.py:choose_boss_layout |
| `rule:first_option` | plant | active | assembly.py:ChooseStack, choose_archetype_rule |
| `rule:fixed_by_primary` | guardrail | active | assembly.py:ArrangeContents |
| `rule:hole_column_d` | guardrail | active | assembly.py:ArrangeContents |
| `rule:interface_thread` | plant | active | assembly.py:board_screw_choice |
| `rule:largest_complete_screw` | plant | active | assembly.py:lid_screw_choice, derive |
| `rule:lid_to_fastening` | plant | active | assembly.py:derive_features, add_corner_pilasters, add_inside_bosses |
| `rule:mount_hole_to_standoff` | plant | active | assembly.py:derive_features |
| `rule:no_exposed_connector` | plant | active | assembly.py:ArrangeContents |
| `rule:only_feasible` | **semantic-rule** | pending **R07** | assembly.py:choose_archetype_rule (the archetype text gate) |
| `rule:plug_sweep` | plant | active | parts.py:plug_sweep |
| `rule:prescore` | guardrail | active | assembly.py:ArrangeContents |
| `rule:primary_reference` | plant | active | assembly.py:Contents |
| `rule:smallest_thread_through_board_hole` | plant | active | assembly.py:board_screw_choice, ArrangeContents |
| `rule:text_evidence[board]` | **semantic-rule** | pending **R03** | assembly.py:board_screw_choice |
| `rule:text_evidence[lid]` | **semantic-rule** | pending **R03** | assembly.py:lid_screw_choice |
| `rule:text_evidence[stack]` | **semantic-rule** | pending **R02** | assembly.py:ChooseStack |
| `rule:tray_lid` | plant | active | assembly.py:derive_features |
| `rule:vent_row` | plant | active | assembly.py:add_vent_row |
| `rule:vent_zone` | **semantic-rule** | pending **R04** | assembly.py:Vents |
| `rule:text_coverage` | semantic-rule | **retired (R01)** | → sensor `text_coverage` + actuator `expose` |
| `rule:coverage_infeasible` | semantic-rule | **retired (R01)** | → an infeasible `expose` is rejected; the sensor is typed a conflict |
| `rule:text_evidence[closure]` | semantic-rule | **retired (R01)** | → sensor `closure_evidence` + actuator `set_closure` |
| `rule:text_evidence` | semantic-rule | **retired (R01)** | renamed per site: `[stack]`, `[lid]` |

Classification notes (the judgement calls a reviewer should check):
- `rule:primary_reference` is **plant**: it picks the datum frame from part data (carrier, else the largest plan
  footprint) and reads no text; what is in the design is the controller's answer. A `set_primary` actuator comes with
  GM2b relations.
- `rule:only_feasible` is **semantic**: the name only says "one archetype was feasible", but feasibility includes
  `archetype_gate`'s word test, so the form is decided by reading the text. R07 retires the gate.
- `rule:prescore`, `rule:hole_column_d`, `rule:bridge_roof`, `rule:fixed_by_primary` are **guardrails** (error-based
  acceptance, driver access, printability, physics).
- Defaults that read no meaning (`rule:catalogue_default`, `rule:default_closure`, `rule:largest_complete_screw`,
  `rule:smallest_thread_through_board_hole`, `rule:interface_thread`, `rule:first_option`) are **plant**: they are the
  proposal the controller corrects once the matching sensor exists.

## 3. The delta, every change classified

| # | Change | Class | Files |
|---|---|---|---|
| (a) | **The closed-loop controller** `controller.ControllerLoop`, wired into the assembly tree right after DeriveFeatures (the proposal's first, manifold-only build). Sense → one voted menu question (`assy_control`) → apply on a fork → re-run the invalidated stages → rebuild on manifold → keep only when the controllable error does not rise beyond the trust region → feed back → repeat; stop when nothing actionable fails, on `stop`, or at the budget. OpenSCAD runs once afterwards (Build). Never fails the tree. | controller-information (prompt, menu, feedback), actuator (application), guardrail (acceptance), plant (re-run) | `controller.py` (new), `assembly.build_assembly_tree` |
| (a) | **Stage checkpoints**: ChooseStack, ArrangeContents, Vents, BuildEnvelopes, ChooseArchetype and DeriveFeatures snapshot the state at entry (`assembly.snapshot` / `checkpoint`). An action forks the checkpoint of the stage it invalidates and re-applies every kept action, so no record of a discarded downstream pass (votes, notes, assumptions, number ownership) leaks. | plant | `assembly.py` |
| (a) | **One question, one answer per run** (`controller.QuestionCache`, wrapped round the controller in `build_assembly_tree`): a question asked again with the same label, prompt, schema and sampling gets its first answer with no LLM call. A stage re-run after an action asks such questions (the vent size mapping after an `expose`); the seeded 9B gives the same answer to the same prompt, so no decision changes and calls are saved. | plant (memoisation of the controller's own answers) | `controller.py`, `assembly.build_assembly_tree` |
| (a) | **Trajectory logging**: `controller_trace.json` in every package (initial and per-step state digests, error keys, failing checks, menu, votes, choice, kept/undone/infeasible with the reason, LLM calls, seconds; stop; final; kept actions) and the **authority audit** (every `st.choices` decision classified through the registry, plus the proposal questions' answers: slots the LLM mapped, rules defaults, content items; `llm_share`; the semantic-rule decisions with their migration delta); `design.json` `assembly.controller` and `assembly.control`. | controller-information | `controller.py`, `assembly.WritePackage`, `AssemblyState.summary` |
| (b) | **Error-vector sensors from the existing checks**: `controller.error_vector` turns failing `CheckResult`s into typed terms (check, type, requirement = L1 links, where, deficit in mm or count, direction, controllable, actionable), ranked actionable → controllable → conflicts, worst margin first; `error_key` = the controllable error (conflicts excluded, as in 7.11). `trace_links` also reads a text sensor's quoted L1 sources. | sensor, controller-information | `controller.py`, `assembly.trace_links` |
| (c) | **text_coverage converted**: `ExposureCoverage` becomes a sensor stage (rows `resolved: open`, nothing exposed); the `text_coverage` check is controllable (a `coverage` conflict only when every `expose` action was infeasible); actuator `expose(item.connector)` (`assembly.expose_connector`, invalidates arrange). `rule:text_coverage`, `rule:coverage_infeasible` and `ArrangeContents.revert_coverage` are gone. | sensor + actuator (semantic rule retired) | `assembly.py`, `controller.py` |
| (c) | **closure converted**: `closure_choice` returns the controller's decision or the default (`rule:default_closure`); the text's closure words are the new `closure_evidence` sensor (graph data, controllable; only added when a lid sentence names a buildable closure, so other plans are unchanged); actuator `set_closure(name)` over `assembly.buildable_closures` (invalidates derive). `rule:text_evidence[closure]` is gone. When every named closure is infeasible (no inside boss layout fits a rebate), `closure_evidence` is typed as a `closure` conflict; such a text now gets a package with that conflict, where until R01 the rebate rule made derive fail and left no package (delta 003 review N1). | sensor + actuator (semantic rule retired) | `assembly.py`, `assembly_checks.py`, `controller.py` |
| (c) | The shared `rule:text_evidence` is split per decision site: `rule:text_evidence[stack]` (ChooseStack), `rule:text_evidence[lid]` (lid screw), each registered with its own delta. | registry hygiene | `assembly.py` |
| (d) | `controller_rules.json` (registry, read at run time for the authority audit) and `test_controller_authority.py` (every `rule:*` in the code registered; classes and statuses valid; a semantic rule in the code only as `pending_migration` with a delta id from ARCHITECTURE.md 10.8; active names in the code, retired names not; runtime canonical names agree). | guardrail on the development loop | new files |
| (e) | `cad_agent.py --controller {llm,stub}`: `controller.StubController` answers every schema question with its first offered option, every p_yes with 0.5, takes no corrective step and makes no network call; no `OllamaAgent` is created. Assembly mode only. | controller-information (authority probe) | `cad_agent.py`, `controller.py` |
| (f) | `run_suite.py --paraphrase K` (0 = design.json, K = paraphrases.json entry K; train strict, held-out falls back quietly, regression ignores it; recorded in `runs.jsonl` `paraphrase`, `summary.json` `paraphrase`, and the judge-cache key `|p<K>` for K > 0) and `--controller stub` (rows `<id>_sS_stub`, never judged, `counts.train_stub`); `summary.json` `stub_verified`, `llm_dependent`, `stub` {verified, compared, same_geometry, verified_share} and `controller` (steps, kept, decisions by class, semantic-rule decisions summed from each package's trace); rows carry `controller_run` and `authority`; `code_sha1.txt` covers `controller_rules.json`; `build_parser()` factored out; a stub run's preflight checks only that no other agent runs (it needs no Ollama); `cache_verdicts.py` keys by paraphrase, refuses stub rows and lets a bare design id name only the judged run. | plant (Run tooling) | `benchmarks/generalize/run_suite.py`, `cache_verdicts.py` |
| (g) | `loop/launch_config.json`: `commands` = train `--paraphrase {para}`, regression, stub train `--paraphrase {para} --controller stub`; `holdout_commands` = held-out `--paraphrase {para}`. | plant (Run tooling) | new file |
| — | `design_rules.json`: `controller_step_budget` 6, `controller_trust_region` 0.05, `controller_error_terms` 6, `controller_menu_max` 8 (each with a source). | plant (generic values) | `design_rules.json` |
| — | `test_no_hardcoding` scans `controller.py` too. | guardrail | `test_no_hardcoding.py` |

No change in R01 is a semantic rule. Two judgement calls for the reviewer: the closure sensor reuses the retired rule's
gate (one sentence with a closure word and a lid word) as its *reading* — D1's own example converts
`rule:text_coverage` the same way — and the unit-test fake answers an unscripted controller question with the first
offered action (a test convenience, documented in `test_assembly.FakeLLM`; the controller's own tests script it).

## 4. How the controller sees a design (example from the live run)

The live E1-01 run (ornith-1.5:9b, seed 4, run_suite's exact regression command): the Contents vote left the Pico's
USB closed (as in 11 of the 12 regression runs of iterations 002–004), the first manifold build failed `text_coverage`, and the
controller was asked once (`llm/015-017_assy_control.txt`):

```
Request: An enclosure for a 70 x 50 mm perfboard that will hold a Raspberry Pi Pico 2 CW radio keyer. ...

The design was built and measured. Requirements that fail now (worst first):
1. text_coverage (L1.5, L1.6): module_1.usb (raspberry pi pico 2) is closed, but L1.5 names a micro-usb plug: "With the
   lid closed, a micro-USB cable shall plug fully into the Pico through one opening in its end wall without touching the
   enclosure, and that opening sh..."; needs: an opening for each connector whose mating plug the text names

The design now:
- board (primary): perfboard x1
- module_1: raspberry pi pico 2 x1; connectors: usb closed
- connector_1: 3.5 mm jack x2; connectors: jack open through +X
- lid closure: lip; lid bosses: outside_corners

Actions you can take now (one per step; Python applies it, rebuilds and measures again):
- A: expose module_1.usb: open the enclosure wall for the raspberry pi pico 2's usb connector so a micro-usb plug plugs
  in with the enclosure closed
- B: stop: keep the design as it is (the failing requirements above stay failing)

Which one action makes the design do what the request asks? Answer with its letter.
```

Votes A 3/3. Python re-ran the arrangement from its checkpoint with the USB exposed (the edge vote and the relation
question with both connectors, iteration 004's prompts), rebuilt on manifold, measured 1 → 0 failing checks, and kept
it (21.3 s, 10 LLM calls for the step). On G02 the second step's menu was `A: set the lid closure to rebate: a flat
plate that drops into a rebate in the top of the walls, flush with the upstand` / `B: stop`, with the first step's
feedback line `step 1: A (expose board.dc) was kept: fewer failing checks (2 -> 1)`.

## 5. Tests

New:
- `test_controller.py` (18): the error vector of a named plug on a closed connector (requirement, where, quote, deficit,
  direction, key); ranking and millimetre deficits, conflicts uncounted; the trust region; a kept `expose` traced end to
  end (prompt, choice record with step and votes, coverage row, `design.json` controller block, trace steps, digests,
  authority audit with the R07 archetype rule); `stop` leaves the failure visible and controllable; an infeasible
  `expose` is rejected, tabu, and types `text_coverage` as a coverage conflict; a step that raises the error is undone
  and the design is unchanged; the budget; feedback in the next prompt and tabu in the menu; checkpoints (the fork starts
  at the stage entry, the state and the checkpoint stay untouched); the closure sensor's reading (regression, G04, G11:
  none; G02, G13: rebate; a rebate word without a lid word: none); the rebate by the controller on G02; a rebate no
  inside boss layout fits becomes a typed closure conflict in a written package (delta 003 review N1); the question
  cache answers a repeated question once and delegates everything else; the stub's first
  offered option, no corrective step, no LLM agent from the CLI (stops at Contents), `--controller stub` refused outside
  assembly mode; **regression invariance** (E1-01: the controller's exposure gives the very feature graph and layout of a
  run whose Contents exposed it).
- `test_controller_authority.py` (8): the scanner is not vacuous (docstrings, comments and "rule: " are not names;
  f-string constants resolve); runtime names agree; every rule in the code registered; entries classified and justified;
  no active semantic rule; registry matches the code; R01 conversions retired; the agent reads the registry.
- `test_generalize_suite.py` (+9): paraphrase cases (entry K, train strict, held-out fallback, regression ignores),
  runs record the paraphrase and key the cache (a p0 run of the same geometry is not a hit; p0 keys unchanged), stub rows
  named apart and never judged (cache_verdicts refuses them), `stub_verified` / `llm_dependent`, same geometry is not
  LLM-dependent, the stub run's preflight needs no Ollama, `launch_config.json` commands parse with
  `run_suite.build_parser()`, the code listing covers the registry.

Changed on purpose (each marked "changed in migration delta R01" in the file):
- `test_assembly.FakeLLM`: an unscripted controller question takes the first offered action (the corrections of the
  worst actionable failure come first, stop last), so scripted runs get the correction the retired rules made.
- `test_assembly.CycleReplies` / `cycled` (new helpers): a real run's recorded replies are replayed per question, so a
  question the controller makes a stage ask again (the edge vote once the Pico is exposed) gets the recorded samples
  again (`recorded_llm`, `iter003_answers`, `regression_replay`, the V1 relation replay).
- `staged_to_derive` runs through `ControllerLoop` by default (exposure and the closure are the controller's).
- Rule names per site: `TestContents.test_stack_evidence_gate`, `test_v3_socket_stack_and_request_sized_part`,
  `TestReplayIter007` (`rule:text_evidence[stack]`); `TestLidFastener.test_named_fastener_wins`,
  `test_shared_alias_is_not_a_skip` (`rule:text_evidence[lid]`).
- The controller decides what the retired rules decided: `TestReplayIter007`, `TestReplayIter008`
  (`exposed[...]` by `llm:controller`, one voted `assy_control` question), `TestExposure.test_primary_connectors_and_
  multi_connector_parts` (two expose steps, staged through the controller), `TestCardExposure`, `TestRebate`
  (`closure` by `llm:controller`; T7 reads the sensor, `closure_text_evidence`, and the proposal keeps the lip).
- `TestContents.test_coverage_infeasible_is_reported` rewritten: the expose action is infeasible, rejected and tabu;
  `text_coverage` is typed as a quoted coverage conflict (was: `rule:coverage_infeasible` reverts a forced exposure).
- `TestBossLayout.test_default_kept_when_passing` (T4): two derivations (the proposal and the controller's fork), both
  boss-affected checks only, and iteration 003's feature graph exactly.
- `TestVents.test_prompts_unchanged_without_vent_words` (T11): no vent question, every question iteration 003 recorded
  asked again with the same prompt, extras only the first pass's arrangement questions and the controller's.
- `test_no_hardcoding`: `controller.py` is scanned too.
- `test_generalize_suite` fake agent: `--controller stub` gives other geometry, `STUBFAIL` a stub stop.

Full suite (RUN.md 2, now with `test_controller test_controller_authority`): **492 tests, OK (1658 s)** on the R01 code (457 before R01 + 9 tooling + 18 controller + 8 authority), `test_no_hardcoding` green with `controller.py` scanned; the four modules edited after that run started (`test_controller`, `test_controller_authority`, `test_generalize_suite`, `test_no_hardcoding`) re-run on the final files: 62 tests, OK.

## 6. Measured

**Offline (no Ollama, fn 24, `scratchpad/r01/smoke2.py`; the same as `test_controller.TestRegressionInvariance` for
E1-01).** For each regression text, a run whose Contents answer leaves the Pico's USB closed (the 9B's real answer) and
whose controller exposes it, against a run whose Contents answer exposes it (the path `rule:text_coverage` forced
before R01):

| Text | rc (yes / no) | Feature graph sha1 | Canonical STL sha1 | layout.json references | Controller questions |
|---|---|---|---|---|---|
| E1-01 | 0 / 0 | 8b92655a7335 = 8b92655a7335 | 604a70a3c664 = 604a70a3c664 | equal | 0 / 3 |
| V1 | 0 / 0 | d3f0568e3724 = d3f0568e3724 | bf2c1ab4b7a3 = bf2c1ab4b7a3 | equal | 0 / 3 |
| V2 | 0 / 0 | b28b47d23080 = b28b47d23080 | 36b8057cffcc = 36b8057cffcc | equal | 0 / 3 |
| V3 | 0 / 0 | a74bb4efb7b2 = a74bb4efb7b2 | f5a168cb9fdf = f5a168cb9fdf | equal | 0 / 3 |

**Live, regression set** (ornith-1.5:9b, seed 4 = iteration 004's seed, run_suite's exact command into
`scratchpad/r01/live/`, `scratchpad/r01/live_regression.py`):

| Text | rc | Controller | Canonical geometry vs iteration 004's judged package | Secs (iteration 004) |
|---|---|---|---|---|
| E1-01 | 0 | 1 step: `expose module_1.usb`, A 3/3, kept (1 → 0 failing) | **identical** (judged MEETS) | 94.8 (81.7) |
| V1 | 0 | 1 step: `expose module_1.usb`, A 3/3, kept (1 → 0) | **identical** (MEETS; "same short end" kept through the re-run relation question) | 98.6 (86.5) |
| V2 | 0 | 1 step: `expose module_1.usb`, A 3/3, kept (1 → 0) | **identical** (MEETS) | 103.0 (92.8) |
| V3 | 0 | 1 step: `expose module_1.usb`, A 3/3, kept (1 → 0) | **identical** (MEETS) | 103.2 (92.5) |

So the first iteration on R01 code should find all four regression packages as judge-cache hits. The extra 11–13 s
per run are the controller step and the first-pass arrangement (and CPU shared with a unit-test run during the
measurement).

**Live, train designs** (seed 3 = iteration 003's seed, wording 0, both catalogues, `scratchpad/r01/live_train.py`):

| Design | rc | Initially failing | Controller steps | Finally failing | Secs (iteration 003) |
|---|---|---|---|---|---|
| G02 | 0 | text_coverage, closure_evidence | `expose board.dc` A 3/3 kept (2 → 1); `set_closure rebate` A 3/3 kept (1 → 0) | none | 117.0 (70.9) |
| G04 | 3 | bridge_board_hdmi_cut (typed conflict) | none (the Contents vote exposed every named connector) | bridge_board_hdmi_cut (accepted by G04's requirements, delta 003) | 60.5 (58.0) |
| G13 | 3 | text_coverage, closure_evidence, bbox | `expose module_1.usb` A 3/3 kept (3 → 2); `set_closure rebate` A 3/3 kept (2 → 1) | bbox (Z), grid_conformance (conflict): as delta 003 recorded for G13 | 97.3 (91.7) |
| G50 | 3 | content_placed_display_1, vent_placed | none (no actuator until R04 / R05) | the same; geometry identical to iteration 003/004 | 64.3 (63.8) |

**Live, paraphrase 2** (seed 5, wording K = 2: what iteration 005 runs; `scratchpad/r01/live_train.py 5 004 2`):

| Design | rc | Initially failing | Controller steps (menu letter, votes, action, outcome) | Finally failing | Secs |
|---|---|---|---|---|---|
| G02 | 0 | text_coverage (usb and dc closed), closure_evidence | C 2:1 (D = stop) `set_closure rebate` kept (2 → 1); A 3/3 `expose board.usb` kept (coverage violation 2 → 1); A 3/3 `expose board.dc` kept (1 → 0) | none | 101.8 |
| G13 | 3 | text_coverage, closure_evidence, bbox | A 3/3 `expose module_1.usb` kept (3 → 2); A 3/3 `set_closure rebate` kept (2 → 1) | bbox (Z) | 95.5 |

Across the live runs the controller was asked 13 times (39 samples: 4 regression, 4 train on wording 0, 5 on wording 2):
38 samples chose the correction and 1 chose stop (outvoted 2:1 on G02's first, four-option menu). The paraphrases keep
the technical words ("rebate", the plug names), so both text sensors read all three wordings of G02 and G13 the same;
the next Run measures the other 38 designs' wordings.
With the question cache a correction step on a primary's own connector costs about 4 s and 3 LLM calls (G02 p2).

**Stub probe** (`cad_agent.py --controller stub`, E1-01): rc 1 at Contents in 0.1 s ("nothing to design around": every
quantity's first offered option is 0); 15 transcripts, all marked STUB, no Ollama agent created.

## 7. Expected effect on the next Run (the first iteration on R01 code)

- **Regression set: pass, judge-cache hits** whenever the 9B picks `expose` for the Pico's USB (offline byte-identical
  on all four texts; live see section 6). The packages differ from iteration 004's only in records (`design.json`,
  `controller_trace.json`, transcripts), which the cache key does not cover.
- **Train**: no capability is added, so verdicts move only where the controller now decides: G02 and G13 (rebate via
  `set_closure`, and the plugs their Contents vote leaves closed via `expose`, when they reach DeriveFeatures; seed
  variance at Contents is unchanged), and any design whose Contents vote leaves a named connector closed. Expected
  MEETS/CORRECT unchanged within seed variance (iteration 004: 0 / 0 train; G04 CORRECT 0.99 in iteration 003); on
  wording 2 every train package is judged anew (no cache hit across wordings).
- **Authority, measured for the first time**: `stub_verified` 0 (the stub stops at Contents, section 8); the audit
  shows, per train run, how many decisions are the LLM's and how many are the 5 pending semantic rules'.
- **Disturbance**: the next iteration runs wording K = iteration mod 3; a p1/p2 run is judged on its own.

## 8. Known limitations and risks (deferred)

- **The stub is degenerate at R01.** "The first offered option" of every Contents quantity is 0, so the stub stops at
  Contents on every design: `stub_verified` = 0 and `llm_dependent` = every design with LLM geometry. This is a true
  reading (the LLM alone decides the contents) but the probe cannot see the rules further down. Until R05 (Contents as a
  proposal plus corrections, with the quantity enums offered in Python's proposal order, which the 9B never sees), the
  per-run authority audit is the measurement of those rules. Do not read `stub_verified ≤ 25%` as met by merit before
  R05.
- **The controller is asked only when an actuated sensor fails** (text_coverage, closure_evidence). Every other
  failing check is shown as context but offers no action until its delta (R02–R08) or GM milestone adds one.
- **A sensor's reading can be wrong** (a word match). The controller may answer `stop`; the failing check then stays
  in the package, honest. A rejected or declined correction is in the trace for the gap analyst.
- **Live 9B behaviour** is measured on 6 designs so far (13 questions, section 6), two of them on a paraphrase; the
  next Run measures all 40 train designs on wording 2. Risk: a 9B position bias toward the first option would
  over-pick corrections; acceptance by error bounds the damage (an action that raises the error is undone).
- **Cost**: an `expose` step on a content part re-runs the arrangement (its edge vote, relation question, p_yes ranking
  and prescore) and the plant: 21 s live on E1-01; on a primary's own connector, or a closure step, about 4 s (the
  question cache answers the re-run's repeated questions). The budget of 6 keeps a run well inside 20 minutes.

## 9. Files changed

Line counts against `code_before/` (which reproduces iteration 004's code exactly: all 76 files of
`../iter_004/code_sha1.txt` match by sha1). To revert, copy `code_before/` back over the repo and delete the new files.

| File | + / − lines | Why |
|---|---|---|
| `controller.py` | new (804) | (a) loop, checkpoints use, error vector, actuators, trace, authority audit, question cache, stub |
| `controller_rules.json` | new (94) | (d) the registry |
| `assembly.py` | +207 / −109 | (a) checkpoints, snapshot, tree, trace file, summary; (c) coverage sensor + `expose_connector`, closure sensor + decision, coverage / closure conflict typing; rule names per site |
| `assembly_checks.py` | +16 / 0 | (c) `closure_evidence` check type |
| `cad_agent.py` | +23 / −8 | (e) `--controller {llm,stub}` |
| `design_rules.json` | +5 / −1 | controller budget, trust region, error terms, menu size |
| `benchmarks/generalize/run_suite.py` | +185 / −39 | (f) paraphrase, stub runs, summary fields, cache key, registry in the code version, build_parser, stub preflight |
| `benchmarks/generalize/cache_verdicts.py` | +9 / −4 | (f) paraphrase key, stub rows refused, a bare id names the judged run |
| `loop/launch_config.json` | new (11) | (g) |
| `loop/ARCHITECTURE.md` | +229 / −1 | section 10 (new); principle 1 and section 9 point at it |
| `loop/RUN.md` | +72 / −16 | the three commands, launcher config, paraphrase, stub, summary fields, trace, unit-test line |
| `test_controller.py` | new (390) | the loop's tests (18) |
| `test_controller_authority.py` | new (197) | (d) (8 tests) |
| `test_assembly.py` | +107 / −50 | the changed tests above |
| `test_generalize_suite.py` | +152 / −1 | paraphrase, stub, launch config, registry in the code version |
| `test_no_hardcoding.py` | +2 / −1 | scans `controller.py` |
| `loop/iter_R01/` | new | this file, `code_before/` |

## 10. Assumptions (derived, not asked)

- Step budget 6 (uncertainty medium): one correction per named connector of the largest train contents (4) plus a
  structural correction and a spare; the next Run's traces recalibrate it.
- Trust region 0.05 mm-equivalent (uncertainty low; it only keeps sideways moves, never an extra failing check).
- 6 error terms and 8 actions per prompt (uncertainty medium; from the 9B's measured preference for short enum
  questions).
- The seeded 9B answers the same prompt the same way, so the question cache changes no decision (uncertainty low:
  iteration 003's ten restarted runs gave identical geometry hashes, and every live re-run arrangement here reproduced
  iteration 004's packages).
- No owner questions.
