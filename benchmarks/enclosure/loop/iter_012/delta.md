# Iteration 012: gap analysis and delta design

Inputs: eight runs, all rc 0 (`verified`), from one code version (`iter_012/code_sha1.txt`; the working tree still
matches it, `shasum -c` OK on all 9 files):

| Run | Verdict (both judges) | Class | Score | Worst w3 margin | Failing L3 |
|---|---|---|---|---|---|
| target_s0 (E1-01, seed 0) | **MEETS** | CORRECT | 1.0 | +0.20 | none |
| E1-01_s12 (seed 12) | **MEETS** | CORRECT | 1.0 | +0.20 | none |
| V1_s0, V1_s12 | DNM | **CORRECT** | 0.985 | +0.20 | L3.1.3.1 (w2) only |
| V2_s0, V2_s12 | DNM | **CORRECT** | 0.985 | +0.20 | L3.1.3.1 (w2) only |
| V3_s0, V3_s12 | **MEETS** | CORRECT | 1.0 | +0.20 | none |

Tooling: the claude-context MCP server failed to connect this session (ToolSearch: "configured MCP servers failed to
connect ... claude-context"). I read files at known paths and used targeted grep only. I did not edit any code.

## 1. Where the loop stands

Convergence (ARCHITECTURE.md section 8, rubric section 7) needs two things:

- **E1-01 MEETS on 3 seeds.** Now 2 of 3: seeds 0 and 12, both from the same code version.
- **Each variant at least CORRECT on 1 run.** Done: V1, V2 and V3 are all CORRECT on both seeds, and V3 MEETS.
  `test_no_hardcoding` is green, and so is the full suite (iteration 011 entry: 385/385).

So the one thing left is a third E1-01 seed that MEETS. RUN.md section 3.1 asks for the convergence confirmation
"in the same iteration". The Run step could not do that, because it runs before the judges and the confirmation
depends on their verdict (RC-1203 below).

The controller made no wrong final choice in any of the 8 runs. Within a request, both seeds produced the same
feature graph, spec and layout. For example, `feature_graph.json`, `layout.json` and `assembly.spec` of target_s0 and
E1-01_s12 are identical, and their STLs differ only in OpenSCAD's float/facet order.

## 2. Defects and root causes

### Graded defects

**D1. V1 and V2, L3.1.3.1 (w2): the USB mouth X position.** This is not an agent gap. It is a test-data conflict, the
same as iteration 011 and open as **Q9**.

- **What the agent was given.** The agent's inputs (`iter_012/inputs/V1.*`, `V2.*`: the request and L1s) do not state
  any mouth position. The window [−1.8, 0.5] / [−1.8, −0.8] exists only in `variants.json` `grading_deltas`. That
  file is judge-side data and the agent never receives it.
- **What the agent did.** It followed L2.1.3 as Robin rewrote it ("first header pin on the grid column nearest the
  −X edge") and OWNER_DECISIONS 1.
- **What the judges found.** All four judges independently say that no design can satisfy the window together with
  L3.1.6.1 on the catalogue grid. The first column is at X 5.71 (V1) / 5.63 (V2), which puts the mouth at
  X ≥ 3.04 / 2.96.
- **Why changing the agent would be wrong.** Moving the Pico to the window would break L3.1.6.1 and OWNER_DECISIONS 1.
  It would also hard-code a judge-side number into agent logic (principle 2 and 7.7: "a judge-side L3 number the
  agent never receives is never copied into agent logic").
- **Effect on convergence.** None. The defect is weight 2, so V1 and V2 stay CORRECT, which is what convergence
  needs.

### Ungraded observations, traced

**O1. Thin margins of 0.10 mm.** These are the keep-outs, the screw-head columns and the plug clearances (0.40
against a 0.30 limit). They are intended: the 7.7 / 7.9 setpoint rule targets limit + `rules.design_margin`
(0.10 = 5 × the judge's ε). No change.

**O2. V2: the jacks touch the Pico PCB edge at Y = 12.000 with a 0 gap.** V3's capacitor is 0.16 mm from the Pico
PCB. Both pass L3.1.4.1 (intersection ≤ 0.01 mm³). One judge adds that a real PJ-320A body is 12.2 long, which would
overlap the Pico by about 0.2 mm. This is a latent gap with two parts:

- **RC-1201a (catalogue).** The jack body is 12.0 × 6.0 with no nose. The XKB drawing says 12.2 × 6.1 behind a
  2.0 mm nose. This has been known since iteration 006 (7.9) and is still deferred.
- **RC-1201b (rule).** `layout.py` treats references as colliding only when they overlap (`interference_max`, a
  volume). No generic part-to-part assembly gap exists, unlike `part_to_wall` (0.2) for printed surfaces.

It is ungraded, it does not touch E1-01 (there the Pico and the jacks are about 2.6 mm apart along X), and the
judge's reference model M-JACK is itself 12.0 × 6.0. Fixing the catalogue alone would put the agent's references out
of step with the judge's references. This is deferred as **Q12** for Robin (section 6). It is not part of this delta.

**O3. Corner bosses reach about 0.2 mm into the cavity corners.** This is known from 7.5. The lid lip is notched
there, and the judges call it harmless. No change.

**O4. The lid screws have no counterbore, so the M3 heads stand proud of the lid.** No requirement covers this. It
is noted for Robin (section 6).

**O5. Rubric-side notes.** These are for Robin, not the agent:

- The rubric's pilot table Ø2.0–2.2 disagrees with L2.3.3's Ø1.6–1.8 (**Q8**, still open).
- The rubric's cavity definition (hull minus solids) takes in exterior pockets past the end walls when features
  protrude.
- The end-wall aperture recipe picks up the blind boss pilots.

The judges handled each case correctly. **Q13** in section 6.

### Latent controller gap, found in the transcripts (not in any verdict)

**RC-1202. The arrangement's "vote winner" can be chosen by Python's side order, not by the controller.** This is
control logic: `assembly.ArrangeContents.candidates` / `assignments` / `decide`.

- **What happened in E1-01_s12.** The three edge samples were all `{module_1: -X, connector_1: -X}` (both on one
  end). That layout is infeasible (`ports_do_not_fit`).
- **Why the tie-break decided.** `assignments` scores candidates by *per-item marginal* votes. That left six
  feasible candidates tied at 3 votes, each one item away from the answer: (−X,+X), (+X,−X), (−Y,−X), (+Y,−X),
  (−X,−Y) and (−X,+Y). The tie was broken by `[sides.index(s) for s in combo]`. (−X,+X) comes first only because
  `-X` precedes `-Y` in `SIDES`. It happened to be class 0 (the correct one). `decide` then logged `llm:vote+rank`,
  although the vote's own joint answer was infeasible.
- **What happens if the tie-break picks another class.** (−Y,−X) is class 3, with p_yes 0.117 against class 0's
  0.199. Had the tie-break picked it, `decide` would have asked the sampled A/B question.
- **Why this has not failed yet.** The deterministic p_yes rank has put the correct class first in every run since
  iteration 008. Each of the three A/B picks on record went 3:0 to the top-ranked class: iter_008 V3_s8, iter_011
  V1_s0 and iter_012 V1_s0. Every recorded final arrangement since iteration 004 (25 runs, 19 of them judged) is rank 1.
- **Verdict.** The gap is real but has not cost a verdict. Its fix (C1, section 3) changes `ArrangeContents`, which
  sits on the path that has now passed twice. It is therefore **contingent**: implement it only if a confirmation
  seed fails at the arrangement.

**RC-1203 (process). The convergence confirmation is conditioned on a verdict the Run step cannot see.** RUN.md
section 3.1 says "if target_s0 and E1-01_s12 both MEET, run SEED + 1, SEED + 2 in the same iteration". The Run step
ends before the judges start, so it cannot know whether both MEET. The fix is a RUN.md / LEDGER procedure change
(C0). There is no agent change.

## 3. Delta

**Principle for this iteration: code freeze.** The three E1-01 seeds that prove convergence should come from one
agent version. Otherwise "MEETS on 3 seeds" mixes controllers. The two passing seeds were produced by the code in
`iter_012/code_sha1.txt`. The smallest change that closes the highest-leverage gap (the missing third seed) is
therefore **no agent change at all**: run the confirmation on that exact code. ARCHITECTURE.md section 8 now states
this rule (refinement added this iteration).

### C0 (RC-1203): convergence-confirmation run on the frozen code (RUN.md, LEDGER; no code)

**C0.1. RUN.md section 1, iteration-013 note.** Use `NNN=013`. The Run step runs only:

```sh
cd $REPO && shasum -c benchmarks/enclosure/loop/iter_012/code_sha1.txt   # must print 9 x OK; stop if not
for SEED in 13 14; do run_one E1-01; done                                 # E1-01_s13, E1-01_s14
```

- **Expected result.** Two rows in `runs.jsonl`, `E1-01_s13` and `E1-01_s14`.
- **Runs left out.**
  - **target_s0.** Seed 0 on frozen code is byte-identical in transcript (measured in 005/006 and 011/012), so it
    carries no new information.
  - **V1–V3.** They have already met their convergence condition on this code.

  Leaving these out keeps the Ollama time to about 3 minutes.
- **Copy the hashes.** Copy `iter_012/code_sha1.txt` to `iter_013/code_sha1.txt` before the runs.

**C0.2. RUN.md section 3.1, "Convergence confirmation".** Replace "in the same iteration" with:

> The confirmation is the *next* iteration's Run. It runs E1-01 at the next two seeds on the same code
> (`shasum -c` of the previous iteration's `code_sha1.txt` must pass). The gap/delta step makes no agent change in
> between.

The Run step can then execute it without needing a verdict.

**C0.3. The iteration-013 judges** grade `E1-01_s13` and `E1-01_s14` blind, per rubric, as usual.

**C0.4. Decision rule for the iteration-013 gap analyst:**

- **Converged.** E1-01_s13 MEETS (or E1-01_s14 MEETS) on the iteration-012 SHA. The ledger records convergence:
  seeds 0, 12 and 13/14; V1, V2 and V3 CORRECT on seeds 0 and 12; `test_no_hardcoding` green; the suite green. Open
  questions Q8, Q9, Q12, Q13 and Q14 go to Robin.
- **A seed fails at the arrangement.** The wrong edge class is chosen, or the "no feasible arrangement" path is
  taken. Implement C1 (below). After that, re-run the convergence seeds on the new SHA. Earlier MEETS seeds do not
  carry over across a code change (section 8).
- **A seed fails anywhere else** (ParseSpec, Contents, geometry). Do a normal gap analysis. The replay of that
  seed's `llm/` transcripts becomes the regression test (7.6).

### C1 (RC-1202, CONTINGENT: only under C0.4's second case): class-level joint vote in ConfirmArrangement

The goal is that a tie in the controller's signal is never broken by an arbitrary Python order. The edge vote is a
vote over **whole answers mapped to board-symmetry classes**, not a sum of per-item marginals.

**Files and functions** (`assembly.py` only):

- **`tally_joint(llm, prompt, schema, label, allowed, n=None) -> Tuple[Dict[str, Counter], List[dict]]`.**
  - It is `tally` that also returns the list of valid whole replies. A reply is valid when every key is inside its
    enum. Same sampling: sample 0 greedy, then T 0.7, `seed=i`.
  - `tally` keeps its signature and becomes a wrapper, so `ChooseStack`, `Contents` and the A/B pick are unchanged.
- **`ArrangeContents.candidates`.**
  - Store `joint` (the list of whole replies) in the returned dict.
  - `assignments` order is unchanged. Exploration order still follows the marginals, which keeps
    `arrange_rank_max` truncation the same.
- **`ArrangeContents.rank_candidates`.** After grouping, give each class `joint_votes` = the number of whole replies
  whose `lay.canonical_class(reply, symmetries)` equals the class key. Record it on each class and in `st.arrange`.
- **`ArrangeContents.decide(cands, classes, voted)`.**
  - The vote winner is the class with the most `joint_votes`.
  - **If no class has a joint vote** (every whole reply was infeasible or invalid, as in E1-01_s12), or the top
    count is tied between classes, there is no vote winner. Take the top-ranked class with
    `by = "llm:rank"`, plus a note: `arrange: the edge vote named no feasible class (joint replies: ...); ranked`.
  - **Otherwise** the logic is as today. A vote-winner class ranked at or above the top class gives
    `llm:vote+rank`. Below the top class, the A/B pick decides between the vote-winner class representative and
    the top class.
  - The `voted` argument becomes the class index, not a candidate index. Its representative is
    `classes[k]["rep"]`.
- **`st.arrange["joint_votes"]`.** This is `{str(class key): n}`, so a reader can see why the decision went the way
  it did.

**What it does not change.**

- Prescore filtering (7.11) is not touched.
- p_yes stays a ranking signal (7.6).
- No threshold is added.
- No literal edge, side or number is added.
- Board symmetry classes come from part data, as today.

**Unit tests** (`test_assembly.py`, fake LLMs only):

- **T1 `TestArrange.test_joint_vote_infeasible_answer_falls_back_to_rank`.**
  - Setup: a ScriptedLLM returns `{module_1: -X, connector_1: -X}` three times on E1-01, then the recorded
    `assy_confirm` p_yes from `iter_012/E1-01_s12/*/llm/`.
  - Expect `by == "llm:rank"`, the chosen class contains (−X,+X), and no `assy_arrange_pick` call is made. The fake
    raises if one is asked.
- **T2 `TestArrange.test_side_order_never_breaks_a_vote_tie`.**
  - Setup: the same as T1, but `SIDES` order is permuted for the test (monkeypatch `lay.SIDES` and the placer's
    `edges` order to `[-Y, +Y, -X, +X]`).
  - Expect the same chosen class and `by`. On the current code this test fails: the first tied candidate becomes
    (−Y,−X), and an A/B question is asked.
- **T3 `TestArrange.test_joint_vote_winner_accepted_when_top`.**
  - Setup: whole replies (−X,+X) ×2 and (−X,−X) ×1, with p_yes as recorded in target_s0.
  - Expect `llm:vote+rank` and `joint_votes` {class0: 2}.
- **T4 `TestArrange.test_joint_vote_tie_between_classes_ranks`.**
  - Setup: replies (−X,+X), (−X,−Y) and (−X,+Y), one each.
  - Expect no vote winner and `llm:rank`.
- **T5 `TestReplayIter012`.** Replay the recorded `llm/` transcripts of all 8 iteration-012 runs, plus iter_011
  V1_s0 and iter_008 V3_s8 (the A/B cases).
  - Each final `arrangement_confirmed.value` must be in the same symmetry class as delivered. The `by` label may
    change.
  - For the 8 iteration-012 runs, the feature graph must be unchanged: compare the `feature_graph.json` node set
    and the resolved params within 1e-9.
- **Existing tests.** Every existing `TestArrange` / replay test must pass unchanged. A test that asserts
  `by == "llm:vote+rank"` on a fixture whose joint answer is infeasible may change to `llm:rank`. The ledger then
  carries a one-line justification: the joint vote is now read per class.

**How it moves the verdicts.** On the 8 recorded runs, nothing changes (T5). On a new seed, the arrangement no longer
depends on `SIDES` order, and an extra sampled A/B question is asked only when the controller's own whole answers
favour a lower-ranked feasible class. That removes one source of seed-to-seed variation from the one stage where the
9B's answers vary.

### Deferred, not in this delta

**RC-1201.** This covers the PJ-320A body from the drawing (12.2 × 6.1 plus the 2.0 nose) and a generic
`rules.part_to_part` assembly gap enforced in `Placer` collisions and in a `layout_part_gap` check. It waits for
Robin's answer to Q12, because it would change the agent's references away from the judge's M-JACK. It must not land
before convergence is recorded.

## 4. Files and functions

| Change | Files | Code? |
|---|---|---|
| C0 | `loop/RUN.md` (section 1 iteration-013 note; section 3.1 confirmation wording), `iter_013/code_sha1.txt` (copy) | no |
| ARCHITECTURE | `loop/ARCHITECTURE.md` section 8: same-SHA rule (done by this analyst) | no |
| C1 (contingent) | `assembly.py`: `tally_joint`, `ArrangeContents.candidates` / `rank_candidates` / `decide`; `test_assembly.py` T1–T5 | yes, only under C0.4 case 2 |

## 5. Tests for this iteration (C0 only)

- `shasum -c benchmarks/enclosure/loop/iter_012/code_sha1.txt` → 9 × OK. This is the freeze proof.
- Full suite on the frozen tree, unchanged:
  `venv/bin/python -m unittest test_cascade test_cad_checks test_review_fixes test_cad_agent test_benchmark_runner test_parts test_feature_graph test_assembly test_assembly_checks test_no_hardcoding`.
  Expected: 385/385 OK, as in iteration 011, since no code changed. This is a re-confirmation, not new evidence. It
  may be skipped if the SHA check passes and the iteration-011 log is cited.
- No new unit tests, because no behaviour changes. C1 brings T1–T5 if it is triggered.

## 6. Expected effect on the verdict, and questions for Robin

**Expected.** E1-01_s13 and E1-01_s14 are MEETS / CORRECT, score 1.0, worst w3 +0.20, with the same geometry as
seeds 0 and 12.

- **Basis.** The arrangement is decided by the seed-invariant p_yes rank whenever the vote disagrees, and all three
  A/B picks on record went to rank 1. Every later stage is deterministic given the class. On this SHA, ParseSpec and Contents
  produced the same spec on seeds 0 and 12.
- **Residual risk.** The seed-dependent pieces are the ParseSpec / Contents samples and the A/B pick. C0.4 says what
  to do if one of them fails.

**Questions for Robin.** None of these blocks convergence.

- **Q9** (open since iteration 010). Should V1/V2's `grading_deltas` mouth windows be updated to the owner grid rule?
  For example, V1 mouth X in [2.54, 3.54] and V2 X in [2.46, 3.46], that is, first pin on grid column 0 ± 0.5. As
  written, V1 and V2 can never MEET; they can only be CORRECT.
- **Q8** (open). rubric.md section 6 pilot Ø2.0–2.2 against requirements L2.3.3 Ø1.6–1.8.
- **Q12** (new). Should references keep an assembly gap from each other? If so, what value, and should the
  catalogue/M-JACK take the drawing's 12.2 × 6.1 body plus the 2.0 nose? Today V2 puts the jacks touching the Pico
  PCB (0 gap). That passes as written, but a real part could interfere by about 0.2 mm.
- **Q13** (new, rubric). Should the cavity definition exclude exterior pockets reached through the port openings,
  and should the end-wall aperture recipe exclude blind boss pilots? Judges handled both by hand.
- **Q14** (new). Should the lid's M3 holes be counterbored so the heads sit flush? No L2 covers it today.

## 7. Convergence status after iteration 012

Not yet claimed:

- **E1-01:** MEETS on 2/3 seeds (0, 12; same SHA).
- **Variants:** CORRECT on V1 2/2, V2 2/2, V3 2/2 (V3 MEETS).
- **Guard and suite:** `test_no_hardcoding` green, suite green.

One E1-01 seed on the iteration-012 SHA (C0) is what remains.
