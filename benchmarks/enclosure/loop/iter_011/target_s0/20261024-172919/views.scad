// render file: printed bodies, closed pose
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 25], [0, 0, 1, -8.1], [0, 0, 0, 1]]) difference() { translate([-39, -29, 0]) cube([78, 58, 22.3]); translate([0, 0, 2.4]) translate([-36.6, -26.6, 0]) cube([73.2, 53.2, 20.9]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2], [0, 1, 0, 2], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 68], [0, 1, 0, 2], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2], [0, 1, 0, 48], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 68], [0, 1, 0, 48], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.1, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, -3.787006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 53.787006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, 53.787006], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.6, $fn=64);
  }
  // cut module_1_1_cut (port_cut)
  multmatrix([[-1, 0, 0, -2.8], [0, -1, 0, 25], [0, 0, 1, 1], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut connector_1_1_cut (port_cut)
  multmatrix([[0, 0, 1, 70.6], [0, 1, 0, 17.5], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut connector_1_2_cut (port_cut)
  multmatrix([[0, 0, 1, 70.6], [0, 1, 0, 32.5], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2], [0, 1, 0, 2], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 68], [0, 1, 0, 2], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2], [0, 1, 0, 48], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 68], [0, 1, 0, 48], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, -3.787006], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 53.787006], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, 53.787006], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
}

// body lid
difference() {
  color("#c0504d") union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 25], [0, 0, 1, 14.2], [0, 0, 0, 1]]) translate([-39, -29, 0]) cube([78, 58, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 25], [0, 0, 1, 12.1], [0, 0, 0, 1]]) difference() { translate([-36.35, -26.35, 0]) cube([72.7, 52.7, 4.5]); translate([0, 0, -1]) translate([-35.15, -25.15, 0]) cube([70.3, 50.3, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, -3.787006], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 53.787006], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, 53.787006], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, -3.787006], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, -3.787006], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, -3.787006], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 53.787006], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.787006], [0, 1, 0, 53.787006], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, 53.787006], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 73.787006], [0, 1, 0, 53.787006], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=7.108563, $fn=64);
}

