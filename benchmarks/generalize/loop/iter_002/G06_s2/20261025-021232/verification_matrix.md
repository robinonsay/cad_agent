# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
FAIL     -1.000  L1.1: The design shall place the LCD module and the Pico 2 from the parts catalogue, with the LCD tilted 30 degrees and the Pico's USB port facing the back wall, without the parts colliding, with the Pico lying partly under the LCD (at least 100 mm2 of overlap seen from above), and shall declare that layout.
      NO  content_placed_module_1 [content_placed] module_1 (rpi_pico2) is not placed: lcd1602_hd44780 is not a carrier: no relation places it yet (GM2b)
UNLINKED         L1.2: The LCD plane shall be tilted 30 degrees from the table with the display facing up and toward the front, and the case's front panel shall be a flat sloped face parallel to the LCD.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.3: The sloped panel shall have a window that shows the whole 64.5 x 14 mm LCD viewport without any material in the way, and that is not oversized (0.5 to 2.0 mm bigger than the viewport on each side).  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.4: The LCD shall be fixed on four standoffs at its four 2.5 mm mounting holes with screws, with its edges at least 0.5 mm clear of the case walls.
      ok  inside_board [inside] board: 0.6000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.6000 mm (need >= 0.5)
FAIL     -1.000  L1.5: The Pico 2 shall be mounted behind and below the LCD on four standoffs at its mounting holes, inside the case, with at least 1.0 mm between the Pico's top side and the back of the LCD module, taking 2.0 mm of soldered components and driver epoxy on the LCD's back across its whole PCB.
      NO  content_placed_module_1 [content_placed] module_1 (rpi_pico2) is not placed: lcd1602_hd44780 is not a carrier: no relation places it yet (GM2b)
FAIL     -1.000  L1.6: With the case closed, a micro-USB cable shall plug fully into the Pico through one opening in the back wall without touching the case, and that opening shall be no more than 1.5 mm bigger than the plug on any side.
      NO  text_coverage [coverage] 0 named plug connection(s) covered; uncovered: module_1.usb takes plug_microusb_b named by L1.6
PASS     +0.110  L1.7: The case shall be a base and a separate removable sloped front panel that locates on the base with a sliding fit and is held closed by two M2 self-tapping screws at its rear corners, each driven along the panel normal into a boss on the base.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2 + 2 x 0 vs hole Ø2.5
UNLINKED         L1.8: The closed case shall have no openings other than the LCD window, the USB opening and screw holes, and its walls, floor and panel shall be 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.9: The base and the panel shall each be one manifold body that prints on an FDM printer without supports.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +9.543  L1.10: The closed case shall be no larger than 100 x 80 x 70 mm and shall stand on a desk without tipping.
      ok  bbox [bbox_within] outside 90.47 x 46.47 x 23.60 mm, max 100 x 80 x 70 with X longest
UNLINKED         L1.11: With the panel off, the LCD and the Pico shall each lift out along a clear path and every board screw shall be reachable with a screwdriver.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.12: The design shall be delivered as a base STL, a panel STL, the OpenSCAD source, the declared layout and the agent's own clearance report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -0.390  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 3.646e-15 mm3 (max 1)
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.6000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.1000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.0964 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0964 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.0964 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.0964 mm (need >= 0)
      ok  clear_driver_0 [clear_of] min gap to driver_0 0.0964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 0.0964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 0.0964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 0.0964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_standoff_1_pilot_base [ligament] 1.6969 mm of material round standoff_1_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.6969 mm of material round standoff_2_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.6969 mm of material round standoff_3_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.6969 mm of material round standoff_4_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 1.9466 mm of material round boss_1_pilot toward outer at z = 13.145 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5966 mm of material round boss_1_lid_hole toward outer at z = 16.900 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 1.9466 mm of material round boss_2_pilot toward outer at z = 13.145 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5966 mm of material round boss_2_lid_hole toward outer at z = 16.900 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 1.9466 mm of material round boss_3_pilot toward outer at z = 13.145 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5966 mm of material round boss_3_lid_hole toward outer at z = 16.900 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 1.9466 mm of material round boss_4_pilot toward outer at z = 13.145 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5966 mm of material round boss_4_lid_hole toward outer at z = 16.900 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      NO  pilot_depth_standoff_1 [pilot_depth] pilot depth 5.1 vs standoff 3.100 + floor 2.400 - 0.8
      NO  pilot_depth_standoff_2 [pilot_depth] pilot depth 5.1 vs standoff 3.100 + floor 2.400 - 0.8
      NO  pilot_depth_standoff_3 [pilot_depth] pilot depth 5.1 vs standoff 3.100 + floor 2.400 - 0.8
      NO  pilot_depth_standoff_4 [pilot_depth] pilot depth 5.1 vs standoff 3.100 + floor 2.400 - 0.8
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

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 3.646e-15 mm3 (max 1)
- PASS inside_board: board: 0.6000 mm from the enclosure (need >= 0.5)
- FAIL content_placed_module_1: module_1 (rpi_pico2) is not placed: lcd1602_hd44780 is not a carrier: no relation places it yet (GM2b)
- PASS clear_board: min gap to board 0.6000 mm (need >= 0.5)
- PASS clear_keepout_top: min gap to board_ko_top 0.6000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.1000 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.0964 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.0964 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.0964 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.0964 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 0.0964 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 0.0964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 0.0964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 0.0964 mm (need >= 0)
- PASS apertures_-X: wall -X: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_standoff_1_pilot_base: 1.6969 mm of material round standoff_1_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.6969 mm of material round standoff_2_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.6969 mm of material round standoff_3_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.6969 mm of material round standoff_4_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 1.9466 mm of material round boss_1_pilot toward outer at z = 13.145 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5966 mm of material round boss_1_lid_hole toward outer at z = 16.900 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 1.9466 mm of material round boss_2_pilot toward outer at z = 13.145 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5966 mm of material round boss_2_lid_hole toward outer at z = 16.900 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 1.9466 mm of material round boss_3_pilot toward outer at z = 13.145 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5966 mm of material round boss_3_lid_hole toward outer at z = 16.900 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 1.9466 mm of material round boss_4_pilot toward outer at z = 13.145 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5966 mm of material round boss_4_lid_hole toward outer at z = 16.900 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 90.47 x 46.47 x 23.60 mm, max 100 x 80 x 70 with X longest
- FAIL pilot_depth_standoff_1: pilot depth 5.1 vs standoff 3.100 + floor 2.400 - 0.8
- FAIL pilot_depth_standoff_2: pilot depth 5.1 vs standoff 3.100 + floor 2.400 - 0.8
- FAIL pilot_depth_standoff_3: pilot depth 5.1 vs standoff 3.100 + floor 2.400 - 0.8
- FAIL pilot_depth_standoff_4: pilot depth 5.1 vs standoff 3.100 + floor 2.400 - 0.8
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
- PASS board_screw_passes_hole: thread 2 + 2 x 0 vs hole Ø2.5
- FAIL text_coverage: 0 named plug connection(s) covered; uncovered: module_1.usb takes plug_microusb_b named by L1.6
