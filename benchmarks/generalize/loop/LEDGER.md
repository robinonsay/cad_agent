# LEDGER: generalization control loop

This ledger has one entry per iteration, newest at the bottom, and is append-only. Do not rewrite past
entries. If an entry was wrong, add a correction note in the next entry.

The loop drives the CAD agent from the converged enclosure family (`benchmarks/enclosure/loop`) to the 40
train designs in `../designs/`. The target is `ARCHITECTURE.md`, and the Run procedure is `RUN.md`.

Each iteration works like this:

1. **Run**: `run_suite.py` runs the local-LLM agent on the train split and on the regression set (RUN.md 3).
   This is the only step that uses Ollama.
2. **Judge**: capable models, never the local model, grade each package in `summary.json` `to_judge` blind,
   against the design's requirements.md and `../rubric.md`. Verdicts go into the judge cache
   (`cache_verdicts.py`, RUN.md 5). A cached verdict (same design, same STL bytes, same spec files) is not
   re-judged.
3. **Gap analysis**: a new agent maps defects to missing sensors, generic rules, catalogue errors or
   controller errors, and to milestones GM0–GM10 of `ARCHITECTURE.md`.
4. **Delta design and implementation**: generic rules only. No per-design code, `test_no_hardcoding` green,
   the full suite green.
5. **Review**: a reviewer approves or rejects the delta, and rejects any change worded for one design.

Stop condition: ARCHITECTURE.md section 9.

Held-out isolation: the held-out column holds one number (the held-out CORRECT share from an isolated run,
RUN.md 6). Nothing else about the held-out designs is ever written here.

---

## Progress table (one row per iteration; append as you go)

| Iter | Seed | Code SHA (12) | Code unchanged | Train runs | Train MEETS | Train CORRECT | Train no-output | Regression | Held-out (last) | Milestone reached | Tests | Review |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 000 | — | — | — | not run | — | — | — | not run | — | GM0: loop tooling (repeatable `--parts`, run_suite.py, judge cache, cache_verdicts.py) | see entry | pending |
| 001 | 1 | 72dbcfdfb8de | — (first) | 40 | 0 | 0 | 40 | pass (E1-01/V1/V2 MEETS, V3 CORRECT 0.99; not yet in the cache) | — | GM1 baseline (gate clean; guards b/c folded into delta 001); delta 001 = GM2a designed | 25/25 (no_hardcoding + generalize_suite, by the analyst); full suite per RUN.md 2; after fix round 1: 426/426 (reviewer rerun) | APPROVE (review 2, after fix round 1; review 1 REJECT) |
| 002 | 2 | b0a4f1abe322 | false (delta 001, as intended); one code version | 40 | 0 | 0 | 34 | **fail** (V1 DNM / MINOR 0.92; E1-01, V2, V3 MEETS) | — | GM2a measured (6 packages, all WRONG); delta 002 designed: face-relation sensor + GM3 fastener-chain slice + card access data | 25/25 (no_hardcoding + generalize_suite, by the analyst); after delta 002 implementation: 440/440 (reviewer rerun) | APPROVE (delta 002 implementation review) |
| 003 | 3 | de77b7ab88b1 | false (delta 002, as intended); one code version (10 designs ran twice after a Run restart, identical hashes) | 40 | 0 | 1 (G04 0.99) | 33 | **pass** (E1-01, V1, V2, V3 MEETS; summary.json said `fail` until the verdicts were re-cached in the RUN.md form, P-3) | — | delta 002 measured (7 packages); delta 003 designed: boss layouts (plant-scored), rebate closure, vents, bridge sensor + roof | 26/26 (no_hardcoding + generalize_suite, by the analyst) | pending |

Cell conventions:
- Code SHA: the first 12 hex digits of `summary.json` `code_sha1` (the sha1 of `code_sha1.txt`).
- Train counts: from `summary.json` `counts.train` after every package is judged. CORRECT includes MEETS.
  No-output means no STL (rc 1, a crash or the timeout).
- Regression: `pass` / `fail` / `pending` from `summary.json` `regression`.
- Held-out: the last measured `holdout_score` as a number (for example `0.40`), with the iteration in
  brackets, or `—`.
- Tests: `passed/total`. Review: `APPROVE` / `REJECT`.

---

## Entry format (copy this block for each iteration)

```markdown
## Iteration NNN (YYYY-MM-DD)

**Seed:** SEED (plus any subset or extra seeds from RUN.md section 1)
**Code:** summary.json code_sha1 (12), code_unchanged, runs_on_one_code_version
**Run:** train runs / regression runs, wall time, timeouts

### Results
- Train: MEETS m / CORRECT c / no-output n of N; stages where no-output runs stopped (from summary.json).
- Regression: pass | fail | pending, per id verdict/class.
- Judged this iteration: k (to_judge); reused from the cache: r.

### Defects (judges)
- D1 (designs, capability): what, L3 row ids, weight.

### Gaps (gap analyst)
- D1 → sensor / rule / catalogue / controller → milestone GMx.

### Delta summary (implementer)
- What changed, as generic rules, with the train designs it is expected to move.

### Files changed
| File | + / − lines | Why (gap id) |

### Tests
- Command (RUN.md 2) and result. New tests. Hard-coding guard.

### Reviewer verdict
APPROVE | REJECT, with reasons.

### Notes for Robin
- Owner questions only (real preferences); everything derivable is an assumption with its uncertainty.
```

---

## Iteration 000 (2026-10-24): loop setup (GM0)

**Seed:** none (no Run). **Code:** agent behaviour unchanged except that `--parts` is repeatable.

### Delta summary
- `cad_agent.py`: `--parts DIR` may be given more than once, and defaults to `benchmarks/enclosure/parts`
  as before. `parts.Catalog.load` accepts one folder or a list. The first folder wins an id, a byte-equal
  copy in a later folder is skipped silently, and a different copy is reported as a duplicate. With one
  folder, behaviour is unchanged. `AssemblyState.parts_dirs` records the folders (`design.json`
  `assembly.parts_dirs`).
- `benchmarks/generalize/run_suite.py`: the Run step (train / holdout / regression), with a 20-minute timeout
  per run, `runs.jsonl`, `summary.json`, `code_sha1.txt` with `code_unchanged`, and the judge cache view
  (`to_judge`, `cached`).
- `benchmarks/generalize/cache_verdicts.py`: stores an iteration's verdicts in the judge cache.
- `loop/ARCHITECTURE.md`, `loop/RUN.md`, this ledger.
- `test_generalize_suite.py`: hashing, cache, summary, timeout, CLI and several-catalogue tests (no Ollama;
  a fake agent in a temporary tree).

### Notes
- `../rubric.md` did not exist when this step ran. The spec hash records a missing file as a marker, so
  verdicts cached before the rubric appears are invalidated when it does.
- Regression runs use the enclosure catalogue only (the enclosure loop's exact command). ARCHITECTURE.md
  section 7 says when that switches to both catalogues.

## Iteration 001 (2026-10-24): GM1 baseline, gap analysis, delta 001 (GM2a) designed

**Seed:** 1, full train split + regression set (RUN.md 1).
**Code:** `72dbcfdfb8de` (sha1 of `iter_001/code_sha1.txt`), code_unchanged null (first iteration),
runs_on_one_code_version true. `shasum -c` still matched at gap analysis.
**Run:** 40 train runs (14–69 s each, no timeouts) + 4 regression runs (80–88 s). The regression set used the
enclosure catalogue only, as RUN.md says.

### Results
- Train: MEETS 0 / CORRECT 0 / **no-output 40 of 40** (rc 1 on all). Stops: parse_spec 19 (board size slots
  required), contents 18 ("exactly one board is needed, the answer has 0" ×10, "no catalogue board matches the
  request" ×8), arrange_contents 1 (G23), derive_features 2 (G11, G13: uncaught `MissingParam`, traceback, no
  package).
- Regression: **pass**. E1-01 MEETS (two judges, 1.0), V1 MEETS (two judges), V2 MEETS (two judges), V3 DNM /
  CORRECT 0.99 (one judge; L3.10.1.1 w1, closed height 52.70 > 45).
- Judged this iteration: 4 (regression). Reused from the cache: 0. **The verdicts are not cached yet.**
  `verdicts.json` is a list of `{"id", "meets", ...}` rows, which `cache_verdicts.py` rejects, so `summary.json`
  still says `regression: pending`. RUN.md 1 now tells the iteration 002 Judge step to write the RUN.md 5 form and
  cache 001's verdicts.
- Correction to the computed task text of this step: it said "Train MEETS 3/40, CORRECT 4; regression E1-01
  FAILS". `summary.json`, `verdicts.json` and the judges' files show 0/0 train (no output) and a passing
  regression set. This entry uses the files.

### Defects (judges and run logs)
- S1/S2 (19 designs, all families): ParseSpec requires `board_width` / `board_depth` (`default_rule: null`).
- S3/S4 (18 designs): Contents requires exactly one part of kind `board`. Only `perfboard` has that kind. The
  controller answered perfboard 0 correctly where there is none (G01 transcript), and Python rejected it.
- S5 (G23): the controller put a 25 × 24 perfboard under the camera because the text calls the camera PCB a
  "board".
- S6 (G11, G13): `lid_screw` = largest-thread fastener over both catalogues = `camera_screw_1_4_20` (length
  `from_request`), raised outside derive's `try`.
- R-V3 (regression, w1): `headroom` mapped to "20 mm tall" (the capacitor), which ask_params also used for the
  capacitor height. That adds 17 mm. Seeds 0, 12 and 13 of the enclosure loop mapped it correctly.
- Controller errors seen (secondary): G01 `generic_box` ×1 from the word "box"; G01 `max_x` = 45 (outside its
  `60 x 30 x 26` group); G11 `wall_min` > `wall_max` after a re-ask; Contents `exposed: no` on ports the text
  makes reachable (text coverage repairs it when a plug alias is named).

### Gaps (gap analyst)
- RC1 → rule + catalogue data → **GM2a**: the primary reference is hard-wired to a request-sized `kind ==
  "board"` part with datum names `TOP` / `BOTTOM`. Also `exposed_connectors` takes `connectors[:1]` and never the
  primary's own (S1–S5, 38 designs).
- RC2 → rule + robustness → GM3 slice: the lid fastener rule depends on catalogue contents and ignores named
  fasteners, and part errors escape derive (S6; latent for the regression set on both catalogues).
- RC3 → sensor → GM2 (generated slots): one-number-one-slot is not enforced across ParseSpec and
  `Contents.ask_params` (R-V3).
- RC4 → rule → GM5 prerequisite: `feasible_archetypes` is a constant, so fixtures would get a box once RC1 is
  fixed (G23, G38, G40, G41, G49).
- RC5 → catalogue data: `generic_box` aliases `box` / `block` collide with archetype vocabulary (G01; G08, G10
  and G14 once RC1 is fixed).
- RC6 → prompts → deferred to GM5: enclosure framing in the ParseSpec and Contents prompts (G38, G41).
- No benchmark data defect could be shown (no train package was judged).
- Milestone order: GM1 is closed by this baseline. Its guards (b) and (c) were missing and are folded into delta
  001. GM2 is split into GM2a (primary reference, first) and GM2b. ARCHITECTURE.md 1a records the refinements.

### Delta summary (designed; to be implemented)
`iter_001/delta.md`:
- data: `mount_holes` interfaces on 8 PCB parts (both catalogues), carrier = part with a `grid` block,
  `generic_box` aliases, board slots `required: false`, `archetypes.tray_lid.evidence`.
- rules: primary reference (carrier, else the largest content part, which must offer `mount_holes`), unplaced
  secondary items with a failing `content_placed` check, per-connector exposure including the primary's,
  evidence-gated catalogue-complete lid fastener, contained part errors in derive, cross-stage number ownership,
  shell evidence gate.
- 14 offline tests (T1–T14), each failing on `72dbcfdfb8de`.
- Expected: train packages 0 → 7 (G02 G04 G06 G08 G11 G13 G50), MEETS 0, CORRECT 0–1. 38 designs change their
  stop, every stop is a typed note. Regression pass with E1-01, V1 and V2 byte-identical, V3 → MEETS.

### Files changed (gap analysis step; no agent code)
| File | + / − lines | Why (gap id) |
|---|---|---|
| loop/iter_001/delta.md | new | defects → root causes → delta → tests → expected effect → deferred |
| loop/ARCHITECTURE.md | +44 / 0 | section 1a: baseline and refinements 1–7 (RC1–RC5) |
| loop/RUN.md | +4 / 0 | section 1: iteration 002 run note, verdict format (P1) |
| loop/LEDGER.md | this entry + progress row | — |

### Tests
- `test_no_hardcoding test_generalize_suite`: 25/25 OK on `72dbcfdfb8de` (run by the analyst). The full RUN.md 2
  suite result of the Run step's preflight is not recorded in the iteration folder.
- `test_no_hardcoding` scans only the enclosure catalogue today (GM1 b missing), so its green is weaker than
  ARCHITECTURE.md assumed. T14 of delta 001 fixes this.

### Reviewer verdict
pending (delta not yet implemented).

### Notes for Robin
- No owner questions. Assumptions: the primary is the carrier, else the largest content part (uncertainty low).
  The shell evidence words are {enclosure, box, case, lid} (uncertainty medium; a held-out "housing" brief would
  show it).
- claude-context failed to connect during this step; files were found with targeted grep/ls.

### Delta summary (implemented, delta 001 / GM2a)
Implementer step, 2026-10-25. Reverting means copying `iter_001/code_before/` back (it mirrors the repo paths of every
agent module, `design_rules.json`, every `test_*.py` and both catalogues as they were on `72dbcfdfb8de`). claude-context
failed to connect in this step too; files were found with targeted grep.
- **D1, R9:** `mount_holes` interfaces `{id, kind, holes, seat, top, source}` on `perfboard` (HOLE / BOTTOM / TOP),
  `rpi_pico2`, `arduino_nano`, `arduino_uno_r3`, `rpi_zero2w`, `lcd1602_hd44780`, `oled_ssd1306_096`, `rpi_camera_v2`
  (HOLE / PCB_BOTTOM / PCB_TOP). `parts.interface_failures` is gate rule **R9**: a known kind, and each field names a
  datum of the right class (holes = axis list, seat and top = planes perpendicular to the hole axes). The deferred
  "imported models" rule that was called R9 is now **R10** in `DEFERRED_RULES`. New helpers: `pt.mount_interface`,
  `pt.mount_names`, `pt.is_carrier` (a part with a `grid` block, D2).
- **D3:** `generic_box` loses the aliases `box` and `block`.
- **D4 / D5:** board size slots `"required": false` (the ParseSpec prompt is byte-identical; a required slot is
  `default_rule: null` and not `required: false`). New `archetypes.tray_lid.evidence` = enclosure / box / case / lid.
  `pt.Rules` now carries `archetypes` and each slot's `required`.
- **C1 (primary reference):** Contents candidates = top-k per kind plus every named mount_holes part (appended, so
  the regression lists are unchanged). The primary is exactly one carrier with quantity 1, else the largest
  catalogue plan footprint. If there are two or more carriers, the stop note says `exactly one carrier ...`.
  Recorded as `choice("primary", ..., "rule:primary_reference", reason=carrier | largest plan footprint)`. Typed
  stops: `nothing to design around`, `primary <id> has no mount_holes interface; ... (GM3/GM6)`, primary quantity ≠ 1.
  A request-sized primary takes its size from the board slots when they are filled, else from `ask_params`. A
  non-carrier primary carries nothing else. Other items go in `unplaced` (in design.json, and in layout.json when
  there are any), each with a hard failing `content_placed_<item>` check (`assembly_checks.content_placed`).
  `inside_contents` is emitted only when the primary carries contents. The primary keeps node, item and role id
  `board` (`A.PRIMARY`). Its holes, seat and top come from its interface everywhere (layout.Placer,
  hole_columns, board_symmetries, board_keepout, build_envelopes, driver_columns, derive_cavity, standoffs, seated,
  board_block, board_provenance, board_screw, add_fastener_checks). No `"TOP"` / `"BOTTOM"` / `"HOLE"` literal is
  left in layout.py, parts.py or assembly.py. Exposure is per connector: a one-connector part keeps the `exposed`
  key, and a part with several gets a `<connector>_exposed` key for each (the extra prompt sentence appears only
  then). Items carry `exposed_connectors`, `lay.Item.connectors` and per-connector text coverage and coverage
  revert. `exposed_connectors` yields every exposed connector, including the primary's own. A part with several
  connectors gets `<node>_<conn>_plug` / `_cut` ids (one-connector ids are unchanged). The primary's connectors
  are recorded as `wall[board.<conn>]` by `rule:fixed_by_primary` (wall_facing of the axis).
- **C2 (lid fastener):** `lid_screw_choice`. Only catalogue-complete fasteners (no `from_request` param) qualify.
  A fastener the text names wins (`rule:text_evidence`, quotes kept). Otherwise the rule takes the largest-thread
  complete screw (`rule:largest_complete_screw`, recorded as an assumption). A named fastener that is not complete
  is noted and skipped. `board_screw` has the same complete filter. `derive()` selects the fastener inside its
  `try` and catches `pt.PartError`.
- **C3 (one number, one slot across stages):** `st.number_owner` is filled by ParseSpec and by
  `Contents.ask_params`. The owner question and the slot question are lifted into module functions
  (`owner_question`, `ask_slots`; ParseSpec's prompts are unchanged). When ask_params picks an id a spec slot owns,
  the owner question runs (`assy_spec_owner`). A spec slot that loses is re-asked without the id (`assy_spec_slot`)
  and falls back to its rules default, flagged. A part size that loses is re-asked without it
  (`assy_params_reask`).
- **C4 (archetype gate):** `archetype_gate` returns `tray_lid+screws` only for a mount_holes primary when the text
  contains shell evidence. Otherwise the stop note is `not implemented: archetype (primary <id>; no shell evidence;
  candidates for GM5: plate / bracket / block / cradle)`.
- **C5:** `test_no_hardcoding` scans the ids and aliases of both catalogues (T14). The feature graph's own
  primitive names (`feature_graph.PRIMITIVES`: box, cylinder, tube, shell, part) are the only exemption, and a test
  asserts it stays exactly that set, because `generic_tube`'s alias `tube` equals a primitive name. T8 runs E1-01 on
  both catalogues offline.
- Not changed: the CLI, run_suite.py and RUN.md (no new test module; the RUN.md 2 unittest line is still complete).

### Files changed (implementation)
| File | + / − lines | Why (gap id) |
|---|---|---|
| assembly.py | +495 / −144 | C1–C4 (RC1–RC4): primary reference, unplaced items, per-connector exposure, interface datums, lid fastener, contained part errors, number ownership, archetype gate |
| parts.py | +96 / −10 | R9 interface gate, mount helpers, carrier rule, `required` slots, `archetypes`, board_keepout from the interface; deferred R9 → R10 |
| layout.py | +21 / −12 | primary holes and top from the interface; `Item.connectors`; facing connector by name |
| assembly_checks.py | +9 / 0 | `content_placed` check type |
| design_rules.json | +7 / −3 | D4 `required: false` on the board slots; D5 `archetypes` block |
| enclosure parts: perfboard, rpi_pico2 | +10, +1 | D1 interfaces |
| generalize parts: arduino_nano, arduino_uno_r3, rpi_zero2w, lcd1602_hd44780, oled_ssd1306_096, rpi_camera_v2 | +1 each | D1 interfaces |
| generalize parts: generic_box | 0 / −2 | D3 aliases (RC5) |
| test_assembly.py | +416 / −7 | T1–T3, T6–T12 and two companion tests; three tests updated for the intended behaviour change (below) |
| test_parts.py | +65 / 0 | T4, T5, T13 |
| test_no_hardcoding.py | +18 / −4 | T14 (both catalogues; primitive-name exemption) |
| loop/iter_001/code_before/ | new | revert copy |

### Tests (implementation)
- **Full RUN.md 2 suite: 422 tests, OK** (1142 s). `test_no_hardcoding`: OK (3 tests, both catalogues).
- New tests, by class: `test_assembly.TestPrimaryReference` (T1 module primary without board slots; T2 carrier stays
  primary, with the ParseSpec and Contents prompts **byte-equal to iteration 001's recorded E1-01 transcripts**; T3
  typed stop with no mount_holes; plus unplaced items with failing hard `content_placed` checks).
  `TestLidFastener` (T6, T7). `TestBothCatalogues` (T8: E1-01 through Build on both catalogues, poses, fasteners
  and body volumes equal to the enclosure-only run within 0.01; T9 part error contained). `TestNumberOwnership`
  (T10 in both directions, plus a no-conflict guard). `TestArchetypeGate` (T11). `TestExposure` (T12: Zero 2 W
  primary, two micro-USB connectors named, own sweeps and cuts on the -Y wall, `rule:fixed_by_primary`, HDMI stays
  closed, text_coverage passes). `test_parts.TestInterfaces` (T4, T5). `TestCatalogueVocabulary` (T13).
  `test_no_hardcoding` (T14).
- Run against `code_before` (old modules and old catalogues, new test files): 14 of 18 fail or error. The 4 that pass
  are the T10 no-conflict guard and the 3 `test_no_hardcoding` tests (T14 changes the test, not the agent).
- Tests changed because the behaviour changed on purpose: `test_gate_then_a_typed_parse_spec_failure` and
  `test_enclosure_alias_runs_assembly` (a request with no numbers now stops at contents with `nothing to design
  around`, with no re-ask). `test_two_boards_is_a_typed_failure` (the note now says `exactly one carrier`).
- Offline regression invariance (scripted answers, E1-01 / V1 / V2 / V3, old code against new code): identical
  meshes (canonical sorted-triangle hash), poses, fasteners, question labels, prompts and check results (all rc 0).
- **Smoke run** (`run_suite.py`, seed 1, live ornith-1.5:9b; a scratch repo tree whose `loop/` is
  `scratchpad/impl_001`, so this iteration's real folder was not touched; code `d2ecb4742549`):
  - Regression: E1-01, V1, V2, V3 all rc 0. **E1-01, V1 and V2 give the same meshes as iteration 001's judged
    packages** (canonical hash). **V3 changed as forecast:** the seed-1 headroom mis-map happened again, and
    C3 corrected it live. Note: `n7 (20 mm) is claimed by spec slot headroom and by generic_1.height; owner vote
    {generic_1.height: 3}`, then headroom was re-asked to `n8 (3 mm)`. Closed height is now inside the limit,
    and every agent check passes (iteration 001: rc 3, bbox).
  - G04: **package, rc 3** (iteration 001: parse_spec stop). Zero 2 W primary, three exposed ports on the -Y wall
    (`rule:fixed_by_primary`), M2.5 lid screws by text evidence. Failing agent checks: three
    `ligament_board_*_cut_base` (the three port cuts on one wall leave less than the minimum ligament between
    them), `bbox` and four `pilot_depth_standoff_*`.
  - G11: **package, rc 0** (iteration 001: uncaught MissingParam). Perfboard carrier, DC jack exposed by text
    coverage, M3 self-tap lid by evidence, ISO 4762 bolt noted and skipped. The agent's checks do not see what is
    still missing (fan, opening, exhaust slots; the controller listed no heatsink box).

### Notes for the next gap analyst / Robin (implementation)
- **Process (P3): OpenSCAD 2021.01 STL output is not byte-deterministic.** Compiling the same `.scad` twice
  gives the same triangle set in a different facet order, so the sha1 differs. `run_suite.py`'s `geometry_sha1`
  hashes raw STL bytes, so the judge cache can never hit, even for identical geometry, and the forecast "E1-01 / V1
  / V2 are cache hits in iteration 002" will not come true. A canonical mesh hash (sorted rounded triangles)
  would fix it. That is a Run-tooling change and outside this delta.
- Module primaries with a thin solder-side keep-out fail `pilot_depth_standoff_*`: the standoff height
  (keepout_below + margin) is shorter than the pilot depth (min_engagement + margin) + min_feature − floor. The
  sensor is honest. A generic fix: derive the cavity floor from max(keep-out, the pilot column the screw needs).
- Ports that sit close together on one wall (Zero 2 W) break the minimum ligament between adjacent cuts. They
  need a merged opening or a different rule, decided from rubric evidence once judged.
- No owner questions. Assumption added: two or more carriers is a typed stop (the delta did not say). Uncertainty
  low, because no train design has two carriers.

### Reviewer verdict (delta 001 implementation, adversarial review, 2026-10-25)
**REJECT (approve = false). One real defect, the fix is small. Everything else holds.**

How it was checked: I diffed every file against `iter_001/code_before/` (assembly.py, parts.py, layout.py,
assembly_checks.py, design_rules.json, the 9 changed part.json files, and the three test files). I reran the full
RUN.md 2 suite: **422 tests, OK (1140 s)**, with `test_no_hardcoding` green on both catalogues. I built the
regression set offline with scripted answers on the old code (a scratch copy of `code_before`) and on the new code:
E1-01, V1, V2 and V3 give the **same feature-graph hash, solid volumes, poses, fasteners and spec**, and the only
new record is `choices.primary = perfboard`. On both catalogues the lid choice for all four regression texts is
still `screw_m3_selftap` (`rule:largest_complete_screw`), and the archetype gate gives `tray_lid+screws` for each.
claude-context failed to connect, so I used targeted grep.

Defect (blocking):
- **R1: C3's cross-stage re-ask recurses without a bound. Two spec-owned numbers make it loop until a
  RecursionError, which is a traceback and the kind of failure C2 removes.** `Contents.claim` re-asks a part size
  that lost by calling `ask_params(..., exclude=[ref])`, and that call goes through `claim` again. The exclusion is
  not cumulative, so the number excluded first comes back in the next re-ask. If the controller's first choice
  (A) and its second choice (B) are both owned by spec slots, and the owner question gives each to its spec slot,
  the run goes A → owner → re-ask without A → B → owner → re-ask without B → A → ... Identical prompts get
  identical votes, so a live 9B run repeats the same answers. Reproduction (scripted, V3: headroom mis-mapped to
  the "20 mm tall" number, owner votes for the spec slot, the re-ask prefers 20 and falls back to max_z's number
  otherwise): `RecursionError after 1480 owner calls`
  (`/private/tmp/claude-501/-Users-robinonsay-python-llm-bt/7d706733-5c1d-44fb-a74b-bc29203e1df6/scratchpad/recur.py`). With Ollama that would be about 4,400 voted calls before the crash. The delta specifies
  **one** re-ask with the id removed ("The losing slot is re-asked with that id removed from its enum"). Fix: keep
  the excluded ids cumulative across re-asks, or make the part-size re-ask final (if it again picks a number another
  slot owns, return None and stop with a typed note `no number in the text for <param>`). Add a test with this
  scripted shape that asserts a typed stop and a bounded number of `assy_spec_owner` calls.

Checked and accepted:
- Delta coverage: D1–D5 and C1–C5 are all implemented as written. The assumption "two or more carriers is a typed
  stop" is not in the delta, and the ledger records it. Every `unplaced` item reaches design.json, layout.json and
  self_report.json, each with a hard failing `content_placed_<id>` check. No `"TOP"` / `"BOTTOM"` / `"HOLE"`
  literal is left in code; they appear only in docstrings.
- Generic: no design id, train number or part id in agent code. The new vocabulary lives in design_rules.json
  (`archetypes.tray_lid.evidence`) and in part.json (`interfaces`). The rules trigger on part data (grid block,
  `mount_holes`, `from_request` params) and on text evidence, so an unseen design with the same capability gets
  the same treatment.
- Guard change: `test_no_hardcoding` now exempts the feature graph's own primitive names (box, cylinder, tube,
  shell, part). That loosens the guard slightly, but it is justified (`generic_tube`'s alias equals the primitive
  `tube`), and a test pins the exemption to exactly that set.
- Tests: the 18 new tests are behavioural, not circular. T5 checks the data invariance against the old datum
  names. T2 compares prompts byte for byte with recorded transcripts, and those transcripts exist, so it does not
  skip. T8 compares two catalogue sets through Build. The implementer reports 14 of 18 fail on code_before. The 4
  that pass are guards, which is fine. **Missing:** no test covers the recursive re-ask path (R1).

Non-blocking notes (not defects):
- N1: `layout.describe` still names a part's first connector. For a multi-connector content part on a carrier,
  the arrangement words can name the wrong connector. Today that case is unreachable (Uno and Zero 2 W are always
  primaries), but it will show up once GM2b places them.
- N2: `reask_spec_slot` sets the new spec value without rerunning ParseSpec's relation checks (bands, wall
  min ≤ max). A re-asked `board_width` is not swapped against `board_depth` either.
- N3: the alias `m3 screw` is shared by `bolt_m3_iso4762` and `screw_m3_selftap`, so "M3 screws" adds a spurious
  "skipped bolt" note. The choice is still right.
- N4: the lid rule's text evidence does not tell lid screws from board screws. If a brief names only the board
  screw, the lid gets that screw too. That is acceptable as recorded evidence, so revisit it only when judged
  packages show it matters.

### Fix round 1 (delta 001 implementation, after the REJECT above)
claude-context failed to connect again, so targeted grep was used.

- **R1 fixed (blocking): the part-size re-ask is final.** `Contents.claim` takes `final` (set by `ask_params` when it
  runs as the re-ask, i.e. with `exclude`). If the re-ask picks a number id a spec slot owns, no second owner
  question runs: `claim` returns None and records `Contents.param_stop`, and both `ask_params` callers stop with
  `fail(param_stop)`, a typed stop: `<part>: no number in the text for <param>: the re-asked <param> chose <id>
  (<text>), which spec slot <slot> owns, and the part-size re-ask is final`. This is the delta's "one re-ask with the
  id removed". The reviewer's scripted shape (`scratchpad/recur.py`) now ends in that FAILURE after one owner
  question (3 votes) and one re-ask, where it was a RecursionError after 1480 owner calls.
- **Test gap closed:** `TestNumberOwnership.test_part_size_reask_is_final` scripts that shape (owner always gives the
  number to the spec slot, the re-ask picks `max_z`'s number). It asserts FAILURE with the typed note, exactly
  `VOTES` `assy_spec_owner` calls and `VOTES` `assy_params_reask` calls, the excluded id absent from the re-ask
  prompt, and no number owned by the part size.
- **N1 fixed:** `layout.describe` names the item's exposed connectors (`Item.connectors`) and falls back to the
  part's first connector only when the item names none. Single-connector parts give the same words as before (their
  exposed list is that one connector), so regression prompts do not change. Test: `TestDescribeConnectors`.
- **N2 fixed:** ParseSpec's post-slot rules moved into `settle_spec` (the wall band whose default end breaks it
  yields to the text end; the board_width/board_depth frame swap, which now swaps `number_owner` with the values
  and provenance, so an owner question after a swap names the right slot). `Contents.reask_spec_slot` checks the
  re-asked value with `spec_relation_error` (> 0, wall_min <= wall_max against the other end) and drops a violating
  answer to the rules default, then runs `settle_spec`. Test: `test_reasked_spec_slot_keeps_parse_spec_rules`.
- **N3 fixed:** `lid_screw_choice` reports a skipped (not catalogue-complete) fastener only when some of its text
  hits are not also hits of a complete fastener (same source, sentence and alias). "M3 screws" no longer adds the
  "skipped bolt" note; the bolt's own alias still does. Test: `TestLidFastener.test_shared_alias_is_not_a_skip`.
- **N4 not changed, by the reviewer's own note** ("revisit it only when judged packages show it matters"). Telling
  lid screws from board screws in the text needs a sentence-level role vocabulary; recorded here as open.
- Generic: no design id, part id or number added to agent code; the relations read slot names ParseSpec already
  used. `test_no_hardcoding` green.
- Suite: the full RUN.md 2 unit line, **426 tests OK (1141 s)** (422 + the 4 new tests), `test_no_hardcoding` green.

### Reviewer verdict (delta 001, after fix round 1, adversarial review 2, 2026-10-25)
**APPROVE (approve = true).** The blocking defect R1 is fixed and tested. No new blocking defect was found. Two
non-blocking findings are below for the next gap analyst.

How it was checked: claude-context failed to connect again, so I used targeted grep and diff. I diffed every agent
module, `design_rules.json`, the changed part.json files and the three test files against `iter_001/code_before/`.
I reread the whole assembly.py diff with the fix-round changes (`claim(final=...)`, `param_stop`, `settle_spec`,
`spec_relation_error`, `reask_spec_slot`, `layout.describe`, the `lid_screw_choice` skip filter).
- **Full RUN.md 2 suite rerun: 426 tests, OK (1140 s).** `test_no_hardcoding` is green, and so are the fix-round
  classes (`TestNumberOwnership`, `TestDescribeConnectors`, `TestLidFastener`), each rerun on its own.
- **R1 repro rerun** (`scratchpad/recur.py`, the shape from review 1). It now ends in a typed FAILURE after one owner
  question and one re-ask: `generic_cylinder: no number in the text for height: the re-asked height chose n30
  (45 mm), which spec slot max_z owns, and the part-size re-ask is final`. Before the fix it was a RecursionError
  after 1480 owner calls. The recursion is now bounded by construction: `claim(final=False)` →
  `ask_params(exclude)` → `claim(final=True)`, which never asks the owner question again.
- **Offline regression invariance rerun** with scripted answers on code_before and on the current code
  (`scratchpad/rev2_regr.py`). For E1-01, V1, V2 and V3 these are identical: status, layout poses, fasteners, spec,
  solid volumes, feature-graph hash, the sequence of question labels, the hash of every prompt, and every check id
  with its pass/fail. The only new record is `choices.primary = perfboard`. So the fix round (settle_spec, the
  describe words) left the regression prompts and geometry unchanged.
- **The test for R1 is meaningful.** `test_part_size_reask_is_final` scripts the failing shape and asserts these:
  a typed stop, exactly VOTES owner calls and VOTES re-ask calls, the excluded id missing from the re-ask prompt,
  and no ownership for the part size. On the code from review 1 it hits a RecursionError (an error, not a pass).
  The N1, N2 and N3 tests call functions or behaviour that did not exist before.
- **The fix is generic.** It adds no design id, part id or number to agent code. The relations in
  `spec_relation_error` / `settle_spec` read slot names that ParseSpec already used.

Non-blocking findings (not defects that block this delta; recommended for iteration 002's gap analysis):
- **F1: a cross-stage re-ask that lands on a number another part size owns is accepted and then lost.** In
  `Contents.claim`, `claim(final=True)` accepts an id whose owner is a part size (`"." in owner`) and does not
  record it under this slot. The outer `claim` then looks the id up with `next(r for r, s in number_owner.items() if
  s == slot)`, finds nothing and returns None. The run stops with a misleading note. Reproduction
  (`scratchpad/rev2_edge.py`, V3): headroom is mis-mapped to the "20 mm tall" id, the owner question keeps it for
  headroom, and the re-asked height picks the diameter's id. The result is FAILURE `generic_cylinder: no number in
  the text for diameter, height`, although the diameter was found. It is bounded and typed and needs two controller
  errors in a row, but it makes the error signal wrong. Fix: return the id from the inner re-ask (for example,
  `ask_params` also returns the refs it kept), or make the final re-ask stop with a note that names the shared id.
- **F2: the shell evidence gate also fires on generic printability wording in L1 rows.** I ran it over the 40
  train texts. The words {enclosure, box, case, lid} hit all 15 shell briefs, and they also hit 6 of the 25 non-shell
  briefs through L1 boilerplate: G17, G27 and G37 ("footprint box"), G22 and G32 ("plan bounding box"), and G26
  ("worst-case tolerances"). So delta.md 8's claim that the vocabulary "separates ... from the fixtures and mounts
  in the train split" is false on the full split. It holds for the 5 fixtures this delta unblocks (G23, G38, G40,
  G41 and G49 have no hit), so no iteration 002 forecast changes. A fixture brief that is not seen in training,
  has a mount_holes primary and uses that boilerplate would get a tray and lid, which is wrong-family geometry. That
  is not a regression (before this delta every brief got one), and it scores the same as a typed stop. Measured
  alternative: restrict the evidence to the request text, not the L1 rows. On train this hits exactly the 15
  shell briefs and 0 of the 25 others. The regression requests also say "enclosure". This is generic and is a
  one-line change in `archetype_gate`. Uncertainty: medium.

Still open from review 1: N4 (the lid rule's text evidence does not tell lid screws from board screws).

## Iteration 002 (2026-10-25): GM2a measured, gap analysis, delta 002 designed

**Seed:** 2, full train split + regression set (RUN.md 1).
**Code:** `b0a4f1abe322` (sha1 of `iter_002/code_sha1.txt`), code_unchanged false (delta 001 / GM2a, as intended),
runs_on_one_code_version true. `shasum -c` matched every file at gap analysis.
**Run:** 40 train runs + 4 regression runs, 44 in total, 35 minutes of run time (22–99 s each), no timeouts. The
regression set used the enclosure catalogue only.

### Results
- Train: **MEETS 0 / CORRECT 0 / no-output 34 of 40.** rc: 0 ×2 (G02, G11), 3 ×4 (G04, G06, G13, G50), 1 ×34.
  - Stops (from summary.json):
    - contents 29:
      - `nothing to design around` 18: G16 G17 G18 G20 G21 G22 G24 G27 G30 G31 G32 G33 G35 G36 G38 G42 G43 G45.
      - `primary <id> has no mount_holes interface` 6: G03 G10 G12 (generic_box), G05 (esp32), G09 (dc jack), G47
        (hc_sr04).
      - `no number in the text` 4: G08 generic_cylinder, G26 and G29 generic_tube, G37 gear.
    - choose_archetype 4: G23 G40 G41 G49 (no shell evidence, as designed).
    - arrange_contents 2: G01 G14 (no screw passes the Nano's holes).
  - Iteration 001 forecast 7 packages. G08 is the miss: the 18650 cell came as a cylinder with no number.
- Regression: **fail.** E1-01 MEETS (1.0). **V1 DNM / MINOR 0.9185.** V2 MEETS, V3 MEETS (V3 was CORRECT 0.99 in
  iteration 001; delta 001 C3 fixed its headroom).
- Judged this iteration: 10 (6 train + 4 regression), one judge each. Reused from the cache: 0. Iteration 001's
  forecast "E1-01 / V1 / V2 are cache hits" did not come true: STL facet order is not deterministic (P-2).
  `verdicts.json` is in the RUN.md 5 form and the verdicts are cached.
- **Correction to the computed task text of this step:** it said "Train MEETS 3/40, CORRECT 3; regression E1-01
  FAILS". The files show train 0 / 0, E1-01 MEETS, and a regression set that fails on V1. This entry uses the files.

### Defects (judges)
- R-V1 (V1, regression): the jack faces +X and the Pico USB faces −X. The text says "the same short end". w3 L3.1.2.1;
  w2 L3.1.3.1, L3.5.3.1, L3.6.3.1, L3.8.1.1.
- D-PILOT-DIA (G02 gate G4, G04 gate G6, G11 gate G2): board pilots Ø1.70 (M2) where M3 / M2.5 is required.
- D-PILOT-DEPTH (G02 gate G6 and L3.3.3.2; G13 L2.8.3): pilots shallower than screw length − clamped plate, so the
  screw bottoms out.
- D-STANDOFF (agent-sensed, `pilot_depth_standoff_*`: G04 −1.39, G06 and G13 −0.39): the standoff is too short for its
  pilot.
- D-SD (G04 gate G5): no microSD opening.
- D-SECONDARY: unplaced or unlisted parts. G06 (Pico; gates G4, G5), G11 (fan, heatsink; gate G4), G13 (buttons,
  plungers, plunger holes; G0, G5), G50 (fan, OLED, encoder, window; G0, G3, G4).
- D-VENT (G02 gate G5, G11 gate G5, G50): no vents or slots.
- Others, one design each: G02 lip lid instead of a rebate, and a USB-B bridge of 16.8 > 15. G04 corner bosses give
  Y 42.2 > 40 (w1). G06 has no 30° tilt and no window. G13 Pico USB on +Y instead of −X, and Z 37.3 > 35. G50 has no
  snaps.

### Gaps (gap analyst)
- R-V1 → **RC-A**, missing sensor: no check reads a stated relation between exposed items, and p_yes near-tied (0.265 vs
  0.254). → first slice of GM2b (`face` relation). **Fix first.**
- D-PILOT-DIA → **RC-B1**, wrong rule + catalogue datum: the board screw is the smallest that passes the hole. It ignores
  the board-role fastener in the text and the board's datasheet thread. → GM3.
- D-PILOT-DEPTH → **RC-B2**, missing bottoming sensor + derivation term (screw length unused). Latent in E1-01's bosses
  too. → GM3.
- D-STANDOFF → **RC-B3**, derivation term: the cavity floor ignores the pilot column. → GM3.
- D-SD → **RC-D**, catalogue: the Zero has the SD datums but no connector and no mating card part. Benchmark note: G04
  A4 cites a catalogue `sd_card_zone` that no part.json has. That is a stale reference, resolved by the catalogue data.
  The requirement's numbers stand, and no benchmark file was changed.
- D-SECONDARY and the 18 + 1 Contents stops → **RC-C**, Contents offers four kinds only, with enclosure framing. →
  GM2b. Deferred: no geometry until relations place secondary items.
- D-VENT → **RC-E**, missing capability → GM4 slice; the next delta's first candidate.
- G01 and G14 → RC-B4, locating pins (GM3). G03, G05, G09, G12, G47 → pocket / cradle (GM6).
- Process: **P-1** `../rubric.md` still missing. Judges used the enclosure rubric with each requirements.md; classes are
  sound and scores are estimates. **P-2** the byte-level geometry hash never hits.
- No benchmark data contradiction or impossible band found in the judged designs, so no benchmark file was changed.

### Delta summary (designed; to be implemented)
`iter_002/delta.md`:
- **C0 (RC-A):** `face_relations` vocabulary (rules), a sentence-scoped evidence gate, one voted `assy_relation`
  question per run when gated, unanimous readings only, and a controllable `face_relation_<A>_<B>` check that prescore
  filters on. The smoke measurement on the four regression texts at seeds 1–5 is a merge condition.
- **C1 (RC-B1):** `board_screw_choice`, in order: board-role text evidence (`fastener_roles`) that passes the hole, then
  the interface `thread` (data: Zero 2.5, Uno 3.0, Pico 2.0), then the smallest that passes.
- **C2 (RC-B2, RC-B3):** pilot depth = setpoint(max(min_engagement, length − clamped plate)), a `pilot_bottoming`
  sensor, and a cavity floor that holds every standoff's pilot. Regression geometry changes only in the boss pilots
  (6.1 → 7.7; rubric ≥ 6.0).
- **D1 (RC-D):** the `card_microsd` plug part and an `sd` connector on `rpi_zero2w`.
- **C3 (P-2, tooling):** canonical triangle hash in `run_suite.geometry_sha1`.
- 15 tests (T1–T15), each failing on `b0a4f1abe322` except the T15 guard.
- **Expected:** regression fail → pass (V1 MEETS). Train CORRECT 0 → 1 (G04). G02 gates 3 → 1, G11 gates 3 → 2. The
  no-output stops do not change.

### Files changed (gap analysis step; no agent code)
| File | + / − lines | Why (gap id) |
|---|---|---|
| loop/iter_002/delta.md | new | defects → root causes → delta → tests → expected effect → deferred |
| loop/ARCHITECTURE.md | +29 / 0 | section 1b: iteration 002 measurement and refinements 1–6 (RC-A, RC-B, RC-C, RC-D, RC-E, P-2) |
| loop/RUN.md | +4 / 0 | section 1: iteration 003 run note |
| loop/LEDGER.md | this entry + progress row | — |

### Tests
- `test_no_hardcoding test_generalize_suite`: **25/25 OK** on `b0a4f1abe322`, run by the analyst. The full RUN.md 2
  suite result of the Run step's preflight is not recorded in the iteration folder.

### Reviewer verdict
pending (delta not yet implemented).

### Notes for Robin
- No owner questions. Assumptions:
  - A fastener the text names in a sentence about the board is the board screw when it passes the hole (uncertainty
    low).
  - The microSD fingertip zone is 12.0 × 5.4 (uncertainty medium).
  - Relation words {same} and {opposite, other} cover how briefs state face relations (uncertainty medium; a held-out
    brief with "facing each other" or "back to back" would miss the gate and fall back to today's behaviour, not to a
    wrong constraint).
- `../rubric.md` is still missing (P-1). Writing it is not an owner preference, but it should exist before the first
  held-out measurement.
- claude-context failed to connect during this step; files were found with targeted reads and grep.

### Delta summary (implemented, delta 002)
Implementer step, 2026-10-25. claude-context failed to connect in this step, so files were found with targeted reads and
grep. Nothing under `../holdout/` or `holdout_results/` was opened. The pre-change code, rules, tests and both
catalogues are in `iter_002/code_before/` (paths relative to the repo; `run_suite.py`, `cache_verdicts.py` and RUN.md
too), so the change can be reverted file by file.
- **C0 face relation (RC-A).** `design_rules.json` `face_relations` (same: {same}; opposite: {opposite, other}; each with
  a meaning and a source). `relation_members` (each exposed connector of a content item, one member per item whatever
  its quantity, plus the primary's own exposed connectors), `relation_gate` (sentence-scoped: one sentence names both
  parts and a relation word; pairs on one item, i.e. both on the primary or both on one content part, are never gated),
  `ArrangeContents.ask_relations` (once per run after the edge vote, label `assy_relation`, enum = gated values +
  `not_stated`; a constraint only when every valid sample agrees and it is not `not_stated`), `st.relations`,
  `choices.relation[<A>|<B>]` (`llm:relation`), `design.json arrange.relations` (asked pairs, enums, votes,
  constraints; written only when a pair was asked). Sensor: `face_relation_<A>_<B>` (new check type
  `assembly_checks.face_relation`, value 0 / 1, limit 0, hard, no `conflict` key, so prescore filters on it; the relation
  semantics live in `assembly_checks.FACE_RELATIONS`, and a vocabulary entry without a row there is never offered).
- **C1 board fastener (RC-B1).** `board_screw_choice`: role evidence `rule:text_evidence[board]` (largest thread that
  passes among the screws named with a board role word, `design_rules.json fastener_roles.board`, or the primary's own
  names), then `rule:interface_thread` (new optional interface field `thread`, R9 accepts only a positive number), then
  `rule:smallest_thread_through_board_hole` (now recorded as an assumption). A named screw that does not pass is noted.
  Data D2: `thread` 2.5 on `rpi_zero2w`, 3.0 on `arduino_uno_r3`, 2.0 on `rpi_pico2`; none on the perfboard.
- **C2 pilots (RC-B2, RC-B3).** One helper `pilot_depth(use)` = setpoint(max(min_engagement, length − clamped plate))
  (standoffs: primary `top − seat`; bosses: `lid.z`; no `length`: today's term), read by both pilot nodes and by
  `derive_cavity`, whose `z0` is now `min(seat − keepout_below − m, seat − pilot depth − min_feature + floor − m)`. New
  sensor `pilot_bottoming_<node>` (value = pilot depth, limit = length − plate; `MINIMUM_TYPES`). Engagement shortfall
  is not a check (deferred to GM3, as the delta says).
- **D1 card access (RC-D).** New part `benchmarks/generalize/parts/card_microsd` (kind plug; names "microsd card",
  "micro sd card", "micro-sd card", "tf card"; card 11.0 × 15.0 × 1.0; seat 2.5 mm short of the card end; access zone
  12.0 × 5.4 centred 1.0 above the card axis, 8.5 mm from the seat outward, assumed, uncertainty medium) and a fourth
  connector `sd` on `rpi_zero2w` (`SD_MOUTH` / `SD_AXIS`, mates `card_microsd`; its notes updated).
  **Supporting change needed for D1:** `derive_port_cut` centred every box opening on the mouth, so an access zone above
  its axis would poke 0.6 mm into the wall above the cut. New `crossing_section`: when the crossing plug primitives'
  sections are not centred on the connector axis, the box opening is centred on, and sized by, the union of their
  sections (`node.env` carries that section to `oversize_*`). For every catalogue cable plug (centred sections) the
  iteration 002 expressions are emitted unchanged.
- **C3 canonical geometry hash (P-2, tooling).** `run_suite.geometry_sha1` hashes `canonical_stl` per file (binary or
  ASCII STL, vertices rounded to 1e-4 mm, each triangle started at its smallest vertex with its winding kept, triangles
  sorted); bytes that are no STL with triangles enter raw, as before. RUN.md section 5 updated.

**Deviations from delta.md (measured, generic; the reviewer should check both):**
1. **C1 role evidence is clause-scoped, not sentence-scoped** (clauses = a sentence split at `,` `;` `:`). The delta's
   C1 table says G50 → M2.5 by datasheet ("the OLED sentence has no board word"). That sentence (G50 L1.8) does contain
   "OLED board", so the literal sentence rule picks M2 (the OLED's screw) for the Pi. Measured on the ten texts: the
   sentence rule gives G50 `screw_m2_selftap` by role; the clause rule reproduces the delta's whole table (G02 M3 role,
   G04 M2.5 role, G11 M3 role, G13 M2 role, G06 M2 smallest, G50 M2.5 datasheet, E1-01 / V1 / V2 / V3 M2 smallest).
   Known imprecision: G11 L1.8's lid clause "...into bosses outside the board's outline" also counts as board evidence
   for M3 (same answer). Uncertainty: low.
2. **C0's prompt quotes the gating sentences** ("Where the text relates them:" then each gating sentence, above the pair
   lines). With the delta's prompt the smoke measurement passed its merge condition, but only just, and C0 then never
   constrained V1. With the quotes it constrains V1 in every seed and V2 never (table below). The quotes are the
   sentences Python's gate already found, so nothing new is decided by the LLM.

**Smoke measurement (merge condition for C0; live ornith-1.5:9b, the `assy_relation` question alone, the four
regression texts, seeds 1–5, `scratchpad/smoke_relation.py`):**

| Text (gated enum) | delta.md prompt: votes per seed 1..5 | merged prompt (quotes): votes per seed 1..5 |
|---|---|---|
| V1 {same} | ns3, s2/ns1, s1/ns2, s2/ns1, ns3: **0/5 constrain**, unanimous not_stated 2/5 | s3 ×5: **5/5 same** |
| V2 {same} | ns3, ns2/s1, ns3, ns3, ns2/s1: never unanimous same | ns3 ×5: never unanimous same |
| E1-01 {opposite} | o3, o1/ns2, o3, o3, o3: 4/5 opposite | o3, o2/ns1, o3, o3, o2/ns1: 3/5 opposite |
| V3 {opposite} | o3, o2/ns1, o3, o3, o2/ns1: 3/5 opposite | o3 ×5: 5/5 opposite |

(s = same, o = opposite, ns = not_stated.) Merge condition: V2 never unanimous `same` (holds under both prompts); V1
unanimous `not_stated` on at most 2 of 5 seeds (2/5 with the delta's prompt, 0/5 merged). C0 merges with the merged
prompt. The pre-written V2 exclusion rule was not needed and is not implemented. E1-01 and V3 can never be pushed to
`same` (their enum lacks it).

**Offline regression invariance** (iteration 002's recorded answers and p_yes for E1-01 / V1 / V2 / V3, replayed on a
scratch copy of `code_before` and on the new code, `scratchpad/inv.py`; relation answers V1 same, E1-01 / V3 opposite,
V2 not_stated): poses, fasteners and spec identical for E1-01, V2 and V3; V1's arrangement changes as intended
((−X, +X) → (+X, +X), decision `prescore+llm:vote+rank`). The only geometry change elsewhere is the boss pilot (depth
6.1 → 7.7, h 7.1 → 8.7); standoffs and cavity floors are numerically unchanged. Question labels: the same, plus three
`assy_relation` samples per text, and fewer `assy_confirm` calls where the relation constraint removed classes before
ranking (E1-01 6 → 1, V1 8 → 2, V3 4 → 1; V2 unchanged).

**Smoke run** (`run_suite.py --iter 002 --seed 2`, live ornith-1.5:9b, a scratch repo tree whose `loop/` is
`scratchpad/impl_002`, with run_suite.py copied so it resolves there; this iteration's real folder was not touched. The
code_sha1 there lists scratch paths, so its hash `31fe15f29928` is not the repo's; agent files are byte-identical to the
repo at the end of this step):
- G04: package, **rc 3, the only failing agent check is `bbox`** (77.3 × 42.2 × 19.0 vs 90 × 40 × 22; the delta
  forecast "DNM: bbox Y 42.2 > 40, w1, stays" and Z about 19). M2.5 board screw by role (L1.3), `sd` exposed by text
  coverage on −X (`rule:fixed_by_primary`), standoffs 5.2 tall holding the 6.7 pilot (iteration 002: four failing
  `pilot_depth_standoff_*`). The iteration 001 ligament failures between the −Y ports did not recur.
- G02: package, **rc 0, 78/78 agent checks pass.** M3 board screw by role, standoff pilot 8.5, boss pilot 7.7, standoff
  height 7.0 (band 4–10), outside 87.8 × 67.4 × 27.6 (limit 100 × 70 × 35). The vents are still missing (RC-E, deferred).
- Regression: **E1-01, V1, V2, V3 all rc 0, no failing agent check.** V1: `assy_relation` same 3/3 → both ports on +X,
  `prescore+llm:vote+rank` (iteration 002: −X / +X, judged MINOR). E1-01: opposite 2/1 (split, no constraint),
  arrangement as before. V2: not_stated 3/3. V3: opposite 3/3 → constrained, arrangement as before. Boss pilots 7.7
  everywhere (each regression rubric asks ≥ 6.0).

### Files changed (implementation)
| File | + / − lines (vs code_before) | Why |
|---|---|---|
| assembly.py | +342 / −21 | C0 members, gate, question, sensor wiring; C1 `board_screw_choice`; C2 `pilot_depth`, `clamped_plate`, cavity `z0`, `pilot_bottoming_*`; D1 `crossing_section` in `derive_port_cut` |
| assembly_checks.py | +31 / −1 | `FACE_RELATIONS`, `face_relation` check type; `pilot_bottoming` in `MINIMUM_TYPES` |
| parts.py | +33 / −1 | R9 `thread` field (`INTERFACE_NUMBERS`), `interface_thread`; `Rules.face_relations` / `fastener_roles` loading |
| design_rules.json | +9 / 0 | `face_relations`, `fastener_roles` vocabularies (each with a source) |
| benchmarks/generalize/parts/card_microsd/part.json | new (44 lines) | D1 |
| benchmarks/generalize/parts/rpi_zero2w/part.json | +10 / −2 | D1 `sd` connector and notes; D2 `thread` 2.5 |
| benchmarks/generalize/parts/arduino_uno_r3/part.json | +1 / −1 | D2 `thread` 3.0 |
| benchmarks/enclosure/parts/rpi_pico2/part.json | +1 / −1 | D2 `thread` 2.0 |
| benchmarks/generalize/run_suite.py | +53 / −3 | C3 canonical geometry hash |
| loop/RUN.md | +4 / −1 | section 5: the geometry hash wording (C3) |
| test_assembly.py | +385 / −3 | T1–T7, T9–T11, T13; FakeLLM answers an unscripted `assy_relation` with not_stated; four tests changed on purpose (below) |
| test_parts.py | +69 / 0 | T8, T12 |
| test_generalize_suite.py | +36 / 0 | T14 |
| loop/iter_002/code_before/ | new | revert copy |
| loop/LEDGER.md | this section | — |

### Tests (implementation)
- New tests (all fail or error on `code_before` with the new test files: 14 of 14; run in a scratch copy):
  `test_assembly.TestFaceRelation` (T1 `test_same_end_replay` on iteration 002's recorded V1_s2 answers and p_yes; T2
  `test_gate_enums`; T3 `test_split_vote_is_no_constraint`; T4 `test_unsatisfiable_relation_is_reported`; T5
  `test_prompts_unchanged_without_gate`, against a run with the stage patched out), `TestBoardFastener` (T6 the C1
  table on the ten texts with each `by`; T7 a named screw that does not pass, plus the clause scope), `TestPilotBottoming`
  (T9, T10, T11), `TestCardExposure.test_card_slot_exposed_by_text` (T13; the delta named it TestExposure),
  `test_parts.TestInterfaces.test_thread_field` (T8), `test_parts.TestCardAccess` (T12),
  `test_generalize_suite.TestHashes.test_geometry_hash_is_order_free` (T14). T15: `test_no_hardcoding` green.
- Tests changed because behaviour changed on purpose (each marked "changed in generalize delta 002"):
  `TestExposure.test_primary_connectors_and_multi_connector_parts` (the Zero has 4 connectors; the request sentence
  naming the card is left out), `TestDeriveFeatures.test_one_sided_minimums_have_the_design_margin` (pilot depth target
  includes length − plate), `TestDeriveFeatures.test_minimum_checks_pass_with_margin_and_fail_on_a_mutant`
  (`pilot_bottoming_*` counted; on the mutant the boss's binding minimum is now bottoming),
  `TestReplayIter005.test_replay_iter005_answers_end_to_end` (base volume = iteration 010's minus the deeper boss
  pilots, computed from the pilot polygon and the added depth).
- Full RUN.md 2 suite: first run 440 tests, 4 failures (exactly the four tests above, all from the intended boss pilot
  change); after updating them: see the final line below.
- **Final full RUN.md 2 suite (on the final code): 440 tests, OK (1195 s).** `test_no_hardcoding` green (both
  catalogues scanned; the relation and role words live in design_rules.json).

### Notes for the reviewer / next gap analyst (implementation)
- Review both deviations above (clause-scoped C1 role evidence; quoted gating sentences in the C0 prompt). Both are
  generic and measured; neither reads a design id, name or number.
- D1 changes the Contents prompt wherever the Zero 2 W is a candidate (one more `sd_exposed` key, "takes a microsd
  card"). G50 says "the microSD slot are not used": coverage does not fire (the card's names say card, not slot), but
  the 9B's own Contents vote could still expose it. Watch G50's SD opening in iteration 003.
- Run code for iteration 003 is the repo as left by this step; the iteration 003 run note in RUN.md section 1 still
  holds (all six packages and the regression set must be judged).
- claude-context failed to connect during this step; targeted reads and grep were used.

### Reviewer verdict (delta 002 implementation, adversarial review, 2026-10-25)
**APPROVE (approve = true).** No blocking defect was found. Eight non-blocking findings are listed below for the next
gap analyst. N1 and N2 are the ones most likely to show up on held-out briefs.

How it was checked: claude-context failed to connect (the MCP server did not start), so I used diff and targeted grep.
Nothing under `../holdout/` or `holdout_results/` was opened, listed or searched.
- **Diff against `iter_002/code_before/`.** I read every changed file in full: assembly.py, assembly_checks.py, parts.py,
  design_rules.json, run_suite.py, RUN.md, the three changed part.json files, the new `card_microsd`, test_assembly.py,
  test_parts.py and test_generalize_suite.py. layout.py, feature_graph.py and cad_agent.py are byte-identical.
- **Delta coverage.** C0, C1, C2, D1, D2 and C3 are implemented as delta.md section 4 specifies, and T1 to T15 all
  exist. There are two deviations, and the ledger records both:
  - C1 role evidence is clause-scoped. I accept it. It is generic, and on the ten texts it reproduces the delta's own C1
    table. When it misses, it falls back to the datasheet rule and then to the smallest screw that passes, never to a
    wrong screw. It was tuned on one train sentence (G50 L1.8), so held-out results will show whether that is an
    overfit.
  - The C0 prompt quotes the gating sentences. I accept it. The quotes are sentences Python's gate already selected,
    and the smoke table shows V1 constrained in 5 of 5 seeds and V2 never forced to `same`.
  The `crossing_section` change to `derive_port_cut` is a necessary supporting change for D1. For every centred
  catalogue plug it emits the same expressions as before, and the regression replay below confirms that.
- **Generic.** No design id, train number or part id appears in agent code. The vocabularies live in design_rules.json
  (`face_relations`, `fastener_roles`, each with a source), and the thread data lives in part.json with datasheet
  sources. The rules trigger on part data (mount_holes `thread`, connector `mates`, a fastener's `length`) and on
  sentence or clause text evidence. An unseen brief with the same capability (a stated same or opposite relation, a
  named board screw, a datasheet thread, long screws) gets the same treatment.
- **Full RUN.md 2 suite rerun: 440 tests, OK (1198 s).** `test_no_hardcoding` passes on its own too (3 tests, OK).
- **The new tests fail before the change.** I built a scratch tree with the code_before modules, rules and both
  catalogues and the new test files (holdout not copied or linked), then ran T1 to T14 on it. All 14 fail: 6 with
  assertion failures and 22 errors across subtests. T1 (`test_same_end_replay`) and T9 to T11 fail on real assertions
  about the arrangement and the pilot depths. T5 fails only because `ask_relations` does not exist yet, which is
  acceptable for a guard test. The tests are not circular:
  - T1 and T4 replay iteration 002's recorded V1_s2 answers and p_yes, and those recordings exist, so T1 does not skip.
  - T6 checks the C1 table against each train design's own requirements.
  - T9 to T11 check depths against the screw length and clamped plate taken from the catalogue.
  - T13 checks the aperture, oversize, ligament and coverage results on the built plan.
- **Offline regression invariance rerun** (`scratchpad/inv.py`, the implementer's script, with my own scratch copy of
  code_before; relation answers V1 `same`, E1-01 and V3 `opposite`, V2 `not_stated`). Every run is rc 0 with no failing
  check, before and after.
  - E1-01, V2 and V3 are unchanged in reference poses, fasteners and spec.
  - V1's arrangement changes as intended: (−X, +X) becomes (+X, +X), the Pico rotates 180°, and the decision is
    `prescore+llm:vote+rank`.
  - The only geometry change elsewhere is the four boss pilots: depth 6.1 → 7.7 and h 7.1 → 8.7.
  - The question labels are the same, plus three `assy_relation` samples per text and fewer `assy_confirm` calls where
    the constraint removed classes (E1-01 −5, V1 −6, V3 −3).
  This matches the ledger.

Non-blocking findings (not defects against delta.md; candidates for delta 003 or later):
- **N1: the face-relation gate is per part, not per connector.** For a primary member, the gate tests the primary
  *part's* names. When a multi-connector primary (Zero 2 W, Uno) exposes several connectors and a content item has a
  connector, one sentence such as "the jack on the same side as the Zero's USB" gates a pair for *every* exposed primary
  connector (usb, pwr, sd ...). A unanimous `same` on a connector the sentence does not mean adds a wrong, possibly
  unsatisfiable constraint. Each pair line does name its connector, so the 9B can answer `not_stated`, but nothing has
  measured that. Suggested fix: when a part has more than one exposed member, gate only the members whose mate's
  aliases (or the connector name) also appear in the sentence.
- **N2: the relation filter runs after the `arrange_rank_max` cap.** The constraint is known before the candidate loop
  (`ask_relations` runs inside `candidates()`), but prescore only sees the top 16 assignments in vote order. With 3 or
  more exposed items (64 or more assignments), the assignments that satisfy the relation can be truncated. The package
  then carries a failing `face_relation_*` that looks unsatisfiable when it is not. Suggested fix: move assignments that
  meet every unanimous relation ahead of the cap (Python knows each edge's wall).
- **N3: `other` is broad opposite evidence** ("no other parts", "each other"). The gate only offers the enum, and a
  constraint still needs a unanimous controller reading. The smoke measurement covered only the four regression texts.
- **N4: C1 takes the largest role-named screw, and clause scope still counts lid clauses that mention the board**
  (G11 L1.8 "bosses outside the board's outline"). On a board whose holes pass both screws (Uno class, Ø3.2), a lid M3
  in such a clause would beat an M2.5 that another clause names for the board. No train text has this shape. A fix
  would prefer clauses that name the primary itself, or "through the board" role words, over bare "board".
- **N5: boss pilots have no floor-breakthrough sensor.** Only `pilot_depth_standoff_*` exists. C2 makes boss pilots
  1.6 mm deeper, and longer lid screws make them deeper still. In a low base (split − z0 + floor < depth) the pilot would
  break through the bottom, and no check would see it. A `pilot_depth_boss_*` check like the standoff one would close
  this.
- **N6: the off-axis port cut freezes resolved numbers.** `derive_port_cut` writes `sec['w']`, `sec['h']`, `dt` and
  `dz` into the expressions as numbers, not as node references. That is fine while plug parameters are catalogue
  constants, but it would bring back the size-leak if a plug ever became request-sized.
- **N7: a single valid sample counts as unanimous.** If 2 of 3 samples are invalid, the one valid sample constrains.
  The answers are schema-constrained, so this is rare. Requiring at least 2 valid samples would follow 7.6 literally.
- **N8: cache hits are now real, so their key matters more.** With the canonical hash, unchanged geometry hits the judge
  cache. The key does not cover the package's own design.json or self-report, so a verdict can carry over across
  changed agent records when the geometry is the same. Judges grade geometry, so this is acceptable. Keep it in mind if
  a judge ever grades the records.

> **Workflow restart (2026-10-25, by the orchestrator):** the loop script mis-scored the regression set (the
> regression judge returned ids such as `E1-01_s2`, so they were counted as train designs and E1-01 never counted as
> passing). That explains the "computed task text" corrections in iterations 001 and 002. The script now normalises
> ids. Iteration 003's partial run (12 of 44 designs, same code as delta 002) was moved to `iter_003_aborted_partial/`,
> and iteration 003 restarted from its Run step. No agent code or data changed.

---

## Iteration 003 (2026-10-25): delta 002 measured, gap analysis, delta 003 designed

**Seed:** 3, full train split + regression set (RUN.md 1).
**Code:** `de77b7ab88b1` (sha1 of `iter_003/code_sha1.txt`), code_unchanged false (delta 002, as intended),
runs_on_one_code_version true. `shasum -c` matched every file at gap analysis.
**Run:** 40 train + 4 regression runs (54 rows: the first ten train designs ran twice because the Run step restarted;
both runs used the same code, and every pair agrees in rc, stop and canonical geometry hash). 44.9 minutes of run time over
the 54 rows (24–107 s each), no timeouts. The regression set used the enclosure catalogue only.

### Results
- Train: **MEETS 0 / CORRECT 1 / no-output 33 of 40.** rc: 0 ×3 (G02 G08 G11), 3 ×4 (G04 G06 G13 G50), 1 ×33.
  - Packages, with judge verdict and score:

    | Design | Verdict | Score |
    |---|---|---|
    | G04 | DNM / CORRECT | 0.99 |
    | G02 | WRONG | 0.84 |
    | G06 | WRONG | 0.51 |
    | G08 | WRONG | 0.41 |
    | G11 | WRONG | 0.35 |
    | G13 | WRONG | 0.30 |
    | G50 | WRONG | 0.30 |

  - Stops (from summary.json):
    - contents 28:
      - `nothing to design around` 17: G16 G17 G18 G20 G21 G22 G24 G27 G30 G31 G32 G33 G35 G36 G38 G40 G45.
      - `primary has no mount_holes interface` 6: G03 G05 G09 G10 G12 G47.
      - `no number in the text` 5: G26 G29 G37 G42 G43.
    - choose_archetype 3: G23 G41 G49.
    - arrange_contents 2: G01 G14.
  - Changes from iteration 002 are seed variance in Contents, not code:
    - G08 now gives a package (the cell is not listed).
    - G40 now stops at contents.
    - G42 and G43 now stop on "no number".
- Regression: **pass.** E1-01, V1, V2 and V3 are all MEETS (1.0). V1 is fixed (both ports on −X), as delta 002 forecast.
- Judged this iteration: 11 (7 train + 4 regression), one judge each. Reused from the cache: 0. The regression packages
  changed geometry on purpose (delta 002 boss pilots), so no cache hit was possible.
- **Correction (P-3, loop record).** The orchestrator's `verdicts.json` uses a boolean `meets` and no `verdict` string.
  `run_suite.verdict_flags` reads only `verdict`, so `summary.json` reported regression `fail` and regression meets 0. The
  analyst re-cached `iter_003/verdicts_normalised.json` (the same verdicts plus `"verdict"`; the original file is
  untouched) with `cache_verdicts.py 003`. `summary.json` now says regression `pass`, and train MEETS 0 / CORRECT 1. The
  computed task text's "regression E1-01 MEETS" agrees.
- Delta 002's forecast held:
  - regression fail → pass;
  - G04 CORRECT with only the bbox w1 miss;
  - G02 failed gates 3 → 1;
  - G11 failed gates 3 → 2;
  - board pilots right in every judged package.

### Defects (judges)
- D-BOSS-OUT (G04 L3.11.1.1 w1, its only defect): Y 42.22 > 40, because the corner lid pilasters sit outside the walls.
  The agent sensed it (`bbox` −2.21).
- D-LID-FORM (G02 L3.8.2.x w3, fixed decision F2; G13 L3.8.2.1 w2): lip lid where L1.8 asks for a plate in a wall rebate.
- D-VENT (G02 gate G5 and L3.7.x; G11 gate G5; G50 gate G3 in part): no vent or exhaust slots.
- D-BRIDGE (G02 L3.10.1.1 w2): a flat 16.8 mm roof on the USB-B opening, over the 15.0 bridge limit. Not sensed (78/78
  agent checks pass).
- D-SECONDARY: unplaced or unlisted named parts (G06 Pico; G08 cell, switch, door; G11 fan, heatsink; G13 buttons,
  plungers; G50 fan, OLED, encoder). These cause most of the gate failures.
- Others: G06 and G08 have 4 bosses where the text says 2 (w2). G11's lid is 2.4 thick where the text says 4.8–6 (w3). G06
  has no tilt or window. G50 has no snaps. G13 Z 37.8 > 35 (agent-sensed).

### Gaps (gap analyst)
- D-BOSS-OUT → **RC-F**, a sensor without an actuator. One boss layout exists, and prescore varies only the arrangement.
  → GM3 slice: derive-level boss layouts, plant-scored on failure.
- D-LID-FORM → **RC-G**, missing closure rule and vocabulary. The rebate also needs bosses under the plate (RC-F). → GM9
  first slice.
- D-VENT → **RC-E** (iteration 002), missing capability, plus a missing catalogue region: the Uno has a point `MCU` but no
  footprint or name. → GM4 vent slice + the `zone` interface kind.
- D-BRIDGE → **RC-H**, a rule (`bridge_max`) with no sensor and no derivation term. → GM5 `printable` first slice.
- D-SECONDARY → RC-C (iteration 002) → GM2b, deferred again because alone it moves no verdict (delta.md 3).
- D-CLOSE-COUNT, D-LID-T → deferred to GM2b and GM3 (they move no verdict).
- P-3 → Run tooling (`verdict_flags`). P-1 (`../rubric.md` missing) is still open.
- Benchmark data: no contradiction or impossible band found. G04's bridge exception (20.0) is already in its requirements
  and is consistent with the plug data. No benchmark file changed.

### Delta summary (designed; to be implemented)
`iter_003/delta.md`:
- **C0 (P-3, tooling):** `verdict_flags` and `parse_verdicts` accept a boolean `meets`.
- **C1 (RC-F):** boss layouts `outside_corners` (default, unchanged) / `inside_band_x` / `inside_band_y`, with a 1-D
  interval solve that slides bosses off plug sweeps, cuts and keep-outs. Alternatives are derived on scratch states and
  scored with the prescore error key, only when the default is infeasible or fails a check it affects. Adds the
  `pilot_depth_boss_*` sensor (delta 002 review N5).
- **C2 (RC-G):** the `closures` vocabulary (lip default; rebate on the evidence "rebate"). Rebate geometry: upstand
  `rules.rebate_upstand` 1.5, the plate in the rebate at the sliding fit, flush, bosses on the rebate floor. Sensors
  `lid_fit`, `rebate_upstand`, `lid_flush`, `boss_top_plane`.
- **C3 (RC-E):**
  - `vents` evidence words.
  - The face comes from a named part `zone` (lid over the zone), else from a voted relation to an exposed item (wall,
    `assy_vent_relation`), else a typed note.
  - Sizes come from one voted `assy_vent_spec` mapping over the vent sentences' numbers.
  - A Python solve with setpoints inside the bands.
  - `vent_cut` nodes counted as apertures, sensors `vent_count/width/length/pitch/area/zone` and ligaments.
  - Data D1: `zone` interface kind; the Uno `mcu` zone 35.6 × 7.6 with names atmega328p, atmega and so on.
- **C4 (RC-H):** a `bridge_<cut>` sensor, then a 45° trapezoid roof when it keeps the stated oversize; otherwise flat with a
  typed conflict (G04 HDMI). New `prism` primitive in feature_graph.
- 15 tests (T1–T15), each failing on `de77b7ab88b1` except the guards T4, T7, T11 and T15.
- **Expected:**
  - Train MEETS 0 → 2 (G02, G04), CORRECT 1 → 2.
  - G11 loses gate G5 (still WRONG on the fan). G13 gains the rebate row.
  - Regression unchanged, and its packages are expected to be cache hits.
  - The 33 no-output stops do not change.

### Files changed (gap analysis step; no agent code)
| File | + / − lines | Why (gap id) |
|---|---|---|
| loop/iter_003/delta.md | new | defects → root causes → delta → tests → expected effect → deferred |
| loop/iter_003/verdicts_normalised.json | new | P-3: the verdicts in the RUN.md 5 form, re-cached |
| loop/judge_cache.json, loop/iter_003/summary.json | rewritten by `cache_verdicts.py 003` | P-3: the 11 verdicts re-stored with `verdict`; regression now `pass` |
| loop/ARCHITECTURE.md | +32 / 0 | section 1c: iteration 003 measurement and refinements 1–6 |
| loop/RUN.md | +5 / 0 | section 1: iteration 004 run note (SEED 4, full split, verdict form) |
| loop/LEDGER.md | this entry + progress row | — |

### Tests
- `test_no_hardcoding test_generalize_suite`: **26/26 OK** on `de77b7ab88b1`, run by the analyst. The full RUN.md 2 suite
  result of the Run step's preflight is not recorded in the iteration folder.

### Reviewer verdict
pending (delta not yet implemented).

### Notes for Robin
- No owner questions. Assumptions (derived, not asked):
  - When the text names a rebate, the upstand is 1.5 mm and the plate sits at the sliding fit of 0.25 per side.
    Uncertainty low: G02 and G13 ask for ≥ 1.0 and 0.15–0.35.
  - A vent row "over" a named chip runs along the chip's long axis, with every slot over the chip's length and the slots
    centred across it. Uncertainty medium: a brief could mean slots across the short axis.
  - The ATmega328P footprint is 35.6 × 7.6 at the catalogue's `MCU` point. Uncertainty ±2 mm, as in G02 A4.
  - Silent vent sizes default to 2.0 wide and 10.0 long. Uncertainty medium.
  - When a stated opening oversize and the rules bridge limit cannot both hold, the stated oversize wins and the bridge
    failure is reported as a conflict. Uncertainty low: G04's requirements make the same call.
- `../rubric.md` is still missing (P-1). It should exist before the first held-out measurement.
- claude-context failed to connect during this step. Files were found with targeted reads and grep. Nothing under
  `../holdout/` or `holdout_results/` was opened.

### Delta summary (implemented, delta 003)
Implementer step, 2026-10-25. claude-context failed to connect in this step (the MCP server did not start), so files were
found with targeted reads and grep. Nothing under `../holdout/` or `holdout_results/` was opened, listed or searched.
The pre-change agent modules, `design_rules.json`, every `test_*.py`, both catalogues, `run_suite.py`,
`cache_verdicts.py` and RUN.md are in `iter_003/code_before/` (paths relative to the repo), so the change can be reverted
file by file. All of C0–C4 and D1 are implemented, in the delta's priority order C0 → C1 → C4 → C2 → C3.
- **C0 (P-3, tooling).** `run_suite.verdict_flags` reads `meets` when it is `true`. `cache_verdicts.parse_verdicts`
  accepts `meets` (a bool; anything else is rejected) and stores `"verdict": "MEETS" | "DNM"` next to it when no
  `verdict` is given. RUN.md section 5 says that both forms are accepted.
- **C1 (RC-F) boss layouts.**
  - `BOSS_LAYOUTS` = outside_corners (the iteration 002 pilasters, byte-identical: `add_corner_pilasters`), then
    inside_band_x and inside_band_y.
  - `derive_cavity(st, layout)` grows the cavity by `band = boss_d + spec.board_clearance + rules.design_margin` at both
    ends of the layout's axis.
  - The 1-D interval solve is `inside_boss_positions`:
    - Each boss stands tangent to the end wall and reaches `design_margin` into it. It starts at its band corner and
      slides (`free_slot`) to the nearest free position, towards the band's middle.
    - The forbidden intervals come from every envelope at its KEEP_OUTS clearance, every port cut and roof, the primary
      at `board_clearance` and the other references at `part_to_wall`. Each clearance gets `+ design_margin`.
    - No free position, or two bosses closer than `d + min_ligament`, raises `BossLayoutInfeasible` and adds a note.
  - Inside bosses get no lid pads. Clearance holes go through the plate, and lip notches are kept on the lip closure.
  - The choice is `choose_boss_layout`, called from `derive()`:
    - outside_corners is kept by `rule:default_layout_passes` when the closure allows it and no controllable `bbox` /
      `clear_*` / `inside` failure is boss-affected. `boss_affected` reruns each failing check against the boss solids
      alone.
    - Otherwise every feasible layout runs through the plant on a scratch state, and the strictly smallest error key
      wins (`prescore:derive`). A tie keeps enumeration order.
    - `choices.boss_layout.errors` records each layout's key, failing checks or infeasibility.
  - New sensor `pilot_depth_boss_<k>`: pilot depth ≤ boss h (floor included) − `min_feature`.
- **C2 (RC-G) rebate closure.**
  - `design_rules.json` gets a `closures` block (lip default; rebate evidence "rebate" / "rebated", each with a meaning
    and a source) and `archetypes.tray_lid.lid_words` ["lid"].
  - `closure_choice` is a rule: the rebate closure needs a sentence with both a rebate word and a lid word.
  - Rebate geometry:
    - The base gets `rim = cavity.wall`, and its z grows by the rim.
    - The split drops the lip-engagement term.
    - The lid plate is `base − 2·(rebate_upstand + sliding_fit)` thick `cavity.wall`, at `base.split`.
    - A `rebate` cut `base − 2·rebate_upstand`, `lid.z + cut_overrun` high, leaves the upstand. There is no lip.
    - outside_corners is infeasible, so the bosses end on the rebate floor.
  - New rule `rebate_upstand` = 1.5 (source given).
  - Sensors `lid_fit_x/_y` (band [sliding_fit_min, sliding_fit_max]), `rebate_upstand_x/_y`, `lid_flush`,
    `boss_top_plane_<boss>`.
- **C3 (RC-E) vents.**
  - Vocabulary and slots: `design_rules.json vents` holds the evidence words and the nine size slots, each with a
    meaning and a unit. New rules `vent_slot_width` 2.0 and `vent_slot_length` 10.0 (sources given). New stage `Vents`
    after ArrangeContents.
  - Face resolution:
    - (1) A placed part's `zone` named in a vent sentence: `rule:vent_zone`.
    - (2) Otherwise a voted `assy_vent_relation` over {(exposed member, relation)} + not_stated, quoting the vent
      sentences. Only a unanimous reading counts (`llm:vent_relation`).
    - (3) Otherwise the note `vent: face not resolved (face words only)` and a `vent_placed` check that fails with a
      typed conflict.
  - Sizes: once the face resolves, a voted `assy_vent_spec` maps the vent sentences' unowned numbers. One re-ask
    (`assy_vent_spec_reask`) handles a shared number, lo > hi, a count that is not whole, or a value ≤ 0; slots still
    broken after it fall to none.
  - `vent_solve` is the delta's Python solve. `add_vent_row` builds the slots:
    - Lid rows: one box per slot along the zone's long axis.
    - Wall rows: in the longest free stretch of the wall, after min_ligament ends and the bosses and port cuts on that
      wall are taken out. The height runs from the floor top to the split.
  - `vent_cut` joins `APERTURE_CUT_ROLES`, so slots get ligament checks, and wall slots join their wall's
    `aperture_count`.
  - Sensors `vent_count/width/length/pitch` (stated ends only), `vent_area` (a typed conflict when infeasible) and
    `vent_zone_<zone>`. They are linked to their L1 through the vent slots' `spec_provenance`.
- **D1.** `parts.py` interface kind `zone` (R9: `at` a Point datum, `size` two expressions > 0, `long_axis` a horizontal
  unit vector, non-empty `names`). `zone_reserved_failures` makes LoadRules drop a part whose zone name is an archetype
  evidence word. The Uno gets `mcu` (`MCU`, `mcu_length` 35.6 × `mcu_width` 7.6, long axis +X; names atmega328p,
  atmega328, atmega, microcontroller, mcu; Microchip DIP-28 drawing; ±2 mm position).
- **C4 (RC-H) bridges.**
  - `feature_graph` gains the `prism` primitive (convex polygon `n`, `x1..xn`, `y1..yn`, extruded `h` along local Z;
    the vertex order is normalised to counter-clockwise). It has a SCAD emitter `linear_extrude(polygon)` and a manifold
    emitter `CrossSection.extrude`. Expressions gain `tand()`.
  - `port_roof`: a box opening with `w_o > bridge_max − design_margin` gets a trapezoid roof (top
    `b = bridge_max − design_margin`, rise `(w_o − b)/2 / tand(overhang_angle_deg)`), when
    `pad + rise ≤ opening_oversize_max − design_margin`. Otherwise it stays flat with a typed conflict.
  - The cut's `top` includes the rise. `cut_volume` unions box + roof for the aperture and ligament sensors.
    `oversize_*` of a roofed opening is measured per side about the plug section (`center`).
  - New sensor `bridge_<cut>` for every port cut or wall slot. It reads the roof top width or the flat span, against
    `bridge_max`. Round openings up to `round_hole_exempt_max` are exempt; larger ones are measured by diameter.

**Deviations from delta.md (measured, generic; the reviewer should check all three):**
1. **Boss clearance to port cuts is `design_margin`, not `min_ligament`.**
   - With `+ min_ligament`, G04's −X band (the microSD slot) is 0.3 mm short at the y1 corner: forbidden up to 27.95,
     corner at 27.65. inside_band_x is then infeasible, and G04 stays at bbox −2.21.
   - A boss stands in the cavity, outside the wall cross-section that `ligament_<cut>` measures (the wall's mid-plane).
     The only physical constraint is that the cut's 1 mm overrun must not nick the boss.
   - The plug sweep keeps its `plug_to_opening` clearance. Each opening's ligament check is unchanged and passes.
2. **The vent relation gate is clause-scoped, as delta 002 C1 already was.**
   - G02 L1.9, G11 L1.9 and G50 L1.11 ("no openings other than ... the vents") hold a vent word and "other" (opposite
     evidence) in one sentence. The sentence-level gate would ask G50 a relation question; T10 and section 6 forecast
     none.
   - The clause gate keeps G11 (request "... and exhaust slots line the opposite end wall"; L1.7 "Exhaust slots shall
     line the end wall opposite the jack") and drops the "other than" clauses.
3. **T3 uses a real catalogue part, not a synthetic one.** The Uno's DC jack sits at the −X / y0 corner of the X band
   that G02's rebate needs. A catalogue copy with `jack_centre_y` + 1 checks that the boss follows the data.

**Smoke check** (`run_suite.py --iter 003 --seed 3`, live ornith-1.5:9b, in a scratch repo tree
`scratchpad/impl_003/repo`):
- Setup: the agent modules, design_rules.json, the designs, both catalogues and venv are symlinked. run_suite.py and
  cache_verdicts.py are copied, so `loop/` resolves to the scratch tree. This iteration's real folder was not touched.
- Code hashes: the train invocation recorded `280b11ccc376` and the regression invocation `fff04f7f2a2b`. The only
  change between them is the assembly.py module docstring (the Vents stage line). A scratch-only defect; behaviour is
  identical.
- **G02: rc 0, 104/104 agent checks pass.**
  - Rebate by rule, boss layout inside_band_x by `prescore:derive` (outside_corners infeasible under the rebate;
    inside_band_y bbox Y 75.6 > 70).
  - Outside 96.0 × 61.2 × 28.35 (limit 100 × 70 × 35). boss_1 slides 15.35 mm off the DC plug.
  - USB-B roof: top width 14.9, rise 0.95, top excess 1.35 ≤ 1.5.
  - Lid vent row over the mcu zone: 7 slots, 2.0 × 10 at pitch 5.0, 140 mm².
  - The 9B mapped 7 of 9 vent slots; width_min and length_min fell to the rules defaults, both inside the stated
    bands.
- **G04: rc 3.** The only failing check is `bridge_board_hdmi_cut` with its typed conflict (17.8 wide; a roof would rise
  1.45 and leave the top 1.85 above the plug). G04's requirements accept 20 there. inside_band_x by `prescore:derive`,
  outside **85.40 × 36.90 × 19.00** (was 77.32 × 42.22; limit 90 × 40 × 22; delta forecast about 85 × 37 × 19).
- **Regression E1-01, V1, V2, V3: rc 0 each, no failing agent check.** outside_corners by
  `rule:default_layout_passes`, lip. **The canonical geometry hash equals iteration 003's for all four** (a93f14f30874,
  e3a1f64a30cb, 39b5eb4c1d91, ec56b723f032), so they will be cache hits.
- Offline G11 with a scripted "opposite": 10 slots, 3 × 24.3 on +X (the jack is on −X), 729 mm². All checks pass.
- Offline G50: vent_placed fails with a conflict, and no vent question is asked.

### Files changed (implementation, delta 003)
| File | + / − lines (diff vs code_before) | Why |
|---|---|---|
| assembly.py | +992 / −49 | C1 layouts, band, interval solve, choice, `pilot_depth_boss_*`; C2 closure rule, rebate geometry and sensors; C3 Vents stage, `vent_solve`, rows, sensors; C4 `port_roof`, `cut_volume`, `bridge_*`; wall cuts in apertures and ligaments; zone-name gate in LoadRules |
| assembly_checks.py | +44 / −4 | `VALUE_CHECKS` / `value_check` (bridge, lid_fit, rebate_upstand, lid_flush, boss_top_plane, vent_*), `vent_placed`, per-side `aperture_oversize(center=...)` |
| feature_graph.py | +36 / −3 | `prism` primitive (manifold + SCAD), `tand` |
| parts.py | +91 / −2 | `zone` interface kind and R9 checks, `zones`, `zone_geometry`, `zone_reserved_failures`; `Rules.closures`, `Rules.vents` |
| design_rules.json | +28 / −4 | rules `rebate_upstand`, `vent_slot_width`, `vent_slot_length`; `closures`; `vents`; `tray_lid.lid_words`; `face_relations.*.wall_meaning` |
| benchmarks/generalize/parts/arduino_uno_r3/part.json | +10 / −2 | D1: `mcu_length`, `mcu_width`, the `mcu` zone, notes |
| benchmarks/generalize/run_suite.py | +3 / −2 | C0 |
| benchmarks/generalize/cache_verdicts.py | +11 / −4 | C0 |
| loop/RUN.md | +4 / 0 | section 5: both verdict forms (C0) |
| test_assembly.py | +459 / 0 | T2–T12; FakeLLM answers unscripted vent questions none / not_stated (marked "changed in generalize delta 003") |
| test_parts.py | +33 / 0 | T14 |
| test_feature_graph.py | +67 / 0 | T13 (+ prism orientation and bad-prism tests) |
| test_generalize_suite.py | +31 / 0 | T1 |
| test_no_hardcoding.py | +2 / −1 | the geometry vocabulary now includes `prism` (marked "changed in generalize delta 003") |
| loop/iter_003/code_before/ | new | revert copy |
| loop/LEDGER.md | these three sections | — |

### Tests (implementation, delta 003)
- New tests:
  - `test_generalize_suite.TestVerdicts.test_boolean_meets_form` (T1).
  - `test_assembly.TestBossLayout`: `test_size_limit_moves_bosses_inside` (T2, the iteration 003 G04_s3 replay: bbox
    passes, inside band, bosses ≥ board_clearance from the board, every clear_* passes); `test_band_slides_past_plug_sweeps`
    (T3); `test_default_kept_when_passing` (T4 guard: E1-01 to V3 replays derive iteration 003's exact
    `feature_graph.json` and layout, outside_corners by rule, no scratch plant run in DeriveFeatures);
    `test_boss_pilot_floor_sensor` (T5).
  - `TestRebate`: `test_rebate_closure_from_text` (T6), `test_no_evidence_keeps_lip` (T7 guard).
  - `TestVents`: `test_zone_row_in_lid` (T8: 7 slots, 2.25 × 10, pitch 5.0, in the zone, linked to L1.7);
    `test_wall_row_opposite_exposed_item` (T9); `test_unresolved_face_is_typed` (T10);
    `test_prompts_unchanged_without_vent_words` (T11 guard: labels and prompts equal iteration 003's).
  - `TestBridge`: `test_wide_opening_gets_roof`, `test_roof_yields_to_oversize` (T12).
  - `test_feature_graph.TestPrism`: `test_prism_parity` (T13, OpenSCAD), plus orientation and rejection tests.
  - `test_parts.TestInterfaces.test_zone_kind` (T14). T15: `test_no_hardcoding` green.
- The new tests were **not run against `code_before`** in this step. The capability tests call symbols, rules and
  catalogue data that code_before lacks (`A.INSIDE_LAYOUTS`, `pt.zones`, the `prism` primitive, `rules.vents`), so they
  error there by construction. The guards T4, T7 and T11 compare with iteration 003's recorded packages and prompts.
  The reviewer may confirm with a scratch copy.
- No existing test changed behaviour. The two tests changed on purpose are marked "changed in generalize delta 003":
  - `test_no_hardcoding`: the vocabulary now includes `prism`.
  - `test_assembly.FakeLLM`: unscripted vent questions are answered.
  - No test counted the new `bridge_*` / `pilot_depth_boss_*` ids in a way that broke.
- **Final full RUN.md 2 suite: 457 tests, OK (1467 s).** `test_no_hardcoding` green: every new word lives in
  design_rules.json and every new number in rules or part.json.

### Notes for the reviewer / next gap analyst (implementation, delta 003)
- Review the three deviations above.
- Prescore calls `derive()`, so an arrangement candidate that fails a boss-affected check scores the inside layouts too.
  In V3 this happened for several prescore candidates. The accepted arrangement and its feature graph are unchanged
  (T4), but the prescore keys of failing candidates now reflect the best boss layout.
- With the lip closure, an inside band along a connector's wall puts the plug overmold inside the cavity, under the lip.
  `clear_*_plug` senses it, and that layout loses (G04 inside_band_y). A lip notch over plug sweeps would be a later
  refinement.
- Iteration 004 forecast unchanged from delta.md section 6: G02 and G04 MEETS expected (the G04 bridge conflict is
  accepted by its requirements), G11's gate G5 should pass, G50 gets the typed vent note, and the regression packages
  should be cache hits.
- claude-context failed to connect during this step; targeted reads and grep were used.

### Reviewer verdict (delta 003 implementation, adversarial review, 2026-10-25)
**APPROVE (approve = true).** I found no blocking defect. Eight non-blocking findings are listed below for the next gap
analyst. N1 and N2 are the ones most likely to cost a held-out design.

How it was checked: claude-context failed to connect (the MCP server did not start), so I used diff and targeted grep.
Nothing under `../holdout/` or `holdout_results/` was opened, listed or searched.
- **Diff against `iter_003/code_before/`.** I read every changed file: assembly.py (+992/−49), assembly_checks.py,
  feature_graph.py, parts.py, design_rules.json, the Uno part.json, run_suite.py, cache_verdicts.py, RUN.md and the five
  test files. No other module or catalogue file changed.
- **Delta coverage.** C0 to C4 and D1 are implemented, and T1 to T15 all exist. The three recorded deviations are
  accepted:
  - (1) The boss clearance to port cuts is `design_margin`, not `min_ligament`. I accept it because the forbidden
    interval is taken from the cut's AABB, and that AABB includes the 1 mm cavity overrun. The boss therefore never nicks
    the cut, and each opening's own ligament check (taken at the wall mid-plane) is unchanged and passes.
  - (2) The vent relation gate is clause-scoped. It is generic and consistent with delta 002 C1.
  - (3) T3 uses catalogue data. It is stronger than a synthetic case, because moving `jack_centre_y` by +1 moves the
    boss by exactly 1.
  - One deviation is **not recorded**. Delta C3 says "the cross-stage owner question of delta 001 C3 applies".
    `Vents.ask_sizes` simply never offers owned numbers, and no owner question runs (see N5).
- **Generic.** No design id, train number or part name is in agent logic. The only hits are docstrings, which mention
  the G04 card-slot measurement behind deviation 1. All vocabulary (`closures`, `vents`, `lid_words`, `wall_meaning`) and
  all new numbers (`rebate_upstand`, `vent_slot_width`, `vent_slot_length`) are in design_rules.json with sources. The
  ATmega footprint is in part.json with a datasheet source. Every trigger is part data (a `zone` interface), a text
  evidence word, or plant error (the boss layout).
- **Full RUN.md 2 suite rerun: 457 tests, OK (1426 s).** `test_no_hardcoding` passes on its own too (3 tests, OK).
- **The new tests fail before the change.** I built a scratch tree with the code_before modules, rules and both
  catalogues, the current test files, and links to the designs and `iter_003` (holdout not copied or linked). Then I
  ran T1 to T14 on it: 23 cases, 2 failures and 21 errors, so every one fails.
  - T2 fails on the real assertion, reproducing iteration 003's bbox 77.32 × 42.22 > 40.
  - T1 fails on the real assertion: the boolean MEETS is scored DNM.
  - The rest fail on missing capability (no `prism`, `zones`, `rules.vents`, `REBATE` or `plant_error`), which is
    acceptable for capability tests.
  - The guards are not circular. T4 compares the derived graph with iteration 003's recorded `feature_graph.json`, and T11
    compares the prompts with the recorded transcripts.
- **Independent geometry check** (`scratchpad/rev003/geo.py`, `geo2.py`; offline, recorded and scripted answers).
  - G02:
    - Rebate closure by rule, `inside_band_x` by `prescore:derive`, 0 failing checks.
    - Closed size 96.0 × 61.2 × 28.35. Base ∩ lid = 0.
    - I measured the USB-B opening on the manifold solid at the wall mid-plane: 16.6 wide just below the roof, **14.90
      wide at the roof top**, centred on the plug axis (Y 38.10), and solid 0.1 above. The roof is real geometry, not
      only the `b` param that `bridge_*` reads.
    - The plate overlaps the rebate floor by 0.65 per side and sits on the four boss tops, matching G02 F2 and L2.8.2.
      The 7 lid slots lie inside the requirements' V-VENT rectangle.
  - G04:
    - `inside_band_x`, closed size 85.40 × 36.90 × 19.00. The lip notches clear the inside bosses (base ∩ lid = 0).
    - Only `bridge_board_hdmi_cut` fails, with its typed conflict.
  - G11 (scripted `opposite`): 10 slots, 3 × 24.3, on +X, opposite the −X jack. Area 729, 0 failing checks.
  - G13: rebate with `inside_band_x`. Closed Z is now 35.7 (was 37.8) because the rebate drops the lip-engagement term.
    The remaining failures are bbox Z and the existing grid conflict.
  - The regression set is covered by T4 (exact feature graph, `outside_corners` by rule, no scratch derivation) and T11
    (identical prompts). Both pass in the suite.

Non-blocking findings (not defects against delta.md; candidates for delta 004 or later):
- **N1: a rebate text with no feasible inside layout now gives no package.** `choose_boss_layout` raises "no feasible lid
  boss layout", and `derive` fails. Before this change the same text produced a lip-closure package. This also applies to
  every prescore candidate, so the arrangement can fail as a whole. No train design hits it (G02 and G13 are feasible).
  Suggested fix: fall back to the default closure, with a typed `closure` conflict check.
- **N2: wall vent slots run up behind the lid lip.** The slot top is `split − min_ligament`, but the lip hangs to
  `split − lip_engagement setpoint` (2.1). On G11, the top 0.6 mm of each 24.3 mm slot faces the lip across a 0.25 mm
  gap. `vent_area` counts the full slot, and no sensor sees the blockage. Suggested fix: with the lip closure, end wall
  slots at `split − engagement − min_ligament`.
- **N3: wall-row ligaments are derived at the limit, not at the setpoint.** The ends, top, bottom and pitch floor all use
  `min_ligament`, not `setpoint(min_ligament)` (ARCHITECTURE 7.7/7.9). On G11 the slot bottom is exactly 1.5 above the
  floor top. The checks pass at tolerance, but there is no margin. The delta specified `min_ligament`, so this is not a
  deviation.
- **N4: `vent_solve` reports a false pitch conflict.** Width starts at the middle of its band. If `w_mid + min_ligament
  > pitch_max`, the solve returns a conflict without trying a narrower width that is still in the band. Probe: width 2–4
  with pitch ≤ 4 gives a conflict, although width 2 and pitch 3.5 fit. No train design hits it.
- **N5: the cross-stage owner question was not implemented** (the unrecorded deviation above). A vent number that
  ParseSpec wrongly gave to a spec slot is never offered to the vent question, so that vent band falls to none. G02's
  iteration 003 ownership shows no such steal, so the forecast is unaffected.
- **N6: the vent sensors are graph data.** `lid_fit_*`, `rebate_upstand_*`, `lid_flush`, `vent_count/width/length/pitch/
  area` and `bridge_*` read resolved params, and the first three hold by construction. Only the generic opening sensors
  measure solids: `ligament_*`, `apertures_*`, and `oversize_*` (per side). I checked the roof geometry by hand above. A
  measured bridge or slot sensor (a slice of the wall or lid) would make these real error signals.
- **N7: a zone match wins over a stated wall.** A vent sentence that names a zone word ("mcu", "microcontroller") for a
  different reason, for example "slots in the end wall, away from the microcontroller", gets a lid row over the zone and
  no relation question. This is the delta's order. Watch for it on held-out briefs.
- **N8: data nit.** The Uno `notes` still give the MCU position as ±8 mm and recommend a row of at least 40 mm, while the
  new zone source says ±2 mm (G02 A4). One of them should be corrected.

---

## D1 re-architecture (2026-10-25): the controller architecture designed, migration delta R01 implemented

Between iterations 004 and 005 (iteration 004 ran on delta 003's code; its gap analysis is not in this ledger yet).
**Owner decision:** D1 (`OWNER_DECISIONS.md`): the small local LLM is the controller; Python is the plant, the sensors,
the actuators and the guardrails; semantic rules are forbidden. **Design:** `ARCHITECTURE.md` section 10 (new; section 0
principle 1 and section 9 point at it). **Delta:** `iter_R01/delta.md`. **Revert:** `iter_R01/code_before/` holds every
file R01 changed as it was; all 76 files of `iter_004/code_sha1.txt` match it byte for byte (sha1), and R01's new files
(`controller.py`, `controller_rules.json`, `test_controller.py`, `test_controller_authority.py`,
`loop/launch_config.json`, `loop/iter_R01/`) are deleted to revert. **Code after R01:** `46b9530eac79` (the sha1 of the
listing `run_suite.py` writes; 78 files). claude-context failed to connect; targeted reads and grep were used. Nothing
under `../holdout/` or `holdout_results/` was opened; no commit.

### What changed (every change classified; details in iter_R01/delta.md section 3)
- **Controller** (`controller.py`, new): `ControllerLoop` after DeriveFeatures: the proposal's first manifold build, the
  typed error vector, one voted `assy_control` question per step over a typed action menu, the action applied on a fork
  of the checkpoint of the stage it invalidates (stage checkpoints in assembly.py), kept only when the controllable error
  does not rise beyond the trust region, feedback on undone and infeasible steps, budget / trust region / menu sizes in
  `design_rules.json`; `controller_trace.json` per package; a per-run question cache (a re-run stage's repeated question
  is not asked twice). Classes: controller-information, actuator, guardrail, plant.
- **Sensors**: `error_vector` over the existing checks (requirement, where, deficit, direction, controllable,
  actionable).
- **Semantic rules converted**: `rule:text_coverage` and `rule:coverage_infeasible` → the controllable `text_coverage`
  sensor + `expose`; `rule:text_evidence[closure]` → the `closure_evidence` sensor + `set_closure`. A sensor whose every
  action is infeasible is typed as a requirement conflict.
- **Registry** `controller_rules.json` + `test_controller_authority.py`: 29 rule names in the code (20 plant, 4 guardrail,
  5 semantic pending: R02 stack, R03 board and lid fasteners, R04 vent zone, R07 archetype gate), 4 retired.
- **Authority probe** `cad_agent.py --controller stub`; **Run tooling** `run_suite.py --paraphrase K` and
  `--controller stub` (summary `paraphrase`, `stub_verified`, `llm_dependent`, `stub`, `controller`; cache key `|pK`),
  `cache_verdicts.py` (paraphrase key, refuses stub rows), `loop/launch_config.json`, RUN.md.

### Measured
- Offline: with the 9B's real Contents answer (USB closed), the controller's `expose` gives byte-identical feature graphs,
  layouts and canonical meshes to the pre-R01 path on E1-01, V1, V2 and V3.
- Live (ornith-1.5:9b): seed 4, the regression set: `expose module_1.usb` A 3/3 on each, kept, rc 0, canonical geometry
  identical to iteration 004's judged MEETS packages (cache hits expected). Seed 3, train: G02 `expose board.dc` then
  `set_closure rebate` (both 3/3, kept, every check passes); G13 the same two corrections (bbox Z and the grid conflict
  remain, as before); G04 and G50 needed no correction. Seed 5 on paraphrase 2 (iteration 005's wording): G02 three
  kept corrections (rebate 2:1 over stop, then both plugs 3/3), every check passes; G13 the same two corrections as on
  wording 0. Of 39 controller samples, 38 chose the correction.
- Tests: the full RUN.md 2 suite (now with `test_controller test_controller_authority`): **492 tests, OK (1658 s)** on the R01 code (457 before R01 + 9 tooling + 18 controller + 8 authority), `test_no_hardcoding` green with `controller.py` scanned; the four modules edited after that run started (`test_controller`, `test_controller_authority`, `test_generalize_suite`, `test_no_hardcoding`) re-run on the final files: 62 tests, OK.

### Notes for the next gap analyst / Robin
- The next Run has three commands (`launch_config.json`): train on wording K = iteration mod 3 (iteration 005 → K = 2),
  regression, stub train. A K > 0 train package is never a cache hit for a verdict given on another wording, so every
  train package with output is judged; the regression packages should be hits.
- `stub_verified` is 0 by construction at R01 (every Contents quantity's first option is 0); read the per-run authority
  audit (`summary.json` `controller`) for the five pending semantic rules until R05.
- Owner questions: none. Assumptions: budget 6, trust region 0.05, 6 error terms, 8 actions (iter_R01/delta.md 10).

### Reviewer verdict (migration delta R01, adversarial review, 2026-10-25)
**APPROVE (approve = true).** I found no blocking defect. R01 does what `iter_R01/delta.md` and ARCHITECTURE.md 10.8
say, adds no semantic rule, gives the controller more authority, and leaves the regression set byte-identical whenever
the 9B picks the correction. Five non-blocking findings are below. F1 and F2 matter most for generalization.

How it was checked: claude-context failed to connect (the MCP server did not start), so I used diff and targeted grep.
Nothing under `../holdout/` or `holdout_results/` was opened, listed or searched. `benchmarks/heldout.json` and
`.mcp.json` were not touched, and nothing was committed. No live LLM run: another llama-server process was resident.
- **Diff against `iter_R01/code_before/`.** Only these files changed: assembly.py, assembly_checks.py, cad_agent.py,
  design_rules.json, test_assembly.py, test_generalize_suite.py, test_no_hardcoding.py, run_suite.py, cache_verdicts.py,
  ARCHITECTURE.md and RUN.md. The new files are controller.py, controller_rules.json, test_controller.py,
  test_controller_authority.py and launch_config.json. I read all of them. Every other module and every part.json is
  unchanged. The code listing hashes to `46b9530eac79` with 78 files, as the delta claims.
- **Delta coverage.** Items (a) to (g) are all implemented: the loop, checkpoints, question cache, trace and authority
  audit; the error vector; the text_coverage and closure conversions; the registry and its test; the stub; paraphrase
  and stub runs; and the launch config. The two retired rule names are gone from the code, and `ArrangeContents.revert_coverage` is removed.
- **No semantic rule, authority not reduced.**
  - Before R01, `rule:text_coverage` overrode the Contents vote. Now the vote stands. The text reading is a
    controllable failing check, and the LLM can answer `expose` or `stop`.
  - `closure_choice` reads no text. It takes the controller's `set_closure` or the plant default (`rule:default_closure`,
    registered as plant).
  - The new `rule:*` names are `[stack]` and `[lid]`. They split the old shared name and stay `pending_migration`
    (R02, R03), as is honest.
  - The registry classifications hold up: `primary_reference` as plant; `only_feasible` as semantic, pending R07;
    `prescore`, `hole_column_d`, `bridge_roof` and `fixed_by_primary` as guardrails.
  - The menu, prompt and acceptance logic contain nothing that picks a meaning. `buildable_closures` lists plant
    capability (what derive can build), not a reading of the text.
- **Generic.** controller.py holds no design id, part, face or number. Its four new values are in design_rules.json
  with sources, and test_no_hardcoding now scans controller.py. The sensors and actuators are keyed on check types and
  catalogue `mates` data.
- **Correctness spot checks.**
  - Snapshots share `placed`, `catalog`, `rules` and the graph's nodes. Downstream stages only add graph nodes. The one
    in-place node edit, `port_roof`, touches a cut node that derive creates in the same call, so no fork leaks into the
    kept state.
  - `QuestionCache` keys on label, prompt, schema, temperature, seed and system. `tally` passes seed = sample index, so
    the samples of a vote stay distinct. Re-asks carry the violation in the prompt, so the cache never freezes a retry.
  - An infeasible action re-measures the unchanged design before the next comparison, so both sides are typed the same
    way.
  - ChooseStack does not read exposure, so re-running from `arrange` after `expose` is sound.
- **Tests: full RUN.md 2 suite rerun, 492 tests, OK.** That is 358 in 152 s plus test_assembly's 134 in 1488 s.
  `test_no_hardcoding` and `test_controller_authority` are green.
  - The new tests are not circular. The controller tests script `assy_control` explicitly, including stop, infeasible,
    undo and budget cases. Regression invariance compares two independent paths.
  - The authority scanner has a non-vacuity test. The changed tests are marked in the files, and each change follows
    from the migration.
  - T11 was loosened from an exact prompt sequence to "every recorded prompt is asked again, and the only extras are
    the controller's and the first pass's arrangement". The re-run arrangement justifies this.
- **E1-01.** There is no regression. The offline invariance test and the delta's live seed-4 run both show iteration
  004's judged geometry.

Non-blocking findings (for the next gap analyst; none is a defect against delta.md):
- **F1: the closure sensor is still a word list, so R01 moves authority but not robustness for closure.** I reworded
  G02 L1.8, replacing "rebate" with "recess", "step", "ledge" or "inset". `closure_text_evidence` returns {} every
  time: no closure_evidence check, no controller question, lip. That matches pre-R01 behaviour, so nothing regresses,
  but it fails D1's paraphrase goal, and the R01 paraphrases kept the technical word. Suggestion: show the controller
  the lid sentence(s) with the buildable closures and their `meaning`. The sensor should not need to recognise the word
  first; the plant feasibility and the error stay Python's.
- **F2: the controller's measured choices cannot yet be told apart from position bias.** Every menu lists the
  sensor's corrections first and `stop` last, and 38 of 39 live samples chose the first correction. Before R02 builds on
  this result, add a probe: a shuffled menu order, and a deliberately wrong sensor reading the controller should refuse.
- **F3: the stub probe is degenerate.** The delta's section 8 says so already. `stub_verified` is 0 by construction
  until R05, so the D1 bar "stub ≤ 25%" must not be counted as met before then.
- **F4: the closure and coverage sensors also judge acceptance.** The same word or alias reading that offers the action
  also scores it, through the error key. A wrong reading can therefore only be declined (`stop`), never argued. This is
  inherent in the D1 sensor pattern. It is acceptable now but worth watching in the traces.
- **F5: the loop's exception set is narrow.** It catches ValueError, KeyError, ExprError and PartError. Any other
  exception from a re-run stage or the manifold build would propagate, although the docstring says the loop "never
  fails the tree". Consider catching broadly and typing the action as infeasible.
