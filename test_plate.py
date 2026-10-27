"""Tests for migration delta R12 (owner decision D1): structural forms as controller choices (forms.py), the plate
archetype (plate.py) and spec slots by form (ParseSpec). No Ollama: the controller's questions are scripted.

The plate tests run on a generic fixture catalogue written to a temporary folder (a block with a bolt_face and an
engage interface, the base it engages with keep-outs, a swept keep-out and a mirror_pair, plus the catalogue's own M4
bolt, nut and set screw); no number of any design is asserted here (T01's requirements stay judge-side).

What is checked:
* Spec slots by form: the shell's slots are asked unchanged when only shell parts are named (the regression prompts
  stay byte-identical); a named bolt_face part adds the plate's slots and the neutral wording; a mapped number whose
  unit word names another unit, or whose value leaves the slot's band, or a lo/hi pair out of order, is re-asked.
* Forms: feasibility from catalogue data with the reason for each infeasible form; one feasible form is plant
  feasibility (no question); several are a permutation-voted menu; no valid answer is the measured error
  (prescore:archetype); the form_evidence sensor and set_archetype (the closed loop switches a shell to a plate).
* The plate end to end: the engaged base placed by the engage datums, bolts and nuts on the hole axes in slots and hex
  channels along the declared adjustment, the part's keep-out cut, the outline placed clear of the swept keep-out, the
  sensors (clearances, travel, engagement, nut trap, size, printability, handedness, surface features) on the solids,
  and the controller's set_handedness / add_surface_feature applied and kept.
* Measurement helpers against hand calculations: section modulus of a rectangle, the bending stress of a cantilever
  plate, the bridge span of a pocket ceiling, the slot and hex channel outlines.
* Review fixes of R12 (TestReviewFixesR12): the clamp path sensors against a hand calculation (a nut on the two lands
  beside a slot keeps about 42 % of its face; over a slot wider than its flats it keeps none), the nut frame's floor and
  flange, the worst-case load stress over the adjustment range with the 45-degree width (hand calculation) and its
  typed conflict at the thickness limit, unit words with prefixes (kN, GPa, cm2), no design wording in the
  controller-visible vocabulary, the prescore ignoring the text sensor, unlinked or text-only L1s never verified, the
  keep-out names in the trace, the keep-out margin not counted twice, the bearing area on the engaged part, thin
  features and stud engagement measured, the part-shaped seat, the required adjustment.
"""

import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

import assembly as A
import assembly_checks as ac
import cad_agent as ca
import controller as C
import feature_graph as fg
import forms
import parts as pt
import plate as pl
from test_assembly import (BOTH, RULES_PATH, FakeLLM, design_for, run_stages, staged_to_derive, test_rules, texts)

REPO = Path(__file__).parent
GEN_PARTS = REPO / "benchmarks" / "generalize" / "parts"
HARDWARE = ("bolt_m4_iso4762", "nut_m4", "grub_m4_iso4026")
LID_SCREW = "screw_m3_selftap"           # the enclosure catalogue's lid screw, so a shell can be derived too

BLOCK = {
    "id": "fx_block", "schema": 1, "units": "mm", "names": ["widget carrier"], "kind": "mech",
    "source": "unit-test fixture: a block that bolts face-on and engages a base",
    "params": {"length": {"default": 30.0}, "width": {"default": 20.0}, "height": {"default": 6.0},
               "pitch": {"default": 12.0}, "slide": {"default": 8.0}},
    "geometry": [{"id": "body", "primitive": "box", "size": ["length", "width", "height"],
                  "at": ["-length / 2", "-width / 2", "-height"]}],
    "keepouts": [{"id": "gap", "primitive": "box", "size": ["length + 4", "width + 4", 1],
                  "at": ["-length / 2 - 2", "-width / 2 - 2", -1]}],
    "datums": {
        "FACE": {"kind": "plane", "at": [0, 0, 0], "normal": [0, 0, 1]},
        "BOTTOM": {"kind": "plane", "at": [0, 0, "-height"], "normal": [0, 0, -1]},
        "SEAT": {"kind": "plane", "at": [0, 0, -2], "normal": [0, 0, -1]},
        "CONTACT": {"kind": "plane", "at": [0, 0, -1], "normal": [0, 0, -1]},
        "CENTRE": {"kind": "axis", "at": [0, 0, 0], "dir": [0, 0, 1]},
        "HOLES": {"kind": "axis_list", "dir": [0, 0, 1], "diameter": 4.0, "keepout_diameter": 7.0,
                  "at": [["-pitch / 2", 0, 0], ["pitch / 2", 0, 0]]}},
    "interfaces": [
        {"id": "mount", "kind": "bolt_face", "holes": "HOLES", "face": "FACE", "head_seat": "SEAT", "thread": 4.0,
         "adjust": [{"dir": [1, 0, 0], "range": "slide"}]},
        {"id": "seat", "kind": "engage", "plane": "CONTACT", "centre": "CENTRE", "mates": "fx_base",
         "mate_plane": "TOP", "mate_point": "MID", "keepouts": ["gap"]}],
    "connectors": [],
}
BASE = {
    "id": "fx_base", "schema": 1, "units": "mm", "names": ["fixture base"], "kind": "mech",
    "source": "unit-test fixture: the base the block engages, with a contact keep-out and a swept side keep-out",
    "params": {"twist": {"default": 10.0}, "wall_y": {"default": 35.0}},
    "geometry": [{"id": "body", "primitive": "box", "size": [60, 40, 10], "at": [-30, -20, -10]}],
    "keepouts": [{"id": "under", "primitive": "box", "size": [20, 16, 4], "at": [-10, -8, -4]},
                 {"id": "wall", "primitive": "box", "size": [100, 40, 60], "at": [-50, "-wall_y - 40", -20],
                  "sweep": {"about": "MID", "axis": [0, 0, 1], "angle": "twist"}, "names": ["side wall"]}],
    "datums": {"TOP": {"kind": "plane", "at": [0, 0, 0], "normal": [0, 0, 1]},
               "MID": {"kind": "point", "at": [0, 0, 0]},
               "MIRROR": {"kind": "plane", "at": [0, 0, 0], "normal": [0, 1, 0]}},
    "mirror_pair": {"plane": "MIRROR", "names": ["mirror image"]},
    "connectors": [],
}
REQUEST = ("A printed plate holds the widget carrier on the fixture base. The plate is at least 60 mm each way. "
           "Its top face carries at least 6 raised studs.")


def fixture_catalogue(root: Path, lateral: float = 0.0) -> Path:
    """The fixture catalogue; `lateral` > 0 gives the block a second adjustment axis (across the hole line)."""
    cat = root / (f"fx_parts_lat" if lateral else "fx_parts")
    if cat.exists():
        return cat
    block = json.loads(json.dumps(BLOCK))
    if lateral:
        block["params"]["lateral"] = {"default": lateral}
        block["interfaces"][0]["adjust"].append({"dir": [0, 1, 0], "range": "lateral"})
    for data in (block, BASE):
        (cat / data["id"]).mkdir(parents=True)
        (cat / data["id"] / "part.json").write_text(json.dumps(data))
    for pid in HARDWARE:
        shutil.copytree(GEN_PARTS / pid, cat / pid)
    shutil.copytree(REPO / "benchmarks" / "enclosure" / "parts" / LID_SCREW, cat / LID_SCREW)
    return cat


def spec_by_value(want: dict):
    """A slot-mapping reply: each slot in `want` gets the number id whose value equals want[slot] (else none)."""
    import re

    def reply(prompt):
        nums = re.findall(r"^(n\d+) = ([\d.]+)", prompt, re.M)
        slots = re.findall(r"^- (\w+): ", prompt, re.M)
        return {s: next((i for i, v in nums if s in want and abs(float(v) - want[s]) < 1e-9), "none") for s in slots}
    return reply


def contents_of(parts: dict):
    def reply(prompt):
        return {ln[2:].split(":")[0]: {"quantity": parts.get(ln[2:].split(":")[0], 0)}
                for ln in prompt.splitlines() if ln.startswith("- ") and ":" in ln}
    return reply


class Case(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.fx = fixture_catalogue(cls.root)
        cls.rules_path = test_rules(cls.root, fn=24)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_fixture(self, tag: str, form: str = "plate", control=None, want=None, upto="ControllerLoop",
                    contents=None, request: str = REQUEST):
        d = design_for(request, [], self.root / tag, [self.fx], self.rules_path)
        script = {"assy_spec": [spec_by_value(want if want is not None else {"size_min": 60, "feature_count_min": 6})],
                  "assy_contents": [contents_of(contents or {"fx_block": 1, "fx_base": 1})],
                  forms.FORM_LABEL: [{"reason": "", "archetype": form}]}
        if control is not None:
            script[C.CONTROL_LABEL] = control
        llm = FakeLLM(script)
        status, child, st, results = staged_to_derive(d, llm, upto)
        return llm, status, child, st, results, d


# ---------------------------------------------------------------------------
# Spec slots by form, unit and band validation
# ---------------------------------------------------------------------------


class TestSpecSlotsByForm(Case):
    def test_shell_only_texts_keep_the_shell_slots_and_wording(self):
        st = A.AssemblyState(catalog=pt.Catalog.load(BOTH), rules=pt.load_rules(RULES_PATH), texts=texts("E1-01"))
        cands = forms.candidate_forms(st)
        self.assertEqual(cands, [forms.SHELL])
        self.assertEqual(forms.spec_slots(st.rules, cands), st.rules.spec_slots)
        self.assertEqual(forms.subject(cands), "An enclosure is being designed from this request and its requirements.")
        self.assertTrue(A.spec_prompt([], st.rules.spec_slots).startswith(forms.SUBJECTS[forms.SHELL]))

    def test_a_named_bolt_face_part_adds_the_plate_slots(self):
        cat = pt.Catalog.load([self.fx])
        st = A.AssemblyState(catalog=cat, rules=pt.load_rules(RULES_PATH), texts=[("request", REQUEST)])
        cands = forms.candidate_forms(st)
        self.assertEqual(cands, [forms.SHELL, forms.PLATE])
        names = [s["name"] for s in forms.spec_slots(st.rules, cands)]
        self.assertEqual(names[:len(st.rules.spec_slots)], [s["name"] for s in st.rules.spec_slots])
        self.assertIn("load_force", names)
        self.assertNotEqual(forms.subject(cands), forms.SUBJECTS[forms.SHELL])

    def test_unit_words_and_bands(self):
        rules = pt.load_rules(RULES_PATH)
        nums = {n["text"]: n for n in A.extract_numbers([("request", "a 2500 N load, 25 MPa, 600 mm2, 60 percent, "
                                                                      "between 80 and 105 mm, 4 x 3 holes")])}
        self.assertEqual((nums["2500"]["after"], nums["25"]["after"], nums["600"]["after"]), ("n", "mpa", "mm2"))
        slot = {s["name"]: s for v in rules.form_slots.values() for s in v}
        self.assertIsNone(forms.slot_violation(rules, slot["load_force"], nums["2500"]))
        self.assertIsNone(forms.slot_violation(rules, slot["strength"], nums["25"]))
        self.assertIn("is in mm, but", forms.slot_violation(rules, slot["size_min"], nums["2500"]))
        self.assertIsNotNone(forms.slot_violation(rules, slot["load_patch"], nums["600"]))      # mm2 is not mm
        self.assertIsNone(forms.slot_violation(rules, slot["size_min"], nums["80"]))           # no unit word: accepted
        self.assertIn("must lie in", forms.slot_violation(rules, slot["feature_coverage_min"], dict(nums["105 mm"],
                                                                                                    unit=None)))
        self.assertEqual(forms.pair_violations(rules.form_slots["plate"], {"size_min": 105, "size_max": 80})[0][1],
                         ["size_min", "size_max"])

    def test_parse_spec_reasks_a_unit_mismatch(self):
        d = design_for("The widget carrier plate carries a 300 N load and is at least 60 mm wide.", [],
                       self.root / "unit", [self.fx], self.rules_path)
        first = spec_by_value({"size_min": 300})            # the load's number for a length: wrong unit
        again = spec_by_value({"size_min": 60, "load_force": 300})
        llm = FakeLLM({"assy_spec_reask": [again], "assy_spec": [first]})
        status, _ = run_stages(d, llm, "ParseSpec")
        self.assertEqual(status, ca.Status.SUCCESS)
        st = d.assy
        self.assertEqual((st.spec["size_min"], st.spec["load_force"]), (60.0, 300.0))
        self.assertTrue(any("is in mm, but" in n for n in st.notes), st.notes)


# ---------------------------------------------------------------------------
# Forms: feasibility, the archetype question, the form sensor and set_archetype
# ---------------------------------------------------------------------------


class TestForms(Case):
    def test_feasibility_is_catalogue_data_with_reasons(self):
        cat = pt.Catalog.load(BOTH)
        st = A.AssemblyState(catalog=cat, rules=pt.load_rules(RULES_PATH), texts=texts("E1-01"))
        st.contents = [{"id": A.PRIMARY, "part": "perfboard", "kind": "board", "quantity": 1}]
        opts = {o["form"]: o for o in forms.catalogue_options(st)}
        self.assertTrue(opts["shell"]["feasible"])
        self.assertFalse(opts["plate"]["feasible"])
        self.assertIn(pt.BOLT_FACE, opts["plate"]["reason"])
        self.assertEqual(A.feasible_archetypes(st), [("tray_lid", "screws")])

    def test_menu_vote_and_one_question(self):
        llm, status, child, st, results, _ = self.run_fixture("vote", upto="ChooseArchetype")
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        rec = st.choices["archetype"]
        self.assertEqual((rec["value"], rec["by"]), ("plate+bolt_through", "llm"))
        self.assertEqual(sorted(rec["options"]), ["plate", "shell"])
        asked = [c for c in llm.calls if c[0] == forms.FORM_LABEL]
        self.assertEqual(len(asked), 2)                    # two options: two orderings
        self.assertNotEqual(asked[0][1], asked[1][1])
        self.assertIn("- plate: ", asked[0][1])

    def test_no_valid_answer_is_the_measured_error(self):
        _, status, _, st, _, _ = self.run_fixture("novote", form="neither", upto="ChooseArchetype")
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        rec = st.choices["archetype"]
        self.assertEqual(rec["by"], forms.PRESCORE_BY)
        self.assertEqual(set(rec["errors"]), {"tray_lid+screws", "plate+bolt_through"})
        self.assertEqual(C.decision_class(rec["by"], C.load_registry()), "guardrail")

    def test_one_feasible_form_asks_nothing(self):
        cat = pt.Catalog.load(BOTH)
        st = A.AssemblyState(catalog=cat, rules=pt.load_rules(RULES_PATH), texts=texts("E1-01"))
        st.contents = [{"id": A.PRIMARY, "part": "perfboard", "kind": "board", "quantity": 1}]
        self.assertIsNone(forms.choose(st, FakeLLM({}), "request"))
        self.assertEqual(st.choices["archetype"]["by"], "rule:only_feasible")
        self.assertEqual(C.decision_class("rule:only_feasible", C.load_registry()), "plant")

    def test_controller_switches_a_shell_to_the_plate(self):
        # changed in the R12 review 2 (N4): the text states a light preload, so the plate's default hex channels pass
        # the new fastener_bearing sensor and the switch is measured on the form alone (with the default preload the
        # channel's nut lands are crushed: 4 failing checks against the shell's 2, and the greedy step rejects it)
        llm, status, child, st, results, d = self.run_fixture(
            "switch", form="shell", want={"size_min": 60, "feature_count_min": 6, "fastener_preload": 200},
            request=REQUEST + " Each bolt is tightened to a 200 N preload.")
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        steps = [s for s in st.trajectory["steps"] if s.get("kind") != "initial"]
        first = st.trajectory["steps"][0]
        self.assertIn(forms.FORM_EVIDENCE, first["failing"])
        chosen = [s["chosen"] for s in steps]
        self.assertIn("set_archetype:plate", chosen)
        self.assertEqual(st.choices["archetype"]["value"], "plate+bolt_through")
        self.assertEqual(st.choices["archetype"]["by"], C.CONTROLLER_BY)
        self.assertTrue(forms.is_plate(st))
        self.assertTrue(results["form_evidence"].passed)

    def test_form_evidence_needs_two_buildable_forms(self):
        st = A.AssemblyState(catalog=pt.Catalog.load(BOTH), rules=pt.load_rules(RULES_PATH), texts=texts("E1-01"))
        st.forms = [{"form": "shell", "key": "tray_lid+screws", "feasible": True}]
        plan = ac.Plan()
        forms.add_form_checks(st, plan)
        self.assertEqual(plan.specs, [])


# ---------------------------------------------------------------------------
# The plate end to end on the fixture catalogue
# ---------------------------------------------------------------------------


class TestPlateEndToEnd(Case):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        tc = Case.run_fixture.__get__(cls("run"))
        cls.out = tc("plate")

    def test_proposal_and_corrections(self):
        llm, status, child, st, results, d = self.out
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        trace = st.trajectory
        first = trace["steps"][0]
        self.assertIn(f"{pl.HANDEDNESS}_{pl.BODY}", first["failing"])     # the plate is offset away from the wall
        self.assertIn("surface_features", first["failing"])              # the text's count is mapped, none placed
        kept = [s["chosen"] for s in trace["steps"][1:] if s.get("accepted")]
        self.assertIn("set_handedness:plate=mirror_pair", kept)
        self.assertTrue(any(k.startswith("add_surface_feature:top=") for k in kept))
        self.assertEqual([k for k, r in results.items() if not r.passed], [])

    def test_geometry_follows_the_catalogue(self):
        llm, status, child, st, results, d = self.out
        p = st.plate
        g = st.graph
        base = next(n for n in g.references() if n.part == "fx_base")
        res = st.resolved
        # the base's TOP plane lies on the block's CONTACT plane (engage pose), the plate's underside on it
        top = res.datums[f"{base.id}.TOP"].at[2]
        self.assertAlmostEqual(top, p["z_bot"], 6)
        self.assertAlmostEqual(p["z_bot"], -1.0, 6)
        bolts = [n for n in g.references() if n.part == "bolt_m4_iso4762"]
        nuts = [n for n in g.references() if n.part == "nut_m4"]
        self.assertEqual((len(bolts), len(nuts)), (2, 2))
        self.assertEqual(sorted(round(res.poses[n.id][0, 3], 6) for n in bolts), [-6.0, 6.0])
        self.assertIn(p["chain"]["length"], pt.stock_lengths(st.catalog.get("bolt_m4_iso4762")))
        self.assertGreaterEqual(p["tip"], p["nut_top"])
        self.assertLess(p["tip"], p["z_top"])
        self.assertEqual(p["slide"]["range"], 8.0)
        # the outline: the mapped minimum size, shifted away from the swept wall (asymmetric about the mirror plane)
        x0, y0, x1, y1 = p["outline"]
        self.assertGreaterEqual(min(x1 - x0, y1 - y0), 60.0)
        self.assertGreater(y0 + y1, 0.0)
        item = next(c["id"] for c in st.contents if c["part"] == "fx_base")
        self.assertTrue(results[f"clear_{item}_wall"].passed)
        self.assertTrue(results[f"clear_{item}_under"].passed)
        self.assertTrue(results["clear_gap"].passed)
        self.assertTrue(results["travel_x"].passed)
        self.assertEqual(results["printable"].evidence["orientation"], p["orientation"])

    def test_sensors_measure_the_solids(self):
        llm, status, child, st, results, d = self.out
        nt = results["nut_trap_0"]
        self.assertEqual(nt.evidence["basis"], "measured")
        flats = st.catalog.get("nut_m4").params["across_flats"]["default"]
        self.assertAlmostEqual(nt.evidence["width"], flats + 2 * 0.2, 2)
        self.assertEqual(results[f"{pl.HANDEDNESS}_{pl.BODY}"].evidence["declared"], "mirror_pair")
        sf = results["surface_features"]
        self.assertGreaterEqual(sf.evidence["value"], 6)
        auth = C.authority(st)
        self.assertEqual(auth["unregistered"], [])
        self.assertFalse(any(r["decision"] == "archetype" for r in auth["semantic_rule_decisions"]))

    def test_package(self):
        llm, status, child, st, results, d = self.out
        tree = A.build_assembly_tree(d, llm, self.fx, d.assy.rules_path)
        names = [type(c).__name__ for c in tree.children]
        for c in tree.children[names.index("Build"):]:
            self.assertEqual(c.update(), ca.Status.SUCCESS)
        wd = d.workdir
        self.assertTrue((wd / "plate.stl").is_file())
        self.assertTrue((wd / "plate_mirror.stl").is_file())
        lay_ = json.loads((wd / "layout.json").read_text())
        self.assertEqual(lay_["bodies"]["plate"]["orientation"], st.plate["orientation"])
        self.assertIn("mirror_pair", lay_["bodies"]["plate"])
        self.assertTrue(any(r["role"] == "engaged" for r in lay_["references"]))
        rep = json.loads((wd / "self_report.json").read_text())
        self.assertTrue(rep["all_passed"], [r["check_id"] for r in rep["results"] if not r["passed"]])


class TestNutFrame(Case):
    def test_two_adjustment_axes_get_the_nut_frame(self):
        # a hex channel covers one adjustment direction; the travel sensor across it fails (controllable while the
        # frame is buildable) and the controller's set_nut_retention frame covers both
        self.fx = fixture_catalogue(self.root, lateral=3.0)
        llm, status, child, st, results, d = self.run_fixture("frame")
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        first = st.trajectory["steps"][0]
        self.assertIn("travel_y", first["failing"])
        menu_ids = [a["id"] for s in st.trajectory["steps"][1:] for a in s["menu"]]
        self.assertIn("set_nut_retention:plate=frame", menu_ids)
        self.assertEqual(st.plate["retention"], "frame")
        self.assertIn(pl.FRAME, st.graph.bodies())
        self.assertEqual([k for k, r in results.items() if not r.passed], [])
        self.assertTrue(results["travel_x"].passed and results["travel_y"].passed)
        self.assertTrue(results["nut_frame_turn"].passed)
        self.assertAlmostEqual(results["nut_trap_0"].evidence["width"],
                               st.catalog.get("nut_m4").params["across_flats"]["default"] + 0.4, 2)
        # changed in the R12 review fix (B1): the clamp path is measured, and it holds. Each nut sits on the frame's own
        # floor (rules.plate_floor_min) and the frame bears on the pocket floor beside the slots at every adjustment
        # extreme (its flange is wider than the slots by rules.plate_wall_min on both sides)
        fr = st.plate["frame"]
        self.assertGreaterEqual(fr["floor"], st.rules.values["plate_floor_min"])
        for k in ("clamp_seat_0", "clamp_seat_1", "clamp_frame", "clamp_face"):
            self.assertTrue(results[k].passed, results[k].evidence)
            self.assertEqual(results[k].evidence["basis"], "measured")
        self.assertEqual(results["clamp_frame"].evidence["positions"], 9)       # every extreme of both ranges
        self.assertGreater(results["clamp_seat_0"].evidence["value"], 0.95)    # the whole face on the frame floor
        # the pre-fix frame (traps through the frame, no floor) leaves the nuts over the pocket-floor slot, which is
        # wider than their flats: the sensor sees no seat
        bodies = dict(st.solids)
        nd = st.catalog.get("nut_m4").params
        traps = [ac.m3d.Manifold.cylinder(fr["h"] + 2, nd["across_corners"]["default"] / 2 + 0.3,
                                          nd["across_corners"]["default"] / 2 + 0.3, 6).translate([h[0], h[1], fr["z0"] - 1])
                 for h in st.plate["holes"]]
        bodies[pl.FRAME] = bodies[pl.FRAME] - ac.union(traps)
        spec = next(sp for sp in A.build_plan(st).specs if sp["id"] == "clamp_seat_0")
        bad = pl.clamp_seat_check("clamp_seat_0", "clamp_seat", spec["args"], bodies, A.build_plan(st))
        self.assertFalse(bad.passed, bad.evidence)
        self.assertLess(bad.evidence["value"], 0.05)


class TestScrewIntoChain(Case):
    def test_tapped_part_gets_screws_from_the_free_face(self):
        # a catalogue part whose bolt_face holes are tapped (thread_depth, no head seat): the plate is the thinnest one
        # through which a stock screw engages at least rules.tapped_engagement_ratio diameters without bottoming; the
        # part's geometry above its face (a pilot boss, a shaft) is cut with rules.part_to_wall
        from test_assembly import gen_request
        cat = pt.Catalog.load(BOTH)
        part = next(pid for pid in cat.ids() if (pt.bolt_face_interface(cat.get(pid)) or {}).get("thread_depth"))
        gid = next(g for g in ("G16", "G37", "G32") if A.text_evidence([("request", gen_request(g)["request"])],
                                                                         cat.get(part).names))
        r = gen_request(gid)
        d = design_for(r["request"], r["l1"], self.root / "into", BOTH, self.rules_path)
        llm = FakeLLM({"assy_spec": [spec_by_value({})], "assy_contents": [contents_of({part: 1})],
                       "assy_params": [lambda p: {}], forms.FORM_LABEL: [{"reason": "", "archetype": "plate"}]})
        status, child, st, results = staged_to_derive(d, llm)
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        self.assertTrue(forms.is_plate(st))
        p = st.plate
        ratio = st.rules.values["tapped_engagement_ratio"]
        d_thread = p["chain"]["bolt_params"]["thread_diameter"]
        self.assertTrue(ratio * d_thread - 1e-9 <= p["engagement"] <= p["chain"]["depth"])
        self.assertIsNone(p["chain"]["nut"])
        self.assertTrue(any(x.get("cyl") for x in p["own"]))
        self.assertEqual([k for k, v in results.items() if not v.passed and k.startswith("bolt_")], [])


# ---------------------------------------------------------------------------
# Measurement helpers against hand calculations
# ---------------------------------------------------------------------------


class TestMeasurements(unittest.TestCase):
    def test_section_props_of_a_rectangle(self):
        b, h = 40.0, 6.0
        ring = np.array([[0, 0], [b, 0], [b, h], [0, h]], float)     # (u, z), counter-clockwise
        props = pl.section_props([ring], 1)
        self.assertAlmostEqual(props["area"], b * h, 6)
        self.assertAlmostEqual(props["zc"], h / 2, 6)
        self.assertAlmostEqual(props["I"], b * h ** 3 / 12.0, 6)
        self.assertAlmostEqual(props["c"], h / 2, 6)

    def test_edge_stress_of_a_cantilever_plate(self):
        L, W, t = 100.0, 30.0, 8.0
        solid = ac.m3d.Manifold.cube([L, W, t]).translate([-L / 2, -W / 2, 0])
        prim_lo, prim_hi = np.array([-10.0, -10.0, 0]), np.array([10.0, 10.0, 0])
        case = {"force": 1000.0, "patch": 20.0}
        rows = {r["edge"]: r for r in pl.edge_stresses(solid, [-L / 2, -W / 2, L / 2, W / 2], [], prim_lo, prim_hi, case)}
        arm = L / 2 - case["patch"] / 2 - 10.0
        want = case["force"] * arm * (t / 2) / (W * t ** 3 / 12.0)
        self.assertAlmostEqual(rows["+x"]["stress"], want, 3)
        self.assertEqual(rows["+y"]["stress"], 0.0)                       # the patch lies over the support

    def test_bridge_span_of_a_pocket_ceiling(self):
        rules = {"measure_tol": 1e-3, "overhang_angle_deg": 45.0, "bridge_max": 15.0}
        block = ac.m3d.Manifold.cube([60, 40, 10])
        pocket = ac.m3d.Manifold.cube([30, 20, 3]).translate([15, 10, -1])
        up = pl.overhangs(block - pocket, pl.ORIENTATIONS[0], rules)      # the pocket opens downward: its ceiling bridges
        self.assertAlmostEqual(up["worst_span"], 20.0, 3)
        self.assertAlmostEqual(up["violation"], 5.0, 3)
        down = pl.overhangs(block - pocket, pl.ORIENTATIONS[1], rules)    # flipped: the pocket opens up, nothing hangs
        self.assertEqual(down["violation"], 0.0)

    def test_slot_and_channel_outlines(self):
        from shapely.geometry import Point, Polygon
        slot = Polygon(pl.stadium(10.0, 4.0))
        self.assertTrue(slot.contains(Point(5.0, 1.99)) and slot.contains(Point(-6.99, 0)))
        self.assertGreaterEqual(slot.bounds[3] - slot.bounds[1], 4.0)
        ch = Polygon(pl.hex_channel(10.0, 7.4))
        self.assertAlmostEqual(ch.bounds[3] - ch.bounds[1], 7.4, 9)
        corners = 7.4 / math.cos(math.radians(30))
        self.assertAlmostEqual(ch.bounds[2] - ch.bounds[0], 10.0 + corners, 9)


class TestReviewFixesR12(Case):
    """The R12 review fixes on generic geometry (no design's numbers)."""

    PLAN = ac.Plan(tol=ac.Tol(measure=0.01, scale=1.0))

    def test_nut_seat_hand_calculation(self):
        # a 2 mm floor with a slot as wide as the bolt clearance (5.5 mm) under an ISO M5 nut (8 mm flats, flats
        # parallel to the slot): the nut keeps its two side lands. Hand calculation: hexagon (sqrt(3)/2) s^2 = 55.43 mm2;
        # the slot strip |y| <= 2.75 over the hexagon = 4 (e/2 * 2.75 - 2.75^2 / (2 sqrt 3)) = 42.08 mm2 (e = 9.238);
        # lands 13.35 mm2 of a nominal face 55.43 - pi/4 5.5^2 = 31.67 mm2: 42.2 %
        M = ac.m3d.Manifold
        floor = M.cube([40, 30, 2]).translate([-20, -15, 0]) - M.cube([30, 5.5, 4]).translate([-15, -2.75, -1])
        a = {"xy": [0.0, 0.0], "z": 2.0, "face": "hex", "size": 8.0, "hole": 5.5, "angle": 0.0, "shifts": [[0.0, 0.0]],
             "ratio": 0.3}
        e = 8.0 / math.cos(math.radians(30))
        hexa = math.sqrt(3) / 2 * 64.0
        strip = 4 * (e / 2 * 2.75 - 2.75 ** 2 / (2 * math.sqrt(3)))
        want = (hexa - strip) / (hexa - math.pi / 4 * 5.5 ** 2)
        r = pl.clamp_seat_check("s", "clamp_seat", a, {"plate": floor}, self.PLAN)
        self.assertTrue(r.passed, r.evidence)
        self.assertAlmostEqual(r.evidence["value"], want, 2)
        # the pre-fix nut frame's floor slot: as wide as the lateral range plus the clearance (10.5 mm > 8 mm flats)
        wide = M.cube([40, 30, 2]).translate([-20, -15, 0]) - M.cube([30, 10.5, 4]).translate([-15, -5.25, -1])
        r = pl.clamp_seat_check("s", "clamp_seat", a, {"plate": wide}, self.PLAN)
        self.assertFalse(r.passed)
        self.assertEqual(r.evidence["value"], 0.0)
        # lands on one side only: the nut tips into the slot (the axis is outside the bearing)
        side = M.cube([40, 30, 2]).translate([-20, -15, 0]) - M.cube([30, 20, 4]).translate([-15, -17.25, -1])
        r = pl.clamp_seat_check("s", "clamp_seat", a, {"plate": side}, self.PLAN)
        self.assertFalse(r.passed)
        self.assertIn("OUTSIDE", r.evidence["detail"])

    def test_load_stress_is_the_worst_adjustment_position(self):
        # a 100 x 120 x 8 plate on a footprint x in [-10, 10] that can be set 10 mm along x (+/-5): for the +x edge the
        # longest arm is with the footprint at -5: arm = 50 - 20/2 - (10 - 5) = 35 mm; the 45-degree width is
        # 20 + 2 * 35 = 90 mm (< 120): stress = F arm (t/2) / (w t^3 / 12) = 1000 * 35 * 4 / (90 * 512 / 12) = 36.46 MPa
        L, W, t = 100.0, 120.0, 8.0
        solid = ac.m3d.Manifold.cube([L, W, t]).translate([-L / 2, -W / 2, 0])
        lo, hi = np.array([-10.0, -10.0, 0]), np.array([10.0, 10.0, 0])
        case = {"force": 1000.0, "patch": 20.0}
        adjust = [{"dir": [1.0, 0.0, 0.0], "range": 10.0}]
        rows = {r["edge"]: r for r in pl.edge_stresses(solid, [-L / 2, -W / 2, L / 2, W / 2], adjust, lo, hi, case)}
        self.assertAlmostEqual(rows["+x"]["arm"], 35.0, 6)
        # changed in the R12 review 2 (N1): the patch is also moved along the edge; the worst is at a corner, where the
        # plate's own edge clips the 45-degree width to 20 + 35 = 55 mm (the patch centred on the edge: 90 mm, 36.46 MPa)
        self.assertAlmostEqual(rows["+x"]["width"], 55.0, 6)
        self.assertAlmostEqual(rows["+x"]["stress"], 1000 * 35 * 4 / (55 * t ** 3 / 12), 2)       # 59.66 MPa
        self.assertAlmostEqual(abs(rows["+x"]["patch_at"]), W / 2 - 10.0, 6)                      # at a corner
        self.assertEqual(rows["+x"]["shift"], [-5.0, 0.0])
        self.assertAlmostEqual(rows["-x"]["stress"], rows["+x"]["stress"], 3)      # symmetric
        # the +y edge has no adjustment along y: arm 60 - 10 - 10 = 40; at a corner the width is 20 + 40 = 60 mm
        self.assertAlmostEqual(rows["+y"]["stress"], 1000 * 40 * 4 / (60 * t ** 3 / 12), 2)
        # the pre-fix rule (the footprint at its far end: arm 25, the full 120 mm width) reported 19.5 MPa
        self.assertGreater(rows["+x"]["stress"], 1.8 * 1000 * 25 * 4 / (W * t ** 3 / 12))

    def test_load_stress_covers_corners_and_intermediate_shifts(self):
        """R12 review 2 (N1, N9), a hand calculation. The 100 x 120 x 8 plate above with a 1 x 40 mm through hole at
        x 11.5..12.5, |y| <= 20: the footprint's +x edge (10 + shift, shift -5..+5) passes through it only at an
        intermediate shift. At shift +2 the section plane x = 12 lies in the hole: arm = 40 - 12 = 28 mm, the
        45-degree width 20 + 2 x 28 = 76 mm; with the patch near the middle of the edge the window holds the whole hole,
        so 76 - 40 = 36 mm of material: stress = 1000 x 28 x 4 / (36 x 8^3 / 12) = 72.92 MPa. Sampling only the
        extremes and the middle (shift -5, 0, +5) with the patch at the edge's midpoint gave 36.46 MPa (the plate
        without the hole at shift -5); a corner patch at shift -5 gives 59.66. Without the hole the same section would
        carry the full 76 mm: 34.54 MPa, so the hole adds 38.38 MPa (section_loss)."""
        L, W, t = 100.0, 120.0, 8.0
        M = ac.m3d.Manifold
        plain = M.cube([L, W, t]).translate([-L / 2, -W / 2, 0])
        solid = plain - M.cube([1.0, 40.0, t + 2]).translate([11.5, -20.0, -1])
        lo, hi = np.array([-10.0, -10.0, 0]), np.array([10.0, 10.0, 0])
        case = {"force": 1000.0, "patch": 20.0}
        adjust = [{"dir": [1.0, 0.0, 0.0], "range": 10.0}]
        rows = {r["edge"]: r for r in pl.edge_stresses(solid, [-L / 2, -W / 2, L / 2, W / 2], adjust, lo, hi, case,
                                                        step=1.0)}
        w = rows["+x"]
        self.assertEqual(w["shift"], [2.0, 0.0])
        self.assertAlmostEqual(w["arm"], 28.0, 6)
        self.assertAlmostEqual(w["stress"], 1000 * 28 * 4 / (36 * t ** 3 / 12), 1)
        self.assertLessEqual(abs(w["patch_at"]), 18.0 + 1e-6)          # the window holds the whole hole
        loss = pl.section_loss(w, case, plain, {"hole": plain})
        self.assertAlmostEqual(loss["uncut"], 1000 * 28 * 4 / (76 * t ** 3 / 12), 1)
        self.assertAlmostEqual(loss["by_cut"][0]["adds"], w["stress"] - loss["uncut"], 2)
        self.assertIn("the cuts add (MPa): hole +38.4", pl.loss_words(loss))
        self.assertEqual(pl.probe_points(-5.0, 5.0, 4.0, (0.0,)), [-5.0, -1.666666667, 0.0, 1.666666667, 5.0])

    def test_load_stress_at_the_thickness_limit_is_a_typed_conflict(self):
        solid = ac.m3d.Manifold.cube([100, 40, 4]).translate([-50, -20, 0])
        plan = ac.Plan(tol=ac.Tol(measure=0.01, scale=1.0))
        plan.volumes["primary"] = ac.m3d.Manifold.cube([20, 20, 5]).translate([-10, -10, -5])
        a = {"case": {"force": 1000.0, "patch": 20.0, "allow": 10.0}, "plate": {"outline": [-50, -20, 50, 20],
             "adjust": []}, "tol": 0.05, "capped": True, "thickness": 4.0}
        r = pl.load_stress_check("load_stress", "load_stress", a, {"plate": solid}, plan)
        self.assertFalse(r.passed)
        self.assertIn("requirement question", r.evidence["conflict"])
        self.assertEqual(A.controllable([r]), ([], [r]))                       # the requirement loop's, not an action's
        r = pl.load_stress_check("load_stress", "load_stress", dict(a, capped=False), {"plate": solid}, plan)
        self.assertNotIn("conflict", r.evidence)                               # still sizeable: a controllable error

    def test_prefixed_unit_words_scale(self):
        rules = pt.load_rules(RULES_PATH)
        slot = {s["name"]: s for v in rules.form_slots.values() for s in v}
        nums = {n["text"]: n for n in A.extract_numbers([("request", "a 2.5 kN load, 0.05 GPa, 6 cm2, 250 g, 12 mm")])}
        self.assertEqual(forms.slot_value(rules, slot["load_force"], nums["2.5"]), 2500.0)
        self.assertAlmostEqual(forms.slot_value(rules, slot["strength"], nums["0.05"]), 50.0, 9)
        self.assertEqual(forms.slot_value(rules, slot["bearing_area_min"], nums["6"]), 600.0)
        self.assertEqual(forms.slot_value(rules, slot["size_min"], nums["12 mm"]), 12.0)   # regex unit: not scaled twice
        self.assertIsNone(forms.slot_violation(rules, slot["load_force"], nums["2.5"]))
        self.assertIn("is in N, but", forms.slot_violation(rules, slot["load_force"], nums["250"]))
        d = design_for("The widget carrier plate carries a 2.5 kN load and is at least 60 mm wide.", [],
                       self.root / "kn", [self.fx], self.rules_path)
        llm = FakeLLM({"assy_spec": [spec_by_value({"size_min": 60, "load_force": 2.5})]})
        status, _ = run_stages(d, llm, "ParseSpec")
        self.assertEqual(status, ca.Status.SUCCESS)
        self.assertEqual(d.assy.spec["load_force"], 2500.0)

    def test_controller_vocabulary_names_no_design(self):
        from test_no_hardcoding import catalogue_strings
        data = json.loads(RULES_PATH.read_text())
        texts = [w for row in data["archetypes"].values() if isinstance(row, dict) for w in row.get("evidence", [])]
        for block in data["building_blocks"].values():
            if isinstance(block, dict):
                for o in (block.get("options") or {}).values():
                    texts += [o.get("meaning", ""), o.get("source", "")]
        texts += [v["source"] for k, v in data["rules"].items() if k.startswith(("grip_", "clamp_", "bolt_tip"))]
        words = set(catalogue_strings()) | {"shoe", "cleat", "pedal", "cycling", "adapter"}
        for t in texts:
            for w in words:
                self.assertNotIn(f" {w} ", f" {t.lower()} ", (w, t))

    def test_prescore_ignores_the_text_sensor(self):
        import cad_checks as cc
        st = A.AssemblyState()
        calls = []

        def plant(sc):
            calls.append(sc.choices["archetype"]["value"])
            ev = cc.CheckResult(forms.FORM_EVIDENCE, "rules", forms.FORM_EVIDENCE, sc.choices["archetype"]["value"] == "b",
                                -1.0, "count", {}, {"basis": "text"})
            return None, [ev]
        orig = (A.snapshot, A.derive, A.plant_error)
        try:
            A.snapshot = lambda s: A.AssemblyState(choices={})
            A.derive = lambda sc: None
            A.plant_error = plant
            key, errors = forms.prescore_form(st, ["a", "b"])
        finally:
            A.snapshot, A.derive, A.plant_error = orig
        self.assertEqual(calls, ["a", "b"])
        self.assertEqual(errors["a"], errors["b"])           # the failing form_evidence of "a" is not counted
        self.assertEqual(key, "a")                           # a tie keeps the enumeration order

    def test_unlinked_or_text_only_l1_is_never_verified(self):
        import cad_checks as cc
        chk = [cc.Check("m", "rules", "clear_of", {}, "measured"), cc.Check("t", "rules", "form_evidence", {}, "text")]
        res = [cc.CheckResult("m", "rules", "clear_of", True, 1.0, "mm", {}, {"basis": "measured"}),
               cc.CheckResult("t", "rules", "form_evidence", True, 1.0, "count", {}, {"basis": "text"})]
        l1 = [{"id": "L1.1", "text": "a"}, {"id": "L1.2", "text": "b"}, {"id": "L1.3", "text": "c"}]
        rows = {r["l1_id"]: r for r in A.trace_matrix(l1, chk, res, {"m": ["L1.1"], "t": ["L1.1", "L1.2"]})}
        self.assertEqual((rows["L1.1"]["status"], rows["L1.2"]["status"], rows["L1.3"]["status"]),
                         ("PASS", "UNLINKED", "UNLINKED"))
        self.assertIn("only text sensors", rows["L1.2"]["note"])
        self.assertEqual(A.unlinked_l1(list(rows.values())), ["L1.2", "L1.3"])

    def test_package_with_an_unlinked_l1_is_unverified_and_names_link_features(self):
        l1 = [{"id": "L1.1", "text": "The plate keeps clear of the side wall at every position."},
              {"id": "L1.2", "text": "Its mirror image also fits."},
              {"id": "L1.3", "text": "The design is delivered with a written report."}]
        d = design_for(REQUEST, l1, self.root / "unlinked", [self.fx], self.rules_path)
        script = {"assy_spec": [spec_by_value({"size_min": 60, "feature_count_min": 6})],
                  "assy_contents": [contents_of({"fx_block": 1, "fx_base": 1})],
                  forms.FORM_LABEL: [{"reason": "", "archetype": "plate"}]}
        llm = FakeLLM(script)
        tree = A.build_assembly_tree(d, llm, self.fx, d.assy.rules_path)
        for c in tree.children:
            self.assertEqual(c.update(), ca.Status.SUCCESS, (type(c).__name__, d.assy.notes[-3:]))
        st = d.assy
        item = next(c["id"] for c in st.contents if c["part"] == "fx_base")
        self.assertEqual(st.links[f"clear_{item}_wall"], ["L1.1"])            # by the keep-out's names
        self.assertEqual(st.links[f"{pl.HANDEDNESS}_{pl.BODY}"], ["L1.2"])     # by the mirror pairing's names
        rec = A.finalize(d, llm)
        self.assertEqual(rec["failed"], [])
        self.assertEqual((rec["outcome"], rec["unlinked"]), ("unverified", ["L1.3"]))
        rep = json.loads((d.workdir / "self_report.json").read_text())
        self.assertEqual((rep["all_passed"], rep["verified"], rep["unlinked_l1"]), (True, False, ["L1.3"]))

    def test_keepout_margin_is_not_counted_twice(self):
        st = A.AssemblyState(spec={"ref_clearance": 2.0})
        self.assertEqual(pl.keepout_clearance(st, {"margin": 2.0}), 0.0)
        self.assertEqual(pl.keepout_clearance(st, {"margin": 0.5}), 1.5)
        self.assertEqual(pl.keepout_clearance(A.AssemblyState(), {"margin": 0.0}), 0.0)
        cat = pt.Catalog.load(BOTH)
        inst = cat.instantiate("pedal_shimano_pd_m520", {})
        self.assertGreater(pt.keepout_margin(inst, "crank_side"), 0.0)         # catalogue data, read by the plant

    def test_subject_keeps_the_enclosure_wording(self):
        sub = forms.subject([forms.SHELL, forms.PLATE])
        self.assertIn("an enclosure", sub)
        self.assertIn("plate", sub)
        self.assertEqual(forms.subject([forms.SHELL]), forms.SUBJECTS[forms.SHELL])

    def test_bearing_area_is_the_overlap_with_the_engaged_part(self):
        M = ac.m3d.Manifold
        plate = M.cube([60, 60, 5])
        plan = ac.Plan(tol=ac.Tol(measure=0.01, scale=1.0))
        plan.volumes["engaged"] = M.cube([20, 30, 10]).translate([50, 0, -10])      # overlaps 10 x 30
        a = {"z": 0.0, "limit": 100.0, "engaged": True}
        r = pl.bearing_area_check("b", "bearing_area", a, {"plate": plate}, plan)
        self.assertAlmostEqual(r.evidence["value"], 300.0, 3)
        r = pl.bearing_area_check("b", "bearing_area", dict(a, engaged=False), {"plate": plate}, plan)
        self.assertAlmostEqual(r.evidence["value"], 3600.0, 3)

    def test_thin_features_and_stud_engagement_are_measured(self):
        M = ac.m3d.Manifold
        a = {"body": "plate", "limit": 0.8, "step": 2.0}
        block = M.cube([40, 30, 10])
        wall = block - M.cube([20, 10, 12]).translate([10, 0.5, -1])        # a 0.5 mm side wall
        floor = block - M.cube([20, 10, 10]).translate([10, 10, 0.5])       # a 0.5 mm floor
        hole = block - M.cylinder(12, 3, 3, 48).translate([20, 15, -1])     # a hole: no thin feature
        for solid, ok in ((wall, False), (floor, False), (hole, True), (block, True)):
            r = pl.thin_feature_check("t", "thin_feature", a, {"plate": solid}, self.PLAN)
            self.assertEqual(r.passed, ok, r.evidence["detail"])
        r = pl.thin_feature_check("t", "thin_feature", a, {"plate": wall}, self.PLAN)
        self.assertAlmostEqual(r.evidence["value"], 0.5, 2)
        # a 3.3 mm tap hole 6 mm deep in a 10 mm block; over a pocket only 4 mm of it is in material
        tap = block - M.cylinder(7, 1.65, 1.65, 48).translate([10, 10, 4])
        s = {"body": "plate", "xy": [10, 10], "z_top": 10.0, "depth": 6.0, "tap": 3.3, "major": 4.0, "need": 5.5}
        r = pl.stud_engagement_check("e", "stud_engagement", s, {"plate": tap}, self.PLAN)
        self.assertTrue(r.passed, r.evidence)
        self.assertAlmostEqual(r.evidence["value"], 6.0, 1)
        pocket = tap - M.cube([10, 10, 2]).translate([5, 5, 4])
        r = pl.stud_engagement_check("e", "stud_engagement", s, {"plate": pocket}, self.PLAN)
        self.assertFalse(r.passed)
        self.assertAlmostEqual(r.evidence["value"], 4.0, 1)

    def test_part_shaped_seat_and_required_adjustment(self):
        prim = pt.Primitive("k", "cylinder", d=10.0, h=2.0, at=(0.0, 0.0, 0.0), dir=(0.0, 0.0, 1.0))
        shifts = pl._shifts([(np.array([1.0, 0, 0]), 20.0)])
        from shapely.geometry import Polygon
        poly = Polygon(pl.swept_plan(prim, np.eye(4), shifts))
        self.assertAlmostEqual(poly.area, 20 * 10 + math.pi * 25, 0)                # a stadium, not a 30 x 10 box
        self.assertIsNone(pl.swept_plan(pt.Primitive("b", "box", size=(1.0, 1.0, 1.0), at=(0.0, 0.0, 0.0)), np.eye(4),
                                        shifts))
        st = A.AssemblyState(spec={"adjust_min": 25.0, "adjust_cross_min": 4.0})
        out = pl.required_adjust(st, [(np.array([1.0, 0, 0]), 20.0), (np.array([0, 1.0, 0]), 2.0)], np.eye(3))
        self.assertEqual([round(r, 6) for _, r in out], [25.0, 4.0])
        out = pl.required_adjust(st, [(np.array([1.0, 0, 0]), 20.0)], np.eye(3))     # no declared cross axis: none added
        self.assertEqual([round(r, 6) for _, r in out], [25.0])
        self.assertEqual(pl.required_adjust(st, [], np.eye(3)), [])                  # nothing declared: nothing invented
        self.assertEqual([r for _, r in pl.required_adjust(A.AssemblyState(), [(np.array([1.0, 0, 0]), 20.0)],
                                                           np.eye(3))], [20.0])


class TestReviewFixesR12Second(Case):
    """The second adversarial review of R12 (ACCEPT-WITH-NITS): N2 a package whose every check passes and whose every
    L1 is traced reaches `verified` with rc 0; N4 the fastener bearing / punch-through sensor (hand calculation) and the
    typed note of a cut open on a contact face; N5 setpoint wording; N6 one stated value sets both band ends; N7 generic
    properties trace to the L1s naming them; N8 notes of the shell's layout stages leave the plate's record."""

    PLAN = ac.Plan(tol=ac.Tol(measure=0.01, scale=1.0))

    def test_fastener_bearing_hand_calculation(self):
        # an M5-sized hex nut face (8 mm across flats, 5.5 mm bolt hole) on a 3 mm printed floor with no slot under it:
        # bearing area = sqrt(3)/2 x 8^2 - pi/4 x 5.5^2 = 55.43 - 23.76 = 31.67 mm2; shear area = the hex perimeter
        # 6 x 8 / sqrt(3) = 27.71 mm times the 3 mm floor = 83.14 mm2. Under 1000 N: 31.6 MPa and 12.0 MPa; allowed 40 and
        # 20: ratio max(0.79, 0.60) = 0.79, it passes. On a 1 mm floor the shear is 36.1 MPa: ratio 1.80, it fails.
        M = ac.m3d.Manifold
        a = {"xy": [0.0, 0.0], "z": 3.0, "face": "hex", "size": 8.0, "hole": 5.5, "angle": 0.0, "shifts": [[0.0, 0.0]],
             "preload": 1000.0, "allow_bearing": 40.0, "allow_shear": 20.0, "preload_source": "test", "step": 0.2}
        floor3 = M.cube([40, 40, 3]).translate([-20, -20, 0]) - M.cylinder(5, 2.75, 2.75, 64).translate([0, 0, -1])
        r = pl.fastener_bearing_check("b", "fastener_bearing", a, {"plate": floor3}, self.PLAN)
        w = r.evidence["worst"]
        self.assertAlmostEqual(w["bearing_area"], math.sqrt(3) / 2 * 64 - math.pi / 4 * 5.5 ** 2, 0)
        self.assertAlmostEqual(w["shear_area"], 6 * 8 / math.sqrt(3) * 3, 0)
        self.assertAlmostEqual(r.evidence["value"], 1000 / 31.67 / 40, 2)
        self.assertTrue(r.passed, r.evidence["detail"])
        floor1 = M.cube([40, 40, 1]).translate([-20, -20, 2]) - M.cylinder(5, 2.75, 2.75, 64).translate([0, 0, -1])
        r = pl.fastener_bearing_check("b", "fastener_bearing", a, {"plate": floor1}, self.PLAN)
        self.assertFalse(r.passed)
        self.assertAlmostEqual(r.evidence["worst"]["floor_depth"], 1.0, 6)
        self.assertAlmostEqual(r.evidence["value"], 1000 / (6 * 8 / math.sqrt(3)) / 20, 2)
        self.assertNotIn("conflict", r.evidence)                 # a retention option may still change the seat
        r = pl.fastener_bearing_check("b", "fastener_bearing", dict(a, no_action=True), {"plate": floor1}, self.PLAN)
        self.assertIn("requirement question", r.evidence["conflict"])   # none left: typed, never actuated
        # a gap under the floor stops the shear path (the floor's contiguous depth, not the solid below it)
        stacked = floor1 + M.cube([40, 40, 1]).translate([-20, -20, 0])
        r = pl.fastener_bearing_check("b", "fastener_bearing", a, {"plate": stacked}, self.PLAN)
        self.assertAlmostEqual(r.evidence["worst"]["floor_depth"], 1.0, 6)

    def test_band_setpoints_and_limit_words(self):
        rules = pt.load_rules(RULES_PATH)
        st = A.AssemblyState(spec={"thickness_min": 8.0, "thickness_max": 14.0, "size_min": 70.0, "size_max": 70.0})
        st.rules = rules
        m = rules.values["design_margin"]
        self.assertEqual(pl.band_setpoints(st, "thickness_min", "thickness_max"), (8.0 + m, 14.0 - m))
        self.assertEqual(pl.band_setpoints(st, "size_min", "size_max"), (70.0, 70.0))      # one value: its centre
        self.assertIn("setpoint 13.90 (thickness_max 14 less the design margin)",
                      pl.limit_words(st, "thickness_max", 14.0 - m))
        self.assertEqual(pl.limit_words(st, "size_max", 70.0), "size_max 70")

    def test_one_stated_value_sets_both_band_ends(self):
        req = ("A printed plate holds the widget carrier on the fixture base. The plate is 70 mm each way. "
               "Its top face carries at least 6 raised studs.")
        d = design_for(req, [], self.root / "exact", [self.fx], self.rules_path)
        script = {"assy_spec": [spec_by_value({"size_exact": 70, "feature_count_min": 6})],
                  "assy_contents": [contents_of({"fx_block": 1, "fx_base": 1})],
                  forms.FORM_LABEL: [{"reason": "", "archetype": "plate"}]}
        status, child, st, results = staged_to_derive(d, FakeLLM(script))
        self.assertEqual(status, ca.Status.SUCCESS, st.notes)
        self.assertEqual((st.spec["size_min"], st.spec["size_max"]), (70.0, 70.0))
        self.assertEqual(st.spec_provenance["size_min"], st.spec_provenance["size_exact"])
        self.assertEqual([round(v, 6) for v in st.plate["size"]], [70.0, 70.0])
        self.assertTrue(results["plate_size_x"].passed and results["plate_size_y"].passed)
        self.assertFalse(any("size_max" in n for n in st.notes if n.startswith("derive: plate:")))

    def test_every_check_passing_and_every_l1_traced_is_verified_rc0(self):
        """N2 (positive), N4 note, N7, N8: the fixture end to end through cad_agent.main with L1s that each name what a
        check measures: rc 0, outcome verified, nothing unlinked."""
        from unittest import mock
        l1 = [{"id": "L1.1", "text": "The plate keeps clear of the side wall at every position."},
              {"id": "L1.2", "text": "Its mirror image also fits."},
              {"id": "L1.3", "text": "The plate prints without supports, as one manifold body, and fits the printer bed."},
              {"id": "L1.4", "text": "Each bolt shall engage its nut, no bolt tip shall stand proud, and the nuts clamp "
                                     "without pulling through."}]
        lp = self.root / "verified.l1.json"
        lp.write_text(json.dumps(l1))
        script = {"assy_spec": [spec_by_value({"size_min": 60, "feature_count_min": 6})],
                  "assy_contents": [contents_of({"fx_block": 1, "fx_base": 1})],
                  forms.FORM_LABEL: [{"reason": "", "archetype": "plate"}]}
        llm = FakeLLM(script)
        out = self.root / "out_verified"
        with mock.patch.object(ca, "OllamaAgent", lambda *a, **k: llm), mock.patch("builtins.print"):
            rc = ca.main(["--mode", "assembly", "--auto", "--l1", str(lp), "--parts", str(self.fx),
                          "--rules", str(self.rules_path), "--out", str(out), REQUEST])
        pkg = sorted(out.glob("*/"))[-1]
        rec = json.loads((pkg / "design.json").read_text())
        rep = json.loads((pkg / "self_report.json").read_text())
        failing = [r["check_id"] for r in rep["results"] if not r["passed"]]
        self.assertEqual(failing, [], rec["assembly"]["notes"][-6:])
        self.assertEqual((rc, rec["outcome"], rep["verified"], rep["unlinked_l1"]), (ca.EXIT_OK, "verified", True, []))
        checks = {c["id"]: c for c in json.loads((pkg / "checks.json").read_text())}
        self.assertIn("L1.3", checks["printable"]["links"])                  # N7: by design_rules trace_names
        self.assertIn("L1.3", checks["bbox"]["links"])
        self.assertIn("L1.3", checks["separable"]["links"])
        self.assertIn("L1.4", checks["bolt_engagement_0"]["links"])
        self.assertIn("L1.4", checks["bolt_tip_0"]["links"])
        self.assertIn("L1.4", checks["fastener_bearing_0"]["links"])
        # N8: the shell layout stages' notes and the "unplaced" note of the part the plate places are gone
        notes = rec["assembly"]["notes"]
        self.assertFalse([n for n in notes if n.startswith("arrange:") or " is unplaced: " in n], notes)
        # N4: the controller's nut frame leaves its pocket open on the free face, which the mapped feature slots
        # declare a working face: a typed note in self_report and the notes
        rows = rep["typed_notes"]
        self.assertEqual(rec["assembly"]["plate"]["retention"], "frame")
        top = next(r for r in rows if r["face"] == "top")
        self.assertEqual(top["type"], "open_cut_on_contact_face")
        self.assertIn("nut_pocket", [c["id"] for c in top["cuts"]])
        self.assertTrue(any("typed note: cuts open on the top face" in n for n in notes))


class TestRegistration(unittest.TestCase):
    def test_controller_knows_the_r12_actions(self):
        for kind in (forms.SET_ARCHETYPE, pl.SET_SURFACE, pl.SET_HANDEDNESS, pl.SET_RETENTION):
            self.assertIn(kind, C.APPLIERS)
        for typ in (forms.FORM_EVIDENCE, "surface_features", pl.HANDEDNESS, "printable", "travel"):
            self.assertIn(typ, C.ACTUATORS)
        reg = C.load_registry()
        self.assertEqual(reg["rule:first_option[archetype]"]["status"], "retired")
        self.assertEqual((reg["rule:only_feasible"]["class"], reg["rule:only_feasible"]["status"]), ("plant", "active"))


if __name__ == "__main__":
    unittest.main()
