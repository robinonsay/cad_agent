// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 26.7], [0, 1, 0, 13.95], [0, 0, 1, 15.4], [0, 0, 0, 1]]) translate([-30.7, -16.97, 0]) cube([61.4, 33.94, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 26.7], [0, 1, 0, 13.95], [0, 0, 1, 13.3], [0, 0, 0, 1]]) difference() { translate([-28.05, -14.32, 0]) cube([56.1, 28.64, 4.5]); translate([0, 0, -1]) translate([-26.85, -13.12, 0]) cube([53.7, 26.24, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -2.807006], [0, 0, 1, 15.4], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 57.187006], [0, 1, 0, -2.807006], [0, 0, 1, 15.4], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 30.707006], [0, 0, 1, 15.4], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 57.187006], [0, 1, 0, 30.707006], [0, 0, 1, 15.4], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -2.807006], [0, 0, 1, 14.4], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -2.807006], [0, 0, 1, 12.3], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 57.187006], [0, 1, 0, -2.807006], [0, 0, 1, 14.4], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 57.187006], [0, 1, 0, -2.807006], [0, 0, 1, 12.3], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 30.707006], [0, 0, 1, 14.4], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 30.707006], [0, 0, 1, 12.3], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 57.187006], [0, 1, 0, 30.707006], [0, 0, 1, 14.4], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 57.187006], [0, 1, 0, 30.707006], [0, 0, 1, 12.3], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}
