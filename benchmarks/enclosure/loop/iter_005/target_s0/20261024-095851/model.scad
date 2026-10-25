// assembly: printed bodies in the closed pose; references are % ghosts (never printed)
color("#4f81bd") {
  // body base
  difference() {
    union() {
      // body base (tray)
      multmatrix([[1, 0, 0, 34.6], [0, 1, 0, 25], [0, 0, 1, -8.1], [0, 0, 0, 1]]) difference() { translate([-38.9, -28.5, 0]) cube([77.8, 57, 22.2]); translate([0, 0, 2.4]) translate([-36.5, -26.1, 0]) cube([73, 52.2, 20.8]); }
      // add standoff_1 (standoff)
      multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
      // add standoff_2 (standoff)
      multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 2.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
      // add standoff_3 (standoff)
      multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 47.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
      // add standoff_4 (standoff)
      multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 47.5], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=6.5, d=5.3, $fn=64);
      // add boss_1 (boss)
      multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, -3.074874], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.2, d=6, $fn=64);
      // add boss_2 (boss)
      multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, -3.074874], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.2, d=6, $fn=64);
      // add boss_3 (boss)
      multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, 53.074874], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.2, d=6, $fn=64);
      // add boss_4 (boss)
      multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, 53.074874], [0, 0, 1, -8.1], [0, 0, 0, 1]]) cylinder(h=22.2, d=6, $fn=64);
    }
    // cut module_1_1_cut (port_cut)
    multmatrix([[-1, 0, 0, -3.1], [0, -1, 0, 24.09], [0, 0, 1, 1], [0, 0, 0, 1]]) translate([-2.2, -5.4, 0]) cube([4.4, 10.8, 7.8]);
    // cut connector_1_1_cut (port_cut)
    multmatrix([[0, 0, 1, 70.1], [0, 1, 0, 17.666667], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
    // cut connector_1_2_cut (port_cut)
    multmatrix([[0, 0, 1, 70.1], [0, 1, 0, 32.333333], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.810613, $fn=64);
    // cut standoff_1_pilot (pilot)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.102533, $fn=64);
    // cut standoff_2_pilot (pilot)
    multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 2.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.102533, $fn=64);
    // cut standoff_3_pilot (pilot)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 47.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.102533, $fn=64);
    // cut standoff_4_pilot (pilot)
    multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 47.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.102533, $fn=64);
    // cut boss_1_pilot (pilot)
    multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, -3.074874], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7, d=2.503015, $fn=64);
    // cut boss_2_pilot (pilot)
    multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, -3.074874], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7, d=2.503015, $fn=64);
    // cut boss_3_pilot (pilot)
    multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, 53.074874], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7, d=2.503015, $fn=64);
    // cut boss_4_pilot (pilot)
    multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, 53.074874], [0, 0, 1, 8.1], [0, 0, 0, 1]]) cylinder(h=7, d=2.503015, $fn=64);
  }
}
color("#c0504d") {
  // body lid
  difference() {
    union() {
      // body lid (lid_plate)
      multmatrix([[1, 0, 0, 34.6], [0, 1, 0, 25], [0, 0, 1, 14.1], [0, 0, 0, 1]]) translate([-38.9, -28.5, 0]) cube([77.8, 57, 2.4]);
      // add lid_lip (lip)
      multmatrix([[1, 0, 0, 34.6], [0, 1, 0, 25], [0, 0, 1, 12.1], [0, 0, 0, 1]]) difference() { translate([-36.25, -25.85, 0]) cube([72.5, 51.7, 4.4]); translate([0, 0, -1]) translate([-35.05, -24.65, 0]) cube([70.1, 49.3, 6.4]); }
      // add boss_1_pad (pad)
      multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, -3.074874], [0, 0, 1, 14.1], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
      // add boss_2_pad (pad)
      multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, -3.074874], [0, 0, 1, 14.1], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
      // add boss_3_pad (pad)
      multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, 53.074874], [0, 0, 1, 14.1], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
      // add boss_4_pad (pad)
      multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, 53.074874], [0, 0, 1, 14.1], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
    }
    // cut boss_1_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, -3.074874], [0, 0, 1, 13.1], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_1_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, -3.074874], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3, d=6.507839, $fn=64);
    // cut boss_2_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, -3.074874], [0, 0, 1, 13.1], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_2_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, -3.074874], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3, d=6.507839, $fn=64);
    // cut boss_3_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, 53.074874], [0, 0, 1, 13.1], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_3_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, -3.874874], [0, 1, 0, 53.074874], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3, d=6.507839, $fn=64);
    // cut boss_4_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, 53.074874], [0, 0, 1, 13.1], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
    // cut boss_4_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, 73.074874], [0, 1, 0, 53.074874], [0, 0, 1, 11.1], [0, 0, 0, 1]]) cylinder(h=3, d=6.507839, $fn=64);
  }
}
%color("#7f7f7f") multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.6], [0, 0, 0, 1]]) cube([70, 50, 1.6]); } // ghost board
%color("#7f7f7f") multmatrix([[1, 0, 0, 0], [0, 1, 0, 13.59], [0, 0, 1, 2.5], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([51, 21, 1]); multmatrix([[1, 0, 0, -1.3], [0, 1, 0, 6.5], [0, 0, 1, 1], [0, 0, 0, 1]]) cube([5.5, 8, 2.8]); } // ghost module_1_1
%color("#7f7f7f") multmatrix([[1, 0, 0, 1.37], [0, 1, 0, 15.2], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 2.5]); } // ghost module_1_1_stack_1
%color("#7f7f7f") multmatrix([[1, 0, 0, 1.37], [0, 1, 0, 32.98], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 2.5]); } // ghost module_1_1_stack_2
%color("#7f7f7f") multmatrix([[1, 0, 0, 58], [0, 1, 0, 14.666667], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([12, 6, 5]); } // ghost connector_1_1
%color("#7f7f7f") multmatrix([[1, 0, 0, 58], [0, 1, 0, 29.333333], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([12, 6, 5]); } // ghost connector_1_2
