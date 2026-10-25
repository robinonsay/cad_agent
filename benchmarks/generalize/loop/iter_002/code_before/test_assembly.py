"""Tests for --mode assembly: CLI wiring, the controller interface (ParseSpec, Contents, ChooseStack,
ArrangeContents + ConfirmArrangement), DeriveFeatures, the package and an offline end-to-end run.

No Ollama: OllamaAgent is replaced by a scripted fake keyed by question label. Request and L1
texts come from benchmarks/enclosure/enclosure.json and variants.json; expected numbers are
computed in the test from those texts and from part data, never typed into the agent.
"""

import copy
from collections import Counter
import json
import math
import shutil
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

import numpy as np

import assembly as A
import assembly_checks as ac
import cad_agent as ca
import feature_graph as fg
import layout as lay
import parts as pt
from test_cad_agent import ScriptedLLM

REPO = Path(__file__).parent
PARTS = REPO / "benchmarks" / "enclosure" / "parts"
RULES_PATH = REPO / "design_rules.json"
L1 = [{"id": "L1.1", "text": "The enclosure shall have a base and a lid.", "method": "inspection"}]


class FakeLLM(ScriptedLLM):
    """ScriptedLLM that accepts assembly mode's num_predict keyword."""

    def chat(self, prompt, system="", images=(), schema=None, temperature=0.0, seed=0, label="ask",
             num_predict=None):
        return super().chat(prompt, system, images, schema, temperature, seed, label)


class SchemaLLM(FakeLLM):
    """FakeLLM that also records the schema of every question (to check the action space it offers)."""

    def __init__(self, script):
        super().__init__(script)
        self.schemas = []

    def chat(self, prompt, system="", images=(), schema=None, temperature=0.0, seed=0, label="ask",
             num_predict=None):
        self.schemas.append((label, schema))
        return super().chat(prompt, system, images, schema, temperature, seed, label, num_predict)


class RankedLLM(FakeLLM):
    """FakeLLM whose p_yes reads a table: each entry is (substrings that must all appear in the question,
    p); the first matching entry wins, else `default`. Edge votes and the other answers are scripted."""

    def __init__(self, script, table, default=0.09):
        super().__init__(script)
        self.table = list(table)
        self.default = default

    def p_yes(self, prompt, label="p_yes", system="", images=()):
        self.calls.append((label, prompt, list(images)))
        return next((p for keys, p in self.table if all(k in prompt for k in keys)), self.default)


def fake_agent_factory(*args, **kwargs):
    return ScriptedLLM({})       # any LLM call raises


def request(rid: str) -> dict:
    for src in ("enclosure.json", "variants.json"):
        for r in json.loads((REPO / "benchmarks" / "enclosure" / src).read_text())["requests"]:
            if r["id"] == rid:
                return r
    raise KeyError(rid)


def texts(rid: str, with_l1: bool = True):
    r = request(rid)
    return [("request", r["request"])] + ([(x["id"], x["text"]) for x in r["l1"]] if with_l1 else [])


def l1_with(rid: str, words: str) -> str:
    return next(x["id"] for x in request(rid)["l1"] if words in x["text"])


def number_id(rid: str, value: float, source: str, k: int = 0, with_l1: bool = True) -> str:
    hits = [n["id"] for n in A.extract_numbers(texts(rid, with_l1))
            if abs(n["value"] - value) < 1e-9 and n["source"] == source]
    return hits[k]


def request_numbers(rid: str):
    """(board w, board d, (max x, y, z)) parsed by the test from the request and its size L1."""
    import re
    req = request(rid)
    w, d = map(float, re.search(r"(\d+) x (\d+) mm perfboard", req["request"]).groups())
    size_l1 = l1_with(rid, "no larger than")
    text = next(x["text"] for x in req["l1"] if x["id"] == size_l1)
    mx = tuple(map(float, re.search(r"(\d+) x (\d+) x (\d+) mm", text).groups()))
    return w, d, mx, size_l1


def l1_text(rid: str, l1_id: str) -> str:
    return next(x["text"] for x in request(rid)["l1"] if x["id"] == l1_id)


def spec_reply(rid: str) -> dict:
    """The correct ParseSpec answer for a request: number ids located from the texts (values parsed by the test)."""
    import re
    w, d, mx, size_l1 = request_numbers(rid)
    keep = l1_with(rid, "above the board")
    above, below = map(float, re.search(r"within (\d+) mm above .* or (\d+) mm below", l1_text(rid, keep)).groups())
    clear = l1_with(rid, "clearance")
    walls = l1_with(rid, "thick")
    over = l1_with(rid, "bigger than")
    head = re.search(r"at least (\d+) mm of space above the tallest part", request(rid)["request"])
    return {"board_width": number_id(rid, w, "request"), "board_depth": number_id(rid, d, "request"),
            "keepout_above": number_id(rid, above, keep), "keepout_below": number_id(rid, below, keep),
            "board_clearance": number_id(rid, 0.5, clear),
            "headroom": number_id(rid, float(head.group(1)), "request") if head else "none",
            "opening_oversize_max": number_id(rid, 1.5, over),
            "wall_min": number_id(rid, 2, walls), "wall_max": number_id(rid, 4, walls),
            "max_x": number_id(rid, mx[0], size_l1), "max_y": number_id(rid, mx[1], size_l1),
            "max_z": number_id(rid, mx[2], size_l1)}


SCRIPTED = {
    "E1-01": {"jacks": 2, "edges": {"module_1": "-X", "connector_1": "+X"}, "stack": "header_male_2p54"},
    "V1": {"jacks": 1, "edges": {"module_1": "-X", "connector_1": "-X"}, "stack": "header_male_2p54"},
    "V2": {"jacks": 3, "edges": {"module_1": "-X", "connector_1": "+Y"}, "stack": "header_male_2p54"},
    "V3": {"jacks": 1, "edges": {"module_1": "-X", "connector_1": "+X"}, "stack": "header_female_2p54",
           "cylinders": 1},
}


def cylinder_params_reply(rid: str) -> dict:
    """The assy_params answer for a request-sized capacitor: the ids of its diameter and height in the request."""
    nums = A.extract_numbers(texts(rid))
    dia = next(n["id"] for n in nums if n["source"] == "request" and "diameter" in n["quote"] and n["text"].startswith("10"))
    tall = next(n["id"] for n in nums if n["source"] == "request" and n["text"].startswith("20"))
    return {"diameter": dia, "height": tall}


def script_for(rid: str, **over) -> dict:
    s = SCRIPTED[rid]
    script = {
        "assy_spec": [spec_reply(rid)],
        "assy_contents": [{"perfboard": {"quantity": 1}, "rpi_pico2": {"quantity": 1, "exposed": "yes"},
                           "jack_3p5_pj320a": {"quantity": s["jacks"], "exposed": "yes"},
                           "generic_cylinder": {"quantity": s.get("cylinders", 0)}}],
        "assy_stack": [{"stack": s["stack"]}],
        "assy_edge": [dict(s["edges"])],
        "assy_confirm": [{"answer": "yes"}],
    }
    if s.get("cylinders"):
        script["assy_params"] = [cylinder_params_reply(rid)]
    script.update(over)
    return script


def new_design(rid: str, root: Path, with_l1: bool = True, rules_path: Path = RULES_PATH):
    r = request(rid)
    l1 = r["l1"] if with_l1 else []
    d = ca.Design(request=ca.request_with_l1(r["request"], l1), workdir=root / rid, l1=l1,
                  base_request=r["request"])
    d.assy = A.AssemblyState(parts_dir=str(PARTS), rules_path=str(rules_path))
    return d


def run_stages(design, llm, upto: str):
    """Tick the assembly tree's stages in order up to and including `upto` (a class name)."""
    tree = A.build_assembly_tree(design, llm, PARTS, design.assy.rules_path)
    for child in tree.children:
        status = child.update()
        if status != ca.Status.SUCCESS:
            return status, child
        if type(child).__name__ == upto:
            return status, child
    return ca.Status.SUCCESS, None


def test_rules(root: Path, **override) -> Path:
    """A copy of design_rules.json with some values overridden (e.g. fn for a fast test)."""
    data = json.loads(RULES_PATH.read_text())
    for k, v in override.items():
        data["rules"][k]["value"] = v
    path = root / "rules.json"
    path.write_text(json.dumps(data))
    return path


# ---------------------------------------------------------------------------
# CLI (milestone M0 tests, updated for the walking skeleton)
# ---------------------------------------------------------------------------


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

    def run_main(self, *argv, llm=None):
        factory = (lambda *a, **k: llm) if llm is not None else fake_agent_factory
        with mock.patch.object(ca, "OllamaAgent", factory):
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

    def test_gate_then_a_typed_parse_spec_failure(self):
        # changed in generalize iteration 001 (delta 001 D4, behaviour intentionally changed): the board size slots are
        # optional, so a request with no number passes ParseSpec without a re-ask, and the run stops at Contents with a
        # typed note (nothing in the text names a catalogue part), exit 1.
        out = self.root / "out"
        llm = FakeLLM({"assy_spec": [lambda p: {k: "none" for k in A_SLOTS}]})
        rc = self.run_main("--mode", "assembly", "--auto", "--l1", str(self.l1), "--parts", str(self.parts),
                           "--out", str(out), "an enclosure", llm=llm)
        self.assertEqual(rc, ca.EXIT_FAILED)
        rec = self.design_record(out)
        self.assertEqual(rec["outcome"], "failed")
        assy = rec["assembly"]
        self.assertEqual(assy["stage"], "contents")
        self.assertTrue(any("nothing to design around" in n for n in assy["notes"]), assy["notes"])
        self.assertEqual(llm.labels().count("assy_spec_reask"), 0)
        # the gate dropped the inch-scaled copy and said why; the good parts were kept
        self.assertNotIn("bad_scaled_module", assy["catalog"])
        self.assertIn("rpi_pico2", assy["catalog"])
        self.assertTrue(any("bad_scaled_module" in n and "R1" in n for n in assy["notes"]), assy["notes"])
        self.assertIn("fn", assy["rules"])
        self.assertFalse(assy["with_models"])

    def test_enclosure_alias_runs_assembly(self):
        out = self.root / "out2"
        llm = FakeLLM({"assy_spec": [lambda p: {k: "none" for k in A_SLOTS}]})
        rc = self.run_main("--mode", "enclosure", "--auto", "--l1", str(self.l1), "--parts", str(self.parts),
                           "--with-models", "--out", str(out), "an enclosure", llm=llm)
        self.assertEqual(rc, ca.EXIT_FAILED)
        rec = self.design_record(out)
        self.assertEqual(rec["assembly"]["stage"], "contents")      # generalize delta 001 D4: size slots are optional
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


A_SLOTS = [s["name"] for s in pt.load_rules(RULES_PATH).spec_slots]


# ---------------------------------------------------------------------------
# ParseSpec
# ---------------------------------------------------------------------------


class TestExtractNumbers(unittest.TestCase):
    def test_every_occurrence_has_its_own_id_and_groups_share_a_unit(self):
        nums = A.extract_numbers(texts("E1-01"))
        ids = [n["id"] for n in nums]
        self.assertEqual(len(ids), len(set(ids)))
        w, d, mx, size_l1 = request_numbers("E1-01")
        board = [n for n in nums if n["source"] == "request"][:2]
        self.assertEqual([n["value"] for n in board], [w, d])
        self.assertTrue(all(n["unit"] == "mm" for n in board))        # "a x b mm": the unit applies to both
        limits = [n for n in nums if n["source"] == size_l1][:3]
        self.assertEqual(tuple(n["value"] for n in limits), mx)
        same = [n for n in nums if n["value"] == mx[1]]               # the same value in several places
        self.assertGreater(len({n["id"] for n in same}), 1)
        self.assertTrue(all(len(n["quote"]) <= A.QUOTE_CHARS for n in nums))

    def test_part_numbers_and_ranges(self):
        nums = A.extract_numbers([("t", "an M2.5 screw, a PJ-320A jack, walls 2 to 4 mm, 3 cm wide")])
        vals = [(n["value"], n["unit"]) for n in nums]
        self.assertNotIn(2.5, [v for v, _ in vals])                   # "M2.5" is a name, not a number
        self.assertNotIn(320.0, [v for v, _ in vals])
        self.assertIn((2.0, "mm"), vals)                              # "2 to 4 mm": the range shares the unit
        self.assertIn((30.0, "mm"), vals)                             # cm -> mm


class TestParseSpec(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def parse(self, rid, script, with_l1=True):
        d = new_design(rid, self.root, with_l1)
        llm = FakeLLM(script)
        status, _ = run_stages(d, llm, "ParseSpec")
        return d.assy, llm, status

    def test_correct_spec_with_provenance(self):
        st, llm, status = self.parse("E1-01", {"assy_spec": [spec_reply("E1-01")]})
        self.assertEqual(status, ca.Status.SUCCESS)
        w, d, mx, size_l1 = request_numbers("E1-01")
        self.assertEqual((st.spec["board_width"], st.spec["board_depth"]), (w, d))
        self.assertEqual((st.spec["max_x"], st.spec["max_y"], st.spec["max_z"]), mx)
        self.assertEqual((st.spec["keepout_above"], st.spec["keepout_below"]), (12.0, 4.0))
        self.assertTrue(st.spec_provenance["max_x"].startswith(f'{size_l1}:"'))
        self.assertTrue(st.spec_provenance["board_width"].startswith('request:"'))
        self.assertEqual(st.spec_provenance["headroom"], "rules:board_to_wall")
        self.assertEqual(llm.labels(), ["assy_spec"] * ca.VOTES)

    def test_reply_outside_the_enum_takes_the_default(self):
        reply = dict(spec_reply("E1-01"), keepout_above="n999")
        st, _, status = self.parse("E1-01", {"assy_spec": [reply]})
        self.assertEqual(status, ca.Status.SUCCESS)
        rules = pt.load_rules(RULES_PATH)
        default = rules.slot("keepout_above")["default_rule"]
        self.assertEqual(st.spec["keepout_above"], rules.values[default])
        self.assertEqual(st.spec_provenance["keepout_above"], f"rules:{default}")
        self.assertTrue(any(a.startswith("keepout_above") for a in st.assumptions))
        values = {n["value"] for n in st.numbers} | set(rules.values.values())
        self.assertTrue(all(v in values for v in st.spec.values()))     # never an invented number

    def test_relation_violation_is_re_asked_once(self):
        good = spec_reply("E1-01")
        swapped = dict(good, wall_min=good["wall_max"], wall_max=good["wall_min"])
        st, llm, status = self.parse("E1-01", {"assy_spec": [swapped], "assy_spec_reask": [good]})
        self.assertEqual(status, ca.Status.SUCCESS)
        self.assertEqual(llm.labels().count("assy_spec_reask"), ca.VOTES)
        reask = next(p for lb, p, _ in llm.calls if lb == "assy_spec_reask")
        self.assertIn("wall_min", reask.split("broke these rules:")[1])
        self.assertLessEqual(st.spec["wall_min"], st.spec["wall_max"])

    def keepout_ids(self, rid="E1-01"):
        keep = l1_with(rid, "above the board")
        return number_id(rid, 12, keep), number_id(rid, 4, keep)

    def test_shared_number_id_is_reasked(self):
        good = spec_reply("E1-01")
        above, below = self.keepout_ids()
        dup = dict(good, keepout_below=above)                  # the iter_003 controller's answer
        st, llm, status = self.parse("E1-01", {"assy_spec": [dup], "assy_spec_reask": [good]})
        self.assertEqual(status, ca.Status.SUCCESS)
        reask = next(p for lb, p, _ in llm.calls if lb == "assy_spec_reask").split("broke these rules:")[1]
        self.assertIn("keepout_above and keepout_below both use " + above, reask)
        quote = next(n["quote"] for n in st.numbers if n["id"] == above)
        self.assertIn(quote, reask)
        self.assertEqual((st.spec["keepout_above"], st.spec["keepout_below"]), (12.0, 4.0))
        self.assertIn("4 mm below", st.spec_provenance["keepout_below"])
        self.assertNotIn("assy_spec_owner", llm.labels())

    def test_persistent_shared_id_is_resolved_by_owner_question(self):
        good = spec_reply("E1-01")
        above, below = self.keepout_ids()
        dup = dict(good, keepout_below=above)
        d = new_design("E1-01", self.root / "a")
        llm = SchemaLLM({"assy_spec": [dup], "assy_spec_reask": [dup], "assy_spec_owner": [{"owner": "keepout_above"}],
                         "assy_spec_slot": [{"keepout_below": below}]})
        status, _ = run_stages(d, llm, "ParseSpec")
        st = d.assy
        self.assertEqual(status, ca.Status.SUCCESS)
        self.assertEqual(llm.labels().count("assy_spec_owner"), ca.VOTES)
        owner_schema = next(sc for lb, sc in llm.schemas if lb == "assy_spec_owner")
        self.assertEqual(owner_schema["properties"]["owner"]["enum"], ["keepout_above", "keepout_below"])
        slot_schema = next(sc for lb, sc in llm.schemas if lb == "assy_spec_slot")
        self.assertEqual(list(slot_schema["properties"]), ["keepout_below"])     # only the losing slot
        self.assertNotIn(above, slot_schema["properties"]["keepout_below"]["enum"])
        self.assertIn(below, slot_schema["properties"]["keepout_below"]["enum"])
        self.assertEqual((st.spec["keepout_above"], st.spec["keepout_below"]), (12.0, 4.0))
        self.assertIn("4 mm below", st.spec_provenance["keepout_below"])
        # no valid owner: both slots fall back to their rules defaults, flagged (as for any persistent violation)
        d = new_design("E1-01", self.root / "b")
        llm = FakeLLM({"assy_spec": [dup], "assy_spec_reask": [dup], "assy_spec_owner": [{"owner": "headroom"}]})
        status, _ = run_stages(d, llm, "ParseSpec")
        self.assertEqual(status, ca.Status.SUCCESS)
        self.assertNotIn("assy_spec_slot", llm.labels())
        rules = pt.load_rules(RULES_PATH)
        for k in ("keepout_above", "keepout_below"):
            self.assertEqual(d.assy.spec[k], rules.values[rules.slot(k)["default_rule"]])
            self.assertTrue(any(a.startswith(k) for a in d.assy.assumptions), k)

    def test_silent_request_uses_flagged_rules_defaults(self):
        rid = "V1"
        w, d, _, _ = request_numbers(rid)
        reply = {k: "none" for k in A_SLOTS}
        reply.update(board_width=number_id(rid, w, "request", with_l1=False),
                     board_depth=number_id(rid, d, "request", with_l1=False))
        st, _, status = self.parse(rid, {"assy_spec": [reply]}, with_l1=False)
        self.assertEqual(status, ca.Status.SUCCESS)
        rules = pt.load_rules(RULES_PATH)
        for k in ("keepout_above", "keepout_below", "board_clearance"):
            self.assertEqual(st.spec[k], rules.values[rules.slot(k)["default_rule"]])
            self.assertTrue(any(a.startswith(k) for a in st.assumptions), k)


# ---------------------------------------------------------------------------
# Contents and ChooseStack
# ---------------------------------------------------------------------------


class TestContents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_e1_contents_and_candidates(self):
        d = new_design("E1-01", self.root)
        llm = FakeLLM(script_for("E1-01"))
        status, _ = run_stages(d, llm, "ChooseStack")
        self.assertEqual(status, ca.Status.SUCCESS)
        got = {(c["part"], c["quantity"], c["exposed"]) for c in d.assy.contents}
        self.assertEqual(got, {("perfboard", 1, False), ("rpi_pico2", 1, True), ("jack_3p5_pj320a", 2, True)})
        prompt = next(p for lb, p, _ in llm.calls if lb == "assy_contents")
        cat = pt.Catalog.load(PARTS)
        for pid in cat.ids():
            if cat.get(pid).kind in ("plug", "fastener"):
                self.assertNotIn(f"- {pid}:", prompt)
        board = next(c for c in d.assy.contents if c["kind"] == "board")
        w, dd, _, _ = request_numbers("E1-01")
        self.assertEqual(board["params"], {"width": w, "depth": dd})
        self.assertEqual(d.assy.choices["stack[module_1]"]["value"], "header_male_2p54")

    def test_board_provenance(self):
        # iteration 011 (C1, RC-1101): the board's hole numbers say where they came from. E1-01's board is the
        # catalogue's photographed specimen; V1's board gets the family holes, stated once as an assumption whose
        # numbers are read back from the instance here
        d = new_design("E1-01", self.root / "e1")
        status, _ = run_stages(d, FakeLLM(script_for("E1-01")), "Contents")
        self.assertEqual(status, ca.Status.SUCCESS)
        st = d.assy
        self.assertTrue(st.spec_provenance["board.hole_inset"].startswith("catalogue:perfboard specimen photo_70x50"))
        self.assertTrue(st.spec_provenance["board.hole_diameter"].startswith("catalogue:perfboard specimen photo_70x50"))
        self.assertFalse([a for a in st.assumptions if "mounting-hole" in a], st.assumptions)
        self.assertIn("contents: board matches catalogue specimen photo_70x50", st.notes)
        d = new_design("V1", self.root / "v1")
        status, _ = run_stages(d, FakeLLM(script_for("V1")), "Contents")
        self.assertEqual(status, ca.Status.SUCCESS)
        st = d.assy
        board = next(c for c in st.contents if c["kind"] == "board")
        inst = st.catalog.instantiate(board["part"], board["params"])
        self.assertIsNone(inst.specimen)
        for p in ("hole_inset", "hole_diameter"):
            self.assertEqual(st.spec_provenance[f"board.{p}"], "catalogue:perfboard family default")
        lines = [a for a in st.assumptions if "mounting-hole" in a]
        self.assertEqual(len(lines), 1, st.assumptions)
        holes = inst.datums["HOLE"]
        self.assertIn(f"Ø{holes.diameter:g} ", lines[0])
        self.assertIn(f" {holes.at[0][0]:g} mm from each edge", lines[0])
        self.assertEqual((holes.diameter, holes.at[0][0]), (3.0, 2.5))

    def test_two_boards_is_a_typed_failure(self):
        d = new_design("E1-01", self.root)
        script = script_for("E1-01", assy_contents=[{"perfboard": {"quantity": 2}}])
        status, child = run_stages(d, FakeLLM(script), "Contents")
        self.assertEqual(status, ca.Status.FAILURE)
        self.assertEqual(d.assy.stage, "contents")
        # generalize delta 001 C1: the rule is now "exactly one carrier" (the primary reference), still a typed failure
        self.assertTrue(any("exactly one carrier" in n for n in d.assy.notes), d.assy.notes)

    def test_v3_socket_stack_and_request_sized_part(self):
        rid = "V3"
        nums = A.extract_numbers(texts(rid))
        dia = next(n["id"] for n in nums if n["source"] == "request" and "diameter" in n["quote"]
                   and n["text"].startswith("10"))
        tall = next(n["id"] for n in nums if n["source"] == "request" and n["text"].startswith("20"))
        w, dd = (float(v) for v in __import__("re").search(r"(\d+) x (\d+) mm", request(rid)["request"]).groups())
        spec = {k: "none" for k in A_SLOTS}
        spec.update(board_width=number_id(rid, w, "request"), board_depth=number_id(rid, dd, "request"))
        script = {"assy_spec": [spec],
                  "assy_contents": [{"perfboard": {"quantity": 1}, "rpi_pico2": {"quantity": 1, "exposed": "yes"},
                                     "jack_3p5_pj320a": {"quantity": 1, "exposed": "yes"},
                                     "generic_cylinder": {"quantity": 1}}],
                  "assy_params": [{"diameter": dia, "height": tall}],
                  "assy_stack": [{"stack": "header_male_2p54"}]}
        d = new_design(rid, self.root)
        llm = FakeLLM(script)
        status, _ = run_stages(d, llm, "ChooseStack")
        self.assertEqual(status, ca.Status.SUCCESS)
        cap = next(c for c in d.assy.contents if c["part"] == "generic_cylinder")
        self.assertEqual(cap["params"], {"diameter": 10.0, "height": 20.0})
        # changed in iteration 007 (behaviour intentionally changed, ARCHITECTURE.md 7.10): the stack is a rule decision
        # from text evidence ("female header sockets", "8.5 mm"), so the scripted (wrong) answer is never asked for
        self.assertEqual(d.assy.choices["stack[module_1]"]["value"], "header_female_2p54")
        self.assertEqual(d.assy.choices["stack[module_1]"]["by"], "rule:text_evidence")
        self.assertNotIn("assy_stack", llm.labels())

    def test_contents_words_name_the_mating_plug(self):
        # iteration 007 (C3): a connector is worded by its mating plug's first human name, never by the plug's id
        d = new_design("E1-01", self.root)
        llm = FakeLLM(script_for("E1-01"))
        status, _ = run_stages(d, llm, "Contents")
        self.assertEqual(status, ca.Status.SUCCESS)
        prompt = next(p for lb, p, _ in llm.calls if lb == "assy_contents")
        cat = pt.Catalog.load(PARTS)
        for pid in cat.ids():
            for c in cat.get(pid).data.get("connectors", []):
                self.assertIn(f"{c['name']} connector (takes a {cat.get(c['mates']).names[0]})", prompt)
                self.assertNotIn(f"takes a {c['mates']}", prompt)

    def test_stack_evidence_gate(self):
        # iteration 007 (C2, RC-703, ARCHITECTURE.md 7.10): an option is offered only with evidence in the text
        cat = pt.Catalog.load(PARTS)
        options = cat.get("rpi_pico2").data["mount"]["stack_options"]
        for rid in ("E1-01", "V1", "V2"):        # no word for a mounting: the catalogue default, no question
            with self.subTest(rid=rid):
                d = new_design(rid, self.root / rid)
                llm = FakeLLM({k: v for k, v in script_for(rid).items() if k != "assy_stack"})   # a stack call raises
                status, _ = run_stages(d, llm, "ChooseStack")
                self.assertEqual(status, ca.Status.SUCCESS, d.assy.notes)
                rec = d.assy.choices["stack[module_1]"]
                self.assertEqual((rec["value"], rec["by"], rec["evidence"]), (options[0], "rule:catalogue_default", []))
                self.assertNotIn("assy_stack", llm.labels())
                self.assertTrue(any(a.startswith("stack[module_1]") and "catalogue default" in a
                                    for a in d.assy.assumptions), d.assy.assumptions)
        d = new_design("V3", self.root / "V3")   # "female header sockets" and "8.5 mm": one option, chosen by rule
        llm = FakeLLM({k: v for k, v in script_for("V3").items() if k != "assy_stack"})
        status, _ = run_stages(d, llm, "ChooseStack")
        self.assertEqual(status, ca.Status.SUCCESS, d.assy.notes)
        rec = d.assy.choices["stack[module_1]"]
        self.assertEqual((rec["value"], rec["by"]), ("header_female_2p54", "rule:text_evidence"))
        quotes = [e["quote"] for e in rec["evidence"]]
        self.assertTrue(any("female header" in q.lower() for q in quotes), quotes)
        self.assertTrue(all(e["option"] == "header_female_2p54" for e in rec["evidence"]))
        self.assertNotIn("assy_stack", llm.labels())
        # a text naming both options (an alias of one, the stack height of the other): asked among exactly those two
        r = request("V1")
        both = {"id": "L1.x", "text": "The Pico 2 sits either on male headers or on 8.5 mm sockets.", "method": "inspection"}
        l1 = r["l1"] + [both]
        d = ca.Design(request=ca.request_with_l1(r["request"], l1), workdir=self.root / "both", l1=l1,
                      base_request=r["request"])
        d.assy = A.AssemblyState(parts_dir=str(PARTS), rules_path=str(RULES_PATH))
        llm = SchemaLLM(script_for("V1", assy_stack=[{"stack": "header_female_2p54"}]))
        status, _ = run_stages(d, llm, "ChooseStack")
        self.assertEqual(status, ca.Status.SUCCESS, d.assy.notes)
        self.assertEqual(llm.labels().count("assy_stack"), ca.VOTES)
        schema = next(sc for lb, sc in llm.schemas if lb == "assy_stack")
        self.assertEqual(schema["properties"]["stack"]["enum"], ["header_male_2p54", "header_female_2p54"])
        rec = d.assy.choices["stack[module_1]"]
        self.assertEqual((rec["value"], rec["by"]), ("header_female_2p54", "llm"))
        self.assertEqual({e["option"] for e in rec["evidence"]}, set(options))
        self.assertTrue(all(e["source"] == "L1.x" for e in rec["evidence"]))

    def test_text_evidence_is_generic(self):
        # alias runs are contiguous token runs (plurals folded); numbers match within the tolerance; one hit per sentence
        texts_ = [("a", "Two 3.5 mm plugs go in. A plug of 3.5 mm. Nothing here."), ("b", "It sits 8.49 mm up.")]
        hits = A.text_evidence(texts_, ["3.5 mm plug"], [8.5], tol=0.02)
        self.assertEqual([(h["source"], h["kind"]) for h in hits], [("a", "alias"), ("b", "number")])
        self.assertEqual(hits[0]["quote"], "Two 3.5 mm plugs go in.")
        self.assertEqual(A.text_evidence(texts_, ["3.5 mm plug"], [8.5], tol=0.0)[1:], [])

    def test_coverage_infeasible_is_reported(self):
        # Replaces test_coverage_no_is_reported (iteration 008, RC-801, behaviour intentionally changed): the LLM may no
        # longer leave a named plug's connector unexposed; only geometric infeasibility can. Every placement holding the
        # coverage-forced item collides, so it is reverted (rule:coverage_infeasible), the placement runs exactly once
        # more, and the missing opening is a failing text_coverage check with a quoted `coverage` conflict.
        llm = iter007_llm("V1_s5")
        forced = "module_1"
        orig = lay.Placer.place

        def place(placer, items_, assign):
            if forced in assign:
                raise lay.LayoutError("collides", f"{forced} collides (test)")
            return orig(placer, items_, assign)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(lay.Placer, "place", place):
            rc, pkg, _ = run_offline("V1", Path(tmp), test_rules(Path(tmp), fn=24), llm=llm)
            rec = json.loads((pkg / "design.json").read_text())
            matrix = json.loads((pkg / "verification_matrix.json").read_text())
        assy = rec["assembly"]
        naming = l1_with("V1", "micro-USB cable")
        self.assertNotIn("assy_expose", llm.labels())
        self.assertEqual(llm.labels().count("assy_edge"), 2 * ca.VOTES)          # the placement ran exactly twice
        self.assertEqual(len([n for n in assy["notes"] if "reverted to unexposed" in n]), 1, assy["notes"])
        self.assertEqual(rc, ca.EXIT_UNSATISFIED)                                 # the package is written (not rc 1)
        self.assertEqual(rec["outcome"], "unsatisfied")
        (row,) = assy["coverage"]
        self.assertEqual(row["resolved"], "unexposed")
        self.assertIn("collides", row["reason"])
        self.assertEqual(row["by"], "rule:coverage_infeasible")
        ch = assy["choices"][f"exposed[{forced}]"]
        self.assertEqual((ch["value"], ch["by"]), (False, "rule:coverage_infeasible"))
        self.assertIn("collides", ch["reason"])
        cov = next(r for r in assy["results"] if r["check_id"] == "text_coverage")
        self.assertFalse(cov["passed"])
        self.assertEqual(cov["margin"], -1.0)
        (u,) = cov["evidence"]["uncovered"]
        self.assertEqual((u["plug"], u["connector"]), ("plug_microusb_b", "usb"))
        self.assertIn(naming, [e["source"] for e in u["evidence"]])
        conflicts = [c for c in assy["conflicts"] if c["kind"] == "coverage"]
        self.assertEqual(len(conflicts), 1, assy["conflicts"])
        self.assertEqual(conflicts[0]["check_id"], "text_coverage")
        self.assertIn(l1_text("V1", naming), conflicts[0]["conflict"])
        self.assertFalse(next(c for c in assy["contents"] if c["part"] == "rpi_pico2")["exposed"])
        self.assertEqual(sorted(r["check_id"] for r in assy["results"] if not r["passed"]),
                         ["text_coverage"])     # changed in iteration 010: grid_conformance passes (C4 / C5)
        row = next(r for r in matrix if r["l1_id"] == naming)       # the naming L1 shows the failure
        self.assertEqual(row["status"], "FAIL")
        self.assertIn("text_coverage", [c["id"] for c in row["checks"] if not c["passed"]])

    def test_no_question_without_named_plug(self):
        # iteration 007 (C3): no text names the module's mating plug, so a "no" stands and no assy_expose is asked
        l1 = without_plug_names("E1-01")
        no = script_for("E1-01")
        no["assy_contents"] = [dict(no["assy_contents"][0], rpi_pico2={"quantity": 1, "exposed": "no"})]
        llm = FakeLLM(no)
        with tempfile.TemporaryDirectory() as tmp:
            rc, pkg, _ = run_offline("E1-01", Path(tmp), test_rules(Path(tmp), fn=24), llm=llm, l1_list=l1)
            assy = json.loads((pkg / "design.json").read_text())["assembly"]
        self.assertNotIn("assy_expose", llm.labels())
        self.assertEqual(assy["coverage"], [])
        cov = next(x for x in assy["results"] if x["check_id"] == "text_coverage")
        self.assertTrue(cov["passed"], cov["evidence"])
        self.assertEqual(cov["evidence"]["uncovered"], [])
        self.assertNotIn("plug_microusb_b", cov["evidence"]["named"])
        self.assertFalse(next(c for c in assy["contents"] if c["part"] == "rpi_pico2")["exposed"])


def without_plug_names(rid: str, plug: str = "plug_microusb_b") -> list:
    """The request's L1s with every alias of a plug replaced by a neutral word (same numbers, so recorded number ids
    stay valid); asserts that neither the request nor the new L1s name the plug."""
    r = request(rid)
    aliases = [a.lower() for a in pt.Catalog.load(PARTS).get(plug).names]
    l1 = []
    for x in r["l1"]:
        text = x["text"]
        for a in aliases:
            low = text.lower()
            k = low.find(a)
            while k >= 0:                     # replace every alias of the plug with a neutral word (same numbers)
                text = text[:k] + "cable" + text[k + len(a):]
                low = text.lower()
                k = low.find(a)
        l1.append(dict(x, text=text))
    assert not any(a in (x["text"] + r["request"]).lower() for x in l1 for a in aliases), rid
    return l1


# ---------------------------------------------------------------------------
# ArrangeContents (layout.py) and ConfirmArrangement
# ---------------------------------------------------------------------------


def placer_for(rid: str, w=None, d=None):
    cat = pt.Catalog.load(PARTS)
    rules = pt.load_rules(RULES_PATH).values
    if w is None:
        import re
        w, d = (float(v) for v in re.search(r"(\d+) x (\d+) mm", request(rid)["request"]).groups())
    board = cat.instantiate("perfboard", {"width": w, "depth": d})
    placed = lay.Placed("board", "perfboard", {"width": w, "depth": d}, 0, 0, 0, 0, "", role="board", inst=board)
    screw = A.board_screw(cat, board, rules)
    seat_d = pt.instantiate(screw).params["head_diameter"] + 2 * rules["driver_clearance"]
    return cat, rules, lay.Placer(cat, placed, rules, seat_d, rules["component_height_default"])


def items(jacks, stack="header_male_2p54"):
    return [lay.Item("pico", "rpi_pico2", {}, 1, True, stack, "pico 2"),
            lay.Item("jack", "jack_3p5_pj320a", {}, jacks, True, None, "jack")]


def mouths(layout, item):
    out = []
    for p in layout.of_item(item):
        c = p.inst.connectors[0]
        out.append((np.asarray(lay.world_datum(p, c["mouth"]).at), np.asarray(lay.world_datum(p, c["axis"]).dir)))
    return out


class TestArrange(unittest.TestCase):
    def assert_clean(self, placer, layout):
        self.assertEqual(placer.collisions(layout.placed), [])

    def spacing_need(self, cat, rules, a, b):
        wa, wb = lay.plug_width(cat, cat.get(a)), lay.plug_width(cat, cat.get(b))
        return wa / 2 + wb / 2 + 2 * rules["plug_to_opening"] + rules["min_ligament"]

    def test_e1_ports_on_opposite_short_ends(self):
        cat, rules, placer = placer_for("E1-01")
        layout = placer.place(items(2), {"pico": "-X", "jack": "+X"})
        pico = cat.instantiate("rpi_pico2")
        (m, u), = mouths(layout, "pico")
        np.testing.assert_allclose(u, [-1, 0, 0], atol=1e-9)
        # changed in iteration 010 (behaviour intentionally changed, C4 / L2.1.3): the Pico's first pin sits on grid
        # column 0, so the mouth is column 0 - first pin - overhang, inside the board edge (was flush, -usb_overhang)
        origin, pitch = placer.grid
        self.assertAlmostEqual(m[0], origin[0] - pico.params["pin_from_short_edge"] - pico.params["usb_overhang"], places=9)
        w = layout.get("board").params["width"]
        jm = mouths(layout, "jack")
        for jmouth, ju in jm:
            np.testing.assert_allclose(ju, [1, 0, 0], atol=1e-9)
            self.assertAlmostEqual(jmouth[0], w, places=9)
        need = self.spacing_need(cat, rules, "jack_3p5_pj320a", "jack_3p5_pj320a")
        self.assertGreaterEqual(abs(jm[0][0][1] - jm[1][0][1]), need)
        self.assert_clean(placer, layout)
        # the Pico's pins sit on existing grid holes in both plan axes (changed in iteration 010: was Y only)
        for name in ("PINS_A", "PINS_B"):
            for q in lay.world_datum(layout.get("pico_1"), name).at:
                self.assertLessEqual(float(np.linalg.norm(placer.grid.offset(q))), 1e-6)
        # headers carry the module: its PCB bottom is the header's STACK_TOP
        stack = [p for p in layout.placed if p.of == "pico_1"]
        self.assertEqual(len(stack), 2)
        top = lay.world_datum(stack[0], "STACK_TOP").at[2]
        self.assertAlmostEqual(lay.world_datum(layout.get("pico_1"), "PCB_BOTTOM").at[2], top, places=9)

    def test_v1_two_ports_on_one_edge(self):
        cat, rules, placer = placer_for("V1")
        layout = placer.place(items(1), {"pico": "-X", "jack": "-X"})
        (pm, pu), = mouths(layout, "pico")
        (jm, ju), = mouths(layout, "jack")
        np.testing.assert_allclose(pu, [-1, 0, 0], atol=1e-9)
        np.testing.assert_allclose(ju, [-1, 0, 0], atol=1e-9)
        self.assertGreaterEqual(abs(pm[1] - jm[1]), self.spacing_need(cat, rules, "rpi_pico2", "jack_3p5_pj320a"))
        sweeps = []
        for node in ("pico_1", "jack_1"):
            p = layout.get(node)
            c = p.inst.connectors[0]
            world = {"mouth": lay.world_datum(p, c["mouth"]), "axis": lay.world_datum(p, c["axis"])}
            nodes = pt.plug_sweep(world, cat.instantiate(c["mates"]), 0.0, rules["plug_travel"], prefix=node)
            res = fg.FeatureGraph(nodes).resolve(rules=rules)
            sweeps.append(ac.union([fg.solid(n, res) for n in nodes]))
        self.assertLessEqual((sweeps[0] ^ sweeps[1]).volume(), rules["interference_max"])
        self.assert_clean(placer, layout)

    def test_v2_three_jacks_on_a_long_side(self):
        cat, rules, placer = placer_for("V2")
        layout = placer.place(items(3), {"pico": "-X", "jack": "+Y"})
        jm = sorted(mouths(layout, "jack"), key=lambda t: t[0][0])
        self.assertEqual(len(jm), 3)
        need = self.spacing_need(cat, rules, "jack_3p5_pj320a", "jack_3p5_pj320a")
        for (a, ua), (b, _) in zip(jm, jm[1:]):
            np.testing.assert_allclose(ua, [0, 1, 0], atol=1e-9)
            self.assertGreaterEqual(b[0] - a[0], need)
        gaps = np.diff([m[0] for m, _ in jm])
        # changed in iteration 006 (behaviour intentionally changed: the jacks now carry catalogue pin data, so each
        # copy is grid-snapped along the edge by at most pitch/2 after the equal-gap spread)
        _, pitch = placer.grid
        self.assertLessEqual(abs(gaps[0] - gaps[1]), pitch + 1e-9)
        self.assert_clean(placer, layout)
        # a board too short for three plugs side by side: a typed failure, not an overlap
        _, _, small = placer_for("V2", w=need * 2, d=layout.get("board").params["depth"])
        with self.assertRaises(lay.LayoutError) as cm:
            small.place(items(3), {"pico": "-X", "jack": "+Y"})
        self.assertIn(cm.exception.kind, ("ports_do_not_fit", "collides"))

    def test_v3_socket_stack_raises_the_usb_mouth(self):
        cat, rules, placer = placer_for("V3")
        male = placer.place(items(1, "header_male_2p54"), {"pico": "-X", "jack": "+X"})
        female = placer.place(items(1, "header_female_2p54"), {"pico": "-X", "jack": "+X"})
        h = {}
        for sid in ("header_male_2p54", "header_female_2p54"):
            s = cat.instantiate(sid)
            h[sid] = pt.lookup_datum(s.datums, "STACK_TOP").at[2] - pt.lookup_datum(s.datums, "STACK_BOTTOM").at[2]
        dz = mouths(female, "pico")[0][0][2] - mouths(male, "pico")[0][0][2]
        self.assertAlmostEqual(dz, h["header_female_2p54"] - h["header_male_2p54"], places=9)

    def test_grid_report_types_each_part(self):
        # iteration 004 (C4): the residual is sensed per part.
        # changed in iteration 010 (behaviour intentionally changed, C4 / C5; was test_grid_report_names_the_normal_conflict):
        # the Pico is moved onto the finite grid (kind ok, residual 0), flush_to_edge is retired, and the jacks, whose
        # drawing pins meet no lattice position, are pin_pattern: exempt and not counted in `max`
        cat, rules, placer = placer_for("E1-01")
        layout = placer.place(items(2), {"pico": "-X", "jack": "+X"})
        report = placer.grid_report(layout.placed, layout.snaps)
        pico = layout.get("pico_1")
        offs = [placer.grid.offset(q) for name in pico.inst.part.data["mount"]["stack_pins"]
                for q in lay.world_datum(pico, name).at]
        worst = max(offs, key=np.linalg.norm)
        row = report["parts"]["pico_1"]
        self.assertAlmostEqual(row["residual"], float(np.linalg.norm(worst)), delta=1e-9)
        self.assertLessEqual(row["residual"], 1e-6)
        self.assertEqual((row["kind"], row["snap"]), ("ok", "snapped"))
        self.assertGreater(row["positions"], 0)
        self.assertLessEqual(row["best_any"], rules["grid_residual_max"])
        self.assertAlmostEqual(report["max"], row["residual"], places=9)
        self.assertEqual(report["worst"], "pico_1")
        self.assertFalse(report["soft"])
        no_pins = [p.node_id for p in layout.placed if p.role == "content" and p.inst.connectors
                   and not p.inst.part.data.get("mount", {}).get("stack_pins") and "PINS" not in p.inst.datums]
        self.assertEqual(sorted(report["no_pin_data"]), sorted(no_pins))
        self.assertEqual(no_pins, [])
        for k in (1, 2):
            jack = report["parts"][f"jack_{k}"]
            self.assertEqual(jack["kind"], "pin_pattern")
            self.assertGreater(jack["best_any"], rules["grid_residual_max"])
            self.assertEqual(jack["positions"], 0)
            self.assertGreater(jack["residual"], report["max"])          # exempt: not in the checked maximum
        self.assertEqual(sorted(report["exempt"]), ["jack_1", "jack_2"])

    def test_layout_grid_residual_matches_check(self):
        # iteration 011 (C2, RC-1102): the reported grid residual is the grid sensor's checked maximum (pin_pattern
        # parts excluded); the all-parts worst is kept under its own name
        st, _, status = self.arrange(script_for("E1-01"))
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        rep = st.grid_report
        self.assertEqual(st.layout_grid_residual, rep["max"])
        self.assertLessEqual(st.layout_grid_residual, 1e-6)
        pin_pattern = sorted(nid for nid, row in rep["parts"].items() if row["kind"] == "pin_pattern")
        self.assertEqual(sorted(st.layout_grid_exempt), pin_pattern)
        self.assertEqual(len(pin_pattern), SCRIPTED["E1-01"]["jacks"])
        self.assertGreater(st.layout_grid_residual_all, 0.0)

    def arrange(self, script, table=(), default=0.09, upto="ArrangeContents", board=None):
        """Run the stages up to ArrangeContents with a RankedLLM; `board` overrides the board params first."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = new_design("E1-01", Path(tmp.name))
        llm = RankedLLM(script, table, default)
        tree = A.build_assembly_tree(d, llm, PARTS, d.assy.rules_path)
        for child in tree.children:
            if type(child).__name__ == upto and board is not None:
                next(c for c in d.assy.contents if c["kind"] == "board")["params"].update(board)
            status = child.update()
            if status != ca.Status.SUCCESS or type(child).__name__ == upto:
                return d.assy, llm, status
        raise AssertionError(f"no stage {upto}")

    def test_iter003_replay_accepts_the_voted_arrangement_by_rank(self):
        # iteration 003's real run: votes 2 x (-X, +X) and 1 x (-X, -X), p_yes < 0.5 for every candidate
        st, llm, status = self.arrange(script_for("E1-01", assy_edge=ITER003_EDGE_VOTES), iter003_table())
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        self.assertEqual(st.choices["edge[module_1]"]["value"], "-X")
        self.assertEqual(st.choices["edge[connector_1]"]["value"], "+X")
        conf = st.choices["arrangement_confirmed"]
        self.assertEqual(conf["by"], "llm:vote+rank")
        self.assertEqual(conf["value"], {"module_1": "-X", "connector_1": "+X"})
        self.assertEqual(conf["rank"], 1)
        self.assertGreater(conf["margin_to_next"], 0)
        low = [a for a in st.assumptions if a.startswith("arrangement accepted by rank")]
        self.assertEqual(len(low), 1, st.assumptions)
        self.assertNotIn("assy_arrange_pick", llm.labels())
        self.assertEqual(st.arrange["decision"], "llm:vote+rank")
        self.assertEqual(st.arrange["truncated"], 0)

    def test_symmetric_candidates_are_asked_once(self):
        st, llm, status = self.arrange(script_for("E1-01", assy_edge=ITER003_EDGE_VOTES), iter003_table())
        self.assertEqual(status, ca.Status.SUCCESS)
        feasible = [h for h in st.history if h["stage"] == "confirm_arrangement"]
        classes = {h["class"] for h in feasible}
        self.assertEqual(llm.labels().count("assy_confirm"), len(classes))
        self.assertEqual(st.arrange["classes"], len(classes))
        # the half turn is the board's only non-trivial symmetry and fixes no two-item assignment
        self.assertEqual(len(classes) * 2, len(feasible))
        self.assertLess(len(classes), len(feasible))
        cls = {tuple(sorted(h["assignment"].items())): h["class"] for h in feasible}
        self.assertEqual(cls[(("connector_1", "+X"), ("module_1", "-X"))],
                         cls[(("connector_1", "-X"), ("module_1", "+X"))])
        self.assertEqual(sum(h["asked"] for h in feasible), len(classes))
        self.assertEqual(sum(h["chosen"] for h in feasible), 1)
        json.dumps(st.summary()["arrange"])                    # design.json carries the whole ranking

    def test_disagreement_asks_one_comparative_pick(self):
        cat = pt.Catalog.load(PARTS)
        words = edge_words(cat, "E1-01")
        usb, jack = connector_names(cat)
        # votes favour P = (-X, +X); p_yes ranks Q = (-X, -Y), which is not P's mirror image, highest
        table = [((f"({usb}) faces {words['-X']}", f"({jack}) face {words['-Y']}"), 0.4)]
        votes = [{"module_1": "-X", "connector_1": "+X"}]
        p, q = {"module_1": "-X", "connector_1": "+X"}, {"module_1": "-X", "connector_1": "-Y"}
        for picks, expected in ((["B"], q), (["A"], p), (["A", "B", "C"], q)):     # the last is a tie
            with self.subTest(picks=picks):
                script = script_for("E1-01", assy_edge=votes, assy_arrange_pick=[{"pick": x} for x in picks])
                st, llm, status = self.arrange(script, table, default=0.1)
                self.assertEqual(status, ca.Status.SUCCESS, st.notes)
                self.assertEqual(llm.labels().count("assy_arrange_pick"), ca.VOTES)    # one voted question
                self.assertEqual(st.choices["arrangement_confirmed"]["by"], "llm:pick")
                self.assertEqual(st.choices["arrangement_confirmed"]["value"], expected)
                used = {k[5:-1]: v["value"] for k, v in st.choices.items() if k.startswith("edge[")}
                self.assertEqual(used, expected)
                prompt = next(pr for lb, pr, _ in llm.calls if lb == "assy_arrange_pick")
                self.assertIn(f"A: raspberry pi pico 2 ({usb}) faces {words['-X']}", prompt)
                self.assertIn(f"({jack}) face {words['-Y']}", prompt.split("B:")[1])

    def test_no_feasible_arrangement_lists_every_candidate(self):
        cat, rules, _ = placer_for("E1-01")
        need = TestArrange.spacing_need(self, cat, rules, "jack_3p5_pj320a", "jack_3p5_pj320a")
        st, llm, status = self.arrange(script_for("E1-01"), board={"width": need * 2, "depth": need * 2})
        self.assertEqual(status, ca.Status.FAILURE)
        self.assertEqual(st.stage, "arrange_contents")
        self.assertNotIn("assy_confirm", llm.labels())
        msg = st.notes[-1]
        self.assertTrue(msg.startswith("no feasible arrangement: "), msg)
        sides = list(lay.SIDES)
        self.assertEqual(len(st.arrange["candidates"]), len(sides) ** 2)          # every candidate, not 4
        self.assertTrue(all(c["outcome"] == "pruned" for c in st.arrange["candidates"]))
        self.assertEqual(msg.count(" | ") + 1, len(sides) ** 2)
        for m in sides:
            for c in sides:
                self.assertIn(str({"module_1": m, "connector_1": c}), msg)

    def test_low_confidence_vote_winner_is_not_vetoed(self):
        # Changed in iteration 003 (was test_rejected_arrangement_tries_the_next_feasible_one): an uncalibrated
        # p_yes ("no" to everything) no longer vetoes a feasible voted arrangement (ARCHITECTURE.md 7.6).
        with tempfile.TemporaryDirectory() as tmp:
            d = new_design("E1-01", Path(tmp))
            both = {"module_1": "-X", "connector_1": "-X"}
            llm = FakeLLM(script_for("E1-01", assy_edge=[both], assy_confirm=[{"answer": "no"}]))
            status, _ = run_stages(d, llm, "ArrangeContents")
            self.assertEqual(status, ca.Status.SUCCESS)
            confirms = [h for h in d.assy.history if h["stage"] == "confirm_arrangement"]
            self.assertTrue(all(h["p_yes"] < 0.5 for h in confirms))
            # all three E1-01 ports on one 50 mm end cannot fit the plugs: pruned before asking, with a note
            self.assertTrue(any("infeasible" in n and "ports_do_not_fit" in n for n in d.assy.notes), d.assy.notes)
            self.assertNotIn(both, [h["assignment"] for h in confirms])
            chosen = next(h for h in confirms if h["chosen"])
            used = {k[5:-1]: v["value"] for k, v in d.assy.choices.items() if k.startswith("edge[")}
            self.assertEqual(used, chosen["assignment"])
            self.assertEqual(used, d.assy.choices["arrangement_confirmed"]["value"])
            self.assertEqual(d.assy.choices["arrangement_confirmed"]["by"], "llm:vote+rank")
            self.assertTrue(any(a.startswith("arrangement accepted by rank") for a in d.assy.assumptions))


    # iteration 008 (C2, RC-803, ARCHITECTURE.md 7.11): pre-scored arrangement candidates

    def test_prescore_removes_a_candidate_with_a_controllable_failure(self):
        # V3 at iteration 008: the recorded p_yes ranks "Pico on a long side" highest and the recorded A/B pick chose it,
        # so the box broke bbox. Prescore removes every long-side Pico candidate (bbox fails) before the LLM ranks.
        table = recorded_p_yes("V3_s8")
        if not table:
            self.skipTest(f"no recorded transcripts in {ITER008 / 'V3_s8'}")
        llm = recorded_llm("V3_s8", ITER008, cls=RankedLLM, table=table, default=0.09)
        with tempfile.TemporaryDirectory() as tmp:
            rc, pkg, _ = run_offline("V3", Path(tmp), test_rules(Path(tmp), fn=24), llm=llm)
            assy = json.loads((pkg / "design.json").read_text())["assembly"]
        _, _, placer = placer_for("V3")
        lengths = {s: e["length"] for s, e in placer.edges.items()}
        short = min(lengths.values())
        chosen = assy["choices"]["arrangement_confirmed"]
        self.assertEqual(lengths[chosen["value"]["module_1"]], short, chosen)
        results = {r["check_id"]: r for r in assy["results"]}
        self.assertTrue(results["bbox"]["passed"], results["bbox"]["evidence"])
        arr = assy["arrange"]
        self.assertTrue(arr["filtered"], arr)
        for f in arr["filtered"]:
            self.assertGreater(lengths[f["assignment"]["module_1"]], short, f)
            self.assertIn("bbox", f["failing"], f)
        scored = [c for c in arr["candidates"] if c["outcome"] in ("scored", "filtered")]
        self.assertEqual(arr["prescored"], len(scored))
        for c in scored:                        # every long-side Pico candidate was removed, every short-end one kept
            long_side = lengths[c["assignment"]["module_1"]] > short
            self.assertEqual(c["outcome"], "filtered" if long_side else "scored", c)
        self.assertTrue(arr["decision"].startswith("prescore+"), arr["decision"])
        self.assertTrue(chosen["by"].startswith("prescore+"), chosen)

    def test_prescore_ties_go_to_the_controller(self):
        # E1-01 (iteration 003 replay): every feasible candidate measures 0 controllable failures, so nothing is filtered
        # and the decision equals the vote + rank decision of iterations 003-007
        st, llm, status = self.arrange(script_for("E1-01", assy_edge=ITER003_EDGE_VOTES), iter003_table())
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        self.assertEqual(st.arrange["filtered"], [])
        self.assertEqual(st.arrange["decision"], "llm:vote+rank")
        self.assertEqual(st.choices["arrangement_confirmed"]["value"], {"module_1": "-X", "connector_1": "+X"})
        scored = [c for c in st.arrange["candidates"] if c["outcome"] == "scored"]
        self.assertEqual(st.arrange["prescored"], len(scored))
        for c in scored:
            self.assertEqual(c["prescore"]["failing"], [], c)
            self.assertEqual(c["prescore"]["key"]["hard_failures"], 0, c)

    def placed_candidates(self):
        """The E1-01 state after ChooseStack (plus the board screw) and ArrangeContents' feasible candidates."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = new_design("E1-01", Path(tmp.name))
        llm = FakeLLM(script_for("E1-01", assy_edge=ITER003_EDGE_VOTES))
        status, _ = run_stages(d, llm, "ChooseStack")
        self.assertEqual(status, ca.Status.SUCCESS)
        st = d.assy
        board_item = next(i for i in st.contents if i["kind"] == "board")
        board_inst = st.catalog.instantiate(board_item["part"], board_item["params"])
        screw = A.board_screw(st.catalog, board_inst, st.rules.values)
        st.fasteners.update(A.fastener_values("board", screw))
        board = lay.Placed("board", board_item["part"], dict(board_item["params"]), 0.0, 0.0, 0.0, 0.0, "",
                           role="board", inst=board_inst)
        placer = lay.Placer(st.catalog, board, st.rules.values, A.hole_column_d(st, board_inst), st.spec["keepout_above"])
        got = A.ArrangeContents(d, llm).candidates(st, placer)
        return st, placer, got["cands"]

    def test_prescore_is_pure(self):
        st, placer, cands = self.placed_candidates()
        before = copy.deepcopy((st.choices, st.notes, st.assumptions, st.coverage, st.fasteners, st.history))
        first = A.prescore(st, cands[0], placer)
        self.assertIsNone(st.graph)
        self.assertIsNone(st.placed)
        self.assertEqual((st.choices, st.notes, st.assumptions, st.coverage, st.fasteners, st.history), before)
        self.assertEqual(A.prescore(st, cands[0], placer)["key"], first["key"])
        self.assertIsNone(first["error"])
        # changed in iteration 010 (behaviour intentionally changed, C4 / C5): the Pico is on the grid and the jacks are
        # exempt, so grid_conformance is measured and passes (it was an uncontrollable typed conflict)
        self.assertIn("grid_conformance", first["checked"])
        self.assertNotIn("grid_conformance", first["failing"] + first["uncontrollable"])
        self.assertTrue(any(c.startswith("plug_refs_") for c in first["checked"]))      # iteration 010 (C5)
        self.assertTrue(any(c.startswith("pilot_band_") for c in first["checked"]))     # iteration 010 (C6)
        # iteration 009 (C1): the ligament checks are part of the prescore's controllable error
        self.assertTrue(any(c.startswith("ligament_") for c in first["checked"]))
        self.assertTrue(set(first["failing"]) | set(first["uncontrollable"]) <= set(first["checked"]))

    def test_single_survivor_is_a_rule_decision(self):
        target = {"module_1": "-X", "connector_1": "-Y"}       # feasible, but not the vote winner

        def fake(st, cand, placer):
            ok = cand["assignment"] == target
            return {"key": {"hard_failures": 0 if ok else 1, "violation": 0.0 if ok else 1.0, "soft": 0.0},
                    "failing": [] if ok else ["bbox"], "uncontrollable": [], "error": None}

        with mock.patch.object(A, "prescore", fake):
            st, llm, status = self.arrange(script_for("E1-01", assy_edge=ITER003_EDGE_VOTES), iter003_table())
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        conf = st.choices["arrangement_confirmed"]
        self.assertEqual((conf["value"], conf["by"]), (target, "rule:prescore"))
        self.assertEqual(st.arrange["decision"], "rule:prescore")
        self.assertNotIn("assy_confirm", llm.labels())
        self.assertNotIn("assy_arrange_pick", llm.labels())
        used = {k[5:-1]: v for k, v in st.choices.items() if k.startswith("edge[")}
        self.assertEqual({k: v["value"] for k, v in used.items()}, target)
        self.assertTrue(all(v["by"] == "rule:prescore" for v in used.values()))
        self.assertEqual(len(st.arrange["filtered"]), st.arrange["prescored"] - 1)
        self.assertTrue(all(f["failing"] == ["bbox"] for f in st.arrange["filtered"]))


class TestRender(unittest.TestCase):
    def test_assembly_views_are_derived_and_distinct(self):
        # iteration 008 (C3, RC-804): the elevations look down by rules.view_elevation_deg; iso / top are unchanged
        rules = pt.load_rules(RULES_PATH).values
        views = A.assembly_views(rules)
        self.assertEqual(set(views), set(ca.VIEWS))
        for k, v in ca.VIEWS.items():
            got = list(views[k])
            if k in A.ELEVATION_VIEWS:
                self.assertAlmostEqual(got[A.VIEW_ROTX], v[A.VIEW_ROTX] - rules["view_elevation_deg"])
                got[A.VIEW_ROTX] = v[A.VIEW_ROTX]
            self.assertEqual(tuple(got), tuple(v), k)
        self.assertEqual(views["iso"], ca.VIEWS["iso"])
        self.assertEqual(views["top"], ca.VIEWS["top"])
        self.assertGreater(rules["view_elevation_deg"], 0)


class TestGridFeasibility(unittest.TestCase):
    """iteration 006 (C2, RC-603, ARCHITECTURE.md 7.9): the grid sensor says whether any position could pass,
    from the pins and the pitch only. Fixture numbers live in the tests, never in layout.py."""
    PITCH = 2.54
    LIMIT = 0.15

    def wrap(self, v):
        return (np.asarray(v, dtype=float) + self.PITCH / 2) % self.PITCH - self.PITCH / 2

    def test_lattice_pattern_with_any_offset_fits_and_the_shift_recovers_it(self):
        p = self.PITCH
        offset = np.array([0.731, -1.093])
        pins = np.array([[0, 0], [p, 0], [3 * p, p], [5 * p, 7 * p], [-2 * p, 4 * p]]) + offset
        f = lay.grid_feasibility(pins, p, (0, 1), limit=self.LIMIT, step=0.01)
        self.assertLessEqual(f["best_any"], 1e-6)
        np.testing.assert_allclose(self.wrap(np.asarray(f["any_shift"]) + offset), [0, 0], atol=1e-6)
        # changed in iteration 010 (grid_kind's signature: best_free no longer decides a kind)
        self.assertEqual(lay.grid_kind(float(np.max(np.linalg.norm(self.wrap(pins), axis=1))), f["best_any"],
                                       self.LIMIT), "tangential")

    def test_off_lattice_pattern_is_a_pin_pattern_conflict(self):
        # spacings 3.0 and 4.0 mm (fixture numbers): no translation puts every pin on a 2.54 lattice
        pins = np.array([[0.0, 0.0], [3.0, 0.0], [7.0, 0.0], [8.0, 4.8]])
        f = lay.grid_feasibility(pins, self.PITCH, (1,), limit=self.LIMIT, step=0.01)
        ref = brute_feasibility(pins, self.PITCH, free_axis=1)
        self.assertAlmostEqual(f["best_any"], ref["best_any"], delta=0.01)
        self.assertLessEqual(f["best_any"], ref["best_any"] + 1e-9)        # the refined search is never worse
        self.assertAlmostEqual(f["best_free"], ref["best_free"], delta=0.01)
        self.assertGreater(f["best_any"], self.LIMIT)
        self.assertIsNone(f["normal_needed"])
        residual = float(np.max(np.linalg.norm(self.wrap(pins), axis=1)))
        self.assertEqual(lay.grid_kind(residual, f["best_any"], self.LIMIT), "pin_pattern")      # signature: iteration 010

    def test_normal_offset_is_flush_to_edge_with_the_needed_move(self):
        p = self.PITCH
        pins = np.array([[0, 0], [0, p], [0, 4 * p], [p, 2 * p]]) + np.array([0.4 * p, 0.3])
        f = lay.grid_feasibility(pins, p, (1,), limit=self.LIMIT, step=0.01)   # free: Y (the edge tangent)
        self.assertLessEqual(f["best_any"], 1e-6)
        self.assertAlmostEqual(f["best_free"], 0.4 * p, delta=1e-6)
        self.assertAlmostEqual(f["normal_needed"], 0.4 * p - self.LIMIT, delta=1e-6)
        self.assertAlmostEqual(f["normal_shift"], -(0.4 * p - self.LIMIT), delta=1e-6)
        # changed in iteration 010 (flush_to_edge retired, L2.1.3): a reachable pattern left off the grid is a placement
        # bug (tangential), or grid_extent / blocked when the finite grid or a collision is the reason
        self.assertEqual(lay.grid_kind(f["best_free"], f["best_any"], self.LIMIT), "tangential")
        self.assertEqual(lay.grid_kind(f["best_free"], f["best_any"], self.LIMIT, extent_ok=False), "grid_extent")
        self.assertEqual(lay.grid_kind(f["best_free"], f["best_any"], self.LIMIT, blocked=True), "blocked")
        # past half a pitch the nearer lattice line is on the other side (wrap-around)
        pins2 = np.array([[0, 0], [0, p]]) + np.array([0.7 * p, 0.0])
        f2 = lay.grid_feasibility(pins2, p, (1,), limit=self.LIMIT, step=0.01)
        self.assertAlmostEqual(f2["normal_needed"], 0.3 * p - self.LIMIT, delta=1e-6)

    def test_minimax_snap_beats_first_pin_snap(self):
        cat, rules, placer = placer_for("E1-01")
        origin, p = placer.grid
        rel = np.array([[0.0, 1.0], [0.0, p], [0.0, 2 * p], [0.0, 4 * p]]) + np.array([0.0, 0.37])   # pin 0 is the outlier
        pins = [np.array([origin[0] + x, origin[1] + y, 0.0]) for x, y in rel]
        module = lay.Placed("m_1", "fixture", {}, 0, 0, 0, 0, "m", edge="+X")
        tangent = placer.edges["+X"]["tangent"]

        def worst(shift):
            return max(float(np.linalg.norm(self.wrap(np.asarray(q[:2]) - origin[:2] + shift[:2]))) for q in pins)

        with mock.patch.object(placer, "pins", lambda _p: pins):
            d = placer.grid_shift(module, tangent)
        first = np.zeros(3)
        first[tangent] = -self.wrap(rel[0])[tangent]
        best_free = lay.grid_feasibility(rel, p, (tangent,), step=rules["grid_search_step"])["best_free"]
        self.assertLess(worst(d), worst(first) - 1e-3)
        self.assertAlmostEqual(worst(d), best_free, delta=1e-9)
        self.assertLessEqual(abs(d[tangent]), p / 2 + 1e-9)
        self.assertEqual(d[1 - tangent], 0.0)


def edge_words(cat, rid):
    w, d, _, _ = request_numbers(rid)
    return {s: e["words"] for s, e in lay.board_edges(cat.instantiate("perfboard", {"width": w, "depth": d})).items()}


def connector_names(cat):
    return tuple(cat.get(pid).data["connectors"][0]["name"] for pid in ("rpi_pico2", "jack_3p5_pj320a"))


# iteration 003's recorded controller answers (iter_003/target_s0/*/llm/010-024)
ITER003_EDGE_VOTES = [{"module_1": "-X", "connector_1": "+X"}] * 2 + [{"module_1": "-X", "connector_1": "-X"}]
ITER003_P_YES = {("+X", "-X"): 0.230, ("-X", "+X"): 0.199, ("-Y", "-X"): 0.117, ("+Y", "+X"): 0.113,
                 ("+Y", "-X"): 0.110, ("-X", "-Y"): 0.106, ("+X", "-Y"): 0.103, ("-Y", "-Y"): 0.096,
                 ("-X", "+Y"): 0.096, ("-Y", "+X"): 0.092, ("+X", "+Y"): 0.092, ("+Y", "+Y"): 0.081}


def iter003_table():
    cat = pt.Catalog.load(PARTS)
    words = edge_words(cat, "E1-01")
    usb, jack = connector_names(cat)
    return [((f"({usb}) faces {words[m]}", f"({jack}) face {words[c]}"), p) for (m, c), p in ITER003_P_YES.items()]


class TestSymmetry(unittest.TestCase):
    ROT180 = {"-X": "+X", "+X": "-X", "-Y": "+Y", "+Y": "-Y"}
    IDENTITY = {s: s for s in lay.SIDES}

    def board(self, w, d, catalog=None):
        return (catalog or pt.Catalog.load(PARTS)).instantiate("perfboard", {"width": w, "depth": d})

    def test_request_sized_perfboards_have_the_half_turn(self):
        tol = pt.load_rules(RULES_PATH).values["measure_tol"]
        for rid in ("E1-01", "V1"):
            with self.subTest(rid=rid):
                w, d, _, _ = request_numbers(rid)
                notes = []
                syms = lay.board_symmetries(self.board(w, d), tol, notes)
                self.assertEqual(syms, [self.IDENTITY, self.ROT180])
                # changed in iteration 010 (C1): the measured grid is centred and finite, so the half turn maps its hole
                # set onto itself: nothing to report (it was a soft hole-1 grid whose mismatch was noted)
                self.assertEqual(notes, [])

    def test_moved_hole_or_hard_grid_leaves_only_the_identity(self):
        # changed in iteration 010 (C1, ported to the finite grid): the measured grid is centred, so the "hard grid"
        # fixture is now an off-centre finite grid (shifted by a fixture 1 mm, its self-checks dropped). Hard, it leaves
        # only the identity; declared soft, the half turn is kept and the mismatch is noted
        tol = pt.load_rules(RULES_PATH).values["measure_tol"]
        w, d, _, _ = request_numbers("E1-01")
        for variant in ("moved_hole", "hard_grid", "soft_grid"):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as tmp:
                data = json.loads((PARTS / "perfboard" / "part.json").read_text())
                if variant == "moved_hole":
                    data["datums"]["HOLE"]["at"][3][0] = "width - hole_inset - 1"
                    data["self_checks"] = [c for c in data["self_checks"] if "pitch" not in c["name"]]
                else:
                    data["grid"]["origin"][0] = f"({data['grid']['origin'][0]}) + 1"
                    data["self_checks"] = [c for c in data["self_checks"] if "grid" not in c["name"]]
                    if variant == "soft_grid":
                        data["grid"]["soft"] = True
                (Path(tmp) / "perfboard").mkdir()
                (Path(tmp) / "perfboard" / "part.json").write_text(json.dumps(data))
                notes = []
                syms = lay.board_symmetries(self.board(w, d, pt.Catalog.load(tmp)), tol, notes)
                if variant == "soft_grid":
                    self.assertEqual(syms, [self.IDENTITY, self.ROT180])
                    self.assertTrue(notes)
                else:
                    self.assertEqual(syms, [self.IDENTITY])

    def test_square_board_gets_four_rotations_and_classes_are_canonical(self):
        # changed in iteration 010 (C1): the measured board keeps its edge-pad column on the X edges only, so a square
        # board's grid has more rows than columns and only the half turn maps its hole set onto itself; a fixture board
        # with equal margins (test-only data) gets all four rotations
        tol = pt.load_rules(RULES_PATH).values["measure_tol"]
        w, _, _, _ = request_numbers("E1-01")
        self.assertEqual(lay.board_symmetries(self.board(w, w), tol), [self.IDENTITY, self.ROT180])
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads((PARTS / "perfboard" / "part.json").read_text())
            data["params"]["grid_margin_y"]["default"] = data["params"]["grid_margin_x"]["default"]
            (Path(tmp) / "perfboard").mkdir()
            (Path(tmp) / "perfboard" / "part.json").write_text(json.dumps(data))
            syms = lay.board_symmetries(self.board(w, w, pt.Catalog.load(tmp)), tol)
        self.assertEqual(len(syms), 4)
        self.assertIn(self.ROT180, syms)
        self.assertTrue(all(sorted(m.values()) == sorted(lay.SIDES) for m in syms))
        for a in ({"m": "-X", "c": "+X"}, {"m": "-Y", "c": "-Y"}, {"m": "+X", "c": "-Y"}):
            key = lay.canonical_class(a, syms)
            images = [{k: m[v] for k, v in a.items()} for m in syms]
            self.assertTrue(all(lay.canonical_class(b, syms) == key for b in images))   # invariant over a class
            self.assertEqual(lay.canonical_class(dict(key), syms), key)                 # idempotent
        # no symmetries given: every assignment is its own class
        self.assertNotEqual(lay.canonical_class({"m": "-X"}, []), lay.canonical_class({"m": "+X"}, []))


# ---------------------------------------------------------------------------
# DeriveFeatures
# ---------------------------------------------------------------------------


def derived(rid: str, root: Path, **spec_override):
    d = new_design(rid, root)
    status, child = run_stages(d, FakeLLM(script_for(rid)), "DeriveFeatures")
    assert status == ca.Status.SUCCESS, d.assy.notes
    st = d.assy
    if spec_override:
        st.spec.update(spec_override)
    return st, A.resolve(st)


def measure_manifold(rid: str, root: Path, rules_path: Path = RULES_PATH):
    """Derive a request with the scripted controller, build the manifold bodies and run the rule-derived
    check plan on them (no OpenSCAD, no package). Returns (state, {check id: result})."""
    d = new_design(rid, root, rules_path=rules_path)
    status, _ = run_stages(d, FakeLLM(script_for(rid)), "DeriveFeatures")
    assert status == ca.Status.SUCCESS, d.assy.notes
    st = d.assy
    st.resolved = A.resolve(st)
    st.solids = {b: fg.body_solid(st.graph, b, st.resolved) for b in st.graph.bodies()}
    st.plan = A.build_plan(st)
    return st, {r.check_id: r for r in ac.run_plan(st.plan, st.solids)}


class TestDeriveFeatures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_port_cuts_follow_the_layout(self):
        for rid, expected in (("E1-01", {"-X": 1, "+X": 2}), ("V1", {"-X": 2})):
            with self.subTest(rid=rid):
                st, res = derived(rid, self.root / rid)
                cuts = [n for n in st.graph if n.role == "port_cut"]
                per_wall = {}
                for n in cuts:
                    per_wall[n.wall] = per_wall.get(n.wall, 0) + 1
                self.assertEqual(per_wall, expected)
                exposed = sum(it.quantity for it in st.items if it.exposed)
                self.assertEqual(len(cuts), exposed)

    def test_standoffs_pilots_lid_and_bosses(self):
        st, res = derived("E1-01", self.root)
        board = st.placed.get("board")
        holes = lay.world_datum(board, "HOLE").at
        bottom = lay.world_datum(board, "BOTTOM").at[2]
        standoffs = [n for n in st.graph if n.role == "standoff"]
        self.assertEqual(len(standoffs), len(holes))
        for n, h in zip(standoffs, holes):
            pose = res.poses[n.id][:3, 3]
            self.assertLessEqual(np.linalg.norm(pose[:2] - np.asarray(h[:2])), 1e-6)
            self.assertAlmostEqual(pose[2] + res.params[n.id]["h"], bottom, places=9)
            pilot = res.params[f"{n.id}_pilot"]
            self.assertGreaterEqual(pilot["depth"], st.fasteners["fastener.board.min_engagement"])
        cav, lip = res.params["cavity"], res.params["lid_lip"]
        r = st.rules.values
        gap = (cav["x"] - lip["x"]) / 2
        self.assertAlmostEqual(gap, r["sliding_fit"], places=9)
        self.assertTrue(r["sliding_fit_min"] <= gap <= r["sliding_fit_max"])
        ko_top = res.poses["board_ko_top"][2, 3] + res.params["board_ko_top"]["z"]
        self.assertGreaterEqual(lip["bottom"], ko_top - 1e-9)
        for k in range(1, 5):
            boss = res.poses[f"boss_{k}"][:3, 3]
            hole = res.poses[f"boss_{k}_lid_hole"][:3, 3]
            self.assertLessEqual(np.linalg.norm(boss[:2] - hole[:2]), 1e-9)

    def test_cavity_clears_the_hole_keepout_columns(self):
        # iteration 004 (C1, D1): every plan keep-out column bounds the cavity, with the design margin
        for rid in ("E1-01", "V1"):
            with self.subTest(rid=rid):
                st, res = derived(rid, self.root / rid)
                cav, r = res.params["cavity"], st.rules.values
                holes = lay.world_datum(st.placed.get("board"), "HOLE").at
                self.assertEqual(len(holes), 4)
                for k, h in enumerate(holes):
                    ko = res.params[f"hole_ko_{k}"]["d"]
                    need = max(ko, r["driver_diameter"]) / 2 + r["design_margin"] - 1e-9
                    for dist in (h[0] - cav["x0"], cav["x1"] - h[0], h[1] - cav["y0"], cav["y1"] - h[1]):
                        self.assertGreaterEqual(dist, need, (k, dist))
                        self.assertGreaterEqual(dist, ko / 2 + r["design_margin"] - 1e-9)

    def test_no_dead_envelopes(self):
        # iteration 004 (RC-401): every envelope bounds the cavity, feeds a plan check, or is cut through by a port
        for rid in ("E1-01", "V1"):
            with self.subTest(rid=rid):
                st, res = derived(rid, self.root / rid)
                st.resolved = res
                plan = A.build_plan(st)
                fed = set()
                for spec in plan.specs:
                    for key in ("volume", "minus"):
                        fed |= set(plan.sources.get(spec["args"].get(key), []))
                cav_exprs = " ".join(str(v) for v in st.graph.nodes["cavity"].params.values())
                crossed = {c for n in st.graph if n.role == "port_cut" for c in n.crossing}
                envelopes = [n for n in st.graph if n.kind == "envelope" and n.role != "cavity"]
                self.assertTrue(envelopes)
                for n in envelopes:
                    self.assertIn(n.role, A.KEEP_OUTS, n.id)
                    row = A.KEEP_OUTS[n.role]
                    bounds = (row.get("plan") == "self" and f"{n.id}.d" in cav_exprs) or \
                             (row.get("plan") not in (None, "self") and row["plan"] in cav_exprs
                              and n.pose.at in cav_exprs)
                    self.assertTrue(bounds or n.id in fed or n.id in crossed, f"dead envelope {n.id} ({n.role})")
                for role in ("hole_keepout", "driver"):
                    ids = [n.id for n in envelopes if n.role == role]
                    self.assertEqual(len(ids), 4, role)
                    for nid in ids:
                        self.assertIn(f"clear_{nid}", [sp["id"] for sp in plan.specs])
                driver = next(sp for sp in plan.specs if sp["id"] == "clear_driver_0")
                self.assertEqual(driver["args"]["bodies"], ["base"])
        # an envelope role without a KEEP_OUTS row is a typed error, never silently ignored
        st.graph.add(fg.Node("orphan", "envelope", "box", {"x": 1, "y": 1, "z": 1}, role="mystery"))
        st.resolved = A.resolve(st)
        with self.assertRaises(ValueError):
            A.build_plan(st)

    def test_minus_is_grown_by_the_check_clearance(self):
        # iteration 005 (RC-501): every exemption on a check with clearance c > 0 is its nodes grown by c
        for rid in ("E1-01", "V1"):
            with self.subTest(rid=rid):
                st, res = derived(rid, self.root / rid)
                st.resolved = res
                plan = A.build_plan(st)
                poly = 1 / math.cos(math.pi / res.segments())
                grown = 0
                for sp in plan.specs:
                    a = sp["args"]
                    if sp["type"] not in ("clear_of", "inside") or not a.get("minus"):
                        continue
                    c = a["clearance"]
                    if c <= 0:
                        self.assertEqual(a["minus"], "seats", sp["id"])
                        self.assertNotIn("minus_grown_by", a)
                        continue
                    base = a["minus"].rsplit("@", 1)[0]
                    self.assertEqual(a["minus"], f"{base}@{c:g}", sp["id"])
                    self.assertEqual(a["minus_grown_by"], c)
                    self.assertEqual(plan.sources[a["minus"]], plan.sources[base])
                    self.assertTrue(plan.sources[base])
                    b0 = np.asarray(plan.volumes[base].bounding_box())
                    b1 = np.asarray(plan.volumes[a["minus"]].bounding_box())
                    # changed in iteration 010: the grown exemption is an inscribed fn-gon (vertex radius d/2 + c, errs
                    # against the design) while the ungrown seat envelope stays circumscribed (vertex radius d/2 / cos)
                    r = max(res.params[i]["d"] for i in plan.sources[base]) / 2
                    grow = r + c - r * poly
                    np.testing.assert_allclose(b0[:2] - b1[:2], grow, atol=1e-6)
                    np.testing.assert_allclose(b1[3:5] - b0[3:5], grow, atol=1e-6)
                    self.assertLess(grow, c)
                    self.assertAlmostEqual(b0[2] - b1[2], c, places=6)
                    self.assertAlmostEqual(b1[5] - b0[5], c, places=6)
                    grown += 1
                self.assertEqual(grown, 2)               # clear_board and inside_board
                ko = next(sp for sp in plan.specs if sp["id"] == "clear_keepout_bottom")
                self.assertEqual(ko["args"]["minus"], "seats")
                board = next(sp for sp in plan.specs if sp["id"] == "clear_board")
                seat_d = res.params["seat_0"]["d"] + 2 * st.spec["board_clearance"]
                self.assertIn(f"Ø {seat_d:g}", board["text"])

    def test_composite_checks_report_per_source(self):
        # iteration 005 (RC-503): decomposable reports; the carrier and its contents are separate checks
        for rid in ("E1-01", "V1"):
            with self.subTest(rid=rid):
                st, got = measure_manifold(rid, self.root / rid)
                plan, g = st.plan, st.graph
                ids = [sp["id"] for sp in plan.specs]
                self.assertNotIn("inside_references", ids)
                self.assertIn("inside_board", ids)
                self.assertIn("inside_contents", ids)
                board = st.placed.get("board").node_id
                self.assertEqual(plan.sources["board"], [board])
                refs = {n.id for n in g.references()}
                self.assertEqual(set(plan.sources["contents"]), refs - {board})
                composite = 0
                for sp in plan.specs:
                    if sp["type"] not in ("clear_of", "inside"):
                        continue
                    srcs = plan.sources[sp["args"]["volume"]]
                    ev = got[sp["id"]].evidence
                    self.assertEqual(set(ev["volume_parts"]), set(srcs), sp["id"])
                    for nid, part in ev["volume_parts"].items():
                        self.assertEqual(part, g.nodes[nid].part or g.nodes[nid].role, (sp["id"], nid))
                    if len(srcs) < 2:
                        self.assertNotIn("per_source", ev, sp["id"])
                        continue
                    composite += 1
                    self.assertEqual(set(ev["per_source"]), set(srcs), sp["id"])
                    ds = [v["d"] for v in ev["per_source"].values() if v["d"] is not None]
                    self.assertAlmostEqual(ev["d"], min(ds), delta=1e-6, msg=sp["id"])
                env = next(sp for sp in plan.specs if sp["id"] == "clear_module_1_1_envelope")
                self.assertEqual(env["type"], "inside")
                parts = {g.nodes[i].part for i in plan.sources["module_1_1_envelope"]}
                self.assertEqual(parts, {st.placed.get("module_1_1").inst.part_id} |
                                 {q.inst.part_id for q in st.placed.placed if q.of == "module_1_1"})
                self.assertGreaterEqual(composite, 1 + 1 + sum(1 for _ in A.exposed_connectors(st)))

    def test_hole_keepout_check_is_not_vacuous(self):
        # the sensor sees the iteration 004 defect (hole terms removed from the cavity) and passes the fix
        r = pt.load_rules(RULES_PATH).values
        with mock.patch.dict(A.KEEP_OUTS["hole_keepout"], {"plan": None}):
            _, bad = measure_manifold("E1-01", self.root / "bad")
        _, good = measure_manifold("E1-01", self.root / "good")
        for k in range(4):
            cid = f"clear_hole_ko_{k}"
            self.assertFalse(bad[cid].passed, cid)
            self.assertGreater(bad[cid].evidence["penetration_mm3"], 0)
            where = bad[cid].evidence["where"]
            self.assertEqual((len(where), len(where[0]), len(where[1])), (2, 3, 3))
            self.assertTrue(good[cid].passed, good[cid].evidence)
            self.assertGreaterEqual(good[cid].margin, r["design_margin"] - r["measure_tol"])
            self.assertTrue(good[f"clear_driver_{k}"].passed, good[f"clear_driver_{k}"].evidence)

    def test_clearances_have_the_design_margin(self):
        # iteration 004 (C2): every one-sided clearance is derived at limit + design_margin; with the margin set to
        # 0 the zero-margin gaps of iteration 004 come back, so the rule is the only cause
        r = pt.load_rules(RULES_PATH).values
        m, tol = r["design_margin"], r["measure_tol"]
        zero_rules = test_rules(self.root, design_margin=0.0)
        for rid in ("E1-01", "V1"):
            with self.subTest(rid=rid):
                st, got = measure_manifold(rid, self.root / rid)
                _, zero = measure_manifold(rid, self.root / f"{rid}_0", rules_path=zero_rules)
                seg = st.resolved.segments()
                for cid, res in got.items():
                    if res.type not in ("clear_of", "inside"):
                        continue
                    ev = res.evidence
                    gap = ev["gap"] if res.type == "clear_of" else min(ev["gap_to_solids"], ev["gap_to_outside"])
                    spec = next(sp for sp in st.plan.specs if sp["id"] == cid)
                    # a round envelope is a circumscribed polygon: its vertices reach this far past d/2
                    allow = max([st.resolved.params[n]["d"] / 2 * (1 / math.cos(math.pi / seg) - 1)
                                 for n in st.plan.sources.get(spec["args"]["volume"], [])
                                 if n in st.graph.nodes and st.graph.nodes[n].primitive == "cylinder"
                                 and st.graph.nodes[n].kind == "envelope"] or [0.0])
                    self.assertGreaterEqual(gap, ev["clearance"] + m - tol - allow, cid)
                # changed in iteration 010 (C3): the Ø7 columns moved out with the measured holes, so the cavity is wider
                # than the board and the lid lip no longer sits over the board footprint: clear_keepout_top's gap is a
                # plan distance now, not a setpoint gap (it is still >= clearance + margin, asserted above)
                zero_margin = ["clear_keepout_bottom"] + [cid for cid in got if cid.startswith("clear_") and cid.endswith("_plug")]
                for cid in zero_margin:
                    lim = got[cid].evidence["clearance"]
                    self.assertAlmostEqual(zero[cid].evidence["gap"], lim, delta=1e-6, msg=cid)
                    self.assertAlmostEqual(got[cid].evidence["gap"] - zero[cid].evidence["gap"], m, delta=1e-6, msg=cid)
                # the opening is the plug plus (plug_to_opening + design_margin) per side, inside the oversize limit
                for cid, res in got.items():
                    if res.type == "aperture_oversize":
                        self.assertTrue(res.passed, res.evidence)

    def test_one_sided_minimums_have_the_design_margin(self):
        # iteration 006 (C3, RC-604): pilot depths, boss/standoff ODs and the lip engagement are derived at
        # limit + design_margin; with the margin 0 they equal their limits; the checks stay at the limits
        # changed in iteration 009 (behaviour intentionally changed, RC-902): the lid boss is sized by the opening it
        # carries too, so its OD is max(min_boss_od + m, pilot + 2 wall, clearance + 2 (min_ligament + m))
        r = pt.load_rules(RULES_PATH).values
        m = r["design_margin"]
        zero_rules = test_rules(self.root, design_margin=0.0)

        def minimums(st, res):
            """key -> (value, [candidate targets as a function of the margin]); the value is their max."""
            f = st.fasteners
            out = {}
            for n in st.graph:
                use = {"standoff": "board", "boss": "lid"}.get(n.role)
                if use is None:
                    continue
                wall = r["standoff_wall_min"] if use == "board" else r["boss_wall_min"]
                lim, floor = f[f"fastener.{use}.min_boss_od"], f[f"fastener.{use}.pilot_diameter"] + 2 * wall
                depth = f[f"fastener.{use}.min_engagement"]
                out[f"{n.id}.depth"] = (res.params[f"{n.id}_pilot"]["depth"], lambda mm, x=depth: [x + mm])
                cands = (lambda mm, a=lim, b=floor: [a + mm, b]) if use == "board" else \
                    (lambda mm, a=lim, b=floor, c=f["fastener.lid.clearance_diameter"]:
                     [a + mm, b, c + 2 * (r["min_ligament"] + mm)])
                out[f"{n.id}.d"] = (res.params[n.id]["d"], cands)
            lip = res.params["lid_lip"]
            out["lip"] = (res.params["base"]["split"] - lip["bottom"], lambda mm: [r["lip_engagement"] + mm])
            return out

        for rid in ("E1-01", "V1"):
            with self.subTest(rid=rid):
                st, res = derived(rid, self.root / rid)
                d0 = new_design(rid, self.root / f"{rid}_0", rules_path=zero_rules)
                status, _ = run_stages(d0, FakeLLM(script_for(rid)), "DeriveFeatures")
                self.assertEqual(status, ca.Status.SUCCESS)
                res0 = A.resolve(d0.assy)
                got, zero = minimums(st, res), minimums(d0.assy, res0)
                self.assertEqual(len(got), 2 * 8 + 1)
                for key, (v, cands) in got.items():
                    self.assertAlmostEqual(v, max(cands(m)), delta=1e-6, msg=key)
                    self.assertAlmostEqual(zero[key][0], max(cands(0.0)), delta=1e-6, msg=key)
                f = st.fasteners
                lig = f["fastener.lid.clearance_diameter"] + 2 * (r["min_ligament"] + m)
                for k in range(1, 5):          # the lid boss OD is the ligament term round the clearance hole
                    self.assertAlmostEqual(got[f"boss_{k}.d"][0], lig, delta=1e-6)
                    self.assertAlmostEqual(got[f"boss_{k}.d"][0] - zero[f"boss_{k}.d"][0], 2 * m, delta=1e-6)
                # the lip bottom stays on the cavity top; the split sits engagement + design_margin above it
                for rr in (res, res0):
                    self.assertAlmostEqual(rr.params["lid_lip"]["bottom"], rr.params["cavity"]["z1"], delta=1e-9)
                self.assertAlmostEqual((res.params["base"]["split"] - res.params["cavity"]["z1"])
                                       - (res0.params["base"]["split"] - res0.params["cavity"]["z1"]), m, delta=1e-9)
                # standoff pilots still leave the floor under them (pilot_depth keeps its limit)
                for n in st.graph:
                    if n.role == "standoff":
                        self.assertLessEqual(res.params[f"{n.id}_pilot"]["depth"],
                                             res.params[n.id]["height"] + res.params["base"]["floor"] - r["min_feature"])

    def test_minimum_checks_pass_with_margin_and_fail_on_a_mutant(self):
        # iteration 006 (C3): the agent senses the one-sided minimums the judges flagged; non-vacuous
        # changed in iteration 009 (behaviour intentionally changed, RC-902): the lid boss's binding minimum moved from
        # min_boss_od to the ligament round its clearance hole, so with design_margin -0.2 boss_od_boss_* passes
        # (d = clearance + 2 (min_ligament - 0.2) >= min_boss_od) and ligament_boss_*_lid_hole_lid fails instead
        r = pt.load_rules(RULES_PATH).values
        neg_rules = test_rules(self.root, design_margin=-0.2)
        st, got = measure_manifold("E1-01", self.root / "good")
        _, bad = measure_manifold("E1-01", self.root / "bad", rules_path=neg_rules)
        ids = [c for c in got if c.startswith(("pilot_engagement_", "boss_od_", "lip_engagement"))]
        self.assertEqual(len(ids), 2 * 8 + 1)
        for cid in ids:
            self.assertTrue(got[cid].passed, got[cid].evidence)
            self.assertGreaterEqual(got[cid].margin, r["design_margin"] - 1e-9, cid)
        lid_ligaments = [c for c in got if c.startswith("ligament_boss_") and c.endswith("_lid_hole_lid")]
        # changed in iteration 010 (behaviour intentionally changed, C2): with the M2 board screw the standoff OD is set
        # by min_boss_od (pilot 1.7 + 2 x 1.6 = 4.9 < 5.0), so boss_od_standoff_* fails on the mutant too
        standoff_od = [c for c in ids if c.startswith("boss_od_standoff_")]
        must_fail = [c for c in ids if c.startswith("pilot_engagement_") or c == "lip_engagement"] + lid_ligaments + \
            standoff_od
        self.assertEqual(len(must_fail), 8 + 4 + 1 + 4)
        for cid in must_fail:
            self.assertFalse(bad[cid].passed, (cid, bad[cid].evidence))
        # the lid boss OD is set by the ligament round its clearance hole, so it passes either way
        self.assertTrue(all(bad[c].passed for c in ids if c.startswith("boss_od_boss_")))

    def test_every_opening_has_a_ligament_check(self):
        # iteration 009 (C1, RC-901): every cut in APERTURE_CUT_ROLES has its ligament check, in the body it opens
        r = pt.load_rules(RULES_PATH).values
        for rid in ("E1-01", "V1"):
            with self.subTest(rid=rid):
                st, got = measure_manifold(rid, self.root / rid)
                g, res = st.graph, st.resolved
                specs = {sp["id"]: sp for sp in st.plan.specs if sp["type"] == "ligament"}
                pairs = {(sp["args"]["cut"], sp["args"]["body"]) for sp in specs.values()}
                openings = [n for n in g if n.kind == "cut" and n.role in A.APERTURE_CUT_ROLES]
                self.assertTrue(openings)
                # one check per opening, no more
                self.assertEqual(len(specs), len(openings))
                # expected pairs come from the role alone (lid holes open the lid; pilots and port cuts the base),
                # not from the plan or from n.body, so this equality is a real test of add_ligament_checks
                role_body = {"screw_hole": "lid"}
                expected = {(n.id, role_body.get(n.role, "base")) for n in openings}
                self.assertEqual(pairs, expected)
                # every planned pair really opens material: the grown cut meets that body (no filter on n.body)
                touched = {n.id: {b for b in st.solids
                                  if float((fg.grown_solid(n, res, r["measure_tol"]) ^ st.solids[b]).volume())
                                  > r["interference_max"]} for n in openings}
                for c, b in pairs:
                    self.assertIn(b, touched[c], (c, b, touched[c]))
                # the only other body a cut reaches is the documented departure (ledger 009, deviation 1): a lid
                # hole's overrun into the base boss top, which is not an opening there and gets no check
                for n in openings:
                    extra = touched[n.id] - {role_body.get(n.role, "base")}
                    self.assertTrue(extra <= ({"base"} if n.role == "screw_hole" else set()), (n.id, extra))
                for n in openings:
                    cid = f"ligament_{n.id}_{n.body}"
                    self.assertIn(cid, specs)
                    self.assertIn(cid, got)
                    self.assertEqual(n.body, {"screw_hole": "lid"}.get(n.role, "base"), n.id)
                    a = specs[cid]["args"]
                    self.assertEqual(a["min"], r["min_ligament"])
                    if n.role == "port_cut":
                        self.assertEqual(a["floor_z"], res.params["cavity"]["z0"])
                        self.assertEqual(a["axis"], A.SIDE_BOUND[n.wall][1])
                    else:
                        self.assertNotIn("floor_z", a)
                        self.assertEqual(a["axis"], 2)

    def test_ligament_checks_pass_with_margin(self):
        # iteration 009 (C1, C2): every ligament passes with the design margin (less the polygon allowance)
        r = pt.load_rules(RULES_PATH).values
        m = r["design_margin"]
        for rid in ("E1-01", "V1", "V2", "V3"):
            with self.subTest(rid=rid):
                st, got = measure_manifold(rid, self.root / rid)
                ligs = {k: v for k, v in got.items() if v.type == "ligament"}
                self.assertTrue(ligs)
                for cid, res in ligs.items():
                    self.assertTrue(res.passed, (cid, res.evidence))
                    self.assertGreaterEqual(res.margin, m - 0.01, (cid, res.evidence))
                    if "_lid_hole_" in cid:
                        self.assertEqual(res.evidence["toward"], "outer", cid)
                f = st.fasteners
                for k in range(1, 5):
                    self.assertAlmostEqual(st.resolved.params[f"boss_{k}"]["d"],
                                           f["fastener.lid.clearance_diameter"] + 2 * (r["min_ligament"] + m),
                                           delta=1e-9)

    def test_ligament_is_non_vacuous(self):
        # iteration 009 (C1): the sensor sees the judged defect. design_margin -0.2 shrinks the pad; and the
        # iteration 008 boss formula (no ligament term) reproduces judge 2's 1.346 on every lid hole
        r = pt.load_rules(RULES_PATH).values
        neg_rules = test_rules(self.root, design_margin=-0.2)
        _, bad = measure_manifold("E1-01", self.root / "neg", rules_path=neg_rules)
        for k in range(1, 5):
            res = bad[f"ligament_boss_{k}_lid_hole_lid"]
            self.assertFalse(res.passed, res.evidence)
            self.assertAlmostEqual(res.evidence["ligament"], r["min_ligament"] - 0.2, delta=0.02)
        st, res = derived("E1-01", self.root / "old")
        for k in range(1, 5):              # the iteration 008 expression, restored on the graph
            st.graph.nodes[f"boss_{k}"].params["d"] = (
                f"max({A.setpoint('fastener.lid.min_boss_od')}, fastener.lid.pilot_diameter + 2*rules.boss_wall_min)")
        st.resolved = A.resolve(st)
        st.solids = {b: fg.body_solid(st.graph, b, st.resolved) for b in st.graph.bodies()}
        old = {x.check_id: x for x in ac.run_plan(A.build_plan(st), st.solids)}
        for k in range(1, 5):
            res = old[f"ligament_boss_{k}_lid_hole_lid"]
            self.assertFalse(res.passed, res.evidence)
            self.assertAlmostEqual(res.evidence["ligament"], 1.344, delta=0.01)
            self.assertEqual(res.evidence["toward"], "outer")

    def test_split_ligament_has_the_design_margin(self):
        # iteration 009 (C3, RC-903): the split term over a port-cut top carries the setpoint margin
        r = pt.load_rules(RULES_PATH).values
        m = r["design_margin"]
        st, res = derived("E1-01", self.root / "e1")
        cav = res.params["cavity"]
        self.assertAlmostEqual(res.params["base"]["split"], cav["z1"] + r["lip_engagement"] + m, delta=1e-9)
        st.spec["keepout_above"] = 0.0
        st.spec["headroom"] = 0.0
        cuts = [n.id for n in st.graph if n.role == "port_cut"]
        res = A.resolve(st)
        top = max(res.params[c]["top"] for c in cuts)
        split = res.params["base"]["split"]
        self.assertGreater(top + r["min_ligament"] + m, res.params["cavity"]["z1"] + r["lip_engagement"] + m)
        self.assertAlmostEqual(split - (top + r["min_ligament"]), m, delta=1e-9)

    def test_sizes_are_derived_not_filled_in(self):
        st, res = derived("E1-01", self.root)
        base0 = dict(res.params["base"])
        st.spec["keepout_above"] += 3
        res2 = A.resolve(st)
        self.assertAlmostEqual(res2.params["base"]["split"] - base0["split"], 3.0, places=9)
        self.assertAlmostEqual(res2.params["base"]["x"], base0["x"], places=9)
        self.assertAlmostEqual(res2.params["base"]["y"], base0["y"], places=9)
        st.spec["keepout_above"] -= 3
        # a wider board: only the X-dependent expressions change
        board = st.graph.nodes["board"]
        # changed in iteration 011 (C1, RC-1101): 75 x 50 is no longer the photographed specimen, so the board's hole
        # values are pinned explicitly (an explicit param beats a specimen) to keep this a pure width change
        spec_params = st.placed.get("board").inst.specimen["params"]
        board.params.update({k: st.placed.get("board").inst.params[k] for k in spec_params})
        res_pinned = A.resolve(st)
        self.assertAlmostEqual(res_pinned.params["base"]["x"], base0["x"], places=9)
        board.params["width"] = board.params["width"] + 5
        res3 = A.resolve(st)
        self.assertAlmostEqual(res3.params["base"]["x"] - base0["x"], 5.0, places=6)
        self.assertAlmostEqual(res3.params["base"]["y"], base0["y"], places=9)
        self.assertAlmostEqual(res3.params["base"]["split"], base0["split"], places=9)


# ---------------------------------------------------------------------------
# The package and the offline end-to-end run (M12 / M13 preview)
# ---------------------------------------------------------------------------


GATE_TYPES = ("separable", "inside", "clear_of", "aperture_count", "aperture_oversize", "seated", "bbox_within")


def run_offline(rid: str, root: Path, rules_path: Path, llm=None, parts: Path = PARTS, l1_list=None, tag: str = "",
                **patches):
    """cad_agent.main in assembly mode on a request (no Ollama). `parts`: another catalogue folder; `l1_list`: L1s
    in place of the request's; `tag`: keeps several runs of one request apart under one root."""
    r = request(rid)
    l1 = root / f"{rid}{tag}.l1.json"
    l1.write_text(json.dumps(r["l1"] if l1_list is None else l1_list))
    llm = llm or FakeLLM(script_for(rid))
    out = root / f"out_{rid}{tag}"
    with mock.patch.object(ca, "OllamaAgent", lambda *a, **k: llm), mock.patch("builtins.print"):
        ctx = [mock.patch.object(ca, k, v) for k, v in patches.items()]
        for c in ctx:
            c.start()
        try:
            rc = ca.main(["--mode", "assembly", "--auto", "--l1", str(l1), "--parts", str(parts),
                          "--rules", str(rules_path), "--out", str(out), r["request"]])
        finally:
            for c in ctx:
                c.stop()
    pkg = sorted(out.glob("*/"))[-1]
    return rc, pkg, llm


def rubric_clear_of(bodies, vol, c):
    """rubric.md 3.2, verbatim (the independent re-measurement)."""
    pen = (bodies ^ vol).volume()
    if pen > 0.01:
        return None
    return bodies.min_gap(vol, c + 5.0)


def rubric_load(pkg: Path):
    """rubric.md 3.1 load recipe (trimesh -> manifold3d), not assembly_checks."""
    import trimesh
    import manifold3d as m3d
    out = []
    for body in ("base", "lid"):
        tm = trimesh.load(str(pkg / f"{body}.stl"), force="mesh")
        out.append(m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                                         tri_verts=np.asarray(tm.faces, np.uint32))))
    return out


def rubric_inside(solids, vol, c, big=2000.0):
    """rubric.md 3.3, verbatim (the independent re-measurement). d is None when the volume sticks out."""
    import manifold3d as m3d
    both = m3d.Manifold.batch_boolean(list(solids), m3d.OpType.Add)
    hull = both.hull()
    if (vol - hull).volume() > 0.01:
        return None
    shell = m3d.Manifold.cube([big] * 3, True) - hull
    return min(vol.min_gap(both, c + 5.0), vol.min_gap(shell, c + 5.0))


def catalogue_solid(cat, ref: dict, seg: int):
    """A layout.json reference rebuilt from part.json geometry at its pose (rubric: the M- reference models),
    never from the agent's graph or envelope nodes."""
    import manifold3d as m3d
    inst = cat.instantiate(ref["part"], ref["params"])
    pose = lay.pose_of(ref["x"], ref["y"], ref["z"], ref["rot_z"])
    prims = []
    for g in inst.geometry:
        if g.primitive == "box":
            lo, hi = g.bbox()
            m = m3d.Manifold.cube((hi - lo).tolist()).translate(lo.tolist())
        else:
            u = np.asarray(g.dir, dtype=float)
            u = u / np.linalg.norm(u)
            m = m3d.Manifold.cylinder(g.h, g.d / 2, g.d / 2, seg).transform(
                fg._m3(fg.matrix(fg.align_z_to(u), g.at)))
        prims.append(m.transform(pose[:3, :4]))
    return inst, pose, m3d.Manifold.batch_boolean(prims, m3d.OpType.Add)


def requirement_reference_comparisons(case: unittest.TestCase, pkg: Path, rules: dict, tol: float = 0.02) -> int:
    """iteration 005 (ARCHITECTURE.md 7.8): the self-report against references rebuilt from the catalogue at the
    layout.json poses with the rubric 3.2 / 3.3 recipes. Returns the number of comparisons made."""
    import manifold3d as m3d
    rec = json.loads((pkg / "design.json").read_text())["assembly"]
    report = json.loads((pkg / "self_report.json").read_text())
    by_id = {r["check_id"]: r for r in report["results"]}
    refs = json.loads((pkg / "layout.json").read_text())["references"]
    cat, seg = pt.Catalog.load(PARTS), int(rules["fn"])
    solids = rubric_load(pkg)
    both = solids[0] + solids[1]
    built = {r["id"]: catalogue_solid(cat, r, seg) for r in refs}
    n = 0

    def same(mine, ref, c, what, below=0.0):
        """mine == ref within tol; `below`: mine may also be up to this much smaller (stricter) than ref."""
        nonlocal n
        case.assertIsNotNone(ref, what)
        case.assertIsNotNone(mine, what)
        want = min(ref, c + 5.0)
        case.assertLessEqual(mine, want + tol, f"{pkg.name} {what}")
        case.assertGreaterEqual(mine, want - tol - below, f"{pkg.name} {what}")
        n += 1

    # the board minus Ø(seat_d + 2 x board_clearance) columns on its HOLE datums (V-SEAT grown, L2.2.1)
    bref = next(r for r in refs if r["role"] == "board")
    binst, bpose, bsolid = built[bref["id"]]
    bc = rec["spec"]["board_clearance"]
    # changed in iteration 010 (C3): the seat column is the larger of the board's mounting-hole keep-out (part data)
    # and the board screw's head + driver room
    seat_d = max(pt.lookup_datum(binst.datums, "HOLE").keepout_diameter or 0.0,
                 rec["fasteners"]["fastener.board.head_diameter"] + 2 * rules["driver_clearance"])
    lo, hi = bsolid.bounding_box()[2], bsolid.bounding_box()[5]
    cols = [m3d.Manifold.cylinder(hi - lo + 2, (seat_d + 2 * bc) / 2, (seat_d + 2 * bc) / 2, 256)
            .translate([float(h[0]), float(h[1]), lo - 1])
            for h in pt.transform(pt.lookup_datum(binst.datums, "HOLE"), bpose).at]
    board = bsolid - m3d.Manifold.batch_boolean(cols, m3d.OpType.Add)
    # changed in iteration 010: the agent's grown exemption is an inscribed fn-gon (it errs against the design), so
    # where a standoff rim sets the board gap (the walls moved out with the measured holes) the agent's d may be
    # smaller than the exact one by up to R (1 - cos(pi/fn)), R the exemption radius; never larger
    below = (seat_d / 2 + bc) * (1 - math.cos(math.pi / seg))
    same(by_id["clear_board"]["evidence"]["gap"], rubric_clear_of(both, board, bc), bc, "clear_board", below)
    same(by_id["inside_board"]["evidence"]["d"], rubric_inside(solids, board, bc), bc, "inside_board", below)
    # each module with stack parts: the union of its and its stacks' catalogue primitives (V-PICO), inside
    ptw = rules["part_to_wall"]
    for r in refs:
        stacks = [q for q in refs if q.get("of") == r["id"]]
        if not stacks:
            continue
        vol = m3d.Manifold.batch_boolean([built[q["id"]][2] for q in [r] + stacks], m3d.OpType.Add)
        check = by_id[f"clear_{r['id']}_envelope"]
        case.assertEqual(check["type"], "inside")
        same(check["evidence"]["d"], rubric_inside(solids, vol, ptw), ptw, f"V-{r['id']}")
    # every non-board reference, together and alone
    others = [r for r in refs if r["role"] != "board"]
    vol = m3d.Manifold.batch_boolean([built[r["id"]][2] for r in others], m3d.OpType.Add)
    contents = by_id["inside_contents"]["evidence"]
    same(contents["d"], rubric_inside(solids, vol, ptw), ptw, "inside_contents")
    case.assertEqual(set(contents["per_source"]), {r["id"] for r in others})
    for r in others:
        same(contents["per_source"][r["id"]]["d"], rubric_inside(solids, built[r["id"]][2], ptw), ptw,
             f"inside_contents[{r['id']}]")
        case.assertEqual(contents["per_source"][r["id"]]["part"], r["part"])
        case.assertEqual(report["references"][r["id"]]["part"], r["part"])
    case.assertEqual(set(report["references"]), {r["id"] for r in refs})
    return n


def board_holes(binst):
    """The test's own reading of the board's grid block: (origin xy, pitch, count or None)."""
    g = binst.part.data["grid"]
    origin, pitch = fg.evaluate3(g["origin"], binst.env)[:2], fg.evaluate(g["pitch"], binst.env)
    count = None if "count" not in g else np.array([round(fg.evaluate(c, binst.env)) for c in g["count"]], dtype=float)
    return origin, pitch, count


def hole_offset(rel: np.ndarray, pitch: float, count) -> np.ndarray:
    """Plan offsets from the nearest existing hole (rel: points relative to the grid origin)."""
    if count is None:
        return np.mod(rel + pitch / 2, pitch) - pitch / 2
    return rel - pitch * np.clip(np.round(rel / pitch), 0, count - 1)


def grid_expectation(pkg: Path, rules: dict) -> dict:
    """Grid conformance recomputed by the test from layout.json and part data (not layout.Placer): the worst
    pin-to-hole residual of the parts that must sit on the grid, and the parts with a connector but no pin data.
    `fails` is what grid_conformance must say.
    changed in iteration 010 (C1 / C4 / C5): the residual is to the nearest existing hole of the finite array, and a
    part whose own pattern meets no lattice position (pin_pattern) is exempt, so it is not in `worst`."""
    cat = pt.Catalog.load(PARTS)
    refs = json.loads((pkg / "layout.json").read_text())["references"]
    board = next(r for r in refs if r["role"] == "board")
    binst = cat.instantiate(board["part"], board["params"])
    origin, pitch, count = board_holes(binst)
    kinds, rows = part_grid_kinds(cat, refs, origin, pitch, rules, count)
    no_pins = []
    for r in refs:
        if r["role"] != "content":
            continue
        inst = cat.instantiate(r["part"], r["params"])
        names = inst.part.data.get("mount", {}).get("stack_pins") or (["PINS"] if "PINS" in inst.datums else [])
        if not names and inst.connectors:
            no_pins.append(r["id"])
    worst = max((row["residual"] for nid, row in rows.items() if kinds[nid] != "pin_pattern"), default=0.0)
    fails = bool(no_pins) or worst > rules["grid_residual_max"] + rules["measure_tol"]
    for nid in no_pins:
        kinds[nid] = "no_pin_data"
    return {"worst": worst, "no_pin_data": sorted(no_pins), "fails": fails, "kinds": kinds, "rows": rows,
            "exempt": sorted(nid for nid, k in kinds.items() if k == "pin_pattern")}


def brute_worst(pins: np.ndarray, pitch: float, shifts: np.ndarray) -> np.ndarray:
    """The test's own worst pin-to-lattice distance for each shift (not layout.grid_worst)."""
    out = np.empty(len(shifts))
    for k in range(0, len(shifts), 4096):
        s = shifts[k:k + 4096]
        d = np.mod(pins[None, :, :] + s[:, None, :] + pitch / 2, pitch) - pitch / 2
        out[k:k + 4096] = np.max(np.hypot(d[..., 0], d[..., 1]), axis=1)
    return out


def brute_feasibility(pins: np.ndarray, pitch: float, free_axis=None, step: float = 0.005) -> dict:
    """A brute-force grid search (step 0.005 mm) of the best residual over every translation and along one axis."""
    u = np.arange(0.0, pitch, step)
    xx, yy = np.meshgrid(u, u, indexing="ij")
    best_any = float(brute_worst(pins, pitch, np.stack([xx.ravel(), yy.ravel()], axis=1)).min())
    out = {"best_any": best_any}
    if free_axis is not None:
        sh = np.zeros((len(u), 2))
        sh[:, free_axis] = u
        out["best_free"] = float(brute_worst(pins, pitch, sh).min())
    return out


def part_grid_kinds(cat, refs, origin, pitch, rules, count=None):
    """Each content part's grid kind, recomputed from layout.json and part data with a brute-force lattice search.
    changed in iteration 010: residuals are to the nearest existing hole (`count`: a finite array); flush_to_edge is
    retired, so a part is ok, pin_pattern (no lattice position) or off-grid (`tangential`; the test cannot tell
    grid_extent or blocked, which need the placer's history)."""
    limit, tol = rules["grid_residual_max"], rules["measure_tol"]
    kinds, rows = {}, {}
    for r in refs:
        if r["role"] != "content":
            continue
        inst = cat.instantiate(r["part"], r["params"])
        names = inst.part.data.get("mount", {}).get("stack_pins") or (["PINS"] if "PINS" in inst.datums else [])
        if not names:
            continue
        pose = lay.pose_of(r["x"], r["y"], r["z"], r["rot_z"])
        pins = np.asarray([np.asarray(q[:2]) - origin for name in names
                           for q in pt.transform(pt.lookup_datum(inst.datums, name), pose).at])
        d = hole_offset(pins, pitch, count)
        residual = float(np.hypot(d[:, 0], d[:, 1]).max())
        tangent = None if not r["edge"] else 1 - "XY".index(r["edge"][1])
        b = brute_feasibility(pins, pitch, tangent)
        row = {"residual": residual, "best_any": b["best_any"], "best_free": b.get("best_free", b["best_any"])}
        if residual <= limit + tol:
            kind = "ok"
        elif b["best_any"] > limit + tol:
            kind = "pin_pattern"
        else:
            kind = "tangential"
        kinds[r["id"]], rows[r["id"]] = kind, row
    return kinds, rows


LITERAL_INSET = 1e-4     # mm: below any modelled feature, above float32 vertex noise


def rubric_aperture_regions(pkg: Path, side: str, min_volume: float = 1.0) -> list:
    """rubric.md 3.4 applied literally to the delivered STLs (no classification, not assembly_checks). Faces are
    found from the mesh facets: the wall's outer face is the largest-area plane with outward normal `side`, its
    inner face the largest-area plane facing back into the box between the outer face and the box centre. The
    wall's full extent along each other axis runs between the largest-area outward planes of the enclosure on
    that axis (the perpendicular walls' outer faces; the floor's underside and the lid's top). Aperture = slab -
    (base + lid); regions >= 1 mm3."""
    import trimesh
    import manifold3d as m3d
    axis, sign = "XY".index(side[1]), 1.0 if side[0] == "+" else -1.0
    meshes = [trimesh.load(str(pkg / f"{b}.stl"), force="mesh") for b in ("base", "lid")]
    centre = (np.min([m.bounds[0] for m in meshes], axis=0) + np.max([m.bounds[1] for m in meshes], axis=0)) / 2
    planes = {}
    for m in meshes:
        for n, c, a in zip(m.face_normals, m.triangles_center, m.area_faces):
            for k in range(3):
                if abs(abs(n[k]) - 1.0) <= 1e-6:
                    key = (k, int(np.sign(n[k])), round(float(c[k]), 3))
                    planes[key] = planes.get(key, 0.0) + a

    def largest(k, sgn, keep=lambda v: True):
        return max((key for key in planes if key[0] == k and key[1] == sgn and keep(key[2])), key=planes.get)[2]

    outer = largest(axis, sign)
    # changed in iteration 010: the inner face is the inward-facing plane nearest the outer face among those with at
    # least a tenth of the outer face's area (was the largest-area one: once the overmold-sized USB opening of the
    # on-grid Pico cut V1's -X wall, the lid lip's inner face out-sized the wall's and the slab took in cavity air)
    big = planes[(axis, int(sign), round(float(outer), 3))] / 10
    inner = min((key[2] for key in planes if key[0] == axis and key[1] == -sign and planes[key] >= big
                 and 0 < (key[2] - centre[axis]) * sign < (outer - centre[axis]) * sign),
                key=lambda v: abs(outer - v))
    lo, hi = np.zeros(3), np.zeros(3)
    lo[axis], hi[axis] = min(outer, inner), max(outer, inner)
    for k in range(3):
        if k != axis:
            lo[k], hi[k] = largest(k, -1, lambda v: v < centre[k]), largest(k, 1, lambda v: v > centre[k])
    # changed in iteration 010: every slab face is inset by 1e-4 mm (float32 noise of the STL vertices). V1's wall inner
    # face moved to Y/X = -1.6, which float32 stores 2.4e-8 outside the slab face, so the literal slab took a skin of
    # cavity air that joined both -X openings (the 7.10 coplanar-skin effect, on the test's side)
    lo, hi = lo + LITERAL_INSET, hi - LITERAL_INSET
    slab = m3d.Manifold.cube((hi - lo).tolist()).translate(lo.tolist())
    both = rubric_load(pkg)
    regions = (slab - (both[0] + both[1])).decompose()
    return [r for r in regions if r.volume() >= min_volume]


def expected_apertures(rid: str) -> dict:
    """Openings per wall implied by the scripted edges and quantities."""
    s = SCRIPTED[rid]
    qty = {"module_1": 1, "connector_1": s["jacks"]}
    out = {f"apertures_{side}": 0 for side in lay.SIDES}
    for item, side in s["edges"].items():
        out[f"apertures_{side}"] += qty[item]
    return out


class TestEndToEnd(unittest.TestCase):
    """E1-01, V1, V2 and V3 through cad_agent.main with a scripted controller (no Ollama), rules.fn = 24."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rules = test_rules(cls.root, fn=24)
        cls.runs = {rid: run_offline(rid, cls.root, cls.rules) for rid in ("E1-01", "V1", "V2", "V3")}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def record(self, rid):
        return json.loads((self.runs[rid][1] / "design.json").read_text())

    def test_exit_code_and_gate_checks(self):
        for rid in self.runs:
            with self.subTest(rid=rid):
                rc, pkg, llm = self.runs[rid]
                rec = self.record(rid)
                results = rec["assembly"]["results"]
                failing = [r["check_id"] for r in results if not r["passed"]]
                self.assertIn(rc, (ca.EXIT_OK, ca.EXIT_UNSATISFIED))
                if rc == ca.EXIT_UNSATISFIED:
                    matrix = (pkg / "verification_matrix.md").read_text()
                    for cid in failing:
                        self.assertIn(cid, matrix)
                gates = [r for r in results if r["type"] in GATE_TYPES]
                self.assertTrue(gates)
                self.assertEqual([r["check_id"] for r in gates if not r["passed"]], [])
                # changed in iteration 004 (behaviour intentionally changed: grid conformance is now a check):
                # every other check passes; grid_conformance fails exactly when the part data say it must
                grid = grid_expectation(pkg, pt.load_rules(self.rules).values)
                expected_failed = ["grid_conformance"] if grid["fails"] else []
                self.assertEqual(failing, expected_failed)
                self.assertEqual(rc, ca.EXIT_UNSATISFIED if expected_failed else ca.EXIT_OK, failing)
                self.assertEqual(rec["outcome"], "unsatisfied" if expected_failed else "verified")
                if Path(ca.OPENSCAD).exists():      # the delivered meshes are OpenSCAD's and agree with manifold3d
                    self.assertEqual(rec["assembly"]["stl_source"], {"base": "openscad", "lid": "openscad"})
                counts = {r["check_id"]: r["evidence"]["count"] for r in results if r["type"] == "aperture_count"}
                self.assertEqual(counts, expected_apertures(rid))
                spec = rec["assembly"]["spec"]
                size = next(r for r in results if r["type"] == "bbox_within")["evidence"]["size"]
                self.assertLessEqual(size[0], spec["max_x"])
                self.assertLessEqual(size[1], spec["max_y"])
                self.assertLessEqual(size[2], spec["max_z"])
                self.assertGreater(size[0], size[1])

    def test_manifest(self):
        for rid, (rc, pkg, _) in self.runs.items():
            with self.subTest(rid=rid):
                for name in ("base.stl", "lid.stl", "base.scad", "lid.scad", "model.scad", "open.scad", "layout.json",
                             "self_report.json", "feature_graph.json", "checks.json", "verification_matrix.md",
                             "verification_matrix.json", "design.json", "model.3mf"):
                    self.assertTrue((pkg / name).is_file(), name)
                for name in ("layout.json", "self_report.json", "feature_graph.json", "checks.json",
                             "verification_matrix.json"):
                    json.loads((pkg / name).read_text())
                fg.FeatureGraph.from_json((pkg / "feature_graph.json").read_text())
                for body in ("base", "lid"):
                    m = ac.load_mesh(pkg / f"{body}.stl")
                    self.assertEqual(len(m.decompose()), 1)
                    self.assertEqual(str(m.status()).split(".")[-1], "NoError")
                    b = m.bounding_box()
                    for k in range(3):
                        self.assertTrue(1.0 <= b[k + 3] - b[k] <= 200.0, (body, b))
                # iteration 006 (C5, RC-606): the lid-off evidence view: the base and the references, no lid body
                text = (pkg / "open.scad").read_text()
                graph = fg.FeatureGraph.from_json((pkg / "feature_graph.json").read_text())
                lid_nodes = [n.id for n in graph if n.body == "lid" or n.id == "lid"]
                self.assertTrue(lid_nodes)
                self.assertTrue(all(f"body {n}" not in text and f" {n} (" not in text for n in lid_nodes))
                self.assertIn("body base", text)
                self.assertEqual(text.count("{"), text.count("}"))
                if Path(ca.OPENSCAD).exists():
                    for v in ("open_iso.png", "open_top.png"):
                        self.assertTrue((pkg / "views" / v).is_file(), v)
                lay_json = json.loads((pkg / "layout.json").read_text())
                parts = {r["part"] for r in lay_json["references"]}
                self.assertTrue({"perfboard", "rpi_pico2", "jack_3p5_pj320a"} <= parts)
                self.assertEqual(set(lay_json["bodies"]), {"base", "lid"})

    def test_end_views_differ(self):
        # iteration 008 (C3, RC-804): the judges saw byte-identical model_left / model_right renders (exact orthographic
        # elevations); tilted down, the openings show and the opposite views differ
        if not Path(ca.OPENSCAD).exists():
            self.skipTest("OpenSCAD not installed")
        # (left / right only: E1-01's +-Y walls have no openings and mirror each other, so front / back may match)
        views = self.runs["E1-01"][1] / "views"
        a, b = "model_left.png", "model_right.png"
        self.assertTrue((views / a).is_file() and (views / b).is_file(), (a, b))
        self.assertNotEqual((views / a).read_bytes(), (views / b).read_bytes(), (a, b))

    def test_self_report_has_ligaments(self):
        # iteration 009 (C1): the delivered STLs are re-measured round every opening, in agreement with the manifold
        rc, pkg, _ = self.runs["E1-01"]
        rec = self.record("E1-01")["assembly"]
        report = json.loads((pkg / "self_report.json").read_text())
        mine = {r["check_id"]: r for r in rec["results_manifold"] if r["type"] == "ligament"}
        stl = {r["check_id"]: r for r in report["results"] if r["type"] == "ligament"}
        graph = fg.FeatureGraph.from_json((pkg / "feature_graph.json").read_text())
        openings = [n for n in graph if n.kind == "cut" and n.role in A.APERTURE_CUT_ROLES]
        self.assertEqual(set(stl), {f"ligament_{n.id}_{n.body}" for n in openings})
        self.assertEqual(set(stl), set(mine))
        for cid, r in stl.items():
            self.assertTrue(r["passed"], (cid, r["evidence"]))
            self.assertAlmostEqual(r["evidence"]["ligament"], mine[cid]["evidence"]["ligament"], delta=0.02, msg=cid)
        self.assertEqual([r["check_id"] for r in report["results"] if not r["passed"]
                          and r["check_id"] != "grid_conformance"], [])

    def test_self_report_agrees_with_an_independent_measurement(self):
        rc, pkg, _ = self.runs["E1-01"]
        report = json.loads((pkg / "self_report.json").read_text())
        graph = fg.FeatureGraph.from_json((pkg / "feature_graph.json").read_text())
        rec = self.record("E1-01")["assembly"]
        rules = pt.load_rules(self.rules)
        res = graph.resolve(rec["spec"], rules.values, catalog=pt.Catalog.load(PARTS), fasteners=rec["fasteners"])
        import trimesh
        import manifold3d as m3d
        solids = []
        for body in ("base", "lid"):          # rubric.md 3.1 load recipe, not assembly_checks
            tm = trimesh.load(str(pkg / f"{body}.stl"), force="mesh")
            solids.append(m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                                                tri_verts=np.asarray(tm.faces, np.uint32))))
        both = solids[0] + solids[1]
        by_id = {r["check_id"]: r for r in report["results"]}
        compared = 0
        for name in [n.id for n in graph if n.role == "plug_overmold"]:
            vol_id = name.rsplit("_plug_", 1)[0] + "_plug"
            parts = [n for n in graph if n.kind == "envelope" and n.id.startswith(vol_id + "_")]
            vol = parts[0] and ac.union([fg.solid(n, res) for n in parts])
            mine = by_id[f"clear_{vol_id}"]["evidence"]["gap"]
            ref = rubric_clear_of(both, vol, rules.values["plug_to_opening"])
            self.assertIsNotNone(ref)
            self.assertAlmostEqual(mine, min(ref, rules.values["plug_to_opening"] + ac.SEARCH_EXTRA), delta=0.02)
            compared += 1
        # changed in iteration 005: the board half subtracted the agent's own seat nodes, so it repeated RC-501; it
        # moved to test_self_report_matches_requirement_references (references rebuilt from the catalogue)
        self.assertEqual(compared, 3)

    def test_self_report_matches_requirement_references(self):
        # iteration 005 (ARCHITECTURE.md 7.8): board, V-PICO and contents rebuilt from part.json at layout.json poses
        rules = pt.load_rules(self.rules).values
        for rid, (rc, pkg, _) in self.runs.items():
            with self.subTest(rid=rid):
                n = requirement_reference_comparisons(self, pkg, rules)
                refs = json.loads((pkg / "layout.json").read_text())["references"]
                self.assertEqual(n, 2 + 1 + 1 + sum(r["role"] != "board" for r in refs))

    def test_jack_gap_matches_an_exact_envelope(self):
        # iteration 004 (C3): the self-report's jack-plug gap equals a re-measurement against an exact (high-fn)
        # plug, and it is not lenient: plug_to_opening + design_margin
        rc, pkg, _ = self.runs["E1-01"]
        report = {r["check_id"]: r for r in json.loads((pkg / "self_report.json").read_text())["results"]}
        graph = fg.FeatureGraph.from_json((pkg / "feature_graph.json").read_text())
        rec = self.record("E1-01")["assembly"]
        rules = pt.load_rules(self.rules).values
        exact = graph.resolve(rec["spec"], dict(rules, fn=256), catalog=pt.Catalog.load(PARTS), fasteners=rec["fasteners"])
        both = ac.load_mesh(pkg / "base.stl") + ac.load_mesh(pkg / "lid.stl")
        jacks = [n.id.rsplit("_plug_", 1)[0] for n in graph if n.role == "plug_overmold" and n.primitive == "cylinder"]
        self.assertEqual(len(jacks), 2)
        for j in jacks:
            vol = ac.union([fg.solid(n, exact) for n in graph if n.kind == "envelope" and n.id.startswith(j + "_plug_")])
            ref = rubric_clear_of(both, vol, rules["plug_to_opening"])
            mine = report[f"clear_{j}_plug"]["evidence"]["gap"]
            self.assertIsNotNone(ref)
            self.assertAlmostEqual(mine, ref, delta=0.02)
            self.assertGreaterEqual(mine, rules["plug_to_opening"] + rules["design_margin"] - rules["measure_tol"])

    def test_grid_conflict_is_reported_not_hidden(self):
        # iteration 004 (C4): the known pin-to-grid residual is a failing check with a typed conflict
        # changed in iteration 006 (one conflict per failing part, each with a kind recomputed here from layout.json and
        # part data, never from layout.Placer).
        # changed in iteration 010 (behaviour intentionally changed, C4 / C5): the Pico sits on the finite grid and the
        # jacks are exempt (pin_pattern, an assumption), so the check passes with no conflict on every request; the
        # kinds and the exempt list still agree with the test's own recomputation
        rules = pt.load_rules(self.rules).values
        for rid in self.runs:
            with self.subTest(rid=rid):
                rc, pkg, _ = self.runs[rid]
                assy = self.record(rid)["assembly"]
                grid = grid_expectation(pkg, rules)
                check = next(r for r in assy["results"] if r["check_id"] == "grid_conformance")
                self.assertEqual(check["passed"], not grid["fails"])
                self.assertFalse(grid["fails"])
                self.assertAlmostEqual(check["evidence"]["value"], grid["worst"], delta=1e-6)
                self.assertEqual(sorted(check["evidence"]["no_pin_data"]), grid["no_pin_data"])
                self.assertFalse(check["evidence"]["soft"])
                self.assertEqual(check["evidence"]["kinds"], grid["kinds"])
                self.assertEqual(sorted(e["part"] for e in check["evidence"]["exempt"]), grid["exempt"])
                self.assertEqual([c for c in assy["conflicts"] if c["check_id"] == "grid_conformance"], [])
                for e in check["evidence"]["exempt"]:
                    self.assertAlmostEqual(e["best_any"], grid["rows"][e["part"]]["best_any"], delta=0.01)
                    self.assertIn(e["assumption"], assy["assumptions"])
        grid = grid_expectation(self.runs["E1-01"][1], rules)
        self.assertEqual(grid["kinds"], {"module_1_1": "ok", "connector_1_1": "pin_pattern",
                                         "connector_1_2": "pin_pattern"})

    def test_aperture_regions_follow_the_literal_rubric_slab(self):
        # iteration 006 (C4, RC-605): the agent's slab is rubric 3.4's (full extent); through + blind regions equal an
        # independent literal application of the recipe; blind regions name the corner pilots and lid holes
        for rid, (rc, pkg, _) in self.runs.items():
            with self.subTest(rid=rid):
                report = json.loads((pkg / "self_report.json").read_text())
                results = {r["check_id"]: r for r in report["results"]}
                graph = fg.FeatureGraph.from_json((pkg / "feature_graph.json").read_text())
                rec = self.record(rid)["assembly"]
                res = graph.resolve(rec["spec"], pt.load_rules(self.rules).values, catalog=pt.Catalog.load(PARTS),
                                    fasteners=rec["fasteners"])
                cav = res.params["cavity"]
                for side in lay.SIDES:
                    ev = results[f"apertures_{side}"]["evidence"]
                    literal = rubric_aperture_regions(pkg, side)
                    self.assertEqual(ev["through"] + len(ev["blind"]), len(literal), (side, ev["detail"]))
                    self.assertEqual(report["apertures"][side]["through"], ev["through"])
                    self.assertEqual(ev["through"], expected_apertures(rid)[f"apertures_{side}"])
                    # the bosses at this wall's two corners: each corner is one blind region (pilot + lid hole)
                    axis, sign = "XY".index(side[1]), 1 if side[0] == "+" else -1
                    bound = cav[("x" if axis == 0 else "y") + ("1" if sign > 0 else "0")]
                    corner = [n.id for n in graph if n.role == "boss"
                              and sign * (res.params[n.id]["ax" if axis == 0 else "ay"] - bound) > 0]
                    self.assertEqual(len(corner), 2, side)
                    blind_nodes = {x for b in ev["blind"] for x in b["nodes"]}
                    self.assertEqual(blind_nodes, {f"{b}_{c}" for b in corner for c in ("pilot", "lid_hole")}, side)
                    self.assertEqual(len(ev["blind"]), 2, side)
                    for row in ev["regions"]:
                        if row["class"] == "through":
                            self.assertTrue(row["nodes"] and all(graph.nodes[n].role == "port_cut" for n in row["nodes"]))
        rc, pkg, _ = self.runs["E1-01"]
        ev = {r["check_id"]: r for r in json.loads((pkg / "self_report.json").read_text())["results"]}
        self.assertEqual((ev["apertures_-X"]["evidence"]["through"], ev["apertures_+X"]["evidence"]["through"]), (1, 2))
        self.assertEqual((ev["apertures_-X"]["evidence"]["total"], ev["apertures_+X"]["evidence"]["total"]), (3, 4))

    def test_trace_links(self):
        # iteration 007 (C4, RC-701, ARCHITECTURE.md 7.10): the rule-derived checks are traced to L1s from spec-slot
        # provenance and the catalogue parts each L1 names; expected L1s are found from the texts, never typed in
        rid = "E1-01"
        rc, pkg, _ = self.runs[rid]
        checks = check_params(pkg)
        links = {k: c["links"] for k, c in checks.items()}
        matrix = json.loads((pkg / "verification_matrix.json").read_text())
        md = (pkg / "verification_matrix.md").read_text()
        l1 = request(rid)["l1"]
        clearance = l1_with(rid, "0.5 mm clearance")
        size = l1_with(rid, "no larger than")
        keep = l1_with(rid, "above the board")
        for k in ("inside_board", "clear_board"):
            self.assertEqual(links[k], [clearance], k)
        self.assertEqual(links["bbox"], [size])
        for k in ("clear_keepout_top", "clear_keepout_bottom"):
            self.assertEqual(links[k], [keep], k)
        cat = pt.Catalog.load(PARTS)
        graph = fg.FeatureGraph.from_json((pkg / "feature_graph.json").read_text())

        def naming(pid):                          # the test's own reading: an alias as a lower-case substring
            return [x["id"] for x in l1 if any(a.lower() in x["text"].lower() for a in cat.get(pid).names)]

        plugs = [k for k in checks if k.startswith("clear_") and k.endswith("_plug")]
        self.assertEqual(len(plugs), 3)
        for k in plugs:
            pids = {n.part for n in graph if n.group == k[len("clear_"):] and n.part}
            self.assertEqual(len(pids), 1, k)
            self.assertEqual(links[k], naming(pids.pop()), k)
            self.assertTrue(links[k], k)
        contents = {r["part"] for r in json.loads((pkg / "layout.json").read_text())["references"] if r["role"] != "board"}
        content_l1 = sorted({i for pid in contents for i in naming(pid)})
        self.assertEqual(sorted(links["inside_contents"]), content_l1)
        linked = {i for v in links.values() for i in v}
        plug_l1 = {i for k in plugs for i in links[k]}
        over = {i for k in checks if k.startswith("oversize_") for i in links[k]}
        self.assertEqual(linked, {clearance, size, keep} | plug_l1 | set(content_l1) | over)
        rows = {r["l1_id"]: r for r in matrix}
        self.assertEqual(set(rows), {x["id"] for x in l1} | {ac.L1_RULES})
        for x in l1:
            r = rows[x["id"]]
            if x["id"] in linked:
                self.assertIn(r["status"], ("PASS", "FAIL"))
                self.assertEqual({c["id"] for c in r["checks"]}, {k for k, v in links.items() if x["id"] in v})
            else:
                self.assertEqual((r["status"], r["checks"]), ("UNLINKED", []), x["id"])
                self.assertIn("M10", r["note"])
        self.assertNotIn("no check covers", md)
        self.assertFalse(any(r["status"] == "FAIL" and not r["checks"] for r in matrix))
        self.assertEqual({c["id"] for c in rows[ac.L1_RULES]["checks"]}, {k for k, v in links.items() if not v})
        # E1-01: six L1s traced, six UNLINKED until M10 (no check consumes the wall band yet: a gap for M5 / M10)
        self.assertEqual(len(linked), 6)
        self.assertEqual(sum(r["status"] == "UNLINKED" for r in matrix), 6)

    def test_v1_socket_stack_apertures(self):
        # iteration 007 (C1, RC-704): V1 on a socket stack with the Pico left unexposed (the iteration 007 run: split on an
        # exactly representable Z). Before C1 the seam joined a wall's corner pockets into a false `through` opening. The
        # catalogue copy lists the sockets first, so the catalogue default (no stack word in V1) is the socket stack.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parts = root / "parts"
            shutil.copytree(PARTS, parts)
            pj = parts / "rpi_pico2" / "part.json"
            data = json.loads(pj.read_text())
            data["mount"]["stack_options"] = list(reversed(data["mount"]["stack_options"]))
            pj.write_text(json.dumps(data))
            # changed in iteration 008 (RC-801): a named plug now exposes its connector by rule, so the unexposed case
            # needs L1s that do not name the plug (was: the scripted assy_expose "no")
            rc, pkg, _ = run_offline("V1", root, self.rules, llm=iter007_llm("V1_s5"), parts=parts,
                                     l1_list=without_plug_names("V1"))
            assy = json.loads((pkg / "design.json").read_text())["assembly"]
            report = json.loads((pkg / "self_report.json").read_text())
            literal = {side: len(rubric_aperture_regions(pkg, side)) for side in lay.SIDES}
            walls = {k[len("oversize_"):]: c["params"]["wall"] for k, c in check_params(pkg).items()
                     if c["type"] == "aperture_oversize"}
        self.assertEqual(assy["choices"]["stack[module_1]"]["value"], "header_female_2p54")
        graph = fg.FeatureGraph.from_json(assy["feature_graph"])
        rules = pt.load_rules(self.rules).values
        res = graph.resolve(assy["spec"], rules, catalog=pt.Catalog.load(PARTS), fasteners=assy["fasteners"])
        split = res.params["base"]["split"]
        self.assertEqual(split, round(split, 1))             # the case that exposed the skin
        results = {r["check_id"]: r for r in report["results"]}
        cav = res.params["cavity"]
        for side in lay.SIDES:
            ev = results[f"apertures_{side}"]["evidence"]
            self.assertTrue(results[f"apertures_{side}"]["passed"], ev["detail"])
            cuts = [n for n in graph if n.role == "port_cut" and walls[n.id] == side]
            self.assertEqual(ev["through"], len(cuts), side)
            for row in ev["regions"]:
                if row["class"] == "through":
                    self.assertTrue(row["nodes"] and all(graph.nodes[n].role == "port_cut" for n in row["nodes"]))
            if assy["stl_source"] == {"base": "openscad", "lid": "openscad"}:
                axis, sign = "XY".index(side[1]), 1 if side[0] == "+" else -1
                bound = cav[("x" if axis == 0 else "y") + ("1" if sign > 0 else "0")]
                corner = {n.id for n in graph if n.role == "boss"
                          and sign * (res.params[n.id]["ax" if axis == 0 else "ay"] - bound) > 0}
                self.assertEqual(len(ev["blind"]), 2, side)
                owners = []
                for b in ev["blind"]:                         # each blind region is one corner's pilot + lid hole
                    bosses = {x for x in corner if any(y.startswith(x + "_") for y in b["nodes"])}
                    self.assertEqual(len(bosses), 1, (side, b["nodes"]))
                    owners += sorted(bosses)
                self.assertEqual(sorted(owners), sorted(corner), side)
                # the literal rubric 3.4 helper (judge side, slab Z on the base bottom and the lid top) can only see fewer
                # regions: on this case its zero-thickness seam skin joins the corner pockets (iteration 007 measured -X: 2
                # literal regions vs 1 through + 2 blind). A rubric question for Robin (question 5), not an agent change.
                self.assertLessEqual(literal[side], ev["through"] + len(ev["blind"]), side)
                self.assertGreaterEqual(literal[side], ev["through"], side)

    def test_no_reference_in_a_body(self):
        rc, pkg, _ = self.runs["E1-01"]
        graph = fg.FeatureGraph.from_json((pkg / "feature_graph.json").read_text())
        refs = [n.id for n in graph if n.kind in fg.NOT_PRINTED]
        self.assertTrue(refs)
        for body in ("base", "lid"):
            text = (pkg / f"{body}.scad").read_text()
            for rid in refs:
                self.assertNotIn(f" {rid} (", text, (body, rid))
        model = (pkg / "model.scad").read_text()
        ghost_lines = [l for l in model.splitlines() if "ghost " in l]
        self.assertTrue(all(l.startswith("%") for l in ghost_lines))

    def test_components_come_from_the_graph(self):
        rec = self.record("E1-01")["assembly"]
        graph = fg.FeatureGraph.from_json(rec["feature_graph"])
        comps = rec["components"]
        self.assertEqual(sum(c["role"] == "standoff" for c in comps), sum(n.role == "standoff" for n in graph))
        self.assertEqual({c["id"] for c in comps}, {n.id for n in graph if n.kind in fg.BUILD_KINDS})
        self.assertTrue(all(c["source"].startswith("rule:") for c in comps))
        self.assertEqual(rec["choices"]["archetype"]["by"], "rule:only_feasible")
        self.assertEqual(rec["choices"]["edge[module_1]"]["by"], "llm")

    def test_manifold_fallback_when_openscad_times_out(self):
        failed = ca.CompileResult(False, ["ERROR: OpenSCAD timed out after 300s"])
        with tempfile.TemporaryDirectory() as tmp:
            rc, pkg, _ = run_offline("E1-01", Path(tmp), self.rules, compile_scad=lambda *a, **k: failed,
                                     render_openscad=lambda *a, **k: ({}, ["skipped in the test"]))
            rec = json.loads((pkg / "design.json").read_text())["assembly"]
            self.assertEqual(rec["stl_source"], {"base": "manifold", "lid": "manifold"})
            self.assertTrue((pkg / "base.stl").is_file() and (pkg / "lid.stl").is_file())
            # changed in iteration 004 (grid conformance is now a check): only grid_conformance fails
            # changed in iteration 010 (C1-C5): nothing fails, the manifold-mesh package verifies
            self.assertEqual([r["check_id"] for r in rec["results"] if not r["passed"]], [])
            self.assertEqual(rc, ca.EXIT_OK)


class TestReplayIter003(unittest.TestCase):
    """Iteration 003's real-run answers (iter_003/target_s0/*/llm) replayed offline through cad_agent.main:
    the spec with keepout_below on the keepout_above number, a 2-of-3 stack vote, the 2-of-3 edge vote
    and the recorded p_yes table (all < 0.5). The repaired agent gets past ArrangeContents and verifies."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rules = test_rules(cls.root, fn=24)
        good = spec_reply("E1-01")
        keep = l1_with("E1-01", "above the board")
        cls.below = 4.0
        dup = dict(good, keepout_below=number_id("E1-01", 12, keep))
        script = script_for("E1-01", assy_spec=[dup], assy_spec_reask=[good],
                            assy_stack=[{"stack": "header_male_2p54"}, {"stack": "header_female_2p54"},
                                        {"stack": "header_male_2p54"}],
                            assy_edge=ITER003_EDGE_VOTES)
        cls.llm = RankedLLM(script, iter003_table())
        cls.rc, cls.pkg, _ = run_offline("E1-01", cls.root, cls.rules, llm=cls.llm)
        cls.rec = json.loads((cls.pkg / "design.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_replay_iter003_answers_end_to_end(self):
        # changed in iteration 004 (grid conformance is now a check): rc 3 with exactly grid_conformance failing
        # changed in iteration 010 (behaviour intentionally changed, C1-C5): the Pico sits on the measured finite grid and the
        # jacks are exempt (pin_pattern), so no check fails and the package verifies (was: grid_conformance only, rc 3)
        assy = self.rec["assembly"]
        self.assertEqual([r["check_id"] for r in assy["results"] if not r["passed"]], [])
        self.assertEqual(self.rc, ca.EXIT_OK, assy["notes"])
        self.assertEqual(self.rec["outcome"], "verified")
        self.assertEqual(assy["choices"]["arrangement_confirmed"]["by"], "llm:vote+rank")
        self.assertNotIn("assy_arrange_pick", self.llm.labels())
        results = assy["results"]
        counts = {r["check_id"]: r["evidence"]["count"] for r in results if r["type"] == "aperture_count"}
        self.assertEqual(counts, {"apertures_-X": 1, "apertures_+X": 2, "apertures_-Y": 0, "apertures_+Y": 0})
        size = next(r for r in results if r["type"] == "bbox_within")["evidence"]["size"]
        self.assertLessEqual(size[2], assy["spec"]["max_z"])
        # the shared n-id was re-asked: the solder-side keep-out is the "4 mm below" number, not the 12
        self.assertEqual(assy["spec"]["keepout_below"], self.below)
        graph = fg.FeatureGraph.from_json((self.pkg / "feature_graph.json").read_text())
        res = graph.resolve(assy["spec"], pt.load_rules(self.rules).values, catalog=pt.Catalog.load(PARTS),
                            fasteners=assy["fasteners"])
        heights = [res.params[n.id]["height"] for n in graph if n.role == "standoff"]
        self.assertTrue(heights)
        margin = pt.load_rules(self.rules).values["design_margin"]
        for h in heights:      # changed in iteration 004: the floor sits design_margin below the solder-side keep-out
            self.assertAlmostEqual(h, self.below + margin, places=9)
        json.dumps(assy["arrange"])
        self.assertEqual(assy["arrange"]["decision"], "llm:vote+rank")


# iteration 004's recorded controller answers (iter_004/target_s0/20261024-091709/llm/001-021)
ITER004_EDGE_VOTES = [{"module_1": "-X", "connector_1": "+X"}] * 2 + [{"module_1": "-X", "connector_1": "-X"}]
ITER004_P_YES = {("-X", "+X"): 0.199, ("-X", "-Y"): 0.106, ("-X", "+Y"): 0.096, ("-Y", "+X"): 0.092,
                 ("+Y", "+X"): 0.113, ("-Y", "-Y"): 0.096}


def iter004_llm():
    """The recorded iter_004 controller answers as a fake LLM. Iteration 005's answers
    (iter_005/target_s0/20261024-095851/llm/001-021) are the same responses, file for file."""
    good = spec_reply("E1-01")
    dup = dict(good, keepout_below=good["keepout_above"])
    other_over = dict(good, opening_oversize_max=number_id("E1-01", 1.5, l1_with("E1-01", "two 3.5 mm plugs")))
    cat = pt.Catalog.load(PARTS)
    words = edge_words(cat, "E1-01")
    usb, jack = connector_names(cat)
    table = [((f"({usb}) faces {words[m]}", f"({jack}) face {words[c]}"), p) for (m, c), p in ITER004_P_YES.items()]
    script = script_for("E1-01", assy_spec=[dup, dup, dup], assy_spec_reask=[good, good, other_over],
                        assy_stack=[{"stack": "header_male_2p54"}, {"stack": "header_female_2p54"},
                                    {"stack": "header_male_2p54"}],
                        assy_edge=ITER004_EDGE_VOTES)
    return RankedLLM(script, table)


class TestReplayIter004(unittest.TestCase):
    """Iteration 004's real-run answers replayed offline (ARCHITECTURE.md 7.6): the spec with keepout_below on the
    keepout_above number (3 x), a re-ask fixed 3 x (one vote put opening_oversize_max on the second 1.5 mm), a 2-of-3
    stack vote, a 2-of-3 edge vote and the recorded p_yes per class. The screw-head columns now bound the cavity."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rules = test_rules(cls.root, fn=24)
        cls.llm = iter004_llm()
        cls.rc, cls.pkg, _ = run_offline("E1-01", cls.root, cls.rules, llm=cls.llm)
        cls.rec = json.loads((cls.pkg / "design.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_replay_iter004_answers_end_to_end(self):
        assy = self.rec["assembly"]
        results = {r["check_id"]: r for r in assy["results"]}
        # the package is built; only the (now sensed) grid conformance fails, as a typed conflict
        # changed in iteration 010 (behaviour intentionally changed, C1-C5): the Pico sits on the measured finite grid and the
        # jacks are exempt (pin_pattern), so no check fails and the package verifies (was: grid_conformance only, rc 3)
        self.assertEqual([k for k, r in results.items() if not r["passed"]], [], assy["notes"])
        self.assertEqual(self.rc, ca.EXIT_OK)
        # changed in iteration 006, then iteration 010: no conflicts (the jacks are an exemption, not a conflict)
        self.assertEqual(assy["conflicts"], [])
        self.assertEqual(assy["choices"]["arrangement_confirmed"]["by"], "llm:vote+rank")
        self.assertEqual(assy["spec"]["opening_oversize_max"], 1.5)
        for k in range(4):
            self.assertTrue(results[f"clear_hole_ko_{k}"]["passed"], results[f"clear_hole_ko_{k}"])
            self.assertTrue(results[f"clear_driver_{k}"]["passed"], results[f"clear_driver_{k}"])
        # independent rubric 3.2 re-measurement: base + lid against exact screw-head columns
        graph = fg.FeatureGraph.from_json((self.pkg / "feature_graph.json").read_text())
        rules = pt.load_rules(self.rules).values
        res = graph.resolve(assy["spec"], rules, catalog=pt.Catalog.load(PARTS), fasteners=assy["fasteners"])
        import trimesh
        import manifold3d as m3d
        solids = []
        for body in ("base", "lid"):
            tm = trimesh.load(str(self.pkg / f"{body}.stl"), force="mesh")
            solids.append(m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                                                tri_verts=np.asarray(tm.faces, np.uint32))))
        both = solids[0] + solids[1]
        cols = [n for n in graph if n.role == "hole_keepout"]
        self.assertEqual(len(cols), 4)
        for n in cols:
            p, at = res.params[n.id], res.poses[n.id][:3, 3]
            exact = m3d.Manifold.cylinder(p["h"], p["d"] / 2, p["d"] / 2, 256).translate(at.tolist())
            self.assertLessEqual((both ^ exact).volume(), 0.01, n.id)



ITER005_PKG = REPO / "benchmarks" / "enclosure" / "loop" / "iter_005" / "target_s0" / "20261024-095851"
# iteration 006 offline replay of the iter_004/005 answers at the real rules (OpenSCAD meshes), after the C3 setpoint
# margins (deeper pilots, wider lid bosses, +design_margin lip engagement): the recomputed body volumes in mm3
# (iteration 006: base 24467.2891, lid 11355.4662)
# changed in iteration 009 (geometry changed on purpose, C2 / RC-902): the corner columns and lid pads grow from
# Ø6.1 to Ø6.6 (clearance + 2 x (min_ligament + design_margin)); the recomputed volumes in mm3
# (iteration 009: base 24896.0554, lid 11401.6104)
# changed in iteration 010 (geometry changed on purpose, C1-C4): standoffs on the measured 66 x 46 holes (Ø5.1, Ø1.7
# M2 pilots), the cavity bounded by the Ø7 columns on those holes (-1.6 .. 71.6 x -1.6 .. 51.6), the Pico on grid
# column 0 with an overmold-sized USB opening; Z is unchanged
ITER010_VOLUMES = {"base": 25222.8633, "lid": 11622.2185}


class TestReplayIter005(unittest.TestCase):
    """Iteration 005's real-run answers replayed offline at the real rules (fn 64), ARCHITECTURE.md 7.6: the
    sensor-only delta leaves the bodies unchanged, and the self-report now agrees with references rebuilt from
    the catalogue."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.llm = iter004_llm()
        cls.rc, cls.pkg, _ = run_offline("E1-01", cls.root, RULES_PATH, llm=cls.llm)
        cls.rec = json.loads((cls.pkg / "design.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_replay_iter005_answers_end_to_end(self):
        assy = self.rec["assembly"]
        # changed in iteration 010 (behaviour intentionally changed, C1-C5): the Pico sits on the measured finite grid and the
        # jacks are exempt (pin_pattern), so no check fails and the package verifies (was: grid_conformance only, rc 3)
        self.assertEqual([r["check_id"] for r in assy["results"] if not r["passed"]], [], assy["notes"])
        self.assertEqual(self.rc, ca.EXIT_OK)
        self.assertEqual(assy["conflicts"], [])
        report = json.loads((self.pkg / "self_report.json").read_text())
        recorded = ITER005_PKG / "self_report.json"
        if recorded.is_file() and assy["stl_source"] == {"base": "openscad", "lid": "openscad"}:
            old = json.loads(recorded.read_text())["bodies"]
            # changed in iteration 006 (geometry changed on purpose, C3 setpoint margins): the bodies equal this
            # iteration's recomputed volumes, and each body is taller than iteration 005's by design_margin in Z
            # changed in iteration 009 (C2): the volumes are iteration 009's (wider corner columns); Z is unchanged
            # changed in iteration 010 (C1-C4): the volumes are iteration 010's (measured board, M2, on-grid Pico)
            margin = pt.load_rules(RULES_PATH).values["design_margin"]
            for body in ("base", "lid"):
                self.assertAlmostEqual(report["bodies"][body]["volume"], ITER010_VOLUMES[body], delta=0.01, msg=body)
                self.assertAlmostEqual(report["bodies"][body]["bbox"][1][2] - old[body]["bbox"][1][2], margin,
                                       delta=1e-3, msg=body)
        n = requirement_reference_comparisons(self, self.pkg, pt.load_rules(RULES_PATH).values)
        self.assertGreaterEqual(n, 4)


ITER007 = REPO / "benchmarks" / "enclosure" / "loop" / "iter_007"


ITER008 = REPO / "benchmarks" / "enclosure" / "loop" / "iter_008"


def recorded_answers(run: str, iteration_dir: Path = ITER007) -> dict:
    """{label: [JSON replies in file order]} from a real run's transcripts (<iteration_dir>/<run>/*/llm/NNN_<label>.txt);
    the p_yes transcripts (not JSON) are skipped."""
    out: dict = {}
    for f in sorted((iteration_dir / run).glob("*/llm/*.txt")):
        body = f.read_text().split("=== RESPONSE ===", 1)[-1].strip()
        try:
            reply = json.loads(body)
        except ValueError:
            continue
        out.setdefault(f.stem.split("_", 1)[1], []).append(reply)
    return out


def recorded_p_yes(run: str, iteration_dir: Path = ITER008) -> list:
    """RankedLLM table entries ((arrangement words,), p_yes) from a real run's assy_confirm transcripts."""
    out = []
    for f in sorted((iteration_dir / run).glob("*/llm/*_assy_confirm.txt")):
        text = f.read_text()
        words = text.split("Proposed arrangement on the board: ", 1)[1].split("\n", 1)[0]
        out.append(((words,), float(text.rsplit("p_yes=", 1)[1].split()[0])))
    return out


def recorded_llm(run: str, iteration_dir: Path = ITER007, cls=None, **extra):
    """A real run's recorded controller answers (spec with its re-asks, contents, stack, params, edges) with no
    assy_expose key (iteration 008, RC-801: any exposure question raises) and assy_confirm "yes" (every class gets the
    same p_yes, so the vote winner is accepted). Recorded edge votes from a run where the Pico was unexposed name only
    the jacks, so the module's edge has no valid vote and its first candidate is tried first (noted as an
    assumption)."""
    script = recorded_answers(run, iteration_dir)
    if not script:
        raise unittest.SkipTest(f"no recorded transcripts in {iteration_dir / run}")
    script.pop("assy_expose", None)
    script.update(assy_confirm=[{"answer": "yes"}])
    return (cls or SchemaLLM)(script, **extra)


def iter007_llm(run: str) -> SchemaLLM:
    """iteration 007's recorded answers (changed in iteration 008: the scripted assy_expose answer is gone, RC-801)."""
    return recorded_llm(run, ITER007)


def recorded_votes(run: str, iteration_dir: Path, pid: str) -> dict:
    """The recorded Contents exposure votes of one part ({"yes": n, "no": m}), counted from the transcripts."""
    out: dict = {}
    for reply in recorded_answers(run, iteration_dir).get("assy_contents", []):
        v = reply.get(pid, {}).get("exposed")
        if v in ("yes", "no"):
            out[v] = out.get(v, 0) + 1
    return out


def check_params(pkg: Path) -> dict:
    return {c["id"]: c for c in json.loads((pkg / "checks.json").read_text())}


class TestReplayIter007(unittest.TestCase):
    """Iteration 007's real-run answers on V1, V2 and V3 (ARCHITECTURE.md 7.6, 7.10, 7.11): the 9B said the Pico's
    connector was not exposed (3/3) although L1.5 names a micro-USB cable. Text coverage senses it and exposes it by rule
    (no question since iteration 008), and each variant gets its USB opening."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rules = test_rules(cls.root, fn=24)
        cls.runs = {}
        for rid in ("V1", "V2", "V3"):
            llm = iter007_llm(f"{rid}_s5")
            rc, pkg, _ = run_offline(rid, cls.root, cls.rules, llm=llm)
            cls.runs[rid] = (rc, pkg, llm, json.loads((pkg / "design.json").read_text())["assembly"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def walls(self, pkg):
        """The wall of each port cut, from checks.json (aperture_oversize params)."""
        return {k[len("oversize_"):]: c["params"]["wall"] for k, c in check_params(pkg).items()
                if c["type"] == "aperture_oversize"}

    def test_replay_iter007_exposes_the_named_connector(self):
        for rid, (rc, pkg, llm, assy) in self.runs.items():
            with self.subTest(rid=rid):
                # changed in iteration 008 (behaviour intentionally changed, RC-801): exposure from text coverage is a
                # rule, so no assy_expose question is asked (was 3 voted calls and by = "llm:coverage")
                self.assertNotIn("assy_expose", llm.labels())
                naming = l1_with(rid, "micro-USB cable")
                pico = next(c for c in assy["contents"] if c["part"] == "rpi_pico2")
                self.assertTrue(pico["exposed"])
                self.assertEqual(assy["choices"][f"exposed[{pico['id']}]"]["by"], "rule:text_coverage")
                self.assertTrue(any(e["source"] == naming and e["quote"] in l1_text(rid, naming)
                                    for e in assy["coverage"][0]["evidence"]), assy["coverage"])
                self.assertEqual([c["resolved"] for c in assy["coverage"]], ["exposed"])
                results = {r["check_id"]: r for r in assy["results"]}
                self.assertTrue(results["text_coverage"]["passed"], results["text_coverage"]["evidence"])
                # changed in iteration 010 (C1-C5): nothing fails any more (was grid_conformance only, rc 3)
                self.assertEqual([k for k, r in results.items() if not r["passed"]], [], assy["notes"])
                self.assertEqual(rc, ca.EXIT_OK)
                walls = self.walls(pkg)
                usb = [w for cut, w in walls.items() if cut.startswith(pico["id"])]
                jacks = [w for cut, w in walls.items() if not cut.startswith(pico["id"])]
                self.assertEqual(len(usb), 1, walls)
                n = {side: results[f"apertures_{side}"]["evidence"]["expected"] for side in lay.SIDES}
                for side in lay.SIDES:
                    self.assertEqual(results[f"apertures_{side}"]["evidence"]["through"], n[side], side)
                    self.assertEqual(n[side], list(walls.values()).count(side), side)
                if rid == "V1":                    # both ports through the same short end
                    self.assertEqual(set(jacks), set(usb))
                    self.assertEqual(n[usb[0]], 2)
                elif rid == "V3":                  # USB and jack through opposite short ends
                    self.assertEqual(len(jacks), 1)
                    self.assertEqual({usb[0][1], jacks[0][1]}, {"X"})
                    self.assertNotEqual(usb[0], jacks[0])
                else:                              # USB through a short end, three jacks through one long side
                    self.assertEqual(usb[0][1], "X")
                    self.assertEqual(len(jacks), 3)
                    self.assertEqual(len(set(jacks)), 1)
                    self.assertEqual(jacks[0][1], "Y")
        self.assertEqual(self.runs["V3"][3]["choices"]["stack[module_1]"]["by"], "rule:text_evidence")
        for rid in ("V1", "V2"):                   # no word for a mounting: male headers by default, never a coin flip
            self.assertEqual(self.runs[rid][3]["choices"]["stack[module_1]"]["by"], "rule:catalogue_default")
            self.assertNotIn("assy_stack", self.runs[rid][2].labels())


class TestReplayIter008(unittest.TestCase):
    """Iteration 008's real-run answers (ARCHITECTURE.md 7.11): Contents said the Pico's connector was not exposed (target_s0
    1:2, V1_s8 0:3) although L1.5 names a micro-USB cable. Exposure is now a rule (rule:text_coverage): no question is
    asked, the votes are recorded under `overrides`, and the USB opening is there."""

    RUNS = (("target_s0", "E1-01"), ("V1_s8", "V1"))

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rules = test_rules(cls.root, fn=24)
        cls.runs = {}
        for run, rid in cls.RUNS:
            if not recorded_answers(run, ITER008):
                continue
            llm = recorded_llm(run, ITER008)
            rc, pkg, _ = run_offline(rid, cls.root, cls.rules, llm=llm, tag=run)
            cls.runs[run] = (rid, rc, pkg, llm, json.loads((pkg / "design.json").read_text())["assembly"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def get(self, run):
        if run not in self.runs:
            self.skipTest(f"no recorded transcripts in {ITER008 / run}")
        return self.runs[run]

    def common(self, run):
        """Assertions shared by both runs: rule exposure with the quoted L1 and the recorded votes, coverage closed,
        only the grid conflict failing, the USB plug check present and passing."""
        rid, rc, pkg, llm, assy = self.get(run)
        self.assertNotIn("assy_expose", llm.labels())
        pico = next(c for c in assy["contents"] if c["part"] == "rpi_pico2")
        self.assertTrue(pico["exposed"])
        ch = assy["choices"][f"exposed[{pico['id']}]"]
        self.assertEqual((ch["value"], ch["by"]), (True, "rule:text_coverage"))
        naming = l1_with(rid, "micro-USB cable")
        self.assertTrue(any(e["source"] == naming and e["quote"] in l1_text(rid, naming) for e in ch["evidence"]),
                        ch["evidence"])
        self.assertEqual(ch["overrides"]["contents_votes"], recorded_votes(run, ITER008, "rpi_pico2"))
        self.assertEqual([c["resolved"] for c in assy["coverage"]], ["exposed"])
        results = {r["check_id"]: r for r in assy["results"]}
        self.assertTrue(results["text_coverage"]["passed"], results["text_coverage"]["evidence"])
        # changed in iteration 010 (C1-C5): nothing fails any more (was grid_conformance only, rc 3)
        self.assertEqual([k for k, r in results.items() if not r["passed"]], [], assy["notes"])
        self.assertEqual(rc, ca.EXIT_OK)
        refs = {r["id"]: r for r in json.loads((pkg / "layout.json").read_text())["references"]}
        pico_id = next(k for k, r in refs.items() if r["part"] == "rpi_pico2")
        plug = f"clear_{pico_id}_plug"
        self.assertIn(plug, results)
        self.assertTrue(results[plug]["passed"], results[plug]["evidence"])
        return rid, pkg, assy, results, refs, pico_id

    def test_target_s0_exposes_the_named_usb_without_a_question(self):
        rid, pkg, assy, results, refs, pico_id = self.common("target_s0")
        side = refs[pico_id]["edge"]
        self.assertEqual(side[1], "X")                                    # a short end of the board
        ev = results[f"apertures_{side}"]["evidence"]
        self.assertEqual((ev["expected"], ev["through"]), (1, 1), ev)
        # changed in iteration 010 (behaviour intentionally changed, C4 / L2.1.3): the USB mouth is no longer flush; the
        # first pin is on the grid column nearest the edge, so the mouth sits (column - edge - first pin) inside the
        # flush position: edge + overhang + that inward move (part data and the board's grid, never typed)
        cat = pt.Catalog.load(PARTS)
        board_ref = next(r for r in refs.values() if r["role"] == "board")
        self.assertEqual((board_ref["x"], board_ref["y"], board_ref["rot_z"]), (0, 0, 0))
        edges = lay.board_edges(cat.instantiate(board_ref["part"], board_ref["params"]))
        r = refs[pico_id]
        inst = cat.instantiate(r["part"], r["params"])
        placed = lay.Placed(pico_id, r["part"], r["params"], r["x"], r["y"], r["z"], r["rot_z"], r["item"], r["copy"],
                            r["role"], r["edge"], r["of"], inst=inst)
        conn = inst.connectors[0]
        u = np.asarray(pt.lookup_datum(inst.datums, conn["axis"]).dir, dtype=float)
        lo, hi = inst.bbox(cat.get(r["part"]).data["size_of"])
        face = max(float(np.dot(lo, u)), float(np.dot(hi, u)))
        overhang = float(np.dot(pt.lookup_datum(inst.datums, conn["mouth"]).at, u)) - face
        e = edges[side]
        mouth = lay.world_datum(placed, conn["mouth"]).at
        grid = lay.board_grid(cat.instantiate(board_ref["part"], board_ref["params"]))
        col = grid.origin[e["axis"]] + (0 if e["sign"] < 0 else (grid.count[e["axis"]] - 1) * grid.pitch)
        first = inst.params["pin_from_short_edge"]
        inward = abs(col - e["coord"]) - first
        self.assertGreater(inward, 0.0)
        self.assertAlmostEqual(mouth[e["axis"]], e["coord"] + e["sign"] * (overhang - inward), places=6)

    def test_v1_s8_exposes_the_named_usb(self):
        rid, pkg, assy, results, refs, pico_id = self.common("V1_s8")
        walls = {k[len("oversize_"):]: c["params"]["wall"] for k, c in check_params(pkg).items()
                 if c["type"] == "aperture_oversize"}
        usb = [w for cut, w in walls.items() if cut.startswith(pico_id)]
        jacks = [w for cut, w in walls.items() if not cut.startswith(pico_id)]
        self.assertEqual(len(usb), 1, walls)
        self.assertEqual(set(jacks), set(usb))                            # the USB opening is on the jack's wall
        for side in lay.SIDES:
            ev = results[f"apertures_{side}"]["evidence"]
            self.assertEqual(ev["through"], ev["expected"], side)
            self.assertEqual(ev["expected"], list(walls.values()).count(side), side)


# ---------------------------------------------------------------------------
# iteration 010 (ARCHITECTURE.md 7.13): measured board, M2 board screw, on-grid placement, new sensors
# ---------------------------------------------------------------------------

ITER010 = REPO / "benchmarks" / "enclosure" / "loop" / "iter_010"


def catalogue_copy(root: Path, edits=None) -> Path:
    """A copy of the catalogue under root/parts with edits {part id: fn(data) -> data or None (drop the part)}."""
    out = root / "parts"
    out.mkdir(parents=True, exist_ok=True)
    for src in PARTS.iterdir():
        if not (src / "part.json").is_file():
            continue
        data = json.loads((src / "part.json").read_text())
        if edits and src.name in edits:
            data = edits[src.name](copy.deepcopy(data))
            if data is None:
                continue
        (out / src.name).mkdir()
        (out / src.name / "part.json").write_text(json.dumps(data))
    return out


def measure_with_parts(rid: str, root: Path, parts: Path, rules_path: Path = RULES_PATH, llm=None):
    """measure_manifold with another catalogue folder: the scripted controller up to DeriveFeatures, the manifold
    bodies and the rule-derived plan run on them. Returns (state, {check id: result})."""
    d = new_design(rid, root, rules_path=rules_path)
    d.assy.parts_dir = str(parts)
    tree = A.build_assembly_tree(d, llm or FakeLLM(script_for(rid)), parts, d.assy.rules_path)
    for child in tree.children:
        status = child.update()
        assert status == ca.Status.SUCCESS, (type(child).__name__, d.assy.notes[-3:])
        if type(child).__name__ == "DeriveFeatures":
            break
    st = d.assy
    st.resolved = A.resolve(st)
    st.solids = {b: fg.body_solid(st.graph, b, st.resolved) for b in st.graph.bodies()}
    st.plan = A.build_plan(st)
    return st, {r.check_id: r for r in ac.run_plan(st.plan, st.solids)}


def replan(st):
    """Re-resolve a (mutated) state and run its rule-derived plan on fresh solids."""
    st.resolved = A.resolve(st)
    st.solids = {b: fg.body_solid(st.graph, b, st.resolved) for b in st.graph.bodies()}
    st.plan = A.build_plan(st)
    return {r.check_id: r for r in ac.run_plan(st.plan, st.solids)}


def pico_pins(p):
    return [np.asarray(q) for name in p.inst.part.data["mount"]["stack_pins"] for q in lay.world_datum(p, name).at]


class TestFasteners(unittest.TestCase):
    def test_board_screw_through_given_hole(self):
        # RC-1002: the board's hole is a given datum, so a screw passes it when its thread fits (A9: M2 in Ø2.0)
        cat = pt.Catalog.load(PARTS)
        rules = pt.load_rules(RULES_PATH).values
        w, d, _, _ = request_numbers("E1-01")
        board = cat.instantiate("perfboard", {"width": w, "depth": d})
        hole = pt.lookup_datum(board.datums, "HOLE").diameter
        screw = A.board_screw(cat, board, rules)
        self.assertEqual(screw.id, "screw_m2_selftap")
        self.assertLessEqual(pt.instantiate(screw).params["thread_diameter"], hole + rules["measure_tol"])
        # M2.5 does not pass the measured Ø2.0 hole: without the M2 part no screw is chosen (the iteration 010 G5 cause
        # was M2.5 chosen for the stale Ø3.0 hole); on a Ø3.0 hole the smallest passing thread is still chosen
        no_m2 = pt.Catalog.load(catalogue_copy(Path(self.tmp()), {"screw_m2_selftap": lambda data: None}))
        self.assertIsNone(A.board_screw(no_m2, no_m2.instantiate("perfboard", {"width": w, "depth": d}), rules))
        wide = no_m2.instantiate("perfboard", {"width": w, "depth": d, "hole_diameter": 3.0})
        self.assertEqual(A.board_screw(no_m2, wide, rules).id, "screw_m2p5_selftap")
        self.assertEqual(A.board_screw(cat, cat.instantiate("perfboard", {"width": w, "depth": d, "hole_diameter": 3.0}),
                                       rules).id, "screw_m2_selftap")
        # a Ø1.5 hole takes no catalogue screw: ArrangeContents fails with the typed message
        self.assertIsNone(A.board_screw(cat, cat.instantiate("perfboard", {"width": w, "depth": d, "hole_diameter": 1.5}),
                                        rules))
        st, llm, status = TestArrange.arrange(self, script_for("E1-01"), board={"hole_diameter": 1.5})
        self.assertEqual(status, ca.Status.FAILURE)
        self.assertEqual(st.stage, "arrange_contents")
        self.assertIn("no catalogue screw passes the board's mounting holes", st.notes[-1])
        # the lid screw is still the largest thread
        self.assertEqual(A.lid_screw(cat, rules).id, "screw_m3_selftap")

    def tmp(self) -> str:
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        return t.name


class TestGridPlacement(unittest.TestCase):
    """RC-1004 (C4): a through-hole part whose pins can meet the grid sits with every pin on an existing hole, nearest
    its chosen edge; a finite grid never uses lattice points in the board margin."""

    def test_pico_first_pin_on_column_nearest_edge(self):
        cat, rules, placer = placer_for("E1-01")
        layout = placer.place(items(2), {"pico": "-X", "jack": "+X"})
        grid = placer.grid
        self.assertIsNotNone(grid.count)
        pico = layout.get("pico_1")
        pins = pico_pins(pico)
        self.assertAlmostEqual(min(q[0] for q in pins), grid.origin[0], places=9)      # grid column 0
        for q in pins:
            self.assertLessEqual(float(np.linalg.norm(grid.offset(q))), 1e-6)
        part = cat.instantiate("rpi_pico2").params
        (m, u), = mouths(layout, "pico")
        self.assertAlmostEqual(m[0], grid.origin[0] - part["pin_from_short_edge"] - part["usb_overhang"], places=9)
        self.assertEqual(layout.snaps["pico_1"]["status"], "snapped")
        w = layout.get("board").params["width"]
        for k in (1, 2):                               # the jacks: pin_pattern, exempt, not moved, still flush
            self.assertEqual(layout.snaps[f"jack_{k}"]["status"], "pin_pattern")
        for jmouth, _ in mouths(layout, "jack"):
            self.assertAlmostEqual(jmouth[0], w, places=9)
        report = placer.grid_report(layout.placed, layout.snaps)
        self.assertEqual(report["parts"]["pico_1"]["kind"], "ok")
        self.assertEqual(sorted(report["exempt"]), ["jack_1", "jack_2"])
        self.assertLessEqual(report["max"], 1e-6)
        self.assertFalse(report["soft"])
        self.assertTrue(report["finite"])

    def margin_board(self, root: Path, finite: bool):
        """A synthetic perfboard whose grid margin leaves two lattice columns in the margin (fixture numbers)."""
        def edit(data):
            data["params"]["grid_margin_x"]["default"] = 7.5
            data["self_checks"] = [c for c in data["self_checks"] if "grid" not in c["name"]]
            if not finite:
                del data["grid"]["count"]
            return data
        cat = pt.Catalog.load(catalogue_copy(root, {"perfboard": edit}))
        rules = pt.load_rules(RULES_PATH).values
        w, d, _, _ = request_numbers("E1-01")
        board = cat.instantiate("perfboard", {"width": w, "depth": d})
        placed = lay.Placed("board", "perfboard", {"width": w, "depth": d}, 0, 0, 0, 0, "", role="board", inst=board)
        return cat, lay.Placer(cat, placed, rules, 7.0, rules["component_height_default"])

    def test_finite_grid_never_uses_margin_lattice_points(self):
        cat = pt.Catalog.load(PARTS)
        first = cat.instantiate("rpi_pico2").params["pin_from_short_edge"]
        out = {}
        for finite in (True, False):
            with tempfile.TemporaryDirectory() as tmp:
                _, placer = self.margin_board(Path(tmp), finite)
                layout = placer.place(items(2), {"pico": "-X", "jack": "+X"})
                pins = pico_pins(layout.get("pico_1"))
                out[finite] = (min(q[0] for q in pins), placer.grid)
        x_fin, grid = out[True]
        p = grid.pitch
        lattice_first = grid.origin[0] - p * math.floor((grid.origin[0] - first) / p)     # nearest lattice column >= flush
        self.assertLess(lattice_first, grid.origin[0] - 1e-6)            # the fixture has lattice points in the margin
        self.assertAlmostEqual(x_fin, grid.origin[0], places=9)          # finite: column 0, never the margin point
        self.assertGreater(x_fin - first, lattice_first - first + 1e-6)
        x_inf, _ = out[False]
        self.assertAlmostEqual(x_inf, lattice_first, places=9)           # an infinite lattice takes the margin point

    def test_grid_extent_and_blocked_kinds(self):
        import types
        rules = pt.load_rules(RULES_PATH).values
        cat = pt.Catalog.load(PARTS)
        pico = cat.instantiate("rpi_pico2").params
        # grid_extent: a board as long as the Pico but with fewer grid columns than its pin row needs
        width = pico["pcb_length"] + 1.0
        _, _, placer = placer_for("E1-01", w=width, d=40.0)
        layout = placer.place(items(0)[:1], {"pico": "-X"})
        row = pt.lookup_datum(cat.instantiate("rpi_pico2").datums, "PINS_A").at
        self.assertLess((placer.grid.count[0] - 1) * placer.grid.pitch, (len(row) - 1) * pico["pin_pitch"])
        self.assertEqual(layout.snaps["pico_1"]["status"], "grid_extent")
        rep = placer.grid_report(layout.placed, layout.snaps)
        self.assertEqual(rep["parts"]["pico_1"]["kind"], "grid_extent")
        st = types.SimpleNamespace(grid_report=rep, rules=types.SimpleNamespace(values=rules), placed=layout)
        plan = ac.Plan(tol=ac.Tol.from_rules(rules))
        A.grid_check(st, plan)
        res = ac.run_plan(plan, {})
        self.assertFalse(res[0].passed)
        self.assertEqual([(c["part"], c["kind"]) for c in A.conflict_entries(res)], [("pico_1", "grid_extent")])
        # blocked: every on-grid position collides (a fixture obstacle on each), the pairs are listed
        _, _, placer = placer_for("E1-01")
        with mock.patch.object(lay.Placer, "_hits", lambda self, trial, others, solids: [f"{trial[0].node_id} x obstacle"]):
            layout = placer.place(items(2), {"pico": "-X", "jack": "+X"})
        snap = layout.snaps["pico_1"]
        self.assertEqual(snap["status"], "blocked")
        self.assertEqual(snap["pairs"], ["pico_1 x obstacle"])
        self.assertEqual(snap["tried"], len(placer.snap_moves(layout.get("pico_1"))[0]))
        rep = placer.grid_report(layout.placed, layout.snaps)
        self.assertEqual(rep["parts"]["pico_1"]["kind"], "blocked")
        self.assertEqual(rep["parts"]["pico_1"]["blocked_by"], ["pico_1 x obstacle"])
        st = types.SimpleNamespace(grid_report=rep, rules=types.SimpleNamespace(values=rules), placed=layout)
        plan = ac.Plan(tol=ac.Tol.from_rules(rules))
        A.grid_check(st, plan)
        res = ac.run_plan(plan, {})
        entries = A.conflict_entries(res)
        self.assertEqual([(c["part"], c["kind"]) for c in entries], [("pico_1", "blocked")])
        self.assertIn("pico_1 x obstacle", entries[0]["conflict"])
        # pin_pattern: the jacks' drawing pins meet no lattice position: exempt with an assumption, never failing
        _, _, placer = placer_for("E1-01")
        layout = placer.place(items(2), {"pico": "-X", "jack": "+X"})
        rep = placer.grid_report(layout.placed, layout.snaps)
        st = types.SimpleNamespace(grid_report=rep, rules=types.SimpleNamespace(values=rules), placed=layout)
        plan = ac.Plan(tol=ac.Tol.from_rules(rules))
        A.grid_check(st, plan)
        res = ac.run_plan(plan, {})
        self.assertTrue(res[0].passed, res[0].evidence["detail"])
        exempt = res[0].evidence["exempt"]
        self.assertEqual(sorted(e["part"] for e in exempt), ["jack_1", "jack_2"])
        self.assertTrue(all("enlarged holes" in e["assumption"] and e["best_any"] > rules["grid_residual_max"]
                            for e in exempt))
        self.assertEqual(A.conflict_entries(res), [])
        # non-vacuous: a module with a feasible pattern left off the grid still fails
        p = layout.get("pico_1")
        moved = lay.Placed(p.node_id, p.part, p.params, p.x + placer.grid.pitch / 2, p.y, p.z, p.rot_z, p.item, p.copy,
                           p.role, p.edge, p.of, p.inst)
        rep = placer.grid_report([moved if q is p else q for q in layout.placed], layout.snaps)
        self.assertEqual(rep["parts"]["pico_1"]["kind"], "tangential")
        self.assertGreater(rep["max"], rules["grid_residual_max"])

    def test_resolve_keeps_grid(self):
        cat, rules, placer = placer_for("E1-01")
        layout = placer.place(items(2), {"pico": "-X", "jack": "+X"})
        pico = layout.get("pico_1")
        stacks = [q for q in layout.placed if q.of == "pico_1"]
        lo, hi = lay.bbox_of(pico.inst, pico.pose)
        # a fixture obstacle (a request-sized cylinder) over the Pico's +Y edge forces a collision shift
        it = lay.Item("obstacle", "generic_cylinder", {"diameter": 3.0, "height": 10.0}, 1, False)
        inst = cat.instantiate("generic_cylinder", it.params)
        olo, ohi = lay.bbox_of(inst, np.eye(4))
        ob = lay.Placed("obstacle_1", "generic_cylinder", dict(it.params), float((lo[0] + hi[0]) / 2 - (olo[0] + ohi[0]) / 2),
                        float(hi[1] - 1.5 - (olo[1] + ohi[1]) / 2), 0.0, 0.0, "obstacle", inst=inst)
        pico_item = items(2)[0]
        groups = {"pico_1": ([pico] + stacks, pico_item), "obstacle_1": ([ob], it)}
        self.assertTrue(placer.collisions([pico] + stacks + [ob]))
        out = placer._resolve("pico_1", groups, snapped=True)
        dy = out[0].y - pico.y
        self.assertGreater(abs(dy), 0.0)
        k = dy / placer.grid.pitch
        self.assertAlmostEqual(k, round(k), places=9)
        self.assertTrue(placer.on_grid(out[0]))
        for q in pico_pins(out[0]):
            self.assertLessEqual(float(np.linalg.norm(placer.grid.offset(q))), 1e-6)
        self.assertEqual(placer.collisions(out + [ob, layout.get("board")]), [])


class TestIter010Sensors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_column_takes_board_keepout(self):
        # RC-1003: the seat / hole_ko column is max(board keep-out, head + 2 x driver_clearance), and the cavity follows
        st, res = derived("E1-01", self.root / "a")
        r = st.rules.values
        board = st.placed.get("board")
        holes = lay.world_datum(board, "HOLE")
        expect = max(holes.keepout_diameter, st.fasteners["fastener.board.head_diameter"] + 2 * r["driver_clearance"])
        self.assertGreater(holes.keepout_diameter, st.fasteners["fastener.board.head_diameter"] + 2 * r["driver_clearance"])
        for i in range(len(holes.at)):
            self.assertAlmostEqual(res.params[f"seat_{i}"]["d"], expect, places=9)
            self.assertAlmostEqual(res.params[f"hole_ko_{i}"]["d"], expect, places=9)
        y_hole = min(h[1] for h in holes.at)
        cav = res.params["cavity"]
        self.assertLessEqual(cav["y0"], y_hole - expect / 2 - r["design_margin"] + 1e-9)
        self.assertTrue(any("rule:hole_column_d" in n for n in st.notes), st.notes)

        def no_keepout(data):
            del data["datums"]["HOLE"]["keepout_diameter"]
            return data
        parts = catalogue_copy(self.root / "m", {"perfboard": no_keepout})
        st2, _ = measure_with_parts("E1-01", self.root / "m", parts)
        res2 = st2.resolved
        fallback = st2.fasteners["fastener.board.head_diameter"] + 2 * r["driver_clearance"]
        for i in range(len(holes.at)):
            self.assertAlmostEqual(res2.params[f"seat_{i}"]["d"], fallback, places=9)
        bound = y_hole - max(fallback, r["driver_diameter"]) / 2 - r["design_margin"]
        self.assertAlmostEqual(res2.params["cavity"]["y0"], bound, places=9)
        self.assertGreater(res2.params["cavity"]["y0"], cav["y0"] + 1e-6)          # the bound follows the data

    def test_plug_clear_of_references(self):
        # C5: E1-01's plugs clear the references; a flat-soldered module (USB axis a little over 2.4 above the board,
        # fixture) moved inward puts its overmold into the board, and the board is named
        st, res = measure_manifold("E1-01", self.root / "a")
        checks = {k: v for k, v in res.items() if k.startswith("plug_refs_")}
        self.assertEqual(len(checks), sum(it.quantity for it in st.items if it.exposed))
        usb = next(v for k, v in checks.items() if k.startswith("plug_refs_module_"))
        self.assertTrue(usb.passed)
        self.assertGreaterEqual(usb.evidence["d"], 1.0)
        self.assertTrue(all(v.passed for v in checks.values()))
        self.assertEqual(usb.evidence["per_source"]["board"]["part"], "perfboard")
        self.assertAlmostEqual(usb.evidence["d"], usb.evidence["per_source"]["board"]["d"], places=6)

        def flat(data):
            data["params"]["spacer_height"]["default"] = 0.01
            data["self_checks"] = [c for c in data["self_checks"] if "height" not in c["name"]]
            return data
        parts = catalogue_copy(self.root / "f", {"header_male_2p54": flat})
        # the check is part of the prescore's controllable error: every short-end Pico candidate is removed by it
        st1, _ = measure_with_parts("E1-01", self.root / "p", parts)
        removed = [f for f in st1.arrange["filtered"] if f["assignment"]["module_1"][1] == "X"]
        self.assertTrue(removed, st1.arrange["filtered"])
        self.assertTrue(all(any(c.startswith("plug_refs_module_") for c in f["failing"]) for f in removed))
        # with the prescore filter off, the scripted (voted) arrangement is built and the check names the board
        with mock.patch.object(A, "prescore_survivors", lambda cands: list(range(len(cands)))):
            st2, res2 = measure_with_parts("E1-01", self.root / "f", parts)
        self.assertEqual(st2.choices["edge[module_1]"]["value"], SCRIPTED["E1-01"]["edges"]["module_1"])
        pico = next(p for p in st2.placed.placed if p.part == "rpi_pico2")
        axis_z = lay.world_datum(pico, pico.inst.connectors[0]["axis"]).at[2]
        self.assertLess(axis_z, 2.5)
        bad = res2[f"plug_refs_{pico.node_id}_plug"]
        self.assertFalse(bad.passed)
        self.assertGreater(bad.evidence["per_source"]["board"]["penetration_mm3"], 0.0)
        self.assertIsNone(bad.evidence["per_source"]["board"]["d"])
        self.assertTrue(res2[f"clear_{pico.node_id}_plug"].passed)     # the body-only plug check cannot see it

    def test_pilot_band_and_screw_hole_checks(self):
        # C6: pilot diameter within the chosen fastener's band; the board screw's thread passes the board hole
        st, res = measure_manifold("E1-01", self.root / "a")
        bands = {k: v for k, v in res.items() if k.startswith("pilot_band_")}
        self.assertEqual(len(bands), sum(1 for n in st.graph if n.role in ("standoff", "boss")))
        f = st.fasteners
        for k, v in bands.items():
            self.assertTrue(v.passed, v.evidence)
        self.assertAlmostEqual(res["pilot_band_standoff_1"].evidence["value"], f["fastener.board.pilot_diameter"])
        self.assertEqual((res["pilot_band_standoff_1"].evidence["lo"], res["pilot_band_standoff_1"].evidence["hi"]),
                         (f["fastener.board.pilot_min"], f["fastener.board.pilot_max"]))
        self.assertTrue(res["board_screw_passes_hole"].passed)
        # mutant: an M2.5 pilot on the M2 board screw
        m25 = pt.instantiate(st.catalog.get("screw_m2p5_selftap")).params["pilot_diameter"]
        st.graph.nodes["standoff_1_pilot"].params["d"] = m25
        res2 = replan(st)
        self.assertFalse(res2["pilot_band_standoff_1"].passed)
        self.assertTrue(res2["pilot_band_standoff_2"].passed)
        # mutant: a board hole smaller than the M2 thread
        st.graph.nodes["standoff_1_pilot"].params["d"] = "fastener.board.pilot_diameter"
        board = st.placed.get("board")
        board.inst.datums["HOLE"].diameter = f["fastener.board.thread_diameter"] - 0.1
        res3 = replan(st)
        self.assertFalse(res3["board_screw_passes_hole"].passed)
        self.assertTrue(res3["pilot_band_standoff_1"].passed)


def inscribed_pilot(base, axis_xy, z: float) -> float:
    """The inscribed diameter of the hole round axis_xy in the base mesh's cross-section at height z (the test's own
    recipe: 2 x the smallest distance from the axis to the edges of the loop that encloses it)."""
    polys = base.slice(z).to_polygons()
    best = None
    q = np.asarray(axis_xy, dtype=float)
    for poly in polys:
        pts = np.asarray(poly, dtype=float)
        a, b = pts, np.roll(pts, -1, axis=0)
        ab = b - a
        t = np.clip(((q - a) * ab).sum(axis=1) / np.maximum((ab * ab).sum(axis=1), 1e-18), 0, 1)
        dist = np.linalg.norm(a + t[:, None] * ab - q, axis=1).min()
        if dist < 5.0 and (best is None or dist < best):
            best = dist
    return 2 * best


class TestEndToEndIter010(unittest.TestCase):
    """E1-01 and V1-V3 (scripted, fn 24, OpenSCAD meshes): the measured board package verifies with no conflicts."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rules = test_rules(cls.root, fn=24)
        cls.runs = {rid: run_offline(rid, cls.root, cls.rules) for rid in ("E1-01", "V1", "V2", "V3")}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_measured_board_package(self):
        rules = pt.load_rules(self.rules).values
        cat = pt.Catalog.load(PARTS)
        for rid, (rc, pkg, _) in self.runs.items():
            with self.subTest(rid=rid):
                rec = json.loads((pkg / "design.json").read_text())
                assy = rec["assembly"]
                self.assertEqual([r["check_id"] for r in assy["results"] if not r["passed"]], [], assy["notes"][-5:])
                self.assertEqual((rc, rec["outcome"]), (ca.EXIT_OK, "verified"))
                self.assertEqual(assy["conflicts"], [])
                report = json.loads((pkg / "self_report.json").read_text())
                self.assertTrue(report["all_passed"])
                # standoffs on the HOLE datums: their pitch is the board's hole pitch
                refs = json.loads((pkg / "layout.json").read_text())["references"]
                bref = next(r for r in refs if r["role"] == "board")
                binst = cat.instantiate(bref["part"], bref["params"])
                holes = np.asarray(pt.lookup_datum(binst.datums, "HOLE").at)[:, :2]
                comps = {c["id"]: c for c in assy["components"]}
                axes = np.asarray([[(comps[f"standoff_{k + 1}"]["bbox"][0][i] + comps[f"standoff_{k + 1}"]["bbox"][1][i]) / 2
                                    for i in (0, 1)] for k in range(len(holes))])
                np.testing.assert_allclose(axes, holes, atol=1e-3)
                # the pilot measured on the delivered STL: inscribed Ø = the M2 pilot, within 0.02
                base = ac.load_mesh(pkg / "base.stl")
                screw = cat.instantiate(assy["choices"]["fastener[board]"]["value"]).params
                top = comps["standoff_1"]["bbox"][1][2]
                for k, h in enumerate(holes):
                    d = inscribed_pilot(base, h, top - screw["min_engagement"] / 2)
                    self.assertAlmostEqual(d, screw["pilot_diameter"], delta=0.02, msg=(rid, k))
                # the board-clearance exemption is the column grown by the clearance: Ø(keep-out + 2 x board_clearance)
                clear = next(c for c in json.loads((pkg / "checks.json").read_text()) if c["id"] == "clear_board")
                graph = fg.FeatureGraph.from_json((pkg / "feature_graph.json").read_text())
                res = graph.resolve(assy["spec"], rules, catalog=cat, fasteners=assy["fasteners"])
                bc = assy["spec"]["board_clearance"]
                self.assertEqual(clear["params"]["minus_grown_by"], bc)
                ko = pt.lookup_datum(binst.datums, "HOLE").keepout_diameter
                for n in graph:
                    if n.role == "seat":
                        self.assertAlmostEqual(res.params[n.id]["d"] + 2 * bc, ko + 2 * bc, places=9)
                n = requirement_reference_comparisons(self, pkg, rules)
                self.assertGreaterEqual(n, 4)


class TestReplayIter010(unittest.TestCase):
    """Iteration 010's real-run answers (iter_010/target_s0/*/llm) replayed offline: with the measured board, the M2
    screw and on-grid placement the package verifies, with the Pico's first pin on grid column 0."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rules = test_rules(cls.root, fn=24)
        cls.llm = recorded_llm("target_s0", ITER010)
        cls.rc, cls.pkg, _ = run_offline("E1-01", cls.root, cls.rules, llm=cls.llm)
        cls.rec = json.loads((cls.pkg / "design.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_replay_iter010_answers_verify(self):
        assy = self.rec["assembly"]
        self.assertEqual([r["check_id"] for r in assy["results"] if not r["passed"]], [], assy["notes"][-5:])
        self.assertEqual((self.rc, self.rec["outcome"]), (ca.EXIT_OK, "verified"))
        self.assertEqual(assy["conflicts"], [])
        self.assertEqual(assy["choices"]["fastener[board]"]["value"], "screw_m2_selftap")
        refs = {r["id"]: r for r in json.loads((self.pkg / "layout.json").read_text())["references"]}
        cat = pt.Catalog.load(PARTS)
        bref = next(r for r in refs.values() if r["role"] == "board")
        grid = lay.board_grid(cat.instantiate(bref["part"], bref["params"]))
        r = next(r for r in refs.values() if r["part"] == "rpi_pico2")
        inst = cat.instantiate(r["part"], r["params"])
        p = lay.Placed(r["id"], r["part"], r["params"], r["x"], r["y"], r["z"], r["rot_z"], r["item"], r["copy"],
                       r["role"], r["edge"], r["of"], inst=inst)
        pins = pico_pins(p)
        near = min(pins, key=lambda q: abs(q[0] - (0.0 if r["edge"] == "-X" else bref["params"]["width"])))
        self.assertEqual(r["edge"][1], "X")
        col = 0 if r["edge"] == "-X" else grid.count[0] - 1
        self.assertAlmostEqual(near[0], grid.origin[0] + col * grid.pitch, places=6)
        for q in pins:
            self.assertLessEqual(float(np.linalg.norm(grid.offset(q))), 1e-6)


ITER011 = REPO / "benchmarks" / "enclosure" / "loop" / "iter_011"


def loop_centroid(base, z: float, near, area_lo: float, area_hi: float):
    """The centroid of the cross-section loop of the base mesh at height z that lies nearest `near` and whose area is in
    [area_lo, area_hi] (the test's own recipe, as the judges slice the delivered STL); None if there is none."""
    best = None
    q = np.asarray(near, dtype=float)
    for poly in base.slice(z).to_polygons():
        pts = np.asarray(poly, dtype=float)
        x, y = pts[:, 0], pts[:, 1]
        cross = x * np.roll(y, -1) - np.roll(x, -1) * y
        area = cross.sum() / 2
        if not area_lo <= abs(area) <= area_hi:
            continue
        c = np.array([((x + np.roll(x, -1)) * cross).sum(), ((y + np.roll(y, -1)) * cross).sum()]) / (6 * area)
        dist = float(np.linalg.norm(c - q))
        if best is None or dist < best[0]:
            best = (dist, c)
    return None if best is None else best[1]


class TestEndToEndIter011(unittest.TestCase):
    """iteration 011 (C1-C3): each variant board keeps the catalogue family holes (3.0 at 2.5); E1-01's photographed
    board is the specimen and its package is unchanged. Scripted, fn 24, OpenSCAD meshes."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rules = test_rules(cls.root, fn=24)
        cls.runs = {rid: run_offline(rid, cls.root, cls.rules) for rid in ("E1-01", "V1", "V2", "V3")}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def package(self, rid):
        rc, pkg, _ = self.runs[rid]
        rec = json.loads((pkg / "design.json").read_text())
        return rc, pkg, rec, rec["assembly"], json.loads((pkg / "layout.json").read_text())

    def test_variant_boards_use_family_holes(self):
        rules = pt.load_rules(self.rules).values
        cat = pt.Catalog.load(PARTS)
        for rid in ("V1", "V2", "V3"):
            with self.subTest(rid=rid):
                rc, pkg, rec, assy, lay_json = self.package(rid)
                self.assertEqual([r["check_id"] for r in assy["results"] if not r["passed"]], [], assy["notes"][-5:])
                self.assertEqual((rc, rec["outcome"]), (ca.EXIT_OK, "verified"))
                self.assertEqual(assy["conflicts"], [])
                w, d, _, _ = request_numbers(rid)
                expect = np.array([(2.5, 2.5), (w - 2.5, 2.5), (2.5, d - 2.5), (w - 2.5, d - 2.5)])
                board = lay_json["board"]
                self.assertIsNone(board["specimen"])
                self.assertEqual(board["hole_diameter"], 3.0)
                bref = next(r for r in lay_json["references"] if r["role"] == "board")
                binst = cat.instantiate(bref["part"], bref["params"])
                np.testing.assert_allclose(board["holes"], pt.lookup_datum(binst.datums, "HOLE").at, atol=1e-6)
                np.testing.assert_allclose(np.asarray(board["holes"])[:, :2], expect, atol=1e-9)
                self.assertEqual(board["params"], binst.params)
                self.assertEqual(board["screw"], assy["choices"]["fastener[board]"]["value"])
                # standoff and pilot axes, sliced from the delivered base STL
                base = ac.load_mesh(pkg / "base.stl")
                comps = {c["id"]: c for c in assy["components"]}
                screw = cat.instantiate(board["screw"]).params
                self.assertEqual(board["screw"], "screw_m2_selftap")
                top = comps["standoff_1"]["bbox"][1][2]
                z = top - screw["min_engagement"] / 2
                pilot_a = math.pi * (screw["pilot_diameter"] / 2) ** 2
                axes = []
                for k, h in enumerate(expect):
                    pilot = loop_centroid(base, z, h, 0.5 * pilot_a, 1.5 * pilot_a)
                    self.assertIsNotNone(pilot, (rid, k))
                    self.assertLessEqual(float(np.linalg.norm(pilot - h)), 0.05, (rid, k, pilot))
                    box = comps[f"standoff_{k + 1}"]["bbox"]
                    axis = np.array([(box[0][i] + box[1][i]) / 2 for i in (0, 1)])
                    self.assertLessEqual(float(np.linalg.norm(axis - h)), 0.05, (rid, k, axis))
                    axes.append(axis)
                    self.assertAlmostEqual(inscribed_pilot(base, h, z), screw["pilot_diameter"], delta=0.02)
                axes = np.asarray(axes)
                self.assertAlmostEqual(axes[1][0] - axes[0][0], w - 5.0, delta=0.05)
                self.assertAlmostEqual(axes[2][1] - axes[0][1], d - 5.0, delta=0.05)
                res = {r["check_id"]: r for r in assy["results"]}
                self.assertLessEqual(max(res["seated"]["evidence"]["residuals"]), 0.05)
                self.assertTrue(res["board_screw_passes_hole"]["passed"])
                self.assertIn("Ø3", res["board_screw_passes_hole"]["evidence"]["detail"])
                # clear_driver_k against an independent driver column on the family holes (Ø rules.driver_diameter,
                # from the board top to past the base)
                drivers = {k: v for k, v in res.items() if k.startswith("clear_driver_")}
                self.assertEqual(len(drivers), 4)
                hi = base.bounding_box()[5]
                for cid, r in drivers.items():
                    k = int(cid.rsplit("_", 1)[1])
                    col = fg.m3d.Manifold.cylinder(hi + 5.0, rules["driver_diameter"] / 2, rules["driver_diameter"] / 2,
                                                   64).translate([float(expect[k][0]), float(expect[k][1]), 0.0])
                    gap = float(base.min_gap(col, 10.0))
                    self.assertAlmostEqual(r["evidence"]["d"], gap, delta=0.10, msg=(rid, cid))
                # the hole-pattern assumption is in design.json
                self.assertEqual(len([a for a in assy["assumptions"] if "mounting-hole" in a]), 1)

    def test_e1_unchanged(self):
        rc, pkg, rec, assy, lay_json = self.package("E1-01")
        self.assertEqual((rc, rec["outcome"]), (ca.EXIT_OK, "verified"))
        self.assertEqual(lay_json["board"]["specimen"], "photo_70x50")
        self.assertEqual(lay_json["board"]["hole_diameter"], 2.0)
        comps = {c["id"]: c for c in assy["components"]}
        ax = [[(comps[f"standoff_{k}"]["bbox"][0][i] + comps[f"standoff_{k}"]["bbox"][1][i]) / 2 for i in (0, 1)]
              for k in (1, 2, 3)]
        self.assertAlmostEqual(ax[1][0] - ax[0][0], 66.0, delta=1e-3)
        self.assertAlmostEqual(ax[2][1] - ax[0][1], 46.0, delta=1e-3)
        res = {r["check_id"]: r for r in assy["results"]}
        np.testing.assert_allclose(res["bbox"]["evidence"]["size"], [84.17, 64.17, 24.70], atol=0.01)
        self.assertAlmostEqual(assy["fasteners"]["fastener.board.pilot_diameter"], 1.7, places=9)
        self.assertFalse([a for a in assy["assumptions"] if "mounting-hole" in a])

    def test_layout_grid_residual_matches_check(self):
        # iteration 011 (C2): layout.json's grid_residual is the grid_conformance value; the exempt ids are the
        # pin_pattern parts, and the all-parts number is labelled as such
        for rid in self.runs:
            with self.subTest(rid=rid):
                _, _, _, assy, lay_json = self.package(rid)
                grid = next(r for r in assy["results"] if r["check_id"] == "grid_conformance")
                self.assertEqual(lay_json["grid_residual"], grid["evidence"]["value"])
                kinds = grid["evidence"]["kinds"]
                self.assertEqual(sorted(lay_json["grid_exempt"]), sorted(k for k, v in kinds.items() if v == "pin_pattern"))
                self.assertEqual(set(lay_json["grid_exempt_assumptions"]), set(lay_json["grid_exempt"]))
                if lay_json["grid_exempt"]:
                    self.assertGreater(lay_json["grid_residual_all_parts"], lay_json["grid_residual"])
        _, _, _, _, e1 = self.package("E1-01")
        self.assertEqual(e1["grid_residual"], 0.0)
        self.assertEqual(len(e1["grid_exempt"]), SCRIPTED["E1-01"]["jacks"])


class TestReplayIter011(unittest.TestCase):
    """Iteration 011's real-run answers replayed offline: E1-01 (target_s0, real rules) gives the delivered bodies,
    so C1 did not move E1-01; V1_s0 now puts the standoffs on the family holes (2.5 inset)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_replay_iter011_answers(self):
        delivered = sorted((ITER011 / "target_s0").glob("*/self_report.json"))
        if not delivered:
            raise unittest.SkipTest(f"no delivered package in {ITER011 / 'target_s0'}")
        rc, pkg, _ = run_offline("E1-01", self.root, RULES_PATH, llm=recorded_llm("target_s0", ITER011))
        self.assertEqual(rc, ca.EXIT_OK)
        report = json.loads((pkg / "self_report.json").read_text())
        old = json.loads(delivered[-1].read_text())["bodies"]
        for body in ("base", "lid"):
            self.assertAlmostEqual(report["bodies"][body]["volume"], old[body]["volume"],
                                   delta=0.005 * old[body]["volume"], msg=body)
        rules = test_rules(self.root, fn=24)
        rc, pkg, _ = run_offline("V1", self.root, rules, llm=recorded_llm("V1_s0", ITER011))
        rec = json.loads((pkg / "design.json").read_text())
        self.assertEqual((rc, rec["outcome"]), (ca.EXIT_OK, "verified"), rec["assembly"]["notes"][-5:])
        w, d, _, _ = request_numbers("V1")
        comps = {c["id"]: c for c in rec["assembly"]["components"]}
        expect = [(2.5, 2.5), (w - 2.5, 2.5), (2.5, d - 2.5), (w - 2.5, d - 2.5)]
        for k, h in enumerate(expect):
            box = comps[f"standoff_{k + 1}"]["bbox"]
            np.testing.assert_allclose([(box[0][i] + box[1][i]) / 2 for i in (0, 1)], h, atol=1e-3)


# ---------------------------------------------------------------------------
# Generalize delta 001 (GM2a): primary reference, lid fastener, both catalogues, number ownership, archetype gate,
# per-connector exposure. Train requests are loaded as data (ARCHITECTURE.md 6); nothing here is typed into the agent.
# ---------------------------------------------------------------------------

GEN_PARTS = REPO / "benchmarks" / "generalize" / "parts"
BOTH = [GEN_PARTS, PARTS]                 # the order run_suite.py passes them (the first folder wins an id)
GEN_DESIGNS = REPO / "benchmarks" / "generalize" / "designs"
ITER001_GEN = REPO / "benchmarks" / "generalize" / "loop" / "iter_001"


def gen_request(gid: str) -> dict:
    return json.loads((GEN_DESIGNS / gid / "design.json").read_text())["requests"][0]


def gen_texts(gid: str, l1=None):
    r = gen_request(gid)
    return [("request", r["request"])] + [(x["id"], x["text"]) for x in (r["l1"] if l1 is None else l1)]


def design_for(request_text: str, l1: list, root: Path, parts=BOTH, rules_path: Path = RULES_PATH):
    import os
    d = ca.Design(request=ca.request_with_l1(request_text, l1), workdir=root, l1=l1, base_request=request_text)
    dirs = [str(p) for p in parts]
    d.assy = A.AssemblyState(parts_dir=os.pathsep.join(dirs), parts_dirs=dirs, rules_path=str(rules_path))
    return d


def gen_design(gid: str, root: Path, l1=None, parts=BOTH):
    r = gen_request(gid)
    return design_for(r["request"], r["l1"] if l1 is None else l1, root / gid, parts)


def all_none(prompt):
    return {k: "none" for k in A_SLOTS}


def recorded_prompt(run_dir: Path, label: str):
    """The PROMPT section of the first recorded transcript with this label in a package's llm/ folder (None if absent)."""
    files = sorted(run_dir.glob(f"*/llm/*_{label}.txt"))
    if not files:
        return None
    text = files[0].read_text()
    return text.split("=== PROMPT ===\n", 1)[1].split("\n\n=== RESPONSE ===", 1)[0]


class TestPrimaryReference(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_module_is_primary_without_board_slots(self):
        # T1: a fixed-size module the text names is the primary; no board size slot is needed and no perfboard is
        # invented (iteration 001 stopped at ParseSpec: "no number in the text for board_width, board_depth")
        cat = pt.Catalog.load(BOTH)
        module = next(pid for pid in cat.ids() if pt.mount_interface(cat.get(pid)) is not None
                      and A.text_evidence(gen_texts("G04"), cat.get(pid).names) and not pt.is_carrier(cat.get(pid)))
        conns = cat.get(module).data["connectors"]
        reply = {module: dict({"quantity": 1}, **{A.exposure_key(c): "yes" for c in conns})}
        d = gen_design("G04", self.root)
        llm = SchemaLLM({"assy_spec": [all_none], "assy_contents": [reply]})
        status, _ = run_stages(d, llm, "Contents")
        st = d.assy
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        self.assertNotIn("board_width", st.spec)
        self.assertEqual(st.choices["primary"]["by"], "rule:primary_reference")
        self.assertEqual(st.choices["primary"]["value"], module)
        prim = A.primary_item(st)
        self.assertEqual((prim["id"], prim["part"]), (A.PRIMARY, module))
        self.assertFalse([c for c in st.contents if pt.is_carrier(cat.get(c["part"]))])
        self.assertEqual(sorted(prim["exposed_connectors"]), sorted(c["name"] for c in conns))
        schema = next(sc for lb, sc in llm.schemas if lb == "assy_contents")["properties"][module]["properties"]
        self.assertEqual(set(schema), {"quantity"} | {A.exposure_key(c) for c in conns})   # one key per connector
        self.assertEqual(st.items, [])
        self.assertEqual(st.unplaced, [])

    def test_carrier_stays_primary(self):
        # T2: the carrier (a part with a grid block) is the primary, and the ParseSpec and Contents prompts are byte-equal
        # to the ones iteration 001 recorded for E1-01 (so the regression set sees the same questions)
        d = new_design("E1-01", self.root)
        llm = FakeLLM(script_for("E1-01"))
        status, _ = run_stages(d, llm, "Contents")
        st = d.assy
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        prim = A.primary_item(st)
        self.assertTrue(pt.is_carrier(st.catalog.get(prim["part"])))
        self.assertEqual(st.choices["primary"]["by"], "rule:primary_reference")
        self.assertEqual(st.choices["primary"]["reason"], "carrier")
        w, dd, _, _ = request_numbers("E1-01")
        self.assertEqual(list(prim["params"].values()), [w, dd])
        self.assertEqual([i.id for i in st.items], ["module_1", "connector_1"])
        run = ITER001_GEN / "E1-01_s1"
        for label in ("assy_spec", "assy_contents"):
            want = recorded_prompt(run, label)
            if want is None:
                raise unittest.SkipTest(f"no recorded {label} transcript in {run}")
            got = next(p for lb, p, _ in llm.calls if lb == label)
            self.assertEqual(got, want, label)

    def test_primary_without_mount_holes_stops_typed(self):
        # T3: the largest content part offers no mount_holes interface: a typed note, no exception, no package
        cat = pt.Catalog.load(BOTH)
        texts_ = gen_texts("G05")
        named = [pid for pid in cat.ids() if cat.get(pid).kind == "module" and A.text_evidence(texts_, cat.get(pid).names)]
        holeless = [pid for pid in named if pt.mount_interface(cat.get(pid)) is None]
        with_holes = [pid for pid in cat.ids() if pt.mount_interface(cat.get(pid)) is not None
                      and A.text_evidence(texts_, cat.get(pid).names)]
        self.assertTrue(holeless and with_holes, (named, with_holes))
        reply = {pid: {"quantity": 1, "exposed": "yes"} for pid in holeless + with_holes}
        d = gen_design("G05", self.root)
        status, child = run_stages(d, FakeLLM({"assy_spec": [all_none], "assy_contents": [reply]}), "Contents")
        st = d.assy
        self.assertEqual(status, ca.Status.FAILURE)
        self.assertEqual(st.stage, "contents")
        self.assertTrue(any("has no mount_holes interface" in n and holeless[0] in n for n in st.notes), st.notes)
        self.assertFalse(any("exactly one board" in n for n in st.notes))

    def test_non_carrier_primary_lists_unplaced(self):
        # C1: a non-carrier primary carries no other contents; each other item is unplaced with a failing hard
        # content_placed check, so the package is honest (measured on the manifold solids, no OpenSCAD)
        cat = pt.Catalog.load(BOTH)
        texts_ = gen_texts("G06")
        named = [pid for pid in cat.ids() if pt.mount_interface(cat.get(pid)) is not None
                 and A.text_evidence(texts_, cat.get(pid).names)]
        self.assertGreaterEqual(len(named), 2, named)
        reply = {pid: dict({"quantity": 1}, **({"exposed": "yes"} if cat.get(pid).data.get("connectors") else {}))
                 for pid in named}
        d = gen_design("G06", self.root)
        status, _ = run_stages(d, FakeLLM({"assy_spec": [all_none], "assy_contents": [reply]}), "DeriveFeatures")
        st = d.assy
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        prim = A.primary_item(st)
        area = {pid: A.plan_footprint(cat, {"part": pid}) for pid in named}
        self.assertEqual(prim["part"], max(area, key=area.get))
        self.assertEqual(st.choices["primary"]["reason"], "largest plan footprint")
        self.assertEqual(len(st.unplaced), len(named) - 1)
        self.assertEqual([p.node_id for p in st.placed.placed], [A.PRIMARY])
        st.solids = {b: fg.body_solid(st.graph, b, st.resolved) for b in st.graph.bodies()}
        results = {r.check_id: r for r in ac.run_plan(A.build_plan(st), st.solids)}
        for u in st.unplaced:
            r = results[f"content_placed_{u['id']}"]
            self.assertFalse(r.passed)
            self.assertTrue(r.hard)
        self.assertNotIn("inside_contents", results)


def fastener_text(words: str):
    return [("request", words)]


class TestLidFastener(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = pt.load_rules(RULES_PATH).values
        cls.enc = pt.Catalog.load(PARTS)
        cls.both = pt.Catalog.load(BOTH)

    def test_unified_catalogue_default(self):
        # T6: a text with no fastener words: the largest catalogue-complete screw, the same part the enclosure catalogue
        # alone gives (iteration 001 picked a 1/4-20 screw whose length must come from the request)
        texts_ = texts("E1-01")
        one = A.lid_screw_choice(self.enc, self.rules, texts_)
        two = A.lid_screw_choice(self.both, self.rules, texts_)
        self.assertEqual(two["part"].id, one["part"].id)
        self.assertEqual(two["by"], "rule:largest_complete_screw")
        self.assertTrue(A.catalogue_complete(two["part"]))
        incomplete = [pid for pid in self.both.ids() if self.both.get(pid).kind == "fastener"
                      and not A.catalogue_complete(self.both.get(pid))]
        self.assertTrue(incomplete)
        self.assertNotIn(two["part"].id, incomplete)
        self.assertEqual(A.lid_screw(self.both, self.rules).id, one["part"].id)
        board = self.both.instantiate("perfboard", {"width": 70.0, "depth": 50.0})
        self.assertEqual(A.board_screw(self.both, board, self.rules).id, A.board_screw(self.enc, board, self.rules).id)

    def test_named_fastener_wins(self):
        # T7: the text names the lid screw: that screw, by rule:text_evidence, with the quote
        cat = self.both
        complete = [pid for pid in cat.ids() if cat.get(pid).kind == "fastener" and A.catalogue_complete(cat.get(pid))
                    and all(cat.get(pid).params.get(k, {}).get("default") is not None for k in A.LID_FIELDS)]
        largest = A.lid_screw_choice(cat, self.rules, ())["part"].id
        target = next(pid for pid in complete if pid != largest)
        alias = cat.get(target).names[0]
        words = f"The lid is held by four {alias}s."
        pick = A.lid_screw_choice(cat, self.rules, fastener_text(words))
        self.assertEqual((pick["part"].id, pick["by"]), (target, "rule:text_evidence"))
        self.assertEqual(pick["evidence"][0]["quote"], words)
        # a named fastener that is not catalogue-complete is skipped and reported; the default rule then decides
        bolt = next(pid for pid in cat.ids() if cat.get(pid).kind == "fastener" and not A.catalogue_complete(cat.get(pid))
                    and "pilot_diameter" not in cat.get(pid).params)
        words = f"All screws are {cat.get(bolt).names[-1]}s."
        pick = A.lid_screw_choice(cat, self.rules, fastener_text(words))
        self.assertIn(bolt, pick["skipped"])
        self.assertEqual(pick["part"].id, largest)

    def test_shared_alias_is_not_a_skip(self):
        # Fix round 1 N3: an alias a complete and an incomplete fastener share names the complete one; no skip note
        cat = self.both
        fast = [cat.get(pid) for pid in cat.ids() if cat.get(pid).kind == "fastener"]
        pair = next(((a, c, w) for a in fast if not A.catalogue_complete(a) for c in fast if A.catalogue_complete(c)
                     and all(c.params.get(k, {}).get("default") is not None for k in A.LID_FIELDS)
                     for w in a.names if w in c.names), None)
        if pair is None:
            self.skipTest("no alias shared by a complete and an incomplete fastener in the catalogues")
        bolt, screw, alias = pair
        pick = A.lid_screw_choice(cat, self.rules, fastener_text(f"The lid is held by four {alias}s."))
        self.assertEqual((pick["part"].id, pick["by"]), (screw.id, "rule:text_evidence"))
        self.assertNotIn(bolt.id, pick["skipped"])
        own = next(w for w in bolt.names if w not in screw.names)       # its own alias still reports the skip
        pick = A.lid_screw_choice(cat, self.rules, fastener_text(f"The lid is held by four {own}s."))
        self.assertIn(bolt.id, pick["skipped"])


def stage_through(design, llm, upto: str, parts=None):
    tree = A.build_assembly_tree(design, llm, parts or PARTS, design.assy.rules_path)
    for child in tree.children:
        status = child.update()
        if status != ca.Status.SUCCESS or type(child).__name__ == upto:
            return status, child
    return ca.Status.SUCCESS, None


class TestBothCatalogues(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def built(self, parts, tag):
        r = request("E1-01")
        d = design_for(r["request"], r["l1"], self.root / tag, parts, test_rules(self.root, fn=24))
        status, child = stage_through(d, FakeLLM(script_for("E1-01")), "Build")
        self.assertEqual(status, ca.Status.SUCCESS, (type(child).__name__, d.assy.notes[-5:]))
        return d.assy

    def test_e1_01_derives(self):
        # T8 (GM1 c): E1-01 scripted through Build on both catalogues builds, and its poses and fasteners equal the
        # enclosure-only run (iteration 001: an uncaught MissingParam at derive_features)
        one, two = self.built([PARTS], "enc"), self.built(BOTH, "both")
        self.assertEqual(set(one.layout), set(two.layout))
        for nid, ref in one.layout.items():
            for k in ("x", "y", "z", "rot_z"):
                self.assertAlmostEqual(two.layout[nid][k], ref[k], delta=0.01, msg=f"{nid}.{k}")
        self.assertEqual(set(one.fasteners), set(two.fasteners))
        for k, v in one.fasteners.items():
            self.assertAlmostEqual(two.fasteners[k], v, delta=0.01, msg=k)
        self.assertEqual(two.choices["fastener[lid]"]["value"], one.choices["fastener[lid]"]["value"])
        for b in ("base", "lid"):
            self.assertAlmostEqual(two.solids[b].volume(), one.solids[b].volume(), delta=0.01, msg=b)

    def test_derive_contains_part_errors(self):
        # T9: a fastener with an unresolved request param forced into derive: a typed note, never a traceback
        r = request("E1-01")
        d = design_for(r["request"], r["l1"], self.root / "t9", BOTH)
        status, child = stage_through(d, FakeLLM(script_for("E1-01")), "ChooseArchetype")
        self.assertEqual(status, ca.Status.SUCCESS, d.assy.notes[-3:])
        cat = d.assy.catalog
        bad = next(pid for pid in cat.ids() if cat.get(pid).kind == "fastener" and not A.catalogue_complete(cat.get(pid))
                   and all(cat.get(pid).params.get(k, {}).get("default") is not None for k in A.LID_FIELDS))
        forced = {"part": cat.get(bad), "by": "test", "evidence": [], "skipped": []}
        with mock.patch.object(A, "lid_screw_choice", lambda *a, **k: forced):
            err = A.derive(A.scratch_state(d.assy))
            self.assertTrue(err and err.startswith("derivation failed:"), err)
            self.assertIn("must come from the request", err)
            step = A.DeriveFeatures(d)
            self.assertEqual(step.update(), ca.Status.FAILURE)
        self.assertTrue(d.assy.notes[-1].startswith("derivation failed:"), d.assy.notes[-1])
        self.assertEqual(d.assy.stage, "derive_features")


class TestNumberOwnership(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def ids(self):
        import re
        rid = "V3"
        tall = cylinder_params_reply(rid)["height"]
        head = re.search(r"at least (\d+) mm of space above the tallest part", request(rid)["request"])
        three = number_id(rid, float(head.group(1)), "request")
        return rid, tall, three

    def test_spec_slot_and_part_param_share_a_number(self):
        # T10 (the V3 seed-1 defect): ParseSpec maps headroom to the capacitor's "20 mm tall" and ask_params maps the
        # capacitor height to the same occurrence. The owner question runs across the stages; the height keeps it and
        # headroom is re-asked without it.
        rid, tall, three = self.ids()
        spec = dict(spec_reply(rid), headroom=tall)
        d = new_design(rid, self.root / "a")
        llm = SchemaLLM(script_for(rid, assy_spec=[spec], assy_spec_owner=[{"owner": "generic_1.height"}],
                                   assy_spec_slot=[{"headroom": three}]))
        status, _ = run_stages(d, llm, "Contents")
        st = d.assy
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        self.assertEqual(llm.labels().count("assy_spec_owner"), ca.VOTES)
        owner_schema = next(sc for lb, sc in llm.schemas if lb == "assy_spec_owner")
        self.assertEqual(owner_schema["properties"]["owner"]["enum"], ["headroom", "generic_1.height"])
        slot_schema = next(sc for lb, sc in llm.schemas if lb == "assy_spec_slot")
        self.assertEqual(list(slot_schema["properties"]), ["headroom"])
        self.assertNotIn(tall, slot_schema["properties"]["headroom"]["enum"])
        cap = next(c for c in st.contents if c["part"] == "generic_cylinder")
        self.assertEqual(cap["params"]["height"], 20.0)
        self.assertEqual(st.spec["headroom"], 3.0)
        self.assertIn("space above the tallest part", st.spec_provenance["headroom"])
        self.assertEqual((st.number_owner[tall], st.number_owner[three]), ("generic_1.height", "headroom"))
        # the spec slot wins instead: the part size is re-asked without that occurrence (it takes the L1's 20)
        d = new_design(rid, self.root / "b")
        l1_tall = number_id(rid, 20.0, l1_with(rid, "tall upright capacitor"))
        llm = SchemaLLM(script_for(rid, assy_spec=[spec], assy_spec_owner=[{"owner": "headroom"}],
                                   assy_params_reask=[{"height": l1_tall}]))
        status, _ = run_stages(d, llm, "Contents")
        st = d.assy
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        reask = next(sc for lb, sc in llm.schemas if lb == "assy_params_reask")
        self.assertNotIn(tall, reask["properties"]["height"]["enum"])
        self.assertEqual(st.number_owner[tall], "headroom")
        self.assertEqual(st.number_owner[l1_tall], "generic_1.height")
        self.assertTrue(st.spec_provenance["generic_1.height"].startswith(l1_with(rid, "tall upright capacitor")))

    def test_part_size_reask_is_final(self):
        # Fix round 1 R1: the spec slot keeps the number and the part-size re-ask picks another spec slot's number. The
        # re-ask is final: no second owner question, a typed stop, a bounded number of owner calls (was a RecursionError).
        import re
        rid, tall, three = self.ids()
        spec = spec_reply(rid)
        other = spec["max_z"]                         # a number another spec slot owns
        spec = dict(spec, headroom=tall)
        reasks = []

        def owner(prompt):
            names = re.findall(r"^- ([\w.]+): ", prompt.split("Which one")[1], re.M)
            return {"owner": next(n for n in names if "." not in n)}     # the spec slot always keeps its number

        def reask(prompt):
            reasks.append(prompt)
            return {"height": other}
        d = new_design(rid, self.root)
        llm = FakeLLM(script_for(rid, assy_spec=[spec], assy_spec_owner=[owner], assy_params_reask=[reask]))
        status, _ = run_stages(d, llm, "Contents")
        st = d.assy
        self.assertEqual(status, ca.Status.FAILURE, st.notes)
        self.assertEqual(llm.labels().count("assy_spec_owner"), ca.VOTES)      # one owner question, never a second
        self.assertEqual(llm.labels().count("assy_params_reask"), ca.VOTES)    # one re-ask
        self.assertTrue(reasks)
        self.assertFalse(any(re.search(rf"^{re.escape(tall)} = ", p, re.M) for p in reasks))  # the id is removed
        stop = st.notes[-1]
        self.assertIn("re-ask is final", stop)
        self.assertIn(f"{other} ", stop)
        self.assertIn("max_z", stop)
        self.assertEqual((st.number_owner[tall], st.number_owner[other]), ("headroom", "max_z"))
        self.assertNotIn("generic_1.height", st.number_owner.values())

    def test_reasked_spec_slot_keeps_parse_spec_rules(self):
        # Fix round 1 N2: a spec slot re-asked after ParseSpec meets the same relations (> 0, wall band) and the frame
        # rule (board_width along the longest edge, ownership swapped with the values)
        rules = pt.load_rules(RULES_PATH)
        st = A.AssemblyState(rules=rules, texts=[])
        st.spec = {"wall_min": 2.0, "wall_max": 3.0, "board_width": 50.0, "board_depth": 40.0}
        self.assertIsNone(A.spec_relation_error(st.spec, "wall_max", 2.5))
        self.assertIn("greater than 0", A.spec_relation_error(st.spec, "headroom", 0.0))
        self.assertIn("must not exceed", A.spec_relation_error(st.spec, "wall_max", 1.5))
        self.assertIn("must not exceed", A.spec_relation_error(st.spec, "wall_min", 3.5))
        st.spec["board_depth"] = 70.0                                   # a re-asked depth now longer than the width
        st.spec_provenance = {"board_width": "request:w", "board_depth": "request:d"}
        st.number_owner = {"n1": "board_width", "n2": "board_depth", "n3": "wall_min"}
        A.settle_spec(st, "contents")
        self.assertEqual((st.spec["board_width"], st.spec["board_depth"]), (70.0, 50.0))
        self.assertEqual(st.spec_provenance, {"board_width": "request:d", "board_depth": "request:w"})
        self.assertEqual(st.number_owner, {"n1": "board_depth", "n2": "board_width", "n3": "wall_min"})
        self.assertIn("contents: board_width/board_depth swapped", st.notes[-1])

    def test_no_conflict_asks_nothing(self):
        # the regression answers: no shared occurrence, so no owner question (prompts and labels as before)
        rid = "V3"
        d = new_design(rid, self.root)
        llm = FakeLLM(script_for(rid))
        status, _ = run_stages(d, llm, "Contents")
        self.assertEqual(status, ca.Status.SUCCESS, d.assy.notes)
        self.assertNotIn("assy_spec_owner", llm.labels())


class TestDescribeConnectors(unittest.TestCase):
    def test_describe_names_the_exposed_connectors(self):
        # Fix round 1 N1: the arrangement words name the item's exposed connectors, not the part's first one
        inst = type("Inst", (), {"connectors": [{"name": "first"}, {"name": "second"}, {"name": "third"}]})()
        layout = lay.Layout(placed=[lay.Placed("m", "p", {}, 0.0, 0.0, 0.0, 0.0, "item_1", edge="e", inst=inst)],
                            edges={"e": {"words": "the short end at -X"}})
        multi = lay.Item("item_1", "p", name="module", connectors=["second", "third"])
        self.assertEqual(lay.describe(layout, [multi]), "module (second, third) faces the short end at -X")
        first = lay.Item("item_1", "p", name="module")                 # no names given: the first connector, as before
        self.assertEqual(lay.describe(layout, [first]), "module (first) faces the short end at -X")


class TestArchetypeGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = pt.Catalog.load(BOTH)
        cls.rules = pt.load_rules(RULES_PATH)

    def state(self, texts_, part):
        st = A.AssemblyState(catalog=self.cat, rules=self.rules, texts=list(texts_))
        st.contents = [{"id": A.PRIMARY, "part": part, "kind": self.cat.get(part).kind, "quantity": 1}]
        return st

    def test_shell_needs_evidence(self):
        # T11: the same mount_holes primary; a shell only with shell words in the text (G40 is a drill guide)
        g40 = gen_texts("G40")
        module = next(pid for pid in self.cat.ids() if pt.mount_interface(self.cat.get(pid)) is not None
                      and A.text_evidence(g40, self.cat.get(pid).names))
        st = self.state(g40, module)
        self.assertEqual(A.feasible_archetypes(st), [])
        err = A.choose_archetype_rule(st)
        self.assertTrue(err.startswith("not implemented: archetype"), err)
        self.assertIn("no shell evidence", err)
        st = self.state(texts("E1-01"), "perfboard")
        self.assertEqual(A.feasible_archetypes(st), [("tray_lid", "screws")])
        self.assertIsNone(A.choose_archetype_rule(st))
        self.assertEqual(st.choices["archetype"]["value"], "tray_lid+screws")
        holeless = next(pid for pid in self.cat.ids() if self.cat.get(pid).kind == "module"
                        and pt.mount_interface(self.cat.get(pid)) is None)
        self.assertEqual(A.feasible_archetypes(self.state(texts("E1-01"), holeless)), [])


class TestExposure(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_primary_connectors_and_multi_connector_parts(self):
        # T12: a primary with three connectors; the texts name the plug that two of them take. Both are exposed (text
        # coverage, per connector), each with its own plug sweep and port cut on the wall its axis faces, recorded
        # rule:fixed_by_primary; the third stays closed. Iteration 001 exposed only a content part's first connector.
        cat = pt.Catalog.load(BOTH)
        r = gen_request("G04")
        prim = next(pid for pid in cat.ids() if pt.mount_interface(cat.get(pid)) is not None
                    and A.text_evidence(gen_texts("G04"), cat.get(pid).names) and len(cat.get(pid).data["connectors"]) == 3)
        conns = cat.get(prim).data["connectors"]
        mates = Counter(c["mates"] for c in conns)
        plug, n = mates.most_common(1)[0]
        self.assertEqual(n, 2)
        named = [x for x in r["l1"] if A.text_evidence([(x["id"], x["text"])], cat.get(plug).names)]
        others = [c["mates"] for c in conns if c["mates"] != plug]
        shell = [x for x in r["l1"] if A.text_evidence([(x["id"], x["text"])], ["lid"])]
        l1 = [x for x in named + shell if not A.text_evidence([(x["id"], x["text"])],
                                                                [a for o in others for a in cat.get(o).names])]
        self.assertTrue(l1)
        self.assertFalse(A.text_evidence([("request", r["request"])], [a for o in [plug] + others
                                                                         for a in cat.get(o).names]))
        reply = {prim: dict({"quantity": 1}, **{A.exposure_key(c): "no" for c in conns})}
        d = design_for(r["request"], l1, self.root / "t12", BOTH)
        status, child = run_stages(d, FakeLLM({"assy_spec": [all_none], "assy_contents": [reply]}), "DeriveFeatures")
        st = d.assy
        self.assertEqual(status, ca.Status.SUCCESS, (type(child).__name__, st.notes[-3:]))
        want = sorted(c["name"] for c in conns if c["mates"] == plug)
        got = [(p.node_id, c["name"]) for p, c in A.exposed_connectors(st)]
        self.assertEqual(sorted(name for _, name in got), want)
        self.assertTrue(all(node == A.PRIMARY for node, _ in got))
        board = st.placed.get(A.PRIMARY)
        for c in [c for c in conns if c["name"] in want]:
            key = f"{A.PRIMARY}_{c['name']}"
            self.assertTrue(any(nd.id.startswith(f"{key}_plug_") for nd in st.graph), key)
            cut = st.graph.nodes[f"{key}_cut"]
            wall = A.wall_facing(lay.world_datum(board, c["axis"]).dir)
            self.assertEqual(cut.wall, wall)
            self.assertEqual(st.choices[f"wall[{A.PRIMARY}.{c['name']}]"], {"value": wall, "by": "rule:fixed_by_primary"})
            self.assertEqual(st.choices[f"exposed[{A.PRIMARY}.{c['name']}]"]["by"], A.COVERAGE_RULE)
        closed = [c["name"] for c in conns if c["name"] not in want]
        for name in closed:
            self.assertNotIn(f"{A.PRIMARY}_{name}_cut", st.graph.nodes)
        st.solids = {b: fg.body_solid(st.graph, b, st.resolved) for b in st.graph.bodies()}
        results = {x.check_id: x for x in ac.run_plan(A.build_plan(st), st.solids)}
        self.assertTrue(results["text_coverage"].passed, results["text_coverage"].evidence)
        for name in want:
            self.assertIn(f"clear_{A.PRIMARY}_{name}_plug", results)


if __name__ == "__main__":
    unittest.main()
