"""Unit and integration tests for cad_agent.py.

Uses the standard-library unittest so no extra dependencies are needed. LLM calls
go to a scripted fake (no network). Tests that need real geometry run OpenSCAD
and are skipped when it is not installed.
"""

import json
import math
import shutil
import struct
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

from py_trees.common import Status

import cad_agent as ca

HAVE_OPENSCAD = bool(shutil.which(ca.OPENSCAD) or Path(ca.OPENSCAD).exists())
needs_openscad = unittest.skipUnless(HAVE_OPENSCAD, "OpenSCAD is not installed")

REQUEST = ("A desk phone stand: a 80x60x5 mm base plate with a back rest leaning at 70 degrees, "
           "70 mm tall, and a 10 mm lip at the front to stop the phone sliding off")


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class ScriptedLLM(ca.OllamaAgent):
    """A real OllamaAgent (so ask_json/vote logic runs) whose chat() replays scripted replies.

    `script` maps a label prefix to a list of replies (dicts are JSON-encoded). The
    longest matching prefix wins, and the last reply is repeated, so a vote gets
    unanimous answers.
    """

    def __init__(self, script):
        super().__init__()
        self.script = {k: list(v) for k, v in script.items()}
        self.calls = []

    def chat(self, prompt, system="", images=(), schema=None, temperature=0.0, seed=0, label="ask"):
        self.calls.append((label, prompt, list(images)))
        for prefix in sorted(self.script, key=len, reverse=True):
            if label.startswith(prefix):
                replies = self.script[prefix]
                reply = replies.pop(0) if len(replies) > 1 else replies[0]
                if callable(reply):
                    reply = reply(prompt)
                return reply if isinstance(reply, str) else json.dumps(reply)
        raise AssertionError(f"unexpected LLM call: {label}")

    def p_yes(self, prompt, label="p_yes", system="", images=()):
        answer = json.loads(self.chat(prompt, system, images, label=label)).get("answer")
        return 0.9 if answer == "yes" else 0.1

    def labels(self):
        return [c[0] for c in self.calls]


YES = {"reasoning": "", "answer": "yes"}
NO = {"reasoning": "", "answer": "no"}


def asked_about(phrase):
    """A yes/no reply that is "yes" only when the question or the described design mentions `phrase`."""
    def reply(prompt):
        lines = prompt.strip().splitlines()
        design = next((l for l in lines if l.startswith("In the current design:")), "")
        return YES if phrase in lines[-1] or phrase in design else NO
    return reply


def phone_stand_script(**overrides):
    script = {
        "components": [{"components": [
            {"name": "base", "description": "flat plate 80x60x5 mm on the table"},
            {"name": "back_rest", "description": "back rest leaning back at 70 degrees, 70 mm tall"},
            {"name": "lip", "description": "10 mm tall lip along the front edge"},
        ]}],
        "shape_base": [{"reasoning": "", "shape": "box"}],
        "shape_back_rest": [{"reasoning": "", "shape": "panel"}],
        "shape_lip": [{"reasoning": "", "shape": "box"}],
        "params_base": [{"reasoning": "", "width": 80, "depth": 60, "height": 5}],
        "params_back_rest": [{"reasoning": "", "width": 80, "height": 70, "thickness": 5,
                              "angle": 70, "lean": "back"}],
        "params_lip": [{"reasoning": "", "width": 80, "depth": 5, "height": 10}],
        "parent_lip": [{"reasoning": "", "parent": "base"}],
        "side_": [YES],
        "spans_": [NO],
        "verify_": [YES],
        "complete": [YES],
        "align_back_rest": [asked_about("along the base's back edge")],
        "align_lip": [asked_about("along the base's front edge")],
        # probe ("is it a ball?") -> no, then the real question -> yes
        "visual_": [{"reasoning": "", "answer": "no"}, {"reasoning": "", "answer": "yes"}],
    }
    script.update(overrides)
    return script


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestHelpers(unittest.TestCase):
    def test_extract_json(self):
        self.assertEqual(ca.extract_json('sure: ```json\n{"a": [1]}\n``` bye'), {"a": [1]})
        self.assertEqual(ca.extract_json('{oops} {"ok": true}'), {"ok": True})
        with self.assertRaises(ValueError):
            ca.extract_json("nothing")

    def test_slugify(self):
        self.assertEqual(ca.slugify("Back Rest!"), "back_rest")
        self.assertEqual(ca.slugify("3 legs"), "c_3_legs")

    def test_validate_params(self):
        panel = ca.SHAPES["panel"]
        good = {"width": 80, "height": 70, "thickness": 5, "angle": 70, "lean": "back"}
        params, errors = ca.validate_params(panel, good)
        self.assertEqual(errors, [])
        self.assertEqual(params["angle"], 70.0)
        params, errors = ca.validate_params(panel, dict(good, angle=120, lean="up"))
        self.assertIsNone(params)
        self.assertEqual(len(errors), 2)
        _, errors = ca.validate_params(ca.SHAPES["tube"], {"outer_diameter": 10, "inner_diameter": 12,
                                                          "height": 5, "axis": "z"})
        self.assertIn("smaller", errors[0])

    def test_attach_position(self):
        base = ((0, 0, 0), (80, 60, 5))
        self.assertEqual(ca.attach_position(*base, (80, 5, 10), {"side": "top", "x": "center", "y": "front"}),
                         (0, 0, 5))
        self.assertEqual(ca.attach_position(*base, (80, 30, 70), {"side": "top", "x": "center", "y": "back"}),
                         (0, 30, 5))
        self.assertEqual(ca.attach_position(*base, (10, 10, 10), {"side": "right", "y": "center", "z": "bottom"}),
                         (80, 25, 0))
        self.assertEqual(ca.attach_position(*base, (10, 10, 10), {"side": "bottom", "x": "left", "y": "back"}),
                         (0, 50, -10))

    def test_vertical_panel_is_as_deep_as_it_is_thick(self):
        w, d, h = ca.SHAPES["panel"].size({"width": 80, "height": 70, "thickness": 5, "angle": 90, "lean": "back"})
        self.assertAlmostEqual(d, 5)
        self.assertEqual((w, h), (80, 70))

    def test_request_numbers(self):
        nums = [(v, u) for v, u, _ in ca.request_numbers(REQUEST)]
        self.assertEqual(nums, [(80, ""), (60, ""), (5, "mm"), (70, "deg"), (70, "mm"), (10, "mm")])
        self.assertEqual(ca.request_numbers("2 cm and 1 inch")[0][0], 20)
        self.assertAlmostEqual(ca.request_numbers("2 cm and 1 inch")[1][0], 25.4)

    def test_mesh_helpers(self):
        # A unit cube as 12 outward-facing triangles.
        v = [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        tris = []
        for a, b, c, d in faces:
            tris += [(v[a], v[b], v[c]), (v[a], v[c], v[d])]
        volume, com = ca.mesh_mass(tris)
        self.assertAlmostEqual(volume, 1.0)
        for c in com:
            self.assertAlmostEqual(c, 0.5)
        self.assertEqual(ca.mesh_bodies(tris), 1)
        moved = [tuple((p[0] + 5, p[1], p[2]) for p in t) for t in tris]
        self.assertEqual(ca.mesh_bodies(tris + moved), 2)
        hull = ca.convex_hull([(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5)])
        self.assertEqual(len(hull), 4)
        self.assertTrue(ca.inside_hull((0.5, 0.5), hull))
        self.assertFalse(ca.inside_hull((1.5, 0.5), hull))

    def test_read_stl_ascii_and_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.stl"
            a.write_text("solid t\n facet normal 0 0 1\n outer loop\n vertex -1 2 3\n vertex 4 5 6\n"
                         " vertex 0 0 0\n endloop\n endfacet\nendsolid t\n")
            self.assertEqual(ca.mesh_bbox(ca.read_stl(a)), ((-1, 0, 0), (4, 5, 6)))
            b = Path(tmp) / "b.stl"
            b.write_bytes(b"\0" * 80 + struct.pack("<I", 1)
                          + struct.pack("<12fH", 0, 0, 1, 0, 0, 0, 10, 0, 0, 0, 20, 3, 0))
            self.assertEqual(ca.mesh_bbox(ca.read_stl(b)), ((0, 0, 0), (10, 20, 3)))

    def test_openscad_problems(self):
        stderr = "Geometries in cache: 1\nWARNING: unknown module\nERROR: boom\n"
        self.assertEqual(ca.openscad_problems(stderr, 1), ["WARNING: unknown module", "ERROR: boom"])
        self.assertIn("no geometry", ca.openscad_problems("Current top level object is empty.", 1)[0])
        self.assertEqual(ca.openscad_problems("fine\n", 0), [])


# ---------------------------------------------------------------------------
# LLM client
# ---------------------------------------------------------------------------


class TestOllamaAgent(unittest.TestCase):
    def test_request_body(self):
        sent = {}

        def post(url, body, timeout):
            sent.update(url=url, body=body)
            return {"message": {"content": '{"a": 1}'}}

        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "x.png"
            png.write_bytes(b"png")
            agent = ca.OllamaAgent("m", "http://h:1/", post=post)
            self.assertEqual(agent.ask_json("q", {"type": "object"}, images=[png], system="s",
                                            temperature=0.5, seed=3), {"a": 1})
        body = sent["body"]
        self.assertEqual(sent["url"], "http://h:1/api/chat")
        self.assertEqual(body["format"], {"type": "object"})
        self.assertFalse(body["think"])
        self.assertEqual(body["messages"][0], {"role": "system", "content": "s"})
        self.assertEqual(body["messages"][1]["images"], ["cG5n"])
        self.assertEqual(body["options"]["temperature"], 0.5)
        self.assertEqual(body["options"]["seed"], 3)

    def test_vote_takes_more_samples_without_a_majority(self):
        replies = iter(['{"k": "a"}', '{"k": "b"}', '{"k": "c"}', '{"k": "b"}', '{"k": "d"}'])
        agent = ca.OllamaAgent(post=lambda u, b, t: {"message": {"content": next(replies)}})
        self.assertEqual(agent.vote("q", {}, ["k"]), ({"k": "b"}, 2))

    def test_vote_skips_bad_json(self):
        replies = iter(["garbage", '{"k": "x"}', '{"k": "x"}'])
        agent = ca.OllamaAgent(post=lambda u, b, t: {"message": {"content": next(replies)}})
        self.assertEqual(agent.vote("q", {}, ["k"]), ({"k": "x"}, 2))

    def test_judge_panel_averages_and_batches_by_model(self):
        order = []

        def judge(model, p):
            def post(url, body, timeout):
                order.append((model, body["messages"][-1]["content"]))
                self.assertEqual(body["options"]["num_ctx"], 8192)
                return {"logprobs": [{"top_logprobs": [{"token": "yes", "logprob": math.log(p)},
                                                       {"token": "no", "logprob": math.log(1 - p)}]}]}
            return ca.OllamaAgent(model, post=post, num_ctx=8192)

        panel = ca.OllamaAgent("main", judges=[judge("a", 0.9), judge("b", 0.3)],
                               post=lambda u, b, t: self.fail("the main model must not judge"))
        scores = panel.p_yes_many(["q1", "q2"], "bt")
        self.assertEqual([round(s, 3) for s in scores], [0.6, 0.6])
        self.assertEqual(order, [("a", "q1"), ("a", "q2"), ("b", "q1"), ("b", "q2")])
        self.assertAlmostEqual(panel.p_yes("q3"), 0.6)

    def test_transcript_logging(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = ca.OllamaAgent(log_dir=Path(tmp), post=lambda u, b, t: {"message": {"content": "hi"}})
            agent.chat("prompt text", label="components")
            self.assertIn("prompt text", (Path(tmp) / "001_components.txt").read_text())


# ---------------------------------------------------------------------------
# Shape library against real OpenSCAD
# ---------------------------------------------------------------------------


@needs_openscad
class TestShapesCompile(unittest.TestCase):
    """Every shape variant compiles and measures exactly what size() predicts."""

    CASES = [
        ("box", {"width": 10, "depth": 20, "height": 5}),
        ("cylinder", {"diameter": 10, "height": 30, "axis": "z"}),
        ("cylinder", {"diameter": 10, "height": 30, "axis": "x"}),
        ("cylinder", {"diameter": 10, "height": 30, "axis": "y"}),
        ("tube", {"outer_diameter": 20, "inner_diameter": 16, "height": 30, "axis": "y"}),
        ("sphere", {"diameter": 12}),
    ] + [("panel", {"width": 40, "height": 30, "thickness": 4, "angle": 60, "lean": lean})
         for lean in ca.SIDES4] + [("wedge", {"width": 10, "depth": 20, "height": 15, "high_side": side})
                                    for side in ca.SIDES4]

    def test_measured_size_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i, (name, params) in enumerate(self.CASES):
                shape = ca.SHAPES[name]
                src = Path(tmp) / f"s{i}.scad"
                src.write_text(f"$fn = {ca.SEGMENTS};\n{shape.scad(params)}\n")
                result = ca.compile_scad(src, src.with_suffix(".stl"))
                self.assertTrue(result.ok, (name, params, result.problems))
                lo, hi = result.bbox
                expected = shape.size(params)
                for a in range(3):
                    self.assertAlmostEqual(lo[a], 0, delta=0.05, msg=(name, params, lo))
                    self.assertAlmostEqual(hi[a], expected[a], delta=0.05, msg=(name, params, hi))


# ---------------------------------------------------------------------------
# Behaviours
# ---------------------------------------------------------------------------


class BehaviourTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.design = ca.Design(request=REQUEST, workdir=Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def tick(self, node, n=1):
        out = []
        for _ in range(n):
            node.tick_once()
            out.append(node.status)
        return out

    def understand(self, llm):
        self.tick(ca.ExtractComponents(self.design, llm))
        for comp in self.design.components:
            self.assertEqual(self.tick(ca.component_subtree(self.design, llm, comp)), [Status.SUCCESS])


class TestUnderstand(BehaviourTest):
    def test_component_subtree_decides_everything(self):
        llm = ScriptedLLM(phone_stand_script())
        self.understand(llm)
        base, rest, lip = self.design.components
        self.assertIsNone(base.place)
        self.assertEqual(rest.shape, "panel")
        self.assertEqual(rest.place, {"parent": "base", "side": "top", "x": "center", "y": "back", "z": "center"})
        self.assertEqual(lip.place["y"], "front")
        # back_rest has a single possible parent, so no parent question was asked for it
        self.assertNotIn("parent_back_rest", llm.labels())

    def test_clean_components_are_not_asked_again(self):
        llm = ScriptedLLM(phone_stand_script())
        self.understand(llm)
        n = len(llm.calls)
        for comp in self.design.components:
            self.tick(ca.component_subtree(self.design, llm, comp))
        self.assertEqual(len(llm.calls), n)

    def test_place_note_reasks_only_placement(self):
        llm = ScriptedLLM(phone_stand_script())
        self.understand(llm)
        lip = self.design.component("lip")
        lip.notes["place"] = ["wrong side"]
        lip.rejected["side"] = [("base", "top")]
        n = len(llm.calls)
        self.tick(ca.component_subtree(self.design, llm, lip))
        new = llm.labels()[n:]
        self.assertTrue(new and all(l.startswith(("parent_lip", "side_lip", "spans_lip", "align_lip"))
                                    for l in new), new)
        self.assertNotEqual(lip.place["side"], "top")  # the rejected option is never offered again
        self.assertNotIn("place", lip.notes)

    def test_invalid_params_are_retried_with_errors(self):
        llm = ScriptedLLM(phone_stand_script(params_base=[
            {"reasoning": "", "width": -1, "depth": 60, "height": 5},
            {"reasoning": "", "width": 80, "depth": 60, "height": 5}]))
        self.tick(ca.ExtractComponents(self.design, llm))
        base = self.design.components[0]
        base.shape = "box"
        self.assertEqual(self.tick(ca.FillParams(self.design, llm, base)), [Status.SUCCESS])
        self.assertIn("width must be above 0", llm.calls[-1][1])
        self.assertEqual(base.params["width"], 80)

    def test_unused_number_is_routed_to_component(self):
        llm = ScriptedLLM(phone_stand_script(
            params_back_rest=[{"reasoning": "", "width": 80, "height": 70, "thickness": 5,
                               "angle": 60, "lean": "back"}],
            number=[{"reasoning": "", "component": "back_rest"}]))
        self.understand(llm)
        self.assertEqual(self.tick(ca.AccountForNumbers(self.design, llm)), [Status.FAILURE])
        self.assertIn("exactly 70 degrees", self.design.component("back_rest").notes["params"][0])


class TestDescribeAndCopies(BehaviourTest):
    def stool(self, arrangement="corners_xy"):
        self.design.components = [
            ca.Component("seat", "round seat", "cylinder", {"diameter": 300, "height": 20, "axis": "z"}),
            ca.Component("leg", "square leg", "box", {"width": 30, "depth": 30, "height": 400},
                         {"parent": "seat", "side": "bottom", "x": "center", "y": "center", "z": "center"},
                         count=4, arrangement=arrangement),
        ]
        ca.layout(self.design)
        return self.design.components

    def test_corner_copies_and_regrounding(self):
        seat, leg = self.stool()
        self.assertEqual(len(set(leg.positions)), 4)
        for x, y, z in leg.positions:  # on a round seat the corner legs are pulled in under the circle
            self.assertEqual(z, 0)
            for cx in (x, x + 30):
                for cy in (y, y + 30):
                    self.assertLess(math.hypot(cx - 150, cy - 150), 150)
        self.assertEqual(seat.position, (0, 0, 400))  # the legs stand on the table, the seat on them

    def test_describe_back_translates_the_layout(self):
        _, leg = self.stool()
        text = ca.describe(self.design, leg)
        self.assertIn("There are 4 leg parts", text)
        self.assertIn("are fixed underneath the seat", text)
        self.assertIn("one near each corner of the seat", text)

    def test_describe_flags_a_part_covering_its_parent(self):
        self.design.components = [
            ca.Component("base", "plate", "box", {"width": 80, "depth": 60, "height": 5}),
            ca.Component("lip", "lip", "box", {"width": 80, "depth": 60, "height": 10},
                         {"parent": "base", "side": "top", "x": "center", "y": "front", "z": "center"}),
        ]
        ca.layout(self.design)
        self.assertIn("covering the base's whole top surface", ca.describe(self.design, self.design.components[1]))

    def test_describe_edges_and_lean(self):
        self.design.components = [
            ca.Component("base", "plate", "box", {"width": 80, "depth": 60, "height": 5}),
            ca.Component("back_rest", "rest", "panel",
                         {"width": 80, "height": 70, "thickness": 5, "angle": 70, "lean": "back"},
                         {"parent": "base", "side": "top", "x": "center", "y": "back", "z": "center"}),
        ]
        ca.layout(self.design)
        text = ca.describe(self.design, self.design.components[1])
        self.assertIn("leaning backwards at 70 degrees", text)
        self.assertIn("sits on top of the base, running the full width of the base, along the base's back edge", text)

    def test_ends_and_rows(self):
        self.assertEqual(ca.instance_fractions("ends_x", 2), [{"x": 0.0}, {"x": 1.0}])
        self.assertEqual(ca.instance_fractions("row_y", 3), [{"y": 0.0}, {"y": 0.5}, {"y": 1.0}])
        self.assertEqual(ca.instance_fractions(None, 1), [{}])


class TestVerify(BehaviourTest):
    def setUp(self):
        super().setUp()
        self.design.components = [
            ca.Component("base", "plate", "box", {"width": 80, "depth": 60, "height": 5}),
            ca.Component("lip", "lip", "box", {"width": 80, "depth": 60, "height": 10},
                         {"parent": "base", "side": "top", "x": "center", "y": "front", "z": "center"}),
        ]
        ca.layout(self.design)

    def test_pass_marks_verified_and_is_not_asked_again(self):
        self.design.components[1].params["depth"] = 5
        ca.layout(self.design)
        llm = ScriptedLLM({"verify_": [YES]})
        node = ca.VerifyComponent(self.design, llm, self.design.components[1])
        self.tick(node)
        self.tick(node)
        self.assertEqual(len(llm.calls), 2)  # two samples agreed on the first tick; nothing on the second
        self.assertEqual(self.design.flagged, [])
        self.assertEqual(self.design.components[1].status, "verified")
        self.assertTrue(ca.verification_summary(self.design)["verified"] == ["lip"])

    def test_failure_repairs_by_ranking_neighbours(self):
        def judge(prompt):
            design = next(l for l in prompt.splitlines() if l.startswith("In the current design:"))
            return YES if "5 mm deep" in design and "front edge" in design else NO
        llm = ScriptedLLM({"verify_": [judge], "repair_": [judge],
                           "params_lip": [{"reasoning": "", "width": 80, "depth": 5, "height": 10}]})
        lip = self.design.components[1]
        old = lip.spec_key()
        self.tick(ca.VerifyComponent(self.design, llm, lip))
        self.assertEqual(self.design.flagged, ["lip"])
        self.assertEqual(lip.params["depth"], 5)
        self.assertEqual(lip.place["y"], "front")
        self.assertIn(old, lip.rejected["spec"])

    def test_rejected_designs_are_never_candidates(self):
        lip = self.design.components[1]
        node = ca.VerifyComponent(self.design, ScriptedLLM({"params_lip": [
            {"reasoning": "", "width": 80, "depth": 60, "height": 10}]}), lip)
        lip.rejected["spec"] = [node.neighbours("built")["side=front"].spec_key()]
        candidates = node.neighbours("built")
        self.assertNotIn("side=front", candidates)
        self.assertIn("side=back", candidates)
        self.assertNotIn("span_y", candidates)  # it already runs the full depth


class TestSizeMoves(BehaviourTest):
    def test_swap_and_thin_moves(self):
        self.design.components = [
            ca.Component("base", "plate", "box", {"width": 80, "depth": 60, "height": 5}),
            ca.Component("front_lip", "lip", "box", {"width": 80, "depth": 60, "height": 10},
                         {"parent": "base", "side": "top", "x": "center", "y": "front", "z": "center"}),
        ]
        ca.layout(self.design)
        lip = self.design.components[1]
        moves = ca.VerifyComponent(self.design, ScriptedLLM({}), lip).size_moves()
        self.assertEqual(moves["depth=10"].params, {"width": 80, "depth": 10, "height": 10})
        self.assertEqual(moves["depth=5"].params["depth"], 5)       # the parent's thickness
        self.assertEqual(moves["swap_depth_height"].params["height"], 60)
        self.assertEqual(lip.params["depth"], 60)                   # the original is untouched


class TestSearchStops(BehaviourTest):
    def setUp(self):
        super().setUp()
        self.design.components = [
            ca.Component("base", "plate", "box", {"width": 80, "depth": 60, "height": 5}),
            ca.Component("lip", "lip", "box", {"width": 80, "depth": 5, "height": 10},
                         {"parent": "base", "side": "top", "x": "center", "y": "front", "z": "center"}),
        ]
        ca.layout(self.design)

    def test_local_optimum_is_kept_but_reported_unsatisfied(self):
        # The verifier says no, but no neighbour describes better than the current design.
        def judge(prompt):
            design = next(l for l in prompt.splitlines() if l.startswith("In the current design:"))
            return YES if "5 mm thick (front to back)" in design and "front edge" in design else NO
        llm = ScriptedLLM({"verify_": [NO], "repair_": [judge],
                           "params_lip": [{"reasoning": "", "width": 80, "depth": 30, "height": 10}]})
        lip = self.design.components[1]
        self.tick(ca.VerifyComponent(self.design, llm, lip))
        self.assertEqual(self.design.flagged, [])
        self.assertEqual(lip.verified, lip.spec_key())  # the search stops...
        self.assertEqual(lip.params["depth"], 5)
        self.assertEqual(lip.status, "unsatisfied")      # ...but it is not called a pass
        self.assertTrue(lip.residual[0].startswith("stagnated"))
        self.assertTrue(any("back-translation" in r for r in lip.residual))

    def test_out_of_attempts_restores_the_best_version(self):
        lip = self.design.components[1]
        good = {"params": dict(lip.params), "place": dict(lip.place), "arrangement": None,
                "shape": "box", "count": 1}
        bad = dict(good, params={"width": 5, "depth": 5, "height": 10})
        lip.history = [(1, 0.0, 0, bad), (0, 0.0, 1, good), (0, 0.0, 2, bad)]
        lip.params = dict(bad["params"])
        lip.verify_attempts = 6
        self.tick(ca.VerifyComponent(self.design, ScriptedLLM({}), lip))
        self.assertEqual(lip.params, good["params"])

    def test_out_of_attempts_is_a_typed_failure_not_a_pass(self):
        lip = self.design.components[1]
        snap = {"params": dict(lip.params), "place": dict(lip.place), "arrangement": None,
                "shape": "box", "count": 1}
        lip.history = [(0, 0.0, 0, snap)]
        lip.verify_attempts = 6
        self.tick(ca.VerifyComponent(self.design, ScriptedLLM({}), lip))
        self.assertEqual(lip.status, "unsatisfied")
        self.assertTrue(lip.residual[0].startswith("saturated"))
        self.assertEqual([c.name for c in self.design.unsatisfied()], ["lip"])
        summary = ca.verification_summary(self.design)
        self.assertFalse(summary["all_verified"])
        self.assertEqual(summary["unsatisfied"], ["lip"])
        self.assertIn("UNSATISFIED", ca.component_report(self.design, lip))
        self.assertNotIn("UNSATISFIED", ca.describe(self.design, lip))  # never leaks into back-translation
        self.assertTrue(any(n.startswith("UNSATISFIED lip:") for n in self.design.feedback_notes))
        record = json.loads(ca.write_design_json(self.design, "unsatisfied").read_text())
        self.assertEqual(record["verification"]["unsatisfied"], ["lip"])
        self.assertEqual(record["components"][1]["status"], "unsatisfied")
        self.assertTrue(record["components"][1]["residual"])

    def test_human_review_shows_unsatisfied(self):
        lip = self.design.components[1]
        lip.status, lip.residual = "unsatisfied", ["saturated: out of verification attempts (6)"]
        printed = []
        node = ca.HumanReview(self.design, ScriptedLLM({}), input_fn=lambda _: "")
        with mock.patch("builtins.print", side_effect=lambda *a, **k: printed.append(" ".join(map(str, a)))):
            self.tick(node)
        text = "\n".join(printed)
        self.assertIn("UNSATISFIED: saturated", text)
        self.assertIn("failed verification: lip", text)


class TestSeedAndL1(unittest.TestCase):
    def test_seed_zero_is_unchanged_and_other_seeds_differ(self):
        sent = []
        def post(url, body, timeout):
            sent.append(body["options"])
            return {"message": {"content": "{}"}}
        ca.OllamaAgent(post=post).chat("hi", temperature=0.0, seed=1)
        ca.OllamaAgent(post=post, seed_offset=2).chat("hi", temperature=0.0, seed=1)
        ca.OllamaAgent(post=post, seed_offset=2).chat("hi", temperature=0.7, seed=1)
        self.assertEqual((sent[0]["temperature"], sent[0]["seed"]), (0.0, 1))
        self.assertEqual((sent[1]["temperature"], sent[1]["seed"]), (ca.SEED_TEMPERATURE, 2001))
        self.assertEqual(sent[2]["temperature"], 0.7)

    def test_load_l1_from_inline_json_file_and_benchmark_entry(self):
        inline = '[{"id": "L1.1", "text": "The base shall be 80 mm wide.", "method": "inspection"}, "Stands up."]'
        l1 = ca.load_l1(inline)
        self.assertEqual(l1[0], {"id": "L1.1", "text": "The base shall be 80 mm wide.", "method": "inspection"})
        self.assertEqual(l1[1], {"id": "L1.2", "text": "Stands up.", "method": None})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "l1.json"
            path.write_text(json.dumps({"id": "X", "request": "r", "l1": [{"id": "A", "text": "t"}]}))
            self.assertEqual(ca.load_l1(str(path))[0]["id"], "A")
        with self.assertRaises(ValueError):
            ca.load_l1('{"nothing": 1}')
        with self.assertRaises(ValueError):
            ca.load_l1('[{"id": "L1.1"}]')

    def test_request_with_l1(self):
        self.assertEqual(ca.request_with_l1("A cup.", []), "A cup.")
        text = ca.request_with_l1("A cup.", [{"id": "L1.1", "text": "It shall be 80 mm tall."},
                                             {"id": "L1.2", "text": "It shall stand up"}])
        self.assertEqual(text, "A cup. Requirements: It shall be 80 mm tall. It shall stand up.")
        self.assertEqual([n[0] for n in ca.request_numbers(text)], [80])  # the ids add no numbers
        self.assertEqual(ca.scad_comment("a\nb  c"), "// a b c")

    def test_main_records_seed_and_l1(self):
        # Stop the run at the first LLM call; design.json must still record the settings.
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(ca, "run", side_effect=KeyboardInterrupt), \
                mock.patch("builtins.print"):
            rc = ca.main(["--auto", "--out", tmp, "--seed", "3",
                          "--l1", '[{"id": "L1.1", "text": "It shall be 9 mm thick.", "method": "inspection"}]',
                          "A plate."])
            self.assertEqual(rc, 130)
            record = json.loads(next(Path(tmp).glob("*/design.json")).read_text())
        self.assertEqual(record["seed"], 3)
        self.assertEqual(record["l1"][0]["id"], "L1.1")
        self.assertEqual(record["base_request"], "A plate.")
        self.assertIn("Requirements: It shall be 9 mm thick.", record["request"])
        self.assertEqual(record["outcome"], "interrupted")


class TestExtractionCleanup(BehaviourTest):
    def test_duplicates_dropped_and_base_first(self):
        llm = ScriptedLLM({"components": [{"components": [
            {"name": "cup", "count": 1, "description": "round cup 70 mm across and 100 mm tall"},
            {"name": "base", "count": 1, "description": "square base 90 x 90 x 6 mm"},
            {"name": "cup_copy", "count": 1, "description": "round cup 70 mm across and 100 mm tall"},
        ]}]})
        self.tick(ca.ExtractComponents(self.design, llm))
        self.assertEqual([c.name for c in self.design.components], ["base", "cup"])

    def test_parts_differing_by_place_or_number_kept(self):
        walls = [ca.Component("floor", "flat rectangular plate 150 x 100 x 3 mm"),
                 ca.Component("front wall", "wall 30 mm high and 3 mm thick running along the front edge of the floor"),
                 ca.Component("back wall", "wall 30 mm high and 3 mm thick running along the back edge of the floor"),
                 ca.Component("low wall", "back wall 90 x 5 x 10 mm standing up from the edge of the base"),
                 ca.Component("high wall", "back wall 90 x 5 x 20 mm standing up from the edge of the base")]
        self.assertEqual(len(ca.dedupe_components(walls)), 5)

    def test_parent_named_in_description(self):
        self.design.components = [
            ca.Component("base", "round base", "cylinder", {"diameter": 120, "height": 10, "axis": "z"}),
            ca.Component("post", "post in the middle of the base", "cylinder", {"diameter": 25, "height": 250, "axis": "z"}),
            ca.Component("bar", "horizontal bar on top of the post", "box", {"width": 100, "depth": 25, "height": 25}),
        ]
        for c in self.design.components:
            c.others = [o.name for o in self.design.components if o is not c]
        bar = self.design.components[2]
        bar.draft = {}
        self.tick(ca.ChooseParent(self.design, ScriptedLLM({}), bar))
        self.assertEqual(bar.draft["parent"], "post")

    def test_roles_for_copies(self):
        req = ("A napkin holder: a 150 x 60 x 6 mm base with two upright panels 150 mm wide, 90 mm tall "
               "and 4 mm thick, one along the front edge and one along the back edge.")
        same_name = [("base", "rectangular base 150 x 60 x 6 mm", 1),
                     ("panel", "upright panel 150 mm wide standing on the base along its front edge", 2),
                     ("panel", "upright panel 150 mm wide standing on the base along its back edge", 1)]
        comps = ca.assign_roles(same_name, req)
        self.assertEqual([(c.name, c.count) for c in comps], [("base", 1), ("front_panel", 1), ("back_panel", 1)])
        one_entry = [("base", "rectangular base", 1),
                     ("panel", "two upright panels 150 mm wide, one along the front edge and one along the back edge", 2)]
        comps = ca.assign_roles(one_entry, req)
        self.assertEqual([c.name for c in comps], ["base", "front_panel", "back_panel"])
        self.assertNotIn("front", comps[2].description)
        self.assertEqual(comps[1].description, "upright panel 150 mm wide, along the front edge")
        faces = ca.assign_roles([("wedge", "wedge 300 x 60 x 20 mm", 1), ("top_surface", "the sloped top", 1),
                                 ("front_edge", "the thin front edge", 1), ("left_side", "left side of the block", 1),
                                 ("lip", "lip along the front edge", 1)], "x")
        self.assertEqual([c.name for c in faces], ["wedge", "lip"])
        legs = ca.assign_roles([("seat", "seat", 1), ("leg", "four legs, one at each corner", 4)], "a stool")
        self.assertEqual([(c.name, c.count) for c in legs], [("seat", 1), ("leg", 4)])

    def test_ball_has_feasible_sides(self):
        plate = ca.Component("plate", "plate", "box", {"width": 150, "depth": 150, "height": 6})
        ball = ca.Component("foot", "ball under each corner", "sphere", {"diameter": 15})
        self.design.components = [plate, ball]
        ca.layout(self.design)
        feasible = ca.feasible_attachments(self.design, ball, plate)
        self.assertIn("bottom", feasible)
        self.assertIn({"x": "left", "y": "front"}, feasible["bottom"])

    def test_triangle_of_three(self):
        self.assertEqual(len(ca.instance_fractions("triangle_xy", 3)), 3)
        self.assertEqual(ca.arrangement_cue(ca.Component("leg", "three round legs")), "triangle")


class TestCues(BehaviourTest):
    def comp(self, name, description, **kw):
        return ca.Component(name, description, **kw)

    def test_shape_cues(self):
        self.assertEqual(ca.shape_cue(self.comp("seat", "round seat 300 mm across")), "cylinder")
        self.assertEqual(ca.shape_cue(self.comp("cup", "round cup 60 mm wide")), "tube")
        self.assertEqual(ca.shape_cue(self.comp("gusset", "brace on each side")), "wedge")
        self.assertEqual(ca.shape_cue(self.comp("back_rest", "leaning back at 70 degrees")), "panel")
        self.assertIsNone(ca.shape_cue(self.comp("base", "80x60x5 mm plate")))

    def test_placement_cues(self):
        leg = self.comp("leg", "square leg 400 mm tall")
        lip = self.comp("front_lip", "10 mm lip to stop the phone sliding off")
        self.assertEqual(ca.side_cue(leg), "bottom")
        self.assertEqual(ca.edge_cue(lip, "y"), "front")
        self.assertEqual(ca.arrangement_cue(self.comp("gusset", "a gusset on each side")), "ends_x")

    def test_other_components_names_are_not_cues(self):
        base = self.comp("base", "base plate 250 x 200 x 6 mm under the wedge", others=["wedge"])
        self.assertIsNone(ca.shape_cue(base))
        self.assertEqual(ca.shape_cue(self.comp("rim", "3 mm high rim around the edge")), "tube")

    @needs_openscad
    def test_wedge_under_a_board_is_flipped_flat_side_up(self):
        self.design.components = [
            ca.Component("board", "shelf board", "box", {"width": 300, "depth": 150, "height": 10}),
            ca.Component("bracket", "bracket", "wedge", {"width": 10, "depth": 150, "height": 100, "high_side": "back"},
                         {"parent": "board", "side": "bottom", "x": "left", "y": "center", "z": "center"}),
        ]
        ca.layout(self.design)
        board, bracket = self.design.components
        area = ca.contact_area(bracket, bracket.position, board, board.position, self.design.workdir / "checks")
        self.assertAlmostEqual(area, 10 * 150, delta=20)  # the whole flat face touches the board

    def test_contradiction_fails_verification_without_the_model(self):
        self.design.components = [
            ca.Component("base", "plate", "box", {"width": 80, "depth": 60, "height": 5}),
            ca.Component("front_lip", "lip", "box", {"width": 80, "depth": 5, "height": 10},
                         {"parent": "base", "side": "top", "x": "center", "y": "back", "z": "center"}),
        ]
        ca.layout(self.design)
        lip = self.design.components[1]
        self.assertEqual(ca.cue_conflicts(self.design, lip), ["its placement contradicts its description"])
        llm = ScriptedLLM({"repair_": [NO], "params_": [{"reasoning": "", "width": 80, "depth": 5, "height": 10}]})
        self.tick(ca.VerifyComponent(self.design, llm, lip))
        self.assertNotIn("verify_front_lip", llm.labels())
        self.assertEqual(lip.place["y"], "front")  # the repair search follows the cue


class TestHumanReview(BehaviourTest):
    def setUp(self):
        super().setUp()
        self.design.components = [ca.Component("base", "plate", "box", {"width": 1, "depth": 1, "height": 1}),
                                  ca.Component("lip", "lip", "box", {"width": 1, "depth": 1, "height": 1},
                                               {"parent": "base", "side": "top"})]

    def review(self, answer, llm=None):
        node = ca.HumanReview(self.design, llm or ScriptedLLM({}), input_fn=lambda _: answer)
        with mock.patch("builtins.print"):
            return self.tick(node)[0]

    def test_accept_and_quit(self):
        self.assertEqual(self.review(""), Status.SUCCESS)
        with self.assertRaises(ca.UserAbort):
            self.review("q")

    def test_feedback_routes_changes(self):
        llm = ScriptedLLM({"feedback": [{"changes": [
            {"component": "lip", "change": "params", "instruction": "make it 15 mm tall"},
            {"component": "new", "change": "add", "instruction": "cable hole block at the back"},
        ]}]})
        self.assertEqual(self.review("taller lip and a cable block", llm), Status.FAILURE)
        self.assertIn("15 mm", self.design.component("lip").notes["params"][0])
        self.assertEqual(len(self.design.components), 3)
        self.assertTrue(self.design.components[2].needs("shape"))

    def test_remove_detaches_children(self):
        self.design.components.append(ca.Component("knob", "knob", "sphere", {"diameter": 1},
                                                   {"parent": "lip", "side": "top"}))
        llm = ScriptedLLM({"feedback": [{"changes": [
            {"component": "lip", "change": "remove", "instruction": "no lip"}]}]})
        self.review("remove the lip", llm)
        self.assertIsNone(self.design.component("lip"))
        self.assertIsNone(self.design.component("knob").place)


@needs_openscad
class TestBuild(BehaviourTest):
    def build(self, components):
        self.design.components = components
        nodes = [ca.Layout(self.design), ca.EmitScad(self.design), ca.CompileCheck(self.design),
                 ca.PhysicalChecks(self.design)]
        return [self.tick(n)[0] for n in nodes]

    def stand(self, rest_place=None):
        return [
            ca.Component("base", "plate", "box", {"width": 80, "depth": 60, "height": 5}),
            ca.Component("back_rest", "rest", "panel",
                         {"width": 80, "height": 70, "thickness": 5, "angle": 70, "lean": "back"},
                         rest_place or {"parent": "base", "side": "top", "x": "center", "y": "back", "z": "center"}),
            ca.Component("lip", "lip", "box", {"width": 80, "depth": 5, "height": 10},
                         {"parent": "base", "side": "top", "x": "center", "y": "front", "z": "center"}),
        ]

    def test_good_stand_builds_as_one_stable_body(self):
        self.assertEqual(self.build(self.stand()), [Status.SUCCESS] * 4)
        self.assertTrue(self.design.stability["stable"])
        self.assertIn("translate([0, 29.201, 5]) c_back_rest();", self.design.assembly.read_text())

    def test_panel_on_back_face_floats_and_is_sent_back(self):
        # Against the back face, a backward-leaning panel touches the plate's bbox but not the plate.
        statuses = self.build(self.stand(rest_place={"parent": "base", "side": "back", "x": "center",
                                                     "y": "center", "z": "center"}))
        self.assertEqual(statuses[2], Status.FAILURE)
        self.assertIn("did not touch base", self.design.component("back_rest").notes["place"][0])

    def test_tipping_routes_to_overhanging_part(self):
        base = ca.Component("base", "plate", "box", {"width": 30, "depth": 20, "height": 2})
        heavy = ca.Component("block", "heavy block", "box", {"width": 30, "depth": 80, "height": 40},
                             {"parent": "base", "side": "top", "x": "center", "y": "back", "z": "center"})
        statuses = self.build([base, heavy])
        self.assertEqual(statuses[3], Status.FAILURE)
        self.assertIn("sticks out", heavy.notes["params"][0])


@needs_openscad
class TestFullTree(BehaviourTest):
    def test_phone_stand_end_to_end_with_feedback(self):
        llm = ScriptedLLM(phone_stand_script(
            feedback=[{"changes": [{"component": "lip", "change": "params",
                                    "instruction": "make the lip 15 mm tall"}]}],
            params_lip=[{"reasoning": "", "width": 80, "depth": 5, "height": 10},
                        {"reasoning": "", "width": 80, "depth": 5, "height": 15}]))
        answers = iter(["make the lip 15 mm tall", ""])
        root = ca.build_tree(self.design, llm, llm, input_fn=lambda _: next(answers))
        with mock.patch("builtins.print"):
            status = ca.run(root)
        self.assertEqual(status, Status.SUCCESS)
        self.assertTrue(self.design.export_path.exists())
        self.assertEqual(self.design.component("lip").params["height"], 15)
        # After the feedback only the lip was reworked and re-verified (plus the visual checks).
        labels = llm.labels()
        after = labels[labels.index("feedback") + 1:]
        self.assertEqual(sorted(set(l for l in after if not l.startswith("visual_"))), ["params_lip", "verify_lip"])
        self.assertEqual(set(self.design.views), set(ca.VIEWS))
        self.assertEqual(set(self.design.highlights), {"base", "back_rest", "lip"})

    def test_visual_no_triggers_targeted_repair(self):
        script = phone_stand_script(
            repair_back_rest=[{"reasoning": "", "aspect": "params"}],
            params_back_rest=[
                {"reasoning": "", "width": 80, "height": 70, "thickness": 5, "angle": 70, "lean": "front"},
                {"reasoning": "", "width": 80, "height": 70, "thickness": 5, "angle": 70, "lean": "back"}])
        # back_rest: probe no, verdict no, confirmation no; after the repair: probe no, verdict yes
        script["visual_back_rest"] = [
            {"reasoning": "", "answer": "no"}, {"reasoning": "leans forward", "answer": "no"},
            {"reasoning": "leans forward", "answer": "no"}, {"reasoning": "", "answer": "no"},
            {"reasoning": "", "answer": "yes"}]
        llm = ScriptedLLM(script)
        root = ca.build_tree(self.design, llm, llm, auto_approve=True)
        self.assertEqual(ca.run(root), Status.SUCCESS)
        self.assertEqual(self.design.component("back_rest").params["lean"], "back")
        last_params_prompt = [c for c in llm.calls if c[0] == "params_back_rest"][-1][1]
        self.assertIn("leans forward", last_params_prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
