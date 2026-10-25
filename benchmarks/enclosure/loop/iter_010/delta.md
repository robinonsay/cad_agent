# Iteration 010: gap analysis and delta design

Input: `target_s0` (E1-01, seed 0, rc 3 `unsatisfied`, 80 s). This is the first run judged against
Robin's owner decisions (`OWNER_DECISIONS.md`, updated `requirements.md` A5, A7, A9, L2.1.3, L2.1.6, L2.3.x).
Both judges: **DOES NOT MEET / WRONG**. Gate G5 fails on L3.3.3.1. Score 119/137 (judge 1, 0.869).

Tooling: the claude-context MCP server failed to connect in this session. I read known paths and ran targeted
grep only.

## 1. What happened

The agent built the same package as iteration 009, and nothing in its control logic changed. The judges
now grade against the measured board (A7) and the M2 screw (A9). The agent's catalogue and two of its rules
still encode the earlier assumptions. Every defect traces to one of four root causes. None is a controller
(9B) mistake: the votes and ranks were right (`edge[module_1] = -X` 3/3, `+X` for the jacks, prescore 0).

## 2. Root causes (grouped)

### RC-1001: stale board data in the catalogue (data model)

`parts/perfboard/part.json` has these values:

| Field | Catalogue | requirements.md A7 |
|---|---|---|
| `hole_inset` | 2.5 | 2.0 |
| `hole_diameter` | 3.0 | 2.0 |
| `grid.origin` | `(hole_inset, hole_inset)`, `soft: true` | centred 24 × 18 array, first column 5.79, first row 3.41 |

**Representation gap:** `grid` is an *infinite lattice* (origin + pitch). Nothing says where the holes stop.
The real board's grid is a finite array centred on the board, with an edge-pad column outside it.

Defects this explains:

- **L3.3.1.3:** standoff pitch 65 × 45, should be 66 × 46.
- **L3.3.1.4 and L3.12.1.2:** offset 0.707 from each hole.
- **L3.3.5.1:** the walls reach 0.4 mm into the Ø7 columns. The cavity bound is correct, but it follows
  the hole datums, which sit 0.5 mm too far in.
- **L3.12.2.1:** the agent measured against the same stale datums, so its numbers disagree with the judge's.
- **L3.1.6.1, in part:** the grid origin is wrong.

### RC-1002: no M2 screw, and a pass test that cannot accept one (catalogue + rule)

The catalogue has no `screw_m2_selftap`. `assembly.board_screw` (assembly.py:715) accepts a screw only when
`thread + 2·rules.screw_hole_clearance_min ≤ hole` (0.2 mm per side, from ISO 273). ISO 273 sizes holes that
*the design drills*, such as the lid holes. The board's corner hole is a given datum.

- **With the stale Ø3.0:** M2.5 passes (2.9 ≤ 3.0), so the pilots are Ø2.1. This is the **G5 blocker
  (L3.3.3.1)**.
- **With the correct Ø2.0:** nothing passes, not even M2 (2.4 > 2.0). ArrangeContents would fail with
  "no catalogue screw passes the board's mounting holes" and produce **no package (G0)**.

Fixing RC-1001 alone therefore turns WRONG/G5 into no package at all. RC-1001 and RC-1002 must land together.

Missing sensor: the agent has a pilot *depth* check (`value_at_least`), but no pilot *diameter* check against
the chosen fastener's range. Here it would have passed anyway (M2.5's range), so this is an audit-rule gap
(7.12), not the cause.

### RC-1003: the screw-head and seat column is sized from the screw alone (derivation rule)

Today `seat_d = head_diameter + 2·rules.driver_clearance` is used for:

- V-SEAT and V-HOLE-KO;
- the cavity's plan bound;
- the placement's hole columns.

This appears in two places: `ArrangeContents.update`, assembly.py:848, and `build_envelopes`, assembly.py:1029.

- With M2.5 the value came out at Ø7.0 (5.0 + 2), the same as the judge's V-HOLE-KO and V-SEAT.
- Once the board screw becomes M2 (ISO 7045 head Ø4.0) the value drops to Ø6.0. The `driver` row is also
  Ø6.0. The -Y and +Y walls would then sit at 2.0 − 3.0 − 0.1 = −1.1 again, and L3.3.5.1 would fail exactly
  as it does now.

So this is a *latent* defect that RC-1002's fix would expose. The board declares no keep-out round its
mounting holes, but real board drawings do. With a board keep-out, the column is the larger of what the board
reserves and what the fastener needs.

### RC-1004: grid placement uses the old priority and an infinite lattice (control logic)

`layout.Placer.place` keeps the part flush with the edge and snaps it along the edge only (ARCHITECTURE 7.5:
"a port reaching its wall outranks grid conformance"). The agent's own sensor already flagged this, typed
correctly: `flush_to_edge`, `normal_needed 0.98`, listed in `assembly.conflicts`.

Robin has since answered the conflict. L2.1.3 now says "the Pico sits with its first header pin on the grid
column nearest the −X edge", and the plug envelope, not the flush rule, sets the opening.

The rule is generic: a through-hole part cannot be soldered to a perfboard off its holes. So when the part's
pin pattern can meet the grid, the part goes on the grid, at the on-grid position nearest its chosen edge.

This only works with a *finite* grid. Moving inward from the flush pose on the infinite lattice, the
nearest on-lattice position puts the first pin at X 3.25. That is inside the edge-pad strip, where the board
has no hole, and the mouth would land at X 0.58, outside L2.1.3's [2.62, 3.62]. `grid_feasibility`,
`_offgrid` and `normal_needed` all work modulo the pitch, so they cannot sense this.

Defects this explains:

- **L3.1.3.1:** USB_MOUTH at X −1.30.
- **L3.1.6.1:** the Pico's pins are 1.1–4.5 mm off the grid.

Related but not judged: the jacks are typed `pin_pattern` (best residual on any lattice is 0.54). A5 and
L2.1.6 now exempt them, because they mount through enlarged holes. The agent still counts them as failing
`grid_conformance`, so its own verdict can never be `verified`. A part whose pins cannot meet any grid
position yields a check that no design can pass. That is a constant, not an error signal.

New exposure (generic): moving a module inward puts its plug's shell and overmold over the board margin.
No agent check says that a plug envelope must clear the *reference parts*, such as the board or neighbouring
parts. Today the only check is against the printed bodies. For E1-01 the overmold's underside is 1.4 above the
board top, so the plug clears. A flat-soldered module (A3, USB axis about 2.4) would put the overmold into
the board, and the agent would not notice.

## 3. Delta (one pass; changes C1 to C6)

C1 to C4 close every judged defect. C5 and C6 are small sensor additions that keep the error signal honest
after the change (the 7.12 audit rule). No change touches `cad_agent.py`, `cascade.py` or `cad_checks.py`.

### C1 (RC-1001): measured, parametric perfboard with a finite centred grid

**`parts/perfboard/part.json`** (data only; the source text cites A7 and the photo method)

Params:

| Param | Value | Source to cite |
|---|---|---|
| `hole_inset` | 2.0 | A7 |
| `hole_diameter` | 2.0 | A7 |
| `grid_margin_x` | see below | minimum distance from a short (X) edge to the first grid column centre; the edge-pad column lies outside the grid |
| `grid_margin_y` | see below | the same for the long (Y) edges |

For the margins, propose `grid_margin_x = 4.74` (edge-pad column centre ≈ 2.2 plus one pitch, A7) and
`grid_margin_y = 2.54` (one pitch).

- Any value in X (4.52, 5.79] and Y (2.14, 3.41] reproduces A7's 24 × 18 holes on 70 × 50.
- The implementer states the chosen value and its reason in `source`.
- These are board-family layout constants. They live only in this file.

The grid block becomes finite and centred:

```json
"grid": {"pitch": "grid_pitch",
         "count":  ["floor((width - 2*grid_margin_x) / grid_pitch) + 1",
                    "floor((depth - 2*grid_margin_y) / grid_pitch) + 1"],
         "origin": ["(width - (floor((width - 2*grid_margin_x) / grid_pitch)) * grid_pitch) / 2",
                    "(depth - (floor((depth - 2*grid_margin_y) / grid_pitch)) * grid_pitch) / 2", 0],
         "source": "A7: measured hole array, centred on the board; edge pads are not grid holes"}
```

- Remove `soft`. The registration is measured now, and a centred grid maps onto itself under the
  half-turn on every board size.
- New `self_checks`:
  - the grid lies inside the board;
  - the grid is centred: `origin.x + (count.x−1)·pitch/2 = width/2`, and the same in Y;
  - the first column is ≥ `grid_margin_x`.
- The `HOLE` datum gains `"keepout_diameter": "hole_keepout_diameter"`. New param
  `hole_keepout_diameter = 7.0` (source: the board's component and fastener keep-out round each mounting
  hole, requirements V-SEAT / V-HOLE-KO). See C3.

**`feature_graph.py`:** add `floor` to `FUNCTIONS`. This is generic math, like `ceil_to`.

**`parts.py`:**

- The `grid` block accepts `count` (2 expressions). Both the loader and `parts.validate` evaluate it.
  `count` must be an integer ≥ 1. A grid without `count` stays an infinite lattice, for backward
  compatibility.
- `Axis` and `AxisList` gain an optional `keepout_diameter`. `transform` carries it through, and
  `datum_value` answers `HOLE.keepout_diameter`.

### C2 (RC-1002): M2 board screw and a given-hole pass test

**New `parts/screw_m2_selftap/part.json`**, in the same schema as the M2.5 part:

| Param | Value | Source |
|---|---|---|
| `thread_diameter` | 2.0 | |
| `pilot_diameter` | 1.7 | A9 |
| `pilot_min` / `pilot_max` | 1.6 / 1.8 | A9 |
| `clearance_diameter` | 2.4 | ISO 273 medium |
| `head_diameter` | 4.0 | ISO 7045 dk |
| `head_height` | 1.6 | ISO 7045 k |
| `length` | 6.0 | stock |
| `min_engagement` | 5.0 | owner's M2 board-screw spec, requirements L2.3.3 / A9 |
| `min_boss_od` | 5.0 | owner's standoff spec, L2.3.2 |

- Every number cites its source, as the M2.5 part already cites A9/A10.
- Self-checks as in the M2.5 part.
- Hard rules allow target numbers in part.json. They are never allowed in agent code.

**`design_rules.json`:** new key `given_hole_clearance_min` = 0.0 mm. Source: a board's existing mounting
hole is a fixed datum. A screw passes it when its major diameter fits (A9: "M2 passes the Ø2.0 holes"). ISO
273 clearance applies only to holes the design makes.

**`assembly.board_screw`:**

- The pass test becomes `thread + 2·given_hole_clearance_min ≤ hole + measure_tol`.
- The selection stays the smallest thread that passes. Choice tag: `rule:smallest_thread_through_board_hole`.
- `screw_hole_clearance_min` keeps its meaning for drilled clearance holes.
- `lid_screw` is unchanged: the largest thread is still M3.

### C3 (RC-1003): one column-diameter rule, read from board and fastener

**`assembly.hole_column_d(st, board_inst)`** returns
`max(HOLE.keepout_diameter or 0, fastener.board.head_diameter + 2·rules.driver_clearance)`. Its provenance is
recorded in `design.json` `assembly.notes`.

- Used in `ArrangeContents.update` (the Placer's `column_d`) and in `build_envelopes` (seat and hole_ko
  columns), replacing both inline formulas.
- A board without a keep-out falls back to today's rule.
- `KEEP_OUTS` is unchanged. The `hole_keepout` row still bounds the cavity with `plan: "self"`, so the cavity
  follows the column automatically: −Y wall at 2.0 − 3.5 − 0.1 = −1.6.

### C4 (RC-1004): finite grid and on-grid placement nearest the edge (`layout.py`)

**Grid object.** `Placer._grid` returns `Grid(origin(2), pitch, count(2) | None)`. `None` means an infinite
lattice. Nearest hole = `clip(round((q − origin)/pitch), 0, count−1)`.

- `_offgrid`, `grid_residual` and `grid_report` measure against *existing* holes.
- `board_symmetries` compares the finite hole sets, not the origin modulo the pitch.

**`grid_positions(pins_rel, grid, limit, step)`** (new, pure). Let `s0 = grid_feasibility(...)["any_shift"]`
on the lattice.

1. If `best_any > limit`, return `[]`: the part is `pin_pattern`.
2. Otherwise enumerate `s0 + pitch·(i, j)` over the index ranges that keep every pin within
   `[origin − limit, origin + (count−1)·pitch + limit]`.
3. Keep the shifts whose finite-grid residual is ≤ limit.

There are at most `count.x · count.y` candidates (432 on E1-01), and the work is vectorised.

**`Placer.place`, snap step** (replaces the tangential-only `grid_shift` call). For each placed group whose
part has pin data:

1. Build the candidates from `grid_positions`, expressed as the move `d` from the spread pose.
2. For an edge-placed part (normal axis `a`, outward sign `σ`), the inward move is `n = −σ·d[a]`. Discard
   candidates with `n < −measure_tol`: an outward move would push the part past the board edge.
3. Order by (`n` ascending, `|d[tangent]|` ascending). This is "nearest the chosen edge, then nearest its
   spread slot".
4. Accept the first candidate whose moved group passes `collisions` and `_spacing_ok`, as the code does now.
5. If none passes, the part stays at the spread pose, and the report types the reason (below).

A part with no edge (`_free_spot`) orders the candidates by plan distance from its free spot. A
`pin_pattern` part is not snapped: A5's legs go through enlarged holes, so the spread pose stays.

**`_resolve` keeps the grid.** For a group that was snapped, the 1-D collision shift steps by
`k·pitch` (an integer number of pitches), not by `rules.layout_step`.

**Grid kinds** (`grid_kind`, `grid_report`, `assembly.grid_conflict_text`):

| Kind | Meaning |
|---|---|
| `ok` | |
| `pin_pattern` | Exempt. Reported, not failing (C5). |
| `grid_extent` | The pattern meets the lattice, but no position inside the finite grid does. A catalogue or requirement question; a conflict entry. |
| `blocked` | On-grid positions exist, but every one collides or crowds a port. A conflict entry that lists the blocking pairs. |
| `tangential` | The snap failed: an agent bug, not a conflict. |
| `no_pin_data` | |

`flush_to_edge` is retired. Robin resolved that priority in L2.1.3.

The change of priority is not oscillation. 7.5's tangential-only rule was right under the old L2.1.3
("flush"). The owner changed the requirement. The finite grid is the new capability that makes the new rule
correct. Without it, the first pin would move into the edge-pad strip, as noted in RC-1004.

### C5 (RC-1004, sensor side): grid exemption and plug clear of references (`assembly.py`)

**`grid_check`:**

- Parts typed `pin_pattern` go to `evidence.exempt`, each with the assumption "mounted through enlarged
  holes; its pin pattern meets no grid position (best X mm)".
- They no longer fail `grid_conformance`. The check stays non-vacuous: a module with a feasible pattern that
  is off grid still fails.
- `conflict_entries` keeps `grid_extent` and `blocked`. It drops `pin_pattern` from the conflicts, because it
  is now an assumption.

**New rule-derived check `plug_refs_<group>`** for each exposed connector:

- `clear_of(references except the connector's own part and its stack parts, plug-sweep group, 0.0)`.
- Built in `build_plan` next to the `plug_*` KEEP_OUTS rows, so it also runs in `prescore` and counts towards
  the controllable error.
- It is a check on references only, with no bodies, so `measure_package` reports it from the same solids.
- E1-01: d ≈ 1.4 to the board top (overmold underside at Z 1.4).

### C6 (audit rule 7.12): pilot-diameter sensor

New `value_at_least`-style band check, `pilot_band_<node>`, on the resolved graph. Every `pilot` node's `d`
must lie within the chosen fastener's `[pilot_min, pilot_max]`. Its links go to L1.3 via the standoff/boss
roles.

Also add `board_screw_passes_hole`: the board screw's thread must be ≤ the board's `HOLE.diameter` +
`measure_tol`. This is a graph-data check, so the screw/hole relation is sensed and not only enforced at
selection.

Neither check is re-measured on the STLs. `measure_package` has no inscribed-circle recipe yet; that is
deferred and noted.

## 4. Files and functions

| File | Change |
|---|---|
| `benchmarks/enclosure/parts/perfboard/part.json` | C1 data: holes, margins, finite centred grid, `keepout_diameter`, self_checks, `soft` removed |
| `benchmarks/enclosure/parts/screw_m2_selftap/part.json` | new (C2) |
| `design_rules.json` | `given_hole_clearance_min` (C2) |
| `feature_graph.py` | `floor` in `FUNCTIONS` (C1) |
| `parts.py` | grid `count`; `keepout_diameter` on axis datums (`_datums`, `transform`, `datum_value`); validate grid (C1) |
| `layout.py` | `Grid`, finite `_offgrid`, `grid_positions`, 2-D snap in `place`, pitch-step `_resolve`, kinds `grid_extent` / `blocked`, finite `board_symmetries`; module docstring item 5 rewritten (C4) |
| `assembly.py` | `board_screw` pass test (C2); `hole_column_d` used in two places (C3); `grid_check` exemption, conflict kinds and texts (C5); `plug_refs_*` in `build_plan` (C5); `pilot_band_*`, `board_screw_passes_hole` (C6) |
| `assembly_checks.py` | only if a band helper is missing: `value_in_band(check_id, value, lo, hi, tol, ...)` |

## 5. Unit tests (all offline; fake LLMs: ScriptedLLM, recorded replays)

New tests (each names the defect it guards):

1. `test_parts.TestPerfboard.test_measured_board_70x50` (RC-1001):
   - `HOLE` at (2,2), (68,2), (2,48), (68,48), Ø2.0, `keepout_diameter` 7.0;
   - grid count (24, 18) and origin (5.79, 3.41) within 1e-9;
   - all self_checks pass.
   - The numbers sit in the test file (tests are not scanned) and are read back from part.json.
2. `test_parts.TestPerfboard.test_grid_centred_on_every_size`. For 80×60, 90×45, 80×40 and 100×75:
   - the grid is centred;
   - the first column is ≥ `grid_margin_x`;
   - the count is an integer;
   - the half-turn symmetry holds (`layout.board_symmetries` returns 2 entries with no note).
3. `test_feature_graph.test_floor_function`.
4. `test_assembly.TestFasteners.test_board_screw_through_given_hole` (RC-1002):
   - a Ø2.0 hole selects `screw_m2_selftap`;
   - M2.5 is rejected for Ø2.0, which reproduces the G5 cause;
   - a Ø1.5 hole returns None, and ArrangeContents fails with the typed message;
   - `lid_screw` is still M3.
5. `test_assembly.TestDeriveFeatures.test_column_takes_board_keepout` (RC-1003). On E1-01:
   - the seat and hole_ko nodes have d = 7.0 = max(keepout, 4.0 + 2·1.0);
   - the cavity's inner −Y face is ≤ hole_y − 3.5 − design_margin.
   - Mutant (`keepout_diameter` removed): d = 6.0, and the face moves to −1.1. This proves the bound
     follows the data.
6. `test_assembly.TestGridPlacement.test_pico_first_pin_on_column_nearest_edge` (RC-1004). E1-01 with a
   scripted controller:
   - the Pico's first pin X equals the grid's first column;
   - every Pico pin's finite-grid residual is ≤ 1e-6;
   - USB_MOUTH x = column 0 − `pin_from_short_edge` − `usb_overhang`, all read from part data;
   - the jacks' mouths are still flush, and they are not snapped.
7. `test_assembly.TestGridPlacement.test_finite_grid_never_uses_margin_lattice_points`. A synthetic board
   whose infinite lattice has points in the margin:
   - the placer must not choose the lattice point at `n = 1.88`, which is today's `normal_needed`
     behaviour;
   - **fails on the pre-delta code.**
8. `test_assembly.TestGridPlacement.test_grid_extent_and_blocked_kinds`:
   - a pin row longer than the grid gives `grid_extent` and a conflict entry;
   - with a fixture part on every on-grid position, the result is `blocked`, with the pairs listed;
   - an off-lattice pattern is `pin_pattern` and exempt.
9. `test_assembly.TestGridPlacement.test_resolve_keeps_grid`: a collision shift of a snapped group is a whole
   number of pitches, and the residual stays at 0.
10. `test_assembly.TestDeriveFeatures.test_plug_clear_of_references` (C5):
    - E1-01 passes with d ≥ 1.0;
    - a fixture module with its USB axis 2.4 above the board, moved inward, fails, with the board named in
      `per_source`.
11. `test_assembly.TestDeriveFeatures.test_pilot_band_and_screw_hole_checks` (C6):
    - the M2 pilot 1.7 passes;
    - a mutant graph with an M2.5 pilot (2.1) on the M2 board screw fails `pilot_band_*`;
    - a mutant board Ø1.9 fails `board_screw_passes_hole`.
12. `test_assembly.TestEndToEnd` for E1-01 and V1–V3 (scripted, fn 24, OpenSCAD meshes):
    - every frozen check passes, the outcome is `verified`, and `assembly.conflicts` is empty;
    - pilot inscribed Ø1.7 ± 0.02 on the STL;
    - standoff pitch equals the HOLE pitch;
    - the self-report agrees with references rebuilt from part.json at the layout.json poses (7.8 rule);
    - the board-clearance exemption is Ø(7.0 + 2·0.5), the same as the judge's Ø8.
13. `test_assembly.TestReplayIter010`: the iteration 010 `llm/` answers, scripted, reach `verified`, with the
    Pico on grid column 0.

Tests expected to change (behaviour changed on purpose; one line each in the ledger):

- **Assertions that the grid is `soft`** (test_assembly ~781, ~2092): the grid is measured now (C1).
- **Assertions that expect `flush_to_edge` and `pin_pattern` conflicts** (~788, ~2110, ~2396, ~2455): the
  kind is retired and the jacks are exempt (C4/C5).
- **The 1136–1148 symmetry fixture:** it edits `hole_inset` and `soft`. Port it to the finite grid.
- **`test_parts` fixtures that read `hole_inset` defaults or hard-wire `screw_m2p5_selftap` for `seat_d`**
  (~120, ~279, ~462): read the chosen board screw and `hole_column_d`.
- **Replay tests with pinned body volumes** (`TestReplayIter005`, the iteration 009 ligament-test volumes):
  the geometry changed on purpose (66 × 46 standoffs, Ø5.1 OD, Ø1.7 pilots, cavity −1.6).
- The infinite-lattice `grid_feasibility` unit tests (~1049–1070) stay as they are: the function remains the
  lattice sensor used by `grid_positions`.

Suite: the standard command plus `test_parts test_feature_graph test_assembly test_assembly_checks
test_no_hardcoding`. `test_no_hardcoding` must stay green: no new numeric literal in agent modules except
array indices.

## 6. Expected effect on the verdict (E1-01)

| Defect | After the delta (predicted, from part data) |
|---|---|
| G5 / L3.3.3.1 (w3) | pilot Ø1.7 (in 1.6–1.8) → PASS. Depth setpoint 5.1 ≥ 5.0 (L3.3.3.2) |
| L3.3.1.3 / L3.3.1.4 / L3.12.1.2 (w3) | standoffs on the HOLE datums: 66.0 × 46.0, offset 0 → PASS |
| L3.3.2.1 (w2) | OD = max(1.7 + 3.2, setpoint(5.0)) = 5.1 → PASS |
| L3.3.5.1 (w2) | column Ø7 → inner faces at Y −1.6 / 51.6 and X ≥ 71.6 near the holes → PASS by 0.1 |
| L3.1.3.1 (w2) | USB_MOUTH X = 5.79 − 1.37 − 1.3 = 3.12 → PASS (centre of [2.62, 3.62]) |
| L3.1.6.1 (w1) | Pico pins on grid columns 0–19, rows 5 and 12 (residual 0); jacks exempt → PASS |
| L3.12.2.1 (w1) | same datums as the judge; seat exemption Ø8 matches → expected PASS |
| USB opening (G3) | unchanged mechanism (plug envelope ∩ wall). The overmold underside is 1.4 above the board, so the plug passes over the board margin; `plug_refs` reports it |

Expected next verdict: **E1-01 MEETS** is reachable, conditional on the seeds (3 needed), and the agent's own
outcome becomes `verified`. The closed size should be about 84 × 64 × 25, under 90 × 70 × 35:

- The cavity in Y grows from −1.1..51.1 to −1.6..51.6, because the columns move out with the holes.
- The cavity in X goes from about −1.9..71.1 to −1.6..71.6, because the receptacle no longer overhangs −X.

Re-measure this after the build.

## 7. Risks and questions for Robin

- **Q8. Rubric versus requirements on the pilot.** The rubric's section 6 table still says pilot Ø2.0–2.2
  (the M2.5 value). requirements.md L2.3.3 and A9 say Ø1.6–1.8. Both judges flagged this and graded on
  requirements.md. Please reconcile the rubric.
- **Q9. variants.json is older than the owner decisions.** Its `about` and `grading_deltas` still say
  "corner holes 3.0 mm at 2.5 mm from each edge" and give flush USB-mouth ranges (V1: X in [−1.8, 0.5];
  V2: [−1.8, −0.8]).
  - With C1 and C4, the variants get the measured board's holes (2.0, Ø2.0) and a Pico on grid column 0.
    The mouth is then about 3.0 inside the edge.
  - The loop does not change a judge reference without your confirmation (7.9). Until variants.json is
    updated, variant judges should apply OWNER_DECISIONS item 1 to every perfboard, or V1–V3 will be graded
    against a board the catalogue no longer models.
  - If you want the variants to keep a *different* board (2.5 / Ø3.0), say so. A second catalogue board
    (`perfboard_generic`) plus a request-evidence rule could select it, but the variant request texts give no
    words that tell the two boards apart today.
- **Q10. M2.5-era numbers in requirements.md.** V-HOLE-KO and V-SEAT are Ø7.0. The V-HOLE-KO core is Ø2.9,
  which is the M2.5 clearance hole. With an M2 screw, head plus driver room is Ø6.0.
  - The delta keeps Ø7 by declaring it as the board's mounting-hole keep-out in part.json (C1/C3). It is not
    a constant in code.
  - If Ø7 was only the old M2.5 head plus 2 × 1.0, tell us. The board keep-out can then drop, and the box
    shrinks by about 1 mm per axis.
- **Risk: a 2-D snap that is blocked by collisions.** On E1-01 the Pico ends at X about 55.3 and the jacks
  start at X 58.0, so there is no collision. If a variant is blocked, the typed `blocked` conflict says so,
  and the part stays at its spread pose. No silent fallback.
- **Risk: test volume.** About 13 new tests, plus the changed fixtures above. The suite runs in about
  800 s. No Ollama is used.
