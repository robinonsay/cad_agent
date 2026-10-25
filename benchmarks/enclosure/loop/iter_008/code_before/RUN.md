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
                            # iteration 007: SEED=5 (NOT 0: seed 0 was measured in 005 and 006 with byte-identical
                            # transcripts, so it carries no new information; iteration 006 delta section 4)
                            # iteration 008: SEED=8, all four requests (iteration 007 delta section 4)
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
iteration 002). Implementers append new modules to it as they appear. It takes about 310 s (343 tests); the
offline end-to-end test (`test_assembly.TestEndToEnd`) compiles E1-01, V1, V2 and V3 with OpenSCAD
(V2 and V3 since iteration 004), and `TestReplayIter005` replays iteration 005's answers at the real rules
(fn 64) since iteration 005. Since iteration 006 `TestEndToEnd` also re-applies rubric 3.4 literally to the
delivered STLs and brute-forces the grid feasibility of every part. Since iteration 007 `TestReplayIter007`
replays iteration 007's recorded V1/V2/V3 answers (from `iter_007/<name>_s5/*/llm/`; skipped if that folder is
missing) and `test_v1_socket_stack_apertures` runs V1 on a socket stack.

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
(spec slots, contents, edges, one confirmation; most are voted 3 times; since iteration 007 the stack is asked
only when the text names two or more mountings, and `assy_expose` is asked once (voted) per connector that a text
names by its plug but Contents left unexposed), then about 30 s of OpenSCAD per run.

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
run_one V1; run_one V2; run_one V3      # every iteration from 007 on: convergence needs each variant CORRECT
                                        # (ARCHITECTURE.md 8), and the variants have never been run by the real
                                        # controller. Iteration 006's Run skipped them and re-ran seed 0: a
                                        # process defect. Run all four, in this order, with the SEED of section 1.
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
| OpenSCAD source | `$pkg/base.scad`, `$pkg/lid.scad` (one body each), `$pkg/model.scad` (both bodies in the closed pose, references as `%` ghosts); `views.scad` / `ghost.scad` / `open.scad` (base only, lid off, references translucent; since iteration 006) are render-only files | `$pkg/model.scad` (one `union()`, single body) |
| STL | `$pkg/base.stl`, `$pkg/lid.stl` (closed pose, enclosure frame, mm; OpenSCAD's mesh, or manifold3d's when OpenSCAD fails or disagrees: `design.json` `assembly.stl_source`) | `$pkg/model.stl` |
| 3MF | `$pkg/model.3mf` (both bodies, one object each) | `$pkg/model.3mf` |
| renders | `$pkg/views/model_{iso,front,back,left,right,top}.png` (bodies) + `$pkg/views/ghost_*.png` (bodies translucent, references solid) + `$pkg/views/open_{iso,top}.png` (lid off: standoffs, bosses, rim; since iteration 006) | `$pkg/views/model_*.png` |
| design record | `$pkg/design.json`: request, seed, l1, outcome, and `assembly` (spec with provenance, contents, layout, fasteners, choices with who made them, assumptions, stl_source, components generated from the graph, results on the delivered STLs and on the manifold, notes) + `$pkg/feature_graph.json` | request, seed, l1, outcome, components, cascade summary |
| checks / matrix | `$pkg/checks.json` (rule-derived checks, `l1_id: "rules"`, and since iteration 007 `links`: the L1 ids each check is traced to), `$pkg/verification_matrix.{md,json}` (since iteration 007 one row per L1 over its linked checks with `status` PASS / FAIL / UNLINKED; UNLINKED = no traced check yet, milestone M10; a final `rules` row holds the unlinked checks) | `verification_matrix.*` as before |
| layout + self-report | `$pkg/layout.json` (frame, every reference part with catalogue id, params, x, y, z, rot_z, body print orientations, spec), `$pkg/self_report.json` (checks re-measured on the delivered STLs; `references` table; `apertures` per wall: through count and blind regions with their cut nodes, since iteration 006) | not produced |
| LLM transcripts | `$pkg/llm/` | same |

The judge writes `judge.md` and `defects.json` (or `judge_N.json`) next to the package, in
`$ITER/<name>_s<SEED>/` (rubric section 5). The ledger entry for the iteration links them.

**Expected now (iteration 008's Run; iteration 007 changes listed at the end of this section):** a tray base and a lid with a locating lip, four corner
pilaster bosses with lid screws, four standoffs with pilots under the board holes, and one opening per
exposed connector, sized from the plug envelope plus `plug_to_opening + design_margin` per side. The cavity
is bounded by the screw-head (V-HOLE-KO) columns and the screwdriver (V-DRIVER) radius around every board
hole, and every one-sided limit the derivation sets is derived at limit + `rules.design_margin` (0.1 mm):
clearances since iteration 004, and since iteration 006 also the pilot depths (5.1 / 6.1 mm), the lid-boss
OD (6.1 mm) and the lip engagement (2.1 mm). With correct controller answers E1-01 is about
83.12 x 62.32 x 24.70 mm (iteration 006 offline; the wider bosses add 0.17 mm in plan, the lip 0.1 mm in Z).

**E1-01 is expected to end `unsatisfied` (rc 3) with exactly one failing check, `grid_conformance`, and three
entries in `design.json` `assembly.conflicts`, one per part, each with a `kind`:** the Pico is
`flush_to_edge` (its pins are 1.13 mm off the assumed hole-1 grid normal to its edge; `normal_needed`
0.98 mm, a move off the flush position that rule flush_to_edge forbids), and each PJ-320A jack is
`pin_pattern` (its terminals, now read from the vendor drawing, cannot meet a 2.54 grid at any position:
best 0.54 mm). These go to Robin (questions 2 and 3), not to agent code. `no_pin_data` should be empty. V1,
V2 and V3 behave the same way offline (Pico `flush_to_edge`, each jack `pin_pattern`). rc 3 packages are
judgeable (section 3.4). New checks in `checks.json` since iteration 006: `pilot_engagement_<standoff|boss>_k`,
`boss_od_<standoff|boss>_k` and `lip_engagement` (all at their limits; the design sits 0.1 mm inside), and the
`apertures_<side>` checks now use rubric 3.4's full-extent wall slab and count only `through` regions (E1-01:
-X 1 through + 2 blind, +X 2 through + 2 blind, ±Y 0 through + 2 blind; the blind regions are the corner
pilots joined with the lid holes, listed with their node ids in `self_report.json` `apertures`).
Judges grading L3.1.6.1 should read `assembly.conflicts` and report the conflict kinds (iteration 006 delta
section 4).
Since iteration 005: `inside_board` (the board minus the seat columns) and `inside_contents` (every reference
except the board, `rules.part_to_wall`); `clear_module_<k>_envelope` is an `inside` check over the union of
the module's and its stacks' catalogue primitives; an exemption on a check with clearance c > 0 is the seat
columns grown by c (`clear_board` and `inside_board` about 1.10 mm for E1-01, `inside_contents` about 1.21,
the module envelope about 1.52). Every composite clear_of / inside result carries `per_source` d values and
`volume_parts`, and `self_report.json` has a top-level `references` table.
ConfirmArrangement still asks `assy_confirm` once per feasible board-symmetry class (6 for E1-01), plus at
most one voted `assy_arrange_pick`. ParseSpec re-asks when one number id fills two slots. Not yet checked by
the agent: printability, wall thickness by ray casting, other openings (V-AP-OTHER) and the install sweep.

Since iteration 007 (ARCHITECTURE.md 7.10):
- **ChooseStack is evidence-gated.** E1-01, V1 and V2 name no mounting, so they get male headers by catalogue
  default (`choices.stack[module_1].by = "rule:catalogue_default"`, plus an assumption) with no `assy_stack`
  question. V3 ("female header sockets", "8.5 mm") gets sockets by `rule:text_evidence`, with the quotes.
- **Text coverage.** A new stage, `ExposureCoverage`, runs after Contents. If an L1 names a micro-USB cable
  and Contents said the Pico is not exposed, it asks `assy_expose` (voted 3 times). On yes, the Pico is exposed
  (`choices.exposed[module_1].by = "llm:coverage"`). On no, the new check `text_coverage` fails and
  `assembly.conflicts` gets a `coverage` entry that quotes the L1. `assembly.coverage` records each case.
- **Check count.** Every package has one more check, `text_coverage` (E1-01 offline: 53 checks, only
  `grid_conformance` fails).
- **Matrix.** For E1-01, 6 L1s are linked (L1.1, L1.2, L1.4, L1.5, L1.6, L1.10) and 6 are UNLINKED.
- **Aperture slab.** It is inset by `measure_tol` on all six faces. A face is reached only by a cross-section at
  least `measure_tol` across, so the false `through` openings of the iteration 007 V1/V2 runs are gone.
- **Judging.** The judges must grade V1, V2 and V3 as well as E1-01 (iteration 007 delta section 4).
