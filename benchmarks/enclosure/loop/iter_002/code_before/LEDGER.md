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
