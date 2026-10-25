# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.110  L1.1: The design shall place the Pi Zero 2 W, the fan, the OLED and the encoder from the parts catalogue, with the Pi's two micro-USB ports facing the rear wall, without the parts colliding, and shall declare that layout.
      ok  inside_board [inside] board: 0.6000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.6000 mm (need >= 0.5)
PASS     +0.110  L1.2: The Pi shall rest on four standoffs at its four mounting holes, fixed with screws, inside the case, with its board edges at least 0.5 mm from the side and front walls and the whole Pi, connectors included, at least 0.2 mm inside the cavity.
      ok  inside_board [inside] board: 0.6000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.6000 mm (need >= 0.5)
PASS     -0.000  L1.3: With the lid closed, two micro-USB cable plugs shall plug fully into the Pi's two micro-USB ports through the rear wall at the same time, without touching the case or each other, and each opening shall be no more than 1.5 mm bigger than the plug on any side.
      ok  clear_board_usb_data_plug [clear_of] min gap to board_usb_data_plug 0.4000 mm (need >= 0.3)
      ok  clear_board_usb_power_plug [clear_of] min gap to board_usb_power_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_usb_data_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  oversize_board_usb_power_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 2 named plug connection(s) covered
UNLINKED         L1.4: The fan shall sit above the Pi on four screws through its 32 mm hole pattern, blowing down, with its axis within 6 mm of the Pi board's centre in plan, and at least 5 mm of free air above its inlet and below its exhaust.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.5: The side walls shall have vent slots that give at least 300 square millimetres of open area above the fan's mid-plane for intake and at least 300 square millimetres of open area below the fan for exhaust, with slots 2 to 3 mm wide and at least 1.5 mm of wall between slots, the intake and the exhaust vents each on at least two different walls, and no vent in the front panel, lid or floor. Intake means vents whose area-weighted centre is above the fan's mid-plane, exhaust means at or below the fan's exhaust face, and no vent may straddle the fan's frame between them.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.6: A continuous air path shall exist from the intake vents through the fan to the exhaust vents past the Pi, wide enough for a 5 mm sphere to roll through the inside of the case: from a vent's inner mouth to the centre of the 5 mm air gap above the fan inlet, and from the centre of the 5 mm air gap below the fan exhaust past the Pi to an exhaust vent's inner mouth (the slots themselves are sized by the vent rule).
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.1000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.1000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.5555 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.1000 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.1000 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.1000 mm (need >= 0)
UNLINKED         L1.7: The front panel shall have a window that shows the whole 25 x 14 mm viewing area of the OLED with nothing in the way and that is not oversized (26 to 29 mm wide, 15 to 22 mm tall, its bottom edge 0.4 to 2.0 mm below the viewing area and centred on it in width).  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.8: The OLED shall be fixed behind the window, glass toward the front: by M2 screws into posts at its two header-side holes, and located by pins in its other two holes (those two holes lie only 1.5 mm from the glass edge, too close for a screw post or head), with 3 mm behind the OLED board kept free for header pins and wires, and at least 0.5 mm clear of the fan, the encoder and the Pi.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2 + 2 x 0 vs hole Ø2.75
UNLINKED         L1.9: The encoder shall be mounted through a hole in the front panel with its body behind the panel and its nut and shaft on the outside, with a panel 2 to 3 mm thick at the hole, thin enough for the thread.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: The case shall be a base and a separate lid that locates on the base with a sliding fit and is held closed by snap latches that can flex without breaking (four to eight cantilever hooks, at least two on each of two opposite side walls and at least 20 mm apart along the wall, each engaging a blind catch recess by 0.6 to 1.2 mm with a peak bending strain of at most 1.5 percent).  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.11: The closed case shall have no openings other than the window, the encoder hole, the two USB openings and the vents, and its walls, floor and lid shall be 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.12: The base and the lid shall each be one manifold body that prints on an FDM printer without supports (round holes up to 12 mm, bridges up to 15 mm and a horizontal step up to 1.2 mm deep, such as a hook's return face, are allowed).  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +13.543  L1.13: The closed case shall be no larger than 90 x 70 x 45 mm and shall stand on a desk without tipping.
      ok  bbox [bbox_within] outside 76.47 x 41.37 x 18.50 mm, max 90 x 70 x 45 with X longest
UNLINKED         L1.14: The design shall be delivered as a base STL, a lid STL, the OpenSCAD source, the declared layout and the agent's own clearance report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -1.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 1.532e-15 mm3 (max 1)
      NO  content_placed_display_1 [content_placed] display_1 (oled_ssd1306_096) is not placed: rpi_zero2w is not a carrier: no relation places it yet (GM2b)
      ok  clear_driver_0 [clear_of] min gap to driver_0 1.4000 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 1.0964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 1.0964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 1.0964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 2 through opening(s), expected 2; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_board_usb_data_cut_base [ligament] 1.8000 mm of material round board_usb_data_cut toward board_usb_power_cut at y = -2.700 (need >= 1.5)
      ok  ligament_board_usb_power_cut_base [ligament] 1.8000 mm of material round board_usb_power_cut toward board_usb_data_cut at y = -2.700 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.6969 mm of material round standoff_1_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.6969 mm of material round standoff_2_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.6969 mm of material round standoff_3_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.6969 mm of material round standoff_4_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 1.9466 mm of material round boss_1_pilot toward outer at z = 6.045 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5966 mm of material round boss_1_lid_hole toward outer at z = 9.800 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 1.9466 mm of material round boss_2_pilot toward outer at z = 6.045 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5966 mm of material round boss_2_lid_hole toward outer at z = 9.800 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 1.9466 mm of material round boss_3_pilot toward outer at z = 6.045 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5966 mm of material round boss_3_lid_hole toward outer at z = 9.800 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 1.9466 mm of material round boss_4_pilot toward outer at z = 6.045 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5966 mm of material round boss_4_lid_hole toward outer at z = 9.800 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_board_usb_data_cut [port_below_split] board_usb_data_cut top 6.600 + ligament 1.5 vs split 8.600
      ok  below_split_board_usb_power_cut [port_below_split] board_usb_power_cut top 6.600 + ligament 1.5 vs split 8.600
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 5.1 vs standoff 5.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 5.1 vs standoff 5.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 5.1 vs standoff 5.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 5.1 vs standoff 5.100 + floor 2.400 - 0.8
      ok  pilot_engagement_standoff_1 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_1 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_engagement_standoff_2 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_2 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_engagement_standoff_3 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_3 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_engagement_standoff_4 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_4 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_engagement_boss_1 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_boss_1 [boss_od] outside diameter 5.600 vs min_boss_od 5
      ok  pilot_engagement_boss_2 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_boss_2 [boss_od] outside diameter 5.600 vs min_boss_od 5
      ok  pilot_engagement_boss_3 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_boss_3 [boss_od] outside diameter 5.600 vs min_boss_od 5
      ok  pilot_engagement_boss_4 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_boss_4 [boss_od] outside diameter 5.600 vs min_boss_od 5
      ok  lip_engagement [lip_engagement] lip engagement 2.100 vs 2
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 1.532e-15 mm3 (max 1)
- PASS inside_board: board: 0.6000 mm from the enclosure (need >= 0.5)
- FAIL content_placed_display_1: display_1 (oled_ssd1306_096) is not placed: rpi_zero2w is not a carrier: no relation places it yet (GM2b)
- PASS clear_board: min gap to board 0.6000 mm (need >= 0.5)
- PASS clear_keepout_top: min gap to board_ko_top 0.1000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.1000 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.5555 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.1000 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.1000 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.1000 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 1.4000 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 1.0964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 1.0964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 1.0964 mm (need >= 0)
- PASS clear_board_usb_data_plug: min gap to board_usb_data_plug 0.4000 mm (need >= 0.3)
- PASS clear_board_usb_power_plug: min gap to board_usb_power_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 2 through opening(s), expected 2; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS oversize_board_usb_data_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS oversize_board_usb_power_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_board_usb_data_cut_base: 1.8000 mm of material round board_usb_data_cut toward board_usb_power_cut at y = -2.700 (need >= 1.5)
- PASS ligament_board_usb_power_cut_base: 1.8000 mm of material round board_usb_power_cut toward board_usb_data_cut at y = -2.700 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.6969 mm of material round standoff_1_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.6969 mm of material round standoff_2_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.6969 mm of material round standoff_3_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.6969 mm of material round standoff_4_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 1.9466 mm of material round boss_1_pilot toward outer at z = 6.045 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5966 mm of material round boss_1_lid_hole toward outer at z = 9.800 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 1.9466 mm of material round boss_2_pilot toward outer at z = 6.045 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5966 mm of material round boss_2_lid_hole toward outer at z = 9.800 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 1.9466 mm of material round boss_3_pilot toward outer at z = 6.045 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5966 mm of material round boss_3_lid_hole toward outer at z = 9.800 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 1.9466 mm of material round boss_4_pilot toward outer at z = 6.045 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5966 mm of material round boss_4_lid_hole toward outer at z = 9.800 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 76.47 x 41.37 x 18.50 mm, max 90 x 70 x 45 with X longest
- PASS below_split_board_usb_data_cut: board_usb_data_cut top 6.600 + ligament 1.5 vs split 8.600
- PASS below_split_board_usb_power_cut: board_usb_power_cut top 6.600 + ligament 1.5 vs split 8.600
- PASS pilot_depth_standoff_1: pilot depth 5.1 vs standoff 5.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 5.1 vs standoff 5.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 5.1 vs standoff 5.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 5.1 vs standoff 5.100 + floor 2.400 - 0.8
- PASS pilot_engagement_standoff_1: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_1: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_engagement_standoff_2: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_2: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_engagement_standoff_3: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_3: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_engagement_standoff_4: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_4: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_engagement_boss_1: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_boss_1: outside diameter 5.600 vs min_boss_od 5
- PASS pilot_engagement_boss_2: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_boss_2: outside diameter 5.600 vs min_boss_od 5
- PASS pilot_engagement_boss_3: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_boss_3: outside diameter 5.600 vs min_boss_od 5
- PASS pilot_engagement_boss_4: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_boss_4: outside diameter 5.600 vs min_boss_od 5
- PASS lip_engagement: lip engagement 2.100 vs 2
- PASS pilot_band_standoff_1: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_2: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_3: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_4: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_boss_1: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_boss_2: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_boss_3: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_boss_4: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS board_screw_passes_hole: thread 2 + 2 x 0 vs hole Ø2.75
- PASS text_coverage: 2 named plug connection(s) covered
