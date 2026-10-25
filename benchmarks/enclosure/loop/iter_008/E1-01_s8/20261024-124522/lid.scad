// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 34.6], [0, 1, 0, 25], [0, 0, 1, 14.2], [0, 0, 0, 1]]) translate([-38.9, -28.5, 0]) cube([77.8, 57, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 34.6], [0, 1, 0, 25], [0, 0, 1, 12.1], [0, 0, 0, 1]]) difference() { translate([-36.25, -25.85, 0]) cube([72.5, 51.7, 4.5]); translate([0, 0, -1]) translate([-35.05, -24.65, 0]) cube([70.1, 49.3, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, -3.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, -3.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, 53.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, 53.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, -3.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, -3.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, -3.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, -3.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, 53.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, 53.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, 53.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, 53.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
}
