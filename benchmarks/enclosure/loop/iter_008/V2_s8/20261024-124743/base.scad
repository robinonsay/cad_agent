// body base
difference() {
  union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 44.6], [0, 1, 0, 22.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) difference() { translate([-48.9, -26, 0]) cube([97.8, 52, 22.3]); translate([0, 0, 2.4]) translate([-46.5, -23.6, 0]) cube([93, 47.2, 20.9]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 87.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 42.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 87.5], [0, 1, 0, 42.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, -3.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.1, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, -3.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.1, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, 48.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.1, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, 48.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.1, $fn=64);
  }
  // cut module_1_1_cut (port_cut)
  multmatrix([[-1, 0, 0, -3.1], [0, -1, 0, 22.5], [0, 0, 1, 1], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut connector_1_1_cut (port_cut)
  multmatrix([[1, 0, 0, 25.220011], [0, 0, -1, -0.1], [0, 1, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut connector_1_2_cut (port_cut)
  multmatrix([[1, 0, 0, 45.540011], [0, 0, -1, -0.1], [0, 1, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut connector_1_3_cut (port_cut)
  multmatrix([[1, 0, 0, 65.860011], [0, 0, -1, -0.1], [0, 1, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 87.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 42.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 87.5], [0, 1, 0, 42.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, -3.110229], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, -3.110229], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, 48.110229], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, 48.110229], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
}
