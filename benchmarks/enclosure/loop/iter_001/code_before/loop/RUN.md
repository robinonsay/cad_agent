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
cd "$REPO" && "$PY" -m unittest test_cascade test_cad_checks test_review_fixes test_cad_agent test_benchmark_runner
```

The last command also runs any new `test_*.py` files the implementers added. Append their module
names to it as they appear (`test_parts test_feature_graph test_assembly_checks test_assembly test_no_hardcoding`).

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

### 3.2 Target commands once `--mode assembly` exists (milestone M0 onward; implementers edit this)

Same as 3.1, with the agent line replaced by:

```sh
      --mode assembly --auto --seed "$SEED" --num-ctx 8192 \
      --parts "$REPO/benchmarks/enclosure/parts" \
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
