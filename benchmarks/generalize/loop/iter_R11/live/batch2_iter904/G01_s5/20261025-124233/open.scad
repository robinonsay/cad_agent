// render file: base only (lid off), closed pose; references are translucent ghosts
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 22.15], [0, 1, 0, 9], [0, 0, 1, -5.5], [0, 0, 0, 1]]) difference() { translate([-25.85, -12, 0]) cube([51.7, 24, 15.5]); translate([0, 0, 2.4]) translate([-23.45, -9.6, 0]) cube([46.9, 19.2, 14.1]); }
    // add cradle_support_xm_1 (support)
    multmatrix([[1, 0, 0, -0.125], [0, 1, 0, 9], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.325, -9, 0]) cube([2.65, 18, 5.5]);
    // add cradle_support_xp_1 (support)
    multmatrix([[1, 0, 0, 45.125], [0, 1, 0, 9], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.325, -9, 0]) cube([2.65, 18, 5.5]);
    // add cradle_support_ym_1 (support)
    multmatrix([[1, 0, 0, 1.625], [0, 1, 0, -0.125], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.625, -1.325, 0]) cube([3.25, 2.65, 5.5]);
    // add cradle_support_ym_2 (support)
    multmatrix([[1, 0, 0, 43.375], [0, 1, 0, -0.125], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.625, -1.325, 0]) cube([3.25, 2.65, 5.5]);
    // add cradle_support_yp_1 (support)
    multmatrix([[1, 0, 0, 1.625], [0, 1, 0, 18.125], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.625, -1.325, 0]) cube([3.25, 2.65, 5.5]);
    // add cradle_support_yp_2 (support)
    multmatrix([[1, 0, 0, 43.375], [0, 1, 0, 18.125], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.625, -1.325, 0]) cube([3.25, 2.65, 5.5]);
    // add cradle_rim_xm_1 (rim)
    multmatrix([[1, 0, 0, -0.85], [0, 1, 0, 9], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-0.6, -10.45, 0]) cube([1.2, 20.9, 7.1]);
    // add cradle_rim_xp_1 (rim)
    multmatrix([[1, 0, 0, 45.85], [0, 1, 0, 9], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-0.6, -10.45, 0]) cube([1.2, 20.9, 7.1]);
    // add cradle_rim_ym_1 (rim)
    multmatrix([[1, 0, 0, 1.35], [0, 1, 0, -0.85], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.6, -0.6, 0]) cube([3.2, 1.2, 7.1]);
    // add cradle_rim_ym_2 (rim)
    multmatrix([[1, 0, 0, 43.65], [0, 1, 0, -0.85], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.6, -0.6, 0]) cube([3.2, 1.2, 7.1]);
    // add cradle_rim_yp_1 (rim)
    multmatrix([[1, 0, 0, 1.35], [0, 1, 0, 18.85], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.6, -0.6, 0]) cube([3.2, 1.2, 7.1]);
    // add cradle_rim_yp_2 (rim)
    multmatrix([[1, 0, 0, 43.65], [0, 1, 0, 18.85], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.6, -0.6, 0]) cube([3.2, 1.2, 7.1]);
    // add cradle_rib_xm_1 (crush_rib)
    multmatrix([[1, 0, 0, -0.35], [0, 1, 0, 9], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_xp_1 (crush_rib)
    multmatrix([[1, 0, 0, 45.35], [0, 1, 0, 9], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_ym_1 (crush_rib)
    multmatrix([[1, 0, 0, 1.475], [0, 1, 0, -0.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_ym_2 (crush_rib)
    multmatrix([[1, 0, 0, 43.525], [0, 1, 0, -0.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_yp_1 (crush_rib)
    multmatrix([[1, 0, 0, 1.475], [0, 1, 0, 18.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_yp_2 (crush_rib)
    multmatrix([[1, 0, 0, 43.525], [0, 1, 0, 18.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.487006], [0, 1, 0, -2.787006], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=15.5, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 47.787006], [0, 1, 0, -2.787006], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=15.5, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.487006], [0, 1, 0, 20.787006], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=15.5, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 47.787006], [0, 1, 0, 20.787006], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=15.5, d=6.6, $fn=64);
  }
  // cut board_cut (port_cut)
  multmatrix([[-1, 0, 0, -2.5], [0, -1, 0, 9], [0, 0, 1, -0.85], [0, 0, 0, 1]]) translate([-2.2, -5.9, 0]) cube([4.4, 11.8, 8.8]);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.487006], [0, 1, 0, -2.787006], [0, 0, 1, 2.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 47.787006], [0, 1, 0, -2.787006], [0, 0, 1, 2.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.487006], [0, 1, 0, 20.787006], [0, 0, 1, 2.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 47.787006], [0, 1, 0, 20.787006], [0, 0, 1, 2.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
}

color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([45, 18, 1.6]); multmatrix([[1, 0, 0, -0.7], [0, 1, 0, 5.15], [0, 0, 1, 1.6], [0, 0, 0, 1]]) cube([9, 7.7, 3.9]); multmatrix([[1, 0, 0, 3.45], [0, 1, 0, 0.11], [0, 0, 1, -2.5], [0, 0, 0, 1]]) cube([38.1, 2.54, 2.5]); multmatrix([[1, 0, 0, 3.45], [0, 1, 0, 15.35], [0, 0, 1, -2.5], [0, 0, 0, 1]]) cube([38.1, 2.54, 2.5]); } // ghost board
color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 22.35], [0, 1, 0, 9.05], [0, 0, 1, 9], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=1, d=5.8, $fn=64); multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=8.6, d=5, $fn=64); } // ghost control_1_1
color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 16.35], [0, 1, 0, 9.05], [0, 0, 1, 9], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=1, d=5.8, $fn=64); multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=8.6, d=5, $fn=64); } // ghost control_1_2
color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 28.35], [0, 1, 0, 9.05], [0, 0, 1, 9], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=1, d=5.8, $fn=64); multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=8.6, d=5, $fn=64); } // ghost control_1_3
