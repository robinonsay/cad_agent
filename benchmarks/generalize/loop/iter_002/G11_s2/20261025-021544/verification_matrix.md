# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.160  L1.1: The design shall place the DC jack, the heatsink and the two capacitors on the 80 x 60 mm board, from the parts catalogue, with the jack facing one short end, without the parts colliding or covering the corner holes, and shall declare that layout.
      ok  inside_contents [inside] contents: 1.1000 mm from the enclosure (need >= 0.2)
      ok  plug_refs_connector_1_1_plug [clear_of] min gap to refs_connector_1_1_plug 1.0000 mm (need >= 0)
      ok  grid_conformance [grid_conformance] worst pin-to-grid residual 0.0000 mm (max 0.15)
PASS     +0.610  L1.2: The 80 x 60 x 1.6 mm board shall fit inside the closed enclosure with at least 0.5 mm clearance to every printed surface, apart from where it rests on its standoffs.
      ok  inside_board [inside] board: 1.1000 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 1.1000 mm (need >= 0.5)
PASS     +0.110  L1.3: The board shall rest on exactly four standoffs, 4 to 10 mm tall, one under each corner hole, each with a pilot hole at least 5 mm deep for an M3 screw through the board, and the declared screws shall bite with at least 4 mm of thread engagement.
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
PASS     +0.110  L1.4: With the lid closed, no printed surface shall come within 0.5 mm of any board part or within 4.0 mm below the board's underside (except the standoffs under the holes), and every part shall lie inside the enclosure.
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.1000 mm (need >= 0)
PASS     -0.000  L1.5: With the lid closed, a 5.5 x 2.1 mm DC plug shall plug fully into the jack through one opening in its end wall without touching the enclosure, and that opening shall be no more than 1.5 mm bigger than the plug on any side.
      ok  clear_connector_1_1_plug [clear_of] min gap to connector_1_1_plug 0.4000 mm (need >= 0.3)
      ok  plug_refs_connector_1_1_plug [clear_of] min gap to refs_connector_1_1_plug 1.0000 mm (need >= 0)
      ok  oversize_connector_1_1_cut [aperture_oversize] opening 11.814 x 11.814 vs plug 11.000 x 11.000: 0.407 mm per side (max 1.5)
      ok  text_coverage [coverage] 1 named plug connection(s) covered
PASS     +0.110  L1.6: The 40 x 40 x 10 mm fan shall sit on the lid's underside blowing into the box, fixed on its 32 mm hole pattern by four M3 screws with at least 3 mm of thread engagement into pilot holes in the lid that leave at least 0.8 mm of skin, over an opening in the lid of at least 60 percent of its 38 mm bore, with its frame at least 5 mm from every board part.
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
UNLINKED         L1.7: Exhaust slots shall line the end wall opposite the jack: at least 8 slots, each 2 to 4 mm wide and at least 10 mm tall, with a total open area of at least 567 mm2.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.8: The enclosure shall be a base and a separate removable lid, a flat plate 4.8 to 6 mm thick with a locating lip that engages the base 2 to 3 mm with a sliding fit, no more than 9 mm tall overall, held closed by four M3 screws into bosses outside the board's outline.
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
UNLINKED         L1.9: The closed enclosure shall have no openings other than the DC opening, the exhaust slots, the fan opening and screw holes, and its walls and floor shall be 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: The base and the lid shall each be one manifold body that prints on an FDM printer without supports.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.11: The closed enclosure shall be no larger than 100 x 80 x 40 mm, longest along the board's 80 mm side, and shall stand flat on a desk without tipping, stable at 5 degrees of table tilt.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.12: With the lid off, the populated board shall drop straight down onto its standoffs and every board screw shall be reachable with a screwdriver.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.13: The design shall be delivered as a base STL, a lid STL, the OpenSCAD source, the declared layout and the agent's own clearance report, and that report shall agree with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap -4.395e-14 mm3 (max 1)
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 1.1000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.0958 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0958 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.0958 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.0958 mm (need >= 0)
      ok  clear_driver_0 [clear_of] min gap to driver_0 0.5964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 0.5964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 0.5964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 0.5964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_connector_1_1_cut_base [ligament] 5.2929 mm of material round connector_1_1_cut toward floor_top at x = -2.300 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.6969 mm of material round standoff_1_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.6969 mm of material round standoff_2_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.6969 mm of material round standoff_3_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.6969 mm of material round standoff_4_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 15.645 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5960 mm of material round boss_1_lid_hole toward outer at z = 19.900 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 15.645 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5960 mm of material round boss_2_lid_hole toward outer at z = 19.900 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 15.645 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5960 mm of material round boss_3_lid_hole toward outer at z = 19.900 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 15.645 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5960 mm of material round boss_4_lid_hole toward outer at z = 19.900 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  bbox [bbox_within] outside 93.17 x 73.17 x 29.20 mm, max 100 x 80 x 40 with X longest
      ok  below_split_connector_1_1_cut [port_below_split] connector_1_1_cut top 11.400 + ligament 1.5 vs split 18.700
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
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
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2 + 2 x 0 vs hole Ø3
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap -4.395e-14 mm3 (max 1)
- PASS inside_board: board: 1.1000 mm from the enclosure (need >= 0.5)
- PASS inside_contents: contents: 1.1000 mm from the enclosure (need >= 0.2)
- PASS clear_board: min gap to board 1.1000 mm (need >= 0.5)
- PASS clear_keepout_top: min gap to board_ko_top 1.1000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.1000 mm (need >= 0)
- PASS clear_hole_ko_0: min gap to hole_ko_0 0.0958 mm (need >= 0)
- PASS clear_hole_ko_1: min gap to hole_ko_1 0.0958 mm (need >= 0)
- PASS clear_hole_ko_2: min gap to hole_ko_2 0.0958 mm (need >= 0)
- PASS clear_hole_ko_3: min gap to hole_ko_3 0.0958 mm (need >= 0)
- PASS clear_driver_0: min gap to driver_0 0.5964 mm (need >= 0)
- PASS clear_driver_1: min gap to driver_1 0.5964 mm (need >= 0)
- PASS clear_driver_2: min gap to driver_2 0.5964 mm (need >= 0)
- PASS clear_driver_3: min gap to driver_3 0.5964 mm (need >= 0)
- PASS clear_connector_1_1_plug: min gap to connector_1_1_plug 0.4000 mm (need >= 0.3)
- PASS plug_refs_connector_1_1_plug: min gap to refs_connector_1_1_plug 1.0000 mm (need >= 0)
- PASS apertures_-X: wall -X: 1 through opening(s), expected 1; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS oversize_connector_1_1_cut: opening 11.814 x 11.814 vs plug 11.000 x 11.000: 0.407 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_connector_1_1_cut_base: 5.2929 mm of material round connector_1_1_cut toward floor_top at x = -2.300 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.6969 mm of material round standoff_1_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.6969 mm of material round standoff_2_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.6969 mm of material round standoff_3_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.6969 mm of material round standoff_4_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 15.645 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5960 mm of material round boss_1_lid_hole toward outer at z = 19.900 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 15.645 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5960 mm of material round boss_2_lid_hole toward outer at z = 19.900 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 15.645 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5960 mm of material round boss_3_lid_hole toward outer at z = 19.900 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 15.645 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5960 mm of material round boss_4_lid_hole toward outer at z = 19.900 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- PASS bbox: outside 93.17 x 73.17 x 29.20 mm, max 100 x 80 x 40 with X longest
- PASS below_split_connector_1_1_cut: connector_1_1_cut top 11.400 + ligament 1.5 vs split 18.700
- PASS pilot_depth_standoff_1: pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 5.1 vs standoff 4.100 + floor 2.400 - 0.8
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
- PASS board_screw_passes_hole: thread 2 + 2 x 0 vs hole Ø3
- PASS grid_conformance: worst pin-to-grid residual 0.0000 mm (max 0.15)
- PASS text_coverage: 1 named plug connection(s) covered
