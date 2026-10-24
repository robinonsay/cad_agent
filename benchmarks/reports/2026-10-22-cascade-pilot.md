# Cascade pilot: status report, 2026-10-22

## In short

- **Built:** the cascade mode (`--mode cascade --l1 ...`) is working. It includes typed checks, the gates that decide which checks to trust, the control loops, and a verification matrix. All 188 unit tests pass. The default mode and CLI still work as before, with one change: exit code 3 now means "built but some requirement fails".
- **Pilot:** 70 runs on 10 dev requests. **The cascade produced the most correct designs:** 15 of 20 runs (75%), against 63% for the default mode with requirements, 40% without requirements, and 70% for best-of-3.
- **Trust:** when the cascade said "verified", it was right every time (0 of 6 wrong). The default mode was wrong about 1 time in 4 when it said "verified" (6 of 23 with requirements).
- **The cascade is too strict.** It rejected 9 of its 15 good designs, mostly because the model could not turn some requirements into checks that pass the gates, or because a check it wrote was itself wrong.
- **The sample is small.** With 10 requests (one of which always hangs), none of the differences is statistically significant. The direction is encouraging, but it is not proof.
- **Recommendation:** do **not** run the full held-out study yet. First fix the ball-shaped part hang and the three main causes of false failures, then run a larger dev pilot (5 seeds). Details are in the last section.

## 1. What was built

All files are in `/Users/robinonsay/python/llm-bt` and are untracked. Nothing was committed.

| File | Lines | What it is |
|---|---|---|
| `cad_agent.py` | 2,938 | Existing agent, extended. Components now carry a status (verified, unsatisfied or pending) and what is still wrong. New `--seed`, `--l1` and `--mode cascade` options. design.json records the outcome. Exit codes: 0 = all passed, 3 = built but failing, 2 = bad command line. |
| `cad_checks.py` | 2,517 | **The typed check library.** It has 13 check types: count, dimension, shape, relation, edge, span, arrangement, touches, connected, no_overlap, stable, fits and rests_on. Each check returns pass/fail, a signed margin (0 = on the limit, negative = violated) and readable evidence. The physical checks use the real solids. It also contains the mutant generator (deliberately broken copies of a design), the gates, the error ranking, sensitivity analysis and direct fixes. |
| `cascade.py` | 1,720 | **The cascade mode.** It turns each requirement into checks, freezes them, then runs a design loop that only accepts a change if the error goes strictly down. An outer loop refines or drops sub-checks. It writes `verification_matrix.md/.json`. |
| `benchmarks/run.py` | 255 | Benchmark runner. Runs one at a time with a lock and a 20-minute timeout, can resume, and writes `results.jsonl`. |
| `benchmarks/dev.json` | | 16 dev requests with user-style requirements. They do not overlap with held-out. |
| Tests | 2,830 | `test_cad_agent.py`, `test_cad_checks.py`, `test_cascade.py`, `test_benchmark_runner.py`, `test_review_fixes.py`. **188 tests, all passing (65 s).** All use fakes and need no network. |

A code review found 17 problems, and all were fixed before the pilot. Several of them made the cascade report "verified" when it should not have; those all have regression tests now. `benchmarks/heldout.json` has not been touched or run.

## 2. How the pilot was run

- **Requests:** 10 dev requests: 5 simple single-part objects (D1-02 to D1-06) and 5 two-part objects (D2-01, D2-03 to D2-06). D1-01 and D2-02 were dropped because they hang every time (see open problem 1). D2-03 has the same hang and was kept, so it shows up as "no design" in every condition.
- **Conditions:**

| | Condition | Runs |
|---|---|---|
| A | Default mode, request only (no requirements) | 10 requests × 2 seeds |
| B | Default mode, request plus requirements | 10 × 3 seeds |
| C | Cascade mode, request plus requirements | 10 × 2 seeds |
| D | Best of B's 3 seeds, picked by the frozen checks | 10 picks |

- **Grading:** a separate reviewer graded each design from its renders alone, without knowing which condition made it ("blind"). That reviewer was a Claude grader, not you. Each design got CORRECT, MINOR or WRONG, plus pass or fail for each requirement.
- **One correction to the grades:** the egg holder (D2-05) asks for 2 mm cup walls. design.json shows that every B and C design built 1 mm walls: the model used the egg's 43 mm as the cup's inner diameter. The visual grader caught this in only 1 of 5 cases. The tables below use the corrected grades, with the uncorrected figures in brackets where they differ.
- **What counts as a failure:** a run that produced no design (timeout or crash) counts as not correct.

## 3. Results

### 3.1 Does the design come out right? (blind grade)

| | A: no reqs | B: with reqs | C: cascade | D: best of 3 (B) |
|---|---|---|---|---|
| Runs | 20 | 30 | 20 | 10 |
| Produced a design | 16 | 27 | 18 | 9 |
| **CORRECT** | **8 (40%)** | **19 (63%)** [21, 70%] | **15 (75%)** [16, 80%] | **7 (70%)** [8, 80%] |
| CORRECT or MINOR | 8 (40%) | 22 (73%) | 17 (85%) | 8 (80%) |
| WRONG | 8 | 5 | 1 | 1 |
| No design | 4 | 3 | 2 | 1 |
| Requirements met (designs only) | 50/63 (79%) | 96/108 (89%) | 67/72 (93%) | 33/36 (92%) |
| Requirements met (no design = all failed) | 50/76 (66%) | 96/120 (80%) | 67/80 (84%) | 33/40 (83%) |

### 3.2 Can you trust the system's own "pass"?

Two different things can say "pass":

1. **Own verdict:** the agent's own verdict for that run. Default mode uses its back-translation check; the cascade uses its frozen checks.
2. **Common checks:** one shared set of frozen checks, taken from the cascade's seed-0 run and applied to every design afterwards for scoring.

In the table, "bad" means the grader called the design WRONG or at least one requirement failed. "Good" means CORRECT with every requirement met.

| | A | B | C | D |
|---|---|---|---|---|
| Own verdict says "verified" | 8 / 20 | 23 / 30 | 6 / 20 | 9 / 10 |
| **False pass:** said verified but actually bad | **2 of 8 (25%)** | **6 of 23 (26%)** | **0 of 6 (0%)** | **2 of 9 (22%)** |
| Bad designs that slipped through | 2 of 8 | 6 of 8 | 0 of 3 | 2 of 2 |
| **False fail:** good design rejected | 2 of 8 | 2 of 19 (11%) | **9 of 15 (60%)** | 0 of 7 |
| Common frozen checks all pass | 6 / 20 | 12 / 30 | 10 / 20 | 6 / 10 |
| False pass on common checks | 0 | 0 | 0 | 0 |
| False fail on common checks | 2 of 8 | 7 of 19 | 5 of 15 | 1 of 7 |

How to read this:

- **The default mode's self-check is too lenient.** With requirements, 6 of the 8 bad designs were still called "verified". Examples: a napkin holder with only one panel, a letter rack whose base was turned 90°, and egg cups with 1 mm walls.
- **The cascade's verdict is strict and, in this pilot, never falsely passed.** It caught all 3 of its own bad designs: one missing panel, and the 1 mm egg-cup walls twice. The cost is many false failures (section 4).
- **No design passed the common frozen checks while being bad.** That number is flattering, though: the checks match part names strictly, and several are wrong, so they also fail many good designs.

### 3.3 Cost (designs only, per run)

| | A | B | C | D |
|---|---|---|---|---|
| Median wall time | 55 s | 47 s | 114 s | 47 s per run, about 140 s for all 3 |
| Median LLM calls | 24 | 20 | 45 | 18 per run, about 55 for all 3 |

The 1,200 s timeouts (D2-03 everywhere) are left out of the medians. The cascade costs about 2.4 times as much as one default run with requirements, roughly the same as best-of-3.

### 3.4 How the cascade's runs ended (C, 20 runs)

| Outcome | Runs |
|---|---|
| Verified | 6 |
| Unsatisfied, but the only problem was a requirement with no accepted check ("unverified") | 6 |
| Unsatisfied because a wrong check failed a good design | 3 |
| Unsatisfied because of a real fault, correctly caught | 3 |
| Timeout (ball hang, D2-03) | 2 |

Inside those runs, each loop also ended with one of the typed reports:

- **Design loop (18 runs):** 12 converged (all checks passed or nothing left to fix) and 6 stagnated (no change made the error strictly smaller). None was "uncontrollable": no check was found that no design change could move.
- **Requirement-to-check translation (72 requirements):**
  - 41 converged, with an accepted check.
  - 26 saturated: they ran out of attempts, and some of their checks never passed the gates.
  - 5 stagnated.
- **Outer loop:** it added sub-checks in 3 runs (D2-04 seed 1, and D2-05 seed 0 three times and seed 1 once). It never dropped one. Each time it added sub-checks, the requirement involved a stand-in object (a letter or an egg).

### 3.5 Paired comparison per request

For each request, I compared the share of CORRECT runs between two conditions. D2-03 is a tie at 0 everywhere.

| Comparison | First better | First worse | Tie | Sign-test p |
|---|---|---|---|---|
| C (cascade) vs B (default + reqs) | 3 (D1-03, D2-01, D2-04) | 0 | 7 | 0.25 |
| C vs D (best of 3) | 1 (D2-01) | 0 | 9 | 1.0 |
| B vs A (requirements help?) | 5 | 2 (D2-04, D2-05) | 3 | 0.45 |
| C vs A | 5 | 1 (D2-05) | 4 | 0.22 |

**What the sample supports:**

- Most plausible, but still not significant (p 0.22 to 0.45): adding requirements (B, C) beats the bare request (A). The reason is easy to see in the renders: without requirements, the model often adds duplicate parts or turns a part the wrong way.
- Suggestive, not shown: the cascade makes the design itself better than the default mode with requirements. It never lost a request, but it won only 3 of 10, which is far from significant. To get p < 0.05 with a sign test, it would need to win about 6 of 6 untied requests. Most requests are easy enough that every condition gets them right, so they tell us nothing.
- The clearest result is the trustworthiness of "verified": 0 false passes in 6 for the cascade, against 6 in 23 for default mode. Even that is only 6 cascade verdicts, so the true false-pass rate could plausibly still be around 30–40%.
- Only 2–3 seeds per request were run, and the cascade wrote different checks for each seed, so the run-to-run spread is not well measured.

## 4. Why the cascade rejects good designs

9 of the 15 good cascade designs were reported as not passing. The causes are:

| Cause | Runs | Example |
|---|---|---|
| The model never produced an accepted check for a requirement, so it stays "unverified" | 6 | "The ruler shall be a single flat strip" (D1-02): every proposed check was rejected by the gates. "Open at both ends" and "axis vertical" (D1-05): the checks passed, but the word gate wanted a check for "each end" or "upright" and none was accepted. |
| The check itself is wrong | 3 | D1-06: "0 mm tall at the front" became "height = 0 mm". D2-01: both panels were named `front_panel`, so the back one fails "along the front edge". D2-04 seed 1: "a letter 5 mm thick" became a 160 × 240 × 30 mm book. |

**A wrong check can also push the design the wrong way.** In D2-05 seed 0, the impossible check "a 43 mm egg drops into a 45 mm cup" made the design loop change the cups to 25 mm tall.

## 5. Worst failure types by condition

| Condition | What went wrong (most serious first) |
|---|---|
| A: no requirements | Extra duplicate parts (a second block stacked crosswise, a second rolling pin, extra wedges and legs) in 5 runs. A bangle standing on its edge (2 runs). Napkin holder with one panel. 2 crashes and 2 timeouts. Two bad designs were still called "verified". |
| B: default + reqs | Bad designs called "verified": napkin holder with one panel (2 runs, one also rotated and overhanging), letter rack with the base turned 90° so the dividers overhang (2 runs), and 1 mm cup walls (3 runs: the egg's 43 mm became the inner diameter). One duplicate block. 3 timeouts. |
| C: cascade | 1 WRONG design (one panel), and it was correctly flagged. Cups pushed to 25 mm tall by a wrong check. 1 mm cup walls, flagged both times. The main problem is good designs being rejected (section 4). 2 timeouts. |
| D: best of 3 | Picked the one-panel napkin holder even though B seed 2 was correct, because the frozen D2-01 checks are wrong and favour the wrong design. Picked a 1 mm-wall egg holder. The picker is only as good as its checks. |

## 6. Open problems, in priority order

1. **Hang with ball-shaped parts.** A ball touches a flat face at a single point, so the attachment search finds no allowed side, and the "choose side → refill sizes" step retries with no limit. This makes D1-01, D2-02 and D2-03 (3 of 16 dev requests) time out at 20 minutes in every mode. Each retry is also slow (about 100 s), because the schema-constrained reply is padded out to the full token limit. **This has to be fixed before any larger study.**
2. **Checks can't tell copies of one part apart.** When the model makes one `front_panel` part with 2 copies, no check can say "one at the front and one at the back". Parts need roles (e.g. `panel[front]`, `panel[back]`), or the edge check needs a "one copy per edge" form.
3. **Requirements left "unverified".** The gates are too strict for simple statements like "a single flat strip", "open at both ends" and "axis vertical". A small set of standard check templates for these common phrases would help: count = 1 of one shape, tube open, axis = z. They would be filled by Python, not the model.
4. **Wrong checks get through the gates.** "0 mm at the front edge" read as overall height, an impossible fit, and a "book" for a letter. These suggest two new gates: a **satisfiability gate** (the check must be passable by some design in the library, e.g. checked with a Python-built design) and a **stand-in size gate** (the stand-in's size must come from the requirement text).
5. **Requirement text leaks into sizes.** In B and C, "an egg 43 mm across" changed the cup's inner diameter from 41 mm to 43 mm. In A, with no requirements, the walls came out right.
6. **Two crashes in default mode** (exit code 1, D1-06 and D2-01 seed 1, condition A). Not yet investigated.
7. **The visual grader misses small dimensions.** It missed 1 mm walls in 4 of 5 cases. Future grading should combine the renders with the measured sizes from design.json.
8. **Best-of-N scoring is circular** when the same frozen checks both pick the winner and score it. Future studies should score best-of-N only by the blind grade.

## 7. Recommended next step

**Don't run the held-out study yet.** As things stand, about 10% of runs would be guaranteed timeouts (ball shapes). The cascade's 60% false-fail rate would also make its "verified" rate meaningless as a headline number.

Suggested order:

1. Fix the ball hang. Add a retry limit, allow point or line contact for spheres, and cap the padded replies.
2. Add roles for part copies, standard templates for the common phrases, and the satisfiability and stand-in gates (problems 2–4).
3. Run the dev pilot again on all 16 dev requests with **5 seeds** for B and C (about 160 runs, roughly 6–8 hours on the one model server). Grade blind, with design.json sizes alongside the renders. Go ahead when, with false passes still at or near zero, the cascade's false-fail rate is below about 20% and no run times out.
4. Then run the held-out study. Two points about it:
   - **The design needs one decision:** the cascade cannot run without requirements, so a 2×2 of mode × (with/without requirements) has one empty cell. A workable set is A, B, C, plus best-of-5 from B, plus best-of-N from C, all scored by blind grade only.
   - **Expected size:** 30 requests × 5 seeds × 3 conditions is 450 runs, at about 1–2 minutes each, or roughly 12–20 hours of machine time with no timeouts. Best-of-N comes from the B and C seeds at no extra cost.
   - **What it can show:** with 30 requests, a difference of about 6–8 requests won and none lost would reach significance, which is a realistic target if the cascade's current direction holds.

## Where everything is

- Pilot runs and raw results: `/private/tmp/claude-501/-Users-robinonsay-python-llm-bt/7d706733-5c1d-44fb-a74b-bc29203e1df6/scratchpad/pilot/` (`results.jsonl`, `summary.json`, `blind_key.json`, run folders)
- Analysis for this report: `/private/tmp/claude-501/-Users-robinonsay-python-llm-bt/7d706733-5c1d-44fb-a74b-bc29203e1df6/scratchpad/final/analyze.py`. Run `CORRECTED=1 python3 analyze.py` for the corrected grades.
- Backup of the original code from before this work: `.../scratchpad/backup_before_workflow/`
- Note: the claude-context code-search server failed to connect throughout this session, so grep and direct file reads were used instead.
