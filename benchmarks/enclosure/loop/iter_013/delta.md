# Iteration 013: gap analysis and delta design

Analyst: gap/delta step, iteration 013. Tooling: the claude-context MCP server failed to connect in this session (it
was reported as configured but unreachable). I read files at known paths and ran only targeted shell checks, with no
code search.

## 1. Where the loop stands

Iteration 013 was the convergence-confirmation Run on frozen code (iter_012/delta.md C0, ARCHITECTURE.md 8).

- **Freeze proof.** `shasum -c iter_013/code_sha1.txt` printed 9 × OK, both in the Run step (`run_driver.log`) and
  again now. The parts catalogue (`benchmarks/enclosure/parts/`, 12 files, combined hash `235689f7bea6`) and every
  `test_*.py` file were last modified before the iteration-012 runs (parts 18:03, tests 18:25, runs from 19:14). So
  the agent version that produced iterations 012 and 013 is one version, data included.
- **Runs (6 rows, all rc 0, `missing: []`).** E1-01_s13 and E1-01_s14 as planned. The Run step also ran target_s0,
  V1_s0, V2_s0 and V3_s0. This was more than RUN.md 3.1a asked for, but harmless: same code, and it adds evidence.
- **Judged.** E1-01_s13, V1_s0, V2_s0, V3_s0, two judges each, both judges agreeing on every run.

| Run | Verdict | Class | Score | Worst w3 margin | Failing L3 |
|---|---|---|---|---|---|
| E1-01_s13 | **MEETS** | CORRECT | 1.0 | +0.20 | none |
| V1_s0 | DNM | CORRECT | 0.985 | +0.20 | L3.1.3.1 (w2), Q9 |
| V2_s0 | DNM | CORRECT | 0.985 | +0.20 | L3.1.3.1 (w2), Q9 |
| V3_s0 | **MEETS** | CORRECT | 1.0 | +0.20 | none |

- **Unjudged E1-01 runs.** I measured E1-01_s14 and target_s0 against the judged E1-01_s13 with manifold3d. For both
  base.stl and lid.stl, the boolean symmetric difference is 0.0 mm³, and `layout.json` is identical. The same is true
  against iteration 012's judged MEETS packages (target_s0 and E1-01_s12). Every E1-01 run on this version
  (seeds 0, 12, 13, 14) delivers the same geometry. The transcripts differ by seed (14 of 18 `llm/` files differ
  between s13 and s14), but the controller lands in the same design.

## 2. Defects and root causes

### D1: L3.1.3.1 on V1 and V2 (weight 2). Not an agent gap; a requirements conflict (Q9, unchanged since 011)

- **Observed.** The Pico USB_MOUTH is at X 3.04 (V1) and 2.96 (V2). The V1 grading delta wants [-1.8, 0.5] and the V2
  delta wants [-1.8, -0.8].
- **Trace.** The agent puts the Pico's first header pin on grid column 0, nearest the USB edge (OWNER_DECISIONS 1 and
  2, L2.1.3, L3.1.6.1, ARCHITECTURE 7.13). The grid is the family default from part data: centred, with an edge
  margin. On the 80 mm and 90 mm variant boards, column 0 is at X 5.71 and 5.63. The Pico's pin-to-mouth offset is
  fixed by its part.json, which puts the mouth at X 3.04 and 2.96. Meeting either window would put every pin at least
  2.5 mm off grid, which fails L3.1.6.1 (w1) and the owner's on-grid decision. Both pairs of judges reached this
  independently and asked Robin to fix the delta. For example, a mouth window like E1-01's [column-0 mouth ± 0.5]
  gives V1 [2.54, 3.54] and V2 [2.46, 3.46].
- **Why no agent change.** The only agent-side "fix" would be to drop the grid rule for variants, or special-case
  them. That would be hard-coding against the owner's decision, and it would trade a w2 failure for a w1 failure. The
  variants already meet ARCHITECTURE 8's bar (at least CORRECT), so D1 does not block convergence.
- **Root cause.** Test data: judge-side `grading_deltas` in variants.json. This is **Q9** for Robin.

### Observations (no verdict cost), traced

- **O1, thin margins** (judges: keep-outs 0.10, plug clearances 0.40 against 0.30, lip engagement 2.1, pilot depths
  5.1 and 6.1).
  - **Trace.** These are the deliberate setpoint rule (ARCHITECTURE 7.9: every one-sided minimum is driven to
    limit + `design_margin` from `design_rules.json`). The value is generic, not target-specific.
  - **Disposition.** Raising it is a single data change, but it would be a new agent version and restart the
    convergence count. Deferred: **Q15** for Robin (what print-tolerance margin does he want above each limit?).
- **O2, rubric conflicts.**
  - Standoff pilot Ø2.0–2.2 in the rubric against Ø1.6–1.8 in requirements (Q8).
  - End-wall slab recipe counts blind boss pilots, and the V-CAVITY leak (Q13).
  - Both are judge-side. The judges graded against requirements.md, which the agent follows.
- **O3, V2 jacks touch the Pico PCB edge with 0 gap. O4, the V3 capacitor is 0.16 mm from the Pico.**
  - There is no part-to-part assembly gap in requirements. This is RC-1201, deferred pending **Q12**, as recorded
    in iteration 012.
  - Not touched under the freeze.
- **O5, board screw fit.** An M2 screw in the Ø2.0 photographed holes has zero clearance. This is OWNER_DECISIONS 1
  (M2 self-tapping; M2.5 would not pass). Ungraded and owner-decided: noted only.
- **RC-1202** (arrangement tie broken by `SIDES` order). The contingent C1 is **not triggered**. No seed failed at the
  arrangement: s13 and s14 picked the same edge class as s0 and s12 (identical layout.json).

### Process gap found this iteration (no verdict cost)

- **RC-1301.** `code_sha1.txt` hashes the 8 agent modules and `design_rules.json`, but not the parts catalogue. Part
  data drives the agent: specimen selection, grids, pin offsets. So today the same-SHA rule (ARCHITECTURE 8) cannot
  by itself prove "one agent version".
- For iterations 012 and 013 I verified it separately by modification time (section 1).
- Fix (bookkeeping, no agent code): from the next code change on, `code_sha1.txt` also lists every
  `benchmarks/enclosure/parts/**/part.json`. ARCHITECTURE 8 has been updated to say so.

## 3. Delta

**Converged: no agent change.** iter_012/delta.md C0.4, first case: E1-01_s13 MEETS on the iteration-012 version.
ARCHITECTURE.md section 8 is now satisfied on one agent version (`iter_012/code_sha1.txt`, parts catalogue
unchanged):

1. **E1-01 MEETS on 3 seeds:** 0 and 12 (iteration 012) and 13 (iteration 013). Seed 14 and a repeat of seed 0 are
   geometrically identical to them (section 1).
2. **V1, V2 and V3 each at least CORRECT on at least 1 run:**
   - V1 and V2 are CORRECT on seeds 0 (twice) and 12.
   - V3 MEETS on seeds 0 (twice) and 12.
3. **`test_no_hardcoding` green** and the full suite green (385/385, iteration 012, on this exact code and these
   exact test files).

Implementation step for this iteration (no code, no tests changed):

- **C0. Record convergence.**
  - **LEDGER.md:** add the iteration-013 entry and a progress row: E1-01 MEETS (s13; s14 and s0 identical
    geometry), V1/V2 DNM/CORRECT (Q9), V3 MEETS, Convergence status **CONVERGED** on version iter_012 SHA.
  - **Freeze proof:** copy `iter_013/code_sha1.txt` into the entry.
- **C0.1. Re-run the full unit suite once** on the frozen tree, to record green alongside the convergence claim. Use
  the RUN.md command plus the 5 new test files, with no Ollama. Expect 385/385 OK. If it is not green, convergence
  is not claimed. Do a normal gap analysis on the failure instead.
- **C0.2. Parts hash (RC-1301).** Append the parts catalogue hashes as a separate line block in the ledger entry,
  not in `code_sha1.txt` (so its 9-line `shasum -c` check stays as it was). Use
  `find benchmarks/enclosure/parts -name part.json | sort | xargs shasum`. Future freezes include these in
  `code_sha1.txt` (ARCHITECTURE 8).
- **C0.3. RUN.md.** Mark section 3.1a as done (iteration 013). Add a line saying that the loop's stop condition is
  met, and that any later Run step requires a new delta, which starts a new version count.

**Explicitly not done, and why.**

- **C1 (joint vote):** its trigger did not happen, and any code change would void the convergence just reached.
- **RC-1201 / Q12 (part-to-part gap), O1 / Q15 (margin size), D1 / Q9:** these are owner decisions or judge-side
  data. If Robin wants any of them, it becomes a new post-convergence delta with its own 3-seed count.

## 4. Tests

None new, none changed. C0.1 re-runs the existing suite to record the green result next to the convergence claim.

## 5. Expected effect on the verdict

None, because nothing changes. The loop's error signal is zero on E1-01 across 4 seeds. The only remaining graded
failure (V1/V2 L3.1.3.1) is a requirements conflict that no agent change can fix without breaking the owner's grid
rule.

## 6. Questions for Robin

- **Q9.** The V1 and V2 USB-mouth windows contradict the on-grid rule. Suggested windows are column-0 mouth ± 0.5:
  V1 [2.54, 3.54] and V2 [2.46, 3.46].
- **Q8.** The rubric's section 6 standoff pilot is Ø2.0–2.2; requirements L2.3.3 / A9 say Ø1.6–1.8.
- **Q12.** Should there be a minimum part-to-part gap (V2 jacks touching the Pico, the V3 capacitor at 0.16)? And
  should the PJ-320A body come from the drawing?
- **Q13.** The rubric's cavity definition leaks through the openings, and the end-wall slab recipe counts blind
  pilots.
- **Q14.** Counterbored lid M3 holes?
- **Q15 (new).** Several limits are met by exactly the 0.10 design margin, which judges called fragile under print
  variation. Do you want a larger generic margin (one `design_rules.json` value)?
