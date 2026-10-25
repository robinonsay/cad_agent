// render file: printed bodies, closed pose; references drawn solid
color("#9bbb59") multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([54.4, 27.9, 1.6]); multmatrix([[1, 0, 0, -1], [0, 1, 0, 10.2], [0, 0, 1, 1.6], [0, 0, 0, 1]]) cube([5.9, 7.5, 2.9]); multmatrix([[1, 0, 0, 28.9], [0, 1, 0, 4.95], [0, 0, 1, 1.6], [0, 0, 0, 1]]) cube([25.5, 18, 3.1]); multmatrix([[1, 0, 0, 3.07], [0, 1, 0, -0.02], [0, 0, 1, 1.6], [0, 0, 0, 1]]) cube([48.26, 2.54, 2.5]); multmatrix([[1, 0, 0, 3.07], [0, 1, 0, 25.38], [0, 0, 1, 1.6], [0, 0, 0, 1]]) cube([48.26, 2.54, 2.5]); } // reference board
color("#8064a2") multmatrix([[1, 0, 0, 26.55], [0, 1, 0, 14.03], [0, 0, 1, 14], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=1, d=5.8, $fn=64); multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=8.6, d=5, $fn=64); } // reference control_1_1
color("#f79646") multmatrix([[1, 0, 0, 32.55], [0, 1, 0, 14.03], [0, 0, 1, 14], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=1, d=5.8, $fn=64); multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=8.6, d=5, $fn=64); } // reference control_1_2
color("#4f81bd") multmatrix([[1, 0, 0, 26.55], [0, 1, 0, 8.03], [0, 0, 1, 14], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=1, d=5.8, $fn=64); multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=8.6, d=5, $fn=64); } // reference control_1_3
// body base
difference() {
  color("#4f81bd", 0.3) union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 26.7], [0, 1, 0, 13.95], [0, 0, 1, -5.5], [0, 0, 0, 1]]) difference() { translate([-33.2, -19.47, 0]) cube([66.4, 38.94, 20.5]); translate([0, 0, 2.4]) translate([-30.8, -17.07, 0]) cube([61.6, 34.14, 19.1]); }
    // add cradle_support_xm_1 (support)
    multmatrix([[1, 0, 0, -0.125], [0, 1, 0, 13.95], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.325, -13.95, 0]) cube([2.65, 27.9, 5.5]);
    // add cradle_support_xp_1 (support)
    multmatrix([[1, 0, 0, 54.525], [0, 1, 0, 13.95], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.325, -13.95, 0]) cube([2.65, 27.9, 5.5]);
    // add cradle_support_ym_1 (support)
    multmatrix([[1, 0, 0, 1.535], [0, 1, 0, -0.125], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.535, -1.325, 0]) cube([3.07, 2.65, 5.5]);
    // add cradle_support_ym_2 (support)
    multmatrix([[1, 0, 0, 52.865], [0, 1, 0, -0.125], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.535, -1.325, 0]) cube([3.07, 2.65, 5.5]);
    // add cradle_support_yp_1 (support)
    multmatrix([[1, 0, 0, 1.535], [0, 1, 0, 28.025], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.535, -1.325, 0]) cube([3.07, 2.65, 5.5]);
    // add cradle_support_yp_2 (support)
    multmatrix([[1, 0, 0, 52.865], [0, 1, 0, 28.025], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.535, -1.325, 0]) cube([3.07, 2.65, 5.5]);
    // add cradle_rim_xm_1 (rim)
    multmatrix([[1, 0, 0, -0.85], [0, 1, 0, 13.95], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-0.6, -15.4, 0]) cube([1.2, 30.8, 7.1]);
    // add cradle_rim_xp_1 (rim)
    multmatrix([[1, 0, 0, 55.25], [0, 1, 0, 13.95], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-0.6, -15.4, 0]) cube([1.2, 30.8, 7.1]);
    // add cradle_rim_ym_1 (rim)
    multmatrix([[1, 0, 0, 27.2], [0, 1, 0, -0.85], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-27.45, -0.6, 0]) cube([54.9, 1.2, 7.1]);
    // add cradle_rim_yp_1 (rim)
    multmatrix([[1, 0, 0, 27.2], [0, 1, 0, 28.75], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-27.45, -0.6, 0]) cube([54.9, 1.2, 7.1]);
    // add cradle_rib_xm_1 (crush_rib)
    multmatrix([[1, 0, 0, -0.35], [0, 1, 0, 13.95], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_xp_1 (crush_rib)
    multmatrix([[1, 0, 0, 54.75], [0, 1, 0, 13.95], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_ym_1 (crush_rib)
    multmatrix([[1, 0, 0, 9.066667], [0, 1, 0, -0.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_ym_2 (crush_rib)
    multmatrix([[1, 0, 0, 27.2], [0, 1, 0, -0.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_ym_3 (crush_rib)
    multmatrix([[1, 0, 0, 45.333333], [0, 1, 0, -0.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_yp_1 (crush_rib)
    multmatrix([[1, 0, 0, 9.066667], [0, 1, 0, 28.25], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_yp_2 (crush_rib)
    multmatrix([[1, 0, 0, 27.2], [0, 1, 0, 28.25], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_yp_3 (crush_rib)
    multmatrix([[1, 0, 0, 45.333333], [0, 1, 0, 28.25], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, -4.574773], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=20.5, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, -4.574773], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=20.5, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, 32.474773], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=20.5, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, 32.474773], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=20.5, d=6.6, $fn=64);
  }
  // cut board_cut (port_cut)
  multmatrix([[-1, 0, 0, -5.3], [0, -1, 0, 13.95], [0, 0, 1, -0.85], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, -4.574773], [0, 0, 1, 7.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, -4.574773], [0, 0, 1, 7.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, 32.474773], [0, 0, 1, 7.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, 32.474773], [0, 0, 1, 7.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
}

// body lid
difference() {
  color("#c0504d", 0.3) union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 26.7], [0, 1, 0, 13.95], [0, 0, 1, 15], [0, 0, 0, 1]]) translate([-33.2, -19.47, 0]) cube([66.4, 38.94, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 26.7], [0, 1, 0, 13.95], [0, 0, 1, 12.9], [0, 0, 0, 1]]) difference() { translate([-30.55, -16.82, 0]) cube([61.1, 33.64, 4.5]); translate([0, 0, -1]) translate([-29.35, -15.62, 0]) cube([58.7, 31.24, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, -4.574773], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, -4.574773], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, 32.474773], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, 32.474773], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, -4.574773], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, -4.574773], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, -4.574773], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, -4.574773], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, 32.474773], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, 32.474773], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, 32.474773], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, 32.474773], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut control_1_1_panel_hole (panel_hole)
  multmatrix([[1, 0, 0, 26.55], [0, 1, 0, 14.03], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=5.506633, $fn=64);
  // cut control_1_2_panel_hole (panel_hole)
  multmatrix([[1, 0, 0, 32.55], [0, 1, 0, 14.03], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=5.506633, $fn=64);
  // cut control_1_3_panel_hole (panel_hole)
  multmatrix([[1, 0, 0, 26.55], [0, 1, 0, 8.03], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=5.506633, $fn=64);
}

