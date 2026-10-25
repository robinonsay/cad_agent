// body base
difference() {
  union() {
    // body base (tray)
    multmatrix([[1, 0, 0, 32], [0, 1, 0, 14.55], [0, 0, 1, -7.6], [0, 0, 0, 1]]) difference() { translate([-36, -18.45, 0]) cube([72, 36.9, 16.6]); translate([0, 0, 2.4]) translate([-33.6, -16.05, 0]) cube([67.2, 32.1, 15.2]); }
    // add standoff_1 (standoff)
    multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 3.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add standoff_2 (standoff)
    multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 3.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add standoff_3 (standoff)
    multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 26.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add standoff_4 (standoff)
    multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 26.5], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=7.6, d=5.3, $fn=64);
    // add boss_1 (boss)
    multmatrix([[1, 0, 0, -3.610229], [0, 1, 0, -3.510229], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=16.6, d=6.1, $fn=64);
    // add boss_2 (boss)
    multmatrix([[1, 0, 0, 67.610229], [0, 1, 0, -3.510229], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=16.6, d=6.1, $fn=64);
    // add boss_3 (boss)
    multmatrix([[1, 0, 0, -3.610229], [0, 1, 0, 32.610229], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=16.6, d=6.1, $fn=64);
    // add boss_4 (boss)
    multmatrix([[1, 0, 0, 67.610229], [0, 1, 0, 32.610229], [0, 0, 1, -7.6], [0, 0, 0, 1]]) cylinder(h=16.6, d=6.1, $fn=64);
  }
  // cut board_hdmi_cut (port_cut)
  multmatrix([[0, 1, 0, 12.4], [-1, 0, 0, -2.7], [0, 0, 1, -1.4], [0, 0, 0, 1]]) translate([-2.2, -8.9, 0]) cube([4.4, 17.8, 8.8]);
  // cut board_usb_data_cut (port_cut)
  multmatrix([[0, 1, 0, 41.4], [-1, 0, 0, -2.7], [0, 0, 1, -1.2], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut board_usb_power_cut (port_cut)
  multmatrix([[0, 1, 0, 54], [-1, 0, 0, -2.7], [0, 0, 1, -1.2], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
  // cut board_sd_cut (port_cut)
  multmatrix([[-1, 0, 0, -2.8], [0, -1, 0, 16.9], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([-2.2, -6.4, 0]) cube([4.4, 12.8, 6.2]);
  // cut standoff_1_pilot (pilot)
  multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 3.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut standoff_2_pilot (pilot)
  multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 3.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut standoff_3_pilot (pilot)
  multmatrix([[1, 0, 0, 3.5], [0, 1, 0, 26.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut standoff_4_pilot (pilot)
  multmatrix([[1, 0, 0, 61.5], [0, 1, 0, 26.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=7.7, d=2.102533, $fn=64);
  // cut boss_1_pilot (pilot)
  multmatrix([[1, 0, 0, -3.610229], [0, 1, 0, -3.510229], [0, 0, 1, 3.3], [0, 0, 0, 1]]) cylinder(h=6.7, d=2.102533, $fn=64);
  // cut boss_2_pilot (pilot)
  multmatrix([[1, 0, 0, 67.610229], [0, 1, 0, -3.510229], [0, 0, 1, 3.3], [0, 0, 0, 1]]) cylinder(h=6.7, d=2.102533, $fn=64);
  // cut boss_3_pilot (pilot)
  multmatrix([[1, 0, 0, -3.610229], [0, 1, 0, 32.610229], [0, 0, 1, 3.3], [0, 0, 0, 1]]) cylinder(h=6.7, d=2.102533, $fn=64);
  // cut boss_4_pilot (pilot)
  multmatrix([[1, 0, 0, 67.610229], [0, 1, 0, 32.610229], [0, 0, 1, 3.3], [0, 0, 0, 1]]) cylinder(h=6.7, d=2.102533, $fn=64);
}
