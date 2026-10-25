"""Tests for --mode assembly (milestone M0): CLI wiring, the stub tree and design.json.

No Ollama: OllamaAgent is replaced by a scripted fake that fails the test if any
stage asks it a question (M0's stages are pure Python).
"""

import json
import shutil
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

import cad_agent as ca
from test_cad_agent import ScriptedLLM

REPO = Path(__file__).parent
PARTS = REPO / "benchmarks" / "enclosure" / "parts"
L1 = [{"id": "L1.1", "text": "The enclosure shall have a base and a lid.", "method": "inspection"}]


def fake_agent_factory(*args, **kwargs):
    return ScriptedLLM({})       # any LLM call raises: M0 must not ask the model anything


class TestAssemblyCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.l1 = self.root / "l1.json"
        self.l1.write_text(json.dumps(L1))
        self.parts = self.root / "parts"
        self.parts.mkdir()
        for pid in ("rpi_pico2", "plug_microusb_b", "header_male_2p54", "header_female_2p54"):
            shutil.copytree(PARTS / pid, self.parts / pid)
        bad = json.loads((PARTS / "rpi_pico2" / "part.json").read_text())
        bad["id"] = "bad_scaled_module"
        for g in bad["geometry"]:
            g["size"] = [f"({s}) * 25.4" for s in g["size"]]
        (self.parts / "bad_scaled_module").mkdir()
        (self.parts / "bad_scaled_module" / "part.json").write_text(json.dumps(bad))

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *argv):
        with mock.patch.object(ca, "OllamaAgent", fake_agent_factory):
            return ca.main(list(argv))

    def design_record(self, out: Path) -> dict:
        found = sorted(out.glob("*/design.json"))
        self.assertTrue(found, "design.json was not written")
        return json.loads(found[-1].read_text())

    def test_mode_choices(self):
        for mode in ("assembly", "enclosure"):
            with self.subTest(mode=mode):
                with mock.patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
                    self.run_main("--mode", mode, "--out", str(self.root / "o"), "a box")
                self.assertEqual(cm.exception.code, ca.EXIT_USAGE)

    def test_stub_exit(self):
        out = self.root / "out"
        rc = self.run_main("--mode", "assembly", "--auto", "--l1", str(self.l1), "--parts", str(self.parts),
                           "--out", str(out), "an enclosure")
        self.assertEqual(rc, ca.EXIT_FAILED)
        rec = self.design_record(out)
        self.assertEqual(rec["outcome"], "failed")
        assy = rec["assembly"]
        self.assertEqual(assy["stage"], "parse_spec")
        self.assertIn("not implemented: parse_spec", assy["notes"])
        # the gate dropped the inch-scaled copy and said why; the good parts were kept
        self.assertNotIn("bad_scaled_module", assy["catalog"])
        self.assertIn("rpi_pico2", assy["catalog"])
        self.assertTrue(any("bad_scaled_module" in n and "R1" in n for n in assy["notes"]), assy["notes"])
        self.assertIn("fn", assy["rules"])
        self.assertFalse(assy["with_models"])

    def test_enclosure_alias_runs_assembly(self):
        out = self.root / "out2"
        rc = self.run_main("--mode", "enclosure", "--auto", "--l1", str(self.l1), "--parts", str(self.parts),
                           "--with-models", "--out", str(out), "an enclosure")
        self.assertEqual(rc, ca.EXIT_FAILED)
        rec = self.design_record(out)
        self.assertEqual(rec["assembly"]["stage"], "parse_spec")
        self.assertTrue(rec["assembly"]["with_models"])

    def test_missing_catalogue_fails_at_load(self):
        out = self.root / "out3"
        rc = self.run_main("--mode", "assembly", "--auto", "--l1", str(self.l1), "--parts",
                           str(self.root / "nowhere"), "--out", str(out), "an enclosure")
        self.assertEqual(rc, ca.EXIT_FAILED)
        self.assertEqual(self.design_record(out)["assembly"]["stage"], "load_catalog")

    def test_missing_rules_fail_at_load(self):
        out = self.root / "out4"
        rc = self.run_main("--mode", "assembly", "--auto", "--l1", str(self.l1), "--parts", str(self.parts),
                           "--rules", str(self.root / "none.json"), "--out", str(out), "an enclosure")
        self.assertEqual(rc, ca.EXIT_FAILED)
        self.assertEqual(self.design_record(out)["assembly"]["stage"], "load_rules")

    def test_design_has_no_assembly_record_in_other_modes(self):
        d = ca.Design(request="x", workdir=self.root / "w")
        self.assertNotIn("assembly", json.loads(ca.write_design_json(d, "failed").read_text()))


if __name__ == "__main__":
    unittest.main()
