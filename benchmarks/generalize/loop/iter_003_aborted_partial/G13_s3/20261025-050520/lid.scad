// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 24.85], [0, 0, 1, 27.8], [0, 0, 0, 1]]) translate([-39, -29.15, 0]) cube([78, 58.3, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 24.85], [0, 0, 1, 25.7], [0, 0, 0, 1]]) difference() { translate([-36.35, -26.5, 0]) cube([72.7, 53, 4.5]); translate([0, 0, -1]) translate([-35.15, -25.3, 0]) cube([70.3, 50.6, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -4.087006], [0, 0, 1, 27.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, -4.087006], [0, 0, 1, 27.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 53.787006], [0, 0, 1, 27.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, 53.787006], [0, 0, 1, 27.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -4.087006], [0, 0, 1, 26.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -4.087006], [0, 0, 1, 24.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, -4.087006], [0, 0, 1, 26.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, -4.087006], [0, 0, 1, 24.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 53.787006], [0, 0, 1, 26.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 53.787006], [0, 0, 1, 24.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, 53.787006], [0, 0, 1, 26.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, 53.787006], [0, 0, 1, 24.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}
