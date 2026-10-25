# Target architecture: `--mode assembly` (the enclosure-designing agent)

The enclosure control loop builds this agent. It is the **target**: implementers move the code
towards it one milestone at a time, and they refine it (with a ledger entry) when the code shows
that a better path exists. Robin's agreed design direction is kept. The parts below that are
"refined against the real code" say where and why.

Inputs to read alongside this file: `../requirements.md` (L1/L2/L3, reference models M-, envelopes
V-, assumptions A1–A17), `../rubric.md` (judge procedure, measurement recipes, verdict),
`../enclosure.json` (E1-01) and `../variants.json` (V1–V3). The run commands are in `RUN.md`;
the history of each iteration is in `LEDGER.md`.

---

## 0. Principles (from Robin; they override anything below)

1. **Control system, not a script.** The local LLM is the *controller* for discrete choices.
   Python is the *plant model and the sensor*: it owns geometry, continuous math, placement in
   millimetres, and a signed, typed error signal with margins. The LLM never invents a millimetre
   value. It picks from enums that Python generates, and it fills typed slots whose numbers must
   appear in the request text.
2. **No hard-coding of the box.** Agent logic contains no number, layout, face or part that is
   specific to E1-01 or a variant. Target numbers live **only** in `parts/<id>/part.json` (datasheet
   data) and in the request and L1 text. Generic process rules (FDM fits, overhang angle, fastener
   pilot sizes) live in one reviewed data file (`design_rules.json`, section 4.5). A unit test
   enforces this (`test_no_hardcoding.py`, milestone M0).
3. **Local models only** inside the agent (ornith-1.5:9b main; qwen3.5:9b and gemma4:latest are
   allowed as judge-panel members; gpt-oss:latest is allowed but measured weaker). Never a cloud
   model. Only one process may use Ollama at a time.
4. **References are never printed.** The perfboard, Pico, jacks, plugs and envelopes exist for
   checks and ghost renders only. A test asserts that no reference node reaches a body's STL
   (`not_printed`).
5. **Existing modes keep working.** `default` and `cascade` behaviour and their tests stay
   unchanged, except for the listed pilot bug fixes (M0b), each with a regression test.
6. Do not look for Robin's hidden design. Do not open `benchmarks/heldout.json`.

## 1. What exists today (measured against the code, 2026-10-24)

| Area | Today | File:line | Consequence for E1-01 |
|---|---|---|---|
| Representation | flat `Design.components: List[Component]` with `shape` from `SHAPES` (box, panel, wedge, cylinder, tube, sphere) | `cad_agent.py:222`, `:778`, `:827` | no cuts, no shells, no references |
| SCAD | one `union()` of every component | `scad_source`, `cad_agent.py:2095` | union only, so no openings or pilot holes |
| Placement | child on a parent's outside face; edge = left/center/right fractions | `attach_position` `:310`, `instance_fractions` `:762` | no mm offsets, no interior placement, no datums |
| Sizes | LLM fills every parameter; `AccountForNumbers` forces request numbers into some parameter | `:1947` | size leak: a cavity is not derived from what it holds |
| Bodies | one fused assembly, one `model.stl`/`model.3mf` | `EmitScad` `:2127`, `ExportModel` `:2910` | no separate base and lid |
| Parts | `MAX_COMPONENTS = 8` | `:71` | an enclosure with 4 standoffs + 4 bosses + walls + lid already overflows |
| Checks | 13 typed checks; `fits` is a 2-D drop of a stand-in box | `cad_checks.py:1326` | no clear_of / inside / apertures / printability |
| Cascade | L1 → frozen typed checks, inner monotone loop (deadbeat + neighbourhood search + LLM rank), outer CEGAR refinement, verification matrix | `cascade.py` | **reused**: ControlLoop, LoopReport, error_key, strictly_better, gates |
| Geometry engine | layer-2 solids in manifold3d mirror the SCAD shape library; parity test vs OpenSCAD STL | `cad_checks.py:616` | **reused** as the measurement engine |
| OpenSCAD | 2021.01 (CGAL only, no manifold backend) | `cad_agent.OPENSCAD` | `difference()` with many `$fn=64` cuts is slow: measure in manifold3d, compile with OpenSCAD only for the deliverable |
| LLM | `OllamaAgent`: schema-constrained JSON, `p_yes`, `vote`, judge panel (`--judges`), `seed_offset`, injectable `post` for fakes | `:563` | **reused unchanged**; tests use `ScriptedLLM` / `CascadeLLM` fakes |

Iteration 001 measured the baseline. Cascade mode ran in the working tree with ×10 retry caps
(`cascade.TRANSLATE_ITERATIONS = 30`, `cad_agent` FillParams/ExtractComponents at 30). It spent all
90 minutes translating L1.1 and produced a 90 × 74 × 4 slab. Cascade is not the vehicle for this
target: its representation cannot express the requirements, so more retries cannot help.

Known pilot bugs (fix in M0b, each with a regression test): `edge_cue` fires on "at its back edge"
(the word names the parent's edge, not a placement cue; `:1061`); `instance_fractions("ends_*", 3)`
returns 2 positions and drops a copy (`:762`); `cad_checks.satisfiability` abstains ("unknown") too
broadly whenever any accepted check fails on the provisional design (`cad_checks.py:2475`); the
size leak above.

## 2. Plug-in point: a new `--mode assembly`

- `cad_agent.main`: add `"assembly"` to `--mode` choices (`--mode enclosure` is accepted as an alias
  that maps to `assembly`). It requires `--l1`, like `cascade`. New options, all ignored by the
  other modes:
  - `--parts DIR`: the parts catalogue (default `benchmarks/enclosure/parts`). The catalogue is
    data handed to the agent, not code.
  - `--rules PATH`: generic design rules (default `design_rules.json` at the repo root).
  - `--with-models`: allow `ImportModel` to use mesh files found in `--parts` (the optional second
    arm). Without it, imported models are ignored even if present (primary arm).
- `Design` gets one new optional field `assy: Optional[AssemblyState]`, like `cascade`. Note that
  `Design.assembly` is already taken: it is the `.scad` path.
- `import assembly as assy_mod` lazily, as is done for cascade. `root = assy_mod.build_assembly_tree(design,
  llm, auto_approve=args.auto)`. On SUCCESS call `assy_mod.finalize(design, llm)`, which returns the
  outcome `verified | unsatisfied` and uses the same exit codes (0 / 3 / 1 / 2 / 130).
- `write_design_json` adds `record["assembly"] = d.assy.summary()` when present.
- `benchmarks/run.py`: add `assembly` to its `--mode` choices. The existing runner tests must pass.
- New modules. None of them is imported by `default` or `cascade` at import time:

| Module | Contents |
|---|---|
| `parts.py` | part.json schema and loader, catalogue lookup by alias, datum math, import validation gate (R1–R9), envelope generators |
| `feature_graph.py` | Node / Pose / Expr / Datum types, the expression resolver, manifold3d solids per node and per body, SCAD emission per body, ghost SCAD, JSON round trip |
| `assembly_checks.py` | the new typed checks (section 5) on manifold solids, returning `cad_checks.CheckResult`; mesh-based re-measurement of delivered STLs (rubric recipes) |
| `assembly.py` | `AssemblyState`, the behaviours, the tree, the loops, package writing, `finalize` |
| `design_rules.json` | generic FDM and fastener rules (no target numbers) |
| tests | `test_parts.py`, `test_feature_graph.py`, `test_assembly_checks.py`, `test_assembly.py`, `test_no_hardcoding.py` |

The new modules reuse `cad_checks.Check`, `CheckResult`, `error_key`, `strictly_better` and
`verification_matrix`. They also reuse `cascade.ControlLoop`, `LoopReport`, `translate_loop`'s
gating pattern (validation, non-vacuity, number coverage, back-translation) and
`cad_agent.OllamaAgent`, `Step`, `ForEach`, `run`, `render_openscad`, `compile_scad` and
`HumanReview`. New check types go in their own registry `assembly_checks.CHECKS`, so cascade's
offered types (`cascade.METHOD_TYPES`) do not change.

## 3. Data model (the blackboard)

```python
@dataclass
class AssemblyState:
    spec: EnclosureSpec            # numbers taken from the request/L1 text (with provenance) + rules defaults
    contents: List[ContentItem]    # what goes inside, resolved against the catalogue
    frame: Frame                   # enclosure frame: X = board's longest edge, Z up, origin rules (section 3.4)
    layout: Dict[str, Pose]        # declared pose of every reference part (written to layout.json)
    graph: FeatureGraph            # reference / body / add / cut / envelope nodes
    choices: Dict[str, str]        # discrete decisions + who made them (llm | rule | human), e.g. archetype
    checks: List[Check]            # frozen check set (rule-derived + translated)
    results: List[CheckResult]     # latest measurement
    reports: List[LoopReport]      # inner / middle / outer loop endings
    assumptions: List[str]         # EstimateAndFlag + rules defaults used where the text is silent
    history: List[dict]            # accepted moves with error keys (monotone)
```

### 3.1 Parts catalogue: `parts/<part_id>/part.json`

The `parts/` folder is empty today. Milestone M1 creates it. Schema (version 1):

```json
{
  "id": "rpi_pico2", "schema": 1, "units": "mm",
  "names": ["raspberry pi pico 2", "rpi pico2", "pico 2", "pico2"],
  "kind": "module | board | connector | plug | header | fastener | generic",
  "source": "datasheet URL / document and section",
  "params": {"width": {"default": null, "from_request": true}},          // parametric parts (perfboard, generic_cylinder)
  "datasheet_size": [51.0, 21.0, 1.0], "size_tolerance": 0.2,
  "geometry": [ {"id": "pcb", "primitive": "box", "size": ["...exprs..."], "at": [0,0,0]},
                {"id": "usb", "primitive": "box", "size": [...], "at": [...]} ],
  "datums": { "USB_MOUTH": {"kind": "point", "at": [...]},
              "USB_AXIS":  {"kind": "axis", "at": [...], "dir": [-1,0,0]},
              "PCB_BOTTOM": {"kind": "plane", "at": [...], "normal": [0,0,-1]},
              "HOLE": {"kind": "axis_list", "at": [[...],[...]], "dir": [0,0,1], "diameter": 2.1} },
  "connectors": [ {"name": "usb", "mouth": "USB_MOUTH", "axis": "USB_AXIS", "mates": "plug_microusb_b",
                   "overhang_datum": "USB_MOUTH"} ],
  "mount": {"stack_options": ["header_male_2p54", "header_female_2p54"], "stack_datum": "PCB_BOTTOM"},
  "grid": {"pitch": 2.54, "origin": [...]},                              // boards only
  "pins": {"kind": "axis_list", "at": [...]},                            // for grid conformance
  "keepouts": [ {"id": "component_side", "primitive": "box", "size": [...], "at": [...]} ],
  "model": {"file": "pico2.stl", "units": "mm", "transform": [...], "datum_map": {...}}   // optional, second arm
}
```

The catalogue parts are the ones `variants.json` names: `perfboard` (parametric width and depth, with
hole inset, hole diameter and grid from part data), `rpi_pico2`, `header_male_2p54`,
`header_female_2p54`, `jack_3p5_pj320a`, `plug_microusb_b`, `plug_trs_3p5`, `generic_cylinder`
(parametric, sized from the request, for V3's capacitor), and fasteners `screw_m2p5_selftap`,
`screw_m3_selftap` and `heatset_m2p5`, with pilot, clearance and head diameters from fastener
tables. Plug parts carry the overmold and shaft geometry. Every number cites its source.

**Import validation gate** (`parts.validate`): bbox in mm vs `datasheet_size` (this catches ×25.4 and
×1000 unit errors and swapped axes), datum directions are unit vectors, connector datums lie on
the geometry, R1–R8 from requirements 2.4. For imported meshes (second arm only) also R9: the
imported bbox and datums match the catalogue part within 0.3 / 0.2 mm. A part that fails the gate
is not used. The failure is reported, and `CatalogLookup` falls back to the parametric part.

### 3.2 Feature graph (`feature_graph.py`)

```python
@dataclass
class Node:
    id: str                       # "board", "pico", "jack_1", "base", "floor", "usb_cut", "standoff_3"
    kind: str                     # reference | body | add | cut | envelope
    primitive: str                # box | cylinder | tube | rounded_box | shell | prism(profile) | ring | sweep | part
    params: Dict[str, Expr]       # number or expression string
    pose: Pose                    # datum-relative placement
    body: Optional[str] = None    # add/cut: which body it modifies; body: itself
    role: str = ""                # floor, wall, lid_plate, lip, standoff, boss, port_cut, pilot, screw_hole ...
    part: Optional[str] = None    # reference: catalogue id
    source: str = "rule"          # rule:<name> | llm:<decision id> | human | estimate (provenance for corrections)
    free: List[str] = field(default_factory=list)   # params the inner continuous loop may move, with bounds

@dataclass
class Pose:
    at: str = "frame.origin"      # datum ref: "board.HOLE[2]", "pico.USB_MOUTH", "cavity.wall[-X].inner"
    offset: Expr3 = (0, 0, 0)     # mm, in the datum's frame or the world frame (flag)
    axis: Optional[str] = None    # align the node's +Z to a datum axis ("pico.USB_AXIS")
    project_to: Optional[str] = None   # project the point onto a face (usb_cut @ pico.USB_MOUTH projected onto wall[-X])
    rot_z: Expr = 0
```

- **Expressions** use a safe AST subset: numbers, `+ - * /`, `min`, `max`, `abs`, `ceil_to(x, step)`,
  dotted references `node.param`, datum references `node.DATUM[i].x` and `spec.*` / `rules.*`. Python
  resolves them in dependency order (topological sort). A cycle or a missing reference is a typed
  error naming the nodes. Example: `cavity.width = board.width + 2*spec.board_clearance`,
  `wall.height = floor.thickness + standoff.height + board.thickness + spec.keepout_above - lid.lip_overlap`.
- **Bodies** are emitted per body as
  `difference(){ union(){ <body base primitive>; <adds> } <cuts> }`. The adds and cuts are the nodes
  whose `body` field names it. A cut whose role is `port_cut` may target several bodies (when it
  crosses the seam). Each body is written as `base.scad`, `lid.scad`, and so on, plus `model.scad`
  (all bodies in the closed pose, references as `%` ghosts in their own colours) and
  `print_<body>.scad` (the body in its print orientation).
- **Measurement truth** is manifold3d. Each node becomes a `Manifold` built exactly like its SCAD
  (same `$fn`, same profiles). This is the same pattern as `cad_checks._solid_cached`, and the
  same kind of parity test is kept: OpenSCAD's STL volume and bbox must be within 0.5% and 0.05 mm.
- **Delivered meshes** come from OpenSCAD (`compile_scad(base.scad, base.stl)`). If CGAL takes
  longer than `OPENSCAD_TIMEOUT`, the STL is written from the manifold, and that fact is recorded in
  `design.json` (`"stl_source": "manifold"`). The final verification then re-measures the delivered
  STLs with the rubric recipes (`assembly_checks.measure_package`), so the self-report is about
  what the judge will load (L3.12.2.1).

### 3.3 Envelopes (generated, never drawn)

`parts.envelopes(state)` builds V- volumes from datums only:

| Generator | Inputs | Produces |
|---|---|---|
| `plug_sweep(connector, plug_part, clearance, travel)` | connector mouth and axis datums, plug geometry from its part.json | full-mate plug solid ∪ overmold swept outward along the axis past any wall (V-USB-PLUG, V-JACK-PLUG-k) |
| `board_keepout(board, above, below, minus_seats)` | board datums, spec heights | V-KO-TOP, V-KO-BOT |
| `column(axis_datum, diameter, z_from, z_to)` | hole axes | V-SEAT-k, V-HOLE-KO-k, V-DRIVER-k, V-LIDDRIVER-j |
| `install_sweep(assembly_refs, z_to)` | the plan silhouette of all references | V-INSTALL |
| `content_envelope(parts)` | Pico ∪ headers | V-PICO |
| computed: `cavity(bodies)`, `apertures(bodies, wall)` | the design's bodies | V-CAVITY, V-AP-* |

Heights, clearances and travel come from `spec` (request numbers) or `rules` (generic). They are
never literals in code.

### 3.4 Frame and naming (generic rules)

The enclosure frame puts X along the board's longest edge and Z up. The origin is at the board's
min corner, on its top surface (the board frame of requirements 1.1). Walls are named by outward
normal: `wall[-X]`, `wall[+X]`, `wall[-Y]`, `wall[+Y]`. The LLM sees them in words that Python builds
from the board params, for example "a short (50 mm) end". Python generates the words. The LLM
answers with an enum key.

## 4. Behaviour tree

```
cad_assembly (Sequence)
├── review_loop (Retry)                                   outer loop: requirements cascade
│   └── assembly_design (Sequence)
│       ├── ParseSpec              LLM fills EnclosureSpec slots; number-coverage gate; rules fill the rest (flagged)
│       ├── Contents (Sequence)
│       │   ├── ExtractContents    LLM lists items (enum catalogue ids + "other"), quantities, exposed ports
│       │   └── ForEach content → Selector
│       │         ├── ImportModel      only with --with-models and a valid mesh (gate R1–R9)
│       │         ├── CatalogLookup    alias match + LLM pick among top-k catalogue ids; params from request numbers
│       │         ├── AskHuman         interactive only; FAILURE under --auto
│       │         └── EstimateAndFlag  generic_* part sized from request numbers, else an estimate; added to assumptions
│       ├── ChooseStack            per module with stack_options: LLM picks enum (e.g. male headers vs sockets) from request words
│       ├── ArrangeContents        LLM: discrete edge / side / order per item (enums); Python: mm poses, grid snap, packing
│       │   └── PortsReachEdge     Python check + deadbeat shift; typed failure back to ArrangeContents
│       ├── BuildEnvelopes         section 3.3
│       ├── ChooseArchetype        Python generates feasible archetypes (tray+lid, clamshell, sliding lid) × closure
│       │                          (screws, snaps, slide); LLM ranks the feasible ones; best is tried first
│       ├── DeriveFeatures (Sequence; Python rules)
│       │   ├── CavityFromContents   cavity = hull(references ∪ keepouts) + clearances (the size-leak fix)
│       │   ├── ConnectorToCut       per exposed connector: wall it faces; cut = (plug envelope ∩ wall slab) ⊕ clearance
│       │   ├── MountHoleToStandoff  per board hole: standoff (OD and pilot from the chosen fastener part), height from keepout below
│       │   └── LidToFastening       lip / rebate with sliding fit; bosses + lid holes, or rails, or latches, per archetype
│       ├── Solve                  inner loop (no LLM): resolve expressions; deadbeat + sensitivity moves on `free` params
│       ├── Build                  manifold solids per body; OpenSCAD compile per body; measure; parity
│       ├── Verify                 run frozen checks L1→L2→L3 (cascade order); typed failures with margins
│       │   └── Correct (Selector)   numeric → Solve again | discrete → middle loop (LLM) | requirement → translator
│       ├── RenderViews            closed-pose views + ghost views + per-body print-orientation views
│       ├── Review                 local judge panel P(yes) on Python's English rendering of each L1 vs the matrix
│       ├── WritePackage           base.stl, lid.stl, *.scad, layout.json, self_report.json, design.json, matrix
│       └── AssemblyReview         HumanReview showing the matrix (auto-accepts under --auto)
└── ExportModel                    3MF of the closed assembly (bodies only), as in the other modes
```

**Translate** (requirements → checks) runs once after the first successful Build, as cascade does
after its provisional loop:

- (a) **rule-derived checks** come from the contents and the spec. Every exposed connector gets
  insertable + aligned + through + aperture-oversize + aperture-count. The board gets clear_of +
  seated + keep-outs. Every body gets separable, printable, min_wall and not_printed. These are
  generic consequences of "exposed", "holds" and "printed", so they are not hard-coded requirements.
- (b) **translated checks**: the LLM fills templates of the new check types for each L1, with the
  same gates as `cascade.gate_checks`. Non-vacuity uses feature-graph mutants (drop a cut, shrink the
  cavity, merge bodies, move a standoff).

The two sets are frozen together and written to `checks.json`.

### 4.1 Nested loops

| Loop | Who acts | Error signal | Moves | Acceptance / ending |
|---|---|---|---|---|
| inner (Solve) | Python only | Σ normalised violation of the continuous checks (`error_key`) | deadbeat on invertible margins (e.g. cut top Z, cavity length, standoff height); finite-difference sensitivity steps on `free` params within bounds | strict decrease only; ends converged / saturated (bounds hit) / stagnated, and reports which checks are uncontrollable by continuous params |
| middle (discrete) | LLM picks, Python proposes and pre-scores | typed failures with margins that the inner loop could not fix, for example "insertable(usb) d = −0.8 mm, depends on choice `edge[pico]`, `archetype`" | Python generates the discrete alternatives that touch the failing checks' `depends_on` choices (flip an item's edge, reorder along an edge, change stack, archetype, closure, boss placement, split height rule). Each alternative is run through the inner loop. The LLM ranks only the top `RANK_LIMIT` that tie on error | strict lexicographic decrease; `LoopReport` |
| outer (requirements) | LLM + gates | an L1's own check fails while its sub-checks pass, or the reverse (cascade CEGAR) | add or drop translated sub-checks; re-ask ParseSpec when a spec number has no source | the check set changes are bounded by a no-repeat set; the matrix shows any L1 that is not met |

None of the loops has a fixed iteration cap that hides a failure: each one ends with a typed
report. The wall-clock guard is the 90-minute run timeout in RUN.md. Internal patience limits are
named constants that are reported in `design.json`.

### 4.2 Arrangement (refined against the code)

Today the agent places by face + left/center/right. In assembly mode the LLM answers per content
item (Python fills the enums):

- `edge`: the board edge the item's connector faces (`-X | +X | -Y | +Y` shown as words with
  lengths), or `none` for items without an exposed connector;
- `group`: `same_edge_as:<item>` / `opposite_edge_of:<item>` when the request relates them;
- `order` along a shared edge (a permutation enum when there are 2–4 items).

Python then computes the mm poses:

- The connector mouth is placed at the board edge plus the catalogue overhang.
- Positions along the edge are spread inside the edge's free span. That span is the edge minus the
  hole keep-out columns. Spacing must be at least the spacing implied by the plug envelopes plus
  2 × clearance plus a minimum ligament from the rules.
- Items with a large footprint are centred in the free band. Pin datums snap to the board grid by a
  shift of at most pitch/2.
- Remaining collisions and hole-column intrusions are resolved by a 1-D shift.

Anything Python cannot resolve becomes a typed failure (`PortsReachEdge`, `collides`,
`on_screw_column`) sent back to the LLM with the alternatives that remain feasible. This replaces
fraction placement for references. It does not change the default mode.

### 4.3 Archetypes and closures

Each archetype is a generic generator from (cavity, contents, spec, rules) to body nodes plus add and
cut nodes with expressions:

- **tray + lid**: base = floor + 4 walls up to the split plane; lid = plate + locating lip.
- **clamshell**: the split plane passes through the port centres, and each half carries half of
  each cut.
- **sliding lid**: rails on two opposite walls plus an end stop.

Closures are: screws (bosses with pilots, and lid clearance holes coaxial with them), snaps, and
slide. The split plane is computed with the rule "above the highest port cut top plus the minimum
ligament, or through the port centres for a clamshell". Python generates only feasible combinations.
The LLM ranks them by fit to the request text.

### 4.4 Corrections selector (Verify → Correct)

1. **numeric** (a failing check is invertible or locally sensitive in a `free` param): Python
   applies the change. There is no LLM call.
2. **discrete** (it depends only on choices): middle loop.
3. **requirement** (a check is unsatisfiable by any reachable design, or a spec number has no
   source in the text): the translator / ParseSpec loop, with the cascade's satisfiability gate.
   After M0b, that gate abstains only when the provisional design is inconsistent *in the checks
   the candidate depends on*.

### 4.5 `design_rules.json` (generic only)

Generic FDM rules: sliding fit range, minimum feature, overhang limit and bridge length, bed size,
and the default print orientation per role. Generic clearances: plug-to-opening, board-to-wall
default when the text is silent, and the minimum ligament. Fastener selection: screws must pass the
board hole, which is read from part.json. Every value used in a design is recorded with its
provenance (`rules:<key>` or `request:"<quoted words>"`) in `design.json`, so the judge and Robin
can see which numbers were assumed.

## 5. New checks (`assembly_checks.py`)

Every check returns a `cad_checks.CheckResult` with `passed`, a signed normalised `margin` (≥ 0 passes),
the raw value and unit, `depends_on` = {nodes, params, choices}, evidence (location bbox,
intersection volume), and where it can, `d_margin/d_param` for each free param (for deadbeat). The
implementations follow `rubric.md` section 3, so the agent's numbers can agree with the judge's
numbers within 0.10 mm (L3.12.2.1).

| Check | Measures | Margin | Typical deps |
|---|---|---|---|
| `clear_of(bodies, volume, clearance)` | penetration volume, then `min_gap` | (d − c)/tol; penetration ⇒ −(pen^(1/3)+c)/tol | body nodes near the volume, cut sizes, cavity params |
| `inside(volume, cavity, clearance)` | volume outside the closed hull; min gap to solids and to the outside | (d − c)/tol | cavity params, wall offsets, split height |
| `aligned(cut, connector, tol)` | offset between the cut centre (from the mesh aperture) and the connector axis | (tol − offset)/tol | cut pose, layout |
| `insertable(plug_sweep, bodies, clearance)` | `clear_of` with the swept plug envelope | as clear_of | cut size and pose, wall thickness at the port |
| `through(cut, body)` | the cut passes fully through the body wall (aperture region exists, depth ≥ wall) | remaining wall depth | cut depth / pose |
| `aperture_count(wall, n)` / `aperture_oversize(wall, envelopes, max)` | apertures of a wall slab via `decompose()`; containment in the grown envelope | count difference; (max − excess)/tol | cuts on that wall |
| `min_wall(body, lo, hi)` | ray-cast thickness median and range on a 2 mm grid away from features | both-sided band | wall/floor/lid params |
| `printable(body, orientation)` | overhang patches (n_z < −cos 45°, off bed, minus exempt holes and bridges), bed contact, per-body bbox ≤ bed | worst patch area / limit | archetype, lip/boss geometry |
| `separable(bodies)` | each body is 1 shell, pairwise overlap ≤ 1 mm³ when closed | shells and overlap | archetype |
| `not_printed(ref)` | no reference node appears in any body's CSG; the STL volume equals the body-only volume | boolean as ±1 | graph structure |
| `seated(board, standoffs)` | board bottom to standoff tops; hole axes to pilot axes (least squares) | (0.10 − gap), (0.25 − residual) | standoff height and poses |
| `gap(face_a, face_b, lo, hi)` | face-to-face distance (lip fit, seam, inner length) | band | lip offset, cavity length |
| `pitch(nodes, axis, value, tol)` | axis-to-axis distances of copies | band | standoff poses |
| `layout_*` | datum direction, position and distance; grid residual; pairwise interference of references; plan bounds | per rubric | arrangement choices |
| `bbox(assembly, limits)` | closed outside size, X > Y | per axis | cavity, walls, bosses |
| `stable(..., force)` | 5° tilt and port pull (extends today's `stable`) | moment margin | footprint |

Agreement test (M5): for synthetic shells with known answers, each check equals the rubric
reference recipe within 0.02 mm.

## 6. Package (what the judge receives)

The workdir is `--out/<timestamp>/` (cad_agent always adds the timestamp folder). It contains:

- `base.stl`, `lid.stl` (closed assembly pose, enclosure frame, mm; one per body), `base.scad`,
  `lid.scad`, `model.scad` (all bodies plus ghosts), `print_<body>.scad`;
- `layout.json`: frame, the pose of each reference part with catalogue id and X, Y, Z, rot_z, and
  each body's print orientation;
- `self_report.json`: every `clear_of` / `inside` / aperture result measured on the delivered STLs;
- `design.json` (the existing record plus `assembly`: spec with provenance, contents, choices,
  assumptions, loop reports, `stl_source`), `feature_graph.json`, `checks.json`,
  `verification_matrix.md/.json`;
- `views/model_{iso,front,back,left,right,top}.png` (bodies), `views/ghost_*.png` (bodies
  translucent, references solid), `views/print_<body>_iso.png`;
- `model.3mf` (ExportModel) and `llm/` transcripts.

## 7. Milestones (in order; each is independently testable with unit tests and fake LLMs, no Ollama)

Each milestone must leave the full suite green:
`venv/bin/python -m unittest test_cascade test_cad_checks test_review_fixes test_cad_agent test_benchmark_runner`
plus the new test files. RUN.md is updated as soon as the CLI changes.

| # | Milestone | Done when (tests) |
|---|---|---|
| **M0** | CLI scaffold: `--mode assembly` (alias `enclosure`), `--parts`, `--rules`, `--with-models`; `Design.assy`; `assembly.build_assembly_tree` stub that writes design.json and exits 1 with "not implemented: <stage>"; run.py choice; `test_no_hardcoding.py` (scans `assembly.py`, `feature_graph.py`, `parts.py`, `assembly_checks.py` for target literals such as 70, 50, 51, 21, 4.9, 17.5, 32.5, 65, 45, 80, 60, 90, 40 as numeric literals and for target part ids) | parse tests; stub exit code; other modes byte-for-byte unchanged on existing tests; the hard-coding guard passes |
| **M0b** | Pilot bug fixes in the existing modes: edge cue "at its back edge", `ends` with 3 copies, satisfiability abstention scope, size leak guard in `AccountForNumbers` | one regression test each; existing tests unchanged, or a ledger justification for each change |
| **M1** | `parts.py` + catalogue files (section 3.1) + `design_rules.json`; loader, alias lookup, datum transforms, validation gate R1–R8 (R9 stubbed) | each part loads; bbox vs datasheet_size; a ×25.4 mesh and an axis-swapped mesh are rejected; datum consistency; perfboard params from (w, d) only |
| **M2** | `feature_graph.py` data model: Node, Pose, Expr resolver, datum references, projection onto faces, JSON round trip | topological order; cycle and missing-ref errors name the nodes; `cavity.width = board.width + 2*c` resolves; pose projection unit tests |
| **M3** | Geometry: manifold solid per node; body = difference(union(adds), cuts); SCAD per body; ghosts; parity with OpenSCAD (skipped if OpenSCAD is missing) | a plate with a round and a rectangular hole has the expected volume; a reference never appears in a body; SCAD vs manifold parity |
| **M4** | Envelopes (section 3.3) from datums | each V- volume's bbox equals the hand formula from the part data for a fixture board (R8) |
| **M5** | `assembly_checks.py`: all section-5 checks, margins, deps, sensitivities, `measure_package` on STLs | synthetic cases pass/fail at the boundary ± ε; agreement with the rubric recipes; typed evidence locations |
| **M6** | ExtractContents + content Selector + ChooseStack + ParseSpec (number-coverage gate, provenance) | ScriptedLLM on E1-01 and V1–V3 request texts gives the right catalogue ids, quantities, exposed ports, board size and stack; an invented number is rejected; under `--auto` AskHuman yields to EstimateAndFlag |
| **M7** | ArrangeContents + PortsReachEdge: enum prompts, Python mm placement, grid snap, packing, typed failures | E1-01 (ports on opposite short ends), V1 (two ports on one edge, envelopes disjoint), V2 (three jacks on a long side, spacing from envelopes), V3 (socket stack raises the USB datum) all place with the layout_* checks passing given scripted choices |
| **M8** | ChooseArchetype + DeriveFeatures rules (tray+lid with screws first, then sliding lid, then snaps) | for scripted contents and layout, the derived graph has one cut per exposed connector on the right wall, standoffs coaxial with the holes, bosses + lid holes coaxial, lip fit inside the rules band |
| **M9** | Solve (inner loop) with deadbeat and sensitivity moves on `free` params; monotone acceptance; LoopReport | a cut that starts too low converges; a too-thin wall is fixed; a bound hit reports saturated with the uncontrollable checks |
| **M10** | Translate: rule-derived checks + LLM templates for the new types with gates (validation, non-vacuity via graph mutants, number coverage, back-translation); freeze → checks.json | ScriptedLLM: E1-01's 12 L1s each get ≥ 1 accepted check; a vacuous check is rejected by a mutant |
| **M11** | Verify + corrections selector + middle loop (discrete alternatives pre-scored, LLM ranks ties) + outer refinement | fake failures route correctly (numeric / discrete / requirement); a wrong edge choice is corrected by the middle loop; the error is monotone |
| **M12** | Build + WritePackage + RenderViews (ghosts, print views) + verification matrix + self_report on delivered STLs | package manifest test (the G0 equivalent): every file in section 6 exists and parses; STL bbox in mm; self_report equals a re-measurement |
| **M13** | Full tree end-to-end with ScriptedLLM on E1-01 and V1–V3 (offline, no Ollama); Review with a fake judge panel; ExportModel | the agent's own frozen checks all pass on each request with correct scripted choices, so the Python pipeline can produce a passing design. Then the Run step measures the real 9B controller |
| **M14** | (optional, second arm) ImportModel: STEP→STL conversion once, datum_map, R9 gate, `--with-models` | an imported mesh with wrong units is rejected; a good one replaces the catalogue geometry for checks and ghosts only |

### 7.1 Build order: walking skeleton (refined in iteration 001)

Why this changed: iteration 001's judges showed that the judge signal stays flat (WRONG at G0–G5)
until assembly mode writes a two-body package. If the milestones above are done strictly in
order, the first judgeable package appears only after M13, about ten iterations of unchanged
verdicts. The order is therefore:

1. **Iteration 001 delta:** M0 + M1 + M2 + M3. This is the foundation: types, catalogue,
   geometry. M0b is deferred because none of its bugs is on the assembly path.
2. **Walking skeleton (next):** M4 + M7 + M8 (tray + lid with screws only) + an **M5 subset**
   (`separable`, `inside`, `clear_of`, `aperture_count`, `seated`) + M12, wired as a thin tree:
   - ParseSpec-lite: typed slots with number coverage;
   - CatalogLookup: alias match, with the LLM picking among the top k;
   - ArrangeContents: one `edge` enum per connector item;
   - DeriveFeatures, Build, WritePackage.
   This is the first point where the judges can move G0, G1, G2 and G5, and G3/G4.
3. **Then, to grow the error signal and the controller:** the rest of M5, M9 (inner loop), M6 in
   full, M10 (translate), M11 (corrections and middle loop), M13, and M0b when convenient.

Each step keeps the "done when" tests of the milestones it includes. A subset milestone states
which of its tests are deferred.

### 7.2 Part-frame conventions and data-only sanity checks (refined in iteration 001)

- Every part.json carries a `frame` text field that states its origin and axes:
  - board: origin at the min corner of the top surface;
  - module: origin at the PCB min corner, PCB bottom at Z = 0, primary connector toward −X;
  - header: origin at pin 0, spacer bottom at Z = 0;
  - jack: origin at the body min corner, mouth on +X;
  - plug: origin at the tip, mating along −X;
  - fastener: axis Z.
- The part-specific sanity checks (R2, R4, R5, R6) are `self_checks` entries in part.json
  (`{name, expr, value, tol}`), which `parts.validate` evaluates. This keeps their numbers out of
  `parts.py`.
- The board is the parametric catalogue part `perfboard`. requirements.md's `perfboard_70x50` is
  that part with `width`/`depth` from the request, and layout.json records it as
  `{"part": "perfboard", "params": {...}}`.

### 7.3 Conventions fixed by the code (iteration 001: M0–M3 implemented)

Status: M0, M1, M2 and M3 are implemented and tested (`assembly.py` stub, `parts.py`,
`feature_graph.py`, `design_rules.json`, 11 part files). M0b is still open. The code settled these
details, which later milestones must keep:

- **part.json additions to section 3.1:** `frame` (text); `size_of` (the geometry id that R1
  compares with `datasheet_size`; default the union of all geometry); `gate_params` (sample values
  for request-sized params, used only by the load-time gate, never as design values); an
  `axis_list` may be a generator `{start, step, count}` instead of an `at` list; `self_checks`
  entries take an optional `op` (`eq` default, `le`, `ge`), and `value` may be an expression.
  Part geometry primitives are `box` (`at` = min corner, `size`) and `cylinder` (`at` = centre of
  the start face, `d`, `h`, `dir`).
- **Expression names inside a part** are bare param names plus `<geometry id>.min_x|max_x|size_x|center_x`
  (and `bbox.*` for the union) and datum refs `NAME.x|y|z|dx|dy|dz|diameter|count`,
  `NAME[i].x`. A plane's normal is read as `dx|dy|dz`.
- **Feature-graph primitives** are built in a local frame centred in X and Y with the base at
  Z = 0: `box(x, y, z)`, `cylinder(d, h)`, `tube(od, id, h)`, `shell(x, y, z, wall, floor,
  open_top)` (floor 0 = open bottom, a ring), `part` (the part's own frame). `Pose.offset` is in
  the world frame, `rot_z` is in degrees and applied before `axis`. Face refs exist for `box`
  (outer) and `shell` (outer and inner).
- **The stub stage** is the behaviour `NotImplementedStage(stage)` (not `NotImplemented`, which
  would shadow the Python builtin). It sets `assy.stage` and returns FAILURE, so a stub run exits 1
  with `design.json` `outcome: "failed"`.

### 7.4 Refinements decided in iteration 002 (walking skeleton; see `iter_002/delta.md`)

- **The judged arm is assembly mode from iteration 003 on.** This replaces "switch at M13" in
  RUN.md §3.2.
  - Why: iteration 002 judged the frozen cascade baseline again. The output was byte-identical,
    so the loop ran open-loop.
  - A run that stops at `not implemented: <stage>` is judged G0 FAIL with that stage named.
  - The cascade arm runs only when its code path changes or the seed is not 0.
- **ParseSpec-lite interface.** Python extracts every number occurrence (with a context quote and
  its source, request or L1 id) into ids.
  - The LLM maps generic `spec_slots` onto those ids, or `none`. The slots are data in
    `design_rules.json`.
  - Number coverage therefore holds by construction. A `none` slot takes its rules default and is
    flagged as an assumption.
- **Split plane rule (§4.3).** The split is `board TOP + spec.keepout_above + rules.lip_engagement`,
  raised by `max()` if a port cut top plus `min_ligament` is higher.
  - The lid lip therefore stays above V-KO-TOP.
- **Screw-closure boss placement (§4.3).** The bosses are corner pilasters. Each axis lies on the
  diagonal out from each corner of the contents' plan AABB, at `boss_od/2 + spec.board_clearance`.
  - The lid carries coaxial pads and clearance holes.
  - Why: a boss inside a cavity sized by the board clearance would hit the board. Thickening the
    walls to hold it would break the 2 to 4 mm wall band.
  - The rule is generic: it is derived from clearances, not from one box.
- **Placement rules (§4.2, concretised).**
  - `rot_z` is computed from directions with `atan2`, never from literal angles.
  - The part's `size_of` face is flush with the chosen board edge, so connector overhang comes
    from part data.
  - Items on an edge are spread with equal gaps over the free span, which is the edge minus the
    hole keep-out columns.
  - Pins snap to the grid by at most pitch/2.
  - **ConfirmArrangement** (the first piece of the middle loop): Python words the arrangement and
    asks the LLM `p_yes`. On "no", Python tries the next feasible edge assignment from the finite
    set, ordered by votes.
- **Verify never blocks the package.** WritePackage always runs, and `finalize` decides between
  `verified` and `unsatisfied`.
  - `self_report.json` is `assembly_checks.measure_package` run on the delivered STLs.
  - The design.json components are generated from the graph, never from LLM text.

After M13 the loop's error signal comes from real runs (RUN.md) judged with `rubric.md`. Gaps found
by the judge become deltas against this file. A delta can add a milestone M15+, or refine a section
with a ledger entry saying why.

## 8. Convergence (from rubric section 7)

The E1-01 package **MEETS** on 3 runs with different seeds, **and** each of V1, V2 and V3 is at
least **CORRECT** on 1 run. The agent logic contains no target-specific number
(`test_no_hardcoding.py` green), and all unit tests pass.
