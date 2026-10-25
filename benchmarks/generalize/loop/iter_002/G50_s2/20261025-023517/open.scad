// render file: base only (lid off), closed pose; references are translucent ghosts
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, -7.5], [0, 0, 0, 1]]) difference() { translate([-36, -18.45, 0]) cube([72, 36.9, 16.1]); translate([0, 0, 2.4]) translate([-33.6, -16.05, 0]) cube([67.2, 32.1, 14.7]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 3.5], [0, 0, 1, -7.5], [0, 0, 0, 1]]) cylinder(h=7.5, d=5.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 3.5], [0, 0, 1, -7.5], [0, 0, 0, 1]]) cylinder(h=7.5, d=5.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 26.5], [0, 0, 1, -7.5], [0, 0, 0, 1]]) cylinder(h=7.5, d=5.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 26.5], [0, 0, 1, -7.5], [0, 0, 0, 1]]) cylinder(h=7.5, d=5.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, -3.333452], [0, 0, 1, -7.5], [0, 0, 0, 1]]) cylinder(h=16.1, d=5.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, -3.333452], [0, 0, 1, -7.5], [0, 0, 0, 1]]) cylinder(h=16.1, d=5.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, 32.433452], [0, 0, 1, -7.5], [0, 0, 0, 1]]) cylinder(h=16.1, d=5.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, 32.433452], [0, 0, 1, -7.5], [0, 0, 0, 1]]) cylinder(h=16.1, d=5.6, $fn=64);
  }
  // cut board_usb_data_cut (port_cut)
  multmatrix([[0, 1, 0, 41.4], [-1, 0, 0, -2.7], [0, 0, 1, -1.2], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut board_usb_power_cut (port_cut)
  multmatrix([[0, 1, 0, 54], [-1, 0, 0, -2.7], [0, 0, 1, -1.2], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 3.5], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 3.5], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 26.5], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 26.5], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, -3.333452], [0, 0, 1, 3.5], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, -3.333452], [0, 0, 1, 3.5], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, 32.433452], [0, 0, 1, 3.5], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, 32.433452], [0, 0, 1, 3.5], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
}

color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([65, 30, 1.4]); multmatrix([[1, 0, 0, 6.8], [0, 1, 0, -0.5], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([11.2, 7.5, 3.2]); multmatrix([[1, 0, 0, 37.65], [0, 1, 0, -0.9], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([7.5, 5.9, 2.6]); multmatrix([[1, 0, 0, 50.25], [0, 1, 0, -0.9], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([7.5, 5.9, 2.6]); multmatrix([[1, 0, 0, -1], [0, 1, 0, 10.9], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([14, 12, 1.4]); } // ghost board
