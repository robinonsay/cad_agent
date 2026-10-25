// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, 8.6], [0, 0, 0, 1]]) translate([-36, -18.45, 0]) cube([72, 36.9, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, 6.5], [0, 0, 0, 1]]) difference() { translate([-33.35, -15.8, 0]) cube([66.7, 31.6, 4.5]); translate([0, 0, -1]) translate([-32.15, -14.6, 0]) cube([64.3, 29.2, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, -3.333452], [0, 0, 1, 8.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, -3.333452], [0, 0, 1, 8.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, 32.433452], [0, 0, 1, 8.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, 32.433452], [0, 0, 1, 8.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, -3.333452], [0, 0, 1, 7.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, -3.333452], [0, 0, 1, 5.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, -3.333452], [0, 0, 1, 7.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, -3.333452], [0, 0, 1, 5.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, 32.433452], [0, 0, 1, 7.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, 32.433452], [0, 0, 1, 5.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, 32.433452], [0, 0, 1, 7.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, 32.433452], [0, 0, 1, 5.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
}
