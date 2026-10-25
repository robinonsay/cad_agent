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


def spec_reply(rid: str) -> dict:
    """The correct ParseSpec answer for a request: number ids located from the texts."""
    w, d, mx, size_l1 = request_numbers(rid)
    keep = l1_with(rid, "above the board")
    clear = l1_with(rid, "clearance")
    walls = l1_with(rid, "thick")
    over = l1_with(rid, "bigger than")
    return {"board_width": number_id(rid, w, "request"), "board_depth": number_id(rid, d, "request"),
            "keepout_above": number_id(rid, 12, keep), "keepout_below": number_id(rid, 4, keep),
            "board_clearance": number_id(rid, 0.5, clear), "headroom": "none",
            "opening_oversize_max": number_id(rid, 1.5, over),
            "wall_min": number_id(rid, 2, walls), "wall_max": number_id(rid, 4, walls),
            "max_x": number_id(rid, mx[0], size_l1), "max_y": number_id(rid, mx[1], size_l1),
            "max_z": number_id(rid, mx[2], size_l1)}


SCRIPTED = {
    "E1-01": {"jacks": 2, "edges": {"module_1": "-X", "connector_1": "+X"}, "stack": "header_male_2p54"},
    "V1": {"jacks": 1, "edges": {"module_1": "-X", "connector_1": "-X"}, "stack": "header_male_2p54"},
}


def script_for(rid: str, **over) -> dict:
    s = SCRIPTED[rid]
    script = {
        "assy_spec": [spec_reply(rid)],
        "assy_contents": [{"perfboard": {"quantity": 1}, "rpi_pico2": {"quantity": 1, "exposed": "yes"},
                           "jack_3p5_pj320a": {"quantity": s["jacks"], "exposed": "yes"},
                           "generic_cylinder": {"quantity": 0}}],
        "assy_stack": [{"stack": s["stack"]}],
        "assy_edge": [dict(s["edges"])],
        "assy_confirm": [{"answer": "yes"}],
    }
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

    def test_rejected_arrangement_tries_the_next_feasible_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = new_design("E1-01", Path(tmp))
            both = {"module_1": "-X", "connector_1": "-X"}
            llm = FakeLLM(script_for("E1-01", assy_edge=[both], assy_confirm=[{"answer": "no"}, {"answer": "yes"}]))
            status, _ = run_stages(d, llm, "ArrangeContents")
            self.assertEqual(status, ca.Status.SUCCESS)
            confirms = [h for h in d.assy.history if h["stage"] == "confirm_arrangement"]
            self.assertEqual([h["p_yes"] > 0.5 for h in confirms], [False, True])
            self.assertEqual(llm.labels().count("assy_confirm"), 2)
            # all three E1-01 ports on one 50 mm end cannot fit the plugs: pruned before asking, with a note
            self.assertTrue(any("infeasible" in n and "ports_do_not_fit" in n for n in d.assy.notes), d.assy.notes)
            self.assertNotEqual(confirms[0]["assignment"], both)
            used = {k[5:-1]: v["value"] for k, v in d.assy.choices.items() if k.startswith("edge[")}
            self.assertEqual(used, confirms[1]["assignment"])
            self.assertNotEqual(used, confirms[0]["assignment"])


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


def run_offline(rid: str, root: Path, rules_path: Path, **patches):
    r = request(rid)
    l1 = root / f"{rid}.l1.json"
    l1.write_text(json.dumps(r["l1"]))
    llm = FakeLLM(script_for(rid))
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


class TestEndToEnd(unittest.TestCase):
    """E1-01 and V1 through cad_agent.main with a scripted controller (no Ollama), rules.fn = 24."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.rules = test_rules(cls.root, fn=24)
        cls.runs = {rid: run_offline(rid, cls.root, cls.rules) for rid in ("E1-01", "V1")}

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
                self.assertEqual(rc, ca.EXIT_OK, failing)
                self.assertEqual(rec["outcome"], "verified")
                if Path(ca.OPENSCAD).exists():      # the delivered meshes are OpenSCAD's and agree with manifold3d
                    self.assertEqual(rec["assembly"]["stl_source"], {"base": "openscad", "lid": "openscad"})
                counts = {r["check_id"]: r["evidence"]["count"] for r in results if r["type"] == "aperture_count"}
                expected = {"E1-01": {"apertures_-X": 1, "apertures_+X": 2, "apertures_-Y": 0, "apertures_+Y": 0},
                            "V1": {"apertures_-X": 2, "apertures_+X": 0, "apertures_-Y": 0, "apertures_+Y": 0}}[rid]
                self.assertEqual(counts, expected)
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
        board = fg.solid(graph.nodes["board"], res) - ac.union([fg.solid(n, res) for n in graph if n.role == "seat"])
        ref = rubric_clear_of(both, board, rec["spec"]["board_clearance"])
        self.assertAlmostEqual(by_id["clear_board"]["evidence"]["gap"], ref, delta=0.02)
        self.assertEqual(compared, 3)

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
            self.assertEqual(rc, ca.EXIT_OK)


if __name__ == "__main__":
    unittest.main()
