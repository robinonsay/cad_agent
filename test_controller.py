"""Tests for the closed-loop controller (controller.py; owner decision D1, migration delta R01). No Ollama: the
controller's question (label assy_control) is scripted; the regression and train texts are data.

What is checked: the typed error vector (which requirement, where, by how much, which direction), the action menu, the
loop (a kept correction, stop, an infeasible action, an undone action, the budget), the stage checkpoints, the trace
(controller_trace.json) with its authority audit, the stub controller (first offered option, no corrective step, no LLM
call), the converted sensors (text_coverage, closure_evidence), and regression invariance: when the controller exposes
the connector the text names, the package is byte-identical to the pre-R01 path where it was exposed before the
arrangement.
"""

import hashlib
import json
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

import assembly as A
import cad_agent as ca
import cad_checks as cc
import controller as C
import layout as lay
import parts as pt
from test_assembly import (BOTH, FakeLLM, g02_script, gen_run, gen_texts, l1_text, l1_with, new_design, run_offline,
                           run_stages, script_for, test_rules, texts)

REPO = Path(__file__).parent


def closed_usb(rid: str) -> dict:
    """The scripted answers with the Contents vote the 9B really gave in iterations 002-004 (the Pico's USB not exposed)."""
    s = script_for(rid)
    s["assy_contents"] = [dict(s["assy_contents"][0], rpi_pico2={"quantity": 1, "exposed": "no"})]
    return s


def staged(rid: str, root: Path, script: dict, rules: Path):
    """A regression design staged to DeriveFeatures (the initial proposal), with its LLM."""
    d = new_design(rid, root / rid, rules_path=rules)
    llm = FakeLLM(script)
    status, child = run_stages(d, llm, "DeriveFeatures")
    assert status == ca.Status.SUCCESS, (type(child).__name__, d.assy.notes[-3:])
    return d, llm


def graph_hash(pkg: Path) -> str:
    return hashlib.sha1(json.dumps(json.loads((pkg / "feature_graph.json").read_text()), sort_keys=True).encode()
                        ).hexdigest()


class Case(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rules = test_rules(cls.root, fn=24)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class TestErrorVector(Case):
    def test_named_plug_on_a_closed_connector(self):
        d, _ = staged("E1-01", self.root / "ev", closed_usb("E1-01"), self.rules)
        st = d.assy
        plan, results, links = C.plant(st)
        terms = C.error_vector(st, results, links)
        self.assertEqual([t.check for t in terms], ["text_coverage"])
        t = terms[0]
        naming = l1_with("E1-01", "micro-USB cable")
        self.assertIn(naming, t.requirement)                          # which requirement
        self.assertIn("module_1.usb", t.where)                        # where
        self.assertIn(l1_text("E1-01", naming)[:40], t.where)          # the quote
        self.assertEqual((t.deficit, t.unit), (1.0, "count"))          # by how much
        self.assertTrue(t.controllable and t.actionable and t.hard)
        self.assertIn("opening", t.direction)                          # which direction
        key = C.error_key(results)
        self.assertEqual((key.hard_failures, key.violation), (1, 1.0))
        self.assertEqual(st.coverage[0]["resolved"], A.COVERAGE_OPEN)  # the sensor stage recorded it, exposed nothing
        self.assertFalse(next(c for c in st.contents if c["part"] == "rpi_pico2")["exposed"])

    def test_ranking_and_millimetre_deficit(self):
        r_ok = cc.CheckResult("a", "rules", "clear_of", True, 0.5, "mm", {}, {"detail": "ok"})
        r_mm = cc.CheckResult("gap", "rules", "clear_of", False, -0.25, "mm", {}, {"detail": "min gap 0.05"})
        r_conf = cc.CheckResult("grid", "rules", "grid_conformance", False, -3.0, "mm", {},
                                {"detail": "x", "conflict": "pin pattern"})
        r_cov = cc.CheckResult("text_coverage", "rules", "coverage", False, -1.0, "count", {},
                               {"detail": "d", "uncovered": []})
        st = A.AssemblyState(rules=pt.load_rules(REPO / "design_rules.json"), catalog=pt.Catalog.load(BOTH))
        terms = C.error_vector(st, [r_ok, r_mm, r_conf, r_cov], {})
        self.assertEqual([t.check for t in terms], ["text_coverage", "gap", "grid"])   # actionable, controllable, conflict
        self.assertEqual(terms[1].deficit, 0.25)
        self.assertIn("increase the gap", terms[1].direction)
        self.assertFalse(terms[2].controllable)
        self.assertIn("typed conflict", terms[2].direction)
        self.assertEqual(C.error_key([r_ok, r_mm, r_conf, r_cov]), cc.ErrorKey(2, 1.25))  # the conflict is not counted


class TestAccept(unittest.TestCase):
    def test_trust_region(self):
        k = cc.ErrorKey
        self.assertTrue(C.accept(k(2, 3.0), k(1, 9.0), 0.05)[0])           # fewer failures, whatever the violation
        self.assertFalse(C.accept(k(1, 0.1), k(2, 0.0), 0.05)[0])          # never more failing checks
        self.assertTrue(C.accept(k(1, 1.0), k(1, 0.4), 0.05)[0])
        self.assertTrue(C.accept(k(1, 1.0), k(1, 1.04), 0.05)[0])          # sideways inside the trust region
        ok, why = C.accept(k(1, 1.0), k(1, 1.2), 0.05)
        self.assertFalse(ok)
        self.assertIn("rose", why)


class TestLoop(Case):
    def test_expose_is_kept_and_traced(self):
        llm = FakeLLM(dict(closed_usb("E1-01"), assy_control=[{"action": "A"}]))
        rc, pkg, _ = run_offline("E1-01", self.root, self.rules, llm=llm, tag="kept")
        rec = json.loads((pkg / "design.json").read_text())["assembly"]
        trace = json.loads((pkg / "controller_trace.json").read_text())
        self.assertEqual(rc, ca.EXIT_OK)
        self.assertEqual(llm.labels().count(C.CONTROL_LABEL), ca.VOTES)
        prompt = next(p for lb, p, _ in llm.calls if lb == C.CONTROL_LABEL)
        self.assertIn("A: expose module_1.usb", prompt)
        self.assertIn("B: stop", prompt)
        self.assertIn(l1_with("E1-01", "micro-USB cable"), prompt)
        ch = rec["choices"]["exposed[module_1]"]
        self.assertEqual((ch["value"], ch["by"], ch["step"]), (True, C.CONTROLLER_BY, 1))
        self.assertEqual(ch["votes"], {"A": ca.VOTES})
        self.assertEqual(ch["overrides"]["contents_votes"], {"no": ca.VOTES})
        self.assertEqual([r["resolved"] for r in rec["coverage"]], ["exposed"])
        self.assertEqual(rec["controller"], {"kind": "llm", "budget": 6, "steps": 1, "kept": 1, "stop": "every check passes"})
        self.assertEqual([s.get("kind") for s in trace["steps"]], ["initial", None])
        s0, s1 = trace["steps"]
        self.assertEqual(s0["error"], {"hard_failures": 1, "violation": 1.0})
        self.assertEqual(s0["failing"], ["text_coverage"])
        self.assertEqual((s1["accepted"], s1["chosen"], s1["action"]["kind"]), (True, "A", "expose"))
        self.assertEqual(s1["error_after"], {"hard_failures": 0, "violation": 0})
        self.assertNotEqual(s1["state_before"], s1["state_after"])
        self.assertEqual(len(s1["state_before"]), C.DIGEST_HEX)
        self.assertEqual(trace["final"]["failing"], [])
        self.assertEqual(trace["accepted"][0]["key"], "expose:module_1.usb=True")
        # the authority audit: the controller's exposure is an llm decision; the archetype is the R07 semantic rule
        auth = trace["authority"]
        self.assertGreaterEqual(auth["decisions"]["llm"], 1)
        self.assertEqual(auth["unregistered"], [])
        self.assertIn({"decision": "archetype", "by": "rule:only_feasible", "migration": "R07"},
                      auth["semantic_rule_decisions"])
        results = {r["check_id"]: r for r in rec["results"]}
        self.assertTrue(results["text_coverage"]["passed"])
        pico = next(r["id"] for r in json.loads((pkg / "layout.json").read_text())["references"]
                    if r["part"] == "rpi_pico2")
        self.assertTrue(results[f"clear_{pico}_plug"]["passed"])

    def test_stop_leaves_the_failure_visible(self):
        llm = FakeLLM(dict(closed_usb("E1-01"), assy_control=[{"action": "B"}]))
        rc, pkg, _ = run_offline("E1-01", self.root, self.rules, llm=llm, tag="stop")
        rec = json.loads((pkg / "design.json").read_text())["assembly"]
        trace = json.loads((pkg / "controller_trace.json").read_text())
        self.assertEqual(rc, ca.EXIT_UNSATISFIED)
        self.assertEqual(trace["stop"], {"reason": "the controller chose stop", "step": 1})
        self.assertIsNone(trace["steps"][1]["accepted"])
        self.assertNotIn("exposed[module_1]", rec["choices"])
        cov = next(r for r in rec["results"] if r["check_id"] == "text_coverage")
        self.assertFalse(cov["passed"])
        self.assertNotIn("conflict", cov["evidence"])           # a controllable failure, not a requirement question
        self.assertEqual([c for c in rec["conflicts"] if c["kind"] == "coverage"], [])
        self.assertEqual([r["resolved"] for r in rec["coverage"]], [A.COVERAGE_OPEN])

    def test_infeasible_expose_is_rejected_and_typed(self):
        # every placement holding the Pico's exposed connector collides: the action cannot be applied; the design is
        # unchanged, the action is tabu, the loop stops, and text_coverage is typed as a coverage conflict
        llm = FakeLLM(dict(closed_usb("V1"), assy_control=[{"action": "A"}]))
        orig = lay.Placer.place

        def place(placer, items_, assign):
            if "module_1" in assign:
                raise lay.LayoutError("collides", "module_1 collides (test)")
            return orig(placer, items_, assign)

        with mock.patch.object(lay.Placer, "place", place):
            rc, pkg, _ = run_offline("V1", self.root, self.rules, llm=llm, tag="infeasible")
        rec = json.loads((pkg / "design.json").read_text())["assembly"]
        trace = json.loads((pkg / "controller_trace.json").read_text())
        self.assertEqual(rc, ca.EXIT_UNSATISFIED)
        step = trace["steps"][1]
        self.assertFalse(step["accepted"])
        self.assertIn("infeasible", step["reason"])
        self.assertIn("collides", step["reason"])
        self.assertEqual(trace["stop"]["reason"], "no failing check has an action")
        self.assertIn("expose:module_1.usb=True", rec["control"]["infeasible"])
        cov = next(r for r in rec["results"] if r["check_id"] == "text_coverage")
        self.assertFalse(cov["passed"])
        self.assertIn("infeasible", cov["evidence"]["conflict"])
        conflicts = [c for c in rec["conflicts"] if c["kind"] == "coverage"]
        self.assertEqual(len(conflicts), 1, rec["conflicts"])
        self.assertIn(l1_text("V1", l1_with("V1", "micro-USB cable"))[:40], conflicts[0]["conflict"])

    def test_a_step_that_raises_the_error_is_undone(self):
        d, llm = staged("E1-01", self.root / "undo", dict(closed_usb("E1-01"), assy_control=[{"action": "A"}]),
                        self.rules)
        st = d.assy
        real = C.plant
        worse = cc.CheckResult("injected", "rules", "clear_of", False, -2.0, "mm", {}, {"detail": "injected (test)"})

        def plant(state):
            plan, results, links = real(state)
            return plan, (results + [worse] if state is not st else results), links

        before = C.decision_vector(st)
        with mock.patch.object(C, "plant", plant):
            trace = C.run_loop(d, llm)
        step = trace["steps"][1]
        self.assertFalse(step["accepted"])
        self.assertIn("rose", step["reason"])                   # same failing count (coverage fixed, one injected)
        self.assertIn("injected", step["failing_after"])
        self.assertEqual(C.decision_vector(d.assy), before)      # the design is unchanged
        self.assertEqual(trace["stop"]["reason"], "no failing check has an action")   # the action is tabu

    def test_budget_bounds_the_steps(self):
        (self.root / "b0").mkdir(exist_ok=True)
        rules = test_rules(self.root / "b0", fn=24, controller_step_budget=0)
        d, llm = staged("E1-01", self.root / "budget", dict(closed_usb("E1-01"), assy_control=[{"action": "A"}]), rules)
        trace = C.run_loop(d, llm)
        self.assertEqual(trace["stop"], {"reason": "step budget spent (0)", "step": 0})
        self.assertNotIn(C.CONTROL_LABEL, llm.labels())

    def test_feedback_lines_reach_the_next_prompt(self):
        d, _ = staged("E1-01", self.root / "fb", closed_usb("E1-01"), self.rules)
        st = d.assy
        plan, results, links = C.plant(st)
        terms = C.error_vector(st, results, links)
        options = C.menu(st, results, []) + [C.STOP_ACTION]
        prompt = C.control_prompt(d, st, terms, options, ["step 1: A (expose module_1.usb) was undone: test"])
        self.assertIn("Earlier steps:\n- step 1: A (expose module_1.usb) was undone: test", prompt)
        self.assertIn("- module_1: raspberry pi pico 2 x1; connectors: usb closed", prompt)
        self.assertEqual(C.menu(st, results, ["expose:module_1.usb=True"]), [])        # tabu


class TestCheckpoints(Case):
    def test_fork_starts_from_the_stage_entry_and_leaves_the_state_alone(self):
        d, _ = staged("E1-01", self.root / "cp", closed_usb("E1-01"), self.rules)
        st = d.assy
        self.assertEqual(list(st.checkpoints), ["stack", "arrange", "vents", "envelopes", "archetype", "derive"])
        self.assertEqual(st.checkpoints["arrange"].stage, "arrange_contents")
        fork = C.fork_from(st, "arrange")
        self.assertEqual(sorted(fork.checkpoints), ["stack"])
        self.assertIsNot(fork.contents, st.contents)
        self.assertEqual(fork.choices.get("edge[connector_1]"), None)     # the arrangement's votes are not in the fork
        A.expose_connector(fork, "module_1", "usb", by=C.CONTROLLER_BY, record={"step": 1})
        self.assertFalse(next(c for c in st.contents if c["id"] == "module_1")["exposed"])
        self.assertFalse(next(c for c in st.checkpoints["arrange"].contents if c["id"] == "module_1")["exposed"])
        with self.assertRaises(ValueError):
            C.fork_from(A.AssemblyState(), "arrange")


class TestClosure(Case):
    def test_closure_sensor_reads_lid_sentences_only(self):
        # the old rule's gate, now the sensor's reading (T7 of delta 003 in the new frame)
        rules = pt.load_rules(REPO / "design_rules.json")
        for name, t_, want in ([(rid, texts(rid), {}) for rid in ("E1-01", "V1", "V2", "V3")]
                               + [(g, gen_texts(g), {}) for g in ("G04", "G11")]
                               + [(g, gen_texts(g), {A.REBATE}) for g in ("G02", "G13")]):
            with self.subTest(name=name):
                st = A.AssemblyState(rules=rules, texts=list(t_))
                self.assertEqual(set(A.closure_text_evidence(st)), set(want))
                self.assertEqual(A.closure_choice(st), {"value": "lip", "by": "rule:default_closure"})
        st = A.AssemblyState(rules=rules, texts=[("request", "The walls have a rebate for the label."),
                                                 ("L1.1", "The lid is screwed down.")])
        self.assertEqual(A.closure_text_evidence(st), {})
        self.assertEqual(A.buildable_closures(rules), ["lip", A.REBATE])

    def test_rebate_by_the_controller(self):
        # G02 names a rebate lid (L1.8): the proposal keeps the default lip, closure_evidence fails after the first build,
        # and the controller's set_closure is kept (an unscripted FakeLLM takes the first offered action)
        llm, status, child, st, results = gen_run(self.root, "G02", g02_script(), tag="_r01")
        self.assertEqual(status, ca.Status.SUCCESS, (type(child).__name__, st.notes[-3:]))
        first = st.trajectory["steps"][0]
        self.assertIn("closure_evidence", first["failing"])
        self.assertEqual((st.choices["closure"]["value"], st.choices["closure"]["by"]), (A.REBATE, C.CONTROLLER_BY))
        self.assertTrue(all("rebate" in e["quote"] for e in st.choices["closure"]["evidence"]))
        self.assertEqual(st.control["closure"], A.REBATE)
        self.assertNotIn("lid_lip", st.graph.nodes)
        kept = [s_["action"]["kind"] for s_ in st.trajectory["steps"][1:] if s_.get("accepted")]
        self.assertIn("set_closure", kept)
        self.assertTrue(results["closure_evidence"].passed, results["closure_evidence"].evidence)
        self.assertIn(C.CONTROL_LABEL, llm.labels())


    def test_infeasible_rebate_is_a_typed_conflict_not_a_missing_package(self):
        # no inside boss layout fits: before R01 the rebate rule made derive fail and the run left no package (delta 003
        # review N1); now the proposal keeps the lip, the controller's set_closure is rejected as infeasible, and
        # closure_evidence is typed as a closure conflict in a package that is written
        def no_room(st, layout, res):
            raise A.BossLayoutInfeasible(f"{layout}: no free position (test)")

        with mock.patch.object(A, "inside_boss_positions", no_room):
            llm, status, child, st, results = gen_run(self.root, "G02", g02_script(), tag="_r01_nf")
        self.assertEqual(status, ca.Status.SUCCESS, (type(child).__name__, st.notes[-3:]))
        rows = [s_ for s_ in st.trajectory["steps"][1:] if (s_.get("action") or {}).get("kind") == "set_closure"]
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["accepted"])
        self.assertIn("infeasible", rows[0]["reason"])
        self.assertEqual(st.choices["closure"]["value"], "lip")
        self.assertIn("set_closure:closure=rebate", st.control["infeasible"])
        ev = results["closure_evidence"].evidence
        self.assertFalse(results["closure_evidence"].passed)
        self.assertEqual(ev["competing_rule"], "closure")
        self.assertIn("cannot build", ev["conflict"])


class TestStub(Case):
    def test_first_offered_option(self):
        schema = ca.obj_schema({"a": {"type": "string", "enum": ["x", "y"]},
                                "b": ca.obj_schema({"quantity": {"type": "integer", "enum": [0, 1, 2]},
                                                    "exposed": {"type": "string", "enum": ["yes", "no"]}}),
                                "n": {"type": "integer"}, "f": {"type": "boolean"}})
        self.assertEqual(C.first_option(schema), {"a": "x", "b": {"quantity": 0, "exposed": "yes"}, "n": 0, "f": False})
        stub = C.StubController()
        self.assertEqual(stub.ask_json("q", schema)["a"], "x")
        self.assertEqual(stub.p_yes_many(["p", "q"]), [0.5, 0.5])
        self.assertEqual(C.ncalls(stub), 3)

    def test_stub_takes_no_corrective_step(self):
        d = new_design("E1-01", self.root / "stub", rules_path=self.rules)
        status, child = run_stages(d, FakeLLM(closed_usb("E1-01")), "DeriveFeatures")
        self.assertEqual(status, ca.Status.SUCCESS)
        stub = C.StubController()
        trace = C.run_loop(d, stub)
        self.assertEqual(trace["controller"], "stub")
        self.assertEqual(trace["budget"], 0)
        self.assertEqual(trace["stop"], {"reason": "stub controller: no corrective steps", "step": 0})
        self.assertEqual(stub.calls, 0)
        self.assertFalse(next(c for c in d.assy.contents if c["part"] == "rpi_pico2")["exposed"])

    def test_cli_stub_creates_no_llm_agent(self):
        def no_agent(*a, **k):
            raise AssertionError("the stub controller must not create an Ollama agent")

        r = json.loads((REPO / "benchmarks" / "enclosure" / "enclosure.json").read_text())["requests"][0]
        l1 = self.root / "stub_l1.json"
        l1.write_text(json.dumps(r["l1"]))
        out = self.root / "stub_out"
        with mock.patch.object(ca, "OllamaAgent", no_agent), mock.patch("builtins.print"):
            rc = ca.main(["--mode", "assembly", "--auto", "--controller", "stub", "--l1", str(l1), "--parts",
                          str(REPO / "benchmarks" / "enclosure" / "parts"), "--rules", str(self.rules), "--out",
                          str(out), r["request"]])
        pkg = sorted(out.glob("*/"))[-1]
        self.assertEqual(rc, ca.EXIT_FAILED)                     # every quantity's first option is 0: no contents
        rec = json.loads((pkg / "design.json").read_text())
        self.assertEqual(rec["assembly"]["stage"], "contents")
        self.assertTrue(all("STUB" in f.read_text() for f in (pkg / "llm").glob("*.txt")))
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            ca.main(["--controller", "stub", "a box"])            # the probe is assembly mode's only


class TestQuestionCache(unittest.TestCase):
    def test_a_repeated_question_is_answered_once(self):
        llm = FakeLLM({"q": [{"a": "x"}, {"a": "y"}], "assy_confirm": [{"answer": "yes"}]})
        cache = C.QuestionCache(llm)
        schema = ca.obj_schema({"a": {"type": "string", "enum": ["x", "y"]}})
        first = cache.ask_json("prompt", schema, temperature=0.0, seed=0, label="q")
        again = cache.ask_json("prompt", schema, temperature=0.0, seed=0, label="q")
        other = cache.ask_json("prompt", schema, temperature=0.7, seed=1, label="q")    # another sample: asked
        self.assertEqual((first, again, other), ({"a": "x"}, {"a": "x"}, {"a": "y"}))
        self.assertEqual(llm.labels(), ["q", "q"])
        self.assertEqual(cache.p_yes_many(["p1", "p2"], "assy_confirm"), [0.9, 0.9])
        self.assertEqual(cache.p_yes_many(["p2", "p3"], "assy_confirm"), [0.9, 0.9])   # only p3 is asked
        self.assertEqual(llm.labels().count("assy_confirm"), 3)
        self.assertEqual(cache.hits, 2)
        self.assertIs(cache.calls, llm.calls)                     # everything else is the wrapped controller's
        self.assertTrue(C.is_stub(C.QuestionCache(C.StubController())))


class TestRegressionInvariance(Case):
    def test_controller_exposure_equals_the_pre_r01_path(self):
        # the 9B's real Contents answer (USB closed) + the controller's expose gives the very package of a run whose
        # Contents exposed it (the path rule:text_coverage forced before R01): feature graph, layout and meshes
        out = {}
        for tag, script in (("yes", script_for("E1-01")), ("no", dict(closed_usb("E1-01"), assy_control=[{"action": "A"}]))):
            llm = FakeLLM(script)
            rc, pkg, _ = run_offline("E1-01", self.root, self.rules, llm=llm, tag=f"inv_{tag}")
            out[tag] = (rc, graph_hash(pkg), json.loads((pkg / "layout.json").read_text())["references"],
                        llm.labels().count(C.CONTROL_LABEL))
        self.assertEqual(out["yes"][0], out["no"][0])
        self.assertEqual(out["yes"][1], out["no"][1])
        self.assertEqual(out["yes"][2], out["no"][2])
        self.assertEqual((out["yes"][3], out["no"][3]), (0, ca.VOTES))   # no question when nothing actionable fails


if __name__ == "__main__":
    unittest.main()
