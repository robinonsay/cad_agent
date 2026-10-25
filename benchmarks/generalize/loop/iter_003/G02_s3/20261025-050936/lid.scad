// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 31.8], [0, 1, 0, 26.6], [0, 0, 1, 15.8], [0, 0, 0, 1]]) translate([-40.8, -30.6, 0]) cube([81.6, 61.2, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 31.8], [0, 1, 0, 26.6], [0, 0, 1, 13.7], [0, 0, 0, 1]]) difference() { translate([-38.15, -27.95, 0]) cube([76.3, 55.9, 4.5]); translate([0, 0, -1]) translate([-36.95, -26.75, 0]) cube([73.9, 53.5, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, -3.787006], [0, 0, 1, 15.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 72.387006], [0, 1, 0, -3.787006], [0, 0, 1, 15.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, 56.987006], [0, 0, 1, 15.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 72.387006], [0, 1, 0, 56.987006], [0, 0, 1, 15.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, -3.787006], [0, 0, 1, 14.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, -3.787006], [0, 0, 1, 12.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 72.387006], [0, 1, 0, -3.787006], [0, 0, 1, 14.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 72.387006], [0, 1, 0, -3.787006], [0, 0, 1, 12.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, 56.987006], [0, 0, 1, 14.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -8.787006], [0, 1, 0, 56.987006], [0, 0, 1, 12.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 72.387006], [0, 1, 0, 56.987006], [0, 0, 1, 14.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 72.387006], [0, 1, 0, 56.987006], [0, 0, 1, 12.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}
