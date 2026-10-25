# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.010  L1.1: Take the ESP32-DevKitC from the parts catalogue and orient it with the micro-USB end towards one short end of the box and the antenna end towards the other short end, then declare that layout.
      ok  inside_board [inside] board: 0.5000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.5000 mm (need >= 0.5)
      ok  retention_board [retention] esp32 devkitc held by crush_ribs: free travel (mm) -z 0.00, +z 0.00, -X 0.00, +X 0.00, -Y 0.00, +Y 0.00; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets header_a, keepout component_side, keepout header_pins_a; -X: the hook or arm meets keepout component_side, usb)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 6 ledge(s)
PASS     +0.010  L1.2: Inside the closed box, the 54.4 x 27.9 x 1.6 mm board has at least 0.5 mm clearance from all printed surfaces; the features that hold it (supports, ribs and stops) stay at least 0.2 mm from it, other than where it sits on its supports.
      ok  inside_board [inside] board: 0.5000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 0.5000 mm (need >= 0.5)
UNLINKED         L1.3: Hold the board without screws: at least three supports beneath it (each 4.0 mm2 or larger in plan view, clear of the pin-tail strips, tops level to within 0.10 mm and in contact with the underside); at least two retention ribs across its top at the USB end, one on each long edge, with undersides 0.1 to 0.3 mm over the board top; and stops at all four edges, 0.1 to 0.3 mm from the board edge. The board then moves no more than 1.0 mm lengthways, 0.6 mm sideways or 0.5 mm vertically.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.010  L1.4: With the lid on, keep the box 10.6 mm clear above the board's top surface (8.5 mm header pins and 0.5 mm margin, over the 1.6 mm board) and 3.3 mm clear below the underside (pin tails and 0.3 mm), the only exceptions being the supports under the board and the retention ribs.
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.0000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.0000 mm (need >= 0)
PASS     -0.000  L1.5: With the lid on, a micro-USB plug has to push right into the board's receptacle through one opening in the end wall, at least 0.3 mm clear of the plug all round. The receptacle front sits 0.5 to 3.0 mm back from the inside face of the end wall, the wall around the opening is at least 1.5 mm, and the opening is no more than 1.5 mm larger than the plug per side.
      ok  clear_board_plug [clear_of] min gap to board_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 1 named plug connection(s) covered
UNLINKED         L1.6: No wall, lid or rib may intrude into the 8 mm of free space past the board end at the antenna, or into the volume above the antenna module; the free length beyond the board end must not exceed 12.0 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.7: Make a base and a separate lid that can be removed, which seats on the base with a sliding fit, using a continuous lip with 0.15 to 0.35 mm clearance each side, 1.0 to 2.0 mm of engagement and a thickness of 0.8 mm or more.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.8: Snap hooks on at least two opposite walls keep the lid shut, with undercut engagement of 0.4 mm or more and flex within a 2 percent strain limit; the lid must come off by hand. A hook arm is 1.2 to 2.0 mm thick, 9.0 mm or more in free length and 5.0 mm or more wide, undercut not above 1.0 mm, retention face 45 to 65 degrees and lead-in face 20 to 40 degrees from horizontal, and each hook has to remain engaged when the lid is raised 0.3 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.9: The closed box has a single opening, for the USB, and 2.0 to 4.0 mm thick walls, floor and lid.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: Both base and lid must be single manifold bodies that print on an FDM printer without supports: 45 degree overhang limit, over half of each part's plan area flat on the bed, nothing thinner than 0.8 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.11: The closed box must fit in 75 x 45 x 25 mm and rest flat on a table without tipping.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.12: With the lid removed, the board must drop straight down onto the supports and touch nothing (0.2 mm or more clearance), and the lid must close onto the base with nothing but the snap hooks being forced.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.13: Deliver a base STL, a lid STL, the OpenSCAD source, the declared board layout and the agent's own clearance report; the report must agree with an independent measurement to 0.10 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap -8.281e-14 mm3 (max 1)
      ok  apertures_-X [aperture_count] wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_board_cut_base [ligament] 2.5500 mm of material round board_cut toward floor_top at x = -2.800 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 11.545 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5960 mm of material round boss_1_lid_hole toward outer at z = 16.600 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 11.545 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5960 mm of material round boss_2_lid_hole toward outer at z = 16.600 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 11.545 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5960 mm of material round boss_3_lid_hole toward outer at z = 16.600 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 11.545 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5960 mm of material round boss_4_lid_hole toward outer at z = 16.600 (need >= 1.5)
      ok  rib_interference_cradle_rib_xm_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_xp_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_2 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_ym_3 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_1 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_2 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  rib_interference_cradle_rib_yp_3 [rib_interference] rib depth in the part 0.150 mm (designed 0.15) vs [0.05, 0.3]
      ok  bbox [bbox_within] outside 67.57 x 40.11 x 23.60 mm, max 75 x 45 x 25 with X longest
      ok  below_split_board_cut [port_below_split] board_cut top 6.950 + ligament 1.5 vs split 15.400
      ok  bridge_board_cut [bridge] board_cut: flat roof span 10.800 vs bridge limit 15
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 7.7 vs boss height 21.200 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 7.7 vs boss height 21.200 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 7.7 vs boss height 21.200 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 7.7 vs boss height 21.200 (floor included) - 0.8
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

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap -8.281e-14 mm3 (max 1)
- PASS inside_board: board: 0.5000 mm from the enclosure (need >= 0.5)
- PASS clear_board: min gap to board 0.5000 mm (need >= 0.5)
- PASS clear_keepout_top: min gap to board_ko_top 0.0000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.0000 mm (need >= 0)
- PASS clear_board_plug: min gap to board_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS oversize_board_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_board_cut_base: 2.5500 mm of material round board_cut toward floor_top at x = -2.800 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 11.545 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5960 mm of material round boss_1_lid_hole toward outer at z = 16.600 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 11.545 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5960 mm of material round boss_2_lid_hole toward outer at z = 16.600 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 11.545 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5960 mm of material round boss_3_lid_hole toward outer at z = 16.600 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 11.545 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5960 mm of material round boss_4_lid_hole toward outer at z = 16.600 (need >= 1.5)
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
- PASS bbox: outside 67.57 x 40.11 x 23.60 mm, max 75 x 45 x 25 with X longest
- PASS below_split_board_cut: board_cut top 6.950 + ligament 1.5 vs split 15.400
- PASS bridge_board_cut: board_cut: flat roof span 10.800 vs bridge limit 15
- PASS pilot_depth_boss_1: pilot depth 7.7 vs boss height 21.200 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 7.7 vs boss height 21.200 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 7.7 vs boss height 21.200 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 7.7 vs boss height 21.200 (floor included) - 0.8
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
