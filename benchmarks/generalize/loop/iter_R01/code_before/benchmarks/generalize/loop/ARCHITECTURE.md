# Target architecture: from one enclosure family to arbitrary printed assemblies

The generalization control loop moves the CAD agent from the one family it converged on (the Pico
keyer enclosure, `benchmarks/enclosure/loop`) to the train suite in `../designs/` (40 designs: enclosures,
brackets and mounts, housings, fixtures and adapters, combinations). This file is the **target**.
Implementers move the code towards it one milestone at a time. They refine it, with a ledger entry, when
the code shows a better path.

Inputs to read with this file:
- `../plan.json`: per design, its family, `capabilities` tags, catalogue parts and brief. Read only the
  `"split": "train"` entries. Held-out briefs in it are not design input.
- `../designs/<id>/requirements.md` and `design.json`: the request, the L1s and the L2/L3 grading tables.
- `../rubric.md`: the judge procedure (being written alongside this loop; until it exists, the judge
  grades against each design's requirements.md).
- `../parts/` and `../../enclosure/parts/`: the two catalogues. The agent loads both (section 3.1).
- `../../enclosure/loop/ARCHITECTURE.md`: the converged enclosure architecture. Its sections 3 to 7 are
  still true, and this file only says what changes.

Run commands are in `RUN.md`. Each iteration's history is in `LEDGER.md`.

---

## 0. Principles (Robin's; they override anything below)

1. **Control system, not a script.** The local 9B LLM is the controller for discrete choices. Python is
   the plant model and the sensor: geometry, millimetres, and a signed, typed error with margins. The
   LLM never invents a millimetre. It picks from enums Python generates. It maps typed slots to numbers
   that appear in the request text.
2. **No per-design code.** Agent logic holds no number, part id, body name, face or layout that is
   specific to any design, train or held out. Target numbers live only in `part.json` (datasheet data),
   in `design_rules.json` (generic values), and in request and requirement text. A design is never a
   branch in code. A capability is a generic rule that every design with the matching parts and words
   triggers. `test_no_hardcoding.py` guards this (extended in GM1).
3. **Derive, don't ask.** Decide anything derivable from the brief, a datasheet or engineering convention,
   and record it as an assumption with its uncertainty. Only real preferences go to Robin.
4. **Designed contact is never interference.** A part on its supports, a screw in its pilot, a bearing in
   its press-fit bore, a lid on its rim, a pin in its hinge knuckle: every rule that creates a contact also
   exempts it, by construction (enclosure 7.8: the exemption is grown by the check's clearance).
5. **Keep the converged enclosure working.** E1-01, V1, V2 and V3 are the regression set. Every
   iteration runs them (`run_suite.py --regression`). E1-01 must stay MEETS and V1–V3 at least CORRECT.
6. **Held-out isolation.** Nobody in the loop opens `../holdout/` or `holdout_results/`. Only the held-out
   score, as a number, reaches the ledger (section 8).
7. **Local models only, one at a time** (ornith-1.5:9b). Never `benchmarks/heldout.json`, never `.mcp.json`,
   no git commit or push.

## 1. Where the agent stands (measured against the code, 2026-10-24)

The converged tree is LoadCatalog → LoadRules → ParseSpec → Contents → ExposureCoverage → ChooseStack →
ArrangeContents → BuildEnvelopes → ChooseArchetype → DeriveFeatures → Build → Verify → RenderViews →
WritePackage (`assembly.build_assembly_tree`). The generic machinery is sound and is kept unchanged:

| Kept as is (generic already) | Where |
|---|---|
| part.json schema, alias lookup, datums, specimens, import gate R1–R8 | `parts.py` |
| feature graph: nodes, expressions, datum refs, manifold solids, SCAD per body, ghosts | `feature_graph.py` |
| typed checks with signed margins, `per_source`, grown exemptions, ligament, apertures | `assembly_checks.py`, `assembly.build_plan` |
| number extraction with ids, one number per slot, number coverage by construction | `assembly.ParseSpec`, `extract_numbers` |
| evidence-gated discrete choices (`text_evidence`), text coverage as an error signal | `assembly.ChooseStack`, `ExposureCoverage` |
| pre-scored discrete alternatives (no vote may pick a larger Python error) | `assembly.prescore` |
| placement with collision and grid sensors, board symmetries | `layout.py` |
| setpoint rule (limit + `design_margin`), circumscribed cut polygons | `assembly.setpoint`, `feature_graph` |
| package: STLs, SCAD, layout.json, self_report.json on the delivered meshes, matrix, renders | `assembly.WritePackage`, `RenderViews` |

What is enclosure-specific today. Each row becomes the generic rule on its right:

| Enclosure-specific today | Where | Generic rule it becomes | Milestone |
|---|---|---|---|
| One catalogue folder | `cad_agent --parts` | `--parts` is repeatable; first folder wins an id; byte-equal duplicates are silent, different ones are reported (**done in this step**) | GM0 |
| `CONTENT_KINDS = board, module, connector, generic`; fasteners only chosen by rule | `assembly.py:68`, `Contents` | Any catalogue kind may be content. A part's role comes from its **interfaces** (section 3.1), not its kind. A fastener the text names (G16: "two M5 bolts into drop-in T-nuts") is content with a quantity. Unnamed fasteners are still chosen by rule. | GM2 |
| Spec slots `board_width`, `board_depth`, `keepout_above/below`, `board_clearance`, `headroom` | `design_rules.json` `spec_slots` | Slots are **generated**: (a) every `from_request` param of every content part (`<part>.<param>`), (b) the generic slot set of the archetype family (data in `design_rules.json`: limits `max_x/y/z`, wall band, clearances, travel, angle), (c) one slot per relation number (offsets, travel, tilt). Number coverage and one-number-one-slot stay as they are. | GM2 |
| Enclosure frame = the board's longest edge, origin on the board top | ARCH 3.4, `layout.py` | The frame is the **primary reference's** frame: the content part with the most interfaces that relate to a printed body (ties: the largest datasheet volume). The board stays primary for every enclosure, so E1-01–V3 are unchanged. layout.json declares every pose. The judge normalises the frame. | GM2 |
| Arrangement = an edge of the board (`-X..+Y`) per connector | `ArrangeContents`, `layout.Placer` | Arrangement = one **relation** per interface, chosen from Python's enum: `face` (which outer face an axis leaves through), `against` (datum plane on datum plane), `coaxial` (axis on axis), `on_pattern` (hole pattern on hole pattern), `along` (offset along an edge or axis). Python solves poses. The board-edge enum is the `face` relation of a board connector. | GM2 |
| Standoffs and pilots under `board.HOLE` only | `derive_features` | `mount_holes` interface rule on **any** placed part with a `HOLE` axis list (Pi Zero, fans, LCD, OLED, servo tabs, NEMA 17 face): seat on posts, bolt through a plate, screw into a boss, or trap a nut, chosen by the relation and the fastener chain. | GM3 |
| Lid screws = 4 corner pilasters, the largest catalogue screw | `derive_features`, `lid_screw` | The closure rule of the `shell` archetype (screws / snaps / slide / hinge), with the fastener named in the text by evidence, else the rule default. | GM3, GM9 |
| Port cut from a plug sweep through a side wall | `derive_port_cut` | **Envelope aperture** through any face of any body (side wall, lid top, plate) for every interface whose envelope must leave the body: plug sweeps, view cones (displays, LEDs, camera lens), actuator travel (buttons, switches), bushings and shafts. Same sensors: insertable / clear, aperture count and oversize, ligament. | GM4 |
| `BODIES = ("base", "lid")`, one archetype `tray_lid + screws` | `assembly.py:69`, `feasible_archetypes` | An **archetype library** (section 4). Each archetype is a generator from (contents, relations, spec, rules) to bodies, adds and cuts, and declares its body roles and print orientations. Bodies are named by role, and the package writes one `<body>.stl` each. | GM5, GM7 |
| Print orientation per body name (`base`, `lid`) | `design_rules.json` `print_orientation` | Per body role, plus the generic rule "largest flat face down", sensed by a `printable` check (overhang, bed contact). | GM5 |
| KEEP_OUTS rows for board keep-outs, columns, plugs | `assembly.KEEP_OUTS` | The table stays the single place where an envelope role is consumed. It gains rows for each new generator: travel sweeps, rotation and tilt sweeps, view cones, airflow columns, hex-key columns, belt paths. A role without a row still raises. | GM4–GM10 |
| Text coverage: a named plug requires its connector exposed | `ExposureCoverage` | Any named **mating** part requires the interface it mates to be realised: a plug → its connector exposed, a bolt into a T-nut → the slot interface used, a duct over a spigot → the spigot built. | GM4 |
| Board grid conformance (perfboard) | `grid_check` | Unchanged. It is the `grid` interface of boards that have a `grid` block. | — |

## 1a. Measured baseline and plan refinements (iteration 001)

The first train Run (`iter_001`, code `72dbcfdfb8de`, SEED 1) produced **no geometry for any of the 40 train
designs**. Every run stopped before derive: 19 at parse_spec (required `board_width` / `board_depth` slots), 18 at
contents ("exactly one board" or no board candidate), 1 at arrange (a perfboard invented under a camera), and 2
crashed at derive_features (lid screw rule chose a 1/4-20 screw with a request-only length). The regression set
passed (E1-01, V1, V2 MEETS; V3 CORRECT 0.99, closed height from a cross-stage number reuse). Full analysis:
`iter_001/delta.md`.

Refinements to the plan below. Each is generic, and each has a ledger reason:

1. **GM1 is closed by the baseline plus two guards folded into GM2a**: (b) `test_no_hardcoding` reads both
   catalogues, (c) an offline E1-01 test on both catalogues. The import gate was already clean (65 parts load).
2. **GM2 is split.** **GM2a (primary reference)** comes first, because it alone decides where 38 of 40 designs
   stop:
   - The primary is the **carrier** (a part with a `grid` block) when one is in the contents. Otherwise it is the
     **largest content part by catalogue plan footprint**, and it must offer a `mount_holes` interface (3.1),
     else the run stops with a typed note naming the missing support capability. This replaces section 1's
     "most interfaces" rule, which would make the Pico outrank the perfboard in E1-01.
   - The board size slots are optional. A request-sized primary takes its `from_request` params from them or
     from `ask_params`.
   - The primary's seat, top and holes come from its `mount_holes` interface, never from the datum names
     `TOP` / `BOTTOM`.
   - A non-carrier primary carries no other contents. Other items are `unplaced`, each with a failing
     `content_placed` check, until GM2b gives them relations.
   - Exposure is per connector, and a primary's own connectors are exposable (the wall follows from the axis).
   - **GM2b** is the rest of GM2: relation enums for secondary contents, any-kind contents, generated slots per
     archetype family, and prompts without enclosure framing.
3. **Archetype evidence gate (pulled forward from GM5).** `tray_lid` is feasible only with a mount_holes
   primary and text evidence of an enclosing body (`design_rules.json` `archetypes.tray_lid.evidence`).
   Otherwise the run stops at choose_archetype with a typed note, never with a wrong-family box.
4. **Fastener choice is evidence-gated and catalogue-robust (first slice of GM3).** A named fastener wins.
   Otherwise the largest *catalogue-complete* fastener (no `from_request` param) is used. "The largest catalogue
   screw" depended on which catalogues were loaded, and it broke when they were unified. Part errors inside
   derive are contained: the stage fails with a note, never with a traceback.
5. **One number, one slot across stages.** A number id owned by a spec slot and picked again by
   `Contents.ask_params` triggers the owner question, the same as inside ParseSpec. This is the
   generated-slots property of GM2, pulled forward for the request-sized parts that exist today.
6. **GM3 starts with the locating-pin relation** (a mount hole no catalogue screw passes: pin on post). Three
   train designs reach arrange after GM2a and stop there.
7. **Catalogue vocabulary rule:** no part alias may equal an archetype evidence word (`generic_box` loses `box`
   and `block`).

The milestone table in section 5 still holds. Its "Unlocked" column assumed geometry from GM2 on. GM2a is the
step that makes that true.

## 1b. Measured iteration 002 and plan refinements

Iteration 002 (code `b0a4f1abe322`, GM2a, SEED 2) produced 6 train packages (G02 G04 G06 G11 G13 G50). All 6 are
WRONG, so train MEETS 0 and CORRECT 0. 34 runs had no output, and every stop was a typed note. The regression set
**failed on V1** (DNM / MINOR: the jack on the opposite short end from the USB, though the text says "the same short
end"). E1-01, V2 and V3 are MEETS. Full analysis: `iter_002/delta.md`. Refinements, each with its ledger reason:

1. **A stated relation between exposed items is a sensor (first slice of GM2b's `face` relation).** Python's evidence
   gate is sentence-scoped: one sentence names both parts and has a relation word from `design_rules.json`
   `face_relations`. The gate limits the enum. The controller reads the relation. A unanimous reading becomes a
   controllable `face_relation` check, which prescore uses to remove violating arrangements. The edge vote and the
   p_yes rank stay as in enclosure 7.6. Why: V1 was lost at a p_yes near-tie (0.265 vs 0.254) that no sensor could break.
2. **GM3's fastener-chain sensors come before GM2b's secondary placement.** The judged packages lose their gates on
   pilots: the wrong board screw size (3 designs) and screws that bottom out (G02, plus E1-01 latently). Order:
   - **Board fastener:** a fastener the text names in a sentence with board role words (`fastener_roles`), if it passes
     the given hole; else the `mount_holes` interface's datasheet `thread`; else the smallest that passes (today's rule,
     which OWNER_DECISIONS fixes for the family perfboard).
   - **Pilot depth:** max(min_engagement, length − clamped plate) + margin, with a `pilot_bottoming` sensor.
   - **Cavity floor:** low enough that every standoff holds its pilot over `min_feature`.
   - Stock-length choice and the engagement-shortfall sensor stay in GM3 proper.
3. **Card-type access is a connector with a mating "plug" part** (`card_microsd`): a seated card plus a fingertip zone.
   No new interface kind is needed. The same pattern covers any slot a user reaches into.
4. **Any-kind Contents (GM2b) waits for the first relation that can place a secondary item.** Offering every named part
   moves 18+ stops but yields no geometry. On a carrier it would seat fans and displays on the board. It lands together
   with `against` / `on_pattern` (a fan on a lid) or with GM5's `plate` / `bracket`.
5. **Vents (GM4 slice) are the next shell capability** (G02's last gate after delta 002; G11 and G50 gates).
6. **The judge cache keys geometry by canonical triangles** (sorted, rounded), not STL bytes. OpenSCAD's facet order is
   not deterministic, so the byte key never hit.

## 1c. Measured iteration 003 and plan refinements

Iteration 003 (code `de77b7ab88b1`, delta 002, SEED 3): **regression pass** (all four MEETS, V1 fixed). Train MEETS 0,
CORRECT 1 (G04 0.99, one w1 bbox miss), 7 packages, 33 no-output, with stops as in iteration 002 apart from seed variance.
The ten designs that ran twice after a Run restart gave identical canonical geometry hashes. Full analysis:
`iter_003/delta.md`. Refinements, each with its ledger reason:

1. **The shell's closure and openings come before GM2b.** The judged packages fail on things the shell itself should
   do: bosses that break the size limit, a lid form the text names, vents, and a bridge nobody senses. That cluster moves 2
   verdicts (G02, G04). GM2b moves none until its items get apertures. Delta 003 therefore takes four slices out of order:
   - GM3: the screw closure through a generic rule (boss layouts);
   - GM9: the first closure beyond the lip (rebate);
   - GM4: vents;
   - GM5: the first `printable` sensor (bridge span).
   GM2b is next.
2. **Derive-level discrete alternatives are plant-scored, and only on failure.** When a derivation rule has several
   generic forms (here: outside pilasters, inside bands along X or along Y), the default is derived first. Alternatives are
   derived on scratch states and scored with the same controllable error key as prescore, but only when the default is
   infeasible or fails a controllable check it affects. A passing default is never re-derived, so converged designs stay
   byte-identical. This is the enclosure loop's 7.11 applied below the arrangement.
3. **A named region of a part is catalogue data: the `zone` interface** (point datum + size + long axis + names). The
   text's "over the ATmega328P" resolves through `names`, never through a datum name. Any future "above the SoC", "over
   the regulator" or "around the antenna" uses the same kind.
4. **Every derivation term that has a printability rule gets a sensor first.** `rules.bridge_max` existed with no reader.
   C4 adds `bridge_<cut>`, then the 45° roof. A stated text band, here the opening oversize, outranks a rules default.
   When both cannot hold, the failure is a typed `conflict`, never a silent violation of the text.
5. **Feature-graph primitive `prism`** (a convex polygon extruded). Roofs need it first, and GM5's gussets, chamfers and
   teardrops reuse it.
6. **Verdict form (tooling).** `run_suite` accepts a boolean `meets` as well as the `verdict` string. Iteration 003's
   regression was mis-reported `fail` by the old reader and re-cached in this step.

## 2. How a request maps to bodies, parts, features and checks (no per-design code)

The pipeline below is the target. Every arrow is a generic rule or a controller choice over a
Python-generated enum. No arrow reads a design id.

```
request + L1 text
  │ ParseSpec      number ids (with quotes) ──LLM maps──▶ generated slots (part params, archetype limits, relation numbers)
  │ Contents       alias runs over both catalogues ──LLM confirms──▶ parts + quantities + request-sized params
  ▼
interfaces         every content part's part.json `interfaces` (section 3.1) instantiated at its datums
  │ Relations      per interface, Python enumerates the feasible relations; evidence-gated; LLM picks among
  │                survivors after prescore (exposed through face k / against / coaxial / on_pattern / internal)
  ▼
archetype          Python enumerates archetypes whose required relations are present (section 4);
  │                prescore runs each through Derive+Build+checks; LLM ranks only the survivors
  ▼
features           one rule per (interface kind × relation × archetype) emits feature-graph nodes with
  │                expressions over datums, spec, rules and the chosen fastener chain
  ▼
envelopes          one generator per interface kind (plug sweep, travel, rotation, view cone, airflow, driver)
  ▼
checks             every feature rule emits the sensors for each L2 number it sets (enclosure 7.12:
                   every L2 needs a sensor); KEEP_OUTS turns envelopes into clear_of / inside checks;
                   every body gets separable, printable, min_wall, bbox, not_printed; links to L1s come
                   from slot provenance and named parts (trace matrix)
```

Three properties make this generic:

1. **Closed vocabularies, open combinations.** About 12 interface kinds, about 6 relation kinds and about
   8 archetypes cover all 40 train designs (section 5). A new design is a new combination of these. A new
   rule is justified only when two or more train designs need it. A rule only one design needs is held
   until a second one appears or Robin approves it.
2. **The catalogue carries the specifics.** Bolt patterns, bore diameters, view areas, actuator travel,
   plug envelopes and slot profiles are part data. Fit allowances (press, slip, sliding, clearance, captive
   nut, heat-set) are generic tables in `design_rules.json`. A rule reads both and holds neither.
3. **The controller's questions stay small.** Each question is an enum built from the request's own words
   and the feasible options, never a free-form design. Prescore removes any option with a larger Python
   error before the LLM sees it (enclosure 7.11). A run must finish inside the 20-minute timeout
   (RUN.md), so the question count per run stays near today's 13 to 20.

## 3. Data model changes

### 3.1 part.json: `interfaces` (schema 1, additive)

Datums stay as they are. A new optional list says what each group of datums offers a design. The load
gate checks that every entry names existing datums of the right kind, and that a `fit` names a row of
the rules' fit table:

```json
"interfaces": [
  {"id": "usb",   "kind": "connector",   "mouth": "USB_MOUTH", "axis": "USB_AXIS", "mates": "plug_microusb_b"},
  {"id": "mount", "kind": "mount_holes", "holes": "HOLE", "face": "PCB_BOTTOM", "keepout": "keepout_diameter"},
  {"id": "view",  "kind": "view",        "axis": "VIEW_AXIS", "area": "active_area", "face": "GLASS_TOP"},
  {"id": "bore",  "kind": "bore",        "axis": "AXIS", "seat": "HOUSING_BORE", "fit": "press"},
  {"id": "shaft", "kind": "actuator",    "axis": "SHAFT_AXIS", "bushing": "BUSHING_TOP", "travel": "rotate"}
]
```

- `connectors[]` of the enclosure catalogue are read as `connector` interfaces, so no existing part file
  has to change for the regression set.
- Until a part has `interfaces`, a loader shim derives the obvious ones (connectors, `HOLE` lists) and
  writes a note. It never guesses from datum names beyond these two.

Interface kinds, prioritised by the train designs that need them:

| Kind | Datums it needs | Relations offered | Feature rule | Envelope | Sensors (each L2 number) |
|---|---|---|---|---|---|
| `mount_holes` | axis list + seat plane | seat on posts · bolt through · screw into boss · trap nut | posts + pilots / clearance holes + counterbore / bosses / nut traps (fastener chain) | head + driver columns, seat columns | seated, pilot band, engagement, bottoming, ligament, hex-key reach |
| `connector` | mouth point + axis + `mates` | exposed through face k · internal | envelope aperture | plug sweep | insertable, aperture count / oversize, ligament, plug_refs |
| `view` | axis + area (display, LED, lens, sensor) | window through face k · light pipe | window cut = area + margin; bezel | view cone | window covers area, aligned, ligament |
| `actuator` | axis + top / travel (button, switch, encoder, pot) | through face k (cap / bushing hole / lever slot) | panel hole with thickness ≤ bushing length; plunger cap | travel sweep | travel clear, panel thickness band, nut thread engagement |
| `pocket` | outline (any part: magnet, battery, camera PCB, servo body, generic box) | pocket from face k · cradle · clip | pocket = outline ⊕ fit; retention lip or press | insertion sweep | fit band, retention, ligament, floor thickness |
| `bore` | axis + seat (bearing, rod, tube, shaft) | press · slip · clear · clamp | bore with fit; split clamp with preload gap | rotation sweep | fit band, coaxial, wall round bore |
| `slot_profile` | slot faces (2020 extrusion) | mount on face k with T-nuts | locating tongue + clearance holes on the slot line | bolt column | slot engagement, bolt length into T-nut |
| `airflow` | axis + inlet / exhaust faces (fans) | duct to · vent through face k | flange + loft / vent grid | airflow column | flow area, open fraction, wall ≥ min |
| `grid` | board grid | (placement only) | on-grid placement | — | grid_conformance |
| `drive` | pitch circle / belt plane (pulley, belt, gear) | mesh with · run on · guard | centre distance; guard shell | belt path, tip-circle sweep | centre-distance band, clear |
| `joint` | axis (dowel pin, bolt as pivot, print-in-place) | hinge · pivot · slide | knuckles / pivot bosses / rails | rotation or slide sweep | rotation clearance, end play, engagement |
| `fastener` | axis, head bearing, tip / seat | member of a chain | clearance / pilot / insert hole, counterbore, nut trap | driver column | engagement, bottoming, head bearing on material |

### 3.2 design_rules.json (generic values only)

- **Fit table** (`fits`): `press`, `transition`, `slip`, `sliding`, `clearance`, `captive_nut`, `heatset`,
  each as a diametral allowance band for FDM with its source. The enclosure's `sliding_fit*` keys stay and
  become the `sliding` row's alias, so the regression set reads the same numbers.
- **Archetype slot sets** (`spec_slots` grouped by archetype family). The enclosure's slot list becomes the
  `shell` family's set, unchanged, so E1-01–V3 parse as before.
- **Print orientation per body role** (`print_orientation` keyed by role, not by body name).
- New generic limits as each milestone needs them (overhang already exists: `overhang_angle_deg`,
  `bridge_max`). Every value carries a source.

### 3.3 AssemblyState

- `relations: Dict[str, dict]`: the chosen relation per interface instance, with `by` (llm / rule /
  prescore) and evidence. This replaces `choices.edge[...]`, which stays as a view for the shell archetype.
- `bodies: List[str]` from the archetype, not `BODIES`. `OPEN_BODY` becomes "the body the archetype marks
  as `open_view`".
- Package: `<body>.stl` per body, layout.json lists bodies with role and print orientation. The regression
  set still writes `base.stl` and `lid.stl`, because the shell archetype names its bodies that way.

## 4. Archetype library

An archetype is a generator, like `tray_lid` today. It declares the relations it needs, its bodies with
roles and print orientations, its slot set, and its feature rules. `feasible_archetypes` returns those whose
needs are met. Prescore runs each one, and the LLM ranks the survivors.

| Archetype | Bodies (roles) | Triggered by | Train designs (examples) |
|---|---|---|---|
| `shell` (tray + lid; closures: screws, snaps, slide, hinge) | base, lid (+ door) | contents inside, apertures on faces | G01–G14, G50 |
| `plate` | plate | a mount_holes / slot_profile pair, one flat body | G16, G20 |
| `bracket` (L, gusseted, corner) | bracket | two mounting planes at an angle | G17, G21, G22 |
| `block` (housing with bores, pillow block, carriage) | block (+ cap for a split clamp) | bore interfaces | G18, G27, G31, G37 |
| `cradle` / `fixture` (pockets, pins, holder) | base (+ cradle) | pocket interfaces, drill guide | G23, G38, G40, G41, G45, G47 |
| `revolved` (adapter, spigot, duct, knob) | one body from a profile | coaxial bores of different sizes, airflow | G29, G30, G36, G42, G43 |
| `joint_pair` (hinge leaves, chain links, pan-tilt) | 2+ bodies with a joint | joint interfaces | G33, G35, G49 |
| `clip` (snap clip, tube clip, clamp) | clip | a bore with a snap or clamp relation | G24, G26 |

Archetypes compose. A shell with a hinge lid is `shell` with the `hinge` closure. A fan duct is `revolved`
with a `mount_holes` flange. Composition is by the relations present, never by a design id.

## 5. Capabilities: what each train design needs, and the build order

Counts are over the 40 train designs of `../plan.json` (held-out entries excluded). "Touches" is the number
of train designs with at least one of the milestone's capabilities. Because the rubric weights every L3 row,
a design scores partial credit before all its capabilities exist. "Unlocked" is the cumulative number of
train designs whose every capability tag is covered once that milestone is done.

| Capability (train designs) | Count |
|---|---|
| datum_placement | 19 |
| bolt_pattern | 16 |
| plug_envelope_opening | 14 |
| multi_body_assembly | 12 |
| standoffs, pocket_fit, tolerance_stack | 9 each |
| window, load_path, print_orientation | 8 each |
| sliding_fit | 7 |
| keepout_clearance, captive_nut | 5 each |
| snap_fit, vent_pattern, hinge, thermal_airflow, slot_engagement, bearing_press_fit, rotation_clearance | 4 each |
| panel_mount_bushing, shaft_clearance, counterbore, pattern_array, concentric_step, magnet_pocket | 3 each |
| screw_boss, lid_removable, button_actuation, stacked_boards, battery_retention, wall_mount, slot_adjust, clamp_preload, cable_routing, thread_boss, duct_transition, belt_geometry | 2 each |
| angled_face, panel_mount_switch, led_lightpipe, split_clamp, print_in_place_clearance, press_fit, gear_mesh_center_distance, drill_guide | 1 each |

Build order. Each milestone states its capabilities, how many train designs it touches, the cumulative
designs unlocked, and its done-when tests (unit tests with fake LLMs, no Ollama). **Every milestone keeps
the regression set and the full suite green.**

| # | Milestone | Capabilities | Touches | Unlocked | Done when |
|---|---|---|---|---|---|
| **GM0** | Loop tooling (**this step**): repeatable `--parts`, `run_suite.py`, judge cache, `cache_verdicts.py`, RUN.md, LEDGER.md | — | — | 0 | `test_generalize_suite` green; dry-run lists 40 train commands with both catalogues |
| **GM1** | Baseline and guards. (a) All 54 generalize parts pass the import gate (any failure is a catalogue fix, never code). (b) `test_no_hardcoding` scans both catalogues' ids and aliases, plus a generic numeric guard: any literal in agent modules that equals a number in a train request or a part.json and is not in an allow-list of generic constants fails. (c) A golden offline test for E1-01–V3 (scripted controller): layout.json poses and STL volumes stay equal within 0.01 mm unless a delta justifies the change. (d) First real Run on train, to measure where each design stops. | — | — | 0 | gate report clean; guard green on the iter_012 code; golden test green |
| **GM2** | Any-part contents, generated slots, primary-reference frame, relation enums (`face`, `against`, `coaxial`, `on_pattern`, `along`), interface instances from part data (shim for connectors and HOLE lists) | datum_placement, keepout_clearance, stacked_boards | 21 | 0 | ScriptedLLM: every train request reaches the relation stage with the right catalogue ids, quantities and slots; E1-01–V3 golden unchanged |
| **GM3** | Interface rules for holes and fastener chains: `mount_holes` on any part; bolt / screw / nut / heat-set chains from evidence; counterbores, nut traps, bosses, wall-mount keyholes; the shell's screw closure through the same rule | bolt_pattern, standoffs, screw_boss, counterbore, captive_nut, thread_boss, wall_mount, lid_removable | 28 | 0 | per chain: pilot band, engagement, bottoming, head bearing, ligament sensors; a fan's 4-hole pattern and a NEMA 17 face resolve from part data |
| **GM4** | Envelope apertures through any face (plug, view, actuator, bushing, shaft, vent), named-mating-part coverage | plug_envelope_opening, window, button_actuation, led_lightpipe, panel_mount_bushing, shaft_clearance, panel_mount_switch, vent_pattern, drill_guide | 20 | 4 (G02 G05 G10 G12) | a window on a lid top and an actuator hole through a panel get aperture count, oversize and ligament sensors; text coverage for every mating kind |
| **GM5** | Archetypes `plate`, `bracket`, `block`, `cradle`; `printable` (overhang patches, bed contact) and `min_wall` (ray cast) sensors; print orientation per role; load-path ligament (minimum section) | print_orientation, load_path, slot_engagement, slot_adjust, angled_face | 16 | 8 (+G06 G16 G17 G22) | each archetype derives for scripted relations; a printable check fails a 50° unsupported overhang and passes a 45° one |
| **GM6** | Fit tables and pockets: press / slip / sliding bores, pockets from outlines, magnets, batteries, pattern arrays, split clamp with preload gap, tolerance-stack sensors (worst-case band) | pocket_fit, tolerance_stack, sliding_fit, bearing_press_fit, magnet_pocket, press_fit, battery_retention, pattern_array, clamp_preload, split_clamp | 24 | 20 | a 608 bore measures inside its press band; a stacked chain of three fits reports its worst case |
| **GM7** | N bodies, `joint_pair`, joints (hinge, pivot, slide) with rotation, tilt and slide sweeps; cable channels | multi_body_assembly, hinge, rotation_clearance, print_in_place_clearance, cable_routing | 13 | 28 | a hinge pair clears through its full rotation sweep; designed contact at the pin is exempt |
| **GM8** | `revolved` archetype and lofted transitions (flange to spigot), airflow checks | concentric_step, duct_transition, thermal_airflow | 6 | 33 | a 45° transition passes printable; flow area sensor equals the hand formula |
| **GM9** | Shell closures beyond screws: snap (cantilever strain sensor), sliding lid or door, hinged lid | snap_fit | 4 | 37 | snap strain within the rules band; a sliding door clears its travel sweep |
| **GM10** | Drive geometry: belt path, pulley guard, gear centre distance | belt_geometry, gear_mesh_center_distance | 3 | 40 | centre-distance band from pitch circles in part data |

Why this order:
- GM2 and GM3 touch the most designs (21 and 28) and everything else depends on them.
- GM4 comes before the new archetypes because it extends the existing shell, where 14 enclosure designs
  score most of their weight. It unlocks the first four complete designs.
- GM6 touches more designs (24) than GM5 (16), but pockets and bores need the archetypes that carry them.
- Snap fits (4) and drive geometry (3) are last by count. G01, the simplest enclosure, waits for GM9. It
  still scores partial credit from GM2–GM4.

The gap analyst may reorder milestones when the measured error signal (the judges' defects) says so. The
reason goes in the ledger.

## 6. Error signal and judging

- **Train verdicts** come from judges grading each package blind against the design's requirements.md and
  `../rubric.md`. A verdict is `{"verdict": "MEETS" | "DNM", "class": "CORRECT" | "MINOR" | "WRONG",
  "score": 0..1}`. MEETS counts as CORRECT.
- **Judge cache.** A verdict is reused when the same design produces byte-identical STLs and its
  requirements.md, design.json and the rubric are unchanged (`run_suite.py`, key = id + geometry sha1 +
  spec sha1). Judges spend time only on new geometry. A rubric edit invalidates every cached verdict.
- **The agent's own verdict is never the loop's verdict** (rc 0 / 3 are reported, not graded).
- **Gap analysis** maps each defect to (a) a missing sensor, (b) a missing or wrong generic rule, (c) a
  catalogue error, or (d) a controller error. The enclosure loop's audit rule holds: when a judge finds
  something the agent did not sense, the fix is a generic sensor first, then the derivation term.
- **Every real-run failure becomes an offline replay test** (enclosure 7.6), keyed by capability, not by
  design id. The test may load a train design's request text as data.
- **Overfitting guard.** A delta is justified by the capability it adds and by the number of train designs
  it moves. A change that improves one design and is worded for that design is rejected at review.

## 7. Regression set

E1-01, V1, V2 and V3 run every iteration with `run_suite.py --regression`, which is exactly the enclosure
loop's RUN.md command (enclosure catalogue only, `--num-ctx 8192`). Judges grade them against the enclosure
rubric. The bar is the converged one: E1-01 MEETS, V1–V3 at least CORRECT. Byte-identical geometry is
graded once and then cached. Offline, the GM1 golden test catches most regressions before any Ollama time is
spent. Once the catalogues are unified (both catalogues on every run), the regression command also runs with
both, and the ledger says from which iteration.

## 8. Held-out protocol

- The held-out designs measure generalization. No implementer, analyst, judge of train runs or reviewer
  reads `../holdout/` or `holdout_results/`, and no train judge sees a held-out verdict (held-out verdicts
  go to `holdout_results/judge_cache.json`).
- A held-out Run happens only on a frozen version: the train iteration's `code_sha1.txt` must equal the
  held-out iteration's (`summary.json` `code.matches_train_iter`). It runs at most once per milestone, and
  never twice on the same version.
- An isolated runner and isolated judges handle it. Only one number reaches the ledger: the held-out CORRECT
  share (`holdout_score`). No defect list, design id or verdict text comes back into the loop.

## 9. Convergence (proposed; Robin may change the numbers)

The loop stops when, on one agent version (same `code_sha1.txt`, which covers both catalogues):
1. The regression set passes (E1-01 MEETS, V1–V3 at least CORRECT).
2. At least 80% of the train designs are CORRECT on two seeds, with no train design that was CORRECT on an
   earlier version now WRONG without a ledger justification.
3. `test_no_hardcoding` (extended in GM1) and the full suite are green.
4. One held-out measurement on that version is recorded in the ledger as a number.

**Assumption (derived, not asked):** 80% is a starting bar from the enclosure loop's own experience: a
CORRECT-class variant rate came only after the error signal covered every L2. Its uncertainty is high, and the
first full train Run (GM1) recalibrates it.
