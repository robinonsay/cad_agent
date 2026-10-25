// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, 9], [0, 0, 0, 1]]) translate([-42.7, -18.45, 0]) cube([85.4, 36.9, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, 6.9], [0, 0, 0, 1]]) difference() { translate([-40.05, -15.8, 0]) cube([80.1, 31.6, 4.5]); translate([0, 0, -1]) translate([-38.85, -14.6, 0]) cube([77.7, 29.2, 6.5]); }
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -5.35], [0, 1, 0, 1.45], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.903497, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -5.35], [0, 1, 0, 1.45], [0, 0, 1, 5.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 69.35], [0, 1, 0, 1.45], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.903497, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 69.35], [0, 1, 0, 1.45], [0, 0, 1, 5.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -5.35], [0, 1, 0, 27.65], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.903497, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -5.35], [0, 1, 0, 27.65], [0, 0, 1, 5.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 69.35], [0, 1, 0, 27.65], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.903497, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 69.35], [0, 1, 0, 27.65], [0, 0, 1, 5.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
}
