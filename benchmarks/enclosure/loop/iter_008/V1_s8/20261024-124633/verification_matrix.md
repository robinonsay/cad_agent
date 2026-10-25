# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
FAIL     -1.194  L1.1: The design shall place the Pico 2 and one 3.5 mm jack on the 80 x 60 mm board, from the parts catalogue, with the Pico's USB port and the jack both facing the same short (60 mm) end, without the parts colliding or covering the corner holes, and shall declare that layout.
      ok  inside_contents [inside] contents: 1.2076 mm from the enclosure (need >= 0.2)
      ok  clear_module_1_1_envelope [inside] module_1_1_envelope: 5.2000 mm from the enclosure (need >= 0.2)
      NO  grid_conformance [grid_conformance] worst pin-to-grid residual 1.3542 mm (max 0.15); conflict: connector_1_1: the part's own pin pattern cannot meet the board grid at any position (best 0.540 mm > 0.15); a catalogue or requirement question
PASS     +0.610  L1.2: The 80 x 60 x 1.6 mm board shall fit inside the closed enclosure with at least 0.5 mm clearance to every printed surface, apart from where it rests on its supports.
      ok  inside_board [inside] board: 1.1000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 1.1000 mm (need >= 0.5)
UNLINKED         L1.3: The board shall rest on exactly four standoffs, one under each corner hole, each with a pilot hole for a screw through the board.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.106  L1.4: With the lid closed, no part of the enclosure shall come within 12 mm above the board's top surface or 4 mm below its underside, except the standoffs under the holes, and the Pico and the jack shall lie inside the enclosure.
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.1000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.1000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.0958 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0958 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.0958 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.0958 mm (need >= 0)
FAIL     -1.000  L1.5: With the lid closed, a micro-USB cable and a 3.5 mm plug shall both plug fully, at the same time, through two separate openings in the same end wall without touching the enclosure or each other, and each opening shall be no more than 1.5 mm bigger than its plug on any side.
      ok  clear_connector_1_1_plug [clear_of] min gap to connector_1_1_plug 0.4000 mm (need >= 0.3)
      ok  oversize_connector_1_1_cut [aperture_oversize] opening 8.811 x 8.811 vs plug 8.000 x 8.000: 0.405 mm per side (max 1.5)
      NO  text_coverage [coverage] 1 named plug connection(s) covered; uncovered: module_1.usb takes plug_microusb_b named by L1.5
UNLINKED         L1.6: The enclosure shall be a base and a separate removable lid that locates on the base with a sliding fit and is held closed.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.7: The closed enclosure shall have no openings other than the two port openings and screw holes, and its walls, floor and lid shall be 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.8: The base and the lid shall each be one manifold body that prints on an FDM printer without supports.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +7.690  L1.9: The closed enclosure shall be no larger than 100 x 80 x 35 mm, longest along the board's 80 mm side, and shall stand flat on a desk without tipping.
      ok  bbox [bbox_within] outside 92.32 x 72.32 x 24.70 mm, max 100 x 80 x 35 with X longest
UNLINKED         L1.10: With the lid off, the populated board shall drop straight down onto its standoffs and every board screw shall be reachable with a screwdriver.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.11: The design shall be delivered as a base STL, a lid STL, the OpenSCAD source, the declared board layout and the agent's own clearance report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap -1.645e-15 mm3 (max 1)
      ok  clear_driver_0 [clear_of] min gap to driver_0 0.5964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 0.5964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 0.5964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 0.5964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_connector_1_1_cut [port_below_split] connector_1_1_cut top 6.900 + ligament 1.5 vs split 14.200
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
      ok  pilot_engagement_standoff_1 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_1 [boss_od] outside diameter 5.300 vs min_boss_od 5
      ok  pilot_engagement_standoff_2 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_2 [boss_od] outside diameter 5.300 vs min_boss_od 5
      ok  pilot_engagement_standoff_3 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_3 [boss_od] outside diameter 5.300 vs min_boss_od 5
      ok  pilot_engagement_standoff_4 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_4 [boss_od] outside diameter 5.300 vs min_boss_od 5
      ok  pilot_engagement_boss_1 [pilot_engagement] pilot depth 6.100 vs min_engagement 6
      ok  boss_od_boss_1 [boss_od] outside diameter 6.100 vs min_boss_od 6
      ok  pilot_engagement_boss_2 [pilot_engagement] pilot depth 6.100 vs min_engagement 6
      ok  boss_od_boss_2 [boss_od] outside diameter 6.100 vs min_boss_od 6
      ok  pilot_engagement_boss_3 [pilot_engagement] pilot depth 6.100 vs min_engagement 6
      ok  boss_od_boss_3 [boss_od] outside diameter 6.100 vs min_boss_od 6
      ok  pilot_engagement_boss_4 [pilot_engagement] pilot depth 6.100 vs min_engagement 6
      ok  boss_od_boss_4 [boss_od] outside diameter 6.100 vs min_boss_od 6
      ok  lip_engagement [lip_engagement] lip engagement 2.100 vs 2
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap -1.645e-15 mm3 (max 1)
- PASS inside_board: board: 1.1000 mm from the enclosure (need >= 0.5)
- PASS inside_contents: contents: 1.2076 mm from the enclosure (need >= 0.2)
- PASS clear_board: min gap to board 1.1000 mm (need >= 0.5)
- PASS clear_module_1_1_envelope: module_1_1_envelope: 5.2000 mm from the enclosure (need >= 0.2)
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
- PASS clear_connector_1_1_plug: min gap to connector_1_1_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS oversize_connector_1_1_cut: opening 8.811 x 8.811 vs plug 8.000 x 8.000: 0.405 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 92.32 x 72.32 x 24.70 mm, max 100 x 80 x 35 with X longest
- PASS below_split_connector_1_1_cut: connector_1_1_cut top 6.900 + ligament 1.5 vs split 14.200
- PASS pilot_depth_standoff_1: pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
- PASS pilot_engagement_standoff_1: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_1: outside diameter 5.300 vs min_boss_od 5
- PASS pilot_engagement_standoff_2: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_2: outside diameter 5.300 vs min_boss_od 5
- PASS pilot_engagement_standoff_3: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_3: outside diameter 5.300 vs min_boss_od 5
- PASS pilot_engagement_standoff_4: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_4: outside diameter 5.300 vs min_boss_od 5
- PASS pilot_engagement_boss_1: pilot depth 6.100 vs min_engagement 6
- PASS boss_od_boss_1: outside diameter 6.100 vs min_boss_od 6
- PASS pilot_engagement_boss_2: pilot depth 6.100 vs min_engagement 6
- PASS boss_od_boss_2: outside diameter 6.100 vs min_boss_od 6
- PASS pilot_engagement_boss_3: pilot depth 6.100 vs min_engagement 6
- PASS boss_od_boss_3: outside diameter 6.100 vs min_boss_od 6
- PASS pilot_engagement_boss_4: pilot depth 6.100 vs min_engagement 6
- PASS boss_od_boss_4: outside diameter 6.100 vs min_boss_od 6
- PASS lip_engagement: lip engagement 2.100 vs 2
- FAIL grid_conformance: worst pin-to-grid residual 1.3542 mm (max 0.15); conflict: connector_1_1: the part's own pin pattern cannot meet the board grid at any position (best 0.540 mm > 0.15); a catalogue or requirement question
- FAIL text_coverage: 1 named plug connection(s) covered; uncovered: module_1.usb takes plug_microusb_b named by L1.5
