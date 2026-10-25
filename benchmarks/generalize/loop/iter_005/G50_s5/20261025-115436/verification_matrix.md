# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.110  L1.1: From the parts catalogue, position the Pi Zero 2 W, the fan, the OLED and the encoder so that nothing collides and the Pi's two micro-USB ports face the rear wall; declare the layout.
      ok  inside_board [inside] board: 0.3000 mm from the enclosure (need >= 0.2)
      ok  clear_board [clear_of] min gap to board 0.3000 mm (need >= 0.2)
PASS     +0.110  L1.2: Inside the case the Pi is carried on four standoffs, one at each of its four mounting holes, with screws. Keep the board edges 0.5 mm or more from the side and front walls, and the entire Pi, connectors and all, 0.2 mm or more inside the cavity.
      ok  inside_board [inside] board: 0.3000 mm from the enclosure (need >= 0.2)
      ok  clear_board [clear_of] min gap to board 0.3000 mm (need >= 0.2)
PASS     -0.000  L1.3: With the lid on, it must be possible to push two micro-USB cable plugs all the way into the Pi's two micro-USB ports through the rear wall simultaneously, with no contact with the case or with each other. No opening may exceed the plug by more than 1.5 mm on any side.
      ok  clear_board_usb_data_plug [clear_of] min gap to board_usb_data_plug 0.4000 mm (need >= 0.3)
      ok  clear_board_usb_power_plug [clear_of] min gap to board_usb_power_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_usb_data_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  oversize_board_usb_power_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 2 named plug connection(s) covered
UNLINKED         L1.4: Mount the fan over the Pi with four screws in its 32 mm hole pattern, blowing downward. In plan its axis must be within 6 mm of the centre of the Pi board, and there must be 5 mm or more of free air over the inlet and under the exhaust.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.5: Put vent slots in the side walls: 300 square millimetres or more of open area above the fan's mid-plane for intake, and 300 square millimetres or more below the fan for exhaust. Each slot is 2 to 3 mm wide, with 1.5 mm or more of wall left between slots. Spread the intake vents and the exhaust vents over at least two different walls each, and do not put any vent in the front panel, the lid or the floor. A vent counts as intake if its area-weighted centre is above the fan's mid-plane and as exhaust if it is at or below the fan's exhaust face; none may straddle the fan's frame between them.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.6: Inside the case there has to be a continuous route for air, wide enough for a 5 mm sphere to roll along: intake vents, through the fan, then past the Pi to the exhaust vents. Check it in these legs: from a vent's inner mouth to the middle of the 5 mm air gap over the fan inlet, and from the middle of the 5 mm air gap under the fan exhaust, past the Pi, to an exhaust vent's inner mouth. The slots themselves are sized by the vent rule.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.7: The window in the front panel has to reveal the full 25 x 14 mm viewing area of the OLED with nothing in the way, without being too big: 26 to 29 mm wide and 15 to 22 mm tall, centred on the viewing area in width, with its bottom edge 0.4 to 2.0 mm lower than the viewing area's.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.8: Behind the window, glass towards the front, the OLED is held by M2 screws going into posts at its two header-side holes and located by pins in the other two holes, which sit just 1.5 mm from the glass edge, too close for a screw post or head. Leave 3 mm free behind the board for header pins and wires, and keep the OLED 0.5 mm or more away from the fan, the encoder and the Pi.
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
UNLINKED         L1.9: The encoder goes through a hole in the front panel with its body on the inside and its nut and shaft on the outside; at the hole the panel is 2 to 3 mm thick, thin enough for the thread to reach.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: Build the case as a base and a separate lid. The lid locates on the base with a sliding fit and stays closed with snap latches that can flex without breaking: four to eight cantilever hooks, with two or more on each of two opposite side walls, spaced at least 20 mm apart along the wall. Each hook catches a blind recess by 0.6 to 1.2 mm, and peak bending strain must not exceed 1.5 percent.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.11: Apart from the window, the encoder hole, the two USB openings and the vents, the closed case must be sealed, with walls, floor and lid each 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.12: Each of the base and the lid is one manifold body that prints on an FDM printer without supports; round holes to 12 mm, bridges to 15 mm and a horizontal step to 1.2 mm deep (a hook's return face, say) are acceptable.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +13.967  L1.13: Keep the closed case within 90 x 70 x 45 mm so that it sits on a desk and does not tip.
      ok  bbox [bbox_within] outside 76.04 x 40.94 x 23.60 mm, max 90 x 70 x 45 with X longest
UNLINKED         L1.14: Deliverables: STLs for the base and the lid, the OpenSCAD source, the declared layout, and the agent's own clearance report, matching an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -1.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap -3.156e-14 mm3 (max 1)
      NO  content_placed_display_1 [content_placed] display_1 (oled_ssd1306_096) is not placed: rpi_zero2w is not a carrier: no relation places it yet (GM2b)
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.1000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.3000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.1000 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.1000 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.1000 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.1000 mm (need >= 0)
      ok  clear_driver_0 [clear_of] min gap to driver_0 1.4000 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 0.7964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 0.7964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 0.7964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 2 through opening(s), expected 2; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_board_usb_data_cut_base [ligament] 1.8000 mm of material round board_usb_data_cut toward board_usb_power_cut at y = -2.400 (need >= 1.5)
      ok  ligament_board_usb_power_cut_base [ligament] 1.8000 mm of material round board_usb_power_cut toward board_usb_data_cut at y = -2.400 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.5968 mm of material round standoff_1_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.5968 mm of material round standoff_2_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.5968 mm of material round standoff_3_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.5968 mm of material round standoff_4_pilot toward outer at z = -3.355 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 1.9466 mm of material round boss_1_pilot toward outer at z = 11.045 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5966 mm of material round boss_1_lid_hole toward outer at z = 14.800 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 1.9466 mm of material round boss_2_pilot toward outer at z = 11.045 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5966 mm of material round boss_2_lid_hole toward outer at z = 14.800 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 1.9466 mm of material round boss_3_pilot toward outer at z = 11.045 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5966 mm of material round boss_3_lid_hole toward outer at z = 14.800 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 1.9466 mm of material round boss_4_pilot toward outer at z = 11.045 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5966 mm of material round boss_4_lid_hole toward outer at z = 14.800 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_board_usb_data_cut [port_below_split] board_usb_data_cut top 6.600 + ligament 1.5 vs split 13.600
      ok  below_split_board_usb_power_cut [port_below_split] board_usb_power_cut top 6.600 + ligament 1.5 vs split 13.600
      ok  bridge_board_usb_data_cut [bridge] board_usb_data_cut: flat roof span 10.800 vs bridge limit 15
      ok  bridge_board_usb_power_cut [bridge] board_usb_power_cut: flat roof span 10.800 vs bridge limit 15
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 5.1 vs boss height 21.200 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 5.1 vs boss height 21.200 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 5.1 vs boss height 21.200 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 5.1 vs boss height 21.200 (floor included) - 0.8
      NO  vent_placed [vent_placed] no vent slot placed: vent: face not resolved (face words only)
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
      ok  pilot_engagement_boss_1 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_boss_1 [boss_od] outside diameter 5.600 vs min_boss_od 5
      ok  pilot_bottoming_boss_1 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 2.400
      ok  pilot_engagement_boss_2 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_boss_2 [boss_od] outside diameter 5.600 vs min_boss_od 5
      ok  pilot_bottoming_boss_2 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 2.400
      ok  pilot_engagement_boss_3 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_boss_3 [boss_od] outside diameter 5.600 vs min_boss_od 5
      ok  pilot_bottoming_boss_3 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 2.400
      ok  pilot_engagement_boss_4 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_boss_4 [boss_od] outside diameter 5.600 vs min_boss_od 5
      ok  pilot_bottoming_boss_4 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 2.400
      ok  lip_engagement [lip_engagement] lip engagement 2.100 vs 2
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2.5 + 2 x 0 vs hole Ø2.75
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap -3.156e-14 mm3 (max 1)
- PASS inside_board: board: 0.3000 mm from the enclosure (need >= 0.2)
- FAIL content_placed_display_1: display_1 (oled_ssd1306_096) is not placed: rpi_zero2w is not a carrier: no relation places it yet (GM2b)
- PASS clear_board: min gap to board 0.3000 mm (need >= 0.2)
- PASS clear_keepout_top: min gap to board_ko_top 0.1000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.3000 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.1000 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.1000 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.1000 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.1000 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 1.4000 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 0.7964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 0.7964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 0.7964 mm (need >= 0)
- PASS clear_board_usb_data_plug: min gap to board_usb_data_plug 0.4000 mm (need >= 0.3)
- PASS clear_board_usb_power_plug: min gap to board_usb_power_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 2 through opening(s), expected 2; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS oversize_board_usb_data_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS oversize_board_usb_power_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_board_usb_data_cut_base: 1.8000 mm of material round board_usb_data_cut toward board_usb_power_cut at y = -2.400 (need >= 1.5)
- PASS ligament_board_usb_power_cut_base: 1.8000 mm of material round board_usb_power_cut toward board_usb_data_cut at y = -2.400 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.5968 mm of material round standoff_1_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.5968 mm of material round standoff_2_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.5968 mm of material round standoff_3_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.5968 mm of material round standoff_4_pilot toward outer at z = -3.355 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 1.9466 mm of material round boss_1_pilot toward outer at z = 11.045 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5966 mm of material round boss_1_lid_hole toward outer at z = 14.800 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 1.9466 mm of material round boss_2_pilot toward outer at z = 11.045 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5966 mm of material round boss_2_lid_hole toward outer at z = 14.800 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 1.9466 mm of material round boss_3_pilot toward outer at z = 11.045 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5966 mm of material round boss_3_lid_hole toward outer at z = 14.800 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 1.9466 mm of material round boss_4_pilot toward outer at z = 11.045 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5966 mm of material round boss_4_lid_hole toward outer at z = 14.800 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 76.04 x 40.94 x 23.60 mm, max 90 x 70 x 45 with X longest
- PASS below_split_board_usb_data_cut: board_usb_data_cut top 6.600 + ligament 1.5 vs split 13.600
- PASS below_split_board_usb_power_cut: board_usb_power_cut top 6.600 + ligament 1.5 vs split 13.600
- PASS bridge_board_usb_data_cut: board_usb_data_cut: flat roof span 10.800 vs bridge limit 15
- PASS bridge_board_usb_power_cut: board_usb_power_cut: flat roof span 10.800 vs bridge limit 15
- PASS pilot_depth_standoff_1: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 6.7 vs standoff 5.200 + floor 2.400 - 0.8
- PASS pilot_depth_boss_1: pilot depth 5.1 vs boss height 21.200 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 5.1 vs boss height 21.200 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 5.1 vs boss height 21.200 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 5.1 vs boss height 21.200 (floor included) - 0.8
- FAIL vent_placed: no vent slot placed: vent: face not resolved (face words only)
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
- PASS pilot_engagement_boss_1: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_boss_1: outside diameter 5.600 vs min_boss_od 5
- PASS pilot_bottoming_boss_1: pilot depth 5.100 vs screw length 6 - clamped plate 2.400
- PASS pilot_engagement_boss_2: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_boss_2: outside diameter 5.600 vs min_boss_od 5
- PASS pilot_bottoming_boss_2: pilot depth 5.100 vs screw length 6 - clamped plate 2.400
- PASS pilot_engagement_boss_3: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_boss_3: outside diameter 5.600 vs min_boss_od 5
- PASS pilot_bottoming_boss_3: pilot depth 5.100 vs screw length 6 - clamped plate 2.400
- PASS pilot_engagement_boss_4: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_boss_4: outside diameter 5.600 vs min_boss_od 5
- PASS pilot_bottoming_boss_4: pilot depth 5.100 vs screw length 6 - clamped plate 2.400
- PASS lip_engagement: lip engagement 2.100 vs 2
- PASS pilot_band_standoff_1: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_standoff_2: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_standoff_3: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_standoff_4: pilot diameter 2.100 vs [2, 2.2] (screw_m2p5_selftap)
- PASS pilot_band_boss_1: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_boss_2: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_boss_3: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_boss_4: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS board_screw_passes_hole: thread 2.5 + 2 x 0 vs hole Ø2.75
- PASS text_coverage: 2 named plug connection(s) covered
