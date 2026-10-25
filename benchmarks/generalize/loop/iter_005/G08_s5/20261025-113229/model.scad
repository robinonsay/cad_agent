// assembly: printed bodies in the closed pose; references are % ghosts (never printed)
color("#4f81bd") {
  // body base
  difference() {
    union() {
      // body base (tray)
      multmatrix([[1, 0, 0, 25.2], [0, 1, 0, 10.5], [0, 0, 1, -6], [0, 0, 0, 1]]) difference() { translate([-29.3, -13.3, 0]) cube([58.6, 26.6, 16]); translate([0, 0, 2.4]) translate([-26.9, -10.9, 0]) cube([53.8, 21.8, 14.6]); }
      // add standoff_1 (standoff)
      multmatrix([[1, 0, 0, 2], [0, 1, 0, 4.8], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
      // add standoff_2 (standoff)
      multmatrix([[1, 0, 0, 49], [0, 1, 0, 4.8], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
      // add standoff_3 (standoff)
      multmatrix([[1, 0, 0, 2], [0, 1, 0, 16.2], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
      // add standoff_4 (standoff)
      multmatrix([[1, 0, 0, 49], [0, 1, 0, 16.2], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
      // add boss_1 (boss)
      multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, -2.645584], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=16, d=6.6, $fn=64);
      // add boss_2 (boss)
      multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, -2.645584], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=16, d=6.6, $fn=64);
      // add boss_3 (boss)
      multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, 23.645584], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=16, d=6.6, $fn=64);
      // add boss_4 (boss)
      multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, 23.645584], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=16, d=6.6, $fn=64);
    }
    // cut board_cut (port_cut)
    multmatrix([[-1, 0, 0, -2.9], [0, -1, 0, 10.5], [0, 0, 1, -1.5], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
    // cut standoff_1_pilot (pilot)
    multmatrix([[1, 0, 0, 2], [0, 1, 0, 4.8], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
    // cut standoff_2_pilot (pilot)
    multmatrix([[1, 0, 0, 49], [0, 1, 0, 4.8], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
    // cut standoff_3_pilot (pilot)
    multmatrix([[1, 0, 0, 2], [0, 1, 0, 16.2], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
    // cut standoff_4_pilot (pilot)
    multmatrix([[1, 0, 0, 49], [0, 1, 0, 16.2], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
    // cut boss_1_pilot (pilot)
    multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, -2.645584], [0, 0, 1, 2.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
    // cut boss_2_pilot (pilot)
    multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, -2.645584], [0, 0, 1, 2.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
    // cut boss_3_pilot (pilot)
    multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, 23.645584], [0, 0, 1, 2.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
    // cut boss_4_pilot (pilot)
    multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, 23.645584], [0, 0, 1, 2.3], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  }
}
color("#c0504d") {
  // body lid
  difference() {
    union() {
      // body lid (lid_plate)
      multmatrix([[1, 0, 0, 25.2], [0, 1, 0, 10.5], [0, 0, 1, 10], [0, 0, 0, 1]]) translate([-29.3, -13.3, 0]) cube([58.6, 26.6, 2.4]);
      // add lid_lip (lip)
      multmatrix([[1, 0, 0, 25.2], [0, 1, 0, 10.5], [0, 0, 1, 7.9], [0, 0, 0, 1]]) difference() { translate([-26.65, -10.65, 0]) cube([53.3, 21.3, 4.5]); translate([0, 0, -1]) translate([-25.45, -9.45, 0]) cube([50.9, 18.9, 6.5]); }
      // add boss_1_pad (pad)
      multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, -2.645584], [0, 0, 1, 10], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
      // add boss_2_pad (pad)
      multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, -2.645584], [0, 0, 1, 10], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
      // add boss_3_pad (pad)
      multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, 23.645584], [0, 0, 1, 10], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
      // add boss_4_pad (pad)
      multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, 23.645584], [0, 0, 1, 10], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    }
    // cut boss_1_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, -2.645584], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_1_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, -2.645584], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
    // cut boss_2_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, -2.645584], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_2_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, -2.645584], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
    // cut boss_3_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, 23.645584], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_3_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, 23.645584], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
    // cut boss_4_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, 23.645584], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_4_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, 23.645584], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  }
}
%color("#7f7f7f") multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([51, 21, 1]); multmatrix([[1, 0, 0, -1.3], [0, 1, 0, 6.5], [0, 0, 1, 1], [0, 0, 0, 1]]) cube([5.5, 8, 2.8]); } // ghost board
