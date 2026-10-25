"""Tests for the generalization loop's Run-step tooling (benchmarks/generalize/run_suite.py, cache_verdicts.py)
and for the repeatable --parts catalogue option it relies on. No Ollama: cad_agent.py is replaced by a fake
script inside a temporary repo tree, and nothing under benchmarks/generalize/holdout is read."""

import hashlib
import json
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).parent
sys.path.insert(0, str(REPO / "benchmarks" / "generalize"))

import cache_verdicts as cv  # noqa: E402
import run_suite as rs  # noqa: E402

ENCL_PARTS = REPO / "benchmarks" / "enclosure" / "parts"

FAKE_AGENT = textwrap.dedent('''
    import json, sys, time
    from pathlib import Path
    argv = sys.argv[1:]
    out = Path(argv[argv.index("--out") + 1])
    seed = argv[argv.index("--seed") + 1]
    request = argv[-1]
    if "SLEEP" in request:
        time.sleep(60)
    if "NOPKG" in request:
        print("not implemented: parse_spec")
        sys.exit(1)
    stub = "--controller" in argv and argv[argv.index("--controller") + 1] == "stub"
    if stub and "STUBFAIL" in request:
        print("contents: nothing to design around")
        sys.exit(1)
    pkg = out / time.strftime("%Y%m%d-%H%M%S")
    (pkg / "views").mkdir(parents=True, exist_ok=True)
    body = ("STUB" if stub else "") + ("WIDE" if "WIDE" in request else "BOX")
    (pkg / "base.stl").write_text("solid base " + body + "\\nendsolid\\n")
    (pkg / "lid.stl").write_text("solid lid\\nendsolid\\n")
    if "NORENDER" not in request:
        (pkg / "views" / "model_iso.png").write_bytes(b"png" + seed.encode())
    for f in ("layout.json", "self_report.json"):
        (pkg / f).write_text("{}")
    (pkg / "design.json").write_text(json.dumps({"outcome": "verified", "assembly": {"stage": "write_package",
                                                 "notes": ["done"]}}))
    print("parts", [argv[i + 1] for i, a in enumerate(argv) if a == "--parts"])
''')


def request_json(rid, text):
    return {"requests": [{"id": rid, "request": text, "l1": [{"id": "L1.1", "text": "shall hold", "method": "inspection"}]}]}


class Tree:
    """A throwaway repo: two train designs, the enclosure regression files, two catalogues and a fake agent."""

    def __init__(self, root: Path):
        self.root = root
        g = root / "benchmarks" / "generalize"
        e = root / "benchmarks" / "enclosure"
        for gid, text in (("G90", "a box"), ("G91", "a WIDE bracket")):
            d = g / "designs" / gid
            d.mkdir(parents=True)
            (d / "design.json").write_text(json.dumps(request_json(gid, text)))
            (d / "requirements.md").write_text(f"# {gid} requirements\n")
        (g / "designs" / "notes").mkdir()                       # a folder without design.json is not a design
        (g / "rubric.md").write_text("# rubric\n")
        (g / "parts" / "gpart").mkdir(parents=True)
        (g / "parts" / "gpart" / "part.json").write_text('{"id": "gpart"}')
        e.mkdir(parents=True)
        (e / "enclosure.json").write_text(json.dumps(request_json("E1-01", "an enclosure")))
        (e / "variants.json").write_text(json.dumps({"requests": [
            request_json(v, f"variant {v}")["requests"][0] for v in ("V1", "V2", "V3", "V4")]}))
        (e / "requirements.md").write_text("# enclosure requirements\n")
        (e / "rubric.md").write_text("# enclosure rubric\n")
        (e / "parts" / "epart").mkdir(parents=True)
        (e / "parts" / "epart" / "part.json").write_text('{"id": "epart"}')
        (root / "design_rules.json").write_text('{"rules": {}}')
        (root / "cad_agent.py").write_text(FAKE_AGENT)
        (root / "assembly.py").write_text("# agent module\n")
        (root / "test_assembly.py").write_text("# a test, not part of the agent version\n")
        self.paths = rs.Paths(root)

    def make_package(self, run_dir: Path, stls: dict, renders: bool = True, stamp: str = "20260101-000000") -> Path:
        pkg = run_dir / stamp
        (pkg / "views").mkdir(parents=True)
        for name, data in stls.items():
            (pkg / name).write_bytes(data)
        if renders:
            (pkg / "views" / "model_iso.png").write_bytes(b"png")
        return pkg


class TreeCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tree = Tree(Path(self.tmp.name))
        self.paths = self.tree.paths

    def tearDown(self):
        self.tmp.cleanup()


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


class TestHashes(TreeCase):
    def test_spec_hash_tracks_every_file_its_order_and_a_missing_file(self):
        a, b, c = (self.tree.root / n for n in ("a.md", "b.json", "c.md"))
        a.write_text("req")
        b.write_text("design")
        c.write_text("rubric")
        h = rs.spec_sha1([a, b, c])
        self.assertEqual(h, rs.spec_sha1([a, b, c]))
        self.assertNotEqual(h, rs.spec_sha1([b, a, c]))
        c.write_text("rubric v2")
        self.assertNotEqual(h, rs.spec_sha1([a, b, c]))
        # bytes moved across a file boundary give a different hash
        a.write_text("re")
        b.write_text("qdesign")
        c.write_text("rubric")
        self.assertNotEqual(h, rs.spec_sha1([a, b, c]))
        missing = rs.spec_sha1([a, b, self.tree.root / "nope.md"])
        empty = self.tree.root / "empty.md"
        empty.write_text("")
        self.assertNotEqual(missing, rs.spec_sha1([a, b, empty]))

    def test_geometry_hash_is_over_sorted_stl_files_only(self):
        r = self.tree.root
        p1 = self.tree.make_package(r / "one", {"lid.stl": b"L", "base.stl": b"B"})
        p2 = self.tree.make_package(r / "two", {"base.stl": b"B", "lid.stl": b"L"}, renders=False)
        (p2 / "design.json").write_text("{}")                  # non-STL files do not count
        self.assertEqual(rs.geometry_sha1(p1), rs.geometry_sha1(p2))
        expect = hashlib.sha1(b"base.stl\x001:B" + b"lid.stl\x001:L").hexdigest()
        self.assertEqual(rs.geometry_sha1(p1), expect)
        p3 = self.tree.make_package(r / "three", {"base.stl": b"L", "lid.stl": b"B"})   # swapped bodies
        self.assertNotEqual(rs.geometry_sha1(p1), rs.geometry_sha1(p3))
        p4 = self.tree.make_package(r / "four", {"base.stl": b"B", "lid.stl": b"L2"})
        self.assertNotEqual(rs.geometry_sha1(p1), rs.geometry_sha1(p4))
        self.assertIsNone(rs.geometry_sha1(self.tree.make_package(r / "five", {})))
        self.assertIsNone(rs.geometry_sha1(None))

    def test_geometry_hash_is_order_free(self):
        # generalize delta 002 T14 (C3, P-2): the same triangles in another facet order (and in the other STL format, with
        # sub-1e-4 mm noise) give the same geometry_sha1; a moved vertex or a flipped winding does not
        import struct
        tris = [((0, 0, 0), (10, 0, 0), (0, 10, 0)), ((0, 0, 5), (0, 10, 5), (10, 0, 5)),
                ((10, 0, 0), (10, 10, 0), (0, 10, 0)), ((0, 0, 0), (0, 0, 5), (10, 0, 5))]

        def ascii_stl(ts):
            return ("solid s\n" + "".join("facet normal 0 0 0\nouter loop\n" + "".join(
                f"vertex {x:.6f} {y:.6f} {z:.6f}\n" for x, y, z in t) + "endloop\nendfacet\n" for t in ts)
                + "endsolid s\n").encode()

        def binary_stl(ts):
            out = b"\0" * 80 + struct.pack("<I", len(ts))
            for t in ts:
                out += struct.pack("<12fH", 0, 0, 0, *[c for v in t for c in v], 0)
            return out

        r = self.tree.root
        lid = ascii_stl(tris[:1])
        p1 = self.tree.make_package(r / "a", {"base.stl": ascii_stl(tris), "lid.stl": lid})
        permuted = [tris[2], (tris[0][1], tris[0][2], tris[0][0]), tris[3], tris[1]]   # facet order + vertex rotation
        p2 = self.tree.make_package(r / "b", {"base.stl": ascii_stl(permuted), "lid.stl": lid})
        noisy = [tuple(tuple(c + 2e-6 for c in v) for v in t) for t in reversed(tris)]
        p3 = self.tree.make_package(r / "c", {"base.stl": binary_stl(noisy), "lid.stl": lid})
        self.assertNotEqual(ascii_stl(tris), ascii_stl(permuted))
        self.assertEqual(rs.geometry_sha1(p1), rs.geometry_sha1(p2))
        self.assertEqual(rs.geometry_sha1(p1), rs.geometry_sha1(p3))
        moved = [tris[0], tris[1], tris[2], ((0, 0, 0), (0, 0, 5), (10, 0, 6))]
        p4 = self.tree.make_package(r / "d", {"base.stl": ascii_stl(moved), "lid.stl": lid})
        flipped = [tris[0], tris[1], tris[2], (tris[3][0], tris[3][2], tris[3][1])]
        p5 = self.tree.make_package(r / "e", {"base.stl": ascii_stl(flipped), "lid.stl": lid})
        p6 = self.tree.make_package(r / "f", {"lid.stl": ascii_stl(tris), "base.stl": lid})     # swapped bodies
        for p in (p4, p5, p6):
            self.assertNotEqual(rs.geometry_sha1(p1), rs.geometry_sha1(p))

    def test_code_listing_covers_modules_rules_and_both_catalogues(self):
        info = rs.write_code_sha1(self.paths, "train", "001")
        listing = (self.paths.iter_dir("train", "001") / "code_sha1.txt").read_text()
        names = [line.split("  ", 1)[1] for line in listing.splitlines()]
        self.assertEqual(names, ["assembly.py", "cad_agent.py", "design_rules.json",
                                 "benchmarks/enclosure/parts/epart/part.json",
                                 "benchmarks/generalize/parts/gpart/part.json"])
        for line in listing.splitlines():                       # shasum -c format
            sha, rel = line.split("  ", 1)
            self.assertEqual(sha, rs.sha1_file(self.tree.root / rel))
        self.assertIsNone(info["code_unchanged"])
        self.assertIsNone(info["previous_iter"])
        self.assertTrue(rs.write_code_sha1(self.paths, "train", "002")["code_unchanged"])
        (self.tree.root / "benchmarks/enclosure/parts/epart/part.json").write_text('{"id": "epart", "x": 1}')
        info3 = rs.write_code_sha1(self.paths, "train", "003")
        self.assertEqual(info3["previous_iter"], "iter_002")
        self.assertFalse(info3["code_unchanged"])
        # re-writing 003 after another change flags a mixed-version iteration
        (self.tree.root / "assembly.py").write_text("# changed\n")
        self.assertTrue(rs.write_code_sha1(self.paths, "train", "003")["changed_within_iteration"])

    def test_holdout_code_is_compared_with_the_train_iteration(self):
        rs.write_code_sha1(self.paths, "train", "004")
        info = rs.write_code_sha1(self.paths, "holdout", "004")
        self.assertTrue(info["matches_train_iter"])
        self.assertTrue((self.paths.loop / "holdout_results" / "iter_004" / "code_sha1.txt").is_file())


# ---------------------------------------------------------------------------
# Judge cache
# ---------------------------------------------------------------------------


class TestCache(TreeCase):
    def test_store_and_lookup_need_the_same_id_geometry_and_spec(self):
        cache = rs.load_cache(self.paths.cache_path("train"))
        self.assertEqual(cache["entries"], {})
        v = {"verdict": "MEETS", "class": "CORRECT"}
        rs.cache_store(cache, "G90", "g1", "s1", v, iter="001", run="G90_s1")
        rs.save_json(self.paths.cache_path("train"), cache)
        cache = rs.load_cache(self.paths.cache_path("train"))
        self.assertEqual(rs.cache_lookup(cache, "G90", "g1", "s1"), v)
        self.assertIsNone(rs.cache_lookup(cache, "G90", "g2", "s1"))
        self.assertIsNone(rs.cache_lookup(cache, "G90", "g1", "s2"))
        self.assertIsNone(rs.cache_lookup(cache, "G91", "g1", "s1"))
        self.assertIsNone(rs.cache_lookup(cache, "G90", None, "s1"))
        with self.assertRaises(ValueError):
            rs.cache_store(cache, "G90", None, "s1", v)

    def test_a_malformed_cache_is_an_error_not_an_empty_cache(self):
        path = self.paths.cache_path("train")
        path.parent.mkdir(parents=True)
        path.write_text('{"G90": "MEETS"}')
        with self.assertRaises(ValueError):
            rs.load_cache(path)

    def test_holdout_has_its_own_cache_and_iteration_folder(self):
        self.assertEqual(self.paths.cache_path("train"), self.paths.loop / "judge_cache.json")
        self.assertEqual(self.paths.cache_path("regression"), self.paths.loop / "judge_cache.json")
        self.assertEqual(self.paths.cache_path("holdout"), self.paths.loop / "holdout_results" / "judge_cache.json")
        self.assertEqual(self.paths.iter_dir("holdout", "007"), self.paths.loop / "holdout_results" / "iter_007")
        self.assertEqual(self.paths.iter_dir("regression", "007"), self.paths.loop / "iter_007")


# ---------------------------------------------------------------------------
# Cases, runs, summary
# ---------------------------------------------------------------------------


class TestCases(TreeCase):
    def test_train_and_regression_cases(self):
        train = rs.load_cases(self.paths, "train")
        self.assertEqual([c.id for c in train], ["G90", "G91"])
        g = self.paths.generalize
        self.assertEqual(train[0].spec_files, [g / "designs/G90/requirements.md", g / "designs/G90/design.json",
                                               g / "rubric.md"])
        reg = rs.load_cases(self.paths, "regression")
        self.assertEqual([c.id for c in reg], list(rs.REGRESSION_IDS))   # V4 is not in the regression set
        self.assertEqual(reg[1].spec_files[1], self.paths.enclosure / "variants.json")
        self.assertEqual(self.paths.catalogues("regression"), [self.paths.enclosure / "parts"])
        self.assertEqual(self.paths.catalogues("train"), [g / "parts", self.paths.enclosure / "parts"])
        with self.assertRaises(ValueError):
            rs.load_cases(self.paths, "train", ["G99"])
        with self.assertRaises(ValueError):
            rs.load_cases(self.paths, "regression", ["V4"])

    def test_iteration_labels(self):
        self.assertEqual(rs.iter_label("7"), "007")
        self.assertEqual(rs.iter_label(12), "012")
        with self.assertRaises(ValueError):
            rs.iter_label("x1")


class TestRunAndSummary(TreeCase):
    def run_cases(self, split="train", ids=(), seed=1, timeout=60.0, nnn="001"):
        code = rs.write_code_sha1(self.paths, split, nnn)
        rows = [rs.run_case(self.paths, c, seed, nnn, python=sys.executable, timeout_s=timeout,
                            catalogues=self.paths.catalogues(split), code_sha1=code["code_sha1"])
                for c in rs.load_cases(self.paths, split, ids)]
        return rows, rs.build_summary(self.paths, split, nnn, code_info=code)

    def test_runs_write_rows_hashes_and_a_to_judge_list(self):
        rows, s = self.run_cases()
        d = self.paths.iter_dir("train", "001")
        self.assertEqual([r["name"] for r in rows], ["G90_s1", "G91_s1"])
        for r in rows:
            self.assertEqual(r["rc"], 0)
            self.assertTrue(r["has_renders"])
            self.assertEqual(r["missing"], [])
            self.assertEqual(r["stl_files"], ["base.stl", "lid.stl"])
            self.assertEqual(r["outcome"], "verified")
            pkg = self.tree.root / r["package"]
            self.assertEqual(r["geometry_sha1"], rs.geometry_sha1(pkg))
            self.assertTrue((d / r["name"] / "run.log").is_file())
            self.assertTrue((d / "inputs" / f"{r['id']}.request.txt").is_file())
        self.assertNotEqual(rows[0]["geometry_sha1"], rows[1]["geometry_sha1"])
        log = (d / "G90_s1" / "run.log").read_text()
        self.assertIn("benchmarks/generalize/parts", log)        # both catalogues reached the agent, in order
        self.assertLess(log.index("generalize/parts"), log.index("enclosure/parts"))
        self.assertEqual(len((d / "runs.jsonl").read_text().splitlines()), 2)
        self.assertEqual(s["to_judge"], ["G90_s1", "G91_s1"])
        self.assertEqual(s["cached"], [])
        self.assertEqual(s["counts"]["train"]["runs"], 2)
        self.assertEqual(s["counts"]["train"]["no_output"], 0)
        self.assertTrue(s["runs_on_one_code_version"])
        self.assertEqual(json.loads((d / "summary.json").read_text())["to_judge"], ["G90_s1", "G91_s1"])

    def test_a_cached_verdict_is_reused_for_the_same_geometry_and_spec_only(self):
        rows, _ = self.run_cases()
        verdicts = {"G90_s1": {"verdict": "MEETS", "class": "CORRECT", "score": 1.0},
                    "G91_s1": {"verdict": "DNM", "class": "MINOR"}}
        res = cv.store_verdicts(self.paths, "001", cv.parse_verdicts(verdicts))
        self.assertEqual(res["stored"], ["G90_s1", "G91_s1"])
        s = res["summary"]
        self.assertEqual(s["to_judge"], [])
        self.assertEqual(s["counts"]["train"]["meets"], 1)
        self.assertEqual(s["counts"]["train"]["correct"], 1)
        # the next iteration, same code and same geometry: both verdicts are reused
        _, s2 = self.run_cases(seed=2, nnn="002")
        self.assertEqual(s2["to_judge"], [])
        self.assertEqual([c["name"] for c in s2["cached"]], ["G90_s2", "G91_s2"])
        self.assertTrue(s2["code"]["code_unchanged"])
        # a rubric edit invalidates every cached verdict of the suite
        (self.paths.rubric).write_text("# rubric v2\n")
        s3 = rs.build_summary(self.paths, "train", "002")
        self.assertEqual(s3["to_judge"], ["G90_s2", "G91_s2"])
        self.assertTrue(all(r["spec_changed_since_run"] for r in s3["runs"]))
        self.assertTrue(s3["code"]["code_unchanged"])            # a rebuild keeps the Run's code comparison
        # a design.json edit invalidates that design only
        (self.paths.rubric).write_text("# rubric\n")
        dj = self.paths.designs / "G91" / "design.json"
        dj.write_text(dj.read_text() + "\n")
        s4 = rs.build_summary(self.paths, "train", "002")
        self.assertEqual(s4["to_judge"], ["G91_s2"])

    def test_no_package_and_no_renders_are_never_sent_to_the_judge(self):
        dj = self.paths.designs / "G90" / "design.json"
        dj.write_text(json.dumps(request_json("G90", "a box NOPKG")))
        dj1 = self.paths.designs / "G91" / "design.json"
        dj1.write_text(json.dumps(request_json("G91", "a box NORENDER")))
        rows, s = self.run_cases()
        self.assertEqual(rows[0]["rc"], 1)
        self.assertIsNone(rows[0]["package"])
        self.assertIsNone(rows[0]["geometry_sha1"])
        self.assertEqual(rows[0]["missing"], list(rs.PACKAGE_NEED["train"]))
        self.assertFalse(rows[1]["has_renders"])
        self.assertIsNotNone(rows[1]["geometry_sha1"])
        self.assertEqual(s["to_judge"], [])
        self.assertEqual(s["counts"]["train"]["no_output"], 1)
        self.assertEqual({r["name"]: r["cache"] for r in s["runs"]}, {"G90_s1": "no_package", "G91_s1": "no_package"})
        res = cv.store_verdicts(self.paths, "001", [("G90_s1", {"verdict": "DNM", "class": "WRONG"})])
        self.assertEqual(res["stored"], [])
        self.assertEqual(res["skipped"][0]["reason"], "the run has no STL package")

    def test_a_rerun_replaces_its_row_and_uses_only_its_own_package(self):
        self.run_cases(ids=["G90"])
        dj = self.paths.designs / "G90" / "design.json"
        dj.write_text(json.dumps(request_json("G90", "a box NOPKG")))
        rows, s = self.run_cases(ids=["G90"])
        self.assertIsNone(rows[0]["package"])                    # the first run's package is not reused
        self.assertEqual(len(s["runs"]), 1)
        self.assertEqual(s["runs"][0]["rc"], 1)

    def test_the_timeout_kills_the_run(self):
        dj = self.paths.designs / "G90" / "design.json"
        dj.write_text(json.dumps(request_json("G90", "a box SLEEP")))
        with mock.patch.object(rs, "KILL_GRACE_S", 5):
            rows, s = self.run_cases(ids=["G90"], timeout=1.0)
        self.assertEqual(rows[0]["rc"], rs.TIMEOUT_RC)
        self.assertTrue(rows[0]["timed_out"])
        self.assertLess(rows[0]["secs"], 30)
        self.assertEqual(s["counts"]["train"]["timed_out"], 1)

    def test_regression_runs_with_the_enclosure_catalogue_and_reports_a_status(self):
        rows, s = self.run_cases(split="regression")
        self.assertEqual([r["id"] for r in rows], list(rs.REGRESSION_IDS))
        self.assertEqual(rows[0]["catalogues"], ["benchmarks/enclosure/parts"])
        log = (self.paths.iter_dir("regression", "001") / "E1-01_s1" / "run.log").read_text()
        self.assertNotIn("generalize/parts", log)
        self.assertEqual(s["regression"], "pending")
        good = {"E1-01_s1": {"verdict": "MEETS", "class": "CORRECT"}}
        good.update({f"{v}_s1": {"verdict": "DNM", "class": "CORRECT"} for v in ("V1", "V2", "V3")})
        self.assertEqual(cv.store_verdicts(self.paths, "001", cv.parse_verdicts(good))["summary"]["regression"], "pass")
        bad = {"E1-01_s1": {"verdict": "DNM", "class": "CORRECT"}}
        self.assertEqual(cv.store_verdicts(self.paths, "001", cv.parse_verdicts(bad))["summary"]["regression"], "fail")

    def test_holdout_score_needs_every_run_judged(self):
        d = self.paths.iter_dir("holdout", "001")
        d.mkdir(parents=True)
        rows = []
        for i, cls in enumerate(("CORRECT", "WRONG")):
            pkg = self.tree.make_package(d / f"H{i}_s1", {"base.stl": bytes([i])})
            rows.append({"name": f"H{i}_s1", "id": f"H{i}", "split": "holdout", "seed": 1, "rc": 0,
                         "package": self.paths.rel(pkg), "has_renders": True, "geometry_sha1": rs.geometry_sha1(pkg),
                         "spec_files": ["benchmarks/generalize/rubric.md"]})
        (d / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        s = rs.build_summary(self.paths, "holdout", "001")
        self.assertIsNone(s["holdout_score"])
        res = cv.store_verdicts(self.paths, "001", [("H0", {"class": "CORRECT"}), ("H1", {"class": "WRONG"})],
                                holdout=True)
        self.assertEqual(res["summary"]["holdout_score"], 0.5)
        self.assertTrue(self.paths.cache_path("holdout").is_file())
        self.assertFalse(self.paths.cache_path("train").exists())   # held-out verdicts never reach the train cache


class TestCli(TreeCase):
    def test_dry_run_and_summarize_need_no_ollama(self):
        with mock.patch("sys.stdout"):
            self.assertEqual(rs.main(["--iter", "5", "--seed", "3", "--dry-run", "G90"], paths=self.paths), 0)
            self.assertEqual(rs.main(["--iter", "5", "--summarize"], paths=self.paths), 0)
        self.assertTrue((self.paths.iter_dir("train", "005") / "summary.json").is_file())
        self.assertFalse((self.paths.iter_dir("train", "005") / "G90_s3").exists())

    def test_a_full_cli_run_with_preflight_skipped(self):
        with mock.patch("sys.stdout"):
            rc = rs.main(["--iter", "6", "--seed", "1", "--no-preflight", "--python", sys.executable, "G91"],
                         paths=self.paths)
        self.assertEqual(rc, 0)
        s = json.loads((self.paths.iter_dir("train", "006") / "summary.json").read_text())
        self.assertEqual(s["to_judge"], ["G91_s1"])
        self.assertIsNone(s["code"]["code_unchanged"])
        verdicts = self.tree.root / "v.json"
        verdicts.write_text(json.dumps([{"name": "G91_s1", "verdict": {"verdict": "MEETS"}}]))
        with mock.patch("sys.stdout"):
            self.assertEqual(cv.main(["6", str(verdicts)], paths=self.paths), 0)
        s = json.loads((self.paths.iter_dir("train", "006") / "summary.json").read_text())
        self.assertEqual([c["name"] for c in s["cached"]], ["G91_s1"])

    def test_bad_verdict_files_are_rejected(self):
        for bad in ({"G90_s1": "MEETS"}, [{"name": "G90_s1"}], "MEETS", {"G90_s1": {"score": 1}}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                cv.parse_verdicts(bad)
        self.assertEqual(cv.parse_verdicts({"verdicts": [{"name": "a", "verdict": {"class": "WRONG"}}]}),
                         [("a", {"class": "WRONG"})])


class TestParaphrase(TreeCase):
    """Owner decision D1 (migration delta R01): --paraphrase K runs entry K of each design's paraphrases.json (same numbers
    and meaning, other words); the paraphrase is in runs.jsonl, summary.json and the judge-cache key."""

    def write_paraphrases(self, gid: str, texts):
        d = self.paths.designs / gid
        entries = [dict(request_json(gid, t)["requests"][0], tier=1, title=gid) for t in texts]
        (d / rs.PARAPHRASES).write_text(json.dumps({"paraphrases": entries}))

    def run_one(self, gid, paraphrase, seed=1, nnn="001", controller="llm"):
        code = rs.write_code_sha1(self.paths, "train", nnn)
        (case,) = rs.load_cases(self.paths, "train", [gid], paraphrase=paraphrase)
        row = rs.run_case(self.paths, case, seed, nnn, python=sys.executable, timeout_s=60.0,
                          catalogues=self.paths.catalogues("train"), code_sha1=code["code_sha1"], controller=controller)
        return row, rs.build_summary(self.paths, "train", nnn, code_info=code)

    def test_cases_take_the_paraphrase_entry(self):
        self.write_paraphrases("G90", ["a box, said again", "a box, in a third wording"])
        (c0,) = rs.load_cases(self.paths, "train", ["G90"])
        (c2,) = rs.load_cases(self.paths, "train", ["G90"], paraphrase=2)
        self.assertEqual((c0.request, c0.paraphrase), ("a box", 0))
        self.assertEqual((c2.request, c2.paraphrase), ("a box, in a third wording", 2))
        self.assertEqual(c2.spec_files, c0.spec_files)            # the judge still grades against the same files
        with self.assertRaises(ValueError):                       # a train design without the entry is an error
            rs.load_cases(self.paths, "train", ["G91"], paraphrase=1)
        with self.assertRaises(ValueError):
            rs.load_cases(self.paths, "train", ["G90"], paraphrase=3)
        reg = rs.load_cases(self.paths, "regression", paraphrase=2)
        self.assertTrue(all(c.paraphrase == 0 for c in reg))      # the regression set has no paraphrases

    def test_holdout_without_paraphrases_falls_back_quietly(self):
        h = self.paths.holdout / "H1"
        h.mkdir(parents=True)
        (h / "design.json").write_text(json.dumps(request_json("H1", "a hidden box")))
        (case,) = rs.load_cases(self.paths, "holdout", paraphrase=1)
        self.assertEqual((case.request, case.paraphrase, case.paraphrase_requested), ("a hidden box", 0, 1))

    def test_runs_record_the_paraphrase_and_key_the_cache(self):
        self.write_paraphrases("G90", ["a box, said again", "a box, in a third wording"])
        row, s = self.run_one("G90", 1)
        d = self.paths.iter_dir("train", "001")
        self.assertEqual((row["paraphrase"], row["controller"]), (1, "llm"))
        self.assertEqual((d / "inputs" / "G90.p1.request.txt").read_text(), "a box, said again")
        self.assertEqual(s["paraphrase"], 1)
        res = cv.store_verdicts(self.paths, "001", [("G90_s1", {"verdict": "MEETS", "class": "CORRECT"})])
        self.assertEqual(res["stored"], ["G90_s1"])
        keys = list(rs.load_cache(self.paths.cache_path("train"))["entries"])
        self.assertEqual(len(keys), 1)
        self.assertTrue(keys[0].endswith("|p1"), keys)
        # the same geometry on the original wording is not a cache hit: MEETS is measured per wording
        _, s0 = self.run_one("G90", 0, seed=2, nnn="002")
        self.assertEqual(s0["to_judge"], ["G90_s2"])
        self.assertEqual(s0["paraphrase"], 0)
        self.assertEqual(rs.cache_key("G90", "g", "s"), "G90|g|s")          # paraphrase 0 keeps the pre-R01 key
        self.assertEqual(rs.cache_key("G90", "g", "s", 2), "G90|g|s|p2")


class TestStubRuns(TreeCase):
    """Owner decision D1 (migration delta R01): --controller stub is the authority probe. Its rows are <id>_sS_stub, never
    judged, and give summary.json stub_verified and llm_dependent."""

    def run_all(self, controller, seed=1, nnn="001"):
        code = rs.write_code_sha1(self.paths, "train", nnn)
        rows = [rs.run_case(self.paths, c, seed, nnn, python=sys.executable, timeout_s=60.0,
                            catalogues=self.paths.catalogues("train"), code_sha1=code["code_sha1"], controller=controller)
                for c in rs.load_cases(self.paths, "train")]
        return rows, rs.build_summary(self.paths, "train", nnn, code_info=code)

    def test_stub_rows_are_named_apart_and_never_judged(self):
        (c,) = rs.load_cases(self.paths, "train", ["G90"])
        dry = rs.run_case(self.paths, c, 4, "001", python=sys.executable, timeout_s=60.0,
                          catalogues=self.paths.catalogues("train"), code_sha1="", dry_run=True, controller="stub")
        self.assertEqual(dry["name"], "G90_s4_stub")
        self.assertEqual(dry["cmd"][dry["cmd"].index("--controller") + 1], "stub")
        self.run_all("llm")
        rows, s = self.run_all("stub")
        self.assertEqual([r["name"] for r in rows], ["G90_s1_stub", "G91_s1_stub"])
        self.assertEqual(s["to_judge"], ["G90_s1", "G91_s1"])              # only the LLM runs go to the judges
        self.assertEqual(s["counts"]["train"]["runs"], 2)
        self.assertEqual(s["counts"]["train_stub"]["runs"], 2)
        self.assertEqual({r["name"]: r["cache"] for r in s["runs"] if r["controller"] == "stub"},
                         {"G90_s1_stub": "stub", "G91_s1_stub": "stub"})
        res = cv.store_verdicts(self.paths, "001", [("G90_s1_stub", {"verdict": "MEETS"})])
        self.assertEqual(res["stored"], [])
        self.assertIn("never judged", res["skipped"][0]["reason"])
        res = cv.store_verdicts(self.paths, "001", [("G91", {"verdict": "DNM", "class": "WRONG"})])
        self.assertEqual(res["stored"], ["G91_s1"])          # a bare id still names the judged run, not the stub's

    def test_stub_verified_and_llm_dependent(self):
        dj = self.paths.designs / "G91" / "design.json"
        dj.write_text(json.dumps(request_json("G91", "a WIDE bracket STUBFAIL")))
        self.run_all("llm")
        _, s = self.run_all("stub")
        self.assertEqual(s["stub_verified"], 1)                            # G91's stub run stops (rc 1)
        self.assertEqual(s["stub"]["verified"], ["G90"])
        self.assertEqual(s["llm_dependent"], ["G90", "G91"])               # different geometry; geometry vs none
        self.assertEqual(s["stub"]["compared"], 2)
        self.assertEqual(s["stub"]["verified_share"], 0.5)

    def test_stub_preflight_needs_no_ollama(self):
        idle = mock.Mock(stdout="")
        with mock.patch.object(rs.subprocess, "run", return_value=idle), \
                mock.patch.object(rs.urllib.request, "urlopen", side_effect=OSError("no server")):
            self.assertEqual(rs.preflight(need_ollama=False), [])
            self.assertTrue(any("not reachable" in p for p in rs.preflight()))

    def test_same_geometry_is_not_llm_dependent(self):
        rows, _ = self.run_all("llm")
        stub_rows = [dict(r, name=r["name"] + rs.STUB_SUFFIX, controller="stub") for r in rows]
        a = rs.authority_summary(rows, stub_rows)
        self.assertEqual((a["llm_dependent"], a["stub"]["same_geometry"]), ([], ["G90", "G91"]))
        nogeo = [dict(r, geometry_sha1=None) for r in rows]
        self.assertEqual(rs.authority_summary(nogeo, [dict(r, controller="stub") for r in nogeo])["llm_dependent"], [])


class TestLaunchConfig(unittest.TestCase):
    """loop/launch_config.json (migration delta R01): the launcher's commands, each the args after the interpreter with
    placeholders {iter}, {seed} and {para}, parse with run_suite's own command line."""

    def test_commands_parse_and_cover_train_regression_stub_and_holdout(self):
        import string
        cfg = json.loads((REPO / "benchmarks" / "generalize" / "loop" / "launch_config.json").read_text())
        sub = {"iter": "005", "seed": "5", "para": "2"}

        def parsed(cmd):
            fields = {f for _, f, _, _ in string.Formatter().parse(" ".join(cmd)) if f}
            self.assertTrue(fields <= set(sub), fields)
            args = [a.format(**sub) for a in cmd]
            self.assertTrue((REPO / args[0]).is_file(), args[0])
            return rs.build_parser().parse_args(args[1:])

        train, reg, stub = (parsed(c) for c in cfg["commands"])
        self.assertEqual((train.split, train.regression, train.paraphrase, train.controller), ("train", False, 2, "llm"))
        self.assertEqual((reg.regression, reg.paraphrase, reg.controller), (True, 0, "llm"))
        self.assertEqual((stub.split, stub.paraphrase, stub.controller), ("train", 2, "stub"))
        self.assertTrue(train.iter == reg.iter == stub.iter == "005" and train.seed == stub.seed == 5)
        (hold,) = (parsed(c) for c in cfg["holdout_commands"])
        self.assertEqual((hold.split, hold.paraphrase, hold.controller), ("holdout", 2, "llm"))

    def test_code_listing_includes_the_rule_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Tree(Path(tmp))
            (Path(tmp) / "controller_rules.json").write_text('{"rules": {}}')
            names = [rs.Paths(Path(tmp)).rel(p) for p in rs.code_files(tree.paths)]
            self.assertEqual(names[:4], ["assembly.py", "cad_agent.py", "design_rules.json", "controller_rules.json"])


class TestVerdicts(unittest.TestCase):
    """Generalize delta 003 C0 (P-3): the boolean verdict form is accepted and stored normalised."""

    ITER003 = REPO / "benchmarks" / "generalize" / "loop" / "iter_003" / "verdicts.json"

    def test_boolean_meets_form(self):
        # T1: verdict_flags reads {"meets": true}; iteration 003's original verdicts.json (boolean `meets`, no `verdict`
        # string) gives regression `pass`, and parse_verdicts stores the normalised verdict string next to `meets`
        self.assertEqual(rs.verdict_flags({"meets": True, "class": "CORRECT"}), {"meets": True, "correct": True})
        self.assertEqual(rs.verdict_flags({"meets": False, "class": "CORRECT"}), {"meets": False, "correct": True})
        self.assertEqual(rs.verdict_flags({"meets": False, "class": "WRONG"}), {"meets": False, "correct": False})
        self.assertEqual(rs.verdict_flags({"verdict": "MEETS"}), {"meets": True, "correct": True})
        self.assertEqual(cv.parse_verdicts({"a": {"meets": True, "class": "CORRECT"}}),
                         [("a", {"meets": True, "class": "CORRECT", "verdict": "MEETS"})])
        self.assertEqual(cv.parse_verdicts({"a": {"meets": False}}), [("a", {"meets": False, "verdict": "DNM"})])
        with self.assertRaises(ValueError):
            cv.parse_verdicts({"a": {"meets": "yes"}})
        if not self.ITER003.is_file():
            self.skipTest(f"{self.ITER003} is missing")
        rows = []
        for name, v in cv.parse_verdicts(json.loads(self.ITER003.read_text())):
            if name in rs.REGRESSION_IDS:
                rows.append({"id": name, "split": "regression", "geometry_sha1": "x", "verdict": v})
        self.assertEqual(sorted(r["id"] for r in rows), sorted(rs.REGRESSION_IDS))
        self.assertEqual(rs.regression_status(rows), "pass")
        raw = json.loads(self.ITER003.read_text())           # the original rows, not normalised, read directly
        self.assertTrue(all("verdict" not in raw[k] for k in rs.REGRESSION_IDS))
        self.assertEqual(rs.regression_status([{"id": k, "split": "regression", "geometry_sha1": "x", "verdict": raw[k]}
                                               for k in rs.REGRESSION_IDS]), "pass")


# ---------------------------------------------------------------------------
# Several catalogue folders (cad_agent --parts DIR --parts DIR)
# ---------------------------------------------------------------------------


class TestSeveralCatalogues(unittest.TestCase):
    def setUp(self):
        import parts as pt
        self.pt = pt
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.a, self.b = root / "a", root / "b"
        shutil.copytree(ENCL_PARTS / "rpi_pico2", self.a / "rpi_pico2")
        shutil.copytree(ENCL_PARTS / "plug_microusb_b", self.a / "plug_microusb_b")
        shutil.copytree(ENCL_PARTS / "plug_microusb_b", self.b / "plug_microusb_b")     # byte-equal copy
        shutil.copytree(ENCL_PARTS / "header_male_2p54", self.b / "header_male_2p54")
        other = json.loads((ENCL_PARTS / "rpi_pico2" / "part.json").read_text())
        other["names"] = other["names"] + ["another pico"]
        (self.b / "rpi_pico2").mkdir()
        (self.b / "rpi_pico2" / "part.json").write_text(json.dumps(other))           # same id, different data

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_folder_wins_and_only_a_differing_duplicate_is_reported(self):
        cat = self.pt.Catalog.load([self.a, self.b])
        self.assertEqual(cat.ids(), ["header_male_2p54", "plug_microusb_b", "rpi_pico2"])
        self.assertEqual(cat.get("rpi_pico2").path, self.a / "rpi_pico2" / "part.json")
        self.assertEqual(len(cat.errors), 1, cat.errors)
        self.assertIn("duplicate id 'rpi_pico2'", cat.errors[0])
        self.assertEqual(cat.roots, [self.a, self.b])
        self.assertEqual(cat.root, self.a)

    def test_one_folder_behaves_as_before(self):
        cat = self.pt.Catalog.load(self.a)
        self.assertEqual(cat.ids(), ["plug_microusb_b", "rpi_pico2"])
        self.assertEqual(cat.errors, [])
        missing = self.pt.Catalog.load(self.a.parent / "nowhere")
        self.assertEqual(missing.parts, {})
        self.assertTrue(missing.errors[0].endswith("not a directory"))
        partly = self.pt.Catalog.load([self.a.parent / "nowhere", self.a])
        self.assertEqual(partly.ids(), ["plug_microusb_b", "rpi_pico2"])

    def test_cli_passes_every_parts_folder_to_assembly_mode(self):
        import cad_agent as ca
        out = Path(self.tmp.name) / "out"
        l1 = Path(self.tmp.name) / "l1.json"
        l1.write_text(json.dumps([{"id": "L1.1", "text": "shall hold", "method": "inspection"}]))
        nowhere = [str(Path(self.tmp.name) / n) for n in ("x", "y")]
        with mock.patch.object(ca, "OllamaAgent", lambda *a, **k: mock.MagicMock()):
            rc = ca.main(["--mode", "assembly", "--auto", "--l1", str(l1), "--parts", nowhere[0], "--parts",
                          nowhere[1], "--out", str(out), "an enclosure"])
        self.assertEqual(rc, ca.EXIT_FAILED)
        rec = json.loads(sorted(out.glob("*/design.json"))[-1].read_text())["assembly"]
        self.assertEqual(rec["stage"], "load_catalog")
        self.assertEqual(rec["parts_dirs"], nowhere)
        self.assertTrue(all(any(n in note for note in rec["notes"]) for n in nowhere), rec["notes"])


if __name__ == "__main__":
    unittest.main()
