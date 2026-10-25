// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, 13.6], [0, 0, 0, 1]]) translate([-35.7, -18.15, 0]) cube([71.4, 36.3, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, 11.5], [0, 0, 0, 1]]) difference() { translate([-33.05, -15.5, 0]) cube([66.1, 31, 4.5]); translate([0, 0, -1]) translate([-31.85, -14.3, 0]) cube([63.7, 28.6, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, -3.12132], [0, 0, 1, 13.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, -3.12132], [0, 0, 1, 13.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, 32.22132], [0, 0, 1, 13.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, 32.22132], [0, 0, 1, 13.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, -3.12132], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, -3.12132], [0, 0, 1, 10.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, -3.12132], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, -3.12132], [0, 0, 1, 10.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, 32.22132], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, 32.22132], [0, 0, 1, 10.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, 32.22132], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, 32.22132], [0, 0, 1, 10.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
}
