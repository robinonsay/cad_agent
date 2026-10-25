"""Tests for migration delta R02 (owner decision D1): content-keyed shuffled menus, permutation voting, no LLM
probability as a gate, verifier-guided search in the closed loop, and the bias audit's replay logic. No Ollama: every
model is a scripted fake (a position-biased one that always answers the option shown first, a content-following one
that always answers the same id, and the recorded-run fakes of test_assembly).
"""

import ast
import json
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

import assembly as A
import cad_agent as ca
import cad_checks as cc
import controller as C
import menus
from test_assembly import FakeLLM, gen_request, design_for, staged_to_derive, g02_script, BOTH, test_rules
from test_controller import Case, closed_usb, staged

REPO = Path(__file__).parent
sys.path.insert(0, str(REPO / "benchmarks" / "generalize"))
import audit_controller as AU  # noqa: E402

RULES = menus.vote_rules({})


def shown_ids(prompt: str, head: str = C.ACTIONS_LINE) -> list:
    """The option ids in the order a menu prompt lists them (the block after `head`)."""
    block = prompt.split(head + "\n", 1)[1].split("\n\n", 1)[0]
    return [ln[2:].split(": ", 1)[0] for ln in block.splitlines() if ln.startswith("- ")]


class FirstShown(FakeLLM):
    """A position-biased controller: every assy_control question is answered with the action shown first."""

    def chat(self, prompt, system="", images=(), schema=None, temperature=0.0, seed=0, label="ask", num_predict=None):
        if label.startswith(C.CONTROL_LABEL):
            self.calls.append((label, prompt, list(images)))
            return json.dumps({"reason": "first", "action": shown_ids(prompt)[0]})
        return super().chat(prompt, system, images, schema, temperature, seed, label, num_predict)


class Recorder:
    """A minimal ask_json fake: `answer(prompt, schema)` gives the reply; every call is kept."""

    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def ask_json(self, prompt, schema, **kw):
        self.calls.append((prompt, schema, kw))
        return self.answer(prompt, schema)


# ---------------------------------------------------------------------------
# Item 2: content-keyed, shuffled menus
# ---------------------------------------------------------------------------


class TestOrderings(unittest.TestCase):
    def test_deterministic_rotations_every_option_leads_once(self):
        ids = ["a", "b", "c"]
        o1, o2 = menus.orderings(ids, "m", 3), menus.orderings(ids, "m", 3)
        self.assertEqual(o1, o2)                                     # reproducible
        self.assertEqual(sorted(o[0] for o in o1), ids)              # each option shown first once (K = N)
        for k in range(3):
            self.assertEqual([o[k] for o in o1].count("a"), 1)       # and in every position once
        self.assertNotEqual(menus.orderings(ids, "other", 3), o1)    # another seed material, another design
        self.assertEqual(len(menus.orderings(["x", "stop"], "m", 3)), 2)   # two options have two distinct orders
        self.assertEqual(len(menus.orderings(list("abcde"), "m", 3)), 3)
        self.assertEqual(len({tuple(o) for o in menus.orderings(list("abc"), "m", 5)}), 5)  # more seeded permutations

    def test_schema_reason_first_and_enum_canonical(self):
        s = menus.menu_schema(["z", "a"], "action")
        self.assertEqual(list(s["properties"]), ["reason", "action"])
        self.assertEqual(s["properties"]["action"]["enum"], ["z", "a"])
        self.assertEqual(s["required"], ["reason", "action"])

    def test_stub_takes_pythons_first_option_under_every_shuffle(self):
        stub = C.StubController()
        for m in ("a", "b", "c"):
            v = menus.perm_vote(stub, "q", lambda order: "\n".join(order), ["first", "second", "third"], RULES, m)
            self.assertEqual(v.pick, "first")
            self.assertTrue(v.confident)


class TestControllerPrompt(Case):
    def test_content_keyed_shuffled_and_reproducible(self):
        d, _ = staged("E1-01", self.root / "ck", closed_usb("E1-01"), self.rules)
        prompts = []
        for _ in range(2):
            llm = FakeLLM({"assy_control": [{"reason": "r", "action": "stop"}]})
            trace = C.run_loop(d, llm) if not prompts else C.run_loop(d, llm)
            prompts.append([p for lb, p, _ in llm.calls if lb == C.CONTROL_LABEL])
        self.assertEqual(prompts[0], prompts[1])                          # deterministic orderings
        orders = [shown_ids(p) for p in prompts[0]]
        self.assertEqual(sorted(map(tuple, orders)), [("expose:module_1.usb", "stop"), ("stop", "expose:module_1.usb")])
        for p in prompts[0]:
            self.assertNotRegex(p, r"\n- [A-H]: ")                        # never a letter
            self.assertIn(C.CONTROL_QUESTION, p)
        step = trace["steps"][1]
        self.assertEqual(step["orders"], orders)
        self.assertEqual(step["vote"]["answers"][0]["reason"], "r")


class TestProposalMenusShuffled(Case):
    def test_edge_vote_lists_the_edges_in_several_orders(self):
        d, llm = staged("E1-01", self.root / "edge", closed_usb("E1-01"), self.rules)
        edges = [shown_ids(p, "The board edges:") for lb, p, _ in llm.calls if lb == "assy_edge"]
        self.assertGreaterEqual(len({tuple(e) for e in edges}), 2)
        self.assertEqual({tuple(sorted(e)) for e in edges}, {("+X", "+Y", "-X", "-Y")})
        self.assertIn("edge_vote", d.assy.arrange)

    def test_contents_candidates_shuffled(self):
        d, llm = staged("E1-01", self.root / "cont", closed_usb("E1-01"), self.rules)
        lists = [shown_ids(p, "Catalogue parts that may be in the request:") for lb, p, _ in llm.calls
                 if lb == "assy_contents"]
        self.assertGreaterEqual(len({tuple(x) for x in lists}), 2)
        self.assertEqual(len({tuple(sorted(x)) for x in lists}), 1)

    def test_stack_menu_is_content_keyed(self):
        # two text-backed stack options -> a permutation-voted menu of catalogue ids; the record keeps consistency
        st = A.AssemblyState()
        calls = []

        class L(FakeLLM):
            def chat(self, prompt, system="", images=(), schema=None, temperature=0.0, seed=0, label="ask",
                     num_predict=None):
                if label == "assy_stack":
                    calls.append((prompt, schema))
                    return json.dumps({"reason": "", "stack": schema["properties"]["stack"]["enum"][-1]})
                return super().chat(prompt, system, images, schema, temperature, seed, label, num_predict)

        llm = L({})
        v = menus.perm_vote(llm, "assy_stack", lambda o: "Options:\n" + "\n".join(f"- {i}: x" for i in o),
                            ["header_male_2p54", "header_female_2p54"], RULES, "m", key="stack")
        self.assertEqual(v.pick, "header_female_2p54")
        self.assertEqual(v.votes, {"header_female_2p54": 2})
        self.assertTrue(v.confident)
        self.assertEqual(list(calls[0][1]["properties"]), ["reason", "stack"])
        del st


# ---------------------------------------------------------------------------
# Item 3: permutation voting
# ---------------------------------------------------------------------------


class TestPermutationVote(unittest.TestCase):
    def test_position_bias_is_low_confidence_content_is_high(self):
        ids = ["expose:a.x", "set_closure:rebate", "stop"]

        def render(order):
            return C.ACTIONS_LINE + "\n" + "\n".join(f"- {i}: words" for i in order) + "\n\nq"

        biased = Recorder(lambda p, s: {"reason": "", "action": shown_ids(p)[0]})
        v = menus.perm_vote(biased, C.CONTROL_LABEL, render, ids, RULES, "m")
        self.assertEqual(sorted(v.votes.values()), [1, 1, 1])
        self.assertFalse(v.confident)
        self.assertAlmostEqual(v.consistency, 1 / 3, places=3)
        self.assertEqual(v.first_position, 3)
        self.assertEqual(v.pick, v.answers[0]["answer"])        # a tie goes to the first ordering's answer
        content = Recorder(lambda p, s: {"reason": "", "action": "set_closure:rebate"})
        v2 = menus.perm_vote(content, C.CONTROL_LABEL, render, ids, RULES, "m")
        self.assertEqual((v2.pick, v2.consistency, v2.confident), ("set_closure:rebate", 1.0, True))
        self.assertEqual(v2.ranked()[0], "set_closure:rebate")
        self.assertEqual(len(content.calls), 3)

    def test_invalid_answers_and_thresholds(self):
        bad = Recorder(lambda p, s: {"action": "B"})                      # a letter is not an id
        v = menus.perm_vote(bad, "q", lambda o: "x", ["a", "b"], RULES, "m")
        self.assertIsNone(v.pick)
        self.assertEqual(v.valid, 0)
        loose = menus.vote_rules({"menu_consistency_min": {"value": 0.5}, "menu_orderings": 4})
        self.assertEqual((loose["menu_orderings"], loose["menu_consistency_min"]), (4, 0.5))

    def test_perm_tally_counts_per_key(self):
        def answer(p, s):
            first = p.splitlines()[0]
            return {"a": first, "b": "y"}

        got = menus.perm_tally(Recorder(answer), "q", lambda o: "\n".join(o["opts"]), {"opts": ["x", "y", "z"]},
                               {}, {"a": ["x", "y", "z"], "b": ["x", "y", "z"]}, RULES, "m")
        self.assertEqual(got["consistency"]["b"], 1.0)
        self.assertAlmostEqual(got["consistency"]["a"], 1 / 3, places=3)
        self.assertEqual(sum(got["counts"]["a"].values()), 3)

    def test_tie_goes_to_the_earliest_valid_tied_answer(self):
        # review fix 4: decide()'s tie rule as documented: ordering 0's answer wins a tie when it is valid and tied;
        # when ordering 0's answer is invalid (or not among the tied) the tied option answered earliest wins
        ids = ["a", "b", "c"]

        def scripted(seq):
            it = iter(seq)
            return Recorder(lambda p, s: {"action": next(it)})

        v = menus.perm_vote(scripted(["b", "a", "c"]), "q", lambda o: "x", ids, RULES, "m")
        self.assertEqual((v.pick, v.votes), ("b", {"b": 1, "a": 1, "c": 1}))      # ordering 0's answer
        v = menus.perm_vote(scripted(["B", "c", "a"]), "q", lambda o: "x", ids, RULES, "m")
        self.assertEqual(v.answers[0]["answer"], None)
        self.assertEqual(v.pick, "c")                                             # invalid first: earliest valid
        v = menus.perm_vote(scripted(["c", "a", "a", "b", "b"]), "q", lambda o: "x", ids,
                            menus.vote_rules({"menu_orderings": 5}), "m")
        self.assertEqual(v.pick, "a")                                             # c is not tied: earliest tied

    def test_perm_tally_invalid_answer_never_wins_a_tie(self):
        # review fix 4: an invalid answer (None) counted first and tied with a valid one does not win the majority
        seq = iter([{"a": "bad"}, {"a": "y"}])
        got = menus.perm_tally(Recorder(lambda p, s: next(seq)), "q", lambda o: "x", {"opts": ["x", "y"]}, {},
                               {"a": ["x", "y"]}, RULES, "m")
        self.assertEqual(dict(got["counts"]["a"]), {None: 1, "y": 1})
        self.assertEqual(A.majority(got["counts"]["a"]), "y")
        self.assertEqual(list(got["counts"]["a"])[-1], None)
        seq2 = iter([{"a": "bad"}, {"a": "bad"}, {"a": "y"}])
        got2 = menus.perm_tally(Recorder(lambda p, s: next(seq2)), "q", lambda o: "x", {"opts": ["x", "y", "z"]}, {},
                                {"a": ["x", "y", "z"]}, RULES, "m")
        self.assertIsNone(A.majority(got2["counts"]["a"]))                       # strictly more invalid: None


# ---------------------------------------------------------------------------
# Item 4: no LLM probability gates a decision
# ---------------------------------------------------------------------------


class TestNoProbabilityGate(unittest.TestCase):
    def test_agent_modules_call_no_p_yes(self):
        """assembly.py and layout.py call no p_yes / yes_score; controller.py only inside the wrappers that forward it
        (QuestionCache, StubController)."""
        for name, allowed in (("assembly.py", set()), ("layout.py", set()),
                              ("controller.py", {"QuestionCache", "StubController"})):
            tree = ast.parse((REPO / name).read_text())
            owners = {}
            for c in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                for sub in ast.walk(c):
                    owners.setdefault(id(sub), c.name)
            bad = [f"{name}:{node.lineno}" for node in ast.walk(tree)
                   if isinstance(node, ast.Attribute) and node.attr in ("p_yes", "p_yes_many", "yes_score")
                   and isinstance(node.ctx, ast.Load) and owners.get(id(node)) not in allowed]
            self.assertEqual(bad, [], name)


class TestArrangementMenu(Case):
    def test_arrangement_without_p_yes(self):
        class NoProb(FakeLLM):
            def p_yes(self, *a, **k):
                raise AssertionError("p_yes must not be asked (R02)")

            p_yes_many = p_yes

        from test_assembly import new_design, run_stages
        d = new_design("E1-01", self.root / "noprob", rules_path=self.rules)
        llm = NoProb(closed_usb("E1-01"))
        status, child = run_stages(d, llm, "ControllerLoop")
        self.assertEqual(status, ca.Status.SUCCESS, (type(child).__name__, d.assy.notes[-3:]))
        self.assertNotIn("assy_confirm", llm.labels())
        self.assertNotIn("p_yes", d.assy.choices["arrangement_confirmed"])

    def test_class_menu_decides_against_an_inconsistent_vote(self):
        # decide(): agreement -> llm:vote+menu; a consistent menu overrides the edge vote -> llm:menu; an inconsistent
        # menu leaves the edge vote -> llm:vote; no answer at all -> the registered first-option fallback
        arr = A.ArrangeContents.__new__(A.ArrangeContents)
        cands = [{"assignment": {"m": "-X"}, "words": "m faces -X", "votes": 3, "class": 0},
                 {"assignment": {"m": "-Y"}, "words": "m faces -Y", "votes": 0, "class": 1}]
        classes = [{"id": "m=-X", "rep": 0, "members": [0]}, {"id": "m=-Y", "rep": 1, "members": [1]}]

        def with_vote(votes, valid):
            v = menus.MenuVote(ids=["m=-X", "m=-Y"], votes=votes, valid=valid)
            v.answers = [{"answer": k} for k in votes]
            return menus.decide(v, RULES)

        for votes, valid, voted, want in (({"m=-X": 2}, 2, 0, (0, "llm:vote+menu")),
                                          ({"m=-Y": 2}, 2, 0, (1, "llm:menu")),
                                          ({"m=-Y": 1, "m=-X": 1}, 2, 0, (0, "llm:vote")),
                                          ({}, 0, None, (0, "rule:first_option[arrange]"))):
            with mock.patch.object(A.ArrangeContents, "ask_classes", lambda self, c, k, v=with_vote(votes, valid): v):
                pick, by, extra = arr.decide(cands, classes, voted)
            self.assertEqual((pick, by), want, votes)
            self.assertIn("class_vote", extra)
        self.assertEqual(arr.decide(cands[:1], classes[:1], None)[1], "rule:symmetric_class")


# ---------------------------------------------------------------------------
# Item 5: verifier-guided search in the closed loop
# ---------------------------------------------------------------------------


class TestSearch(Case):
    def test_inconsistent_vote_is_searched_and_the_measured_best_kept(self):
        # a position-biased controller splits its votes 1:1 between expose and stop (two orderings): low confidence, so
        # both are candidates; expose measures lower than the current design and is kept
        d, _ = staged("E1-01", self.root / "s1", closed_usb("E1-01"), self.rules)
        llm = FirstShown(closed_usb("E1-01"))
        trace = C.run_loop(d, llm)
        step = trace["steps"][1]
        self.assertFalse(step["confident"])
        self.assertEqual(step["votes"], {"expose:module_1.usb": 1, "stop": 1})
        ids = [c["id"] for c in step["candidates"]]
        self.assertEqual(sorted(ids), ["expose:module_1.usb", "stop"])
        exp = next(c for c in step["candidates"] if c["id"] == "expose:module_1.usb")
        self.assertEqual(exp["outcome"], "kept")
        self.assertEqual(exp["error_after"], {"hard_failures": 0, "violation": 0})
        self.assertEqual(exp["sensor_delta"], {"hard_failures": -1, "violation": -1.0})
        self.assertEqual((step["accepted"], step["selected"]), (True, "expose:module_1.usb"))
        self.assertEqual(trace["final"]["failing"], [])
        # the record is complete training data: state, menu, orders, votes with reasons, candidates, outcome
        for k in ("state_before", "state_summary", "error_before", "terms_before", "menu", "orders", "vote", "chosen",
                  "candidates", "selected", "selected_by", "outcome", "error_after", "state_after", "sensor_delta"):
            self.assertIn(k, step, k)
        self.assertEqual(trace["evals"], 1)

    def test_measured_error_overrides_the_vote_ranking(self):
        # G02: the controller ranks set_closure first (2 of 3 orderings) but not unanimously; Python measures every
        # survivor and an injected extra failure on the closure fork makes expose the lower-error choice
        r = gen_request("G02")
        root = self.root / "s2"
        d = design_for(r["request"], r["l1"], root / "G02", BOTH, test_rules(root.parent, fn=24))
        script = g02_script()
        status, child, st, _ = staged_to_derive(d, FakeLLM(dict(script, assy_control=[{"action": "stop"}])),
                                                 "DeriveFeatures")
        self.assertEqual(status, ca.Status.SUCCESS)
        answers = iter(["set_closure:rebate", "set_closure:rebate", "expose:board.dc"] + ["stop"] * 30)

        class Split(FakeLLM):
            def chat(self, prompt, system="", images=(), schema=None, temperature=0.0, seed=0, label="ask",
                     num_predict=None):
                if label.startswith(C.CONTROL_LABEL):
                    self.calls.append((label, prompt, list(images)))
                    return json.dumps({"reason": "", "action": next(answers)})
                return super().chat(prompt, system, images, schema, temperature, seed, label, num_predict)

        real = C.plant
        worse = cc.CheckResult("injected", "rules", "clear_of", False, -2.0, "mm", {}, {"detail": "injected (test)"})

        def plant(state):
            plan, results, links = real(state)
            if state.control.get("closure") == A.REBATE:
                results = results + [worse]
            return plan, results, links

        with mock.patch.object(C, "plant", plant):
            trace = C.run_loop(d, Split(script))
        step = trace["steps"][1]
        self.assertEqual(step["chosen"], "set_closure:rebate")
        self.assertFalse(step["confident"])
        out = {c["id"]: c["outcome"] for c in step["candidates"]}
        self.assertEqual(out["expose:board.dc"], "kept")
        self.assertIn(out["set_closure:rebate"], ("undone", "not_selected"))
        self.assertEqual(step["selected"], "expose:board.dc")
        self.assertEqual(step["selected_by"], "search_among_votes")
        self.assertEqual(d.assy.choices["exposed[board.dc]" if "exposed[board.dc]" in d.assy.choices
                                        else next(k for k in d.assy.choices if k.startswith("exposed["))]["by"],
                         C.CONTROLLER_BY)

    def test_eval_budget_limits_the_candidates(self):
        # changed in the R02/R11 review fixes (finding 2): max_evals is a hard cap; with none left no action is measured
        # (was: at least the top candidate) and the loop stops before asking
        (self.root / "s3").mkdir(exist_ok=True)
        rules = test_rules(self.root / "s3", fn=24, controller_search_max_evals=0)
        d, _ = staged("E1-01", self.root / "s3b", closed_usb("E1-01"), rules)
        vote = menus.MenuVote(ids=["a", "b", "c", C.STOP], votes={"a": 1, "b": 1, "c": 1}, valid=3)
        vote.answers = [{"answer": "a"}, {"answer": "b"}, {"answer": "c"}]
        menus.decide(vote, RULES)
        self.assertEqual(C.search_candidates(vote, 3, 0), [])                # the budget is spent: nothing measured
        self.assertEqual(C.search_candidates(vote, 3, 1), ["a"])
        self.assertEqual(C.search_candidates(vote, 3, 5), ["a", "b", "c"])
        vote2 = menus.MenuVote(ids=["a", "b", C.STOP], votes={"b": 2}, valid=2)
        menus.decide(vote2, RULES)
        self.assertEqual(C.search_candidates(vote2, 3, 5), ["b"])            # confident: only the voted action
        llm = FirstShown(closed_usb("E1-01"))
        trace = C.run_loop(d, llm)
        self.assertEqual(trace["evals"], 0)
        self.assertEqual(trace["stop"]["reason"], "search evaluation budget spent (0 plant evaluations)")
        self.assertNotIn(C.CONTROL_LABEL, llm.labels())                     # stopped before asking
        self.assertEqual(C.search_rules({"controller_search_depth": 3})["depth"], 1)
        self.assertEqual(C.decision_class(C.SEARCH_BY, {}), "guardrail")

    def test_total_evaluations_never_exceed_max_evals(self):
        # review fix 2: over a whole run the plant evaluations (forks measured) are at most max_evals, counted at the
        # evaluate() call itself, while each inconsistent step would otherwise measure several candidates
        for cap in (1, 2):
            with self.subTest(max_evals=cap):
                root = self.root / f"cap{cap}"
                root.mkdir(exist_ok=True)
                r = gen_request("G02")
                d = design_for(r["request"], r["l1"], root / "G02", BOTH,
                               test_rules(root, fn=24, controller_search_max_evals=cap))
                script = g02_script()
                status, _, _, _ = staged_to_derive(d, FakeLLM(dict(script, assy_control=[{"action": "stop"}])),
                                                   "DeriveFeatures")
                self.assertEqual(status, ca.Status.SUCCESS)
                calls = []
                real = C.evaluate

                def counted(*a, **k):
                    calls.append(a[4].id)
                    return real(*a, **k)

                with mock.patch.object(C, "evaluate", counted):
                    trace = C.run_loop(d, FirstShown(script))
                self.assertLessEqual(len(calls), cap)
                self.assertEqual(trace["evals"], len(calls))
                self.assertEqual(sum(s.get("evals", 0) for s in trace["steps"][1:]), len(calls))

    def test_confident_stop_ends_the_loop_whatever_the_consistency_threshold(self):
        # review fix 2: with menu_consistency_min below 1 a winner can be confident while other actions have votes; a
        # confident stop is still the only candidate (no fork is measured) and the loop ends
        loose = menus.vote_rules({"menu_consistency_min": 0.6})
        vote = menus.MenuVote(ids=["expose:board.dc", C.STOP], votes={C.STOP: 2, "expose:board.dc": 1}, valid=3)
        vote.answers = [{"answer": C.STOP}, {"answer": "expose:board.dc"}, {"answer": C.STOP}]
        menus.decide(vote, loose)
        self.assertTrue(vote.confident)
        self.assertEqual(C.search_candidates(vote, 3, 5), [C.STOP])
        root = self.root / "cstop"
        root.mkdir(exist_ok=True)
        r = gen_request("G02")
        d = design_for(r["request"], r["l1"], root / "G02", BOTH,
                       test_rules(root, fn=24, menu_consistency_min=0.6))
        script = g02_script()
        status, _, _, _ = staged_to_derive(d, FakeLLM(dict(script, assy_control=[{"action": "stop"}])),
                                           "DeriveFeatures")
        self.assertEqual(status, ca.Status.SUCCESS)
        answers = iter([C.STOP, "expose:board.dc", C.STOP] + [C.STOP] * 30)

        class Mostly(FakeLLM):
            def chat(self, prompt, system="", images=(), schema=None, temperature=0.0, seed=0, label="ask",
                     num_predict=None):
                if label.startswith(C.CONTROL_LABEL):
                    self.calls.append((label, prompt, list(images)))
                    return json.dumps({"reason": "", "action": next(answers)})
                return super().chat(prompt, system, images, schema, temperature, seed, label, num_predict)

        with mock.patch.object(C, "evaluate", side_effect=AssertionError("a confident stop measures nothing")):
            trace = C.run_loop(d, Mostly(script))
        step = trace["steps"][1]
        self.assertTrue(step["confident"])
        self.assertEqual((step["selected"], step["outcome"], step["evals"]), (C.STOP, "stop", 0))
        self.assertEqual(trace["stop"]["reason"], "the controller chose stop")
        self.assertEqual(len(trace["steps"]), 2)

    def test_infeasible_candidate_does_not_retype_later_forks(self):
        # review fix B1 (the reproduced G02 case): the first candidate (expose:board.dc) is infeasible; once every
        # expose of the named plug is infeasible, the coverage sensor types text_coverage as a conflict. Before the fix
        # that infeasibility was written to the live state inside the candidate loop, so the later set_closure fork was
        # measured with text_coverage excluded while `key` and stop still counted it: a rebate fork that raises the
        # violation by 1.0 (> the 0.05 trust region) was kept. Now every fork starts from the pre-step bookkeeping and,
        # after the merge, the current design and every fork are re-measured under the same typing
        root = self.root / "b1"
        root.mkdir(exist_ok=True)
        r = gen_request("G02")
        d = design_for(r["request"], r["l1"], root / "G02", BOTH, test_rules(root, fn=24))
        script = g02_script()
        status, _, _, _ = staged_to_derive(d, FakeLLM(dict(script, assy_control=[{"action": "stop"}])),
                                           "DeriveFeatures")
        self.assertEqual(status, ca.Status.SUCCESS)
        _, results0, _ = C.plant(d.assy)
        self.assertEqual(sorted(x.check_id for x in results0 if not x.passed), ["closure_evidence", "text_coverage"])
        answers = iter(["expose:board.dc", "expose:board.dc", "set_closure:rebate"] + [C.STOP] * 30)

        class Split(FakeLLM):
            def chat(self, prompt, system="", images=(), schema=None, temperature=0.0, seed=0, label="ask",
                     num_predict=None):
                if label.startswith(C.CONTROL_LABEL):
                    self.calls.append((label, prompt, list(images)))
                    return json.dumps({"reason": "", "action": next(answers)})
                return super().chat(prompt, system, images, schema, temperature, seed, label, num_predict)

        real_eval, real_plant = C.evaluate, C.plant
        worse = cc.CheckResult("injected", "rules", "clear_of", False, -2.0, "mm", {}, {"detail": "injected (test)"})
        seen_control = []

        def evaluate(design, llm, st, accepted, action, record, by, **kw):
            seen_control.append((action.id, dict((kw.get("control") or {}).get("infeasible") or {})))
            if action.id == "expose:board.dc":
                return {"fork": None, "err": "forced infeasible (test)", "plan": None, "results": None, "links": None}
            return real_eval(design, llm, st, accepted, action, record, by, **kw)

        def plant(state):
            plan, results, links = real_plant(state)
            if state.control.get("closure") == A.REBATE:
                results = results + [worse]
            return plan, results, links

        with mock.patch.object(C, "evaluate", evaluate), mock.patch.object(C, "plant", plant):
            trace = C.run_loop(d, Split(script))
        step = trace["steps"][1]
        self.assertEqual(step["error_before"], {"hard_failures": 2, "violation": 2.0})
        # every candidate of the step forked from the same (pre-step) bookkeeping: no infeasibility leaked mid-step
        self.assertEqual([c for _, c in seen_control], [{}, {}])
        out = {c["id"]: c for c in step["candidates"]}
        self.assertEqual(out["expose:board.dc"]["outcome"], "infeasible")
        # re-measured under the merged typing: text_coverage is a conflict on both sides of the comparison
        self.assertEqual(step["error_before_retyped"], {"hard_failures": 1, "violation": 1.0})
        self.assertEqual(out[C.STOP]["error_after"], {"hard_failures": 1, "violation": 1.0})
        self.assertEqual(out["set_closure:rebate"]["error_after"], {"hard_failures": 1, "violation": 2.0})
        self.assertEqual(out["set_closure:rebate"]["outcome"], "undone")
        self.assertIn("violation rose", out["set_closure:rebate"]["reason"])
        self.assertEqual((step["selected"], step["outcome"]), (C.STOP, "stop"))
        self.assertNotEqual((d.assy.choices.get("closure") or {}).get("value"), A.REBATE)
        self.assertEqual(trace["final"]["error"], {"hard_failures": 1, "violation": 1.0})
        self.assertNotIn("injected", trace["final"]["failing"])

    def test_new_action_kinds_plug_in(self):
        # a new kind registers an applier; its id, menu line, vote and search need no change
        a = C.Action("add_duct", "fan_1", True, "add_duct fan_1: route a duct from the fan to the wall")
        self.assertEqual((a.id, a.desc), ("add_duct:fan_1", "route a duct from the fan to the wall"))
        self.assertEqual(C.Action.from_dict(a.to_dict()).id, a.id)
        self.assertEqual(C.Action("set_hinge", "", "pin", "x").id, "set_hinge:pin")
        self.assertEqual(C.STOP_ACTION.id, "stop")
        with self.assertRaises(ValueError):
            C.apply_action(A.AssemblyState(), a, {})
        seen = []
        with mock.patch.dict(C.APPLIERS, {"add_duct": lambda st, act, rec, by: seen.append((act.id, by))}):
            C.apply_action(A.AssemblyState(), a, {})
        self.assertEqual(seen, [("add_duct:fan_1", C.CONTROLLER_BY)])


# ---------------------------------------------------------------------------
# Item 1: the bias audit's replay logic (offline)
# ---------------------------------------------------------------------------


class TestAudit(unittest.TestCase):
    def package(self, root: Path) -> Path:
        pkg = root / "G00_s1" / "20260101-000000"
        (pkg / "llm").mkdir(parents=True)
        menu = [{"kind": "expose", "target": "board.usb", "value": True,
                 "words": "expose board.usb: open the wall for the usb connector"},
                {"kind": "stop", "target": "", "value": None, "words": "stop: keep the design as it is"}]
        (pkg / "controller_trace.json").write_text(json.dumps({"steps": [
            {"step": 0, "kind": "initial"},
            {"step": 1, "menu": menu, "votes": {"A": 3}, "chosen": "A", "accepted": True, "reason": "fewer"}]}))
        prompt = ("Request: a box\n\nThe design was built and measured.\n\nThe design now:\n"
                  "- board (primary): a board x1; connectors: usb closed, sd open through -X\n- lid closure: lip\n\n"
                  f"{AU.ACTIONS_LINE}\n- A: {menu[0]['words']}\n- B: {menu[1]['words']}\n\n{AU.LETTER_Q}")
        for i in range(3):
            (pkg / "llm" / f"00{i + 1}_assy_control.txt").write_text(
                f"MODEL: m\nIMAGES: []\n\n=== SYSTEM ===\n\n\n=== PROMPT ===\n{prompt}\n\n=== RESPONSE ===\n"
                '{"action": "A"}\n')
        (pkg / "design.json").write_text(json.dumps({"assembly": {"coverage": [{"item": "board",
                                                                                 "connector": "sd"}]}}))
        return pkg

    def test_replay_measures_position_and_content(self):
        with tempfile.TemporaryDirectory() as t:
            pkg = self.package(Path(t))
            ds = AU.control_decisions(pkg, ["lip", "rebate"])
            self.assertEqual(len(ds), 1)
            d = ds[0]
            self.assertEqual(d["ids"], ["expose:board.usb", "stop"])
            self.assertEqual(d["planted"]["target"], "board.sd")          # closes an opening whose plug the text names
            self.assertIn("coverage sensor", d["planted"]["why"])

            class Biased:      # always the first shown option (a letter A, or the first id listed)
                def ask_json(self, prompt, schema, **kw):
                    enum = schema["properties"]["action"]["enum"]
                    if enum[0] == "A":
                        return {"action": "A"}
                    return {"action": shown_ids(prompt, AU.ACTIONS_LINE)[0]}

            res = AU.audit_control(d, AU.Asker(Biased(), None, "fake"), 3, None)
            m = res["metrics"]
            self.assertEqual(m["original"]["first_position_rate"], 1.0)
            self.assertEqual(m["keyed"]["first_position_rate"], 1.0)
            self.assertLess(m["keyed"]["consistency"], 1.0)
            self.assertEqual(m["planted_lettered"]["planted_rate"], 1.0)    # the plant sits at A
            summ = AU.summarise([res])
            self.assertEqual(summ["control"]["original"]["first_position_rate"], 1.0)

            class Content:
                def ask_json(self, prompt, schema, **kw):
                    enum = schema["properties"]["action"]["enum"]
                    if enum[0] == "A":
                        lines = prompt.split(AU.ACTIONS_LINE + "\n", 1)[1].split("\n\n", 1)[0].splitlines()
                        k = next(n for n, ln in enumerate(lines) if "usb connector" in ln and "open" in ln)
                        return {"action": enum[k]}
                    return {"reason": "", "action": "expose:board.usb"}

            res2 = AU.audit_control(d, AU.Asker(Content(), None, "fake"), 3, None)
            for fmt in ("lettered", "keyed", "planted_keyed"):
                self.assertEqual(res2["metrics"][fmt]["consistency"], 1.0, fmt)
                self.assertEqual(res2["metrics"][fmt]["sensor_best_rate"], 1.0, fmt)
            self.assertEqual(res2["metrics"]["planted_keyed"]["planted_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
