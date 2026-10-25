# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.110  L1.1: The design shall place the Pico 2, the 18650 cell and the slide switch from the parts catalogue, with the Pico above the cell and both lengthwise, the Pico's USB port facing one end, and the switch handle facing one side wall, without the parts colliding, and shall declare that layout.
      ok  inside_board [inside] board: 0.4000 mm from the enclosure (need >= 0.3)
      ok  clear_board [clear_of] min gap to board 0.4000 mm (need >= 0.3)
UNLINKED         L1.2: The 18.6 x 65.2 mm cell shall lie in a cradle inside the closed enclosure without penetrating any printed surface, with 3.0 mm of free space at each end for contacts and 0.3 to 1.0 mm of side clearance at its widest point.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.3: With the door closed, the cell shall be held so that it cannot move more than 1.0 mm sideways or upward, nor more than 4.0 mm along its axis, and it shall rest on the door (within 0.3 mm of its upper face).  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.4: The door shall be a separate body 2.0 to 3.0 mm thick on the bottom of the enclosure that slides along the cell axis with 0.25 to 0.35 mm of clearance per side, leaves through the end opposite the USB, is held closed by a detent (0.3 to 0.8 mm deep) and an end stop, and has a grip (1.0 to 5.0 mm beyond the end wall); the door shall overlap each side wall by at least 1.0 mm along at least 60 percent of its length, and its outer face shall lie 0.3 to 3.0 mm above the base's bottom plane.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.5: With the door removed and the lid on, the cell shall drop straight down out of the cradle through the bottom opening (at least 0.3 mm wider than the cell on each side) without touching anything.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.106  L1.6: The Pico shall be fixed on four posts under its mounting holes, each with a pilot hole for an M2 self-tapping screw, with at least 4.0 mm clear above its top surface and 2.0 mm clear below its underside, at least 0.3 mm from every wall, and with a passage for the cell wires at each end of the cell (a hole at least 4.0 mm across through the shelf, not open to the outside).
      ok  inside_board [inside] board: 0.4000 mm from the enclosure (need >= 0.3)
      ok  clear_board [clear_of] min gap to board 0.4000 mm (need >= 0.3)
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.4000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.4000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.6964 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0964 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.6964 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.0964 mm (need >= 0)
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2 + 2 x 0 vs hole Ø2.1
PASS     -0.000  L1.7: With the lid closed, a micro-USB cable shall plug fully into the Pico through one opening in the end wall staying at least 0.3 mm clear of the plug's envelope, and that opening shall be no more than 1.5 mm bigger than the plug on any side.
      ok  clear_board_plug [clear_of] min gap to board_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 1 named plug connection(s) covered
UNLINKED         L1.8: The slide switch shall be held captive (within 1.0 mm in every direction except toward its wire side) with 5.0 mm of free space behind its terminals, its handle shall pass through a slot in the side wall and move through its full 3.5 mm throw without touching the slot (at least 0.25 mm clearance), the slot shall be no more than 1.0 mm bigger than the handle's swept area, and the handle shall protrude 1.0 to 3.0 mm beyond the wall.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.9: The base and a separate removable lid shall close the top, the lid locating on the base with a lip with a sliding fit and held by two M3 screws into bosses (lid lip clearance 0.15 to 0.35 mm, engagement 2.0 to 3.0 mm, lid plate 2.0 to 3.0 mm, total lid height at most 6.0 mm); with the lid off, the Pico and the switch shall install along their own axes and a screwdriver shall reach each Pico screw and each lid screw.
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
UNLINKED         L1.10: The closed enclosure shall have no openings other than the USB opening, the switch slot, the door seam (gap at most 0.4 mm) and screw holes, with at least 1.0 mm of material round each opening, and its walls, shelf and lid shall be 2.0 to 4.0 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.11: The base, the lid and the door shall each be one manifold body that prints on an FDM printer without supports (at least 25 percent of the base's and 50 percent of the lid's and the door's plan bounding box on the bed).  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +7.119  L1.12: The closed enclosure shall be no larger than 85 x 40 x 40 mm, longest along the cell axis, and shall stand on its base without tipping.
      ok  bbox [bbox_within] outside 64.89 x 32.89 x 16.30 mm, max 85 x 40 x 40 with X longest
UNLINKED         L1.13: The design shall be delivered as the base, lid and door STLs, the OpenSCAD source, the declared layout and the agent's own clearance report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap -6.475e-16 mm3 (max 1)
      ok  clear_driver_0 [clear_of] min gap to driver_0 0.6964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 0.0964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 0.6964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 0.0964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_board_cut_base [ligament] 1.6000 mm of material round board_cut toward outer at x = -2.900 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.6969 mm of material round standoff_1_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.6969 mm of material round standoff_2_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.6969 mm of material round standoff_3_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.6969 mm of material round standoff_4_pilot toward outer at z = -2.555 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 4.045 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5960 mm of material round boss_1_lid_hole toward outer at z = 9.100 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 4.045 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5960 mm of material round boss_2_lid_hole toward outer at z = 9.100 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 4.045 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5960 mm of material round boss_3_lid_hole toward outer at z = 9.100 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 4.045 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5960 mm of material round boss_4_lid_hole toward outer at z = 9.100 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_board_cut [port_below_split] board_cut top 6.300 + ligament 1.5 vs split 7.900
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
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

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap -6.475e-16 mm3 (max 1)
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
- PASS ligament_board_cut_base: 1.6000 mm of material round board_cut toward outer at x = -2.900 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.6969 mm of material round standoff_1_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.6969 mm of material round standoff_2_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.6969 mm of material round standoff_3_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.6969 mm of material round standoff_4_pilot toward outer at z = -2.555 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 4.045 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5960 mm of material round boss_1_lid_hole toward outer at z = 9.100 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 4.045 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5960 mm of material round boss_2_lid_hole toward outer at z = 9.100 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 4.045 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5960 mm of material round boss_3_lid_hole toward outer at z = 9.100 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 4.045 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5960 mm of material round boss_4_lid_hole toward outer at z = 9.100 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 64.89 x 32.89 x 16.30 mm, max 85 x 40 x 40 with X longest
- PASS below_split_board_cut: board_cut top 6.300 + ligament 1.5 vs split 7.900
- PASS pilot_depth_standoff_1: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
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
