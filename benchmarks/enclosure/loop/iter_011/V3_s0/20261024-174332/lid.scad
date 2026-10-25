// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 20], [0, 0, 1, 25.2], [0, 0, 0, 1]]) translate([-44, -24, 0]) cube([88, 48, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 20], [0, 0, 1, 23.1], [0, 0, 0, 1]]) difference() { translate([-41.35, -21.35, 0]) cube([82.7, 42.7, 4.5]); translate([0, 0, -1]) translate([-40.15, -20.15, 0]) cube([80.3, 40.3, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, -3.787006], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 43.787006], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, 43.787006], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, -3.787006], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, -3.787006], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 43.787006], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 43.787006], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, 43.787006], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 83.787006], [0, 1, 0, 43.787006], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}
