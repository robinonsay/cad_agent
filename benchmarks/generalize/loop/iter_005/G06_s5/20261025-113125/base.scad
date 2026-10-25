// body base
difference() {
  union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 18], [0, 0, 1, -6], [0, 0, 0, 1]]) difference() { translate([-43, -27.2, 0]) cube([86, 54.4, 21.7]); translate([0, 0, 2.4]) translate([-40.6, -24.8, 0]) cube([81.2, 49.6, 20.3]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 33.5], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 33.5], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=6, d=5.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, 2.1], [0, 1, 0, -4.1], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=21.7, d=5.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 77.9], [0, 1, 0, -4.1], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=21.7, d=5.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, 2.1], [0, 1, 0, 40.1], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=21.7, d=5.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 77.9], [0, 1, 0, 40.1], [0, 0, 1, -6], [0, 0, 0, 1]]) cylinder(h=21.7, d=5.6, $fn=64);
  }
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 33.5], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 33.5], [0, 0, 1, -5.1], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.1], [0, 1, 0, -4.1], [0, 0, 1, 10.6], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 77.9], [0, 1, 0, -4.1], [0, 0, 1, 10.6], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.1], [0, 1, 0, 40.1], [0, 0, 1, 10.6], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 77.9], [0, 1, 0, 40.1], [0, 0, 1, 10.6], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
}
