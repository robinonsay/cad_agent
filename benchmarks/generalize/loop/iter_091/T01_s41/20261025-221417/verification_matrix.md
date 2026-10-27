# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
FAIL     -4.918  L1.1: The design shall carry one Shimano SM-SH51 cleat (catalogue cleat) with its mount face against the adapter's cleat seat, fastened by the cleat's own two bolt positions with standard M5 hardware (catalogue M5 socket-head bolts and M5 hex nuts), and shall declare the layout (cleat pose, bolts, nuts, grip features, print orientation).
      ok  clear_primary [clear_of] min gap to primary 0.0000 mm (need >= 0)
      ok  clear_recess [clear_of] min gap to keepout_recess 0.0000 mm (need >= 0)
      ok  travel_x [travel] min gap to travel_0 0.2500 mm (need >= 0)
      NO  travel_y [travel] bodies penetrate travel_1 by 119 mm3 at [[-9.9853, -5.0, 0.0], [9.9853, 5.0, 8.0]]; conflict: the cleat_shimano_sm_sh51 declares 5 mm of adjustment along y, but a captive hex nut stops turning only while it slides along one direction (the slots cover 20 mm along x); a requirement question: accept the covered axis, or a nut plate / threaded insert the catalogue does not hold
      ok  bolt_engagement_0 [bolt_engagement] design check: tip z 8.000 vs nut top 6.800 (bolt_m5_iso4762 10 mm)
      ok  nut_trap_0 [nut_trap] channel width 8.400 mm across the slide at the nut axis: 0.200 per flat side (band 0.1-0.4), corners 8.79
      ok  bolt_engagement_1 [bolt_engagement] design check: tip z 8.000 vs nut top 6.800 (bolt_m5_iso4762 10 mm)
      ok  nut_trap_1 [nut_trap] channel width 8.400 mm across the slide at the nut axis: 0.200 per flat side (band 0.1-0.4), corners 8.79
      ok  form_evidence [form_evidence] the design is a plate; request names it
UNLINKED         L1.2: The cleat shall be adjustable fore-aft by at least 20 mm and sideways by at least 5 mm, as on a shoe, and shall clamp firmly at any position in that range; each nut shall be held captive so that it does not turn when a bolt is tightened with a 4 mm hex key.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +1.000  L1.3: At every cleat position in that range the M5 hardware shall fit: each bolt head shall seat on the cleat and be reachable with a 4 mm hex key from the pedal side with the adapter off the pedal, each bolt shall engage its nut for its whole thickness, and no bolt tip shall reach the top face of the platform.
      ok  form_evidence [form_evidence] the design is a plate; request names it
PASS     +0.010  L1.4: The adapter shall let the cleat clip into the SPD pedal: with the adapter on the pedal in the engaged pose, nothing but the cleat shall enter the pedal's binding space or the cleat's recess space, at every cleat position in the adjustment range.
      ok  clear_mech_1 [clear_of] min gap to engaged 0.0000 mm (need >= 0)
      ok  clear_mech_1_binding_cage [clear_of] min gap to keepout_mech_1_binding_cage 0.0000 mm (need >= 0)
      ok  clear_mech_1_crank_side [clear_of] min gap to keepout_mech_1_crank_side 0.1887 mm (need >= 0)
      ok  handedness_plate [handedness] mirror image does not clear keepout_mech_1_crank_side (penetrates it by 264.6 mm3); a mirror pair is declared (the left part is the exact mirror image)
      ok  form_evidence [form_evidence] the design is a plate; request names it
PASS     +1.000  L1.5: The adapter's pedal-side face shall sit on the pedal's sole plane like a shoe sole: no adapter material below that plane outside the cleat, and a flat bearing area of at least 600 mm2 on it.
      ok  bearing_area [bearing_area] underside area 3836.0 mm2
      ok  form_evidence [form_evidence] the design is a plate; request names it
PASS     +1.000  L1.6: The adapter shall clear the crank arm: with the cleat at any position in its sideways range, and the adapter twisted about the cleat axis through the release angle either way, every point of the adapter shall stay at least 2.0 mm from the crank arm's inner face.
      ok  form_evidence [form_evidence] the design is a plate; request names it
PASS     +0.110  L1.7: The platform shall be sized like a commercial flat pedal: each plan dimension between 80 and 105 mm, with a thickness above the pedal-side face of 8 to 14 mm, not counting the grip features.
      ok  plate_size_x [plate_size] plan length 80.100 mm
      ok  plate_size_y [plate_size] plan length 80.100 mm
      ok  plate_thickness [plate_thickness] thickness 12.400 mm at the corners
      ok  form_evidence [form_evidence] the design is a plate; request names it
PASS     +1.000  L1.8: The top face shall carry grip features for shoes: at least 8 raised pins or ridges, each 1.5 to 5.0 mm tall, spread over at least 60 percent of the platform's plan area and kept at least 3 mm from its edge.
      ok  surface_features [surface_features] 8 studs features, spread 74.2 %
      ok  form_evidence [form_evidence] the design is a plate; request names it
PASS     +0.038  L1.9: The adapter shall carry a standing rider: a 2500 N load on a 30 x 30 mm patch at the outer edge of the platform, with only the cleat clamp footprint as support, shall give a bending stress at most 1/1.5 of the printed material's 25 MPa in-plane strength.
      ok  load_stress [load_stress] worst bending stress 16.03 MPa at edge +y (arm 6.85 mm) vs 16.67 MPa
      ok  form_evidence [form_evidence] the design is a plate; request names it
UNLINKED         L1.10: One printed part shall serve both pedals: the part and its mirror image shall both pass every check above (or the design shall declare a left/right pair of two mirror-image parts, each passing every check on its own pedal).  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.11: Each printed body shall be one manifold body that prints in PETG on an FDM printer without supports in its declared orientation, with no feature thinner than 0.8 mm, and fit a 200 x 200 x 200 mm bed.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.12: The design shall be delivered as the STL of each printed body, the OpenSCAD source, the declared layout and the agent's own clearance and strength report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.273  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'plate': 1}, worst overlap 0 mm3 (max 1)
      ok  clear_fasteners [clear_of] min gap to fasteners 0.2633 mm (need >= 0)
      ok  bolt_tip_0 [bolt_tip] design check: top face z 9.400 vs tip 8.000
      ok  bolt_tip_1 [bolt_tip] design check: top face z 9.400 vs tip 8.000
      ok  printable [printable] top_face_down: longest bridge 8.40 mm (max 15), steep overhang area 0.00 mm2
      ok  bbox [bbox_within] outside 80.10 x 80.10 x 12.40 mm, max 200 x 200 x 200
```

- PASS separable: shells {'plate': 1}, worst overlap 0 mm3 (max 1)
- PASS clear_primary: min gap to primary 0.0000 mm (need >= 0)
- PASS clear_fasteners: min gap to fasteners 0.2633 mm (need >= 0)
- PASS clear_recess: min gap to keepout_recess 0.0000 mm (need >= 0)
- PASS clear_mech_1: min gap to engaged 0.0000 mm (need >= 0)
- PASS clear_mech_1_binding_cage: min gap to keepout_mech_1_binding_cage 0.0000 mm (need >= 0)
- PASS clear_mech_1_crank_side: min gap to keepout_mech_1_crank_side 0.1887 mm (need >= 0)
- PASS handedness_plate: mirror image does not clear keepout_mech_1_crank_side (penetrates it by 264.6 mm3); a mirror pair is declared (the left part is the exact mirror image)
- PASS travel_x: min gap to travel_0 0.2500 mm (need >= 0)
- FAIL travel_y: bodies penetrate travel_1 by 119 mm3 at [[-9.9853, -5.0, 0.0], [9.9853, 5.0, 8.0]]; conflict: the cleat_shimano_sm_sh51 declares 5 mm of adjustment along y, but a captive hex nut stops turning only while it slides along one direction (the slots cover 20 mm along x); a requirement question: accept the covered axis, or a nut plate / threaded insert the catalogue does not hold
- PASS bolt_engagement_0: design check: tip z 8.000 vs nut top 6.800 (bolt_m5_iso4762 10 mm)
- PASS bolt_tip_0: design check: top face z 9.400 vs tip 8.000
- PASS nut_trap_0: channel width 8.400 mm across the slide at the nut axis: 0.200 per flat side (band 0.1-0.4), corners 8.79
- PASS bolt_engagement_1: design check: tip z 8.000 vs nut top 6.800 (bolt_m5_iso4762 10 mm)
- PASS bolt_tip_1: design check: top face z 9.400 vs tip 8.000
- PASS nut_trap_1: channel width 8.400 mm across the slide at the nut axis: 0.200 per flat side (band 0.1-0.4), corners 8.79
- PASS plate_size_x: plan length 80.100 mm
- PASS plate_size_y: plan length 80.100 mm
- PASS plate_thickness: thickness 12.400 mm at the corners
- PASS bearing_area: underside area 3836.0 mm2
- PASS load_stress: worst bending stress 16.03 MPa at edge +y (arm 6.85 mm) vs 16.67 MPa
- PASS printable: top_face_down: longest bridge 8.40 mm (max 15), steep overhang area 0.00 mm2
- PASS surface_features: 8 studs features, spread 74.2 %
- PASS bbox: outside 80.10 x 80.10 x 12.40 mm, max 200 x 200 x 200
- PASS form_evidence: the design is a plate; request names it
