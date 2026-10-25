# Iteration 006: gap analysis and delta design

Tooling note: the claude-context MCP server failed to connect in this session ("configured MCP servers
failed to connect: claude-context"). I read files at known paths and used targeted grep only
(`assembly.py`, `layout.py`, `design_rules.json`, part.json files, judge JSON).

## 0. What the run tells us

- Both judges: DOES NOT MEET / CORRECT, 133/134 = 0.993, every gate and every weight-3 L3 passes.
  Worst weight-3 normalised margin is 0.20, unchanged.
- Iteration 005's change worked: L3.12.2.1 (self-report agreement) now passes for both judges
  ("agent's numbers agree with mine within 0.005 mm"). Nothing regressed.
- The only failing L3 is **L3.1.6.1** (weight 1, grid conformance). It has two halves:
  - the Pico header pins are 1.130 mm off the grid;
  - the jack pins are UNVERIFIED, which the rubric counts as FAIL.
- **Process deviation (important for the loop, not the agent).** The Run step ran **seed 0 again,
  not SEED = 5**, and did **not run V1, V2 or V3**, although RUN.md 3.1 and the iteration 005 ledger
  entry asked for both. `iter_006/target_s0/*/llm/` is byte-identical to `iter_005/target_s0/*/llm/`
  (`diff -rq` is empty). So this iteration measured the same controller trajectory again. It gave no
  new information about seed robustness or about the variants, and convergence needs both
  (ARCHITECTURE.md 8). See section 4.

## 1. Defects → root causes

| Defect | Where | Root cause | Agent gap? |
|---|---|---|---|
| D1: Pico pins 1.130 mm off grid in X (L3.1.6.1, w1). Both judges. | `layout.Placer.grid_shift` (tangential-only snap, 7.5); perfboard `grid.origin` = hole 1 | **RC-601: requirement conflict.** L2.1.3 holds the USB mouth in [-1.8, -0.8], which puts pin 1 at X in [0.87, 1.87]. The hole-1 grid needs X ≡ 2.50 (mod 2.54) ± 0.15. The best residual any placement can reach is 0.63. The agent already reports this as a typed conflict (`assembly.conflicts`, `flush_to_edge`). Both judges independently say "changing the agent cannot fix it". | No (Robin). See 1.1 for new evidence from the photo. |
| D2: jack pins UNVERIFIED (L3.1.6.1). Both judges. | `parts/jack_3p5_pj320a/part.json` has no `PINS` datum | **RC-602: catalogue data gap.** The agent code already reads a `PINS` datum (iteration 004 C4). Only the data is missing. | Data only (C1) |
| D2′: once the pins exist, the agent's sensor cannot tell an *unplaceable* pin pattern from a *placement* conflict. It also snaps by the first pin, not the worst. | `layout.Placer.grid_shift` (snaps `pins[0]`); `assembly.grid_check` (only knows `flush_to_edge`) | **RC-603: missing error-signal type.** `grid_conformance` has one conflict kind (normal to the edge). It never computes the best residual the part's own pin pattern can reach at *any* position. For a pattern that is not on a 2.54 lattice (see 1.2), it would wrongly report "move it off flush by x mm", which is a fix that does not exist. | Yes (C2) |
| O1: pilot depth 5.00, boss pilot depth 6.00, boss OD 6.00 and lip engagement 2.00 each sit exactly on their limits. Judge 2 says "any print shrinkage or a 0.1 mm rounding change flips these"; iteration 005's judges said the same. | `assembly.DeriveFeatures`: `standoff_k_pilot.depth = fastener.board.min_engagement`, `boss_k.d = max(fastener.lid.min_boss_od, …)`, `boss_k_pilot.depth = fastener.lid.min_engagement`, `lid_lip` and split use `rules.lip_engagement` | **RC-604: setpoint-in-band rule only half applied.** Rule 7.7 put `design_margin` on one-sided *clearances* only. Every other one-sided *minimum* is derived exactly at its limit. These are weight-2/1 L3s (L3.3.3.2, L2.7.3, L3.7.2.2), so a tessellation or rounding change can flip MEETS on another seed. | Yes (C3) |
| O2: the literal rubric 3.4 end-wall slab also catches the four blind corner-boss pilots. Both judges *chose* to count them as screw holes. A literal judge would fail L3.5.3.1 and L3.6.3.1 (w2 each: -X 3 regions, +X 4). | `assembly.build_plan` `apertures_<side>`: the slab spans only the cavity's tangential range (7.5 "corners belong to the perpendicular walls") | **RC-605: the sensor disagrees with the rubric recipe** (the lesson of 7.8, here for apertures). The agent counts openings in a smaller slab than the judge. It never sees the blind regions, so it cannot report or classify them. | Yes (C4) |
| O3: no render shows the base with the lid off, so the standoffs and lip cannot be seen (judge 1). The USB rectangle is hard to see in `model_left.png` (judge 2). | `RenderViews` renders only `views.scad` (closed) and `ghost.scad` | **RC-606: missing evidence view.** | Yes, small (C5) |

### 1.1 New evidence on RC-601 (for Robin, not for agent code)

I measured the photo (`perfboard_photo.png`, crop of the board, about 22 px/mm after scaling):

- The board has **24 columns (silk A–X) × 18 rows (silk 1–18)**.
- The array looks **centred on the outline**: about 5.8 mm and 5.7 mm from the first and last
  column to the short edges. That matches (70 − 23 × 2.54)/2 = 5.79.
- The corner holes are about 1.8–1.9 mm in from the edges. A7 already says "some boards have Ø2.0
  holes 2.0 in".
- So the grid is probably **not** registered to hole 1, which the iteration 001 catalogue assumed.
  requirements.md never defines the grid origin, and judge 1 noted this.

With a centred 24 × 18 lattice the grid is X ≡ 0.71, Y ≡ 0.87 (mod 2.54):

- **Y:** the Pico rows at 16.11 and 33.89 land exactly on the grid with the Pico centred.
- **X:** the residual at flush is 0.66. The best inside the L2.1.3 band is **0.16 at a 0.5 mm
  overhang**, with the USB mouth at −1.80. That passes only within ε (0.15 + 0.02), and with
  L3.1.3.1 also at its limit.

So even the evidence-based registration leaves a zero-margin conflict. **I do not change the
catalogue grid in this delta.** It would change the judges' reference without Robin's A7
confirmation (requirements.md: "when Robin confirms A3–A7, the catalogue is updated"). It would also
not produce a robust pass. This goes into the Robin questions (section 5).

### 1.2 The PJ-320A pin pattern is not on a 2.54 lattice

A secondary source (an OpenSCAD model of the PJ-320A found by web search; not yet checked against
the LCSC C18438 drawing) gives these footprint pins: (3.2, 2.3), (6.2, 2.3), (10.2, 2.3) and
(11.3, −2.3).

- The spacings are 3.0, 4.0 and 4.6 mm, none of which is a multiple of 2.54.
- A brute-force minimax over all plan translations (0.005 mm step) gives a **best residual of
  0.60 mm**, 4× the 0.15 limit, wherever the jack is placed.

If the datasheet confirms these values, the jack half of L3.1.6.1 is **infeasible for this part on any
2.54 perfboard**. That is a second, intrinsic requirement/catalogue conflict. The only fixes are a
jack whose pins are on 0.1 in, or Robin relaxing L2.1.6 for the jacks (hobbyists bend or drill these
legs). C1 and C2 make the agent *measure and say this*, instead of leaving it UNVERIFIED.

**Consequence for the loop:** E1-01 cannot reach MEETS through agent changes while RC-601 and
(probably) the jack pattern stand. The agent work below is what still moves the error signal:

- turn UNVERIFIED into a measured, correctly typed conflict;
- harden the zero-margin passes, so MEETS holds on 3 seeds once Robin decides;
- make the aperture sensor agree with the literal rubric;
- make the Run step produce variant and seed evidence.

None of this repeats a failed idea. Iterations 004 and 005 deliberately left L3.1.6.1 to Robin, and
that stays.

## 2. Delta (implementable in one pass; no cad_agent.py / cascade.py / cad_checks.py change)

### C1 (RC-602): jack footprint pins as catalogue data

- **File:** `benchmarks/enclosure/parts/jack_3p5_pj320a/part.json` only.
- **Change:**
  - Add a `PINS` datum: `{"kind": "axis_list", "dir": [0, 0, -1], "at": [[x, y, 0], …]}`, in the part
    frame (origin at the body min corner, mouth on +X).
  - Add a `self_checks` entry that recomputes one pin spacing from the datasheet.
  - Change `notes` and `source` to cite the drawing.
- **Hard rule:** the implementer must read the values off a datasheet drawing. Try the LCSC C18438
  PDF and the vendor PDF linked from evelta / tayda product pages.
  - The secondary-source numbers in 1.2 may be used **only if** a datasheet confirms them. Map their
    frame first: the source's x origin and its ±2.3 y offsets are about the body centreline.
  - If no drawing can be read, do not add `PINS`, and record that in the ledger. C2 still lands and
    still reports `no_pin_data`.
- **Tests:**
  - `test_parts`: the jack loads, `PINS` count = 4, the pins lie inside the body plan ± leg
    overhang, and the self_check passes.
  - Existing jack tests stay unchanged.
- **Verdict effect:** the judges can measure the jack residual. L3.1.6.1's jack half goes from
  UNVERIFIED to a measured FAIL (about 0.6 mm), with the agent naming the cause. The score does not
  change, but the error is now observable.

### C2 (RC-603): grid feasibility, minimax snap, typed conflict kinds

The sensor change. It is generic: it uses only the part's pin datums and the board grid's pitch.

- **`layout.py`**
  - `grid_feasibility(pins_xy, pitch, free_axes) -> dict`:
    - `best_any`: the minimax over plan translations of the worst pin-to-lattice distance, with the
      shift. Search the torus [0, p)² on a coarse grid of `rules.grid_search_step` (new rule,
      generic, e.g. pitch/254), refine locally, vectorised in numpy.
    - `best_free`: the same, restricted to `free_axes` (the tangent of the part's edge).
    - `normal_needed`: the smallest |shift| normal to the edge that brings the free-axis minimax
      ≤ `grid_residual_max`. It is `None` when `best_any` > the limit.
  - `Placer.grid_shift`: snap by the **minimax** shift along the tangent (bounded by pitch/2), not by
    `pins[0]`. The result is identical for a part whose pins are all on one lattice (the Pico), so
    nothing moves for E1-01's Pico.
  - `Placer.grid_report`: per part, add `best_any`, `best_free`, `normal_needed` and a `kind`:
    - `"ok"` when residual ≤ limit;
    - `"pin_pattern"` when `best_any` > limit (no placement can pass);
    - `"flush_to_edge"` when it fits somewhere but not at the flush normal position;
    - `"tangential"` otherwise, which is a placement bug: the snap failed.
- **`assembly.grid_check`**
  - Build each conflict from `kind`:
    - `pin_pattern`: "the part's own pin pattern cannot meet the board grid at any position (best
      {best_any:.3f} mm > {limit}); a catalogue or requirement question";
    - `flush_to_edge`: today's text, with `normal_needed` in place of `normal_fix`.
  - Keep `competing_rule` = the kind.
  - `no_pin_data` parts stay a failure, with `kind: "no_pin_data"`.
  - `finalize` already copies conflicts into `assembly.conflicts`. Add `kind` to each entry.
- **`design_rules.json`:** add `grid_search_step` with a source line. It is generic, not a target
  number.
- **Tests (fake LLMs / fixtures, no Ollama):**
  - `test_parts` or new `TestGridFeasibility` in `test_assembly.py`:
    1. Pins on an exact lattice offset by an arbitrary vector: `best_any` ≤ 1e-6, and the shift
       recovers the offset mod p.
    2. A test-only fixture pattern with spacings 3.0 / 4.0 (fixture numbers in the test, not in
       agent code): `best_any` equals a brute-force reference computed in the test within 0.01,
       and `kind == "pin_pattern"`.
    3. An on-lattice pattern with a normal offset of 0.4·p and a free tangent: `kind ==
       "flush_to_edge"`, and `normal_needed` = 0.4·p − limit (or the wrap-around value) within 1e-6.
    4. Minimax snap: for a fixture `PINS` part whose first pin is the outlier, the snapped worst
       residual is strictly less than with first-pin snapping and equals `best_free`.
  - `TestEndToEnd.test_grid_conflict_is_reported_not_hidden`: extend it to assert `kind` per conflict,
    recomputed in the test from layout.json and part data, never from `layout.Placer`. E1-01's Pico is
    `flush_to_edge`. If C1 landed, each jack is `pin_pattern`; otherwise both are `no_pin_data`.
  - The `TestReplayIter004` / `TestReplayIter005` assertions keep "only `grid_conformance` fails".
    If C1 lands, the conflict count rises from 1 to 1 + number of jacks. Change those asserts with a
    one-line ledger justification (the new pin data makes the jacks measurable).
- **Verdict effect:** none on the score. The agent's self-report then states the same two-part
  infeasibility the judges derived by hand, with numbers. That keeps L3.12.2.1 and the matrix honest,
  and gives the loop the typed signal "stop: Robin".

### C3 (RC-604): design margin on every one-sided minimum (completes 7.7)

- **`assembly.DeriveFeatures`** (lines around 1055–1100):
  - `standoff_k_pilot.depth` = `fastener.board.min_engagement + rules.design_margin` (and its `h`,
    pose z alike).
  - `boss_k_pilot.depth` = `fastener.lid.min_engagement + rules.design_margin`.
  - `boss_k.d` = `max(fastener.lid.min_boss_od + rules.design_margin, fastener.lid.pilot_diameter + 2*rules.boss_wall_min)`.
    Do the same for the standoff OD term `fastener.board.min_boss_od`.
  - Lip: introduce one expression `rules.lip_engagement + rules.design_margin` (name it in the lip
    node's params as `engagement`). Use it in `lid_lip.z`, `lid_lip.bottom`, the lip pose, the split
    term `cavity.z1 + …` and `boss_k_lip_notch`, so the lip bottom stays at `cavity.z1`. V-KO-TOP's
    0.100 is unchanged and the box grows 0.1 mm in Z.
  - The pilot-floor check (`pilot_depth_<standoff>`) keeps its limit and recomputes automatically.
- **Write it as one generic helper** `setpoint(limit_expr) -> f"{limit_expr} + rules.design_margin"`,
  used at every one-sided-minimum derivation. Its docstring lists the roles. Checks keep the limits.
- **New agent checks** (so the agent senses what the judges flagged):
  - `pilot_engagement_<n>` (pilot depth ≥ fastener min_engagement) for standoffs and bosses;
  - `boss_od_<n>` (≥ min_boss_od);
  - `lip_engagement` (≥ rules.lip_engagement).
  These are plain value/limit plan entries like `pilot_depth`, measured on the resolved graph. Where
  `measure_package` already has a recipe, also measure them on the delivered STLs (ray-cast depth
  down the pilot axis; mid-height slice for the OD).
- **Tests:**
  - `TestDeriveFeatures.test_one_sided_minimums_have_the_design_margin`: for E1-01 and V1, each new
    value = limit + design_margin within 1e-6. With `design_margin = 0` they equal the limits, and the
    split moves by exactly design_margin.
  - `test_clearances_have_the_design_margin` keeps passing.
  - The new checks fail on a mutant with the margin set to −0.2 (non-vacuity).
  - The E1-01 offline result: bbox Z grows by 0.1 (24.60 → 24.70); every other clearance figure is
    unchanged.
  - `TestReplayIter00x` volume-equality asserts against the old self_report will change (geometry
    changed on purpose). Replace them with the new recomputed values, with a ledger line.
- **Verdict effect:** removes four exact-limit passes (L3.3.3.2, L2.7.3 depth and OD, L3.7.2.2), so
  MEETS will not flip on a rounding change across the 3 seeds that convergence needs.

### C4 (RC-605): aperture slabs follow the rubric recipe; regions are classified

- **`assembly.build_plan` / `assembly_checks`:**
  - The end-wall slab for `apertures_<side>` becomes the rubric 3.4 slab: inner to outer face over
    the wall's **full** tangential and Z extent, inset by `measure_tol` from the two faces only.
    The Z extent spans base ∪ lid when closed.
  - `aperture_count` decomposes the slab minus the bodies as before (regions ≥ 1 mm³). It then
    classifies each region:
    - `through`: the region touches both the inner and the outer face plane (test the region's
      bbox against the two planes, then confirm with a manifold intersection with thin face slices);
    - `blind`: anything else. Record the graph node ids of the `pilot` / `screw_hole` cuts that the
      region intersects.
  - The pass/fail value counts `through` regions only. That is the requirement's intent ("openings
    other than … screw holes", L1.8).
  - `evidence` lists every region with its class, bbox and node ids. `self_report.json` gains
    `apertures[<side>] = {through: n, blind: [{nodes, bbox}]}`.
- **Tests:**
  - `test_assembly_checks`: a synthetic wall with one through-hole and one blind pocket in the slab
    gives through = 1, blind = 1 (with the pocket's node id). Moving the pocket to the outside of the
    slab gives blind = 0.
  - `TestEndToEnd`: E1-01's -X wall gives through 1 and blind = the corner pilots and lid holes
    found by the literal recipe. +X gives through 2.
  - An independent test helper applies rubric 3.4 literally (full-extent slab, no classification).
    Its total region count equals the agent's through + blind.
- **Verdict effect:** the agent's sensor now sees what a literal judge sees, and the self-report
  gives the classification, so a literal judge has the agent's evidence. Geometry is unchanged. If
  a later iteration wants zero blind regions in the end-wall slabs, it is a closure decision for the
  middle loop (section 4.3), not part of this delta.

### C5 (RC-606): lid-off evidence view

- **`assembly.WritePackage`:** also write `open.scad` (the base only, closed pose, references as
  ghosts, lid omitted).
- **`RenderViews`:** render it with stem `open` and only the `iso` and `top` views, so
  `views/open_iso.png` and `views/open_top.png` exist.
- **Optional:** in `views_scad`, colour the cut faces (OpenSCAD's cut colour already) and add a
  `front_left` iso view, so the -X opening is visible.
- **Tests:** the package manifest test lists `views/open_iso.png` when OpenSCAD is present (skipped
  otherwise), and `open.scad` parses and contains no `lid` body module.
- **Verdict effect:** none on the score. It removes an observation and lets the judges see the
  standoffs and lip.

### Not in this delta (and why)

- **Changing the perfboard grid registration** (1.1): this needs Robin's A7 decision, and even then
  the residual is 0.16 at a band edge.
- **Moving the Pico 0.5 mm off flush:** the agent never receives L2.1.3's ±0.5 band. Copying a
  judge-side number into rules is forbidden (7.7).
- **M9–M11:** no defect in this run needs them. They become the next milestone once the variants
  produce real defects (section 4).

## 3. Expected outcome after the delta (offline, scripted controller)

- E1-01: rc 3, only `grid_conformance` failing.
  - Conflicts: Pico `flush_to_edge` (residual 1.130, normal_needed ≈ 0.98 under the hole-1 grid).
  - If C1 lands, each jack is `pin_pattern` (best ≈ 0.60).
- Bbox 82.95 × 62.15 × 24.70.
- New checks: `pilot_engagement_*` margin 0.1, `boss_od_*` 0.1, `lip_engagement` 0.1.
- `apertures_-X` through 1 (blind 4: 2 pilots + 2 lid holes per the judges' boxes),
  `apertures_+X` through 2.
- Judges: still DOES NOT MEET / CORRECT, 133/134. L3.1.6.1 now has both halves measured and
  explained by the agent. The four near-limit observations are gone.

## 4. Run-step instructions for iteration 007 (process gap, not code)

1. Run **E1-01 with SEED = 5** (not 0). The seed-0 trajectory has been measured twice, with
   identical transcripts.
2. Then run **V1, V2 and V3** (RUN.md 3.1, `run_one`). They have never been run by the real
   controller, and convergence needs each of them CORRECT. Their defects are now the
   highest-information error signal the loop can get.
3. Judges should grade L3.1.6.1 with the agent's `assembly.conflicts` in view, and report the
   conflict kinds.

## 5. Questions for Robin (carried over; 2 and 3 updated with new evidence)

1. L3.12.1.1's 20–200 mm per-axis band fails any flat lid (4.4 mm). Should it be a units check on the
   largest axis?
2. **Grid registration.** Your photo shows a 24 × 18 array that appears centred on the 70 × 50 outline
   (margins about 5.8 mm), not registered to the corner holes. Please confirm, or measure hole 1 to the
   first grid column. Even centred, the Pico can reach 0.16 mm only at a 0.5 mm overhang (the edge of
   L2.1.3). Do you want L2.1.3's band widened, L2.1.6's tolerance raised to about 0.25 mm, or the Pico
   allowed to sit inboard?
3. **Jack pins.** The PJ-320A's legs (spacings about 3.0 / 4.0 / 4.6 mm) do not fit a 2.54 grid at any
   position (best about 0.60 mm). Should L2.1.6 exclude the jacks (bent legs or drilled holes), or do
   you use a different jack whose footprint is on 0.1 in?
4. Should L3.11.1.1's V-INSTALL exclude the V-SEAT contact?
5. Should blind screw pilots inside an end-wall slab count as screw holes for L3.5.3.1 and L3.6.3.1?
   Both judges assumed yes.
