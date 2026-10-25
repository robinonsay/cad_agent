// body base
difference() {
  union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 30], [0, 0, 1, -8.1], [0, 0, 0, 1]]) difference() { translate([-43.5, -33.5, 0]) cube([87, 67, 26.8]); translate([0, 0, 2.4]) translate([-41.1, -31.1, 0]) cube([82.2, 62.2, 25.4]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 57.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 57.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, -3.287006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=26.8, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, -3.287006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=26.8, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, 63.287006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=26.8, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, 63.287006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=26.8, d=6.6, $fn=64);
  }
  // cut connector_1_1_cut (port_cut)
  multmatrix([[0, 0, -1, -0.1], [0, 1, 0, 30], [1, 0, 0, 5.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=11.814231, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 57.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 57.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, -3.287006], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, -3.287006], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.287006], [0, 1, 0, 63.287006], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 83.287006], [0, 1, 0, 63.287006], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
}
