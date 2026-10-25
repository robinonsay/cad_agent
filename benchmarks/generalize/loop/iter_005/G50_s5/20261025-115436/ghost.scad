// render file: printed bodies, closed pose; references drawn solid
color("#9bbb59") multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([65, 30, 1.4]); multmatrix([[1, 0, 0, 6.8], [0, 1, 0, -0.5], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([11.2, 7.5, 3.2]); multmatrix([[1, 0, 0, 37.65], [0, 1, 0, -0.9], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([7.5, 5.9, 2.6]); multmatrix([[1, 0, 0, 50.25], [0, 1, 0, -0.9], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([7.5, 5.9, 2.6]); multmatrix([[1, 0, 0, -1], [0, 1, 0, 10.9], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([14, 12, 1.4]); } // reference board
// body base
difference() {
  color("#4f81bd", 0.3) union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, -7.6], [0, 0, 0, 1]]) difference() { translate([-35.7, -18.15, 0]) cube([71.4, 36.3, 21.2]); translate([0, 0, 2.4]) translate([-33.3, -15.75, 0]) cube([66.6, 31.5, 19.8]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 3.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 3.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 26.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 26.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, -3.12132], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=21.2, d=5.6, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, -3.12132], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=21.2, d=5.6, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, 32.22132], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=21.2, d=5.6, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, 32.22132], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=21.2, d=5.6, $fn=64);
  }
  // cut board_usb_data_cut (port_cut)
  multmatrix([[0, 1, 0, 41.4], [-1, 0, 0, -2.4], [0, 0, 1, -1.2], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut board_usb_power_cut (port_cut)
  multmatrix([[0, 1, 0, 54], [-1, 0, 0, -2.4], [0, 0, 1, -1.2], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 3.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 3.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 26.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 26.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, -3.12132], [0, 0, 1, 8.5], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, -3.12132], [0, 0, 1, 8.5], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, 32.22132], [0, 0, 1, 8.5], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, 32.22132], [0, 0, 1, 8.5], [0, 0, 0, 1]]) cylinder(h=6.1, d=1.70205, $fn=64);
}

// body lid
difference() {
  color("#c0504d", 0.3) union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, 13.6], [0, 0, 0, 1]]) translate([-35.7, -18.15, 0]) cube([71.4, 36.3, 2.4]);
    // add lid_lip (lip)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, 11.5], [0, 0, 0, 1]]) difference() { translate([-33.05, -15.5, 0]) cube([66.1, 31, 4.5]); translate([0, 0, -1]) translate([-31.85, -14.3, 0]) cube([63.7, 28.6, 6.5]); }
    // add boss_1_pad (pad)
    multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, -3.12132], [0, 0, 1, 13.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_2_pad (pad)
    multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, -3.12132], [0, 0, 1, 13.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_3_pad (pad)
    multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, 32.22132], [0, 0, 1, 13.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
    // add boss_4_pad (pad)
    multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, 32.22132], [0, 0, 1, 13.6], [0, 0, 0, 1]]) cylinder(h=2.4, d=5.6, $fn=64);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, -3.12132], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_1_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, -3.12132], [0, 0, 1, 10.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, -3.12132], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_2_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, -3.12132], [0, 0, 1, 10.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, 32.22132], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_3_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, -3.22132], [0, 1, 0, 32.22132], [0, 0, 1, 10.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, 32.22132], [0, 0, 1, 12.6], [0, 0, 0, 1]]) cylinder(h=4.4, d=2.402894, $fn=64);
  // cut boss_4_lip_notch (lip_notch)
  multmatrix([[1, 0, 0, 67.22132], [0, 1, 0, 32.22132], [0, 0, 1, 10.5], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.107357, $fn=64);
}

