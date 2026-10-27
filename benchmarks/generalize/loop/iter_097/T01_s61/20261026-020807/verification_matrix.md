# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
FAIL     -1.000  L1.1: The design shall carry one Shimano SM-SH51 cleat (catalogue cleat) with its mount face against the adapter's cleat seat, fastened by the cleat's own two bolt positions with standard M5 hardware (catalogue M5 socket-head bolts and M5 hex nuts), and shall declare the layout (cleat pose, bolts, nuts, grip features, print orientation).
      ok  clear_primary [clear_of] min gap to primary 0.0000 mm (need >= 0)
      ok  travel_x [travel] min gap to travel_0 0.0000 mm (need >= 0)
      ok  travel_y [travel] min gap to travel_1 0.0000 mm (need >= 0)
      ok  bolt_engagement_0 [bolt_engagement] design check: tip z 10.000 vs nut top 8.900 (bolt_m5_iso4762 12 mm)
      ok  nut_trap_0 [nut_trap] channel width 8.400 mm across the slide at the nut axis: 0.200 per flat side (band 0.1-0.4), corners 8.79
      ok  bolt_engagement_1 [bolt_engagement] design check: tip z 10.000 vs nut top 8.900 (bolt_m5_iso4762 12 mm)
      ok  nut_trap_1 [nut_trap] channel width 8.400 mm across the slide at the nut axis: 0.200 per flat side (band 0.1-0.4), corners 8.79
      ok  nut_frame_turn [nut_frame_turn] design check: frame diagonal 37.48 mm vs pocket width 27.00 mm
      ok  clamp_seat_0 [clamp_seat] fastener seat: worst 100% of the nominal bearing (31.6 of 31.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      NO  fastener_bearing_0 [fastener_bearing] nut_frame seat under a 970 N preload (rule:default_preload): bearing pressure 30.70 MPa on 31.6 mm2 (allowed 16.67), punch-through shear 16.66 MPa on 58.2 mm2 (the face outline over 2.10 mm of floor; allowed 8.33) at shift [0.0, 0.0]; conflict: the nut_frame seat carries 2.00 x what the printed material allows under the 970 N preload (rule:default_preload), and no buildable retention option changes the seat: a requirement question (a stated lower preload, a stronger material, a washer or a nut plate the catalogue does not hold)
      ok  clamp_seat_1 [clamp_seat] fastener seat: worst 100% of the nominal bearing (31.6 of 31.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      NO  fastener_bearing_1 [fastener_bearing] nut_frame seat under a 970 N preload (rule:default_preload): bearing pressure 30.70 MPa on 31.6 mm2 (allowed 16.67), punch-through shear 16.66 MPa on 58.2 mm2 (the face outline over 2.10 mm of floor; allowed 8.33) at shift [0.0, 0.0]; conflict: the nut_frame seat carries 2.00 x what the printed material allows under the 970 N preload (rule:default_preload), and no buildable retention option changes the seat: a requirement question (a stated lower preload, a stronger material, a washer or a nut plate the catalogue does not hold)
      ok  clamp_frame [clamp_frame] nut frame on the pocket floor: worst 533% of the nominal bearing (337.5 of 63.3 mm2) at shift [0.0, -2.5], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_face [clamp_face] bolted face on the plate: worst 1282% of the nominal bearing (845.8 of 66.0 mm2) at shift [0.0, -2.5], axis inside the bearing (need >= 30%, axis inside)
FAIL     -1.000  L1.2: The cleat shall be adjustable fore-aft by at least 20 mm and sideways by at least 5 mm, as on a shoe, and shall clamp firmly at any position in that range; each nut shall be held captive so that it does not turn when a bolt is tightened with a 4 mm hex key.
      ok  travel_x [travel] min gap to travel_0 0.0000 mm (need >= 0)
      ok  travel_y [travel] min gap to travel_1 0.0000 mm (need >= 0)
      ok  clamp_seat_0 [clamp_seat] fastener seat: worst 100% of the nominal bearing (31.6 of 31.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      NO  fastener_bearing_0 [fastener_bearing] nut_frame seat under a 970 N preload (rule:default_preload): bearing pressure 30.70 MPa on 31.6 mm2 (allowed 16.67), punch-through shear 16.66 MPa on 58.2 mm2 (the face outline over 2.10 mm of floor; allowed 8.33) at shift [0.0, 0.0]; conflict: the nut_frame seat carries 2.00 x what the printed material allows under the 970 N preload (rule:default_preload), and no buildable retention option changes the seat: a requirement question (a stated lower preload, a stronger material, a washer or a nut plate the catalogue does not hold)
      ok  clamp_seat_1 [clamp_seat] fastener seat: worst 100% of the nominal bearing (31.6 of 31.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      NO  fastener_bearing_1 [fastener_bearing] nut_frame seat under a 970 N preload (rule:default_preload): bearing pressure 30.70 MPa on 31.6 mm2 (allowed 16.67), punch-through shear 16.66 MPa on 58.2 mm2 (the face outline over 2.10 mm of floor; allowed 8.33) at shift [0.0, 0.0]; conflict: the nut_frame seat carries 2.00 x what the printed material allows under the 970 N preload (rule:default_preload), and no buildable retention option changes the seat: a requirement question (a stated lower preload, a stronger material, a washer or a nut plate the catalogue does not hold)
      ok  clamp_frame [clamp_frame] nut frame on the pocket floor: worst 533% of the nominal bearing (337.5 of 63.3 mm2) at shift [0.0, -2.5], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_face [clamp_face] bolted face on the plate: worst 1282% of the nominal bearing (845.8 of 66.0 mm2) at shift [0.0, -2.5], axis inside the bearing (need >= 30%, axis inside)
PASS     +1.000  L1.3: At every cleat position in that range the M5 hardware shall fit: each bolt head shall seat on the cleat and be reachable with a 4 mm hex key from the pedal side with the adapter off the pedal, each bolt shall engage its nut for its whole thickness, and no bolt tip shall reach the top face of the platform.
      ok  bolt_engagement_0 [bolt_engagement] design check: tip z 10.000 vs nut top 8.900 (bolt_m5_iso4762 12 mm)
      ok  bolt_tip_0 [bolt_tip] design check: top face z 11.000 vs tip 10.000
      ok  bolt_engagement_1 [bolt_engagement] design check: tip z 10.000 vs nut top 8.900 (bolt_m5_iso4762 12 mm)
      ok  bolt_tip_1 [bolt_tip] design check: top face z 11.000 vs tip 10.000
      ok  form_evidence [form_evidence] the design is a plate; request names it
PASS     +0.010  L1.4: The adapter shall let the cleat clip into the SPD pedal: with the adapter on the pedal in the engaged pose, nothing but the cleat shall enter the pedal's binding space or the cleat's recess space, at every cleat position in the adjustment range.
      ok  clear_recess [clear_of] min gap to keepout_recess 0.0000 mm (need >= 0)
      ok  clear_mech_1 [clear_of] min gap to engaged 0.0000 mm (need >= 0)
      ok  clear_mech_1_binding_cage [clear_of] min gap to keepout_mech_1_binding_cage 0.0000 mm (need >= 0)
PASS     +2427.010  L1.5: The adapter's pedal-side face shall sit on the pedal's sole plane like a shoe sole: no adapter material below that plane outside the cleat, and a flat bearing area of at least 600 mm2 on it.
      ok  bearing_area [bearing_area] underside area on the engaged part 3027.0 mm2
PASS     +0.199  L1.6: The adapter shall clear the crank arm: with the cleat at any position in its sideways range, and the adapter twisted about the cleat axis through the release angle either way, every point of the adapter shall stay at least 2.0 mm from the crank arm's inner face.
      ok  clear_mech_1_crank_side [clear_of] min gap to keepout_mech_1_crank_side 0.1887 mm (need >= 0)
PASS     +0.010  L1.7: The platform shall be sized like a commercial flat pedal: each plan dimension between 80 and 105 mm, with a thickness above the pedal-side face of 8 to 14 mm, not counting the grip features.
      ok  plate_size_x [plate_size] plan length 80.100 mm
      ok  plate_size_y [plate_size] plan length 80.100 mm
      ok  plate_thickness [plate_thickness] thickness 14.000 mm at the corners
      ok  form_evidence [form_evidence] the design is a plate; request names it
PASS     +1.000  L1.8: The top face shall carry grip features for shoes: at least 8 raised pins or ridges, each 1.5 to 5.0 mm tall, spread over at least 60 percent of the platform's plan area and kept at least 3 mm from its edge.
      ok  surface_features [surface_features] 8 studs features, spread 74.2 %
      ok  form_evidence [form_evidence] the design is a plate; request names it
FAIL     -2.515  L1.9: The adapter shall carry a standing rider: a 2500 N load on a 30 x 30 mm patch at the outer edge of the platform, with only the cleat clamp footprint as support, shall give a bending stress at most 1/1.5 of the printed material's 25 MPa in-plane strength.
      ok  printable_nut_frame [printable] contact_face_down: longest bridge 0.00 mm (max 15), steep overhang area 0.00 mm2
      NO  fastener_bearing_0 [fastener_bearing] nut_frame seat under a 970 N preload (rule:default_preload): bearing pressure 30.70 MPa on 31.6 mm2 (allowed 16.67), punch-through shear 16.66 MPa on 58.2 mm2 (the face outline over 2.10 mm of floor; allowed 8.33) at shift [0.0, 0.0]; conflict: the nut_frame seat carries 2.00 x what the printed material allows under the 970 N preload (rule:default_preload), and no buildable retention option changes the seat: a requirement question (a stated lower preload, a stronger material, a washer or a nut plate the catalogue does not hold)
      NO  fastener_bearing_1 [fastener_bearing] nut_frame seat under a 970 N preload (rule:default_preload): bearing pressure 30.70 MPa on 31.6 mm2 (allowed 16.67), punch-through shear 16.66 MPa on 58.2 mm2 (the face outline over 2.10 mm of floor; allowed 8.33) at shift [0.0, 0.0]; conflict: the nut_frame seat carries 2.00 x what the printed material allows under the 970 N preload (rule:default_preload), and no buildable retention option changes the seat: a requirement question (a stated lower preload, a stronger material, a washer or a nut plate the catalogue does not hold)
      NO  load_stress [load_stress] worst bending stress 58.59 MPa at edge +x, patch centre at -23.8 mm along it (arm 17.10 mm, section width 47.1 mm, part shifted [-10.0, 0.0]) vs 16.67 MPa; section loss at that section: the uncut plate would carry 27.79 MPa, the cuts add (MPa): recess +11.2, nut_pocket +10.5, bolt_slot +3.6; conflict: the load case needs a bending stress of at most 16.67 MPa, but at the largest allowed thickness (14 mm, thickness_max) the worst case over the patch positions and the adjustment range is 58.59 MPa at edge +x, patch centre at -23.8 mm along it; section loss at that section: the uncut plate would carry 27.79 MPa, the cuts add (MPa): recess +11.2, nut_pocket +10.5, bolt_slot +3.6: a requirement question (a thicker plate, a stronger material, a smaller load or patch, a larger support, or a fastener retention or recess that removes less of that section)
      ok  printable [printable] top_face_down: longest bridge 9.15 mm (max 15), steep overhang area 0.00 mm2
      ok  form_evidence [form_evidence] the design is a plate; request names it
PASS     +1.000  L1.10: One printed part shall serve both pedals: the part and its mirror image shall both pass every check above (or the design shall declare a left/right pair of two mirror-image parts, each passing every check on its own pedal).
      ok  handedness_plate [handedness] mirror image does not clear keepout_mech_1_crank_side (penetrates it by 298.8 mm3); a mirror pair is declared (the left part is the exact mirror image)
PASS     +0.390  L1.11: Each printed body shall be one manifold body that prints in PETG on an FDM printer without supports in its declared orientation, with no feature thinner than 0.8 mm, and fit a 200 x 200 x 200 mm bed.
      ok  separable [separable] shells {'plate': 1, 'nut_frame': 1}, worst overlap 0 mm3 (max 1)
      ok  printable_nut_frame [printable] contact_face_down: longest bridge 0.00 mm (max 15), steep overhang area 0.00 mm2
      ok  thin_feature_plate [thin_feature] no feature thinner than 0.8 mm (84 sections)
      ok  thin_feature_nut_frame [thin_feature] no feature thinner than 0.8 mm (27 sections)
      ok  printable [printable] top_face_down: longest bridge 9.15 mm (max 15), steep overhang area 0.00 mm2
      ok  bbox [bbox_within] outside 80.10 x 80.10 x 14.00 mm, max 200 x 200 x 200
UNLINKED         L1.12: The design shall be delivered as the STL of each printed body, the OpenSCAD source, the declared layout and the agent's own clearance and strength report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.260  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  clear_fasteners [clear_of] min gap to fasteners 0.2500 mm (need >= 0)
      ok  stud_engagement_0 [stud_engagement] thread engagement in printed material 6.68 mm (need 6)
      ok  stud_engagement_1 [stud_engagement] thread engagement in printed material 6.68 mm (need 6)
      ok  stud_engagement_2 [stud_engagement] thread engagement in printed material 6.68 mm (need 6)
      ok  stud_engagement_3 [stud_engagement] thread engagement in printed material 6.68 mm (need 6)
      ok  stud_engagement_4 [stud_engagement] thread engagement in printed material 6.68 mm (need 6)
      ok  stud_engagement_5 [stud_engagement] thread engagement in printed material 6.68 mm (need 6)
      ok  stud_engagement_6 [stud_engagement] thread engagement in printed material 6.68 mm (need 6)
      ok  stud_engagement_7 [stud_engagement] thread engagement in printed material 6.68 mm (need 6)
```

- PASS separable: shells {'plate': 1, 'nut_frame': 1}, worst overlap 0 mm3 (max 1)
- PASS clear_primary: min gap to primary 0.0000 mm (need >= 0)
- PASS clear_fasteners: min gap to fasteners 0.2500 mm (need >= 0)
- PASS clear_recess: min gap to keepout_recess 0.0000 mm (need >= 0)
- PASS clear_mech_1: min gap to engaged 0.0000 mm (need >= 0)
- PASS clear_mech_1_binding_cage: min gap to keepout_mech_1_binding_cage 0.0000 mm (need >= 0)
- PASS clear_mech_1_crank_side: min gap to keepout_mech_1_crank_side 0.1887 mm (need >= 0)
- PASS handedness_plate: mirror image does not clear keepout_mech_1_crank_side (penetrates it by 298.8 mm3); a mirror pair is declared (the left part is the exact mirror image)
- PASS travel_x: min gap to travel_0 0.0000 mm (need >= 0)
- PASS travel_y: min gap to travel_1 0.0000 mm (need >= 0)
- PASS bolt_engagement_0: design check: tip z 10.000 vs nut top 8.900 (bolt_m5_iso4762 12 mm)
- PASS bolt_tip_0: design check: top face z 11.000 vs tip 10.000
- PASS nut_trap_0: channel width 8.400 mm across the slide at the nut axis: 0.200 per flat side (band 0.1-0.4), corners 8.79
- PASS bolt_engagement_1: design check: tip z 10.000 vs nut top 8.900 (bolt_m5_iso4762 12 mm)
- PASS bolt_tip_1: design check: top face z 11.000 vs tip 10.000
- PASS nut_trap_1: channel width 8.400 mm across the slide at the nut axis: 0.200 per flat side (band 0.1-0.4), corners 8.79
- PASS nut_frame_turn: design check: frame diagonal 37.48 mm vs pocket width 27.00 mm
- PASS printable_nut_frame: contact_face_down: longest bridge 0.00 mm (max 15), steep overhang area 0.00 mm2
- PASS clamp_seat_0: fastener seat: worst 100% of the nominal bearing (31.6 of 31.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
- FAIL fastener_bearing_0: nut_frame seat under a 970 N preload (rule:default_preload): bearing pressure 30.70 MPa on 31.6 mm2 (allowed 16.67), punch-through shear 16.66 MPa on 58.2 mm2 (the face outline over 2.10 mm of floor; allowed 8.33) at shift [0.0, 0.0]; conflict: the nut_frame seat carries 2.00 x what the printed material allows under the 970 N preload (rule:default_preload), and no buildable retention option changes the seat: a requirement question (a stated lower preload, a stronger material, a washer or a nut plate the catalogue does not hold)
- PASS clamp_seat_1: fastener seat: worst 100% of the nominal bearing (31.6 of 31.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
- FAIL fastener_bearing_1: nut_frame seat under a 970 N preload (rule:default_preload): bearing pressure 30.70 MPa on 31.6 mm2 (allowed 16.67), punch-through shear 16.66 MPa on 58.2 mm2 (the face outline over 2.10 mm of floor; allowed 8.33) at shift [0.0, 0.0]; conflict: the nut_frame seat carries 2.00 x what the printed material allows under the 970 N preload (rule:default_preload), and no buildable retention option changes the seat: a requirement question (a stated lower preload, a stronger material, a washer or a nut plate the catalogue does not hold)
- PASS clamp_frame: nut frame on the pocket floor: worst 533% of the nominal bearing (337.5 of 63.3 mm2) at shift [0.0, -2.5], axis inside the bearing (need >= 30%, axis inside)
- PASS clamp_face: bolted face on the plate: worst 1282% of the nominal bearing (845.8 of 66.0 mm2) at shift [0.0, -2.5], axis inside the bearing (need >= 30%, axis inside)
- PASS thin_feature_plate: no feature thinner than 0.8 mm (84 sections)
- PASS thin_feature_nut_frame: no feature thinner than 0.8 mm (27 sections)
- PASS stud_engagement_0: thread engagement in printed material 6.68 mm (need 6)
- PASS stud_engagement_1: thread engagement in printed material 6.68 mm (need 6)
- PASS stud_engagement_2: thread engagement in printed material 6.68 mm (need 6)
- PASS stud_engagement_3: thread engagement in printed material 6.68 mm (need 6)
- PASS stud_engagement_4: thread engagement in printed material 6.68 mm (need 6)
- PASS stud_engagement_5: thread engagement in printed material 6.68 mm (need 6)
- PASS stud_engagement_6: thread engagement in printed material 6.68 mm (need 6)
- PASS stud_engagement_7: thread engagement in printed material 6.68 mm (need 6)
- PASS plate_size_x: plan length 80.100 mm
- PASS plate_size_y: plan length 80.100 mm
- PASS plate_thickness: thickness 14.000 mm at the corners
- PASS bearing_area: underside area on the engaged part 3027.0 mm2
- FAIL load_stress: worst bending stress 58.59 MPa at edge +x, patch centre at -23.8 mm along it (arm 17.10 mm, section width 47.1 mm, part shifted [-10.0, 0.0]) vs 16.67 MPa; section loss at that section: the uncut plate would carry 27.79 MPa, the cuts add (MPa): recess +11.2, nut_pocket +10.5, bolt_slot +3.6; conflict: the load case needs a bending stress of at most 16.67 MPa, but at the largest allowed thickness (14 mm, thickness_max) the worst case over the patch positions and the adjustment range is 58.59 MPa at edge +x, patch centre at -23.8 mm along it; section loss at that section: the uncut plate would carry 27.79 MPa, the cuts add (MPa): recess +11.2, nut_pocket +10.5, bolt_slot +3.6: a requirement question (a thicker plate, a stronger material, a smaller load or patch, a larger support, or a fastener retention or recess that removes less of that section)
- PASS printable: top_face_down: longest bridge 9.15 mm (max 15), steep overhang area 0.00 mm2
- PASS surface_features: 8 studs features, spread 74.2 %
- PASS bbox: outside 80.10 x 80.10 x 14.00 mm, max 200 x 200 x 200
- PASS form_evidence: the design is a plate; request names it
