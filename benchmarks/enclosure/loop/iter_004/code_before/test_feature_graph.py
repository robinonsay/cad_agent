"""Tests for feature_graph.py: expressions, poses, resolution, geometry per body and SCAD parity.

Graphs are built by hand (the archetype that decides which nodes exist is M8).
No Ollama. The parity test needs OpenSCAD and is skipped without it.
"""

import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

import cad_agent as ca
import feature_graph as fg
import parts as pt
from feature_graph import FeatureGraph, Node, Pose

REPO = Path(__file__).parent
PARTS = REPO / "benchmarks" / "enclosure" / "parts"
RULES = pt.load_rules(REPO / "design_rules.json").values
HAVE_OPENSCAD = bool(shutil.which(ca.OPENSCAD) or Path(ca.OPENSCAD).exists())


def shell(id_, x, y, z, wall, floor, open_top=1, **kw):
    return Node(id_, "body", "shell", {"x": x, "y": y, "z": z, "wall": wall, "floor": floor, "open_top": open_top},
                **kw)


class TestExpressions(unittest.TestCase):
    def test_arithmetic_and_functions(self):
        env = {"a.b": 2.0, "spec.c": 3.0, "n.HOLE[2].x": 7.5}
        self.assertEqual(fg.evaluate("a.b + 2*spec.c - (1 - 3)", env), 10.0)
        self.assertEqual(fg.evaluate("max(a.b, spec.c) + min(1, 2) + abs(-1)", env), 5.0)
        self.assertEqual(fg.evaluate("ceil_to(a.b * 1.1, 0.5)", env), 2.5)
        self.assertEqual(fg.evaluate("-n.HOLE[2].x / 2", env), -3.75)
        self.assertEqual(fg.refs("a.b + n.HOLE[2].x + max(spec.c, 1)"), {"a.b", "n.HOLE[2].x", "spec.c"})
        self.assertEqual(fg.evaluate(4, {}), 4.0)

    def test_unsafe_expressions_are_rejected(self):
        for bad in ("__import__('os')", "os.system('ls')", "(lambda: 1)()", "a.b()", "a ** 2", "'x'",
                    "a if b else c", "[1, 2]", "a.__class__", "max(x=1)"):
            with self.subTest(expr=bad):
                with self.assertRaises(fg.ExprError):
                    fg.evaluate(bad, {"a": 1, "b": 1, "c": 1, "a.b": 1})

    def test_unknown_reference(self):
        with self.assertRaises(fg.MissingRefError) as cm:
            fg.evaluate("foo.bar + 1", {})
        self.assertEqual(cm.exception.ref, "foo.bar")


class TestResolve(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = pt.Catalog.load(PARTS)

    def board_graph(self, offset=(0, 0, 0)):
        g = FeatureGraph()
        g.add(Node("board", "reference", "part", {"width": "spec.board_w", "depth": "spec.board_d"},
                   Pose(offset=offset), part="perfboard"))
        g.add(Node("cavity", "body", "shell", {"x": "board.width + 2*spec.board_clearance",
                                               "y": "board.depth + 2*spec.board_clearance",
                                               "z": "board.thickness + spec.above", "wall": "rules.wall_default",
                                               "floor": "rules.floor_default", "open_top": 1}))
        return g

    def test_derived_size_reresolves_when_spec_changes(self):
        g = self.board_graph()
        spec = {"board_w": 61.0, "board_d": 37.0, "board_clearance": 0.7, "above": 9.0}
        res = g.resolve(spec, RULES, catalog=self.cat)
        self.assertAlmostEqual(res.params["cavity"]["x"], 61.0 + 1.4)
        self.assertEqual(res.order.index("board") < res.order.index("cavity"), True)
        spec2 = dict(spec, board_w=83.0, board_clearance=1.1)
        res2 = g.resolve(spec2, RULES, catalog=self.cat)
        self.assertAlmostEqual(res2.params["cavity"]["x"], 83.0 + 2.2)
        thickness = self.cat.get("perfboard").params["thickness"]["default"]
        self.assertAlmostEqual(res2.params["cavity"]["z"], thickness + 9.0)

    def test_cycle_names_both_nodes(self):
        g = FeatureGraph([Node("a", "add", "box", {"x": "b.x", "y": 1, "z": 1}, body="base"),
                          Node("b", "add", "box", {"x": "a.x", "y": 1, "z": 1}, body="base")])
        with self.assertRaises(fg.CycleError) as cm:
            g.resolve()
        self.assertEqual(set(cm.exception.nodes), {"a", "b"})

    def test_missing_reference_names_node_and_ref(self):
        g = FeatureGraph([Node("a", "add", "box", {"x": "foo.bar", "y": 1, "z": 1}, body="base")])
        with self.assertRaises(fg.MissingRefError) as cm:
            g.resolve()
        self.assertEqual((cm.exception.node, cm.exception.ref), ("a", "foo.bar"))
        g2 = FeatureGraph([Node("a", "add", "box", {"x": "spec.nope", "y": 1, "z": 1}, body="base")])
        with self.assertRaises(fg.MissingRefError) as cm:
            g2.resolve({})
        self.assertEqual((cm.exception.node, cm.exception.ref), ("a", "spec.nope"))

    def test_axis_alignment(self):
        datums = {"ax_px": pt.Axis([0, 0, 0], [1, 0, 0]), "ax_nz": pt.Axis([0, 0, 0], [0, 0, -1])}
        g = FeatureGraph([Node("c1", "cut", "cylinder", {"d": 1, "h": 1}, Pose(at="ax_px", axis="ax_px"), body="b"),
                          Node("c2", "cut", "cylinder", {"d": 1, "h": 1}, Pose(at="ax_nz", axis="ax_nz"), body="b")])
        res = g.resolve(datums=datums)
        np.testing.assert_allclose(res.poses["c1"][:3, :3] @ [0, 0, 1], [1, 0, 0], atol=1e-12)
        r2 = res.poses["c2"][:3, :3]
        np.testing.assert_allclose(r2 @ [0, 0, 1], [0, 0, -1], atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(r2), 1.0)

    def test_project_to_wall_outer_plane(self):
        X, Y, Z, W = 63.0, 41.0, 17.0, 2.2
        inside_mx = pt.Point([-X / 2 + 3.0, 4.0, 6.0])     # 3 mm in from the -X outer face
        inside_py = pt.Point([5.0, Y / 2 - 3.0, 6.0])      # 3 mm in from the +Y outer face
        g = FeatureGraph([shell("base", X, Y, Z, W, W),
                          Node("cut_mx", "cut", "box", {"x": 1, "y": 1, "z": 1},
                               Pose(at="p_mx", project_to="base.face[-X].outer"), body="base"),
                          Node("cut_py", "cut", "box", {"x": 1, "y": 1, "z": 1},
                               Pose(at="p_py", project_to="base.face[+Y].outer"), body="base"),
                          Node("cut_in", "cut", "box", {"x": 1, "y": 1, "z": 1},
                               Pose(at="p_mx", project_to="base.face[-X].inner"), body="base")])
        res = g.resolve(datums={"p_mx": inside_mx, "p_py": inside_py})
        np.testing.assert_allclose(res.poses["cut_mx"][:3, 3], [-X / 2, 4.0, 6.0])
        np.testing.assert_allclose(res.poses["cut_py"][:3, 3], [5.0, Y / 2, 6.0])
        np.testing.assert_allclose(res.poses["cut_in"][:3, 3], [-X / 2 + W, 4.0, 6.0])

    def test_datum_ref_through_placed_reference(self):
        off = (4.5, -2.25, 7.0)
        g = self.board_graph(offset=off)
        g.add(Node("probe", "add", "cylinder", {"d": 1, "h": "board.HOLE[3].x"}, body="cavity"))
        spec = {"board_w": 61.0, "board_d": 37.0, "board_clearance": 0.7, "above": 9.0}
        res = g.resolve(spec, RULES, catalog=self.cat)
        inst = self.cat.instantiate("perfboard", {"width": 61.0, "depth": 37.0})
        self.assertAlmostEqual(res.params["probe"]["h"], inst.datums["HOLE"].at[3][0] + off[0])
        np.testing.assert_allclose(res.datums["board.HOLE"].at[3],
                                   np.array(inst.datums["HOLE"].at[3]) + np.array(off))

    def test_reference_without_catalog_is_a_typed_error(self):
        with self.assertRaises(fg.MissingRefError) as cm:
            self.board_graph().resolve({"board_w": 1, "board_d": 1, "board_clearance": 0, "above": 1}, RULES)
        self.assertEqual(cm.exception.node, "board")

    def test_json_round_trip(self):
        g = self.board_graph(offset=("spec.board_clearance", 0, 1))
        g.add(Node("usb_cut", "cut", "box", {"x": 3, "y": "board.width / 10", "z": 2},
                   Pose(at="board.HOLE[1]", offset=(0, 0, "rules.wall_default"), rot_z=30,
                        project_to="cavity.face[-X].outer"),
                   body="cavity,lid", role="port_cut", free=[("y", 1, "board.width")]))
        g.add(Node("lid", "body", "box", {"x": 5, "y": 5, "z": 2}))
        spec = {"board_w": 61.0, "board_d": 37.0, "board_clearance": 0.7, "above": 9.0}
        text = json.dumps(g.to_json())
        g2 = FeatureGraph.from_json(text)
        self.assertEqual(g2.to_json(), g.to_json())
        a = g.resolve(spec, RULES, catalog=self.cat).as_dict()
        b = g2.resolve(spec, RULES, catalog=self.cat).as_dict()
        self.assertEqual(a, b)

    def test_only_port_cuts_may_span_bodies(self):
        with self.assertRaises(ValueError):
            FeatureGraph([Node("c", "cut", "box", {"x": 1, "y": 1, "z": 1}, body="base,lid", role="pilot")])


@unittest.skipIf(fg.m3d is None, "manifold3d is not installed")
class TestGeometry(unittest.TestCase):
    def test_plate_with_round_and_rect_through_cuts(self):
        X, Y, T, D, RX, RY = 47.0, 31.0, 3.0, 6.0, 8.0, 5.0
        g = FeatureGraph([Node("plate", "body", "box", {"x": X, "y": Y, "z": T}),
                          Node("hole", "cut", "cylinder", {"d": D, "h": T + 2}, Pose(offset=(-10, 0, -1)), body="plate"),
                          Node("slot", "cut", "box", {"x": RX, "y": RY, "z": T + 2}, Pose(offset=(10, 0, -1)),
                               body="plate", role="port_cut")])
        res = g.resolve(rules=RULES)
        stats = fg.body_stats(fg.body_solid(g, "plate", res))
        expected = X * Y * T - math.pi * (D / 2) ** 2 * T - RX * RY * T
        self.assertAlmostEqual(stats["volume"] / expected, 1.0, delta=0.005)
        self.assertEqual(stats["shells"], 1)
        self.assertEqual(stats["genus"], 2)

    def lidded(self, gap=0.25):
        X, Y, Z, W, LT, LIP = 64.0, 44.0, 20.0, 2.0, 2.0, 3.0
        g = FeatureGraph([
            shell("base", X, Y, Z, W, W, open_top=1),
            Node("lid", "body", "box", {"x": X, "y": Y, "z": LT}, Pose(offset=(0, 0, Z))),
            Node("lip", "add", "shell", {"x": X - 2 * W - 2 * gap, "y": Y - 2 * W - 2 * gap, "z": LIP,
                                         "wall": 1.6, "floor": 0, "open_top": 1},
                 Pose(offset=(0, 0, Z - LIP)), body="lid", role="lip"),
        ])
        return g, g.resolve(rules=RULES)

    def test_base_and_lid_are_separate_single_shells(self):
        g, res = self.lidded()
        base, lid = fg.body_solid(g, "base", res), fg.body_solid(g, "lid", res)
        self.assertEqual(fg.body_stats(base)["shells"], 1)
        self.assertEqual(fg.body_stats(lid)["shells"], 1)
        self.assertLessEqual((base ^ lid).volume(), 1.0)
        # and the overlap measurement does see a lip that is too big
        g2, res2 = self.lidded(gap=-0.5)
        self.assertGreater((fg.body_solid(g2, "base", res2) ^ fg.body_solid(g2, "lid", res2)).volume(), 1.0)

    def test_hull_minus_solid_is_the_cavity(self):
        X, Y, Z, W, F = 50.0, 30.0, 20.0, 2.0, 3.0
        g = FeatureGraph([shell("closed", X, Y, Z, W, F, open_top=0),
                          Node("block", "body", "box", {"x": X, "y": Y, "z": Z})])
        res = g.resolve(rules=RULES)
        closed = fg.body_solid(g, "closed", res)
        cavity = closed.hull().volume() - closed.volume()
        self.assertAlmostEqual(cavity, (X - 2 * W) * (Y - 2 * W) * (Z - F - W), places=3)
        block = fg.body_solid(g, "block", res)
        self.assertAlmostEqual(block.hull().volume() - block.volume(), 0.0, places=6)

    def test_reference_with_same_body_name_is_never_printed(self):
        cat = pt.Catalog.load(PARTS)
        g = FeatureGraph([Node("plate", "body", "box", {"x": 30, "y": 20, "z": 2})])
        before = fg.body_stats(fg.body_solid(g, "plate", g.resolve(rules=RULES)))["volume"]
        g.add(Node("ghostpart", "reference", "part", {"width": 30, "depth": 20}, Pose(offset=(0, 0, 5)),
                   body="plate", part="perfboard"))
        res = g.resolve(rules=RULES, catalog=cat)
        self.assertAlmostEqual(fg.body_stats(fg.body_solid(g, "plate", res))["volume"], before)
        self.assertNotIn("ghostpart", fg.scad_body(g, "plate", res))
        model = fg.scad_model(g, res)
        lines = [l for l in model.splitlines() if "ghostpart" in l]
        self.assertTrue(lines)
        self.assertTrue(all(l.lstrip().startswith("%") for l in lines), lines)
        # the structural guard: a reference smuggled into a body's member list trips the assertion
        g.nodes_of = lambda body: [g.nodes["plate"], g.nodes["ghostpart"]]
        with self.assertRaises(AssertionError):
            fg.body_solid(g, "plate", res)

    def test_blind_pilot(self):
        H, OD, PD, DEPTH = 8.0, 6.0, 2.2, 5.0
        g = FeatureGraph([Node("base", "body", "box", {"x": 20, "y": 20, "z": 2}),
                          Node("standoff", "add", "cylinder", {"d": OD, "h": H}, Pose(offset=(0, 0, 2)),
                               body="base", role="standoff"),
                          Node("pilot", "cut", "cylinder", {"d": PD, "h": DEPTH + 1},
                               Pose(offset=(0, 0, "standoff.h + 2 - 5.0")), body="base", role="pilot")])
        res = g.resolve(rules=RULES)
        with_pilot = fg.body_stats(fg.body_solid(g, "base", res))
        g2 = FeatureGraph([n for n in g if n.id != "pilot"])
        without = fg.body_stats(fg.body_solid(g2, "base", g2.resolve(rules=RULES)))
        self.assertEqual(with_pilot["shells"], 1)
        removed = without["volume"] - with_pilot["volume"]
        self.assertAlmostEqual(removed / (math.pi * (PD / 2) ** 2 * DEPTH), 1.0, delta=0.005)

    def test_write_stl_round_trips(self):
        g, res = self.lidded()
        base = fg.body_solid(g, "base", res)
        with tempfile.TemporaryDirectory() as tmp:
            path = fg.write_stl(base, Path(tmp) / "base.stl")
            tris = ca.read_stl(path)
            self.assertEqual(len(tris), base.num_tri())
            self.assertEqual(ca.mesh_bodies(tris), 1)

    @unittest.skipUnless(HAVE_OPENSCAD, "OpenSCAD is not installed")
    def test_scad_matches_manifold(self):
        rules = dict(RULES, fn=24)
        g = FeatureGraph([shell("base", 40.0, 26.0, 15.0, 2.0, 2.0, open_top=1),
                          Node("port", "cut", "cylinder", {"d": 7.0, "h": 6.0},
                               Pose(at="mouth", axis="mouth", offset=(3, 0, 0)), body="base", role="port_cut")])
        res = g.resolve(rules=rules, datums={"mouth": pt.Axis([-20.0, 1.5, 7.0], [-1.0, 0.0, 0.0])})
        m = fg.body_solid(g, "base", res)
        stats = fg.body_stats(m)
        self.assertEqual(stats["genus"], 1)            # the cut really passes through the -X wall
        with tempfile.TemporaryDirectory() as tmp:
            scad = Path(tmp) / "base.scad"
            scad.write_text(fg.scad_body(g, "base", res))
            out = ca.compile_scad(scad, Path(tmp) / "base.stl")
            self.assertTrue(out.ok, out.problems)
            vol, _ = ca.mesh_mass(out.tris)
            self.assertAlmostEqual(vol / stats["volume"], 1.0, delta=0.005)
            lo, hi = ca.mesh_bbox(out.tris)
            np.testing.assert_allclose(lo, stats["bbox"][0], atol=0.05)
            np.testing.assert_allclose(hi, stats["bbox"][1], atol=0.05)


class TestResolverExtensions(unittest.TestCase):
    """Iteration 002: world AABB refs of placed parts, the fastener namespace, axis_dir poses."""

    def test_bbox_refs_follow_the_pose(self):
        cat = pt.Catalog.load(PARTS)
        jack = cat.instantiate("jack_3p5_pj320a")
        L, W = jack.params["body_length"], jack.params["body_width"]
        g = FeatureGraph([
            Node("j", "reference", "part", pose=Pose(offset=(10, 20, 0), rot_z=math.degrees(math.atan2(1, 0))),
                 part="jack_3p5_pj320a"),
            Node("cav", "envelope", "box", {"x": "j.bbox.size_x + 2*spec.c", "y": "j.bbox.size_y", "z": 1,
                                            "lo": "j.bbox.min_x"}),
        ])
        res = g.resolve({"c": 0.5}, catalog=cat)
        self.assertAlmostEqual(res.params["cav"]["x"], W + 1.0, places=9)    # rotated: X extent is the width
        self.assertAlmostEqual(res.params["cav"]["y"], L, places=9)
        self.assertAlmostEqual(res.params["cav"]["lo"], 10 - W, places=9)
        self.assertEqual(g.order().index("j") < g.order().index("cav"), True)

    def test_fastener_namespace(self):
        g = FeatureGraph([Node("p", "cut", "cylinder", {"d": "fastener.lid.pilot_diameter", "h": 2}, body="b"),
                          Node("b", "body", "box", {"x": 5, "y": 5, "z": 5})])
        self.assertAlmostEqual(g.resolve(fasteners={"fastener.lid.pilot_diameter": 2.5}).params["p"]["d"], 2.5)
        with self.assertRaises(fg.MissingRefError):
            g.resolve()

    def test_axis_dir_pose_and_json(self):
        n = Node("c", "envelope", "cylinder", {"d": 2, "h": 10}, Pose(offset=(1, 2, 3), axis_dir=(0, 1, 0)))
        g = FeatureGraph([n])
        res = g.resolve()
        np.testing.assert_allclose(res.poses["c"][:3, 2], [0, 1, 0], atol=1e-12)
        back = FeatureGraph.from_json(json.loads(json.dumps(g.to_json())))
        self.assertEqual(back.nodes["c"].pose.axis_dir, (0, 1, 0))
        np.testing.assert_allclose(back.resolve().poses["c"], res.poses["c"])


if __name__ == "__main__":
    unittest.main()
