// render file: printed bodies, closed pose; references drawn solid
color("#9bbb59") multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.6], [0, 0, 0, 1]]) cube([80, 40, 1.6]); } // reference board
color("#8064a2") multmatrix([[1, 0, 0, 4.34], [0, 1, 0, 9.5], [0, 0, 1, 8.5], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([51, 21, 1]); multmatrix([[1, 0, 0, -1.3], [0, 1, 0, 6.5], [0, 0, 1, 1], [0, 0, 0, 1]]) cube([5.5, 8, 2.8]); } // reference module_1_1
color("#f79646") multmatrix([[1, 0, 0, 5.71], [0, 1, 0, 11.11], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 8.5]); } // reference module_1_1_stack_1
color("#4f81bd") multmatrix([[1, 0, 0, 5.71], [0, 1, 0, 28.89], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 8.5]); } // reference module_1_1_stack_2
color("#c0504d") multmatrix([[1, 0, 0, 68], [0, 1, 0, 17], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([12, 6, 5]); } // reference connector_1_1
color("#9bbb59") multmatrix([[1, 0, 0, 60.5], [0, 1, 0, 20], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=20, d=10, $fn=64); } // reference generic_1_1
// body base
difference() {
  color("#4f81bd", 0.3) union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 20], [0, 0, 1, -8.1], [0, 0, 0, 1]]) difference() { translate([-43.5, -23.5, 0]) cube([87, 47, 33.3]); translate([0, 0, 2.4]) translate([-41.1, -21.1, 0]) cube([82.2, 42.2, 31.9]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 37.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 37.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, -3.287006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, -3.287006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, 43.287006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, 43.287006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.6, $fn=64);
  }
  // cut module_1_1_cut (port_cut)
  multmatrix([[-1, 0, 0, -2.3], [0, -1, 0, 20], [0, 0, 1, 7], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut connector_1_1_cut (port_cut)
  multmatrix([[0, 0, 1, 80.1], [0, 1, 0, 20], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 37.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 37.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, -3.287006], [0, 0, 1, 17.5], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, -3.287006], [0, 0, 1, 17.5], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, 43.287006], [0, 0, 1, 17.5], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, 43.287006], [0, 0, 1, 17.5], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
}

// body lid
difference() {
  color("#c0504d", 0.3) union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 20], [0, 0, 1, 25.2], [0, 0, 0, 1]]) translate([-43.5, -23.5, 0]) cube([87, 47, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 20], [0, 0, 1, 23.1], [0, 0, 0, 1]]) difference() { translate([-40.85, -20.85, 0]) cube([81.7, 41.7, 4.5]); translate([0, 0, -1]) translate([-39.65, -19.65, 0]) cube([79.3, 39.3, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, -3.287006], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, -3.287006], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, 43.287006], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, 43.287006], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, -3.287006], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, -3.287006], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, -3.287006], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, -3.287006], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, 43.287006], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, 43.287006], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, 43.287006], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, 43.287006], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}

