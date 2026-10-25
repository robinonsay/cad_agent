// body base
difference() {
  union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 31.8], [0, 1, 0, 26.6], [0, 0, 1, -9.4], [0, 0, 0, 1]]) difference() { translate([-40.8, -30.6, 0]) cube([81.6, 61.2, 25.2]); translate([0, 0, 2.4]) translate([-38.4, -28.2, 0]) cube([76.8, 56.4, 23.8]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 14], [0, 1, 0, 2.5], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 15.3], [0, 1, 0, 50.7], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 7.6], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 35.5], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=9.4, d=6.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, -3.787006], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=25.2, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 72.387006], [0, 1, 0, -3.787006], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=25.2, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, 56.987006], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=25.2, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 72.387006], [0, 1, 0, 56.987006], [0, 0, 1, -9.4], [0, 0, 0, 1]]) cylinder(h=25.2, d=6.6, $fn=64);
  }
  // cut board_usb_cut (port_cut)
  multmatrix([[-1, 0, 0, -7.8], [0, -1, 0, 38.1], [0, 0, 1, 0.2], [0, 0, 0, 1]]) translate([-2.2, -8.4, 0]) cube([4.4, 16.8, 13.8]);
  // cut board_dc_cut (port_cut)
  multmatrix([[0, 0, -1, -5.6], [0, 1, 0, 7.6], [1, 0, 0, 7.1], [0, 0, 0, 1]]) cylinder(h=4.4, d=11.814231, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 14], [0, 1, 0, 2.5], [0, 0, 1, -8.5], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 15.3], [0, 1, 0, 50.7], [0, 0, 1, -8.5], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 7.6], [0, 0, 1, -8.5], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 66.1], [0, 1, 0, 35.5], [0, 0, 1, -8.5], [0, 0, 0, 1]]) cylinder(h=9.5, d=2.503015, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, -3.787006], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 72.387006], [0, 1, 0, -3.787006], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, 56.987006], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 72.387006], [0, 1, 0, 56.987006], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
}
