// body base
difference() {
  union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 13.25], [0, 1, 0, 8.75], [0, 0, 1, -5.5], [0, 0, 0, 1]]) difference() { translate([-15.95, -11.45, 0]) cube([31.9, 22.9, 76.4]); translate([0, 0, 2.4]) translate([-13.55, -9.05, 0]) cube([27.1, 18.1, 75]); }
    // add cradle_support_xm_1 (support)
    multmatrix([[1, 0, 0, -0.125], [0, 1, 0, 8.75], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.325, -8.75, 0]) cube([2.65, 17.5, 5.5]);
    // add cradle_support_xp_1 (support)
    multmatrix([[1, 0, 0, 26.625], [0, 1, 0, 8.75], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-1.325, -8.75, 0]) cube([2.65, 17.5, 5.5]);
    // add cradle_support_ym_1 (support)
    multmatrix([[1, 0, 0, 13.25], [0, 1, 0, -0.125], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-13.25, -1.325, 0]) cube([26.5, 2.65, 5.5]);
    // add cradle_support_yp_1 (support)
    multmatrix([[1, 0, 0, 13.25], [0, 1, 0, 17.625], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-13.25, -1.325, 0]) cube([26.5, 2.65, 5.5]);
    // add cradle_rim_xm_1 (rim)
    multmatrix([[1, 0, 0, -0.85], [0, 1, 0, 8.75], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-0.6, -10.2, 0]) cube([1.2, 20.4, 8.5]);
    // add cradle_rim_xp_1 (rim)
    multmatrix([[1, 0, 0, 27.35], [0, 1, 0, 8.75], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-0.6, -10.2, 0]) cube([1.2, 20.4, 8.5]);
    // add cradle_rim_ym_1 (rim)
    multmatrix([[1, 0, 0, 13.25], [0, 1, 0, -0.85], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-13.5, -0.6, 0]) cube([27, 1.2, 8.5]);
    // add cradle_rim_yp_1 (rim)
    multmatrix([[1, 0, 0, 13.25], [0, 1, 0, 18.35], [0, 0, 1, -5.5], [0, 0, 0, 1]]) translate([-13.5, -0.6, 0]) cube([27, 1.2, 8.5]);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -2.574874], [0, 1, 0, -2.574874], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=76.4, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 29.074874], [0, 1, 0, -2.574874], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=76.4, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -2.574874], [0, 1, 0, 20.074874], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=76.4, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 29.074874], [0, 1, 0, 20.074874], [0, 0, 1, -5.5], [0, 0, 0, 1]]) cylinder(h=76.4, d=6.6, $fn=64);
  }
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -2.574874], [0, 1, 0, -2.574874], [0, 0, 1, 63.2], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 29.074874], [0, 1, 0, -2.574874], [0, 0, 1, 63.2], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -2.574874], [0, 1, 0, 20.074874], [0, 0, 1, 63.2], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 29.074874], [0, 1, 0, 20.074874], [0, 0, 1, 63.2], [0, 0, 0, 1]]) cylinder(h=8.7, d=2.503015, $fn=64);
}
