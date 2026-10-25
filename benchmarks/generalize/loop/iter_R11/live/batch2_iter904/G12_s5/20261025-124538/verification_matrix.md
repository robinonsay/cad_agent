# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.010  L1.1: Using the catalogue, the design positions the ESP32 DevKitC V4 so the micro-USB port faces the short end at −X and the antenna points toward +X; it also puts three 5 mm LEDs in the lid. Nothing may collide, and the layout has to be declared.
      ok  inside_board [inside] board: 3.0000 mm from the enclosure (need >= 3)
      ok  clear_board [clear_of] min gap to board 3.0000 mm (need >= 3)
      ok  plug_refs_board_plug [clear_of] min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
      ok  retention_board [retention] esp32 devkitc held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets header_a, keepout component_side, keepout header_pins_a; -X: the hook or arm meets keepout component_side, usb)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
      ok  panel_keepouts_control_1_1 [clear_of] min gap to control_1_1_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_1 [clear_of] min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_1 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_1 [panel_seated] lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_1 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_2 [clear_of] min gap to control_1_2_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_2 [clear_of] min gap to control_1_2_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_2 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_2 [panel_seated] lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_2 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_3 [clear_of] min gap to control_1_3_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_3 [clear_of] min gap to control_1_3_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_3 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_3 [panel_seated] lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_3 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
UNLINKED         L1.2: Support the board on four pads beneath its two end regions, away from the header footprint, every pad no smaller than 10 mm². The walls plus two stops at the antenna end hold it in place, the stops being 0.2 to 1.0 mm away from the board and under its top face. None of the printed box may intrude on the board's keep-out volumes (header pins, tails, component side).  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.3: The antenna keep-out must stay empty of walls and lid. Per the part's data it covers the final 6.0 mm of the board and the 8.0 mm past its end, spanning the board's full width and reaching up to 5.0 mm over the top of the module; the cavity must run at least 8.0 mm beyond the antenna end.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  L1.4: It must be possible to push a micro-USB cable all the way into the board, lid on, through one hole in the end wall at −X. The hole gives the plug at least 0.3 mm of room all the way round, but is no more than 1.5 mm larger than the plug on any side, and at least 1.5 mm of wall remains around it.
      ok  clear_board_plug [clear_of] min gap to board_plug 0.4000 mm (need >= 0.3)
      ok  plug_refs_board_plug [clear_of] min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
      ok  oversize_board_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 1 named plug connection(s) covered
PASS     +0.110  L1.5: In the lid, each of three 5 mm LEDs goes into a collar so its dome is level with the outer surface and its flange is caught by a shoulder with a snap lip behind, which keeps the LED from dropping out. The collar holes measure 5.2 to 5.4 mm across, the flange overlaps by at least 0.2 mm each side, the dome is within 0.3 mm of flush, and the snap-lip opening is 5.3 to 5.6 mm with at least two slits. Arrange the LEDs in a line with at least 10.0 mm between them, and keep every LED axis at least 4.5 mm (in plan) from the board's header-pin and antenna keep-outs.
      ok  plug_refs_board_plug [clear_of] min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
      ok  panel_keepouts_control_1_1 [clear_of] min gap to control_1_1_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_1 [clear_of] min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_1 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_1 [panel_seated] lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_1 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_2 [clear_of] min gap to control_1_2_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_2 [clear_of] min gap to control_1_2_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_2 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_2 [panel_seated] lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_2 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_3 [clear_of] min gap to control_1_3_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_3 [clear_of] min gap to control_1_3_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_3 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_3 [panel_seated] lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_3 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
UNLINKED         L1.6: The box gets a pair of ears, and each carries a countersunk slot sized for a 4.2 mm wood screw. The centres of the two slots are 100.0 mm from each other, and the countersink outline of each slot stays at least 3.0 mm away from its ear's edge and from the box. Every slot is a stadium 4.5 mm wide with 4.0 mm between the centres of its ends (so you can adjust), beneath a 90 degree countersink that is 8.4 mm across. Make the ears 3.5 to 5.0 mm thick, with the slot centres symmetric about the centre of the box to within 0.5 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.7: So the box can lie flat on the wall, its back should be a flat face and the ears must be coplanar with it, within 0.3 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.8: Make the lid a separate piece that sits on the base via a sliding lip and is secured by four M3 self-tapping screws that go into tabs outside the cavity. The screw axes lie 3.5 to 5.0 mm outside the wall's outer face, the pilot holes are 2.4 to 2.6 mm across and at least 6.0 mm deep, and the lid's holes are 3.4 mm. The lip should be at least 2.0 mm deep, with 0.15 to 0.35 mm of clearance on each side.
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
PASS     +0.110  L1.9: Once closed, the box may be open only at the USB port, the three LED holes, the screw holes for the lid and the two slots in the ears. Wall, floor and lid thickness should fall between 2.0 and 4.0 mm, and every opening needs at least 1.5 mm of surrounding material.
      ok  plug_refs_board_plug [clear_of] min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
      ok  panel_keepouts_control_1_1 [clear_of] min gap to control_1_1_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_1 [clear_of] min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_1 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_1 [panel_seated] lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_1 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_2 [clear_of] min gap to control_1_2_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_2 [clear_of] min gap to control_1_2_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_2 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_2 [panel_seated] lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_2 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
      ok  panel_keepouts_control_1_3 [clear_of] min gap to control_1_3_keepouts ≥ 5.0000 mm (need >= 0)
      ok  panel_clear_control_1_3 [clear_of] min gap to control_1_3_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_3 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_3 [panel_seated] lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_3 [panel_hole] hole Ø5.500 for Ø5 (0.250 per side)
UNLINKED         L1.10: Each part must be one manifold body that prints without supports: the base resting on its back face and the lid on its outer face.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +3.110  L1.11: Overall, counting ears and tabs, the shut box must fit within 125 x 50 x 26 mm, with the long direction running along the 54.4 mm side of the board.
      ok  bbox [bbox_within] outside 71.11 x 43.65 x 22.90 mm, max 125 x 50 x 26 with X longest
UNLINKED         L1.12: What comes back is a base STL and a lid STL, the OpenSCAD source, the layout declaration, and the agent's own clearance report, whose figures have to agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -2.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 4.055e-15 mm3 (max 1)
      NO  content_placed_generic_1 [content_placed] generic_1 (generic_box) is not placed: generic_box: no number in the text for size_x, size_y, size_z; the plant cannot build a part whose size the text does not state
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.0000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.0000 mm (need >= 0)
      NO  apertures_-X [aperture_count] wall -X: 3 through opening(s), expected 1; 0 blind region(s)
      NO  apertures_+X [aperture_count] wall +X: 2 through opening(s), expected 0; 0 blind region(s)
      NO  apertures_-Y [aperture_count] wall -Y: 2 through opening(s), expected 0; 0 blind region(s)
      NO  apertures_+Y [aperture_count] wall +Y: 2 through opening(s), expected 0; 0 blind region(s)
      ok  ligament_board_cut_base [ligament] 2.2500 mm of material round board_cut toward floor_top at x = -5.300 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 11.145 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5960 mm of material round boss_1_lid_hole toward outer at z = 16.200 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 11.145 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5960 mm of material round boss_2_lid_hole toward outer at z = 16.200 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 11.145 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5960 mm of material round boss_3_lid_hole toward outer at z = 16.200 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 11.145 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5960 mm of material round boss_4_lid_hole toward outer at z = 16.200 (need >= 1.5)
      ok  rib_interference_cradle_rib_xm_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_xp_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_2 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_3 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_2 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_3 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  below_split_board_cut [port_below_split] board_cut top 6.950 + ligament 1.5 vs split 15.000
      ok  bridge_board_cut [bridge] board_cut: flat roof span 10.800 vs bridge limit 15
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 7.7 vs boss height 20.500 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 7.7 vs boss height 20.500 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 7.7 vs boss height 20.500 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 7.7 vs boss height 20.500 (floor included) - 0.8
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
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 4.055e-15 mm3 (max 1)
- PASS inside_board: board: 3.0000 mm from the enclosure (need >= 3)
- FAIL content_placed_generic_1: generic_1 (generic_box) is not placed: generic_box: no number in the text for size_x, size_y, size_z; the plant cannot build a part whose size the text does not state
- PASS clear_board: min gap to board 3.0000 mm (need >= 3)
- PASS clear_keepout_top: min gap to board_ko_top 0.0000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.0000 mm (need >= 0)
- PASS clear_board_plug: min gap to board_plug 0.4000 mm (need >= 0.3)
- PASS plug_refs_board_plug: min gap to refs_board_plug ≥ 5.0000 mm (need >= 0)
- FAIL apertures_-X: wall -X: 3 through opening(s), expected 1; 0 blind region(s)
- PASS oversize_board_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- FAIL apertures_+X: wall +X: 2 through opening(s), expected 0; 0 blind region(s)
- FAIL apertures_-Y: wall -Y: 2 through opening(s), expected 0; 0 blind region(s)
- FAIL apertures_+Y: wall +Y: 2 through opening(s), expected 0; 0 blind region(s)
- PASS ligament_board_cut_base: 2.2500 mm of material round board_cut toward floor_top at x = -5.300 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 11.145 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5960 mm of material round boss_1_lid_hole toward outer at z = 16.200 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 11.145 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5960 mm of material round boss_2_lid_hole toward outer at z = 16.200 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 11.145 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5960 mm of material round boss_3_lid_hole toward outer at z = 16.200 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 11.145 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5960 mm of material round boss_4_lid_hole toward outer at z = 16.200 (need >= 1.5)
- PASS retention_board: esp32 devkitc held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets header_a, keepout component_side, keepout header_pins_a; -X: the hook or arm meets keepout component_side, usb)
- PASS supported: worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
- PASS rib_interference_cradle_rib_xm_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_xp_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_ym_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_ym_2: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_ym_3: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_yp_1: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_yp_2: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS rib_interference_cradle_rib_yp_3: rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
- PASS bbox: outside 71.11 x 43.65 x 22.90 mm, max 125 x 50 x 26 with X longest
- PASS below_split_board_cut: board_cut top 6.950 + ligament 1.5 vs split 15.000
- PASS bridge_board_cut: board_cut: flat roof span 10.800 vs bridge limit 15
- PASS pilot_depth_boss_1: pilot depth 7.7 vs boss height 20.500 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 7.7 vs boss height 20.500 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 7.7 vs boss height 20.500 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 7.7 vs boss height 20.500 (floor included) - 0.8
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
- PASS panel_seated_control_1_1: lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
- PASS panel_hole_control_1_1: hole Ø5.500 for Ø5 (0.250 per side)
- PASS panel_keepouts_control_1_2: min gap to control_1_2_keepouts ≥ 5.0000 mm (need >= 0)
- PASS panel_clear_control_1_2: min gap to control_1_2_ref 0.4000 mm (need >= 0.2)
- PASS panel_board_control_1_2: min gap to board ≥ 5.2000 mm (need >= 0.2)
- PASS panel_seated_control_1_2: lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
- PASS panel_hole_control_1_2: hole Ø5.500 for Ø5 (0.250 per side)
- PASS panel_keepouts_control_1_3: min gap to control_1_3_keepouts ≥ 5.0000 mm (need >= 0)
- PASS panel_clear_control_1_3: min gap to control_1_3_ref 0.4000 mm (need >= 0.2)
- PASS panel_board_control_1_3: min gap to board ≥ 5.2000 mm (need >= 0.2)
- PASS panel_seated_control_1_3: lid underside 15.000 vs contact plane 15.000 (gap 0.0000, max 0.1)
- PASS panel_hole_control_1_3: hole Ø5.500 for Ø5 (0.250 per side)
- PASS text_coverage: 1 named plug connection(s) covered
