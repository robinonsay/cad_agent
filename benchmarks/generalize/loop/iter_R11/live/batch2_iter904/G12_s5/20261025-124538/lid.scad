// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 26.7], [0, 1, 0, 13.95], [0, 0, 1, 15], [0, 0, 0, 1]]) translate([-33.2, -19.47, 0]) cube([66.4, 38.94, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 26.7], [0, 1, 0, 13.95], [0, 0, 1, 12.9], [0, 0, 0, 1]]) difference() { translate([-30.55, -16.82, 0]) cube([61.1, 33.64, 4.5]); translate([0, 0, -1]) translate([-29.35, -15.62, 0]) cube([58.7, 31.24, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, -4.574773], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, -4.574773], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, 32.474773], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, 32.474773], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, -4.574773], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, -4.574773], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, -4.574773], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, -4.574773], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, 32.474773], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -5.554773], [0, 1, 0, 32.474773], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, 32.474773], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 58.954773], [0, 1, 0, 32.474773], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut control_1_1_panel_hole (panel_hole)
  multmatrix([[1, 0, 0, 26.55], [0, 1, 0, 14.03], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=5.506633, $fn=64);
  // cut control_1_2_panel_hole (panel_hole)
  multmatrix([[1, 0, 0, 32.55], [0, 1, 0, 14.03], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=5.506633, $fn=64);
  // cut control_1_3_panel_hole (panel_hole)
  multmatrix([[1, 0, 0, 26.55], [0, 1, 0, 8.03], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=5.506633, $fn=64);
}
