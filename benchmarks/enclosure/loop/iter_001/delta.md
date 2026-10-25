# Iteration 001: gap analysis and delta design

Inputs: judge_1.json and judge_2.json for `target_s0` (E1-01, seed 0, `--mode cascade`, rc 124 after
5411 s), the package `target_s0/20261024-035938/`, the run log, ARCHITECTURE.md, LEDGER.md (empty, so
this is the first delta and no idea has been tried before) and the code at the SHA1s in
`code_sha1.txt`. These equal `baseline_code/SHA1SUMS`, so the run used the working tree, including
the uncommitted ×10 retry caps in `cad_agent.py` and `cascade.py`.

Tooling note: the claude-context MCP server failed to connect in this session ("failed to connect";
its tools were not offered). I fell back to reading known paths and to targeted `grep` for the line
anchors quoted below.

## 1. Verdict in one line

Both judges: **WRONG**, all 12 L1s fail and gates G0–G5 all fail. The package is one 12-triangle
slab, 90 × 74 × 4. This is exactly the "expected baseline" in RUN.md section 4: the cascade mode can
only union up to 8 primitives on each other's outside faces. Every defect traces to a missing agent
capability, not to a bad LLM answer that a better prompt would fix.

## 2. Root causes (defects grouped by shared cause)

| RC | Root cause in the agent | Where in code | Defects it explains (L3 ids, gate) |
|---|---|---|---|
| **RC1** | **Representation is a flat list of additive primitives.** There are no cut nodes, no shell or cavity primitive, no interior placement and no datums. `scad_source` emits one `union()`. A child can only sit on a parent's *outside* face at a left/center/right fraction. An opening, a pilot hole, a cavity or a standoff inside a footprint therefore cannot be expressed, whatever the LLM says. | `cad_agent.py:223` `SHAPES`; `:310` `attach_position`; `:2095` `scad_source`; `:71` `MAX_COMPONENTS = 8` | L3.2.1.2, 3.2.2.1-2 (G2, zero cavity); L3.3.1.1-4, 3.3.2.x, 3.3.3.x (G5, no standoffs or pilots); L3.5.3.1, 3.5.2.1 (G3); L3.6.3.1, 3.6.2.1 (G4); L3.8.1.1, 3.8.2.x, 3.8.4.1; L3.4.1.2, 3.4.2.2, 3.4.3.1 |
| **RC2** | **There is no concept of a printed body.** The design is one fused assembly, and `EmitScad`/`ExportModel` write one `model.stl`. "lid" is just another component attached to an outside face, so the LLM's "lid" became a 90 × 4 × 4 strip on the base's +Y face. There is no closed-pose "covers the base" relation and no seam. | `cad_agent.py:2127` `EmitScad`, `:2910` `ExportModel`, `:310` (placement on the outside face only) | L3.7.1.1, 3.9.2.1 (G1); L3.7.1.2, 3.7.2.x, 3.7.3.x, 3.7.4.1; L3.10.1.1 (Y = 74 comes only from the side-strip lid) |
| **RC3** | **There is no parts catalogue, no datums and no layout.** `benchmarks/enclosure/parts/` is empty. The agent never knows where the USB mouth, the jack axes or the board holes are, so it cannot place openings or standoffs, cannot declare a layout, and the judges had to build references from requirements.md. | `parts/` empty; no loader module exists | L3.1.1.1, 3.1.2.1-6.1 (all of L1.1); L3.12.1.2; and indirectly every port and standoff position |
| **RC4** | **The LLM invents sizes (the size leak).** `AccountForNumbers` forces each request number into *some* parameter, so "50" went to the base again and again (run.log), and the size limit 90 × 70 became the box itself, with the 4 mm wall number as its height. Nothing derives the cavity from what it must hold. | `cad_agent.py:1947` `AccountForNumbers`; `FillParams :1510` | L3.2.x, 3.4.x (outer Z 4.0, not about 21.6 or more); L3.10.1.1 |
| **RC5** | **There is no package writer for the judge's contract.** Nothing writes base.stl, lid.stl, layout.json or a self-report, and the descriptions in design.json and the SCAD comments are written from the LLM's *intent*, not from the built geometry. | `write_design_json :2162`; component `summary()` text | L3.12.1.1 (G0); L3.12.2.1 (the claims are false) |
| **RC6** | **The error signal cannot see the defects, and the control logic spent the whole budget translating requirements the representation cannot express.** `cad_checks` has 13 check types and no clear_of, inside, aperture, separable or seated check. The cascade translator saturated on L1.1 after 30 iterations (the ×10 caps) proposing vacuous checks ("exactly 1 parts"). The run was then killed at 90 min, before Verify or export of any self-report. | `cascade.py:70` `TRANSLATE_ITERATIONS = 30`, `:974` `translate_loop`; `cad_checks.py` check registry | the G0 timeout; every UNVERIFIED (L3.11.x, 3.10.3.1) |

The fix for RC1–RC6 is the target architecture itself (ARCHITECTURE.md sections 3–6). Patching
cascade would not help. The cascade's representation cannot express a cut, so a better prompt or
more retries only spends more time (RC6 shows this). Reverting the ×10 caps would only make the
baseline fail faster. The caps are Robin's working-tree change and are left alone.

## 3. What blocks progress, and the choice for this iteration

The judges' verdict can move off "WRONG at G0/G1" only when assembly mode writes a package with two
bodies. In milestone terms, that needs M0–M4, M7, M8 and M12 (see the new ARCHITECTURE.md
section 7.1). That is too much for one safe pass. This iteration therefore builds the
**foundation that every later milestone depends on and that closes RC1 and RC2 at the
representation level, plus RC3's data**: **M0 + M1 + M2 + M3**. It is pure Python plus data,
testable with no Ollama, and it adds no LLM behaviour yet.

Deferred, with reasons:
- **M0b** (pilot bug fixes in default and cascade): none of those bugs is on the assembly path, and
  none explains any judged defect. It stays in the milestone list.
- **M4 onward:** these need M1–M3's types. Iteration 002 is planned in section 9.

Honest expectation: **the E1-01 judge verdict will not change in iteration 002's Run.** It stays
WRONG, because assembly mode stops at a typed "not implemented: <stage>". Section 8 says what the
Run step should do with that.

## 4. Change C0: CLI scaffold and hard-coding guard (M0)

**Files and functions**
- `cad_agent.py`
  - `main()` (`:3039`): add `"assembly"` and `"enclosure"` to `--mode` choices and map `enclosure`
    to `assembly` right after parsing. `assembly` needs `--l1`, exactly like cascade (same
    `parser.error` path). Add `--parts DIR` (default `benchmarks/enclosure/parts` relative to the
    repo, i.e. `Path(__file__).parent / "benchmarks/enclosure/parts"`), `--rules PATH` (default
    `Path(__file__).parent / "design_rules.json"`) and `--with-models` (store_true). All three are
    ignored by the other modes.
  - In `main()`: `if args.mode == "assembly": import assembly as assy_mod; root =
    assy_mod.build_assembly_tree(design, llm, parts_dir=args.parts, rules_path=args.rules,
    with_models=args.with_models, auto_approve=args.auto)`. On SUCCESS call `assy_mod.finalize`,
    mirroring the cascade branch (`:3085`). On FAILURE the existing path writes design.json
    "failed" and returns `EXIT_FAILED`.
  - `Design` (`:827`): add `assy: Optional[object] = None` next to `cascade`. Do not use the
    name `assembly`: it already holds the .scad path.
  - `write_design_json` (`:2162`): `if d.assy is not None: record["assembly"] = d.assy.summary()`.
- `benchmarks/run.py`: add `assembly` to `--mode` choices. In `plan_runs` (`:114`), apply the L1
  requirement to `mode in ("cascade", "assembly")`. Also generalise the error text, keeping the
  existing cascade message byte-identical so the existing runner tests still pass.
- New `assembly.py` (stub in this iteration):
  - `AssemblyState` dataclass with the fields of ARCHITECTURE.md section 3. Only `catalog`, `rules`,
    `stage` and `notes` are filled now. `summary() -> dict`.
  - `build_assembly_tree(...)` returns `Sequence("cad_assembly", [LoadCatalog, LoadRules,
    NotImplemented("parse_spec")])`. `LoadCatalog` calls `parts.Catalog.load(parts_dir)` and runs
    `parts.validate` on every part. A part that fails the gate is dropped and the failure is
    recorded in `state.notes`. `LoadRules` loads design_rules.json. `NotImplemented(stage)` logs
    `not implemented: <stage>`, sets `state.stage` and returns FAILURE.
  - `finalize(design, llm)` exists and raises NotImplementedError. It is unreachable until M13.
- New `test_no_hardcoding.py`:
  - An AST scan of `assembly.py`, `parts.py`, `feature_graph.py` and `assembly_checks.py` (if
    present). It fails on any numeric literal in the banned set {70, 50, 51, 21, 4.9, 17.5, 32.5,
    65, 45, 80, 60, 90, 40, 47, 11.4, 1.3, 1.6, 2.54, 12, 35, 8.5, 10.9, 6.9, 1.85}, compared
    within 1e-9.
  - It also fails on any string literal equal to a catalogue part id or alias. Ids and aliases are
    read from `parts/*/part.json` at test time, so the list grows with the catalogue.
  - **Guard of the guard:** the scanner function is also run on an inline source string
    `"x = 70\ny = 'rpi_pico2'"` and must report both. This proves the guard is not vacuous.
- `RUN.md` section 2: append the new test modules to the test command. Add section 3.1b (the stub
  smoke arm, see section 8).

**Tests (new, in `test_assembly.py`)**
- `test_mode_choices`: `--mode assembly` without `--l1` gives exit 2 (SystemExit 2). `--mode
  enclosure` parses to `assembly`.
- `test_stub_exit`: `main([... "--mode","assembly","--l1",<tmp l1>,"--parts",<fixture parts
  dir>,"--out",tmp, "req"])` with an injected fake LLM returns `EXIT_FAILED`. design.json has
  `outcome == "failed"` and `assembly.stage == "parse_spec"`. This needs `main` to accept an
  `llm_factory` or a monkeypatched `OllamaAgent`; use `unittest.mock.patch.object(ca,
  "OllamaAgent", ScriptedLLM-factory)` so `main`'s signature does not change.
- `test_other_modes_untouched`: the full existing suite stays green unchanged. That is the proof.
- `test_benchmark_runner` gets one **added** test: `plan_runs(..., mode="assembly", with_l1=False)`
  raises. No existing test changes.

## 5. Change C1: parts catalogue, loader, validation gate and rules (M1), which closes RC3's data gap

**Data: `benchmarks/enclosure/parts/<id>/part.json`** (schema 1, ARCHITECTURE.md section 3.1):
`perfboard` (parametric), `rpi_pico2`, `header_male_2p54`, `header_female_2p54`,
`jack_3p5_pj320a`, `plug_microusb_b`, `plug_trs_3p5`, `generic_cylinder` (parametric),
`screw_m2p5_selftap`, `screw_m3_selftap` and `heatset_m2p5`.
- Numbers come from the public datasheets listed in requirements.md 2.2 and A3–A9, and each block
  cites its `source`. This is the **only** place they may live.
- `perfboard`: `params` are `width` and `depth` (`from_request: true`, no default), plus
  `thickness`, `hole_inset`, `hole_diameter` and `grid_pitch`, each with a default and a
  `source`. Geometry and datums are expressions in those params: `HOLE` is an axis_list at
  `[[hole_inset, hole_inset, 0], [width-hole_inset, hole_inset, 0], ...]`.
- **Part frames** (write this into each part.json's `frame` text field):
  - board: origin at the min corner of the top surface, Z up.
  - module (Pico): origin at the PCB min corner, PCB bottom at Z = 0, USB end at −X.
  - header: origin at pin 0, spacer bottom at Z = 0.
  - jack: origin at the body min corner, bottom on Z = 0, mouth on the +X face.
  - plug: origin at the tip, inserted along −X of its own frame (mating direction = −`PLUG_AXIS`).
  - fastener: axis along Z.
- `self_checks`: a list of `{name, expr, value, tol}` evaluated by `validate`. This is how R2, R4,
  R5 and R6 become data, not code (for example `{"name":"R4 receptacle overhang",
  "expr":"-usb.min_x", "value":1.3, "tol":0.3}`).
- `connectors`: `{name, mouth, axis, mates}`. Example: the Pico's `usb` mates `plug_microusb_b`.
- `mount.stack_options` on `rpi_pico2`: `["header_male_2p54", "header_female_2p54"]`. The header
  part carries a `STACK_TOP` plane datum that sets the module's height. This is what V3 exercises.

**Data: `design_rules.json`** (repo root, generic only, each value with a `source`):
- sliding fit band;
- board-to-wall default;
- plug-to-opening clearance;
- minimum ligament;
- wall default;
- overhang angle;
- bed size;
- `$fn`;
- the default print orientation per role;
- keep-out defaults used only when the request is silent (provenance `rules:`).

These hold no target numbers. The hard-coding guard does not scan JSON. A reviewer checks this
file by hand.

**Code: `parts.py`**
- `Part` and `PartInstance` dataclasses. `Catalog.load(dir) -> Catalog`, which skips and reports
  unreadable files. `Catalog.lookup(text, k=3) -> List[(part_id, score)]` uses normalised alias
  tokens: lowercase, drop punctuation, join digit-letter splits ("pico2" ≡ "pico 2", "3.5mm" ≡
  "3.5 mm").
- `instantiate(part_id, params: Dict[str, float]) -> PartInstance`. It resolves geometry sizes,
  `at` values and datums through `feature_graph.evaluate` (C2). It raises `MissingParam(part,
  name)` when a `from_request` param is absent.
- Datum types: `Point`, `Axis(at, dir)`, `Plane(at, normal)`, `AxisList`.
  `transform(datum, Pose4x4)` covers translation plus rotation about Z by any angle, and an
  optional general 3×3 rotation for later use.
- `validate(inst) -> List[GateFailure]`. It runs:
  - R1: the bbox of the geometry union vs `datasheet_size` ± `size_tolerance`, checked per axis
    after sorting, plus an orientation check against the unsorted bbox;
  - datum direction vectors are unit length (±1e-6);
  - every connector `mouth` lies on the bbox surface of a geometry primitive (≤ 0.05);
  - every `self_check` holds;
  - R7 is deferred to M7 (it needs a layout), R8 to M4, and R9 is stubbed (returns "skipped").

**Tests (`test_parts.py`, no Ollama)**
- Every part.json in the repo catalogue loads and passes `validate`. Parametric parts are
  instantiated with params from a fixture request, not from code.
- `perfboard` with (w, d) = (fixture A) and (fixture B): there are 4 hole axes at the inset
  corners, and the bbox is `w × d × thickness`. The test computes the expected values from the
  part.json defaults it reads, so the test file has no target numbers either.
- **Unit-error rejection:** a copy of `rpi_pico2` with every size × 25.4, and one with X and Y
  swapped, each fail R1. A datum dir of `[2,0,0]` fails the unit-vector check. A mouth placed
  1 mm off the receptacle fails the connector check.
- `lookup`: "Raspberry Pi Pico 2" → `rpi_pico2` first; "3.5 mm aux jacks" → `jack_3p5_pj320a`
  first; "70 x 50 mm perfboard" → `perfboard` first; "female header sockets" →
  `header_female_2p54` first; "a 10 mm diameter capacitor" → `generic_cylinder` within top 3.
- `transform`: an axis datum rotated 90° about Z maps +X to +Y, and a point offset is applied.

## 6. Change C2: feature graph data model (M2), which closes RC1 and RC4 at the type level

**Code: `feature_graph.py`**
- `Expr`: a safe AST evaluator over `ast.parse(mode="eval")`. It allows numbers, `+ - * /`, unary
  minus, parentheses, `min`, `max`, `abs` and `ceil_to(x, step)`. Names are dotted refs:
  `node.param`, `spec.key`, `rules.key`, and datum refs `node.DATUM[i].x|y|z`. Any other AST node
  raises `ExprError(expr, reason)`. `evaluate(expr, env) -> float`. `refs(expr) -> Set[str]`.
- `Pose(at, offset, axis, project_to, rot_z)` as in section 3.2. `resolve_pose(pose, ctx) ->
  4×4`:
  - `at` is a datum point (or `frame.origin`);
  - `offset` is an Expr3;
  - `axis` rotates the node's +Z onto the datum axis direction (Rodrigues, with the antiparallel
    case handled);
  - `project_to` projects the anchor point onto a plane datum or a body face ref
    `body.face[-X].outer|inner`, along the plane normal. Face planes come from the resolved
    primitive params and pose of `shell` and `box` nodes.
- `Node` exactly as section 3.2, including `role`, `source` (provenance) and `free`
  (`[(param, lo_expr, hi_expr)]`).
- `FeatureGraph`: `add(node)`, `nodes_of(body)`, `references()`, `resolve(spec, rules,
  datums) -> Resolved`.
  - It topologically sorts on the `refs` of params and pose exprs.
  - A cycle raises `CycleError(nodes=[...])`.
  - An unknown ref raises `MissingRefError(node, ref)`.
  - `to_json()` and `from_json()` round-trip losslessly.
- Datums of reference nodes come from `parts.instantiate(...)` placed at the node pose, so
  `board.HOLE[2].x` is a real coordinate after placement.

**Tests (`test_feature_graph.py`)**
- `cavity.width = board.width + 2*spec.board_clearance` resolves. It re-resolves when `spec`
  changes (that is the size-leak fix in miniature: a size is *derived*, never typed in).
- A cycle a→b→a raises `CycleError` naming both nodes. A missing `foo.bar` raises
  `MissingRefError` naming the node and the ref.
- `__import__('os')`, attribute calls and lambdas raise `ExprError`.
- Pose with `axis` = +X datum: the node's +Z maps to +X. Antiparallel −Z maps correctly.
- `project_to`: a cut anchored at a point 3 mm inside a wall lands on the wall's outer plane
  (both the −X and +Y walls are tested).
- Datum ref through a placed reference: `board.HOLE[3].x` equals the instantiated part's hole x
  plus the board pose offset.
- JSON round trip: `from_json(to_json(g)).resolve(...)` equals `g.resolve(...)`.

## 7. Change C3: geometry, bodies and SCAD per body (M3), which closes RC1 and RC2 at the geometry level

**Code: `feature_graph.py`, geometry section** (manifold3d, with the same pattern and `$fn` as
`cad_checks._solid_cached`, `cad_checks.py:616`)
- Primitives for this iteration:
  - `box(size)`;
  - `cylinder(d, h)` (axis +Z, then posed);
  - `tube(od, id, h)`;
  - `shell(outer_size, wall, floor, open_top: bool)`, which is a box minus an inset box;
  - `part`, for references: the union of the instantiated part's geometry.
  `rounded_box`, `prism` and `sweep` come later.
- `solid(node, resolved) -> Manifold`. `body_solid(graph, body) ->
  difference(union(body base, adds), cuts)`. A cut with `role == "port_cut"` may list several
  bodies in `body` (comma list).
- `body_solid` **never** reads nodes with `kind in {"reference","envelope"}`. This is enforced
  with an assertion and tested: the structural half of `not_printed`.
- `scad_body(graph, body) -> str` emits `difference(){ union(){...} ...cuts }` with the same
  primitives, using `multmatrix` for poses so SCAD matches the 4×4 exactly. `scad_model(graph)`
  emits all bodies in their colours, plus references as `%`-prefixed ghosts.
- `body_stats(m) -> {volume, bbox, shells (len(decompose())), genus}`. `write_stl(m, path)` is the
  manifold fallback writer, used when OpenSCAD times out (section 3.2 "Delivered meshes").
- **Not this iteration:** the archetype that decides *which* nodes exist (M8). Tests build
  graphs by hand.

**Tests (`test_feature_graph.py`, geometry part)**
- A plate with one round and one rectangular through-cut has volume = plate − cut volumes,
  within 0.5% for `$fn` from rules.
- `shell(open_top=True)` plus a separate `lid` body: `body_stats(base).shells == 1`,
  `body_stats(lid).shells == 1`, and the intersection volume of the two at the closed pose is
  ≤ 1 mm³. This is the G1 property, proved in the plant model.
- The hull minus solid of a closed shell has the expected cavity volume. Hull minus solid of a
  `box` is 0. This is the judges' RC1 measurement, used here as a regression test.
- A reference node with the same `body` name is excluded from `body_solid`: the volume is
  unchanged and the SCAD text does not contain it outside `%`.
- A blind pilot (cut with depth < standoff height) leaves the shell count at 1 and reduces the
  volume by π r² h.
- **Parity** (`skipUnless(ca.OPENSCAD)`, `$fn = 24` to keep CGAL fast): compile `scad_body` of a
  shell with one cut. The STL volume is within 0.5% of the manifold and the bbox within 0.05 mm.

## 8. How this moves the judges and the loop

| Gap | After this delta | First iteration the judges can see it |
|---|---|---|
| RC1 representation | cuts, shells, interior poses and datums exist and are tested | 002/003, once M8 + M12 emit a package |
| RC2 bodies | per-body solids and SCAD, 1 shell each, overlap measured | same (G1) |
| RC3 catalogue | 11 validated parts with datums. The catalogue the judges reported empty now exists and can also feed their references | 002 (judges can build M- volumes from part.json) |
| RC4 size leak | sizes are expressions over part params and spec | after M8 (cavity from contents) |
| RC5 package | — | M12 |
| RC6 error signal | — | M5 / M10 |

Verdict expectation for iteration 002's Run: still **WRONG** (assembly mode stops at
`not implemented: parse_spec`). Recommended Run for iteration 002, to be added as RUN.md 3.1b by
the implementer:
- the assembly **stub smoke** arm `E1-01_asm_s$SEED`, which takes seconds and only proves the CLI,
  the catalogue load and the gate;
- optionally, skip re-running the 90-minute cascade baseline. Its code path is byte-identical to
  iteration 001, so seed 0 is greedy and will reproduce the same slab. The judges may record
  "unchanged, see iter_001".

The hard-coding guard is green by construction: no new module contains a target literal or part
id.

## 9. Plan for iteration 002 (the walking skeleton, ARCHITECTURE.md section 7.1)

M4 (envelopes) + M7 (Python placement from enum choices) + M8 (tray + lid with screws only) +
M5-subset (`separable`, `inside`, `clear_of`, `aperture_count`, `seated`) + M12 (WritePackage:
base/lid STL, layout.json, self_report from the delivered STL) + a thin tree. The thin tree has
three steps:
- ParseSpec-lite: the LLM fills typed slots whose numbers must occur in the request.
- Catalogue alias lookup, with the LLM choosing among the top k.
- One LLM enum question per connector item for `edge`.

With these, the first judgeable package can move G0, G1, G2 and G5, and G3/G4 if the cuts are
right.

## 10. Notes for Robin (questions, never relaxations)

- The run used the working tree's ×10 retry caps (`cascade.TRANSLATE_ITERATIONS = 30` etc.). With
  them, the cascade spent its whole 90 minutes translating L1.1. This does not change any verdict,
  but cascade-mode runs now cannot finish within RUN.md's timeout.
- requirements.md 2.2 names the board part `perfboard_70x50`. The catalogue part is the
  parametric `perfboard` with `width = 70`, `depth = 50` from the request, so that V1–V3 reuse it.
  layout.json will record `{"part": "perfboard", "params": {...}}`. Judges should treat these as
  the same part.
