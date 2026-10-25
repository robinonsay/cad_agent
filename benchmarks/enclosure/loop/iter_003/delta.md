# Iteration 003: gap analysis and delta design

Author: gap analyst / delta designer, iteration 003. Code not edited.
Tooling: the claude-context MCP server failed to connect in this session ("configured MCP servers failed
to connect: claude-context"), so this analysis used targeted grep and reads of known paths only.

## 1. What the error signal says

| Run | rc | Status | Stage | Package |
|---|---|---|---|---|
| E1-01 `target_s0` (assembly, seed 0) | 1 | failed after 38 s | `arrange_contents` | none: G0 FAIL, "no renderable output" |

The judge had nothing to measure. This is the first assembly-mode run graded (RUN.md 3.2), so the defect is
"G0 FAIL, the run stopped at ArrangeContents". The transcripts in
`iter_003/target_s0/20261024-085515/llm/` show where it stopped.

The 9B controller answered every question the tree asked before ConfirmArrangement correctly, with one
exception (D2 below):

| Stage | 9B answer | Correct? |
|---|---|---|
| ParseSpec (`001-003_assy_spec`, 3/3 same) | board 70 x 50, keepout_above n15 = 12, **keepout_below n15 = 12**, clearance 0.5, oversize 1.5, walls 2-4, max 90 x 70 x 35 | yes, except keepout_below (should be n16 = 4 mm) |
| Contents (`004-006`) | perfboard 1, rpi_pico2 1 exposed, jack 2 exposed, cylinder 0 | yes |
| ChooseStack (`007-009`) | header_male_2p54 (2 of 3 votes) | yes |
| ArrangeContents edge vote (`010-012`) | module_1 -X, connector_1 +X (2 of 3); third sample -X/-X | **yes** (opposite short ends) |
| ConfirmArrangement (`013-024`) | p_yes for each of 12 feasible / pruned candidates, all < 0.5 | rejected the correct answer |

The p_yes values the controller gave (from the transcripts):

| Assignment (module_1 / connector_1) | p_yes |
|---|---|
| **+X / -X** (opposite short ends, the mirror of the vote) | **0.230** |
| **-X / +X** (opposite short ends, the vote winner) | **0.199** |
| -Y / -X | 0.117 |
| +Y / +X | 0.113 |
| +Y / -X | 0.110 |
| -X / -Y | 0.106 |
| +X / -Y | 0.103 |
| -Y / -Y | 0.096 |
| -X / +Y | 0.096 |
| -Y / +X, +X / +Y | 0.092 |
| +Y / +Y | 0.081 |
| -X/-X, +X/+X, -Y/+Y, +Y/-Y | pruned by Python (ports_do_not_fit, collides) |

The controller's absolute yes/no is badly calibrated: it says "no" to everything. But its **ranking** is
right and well separated: both "opposite short ends" assignments are the top two, at about twice the
score of every other candidate.

**Counterfactual (measured offline, no Ollama).** I replayed the run's own recorded answers (the spec
with the n15 duplicate, the same contents, stack and edge votes) through `cad_agent.main --mode assembly`
with ConfirmArrangement forced to accept the vote winner. The script is at
`/private/tmp/claude-501/-Users-robinonsay-python-llm-bt/7d706733-5c1d-44fb-a74b-bc29203e1df6/scratchpad/replay/replay.py`; it uses only `test_assembly` helpers and production rules (`fn` 64). The
result: **rc 0, verified**. The agent's own checks all pass, and OpenSCAD compiled base.stl and lid.stl,
**82.25 x 60.95 x 32.40 mm**. With the correct keepout_below (n16 = 4 mm), the iteration-002 offline run
measured 82.3 x 61.0 x 24.4 mm. So, apart from these two defects, the whole pipeline after ArrangeContents
already works on this controller's real answers.

## 2. Defects traced to root causes in the agent

### D1 (blocker, G0): no package. ConfirmArrangement vetoed the correct, voted, feasible arrangement

- **Root cause RC-301: wrong control logic. A ranking signal is used as an absolute gate.**
  `assembly.py` `ArrangeContents.update` (around lines 593-603) accepts an assignment only if
  `llm.p_yes(...) >= 0.5`. Otherwise it tries the next candidate, and when the list runs out it fails.
  `cad_agent.OllamaAgent.p_yes`'s own docstring (`cad_agent.py:644-650`) says p_yes is "well suited to
  RANKING alternatives; for an accept/reject decision use yes_score". A 9B model's single-token P(yes)
  sits well below 0.5 for every candidate here (0.08-0.23). As a veto, the gate is just noise. It
  rejected the very answer the same controller had voted for 2 of 3 times. In control terms, an
  uncalibrated sensor was compared with a fixed set-point, and the loop had no way out other than a
  failure.
- **RC-302: the controller's two signals are never combined.** The edge vote, the controller's
  answer, only orders the candidates. After that, each p_yes is judged alone. The two independent
  signals agree here (the vote winner's class is the p_yes argmax), and the code ignores that.
- **RC-303: symmetry-equivalent candidates are treated as competitors.** The perfboard's outline and
  its corner-hole pattern are invariant under a 180° rotation about the board centre. Under that
  rotation, -X/+X and +X/-X are the same physical product, rotated. Python asked about both, and they
  "competed" (0.199 vs 0.230). With an absolute threshold this cost nothing extra, but any relative rule
  must not split the vote between equivalent layouts.
- **RC-304 (error-signal quality): the failure message drops the evidence.**
  `self.fail(... " | ".join(tried[-4:]))` keeps only the last 4 of 12 candidates. The correct
  candidate's rejection (p_yes 0.199) appears only in the transcripts, not in `design.json`
  `assembly.notes`, so the judge and the next analyst cannot see it from the record.
- Not the cause: the prompt words, the edge enum, the placement math and the pruning. The pruned
  assignments really are infeasible: three plugs on one 50 mm end need 10.1 mm spacing and get 7.25 mm,
  and a jack on the Pico's side collides with it.

### D2 (latent, will show in the next package): keepout_below = 12 mm taken from the keepout_above number

Not in this judge report, because there was no package. The counterfactual shows it would ship: standoffs
about 12 mm tall and the enclosure 32.4 mm high instead of about 24.4 mm (still within the 35 mm limit, so
no agent check fails).

- **Root cause RC-305: a missing check on the controller's action.** `ParseSpec.violations`
  (`assembly.py` around lines 312-329) rejects a number id used twice only among slots with **no
  default** (`board_width`, `board_depth`). `keepout_above` and `keepout_below` have rules defaults, so
  the 9B answer `n15` for both passed without a re-ask. Each extracted occurrence has its own id
  (`extract_numbers`), and every spec slot names a different physical quantity. So "one occurrence fills
  two slots" is a generic inconsistency that Python can sense, and it should be fed back to the LLM.
- **RC-306: the fallback after a failed re-ask throws away good information.** When a violation
  persists, the code sets **every** named slot to None. For a duplicate, that would replace the correct
  `keepout_above = 12` with the generic rules default as well. The contested id belongs to exactly one of
  the slots, so the loop should find out which one, not drop both.

### Grouping

| Root cause | Defects | Class | ARCHITECTURE.md |
|---|---|---|---|
| RC-301, RC-302, RC-303 | D1 | wrong control logic / representation of choices | 4.2, 7.4 (ConfirmArrangement), 7.5; middle loop (4.1) |
| RC-304 | D1 (observability) | error-signal quality | 4.1 "each loop ends with a typed report" |
| RC-305, RC-306 | D2 | missing check on the controller's action | M6 (ParseSpec gates), 4.5 provenance |

Ledger check (no repeated failed idea, no oscillation): iteration 002 introduced ConfirmArrangement as
"p_yes, on no try the next feasible assignment" (7.4 and 7.5). This is its first contact with the real
controller, and the absolute threshold is the part that failed. The change below keeps
ConfirmArrangement (Robin's direction: the LLM decides the discrete choice, and Python generates and
pre-scores the alternatives). It changes only how the controller's output is read: as a ranking, plus
the vote. That replaces the threshold that just failed. It is not a return to an idea tried earlier.

## 3. Delta design (one pass, four changes)

All four are generic. No number, edge or part id specific to E1-01 enters agent logic. New tunables go in
`design_rules.json` with a source (the hard-coding guard does not scan JSON, so the reviewer must read
them by hand).

### C1. ConfirmArrangement becomes a ranking decision (closes RC-301, RC-302; D1)

**Files and functions:** `assembly.py`: `ArrangeContents.update` and `ArrangeContents.assignments`, plus
new methods `ArrangeContents.rank_candidates` and `ArrangeContents.decide`.

**Control logic (replaces `if p >= 0.5`):**

1. As today, enumerate assignments in vote order and prune the infeasible ones through
   `placer.place`, with the notes kept. Keep at most `rules.arrange_rank_max` feasible candidates
   (new rule, default 16, generic: the number of candidates the controller ranks). If more remain, they
   are cut in vote order, the cut is reported in `design.json` (`assembly.arrange.truncated: n`), and it is
   never silent.
2. Group the feasible candidates into symmetry classes (C2). Each class's representative is the member
   with the most votes, ties broken by fewest differences from the vote winner, then by the existing
   side order. Ask `p_yes` **once per class representative**, batched through
   `getattr(llm, "p_yes_many", None)` (the cascade pattern at `cascade.py:878`). Label: `assy_confirm`.
   Each class's score is its representative's p_yes.
3. Decision (no absolute threshold):
   - **Agreement:** if the vote winner's class has the highest score, accept the vote winner.
     `by = "llm:vote+rank"`.
   - **Disagreement:** otherwise ask one comparative, voted multiple-choice question
     (`assy_arrange_pick`, schema enum `["A", "B"]`, via `tally`). A is the vote winner's words and B is
     the top class representative's words, both from `lay.describe`. "Which arrangement matches the
     request?" The majority wins, and a tie or no valid answer goes to the higher-ranked one.
     `by = "llm:pick"`. Why comparative: a 9B model separates A from B more reliably than it answers an
     absolute yes/no, as the p_yes table above shows.
   - If there is no vote winner (every edge vote invalid), accept the top class. `by = "llm:rank"`.
4. Record everything in `st.history` (each candidate: assignment, class id, words, p_yes, chosen) and in
   `st.choices["arrangement_confirmed"] = {value, by, p_yes, rank, margin_to_next}`. If the accepted
   score is below 0.5, add one line to `assumptions`: "arrangement accepted by rank: the controller's
   absolute confidence was low (p_yes x.xx; next class y.yy)". The judge can see the low confidence, and
   it does not block the build.
5. Fail only when **no feasible assignment exists** (a typed `LayoutError` summary, see C3). A rejection
   by the controller is no longer a failure mode, because a ranking always has a top. The real veto on
   a wrong arrangement is downstream: the agent's own checks (aperture counts per wall, insertable), and
   then the judges.

**Data model:** none beyond the history and choices fields. Update the tree diagram line at
`assembly.py:13` to "ConfirmArrangement: LLM ranks the feasible classes (p_yes) + vote; comparative pick
on disagreement".

### C2. Board symmetry classes from part data (closes RC-303; D1)

**Files and functions:** `layout.py`: new `board_symmetries(board_inst, tol) -> List[Dict[str, str]]`
and `canonical_class(assign, symmetries) -> Tuple`. The new methods in `assembly.py` call them.

- Candidate symmetries are generated, never listed per target: the identity and the in-plane rotation
  by 180° about the board's plan centre (edge map -X↔+X, -Y↔+Y). For square boards, also add the
  rotations by 90° and 270°. Mirrors are excluded, because parts are chiral and a mirrored layout is not
  the same product.
- A symmetry is kept only if it maps the board's outline (`size_of`) and every datum in its `HOLE`
  axis_list (and its `grid` origin, when the part has one, modulo the pitch) onto itself within
  `rules.measure_tol`. All values come from `board_inst`, so this is part data, not code.
- `canonical_class(assign)` maps an edge assignment to the lexicographically smallest image of it
  under the kept symmetries.
- If the grid check fails (for example, a grid registered off-centre), only the identity is kept, and
  C1 still works with singleton classes.

**Why this is not hard-coding:** the function tests the invariance on whatever board the catalogue
instantiates. A board with an asymmetric hole pattern gets singleton classes.

### C3. Failure summary keeps every candidate (closes RC-304)

`ArrangeContents.update`: on failure, `self.fail` lists every candidate with its outcome (pruned kind
and detail, or score), sorted best first, instead of `tried[-4:]`. Also add `assembly.arrange` to
`AssemblyState.summary()`: `{candidates: [...], classes: n, truncated: n, decision: by}`, so design.json
carries the whole ranking.

### C4. ParseSpec: one occurrence fills one slot, with a contested-id resolution (closes RC-305, RC-306; D2)

**Files and functions:** `assembly.py`: `ParseSpec.violations`, `ParseSpec.update`, and a new
`ParseSpec.resolve_shared`.

- `violations`: the duplicate test covers **all** slots. Any number id that the answer uses for two or
  more slots is a violation, and the message names the slots and the quote:
  "keepout_above and keepout_below both use n15 (12 mm, '...12 mm above the board's top surface or 4 mm
  below...'); each number in the text states one quantity". The existing no-default duplicate message
  stays as a special case of this one.
- `update`: the existing single re-ask runs. If a shared id remains after it, call
  `resolve_shared(id, slots)`:
  1. Ask one enum question, voted through `tally` (label `assy_spec_owner`): "Number `<id>` = `<value>`
     (`<quote>`) states which one quantity?", with the enum = the slots that share it. The majority owner
     keeps the id.
  2. Re-ask only the losing slots (label `assy_spec_slot`), with that id **removed from their enum**.
     This constrains the action space: the controller can no longer repeat the contested answer. The
     answer goes through the remaining violations as usual. A still-invalid slot falls back to its
     rules default, flagged as today.
- This replaces "set every named slot to None" for the duplicate case only. The other violations
  (wall band, ≤ 0, missing no-default slot) keep today's behaviour.

## 4. Unit tests (fake LLMs, no Ollama)

New helper in `test_assembly.py`: `RankedLLM(FakeLLM)`. Its `p_yes(prompt, label)` returns a float from a
table keyed by substrings of Python's arrangement words (for example `"(usb) faces the short (50 mm) end at
-X"` with `"face the short (50 mm) end at +X"` → 0.199), with a default of 0.09. The edge votes are
scripted as a list.

| Test | Proves |
|---|---|
| `TestArrange.test_iter003_replay_accepts_the_voted_arrangement_by_rank` | **Regression of this iteration's failure.** Edge votes [-X/+X, -X/+X, -X/-X] and the recorded iter_003 p_yes table (every value < 0.5). ArrangeContents succeeds. The choices are `edge[module_1] = -X`, `edge[connector_1] = +X`, and `arrangement_confirmed.by == "llm:vote+rank"`. One "low absolute confidence" assumption is present. No `assy_arrange_pick` call. |
| `TestArrange.test_disagreement_asks_one_comparative_pick` | The votes favour assignment P, and p_yes ranks a different, non-equivalent class Q highest. Exactly one `assy_arrange_pick` vote is asked, and its scripted answer ("B" in one test, "A" in a subTest) decides. A tie goes to the higher-ranked class. |
| `TestArrange.test_symmetric_candidates_are_asked_once` | For E1-01, the number of `assy_confirm` calls equals the number of feasible symmetry classes (not 12), and -X/+X and +X/-X share a class. |
| `TestArrange.test_no_feasible_arrangement_lists_every_candidate` | A shrunk board (the existing V2 fixture pattern) where no assignment fits. Typed failure, and the note lists every candidate's prune reason, not 4. |
| `TestArrange.test_rejected_arrangement_tries_the_next_feasible_one` → **changed**, renamed `test_low_confidence_vote_winner_is_not_vetoed` | Ledger justification: behaviour intentionally changed. An uncalibrated p_yes no longer vetoes a feasible voted arrangement (RC-301). The test keeps its other assertions: the all-on-one-end assignment is pruned with a `ports_do_not_fit` note before any question, and the used edges equal the decided assignment. |
| `test_layout.TestSymmetry` (or a new class in `test_assembly.py`) | The perfboard instantiated at the E1-01 request size and at the V1 size (read from the request texts, as `request_numbers` does) has {identity, rot180} with the edge map -X↔+X, -Y↔+Y. A board whose `HOLE` list has one hole moved by 1 mm (fixture part.json in a temp catalogue) has only the identity. A square fixture board gets 4 rotations. `canonical_class` is idempotent and invariant over a class. No target number appears in agent code (`test_no_hardcoding` stays green). |
| `TestParseSpec.test_shared_number_id_is_reasked` | First answer: keepout_above = keepout_below = the id of "12" in the keep-out L1. The re-ask (`assy_spec_reask`) names both slots and the quote. The scripted re-ask gives the "4" id. Result: spec keepout_below = 4, with provenance quoting "4 mm below". |
| `TestParseSpec.test_persistent_shared_id_is_resolved_by_owner_question` | The re-ask repeats the duplicate. `assy_spec_owner` picks keepout_above. `assy_spec_slot` is asked for keepout_below with that id absent from its enum (the test asserts that on the schema it receives) and answers "4". Result: 12 / 4. With an owner question that has no valid answer, both slots fall back as today, flagged. |
| `TestEndToEnd` (unchanged expectations) + a new `test_replay_iter003_answers_end_to_end` | `run_offline` with the recorded spec answer (n15 twice; the scripted re-ask returns n16), the recorded contents, stack and edge votes, and the recorded p_yes table. rc 0, verified, aperture counts -X 1 / +X 2 / ±Y 0, outside Z within max_z, and the standoff height above the floor equal to keepout_below 4 (not 12). Use `fn = 24` for speed. |

The full suite must stay green: `test_cascade test_cad_checks test_review_fixes test_cad_agent
test_benchmark_runner test_parts test_feature_graph test_assembly test_assembly_checks test_no_hardcoding`
(plus `test_layout` if it is added; then append it to RUN.md section 2). Default and cascade modes are not
touched: `cad_agent.py` and `cascade.py` are unchanged by this delta.

## 5. Expected effect on the judges' verdict

- **G0 goes from FAIL to PASS.** On the same seed and the same controller answers, the counterfactual
  replay already verifies (rc 0) and writes base.stl, lid.stl, layout.json, self_report.json, views and
  model.3mf. C1 makes the agent take that path.
- With C4, the package's height drops from 32.4 mm to about 24.4 mm, and the standoffs drop from about
  12 mm to about 4 mm. This removes a defect a judge would otherwise flag in the L1.4 and L1.10
  context and in the provenance (keepout_below quoting the "12 mm above" text).
- For the first time, the judges can grade G1-G5 and the L1 table. Iteration 002's notes list what the
  agent does not yet check (printability, ray-cast wall thickness, V-AP-OTHER, install sweep, screwdriver
  access, and the corner pilasters standing 2.6 mm proud). Those become iteration 004's error signal.
  They are deliberately not in this delta: they do not block a package, and only a judged package can
  show which of them matters most.
- Variants: V1 (two ports on one edge) runs through the same ranking. V2 and V3 are not run until the loop
  asks for them.

## 6. Architecture changes

ARCHITECTURE.md gains section 7.6 "Refinements decided in iteration 003". It covers: p_yes from the local
controller is a ranking signal and is never compared with a fixed threshold to veto a feasible choice;
ConfirmArrangement = vote + rank over symmetry classes + a comparative pick on disagreement; board
symmetry from part data; one occurrence fills one spec slot, with contested-id resolution; and a real-run
failure becomes an offline replay test built from its transcripts. Sections 7.4 and 7.5's ConfirmArrangement
bullets are superseded by 7.6 (they stay as history).

## 7. Notes for the implementer

- Keep `p_yes` calls batched (`p_yes_many` when present), because a judge panel loads each model once.
- `design_rules.json`: add `arrange_rank_max` (16, source: "generic cap on controller-ranked layout
  candidates; reported when it truncates"). It is the only new value.
- RUN.md: no CLI change. Update the "Expected now" paragraph in section 4 (the ConfirmArrangement question
  count now equals the number of feasible symmetry classes, plus at most one pick vote).
- Do not change `OllamaAgent.p_yes` or the cascade's thresholds. This delta changes only how assembly
  mode reads the signal.
