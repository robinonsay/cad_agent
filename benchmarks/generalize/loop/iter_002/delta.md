# Iteration 002: gap analysis and delta 002

Analyst step, 2026-10-25. Code at run time: `b0a4f1abe322` (`shasum -c iter_002/code_sha1.txt`: every file OK at
analysis time, so the code has not changed since the Run). claude-context failed to connect in this step, so files were
found with targeted reads and grep. Nothing under `../holdout/` or `holdout_results/` was opened.

**Correction to the computed task text.** It said "Train MEETS 3/40, CORRECT 3; regression E1-01 FAILS". The files say
otherwise. `summary.json` and `verdicts.json` give **train MEETS 0 / CORRECT 0** (6 packages, all WRONG; 34 no-output).
The **regression set fails because of V1** (DNM / MINOR 0.9185). **E1-01 is MEETS**, and V2 and V3 are MEETS too. This
document uses the files.

---

## 1. Measured error signal

| Run | rc | Stop / verdict | Score | Gates failed (judge) |
|---|---|---|---|---|
| E1-01 | 0 | MEETS | 1.0 | none |
| V1 | 0 | **DNM / MINOR** | 0.92 | none; w3 L3.1.2.1 (jack faces +X, the Pico USB faces −X; request: "the same short end") |
| V2, V3 | 0 | MEETS | 1.0 | none |
| G04 | 3 | WRONG | 0.82 | G5 no microSD opening; G6 board pilots Ø1.70 (M2), need 2.0–2.2 (M2.5) |
| G02 | 0 | WRONG | 0.74 | G4 board pilots M2, need M3; G5 no lid vents; G6 boss pilot 6.1 deep, need ≥ 7.6 |
| G11 | 0 | WRONG | 0.55 | G2 board pilots M2, need M3; G4 no fan / fan pilots; G5 no exhaust slots |
| G06 | 3 | WRONG | 0.30 | G2 no tilt / window; G4 Pico unplaced; G5 no USB opening |
| G13 | 3 | WRONG | 0.10 | G0/G3/G5: no buttons, no plungers, no plunger holes, Pico USB on the wrong wall |
| G50 | 3 | WRONG | 0.10 | G0/G3/G4/G5: fan, OLED, encoder, vents, window, snaps missing |

No-output stops (34): contents 25 (`nothing to design around` 18; `primary <id> has no mount_holes interface` 6; a
generic part with no number 1 (G08)); part-size stops `no number in the text` 3 (G26, G29, G37); choose_archetype 4
(G23, G40, G41, G49: no shell evidence, as designed); arrange_contents 2 (G01, G14: no catalogue screw passes the Nano's
holes).

Iteration 001's forecast was 7 packages (G02 G04 G06 G08 G11 G13 G50). 6 came. G08 stopped at contents: the controller
listed the 18650 cell as `generic_cylinder`, because `cell_18650` (kind `battery`) is not offered (RC-C below).

The agent's own sensors already saw part of this. `pilot_depth_standoff_1..4` fails in **G04 (−1.39), G06 (−0.39) and
G13 (−0.39)**: the standoff is too short to hold its own pilot over the minimum floor. `bbox` fails in G04 and G13.

## 2. Defects → root causes (traced to the agent, not to the design)

| Defect (designs) | Root cause | Class |
|---|---|---|
| **R-V1**: jack on +X, USB on −X; the text says "both ... through the same short end" (V1) | **RC-A.** The edge vote is two independent per-item marginals, and the 9B voted (−X, +X) in 2 of 3 samples. ConfirmArrangement's p_yes ranks the two classes almost equally (0.265 vs 0.254), so the vote winner's class "ranks top" and is accepted (`llm:vote+rank`). No sensor reads a stated *relation* between two exposed items, so prescore (7.11) cannot remove the violating candidates. E1-01 ("one short end ... the other short end"), V3 ("the other short end") and V2 also state relations. Today they pass only because of good draws or prescore's `bbox`. | missing sensor (controller error not caught) |
| **D-PILOT-DIA**: board pilots Ø1.70 (M2) where M3 (G02, G11) or M2.5 (G04) is required. Gate in all three. | **RC-B1.** `board_screw` = the *smallest* catalogue screw that passes the given hole. It ignores the fastener the text names for the board ("a pilot hole ... for a 10 mm M3 self-tapping screw (through the 1.6 board)" G02 L1.3; "an M2.5" G04 L1.3; "an M3 screw through the board" G11 L1.3), and the datasheet screw of the board's holes (Pi Zero: M2.5). The lid rule reads text evidence (delta 001 C2); the board rule never does (review N4, the other direction). | wrong generic rule + missing catalogue datum |
| **D-PILOT-DEPTH**: boss pilot 6.1 where ≥ 7.6 is needed (G02 gate G6; G13 L2.8.3 "≥ 10.0 − lid plate"); standoff pilot 5.1 where ≥ 8.4 is needed (G02 L3.3.3.2). | **RC-B2.** Pilot depth = `setpoint(min_engagement)`. The screw's **length** is never used. A catalogue screw of length L through a clamped plate t protrudes L − t. A shallower pilot makes the screw bottom out before the head seats (G02 requirements note 2 says exactly this). The bottoming sensor listed for GM3 does not exist. **E1-01 has the same latent defect:** M3 × 10 through a 2.4 lid into a 6.1 pilot bottoms 1.5 mm early, and its rubric only checks ≥ 6.0. | missing sensor + wrong derivation term |
| **D-STANDOFF**: `pilot_depth_standoff_*` fails (agent-sensed) in G04, G06 and G13. | **RC-B3.** The cavity floor (`cavity.z0`) comes only from `keepout_below`. Module primaries and small keep-outs give a standoff too short for its pilot plus `min_feature` of floor. The implementer flagged this in iteration 001 ("derive the cavity floor from max(keep-out, the pilot column)"). | wrong derivation term (sensor exists) |
| **D-SD**: no microSD opening (G04 gate G5). | **RC-D.** Catalogue gap. `rpi_zero2w` has the `SD_MOUTH` / `SD_AXIS` datums and `sd_*` params, but no `sd` connector and no mating "card" part, so the slot cannot be exposed. G04 requirement A4 cites a catalogue `sd_card_zone` that does not exist in any part.json. That is a stale reference in the benchmark text. It is resolved by adding the data (D1), and the requirement's numbers stand (its precedence rule 7). | catalogue data |
| **D-SECONDARY**: fan, heatsink (G11), buttons (G13), fan and encoder (G50) are never listed by Contents. The Pico is unplaced (G06), and so are the OLED and the encoder (G50). | **RC-C.** Contents offers only kinds `board / module / connector / generic` (+ named mount_holes parts), and its prompt says "inside the enclosure". The same cause gives the 18 `nothing to design around` stops (NEMA 17, 2020 extrusion, bearings, servos and magnets are never offered) and G08's cylinder-for-a-cell. Fixing the candidate list alone yields no geometry: a non-carrier primary leaves the new items unplaced, and a carrier would put a fan *on the board*. Placing them needs GM2b relations. | missing generic rule (GM2b) |
| **D-VENT**: no vents or slots (G02 G5, G11 G5, G50; G14 waits behind RC-B4) | **RC-E.** No vent / airflow aperture generator (GM4 `vent_pattern`, GM8 `airflow`). | missing capability |
| G02 lip-in-wall lid instead of a rebate (major); G02 USB-B roof bridge 16.8 > 15 (major); G04 corner bosses push Y to 42.2 > 40 (w1); G13 / G50 multi-body (plungers), snaps; G06 tilt and window | closure variants (GM9), `printable` bridge sensor (GM5), boss placement inside the outline, GM7 | deferred |
| G01, G14 stop: no screw passes the Nano's Ø1.8 holes | **RC-B4.** Locating-pin relation not implemented (ARCHITECTURE 1a refinement 6) | missing rule (GM3) |
| G03, G05, G12 (ESP32 DevKitC, no holes), G09, G47 primaries without mount_holes | pocket / cradle support (GM6) | missing capability |

Process findings (not the agent):
- **P-1:** `../rubric.md` still does not exist. Every judge used the enclosure rubric plus the design's requirements.md, and
  wrote "Score is an estimate". The class rules (WRONG = a gate fails, MINOR = a w3 L3 fails, CORRECT = neither) are the
  same, so verdict classes are sound and scores are approximate.
- **P-2:** the judge cache can never hit on new runs. OpenSCAD 2021.01 STL facet order is not deterministic (iteration 001
  implementer's P3). All 10 iteration 002 packages were judged afresh.

## 3. Clustering and choice

Ranked by verdict payoff on the next Run per generic change. The regression comes first.

| Change | Designs whose verdict or gates move next Run | Generic capability | Chosen? |
|---|---|---|---|
| RC-A face-relation sensor | V1 (regression: MINOR → MEETS); hardens E1-01, V2, V3 against seed draws | `face` relation from text, the first slice of GM2b | **yes (first)** |
| RC-B1 board fastener from role evidence and datasheet | G02 (gate G4), G04 (gate G6), G11 (gate G2); G50 pilots made right | fastener chain (GM3) | **yes** |
| RC-B2 bottoming + RC-B3 standoff holds its pilot | G02 (gate G6, L3.3.3.2), G13 (L2.8.3), the agent-sensed failures in G04, G06 and G13; removes E1-01's latent bottoming | fastener chain (GM3): bottoming, engagement | **yes** |
| RC-D card access (catalogue) | G04 (gate G5) | connector with a mating card | **yes (data)** |
| RC-C any-kind contents | 0 verdicts next Run (moves 18+ stops to later typed stops) | GM2b | deferred (section 7) |
| RC-E vents | G02 (last gate after this delta), G11, G50 | GM4 slice | deferred (next delta's first candidate) |

Together the chosen changes clear **every gate of G04** and **two of G02's three gates**, and they fix the regression.
Every change is a rule over part data, rules data and text evidence. None reads a design id, name or number.

---

## 4. Delta 002

### C0 (RC-A, regression first): face-relation sensor between exposed items

**Rule.** When the text states how two exposed connectors face each other, Python turns the controller's reading of it
into a **controllable check**. Prescore (7.11) then removes the arrangements that break it before p_yes ranks anything.

1. **Vocabulary (data, `design_rules.json`):**
   `"face_relations": {"same": {"evidence": ["same"]}, "opposite": {"evidence": ["opposite", "other"]}, "source": ...}`.
   Generic English relation words, no design numbers.
2. **Pairs (`ArrangeContents.candidates`, after the edge vote).** The members are every exposed connector of a content
   item, plus the primary's own exposed connectors (their wall is fixed by `wall_facing`). An item with quantity > 1 is
   one member, because its copies share an edge by construction. A pair whose two members are both fixed (two connectors
   of the primary) is never asked about: no choice can change it.
3. **Evidence gate (Python, sentence-scoped, `text_evidence`).** Pair (A, B) may take relation value v only when one
   sentence of the request or an L1 names **both** A and B (an alias run of each part's `names`) and contains one of v's
   evidence words. A pair with no gated value is not asked about. If no pair is gated, no question is asked, and the
   transcript is byte-identical to today's.
4. **Controller question (one voted `tally`, label `assy_relation`).** The prompt is the request, then one line per gated
   pair: `- pair_k: <name A> (<conn> connector) and <name B> (<conn> connector)`, then "How does the request place these
   two cable connectors relative to each other?". The per-pair enum is the gated values plus `not_stated`, with
   one-line meanings: `same` = through the same end or side of the enclosure; `opposite` = through opposite ends or
   sides.
5. **Constraint only on agreement.** A relation becomes a constraint only when **every** valid sample names the same value
   and it is not `not_stated`. A split vote is recorded in `st.arrange["relations"]` and constrains nothing (7.6: one noisy
   signal never vetoes alone).
6. **Sensor (`build_plan` → `face_relation_<A>_<B>`, new check type in `assembly_checks.py`).** The relation is computed
   from the layout. `same` means the two walls are equal. `opposite` means the walls are on one axis with opposite sign.
   value = 0 when it holds, 1 when it is broken; limit 0; hard; evidence = the quoted sentence(s) and the votes. It is a
   normal controllable failure, so `prescore_survivors` removes violating candidates. If **no** feasible candidate
   satisfies it, every candidate ties on it, nothing is removed by it, and the package carries the failing check: an
   honest error, never a forced layout.
7. Record: `choices.relation[<A>|<B>] = {value, by: "llm:relation", votes, evidence}`. `design.json` `arrange.relations`
   lists asked pairs, enums, votes and constraints.

**V1 seed 2 with C0.** The gate gives the pair (module_1.usb, connector_1.jack) the enum {same, not_stated} (sentence
"... both the Pico's micro-USB port and the jack must be exposed through the same short end ..."). A unanimous `same`
removes every opposite or adjacent candidate. The survivors in vote order start with (+X, +X), and its class (p_yes
0.254) ranks top, so the decision is `prescore+llm:vote+rank`: both ports on one short end.

**Why the gate keeps the regression safe.** On the regression texts the gated enums are: V1 {same}, E1-01 {opposite}
(L1.1: "Pico 2 ... 3.5 mm jacks ... the other short end"; the implementer confirms the alias match of "jacks"), V3
{opposite}, V2 {same} (its L1.1 sentence names the Pico and the jacks and says "the same long side"). E1-01 and V3 can
never be pushed to "same". V2 is the one exposure: a unanimous wrong `same` would force the Pico onto the jacks' side.
Hence the **smoke measurement** in section 5, which is a merge condition.

### C1 (RC-B1): board fastener from role evidence, then the datasheet, then the smallest that passes

`board_screw` becomes `board_screw_choice(catalog, board_inst, rules, texts)`, with the same candidate filter as today
(kind fastener, catalogue-complete, pilot and thread fields), in this order:

1. **Role evidence (`rule:text_evidence[board]`).** Take the fasteners whose alias hits fall in a sentence with **board
   role words**: the primary's own alias run, or a word of `design_rules.json`
   `fastener_roles.board.evidence = ["board", "pcb", "standoff", "mounting hole"]`. Keep those whose thread passes the
   given hole (`thread + 2 x given_hole_clearance_min <= hole + measure_tol`, today's pass test) and take the largest
   thread. A named fastener that does not pass is noted (`board fastener <id> named but does not pass the Ø<d> hole`)
   and skipped. The N3 shared-alias rule applies ("M3 screw" names the self-tapper, not the bolt).
2. **Datasheet (`rule:interface_thread`).** The primary's `mount_holes` interface may carry `"thread": <nominal mm>` with
   a source. Take the complete fastener with that thread (within `measure_tol`) if it passes.
3. **Fallback (`rule:smallest_thread_through_board_hole`)**, today's rule, recorded as an assumption.

The lid rule is unchanged (its N4 half, lid-role evidence, waits for GM9 closures). On this split it already picks the
lid screw the judges expect.

Data (D2): `"thread"` on the mount interface of `rpi_zero2w` (2.5, Raspberry Pi Zero 2 W mechanical drawing: M2.5
holes), `arduino_uno_r3` (3.0, Ø3.2 holes for M3) and `rpi_pico2` (2.0; the datasheet gives Ø2.1 drilled holes, and M2 is the screw that fits them. This is a convention,
uncertainty low). Perfboard
gets none: a family board with given holes keeps the smallest-passing rule (OWNER_DECISIONS: M2). Gate R9 accepts an
optional positive number `thread`.

Measured on the texts (request + L1s as given to the agent):

| Text | Today | With C1 | Expected by its requirements |
|---|---|---|---|
| G02 | M2 | M3 (role: L1.3 "... M3 ... through the 1.6 board") | M3 |
| G04 | M2 | M2.5 (role: L1.3) | M2.5 |
| G11 | M2 | M3 (role: L1.3 "an M3 screw through the board"; passes Ø3.0 with clearance 0) | M3 |
| G13 | M2 | M2 (role names M2; the Ø2.0 specimen) | M2 |
| G06 | M2 | M2 (no role sentence; the LCD primary has no thread) | M2 |
| G50 | M2 | M2.5 (no role sentence; the OLED sentence has no board word; datasheet) | M2.5 |
| E1-01, V1, V2, V3 | M2 | M2 (no screw named; perfboard has no thread) | M2 (rubric section 6) |

### C2 (RC-B2, RC-B3): screws do not bottom, and standoffs hold their pilots

1. **Pilot depth term.** For a screw of catalogue `length` L through a clamped plate t:
   `depth = setpoint(max(fastener.<use>.min_engagement, fastener.<use>.length - t))`.
   - Standoffs: t = the primary's `top.z − seat.z` (from its mount_holes interface: 1.6 perfboard, 1.4 Zero).
   - Bosses: t = the lid plate (`lid.z`, which is the lid pad height too).
   - A fastener with no `length` keeps today's term.
2. **New sensor `pilot_bottoming_<node>`** (`add_minimum_checks`): value = pilot depth, limit = L − t. Engagement
   shortfall (L − t < min_engagement, e.g. M2 × 6 through 1.6) is **not** added as a failing check in this delta. It needs
   the stock-length rule of GM3 (G06 and G50 declare lengths), so it is deferred and noted.
3. **Cavity floor from the pilot column** (`derive_cavity` z0):
   `z0 = min(seat.z − keepout_below − m, seat.z − (standoff pilot depth) − rules.min_feature + floor − m)`, so
   `pilot_depth_standoff_*` holds by construction. The pilot-depth expression lives in one helper that both
   `derive_cavity` and the standoff pilot node read.

**Regression effect:** standoffs unchanged (E1-01 and V1–V3: max(5.0, 6 − 1.6) = 5.0, and keepout_below 4 dominates the
floor). Boss pilots get deeper: 6.1 → 7.7 (M3 × 10 − 2.4 lid). Each regression requirement asks ≥ 6.0, so they still
pass, and the latent bottoming is removed. This is the only regression geometry change in the delta, and judges
re-grade it.

### D1 (RC-D): microSD card access as a connector with a mating card

- New catalogue part `benchmarks/generalize/parts/card_microsd/part.json`, kind `plug`. Names: "microsd card", "micro sd
  card", "micro-sd card", "tf card". **Not** "sd slot" or "microsd slot": a slot is the receptacle, and G50's "the
  microSD slot are not used" must not hit. Geometry and datums follow `plug_microusb_b`: `PLUG_TIP`, `PLUG_AXIS`, `SEAT`,
  `OVERMOLD_FACE`.
  - The card: 11.0 × 15.0 × 1.0 (SD Association microSD physical spec).
  - The access zone outside the seated card, as the "overmold" box: 12.0 wide × 5.4 high, offset +1.0 above the card
    axis, starting at `SEAT`. This is a fingertip zone for a push-push slot. **Assumed, uncertainty medium.** The numbers
    equal the zone G04's A4 attributes to the catalogue, and the source says so.
  - `self_checks` as for the plugs.
- `rpi_zero2w`: a fourth connector `{"name": "sd", "mouth": "SD_MOUTH", "axis": "SD_AXIS", "mates": "card_microsd",
  "overhang_datum": "SD_MOUTH"}`.
- Exposure is then decided the way every connector's is: the Contents vote (`sd_exposed`, "takes a microsd card"), plus
  text coverage when "microsd card" is named (G04: "the microSD card slot ... pushed in and out").

### C3 (P-2, Run tooling, not agent code): canonical geometry hash

`run_suite.geometry_sha1` hashes each STL as its sorted triangle list, with vertices rounded to 1e-4 mm, in place of raw
bytes. The same geometry then gets the same key, so unchanged regression packages become cache hits. Old cache entries
keep their raw-byte keys and simply never hit (as today). The `code_sha1` coverage is unchanged (run_suite is not an
agent module). RUN.md section 5 wording is updated in the same delta.

## 5. Tests (each fails on `b0a4f1abe322`, passes after)

ScriptedLLM / fake LLMs only, except the one smoke measurement. Train request and L1 texts may be loaded as data
(ARCHITECTURE 6). Test names say capabilities, not design ids.

| # | Test | Asserts | Fails today because |
|---|---|---|---|
| T1 | `test_assembly.TestFaceRelation.test_same_end_replay` | V1 transcripts of `iter_002/V1_s2` (edge votes, confirm p_yes) + `assy_relation` = same ×3 → both items on one X end; `face_relation_*` passes; decision `prescore+llm:vote+rank`; no `assy_arrange_pick` | no relation stage; (−X, +X) is chosen |
| T2 | `TestFaceRelation.test_gate_enums` | gated enums on the four regression texts: V1 {same}, V2 {same}, E1-01 {opposite}, V3 {opposite}; no pair on G04 / G50 texts (primary-only connectors in one sentence without relation words) | helper missing |
| T3 | `TestFaceRelation.test_split_vote_is_no_constraint` | V2 with `same` 2 of 3 → layout equal to today's (USB on a short end, jacks on one long side) | helper missing |
| T4 | `TestFaceRelation.test_unsatisfiable_relation_is_reported` | a scripted relation no feasible candidate meets → no candidate removed by it; final `face_relation_*` fails with the quote | check type missing |
| T5 | `TestFaceRelation.test_prompts_unchanged_without_gate` | a request with no relation words: prompt sequence byte-equal to today's | new stage could add prompts |
| T6 | `TestBoardFastener.test_role_evidence_and_datasheet` | the table in C1 for the ten texts, with the `by` of each | today M2 everywhere |
| T7 | `TestBoardFastener.test_named_screw_that_does_not_pass` | M3 named for a Ø2.0-hole board → M2 + the note | no note, no role |
| T8 | `test_parts.TestInterfaces.test_thread_field` | R9 accepts a positive `thread`, rejects 0, a negative or a string | field unknown |
| T9 | `TestPilotBottoming.test_boss_pilot_clears_screw_tip` | E1-01 offline: boss pilot depth ≥ 10 − lid.z + margin; standoff pilot 5.1 unchanged; `pilot_bottoming_*` present and passing | check missing; boss pilot 6.1 |
| T10 | `TestPilotBottoming.test_standoff_holds_its_pilot` | module primary with a thin keep-out (Zero 2 W, M2.5 by role text) offline: every `pilot_depth_standoff_*` passes; standoff height = depth + min_feature − floor + margin | −1.39 today |
| T11 | `TestPilotBottoming.test_long_screw_through_board` | Uno primary, M3 × 10 by role text: standoff pilot ≥ 8.4, boss ≥ 7.6 | 5.1 / 6.1 |
| T12 | `test_parts.TestCardAccess` | `card_microsd` passes the gate; the Zero has an `sd` connector mating it; the sweep section at the mouth is 12.0 × 5.4 ± tol | part missing |
| T13 | `TestExposure.test_card_slot_exposed_by_text` | Zero primary + G04-shaped text offline: `wall[board.sd] = -X`, one −X aperture, text_coverage passes; a text saying "the microSD slot is not used" gives no coverage hit | connector missing |
| T14 | `test_generalize_suite.test_geometry_hash_is_order_free` | two STLs with permuted facets → equal `geometry_sha1` | byte hash |
| T15 | `test_no_hardcoding` | green; no new literal in agent modules (the role and relation words live in design_rules.json) | — (guard) |

**Offline regression invariance (implementer, before any Run).** With scripted answers, E1-01, V1, V2 and V3 must give
the same poses, fasteners, spec and question labels as iteration 002. The only differences allowed are the boss pilot
depth (C2), the new `assy_relation` question where the gate fires, and V1's arrangement.

**Smoke measurement (merge condition for C0; live ornith-1.5:9b on a scratch tree, as in iteration 001).** Run the
`assy_relation` question alone on the four regression texts at seeds 1 to 5 (20 tallies, about 60 calls, minutes). C0
merges only if no regression text ever gets a **unanimous wrong** constraint: V2 must never be unanimous `same`, V1 must
never be unanimous `not_stated` on more than 2 of 5 seeds. If V2 fails, C0 ships with V2-shaped pairs excluded by one
generic rule: a "same" whose sentence also names a different edge type for one member ("short ... end" vs "long ...
side", Python's own edge words) is not gated. That rule is pre-written here so the implementer does not invent one.

## 6. Expected effect (next Run, SEED 3)

| Design | Now | Expected | Why |
|---|---|---|---|
| V1 | MINOR 0.92 | **MEETS** | C0: same-end class only |
| E1-01, V2, V3 | MEETS | MEETS | boss pilot deeper (still ≥ 6.0); prompts otherwise unchanged except a gated `assy_relation` |
| G04 | WRONG 0.82 | **CORRECT** (DNM: bbox Y 42.2 > 40, w1, stays) | C1 M2.5 pilots (G6); D1 −X SD opening (G5); C2 standoffs hold the 6.7 pilot (Z 15.9 → about 19, limit 22) |
| G02 | WRONG 0.74 | WRONG, gates 3 → 1 (vents) | C1 M3 pilots (G4); C2 standoff pilot 8.5, boss 7.7 (G6, L3.3.3.2); standoff height about 7.0 (band 4–10); Z about 29 (limit 35) |
| G11 | WRONG 0.55 | WRONG, gates 3 → 2 (fan, exhaust) | C1 M3 pilots (G2) |
| G06, G13 | WRONG | WRONG (agent `pilot_depth_*` now pass; G13 boss depth row passes; G13 Z +0.5, already over) | C2 |
| G50 | WRONG | WRONG (pilots now M2.5) | C1 datasheet |
| 34 no-output | unchanged stops | unchanged | nothing here touches Contents or the archetype gate |

**Train: MEETS 0, CORRECT 0 → 1. Regression: fail → pass.** Uncertainty: medium for G04 (the judge may find a new
interaction of the SD opening with a corner boss) and low for V1 (conditional on the smoke measurement).

## 7. Deferred, and why

- **RC-C any-kind Contents (GM2b) — the largest cluster (18 stops + G08 + the missing parts of G11, G13, G50).** Offering
  every named part (any kind except plug and fastener) and dropping "inside the enclosure" from the prompt is simple.
  But next Run it moves stops from `contents` to `primary has no mount_holes` or to the archetype gate, and turns no
  stop into geometry. On a carrier it would also place fans and displays on the board. It must land together with the
  first relation enums that place secondary items (`against` / `on_pattern` for a fan on a lid, `face` for a window), or
  with GM5's `plate` / `bracket` archetypes. That is the next milestone after this delta, and ARCHITECTURE 1b says so.
- **RC-E vents (GM4 slice).** This is the last gate of G02 after this delta, and a gate of G11 and G50. Generic vents need
  an aperture-through-any-face generator, a placement region (a hot-zone datum per part, or "over part X" relations) and
  an area rule. That is more than one delta can carry safely next to the regression fix. **It is the first candidate for
  delta 003.**
- **RC-B4 locating pins** (G01, G14) and **pocket / cradle primaries** (G03, G05, G09, G12, G47): GM3 / GM6 as planned.
- **Engagement shortfall and stock screw lengths** (G06, G50 declare lengths; M2 × 6 through 1.6 gives 4.4 < 5.0): the
  GM3 fastener-chain length rule. Adding the sensor now would fail every perfboard design without an actuator.
- **G02 rebate lid, G02 bridge, G04 bosses outside the outline:** GM9 closures, the GM5 `printable` sensor, and the
  boss-placement rule. Each is one design today.
- **P-1 `../rubric.md`:** still missing. The verdict classes are unaffected. It should be written before the first
  held-out measurement, because every held-out score depends on it. Not an agent change.
