"""Tests for parts.py: catalogue loading, the import validation gate, lookup and datum transforms.

No Ollama, no OpenSCAD. Request-sized parameters come from the request texts in
benchmarks/enclosure/*.json (fixtures), never from numbers typed into the agent.
"""

import copy
import json
import math
import re
import tempfile
import unittest
from pathlib import Path

import numpy as np

import parts as pt

REPO = Path(__file__).parent
PARTS = REPO / "benchmarks" / "enclosure" / "parts"


def request_text(rid: str) -> str:
    for src in ("enclosure.json", "variants.json"):
        for r in json.loads((REPO / "benchmarks" / "enclosure" / src).read_text())["requests"]:
            if r["id"] == rid:
                return r["request"]
    raise KeyError(rid)


def board_size(text: str):
    """'70 x 50 mm perfboard' -> (70.0, 50.0): the fixture parser for request-sized boards."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm", text)
    return float(m.group(1)), float(m.group(2))


def cylinder_size(text: str):
    d = re.search(r"(\d+(?:\.\d+)?)\s*mm diameter", text)
    h = re.search(r"(\d+(?:\.\d+)?)\s*mm tall", text)
    return float(d.group(1)), float(h.group(1))


def fixture_params(part_id: str):
    if part_id == "perfboard":
        w, d = board_size(request_text("E1-01"))
        return {"width": w, "depth": d}
    if part_id == "generic_cylinder":
        dia, h = cylinder_size(request_text("V3"))
        return {"diameter": dia, "height": h}
    return {}


class TestCatalogue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = pt.Catalog.load(PARTS)

    def test_every_part_loads_and_passes_the_gate(self):
        self.assertEqual(self.cat.errors, [])
        self.assertGreaterEqual(len(self.cat.parts), 11)
        self.assertEqual(self.cat.cross_references(), [])
        for pid in self.cat.ids():
            with self.subTest(part=pid):
                inst = self.cat.instantiate(pid, fixture_params(pid))
                self.assertEqual([str(f) for f in pt.validate(inst)], [])
                self.assertTrue(self.cat.get(pid).data.get("frame"), "every part states its frame")
                self.assertTrue(self.cat.get(pid).data.get("source"))

    def test_gate_params_also_pass(self):
        for pid in self.cat.ids():
            part = self.cat.get(pid)
            if part.request_params():
                self.assertEqual(pt.validate(pt.instantiate(part, part.gate_params())), [], pid)

    def test_request_sized_param_is_required(self):
        with self.assertRaises(pt.MissingParam) as cm:
            self.cat.instantiate("perfboard", {})
        self.assertEqual(cm.exception.part, "perfboard")
        with self.assertRaises(pt.PartError):
            self.cat.instantiate("perfboard", {"width": 1, "depth": 1, "colour": 3})

    def test_perfboard_holes_and_bbox_follow_the_request(self):
        part = self.cat.get("perfboard")
        defaults = {k: v["default"] for k, v in part.params.items() if v.get("default") is not None}
        for rid in ("E1-01", "V1"):
            w, d = board_size(request_text(rid))
            inst = self.cat.instantiate("perfboard", {"width": w, "depth": d})
            lo, hi = inst.bbox()
            np.testing.assert_allclose(hi - lo, [w, d, defaults["thickness"]])
            self.assertAlmostEqual(hi[2], 0.0)          # board frame: top surface at Z = 0
            holes = inst.datums["HOLE"]
            self.assertEqual(len(holes.at), 4)
            i = defaults["hole_inset"]
            expected = {(i, i), (w - i, i), (i, d - i), (w - i, d - i)}
            self.assertEqual({(round(p[0], 6), round(p[1], 6)) for p in holes.at},
                             {(round(x, 6), round(y, 6)) for x, y in expected})
            self.assertAlmostEqual(holes.diameter, defaults["hole_diameter"])

    def test_stack_option_sets_module_height(self):
        """The header's STACK_TOP plane is what raises a module (V3 uses the taller socket)."""
        pico = self.cat.get("rpi_pico2")
        heights = {}
        for hid in pico.data["mount"]["stack_options"]:
            heights[hid] = self.cat.instantiate(hid).datums["STACK_TOP"].at[2]
        self.assertGreater(heights["header_female_2p54"], heights["header_male_2p54"])


def mutated(part: pt.Part, fn) -> pt.Part:
    data = copy.deepcopy(part.data)
    fn(data)
    return pt.Part(part.id, data)


class TestGateRejectsBadData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = pt.Catalog.load(PARTS)
        cls.pico = cls.cat.get("rpi_pico2")

    def rules_failed(self, part):
        return {f.rule for f in pt.validate(pt.instantiate(part))}

    def test_inch_scaled_model_fails_r1(self):
        def scale(d):
            for g in d["geometry"]:
                g["size"] = [f"({s}) * 25.4" for s in g["size"]]
        self.assertIn("R1", self.rules_failed(mutated(self.pico, scale)))

    def test_axis_swapped_model_fails_r1(self):
        def swap(d):
            for g in d["geometry"]:
                g["size"] = [g["size"][1], g["size"][0], g["size"][2]]
        fails = pt.validate(pt.instantiate(mutated(self.pico, swap)))
        self.assertTrue(any(f.rule == "R1" and "swapped" in f.detail for f in fails), [str(f) for f in fails])

    def test_non_unit_datum_direction_fails(self):
        def bad(d):
            d["datums"]["USB_AXIS"]["dir"] = [2, 0, 0]
        self.assertIn("datum", self.rules_failed(mutated(self.pico, bad)))

    def test_mouth_off_the_receptacle_fails(self):
        def off(d):
            d["datums"]["USB_MOUTH"]["at"][0] = "-usb_overhang - 1"
        self.assertIn("connector", self.rules_failed(mutated(self.pico, off)))

    def test_self_check_failure_is_reported(self):
        def thick(d):
            d["params"]["pcb_thickness"]["default"] = 2.0
        self.assertIn("self_check", self.rules_failed(mutated(self.pico, thick)))

    def test_catalog_load_skips_and_reports_bad_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "good").mkdir()
            (root / "good" / "part.json").write_text((PARTS / "rpi_pico2" / "part.json").read_text())
            (root / "broken").mkdir()
            (root / "broken" / "part.json").write_text("{not json")
            (root / "old").mkdir()
            (root / "old" / "part.json").write_text(json.dumps({"id": "old", "schema": 0, "names": [], "kind": "x",
                                                                "source": "s", "geometry": []}))
            cat = pt.Catalog.load(root)
            self.assertEqual(cat.ids(), ["rpi_pico2"])
            self.assertEqual(len(cat.errors), 2)
            self.assertTrue(any("missing part" in p for p in cat.cross_references()))


class TestLookup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = pt.Catalog.load(PARTS)

    def first(self, text):
        return self.cat.lookup(text)[0][0]

    def test_lookup(self):
        self.assertEqual(self.first("Raspberry Pi Pico 2"), "rpi_pico2")
        self.assertEqual(self.first("3.5 mm aux jacks"), "jack_3p5_pj320a")
        self.assertEqual(self.first("70 x 50 mm perfboard"), "perfboard")
        self.assertEqual(self.first("female header sockets"), "header_female_2p54")
        self.assertIn("generic_cylinder", [p for p, _ in self.cat.lookup("a 10 mm diameter capacitor", k=3)])

    def test_token_normalisation(self):
        self.assertEqual(pt.tokens("pico2"), pt.tokens("pico 2"))
        self.assertEqual(pt.tokens("3.5mm"), pt.tokens("3.5 mm"))
        self.assertEqual(pt.tokens("Jacks!"), ["jack"])


class TestDatums(unittest.TestCase):
    def test_rotation_about_z_maps_x_to_y(self):
        ax = pt.Axis([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        moved = pt.transform(ax, pt.pose_matrix([10.0, 20.0, 3.0], rot_z_deg=90.0))
        np.testing.assert_allclose(moved.dir, [0, 1, 0], atol=1e-12)
        np.testing.assert_allclose(moved.at, [10.0, 21.0, 3.0], atol=1e-12)

    def test_point_offset_and_general_rotation(self):
        p = pt.Point([1.0, 2.0, 3.0])
        np.testing.assert_allclose(pt.transform(p, pt.pose_matrix([5, 0, -1])).at, [6, 2, 2])
        flip = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]
        np.testing.assert_allclose(pt.transform(p, pt.pose_matrix(rotation=flip)).at, [1, -2, -3])

    def test_datum_values(self):
        d = {"HOLE": pt.AxisList([[1, 2, 0], [3, 4, 0]], [0, 0, 1], 2.0), "AX": pt.Axis([0, 0, 5], [-1, 0, 0])}
        self.assertEqual(pt.datum_value(d, "HOLE[1].y"), 4.0)
        self.assertEqual(pt.datum_value(d, "HOLE.diameter"), 2.0)
        self.assertEqual(pt.datum_value(d, "HOLE.count"), 2.0)
        self.assertEqual(pt.datum_value(d, "AX.dx"), -1.0)
        with self.assertRaises(KeyError):
            pt.datum_value(d, "HOLE[5].x")


class TestRules(unittest.TestCase):
    def test_rules_load_with_sources(self):
        rules = pt.load_rules(REPO / "design_rules.json")
        self.assertIn("fn", rules.values)
        self.assertEqual(set(rules.values), set(rules.sources))
        self.assertTrue(all(rules.sources.values()))
        lo, hi = rules.values["sliding_fit_min"], rules.values["sliding_fit_max"]
        self.assertLess(lo, hi)

    def test_rule_without_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(json.dumps({"schema": 1, "rules": {"x": {"value": 1}}}))
            with self.assertRaises(pt.PartError):
                pt.load_rules(path)


if __name__ == "__main__":
    unittest.main()
