# Iteration 007: gap analysis and delta design

Tooling: the claude-context MCP server failed to connect in this session ("configured MCP servers failed to
connect: claude-context"). I read known paths and used targeted grep only.

## 0. What the run tells us

Iteration 007 is the first iteration that ran the variants (process fix from 006). Five runs, all rc 3
(`unsatisfied`), about 70 s each:

| Run | Own checks | Contents (part, exposed) | Stack (votes) | Judged |
|---|---|---|---|---|
| target_s0 (E1-01, seed 0) | 51/52, grid only | pico **yes** (3/3), jacks yes | male (2:1) | yes, both judges: DNM / CORRECT 133/134 |
| E1-01_s5 | 51/52, grid only | pico **yes (2:1)**, jacks yes | male (2:1) | no |
| V1_s5 | 43/46: grid, apertures_-X, apertures_+Y | pico **no (0:3)**, jack yes | **female (2:1)** | no |
| V2_s5 | 50/52: grid, apertures_-X | pico **no (0:3)**, jacks yes | **female (2:1)** | no |
| V3_s5 | 45/46, grid only | pico **no (0:3)**, jack yes | female (3:0), correct | no |

The judges graded only target_s0. Both found exactly what iteration 006 predicted: one weight-1 failure,
L3.1.6.1. It is infeasible as written (Pico `flush_to_edge`, jacks `pin_pattern`, best 0.54 mm), so it
stays a question for Robin. Their only observation that concerns the agent is O3: the verification matrix
marks all 12 L1s "FAIL n/a, no check covers this requirement".

The variant runs are the real news. They come from the agent's own outputs; no judge has read them yet. I
re-measured V1 myself with manifold3d. **None of V1, V2 or V3 has a USB opening.** Each request says
"the Pico's micro-USB port ... exposed", and each L1.5 says "a micro-USB cable shall plug fully into
the Pico". Against requirements.md, every variant fails L1.5 (weight 3), so each is WRONG-class, and
convergence (section 8: V1–V3 at least CORRECT) is blocked. E1-01 itself only just got the Pico's USB
right on seed 5 (2:1 vote), so the 3-seed MEETS criterion is fragile too.

Even so, the agent rated V3 exactly like E1-01: everything passes except the grid. Its own checks are
derived from the same wrong contents decision, so they cannot see the missing opening. The design is
open-loop on Contents.

## 1. Defects → root causes

| Id | Defect (source) | Root cause in the agent | Class |
|---|---|---|---|
| D1 | E1-01 L3.1.6.1, pins off grid (both judges, w1) | None. Requirement/catalogue conflict, already typed (`flush_to_edge`, `pin_pattern`) | Robin, question 2/3 (unchanged) |
| D2 | O3: matrix says every L1 "no check covers" (both judges) | **RC-701.** Every rule-derived check has `l1_id = "rules"` (`assembly_checks.L1_RULES`, `Plan.checks`). No link from a check to the L1 its numbers or parts came from, although ParseSpec already records that provenance (`spec_provenance`, e.g. `board_clearance ← L1.2`). | missing traceability (part of M10) |
| D3 | V1, V2, V3: Pico not exposed, so no USB opening (run outputs, L1.5 w3) | **RC-702.** `Contents.update` asks one joint question over all candidates. Exposure is a bare yes/no per part, worded with ids (`usb (takes a plug_microusb_b)`), and nothing checks it independently. The 9B answered "no" 3/3 on all variants. The rule-derived checks are generated from that same answer, so the error signal is blind to it (V3: 45/46, "grid only"). The L1 texts name the mating plug by a catalogue alias ("micro-USB cable", alias of `plug_microusb_b`), and no Python sensor reads that. | missing error signal + open-loop controller decision |
| D4 | V1, V2: female sockets chosen with no word in the text for it (run outputs; requirements A3 default is male headers) | **RC-703.** `ChooseStack` asks the LLM to pick among all `stack_options` even when the text gives no evidence for any of them. The 9B guesses (2:1 female). The same question is 2:1 on E1-01, so it is noise. | discrete choice without an evidence gate |
| D5 | V1 `apertures_-X` 2 through (expected 1), `apertures_+Y` 1 through (expected 0); V2 `apertures_-X` 1 through (expected 0) | **RC-704** (sensor bug, my measurement). The wall slab's Z faces are exactly coplanar with the base bottom (`cav.z0 - floor`) and the lid top (`split + lid.z`) (`assembly.build_plan`, slab loop). `slab − bodies` then keeps a zero-thickness skin along the lid top. The skin joins the two corner pockets of a wall into one region and touches both face planes. `assembly_checks._reaches` accepts any slice volume `> 0.0`, so the joined pocket reads as a `through` opening. Re-measured on V1 base+lid: with the slab as built, the +X wall gives 1 region spanning y −3.5…63.5. With the Z faces inset by 0.01 it gives 2 separate corner pockets (x 81.41…83.49), which are blind. The bug shows when the split lands on an exactly representable value (15.0 in V1/V2, sockets); E1-01's 14.2 hid it. Iteration 006 removed the Z inset (7.9 "only the two face planes are inset"). | sensor robustness regression |

D3 and D5 never coincide by construction, but they compound: in V1 the false `through` failures were the
*only* aperture signal, and they pointed at the wrong walls.

Grouping: D3 and D4 share one principle. A discrete content decision that changes the geometry must be
backed by evidence in the text that Python can verify, the way ParseSpec's numbers already are. D2 and
D3 share the trace: if Python knows which L1 names which part, it can both fill the matrix and sense
an L1 whose part the design never serves.

Ledger check (no repeated idea): no earlier iteration touched Contents, ChooseStack or L1 traceability.
Iteration 003 made ArrangeContents vote+rank; that pattern is reused here, not repeated. The Z inset
was dropped in 006 for a different reason (corner pockets must stay visible). This delta restores it
without losing that: an inset of `measure_tol` keeps the pockets (verified above).

## 2. Delta (one pass; no cad_agent.py / cascade.py / cad_checks.py change)

### C1 (RC-704): wall slab inset on all six faces; a face is "reached" only by a real cross-section

- `assembly.build_plan`, slab loop:
  - Z becomes `[z_lo + eps, z_hi - eps]`.
  - The tangent becomes `[t_lo + eps, t_hi - eps]`.
  - `eps = rules.measure_tol`, as for the two wall faces.
  - Update the comment and 7.9's slab bullet (ARCHITECTURE 7.10 says why).
- `assembly_checks._reaches`: the face-slice intersection must have a real cross-section. Accept only
  when its bbox extent along both in-plane axes is ≥ `tol.measure`. Today the test is volume `> 0.0`.
  A skin of float-noise thickness then never makes a region `through`.
- Tests (no LLM):
  - `test_assembly_checks.TestApertures.test_coplanar_cap_does_not_join_pockets`: a shell base plus a
    separate lid plate whose top is at an exactly representable Z (15.0), with a blind pilot in two
    corners of the same wall. With the slab Z faces on the body faces, each wall must give 0 through and
    2 blind. Run the same case with the old zero threshold to show the test discriminates.
  - `test_assembly.TestEndToEnd.test_v1_socket_stack_apertures` (offline, scripted): V1 with
    `stack = header_female_2p54`, which gives split 15.0. Every wall's through count equals its port
    cuts, and every blind region names exactly one corner.
  - The existing `test_aperture_regions_follow_the_literal_rubric_slab` must stay green. Its literal
    rubric helper is judge-side, so it keeps the uninset Z.
  - If that helper itself counts the joined skin on the V1 socket case, record that as a rubric
    question for Robin, not as an agent change.
- Verdict effect: V1/V2 self-reports stop claiming false openings, so L1.12-type agreement holds on the
  variants. E1-01 is unchanged.

### C2 (RC-703): evidence-gated stack choice

- New helper `assembly.text_evidence(texts, aliases, numbers=()) -> List[dict]`.
  - Input: the request plus the L1 texts as `(source, text)`.
  - It returns the occurrences, with source and quote, where the `parts.tokens` of some alias are a
    contiguous run in a sentence's tokens, or where one of `numbers` occurs among `st.numbers` (within
    `rules.measure_tol`).
  - It is generic and data-driven: aliases come from part.json `names`.
- `ChooseStack.update`:
  1. For each option, the evidence is `text_evidence(texts, option.names, [stack height])`. The height
     is the `STACK_TOP − STACK_BOTTOM` it already computes.
  2. The enum offered to the LLM is the options *with* evidence.
     - If exactly one option has evidence, choose it with no question (`rule:text_evidence`, quote in
       the choice record).
     - If two or more do, ask as today but only among them.
     - If none does, take `stack_options[0]` (`rule:catalogue_default`) and append an assumption
       ("the text names no mounting; catalogue default used"). That is the catalogue's own order, so it
       is data, not hard-coding. Add a `notes` line to `rpi_pico2/part.json` `mount` saying the first
       option is the default.
  3. Every choice record gets `evidence: [...]`.
- Expected: V3 gets "female header" plus "8.5 mm" → female, with no LLM call. E1-01, V1 and V2 have no
  stack words → male by default. That matches A3 and removes the 2:1 coin flip from E1-01's seeds.
- Tests (fake LLM):
  - `TestContents.test_stack_evidence_gate`, one per request:
    - E1-01, V1, V2: male, no `assy_stack` call. Use a `ScriptedLLM({})` that raises on any stack call,
      or assert that the label is absent from `llm.calls`.
    - V3: female by `rule:text_evidence`, with the quote.
    - A synthetic request naming both "male header" and "8.5 mm sockets" asks the LLM among exactly
      those two.
  - Change `test_v3_socket_stack_and_request_sized_part` (behaviour changed intentionally: the stack is
    now a rule decision from text evidence). It must assert `by == "rule:text_evidence"`, not the
    scripted answer.

### C3 (RC-702): exposure coverage, an L1/request text that names a mating plug requires that connector

This is the outer-loop signal of 4.1 ("an L1 has no check"), applied before Arrange so that no rebuild
loop is needed.

- New function `assembly.named_parts(st) -> Dict[str, List[dict]]`. For every catalogue part, it returns
  the `text_evidence` hits of its `names` across the request and every L1 (source id, quote).
- Contents: improve the wording, keep the joint question. `part_words` names each connector with the
  mating plug's first human name, not its id: `usb connector (takes a micro-usb plug)`. Data only.
- New stage inside `Contents.update`, after the items are built (or a small `ExposureCoverage` step right
  after Contents in `build_assembly_tree`):
  1. For each content item with a connector whose `mates` part has hits in `named_parts`, and whose
     `exposed` is False, raise a *coverage violation*: `(item, connector, plug id, [source:quote])`.
  2. For each violation, ask one focused question with label `assy_expose`, voted with `tally`. Python
     words it: `L1.5 says: "<quote>". Must the <plug human name> plug into the <part name>'s <connector>
     from outside the closed enclosure? yes/no`.
     - Majority yes: `exposed = True` (`by = "llm:coverage"`, quote recorded).
     - Majority no: keep it unexposed. Record `assembly.conflicts` kind `coverage` with the quote, and
       a matching failing check (next bullet), so the self-verdict cannot say "grid only".
  3. A coverage violation that the LLM resolves leaves a note. A text naming a plug whose mating part is
     not in the contents at all becomes a note, not a failure.
- New rule-derived check `text_coverage`, type `coverage`, added in `build_plan` and computed from
  `st.contents` plus `named_parts`. It fails when a named plug's mating connector has no
  `clear_of_<conn>_plug` check. `margin = −(uncovered count)`. Evidence lists source ids and quotes.
  `l1_id` is the naming L1 (see C4). It runs on graph data only (`value` check family, no mesh).
- Expected on the iteration 007 transcripts:
  - V1–V3 L1.5 contain "micro-USB cable", an alias of `plug_microusb_b`, which mates `rpi_pico2.usb`.
  - The Pico was "no", so the violation fires and the focused question is asked.
  - If the 9B still says no, the agent reports `coverage` as a failing check and a conflict. That is
    an honest WRONG self-verdict, not a hidden one.
  - The jacks' "3.5 mm plug" hits are already exposed, so no question is asked.
- Tests (fake LLM):
  - `TestReplayIter007` (7.6 rule: every real-run failure becomes a replay test). Script V1's recorded
    answers from `iter_007/V1_s5/*/llm/` (spec, contents with pico "no", stack, edge, confirm), plus
    `assy_expose: yes`. Run to Verify offline. Assert:
    - the Pico is exposed (`by == "llm:coverage"`);
    - there is one USB `port_cut` on the same wall as the jack cut;
    - `apertures_-X` expects 2 and passes;
    - `text_coverage` passes.
    The same for V3 (USB opening on the wall opposite the jack) and V2.
  - `TestContents.test_coverage_no_is_reported`: same V1 replay with `assy_expose: no`. `text_coverage`
    fails, `assembly.conflicts` has kind `coverage` quoting L1.5, and the outcome is `unsatisfied`.
  - `TestContents.test_no_question_without_named_plug`: a synthetic request and L1s that never name a
    micro-USB plug or cable, with the Pico "no". No `assy_expose` call, and `text_coverage` passes
    (vacuous: nothing named).
  - `test_no_hardcoding` stays green: aliases come only from part.json.

### C4 (RC-701): deterministic L1 trace for the rule-derived checks

- `assembly_checks.Plan.add` takes an optional `slots=(...)`, the spec slot names whose values the check
  uses, and `parts=(...)`, the catalogue ids it concerns (for clear_of / inside / plug checks these are
  already in `Plan.parts` / `labels`).
- New function `assembly.trace_links(st, plan) -> Dict[check_id, List[l1_id]]`. A check links to:
  - every L1 that is the provenance source of one of its slots (`spec_provenance` already holds
    `L1.k:"quote"`);
  - every L1 whose `named_parts` include one of its parts.
- `checks.json` rows get a `links` list. This is added in WritePackage on the dicts, so `cc.Check` is
  unchanged.
- WritePackage builds the matrix with a new `assembly.trace_matrix(l1, checks, results, links)`: one row
  per L1 over all its linked checks.
  - An L1 with no linked check is shown as `UNLINKED` (note: "translation to checks is milestone M10"),
    not `FAIL n/a`.
  - The `rules` row keeps every unlinked check.
  - `cc.verification_matrix` is not touched (cascade uses it).
- Slots to pass, all already used by those checks:
  - board/contents/keep-out checks: `board_clearance`, `keepout_above`, `keepout_below`;
  - aperture_oversize: `opening_oversize_max`;
  - bbox: `max_x/y/z`;
  - plug clear_of: plug part ids.
- Tests:
  - `TestEndToEnd.test_trace_links` (E1-01 scripted):
    - `inside_board`/`clear_board` link to the L1 that states 0.5 mm, found in the test by searching
      the L1 texts for the clearance number, never a literal id;
    - plug checks link to the L1s naming the plugs;
    - `bbox` links to the size L1;
    - no L1 is shown `FAIL n/a`;
    - the unlinked L1s are listed as `UNLINKED`.
  - Expected for E1-01: L1.1, L1.2, L1.4, L1.5, L1.6 and L1.10 linked. L1.3, L1.7, L1.8, L1.9, L1.11 and
    L1.12 are UNLINKED until M10. L1.8 stays unlinked because no check consumes `wall_min`/`wall_max` yet:
    there is no `min_wall` check, which is itself a gap for M5/M10.
- Verdict effect: clears both judges' O3. The matrix becomes a real self-assessment that M10 can extend.

### Not in this delta (and why)

- **M10 LLM translation templates and mutants:** too large to do alongside C1–C4. C4 gives M10 its data
  structure (links). C3 is the first L1-driven correction.
- **M11 middle loop on aperture failures:** after C1 the false aperture signals are gone, and C3 removes
  the true cause of the missing openings. The middle loop is the next lever if the real controller still
  misplaces ports.
- **D1 grid:** Robin's decision (questions 2 and 3 carried over). No agent change.
- **L3.12.1.1 (20–200 mm per axis):** a judge-side number. Unchanged; still question 1.
- **V2's jacks on −Y vs the grading note's +Y:** the request says "one long edge". By board symmetry
  this is a judge-side convention. If the judges grade it as a defect, that is a rubric question for
  Robin.

## 3. Expected outcome after the delta (offline, scripted controller)

- E1-01:
  - geometry is byte-identical to iteration 007 (male by default, Pico exposed);
  - 52 + 1 checks (`text_coverage` passes);
  - only `grid_conformance` fails;
  - the matrix links 6 of 12 L1s and shows 6 UNLINKED;
  - predicted verdict: DNM / CORRECT 133/134 (D1 unchanged), but more seed-robust (stack and exposure
    no longer coin flips).
- V1 (replay with coverage yes): USB and jack on the −X wall, 2 through, 0 false regions, male headers.
  Predicted CORRECT-class, failing only the jack-grid L3 (w1).
- V2: USB on −X plus three jacks on a long side, male headers. Predicted CORRECT-class.
- V3: USB high on −X, jack on +X, sockets by evidence. Predicted CORRECT-class.
- Test count: about 334 + 9 new tests; one changed test (justified above).

## 4. Run-step instructions for iteration 008

- SEED = 8. Run all four (`run_one E1-01; run_one V1; run_one V2; run_one V3`).
- **The judges must grade V1–V3 this time.** Iteration 007 ran them but judged only target_s0.
  Convergence needs variant verdicts.

## 5. Questions for Robin (carried over)

1. L3.12.1.1: units sanity on the largest axis, or a deep-cap lid?
2. Perfboard grid registration (photo suggests a centred 24 × 18 array). Or should the USB band follow
   the grid?
3. PJ-320A: exclude the jacks from L2.1.6, or use a jack with a 0.1 in footprint?
4. L3.11.1.1: exclude V-SEAT from V-INSTALL?
5. (new) The rubric 3.4 slab is literally "base bottom to lid top". With exactly representable Z values
   (V1/V2 sockets) a literal implementation can count a zero-thickness skin as an opening. Should the
   rubric inset the slab's Z faces by ε as well?
