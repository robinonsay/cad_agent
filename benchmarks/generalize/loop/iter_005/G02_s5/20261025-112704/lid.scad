// body lid
difference() {
  union() {
    // body lid (lid_plate)
    multmatrix([[1, 0, 0, 31.8], [0, 1, 0, 26.6], [0, 0, 1, 16.55], [0, 0, 0, 1]]) translate([-46.25, -28.85, 0]) cube([92.5, 57.7, 2.4]);
  }
  // cut boss_1_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -10.6], [0, 1, 0, 16.907115], [0, 0, 1, 15.55], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_2_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 74.2], [0, 1, 0, 1.6], [0, 0, 1, 15.55], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_3_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, -10.6], [0, 1, 0, 51.6], [0, 0, 1, 15.55], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut boss_4_lid_hole (screw_hole)
  multmatrix([[1, 0, 0, 74.2], [0, 1, 0, 51.6], [0, 0, 1, 15.55], [0, 0, 0, 1]]) cylinder(h=4.4, d=3.4041, $fn=64);
  // cut vent_1 (vent_cut)
  multmatrix([[1, 0, 0, 32], [0, 1, 0, 18], [0, 0, 1, 15.55], [0, 0, 0, 1]]) translate([-1, -5, 0]) cube([2, 10, 4.4]);
  // cut vent_2 (vent_cut)
  multmatrix([[1, 0, 0, 36], [0, 1, 0, 18], [0, 0, 1, 15.55], [0, 0, 0, 1]]) translate([-1, -5, 0]) cube([2, 10, 4.4]);
  // cut vent_3 (vent_cut)
  multmatrix([[1, 0, 0, 40], [0, 1, 0, 18], [0, 0, 1, 15.55], [0, 0, 0, 1]]) translate([-1, -5, 0]) cube([2, 10, 4.4]);
  // cut vent_4 (vent_cut)
  multmatrix([[1, 0, 0, 44], [0, 1, 0, 18], [0, 0, 1, 15.55], [0, 0, 0, 1]]) translate([-1, -5, 0]) cube([2, 10, 4.4]);
  // cut vent_5 (vent_cut)
  multmatrix([[1, 0, 0, 48], [0, 1, 0, 18], [0, 0, 1, 15.55], [0, 0, 0, 1]]) translate([-1, -5, 0]) cube([2, 10, 4.4]);
  // cut vent_6 (vent_cut)
  multmatrix([[1, 0, 0, 52], [0, 1, 0, 18], [0, 0, 1, 15.55], [0, 0, 0, 1]]) translate([-1, -5, 0]) cube([2, 10, 4.4]);
  // cut vent_7 (vent_cut)
  multmatrix([[1, 0, 0, 56], [0, 1, 0, 18], [0, 0, 1, 15.55], [0, 0, 0, 1]]) translate([-1, -5, 0]) cube([2, 10, 4.4]);
  // cut vent_8 (vent_cut)
  multmatrix([[1, 0, 0, 60], [0, 1, 0, 18], [0, 0, 1, 15.55], [0, 0, 0, 1]]) translate([-1, -5, 0]) cube([2, 10, 4.4]);
  // cut vent_9 (vent_cut)
  multmatrix([[1, 0, 0, 64], [0, 1, 0, 18], [0, 0, 1, 15.55], [0, 0, 0, 1]]) translate([-1, -5, 0]) cube([2, 10, 4.4]);
}
