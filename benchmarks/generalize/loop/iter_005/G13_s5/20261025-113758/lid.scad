// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 25], [0, 0, 1, 25.7], [0, 0, 0, 1]]) translate([-44.45, -27.25, 0]) cube([88.9, 54.5, 2.4]);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -5.6], [0, 1, 0, 1.6], [0, 0, 1, 24.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 75.6], [0, 1, 0, 1.6], [0, 0, 1, 24.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -5.6], [0, 1, 0, 48.4], [0, 0, 1, 24.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 75.6], [0, 1, 0, 48.4], [0, 0, 1, 24.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
}
