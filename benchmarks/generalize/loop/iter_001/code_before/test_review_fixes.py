"""Regression tests for the confirmed review findings on the cascade and the typed checks.

Each test names the finding it pins down. Standard-library unittest with fakes
(no network); layer-2 checks use manifold3d, and the one end-to-end cascade run
needs OpenSCAD (skipped without it).
"""

import json
import math
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

import py_trees
from py_trees.common import Status

import cad_agent as ca
import cad_checks as cc
import cascade as cs
from test_cad_agent import YES, ScriptedLLM, needs_openscad, phone_stand_script
from test_cad_checks import comp, design, place, real, result
from test_cascade import (PHONE_L1, CascadeLLM, ExplodingLLM, bookend, chk, make_design, phone_stand,
                          tick_until_done)


# ---------------------------------------------------------------------------
# Cascade: an L1's own translated checks are never ignored or dropped
# ---------------------------------------------------------------------------


class TestTranslatedChecksStayLevelOne(unittest.TestCase):
    """A failing check carrying the L1's own number must fail the L1 (findings 1, 4, 5)."""

    L1 = [{"id": "L1.1", "text": "The base shall be 200 mm wide so that the stand does not tip over.",
           "method": "analysis"}]

    def setUp(self):
        py_trees.blackboard.Blackboard.clear()
        self.d = phone_stand()          # base 80 mm wide
        st = self.d.cascade
        st.l1 = list(self.L1)
        st.drafts = {"L1.1": [chk("L1.1.c1", "stable", tilt_deg=5.0),
                              chk("L1.1.c2", "dimension", part="base", measure="width", value=200)]}
        self.assertEqual(cs.FreezeChecks(self.d).update(), Status.SUCCESS)

    def test_translated_checks_are_level_one(self):
        self.assertEqual({c.id: c.level for c in self.d.cascade.checks if c.l1_id == "L1.1"},
                         {"L1.1.c1": 1, "L1.1.c2": 1})

    def test_refine_never_drops_a_translated_check(self):
        st = self.d.cascade
        status = cs.RefineChecks(self.d, ExplodingLLM()).update()
        self.assertEqual(status, Status.SUCCESS)          # nothing to add or drop
        self.assertIn("L1.1.c2", [c.id for c in st.checks])
        self.assertEqual(st.dropped, [])
        rec = cs.finalize(self.d)
        row = next(r for r in rec["rows"] if r["l1_id"] == "L1.1")
        self.assertEqual(row["status"], "fail")
        self.assertLess(row["margin"], 0)
        self.assertEqual(rec["outcome"], "unsatisfied")

    def test_row_fails_even_when_the_outer_loop_is_capped(self):
        self.d.cascade.outer_iterations = cs.MAX_OUTER
        self.assertEqual(cs.RefineChecks(self.d, ExplodingLLM()).update(), Status.SUCCESS)
        self.assertEqual(cs.finalize(self.d)["outcome"], "unsatisfied")

    def test_dropping_a_refinement_rechecks_number_coverage(self):
        st = self.d.cascade
        # A refinement (level 2) that alone carried the L1's 200: when it is dropped the number
        # must come back as unchecked, so the row cannot pass.
        st.checks = [chk("L1.1.c1", "stable", tilt_deg=5.0),
                     chk("L1.1.r9", "dimension", level=2, part="base", measure="width", value=200)] \
            + cs.system_checks()
        st.translation = {"L1.1": {"uncovered": [], "rejected": []}}
        self.assertEqual(cs.RefineChecks(self.d, ExplodingLLM()).update(), Status.FAILURE)
        self.assertEqual([x["check"]["id"] for x in st.dropped], ["L1.1.r9"])
        self.assertEqual([u["value"] for u in st.translation["L1.1"]["uncovered"]], [200.0])
        row = next(r for r in cs.finalize(self.d)["rows"] if r["l1_id"] == "L1.1")
        self.assertEqual(row["status"], "unverified")


class TestDesignJsonFollowsTheMatrix(unittest.TestCase):
    """design.json may not say all_verified next to an unsatisfied outcome (finding 3)."""

    def test_orphan_failures_mark_every_component(self):
        d = bookend()
        st = d.cascade
        st.l1 = [{"id": "L1.1", "text": "The ghost shall be 10 mm wide.", "method": "inspection"},
                 {"id": "L1.2", "text": "It shall look nice.", "method": "human"}]
        st.checks = [chk("L1.1.c1", "dimension", part="ghost", measure="width", value=10)] + cs.system_checks()
        rec = cs.finalize(d)
        self.assertEqual(rec["outcome"], "unsatisfied")
        self.assertTrue(all(c.status == "unsatisfied" for c in d.components))
        summary = ca.verification_summary(d)
        self.assertFalse(summary["all_verified"])
        self.assertEqual(sorted(summary["unsatisfied"]), ["back_plate", "base"])
        record = json.loads(ca.write_design_json(d, rec["outcome"]).read_text())
        self.assertFalse(record["verification"]["all_verified"])
        self.assertEqual(sorted(record["verification"]["l1_not_passed"]), ["L1.1", "L1.2"])

    def test_verified_outcome_keeps_components_verified(self):
        d = bookend()
        d.cascade.l1 = [{"id": "L1.1", "text": "The base shall be 120 mm wide.", "method": "inspection"}]
        d.cascade.checks = [chk("L1.1.c1", "dimension", part="base", measure="width", value=120)] \
            + cs.system_checks()
        self.assertEqual(cs.finalize(d)["outcome"], "verified")
        self.assertTrue(ca.verification_summary(d)["all_verified"])
        record = json.loads(ca.write_design_json(d, "verified").read_text())
        self.assertTrue(record["verification"]["all_verified"])


# ---------------------------------------------------------------------------
# Typed checks
# ---------------------------------------------------------------------------


class TestFitsEnclosure(unittest.TestCase):
    """fits drops into each container and requires walls around the object (finding 6)."""

    def posts(self, count, shape="cylinder", params=None):
        return design(comp("base", "box", {"width": 200, "depth": 80, "height": 5}),
                      comp("cup", shape, params or {"diameter": 30, "height": 80, "axis": "z"}, place("base"),
                           count=count, arrangement="row_x"))

    def test_solid_posts_are_not_cups_whatever_their_count(self):
        for n in (2, 3):
            r = result(self.posts(n), "fits", object="pencil", into=["cup"])
            self.assertFalse(r.passed, f"{n} posts: {r.evidence['detail']}")

    def test_each_tube_holds_the_pencil(self):
        tubes = self.posts(2, "tube", {"outer_diameter": 40, "inner_diameter": 30, "height": 80, "axis": "z"})
        r = result(tubes, "fits", object="pencil", into=["cup"])
        self.assertTrue(r.passed, r.evidence["detail"])
        self.assertIn("walled in on 4 of 4 sides", r.evidence["detail"])

    def test_a_plate_with_one_wall_is_not_a_tray(self):
        tray = design(comp("floor", "box", {"width": 150, "depth": 100, "height": 3}),
                      comp("front_wall", "box", {"width": 150, "depth": 3, "height": 30}, place("floor", y="front")))
        for depth in (None, 20):
            r = result(tray, "fits", object="box", size=[100, 60, 20], into=["floor", "front_wall"],
                       orientation="flat", min_depth=depth)
            self.assertFalse(r.passed, r.evidence["detail"])
            self.assertIn("open:", r.evidence["detail"])

    def test_a_cup_on_a_base_still_fits(self):
        self.assertTrue(result(real("toothbrush_good"), "fits", object="cylinder", size=[18, 190],
                               into=["cup"]).passed)


class TestRelationNeedsRealContact(unittest.TestCase):
    """'on top of, touching' is measured on the solids, not the boxes (finding 7)."""

    def headphone(self, shift):
        d = real("headphone_good")
        post = d.component("post")
        lo = post.positions[0]
        post.positions = [(lo[0] + shift, lo[1] + shift, lo[2])]
        return d

    def test_diagonal_round_post_off_the_round_base_fails(self):
        d = self.headphone(60.5)   # boxes overlap 12 mm in x and y; the round parts do not touch
        r = result(d, "relation", part="post", relation="on_top_of", other="base")
        self.assertFalse(r.passed, r.evidence["detail"])
        self.assertIn("contact 0", r.evidence["detail"])
        self.assertTrue(result(self.headphone(0), "relation", part="post", relation="on_top_of",
                               other="base").passed)

    def test_corner_overlap_is_not_support(self):
        d = real("toothbrush_good")
        cup = d.component("cup")
        lo = cup.positions[0]
        cup.positions = [(lo[0] + 88, lo[1], lo[2])]   # the cup now overlaps the base by 2 mm
        r = result(d, "relation", part="cup", relation="on_top_of", other="base")
        self.assertFalse(r.passed, r.evidence["detail"])


class TestShapeOrientation(unittest.TestCase):
    """upright / flat are exclusive for round parts; 'z' is worded as it is checked (finding 8)."""

    def test_flat_disc_is_flat_not_upright(self):
        disc = design(comp("body", "cylinder", {"diameter": 100, "height": 5, "axis": "z"}))
        self.assertFalse(result(disc, "shape", part="body", shape="cylinder", orient="upright").passed)
        self.assertTrue(result(disc, "shape", part="body", shape="cylinder", orient="flat").passed)

    def test_disc_on_its_edge_is_upright(self):
        wheel = design(comp("body", "cylinder", {"diameter": 100, "height": 5, "axis": "y"}))
        self.assertTrue(result(wheel, "shape", part="body", shape="cylinder", orient="upright").passed)
        self.assertFalse(result(wheel, "shape", part="body", shape="cylinder", orient="flat").passed)

    def test_post_is_upright(self):
        self.assertTrue(result(real("headphone_good"), "shape", part="post", shape="cylinder",
                               orient="upright").passed)

    def test_orient_z_is_rendered_as_longest_side_vertical(self):
        wall = cc.Check("w", "L1.1", "shape", {"part": "wall", "shape": "box", "orient": "z"})
        self.assertIn("longest side vertical", wall.text)
        self.assertNotIn("upright", wall.text)
        post = cc.Check("p", "L1.1", "shape", {"part": "post", "shape": "cylinder", "orient": "z"})
        self.assertIn("axis vertical", post.text)


class TestRestsOn(unittest.TestCase):
    """The object's side is part of the check (finding 9); a nudge must not tip it (finding 10)."""

    def stand(self, lean, rest_y="back"):
        return design(comp("base", "box", {"width": 80, "depth": 60, "height": 5}),
                      comp("back_rest", "panel", {"width": 70, "height": 80, "thickness": 5, "angle": 70,
                                                  "lean": lean}, place("base", y=rest_y)))

    def test_back_rest_turned_the_wrong_way_fails(self):
        good = result(self.stand("back"), "rests_on", object="phone", support="back_rest", also_touches=["base"])
        self.assertTrue(good.passed, good.evidence["detail"])
        for rest_y in ("back", "front"):
            bad = result(self.stand("front", rest_y), "rests_on", object="phone", support="back_rest",
                         also_touches=["base"])
            self.assertFalse(bad.passed, f"{rest_y}: {bad.evidence['detail']}")

    def test_turn_mutant_is_killed(self):
        d = self.stand("back")
        c = cc.Check("r", "L1.1", "rests_on", {"object": "phone", "support": "back_rest", "also_touches": ["base"]})
        rep = cc.non_vacuity(d, [c])[0]
        self.assertTrue(any(k.startswith(("turn", "tilt")) for k in rep.killed), rep.killed)

    def test_phone_on_its_edge_against_a_vertical_wall_is_not_at_rest(self):
        d = design(comp("base", "box", {"width": 80, "depth": 60, "height": 5}),
                   comp("back_rest", "box", {"width": 80, "depth": 5, "height": 70}, place("base", y="back")))
        r = result(d, "rests_on", object="phone", support="back_rest", also_touches=["base"])
        self.assertFalse(r.passed, r.evidence["detail"])
        self.assertIn("nudge tips it", r.evidence["detail"])
        self.assertTrue(result(d, "rests_on", object="phone", support="back_rest", also_touches=["base"],
                               tilt_deg=0).passed)


class TestNumberCoverage(unittest.TestCase):
    """Defaults never cover a stated number, and no numbers are invented (finding 11)."""

    def test_default_slot_values_do_not_cover(self):
        stable = cc.Check("s", "L1.1", "stable", {})
        self.assertEqual([v for v, _, _ in cc.number_coverage(
            "The base plate shall be 5 mm thick and the object shall not tip over.", [stable])], [5.0])
        fits = cc.Check("f", "L1.1", "fits", {"object": "pencil", "into": ["cup"]})
        self.assertEqual([v for v, _, _ in cc.number_coverage(
            "The cup wall shall be 1 mm thick and a pencil shall fit inside.", [fits])], [1.0])

    def test_a_default_tilt_still_covers_a_stated_tilt(self):
        stable = cc.Check("s", "L1.1", "stable", {})
        self.assertEqual(cc.number_coverage("It shall not tip over when tilted 5 degrees.", [stable]), [])

    def test_standin_sizes_count_only_when_the_l1_names_the_object(self):
        rest = cc.Check("r", "L1.1", "rests_on", {"object": "phone", "support": "back_rest"})
        self.assertEqual(cc.number_coverage("A phone 150 mm tall shall rest on it.", [rest]), [])
        self.assertEqual([v for v, _, _ in cc.number_coverage("The rest shall be 150 mm tall.", [rest])], [150.0])

    def test_no_invented_numbers(self):
        self.assertEqual([v for v, _, _ in cc.l1_numbers("Both legs shall be 400 mm tall.")], [400.0])
        self.assertEqual(cc.l1_numbers("A 3D printed pot of 1 kg shall stand."), [])
        self.assertEqual(cc.l1_numbers("It shall hold a pair of M3 screws twice."), [])
        self.assertEqual([v for v, u, _ in cc.l1_numbers("It is 20mm wide and 2 cm deep at 30°.")], [20, 20, 30])
        c = cc.Check("c", "L1.1", "count", {"part": "leg", "count": 3})
        self.assertEqual(cs.foreign_number("A 3D printed stool.", c), 3.0)


class TestArrangementAxis(unittest.TestCase):
    """A row / ends without an axis is judged along either horizontal axis (finding 12)."""

    def rack(self, arrangement):
        return design(comp("base", "box", {"width": 100, "depth": 150, "height": 5}),
                      comp("divider", "box", {"width": 100, "depth": 3, "height": 60}, place("base"), count=3,
                           arrangement=arrangement))

    def test_front_to_back_row_passes_without_an_axis(self):
        r = result(self.rack("row_y"), "arrangement", part="divider", pattern="row", other="base")
        self.assertTrue(r.passed, r.evidence["detail"])
        self.assertIn("row along y", r.evidence["detail"])
        self.assertFalse(result(self.rack("row_y"), "arrangement", part="divider", pattern="row", other="base",
                                axis="x").passed)

    def test_ends_without_an_axis(self):
        d = design(comp("base", "box", {"width": 100, "depth": 150, "height": 5}),
                   comp("plate", "box", {"width": 100, "depth": 3, "height": 60}, place("base"), count=2,
                        arrangement="ends_y"))
        self.assertTrue(result(d, "arrangement", part="plate", pattern="ends", other="base").passed)

    def test_rendering_names_the_axes(self):
        c = cc.Check("a", "L1.1", "arrangement", {"part": "divider", "pattern": "row"})
        self.assertIn("left to right or front to back", c.text)


# ---------------------------------------------------------------------------
# main(): exit codes and the outcome it writes (finding 13)
# ---------------------------------------------------------------------------


class StatusStub(py_trees.behaviour.Behaviour):
    """A one-leaf tree that sets the component statuses of the Design main() built."""

    def __init__(self, design, statuses):
        super().__init__("stub")
        self.design, self.statuses = design, statuses

    def update(self):
        self.design.components = [ca.Component(n, n, "box", {"width": 10, "depth": 10, "height": 10}, None)
                                  for n in self.statuses]
        for c, s in zip(self.design.components, self.statuses.values()):
            c.status = s
        return Status.SUCCESS


class TestMainExitCodes(unittest.TestCase):
    def setUp(self):
        py_trees.blackboard.Blackboard.clear()
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def main_with(self, statuses, argv=()):
        def build(design, *a, **k):
            return StatusStub(design, statuses)
        with mock.patch.object(ca, "build_tree", side_effect=build), mock.patch("builtins.print"):
            rc = ca.main(["--auto", "--out", self.tmp.name, *argv, "A plate."])
        record = json.loads(next(Path(self.tmp.name).glob("*/design.json")).read_text())
        return rc, record

    def test_all_verified(self):
        rc, record = self.main_with({"a": "verified", "b": "verified"})
        self.assertEqual((rc, record["outcome"]), (ca.EXIT_OK, "verified"))

    def test_unsatisfied_component(self):
        rc, record = self.main_with({"a": "verified", "b": "unsatisfied"})
        self.assertEqual((rc, record["outcome"]), (ca.EXIT_UNSATISFIED, "unsatisfied"))
        self.assertNotEqual(ca.EXIT_UNSATISFIED, 2)   # 2 is argparse's usage error

    def test_pending_component_is_not_a_pass(self):
        rc, record = self.main_with({"a": "verified", "b": None})
        self.assertEqual((rc, record["outcome"]), (ca.EXIT_UNSATISFIED, "unsatisfied"))

    def test_crash_is_recorded_and_propagates(self):
        with mock.patch.object(ca, "run", side_effect=RuntimeError("boom")), mock.patch("builtins.print"):
            with self.assertRaises(RuntimeError):
                ca.main(["--auto", "--out", self.tmp.name, "A plate."])
        record = json.loads(next(Path(self.tmp.name).glob("*/design.json")).read_text())
        self.assertEqual(record["outcome"], "crashed")

    def test_usage_error_is_exit_2(self):
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit) as e:
            ca.main(["--auto", "--mode", "cascade", "--out", self.tmp.name, "A plate."])
        self.assertEqual(e.exception.code, ca.EXIT_USAGE)

    def test_cascade_outcome_sets_the_exit_code(self):
        for outcome, rc_want in (("unsatisfied", ca.EXIT_UNSATISFIED), ("verified", ca.EXIT_OK)):
            def build(design, *a, **k):
                return StatusStub(design, {"a": "verified"})
            with mock.patch("cascade.build_cascade_tree", side_effect=build), \
                    mock.patch("cascade.finalize", return_value={"outcome": outcome}), \
                    mock.patch("cascade.matrix_text", return_value=""), mock.patch("builtins.print"):
                rc = ca.main(["--auto", "--mode", "cascade", "--out", self.tmp.name,
                              "--l1", json.dumps(PHONE_L1[:1]), "A plate."])
            self.assertEqual(rc, rc_want, outcome)


# ---------------------------------------------------------------------------
# Design loop: LLM tie-break and the acceptance threshold (findings 14, 15)
# ---------------------------------------------------------------------------


class PhraseLLM(CascadeLLM):
    """p_yes is high only when the described design contains `phrase`."""

    def __init__(self, phrase):
        super().__init__({})
        self.phrase = phrase

    def p_yes(self, prompt, label="p_yes", system="", images=()):
        self.calls.append((label, prompt, []))
        return 0.9 if self.phrase in prompt else 0.2


class TestTieBreak(unittest.TestCase):
    def setUp(self):
        py_trees.blackboard.Blackboard.clear()

    def run_tied(self, llm):
        d = bookend(back_y="front")
        d.cascade.checks = [chk("L1.1.c1", "relation", part="back_plate", relation="on_top_of", other="base"),
                            chk("L1.1.c2", "edge", part="back_plate", other="base", where="center", axis="y")] \
            + cs.system_checks()
        d.cascade.frozen = True
        loop = cs.design_loop(d, llm)
        tick_until_done(loop)
        self.assertEqual(loop.report.status, "converged")
        return d

    def test_the_llm_preference_wins_over_move_cost(self):
        # move cost alone would pick "back_plate.y=center"; the LLM prefers the full-cover block
        llm = PhraseLLM("covering the base's whole top surface")
        d = self.run_tied(llm)
        self.assertIn("rank_back_plate", llm.labels())
        self.assertEqual(d.component("back_plate").params["depth"], 100)

    def test_the_llm_preference_for_the_cheapest_move(self):
        llm = PhraseLLM("centred front to back")
        d = self.run_tied(llm)
        self.assertIn("rank_back_plate", llm.labels())
        self.assertEqual((d.component("back_plate").place["y"], d.component("back_plate").params["depth"]),
                         ("center", 5))


class TestAcceptEps(unittest.TestCase):
    def test_strictly_better_eps(self):
        new, old = cc.ErrorKey(1, 0.995), cc.ErrorKey(1, 1.0)
        self.assertTrue(cc.strictly_better(new, old))
        self.assertFalse(cc.strictly_better(new, old, eps=cs.ACCEPT_EPS))
        self.assertTrue(cc.strictly_better(cc.ErrorKey(0, 5.0), old, eps=cs.ACCEPT_EPS))  # fewer failures wins

    def test_design_loop_rejects_tiny_violation_gains(self):
        self.assertGreaterEqual(cs.ACCEPT_EPS, 0.01)
        d = bookend()
        d.cascade.checks = cs.system_checks()
        loop = cs.design_loop(d, ExplodingLLM())
        self.assertFalse(loop.accept_fn(cc.ErrorKey(1, 0.995), cc.ErrorKey(1, 1.0)))
        self.assertTrue(loop.accept_fn(cc.ErrorKey(1, 0.95), cc.ErrorKey(1, 1.0)))


# ---------------------------------------------------------------------------
# The real p_yes and the num_predict caps (finding 16)
# ---------------------------------------------------------------------------


def tok(token, alts):
    return {"token": token, "logprob": 0.0,
            "top_logprobs": [{"token": t, "logprob": math.log(p)} for t, p in alts]}


class TestRealPYes(unittest.TestCase):
    def agent(self, response, sent):
        def post(url, body, timeout):
            sent.append(body)
            return response
        return ca.OllamaAgent("m", "http://h:1", post=post)

    def test_logprobs_after_a_leading_token(self):
        sent = []
        resp = {"message": {"content": '{"answer":"yes"}'},
                "logprobs": [tok('{"', [('{"', 0.99)]), tok("yes", [("yes", 0.8), ("no", 0.2)])]}
        p = self.agent(resp, sent).p_yes("q")
        self.assertAlmostEqual(p, 0.8, places=6)
        self.assertTrue(sent[0]["logprobs"])
        self.assertEqual(sent[0]["options"]["num_predict"], 8)

    def test_content_fallback(self):
        for content, want in (('{"answer":"yes"}', 0.75), ('{"answer":"no"}', 0.25), ("", 0.5)):
            self.assertEqual(self.agent({"message": {"content": content}}, []).p_yes("q"), want)

    def test_tiny_yes_no_mass_is_ignored(self):
        resp = {"message": {"content": '{"answer":"no"}'},
                "logprobs": [tok("x", [("x", 0.97), ("yes", 0.01), ("no", 0.02)])]}
        self.assertEqual(self.agent(resp, []).p_yes("q"), 0.25)

    def test_ask_checks_caps_reply_length(self):
        sent = []
        replies = iter(['{"tests": ["dimension"]}',
                        '{"tests": [{"part": "base", "measure": "width", "value": 120, "op": "eq", "tol": 0}]}'])

        def post(url, body, timeout):
            sent.append(body)
            return {"message": {"content": next(replies)}}
        llm = ca.OllamaAgent("m", "http://h:1", post=post)
        d = bookend()
        req = {"id": "L1.1", "text": "The base shall be 120 mm wide.", "method": "inspection"}
        out = cs.ask_checks(llm, d, req, cs.INSPECTION_TYPES, [], 0)
        self.assertEqual([c.type for c in out], ["dimension"])
        self.assertEqual([b["options"]["num_predict"] for b in sent], [cs.TYPES_TOKENS, cs.FILL_TOKENS])


# ---------------------------------------------------------------------------
# End to end: the inner loop corrects the design and the result is rebuilt (finding 17)
# ---------------------------------------------------------------------------


class TestOuterLoopRetry(unittest.TestCase):
    def setUp(self):
        py_trees.blackboard.Blackboard.clear()

    def test_refinement_reruns_the_inner_loop_with_a_new_reference(self):
        d = phone_stand()
        st = d.cascade
        st.l1 = [{"id": "L1.1", "text": "The stand shall not tip with a 5 kg load hung 100 mm behind it.",
                  "method": "analysis"}]
        st.checks = [chk("L1.1.c1", "stable", load={"mass_g": 5000, "point": [40, 200, 50]}, tilt_deg=5.0)] \
            + cs.system_checks()
        st.frozen, st.version = True, 1
        llm = CascadeLLM({"l1types_": [{"tests": ["dimension"]}],
                          "l1fill_": [{"tests": [{"part": "base", "measure": "depth", "value": 200, "op": "ge",
                                                  "tol": 0}]}],
                          "bt_": [YES], "rank_": [YES]})
        # one inner iteration per run: the first run saturates, so the outer loop must refine and retry
        with mock.patch.object(cs, "DESIGN_ITERATIONS", 1):
            root = cs.outer_loop(d, llm)
        self.assertEqual(tick_until_done(root, 2000), Status.SUCCESS)
        self.assertEqual([r["status"] for r in st.design_reports], ["saturated", "converged"])
        self.assertNotEqual(st.design_reports[0]["reference"], st.design_reports[1]["reference"])
        self.assertEqual([r["checks_version"] for r in st.design_reports], [1, 2])
        self.assertEqual(len(st.refinements), 1)
        self.assertEqual([c.level for c in st.checks if c.l1_id == "L1.1"], [1, 2])
        self.assertEqual(cs.finalize(d)["outcome"], "verified")


class TestCascadeCorrectsEndToEnd(unittest.TestCase):
    def setUp(self):
        py_trees.blackboard.Blackboard.clear()
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    @needs_openscad
    def test_wrong_base_width_is_corrected_rebuilt_and_exported(self):
        script = phone_stand_script(params_base=[{"reasoning": "", "width": 70, "depth": 60, "height": 5}])
        script.update({
            "l1types_L1_1": [{"tests": ["dimension"]}],
            "l1fill_L1_1": [{"tests": [
                {"part": "base", "measure": "width", "value": 80, "op": "eq", "tol": 0},
                {"part": "base", "measure": "depth", "value": 60, "op": "eq", "tol": 0},
                {"part": "base", "measure": "height", "value": 5, "op": "eq", "tol": 0}]}],
            "l1types_L1_2": [{"tests": ["edge"]}],
            "l1fill_L1_2": [{"tests": [{"part": "lip", "other": "base", "where": "front"}]}],
            "l1types_L1_3": [{"tests": ["dimension"]}],
            "l1fill_L1_3": [{"tests": [{"part": "back_rest", "measure": "angle", "value": 70, "op": "eq",
                                        "tol": 0}]}],
            "bt_": [YES], "rank_": [YES],
        })
        llm = CascadeLLM(script)
        d = ca.Design(request=ca.request_with_l1("A desk phone stand", PHONE_L1), workdir=Path(self.tmp.name),
                      l1=PHONE_L1, base_request="A desk phone stand")
        # the provisional design keeps 70: AccountForNumbers must not quietly fix it first
        with mock.patch.object(ca.AccountForNumbers, "update", return_value=Status.SUCCESS):
            root = cs.build_cascade_tree(d, llm, auto_approve=True)
            self.assertEqual(ca.run(root), Status.SUCCESS)
        reports = d.cascade.design_reports
        self.assertGreaterEqual(reports[0]["iterations"], 1)
        self.assertIn("deadbeat", [h.get("note") for h in reports[0]["history"]])
        self.assertEqual(d.component("base").params["width"], 80)
        self.assertIn("80", (d.workdir / "model.scad").read_text())
        record = json.loads((d.workdir / "design.json").read_text())
        base = next(c for c in record["components"] if c["name"] == "base")
        self.assertEqual(base["params"]["width"], 80)
        rec = json.loads((d.workdir / "verification_matrix.json").read_text())
        self.assertEqual(rec["outcome"], "verified", cs.matrix_text(rec))
        self.assertTrue(d.export_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
