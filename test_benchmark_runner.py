"""Tests for benchmarks/run.py bookkeeping, with a fake runner (no model, no OpenSCAD)."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location("bench_run", Path(__file__).parent / "benchmarks" / "run.py")
br = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(br)

REQUESTS = [
    {"id": "A", "request": "A plate.", "l1": [{"id": "L1.1", "text": "It shall be 5 mm thick.",
                                               "method": "inspection"}]},
    {"id": "B", "request": "A ball.", "l1": []},
]


class FakeRunner:
    """Pretends to be cad_agent: writes a design.json with an outcome and returns an exit code."""

    def __init__(self, outcomes):
        self.outcomes = dict(outcomes)   # (id, seed) -> (rc, outcome or None)
        self.calls = []

    def __call__(self, spec):
        self.calls.append(spec.key())
        rc, outcome = self.outcomes.get((spec.id, spec.seed), (0, "verified"))
        if outcome:
            (spec.workdir / "20260101-000000").mkdir()
            (spec.workdir / "20260101-000000" / "design.json").write_text(json.dumps(
                {"outcome": outcome, "verification": {"unsatisfied": []}}))
        return br.RunResult(rc, 1.0)


class TestBenchmarkRunner(unittest.TestCase):
    def test_exit_codes_match_the_agent(self):
        import cad_agent as ca
        self.assertEqual(br.STATUS_BY_RC[ca.EXIT_OK], "verified")
        self.assertEqual(br.STATUS_BY_RC[ca.EXIT_UNSATISFIED], "unsatisfied")
        self.assertEqual(br.STATUS_BY_RC[ca.EXIT_USAGE], "usage_error")
        self.assertEqual(br.STATUS_BY_RC[ca.EXIT_FAILED], "failed")
        self.assertEqual(br.STATUS_BY_RC[ca.EXIT_INTERRUPTED], "interrupted")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.results = self.out / "results.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, **kw):
        return br.plan_runs(REQUESTS, "base", [0, 1], self.out, **kw)

    def test_plan_layout_and_subset(self):
        specs = self.plan()
        self.assertEqual([s.key() for s in specs], [("base", "A", 0), ("base", "A", 1),
                                                     ("base", "B", 0), ("base", "B", 1)])
        self.assertEqual(specs[1].workdir, self.out / "base" / "A" / "seed1")
        self.assertEqual([s.id for s in self.plan(ids=["B"])], ["B", "B"])
        self.assertIsNone(self.plan(with_l1=False)[0].l1)
        with self.assertRaises(ValueError):
            self.plan(ids=["nope"])

    def test_command_passes_seed_l1_and_mode_only_when_needed(self):
        spec = self.plan()[1]
        cmd = br.agent_command(spec, python="py")
        self.assertEqual(cmd[:2], ["py", str(br.AGENT)])
        self.assertIn("--auto", cmd)
        self.assertEqual(cmd[cmd.index("--seed") + 1], "1")
        self.assertEqual(json.loads(cmd[cmd.index("--l1") + 1])[0]["id"], "L1.1")
        self.assertNotIn("--mode", cmd)
        self.assertEqual(cmd[-1], "A plate.")
        self.assertNotIn("--l1", br.agent_command(self.plan()[2]))       # B has no L1s
        cascade = br.agent_command(self.plan(mode="cascade", ids=["A"])[0])
        self.assertEqual(cascade[cascade.index("--mode") + 1], "cascade")

    def test_cascade_without_l1_is_refused_up_front(self):
        # Otherwise every run would be an argparse usage error (exit 2) of the agent.
        with self.assertRaises(ValueError):
            self.plan(mode="cascade")                   # B has no L1s
        with self.assertRaises(ValueError):
            self.plan(mode="cascade", ids=["A"], with_l1=False)

    def test_records_every_run_and_resumes(self):
        runner = FakeRunner({("A", 1): (3, "unsatisfied"), ("B", 0): (None, None), ("B", 1): (1, None)})
        lines = br.run_benchmark(self.plan(), self.results, runner, log=lambda _: None)
        self.assertEqual([l["status"] for l in lines], ["verified", "unsatisfied", "timeout", "failed"])
        recorded = [json.loads(l) for l in self.results.read_text().splitlines()]
        self.assertEqual(len(recorded), 4)
        self.assertEqual(set(recorded[0]), {"condition", "id", "seed", "rc", "secs", "workdir", "status",
                                            "mode", "with_l1", "verification", "agent_args"})
        self.assertIsNone(recorded[2]["rc"])
        # Second invocation: everything is recorded, nothing runs again.
        again = FakeRunner({})
        self.assertEqual(br.run_benchmark(self.plan(), self.results, again, log=lambda _: None), [])
        self.assertEqual(again.calls, [])
        # A new seed only runs the missing ones.
        more = br.plan_runs(REQUESTS, "base", [0, 1, 2], self.out)
        br.run_benchmark(more, self.results, again, log=lambda _: None)
        self.assertEqual(again.calls, [("base", "A", 2), ("base", "B", 2)])

    def test_unrecorded_attempt_is_started_clean_and_torn_lines_ignored(self):
        spec = self.plan()[0]
        spec.workdir.mkdir(parents=True)
        (spec.workdir / "stale.txt").write_text("old")
        self.results.write_text('{"condition": "base", "id": "A", "seed": 1, "status": "verified"}\n{"cond')
        runner = FakeRunner({})
        br.run_benchmark(self.plan(ids=["A"]), self.results, runner, log=lambda _: None)
        self.assertEqual(runner.calls, [("base", "A", 0)])
        self.assertFalse((spec.workdir / "stale.txt").exists())
        self.assertIn(("base", "A", 0), br.recorded_runs(self.results))

    def test_status_prefers_the_agents_outcome(self):
        self.assertEqual(br.run_status(br.RunResult(0, 1), {"outcome": "unsatisfied"}), "unsatisfied")
        self.assertEqual(br.run_status(br.RunResult(3, 1), None), "unsatisfied")
        # exit 2 without a design.json is argparse rejecting the command line, not a failed design
        self.assertEqual(br.run_status(br.RunResult(2, 1), None), "usage_error")
        self.assertEqual(br.run_status(br.RunResult(None, 1), {"outcome": "verified"}), "timeout")
        self.assertEqual(br.run_status(br.RunResult(9, 1), None), "rc9")

    def test_benchmark_files_are_well_formed(self):
        for name in ("dev.json", "heldout.json"):
            reqs = br.load_requests(Path(__file__).parent / "benchmarks" / name)
            for r in reqs:
                self.assertTrue(r["request"] and r["l1"], r["id"])
                for req in r["l1"]:
                    self.assertEqual(set(req), {"id", "text", "method"}, r["id"])
        dev = br.load_requests(Path(__file__).parent / "benchmarks" / "dev.json")
        held = br.load_requests(Path(__file__).parent / "benchmarks" / "heldout.json")
        self.assertFalse({r["request"] for r in dev} & {r["request"] for r in held})
        self.assertFalse({r["id"] for r in dev} & {r["id"] for r in held})


if __name__ == "__main__":
    unittest.main(verbosity=2)
