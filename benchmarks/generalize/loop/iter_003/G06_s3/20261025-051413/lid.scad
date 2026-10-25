// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 18], [0, 0, 1, 15.7], [0, 0, 0, 1]]) translate([-43, -21, 0]) cube([86, 42, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 40], [0, 1, 0, 18], [0, 0, 1, 13.6], [0, 0, 0, 1]]) difference() { translate([-40.35, -18.35, 0]) cube([80.7, 36.7, 4.5]); translate([0, 0, -1]) translate([-39.15, -17.15, 0]) cube([78.3, 34.3, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -2.433452], [0, 1, 0, -2.433452], [0, 0, 1, 15.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 82.433452], [0, 1, 0, -2.433452], [0, 0, 1, 15.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -2.433452], [0, 1, 0, 38.433452], [0, 0, 1, 15.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 82.433452], [0, 1, 0, 38.433452], [0, 0, 1, 15.7], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -2.433452], [0, 1, 0, -2.433452], [0, 0, 1, 14.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -2.433452], [0, 1, 0, -2.433452], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 82.433452], [0, 1, 0, -2.433452], [0, 0, 1, 14.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 82.433452], [0, 1, 0, -2.433452], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -2.433452], [0, 1, 0, 38.433452], [0, 0, 1, 14.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -2.433452], [0, 1, 0, 38.433452], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 82.433452], [0, 1, 0, 38.433452], [0, 0, 1, 14.7], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 82.433452], [0, 1, 0, 38.433452], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
}
