# Owner decisions (Robin, 2026-10-24)

These answer the four open questions that had blocked convergence since iteration 005. They
override earlier assumptions. `requirements.md` and `rubric.md` were updated the same day
(copies from before the update: `iter_009/*_before_owner_decisions.md`). Judges now grade against
the new values.

1. **Board hole grid: measured from the photo.**
   - **Grid:** 24 × 18 holes at 2.54 pitch, centred on the board. On a 70 × 50 board, the first
     column is X 5.79 and the first row is Y 3.41. It is NOT registered to corner hole 1.
   - **Corner holes:** 2.0 in from each edge (pitch 66.0 × 46.0), Ø2.0.
   - **Board screws:** M2 self-tapping, pilot Ø1.6–1.8. M2.5 would not pass a Ø2.0 hole.
   - **Edge pads:** a column of elongated pads at X ≈ 2.2 and X ≈ 67.8 is not part of the grid.
   - **Method and uncertainty:** requirements.md A7.
2. **Jack: PJ-320A, fixed.**
   - Its terminals are not on 0.1 in, so the jacks are exempt from the grid rule. L2.1.6 /
     L3.1.6.1 now apply to the Pico's header pins only.
3. **Lid: fixed by L2.7.5.**
   - A flat plate covering the base's whole outer outline (± 0.5), 2.0–3.0 thick.
   - A continuous locating lip: engagement 2.0–3.0, fit 0.15–0.35 per side.
   - Total lid height ≤ 6.0.
   - 4 × M3 screws into base corner bosses.
   - No snap, sliding or deep cap lid.
   - **Units check:** L3.12.1.1 now applies to each body's largest axis only, so a thin lid is
     not a units error.
4. **Designed contact is not interference** (requirements 1.3).
   - The board resting on the standoff tops, a screw in its pilot, the lid lip on its seat and the
     lid on the rim never count as interference.
   - V-INSTALL excludes the V-SEAT columns.

## Consequences for the agent

The next gap analyst should expect these defects and treat them as agent/catalogue work:

- **The Pico now sits with its first header pin on grid column 0.** In the default layout:
  - PCB end 4.42 in from the −X edge
  - `USB_MOUTH` at X 3.12, inside the board edge (L2.1.3: X in [2.62, 3.62])
  - pin rows on grid rows 5 and 12 (Y 16.11 / 33.89)

  So the micro-USB overmold must pass over the board margin and enter the end-wall opening. The
  plug envelope (V-USB-PLUG), not a flush-to-edge rule, sets the USB opening.
- **`parts/perfboard/part.json` must model the centred grid and the measured holes.** The
  catalogue part must stay parametric for the variants. A generic representation is a grid
  centred on the board, with column and row counts derived from the board size and an edge margin,
  or given as params. It must not be a hard-coded 70 × 50 special case. Variants keep their own
  boards.
- **An M2 self-tapping screw part is needed in the catalogue** for the board screws. M3 stays for
  the lid.
- **The lid derivation must meet L2.7.5's numbers,** including outline match and total height
  ≤ 6.0.
- **The seating / installation checks must exclude designed contact.**

## Test-data corrections, 2026-10-24 (after iteration 013; Q9, Q8)
- Q9: V1 and V2 USB-mouth windows in variants.json now follow decision 1 (Pico on grid column 0):
  V1 [2.54, 3.54], V2 [2.46, 3.46]. The V1 jack window stays [-1.8, 0.5] (jacks are exempt from the grid).
- Q8: rubric.md section 6 standoff pilot is now Ø1.6–1.8 (M2), matching L2.3.3 / A9.
- These are judge-side data only; no agent code or part data changed, so the agent version is unchanged.
- Backups: loop/iter_013/owner_fix/.
