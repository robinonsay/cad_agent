# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.110  L1.1: From the parts catalogue, put the Raspberry Pi Zero 2 W into the case in its natural orientation, so that the mini-HDMI port and both micro-USB ports face a long wall and the microSD slot faces the short wall at that end, and declare this pose.
      ok  inside_board [inside] board: 0.6000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.6000 mm (need >= 0.5)
PASS     +0.110  L1.2: Once the case is closed, the 65 x 30 mm board needs at least 0.5 mm of space around it from all printed surfaces, with the exception of its standoffs.
      ok  inside_board [inside] board: 0.6000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.6000 mm (need >= 0.5)
PASS     +0.110  L1.3: Four standoffs, exactly, carry the board; one sits under each 2.75 mm mounting hole of the 58 x 23 mm pattern and has a pilot hole to take an M2.5 screw through the board.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2.5 + 2 x 0 vs hole Ø2.75
PASS     +0.510  L1.4: Shut the lid and nothing in the case may be nearer than 5 mm above the board's top surface or 2 mm below its underside (the standoffs at the holes excepted); the board and its connectors must be inside the case.
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.5000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.6000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.5021 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.5021 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.5000 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.5000 mm (need >= 0)
FAIL     -2.790  L1.5: With the lid shut, a mini-HDMI plug must seat fully in the board through a single opening in the long wall and not touch the case, the opening being no more than 1.5 mm larger than the plug per side.
      ok  clear_board_hdmi_plug [clear_of] min gap to board_hdmi_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_sd_cut [aperture_oversize] opening 12.800 x 6.200 vs plug 12.000 x 5.400: 0.400 mm per side (max 1.5)
      ok  oversize_board_hdmi_cut [aperture_oversize] opening 17.800 x 8.800 vs plug 17.000 x 8.000: 0.400 mm per side (max 1.5)
      ok  oversize_board_usb_data_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  oversize_board_usb_power_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      NO  bridge_board_hdmi_cut [bridge] board_hdmi_cut: flat roof span 17.800 vs bridge limit 15; conflict: stated oversize vs bridge limit: board_hdmi_cut is 17.800 mm wide; a roof to the 15 mm bridge limit would rise 1.450 mm and leave its top 1.850 mm above the plug (opening_oversize_max 1.5 - design margin 0.1), so the roof stays flat
      ok  text_coverage [coverage] 4 named plug connection(s) covered
PASS     -0.000  L1.6: With the lid shut, two micro-USB plugs (data and power) must seat fully at once through two openings in that same long wall, touching neither the case nor one another, and each opening is no more than 1.5 mm larger than its plug per side.
      ok  clear_board_usb_data_plug [clear_of] min gap to board_usb_data_plug 0.4000 mm (need >= 0.3)
      ok  clear_board_usb_power_plug [clear_of] min gap to board_usb_power_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_usb_data_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  oversize_board_usb_power_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 4 named plug connection(s) covered
PASS     -0.000  L1.7: With the lid shut, you must be able to push a microSD card in and pull it out through one opening in the end wall without touching the case, the opening being at most 1.5 mm larger than the card access zone on any side.
      ok  clear_board_sd_plug [clear_of] min gap to board_sd_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_sd_cut [aperture_oversize] opening 12.800 x 6.200 vs plug 12.000 x 5.400: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 4 named plug connection(s) covered
PASS     +0.110  L1.8: The case consists of a base and a separate lid that can be taken off; it sits on the base with a sliding fit and four M2.5 screws keep it closed.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2.5 + 2 x 0 vs hole Ø2.75
UNLINKED         L1.9: When closed, the only holes in the case are the HDMI opening, the two USB openings, the SD opening and the screw holes, and walls, floor and lid are between 2 and 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: Base and lid should each be a single manifold body that can be printed on an FDM printer without supports.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +3.010  L1.11: Closed, the case must be no bigger than 90 x 40 x 22 mm, its long axis running along the board's 65 mm side, and it must stand flat on a desk and not tip.
      ok  bbox [bbox_within] outside 85.40 x 36.90 x 19.00 mm, max 90 x 40 x 22 with X longest
UNLINKED         L1.12: Take the lid off and the board should drop straight down on to its standoffs, with every board screw within reach of a screwdriver.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.13: Hand over the base STL, lid STL, OpenSCAD source, declared board pose and the agent's own clearance report, which must agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap -5.227e-15 mm3 (max 1)
      ok  clear_driver_0 [clear_of] min gap to driver_0 1.4000 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 1.4000 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 1.0964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 1.0964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 1 through opening(s), expected 1; 0 blind region(s)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 0 blind region(s)
      ok  apertures_-Y [aperture_count] wall -Y: 3 through opening(s), expected 3; 0 blind region(s)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 0 blind region(s)
      ok  ligament_board_hdmi_cut_base [ligament] 1.6000 mm of material round board_hdmi_cut toward outer at y = -2.700 (need >= 1.5)
      ok  ligament_board_usb_data_cut_base [ligament] 1.8000 mm of material round board_usb_data_cut toward board_usb_power_cut at y = -2.700 (need >= 1.5)
      ok  ligament_board_usb_power_cut_base [ligament] 1.8000 mm of material round board_usb_power_cut toward board_usb_data_cut at y = -2.700 (need >= 1.5)
      ok  ligament_board_sd_cut_base [ligament] 2.8000 mm of material round board_sd_cut toward outer at x = -9.500 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.5968 mm of material round standoff_1_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.5968 mm of material round standoff_2_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.5968 mm of material round standoff_3_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.5968 mm of material round standoff_4_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 1.9963 mm of material round boss_1_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 3.8983 mm of material round boss_1_lid_hole toward outer at z = 10.200 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 1.9963 mm of material round boss_2_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 3.8982 mm of material round boss_2_lid_hole toward outer at z = 10.200 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 1.9963 mm of material round boss_3_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 3.8983 mm of material round boss_3_lid_hole toward outer at z = 10.200 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 1.9963 mm of material round boss_4_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 3.8982 mm of material round boss_4_lid_hole toward outer at z = 10.200 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_board_hdmi_cut [port_below_split] board_hdmi_cut top 7.400 + ligament 1.5 vs split 9.000
      ok  below_split_board_usb_data_cut [port_below_split] board_usb_data_cut top 6.600 + ligament 1.5 vs split 9.000
      ok  below_split_board_usb_power_cut [port_below_split] board_usb_power_cut top 6.600 + ligament 1.5 vs split 9.000
      ok  below_split_board_sd_cut [port_below_split] board_sd_cut top 6.200 + ligament 1.5 vs split 9.000
      ok  bridge_board_usb_data_cut [bridge] board_usb_data_cut: flat roof span 10.800 vs bridge limit 15
      ok  bridge_board_usb_power_cut [bridge] board_usb_power_cut: flat roof span 10.800 vs bridge limit 15
      ok  bridge_board_sd_cut [bridge] board_sd_cut: flat roof span 12.800 vs bridge limit 15
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 5.7 vs boss height 16.600 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 5.7 vs boss height 16.600 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 5.7 vs boss height 16.600 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 5.7 vs boss height 16.600 (floor included) - 0.8
      ok  pilot_engagement_standoff_1 [pilot_engagement] pilot depth 6.700 vs min_engagement 5
      ok  boss_od_standoff_1 [boss_od] outside diameter 5.300 vs min_boss_od 5
      ok  pilot_bottoming_standoff_1 [pilot_bottoming] pilot depth 6.700 vs screw length 8 - clamped plate 1.400
      ok  pilot_engagement_standoff_2 [pilot_engagement] pilot depth 6.700 vs min_engagement 5
      ok  boss_od_standoff_2 [boss_od] outside diameter 5.300 vs min_boss_od 5
      ok  pilot_bottoming_standoff_2 [pilot_bottoming] pilot depth 6.700 vs screw length 8 - clamped plate 1.400
      ok  pilot_engagement_standoff_3 [pilot_engagement] pilot depth 6.700 vs min_engagement 5
      ok  boss_od_standoff_3 [boss_od] outside diameter 5.300 vs min_boss_od 5
      ok  pilot_bottoming_standoff_3 [pilot_bottoming] pilot depth 6.700 vs screw length 8 - clamped plate 1.400
      ok  pilot_engagement_standoff_4 [pilot_engagement] pilot depth 6.700 vs min_engagement 5
      ok  boss_od_standoff_4 [boss_od] outside diameter 5.300 vs min_boss_od 5
      ok  pilot_bottoming_standoff_4 [pilot_bottoming] pilot depth 6.700 vs screw length 8 - clamped plate 1.400
      ok  pilot_engagement_boss_1 [pilot_engagement] pilot depth 5.700 vs min_engagement 5
      ok  boss_od_boss_1 [boss_od] outside diameter 6.100 vs min_boss_od 5
      ok  pilot_bottoming_boss_1 [pilot_bottoming] pilot depth 5.700 vs screw length 8 - clamped plate 2.400
      ok  pilot_engagement_boss_2 [pilot_engagement] pilot depth 5.700 vs min_engagement 5
      ok  boss_od_boss_2 [boss_od] outside diameter 6.100 vs min_boss_od 5
      ok  pilot_bottoming_boss_2 [pilot_bottoming] pilot depth 5.700 vs screw length 8 - clamped plate 2.400
      ok  pilot_engagement_boss_3 [pilot_engagement] pilot depth 5.700 vs min_engagement 5
      ok  boss_od_boss_3 [boss_od] outside diameter 6.100 vs min_boss_od 5
      ok  pilot_bottoming_boss_3 [pilot_bottoming] pilot depth 5.700 vs screw length 8 - clamped plate 2.400
      ok  pilot_engagement_boss_4 [pilot_engagement] pilot depth 5.700 vs min_engagement 5
      ok  boss_od_boss_4 [boss_od] outside diameter 6.100 vs min_boss_od 5
      ok  pilot_bottoming_boss_4 [pilot_bottoming] pilot depth 5.700 vs screw length 8 - clamped plate 2.400
      ok  lip_engagement [lip_engagement] lip engagement 2.100 vs 2
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap -5.227e-15 mm3 (max 1)
- PASS inside_board: board: 0.6000 mm from the enclosure (need >= 0.5)
- PASS clear_board: min gap to board 0.6000 mm (need >= 0.5)
- PASS clear_keepout_top: min gap to board_ko_top 0.5000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.6000 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.5021 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.5021 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.5000 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.5000 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 1.4000 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 1.4000 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 1.0964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 1.0964 mm (need >= 0)
- PASS clear_board_hdmi_plug: min gap to board_hdmi_plug 0.4000 mm (need >= 0.3)
- PASS clear_board_usb_data_plug: min gap to board_usb_data_plug 0.4000 mm (need >= 0.3)
- PASS clear_board_usb_power_plug: min gap to board_usb_power_plug 0.4000 mm (need >= 0.3)
- PASS clear_board_sd_plug: min gap to board_sd_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 1 through opening(s), expected 1; 0 blind region(s)
- PASS oversize_board_sd_cut: opening 12.800 x 6.200 vs plug 12.000 x 5.400: 0.400 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 0 blind region(s)
- PASS apertures_-Y: wall -Y: 3 through opening(s), expected 3; 0 blind region(s)
- PASS oversize_board_hdmi_cut: opening 17.800 x 8.800 vs plug 17.000 x 8.000: 0.400 mm per side (max 1.5)
- PASS oversize_board_usb_data_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS oversize_board_usb_power_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 0 blind region(s)
- PASS ligament_board_hdmi_cut_base: 1.6000 mm of material round board_hdmi_cut toward outer at y = -2.700 (need >= 1.5)
- PASS ligament_board_usb_data_cut_base: 1.8000 mm of material round board_usb_data_cut toward board_usb_power_cut at y = -2.700 (need >= 1.5)
- PASS ligament_board_usb_power_cut_base: 1.8000 mm of material round board_usb_power_cut toward board_usb_data_cut at y = -2.700 (need >= 1.5)
- PASS ligament_board_sd_cut_base: 2.8000 mm of material round board_sd_cut toward outer at x = -9.500 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.5968 mm of material round standoff_1_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.5968 mm of material round standoff_2_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.5968 mm of material round standoff_3_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.5968 mm of material round standoff_4_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 1.9963 mm of material round boss_1_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 3.8983 mm of material round boss_1_lid_hole toward outer at z = 10.200 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 1.9963 mm of material round boss_2_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 3.8982 mm of material round boss_2_lid_hole toward outer at z = 10.200 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 1.9963 mm of material round boss_3_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 3.8983 mm of material round boss_3_lid_hole toward outer at z = 10.200 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 1.9963 mm of material round boss_4_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 3.8982 mm of material round boss_4_lid_hole toward outer at z = 10.200 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 85.40 x 36.90 x 19.00 mm, max 90 x 40 x 22 with X longest
- PASS below_split_board_hdmi_cut: board_hdmi_cut top 7.400 + ligament 1.5 vs split 9.000
- PASS below_split_board_usb_data_cut: board_usb_data_cut top 6.600 + ligament 1.5 vs split 9.000
- PASS below_split_board_usb_power_cut: board_usb_power_cut top 6.600 + ligament 1.5 vs split 9.000
- PASS below_split_board_sd_cut: board_sd_cut top 6.200 + ligament 1.5 vs split 9.000
- FAIL bridge_board_hdmi_cut: board_hdmi_cut: flat roof span 17.800 vs bridge limit 15; conflict: stated oversize vs bridge limit: board_hdmi_cut is 17.800 mm wide; a roof to the 15 mm bridge limit would rise 1.450 mm and leave its top 1.850 mm above the plug (opening_oversize_max 1.5 - design margin 0.1), so the roof stays flat
- PASS bridge_board_usb_data_cut: board_usb_data_cut: flat roof span 10.800 vs bridge limit 15
- PASS bridge_board_usb_power_cut: board_usb_power_cut: flat roof span 10.800 vs bridge limit 15
- PASS bridge_board_sd_cut: board_sd_cut: flat roof span 12.800 vs bridge limit 15
- PASS pilot_depth_standoff_1: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_boss_1: pilot depth 5.7 vs boss height 16.600 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 5.7 vs boss height 16.600 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 5.7 vs boss height 16.600 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 5.7 vs boss height 16.600 (floor included) - 0.8
- PASS pilot_engagement_standoff_1: pilot depth 6.700 vs min_engagement 5
- PASS boss_od_standoff_1: outside diameter 5.300 vs min_boss_od 5
- PASS pilot_bottoming_standoff_1: pilot depth 6.700 vs screw length 8 - clamped plate 1.400
- PASS pilot_engagement_standoff_2: pilot depth 6.700 vs min_engagement 5
- PASS boss_od_standoff_2: outside diameter 5.300 vs min_boss_od 5
- PASS pilot_bottoming_standoff_2: pilot depth 6.700 vs screw length 8 - clamped plate 1.400
- PASS pilot_engagement_standoff_3: pilot depth 6.700 vs min_engagement 5
- PASS boss_od_standoff_3: outside diameter 5.300 vs min_boss_od 5
- PASS pilot_bottoming_standoff_3: pilot depth 6.700 vs screw length 8 - clamped plate 1.400
- PASS pilot_engagement_standoff_4: pilot depth 6.700 vs min_engagement 5
- PASS boss_od_standoff_4: outside diameter 5.300 vs min_boss_od 5
- PASS pilot_bottoming_standoff_4: pilot depth 6.700 vs screw length 8 - clamped plate 1.400
- PASS pilot_engagement_boss_1: pilot depth 5.700 vs min_engagement 5
- PASS boss_od_boss_1: outside diameter 6.100 vs min_boss_od 5
- PASS pilot_bottoming_boss_1: pilot depth 5.700 vs screw length 8 - clamped plate 2.400
- PASS pilot_engagement_boss_2: pilot depth 5.700 vs min_engagement 5
- PASS boss_od_boss_2: outside diameter 6.100 vs min_boss_od 5
- PASS pilot_bottoming_boss_2: pilot depth 5.700 vs screw length 8 - clamped plate 2.400
- PASS pilot_engagement_boss_3: pilot depth 5.700 vs min_engagement 5
- PASS boss_od_boss_3: outside diameter 6.100 vs min_boss_od 5
- PASS pilot_bottoming_boss_3: pilot depth 5.700 vs screw length 8 - clamped plate 2.400
- PASS pilot_engagement_boss_4: pilot depth 5.700 vs min_engagement 5
- PASS boss_od_boss_4: outside diameter 6.100 vs min_boss_od 5
- PASS pilot_bottoming_boss_4: pilot depth 5.700 vs screw length 8 - clamped plate 2.400
- PASS lip_engagement: lip engagement 2.100 vs 2
- PASS pilot_band_standoff_1: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_standoff_2: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_standoff_3: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_standoff_4: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_boss_1: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_boss_2: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_boss_3: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_boss_4: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS board_screw_passes_hole: thread 2.5 + 2 x 0 vs hole Ø2.75
- PASS text_coverage: 4 named plug connection(s) covered
