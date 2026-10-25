# RUN: how the Run step runs the CAD agent each iteration

The Run step is the **only** step in the loop that runs a local LLM. It runs the agent on the target
(E1-01) and on each variant (V1, V2, V3), one run at a time, and leaves one design package per run
for the judge (`../rubric.md`).

**Implementers keep this file current.** When the CLI changes (for example when `--mode assembly`
lands, milestone M0 in `ARCHITECTURE.md`), update section 3 in the same delta and record that in
the ledger.

Rules: local models only (Ollama at the default host `http://localhost:11434`). One Ollama user at a
time. Never open, edit or run `benchmarks/heldout.json`. Never touch `.mcp.json`. No git commit or
push.

---

## 1. Variables (set once per iteration)

```sh
REPO=/Users/robinonsay/python/llm-bt
PY=$REPO/venv/bin/python
NNN=001                     # iteration number, zero-padded to 3 digits
SEED=1                      # seed for this iteration (suggestion: SEED = the iteration number; 0 = greedy)
ITER=$REPO/benchmarks/enclosure/loop/iter_$NNN
TIMEOUT_S=5400              # 90 minutes per run
mkdir -p "$ITER/inputs"
```

## 2. Preflight (every iteration)

```sh
# nothing else may be using Ollama: both must print nothing
pgrep -fl cad_agent.py
pgrep -fl 'benchmarks/run.py'
# the server is up and the main model is present
curl -s http://localhost:11434/api/tags | "$PY" -c 'import json,sys; m=[x["name"] for x in json.load(sys.stdin)["models"]]; print("ok" if "ornith-1.5:9b" in m else "MISSING ornith-1.5:9b", m)'
# unit tests are green before spending hours of runs
cd "$REPO" && "$PY" -m unittest test_cascade test_cad_checks test_review_fixes test_cad_agent test_benchmark_runner \
    test_parts test_feature_graph test_assembly test_no_hardcoding
```

The last command also runs the assembly-mode test files (added in iteration 001). Implementers
append new modules to it as they appear (next expected: `test_assembly_checks`).

### 2.1 Inputs: request text and L1s, extracted from the benchmark files

`cad_agent.py --l1` takes a list of `{id, text, method}` (or an object holding it under `"l1"`). The
benchmark files hold a `"requests"` list, so each request's `request` text and `l1` list are
extracted once per iteration into `$ITER/inputs/`:

```sh
"$PY" - "$REPO" "$ITER/inputs" <<'EOF'
import json, sys
from pathlib import Path
repo, out = Path(sys.argv[1]), Path(sys.argv[2])
for src in ("benchmarks/enclosure/enclosure.json", "benchmarks/enclosure/variants.json"):
    for r in json.loads((repo / src).read_text())["requests"]:
        (out / f"{r['id']}.request.txt").write_text(r["request"])
        (out / f"{r['id']}.l1.json").write_text(json.dumps(r["l1"], indent=2))
        print(r["id"], len(r["l1"]), "L1s")
EOF
```

This writes `E1-01`, `V1`, `V2` and `V3` (`.request.txt` and `.l1.json` each). The agent gets the
`request` field, which is Robin's request with the clarifications in `request_notes`
(primary arm, requirements.md section 7). It does not get the photo, the default layout or
requirements.md.

### 2.2 Timeout wrapper (macOS has no `timeout`)

```sh
run_with_timeout() {  # usage: run_with_timeout SECONDS cmd args...  -> exit code, 124 = timed out
  "$PY" -c '
import os, signal, subprocess, sys
p = subprocess.Popen(sys.argv[2:], start_new_session=True)
try:
    sys.exit(p.wait(timeout=float(sys.argv[1])))
except subprocess.TimeoutExpired:
    os.killpg(p.pid, signal.SIGTERM)
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
    print(f"[RUN.md] killed after {sys.argv[1]} s", flush=True)
    sys.exit(124)
' "$@"
}
```

It kills the whole process group, including any OpenSCAD child processes.

## 3. Run commands

> **Run policy (set by Robin, 2026-10-24; overrides anything below):**
> - **Every iteration runs ONLY the assembly arm** (`run_asm`, section 3.1b) for E1-01, and for the variants when the loop asks for them. Its output is what the judges grade.
> - **Do NOT run the cascade baseline** (section 3.1). It is already recorded in iter_001 (a 90-minute timeout). The cascade code path cannot change the judges' verdict, and it keeps the single Ollama server busy for 1.5 h.
>   - Run it again only if an implementer explicitly asks for it in that iteration's LEDGER entry, because they changed `cascade.py` or `cad_checks.py` in a way meant to affect it.
> - **While assembly mode is a stub** (exit 1, `not implemented: <stage>`), there is no package to judge. Report the output with `has_renders: false`, and the loop records "no package (stub)" without spending judge time.
> - **Implementers:** when assembly mode produces a package (SCAD/STL + renders), make sure `run_asm` writes renders to `views/` so it is judgeable.

Exit codes from `cad_agent.py`: 0 = verified by its own checks, 3 = built but its own checks fail
(NOT a pass), 1 = failed, 2 = usage error, 130 = interrupted, 124 = killed by the 90-minute
timeout. The agent's own verdict is never the loop's verdict. The judge decides.

### 3.1 Current commands (baseline: no assembly mode exists yet, so use `--mode cascade`)

```sh
run_one() {  # usage: run_one NAME   (NAME = E1-01 | V1 | V2 | V3)
  name=$1
  out="$ITER/${name}_s$SEED"
  mkdir -p "$out"
  start=$(date +%s)
  ( cd "$REPO" && run_with_timeout "$TIMEOUT_S" "$PY" "$REPO/cad_agent.py" \
      --mode cascade --auto --seed "$SEED" --num-ctx 8192 \
      --l1 "$ITER/inputs/$name.l1.json" \
      --out "$out" \
      "$(cat "$ITER/inputs/$name.request.txt")" ) > "$out/run.log" 2>&1
  rc=$?
  echo "{\"name\": \"$name\", \"seed\": $SEED, \"rc\": $rc, \"secs\": $(( $(date +%s) - start ))}" >> "$ITER/runs.jsonl"
  echo "$name rc=$rc"
}

run_one E1-01
run_one V1
run_one V2
run_one V3
```

Run them strictly one after another, never in parallel. Worst case is 4 × 90 min = 6 h per
iteration.

**Convergence confirmation** (rubric section 7): when the E1-01 package of an iteration is judged
**MEETS**, run E1-01 with two more seeds in the same iteration folder before claiming convergence:

```sh
for SEED in $((SEED + 1)) $((SEED + 2)); do run_one E1-01; done
```

### 3.1b Assembly stub smoke arm (iteration 002 onward, until M13)

`--mode assembly` exists since iteration 001 (milestone M0) but stops early with a typed
`not implemented: <stage>` (exit 1, design.json `outcome: "failed"`, `assembly.stage` = the stage).
It makes **no LLM calls** yet, so it takes seconds. It proves the CLI, the catalogue load, the
import gate and the rules load. Run it after the section 3.1 runs (or instead of the cascade E1-01
run when its code path is unchanged; see below):

```sh
run_asm() {  # usage: run_asm NAME   (NAME = E1-01 | V1 | V2 | V3)
  name=$1
  out="$ITER/${name}_asm_s$SEED"
  mkdir -p "$out"
  start=$(date +%s)
  ( cd "$REPO" && run_with_timeout "$TIMEOUT_S" "$PY" "$REPO/cad_agent.py" \
      --mode assembly --auto --seed "$SEED" --num-ctx 8192 \
      --parts "$REPO/benchmarks/enclosure/parts" \
      --rules "$REPO/design_rules.json" \
      --l1 "$ITER/inputs/$name.l1.json" \
      --out "$out" \
      "$(cat "$ITER/inputs/$name.request.txt")" ) > "$out/run.log" 2>&1
  rc=$?
  echo "{\"name\": \"${name}_asm\", \"seed\": $SEED, \"rc\": $rc, \"secs\": $(( $(date +%s) - start ))}" >> "$ITER/runs.jsonl"
  echo "${name}_asm rc=$rc"
}

run_asm E1-01
```

Expected today: rc 1, `run.log` ends with `not implemented: parse_spec`, and
`$out/<timestamp>/design.json` has `assembly.stage == "parse_spec"`, `assembly.catalog` listing
the 11 catalogue parts and no `catalogue: ... failed the import gate` note. Any other ending
(a traceback, a dropped part, rc 2) is a defect to report. There is no package to judge yet; the
judge records "no package (stub)".

**Skipping the cascade baseline** (superseded by the run policy at the top of section 3: the cascade baseline is not run at all). The cascade code path (`cascade.py`, `cad_checks.py`, and
`cad_agent.py` outside `main()`'s mode switch) is unchanged since iteration 001. At seed 0
(greedy) it reproduces the same slab, so the Run step may skip the 90-minute cascade run of
E1-01 and the judges may record "unchanged, see iter_001". With any other seed it is a new sample
and should be run if time allows.

### 3.2 Target commands once `--mode assembly` exists (milestone M0 onward; implementers edit this)

Same as 3.1, with the agent line replaced by:

```sh
      --mode assembly --auto --seed "$SEED" --num-ctx 8192 \
      --parts "$REPO/benchmarks/enclosure/parts" \
      --rules "$REPO/design_rules.json" \
      --l1 "$ITER/inputs/$name.l1.json" \
      --out "$out" \
      "$(cat "$ITER/inputs/$name.request.txt")"
```

Switch section 3.1 to this command only when the full tree runs end to end (M13). Before that,
the Run step keeps using cascade as the baseline. Partial runs of assembly mode may be added as an
extra arm named `<name>_asm_s$SEED`.

### 3.3 Optional second arm: `with_models`

This arm runs only if `benchmarks/enclosure/parts/` holds imported models. Check for them:

```sh
find "$REPO/benchmarks/enclosure/parts" -type f \( -iname '*.stl' -o -iname '*.3mf' -o -iname '*.step' -o -iname '*.stp' \) | head
```

If any are listed and the agent supports `--with-models` (milestone M14), also run each request with
`--with-models` added and `out="$ITER/${name}_with_models_s$SEED"`. That arm is reported separately
in the ledger and is **not required for convergence**. Its scores are never mixed with the primary
arm (requirements.md section 7).

## 4. Where the outputs land

`cad_agent.py` always adds a timestamp folder under `--out`, so each run's package is at
`$ITER/<name>_s<SEED>/<YYYYmmdd-HHMMSS>/`. Find it with:

```sh
pkg=$(ls -d "$ITER/${name}_s$SEED"/2*/ | tail -1)
```

| File | Today (cascade baseline) | After assembly mode (ARCHITECTURE.md section 6) |
|---|---|---|
| run log | `$ITER/<name>_s<SEED>/run.log` (stdout + stderr) | same |
| run summary | `$ITER/runs.jsonl` (name, seed, rc, secs) | same |
| OpenSCAD source | `$pkg/model.scad` (one `union()`, single body) | `$pkg/base.scad`, `$pkg/lid.scad`, `$pkg/model.scad` (bodies + ghosts), `$pkg/print_<body>.scad` |
| STL | `$pkg/model.stl` (single fused body, written by the final Rebuild) | `$pkg/base.stl`, `$pkg/lid.stl` (closed pose, enclosure frame, mm) |
| 3MF | `$pkg/model.3mf` (ExportModel) | `$pkg/model.3mf` |
| renders | `$pkg/views/model_{iso,front,back,left,right,top}.png` | same + `$pkg/views/ghost_*.png` + `$pkg/views/print_<body>_iso.png` |
| design record | `$pkg/design.json` (request, seed, l1, outcome, components, cascade summary) | same + `assembly` (spec with provenance, contents, choices, assumptions, loop reports) + `$pkg/feature_graph.json` |
| checks / matrix | `$pkg/checks.json`, `$pkg/verification_matrix.{md,json}` | same |
| layout + self-report | not produced (so judge gate G0 fails: the expected baseline) | `$pkg/layout.json`, `$pkg/self_report.json` |
| LLM transcripts | `$pkg/llm/` | same |

The judge writes `judge.md` and `defects.json` next to the package, in
`$ITER/<name>_s<SEED>/` (rubric section 5). The ledger entry for the iteration links them.

**Expected baseline:** the cascade mode builds one fused body from a union of at most 8 primitive
parts, with no openings, no base/lid split, no layout.json and no self-report. Every E1-01 and
variant package should be judged WRONG at G0/G1. That is the starting error signal of the loop.
