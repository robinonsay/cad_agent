"""Tests for assembly_checks.py (milestone M5 subset): synthetic manifold3d solids with known answers.

No Ollama, no OpenSCAD. Each check is tried at its boundary (+/- 0.02 mm), with the
margin compared to the analytic value, and the delivered-STL path is compared with
the manifold path.
"""

import tempfile
import unittest
from pathlib import Path

import manifold3d as m3d
import numpy as np

import assembly_checks as ac
import feature_graph as fg
import parts as pt

REPO = Path(__file__).parent
RULES = pt.load_rules(REPO / "design_rules.json").values
TOL = ac.Tol.from_rules(RULES)
M = m3d.Manifold
SEG = 48


def box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return M.cube((hi - lo).tolist()).translate(lo.tolist())


def cyl_x(y, z, d, x0, x1):
    """A cylinder along +X from x0 to x1 through (y, z)."""
    c = M.cylinder(x1 - x0, d / 2, d / 2, SEG)
    return c.transform(fg._m3(fg.matrix(fg.align_z_to([1, 0, 0]), [x0, y, z])))


class TestClearOf(unittest.TestCase):
    def test_boundary_and_margin(self):
        c = 0.5
        a = box([0, 0, 0], [10, 10, 10])
        for gap, ok in ((c + 0.02, True), (c - 0.02, False)):
            with self.subTest(gap=gap):
                v = box([10 + gap, 0, 0], [20, 10, 10])
                r = ac.clear_of(a, v, c, TOL)
                self.assertEqual(r.passed, ok)
                self.assertAlmostEqual(r.margin, (gap - c) / TOL.scale, delta=0.02)
                self.assertAlmostEqual(r.evidence["gap"], gap, places=6)

    def test_penetration_is_negative_with_its_location(self):
        a = box([0, 0, 0], [10, 10, 10])
        v = box([8, 2, 3], [12, 6, 7])
        r = ac.clear_of(a, v, 0.5, TOL)
        self.assertFalse(r.passed)
        self.assertLess(r.margin, 0)
        self.assertAlmostEqual(r.evidence["penetration_mm3"], 2 * 4 * 4, places=6)
        np.testing.assert_allclose(r.evidence["where"], [[8, 2, 3], [10, 6, 7]], atol=1e-6)

    def test_minus_removes_a_seat_column(self):
        a = box([0, 0, 0], [10, 10, 1])                 # a standoff top touching the board
        board = box([-5, -5, 1], [15, 15, 2])
        seat = M.cylinder(4, 8, 8, SEG).translate([5, 5, 0])
        self.assertFalse(ac.clear_of(a, board, 0.5, TOL).passed)
        self.assertTrue(ac.clear_of(a, board, 0.5, TOL, minus=seat).passed)


    def test_exemption_grown_by_clearance(self):
        # iteration 005 (RC-501): a peg touching the plate inside the exemption column is measured against the
        # column's rim unless the column is grown by the clearance; grown, the next real surface (a wall) counts
        D, OD, HOLE, c, w, fn = 7.0, 5.0, 3.0, 0.5, 1.1, 256
        rules = dict(RULES, fn=fn)
        plate = box([0, 0, 1], [20, 20, 2]) - M.cylinder(3, HOLE / 2, HOLE / 2, fn).translate([10, 10, 0])
        peg = M.cylinder(1, OD / 2, OD / 2, fn).translate([10, 10, 0])          # touches the plate underside
        wall = box([20 + w, -5, 0], [25, 25, 3])
        seat = fg.Node("seat", "envelope", "cylinder", {"d": D, "h": 4}, fg.Pose(offset=(10, 10, -1)))
        res = fg.FeatureGraph([seat]).resolve(rules=rules)
        bodies = peg + wall
        poly = 1 / np.cos(np.pi / fn)
        ungrown = ac.clear_of(bodies, plate, c, TOL, minus=fg.solid(seat, res))
        self.assertAlmostEqual(ungrown.evidence["gap"], (D - OD) / 2, delta=OD / 2 * (poly - 1) + 1e-4)
        grown = ac.clear_of(bodies, plate, c, TOL, minus=fg.grown_solid(seat, res, c))
        self.assertAlmostEqual(grown.evidence["gap"], min(w, (D + 2 * c - OD) / 2), delta=1e-4)
        self.assertAlmostEqual(grown.evidence["gap"], w, delta=1e-4)        # the wall is the nearer real surface

    def test_per_source_is_decomposable(self):
        # iteration 005 (RC-503): each member measured alone; the headline is the minimum of the members
        a = box([0, 0, 0], [10, 10, 10])
        near, far = box([10.7, 0, 0], [12, 4, 4]), box([12.5, 6, 0], [14, 10, 4])
        parts = {"near": near, "far": far}
        r = ac.clear_of(a, near + far, 0.5, TOL, parts=parts, labels={"near": "part_a", "far": "part_b"})
        per = r.evidence["per_source"]
        self.assertEqual(set(per), {"near", "far"})
        self.assertEqual(per["near"]["part"], "part_a")
        for k, v in parts.items():
            self.assertAlmostEqual(per[k]["d"], ac.clear_of(a, v, 0.5, TOL).evidence["gap"], delta=1e-6)
        self.assertAlmostEqual(r.evidence["gap"], min(x["d"] for x in per.values()), delta=1e-6)

    def test_bodies_subset_in_a_plan(self):
        # iteration 004: V-DRIVER is checked against the base only (lid off)
        column = box([0, 0, 0], [2, 2, 20])
        base_clear, base_hit = box([5, 0, 0], [10, 10, 5]), box([1, 1, 0], [10, 10, 5])
        lid_hit = box([-5, -5, 10], [10, 10, 12])
        plan = ac.Plan(tol=TOL, seg=SEG)
        plan.volumes["driver"] = column
        plan.add("clear_driver", "clear_of", "driver column clear of the base", volume="driver", clearance=0.0,
                 bodies=["base"])
        plan.add("clear_driver_all", "clear_of", "driver column clear of every body", volume="driver", clearance=0.0)
        ok, every = ac.run_plan(plan, {"base": base_clear, "lid": lid_hit})
        self.assertTrue(ok.passed, ok.evidence)              # the intruding lid is ignored
        self.assertFalse(every.passed)                       # ... but only because the check says base only
        bad, _ = ac.run_plan(plan, {"base": base_hit, "lid": lid_hit})
        self.assertFalse(bad.passed)
        self.assertGreater(bad.evidence["penetration_mm3"], 0)


class TestInside(unittest.TestCase):
    def test_volume_in_a_closed_box(self):
        outer = box([0, 0, 0], [30, 20, 10]) - box([2, 2, 2], [28, 18, 8])
        good = box([3, 3, 3], [27, 17, 7])
        self.assertTrue(ac.inside(good, [outer], 0.5, TOL).passed)
        r = ac.inside(good, [outer], 1.5, TOL)
        self.assertFalse(r.passed)
        self.assertAlmostEqual(r.margin, (1.0 - 1.5 + TOL.measure) / TOL.scale, delta=0.02)
        out = box([25, 3, 3], [35, 17, 7])
        self.assertFalse(ac.inside(out, [outer], 0.5, TOL).passed)


    def test_per_source_is_decomposable(self):
        # iteration 005 (RC-503): two boxes at different distances from a closed shell
        outer = box([0, 0, 0], [30, 20, 10]) - box([2, 2, 2], [28, 18, 8])
        a, b = box([3, 3, 3], [10, 10, 7]), box([15, 4.2, 4.5], [24, 14, 6])
        parts = {"a": a, "b": b}
        r = ac.inside(a + b, [outer], 0.5, TOL, parts=parts)
        per = r.evidence["per_source"]
        self.assertEqual(set(per), {"a", "b"})
        for k, v in parts.items():
            alone = ac.inside(v, [outer], 0.5, TOL).evidence
            self.assertAlmostEqual(per[k]["d"], min(alone["gap_to_solids"], alone["gap_to_outside"]), delta=1e-6)
        self.assertAlmostEqual(r.evidence["d"], min(x["d"] for x in per.values()), delta=1e-6)
        self.assertNotAlmostEqual(per["a"]["d"], per["b"]["d"], delta=0.1)
        # through a plan: per_source, volume_parts and the exemption description reach the evidence
        plan = ac.Plan(tol=TOL, seg=SEG)
        plan.volumes.update(both=a + b, none=M())
        plan.sources.update(both=["a", "b"], none=[])
        plan.parts["both"] = parts
        plan.labels.update(a="part_a", b="part_b")
        plan.references.update(a="part_a", b="part_b")
        plan.add("inside_both", "inside", "both inside", volume="both", clearance=0.5, minus="none",
                 minus_grown_by=0.5)
        (res,) = ac.run_plan(plan, {"shell": outer})
        self.assertEqual(res.evidence["volume_parts"], {"a": "part_a", "b": "part_b"})
        self.assertEqual(res.evidence["minus"], {"volume": "none", "sources": [], "grown_by": 0.5})
        self.assertAlmostEqual(res.evidence["per_source"]["b"]["d"], per["b"]["d"], delta=1e-6)
        table = ac.reference_table(plan, [res])
        self.assertEqual(table["a"], {"part": "part_a", "d": per["a"]["d"], "check": "inside_both"})


class TestSeparable(unittest.TestCase):
    def test_two_bodies(self):
        base = box([0, 0, 0], [20, 20, 10])
        lid = box([0, 0, 10], [20, 20, 12])
        self.assertTrue(ac.separable({"base": base, "lid": lid}, RULES["overlap_max"], TOL).passed)
        fused = box([0, 0, 5], [20, 20, 12])                    # fused into the base
        self.assertFalse(ac.separable({"base": base, "lid": fused}, RULES["overlap_max"], TOL).passed)
        over = box([0, 0, 10 - 2.0 / 400], [20, 20, 12])        # a 2 mm3 overlap
        r = ac.separable({"base": base, "lid": over}, RULES["overlap_max"], TOL)
        self.assertFalse(r.passed)
        self.assertAlmostEqual(r.evidence["overlap_mm3"]["base^lid"], 2.0, places=6)
        two = base + box([30, 0, 0], [40, 10, 10])               # a body in two shells
        self.assertFalse(ac.separable({"base": two, "lid": lid}, RULES["overlap_max"], TOL).passed)


class TestApertures(unittest.TestCase):
    def setUp(self):
        self.wall = box([-2.4, -10, 0], [0, 30, 20])             # a -X end wall, inner face at x = 0
        self.slab = box([-2.4 + TOL.measure, -10, 0 + TOL.measure], [0 - TOL.measure, 30, 20 - TOL.measure])
        self.env = 8.0

    def cut(self, y, d):
        return cyl_x(y, 8, d, -4, 1)

    def test_count_and_missing_cut(self):
        two = self.wall - self.cut(0, 8.6) - self.cut(15, 8.6)
        r = ac.aperture_count(two, self.slab, 2, TOL)
        self.assertTrue(r.passed)
        self.assertEqual(r.evidence["count"], 2)
        one = self.wall - self.cut(0, 8.6)
        r = ac.aperture_count(one, self.slab, 2, TOL)
        self.assertFalse(r.passed)
        self.assertEqual(r.margin, -1)

    def test_through_and_blind_regions_are_classified(self):
        # iteration 006 (RC-605, ARCHITECTURE.md 7.9): only regions that reach both face planes count as openings;
        # a pocket that stops inside the wall is listed as blind with the cut node it meets
        hole = self.cut(0, 8.6)
        pocket = M.cylinder(12, 0.75, 0.75, SEG).translate([-1.2, 20, 10])           # from the top, stops at z = 10
        side = cyl_x(25, 8, 2.0, -3.0, -1.0)                                          # from the outer face, 1.4 deep
        body = self.wall - hole - pocket - side
        cuts = {"hole": hole, "pocket": pocket, "side": side}
        r = ac.aperture_count(body, self.slab, 1, TOL, wall="-X", normal_axis=0, cuts=cuts)
        self.assertTrue(r.passed, r.evidence)
        self.assertEqual((r.evidence["through"], r.evidence["count"], r.evidence["total"]), (1, 1, 3))
        self.assertEqual(sorted(b["nodes"] for b in r.evidence["blind"]), [["pocket"], ["side"]])
        through = [x for x in r.evidence["regions"] if x["class"] == "through"]
        self.assertEqual(through[0]["nodes"], ["hole"])
        # without the wall's normal every region counts (the rubric 3.4 total)
        self.assertEqual(ac.aperture_count(body, self.slab, 3, TOL).evidence["count"], 3)
        # the same pocket moved out of the slab (into a block inside the cavity): no blind region
        block = box([0, 15, 0], [3, 25, 20])
        moved = M.cylinder(12, 0.75, 0.75, SEG).translate([1.5, 20, 10])
        r = ac.aperture_count(self.wall + block - hole - moved, self.slab, 1, TOL, normal_axis=0,
                              cuts={"hole": hole, "pocket": moved})
        self.assertTrue(r.passed)
        self.assertEqual((r.evidence["through"], len(r.evidence["blind"])), (1, 0))
        # a missing through cut fails even when blind regions exist
        r = ac.aperture_count(self.wall - pocket, self.slab, 1, TOL, normal_axis=0, cuts={"pocket": pocket})
        self.assertFalse(r.passed)
        self.assertEqual((r.evidence["through"], len(r.evidence["blind"]), r.margin), (0, 1, -1))

    def test_value_at_least_boundary(self):
        for value, ok in ((5.0 - TOL.measure / 2, True), (5.0 - 2 * TOL.measure, False), (5.1, True)):
            with self.subTest(value=value):
                r = ac.value_at_least("x", "pilot_engagement", value, 5.0, TOL, "d")
                self.assertEqual(r.passed, ok)
                self.assertAlmostEqual(r.margin, (value - 5.0 + TOL.measure) / TOL.scale, places=6)

    def test_oversize(self):
        for per_side, ok in ((0.3, True), (1.6, False)):
            with self.subTest(per_side=per_side):
                body = self.wall - self.cut(0, self.env + 2 * per_side)
                region = ac.apertures(body, self.slab, TOL)[0]
                r = ac.aperture_oversize(region, 0, self.env, self.env, 1.5, TOL)
                self.assertEqual(r.passed, ok)
                self.assertAlmostEqual(r.evidence["excess_per_side"], per_side, delta=0.02)


def standoff_base(tops, moved=(0.0, 0.0), pilot_d=2.1, od=5.3):
    holes = [(5, 5), (35, 5), (5, 25), (35, 25)]
    floor = box([0, 0, -2], [40, 30, 0])
    parts = [floor]
    pilots = []
    for k, ((x, y), top) in enumerate(zip(holes, tops)):
        dx, dy = moved if k == 1 else (0.0, 0.0)
        parts.append(M.cylinder(top + 2, od / 2, od / 2, SEG).translate([x + dx, y + dy, -2]))
        pilots.append(M.cylinder(6, pilot_d / 2, pilot_d / 2, SEG).translate([x + dx, y + dy, top - 5]))
    return ac.union(parts) - ac.union(pilots), holes


def seated_result(base, holes, bottom=4.0):
    tops = [ac.standoff_top(base, h, 3.7, 0.0, bottom + 1, SEG) for h in holes]
    pilots = [ac.pilot_axis(base, h, 3.7, t, 2.5, SEG) for h, t in zip(holes, tops)]
    return ac.seated(bottom, tops, holes, pilots, RULES["seat_gap_max"], RULES["seat_axis_residual_max"], TOL)


class TestSeated(unittest.TestCase):
    def test_seated_and_its_failures(self):
        base, holes = standoff_base([4.0] * 4)
        r = seated_result(base, holes)
        self.assertTrue(r.passed, r.evidence)
        self.assertLess(max(r.evidence["residuals"]), 1e-6)
        low, holes = standoff_base([4.0, 3.8, 4.0, 4.0])
        r = seated_result(low, holes)
        self.assertFalse(r.passed)
        self.assertAlmostEqual(max(r.evidence["gaps"]), 0.2, places=6)
        moved, holes = standoff_base([4.0] * 4, moved=(0.3, 0.0))
        r = seated_result(moved, holes)
        self.assertFalse(r.passed)
        self.assertAlmostEqual(max(r.evidence["residuals"]), 0.3, delta=0.02)


class TestBBox(unittest.TestCase):
    def test_limits_and_longest_side(self):
        b = box([0, 0, 0], [80, 60, 20])
        self.assertTrue(ac.bbox_within(b, [90, 70, 35], TOL, x_longest=True).passed)
        self.assertFalse(ac.bbox_within(b, [79, 70, 35], TOL).passed)
        self.assertFalse(ac.bbox_within(box([0, 0, 0], [60, 80, 20]), [90, 90, 35], TOL, x_longest=True).passed)


class TestDeliveredMeshes(unittest.TestCase):
    def test_measure_package_agrees_with_the_manifold(self):
        wall = box([-2.4, -10, -2], [0, 30, 20])
        base, holes = standoff_base([4.0] * 4)
        base = (base + wall) - cyl_x(10, 8, 8.6, -4, 1)
        lid = box([-2.4, -10, 20], [40, 30, 22])
        plan = ac.Plan(tol=TOL, seg=SEG)
        plan.volumes.update({"plug": cyl_x(10, 8, 8.0, -60, 5), "board": box([1, 1, 4], [39, 29, 5.6]),
                             "slab": box([-2.4 + TOL.measure, -10, -2 + TOL.measure], [-TOL.measure, 30, 22 - TOL.measure])})
        plan.add("sep", "separable", "", bodies=["base", "lid"], overlap_max=RULES["overlap_max"])
        plan.add("plug", "clear_of", "", volume="plug", clearance=0.3)
        plan.volumes["seats"] = ac.union([M.cylinder(10, 3.5, 3.5, SEG).translate([x, y, -1]) for x, y in holes])
        plan.add("board", "clear_of", "", volume="board", minus="seats", clearance=0.5)
        plan.add("ap", "aperture_count", "", slab="slab", n=1, wall="-X")
        plan.add("os", "aperture_oversize", "", slab="slab", wall="-X", normal_axis=0, point=[-1.2, 10, 8],
                 env_w=8.0, env_h=8.0, max=1.5)
        plan.add("seat", "seated", "", body="base", holes=[list(h) for h in holes], board_bottom=4.0, search_d=3.7,
                 z_lo=0.0, z_hi=5.0, probe_depth=2.5, gap_max=RULES["seat_gap_max"],
                 residual_max=RULES["seat_axis_residual_max"])
        plan.add("bb", "bbox_within", "", max=[50, 50, 30])
        bodies = {"base": base, "lid": lid}
        direct = ac.run_plan(plan, bodies)
        with tempfile.TemporaryDirectory() as tmp:
            for name, solid in bodies.items():
                fg.write_stl(solid, Path(tmp) / f"{name}.stl")
            report = ac.measure_package(Path(tmp), plan, list(bodies))
        self.assertEqual(report["errors"], [])
        self.assertEqual([b["shells"] for b in report["bodies"].values()], [1, 1])
        for d, r in zip(direct, report["results"]):
            with self.subTest(check=d.check_id):
                self.assertEqual(d.passed, r["passed"])
                self.assertAlmostEqual(d.margin, r["margin"], delta=0.02)
        self.assertTrue(report["all_passed"], [r for r in report["results"] if not r["passed"]])

    def test_missing_stl_is_a_failed_measurement(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = ac.measure_package(Path(tmp), ac.Plan(tol=TOL), ["base"])
        self.assertFalse(report["all_passed"])
        self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()
