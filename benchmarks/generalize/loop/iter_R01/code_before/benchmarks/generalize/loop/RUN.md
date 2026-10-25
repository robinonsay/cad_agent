# RUN: how the Run step runs the CAD agent each iteration (generalization loop)

The Run step is the **only** step in the loop that uses a local LLM. It runs the agent on the train designs
(`../designs/*`) and on the regression set (`benchmarks/enclosure` E1-01, V1, V2, V3), one run at a time,
through `../run_suite.py`. It leaves one package per run for the judges, plus `runs.jsonl` and `summary.json`.

**Implementers keep this file current.** When the CLI or `run_suite.py` changes, update this file in the
same delta and say so in the ledger.

Rules:
- Local models only: Ollama at `http://localhost:11434`, model `ornith-1.5:9b`, `--num-ctx 8192`.
- **One model resident and one Ollama user at a time.** Never start a second run, a judge panel on Ollama,
  or `benchmarks/run.py` while a suite is running.
- Never open, edit or run `benchmarks/heldout.json`. Never touch `.mcp.json`. No git commit or push.
- Held-out isolation: never open, list, read or search `../holdout/` or `holdout_results/`. Only the isolated
  held-out runner of section 6 runs `--split holdout`, and it reads only the aggregate line it prints.

---

## 1. Variables (set once per iteration)

```sh
REPO=/Users/robinonsay/python/llm-bt
PY=$REPO/venv/bin/python
NNN=001        # iteration number (run_suite accepts 1 or 001; folders are always 3 digits)
SEED=1         # the iteration's seed: SEED = the iteration number unless the ledger says otherwise
               # (seed 0 is greedy and reproduces byte-identical transcripts, so it adds no information twice)
ITER=$REPO/benchmarks/generalize/loop/iter_$NNN
```

Per-iteration notes from the gap analyst (subset, extra seeds) go here, newest last:

- iteration 001: full train split + regression set, SEED=1 (GM1 baseline: where each design stops).
- iteration 002: full train split + regression set, SEED=2. Delta 001 (GM2a) changes the stopping point of 38
  designs, so no subset. Before judging, write `verdicts.json` in the RUN.md 5 form (`{"<name>": {"verdict": ...,
  "class": ..., "score": ...}}`). Iteration 001's list of `{"id", "meets", ...}` rows is not accepted by
  `cache_verdicts.py`. Cache iteration 001's regression verdicts too, so that E1-01, V1 and V2 are cache hits.
- iteration 003: full train split + regression set, SEED=3, no subset. Delta 002 changes pilots and floors in every
  shell package and adds a gated relation question, so all six packaged designs and the regression set must be judged.
  Judges grade the regression packages' boss pilots against the enclosure rubric (≥ 6.0; delta 002 makes them about
  7.7). `../rubric.md` is still missing: judges keep using the enclosure rubric plus each requirements.md and say so.
- iteration 004: full train split + regression set, SEED=4, no subset. Delta 003 changes boss layouts, closures, vents and
  roofs only where a default fails or the text asks, so the regression packages are expected to be **cache hits**
  (judge only what `to_judge` lists). Every changed train package must be judged: at least G02, G04, G11, G13. In
  `verdicts.json`, write `"verdict": "MEETS" | "DNM"` (RUN.md 5). Iteration 003's boolean `meets` form was mis-scored
  until delta 003 C0.

## 2. Preflight (every iteration)

```sh
# nothing else may be using Ollama: both must print nothing
pgrep -fl cad_agent.py
pgrep -fl 'benchmarks/run.py'
# the server is up and the model is present
curl -s http://localhost:11434/api/tags | "$PY" -c 'import json,sys; m=[x["name"] for x in json.load(sys.stdin)["models"]]; print("ok" if "ornith-1.5:9b" in m else "MISSING ornith-1.5:9b", m)'
# the full unit suite is green before spending hours of runs (about 20 minutes; no Ollama)
cd "$REPO" && "$PY" -m unittest test_cascade test_cad_checks test_review_fixes test_cad_agent test_benchmark_runner \
    test_parts test_feature_graph test_assembly test_assembly_checks test_no_hardcoding test_generalize_suite
```

`run_suite.py` repeats the first three checks itself and stops with exit 2 if one fails. Use
`--no-preflight` only in tests. Implementers append new test modules to the unittest line as they appear.

## 3. Run commands

> **Run policy (every iteration):**
> - Run the **whole train split** once at `SEED`, then the **regression set** at `SEED`. These are the two
>   commands below, in this order, and nothing in parallel.
> - The gap analyst may narrow the train run to a named subset in section 1 (the designs the delta touches
>   plus five sentinels from different families). The full train split must still run at least every third
>   iteration and always before a held-out measurement.
> - Every run uses `--mode assembly` (the judged arm). The cascade and default modes are not run.
> - A run that ends without a package (rc 1, `not implemented: <stage>`, a crash or the timeout) is
>   recorded as no-output and is not judged. The ledger names the stage from `summary.json` (`stage`,
>   `last_note`).

```sh
cd "$REPO"
"$PY" benchmarks/generalize/run_suite.py --iter "$NNN" --seed "$SEED"                 # all train designs
"$PY" benchmarks/generalize/run_suite.py --iter "$NNN" --seed "$SEED" --regression    # E1-01, V1, V2, V3
```

A subset: append design ids, for example `... --seed "$SEED" G01 G16 G29`. A re-run of a design in the
same iteration replaces its row in `summary.json`. `runs.jsonl` keeps both rows.

What `run_suite.py` does for each design, strictly one after another:

1. It writes `$ITER/inputs/<id>.request.txt` (the `request` field) and `<id>.l1.json` (the `l1` list) from
   the design's `design.json`. For the regression set it reads `benchmarks/enclosure/enclosure.json` and
   `variants.json`, as in the enclosure loop's RUN.md 2.1. The agent never gets requirements.md.
2. It runs, with cwd = `$REPO`:

   ```sh
   $PY cad_agent.py --mode assembly --auto --seed $SEED --num-ctx 8192 \
       --parts benchmarks/generalize/parts --parts benchmarks/enclosure/parts \
       --rules design_rules.json --l1 $ITER/inputs/<id>.l1.json --out $ITER/<id>_s$SEED "<request>"
   ```

   - The regression set passes `--parts benchmarks/enclosure/parts` only. That is exactly the enclosure
     loop's command, and the enclosure loop's 90-minute limit is replaced by this loop's 20 minutes (a
     regression run takes about 80 s).
   - `--parts` is repeatable (since this loop's setup). The first folder wins a part id. A byte-equal copy
     in a later folder is skipped silently (`plug_microusb_b` is in both), and a different one is noted in
     `design.json` `assembly.notes`.
   - stdout and stderr go to `$ITER/<id>_s$SEED/run.log`.
3. **Timeout: 20 minutes per run.** On timeout the whole process group gets SIGTERM, then SIGKILL after
   30 s (OpenSCAD children included), and the run is recorded with rc 124.
4. It appends one row to `$ITER/runs.jsonl` and rebuilds `$ITER/summary.json` (section 5).

Exit codes of `cad_agent.py`: 0 = verified by its own checks, 3 = built but its own checks fail (NOT a pass),
1 = failed, 2 = usage error, 130 = interrupted, 124 = killed by the timeout. The agent's own verdict is never
the loop's verdict. The judges decide.

Useful flags: `--dry-run` prints the commands and runs nothing. `--summarize` only rebuilds `summary.json`
(after verdicts are cached, or after a rubric edit). `--timeout S` overrides the 1200 s (only with a ledger
reason). `--parts DIR` (repeatable) overrides the catalogue folders.

## 4. Code version

Each invocation writes `$ITER/code_sha1.txt` in `shasum` format, with paths relative to `$REPO`. It covers
every top-level agent module (`*.py` except `test_*.py` and `__init__.py`), `design_rules.json` and every
`part.json` of both catalogues. `summary.json` `code` says:

- `code_unchanged`: equal to the newest earlier iteration's file (null for the first iteration);
- `changed_within_iteration`: the code changed between two invocations of the same iteration. That is a
  process defect: the iteration mixes versions. `runs_on_one_code_version` is false, and the ledger must say
  so.

Check a frozen version by hand: `cd "$REPO" && shasum -c benchmarks/generalize/loop/iter_$NNN/code_sha1.txt`.

## 5. Judging and the judge cache

`summary.json` lists:
- `to_judge`: runs with renders in `views/` and no cached verdict. Only these go to the judges.
- `cached`: runs whose verdict was reused. The key is the design id + the geometry hash (sha1 over the
  package's STL files, sorted by path, each as its path, length and canonical geometry: the triangles with
  vertices rounded to 1e-4 mm, each started at its smallest vertex (winding kept), sorted; delta 002 C3. OpenSCAD's
  facet order is not deterministic, so raw bytes never matched twice. Entries cached before delta 002 keep their
  raw-byte keys and never hit) + the spec hash (sha1 over the
  design's requirements.md, design.json and `../rubric.md`; for the regression set the enclosure
  requirements.md, enclosure.json or variants.json, and the enclosure rubric.md).
- `counts` per split: runs, rc histogram, `no_output` (no STL), `with_renders`, `timed_out`, `judged`,
  `meets`, `correct` (MEETS counts as CORRECT), `to_judge`.
- `regression`: `pass` (E1-01 MEETS and V1–V3 at least CORRECT), `fail`, `pending` (not all judged) or
  `not_run`.

The judges grade each package in `to_judge` blind, against the design's requirements.md and `../rubric.md`
(the enclosure rubric for the regression set). Each writes `judge.md` and `defects.json` next to the package,
in `$ITER/<id>_s$SEED/`. Then the verdicts are collected into one file and cached:

```sh
cat > "$ITER/verdicts.json" <<'EOF'
{"G01_s1": {"verdict": "DNM", "class": "MINOR", "score": 0.91, "judge": "iter_001/G01_s1/judge.md"},
 "E1-01_s1": {"verdict": "MEETS", "class": "CORRECT", "score": 1.0}}
EOF
"$PY" benchmarks/generalize/cache_verdicts.py "$NNN" "$ITER/verdicts.json"
```

Both verdict forms are accepted (generalize delta 003 C0): `"verdict": "MEETS" | "DNM"` (preferred) or a boolean
`"meets": true | false`. A boolean verdict is stored normalised, with `"verdict"` added next to `"meets"`, and
`run_suite.verdict_flags` reads either form, so a boolean MEETS is never counted as DNM again (iteration 003, P-3).

This stores each verdict under its key in `loop/judge_cache.json`, rebuilds `summary.json` (`to_judge` empty,
counts current), and prints the counts the ledger needs. A run with no STL is skipped and reported (exit 1).
With two judges per package, cache the reconciled verdict (the lower class when they disagree, as in the
enclosure loop).

## 6. Held-out measurement (isolated runner only; at most once per milestone)

Run only when the gap analyst asks for it in the ledger, on a version whose train iteration ran on the same
code, after the train runs:

```sh
cd "$REPO" && "$PY" benchmarks/generalize/run_suite.py --iter "$NNN" --seed "$SEED" --split holdout
```

- Output goes to `loop/holdout_results/iter_$NNN/`. The script prints only aggregate lines (no ids, rc
  values or stages). `summary.json` there has `code.matches_train_iter`, and it must be true.
- Isolated judges grade the packages. `cache_verdicts.py "$NNN" verdicts.json --split holdout` stores them in
  `loop/holdout_results/judge_cache.json` and prints `{"holdout_score": x}`.
- The runner copies **only that number** into the ledger. Nobody else reads anything under
  `holdout_results/`.

## 7. Iteration folder layout

```
benchmarks/generalize/
├── run_suite.py, cache_verdicts.py     the Run-step tooling (no LLM)
├── designs/<id>/                       train: requirements.md, design.json
└── loop/
    ├── ARCHITECTURE.md  RUN.md  LEDGER.md
    ├── judge_cache.json                train + regression verdicts: id|geometry sha1|spec sha1 -> verdict
    ├── iter_NNN/
    │   ├── code_sha1.txt               agent version (shasum format)
    │   ├── inputs/<id>.request.txt, <id>.l1.json
    │   ├── runs.jsonl                  one row per run (appended; a re-run adds a row)
    │   ├── summary.json                rebuilt from runs.jsonl + the cache: counts, to_judge, cached, regression
    │   ├── verdicts.json               the judges' verdicts for cache_verdicts.py
    │   ├── <id>_s<SEED>/               G.. (train) and E1-01 / V1-V3 (regression)
    │   │   ├── run.log
    │   │   ├── <YYYYmmdd-HHMMSS>/      the package: <body>.stl, *.scad, layout.json, self_report.json,
    │   │   │                           design.json, checks.json, verification_matrix.*, views/*.png, llm/
    │   │   ├── judge.md, defects.json  (judges)
    │   ├── gaps.md, delta.md, review.md (gap analyst, implementer, reviewer)
    └── holdout_results/                held-out only (isolated; never read by the loop)
```

A `runs.jsonl` row has: `name`, `id`, `split`, `seed`, `rc`, `timed_out`, `secs`, `package` (path relative
to the repo, or null), `has_renders`, `geometry_sha1`, `stl_files`, `missing` (package files missing:
`base.stl`, `lid.stl`, `layout.json`, `self_report.json` for the regression set; `design.json`, `layout.json`,
`self_report.json` and at least one STL otherwise), `spec_files`, `spec_sha1_at_run`, `code_sha1`,
`catalogues`, `outcome`, `stage` and `last_note` (from the package's design.json), `finished`.
`summary.json` adds `spec_sha1` (now), `spec_changed_since_run`, `verdict` and `cache` (hit / miss /
no_package) to each run.
