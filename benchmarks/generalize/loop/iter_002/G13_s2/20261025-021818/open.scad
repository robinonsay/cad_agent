// render file: base only (lid off), closed pose; references are translucent ghosts
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 25.15], [0, 0, 1, -7.1], [0, 0, 0, 1]]) difference() { translate([-39, -29.15, 0]) cube([78, 58.3, 34.9]); translate([0, 0, 2.4]) translate([-36.6, -26.75, 0]) cube([73.2, 53.5, 33.5]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2], [0, 1, 0, 2], [0, 0, 1, -7.1], [0, 0, 0, 1]]) cylinder(h=5.5, d=5.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 68], [0, 1, 0, 2], [0, 0, 1, -7.1], [0, 0, 0, 1]]) cylinder(h=5.5, d=5.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2], [0, 1, 0, 48], [0, 0, 1, -7.1], [0, 0, 0, 1]]) cylinder(h=5.5, d=5.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 68], [0, 1, 0, 48], [0, 0, 1, -7.1], [0, 0, 0, 1]]) cylinder(h=5.5, d=5.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, -7.1], [0, 0, 0, 1]]) cylinder(h=34.9, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, -3.787006], [0, 0, 1, -7.1], [0, 0, 0, 1]]) cylinder(h=34.9, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 54.087006], [0, 0, 1, -7.1], [0, 0, 0, 1]]) cylinder(h=34.9, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, 54.087006], [0, 0, 1, -7.1], [0, 0, 0, 1]]) cylinder(h=34.9, d=6.6, $fn=64);
  }
  // cut module_1_1_cut (port_cut)
  multmatrix([[0, -1, 0, 35], [1, 0, 0, 53.1], [0, 0, 1, 7], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2], [0, 1, 0, 2], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 68], [0, 1, 0, 2], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2], [0, 1, 0, 48], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 68], [0, 1, 0, 48], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 21.7], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, -3.787006], [0, 0, 1, 21.7], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 54.087006], [0, 0, 1, 21.7], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, 54.087006], [0, 0, 1, 21.7], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
}

color("#7f7f7f", 0.3) multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.6], [0, 0, 0, 1]]) cube([70, 50, 1.6]); } // ghost board
color("#7f7f7f", 0.3) multmatrix([[0, 1, 0, 24.5], [-1, 0, 0, 50], [0, 0, 1, 8.5], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([51, 21, 1]); multmatrix([[1, 0, 0, -1.3], [0, 1, 0, 6.5], [0, 0, 1, 1], [0, 0, 0, 1]]) cube([5.5, 8, 2.8]); } // ghost module_1_1
color("#7f7f7f", 0.3) multmatrix([[0, 1, 0, 26.11], [-1, 0, 0, 48.63], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 8.5]); } // ghost module_1_1_stack_1
color("#7f7f7f", 0.3) multmatrix([[0, 1, 0, 43.89], [-1, 0, 0, 48.63], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 8.5]); } // ghost module_1_1_stack_2
