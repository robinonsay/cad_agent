// body base
difference() {
  union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 25.2], [0, 1, 0, 10.5], [0, 0, 1, -6], [0, 0, 0, 1]]) difference() { translate([-29.3, -13.3, 0]) cube([58.6, 26.6, 13.9]); translate([0, 0, 2.4]) translate([-26.9, -10.9, 0]) cube([53.8, 21.8, 12.5]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2], [0, 1, 0, 4.8], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 49], [0, 1, 0, 4.8], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2], [0, 1, 0, 16.2], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 49], [0, 1, 0, 16.2], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, -2.645584], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=13.9, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, -2.645584], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=13.9, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, 23.645584], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=13.9, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, 23.645584], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=13.9, d=6.6, $fn=64);
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
  multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, -2.645584], [0, 0, 1, 0.2], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, -2.645584], [0, 0, 1, 0.2], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, 23.645584], [0, 0, 1, 0.2], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, 23.645584], [0, 0, 1, 0.2], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
}
