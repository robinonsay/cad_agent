# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.010  L1.1: Using the Nano from the catalogue, orient it so the mini-USB port looks at one of the short 18 mm ends, put three 5 mm LEDs in the lid, keep the parts from colliding, and state the layout you chose.
      ok  inside_board [inside] board: 0.5000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.5000 mm (need >= 0.5)
      ok  plug_refs_board_plug [clear_of] min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
      ok  retention_board [retention] arduino nano held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: no rim piece 6 mm long; -X: the hook or arm meets keepout component_side, usb)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
      ok  panel_keepouts_control_1_1 [clear_of] min gap to control_1_1_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_1 [clear_of] min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_1 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_1 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_1 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_2 [clear_of] min gap to control_1_2_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_2 [clear_of] min gap to control_1_2_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_2 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_2 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_2 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_3 [clear_of] min gap to control_1_3_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_3 [clear_of] min gap to control_1_3_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_3 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_3 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_3 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
PASS     +0.010  L1.2: Inside the closed box the 45 x 18 x 1.6 mm board needs at least 0.5 mm of clearance from every printed surface (its posts excepted), and the USB receptacle has to be within the box.
      ok  inside_board [inside] board: 0.5000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.5000 mm (need >= 0.5)
UNLINKED         L1.3: Four posts, no more and no fewer, carry the board, each below a mounting hole and 3.0 to 4.0 mm wide (the hole's own keep-out being 4.0). A locating pin runs through each hole, 0.1 to 0.3 mm under the 1.7 mm hole size, and the header tails must not touch the floor.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.010  L1.4: When the lid is shut, keep everything at least 5.0 mm above the top of the board, and at least 0.3 mm away from the header bodies and pin tails below.
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.0000 mm (need >= 0)
PASS     -0.000  L1.5: With the lid shut, a mini-USB cable has to go all the way into the Nano via one opening in the −X end wall, leaving at least 0.3 mm spare around the plug. Between that opening and the lid seam, the floor and the corners leave 1.5 mm of wall or more. The opening may exceed the plug by 1.5 mm at most per side.
      ok  inside_board [inside] board: 0.5000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.5000 mm (need >= 0.5)
      ok  clear_board_plug [clear_of] min gap to board_plug 0.4000 mm (need >= 0.3)
      ok  plug_refs_board_plug [clear_of] min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
      ok  oversize_board_cut [aperture_oversize] opening 11.800 x 8.800 vs plug 11.000 x 8.000: 0.400 mm per side (max 1.5)
      ok  retention_board [retention] arduino nano held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: no rim piece 6 mm long; -X: the hook or arm meets keepout component_side, usb)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
      ok  text_coverage [coverage] 1 named plug connection(s) covered
PASS     +0.110  L1.6: Three 5 mm LEDs are carried by the lid: lenses stick out through holes of 5.2 to 5.4 mm in the top face with the flanges held behind, so every dome can be seen from outside and none can be pulled out forwards (flange overlap on the hole of 0.2 mm per side minimum). Put them in a line above the board, spaced 9.0 mm or more apart and 4.0 mm or more from the cavity edge.
      ok  plug_refs_board_plug [clear_of] min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
      ok  panel_keepouts_control_1_1 [clear_of] min gap to control_1_1_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_1 [clear_of] min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_1 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_1 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_1 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_2 [clear_of] min gap to control_1_2_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_2 [clear_of] min gap to control_1_2_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_2 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_2 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_2 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_3 [clear_of] min gap to control_1_3_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_3 [clear_of] min gap to control_1_3_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_3 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_3 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_3 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
UNLINKED         L1.7: Only snap hooks hold the lid, with no screws or other fasteners: two or more hooks on each long side and none on the end walls. Hooks are at least 5 mm wide and engage 0.6 to 1.0 mm, on an arm where the bending strain 1.5 t y / L^2 (t thickness, y engagement, L free length) does not exceed 0.02.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.8: Make the lid a separate body that sits on the base via a sliding lip, at least 2.0 mm deep with 0.15 to 0.35 mm of clearance each side, and closes flush without the two overlapping.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.9: Once closed, the box should have just the USB opening and three LED holes. Wall, floor and lid thickness is 2.0 to 3.0 mm, and every opening has at least 1.5 mm of material around it.
      ok  plug_refs_board_plug [clear_of] min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
      ok  panel_keepouts_control_1_1 [clear_of] min gap to control_1_1_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_1 [clear_of] min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_1 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_1 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_1 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_2 [clear_of] min gap to control_1_2_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_2 [clear_of] min gap to control_1_2_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_2 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_2 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_2 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_3 [clear_of] min gap to control_1_3_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_3 [clear_of] min gap to control_1_3_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_3 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_3 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_3 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
UNLINKED         L1.10: Base prints flat on its floor and lid on its outer face, each as a single manifold body needing no supports.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -0.164  L1.11: Excluding the LED domes, the closed box can be at most 60 x 30 x 26 mm, with its long dimension running along the board's 45 mm side, and it has to stand flat on a shelf and not tip.
      ok  plug_refs_board_plug [clear_of] min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
      NO  bbox [bbox_within] outside 57.87 x 30.17 x 17.90 mm, max 60 x 30 x 26 with X longest
      ok  panel_keepouts_control_1_1 [clear_of] min gap to control_1_1_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_1 [clear_of] min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_1 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_1 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_1 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_2 [clear_of] min gap to control_1_2_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_2 [clear_of] min gap to control_1_2_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_2 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_2 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_2 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_3 [clear_of] min gap to control_1_3_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_3 [clear_of] min gap to control_1_3_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_3 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_3 [panel_seated] lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_3 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
UNLINKED         L1.12: Hand over a base STL, a lid STL, the OpenSCAD source, the declared layout, and the agent's own clearance report, which has to agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -1.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 1.143e-15 mm3 (max 1)
      NO  content_placed_generic_1 [content_placed] generic_1 (generic_box) is not placed: generic_box: no number in the text for size_x, size_y, size_z; the plant cannot build a part whose size the text does not state
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.0000 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_board_cut_base [ligament] 2.0500 mm of material round board_cut toward outer at x = -2.500 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5960 mm of material round boss_1_lid_hole toward outer at z = 11.200 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5960 mm of material round boss_2_lid_hole toward outer at z = 11.200 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5960 mm of material round boss_3_lid_hole toward outer at z = 11.200 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5960 mm of material round boss_4_lid_hole toward outer at z = 11.200 (need >= 1.5)
      ok  rib_interference_cradle_rib_xm_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_xp_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_2 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_2 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  below_split_board_cut [port_below_split] board_cut top 7.950 + ligament 1.5 vs split 10.000
      ok  bridge_board_cut [bridge] board_cut: flat roof span 11.800 vs bridge limit 15
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 7.7 vs boss height 15.500 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 7.7 vs boss height 15.500 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 7.7 vs boss height 15.500 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 7.7 vs boss height 15.500 (floor included) - 0.8
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

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 1.143e-15 mm3 (max 1)
- PASS inside_board: board: 0.5000 mm from the enclosure (need >= 0.5)
- FAIL content_placed_generic_1: generic_1 (generic_box) is not placed: generic_box: no number in the text for size_x, size_y, size_z; the plant cannot build a part whose size the text does not state
- PASS clear_board: min gap to board 0.5000 mm (need >= 0.5)
- PASS clear_keepout_top: min gap to board_ko_top 0.0000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.0000 mm (need >= 0)
- PASS clear_board_plug: min gap to board_plug 0.4000 mm (need >= 0.3)
- PASS plug_refs_board_plug: min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
- PASS apertures_-X: wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS oversize_board_cut: opening 11.800 x 8.800 vs plug 11.000 x 8.000: 0.400 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_board_cut_base: 2.0500 mm of material round board_cut toward outer at x = -2.500 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5960 mm of material round boss_1_lid_hole toward outer at z = 11.200 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5960 mm of material round boss_2_lid_hole toward outer at z = 11.200 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5960 mm of material round boss_3_lid_hole toward outer at z = 11.200 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5960 mm of material round boss_4_lid_hole toward outer at z = 11.200 (need >= 1.5)
- PASS retention_board: arduino nano held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: no rim piece 6 mm long; -X: the hook or arm meets keepout component_side, usb)
- PASS supported: worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
- PASS rib_interference_cradle_rib_xm_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_xp_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_ym_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_ym_2: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_yp_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_yp_2: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- FAIL bbox: outside 57.87 x 30.17 x 17.90 mm, max 60 x 30 x 26 with X longest
- PASS below_split_board_cut: board_cut top 7.950 + ligament 1.5 vs split 10.000
- PASS bridge_board_cut: board_cut: flat roof span 11.800 vs bridge limit 15
- PASS pilot_depth_boss_1: pilot depth 7.7 vs boss height 15.500 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 7.7 vs boss height 15.500 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 7.7 vs boss height 15.500 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 7.7 vs boss height 15.500 (floor included) - 0.8
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
- PASS panel_keepouts_control_1_1: min gap to control_1_1_keepouts ≥ 5.0000 mm (need >= 0)
- PASS panel_clear_control_1_1: min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
- PASS panel_board_control_1_1: min gap to board ≥ 5.2000 mm (need >= 0.2)
- PASS panel_seated_control_1_1: lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
- PASS panel_hole_control_1_1: hole Ø5.500 for Ø5 (0.250 per side)
- PASS panel_keepouts_control_1_2: min gap to control_1_2_keepouts ≥ 5.0000 mm (need >= 0)
- PASS panel_clear_control_1_2: min gap to control_1_2_ref 0.4000 mm (need >= 0.2)
- PASS panel_board_control_1_2: min gap to board ≥ 5.2000 mm (need >= 0.2)
- PASS panel_seated_control_1_2: lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
- PASS panel_hole_control_1_2: hole Ø5.500 for Ø5 (0.250 per side)
- PASS panel_keepouts_control_1_3: min gap to control_1_3_keepouts ≥ 5.0000 mm (need >= 0)
- PASS panel_clear_control_1_3: min gap to control_1_3_ref 0.4000 mm (need >= 0.2)
- PASS panel_board_control_1_3: min gap to board ≥ 5.2000 mm (need >= 0.2)
- PASS panel_seated_control_1_3: lid underside 10.000 vs contact plane 10.000 (gap 0.0000, max 0.1)
- PASS panel_hole_control_1_3: hole Ø5.500 for Ø5 (0.250 per side)
- PASS text_coverage: 1 named plug connection(s) covered
