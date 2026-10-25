// render file: printed bodies, closed pose
// body base
difference() {
  color("#4f81bd") union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, -7.6], [0, 0, 0, 1]]) difference() { translate([-36, -18.45, 0]) cube([72, 36.9, 19.4]); translate([0, 0, 2.4]) translate([-33.6, -16.05, 0]) cube([67.2, 32.1, 18]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 3.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 3.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 26.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 26.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, -3.333452], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=19.4, d=5.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, -3.333452], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=19.4, d=5.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, 32.433452], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=19.4, d=5.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, 32.433452], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=19.4, d=5.6, $fn=64);
  }
  // cut board_usb_data_cut (port_cut)
  multmatrix([[0, 1, 0, 41.4], [-1, 0, 0, -2.7], [0, 0, 1, -1.2], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut board_usb_power_cut (port_cut)
  multmatrix([[0, 1, 0, 54], [-1, 0, 0, -2.7], [0, 0, 1, -1.2], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 3.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 3.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 26.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 26.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, -3.333452], [0, 0, 1, 6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, -3.333452], [0, 0, 1, 6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, 32.433452], [0, 0, 1, 6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, 32.433452], [0, 0, 1, 6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
}

// body lid
difference() {
  color("#c0504d") union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, 11.8], [0, 0, 0, 1]]) translate([-36, -18.45, 0]) cube([72, 36.9, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, 9.7], [0, 0, 0, 1]]) difference() { translate([-33.35, -15.8, 0]) cube([66.7, 31.6, 4.5]); translate([0, 0, -1]) translate([-32.15, -14.6, 0]) cube([64.3, 29.2, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, -3.333452], [0, 0, 1, 11.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, -3.333452], [0, 0, 1, 11.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, 32.433452], [0, 0, 1, 11.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, 32.433452], [0, 0, 1, 11.8], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, -3.333452], [0, 0, 1, 10.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, -3.333452], [0, 0, 1, 8.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, -3.333452], [0, 0, 1, 10.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, -3.333452], [0, 0, 1, 8.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, 32.433452], [0, 0, 1, 10.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.433452], [0, 1, 0, 32.433452], [0, 0, 1, 8.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, 32.433452], [0, 0, 1, 10.8], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 67.433452], [0, 1, 0, 32.433452], [0, 0, 1, 8.7], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
}

