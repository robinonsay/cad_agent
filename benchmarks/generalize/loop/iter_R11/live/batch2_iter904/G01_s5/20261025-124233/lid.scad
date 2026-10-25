// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 22.15], [0, 1, 0, 9], [0, 0, 1, 10], [0, 0, 0, 1]]) translate([-25.85, -12, 0]) cube([51.7, 24, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 22.15], [0, 1, 0, 9], [0, 0, 1, 7.9], [0, 0, 0, 1]]) difference() { translate([-23.2, -9.35, 0]) cube([46.4, 18.7, 4.5]); translate([0, 0, -1]) translate([-22, -8.15, 0]) cube([44, 16.3, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.487006], [0, 1, 0, -2.787006], [0, 0, 1, 10], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 47.787006], [0, 1, 0, -2.787006], [0, 0, 1, 10], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.487006], [0, 1, 0, 20.787006], [0, 0, 1, 10], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 47.787006], [0, 1, 0, 20.787006], [0, 0, 1, 10], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.487006], [0, 1, 0, -2.787006], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.487006], [0, 1, 0, -2.787006], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 47.787006], [0, 1, 0, -2.787006], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 47.787006], [0, 1, 0, -2.787006], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.487006], [0, 1, 0, 20.787006], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.487006], [0, 1, 0, 20.787006], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 47.787006], [0, 1, 0, 20.787006], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 47.787006], [0, 1, 0, 20.787006], [0, 0, 1, 6.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut control_1_1_panel_hole (panel_hole)
  multmatrix([[1, 0, 0, 22.35], [0, 1, 0, 9.05], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=5.506633, $fn=64);
  // cut control_1_2_panel_hole (panel_hole)
  multmatrix([[1, 0, 0, 16.35], [0, 1, 0, 9.05], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=5.506633, $fn=64);
  // cut control_1_3_panel_hole (panel_hole)
  multmatrix([[1, 0, 0, 28.35], [0, 1, 0, 9.05], [0, 0, 1, 9], [0, 0, 0, 1]]) cylinder(h=4.4, d=5.506633, $fn=64);
}
