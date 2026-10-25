# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
FAIL     -2.880  L1.1: The design shall place the four tactile switches in a 2 x 2 array at 19.05 mm pitch and the Pico 2 on female sockets behind them on the 70 x 50 mm board, from the parts catalogue, with the Pico's USB port facing the rear short end, without the parts colliding or covering the corner holes, and shall declare that layout.
      ok  inside_contents [inside] contents: 0.6000 mm from the enclosure (need >= 0.2)
      ok  clear_module_1_1_envelope [inside] module_1_1_envelope: 0.6000 mm from the enclosure (need >= 0.2)
      NO  grid_conformance [grid_conformance] worst pin-to-grid residual 3.0400 mm (max 0.15); conflict: module_1_1: its pin pattern meets the grid lattice (best 0.000 mm <= 0.15), but no position inside the board's finite hole array reachable from its edge; a catalogue or requirement question
PASS     +0.958  L1.2: The 70 x 50 x 1.6 mm board shall fit inside the closed enclosure with at least 0.5 mm clearance to every printed surface, apart from where it rests on its standoffs.
      ok  inside_board [inside] board: 1.4482 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 1.4482 mm (need >= 0.5)
PASS     +0.010  L1.3: The board shall rest on exactly four standoffs, one under each corner hole, each 5 to 7 mm in outside diameter, with its top plane within 0.1 mm of the others and a pilot hole for an M2 self-tapping screw through the board.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2 + 2 x 0 vs hole Ø2
UNLINKED         L1.4: With the lid closed, no part of the base or the lid shall come within 13.3 mm above the board's top surface or 4 mm below its underside, except the standoffs under the holes, and the Pico, the sockets and the switches shall lie inside the enclosure.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  L1.5: With the lid closed, a micro-USB cable shall plug fully into the Pico through one opening in the rear end wall without touching the enclosure (at least 0.3 mm clear all round), and that opening shall be no more than 1.5 mm bigger than the plug on any side.
      ok  clear_module_1_1_plug [clear_of] min gap to module_1_1_plug 0.4000 mm (need >= 0.3)
      ok  plug_refs_module_1_1_plug [clear_of] min gap to refs_module_1_1_plug ≥ 5.0000 mm (need >= 0)
      ok  oversize_module_1_1_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 1 named plug connection(s) covered
UNLINKED         L1.6: Each switch shall have its own printed plunger that comes up through a round hole in the top plate, coaxial with the switch (within 0.2 mm), with 0.4 mm clearance on every side between plunger and hole; each plunger has a round stem 4.0 to 5.6 mm in diameter and a tip face at least 3.5 mm across.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.7: Each plunger shall have 1.5 mm of travel before it bottoms out, shall reach the switch's actuation point before bottoming without crushing the switch, shall stay proud of the plate by at least 0.5 mm at the end of its travel, and shall stay in the plate when the case is turned over, held by a flange at least 2 mm wider than the hole that rests against the underside of the plate.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.8: The enclosure shall be a base and a separate removable lid, a flat plate that drops into a rebate in the top of the walls (plate 2 to 3 mm thick, 0.15 to 0.35 mm fit gap per side, upstand at least 1 mm) and is screwed down with four M3 self-tapping screws into four bosses in the base.
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
UNLINKED         L1.9: The closed enclosure shall have no openings other than the USB opening, the four plunger holes and screw holes, and its walls, floor and lid shall be 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: The base, the lid and the plunger shall each be one manifold body that prints on an FDM printer without supports (no overhang steeper than 45° from vertical, no bridge over 15 mm).  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -2.290  L1.11: The closed enclosure shall be no larger than 95 x 70 x 35 mm, longest along the board's 70 mm side, and shall stand flat on a desk without tipping.
      NO  bbox [bbox_within] outside 84.17 x 64.47 x 37.30 mm, max 95 x 70 x 35 with X longest
UNLINKED         L1.12: The plungers shall load into the lid from below, the populated board shall drop straight down onto its standoffs with the lid off, the lid with its plungers shall close over the board, and every screw shall be reachable with a screwdriver.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.13: The design shall be delivered as a base STL, a lid STL, a plunger STL, the OpenSCAD source, the declared layout and the agent's own clearance report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -0.390  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 7.194e-14 mm3 (max 1)
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 1.6000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.1000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.0958 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0958 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.0958 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.0958 mm (need >= 0)
      ok  clear_driver_0 [clear_of] min gap to driver_0 0.5964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 0.5964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 0.5964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 0.5964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 1 through opening(s), expected 1; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_module_1_1_cut_base [ligament] 11.7000 mm of material round module_1_1_cut toward floor_top at y = 53.100 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.6969 mm of material round standoff_1_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.6969 mm of material round standoff_2_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.6969 mm of material round standoff_3_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.6969 mm of material round standoff_4_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 24.745 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5960 mm of material round boss_1_lid_hole toward outer at z = 29.000 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 24.745 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5960 mm of material round boss_2_lid_hole toward outer at z = 29.000 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 24.745 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5960 mm of material round boss_3_lid_hole toward outer at z = 29.000 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 24.745 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5960 mm of material round boss_4_lid_hole toward outer at z = 29.000 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_module_1_1_cut [port_below_split] module_1_1_cut top 14.800 + ligament 1.5 vs split 27.800
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
      ok  pilot_engagement_boss_1 [pilot_engagement] pilot depth 6.100 vs min_engagement 6
      ok  boss_od_boss_1 [boss_od] outside diameter 6.600 vs min_boss_od 6
      ok  pilot_engagement_boss_2 [pilot_engagement] pilot depth 6.100 vs min_engagement 6
      ok  boss_od_boss_2 [boss_od] outside diameter 6.600 vs min_boss_od 6
      ok  pilot_engagement_boss_3 [pilot_engagement] pilot depth 6.100 vs min_engagement 6
      ok  boss_od_boss_3 [boss_od] outside diameter 6.600 vs min_boss_od 6
      ok  pilot_engagement_boss_4 [pilot_engagement] pilot depth 6.100 vs min_engagement 6
      ok  boss_od_boss_4 [boss_od] outside diameter 6.600 vs min_boss_od 6
      ok  lip_engagement [lip_engagement] lip engagement 2.100 vs 2
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 7.194e-14 mm3 (max 1)
- PASS inside_board: board: 1.4482 mm from the enclosure (need >= 0.5)
- PASS inside_contents: contents: 0.6000 mm from the enclosure (need >= 0.2)
- PASS clear_board: min gap to board 1.4482 mm (need >= 0.5)
- PASS clear_module_1_1_envelope: module_1_1_envelope: 0.6000 mm from the enclosure (need >= 0.2)
- PASS clear_keepout_top: min gap to board_ko_top 1.6000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.1000 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.0958 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.0958 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.0958 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.0958 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 0.5964 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 0.5964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 0.5964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 0.5964 mm (need >= 0)
- PASS clear_module_1_1_plug: min gap to module_1_1_plug 0.4000 mm (need >= 0.3)
- PASS plug_refs_module_1_1_plug: min gap to refs_module_1_1_plug ≥ 5.0000 mm (need >= 0)
- PASS apertures_-X: wall -X: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS apertures_+Y: wall +Y: 1 through opening(s), expected 1; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS oversize_module_1_1_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS ligament_module_1_1_cut_base: 11.7000 mm of material round module_1_1_cut toward floor_top at y = 53.100 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.6969 mm of material round standoff_1_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.6969 mm of material round standoff_2_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.6969 mm of material round standoff_3_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.6969 mm of material round standoff_4_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 24.745 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5960 mm of material round boss_1_lid_hole toward outer at z = 29.000 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 24.745 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5960 mm of material round boss_2_lid_hole toward outer at z = 29.000 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 24.745 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5960 mm of material round boss_3_lid_hole toward outer at z = 29.000 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 24.745 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5960 mm of material round boss_4_lid_hole toward outer at z = 29.000 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- FAIL bbox: outside 84.17 x 64.47 x 37.30 mm, max 95 x 70 x 35 with X longest
- PASS below_split_module_1_1_cut: module_1_1_cut top 14.800 + ligament 1.5 vs split 27.800
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
- PASS pilot_engagement_boss_1: pilot depth 6.100 vs min_engagement 6
- PASS boss_od_boss_1: outside diameter 6.600 vs min_boss_od 6
- PASS pilot_engagement_boss_2: pilot depth 6.100 vs min_engagement 6
- PASS boss_od_boss_2: outside diameter 6.600 vs min_boss_od 6
- PASS pilot_engagement_boss_3: pilot depth 6.100 vs min_engagement 6
- PASS boss_od_boss_3: outside diameter 6.600 vs min_boss_od 6
- PASS pilot_engagement_boss_4: pilot depth 6.100 vs min_engagement 6
- PASS boss_od_boss_4: outside diameter 6.600 vs min_boss_od 6
- PASS lip_engagement: lip engagement 2.100 vs 2
- PASS pilot_band_standoff_1: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_2: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_3: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_4: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_boss_1: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_2: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_3: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_4: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS board_screw_passes_hole: thread 2 + 2 x 0 vs hole Ø2
- FAIL grid_conformance: worst pin-to-grid residual 3.0400 mm (max 0.15); conflict: module_1_1: its pin pattern meets the grid lattice (best 0.000 mm <= 0.15), but no position inside the board's finite hole array reachable from its edge; a catalogue or requirement question
- PASS text_coverage: 1 named plug connection(s) covered
