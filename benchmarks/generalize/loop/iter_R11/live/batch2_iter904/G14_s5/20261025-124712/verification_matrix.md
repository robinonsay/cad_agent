# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
FAIL     -1.000  L1.1: From the parts catalogue, the design positions the Nano with its mini-USB port towards the open short end and the 12 mm buzzer alongside the far end of the Nano, no closer than 2.0 mm to it. The parts must not collide, and the layout must be declared.
      ok  inside_board [inside] board: 0.3000 mm from the enclosure (need >= 0.3)
      NO  content_placed_control_1 [content_placed] control_1 (buzzer_12mm) is not placed: arduino_nano is not a carrier: no relation places it yet (GM2b)
      ok  clear_board [clear_of] min gap to board 0.3000 mm (need >= 0.3)
      ok  retention_board [retention] arduino nano held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets keepout component_side; -X: the hook or arm meets keepout component_side, usb)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
PASS     +0.010  L1.2: Four standoffs, and no others, hold up the Nano, one beneath each of its mounting holes, and a pin passes through each hole to locate the board. The header pins and tails beneath the board need at least 0.3 mm of clearance from the base. Standoffs measure 3.0 to 4.0 mm across and 8.8 to 12.0 mm high, with tops level within 0.10 mm that touch the underside of the board; the pins are 1.4 to 1.6 mm in diameter and rise at least 3.0 mm over the board top, so the board can shift no more than 0.4 mm along X or Y.
      ok  inside_board [inside] board: 0.3000 mm from the enclosure (need >= 0.3)
      ok  clear_board [clear_of] min gap to board 0.3000 mm (need >= 0.3)
      ok  retention_board [retention] arduino nano held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets keepout component_side; -X: the hook or arm meets keepout component_side, usb)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
PASS     +0.010  L1.3: The closed box has to contain the Nano with at least 0.5 mm of gap to all printed surfaces other than the standoffs, and at least 1.0 mm from the highest part of the Nano up to the lid. Between the long walls the inside width should be no less than 19.0 mm.
      ok  inside_board [inside] board: 0.3000 mm from the enclosure (need >= 0.3)
      ok  clear_board [clear_of] min gap to board 0.3000 mm (need >= 0.3)
      ok  retention_board [retention] arduino nano held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets keepout component_side; -X: the hook or arm meets keepout component_side, usb)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
FAIL     -1.000  L1.4: Seat the buzzer upright, sound port toward the lid, in a printed pocket with a diameter of 12.4 mm; it rests on a ring-shaped ledge that doesn't pinch the leads. Above the ledge the pocket is 2.5 to 4.0 mm deep, the inner diameter of the ledge ring is 8.0 to 10.0 mm, and the pocket is surrounded by at least 1.6 mm of material.
      NO  content_placed_control_1 [content_placed] control_1 (buzzer_12mm) is not placed: arduino_nano is not a carrier: no relation places it yet (GM2b)
PASS     -0.000  L1.5: Leave out the end wall where the mini-USB connector is, so a mini-USB plug can be driven all the way into the Nano without contacting the box, keeping at least 0.3 mm from the plug and its overmold on all sides, both with the lid seated and as it slides. The base should reach no more than 3.3 mm past the front of the receptacle, and the end of the lid should remain at least 0.3 mm away from the face of the overmold.
      ok  inside_board [inside] board: 0.3000 mm from the enclosure (need >= 0.3)
      ok  clear_board [clear_of] min gap to board 0.3000 mm (need >= 0.3)
      ok  clear_board_plug [clear_of] min gap to board_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_cut [aperture_oversize] opening 11.800 x 8.800 vs plug 11.000 x 8.000: 0.400 mm per side (max 1.5)
      ok  retention_board [retention] arduino nano held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets keepout component_side; -X: the hook or arm meets keepout component_side, usb)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
      ok  text_coverage [coverage] 1 named plug connection(s) covered
UNLINKED         L1.6: A dovetail rail runs along the outer side of both long walls of the base, and the lid has a groove to match; flanks slope at 60 degrees from horizontal with 0.25 mm of fit clearance on each flank, which prevents the lid lifting off. Rails are at least 40.0 mm in length and 3.0 to 4.0 mm in height, and project at least 1.2 mm past the wall. Keep the flank angle within 5 degrees of 60 and the flank gap between 0.20 and 0.30 mm; any other gap between lid and base is at least 0.15 mm, and the lid skirt is at least 1.6 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -1.000  L1.7: Make the lid its own body; it slides on and off lengthwise, rubbing on nothing except the surfaces it rests on, and it comes to a stop at the far end wall. Its end face ends up no more than 0.3 mm from that wall and its underside within 0.3 mm of the wall tops. In plan it covers the Nano and buzzer with at least 1.0 mm to spare, and throughout the slide it stays at least 0.3 mm clear of the Nano, the buzzer and the plug.
      ok  inside_board [inside] board: 0.3000 mm from the enclosure (need >= 0.3)
      NO  content_placed_control_1 [content_placed] control_1 (buzzer_12mm) is not placed: arduino_nano is not a carrier: no relation places it yet (GM2b)
      ok  clear_board [clear_of] min gap to board 0.3000 mm (need >= 0.3)
      ok  retention_board [retention] arduino nano held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets keepout component_side; -X: the hook or arm meets keepout component_side, usb)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
FAIL     -1.000  L1.8: In the lid, put a ring of at least six sound holes around the point above the buzzer, and one more hole in the middle above the sound port; the lid's underside should sit 0.5 to 1.5 mm over the top of the buzzer. The middle hole has a diameter of 2.0 to 3.5 mm. The ring holes are 1.5 to 2.5 mm, evenly spaced on a 7.0 to 10.0 mm diameter circle, leave at least 1.0 mm of material between holes, and together give at least 15 mm2 of open area.
      NO  content_placed_control_1 [content_placed] control_1 (buzzer_12mm) is not placed: arduino_nano is not a carrier: no relation places it yet (GM2b)
UNLINKED         L1.9: Apart from the open USB end, the sound holes and the sliding seam of the lid, the shut box has no openings, and its walls, floor and lid are between 2.0 and 4.0 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: Both the base and the lid must be a single manifold body apiece, and print on an FDM printer without needing supports.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +8.310  L1.11: The box, closed, needs to fit inside 80 x 40 x 30 mm and rest flat on a table without tipping over.
      ok  bbox [bbox_within] outside 57.59 x 29.89 x 21.70 mm, max 80 x 40 x 30 with X longest
FAIL     -1.000  L1.12: Take the lid off and lower the Nano vertically onto its standoffs and the buzzer into its pocket; neither should touch anything, with at least 0.2 mm of clearance around the Nano and 0.1 mm around the buzzer.
      ok  inside_board [inside] board: 0.3000 mm from the enclosure (need >= 0.3)
      NO  content_placed_control_1 [content_placed] control_1 (buzzer_12mm) is not placed: arduino_nano is not a carrier: no relation places it yet (GM2b)
      ok  clear_board [clear_of] min gap to board 0.3000 mm (need >= 0.3)
      ok  retention_board [retention] arduino nano held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets keepout component_side; -X: the hook or arm meets keepout component_side, usb)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
UNLINKED         L1.13: Supply a base STL and a lid STL together with the OpenSCAD source, the layout declaration and the agent's own clearance report, which has to agree with an independent measurement to within 0.10 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 2.071e-15 mm3 (max 1)
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.0000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.0000 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_board_cut_base [ligament] 2.2500 mm of material round board_cut toward floor_top at x = -2.300 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 9.945 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5960 mm of material round boss_1_lid_hole toward outer at z = 15.000 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 9.945 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5960 mm of material round boss_2_lid_hole toward outer at z = 15.000 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 9.945 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5960 mm of material round boss_3_lid_hole toward outer at z = 15.000 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 9.945 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5960 mm of material round boss_4_lid_hole toward outer at z = 15.000 (need >= 1.5)
      ok  rib_interference_cradle_rib_xm_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_xp_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_2 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_3 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_2 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_3 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  below_split_board_cut [port_below_split] board_cut top 7.950 + ligament 1.5 vs split 13.800
      ok  bridge_board_cut [bridge] board_cut: flat roof span 11.800 vs bridge limit 15
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 7.7 vs boss height 19.300 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 7.7 vs boss height 19.300 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 7.7 vs boss height 19.300 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 7.7 vs boss height 19.300 (floor included) - 0.8
      ok  pilot_engagement_boss_1 [pilot_engagement] pilot depth 7.700 vs min_engagement 6
      ok  boss_od_boss_1 [boss_od] outside diameter 6.600 vs min_boss_od 6
      ok  pilot_bottoming_boss_1 [pilot_bottoming] pilot depth 7.700 vs screw length 10 - clamped plate 2.400
      ok  pilot_engagement_boss_2 [pilot_engagement] pilot depth 7.700 vs min_engagement 6
      ok  boss_od_boss_2 [boss_od] outside diameter 6.600 vs min_boss_od 6
      ok  pilot_bottoming_boss_2 [pilot_bottoming] pilot depth 7.700 vs screw length 10 - clamped plate 2.400
      ok  pilot_engagement_boss_3 [pilot_engagement] pilot depth 7.700 vs min_engagement 6
      ok  boss_od_boss_3 [boss_od] outside diameter 6.600 vs min_boss_od 6
      ok  pilot_bottoming_boss_3 [pilot_bottoming] pilot depth 7.700 vs screw length 10 - clamped plate 2.400
      ok  pilot_engagement_boss_4 [pilot_engagement] pilot depth 7.700 vs min_engagement 6
      ok  boss_od_boss_4 [boss_od] outside diameter 6.600 vs min_boss_od 6
      ok  pilot_bottoming_boss_4 [pilot_bottoming] pilot depth 7.700 vs screw length 10 - clamped plate 2.400
      ok  lip_engagement [lip_engagement] lip engagement 2.100 vs 2
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 2.071e-15 mm3 (max 1)
- PASS inside_board: board: 0.3000 mm from the enclosure (need >= 0.3)
- FAIL content_placed_control_1: control_1 (buzzer_12mm) is not placed: arduino_nano is not a carrier: no relation places it yet (GM2b)
- PASS clear_board: min gap to board 0.3000 mm (need >= 0.3)
- PASS clear_keepout_top: min gap to board_ko_top 0.0000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.0000 mm (need >= 0)
- PASS clear_board_plug: min gap to board_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS oversize_board_cut: opening 11.800 x 8.800 vs plug 11.000 x 8.000: 0.400 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_board_cut_base: 2.2500 mm of material round board_cut toward floor_top at x = -2.300 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 9.945 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5960 mm of material round boss_1_lid_hole toward outer at z = 15.000 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 9.945 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5960 mm of material round boss_2_lid_hole toward outer at z = 15.000 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 9.945 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5960 mm of material round boss_3_lid_hole toward outer at z = 15.000 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 9.945 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5960 mm of material round boss_4_lid_hole toward outer at z = 15.000 (need >= 1.5)
- PASS retention_board: arduino nano held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets keepout component_side; -X: the hook or arm meets keepout component_side, usb)
- PASS supported: worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
- PASS rib_interference_cradle_rib_xm_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_xp_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_ym_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_ym_2: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_ym_3: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_yp_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_yp_2: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_yp_3: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS bbox: outside 57.59 x 29.89 x 21.70 mm, max 80 x 40 x 30 with X longest
- PASS below_split_board_cut: board_cut top 7.950 + ligament 1.5 vs split 13.800
- PASS bridge_board_cut: board_cut: flat roof span 11.800 vs bridge limit 15
- PASS pilot_depth_boss_1: pilot depth 7.7 vs boss height 19.300 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 7.7 vs boss height 19.300 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 7.7 vs boss height 19.300 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 7.7 vs boss height 19.300 (floor included) - 0.8
- PASS pilot_engagement_boss_1: pilot depth 7.700 vs min_engagement 6
- PASS boss_od_boss_1: outside diameter 6.600 vs min_boss_od 6
- PASS pilot_bottoming_boss_1: pilot depth 7.700 vs screw length 10 - clamped plate 2.400
- PASS pilot_engagement_boss_2: pilot depth 7.700 vs min_engagement 6
- PASS boss_od_boss_2: outside diameter 6.600 vs min_boss_od 6
- PASS pilot_bottoming_boss_2: pilot depth 7.700 vs screw length 10 - clamped plate 2.400
- PASS pilot_engagement_boss_3: pilot depth 7.700 vs min_engagement 6
- PASS boss_od_boss_3: outside diameter 6.600 vs min_boss_od 6
- PASS pilot_bottoming_boss_3: pilot depth 7.700 vs screw length 10 - clamped plate 2.400
- PASS pilot_engagement_boss_4: pilot depth 7.700 vs min_engagement 6
- PASS boss_od_boss_4: outside diameter 6.600 vs min_boss_od 6
- PASS pilot_bottoming_boss_4: pilot depth 7.700 vs screw length 10 - clamped plate 2.400
- PASS lip_engagement: lip engagement 2.100 vs 2
- PASS pilot_band_boss_1: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_2: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_3: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_4: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS text_coverage: 1 named plug connection(s) covered
