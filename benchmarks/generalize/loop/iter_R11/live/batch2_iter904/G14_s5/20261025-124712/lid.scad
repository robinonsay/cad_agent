// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 22.15], [0, 1, 0, 9], [0, 0, 1, 13.8], [0, 0, 0, 1]]) translate([-25.65, -11.8, 0]) cube([51.3, 23.6, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 22.15], [0, 1, 0, 9], [0, 0, 1, 11.7], [0, 0, 0, 1]]) difference() { translate([-23, -9.15, 0]) cube([46, 18.3, 4.5]); translate([0, 0, -1]) translate([-21.8, -7.95, 0]) cube([43.6, 15.9, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, -2.645584], [0, 0, 1, 13.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, -2.645584], [0, 0, 1, 13.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, 20.645584], [0, 0, 1, 13.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, 20.645584], [0, 0, 1, 13.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, -2.645584], [0, 0, 1, 12.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, -2.645584], [0, 0, 1, 10.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, -2.645584], [0, 0, 1, 12.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, -2.645584], [0, 0, 1, 10.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, 20.645584], [0, 0, 1, 12.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.345584], [0, 1, 0, 20.645584], [0, 0, 1, 10.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, 20.645584], [0, 0, 1, 12.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 47.645584], [0, 1, 0, 20.645584], [0, 0, 1, 10.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}
