"""Tests for cascade.py: the ControlLoop composite, L1 -> check translation and its gates,
the inner design loop, the CEGAR outer loop, the verification matrix and the full
cascade tree. LLM calls go to scripted fakes (no network); the full-tree test needs
OpenSCAD and is skipped without it.
"""

import json
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

import py_trees
from py_trees.common import Status

import cad_agent as ca
import cad_checks as cc
import cascade as cs
from test_cad_agent import NO, YES, ScriptedLLM, needs_openscad, phone_stand_script
from test_cad_checks import comp, place


def tick_until_done(node, limit=200):
    for _ in range(limit):
        node.tick_once()
        if node.status != Status.RUNNING:
            break
    return node.status


class CascadeLLM(ScriptedLLM):
    """ScriptedLLM that accepts the cascade's extra keyword (num_predict) and logs prompts."""

    def chat(self, prompt, system="", images=(), schema=None, temperature=0.0, seed=0, label="ask",
             num_predict=None):
        return super().chat(prompt, system, images, schema, temperature, seed, label)


def make_design(*components, l1=(), request="test object"):
    tmp = tempfile.mkdtemp()
    d = ca.Design(request=request, workdir=Path(tmp), l1=list(l1), base_request=request)
    d.components = list(components)
    for c in d.components:
        c.others = [o.name for o in d.components if o is not c]
    ca.layout(d)
    d.cascade = cs.CascadeState(l1=list(l1))
    return d


def bookend(back_y="back", width=120):
    return make_design(comp("base", "box", {"width": width, "depth": 100, "height": 5}),
                       comp("back_plate", "box", {"width": 120, "depth": 5, "height": 150}, place("base", y=back_y)))


def chk(id_, type_, l1="L1.1", level=1, hard=True, **params):
    c = cc.Check(id=id_, l1_id=l1, type=type_, params=params, level=level, hard=hard)
    return c


# ---------------------------------------------------------------------------
# ControlLoop with fake propose / measure
# ---------------------------------------------------------------------------


def scalar_measure(x):
    """Error of a number against 0: hard failure while |x| >= 1, violation |x|."""
    failing = ["x"] if abs(x) >= 1 else []
    return cs.Measurement(cc.ErrorKey(len(failing), round(abs(x), 6)), failing, [f"x = {x}"] if failing else [])


class TestControlLoop(unittest.TestCase):
    def setUp(self):
        py_trees.blackboard.Blackboard.clear()
        self.ref = ["target 0"]
        self.measured = []

    def loop(self, propose, start=10.0, **kw):
        def measure(x):
            self.measured.append(x)
            return scalar_measure(x)
        kw.setdefault("max_iterations", 20)
        return cs.ControlLoop("test", "test", reference=lambda: self.ref, initial=lambda: start,
                              propose=propose, measure=measure, state_key=lambda x: str(x), **kw)

    def test_converges_and_reports_on_the_blackboard(self):
        loop = self.loop(lambda x, ctx: x / 2)
        self.assertEqual(tick_until_done(loop), Status.SUCCESS)
        self.assertEqual(loop.report.status, "converged")
        self.assertEqual(loop.report.iterations, 4)   # 10 -> 5 -> 2.5 -> 1.25 -> 0.625
        self.assertEqual(loop.report.best_state, 0.625)
        self.assertIs(py_trees.blackboard.Blackboard.get("/loop/test/report"), loop.report)
        self.assertEqual(py_trees.blackboard.Blackboard.get("/loop/test/status"), "converged")
        self.assertEqual(loop.reports["test"]["status"], "converged")

    def test_one_iteration_per_tick(self):
        loop = self.loop(lambda x, ctx: x - 3)
        loop.tick_once()
        self.assertEqual(loop.status, Status.RUNNING)
        self.assertEqual(loop.iterations, 1)

    def test_acceptance_is_monotone(self):
        steps = iter([+5, -2, +7, -3, -1, +4, -4, -1])   # worse proposals interleaved with better ones
        loop = self.loop(lambda x, ctx: x + next(steps), patience=10, max_iterations=8)
        tick_until_done(loop)
        accepted = [h["error"]["violation"] for h in loop.report.history if h["accepted"]]
        self.assertTrue(all(b < a for a, b in zip(accepted, accepted[1:])), accepted)
        self.assertEqual(loop.report.best_state, 10 - 2 - 3 - 1 - 4)
        self.assertEqual(loop.report.status, "converged")

    def test_stagnates_when_nothing_new_is_proposed(self):
        loop = self.loop(lambda x, ctx: None)
        self.assertEqual(tick_until_done(loop), Status.FAILURE)
        self.assertEqual(loop.report.status, "stagnated")
        self.assertEqual(loop.report.best_state, 10.0)

    def test_stagnates_after_patience_rejections(self):
        worse = iter(range(11, 100))
        loop = self.loop(lambda x, ctx: float(next(worse)), patience=3)
        self.assertEqual(tick_until_done(loop), Status.FAILURE)
        self.assertEqual(loop.report.status, "stagnated")
        self.assertEqual(loop.report.iterations, 3)
        self.assertEqual(loop.report.best_state, 10.0)   # never worse than the start

    def test_saturates_and_keeps_the_best(self):
        loop = self.loop(lambda x, ctx: x - 1, max_iterations=3)
        self.assertEqual(tick_until_done(loop), Status.FAILURE)
        self.assertEqual(loop.report.status, "saturated")
        self.assertEqual(loop.report.best_state, 7.0)
        self.assertEqual(loop.report.residual, ["x = 7.0"])

    def test_uncontrollable_is_reported_before_any_attempt(self):
        calls = []
        loop = self.loop(lambda x, ctx: calls.append(x) or x - 1, diagnose=lambda x, m: list(m.failing))
        self.assertEqual(tick_until_done(loop), Status.FAILURE)
        self.assertEqual(loop.report.status, "uncontrollable")
        self.assertEqual(loop.report.uncontrollable, ["x"])
        self.assertEqual(calls, [])
        self.assertEqual(loop.report.iterations, 0)

    def test_memory_is_kept_for_the_same_reference_and_reset_when_it_changes(self):
        loop = self.loop(lambda x, ctx: 50.0, patience=1)
        tick_until_done(loop)
        self.assertIn("50.0", loop.rejected)
        self.measured.clear()
        loop.stop(Status.INVALID)
        tick_until_done(loop)          # same reference: 50 is known bad, not measured again
        self.assertEqual(self.measured, [10.0])
        self.assertEqual(loop.history[-1]["note"], "already tried")
        self.ref = ["target 0, refined"]
        self.measured.clear()
        loop.stop(Status.INVALID)
        tick_until_done(loop)          # new reference: memory reset (anti-windup), 50 measured again
        self.assertEqual(self.measured, [10.0, 50.0])
        self.assertEqual(loop.history[0]["note"], "initial")

    def test_prior_errors_reach_the_proposer(self):
        seen = []

        def propose(x, ctx):
            seen.append(list(ctx.best.residual))
            return x - 6
        tick_until_done(self.loop(propose))
        self.assertEqual(seen[0], ["x = 10.0"])
        self.assertEqual(seen[1], ["x = 4.0"])


# ---------------------------------------------------------------------------
# L1 -> checks
# ---------------------------------------------------------------------------


def width_fill(value, tol=0):
    return {"tests": [{"part": "base", "measure": "width", "value": value, "op": "eq", "tol": tol}]}


class TestTranslation(unittest.TestCase):
    def setUp(self):
        py_trees.blackboard.Blackboard.clear()
        self.req = {"id": "L1.1", "text": "The base shall be 120 mm wide.", "method": "inspection"}
        self.d = bookend()
        self.d.l1 = [self.req]
        self.d.cascade = cs.CascadeState(l1=[self.req])

    def run_translation(self, llm):
        loop = cs.translate_loop(self.d, llm, self.req)
        tick_until_done(loop)
        return loop

    def test_template_filled_gated_and_accepted(self):
        llm = CascadeLLM({"l1types_": [{"tests": ["dimension"]}], "l1fill_": [width_fill(120)], "bt_": [YES]})
        loop = self.run_translation(llm)
        self.assertEqual(loop.report.status, "converged")
        [c] = self.d.cascade.drafts["L1.1"]
        self.assertEqual((c.type, c.params["part"], c.params["value"]), ("dimension", "base", 120))
        self.assertIsNone(c.params["tol"])          # the 0 sentinel means "default"
        self.assertEqual(c.text, "The base's width (left to right) is 120 mm (within 1.2 mm).")
        # the component names were offered as an enum
        fill_prompt = next(p for l, p, _ in llm.calls if l.startswith("l1fill_"))
        self.assertIn("back_plate", fill_prompt)
        self.assertTrue(self.d.cascade.gates[c.id]["non_vacuity"]["ok"])

    def test_number_coverage_retries_with_the_gate_message(self):
        llm = CascadeLLM({"l1types_": [{"tests": ["dimension"]}], "l1fill_": [width_fill(100), width_fill(120)],
                          "bt_": [YES]})
        loop = self.run_translation(llm)
        self.assertEqual(loop.report.status, "converged")
        prompts = [p for l, p, _ in llm.calls if l.startswith("l1fill_")]
        self.assertEqual(len(prompts), 2)
        self.assertIn('the number "120 mm" in the requirement is not used by any test', prompts[1])
        self.assertEqual([c.params["value"] for c in self.d.cascade.drafts["L1.1"]], [120])
        # the 100 mm draft is rejected outright: the requirement never states 100
        rejected = self.d.cascade.translation["L1.1"]["rejected"]
        self.assertIn("a number the requirement does not give", rejected[0]["problems"][0])

    def test_vacuous_check_is_rejected_by_the_mutant_gate(self):
        # A tolerance of 1000 mm passes on every mutant: it cannot catch a wrong design.
        llm = CascadeLLM({"l1types_": [{"tests": ["dimension"]}], "l1fill_": [width_fill(120, tol=1000)],
                          "bt_": [YES]})
        loop = self.run_translation(llm)
        self.assertNotEqual(loop.report.status, "converged")
        self.assertEqual(self.d.cascade.drafts["L1.1"], [])
        rejected = self.d.cascade.translation["L1.1"]["rejected"]
        self.assertTrue(any("would not catch a wrong design" in p for r in rejected for p in r["problems"]))
        self.assertFalse(any(l.startswith("bt_") for l in llm.labels()))   # the LLM was not asked about it

    def test_backtranslation_no_rejects_the_check(self):
        llm = CascadeLLM({"l1types_": [{"tests": ["dimension"]}], "l1fill_": [width_fill(120)], "bt_": [NO]})
        loop = self.run_translation(llm)
        self.assertEqual(loop.report.status, "stagnated")
        self.assertEqual(self.d.cascade.drafts["L1.1"], [])
        self.assertEqual(llm.labels().count("l1types_L1_1"), cs.TRANSLATE_ITERATIONS)
        self.assertEqual(llm.labels().count("bt_L1_1"), 1)   # cached: the same check is not asked twice

    def test_invalid_template_is_reported(self):
        llm = CascadeLLM({"l1types_": [{"tests": ["dimension"]}],
                          "l1fill_": [{"tests": [{"part": "back_plate", "measure": "diameter", "value": 120,
                                                  "op": "eq", "tol": 0}]}, width_fill(120)], "bt_": [YES]})
        loop = self.run_translation(llm)
        self.assertEqual(loop.report.status, "converged")
        second = [p for l, p, _ in llm.calls if l.startswith("l1fill_")][1]
        self.assertIn("would not catch a wrong design", second)  # diameter of a box fails everywhere

    def test_sentinels_map_to_defaults(self):
        p = cs.params_from_template("stable", {"load_mass_g": 0, "load_part": "none", "tilt_deg": 0})
        self.assertEqual((p["load"], p["tilt_deg"]), (None, cc.STABLE_TILT))
        p = cs.params_from_template("stable", {"load_mass_g": 500, "load_part": "seat", "tilt_deg": 0})
        self.assertEqual(p["load"], {"mass_g": 500.0, "part": "seat", "face": "top"})
        p = cs.params_from_template("rests_on", {"object": "phone", "size": [], "support": "rest", "mode": "lean",
                                                 "also_touches": [], "orientation": "any", "mu": 0})
        self.assertEqual((p["size"], p["orientation"], p["also_touches"], p["mu"]), (None, None, None, cc.DEFAULT_MU))
        self.assertEqual(cs.params_from_template("count", {"part": "whole_object", "shape": "any", "count": 2.0,
                                                           "op": "eq"}), {"part": None, "shape": None, "count": 2,
                                                                          "op": "eq"})

    def test_offered_types_follow_the_method(self):
        self.assertNotIn("rests_on", cs.offered_types("inspection"))
        self.assertEqual(cs.offered_types("demonstration")[0], "fits")
        self.assertEqual(set(cs.offered_types(None)), set(cs.TYPE_DOCS))


class TestPythonGates(unittest.TestCase):
    """The Python-side gates added after the first smoke runs (each one caught a real translation)."""

    def setUp(self):
        self.d = bookend()

    def gate(self, text, *checks, method="inspection"):
        req = {"id": "L1.1", "text": text, "method": method}
        llm = CascadeLLM({"bt_": [YES]})
        return cs.gate_checks(llm, self.d, req, list(checks), {})[0]

    def test_whole_object_count_needs_a_reason(self):
        c = chk("a", "count", count=2, op="eq")
        self.assertIn("counts every part", self.gate("There shall be exactly two upright plates.", c)["a"][0])
        self.assertEqual(self.gate("The bookend shall be made of exactly two parts.", c)["a"], [])

    def test_side_relation_for_an_edge_requirement_is_rejected(self):
        c = chk("a", "relation", part="back_plate", relation="behind", other="base")
        self.assertIn("use an edge test", self.gate("The plate shall stand along the back edge of the base.", c)["a"][0])

    def test_contradicting_edges_are_rejected(self):
        a = chk("a", "edge", part="back_plate", other="base", where="back")
        b = chk("b", "edge", part="back_plate", other="base", where="center", axis="y")
        c = chk("c", "edge", part="back_plate", other="base", where="center", axis="x")
        problems = self.gate("The plate shall be along the back edge, centred left to right.", a, b, c)
        self.assertEqual(problems["a"], [])
        self.assertIn("contradicts", problems["b"][0])
        self.assertEqual(problems["c"], [])   # back (y) and centred left-right (x) can both hold

    def test_standin_must_come_from_the_requirement(self):
        letter = "A letter 5 mm thick shall fit upright between two neighbouring plates."
        book = chk("a", "fits", object="book", into=["back_plate"], between=True)
        self.assertIn("does not mention a book", cs.standin_problem(letter, book))
        sized = chk("b", "fits", object="box", size=[5, 100, 200], into=["back_plate"], between=True)
        self.assertIsNone(cs.standin_problem(letter, sized))
        wrong = chk("c", "fits", object="box", size=[30, 100, 200], into=["back_plate"], between=True)
        self.assertIn("does not state", cs.standin_problem(letter, wrong))
        self.assertIsNone(cs.standin_problem("A phone shall rest against the plate.",
                                             chk("d", "rests_on", object="phone", support="back_plate")))

    def test_single_states_one_and_open_ends_is_not_an_arrangement(self):
        self.assertIsNone(cs.foreign_number("The ruler shall be a single flat strip.", chk("a", "count", count=1)))
        req = {"id": "x", "text": "The bangle shall be a single hollow tube open at both ends.", "method": "inspection"}
        self.assertEqual(cs.cue_coverage(req, []), [])

    def test_count_of_one_role_is_rejected_and_the_group_is_offered(self):
        from test_cad_checks import comp, design, place
        self.d = design(comp("base", "box", {"width": 150, "depth": 60, "height": 6}),
                        comp("front_panel", "box", {"width": 150, "depth": 4, "height": 90}, place("base", y="front")),
                        comp("back_panel", "box", {"width": 150, "depth": 4, "height": 90}, place("base", y="back")))
        one_role = chk("a", "count", part="back_panel", count=2, op="eq")
        self.assertIn('use part "panel"', cs.role_count_problem(self.d, one_role))
        self.assertIsNone(cs.role_count_problem(self.d, chk("b", "count", part="panel", count=2, op="eq")))
        self.assertEqual(cs.group_names(self.d), ["panel"])
        self.assertIn("panel: front_panel and back_panel together", cs.parts_text(self.d))

    def test_cue_coverage(self):
        req = {"id": "L1.1", "text": "One leg shall be under each corner and the top centred.", "method": "inspection"}
        missing = [q for q, _ in cs.cue_coverage(req, [])]
        self.assertEqual(missing, ["corner", "centred"])
        corner = chk("a", "arrangement", part="leg", pattern="corners")
        self.assertEqual([q for q, _ in cs.cue_coverage(req, [corner])], ["centred"])
        # a cue the method cannot check (stability by inspection) is not demanded
        self.assertEqual(cs.cue_coverage({"id": "x", "text": "It shall not tip.", "method": "inspection"}, []), [])
        self.assertEqual(len(cs.cue_coverage({"id": "x", "text": "It shall not tip.", "method": "analysis"}, [])), 1)


class TestCheckAdditions(unittest.TestCase):
    """cad_checks changes made for the cascade: new mutants, upright panels, fits between copies."""

    def rack(self):
        return make_design(comp("base", "box", {"width": 180, "depth": 70, "height": 6}),
                           comp("divider", "box", {"width": 180, "depth": 4, "height": 60}, place("base"),
                                count=3, arrangement="row_y"))

    def test_row_and_upright_checks_now_kill_mutants(self):
        d = self.rack()
        checks = [chk("row", "arrangement", part="divider", pattern="row", other="base", axis="y"),
                  chk("up", "shape", part="divider", shape="box", orient="upright")]
        reports = {r.check_id: r for r in cc.non_vacuity(d, checks)}
        self.assertIn("rearrange:divider", reports["row"].killed)
        self.assertIn("rotate:divider", reports["up"].killed)
        self.assertTrue(all(r.ok for r in reports.values()))

    def test_angle_check_kills_the_tilt_mutant(self):
        d = phone_stand()
        rep = cc.non_vacuity(d, [chk("a", "dimension", part="back_rest", measure="angle", value=70)])[0]
        self.assertIn("tilt:back_rest", rep.killed)
        self.assertTrue(rep.ok)

    def test_upright_panel_means_vertical(self):
        for angle, ok in ((90, True), (65, False)):
            d = phone_stand(angle)
            self.assertEqual(cc.run_check(d, chk("u", "shape", part="back_rest", shape="panel",
                                                 orient="upright")).passed, ok)

    def test_fits_between_two_copies_of_one_part(self):
        d = self.rack()
        letter = chk("f", "fits", object="box", size=[5, 220, 110], into=["divider", "divider"], between=True,
                     orientation="edge")
        r = cc.run_check(d, letter)
        self.assertTrue(r.passed, r.evidence)
        self.assertIn("gap 29 mm along y", r.evidence["detail"])
        self.assertEqual(cc.number_coverage("A letter 5 mm thick shall fit between two dividers.", [letter]), [])


class TestFreeze(unittest.TestCase):
    def test_levels_system_checks_and_checks_json(self):
        d = bookend()
        st = d.cascade
        st.l1 = [{"id": "L1.1", "text": "a"}, {"id": "L1.2", "text": "b"}]
        st.drafts = {"L1.1": [chk("L1.1.c1", "dimension", part="base", measure="width", value=120)],
                     "L1.2": [chk("L1.2.c2", "rests_on", "L1.2", object="book", support="back_plate"),
                              chk("L1.2.c3", "dimension", "L1.2", part="back_plate", measure="height", value=150)]}
        self.assertEqual(cs.FreezeChecks(d).update(), Status.SUCCESS)
        levels = {c.id: c.level for c in st.checks}
        # every translated check verifies its L1 (level 1); level 2 is only for the outer loop's refinements
        self.assertEqual(levels, {"L1.1.c1": 1, "L1.2.c2": 1, "L1.2.c3": 1, "SYS.connected": 1, "SYS.no_overlap": 1})
        self.assertTrue(st.frozen)
        record = json.loads((d.workdir / "checks.json").read_text())
        self.assertTrue(record["frozen"])
        self.assertEqual([c["id"] for c in record["checks"]][-2:], ["SYS.connected", "SYS.no_overlap"])
        self.assertTrue(record["checks"][-1]["hard"])
        # a second freeze is a no-op: frozen checks never change behind the loop's back
        st.drafts["L1.1"] = []
        cs.FreezeChecks(d).update()
        self.assertEqual(len(st.checks), 5)


# ---------------------------------------------------------------------------
# Inner loop
# ---------------------------------------------------------------------------


class ExplodingLLM:
    """Any LLM use fails the test: these corrections must be Python-only."""
    calls = 0

    def __getattr__(self, name):
        raise AssertionError(f"unexpected LLM use: {name}")


class TestDesignLoop(unittest.TestCase):
    def setUp(self):
        py_trees.blackboard.Blackboard.clear()

    def run_loop(self, d, checks, llm=None):
        d.cascade.checks = checks + cs.system_checks()
        d.cascade.frozen = True
        loop = cs.design_loop(d, llm if llm is not None else ExplodingLLM())
        tick_until_done(loop)
        return loop

    def test_deadbeat_fixes_a_dimension_in_one_step(self):
        d = bookend(width=100)
        loop = self.run_loop(d, [chk("L1.1.c1", "dimension", part="base", measure="width", value=120)])
        self.assertEqual(loop.report.status, "converged")
        self.assertEqual(loop.report.iterations, 1)
        self.assertEqual(d.component("base").params["width"], 120)   # committed to the real design
        self.assertEqual(loop.report.history[-1]["note"], "deadbeat")

    def test_count_is_set_directly_with_a_matching_arrangement(self):
        d = make_design(comp("seat", "box", {"width": 300, "depth": 300, "height": 20}),
                        comp("leg", "box", {"width": 30, "depth": 30, "height": 400}, place("seat", "bottom"),
                             count=3, arrangement="triangle_xy"))
        loop = self.run_loop(d, [chk("L1.1.c1", "count", part="leg", count=4, op="eq")])
        self.assertEqual(loop.report.status, "converged")
        self.assertEqual((d.component("leg").count, d.component("leg").arrangement), (4, "corners_xy"))

    def test_count_fix_picks_the_arrangement_by_error(self):
        # Two plates "front and back": count 1 -> 2 must lay the copies out front-to-back.
        d = make_design(comp("base", "box", {"width": 150, "depth": 60, "height": 6}),
                        comp("plate", "box", {"width": 150, "depth": 4, "height": 90}, place("base", y="front")))
        checks = [chk("L1.1.c1", "count", part="plate", count=2, op="eq"),
                  chk("L1.1.c2", "arrangement", part="plate", pattern="ends", other="base", axis="y")]
        loop = self.run_loop(d, checks, CascadeLLM({"rank_": [YES]}))
        self.assertEqual(loop.report.status, "converged")
        self.assertEqual((d.component("plate").count, d.component("plate").arrangement), (2, "ends_y"))

    def test_structural_error_is_localised_and_searched(self):
        d = bookend(back_y="front")
        checks = [chk("L1.1.c1", "edge", part="back_plate", other="base", where="back")]
        llm = CascadeLLM({"rank_": [YES]})   # several moves fix it equally well: the LLM breaks the tie
        loop = self.run_loop(d, checks, llm)
        self.assertEqual(loop.report.status, "converged")
        self.assertEqual(d.component("back_plate").place["y"], "back")
        accepted = [h["error"] for h in loop.report.history if h["accepted"]]
        keys = [cc.ErrorKey(**e) for e in accepted]
        self.assertTrue(all(cc.strictly_better(b, a) for a, b in zip(keys, keys[1:])))

    def test_tied_candidates_are_ranked_by_the_llm(self):
        d = bookend(back_y="front")
        llm = CascadeLLM({"rank_": [YES]})
        checks = [chk("L1.1.c1", "relation", part="back_plate", relation="on_top_of", other="base"),
                  chk("L1.1.c2", "edge", part="back_plate", other="base", where="center", axis="y")]
        loop = self.run_loop(d, checks, llm)
        self.assertEqual(loop.report.status, "converged")
        self.assertEqual(d.component("back_plate").place["y"], "center")

    def test_uncontrollable_check_is_reported_immediately(self):
        d = bookend()
        # The whole object having 5 parts: no knob or direct fix changes the number of components.
        loop = self.run_loop(d, [chk("L1.1.c1", "count", count=5, op="eq")])
        self.assertEqual(loop.report.status, "uncontrollable")
        self.assertEqual(loop.report.uncontrollable, ["L1.1.c1"])
        self.assertEqual(loop.report.iterations, 0)

    def test_llm_gets_the_failing_evidence_when_python_has_no_move(self):
        d = make_design(comp("ball", "box", {"width": 60, "depth": 60, "height": 60}))
        llm = CascadeLLM({"params_ball": [{"reasoning": "", "diameter": 60}], "rank_": [YES]})
        loop = self.run_loop(d, [chk("L1.1.c1", "shape", part="ball", shape="sphere")], llm)
        self.assertEqual(loop.report.status, "converged")
        self.assertEqual((d.component("ball").shape, d.component("ball").params), ("sphere", {"diameter": 60}))
        prompt = next(p for l, p, _ in llm.calls if l == "params_ball")
        self.assertIn("It must be a ball", prompt)


# ---------------------------------------------------------------------------
# Outer loop and the matrix
# ---------------------------------------------------------------------------


def phone_stand(angle=70):
    return make_design(
        comp("base", "box", {"width": 80, "depth": 100, "height": 5}),
        comp("back_rest", "panel", {"width": 80, "height": 120, "thickness": 5, "angle": angle, "lean": "back"},
             place("base", y="back")),
        comp("lip", "box", {"width": 80, "depth": 5, "height": 10}, place("base", y="front")))


class TestOuterLoop(unittest.TestCase):
    def setUp(self):
        py_trees.blackboard.Blackboard.clear()

    def test_failing_sub_checks_are_dropped_when_the_l1_passes(self):
        d = phone_stand()
        st = d.cascade
        st.l1 = [{"id": "L1.1", "text": "The stand shall not tip over.", "method": "analysis"}]
        st.checks = [chk("L1.1.c1", "stable", tilt_deg=5.0),
                     chk("L1.1.c2", "dimension", level=2, part="base", measure="width", value=200)] + cs.system_checks()
        st.frozen, st.version = True, 1
        self.assertEqual(cs.RefineChecks(d, ExplodingLLM()).update(), Status.FAILURE)
        self.assertEqual([c.id for c in st.checks], ["L1.1.c1", "SYS.connected", "SYS.no_overlap"])
        self.assertEqual(st.dropped[0]["check"]["id"], "L1.1.c2")
        self.assertEqual((st.version, st.outer_iterations), (2, 1))
        self.assertEqual(cs.RefineChecks(d, ExplodingLLM()).update(), Status.SUCCESS)  # nothing left to change

    def test_failing_l1_with_passing_sub_checks_gets_new_sub_checks(self):
        d = phone_stand()
        st = d.cascade
        st.l1 = [{"id": "L1.1", "text": "The stand shall not tip with a 5 kg load hung 100 mm behind it.",
                  "method": "analysis"}]
        st.checks = [chk("L1.1.c1", "stable", load={"mass_g": 5000, "point": [40, 200, 50]}, tilt_deg=5.0)] \
            + cs.system_checks()
        st.frozen, st.version = True, 1
        self.assertFalse(cc.run_checks(d, st.checks[:1])[0].passed)
        llm = CascadeLLM({"l1types_": [{"tests": ["dimension"]}],
                          "l1fill_": [{"tests": [{"part": "base", "measure": "depth", "value": 200, "op": "ge",
                                                  "tol": 0}]}], "bt_": [YES]})
        self.assertEqual(cs.RefineChecks(d, llm).update(), Status.FAILURE)
        added = [c for c in st.checks if c.level == 2]
        self.assertEqual(len(added), 1)
        self.assertEqual((added[0].params["measure"], added[0].params["value"]), ("depth", 200))
        prompt = next(p for l, p, _ in llm.calls if l.startswith("l1types_"))
        self.assertIn("FAILS", prompt)
        self.assertEqual(st.refinements[0]["changes"][0], f"added {added[0].id} for L1.1")

    def test_outer_iterations_are_capped(self):
        d = phone_stand()
        d.cascade.outer_iterations = cs.MAX_OUTER
        self.assertEqual(cs.RefineChecks(d, ExplodingLLM()).update(), Status.SUCCESS)


class TestMatrix(unittest.TestCase):
    def test_rows_failing_first_unverified_and_files(self):
        d = bookend()
        st = d.cascade
        st.l1 = [{"id": "L1.1", "text": "The base shall be 120 mm wide.", "method": "inspection"},
                 {"id": "L1.2", "text": "The plate shall be 200 mm tall.", "method": "inspection"},
                 {"id": "L1.3", "text": "The plate shall be 5 mm thick and 120 mm wide.", "method": "inspection"},
                 {"id": "L1.4", "text": "It shall look nice.", "method": "human"}]
        st.checks = [chk("L1.1.c1", "dimension", part="base", measure="width", value=120),
                     chk("L1.2.c2", "dimension", "L1.2", part="back_plate", measure="height", value=200),
                     chk("L1.3.c3", "dimension", "L1.3", part="back_plate", measure="depth", value=5)] \
            + cs.system_checks()
        st.translation = {"L1.3": {"uncovered": [{"value": 120, "unit": "mm", "text": "120 mm"}]}}
        rec = cs.finalize(d)
        self.assertEqual([r["l1_id"] for r in rec["rows"]], ["L1.2", "L1.4", "L1.3", "L1.1"])
        self.assertEqual([r["status"] for r in rec["rows"]], ["fail", "unverified", "unverified", "pass"])
        self.assertEqual(rec["outcome"], "unsatisfied")
        self.assertEqual(d.component("back_plate").status, "unsatisfied")
        # unverified L1s belong to no single part, so every part carries them: design.json can
        # never say all_verified next to an unsatisfied outcome
        base = d.component("base")
        self.assertEqual(base.status, "unsatisfied")
        self.assertTrue(any(r.startswith("L1 L1.4 unverified") for r in base.residual), base.residual)
        self.assertFalse(ca.verification_summary(d)["all_verified"])
        record = json.loads(ca.write_design_json(d, rec["outcome"]).read_text())
        self.assertFalse(record["verification"]["all_verified"])
        self.assertEqual(sorted(record["verification"]["l1_not_passed"]), ["L1.2", "L1.3", "L1.4"])
        md = (d.workdir / "verification_matrix.md").read_text()
        self.assertIn("| FAIL | L1.2 |", md)
        self.assertIn("120 mm", md)
        self.assertEqual(json.loads((d.workdir / "verification_matrix.json").read_text())["outcome"], "unsatisfied")

    def test_all_pass_is_verified(self):
        d = bookend()
        d.cascade.l1 = [{"id": "L1.1", "text": "The base shall be 120 mm wide.", "method": "inspection"}]
        d.cascade.checks = [chk("L1.1.c1", "dimension", part="base", measure="width", value=120)] + cs.system_checks()
        self.assertEqual(cs.finalize(d)["outcome"], "verified")


# ---------------------------------------------------------------------------
# The whole cascade tree and the CLI
# ---------------------------------------------------------------------------

PHONE_L1 = [
    {"id": "L1.1", "text": "The base shall be 80 x 60 x 5 mm.", "method": "inspection"},
    {"id": "L1.2", "text": "The lip shall be along the front edge of the base.", "method": "inspection"},
    {"id": "L1.3", "text": "The back rest shall lean back at 70 degrees.", "method": "inspection"},
]


class TestCascadeTree(unittest.TestCase):
    def setUp(self):
        py_trees.blackboard.Blackboard.clear()
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    @needs_openscad
    def test_phone_stand_end_to_end(self):
        script = phone_stand_script()
        script.update({
            "l1types_L1_1": [{"tests": ["dimension"]}],
            "l1fill_L1_1": [{"tests": [
                {"part": "base", "measure": "width", "value": 80, "op": "eq", "tol": 0},
                {"part": "base", "measure": "depth", "value": 60, "op": "eq", "tol": 0},
                {"part": "base", "measure": "height", "value": 5, "op": "eq", "tol": 0}]}],
            "l1types_L1_2": [{"tests": ["edge"]}],
            "l1fill_L1_2": [{"tests": [{"part": "lip", "other": "base", "where": "front"}]}],
            "l1types_L1_3": [{"tests": ["dimension"]}],
            # deliberately wrong at first draft: 60 degrees is not what the L1 says -> coverage retry
            "l1fill_L1_3": [{"tests": [{"part": "back_rest", "measure": "angle", "value": 60, "op": "eq", "tol": 0}]},
                            {"tests": [{"part": "back_rest", "measure": "angle", "value": 70, "op": "eq", "tol": 0}]}],
            "bt_": [YES], "rank_": [YES],
        })
        llm = CascadeLLM(script)
        d = ca.Design(request=ca.request_with_l1("A desk phone stand", PHONE_L1), workdir=Path(self.tmp.name),
                      l1=PHONE_L1, base_request="A desk phone stand")
        root = cs.build_cascade_tree(d, llm, auto_approve=True)
        self.assertEqual(ca.run(root), Status.SUCCESS)
        self.assertTrue(d.export_path.exists())
        record = json.loads((d.workdir / "checks.json").read_text())
        self.assertTrue(record["frozen"])
        ids = [c["l1_id"] for c in record["checks"]]
        self.assertEqual(sorted(set(ids)), ["L1.1", "L1.2", "L1.3", "SYS"])
        rec = json.loads((d.workdir / "verification_matrix.json").read_text())
        self.assertEqual(rec["outcome"], "verified", cs.matrix_text(rec))
        self.assertEqual(rec["loops"]["design"]["status"], "converged")
        self.assertTrue((d.workdir / "verification_matrix.md").exists())
        # translation happened after the components existed, and before the design loop
        labels = llm.labels()
        self.assertLess(labels.index("components"), labels.index("l1types_L1_1"))
        self.assertNotIn("verify_base", labels)   # the cascade replaces back-translation verification

    def test_review_shows_the_matrix(self):
        d = bookend()
        d.cascade.l1 = [{"id": "L1.1", "text": "The base shall be 120 mm wide.", "method": "inspection"}]
        d.cascade.checks = [chk("L1.1.c1", "dimension", part="base", measure="width", value=130)] + cs.system_checks()
        cs.finalize(d)
        review = cs.CascadeReview(d, None, input_fn=lambda _: "")
        with mock.patch("builtins.print") as p:
            self.assertEqual(review.update(), Status.SUCCESS)
        printed = "\n".join(str(c.args[0]) for c in p.call_args_list if c.args)
        self.assertIn("FAIL", printed)
        self.assertIn("L1.1", printed)

    def test_cli_needs_l1_for_cascade(self):
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            ca.main(["--auto", "--mode", "cascade", "--out", self.tmp.name, "A plate."])

    def test_cli_builds_the_cascade_tree(self):
        with mock.patch.object(ca, "run", side_effect=KeyboardInterrupt), mock.patch("builtins.print"), \
                mock.patch("cascade.build_cascade_tree", wraps=cs.build_cascade_tree) as build:
            rc = ca.main(["--auto", "--mode", "cascade", "--out", self.tmp.name,
                          "--l1", json.dumps(PHONE_L1[:1]), "A plate."])
        self.assertEqual(rc, 130)
        build.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
