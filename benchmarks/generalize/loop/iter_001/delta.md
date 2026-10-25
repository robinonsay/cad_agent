# Iteration 001: gap analysis and delta design

Author: gap analyst (iteration 001). Inputs: `summary.json`, `runs.jsonl`, every train `run.log` and `design.json`,
the LLM transcripts of G01, the regression judges' `judge_*.json`, `verdicts.json`, `../ARCHITECTURE.md`,
`../RUN.md`, `../LEDGER.md`, `../../plan.json` (train entries only) and the agent code. Held-out folders were not
opened. claude-context failed to connect in this session, so files were found with targeted `grep`/`ls`.

## 0. What the error signal actually says

The task text for this step said "Train MEETS 3/40, CORRECT 4; regression E1-01 FAILS". The iteration's own files
say otherwise. This analysis uses the files:

| Source | Train | Regression |
|---|---|---|
| `summary.json` (code `72dbcfdfb8de`, one code version) | 40 runs, **rc 1 on all 40, 0 STL, 0 judged** | 4 runs: rc 0 ×3, rc 3 ×1 (V3), all with renders |
| `verdicts.json` + `judge_*.json` | none (nothing to judge) | **E1-01 MEETS** (two judges, both 1.0), **V1 MEETS**, **V2 MEETS** (two judges each), **V3 DNM / CORRECT 0.99** (one judge) |
| Regression bar (ARCHITECTURE.md 7) | | **pass**: E1-01 MEETS, V1–V3 at least CORRECT |

So the regression set does not fail, and no train design produced geometry. The first train run measured where
every design stops, which is what GM1(d) asked for. Every one of the 40 stops **before any geometry exists**.

Process defects found on the way (not agent code):
- P1. `verdicts.json` is a list of `{"id", "meets", "class", ...}` rows. `cache_verdicts.py` needs `name` and
  `verdict` per row (or the dict form of RUN.md 5), so it would reject this file. The verdicts are not in
  `judge_cache.json` (the file does not exist), and `summary.json` still says `regression: pending`, `judged: 0`.
  The Judge step should rewrite the file in the RUN.md 5 form (`{"E1-01_s1": {"verdict": "MEETS", "class":
  "CORRECT", "score": 1.0}, ...}`) and run `cache_verdicts.py 001`. Then E1-01, V1 and V2 (byte-identical geometry
  expected after this delta) are cache hits in iteration 002.
- P2. The judges wrote `judge_N.json`, not `judge.md` + `defects.json` as RUN.md 5 says. V3 has one judge, not
  two. Neither changes a verdict.

## 1. Defects: where each train run stopped

Stop stage and last note from `summary.json`, grouped. "Count" is train designs.

| # | Stage | Note (verbatim) | Designs | Count |
|---|---|---|---|---|
| S1 | parse_spec | `no number in the text for board_width, board_depth (no default exists)` | G16 G17 G18 G22 G24 G26 G27 G29 G30 G31 G32 G35 G36 G37 G42 G43 G45 | 17 |
| S2 | parse_spec | `no number in the text for board_depth (no default exists)` | G10 G14 | 2 |
| S3 | contents | `exactly one board is needed, the answer has 0` | G01 G02 G03 G04 G05 G12 G38 G41 G47 G49 | 10 |
| S4 | contents | `no catalogue board matches the request` | G06 G08 G09 G20 G21 G33 G40 G50 | 8 |
| S5 | arrange_contents | `no feasible arrangement: ... no free spot on the board for rpi_camera_v2` | G23 | 1 |
| S6 | derive_features | **uncaught** `parts.MissingParam: camera_screw_1_4_20: parameter 'length' must come from the request` (traceback, no package) | G11 G13 | 2 |

Regression defect (judged):

| # | Design | Requirement | What |
|---|---|---|---|
| R-V3 | V3 | L3.10.1.1 (w1) | Closed height 52.70 mm against a 45 mm limit. Was 35.70 and MEETS on seeds 0, 12 and 13 of the enclosure loop. The agent's own bbox check also failed (rc 3) and prescore reported the same hard failure (violation 7.69) on every arrangement. |

Controller errors seen in transcripts (secondary; they do not decide where a run stops today):
- C-a (G01): Contents answered `generic_box` ×1. The request's word "box" means the enclosure, but `generic_box`
  has the bare alias `box`.
- C-b (G01): ParseSpec mapped `max_x` to 45 (the board's 45 mm side). The other two members of the same
  `60 x 30 x 26` group went to `max_y` and `max_z`.
- C-c (G11): ParseSpec gave `wall_min` 4.8 > `wall_max` 4. It was still violated after the re-ask and fell back
  to the rules default.
- C-d (G01, G13, V3, E1-01): Contents votes `exposed: no` for a USB port the text says is reachable. Text
  coverage repairs it when the text names the plug's alias, as it did in G13 and V3.

## 2. Root causes (in the agent, not in the designs)

### RC1: the frame's primary reference is hard-wired to "one catalogue part of kind `board`, sized by the request" (38 designs: S1–S5)

Code facts:
- `design_rules.json` `spec_slots` make `board_width` and `board_depth` **required**: `default_rule: null`, and
  `ParseSpec.update` fails when either is "none" (`assembly.py:479-481`). A request with no circuit board (motor
  plate, bracket, adapter: S1) or with a fixed-size module whose size the text does not repeat (G10 and G14,
  Arduino Nano: S2) cannot pass ParseSpec.
- `Contents.update` requires exactly one content item with `kind == "board"` (`assembly.py:545`, `574-576`). Only
  one catalogue part has that kind, `perfboard`. Every other board-like part (Arduino Nano and Uno, ESP32,
  Raspberry Pi Zero 2 W, Pico 2, 1602 LCD, OLED, camera) has kind `module` or `display`.
  - When the text says the word "board", the alias lookup offers `perfboard`. The 9B controller then answers it
    **correctly** with 0, because there is no perfboard in G01–G05, G12, G47 or G49 (G01 transcript
    `013_assy_contents.txt`: `perfboard: 0`, `arduino_nano: 1`). Python rejects the right answer (S3).
  - When the text never says "board", `perfboard` is not even a candidate (`Catalog.lookup` keeps only
    token-overlap hits), and the run fails before the controller is asked (S4).
  - In G23 the text calls the camera's PCB a "board" ("camera v2 board: 25 x 24 mm"). The controller then put a
    25 × 24 perfboard under the camera, and the camera could not fit on it (S5). The controller error is invited
    by the rule that a perfboard must exist.
  - G38 and G41 do contain a perfboard, but the Contents prompt asks how many the request puts "inside the
    enclosure". A fixture holds the board and does not enclose it, so the controller answered 0 (prompt framing,
    see RC6).
- Every geometric use of the primary reads the datum names `TOP` and `BOTTOM` (`layout.Placer.__init__`,
  `parts.board_keepout`, `assembly.build_envelopes`, `driver_columns`, `derive_cavity` expressions
  `board.TOP.z` / `board.BOTTOM.z`, `build_plan`). The PCB modules name their planes `PCB_TOP` and `PCB_BOTTOM`,
  so a module could not be the primary even if Contents allowed it.
- `exposed_connectors` takes `connectors[:1]` and only for `role == "content"`. A primary's own connectors (the
  Nano's USB) are never exposed, and a part with several connectors (Uno: USB-B + DC; Zero 2 W: mini-HDMI + two
  micro-USB) exposes only its first one.

This is ARCHITECTURE.md's GM2 row "Enclosure frame = the board's longest edge" and the generated-slots row.
GM2 was scheduled after GM1 anyway. The baseline shows it is the single gate in front of every design.

### RC2: the lid fastener rule depends on what the catalogue happens to hold, and its failure is uncaught (G11, G13; latent in every shell design and in the regression set run on both catalogues)

- `lid_screw` picks the **largest-thread** catalogue fastener that has `pilot_diameter`, `thread_diameter`,
  `clearance_diameter` and `min_engagement`. With the enclosure catalogue alone that is `screw_m3_selftap`. With
  both catalogues it is `camera_screw_1_4_20` (6.35 mm thread), whose `length` is `from_request`.
  `fastener_values` then raises `MissingParam`.
- `derive()` calls `lid_screw` / `fastener_values` **outside** its `try`, and the `try` does not catch
  `pt.PartError`. The exception escapes the behaviour tree: no package, no `finalize`, and only a traceback in
  `run.log`.
- The regression set passes only because RUN.md runs it with the enclosure catalogue alone. With both catalogues,
  E1-01 would crash at the same line. ARCHITECTURE.md 7 plans exactly that switch.
- The rule ignores the text. G02, G05, G10 and G12 name "M3 (self-tapping) screws", and G04 names "M2.5 screws".
  ChooseStack's evidence gate (enclosure 7.10) is the established pattern for this choice and is not used here.

### RC3: one-number-one-slot holds inside ParseSpec only, not across ParseSpec and Contents (V3 regression defect; latent for every request-sized content part)

- V3 seed 1: ParseSpec mapped `headroom` to the number "20" in "a 10 mm diameter, 20 mm tall capacitor"
  (`spec_provenance.headroom`). The text's headroom is "Leave at least **3** mm of space above the tallest part".
  Then `Contents.ask_params` mapped `generic_1.height` to the **same** occurrence. Nothing compares the two
  stages, so the shared-number sensor (`ParseSpec.shared`) never saw a conflict.
- headroom 20 instead of 3 adds 17 mm, which explains 52.70 against 35.70 exactly.
- The plant sensed the result (bbox check fails, prescore hard failure on every arrangement), but no actuator can
  reopen a spec mapping. The enclosure loop's seeds mapped headroom correctly, so the defect is seed-dependent.

### RC4: the archetype set is a constant (latent; becomes active as soon as RC1 is fixed)

`feasible_archetypes` returns `[("tray_lid", "screws")]` for every request. Once RC1 is fixed, designs whose
primary qualifies but whose text asks for no enclosure (G23 camera holder, G38 board holder, G40 drill guide, G41
soldering jig, G49 camera pod) would get a tray and lid around their part. The judges would grade that WRONG, and
the run would spend judge time on geometry of the wrong family.

### RC5: catalogue alias collides with archetype vocabulary (data; G01 controller error C-a)

`generic_box.names` includes `box` (and `block`). Every enclosure request that says "box" names a generic box.
The controller took the bait in G01. Once RC1 is fixed, a `generic_box` content item needs `size_x/y/z` from the
text, and `ask_params` would stop the run at Contents (G08, G10 and G14 all say "box").

### RC6: enclosure framing in the prompts the 9B sees (deferred; see section 6)

ParseSpec opens "An enclosure is being designed", the slots speak of "the circuit board", and Contents asks what
goes "inside the enclosure". This framing is right for 14 train designs and the regression set, and wrong for the
fixtures and mounts (G38 and G41 answered perfboard 0). Changing it changes the regression prompts byte for byte,
so it waits until the non-shell archetypes exist (GM5) and can be measured.

## 3. Clustering and choice

| Root cause | Designs whose stop it decides now | Designs it blocks next | Class | Milestone |
|---|---|---|---|---|
| RC1 primary reference | 38 (S1–S5) | — | rule + catalogue data | GM2 (first slice) |
| RC2 lid fastener + crash | 2 (S6) | every shell design once RC1 is fixed; regression on both catalogues | rule + robustness | GM3 (first slice) |
| RC3 cross-stage number ownership | 0 train; V3 (regression, w1) | every request-sized content part (generic parts in G11, G42–G45) | sensor | GM2 (generated slots) |
| RC4 archetype evidence gate | 0 now | 5 (G23 G38 G40 G41 G49) would build wrong-family boxes | rule (data vocabulary) | GM5 prerequisite |
| RC5 alias collision | 0 now (G01 controller error) | G08 G10 G14 (generic_box would stop Contents) | catalogue data | — |

**Chosen delta: "primary reference" (GM2a), with RC2, RC3, RC4 and RC5 as its necessary companions.** RC1 alone
moves 38 of 40 designs. Without RC2 every shell design it frees would crash at derive_features. Without RC4 the
fixtures it frees would produce wrong-family geometry. Without RC5 three of the shell designs it frees would stop
at Contents on a phantom box. RC3 is the only fix for the one judged defect in the regression set. Each change is
a generic rule triggered by part data and request words. None names a design.

## 4. The delta

### 4.1 Catalogue data (both catalogues)

D1. **`interfaces` with the `mount_holes` kind** (ARCHITECTURE.md 3.1 schema, first use):
`{"id": "mount", "kind": "mount_holes", "holes": "<axis_list>", "seat": "<plane under the part>", "top": "<plane
the component keep-out starts from>"}`. Add it to every part that can be the primary reference in this slice:
- enclosure catalogue: `perfboard` (`HOLE`, `BOTTOM`, `TOP`) and `rpi_pico2` (`HOLE`, `PCB_BOTTOM`, `PCB_TOP`);
- generalize catalogue: `arduino_nano`, `arduino_uno_r3`, `rpi_zero2w`, `lcd1602_hd44780`, `oled_ssd1306_096`,
  `rpi_camera_v2` (each `HOLE`, `PCB_BOTTOM`, `PCB_TOP`).

Not added in this slice: `esp32_devkitc_v4` (it has no holes; its support is a pocket or ribs, GM6), and fans,
motors and servos (they bolt through or screw into a plate or boss, which are GM3 relations).
The import gate gains rule R9: every interface names existing datums of the declared kinds (`holes` an
axis_list, `seat` and `top` planes perpendicular to the hole axes).

D2. **Carrier**: a part that other contents are placed on. In this slice a carrier is a part with a `grid` block
(`perfboard`). This is part data, read by rule.

D3. `generic_box.names`: drop `box` and `block` (keep `rectangular block`, `cuboid` if present). Reason: these
aliases are archetype vocabulary (RC5). No train request uses them for a generic box (G30 and G45 size their boxes
without these words).

### 4.2 Rules data (`design_rules.json`)

D4. `spec_slots`: `board_width` and `board_depth` get `"required": false`. The slot lines in the ParseSpec prompt
stay byte-identical (the flag is not shown to the controller). A required slot is one with `default_rule: null`
and `required` not false.

D5. New `archetypes` block: `{"tray_lid": {"evidence": ["enclosure", "box", "case", "lid"], "needs":
"mount_holes primary", "source": "words that ask for a body enclosing its contents; a generic vocabulary, no
design names"}}`. "housing" and "block" are deliberately not included, because they name bearing housings and
pillow blocks (block archetype, GM5).

### 4.3 Agent rules (code, for the implementer)

C1. **Primary reference rule** (replaces "exactly one board"):
- Contents candidates = today's top-k per `CONTENT_KINDS` ∪ every part with a `mount_holes` interface that the
  text **names** (`named_parts`, a contiguous alias run, which is stricter than token overlap, so the regression
  candidate lists are unchanged).
- After the quantity vote, the primary = the carrier if exactly one carrier has quantity 1. Otherwise it is the
  content part with the largest catalogue plan footprint. The choice is recorded as
  `choice("primary", id, "rule:primary_reference")`.
- If the primary has no `mount_holes` interface, the run stops with a typed note: `contents: primary <id> has no
  mount_holes interface; its support (pocket / ribs / bolt-through) is not implemented (GM3/GM6)`. If there are
  no contents, the note is `contents: nothing to design around`.
- A request-sized primary (one with `from_request` params) takes them from the spec's size slots when ParseSpec
  filled them, else from `ask_params`. The longest-edge swap in ParseSpec runs only when both slots are present.
- A non-carrier primary carries no other contents. Other content items are not placed on it. They are listed as
  `unplaced` in design.json and layout.json, and a hard `content_placed` check fails for each one (a sensor, so
  the package is honest and rc is 3). Their relations (face, against, on_pattern) are GM2b.
- The primary keeps node id `board` and role `board` in the layout and feature graph, so every downstream
  expression keeps its anchor. Its seat, top and holes are read from its `mount_holes` interface: no `"TOP"` /
  `"BOTTOM"` literal remains in `layout.py`, `parts.py` or `assembly.py`.
- Exposure is per connector. A part with one connector keeps today's single `exposed` key (the regression schema
  is unchanged). A part with two or more gets one yes/no key per connector name. Text coverage forces each
  connector whose mate the text names. `exposed_connectors` iterates over every exposed connector, not
  `[:1]`, and includes the primary's own connectors. A primary's connector has no edge choice: the wall it leaves
  through follows from its axis (`wall_facing`) and is recorded as `rule:fixed_by_primary`.

C2. **Lid fastener rule** (replaces "largest catalogue screw"):
- A fastener is *catalogue-complete* when it has no `from_request` param.
- Lid screw = the catalogue-complete fastener with the lid fields that the text names (`text_evidence` over
  fastener aliases, recorded `rule:text_evidence`). When there are several, take the largest thread among them.
  When none is named, take the largest-thread catalogue-complete fastener (`rule:largest_complete_screw`, flagged
  as an assumption).
- A named fastener that is not catalogue-complete (G11 and G17: ISO 4762 bolts whose length comes from a stock
  list) is noted and skipped, and its length rule is GM3.
- `board_screw` gets the same catalogue-complete filter.
- `derive()` moves fastener selection inside its `try` and catches `pt.PartError` (with `MissingParam`), so
  derive_features fails with a note and a package, never with a traceback. The same holds for prescore.

C3. **Cross-stage number ownership**:
- `st.number_owner: {number id: slot}` is filled by ParseSpec and by `Contents.ask_params` (`<item>.<param>`).
- When `ask_params` picks an id that a spec slot already owns, the existing owner question
  (`ParseSpec.resolve_shared`, lifted to a module function) runs between the two slots. The losing slot is
  re-asked with that id removed from its enum. A spec slot that loses falls back to its rules default if the
  re-ask also fails, flagged as today.

C4. **Archetype evidence gate**:
- `feasible_archetypes` returns `tray_lid` only when (a) the primary has a `mount_holes` interface and (b)
  `text_evidence` finds one of `archetypes.tray_lid.evidence` in the request or an L1.
- Otherwise ChooseArchetype fails with `not implemented: archetype (primary <id>; no shell evidence; candidates
  for GM5: plate / bracket / block / cradle)`.

C5. **Guards (GM1 b and c, folded in here because the baseline showed they were missing)**:
- `test_no_hardcoding` reads ids and aliases from **both** catalogues.
- A new offline test runs E1-01 with a scripted controller on both catalogues (section 5, T8).

### 4.4 RUN.md / ARCHITECTURE.md

- RUN.md section 1: iteration 002 runs the full train split + regression, SEED=2 (added by this step).
- ARCHITECTURE.md: section 1a records the baseline and these plan refinements (added by this step).

## 5. Tests (offline, fake LLMs, no Ollama). Each one fails on code `72dbcfdfb8de` and passes after the delta

Tests may load a train design's request text as data (ARCHITECTURE.md 6). They are keyed by capability.

| # | Test (module) | Before | After |
|---|---|---|---|
| T1 | `test_assembly.TestPrimaryReference.test_module_is_primary_without_board_slots`: G04's request as data; scripted ParseSpec answers "none" for both board slots; scripted Contents answers 1 for the module with a mount_holes interface | ParseSpec fails `no number in the text for board_width, board_depth` | ParseSpec succeeds; `choices.primary.by == "rule:primary_reference"`; the primary is the named mount_holes part; no perfboard in contents |
| T2 | `...test_carrier_stays_primary` (E1-01 text, enclosure catalogue) | passes (guard) | passes; primary is the carrier; ParseSpec and Contents prompts byte-equal to the recorded ones |
| T3 | `...test_primary_without_mount_holes_stops_typed`: largest content part has no interface (G05 text) | fails with `exactly one board ...` | fails with a note containing `has no mount_holes interface`; no exception |
| T4 | `test_parts.TestInterfaces.test_mount_holes_gate`: an interface naming a missing datum, a non-plane seat | no R9; loads | gate failure R9 for each; every catalogue part still passes |
| T5 | `test_parts.TestInterfaces.test_perfboard_planes_equal_top_bottom` | no `interfaces` | interface seat/top z equal the old `BOTTOM`/`TOP` z for every specimen (regression invariance) |
| T6 | `test_assembly.TestLidFastener.test_unified_catalogue_default`: both catalogues, text without fastener words | `lid_screw` returns `camera_screw_1_4_20` | returns the largest catalogue-complete screw (the same part the enclosure catalogue alone gives) |
| T7 | `...test_named_fastener_wins`: text "held by four M2.5 screws" | largest thread, ignores text | the named M2.5 screw, `rule:text_evidence` |
| T8 | `test_assembly.TestBothCatalogues.test_e1_01_derives`: E1-01 scripted end to end to Build, both catalogues | uncaught `MissingParam` | builds; layout.json poses and fasteners equal the enclosure-only run within 0.01 mm |
| T9 | `...test_derive_contains_part_errors`: a fastener with an unresolved request param forced into derive | exception escapes `derive()` | `derive()` returns `derivation failed: ...`; DeriveFeatures returns FAILURE with the note |
| T10 | `test_assembly.TestNumberOwnership.test_spec_slot_and_part_param_share_a_number`: V3 text; scripted ParseSpec maps `headroom` to the "20 mm tall" id and ask_params maps the cylinder height to the same id | both get 20; no note | owner question asked; height keeps 20; `headroom` re-asked without it and gets 3 |
| T11 | `test_assembly.TestArchetypeGate.test_shell_needs_evidence`: G40's text (drill guide) vs E1-01's text | `tray_lid+screws` for both | `[]` with a typed `not implemented: archetype` note for G40; `tray_lid+screws` for E1-01 |
| T12 | `test_assembly.TestExposure.test_primary_connectors_and_multi_connector_parts`: a primary with three connectors, two named by plugs | first connector only, never the primary's | both named connectors exposed, each with its own plug sweep and port cut on the wall its axis faces; `rule:fixed_by_primary` |
| T13 | `test_parts.TestCatalogueVocabulary.test_no_alias_is_archetype_vocabulary` | fails (`generic_box: box`) | passes |
| T14 | `test_no_hardcoding` scans both catalogues' ids and aliases | generalize ids not scanned | scanned; green |

Full suite (RUN.md 2) and `test_no_hardcoding` must stay green. No literal from a train request may appear in
agent code: the new words live in `design_rules.json`, and the new datum names live in part.json.

## 6. Expected effect per design (iteration 002, SEED=2)

"Now" is iteration 001's stop. "After" is the forecast. Packages are judged. A typed stop is not judged, but it
names the next missing capability.

| Design | Now | After (forecast) | Why / what is still missing |
|---|---|---|---|
| G01 | S3 contents | arrange_contents typed stop | Nano holes Ø1.7: no catalogue screw passes. The locating-pin relation (L1.3 asks for it) is deferred to GM3 |
| G02 | S3 | **package** (DNM, MINOR at best) | Uno primary; USB-B + DC both exposed through one short wall (per-connector exposure); M3 self-tap lid by evidence. Missing: lid vent slots (GM4) |
| G03 | S3 | contents typed stop | ESP32 has no holes: pocket/rib support is GM6 |
| G04 | S3 | **package** (DNM) | Zero 2 W primary; mini-HDMI + 2 micro-USB exposed on one long wall; M2.5 lid screws by evidence. Missing: microSD slot (not a catalogue connector: catalogue data for GM4) |
| G05 | S3 | contents typed stop | ESP32 is the largest content part, with no holes (GM6) |
| G06 | S4 | **package** (DNM, likely WRONG) | LCD primary; Pico listed unplaced (`content_placed` fails). Missing: 30° face, window (GM4/GM5) |
| G08 | S4 | **package** (DNM, likely WRONG) | Pico primary, USB exposed. Missing: cell cradle, door, switch slot (GM6/GM9) |
| G09 | S4 | contents typed stop | No content part has a mount_holes interface (battery pocket GM6, hinge GM7) |
| G10 | S2 | arrange_contents typed stop | Nano holes (as G01) |
| G11 | S6 crash | **package** (DNM) | Perfboard carrier; DC jack exposed; M3 lid screws by evidence. Missing: fan and lid opening, exhaust slots (GM4/GM8), ISO 4762 stock-length rule (GM3) |
| G12 | S3 | contents typed stop | ESP32 (GM6) |
| G13 | S6 crash | **package** (DNM) | Perfboard + Pico on female headers. Missing: 4 switches, plungers, top-plate holes (GM4 actuator) |
| G14 | S2 | arrange_contents typed stop | Nano holes (as G01) |
| G16 G17 G18 G20 G21 G22 G24 G26 G27 G29 G30 G31 G32 G33 G35 G36 G37 G42 G43 G45 G47 | S1/S4/S3 | contents typed stop | No mount_holes content part yet (motors, fans, servos, bearings, tubes: GM3, GM5, GM6) |
| G23 | S5 | arrange or choose_archetype typed stop | If the controller again sizes a perfboard from "camera board": unchanged (deferred sensor, section 7). Otherwise camera primary and no shell evidence |
| G38 G40 G41 G49 | S3/S4 | choose_archetype typed stop | Primary qualifies, no shell words: cradle / plate / fixture archetypes are GM5 |
| G50 | S4 | **package** (DNM, likely WRONG) | Zero 2 W primary; per-connector exposure votes (text: both micro-USB exposed, mini-HDMI unused; no plug alias in the request, so coverage cannot force it). OLED unplaced. Missing: fan, window, encoder, vents, snaps |
| E1-01, V1, V2 | MEETS | MEETS, **byte-identical geometry** (cache hit) | Every changed path reduces to today's behaviour for a carrier primary, enclosure catalogue, no fastener words, single-connector parts, no cross-stage number conflict (T2, T5, T8) |
| V3 | DNM / CORRECT 0.99 | MEETS (when the seed reproduces the headroom mis-map, C3 corrects it; otherwise unchanged geometry) | RC3 |

Forecast totals: **train packages 0 → 7** (G02 G04 G06 G08 G11 G13 G50), MEETS 0, CORRECT 0–1 (G02 is the only
plausible one). 38 designs change their stopping point. All 40 runs end with a typed note, and none in a traceback
or a "board" message. Regression: pass, V3 to MEETS. Uncertainty: the controller's per-connector exposure votes
are new questions (G02, G04, G50), and text coverage rescues them only where the text uses a plug alias.

This delta does not move the CORRECT count much by itself. It is the precondition for every milestone after it:
until a design produces geometry the judges cannot report defects, and the loop has no error signal for GM3–GM10.

## 7. Deferred, and why

| Item | Designs | Why deferred | Where |
|---|---|---|---|
| Locating-pin relation (no catalogue screw passes the hole: pin = hole − fit, seated on posts) | G01 G10 G14 | A new feature rule with its own sensors (pin band, seat). It is the first item of GM3, and the next iteration's best candidate (3 designs, all already reaching arrange after this delta) | GM3 |
| ESP32 pocket / rib support (primary without holes) | G03 G05 G12 | Needs the pocket interface + retention sensors | GM6 |
| Relations for non-carrier secondary contents (OLED/LCD/encoder/LED/fan on faces) and any-kind contents | G05 G06 G08 G10 G13 G50 | GM2b relation enums + GM4 apertures; until then they are `unplaced` with a failing check | GM2b, GM4 |
| Enclosure framing in the ParseSpec / Contents prompts (RC6) | G38 G41 + all fixtures | Changes the regression prompts; worth doing only when a non-shell archetype can consume the answers | GM5 |
| Group coherence sensor for limit triples (`max_x/y/z` from one `a x b x c` group) | G01 (C-b), latent | Generic and cheap, but no run reaches a size check yet. Revisit when packages show it | GM2b |
| "Carrier sized like a named module" sensor (a perfboard whose request size equals a named module's footprint is that module) | G23 | One design; G23 then stops at the archetype gate anyway | GM5 |
| ISO 4762 / bolt length from a stock list | G11 G17 G37 | Fastener chain length rule | GM3 |
| microSD slot as a catalogue connector (`rpi_zero2w` has `SD_MOUTH`/`SD_AXIS` datums but no connector entry and no card "plug") | G04 | Catalogue data plus a card envelope part; one design | GM4 |
| Regression on both catalogues in the real Run | regression set | The Contents candidate list would gain generalize parts and change the converged prompts. T8 covers the plant offline first | ARCHITECTURE.md 7 |
| Benchmark data fixes | none | No train package was judged, so no requirement could be shown contradictory or impossible. The audit waits for the first judged train packages | — |

## 8. Owner questions

None. Every choice above is derivable. Two assumptions with their uncertainty:
- The primary = carrier, else the largest content part (replacing ARCHITECTURE.md's "most interfaces"). That
  rule would make the Pico outrank the perfboard in E1-01, which contradicts section 1's own "board stays
  primary". The new rule needs a review if a train design's largest part is not the one the brief builds around.
  None of the 40 is like that in this slice (checked against plan.json `parts` and the briefs). Uncertainty: low.
- The shell evidence vocabulary {enclosure, box, case, lid} separates the 14 enclosure briefs plus the regression
  set from the fixtures and mounts in the train split. Uncertainty: medium. A held-out brief may call a box a
  "housing"; the held-out score will show it.
