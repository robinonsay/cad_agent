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

    def test_coplanar_cap_does_not_join_pockets(self):
        # iteration 007 (C1, RC-704, ARCHITECTURE.md 7.10): a shell base with a separate lid plate on the split plane
        # (top at an exactly representable Z) and a blind pilot + lid hole in the two corners of the -X wall. The base's
        # top, computed as the graph does (bottom + height), lands a float-noise step below the lid's underside, so
        # slab - bodies keeps a skin along the seam that joins the two corner pockets and spans both wall faces. With
        # the slab's Z faces on the body faces, the skin must never make a region `through`; the old zero threshold
        # (any positive slice volume) did. With the seam welded (no skin) the pockets are two separate blind regions.
        X, Y, w, lid_z, top, d = 40.0, 30.0, 2.5, 2.5, 15.0, 1.0
        split = top - lid_z
        eps = TOL.measure

        def case(skin: float):
            z0 = -5.699999999999999                       # a cavity floor that is not exactly representable
            bottom, height = z0 - w, split - z0 + w - skin
            base = M.cube([X + 2 * w, Y + 2 * w, height]).translate([-w, -w, bottom]) - box([0, 0, z0], [X, Y, split + 1])
            lid = box([-w, -w, split], [X + w, Y + w, top])
            cuts = {}
            for k, cy in enumerate((-w / 2, Y + w / 2), 1):
                cuts[f"boss_{k}_pilot"] = M.cylinder(6.0, d / 2, d / 2, SEG).translate([-w / 2, cy, split - 5.0])
                cuts[f"boss_{k}_lid_hole"] = M.cylinder(lid_z + 2, d / 2 + 0.2, d / 2 + 0.2, SEG).translate(
                    [-w / 2, cy, split - 1.0])
            cut = ac.union(list(cuts.values()))
            bodies = (base - cut) + (lid - cut)
            slab = box([-w + eps, -w, bottom], [-eps, Y + w, top])      # Z faces on the base bottom and the lid top
            return bodies, slab, cuts

        bodies, slab, cuts = case(skin=1e-9)
        r = ac.aperture_count(bodies, slab, 0, TOL, wall="-X", normal_axis=0, cuts=cuts)
        self.assertTrue(r.passed, r.evidence["detail"])
        self.assertEqual(r.evidence["through"], 0)
        self.assertEqual({x for b in r.evidence["blind"] for x in b["nodes"]}, set(cuts))
        regions = ac.apertures(bodies, slab, TOL)
        old = [ac._reaches(g, slab, 0, False) and ac._reaches(g, slab, 0, True) for g in regions]
        self.assertGreaterEqual(sum(old), 1)              # the iteration 006 test counted the joined skin as an opening
        bodies, slab, cuts = case(skin=0.0)
        bodies = bodies + box([-w, -w, split - 1e-3], [X + w, Y + w, split + 1e-3]) - ac.union(list(cuts.values()))
        r = ac.aperture_count(bodies, slab, 0, TOL, wall="-X", normal_axis=0, cuts=cuts)
        self.assertEqual((r.evidence["through"], len(r.evidence["blind"])), (0, 2), r.evidence["detail"])
        self.assertEqual(sorted(sorted(b["nodes"]) for b in r.evidence["blind"]),
                         [[f"boss_{k}_lid_hole", f"boss_{k}_pilot"] for k in (1, 2)])

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


def pad_plate(pad_d, inset=0.39, hole_d=3.4, fn=64, t=2.4):
    """iteration 009 (D1): a lid plate with a corner pad whose axis sits `inset` inside the plate edge, the pad an
    inscribed polygon (an add), the clearance hole a circumscribed one (a cut). Returns (body, hole, axis xy)."""
    cx, cy = 20 - inset, 10.0
    plate = box([0, 0, 0], [20, 20, t])
    pad = M.cylinder(t, pad_d / 2, pad_d / 2, fn).translate([cx, cy, 0])
    hd = hole_d / np.cos(np.pi / fn)
    hole = M.cylinder(t + 0.4, hd / 2, hd / 2, fn).translate([cx, cy, -0.2])
    return (plate + pad) - hole, hole, (cx, cy)


def ray_cast_ligament(body, centre, z, step_deg=2.0):
    """Judge 2's recipe (independent of assembly_checks): rays every step_deg outward from the hole axis at height z;
    the material length is from the first hit (the hole wall) to the next (where the ray leaves the material)."""
    import trimesh
    mesh = body.to_mesh()
    tm = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)
    best = np.inf
    for a in np.radians(np.arange(0.0, 360.0, step_deg)):
        d = np.array([np.cos(a), np.sin(a), 0.0])
        o = np.array([centre[0], centre[1], z])
        locs, _, _ = tm.ray.intersects_location([o], [d], multiple_hits=True)
        s = np.unique(np.round(np.sort((locs - o) @ d), 9))
        if len(s) >= 2:
            best = min(best, float(s[1] - s[0]))
    return best


class TestLigament(unittest.TestCase):
    """iteration 009 (C1, RC-901): the measured material round every opening (L2.8.3)."""
    MIN = RULES["min_ligament"]

    def test_round_hole_in_pad_matches_the_judge_case(self):
        body, hole, (cx, cy) = pad_plate(6.1)
        r = ac.ligament(body, hole, 2, 1.2, self.MIN, TOL, "lig")
        self.assertEqual(r.type, "ligament")
        self.assertAlmostEqual(r.evidence["ligament"], 1.344, delta=0.01)
        self.assertFalse(r.passed)
        self.assertLess(r.margin, 0)
        self.assertEqual(r.evidence["toward"], "outer")
        at, to = r.evidence["where"]
        self.assertGreater(to[0], 20.0)                     # the nearest boundary is the pad, outside the plate
        self.assertAlmostEqual(np.hypot(at[0] - cx, at[1] - cy), 1.7, delta=0.01)
        for pad_d, expected in ((6.5, 1.546), (6.6, 1.594)):   # Ø6.6 = 3.4 + 2 x (1.5 + 0.1): the agent's derivation
            with self.subTest(pad=pad_d):
                body, hole, _ = pad_plate(pad_d)
                r = ac.ligament(body, hole, 2, 1.2, self.MIN, TOL, "lig")
                self.assertAlmostEqual(r.evidence["ligament"], expected, delta=0.01)
                self.assertTrue(r.passed, r.evidence)

    def test_agrees_with_ray_cast_recipe(self):
        for pad_d in (6.1, 6.6):
            with self.subTest(pad=pad_d):
                body, hole, centre = pad_plate(pad_d)
                mine = ac.ligament(body, hole, 2, 1.2, self.MIN, TOL, "lig").evidence["ligament"]
                ray = ray_cast_ligament(body, centre, 1.2)
                self.assertLessEqual(mine, ray + 1e-6)          # the agent is never more lenient than the judge
                self.assertAlmostEqual(mine, ray, delta=0.02)

    def test_neighbouring_openings(self):
        hd = 3.0 / np.cos(np.pi / SEG)
        for gap, ok in ((1.2, False), (1.8, True)):
            with self.subTest(gap=gap):
                a = M.cylinder(3, hd / 2, hd / 2, SEG).translate([12, 10, -0.5])
                b = M.cylinder(3, hd / 2, hd / 2, SEG).translate([12 + 3.0 + gap, 10, -0.5])
                body = box([0, 0, 0], [30, 20, 2]) - a - b
                r = ac.ligament(body, a, 2, 1.0, self.MIN, TOL, "lig", neighbours={"hole_b": b})
                self.assertEqual(r.passed, ok, r.evidence)
                self.assertAlmostEqual(r.evidence["ligament"], gap, delta=0.01)
                self.assertEqual(r.evidence["toward"], "hole_b")

    def test_wall_opening_seam_and_floor_top(self):
        wall = box([0, 0, 0], [2.4, 30, 20])

        def check(z0, z1, floor_z=None):
            cut = box([-0.5, 10, z0], [2.9, 20, z1])
            return ac.ligament(wall - cut, cut, 0, 1.2, self.MIN, TOL, "lig", floor_z=floor_z)

        r = check(5.0, 19.0)
        self.assertFalse(r.passed)
        self.assertAlmostEqual(r.evidence["ligament"], 1.0, delta=1e-6)
        self.assertEqual(r.evidence["toward"], "outer")
        self.assertAlmostEqual(r.evidence["where"][0][2], 19.0, delta=1e-6)
        r = check(5.0, 18.0, floor_z=3.8)
        self.assertFalse(r.passed)
        self.assertAlmostEqual(r.evidence["ligament"], 1.2, delta=1e-6)
        self.assertEqual(r.evidence["toward"], "floor_top")
        r = check(5.0, 18.0, floor_z=3.0)
        self.assertTrue(r.passed, r.evidence)
        self.assertAlmostEqual(r.evidence["ligament"], 2.0, delta=1e-6)
        self.assertAlmostEqual(r.margin, (2.0 - self.MIN + TOL.measure) / TOL.scale, delta=1e-6)

    def test_no_material_is_a_failure(self):
        body, hole, _ = pad_plate(6.6)
        r = ac.ligament(body, hole, 2, 10.0, self.MIN, TOL, "lig")
        self.assertFalse(r.passed)
        self.assertEqual(r.margin, -1.0)
        self.assertIn("no material", r.evidence["detail"])
        # a cut that misses the body's material at the plane has no rim either
        far = M.cylinder(3, 1, 1, SEG).translate([50, 50, -0.5])
        self.assertEqual(ac.ligament(body, far, 2, 1.2, self.MIN, TOL, "lig").margin, -1.0)

    def test_run_plan_and_delivered_mesh_agree(self):
        body, hole, _ = pad_plate(6.1)
        plan = ac.Plan(tol=TOL, seg=64)
        plan.volumes["hole"] = hole
        plan.add("lig", "ligament", "", body="lid", cut="hole", axis=2, plane=1.2, min=self.MIN, neighbours=[])
        direct = ac.run_plan(plan, {"lid": body})[0]
        with tempfile.TemporaryDirectory() as tmp:
            fg.write_stl(body, Path(tmp) / "lid.stl")
            report = ac.measure_package(Path(tmp), plan, ["lid"])
        self.assertEqual(report["errors"], [])
        got = report["results"][0]
        self.assertEqual(got["passed"], direct.passed)
        self.assertAlmostEqual(got["evidence"]["ligament"], direct.evidence["ligament"], delta=0.02)


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
