# Migration delta R12: structural forms as controller choices, the plate archetype, spec slots by form

**Owner decision:** D1 (`../OWNER_DECISIONS.md`). **Design:** `../ARCHITECTURE.md` section 4 (plate row), 3.1 (the
`bolt_face` and `engage` interface kinds) and section 10 (10.2 action rows, 10.6 ChooseArchetype row, 10.8: R07 marked
**partly done** by R12 — the archetype half; the closure half, `rule:default_closure`, stays pending — and a new R12 row).
**Base:** commit `d2d5fcd`, clean tree. Implemented 2026-10-25, nothing committed. claude-context failed to connect this
session (the MCP server did not start: "failed to connect"), so files were found with targeted reads and grep. Nothing
under `../../holdout/` or `../holdout_results/` was opened, listed or searched; `benchmarks/heldout.json` and `.mcp.json`
were not touched.

## 1. Why (evidence)

Iteration 090's live T01 (SPD flat-pedal adapter) stopped at ChooseArchetype: "not implemented: archetype (primary
cleat_shimano_sm_sh51; no shell evidence; candidates for GM5: plate / bracket / block / cradle)", after ParseSpec had
mapped the request onto enclosure-only slots (keepout_above, board_clearance, wall_min, ...). 14 train designs
(brackets / plates / blocks: G16 G18 G20 G21 G23 G24 G29 G31 G36 G40 G41 G45 G47 G49, `iter_R11/delta.md` section 1)
stop at the same gate. The gate was a semantic rule: a shell was feasible only when a sentence named an enclosure word,
and with several archetypes and no valid answer the first of Python's enumeration was taken.

## 2. The delta, item by item

### Item 1 — archetype choice moves to the controller (`forms.py`)
- **Plant feasibility** (`forms.catalogue_options`, `form_options`): Python enumerates every form the rules describe
  (`design_rules.json archetypes`: `tray_lid` = shell, `plate`), checks each from catalogue data only (shell: a primary
  with a mount_holes or seat interface; plate: a content part with a `bolt_face` interface and a fitting catalogue
  fastener chain, `plate.feasibility`), and with two or more candidates derives each on a scratch copy (`trial`): a form
  whose derivation fails is infeasible with the plant's reason. Every option and reason is recorded (`design.json
  assembly.forms`, notes "choose_archetype: <form> is not buildable: ...").
- **Controller**: one feasible form is `rule:only_feasible` (now plant); several are one content-keyed, seeded-shuffled,
  permutation-voted menu (`assy_archetype`, ids `shell` / `plate`, the forms' `meaning`s); no valid answer: every
  feasible form is measured (derive, manifold build, every check) and the lowest controllable error is kept
  (`prescore:archetype`, a guardrail tag). A scratch prescore run of a shell arrangement is tagged the same way
  (`choose_archetype_rule`; it never reaches the real state).
- **Sensors**: `form_evidence` (a text sensor, only when two or more forms are buildable: a buildable form's evidence
  words are named and the current form's are not; it reports the quotes) and `content_placed` of a part another form
  would place (the plate places the reference part its primary `engage`s).
- **Actuator**: `set_archetype:<form>` (invalidates the archetype stage) registered in `controller.ACTUATORS` /
  `APPLIERS`, so it goes through R02's menu, permutation vote and verifier search; ChooseArchetype keeps the controller's
  form when it re-runs (an unbuildable one makes the action infeasible with the reason).
- Retired: `rule:first_option[archetype]`, and for the record `rule:archetype_text_gate` (its decisions were recorded as
  `rule:only_feasible`). `archetype_gate` reads plant feasibility only.

### Item 2 — the plate archetype (`plate.py`, catalogue extensions)
- **Plant**: anchored on the primary's `bolt_face` (holes, face, head_seat or thread_depth, adjust ranges); the
  reference part it `engage`s is placed by the engage datums (`rule:engage_pose`) and the plate's underside lies on its
  mating plane; the chain is chosen from catalogue data (`rule:plate_fastener`: thread = the interface's, head fits the
  hole keep-out, stock lengths; the shortest stock length that engages the whole nut; for a tapped part — `thread_depth` —
  screws from the free face, the thinnest plate through which a stock screw engages ≥ `tapped_engagement_ratio` × d
  without bottoming); slots along the largest declared adjustment with captive hex nut channels (`rule:adjust_slot`),
  or the nut frame (see actions); the primary's engage keep-outs (a cleat recess) and its geometry above the face are
  cut, swept over its adjustment (`rule:recess`); the outline is the cuts plus `plate_wall_min`, at least the mapped
  `size_min` (setpoint), placed on a `position_step` grid nearest the core that keeps the mapped `ref_clearance` (or
  `design_margin`) from every non-contact reference keep-out swept over the adjustment shifts and its catalogue `sweep`
  (a release twist); the thickness is the largest of the fastener stack, the mapped minimum and, when the request states
  a load case (mapped `load_force`, `load_patch`, `strength`, `safety_factor`), the bending stress measured on the built
  section, up to the mapped maximum (`size_for_load`); the print orientation is the flat face with the least overhang
  (`rule:print_orientation`, guardrail).
- **Actions** (controller only; Python never adds them): `add_surface_feature:top=studs|pins` (vocabulary
  `building_blocks.surface_feature`: catalogue set screws in tapped holes, or printed pins; laid out by farthest-point
  sampling within the mapped count / height / edge bands, `rule:surface_feature`), `set_handedness:plate=mirror_pair`
  (when the engaged reference declares `mirror_pair`; Build writes `plate_mirror.stl`, layout.json declares the pair),
  `set_nut_retention:plate=frame` (vocabulary `building_blocks.nut_retention`; a hex trap stops a nut turning only while
  it slides one way, so a part adjustable in two directions needs a separate printed nut frame sliding in a pocket that
  covers both ranges, like a shoe's cleat nut plate; `rule:nut_frame`). Defaults: `rule:default_surface_feature` (none),
  `rule:default_handedness` (single), `rule:default_nut_retention` (channel) — plant, no text.
- **Sensors** (measured unless marked design): `clear_primary`, `clear_fasteners`, `clear_<primary keep-out>`,
  `clear_<engaged>` and `clear_<engaged>_<keep-out>` (contact keep-outs interference-only, others at the mapped
  clearance; swept), `travel_<axis>` (bolts, and the nut frame, swept over each declared adjustment axis; typed as a
  conflict only when no buildable retention option covers it), `bolt_engagement_*` / `bolt_tip_*` /
  `bolt_bottoming_*` (design), `nut_trap_*` (the channel or frame hole width across the slide at each nut's mid height),
  `nut_frame_turn` (design), `plate_size_x|y`, `plate_thickness`, `bearing_area`, `load_stress` (the section of the
  delivered mesh at the support edge, per outline edge, only with a stated load case), `printable` (and
  `printable_nut_frame`: downward faces steeper than `overhang_angle_deg`; flat ones grouped, span = diameter of the
  largest inscribed circle vs `bridge_max`), `surface_features` (design, only when a feature slot is mapped),
  `handedness` (the mirror image against the same swept keep-outs, or a declared pair), `bbox`, `form_evidence`,
  `content_placed`.
- **Catalogue** (clearly marked assumptions, UNVERIFIED markers kept; values already in T01 requirements.md section 3):
  `cleat_shimano_sm_sh51` gains interfaces `mount` (bolt_face: BOLT, MOUNT_FACE, head_seat BOLT_SEAT, thread 5,
  adjust fore_aft_range along X and lateral_range along Y) and `clip` (engage: SOLE_PLANE / CENTRE onto the pedal's
  SOLE_PLANE / CLEAT_CENTRE, keep-out `recess`); `pedal_shimano_pd_m520` gains the `CENTRE_PLANE` datum, a `mirror_pair`
  and a `sweep` on `crank_side` (release_angle about the cleat's vertical axis); `bolt_m3/m4/m5_iso4762` and
  `grub_m4_iso4026` gain `stock_lengths` (ISO preferred lengths); `nema17_motor` gains a bolt_face (FACE, HOLE, thread 3,
  thread_depth hole_thread_depth: the data its `mount` block already stated). parts.py: interface kinds `bolt_face`,
  `engage` with R9 gate checks, keep-out `sweep` and `mirror_pair` checks, engage cross-references, `fastener_role`
  (bolt / nut / stud from declared params), `stock_lengths`.

### Item 3 — generic spec parsing
`design_rules.json spec_slots.forms.plate` (15 optional slots: size_min/max, thickness_min/max, ref_clearance,
load_force, load_patch, strength, safety_factor, bearing_area_min, feature_count_min, feature_height_min/max,
feature_edge_min, feature_coverage_min; units, plausible `range`s, lo/hi `pair`s) and `unit_words`. ParseSpec asks the
shell slots always (unchanged) plus the slots of each candidate form a named part can anchor (`forms.candidate_forms`:
catalogue data — a named bolt_face part adds the plate); the questions' first sentence is the enclosure wording only when
the shell is the only candidate. The LLM maps, Python validates: a number whose unit word (`extract_numbers` now records
the word after each number) names another unit, a value outside the slot's band, or a lo > hi pair is re-asked (the
existing re-ask / owner-question path). The Contents question loses its enclosure wording under the same condition.
E1-01's slot set, prompts and mapping are unchanged (test).

## 3. Every change, classified

| # | Change | Class | Files |
|---|---|---|---|
| 1 | Form enumeration from catalogue data, trial derivations, reasons | plant (feasibility) | forms.py, assembly.archetype_gate |
| 2 | Archetype menu (content-keyed, shuffled, permutation-voted) | controller-information | forms.choose, assembly.ChooseArchetype |
| 3 | No valid vote → lowest measured error (`prescore:archetype`) | guardrail | forms.prescore_form |
| 4 | `form_evidence` sensor | sensor (text) | forms.add_form_checks / form_evidence_check |
| 5 | `set_archetype` (+ content_placed → set_archetype) | actuator | forms.archetype_actions / placing_actions / apply_archetype, controller.py |
| 6 | Retire `rule:first_option[archetype]`, the text gate; `rule:only_feasible` → plant | registry | controller_rules.json |
| 7 | Plate plant (engage pose, chain, slots, channels, recess, outline position, thickness, load sizing) | plant | plate.py |
| 8 | Print orientation by measured overhang | guardrail | plate.choose_orientation |
| 9 | Plate sensors (clear_*, travel_*, engagement, nut trap, size, thickness, bearing, load_stress, printable, surface, handedness, frame turn) | sensor / design check | plate.py, assembly_checks.EXTRA_CHECKS |
| 10 | `add_surface_feature`, `set_handedness`, `set_nut_retention` and their defaults | actuator / plant defaults | plate.py, controller.py |
| 11 | Mirror-pair STL, layout.json bodies (orientation, pair), design.json plate / forms | plant (package) | assembly.Build / WritePackage / summary |
| 12 | Interface kinds bolt_face / engage, sweep, mirror_pair, fastener roles, stock lengths | plant (catalogue loader + gate) | parts.py |
| 13 | Spec slots by form, unit / band / pair validation, neutral wording | controller-information + plant (validation) | forms.py, assembly.ParseSpec / spec_prompt / owner_question / Contents |
| 14 | Catalogue data (cleat, pedal, bolts, grub, NEMA 17) | data (assumptions marked) | benchmarks/generalize/parts/*/part.json |
| 15 | design_rules.json: 15 values, plate slots, unit_words, archetype meanings, 3 vocabularies | plant (generic values) | design_rules.json |
| 16 | State words (form, plate), decision vector | controller-information | controller.state_words / decision_vector |
| 17 | Scanned modules += forms.py, plate.py; new tests | guardrail on the loop | test_no_hardcoding.py, test_controller_authority.py, test_plate.py |

No new semantic rule: no new code reads the request text to decide. Judgement calls for the reviewer: (a)
`candidate_forms` uses the alias reading Contents admission already uses (`named_parts`) only to decide which slots are
offered; (b) `form_evidence` is a word-list text sensor (reviewer F1's fragility applies; it only reports, the controller
decides, and the archetype menu shows every buildable form's meaning with no word gate); (c) `rule:plate_fastener` picks
the largest fitting head when several bolts fit (plant, no text; R03's set_fastener would make it correctable).

Registry: retired `rule:first_option[archetype]`, `rule:archetype_text_gate` (record); reclassified `rule:only_feasible`
semantic → plant; new plant `rule:plate`, `rule:engage_pose`, `rule:plate_fastener`, `rule:adjust_slot`, `rule:recess`,
`rule:surface_feature`, `rule:nut_frame`, `rule:default_surface_feature`, `rule:default_handedness`,
`rule:default_nut_retention`; new guardrail `rule:print_orientation`; decision tag `prescore:archetype`.

## 4. Measured

**Tests.** Full RUN.md section 2 suite (16 modules, `test_plate` added): **565 tests, OK (1722 s)** on the final code
(an earlier run before the nut frame and the screw-into chain: 563, OK). New `test_plate.py`: 21 tests on a generic
fixture catalogue (slots by form, unit / band / pair validation with a live re-ask, form feasibility with reasons, the
archetype vote, prescore fallback, one feasible form asks nothing, the closed loop switching a shell to a plate,
form_evidence only with two forms, the plate end to end with set_handedness and add_surface_feature kept and every check
passing on solids and STLs, the nut frame for two adjustment axes, the screw-into chain on a tapped catalogue part, and
hand calculations: rectangle section, cantilever stress, pocket bridge span, slot / channel outlines). Changed on
purpose (marked "changed in migration delta R12"): `test_assembly.TestArchetypeGate.test_shell_needs_evidence` →
`test_shell_feasibility_is_plant_data`; `test_controller` audit expectation (the archetype is plant, not the R07
semantic rule). `test_controller_authority` and `test_no_hardcoding` scan forms.py and plate.py: green.

**Regression E1-01.** Offline (`scratchpad/regress.py`, fn 24, E1-01 / V1 / V2 / V3, exposed and closed-USB + scripted
expose): every feature-graph, layout.json and canonical-STL hash equals `scratchpad/reg_fix.json` (`same`). The
shell-only prompts are byte-identical (ParseSpec subject and slot list, Contents tail; test). Live
`run_suite --iter 091 --seed 41 --regression E1-01`: rc 0, **verified**, one controller step (`expose:module_1.usb` 2/2,
kept), archetype `rule:only_feasible` (one buildable form: no new question), feature graph 8b92655a7335 and layout
4536c7e83718 = the documented regression values; judge-cache hit (MEETS).

**T01 live** (`run_suite --target T01`, seed 41; package views in `<pkg>/views/model_*.png`, `ghost_*.png`):

| Attempt | Code | rc / outcome | Failing | Controller |
|---|---|---|---|---|
| iter 091 | R12 without the nut frame | rc 3, unsatisfied, 24/25 | `travel_y` (typed conflict: a hex channel covers fore-aft only, the cleat declares 5 mm lateral) | archetype `plate` 2/2 (confident; the 9B: "a bolt-on plate, not an enclosure"); step 1 split vote (studs / pins / mirror_pair, 1 each) → search kept `set_handedness:plate=mirror_pair` (pins undone: printable); step 2 `add_surface_feature:top=studs` 2/2 kept; stop: no failing check has an action |
| iter 092 | + the nut frame (diagnosis of 091: a generic plant fix, `set_nut_retention`) | **rc 0, verified, 27/27** | — | archetype `plate` 2/2; step 1 vote pins 2 : studs 1 (not confident) → search measured pins (undone: printable), studs (acceptable) and the unvoted `set_nut_retention:plate=frame` (kept: lowest error, `search:controller`); step 2 `set_handedness:plate=mirror_pair` 2 : 1 kept (llm); step 3 `add_surface_feature:top=studs` 2/2 kept (llm); stop: every check passes |
| iter 093 | final code (+ screw-into chain, docs) | **rc 0, verified, 27/27** | — | identical decisions and geometry (canonical STL 94f2007bfaf0 = iter 092) |

ParseSpec (27 slots) mapped 14 numbers to plate slots from L1.5–L1.9 (sizes 80/105, thickness 8/14, load 2500 N, patch
30, strength 25, safety factor 1.5, bearing 600, grip count 8, height 1.5/5.0, edge 3, spread 60 %); `ref_clearance`
was left `none` (the crank keep-out carries the catalogue's 2 mm margin). Contents: cleat 1, pedal 1. Delivered: plate
80.1 x 80.1 x 12.4 mm printed top face down (the cleat recess opens upward), 2 x M5 x 10 bolts through 2-D slots into
nuts held by a printed nut frame (30.7 x 14.4 mm, `nut_frame.stl`) sliding in a 51.2 x 19.9 mm pocket (20 mm fore-aft,
5 mm lateral), 8 M4 set-screw studs 3.25 mm proud, a declared mirror pair (`plate_mirror.stl`), worst load-case stress
16.0 MPa vs 16.67 allowed (measured section), crank keep-out cleared over the 15 degree release twist and the adjustment
range. Authority: llm 3, guardrail 2, semantic 1 (`rule:primary_reference`, pending R05), unregistered 0.
Packages: `loop/iter_092/T01_s41/20261025-222031/`, `loop/iter_093/T01_s41/20261025-230015/` (and the 091 one).

**Train design G16** (blocked at the archetype gate before; `run_suite --iter 092 --seed 41 G16`, once): rc 3, a package
(no longer stopped at ChooseArchetype): archetype plate by `rule:only_feasible` (the shell's cradle is infeasible for
the NEMA 17: its keep-outs cover every ledge strip), 11/17 checks pass. Failing: `content_placed` of the T-nuts (no
relation places them yet) and of the extrusion (its length is not in the text, R11's unsized rule), and
`bolt_engagement_0..3`: the mapped 5 mm plate minimum (setpoint 5.1, layer-rounded 5.2) leaves an M3 x 8 screw 2.8 mm in
the motor's 4.5 mm thread (1.0 d required) while M3 x 10 would bottom: an honest near-conflict of the request with the
catalogue screw lengths. Package `loop/iter_092/G16_s41/20261025-222455/`.

## 5. Known limitations

- The plate is horizontal and anchored on the primary (a bolt_face part that is not the primary is not placed); outline
  axes are the primary's placed frame (rot 0 in every layout so far). G16 gets a motor plate, but its extrusion is
  unsized in the text (rejected by R11's unsized rule) and the T-nut mounting is a second interface not built yet.
- `form_evidence` is a word list (see 3b). The closure half of R07 (`rule:default_closure`) is still pending.
- Bridge span = largest inscribed circle of a flat downward region: a strip beside a through slot counts as its width.
- The handedness sensor declares a pair by an action; the left part is the exact mirror (design basis), not re-measured.
- `ref_clearance` unmapped means `design_margin` from the reference keep-outs (T01's crank keep-out already includes the
  catalogue's 2 mm crank margin).

## 6. Files and revert

New: `forms.py`, `plate.py`, `test_plate.py`, `benchmarks/generalize/loop/iter_R12/`. Changed: `assembly.py`,
`controller.py`, `parts.py`, `design_rules.json`, `controller_rules.json`, `test_assembly.py`, `test_controller.py`,
`test_controller_authority.py`, `test_no_hardcoding.py`, `benchmarks/generalize/loop/{ARCHITECTURE,LEDGER,RUN}.md`,
`benchmarks/generalize/parts/{cleat_shimano_sm_sh51,pedal_shimano_pd_m520,bolt_m3_iso4762,bolt_m4_iso4762,bolt_m5_iso4762,grub_m4_iso4026,nema17_motor}/part.json`.
Live packages: `loop/iter_091/`, `iter_092/`, `iter_093/`.

Revert: `git checkout d2d5fcd -- assembly.py controller.py parts.py design_rules.json controller_rules.json
test_assembly.py test_controller.py test_controller_authority.py test_no_hardcoding.py
benchmarks/generalize/loop/ARCHITECTURE.md benchmarks/generalize/loop/LEDGER.md benchmarks/generalize/loop/RUN.md
benchmarks/generalize/parts/cleat_shimano_sm_sh51/part.json benchmarks/generalize/parts/pedal_shimano_pd_m520/part.json
benchmarks/generalize/parts/bolt_m3_iso4762/part.json benchmarks/generalize/parts/bolt_m4_iso4762/part.json
benchmarks/generalize/parts/bolt_m5_iso4762/part.json benchmarks/generalize/parts/grub_m4_iso4026/part.json
benchmarks/generalize/parts/nema17_motor/part.json` and delete `forms.py`, `plate.py`, `test_plate.py`,
`benchmarks/generalize/loop/iter_R12/` (and the live folders `iter_091`–`iter_093` if wanted).

## 7. Review fixes (2026-10-26, adversarial review of R12)

claude-context failed to connect again (MCP server "failed to connect"); targeted reads and grep. Nothing under the
held-out folders opened; `benchmarks/heldout.json` and `.mcp.json` untouched; nothing committed.

**The lesson the review taught:** iter 093 reported "verified 27/27" for a part that would not work, because sensors
were missing (no clamp path, no thin-feature check, unlinked L1s counted as fine) or measured the wrong thing (the load
case at the *shortest* lever arm, over the full plate width). The sensors were fixed first, so those failures are now
visible to the controller; then the plant got generic ways to fix what it can. Nothing is fitted to T01.

| Finding | Change (file:function) | Class | Test |
|---|---|---|---|
| B1 nut frame gave the nuts no seat | sensors `clamp_seat_<k>` (nut on plate/frame floor, or screw head on the free face), `clamp_frame` (frame on the pocket floor), `clamp_face` (bolted face on the plate): measured sections at every adjustment extreme, bearing >= `clamp_bearing_ratio_min` of the nominal face and the bolt axis inside the bearing's convex hull (plate.py `add_clamp_checks`, `clamp_*_check`, `seat_bearing`); plant: the frame gets its own floor (`plate_floor_min`) with bolt clearance holes and a flange wider than the floor slots by `plate_wall_min` at every position (`frame_layout`, the z stack in `_derive`); `clamp_seat` offers `set_nut_retention` | sensor + plant | `test_plate.TestReviewFixesR12.test_nut_seat_hand_calculation` (42.2 % hand calc; the 10.5 mm slot gives 0 %; one-sided lands tip), `TestNutFrame` (now asserts the clamp sensors, and that the pre-fix through-trap frame fails) |
| B2 load stress at the shortest arm | `edge_stresses` evaluates every adjustment extreme (worst case) in both the sensor and `size_for_load`; at the thickness limit the failure is a typed conflict (`load_stress_check`, `p["load"]["capped"]`); no structural actuator yet, so it is a requirement question, never verified | sensor + plant | `test_load_stress_is_the_worst_adjustment_position` (hand calc 36.46 MPa vs 19.5 by the old rule), `test_load_stress_at_the_thickness_limit_is_a_typed_conflict` |
| N1 section width | the section is clipped to patch + 2 x arm centred on the patch (45-degree spread, `clip_ring`) | sensor | same hand calc (width 90 of 120 mm) |
| N2 prefixed units unscaled | `unit_words` map each word to its factor (kN 1000, GPa 1000, psi, cm2 100, g 0.001); `forms.slot_value` scales in ParseSpec's violations and stored value; parts.py loads `unit_scales` | plant (validation) | `test_prefixed_unit_words_scale` (2.5 kN, 0.05 GPa, 6 cm2, live ParseSpec) |
| N3 T01 wording | frame meaning/source generic; "adapter" removed from the plate evidence words; grip_*/bolt_tip/stud sources generic; docstring/comment examples generic | controller-information | `test_controller_vocabulary_names_no_design` |
| N4 form_evidence in prescore | `prescore_form` compares measured checks only (text-basis checks excluded) | guardrail | `test_prescore_ignores_the_text_sensor` |
| N5 verified with UNLINKED L1s | `finalize`: outcome `unverified` (rc 3) when any L1 has no measuring check; a row traced only to text sensors is UNLINKED (`trace_matrix`, `TEXT_ONLY_NOTE`); self_report `verified` / `unlinked_l1`, design.json `unlinked_l1`; `thin_feature_<body>` measured (horizontal sections per vertex band with a disc opening, vertical sections with a z-only opening) linked by the new `feature_min` slot; keep-out and mirror-pair checks carry catalogue `names` so the trace links the L1 naming the feature (crank keep-out -> L1.6, not L1.4); clamp and travel checks carry the new `adjust_min` / `adjust_cross_min` slots | sensor | `test_unlinked_or_text_only_l1_is_never_verified`, `test_package_with_an_unlinked_l1_is_unverified_and_names_link_features`, `test_thin_features_and_stud_engagement_are_measured` |
| N6 enclosure prompts lost; crank margin counted twice | multi-form subject keeps the enclosure ("A printed part ...: an enclosure, or another printed form (a plate ...)"), the Contents tail keeps "for an enclosure: how many it puts inside"; keep-out entries may declare `margin` (pedal crank_side: crank_margin): required gap = max(0, ref_clearance - margin) in `position` and the clearance checks (`keepout_clearance`) | controller-information + plant | `test_subject_keeps_the_enclosure_wording`, `test_keepout_margin_is_not_counted_twice` |
| N7 | docstring names `rule:plate_position` / `rule:plate_thickness` removed; the scratch shell preference is `rule:arrange_scratch_form` (registered plant, documented); `stress_tol` rule replaces the 0.1 MPa literal; `bearing_area` measures the overlap with the engaged reference | registry / sensor | `test_bearing_area_is_the_overlap_with_the_engaged_part`, test_controller_authority |
| plant suggestions | part-shaped seat (`swept_plan`: a vertical-cylinder keep-out swept over its range is a stadium, boxes unchanged); floor under fasteners from `plate_floor_min` (frame floor); `stud_engagement_<k>` measured thread engagement in plastic (`plastic_thread_engagement_ratio`, also used to size the stud); required adjustment `required_adjust` (raises declared catalogue axes only) | plant + sensor | `test_part_shaped_seat_and_required_adjustment`, `test_thin_features_and_stud_engagement_are_measured` |

Not done (documented, no T01 specifics): heat-set inserts / through-nuts for studs (the catalogue holds only an M3 insert,
the studs are M4; the option needs a catalogue part of the stud's thread); a nut pocket closed on a declared contact face
(needs a contact-face slot the text can map; a closed pocket over a 27 mm frame would also exceed `bridge_max`); a
structural actuator (ribs, local thickening) for the load case: absent, the load case at the thickness limit is a typed
conflict. Catalogue data added (marked, trace/plant only): pedal keep-out `names` and `margin`, mirror_pair `names`,
cleat recess `names`. design_rules.json: 4 new values (`stress_tol`, `clamp_bearing_ratio_min`, `thin_probe_step`,
`plastic_thread_engagement_ratio`), 3 new plate slots (`adjust_min`, `adjust_cross_min`, `feature_min`), unit factors.

**E1-01 / V1-V3.** Offline `regress.py`: feature graph, layout, layout references and canonical STL hashes identical to
`reg_fix.json` for all eight runs; only rc changed 0 -> 3. Investigated: E1-01 has six UNLINKED L1s (L1.3, L1.7, L1.8,
L1.9, L1.11, L1.12) since before R12 (M10 not built), so under N5 its own verdict is legitimately `unverified`; not
weakened. 25 suite assertions that expected `verified` / rc 0 for all-pass regression packages now expect
`unverified` / rc 3 (`test_assembly.ALL_PASS_RC`, marked "changed in the R12 review fix (N5)").

**Live (seed 51).** iter 094: T01 rc 3 (load_stress typed conflict 49.77 vs 16.67 MPa; bbox failed because the 9B mapped
the request's 80 to the shell slot max_x; L1.3, L1.12 unlinked); E1-01 rc 3 unverified, 94/94 checks, graph
8b92655a7335 / layout 4536c7e83718 (the regression values), judge-cache hit; G16 rc 1 at Contents (the 9B counted the
motor 0 under the new Contents wording "inside the enclosure, or ..."). Diagnosis: wording, and the adjust slots applied
to a part that declares no adjustment (G16's T-nut travel mapped onto the motor's holes, whose heads then had no seat).
Fixed generically (neutral-first wording that keeps the enclosure clause; `required_adjust` raises declared axes only).
iter 095: G16 on the intermediate code (rc 3; clamp_seat 0 % found the head-over-slot defect). iter 096 (final code):
T01 rc 3, 40/41, failing only `load_stress` (typed conflict), L1.3 / L1.12 unlinked; G16 rc 3, 20/22 (content_placed of
the T-nuts and the unsized extrusion, as before R12's fixes; its bolt_engagement near-conflict is gone with the M3 x 8
through 3.6 mm); E1-01 rc 3 unverified, geometry unchanged.

**Final suite:** RUN.md section 2 (16 modules): 578 tests, OK (1727 s).

## 8. Second review fixes (2026-10-26, re-review verdict ACCEPT-WITH-NITS)

claude-context failed to connect again (MCP server "failed to connect"); targeted reads and grep. Nothing under the
held-out folders opened; `benchmarks/heldout.json` and `.mcp.json` untouched; nothing committed. No T01 wording or number
in code or controller-visible text.

| Nit | Change (file:function) | Class | Test |
|---|---|---|---|
| N1 load case sampled at 3 shifts, patch at the edge midpoint | `edge_stresses` moves the patch along each edge from corner to corner and the bolted part over its whole adjustment range, both `rules.stress_probe_step` (1 mm) apart with the corners, the extremes and the middles included (`probe_points`); one slice per section plane, clipped per patch window; rows record `patch_at`, `window`, `at` | sensor + plant (sizing uses it) | `test_load_stress_covers_corners_and_intermediate_shifts` (hand calc: a hole met only at shift +2 gives 72.92 MPa; the old 3-shift / midpoint sampling gave 36.46); `test_load_stress_is_the_worst_adjustment_position` changed on purpose (corner: width 55, 59.66 MPa) |
| N2 rc 3 hides two outcomes | `run_suite.run_outcome` (verified / unverified / unsatisfied / failed, from design.json `outcome`; pre-R12 rows by rc); `counts.<split>.outcome`; `stub_all_checks_pass` (headline authority probe: verified or unverified) and `stub_verified` apart, `stub.outcomes`, `all_checks_pass_share`; each summary row `run_outcome`; RUN.md sections 3 and 5 | measurement | `test_generalize_suite.test_rc3_outcomes_are_told_apart`, `test_stub_verified_and_llm_dependent`; positive assembly test `test_plate.TestReviewFixesR12Second.test_every_check_passing_and_every_l1_traced_is_verified_rc0` (cad_agent.main: rc 0, verified, nothing unlinked) |
| N3 replay asserted rc only | also asserts outcome `unverified`, no failing check, `all_passed`, unlinked L1s present | test | `test_assembly.TestReplayIter011` |
| N4 bearing / punch-through | sensor `fastener_bearing_<k>` (plate.py `add_bearing_check`, `fastener_bearing_check`): on the body the face bears on, bearing pressure = preload / measured seat area, punch-through shear = preload / (face outline x the contiguous printed floor under it, horizontal sections every layer); allowed `strength x bearing_strength_ratio / sf` and `strength x shear_strength_ratio / sf`; preload = mapped `fastener_preload` (new plate slot) else `rules.fastener_preload_stress_default` x the bolt's tap-drill area (`rule:default_preload`, plant), strength = mapped else `rules.print_strength_default` (`rule:default_print_strength`, plant); offers `set_nut_retention` (the frame seats the whole nut face); with no retention option left it is a typed requirement conflict. Open pocket on a contact face: `contact_face_openings` — the free face is a contact face when a raised-feature slot is mapped, the underside when the plate lies on an engaged catalogue part (its keep-out recess excluded); a typed note in self_report `typed_notes`, design.json, the notes and the controller's state words (no actuator closes a pocket yet, so a note, not a check) | sensor + plant defaults + typed note | `test_fastener_bearing_hand_calculation` (31.67 mm2 / 83.14 mm2 hand calc; 1 mm floor fails; a gap under the floor stops the shear path; typed conflict with no action), the positive package test (frame chosen by the controller, nut_pocket typed note) |
| N5 conflict compared to the setpoint, printed the limit | a conflict only beyond the stated limit; between setpoint and limit a note naming both (`limit_words`) | controller-information | `test_band_setpoints_and_limit_words` |
| N6 single value mapped to one band end | slot semantics: `sets` (design_rules.json `size_exact`, `thickness_exact`; parts.py validates the targets); `forms.apply_exact_slots` copies the mapped value to each unmapped end with its provenance; `plate.band_setpoints`: a band narrower than 2 x design_margin targets its centre (no crossed setpoints) | controller-information + plant | `test_one_stated_value_sets_both_band_ends` (70 mm each way -> 70 x 70 plate, size checks pass) |
| N7 generic checks unlinked | design_rules.json `trace_names` by check type (printable, separable, bbox_within, bolt_engagement, bolt_tip, fastener_bearing), read by `assembly.trace_links` as an added link (trace only, never a decision) | trace | positive package test (L1 links asserted); `test_assembly.test_trace_links` changed on purpose (E1-01 L1.9 "one manifold body ... without supports" now traced: 7 linked / 5 UNLINKED) |
| N8 stale shell notes | `plate.drop_stale_notes`: notes written between the `arrange` and `archetype` checkpoints (the shell's layout stages) and the Contents "unplaced" note of an item the plate places leave the record (`plate.dropped_notes` counts them) | record | positive package test (no `arrange:` / unplaced notes) |
| N9 section loss by cut | the load_stress evidence (`section_loss`) evaluates the worst section on the design solids without each cut role and uncut (`plate_solid_without`, `stress_at`): what each cut adds, in the detail and the conflict text | sensor | `test_load_stress_covers_corners_and_intermediate_shifts` (hole adds 38.38 MPa over the 34.54 uncut) |

Registry: new plant `rule:default_preload`, `rule:default_print_strength`. design_rules.json: 5 values
(`stress_probe_step`, `fastener_preload_stress_default`, `print_strength_default`, `shear_strength_ratio`,
`bearing_strength_ratio`), 3 plate slots (`size_exact`, `thickness_exact`, `fastener_preload`), `trace_names`. Test
fixture change marked in `test_plate.test_controller_switches_a_shell_to_the_plate` (the request states a 200 N
preload, so the plate's default channels pass the new sensor and the switch is measured on the form alone).

**Tests.** Full RUN.md section 2 suite (16 modules): **584 tests, OK (1739 s)** on the final code (the live runs and
the offline regression ran on the same code).

**Regression.** Offline `regress.py` (E1-01 / V1-V3, exposed and closed): feature graph, layout, layout references
and canonical STL hashes identical to `reg_fix.json` for all eight runs (rc 3 as since section 7).

**Live seed 61 (iter 097).** E1-01: rc 3 `unverified` (every check passes; L1.3, L1.7, L1.8, L1.11, L1.12 unlinked —
L1.9 is now traced), graph 8b92655a7335 / layout 4536c7e83718, judge-cache hit (MEETS). T01: rc 3 `unsatisfied`,
40/43: archetype plate (the 9B), step 1 `set_nut_retention:plate=frame` (a 1/1/1 split vote; kept: 5 -> 2
controllable failing checks, the frame clears travel_y and seats the whole nut face), step 2 `add_surface_feature:top=studs` (2/3), step 3 `set_handedness:plate=mirror_pair`
(2/2); stop: no failing check has an action. Failing, all typed requirement conflicts: `load_stress` 58.59 MPa vs
16.67 allowed at edge +x, patch centre -23.8 mm along it, part shifted -10 mm (the far end of the fore-aft range), arm
17.1 mm, 47.1 mm section; the uncut plate would carry 27.79 MPa there, the cleat recess adds 11.2, the nut pocket 10.5,
the bolt slots 3.6 (iter 096 reported 49.77 with the patch at the edge midpoint); `fastener_bearing_0/1`: under the
default 970 N preload the nut frame floor sees 30.70 MPa bearing (16.67 allowed) and 16.66 MPa punch-through shear on
2.1 mm of floor (8.33 allowed). Typed note: the nut pocket is open on the top (grip) face, 1382 mm2. L1.12 unlinked.
The derive note now reads "14.00 mm: within thickness_max 14, but more than the thickness_max setpoint 13.90".
Package `loop/iter_097/T01_s61/20261026-020807/`.

Not done: no plant sizing of the nut floor for punch-through (the frame floor stays `plate_floor_min`; a thicker floor
would push the 14 mm stack over thickness_max); no actuator that closes a pocket on a contact face (a closed pocket over
the frame would exceed `bridge_max`), so it stays a typed note; the preload default is an order-of-magnitude assumption
(x2), reported with its source in every detail.
