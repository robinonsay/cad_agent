// render file: printed bodies, closed pose
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 22.15], [0, 1, 0, 9], [0, 0, 1, -5.5], [0, 0, 0, 1]]) difference() { translate([-25.65, -11.8, 0]) cube([51.3, 23.6, 19.3]); translate([0, 0, 2.4]) translate([-23.25, -9.4, 0]) cube([46.5, 18.8, 17.9]); }
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
    multmatrix([[1, 0, 0, 22.5], [0, 1, 0, -0.85], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-22.75, -0.6, 0]) cube([45.5, 1.2, 7.1]);
    // add cradle_rim_yp_1 (rim)
    multmatrix([[1, 0, 0, 22.5], [0, 1, 0, 18.85], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-22.75, -0.6, 0]) cube([45.5, 1.2, 7.1]);
    // add cradle_rib_xm_1 (crush_rib)
    multmatrix([[1, 0, 0, -0.35], [0, 1, 0, 9], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_xp_1 (crush_rib)
    multmatrix([[1, 0, 0, 45.35], [0, 1, 0, 9], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_ym_1 (crush_rib)
    multmatrix([[1, 0, 0, 7.5], [0, 1, 0, -0.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_ym_2 (crush_rib)
    multmatrix([[1, 0, 0, 22.5], [0, 1, 0, -0.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_ym_3 (crush_rib)
    multmatrix([[1, 0, 0, 37.5], [0, 1, 0, -0.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_yp_1 (crush_rib)
    multmatrix([[1, 0, 0, 7.5], [0, 1, 0, 18.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_yp_2 (crush_rib)
    multmatrix([[1, 0, 0, 22.5], [0, 1, 0, 18.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add cradle_rib_yp_3 (crush_rib)
    multmatrix([[1, 0, 0, 37.5], [0, 1, 0, 18.35], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-0.5, -0.5, 0]) cube([1, 1, 1.6]);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, -2.645584], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=19.3, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, -2.645584], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=19.3, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, 20.645584], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=19.3, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, 20.645584], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=19.3, d=6.6, $fn=64);
  }
  // cut board_cut (port_cut)
  multmatrix([[-1, 0, 0, -2.3], [0, -1, 0, 9], [0, 0, 1, -0.85], [0, 0, 0, 1]]) translate([-2.2, -5.9, 0]) cube([4.4, 11.8, 8.8]);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, -2.645584], [0, 0, 1, 6.1], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, -2.645584], [0, 0, 1, 6.1], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, 20.645584], [0, 0, 1, 6.1], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, 20.645584], [0, 0, 1, 6.1], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
}

// body lid
difference() {
  color("#c0504d") union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 22.15], [0, 1, 0, 9], [0, 0, 1, 13.8], [0, 0, 0, 1]]) translate([-25.65, -11.8, 0]) cube([51.3, 23.6, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 22.15], [0, 1, 0, 9], [0, 0, 1, 11.7], [0, 0, 0, 1]]) difference() { translate([-23, -9.15, 0]) cube([46, 18.3, 4.5]); translate([0, 0, -1]) translate([-21.8, -7.95, 0]) cube([43.6, 15.9, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, -2.645584], [0, 0, 1, 13.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, -2.645584], [0, 0, 1, 13.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, 20.645584], [0, 0, 1, 13.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, 20.645584], [0, 0, 1, 13.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, -2.645584], [0, 0, 1, 12.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, -2.645584], [0, 0, 1, 10.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, -2.645584], [0, 0, 1, 12.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, -2.645584], [0, 0, 1, 10.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, 20.645584], [0, 0, 1, 12.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, 20.645584], [0, 0, 1, 10.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, 20.645584], [0, 0, 1, 12.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, 20.645584], [0, 0, 1, 10.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}

