// render file: printed bodies, closed pose
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 25], [0, 0, 1, -8.1], [0, 0, 0, 1]]) difference() { translate([-38.5, -28.5, 0]) cube([77, 57, 22.3]); translate([0, 0, 2.4]) translate([-36.1, -26.1, 0]) cube([72.2, 52.2, 20.9]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 47.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 47.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.1, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, -3.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.1, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 53.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.1, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, 53.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.3, d=6.1, $fn=64);
  }
  // cut connector_1_1_cut (port_cut)
  multmatrix([[0, 0, 1, 70.1], [0, 1, 0, 17.600011], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut connector_1_2_cut (port_cut)
  multmatrix([[0, 0, 1, 70.1], [0, 1, 0, 32.840011], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 47.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 47.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, -3.110229], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 53.110229], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, 53.110229], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
}

// body lid
difference() {
  color("#c0504d") union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 25], [0, 0, 1, 14.2], [0, 0, 0, 1]]) translate([-38.5, -28.5, 0]) cube([77, 57, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 35], [0, 1, 0, 25], [0, 0, 1, 12.1], [0, 0, 0, 1]]) difference() { translate([-35.85, -25.85, 0]) cube([71.7, 51.7, 4.5]); translate([0, 0, -1]) translate([-34.65, -24.65, 0]) cube([69.3, 49.3, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, -3.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 53.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, 53.110229], [0, 0, 1, 14.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, -3.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, -3.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 53.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 53.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, 53.110229], [0, 0, 1, 13.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 73.110229], [0, 1, 0, 53.110229], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
}

