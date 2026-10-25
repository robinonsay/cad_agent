# Iteration 011: gap analysis and delta design

Inputs: four runs, all rc 0 (`verified`):

- `target_s0`: E1-01, seed 0.
- `V1_s0`, `V2_s0`, `V3_s0`: the variants, also run at seed 0. RUN.md asked for SEED = 11 and a fifth row
  (E1-01 at seed 11); neither happened. This is a Run-step process slip, not an agent gap; see section 6.

Verdicts:

| Run | Verdict (both judges) | Class | Score | Worst w3 margin |
|---|---|---|---|---|
| target_s0 (E1-01) | **MEETS** | CORRECT | 1.0 | +0.20 |
| V1_s0 | DNM | MINOR | 0.912 | −3.0 (L3.3.1.3) |
| V2_s0 | DNM | MINOR | 0.912 | −2.92 (L3.3.1.3) |
| V3_s0 | DNM | MINOR | 0.926 | −3.0 / −2.9 (L3.3.1.3) |

E1-01 met the requirements for the first time (1 of the 3 seeds that convergence needs). All three variants fail
for one root cause in the agent's catalogue representation. V1 and V2 also have a USB-mouth defect that comes from
a conflict in the test data.

Tooling: the claude-context MCP server failed to connect this session (ToolSearch: "configured MCP servers failed to
connect ... claude-context"). I read files at known paths and ran targeted grep only. I did not edit any code.

## 1. What happened

The controller (9B) made no wrong choice in any run. Edges, stacks and prescore all came out as the scripted
controller would choose them, and every package verified against the agent's own checks. All the variant defects
are about what the agent *believes the board is*:

- **V1, V2, V3:** standoffs at a 2.0 mm inset with Ø2.0 holes. The variant boards have Ø3.0 holes at a 2.5 mm inset.
- **Self-report:** the agent's references were built on the same wrong holes, so its report disagrees with the
  judges' measurements.

Iteration 010 (C1, RC-1001) replaced the generic perfboard's family defaults (Ø3.0 at 2.5) with the measurements of
E1-01's board from the photo (A7: Ø2.0 at 2.0). That fixed E1-01 and broke every other board size. The catalogue now
claims that *every* perfboard is Robin's photographed board. Both the owner decision ("The catalogue part must stay
parametric for the variants … **Variants keep their own boards**", `OWNER_DECISIONS.md`) and the catalogue note in
`variants.json` ("perfboard (generic, sized per request; corner holes 3.0 mm at 2.5 mm from each edge unless
stated)") say otherwise.

## 2. Root causes (grouped)

### RC-1101: one parametric part cannot hold both a measured specimen and family defaults (data model)

`parts/perfboard/part.json` has one value per param. The photo measurements (A7) describe *one specimen*, the 70 × 50
board in Robin's photo, but they are written as defaults for the whole family:

| Param | Catalogue now | E1-01 board (A7, photo) | Variant boards (catalogue family) |
|---|---|---|---|
| `hole_inset` | 2.0 | 2.0 | 2.5 |
| `hole_diameter` | 2.0 | 2.0 | 3.0 |

`parts.instantiate` has no way to say "these values hold for this specimen, those for the family". Python therefore
places standoffs on HOLE datums that are wrong for every non-70 × 50 board. It also builds V-SEAT, V-HOLE-KO,
V-DRIVER, the seating check and `board_screw_passes_hole` on the same wrong datums.

Defects this explains (all three variants; the weight-3 checks are the ones that keep them out of CORRECT):

- **L3.3.1.3 (w3):** standoff pitch 76 × 56 / 86 × 41 / 76 × 36 instead of 75 × 55 / 85 × 40 / 75 × 35 (margin −0.75).
- **L3.3.1.4 (w3):** every standoff and pilot axis is 0.707 mm from its hole. An M2 screw would hit the Ø3.0 hole
  wall by 0.21 mm.
- **L3.12.1.2 (w3):** the seating rule's hole-axis residual is 0.707. No re-seat can fix it, because the two patterns
  differ in pitch.
- **L3.12.2.1 (w1):** `seated` reports 0.000 against 0.707 measured, `clear_driver_k` 0.596 against 1.100, and
  `clear_board` 1.448 against 1.586.

Why this is an agent gap and not only a test-data gap: the judges say the agent "could not have derived" 2.5 / Ø3.0
from the request text. That is true of the *text*. But the catalogue is the agent's data, and its owner states the
family default. The agent's error was to overwrite a family default with one specimen's measurements, and to record
that silently: no assumption line, no provenance. The fix is a representation the code can select from, using data
only. It is not a special case in agent logic.

Why this is not oscillation: iteration ≤ 009 had only the family defaults, so E1-01 failed (iteration 010, G5).
Iteration 010 had only the specimen values, so the variants failed (this iteration). This delta keeps **both** and
selects between them with data. Neither earlier failure can come back while the selection test (section 5, T1)
holds.

### RC-1102: `layout.json` reports a grid residual that its own grid sensor excludes (self-report consistency)

`accept_layout` writes `st.layout_grid_residual = placer.grid_residual(result.placed)`. That is the worst pin
residual over **all** placed parts, including the `pin_pattern`-exempt jacks. `grid_report` and the
`grid_conformance` check exclude those jacks (7.13). So the reported values disagree:

- E1-01: `layout.json` says `grid_residual` 2.876, but the check, and both judges, say 0.000.
- V2: 1.426 against 0.00. V3: 2.75 against 0.00.

All four judges noted it. It has not been graded as a defect yet, but it is exactly the kind of disagreement that
L3.12.2.1 penalises ("the report shall agree with an independent measurement"). The package also gives no
machine-readable statement of the board the agent used: `layout.json` lists only `{width, depth}` for the board.
Judges have to rebuild the hole pattern from part.json, which is how RC-1101 stayed hidden from the agent's own
package.

### RC-1103 (latent): a capped clearance distance is reported as if exact (sensor honesty)

`_clear_measure` / `_inside_measure` call `min_gap(..., clearance + SEARCH_EXTRA)`. When nothing lies within the
search radius, the value returned is the radius itself, and it is reported as `d` (for example 5.2 for the header
sources in E1-01's `inside_contents`). Judge 2 (target) measured ≥ 5.7 there. Pass/fail agrees, but the number reads
as a measurement, not a bound. This is minor, and the rubric's own recipe has the same search limit. It is a
one-line honesty fix to the error signal, so it is in this delta as C3.

### Not agent gaps (for Robin, graded as written)

- **V1 / V2 L3.1.3.1 (w2), USB mouth position.** The V1 delta asks for X in [−1.8, 0.5]; V2 asks for X in
  [−1.8, −0.8]. Both are the pre-owner-decision "flush" positions. Under the owner's centred grid (OWNER_DECISIONS 1;
  L2.1.6), the first column on these boards is at X 5.71 / 5.63, which puts the mouth at 3.04 / 2.96. Both judges
  say the two checks cannot pass together. Two things do not change this: the board-hole fix, and the
  flush-to-edge alternative (it would break L3.1.6.1 and OWNER_DECISIONS 1). This is weight 2, so it does not stop
  the variants reaching CORRECT, which is what convergence needs. The loop asked this as **Q9** in iteration 010, and
  it is still open.
- **rubric.md section 6** lists the standoff pilot as Ø2.0–2.2 (M2.5). requirements.md L2.3.3 / A9 say 1.6–1.8 (M2).
  This is **Q8**, still open.
- PJ-320A nose (2 mm) missing from the catalogue body: this was already noted in iterations 006 and 010. It fits inside
  the wall hole and is not graded.

## 3. Delta (one pass; changes C1 to C3)

The order of leverage: C1 is the only change that moves any verdict class (three variants, MINOR → CORRECT). C2 and C3
make the self-report agree with the judges.

### C1 (RC-1101): catalogue specimens, selected by data (`parts.py`, `parts/perfboard/part.json`, `assembly.py`)

**Data model (part.json schema 1, a new optional block).** A part may list measured specimens of its family:

```json
"specimens": [
  {
    "id": "photo_70x50",
    "match": {"width": 70.0, "depth": 50.0},
    "params": {"hole_inset": 2.0, "hole_diameter": 2.0},
    "source": "requirements.md A7: the owner's photographed board (2026-10-24), corner holes 2.0 in from each edge, Ø2.0 (hole + plated ring ~2.1)"
  }
]
```

- **`match`:** values for some of the part's `from_request` params. A specimen applies when every one of those params
  is given and lies within the part's `size_tolerance` of the match value.
- **`params`:** specimen values for declared, non-`from_request` params. They replace the family `default`s. An
  explicitly given param still wins over a specimen value.
- **`source`:** required, like every number in the catalogue.

**perfboard part.json:**

- Restore the family defaults `hole_inset` 2.5 and `hole_diameter` 3.0. Their `source` cites the catalogue's family
  note: "typical green 2.54 mm proto board; catalogue family default, corner holes 3.0 mm at 2.5 mm from each edge
  unless stated (OWNER_DECISIONS: variants keep their own boards)".
- Move the A7 values into the specimen above.
- Rewrite the top-level `source` so it describes the family and points to the specimen for A7.
- `hole_keepout_diameter` (7.0), `grid_margin_x/y` (4.74 / 2.54), the centred finite grid and every self-check stay
  family data, unchanged. OWNER_DECISIONS 1 says the generic representation is the centred grid from the board size
  and an edge margin. So E1-01's grid (24 × 18 from 5.79, 3.41) and the variants' grids (first column 5.71 / 5.63)
  do not change.
- No number is added to agent code. 70 and 50 appear only in part.json.

**`parts.py`:**

- `Part.specimens` (list) and `Part.specimen_for(given) -> Optional[dict]`. It returns the one specimen whose `match`
  holds (`|given[k] − match[k]| ≤ size_tolerance` for every k), or None.
- `_resolve_param_values(part, given)` takes `sp = part.specimen_for(given)` first. In the loop: given → `sp.params`
  → `default` → MissingParam.
- `PartInstance` gains `specimen: Optional[dict] = None`, holding `{id, source, params}`. `instantiate` sets it.
- Every instantiation picks the specimen up automatically: Contents, the Placer, envelopes, replays and
  `measure_package` references. So no code path can build E1-01's board with family holes, or a variant's board with
  specimen holes.
- **Load gate** (`validate` / `Catalog.load`, typed `GateFailure`s). The part is dropped and reported, as R1–R9 are,
  when any of these fails:
  - a specimen has no `id` or `source`, or its id is a duplicate;
  - a `match` key is not a `from_request` param;
  - a `params` key is undeclared or is a `from_request` param;
  - two specimens' matches overlap within `size_tolerance`, which would make the choice ambiguous;
  - an instance at a specimen's `match` fails `self_checks` or R1.

  `validate` also runs on each specimen's match instance, as well as on `gate_params`.

**`assembly.py` (provenance; Contents and WritePackage):**

- After the board params are set, Contents instantiates the board once.
  - If `inst.specimen` is set: for each specimen param, `spec_provenance["board.<p>"] = "catalogue:<part>
    specimen <id> (<source>)"`, plus a note `contents: board matches catalogue specimen <id>`.
  - Otherwise, for each hole param the request did not give (`hole_inset`, `hole_diameter`): `spec_provenance` =
    `catalogue:<part> family default`, and one assumption line built from the part data: "The request does not state
    the board's mounting-hole pattern; the catalogue family default is used: Ø{hole_diameter} holes {hole_inset} mm
    from each edge." Take the param names from the HOLE datum's expressions, or list every non-request param that
    has no specimen value. Do not hard-code a list of names in agent code if the datum can give it.
  - The assumption goes into `assembly.assumptions`, so it appears in `design.json` and in the verification matrix
    footer.
- `layout.json` gains a `board` block. The judge can then rebuild the references from the package alone:
  - `part`, `specimen` (id or null), `params` (the **resolved** instance params, every one);
  - `holes` (the four HOLE axes in the enclosure frame), `hole_diameter`, `hole_keepout_diameter`;
  - `grid` (`origin`, `pitch`, `count`);
  - `screw` (the chosen board screw id).

**Expected numbers (offline, scripted controller):**

- E1-01 is **unchanged**: specimen photo_70x50, so holes Ø2.0 at 2.0, standoffs 66 × 46, M2, Ø7 columns, and size
  84.17 × 64.17 × 24.70. Bodies byte-identical to iteration 011 target_s0 at the same answers.
- V1 / V2 / V3 use the family holes Ø3.0 at 2.5:
  - standoffs on 75 × 55, 85 × 40 and 75 × 35;
  - the board screw stays M2 (smallest thread that passes Ø3.0), pilot Ø1.7;
  - the columns stay Ø7 (keep-out ≥ M2 head + 2·driver);
  - the corner columns move 0.5 mm inward, so each outside dimension shrinks by up to 1 mm. The cavity bound
    follows the columns; the placer re-checks the free spans.

### C2 (RC-1102): one grid number in the package (`assembly.py`)

- `accept_layout`:
  - `st.layout_grid_residual = st.grid_report["max"]` (exempt parts excluded, as the check does);
  - new `st.layout_grid_exempt = st.grid_report["exempt"]`;
  - keep `placer.grid_residual(...)` as `layout_grid_residual_all`, labelled.
- `layout.json` writes:
  - `grid_residual`: the non-exempt max; equal to the `grid_conformance` evidence;
  - `grid_exempt`: the node ids, each with the assumption text from `grid_exempt_text`;
  - `grid_residual_all_parts`, with a key name that says it includes exempt parts.
- No geometry changes.

### C3 (RC-1103): capped distances are marked as bounds (`assembly_checks.py`)

- `_clear_measure` and `_inside_measure` compare their `min_gap` results with the search radius. When a gap is
  ≥ `search − tol.measure`, the row gets `"d_capped": true` and `"d_at_least": search`. `d` stays the search value,
  so the pass/fail logic and margins are unchanged.
- This applies to the `gap_to_solids` / `gap_to_outside` terms and to every `per_source` row.
- `detail` strings print `≥ x` for a capped value.
- `reference_table` / the self-report prints `≥ x` for such rows, so no reader takes it as a measurement.
- `measure_package` gets this through the same functions.

## 4. Files and functions

| File | Change | Gap |
|---|---|---|
| `parts.py` | `Part.specimens`, `Part.specimen_for`, `_resolve_param_values` order, `PartInstance.specimen`, specimen gate in `validate` / `Catalog.load` | RC-1101 |
| `benchmarks/enclosure/parts/perfboard/part.json` | family defaults 2.5 / 3.0 restored; `specimens: [photo_70x50]` holding the A7 values; sources | RC-1101 |
| `assembly.py` | Contents provenance + family-default assumption; `layout.json` `board` block; `accept_layout` grid fields (C2) | RC-1101, RC-1102 |
| `assembly_checks.py` | `d_capped` / `d_at_least` in `_clear_measure`, `_inside_measure`, `per_source`; `≥` in detail and reference table | RC-1103 |
| `test_parts.py`, `test_assembly.py`, `test_assembly_checks.py` | tests below | all |
| `loop/ARCHITECTURE.md` | 3.1 schema (`specimens`) and 7.14 (already written by this gap analysis; the implementer adds "fixed by the code") | RC-1101 |
| `loop/RUN.md` | test count; iteration-012 SEED note (section 6) | process |

`cad_agent.py`, `cascade.py`, `cad_checks.py`, `layout.py`, `feature_graph.py`, `design_rules.json` and
`benchmarks/run.py` are untouched. The cascade arm needs no re-run.

## 5. Unit tests (all offline; fake LLMs: ScriptedLLM and recorded replays)

New:

- **T1 `TestPerfboard.test_specimen_selected_by_size`:**
  - 70 × 50 gives specimen photo_70x50, HOLE at (2, 2) … (68, 48), Ø2.0, keep-out 7.0, grid 24 × 18 from
    (5.79, 3.41).
  - 70.1 × 49.9 (inside `size_tolerance`) gives the same specimen.
  - 80 × 60, 90 × 45, 80 × 40 and the gate sample 100 × 75 give `specimen is None`, HOLE inset 2.5 and Ø3.0, with an
    unchanged grid.
  - An explicit `{"hole_inset": 2.2}` beats the specimen.
  - The target numbers live in the test (as in iteration 010's TestPerfboard).
- **T2 `TestPerfboard.test_specimen_gate`:** fixture parts, each dropped with a typed reason:
  - overlapping matches;
  - a match on a non-request param;
  - a `params` key that is undeclared or is a request param;
  - a missing source;
  - a specimen whose match instance fails a self-check (inset < diameter/2).
- **T3 `TestContents.test_board_provenance`** (ScriptedLLM):
  - E1-01: `spec_provenance["board.hole_inset"]` starts with `catalogue:perfboard specimen photo_70x50`, and no
    hole-pattern assumption is written.
  - V1: provenance `family default`, and exactly one assumption line naming Ø3 and 2.5. The numbers in that line are
    read back from the instance, not from the test.
- **T4 `TestEndToEndIter011.test_variant_boards_use_family_holes`** (fn 24, OpenSCAD; V1, V2, V3; sliced STLs, as the
  judges did):
  - standoff and pilot axes are within 0.05 of (2.5, 2.5), (w − 2.5, 2.5), (2.5, d − 2.5), (w − 2.5, d − 2.5);
  - the pitch is (w − 5) × (d − 5);
  - `seated` residual ≤ 0.05;
  - `board_screw_passes_hole` passes with hole 3.0;
  - `clear_driver_k` agrees within 0.10 with an independent driver column (Ø from requirements V-DRIVER, here read as
    head + 2·driver_clearance from the fastener part) on the family holes;
  - the outcome is verified with no conflicts;
  - the `layout.json` `board` block says `specimen: null`, `hole_diameter: 3.0`, and holes equal to the HOLE datums.

  **This test fails on the current code** (axes at 2.0).
- **T5 `TestEndToEndIter011.test_e1_unchanged`:**
  - E1-01 at the same scripted answers gives the iteration 010 offline numbers: standoffs 66 × 46, size
    84.17 × 64.17 × 24.70, pilot Ø1.7;
  - `layout.json` `board.specimen == "photo_70x50"`.
- **T6 `TestReplayIter011.test_replay_iter011_answers`** (skipped if the folders are missing):
  - replay `iter_011/target_s0/*/llm/`: base and lid volumes equal to the delivered iteration 011 STLs' volumes
    within 0.5% (proves C1 did not move E1-01);
  - replay `iter_011/V1_s0/*/llm/`: the standoffs now sit at the 2.5 inset.
- **T7 `TestArrange.test_layout_grid_residual_matches_check`** (C2):
  - E1-01: `layout.json` `grid_residual == grid_conformance.evidence.max == 0.0`;
  - `grid_exempt == ["connector_1_1", "connector_1_2"]` (taken from the report, not literals: assert that it
    equals the set of `pin_pattern` kinds);
  - `grid_residual_all_parts > 0`.
- **T8 `TestClearOf.test_capped_distance_is_marked`** (C3):
  - a box 20 mm from the bodies: `d == clearance + SEARCH_EXTRA`, `d_capped` true, `≥` in detail;
  - a box 1 mm away: no `d_capped` key, `d` within 1e-3 of 1.0;
  - the same through `per_source` and through `inside`.

Changed tests (behaviour intentionally changed; the implementer gives a one-line reason in the ledger for each):

- `TestPerfboard.test_measured_board_70x50`: unchanged assertions, plus `inst.specimen["id"] == "photo_70x50"`.
- Any test that instantiates the perfboard at a non-70 × 50 size and asserts 2.0-inset holes, or pins
  iteration-010 V1/V2/V3 volumes or sizes (`TestEndToEndIter010` V1–V3, `TestReplayIter007/008` V1 replays,
  `TestDeriveFeatures` V-runs): update to the family holes. Reason: RC-1101, variant boards keep their own holes. Do
  **not** loosen tolerances. Re-pin the numbers from the new offline run.

Hard-coding guard: `test_no_hardcoding` must stay green. No new literal goes into agent code. The specimen's 70 / 50 /
2.0 live in part.json; the 2.5 / 3.0 family defaults live in part.json.

## 6. Expected effect on the verdict

| Run | Now | After C1–C3 (expected) |
|---|---|---|
| E1-01 | MEETS, 1.0 | MEETS, 1.0 (geometry unchanged; `layout.json` now agrees with the grid check) |
| V1 | MINOR, 0.912 | **CORRECT**. L3.3.1.3, L3.3.1.4, L3.12.1.2 and L3.12.2.1 pass; L3.1.3.1 (w2) still fails on the Q9 conflict, so DNM / CORRECT |
| V2 | MINOR, 0.912 | **CORRECT**, the same as V1 (L3.1.3.1 w2 remains) |
| V3 | MINOR, 0.926 | **CORRECT**, and probably MEETS: V3 had no L3.1.3.1 failure |

If this holds, the variants part of convergence (each at least CORRECT on one run) is met. Convergence then needs
E1-01 MEETS on two more seeds.

**Run step for iteration 012 (process fix):** SEED = 12. Run exactly the commands in RUN.md section 3:

```sh
( SEED=0; run_one E1-01 target_s0 )
run_one E1-01
run_one V1; run_one V2; run_one V3
```

That gives five rows: target_s0, E1-01_s12, V1_s12, V2_s12, V3_s12. Iteration 011 ran the variants at seed 0 and
skipped E1-01's second seed. If E1-01_s12 and target_s0 both MEET, run the convergence confirmation in RUN.md
section 3 (`SEED + 1`, `SEED + 2`) in the same iteration.

## 7. Risks and questions for Robin

- **Risk (C1): the selection is by size.** A future request for a different 70 × 50 board would get the photographed
  board's holes. The provenance line and the `layout.json` `board.specimen` field make this visible, and an explicit
  request number always wins. A later delta could bind hole numbers stated in the request text (the catalogue's
  "unless stated" clause) through `ask_params` with `from_request: "optional"`. It is left out here, because a 9B
  model binding "3.5 mm" (the jack) to `hole_diameter` is a real risk, and no current request states holes.
- **Risk (C1): the cavity shrinks on the variants.** The free spans and the plug-to-boss ligaments change by up to
  0.5 mm. T4 checks every variant end to end; the ligament sensor (7.12) guards the seam and the bosses.
- **Q9 (repeat, now the only thing between V1 / V2 and MEETS):** update the variants.json grading deltas for the
  USB mouth to the owner's grid rule, "first pin on grid column 0", as E1-01's L2.1.3 now says. That is X ≈ 3.04 on
  V1 and ≈ 2.96 on V2. Or say that variant boards have no measured grid, and the flush rule applies to them.
- **Q8 (repeat):** rubric.md section 6 lists the standoff pilot as Ø2.0–2.2. requirements.md says 1.6–1.8. Judges
  grade against requirements.md.
- **Q11 (new):** do the variant boards share the photographed board's grid margins (edge-pad column) and the Ø7
  hole keep-out? This delta keeps both as family data, per OWNER_DECISIONS 1. If not, they move into the specimen,
  and the variants need their own family values.

## 8. Fix round 1 (reviewer rejection)

- R1 (full suite not seen passing in one run): I re-ran the exact 10-module command from RUN.md section 2 to the end,
  with no other test or Ollama process running. Result: `Ran 385 tests in 1092.701s`, `OK`, exit 0 (log
  `scratchpad/fix011.log`). The LEDGER progress row and the iteration 011 Tests result line now give this result.
- R2 (RUN.md line 57 still said 376 tests): it now says 385 tests since iteration 011, about 1100 s.
- No code or test changes in this round.
