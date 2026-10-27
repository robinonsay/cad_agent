// body nut_frame
difference() {
  union() {
    // body nut_frame (nut_frame)
    multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 2.1], [0, 0, 0, 1]]) linear_extrude(height=4.7) polygon(points=[[-15.349742, -7.2], [15.349742, -7.2], [15.349742, 7.2], [-15.349742, 7.2]]);
  }
  // cut frame_trap_0 (nut_trap)
  multmatrix([[1, 0, 0, -7.5], [0, 1, 0, 0], [0, 0, 1, 1.1], [0, 0, 0, 1]]) linear_extrude(height=6.7) polygon(points=[[-4.849742, 0], [-2.424871, -4.2], [2.424871, -4.2], [4.849742, 0], [2.424871, 4.2], [-2.424871, 4.2]]);
  // cut frame_trap_1 (nut_trap)
  multmatrix([[1, 0, 0, 7.5], [0, 1, 0, 0], [0, 0, 1, 1.1], [0, 0, 0, 1]]) linear_extrude(height=6.7) polygon(points=[[-4.849742, 0], [-2.424871, -4.2], [2.424871, -4.2], [4.849742, 0], [2.424871, 4.2], [-2.424871, 4.2]]);
}
