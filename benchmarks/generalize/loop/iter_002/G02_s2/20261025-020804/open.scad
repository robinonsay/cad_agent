// render file: base only (lid off), closed pose; references are translucent ghosts
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 31.55], [0, 1, 0, 26.6], [0, 0, 1, -6.5], [0, 0, 0, 1]]) difference() { translate([-40.55, -30.1, 0]) cube([81.1, 60.2, 22.3]); translate([0, 0, 2.4]) translate([-38.15, -27.7, 0]) cube([76.3, 55.4, 20.9]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 14], [0, 1, 0, 2.5], [0, 0, 1, -6.5], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 15.3], [0, 1, 0, 50.7], [0, 0, 1, -6.5], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 7.6], [0, 0, 1, -6.5], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 35.5], [0, 0, 1, -6.5], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, -3.287006], [0, 0, 1, -6.5], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 71.887006], [0, 1, 0, -3.287006], [0, 0, 1, -6.5], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, 56.487006], [0, 0, 1, -6.5], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 71.887006], [0, 1, 0, 56.487006], [0, 0, 1, -6.5], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.6, $fn=64);
  }
  // cut board_usb_cut (port_cut)
  multmatrix([[-1, 0, 0, -7.8], [0, -1, 0, 38.1], [0, 0, 1, 0.2], [0, 0, 0, 1]]) translate([-2.2, -8.4, 0]) cube([4.4, 16.8, 13.8]);
  // cut board_dc_cut (port_cut)
  multmatrix([[0, 0, -1, -5.6], [0, 1, 0, 7.6], [1, 0, 0, 7.1], [0, 0, 0, 1]]) cylinder(h=4.4, d=11.814231, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 14], [0, 1, 0, 2.5], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 15.3], [0, 1, 0, 50.7], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 7.6], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 35.5], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, -3.287006], [0, 0, 1, 9.7], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 71.887006], [0, 1, 0, -3.287006], [0, 0, 1, 9.7], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, 56.487006], [0, 0, 1, 9.7], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 71.887006], [0, 1, 0, 56.487006], [0, 0, 1, 9.7], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
}

color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([68.6, 53.3, 1.6]); multmatrix([[1, 0, 0, -6], [0, 1, 0, 32.1], [0, 0, 1, 1.6], [0, 0, 0, 1]]) cube([16, 12, 11]); multmatrix([[1, 0, 0, -2], [0, 1, 0, 3.1], [0, 0, 1, 1.6], [0, 0, 0, 1]]) cube([14, 9, 11]); } // ghost board
