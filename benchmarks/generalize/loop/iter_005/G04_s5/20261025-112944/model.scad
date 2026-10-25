// assembly: printed bodies in the closed pose; references are % ghosts (never printed)
color("#4f81bd") {
  // body base
  difference() {
    union() {
      // body base (tray)
      multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, -7.6], [0, 0, 0, 1]]) difference() { translate([-42.7, -18.45, 0]) cube([85.4, 36.9, 16.6]); translate([0, 0, 2.4]) translate([-40.3, -16.05, 0]) cube([80.6, 32.1, 15.2]); }
      // add standoff_1 (standoff)
      multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 3.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
      // add standoff_2 (standoff)
      multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 3.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
      // add standoff_3 (standoff)
      multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 26.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
      // add standoff_4 (standoff)
      multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 26.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
      // add boss_1 (boss)
      multmatrix([[1, 0, 0, -5.35], [0, 1, 0, 1.45], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=16.6, d=6.1, $fn=64);
      // add boss_2 (boss)
      multmatrix([[1, 0, 0, 69.35], [0, 1, 0, 1.45], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=16.6, d=6.1, $fn=64);
      // add boss_3 (boss)
      multmatrix([[1, 0, 0, -5.35], [0, 1, 0, 27.65], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=16.6, d=6.1, $fn=64);
      // add boss_4 (boss)
      multmatrix([[1, 0, 0, 69.35], [0, 1, 0, 27.65], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=16.6, d=6.1, $fn=64);
    }
    // cut board_hdmi_cut (port_cut)
    multmatrix([[0, 1, 0, 12.4], [-1, 0, 0, -2.7], [0, 0, 1, -1.4], [0, 0, 0, 1]]) translate([-2.2, -8.9, 0]) cube([4.4, 17.8, 8.8]);
    // cut board_usb_data_cut (port_cut)
    multmatrix([[0, 1, 0, 41.4], [-1, 0, 0, -2.7], [0, 0, 1, -1.2], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
    // cut board_usb_power_cut (port_cut)
    multmatrix([[0, 1, 0, 54], [-1, 0, 0, -2.7], [0, 0, 1, -1.2], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
    // cut board_sd_cut (port_cut)
    multmatrix([[-1, 0, 0, -9.5], [0, -1, 0, 16.9], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-2.2, -6.4, 0]) cube([4.4, 12.8, 6.2]);
    // cut standoff_1_pilot (pilot)
    multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 3.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
    // cut standoff_2_pilot (pilot)
    multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 3.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
    // cut standoff_3_pilot (pilot)
    multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 26.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
    // cut standoff_4_pilot (pilot)
    multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 26.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
    // cut boss_1_pilot (pilot)
    multmatrix([[1, 0, 0, -5.35], [0, 1, 0, 1.45], [0, 0, 1, 3.3], [0, 0, 0, 1]]) cylinder(h=6.7, d=2.102533, $fn=64);
    // cut boss_2_pilot (pilot)
    multmatrix([[1, 0, 0, 69.35], [0, 1, 0, 1.45], [0, 0, 1, 3.3], [0, 0, 0, 1]]) cylinder(h=6.7, d=2.102533, $fn=64);
    // cut boss_3_pilot (pilot)
    multmatrix([[1, 0, 0, -5.35], [0, 1, 0, 27.65], [0, 0, 1, 3.3], [0, 0, 0, 1]]) cylinder(h=6.7, d=2.102533, $fn=64);
    // cut boss_4_pilot (pilot)
    multmatrix([[1, 0, 0, 69.35], [0, 1, 0, 27.65], [0, 0, 1, 3.3], [0, 0, 0, 1]]) cylinder(h=6.7, d=2.102533, $fn=64);
  }
}
color("#c0504d") {
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
}
%color("#7f7f7f") multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([65, 30, 1.4]); multmatrix([[1, 0, 0, 6.8], [0, 1, 0, -0.5], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([11.2, 7.5, 3.2]); multmatrix([[1, 0, 0, 37.65], [0, 1, 0, -0.9], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([7.5, 5.9, 2.6]); multmatrix([[1, 0, 0, 50.25], [0, 1, 0, -0.9], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([7.5, 5.9, 2.6]); multmatrix([[1, 0, 0, -1], [0, 1, 0, 10.9], [0, 0, 1, 1.4], [0, 0, 0, 1]]) cube([14, 12, 1.4]); } // ghost board
