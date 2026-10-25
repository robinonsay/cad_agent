# RUN: how the Run step runs the CAD agent each iteration

The Run step is the **only** step in the loop that runs a local LLM. It runs the agent on the target
(E1-01) and on each variant (V1, V2, V3), one run at a time, and leaves one design package per run
for the judge (`../rubric.md`).

**Implementers keep this file current.** When the CLI changes, update section 3 in the same delta
and record that in the ledger.

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
    test_parts test_feature_graph test_assembly test_assembly_checks test_no_hardcoding
```

The last command also runs the assembly-mode test files (iteration 001; `test_assembly_checks` added in
iteration 002). Implementers append new modules to it as they appear. It takes about 40 s; the
offline end-to-end test (`test_assembly.TestEndToEnd`) compiles E1-01 and V1 with OpenSCAD.

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
> - **Every iteration runs ONLY the assembly arm** (`run_one`, section 3.1; `run_asm` is the same command) for E1-01, and for the variants when the loop asks for them. Its output is what the judges grade.
> - **Do NOT run the cascade baseline** (now the cascade reference arm, section 3.1b). It is already recorded in iter_001 (a 90-minute timeout). The cascade code path cannot change the judges' verdict, and it keeps the single Ollama server busy for 1.5 h.
>   - Run it again only if an implementer explicitly asks for it in that iteration's LEDGER entry, because they changed `cascade.py` or `cad_checks.py` in a way meant to affect it.
> - **While assembly mode is a stub** (exit 1, `not implemented: <stage>`), there is no package to judge. Report the output with `has_renders: false`, and the loop records "no package (stub)" without spending judge time.
> - **Implementers:** when assembly mode produces a package (SCAD/STL + renders), make sure `run_asm` writes renders to `views/` so it is judgeable.
>
> *(Iteration 002 implementer: only the section references in the first two bullets were updated, because
> section 3.1 now is the assembly arm. Assembly mode is no longer a stub: it writes a package with renders in
> `views/`.)*

Exit codes from `cad_agent.py`: 0 = verified by its own checks, 3 = built but its own checks fail
(NOT a pass), 1 = failed, 2 = usage error, 130 = interrupted, 124 = killed by the 90-minute
timeout. The agent's own verdict is never the loop's verdict. The judge decides.

### 3.1 The judged runs: `--mode assembly` (iteration 003 onward)

Assembly mode writes a two-body package since iteration 002 (walking skeleton, ARCHITECTURE.md 7.1
step 2 and 7.4), so it is the judged target. A run takes a few minutes: about 13 LLM questions
(spec slots, contents, stack, edges, one confirmation; most are voted 3 times), then about 30 s of
OpenSCAD per run.

```sh
package_missing() {  # usage: package_missing OUT_DIR  -> a JSON list of the missing package files (section 3.4)
  pkg=$(ls -d "$1"/2*/ 2>/dev/null | tail -1)
  "$PY" - "$pkg" <<'EOF'
import json, sys
from pathlib import Path
pkg = Path(sys.argv[1]) if sys.argv[1] else None
need = ["base.stl", "lid.stl", "layout.json", "self_report.json"]
print(json.dumps([f for f in need if pkg is None or not (pkg / f).is_file()]))
EOF
}

run_one() {  # usage: run_one NAME   (NAME = E1-01 | V1 | V2 | V3)
  name=$1
  out="$ITER/${name}_s$SEED"
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
  secs=$(( $(date +%s) - start ))
  missing=$(package_missing "$out")            # section 3.4
  echo "{\"name\": \"$name\", \"seed\": $SEED, \"rc\": $rc, \"secs\": $secs, \"missing\": $missing}" >> "$ITER/runs.jsonl"
  echo "$name rc=$rc missing=$missing"
}
run_asm() { run_one "$@"; }   # the name Robin's run policy uses

run_one E1-01
# run_one V1; run_one V2; run_one V3      # when the loop asks for the variants
```

Run requests strictly one after another, never in parallel.

How a run is judged:

- **A package exists** (rc 0 or 3): it is judged with `../rubric.md`. rc 3 means the agent's own checks
  failed; `verification_matrix.md` and `self_report.json` say which.
- **The run ends with `not implemented: <stage>`**, or with any other rc 1 and no package: it is judged
  **G0 FAIL ("no package")**, and the judge names the stage from `design.json` `assembly.stage` and the
  last `assembly.notes` entry (for example `parse_spec: no number in the text for board_width`). Such a run
  is never silently replaced by the cascade.

**Convergence confirmation** (rubric section 7): when the E1-01 package of an iteration is judged
**MEETS**, run E1-01 with two more seeds in the same iteration folder before claiming convergence:

```sh
for SEED in $((SEED + 1)) $((SEED + 2)); do run_one E1-01; done
```

### 3.1b The cascade reference arm (only when its code path changed, or for a non-zero seed)

The cascade baseline (`--mode cascade`) was judged in iteration 001 (90-minute timeout, a 90 x 74 x 4
slab). Run it again only when `cascade.py`, `cad_checks.py` or the cascade-relevant parts of
`cad_agent.py` changed (the ledger entry says so), or when the seed is not 0. Otherwise the judges
record "unchanged, see iter_001" (seed 0 is greedy and reproduces the same slab). This saves
90 minutes of Ollama time per iteration.

```sh
run_cascade() {  # usage: run_cascade NAME
  name=$1
  out="$ITER/${name}_cascade_s$SEED"
  mkdir -p "$out"
  start=$(date +%s)
  ( cd "$REPO" && run_with_timeout "$TIMEOUT_S" "$PY" "$REPO/cad_agent.py" \
      --mode cascade --auto --seed "$SEED" --num-ctx 8192 \
      --l1 "$ITER/inputs/$name.l1.json" \
      --out "$out" \
      "$(cat "$ITER/inputs/$name.request.txt")" ) > "$out/run.log" 2>&1
  rc=$?
  echo "{\"name\": \"${name}_cascade\", \"seed\": $SEED, \"rc\": $rc, \"secs\": $(( $(date +%s) - start ))}" >> "$ITER/runs.jsonl"
  echo "${name}_cascade rc=$rc"
}
```

### 3.2 Rule: which arm is judged

Assembly mode is the judged target from iteration 003 on, the first Run that has a package writer
(this replaces the earlier "switch at M13" rule; ARCHITECTURE.md 7.4). Partial or failed assembly runs
are judged as they are (section 3.1, "How a run is judged"). The cascade arm (3.1b) is a reference
only and is never graded in place of the assembly run.

### 3.3 Optional second arm: `with_models`

This arm runs only if `benchmarks/enclosure/parts/` holds imported models. Check for them:

```sh
find "$REPO/benchmarks/enclosure/parts" -type f \( -iname '*.stl' -o -iname '*.3mf' -o -iname '*.step' -o -iname '*.stp' \) | head
```

If any are listed and the agent supports `--with-models` (milestone M14), also run each request with
`--with-models` added and `out="$ITER/${name}_with_models_s$SEED"`. That arm is reported separately
in the ledger and is **not required for convergence**. Its scores are never mixed with the primary
arm (requirements.md section 7).

### 3.4 Run-step self-check (after each assembly run)

The package must hold `base.stl`, `lid.stl`, `layout.json` and `self_report.json`. `run_one` checks this
with `package_missing` (defined in the section 3.1 block) and records the missing files in `runs.jsonl`
as `"missing": [...]`: an empty list when all four are there, all four when no package folder exists.
A non-empty list on an rc 0 or rc 3 run is a defect to report in the ledger.

## 4. Where the outputs land

`cad_agent.py` always adds a timestamp folder under `--out`, so each run's package is at
`$ITER/<name>_s<SEED>/<YYYYmmdd-HHMMSS>/`. Find it with:

```sh
pkg=$(ls -d "$ITER/${name}_s$SEED"/2*/ | tail -1)
```

| File | Today (assembly mode, ARCHITECTURE.md section 6) | Cascade reference arm (3.1b) |
|---|---|---|
| run log | `$ITER/<name>_s<SEED>/run.log` (stdout + stderr) | `$ITER/<name>_cascade_s<SEED>/run.log` |
| run summary | `$ITER/runs.jsonl` (name, seed, rc, secs, missing) | same file (no `missing`) |
| OpenSCAD source | `$pkg/base.scad`, `$pkg/lid.scad` (one body each), `$pkg/model.scad` (both bodies in the closed pose, references as `%` ghosts); `views.scad` / `ghost.scad` are render-only files | `$pkg/model.scad` (one `union()`, single body) |
| STL | `$pkg/base.stl`, `$pkg/lid.stl` (closed pose, enclosure frame, mm; OpenSCAD's mesh, or manifold3d's when OpenSCAD fails or disagrees: `design.json` `assembly.stl_source`) | `$pkg/model.stl` |
| 3MF | `$pkg/model.3mf` (both bodies, one object each) | `$pkg/model.3mf` |
| renders | `$pkg/views/model_{iso,front,back,left,right,top}.png` (bodies) + `$pkg/views/ghost_*.png` (bodies translucent, references solid) | `$pkg/views/model_*.png` |
| design record | `$pkg/design.json`: request, seed, l1, outcome, and `assembly` (spec with provenance, contents, layout, fasteners, choices with who made them, assumptions, stl_source, components generated from the graph, results on the delivered STLs and on the manifold, notes) + `$pkg/feature_graph.json` | request, seed, l1, outcome, components, cascade summary |
| checks / matrix | `$pkg/checks.json` (rule-derived checks, `l1_id: "rules"`), `$pkg/verification_matrix.{md,json}` (L1 rows say "no check covers this requirement" until translation, milestone M10) | same names |
| layout + self-report | `$pkg/layout.json` (frame, every reference part with catalogue id, params, x, y, z, rot_z, body print orientations, spec), `$pkg/self_report.json` (checks re-measured on the delivered STLs) | not produced |
| LLM transcripts | `$pkg/llm/` | same |

The judge writes `judge.md` and `defects.json` (or `judge_N.json`) next to the package, in
`$ITER/<name>_s<SEED>/` (rubric section 5). The ledger entry for the iteration links them.

**Expected now (iteration 003's Run):** a tray base and a lid with a locating lip, four corner
pilaster bosses with lid screws, four standoffs with pilots under the board holes, and one opening per
exposed connector, sized from the plug envelope. With correct controller answers the agent's own
checks pass (rc 0). Not yet checked by the agent: printability, wall thickness by ray casting, other
openings (V-AP-OTHER), the install sweep and screwdriver access (next iteration).
