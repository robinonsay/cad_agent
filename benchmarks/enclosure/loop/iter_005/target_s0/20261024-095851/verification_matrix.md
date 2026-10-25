# Verification matrix (delivered STLs)

```
FAIL   n/a   L1.1: The design shall place the Pico 2 and the two 3.5 mm jacks on the 70 x 50 mm board, from the parts catalogue, with the Pico's USB port facing one short (50 mm) end and both jacks facing the other short end, without the parts colliding or covering the corner holes, and shall declare that layout.  (no check covers this requirement)
FAIL   n/a   L1.2: The 70 x 50 x 1.6 mm board shall fit inside the closed enclosure with at least 0.5 mm clearance to every printed surface, apart from where it rests on its supports.  (no check covers this requirement)
FAIL   n/a   L1.3: The board shall rest on exactly four standoffs, one under each corner hole, each with a pilot hole for a screw through the board.  (no check covers this requirement)
FAIL   n/a   L1.4: With the lid closed, no part of the enclosure shall come within 12 mm above the board's top surface or 4 mm below its underside, except the standoffs under the holes, and the Pico and jacks shall lie inside the enclosure.  (no check covers this requirement)
FAIL   n/a   L1.5: With the lid closed, a micro-USB cable shall plug fully into the Pico through one opening in its end wall without touching the enclosure, and that opening shall be no more than 1.5 mm bigger than the plug on any side.  (no check covers this requirement)
FAIL   n/a   L1.6: With the lid closed, two 3.5 mm plugs shall plug fully into the two jacks at the same time through two openings in the opposite end wall without touching the enclosure, and each opening shall be no more than 1.5 mm bigger than the plug on any side.  (no check covers this requirement)
FAIL   n/a   L1.7: The enclosure shall be a base and a separate removable lid that locates on the base with a sliding fit and is held closed.  (no check covers this requirement)
FAIL   n/a   L1.8: The closed enclosure shall have no openings other than the USB opening, the two jack openings and screw holes, and its walls, floor and lid shall be 2 to 4 mm thick.  (no check covers this requirement)
FAIL   n/a   L1.9: The base and the lid shall each be one manifold body that prints on an FDM printer without supports.  (no check covers this requirement)
FAIL   n/a   L1.10: The closed enclosure shall be no larger than 90 x 70 x 35 mm, longest along the board's 70 mm side, and shall stand flat on a desk without tipping.  (no check covers this requirement)
FAIL   n/a   L1.11: With the lid off, the populated board shall drop straight down onto its standoffs and every board screw shall be reachable with a screwdriver.  (no check covers this requirement)
FAIL   n/a   L1.12: The design shall be delivered as a base STL, a lid STL, the OpenSCAD source, the declared board layout and the agent's own clearance report, and that report shall agree with an independent measurement.  (no check covers this requirement)
FAIL -2.000  rules: rule-derived checks (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap -4.723e-14 mm3 (max 1)
      ok  inside_references [inside] references: 0.8532 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.8532 mm (need >= 0.5)
      ok  clear_module_1_1_envelope [clear_of] min gap to module_1_1_envelope 0.6000 mm (need >= 0.2)
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.1000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.1000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.0958 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0958 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.0958 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.0958 mm (need >= 0)
      ok  clear_driver_0 [clear_of] min gap to driver_0 0.5964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 0.5964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 0.5964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 0.5964 mm (need >= 0)
      ok  clear_module_1_1_plug [clear_of] min gap to module_1_1_plug 0.4000 mm (need >= 0.3)
      ok  clear_connector_1_1_plug [clear_of] min gap to connector_1_1_plug 0.4000 mm (need >= 0.3)
      ok  clear_connector_1_2_plug [clear_of] min gap to connector_1_2_plug 0.4000 mm (need >= 0.3)
      ok  apertures_-X [aperture_count] wall -X: 1 opening(s), expected 1
      ok  oversize_module_1_1_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  apertures_+X [aperture_count] wall +X: 2 opening(s), expected 2
      ok  oversize_connector_1_1_cut [aperture_oversize] opening 8.811 x 8.811 vs plug 8.000 x 8.000: 0.405 mm per side (max 1.5)
      ok  oversize_connector_1_2_cut [aperture_oversize] opening 8.811 x 8.811 vs plug 8.000 x 8.000: 0.405 mm per side (max 1.5)
      ok  apertures_-Y [aperture_count] wall -Y: 0 opening(s), expected 0
      ok  apertures_+Y [aperture_count] wall +Y: 0 opening(s), expected 0
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  bbox [bbox_within] outside 82.95 x 62.15 x 24.60 mm, max 90 x 70 x 35 with X longest
      ok  below_split_module_1_1_cut [port_below_split] module_1_1_cut top 8.800 + ligament 1.5 vs split 14.100
      ok  below_split_connector_1_1_cut [port_below_split] connector_1_1_cut top 6.900 + ligament 1.5 vs split 14.100
      ok  below_split_connector_1_2_cut [port_below_split] connector_1_2_cut top 6.900 + ligament 1.5 vs split 14.100
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 5 vs standoff 4.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 5 vs standoff 4.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 5 vs standoff 4.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 5 vs standoff 4.100 + floor 2.400 - 0.8
      NO  grid_conformance [grid_conformance] worst pin-to-grid residual 1.1300 mm (max 0.15); no pin data: connector_1_1, connector_1_2; conflict: fixing it moves module_1_1.USB_MOUTH off its flush edge position by 1.130 mm (rule flush_to_edge, ARCHITECTURE.md 7.5)
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap -4.723e-14 mm3 (max 1)
- PASS inside_references: references: 0.8532 mm from the enclosure (need >= 0.5)
- PASS clear_board: min gap to board 0.8532 mm (need >= 0.5)
- PASS clear_module_1_1_envelope: min gap to module_1_1_envelope 0.6000 mm (need >= 0.2)
- PASS clear_keepout_top: min gap to board_ko_top 0.1000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.1000 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.0958 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.0958 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.0958 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.0958 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 0.5964 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 0.5964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 0.5964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 0.5964 mm (need >= 0)
- PASS clear_module_1_1_plug: min gap to module_1_1_plug 0.4000 mm (need >= 0.3)
- PASS clear_connector_1_1_plug: min gap to connector_1_1_plug 0.4000 mm (need >= 0.3)
- PASS clear_connector_1_2_plug: min gap to connector_1_2_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 1 opening(s), expected 1
- PASS oversize_module_1_1_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 2 opening(s), expected 2
- PASS oversize_connector_1_1_cut: opening 8.811 x 8.811 vs plug 8.000 x 8.000: 0.405 mm per side (max 1.5)
- PASS oversize_connector_1_2_cut: opening 8.811 x 8.811 vs plug 8.000 x 8.000: 0.405 mm per side (max 1.5)
- PASS apertures_-Y: wall -Y: 0 opening(s), expected 0
- PASS apertures_+Y: wall +Y: 0 opening(s), expected 0
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 82.95 x 62.15 x 24.60 mm, max 90 x 70 x 35 with X longest
- PASS below_split_module_1_1_cut: module_1_1_cut top 8.800 + ligament 1.5 vs split 14.100
- PASS below_split_connector_1_1_cut: connector_1_1_cut top 6.900 + ligament 1.5 vs split 14.100
- PASS below_split_connector_1_2_cut: connector_1_2_cut top 6.900 + ligament 1.5 vs split 14.100
- PASS pilot_depth_standoff_1: pilot depth 5 vs standoff 4.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 5 vs standoff 4.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 5 vs standoff 4.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 5 vs standoff 4.100 + floor 2.400 - 0.8
- FAIL grid_conformance: worst pin-to-grid residual 1.1300 mm (max 0.15); no pin data: connector_1_1, connector_1_2; conflict: fixing it moves module_1_1.USB_MOUTH off its flush edge position by 1.130 mm (rule flush_to_edge, ARCHITECTURE.md 7.5)
