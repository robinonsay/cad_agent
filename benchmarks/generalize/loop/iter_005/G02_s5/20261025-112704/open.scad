// render file: base only (lid off), closed pose; references are translucent ghosts
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 31.8], [0, 1, 0, 26.6], [0, 0, 1, -9.4], [0, 0, 0, 1]]) difference() { translate([-48, -30.6, 0]) cube([96, 61.2, 28.35]); translate([0, 0, 2.4]) translate([-45.6, -28.2, 0]) cube([91.2, 56.4, 26.95]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 14], [0, 1, 0, 2.5], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 15.3], [0, 1, 0, 50.7], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 7.6], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 35.5], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -10.6], [0, 1, 0, 16.907115], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=25.95, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 74.2], [0, 1, 0, 1.6], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=25.95, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -10.6], [0, 1, 0, 51.6], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=25.95, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 74.2], [0, 1, 0, 51.6], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=25.95, d=6.6, $fn=64);
  }
  // cut board_usb_cut (port_cut)
  multmatrix([[-1, 0, 0, -15], [0, -1, 0, 38.1], [0, 0, 1, 0.2], [0, 0, 0, 1]]) translate([-2.2, -8.4, 0]) cube([4.4, 16.8, 13.8]);
  // cut board_usb_cut_roof (port_roof)
  multmatrix([[0, 0, -1, -12.8], [0, 1, 0, 38.1], [1, 0, 0, 14], [0, 0, 0, 1]]) linear_extrude(height=4.4) polygon(points=[[0, -8.4], [0.95, -7.45], [0.95, 7.45], [0, 8.4]]);
  // cut board_dc_cut (port_cut)
  multmatrix([[0, 0, -1, -12.8], [0, 1, 0, 7.6], [1, 0, 0, 7.1], [0, 0, 0, 1]]) cylinder(h=4.4, d=11.814231, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 14], [0, 1, 0, 2.5], [0, 0, 1, -8.5], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 15.3], [0, 1, 0, 50.7], [0, 0, 1, -8.5], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 7.6], [0, 0, 1, -8.5], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 35.5], [0, 0, 1, -8.5], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut rebate (rebate)
  multmatrix([[1, 0, 0, 31.8], [0, 1, 0, 26.6], [0, 0, 1, 16.55], [0, 0, 0, 1]]) translate([-46.5, -29.1, 0]) cube([93, 58.2, 3.4]);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -10.6], [0, 1, 0, 16.907115], [0, 0, 1, 8.85], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 74.2], [0, 1, 0, 1.6], [0, 0, 1, 8.85], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -10.6], [0, 1, 0, 51.6], [0, 0, 1, 8.85], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 74.2], [0, 1, 0, 51.6], [0, 0, 1, 8.85], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
}

color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([68.6, 53.3, 1.6]); multmatrix([[1, 0, 0, -6], [0, 1, 0, 32.1], [0, 0, 1, 1.6], [0, 0, 0, 1]]) cube([16, 12, 11]); multmatrix([[1, 0, 0, -2], [0, 1, 0, 3.1], [0, 0, 1, 1.6], [0, 0, 0, 1]]) cube([14, 9, 11]); } // ghost board
