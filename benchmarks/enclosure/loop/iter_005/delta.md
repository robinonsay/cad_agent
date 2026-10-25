# Iteration 005: gap analysis and delta design

Tooling note: the claude-context MCP server failed to connect in this session, so this analysis used
targeted grep and direct reads of known paths (assembly.py, assembly_checks.py, parts.py,
feature_graph.py, test_assembly.py, test_parts.py, requirements.md, rubric.md).

Input: `target_s0/20261024-095851` (E1-01, seed 0, rc 3 `unsatisfied`, 33/34 own checks, only
`grid_conformance` failing). Both judges: **DOES NOT MEET / CORRECT**, about 132/134. All six gates
pass, every weight-3 L3 passes, and the worst weight-3 margin is 0.20. Two weight-1 L3s fail:

| Defect | L3 (L1) | Both judges? | Agent-closable this iteration? |
|---|---|---|---|
| D1: Pico header pins 1.13 mm off the assumed grid in X; jack pins have no data (UNVERIFIED) | L3.1.6.1 (L1.1) | yes | **no.** It is a requirement conflict plus missing catalogue data, so it goes to Robin (section 5) |
| D2: the self-reported board clearance is 0.853 against the judge's 1.100 | L3.12.2.1 (L1.12) | yes | **yes** (C1) |
| D3: the self-reported Pico envelope gap is 0.600 against the judge's inside(V-PICO) of 1.523 | L3.12.2.1 (L1.12) | judge 2 | **yes** (C2) |
| D4: no separate inside() figure for headers and jacks; the agent's `inside_references` (0.853) was compared with L3.4.3.1 (1.208) | L3.12.2.1 (L1.12) | judge 1 | **yes** (C3) |

Observations that do not change the verdict, and are not addressed here (section 6): pilot depth and
lid-boss OD sit exactly on their catalogue minimums, the lid-screw bosses are external corner
columns, the renders do not clearly show the USB opening, the verification matrix maps every
rule-derived check to `rules` rather than to an L1, and the L3.12.1.1 lid bbox band (question 1,
still open).

What changed since iteration 004: the agent now reports `unsatisfied` with the right reason (the
grid conflict), as iteration 004 predicted. The cavity, port and keep-out fixes from iteration 004
held, and every weight-3 check passes with margin. What remains is (a) a decision for Robin and
(b) the agent's **sensor vocabulary**: its self-report measures proxies that the judge does not
measure.

---

## 1. Root causes

### RC-501: contact exemptions are not grown by the check's clearance (D2)

`assembly.build_plan` adds `clear_board` (and `inside_references`) as
`clear_of(ALL, board - seats, board_clearance)`. `seats` is the union of the V-SEAT columns at
Ø `seat_d` = head_diameter + 2 x driver_clearance = 7.0, the same volume the solder-side keep-out
subtracts. A clearance check with a contact exemption is only meaningful when the exemption covers
the contact zone **plus its clearance halo**. Otherwise a body that touches legally inside the zone
(the standoff top) is measured against the rim of the exemption (standoff side at r 2.65 against
board material at r 3.5, giving d = 0.853), not against the next real surface (the walls, at 1.100).
Requirements L2.2.1 defines it this way ("V-SEAT grown by the 0.5 clearance, so a standoff top may
touch"). The L1 text the agent gets ("apart from where it rests on its supports") says the same.
With clearance 0 (V-KO-BOT minus V-SEAT) the grown and ungrown columns are the same, which is why
that check agrees.

Pass/fail agreed. Only the reported number was wrong. The existing agreement test
(`TestEndToEnd.test_self_report_agrees_with_an_independent_measurement`) did not catch it because
its "independent" reference subtracts the agent's own seat nodes (`n.role == "seat"`), so it repeats
the agent's error.

### RC-502: the module envelope is one AABB proxy, not the reference solids (D3)

`parts.content_envelope` returns **one box**: the world AABB of the module plus its stack parts.
For the Pico, that box spans the full PCB and header width (Y) and height (Z) at the receptacle's
overhang X (USB_MOUTH). The receptacle is narrow and sits inside the USB opening, but the AABB's
corner reaches the end wall beside the opening. The gap comes out as 0.600 (to the -X wall inner face
next to the opening) instead of 1.523 (receptacle to the opening's edges). V-PICO in the requirements
is "M-PICO2 ∪ M-HDR bounding solids", the union of the catalogue primitives. A proxy is fine for
derivation. Here it feeds **only** a check (`KEEP_OUTS["module_envelope"]`: plan None, z None), so it
makes the agent's sensor read a different quantity from the judge's. The check is also a `clear_of`,
while the requirement is an `inside` (gap to solids **and** to the outside of the hull).

### RC-503: composite reference volumes are reported as one undifferentiated number (D4)

`inside_references` = inside(board ∪ every content part − seats, all bodies, board_clearance). Its d
is the minimum over all references, which is the board (0.853, from RC-501). A judge cannot get
the gap of any sub-union from it (L3.4.3.1 = headers ∪ jacks, L3.2.2.1 = V-PICO). It maps the one
number to whichever L3 it looks like, and then the numbers disagree. The fix is not to copy the
judge's groupings into the agent (the agent never receives requirements.md). The fix is to make the
report **decomposable**: report d per reference part, so any union's d is the minimum of its
members, and keep the board (the carrier) apart from the contents it carries.

These three causes share one theme, which becomes ARCHITECTURE.md 7.8: **the self-report must
measure the reference parts themselves, in a form any independent measurement can recompose.** It
must never measure a derivation proxy.

### D1 is not an agent gap (no code change)

As in iteration 004: under the catalogue's soft grid registration (hole 1 at (2.5, 2.5)), the pins
need the Pico PCB's min-X in [0.98, 1.28] or [-1.56, -1.26]. Flush-to-edge (L2.1.3) needs [-0.5, 0.5].
No pose satisfies both. The best residual is 0.63 mm. The agent already reports this as a typed
`assembly.conflicts` entry, and both judges credit that. The PJ-320A footprint pins are still missing
from `parts/jack_3p5_pj320a/part.json`, and per iteration 004 they must not be invented. Changing
placement to trade flush-to-edge (weight 2) for grid (weight 1) would swap a weight-1 failure for a
weight-2 one and would undo the 7.5 priority. That would oscillate, so it is rejected.

---

## 2. Delta (three changes, one pass; no derivation or geometry change to the bodies)

The base and lid STLs should come out byte-identical to iteration 005, given the same controller
answers. Only checks.json, self_report.json, feature_graph.json (envelope nodes) and the matrix
change.

### C1 (RC-501): exemptions grown by the clearance

- `feature_graph.py`: new `grown_solid(node, resolved, delta) -> Manifold`. For a `cylinder`:
  d + 2δ, height + 2δ, base moved down by δ along the node's axis. For a `box`: each size + 2δ,
  centred on the same pose. Any other primitive raises `ValueError` naming the node. It uses the
  same circumscribed `_poly_d` rule as `solid()` for envelope cylinders, so it errs against the
  design (7.7).
- `assembly.build_plan`: after every spec has been added, run one generic pass. For each `clear_of`
  or `inside` spec with `minus` = M and clearance c > 0, replace M with the volume
  `f"{M}@{c:g}"` = union(grown_solid(n, res, c) for n in plan.sources[M]). Record
  `plan.sources[f"{M}@{c:g}"] = plan.sources[M]` (no dead envelopes: the seat nodes still feed a
  check), and add `args["minus_grown_by"] = c`. With c = 0 (keepout_bottom), nothing changes.
- Check words: "except the standoff tops in the seat columns grown by the clearance (Ø {d:g})",
  with the grown diameter computed from the resolved seat params, never written as a literal.
- No new rule value. Growing by the check's clearance follows from the definition of an exemption.

### C2 (RC-502): the module envelope is the union of the reference primitives, checked with `inside`

- `parts.content_envelope(parts, node_id, role)` now returns a **list** of envelope nodes, one per
  geometry primitive of each (instance, pose). The pose is built the way `plug_sweep` builds it:
  `rot_z` from the instance pose, and the offset from pose ∘ primitive `at`. Ids are
  `f"{node_id}_{k}"`. Each node carries `group=node_id` and `source="rule:content_envelope"`. The
  union of the list equals the union of the reference solids of the module and its stack.
- `feature_graph.Node`: new optional field `group: Optional[str] = None`, included in
  `to_json` / `from_json`. Old graphs without it still load. `plug_sweep` sets
  `group=prefix` (`{p.node_id}_plug`).
- `assembly.add_keepout_checks`: rows with `"group": True` group their nodes by `n.group`, not by
  an id-prefix lookup in the exposed-connector dict. The plug words still come from that dict when
  the group is a plug group. `KEEP_OUTS["module_envelope"]` gains `"group": True` and
  `"type": "inside"`. `add_keepout_checks` emits `row.get("type", "clear_of")`. The check id stays
  `clear_{group}` (`clear_module_1_1_envelope`) so checks.json stays comparable. The text becomes
  "{group} (the module and its stack parts) lies inside the closed enclosure, at least {c:g} mm from
  every printed surface and from the outside".
- `BuildEnvelopes` adds every node of the list (`for n in pt.content_envelope(...)`).
- The ghost render and `test_no_dead_envelopes` work unchanged, because each node keeps role
  `module_envelope` and feeds the grouped check.

### C3 (RC-503): carrier and contents split, and per-part figures in every composite report

- `assembly.build_plan`: replace `inside_references` with two checks:
  - `inside_board`: inside(board − seats, all bodies, spec.board_clearance). The seats are grown by
    C1.
  - `inside_contents`: inside(union of every reference except the board, all bodies,
    rules.part_to_wall), with volume `contents` and `plan.sources["contents"]` = those reference ids.
    "The board" is `st.placed.get("board")`, the carrier role the code already uses. No part id or
    count is written into the code.
- `assembly_checks.Plan`: new field `parts: Dict[str, Dict[str, Any]]`, mapping a volume name to
  {source node id: solid}. `build_plan` fills it for every volume with two or more sources
  (`contents`, `references` if kept, module envelope groups, plug groups).
- `assembly_checks.clear_of` / `inside` take an optional `parts` mapping. When it is given, they
  measure each part (with the same `minus`) by the same recipe and add
  `evidence["per_source"] = {node_id: {"part": catalogue id or role, "d": gap or None,
  "penetration_mm3" / "outside_mm3": ...}}`. The headline d stays the measurement of the union.
  `run_plan` passes `plan.parts.get(volume)`. Cost: about 15 extra `min_gap` calls. The hull is
  computed once per `inside` call.
- Every reference-based check also records `evidence["volume_parts"]` (node id → catalogue id)
  and the `minus` description. A reader can then see exactly which solids the d is about without
  reading code. `self_report.json` gets a top-level `"references"` table built from these: per
  reference node, its catalogue id and its smallest reported inside/clear d.

### Predicted effect on the judges' verdict

| Agent figure | iter 005 | after delta (predicted) | judge iter 005 |
|---|---|---|---|
| clear_board d | 0.853 | about 1.100 (board edges to walls X 71.1 / Y ±1.1) | 1.100 |
| inside_board d | (inside_references 0.853) | about 1.100 | 1.100 (L3.2.1.1) |
| inside_contents d | n/a | about 1.208; per_source has the headers and each jack | 1.208 (L3.4.3.1) |
| clear_module_1_1_envelope d | 0.600 (clear_of, AABB) | about 1.523 (inside, primitives) | 1.523 (L3.2.2.1) |
| hole_ko / driver / KO / plugs | 0.096 / 0.596 / 0.100 / 0.400 | unchanged | 0.100 / 0.600 / 0.100 / 0.400 |

With every reported d within 0.10, L3.12.2.1 passes and L1.12 passes. E1-01 is expected to stay
**DOES NOT MEET / CORRECT** with 133/134. The only failure left is L3.1.6.1 (L1.1), which needs
Robin's decision (section 5). The agent still ends `unsatisfied` (rc 3), with only `grid_conformance`
failing and one conflict, and that is correct. Once Robin answers questions 2 and 3, the remaining
change is data only (perfboard grid registration, jack PINS), and E1-01 can MEET with no agent
change. That makes this iteration the last sensor-side blocker on E1-01.

---

## 3. Tests (fake LLMs only, no Ollama)

New tests:

- `test_feature_graph.TestGeometry.test_grown_solid`: a cylinder grown by δ has volume
  π(d/2+δ)²(h+2δ) within the polygon allowance, and its bbox is the original ±δ. A box grown by δ has
  size + 2δ on every axis. δ = 0 gives the same volume as `solid()`. A `tube` or `shell` raises with
  the node id in the message.
- `test_assembly_checks.TestClearOf.test_exemption_grown_by_clearance`: a synthetic plate with a
  Ø3 hole and an exemption column of Ø D around it, a peg of OD < D touching the plate's underside
  inside the column, and a wall at a known distance w from the plate edge. With the ungrown column,
  d = (D − OD)/2 (the rim artefact). With the column grown by c, d = min(w, (D + 2c − OD)/2), which
  is w when w is the smaller. Values are computed in the test from the fixture numbers.
- `test_assembly_checks.TestInside.test_per_source_is_decomposable`: a volume made of two boxes at
  different distances from a shell. The headline d equals min(per_source d) within 1e-6, and each
  per_source d equals an `inside` run on that box alone. clear_of gets the same test.
- `test_parts.TestEnvelopes.test_content_envelope_is_the_union_of_primitives`: for the Pico on male
  headers, the returned nodes' union volume equals the union volume of the reference solids of the
  Pico and its stacks within 1e-3 mm³. Every node has `group` = the requested id. A point just
  inside the old AABB corner (USB_MOUTH.x + 0.1, PCB min-Y + 0.1, PCB top + 0.1, computed from the
  datums) is **not** inside any node. This pins RC-502.
- `test_feature_graph`: `Node.group` survives the JSON round trip, and a graph JSON without `group`
  still loads.
- `test_assembly.TestDeriveFeatures.test_minus_is_grown_by_the_check_clearance`: for E1-01 and V1,
  every plan spec with `minus` and clearance c > 0 names a volume `M@c` whose sources are M's sources,
  and whose bbox in plan is M's grown by c. keepout_bottom (c = 0) keeps `seats`.
- `test_assembly.TestDeriveFeatures.test_composite_checks_report_per_source`: every clear_of /
  inside spec whose volume has two or more sources produces `evidence.per_source` with exactly those
  node ids, and `volume_parts` naming their catalogue ids. `inside_contents` excludes the board,
  `inside_board` is the board only, and `inside_references` no longer exists.
- `test_assembly.TestEndToEnd.test_self_report_matches_requirement_references` (replaces the
  board half of the existing agreement test, see below). The references are rebuilt in the test
  from the catalogue (`pt.Catalog.load(PARTS)` geometry and datums at the `layout.json` poses), with
  the rubric 3.1 load, 3.2 clear_of and 3.3 inside recipes. They are never rebuilt from the agent's
  envelope nodes:
  - board minus Ø(seat_d + 2 x board_clearance) columns on the board's HOLE datums, where seat_d
    comes from the fastener record in design.json, compared with `clear_board` and `inside_board`;
  - the union of the module's and its stacks' catalogue primitives, compared with
    `clear_module_1_1_envelope` (inside);
  - the union of every non-board reference's primitives, compared with `inside_contents`, plus each
    of those parts alone, compared with its `per_source` entry.
  Every comparison must agree within 0.02, for E1-01 and V1 (V2 and V3 too if they run within the
  suite's time budget).
- `test_assembly.TestReplayIter005.test_replay_iter005_answers_end_to_end`: per 7.6, the recorded
  iter_005 controller answers (from `iter_005/target_s0/20261024-095851/llm/`) are scripted into the
  fake LLM. The test expects rc 3 with only `grid_conformance` failing and one conflict, base and lid
  volumes equal to the iter_005 self_report volumes within 0.01 mm³ (no geometry change), and the
  `test_self_report_matches_requirement_references` comparisons holding on that package.

Changed tests (behaviour intentionally changed; one line each goes in the ledger):

- `TestEndToEnd.test_self_report_agrees_with_an_independent_measurement`: its board reference
  subtracted the agent's own seat nodes, so it repeated RC-501. The board half moves to the new test
  above. The plug half stays as it is.
- `test_parts.TestEnvelopes.test_columns_and_content_envelope`: `content_envelope` now returns a list
  of primitive nodes. The same assertions are made on the union's bbox (receptacle overhang inside,
  headers standing on the board top).
- Any test or replay that lists check ids: `inside_references` is replaced by `inside_board` and
  `inside_contents`, and `clear_module_*_envelope` changes type from clear_of to inside.
- `test_no_hardcoding` must stay green. C1 to C3 add no numeric literal and no part id.

Suite: `venv/bin/python -m unittest test_cascade test_cad_checks test_review_fixes test_cad_agent
test_benchmark_runner test_parts test_feature_graph test_assembly test_assembly_checks
test_no_hardcoding`. Expect about 322 tests (314 + about 8).

---

## 4. Run step for iteration 006

Iteration 004 asked for variant runs, and iteration 005 ran only E1-01 seed 0. Convergence (section 8)
needs V1, V2 and V3 at least CORRECT, and each takes about 1–2 minutes. Run E1-01 with SEED = 5 (a
second seed), then V1, V2 and V3 (`run_one V1; run_one V2; run_one V3` per RUN.md 3.1). Only the Run
step uses Ollama.

## 5. Questions for Robin (still open; they block E1-01 MEETS, and no agent code can close them)

1. **L3.12.1.1:** the 20–200 mm per-axis bbox band fails any flat lid (4.4 mm). Should it be a units
   check on the largest axis?
2. **Grid registration versus L2.1.3:** where does your board's 2.54 grid sit relative to the corner
   holes? Or should the USB band follow the grid? Under the current assumption (grid on hole 1), no
   Pico pose meets both. The best residual is 0.63 mm.
3. **PJ-320A footprint pins:** if you give the footprint you use, it goes in
   `parts/jack_3p5_pj320a/part.json` as a `PINS` axis_list. The agent already snaps and checks it.
4. **L3.11.1.1 V-INSTALL** touching the standoff tops (from iteration 004).

## 6. Deliberately not in this delta

- **Design margin on pilot depth and boss OD:** an observation only. These limits come from the
  fastener catalogue, and the judges passed them. Revisit if a judge ever fails one by tessellation.
- **Verification matrix L1 mapping** (rule-derived checks tagged `rules`): this is the M10 Translate
  milestone. It is not graded (judge 2), and it needs an LLM mapping step with gates, so it is too big
  to do well in the same pass. It is next after the variants have been judged.
- **USB-opening render:** cosmetic.
- **Grid or placement changes:** rejected (section 1, D1).
