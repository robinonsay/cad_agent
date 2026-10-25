// assembly: printed bodies in the closed pose; references are % ghosts (never printed)
color("#4f81bd") {
  // body base
  difference() {
    union() {
      // body base (tray)
      multmatrix([[1, 0, 0, 40], [0, 1, 0, 20], [0, 0, 1, -8.1], [0, 0, 0, 1]]) difference() { translate([-43.5, -23.5, 0]) cube([87, 47, 33.3]); translate([0, 0, 2.4]) translate([-41.1, -21.1, 0]) cube([82.2, 42.2, 31.9]); }
      // add standoff_1 (standoff)
      multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
      // add standoff_2 (standoff)
      multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
      // add standoff_3 (standoff)
      multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 37.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
      // add standoff_4 (standoff)
      multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 37.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
      // add boss_1 (boss)
      multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.1, $fn=64);
      // add boss_2 (boss)
      multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, -3.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.1, $fn=64);
      // add boss_3 (boss)
      multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 43.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.1, $fn=64);
      // add boss_4 (boss)
      multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, 43.110229], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=33.3, d=6.1, $fn=64);
    }
    // cut connector_1_1_cut (port_cut)
    multmatrix([[0, 0, 1, 80.1], [0, 1, 0, 20.140011], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
    // cut standoff_1_pilot (pilot)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
    // cut standoff_2_pilot (pilot)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 2.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
    // cut standoff_3_pilot (pilot)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 37.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
    // cut standoff_4_pilot (pilot)
    multmatrix([[1, 0, 0, 77.5], [0, 1, 0, 37.5], [0, 0, 1, -6.7], [0, 0, 0, 1]]) cylinder(h=6.1, d=2.102533, $fn=64);
    // cut boss_1_pilot (pilot)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 19.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
    // cut boss_2_pilot (pilot)
    multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, -3.110229], [0, 0, 1, 19.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
    // cut boss_3_pilot (pilot)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 43.110229], [0, 0, 1, 19.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
    // cut boss_4_pilot (pilot)
    multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, 43.110229], [0, 0, 1, 19.1], [0, 0, 0, 1]]) cylinder(h=7.1, d=2.503015, $fn=64);
  }
}
color("#c0504d") {
  // body lid
  difference() {
    union() {
      // body lid (lid_plate)
      multmatrix([[1, 0, 0, 40], [0, 1, 0, 20], [0, 0, 1, 25.2], [0, 0, 0, 1]]) translate([-43.5, -23.5, 0]) cube([87, 47, 2.4]);
      // add lid_lip (lip)
      multmatrix([[1, 0, 0, 40], [0, 1, 0, 20], [0, 0, 1, 23.1], [0, 0, 0, 1]]) difference() { translate([-40.85, -20.85, 0]) cube([81.7, 41.7, 4.5]); translate([0, 0, -1]) translate([-39.65, -19.65, 0]) cube([79.3, 39.3, 6.5]); }
      // add boss_1_pad (pad)
      multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
      // add boss_2_pad (pad)
      multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, -3.110229], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
      // add boss_3_pad (pad)
      multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 43.110229], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
      // add boss_4_pad (pad)
      multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, 43.110229], [0, 0, 1, 25.2], [0, 0, 0, 1]]) cylinder(h=2.4, d=6.1, $fn=64);
    }
    // cut boss_1_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_1_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, -3.110229], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
    // cut boss_2_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, -3.110229], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_2_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, -3.110229], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
    // cut boss_3_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 43.110229], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_3_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, -3.110229], [0, 1, 0, 43.110229], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
    // cut boss_4_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, 43.110229], [0, 0, 1, 24.2], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_4_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, 83.110229], [0, 1, 0, 43.110229], [0, 0, 1, 22.1], [0, 0, 0, 1]]) cylinder(h=3.1, d=6.60796, $fn=64);
  }
}
%color("#7f7f7f") multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.6], [0, 0, 0, 1]]) cube([80, 40, 1.6]); } // ghost board
%color("#7f7f7f") multmatrix([[1, 0, 0, 68], [0, 1, 0, 17.140011], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([12, 6, 5]); } // ghost connector_1_1
%color("#7f7f7f") multmatrix([[1, 0, 0, 15.3], [0, 1, 0, 9.5], [0, 0, 1, 8.5], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([51, 21, 1]); multmatrix([[1, 0, 0, -1.3], [0, 1, 0, 6.5], [0, 0, 1, 1], [0, 0, 0, 1]]) cube([5.5, 8, 2.8]); } // ghost module_1_1
%color("#7f7f7f") multmatrix([[1, 0, 0, 16.67], [0, 1, 0, 11.11], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 8.5]); } // ghost module_1_1_stack_1
%color("#7f7f7f") multmatrix([[1, 0, 0, 16.67], [0, 1, 0, 28.89], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 8.5]); } // ghost module_1_1_stack_2
%color("#7f7f7f") multmatrix([[1, 0, 0, 9], [0, 1, 0, 20], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cylinder(h=20, d=10, $fn=64); } // ghost generic_1_1
