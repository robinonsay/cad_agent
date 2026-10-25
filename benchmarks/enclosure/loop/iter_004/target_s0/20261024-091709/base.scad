// body base
difference() {
  union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 34.35], [0, 1, 0, 25], [0, 0, 1, -8], [0, 0, 0, 1]]) difference() { translate([-38.55, -27.9, 0]) cube([77.1, 55.8, 22]); translate([0, 0, 2.4]) translate([-36.15, -25.5, 0]) cube([72.3, 51, 20.6]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=6.4, d=5.3, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 2.5], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=6.4, d=5.3, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 47.5], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=6.4, d=5.3, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 47.5], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=6.4, d=5.3, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, -2.474874], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=22, d=6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, -2.474874], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=22, d=6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, 52.474874], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=22, d=6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, 52.474874], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=22, d=6, $fn=64);
  }
  // cut module_1_1_cut (port_cut)
  multmatrix([[-1, 0, 0, -3], [0, -1, 0, 24.09], [0, 0, 1, 1.1], [0, 0, 0, 1]]) translate([-2.2, -5.3, 0]) cube([4.4, 10.6, 7.6]);
  // cut connector_1_1_cut (port_cut)
  multmatrix([[0, 0, 1, 69.5], [0, 1, 0, 17.666667], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.6, $fn=64);
  // cut connector_1_2_cut (port_cut)
  multmatrix([[0, 0, 1, 69.5], [0, 1, 0, 32.333333], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.6, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.1, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 2.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.1, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 47.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.1, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 47.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.1, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, -2.474874], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=7, d=2.5, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, -2.474874], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=7, d=2.5, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, 52.474874], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=7, d=2.5, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, 52.474874], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=7, d=2.5, $fn=64);
}
