# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.610  L1.1: The design shall place the Arduino Uno R3 from the parts catalogue, declare its pose, and put the USB-B receptacle and the DC jack, which are on the same short edge of the board, at the same short end of the case.
      ok  inside_board [inside] board: 1.1000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 1.1000 mm (need >= 0.5)
PASS     +0.610  L1.2: The 68.6 x 53.3 x 1.6 mm board shall fit inside the closed case with at least 0.5 mm clearance to every printed surface, apart from where it rests on its standoffs.
      ok  inside_board [inside] board: 1.1000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 1.1000 mm (need >= 0.5)
PASS     +0.110  L1.3: The board shall rest on exactly four standoffs, one under each of its four mounting holes, each 5 to 7 mm in outside diameter, with its top plane within 0.1 mm of the others and a pilot hole deep enough for a 10 mm M3 self-tapping screw (through the 1.6 mm board) to seat.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 3 + 2 x 0 vs hole Ø3.2
PASS     +0.105  L1.4: With the lid closed, no part of the case shall come within 12 mm above the board's top surface or 4 mm below its underside, except the standoffs under the holes.
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.1000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.6000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.0952 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0952 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.0952 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.0952 mm (need >= 0)
PASS     -0.000  L1.5: With the lid closed, a USB-B plug (metal shell and moulded handle) shall plug fully into the receptacle through one opening in the end wall without touching the case (at least 0.3 mm clear all round), and that opening shall be no more than 1.5 mm bigger than the plug on any side.
      ok  clear_board_usb_plug [clear_of] min gap to board_usb_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_usb_cut [aperture_oversize] opening 16.800 x 13.800 vs plug 16.000 x 13.000: 0.400 mm per side (max 1.5)
      ok  oversize_board_dc_cut [aperture_oversize] opening 11.814 x 11.814 vs plug 11.000 x 11.000: 0.407 mm per side (max 1.5)
      ok  text_coverage [coverage] 2 named plug connection(s) covered
PASS     -0.000  L1.6: With the lid closed, a 5.5 x 2.1 mm DC barrel plug (barrel and moulded handle) shall plug fully into the jack through its own opening in the same end wall, at the same time as the USB plug and without touching the case (at least 0.3 mm clear all round), and that opening shall be no more than 1.5 mm bigger than the plug on any side.
      ok  clear_board_dc_plug [clear_of] min gap to board_dc_plug 0.4000 mm (need >= 0.3)
      ok  oversize_board_dc_cut [aperture_oversize] opening 11.814 x 11.814 vs plug 11.000 x 11.000: 0.407 mm per side (max 1.5)
      ok  text_coverage [coverage] 2 named plug connection(s) covered
UNLINKED         L1.7: The lid shall carry a straight row of 5 to 9 ventilation slots (each 1.5 to 3.0 mm wide and 8 to 12 mm long, 3.5 to 6.5 mm pitch) directly over the ATmega328P, with a total open area of at least 100 mm².  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.8: The case shall be a base and a separate removable lid: a flat plate that drops into a rebate in the top of the walls (plate 2 to 3 mm thick, 0.15 to 0.35 mm fit gap per side, upstand at least 1 mm) and is screwed down with four M3 self-tapping screws into four bosses in the base.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 3 + 2 x 0 vs hole Ø3.2
UNLINKED         L1.9: The closed case shall have no openings other than the USB opening, the DC opening, the vent slots and the screw holes, and its walls, floor and lid shall be 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: The base and the lid shall each be one manifold body that prints on an FDM printer without supports (no overhang steeper than 45° from vertical, no bridge over 15 mm).  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +2.636  L1.11: The closed case shall be no larger than 100 x 70 x 35 mm, longest along the board's 68.6 mm side, and shall stand flat on a desk without tipping.
      ok  bbox [bbox_within] outside 87.77 x 67.37 x 27.60 mm, max 100 x 70 x 35 with X longest
UNLINKED         L1.12: With the lid off, the populated board shall drop straight down onto its standoffs and every board screw shall be reachable with a screwdriver; the lid screws and the board screws shall be separate.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.13: The design shall be delivered as a base STL, a lid STL, the OpenSCAD source, the declared board pose and the agent's own clearance report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 3.197e-14 mm3 (max 1)
      ok  clear_driver_0 [clear_of] min gap to driver_0 1.0964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 1.0964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 1.0964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 1.0964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 2 through opening(s), expected 2; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_board_usb_cut_base [ligament] 1.8000 mm of material round board_usb_cut toward outer at x = -7.800 (need >= 1.5)
      ok  ligament_board_dc_cut_base [ligament] 2.7929 mm of material round board_dc_cut toward outer at x = -7.800 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.7963 mm of material round standoff_1_pilot toward outer at z = -4.255 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.7963 mm of material round standoff_2_pilot toward outer at z = -4.255 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.7963 mm of material round standoff_3_pilot toward outer at z = -4.255 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.7963 mm of material round standoff_4_pilot toward outer at z = -4.255 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 11.945 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5960 mm of material round boss_1_lid_hole toward outer at z = 17.000 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 11.945 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5960 mm of material round boss_2_lid_hole toward outer at z = 17.000 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 11.945 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5960 mm of material round boss_3_lid_hole toward outer at z = 17.000 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 11.945 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5960 mm of material round boss_4_lid_hole toward outer at z = 17.000 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_board_usb_cut [port_below_split] board_usb_cut top 14.000 + ligament 1.5 vs split 15.800
      ok  below_split_board_dc_cut [port_below_split] board_dc_cut top 13.000 + ligament 1.5 vs split 15.800
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
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
      ok  lip_engagement [lip_engagement] lip engagement 2.100 vs 2
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 3.197e-14 mm3 (max 1)
- PASS inside_board: board: 1.1000 mm from the enclosure (need >= 0.5)
- PASS clear_board: min gap to board 1.1000 mm (need >= 0.5)
- PASS clear_keepout_top: min gap to board_ko_top 0.1000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.6000 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.0952 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.0952 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.0952 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.0952 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 1.0964 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 1.0964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 1.0964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 1.0964 mm (need >= 0)
- PASS clear_board_usb_plug: min gap to board_usb_plug 0.4000 mm (need >= 0.3)
- PASS clear_board_dc_plug: min gap to board_dc_plug 0.4000 mm (need >= 0.3)
- PASS apertures_-X: wall -X: 2 through opening(s), expected 2; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS oversize_board_usb_cut: opening 16.800 x 13.800 vs plug 16.000 x 13.000: 0.400 mm per side (max 1.5)
- PASS oversize_board_dc_cut: opening 11.814 x 11.814 vs plug 11.000 x 11.000: 0.407 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_board_usb_cut_base: 1.8000 mm of material round board_usb_cut toward outer at x = -7.800 (need >= 1.5)
- PASS ligament_board_dc_cut_base: 2.7929 mm of material round board_dc_cut toward outer at x = -7.800 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.7963 mm of material round standoff_1_pilot toward outer at z = -4.255 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.7963 mm of material round standoff_2_pilot toward outer at z = -4.255 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.7963 mm of material round standoff_3_pilot toward outer at z = -4.255 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.7963 mm of material round standoff_4_pilot toward outer at z = -4.255 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 11.945 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5960 mm of material round boss_1_lid_hole toward outer at z = 17.000 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 11.945 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5960 mm of material round boss_2_lid_hole toward outer at z = 17.000 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 11.945 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5960 mm of material round boss_3_lid_hole toward outer at z = 17.000 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 11.945 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5960 mm of material round boss_4_lid_hole toward outer at z = 17.000 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 87.77 x 67.37 x 27.60 mm, max 100 x 70 x 35 with X longest
- PASS below_split_board_usb_cut: board_usb_cut top 14.000 + ligament 1.5 vs split 15.800
- PASS below_split_board_dc_cut: board_dc_cut top 13.000 + ligament 1.5 vs split 15.800
- PASS pilot_depth_standoff_1: pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 8.5 vs standoff 7.000 + floor 2.400 - 0.8
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
- PASS lip_engagement: lip engagement 2.100 vs 2
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
