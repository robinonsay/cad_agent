// body base
difference() {
  union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 34.6], [0, 1, 0, 25], [0, 0, 1, -8.1], [0, 0, 0, 1]]) difference() { translate([-38.9, -28.5, 0]) cube([77.8, 57, 22.2]); translate([0, 0, 2.4]) translate([-36.5, -26.1, 0]) cube([73, 52.2, 20.8]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 47.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 47.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, -3.074874], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.2, d=6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, -3.074874], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.2, d=6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, 53.074874], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.2, d=6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, 53.074874], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.2, d=6, $fn=64);
  }
  // cut module_1_1_cut (port_cut)
  multmatrix([[-1, 0, 0, -3.1], [0, -1, 0, 24.09], [0, 0, 1, 1], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut connector_1_1_cut (port_cut)
  multmatrix([[0, 0, 1, 70.1], [0, 1, 0, 17.666667], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut connector_1_2_cut (port_cut)
  multmatrix([[0, 0, 1, 70.1], [0, 1, 0, 32.333333], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.102533, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 2.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.102533, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 47.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.102533, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 47.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.102533, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, -3.074874], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, -3.074874], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, 53.074874], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, 53.074874], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7, d=2.503015, $fn=64);
}
