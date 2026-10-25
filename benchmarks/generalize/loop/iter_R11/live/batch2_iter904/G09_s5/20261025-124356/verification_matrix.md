# Verification matrix (delivered STLs)

Each requirement row lists the rule-derived checks traced to it (spec-number provenance and the catalogue parts it names); UNLINKED rows have no traced check yet (M10).

```
FAIL     -1.000  L1.1: From the parts catalogue place the battery, the toggle switch, the DC jack and the hinge pin, declare the layout, and keep everything from colliding. The battery lies along the long axis of the box, the jack faces one short end, and the switch is on the top face of the lid.
      NO  content_placed_connector_1 [content_placed] connector_1 (dc_jack_pj002a) is not placed: battery_9v_pp3 is not a carrier: no relation places it yet (GM2b)
      ok  panel_keepouts_control_1_1 [clear_of] min gap to control_1_1_keepouts 2.6000 mm (need >= 0)
      ok  panel_clear_control_1_1 [clear_of] min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_1 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_1 [panel_seated] lid underside 70.900 vs contact plane 70.900 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_1 [panel_hole] hole Ø6.500 for Ø6 (0.250 per side)
      ok  panel_thickness_control_1_1 [panel_thickness] lid 2.400 mm vs max_panel_thickness 4
PASS     +0.010  L1.2: The battery (26.5 x 17.5 x 48.5 mm) goes in a pocket that keeps at least 0.2 mm from all printed surfaces, other than where it rests on its floor, with a gap of no more than 0.5 mm on its two long sides and its top. The snap-clip zone at the terminal end must be inside the closed box.
      ok  inside_board [inside] board: 0.2000 mm from the enclosure (need >= 0.2)
      ok  clear_board [clear_of] min gap to board 0.2000 mm (need >= 0.2)
UNLINKED         L1.3: When the lid is shut the battery is held so that it shifts at most 1.0 mm in total across its width and thickness, and lengthwise no further than its clip zone plus 1.5 mm. There is a printed stop at the end away from the terminals.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
PASS     +0.110  L1.4: Pass the toggle switch through a hole in the lid plate (2 to 4 mm thick, hole 0.2 to 0.8 mm larger than the bushing) with the switch seated against the underside of the plate. Neither the mounting nut nor the swing of the lever may hit any printed surface, and the switch body and solder lugs must stay clear of the box.
      ok  panel_keepouts_control_1_1 [clear_of] min gap to control_1_1_keepouts 2.6000 mm (need >= 0)
      ok  panel_clear_control_1_1 [clear_of] min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
      ok  panel_board_control_1_1 [clear_of] min gap to board ≥ 5.2000 mm (need >= 0.2)
      ok  panel_seated_control_1_1 [panel_seated] lid underside 70.900 vs contact plane 70.900 (gap 0.0000, max 0.1)
      ok  panel_hole_control_1_1 [panel_hole] hole Ø6.500 for Ø6 (0.250 per side)
      ok  panel_thickness_control_1_1 [panel_thickness] lid 2.400 mm vs max_panel_thickness 4
FAIL     -1.000  L1.5: With the lid shut, a 5.5 x 2.1 mm DC plug with an 11 mm dia handle must slide fully into the jack through a single opening in the end wall and never touch the box. The opening may exceed the plug by at most 1.5 mm on any side, and the jack must be held in place.
      NO  text_coverage [coverage] 0 named plug connection(s) covered; uncovered: connector_1.dc_in takes plug_dc_barrel_5p5 named by request, request, L1.5
FAIL     -1.000  L1.6: The lid pivots on a 3 mm steel dowel pin, 24 mm long, which stays captive in the hinge bores (a press fit in one part and a clearance fit in the other). The lid has to swing to 100 degrees without any part of the lid or the switch hitting the base, the battery or the jack.
      NO  content_placed_mech_1 [content_placed] mech_1 (dowel_pin_generic) is not placed: battery_9v_pp3 is not a carrier: no relation places it yet (GM2b)
UNLINKED         L1.7: Keep the lid shut with a snap latch on the side across from the hinge, a cantilever hook with at least 8 mm free length, 1.2 to 2.5 mm thick, 0.4 to 1.2 mm catch overlap and strain of at most 2 percent. The lid is a flat plate with a locating lip that doesn't fuse to the base and leaves a seam of no more than 0.5 mm.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.8: The shut box has no openings except the switch hole, the jack opening, the hinge bores and the seam, and its walls, floor and lid plate measure 2 to 4 mm thick.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.9: The base and the lid must each be a single manifold body, printable on an FDM printer with no supports.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.10: The shut box has to fit within 90 x 45 x 30 mm (leaving out the switch lever) and sit flat on a desk without tipping.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.11: With the lid swung open, the battery and its snap clip should drop straight down into the pocket and lift straight back out, without touching the lid, the switch, the jack or the base.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
UNLINKED         L1.12: Deliver a base STL, a lid STL, the OpenSCAD source, the declared layout and the agent's own clearance report, where the report agrees with an independent measurement.  (no rule-derived check is traced to this requirement yet (translation to checks is milestone M10))
FAIL     -48.790  rules: rule-derived checks with no L1 link (generic consequences of the contents, the spec and printing)
      ok  separable [separable] shells {'base': 1, 'lid': 1}, worst overlap 8.648e-16 mm3 (max 1)
      ok  clear_keepout_top [clear_of] min gap to board_ko_top 0.3000 mm (need >= 0)
      ok  clear_keepout_bottom [clear_of] min gap to board_ko_bot 0.0000 mm (need >= 0)
      ok  apertures_-X [aperture_count] wall -X: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
      ok  apertures_+X [aperture_count] wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  apertures_-Y [aperture_count] wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
      ok  apertures_+Y [aperture_count] wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
      ok  ligament_boss_1_pilot_base [ligament] 2.0460 mm of material round boss_1_pilot toward outer at z = 67.045 (need >= 1.5)
      ok  ligament_boss_1_lid_hole_lid [ligament] 1.5960 mm of material round boss_1_lid_hole toward outer at z = 72.100 (need >= 1.5)
      ok  ligament_boss_2_pilot_base [ligament] 2.0460 mm of material round boss_2_pilot toward outer at z = 67.045 (need >= 1.5)
      ok  ligament_boss_2_lid_hole_lid [ligament] 1.5960 mm of material round boss_2_lid_hole toward outer at z = 72.100 (need >= 1.5)
      ok  ligament_boss_3_pilot_base [ligament] 2.0460 mm of material round boss_3_pilot toward outer at z = 67.045 (need >= 1.5)
      ok  ligament_boss_3_lid_hole_lid [ligament] 1.5960 mm of material round boss_3_lid_hole toward outer at z = 72.100 (need >= 1.5)
      ok  ligament_boss_4_pilot_base [ligament] 2.0460 mm of material round boss_4_pilot toward outer at z = 67.045 (need >= 1.5)
      ok  ligament_boss_4_lid_hole_lid [ligament] 1.5960 mm of material round boss_4_lid_hole toward outer at z = 72.100 (need >= 1.5)
      NO  retention_board [retention] 9v battery held by pocket: free travel (mm) -z 0.00, +z 22.40, -X 0.25, +X 0.25, -Y 0.25, +Y 0.25; worst +z 22.40 > 0.5; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets keepout clip_zone; -X: the hook or arm meets keepout clip_zone)
      ok  supported [supported] worst ledge gap 0.0000 mm (max 0.1) over 4 ledge(s)
      NO  bbox [bbox_within] outside 38.25 x 29.25 x 78.80 mm, max 90 x 45 x 30 with X longest
      ok  pilot_depth_boss_1 [pilot_depth] pilot depth 7.7 vs boss height 76.400 (floor included) - 0.8
      ok  pilot_depth_boss_2 [pilot_depth] pilot depth 7.7 vs boss height 76.400 (floor included) - 0.8
      ok  pilot_depth_boss_3 [pilot_depth] pilot depth 7.7 vs boss height 76.400 (floor included) - 0.8
      ok  pilot_depth_boss_4 [pilot_depth] pilot depth 7.7 vs boss height 76.400 (floor included) - 0.8
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

- PASS separable: shells {'base': 1, 'lid': 1}, worst overlap 8.648e-16 mm3 (max 1)
- PASS inside_board: board: 0.2000 mm from the enclosure (need >= 0.2)
- FAIL content_placed_connector_1: connector_1 (dc_jack_pj002a) is not placed: battery_9v_pp3 is not a carrier: no relation places it yet (GM2b)
- FAIL content_placed_mech_1: mech_1 (dowel_pin_generic) is not placed: battery_9v_pp3 is not a carrier: no relation places it yet (GM2b)
- PASS clear_board: min gap to board 0.2000 mm (need >= 0.2)
- PASS clear_keepout_top: min gap to board_ko_top 0.3000 mm (need >= 0)
- PASS clear_keepout_bottom: min gap to board_ko_bot 0.0000 mm (need >= 0)
- PASS apertures_-X: wall -X: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_3_lid_hole, boss_3_pilot)
- PASS apertures_+X: wall +X: 0 through opening(s), expected 0; 2 blind region(s) (boss_2_lid_hole, boss_2_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS apertures_-Y: wall -Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_1_lid_hole, boss_1_pilot, boss_2_lid_hole, boss_2_pilot)
- PASS apertures_+Y: wall +Y: 0 through opening(s), expected 0; 2 blind region(s) (boss_3_lid_hole, boss_3_pilot, boss_4_lid_hole, boss_4_pilot)
- PASS ligament_boss_1_pilot_base: 2.0460 mm of material round boss_1_pilot toward outer at z = 67.045 (need >= 1.5)
- PASS ligament_boss_1_lid_hole_lid: 1.5960 mm of material round boss_1_lid_hole toward outer at z = 72.100 (need >= 1.5)
- PASS ligament_boss_2_pilot_base: 2.0460 mm of material round boss_2_pilot toward outer at z = 67.045 (need >= 1.5)
- PASS ligament_boss_2_lid_hole_lid: 1.5960 mm of material round boss_2_lid_hole toward outer at z = 72.100 (need >= 1.5)
- PASS ligament_boss_3_pilot_base: 2.0460 mm of material round boss_3_pilot toward outer at z = 67.045 (need >= 1.5)
- PASS ligament_boss_3_lid_hole_lid: 1.5960 mm of material round boss_3_lid_hole toward outer at z = 72.100 (need >= 1.5)
- PASS ligament_boss_4_pilot_base: 2.0460 mm of material round boss_4_pilot toward outer at z = 67.045 (need >= 1.5)
- PASS ligament_boss_4_lid_hole_lid: 1.5960 mm of material round boss_4_lid_hole toward outer at z = 72.100 (need >= 1.5)
- FAIL retention_board: 9v battery held by pocket: free travel (mm) -z 0.00, +z 22.40, -X 0.25, +X 0.25, -Y 0.25, +Y 0.25; worst +z 22.40 > 0.5; options the plant cannot build here: snap_clips (no pair of opposite sides takes a snap clip: -Y: the hook or arm meets keepout clip_zone; -X: the hook or arm meets keepout clip_zone)
- PASS supported: worst ledge gap 0.0000 mm (max 0.1) over 4 ledge(s)
- FAIL bbox: outside 38.25 x 29.25 x 78.80 mm, max 90 x 45 x 30 with X longest
- PASS pilot_depth_boss_1: pilot depth 7.7 vs boss height 76.400 (floor included) - 0.8
- PASS pilot_depth_boss_2: pilot depth 7.7 vs boss height 76.400 (floor included) - 0.8
- PASS pilot_depth_boss_3: pilot depth 7.7 vs boss height 76.400 (floor included) - 0.8
- PASS pilot_depth_boss_4: pilot depth 7.7 vs boss height 76.400 (floor included) - 0.8
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
- PASS panel_keepouts_control_1_1: min gap to control_1_1_keepouts 2.6000 mm (need >= 0)
- PASS panel_clear_control_1_1: min gap to control_1_1_ref 0.4000 mm (need >= 0.2)
- PASS panel_board_control_1_1: min gap to board ≥ 5.2000 mm (need >= 0.2)
- PASS panel_seated_control_1_1: lid underside 70.900 vs contact plane 70.900 (gap 0.0000, max 0.1)
- PASS panel_hole_control_1_1: hole Ø6.500 for Ø6 (0.250 per side)
- PASS panel_thickness_control_1_1: lid 2.400 mm vs max_panel_thickness 4
- FAIL text_coverage: 0 named plug connection(s) covered; uncovered: connector_1.dc_in takes plug_dc_barrel_5p5 named by request, request, L1.5
