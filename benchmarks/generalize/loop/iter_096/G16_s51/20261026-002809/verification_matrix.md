# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
FAIL     -1.000  L1.1: The design shall place the NEMA 17 motor, the 2020 extrusion, two M5 T-nuts, two M5 bolts and four M3 screws from the parts catalogue as one assembly, with the plate on the extrusion's slot face, the motor beside the extrusion and its shaft perpendicular to the plate and to the extrusion's axis, without the parts colliding, and shall declare that layout.
      NO  content_placed_mech_1 [content_placed] mech_1 (tnut_2020_m5) is not placed: nema17_motor is not a carrier: no relation places it yet (GM2b)
      NO  content_placed_profile_1 [content_placed] profile_1 (extrusion_2020) is not placed: extrusion_2020: no number in the text for length; the plant cannot build a part whose size the text does not state
      ok  clear_primary [clear_of] min gap to primary 0.0000 mm (need >= 0)
      ok  clear_fasteners [clear_of] min gap to fasteners 0.0000 mm (need >= 0)
      ok  bolt_engagement_0 [bolt_engagement] design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
      ok  bolt_bottoming_0 [bolt_engagement] design check: engagement 4.40 mm vs thread depth 4.5 mm
      ok  bolt_engagement_1 [bolt_engagement] design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
      ok  bolt_bottoming_1 [bolt_engagement] design check: engagement 4.40 mm vs thread depth 4.5 mm
      ok  bolt_engagement_2 [bolt_engagement] design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
      ok  bolt_bottoming_2 [bolt_engagement] design check: engagement 4.40 mm vs thread depth 4.5 mm
      ok  bolt_engagement_3 [bolt_engagement] design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
      ok  bolt_bottoming_3 [bolt_engagement] design check: engagement 4.40 mm vs thread depth 4.5 mm
      ok  clamp_seat_0 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_seat_1 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_seat_2 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_seat_3 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
PASS     +0.010  L1.2: The plate shall mount the NEMA 17 on its 31 mm bolt pattern with four M3 screws and a bore that takes the 22 mm pilot, coaxial with the pattern.
      ok  clear_fasteners [clear_of] min gap to fasteners 0.0000 mm (need >= 0)
      ok  bolt_engagement_0 [bolt_engagement] design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
      ok  bolt_bottoming_0 [bolt_engagement] design check: engagement 4.40 mm vs thread depth 4.5 mm
      ok  bolt_engagement_1 [bolt_engagement] design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
      ok  bolt_bottoming_1 [bolt_engagement] design check: engagement 4.40 mm vs thread depth 4.5 mm
      ok  bolt_engagement_2 [bolt_engagement] design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
      ok  bolt_bottoming_2 [bolt_engagement] design check: engagement 4.40 mm vs thread depth 4.5 mm
      ok  bolt_engagement_3 [bolt_engagement] design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
      ok  bolt_bottoming_3 [bolt_engagement] design check: engagement 4.40 mm vs thread depth 4.5 mm
      ok  clamp_seat_0 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_seat_1 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_seat_2 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_seat_3 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
FAIL     -1.000  L1.3: The plate shall be bolted to the extrusion by exactly two M5 bolts into drop-in T-nuts in the T-slot under the plate, through two slotted holes that give 6 mm of travel across the extrusion; the bolts shall be 20 to 40 mm apart along the extrusion, and each shall engage at least 3 mm of its T-nut without reaching the slot floor.
      NO  content_placed_mech_1 [content_placed] mech_1 (tnut_2020_m5) is not placed: nema17_motor is not a carrier: no relation places it yet (GM2b)
      ok  clamp_seat_0 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_seat_1 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_seat_2 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
      ok  clamp_seat_3 [clamp_seat] fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
PASS     +1198.952  L1.4: Sliding the plate through its 6 mm of travel shall keep each bolt inside its slot, each bolt head on the plate, and the motor clear of the extrusion (3.5 to 10 mm from its edge at the nominal position, at least 0.5 mm at the end of the travel toward it), with at least 19 mm² of plate under each bolt head at every position.
      ok  bearing_area [bearing_area] underside area 1217.9 mm2
UNLINKED         L1.5: The plate shall be one flat plate 5 mm thick resting on the extrusion's face without entering the extrusion or touching the motor anywhere except the motor's mounting face.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.6: The plate shall carry the motor and the belt pull to the two bolts through material at least 3 mm wide around every hole and edge, with no cross-section narrower than 20 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.7: The motor shaft shall stay clear above the plate for a pulley and belt (a 20 mm diameter zone from the plate top to 30 mm above it), and every bolt and screw head shall be reachable with a hex key from above.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.8: The plate shall be one manifold body that prints flat on its face on an FDM printer without supports.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +19.406  L1.9: The plate shall be no larger than 60 x 75 mm.
      ok  bbox [bbox_within] outside 40.60 x 40.60 x 3.60 mm, max 60 x 75 x 200
UNLINKED         L1.10: The design shall be delivered as the plate STL, the OpenSCAD source, the declared layout and the agent's own clearance report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.390  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'plate': 1}, worst overlap 0 mm3 (max 1)
      ok  thin_feature_plate [thin_feature] no feature thinner than 0.8 mm (41 sections)
      ok  plate_thickness [plate_thickness] thickness 3.600 mm at the corners
      ok  printable [printable] contact_face_down: longest bridge 0.00 mm (max 15), steep overhang area 0.00 mm2
```

- PASS separable: shells {'plate': 1}, worst overlap 0 mm3 (max 1)
- FAIL content_placed_mech_1: mech_1 (tnut_2020_m5) is not placed: nema17_motor is not a carrier: no relation places it yet (GM2b)
- FAIL content_placed_profile_1: profile_1 (extrusion_2020) is not placed: extrusion_2020: no number in the text for length; the plant cannot build a part whose size the text does not state
- PASS clear_primary: min gap to primary 0.0000 mm (need >= 0)
- PASS clear_fasteners: min gap to fasteners 0.0000 mm (need >= 0)
- PASS bolt_engagement_0: design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
- PASS bolt_bottoming_0: design check: engagement 4.40 mm vs thread depth 4.5 mm
- PASS bolt_engagement_1: design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
- PASS bolt_bottoming_1: design check: engagement 4.40 mm vs thread depth 4.5 mm
- PASS bolt_engagement_2: design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
- PASS bolt_bottoming_2: design check: engagement 4.40 mm vs thread depth 4.5 mm
- PASS bolt_engagement_3: design check: engagement 4.40 mm (bolt_m3_iso4762 8 mm through 3.60 mm of plate)
- PASS bolt_bottoming_3: design check: engagement 4.40 mm vs thread depth 4.5 mm
- PASS clamp_seat_0: fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
- PASS clamp_seat_1: fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
- PASS clamp_seat_2: fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
- PASS clamp_seat_3: fastener seat: worst 100% of the nominal bearing (14.7 of 14.7 mm2) at shift [0.0, 0.0], axis inside the bearing (need >= 30%, axis inside)
- PASS thin_feature_plate: no feature thinner than 0.8 mm (41 sections)
- PASS plate_thickness: thickness 3.600 mm at the corners
- PASS bearing_area: underside area 1217.9 mm2
- PASS printable: contact_face_down: longest bridge 0.00 mm (max 15), steep overhang area 0.00 mm2
- PASS bbox: outside 40.60 x 40.60 x 3.60 mm, max 60 x 75 x 200
