// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 25.2], [0, 1, 0, 10.5], [0, 0, 1, 7.9], [0, 0, 0, 1]]) translate([-29.3, -13.3, 0]) cube([58.6, 26.6, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 25.2], [0, 1, 0, 10.5], [0, 0, 1, 5.8], [0, 0, 0, 1]]) difference() { translate([-26.65, -10.65, 0]) cube([53.3, 21.3, 4.5]); translate([0, 0, -1]) translate([-25.45, -9.45, 0]) cube([50.9, 18.9, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, -2.645584], [0, 0, 1, 7.9], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, -2.645584], [0, 0, 1, 7.9], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, 23.645584], [0, 0, 1, 7.9], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, 23.645584], [0, 0, 1, 7.9], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, -2.645584], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, -2.645584], [0, 0, 1, 4.8], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, -2.645584], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, -2.645584], [0, 0, 1, 4.8], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, 23.645584], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.945584], [0, 1, 0, 23.645584], [0, 0, 1, 4.8], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, 23.645584], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 54.345584], [0, 1, 0, 23.645584], [0, 0, 1, 4.8], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}
