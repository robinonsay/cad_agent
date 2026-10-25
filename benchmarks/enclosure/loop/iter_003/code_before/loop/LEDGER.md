# LEDGER: enclosure control loop

This ledger has one entry per iteration, newest at the bottom, and is append-only. Do not rewrite
past entries. If an entry was wrong, add a correction note in the next entry.

Each iteration of the loop works like this:

1. **Run**: the Run step runs the local-LLM agent per `RUN.md`. This is the only step that uses
   Ollama.
2. **Judge**: a capable model, never the local model, judges each package blind per
   `../rubric.md`. It writes `judge.md` and `defects.json` next to the package.
3. **Gap analysis**: a new agent maps the defects to gaps in the agent and to milestones in
   `ARCHITECTURE.md`.
4. **Delta design and implementation**: the delta is implemented, and the tests are run.
5. **Review**: a reviewer approves or rejects the delta.

The loop stops only on convergence: E1-01 MEETS on 3 seeds, and V1, V2 and V3 are each at least
CORRECT on 1 run, with `test_no_hardcoding` green (rubric section 7, ARCHITECTURE.md section 8).

Folder per iteration: `iter_NNN/` holds `inputs/`, `runs.jsonl`, `<name>_s<SEED>/` (run.log, the
timestamped package, `judge.md`, `defects.json`), and optionally `gaps.md` and `review.md`.

`baseline_code/` holds a snapshot of the agent's code before the loop started, with `SHA1SUMS`.
It is the reference for "files changed" in iteration 001.

---

## Progress table (one row per iteration; append as you go)

| Iter | Seed | Mode run | E1-01 verdict / class | E1-01 score | E1-01 worst w3 margin | V1 | V2 | V3 | Gate fails (E1-01) | Defects G/3/2/1 (E1-01) | Milestone reached | Tests | Review |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 001 | 0 | cascade baseline | DNM / WRONG (both judges) | ~10% (judge 2 estimate) | n/a (no cavity, no openings) | not run | not run | not run | G0 G1 G2 G3 G4 G5 | not reported per weight; all 12 L1s fail | M0+M1+M2+M3 implemented | 248/248 | pending |
| 002 | 0 | cascade baseline (judged) + assembly smoke arm (rc 1, stub) | DNM / WRONG (both judges) | 22% raw, ~0 real (judge 1); ~5% (judge 2) | undefined (no cavity, no standoffs) | not run | not run | not run | G0 G1 G2 G3 G4 G5 | not reported per weight; all 12 L1s fail (byte-identical to iter_001) | walking skeleton: M4 + M5 subset + M7 + M8 (tray+lid, screws) + M12 + ParseSpec-lite/Contents/ChooseStack | 292/292 | pending |

Cell conventions: verdict `MEETS` / `DNM` (does not meet), class `CORRECT` / `MINOR` / `WRONG`;
score = Σ(weight × pass)/Σ(weight) as a percentage; worst margin = normalised (rubric section 4);
variants as class only; tests as `passed/total`; review as `APPROVE` / `REJECT`.

---

## Entry format (copy this block for each iteration)

```markdown
## Iteration NNN (YYYY-MM-DD)

**Seed(s):** SEED (plus confirmation seeds, if any)
**Mode run:** cascade baseline | assembly | assembly + with_models arm
**Code state:** SHA1 of cad_agent.py / cascade.py / cad_checks.py / assembly*.py / parts.py / feature_graph.py at run time

### Runs
| Request | Seed | rc | Status | Minutes | Package |
|---|---|---|---|---|---|
| E1-01 | | | verified / unsatisfied / failed / timeout(124) / crashed | | iter_NNN/E1-01_sSEED/<timestamp>/ |
| V1 | | | | | |
| V2 | | | | | |
| V3 | | | | | |

### Judge verdicts (from each judge.md)
| Request | Verdict | Class | Score | Worst w3 margin | G0 | G1 | G2 | G3 | G4 | G5 |
|---|---|---|---|---|---|---|---|---|---|---|
| E1-01 | MEETS / DOES NOT MEET | CORRECT / MINOR / WRONG | % | | P/F | | | | | |

### Defect count by severity (from each defects.json; UNVERIFIED counts as FAIL)
| Request | Gate | Weight 3 | Weight 2 | Weight 1 | of which UNVERIFIED | Observations |
|---|---|---|---|---|---|---|
| E1-01 | | | | | | |

Change since the previous iteration: +/- per column for E1-01; any defect that came back
(regression) is listed by L3 id.

### Gaps (gap-analysis agent)
One line per gap, most severe first:
- `G-NNN-1` (L3 ids: L3.x.y.z, ...; body/feature; measured vs needed) → agent capability missing or
  broken → ARCHITECTURE.md section / milestone (Mk)

### Delta summary (delta-design agent)
- What was designed and built this iteration, in 3–8 bullets, each tied to a gap id.
- Architecture changes (ARCHITECTURE.md sections edited, and why).
- RUN.md changes (if the CLI changed).

### Files changed
| File | + / - lines | Why (gap id) |
|---|---|---|

### Tests
- Command: `venv/bin/python -m unittest test_cascade test_cad_checks test_review_fixes test_cad_agent test_benchmark_runner <new test modules>`
- Result: N passed / M total, time
- New tests: names, and what each pins down
- Changed tests: `test_name`: one-line justification (behaviour intentionally changed). Never weakened to pass.
- Hard-coding guard (`test_no_hardcoding`): pass / fail

### Reviewer verdict
APPROVE | REJECT. Reasons in 1–5 bullets: correctness, no hard-coding, no weakened test, existing
modes intact, RUN.md current. A REJECT lists what must change; the next iteration starts from it.

### Convergence status
not converged | E1-01 MEETS on k/3 seeds; variants CORRECT: V1 ?, V2 ?, V3 ?
(with_models arm, if run: reported here separately, never mixed in)

### Notes for Robin
Assumptions the judge or agents questioned (requirements.md section 3), or requirements that seem
wrong. These are reported, never relaxed.
```

---

## Entries

<!-- Iteration 001 goes here. iter_000 is not used; the first Run (cascade baseline) is iteration 001. -->

## Iteration 001 (2026-10-24)

**Seed(s):** 0 (greedy)
**Mode run:** cascade baseline
**Code state at run time:** cad_agent.py 805c5017, cascade.py 278b3829, cad_checks.py a3879d40 (the working tree, including Robin's uncommitted x10 retry caps; equal to `baseline_code/SHA1SUMS`). assembly*.py / parts.py / feature_graph.py did not exist yet.
**Code state after this delta:** cad_agent.py fe653f6f, cascade.py 278b3829 (unchanged), cad_checks.py a3879d40 (unchanged), assembly.py 0583e398, parts.py 49742fdc, feature_graph.py 2e133426.

### Runs
| Request | Seed | rc | Status | Minutes | Package |
|---|---|---|---|---|---|
| E1-01 | 0 | 124 | timeout(124) | 90.2 | iter_001/target_s0/20261024-035938/ |
| V1 | | | not run | | |
| V2 | | | not run | | |
| V3 | | | not run | | |

### Judge verdicts (from judge_1.json and judge_2.json)
| Request | Verdict | Class | Score | Worst w3 margin | G0 | G1 | G2 | G3 | G4 | G5 |
|---|---|---|---|---|---|---|---|---|---|---|
| E1-01 (judge 1) | DOES NOT MEET | WRONG | not reported | n/a | F | F | F | F | F | F |
| E1-01 (judge 2) | DOES NOT MEET | WRONG | about 10% | n/a | F | F | F | F | F | F |

### Defect count by severity
| Request | Gate | Weight 3 | Weight 2 | Weight 1 | of which UNVERIFIED | Observations |
|---|---|---|---|---|---|---|
| E1-01 | G0–G5 all fail | not reported per weight | not reported per weight | not reported per weight | judge 2: 1 | One 12-triangle slab, 90 x 74 x 4 (box 90 x 70 x 4 plus a 90 x 4 x 4 "lid" strip fused on its +Y face). 1 shell, cavity volume 0, no walls, standoffs, openings, lid, layout.json or self-report. Judge 1 lists 9 defects, judge 2 lists 12 L1 rows (11 FAIL, 1 UNVERIFIED). |

Change since the previous iteration: none (first iteration; this is the starting error signal).

### Gaps (gap-analysis agent, `iter_001/delta.md` section 2)
- `G-001-1` (L3.2.1.2, 3.2.2.x, 3.3.x, 3.5.x, 3.6.x, 3.8.x; base; cavity 0 vs a cavity for the board, 0 openings vs 3) → the representation is a flat list of additive primitives on outside faces: no cuts, shells, interior poses or datums → ARCHITECTURE.md 3.2 / M2 + M3
- `G-001-2` (L3.7.1.x, 3.9.2.1, 3.7.2–3.7.4; lid; 1 fused body vs 2 separate bodies) → no concept of a printed body; one model.stl → ARCHITECTURE.md 3.2 "Bodies" / M3, M12
- `G-001-3` (L3.1.x, L3.12.1.2; layout; no catalogue, no datums) → `parts/` empty, no loader → ARCHITECTURE.md 3.1 / M1
- `G-001-4` (L3.2.x, 3.4.x, 3.10.1.1; outer Z 4.0 vs about 22) → the size leak: `AccountForNumbers` puts request numbers into some parameter, nothing derives the cavity from its contents → M2 (expressions), M8
- `G-001-5` (L3.12.1.1, 3.12.2.1; package) → no writer for base.stl / lid.stl / layout.json / self_report → M12
- `G-001-6` (G0 timeout, every UNVERIFIED) → the error signal has no clear_of / inside / aperture / separable / seated checks, and the cascade spent 90 min translating L1.1 → M5, M10

### Delta summary (implemented this iteration: M0 + M1 + M2 + M3)
- **C0 / M0 (G-001-1..5 foundation):** `cad_agent.py --mode assembly` (alias `enclosure`), which needs `--l1` like cascade, plus `--parts`, `--rules` and `--with-models`. `Design.assy` and `design.json["assembly"]`. New `assembly.py` with `AssemblyState` and the tree `LoadCatalog → LoadRules → NotImplementedStage("parse_spec")`, which exits 1 with a typed stage. `benchmarks/run.py` accepts `--mode assembly` and requires L1s for it. New `test_no_hardcoding.py` (AST guard plus the guard of the guard).
- **C1 / M1 (G-001-3):** 11 catalogue parts in `benchmarks/enclosure/parts/<id>/part.json`. Each has a `frame`, sourced params, geometry, datums (mouths, axes, hole and pin patterns, stack planes), connectors (`mates`) and `self_checks`, so R2/R4/R5/R6 are data. `perfboard` and `generic_cylinder` are parametric (`from_request`). New `parts.py`: loader (skips and reports bad files), alias lookup with normalised tokens, `instantiate` (MissingParam), datum types and `transform`, and the gate `validate` (R1 sorted plus orientation, unit directions, mouth on geometry, self_checks; R7/R8 deferred, R9 skipped). New `design_rules.json` with generic rules only, each value with a source.
- **C2 / M2 (G-001-1, G-001-4):** new `feature_graph.py`. A safe expression evaluator (numbers, + - * /, unary minus, min/max/abs/ceil_to, dotted and datum refs; everything else raises ExprError). `Pose` with anchor datum, world offset, `axis` alignment (Rodrigues, antiparallel case handled), `project_to` a plane datum or `body.face[±X|Y|Z].outer|inner`, and `rot_z`. `Node` and `FeatureGraph` with topological resolution (CycleError and MissingRefError name the nodes), reference datums placed through `parts.instantiate`, and a JSON round trip.
- **C3 / M3 (G-001-1, G-001-2):** manifold3d solids for box, cylinder, tube, shell and part. `body_solid = difference(union(body, adds), cuts)`, which asserts that no reference or envelope node is ever read, and a port_cut may span bodies. `scad_body` / `scad_model` use `multmatrix` with the same 4x4 poses, and references are `%` ghosts. Also `body_stats` (volume, bbox, shells, genus) and the `write_stl` fallback writer.
- Architecture: added ARCHITECTURE.md section 7.3, "Conventions fixed by the code". It covers the part.json additions (`size_of`, `gate_params`, axis_list generator, self_check `op`), the expression names inside a part, the primitive local frames (centred in XY, base at Z = 0, world-frame offsets) and the stub behaviour name `NotImplementedStage`, which avoids shadowing the builtin `NotImplemented`.
- RUN.md: section 2 test command now includes the four new test modules. New section 3.1b is the assembly stub smoke arm `run_asm` (`<name>_asm_s$SEED`, seconds, no LLM calls), with its expected ending. It also says when the cascade E1-01 baseline may be skipped (seed 0 and unchanged code path). Section 3.2 now passes `--rules`. The 3.1b snippet was executed verbatim in a scratch folder: rc 1, `not implemented: parse_spec`, 11 parts loaded, no gate drops.

### Files changed
| File | + / - lines | Why (gap id) |
|---|---|---|
| cad_agent.py | +32 / -3 | `--mode assembly`/`enclosure`, `--parts`, `--rules`, `--with-models`, `Design.assy`, `design.json["assembly"]`, finalize branch (G-001-1..5, M0) |
| benchmarks/run.py | +4 / -4 | `assembly` mode choice; the L1 requirement applies to cascade and assembly (cascade message byte-identical) (M0) |
| assembly.py (new) | +161 | AssemblyState, LoadCatalog, LoadRules, NotImplementedStage, build_assembly_tree, finalize stub (M0) |
| parts.py (new) | +545 | catalogue, lookup, datums, instantiate, validation gate, rules loader (G-001-3, M1) |
| feature_graph.py (new) | +904 | expressions, poses, nodes, resolution, geometry per body, SCAD, STL writer (G-001-1, G-001-2, G-001-4, M2+M3) |
| design_rules.json (new) | +33 | generic FDM and fastener rules with sources (M1) |
| benchmarks/enclosure/parts/*/part.json (11 new) | +424 | the catalogue data, the only place part numbers live (G-001-3, M1) |
| test_parts.py (new) | +229 | M1 tests |
| test_feature_graph.py (new) | +273 | M2 + M3 tests |
| test_assembly.py (new) | +108 | M0 CLI and stub tests |
| test_no_hardcoding.py (new) | +76 | hard-coding guard (M0) |
| test_benchmark_runner.py | +9 / -0 | one added test (assembly needs L1s); no existing test changed |
| loop/RUN.md | +46 / -3 | new test modules, section 3.1b stub arm, `--rules` in 3.2 |
| loop/ARCHITECTURE.md | +25 / -0 | section 7.3 conventions |

Rollback copies of every modified pre-existing file are in `iter_001/code_before/`, with SHA1SUMS. New files are rolled back by deleting them.

### Tests
- Command: `venv/bin/python -m unittest test_cascade test_cad_checks test_review_fixes test_cad_agent test_benchmark_runner test_parts test_feature_graph test_assembly test_no_hardcoding`
- Result: 248 passed / 248 total, about 14 s. Before the delta: 201/201. The OpenSCAD parity test ran; it was not skipped.
- New tests:
  - `test_parts` (18): every part loads and passes the gate, with request-sized params parsed from the E1-01/V3 request texts; gate samples pass; MissingParam and unknown-param errors; perfboard holes and bbox for E1-01's and V1's board sizes, with expected values computed from part.json defaults; the socket header raises the module more than the male header. The gate rejects a ×25.4 Pico, an X/Y-swapped Pico ("swapped" R1), a `[2,0,0]` datum direction, a mouth 1 mm off the receptacle and a failing self-check. Bad catalogue files are skipped and reported. Lookup returns the 5 delta queries correctly and normalises tokens. Datum transforms: 90° about Z maps +X to +Y with a point offset; general rotation; datum value refs. Rules load with sources, and a rule without a source is rejected.
  - `test_feature_graph` (19): arithmetic and functions; unsafe expressions rejected (`__import__('os')`, attribute calls, lambdas, `**`, strings, conditionals, dunder attributes, keyword args); `cavity.x = board.width + 2*spec.board_clearance` re-resolves when the spec changes; a cycle a↔b names both nodes; a missing `foo.bar` / `spec.nope` names the node and the ref. Axis alignment to +X and to antiparallel −Z (det 1). `project_to` the −X and +Y outer faces, and the −X inner face. `board.HOLE[3].x` through a placed reference. A reference without a catalogue is a typed error. JSON round trip (graph and resolution equal). Only a port_cut may span bodies. Geometry: a plate with a round and a rectangular through-cut has the expected volume within 0.5% (genus 2). Base and lid are 1 shell each, with overlap ≤ 1 mm³ when closed, and an oversized lip is detected (> 1 mm³). The hull minus solid of a closed shell is the cavity, and for a box it is 0. A reference with the same body name is not in the body volume or `scad_body`, it appears only on `%` lines of `scad_model`, and a smuggled reference trips the assertion. A blind pilot leaves 1 shell and removes π r² h within 0.5%. `write_stl` round-trips through `cad_agent.read_stl`. OpenSCAD parity at `$fn = 24`: volume within 0.5%, bbox within 0.05 mm, on a shell whose port cut really passes through the wall (genus 1). The first draft of this test placed the cut outside the wall, which made it vacuous; that was caught and fixed before the run.
  - `test_assembly` (6): `--mode assembly|enclosure` without `--l1` exits 2. The stub exits 1 with design.json `outcome "failed"` and `assembly.stage "parse_spec"`, the gate drops an inch-scaled fixture part with an R1 note, and the good parts are kept. The alias runs assembly and `--with-models` is recorded. A missing catalogue stops at `load_catalog`, missing rules stop at `load_rules`, and other modes have no `assembly` record. The fake LLM raises on any call, which proves M0 asks the model nothing.
  - `test_no_hardcoding` (3): the guard of the guard (`x = 70`, `'rpi_pico2'`, and negative or near-equal floats); catalogue ids and aliases are read from part.json; assembly.py, parts.py and feature_graph.py are clean.
  - `test_benchmark_runner.test_assembly_without_l1_is_refused_up_front` (added).
- Changed tests: none.
- Hard-coding guard (`test_no_hardcoding`): **pass**. On its first run it flagged `feature_graph.py`'s binary-STL header length (the literal 80, a file-format constant that happens to equal a banned number). It now reads `struct.pack("<80sI", ...)`, so the length is part of the documented format string. The guard itself was not changed. The reviewer should confirm that this is acceptable.
- Tooling: the claude-context MCP server failed to connect in this session, so this implementer fell back to grep and reading known paths.

### Reviewer verdict
pending

### Convergence status
not converged. E1-01 MEETS on 0/3 seeds. Variants CORRECT: V1 not run, V2 not run, V3 not run.

### Notes for Robin
- The judge verdict will **not** change in iteration 002's Run. Assembly mode now stops at `not implemented: parse_spec` and writes no package. The first judgeable package is the walking skeleton (ARCHITECTURE.md 7.1, step 2).
- requirements.md 2.2 names the board `perfboard_70x50`. In the catalogue it is the parametric `perfboard` with width and depth from the request, so the variants reuse it.
- The catalogue numbers come from requirements.md A3–A9 and the datasheets cited in each part.json. Some are explicitly approximate: the Pico 2 receptacle overhang and height (A4), the plug overmolds (A6), the heat-set knurl diameter, and the perfboard grid origin (assumed registered to hole 1). The PJ-320A footprint pins are not modelled yet, and grid conformance (L3.1.6.1) needs them. Please confirm A3–A7 when you can. A correction to these numbers goes into part.json only.
- `design_rules.json` holds generic defaults for when a request is silent: `component_height_default` 10 mm and `solder_side_default` 3 mm. These are deliberately not E1-01's 12 / 4 mm, which come from the request text. Please review the file by hand. The hard-coding guard does not scan JSON.
- Your working-tree ×10 retry caps were left untouched. With them, a cascade run cannot finish inside RUN.md's 90-minute timeout.

## Iteration 002 (2026-10-24)

**Seed(s):** 0 (greedy)
**Mode run:** cascade baseline (the judged `target` arm, per the RUN.md of that time) + assembly smoke arm (`target_asm`)
**Code state at run time:** `iter_002/code_sha1.txt`: cad_agent.py fe653f6f, cascade.py 278b3829, cad_checks.py a3879d40, assembly.py 0583e398, parts.py 49742fdc, feature_graph.py 2e133426, design_rules.json 04f3bfc1.
**Code state after this delta:** cad_agent.py fe653f6f (unchanged), cascade.py 278b3829 (unchanged), cad_checks.py a3879d40 (unchanged), assembly.py ecfb006b, assembly_checks.py b0508c80 (new), layout.py 9bc7bfae (new), parts.py 465ee49b, feature_graph.py d41719bb, design_rules.json 6e4b2715. The cascade code path did not change, so the cascade reference arm need not be re-run (RUN.md 3.1b).

### Runs
| Request | Seed | rc | Status | Minutes | Package |
|---|---|---|---|---|---|
| E1-01 (`target`, cascade) | 0 | 124 | timeout(124) | 90.3 | iter_002/target_s0/20261024-060005/ |
| E1-01 (`target_asm`, assembly) | 0 | 1 | failed (`not implemented: parse_spec`, no package) | 0 | iter_002/target_asm_s0/20261024-060001/ |
| V1 | | | not run | | |
| V2 | | | not run | | |
| V3 | | | not run | | |

### Judge verdicts (from judge_1.json and judge_2.json)
| Request | Verdict | Class | Score | Worst w3 margin | G0 | G1 | G2 | G3 | G4 | G5 |
|---|---|---|---|---|---|---|---|---|---|---|
| E1-01 (judge 1) | DOES NOT MEET | WRONG | 22% raw (29/134 weight points, nearly all vacuous); real progress ~0 | undefined (standoff count 0 vs 4; Pico 1194 mm³ outside a zero-volume cavity) | F | F | F | F | F | F |
| E1-01 (judge 2) | DOES NOT MEET | WRONG | about 5% | undefined (no cavity: hull minus solid = 0 mm³) | F | F | F | F | F | F |

### Defect count by severity
| Request | Gate | Weight 3 | Weight 2 | Weight 1 | of which UNVERIFIED | Observations |
|---|---|---|---|---|---|---|
| E1-01 | G0–G5 all fail | not reported per weight | not reported per weight | not reported per weight | not reported | Package byte-identical to iter_001's 90 × 74 × 4 slab: the judged arm was the frozen cascade path. The new code lived in `--mode assembly`, which stopped at `parse_spec` without a package. |

Change since the previous iteration: none (same package). No regression. The loop ran open loop: the judged plant was not the one being changed (RC7).

### Gaps (gap-analysis agent, `iter_002/delta.md` section 2)
- `G-002-1` (every defect; loop control) → the error signal measured the cascade, not assembly mode → RUN.md 3.1/3.2 (RC7, change C0)
- `G-002-2` (L3.12.1.1 G0, L3.12.1.2, L3.12.2.1; package) → assembly mode had no stage after LoadRules and no package writer → M12 (RC8, C7)
- `G-002-3` (L3.2.x, 3.3.x, 3.4.x, 3.7.x, 3.8.x, 3.10.1.1; base/lid; cavity 0, standoffs 0, second body none) → no rule derives body/add/cut nodes from the contents → M8 (RC9, C6)
- `G-002-4` (L3.1.1.1, L3.5.x G3, L3.6.x G4; layout, port positions) → no placement of the references, no envelopes → M4 + M7 (RC10, C1 + C5)
- `G-002-5` (indirectly all) → the LLM was never asked anything in assembly mode: no spec slots, no contents → M6 subset (RC11, C4)
- `G-002-6` (L3.12.2.1; every gate invisible to the agent) → no separable / inside / clear_of / aperture / seated sensors → M5 subset (RC12, C2)

### Delta summary (implemented this iteration: the walking skeleton, ARCHITECTURE.md 7.1 step 2 and 7.4)
- **C0 (G-002-1):** RUN.md section 3.1 is now the assembly arm (`run_one`, writing `${name}_s$SEED`; `run_asm` kept as an alias for Robin's run policy). 3.1b is the cascade reference arm (only when its code path changes or the seed is not 0). 3.2 states the rule: assembly is judged from iteration 003 on, and a `not implemented` / no-package run is G0 FAIL with the stage named, never replaced by the cascade. New 3.4 Run-step self-check: `package_missing` writes `"missing": [...]` (base.stl, lid.stl, layout.json, self_report.json) into runs.jsonl. Section 4's table now describes the assembly package as "Today".
- **C1 / M4 subset (G-002-4):** `parts.plug_sweep` (plug SEAT on the mouth at full mate, PLUG_AXIS on the connector axis, the cable-end primitive swept outward by `rules.plug_travel`; boxes via computed `rot_z`, cylinders via the new `Pose.axis_dir`), `board_keepout` (V-KO-TOP/BOT), `column` (V-SEAT, V-HOLE-KO), `content_envelope` (V-PICO). All envelope nodes are kind `envelope`, never printed; lengths come only from spec, rules and part data.
- **C2 / M5 subset (G-002-6):** new `assembly_checks.py`: `separable`, `clear_of` (penetration, then `min_gap`, rubric 3.2), `inside` (hull minus solids, rubric 3.3), `aperture_count` / `aperture_oversize` (slab minus bodies, `decompose`, rubric 3.4), `seated` (standoff tops and pilot axes measured from the mesh), `bbox_within`, design-level `port_below_split` and `pilot_depth`. A `Plan` holds the check set and its reference/envelope solids; `run_plan` runs it on any bodies; `measure_package` loads the delivered STLs (rubric 3.1 recipe) and its output is `self_report.json`.
- **C3 (guard):** `test_no_hardcoding.MODULES` gains `layout.py`; a missing module now fails the test instead of being skipped. Rotations are computed with atan2; the STL header still uses `STL_HEADER`.
- **C4 / M6 subset (G-002-5):** `ParseSpec`: Python extracts every number occurrence (own id, ≤ 120-character quote, source = request or L1 id, "a x b" groups and "a to b" ranges share the unit); the LLM maps the generic `spec_slots` (data in design_rules.json) onto ids or `none` (label `assy_spec`, per-key vote); relation violations (wall_min > wall_max, ≤ 0, missing board size, same id twice) trigger exactly one re-ask (`assy_spec_reask`) naming them; a band end that came from a default and falls outside the stated end is set equal to it (flagged); `none` takes the rules default, flagged in `assumptions` with provenance `rules:<key>`. `Contents`: top-k `Catalog.lookup` candidates per kind (board, module, connector, generic; never plugs or fasteners), LLM answers quantity and exposed (`assy_contents`), exactly one board required. `ChooseStack` (`assy_stack`) words each option with its STACK_TOP height.
- **C5 / M7 subset (G-002-4):** new `layout.py` (pure placement math): rotate by atan2, flush `size_of` face to the edge, stack Z from STACK_TOP, equal-gap spread over the free span minus the hole columns, `ports_do_not_fit` from plug widths + 2 x plug_to_opening + min_ligament, tangential grid snap, R7 interference and hole-column checks with a 1-D shift, free-spot placement for parts without an exposed connector. `ArrangeContents` asks `assy_edge` (voted), prunes infeasible assignments, and `ConfirmArrangement` asks `assy_confirm` (p_yes); on "no" it tries the next feasible assignment ordered by the LLM's votes, until confirmed or exhausted (typed failure, no cap).
- **C6 / M8 subset (G-002-3):** `ChooseArchetype` (one feasible: `tray_lid+screws`, recorded `rule:only_feasible`). `DeriveFeatures`: every node's params are expressions over reference datums, `<ref>.bbox.*`, `spec.*`, `rules.*` and `fastener.*`: cavity from the contents' AABB + keep-outs + `spec.board_clearance`; base shell (wall/floor clamped to the spec band); split = max(cavity top + lip_engagement, port-cut tops + min_ligament); 4 standoffs + blind pilots on the board HOLE axes (board screw by rule); one port cut per exposed connector on the wall it faces, sized from the plug primitives crossing the wall slab + 2 x plug_to_opening (round when all are cylinders); lid plate, lip ring (sliding fit), corner pilaster bosses with pilots, lid pads and clearance holes, and lip notches at the bosses.
- **C7 / M12 subset (G-002-2):** `Build` (resolve, manifold solid per body, base/lid/model .scad, OpenSCAD compile per body with parity 0.5% / 0.05 mm, manifold fallback recorded in `stl_source`), `Verify` (never fails; runs the plan on the manifold solids and on the delivered STLs), `RenderViews` (`views/model_*`, `views/ghost_*`), `WritePackage` (layout.json, self_report.json, feature_graph.json, checks.json, verification_matrix.{md,json}, model.3mf written from the delivered meshes). `finalize` returns verified exactly when every check passes on the delivered STLs.
- **Architecture:** new ARCHITECTURE.md section 7.5, "Conventions fixed by the code (iteration 002)". The main refinements: grid snap is tangential only, because L2.1.3 at weight 2 outranks the weight-1 grid check, and requirements.md's own default layout is off-grid along X. `inside` measures the references minus the seat columns. The port-cut pose uses offset expressions, because `project_to` would discard the axial position. The lip gets notches at the pilasters. Standoffs and bosses start at the floor's underside. Wall slabs span the cavity's span, inset by measure_tol. The spec gains a new `headroom` slot. Request-sized parts other than the board get an `assy_params` question. The 3MF comes from the meshes, because the CGAL export cost 33 s. Render-only `views.scad` and `ghost.scad` show openings and solid references.
- **RUN.md:** sections 2 (adds `test_assembly_checks`), 3 and 4 as in C0. Proof without Ollama: `bash -n` passed on all 9 extracted `sh` blocks. `package_missing` was run on a real offline package (`[]`) and on a missing folder (all four files listed). The offline end-to-end test runs the same `cad_agent.main` argv as the new 3.1, without `--seed` and `--num-ctx`, which only affect the real model.

### Files changed
| File | + / - lines | Why (gap id) |
|---|---|---|
| assembly.py | +1074 / -29 | the walking-skeleton tree, stages, derive rules, check plan, package, finalize (G-002-2..6) |
| assembly_checks.py (new) | +364 | typed checks, Plan / run_plan, measure_package (G-002-6) |
| layout.py (new) | +511 | placement math (G-002-4) |
| parts.py | +122 / -3 | envelope generators; spec_slots in load_rules; DEFERRED_RULES text for R7/R8 (G-002-4, G-002-5) |
| feature_graph.py | +42 / -4 | `Pose.axis_dir`, `<ref>.bbox.*` world AABB refs, `fastener.*` namespace (G-002-3, G-002-4) |
| design_rules.json | +39 / -1 | 22 new generic rules with sources; `spec_slots` (12 slots) (G-002-3..6) |
| test_assembly.py | +679 / -10 | rewritten for the skeleton; M0 CLI tests kept or adapted (see Tests) |
| test_assembly_checks.py (new) | +206 | M5 subset tests |
| test_parts.py | +148 / -0 | `TestEnvelopes`, spec-slot rules test |
| test_feature_graph.py | +36 / -0 | `TestResolverExtensions` |
| test_no_hardcoding.py | +4 / -8 | scans `layout.py`; a missing module fails (C3) |
| loop/RUN.md | +87 / -73 | C0 |
| loop/ARCHITECTURE.md | +45 / -0 | section 7.5 |

Rollback copies of every modified pre-existing file are in `iter_002/code_before/`, with SHA1SUMS. `cad_agent.py` was copied but not changed. To roll back the new files (`assembly_checks.py`, `layout.py`, `test_assembly_checks.py`), delete them.

### Tests
- Command: `venv/bin/python -m unittest test_cascade test_cad_checks test_review_fixes test_cad_agent test_benchmark_runner test_parts test_feature_graph test_assembly test_assembly_checks test_no_hardcoding`
- Result: **292 passed / 292 total**, about 40 s (248/248 before the delta). OpenSCAD ran: the end-to-end packages are OpenSCAD meshes that passed the parity check, and the test asserts `stl_source == openscad` when OpenSCAD is present.
- New tests:
  - `test_assembly_checks` (11): clear_of passes at c + 0.02 and fails at c − 0.02, with the margin within 0.02 of the analytic value; penetration gives a negative margin and the analytic intersection bbox; `minus` removes a seat column; inside (clearance pass/fail, sticking out); separable (fused, 2 mm³ overlap, 2-shell body fail; touching pair passes); aperture_count (2 cuts → 2, missing cut → margin −1); aperture_oversize (0.3 per side passes, 1.6 fails at max 1.5); seated (tops 0.2 low fails, a standoff moved 0.3 fails, exact passes); bbox_within incl. X longest; `measure_package` on `write_stl` STLs equals the manifold run within 0.02 for every check; a missing STL is a failed measurement.
  - `test_parts.TestEnvelopes` (6): V-USB-PLUG shell and overmold bboxes equal the hand formula from plug_microusb_b/part.json within 1e-6. V-JACK-PLUG-k diameters come from the part, the axis lies on the jack AXIS (≤ 0.01, R8), and the full-mate stop gap and the swept length are checked. Keep-out bboxes equal footprint × [0, above] and [−t − below, −t]. Columns and V-PICO are checked (the receptacle overhang is inside). A connector facing +Y sweeps along +Y. A vertical axis is a typed error. Also `TestRules.test_spec_slots_load_and_unknown_defaults_are_rejected`.
  - `test_feature_graph.TestResolverExtensions` (3): bbox refs follow a rotated pose; the fastener namespace (a missing value is a MissingRefError); `axis_dir` pose and its JSON round trip.
  - `test_assembly` (29):
    - `TestExtractNumbers` (2): own ids per occurrence, group units, and quotes ≤ 120. "M2.5" and "PJ-320A" are not numbers, ranges share the unit, and cm converts to mm.
    - `TestParseSpec` (4): the correct E1-01 spec with provenance. An out-of-enum id takes the flagged default and never an invented number. A wall_min/wall_max swap triggers exactly one re-ask, visible in the labels and naming the violation. A silent request (V1 without L1s) takes flagged rules defaults.
    - `TestContents` (3): E1-01 gives 1 perfboard, 1 rpi_pico2 and 2 jack_3p5_pj320a with exposed flags, no plug or fastener id is offered, and the board params come from the spec. Two boards is a typed failure. V3 gets a female-socket stack and the capacitor's 10/20 from `assy_params`.
    - `TestArrange` (5): E1-01 USB_AXIS is −X with the mouth x = −usb_overhang computed from part data, jack AXIS is +X at the board edge, spacing ≥ the plug need, no interference or column hit, Pico pins on the grid along the edge (≤ 1e-6), and header STACK_TOP = Pico PCB_BOTTOM. V1 has two ports on −X with disjoint plug sweeps. V2 spreads three jacks on +Y with equal gaps, and a shrunk board gives a typed LayoutError. V3 sockets raise the USB mouth by the difference of the stack heights. ConfirmArrangement: "no" then "yes", with the infeasible all-on-one-end assignment pruned with a note.
    - `TestDeriveFeatures` (3): one port cut per exposed connector on the facing wall (E1-01 −X:1, +X:2; V1 −X:2). Standoffs are coaxial with the holes (≤ 1e-6), their tops equal the board BOTTOM, and pilot depth ≥ min_engagement. The lip gap equals sliding_fit inside the band, the lip bottom is ≥ the V-KO-TOP top, and bosses are coaxial with the lid holes. Size leak: keepout_above +3 raises the split by 3 with X and Y unchanged, and board width +5 changes only X.
    - `TestEndToEnd` (6): `cad_agent.main --mode assembly` for E1-01 and V1 with the scripted controller and `rules.fn = 24`. Both give exit 0 / verified with all gate-equivalent checks passing. Aperture counts are E1-01 −X 1, +X 2, ±Y 0 and V1 −X 2, others 0. The size is within spec.max_* with X > Y, and the meshes are OpenSCAD's. Manifest: every package file exists and parses, and both STLs load by the rubric recipe with 1 shell, NoError and bbox 1–200 mm. The self-report agrees with an independent rubric-3.2 re-measurement in the test, which does not use assembly_checks, within 0.02 for the 3 plug sweeps and the board. No reference appears in base.scad or lid.scad, and the ghosts are `%` lines in model.scad. The design.json components come from the graph (standoff counts match, all `rule:` sources). With OpenSCAD mocked to time out, both STLs come from the manifold (`stl_source == manifold`) and the run still verifies.
- Changed tests (behaviour intentionally changed; the stub stage `NotImplementedStage("parse_spec")` no longer exists):
  - `test_assembly.TestAssemblyCli.test_stub_exit` → `test_gate_then_a_typed_parse_spec_failure`: the stage after the gate now asks the LLM. With a request that has no board size, ParseSpec re-asks once and fails with a typed note (exit 1, stage `parse_spec`). The catalogue-gate assertions are kept (inch-scaled part dropped with an R1 note, good parts kept, rules loaded, with_models false).
  - `test_assembly.TestAssemblyCli.test_enclosure_alias_runs_assembly`: the same scripted "none" controller replaces the raising fake, because ParseSpec now asks a question. It asserts the same things (stage `parse_spec`, `--with-models` recorded).
  - `test_missing_catalogue_fails_at_load` and `test_missing_rules_fail_at_load` are unchanged and still use the raising fake, which proves no LLM call happens before `load_catalog` / `load_rules`.
  - `test_no_hardcoding.test_assembly_modules_hold_no_target_literals`: strengthened, not weakened. Every module in MODULES must exist (a missing one fails instead of being skipped, C3), and `layout.py` was added.
- Hard-coding guard (`test_no_hardcoding`): **pass** on assembly.py, parts.py, feature_graph.py, assembly_checks.py and layout.py.
- Tooling: the claude-context MCP server failed to connect in this session ("configured MCP servers failed to connect: claude-context"). I worked from known paths and used targeted grep only.

### Reviewer verdict
pending

### Convergence status
not converged. E1-01 MEETS on 0/3 seeds. Variants CORRECT: V1 not run, V2 not run, V3 not run.

### Notes for Robin
- **Iteration 003 judges assembly mode.** RUN.md 3.1 now runs it. A run takes a few minutes, not 90. With correct scripted controller answers, the offline E1-01 package measures about 82.3 × 61.0 × 24.4 mm with walls 2.4, and all 25 of the agent's checks pass. Whether the 9B controller gives those answers (spec ids, contents, edges) is what the next Run measures. design.json records every choice with who made it, so a wrong answer is traceable to its stage.
- **Lid retention.** I implemented corner pilaster bosses with M3 lid screws, as the delta designed. They stand about 2.6 mm proud of the walls at each corner (visible in the renders). If you prefer a sliding lid or snaps, say so (L2.7.3). The archetype ranking will offer them once they exist.
- **Grid conformance.** The Pico's pins snap to the 2.54 grid along the edge only. Normal to the edge the Pico stays flush, so the USB mouth sits at its catalogue overhang. With the perfboard grid registered to hole 1 (an assumption in part.json), the residual along X is 1.13 mm, and requirements.md's own default layout has the same residual. Please confirm the grid origin of your board. The fix is a part.json change, not code.
- **Board screw rule.** The delta asked for the *smallest*-thread catalogue screw that passes the board hole. Today that is the M2.5 (the M3 does not pass the 3.0 mm hole with ISO 273 medium clearance). Its head sets the 7.0 mm seat columns.
- **New rule values to review by hand** (the guard does not scan JSON): plug_travel 40, driver_clearance 1.0, driver_diameter 6.0, overlap_max 1.0, interference_max 0.01, seat_gap_max 0.10, seat_axis_residual_max 0.25, lip_engagement 2.0, lip_wall 1.2, boss_wall_min 1.6, cut_overrun 1.0, screw_hole_clearance_min 0.2, max_quantity 8, part_to_wall 0.2, measure_tol 0.01, margin_scale 1.0, lookup_k 3, layout_step 0.5, aperture_min_volume 1.0, parity_volume_rel 0.005, parity_bbox 0.05. The spec slots are new too, including `headroom`, whose default is board_to_wall.
- **Not yet checked by the agent:** printability, wall thickness by ray casting, other openings (V-AP-OTHER), the install sweep and screwdriver access. These are iteration 003's delta. The verification matrix's L1 rows say "no check covers this requirement" until translation (M10). The rule-derived checks sit in a `rules` row.
