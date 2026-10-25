"""Unit tests for cad_checks.py (typed checks, mutants, gates, error keys, sensitivity, deadbeat).

Standard-library unittest, no network. Layer-2 checks use manifold3d (installed in the
venv); the one test that compares those solids with OpenSCAD's STL is skipped when
OpenSCAD is not installed. Designs are hand-built like the fixtures in test_cad_agent.py;
the "real designs" tests replay component lists recorded by benchmark runs of cad_agent
(known-good ones from bench17 and the known-wrong ones from bench_new).
"""

import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

import cad_agent as ca
import cad_checks as cc

HAVE_OPENSCAD = bool(shutil.which(ca.OPENSCAD) or Path(ca.OPENSCAD).exists())
needs_openscad = unittest.skipUnless(HAVE_OPENSCAD, "OpenSCAD is not installed")

ON = {"x": "center", "y": "center", "z": "center"}


def place(parent, side="top", **align):
    return dict(ON, parent=parent, side=side, **align)


def comp(name, shape, params, where=None, count=1, arrangement=None):
    return ca.Component(name, name.replace("_", " "), shape, dict(params), where, count=count,
                        arrangement=arrangement)


def design(*components, request="test"):
    d = ca.Design(request=request, workdir=Path(tempfile.gettempdir()) / "cad_checks_tests")
    d.components = list(components)
    ca.layout(d)
    return d


def phone_stand(rest_place=None, lip=True):
    parts = [comp("base", "box", {"width": 80, "depth": 60, "height": 5}),
             comp("back_rest", "panel", {"width": 80, "height": 70, "thickness": 5, "angle": 70, "lean": "back"},
                  rest_place or place("base", y="back"))]
    if lip:
        parts.append(comp("lip", "box", {"width": 80, "depth": 5, "height": 10}, place("base", y="front")))
    return design(*parts)


def stool(arrangement="corners_xy", count=4):
    return design(comp("seat", "cylinder", {"diameter": 300, "height": 20, "axis": "z"}),
                  comp("leg", "box", {"width": 30, "depth": 30, "height": 400}, place("seat", "bottom"),
                       count=count, arrangement=arrangement))


def bookend():
    return design(comp("base", "box", {"width": 120, "depth": 100, "height": 5}),
                  comp("back_plate", "box", {"width": 120, "depth": 5, "height": 150}, place("base", y="back")))


def check(type_, **params):
    return cc.Check(id=f"{type_}_1", l1_id="L1.1", type=type_, params=params)


def result(d, type_, **params):
    return cc.run_check(d, check(type_, **params))


# ---------------------------------------------------------------------------
# Real designs recorded by benchmark runs (component lists from their design.json)
# ---------------------------------------------------------------------------

REAL = {
    "headphone_good": [
        ("base", "cylinder", {"diameter": 120, "height": 10, "axis": "z"}, None, 1, None),
        ("post", "cylinder", {"diameter": 25, "height": 250, "axis": "z"}, place("base"), 1, None),
        ("bar", "box", {"width": 100, "depth": 25, "height": 25}, place("post"), 1, None)],
    "headphone_bar_on_base": [
        ("base", "cylinder", {"diameter": 120, "height": 10, "axis": "z"}, None, 1, None),
        ("post", "cylinder", {"diameter": 25, "height": 250, "axis": "z"}, place("base"), 1, None),
        ("bar", "box", {"width": 100, "depth": 25, "height": 25}, place("base"), 1, None)],
    "plant_good": [
        ("top", "box", {"width": 200, "depth": 200, "height": 15}, None, 1, None),
        ("leg", "cylinder", {"diameter": 20, "height": 150, "axis": "z"}, place("top", "bottom"), 3, "triangle_xy")],
    "plant_legs_in_a_line": [
        ("top", "box", {"width": 200, "depth": 200, "height": 15}, None, 1, None),
        ("leg", "cylinder", {"diameter": 20, "height": 150, "axis": "z"}, place("top", "bottom"), 3, "row_y")],
    "toothbrush_good": [
        ("base", "box", {"width": 90, "depth": 90, "height": 6}, None, 1, None),
        ("cup", "tube", {"outer_diameter": 70, "inner_diameter": 50, "height": 100, "axis": "z"},
         place("base"), 1, None)],
    "toothbrush_upside_down": [
        ("cup", "tube", {"outer_diameter": 70, "inner_diameter": 60, "height": 100, "axis": "z"}, None, 1, None),
        ("base", "box", {"width": 90, "depth": 90, "height": 6}, place("cup"), 1, None)],
    "tray_upside_down": [
        ("floor", "box", {"width": 150, "depth": 100, "height": 3}, None, 1, None),
        ("front_wall", "box", {"width": 150, "depth": 3, "height": 30}, place("floor", "bottom", y="front"), 1, None),
        ("back_wall", "box", {"width": 100, "depth": 3, "height": 30}, place("floor", "bottom", y="back"), 1, None)],
    "door_stop_good": [
        ("body", "wedge", {"width": 150, "depth": 60, "height": 30, "high_side": "left"}, None, 1, None)],
    "door_stop_duplicate": [
        ("body", "wedge", {"width": 60, "depth": 150, "height": 30, "high_side": "left"}, None, 1, None),
        ("wedge", "wedge", {"width": 150, "depth": 60, "height": 30, "high_side": "left"},
         place("body", "back"), 1, None)],
    "phone_stand_good": [
        ("base", "box", {"width": 80, "depth": 60, "height": 5}, None, 1, None),
        ("back_rest", "panel", {"width": 60, "height": 70, "thickness": 3, "angle": 70, "lean": "back"},
         place("base", y="back"), 1, None),
        ("front_lip", "box", {"width": 80, "depth": 5, "height": 10}, place("base", y="front"), 1, None)],
}


def real(key):
    return design(*[comp(n, s, p, w, k, a) for n, s, p, w, k, a in REAL[key]])


# The checks one would write from each request's L1s (frozen before seeing any design).
REAL_CHECKS = {
    "headphone": [
        check("dimension", part="base", measure="diameter", value=120),
        check("relation", part="post", relation="on_top_of", other="base"),
        check("edge", part="post", other="base", where="center"),
        check("relation", part="bar", relation="on_top_of", other="post"),
        check("dimension", part="bar", measure="length", value=100),
        check("connected"), check("no_overlap"), check("stable")],
    "plant": [
        check("count", part="leg", count=3),
        check("relation", part="leg", relation="underneath", other="top"),
        check("arrangement", part="leg", pattern="spread", other="top"),
        check("stable")],
    "toothbrush": [
        check("relation", part="cup", relation="on_top_of", other="base"),
        check("edge", part="cup", other="base", where="center"),
        check("fits", object="cylinder", size=[18, 190], into=["cup"]),
        check("stable")],
    "tray": [
        check("count", part="wall", count=2),
        check("relation", part="wall", relation="on_top_of", other="floor"),
        check("span", part="wall", other="floor", axis="x"),
        check("fits", object="box", size=[100, 60, 20], into=["floor", "wall"], orientation="flat")],
    "door_stop": [
        check("count", shape="wedge", count=1),
        check("dimension", measure="height", value=30),
        check("dimension", measure="width", value=150)],
}
for _name, _checks in REAL_CHECKS.items():
    for _k, _c in enumerate(_checks):
        _c.id = f"{_name}_{_k}"


# ---------------------------------------------------------------------------
# Specs, rendering and schemas
# ---------------------------------------------------------------------------


class TestSpecs(unittest.TestCase):
    def test_defaults_text_and_round_trip(self):
        c = check("dimension", part="seat", measure="diameter", value=300)
        self.assertEqual(c.params["op"], "eq")
        self.assertEqual(c.text, "The seat's diameter is 300 mm (within 3 mm).")
        again = cc.Check.from_dict(json.loads(json.dumps(c.to_dict())))
        self.assertEqual(again, c)

    def test_validation_errors(self):
        self.assertIn("unknown check type", cc.validate_check(cc.Check("a", "L", "nope"))[0])
        self.assertIn("value is required", cc.validate_check(check("dimension", part="x", measure="width")))
        self.assertTrue(cc.validate_check(check("relation", part="a", relation="near", other="b")))
        self.assertTrue(cc.validate_check(check("fits", object="toaster", into=["cup"])))
        self.assertTrue(cc.validate_check(check("fits", object="box", into=["cup"])))  # a box needs a size
        self.assertEqual(cc.validate_check(check("fits", object="box", size=[1, 2, 3], into=["cup"])), [])
        self.assertTrue(cc.validate_check(check("shape", part="a", shape="pyramid")))

    def test_invalid_check_fails_instead_of_passing(self):
        r = cc.run_check(bookend(), check("dimension", part="base", measure="width"))
        self.assertFalse(r.passed)
        self.assertIn("invalid check", r.evidence["detail"])

    def test_schema_lists_parts_and_required_slots(self):
        s = cc.check_schema("relation", ["base", "cup"])
        self.assertEqual(s["properties"]["part"]["enum"], ["base", "cup"])
        self.assertIn("on_top_of", s["properties"]["relation"]["enum"])
        self.assertEqual(sorted(s["required"]), ["other", "part", "relation"])
        self.assertEqual(set(cc.SLOTS), set(cc.CHECKERS))

    def test_every_type_renders_english(self):
        samples = [
            check("count", part="leg", count=4), check("shape", part="seat", shape="cylinder", orient="z"),
            check("relation", part="cup", relation="on_top_of", other="base"),
            check("edge", part="lip", other="base", where="front"), check("span", part="wall", other="base", axis="x"),
            check("arrangement", part="leg", pattern="corners", other="seat"),
            check("touches", part="leg", other="seat"), check("connected"), check("no_overlap"),
            check("stable", load={"part": "shelf", "mass_g": 500}, tilt_deg=10),
            check("fits", object="pencil", into=["cup"]),
            check("rests_on", object="phone", support="back_rest", also_touches=["lip"])]
        texts = [c.text for c in samples]
        self.assertEqual(texts[0], "The design has exactly 4 leg parts.")
        self.assertEqual(texts[2], "The cup sits on top of the base, touching it.")
        self.assertEqual(texts[3], "The lip is along the front edge of the base.")
        self.assertIn("one near each corner of the seat", texts[5])
        self.assertIn("500 g load on the top of the shelf", texts[9])
        self.assertIn("A pencil (8 mm across, 170 mm long), standing upright, fits into the cup", texts[10])
        self.assertIn("leaning against the front of the back rest, also touching the lip", texts[11])
        prompt = cc.backtranslation_prompt(samples[2], "The cup shall stand on the base.")
        self.assertIn(texts[2], prompt)
        self.assertIn("The cup shall stand on the base.", prompt)

    def test_standin_library(self):
        self.assertEqual(sorted(cc.standin("phone")["dims"]), [9, 75, 150])
        self.assertEqual(cc.standin("pencil")["diameter"], 8)
        self.assertEqual(cc.standin("box", [10, 20, 30])["dims"], [10, 20, 30])
        with self.assertRaises(ValueError):
            cc.standin("box")


class TestSelect(unittest.TestCase):
    def test_exact_slug_and_word_matches(self):
        d = design(comp("floor", "box", {"width": 100, "depth": 50, "height": 3}),
                   comp("front_wall", "box", {"width": 100, "depth": 3, "height": 20}, place("floor", y="front")),
                   comp("back_wall", "box", {"width": 100, "depth": 3, "height": 20}, place("floor", y="back")))
        self.assertEqual([c.name for c in cc.select(d, "front_wall")], ["front_wall"])
        self.assertEqual([c.name for c in cc.select(d, "Front Wall")], ["front_wall"])
        self.assertEqual([c.name for c in cc.select(d, "walls")], ["front_wall", "back_wall"])
        self.assertEqual(cc.select(d, "lid"), [])


# ---------------------------------------------------------------------------
# Layer-2 solids match the shape library (and OpenSCAD)
# ---------------------------------------------------------------------------

SHAPE_CASES = [
    ("box", {"width": 30, "depth": 20, "height": 10}),
    ("panel", {"width": 40, "height": 50, "thickness": 4, "angle": 60, "lean": "back"}),
    ("panel", {"width": 40, "height": 50, "thickness": 4, "angle": 75, "lean": "left"}),
    ("wedge", {"width": 30, "depth": 40, "height": 20, "high_side": "front"}),
    ("wedge", {"width": 30, "depth": 40, "height": 20, "high_side": "right"}),
    ("cylinder", {"diameter": 20, "height": 50, "axis": "x"}),
    ("cylinder", {"diameter": 20, "height": 50, "axis": "y"}),
    ("tube", {"outer_diameter": 40, "inner_diameter": 30, "height": 60, "axis": "z"}),
    ("sphere", {"diameter": 30}),
]


class TestSolids(unittest.TestCase):
    def test_bbox_and_volume_match_the_shape_library(self):
        for shape, params in SHAPE_CASES:
            c = comp("p", shape, params)
            c.size = ca.SHAPES[shape].size(params)
            solid = cc.component_solid(c)
            box = solid.bounding_box()
            for a in range(3):
                self.assertAlmostEqual(box[a], 0.0, places=3, msg=(shape, params))
                self.assertAlmostEqual(box[3 + a], c.size[a], places=3, msg=(shape, params))
            vol = cc.mass_properties(solid)[0]
            self.assertAlmostEqual(vol / ca.shape_volume(c), 1.0, delta=0.02, msg=(shape, params))

    def test_wedge_under_a_board_is_flipped(self):
        c = comp("bracket", "wedge", {"width": 10, "depth": 100, "height": 40, "high_side": "back"},
                 place("board", "bottom"))
        _, com = cc.mass_properties(cc.component_solid(c))
        self.assertGreater(com[2], 20)  # flat face up: the mass sits near the top

    @needs_openscad
    def test_solids_agree_with_openscad(self):
        with tempfile.TemporaryDirectory() as tmp:
            for k, (shape, params) in enumerate(SHAPE_CASES):
                c = comp("p", shape, params)
                scad = Path(tmp) / f"s{k}.scad"
                scad.write_text(f"$fn = {ca.SEGMENTS};\n{ca.component_scad(c)}\n")
                res = ca.compile_scad(scad, scad.with_suffix(".stl"))
                self.assertTrue(res.ok, res.problems)
                vol_scad = ca.mesh_mass(res.tris)[0]
                vol_m = cc.mass_properties(cc.component_solid(c))[0]
                self.assertAlmostEqual(vol_m / vol_scad, 1.0, delta=0.01, msg=shape)
                lo, hi = res.bbox
                box = cc.component_solid(c).bounding_box()
                for a in range(3):
                    self.assertAlmostEqual(box[a], lo[a], delta=0.05)
                    self.assertAlmostEqual(box[3 + a], hi[a], delta=0.05)


# ---------------------------------------------------------------------------
# Layer 1 checks
# ---------------------------------------------------------------------------


class TestLayer1(unittest.TestCase):
    def test_count(self):
        d = stool()
        self.assertTrue(result(d, "count", part="leg", count=4).passed)
        r = result(d, "count", part="legs", count=3)
        self.assertFalse(r.passed)
        self.assertEqual(r.evidence["measured"], 4)
        self.assertTrue(result(d, "count", part="leg", count=3, op="ge").passed)
        self.assertFalse(result(d, "count", part="leg", count=3, op="le").passed)
        self.assertTrue(result(d, "count", shape="round", count=1).passed)
        self.assertTrue(result(d, "count", count=5).passed)

    def test_dimension_measures(self):
        d = phone_stand()
        self.assertTrue(result(d, "dimension", part="base", measure="width", value=80).passed)
        self.assertTrue(result(d, "dimension", part="back_rest", measure="angle", value=70).passed)
        self.assertTrue(result(d, "dimension", part="back_rest", measure="thickness", value=5).passed)
        self.assertTrue(result(d, "dimension", part="lip", measure="top", value=15).passed)
        self.assertTrue(result(d, "dimension", measure="height", value=75).passed)  # whole object
        self.assertTrue(result(d, "dimension", part="lip", measure="height", value=8, op="ge").passed)
        r = result(d, "dimension", part="base", measure="depth", value=80)
        self.assertFalse(r.passed)
        self.assertAlmostEqual(r.margin, (0.8 - 20) / 80)
        self.assertEqual(r.depends_on, {"components": ["base"], "params": ["base.depth"]})
        r = result(d, "dimension", part="base", measure="diameter", value=80)
        self.assertFalse(r.passed)
        self.assertIn("does not apply", r.evidence["detail"])
        tube = design(comp("cup", "tube", {"outer_diameter": 60, "inner_diameter": 50, "height": 90, "axis": "z"}))
        self.assertTrue(result(tube, "dimension", part="cup", measure="thickness", value=5).passed)
        self.assertTrue(result(tube, "dimension", part="cup", measure="inner_diameter", value=50).passed)
        self.assertTrue(result(tube, "dimension", part="cup", measure="height", param="height", value=90).passed)

    def test_shape_and_orientation(self):
        d = stool()
        self.assertTrue(result(d, "shape", part="seat", shape="round").passed)
        self.assertTrue(result(d, "shape", part="seat", shape="cylinder", orient="flat").passed)
        self.assertTrue(result(d, "shape", part="leg", shape="box", orient="upright").passed)
        self.assertFalse(result(d, "shape", part="leg", shape="box", orient="flat").passed)
        self.assertFalse(result(d, "shape", part="seat", shape="box").passed)

    def test_relation(self):
        d = phone_stand()
        self.assertTrue(result(d, "relation", part="lip", relation="on_top_of", other="base").passed)
        self.assertFalse(result(d, "relation", part="base", relation="on_top_of", other="lip").passed)
        self.assertTrue(result(d, "relation", part="base", relation="underneath", other="lip").passed)
        side = design(comp("block", "box", {"width": 50, "depth": 50, "height": 50}),
                      comp("knob", "cylinder", {"diameter": 10, "height": 10, "axis": "x"}, place("block", "right")))
        self.assertTrue(result(side, "relation", part="knob", relation="right_of", other="block").passed)
        self.assertTrue(result(side, "relation", part="knob", relation="beside", other="block").passed)
        self.assertFalse(result(side, "relation", part="knob", relation="left_of", other="block").passed)
        # above without touching: ordering only
        tall = real("headphone_good")
        self.assertTrue(result(tall, "relation", part="bar", relation="on_top_of", other="base",
                               touching=False).passed)
        self.assertFalse(result(tall, "relation", part="bar", relation="on_top_of", other="base").passed)

    def test_edge(self):
        d = phone_stand()
        self.assertTrue(result(d, "edge", part="lip", other="base", where="front").passed)
        self.assertFalse(result(d, "edge", part="lip", other="base", where="back").passed)
        self.assertTrue(result(d, "edge", part="back_rest", other="base", where="back").passed)
        self.assertTrue(result(d, "edge", part="lip", other="base", where="center", axis="x").passed)
        self.assertFalse(result(d, "edge", part="lip", other="base", where="center").passed)

    def test_span(self):
        d = bookend()
        self.assertTrue(result(d, "span", part="back_plate", other="base", axis="x").passed)
        self.assertFalse(result(d, "span", part="back_plate", other="base", axis="y").passed)
        short = phone_stand()
        short.components[1].params["width"] = 60
        ca.layout(short)
        r = result(short, "span", part="back_rest", other="base", axis="x")
        self.assertFalse(r.passed)
        self.assertIn("covers 60 of 80", r.evidence["detail"])

    def test_arrangement(self):
        self.assertTrue(result(stool(), "arrangement", part="leg", pattern="corners", other="seat").passed)
        row = stool("row_x")
        self.assertFalse(result(row, "arrangement", part="leg", pattern="corners", other="seat").passed)
        # On a round seat cad_agent pulls the middle copies of a row out to the ends
        # (round_parent_fractions), so the spacing is uneven and "row" rightly fails.
        self.assertFalse(result(row, "arrangement", part="leg", pattern="row", axis="x").passed)
        bench = design(comp("top", "box", {"width": 300, "depth": 100, "height": 20}),
                       comp("leg", "box", {"width": 30, "depth": 30, "height": 400}, place("top", "bottom"),
                            count=4, arrangement="row_x"))
        self.assertTrue(result(bench, "arrangement", part="leg", pattern="row", axis="x").passed)
        self.assertFalse(result(stool(), "arrangement", part="leg", pattern="row", axis="x").passed)
        self.assertFalse(result(row, "arrangement", part="leg", pattern="spread").passed)
        self.assertTrue(result(stool(), "arrangement", part="leg", pattern="spread").passed)  # other = parent
        ends = stool("ends_x", 2)
        self.assertTrue(result(ends, "arrangement", part="leg", pattern="ends", axis="x").passed)
        self.assertFalse(result(ends, "arrangement", part="leg", pattern="ends", axis="y").passed)
        tri = stool("triangle_xy", 3)
        self.assertTrue(result(tri, "arrangement", part="leg", pattern="triangle").passed)
        self.assertFalse(result(stool(), "arrangement", part="leg", pattern="triangle").passed)  # 4 legs

    def test_missing_parts_and_empty_designs_fail(self):
        d = bookend()
        r = result(d, "relation", part="lid", relation="on_top_of", other="base")
        self.assertFalse(r.passed)
        self.assertIn("no laid-out part named 'lid'", r.evidence["detail"])
        empty = design()
        for c in [check("count", count=0), check("no_overlap"), check("connected"), check("stable"),
                  check("dimension", measure="height", value=10)]:
            self.assertFalse(cc.run_check(empty, c).passed, c.type)


# ---------------------------------------------------------------------------
# Layer 2 checks
# ---------------------------------------------------------------------------


class TestLayer2(unittest.TestCase):
    def test_touches_and_floating_panel(self):
        self.assertTrue(result(phone_stand(), "touches", part="back_rest", other="base").passed)
        # Against the back face, a backward-leaning panel touches the plate's bbox but not the plate.
        d = phone_stand(rest_place=place("base", "back"))
        r = result(d, "touches", part="back_rest", other="base")
        self.assertFalse(r.passed)
        self.assertEqual(r.layer, 2)
        self.assertFalse(result(d, "connected").passed)
        self.assertTrue(result(phone_stand(), "connected").passed)

    def test_sphere_on_a_face_is_a_point_contact(self):
        # A ball can only touch a face at a point; that point counts as its joint
        # (with the 20 mm^2 rule a ball foot had no feasible side and placement never ended).
        d = design(comp("base", "cylinder", {"diameter": 50, "height": 6, "axis": "z"}),
                   comp("ball", "sphere", {"diameter": 60}, place("base")))
        self.assertTrue(result(d, "touches", part="ball", other="base").passed)
        self.assertTrue(result(d, "connected").passed)
        self.assertFalse(result(d, "touches", part="ball", other="base", min_area=20).passed)

    def test_no_overlap(self):
        self.assertTrue(result(real("headphone_good"), "no_overlap").passed)
        r = result(real("headphone_bar_on_base"), "no_overlap")
        self.assertFalse(r.passed)
        self.assertIn("post and bar overlap", r.evidence["detail"])

    def test_stable(self):
        self.assertTrue(result(stool(), "stable").passed)
        tip = design(comp("base", "box", {"width": 30, "depth": 20, "height": 2}),
                     comp("block", "box", {"width": 30, "depth": 80, "height": 40}, place("base", y="back")))
        r = result(tip, "stable")
        self.assertFalse(r.passed)
        self.assertIn("outside", r.evidence["detail"])
        shelf = bookend()
        self.assertTrue(result(shelf, "stable").passed)
        heavy = result(shelf, "stable", load={"part": "back_plate", "mass_g": 5000, "offset": [0, 40]})
        self.assertFalse(heavy.passed)
        self.assertLess(result(stool(), "stable", tilt_deg=20).margin, result(stool(), "stable").margin)
        # three legs in a line balance (bare centre of mass inside) but a 5 degree nudge tips them
        line = real("plant_legs_in_a_line")
        self.assertTrue(result(line, "stable", tilt_deg=0).passed)
        self.assertFalse(result(line, "stable").passed)

    def test_fits_into_a_cup(self):
        holder = design(comp("base", "box", {"width": 70, "depth": 70, "height": 4}),
                        comp("cup", "tube", {"outer_diameter": 60, "inner_diameter": 50, "height": 90, "axis": "z"},
                             place("base")))
        r = result(holder, "fits", object="pencil", into=["cup"])
        self.assertTrue(r.passed, r.evidence)
        self.assertAlmostEqual(r.evidence["measured"], 90, delta=0.1)
        fat = result(holder, "fits", object="cylinder", size=[52, 100], into=["cup"])
        self.assertFalse(fat.passed)
        self.assertIn("hole 50 mm across", fat.evidence["detail"])

    def test_fits_between_walls_and_in_a_tray(self):
        card = design(comp("base", "box", {"width": 90, "depth": 60, "height": 5}),
                      comp("back_wall", "box", {"width": 90, "depth": 5, "height": 20}, place("base", y="back")),
                      comp("front_wall", "box", {"width": 90, "depth": 5, "height": 10}, place("base", y="front")))
        self.assertTrue(result(card, "fits", object="box", size=[85, 55, 2], into=["back_wall", "front_wall"],
                               between=True).passed)
        self.assertFalse(result(card, "fits", object="box", size=[85, 55, 60], into=["back_wall", "front_wall"],
                                between=True, orientation="upright").passed)
        tray = design(comp("floor", "box", {"width": 150, "depth": 100, "height": 3}),
                      comp("front_wall", "box", {"width": 150, "depth": 3, "height": 30}, place("floor", y="front")),
                      comp("back_wall", "box", {"width": 150, "depth": 3, "height": 30}, place("floor", y="back")))
        self.assertTrue(result(tray, "fits", object="box", size=[100, 60, 20], into=["floor", "wall"],
                               orientation="flat").passed)
        self.assertFalse(result(tray, "fits", object="box", size=[100, 120, 20], into=["floor", "wall"],
                                orientation="flat").passed)

    def test_rests_on_leaning_and_lying(self):
        r = result(real("phone_stand_good"), "rests_on", object="phone", support="back_rest", also_touches=["base"])
        self.assertTrue(r.passed, r.evidence)
        self.assertEqual(r.evidence["measured"]["touching"], ["back_rest", "base"])
        # the lip is at the front, so the phone (resting against the back rest) never touches it
        r = result(real("phone_stand_good"), "rests_on", object="phone", support="back_rest",
                   also_touches=["front_lip"])
        self.assertFalse(r.passed)
        self.assertIn("does not touch front_lip", r.evidence["detail"])

        def ramp(h):
            return design(comp("base", "box", {"width": 80, "depth": 120, "height": 5}),
                          comp("ramp", "wedge", {"width": 80, "depth": 120, "height": h, "high_side": "back"},
                               place("base")))
        steep = result(ramp(60), "rests_on", object="phone", support="ramp", mode="lie")  # 26.6 deg, no stop
        self.assertFalse(steep.passed)
        self.assertAlmostEqual(steep.evidence["measured"]["required_mu"], 0.5, delta=0.02)
        self.assertTrue(result(ramp(60), "rests_on", object="phone", support="ramp", mode="lie", mu=0.6).passed)
        self.assertTrue(result(ramp(20), "rests_on", object="phone", support="ramp", mode="lie").passed)

    def test_rests_on_needs_a_lip_at_middling_angles(self):
        def stand(angle, lip):
            parts = [comp("base", "box", {"width": 80, "depth": 120, "height": 5}),
                     comp("rest", "panel", {"width": 80, "height": 60, "thickness": 5, "angle": angle, "lean": "back"},
                          place("base", y="back"))]
            return design(*parts)
        self.assertFalse(result(stand(55, False), "rests_on", object="phone", support="rest").passed)
        self.assertTrue(result(stand(80, False), "rests_on", object="phone", support="rest").passed)
        # at 85 degrees the centre of mass is only ~2 mm behind the corner it stands on: it rests
        # (tilt_deg=0) but a 5 degree nudge tips it forward, so it is not robustly at rest
        self.assertTrue(result(stand(85, False), "rests_on", object="phone", support="rest", tilt_deg=0).passed)
        self.assertFalse(result(stand(85, False), "rests_on", object="phone", support="rest").passed)


# ---------------------------------------------------------------------------
# Mutants and gates
# ---------------------------------------------------------------------------


class TestMutants(unittest.TestCase):
    def test_kinds_and_no_equivalent_mutants(self):
        d = stool()
        ms = cc.mutants(d)
        kinds = {m.kind for m in ms}
        self.assertTrue({"remove", "flip", "scale2", "scale05", "row", "detach", "duplicate"} <= kinds)
        base = cc.geometry_signature(d)
        self.assertTrue(all(cc.geometry_signature(m.design) != base for m in ms))
        self.assertEqual(d.components[1].arrangement, "corners_xy")  # the original is untouched
        row = next(m for m in ms if m.name == "row:leg")
        self.assertEqual(row.design.component("leg").arrangement, "row_x")

    def test_flip_root_turns_the_design_upside_down(self):
        d = real("toothbrush_good")
        flipped = next(m for m in cc.mutants(d) if m.name == "flip:base").design
        self.assertEqual(flipped.component("cup").place["side"], "bottom")
        self.assertFalse(cc.run_check(flipped, REAL_CHECKS["toothbrush"][0]).passed)

    def test_reparent_and_remove(self):
        d = real("headphone_good")
        names = [m.name for m in cc.mutants(d)]
        self.assertIn("reparent:bar", names)
        removed = next(m for m in cc.mutants(d) if m.name == "remove:post").design
        self.assertIsNone(removed.component("post"))
        self.assertEqual(removed.component("bar").place["parent"], "base")

    def test_non_vacuity_gate(self):
        d = real("headphone_good")
        checks = REAL_CHECKS["headphone"][:5] + [
            cc.Check("vacuous", "L1.9", "count", {"part": "post", "count": 0, "op": "ge"}),
            cc.Check("loose", "L1.9", "dimension", {"part": "post", "measure": "height", "value": 250, "tol": 1e4})]
        reports = {r.check_id: r for r in cc.non_vacuity(d, checks)}
        for cid in ("headphone_0", "headphone_1", "headphone_3"):
            self.assertTrue(reports[cid].ok, reports[cid])
        self.assertIn("reparent:bar", reports["headphone_3"].killed)
        self.assertIn("flip:post", reports["headphone_1"].killed)
        self.assertFalse(reports["vacuous"].ok)
        self.assertEqual(reports["loose"].reason, "only detects a missing part")
        self.assertIn("remove:post", reports["loose"].killed)
        self.assertTrue(all(r.fails_on_empty for r in reports.values()))

    def test_connected_is_killed_by_detach(self):
        d = phone_stand()
        rep = cc.non_vacuity(d, [check("connected")])[0]
        self.assertTrue(rep.ok)
        self.assertTrue(any(k.startswith("detach:") for k in rep.killed))

    def test_number_coverage(self):
        checks = [check("dimension", part="post", measure="height", value=250),
                  check("count", part="foot", count=4)]
        self.assertEqual(cc.number_coverage("The post shall be 250 mm tall on four feet.", checks), [])
        missing = cc.number_coverage("The post shall be 25 mm thick and 25 cm tall.", checks)
        self.assertEqual([m[0] for m in missing], [25.0])  # 25 cm = 250 mm is covered; 25 mm is not
        self.assertEqual(cc.number_coverage("A phone shall rest on it.", [check("rests_on", object="phone",
                                                                                support="rest")]), [])
        self.assertEqual(cc.number_coverage("Leaning at 70 degrees.", [check(
            "dimension", part="rest", measure="angle", value=70)]), [])


# ---------------------------------------------------------------------------
# Error aggregation
# ---------------------------------------------------------------------------


def fake(passed, margin, hard=True):
    return cc.CheckResult("c", "L1", "dimension", passed, margin, "mm", {}, {}, 1, hard)


class TestErrorKey(unittest.TestCase):
    def test_lexicographic_and_strict(self):
        a = cc.error_key([fake(False, -0.5), fake(True, 0.2)])
        self.assertEqual((a.hard_failures, a.violation), (1, 0.5))
        b = cc.error_key([fake(False, -0.1), fake(False, -0.1)])
        self.assertTrue(cc.strictly_better(a, b))                 # fewer failures beats smaller violation
        self.assertFalse(cc.strictly_better(b, a))
        c = cc.error_key([fake(False, -0.4), fake(True, 0.0)])
        self.assertTrue(cc.strictly_better(c, a))                 # same count, smaller violation
        self.assertFalse(cc.strictly_better(a, a))                # ties are never accepted
        s1 = cc.error_key([fake(True, 0.1)], soft_score=0.9)
        s2 = cc.error_key([fake(True, 0.1)], soft_score=0.6)
        self.assertTrue(cc.strictly_better(s1, s2))
        soft = cc.error_key([fake(False, -0.3, hard=False)])
        self.assertEqual((soft.hard_failures, soft.violation, soft.soft), (0, 0.0, 0.3))
        self.assertLess(cc.ErrorKey(0, 1.0), cc.ErrorKey(1, 0.0))


# ---------------------------------------------------------------------------
# Sensitivity and deadbeat
# ---------------------------------------------------------------------------


class TestSensitivity(unittest.TestCase):
    def test_localisation_and_controllability(self):
        d = phone_stand()
        checks = [cc.Check("w", "L1", "dimension", {"part": "base", "measure": "width", "value": 100}),
                  cc.Check("legs", "L2", "count", {"part": "leg", "count": 4}),
                  cc.Check("lip", "L3", "edge", {"part": "lip", "other": "base", "where": "back"})]
        rep = cc.sensitivity(d, checks)
        self.assertEqual(rep.movers["w"], ["base.width=72", "base.width=88"])
        self.assertEqual(rep.improvers["w"], ["base.width=88"])
        self.assertEqual(rep.localisation["w"], ["base"])
        self.assertEqual(rep.uncontrollable, ["legs"])
        self.assertIn("lip.y=back", rep.improvers["lip"])
        self.assertEqual(rep.localisation["lip"][0], "lip")
        self.assertTrue(all(k in rep.knobs for k in rep.matrix["w"]))


class TestOnePartDesigns(unittest.TestCase):
    def test_shape_whole_object_and_count_checks_are_not_vacuous(self):
        # These were all rejected for the one-part wedge, ruler and bangle in the pilot.
        d = design(comp("wedge", "wedge", {"width": 300, "depth": 60, "height": 20, "high_side": "back"}))
        checks = [check("shape", part="wedge", shape="wedge"), check("dimension", measure="width", value=300),
                  check("count", count=1, op="eq")]
        for k, c in enumerate(checks):
            c.id = f"c{k}"
        reports = cc.non_vacuity(d, checks)
        self.assertEqual([r.ok for r in reports], [True, True, True])
        self.assertIn("reshape:wedge", reports[0].killed)

    def test_flat_strip_as_a_box(self):
        d = design(comp("body", "box", {"width": 300, "depth": 30, "height": 3}))
        self.assertTrue(result(d, "dimension", measure="length", value=300).passed)
        self.assertTrue(result(d, "dimension", measure="thickness", value=3).passed)
        self.assertTrue(result(d, "shape", part="body", shape="panel", orient="flat").passed)
        self.assertFalse(result(bookend(), "shape", part="base", shape="panel", orient="upright").passed)


class TestSatisfiability(unittest.TestCase):
    def egg_cup(self):
        d = design(comp("base", "box", {"width": 100, "depth": 60, "height": 5}),
                   comp("cup", "tube", {"outer_diameter": 45, "inner_diameter": 41, "height": 30, "axis": "z"},
                        place("base")))
        egg = cc.Check("egg", "L1.5", "fits", {"object": "cylinder", "size": [43, 60], "into": ["cup"], "min_depth": 20})
        dia = cc.Check("dia", "L1.2", "dimension", {"part": "cup", "measure": "diameter", "value": 45})
        hole = cc.Check("hole", "L1.3", "dimension", {"part": "cup", "measure": "inner_diameter", "value": 41})
        return d, egg, dia, hole

    def test_conflict_with_accepted_checks_is_rejected(self):
        d, egg, dia, hole = self.egg_cup()
        rep = cc.satisfiability(d, egg, [dia, hole], cc.mutants(d))
        self.assertFalse(rep.ok)
        self.assertEqual(rep.reason, "conflict")
        self.assertEqual(rep.conflicts, ["dia", "hole"])

    def test_reachable_or_passing_checks_are_kept(self):
        d, egg, dia, hole = self.egg_cup()
        self.assertTrue(cc.satisfiability(d, egg, [], cc.mutants(d)).ok)   # nothing to break
        taller = cc.Check("h", "L1.4", "dimension", {"part": "cup", "measure": "height", "value": 40})
        rep = cc.satisfiability(d, taller, [dia, hole])
        self.assertEqual((rep.ok, rep.reason), (True, "reachable"))
        self.assertEqual(cc.satisfiability(d, dia, [hole]).reason, "passes now")

    def test_abstains_on_an_inconsistent_design(self):
        d, egg, dia, hole = self.egg_cup()
        d.components.append(comp("cup2", "tube", {"outer_diameter": 45, "inner_diameter": 41, "height": 30,
                                                  "axis": "z"}, place("base")))   # overlaps the first cup
        ca.layout(d)
        self.assertEqual(cc.satisfiability(d, egg, [dia, hole], cc.mutants(d)).reason, "unknown")

    def test_zero_size_is_invalid(self):
        zero = cc.Check("z", "L1", "dimension", {"part": "wedge", "measure": "height", "value": 0})
        self.assertIn("cannot be built", cc.validate_check(zero)[0])
        self.assertEqual(cc.validate_check(cc.Check("b", "L1", "dimension",
                                                    {"part": "base", "measure": "bottom", "value": 0})), [])


class TestDeadbeat(unittest.TestCase):
    def test_single_parameter_dimension_is_set_directly(self):
        d = phone_stand()
        chk = cc.Check("w", "L1", "dimension", {"part": "base", "measure": "width", "value": 100})
        fixes = cc.deadbeat(d, chk)
        self.assertEqual([(f.component, f.param, f.old, f.new) for f in fixes], [("base", "width", 80, 100)])
        fixed = cc.apply_fixes(d, fixes)
        self.assertTrue(cc.run_check(fixed, chk).passed)
        self.assertEqual(d.component("base").params["width"], 80)  # original untouched

    def test_operators_round_parts_and_spans(self):
        d = design(comp("cup", "tube", {"outer_diameter": 60, "inner_diameter": 50, "height": 90, "axis": "z"}))
        ge = cc.Check("h", "L1", "dimension", {"part": "cup", "measure": "height", "value": 100, "op": "ge"})
        self.assertEqual(cc.deadbeat(d, ge)[0].new, 100)
        dia = cc.Check("d", "L1", "dimension", {"part": "cup", "measure": "diameter", "value": 70})
        self.assertEqual(cc.deadbeat(d, dia)[0].param, "outer_diameter")
        bad = cc.Check("d", "L1", "dimension", {"part": "cup", "measure": "diameter", "value": 40})
        self.assertEqual(cc.deadbeat(d, bad), [])     # would make the hole bigger than the tube
        short = phone_stand()
        short.components[1].params["width"] = 60
        ca.layout(short)
        span = cc.Check("s", "L1", "span", {"part": "back_rest", "other": "base", "axis": "x"})
        fixes = cc.deadbeat(short, span)
        self.assertEqual((fixes[0].param, fixes[0].new), ("width", 80))
        self.assertTrue(cc.run_check(cc.apply_fixes(short, fixes), span).passed)

    def test_structural_or_multi_parameter_failures_are_left_to_the_llm(self):
        d = phone_stand()
        top = cc.Check("t", "L1", "dimension", {"part": "lip", "measure": "top", "value": 30})
        self.assertEqual(cc.deadbeat(d, top), [])
        rel = cc.Check("r", "L1", "relation", {"part": "lip", "relation": "underneath", "other": "base"})
        self.assertEqual(cc.deadbeat(d, rel), [])
        ok = cc.Check("ok", "L1", "dimension", {"part": "base", "measure": "width", "value": 80})
        self.assertEqual(cc.deadbeat(d, ok), [])


# ---------------------------------------------------------------------------
# Records, the verification matrix, and real benchmark designs
# ---------------------------------------------------------------------------


class TestRecords(unittest.TestCase):
    def test_design_json_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = stool()
            d.workdir = Path(tmp)
            path = ca.write_design_json(d, "verified")
            back = cc.design_from_json(path)
            self.assertEqual([c.name for c in back.components], ["seat", "leg"])
            self.assertEqual(back.component("leg").positions, d.component("leg").positions)

    def test_verification_matrix_lists_failures_first(self):
        d = real("plant_legs_in_a_line")
        l1 = [{"id": "L1.1", "text": "Three legs."}, {"id": "L1.2", "text": "Legs spread out."},
              {"id": "L1.3", "text": "Not covered."}]
        checks = [cc.Check("a", "L1.1", "count", {"part": "leg", "count": 3}),
                  cc.Check("b", "L1.2", "arrangement", {"part": "leg", "pattern": "spread", "other": "top"})]
        rows = cc.verification_matrix(l1, checks, cc.run_checks(d, checks))
        self.assertEqual([r["l1_id"] for r in rows], ["L1.3", "L1.2", "L1.1"])
        self.assertEqual(rows[0]["note"], "no check covers this requirement")
        self.assertFalse(rows[1]["passed"])
        self.assertTrue(rows[2]["passed"])
        text = cc.matrix_text(rows)
        self.assertTrue(text.startswith("FAIL"))
        self.assertIn("footprint coverage 0.00", text)


class TestRealDesigns(unittest.TestCase):
    """The checks written from each request pass on the known-good design and catch the known-wrong one."""

    def assert_all_pass(self, key, checks):
        for r in cc.run_checks(real(key), checks):
            self.assertTrue(r.passed, f"{key}: {r.check_id} {r.evidence['detail']}")

    def failing(self, key, checks):
        return {r.check_id for r in cc.run_checks(real(key), checks) if not r.passed}

    def test_headphone_bar_on_the_base(self):
        self.assert_all_pass("headphone_good", REAL_CHECKS["headphone"])
        self.assertEqual(self.failing("headphone_bar_on_base", REAL_CHECKS["headphone"]),
                         {"headphone_3", "headphone_6"})  # bar not on the post; bar passes through the post

    def test_plant_stand_legs_in_a_line(self):
        self.assert_all_pass("plant_good", REAL_CHECKS["plant"])
        self.assertEqual(self.failing("plant_legs_in_a_line", REAL_CHECKS["plant"]), {"plant_2", "plant_3"})

    def test_toothbrush_holder_upside_down(self):
        self.assert_all_pass("toothbrush_good", REAL_CHECKS["toothbrush"])
        self.assertEqual(self.failing("toothbrush_upside_down", REAL_CHECKS["toothbrush"]),
                         {"toothbrush_0", "toothbrush_2"})

    def test_tray_upside_down(self):
        bad = self.failing("tray_upside_down", REAL_CHECKS["tray"])
        self.assertEqual(bad, {"tray_1", "tray_2", "tray_3"})  # walls underneath, back wall short, no cavity

    def test_door_stop_duplicate_wedge(self):
        self.assert_all_pass("door_stop_good", REAL_CHECKS["door_stop"])
        self.assertIn("door_stop_0", self.failing("door_stop_duplicate", REAL_CHECKS["door_stop"]))

    def test_phone_stand(self):
        self.assert_all_pass("phone_stand_good", [
            check("rests_on", object="phone", support="back_rest", also_touches=["base"]),
            check("edge", part="front_lip", other="base", where="front"),
            check("dimension", part="back_rest", measure="angle", value=70), check("stable")])


if __name__ == "__main__":
    unittest.main()
