// render file: printed bodies, closed pose; references drawn solid
color("#9bbb59") multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.6], [0, 0, 0, 1]]) cube([80, 60, 1.6]); } // reference board
color("#8064a2") multmatrix([[-1, 0, 0, 14], [0, -1, 0, 34.5], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([14, 9, 11]); } // reference connector_1_1
color("#f79646") multmatrix([[1, 0, 0, 40], [0, 1, 0, 30], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=16, d=10, $fn=64); } // reference generic_1_1
color("#4f81bd") multmatrix([[1, 0, 0, 30], [0, 1, 0, 30], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=16, d=10, $fn=64); } // reference generic_1_2
// body base
difference() {
  color("#4f81bd", 0.3) union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 30], [0, 0, 1, -11], [0, 0, 0, 1]]) difference() { translate([-44, -34, 0]) cube([88, 68, 29.7]); translate([0, 0, 2.4]) translate([-41.6, -31.6, 0]) cube([83.2, 63.2, 28.3]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -11], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -11], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 57.5], [0, 0, 1, -11], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 57.5], [0, 0, 1, -11], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, -11], [0, 0, 0, 1]]) cylinder(h=29.7, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, -3.787006], [0, 0, 1, -11], [0, 0, 0, 1]]) cylinder(h=29.7, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 63.787006], [0, 0, 1, -11], [0, 0, 0, 1]]) cylinder(h=29.7, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, 63.787006], [0, 0, 1, -11], [0, 0, 0, 1]]) cylinder(h=29.7, d=6.6, $fn=64);
  }
  // cut connector_1_1_cut (port_cut)
  multmatrix([[0, 0, -1, -0.6], [0, 1, 0, 30], [1, 0, 0, 5.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=11.814231, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -10.1], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -10.1], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 57.5], [0, 0, 1, -10.1], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 57.5], [0, 0, 1, -10.1], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, -3.787006], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 63.787006], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, 63.787006], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut vent_1 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 4], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_2 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 8], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_3 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 12], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_4 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 16], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_5 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 20], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_6 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 24], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_7 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 28], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_8 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 32], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_9 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 36], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_10 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 40], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_11 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 44], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_12 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 48], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_13 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 52], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
  // cut vent_14 (vent_cut)
  multmatrix([[1, 0, 0, 82.8], [0, 1, 0, 56], [0, 0, 1, -7.1], [0, 0, 0, 1]]) translate([-2.2, -1, 0]) cube([4.4, 2, 24.3]);
}

// body lid
difference() {
  color("#c0504d", 0.3) union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 30], [0, 0, 1, 18.7], [0, 0, 0, 1]]) translate([-44, -34, 0]) cube([88, 68, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 30], [0, 0, 1, 16.6], [0, 0, 0, 1]]) difference() { translate([-41.35, -31.35, 0]) cube([82.7, 62.7, 4.5]); translate([0, 0, -1]) translate([-40.15, -30.15, 0]) cube([80.3, 60.3, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 18.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, -3.787006], [0, 0, 1, 18.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 63.787006], [0, 0, 1, 18.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, 63.787006], [0, 0, 1, 18.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 17.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 15.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, -3.787006], [0, 0, 1, 17.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, -3.787006], [0, 0, 1, 15.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 63.787006], [0, 0, 1, 17.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 63.787006], [0, 0, 1, 15.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, 63.787006], [0, 0, 1, 17.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, 63.787006], [0, 0, 1, 15.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}

