# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
PASS     +0.160  L1.1: Using catalogue parts, the layout puts the four tactile switches in a 2 x 2 grid with 19.05 mm pitch on the 70 x 50 mm board, with the Pico 2 in female sockets behind them and its USB port pointing at the rear short end. Parts must not collide or cover the corner holes, and the design has to declare this layout.
      ok  inside_contents [inside] contents: ≥ 5.2000 mm from the enclosure (need >= 0.2)
      ok  clear_module_1_1_envelope [inside] module_1_1_envelope: ≥ 5.2000 mm from the enclosure (need >= 0.2)
      ok  grid_conformance [grid_conformance] worst pin-to-grid residual 0.0000 mm (max 0.15)
PASS     +0.958  L1.2: With the enclosure shut, there must be at least 0.5 mm between the 70 x 50 x 1.6 mm board and any printed surface, other than where the board sits on the standoffs.
      ok  inside_board [inside] board: 1.4482 mm from the enclosure (need >= 0.5)
      ok  clear_board [clear_of] min gap to board 1.4482 mm (need >= 0.5)
PASS     +0.010  L1.3: Put the board on precisely four standoffs, one beneath every corner hole. Each has an outside diameter of 5 to 7 mm and a top that is within 0.1 mm of the plane of the other three, and each includes a pilot hole so an M2 self-tapping screw can go through the board.
      ok  pilot_band_standoff_1 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_2 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_3 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  pilot_band_standoff_4 [pilot_band] pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
      ok  board_screw_passes_hole [screw_through_hole] thread 2 + 2 x 0 vs hole Ø2
UNLINKED         L1.4: Keep a 13.3 mm zone above the board's top face and a 4 mm zone beneath its underside free of base and lid material when the lid is closed; only the standoffs below the holes may enter. The Pico, its sockets and the switches need to be inside the enclosure.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  L1.5: A micro-USB cable has to go all the way into the Pico via a single hole in the rear end wall while the lid is on, never touching the enclosure (at least 0.3 mm of space all around). The hole can't be more than 1.5 mm bigger than the plug on any side.
      ok  clear_module_1_1_plug [clear_of] min gap to module_1_1_plug 0.4000 mm (need >= 0.3)
      ok  plug_refs_module_1_1_plug [clear_of] min gap to refs_module_1_1_plug ≥ 5.0000 mm (need >= 0)
      ok  oversize_module_1_1_cut [aperture_oversize] opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
      ok  text_coverage [coverage] 1 named plug connection(s) covered
UNLINKED         L1.6: Every switch gets a dedicated printed plunger that pokes up through a round hole in the top plate, centred on the switch axis within 0.2 mm, leaving 0.4 mm of gap all around between plunger and hole. A plunger's stem is round and 4.0 to 5.6 mm in diameter, and the face at its tip is at least 3.5 mm wide.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.7: Each plunger moves 1.5 mm before it bottoms out; within that travel it must hit the switch's actuation point without crushing the switch, and at the bottom of its stroke it still sticks out of the plate by at least 0.5 mm. When the case is flipped over the plunger stays put, retained by a flange, at least 2 mm wider than the hole, that bears on the plate's underside.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.000  L1.8: Build the enclosure from a base and a detachable lid. The lid is a flat plate that sits down in a rebate cut in the tops of the walls, 2 to 3 mm thick, with a fit gap of 0.15 to 0.35 mm on each side and an upstand of at least 1 mm, and four M3 self-tapping screws hold it down in four bosses on the base.
      ok  pilot_band_boss_1 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_2 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_3 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  pilot_band_boss_4 [pilot_band] pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
      ok  closure_evidence [closure_evidence] closure rebate; the text names rebate (holds; L1.8: "The lid is a flat plate that sits down in a rebate cut in the tops of the walls, 2 to 3 mm thick, with a fit gap of 0.15 to 0.35 mm on each side and an upstand of at least 1 mm, and four M3 self-tapping screws hold it down in four bosses on the base.")
UNLINKED         L1.9: When closed, the only holes allowed are the USB opening, the four plunger holes and the screw holes; walls, floor and lid are to be between 2 and 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: Each of the base, the lid and the plunger should be a single manifold body that an FDM printer can make without supports, meaning overhangs no steeper than 45° from vertical and bridges no longer than 15 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -0.690  L1.11: The shut enclosure needs to fit in 95 x 70 x 35 mm, its longest extent running along the 70 mm side of the board, and it has to sit on a desk without tipping over.
      NO  bbox [bbox_within] outside 92.40 x 58.00 x 35.70 mm, max 95 x 70 x 35 with X longest
UNLINKED         L1.12: Assembly has to work: you insert the plungers into the lid from its underside, lower the populated board vertically onto the standoffs with the lid removed, then close the lid with its plungers over the board, and a screwdriver can get to each screw.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.13: Hand over three STL files (base, lid and plunger), the OpenSCAD source, the declared layout and the agent's own clearance report; an independent measurement has to confirm that report.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     -0.000  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 6.312e-14 mm3 (max 1)
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 1.6000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.6000 mm (need >= 0)
      ok  clear_hole_ko_0 [clear_of] min gap to hole_ko_0 0.0958 mm (need >= 0)
      ok  clear_hole_ko_1 [clear_of] min gap to hole_ko_1 0.0958 mm (need >= 0)
      ok  clear_hole_ko_2 [clear_of] min gap to hole_ko_2 0.0958 mm (need >= 0)
      ok  clear_hole_ko_3 [clear_of] min gap to hole_ko_3 0.0958 mm (need >= 0)
      ok  clear_driver_0 [clear_of] min gap to driver_0 0.5964 mm (need >= 0)
      ok  clear_driver_1 [clear_of] min gap to driver_1 0.5964 mm (need >= 0)
      ok  clear_driver_2 [clear_of] min gap to driver_2 0.5964 mm (need >= 0)
      ok  clear_driver_3 [clear_of] min gap to driver_3 0.5964 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 1 through opening(s), expected 1; 1 blind region(s) ()
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 1 blind region(s) ()
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 1 blind region(s) ()
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 1 blind region(s) ()
      ok  ligament_module_1_1_cut_base [ligament] 12.2000 mm of material round module_1_1_cut toward floor_top at x = -10.000 (need >= 1.5)
      ok  ligament_standoff_1_pilot_base [ligament] 1.6969 mm of material round standoff_1_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_standoff_2_pilot_base [ligament] 1.6969 mm of material round standoff_2_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_standoff_3_pilot_base [ligament] 1.6969 mm of material round standoff_3_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_standoff_4_pilot_base [ligament] 1.6969 mm of material round standoff_4_pilot toward outer at z = -4.155 (need >= 1.5)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 21.845 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 2.1479 mm of material round boss_1_lid_hole toward outer at z = 26.900 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 21.845 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 2.1479 mm of material round boss_2_lid_hole toward outer at z = 26.900 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 21.845 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 2.1479 mm of material round boss_3_lid_hole toward outer at z = 26.900 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 21.845 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 2.1479 mm of material round boss_4_lid_hole toward outer at z = 26.900 (need >= 1.5)
      ok  seated [seated] worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
      ok  below_split_module_1_1_cut [port_below_split] module_1_1_cut top 14.800 + ligament 1.5 vs split 25.700
      ok  bridge_module_1_1_cut [bridge] module_1_1_cut: flat roof span 10.800 vs bridge limit 15
      ok  pilot_depth_standoff_1 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_2 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_3 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_standoff_4 [pilot_depth] pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 7.7 vs boss height 33.300 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 7.7 vs boss height 33.300 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 7.7 vs boss height 33.300 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 7.7 vs boss height 33.300 (floor included) - 0.8
      ok  lid_fit_x [lid_fit] plate 88.900 in rebate 89.400: 0.250 per side
      ok  rebate_upstand_x [rebate_upstand] base 92.400 - rebate 89.400: upstand 1.500
      ok  lid_fit_y [lid_fit] plate 54.500 in rebate 55.000: 0.250 per side
      ok  rebate_upstand_y [rebate_upstand] base 58.000 - rebate 55.000: upstand 1.500
      ok  lid_flush [lid_flush] plate top 28.100 vs upstand top 28.100
      ok  boss_top_plane_boss_1 [boss_top_plane] boss_1 top 25.700 vs rebate floor 25.700
      ok  boss_top_plane_boss_2 [boss_top_plane] boss_2 top 25.700 vs rebate floor 25.700
      ok  boss_top_plane_boss_3 [boss_top_plane] boss_3 top 25.700 vs rebate floor 25.700
      ok  boss_top_plane_boss_4 [boss_top_plane] boss_4 top 25.700 vs rebate floor 25.700
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
```

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 6.312e-14 mm3 (max 1)
- PASS inside_board: board: 1.4482 mm from the enclosure (need >= 0.5)
- PASS inside_contents: contents: ≥ 5.2000 mm from the enclosure (need >= 0.2)
- PASS clear_board: min gap to board 1.4482 mm (need >= 0.5)
- PASS clear_module_1_1_envelope: module_1_1_envelope: ≥ 5.2000 mm from the enclosure (need >= 0.2)
- PASS clear_keepout_top: min gap to board_ko_top 1.6000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.6000 mm (need >= 0)
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
- PASS apertures_-X: wall -X: 1 through opening(s), expected 1; 1 blind region(s) ()
- PASS oversize_module_1_1_cut: opening 10.800 x 7.800 vs plug 10.000 x 7.000: 0.400 mm per side (max 1.5)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 1 blind region(s) ()
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 1 blind region(s) ()
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 1 blind region(s) ()
- PASS ligament_module_1_1_cut_base: 12.2000 mm of material round module_1_1_cut toward floor_top at x = -10.000 (need >= 1.5)
- PASS ligament_standoff_1_pilot_base: 1.6969 mm of material round standoff_1_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_standoff_2_pilot_base: 1.6969 mm of material round standoff_2_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_standoff_3_pilot_base: 1.6969 mm of material round standoff_3_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_standoff_4_pilot_base: 1.6969 mm of material round standoff_4_pilot toward outer at z = -4.155 (need >= 1.5)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 21.845 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 2.1479 mm of material round boss_1_lid_hole toward outer at z = 26.900 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 21.845 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 2.1479 mm of material round boss_2_lid_hole toward outer at z = 26.900 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 21.845 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 2.1479 mm of material round boss_3_lid_hole toward outer at z = 26.900 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 21.845 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 2.1479 mm of material round boss_4_lid_hole toward outer at z = 26.900 (need >= 1.5)
- PASS seated: worst standoff gap 0.0000 mm (max 0.1), worst hole-pilot offset 0.0000 mm (max 0.25)
- FAIL bbox: outside 92.40 x 58.00 x 35.70 mm, max 95 x 70 x 35 with X longest
- PASS below_split_module_1_1_cut: module_1_1_cut top 14.800 + ligament 1.5 vs split 25.700
- PASS bridge_module_1_1_cut: module_1_1_cut: flat roof span 10.800 vs bridge limit 15
- PASS pilot_depth_standoff_1: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_2: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_3: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_standoff_4: pilot depth 5.1 vs standoff 3.600 + floor 2.400 - 0.8
- PASS pilot_depth_boss_1: pilot depth 7.7 vs boss height 33.300 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 7.7 vs boss height 33.300 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 7.7 vs boss height 33.300 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 7.7 vs boss height 33.300 (floor included) - 0.8
- PASS lid_fit_x: plate 88.900 in rebate 89.400: 0.250 per side
- PASS rebate_upstand_x: base 92.400 - rebate 89.400: upstand 1.500
- PASS lid_fit_y: plate 54.500 in rebate 55.000: 0.250 per side
- PASS rebate_upstand_y: base 58.000 - rebate 55.000: upstand 1.500
- PASS lid_flush: plate top 28.100 vs upstand top 28.100
- PASS boss_top_plane_boss_1: boss_1 top 25.700 vs rebate floor 25.700
- PASS boss_top_plane_boss_2: boss_2 top 25.700 vs rebate floor 25.700
- PASS boss_top_plane_boss_3: boss_3 top 25.700 vs rebate floor 25.700
- PASS boss_top_plane_boss_4: boss_4 top 25.700 vs rebate floor 25.700
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
- PASS pilot_band_standoff_1: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_2: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_3: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_standoff_4: pilot diameter 1.700 vs [1.6, 1.8] (screw_m2_selftap)
- PASS pilot_band_boss_1: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_2: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_3: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS pilot_band_boss_4: pilot diameter 2.500 vs [2.4, 2.6] (screw_m3_selftap)
- PASS board_screw_passes_hole: thread 2 + 2 x 0 vs hole Ø2
- PASS grid_conformance: worst pin-to-grid residual 0.0000 mm (max 0.15)
- PASS text_coverage: 1 named plug connection(s) covered
- PASS closure_evidence: closure rebate; the text names rebate (holds; L1.8: "The lid is a flat plate that sits down in a rebate cut in the tops of the walls, 2 to 3 mm thick, with a fit gap of 0.15 to 0.35 mm on each side and an upstand of at least 1 mm, and four M3 self-tapping screws hold it down in four bosses on the base.")
