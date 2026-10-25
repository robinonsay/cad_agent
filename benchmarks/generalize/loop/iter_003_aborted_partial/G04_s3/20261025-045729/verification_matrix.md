# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.110  L1.1: The design shall place the Raspberry Pi Zero 2 W in the case in its own orientation, from the parts catalogue, with the mini-HDMI and both micro-USB ports facing one long wall and the microSD slot facing the short wall at its end, and shall declare that pose.
      ok  inside_board [inside] board: 0.6000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.6000 mm (need >= 0.5)
PASS     +0.110  L1.2: The 65 x 30 mm board shall fit inside the closed case with at least 0.5 mm clearance to every printed surface, apart from where it rests on its standoffs.
      ok  inside_board [inside] board: 0.6000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.6000 mm (need >= 0.5)
PASS     +0.110  L1.3: The board shall rest on exactly four standoffs, one under each 2.75 mm mounting hole on the 58 x 23 mm pattern, each with a pilot hole for an M2.5 screw through the board.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2.5 + 2 x 0 vs hole Ø2.75
PASS     +0.510  L1.4: With the lid closed, no part of the case shall come within 5 mm above the board's top surface or 2 mm below its underside, except the standoffs under the holes, and the board and its connectors shall lie inside the case.
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.5000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.6000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.5021 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.5000 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.5000 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.5000 mm (need >= 0)
PASS     -0.000  L1.5: With the lid closed, a mini-HDMI plug shall plug fully into the board through one opening in the long wall without touching the case, and that opening shall be no more than 1.5 mm bigger than the plug on any side.
      ok  clear_board_hdmi_plug [clear_of] min gap to board_hdmi_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_sd_cut [aperture_oversize] opening 12.800 x 6.200 vs plug 12.000 x 5.400: 0.400 mm per side (max 1.5)
      ok  oversize_board_hdmi_cut [aperture_oversize] opening 17.800 x 8.800 vs plug 17.000 x 8.000: 0.400 mm per side (max 1.5)
      ok  oversize_board_usb_data_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  oversize_board_usb_power_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 4 named plug connection(s) covered
PASS     -0.000  L1.6: With the lid closed, two micro-USB plugs (data and power) shall plug fully in at the same time through two openings in the same long wall without touching the case or each other, and each opening shall be no more than 1.5 mm bigger than the plug on any side.
      ok  clear_board_usb_data_plug [clear_of] min gap to board_usb_data_plug 0.4000 mm (need >= 0.3)
      ok  clear_board_usb_power_plug [clear_of] min gap to board_usb_power_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_usb_data_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  oversize_board_usb_power_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 4 named plug connection(s) covered
PASS     -0.000  L1.7: With the lid closed, a microSD card shall be able to be pushed in and pulled out through one opening in the end wall without touching the case, and that opening shall be no more than 1.5 mm bigger than the card access zone on any side.
      ok  clear_board_sd_plug [clear_of] min gap to board_sd_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_sd_cut [aperture_oversize] opening 12.800 x 6.200 vs plug 12.000 x 5.400: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 4 named plug connection(s) covered
PASS     +0.110  L1.8: The case shall be a base and a separate removable lid that locates on the base with a sliding fit and is held closed by four M2.5 screws.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2.5 + 2 x 0 vs hole Ø2.75
UNLINKED         L1.9: The closed case shall have no openings other than the HDMI opening, the two USB openings, the SD opening and screw holes, and its walls, floor and lid shall be 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: The base and the lid shall each be one manifold body that prints on an FDM printer without supports.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -2.210  L1.11: The closed case shall be no larger than 90 x 40 x 22 mm, longest along the board's 65 mm side, and shall stand flat on a desk without tipping.
      NO  bbox [bbox_within] outside 77.32 x 42.22 x 19.00 mm, max 90 x 40 x 22 with X longest
UNLINKED         L1.12: With the lid off, the board shall drop straight down onto its standoffs and every board screw shall be reachable with a screwdriver.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.13: The design shall be delivered as a base STL, a lid STL, the OpenSCAD source, the declared board pose and the agent's own clearance report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 7.061e-15 mm3 (max 1)
      ok  clear_driver_0 [clear_of] min gap to driver_0 1.4000 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 1.0964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 1.0964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 1.0964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 3 through opening(s), expected 3; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_board_hdmi_cut_base [ligament] 1.6000 mm of material round board_hdmi_cut toward outer at y = -2.700 (need >= 1.5)
      ok  ligament_board_usb_data_cut_base [ligament] 1.8000 mm of material round board_usb_data_cut toward board_usb_power_cut at y = -2.700 (need >= 1.5)
      ok  ligament_board_usb_power_cut_base [ligament] 1.8000 mm of material round board_usb_power_cut toward board_usb_data_cut at y = -2.700 (need >= 1.5)
      ok  ligament_board_sd_cut_base [ligament] 2.8000 mm of material round board_sd_cut toward outer at x = -2.800 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.5968 mm of material round standoff_1_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.5968 mm of material round standoff_2_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.5968 mm of material round standoff_3_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.5968 mm of material round standoff_4_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 1.9963 mm of material round boss_1_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5963 mm of material round boss_1_lid_hole toward outer at z = 10.200 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 1.9963 mm of material round boss_2_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5963 mm of material round boss_2_lid_hole toward outer at z = 10.200 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 1.9963 mm of material round boss_3_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5963 mm of material round boss_3_lid_hole toward outer at z = 10.200 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 1.9963 mm of material round boss_4_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5963 mm of material round boss_4_lid_hole toward outer at z = 10.200 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_board_hdmi_cut [port_below_split] board_hdmi_cut top 7.400 + ligament 1.5 vs split 9.000
      ok  below_split_board_usb_data_cut [port_below_split] board_usb_data_cut top 6.600 + ligament 1.5 vs split 9.000
      ok  below_split_board_usb_power_cut [port_below_split] board_usb_power_cut top 6.600 + ligament 1.5 vs split 9.000
      ok  below_split_board_sd_cut [port_below_split] board_sd_cut top 6.200 + ligament 1.5 vs split 9.000
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
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

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 7.061e-15 mm3 (max 1)
- PASS inside_board: board: 0.6000 mm from the enclosure (need >= 0.5)
- PASS clear_board: min gap to board 0.6000 mm (need >= 0.5)
- PASS clear_keepout_top: min gap to board_ko_top 0.5000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.6000 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.5021 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.5000 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.5000 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.5000 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 1.4000 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 1.0964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 1.0964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 1.0964 mm (need >= 0)
- PASS clear_board_hdmi_plug: min gap to board_hdmi_plug 0.4000 mm (need >= 0.3)
- PASS clear_board_usb_data_plug: min gap to board_usb_data_plug 0.4000 mm (need >= 0.3)
- PASS clear_board_usb_power_plug: min gap to board_usb_power_plug 0.4000 mm (need >= 0.3)
- PASS clear_board_sd_plug: min gap to board_sd_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS oversize_board_sd_cut: opening 12.800 x 6.200 vs plug 12.000 x 5.400: 0.400 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 3 through opening(s), expected 3; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS oversize_board_hdmi_cut: opening 17.800 x 8.800 vs plug 17.000 x 8.000: 0.400 mm per side (max 1.5)
- PASS oversize_board_usb_data_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS oversize_board_usb_power_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_board_hdmi_cut_base: 1.6000 mm of material round board_hdmi_cut toward outer at y = -2.700 (need >= 1.5)
- PASS ligament_board_usb_data_cut_base: 1.8000 mm of material round board_usb_data_cut toward board_usb_power_cut at y = -2.700 (need >= 1.5)
- PASS ligament_board_usb_power_cut_base: 1.8000 mm of material round board_usb_power_cut toward board_usb_data_cut at y = -2.700 (need >= 1.5)
- PASS ligament_board_sd_cut_base: 2.8000 mm of material round board_sd_cut toward outer at x = -2.800 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.5968 mm of material round standoff_1_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.5968 mm of material round standoff_2_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.5968 mm of material round standoff_3_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.5968 mm of material round standoff_4_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 1.9963 mm of material round boss_1_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5963 mm of material round boss_1_lid_hole toward outer at z = 10.200 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 1.9963 mm of material round boss_2_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5963 mm of material round boss_2_lid_hole toward outer at z = 10.200 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 1.9963 mm of material round boss_3_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5963 mm of material round boss_3_lid_hole toward outer at z = 10.200 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 1.9963 mm of material round boss_4_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5963 mm of material round boss_4_lid_hole toward outer at z = 10.200 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- FAIL bbox: outside 77.32 x 42.22 x 19.00 mm, max 90 x 40 x 22 with X longest
- PASS below_split_board_hdmi_cut: board_hdmi_cut top 7.400 + ligament 1.5 vs split 9.000
- PASS below_split_board_usb_data_cut: board_usb_data_cut top 6.600 + ligament 1.5 vs split 9.000
- PASS below_split_board_usb_power_cut: board_usb_power_cut top 6.600 + ligament 1.5 vs split 9.000
- PASS below_split_board_sd_cut: board_sd_cut top 6.200 + ligament 1.5 vs split 9.000
- PASS pilot_depth_standoff_1: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
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
