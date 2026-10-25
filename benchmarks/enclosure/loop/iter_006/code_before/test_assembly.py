"""Tests for --mode assembly: CLI wiring, the controller interface (ParseSpec, Contents, ChooseStack,
ArrangeContents + ConfirmArrangement), DeriveFeatures, the package and an offline end-to-end run.

No Ollama: OllamaAgent is replaced by a scripted fake keyed by question label. Request and L1
texts come from benchmarks/enclosure/enclosure.json and variants.json; expected numbers are
computed in the test from those texts and from part data, never typed into the agent.
"""

import copy
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
        # A request with no board size: every slot is answered "none"; the size slots have no default, so
        # ParseSpec re-asks once naming the violation and then fails with a typed note (exit 1).
        out = self.root / "out"
        llm = FakeLLM({"assy_spec": [lambda p: {k: "none" for k in A_SLOTS}]})
        rc = self.run_main("--mode", "assembly", "--auto", "--l1", str(self.l1), "--parts", str(self.parts),
                           "--out", str(out), "an enclosure", llm=llm)
        self.assertEqual(rc, ca.EXIT_FAILED)
        rec = self.design_record(out)
        self.assertEqual(rec["outcome"], "failed")
        assy = rec["assembly"]
        self.assertEqual(assy["stage"], "parse_spec")
        self.assertTrue(any("no number in the text for board_width" in n for n in assy["notes"]), assy["notes"])
        self.assertEqual(llm.labels().count("assy_spec_reask"), ca.VOTES)
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

    def test_two_boards_is_a_typed_failure(self):
        d = new_design("E1-01", self.root)
        script = script_for("E1-01", assy_contents=[{"perfboard": {"quantity": 2}}])
        status, child = run_stages(d, FakeLLM(script), "Contents")
        self.assertEqual(status, ca.Status.FAILURE)
        self.assertEqual(d.assy.stage, "contents")
        self.assertTrue(any("exactly one board" in n for n in d.assy.notes))

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
                  "assy_stack": [{"stack": "header_female_2p54"}]}
        d = new_design(rid, self.root)
        status, _ = run_stages(d, FakeLLM(script), "ChooseStack")
        self.assertEqual(status, ca.Status.SUCCESS)
        cap = next(c for c in d.assy.contents if c["part"] == "generic_cylinder")
        self.assertEqual(cap["params"], {"diameter": 10.0, "height": 20.0})
        self.assertEqual(d.assy.choices["stack[module_1]"]["value"], "header_female_2p54")


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
        self.assertAlmostEqual(m[0], -pico.params["usb_overhang"], places=9)
        w = layout.get("board").params["width"]
        jm = mouths(layout, "jack")
        for jmouth, ju in jm:
            np.testing.assert_allclose(ju, [1, 0, 0], atol=1e-9)
            self.assertAlmostEqual(jmouth[0], w, places=9)
        need = self.spacing_need(cat, rules, "jack_3p5_pj320a", "jack_3p5_pj320a")
        self.assertGreaterEqual(abs(jm[0][0][1] - jm[1][0][1]), need)
        self.assert_clean(placer, layout)
        # the Pico's pins sit on the board grid along the edge (Y); X stays flush with the edge
        origin, pitch = placer.grid
        for name in ("PINS_A", "PINS_B"):
            for q in lay.world_datum(layout.get("pico_1"), name).at:
                r = (q[1] - origin[1] + pitch / 2) % pitch - pitch / 2
                self.assertLessEqual(abs(r), 1e-6)
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
        self.assertAlmostEqual(gaps[0], gaps[1], places=9)          # spread with equal gaps
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

    def test_grid_report_names_the_normal_conflict(self):
        # iteration 004 (C4): the residual is sensed per part; the Pico's is normal to its -X edge
        cat, rules, placer = placer_for("E1-01")
        layout = placer.place(items(2), {"pico": "-X", "jack": "+X"})
        report = placer.grid_report(layout.placed)
        origin, pitch = placer.grid
        pico = layout.get("pico_1")
        offs = [(np.asarray(q[:2]) - origin[:2] + pitch / 2) % pitch - pitch / 2
                for name in pico.inst.part.data["mount"]["stack_pins"] for q in lay.world_datum(pico, name).at]
        worst = max(offs, key=np.linalg.norm)
        row = report["parts"]["pico_1"]
        self.assertAlmostEqual(row["residual"], float(np.linalg.norm(worst)), delta=0.01)
        self.assertAlmostEqual(row["normal"], abs(worst[0]), delta=0.01)       # -X edge: the normal is X
        self.assertLessEqual(row["tangential"], 1e-6)                           # snapped along the edge
        self.assertAlmostEqual(row["normal_fix"], -worst[0], places=9)
        self.assertGreater(row["normal"], rules["grid_residual_max"])
        self.assertAlmostEqual(report["max"], row["residual"], places=9)
        self.assertEqual(report["worst"], "pico_1")
        self.assertTrue(report["soft"])
        no_pins = [p.node_id for p in layout.placed if p.role == "content" and p.inst.connectors
                   and not p.inst.part.data.get("mount", {}).get("stack_pins") and "PINS" not in p.inst.datums]
        self.assertEqual(sorted(report["no_pin_data"]), sorted(no_pins))
        self.assertEqual(sorted(no_pins), ["jack_1", "jack_2"])

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
                self.assertTrue(notes)            # the soft grid's mismatch is reported, not silent

    def test_moved_hole_or_hard_grid_leaves_only_the_identity(self):
        tol = pt.load_rules(RULES_PATH).values["measure_tol"]
        w, d, _, _ = request_numbers("E1-01")
        for variant in ("moved_hole", "hard_grid"):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as tmp:
                data = json.loads((PARTS / "perfboard" / "part.json").read_text())
                if variant == "moved_hole":
                    data["datums"]["HOLE"]["at"][3][0] = "width - hole_inset - 1"
                    data["self_checks"] = [c for c in data["self_checks"] if "pitch" not in c["name"]]
                else:
                    data["grid"]["soft"] = False     # grid registered to hole 1 is off-centre on this board
                (Path(tmp) / "perfboard").mkdir()
                (Path(tmp) / "perfboard" / "part.json").write_text(json.dumps(data))
                syms = lay.board_symmetries(self.board(w, d, pt.Catalog.load(tmp)), tol)
                self.assertEqual(syms, [self.IDENTITY])

    def test_square_board_gets_four_rotations_and_classes_are_canonical(self):
        tol = pt.load_rules(RULES_PATH).values["measure_tol"]
        w, _, _, _ = request_numbers("E1-01")
        syms = lay.board_symmetries(self.board(w, w), tol)
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
                    xy = c * (poly - 1) + 1e-6           # circumscribed polygons: the vertex grows c / cos
                    np.testing.assert_allclose(b0[:2] - b1[:2], c, atol=xy)
                    np.testing.assert_allclose(b1[3:5] - b0[3:5], c, atol=xy)
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
                zero_margin = ["clear_keepout_top", "clear_keepout_bottom"] + \
                              [cid for cid in got if cid.endswith("_plug")]
                for cid in zero_margin:
                    lim = got[cid].evidence["clearance"]
                    self.assertAlmostEqual(zero[cid].evidence["gap"], lim, delta=1e-6, msg=cid)
                    self.assertAlmostEqual(got[cid].evidence["gap"] - zero[cid].evidence["gap"], m, delta=1e-6, msg=cid)
                # the opening is the plug plus (plug_to_opening + design_margin) per side, inside the oversize limit
                for cid, res in got.items():
                    if res.type == "aperture_oversize":
                        self.assertTrue(res.passed, res.evidence)

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
        board.params["width"] = board.params["width"] + 5
        res3 = A.resolve(st)
        self.assertAlmostEqual(res3.params["base"]["x"] - base0["x"], 5.0, places=6)
        self.assertAlmostEqual(res3.params["base"]["y"], base0["y"], places=9)
        self.assertAlmostEqual(res3.params["base"]["split"], base0["split"], places=9)


# ---------------------------------------------------------------------------
# The package and the offline end-to-end run (M12 / M13 preview)
# ---------------------------------------------------------------------------


GATE_TYPES = ("separable", "inside", "clear_of", "aperture_count", "aperture_oversize", "seated", "bbox_within")


def run_offline(rid: str, root: Path, rules_path: Path, llm=None, **patches):
    r = request(rid)
    l1 = root / f"{rid}.l1.json"
    l1.write_text(json.dumps(r["l1"]))
    llm = llm or FakeLLM(script_for(rid))
    out = root / f"out_{rid}"
    with mock.patch.object(ca, "OllamaAgent", lambda *a, **k: llm), mock.patch("builtins.print"):
        ctx = [mock.patch.object(ca, k, v) for k, v in patches.items()]
        for c in ctx:
            c.start()
        try:
            rc = ca.main(["--mode", "assembly", "--auto", "--l1", str(l1), "--parts", str(PARTS),
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

    def same(mine, ref, c, what):
        nonlocal n
        case.assertIsNotNone(ref, what)
        case.assertIsNotNone(mine, what)
        case.assertAlmostEqual(mine, min(ref, c + 5.0), delta=tol, msg=f"{pkg.name} {what}")
        n += 1

    # the board minus Ø(seat_d + 2 x board_clearance) columns on its HOLE datums (V-SEAT grown, L2.2.1)
    bref = next(r for r in refs if r["role"] == "board")
    binst, bpose, bsolid = built[bref["id"]]
    bc = rec["spec"]["board_clearance"]
    seat_d = rec["fasteners"]["fastener.board.head_diameter"] + 2 * rules["driver_clearance"]
    lo, hi = bsolid.bounding_box()[2], bsolid.bounding_box()[5]
    cols = [m3d.Manifold.cylinder(hi - lo + 2, (seat_d + 2 * bc) / 2, (seat_d + 2 * bc) / 2, 256)
            .translate([float(h[0]), float(h[1]), lo - 1])
            for h in pt.transform(pt.lookup_datum(binst.datums, "HOLE"), bpose).at]
    board = bsolid - m3d.Manifold.batch_boolean(cols, m3d.OpType.Add)
    same(by_id["clear_board"]["evidence"]["gap"], rubric_clear_of(both, board, bc), bc, "clear_board")
    same(by_id["inside_board"]["evidence"]["d"], rubric_inside(solids, board, bc), bc, "inside_board")
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


def grid_expectation(pkg: Path, rules: dict) -> dict:
    """Grid conformance recomputed by the test from layout.json and part data (not layout.Placer): the worst
    pin-to-grid residual, its component normal to each part's edge, and the parts with a connector but no
    pin data. `fails` is what grid_conformance must say."""
    cat = pt.Catalog.load(PARTS)
    refs = json.loads((pkg / "layout.json").read_text())["references"]
    board = next(r for r in refs if r["role"] == "board")
    binst = cat.instantiate(board["part"], board["params"])
    g = binst.part.data["grid"]
    origin, pitch = fg.evaluate3(g["origin"], binst.env)[:2], fg.evaluate(g["pitch"], binst.env)
    worst, normal, no_pins = 0.0, 0.0, []
    for r in refs:
        if r["role"] != "content":
            continue
        inst = cat.instantiate(r["part"], r["params"])
        names = inst.part.data.get("mount", {}).get("stack_pins") or (["PINS"] if "PINS" in inst.datums else [])
        if not names:
            if inst.connectors:
                no_pins.append(r["id"])
            continue
        pose = lay.pose_of(r["x"], r["y"], r["z"], r["rot_z"])
        for name in names:
            for q in pt.transform(pt.lookup_datum(inst.datums, name), pose).at:
                dv = (np.asarray(q[:2]) - origin + pitch / 2) % pitch - pitch / 2
                if np.linalg.norm(dv) > worst:
                    worst = float(np.linalg.norm(dv))
                    normal = float(abs(dv["XY".index(r["edge"][1])])) if r["edge"] else 0.0
    fails = bool(no_pins) or worst > rules["grid_residual_max"] + rules["measure_tol"]
    return {"worst": worst, "normal": normal, "no_pin_data": sorted(no_pins), "fails": fails,
            "conflict": worst > rules["grid_residual_max"] and normal > rules["grid_residual_max"]}


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
                for name in ("base.stl", "lid.stl", "base.scad", "lid.scad", "model.scad", "layout.json",
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
                lay_json = json.loads((pkg / "layout.json").read_text())
                parts = {r["part"] for r in lay_json["references"]}
                self.assertTrue({"perfboard", "rpi_pico2", "jack_3p5_pj320a"} <= parts)
                self.assertEqual(set(lay_json["bodies"]), {"base", "lid"})

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
        for rid in self.runs:
            with self.subTest(rid=rid):
                rc, pkg, _ = self.runs[rid]
                assy = self.record(rid)["assembly"]
                grid = grid_expectation(pkg, pt.load_rules(self.rules).values)
                check = next(r for r in assy["results"] if r["check_id"] == "grid_conformance")
                self.assertEqual(check["passed"], not grid["fails"])
                self.assertAlmostEqual(check["evidence"]["value"], grid["worst"], delta=1e-6)
                self.assertEqual(sorted(check["evidence"]["no_pin_data"]), grid["no_pin_data"])
                self.assertTrue(check["evidence"]["soft"])
                conflicts = assy["conflicts"]
                self.assertEqual(len(conflicts), 1 if grid["fails"] and grid["conflict"] else 0)
                if conflicts:
                    c = conflicts[0]
                    self.assertEqual((c["check_id"], c["competing_rule"]), ("grid_conformance", "flush_to_edge"))
                    self.assertIn("flush", c["conflict"])
                    self.assertAlmostEqual(abs(c["details"][0]["normal_fix"]), grid["normal"], delta=1e-6)
        grid = grid_expectation(self.runs["E1-01"][1], pt.load_rules(self.rules).values)
        self.assertTrue(grid["fails"] and grid["conflict"])          # E1-01: exactly one typed conflict

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
            self.assertEqual([r["check_id"] for r in rec["results"] if not r["passed"]], ["grid_conformance"])
            self.assertEqual(rc, ca.EXIT_UNSATISFIED)


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
        assy = self.rec["assembly"]
        self.assertEqual([r["check_id"] for r in assy["results"] if not r["passed"]], ["grid_conformance"])
        self.assertEqual(self.rc, ca.EXIT_UNSATISFIED, assy["notes"])
        self.assertEqual(self.rec["outcome"], "unsatisfied")
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
        self.assertEqual([k for k, r in results.items() if not r["passed"]], ["grid_conformance"], assy["notes"])
        self.assertEqual(self.rc, ca.EXIT_UNSATISFIED)
        self.assertEqual(len(assy["conflicts"]), 1)
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
        self.assertEqual([r["check_id"] for r in assy["results"] if not r["passed"]], ["grid_conformance"],
                         assy["notes"])
        self.assertEqual(self.rc, ca.EXIT_UNSATISFIED)
        self.assertEqual(len(assy["conflicts"]), 1)
        report = json.loads((self.pkg / "self_report.json").read_text())
        recorded = ITER005_PKG / "self_report.json"
        if recorded.is_file() and assy["stl_source"] == {"base": "openscad", "lid": "openscad"}:
            old = json.loads(recorded.read_text())["bodies"]
            for body in ("base", "lid"):           # no geometry change: the same bodies as the iteration 005 run
                self.assertAlmostEqual(report["bodies"][body]["volume"], old[body]["volume"], delta=0.01, msg=body)
        n = requirement_reference_comparisons(self, self.pkg, pt.load_rules(RULES_PATH).values)
        self.assertGreaterEqual(n, 4)


if __name__ == "__main__":
    unittest.main()
