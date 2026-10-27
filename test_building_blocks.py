"""Tests for the generic building blocks (building_blocks.py; migration delta R11, owner decision D1). No Ollama: the
controller's questions are scripted; the train texts and both catalogues are data.

What is checked:
* Contents admission: every catalogue part a text names by an alias is a candidate unless it is an accessory (a plug a
  connector mates, a stack option, a fastener); the regression texts get exactly the candidates they had before R11.
* The seat interface (parts.seat_interface / support_names): read from plane datums only; a mount_holes part is
  unchanged.
* Cradle retention for a primary without mounting holes, end to end: the proposal (the vocabulary's default, a plain
  pocket) is derived and fails the retention sensor (+z free travel); the menu offers only the options the plant can
  build (an infeasible option is named with its reason in the sensor's words); the controller's set_retention is
  applied on a fork, re-derived and kept; the sensors (supported, retention, rib_interference) pass on the solids and
  on the delivered STLs; stop leaves the failure visible and controllable; the decision records who made it.
* Snap clips on a part whose top-face edges are free: arms, hooks, strain and overlap sensors; an arm too short for
  the strain limit makes the option infeasible.
"""

import json
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

import assembly as A
import assembly_checks as ac
import building_blocks as bb
import cad_agent as ca
import controller as C
import feature_graph as fg
import layout as lay
import parts as pt
from test_assembly import (BOTH, PARTS, RULES_PATH, FakeLLM, all_none, design_for, gen_request, gen_texts, request,
                           staged_to_derive, test_rules)

REPO = Path(__file__).parent


def contents_reply(parts: dict):
    """A Contents answer: the given parts with their quantities (and exposure), every other candidate 0."""
    def reply(prompt):
        out = {}
        for line in prompt.splitlines():
            if line.startswith("- ") and ":" in line:
                pid = line[2:].split(":")[0]
                out[pid] = dict(parts.get(pid, {"quantity": 0}))
                if "cable connector" in line and "exposed" not in out[pid]:
                    out[pid]["exposed"] = "no"
        return out
    return reply


def holeless_module(cat: pt.Catalog, gid: str) -> str:
    """The module part a train text names that has no mount_holes interface (read from the catalogue, not a literal)."""
    texts = gen_texts(gid)
    return next(pid for pid in cat.ids() if cat.get(pid).kind == "module" and pt.mount_interface(cat.get(pid)) is None
                and A.text_evidence(texts, cat.get(pid).names))


def cradle_run(root: Path, gid: str, parts: dict, control=None, tag: str = ""):
    r = gen_request(gid)
    d = design_for(r["request"], r["l1"], root / f"{gid}{tag}", BOTH, test_rules(root, fn=24))
    def no_size(prompt):                     # every part size: "none" (the text states it nowhere)
        tail = prompt.split("or \"none\".", 1)[-1]
        return {ln[2:].split(":")[0]: "none" for ln in tail.splitlines() if ln.startswith("- ")}

    script = {"assy_spec": [all_none], "assy_contents": [contents_reply(parts)], "assy_params": [no_size]}
    if control is not None:
        script[C.CONTROL_LABEL] = control
    llm = FakeLLM(script)
    status, child, st, results = staged_to_derive(d, llm)
    return llm, status, child, st, results


class Case(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.cat = pt.Catalog.load(BOTH)
        cls.rules = pt.load_rules(RULES_PATH)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class TestContentsAdmission(Case):
    def state(self, texts, cat=None):
        st = A.AssemblyState()
        st.catalog, st.rules, st.texts = cat or self.cat, self.rules, list(texts)
        return st

    def test_accessories_are_read_from_catalogue_references(self):
        acc = bb.accessory_ids(self.cat)
        mated = {c["mates"] for pid in self.cat.ids() for c in self.cat.get(pid).data.get("connectors", []) or []
                 if c.get("mates")}
        stacks = {o for pid in self.cat.ids() for o in (self.cat.get(pid).data.get("mount") or {}).get("stack_options", [])}
        fasteners = {pid for pid in self.cat.ids() if self.cat.get(pid).kind == "fastener"}
        self.assertTrue(mated and stacks and fasteners)
        self.assertEqual(acc, mated | stacks | fasteners)

    def test_named_mechanical_parts_become_candidates(self):
        # iteration 005: 19 train designs stopped with "nothing to design around" because only electronics kinds and
        # mount_holes parts were offered; a motor, an extrusion, a bearing, a fan are offered now when the text names them
        for gid in ("G16", "G18", "G29"):
            st = self.state(gen_texts(gid))
            named = A.named_parts(st)
            got = bb.admissible_named(st, [])
            self.assertTrue(got, gid)
            for pid in got:
                self.assertIn(pid, named)
                self.assertNotIn(pid, bb.accessory_ids(self.cat))
            kinds = {self.cat.get(pid).kind for pid in got}
            self.assertTrue(kinds - set(A.CONTENT_KINDS), (gid, kinds))   # parts Contents never offered before R11

    def test_regression_candidates_unchanged(self):
        # the regression texts name nothing new: their Contents prompts (and so the 9B's answers) stay as they were
        enc = pt.Catalog.load(PARTS)
        for rid in ("E1-01", "V1", "V2", "V3"):
            r = request(rid)
            st = self.state([("request", r["request"])] + [(x["id"], x["text"]) for x in r["l1"]], enc)
            d = type("D", (), {"base_request": r["request"], "request": r["request"], "assy": st})()
            c = A.Contents.__new__(A.Contents)
            c.design = d
            got = A.Contents.candidates(c)
            with mock.patch.object(bb, "admissible_named", lambda *_: []):     # the pre-R11 candidate rule
                old = A.Contents.candidates(c)
            self.assertEqual(got, old, rid)


class TestSeatInterface(Case):
    def inst(self, pid):
        return self.cat.instantiate(pid, {})

    def test_seat_and_top_planes_from_datums(self):
        mod = holeless_module(self.cat, "G03")
        s = pt.seat_interface(self.inst(mod))
        self.assertEqual(s["kind"], pt.SEAT)
        inst = self.inst(mod)
        self.assertEqual(list(inst.datums[s["seat"]].normal), [0, 0, -1])
        self.assertEqual(list(inst.datums[s["top"]].normal), [0, 0, 1])
        # the top is the lowest +Z plane above the seat (a part with a taller +Z plane keeps the lower one)
        for pid in self.cat.ids():
            part = self.cat.get(pid)
            if part.request_params() or pt.mount_interface(part) is not None:
                continue
            i = self.inst(pid)
            s = pt.seat_interface(i)
            if s is None:
                continue
            zs = [i.datums[k].at[2] for k, d in i.datums.items() if isinstance(d, pt.Plane)
                  and list(d.normal) == [0, 0, 1] and d.at[2] > i.datums[s["seat"]].at[2]]
            self.assertAlmostEqual(i.datums[s["top"]].at[2], min(zs), msg=pid)

    def test_part_without_a_top_plane_has_no_seat(self):
        no_top = [pid for pid in self.cat.ids() if not self.cat.get(pid).request_params()
                  and pt.mount_interface(self.cat.get(pid)) is None and self.cat.get(pid).kind == "connector"]
        self.assertTrue(no_top)
        for pid in no_top:
            inst = self.inst(pid)
            ups = [k for k, d in inst.datums.items() if isinstance(d, pt.Plane) and list(d.normal) == [0, 0, 1]]
            if not ups:
                self.assertIsNone(pt.seat_interface(inst), pid)
                with self.assertRaises(pt.PartError):
                    pt.support_names(inst)

    def test_mount_holes_part_unchanged(self):
        for pid in self.cat.ids():
            part = self.cat.get(pid)
            if pt.mount_interface(part) is not None and not part.request_params():
                self.assertEqual(pt.support_names(self.inst(pid)), pt.mount_names(part), pid)


class TestCradleRetention(Case):
    def test_proposal_pocket_fails_retention_and_ribs_are_offered(self):
        mod = holeless_module(self.cat, "G03")
        llm, status, child, st, results = cradle_run(self.root, "G03", {mod: {"quantity": 1, "exposed": "yes"}},
                                                     control=[{"action": C.STOP}], tag="_stop")   # changed in the R02 merge (R11): content-keyed id, was letter B
        self.assertEqual(status, ca.Status.SUCCESS, st.notes[-4:])
        # the proposal: the default option (plant), recorded rule:default_retention
        ch = st.choices["retention[board]"]
        self.assertEqual((ch["value"], ch["by"]), (bb.default_option(st.rules), "rule:default_retention"))
        r = results["retention_board"]
        self.assertFalse(r.passed)
        self.assertEqual(r.evidence["worst"], "+z")                 # nothing holds it down
        self.assertGreater(r.evidence["travel"]["+z"], st.rules.values["retention_play_max"])
        for d in ("-X", "+X", "-Y", "+Y"):                          # the rim locates it with the sliding fit
            self.assertAlmostEqual(r.evidence["travel"][d], st.rules.values["sliding_fit"])
        self.assertTrue(results["supported"].passed, results["supported"].evidence)
        # the menu: only the buildable options (crush ribs); snap clips are named with the plant's reason
        step = st.trajectory["steps"][1]
        kinds = [(m["kind"], m["value"]) for m in step["menu"]]
        self.assertEqual(kinds, [(bb.SET_RETENTION, "crush_ribs"), (C.STOP, None)])
        self.assertIn("snap_clips (", r.evidence["detail"])
        self.assertIn("cannot build", r.evidence["detail"])
        terms = C.error_vector(st, list(results.values()), {})
        t = next(t for t in terms if t.check == "retention_board")
        self.assertTrue(t.controllable and t.actionable)
        self.assertEqual(t.unit, "mm")
        self.assertIn("decrease the free travel", t.direction)
        prompt = next(p for lb, p, _ in llm.calls if lb.startswith(C.CONTROL_LABEL))
        self.assertIn("board retention: pocket", prompt)
        self.assertIn("crush_ribs", prompt)

    def test_controller_chooses_crush_ribs_end_to_end(self):
        mod = holeless_module(self.cat, "G03")
        llm, status, child, st, results = cradle_run(self.root, "G03", {mod: {"quantity": 1, "exposed": "yes"}})
        self.assertEqual(status, ca.Status.SUCCESS, st.notes[-4:])
        ch = st.choices["retention[board]"]
        self.assertEqual((ch["value"], ch["by"], ch["step"]), ("crush_ribs", C.CONTROLLER_BY, 1))
        self.assertEqual(st.control["retention"], "crush_ribs")
        self.assertTrue(results["retention_board"].passed, results["retention_board"].evidence)
        self.assertEqual(results["retention_board"].evidence["travel"]["+z"], 0.0)
        ribs = [k for k in results if k.startswith("rib_interference_")]
        self.assertGreaterEqual(len(ribs), 4)
        self.assertTrue(all(results[k].passed for k in ribs))
        sides = {k[len("rib_interference_"):].split("_")[2] for k in ribs}       # cradle_rib_<side>_<k>
        self.assertTrue({"xm", "xp"} <= sides or {"ym", "yp"} <= sides, sides)
        failing = [k for k, v in results.items() if not v.passed]
        self.assertEqual(failing, [], failing)
        self.assertEqual(st.trajectory["stop"]["reason"], "every check passes")
        # every cradle feature is on the base and has its designed-contact envelope (role seat)
        feats = [n for n in st.graph if n.role in bb.CRADLE_ROLES]
        self.assertTrue(feats)
        for n in feats:
            self.assertEqual(n.body, "base")
            self.assertTrue(n.source.startswith("rule:cradle.crush_ribs."))
            self.assertEqual(st.graph.nodes[f"{n.id}_contact"].role, "seat")
        self.assertNotIn("fastener[board]", st.choices)          # no holes, no board screw
        self.assertFalse([n for n in st.graph if n.role in ("standoff", "driver")])
        audit = C.authority(st)
        self.assertEqual(audit["unregistered"], [])

    def test_infeasible_reason_and_tabu(self):
        # the controller may not pick an option the plant cannot build: it is never in the menu
        mod = holeless_module(self.cat, "G03")
        _, status, _, st, results = cradle_run(self.root, "G03", {mod: {"quantity": 1, "exposed": "yes"}},
                                               tag="_opts")
        opts = {o["name"]: o for o in bb.retention_options(st)}
        self.assertTrue(opts["crush_ribs"]["feasible"])
        self.assertFalse(opts["snap_clips"]["feasible"])
        self.assertIn("keepout", opts["snap_clips"]["reason"])    # the part's own keep-outs cover the hook strips
        menus = [m["value"] for s in st.trajectory["steps"][1:] for m in s["menu"]]
        self.assertNotIn("snap_clips", menus)

    def test_package_verified_on_stls(self):
        # the whole tree with OpenSCAD: the cradle sensors run on the delivered STLs too (assembly_checks.EXTRA_CHECKS)
        mod = holeless_module(self.cat, "G03")
        r = gen_request("G03")
        root = self.root / "pkg"
        root.mkdir()
        l1 = root / "l1.json"
        l1.write_text(json.dumps(r["l1"]))
        llm = FakeLLM({"assy_spec": [all_none], "assy_contents": [contents_reply({mod: {"quantity": 1,
                                                                                         "exposed": "yes"}})]})
        args = ["--mode", "assembly", "--auto", "--l1", str(l1)]
        for p in BOTH:
            args += ["--parts", str(p)]
        args += ["--rules", str(test_rules(root, fn=24)), "--out", str(root / "out"), r["request"]]
        with mock.patch.object(ca, "OllamaAgent", lambda *a, **k: llm), mock.patch("builtins.print"):
            rc = ca.main(args)
        self.assertEqual(rc, 3)   # R12 review fix N5: all pass, L1s unlinked -> unverified
        pkg = sorted((root / "out").glob("*/"))[-1]
        for f in ("base.stl", "lid.stl", "layout.json", "controller_trace.json"):
            self.assertTrue((pkg / f).is_file(), f)
        checks = json.loads((pkg / "checks.json").read_text())
        text = json.dumps(checks)
        for cid in ("retention_board", "supported"):
            self.assertIn(cid, text)
        trace = json.loads((pkg / "controller_trace.json").read_text())
        self.assertEqual(trace["accepted"][0]["kind"], bb.SET_RETENTION)


class TestHoldingPrimaries(Case):
    def test_battery_primary_gets_a_cradle(self):
        # a non-board primary (a battery the text names: kind outside the old content kinds) rests in a cradle
        texts = gen_texts("G09")
        batt = next(pid for pid in self.cat.ids() if self.cat.get(pid).kind == "power"
                    and A.text_evidence(texts, self.cat.get(pid).names))
        _, status, _, st, results = cradle_run(self.root, "G09", {batt: {"quantity": 1}})
        self.assertEqual(status, ca.Status.SUCCESS, st.notes[-4:])
        self.assertEqual(A.primary_item(st)["part"], batt)
        self.assertEqual(st.choices["primary"]["interface"], pt.SEAT)
        self.assertTrue(results["supported"].passed)
        self.assertTrue(results["retention_board"].passed)

    def test_holeless_primary_without_a_top_plane_stops_typed(self):
        texts = gen_texts("G09")
        jack = next(pid for pid in self.cat.ids() if self.cat.get(pid).kind == "connector"
                    and A.text_evidence(texts, self.cat.get(pid).names))
        _, status, _, st, _ = cradle_run(self.root, "G09", {jack: {"quantity": 1, "exposed": "yes"}}, tag="_jack")
        self.assertEqual(status, ca.Status.FAILURE)
        self.assertTrue(any("no seat/top plane pair" in n for n in st.notes), st.notes[-3:])


class TestUnsizedAndScrewFallback(Case):
    def test_unsizable_part_is_rejected_and_reported(self):
        # iteration 005 G01: the 9B put in a request-sized generic part whose size the text does not state; until R11
        # the run stopped at Contents. Now that part is rejected (as an infeasible action is) and reported by its
        # failing content_placed check, and the rest of the design goes on
        texts = gen_texts("G01")
        board = next(pid for pid in self.cat.ids() if pt.mount_interface(self.cat.get(pid)) is not None
                     and A.text_evidence(texts, self.cat.get(pid).names))
        st0 = A.AssemblyState()
        st0.catalog, st0.rules, st0.texts = self.cat, self.rules, texts
        ranked = [pid for pid, _ in self.cat.lookup(dict(texts)["request"], k=len(self.cat.parts))]
        sized = next(pid for pid in ranked if self.cat.get(pid).kind == "generic"
                     and self.cat.get(pid).request_params())          # the generic part Contents offers first
        llm, status, _, st, results = cradle_run(self.root, "G01", {board: {"quantity": 1, "exposed": "yes"},
                                                                     sized: {"quantity": 1}}, tag="_unsized")
        if not any(c[0] == "assy_contents" and f"- {sized}:" in c[1] for c in llm.calls):
            self.skipTest(f"{sized} is not a Contents candidate for G01")
        self.assertEqual(status, ca.Status.SUCCESS, st.notes[-4:])
        self.assertNotIn(sized, [c["part"] for c in st.contents])
        u = next(x for x in st.unplaced if x["part"] == sized)
        r = results[f"content_placed_{u['id']}"]
        self.assertFalse(r.passed)
        self.assertIn("no number in the text", r.evidence["detail"])

    def test_no_screw_fits_the_holes_cradle_instead(self):
        # a mount_holes primary whose holes no catalogue screw passes (iteration 005 G14: arrange_contents stop) is held
        # by the cradle on its mount seat plane; the decision is the guardrail's
        texts = gen_texts("G14")
        board = next(pid for pid in self.cat.ids() if pt.mount_interface(self.cat.get(pid)) is not None
                     and A.text_evidence(texts, self.cat.get(pid).names))
        _, status, _, st, results = cradle_run(self.root, "G14", {board: {"quantity": 1, "exposed": "yes"}},
                                               tag="_noscrew")
        self.assertEqual(status, ca.Status.SUCCESS, st.notes[-4:])
        self.assertEqual(st.choices["support[board]"]["by"], "rule:no_screw_fits")
        self.assertNotIn("fastener[board]", st.choices)
        self.assertIsNone(A.primary_mount(st)[0])
        self.assertTrue(results["supported"].passed)
        self.assertTrue(results["retention_board"].passed)       # the controller (first option) chose crush ribs
        self.assertFalse([n for n in st.graph if n.role == "standoff"])


class TestSnapClips(Case):
    """A plain block part (no keep-outs) whose top-face edges are free: the snap option is buildable."""

    def block_state(self, height: float):
        root = Path(tempfile.mkdtemp(dir=self.root))
        part = {"id": "test_block", "schema": 1, "units": "mm", "names": ["test block"], "kind": "generic",
                "source": "unit test", "frame": "origin at the min corner, base on Z = 0",
                "params": {"sx": {"default": 30.0, "source": "test"}, "sy": {"default": 20.0, "source": "test"},
                           "sz": {"default": height, "source": "test"}},
                "datasheet_size": ["sx", "sy", "sz"], "size_tolerance": 0.1,
                "geometry": [{"id": "body", "primitive": "box", "size": ["sx", "sy", "sz"], "at": [0, 0, 0]}],
                "datums": {"BOTTOM": {"kind": "plane", "at": [0, 0, 0], "normal": [0, 0, -1]},
                           "TOP": {"kind": "plane", "at": [0, 0, "sz"], "normal": [0, 0, 1]}},
                "connectors": []}
        (root / "test_block").mkdir()
        (root / "test_block" / "part.json").write_text(json.dumps(part))
        cat = pt.Catalog.load([root])
        st = A.AssemblyState()
        st.catalog, st.rules = cat, self.rules
        st.spec = {"keepout_below": self.rules.values["solder_side_default"], "board_clearance":
                   self.rules.values["board_to_wall"]}
        inst = cat.instantiate("test_block", {})
        st.placed = lay.Layout(placed=[lay.Placed(A.PRIMARY, "test_block", {}, 0.0, 0.0, 0.0, 0.0, "", role="board",
                                                  inst=inst)])
        st.contents = [{"id": A.PRIMARY, "part": "test_block", "quantity": 1}]
        return st

    def test_snap_clips_are_sized_and_measured(self):
        st = self.block_state(15.0)
        plan = bb.cradle_plan(st, "snap_clips")
        self.assertIsNone(plan.infeasible)
        self.assertEqual(len(plan.clips), 2)
        self.assertEqual({c["side"] for c in plan.clips}, {"-Y", "+Y"})     # the long sides first
        r = st.rules.values
        for c in plan.clips:
            self.assertLessEqual(c["strain"], r["snap_strain_max"])
            want = 1.5 * r["snap_arm_thickness"] * (r["sliding_fit"] + r["snap_overlap"]) / c["free_length"] ** 2
            self.assertAlmostEqual(c["strain"], want)
        hooks = [f for f in plan.features if f.role == "snap_hook"]
        self.assertEqual(len(hooks), 2)
        for h in hooks:
            self.assertAlmostEqual(h.z0, plan.top_z + r["snap_gap"])
        self.assertAlmostEqual(plan.held["+z"], r["snap_gap"])
        # the rim beside each arm is cut so the arm can flex
        for c in plan.clips:
            arm = next(f for f in plan.features if f.id == c["id"])
            for f in plan.features:
                if f.role == "rim" and f.side == c["side"]:
                    self.assertTrue(f.x1 <= arm.x0 - r["snap_slot"] + 1e-9 or f.x0 >= arm.x1 + r["snap_slot"] - 1e-9)

    def test_short_arm_is_infeasible_by_strain(self):
        st = self.block_state(1.0)
        plan = bb.cradle_plan(st, "snap_clips")
        self.assertIsNotNone(plan.infeasible)
        self.assertIn("strain", plan.infeasible)
        self.assertIsNone(bb.cradle_plan(st, "crush_ribs").infeasible)

    def test_controller_chooses_snap_clips_end_to_end(self):
        # a design whose primary is the plain block: the menu offers both buildable options; the controller picks snap
        # clips, the plant derives arms and hooks, and every cradle sensor passes on the solids
        root = Path(tempfile.mkdtemp(dir=self.root))
        self.block_state(15.0)                       # writes nothing global; the part file is rebuilt here
        part_dir = root / "parts" / "test_block"
        part_dir.mkdir(parents=True)
        src = next(Path(self.root).glob("*/test_block/part.json"))
        (part_dir / "part.json").write_text(src.read_text())
        text = "A box that holds one test block, with a lid."
        d = design_for(text, [], root / "d", [root / "parts", PARTS], test_rules(root, fn=24))
        llm = FakeLLM({"assy_spec": [all_none], "assy_contents": [contents_reply({"test_block": {"quantity": 1}})],
                       C.CONTROL_LABEL: [{"action": f"{bb.SET_RETENTION}:{A.PRIMARY}=snap_clips"}]})   # R02 merge (R11): an id, was "B"
        status, child, st, results = staged_to_derive(d, llm)
        self.assertEqual(status, ca.Status.SUCCESS, st.notes[-4:])
        menu = [(m["kind"], m["value"]) for m in st.trajectory["steps"][1]["menu"]]
        self.assertEqual(menu, [(bb.SET_RETENTION, "crush_ribs"), (bb.SET_RETENTION, "snap_clips"), (C.STOP, None)])
        self.assertEqual(st.choices["retention[board]"]["value"], "snap_clips")
        self.assertEqual(len([n for n in st.graph if n.role == "snap_hook"]), 2)
        for k in [k for k in results if k.startswith(("snap_strain_", "snap_overlap_"))] + ["retention_board",
                                                                                             "supported"]:
            self.assertTrue(results[k].passed, (k, results[k].evidence))
        self.assertEqual(len([k for k in results if k.startswith("snap_strain_")]), 2)
        self.assertEqual([k for k, v in results.items() if not v.passed], [])

    def test_value_sensors(self):
        tol = ac.Tol.from_rules(self.rules.values)
        plan = ac.Plan(tol=tol)
        f = bb.EXTRA_CHECKS["snap_strain"]
        self.assertTrue(f("s", "snap_strain", {"value": 0.01, "limit": 0.02}, {}, plan).passed)
        self.assertFalse(f("s", "snap_strain", {"value": 0.021, "limit": 0.02}, {}, plan).passed)   # exact (a ratio)
        g = bb.EXTRA_CHECKS["rib_interference"]          # measured: overlap volume / rib face area, along X here
        part = ac.m3d.Manifold.cube([10.0, 10.0, 2.0])
        for reach, ok in ((0.1, True), (0.4, False), (-0.2, False)):
            plan.volumes["rib"] = ac.m3d.Manifold.cube([1.0, 1.0, 2.0]).translate([reach - 1.0, 4.0, 0.0])
            plan.volumes["part"] = part
            r = g("r", "rib_interference", {"rib": "rib", "part_volume": "part", "axis": 0, "lo": 0.05, "hi": 0.3,
                                            "designed": 0.1}, {}, plan)
            self.assertEqual(r.passed, ok, (reach, r.evidence))
            self.assertAlmostEqual(r.evidence["value"], max(0.0, reach), places=4)
        self.assertIs(ac.EXTRA_CHECKS["retention"], bb.EXTRA_CHECKS["retention"])
        # review fix 3: every block check says how it knows (design checks vs measured sensors)
        self.assertEqual(f("s", "snap_strain", {"value": 0.01, "limit": 0.02}, {}, plan).evidence["basis"], bb.DESIGN)
        for typ in ("retention", "snap_overlap", "panel_thickness"):
            res = bb.EXTRA_CHECKS[typ]("v", typ, {"value": 0.1, "limit": 0.2}, {}, plan)
            self.assertEqual(res.evidence["basis"], bb.DESIGN, typ)
        self.assertEqual(r.evidence["basis"], bb.MEASURED)

    def test_panel_hole_is_measured_on_the_lid(self):
        # review fix 3: panel_hole reads the built lid, so a hole that is missing, too small or too big fails even when
        # the designed diameter is right (it could not fail before: it compared the designed diameter with itself)
        tol = ac.Tol.from_rules(self.rules.values)
        plan = ac.Plan(tol=tol, seg=64)
        r = self.rules.values
        through, lid_z, z0 = 6.0, 2.0, 10.0
        args = {"body": "lid", "xy": [0.0, 0.0], "z": z0 + lid_z / 2, "z0": z0, "z1": z0 + lid_z,
                "through_d": through, "window": through / 2 + 2.0, "lo": r["sliding_fit_min"],
                "hi": r["sliding_fit_max"], "designed": r["sliding_fit"]}
        plate = ac.m3d.Manifold.cube([40.0, 40.0, lid_z]).translate([-20.0, -20.0, z0])
        check = bb.EXTRA_CHECKS["panel_hole"]

        def with_hole(d):
            return plate - ac.m3d.Manifold.cylinder(lid_z + 2, d / 2, d / 2, 256).translate([0.0, 0.0, z0 - 1])

        good = check("h", "panel_hole", args, {"lid": with_hole(through + 2 * r["sliding_fit"])}, plan)
        self.assertTrue(good.passed, good.evidence)
        self.assertAlmostEqual(good.evidence["value"], r["sliding_fit"], delta=tol.measure)
        self.assertEqual(good.evidence["basis"], bb.MEASURED)
        tight = check("h", "panel_hole", args, {"lid": with_hole(through + 2 * 0.05)}, plan)
        self.assertFalse(tight.passed)
        loose = check("h", "panel_hole", args, {"lid": with_hole(through + 2 * 0.8)}, plan)
        self.assertFalse(loose.passed)
        none = check("h", "panel_hole", args, {"lid": plate}, plan)
        self.assertFalse(none.passed)
        self.assertLess(none.evidence["value"], 0.0)
        self.assertIn("no hole", none.evidence["detail"])
        empty = check("h", "panel_hole", args, {"lid": plate - ac.m3d.Manifold.cube([30.0, 30.0, 6.0]).translate(
            [-15.0, -15.0, z0 - 2])}, plan)
        self.assertFalse(empty.passed)                                   # no lid round the axis: the hole is too big


class TestPanelMount(Case):
    """A content part whose catalogue mount.type is panel (a lens or a threaded bushing through a panel)."""

    def panel_part(self, gid: str) -> str:
        texts = gen_texts(gid)
        return next(pid for pid in self.cat.ids() if bb.is_panel_part(self.cat.get(pid))
                    and A.text_evidence(texts, self.cat.get(pid).names))

    def test_panel_geometry_from_primitives(self):
        for pid in self.cat.ids():
            if not bb.is_panel_part(self.cat.get(pid)):
                continue
            inst = self.cat.instantiate(pid, {})
            g = bb.panel_geometry(inst)
            self.assertIsNotNone(g, pid)
            boxes = [p.bbox() for p in inst.geometry]
            body = max(boxes, key=lambda b: (b[1][0] - b[0][0]) * (b[1][1] - b[0][1]))
            self.assertAlmostEqual(g.contact_z, body[1][2])          # the widest primitive stops against the panel
            through = [b for b in boxes if b[1][2] > g.contact_z + 1e-6 and b is not body]
            self.assertTrue(through)
            self.assertLess(g.through_d, min(body[1][0] - body[0][0], body[1][1] - body[0][1]) + 1e-9)

    def test_controller_mounts_panel_parts_in_the_lid(self):
        # G12: a holeless board and LEDs that shine through the lid. The proposal leaves the LEDs unplaced (a failing
        # content_placed check); the controller holds the board with ribs and mounts the LEDs in the lid; every copy is
        # placed, its hole sized, its keep-outs (the lens's view) outside the lid, and every check passes
        mod = holeless_module(self.cat, "G12")
        led = self.panel_part("G12")
        _, status, _, st, results = cradle_run(self.root, "G12", {mod: {"quantity": 1, "exposed": "yes"},
                                                                   led: {"quantity": 3}})
        self.assertEqual(status, ca.Status.SUCCESS, st.notes[-4:])
        kinds = [s["action"]["kind"] for s in st.trajectory["steps"][1:]]
        self.assertIn(bb.SET_PANEL, kinds)
        item = next(u["id"] for u in st.unplaced if u["part"] == led)
        self.assertEqual(st.choices[f"panel[{item}]"]["by"], C.CONTROLLER_BY)
        refs = bb.panel_refs(st)
        self.assertEqual(len(refs), 3)
        self.assertFalse(any(k.startswith("content_placed_") for k in results))
        for n in refs:
            for pre in ("panel_keepouts_", "panel_clear_", "panel_board_", "panel_seated_", "panel_hole_"):
                self.assertIn(pre + n.id, results)
                self.assertTrue(results[pre + n.id].passed, (pre + n.id, results[pre + n.id].evidence))
            self.assertIn(f"{n.id}_panel_hole", st.graph.nodes)
            self.assertEqual(st.graph.nodes[f"{n.id}_panel_hole"].body, "lid")
        self.assertEqual([k for k, v in results.items() if not v.passed], [])
        xy = sorted((round(st.resolved.poses[n.id][0, 3], 3), round(st.resolved.poses[n.id][1, 3], 3)) for n in refs)
        self.assertEqual(len(set(xy)), 3)                         # three distinct positions

    def test_threaded_bushing_part_and_its_panel_limits(self):
        # a bushing part (it declares a max panel thickness and a nut zone): placed in the lid, the lid's thickness is
        # measured against the part's limit and its nut zone stays outside the lid
        texts = gen_texts("G10")
        enc = next(pid for pid in self.cat.ids() if bb.is_panel_part(self.cat.get(pid))
                   and A.text_evidence(texts, self.cat.get(pid).names)
                   and (self.cat.get(pid).data.get("mount") or {}).get("max_panel_thickness"))
        board = next(pid for pid in self.cat.ids() if pt.mount_interface(self.cat.get(pid)) is not None
                     and self.cat.get(pid).kind == "module" and A.text_evidence(texts, self.cat.get(pid).names))
        _, status, _, st, results = cradle_run(self.root, "G10", {board: {"quantity": 1, "exposed": "yes"},
                                                                   enc: {"quantity": 1}}, tag="_enc")
        self.assertEqual(status, ca.Status.SUCCESS, st.notes[-4:])
        n = bb.panel_refs(st)[0]
        self.assertTrue(results[f"panel_thickness_{n.id}"].passed, results[f"panel_thickness_{n.id}"].evidence)
        spec = next(s for s in A.build_plan(st).specs if s["id"] == f"panel_keepouts_{n.id}")
        self.assertTrue(any(k.id in spec["text"] for k in self.cat.instantiate(enc, {}).keepouts))
        self.assertTrue(results[f"panel_keepouts_{n.id}"].passed, results[f"panel_keepouts_{n.id}"].evidence)
        # the lid's inner face rose so the hanging body clears the board's component keep-out
        g = bb.panel_geometry(self.cat.instantiate(enc, {}))
        split = st.resolved.params["base"]["split"]
        _, _, top = A.primary_mount(st)
        board_top = A.lay.world_datum(st.placed.get(A.PRIMARY), top).at[2]
        self.assertGreaterEqual(split - g.depth, board_top + st.spec["keepout_above"] - 1e-6)

    def test_no_panel_decision_leaves_plans_unchanged(self):
        st = A.AssemblyState()
        st.control = {}
        self.assertEqual(bb.cavity_z1_terms(st), [])


class TestRegistration(unittest.TestCase):
    def test_controller_knows_the_block_actions(self):
        self.assertIs(C.ACTUATORS["retention"], bb.retention_actions)
        self.assertIn("retention", C.DIRECTIONS)
        self.assertIn(bb.SET_RETENTION, bb.APPLIERS)
        reg = C.load_registry()
        for name in ("rule:default_retention", "rule:cradle"):
            self.assertEqual(reg[name]["class"], "plant")
            self.assertEqual(reg[name]["status"], "active")


if __name__ == "__main__":
    unittest.main()
