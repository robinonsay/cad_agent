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
