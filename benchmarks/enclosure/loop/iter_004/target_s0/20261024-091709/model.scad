// assembly: printed bodies in the closed pose; references are % ghosts (never printed)
color("#4f81bd") {
  // body base
  difference() {
    union() {
      // body base (tray)
      multmatrix([[1, 0, 0, 34.35], [0, 1, 0, 25], [0, 0, 1, -8], [0, 0, 0, 1]]) difference() { translate([-38.55, -27.9, 0]) cube([77.1, 55.8, 22]); translate([0, 0, 2.4]) translate([-36.15, -25.5, 0]) cube([72.3, 51, 20.6]); }
      // add standoff_1 (standoff)
      multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=6.4, d=5.3, $fn=64);
      // add standoff_2 (standoff)
      multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 2.5], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=6.4, d=5.3, $fn=64);
      // add standoff_3 (standoff)
      multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 47.5], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=6.4, d=5.3, $fn=64);
      // add standoff_4 (standoff)
      multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 47.5], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=6.4, d=5.3, $fn=64);
      // add boss_1 (boss)
      multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, -2.474874], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=22, d=6, $fn=64);
      // add boss_2 (boss)
      multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, -2.474874], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=22, d=6, $fn=64);
      // add boss_3 (boss)
      multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, 52.474874], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=22, d=6, $fn=64);
      // add boss_4 (boss)
      multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, 52.474874], [0, 0, 1, -8], [0, 0, 0, 1]]) cylinder(h=22, d=6, $fn=64);
    }
    // cut module_1_1_cut (port_cut)
    multmatrix([[-1, 0, 0, -3], [0, -1, 0, 24.09], [0, 0, 1, 1.1], [0, 0, 0, 1]]) translate([-2.2, -5.3, 0]) cube([4.4, 10.6, 7.6]);
    // cut connector_1_1_cut (port_cut)
    multmatrix([[0, 0, 1, 69.5], [0, 1, 0, 17.666667], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.6, $fn=64);
    // cut connector_1_2_cut (port_cut)
    multmatrix([[0, 0, 1, 69.5], [0, 1, 0, 32.333333], [-1, 0, 0, 2.5], [0, 0, 0, 1]]) cylinder(h=4.4, d=8.6, $fn=64);
    // cut standoff_1_pilot (pilot)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 2.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.1, $fn=64);
    // cut standoff_2_pilot (pilot)
    multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 2.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.1, $fn=64);
    // cut standoff_3_pilot (pilot)
    multmatrix([[1, 0, 0, 2.5], [0, 1, 0, 47.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.1, $fn=64);
    // cut standoff_4_pilot (pilot)
    multmatrix([[1, 0, 0, 67.5], [0, 1, 0, 47.5], [0, 0, 1, -6.6], [0, 0, 0, 1]]) cylinder(h=6, d=2.1, $fn=64);
    // cut boss_1_pilot (pilot)
    multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, -2.474874], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=7, d=2.5, $fn=64);
    // cut boss_2_pilot (pilot)
    multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, -2.474874], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=7, d=2.5, $fn=64);
    // cut boss_3_pilot (pilot)
    multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, 52.474874], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=7, d=2.5, $fn=64);
    // cut boss_4_pilot (pilot)
    multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, 52.474874], [0, 0, 1, 8], [0, 0, 0, 1]]) cylinder(h=7, d=2.5, $fn=64);
  }
}
color("#c0504d") {
  // body lid
  difference() {
    union() {
      // body lid (lid_plate)
      multmatrix([[1, 0, 0, 34.35], [0, 1, 0, 25], [0, 0, 1, 14], [0, 0, 0, 1]]) translate([-38.55, -27.9, 0]) cube([77.1, 55.8, 2.4]);
      // add lid_lip (lip)
      multmatrix([[1, 0, 0, 34.35], [0, 1, 0, 25], [0, 0, 1, 12], [0, 0, 0, 1]]) difference() { translate([-35.9, -25.25, 0]) cube([71.8, 50.5, 4.4]); translate([0, 0, -1]) translate([-34.7, -24.05, 0]) cube([69.4, 48.1, 6.4]); }
      // add boss_1_pad (pad)
      multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, -2.474874], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
      // add boss_2_pad (pad)
      multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, -2.474874], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
      // add boss_3_pad (pad)
      multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, 52.474874], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
      // add boss_4_pad (pad)
      multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, 52.474874], [0, 0, 1, 14], [0, 0, 0, 1]]) cylinder(h=2.4, d=6, $fn=64);
    }
    // cut boss_1_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, -2.474874], [0, 0, 1, 13], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4, $fn=64);
    // cut boss_1_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, -2.474874], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=3, d=6.5, $fn=64);
    // cut boss_2_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, -2.474874], [0, 0, 1, 13], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4, $fn=64);
    // cut boss_2_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, -2.474874], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=3, d=6.5, $fn=64);
    // cut boss_3_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, 52.474874], [0, 0, 1, 13], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4, $fn=64);
    // cut boss_3_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, -3.774874], [0, 1, 0, 52.474874], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=3, d=6.5, $fn=64);
    // cut boss_4_lid_hole (screw_hole)
    multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, 52.474874], [0, 0, 1, 13], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4, $fn=64);
    // cut boss_4_lip_notch (lip_notch)
    multmatrix([[1, 0, 0, 72.474874], [0, 1, 0, 52.474874], [0, 0, 1, 11], [0, 0, 0, 1]]) cylinder(h=3, d=6.5, $fn=64);
  }
}
%color("#7f7f7f") multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.6], [0, 0, 0, 1]]) cube([70, 50, 1.6]); } // ghost board
%color("#7f7f7f") multmatrix([[1, 0, 0, 0], [0, 1, 0, 13.59], [0, 0, 1, 2.5], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([51, 21, 1]); multmatrix([[1, 0, 0, -1.3], [0, 1, 0, 6.5], [0, 0, 1, 1], [0, 0, 0, 1]]) cube([5.5, 8, 2.8]); } // ghost module_1_1
%color("#7f7f7f") multmatrix([[1, 0, 0, 1.37], [0, 1, 0, 15.2], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 2.5]); } // ghost module_1_1_stack_1
%color("#7f7f7f") multmatrix([[1, 0, 0, 1.37], [0, 1, 0, 32.98], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, -1.27], [0, 1, 0, -1.25], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([50.8, 2.5, 2.5]); } // ghost module_1_1_stack_2
%color("#7f7f7f") multmatrix([[1, 0, 0, 58], [0, 1, 0, 14.666667], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([12, 6, 5]); } // ghost connector_1_1
%color("#7f7f7f") multmatrix([[1, 0, 0, 58], [0, 1, 0, 29.333333], [0, 0, 1, 0], [0, 0, 0, 1]]) union() { multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) cube([12, 6, 5]); } // ghost connector_1_2
