# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.958  L1.1: Pick the Arduino Uno R3 from the parts catalogue, state its pose, and locate its USB-B receptacle and DC jack — both on one short edge of the board — at one and the same short end of the case.
      ok  inside_board [inside] board: 1.4482 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 1.4482 mm (need >= 0.5)
PASS     +0.958  L1.2: With the case shut, the 68.6 x 53.3 x 1.6 mm board must have at least 0.5 mm of space to every printed surface, other than at its standoffs.
      ok  inside_board [inside] board: 1.4482 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 1.4482 mm (need >= 0.5)
PASS     +0.110  L1.3: Support the board on four standoffs, neither more nor fewer, one at each of its four mounting holes. Outside diameter is 5 to 7 mm, their top planes agree within 0.1 mm, and each carries a pilot hole deep enough for a 10 mm M3 self-tapping screw to seat (the 1.6 mm board counted).
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 3 + 2 x 0 vs hole Ø3.2
PASS     +0.105  L1.4: Case closed, nothing may be closer than 12 mm above the board's top surface or 4 mm beneath its underside; the standoffs at the holes are the only exception.
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 1.3000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.9536 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.0952 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0952 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 1.6000 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 1.6000 mm (need >= 0)
PASS     -0.000  L1.5: Case closed, a USB-B plug, shell and moulded handle both, must go right into the receptacle through a single opening in the end wall with 0.3 mm or more between it and the case on every side, and the opening can be no more than 1.5 mm larger than the plug on any side.
      ok  clear_board_usb_plug [clear_of] min gap to board_usb_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_usb_cut [aperture_oversize] opening 16.800 x 14.750 vs plug 16.000 x 13.000: 1.350 mm per side (max 1.5)
      ok  oversize_board_dc_cut [aperture_oversize] opening 11.814 x 11.814 vs plug 11.000 x 11.000: 0.407 mm per side (max 1.5)
      ok  text_coverage [coverage] 2 named plug connection(s) covered
PASS     -0.000  L1.6: Case closed, a 5.5 x 2.1 mm DC barrel plug including its moulded handle must go fully into the jack via a separate opening in that same end wall while the USB plug is in as well, keeping 0.3 mm or more clear of the case all round, and the opening can exceed the plug by 1.5 mm at most on any side.
      ok  clear_board_dc_plug [clear_of] min gap to board_dc_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_dc_cut [aperture_oversize] opening 11.814 x 11.814 vs plug 11.000 x 11.000: 0.407 mm per side (max 1.5)
      ok  text_coverage [coverage] 2 named plug connection(s) covered
PASS     +0.010  L1.7: Fit the lid with a straight line of 5 to 9 vent slots right above the ATmega328P. Each is 1.5 to 3.0 mm wide and 8 to 12 mm long on a 3.5 to 6.5 mm pitch, and the open area adds up to at least 100 mm².
      ok  vent_count [vent_count] count 9 (band 5..9)
      ok  vent_area [vent_area] 9 slots, 180.0 mm2 open (need >= 0)
      ok  vent_zone_mcu [vent_zone] worst slot end -0.800 mm past the zone end; row 0.000 mm off the zone centre line
PASS     +0.000  L1.8: Build the case from a base and a separate lid that can be removed: the lid is a flat plate sitting in a rebate cut in the top of the walls (2 to 3 mm plate, 0.15 to 0.35 mm gap per side as fit, upstand of at least 1 mm), held by four M3 self-tapping screws that go into four bosses in the base.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 3 + 2 x 0 vs hole Ø3.2
      ok  closure_evidence [closure_evidence] closure rebate; the text names rebate (holds; L1.8: "Build the case from a base and a separate lid that can be removed: the lid is a flat plate sitting in a rebate cut in the top of the walls (2 to 3 mm plate, 0.15 to 0.35 mm gap per side as fit, upstand of at least 1 mm), held by four M3 self-tapping screws that go into four bosses in the base.")
UNLINKED         L1.9: When closed the case has no holes except for the USB opening, the DC opening, the vent slots and the screw holes, and the walls, floor and lid are 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: Each of base and lid is a single manifold body for FDM printing with no supports: overhangs no steeper than 45° from vertical and bridges no longer than 15 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +4.010  L1.11: Overall the closed case is limited to 100 x 70 x 35 mm, with the longest dimension along the board's 68.6 mm side, and it should sit flat on a desk without tipping over.
      ok  bbox [bbox_within] outside 96.00 x 61.20 x 28.35 mm, max 100 x 70 x 35 with X longest
UNLINKED         L1.12: With the lid removed, the populated board must lower straight onto the standoffs, a screwdriver must reach every board screw, and the screws for the lid must be distinct from those for the board.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.13: Deliver the base STL, the lid STL, the OpenSCAD source, the declared board pose and the agent's own clearance report; the report has to agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap -1.033e-14 mm3 (max 1)
      ok  clear_driver_0 [clear_of] min gap to driver_0 1.0964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 1.0964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 1.6000 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 1.6000 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 2 through opening(s), expected 2; 1 blind region(s) ()
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 1 blind region(s) ()
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 1 blind region(s) ()
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 1 blind region(s) ()
      ok  ligament_board_usb_cut_base [ligament] 4.0000 mm of material round board_usb_cut toward outer at x = -15.000 (need >= 1.5)
      ok  ligament_board_dc_cut_base [ligament] 5.6929 mm of material round board_dc_cut toward outer at x = -15.000 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.7963 mm of material round standoff_1_pilot toward outer at z = -4.255 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.7963 mm of material round standoff_2_pilot toward outer at z = -4.255 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.7963 mm of material round standoff_3_pilot toward outer at z = -4.255 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.7963 mm of material round standoff_4_pilot toward outer at z = -4.255 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 12.695 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 2.1479 mm of material round boss_1_lid_hole toward outer at z = 17.750 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 12.695 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 2.1479 mm of material round boss_2_lid_hole toward outer at z = 17.750 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 12.695 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 2.1479 mm of material round boss_3_lid_hole toward outer at z = 17.750 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 12.695 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 2.1480 mm of material round boss_4_lid_hole toward outer at z = 17.750 (need >= 1.5)
      ok  ligament_vent_1_lid [ligament] 2.0000 mm of material round vent_1 toward vent_2 at z = 17.750 (need >= 1.5)
      ok  ligament_vent_2_lid [ligament] 2.0000 mm of material round vent_2 toward vent_3 at z = 17.750 (need >= 1.5)
      ok  ligament_vent_3_lid [ligament] 2.0000 mm of material round vent_3 toward vent_4 at z = 17.750 (need >= 1.5)
      ok  ligament_vent_4_lid [ligament] 2.0000 mm of material round vent_4 toward vent_5 at z = 17.750 (need >= 1.5)
      ok  ligament_vent_5_lid [ligament] 2.0000 mm of material round vent_5 toward vent_6 at z = 17.750 (need >= 1.5)
      ok  ligament_vent_6_lid [ligament] 2.0000 mm of material round vent_6 toward vent_7 at z = 17.750 (need >= 1.5)
      ok  ligament_vent_7_lid [ligament] 2.0000 mm of material round vent_7 toward vent_8 at z = 17.750 (need >= 1.5)
      ok  ligament_vent_8_lid [ligament] 2.0000 mm of material round vent_8 toward vent_9 at z = 17.750 (need >= 1.5)
      ok  ligament_vent_9_lid [ligament] 2.0000 mm of material round vent_9 toward vent_8 at z = 17.750 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_board_usb_cut [port_below_split] board_usb_cut top 14.950 + ligament 1.5 vs split 16.550
      ok  below_split_board_dc_cut [port_below_split] board_dc_cut top 13.000 + ligament 1.5 vs split 16.550
      ok  bridge_board_usb_cut [bridge] board_usb_cut: roof top width 14.900 vs bridge limit 15
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 7.7 vs boss height 25.950 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 7.7 vs boss height 25.950 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 7.7 vs boss height 25.950 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 7.7 vs boss height 25.950 (floor included) - 0.8
      ok  lid_fit_x [lid_fit] plate 92.500 in rebate 93.000: 0.250 per side
      ok  rebate_upstand_x [rebate_upstand] base 96.000 - rebate 93.000: upstand 1.500
      ok  lid_fit_y [lid_fit] plate 57.700 in rebate 58.200: 0.250 per side
      ok  rebate_upstand_y [rebate_upstand] base 61.200 - rebate 58.200: upstand 1.500
      ok  lid_flush [lid_flush] plate top 18.950 vs upstand top 18.950
      ok  boss_top_plane_boss_1 [boss_top_plane] boss_1 top 16.550 vs rebate floor 16.550
      ok  boss_top_plane_boss_2 [boss_top_plane] boss_2 top 16.550 vs rebate floor 16.550
      ok  boss_top_plane_boss_3 [boss_top_plane] boss_3 top 16.550 vs rebate floor 16.550
      ok  boss_top_plane_boss_4 [boss_top_plane] boss_4 top 16.550 vs rebate floor 16.550
      ok  pilot_engagement_standoff_1 [pilot_engagement] pilot depth 8.500 vs min_engagement 6
      ok  boss_od_standoff_1 [boss_od] outside diameter 6.100 vs min_boss_od 6
      ok  pilot_bottoming_standoff_1 [pilot_bottoming] pilot depth 8.500 vs screw length 10 - clamped plate 1.600
      ok  pilot_engagement_standoff_2 [pilot_engagement] pilot depth 8.500 vs min_engagement 6
      ok  boss_od_standoff_2 [boss_od] outside diameter 6.100 vs min_boss_od 6
      ok  pilot_bottoming_standoff_2 [pilot_bottoming] pilot depth 8.500 vs screw length 10 - clamped plate 1.600
      ok  pilot_engagement_standoff_3 [pilot_engagement] pilot depth 8.500 vs min_engagement 6
      ok  boss_od_standoff_3 [boss_od] outside diameter 6.100 vs min_boss_od 6
      ok  pilot_bottoming_standoff_3 [pilot_bottoming] pilot depth 8.500 vs screw length 10 - clamped plate 1.600
      ok  pilot_engagement_standoff_4 [pilot_engagement] pilot depth 8.500 vs min_engagement 6
      ok  boss_od_standoff_4 [boss_od] outside diameter 6.100 vs min_boss_od 6
      ok  pilot_bottoming_standoff_4 [pilot_bottoming] pilot depth 8.500 vs screw length 10 - clamped plate 1.600
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
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap -1.033e-14 mm3 (max 1)
- PASS inside_board: board: 1.4482 mm from the enclosure (need >= 0.5)
- PASS clear_board: min gap to board 1.4482 mm (need >= 0.5)
- PASS clear_keepout_top: min gap to board_ko_top 1.3000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.9536 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.0952 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.0952 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 1.6000 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 1.6000 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 1.0964 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 1.0964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 1.6000 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 1.6000 mm (need >= 0)
- PASS clear_board_usb_plug: min gap to board_usb_plug 0.4000 mm (need >= 0.3)
- PASS clear_board_dc_plug: min gap to board_dc_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 2 through opening(s), expected 2; 1 blind region(s) ()
- PASS oversize_board_usb_cut: opening 16.800 x 14.750 vs plug 16.000 x 13.000: 1.350 mm per side (max 1.5)
- PASS oversize_board_dc_cut: opening 11.814 x 11.814 vs plug 11.000 x 11.000: 0.407 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 1 blind region(s) ()
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 1 blind region(s) ()
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 1 blind region(s) ()
- PASS ligament_board_usb_cut_base: 4.0000 mm of material round board_usb_cut toward outer at x = -15.000 (need >= 1.5)
- PASS ligament_board_dc_cut_base: 5.6929 mm of material round board_dc_cut toward outer at x = -15.000 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.7963 mm of material round standoff_1_pilot toward outer at z = -4.255 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.7963 mm of material round standoff_2_pilot toward outer at z = -4.255 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.7963 mm of material round standoff_3_pilot toward outer at z = -4.255 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.7963 mm of material round standoff_4_pilot toward outer at z = -4.255 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 12.695 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 2.1479 mm of material round boss_1_lid_hole toward outer at z = 17.750 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 12.695 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 2.1479 mm of material round boss_2_lid_hole toward outer at z = 17.750 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 12.695 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 2.1479 mm of material round boss_3_lid_hole toward outer at z = 17.750 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 12.695 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 2.1480 mm of material round boss_4_lid_hole toward outer at z = 17.750 (need >= 1.5)
- PASS ligament_vent_1_lid: 2.0000 mm of material round vent_1 toward vent_2 at z = 17.750 (need >= 1.5)
- PASS ligament_vent_2_lid: 2.0000 mm of material round vent_2 toward vent_3 at z = 17.750 (need >= 1.5)
- PASS ligament_vent_3_lid: 2.0000 mm of material round vent_3 toward vent_4 at z = 17.750 (need >= 1.5)
- PASS ligament_vent_4_lid: 2.0000 mm of material round vent_4 toward vent_5 at z = 17.750 (need >= 1.5)
- PASS ligament_vent_5_lid: 2.0000 mm of material round vent_5 toward vent_6 at z = 17.750 (need >= 1.5)
- PASS ligament_vent_6_lid: 2.0000 mm of material round vent_6 toward vent_7 at z = 17.750 (need >= 1.5)
- PASS ligament_vent_7_lid: 2.0000 mm of material round vent_7 toward vent_8 at z = 17.750 (need >= 1.5)
- PASS ligament_vent_8_lid: 2.0000 mm of material round vent_8 toward vent_9 at z = 17.750 (need >= 1.5)
- PASS ligament_vent_9_lid: 2.0000 mm of material round vent_9 toward vent_8 at z = 17.750 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 96.00 x 61.20 x 28.35 mm, max 100 x 70 x 35 with X longest
- PASS below_split_board_usb_cut: board_usb_cut top 14.950 + ligament 1.5 vs split 16.550
- PASS below_split_board_dc_cut: board_dc_cut top 13.000 + ligament 1.5 vs split 16.550
- PASS bridge_board_usb_cut: board_usb_cut: roof top width 14.900 vs bridge limit 15
- PASS pilot_depth_standoff_1: pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
- PASS pilot_depth_boss_1: pilot depth 7.7 vs boss height 25.950 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 7.7 vs boss height 25.950 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 7.7 vs boss height 25.950 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 7.7 vs boss height 25.950 (floor included) - 0.8
- PASS lid_fit_x: plate 92.500 in rebate 93.000: 0.250 per side
- PASS rebate_upstand_x: base 96.000 - rebate 93.000: upstand 1.500
- PASS lid_fit_y: plate 57.700 in rebate 58.200: 0.250 per side
- PASS rebate_upstand_y: base 61.200 - rebate 58.200: upstand 1.500
- PASS lid_flush: plate top 18.950 vs upstand top 18.950
- PASS boss_top_plane_boss_1: boss_1 top 16.550 vs rebate floor 16.550
- PASS boss_top_plane_boss_2: boss_2 top 16.550 vs rebate floor 16.550
- PASS boss_top_plane_boss_3: boss_3 top 16.550 vs rebate floor 16.550
- PASS boss_top_plane_boss_4: boss_4 top 16.550 vs rebate floor 16.550
- PASS vent_count: count 9 (band 5..9)
- PASS vent_area: 9 slots, 180.0 mm2 open (need >= 0)
- PASS vent_zone_mcu: worst slot end -0.800 mm past the zone end; row 0.000 mm off the zone centre line
- PASS pilot_engagement_standoff_1: pilot depth 8.500 vs min_engagement 6
- PASS boss_od_standoff_1: outside diameter 6.100 vs min_boss_od 6
- PASS pilot_bottoming_standoff_1: pilot depth 8.500 vs screw length 10 - clamped plate 1.600
- PASS pilot_engagement_standoff_2: pilot depth 8.500 vs min_engagement 6
- PASS boss_od_standoff_2: outside diameter 6.100 vs min_boss_od 6
- PASS pilot_bottoming_standoff_2: pilot depth 8.500 vs screw length 10 - clamped plate 1.600
- PASS pilot_engagement_standoff_3: pilot depth 8.500 vs min_engagement 6
- PASS boss_od_standoff_3: outside diameter 6.100 vs min_boss_od 6
- PASS pilot_bottoming_standoff_3: pilot depth 8.500 vs screw length 10 - clamped plate 1.600
- PASS pilot_engagement_standoff_4: pilot depth 8.500 vs min_engagement 6
- PASS boss_od_standoff_4: outside diameter 6.100 vs min_boss_od 6
- PASS pilot_bottoming_standoff_4: pilot depth 8.500 vs screw length 10 - clamped plate 1.600
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
- PASS pilot_band_standoff_1: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_standoff_2: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_standoff_3: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_standoff_4: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_1: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_2: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_3: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_4: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS board_screw_passes_hole: thread 3 + 2 x 0 vs hole Ø3.2
- PASS text_coverage: 2 named plug connection(s) covered
- PASS closure_evidence: closure rebate; the text names rebate (holds; L1.8: "Build the case from a base and a separate lid that can be removed: the lid is a flat plate sitting in a rebate cut in the top of the walls (2 to 3 mm plate, 0.15 to 0.35 mm gap per side as fit, upstand of at least 1 mm), held by four M3 self-tapping screws that go into four bosses in the base.")
