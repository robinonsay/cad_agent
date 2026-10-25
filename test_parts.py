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

    def test_jack_footprint_pins_from_the_drawing(self):
        # iteration 006 (C1, RC-602): the PJ-320A solder terminals are catalogue data (a PINS axis_list read off
        # the vendor drawing) with self_checks that recompute the drawing's spacings; the gate runs them
        pid = next(i for i in self.cat.ids() if self.cat.get(i).kind == "connector"
                   and "PINS" in self.cat.get(i).data.get("datums", {}))
        inst = self.cat.instantiate(pid)
        self.assertEqual([str(f) for f in pt.validate(inst)], [])
        pins = pt.lookup_datum(inst.datums, "PINS")
        self.assertEqual(len(pins.at), 4)
        np.testing.assert_allclose(pins.dir, [0, 0, -1], atol=1e-12)
        lo, hi = inst.bbox(inst.part.data.get("size_of"))
        names = [c["name"] for c in inst.part.data["self_checks"]]
        self.assertTrue(any("spacing" in n for n in names), names)
        for q in pins.at:                      # under the body in plan, on its underside (legs go down)
            self.assertTrue(lo[0] - 1e-9 <= q[0] <= hi[0] + 1e-9 and lo[1] - 1e-9 <= q[1] <= hi[1] + 1e-9, q)
            self.assertAlmostEqual(q[2], lo[2], places=9)
        self.assertIn("drawing", inst.part.data["datums"]["PINS"]["source"])
        self.assertIn("http", inst.part.data["source"])
        # a wrong spacing in the data fails the self_check (non-vacuous)
        bad = copy.deepcopy(inst.part.data)
        bad["datums"]["PINS"]["at"][1][0] = "body_length - 6.5"
        fails = pt.validate(pt.instantiate(pt.Part(pid, bad)))
        self.assertTrue(any(f.rule == "self_check" and "spacing" in f.detail for f in fails), fails)
        # the pins hang off the mouth face and the centreline, so they follow the body params
        self.assertIn("body_length", json.dumps(inst.part.data["datums"]["PINS"]["at"]))
        self.assertIn("body_width", json.dumps(inst.part.data["datums"]["PINS"]["at"]))

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
            # iteration 011 (C1, RC-1101): the resolved value is the specimen's when one matches, else the family default
            src = dict(defaults, **((inst.specimen or {}).get("params") or {}))
            i = src["hole_inset"]
            self.assertEqual(inst.params["hole_inset"], i)
            expected = {(i, i), (w - i, i), (i, d - i), (w - i, d - i)}
            self.assertEqual({(round(p[0], 6), round(p[1], 6)) for p in holes.at},
                             {(round(x, 6), round(y, 6)) for x, y in expected})
            self.assertAlmostEqual(holes.diameter, src["hole_diameter"])
            self.assertEqual(inst.specimen is None, rid != "E1-01")

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


class TestPerfboard(unittest.TestCase):
    """iteration 010 (C1, RC-1001): the perfboard is the measured board (requirements.md A7, OWNER_DECISIONS 1) and stays
    parametric: a finite hole array centred on every board size. The A7 numbers live in this test only."""

    @classmethod
    def setUpClass(cls):
        cls.cat = pt.Catalog.load(PARTS)

    def board(self, w, d):
        return self.cat.instantiate("perfboard", {"width": w, "depth": d})

    def test_measured_board_70x50(self):
        w, d = board_size(request_text("E1-01"))
        self.assertEqual((w, d), (70.0, 50.0))
        inst = self.board(w, d)
        holes = inst.datums["HOLE"]
        self.assertEqual({(round(p[0], 9), round(p[1], 9)) for p in holes.at}, {(2, 2), (68, 2), (2, 48), (68, 48)})
        self.assertAlmostEqual(holes.diameter, 2.0, places=9)
        self.assertAlmostEqual(holes.keepout_diameter, 7.0, places=9)
        self.assertAlmostEqual(pt.datum_value(inst.datums, "HOLE.keepout_diameter"), 7.0, places=9)
        self.assertAlmostEqual(pt.transform(holes, pt.pose_matrix((1, 2, 3), 90)).keepout_diameter, 7.0)
        self.assertAlmostEqual(holes.item(3).keepout_diameter, 7.0)
        grid = inst.grid()
        self.assertEqual([round(c, 9) for c in grid["count"]], [24, 18])
        np.testing.assert_allclose(grid["origin"][:2], [5.79, 3.41], atol=1e-9)
        self.assertAlmostEqual(grid["pitch"], 2.54)
        self.assertNotIn("soft", inst.part.data["grid"])
        self.assertEqual(pt.validate(inst), [])
        names = {c["name"] for c in inst.part.data["self_checks"]}
        self.assertTrue(any("centred" in n for n in names) and any("grid_margin_x" in n for n in names))
        self.assertAlmostEqual(inst.env("grid.count_x"), 24.0)
        self.assertAlmostEqual(inst.env("grid.origin_y"), 3.41)
        self.assertEqual(inst.specimen["id"], "photo_70x50")       # iteration 011 (C1): the A7 values are a specimen

    def test_specimen_selected_by_size(self):
        # iteration 011 (C1, RC-1101): the photographed board is a specimen selected by size; every other size gets
        # the family holes (catalogue note in variants.json). The target numbers live in this test only.
        part = self.cat.get("perfboard")
        tol = part.data["size_tolerance"]
        for w, d in ((70.0, 50.0), (70.0 + tol / 2, 50.0 - tol / 2)):
            with self.subTest(size=(w, d)):
                inst = self.board(w, d)
                self.assertEqual(inst.specimen["id"], "photo_70x50")
                self.assertEqual(part.specimen_for({"width": w, "depth": d})["id"], "photo_70x50")
                holes = inst.datums["HOLE"]
                self.assertAlmostEqual(holes.at[0][0], 2.0, places=9)
                self.assertAlmostEqual(holes.at[0][1], 2.0, places=9)
                self.assertAlmostEqual(holes.at[3][0], w - 2.0, places=9)
                self.assertAlmostEqual(holes.diameter, 2.0, places=9)
                self.assertAlmostEqual(holes.keepout_diameter, 7.0, places=9)
                self.assertEqual(pt.validate(inst), [])
        g = self.board(70.0, 50.0).grid()
        self.assertEqual([round(c) for c in g["count"]], [24, 18])
        np.testing.assert_allclose(g["origin"][:2], [5.79, 3.41], atol=1e-9)
        sizes = [(80, 60), (90, 45), (80, 40), tuple(part.gate_params()[k] for k in ("width", "depth"))]
        self.assertIn((100.0, 75.0), sizes)
        for w, d in sizes:
            with self.subTest(size=(w, d)):
                inst = self.board(w, d)
                self.assertIsNone(inst.specimen)
                holes = inst.datums["HOLE"]
                self.assertEqual({(round(p[0], 9), round(p[1], 9)) for p in holes.at},
                                 {(2.5, 2.5), (w - 2.5, 2.5), (2.5, d - 2.5), (w - 2.5, d - 2.5)})
                self.assertAlmostEqual(holes.diameter, 3.0, places=9)
                self.assertAlmostEqual(holes.keepout_diameter, 7.0, places=9)
                # the grid is family data: the same with or without a specimen
                fam = pt.instantiate(pt.Part("perfboard", {k: v for k, v in part.data.items() if k != "specimens"}),
                                     {"width": w, "depth": d})
                np.testing.assert_allclose(inst.grid()["origin"], fam.grid()["origin"], atol=1e-12)
                self.assertEqual(inst.grid()["count"], fam.grid()["count"])
        explicit = self.cat.instantiate("perfboard", {"width": 70.0, "depth": 50.0, "hole_inset": 2.2})
        self.assertAlmostEqual(explicit.datums["HOLE"].at[0][0], 2.2, places=9)
        self.assertAlmostEqual(explicit.datums["HOLE"].diameter, 2.0, places=9)   # the rest still from the specimen
        self.assertEqual(explicit.specimen["params"], {"hole_diameter": 2.0})
        self.assertEqual(pt.gate(part), [])

    def test_specimen_gate(self):
        # iteration 011 (C1): a malformed specimen drops the part with a typed reason (rule "specimen" or the
        # specimen-match instance's own gate rule)
        base = self.cat.get("perfboard").data
        sp0 = base["specimens"][0]

        def variant(edit):
            data = copy.deepcopy(base)
            edit(data)
            return pt.Part("perfboard", data)

        def overlap(d):
            d["specimens"].append(dict(copy.deepcopy(sp0), id="other",
                                       match={k: v + d["size_tolerance"] / 2 for k, v in sp0["match"].items()}))

        cases = {
            "overlapping matches": (overlap, "specimen", "overlapping"),
            "match on a non-request param": (lambda d: d["specimens"][0]["match"].update(thickness=1.6),
                                             "specimen", "not a from_request"),
            "undeclared params key": (lambda d: d["specimens"][0]["params"].update(colour=1.0), "specimen",
                                      "not a declared"),
            "request param in params": (lambda d: d["specimens"][0]["params"].update(width=70.0), "specimen",
                                        "is a from_request"),
            "missing source": (lambda d: d["specimens"][0].pop("source"), "specimen", "no source"),
            "missing id": (lambda d: d["specimens"][0].pop("id"), "specimen", "no id"),
            "duplicate id": (lambda d: d["specimens"].append(dict(copy.deepcopy(sp0), match={"width": 1.0e3})),
                             "specimen", "duplicate"),
            "self-check fails at the match": (lambda d: d["specimens"][0]["params"].update(hole_inset=0.5),
                                              "self_check", "holes inside the board outline"),
        }
        for name, (edit, rule, words) in cases.items():
            with self.subTest(case=name):
                fails = pt.gate(variant(edit))
                self.assertTrue(any(f.rule == rule and words in f.detail for f in fails), [str(f) for f in fails])
        # LoadCatalog drops such a part and reports it
        import assembly as A
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            for pid in self.cat.ids():
                (Path(tmp) / pid).mkdir()
                data = copy.deepcopy(self.cat.get(pid).data)
                if pid == "perfboard":
                    overlap(data)
                (Path(tmp) / pid / "part.json").write_text(json.dumps(data))
            st = A.AssemblyState(parts_dir=tmp)
            step = A.LoadCatalog(SimpleNamespace(assy=st))
            step.update()
            self.assertNotIn("perfboard", st.catalog.parts)
            self.assertTrue(any("perfboard" in n and "overlapping" in n for n in st.notes), st.notes)

    def test_grid_centred_on_every_size(self):
        import layout as lay
        tol = pt.load_rules(REPO / "design_rules.json").values["measure_tol"]
        margin_x = self.cat.get("perfboard").params["grid_margin_x"]["default"]
        margin_y = self.cat.get("perfboard").params["grid_margin_y"]["default"]
        for w, d in ((80, 60), (90, 45), (80, 40), (100, 75)):
            with self.subTest(size=(w, d)):
                inst = self.board(w, d)
                g = inst.grid()
                nx, ny = g["count"]
                self.assertEqual((nx, ny), (round(nx), round(ny)))
                self.assertGreaterEqual(min(nx, ny), 1)
                self.assertAlmostEqual(g["origin"][0] + (nx - 1) * g["pitch"] / 2, w / 2, places=9)
                self.assertAlmostEqual(g["origin"][1] + (ny - 1) * g["pitch"] / 2, d / 2, places=9)
                self.assertGreaterEqual(g["origin"][0], margin_x - 1e-9)
                self.assertGreaterEqual(g["origin"][1], margin_y - 1e-9)
                self.assertLess(g["origin"][0], margin_x + g["pitch"])        # the largest whole number of pitches
                self.assertEqual(pt.validate(inst), [])
                notes = []
                syms = lay.board_symmetries(inst, tol, notes)
                self.assertEqual(len(syms), 2)
                self.assertEqual(notes, [])

    def test_bad_grid_count_fails_the_gate(self):
        data = copy.deepcopy(self.cat.get("perfboard").data)
        data["grid"]["count"] = ["(width - 2*grid_margin_x) / grid_pitch", 1]       # not a whole number
        inst = pt.instantiate(pt.Part("perfboard", data), {"width": 70.0, "depth": 50.0})
        self.assertIn("grid", [f.rule for f in pt.validate(inst)])
        data["grid"]["count"] = [0, 1]
        inst = pt.instantiate(pt.Part("perfboard", data), {"width": 70.0, "depth": 50.0})
        self.assertIn("grid", [f.rule for f in pt.validate(inst)])


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

    def test_spec_slots_load_and_unknown_defaults_are_rejected(self):
        rules = pt.load_rules(REPO / "design_rules.json")
        names = [s["name"] for s in rules.spec_slots]
        self.assertIn("board_width", names)
        self.assertIsNone(rules.slot("board_width")["default_rule"])
        for s in rules.spec_slots:
            self.assertTrue(s["default_rule"] is None or s["default_rule"] in rules.values, s)
        data = json.loads((REPO / "design_rules.json").read_text())
        data["spec_slots"]["slots"][0]["default_rule"] = "no_such_rule"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(json.dumps(data))
            with self.assertRaises(pt.PartError):
                pt.load_rules(path)

    def test_rule_without_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(json.dumps({"schema": 1, "rules": {"x": {"value": 1}}}))
            with self.assertRaises(pt.PartError):
                pt.load_rules(path)


def column_d(cat, board, rules) -> float:
    """The hole-column diameter as assembly.hole_column_d computes it (changed in iteration 010: the chosen board
    screw, and the board's own mounting-hole keep-out, not a hard-wired M2.5 screw)."""
    import assembly as A
    screw = pt.instantiate(A.board_screw(cat, board, rules))
    return max(pt.lookup_datum(board.datums, "HOLE").keepout_diameter or 0.0,
               screw.params["head_diameter"] + 2 * rules["driver_clearance"])


def placed_fixture(rid: str, edges: dict, stack: str = "header_male_2p54"):
    """The board of request `rid` (size parsed from its text) with a Pico 2 and the request's jacks placed by
    layout.Placer from scripted edges. Returns (catalog, rules, layout, placer)."""
    import layout as lay
    cat = pt.Catalog.load(PARTS)
    rules = pt.load_rules(REPO / "design_rules.json").values
    w, d = board_size(request_text(rid))
    board = cat.instantiate("perfboard", {"width": w, "depth": d})
    placed = lay.Placed("board", "perfboard", {"width": w, "depth": d}, 0, 0, 0, 0, "", role="board", inst=board)
    seat_d = column_d(cat, board, rules)
    placer = lay.Placer(cat, placed, rules, seat_d, rules["component_height_default"])
    jacks = {"E1-01": 2, "V1": 1, "V2": 3, "V3": 1}[rid]
    items = [lay.Item("pico", "rpi_pico2", {}, 1, True, stack, "pico 2"),
             lay.Item("jack", "jack_3p5_pj320a", {}, jacks, True, None, "jack")]
    return cat, rules, placer.place(items, edges), placer


def envelope_bbox(nodes, rules):
    import feature_graph as fg
    g = fg.FeatureGraph(nodes)
    res = g.resolve(rules=rules)
    out = {}
    for n in nodes:
        b = fg.solid(n, res).bounding_box()
        out[n.id] = (np.array(b[:3]), np.array(b[3:]))
    return out


class TestEnvelopes(unittest.TestCase):
    """M4 subset: every envelope equals the hand formula from part data (R8: datums within 0.01)."""

    @classmethod
    def setUpClass(cls):
        import layout as lay
        cls.lay = lay
        cls.cat, cls.rules, cls.layout, cls.placer = placed_fixture("E1-01", {"pico": "-X", "jack": "+X"})

    def sweep(self, node_id):
        p = self.layout.get(node_id)
        c = p.inst.connectors[0]
        world = {"mouth": self.lay.world_datum(p, c["mouth"]), "axis": self.lay.world_datum(p, c["axis"])}
        plug = self.cat.instantiate(c["mates"])
        return world, plug, pt.plug_sweep(world, plug, 0.0, self.rules["plug_travel"], prefix=f"{node_id}_plug")

    def test_usb_plug_sweep_matches_the_hand_formula(self):
        world, plug, nodes = self.sweep("pico_1")
        m = np.asarray(world["mouth"].at)
        u = np.asarray(world["axis"].dir)
        np.testing.assert_allclose(u, [-1, 0, 0], atol=1e-9)
        q = plug.params
        boxes = envelope_bbox(nodes, self.rules)
        shell = boxes["pico_1_plug_shell"]
        # shell: from insert_depth inside the mouth to exposed_shell outside it, along USB_AXIS (-X here)
        np.testing.assert_allclose(shell[0], [m[0] - q["exposed_shell"], m[1] - q["shell_width"] / 2,
                                              m[2] - q["shell_height"] / 2], atol=1e-6)
        np.testing.assert_allclose(shell[1], [m[0] + q["insert_depth"], m[1] + q["shell_width"] / 2,
                                              m[2] + q["shell_height"] / 2], atol=1e-6)
        om = boxes["pico_1_plug_overmold"]
        start = m[0] - q["exposed_shell"]
        np.testing.assert_allclose(om[0], [start - q["overmold_length"] - self.rules["plug_travel"],
                                           m[1] - q["overmold_width"] / 2, m[2] - q["overmold_height"] / 2], atol=1e-6)
        np.testing.assert_allclose(om[1], [start, m[1] + q["overmold_width"] / 2, m[2] + q["overmold_height"] / 2],
                                   atol=1e-6)
        roles = {n.id: n.role for n in nodes}
        self.assertEqual(roles["pico_1_plug_overmold"], "plug_overmold")
        self.assertTrue(all(n.kind == "envelope" for n in nodes))

    def test_jack_plug_sweep_is_on_the_jack_axis(self):
        for k in (1, 2):
            world, plug, nodes = self.sweep(f"jack_{k}")
            by = {n.id.rsplit("_", 1)[-1]: n for n in nodes}
            self.assertAlmostEqual(by["shaft"].params["d"], plug.params["shaft_diameter"])
            self.assertAlmostEqual(by["overmold"].params["d"], plug.params["overmold_diameter"])
            u = np.asarray(world["axis"].dir)
            np.testing.assert_allclose(u, [1, 0, 0], atol=1e-9)
            for n in nodes:
                np.testing.assert_allclose(n.pose.axis_dir, u, atol=1e-9)
                p = np.asarray(n.pose.offset) - np.asarray(world["axis"].at)
                off_axis = np.linalg.norm(p - np.dot(p, u) * u)
                self.assertLessEqual(off_axis, 0.01)          # R8
            # full mate: the plug's SEAT is on the mouth, so the overmold starts stop_gap outside it
            gap = plug.params["shaft_length"] - pt.lookup_datum(plug.datums, "SEAT").at[0]
            self.assertAlmostEqual(by["overmold"].params["s0"], gap, places=9)
            self.assertAlmostEqual(by["overmold"].params["h"],
                                   plug.params["overmold_length"] + self.rules["plug_travel"], places=9)

    def test_keepouts_span_the_board_footprint(self):
        board = self.layout.get("board")
        w, d, t = board.params["width"], board.params["depth"], board.inst.params["thickness"]
        above, below = 7.5, 2.5      # arbitrary heights: the generator must use what it is given
        nodes = pt.board_keepout(board.inst, board.pose, above, below)
        boxes = envelope_bbox(nodes, self.rules)
        np.testing.assert_allclose(boxes["board_ko_top"][0], [0, 0, 0], atol=1e-9)
        np.testing.assert_allclose(boxes["board_ko_top"][1], [w, d, above], atol=1e-9)
        np.testing.assert_allclose(boxes["board_ko_bot"][0], [0, 0, -t - below], atol=1e-9)
        np.testing.assert_allclose(boxes["board_ko_bot"][1], [w, d, -t], atol=1e-9)

    def test_columns_and_content_envelope(self):
        board = self.layout.get("board")
        holes = self.lay.world_datum(board, "HOLE")
        col = pt.column(holes, 2, 7.0, -3.0, 4.0, "seat")
        box = envelope_bbox([col], self.rules)[col.id]
        np.testing.assert_allclose((box[0] + box[1])[:2] / 2, holes.at[2][:2], atol=1e-9)
        self.assertAlmostEqual(box[1][2] - box[0][2], 7.0)
        pico = self.layout.get("pico_1")
        stacks = [p for p in self.layout.placed if p.of == "pico_1"]
        env = pt.content_envelope([(pico.inst, pico.pose)] + [(s.inst, s.pose) for s in stacks], "pico_env")
        # changed in iteration 005 (content_envelope returns one node per primitive): the same assertions on the
        # union's bbox
        boxes = envelope_bbox(env, self.rules)
        lo = np.min([b[0] for b in boxes.values()], axis=0)
        mouth = self.lay.world_datum(pico, "USB_MOUTH").at
        self.assertAlmostEqual(lo[0], mouth[0], places=6)      # the receptacle overhang is inside V-PICO
        self.assertAlmostEqual(lo[2], 0.0, places=6)           # headers stand on the board top

    def test_content_envelope_is_the_union_of_primitives(self):
        # iteration 005 (RC-502): V-PICO is the union of the module's and its stacks' catalogue primitives, not
        # their AABB; the AABB corner beside the receptacle is outside every node
        import feature_graph as fg
        pico = self.layout.get("pico_1")
        stacks = [p for p in self.layout.placed if p.of == "pico_1"]
        self.assertTrue(stacks)
        members = [(pico.inst, pico.pose)] + [(s.inst, s.pose) for s in stacks]
        nodes = pt.content_envelope(members, "pico_env", role="module_envelope")
        self.assertEqual(len(nodes), sum(len(inst.geometry) for inst, _ in members))
        self.assertTrue(all(n.group == "pico_env" and n.role == "module_envelope" and n.kind == "envelope"
                            for n in nodes))
        seg = int(self.rules["fn"])
        res = fg.FeatureGraph(nodes).resolve(rules=self.rules)
        env = fg.m3d.Manifold.batch_boolean([fg.solid(n, res) for n in nodes], fg.m3d.OpType.Add)
        ref = fg.m3d.Manifold.batch_boolean([fg.part_solid(inst, seg).transform(fg._m3(pose)) for inst, pose in members],
                                            fg.m3d.OpType.Add)
        self.assertAlmostEqual(env.volume(), ref.volume(), delta=1e-3)
        self.assertAlmostEqual((env ^ ref).volume(), ref.volume(), delta=1e-3)
        pose = np.asarray(pico.pose, dtype=float)
        pcb_lo, pcb_hi = pico.inst.bbox("pcb")
        corners = np.array([[pcb_hi[i] if c >> i & 1 else pcb_lo[i] for i in range(3)] for c in range(8)])
        pcb_min_y = float((corners @ pose[:3, :3].T + pose[:3, 3])[:, 1].min())
        mouth = self.lay.world_datum(pico, "USB_MOUTH").at
        top = self.lay.world_datum(pico, "PCB_TOP").at[2]
        point = np.array([mouth[0] + 0.1, pcb_min_y + 0.1, top + 0.1])
        aabb = fg.instance_world_bbox(pico.inst, pico.pose)
        self.assertTrue(np.all(point > aabb[0]) and np.all(point < aabb[1]))      # inside the old AABB proxy
        probe = fg.m3d.Manifold.cube([0.01] * 3).translate((point - 0.005).tolist())
        self.assertEqual((env ^ probe).volume(), 0.0)

    def test_anchored_column_follows_the_board(self):
        # iteration 004 (RC-401): a column anchored on board.HOLE[i] re-resolves when the board's params change;
        # an unanchored one keeps its frozen floats (the old behaviour, pinned)
        import feature_graph as fg
        board = self.layout.get("board")
        holes = self.lay.world_datum(board, "HOLE")
        w, d = board.params["width"], board.params["depth"]
        g = fg.FeatureGraph([fg.Node("board", "reference", "part", {"width": w, "depth": d}, part="perfboard"),
                             pt.column(holes, 1, 7.0, -3.0, 4.0, "seat", prefix="anch", anchor="board.HOLE[1]"),
                             pt.column(holes, 1, 7.0, -3.0, 4.0, "seat", prefix="frozen")])
        res = g.resolve(rules=self.rules, catalog=self.cat)
        for nid in ("anch_1", "frozen_1"):
            np.testing.assert_allclose(res.poses[nid][:3, 3], [holes.at[1][0], holes.at[1][1], -3.0], atol=1e-9)
        g.nodes["board"].params["width"] = w + 5
        res2 = g.resolve(rules=self.rules, catalog=self.cat)
        moved = pt.lookup_datum(res2.datums, "board.HOLE[1]").at
        np.testing.assert_allclose(res2.poses["anch_1"][:3, 3], [moved[0], moved[1], -3.0], atol=1e-9)
        # iteration 011 (C1): 75 x 50 leaves the 70 x 50 specimen, so the hole inset is the family default there;
        # the anchored column follows the board's HOLE datum either way
        grown = self.cat.instantiate("perfboard", {"width": w + 5, "depth": d})
        shift = grown.datums["HOLE"].at[1][0] - board.inst.datums["HOLE"].at[1][0]
        self.assertGreater(shift, 0)
        self.assertAlmostEqual(moved[0] - holes.at[1][0], shift, places=9)
        np.testing.assert_allclose(res2.poses["frozen_1"][:3, 3], res.poses["frozen_1"][:3, 3], atol=1e-12)
        self.assertAlmostEqual(res2.params["anch_1"]["h"], 7.0, places=9)
        # a derived top (V-DRIVER reaches an expression)
        col = pt.column(holes, 0, 6.0, 0.0, "spec.top + 1", "driver", prefix="drv", anchor="board.HOLE[0]")
        g.add(col)
        self.assertAlmostEqual(g.resolve({"top": 9.0}, self.rules, catalog=self.cat).params["drv_0"]["h"], 10.0)

    def test_part_with_pins_datum_is_snapped_along_its_edge(self):
        # iteration 004 (C4): a connector that declares a PINS datum is snapped tangentially like a module
        import layout as lay
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for src in PARTS.iterdir():
                if (src / "part.json").is_file():
                    (root / src.name).mkdir()
                    (root / src.name / "part.json").write_text((src / "part.json").read_text())
            data = json.loads((PARTS / "jack_3p5_pj320a" / "part.json").read_text())
            # fixture pins (a test-only part, not catalogue data): two pins under the body, one grid pitch apart
            data["datums"]["PINS"] = {"kind": "axis_list", "dir": [0, 0, -1],
                                      "at": [["body_length / 3", "body_width / 3", 0],
                                             ["body_length / 3", "body_width / 3 + 2.54", 0]]}
            (root / "jack_3p5_pj320a" / "part.json").write_text(json.dumps(data))
            cat = pt.Catalog.load(root)
            self.assertEqual(cat.errors, [])
            w, d = board_size(request_text("E1-01"))
            board = cat.instantiate("perfboard", {"width": w, "depth": d})
            placed = lay.Placed("board", "perfboard", {"width": w, "depth": d}, 0, 0, 0, 0, "", role="board", inst=board)
            placer = lay.Placer(cat, placed, self.rules, column_d(cat, board, self.rules),
                                self.rules["component_height_default"])
            out = placer.place([lay.Item("pico", "rpi_pico2", {}, 1, True, "header_male_2p54", "pico 2"),
                                lay.Item("jack", "jack_3p5_pj320a", {}, 2, True, None, "jack")],
                               {"pico": "-X", "jack": "+X"})
            origin, pitch = placer.grid
            report = placer.grid_report(out.placed)
            for k in (1, 2):
                p = out.get(f"jack_{k}")
                for q in lay.world_datum(p, "PINS").at:
                    r = (q[1] - origin[1] + pitch / 2) % pitch - pitch / 2        # along the +X edge: Y
                    self.assertLessEqual(abs(r), 1e-6)
                self.assertLessEqual(report["parts"][p.node_id]["tangential"], 1e-6)
            self.assertEqual(report["no_pin_data"], [])

    def test_rotated_connector_sweeps_along_its_axis(self):
        _, _, layout, _ = placed_fixture("V2", {"pico": "-X", "jack": "+Y"})
        p = layout.get("jack_1")
        c = p.inst.connectors[0]
        world = {"mouth": self.lay.world_datum(p, c["mouth"]), "axis": self.lay.world_datum(p, c["axis"])}
        np.testing.assert_allclose(world["axis"].dir, [0, 1, 0], atol=1e-9)
        plug = self.cat.instantiate(c["mates"])
        nodes = pt.plug_sweep(world, plug, 0.0, self.rules["plug_travel"], prefix="j")
        lo, hi = envelope_bbox(nodes, self.rules)["j_overmold"]
        size = hi - lo
        self.assertAlmostEqual(size[1], plug.params["overmold_length"] + self.rules["plug_travel"], places=6)
        # changed in iteration 004: envelope cylinders are circumscribed $fn-gons (vertex radius (d/2)/cos(pi/fn))
        self.assertAlmostEqual(size[0], plug.params["overmold_diameter"] / math.cos(math.pi / self.rules["fn"]), places=6)
        self.assertGreater(lo[1], world["mouth"].at[1])          # it runs outward along +Y

    def test_vertical_connector_is_a_typed_error(self):
        plug = self.cat.instantiate("plug_trs_3p5")
        with self.assertRaises(pt.PartError):
            pt.plug_sweep({"mouth": pt.Point([0, 0, 0]), "axis": pt.Axis([0, 0, 0], [0, 0, 1])}, plug, 0.0, 1.0)


GEN_PARTS = REPO / "benchmarks" / "generalize" / "parts"
BOTH = [GEN_PARTS, PARTS]


class TestInterfaces(unittest.TestCase):
    """Generalize delta 001 D1 / R9: the mount_holes interface and its gate."""

    @classmethod
    def setUpClass(cls):
        cls.cat = pt.Catalog.load(BOTH)

    def test_mount_holes_gate(self):
        # T4: an interface naming a missing datum, a non-plane seat, a tilted seat or an unknown kind fails R9
        base = self.cat.get("perfboard")
        holes, seat, top = pt.mount_names(base)

        def with_iface(**edit):
            def fn(data):
                data["interfaces"] = [dict(data["interfaces"][0], **edit)]
            return mutated(base, fn)

        tilted = next(n for n, d in base.data["datums"].items() if d["kind"] == "plane" and d["normal"][2] == 0)
        bad = {"missing": with_iface(holes="NO_SUCH_DATUM"), "not_a_plane": with_iface(seat=holes),
               "tilted": with_iface(top=tilted), "unknown_kind": with_iface(kind="no_such_kind")}
        for name, part in bad.items():
            with self.subTest(name=name):
                fails = pt.gate(part)
                self.assertTrue(any(f.rule == "R9" for f in fails), [str(f) for f in fails])
        good = pt.gate(base)
        self.assertEqual(good, [])
        for pid in self.cat.ids():           # every catalogue part (both catalogues) still passes the whole gate
            with self.subTest(pid=pid):
                self.assertEqual([str(f) for f in pt.gate(self.cat.get(pid))], [])
        self.assertEqual(self.cat.errors, [])
        offered = [pid for pid in self.cat.ids() if pt.mount_interface(self.cat.get(pid)) is not None]
        self.assertGreaterEqual(len(offered), 8, offered)

    def test_perfboard_planes_equal_top_bottom(self):
        # T5 (regression invariance): the interface's seat and top planes are the board's old BOTTOM / TOP planes at the
        # gate sample, every specimen and every regression request size, so every derived height is unchanged
        part = self.cat.get("perfboard")
        holes, seat, top = pt.mount_names(part)
        samples = [part.gate_params()] + [dict(sp["match"]) for sp in part.specimens]
        samples += [dict(zip(("width", "depth"), board_size(request_text(rid)))) for rid in ("E1-01", "V1", "V2", "V3")]
        for given in samples:
            inst = pt.instantiate(part, given)
            self.assertEqual(inst.datums[seat].at[2], inst.datums["BOTTOM"].at[2], given)
            self.assertEqual(inst.datums[top].at[2], inst.datums["TOP"].at[2], given)
            self.assertEqual(inst.datums[holes].at, inst.datums["HOLE"].at, given)
        self.assertTrue(pt.is_carrier(part))
        self.assertFalse(pt.is_carrier(self.cat.get("rpi_pico2")))

    def test_thread_field(self):
        # generalize delta 002 T8 (C1, D2): R9 accepts an optional positive number `thread` on an interface and rejects
        # 0, a negative number, a string and a boolean; interface_thread reads it back (None when absent)
        base = self.cat.get("perfboard")
        self.assertNotIn("thread", pt.mount_interface(base))
        self.assertIsNone(pt.interface_thread(base))

        def with_thread(v):
            def fn(data):
                data["interfaces"] = [dict(data["interfaces"][0], thread=v)]
            return mutated(base, fn)

        good = with_thread(2.5)
        self.assertEqual(pt.gate(good), [])
        self.assertEqual(pt.interface_thread(good), 2.5)
        for bad in (0, -2.5, "M3", True):
            with self.subTest(thread=bad):
                fails = pt.gate(with_thread(bad))
                self.assertTrue(any(f.rule == "R9" and "thread" in f.detail for f in fails), [str(f) for f in fails])
        # the catalogue data: the boards whose datasheets give a screw carry it; the family perfboard does not
        given = {pid: pt.interface_thread(self.cat.get(pid)) for pid in self.cat.ids()
                 if pt.interface_thread(self.cat.get(pid)) is not None}
        self.assertGreaterEqual(len(given), 3, given)
        for pid, thread in given.items():
            holes = pt.instantiate(self.cat.get(pid)).datums[pt.mount_names(self.cat.get(pid))[0]]
            self.assertLessEqual(thread, holes.diameter, pid)          # the datasheet screw passes its own holes

    def test_zone_kind(self):
        # generalize delta 003 T14 (D1): the zone interface gate: a good zone loads; a missing datum, a size that does not
        # resolve > 0, a tilted long axis or empty names are R9 failures; a zone name that is an archetype evidence word is
        # rejected by zone_reserved_failures; the Uno's mcu zone resolves to the ATmega328P DIP-28 footprint 35.6 x 7.6
        uno = self.cat.get("arduino_uno_r3")
        self.assertEqual(pt.gate(uno), [])
        zone = next(z for z in pt.zones(uno) if z["id"] == "mcu")
        geo = pt.zone_geometry(pt.instantiate(uno), zone)
        self.assertEqual((round(geo["long"], 9), round(geo["short"], 9)), (35.6, 7.6))
        self.assertEqual(geo["long_axis"], [1.0, 0.0, 0.0])
        self.assertEqual(geo["centre"], list(pt.instantiate(uno).datums[zone["at"]].at))
        self.assertIsNotNone(pt.mount_interface(uno))            # the zone does not displace the mount interface

        def with_zone(**edit):
            def fn(data):
                k = next(i for i, z in enumerate(data["interfaces"]) if z.get("kind") == pt.ZONE)
                data["interfaces"][k] = dict(data["interfaces"][k], **edit)
            return mutated(uno, fn)

        bad = {"missing_datum": with_zone(at="NO_SUCH_DATUM"), "not_a_point": with_zone(at="USB_AXIS"),
               "empty_names": with_zone(names=[]), "no_names": with_zone(names=None),
               "zero_size": with_zone(size=["mcu_length", "0"]), "bad_size": with_zone(size=["no_such_param", "1"]),
               "tilted_axis": with_zone(long_axis=[0, 0, 1])}
        for name, part in bad.items():
            with self.subTest(name=name):
                fails = pt.gate(part)
                self.assertTrue(any(f.rule == "R9" for f in fails), [str(f) for f in fails])
        rules = pt.load_rules(REPO / "design_rules.json")
        reserved = [w for a in rules.archetypes.values() for w in a.get("evidence", [])]
        self.assertEqual(pt.zone_reserved_failures(uno, reserved), [])
        clash = with_zone(names=["mcu", reserved[0]])
        self.assertTrue(pt.zone_reserved_failures(clash, reserved))


class TestCardAccess(unittest.TestCase):
    """Generalize delta 002 T12 (D1, RC-D): microSD card access is a connector with a mating card part."""

    @classmethod
    def setUpClass(cls):
        cls.cat = pt.Catalog.load(BOTH)
        cls.rules = pt.load_rules(REPO / "design_rules.json").values

    def card_id(self):
        # the plug a module's microSD-slot connector takes: found from the catalogue data, never typed
        mods = [self.cat.get(pid) for pid in self.cat.ids() if self.cat.get(pid).kind == "module"]
        pairs = [(m, c) for m in mods for c in m.data.get("connectors", []) if c.get("mouth") and c["mates"] in self.cat
                 and "SD" in c["mouth"]]
        self.assertTrue(pairs)
        return pairs[0]

    def test_card_part_and_connector(self):
        module, conn = self.card_id()
        card = self.cat.get(conn["mates"])
        self.assertEqual(card.kind, "plug")
        self.assertEqual([str(f) for f in pt.gate(card)], [])
        self.assertEqual([str(f) for f in pt.gate(module)], [])
        # the card's names say "card", never "slot": a text that names the slot as unused must not hit it
        self.assertTrue(all("card" in pt.tokens(n) for n in card.names), card.names)
        self.assertFalse(any("slot" in pt.tokens(n) for n in card.names), card.names)
        # the sweep section at the mouth is the access zone the card data declares (width x height), centred where the
        # card data says (its zone_offset above the card axis)
        inst = pt.instantiate(module)
        world = {"mouth": inst.datums[conn["mouth"]], "axis": inst.datums[conn["axis"]]}
        nodes = pt.plug_sweep(world, self.cat.instantiate(card.id), 0.0, self.rules["plug_travel"], prefix="sd_plug")
        far = next(n for n in nodes if n.role == "plug_overmold")
        p = card.params
        tol = 1e-6
        self.assertAlmostEqual(far.params["cw"], p["zone_width"]["default"], delta=tol)
        self.assertAlmostEqual(far.params["ch"], p["zone_height"]["default"], delta=tol)
        z_centre = far.pose.offset[2] + far.params["z"] / 2
        self.assertAlmostEqual(z_centre - world["mouth"].at[2], p["zone_offset"]["default"], delta=tol)
        self.assertEqual(far.params["s0"], 0.0)                              # the zone starts at the seat, outward
        shell = next(n for n in nodes if n.role == "plug_shell")
        self.assertAlmostEqual(shell.params["cw"], p["card_width"]["default"], delta=tol)


class TestCatalogueVocabulary(unittest.TestCase):
    def test_no_alias_is_archetype_vocabulary(self):
        # T13: no part alias may equal an archetype evidence word (generic_box lost "box" and "block"), so a request
        # that asks for a box never names a generic part by that word
        rules = pt.load_rules(REPO / "design_rules.json")
        words = {tuple(pt.tokens(w)) for a in rules.archetypes.values() for w in a["evidence"]}
        self.assertIn(("box",), words)
        cat = pt.Catalog.load(BOTH)
        clashes = [(pid, n) for pid in cat.ids() for n in cat.get(pid).names if tuple(pt.tokens(n)) in words]
        self.assertEqual(clashes, [])


if __name__ == "__main__":
    unittest.main()
