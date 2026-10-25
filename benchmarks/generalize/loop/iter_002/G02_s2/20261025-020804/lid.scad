// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 31.55], [0, 1, 0, 26.6], [0, 0, 1, 15.8], [0, 0, 0, 1]]) translate([-40.55, -30.1, 0]) cube([81.1, 60.2, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 31.55], [0, 1, 0, 26.6], [0, 0, 1, 13.7], [0, 0, 0, 1]]) difference() { translate([-37.9, -27.45, 0]) cube([75.8, 54.9, 4.5]); translate([0, 0, -1]) translate([-36.7, -26.25, 0]) cube([73.4, 52.5, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, -3.287006], [0, 0, 1, 15.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 71.887006], [0, 1, 0, -3.287006], [0, 0, 1, 15.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, 56.487006], [0, 0, 1, 15.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 71.887006], [0, 1, 0, 56.487006], [0, 0, 1, 15.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, -3.287006], [0, 0, 1, 14.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, -3.287006], [0, 0, 1, 12.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 71.887006], [0, 1, 0, -3.287006], [0, 0, 1, 14.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 71.887006], [0, 1, 0, -3.287006], [0, 0, 1, 12.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, 56.487006], [0, 0, 1, 14.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, 56.487006], [0, 0, 1, 12.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 71.887006], [0, 1, 0, 56.487006], [0, 0, 1, 14.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 71.887006], [0, 1, 0, 56.487006], [0, 0, 1, 12.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}
