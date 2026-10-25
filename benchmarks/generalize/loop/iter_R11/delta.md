# Migration delta R11 (building blocks): generic, catalogue-driven plant blocks with typed actions and sensors

**Renumbered at the merge.** Developed as "R03 (building blocks)" in the worktree `agent-a0e0cb1c8fb79628a`; merged into
the main tree on top of R02 as **R11**, the next id not planned in ARCHITECTURE.md 10.8 (R03 there is the `set_fastener`
conversion, R04–R10 are planned too). In code, registry, tests and this folder every mention of this delta now says R11;
"R03" in sections 1–9 below is the historical name, except where it names the fastener conversion. Section 10 is the
merge.

**Owner decision:** D1 (`../OWNER_DECISIONS.md`). Implemented 2026-10-25 in an isolated worktree branched from `4c7d496`
(nothing committed). claude-context failed to connect this session (the MCP server did not start), so files were found
with targeted reads and grep. Nothing under `../../holdout/` or `../holdout_results/` was opened, listed or searched;
`benchmarks/heldout.json` and `.mcp.json` were not touched. (A `git archive` of `4c7d496` into the scratchpad, used for
the pre/post regression comparison, contained the held-out folder; it was deleted unread.)

**Note on the name.** ARCHITECTURE.md 10.8 plans an R03 that converts `rule:text_evidence[board]` / `[lid]` into a
`set_fastener` actuator. This delta does not do that (both stay `pending_migration`, registry unchanged for them); it was
commissioned as "R03: generic building blocks" because most train designs stop before the controller can act. The
fastener conversion should be renumbered (or this delta renamed) when the two lines merge.

---

## 1. Failure tally (iterations 004 and 005, train split, LLM runs)

Read from the main tree's `iter_004/runs.jsonl` and `iter_005/runs.jsonl` (last row per design), `stage` + `last_note`:

| Stop | Reason | iter 004 | iter 005 | Designs (iter 005) |
|---|---|---|---|---|
| contents | "nothing to design around: the answer puts no catalogue part in the request" | 17 | 18 | G16 G17 G18 G20 G21 G22 G24 G27 G29 G30 G31 G32 G33 G35 G36 G38 G42 G45 |
| contents | "primary X has no mount_holes interface; its support (pocket / ribs / bolt-through) is not implemented" | 6 | 4 | G03 G05 G09 G47 |
| contents | "<request-sized part>: no number in the text for ..." | 7 | 6 | G01 G10 G12 (generic_box, perfboard), G26 G43 (generic_tube), G37 (gear) |
| arrange_contents | "no catalogue screw passes the board's mounting holes" | 1 | 1 | G14 |
| choose_archetype | "no shell evidence; candidates for GM5: plate / bracket / block / cradle" | 4 | 4 | G23 G40 G41 G49 |
| done (package) | | 5 | 7 | G02 G04 G06 G08 G11 G13 G50 |

Root causes behind the stops, from the transcripts (e.g. iter_005 `G16_s5/.../004_assy_contents.txt`):

1. **Candidates (18 + 3 of the 4 "no mount_holes")**: the Contents question offered only electronics kinds
   (`CONTENT_KINDS`) plus named parts with a mount_holes interface. A NEMA 17 motor, a 2020 extrusion, a bearing, a fan,
   a servo, a battery, a toggle switch, a pot were never offered, so the 9B could only answer 0 (G16's list: two jacks, a
   box and a capacitor). G09 picked the DC jack as primary because the battery (kind `power`) was not offered.
2. **No support for a holeless primary (4)**: ESP32 boards, an HC-SR04, a battery.
3. **One unsizable part kills the run (6)**: the 9B adds a request-sized generic part whose size the text does not state.
4. **No screw passes the Nano's holes (1, and G01/G10 once they get past contents)**.
5. **No non-shell archetype (4, and most of group 1 once they get past contents)**.

Ranking by designs unblocked (offline simulation with the R03 code: Contents answers every named admissible part, every
connector exposed, spec slots "none", scripted controller taking the first offered action;
`scratchpad/simulate.py`, numbers in section 4):

| Block | Unblocks past its stop | Reaches a package (sim) |
|---|---|---|
| 1. Contents admission | 19 designs offered the parts they name (all of group 1 that names a catalogue part, + G09 G47) | — (moves the stop) |
| 2. Cradle retention (+ screw fallback, + non-board primaries) | G03 G05 G09 G12 + G01 G10 G14 | 7 |
| 3. Unsizable part rejected, not fatal | G01 G10 G12 (+ G37's motor once 5 exists) | (with 2) |
| 4. Panel mount (bushing / lens through the lid) | places parts in G01 G09 G10 G12 G50 | (improves 5 packages) |
| non-shell archetype (plate / bracket / block) | G16 G18 G20 G21 G23 G24 G29 G31 G36 G40 G41 G45 G47 G49 (14) | not landed (section 7) |
| duct / loft | G29 G30 (both also blocked upstream: tube outer diameter not in the text; the 60 mm fan's wording matches no alias) | not landed |
| pin hinge / joints | G33 (+ G09 lid, G35, G38) | not landed |

## 2. Blocks landed (each: plant + typed action + sensors + tests)

### Block 1 — Contents admission (plant / controller information)
`building_blocks.admissible_named`: every catalogue part the request or an L1 names by a part.json alias run
(`assembly.named_parts`) is a Contents candidate unless it is an **accessory** read from catalogue cross-references
(`accessory_ids`: a plug some connector `mates`, a stack option some mount offers, a `fastener`). The controller answers
its quantity as before (0 = not in the design). The regression texts get exactly their old candidate lists
(test `test_regression_candidates_unchanged`; their Contents prompts are byte-identical).
Plus `bb.supportable` in the primary-reference rule: among the content items, the largest footprint **the plant can
hold** (mount_holes or a seat interface) is the primary; a lying cylinder (an 18650 cell) is not supportable, so G08
keeps its Pico as primary and lists the cell as unplaced.

### Block 2 — Cradle retention for a primary without (usable) mounting holes
- **Interface shim** (`parts.seat_interface`, `parts.support_names`): a part with no mount_holes interface offers a
  `seat` interface read from its plane datums only: `seat` = the −Z plane with the largest flat geometry area resting on
  it, `top` = the lowest +Z plane above it. A mount_holes part is unchanged.
- **Plant** (`cradle_plan`, `derive_cradle`, `rule:cradle`): ledges under the edges (strips `support_ledge_width` inside
  the outline, minus the part's own primitives / keep-outs below the seat, e.g. an ESP32's pin tails), a locating rim at
  the sliding fit (`retention_wall`, up to `min(top − seat, pocket_rim_height)`, broken where an overhanging feature
  such as a USB receptacle comes within `board_clearance`), and the option's feature: **crush ribs** (one per
  `crush_rib_pitch` per rim piece, `crush_rib_interference` into the outline between seat and rim top) or **snap
  clips** (two cantilever arms + hooks over the top face on the first opposite pair of sides whose hook strip is clear
  of every primitive and keep-out; strain 1.5 t y / L² ≤ `snap_strain_max`, else infeasible). Every contact is a `seat`
  envelope (designed contact: clear_board, inside_board, the keep-outs exempt exactly these volumes).
- **Proposal**: the vocabulary's default option (`design_rules.json building_blocks.retention`, `pocket`),
  `rule:default_retention` (plant, reads no text).
- **Action** `set_retention(board, option)` (invalidates derive) over the options the plant can build here; an option
  that cannot be built is not offered and is named with the plant's reason in the sensor's detail (e.g. G03:
  "snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets header_a, keepout header_pins_a
  ...)").
- **Sensors**: `retention_board` (worst designed free travel over ±X ±Y ±Z ≤ `retention_play_max`; controllable,
  actionable; −z from ledges, ±X/±Y from rim/ribs else the measured gap to the wall, +z from ribs/hooks else up to the
  split), `supported` (measured on the base body: base top under every ledge at the seat, ledges span the plan
  centre), `rib_interference_*` (measured: overlap volume of the rib with the part's reference solid / rib face area,
  in the band), `snap_strain_*` (exact ratio), `snap_overlap_*`. All run on the manifold solids and on the delivered
  STLs (`assembly_checks.EXTRA_CHECKS`). Review fixes: `retention`, `snap_strain_*` and `snap_overlap_*` (and
  `panel_thickness_*`) are **design checks** (values from the plan; evidence `basis: design`), not measurements; the
  others carry `basis: measured`.
- **Screw fallback** (`cradle_instead_of_screws`, `rule:no_screw_fits`, guardrail): a primary whose mounting holes no
  catalogue screw passes (the existing board-screw guardrail) is held by the cradle on its mount seat plane instead of
  stopping (G01, G10, G14: Arduino Nano).

### Block 3 — An unsizable part is rejected and reported, not fatal (plant + sensor)
`Contents` / `bb.report_unsized`: a part the answer put in whose request-sized params have no number in the text is
dropped from the design (as an infeasible action is rejected) and listed as unplaced; its existing `content_placed`
check fails with the reason. Until R03 one such part stopped the run at Contents. A primary that cannot be sized still
stops. (`set_param` for its size stays R08.)

### Block 4 — Panel mount (plant + action `set_panel` + sensors)
For a content item whose catalogue `mount.type` is `panel` (LED, EC11 encoder, RK09 pot, MTS-102 toggle) and that the
primary does not carry (a failing `content_placed`):
- **Geometry from primitives** (`panel_geometry`): the body (largest plan area) stops against the panel's inner face at
  its top; the primitives above pass through a hole of their largest plan size; the axis is the mount's `hole_axis`.
- **Action** `set_panel(item, lid)` (invalidates derive); Python places nothing on its own. Walls are not derived yet.
- **Plant** (`derive_panels`, `cavity_z1_terms`, `rule:panel_mount`): the lid's inner face rises so the hanging body
  clears the primary's component keep-out by `part_to_wall` (a z1 term only when a panel decision exists); each copy
  at the first free spot nearest the lid centre inside the lip, clear of bosses, pads, vents, cuts and other parts; a
  through hole of the through diameter + 2 × `sliding_fit` in the lid.
- **Sensors**: `panel_keepouts_*` (the part's keep-outs above its contact plane — nut zone, lever swing, view zone —
  clear of every printed body, measured), `panel_clear_*` (part ≥ `part_to_wall` from printed bodies except its
  designed contact), `panel_board_*` (clear of the primary), `panel_seated_*` (measured: the lid's inner face meets the
  contact plane), `panel_hole_*` (clearance per side in the sliding-fit band; review fixes: measured on the built lid, it compared the designed diameter with itself before), `panel_thickness_*` (lid ≤ the part's
  `max_panel_thickness` when it declares one). Placed panel parts leave the `inside_contents` volume (they poke through
  the lid by design) and their `content_placed` check.

## 3. Every change, classified

| # | Change | Class | Files |
|---|---|---|---|
| 1 | Contents candidates: named non-accessory parts | plant (enumeration) / controller-information (menu) | building_blocks.py, assembly.Contents.candidates |
| 2 | Primary = largest *supportable* item | **semantic-rule, pending R05** (re-classed in the review fixes: it extends `rule:primary_reference`, which decides which part carries the others with no actuator; documentation only, behaviour unchanged; the registry justification says so) | assembly.Contents.choose_primary, bb.supportable |
| 3 | `seat` interface shim, `support_names` | plant (interface from datums) | parts.py, layout.Placer, parts.board_keepout |
| 4 | Cradle derivation, contact envelopes | plant (`rule:cradle`) | building_blocks.py; assembly derive_features/derive_cavity/build_envelopes/driver_columns guards |
| 5 | Retention default | plant (`rule:default_retention`) | building_blocks.retention_choice, assembly.derive |
| 6 | `set_retention` | actuator | building_blocks.retention_actions/apply_retention; controller.ACTUATORS/apply_action |
| 7 | supported, rib_interference (measured sensors); retention, snap_strain, snap_overlap (**design checks** on the plan's resolved numbers, evidence `basis: design`; relabelled in the review fixes, they cannot see a defect in the solids) | sensor / design check | building_blocks.py, assembly_checks.EXTRA_CHECKS |
| 8 | Cradle when no screw fits the holes | guardrail (`rule:no_screw_fits`) | building_blocks.cradle_instead_of_screws, assembly.ArrangeContents |
| 9 | keepout_top exempts the cradle's contacts (cradle primaries only) | sensor (designed contact) | building_blocks.add_cradle_checks |
| 10 | Unsizable part rejected, reported as content_placed | plant (feasibility) + sensor | assembly.Contents, bb.report_unsized |
| 11 | Panel placement, lid hole, z1 growth | plant (`rule:panel_mount`) | building_blocks.derive_panels/cavity_z1_terms; assembly hooks |
| 12 | `set_panel` | actuator | building_blocks.panel_actions/apply_panel |
| 13 | panel_* sensors (panel_hole measured on the built lid since the review fixes; panel_thickness a design check); panel refs out of inside_contents | sensor | building_blocks.add_panel_checks, assembly.build_plan |
| 14 | State words (retention, panel), decision vector, directions | controller-information | controller.state_words/decision_vector/DIRECTIONS (via BB) |
| 15 | design_rules.json: 18 generic values + `building_blocks.retention` vocabulary; `parts.Rules.building_blocks` loader | plant (generic values) | design_rules.json, parts.py |
| 16 | Registry: rule:default_retention, rule:cradle (plant), rule:no_screw_fits (guardrail), rule:panel_mount (plant) | guardrail on the loop | controller_rules.json |
| 17 | Scanned modules += building_blocks.py | guardrail on the loop | test_no_hardcoding.py, test_controller_authority.py |

No change is a semantic rule: no new code reads the request text. The judgement calls for the reviewer: (a) admission
uses the existing alias matcher (`named_parts`, the same reading `text_coverage` uses) only to *offer* candidates; the
controller still decides quantities. (b) The cradle fallback when no screw fits is classed guardrail (physics), not
plant. (c) The retention default is the weakest option on purpose, so the controller decides (by D1); a design whose
controller answers stop keeps a failing, honest `retention` check.

## 4. Measured

**Regression (offline, scripted, fn 24; the 9B's real Contents answer with the Pico's USB closed, the controller exposes
it; `scratchpad/regress.py`, same procedure on the `4c7d496` code and on the R03 code):** byte-identical.

| Text | Feature graph | layout.json | Canonical STL (run_suite.geometry_sha1) |
|---|---|---|---|
| E1-01 | 8b92655a7335 = 8b92655a7335 | 3ad6463ef436 = | 604a70a3c664 = 604a70a3c664 |
| V1 | d3f0568e3724 = | 0dba0461bd16 = | bf2c1ab4b7a3 = |
| V2 | b28b47d23080 = | d726ddecfd37 = | 36b8057cffcc = |
| V3 | a74bb4efb7b2 = | d510d6c6ffce = | f5a168cb9fdf = |

(These equal R01's documented hashes, so the regression packages stay judge-cache hits.) No live regression run was
made; the regression Contents prompts are byte-identical (test), so the 9B sees the same questions.

**Offline simulation of all 40 train designs** (R03 code; section 1's assumptions): packages for G01 G02 G03 G04 G05 G06
G08 G09 G10 G12 G13 G14 G22 G27 G50 (iteration 005 had 7). New: G01 G03 G05 G09 G10 G12 G14 (cradle / panel / unsized)
and G22 G27 (a shell, because the archetype text gate finds "block"/"box"-family words: the wrong form, a gate problem
for R07). Still stopped: G16 G18 G20 G21 G23 G24 G29 G31 G36 G40 G41 G45 G47 G49 at choose_archetype (no non-shell
archetype), G17 G32 G37 at derive (a NEMA 17 as a shell primary: its rear-cable keep-out covers every ledge strip, so
the cradle is honestly infeasible), G11 (jack as primary, no seat plane), and G26 G30 G33 G35 G38 G42 G43 (no catalogue
part named).

**Live (ornith-1.5:9b, seed 5, wording 2 = iteration 005's settings; `run_suite.py --iter 903/904 ... <ids>` in the
worktree, folders moved to `live/`).** Batch 1 ran while the panel and unsized blocks were still being written (G03,
G05, G12, G09, G01); batch 2 on the final code:

| Design | iteration 005 | R03 live (batch 2) | Controller steps (votes) | Still failing |
|---|---|---|---|---|
| G03 | contents (no mount_holes) | **rc 0, verified, STLs** | expose usb (3/3), set_retention crush_ribs (3/3) | — |
| G01 | contents (generic_box unsized) | **rc 3, STLs** | expose usb (3/3), set_panel LEDs lid (3/3), set_retention crush_ribs (3/3) | content_placed (the rejected unsized box), bbox |
| G12 | contents (generic_box unsized) | **rc 3, STLs** | expose usb (3/3), set_panel LEDs lid (2:1), crush_ribs (3/3) | content_placed (rejected box), apertures ×4 (lid-boss pilots open into the wall slabs; the 9B mapped board_clearance = 3 mm; not attributed to R03, see 6) |
| G14 | arrange (no screw passes the Nano's holes) | **rc 3, STLs** | expose usb (3/3), crush_ribs (3/3) | content_placed (buzzer: not a panel part) |
| G09 | contents (jack primary, no mount_holes) | **rc 3, STLs** (batch 1 too) | set_panel toggle lid (3/3), then stop (3/3) over crush_ribs | retention (stop chosen), DC jack and dowel unplaced, text_coverage, bbox (battery stands upright) |
| G10 | contents (perfboard unsized) | contents: the 9B again put in a perfboard, which became the (carrier) primary and has no size | — | — |
| G05 | contents (no mount_holes) | arrange: the 9B put in a perfboard (carrier primary) and the ESP32 has no room on it | — | — |

So 5 of the 7 designs now get past Contents and produce STLs (G03 self-verified); in iteration 005 all 7 stopped at
Contents or Arrange. Across both live batches the controller answered 15 menu questions: 14 corrections, all kept (none undone, none
infeasible), and 1 stop (G09, over crush ribs). G05 and G10 are Contents answers of the 9B (an extra carrier board), which is R05's correction
problem.

## 5. Tests

New `test_building_blocks.py` (23 tests): admission (accessories from catalogue references; named mechanical parts are
offered; regression candidate lists unchanged), seat interface (seat/top from plane datums, lowest top, no top → none,
mount_holes parts unchanged), cradle end to end (proposal pocket fails retention at +z with the rim at the sliding fit;
menu = buildable options only, the infeasible one named with its reason; controller crush ribs kept, every check
passes, ribs measured in band, contacts as seat envelopes, no standoffs or board screw, audit has no unregistered name;
the full tree with OpenSCAD verified on the STLs), a battery primary, a holeless primary without a top plane stops
typed, unsized part rejected and reported, screw fallback (rule:no_screw_fits), snap clips sized (long sides first,
strain formula, hooks above the top face with the gap, rim slots) and chosen end to end by the controller, a short arm
infeasible by strain, value/ratio/measured sensors, panel geometry from primitives, LEDs mounted in the lid by the
controller (3 copies, holes, keep-outs, seated, every check passes), a threaded-bushing part with its panel-thickness
limit and nut zone (and the lid raised above the board's keep-out), no panel decision → no cavity term, registration.

Changed on purpose: `test_assembly.TestPrimaryReference.test_primary_without_mount_holes_stops_typed` (marked "changed
in migration delta R03": the holeless G05 module is now the cradle primary with the seat interface; a holeless part with
no seat/top plane pair still stops typed). `test_no_hardcoding` and `test_controller_authority` scan building_blocks.py.

Also changed on purpose after the full run: `test_assembly.TestFasteners.test_board_screw_through_given_hole` (a Ø1.5
hole no screw passes now gives a cradle, `support[board]` by `rule:no_screw_fits`, instead of the arrange stop) and
`test_assembly.TestNumberOwnership.test_part_size_reask_is_final` (the final re-ask's typed stop now rejects only that
part: it is unplaced with the same typed reason, and the run goes on).

RUN.md 2 full suite (14 modules incl. test_building_blocks) on the final code: **515 tests, 513 OK, 2 failures (1740 s)**
— exactly the two tests above, whose expectations encoded the pre-R03 stops; after updating them, both classes re-run
green (`TestFasteners`, `TestNumberOwnership`: 5 tests OK) and `test_building_blocks` 23 OK, `test_controller_authority`
+ `test_no_hardcoding` 11 OK. (An earlier full run on the code before blocks 3–4: 492 tests, 1 failure, the T3 test.)

## 6. Known limitations, risks and open questions

- **Not landed** (ranked by section 1): a non-shell archetype (plate / bracket / block) would take 14 more designs to a
  package, but every such form choice runs into the archetype text gate (`rule:only_feasible`, semantic, pending R07);
  adding a plate as "the form when the shell gate fails" would be a new decision derived from that gate, so it belongs
  with R07's `set_form`. Duct/loft (G29, G30) is blocked upstream (tube outer diameter not in the text; the 60 mm fan's
  wording matches no alias). Pin hinge (G33) names no catalogue part. Panel mounting on walls (G50 front panel, G09's
  jack end) is not derived (lid only).
- **Admission changes prompts**: designs that name more catalogue parts get longer Contents prompts, and the seeded 9B
  answers differently (G05 got a perfboard at the same seed). Regression prompts are unchanged.
- **Primaries change**: with batteries and switches admitted, the largest supportable part can differ from before
  (G09: battery). G08's cell is not supportable (a lying cylinder), so G08 keeps the Pico.
- **Cradle geometry is box-based**: footprints are plan boxes of flat resting primitives; snap hooks have a flat
  underside (a ~1.25 mm overhang when the base prints open side up; no printability sensor yet).
- **Panel parts** are placed by a nearest-to-centre grid search; their positions are not requirement-driven (a text
  saying "beside the window" is not read; that would be a relation sensor + action).
- **G12's aperture failures**: the lid-boss pilots' regions count as through openings in all four wall slabs in that
  live package (spec board_clearance 3 mm from the 9B's mapping). Not reproduced offline yet; it looks like the corner
  pilaster geometry with an enlarged cavity, unrelated to the cradle or panel features, but it was not proven.
- **Name clash with ARCHITECTURE 10.8's R03** (the fastener conversion): see the note at the top.

## 7. Files changed and revert

| File | What |
|---|---|
| `building_blocks.py` | new: blocks 1–4 (plant, actions, sensors, controller registration) |
| `test_building_blocks.py` | new: 23 tests |
| `assembly.py` | delimited hooks, each commented "R03": candidates, primary choice, unsized parts, seat/cradle guards (primary_mount, build_envelopes, driver_columns, derive_cavity, derive_features, build_plan, add_fastener_checks, archetype_gate), screw fallback, panel hooks |
| `assembly_checks.py` | `EXTRA_CHECKS` registry and its dispatch in `run_plan` |
| `controller.py` | 9 lines: import BB; `ACTUATORS.update(BB.ACTUATORS)`, `DIRECTIONS.update(BB.DIRECTIONS)`; `apply_action` delegates BB.APPLIERS; `decision_vector` and `state_words` append BB's |
| `parts.py` | `seat_interface`, `support_names`, `Rules.building_blocks` + loader; board_keepout uses support_names |
| `layout.py` | Placer top plane via support_names (1 line) |
| `design_rules.json` | 18 generic values (support_*, retention_*, pocket_rim_height, crush_rib_*, snap_*) + `building_blocks.retention` |
| `controller_rules.json` | 4 entries (rule:default_retention, rule:cradle, rule:panel_mount: plant; rule:no_screw_fits: guardrail); about text |
| `test_assembly.py`, `test_no_hardcoding.py`, `test_controller_authority.py` | section 5 |
| `loop/RUN.md` | unit line += test_building_blocks |
| `loop/iter_R03/` | this file; `live/` (the two live batches) |

Revert: `git checkout 4c7d496 -- assembly.py assembly_checks.py controller.py parts.py layout.py design_rules.json
controller_rules.json test_assembly.py test_no_hardcoding.py test_controller_authority.py
benchmarks/generalize/loop/RUN.md` and delete `building_blocks.py`, `test_building_blocks.py`. The blocks are
independent enough to revert one at a time: block 4 = the `bb.derive_panels` / `bb.add_panel_checks` / panel lines in
`build_plan` and `derive_cavity`; block 3 = the `unsized` lines in `Contents`; block 2's screw fallback = the
`cradle_instead_of_screws` call in `ArrangeContents`.

## 8. Merge notes (the concurrent controller.py change)

- controller.py edits are registration only: the import, two `update` calls after `ACTUATORS`, one `elif` in
  `apply_action`, one entry in `decision_vector`, one in `state_words`. If the menu becomes content-keyed, the new
  actions' keys are `set_retention:board=<option>` and `set_panel:<item>=lid`; their words come from BB.
- BB's action builders import `controller.Action` lazily and construct it positionally `(kind, target, value, words,
  targets, invalidates, evidence)`; if `Action`'s signature changes, update `retention_actions` and `panel_actions`.
- Best-of-N / verifier search: the new actions invalidate `derive` (cheap re-runs); infeasibility shows as a derive
  ValueError ("retention <option>: ...", "panel <item>: no free spot ..."), which the existing infeasible path records.
- The StubController never acts, so stub runs keep the pocket proposal (a failing retention check) and unplaced panel
  parts: designs that self-verify only after a controller action (G03) are LLM-dependent by construction.

## 9. Assumptions (derived, not asked)

All new design_rules.json values carry a source (FDM practice / snap-fit guides); uncertainties: crush-rib
interference 0.15 mm (band 0.05–0.3, medium), snap strain limit 2.5 % (medium), retention play 0.5 mm (low impact: it
only separates "located" from "loose"), rim height 3 mm (low), ledge width 1.2 mm (low). No owner questions.

## 10. Merge with R02 (2026-10-25)

Applied as a 3-way merge (base `4c7d496`, ours = main tree with R02 + T01, theirs = the worktree) per file with
`git merge-file`; `assembly.py`, `assembly_checks.py`, `layout.py`, `parts.py` merged clean. Conflicts, resolved by hand:

| File | Conflict | Resolution |
|---|---|---|
| `controller.py` `apply_action` | R02 dispatches through the `APPLIERS` table; R03 added an `elif` chain | `APPLIERS.update(BB.APPLIERS)` (R02's table); the elif dropped. `BB.apply_retention` / `apply_panel` now take R02's `(st, action, record, by)` and record `by` (`llm:controller` or `search:controller`) instead of a literal |
| `design_rules.json` | both appended after `controller_menu_max` | R02's menu / search values and R03's 18 block values both kept; R02's `controller_menu_max` wording kept |
| `controller_rules.json` `about` | both added a scanned module | `menus.py, building_blocks.py`; the four R11 entries keep their classes (3 plant, 1 guardrail); the R02 "pending R03" entries are the fastener delta and were not touched |
| `test_controller_authority.py`, `test_no_hardcoding.py` | both added a module | both scanned |
| `RUN.md` | unittest line | `test_menus test_building_blocks` |
| `test_assembly.TestNumberOwnership.test_part_size_reask_is_final` | R02 changed the owner-question count to 2 (two orderings); R03 changed the outcome (part rejected, run goes on) | R03's outcome with R02's count 2 (marked in the file) |

Other merge fixes:
- **Action construction**: R02's `Action` is `(kind, target, value, words, targets, invalidates, evidence, ident)`; R03's
  7 positional args were compatible, but are now keyword args. The menu shows `Action.desc` (the words after the first
  ": "), which would have cut "hold the <part> with <option>" / "mount <item> (<part> xN) in the lid"; the words now lead
  with `<kind> <target>=<value>: `, so the menu line is e.g. `- set_retention:board=crush_ribs: hold the ... with
  crush_ribs: <meaning>`. Ids are R02's generic form: `set_retention:board=<option>`, `set_panel:<item>=lid`.
- **Menus**: retention and panel actions are controller actions, so they appear in R02's content-keyed, seeded-shuffled
  controller menu, are permutation-voted and searched like `expose`; the admitted Contents candidates go through R02's
  shuffled `assy_contents` menu (`menus.perm_tally`, keyed by part id). No block asks its own question.
- `test_building_blocks.py`: two scripted controller answers changed from letters (`"B"`) to ids (`stop`,
  `set_retention:board=snap_clips`), marked in the file; the stop test passed with "B" only because an invalid answer
  counts as stop.

Regression after the merge (offline, fn 24, the closed-USB Contents answer + scripted `expose:module_1.usb`, and the
exposed-USB answer; the same script on a scratch copy of the pre-merge R02 tree): identical.

| Text | Feature graph | layout.json (file sha1) | Canonical STL (run_suite.geometry_sha1) |
|---|---|---|---|
| E1-01 | 8b92655a7335 | 4536c7e83718 | 604a70a3c664 |
| V1 | d3f0568e3724 | d6e4f36c1f53 | bf2c1ab4b7a3 |
| V2 | b28b47d23080 | cec20509f13d | 36b8057cffcc |
| V3 | a74bb4efb7b2 | 44a000bdfac5 | f5a168cb9fdf |

Graph and STL hashes equal sections 4's (R01's) values. E1-01 at the default fn against `iter_R02/live/E1-01_s21`:
feature graph 8b92655a7335, layout.json 4536c7e83718, base.stl 90c88b8e1c90, lid.stl a35daa99c30a: all equal.
Full RUN.md section 2 suite on the merged tree (15 modules): 535 tests, OK (1739 s).
The live batches in `live/` ran on the pre-merge R03 code (lettered menus); no live run was made after the merge.

## Review fixes (2026-10-25)

Adversarial review of the uncommitted R02 + R11 changes (base `4c7d496`), fixed 2026-10-25. claude-context failed to
connect again (MCP server did not start), so files were found with targeted reads and grep. Nothing under the held-out
folders was opened; `benchmarks/heldout.json` and `.mcp.json` untouched; nothing committed.

- **B1 (blocking) infeasibility leaked into later forks' sensor typing**: `controller.run_loop` wrote
  `st.control["infeasible"]` inside the candidate loop, so later forks (copied by `fork_from`) typed text_coverage /
  closure_evidence as conflicts while `key` and `stop` did not; on G02 a rebate fork raising the violation by 1.0 was
  kept. Now every candidate forks from a pre-step snapshot (`fork_from(..., control)`, `evaluate(..., control=)`),
  infeasibility is collected locally, merged after the loop, and the current design (recorded as
  `error_before_retyped`) and every feasible fork are re-measured under the merged typing before `accept` and best-of-N.
  Test: `test_menus.TestSearch.test_infeasible_candidate_does_not_retype_later_forks` (the repro: rebate now `undone`,
  stop selected).
- **2 search budget**: `controller_search_max_evals` is a hard cap (`search_candidates` no longer guarantees one
  evaluation; the loop stops before asking once it is spent, reason "search evaluation budget spent"); a confident
  `stop` is the only candidate whatever `menu_consistency_min` is. Tests: `test_eval_budget_limits_the_candidates`
  (changed), `test_total_evaluations_never_exceed_max_evals`, `test_confident_stop_ends_the_loop_whatever_the_consistency_threshold`.
  design_rules.json source text and ARCHITECTURE.md 3a updated.
- **3 checks that could not fail**: `panel_hole` is measured on the built lid (cross-section at mid-thickness around the
  axis, nearest edge minus the through radius; runs on solids and STLs); retention free travel, snap strain, snap
  overlap and panel thickness are relabelled **design checks** (evidence `basis: design`; measured ones carry
  `basis: measured`). Tests: `test_building_blocks.TestSnapClips.test_panel_hole_is_measured_on_the_lid`, `test_value_sensors`.
- **4 tie rule**: `menus.decide` docstring now states the behaviour (earliest valid tied answer, ordering 0 first; an
  invalid answer is never a candidate); `perm_tally` moves the invalid (None) count last so `majority` never picks it
  on a tie. Tests: `test_tie_goes_to_the_earliest_valid_tied_answer`, `test_perm_tally_invalid_answer_never_wins_a_tie`.
- **5 stale param_stop**: reset after a rejected unsized part in `Contents.update`. Test:
  `test_assembly.TestNumberOwnership.test_rejected_part_does_not_leak_its_stop_reason`.
- **1b registry/docs**: `search:controller` in controller_rules.json `decision_tags` (test
  `test_every_decision_tag_the_controller_records_is_registered`); R11 section 3 row 2 re-classed as extending the
  pending semantic `rule:primary_reference` (R05), registry justification extended (documentation only);
  `bolt_m5_iso4762` already handles `length` parametrically like the other bolts (`from_request`, gate sample 16 mm), left
  as is; its tap-drill source text said M4, corrected to M5.
- **6 test quality**: `test_assembly.TestArrange.test_iter003_replay_menu_overrides_the_edge_vote` replays iteration
  003's answers with an arrangement-menu answer that differs from the edge vote's class: `llm:menu` decides.
- **Measured**: full RUN.md section 2 suite (15 modules) **544 tests, OK (1714 s)** (535 + 9 new). Offline regression
  (`scratchpad/regress.py`, fn 24, E1-01 / V1 / V2 / V3, exposed and closed-USB + scripted expose): feature graph,
  layout.json and canonical STL hashes identical to the merged tree (E1-01 graph 8b92655a7335, layout 4536c7e83718,
  STL 604a70a3c664).
