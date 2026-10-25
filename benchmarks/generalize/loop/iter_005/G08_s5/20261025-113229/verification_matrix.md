# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.110  L1.1: Take the Pico 2, the 18650 cell and the slide switch from the parts catalogue and set them up in a declared layout. The Pico goes over the cell with both running along the length, the Pico's USB port points at one end, the switch handle points at one side wall, and nothing collides.
      ok  inside_board [inside] board: 0.4000 mm from the enclosure (need >= 0.3)
      ok  clear_board [clear_of] min gap to board 0.4000 mm (need >= 0.3)
UNLINKED         L1.2: Inside the closed enclosure the 18.6 x 65.2 mm cell sits in a cradle and does not cut into any printed surface. It needs 3.0 mm of free room at both ends for the contacts and between 0.3 and 1.0 mm of side clearance where it is widest.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.3: With the door shut, the cell may shift no more than 1.0 mm to the side or upward, and no more than 4.0 mm along its axis. It sits on the door, within 0.3 mm of the door's upper face.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.4: The door is its own body on the bottom of the enclosure, 2.0 to 3.0 mm thick, and it slides along the cell axis, 0.25 to 0.35 mm of clearance on each side, coming out at the end away from the USB. A detent (0.3 to 0.8 mm deep) and an end stop hold it shut, and a grip sticks out 1.0 to 5.0 mm beyond the end wall. Along at least 60 percent of its length the door must overlap each side wall by 1.0 mm or more, and its outer face lies 0.3 to 3.0 mm above the bottom plane of the base.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.106  L1.5: If the door is off and the lid is on, the cell has to fall straight down out of the cradle through the bottom opening, without hitting anything. The opening is wider than the cell by at least 0.3 mm on each side.
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.4000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.6964 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0964 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.6964 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.0964 mm (need >= 0)
PASS     +0.110  L1.6: The Pico is fixed on four posts below its mounting holes, each post having a pilot hole for an M2 self-tapping screw. Above the Pico's top surface leave at least 4.0 mm of free space, below its underside 2.0 mm, and keep it at least 0.3 mm from every wall. At each end of the cell there must be a passage for the cell wires, a hole at least 4.0 mm across through the shelf which does not open to the outside.
      ok  inside_board [inside] board: 0.4000 mm from the enclosure (need >= 0.3)
      ok  clear_board [clear_of] min gap to board 0.4000 mm (need >= 0.3)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.4000 mm (need >= 0)
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2 + 2 x 0 vs hole Ø2.1
PASS     -0.000  L1.7: With the lid shut, you must be able to push a micro-USB cable all the way into the Pico via a single opening in an end wall, with at least 0.3 mm between the cable and the plug's envelope. No side of that opening may exceed the plug by more than 1.5 mm.
      ok  clear_board_plug [clear_of] min gap to board_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 1 named plug connection(s) covered
UNLINKED         L1.8: Keep the slide switch captive, within 1.0 mm in every direction other than toward its wire side, and leave 5.0 mm of free room behind its terminals. The handle comes out through a slot in a side wall and moves through its whole 3.5 mm throw while staying at least 0.25 mm from the slot. The slot may be at most 1.0 mm larger than the area the handle sweeps, and the handle should stick out 1.0 to 3.0 mm past the wall.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.9: The top is closed by the base and a separate lid that you can remove. The lid sits on the base with a lip and a sliding fit and is secured by two M3 screws into bosses: lip clearance 0.15 to 0.35 mm, engagement 2.0 to 3.0 mm, lid plate 2.0 to 3.0 mm, and a total lid height of at most 6.0 mm. With the lid removed, the Pico and the switch go in along their own axes, and a screwdriver can get to each Pico screw and each lid screw.
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
UNLINKED         L1.10: When closed, the enclosure may only have the USB opening, the switch slot, the door seam (a gap of no more than 0.4 mm) and the screw holes, and at least 1.0 mm of material must surround every opening. Walls, shelf and lid are 2.0 to 4.0 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.11: Each of the base, the lid and the door is a single manifold body that can be printed on an FDM printer with no supports. On the bed, that means at least 25 percent of the base's plan bounding box and 50 percent of the lid's and the door's.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +7.119  L1.12: The closed enclosure must fit in 85 x 40 x 40 mm, with the long direction along the cell axis, and it has to stand on its base without tipping over.
      ok  bbox [bbox_within] outside 64.89 x 32.89 x 18.40 mm, max 85 x 40 x 40 with X longest
UNLINKED         L1.13: What I get back: base, lid and door STLs, the OpenSCAD source, the declared layout and the agent's own clearance report, with the report agreeing with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap -2.627e-15 mm3 (max 1)
      ok  clear_driver_0 [clear_of] min gap to driver_0 0.6964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 0.0964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 0.6964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 0.0964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_board_cut_base [ligament] 2.1000 mm of material round board_cut toward floor_top at x = -2.900 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.6969 mm of material round standoff_1_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.6969 mm of material round standoff_2_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.6969 mm of material round standoff_3_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.6969 mm of material round standoff_4_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5960 mm of material round boss_1_lid_hole toward outer at z = 11.200 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5960 mm of material round boss_2_lid_hole toward outer at z = 11.200 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5960 mm of material round boss_3_lid_hole toward outer at z = 11.200 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 6.145 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5960 mm of material round boss_4_lid_hole toward outer at z = 11.200 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_board_cut [port_below_split] board_cut top 6.300 + ligament 1.5 vs split 10.000
      ok  bridge_board_cut [bridge] board_cut: flat roof span 10.800 vs bridge limit 15
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 7.7 vs boss height 16.000 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 7.7 vs boss height 16.000 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 7.7 vs boss height 16.000 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 7.7 vs boss height 16.000 (floor included) - 0.8
      ok  pilot_engagement_standoff_1 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_1 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_bottoming_standoff_1 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 1.000
      ok  pilot_engagement_standoff_2 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_2 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_bottoming_standoff_2 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 1.000
      ok  pilot_engagement_standoff_3 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_3 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_bottoming_standoff_3 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 1.000
      ok  pilot_engagement_standoff_4 [pilot_engagement] pilot depth 5.100 vs min_engagement 5
      ok  boss_od_standoff_4 [boss_od] outside diameter 5.100 vs min_boss_od 5
      ok  pilot_bottoming_standoff_4 [pilot_bottoming] pilot depth 5.100 vs screw length 6 - clamped plate 1.000
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

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap -2.627e-15 mm3 (max 1)
- PASS inside_board: board: 0.4000 mm from the enclosure (need >= 0.3)
- PASS clear_board: min gap to board 0.4000 mm (need >= 0.3)
- PASS clear_keepout_top: min gap to board_ko_top 0.4000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.4000 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.6964 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.0964 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.6964 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.0964 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 0.6964 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 0.0964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 0.6964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 0.0964 mm (need >= 0)
- PASS clear_board_plug: min gap to board_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS oversize_board_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_board_cut_base: 2.1000 mm of material round board_cut toward floor_top at x = -2.900 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.6969 mm of material round standoff_1_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.6969 mm of material round standoff_2_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.6969 mm of material round standoff_3_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.6969 mm of material round standoff_4_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5960 mm of material round boss_1_lid_hole toward outer at z = 11.200 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5960 mm of material round boss_2_lid_hole toward outer at z = 11.200 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5960 mm of material round boss_3_lid_hole toward outer at z = 11.200 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 6.145 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5960 mm of material round boss_4_lid_hole toward outer at z = 11.200 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 64.89 x 32.89 x 18.40 mm, max 85 x 40 x 40 with X longest
- PASS below_split_board_cut: board_cut top 6.300 + ligament 1.5 vs split 10.000
- PASS bridge_board_cut: board_cut: flat roof span 10.800 vs bridge limit 15
- PASS pilot_depth_standoff_1: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_boss_1: pilot depth 7.7 vs boss height 16.000 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 7.7 vs boss height 16.000 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 7.7 vs boss height 16.000 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 7.7 vs boss height 16.000 (floor included) - 0.8
- PASS pilot_engagement_standoff_1: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_1: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_bottoming_standoff_1: pilot depth 5.100 vs screw length 6 - clamped plate 1.000
- PASS pilot_engagement_standoff_2: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_2: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_bottoming_standoff_2: pilot depth 5.100 vs screw length 6 - clamped plate 1.000
- PASS pilot_engagement_standoff_3: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_3: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_bottoming_standoff_3: pilot depth 5.100 vs screw length 6 - clamped plate 1.000
- PASS pilot_engagement_standoff_4: pilot depth 5.100 vs min_engagement 5
- PASS boss_od_standoff_4: outside diameter 5.100 vs min_boss_od 5
- PASS pilot_bottoming_standoff_4: pilot depth 5.100 vs screw length 6 - clamped plate 1.000
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
- PASS pilot_band_standoff_1: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_2: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_3: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_4: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_boss_1: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_2: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_3: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_4: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS board_screw_passes_hole: thread 2 + 2 x 0 vs hole Ø2.1
- PASS text_coverage: 1 named plug connection(s) covered
