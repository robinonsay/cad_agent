// render file: base only (lid off), closed pose; references are translucent ghosts
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 24.85], [0, 0, 1, -8.1], [0, 0, 0, 1]]) difference() { translate([-43.5, -29.15, 0]) cube([87, 58.3, 33.3]); translate([0, 0, 2.4]) translate([-41.1, -26.75, 0]) cube([82.2, 53.5, 31.9]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 37.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 37.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.910229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.1, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, -3.910229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.1, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 53.610229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.1, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, 53.610229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.1, $fn=64);
  }
  // cut module_1_1_cut (port_cut)
  multmatrix([[0, 1, 0, 39.33], [-1, 0, 0, -3.1], [0, 0, 1, 7], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut connector_1_1_cut (port_cut)
  multmatrix([[0, 0, -1, -0.1], [0, 1, 0, 20.419989], [1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 37.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 37.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.910229], [0, 0, 1, 19.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, -3.910229], [0, 0, 1, 19.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 53.610229], [0, 0, 1, 19.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, 53.610229], [0, 0, 1, 19.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
}

color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.6], [0, 0, 0, 1]]) cube([80, 40, 1.6]); } // ghost board
color("#7f7f7f", 0.3) multmatrix([[0, -1, 0, 49.83], [1, 0, 0, 0], [0, 0, 1, 8.5], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([51, 21, 1]); multmatrix([[1, 0, 0, -1.3], [0, 1, 0, 6.5], [0, 0, 1, 1], [0, 0, 0, 1]]) cube([5.5, 8, 2.8]); } // ghost module_1_1
color("#7f7f7f", 0.3) multmatrix([[0, -1, 0, 48.22], [1, 0, 0, 1.37], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 8.5]); } // ghost module_1_1_stack_1
color("#7f7f7f", 0.3) multmatrix([[0, -1, 0, 30.44], [1, 0, 0, 1.37], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 8.5]); } // ghost module_1_1_stack_2
color("#7f7f7f", 0.3) multmatrix([[-1, 0, 0, 12], [0, -1, 0, 23.419989], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([12, 6, 5]); } // ghost connector_1_1
color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 55], [0, 1, 0, 20], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=20, d=10, $fn=64); } // ghost generic_1_1
