// render file: base only (lid off), closed pose; references are translucent ghosts
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 24.85], [0, 0, 1, -7.6], [0, 0, 0, 1]]) difference() { translate([-46.2, -29.15, 0]) cube([92.4, 58.3, 35.7]); translate([0, 0, 2.4]) translate([-43.8, -26.75, 0]) cube([87.6, 53.5, 34.3]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2], [0, 1, 0, 2], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 68], [0, 1, 0, 2], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2], [0, 1, 0, 48], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 68], [0, 1, 0, 48], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -5.6], [0, 1, 0, 1.3], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 75.6], [0, 1, 0, 1.3], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -5.6], [0, 1, 0, 48.4], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 75.6], [0, 1, 0, 48.4], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.6, $fn=64);
  }
  // cut module_1_1_cut (port_cut)
  multmatrix([[0, 1, 0, 35], [-1, 0, 0, -3.1], [0, 0, 1, 7], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2], [0, 1, 0, 2], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 68], [0, 1, 0, 2], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2], [0, 1, 0, 48], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 68], [0, 1, 0, 48], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut rebate (rebate)
  multmatrix([[1, 0, 0, 35], [0, 1, 0, 24.85], [0, 0, 1, 25.7], [0, 0, 0, 1]]) translate([-44.7, -27.65, 0]) cube([89.4, 55.3, 3.4]);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -5.6], [0, 1, 0, 1.3], [0, 0, 1, 18], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 75.6], [0, 1, 0, 1.3], [0, 0, 1, 18], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -5.6], [0, 1, 0, 48.4], [0, 0, 1, 18], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 75.6], [0, 1, 0, 48.4], [0, 0, 1, 18], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
}

color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.6], [0, 0, 0, 1]]) cube([70, 50, 1.6]); } // ghost board
color("#7f7f7f", 0.3) multmatrix([[0, -1, 0, 45.5], [1, 0, 0, 0], [0, 0, 1, 8.5], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([51, 21, 1]); multmatrix([[1, 0, 0, -1.3], [0, 1, 0, 6.5], [0, 0, 1, 1], [0, 0, 0, 1]]) cube([5.5, 8, 2.8]); } // ghost module_1_1
color("#7f7f7f", 0.3) multmatrix([[0, -1, 0, 43.89], [1, 0, 0, 1.37], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 8.5]); } // ghost module_1_1_stack_1
color("#7f7f7f", 0.3) multmatrix([[0, -1, 0, 26.11], [1, 0, 0, 1.37], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 8.5]); } // ghost module_1_1_stack_2
