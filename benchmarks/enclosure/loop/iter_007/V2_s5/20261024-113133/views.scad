// render file: printed bodies, closed pose
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 45], [0, 1, 0, 22.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) difference() { translate([-48.5, -26, 0]) cube([97, 52, 23.1]); translate([0, 0, 2.4]) translate([-46.1, -23.6, 0]) cube([92.2, 47.2, 21.7]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 87.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 42.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 87.5], [0, 1, 0, 42.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=23.1, d=6.1, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, -3.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=23.1, d=6.1, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 48.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=23.1, d=6.1, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, 48.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=23.1, d=6.1, $fn=64);
  }
  // cut connector_1_1_cut (port_cut)
  multmatrix([[1, 0, 0, 25.220011], [0, 0, -1, -0.1], [0, 1, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut connector_1_2_cut (port_cut)
  multmatrix([[1, 0, 0, 45.540011], [0, 0, -1, -0.1], [0, 1, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut connector_1_3_cut (port_cut)
  multmatrix([[1, 0, 0, 65.860011], [0, 0, -1, -0.1], [0, 1, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 87.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 42.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 87.5], [0, 1, 0, 42.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 8.9], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, -3.110229], [0, 0, 1, 8.9], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 48.110229], [0, 0, 1, 8.9], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, 48.110229], [0, 0, 1, 8.9], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
}

// body lid
difference() {
  color("#c0504d") union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 45], [0, 1, 0, 22.5], [0, 0, 1, 15], [0, 0, 0, 1]]) translate([-48.5, -26, 0]) cube([97, 52, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 45], [0, 1, 0, 22.5], [0, 0, 1, 12.9], [0, 0, 0, 1]]) difference() { translate([-45.85, -23.35, 0]) cube([91.7, 46.7, 4.5]); translate([0, 0, -1]) translate([-44.65, -22.15, 0]) cube([89.3, 44.3, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, -3.110229], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 48.110229], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, 48.110229], [0, 0, 1, 15], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, -3.110229], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, -3.110229], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 48.110229], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 48.110229], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, 48.110229], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 93.110229], [0, 1, 0, 48.110229], [0, 0, 1, 11.9], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
}

