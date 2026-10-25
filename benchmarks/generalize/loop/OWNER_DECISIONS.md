# Owner decisions: generalization loop

## D1 (2026-10-25): the small LLM is the controller; Python is the plant, the sensors and the guardrails

Robin: "I want to make it a real controller so it can generalize better. ... A rules-based approach is very fragile."

**Why.** In the converged enclosure run, the 9B model answered 18 questions. It decided only the text-to-slot
mapping, the part counts and which ends the ports face. Python rules decided everything else, and overruled it twice.
Over 14 enclosure iterations the loop replaced each LLM mistake with a rule, because rules pass the judges. Rules keyed
to one family's phrasing do not survive new design families or new wording. That is the fragility.

**The target architecture (run time).**
- **Plant:** Python resolves a feature graph into solids. It is deterministic, exact and continuous: formulas,
  datums, sizing to limits, grid snapping (the inner loop stays Python).
- **Sensors:** Python checks measure the design and report a typed error vector. For each failing check it says
  which requirement, where (body, feature, coordinates), by how much, and in which direction.
- **Actuators:** a typed, generic action space that Python validates before applying it. Examples: add, remove or
  modify a feature; choose or replace a catalogue part; set a relation (faces, mates, on edge, through wall, pin
  through); change a parameter within its bounds; pick a structural form. Python rejects malformed or infeasible
  actions and explains why.
- **Controller:** the small LLM. It reads the request, the L1s, the current design state and the error vector, then
  chooses the next action. It is closed loop: build → sense → choose a correction → rebuild, until the checks pass or
  a step budget runs out.
  - Each controller choice is discrete and checked: voted, optionally by the 3-model panel. Free-form numbers are
    never trusted; parameters are set within Python-supplied bounds or by Python's sizing.
  - Python may keep an action only if it does not raise the error (or it falls within a trust region), and it feeds
    back what happened.
- **Guardrails (allowed rules):** physics and manufacturability that hold for any design. Examples: manifold
  solids, minimum wall, printable overhangs, a screw that physically fits its hole, designed contact.

**What Python must no longer do.** Decide what the request means. A rule that reads the text and picks a semantic
answer (which part, which edge, exposed or not, which form, which closure) is a *semantic rule*. Semantic rules are
replaced by sensors: the same knowledge becomes a failing check that the controller sees and corrects. For example,
`rule:text_coverage` becomes a check "L1.5 names a micro-USB cable, but the USB connector is not exposed", which the
LLM fixes.

**How the development loop changes.**
1. **Classify every change.** Each change is one of: sensor, actuator, controller information (state or error
   presentation, prompts, option menus), guardrail, plant, or semantic rule. Semantic rules are not allowed. A rule
   registry (`controller_rules.json`) lists every `rule:*` decision with its class and justification. A test fails
   on any rule not in the registry, and the reviewer rejects new semantic rules.
2. **Measure the controller's authority.** Every iteration also runs the train suite with a stub controller (always
   the first option, no corrections). It needs no LLM, so it is fast. A design where the stub produces the same
   geometry as the real LLM is one the LLM did not control.
3. **Disturbance tests for fragility.** Each design gets 2 paraphrases of its request and L1s: the same numbers and
   meaning in different words. Runs rotate through the original and the paraphrases, and convergence needs passes on
   all three.
4. **Convergence adds:**
   - the stub controller meets at most 25% of train designs (by its own verification)
   - the rule registry test is green
   - MEETS holds across the paraphrases

   The held-out bar (≥ 80%) and the train bar (≥ 90%) stay.
5. **Regression during the migration.** The converged enclosure is preserved at commit `442f57a` (branch
   `enclosure-control-loop`). Migration deltas may regress E1-01 temporarily, if the reviewer agrees the change is
   on the path. It must MEET again before convergence.
