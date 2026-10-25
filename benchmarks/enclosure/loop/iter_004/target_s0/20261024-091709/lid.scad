// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 34.35], [0, 1, 0, 25], [0, 0, 1, 14], [0, 0, 0, 1]]) translate([-38.55, -27.9, 0]) cube([77.1, 55.8, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 34.35], [0, 1, 0, 25], [0, 0, 1, 12], [0, 0, 0, 1]]) difference() { translate([-35.9, -25.25, 0]) cube([71.8, 50.5, 4.4]); translate([0, 0, -1]) translate([-34.7, -24.05, 0]) cube([69.4, 48.1, 6.4]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, -2.474874], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, -2.474874], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, 52.474874], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, 52.474874], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, -2.474874], [0, 0, 1, 13], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, -2.474874], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=3, d=6.5, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, -2.474874], [0, 0, 1, 13], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, -2.474874], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=3, d=6.5, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, 52.474874], [0, 0, 1, 13], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, 52.474874], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=3, d=6.5, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, 52.474874], [0, 0, 1, 13], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, 52.474874], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=3, d=6.5, $fn=64);
}
