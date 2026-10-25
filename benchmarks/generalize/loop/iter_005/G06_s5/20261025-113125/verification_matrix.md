# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
FAIL     -1.000  L1.1: Pick the LCD module and the Pico 2 from the parts catalogue and put them in the layout, then declare it. The LCD should lean 30 degrees, the Pico's USB port should point at the rear wall, nothing may collide, and the Pico should tuck partly beneath the LCD, with at least 100 mm2 of overlap when viewed from above.
      NO  content_placed_module_1 [content_placed] module_1 (rpi_pico2) is not placed: lcd1602_hd44780 is not a carrier: no relation places it yet (GM2b)
UNLINKED         L1.2: Seen from the table, the LCD is inclined 30 degrees with its display looking up and toward the front, and the housing's front panel is one flat slanted face that runs parallel to the LCD.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.3: Cut a window in the slanted panel so the whole 64.5 x 14 mm LCD viewport is visible and nothing blocks it, but keep the cutout reasonable: each side should be 0.5 to 2.0 mm bigger than the viewport, no more.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.4: Hold the LCD with screws on four standoffs at its four 2.5 mm mounting holes, and keep its edges at least 0.5 mm off the housing walls.
      ok  inside_board [inside] board: 0.6000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.6000 mm (need >= 0.5)
FAIL     -1.000  L1.5: Put the Pico 2 inside the housing, at the back and underneath the LCD, on four standoffs at its mounting holes. Between the top of the Pico and the back of the LCD module keep a gap of at least 1.0 mm, after allowing 2.0 mm for the soldered parts and driver epoxy on the back of the LCD, which cover its whole PCB.
      NO  content_placed_module_1 [content_placed] module_1 (rpi_pico2) is not placed: lcd1602_hd44780 is not a carrier: no relation places it yet (GM2b)
FAIL     -1.000  L1.6: When the housing is shut, a micro-USB cable has to go all the way into the Pico via a single opening in the rear wall, without rubbing the housing, and that opening may be at most 1.5 mm larger than the plug on any side.
      NO  text_coverage [coverage] 0 named plug connection(s) covered; uncovered: module_1.usb takes plug_microusb_b named by L1.6
PASS     +0.110  L1.7: Make the housing from a base and a separate, removable slanted front panel. The panel sits on the base with a sliding fit and two M2 self-tapping screws at its rear corners keep it closed, each one going along the panel normal into a boss on the base.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2 + 2 x 0 vs hole Ø2.5
UNLINKED         L1.8: Once shut, the housing should have only three kinds of hole: the LCD window, the USB opening and the screw holes. The walls, the floor and the panel should each be 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.9: Both the base and the panel should be a single manifold body, printable on an FDM printer with no supports.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -15.990  L1.10: Keep the shut housing within 100 x 80 x 70 mm, and make sure it sits on a desk without tipping over.
      NO  bbox [bbox_within] outside 86.00 x 54.40 x 24.10 mm, max 70 x 80 x 100
UNLINKED         L1.11: With the panel taken off, you should be able to lift out the LCD and the Pico along clear paths and get a screwdriver to every board screw.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.12: Hand over a base STL, a panel STL, the OpenSCAD source, the declared layout and the agent's own clearance report, and the report has to match an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 2.342e-15 mm3 (max 1)
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.6000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.4531 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.0964 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0964 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.0964 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.0964 mm (need >= 0)
      ok  clear_driver_0 [clear_of] min gap to driver_0 0.0964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 0.0964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 0.0964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 0.0964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 0 through opening(s), expected 0; 0 blind region(s)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 0 blind region(s)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 0 blind region(s)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 0 blind region(s)
      ok  ligament_standoff_1_pilot_base [ligament] 1.6969 mm of material round standoff_1_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.6969 mm of material round standoff_2_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.6969 mm of material round standoff_3_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.6969 mm of material round standoff_4_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 1.9466 mm of material round boss_1_pilot toward outer at z = 13.145 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 3.8986 mm of material round boss_1_lid_hole toward outer at z = 16.900 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 1.9466 mm of material round boss_2_pilot toward outer at z = 13.145 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 3.8986 mm of material round boss_2_lid_hole toward outer at z = 16.900 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 1.9466 mm of material round boss_3_pilot toward outer at z = 13.145 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 3.8986 mm of material round boss_3_lid_hole toward outer at z = 16.900 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 1.9466 mm of material round boss_4_pilot toward outer at z = 13.145 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 3.8986 mm of material round boss_4_lid_hole toward outer at z = 16.900 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 5.1 vs boss height 21.700 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 5.1 vs boss height 21.700 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 5.1 vs boss height 21.700 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 5.1 vs boss height 21.700 (floor included) - 0.8
      ok  pilot_engagement_standoff_1 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_1 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_bottoming_standoff_1 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 1.600
      ok  pilot_engagement_standoff_2 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_2 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_bottoming_standoff_2 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 1.600
      ok  pilot_engagement_standoff_3 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_3 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_bottoming_standoff_3 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 1.600
      ok  pilot_engagement_standoff_4 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_4 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_bottoming_standoff_4 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 1.600
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
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 2.342e-15 mm3 (max 1)
- PASS inside_board: board: 0.6000 mm from the enclosure (need >= 0.5)
- FAIL content_placed_module_1: module_1 (rpi_pico2) is not placed: lcd1602_hd44780 is not a carrier: no relation places it yet (GM2b)
- PASS clear_board: min gap to board 0.6000 mm (need >= 0.5)
- PASS clear_keepout_top: min gap to board_ko_top 0.6000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.4531 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.0964 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.0964 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.0964 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.0964 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 0.0964 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 0.0964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 0.0964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 0.0964 mm (need >= 0)
- PASS apertures_-X: wall -X: 0 through opening(s), expected 0; 0 blind region(s)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 0 blind region(s)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 0 blind region(s)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 0 blind region(s)
- PASS ligament_standoff_1_pilot_base: 1.6969 mm of material round standoff_1_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.6969 mm of material round standoff_2_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.6969 mm of material round standoff_3_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.6969 mm of material round standoff_4_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 1.9466 mm of material round boss_1_pilot toward outer at z = 13.145 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 3.8986 mm of material round boss_1_lid_hole toward outer at z = 16.900 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 1.9466 mm of material round boss_2_pilot toward outer at z = 13.145 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 3.8986 mm of material round boss_2_lid_hole toward outer at z = 16.900 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 1.9466 mm of material round boss_3_pilot toward outer at z = 13.145 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 3.8986 mm of material round boss_3_lid_hole toward outer at z = 16.900 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 1.9466 mm of material round boss_4_pilot toward outer at z = 13.145 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 3.8986 mm of material round boss_4_lid_hole toward outer at z = 16.900 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- FAIL bbox: outside 86.00 x 54.40 x 24.10 mm, max 70 x 80 x 100
- PASS pilot_depth_standoff_1: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_boss_1: pilot depth 5.1 vs boss height 21.700 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 5.1 vs boss height 21.700 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 5.1 vs boss height 21.700 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 5.1 vs boss height 21.700 (floor included) - 0.8
- PASS pilot_engagement_standoff_1: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_1: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_bottoming_standoff_1: pilot depth 5.100 vs screw length 6 - clamped plate 1.600
- PASS pilot_engagement_standoff_2: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_2: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_bottoming_standoff_2: pilot depth 5.100 vs screw length 6 - clamped plate 1.600
- PASS pilot_engagement_standoff_3: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_3: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_bottoming_standoff_3: pilot depth 5.100 vs screw length 6 - clamped plate 1.600
- PASS pilot_engagement_standoff_4: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_4: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_bottoming_standoff_4: pilot depth 5.100 vs screw length 6 - clamped plate 1.600
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
