# Iteration 002: gap analysis and delta design

Inputs:
- the judge verdicts `target_s0/judge_1.json` and `judge_2.json` (E1-01, seed 0, `--mode cascade`, rc 124 after 5415 s);
- the assembly smoke arm `target_asm_s0/` (rc 1, `not implemented: parse_spec`, 0 s);
- ARCHITECTURE.md, LEDGER.md (iteration 001: M0 to M3 implemented, review pending), RUN.md;
- the code at `iter_002/code_sha1.txt`: `assembly.py`, `parts.py`, `feature_graph.py`, `design_rules.json`, the 11 part files, and the `cad_agent.main` mode switch.

Tooling note: the claude-context MCP server failed to connect again in this session. ToolSearch
reported "configured MCP servers failed to connect: claude-context". So I read files by their
known paths and used targeted `grep` only for the line anchors quoted below.

## 1. Verdict in one line

Both judges: **WRONG**. All six gates G0 to G5 fail and all 12 L1s fail. The judged package is
byte-identical to iter_001's 90 × 74 × 4 slab.

That result was expected, and it says nothing new about the agent:

- **What was judged.** The judged arm (`target`) is still the cascade baseline, whose code path
  has not changed since iteration 001.
- **The new code was never judged.** It lives in `--mode assembly`, which stops at
  `NotImplementedStage("parse_spec")` and writes no package (see ledger iteration 001, "Notes for
  Robin").
- **Why there is no movement.** Every defect in this verdict traces to root causes RC1 to RC6 of
  iteration 001. M0 to M3 fixed their *representation* half. Their *pipeline* half does not exist
  yet: nothing turns a request into a feature graph and nothing writes a package. That missing
  pipeline is what blocks progress.

## 2. Root causes (defects grouped by shared cause)

| RC | Root cause in the agent / the loop | Where in code | Defects it explains |
|---|---|---|---|
| **RC7 (new, loop control)** | **The error signal measures the wrong plant.** RUN.md §3.1/§3.2 make the cascade run the judged `target` "until M13". Assembly mode is only a smoke arm that produces no package. The judges therefore re-measure a frozen code path, so the loop's error is constant (open loop) no matter what the delta changes. | `loop/RUN.md` §3.1, §3.1b ("Switch section 3.1 to this command only when the full tree runs end to end (M13)") | every defect, by construction; "byte-identical to iter_001" (judge 2) |
| **RC8 (pipeline missing: G0, L1.12)** | **Assembly mode has no stage after LoadRules.** `build_assembly_tree` is `LoadCatalog → LoadRules → NotImplementedStage("parse_spec")`, and `finalize` raises `NotImplementedError`. No code writes `base.stl`, `lid.stl`, `layout.json` or `self_report.json`. | `assembly.py` `build_assembly_tree`, `finalize`; there is no package writer (M12) | L3.12.1.1 (G0), L3.12.1.2, L3.12.2.1 |
| **RC9 (no derivation of features from contents: G1, G2, G5, L1.4, L1.8, L1.10)** | **Nothing generates body, add and cut nodes from the contents.** M2 and M3 can *express* `shell`, standoffs, pilots, lids and port cuts as nodes with expressions, but no rule builds them: there is no CavityFromContents, no MountHoleToStandoff, no LidToFastening and no archetype generator (M8). The size leak (RC4) is closed only once the cavity size is an expression of the reference bboxes plus `spec` clearances. | absent: `assembly.py` has no DeriveFeatures; `feature_graph.py` has the primitives (`shell`, `tube`, `cylinder`, `box`) but no generator | L3.2.x, 3.4.x (no cavity); 3.3.x (no standoffs or pilots); 3.7.1.1, 3.9.2.1 (no second body); 3.7.2 and 3.7.3 (no lip or bosses); 3.8.x (no walls); 3.10.1.1 (bbox from limits, not from contents) |
| **RC10 (no placement of the references: L1.1, and every port position)** | **There is no ArrangeContents and there are no envelopes.** Nothing poses the Pico, headers and jacks on the board, so no datums exist in the world frame: no USB_MOUTH, jack AXIS or board HOLE axes, and no plug sweep to cut along (M4, M7). | absent: no `parts.envelopes`; no arrangement in `assembly.py` | L3.1.1.1 (no layout declared); L3.5.x (G3) and L3.6.x (G4): no opening can be placed without a posed mouth and a plug envelope |
| **RC11 (no controller interface: ParseSpec, contents)** | **The LLM is never asked anything in assembly mode.** No stage reads the request numbers (70 × 50, 12 / 4, 0.5, 1.5, 2–4, 90 × 70 × 35) into typed `spec` slots, and no stage maps the request words onto catalogue ids or connector edges. | absent (M6 / ParseSpec-lite and CatalogLookup) | indirectly all of the above: the derivation needs `spec` and contents |
| **RC12 (no sensor for the new defects)** | **There are no `separable`, `inside`, `clear_of`, `aperture_count` or `seated` checks.** Even if a package were written, the agent could not tell that it fails G1, G2, G3, G4 or G5. It could not write a truthful self-report either (L3.12.2.1). | absent: `assembly_checks.py` does not exist (M5) | L3.12.2.1 (self-report contradicts the geometry); every G-gate failure is invisible to the agent |

RC1 to RC6 are already closed at the type level by iteration 001 and are not repeated here. The
cascade's own failures (the translate_L1.1 saturation after 30 iterations, about 1883 LLM calls)
are not addressed. Cascade is not the vehicle (ARCHITECTURE.md §1), and Robin's working-tree
×10 caps stay untouched.

**Oscillation and repetition check against LEDGER.md.** Iteration 001 tried exactly one idea: the
foundation M0 to M3. It worked as designed (248/248 tests) and planned this skeleton as its §9.
Nothing here repeats a failed idea or reverses an earlier change.

## 3. What blocks progress, and the choice for this iteration

The judges' signal can move off "WRONG, G0 to G5 fail" only when two things are true: assembly
mode writes a two-body package, **and** that package is what gets judged.

This iteration implements the **walking skeleton** of ARCHITECTURE.md §7.1, step 2, which is
iteration 001's plan. It is wired as a thin tree:

```
cad_assembly (Sequence, memory=True)
├── LoadCatalog          (exists)
├── LoadRules            (exists)
├── ParseSpec            C4  LLM maps typed slots onto numbers Python extracted from the text (enum); defaults from rules, flagged
├── Contents             C4  Python proposes catalogue candidates (Catalog.lookup); LLM gives quantity + exposed per candidate (enums)
├── ChooseStack          C4  LLM enum among part.mount.stack_options
├── ArrangeContents      C5  LLM: edge enum per connector item; Python: mm poses, flush-to-edge, spread, grid snap, interference
│   └── ConfirmArrangement   Python renders the arrangement in words; LLM p_yes; on "no", the next alternative (finite set)
├── BuildEnvelopes       C1  plug sweeps, keep-outs, seat / driver columns (from datums only)
├── ChooseArchetype      C6  Python lists feasible archetypes; skeleton has one (tray+lid, screws) -> recorded as rule choice, no LLM call
├── DeriveFeatures       C6  cavity from contents, base shell, standoffs+pilots, port cuts, lid plate + lip, corner pilaster bosses + lid holes
├── Build                C7  resolve graph, manifold solids per body, OpenSCAD compile per body (manifold fallback)
├── Verify               C2  rule-derived checks (subset) on manifold AND re-measured on delivered STLs; never fails the tree
├── RenderViews          C7  views/model_* (bodies only), views/ghost_* (bodies + references)
└── WritePackage         C7  base/lid .stl/.scad, model.scad, layout.json, self_report.json, feature_graph.json, checks.json, matrix
finalize(): outcome verified (all checks pass) | unsatisfied (exit 3)
```

C0, a loop-control change to RUN.md, makes this assembly run the judged target.

Deferred, with reasons:

| Deferred item | Reason |
|---|---|
| M9 Solve inner loop | Every derived number is already an expression that is correct by construction. Solve becomes necessary when a check fails numerically, and Verify will now report exactly that. |
| M10 translation of L1s into checks | The rule-derived checks cover the gates. Translated checks refine the weight-1 and weight-2 L3s. |
| M11 middle loop | ConfirmArrangement is its smallest useful piece. |
| `printable`, `min_wall`, `gap`, `pitch`, `install_sweep`, print views | Next iteration. |
| sliding-lid and snap archetypes | Next iteration. |
| M0b | No defect points at it. |

## 4. Change C0: make the error signal measure the plant being built (RC7)

The delta edits `loop/RUN.md`; implementers keep that file current.

- **§3.1 (the judged runs).** `run_one` uses `--mode assembly` with `--parts` and `--rules`, as
  in §3.2, writing to `$ITER/${name}_s$SEED`. That run is the judged `target`.
- **§3.1b.** Rename it the *cascade reference arm*. It is run only when `cascade.py`,
  `cad_checks.py` or cascade-relevant parts of `cad_agent.py` changed, or when the seed is not 0.
  Otherwise the judges record "unchanged, see iter_001". This saves 90 minutes of Ollama time
  per iteration.
- **§3.2.** Replace the "switch at M13" sentence with this rule: assembly mode is the judged
  target from iteration 003 on, the first Run that has a package writer. A run that ends with
  `not implemented: <stage>` is judged as G0 FAIL ("no package"), with the stage named. It is
  never silently replaced by the cascade.
- **§4 table.** Move the "After assembly mode" column to "Today".
- **New §3.4, Run-step self-check.** After each assembly run, check that these files exist under
  `$pkg`: `base.stl`, `lid.stl`, `layout.json` and `self_report.json`. List any that are missing
  in `runs.jsonl` as `"missing": [...]`.
- **Test.** A RUN.md snippet cannot be tested in unittest, and the implementer must not run Ollama.
  No fake-LLM production flag is added. The proof is in two parts, and the ledger records both:
  - the offline end-to-end unittest (C8) runs the same `cad_agent.main` argv as the new §3.1;
  - `bash -n` passes on the extracted snippet.

## 5. Change C1: envelopes from datums (M4 subset) (RC10)

**File:** `parts.py`. Add the functions below. Each returns `feature_graph.Node`s of
`kind="envelope"` (never printed). Where the primitive set lacks a shape, it returns the
`(primitive, params, pose)` spec instead.

| Function | Builds |
|---|---|
| `plug_sweep(conn_world, plug_inst, clearance, travel)` | The plug at full mate: its tip is at the mouth minus `insert_depth` along the mating direction, and its PLUG_AXIS is aligned with the connector's AXIS dir. Each plug geometry primitive is placed by the part's own `at`/`dir`, and the overmold primitive is extended by `travel` along the axis. `travel` = `rules.plug_travel` (new rule: 40 mm, "past any wall"). Returns one envelope node per plug primitive, with role `plug_shell` / `plug_overmold`. |
| `board_keepout(board_world, above, below, seats)` | V-KO-TOP: board footprint, Z 0 to `above`. V-KO-BOT: board footprint, from BOTTOM down `below`. Each is a `box` envelope. The V-SEAT columns are separate `cylinder` envelopes, which checks subtract. |
| `column(axis_datum, i, diameter, z_from, z_to, role)` | V-SEAT-k, V-HOLE-KO-k and V-DRIVER-k as cylinders along the axis. Diameters come from rules: `seat_diameter = board screw head_diameter + 2*rules.driver_clearance` and `driver_diameter`. New rules, with sources. |
| `content_envelope(ref_nodes)` | The AABB of the module plus its stack parts (V-PICO). |

All lengths come from `spec` (`keepout_above`, `keepout_below`, `board_clearance`), `rules`
(`plug_to_opening`, `plug_travel`, `driver_clearance`) or part data. There are no literals.

**Tests (`test_parts.py`, new class `TestEnvelopes`).** These use a fixture board with
`width`/`depth` parsed from the E1-01 request and the parts posed by C5's placer with scripted
edges.

- **V-USB-PLUG.** The shell box spans from the mouth plus `insert_depth` inside to the mouth minus
  `exposed_shell` outside, along USB_AXIS. The overmold starts there and runs `overmold_length + travel`.
  Both bboxes equal the hand formula from `plug_microusb_b/part.json` within 1e-6.
- **V-JACK-PLUG-k.** Cylinder shaft and overmold diameters are read from the part. The axis equals
  the jack AXIS (R8: datum distance ≤ 0.01).
- **Keep-outs.** V-KO-TOP and V-KO-BOT bboxes equal the board footprint × [0, above] and
  [−t − below, −t].
- **Rotation.** A connector rotated to face +Y gives a sweep whose bbox runs along +Y. This guards
  against an axis-specific implementation.

## 6. Change C2: the sensor subset (M5 subset) (RC12)

**File:** a new `assembly_checks.py`. Every check returns `cad_checks.CheckResult` with `passed`,
a signed `margin`, the raw value, `depends_on` and `evidence` (bbox, volume). The recipes follow
rubric §3.2 to §3.4 exactly: same tolerance and same decompose-based shell count.

| Check | Implementation |
|---|---|
| `separable(bodies)` | `len(decompose()) == 1` per body, `status() == NoError`, and the pairwise intersection volume ≤ `rules.overlap_max` (new rule: 1.0 mm³, source requirements L3.7.1.2). |
| `clear_of(bodies, volume, clearance, minus=())` | Penetration volume first. If it is 0, the minimum gap is measured as `volume.min_gap(body, clearance + 1)` (manifold3d 3.x API; if that is absent, use a trimesh signed-distance fallback on volume samples, as in rubric §3.2). Margin = `(gap − clearance) / tol`. |
| `inside(volume, bodies, clearance)` | Cavity = `hull(ALL) − ALL`, keeping the component that contains the volume centroid. Measures the volume outside the cavity, then `clear_of` to the bodies. |
| `aperture_count(bodies, wall_slab, n)` | The slab between a wall's inner and outer face planes, spanning the wall's full extent, minus the bodies, then `decompose()`. Margin = n − count. |
| `aperture_oversize(apertures, envelope, max_excess)` | The per-side excess of each aperture bbox over the plug envelope's cross-section. |
| `seated(board_bottom_plane, standoff_tops, hole_axes, pilot_axes)` | Gap ≤ 0.10 and least-squares axis residual ≤ 0.25. Both limits are read from the new rules `seat_gap_max` and `seat_axis_residual_max`. |
| `bbox_within(bodies, max_xyz)` | Limits come from `spec.max_x/y/z`, plus "X > Y" when `spec.longest_along` is set. |
| `measure_package(pkg_dir, layout, graph)` | Loads `base.stl` and `lid.stl` with the rubric's load recipe (trimesh → manifold3d), rebuilds the references and envelopes from `layout.json` and the catalogue, and runs the checks above. Its output *is* `self_report.json`. |

**Tests (`test_assembly_checks.py`, new).** All use synthetic manifold3d solids with known answers.

- **Boundary tests.** `clear_of` passes at gap = c + 0.02 and fails at c − 0.02. The margin sign
  and magnitude are within 0.02 of the analytic value.
- **Penetration.** A penetrating cube gives a negative margin, and the evidence bbox equals the
  analytic intersection.
- **`separable`.** It fails for a fused pair (1 shell) and for a 2 mm³ overlap, and passes for two
  1-shell bodies.
- **Apertures.** A shell wall with 2 round cuts gives `aperture_count == 2`. A missing cut gives
  margin −1. A cut 1.6 mm bigger per side than the envelope fails `aperture_oversize` at max 1.5.
- **`seated`.** It fails when the tops are 0.2 mm low, and fails when one standoff is moved 0.3 mm.
- **Agreement.** `measure_package` on STLs written by `write_stl` gives the same numbers as the
  manifold measurement within 0.02 mm.

## 7. Change C3: the hard-coding guard follows the new code

`test_no_hardcoding.MODULES` already lists `assembly_checks.py`. Check that the scan runs on it
now that the file exists. A missing file must fail the test, not be skipped.

Two traps to note in the code:

- **Rotations.** Compute every `rot_z` from directions with
  `math.degrees(math.atan2(...))`. Never write the literal `90`/`180`. A quarter-turn literal
  would also be banned (90), and a computed angle is the generic form anyway.
- **Binary-STL header.** Keep using `STL_HEADER`.

## 8. Change C4: the thin controller interface (ParseSpec, Contents, ChooseStack) (RC11)

**File:** `assembly.py`. The LLM answers *only* enums that Python builds (Principle 1).

### ParseSpec

1. **Python extracts the number tokens.** `extract_numbers(texts)` scans the request plus every
   L1 text. It finds each number with its unit and the "a x b (x c)" groups. Each occurrence gets
   an id such as `n7`, plus a ≤ 120-character context quote and its source (`request` or `L1.4`).
   Every occurrence keeps its own id, so the two 70s in "70 x 50" and "90 x 70 x 35" stay
   separate.
2. **The slots are generic data.** Add a new `spec_slots` section to `design_rules.json`. Each
   slot has `name`, a plain-English `meaning`, `unit` and `default_rule`:
   - `board_width`, `board_depth`;
   - `keepout_above` (default rule `component_height_default`);
   - `keepout_below` (default rule `solder_side_default`);
   - `board_clearance` (default rule `board_to_wall`);
   - `opening_oversize_max`, `wall_min`, `wall_max`;
   - `max_x`, `max_y`, `max_z`.
3. **One schema-constrained call, voted.** The label is `assy_spec`. Each slot's enum is the
   number ids plus `"none"`. The call is sampled `VOTES` times, and each slot takes its majority
   independently (a small per-key tally next to `OllamaAgent.vote`).
4. **Gates.**
   - Number coverage holds by construction: the answer is an id.
   - Generic relations must hold, and a violation is a typed failure that triggers one re-ask
     with the violation named: `wall_min ≤ wall_max`, all values > 0, and the board size must
     equal the board part's `from_request` params.
   - A slot answered `none` takes its rules default. It is appended to `assumptions` and its
     provenance is recorded as `rules:<key>`.
5. **Write the spec.** `st.spec[name] = value` and `st.spec_provenance[name] =
   'request:"<quote>"'` or `'L1.4:"<quote>"'`.

### Contents

- **Candidates.** For each kind in `{board, module, connector, generic}`, Python takes the top-k
  `Catalog.lookup` candidates over the request text. Plugs and fasteners are never contents:
  plugs mate with connectors, and fasteners are chosen by the rules.
- **The LLM call.** Label `assy_contents`. For each candidate id, the LLM answers `quantity` (an
  enum from 0 to `rules.max_quantity`) and, when the part has `connectors`, `exposed` (yes/no).
- **Validation.** Exactly one board is required. If there is none, the stage returns FAILURE
  with a typed note. Board params come from `spec.board_width/depth`.

### ChooseStack

For each content item with `mount.stack_options`, label `assy_stack` asks for an enum over those
ids. Python words each option, for example "male pin headers (module 2.5 mm above the board)",
using the stack part's `STACK_TOP`. The choice is recorded with who made it (`llm`).

### Tests (`test_assembly.py`)

`ScriptedLLM` replies keyed by label, with E1-01 and V1 texts read from
`benchmarks/enclosure/enclosure.json` and `variants.json`.

- **Correct spec.** The right ids map to the right slots, and `spec` equals the request numbers
  with provenance.
- **Bad reply.** A reply naming an id that is not in the enum (schema violation) leaves the slot
  at its default, flags it as an assumption, and never yields an invented number.
- **Relation re-ask.** `wall_min > wall_max` triggers exactly one re-ask, visible in the labels.
- **Contents.** The contents are 1 perfboard, 1 rpi_pico2 and 2 jack_3p5_pj320a, with the
  exposed flags set. The candidates offered to the LLM contain no plug or fastener ids.
- **Silent request.** On a request with no keep-out numbers, the defaults come from rules and
  are flagged.

## 9. Change C5: ArrangeContents + ConfirmArrangement (M7 subset) (RC10, L1.1)

**Files:** `assembly.py` holds the stage. A new `layout.py`, or a section of `parts.py`, holds the
pure placement math. Either way it is added to `test_no_hardcoding.MODULES`.

### What the LLM decides

Label `assy_edge`: for each content item that has an exposed connector, an `edge` enum over the
board edges. Python words the edges from the board params, for example "the short (50 mm) end at
−X". The prompt quotes the request. The answer is voted.

### What Python does: generic placement rules

1. **Rotate.** `rot_z = atan2(edge normal) − atan2(connector axis xy)`.
2. **Flush to the edge.** The part's `size_of` geometry face on the connector side is flush with
   the board edge. Any overhanging connector geometry, such as the receptacle, then sits exactly
   at its catalogue overhang.
3. **Set Z.** Z = board TOP. A stacked module sits on its chosen stack part: module PCB_BOTTOM =
   stack STACK_TOP. Stack parts are placed at the module's `stack_pins` datums.
4. **Spread along the edge.**
   - The free span is the edge length minus the corner-hole keep-out columns (V-HOLE-KO, from C1).
   - Several items on one edge are spread with equal gaps over that span.
   - A single item is centred.
   - The spacing must be at least the plug-envelope width plus 2 × `plug_to_opening` plus
     `min_ligament`. If not, the result is a typed failure `ports_do_not_fit(edge, need, have)`.
5. **Snap to the grid.** When a part has pins and the board has a `grid`, Python shifts the part
   by at most pitch/2 so that its pins land on the grid.
6. **Interference.** For each pair of placed references, the intersection must be ≤ 0.01 mm³ (R7),
   and no part may intrude into a hole column. A 1-D shift along the edge resolves what it can.
   Anything left is a typed failure.
7. **Write the layout.** `st.layout[node_id] = {part, params, x, y, z, rot_z}` in the board frame.
   The references become `kind="reference"` nodes in `st.graph`.

### ConfirmArrangement: the cheapest closed-loop error signal on a discrete choice

Python renders the result in words, for example "Pico 2 micro-USB faces the −X short (50 mm) end;
jack ×2 face the +X short (50 mm) end". It asks `p_yes` with label `assy_confirm`: "does this
match the request?".

If p < 0.5:

1. Python enumerates the remaining edge assignments. This set is finite: (edges)^(items), and
   assignments that fail the placement rules are pruned before asking.
2. Python orders them by the LLM's own vote counts.
3. It tries the next one.

The search ends either confirmed or exhausted. Exhausted means FAILURE with a typed note, not a
cap.

### Tests

Scripted edges, no Ollama.

- **E1-01.** USB faces −X and the jacks +X. The asserted values are computed from part data in
  the test: the USB_AXIS world dir is (−1,0,0), the mouth x equals −`usb_overhang`, and the jack
  AXIS dirs are (+1,0,0). The jack spacing is at least the minimum. Pairwise interference is
  ≤ 0.01. No part lies in a hole column. The Pico pins are on the grid (residual ≤ 1e-6).
- **V1.** Two ports on one edge. The envelopes are disjoint and the spacing is at least the minimum.
- **V2.** Three jacks on a long side. They are spread, or `ports_do_not_fit` is raised when the
  board is shrunk in the test.
- **V3.** The socket stack raises the USB_MOUTH z by the difference of the stack heights.
- **Confirmation.** If the fake says "no" to the first assignment (both on −X), the next confirmed
  assignment is used, and the labels show one `assy_confirm` "no" followed by one "yes".

## 10. Change C6: ChooseArchetype + DeriveFeatures for tray + lid with screws (M8 subset) (RC9)

**File:** `assembly.py`, with the rule functions in a new section `derive_*`. Everything is a
`feature_graph.Node` whose params are **expressions** over reference datums, `spec.*` and
`rules.*`. Python never computes a number that the graph could express.

### ChooseArchetype

`feasible_archetypes(state)` returns `[("tray_lid", "screws")]` in the skeleton. With a single
feasible option, the choice is recorded as `rule:only_feasible`, with no LLM call. The ranking
call `assy_archetype` is wired but used only when there are more than one.

### CavityFromContents (the size-leak fix)

The cavity box is the AABB of every reference part (including connector overhangs) together with
V-KO-TOP and V-KO-BOT, grown by `spec.board_clearance` on each side.

### Base

```
base:   body, shell(x, y, z, wall, floor, open_top=1)
  wall  = min(max(rules.wall_default, spec.wall_min), spec.wall_max)
  floor = same clamp, using rules.floor_default
  x, y  = cavity + 2*wall
```

The floor top lies at board BOTTOM − `spec.keepout_below`. The base rim is the split plane, set
by this rule:

```
split = board TOP + spec.keepout_above + rules.lip_engagement
```

The rule puts the lid lip **above** V-KO-TOP, which avoids an L1.4 intrusion by the lip. A
second, generic condition is checked as `port_below_split`: every port cut's top plus
`rules.min_ligament` must be ≤ split. If it is not, the split is raised by the expression
`max(...)`, so this is still not a literal.

### Standoffs (MountHoleToStandoff)

For each board `HOLE[i]` there is an add node, a `cylinder` on the hole axis that runs from the
floor top to board BOTTOM.

- **Diameter.** `od = max(screw.pilot_diameter + 2*rules.standoff_wall_min, screw.min_boss_od
  if present)`.
- **Pilot.** A cut cylinder with `d = screw.pilot_diameter`, blind from the standoff top,
  `depth = screw.min_engagement`. A check verifies that `depth ≤ standoff height + floor −
  rules.min_feature`.
- **Board screw.** The smallest-thread fastener in the catalogue whose
  `thread_diameter + 2*rules.screw_hole_clearance_min` is ≤ the board `hole_diameter`. This needs
  a new rule.

### Port cuts (ConnectorToCut)

For each exposed connector:

1. **Wall.** The wall is the base face whose outward normal is nearest to the connector AXIS dir.
2. **Size.** Intersect the plug sweep (C1) with that wall's slab and take the bbox perpendicular
   to the axis. Add 2 × `rules.plug_to_opening`.
3. **Shape.** If every intersecting plug primitive is a cylinder, the cut is a cylinder.
   Otherwise it is a box.
4. **Pose.** The pose is `at = <conn>.MOUTH`, `project_to = base.face[<side>].inner`,
   `axis = <conn>.AXIS`. The length is the wall thickness plus 2 × `rules.cut_overrun` (new rule,
   e.g. 1 mm).
5. **Role and body.** The node has `role = port_cut` and `body = base` (or `base,lid` if the cut
   crosses the split).

### Lid and closure (LidToFastening, screws)

- **Lid plate.** `lid` is a body `box`: the base outer plan, thickness `wall`, sitting at Z = split.
- **Lip.** An add on `lid`: a `shell` ring (floor 0, open top). Outer size = cavity −
  2 × `rules.sliding_fit`, wall `rules.lip_wall` (new rule), height `rules.lip_engagement` (new
  rule, 2.0 mm, FDM practice). It hangs from the plate bottom.
- **Bosses (generic rule: corner pilasters outside the content clearance).**
  - Each boss axis lies on the diagonal outward from each corner of the contents' plan AABB, at a
    distance `boss_od/2 + spec.board_clearance` from that corner. This puts the boss clear of the
    board by the board clearance, and of the driver columns, which is checked by `clear_of`.
  - Each boss is an add on `base`, a cylinder running from the floor bottom to the split.
  - Its pilot is a cut on `base`, `d = lid_screw.pilot_diameter`, blind from the top,
    `depth = lid_screw.min_engagement`.
  - The lid gets a pad cylinder of the same OD at the same axis, so the plan stays flush, and a
    through cut of `d = lid_screw.clearance_diameter`.
  - The lid screw is the largest-thread catalogue screw whose `min_boss_od` is ≤ the boss OD. The
    boss OD itself is `max(screw.min_boss_od, pilot + 2*rules.boss_wall_min)` (new rule).

### The corner-pilaster refinement

This is the refinement written into ARCHITECTURE.md §4.3. The cavity is sized by the 0.5 mm board
clearance, so a boss inside the cavity corner would collide with the board. Making the walls thick
enough to hold the boss would break L1.8, since walls must be 2 to 4 mm. The pilaster is the
generic feasible placement. It was derived from the clearances, not from this box.

### New `design_rules.json` keys

Each key needs a source:

- `plug_travel`, `driver_clearance`, `overlap_max`;
- `seat_gap_max`, `seat_axis_residual_max`;
- `lip_engagement`, `lip_wall`;
- `boss_wall_min`, `cut_overrun`, `screw_hole_clearance_min`;
- `max_quantity`;
- the `spec_slots` section.

### Tests (`test_assembly.py`, class `TestDeriveFeatures`)

These use scripted contents and layout for E1-01, plus V1 to prove nothing is E1-specific.

- **Port cuts.** There is exactly one port_cut per exposed connector, on the wall that faces it.
  For E1-01 that is 1 on −X and 2 on +X. For V1 the cuts move to the walls V1's layout implies.
- **Standoffs.** There are 4 standoffs, coaxial with board HOLE[i] (offset ≤ 1e-6). Their tops
  equal board BOTTOM. The pilot depth is at least the screw's `min_engagement`.
- **Lid.** The lip-to-cavity gap equals `rules.sliding_fit`, within the rules band. The lip
  bottom is at or above V-KO-TOP's top.
- **Bosses.** The bosses and the lid clearance holes are coaxial.
- **Size leak.** Changing `spec.keepout_above` by +3 raises the split by +3 and changes nothing in
  X or Y. Changing the board width changes only the X-dependent expressions. This proves that
  sizes are derived, not filled in.

## 11. Change C7: Build, Verify, RenderViews, WritePackage, finalize (M12 subset) (RC8, RC12)

### Build

1. Resolve `st.graph` with `spec`, `rules.values` and the catalogue.
2. Compute `body_solid` for `base` and `lid`.
3. Write `base.scad` and `lid.scad` (`scad_body`) and `model.scad` (`scad_model`, with ghosts).
4. Compile each body with `ca.compile_scad`. If that fails or times out (`OPENSCAD_TIMEOUT`),
   write the STL with `fg.write_stl` from the manifold solid and record
   `stl_source[body] = "manifold"`.
5. Parity: the OpenSCAD volume must be within 0.5% and the bbox within 0.05 mm of manifold. A
   mismatch is a typed note, and the manifold STL is used.

### Verify

Verify runs the rule-derived check set below on the manifold solids. It then runs
`measure_package` on the **delivered** STLs. The results go to `st.results`, and Verify always
returns SUCCESS, so the package is always written.

| Check | Arguments |
|---|---|
| `separable` | base, lid |
| `inside` | RBA, 0.5 → `spec.board_clearance` |
| `clear_of` | ALL vs board minus seats, `spec.board_clearance` |
| `clear_of` | ALL vs V-PICO, `rules.part_to_wall` (new rule) |
| `clear_of` | ALL vs each plug sweep, `rules.plug_to_opening` |
| `clear_of` | ALL vs V-KO-TOP / V-KO-BOT minus seats, 0 |
| `aperture_count` | per wall that has cuts, and 0 on the others |
| `aperture_oversize` | ≤ `spec.opening_oversize_max` |
| `seated` | (no extra arguments) |
| `bbox_within` | `spec.max_*` |
| `port_below_split` | (no extra arguments) |

### RenderViews

- `ca.render_openscad` on a bodies-only `views.scad`, giving `views/model_{iso,front,back,left,right,top}.png`.
- `ca.render_openscad` on `model.scad`, giving `views/ghost_*.png`.

### WritePackage

Writes into `design.workdir`:

| File | Contents |
|---|---|
| `base.stl`, `lid.stl` | the delivered bodies |
| `base.scad`, `lid.scad`, `model.scad` | the OpenSCAD source |
| `layout.json` | the frame (board frame = enclosure frame, X along the longest board edge); for each reference its catalogue id, params, x, y, z and rot_z; for each body its print orientation from `rules.print_orientation` |
| `self_report.json` | the `measure_package` output |
| `feature_graph.json` | the feature graph |
| `checks.json` | the check set |
| `verification_matrix.{md,json}` | built with `cad_checks.verification_matrix`, which is reused |

`design.json["assembly"]` gains `spec` with provenance, `choices` with who made them,
`assumptions`, `stl_source`, the results, and a `components` list *generated from the graph and
measured bboxes*, never from LLM text. That last point closes L3.12.2.1's "claims not in the
geometry".

`ExportModel`: export the 3MF of `model.scad` bodies via `ca.export_openscad`. A failure is a
note, not a crash.

### finalize

`finalize(design, llm)` returns `{"outcome": "verified" | "unsatisfied", ...}`: verified exactly
when every check passes on the delivered STLs. `cad_agent.main` already maps that to exit 0 or 3.

### Tests (`test_assembly.py`, class `TestPackage`, and the end-to-end test in C8)

- **Manifest (the G0 equivalent).** Every file listed above exists and parses. Both STLs load
  through the rubric recipe, give 1 shell each and `NoError`, and their bbox per axis is within
  20 to 200 mm.
- **Self-report.** `self_report.json` equals an independent re-measurement within 0.02. The test
  calls the rubric recipes directly and does not use `assembly_checks`.
- **No references in bodies.** No reference node appears in `base.scad` or `lid.scad`.
- **Graph-built components.** The design.json components come from the graph: the count of
  role=standoff entries equals the count of standoff nodes.
- **Fallback.** With OpenSCAD mocked to time out, the STL is written from the manifold and
  `stl_source == "manifold"`.

## 12. Change C8: offline end-to-end (an M13 preview) and other modes intact

- **`test_assembly.TestEndToEnd`.** It runs `cad_agent.main` with
  `--mode assembly --auto --l1 <E1-01 l1> --parts PARTS --rules design_rules.json <E1-01 request>`,
  with `OllamaAgent` patched to a `ScriptedLLM`. The script holds the correct ids, quantities and
  edges, and says yes to the confirmation. Expected results:
  - exit 0, or 3 with every failing check named in the matrix;
  - **all gate-equivalent checks pass**: separable, inside, the board / plug / keep-out `clear_of`
    checks, aperture counts 1 and 2, seated, and bbox;
  - the outer size is within `spec.max_*`, and outer X is greater than outer Y.

  The same test then runs with V1's request and scripted choices, and asserts the same check
  family. The point of the V1 run is to show that the pipeline does not encode E1-01. Runtime
  should stay under about 60 s, using `rules.fn` overridden to 24 in the test rules copy. If
  OpenSCAD is missing, the manifold fallback applies.
- **Existing suites.** `test_cascade test_cad_checks test_review_fixes test_cad_agent
  test_benchmark_runner` pass unchanged. In `test_assembly`, the M0 stub tests
  `test_stub_exits_1...` assert `assembly.stage == "parse_spec"` and that the fake LLM is never
  called. They **must be changed**: the behaviour intentionally changed, because the stub stage
  no longer exists. Each change needs a one-line ledger justification. Keep their
  catalogue-gate assertions: a dropped inch-scaled part and a missing catalogue still stop at
  `load_catalog`. Missing rules still stop at `load_rules`, before any LLM call, and that is
  asserted with the raising fake.
- **Full command.** Add `test_assembly_checks` to the RUN.md §2 test command.

## 13. How this moves the judges and the loop

With C0, iteration 003's judges measure the assembly package. These estimates assume the 9B
controller gives correct answers for ParseSpec, Contents and Edge. ConfirmArrangement covers a
wrong edge, but not a wrong spec slot.

| Gate / L1 | Expected after this delta | Why |
|---|---|---|
| G0 / L1.12 | PASS | All of L2.12.1 is written. The self-report comes from the delivered STLs (L3.12.2.1). |
| G1 / L1.9 shells, L1.7 L3.7.1.x | PASS | Two bodies, 1 shell each, overlap ≤ 1 mm³ (`separable` is in Verify). |
| G2 / L1.2, L1.4 | PASS | The cavity is derived from the contents and keep-outs plus the clearance. The lip sits above the keep-out. |
| G3, G4 / L1.5, L1.6 | PASS | The cuts come from the plug sweep crossing the wall slab, plus `plug_to_opening`. Oversize is checked against `spec.opening_oversize_max`. |
| G5 / L1.3 | PASS | 4 standoffs coaxial with the holes, plus pilots sized from the catalogue fastener. |
| L1.1 | PASS likely | `layout.json` holds catalogue parts, directions, spacing and the hole columns. Grid conformance for the jacks is open: PJ-320A footprint pins are not modelled (iteration 001 note). |
| L1.7 lip / bosses | likely PASS | Sliding fit 0.25 within 0.15 to 0.35, engagement 2.0, 4 bosses with pilot 2.5, OD ≥ 6, lid holes 3.4. |
| L1.8, L1.10, L1.11 | mostly PASS | Walls 2.4. Rough outer size from the rules about 83 × 62 × 25 mm, within 90 × 70 × 35. The install sweep and driver columns are not checked by the agent yet. |
| L1.9 printability, L1.8 "no other openings", seam | unverified by the agent | `printable`, `min_wall` and V-AP-OTHER come next iteration. |

**Realistic outcome.** The verdict moves from WRONG with every gate failing to MINOR or CORRECT,
provided the controller's answers are right. If a 9B answer is wrong, the error signal now says
**which stage** chose it, because design.json records choices and provenance.

**Next deltas.**
- Iteration 003: Solve (M9) on the numeric failures Verify reports, `printable`, `min_wall`,
  V-AP-OTHER, `install_sweep` and the driver columns.
- After that: translation (M10) and the middle loop (M11) for the weight-1 and weight-2 L3s.

## 14. Notes for Robin (questions, never relaxations)

- **Lid retention.** The skeleton puts the lid-screw bosses in corner pilasters outside the board
  clearance, on the outside of the walls. This keeps walls 2 to 4 mm (L1.8) with a 0.5 mm board
  clearance (L1.2). If you prefer a sliding lid or snaps for this box, say so. They are listed
  alternatives (L2.7.3), and the archetype ranking will offer them from iteration 003.
- **Lid height.** The lid lip is placed above the 12 mm keep-out, so the closed height is about
  25 mm, not about 22 mm. That follows from L1.4's "no part of the enclosure within 12 mm above
  the board".
- **Rule values.** New `design_rules.json` values (`lip_engagement` 2.0, `boss_wall_min`,
  `plug_travel` and the others) are generic FDM defaults, each with a source. Please review the
  file by hand, because the hard-coding guard does not scan JSON.
