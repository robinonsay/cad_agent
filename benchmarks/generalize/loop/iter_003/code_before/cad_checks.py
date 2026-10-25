"""Typed checks: the sensors of the cascade controller.

Each L1 requirement the person writes ("the legs shall be at the corners of the
seat", "a phone shall rest on the stand without sliding off") is turned into
one or more typed checks. The LLM only ever fills in a check's typed slots
(type, part names, numbers); Python owns what a check *means*, measures it on
the design and renders it back into English. That keeps the 9B model out of
the business of judging geometry, which it does badly, and gives the
controller a signed, normalised error per requirement instead of a yes/no.

Two measurement layers:

* layer 1 reads the design model: shapes, parameters and the boxes that
  `cad_agent.layout` computes (counts, sizes, relations, edges, spans,
  arrangements);
* layer 2 builds real solids with manifold3d, constructed exactly like the
  OpenSCAD shape library builds them (same profiles, same $fn), and measures
  contact by growing one solid by a small epsilon (touches, connected,
  no_overlap, stable, fits, rests_on). A test compares these solids with
  OpenSCAD's own STL so the two cannot drift apart silently.

Every result carries `passed`, a signed `margin` (dimensionless; 0 is the
boundary, negative means violated, so margins of different checks can be
summed), the unit of the underlying measurement, which components and
parameters it depends on, and human-readable evidence (measured vs expected).

"Who checks the checks": a check must fail on an empty design and must kill at
least one Python-generated mutant of the design that touches what it depends
on (`non_vacuity`), every number in the L1 text must appear in one of its
checks (`number_coverage`), and the English rendering of each check is what
the LLM back-translates against the L1 (`backtranslation_prompt`).

On top of the sensors: a lexicographic error key with a strict monotone
comparator (`error_key`, `strictly_better`), a finite-difference sensitivity
matrix (`sensitivity`) for localisation and controllability, and a deadbeat
solver (`deadbeat`) that sets a single parameter directly when a dimension
check is invertible in it.

cad_agent may import this module, so this module never imports cad_agent at
import time: `_ca()` fetches it lazily (and reuses `__main__` when cad_agent
is being run as a script, so both sides share one set of classes).
"""

import copy
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    import manifold3d as m3d
except ImportError:  # layer-2 checks report themselves as unavailable instead of crashing
    m3d = None

if TYPE_CHECKING:  # pragma: no cover
    from cad_agent import Component, Design

Vec = Tuple[float, float, float]


def _ca():
    """cad_agent, imported lazily to avoid a circular import.

    When cad_agent.py runs as a script it lives in `__main__`; importing it again
    by name would create a second copy with different classes, so reuse it.
    """
    mod = sys.modules.get("cad_agent")
    if mod is not None:
        return mod
    main = sys.modules.get("__main__")
    if main is not None and getattr(main, "__file__", "").endswith("cad_agent.py"):
        return main
    import cad_agent
    return cad_agent


# ---------------------------------------------------------------------------
# Constants and the stand-in object library
# ---------------------------------------------------------------------------

DEFAULT_MU = 0.3          # PLA on PLA / a phone case on plastic, roughly
DENSITY = 1.24e-3         # g/mm^3, solid PLA
SETTLE_STEP = 1.0         # mm; coarse step when sliding a stand-in until it touches
SETTLE_TOL = 0.005        # mm; bisection tolerance for the resting position
CONTACT_GROW_2D = 0.25    # mm; stand-in growth used to find its contacts at rest
OVERLAP_VOLUME = 1.0      # mm^3; less than this is numerical noise, not interpenetration
CONNECT_AREA = 1.0        # mm^2; parts sharing less than this are not joined (as floating_components)
MU_MAX = 2.0              # friction beyond this is "no friction can hold it"
STABLE_TILT = 5.0         # deg; "stable" means a small nudge does not tip it: something balanced on a
                          # line (three legs in a row) passes a bare centre-of-mass test

# Stand-in objects the person's requirements refer to ("a phone shall rest on
# it"). Boxes give their three sizes (any order; orientation is chosen by the
# check), cylinders a diameter and a length. Masses are typical, for loads.
STANDINS: Dict[str, dict] = {
    "phone": {"kind": "box", "dims": [75.0, 150.0, 9.0], "mass_g": 190.0,
              "text": "a phone (75 x 150 x 9 mm)"},
    "tablet": {"kind": "box", "dims": [250.0, 170.0, 8.0], "mass_g": 480.0,
               "text": "a tablet (250 x 170 x 8 mm)"},
    "laptop": {"kind": "box", "dims": [360.0, 250.0, 20.0], "mass_g": 1500.0,
               "text": "a laptop (360 x 250 x 20 mm)"},
    "book": {"kind": "box", "dims": [160.0, 240.0, 30.0], "mass_g": 500.0,
             "text": "a book (160 x 240 x 30 mm)"},
    "pencil": {"kind": "cylinder", "diameter": 8.0, "length": 170.0, "mass_g": 6.0,
               "text": "a pencil (8 mm across, 170 mm long)"},
    "box": {"kind": "box", "dims": None, "mass_g": 100.0, "text": "a box"},
    "cylinder": {"kind": "cylinder", "diameter": None, "length": None, "mass_g": 50.0,
                 "text": "a round object"},
}


def standin(name: str, size: Optional[Sequence[float]] = None) -> dict:
    """The stand-in's spec, with `size` overriding (box: 3 sizes; cylinder: [diameter, length])."""
    if name not in STANDINS:
        raise ValueError(f"unknown stand-in object {name!r}; known: {', '.join(STANDINS)}")
    spec = dict(STANDINS[name])
    if size:
        if spec["kind"] == "box":
            if len(size) != 3:
                raise ValueError("a box stand-in needs three sizes")
            spec["dims"] = [float(v) for v in size]
            spec["text"] = f"{'a ' + name if name != 'box' else 'a box'} ({' x '.join(_fmt(v) for v in size)} mm)"
        else:
            if len(size) != 2:
                raise ValueError("a cylinder stand-in needs [diameter, length]")
            spec["diameter"], spec["length"] = float(size[0]), float(size[1])
            spec["text"] = f"a round {name} ({_fmt(size[0])} mm across, {_fmt(size[1])} mm long)"
    if spec["kind"] == "box" and not spec["dims"]:
        raise ValueError(f"stand-in {name!r} needs a size")
    if spec["kind"] == "cylinder" and not (spec["diameter"] and spec["length"]):
        raise ValueError(f"stand-in {name!r} needs a size [diameter, length]")
    return spec


def _fmt(v: float) -> str:
    v = round(float(v), 3)
    return str(int(v)) if v == int(v) else f"{v:g}"


# ---------------------------------------------------------------------------
# Check specs: typed slots the LLM fills; Python owns their meaning
# ---------------------------------------------------------------------------

# slot: (kind, required, default, choices). Kinds: "part" (a component name),
# "parts" (list of names or null = every part), "number", "int", "enum", "bool",
# "object" (a stand-in name), "numbers" (list), "dict".
MEASURES = ("width", "depth", "height", "length", "thickness", "diameter", "inner_diameter",
            "angle", "top", "bottom")
RELATIONS = ("on_top_of", "underneath", "in_front_of", "behind", "left_of", "right_of", "beside")
EDGE_PLACES = ("front", "back", "left", "right", "center")
PATTERNS = ("corners", "ends", "row", "triangle", "spread")
OPS = ("eq", "ge", "le")

SLOTS: Dict[str, Dict[str, tuple]] = {
    "count": {"part": ("part", False, None, ()), "shape": ("enum", False, None, ()),
              "count": ("int", True, None, ()), "op": ("enum", False, "eq", OPS)},
    "dimension": {"part": ("part", False, None, ()), "measure": ("enum", True, None, MEASURES),
                  "param": ("str", False, None, ()), "value": ("number", True, None, ()),
                  "tol": ("number", False, None, ()), "op": ("enum", False, "eq", OPS)},
    "shape": {"part": ("part", True, None, ()), "shape": ("enum", True, None, ()),
              "orient": ("enum", False, None, ("flat", "upright", "x", "y", "z"))},
    "relation": {"part": ("part", True, None, ()), "relation": ("enum", True, None, RELATIONS),
                 "other": ("part", True, None, ()), "touching": ("bool", False, True, ()),
                 "tol": ("number", False, 0.5, ())},
    "edge": {"part": ("part", True, None, ()), "other": ("part", True, None, ()),
             "where": ("enum", True, None, EDGE_PLACES), "axis": ("enum", False, None, ("x", "y", "xy")),
             "max_offset": ("number", False, None, ())},
    "span": {"part": ("part", True, None, ()), "other": ("part", True, None, ()),
             "axis": ("enum", True, None, ("x", "y", "z")), "tol": ("number", False, 0.5, ())},
    "arrangement": {"part": ("part", True, None, ()), "pattern": ("enum", True, None, PATTERNS),
                    "other": ("part", False, None, ()), "axis": ("enum", False, None, ("x", "y", "z"))},
    "touches": {"part": ("part", True, None, ()), "other": ("part", True, None, ()),
                "min_area": ("number", False, None, ())},
    "connected": {"parts": ("parts", False, None, ())},
    "no_overlap": {"parts": ("parts", False, None, ()), "max_volume": ("number", False, OVERLAP_VOLUME, ())},
    "stable": {"load": ("dict", False, None, ()), "tilt_deg": ("number", False, STABLE_TILT, ()),
               "density": ("number", False, DENSITY, ())},
    "fits": {"object": ("object", True, None, ()), "size": ("numbers", False, None, ()),
             "into": ("parts", True, None, ()), "between": ("bool", False, False, ()),
             "orientation": ("enum", False, None, ("upright", "edge", "flat")),
             "clearance": ("number", False, 1.0, ()), "min_depth": ("number", False, None, ())},
    "rests_on": {"object": ("object", True, None, ()), "size": ("numbers", False, None, ()),
                 "support": ("part", True, None, ()), "mode": ("enum", False, "lean", ("lean", "lie")),
                 "also_touches": ("parts", False, None, ()), "mu": ("number", False, DEFAULT_MU, ()),
                 "orientation": ("enum", False, None, ("portrait", "landscape")),
                 "angle": ("number", False, None, ()),
                 "facing": ("enum", False, None, ("front", "back", "left", "right")),
                 "tilt_deg": ("number", False, STABLE_TILT, ())},
}
LAYER2 = {"touches", "connected", "no_overlap", "stable", "fits", "rests_on"}


@dataclass
class Check:
    """One typed check, JSON-serialisable. `text` is Python's English rendering (never the LLM's)."""
    id: str
    l1_id: str
    type: str
    params: Dict[str, Any] = field(default_factory=dict)
    text: str = ""
    hard: bool = True
    # 1 = verifies the requirement itself; 2 = design-guidance sub-check the cascade's
    # outer loop may add (when the L1 check fails although its sub-checks pass) or drop
    # (when they over-constrain an L1 that already passes).
    level: int = 1

    def __post_init__(self):
        if self.type in SLOTS:
            for slot, (_, _, default, _) in SLOTS[self.type].items():
                self.params.setdefault(slot, default)
        if not self.text and not validate_check(self):
            self.text = render_check(self)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Check":
        return Check(id=str(data["id"]), l1_id=str(data.get("l1_id", "")), type=data["type"],
                     params=dict(data.get("params") or {}), text=data.get("text", ""),
                     hard=bool(data.get("hard", True)), level=int(data.get("level", 1)))


@dataclass
class CheckResult:
    check_id: str
    l1_id: str
    type: str
    passed: bool
    margin: float                        # dimensionless; 0 = boundary, negative = violated
    unit: str                            # unit of the underlying measurement ("mm", "deg", "count", ...)
    depends_on: Dict[str, List[str]]     # {"components": [...], "params": ["comp.param", ...]}
    evidence: Dict[str, Any]             # {"measured": ..., "expected": ..., "detail": "..."}
    layer: int = 1
    hard: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def validate_check(chk: Check) -> List[str]:
    """Errors in a check's typed slots (what a template-filling LLM answer is checked against)."""
    if chk.type not in SLOTS:
        return [f"unknown check type {chk.type!r}; known: {', '.join(SLOTS)}"]
    errors = []
    shapes = tuple(_ca().SHAPES) + ("round", "any")
    for slot, (kind, required, _, choices) in SLOTS[chk.type].items():
        v = chk.params.get(slot)
        if v is None:
            if required:
                errors.append(f"{slot} is required")
            continue
        if slot == "shape":
            choices = shapes
        if kind == "enum" and choices and v not in choices:
            errors.append(f"{slot} must be one of {', '.join(choices)}")
        elif kind in ("number",) and not isinstance(v, (int, float)):
            errors.append(f"{slot} must be a number")
        elif kind == "int" and not (isinstance(v, int) and v >= 0):
            errors.append(f"{slot} must be a whole number")
        elif kind in ("part", "str") and not isinstance(v, str):
            errors.append(f"{slot} must be a name")
        elif kind == "parts" and not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
            errors.append(f"{slot} must be a list of part names")
        elif kind == "object" and v not in STANDINS:
            errors.append(f"{slot} must be one of {', '.join(STANDINS)}")
        elif kind == "numbers" and not (isinstance(v, list) and all(isinstance(x, (int, float)) for x in v)):
            errors.append(f"{slot} must be a list of numbers")
        elif kind == "bool" and not isinstance(v, bool):
            errors.append(f"{slot} must be true or false")
        elif kind == "dict" and not isinstance(v, dict):
            errors.append(f"{slot} must be an object")
    if chk.type in ("fits", "rests_on") and not errors:
        try:
            standin(chk.params["object"], chk.params.get("size"))
        except ValueError as exc:
            errors.append(str(exc))
    if chk.type == "dimension" and chk.params.get("measure") in ("diameter", "inner_diameter", "angle") \
            and not chk.params.get("part"):
        errors.append(f"measure {chk.params['measure']} needs a part")
    if chk.type == "dimension" and chk.params.get("measure") not in ("top", "bottom", "angle") \
            and isinstance(chk.params.get("value"), (int, float)) and chk.params["value"] <= 0 \
            and (chk.params.get("op") or "eq") != "le":
        # "rising from 0 mm at the front" once became "height = 0", which no solid can pass
        errors.append(f"a {chk.params['measure']} of {_fmt(chk.params['value'])} mm cannot be built; "
                      "for a slope, test the larger size or the angle")
    return errors


def check_schema(check_type: str, part_names: Optional[Sequence[str]] = None) -> dict:
    """JSON schema for one check type's slots, for schema-constrained template filling."""
    props, required = {}, []
    for slot, (kind, req, _, choices) in SLOTS[check_type].items():
        if slot == "shape":
            choices = tuple(_ca().SHAPES) + ("round", "any")
        if kind == "part":
            s = {"type": "string"}
            if part_names:
                s["enum"] = list(part_names)
        elif kind == "parts":
            s = {"type": "array", "items": {"type": "string", **({"enum": list(part_names)} if part_names else {})}}
        elif kind == "enum":
            s = {"type": "string", "enum": list(choices)}
        elif kind == "number":
            s = {"type": "number"}
        elif kind == "int":
            s = {"type": "integer"}
        elif kind == "bool":
            s = {"type": "boolean"}
        elif kind == "object":
            s = {"type": "string", "enum": list(STANDINS)}
        elif kind == "numbers":
            s = {"type": "array", "items": {"type": "number"}}
        elif kind == "dict":
            s = {"type": "object"}
        else:
            s = {"type": "string"}
        props[slot] = s
        if req:
            required.append(slot)
    return {"type": "object", "properties": props, "required": required}


# ----- English rendering (for back-translation and the verification matrix) -----

SHAPE_WORDS = {"box": "a rectangular block", "panel": "a flat slab tilted at an angle",
               "wedge": "a triangular wedge", "cylinder": "a solid round rod or disc",
               "tube": "a hollow round tube", "sphere": "a ball", "round": "a round part",
               "any": "a part"}
RELATION_WORDS = {"on_top_of": "sits on top of", "underneath": "is underneath",
                  "in_front_of": "is in front of", "behind": "is behind", "left_of": "is to the left of",
                  "right_of": "is to the right of", "beside": "is beside"}
MEASURE_WORDS = {"width": "width (left to right)", "depth": "depth (front to back)",
                 "height": "height", "length": "longest size", "thickness": "thickness",
                 "diameter": "diameter", "inner_diameter": "inner (hole) diameter",
                 "angle": "tilt angle from the horizontal", "top": "top surface height above the table",
                 "bottom": "bottom surface height above the table"}
OP_WORDS = {"eq": "", "ge": "at least ", "le": "at most "}
AXIS_SPAN = {"x": "full width (left to right)", "y": "full depth (front to back)", "z": "full height"}


def _the(name: Optional[str]) -> str:
    return f"the {name.replace('_', ' ')}" if name else "the whole object"


def render_check(chk: Check) -> str:
    """Python's plain-English statement of what a check tests."""
    p, t = chk.params, chk.type
    if t == "count":
        what = f"{p['part'].replace('_', ' ')} parts" if p.get("part") else "parts"
        if p.get("shape"):
            what = f"{what} shaped as {SHAPE_WORDS.get(p['shape'], p['shape'])}"
        exact = {"eq": "exactly ", "ge": "at least ", "le": "at most "}[p.get("op") or "eq"]
        return f"The design has {exact}{p['count']} {what}."
    if t == "dimension":
        unit = "degrees" if p["measure"] == "angle" else "mm"
        what = f"parameter {p['param']}" if p.get("param") else MEASURE_WORDS[p["measure"]]
        tol = f" (within {_fmt(_dim_tol(p))} {unit})" if (p.get("op") or "eq") == "eq" else ""
        return f"{_the(p.get('part')).capitalize()}'s {what} is {OP_WORDS[p.get('op') or 'eq']}{_fmt(p['value'])} {unit}{tol}."
    if t == "shape":
        # x / y / z mean "axis along" for round parts and "longest side along" for the rest;
        # "z" used to read "standing upright", which a wide upright wall then failed.
        if p["shape"] in ("cylinder", "tube", "round"):
            along = {"x": ", with its axis left to right", "y": ", with its axis front to back",
                     "z": ", with its axis vertical"}
        else:
            along = {"x": ", with its longest side left to right", "y": ", with its longest side front to back",
                     "z": ", with its longest side vertical"}
        orient = dict(along, flat=", lying flat (its thinnest side vertical)",
                      upright=", standing upright (not lying flat)").get(p.get("orient") or "", "")
        return f"{_the(p['part']).capitalize()} is {SHAPE_WORDS.get(p['shape'], p['shape'])}{orient}."
    if t == "relation":
        touch = ", touching it" if p.get("touching", True) else ""
        return f"{_the(p['part']).capitalize()} {RELATION_WORDS[p['relation']]} {_the(p['other'])}{touch}."
    if t == "edge":
        if p["where"] == "center":
            axis = {"x": "left to right", "y": "front to back"}.get(p.get("axis") or "", "left to right and front to back")
            return f"{_the(p['part']).capitalize()} is centred on {_the(p['other'])}, {axis}."
        return f"{_the(p['part']).capitalize()} is along the {p['where']} edge of {_the(p['other'])}."
    if t == "span":
        return f"{_the(p['part']).capitalize()} runs the {AXIS_SPAN[p['axis']]} of {_the(p['other'])}."
    if t == "arrangement":
        on = _the(p.get("other")) if p.get("other") else "the part they are fixed to"
        axis = {"x": "left to right", "y": "front to back", "z": "bottom to top"}.get(
            p.get("axis") or "", "left to right or front to back")
        words = {"corners": f"one near each corner of {on}",
                 "ends": f"one at each end of {on}{', ' + axis if axis else ''}",
                 "row": f"in an evenly spaced straight row{', ' + axis if axis else ''}",
                 "triangle": f"in a triangle spread out under {on}",
                 "spread": f"spread out over {on}, not in a line"}[p["pattern"]]
        return f"The {p['part'].replace('_', ' ')} parts are placed {words}."
    if t == "touches":
        area = p.get("min_area") or _ca().MIN_CONTACT_AREA
        return f"{_the(p['part']).capitalize()} touches {_the(p['other'])} with at least {_fmt(area)} mm² of contact."
    if t == "connected":
        which = ", ".join(x.replace("_", " ") for x in p["parts"]) if p.get("parts") else "all parts"
        return f"{which[0].upper() + which[1:]} form one connected body."
    if t == "no_overlap":
        which = " among " + ", ".join(x.replace("_", " ") for x in p["parts"]) if p.get("parts") else ""
        return f"No two parts{which} pass through each other."
    if t == "stable":
        text = "The object stands on its own on a flat table without tipping over"
        load = p.get("load") or {}
        if load:
            where = f"the {load.get('face', 'top')} of {_the(load['part'])}" if load.get("part") else \
                f"the point {load.get('point')}"
            text += f", even with a {_fmt(load.get('mass_g', 0))} g load on {where}"
        if p.get("tilt_deg"):
            text += f", even when the table is tilted {_fmt(p['tilt_deg'])} degrees"
        return text + "."
    if t == "fits":
        obj = standin(p["object"], p.get("size"))["text"]
        into = " and ".join(_the(x) for x in p["into"])
        where = f"between {into}" if p.get("between") else f"into {into}"
        orient = {"upright": "standing upright", "edge": "standing on its edge", "flat": "lying flat"}[
            p.get("orientation") or ("edge" if p.get("between") else "upright")]
        depth = f", going at least {_fmt(p['min_depth'])} mm deep" if p.get("min_depth") else ""
        return (f"{obj[0].upper() + obj[1:]}, {orient}, fits {where} with "
                f"{_fmt(p.get('clearance', 1.0))} mm clearance all round{depth}.")
    if t == "rests_on":
        obj = standin(p["object"], p.get("size"))["text"]
        how = (f"leaning against the {p.get('facing') or 'front'} of {_the(p['support'])}"
               if (p.get("mode") or "lean") == "lean" else f"lying on {_the(p['support'])}")
        orient = f" in {p['orientation']} orientation" if p.get("orientation") else ""
        also = (", also touching " + " and ".join(_the(x) for x in p["also_touches"])) if p.get("also_touches") else ""
        return (f"{obj[0].upper() + obj[1:]}{orient}, {how}{also}, stays at rest without "
                f"sliding or tipping over (friction coefficient {_fmt(p.get('mu', DEFAULT_MU))}).")
    return f"{t} check"


def backtranslation_prompt(chk: Check, l1_text: str) -> str:
    """The yes/no question asked of the LLM: does this (Python-rendered) check test the requirement?

    Wording measured on the 9B model (10 labelled pairs): asking whether the test
    checks "what the requirement asks for, and nothing that contradicts it" made it
    reject correct partial tests (P(yes) 0.35-0.47 for "the base is 150 mm wide"
    against "150 x 60 x 6 mm"); framing each test as one piece of the requirement
    accepted every correct test (P(yes) >= 0.69) and still rejected wrong parts and
    directions. It does NOT catch a stated number on the wrong axis - that is left
    to Python (number provenance and coverage).
    """
    return ("A requirement is usually checked by several small tests, each covering one piece of it.\n\n"
            f"Requirement: {l1_text}\nOne test: {chk.text or render_check(chk)}\n\n"
            "Is this test about something the requirement talks about (the same part and the same kind of "
            "property, place or behaviour), with no number or direction that disagrees with the requirement?")


# ---------------------------------------------------------------------------
# Scene: the design's instances, with layer-1 boxes and lazily built layer-2 solids
# ---------------------------------------------------------------------------


def _tokens(name: str) -> List[str]:
    toks = [t for t in re.split(r"[^a-z0-9]+", str(name).lower()) if t]
    return [t[:-1] if len(t) > 3 and t.endswith("s") and not t.endswith("ss") else t for t in toks]


def select(d: "Design", selector: Optional[str], laid_out: bool = True) -> List["Component"]:
    """Components a check's part name refers to.

    Exact name first, then the slug, then every component whose name contains
    all the selector's words ("wall" -> front_wall and back_wall; "legs" -> leg).
    Binding role names to components is the cascade's job; this fallback just
    keeps a plural or a qualifier from making a check vacuous.
    """
    comps = [c for c in d.components if (c.positions and c.size) or not laid_out]
    if selector is None:
        return comps
    exact = [c for c in comps if c.name == selector]
    if exact:
        return exact
    slug = _ca().slugify(selector)
    exact = [c for c in comps if c.name == slug]
    if exact:
        return exact
    want = set(_tokens(selector))
    if not want:
        return []
    return [c for c in comps if want <= set(_tokens(c.name))]


@dataclass(eq=False)
class Inst:
    comp: "Component"
    k: int
    lo: Vec
    hi: Vec

    @property
    def label(self) -> str:
        return self.comp.name if self.comp.count == 1 else f"{self.comp.name}#{self.k}"

    @property
    def center(self) -> Vec:
        return tuple((a + b) / 2 for a, b in zip(self.lo, self.hi))

    @property
    def size(self) -> Vec:
        return tuple(b - a for a, b in zip(self.lo, self.hi))


def ensure_layout(d: "Design") -> None:
    """Lay the design out if some component's size or positions are missing."""
    if any(c.shape and c.params and (c.size is None or not c.positions) for c in d.components):
        _ca().layout(d)


class Scene:
    """One design's instances. Layer-2 solids and pairwise measurements are cached per scene."""

    def __init__(self, d: "Design"):
        ensure_layout(d)
        self.d = d
        self.insts: List[Inst] = []
        for c in d.components:
            if not (c.size and c.positions and c.shape and c.params):
                continue
            for k, p in enumerate(c.positions):
                self.insts.append(Inst(c, k, tuple(p), tuple(p[a] + c.size[a] for a in range(3))))
        self._solids: Dict[Tuple[int, float], Any] = {}
        self._pair: Dict[tuple, float] = {}
        self._union = None

    def of(self, comps: Iterable["Component"]) -> List[Inst]:
        ids = {id(c) for c in comps}
        return [i for i in self.insts if id(i.comp) in ids]

    def bbox(self, insts: Optional[Sequence[Inst]] = None) -> Optional[Tuple[Vec, Vec]]:
        insts = self.insts if insts is None else insts
        if not insts:
            return None
        lo = tuple(min(i.lo[a] for i in insts) for a in range(3))
        hi = tuple(max(i.hi[a] for i in insts) for a in range(3))
        return lo, hi

    # ----- layer 2 -----

    def solid(self, inst: Inst, grow: float = 0.0):
        key = (id(inst), grow)
        if key not in self._solids:
            self._solids[key] = component_solid(inst.comp, grow).translate(list(inst.lo))
        return self._solids[key]

    def union(self):
        if self._union is None:
            self._union = m3d.Manifold.batch_boolean([self.solid(i) for i in self.insts], m3d.OpType.Add) \
                if self.insts else m3d.Manifold()
        return self._union

    def contact(self, a: Inst, b: Inst) -> float:
        """Contact area (mm^2): b grown by GROW, intersected with a (as cad_agent.contact_area)."""
        g = _ca().GROW
        key = ("c", id(a), id(b))
        if key not in self._pair:
            if not _boxes_near(a, b, 2 * g):
                self._pair[key] = 0.0
            else:
                self._pair[key] = (self.solid(a) ^ self.solid(b, g)).volume() / g
        return self._pair[key]

    def overlap(self, a: Inst, b: Inst) -> float:
        key = ("o",) + tuple(sorted((id(a), id(b))))
        if key not in self._pair:
            if not _boxes_near(a, b, -1e-6):
                self._pair[key] = 0.0
            else:
                self._pair[key] = (self.solid(a) ^ self.solid(b)).volume()
        return self._pair[key]


def _boxes_near(a: Inst, b: Inst, gap: float) -> bool:
    return all(a.lo[x] <= b.hi[x] + gap and b.lo[x] <= a.hi[x] + gap for x in range(3))


# ----- solids built exactly like the OpenSCAD shape library -----


def _profile(points: Sequence[Tuple[float, float]]):
    pts = [tuple(map(float, p)) for p in points]
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))
    if area < 0:
        pts.reverse()
    return m3d.CrossSection([pts])


def _extrude(points, axis: str, length: float, grow: float):
    """cad_agent.extrude_profile in manifold3d: profile in YZ (axis x) or XZ (axis y)."""
    cs = _profile(points)
    if grow:
        cs = cs.offset(grow, m3d.JoinType.Miter, 2.0)
    solid = cs.extrude(length + 2 * grow).translate([0, 0, -grow])
    if axis == "x":   # (u, v, t) -> (t, u, v)
        mat = [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]]
    else:             # (u, v, t) -> (u, L - t, v)
        mat = [[1, 0, 0, 0], [0, 0, -1, length], [0, 1, 0, 0]]
    return solid.transform(np.array(mat, dtype=float))


def _round_along(axis: str, r: float, solid):
    """cad_agent._axis_place: a z-axis solid centred on the origin -> min corner at the origin."""
    if axis == "z":
        return solid.translate([r, r, 0])
    if axis == "x":
        return solid.rotate([0, 90, 0]).translate([0, r, r])
    return solid.rotate([-90, 0, 0]).translate([r, 0, r])


@lru_cache(maxsize=4096)
def _solid_cached(shape: str, params_json: str, flipped: bool, grow: float):
    ca = _ca()
    p = json.loads(params_json)
    seg = ca.SEGMENTS
    g = grow
    if shape == "box":
        body = m3d.Manifold.cube([p["width"] + 2 * g, p["depth"] + 2 * g, p["height"] + 2 * g]).translate([-g] * 3)
    elif shape == "panel":
        foot, run = ca._panel_geometry(p)
        h = p["height"]
        if p["lean"] in ("back", "right"):
            pts = [(0, 0), (foot, 0), (foot + run, h), (run, h)]
        else:
            pts = [(run, 0), (run + foot, 0), (foot, h), (0, h)]
        body = _extrude(pts, "x" if p["lean"] in ("back", "front") else "y", p["width"], g)
    elif shape == "wedge":
        w, dp, h = p["width"], p["depth"], p["height"]
        side = p["high_side"]
        if side in ("back", "front"):
            pts = [(0, 0), (dp, 0), (dp, h)] if side == "back" else [(0, 0), (dp, 0), (0, h)]
            body = _extrude(pts, "x", w, g)
        else:
            pts = [(0, 0), (w, 0), (w, h)] if side == "right" else [(0, 0), (w, 0), (0, h)]
            body = _extrude(pts, "y", dp, g)
        if flipped:
            body = body.mirror([0, 0, 1]).translate([0, 0, h])
    elif shape == "cylinder":
        r = p["diameter"] / 2
        body = _round_along(p["axis"], r, m3d.Manifold.cylinder(p["height"] + 2 * g, r + g, r + g, seg)
                            .translate([0, 0, -g]))
    elif shape == "tube":
        ro, ri, h = p["outer_diameter"] / 2, p["inner_diameter"] / 2, p["height"]
        body = m3d.Manifold.cylinder(h + 2 * g, ro + g, ro + g, seg).translate([0, 0, -g])
        if ri - g > 0:
            body = body - m3d.Manifold.cylinder(h + 2 * g + 2, ri - g, ri - g, seg).translate([0, 0, -1 - g])
        body = _round_along(p["axis"], ro, body)
    elif shape == "sphere":
        r = p["diameter"] / 2
        body = m3d.Manifold.sphere(r + g, seg).translate([r, r, r])
    else:
        raise ValueError(f"no solid for shape {shape!r}")
    return body


def component_solid(c: "Component", grow: float = 0.0):
    """The component's solid with its min corner at the origin (before growth), as OpenSCAD builds it."""
    if m3d is None:
        raise RuntimeError("manifold3d is not installed; layer-2 checks are unavailable")
    flipped = bool(c.shape == "wedge" and c.place and c.place.get("side") == "bottom")
    return _solid_cached(c.shape, json.dumps(c.params, sort_keys=True), flipped, float(grow))


def mass_properties(solid) -> Tuple[float, np.ndarray]:
    """Volume and centre of mass of a closed solid (signed tetrahedra over its mesh)."""
    mesh = solid.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=float)[:, :3]
    t = np.asarray(mesh.tri_verts, dtype=np.int64)
    if len(t) == 0:
        return 0.0, np.zeros(3)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    total = vol.sum()
    if abs(total) < 1e-12:
        return 0.0, np.zeros(3)
    com = (vol[:, None] * (a + b + c) / 4.0).sum(axis=0) / total
    return float(abs(total)), com


def solid_vertices(solid) -> np.ndarray:
    return np.asarray(solid.to_mesh().vert_properties, dtype=float)[:, :3]


# ---------------------------------------------------------------------------
# Check implementations
# ---------------------------------------------------------------------------


def _deps(comps: Iterable["Component"], params: Iterable[str] = ()) -> Dict[str, List[str]]:
    names = []
    for c in comps:
        if c.name not in names:
            names.append(c.name)
    return {"components": names, "params": list(dict.fromkeys(params))}


def _result(chk: Check, margin: float, unit: str, deps, measured, expected, detail: str,
            passed: Optional[bool] = None) -> CheckResult:
    margin = float(margin)
    if not math.isfinite(margin):
        margin = -1.0
    return CheckResult(chk.id, chk.l1_id, chk.type, margin >= 0 if passed is None else passed, round(margin, 6),
                       unit, deps, {"measured": measured, "expected": expected, "detail": detail},
                       2 if chk.type in LAYER2 else 1, chk.hard)


def _missing(chk: Check, what: str, unit: str = "", deps=None) -> CheckResult:
    return _result(chk, -1.0, unit, deps or {"components": [], "params": []}, None, None,
                   f"cannot check: {what}", passed=False)


def _parts(sc: Scene, chk: Check, slot: str = "part") -> Tuple[List["Component"], Optional[CheckResult]]:
    name = chk.params.get(slot)
    comps = select(sc.d, name)
    if not comps:
        return [], _missing(chk, f"no laid-out part named {name!r}",
                            deps={"components": [name] if name else [], "params": []})
    return comps, None


def _dim_tol(p: dict) -> float:
    if p.get("tol") is not None:
        return float(p["tol"])
    if p.get("measure") == "angle":
        return 0.5
    return max(_ca().ABS_TOL, 0.01 * abs(float(p["value"])))


def _op_margin(measured: float, expected: float, tol: float, op: str) -> float:
    scale = max(abs(expected), tol, 1e-9)
    if op == "ge":
        return (measured - expected + tol) / scale
    if op == "le":
        return (expected + tol - measured) / scale
    return (tol - abs(measured - expected)) / scale


def measure_dimension(sc: Scene, c: "Component", measure: str, param: Optional[str] = None
                      ) -> Tuple[Optional[float], List[str]]:
    """(value, [comp.param it depends on]) for a component; None when the measure does not apply."""
    ca = _ca()
    p = c.params or {}
    if param:
        v = p.get(param)
        return (float(v), [f"{c.name}.{param}"]) if isinstance(v, (int, float)) else (None, [])
    axes = {"width": 0, "depth": 1, "height": 2}
    if measure in axes:
        sp = ca.size_param(c, "xyz"[axes[measure]])
        return c.size[axes[measure]], ([f"{c.name}.{sp}"] if sp else [f"{c.name}.{k}" for k in p
                                                                         if isinstance(p[k], (int, float))])
    if measure in ("length", "thickness"):
        if measure == "thickness" and c.shape == "panel":
            return float(p["thickness"]), [f"{c.name}.thickness"]
        if measure == "thickness" and c.shape == "tube":
            return (p["outer_diameter"] - p["inner_diameter"]) / 2, [f"{c.name}.outer_diameter",
                                                                     f"{c.name}.inner_diameter"]
        vals = list(c.size)
        target = max(vals) if measure == "length" else min(vals)
        axes_hit = [a for a in range(3) if abs(vals[a] - target) <= 1e-6]
        sps = {ca.size_param(c, "xyz"[a]) for a in axes_hit}
        sps.discard(None)
        return target, [f"{c.name}.{s}" for s in sorted(sps)]
    if measure == "diameter":
        key = {"cylinder": "diameter", "sphere": "diameter", "tube": "outer_diameter"}.get(c.shape)
        return (float(p[key]), [f"{c.name}.{key}"]) if key else (None, [])
    if measure == "inner_diameter":
        return (float(p["inner_diameter"]), [f"{c.name}.inner_diameter"]) if c.shape == "tube" else (None, [])
    if measure == "angle":
        return (float(p["angle"]), [f"{c.name}.angle"]) if c.shape == "panel" else (None, [])
    if measure in ("top", "bottom"):
        insts = sc.of([c])
        v = max(i.hi[2] for i in insts) if measure == "top" else min(i.lo[2] for i in insts)
        chain, cur = [], c
        while cur is not None:
            chain.append(cur)
            cur = sc.d.component(cur.place["parent"]) if cur.place else None
        return v, [f"{x.name}.{k}" for x in chain for k in (x.params or {}) if isinstance(x.params[k], (int, float))]
    return None, []


def check_count(sc: Scene, chk: Check) -> CheckResult:
    p = chk.params
    comps = select(sc.d, p.get("part")) if p.get("part") else list(sc.d.components)
    comps = [c for c in comps if c.positions]
    if p.get("shape"):
        want = ("cylinder", "tube", "sphere") if p["shape"] == "round" else (p["shape"],)
        comps = [c for c in comps if c.shape in want]
    n = sum(len(c.positions) for c in comps)
    exp, op = int(p["count"]), p.get("op") or "eq"
    if op == "eq":
        margin = 0.0 if n == exp else -abs(n - exp) / max(exp, 1)
    elif op == "ge":
        margin = (n - exp) / max(exp, 1)
    else:
        margin = (exp - n) / max(exp, 1)
    if not sc.insts:
        margin = min(margin, -1.0)
    names = ", ".join(f"{c.name} x{len(c.positions)}" for c in comps) or "none"
    return _result(chk, margin, "count", _deps(comps, [f"{c.name}.count" for c in comps]), n,
                   f"{OP_WORDS[op]}{exp}".strip(), f"found {n} ({names}); expected {OP_WORDS[op]}{exp}")


def check_dimension(sc: Scene, chk: Check) -> CheckResult:
    p = chk.params
    unit = "deg" if p["measure"] == "angle" else "mm"
    exp, tol, op = float(p["value"]), _dim_tol(p), p.get("op") or "eq"
    if not p.get("part"):
        bb = sc.bbox()
        if bb is None:
            return _missing(chk, "the design is empty", unit)
        extents = [bb[1][a] - bb[0][a] for a in range(3)]
        axis = {"width": 0, "depth": 1, "height": 2, "top": 2}.get(p["measure"])
        if axis is not None:
            v = extents[axis]
        elif p["measure"] in ("length", "thickness"):   # "a strip 300 mm long": the overall longest size
            v = max(extents) if p["measure"] == "length" else min(extents)
        else:
            return _missing(chk, f"measure {p['measure']} needs a part", unit)
        return _result(chk, _op_margin(v, exp, tol, op), unit, _deps(sc.d.components), round(v, 3), exp,
                       f"whole object {p['measure']} = {_fmt(v)} {unit}, expected {OP_WORDS[op]}{_fmt(exp)}")
    comps, err = _parts(sc, chk)
    if err:
        return err
    margins, details, params, measured = [], [], [], []
    for c in comps:
        v, deps = measure_dimension(sc, c, p["measure"], p.get("param"))
        params += deps
        if v is None:
            margins.append(-1.0)
            details.append(f"{c.name}: {p.get('param') or p['measure']} does not apply to a {c.shape}")
            continue
        margins.append(_op_margin(v, exp, tol, op))
        measured.append(round(v, 3))
        details.append(f"{c.name}: {p.get('param') or p['measure']} = {_fmt(v)} {unit}")
    detail = "; ".join(details) + f"; expected {OP_WORDS[op]}{_fmt(exp)} {unit} (tol {_fmt(tol)})"
    return _result(chk, min(margins), unit, _deps(comps, params),
                   measured[0] if len(measured) == 1 else measured, exp, detail)


def check_shape(sc: Scene, chk: Check) -> CheckResult:
    p = chk.params
    comps, err = _parts(sc, chk)
    if err:
        return err
    # "any": only the orientation is checked ("the divider stands vertically")
    want = ("cylinder", "tube", "sphere") if p["shape"] == "round" else \
        tuple(_ca().SHAPES) if p["shape"] == "any" else (p["shape"],)
    margin, details = 0.0, []
    for c in comps:
        ok = c.shape in want
        if not ok and p["shape"] == "panel" and c.shape == "box" and c.size:
            # a thin box is a flat panel ("a single flat strip" built as a 300 x 30 x 3 box)
            s = sorted(c.size)
            ok = s[0] <= 0.25 * s[1]
        why = c.shape
        if ok and p.get("orient"):
            o = p["orient"]
            if c.shape == "sphere" and o in ("flat", "upright"):
                ok = o == "upright"   # a ball never lies flat
            elif o == "upright" and c.shape == "panel":
                ok = c.params["angle"] >= 89.5   # a panel is upright only when vertical
                why += f" at {_fmt(c.params['angle'])} degrees"
            elif o in ("flat", "upright"):
                # flat: the thinnest side is vertical. upright: not flat - the vertical size is
                # not the thinnest (a wall 150 wide, 4 thick, 90 tall stands upright, as does a leg).
                # Round parts use the same rule: an axis-z cylinder 100 across and 5 tall is a disc
                # lying flat, not upright (it used to pass both); a coin on its edge is upright.
                s = list(c.size)
                ok = (s[2] <= min(s) + 1e-6) if o == "flat" else (s[2] > min(s) + 1e-6)
                why += f" sized {' x '.join(_fmt(v) for v in s)}"
            elif c.shape in ("cylinder", "tube"):
                ok = c.params["axis"] == o
                why += f" with axis {c.params['axis']}"
            else:
                ok = c.size["xyz".index(o)] >= max(c.size) - 1e-6
                why += f" longest along {'xyz'[list(c.size).index(max(c.size))]}"
        if not ok:
            margin = -1.0
        details.append(f"{c.name} is a {why}")
    return _result(chk, margin, "shape", _deps(comps, [f"{c.name}.shape" for c in comps]),
                   [c.shape for c in comps], p["shape"] + (f" ({p['orient']})" if p.get("orient") else ""),
                   "; ".join(details))


REL_AXIS = {"on_top_of": (2, +1), "underneath": (2, -1), "behind": (1, +1), "in_front_of": (1, -1),
            "right_of": (0, +1), "left_of": (0, -1)}


def _overlap_1d(a_lo, a_hi, b_lo, b_hi) -> float:
    return min(a_hi, b_hi) - max(a_lo, b_lo)


def _relation_margin(a: Inst, b: Inst, relation: str, touching: bool, tol: float) -> Tuple[float, str]:
    if relation == "beside":
        options = [_relation_margin(a, b, r, touching, tol) for r in ("left_of", "right_of", "in_front_of", "behind")]
        return max(options, key=lambda x: x[0])
    axis, sign = REL_AXIS[relation]
    gap = a.lo[axis] - b.hi[axis] if sign > 0 else b.lo[axis] - a.hi[axis]
    ref = max(a.size[axis] + b.size[axis], 1.0)
    m_gap = (tol - abs(gap)) / ref if touching else (gap + tol) / ref
    others = [x for x in range(3) if x != axis]
    ratios = []
    for x in others:
        ov = _overlap_1d(a.lo[x], a.hi[x], b.lo[x], b.hi[x])
        ratios.append(ov / max(min(a.size[x], b.size[x]), 1e-9))
    m_ov = min(ratios) if touching else min(ratios) + 1.0  # not touching: ordering only, overlap optional
    m_ov = min(m_ov, 1.0)
    margin = min(m_gap, m_ov - 0.01) if touching else m_gap
    return margin, f"gap {_fmt(gap)} mm along {'xyz'[axis]}, face overlap {min(ratios):.2f}"


def check_relation(sc: Scene, chk: Check) -> CheckResult:
    p = chk.params
    comps, err = _parts(sc, chk)
    if err:
        return err
    others, err = _parts(sc, chk, "other")
    if err:
        return err
    other_ids = {id(c) for c in others}
    a_insts = [i for i in sc.of(comps) if id(i.comp) not in other_ids]
    b_insts = sc.of(others)
    if not a_insts:
        return _missing(chk, "part and other are the same", deps=_deps(comps + others))
    touching = p.get("touching", True)

    def margin(a: Inst, b: Inst) -> Tuple[float, str, Inst]:
        m, text = _relation_margin(a, b, p["relation"], touching, p.get("tol") or 0.5)
        if touching and m3d is not None:
            m_t, t_text = _support_margin(sc, a, b, p["relation"])
            m, text = min(m, m_t), f"{text}; {t_text}"
        return m, text, b

    worst, detail = None, ""
    for a in a_insts:
        best = max((margin(a, b) for b in b_insts), key=lambda x: x[0])
        if worst is None or best[0] < worst:
            worst, detail = best[0], f"{a.label} vs {best[2].label}: {best[1]}"
    deps = _deps(comps + others, [f"{c.name}.place" for c in comps + others])
    res = _result(chk, worst, "mm", deps, detail, f"{p['relation']}{' (touching)' if touching else ''}", detail)
    if touching and m3d is not None:
        res.layer = 2   # real contact was measured
    return res


def _support_margin(sc: Scene, a: Inst, b: Inst, relation: str) -> Tuple[float, str]:
    """Real contact behind a "touching" relation (layer 2), plus support for on top of / underneath.

    Bounding boxes alone passed a round post whose box overlapped the round base's
    box diagonally (0 mm^2 of real contact) and a cup resting on 1% of a corner.
    So: the real contact area must reach MIN_CONTACT_AREA, and for a vertical
    relation the centre of the smaller footprint must lie over the larger one.
    """
    need = _ca().min_contact(a.comp, b.comp)
    area = max(sc.contact(a, b), sc.contact(b, a))
    m = max(min((area - need) / need, 1.0), -1.0)
    text = f"contact {_fmt(round(area, 1))} mm^2 (need {_fmt(need)})"
    if relation in ("on_top_of", "underneath"):
        fa = a.size[0] * a.size[1]
        fb = b.size[0] * b.size[1]
        small, big = (a, b) if fa <= fb else (b, a)
        m_c = min(min(small.center[x] - big.lo[x], big.hi[x] - small.center[x]) / max(big.size[x] / 2, 1e-9)
                  for x in (0, 1))
        m = min(m, m_c)
        text += f", {small.comp.name}'s centre {'over' if m_c >= 0 else 'NOT over'} {big.comp.name}"
    return m, text


def check_edge(sc: Scene, chk: Check) -> CheckResult:
    p = chk.params
    comps, err = _parts(sc, chk)
    if err:
        return err
    others, err = _parts(sc, chk, "other")
    if err:
        return err
    b = sc.bbox(sc.of(others))
    where = p["where"]
    axes = {"front": [1], "back": [1], "left": [0], "right": [0]}.get(where) or \
        ([0] if p.get("axis") == "x" else [1] if p.get("axis") == "y" else [0, 1])
    worst, detail = None, ""
    for a in sc.of(comps):
        for x in axes:
            ext = b[1][x] - b[0][x]
            if where in ("front", "left"):
                off = a.lo[x] - b[0][x]
            elif where in ("back", "right"):
                off = b[1][x] - a.hi[x]
            else:
                off = a.center[x] - (b[0][x] + b[1][x]) / 2
            lim = p.get("max_offset")
            if lim is None:
                lim = max(1.0, (0.05 if where == "center" else 0.1) * ext)
            m = (lim - abs(off)) / max(ext, 1.0)
            if worst is None or m < worst:
                worst = m
                detail = (f"{a.label} is {_fmt(abs(off))} mm from the {where if where != 'center' else 'centre'}"
                          f" of {others[0].name} along {'xyz'[x]} (allowed {_fmt(lim)} mm)")
    deps = _deps(comps + others, [f"{c.name}.place" for c in comps])
    return _result(chk, worst, "mm", deps, detail, f"{where} of {others[0].name}", detail)


def check_span(sc: Scene, chk: Check) -> CheckResult:
    p = chk.params
    comps, err = _parts(sc, chk)
    if err:
        return err
    others, err = _parts(sc, chk, "other")
    if err:
        return err
    b = sc.bbox(sc.of(others))
    x = "xyz".index(p["axis"])
    ext = b[1][x] - b[0][x]
    tol = p.get("tol") or 0.5
    worst, detail, params = None, "", []
    for a in sc.of(comps):
        cov = max(0.0, _overlap_1d(a.lo[x], a.hi[x], b[0][x], b[1][x]))
        m = (cov - (ext - tol)) / max(ext, 1.0)
        if worst is None or m < worst:
            worst, detail = m, f"{a.label} covers {_fmt(cov)} of {_fmt(ext)} mm along {p['axis']}"
    for c in comps:
        sp = _ca().size_param(c, p["axis"])
        if sp:
            params.append(f"{c.name}.{sp}")
        params.append(f"{c.name}.place")
    return _result(chk, worst, "mm", _deps(comps + others, params), detail, f"{_fmt(ext)} mm", detail)


def _hull_area(pts: Sequence[Tuple[float, float]]) -> float:
    hull = _ca().convex_hull(list(pts))
    if len(hull) < 3:
        return 0.0
    return abs(sum(hull[i][0] * hull[(i + 1) % len(hull)][1] - hull[(i + 1) % len(hull)][0] * hull[i][1]
                   for i in range(len(hull)))) / 2


def check_arrangement(sc: Scene, chk: Check) -> CheckResult:
    p = chk.params
    comps, err = _parts(sc, chk)
    if err:
        return err
    if p.get("other"):
        others, err = _parts(sc, chk, "other")
        if err:
            return err
    else:
        parent = sc.d.component(comps[0].place["parent"]) if comps[0].place else None
        others = [parent] if parent and parent.positions else [sc.insts[0].comp]
    other_ids = {id(c) for c in others}
    insts = [i for i in sc.of(comps) if id(i.comp) not in other_ids]
    lo, hi = sc.bbox(sc.of(others))
    half = [max((hi[a] - lo[a]) / 2, 1e-9) for a in range(3)]
    ctr = [(hi[a] + lo[a]) / 2 for a in range(3)]
    uv = [tuple((i.center[a] - ctr[a]) / half[a] for a in range(3)) for i in insts]
    pat, n = p["pattern"], len(insts)
    plane = (0, 1)  # horizontal by default; an explicit vertical axis uses it as the first axis
    deps = _deps(comps + others, [f"{c.name}.arrangement" for c in comps] + [f"{c.name}.count" for c in comps])
    detail = f"{n} copies at normalised positions " + ", ".join(f"({u[0]:.2f}, {u[1]:.2f}, {u[2]:.2f})" for u in uv)
    if n == 0:
        return _missing(chk, "no copies to arrange", deps=deps)
    if pat == "corners":
        margins = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                cand = [min(abs(u[0]), abs(u[1])) for u in uv if u[0] * sx > 0 and u[1] * sy > 0]
                margins.append((max(cand) - 0.4) / 0.4 if cand else -1.0)
        margin = min(margins)
    elif pat == "ends":
        # No axis given: either horizontal axis will do (the English rendering names none,
        # so a silent x default failed a correct front-to-back pair).
        cands = ["xyz".index(p["axis"])] if p.get("axis") else [0, 1]

        def ends_margin(a):
            us = [u[a] for u in uv]
            return min((-min(us) - 0.5) / 0.5, (max(us) - 0.5) / 0.5) if n >= 2 else -1.0
        a = max(cands, key=ends_margin)
        margin = ends_margin(a)
        if not p.get("axis"):
            detail += f"; ends along {'xyz'[a]}"
    elif pat == "row":
        if p.get("axis"):
            a = "xyz".index(p["axis"])
        else:   # the horizontal axis the copies are spread along (see "ends")
            a = max((0, 1), key=lambda x: max(u[x] for u in uv) - min(u[x] for u in uv))
            detail += f"; row along {'xyz'[a]}"
        perp = [x for x in plane if x != a] if a in plane else [0, 1]
        us = sorted(u[a] for u in uv)
        if n < 2:
            margin = -1.0
        else:
            dev = max(max(u[x] for u in uv) - min(u[x] for u in uv) for x in perp) / 2
            spread = us[-1] - us[0]
            gaps = [us[i + 1] - us[i] for i in range(n - 1)]
            cv = (max(gaps) - min(gaps)) / max(np.mean(gaps), 1e-9) if n > 2 else 0.0
            margin = min((0.05 - dev) / 0.05, (spread - 0.2) / 0.2, (0.15 - cv) / 0.15)
            detail += f"; off-line {dev:.2f}, spread {spread:.2f}, spacing variation {cv:.2f}"
    else:  # triangle / spread: not collinear and spread over the footprint (normalised square has area 4)
        ratio = _hull_area([(u[plane[0]], u[plane[1]]) for u in uv]) / 4.0
        margin = (ratio - 0.15) / 0.15 if n >= 3 else -1.0
        if pat == "triangle" and n != 3:
            margin = min(margin, -abs(n - 3) / 3)
        detail += f"; footprint coverage {ratio:.2f} (need 0.15)"
    return _result(chk, max(margin, -1.0), "ratio", deps, detail, pat, detail)


def check_touches(sc: Scene, chk: Check) -> CheckResult:
    p = chk.params
    comps, err = _parts(sc, chk)
    if err:
        return err
    others, err = _parts(sc, chk, "other")
    if err:
        return err
    need = p.get("min_area") or min(_ca().min_contact(c, o) for c in comps for o in others)
    worst, detail = None, ""
    other_ids = {id(c) for c in others}
    for a in [i for i in sc.of(comps) if id(i.comp) not in other_ids]:
        area = max((sc.contact(a, b) for b in sc.of(others)), default=0.0)
        m = max((area - need) / need, -1.0)
        if worst is None or m < worst:
            worst, detail = m, f"{a.label} touches {others[0].name} over {_fmt(round(area, 1))} mm^2"
    if worst is None:
        return _missing(chk, "part and other are the same")
    return _result(chk, min(worst, 1.0), "mm^2", _deps(comps + others, [f"{c.name}.place" for c in comps]),
                   detail, f">= {_fmt(need)} mm^2", detail)


def check_connected(sc: Scene, chk: Check) -> CheckResult:
    names = chk.params.get("parts")
    comps = [c for n in names for c in select(sc.d, n)] if names else [i.comp for i in sc.insts]
    insts = sc.of(comps)
    if not insts:
        return _missing(chk, "no parts to connect")
    parent = list(range(len(insts)))

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for i in range(len(insts)):
        for j in range(i + 1, len(insts)):
            if find(i) != find(j) and sc.contact(insts[i], insts[j]) > min(CONNECT_AREA, 0.5 * _ca().min_contact(insts[i].comp, insts[j].comp)):
                parent[find(i)] = find(j)
    groups: Dict[int, List[str]] = {}
    for k, inst in enumerate(insts):
        groups.setdefault(find(k), []).append(inst.label)
    bodies = len(groups)
    margin = 0.0 if bodies == 1 else -(bodies - 1) / max(len(insts) - 1, 1)
    detail = f"{bodies} bod{'y' if bodies == 1 else 'ies'}: " + " | ".join(", ".join(g) for g in groups.values())
    return _result(chk, margin, "bodies", _deps(comps, [f"{c.name}.place" for c in comps]), bodies, 1, detail)


def check_no_overlap(sc: Scene, chk: Check) -> CheckResult:
    names = chk.params.get("parts")
    comps = [c for n in names for c in select(sc.d, n)] if names else [i.comp for i in sc.insts]
    insts = sc.of(comps)
    if not insts:
        return _missing(chk, "no parts")
    limit = chk.params.get("max_volume") or OVERLAP_VOLUME
    worst_ratio, worst = 0.0, None
    for i in range(len(insts)):
        for j in range(i + 1, len(insts)):
            vol = sc.overlap(insts[i], insts[j])
            if vol > limit:
                vi = mass_properties(sc.solid(insts[i]))[0]
                vj = mass_properties(sc.solid(insts[j]))[0]
                ratio = vol / max(min(vi, vj), 1e-9)
                if ratio > worst_ratio:
                    worst_ratio, worst = ratio, (insts[i].label, insts[j].label, vol)
    detail = (f"{worst[0]} and {worst[1]} overlap by {_fmt(round(worst[2], 1))} mm^3 "
              f"({worst_ratio:.0%} of the smaller)") if worst else "no overlapping parts"
    return _result(chk, -min(worst_ratio, 1.0) if worst else 0.0, "mm^3",
                   _deps(comps, [f"{c.name}.place" for c in comps]),
                   round(worst[2], 2) if worst else 0.0, f"<= {_fmt(limit)} mm^3", detail,
                   passed=worst is None)


def _signed_distance(pt: Tuple[float, float], hull: Sequence[Tuple[float, float]]) -> float:
    """Distance from a point to a convex polygon's boundary: positive inside, negative outside."""
    def seg_dist(p, a, b):
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)
    if not hull:
        return -1e9
    if len(hull) == 1:
        return -math.hypot(pt[0] - hull[0][0], pt[1] - hull[0][1])
    d = min(seg_dist(pt, hull[i], hull[(i + 1) % len(hull)]) for i in range(len(hull)))
    return d if _ca().inside_hull(pt, hull) else -d


def check_stable(sc: Scene, chk: Check) -> CheckResult:
    p = chk.params
    if not sc.insts:
        return _missing(chk, "the design is empty", "mm")
    density = p.get("density") or DENSITY
    total_m, moment = 0.0, np.zeros(3)
    pts_by_inst = []
    for inst in sc.insts:
        vol, com = mass_properties(sc.solid(inst))
        total_m += vol * density
        moment += vol * density * com
        pts_by_inst.append(solid_vertices(sc.solid(inst)))
    allpts = np.vstack(pts_by_inst)
    zmin = allpts[:, 2].min()
    deps_comps = [i.comp for i in sc.insts]
    load = p.get("load") or {}
    load_text = ""
    if load:
        mass = float(load.get("mass_g") or 0.0)
        if load.get("point"):
            pt = np.array(load["point"], dtype=float)
        else:
            comps = select(sc.d, load.get("part"))
            if not comps:
                return _missing(chk, f"no part named {load.get('part')!r} to load")
            lo, hi = sc.bbox(sc.of(comps))
            face = load.get("face", "top")
            pt = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, hi[2]])
            axis_side = {"top": (2, 1), "front": (1, 0), "back": (1, 1), "left": (0, 0), "right": (0, 1)}
            a, s = axis_side.get(face, (2, 1))
            pt[a] = hi[a] if s else lo[a]
            off = load.get("offset") or [0.0, 0.0]
            pt[0] += off[0]
            pt[1] += off[1]
        total_m += mass
        moment += mass * pt
        load_text = f"; with {_fmt(mass)} g at {fmt_point(pt)}"
    com = moment / max(total_m, 1e-12)
    feet = [(float(x), float(y)) for x, y, z in allpts if z <= zmin + 0.01]
    hull = _ca().convex_hull(feet)
    area = _hull_area(feet)
    if area < 1e-6:
        return _result(chk, -1.0, "mm", _deps(deps_comps), fmt_point(com), "inside the footprint",
                       "the object touches the table only along a line or at a point" + load_text)
    tilt = math.radians(p.get("tilt_deg") or 0.0)
    dists = []
    dirs = [(math.cos(k * math.pi / 4), math.sin(k * math.pi / 4)) for k in range(8)] if tilt else [(0.0, 0.0)]
    for dx, dy in dirs:
        shift = (com[2] - zmin) * math.tan(tilt)
        dists.append(_signed_distance((com[0] + shift * dx, com[1] + shift * dy), hull))
    dist = min(dists)
    margin = dist / max(math.sqrt(area), 1.0)
    detail = (f"centre of mass {fmt_point(com)} is {_fmt(round(abs(dist), 1))} mm "
              f"{'inside' if dist >= 0 else 'outside'} the {_fmt(round(area))} mm^2 footprint{load_text}")
    return _result(chk, margin, "mm", _deps(deps_comps), round(dist, 2), ">= 0 mm inside", detail)


def fmt_point(v) -> str:
    return "(" + ", ".join(_fmt(round(float(x), 1)) for x in v) + ")"


# ----- stand-ins: fits (3D drop) -----


def _standin_solid(spec: dict, orientation: str, across_axis: Optional[int], lateral: float):
    """A stand-in solid, min corner at the origin, grown sideways by `lateral` (clearance).

    Box orientation: upright = longest side vertical, edge = middle side vertical,
    flat = thinnest side vertical. Its thinnest horizontal side crosses `across_axis`.
    Returns (solid, size xyz, size across, footprint diagonal).
    """
    if spec["kind"] == "cylinder":
        d, L = spec["diameter"], spec["length"]
        if orientation == "upright":
            r = d / 2 + lateral
            solid = m3d.Manifold.cylinder(L, r, r, 48).translate([r, r, 0])
            return solid, (2 * r, 2 * r, L), d, d
        axis = 1 if across_axis == 0 else 0
        size = [0.0, 0.0, d]
        size[axis], size[1 - axis] = L + 2 * lateral, d + 2 * lateral
        solid = m3d.Manifold.cube(size)
        return solid, tuple(size), d, math.hypot(L, d)
    dims = sorted(spec["dims"])
    vert = {"upright": dims[2], "edge": dims[1], "flat": dims[0]}[orientation]
    rest = list(dims)
    rest.remove(vert)
    small, big = sorted(rest)
    size = [0.0, 0.0, vert]
    across = across_axis if across_axis is not None else 1
    size[across], size[1 - across] = small + 2 * lateral, big + 2 * lateral
    return m3d.Manifold.cube(size), tuple(size), small, math.hypot(small, big)


def _drop(sc: Scene, solid, xy: Tuple[float, float], size) -> Tuple[float, List[str]]:
    """Lower a stand-in from above the design until it touches something (or the table). Returns its bottom z."""
    top = (sc.bbox()[1][2] if sc.insts else 0.0) + 1.0
    world = sc.union()
    x0, y0 = xy[0] - size[0] / 2, xy[1] - size[1] / 2

    def hits(z):
        return z < -1e-9 or (solid.translate([x0, y0, z]) ^ world).volume() > 1e-3

    z = top
    while z > 0 and not hits(z - SETTLE_STEP):
        z -= SETTLE_STEP
    if z <= 0:
        lo_z = 0.0
    else:
        free, hit = z, z - SETTLE_STEP
        while free - hit > SETTLE_TOL:
            mid = (free + hit) / 2
            if hits(mid):
                hit = mid
            else:
                free = mid
        lo_z = max(free, 0.0)
    placed = solid.translate([x0, y0, lo_z])
    grown_contacts = []
    for inst in sc.insts:
        if (placed ^ sc.solid(inst, 0.2)).volume() > 1e-4:
            grown_contacts.append(inst.label)
    if lo_z <= 1e-6:
        grown_contacts.append("table")
    return lo_z, grown_contacts


def check_fits(sc: Scene, chk: Check) -> CheckResult:
    p = chk.params
    spec = standin(p["object"], p.get("size"))
    comps = [c for n in p["into"] for c in select(sc.d, n)]
    deps = _deps(comps, [f"{c.name}.{k}" for c in comps for k in (c.params or {})
                         if isinstance(c.params[k], (int, float))])
    if not comps or (p.get("between") and len(p["into"]) != 2):
        return _missing(chk, f"parts {p['into']} not found" if not comps else "between needs exactly two parts",
                        deps=deps)
    clearance = float(p.get("clearance") if p.get("clearance") is not None else 1.0)
    orientation = p.get("orientation") or ("edge" if p.get("between") else "upright")
    margins, notes = [], []
    if p.get("between"):
        a_c, b_c = select(sc.d, p["into"][0]), select(sc.d, p["into"][1])
        if not a_c or not b_c:
            return _missing(chk, "both parts must exist", deps=deps)
        if p["into"][0] == p["into"][1]:
            # "between two neighbouring dividers": two copies of one part, the first two
            # along the direction the copies are spread in
            insts = sc.of(a_c)
            if len(insts) < 2:
                return _missing(chk, "between one part and itself needs at least two copies", deps=deps)
            spread = max(range(3), key=lambda x: max(i.center[x] for i in insts) - min(i.center[x] for i in insts))
            insts = sorted(insts, key=lambda i: i.center[spread])
            A, B = sc.bbox(insts[:1]), sc.bbox(insts[1:2])
        else:
            A, B = sc.bbox(sc.of(a_c)), sc.bbox(sc.of(b_c))
        gaps = []
        for x in (0, 1):
            g = max(B[0][x] - A[1][x], A[0][x] - B[1][x])
            gaps.append(g)
        axis = int(np.argmax(gaps))
        gap = gaps[axis]
        solid, size, across, _ = _standin_solid(spec, orientation, axis, clearance)
        need = across + 2 * clearance
        margins.append((gap - need) / max(need, 1.0))
        notes.append(f"gap {_fmt(round(gap, 2))} mm along {'xy'[axis]} for {_fmt(need)} mm (object + clearance)")
        if A[1][axis] <= B[0][axis]:
            lo_side, hi_side = A[1][axis], B[0][axis]
        elif B[1][axis] <= A[0][axis]:
            lo_side, hi_side = B[1][axis], A[0][axis]
        else:  # they overlap along the axis: no gap to put anything in
            lo_side = hi_side = (max(A[0][axis], B[0][axis]) + min(A[1][axis], B[1][axis])) / 2
        other = 1 - axis
        ov_lo, ov_hi = max(A[0][other], B[0][other]), min(A[1][other], B[1][other])
        xy = [0.0, 0.0]
        xy[axis] = (lo_side + hi_side) / 2
        xy[other] = (ov_lo + ov_hi) / 2 if ov_hi > ov_lo else (A[0][other] + A[1][other]) / 2
        top_ref = min(A[1][2], B[1][2])
        floor = max(A[0][2], B[0][2])
    else:
        solid, size, across, diag = _standin_solid(spec, orientation, None, clearance)
        tubes = [c for c in comps if c.shape == "tube" and c.params["axis"] == "z"]
        if len(comps) == 1 and tubes and orientation == "upright":
            hole = tubes[0].params["inner_diameter"]
            need = (across if spec["kind"] == "cylinder" else diag) + 2 * clearance
            margins.append((hole - need) / max(hole, 1.0))
            notes.append(f"hole {_fmt(hole)} mm across for {_fmt(round(need, 1))} mm (object + clearance)")
    if not sc.insts or not sc.of(comps):
        return _missing(chk, "the design is empty", deps=deps)
    min_depth_slot = p.get("min_depth")
    if p.get("between"):
        targets = [("", xy, top_ref, floor, None)]
    else:
        # One drop per container. Copies of ONE part ("cup" x2) are separate containers:
        # dropping at the centre of all copies' box would land between two solid posts
        # and pass (odd vs even counts gave opposite verdicts). Several different parts
        # ("floor" + "wall") together form one container.
        groups = [[i] for i in sc.of(comps)] if len(comps) == 1 and len(sc.of(comps)) > 1 else [sc.of(comps)]
        targets = []
        for g in groups:
            lo, hi = sc.bbox(g)
            targets.append((g[0].label + ": " if len(groups) > 1 else "", ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2),
                            hi[2], lo[2], (lo, hi)))
    depths = []
    for label, xy_t, top_t, floor_t, box in targets:
        z, contacts = _drop(sc, solid, xy_t, size)
        depth = top_t - z
        depths.append(depth)
        min_depth = min_depth_slot if min_depth_slot is not None else 0.5 * max(top_t - floor_t, 0.0)
        min_depth = max(min_depth, 0.5)
        margins.append((depth - min_depth) / max(min_depth, 1.0))
        notes.append(f"{label}dropped in, it comes to rest at z = {_fmt(round(z, 2))} touching "
                     f"{', '.join(contacts) or 'nothing'}; {_fmt(round(depth, 1))} mm below the rim "
                     f"(need {_fmt(round(min_depth, 1))})")
        if box is not None:
            m_enc, open_sides = _enclosure(sc, xy_t, size, z, box, clearance)
            margins.append(m_enc)
            notes.append(f"{label}walled in on {4 - len(open_sides)} of 4 sides"
                         + (f" (open: {', '.join(open_sides)})" if open_sides else ""))
    margin = min(margins)
    depth = min(depths)
    shown = min_depth_slot if min_depth_slot is not None else 0.5 * max(targets[0][2] - targets[0][3], 0.0)
    return _result(chk, margin, "mm", deps, round(depth, 2), f">= {_fmt(round(max(shown, 0.5), 1))} mm deep",
                   "; ".join(notes))


FIT_SIDES = (("left", 0, -1), ("right", 0, +1), ("front", 1, -1), ("back", 1, +1))


def _enclosure(sc: Scene, xy: Tuple[float, float], size, z: float, box: Tuple[Vec, Vec],
               clearance: float) -> Tuple[float, List[str]]:
    """Is the settled stand-in held in, i.e. does something wall it in sideways?

    The drop alone only measures how far the object sinks below the highest rim;
    a plate with one wall, or two posts with a gap, let it sink just as far. So
    the stand-in's footprint (lifted 0.5 mm off whatever it rests on) is swept
    towards each side, out to the container's own edge plus a little, and any
    part it runs into blocks that side. Held in = blocked on both sides of at
    least one horizontal axis (a tray with front and back walls holds a box);
    margin +1 when walled in all round, +0.5 for one opposite pair, negative
    otherwise. The open sides are reported.
    """
    world = sc.union()
    lo_obj = [xy[0] - size[0] / 2, xy[1] - size[1] / 2]
    hi_obj = [xy[0] + size[0] / 2, xy[1] + size[1] / 2]
    z0, z1 = z + 0.5, z + size[2]
    if z1 <= z0:
        z1 = z0 + 0.5
    blocked = {}
    for name, a, sign in FIT_SIDES:
        reach = (box[1][a] - hi_obj[a]) if sign > 0 else (lo_obj[a] - box[0][a])
        reach = max(reach, 0.0) + clearance + 2.0
        lo, hi = list(lo_obj), list(hi_obj)
        if sign > 0:
            lo[a], hi[a] = hi_obj[a], hi_obj[a] + reach
        else:
            lo[a], hi[a] = lo_obj[a] - reach, lo_obj[a]
        sweep = m3d.Manifold.cube([hi[0] - lo[0], hi[1] - lo[1], z1 - z0]).translate([lo[0], lo[1], z0])
        blocked[name] = (sweep ^ world).volume() > 1e-3
    open_sides = [n for n, _, _ in FIT_SIDES if not blocked[n]]
    pair = (blocked["left"] and blocked["right"]) or (blocked["front"] and blocked["back"])
    if not open_sides:
        return 1.0, open_sides
    if pair:
        return 0.5, open_sides
    return -len(open_sides) / 4.0, open_sides


# ----- stand-ins: rests_on (planar quasi-static) -----

def nnls(A: np.ndarray, b: np.ndarray, max_iter: int = 200) -> Tuple[np.ndarray, float]:
    """Lawson-Hanson non-negative least squares: min ||Ax - b|| with x >= 0. Returns (x, residual)."""
    m, n = A.shape
    x = np.zeros(n)
    passive = np.zeros(n, dtype=bool)
    w = A.T @ (b - A @ x)
    it = 0
    while (~passive).any() and w[~passive].max(initial=-np.inf) > 1e-10 and it < max_iter:
        it += 1
        j = np.argmax(np.where(passive, -np.inf, w))
        passive[j] = True
        while True:
            z = np.zeros(n)
            z[passive] = np.linalg.lstsq(A[:, passive], b, rcond=None)[0]
            if (z[passive] > 1e-12).all():
                x = z
                break
            mask = passive & (z <= 1e-12)
            alpha = np.min(x[mask] / np.maximum(x[mask] - z[mask], 1e-18))
            x = x + alpha * (z - x)
            passive &= x > 1e-12
            if not passive.any():
                break
        w = A.T @ (b - A @ x)
    return x, float(np.linalg.norm(A @ x - b))


def equilibrium_feasible(contacts: Sequence[Tuple[np.ndarray, np.ndarray]], com: np.ndarray,
                         mu: float, scale: float) -> bool:
    """Can contact forces inside friction cones hold a planar body still under gravity?

    contacts: (point, inward unit normal) in the plane (s, z). Gravity is (0, -1)
    at `com`. Torques are divided by `scale` so forces and torques weigh alike.
    """
    cols = []
    for pt, n in contacts:
        t = np.array([-n[1], n[0]])
        for e in (n + mu * t, n - mu * t):
            r = pt - com
            cols.append([e[0], e[1], (r[0] * e[1] - r[1] * e[0]) / scale])
    if not cols:
        return False
    A = np.array(cols, dtype=float).T
    b = np.array([0.0, 1.0, 0.0])
    _, res = nnls(A, b)
    return res < 1e-6


def _rotate_contacts(contacts, com: np.ndarray, deg: float):
    """Contacts rotated about the centre of mass: the same as tilting gravity by -deg."""
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    R = np.array([[c, -s_], [s_, c]])
    return [(com + R @ (np.asarray(pt) - com), R @ np.asarray(n)) for pt, n in contacts]


def required_mu(contacts, com, scale) -> Optional[float]:
    """Smallest friction coefficient (<= MU_MAX) that holds the body; None if none does."""
    if not equilibrium_feasible(contacts, com, MU_MAX, scale):
        return None
    if equilibrium_feasible(contacts, com, 0.0, scale):
        return 0.0
    lo, hi = 0.0, MU_MAX
    for _ in range(30):
        mid = (lo + hi) / 2
        if equilibrium_feasible(contacts, com, mid, scale):
            hi = mid
        else:
            lo = mid
    return hi


def _nearest_edge(pt: np.ndarray, polys) -> Optional[Tuple[float, np.ndarray, bool]]:
    """(distance, outward unit normal, closest point is a vertex) of the polygon edge nearest pt."""
    best = None
    for poly in polys:
        P = np.asarray(poly, dtype=float)
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            d = b - a
            L2 = float(d @ d)
            if L2 < 1e-12:
                continue
            t = float(np.clip((pt - a) @ d / L2, 0.0, 1.0))
            dist = float(np.linalg.norm(pt - (a + t * d)))
            at_vertex = min(t * math.sqrt(L2), (1 - t) * math.sqrt(L2)) < 3 * CONTACT_GROW_2D
            if best is None or dist < best[0] - 1e-9:
                best = (dist, np.array([d[1], -d[0]]) / math.sqrt(L2), at_vertex)
    return best


def _contact_normal(pt: np.ndarray, obs_polys, rect_polys, rect_centre: np.ndarray) -> Optional[np.ndarray]:
    """Inward contact normal on the stand-in at a contact near pt.

    A stand-in corner on an obstacle face takes the face's normal; a stand-in
    face on an obstacle corner takes the stand-in face's normal; corner on
    corner is ambiguous (None: the caller probes instead).
    """
    obs = _nearest_edge(pt, obs_polys)
    own = _nearest_edge(pt, rect_polys)
    if obs and not obs[2]:
        n = obs[1]
    elif own and not own[2]:
        n = -own[1]
    else:
        return None
    if n @ (rect_centre - pt) < 0:
        n = -n
    return n


PROFILE_MAPS = {  # profile frame: s = direction the stand-in moves towards its support, z up, w = width axis
    "back": [[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]],      # s = +y
    "front": [[0, -1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, 0]],   # s = -y
    "right": [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0]],    # s = +x
    "left": [[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]],     # s = -x
}


def _support_angle(c: "Component", mode: str) -> Tuple[float, str]:
    """(angle of the face the stand-in lies against, in degrees from horizontal; direction s points to)."""
    p = c.params
    if c.shape == "panel":
        return float(p["angle"]), p["lean"]
    if c.shape == "wedge":
        h = p["height"]
        run = p["depth"] if p["high_side"] in ("back", "front") else p["width"]
        if c.place and c.place.get("side") == "bottom":
            return 0.0, "back"
        return math.degrees(math.atan2(h, run)), p["high_side"]
    if mode == "lie":
        return 0.0, "back"
    return 90.0, "back"


def check_rests_on(sc: Scene, chk: Check) -> CheckResult:
    """A box stand-in settles against its support under gravity; then: does it stay put?

    Planar quasi-static model in the side view perpendicular to the stand-in's
    width: every part within the stand-in's width is projected into the plane;
    the stand-in rectangle approaches the support, slides down along its own
    face and presses into the support until nothing moves; its contacts (with
    contact normals found by probing which direction frees it) must hold it
    with friction cones of coefficient mu (a non-negative least-squares
    feasibility test). This covers both "slope <= atan(mu)" and "centre of mass
    over the support"; the minimum friction needed is reported.
    """
    p = chk.params
    spec = standin(p["object"], p.get("size"))
    if spec["kind"] != "box":
        return _missing(chk, "rests_on supports box stand-ins only")
    supports = select(sc.d, p["support"])
    also = [c for n in (p.get("also_touches") or []) for c in select(sc.d, n)]
    deps = _deps(supports + also, [f"{c.name}.{k}" for c in supports + also for k in (c.params or {})] +
                 [f"{c.name}.place" for c in supports + also])
    if not supports:
        return _missing(chk, f"no part named {p['support']!r}", deps=deps)
    missing_also = [n for n in (p.get("also_touches") or []) if not select(sc.d, n)]
    mode = p.get("mode") or "lean"
    S = supports[0]
    theta, lean_dir = _support_angle(S, mode)
    direction = lean_dir
    facing = p.get("facing") or ("front" if mode == "lean" else None)
    if facing:
        # The side the object is on is part of the check, never taken from the support:
        # deriving it from the panel's own lean put the phone BEHIND a back rest turned
        # the wrong way (leaning forward onto it), so a reversed stand passed.
        direction = {"front": "back", "back": "front", "left": "right", "right": "left"}[facing]
    reversed_support = mode == "lean" and S.shape in ("panel", "wedge") and lean_dir != direction
    if reversed_support:
        theta = 90.0   # it leans towards the object: settle against its real faces, no borrowed slope
    if p.get("angle") is not None:
        theta = float(p["angle"])
    dims = sorted(spec["dims"])
    t = dims[0]
    orient = p.get("orientation") or ("portrait" if mode == "lean" else "landscape")
    # portrait: the longest side runs up the support (lean) or front to back (lie)
    L, W = (dims[2], dims[1]) if orient == "portrait" else (dims[1], dims[2])
    mat = np.array(PROFILE_MAPS[direction], dtype=float)
    s_lo, s_hi = sc.bbox(sc.of([S]))
    w_axis = int(np.argmax(np.abs(mat[2, :3])))
    w_c = (s_lo[w_axis] + s_hi[w_axis]) / 2 * mat[2, w_axis]
    slab = m3d.Manifold.cube([1e5, 1e5, W]).translate([-5e4, -5e4, w_c - W / 2])
    obstacles: List[Tuple[str, Any]] = []
    for inst in sc.insts:
        prof = (sc.solid(inst).transform(mat) ^ slab).project()
        if prof.area() > 1e-6:
            obstacles.append((inst.comp.name, prof))
    table = m3d.CrossSection.square([2e5, 1e4]).translate([-1e5, -1e4])
    obstacles.append(("table", table))
    world = m3d.CrossSection.batch_boolean([o for _, o in obstacles], m3d.OpType.Add)
    sup_prof = [o for n, o in obstacles if n == S.name]
    if not sup_prof:
        return _missing(chk, f"{S.name} is not within the object's width", deps=deps)
    def axes(th_deg):
        th = math.radians(th_deg)
        return np.array([math.cos(th), math.sin(th)]), np.array([-math.sin(th), math.cos(th)])

    def rect(p0, th_deg):
        a, b = axes(th_deg)
        return m3d.CrossSection.square([L, t]).transform(np.array([[a[0], b[0], p0[0]], [a[1], b[1], p0[1]]]))

    def hits(p0, th_deg):
        return (rect(p0, th_deg) ^ world).area() > 1e-4

    def advance(p0, th_deg, d, max_dist):
        """Move along d until the first touch (coarse steps, then bisection). Returns (p0, distance)."""
        if hits(p0, th_deg):
            return p0, 0.0
        s = 0.0
        while s < max_dist:
            s2 = min(s + SETTLE_STEP, max_dist)
            if hits(p0 + s2 * d, th_deg):
                lo_s, hi_s = s, s2
                while hi_s - lo_s > SETTLE_TOL:
                    mid = (lo_s + hi_s) / 2
                    if hits(p0 + mid * d, th_deg):
                        hi_s = mid
                    else:
                        lo_s = mid
                return p0 + lo_s * d, lo_s
            s = s2
        return p0 + max_dist * d, max_dist

    def centre(p0, th_deg):
        a, b = axes(th_deg)
        return p0 + (L / 2) * a + (t / 2) * b

    def find_contacts(p0, th_deg):
        """Contact points with inward normals, and contact length per part, at a resting pose.

        The normal of each contact region is the mean of the directions that free
        the stand-in when it moves a little, which is the face normal for a face
        contact and the supporting face's normal for a corner resting on a face.
        """
        grown = rect(p0, th_deg).offset(CONTACT_GROW_2D, m3d.JoinType.Miter, 2.0)
        found, touched = [], {}
        dirs = [np.array([math.cos(k * math.pi / 36), math.sin(k * math.pi / 36)]) for k in range(72)]
        for name, obs in obstacles:
            inter = grown ^ obs
            if inter.area() < 1e-6:
                continue
            for region in inter.decompose():
                rb = region.bounds()
                pad = 3 * CONTACT_GROW_2D
                clip = m3d.CrossSection.square([rb[2] - rb[0] + 2 * pad, rb[3] - rb[1] + 2 * pad]).translate(
                    [rb[0] - pad, rb[1] - pad])
                vs = verts(region)
                n = _contact_normal(vs.mean(axis=0), obs.to_polygons(), rect(p0, th_deg).to_polygons(),
                                    centre(p0, th_deg))
                if n is None:   # corner on corner: the direction that frees it, by probing
                    local = obs ^ clip
                    areas = [(grown.translate(list(1.5 * CONTACT_GROW_2D * d)) ^ local).area() for d in dirs]
                    free = [d for d, ar in zip(dirs, areas) if ar < 1e-7]
                    n = np.mean(free, axis=0) if free else dirs[int(np.argmin(areas))]
                if np.linalg.norm(n) < 1e-9:
                    continue
                n = n / np.linalg.norm(n)
                tang = np.array([-n[1], n[0]])
                proj = vs @ tang
                for v in (vs[int(np.argmin(proj))], vs[int(np.argmax(proj))]):
                    found.append((v, n))
                touched[name] = touched.get(name, 0.0) + region.area() / CONTACT_GROW_2D
        return found, touched

    def verts(cs) -> np.ndarray:
        return np.array([v for poly in cs.to_polygons() for v in poly], dtype=float)

    sup_v = verts(sup_prof[0])
    parts_v = np.vstack([verts(o) for n, o in obstacles if n != "table"])
    q = sup_v.mean(axis=0)
    reach = float(np.ptp(parts_v[:, 0]) + np.ptp(parts_v[:, 1])) + L + t + 50
    th = theta
    a, b = axes(th)
    fell = False
    if mode == "lean":
        # Placed flush against the support's facing plane (0.5 mm off it), above everything
        # along the slope; then it slides down that plane, presses into the support, is
        # pushed back against it and drops, until nothing moves (no friction while settling;
        # friction is judged afterwards).
        p0 = (float((sup_v @ b).max()) + 0.5) * b + (float((parts_v @ a).max()) + 1.0) * a
        if hits(p0, th):
            return _result(chk, -1.0, "mu", deps, None, f"rests against {S.name}",
                           f"there is no room to put the {p['object']} against {S.name}", passed=False)
        moves = ([-a] if th > 0.5 else []) + [-b, np.array([1.0, 0.0]), np.array([0.0, -1.0])]
        for _ in range(40):
            moved = 0.0
            for mv in moves:
                p0, m1 = advance(p0, th, mv, reach)
                moved += m1
            if moved < 0.02:
                break
    else:
        # Lowered from above, centred over the support and tilted like its top face; at
        # the first touch it pivots about the contact on the side of its centre of mass
        # until a contact appears on the other side (a rigid body dropped onto points).
        p0 = (float((parts_v @ b).max()) + 1.0) * b + (float(q @ a) - L / 2) * a
        p0, _ = advance(p0, th, -b, reach)
        p0, _ = advance(p0, th, np.array([0.0, -1.0]), reach)
        for _ in range(30):
            cts, _ = find_contacts(p0, th)
            com_now = centre(p0, th)
            xs = [pt[0] for pt, _ in cts]
            if not xs:
                p0, _ = advance(p0, th, np.array([0.0, -1.0]), reach)
                continue
            if min(xs) - 1e-3 <= com_now[0] <= max(xs) + 1e-3 and max(xs) - min(xs) > 1e-3:
                break
            pivot_x = max(xs) if com_now[0] > max(xs) else min(xs)
            pivot = next(pt for pt, _ in cts if abs(pt[0] - pivot_x) < 1e-9)
            sign = -1.0 if com_now[0] > pivot[0] else 1.0
            lift = np.array([0.0, 2 * SETTLE_TOL])

            def pose(delta):
                c, s_ = math.cos(math.radians(delta)), math.sin(math.radians(delta))
                r = p0 + lift - pivot
                return pivot + np.array([c * r[0] - s_ * r[1], s_ * r[0] + c * r[1]]), th + delta

            lo_d, hi_d, step = 0.0, None, 0.5
            while abs(lo_d) < 180:
                cand = lo_d + sign * step
                if hits(*pose(cand)):
                    hi_d = cand
                    break
                lo_d = cand
            if hi_d is None:
                fell = True
                break
            while abs(hi_d - lo_d) > 0.01:
                mid = (lo_d + hi_d) / 2
                if hits(*pose(mid)):
                    hi_d = mid
                else:
                    lo_d = mid
            p0, th = pose(lo_d)
            if abs(th) > 95:
                fell = True
                break
    contacts, touched = find_contacts(p0, th)
    com = centre(p0, th)
    theta = th
    if fell:
        return _result(chk, -2.0, "mu", deps, None, f"rests on {S.name}",
                       f"the {p['object']} tips off {S.name}: nothing stops it rotating", passed=False)
    names_needed = [S.name] + [c.name for c in also]
    lacking = [n for n in names_needed if n not in touched] + missing_also
    mu = float(p.get("mu") if p.get("mu") is not None else DEFAULT_MU)
    need_mu = required_mu(contacts, com, L)
    xs = [pt[0] for pt, _ in contacts]
    if need_mu is None:
        outside = 0.0 if not xs else max(0.0, min(xs) - com[0], com[0] - max(xs))
        m_eq = -1.0 - outside / L
        eq_text = "no friction up to {} can hold it (it tips or falls)".format(_fmt(MU_MAX))
    else:
        # friction margin, and how far the centre of mass is from tipping over the outermost contact
        tip = min(com[0] - min(xs), max(xs) - com[0]) / max(0.1 * L, 1e-9)
        m_eq = min((mu - need_mu) / mu, max(tip, 0.0))
        # Robustness, like check_stable: a nudge of tilt_deg shifts the centre of mass sideways by
        # its height above the lowest contact times tan(tilt_deg); it must stay over the contacts.
        # Without this a phone balanced upright on its 9 mm edge against a vertical wall passed
        # comfortably (it tips forward at about 3.4 degrees). Leaning, only the open side counts
        # (the support is on the +s side and catches it); lying, both sides do. A friction-cone
        # test with gravity tilted is no substitute: with wide cones a corner wedged between
        # wall and base "holds" the body by jamming, so it never reports the tip.
        tilt = float(p.get("tilt_deg") if p.get("tilt_deg") is not None else STABLE_TILT)
        ys = [pt[1] for pt, _ in contacts]
        nudge = max(com[1] - min(ys), 0.0) * math.tan(math.radians(tilt))
        room = com[0] - min(xs) if mode == "lean" else min(com[0] - min(xs), max(xs) - com[0])
        tipped = room - nudge < 0
        if tipped:
            m_eq = min(m_eq, (room - nudge) / max(0.1 * L, 1e-9), -1e-3)
        eq_text = f"needs friction {need_mu:.2f} (have {_fmt(mu)})"
    m_contact = -1.0 * len(lacking) / max(len(names_needed), 1) if lacking else 1.0
    margin = min(m_eq, m_contact)
    detail = (f"{p['object']} ({_fmt(L)} x {_fmt(t)} mm in side view, {_fmt(W)} mm wide) settles at "
              f"{_fmt(round(theta, 1))} deg touching {', '.join(sorted(touched)) or 'nothing'}; {eq_text}; "
              f"slope limit without a stop atan(mu) = {math.degrees(math.atan(mu)):.1f} deg")
    if need_mu is not None and tipped:
        detail += f"; a {_fmt(tilt)} degree nudge tips it over"
    if lacking:
        detail += f"; does not touch {', '.join(lacking)}"
    if reversed_support:
        detail += f"; {S.name} leans {lean_dir}, towards the object on its {facing} side"
    return _result(chk, max(min(margin, 1.0), -2.0), "mu", deps,
                   {"touching": sorted(touched), "required_mu": need_mu, "angle_deg": round(theta, 2)},
                   {"touching": names_needed, "mu": mu}, detail)


CHECKERS: Dict[str, Callable[[Scene, Check], CheckResult]] = {
    "count": check_count, "dimension": check_dimension, "shape": check_shape, "relation": check_relation,
    "edge": check_edge, "span": check_span, "arrangement": check_arrangement, "touches": check_touches,
    "connected": check_connected, "no_overlap": check_no_overlap, "stable": check_stable,
    "fits": check_fits, "rests_on": check_rests_on,
}


def run_check(d_or_scene, chk: Check) -> CheckResult:
    sc = d_or_scene if isinstance(d_or_scene, Scene) else Scene(d_or_scene)
    errors = validate_check(chk)
    if errors:
        return _missing(chk, "invalid check: " + "; ".join(errors))
    if not sc.insts:
        return _missing(chk, "the design is empty")
    if chk.type in LAYER2 and m3d is None:
        return _missing(chk, "manifold3d is not installed")
    try:
        return CHECKERS[chk.type](sc, chk)
    except Exception as exc:  # a sensor that crashes must read as a failure, never as a pass
        return _missing(chk, f"check crashed: {type(exc).__name__}: {exc}")


def run_checks(d: "Design", checks: Sequence[Check]) -> List[CheckResult]:
    sc = Scene(d)
    return [run_check(sc, chk) for chk in checks]


# ---------------------------------------------------------------------------
# Mutants and the gates that keep checks honest
# ---------------------------------------------------------------------------


@dataclass
class Mutant:
    name: str            # e.g. "flip:cup"
    kind: str            # remove | flip | reparent | opposite_edge | scale2 | scale05 | row | duplicate
    #                      | detach (pulled 5 mm off its parent) | overhang (centre moved to the parent's edge)
    #                      | tilt (an angle changed) | turn (a lean / axis / high side flipped)
    #                      | rearrange (row/ends along the other axis) | rotate (laid flat or stood up)
    target: str         # component the mutation is about
    design: "Design"


def clone_design(d: "Design") -> "Design":
    """A copy whose components can be edited without touching the original."""
    new = copy.copy(d)
    comps = []
    for c in d.components:
        cc = copy.copy(c)
        cc.params = dict(c.params) if c.params else c.params
        cc.place = dict(c.place) if c.place else c.place
        cc.positions = list(c.positions)
        comps.append(cc)
    new.components = comps
    return new


def geometry_signature(d: "Design") -> str:
    ensure_layout(d)
    return json.dumps(sorted([[c.shape, c.params, c.place and c.place.get("side"),
                               sorted([[round(x, 2) for x in p] for p in c.positions])]
                              for c in d.components if c.positions], key=str), sort_keys=True, default=str)


def _relayout(d: "Design") -> "Design":
    _ca().layout(d)
    return d


def mutants(d: "Design") -> List[Mutant]:
    """Python-generated wrong designs: the faults a check is supposed to catch.

    Mutants that build exactly the same geometry as the original are dropped
    (an equivalent mutant cannot be killed and says nothing about a check).
    """
    ca = _ca()
    ensure_layout(d)
    base_sig = geometry_signature(d)
    out: List[Mutant] = []
    root = d.components[0].name if d.components else None

    def add(kind, target, edit, post=None):
        m = clone_design(d)
        try:
            if edit(m) is False:
                return
            _relayout(m)
            if post is not None and post(m) is False:   # geometric faults the attach solver cannot express
                return
        except Exception:
            return
        if geometry_signature(m) != base_sig:
            out.append(Mutant(f"{kind}:{target}", kind, target, m))

    for c in d.components:
        name = c.name

        def remove(m, name=name):
            gone = m.component(name)
            for o in m.components:
                if o.place and o.place.get("parent") == name:
                    o.place["parent"] = gone.place["parent"] if gone.place else None
            m.components = [o for o in m.components if o.name != name]
            if m.components and m.components[0].place:
                m.components[0].place = None
        add("remove", name, remove)

        def flip(m, name=name):
            comp = m.component(name)
            swap = {"top": "bottom", "bottom": "top"}
            if name == root:
                kids = [o for o in m.components if o.place and o.place.get("parent") == name]
                if not kids:
                    return False
                for o in kids:
                    if o.place["side"] in swap:
                        o.place["side"] = swap[o.place["side"]]
                    else:
                        o.place["z"] = {"top": "bottom", "bottom": "top"}.get(o.place.get("z", "center"), "bottom")
                return None
            if comp.place["side"] in swap:
                comp.place["side"] = swap[comp.place["side"]]
            else:
                comp.place["z"] = {"top": "bottom", "bottom": "top"}.get(comp.place.get("z", "center"), "bottom")
        add("flip", name, flip)

        if c.place and root and c.place.get("parent") != root:
            def reparent(m, name=name):
                m.component(name).place["parent"] = root
            add("reparent", name, reparent)

        if c.place:
            def opposite(m, name=name):
                comp = m.component(name)
                for axis in ca.face_axes(comp.place["side"]):
                    vals = ca.ALIGN[axis]
                    cur = comp.place.get(axis, "center")
                    comp.place[axis] = {vals[0]: vals[2], vals[2]: vals[0]}.get(cur, vals[0])
            add("opposite_edge", name, opposite)

        if c.shape and c.params:
            for factor, kind in ((2.0, "scale2"), (0.5, "scale05")):
                def scale(m, name=name, factor=factor):
                    comp = m.component(name)
                    spec = ca.SHAPES[comp.shape].params
                    comp.params = {k: (v * factor if spec[k].kind == "mm" else v) for k, v in comp.params.items()}
                    if ca.validate_params(ca.SHAPES[comp.shape], comp.params)[0] is None:
                        return False
                add(kind, name, scale)

        if c.shape and c.params:
            # Non-length parameters: a tilt and every direction-like choice. Without these
            # a correct angle or axis check could never kill a mutant and would be rejected.
            spec = ca.SHAPES[c.shape].params
            for k, v in c.params.items():
                if spec[k].kind == "deg":
                    def tilt(m, name=name, k=k):
                        comp = m.component(name)
                        comp.params[k] = 90.0 if comp.params[k] < 80 else 60.0
                    add("tilt", name, tilt)
                elif spec[k].kind == "enum":
                    opposite = {"back": "front", "front": "back", "left": "right", "right": "left",
                                "x": "z", "y": "z", "z": "x"}
                    def turn(m, name=name, k=k):
                        comp = m.component(name)
                        alt = opposite.get(comp.params[k])
                        if alt not in spec[k].choices:
                            return False
                        comp.params[k] = alt
                    add("turn", name, turn)

        if c.place and c.positions:
            def detach(m, name=name):
                comp = m.component(name)
                axis, sign = ca.SIDE_AXIS[comp.place["side"]]
                step = [0.0, 0.0, 0.0]
                step[axis] = sign * DETACH_GAP
                _shift_subtree(m, name, step)
            add("detach", name, lambda m: None, detach)

            def overhang(m, name=name):
                comp = m.component(name)
                parent = m.component(comp.place["parent"])
                if not (parent and parent.positions):
                    return False
                axis = 0 if ca.SIDE_AXIS[comp.place["side"]][0] != 0 else 1
                edge = max(p[axis] + parent.size[axis] for p in parent.positions)
                centre = max(p[axis] + comp.size[axis] / 2 for p in comp.positions)
                step = [0.0, 0.0, 0.0]
                step[axis] = edge - centre
                if abs(step[axis]) < 1e-6:
                    return False
                _shift_subtree(m, name, step)
            add("overhang", name, lambda m: None, overhang)

        if c.count > 1 and c.place and not (c.arrangement or "").startswith("row"):
            def to_row(m, name=name):
                comp = m.component(name)
                axes = ca.arrangement_axes(comp.arrangement) or "".join(ca.face_axes(comp.place["side"]))
                comp.arrangement = f"row_{axes[0]}"
            add("row", name, to_row)

        if c.count > 1 and c.place and c.arrangement and c.arrangement.startswith(("row", "ends")):
            # The same pattern along the other axis of the face: without it a correct
            # "in a row front to back" check had no mutant to kill once the design was right.
            def other_axis(m, name=name):
                comp = m.component(name)
                kind, _, axis = comp.arrangement.partition("_")
                others = [a for a in ca.face_axes(comp.place["side"]) if a != axis]
                if not others:
                    return False
                comp.arrangement = f"{kind}_{others[0]}"
            add("rearrange", name, other_axis)

        if c.shape in ("box", "wedge") and c.params:
            # Lay an upright part flat, or stand a flat one up (swap height with a horizontal size).
            def rotate(m, name=name):
                comp = m.component(name)
                p = comp.params
                horiz = sorted(("width", "depth"), key=lambda k: p[k])
                if p["height"] <= min(p["width"], p["depth"]):
                    swap = horiz[1]
                else:
                    swap = horiz[0]
                if abs(p[swap] - p["height"]) < 1e-6:
                    return False
                p[swap], p["height"] = p["height"], p[swap]
            add("rotate", name, rotate)

        if c.shape and c.params and c.size:
            # The same bounding box in another shape (a box, or a box becomes a round post):
            # without it a correct "the wedge is a triangular wedge" check only ever
            # detected a missing part and was rejected, leaving one-part designs unverified.
            def reshape(m, name=name):
                comp = m.component(name)
                w, dp, h = comp.size
                if comp.shape != "box":
                    comp.shape, comp.params = "box", {"width": w, "depth": dp, "height": h}
                else:
                    comp.shape, comp.params = "cylinder", {"diameter": min(w, dp), "height": h, "axis": "z"}
            add("reshape", name, reshape)

        if c.shape and c.params:
            def duplicate(m, name=name):
                comp = m.component(name)
                dup = copy.copy(comp)
                dup.params = dict(comp.params)
                dup.name = f"{name}_dup"
                dup.count, dup.arrangement = 1, None
                dup.positions = []
                dup.place = {"parent": name, "side": "top" if not comp.place or comp.place["side"] != "bottom"
                             else "bottom", "x": "center", "y": "center", "z": "center"}
                m.components.append(dup)
            add("duplicate", name, duplicate)
    return out


DETACH_GAP = 5.0   # mm; how far the "detach" mutant pulls a part off its parent


def _shift_subtree(m: "Design", name: str, step: Sequence[float]) -> None:
    """Translate a laid-out component and everything attached to it (after layout)."""
    moving, grew = {name}, True
    while grew:
        grew = False
        for o in m.components:
            if o.name not in moving and o.place and o.place.get("parent") in moving:
                moving.add(o.name)
                grew = True
    for o in m.components:
        if o.name in moving:
            o.positions = [tuple(p[a] + step[a] for a in range(3)) for p in o.positions]


def empty_design(d: "Design") -> "Design":
    m = clone_design(d)
    m.components = []
    return m


@dataclass
class GateReport:
    check_id: str
    ok: bool
    fails_on_empty: bool
    killed: List[str]
    relevant: List[str]
    survived: List[str]
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def kills(original: CheckResult, mutated: CheckResult) -> bool:
    """A mutant is killed when the check fails on it (and, if the original also failed, gets worse)."""
    if mutated.passed:
        return False
    return original.passed or mutated.margin < original.margin - 1e-6


def non_vacuity(d: "Design", checks: Sequence[Check], muts: Optional[Sequence[Mutant]] = None
                ) -> List[GateReport]:
    """Gate (a): each check must fail on an empty design and kill a mutant relevant to what it depends on.

    Relevance: the mutated component is one the check depends on (checks over
    every part, like connected or stable, find every mutant relevant).
    """
    muts = list(mutants(d) if muts is None else muts)
    base = run_checks(d, checks)
    empty = run_checks(empty_design(d), checks)
    by_mutant = {m.name: run_checks(m.design, checks) for m in muts}
    reports = []
    for k, chk in enumerate(checks):
        deps = set(base[k].depends_on.get("components", []))
        global_check = (chk.type in ("connected", "no_overlap", "stable") and not chk.params.get("parts")) \
            or (chk.type in ("dimension", "shape", "count") and not chk.params.get("part"))  # whole object
        relevant = [m.name for m in muts if global_check or m.target in deps]
        killed = [m.name for m in muts if kills(base[k], by_mutant[m.name][k])]
        killed_rel = [n for n in killed if n in relevant]
        # Removing a part kills every check that names it; unless the check is about
        # existence (count), that only proves the part exists, not what the check claims.
        telling = [n for n in killed_rel if chk.type == "count" or not n.startswith("remove:")]
        fails_empty = not empty[k].passed
        ok = fails_empty and bool(telling)
        reason = "ok" if ok else (
            "passes on an empty design" if not fails_empty
            else "only detects a missing part" if killed_rel
            else "kills no relevant mutant" if relevant else "no relevant mutant exists")
        reports.append(GateReport(chk.id, ok, fails_empty, killed, relevant,
                                  [n for n in relevant if n not in killed], reason))
    return reports


# "both", "pair" and "twice" are not stated counts of a part ("both legs shall be 400 mm
# tall" states 400, not a count of 2), so they are left out.
NUMBER_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
                "ten": 10, "eleven": 11, "twelve": 12}
# A number glued to letters ("3D", "M3", "L1.2") is a name, not a quantity; a number in
# a unit no check slot measures (mass, force, percent) is not a size or a count.
_L1_NUMBER = re.compile(r"(?<![A-Za-z0-9.])(\d+(?:\.\d+)?)\s*(mm|cm|inches|inch|in\b|\"|°|deg\w*|kg|g\b|grams?|"
                        r"N\b|newtons?|%|percent)?(?![A-Za-z0-9])")
_FOREIGN_UNITS = ("kg", "g", "gram", "grams", "n", "newton", "newtons", "%", "percent")


def l1_numbers(text: str, words: bool = True) -> List[Tuple[float, str, str]]:
    """Numbers stated in an L1 (value in mm or degrees, unit, snippet), number words included."""
    found: List[Tuple[float, str, str]] = []
    scale = _ca().UNIT_SCALE
    for m in _L1_NUMBER.finditer(text):
        unit = (m.group(2) or "").lower()
        if unit in _FOREIGN_UNITS:
            continue
        value = float(m.group(1))
        if unit.startswith("deg") or unit == "°":
            unit = "deg"
        else:
            value *= scale.get(unit, 1.0)
        start, end = max(0, m.start() - 35), min(len(text), m.end() + 35)
        found.append((value, unit, text[start:end].strip()))
    if words:
        for m in re.finditer(r"\b(" + "|".join(NUMBER_WORDS) + r")\b", text.lower()):
            found.append((float(NUMBER_WORDS[m.group(1)]), "", m.group(0)))
    return found


def _numbers_in(obj) -> List[float]:
    if isinstance(obj, bool):
        return []
    if isinstance(obj, (int, float)):
        return [float(obj)]
    if isinstance(obj, dict):
        return [v for x in obj.values() for v in _numbers_in(x)]
    if isinstance(obj, (list, tuple)):
        return [v for x in obj for v in _numbers_in(x)]
    return []


def number_coverage(l1_text: str, checks: Sequence[Check]) -> List[Tuple[float, str, str]]:
    """Gate (b): numbers in the L1 text that no check's parameters use (empty list = covered)."""
    pool: List[Tuple[float, bool]] = []   # (value, is an angle)
    text = l1_text.lower()
    for chk in checks:
        for slot, v in chk.params.items():
            spec = SLOTS.get(chk.type, {}).get(slot)
            if spec is not None and spec[2] is not None and v == spec[2] and not isinstance(v, bool):
                # A default nobody chose (tilt 5, clearance 1, tol 0.5) covers nothing: it made
                # "the base plate shall be 5 mm thick" look checked by stable{}. Only a default
                # angle may still match an angle the L1 states ("tilted 5 degrees").
                if slot == "tilt_deg":
                    pool += [(x, True) for x in _numbers_in(v)]
                continue
            pool += [(x, slot in ("tilt_deg", "angle") or (slot == "value" and chk.params.get("measure") == "angle"))
                     for x in _numbers_in(v)]
        obj = chk.params.get("object")
        if chk.type in ("fits", "rests_on") and obj in STANDINS and not chk.params.get("size") \
                and re.search(rf"\b{re.escape(obj)}s?\b", text):
            # the stand-in's own sizes count only when the L1 names that object
            spec = STANDINS[obj]
            pool += [(x, False) for x in _numbers_in(spec.get("dims")) + _numbers_in([spec.get("diameter"),
                                                                                       spec.get("length")])]
        if chk.type == "fits" and chk.params.get("between"):
            pool.append((2.0, False))   # "between two dividers"
    out = []
    for value, unit, snippet in l1_numbers(l1_text):
        # angles cover only angles (or a bare number), lengths and counts never cover an angle
        if not any(abs(v - value) <= max(0.5, 0.01 * abs(value))
                   and (unit in ("deg", "") if is_angle else unit != "deg")
                   for v, is_angle in pool):
            out.append((value, unit, snippet))
    return out


# ---------------------------------------------------------------------------
# Error aggregation: lexicographic, with a strict monotone comparator
# ---------------------------------------------------------------------------


@dataclass(frozen=True, order=True)
class ErrorKey:
    """(hard failures, summed violation of hard checks, soft error). Lower is better, compared in order."""
    hard_failures: int
    violation: float
    soft: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def error_key(results: Sequence[CheckResult], soft_score: Optional[float] = None) -> ErrorKey:
    """soft_score: an LLM judgement in [0, 1] (1 = best); soft (non-hard) check violations add to it."""
    hard = [r for r in results if r.hard]
    soft_viol = sum(max(0.0, -r.margin) for r in results if not r.hard)
    soft = (1.0 - soft_score if soft_score is not None else 0.0) + soft_viol
    return ErrorKey(sum(1 for r in hard if not r.passed),
                    round(sum(max(0.0, -r.margin) for r in hard if not r.passed), 9), round(soft, 9))


def strictly_better(new: ErrorKey, old: ErrorKey, eps: float = 1e-6) -> bool:
    """Monotone acceptance: accept only a strict lexicographic decrease (Lyapunov-like, no ties, no drift)."""
    if new.hard_failures != old.hard_failures:
        return new.hard_failures < old.hard_failures
    if abs(new.violation - old.violation) > eps:
        return new.violation < old.violation
    return new.soft < old.soft - eps


# ---------------------------------------------------------------------------
# Finite-difference sensitivity: localisation and controllability
# ---------------------------------------------------------------------------


@dataclass
class Knob:
    component: str
    kind: str          # "param" | "side" | "edge" | "arrangement" | "parent" | "enum"
    name: str          # param or place key
    value: Any

    @property
    def label(self) -> str:
        v = _fmt(self.value) if isinstance(self.value, (int, float)) else self.value
        return f"{self.component}.{self.name}={v}"


@dataclass
class SensitivityReport:
    knobs: List[str]
    baseline: Dict[str, float]                       # check id -> margin
    matrix: Dict[str, Dict[str, float]]              # check id -> knob label -> delta margin
    movers: Dict[str, List[str]]                     # check id -> knobs that move it
    improvers: Dict[str, List[str]]                  # check id -> knobs that raise its margin
    localisation: Dict[str, List[str]]               # failing check id -> components ranked by best improvement
    uncontrollable: List[str]                        # failing checks nothing moves

    def to_dict(self) -> dict:
        return asdict(self)


def knobs(d: "Design", include_placement: bool = True, rel_step: float = 0.1) -> List[Knob]:
    """Every single-step change Python can make: numeric params +-10%, enum alternatives,
    other sides, other edge alignments, other arrangements, re-parenting to the root."""
    ca = _ca()
    out: List[Knob] = []
    root = d.components[0].name if d.components else None
    for c in d.components:
        if not (c.shape and c.params):
            continue
        spec = ca.SHAPES[c.shape].params
        for k, v in c.params.items():
            if spec[k].kind == "enum":
                out += [Knob(c.name, "enum", k, alt) for alt in spec[k].choices if alt != v]
            else:
                for f in (1 - rel_step, 1 + rel_step):
                    out.append(Knob(c.name, "param", k, round(v * f, 6)))
        if not (include_placement and c.place):
            continue
        out += [Knob(c.name, "side", "side", s) for s in ca.SIDES if s != c.place["side"]]
        for axis in ca.face_axes(c.place["side"]):
            out += [Knob(c.name, "edge", axis, v) for v in ca.ALIGN[axis] if v != c.place.get(axis, "center")]
        if c.count > 1:
            axes = "".join(ca.face_axes(c.place["side"]))
            options = [f"corners_{axes}", f"triangle_{axes}"] + [f"{k}_{a}" for k in ("ends", "row") for a in axes]
            out += [Knob(c.name, "arrangement", "arrangement", o) for o in options if o != c.arrangement]
        if c.place.get("parent") != root:
            out.append(Knob(c.name, "parent", "parent", root))
    return out


def apply_knob(d: "Design", knob: Knob) -> Optional["Design"]:
    ca = _ca()
    m = clone_design(d)
    c = m.component(knob.component)
    if knob.kind in ("param", "enum"):
        c.params[knob.name] = knob.value
        if ca.validate_params(ca.SHAPES[c.shape], c.params)[0] is None:
            return None
    elif knob.kind == "side":
        c.place["side"] = knob.value
    elif knob.kind == "edge":
        c.place[knob.name] = knob.value
    elif knob.kind == "arrangement":
        c.arrangement = knob.value
    elif knob.kind == "parent":
        c.place["parent"] = knob.value
    try:
        _relayout(m)
    except Exception:
        return None
    if not c.positions:
        return None
    return m


def sensitivity(d: "Design", checks: Sequence[Check], include_placement: bool = True,
                rel_step: float = 0.1) -> SensitivityReport:
    """Perturb every knob once and record how each check's margin moves.

    A failing check that no knob moves cannot be fixed with the current shape
    library and structure: report it as uncontrollable at once instead of
    letting a search burn its budget on it.
    """
    base = {r.check_id: r for r in run_checks(d, checks)}
    ks = knobs(d, include_placement, rel_step)
    matrix: Dict[str, Dict[str, float]] = {chk.id: {} for chk in checks}
    flips: Dict[str, set] = {chk.id: set() for chk in checks}
    labels = []
    for knob in ks:
        m = apply_knob(d, knob)
        if m is None:
            continue
        labels.append(knob.label)
        for r in run_checks(m, checks):
            delta = r.margin - base[r.check_id].margin
            matrix[r.check_id][knob.label] = round(delta, 6)
            if r.passed != base[r.check_id].passed:
                flips[r.check_id].add(knob.label)
    movers, improvers, local, unctrl = {}, {}, {}, []
    by_label = {k.label: k for k in ks}
    for chk in checks:
        row = matrix[chk.id]
        movers[chk.id] = [k for k, v in row.items() if abs(v) > 1e-9 or k in flips[chk.id]]
        improvers[chk.id] = sorted([k for k, v in row.items() if v > 1e-9], key=lambda k: -row[k])
        if not base[chk.id].passed:
            best: Dict[str, float] = {}
            for k in improvers[chk.id]:
                comp = by_label[k].component
                best[comp] = max(best.get(comp, 0.0), row[k])
            local[chk.id] = sorted(best, key=lambda c: -best[c])
            if not movers[chk.id]:
                unctrl.append(chk.id)
    return SensitivityReport(labels, {k: r.margin for k, r in base.items()}, matrix, movers, improvers,
                             local, unctrl)


# ---------------------------------------------------------------------------
# Satisfiability: can a design near the current one pass the check without breaking others?
# ---------------------------------------------------------------------------

SAT_FACTORS = (0.5, 0.75, 0.9, 1.1, 1.25, 1.5, 2.0)


def neighbour_designs(d: "Design", components: Sequence[str], muts: Sequence[Mutant] = ()) -> List[Tuple[str, "Design"]]:
    """Designs one step from d: each numeric parameter of the named components scaled by
    SAT_FACTORS, plus the given mutants (laid out; invalid parameter sets skipped)."""
    ca = _ca()
    out: List[Tuple[str, "Design"]] = [(m.name, m.design) for m in muts]
    for name in components:
        try:
            c = d.component(name)
        except Exception:
            continue
        if not (c and c.shape and c.params):
            continue
        for k, v in c.params.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                continue
            for f in SAT_FACTORS:
                trial = dict(c.params)
                trial[k] = round(v * f, 4)
                if ca.validate_params(ca.SHAPES[c.shape], trial)[0] is None:
                    continue
                m = clone_design(d)
                m.component(name).params = trial
                try:
                    out.append((f"scale:{name}.{k}x{f}", _relayout(m)))
                except Exception:
                    continue
    return out


@dataclass
class SatReport:
    check_id: str
    ok: bool
    reason: str                        # "passes now" | "reachable" | "unknown" | "conflict"
    witness: Optional[str] = None      # the neighbour that passes everything
    conflicts: List[str] = field(default_factory=list)   # ids of checks every passing neighbour breaks


def satisfiability(d: "Design", chk: Check, others: Sequence[Check], muts: Sequence[Mutant] = ()) -> SatReport:
    """Gate: a check that fails now must be passable by some nearby design that keeps the
    other (already accepted, currently passing) checks passing.

    Rejects only a demonstrated conflict - neighbours exist that pass the check, and
    every one of them breaks an accepted check - because a check no neighbour passes
    may just need more than one step. Measured case: "a 43 mm egg drops into a 45 mm
    cup with 2 mm walls" can only pass by widening the cup or thinning the walls,
    which breaks the 45 mm and 2 mm checks; frozen, it drove the cups to 25 mm tall.
    """
    if run_check(d, chk).passed:
        return SatReport(chk.id, True, "passes now")
    others = [o for o in others if o.id != chk.id]
    system = [Check("_sys_overlap", "SYS", "no_overlap", {}), Check("_sys_connected", "SYS", "connected", {})]
    if not all(r.passed for r in run_checks(d, list(others) + system)):
        # The provisional design is itself inconsistent (two "side" parts stacked on a block
        # once made a correct "18 mm tall" check look unsatisfiable): judge nothing against it.
        return SatReport(chk.id, True, "unknown")
    keep = list(others)
    deps = run_check(d, chk).depends_on.get("components") or [c.name for c in d.components]
    passing_any, broken = False, []  # type: bool, List[List[str]]
    fixes = deadbeat(d, chk)
    direct = [("deadbeat", apply_fixes(d, fixes))] if fixes else []
    for name, nd in direct + neighbour_designs(d, deps, muts):
        if not run_check(nd, chk).passed:
            continue
        passing_any = True
        bad = [o.id for o, r in zip(keep, run_checks(nd, keep)) if not r.passed]
        if not bad:
            return SatReport(chk.id, True, "reachable", witness=name)
        broken.append(bad)
    if not passing_any:
        return SatReport(chk.id, True, "unknown")
    common = sorted(set.intersection(*map(set, broken))) or sorted({b for bs in broken for b in bs})
    return SatReport(chk.id, False, "conflict", conflicts=common)


# ---------------------------------------------------------------------------
# Deadbeat correction: invertible single-parameter failures are set directly
# ---------------------------------------------------------------------------


@dataclass
class Fix:
    check_id: str
    component: str
    param: str
    old: float
    new: float

    def to_dict(self) -> dict:
        return asdict(self)


def deadbeat(d: "Design", chk: Check, result: Optional[CheckResult] = None) -> List[Fix]:
    """For a failing dimension (or span) check that depends on exactly one parameter per
    component, the parameter value that satisfies it. Structural failures return []."""
    ca = _ca()
    sc = Scene(d)
    result = result or run_check(sc, chk)
    if result.passed or chk.type not in ("dimension", "span") or not chk.params.get("part"):
        return []
    fixes = []
    p = chk.params
    for c in select(d, p["part"]):
        if chk.type == "dimension":
            v, deps = measure_dimension(sc, c, p["measure"], p.get("param"))
            if v is None or len(deps) != 1 or p["measure"] in ("top", "bottom"):
                continue
            param = deps[0].split(".", 1)[1]
            current = float(c.params[param])
            target, op = float(p["value"]), p.get("op") or "eq"
            if op == "eq" and abs(v - target) <= _dim_tol(p):
                continue
            if (op == "ge" and v >= target - _dim_tol(p)) or (op == "le" and v <= target + _dim_tol(p)):
                continue
            # the measure is the parameter itself, except an extent that equals it (box width, rod diameter)
            new = target
        else:
            sp = ca.size_param(c, p["axis"])
            others = select(d, p["other"])
            if not sp or not others:
                continue
            lo, hi = sc.bbox(sc.of(others))
            x = "xyz".index(p["axis"])
            new, current = hi[x] - lo[x], float(c.params[sp])
            param = sp
        trial = dict(c.params)
        trial[param] = new
        if ca.validate_params(ca.SHAPES[c.shape], trial)[0] is None:
            continue
        fixes.append(Fix(chk.id, c.name, param, current, round(new, 6)))
    return fixes


def apply_fixes(d: "Design", fixes: Sequence[Fix]) -> "Design":
    """A laid-out copy of the design with the deadbeat fixes applied."""
    m = clone_design(d)
    for f in fixes:
        m.component(f.component).params[f.param] = f.new
    return _relayout(m)


# ---------------------------------------------------------------------------
# Design records and the sprint-review verification matrix
# ---------------------------------------------------------------------------


def design_from_json(path, workdir: Optional[Path] = None) -> "Design":
    """Load a design.json written by cad_agent back into a laid-out Design."""
    ca = _ca()
    path = Path(path)
    data = json.loads(path.read_text())
    d = ca.Design(request=data.get("base_request") or data.get("request", ""),
                  workdir=Path(workdir) if workdir else path.parent)
    d.l1 = list(data.get("l1") or [])
    for c in data["components"]:
        d.components.append(ca.Component(name=c["name"], description=c.get("description", ""),
                                         shape=c.get("shape"), params=c.get("params"), place=c.get("place"),
                                         count=int(c.get("count") or 1), arrangement=c.get("arrangement")))
    ca.layout(d)
    return d


def verification_matrix(l1: Sequence[dict], checks: Sequence[Check], results: Sequence[CheckResult]) -> List[dict]:
    """One row per L1: pass only if all its checks pass; worst margin; evidence. Failing rows first."""
    by_l1: Dict[str, List[Tuple[Check, CheckResult]]] = {}
    for chk, r in zip(checks, results):
        by_l1.setdefault(chk.l1_id, []).append((chk, r))
    rows = []
    for req in l1:
        pairs = by_l1.get(req["id"], [])
        rows.append({
            "l1_id": req["id"], "text": req.get("text", ""), "method": req.get("method"),
            "passed": bool(pairs) and all(r.passed for _, r in pairs),
            "margin": min((r.margin for _, r in pairs), default=None),
            "checks": [{"id": c.id, "type": c.type, "text": c.text, "passed": r.passed, "margin": r.margin,
                        "evidence": r.evidence.get("detail")} for c, r in pairs],
            "note": "" if pairs else "no check covers this requirement",
        })
    rows.sort(key=lambda r: (r["passed"], r["margin"] if r["margin"] is not None else -1e9))
    return rows


def matrix_text(rows: Sequence[dict]) -> str:
    lines = []
    for r in rows:
        mark = "PASS" if r["passed"] else "FAIL"
        margin = f"{r['margin']:+.3f}" if r["margin"] is not None else "  n/a "
        lines.append(f"{mark} {margin}  {r['l1_id']}: {r['text']}{'  (' + r['note'] + ')' if r['note'] else ''}")
        for c in r["checks"]:
            lines.append(f"      {'ok ' if c['passed'] else 'NO '} {c['id']} [{c['type']}] {c['evidence']}")
    return "\n".join(lines)
