- D1-06 (C seed0): cue "edge" fires on "20 mm tall at its back edge" (the wedge's own edge, a height
  profile), demanding a placement edge test -> requirement left unverified. Cue should skip
  "tall/high/thick at its X edge" phrasing.
- D2-02 (C seed0) FALSE PASS: balls under the bar near its ends; arrangement "ends" check passes at
  normalised x = +-0.62 (inside the bar's extent). "At each end of a bar" for a dumbbell = on the end
  faces. Fixes: (a) arrangement ends: optional "beyond"/side-aware variant, or record side in the
  check text so back-translation sees "under the bar"; (b) cascade validation layer: run the
  default mode's design back-translation (Python description of each part vs request) through the
  judge panel as a system check before declaring "verified".
- D2-04 (C seed0): design loop move "divider.arrangement=ends_y" with count 3 lays out only 2 copies
  (ends = 2 positions) -> a divider silently vanishes; count check catches it (unsatisfied, not a
  false pass). Fix: never offer/accept "ends" unless count == 2; layout must never drop copies.
- D2-05 (C seed0) unsatisfied (honest): egg 43 mm leaked into cup inner diameter (1 mm walls, problem 5),
  and the wrong "egg fits INTO cup" check passed the gates again: the satisfiability gate abstained
  because an accepted check (2 mm wall) already failed on the provisional design. Abstain rule is too
  broad: abstain only on system inconsistency (overlap/disconnected), and judge conflicts only against
  accepted checks that pass now (the original rule) - or evaluate against a deadbeat-corrected design.
