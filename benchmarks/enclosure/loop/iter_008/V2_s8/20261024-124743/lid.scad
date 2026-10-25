// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 44.6], [0, 1, 0, 22.5], [0, 0, 1, 14.2], [0, 0, 0, 1]]) translate([-48.9, -26, 0]) cube([97.8, 52, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 44.6], [0, 1, 0, 22.5], [0, 0, 1, 12.1], [0, 0, 0, 1]]) difference() { translate([-46.25, -23.35, 0]) cube([92.5, 46.7, 4.5]); translate([0, 0, -1]) translate([-45.05, -22.15, 0]) cube([90.1, 44.3, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, -3.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, -3.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, 48.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, 48.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, -3.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, -3.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, -3.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, -3.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, 48.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.910229], [0, 1, 0, 48.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, 48.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, 48.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
}
