// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 13.25], [0, 1, 0, 8.75], [0, 0, 1, 60.7], [0, 0, 0, 1]]) translate([-15.95, -11.45, 0]) cube([31.9, 22.9, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 13.25], [0, 1, 0, 8.75], [0, 0, 1, 58.6], [0, 0, 0, 1]]) difference() { translate([-13.3, -8.8, 0]) cube([26.6, 17.6, 4.5]); translate([0, 0, -1]) translate([-12.1, -7.6, 0]) cube([24.2, 15.2, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -2.574874], [0, 1, 0, -2.574874], [0, 0, 1, 60.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 29.074874], [0, 1, 0, -2.574874], [0, 0, 1, 60.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -2.574874], [0, 1, 0, 20.074874], [0, 0, 1, 60.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 29.074874], [0, 1, 0, 20.074874], [0, 0, 1, 60.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -2.574874], [0, 1, 0, -2.574874], [0, 0, 1, 59.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -2.574874], [0, 1, 0, -2.574874], [0, 0, 1, 57.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 29.074874], [0, 1, 0, -2.574874], [0, 0, 1, 59.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 29.074874], [0, 1, 0, -2.574874], [0, 0, 1, 57.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -2.574874], [0, 1, 0, 20.074874], [0, 0, 1, 59.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -2.574874], [0, 1, 0, 20.074874], [0, 0, 1, 57.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 29.074874], [0, 1, 0, 20.074874], [0, 0, 1, 59.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 29.074874], [0, 1, 0, 20.074874], [0, 0, 1, 57.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}
