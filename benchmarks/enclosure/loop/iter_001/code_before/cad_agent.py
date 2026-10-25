"""OpenSCAD CAD agent driven by a behaviour tree.

The script is the brain and a small local LLM is the muscle. The model is never
asked to write geometry or coordinates. It answers narrow, schema-constrained
questions ("list the components", "which of these shapes is the back rest?",
"fill in the panel's dimensions", "what does the lip attach to?"), and Python
turns the answers into exact OpenSCAD, measures the result and decides what to
ask next. Each question is stateless: the script puts everything the model needs
into the prompt, so nothing drifts between calls.

The tree (components are expanded into their own subtrees at runtime):

    cad (Sequence)
    ├── design_loop (Retry)                    re-enter on any failure; clean leaves are no-ops
    │   └── design (Sequence)
    │       ├── understand (Sequence)
    │       │   ├── ExtractComponents          LLM: request -> named components
    │       │   └── components (ForEach)
    │       │       └── <component> (Sequence)
    │       │           ├── ChooseShape        LLM vote over the shape library
    │       │           ├── FillParams         LLM fills the shape's typed parameters
    │       │           └── PlaceComponent     LLM vote: parent, side, alignment
    │       ├── AccountForNumbers              every number in the request must be used
    │       ├── build (Sequence)
    │       │   ├── Layout                     Python attach solver -> positions
    │       │   ├── EmitScad                   Python writes the OpenSCAD
    │       │   ├── CompileCheck               STL: expected bbox, one connected body
    │       │   └── PhysicalChecks             will it stand up on its own?
    │       ├── RenderViews                    fixed cameras + highlight renders per part
    │       ├── visual_review (Sequence)
    │       │   ├── visual (ForEach)
    │       │   │   └── CheckComponentVisual   VLM yes/no, with a false-description probe
    │       │   └── VisualVerdict              repair the "no"s, keep the best design so far
    │       └── HumanReview                    accept, or feedback -> targeted changes
    └── ExportModel                            3MF

With --mode cascade (and --l1), cascade.py reuses understand/numbers/build to make
a provisional design, turns the person's L1 requirements into frozen typed checks
(cad_checks.py) and then drives the design to those checks in a closed loop,
ending with a verification matrix instead of per-part yes/no verdicts.

Conventions shared by every prompt and by the geometry code: millimetres;
X runs left -> right (width), Y runs front -> back (depth), Z runs up (height).
"""

import argparse
import base64
import copy
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

import py_trees
from py_trees.common import Status

HOST = "http://localhost:11434"
MODEL = "ornith-1.5:9b"

ABS_TOL = 0.5          # mm
MAX_COMPONENTS = 8
SEGMENTS = 64          # $fn for round shapes
OPENSCAD_TIMEOUT = 300
VOTES = 3              # samples per voted choice
SEED_TEMPERATURE = 0.3 # temperature floor for sampled answers when a run seed is set (see OllamaAgent)

CONVENTIONS = (
    "Units are millimetres. X runs left to right (width), Y runs front to back "
    "(depth; the front is the side facing the user), Z runs up (height). "
    "The object rests on a table at z = 0."
)

# Cameras in OpenSCAD's gimbal form: transx,transy,transz,rotx,roty,rotz,distance.
# --viewall overrides the distance.
VIEWS: Dict[str, Tuple[float, ...]] = {
    "iso": (0, 0, 0, 60, 0, 35, 0),
    "front": (0, 0, 0, 90, 0, 0, 0),
    "back": (0, 0, 0, 90, 0, 180, 0),
    "left": (0, 0, 0, 90, 0, 270, 0),
    "right": (0, 0, 0, 90, 0, 90, 0),
    "top": (0, 0, 0, 0, 0, 0, 0),
}
HIGHLIGHT_VIEWS = ("iso", "right")

PART_COLORS = [
    "SteelBlue", "Orange", "ForestGreen", "Crimson", "Gold",
    "MediumPurple", "Teal", "SaddleBrown",
]

ACCEPT_WORDS = {"", "y", "yes", "ok", "accept", "looks good", "lgtm"}
QUIT_WORDS = {"q", "quit", "exit", "abort"}


class UserAbort(Exception):
    """The person asked to stop."""


def fmt(v: float) -> str:
    v = round(float(v), 3)
    return str(int(v)) if v == int(v) else f"{v:g}"


def fmt_vec(v: Sequence[float]) -> str:
    return "[" + ", ".join(fmt(x) for x in v) + "]"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
    if slug and slug[0].isdigit():
        slug = "c_" + slug
    return slug


# ---------------------------------------------------------------------------
# Shape library: Python owns every line of geometry
# ---------------------------------------------------------------------------


@dataclass
class Param:
    doc: str
    kind: str = "mm"            # "mm", "deg" or "enum"
    choices: Tuple[str, ...] = ()
    lo: float = 0.0             # exclusive lower bound
    hi: float = 2000.0          # inclusive upper bound

    def schema(self) -> dict:
        if self.kind == "enum":
            return {"type": "string", "enum": list(self.choices), "description": self.doc}
        return {"type": "number", "description": self.doc}

    def unit(self) -> str:
        return {"mm": " (mm)", "deg": " (degrees)"}.get(self.kind, "")


@dataclass
class Shape:
    name: str
    doc: str
    params: Dict[str, Param]
    size: Callable[[dict], Tuple[float, float, float]]
    scad: Callable[[dict], str]
    check: Callable[[dict], List[str]] = lambda p: []


def polygon(points: Sequence[Tuple[float, float]]) -> str:
    return "polygon([" + ", ".join(fmt_vec(p) for p in points) + "]);"


def extrude_profile(points, axis: str, length: float) -> str:
    """Extrude a 2D profile along X (profile in YZ) or Y (profile in XZ); min corner at origin."""
    if axis == "x":
        return f"rotate([90, 0, 90]) linear_extrude({fmt(length)}) {polygon(points)}"
    return f"translate([0, {fmt(length)}, 0]) rotate([90, 0, 0]) linear_extrude({fmt(length)}) {polygon(points)}"


def _panel_geometry(p: dict) -> Tuple[float, float]:
    """(foot, run): horizontal footprint of the slab's thickness, and how far its top leans."""
    a = math.radians(p["angle"])
    return p["thickness"] / math.sin(a), p["height"] / math.tan(a)


def _panel_size(p):
    foot, run = _panel_geometry(p)
    if p["lean"] in ("back", "front"):
        return (p["width"], foot + run, p["height"])
    return (foot + run, p["width"], p["height"])


def _panel_scad(p):
    foot, run = _panel_geometry(p)
    h = p["height"]
    if p["lean"] in ("back", "right"):     # top moves towards +Y / +X
        pts = [(0, 0), (foot, 0), (foot + run, h), (run, h)]
    else:
        pts = [(run, 0), (run + foot, 0), (foot, h), (0, h)]
    return extrude_profile(pts, "x" if p["lean"] in ("back", "front") else "y", p["width"])


def _wedge_scad(p):
    w, d, h = p["width"], p["depth"], p["height"]
    side = p["high_side"]
    if side in ("back", "front"):
        pts = [(0, 0), (d, 0), (d, h)] if side == "back" else [(0, 0), (d, 0), (0, h)]
        return extrude_profile(pts, "x", w)
    pts = [(0, 0), (w, 0), (w, h)] if side == "right" else [(0, 0), (w, 0), (0, h)]
    return extrude_profile(pts, "y", d)


def _axis_size(p, d):
    return {"z": (d, d, p["height"]), "x": (p["height"], d, d), "y": (d, p["height"], d)}[p["axis"]]


def _axis_place(p, r, body):
    if p["axis"] == "z":
        return f"translate([{fmt(r)}, {fmt(r)}, 0]) {body}"
    if p["axis"] == "x":
        return f"translate([0, {fmt(r)}, {fmt(r)}]) rotate([0, 90, 0]) {body}"
    return f"translate([{fmt(r)}, 0, {fmt(r)}]) rotate([-90, 0, 0]) {body}"


def _tube_scad(p):
    od, idia, h = p["outer_diameter"], p["inner_diameter"], p["height"]
    body = (f"difference() {{ cylinder(d={fmt(od)}, h={fmt(h)}); "
            f"translate([0, 0, -1]) cylinder(d={fmt(idia)}, h={fmt(h + 2)}); }}")
    return _axis_place(p, od / 2, body)


AXIS = Param("direction of the round axis: z = standing upright, x = lying left-right, "
             "y = lying front-back", "enum", ("z", "x", "y"))
SIDES4 = ("back", "front", "left", "right")

SHAPES: Dict[str, Shape] = {s.name: s for s in [
    Shape(
        "box", "rectangular block: plates, bases, walls, bars, lips, ledges, pillars",
        {"width": Param("size along X (left to right)"),
         "depth": Param("size along Y (front to back)"),
         "height": Param("size along Z (vertical)")},
        lambda p: (p["width"], p["depth"], p["height"]),
        lambda p: f"cube({fmt_vec([p['width'], p['depth'], p['height']])});",
    ),
    Shape(
        "panel", "flat slab tilted at an angle from the horizontal: back rests, "
        "leaning supports, ramps, sloped walls",
        {"width": Param("length of the slab's horizontal edges"),
         "height": Param("vertical height from the bottom edge to the top edge"),
         "thickness": Param("slab thickness"),
         "angle": Param("tilt measured from the horizontal table: 90 = vertical, "
                        "smaller = leaning more", "deg", lo=5, hi=90),
         "lean": Param("the direction the TOP of the slab leans towards", "enum", SIDES4)},
        _panel_size, _panel_scad,
    ),
    Shape(
        "wedge", "triangular prism with one sloped face: gussets, braces, ramps, door stops",
        {"width": Param("size along X"), "depth": Param("size along Y"),
         "height": Param("size along Z at the tall side"),
         "high_side": Param("which side is tall", "enum", SIDES4)},
        lambda p: (p["width"], p["depth"], p["height"]), _wedge_scad,
    ),
    Shape(
        "cylinder", "solid round rod or disc: pegs, posts, feet, knobs, discs",
        {"diameter": Param("diameter"), "height": Param("length along its axis"), "axis": AXIS},
        lambda p: _axis_size(p, p["diameter"]),
        lambda p: _axis_place(p, p["diameter"] / 2,
                              f"cylinder(d={fmt(p['diameter'])}, h={fmt(p['height'])});"),
    ),
    Shape(
        "tube", "hollow round cylinder open at both ends: cups (on a base), pipes, rings, sleeves",
        {"outer_diameter": Param("outside diameter"),
         "inner_diameter": Param("inside (hole) diameter"),
         "height": Param("length along its axis"), "axis": AXIS},
        lambda p: _axis_size(p, p["outer_diameter"]),
        _tube_scad,
        lambda p: [] if p["inner_diameter"] < p["outer_diameter"]
        else ["inner_diameter must be smaller than outer_diameter"],
    ),
    Shape(
        "sphere", "ball: knobs, round handles, decorations",
        {"diameter": Param("diameter")},
        lambda p: (p["diameter"],) * 3,
        lambda p: f"translate({fmt_vec([p['diameter'] / 2] * 3)}) sphere(d={fmt(p['diameter'])});",
    ),
]}


def validate_params(shape: Shape, raw: dict) -> Tuple[Optional[dict], List[str]]:
    """Check a parameter answer against the shape's typed spec."""
    params, errors = {}, []
    for name, spec in shape.params.items():
        value = raw.get(name)
        if spec.kind == "enum":
            if value not in spec.choices:
                errors.append(f"{name} must be one of {', '.join(spec.choices)}")
            params[name] = value
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            errors.append(f"{name} must be a number")
            continue
        if not (spec.lo < value <= spec.hi):
            errors.append(f"{name} must be above {fmt(spec.lo)} and at most {fmt(spec.hi)} (got {fmt(value)})")
        params[name] = value
    if not errors:
        errors = shape.check(params)
    return (None, errors) if errors else (params, [])


# ---------------------------------------------------------------------------
# Placement: children attach to a face of an earlier component
# ---------------------------------------------------------------------------

SIDES = ("top", "bottom", "front", "back", "left", "right")
ALIGN = {"x": ("left", "center", "right"), "y": ("front", "center", "back"),
         "z": ("bottom", "center", "top")}
SIDE_AXIS = {"top": (2, +1), "bottom": (2, -1), "front": (1, -1), "back": (1, +1),
             "left": (0, -1), "right": (0, +1)}


def attach_position(parent_pos, parent_size, child_size, place,
                    fractions: Optional[Dict[str, float]] = None) -> Tuple[float, float, float]:
    """Min corner of a child placed against `place['side']` of its parent.

    Along the other two axes the child is aligned by word (left/center/right ...)
    or, for arranged copies, by a fraction (0 = start edge, 1 = end edge).
    """
    axis, direction = SIDE_AXIS[place["side"]]
    pos = [0.0, 0.0, 0.0]
    for a, key in enumerate("xyz"):
        if a == axis:
            pos[a] = parent_pos[a] + parent_size[a] if direction > 0 else parent_pos[a] - child_size[a]
            continue
        if fractions and key in fractions:
            t = fractions[key]
        else:
            align = place.get(key, "center")
            t = ALIGN[key].index(align) / 2 if align in ALIGN[key] else 0.5
        pos[a] = parent_pos[a] + (parent_size[a] - child_size[a]) * t
    return (pos[0], pos[1], pos[2])


# ---------------------------------------------------------------------------
# OpenSCAD and mesh measurement
# ---------------------------------------------------------------------------


def find_openscad() -> str:
    """Locate the OpenSCAD binary: $OPENSCAD, then PATH, then the macOS app bundle."""
    env = os.environ.get("OPENSCAD")
    if env:
        return env
    on_path = shutil.which("openscad")
    if on_path:
        return on_path
    apps = sorted(Path("/Applications").glob("OpenSCAD*.app/Contents/MacOS/OpenSCAD"))
    return str(apps[-1]) if apps else "openscad"


OPENSCAD = find_openscad()


def run_openscad(args: Sequence[str]) -> subprocess.CompletedProcess:
    """Run OpenSCAD and return the result; never raises on a non-zero exit."""
    try:
        return subprocess.run([OPENSCAD, *args], capture_output=True, text=True,
                              check=False, timeout=OPENSCAD_TIMEOUT)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 1, "", f"ERROR: OpenSCAD timed out after {OPENSCAD_TIMEOUT}s")
    except FileNotFoundError:
        return subprocess.CompletedProcess(args, 1, "", f"ERROR: OpenSCAD not found at {OPENSCAD!r}; set $OPENSCAD")


def openscad_problems(stderr: str, returncode: int) -> List[str]:
    """Pull the actionable lines out of OpenSCAD's chatty stderr."""
    problems = []
    for line in stderr.splitlines():
        line = line.strip()
        if line.startswith(("ERROR:", "WARNING:")):
            problems.append(line)
        elif "top level object is empty" in line:
            problems.append("ERROR: the code produced no geometry")
    if returncode != 0 and not problems:
        tail = [line for line in stderr.strip().splitlines() if line.strip()][-3:]
        problems.append("ERROR: " + (" | ".join(tail) or f"OpenSCAD exited with {returncode}"))
    return problems


Vec = Tuple[float, float, float]
Tri = Tuple[Vec, Vec, Vec]
BBox = Tuple[Vec, Vec]


def read_stl(stl_path: Path) -> List[Tri]:
    """Triangles of an ASCII or binary STL."""
    data = Path(stl_path).read_bytes()
    tris: List[Tri] = []
    if data[:5] == b"solid" and b"facet" in data[:1024]:
        verts = []
        for line in data.decode("ascii", errors="ignore").splitlines():
            parts = line.split()
            if len(parts) == 4 and parts[0] == "vertex":
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
        tris = [(verts[i], verts[i + 1], verts[i + 2]) for i in range(0, len(verts) - 2, 3)]
    elif len(data) >= 84:
        (count,) = struct.unpack_from("<I", data, 80)
        for i in range(count):
            offset = 84 + i * 50 + 12
            if offset + 36 > len(data):
                break
            v = struct.unpack_from("<9f", data, offset)
            tris.append(((v[0], v[1], v[2]), (v[3], v[4], v[5]), (v[6], v[7], v[8])))
    return tris


def mesh_bbox(tris: Sequence[Tri]) -> Optional[BBox]:
    pts = [p for t in tris for p in t]
    if not pts:
        return None
    xs, ys, zs = zip(*pts)
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def mesh_bodies(tris: Sequence[Tri]) -> int:
    """Number of separate shells (triangles connected through shared vertices)."""
    parent: Dict[tuple, tuple] = {}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for t in tris:
        keys = [tuple(round(c, 4) for c in p) for p in t]
        for k in keys:
            parent.setdefault(k, k)
        for k in keys[1:]:
            ra, rb = find(keys[0]), find(k)
            if ra != rb:
                parent[ra] = rb
    return len({find(k) for k in parent})


def mesh_mass(tris: Sequence[Tri]) -> Tuple[float, Vec]:
    """Volume and centre of mass of a closed mesh (signed tetrahedra)."""
    vol = cx = cy = cz = 0.0
    for a, b, c in tris:
        v = (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
             + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
        vol += v
        cx += v * (a[0] + b[0] + c[0]) / 4
        cy += v * (a[1] + b[1] + c[1]) / 4
        cz += v * (a[2] + b[2] + c[2]) / 4
    if abs(vol) < 1e-9:
        return 0.0, (0.0, 0.0, 0.0)
    return abs(vol), (cx / vol, cy / vol, cz / vol)


def convex_hull(points: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: List[Tuple[float, float]] = []
    upper: List[Tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def inside_hull(point, hull) -> bool:
    if len(hull) < 3:
        return False
    for i in range(len(hull)):
        a, b = hull[i], hull[(i + 1) % len(hull)]
        if (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0]) < -1e-6:
            return False
    return True


@dataclass
class CompileResult:
    ok: bool
    problems: List[str]
    tris: List[Tri] = field(default_factory=list)

    @property
    def bbox(self) -> Optional[BBox]:
        return mesh_bbox(self.tris)


def compile_scad(scad_path: Path, stl_path: Path) -> CompileResult:
    """Compile a .scad to STL (a full CGAL render) and read the mesh back."""
    if stl_path.exists():
        stl_path.unlink()
    result = run_openscad(["-o", str(stl_path), str(scad_path)])
    problems = [p for p in openscad_problems(result.stderr, result.returncode) if p.startswith("ERROR:")]
    if problems or not stl_path.exists():
        return CompileResult(False, problems or ["ERROR: no STL was written"])
    tris = read_stl(stl_path)
    if not tris:
        return CompileResult(False, ["ERROR: the code produced no geometry"])
    return CompileResult(True, [], tris)


def render_openscad(cad_path: Path, views: Optional[Dict[str, Tuple[float, ...]]] = None,
                    out_dir: Optional[Path] = None, stem: Optional[str] = None,
                    imgsize: int = 768) -> Tuple[Dict[str, Path], List[str]]:
    """Render a .scad to one PNG per named camera.

    Returns ({view: png path} for renders that worked, [failure messages]). Uses
    the preview renderer so color() survives into the image.
    """
    cad_path = Path(cad_path)
    if not cad_path.exists():
        raise FileNotFoundError(f"cad_path {cad_path} does not exist")
    views = VIEWS if views is None else views
    if not isinstance(views, dict) or not views:
        raise ValueError("views must be a non-empty dict of name -> camera tuple")
    out_dir = Path(out_dir) if out_dir else cad_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: Dict[str, Path] = {}
    failures: List[str] = []
    for name, camera in views.items():
        png = out_dir / f"{stem or cad_path.stem}_{name}.png"
        result = run_openscad([
            "-o", str(png), "--camera=" + ",".join(str(c) for c in camera),
            "--viewall", "--autocenter", f"--imgsize={imgsize},{imgsize}",
            "--projection=ortho", "--colorscheme=Tomorrow", str(cad_path),
        ])
        if result.returncode == 0 and png.exists():
            rendered[name] = png
        else:
            failures.append(f"{name}: {'; '.join(openscad_problems(result.stderr, result.returncode))[:300]}")
    return rendered, failures


def export_openscad(cad_path: Path, out_path: Optional[Path] = None) -> Tuple[bool, str]:
    """Export a .scad to a mesh file (3MF by default; the suffix picks the format)."""
    cad_path = Path(cad_path)
    if not cad_path.exists():
        raise FileNotFoundError(f"cad_path {cad_path} does not exist")
    out_path = Path(out_path) if out_path else cad_path.with_suffix(".3mf")
    if out_path.exists():
        out_path.unlink()
    result = run_openscad(["-o", str(out_path), str(cad_path)])
    errors = [p for p in openscad_problems(result.stderr, result.returncode) if p.startswith("ERROR:")]
    if errors or not out_path.exists() or out_path.stat().st_size == 0:
        return False, "; ".join(errors or ["no file was written"])[:300]
    return True, str(out_path)


# ---------------------------------------------------------------------------
# LLM: Ollama's native chat API, for schema-constrained (grammar) decoding
# ---------------------------------------------------------------------------


def _http_post(url: str, body: dict, timeout: float) -> dict:
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


class OllamaAgent:
    """Stateless questions to a local model; answers can be forced to match a JSON schema.

    Uses Ollama's native /api/chat (not the anthropic-compatible endpoint) because
    only the native API supports `format` (grammar-constrained JSON), per-call
    temperature and seed.

    `seed_offset` (the --seed of a run) is added to every sampling seed so that
    repeated benchmark runs are independent samples. A seed alone changes
    nothing at temperature 0 (greedy decoding ignores it), so with a non-zero
    offset the greedy first answers are sampled at SEED_TEMPERATURE instead.
    Offset 0 reproduces the unseeded behaviour exactly. p_yes is a measurement
    (token probabilities used for ranking), not a sample, so it is not jittered.
    """

    def __init__(self, model=MODEL, host=HOST, log_dir: Optional[Path] = None,
                 think: bool = False, timeout: float = 600, post=_http_post, seed_offset: int = 0,
                 judges: Sequence["OllamaAgent"] = (), num_ctx: Optional[int] = None):
        self.model = model
        self.host = host.rstrip("/")
        self.log_dir = log_dir
        self.think = think
        self.timeout = timeout
        self.post = post
        self.seed_offset = seed_offset
        self.calls = 0
        # A judge panel: p_yes is the mean over these agents (each a different model).
        # Measured on 200 gold-labelled judgements (benchmarks/reports/2026-10-23-voting.md):
        # different models averaged beat one model sampled many times or asked many ways.
        self.judges = list(judges)
        self.num_ctx = num_ctx

    def _sampling(self, temperature: float, seed: int) -> Tuple[float, int]:
        """The temperature and seed actually sent, after applying the run's seed offset."""
        if not self.seed_offset:
            return temperature, seed
        return max(temperature, SEED_TEMPERATURE), seed + 1000 * self.seed_offset

    def _body(self, prompt: str, system: str, images: Sequence[Path], schema: Optional[dict],
              temperature: float, seed: int, num_predict: Optional[int] = None) -> dict:
        message: dict = {"role": "user", "content": prompt}
        if images:
            message["images"] = [base64.b64encode(Path(i).read_bytes()).decode("ascii") for i in images]
        body: dict = {
            "model": self.model, "stream": False, "think": self.think,
            "messages": ([{"role": "system", "content": system}] if system else []) + [message],
            "options": {"temperature": temperature, "seed": seed,
                        "num_predict": num_predict or (1024 if schema else 2048)},
        }
        if self.num_ctx:
            body["options"]["num_ctx"] = self.num_ctx
        if schema:
            body["format"] = schema
        return body

    def _log(self, label: str, prompt: str, system: str, images: Sequence[Path], text: str, extra: str = ""):
        self.calls += 1
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            (self.log_dir / f"{self.calls:03d}_{label}.txt").write_text(
                f"MODEL: {self.model} {extra}\nIMAGES: {[str(i) for i in images]}\n\n"
                f"=== SYSTEM ===\n{system}\n\n=== PROMPT ===\n{prompt}\n\n=== RESPONSE ===\n{text}\n")

    def chat(self, prompt: str, system: str = "", images: Sequence[Path] = (),
             schema: Optional[dict] = None, temperature: float = 0.0, seed: int = 0,
             label: str = "ask", num_predict: Optional[int] = None) -> str:
        """One stateless question. `num_predict` caps the reply length: a schema-constrained
        reply can otherwise be padded with whitespace up to the default cap, which costs
        about 100 s per call on the 9B model."""
        temperature, seed = self._sampling(temperature, seed)
        body = self._body(prompt, system, images, schema, temperature, seed, num_predict)
        response = self.post(f"{self.host}/api/chat", body, self.timeout)
        text = response.get("message", {}).get("content", "").strip()
        self._log(label, prompt, system, images, text, f"T={temperature} seed={seed}")
        return text

    def p_yes(self, prompt: str, label: str = "p_yes", system: str = "", images: Sequence[Path] = ()) -> float:
        """P(yes) from the token probabilities of a single constrained yes/no answer.

        Cheap (one short call) and well suited to RANKING alternatives; for an
        accept/reject decision use yes_score, which is better calibrated. With a judge
        panel it is the panel's mean.
        """
        if self.judges:
            return self.p_yes_many([prompt], label, system, images)[0]
        return self._p_yes(prompt, label, system, images)

    def p_yes_many(self, prompts: Sequence[str], label: Union[str, Sequence[str]] = "p_yes", system: str = "",
                   images: Sequence[Path] = ()) -> List[float]:
        """p_yes for several prompts; a panel asks one judge about all of them before the
        next, so each model is loaded once per batch rather than once per question."""
        labels = [label] * len(prompts) if isinstance(label, str) else list(label)
        if not self.judges:
            return [self.p_yes(q, lb, system, images) for q, lb in zip(prompts, labels)]
        sums = [0.0] * len(prompts)
        for judge in self.judges:
            for k, (q, lb) in enumerate(zip(prompts, labels)):
                p = judge.p_yes(q, lb, system, images)
                sums[k] += p
                self._log(f"{lb}_{judge.model.split(':')[0]}", q, system, images, f"p_yes={p:.3f}")
        return [v / len(self.judges) for v in sums]

    def _p_yes(self, prompt: str, label: str, system: str, images: Sequence[Path]) -> float:
        schema = obj_schema({"answer": {"type": "string", "enum": ["yes", "no"]}})
        body = self._body(prompt, system, images, schema, 0.0, 0)
        body.update(logprobs=True, top_logprobs=10)
        body["options"]["num_predict"] = 8
        response = self.post(f"{self.host}/api/chat", body, self.timeout)
        p = 0.5
        for tok in response.get("logprobs") or []:
            alts = tok.get("top_logprobs") or []
            yes = sum(math.exp(a["logprob"]) for a in alts if a["token"].strip().lower().startswith("yes"))
            no = sum(math.exp(a["logprob"]) for a in alts if a["token"].strip().lower().startswith("no"))
            if yes + no > 0.05:
                p = yes / (yes + no)
                break
        else:
            text = response.get("message", {}).get("content", "")
            p = 0.75 if '"yes"' in text else 0.25 if '"no"' in text else 0.5
        self._log(label, prompt, system, images, f"p_yes={p:.3f}")
        return p

    def ask_json(self, prompt: str, schema: dict, **kwargs) -> dict:
        text = self.chat(prompt, schema=schema, **kwargs)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = extract_json(text)
        if not isinstance(data, dict):
            raise ValueError("the reply was not a JSON object")
        return data

    def yes_score(self, prompt: str, label: str = "yes_no", **kwargs) -> float:
        """Fraction of samples answering "yes" (stops early once two samples agree)."""
        schema = obj_schema({"reasoning": REASONING, "answer": {"type": "string", "enum": ["yes", "no"]}})
        answers: List[str] = []
        for i in range(VOTES):
            try:
                answers.append(self.ask_json(prompt, schema, temperature=0.0 if i == 0 else 0.7,
                                             seed=i, label=label, **kwargs).get("answer", "no"))
            except ValueError:
                continue
            if len(answers) == 2 and answers[0] == answers[1]:
                break
        return answers.count("yes") / len(answers) if answers else 0.0

    def vote(self, prompt: str, schema: dict, keys: Sequence[str], n: int = VOTES,
             **kwargs) -> Tuple[Optional[dict], int]:
        """Self-consistency: n samples, majority answer on `keys`. Returns (answer, votes)."""
        answers: List[dict] = []

        def sample(i):
            try:
                answers.append(self.ask_json(prompt, schema, temperature=0.0 if i == 0 else 0.7,
                                             seed=i, **kwargs))
            except ValueError:
                pass

        for i in range(n):
            sample(i)
        tally = Counter(tuple(str(a.get(k)) for k in keys) for a in answers)
        if answers and tally.most_common(1)[0][1] * 2 <= len(answers):
            for i in range(n, n + 2):  # no majority yet: two more samples
                sample(i)
        if not answers:
            return None, 0
        tally = Counter(tuple(str(a.get(k)) for k in keys) for a in answers)
        best, count = tally.most_common(1)[0]
        winner = next(a for a in answers if tuple(str(a.get(k)) for k in keys) == best)
        return winner, count


def extract_json(text: str) -> dict:
    """Return the first JSON object in the text, ignoring fences and chatter."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text, match.start())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    raise ValueError("no JSON object found in the response")


def obj_schema(props: dict, required: Optional[Sequence[str]] = None) -> dict:
    return {"type": "object", "properties": props, "required": list(required or props)}


REASONING = {"type": "string", "maxLength": 240, "description": "one short sentence"}


# ---------------------------------------------------------------------------
# Design state
# ---------------------------------------------------------------------------

# Several copies of a component (legs, gussets, feet) are laid out by Python.
# Each arrangement gives every copy a fraction (0 = start edge, 1 = end edge)
# along the axes it controls.
def instance_fractions(arrangement: Optional[str], count: int) -> List[Dict[str, float]]:
    if count <= 1 or not arrangement:
        return [{}]
    kind, _, axes = arrangement.partition("_")
    if kind == "corners":
        a, b = axes[0], axes[1]
        return [{a: i, b: j} for i in (0.0, 1.0) for j in (0.0, 1.0)]
    if kind == "ends":
        return [{axes: 0.0}, {axes: 1.0}]
    if kind == "triangle":
        a, b = axes[0], axes[1]
        return [{a: 0.5, b: 1.0}, {a: 0.0, b: 0.0}, {a: 1.0, b: 0.0}]
    return [{axes: i / (count - 1)} for i in range(count)]  # row


@dataclass
class Component:
    name: str
    description: str
    shape: Optional[str] = None
    params: Optional[dict] = None
    place: Optional[dict] = None
    count: int = 1
    arrangement: Optional[str] = None       # e.g. "corners_xy", "ends_x", "row_y"
    notes: Dict[str, List[str]] = field(default_factory=dict)       # "shape" | "params" | "place"
    rejected: Dict[str, list] = field(default_factory=dict)         # options verification ruled out
    size: Optional[Vec] = None
    positions: List[Vec] = field(default_factory=list)
    draft: Optional[dict] = None            # placement being decided by the placement subtree
    verified: Optional[str] = None          # spec key whose verification FINISHED (passed or not)
    # How that verification ended. "verified": the checks passed. "unsatisfied": the
    # search stopped without passing (out of attempts, or a local optimum) and the
    # best version was kept; `residual` says what is still wrong. Never read
    # `verified` alone as a pass: it only means "do not check this spec again".
    status: Optional[str] = None
    residual: List[str] = field(default_factory=list)
    verify_attempts: int = 0
    history: List[tuple] = field(default_factory=list)  # (conflicts, score, attempt, snapshot) per check
    others: List[str] = field(default_factory=list)       # names of the other components

    @property
    def position(self) -> Optional[Vec]:
        return self.positions[0] if self.positions else None

    def needs(self, aspect: str) -> bool:
        if self.notes.get(aspect):
            return True
        return {"shape": self.shape, "params": self.params, "place": self.place}[aspect] is None

    def spec_key(self) -> str:
        return json.dumps([self.shape, self.params, self.place, self.count, self.arrangement], sort_keys=True)

    def summary(self) -> str:
        bits = [f"{self.name}{f' (x{self.count})' if self.count > 1 else ''}: {self.description}"]
        if self.shape:
            bits.append(f"shape={self.shape}")
        if self.params:
            bits.append("params=" + json.dumps({k: (round(v, 2) if isinstance(v, float) else v)
                                                for k, v in self.params.items()}))
        if self.place:
            bits.append(f"attached to the {self.place['side']} of {self.place['parent']}")
        return "; ".join(bits)


@dataclass
class Design:
    """Everything the behaviours share. The tree reads and writes only this."""
    request: str
    workdir: Path
    components: List[Component] = field(default_factory=list)
    seed: int = 0                                             # run seed (offsets every LLM sampling seed)
    l1: List[dict] = field(default_factory=list)              # the person's L1 requirements {id, text, method}
    base_request: Optional[str] = None                        # the request before the L1s were appended
    feedback_notes: List[str] = field(default_factory=list)   # shown to the person
    number_attempts: Dict[str, int] = field(default_factory=dict)
    human_feedback: List[str] = field(default_factory=list)
    flagged: List[str] = field(default_factory=list)          # components verification sent back
    assembly: Optional[Path] = None
    mesh: List[Tri] = field(default_factory=list)
    stability: dict = field(default_factory=dict)
    views: Dict[str, Path] = field(default_factory=dict)
    highlights: Dict[str, Dict[str, Path]] = field(default_factory=dict)
    visual: Dict[str, dict] = field(default_factory=dict)      # component -> verdict
    visual_rounds: int = 0
    best: Optional[Tuple[int, List[Component]]] = None
    export_path: Optional[Path] = None
    cascade: Optional[object] = None                          # cascade.CascadeState in --mode cascade

    def component(self, name: str) -> Optional[Component]:
        return next((c for c in self.components if c.name == name), None)

    def unsatisfied(self) -> List[Component]:
        """Components whose verification gave up; any summary must count these as failures."""
        return [c for c in self.components if c.status == "unsatisfied"]

    def index(self, name: str) -> int:
        return [c.name for c in self.components].index(name)

    def summary(self) -> str:
        return "\n".join(f"  - {c.summary()}" for c in self.components)


# ---------------------------------------------------------------------------
# Plain-English descriptions of what was built (for back-translation checks)
# ---------------------------------------------------------------------------

AXIS_WORDS = {"z": "standing upright", "x": "lying left to right", "y": "lying front to back"}


def shape_phrase(c: Component) -> str:
    p = c.params
    if c.shape == "box":
        w, dp, h = p["width"], p["depth"], p["height"]
        if h <= 0.25 * min(w, dp):
            return f"a flat plate {fmt(w)} mm wide (left to right), {fmt(dp)} mm deep (front to back) and {fmt(h)} mm thick"
        if dp <= 0.25 * min(w, h):
            return f"an upright wall {fmt(w)} mm wide (left to right), {fmt(h)} mm tall and {fmt(dp)} mm thick (front to back)"
        if w <= 0.25 * min(dp, h):
            return f"an upright wall {fmt(dp)} mm long (front to back), {fmt(h)} mm tall and {fmt(w)} mm thick (left to right)"
        return (f"a block {fmt(w)} mm wide (left to right), {fmt(dp)} mm deep "
                f"(front to back) and {fmt(h)} mm tall")
    if c.shape == "panel":
        stance = ("standing upright" if p["angle"] >= 89.5
                  else f"leaning {'backwards' if p['lean'] == 'back' else 'forwards' if p['lean'] == 'front' else 'to the ' + p['lean']} "
                       f"at {fmt(p['angle'])} degrees from the horizontal")
        return (f"a flat slab {fmt(p['thickness'])} mm thick, {fmt(p['width'])} mm wide and "
                f"{fmt(p['height'])} mm tall, {stance}")
    if c.shape == "wedge":
        return (f"a triangular wedge {fmt(p['width'])} mm wide, {fmt(p['depth'])} mm deep and "
                f"{fmt(p['height'])} mm tall at its {p['high_side']} side, sloping down to the opposite side")
    if c.shape == "cylinder":
        if p["height"] < p["diameter"]:
            flat = {"z": "lying flat", "x": "standing on its edge, facing left and right",
                    "y": "standing on its edge, facing front and back"}[p["axis"]]
            return f"a round disc {fmt(p['diameter'])} mm across and {fmt(p['height'])} mm thick, {flat}"
        return f"a solid round rod {fmt(p['diameter'])} mm across and {fmt(p['height'])} mm long, {AXIS_WORDS[p['axis']]}"
    if c.shape == "tube":
        noun = "ring" if p["height"] < p["outer_diameter"] / 2 else "tube"
        return (f"a hollow round {noun} {fmt(p['outer_diameter'])} mm across with a {fmt(p['inner_diameter'])} mm "
                f"hole, {fmt(p['height'])} mm long, {AXIS_WORDS[p['axis']]}")
    if c.shape == "sphere":
        return f"a ball {fmt(p['diameter'])} mm across"
    return "an unknown shape"


SIDE_RELATION = {
    "top": "sits on top of the {p}",
    "bottom": "is fixed underneath the {p}",
    "front": "is fixed to the front face of the {p}, in front of it",
    "back": "is fixed to the back face of the {p}, behind it",
    "left": "is fixed to the left end of the {p}, beside it",
    "right": "is fixed to the right end of the {p}, beside it",
}
EDGE_WORDS = {
    "x": {"left": "at the {p}'s left end", "center": "centred left to right", "right": "at the {p}'s right end"},
    "y": {"front": "along the {p}'s front edge", "center": "centred front to back",
          "back": "along the {p}'s back edge"},
    "z": {"bottom": "level with the {p}'s bottom", "center": "centred vertically", "top": "level with the {p}'s top"},
}
SPAN_PHRASE = {"x": "running the full width of the {p}", "y": "running the full depth of the {p}",
               "z": "running the full height of the {p}"}
ARRANGEMENT_PHRASE = {
    "corners": "one near each corner of the {p}",
    "triangle": "in a triangle, two near the {p}'s front corners and one at the middle of its back",
    "ends_x": "one at the {p}'s left end and one at its right end",
    "ends_y": "one at the {p}'s front edge and one at its back edge",
    "ends_z": "one at the {p}'s bottom and one at its top",
    "row_x": "spaced evenly in a row from left to right",
    "row_y": "spaced evenly in a row from front to back",
    "row_z": "spaced evenly from bottom to top",
}


def face_axes(side: str) -> List[str]:
    return [a for a in "xyz" if a != "xyz"[SIDE_AXIS[side][0]]]


def arrangement_axes(arrangement: Optional[str]) -> str:
    return (arrangement or "_").partition("_")[2]


def relation_phrase(d: Design, c: Component) -> str:
    return SIDE_RELATION[c.place["side"]].format(p=c.place["parent"])


def edge_phrases(d: Design, c: Component) -> Dict[str, str]:
    """Per in-plane axis: where on the parent's face the component sits."""
    parent = d.component(c.place["parent"])
    out = {}
    for axis in face_axes(c.place["side"]):
        if axis in arrangement_axes(c.arrangement):
            continue
        i = "xyz".index(axis)
        if parent.size and c.size and abs(c.size[i] - parent.size[i]) <= ABS_TOL:
            out[axis] = SPAN_PHRASE[axis].format(p=parent.name)
        else:
            out[axis] = EDGE_WORDS[axis][c.place.get(axis, "center")].format(p=parent.name)
    return out


def arrangement_phrase(c: Component) -> str:
    if c.count <= 1 or not c.arrangement:
        return ""
    key = c.arrangement.split("_")[0] if c.arrangement.startswith(("corners", "triangle")) else c.arrangement
    return ARRANGEMENT_PHRASE[key].format(p=c.place["parent"] if c.place else "object")


def describe(d: Design, c: Component, edges: Optional[Sequence[str]] = None) -> str:
    """What Python actually built for this component, in plain English.

    `edges` limits which in-plane axes get a position phrase (None = all), so
    candidate placements can be compared one decision at a time.
    """
    if c.count > 1:
        text = f"There are {c.count} {c.name} parts; each is {shape_phrase(c)}."
    else:
        text = f"The {c.name} is {shape_phrase(c)}."
    if c.place:
        where = [relation_phrase(d, c)]
        parent = d.component(c.place["parent"])
        if (edges is None and c.place["side"] in ("top", "bottom") and parent and parent.size and c.size and c.count == 1
                and all(abs(c.size[i] - parent.size[i]) <= ABS_TOL for i in (0, 1))):
            if c.shape == "tube":
                where.append(f"running around the {parent.name}'s outer edge")
            else:
                where.append(f"covering the {parent.name}'s whole {c.place['side']} surface")
        else:
            where += [ph for axis, ph in edge_phrases(d, c).items() if edges is None or axis in edges]
        if arrangement_phrase(c):
            where.append(arrangement_phrase(c))
        subject = "They" if c.count > 1 else "It"
        verb = where[0].replace("sits", "sit").replace("is fixed", "are fixed") if c.count > 1 else where[0]
        text += f" {subject} {verb}" + "".join(f", {w}" for w in where[1:]) + "."
    else:
        text += " It is the main body of the object."
    return text


# ---------------------------------------------------------------------------
# Language cues: the person's words often state the answer outright
# ("along the back edge", "a round seat", "a gusset on each side"). Python reads
# them deterministically; they bias every ranking, and a contradiction fails
# verification without asking the model.
# ---------------------------------------------------------------------------

CUE_BONUS = 0.3

SHAPE_CUES = [  # first match wins
    ("tube", r"\b(hollow|tubes?|cups?|pipes?|rings?|sleeves?|mugs?|rims?|collars?|bands?|hoops?)\b"),
    ("sphere", r"\b(balls?|spheres?|spherical)\b"),
    ("wedge", r"\b(triangular|triangles?|gussets?|wedges?|braces?|brackets?)\b"),
    ("panel", r"\b(lean|leans|leaning|tilted|tilts?|inclined|slanted|sloped|sloping)\b"),
    ("cylinder", r"\b(round|circular|discs?|disks?|cylinders?|cylindrical|rods?|dowels?|pegs?)\b"),
]
SIDE_CUES = {
    "bottom": r"\b(under|underneath|beneath|below|legs?|feet|foot)\b",
    "top": r"\b(on top|stands?|standing|sits? on|sitting on|rests? on|resting on|mounted on|on the base|upright|vertical|rising|rises|walls?|lips?|ledges?|fences?|rails?|posts?|pillars?|columns?|uprights?)\b",
    "back": r"\bbehind\b",
    "front": r"\bin front of\b",
}
EDGE_CUES = {
    "x": {"left": r"\bleft\b", "right": r"\bright\b"},
    "y": {"front": r"\bfront\b", "back": r"\b(back|rear)\b"},
    "z": {"top": r"\b(at|along|level with) the top\b", "bottom": r"\b(at|along|level with) the bottom\b"},
}
CENTER_CUE = r"\b(centre|center|middle|centred|centered|central)\b"
ARRANGEMENT_CUES = {
    "corners": r"\bcorners?\b",
    "triangle": r"\b(three|3)\b[\w\s-]{0,20}?\b(legs?|feet|foot|supports?)\b|\btripod\b|\btriangle\b",
    "ends_x": r"\b(each side|both sides|either side|left and right|each end|both ends)\b",
    "ends_y": r"\bfront and back\b",
}
SPAN_NAMES = {"x": "width", "y": "depth", "z": "height"}
SPAN_CUE = r"\b(running along|runs along|run along|along the (whole|full|entire)|full (width|length|depth)|all along)\b"
BRACE_WORDS = r"\b(gussets?|braces?|bracing|brackets?|ribs?|fins?|webs?)\b"
COVER_WORDS = r"\b(cover|covers|covering|lid|cap|top plate|whole|entire)\b"


def cue_text(c: Component) -> str:
    """The component's own words, without the names of other components it mentions
    (so "a base plate under the wedge" does not read as a wedge)."""
    text = f" {c.name.replace('_', ' ')} {c.description} ".lower()
    for other in c.others:
        if other != c.name:
            text = re.sub(rf"\b{re.escape(other.replace('_', ' '))}s?\b", " ", text)
    return text


def shape_cue(c: Component) -> Optional[str]:
    text = cue_text(c)
    return next((shape for shape, pat in SHAPE_CUES if re.search(pat, text)), None)


def side_cue(c: Component) -> Optional[str]:
    text = cue_text(c)
    hits = [side for side, pat in SIDE_CUES.items() if re.search(pat, text)]
    return hits[0] if len(hits) == 1 else None


def edge_cue(c: Component, axis: str) -> Optional[str]:
    text = cue_text(c)
    hits = [v for v, pat in EDGE_CUES[axis].items() if re.search(pat, text)]
    if len(hits) == 1:
        return hits[0]
    if not hits and axis != "z" and re.search(CENTER_CUE, text):
        return "center"
    return None


def arrangement_cue(c: Component) -> Optional[str]:
    text = cue_text(c)
    return next((a for a, pat in ARRANGEMENT_CUES.items() if re.search(pat, text)), None)


def cue_score(d: Design, c: Component, contradictions_only: bool = False) -> float:
    """+1 per placement decision that matches a cue, -1 per contradiction
    (or, with contradictions_only, just the number of contradictions)."""
    if not c.place:
        return 0.0
    if contradictions_only:
        return -sum(1 for k in _cue_checks(d, c) if k < 0)
    return float(sum(_cue_checks(d, c)))


def _cue_checks(d: Design, c: Component) -> List[int]:
    score: List[int] = []
    cue = side_cue(c)
    if cue:
        score.append(1 if c.place["side"] == cue else -1)
    parent = d.component(c.place["parent"])
    for axis in face_axes(c.place["side"]):
        if axis in arrangement_axes(c.arrangement):
            continue
        cue = edge_cue(c, axis)
        i = "xyz".index(axis)
        spans = parent and parent.size and c.size and abs(c.size[i] - parent.size[i]) <= ABS_TOL
        if cue and not spans:
            score.append(1 if c.place.get(axis, "center") == cue else -1)
    cue = arrangement_cue(c)
    if cue and c.count > 1 and c.arrangement:
        score.append(1 if c.arrangement.startswith(cue) else -1)
    return score


DIMENSION_WORDS = {
    "height": r"tall|high|height",
    "width": r"wide|width|across|diameter",
    "thick": r"thick|thickness",
    "long": r"long|length|deep|depth",
}


def stated_dimensions(c: Component) -> List[Tuple[str, float]]:
    """Labelled dimensions in the component's description, e.g. ("height", 150) from "150 mm tall"."""
    out = []
    text = c.description.lower()
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(mm|cm)?\s*(\w+)", text):
        value = float(m.group(1)) * (10.0 if m.group(2) == "cm" else 1.0)
        word = m.group(3)
        for kind, pat in DIMENSION_WORDS.items():
            if re.fullmatch(pat, word):
                out = [(k, v) for k, v in out if k != kind]  # a later statement (feedback) wins
                out.append((kind, value))
    return out


def dimension_conflicts(c: Component, request: str = "") -> List[str]:
    """Does what was built have the dimensions the description states, on the right axis?"""
    if not (c.size and c.params):
        return []
    x, y, z = c.size
    numbers = [v for v in c.params.values() if isinstance(v, (int, float))]
    problems = []
    asked = [v for v, _, _ in request_numbers(request)]
    for kind, value in stated_dimensions(c):
        if request and not any(abs(v - value) <= 1e-6 for v in asked):
            continue  # a size the model invented while listing components is not a requirement
        close = lambda a: abs(a - value) <= max(ABS_TOL, 0.02 * value)  # noqa: E731
        ok = {"height": close(z) or (c.shape == "panel" and close(c.params.get("height", -1))),
              "width": close(x) or close(y) or any(close(v) for v in numbers),
              "thick": close(min(x, y, z)) or any(close(v) for v in numbers),
              "long": close(max(x, y)) or close(y) or any(close(v) for v in numbers)}[kind]
        if not ok:
            problems.append(f"the description says {fmt(value)} mm {kind} but it was built "
                            f"{fmt(x)} x {fmt(y)} x {fmt(z)} mm (width x depth x height)")
    return problems


def cue_conflicts(d: Design, c: Component) -> List[str]:
    """Contradictions between the component's own words and what was built."""
    problems = dimension_conflicts(c, d.request)
    cue = shape_cue(c)
    if cue and c.shape != cue and cue not in c.rejected.get("shape", []):
        problems.append(f"it is described like a {cue} but was built as a {c.shape}")
    if not c.place:
        return problems
    if cue_score(d, c, contradictions_only=True) < 0:
        problems.append("its placement contradicts its description")
    parent = d.component(c.place["parent"])
    if not (parent and parent.size and c.size):
        return problems
    for axis in face_axes(c.place["side"]):
        cue = edge_cue(c, axis)
        i = "xyz".index(axis)
        # (a leaning panel's bounding box is mostly air, so it is exempt)
        if cue in ("front", "back", "left", "right") and c.count == 1 and c.shape != "panel" \
                and c.size[i] > 0.5 * parent.size[i]:
            problems.append(f"it is described at the {cue} edge but takes up {fmt(c.size[i])} mm of "
                            f"{parent.name}'s {fmt(parent.size[i])} mm {SPAN_NAMES[axis]}")
    normal = SIDE_AXIS[c.place["side"]][0]
    if c.place["side"] not in ("top", "bottom") and c.size[normal] > 0.5 * parent.size[normal] + ABS_TOL:
        problems.append(f"it sticks out {fmt(c.size[normal])} mm from {parent.name}'s {c.place['side']} face, "
                        f"further than {parent.name} itself is {SPAN_NAMES['xyz'[normal]]}")
    if c.shape == "wedge":
        run = "depth" if c.params["high_side"] in ("back", "front") else "width"
        if c.params[run] < 0.25 * c.params["height"]:
            problems.append(f"its slope is too steep to be a wedge: it rises {fmt(c.params['height'])} mm "
                            f"over only {fmt(c.params[run])} mm")
    if re.search(BRACE_WORDS, cue_text(c)) and c.position:
        text = f" {c.description} ".lower()
        for other in d.components:
            if other is c or other is parent or not other.position or not other.size:
                continue
            if re.search(rf"\b{re.escape(other.name.replace('_', ' '))}\b", text) and \
                    contact_area(c, c.position, other, other.position, d.workdir / "checks") < min_contact(c, other):
                problems.append(f"it should brace {other.name} but does not touch it")
    if c.shape == "wedge" and re.search(BRACE_WORDS, cue_text(c)):
        thin = "width" if c.params["high_side"] in ("back", "front") else "depth"
        others = [c.params[k] for k in ("width", "depth", "height") if k != thin]
        if c.params[thin] > 0.25 * min(others):
            problems.append(f"a {c.name} is a thin triangle, but its {thin} ({fmt(c.params[thin])} mm) "
                            f"is not its smallest size")
    if (c.place["side"] in ("top", "bottom") and c.count == 1 and parent and parent.size and c.size and c.shape != "tube"
            and all(abs(c.size[i] - parent.size[i]) <= ABS_TOL for i in (0, 1))
            and not re.search(COVER_WORDS, cue_text(c))):
        problems.append(f"it covers the whole {c.place['side']} of {parent.name}, which would just make "
                        f"{parent.name} thicker")
    return problems


# ---------------------------------------------------------------------------
# Behaviours
# ---------------------------------------------------------------------------


class Step(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, design: Design):
        super().__init__(name)
        self.design = design


class ForEach(py_trees.composites.Sequence):
    """A sequence whose children are rebuilt from the design each time it starts.

    This is how the tree grows one subtree per component: the factory is called
    with the current design, so components added later get their own subtrees on
    the next pass.
    """

    def __init__(self, name: str, design: Design,
                 factory: Callable[[Design], List[py_trees.behaviour.Behaviour]]):
        super().__init__(name, memory=True)
        self.design = design
        self.factory = factory

    def tick(self):
        if self.status != Status.RUNNING:
            self.remove_all_children()
            self.add_children(self.factory(self.design))
        yield from super().tick()


# ----- understand ----------------------------------------------------------

EXAMPLE_COMPONENTS = """Example, for "a pencil holder: a 70x70x4 mm square base with a round cup 60 mm wide and 90 mm tall, on four small feet":
{"components": [
  {"name": "base", "count": 1, "description": "square plate 70 x 70 x 4 mm"},
  {"name": "cup", "count": 1, "description": "hollow round tube 60 mm wide and 90 mm tall standing on the centre of the base"},
  {"name": "foot", "count": 4, "description": "small round foot under the base, one near each corner"}
]}"""


BASE_WORDS = r"\b(base|floor|platform|bottom plate|base plate)\b"


# Words that make two otherwise identical descriptions two different parts ("front wall" vs "back wall").
DISTINGUISHING_WORDS = {"front", "back", "rear", "left", "right", "top", "bottom", "upper", "lower", "inner",
                        "outer", "middle", "centre", "center", "first", "second", "third", "side", "end"}


def dedupe_components(comps: List[Component]) -> List[Component]:
    """Drop a component whose description repeats an earlier one (same words, same numbers).

    Descriptions that differ in a number or a place word are different parts even when
    almost every other word is shared: "wall 30 mm high along the front edge" and
    "... along the back edge" once collapsed into one wall.
    """
    def words(c: Component) -> set:
        return set(re.findall(r"[a-z0-9.]+", f"{c.name.replace('_', ' ')} {c.description}".lower()))

    out: List[Component] = []
    for c in comps:
        wc = words(c)
        if any(len(wc & wo) >= 0.85 * max(1, len(wc))
               and not any(w in DISTINGUISHING_WORDS or re.fullmatch(r"[0-9.]+", w) for w in wc ^ wo)
               for wo in map(words, out)):
            continue
        out.append(c)
    return out


PLACE_WORDS = ("front", "back", "rear", "left", "right", "top", "bottom", "upper", "lower", "inner", "outer", "middle")
COUNT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}


def _singular(word: str) -> str:
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def role_word(desc: str, others: Sequence[str]) -> Optional[str]:
    """The first place word of a description that none of the other descriptions use."""
    for w in re.findall(r"[a-z]+", desc.lower()):
        if w in PLACE_WORDS and not any(re.search(rf"\b{w}\b", o.lower()) for o in others):
            return w
    return None


def split_roles(c: Component) -> List[Component]:
    """One entry for copies that each have their own place ("one along the front edge and
    one along the back edge") becomes one component per place, so every check and
    every placement decision can name the copy it means."""
    if c.count < 2:
        return [c]
    pat = rf"\b(?:one|the other)\b(?:\s+\w+){{0,4}}?\s+(?:along|at|on|against|near|by|in)\s+(?:the\s+|its\s+)?" \
          rf"({'|'.join(PLACE_WORDS)})\b(?:\s+(?:edge|side|end|face|corner))?"
    found = list(re.finditer(pat, c.description, re.I))
    places = [m.group(1).lower() for m in found]
    if len(found) != c.count or len(set(places)) != len(places):
        return [c]
    start, end = found[0].start(), found[-1].end()
    out = []
    for m, place in zip(found, places):
        clause = re.sub(r"^(one|the other)\s+", "", m.group(0), flags=re.I)
        desc = (c.description[:start] + clause + c.description[end:]).strip()
        desc = re.sub(rf"\b(?:\d+\b(?!\s*(?:mm|cm|in\b|°|deg))|{'|'.join(COUNT_WORDS)})\s+((?:[a-z-]+\s+){{0,3}}?[a-z]+?)s\b", r"\1", desc,
                      count=1, flags=re.I)  # "two upright panels" -> "upright panel"
        out.append(Component(f"{place}_{c.name}", desc, count=1))
    return out


def stated_count(request: str, name: str) -> Optional[int]:
    """How many of this part the request says there are ("two upright panels" -> 2)."""
    noun = _singular(name.split("_")[-1])
    m = re.search(rf"\b(\d+|{'|'.join(COUNT_WORDS)})\s+(?:[a-z-]+\s+){{0,3}}{re.escape(noun)}s?\b", request.lower())
    if not m:
        return None
    return int(m.group(1)) if m.group(1).isdigit() else COUNT_WORDS[m.group(1)]


def assign_roles(raws: Sequence[Tuple[str, str, int]], request: str) -> List[Component]:
    """Components from the LLM's (name, description, count) entries, with roles for copies.

    Two entries with one name ("panel" along the front edge, "panel" along the back
    edge) used to keep only the first; now each is named by the place word that sets
    it apart, and copies of one entry that each have their own place are split.
    When the request says how many there are and the entries already make that many,
    each role is one copy (the LLM once wrote count 2 for the front panel AND listed
    a back panel).
    """
    comps: List[Component] = []
    for name, desc, count in raws:
        if comps and (re.search(r"(^|_)(surface|face|edge|corner)s?$", name)
                      or re.fullmatch(r"((left|right|front|back|top|bottom)_)?sides?", name)):
            continue  # a face of another part, not a solid piece ("top_surface", "front_edge", "left_side")
        same = [c for c in comps if c.name == name or c.name.endswith("_" + name)]
        if same:
            word = role_word(desc, [c.description for c in same])
            if not word:
                continue
            for c in same:
                if c.name == name:
                    w = role_word(c.description, [desc])
                    if w:
                        c.name = f"{w}_{name}"
            name = f"{word}_{name}"
            if any(c.name == name for c in comps):
                continue
        comps.extend(split_roles(Component(name, desc, count=count)))
    groups: Dict[str, List[Component]] = {}
    for c in comps:
        groups.setdefault(c.name.split("_")[-1], []).append(c)
    for noun, group in groups.items():
        n = stated_count(request, noun)
        if len(group) > 1 and n and len(group) == n and sum(c.count for c in group) > n:
            for c in group:
                c.count = 1
    return comps


class ExtractComponents(Step):
    """LLM: split the request into named components with a count (first = main body)."""

    def __init__(self, design: Design, llm: OllamaAgent, max_attempts: int = 30):
        super().__init__("extract_components", design)
        self.llm = llm
        self.max_attempts = max_attempts

    def update(self):
        d = self.design
        if d.components:
            return Status.SUCCESS
        schema = obj_schema({"components": {
            "type": "array", "minItems": 1, "maxItems": MAX_COMPONENTS,
            "items": obj_schema({"name": {"type": "string"},
                                 "count": {"type": "integer", "minimum": 1, "maximum": 8},
                                 "description": {"type": "string"}}),
        }})
        prompt = "\n".join([
            f"A person wants this object: {d.request}",
            "",
            "List its physical components (the solid pieces you would model).",
            "- The FIRST component is the main body that the other components attach to.",
            "- Order the rest so each component comes after the one it attaches to.",
            "- Identical repeated pieces (legs, feet, gussets on each side) are ONE entry with a count.",
            "- Each description says what the component is, its shape, where it is on the object,",
            "  and repeats every dimension the person gave for it.",
            "- Do not invent features the person did not ask for.",
            f"- Use 1 to {MAX_COMPONENTS} entries.",
            "",
            EXAMPLE_COMPONENTS,
        ])
        for attempt in range(self.max_attempts):
            try:
                data = self.llm.ask_json(prompt, schema, temperature=0.0 if attempt == 0 else 0.5,
                                         seed=attempt, label="components")
            except ValueError:
                continue
            raws: List[Tuple[str, str, int]] = []
            for raw in data.get("components", [])[:MAX_COMPONENTS]:
                name = slugify(raw.get("name", ""))
                desc = str(raw.get("description", "")).strip()
                try:
                    count = max(1, min(8, int(raw.get("count", 1))))
                except (TypeError, ValueError):
                    count = 1
                if name and desc:
                    raws.append((name, desc, count if raws else 1))
            comps = dedupe_components(assign_roles(raws, d.base_request or d.request))[:MAX_COMPONENTS]
            base = next((k for k in comps if re.search(BASE_WORDS, f"{k.name.replace('_', ' ')} {k.description}".lower())
                         and k.count == 1), None)
            if base and comps and comps[0] is not base and not re.search(BASE_WORDS, comps[0].name.replace("_", " ")):
                comps.remove(base)
                comps.insert(0, base)  # what the object stands on is the main body
            if comps:
                for comp in comps:
                    comp.others = [o.name for o in comps if o is not comp]
                d.components = comps
                self.logger.info("components: " + ", ".join(
                    f"{c.name}" + (f" x{c.count}" if c.count > 1 else "") for c in comps))
                return Status.SUCCESS
        self.feedback_message = "could not list components"
        return Status.FAILURE


def other_components_text(d: Design, skip: str) -> str:
    return "\n".join(f"  - {c.summary()}" for c in d.components if c.name != skip) or "  (none)"


def notes_text(notes: List[str]) -> str:
    return "\n".join(f"- {n}" for n in notes)


class ChooseShape(Step):
    """LLM vote: which library shape is this component? Rejected shapes are not offered."""

    def __init__(self, design: Design, llm: OllamaAgent, comp: Component):
        super().__init__(f"shape:{comp.name}", design)
        self.llm, self.comp = llm, comp

    def update(self):
        c, d = self.comp, self.design
        if not c.needs("shape"):
            return Status.SUCCESS
        options = [s for s in SHAPES if s not in c.rejected.get("shape", [])] or list(SHAPES)
        cue = shape_cue(c)
        if cue in options:
            if cue != c.shape:
                c.params, c.place = None, None
            c.shape = cue
            c.notes.pop("shape", None)
            self.logger.info(f"{c.name}: shape {c.shape} (from the description's wording)")
            return Status.SUCCESS
        lines = [
            f"Object: {d.request}",
            f'Component "{c.name}": {c.description}',
            "",
            "Which shape best describes this component on its own?",
        ]
        lines += [f"- {SHAPES[s].name}: {SHAPES[s].doc}" for s in options]
        if c.notes.get("shape"):
            lines += ["", notes_text(c.notes["shape"])]
        schema = obj_schema({"reasoning": REASONING, "shape": {"type": "string", "enum": options}})
        answer, votes = self.llm.vote("\n".join(lines), schema, ["shape"], label=f"shape_{c.name}")
        if answer is None:
            return Status.FAILURE
        if answer["shape"] != c.shape:
            c.params = None  # parameters belong to the old shape
            c.place = None   # and its placement depended on them
        c.shape = answer["shape"]
        c.notes.pop("shape", None)
        self.logger.info(f"{c.name}: shape {c.shape} ({votes} votes)")
        return Status.SUCCESS


def propose_params(llm: OllamaAgent, d: Design, c: Component, notes: List[str],
                   attempt: int = 0, errors: Sequence[str] = ()) -> Tuple[Optional[dict], List[str]]:
    """One LLM proposal for the component's parameters, validated by Python."""
    shape = SHAPES[c.shape]
    props: dict = {"reasoning": REASONING}
    props.update({k: p.schema() for k, p in shape.params.items()})
    lines = [f"Object: {d.request}", CONVENTIONS, "", f'Component "{c.name}": {c.description}']
    if c.count > 1:
        lines.append(f"There are {c.count} identical copies; give the size of ONE.")
    lines.append(f"It is modelled as a {shape.name} ({shape.doc}) with these parameters:")
    lines += [f"- {k}: {p.doc}{p.unit()}" for k, p in shape.params.items()]
    given = [f"{fmt(v)} {'degrees' if u == 'deg' else 'mm'}" for v, u, _ in request_numbers(c.description)]
    lines += ["", "Other components:", other_components_text(d, c.name), ""]
    if given:
        lines.append(f"Dimensions the description gives for {c.name}: {', '.join(given)}. Use each of them exactly.")
    lines += ["For anything not given, choose a sensible real-world size. Do not copy another component's",
              "size unless the description says so. Thin parts (lips, ledges, plates, walls, gussets) are thin."]
    if c.params:
        lines += ["", "Current parameters: " + json.dumps(c.params)]
    if notes:
        lines += ["These need to change:", notes_text(notes)]
    if errors:
        lines += ["", "Your last answer was rejected:", notes_text(list(errors))]
    try:
        raw = llm.ask_json("\n".join(lines), obj_schema(props), temperature=0.0 if attempt == 0 else 0.5,
                           seed=attempt, label=f"params_{c.name}")
    except ValueError as exc:
        return None, [str(exc)]
    return validate_params(shape, raw)


class FillParams(Step):
    """LLM fills the chosen shape's typed parameters; Python validates them."""

    def __init__(self, design: Design, llm: OllamaAgent, comp: Component, max_attempts: int = 30):
        super().__init__(f"params:{comp.name}", design)
        self.llm, self.comp, self.max_attempts = llm, comp, max_attempts

    def update(self):
        c, d = self.comp, self.design
        if not c.needs("params"):
            return Status.SUCCESS
        shape = SHAPES[c.shape]
        errors: List[str] = []
        for attempt in range(self.max_attempts):
            params, errors = propose_params(self.llm, d, c, c.notes.get("params", []), attempt, errors)
            if params:
                c.params = params
                c.notes.pop("params", None)
                self.logger.info(f"{c.name}: {json.dumps(params)}")
                return Status.SUCCESS
        self.feedback_message = f"no valid parameters for {c.name}: {'; '.join(errors)}"
        c.rejected.setdefault("shape", []).append(c.shape)
        c.notes["shape"] = [f"No valid {shape.name} parameters could be found ({'; '.join(errors)})."]
        return Status.FAILURE


# ----- placement subtree ---------------------------------------------------


class PlacementStep(Step):
    """One question of the placement subtree.

    Placement is split into small decisions: which component it touches, which
    side (scored by yes/no votes over the sides Python found physically
    possible), how copies are arranged, whether it spans the parent, and where
    along each edge. Answers accumulate in `comp.draft`; FinishPlacement commits
    them. Options that verification rejected are never offered again.
    """

    key = ""

    def __init__(self, design: Design, llm: OllamaAgent, comp: Component):
        super().__init__(f"{self.key or 'place'}:{comp.name}", design)
        self.llm, self.comp = llm, comp

    def context(self) -> List[str]:
        c, d = self.comp, self.design
        lines = [f"Object: {d.request}", f'Component "{c.name}": {c.description}']
        if c.count > 1:
            lines.append(f"There are {c.count} of them.")
        parent = d.component(c.draft.get("parent", "")) if c.draft else None
        if parent:
            lines.append(f'Component "{parent.name}": {parent.description}')
        return lines

    def yes(self, question: str) -> float:
        return self.llm.yes_score("\n".join(self.context() + ["", question]), label=f"{self.key}_{self.comp.name}")

    def update(self):
        c = self.comp
        if c.draft is None or self.key in c.draft:
            return Status.SUCCESS
        return self.decide()

    def decide(self) -> Status:
        raise NotImplementedError


class StartPlacement(PlacementStep):
    key = "start"

    def update(self):
        c, d = self.comp, self.design
        layout(d)  # sizes are needed for the feasibility checks
        if d.index(c.name) == 0:
            c.place, c.draft, c.arrangement = None, None, None
            c.notes.pop("place", None)
        elif c.needs("place"):
            c.draft = {}
        else:
            c.draft = None
        return Status.SUCCESS


class ChooseParent(PlacementStep):
    key = "parent"

    def decide(self):
        c, d = self.comp, self.design
        parents = [p.name for p in d.components[:d.index(c.name)] if p.count == 1] or [d.components[0].name]
        raw = f" {c.description} ".lower()  # (cue_text strips other parts' names; here we want them)
        named = [n for n in parents if re.search(rf"\b{re.escape(n.replace('_', ' '))}\b", raw)]
        # The part it names, otherwise the main body (the root of everything).
        c.draft["parent"] = named[0] if len(named) == 1 else parents[0]
        self.logger.info(f"{c.name}: parent {c.draft['parent']}" + (" (named)" if len(named) == 1 else ""))
        return Status.SUCCESS


VERIFY_QUESTION = "Is this part of the design what the person asked for?"
GRAVITY_ORDER = ["top", "bottom", "back", "front", "left", "right"]


def verify_prompt(d: Design, built: str) -> str:
    return f"A person asked for: {d.request}\n\nIn the current design: {built}\n\n{VERIFY_QUESTION}"


def variant_design(d: Design, comp: Component, variant: Component) -> Design:
    """A shallow copy of the design with one component swapped for a variant, laid out."""
    clone = copy.copy(d)
    clone.components = [variant if c is comp else copy.copy(c) for c in d.components]
    layout(clone)
    return clone


def shape_volume(c: Component) -> float:
    p = c.params
    if c.shape == "box" or c.shape is None:
        return c.size[0] * c.size[1] * c.size[2]
    if c.shape == "panel":
        return p["width"] * p["thickness"] / math.sin(math.radians(p["angle"])) * p["height"]
    if c.shape == "wedge":
        return p["width"] * p["depth"] * p["height"] / 2
    if c.shape == "cylinder":
        return math.pi * (p["diameter"] / 2) ** 2 * p["height"]
    if c.shape == "tube":
        return math.pi * ((p["outer_diameter"] / 2) ** 2 - (p["inner_diameter"] / 2) ** 2) * p["height"]
    return math.pi / 6 * p["diameter"] ** 3


def stands_up(d: Design) -> bool:
    """Quick analytic stability: centre of mass (bbox centroids) over the table footprint."""
    mass = cx = cy = 0.0
    feet: List[Tuple[float, float]] = []
    for c in d.components:
        if not (c.size and c.positions and c.params):
            continue
        m = shape_volume(c)
        for x, y, z in c.positions:
            mass += m
            cx += m * (x + c.size[0] / 2)
            cy += m * (y + c.size[1] / 2)
            if z < 1e-3:
                feet += [(x, y), (x + c.size[0], y), (x, y + c.size[1]), (x + c.size[0], y + c.size[1])]
    if mass == 0:
        return True
    return inside_hull((cx / mass, cy / mass), convex_hull(feet))


UNSTABLE_PENALTY = 0.3


def rank_variants(llm: OllamaAgent, d: Design, comp: Component, variants: Dict[str, Component],
                  edges: Optional[Sequence[str]] = None, label: str = "rank") -> Dict[str, float]:
    """Score each variant by how well Python's description of it matches the request,
    minus a penalty when Python's physics says the result would tip over."""
    designs = {key: variant_design(d, comp, v) for key, v in variants.items()}
    prompts = [verify_prompt(vd, describe(vd, vd.component(variants[key].name), edges)) for key, vd in designs.items()]
    scores = dict(zip(designs, llm.p_yes_many(prompts, label=label)))
    for key, vd in designs.items():
        if not stands_up(vd):
            scores[key] -= UNSTABLE_PENALTY
    return scores


def params_valid(c: Component) -> bool:
    return validate_params(SHAPES[c.shape], c.params)[0] is not None


def with_place(c: Component, **place) -> Component:
    v = copy.copy(c)
    v.params = dict(c.params)
    v.place = dict(place)
    return v


def geometry_key(d: Design, comp: Component, variant: Component) -> str:
    """What a variant actually builds (shape, sizes, every copy's position), for de-duplication."""
    vd = variant_design(d, comp, variant)
    return json.dumps([[c.name, c.shape, c.params, [[round(x, 2) for x in pos] for pos in c.positions]]
                       for c in vd.components], sort_keys=True)


def snap_to_cues(d: Design, v: Component) -> Component:
    """Put the component on the edge its own description names ("at the front edge" -> y=front)."""
    if not v.place:
        return v
    for axis in face_axes(v.place["side"]):
        cue = edge_cue(v, axis)
        if cue and axis not in arrangement_axes(v.arrangement):
            v.place[axis] = cue
    return v


class ChooseSide(PlacementStep):
    """Rank the physically possible, not-yet-rejected sides by back-translation."""

    key = "side"

    def decide(self):
        c, d = self.comp, self.design
        parent = d.component(c.draft["parent"])
        feasible = feasible_attachments(d, c, parent)
        c.draft["feasible"] = feasible
        rejected = {s for p, s in c.rejected.get("side", []) if p == parent.name}
        sides = [s for s in GRAVITY_ORDER if s in feasible and s not in rejected]
        self.logger.info(f"{c.name}: possible sides of {parent.name}: {sides} (rejected {sorted(rejected)})")
        if not sides:
            c.notes.setdefault("params", []).append(
                f"it cannot be fixed flat against any remaining face of {parent.name}; check its dimensions")
            c.rejected.pop("side", None)
            c.draft = None
            return Status.FAILURE
        if len(sides) == 1:
            c.draft["side"] = sides[0]
            return Status.SUCCESS
        variants = {s: with_place(c, **dict({"x": "center", "y": "center", "z": "center"},
                                            parent=parent.name, side=s, **feasible[s][0]))
                    for s in sides}
        for v in variants.values():
            v.arrangement = None
        scores = rank_variants(self.llm, d, c, variants, edges=(), label=f"side_{c.name}")
        if side_cue(c) in scores:
            scores[side_cue(c)] += CUE_BONUS
        top = max(scores.values())
        best = next(s for s in sides if scores[s] >= top - 0.05)  # near-ties go to the ordinary option
        self.logger.info(f"{c.name}: side scores {fmt_scores(scores)} -> {best}")
        c.draft["side"] = best
        return Status.SUCCESS


def fmt_scores(scores: Dict[str, float]) -> str:
    return "{" + ", ".join(f"{k}: {v:.2f}" for k, v in scores.items()) + "}"


class ChooseArrangement(PlacementStep):
    """How several copies are laid out on the parent's face (ranked by back-translation)."""

    key = "arrangement"

    def decide(self):
        c, d = self.comp, self.design
        if c.count <= 1:
            c.draft["arrangement"] = None
            return Status.SUCCESS
        parent, side = c.draft["parent"], c.draft["side"]
        axes = face_axes(side)
        options = (["corners_" + "".join(axes)] if c.count == 4 else []) + \
                  (["triangle_" + "".join(axes)] if c.count == 3 and side in ("top", "bottom") else []) + \
                  [("ends_" if c.count == 2 else "row_") + a for a in axes]
        options = [o for o in options if o not in c.rejected.get("arrangement", [])] or options
        first = c.draft["feasible"][side][0]
        variants = {}
        for o in options:
            v = with_place(c, **dict({"x": "center", "y": "center", "z": "center"}, parent=parent, side=side, **first))
            v.arrangement = o
            variants[o] = v
        scores = rank_variants(self.llm, d, c, variants, edges=(), label=f"arrangement_{c.name}")
        cue = arrangement_cue(c)
        for o in scores:
            if cue and o.startswith(cue):
                scores[o] += CUE_BONUS
        best = max(options, key=lambda o: (round(scores[o], 2), -options.index(o)))
        self.logger.info(f"{c.name}: arrangement scores {fmt_scores(scores)} -> {best}")
        c.draft["arrangement"] = best
        return Status.SUCCESS


SPAN_WORDS = {"x": "full width (left to right)", "y": "full depth (front to back)", "z": "full height"}


def size_param(comp: Component, axis: str) -> Optional[str]:
    """The parameter that directly sets this component's extent along an axis, if any."""
    if comp.shape in ("box", "wedge"):
        return {"x": "width", "y": "depth", "z": "height"}[axis]
    if comp.shape in ("cylinder", "tube"):
        across = "diameter" if comp.shape == "cylinder" else "outer_diameter"
        return "height" if axis == comp.params["axis"] else across
    if comp.shape == "sphere":
        return "diameter"
    if comp.shape == "panel":
        if axis == "z":
            return "height"
        sideways = comp.params["lean"] in ("left", "right")
        return "width" if (axis == "x") != sideways else None
    return None


class ChooseEdges(PlacementStep):
    """Where on the face, one axis at a time: start edge, centre, end edge, or the full span.

    Each option is described in plain English and ranked; choosing "full span"
    makes Python copy the parent's size into the component's parameter.
    """

    key = "align"

    def decide(self):
        c, d = self.comp, self.design
        parent = d.component(c.draft["parent"])
        side = c.draft["side"]
        feasible = c.draft.get("feasible", {}).get(side) or [{}]
        place = dict({"x": "center", "y": "center", "z": "center"}, parent=parent.name, side=side, **feasible[0])
        done: List[str] = []

        def allowed(axis: str, value: str) -> bool:
            # some feasible alignment agrees with every axis decided so far and with this value
            return any(al.get(axis, value) == value and all(al.get(k, place[k]) == place[k] for k in done)
                       for al in feasible)

        for axis in face_axes(side):
            if axis in arrangement_axes(c.draft.get("arrangement")):
                continue
            i = "xyz".index(axis)
            if abs(c.size[i] - parent.size[i]) <= ABS_TOL:
                place[axis] = "center"   # already as long as the parent
                done.append(axis)
                continue
            bad = {v for p, s, a, v in c.rejected.get("align", []) if (p, s, a) == (parent.name, side, axis)}
            variants: Dict[str, Component] = {}
            for value in ALIGN[axis]:
                if value in bad or not allowed(axis, value):
                    continue
                v = with_place(c, **dict(place, **{axis: value}))
                v.arrangement = c.draft.get("arrangement")
                variants[value] = v
            cue = edge_cue(c, axis)
            if cue in variants:
                place[axis] = cue
                done.append(axis)
                self.logger.info(f"{c.name}: {axis} -> {cue} (from the description's wording)")
                continue
            name = size_param(c, axis)
            other_edge = any(edge_cue(c, a) not in (None, "center") for a in face_axes(side) if a != axis)
            if (name and other_edge and re.search(SPAN_CUE, cue_text(c)) and params_valid(
                    with_place(c, **place)) and 0.5 <= parent.size[i] / c.params[name] <= 2):
                # "running along the back edge": as long as that edge
                c.params[name] = parent.size[i]
                c.size = SHAPES[c.shape].size(c.params)
                place[axis] = "center"
                done.append(axis)
                self.logger.info(f"{c.name}: {axis} spans {parent.name} (from the description's wording)")
                continue
            name = size_param(c, axis)
            target = parent.size[i]
            if name and (axis, target) not in c.rejected.get("span", []) and 0.5 <= target / c.params[name] <= 2:
                v = with_place(c, **dict(place, **{axis: "center"}))
                v.params[name] = target
                v.arrangement = c.draft.get("arrangement")
                if params_valid(v):
                    variants["span"] = v
            if not variants:
                continue
            scores = rank_variants(self.llm, d, c, variants, edges=done + [axis], label=f"align_{c.name}")
            if edge_cue(c, axis) in scores:
                scores[edge_cue(c, axis)] += CUE_BONUS
            order = list(variants)
            top = max(scores.values())
            near = [k for k in order if scores[k] >= top - 0.05]
            best = "center" if "center" in near else max(near, key=lambda k: (scores[k], -order.index(k)))
            self.logger.info(f"{c.name}: {axis} scores {fmt_scores(scores)} -> {best}")
            if best == "span":
                c.params[name] = target
                c.size = SHAPES[c.shape].size(c.params)
                place[axis] = "center"
            else:
                place[axis] = best
            done.append(axis)
        c.draft.update({k: place[k] for k in "xyz"})
        c.draft["align"] = True
        return Status.SUCCESS


class FinishPlacement(PlacementStep):
    key = "finish"

    def update(self):
        c = self.comp
        if c.draft is not None:
            c.place = {k: c.draft.get(k, "center") for k in ("parent", "side", "x", "y", "z")}
            c.arrangement = c.draft.get("arrangement")
            c.notes.pop("place", None)
            c.draft = None
            self.logger.info(f"{c.name}: placed {json.dumps(c.place)}"
                             + (f", {c.count} copies {c.arrangement}" if c.count > 1 else ""))
        return Status.SUCCESS


PLACEMENT_STEPS = (StartPlacement, ChooseParent, ChooseSide, ChooseArrangement, ChooseEdges, FinishPlacement)


def component_subtree(design: Design, llm: OllamaAgent, comp: Component) -> py_trees.behaviour.Behaviour:
    place = py_trees.composites.Sequence(f"place:{comp.name}", memory=True,
                                         children=[cls(design, llm, comp) for cls in PLACEMENT_STEPS])
    return py_trees.composites.Sequence(comp.name, memory=True, children=[
        ChooseShape(design, llm, comp),
        FillParams(design, llm, comp),
        place,
    ])


# ----- numbers -------------------------------------------------------------

UNIT_SCALE = {"mm": 1.0, "cm": 10.0, "in": 25.4, "inch": 25.4, "inches": 25.4, '"': 25.4}


def request_numbers(text: str) -> List[Tuple[float, str, str]]:
    """Numbers the person gave: (value in mm or degrees, unit, surrounding snippet)."""
    found = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(mm|cm|inches|inch|in\b|\"|°|deg\w*)?", text):
        value = float(m.group(1))
        unit = (m.group(2) or "").lower()
        if unit.startswith("deg") or unit == "°":
            unit = "deg"
        else:
            value *= UNIT_SCALE.get(unit, 1.0)
        start, end = max(0, m.start() - 35), min(len(text), m.end() + 35)
        found.append((value, unit, text[start:end].strip()))
    return found


def number_used(value: float, unit: str, design: Design) -> bool:
    """Is this number some parameter (degrees only match angles, lengths only lengths)?"""
    candidates: List[float] = []
    for c in design.components:
        if c.count == value and unit == "":
            return True
        if not (c.shape and c.params):
            continue
        spec = SHAPES[c.shape].params
        candidates += [v for k, v in c.params.items() if isinstance(v, (int, float))
                       and (spec[k].kind == "deg") == (unit == "deg")]
        if unit == "deg":
            continue
        if c.size:
            candidates += list(c.size)
        if c.position and c.size:
            candidates.append(c.position[2] + c.size[2])  # height of its top
    return any(abs(v - value) <= max(0.5, 0.01 * value) for v in candidates)


class AccountForNumbers(Step):
    """Every number in the request must end up in some dimension.

    For each unused number, a narrow question ("which component is this about?")
    routes a note to that component's FillParams. Bounded per number.
    """

    def __init__(self, design: Design, llm: OllamaAgent, max_attempts: int = 20):
        super().__init__("account_for_numbers", design)
        self.llm, self.max_attempts = llm, max_attempts

    def update(self):
        d = self.design
        if d.human_feedback:
            return Status.SUCCESS  # once the person has spoken, their numbers win
        layout(d)
        names = [c.name for c in d.components]
        routed = False
        for value, unit, snippet in request_numbers(d.request):
            if number_used(value, unit, d):
                continue
            key = f"{fmt(value)}|{snippet}"
            tries = d.number_attempts.get(key, 0)
            if tries >= self.max_attempts:
                note = f"the request mentions {fmt(value)} ('{snippet}') but no dimension uses it"
                if note not in d.feedback_notes:
                    d.feedback_notes.append(note)
                continue
            d.number_attempts[key] = tries + 1
            schema = obj_schema({"reasoning": REASONING,
                                 "component": {"type": "string", "enum": names + ["none"]}})
            prompt = "\n".join([
                f"Object: {d.request}",
                "",
                f'The person wrote "...{snippet}...". Which component does the number {fmt(value)} describe?',
                "Components:",
                d.summary(),
                'Answer "none" if it describes the object as a whole or nothing modelled here.',
            ])
            answer, _ = self.llm.vote(prompt, schema, ["component"], label="number")
            comp = d.component(answer["component"]) if answer else None
            if comp is None:
                continue
            what = "degrees" if unit == "deg" else "mm"
            comp.notes.setdefault("params", []).append(
                f'The person wrote "{snippet}": one parameter must be exactly {fmt(value)} {what}.')
            self.logger.info(f"number {fmt(value)} routed to {comp.name}")
            routed = True
        if routed:
            self.feedback_message = "re-filling parameters for unused numbers"
            return Status.FAILURE
        return Status.SUCCESS


# ----- build ---------------------------------------------------------------


def round_parent_fractions(parent: Component, c: Component,
                           fractions: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """On a round face, pull edge/corner copies in so they stay under the circle."""
    round_axes = {"cylinder": None, "tube": None, "sphere": "xyz"}
    if parent.shape not in round_axes or not c.arrangement:
        return fractions
    axis = parent.params.get("axis", "z") if parent.shape != "sphere" else None
    circle = [a for a in "xyz" if a != axis] if axis else list("xyz")
    r = parent.size["xyz".index(circle[0])] / 2
    corners = c.arrangement.startswith(("corners", "triangle"))
    out = []
    for fr in fractions:
        new = dict(fr)
        for a, t in fr.items():
            if a not in circle:
                continue
            i = "xyz".index(a)
            free = parent.size[i] - c.size[i]
            if free <= 0:
                continue
            half = max(c.size["xyz".index(b)] for b in fr if b in circle) / 2
            reach = r / math.sqrt(2) if corners else r   # centre offset that keeps the copy inside
            offset = max(0.0, reach - half * (1.5 if corners else 1.0))
            new[a] = 0.5 + (offset / free) * (1 if t > 0.5 else -1 if t < 0.5 else 0)
        out.append(new)
    return out


def brace_target(d: Design, c: Component) -> Optional[Component]:
    """For a gusset/brace/bracket: the other component it names and braces (already laid out)."""
    if not (c.place and re.search(BRACE_WORDS, cue_text(c))):
        return None
    text = f" {c.description} ".lower()
    for other in d.components:
        if other is c or other.name == c.place["parent"] or not other.positions or not other.size:
            continue
        if re.search(rf"\b{re.escape(other.name.replace('_', ' '))}\b", text):
            return other
    return None


def layout(d: Design) -> List[str]:
    """Attach solver: every component's size and the min corner of each copy."""
    problems = []
    for i, c in enumerate(d.components):
        c.size, c.positions = None, []
        if not (c.shape and c.params):
            continue
        c.size = SHAPES[c.shape].size(c.params)
        if i == 0:
            c.positions = [(0.0, 0.0, 0.0)]
            continue
        parent = d.component(c.place["parent"]) if c.place else None
        if parent is None or parent.position is None or parent.size is None:
            problems.append(f"{c.name} has no valid parent")
            continue
        c.positions = [attach_position(parent.position, parent.size, c.size, c.place, fr)
                       for fr in round_parent_fractions(parent, c, instance_fractions(c.arrangement, c.count))]
        ref = brace_target(d, c)
        if ref and c.count > 1 and c.arrangement:
            # "a gusset on each side" means each side of what it braces, not of its parent
            fractions = instance_fractions(c.arrangement, c.count)
            for a in arrangement_axes(c.arrangement):
                i = "xyz".index(a)
                for k, fr in enumerate(fractions):
                    pos = list(c.positions[k])
                    pos[i] = ref.position[i] + (ref.size[i] - c.size[i]) * fr[a]
                    c.positions[k] = (pos[0], pos[1], pos[2])
    # Rest the whole object on the table, in the positive octant.
    placed = [(c, p) for c in d.components for p in c.positions]
    if placed:
        lo = [min(p[a] for _, p in placed) for a in range(3)]
        for c in d.components:
            c.positions = [(p[0] - lo[0], p[1] - lo[1], p[2] - lo[2]) for p in c.positions]
    return problems


def component_scad(c: Component) -> str:
    """The component's geometry (min corner at the origin). A wedge fixed underneath
    something is turned upside down so its flat face meets the part above."""
    body = SHAPES[c.shape].scad(c.params)
    if c.shape == "wedge" and c.place and c.place["side"] == "bottom":
        body = f"translate([0, 0, {fmt(c.params['height'])}]) mirror([0, 0, 1]) {{ {body} }}"
    return body


def scad_comment(text: str) -> str:
    """A one-line OpenSCAD comment: a newline in model or user text would end it and break parsing."""
    return "// " + " ".join(text.split())


def scad_source(d: Design, highlight: Optional[str] = None) -> str:
    lines = [scad_comment(d.request), f"$fn = {SEGMENTS};", ""]
    for c in d.components:
        lines.append(scad_comment(c.summary()))
        lines.append(f"module c_{c.name}() {{ {component_scad(c)} }}")
    lines += ["", "union() {"]
    for i, c in enumerate(d.components):
        if highlight is None:
            color = f'"{PART_COLORS[i % len(PART_COLORS)]}"'
        elif c.name == highlight:
            color = '"red"'
        else:
            color = '"LightGray", 0.35'
        for pos in c.positions:
            lines.append(f"    color({color}) translate({fmt_vec(pos)}) c_{c.name}();")
    lines += ["}", ""]
    return "\n".join(lines)


class Layout(Step):
    def __init__(self, design: Design):
        super().__init__("layout", design)

    def update(self):
        problems = layout(self.design)
        for p in problems:
            comp = self.design.component(p.split()[0])
            if comp:
                comp.notes.setdefault("place", []).append(p)
        return Status.FAILURE if problems else Status.SUCCESS


class EmitScad(Step):
    def __init__(self, design: Design):
        super().__init__("emit_scad", design)

    def update(self):
        d = self.design
        d.workdir.mkdir(parents=True, exist_ok=True)
        d.assembly = d.workdir / "model.scad"
        d.assembly.write_text(scad_source(d))
        write_design_json(d)
        return Status.SUCCESS


def component_report(d: Design, c: Component) -> str:
    """describe() plus the verification outcome, for people and logs.

    Kept separate from describe() on purpose: describe() is what the model judges
    in back-translation, and the verdict must not leak into its own evidence.
    """
    text = describe(d, c)
    if c.status == "unsatisfied":
        text += " [UNSATISFIED: " + "; ".join(c.residual) + "]"
    elif c.status is None:
        text += " [not verified]"
    return text


def verification_summary(d: Design) -> dict:
    """Counts for summaries: an unsatisfied or unchecked component is a failure, never a pass."""
    return {"verified": [c.name for c in d.components if c.status == "verified"],
            "unsatisfied": [c.name for c in d.unsatisfied()],
            "unchecked": [c.name for c in d.components if c.status is None],
            "all_verified": bool(d.components) and all(c.status == "verified" for c in d.components)}


def write_design_json(d: Design, outcome: Optional[str] = None) -> Path:
    """design.json: the request, run settings, every component and how its verification ended.

    Written when the SCAD is emitted (so a crash still leaves a record) and again
    at the end of the run, when the verification statuses are final.
    """
    def safe_describe(c: Component) -> Optional[str]:
        try:
            return describe(d, c)
        except Exception:  # an incomplete component (e.g. after a crash) has no description
            return None

    d.workdir.mkdir(parents=True, exist_ok=True)
    record = {
        "request": d.request, "base_request": d.base_request or d.request,
        "seed": d.seed, "l1": d.l1, "outcome": outcome,
        "verification": verification_summary(d),
        "notes": list(d.feedback_notes),
        "components": [
            {"name": c.name, "description": c.description, "count": c.count, "shape": c.shape,
             "params": c.params, "place": c.place, "arrangement": c.arrangement,
             "size": c.size, "positions": c.positions, "built": safe_describe(c),
             "status": c.status, "residual": c.residual}
            for c in d.components],
    }
    if d.cascade is not None and hasattr(d.cascade, "summary"):
        record["cascade"] = d.cascade.summary()
        # In cascade mode the verification matrix is the verdict, not the per-part statuses.
        rows = getattr(d.cascade, "rows", None) or []
        record["verification"]["all_verified"] = getattr(d.cascade, "outcome", None) == "verified"
        record["verification"]["l1_not_passed"] = [r["l1_id"] for r in rows if r.get("status") != "pass"]
    path = d.workdir / "design.json"
    path.write_text(json.dumps(record, indent=2, default=str))
    return path


def _boxes_touch(a: Component, b: Component) -> bool:
    for axis in range(3):
        if a.position[axis] + a.size[axis] < b.position[axis] - 1e-3:
            return False
        if b.position[axis] + b.size[axis] < a.position[axis] - 1e-3:
            return False
    return True


GROW = 0.05            # mm; contact is measured by growing one part this much
MIN_CONTACT_AREA = 20  # mm^2; less than this is an edge or a point, not a joint


POINT_CONTACT_AREA = 0.3  # mm^2; a ball on a flat face touches at one point (about 0.9 mm^2 measured)


def min_contact(a: Component, b: Component) -> float:
    """The contact area that counts as a joint between a and b.

    A ball can only ever touch a face at a point, so with the 20 mm^2 rule a ball
    foot had no feasible side at all and placement retried until the run timed out.
    """
    return POINT_CONTACT_AREA if "sphere" in (a.shape, b.shape) else MIN_CONTACT_AREA


_CONTACT_MEMO: Dict[str, float] = {}


def contact_area(a: Component, a_pos: Sequence[float], b: Component, b_pos: Sequence[float],
                 scratch: Path) -> float:
    """Area (mm^2) where the real geometry of a and b touch: b grown by GROW, intersected with a.

    Uses manifold3d (the same solids as cad_checks) when it is installed: an
    OpenSCAD minkowski took about 4 s per pair with a ball, and feasibility asks
    for up to 54 pairs per component per round. Results are memoised by geometry.
    """
    for axis in range(3):
        if a_pos[axis] + a.size[axis] < b_pos[axis] - 1e-3 or b_pos[axis] + b.size[axis] < a_pos[axis] - 1e-3:
            return 0.0
    key = json.dumps([[c.shape, c.params, bool(c.shape == "wedge" and c.place and c.place.get("side") == "bottom"),
                       [round(v, 4) for v in pos]] for c, pos in ((a, a_pos), (b, b_pos))], sort_keys=True)
    if key not in _CONTACT_MEMO:
        _CONTACT_MEMO[key] = _contact_area(a, a_pos, b, b_pos, scratch)
    return _CONTACT_MEMO[key]


def _contact_area(a: Component, a_pos: Sequence[float], b: Component, b_pos: Sequence[float],
                  scratch: Path) -> float:
    try:
        import cad_checks as cc
        if cc.m3d is not None:
            sa = cc.component_solid(a).translate([float(v) for v in a_pos])
            sb = cc.component_solid(b, GROW).translate([float(v) for v in b_pos])
            return (sa ^ sb).volume() / GROW
    except ImportError:
        pass
    scratch.mkdir(parents=True, exist_ok=True)
    src = scratch / f"contact_{a.name}__{b.name}.scad"
    src.write_text("\n".join([
        f"$fn = {SEGMENTS};",
        f"module a() {{ translate({fmt_vec(a_pos)}) {component_scad(a)} }}",
        f"module b() {{ translate({fmt_vec(b_pos)}) {component_scad(b)} }}",
        f"intersection() {{ a(); minkowski() {{ b(); cube({2 * GROW}, center=true); }} }}",
    ]))
    result = compile_scad(src, src.with_suffix(".stl"))
    return mesh_mass(result.tris)[0] / GROW if result.ok else 0.0


def feasible_attachments(d: Design, child: Component, parent: Component) -> Dict[str, List[Dict[str, str]]]:
    """Python decides where on the parent the child can really be fixed.

    Returns {side: [alignments that give a solid face contact]}, each alignment a
    dict over the side's two in-plane axes. The LLM is only offered these options.
    """
    scratch = d.workdir / "checks"
    out: Dict[str, List[Dict[str, str]]] = {}
    origin = (0.0, 0.0, 0.0)
    cache: Dict[Tuple[float, float, float], float] = {}
    for side in SIDES:
        a, b = face_axes(side)
        ok = []
        for va in ALIGN[a]:
            for vb in ALIGN[b]:
                align = {a: va, b: vb}
                pos = attach_position(origin, parent.size, child.size, dict(align, side=side))
                key = tuple(round(v, 3) for v in pos)
                if key not in cache:
                    cache[key] = contact_area(child, pos, parent, origin, scratch)
                if cache[key] >= min_contact(child, parent):
                    ok.append(align)
        if ok:
            # most central first: the default when nothing else is decided
            ok.sort(key=lambda al: sum(v != "center" for v in al.values()))
            out[side] = ok
    return out


def floating_components(d: Design, scratch: Path) -> List[Component]:
    """Components not connected (through touching geometry) to the first component."""
    connected = [d.components[0]]
    grew = True
    while grew:
        grew = False
        for c in d.components:
            if c not in connected and any(
                    contact_area(c, c.position, o, o.position, scratch) >= min(1.0, min_contact(c, o))
                    for o in connected):
                connected.append(c)
                grew = True
    return [c for c in d.components if c not in connected]


class CompileCheck(Step):
    """Compile the assembly; it must match the solver's layout and be one connected body."""

    def __init__(self, design: Design):
        super().__init__("compile_check", design)

    def update(self):
        d = self.design
        (d.workdir / "checks").mkdir(parents=True, exist_ok=True)
        result = compile_scad(d.assembly, d.workdir / "model.stl")
        if not result.ok:
            # All geometry comes from the shape library, so this is a library bug.
            raise RuntimeError(f"generated OpenSCAD failed to compile: {'; '.join(result.problems)}")
        d.mesh = result.tris
        expected_hi = [max(p[a] + c.size[a] for c in d.components for p in c.positions) for a in range(3)]
        lo, hi = result.bbox
        for a in range(3):
            if abs(lo[a]) > ABS_TOL or abs(hi[a] - expected_hi[a]) > ABS_TOL:
                raise RuntimeError(f"mesh bbox {lo}..{hi} disagrees with layout ..{expected_hi}")
        bodies = mesh_bodies(result.tris)
        if bodies > 1:
            floating = floating_components(d, d.workdir / "checks")
            for c in floating:
                parent = c.place["parent"] if c.place else "the rest"
                c.notes.setdefault("place", []).append(
                    f"it did not touch {parent}: there was a gap, so it floated instead of being attached")
                if c.place:
                    c.rejected.setdefault("side", []).append((c.place["parent"], c.place["side"]))
            self.feedback_message = f"{bodies} separate bodies"
            self.logger.warning(f"{bodies} separate bodies; floating: {[c.name for c in floating]}")
            if floating:
                return Status.FAILURE
            note = f"the model has {bodies} separate pieces"
            if note not in d.feedback_notes:
                d.feedback_notes.append(note)
        self.logger.info(f"compiled: {bodies} body, size {fmt_vec([round(v, 1) for v in hi])}")
        return Status.SUCCESS


class PhysicalChecks(Step):
    """Python physics: does the object stand on its own without tipping over?"""

    def __init__(self, design: Design):
        super().__init__("physical_checks", design)

    def update(self):
        d = self.design
        if not d.mesh:
            return Status.SUCCESS
        volume, com = mesh_mass(d.mesh)
        zmin = min(p[2] for t in d.mesh for p in t)
        hull = convex_hull([(p[0], p[1]) for t in d.mesh for p in t if p[2] < zmin + 0.01])
        d.stability = {"volume_mm3": round(volume, 1), "com": [round(v, 2) for v in com],
                       "stable": inside_hull(com[:2], hull)}
        self.logger.info(f"volume {volume:.0f} mm^3, centre of mass {fmt_vec([round(v, 1) for v in com])}")
        if d.stability["stable"]:
            return Status.SUCCESS
        self.logger.warning("it would tip over on its own")
        root = d.components[0]
        overhang = [c for c in d.components[1:] if c.place and c.place["side"] == "top" and any(
            p[a] < root.position[a] - 1e-3 or p[a] + c.size[a] > root.position[a] + root.size[a] + 1e-3
            for p in c.positions for a in (0, 1))]
        tries = d.number_attempts.get("tipping", 0)
        if overhang and tries < 20:
            d.number_attempts["tipping"] = tries + 1
            for c in overhang:
                c.notes.setdefault("params", []).append(
                    f"it sticks out past the edge of {root.name}, so the object tips over; "
                    f"it must fit within {root.name}'s footprint")
            self.feedback_message = "unstable"
            return Status.FAILURE
        note = "the centre of mass is outside the footprint: it would tip over on its own"
        if note not in d.feedback_notes:
            d.feedback_notes.append(note)
        return Status.SUCCESS


# ----- verification by back-translation --------------------------------------


class StartVerification(Step):
    def __init__(self, design: Design):
        super().__init__("start_verification", design)

    def update(self):
        self.design.flagged = []
        return Status.SUCCESS


class VerifyComponent(Step):
    """Python describes what it built; the model judges that description against the request.

    Judging a precise description is reading comprehension, which a small model
    does far more reliably than spatial reasoning. On a "no", the component is
    repaired by search: Python generates neighbouring designs (other sides,
    edges, spans, arrangements, fresh size proposals), describes each, and the
    best-ranked one replaces it. Rejected designs are never revisited.
    """

    def __init__(self, design: Design, llm: OllamaAgent, comp: Component, max_attempts: int = 60):
        super().__init__(f"verify:{comp.name}", design)
        self.llm, self.comp, self.max_attempts = llm, comp, max_attempts

    def update(self):
        d, c = self.design, self.comp
        if c.verified == c.spec_key():
            return Status.SUCCESS
        built = describe(d, c)
        if c.verify_attempts >= self.max_attempts:
            before = c.spec_key()
            best = self.restore_best()
            if c.spec_key() != before:
                d.flagged.append(c.name)  # rebuild what was restored before anything is exported
            self.give_up("saturated", f"out of verification attempts ({self.max_attempts})", best)
            return Status.SUCCESS
        conflicts = cue_conflicts(d, c)
        if conflicts:
            score = 0.0
            self.logger.info(f"{c.name}: verify failed by Python: {'; '.join(conflicts)} - {built}")
        else:
            score = self.llm.yes_score(verify_prompt(d, built), label=f"verify_{c.name}")
            self.logger.info(f"{c.name}: verify {score:.2f} - {built}")
        c.history.append((len(conflicts), score, c.verify_attempts,
                          copy.deepcopy({"params": c.params, "place": c.place, "arrangement": c.arrangement,
                                         "shape": c.shape, "count": c.count})))
        if score > 0.5:
            c.verified, c.status, c.residual = c.spec_key(), "verified", []
            d.feedback_notes = [n for n in d.feedback_notes if not n.startswith(f"UNSATISFIED {c.name}:")]
            return Status.SUCCESS
        c.verify_attempts += 1
        c.rejected.setdefault("spec", []).append(c.spec_key())
        if self.repair(built, current_ok=not conflicts):
            c.status, c.residual = None, []  # changed: pending until it is checked again
            d.flagged.append(c.name)
        else:
            # Nothing nearby is better: a local optimum. Keep it (searching on would
            # only churn) but do NOT call it verified - the check still says no.
            self.give_up("stagnated", "no neighbouring design is clearly better", c.history[-1])
        return Status.SUCCESS

    def give_up(self, reason: str, why: str, best: Optional[tuple]) -> None:
        """Stop searching and record a typed "unsatisfied" status with the residual problems.

        Before this existed, running out of attempts marked the component exactly
        like a pass, so a design could be exported as "verified" while its own
        checks still said no. The residual list is what the person (and any
        benchmark summary) sees instead.
        """
        d, c = self.design, self.comp
        residual = [f"{reason}: {why}"] + cue_conflicts(d, c)
        if best is not None and not best[0]:
            residual.append(f"back-translation judged it wrong (yes score {best[1]:.2f}): {describe(d, c)}")
        elif best is None:
            residual.append(f"could not confirm: {describe(d, c)}")
        c.verified, c.status, c.residual = c.spec_key(), "unsatisfied", residual
        note = f"UNSATISFIED {c.name}: " + "; ".join(residual)
        d.feedback_notes = [n for n in d.feedback_notes if not n.startswith(f"UNSATISFIED {c.name}:")]
        d.feedback_notes.append(note)
        self.logger.warning(note)

    def restore_best(self) -> Optional[tuple]:
        """Out of attempts: go back to the best version seen (fewest contradictions, best score, earliest).

        Returns that history entry (conflicts, score, attempt, snapshot), or None
        when nothing was ever checked.
        """
        c = self.comp
        if not c.history:
            return None
        best = min(c.history, key=lambda h: (h[0], -h[1], h[2]))
        for k, v in best[3].items():
            setattr(c, k, copy.deepcopy(v))
        layout(self.design)
        self.logger.info(f"{c.name}: restored the best version seen (attempt {best[2]})")
        return best

    def neighbours(self, built: str) -> Dict[str, Component]:
        d, c = self.design, self.comp
        out: Dict[str, Component] = {}
        if c.place:
            parent = d.component(c.place["parent"])
            feasible = feasible_attachments(d, c, parent)
            side = c.place["side"]
            for s in feasible:
                if s != side:
                    out[f"side={s}"] = with_place(c, **dict(c.place, side=s, **feasible[s][0]))
            for al in feasible.get(side, []):
                changed = {k: v for k, v in al.items() if v != c.place.get(k) and k not in arrangement_axes(c.arrangement)}
                if len(changed) == 1:
                    (axis, value), = changed.items()
                    out[f"{axis}={value}"] = with_place(c, **dict(c.place, **changed))
            for axis in face_axes(side):
                if axis in arrangement_axes(c.arrangement):
                    continue
                name, target = size_param(c, axis), parent.size["xyz".index(axis)]
                if name and abs(c.params[name] - target) > ABS_TOL and 0.5 <= target / c.params[name] <= 2:
                    v = with_place(c, **dict(c.place, **{axis: "center"}))
                    v.params[name] = target
                    out[f"span_{axis}"] = v
            if c.count > 1:
                for o in (["corners_" + "".join(face_axes(side))] if c.count == 4 else []) + \
                         (["triangle_" + "".join(face_axes(side))] if c.count == 3 and side in ("top", "bottom") else []) + \
                         [("ends_" if c.count == 2 else "row_") + a for a in face_axes(side)]:
                    if o != c.arrangement:
                        v = with_place(c, **c.place)
                        v.arrangement = o
                        out[f"arrangement={o}"] = v
        out.update(self.size_moves())
        root = d.components[0]
        if c.place and c.place["parent"] != root.name and c is not root:
            feasible_root = feasible_attachments(d, c, root)
            if "top" in feasible_root:
                out[f"parent={root.name}"] = with_place(
                    c, **dict({"x": "center", "y": "center", "z": "center"}, parent=root.name, side="top",
                              **feasible_root["top"][0]))
        note = [f'This was judged wrong: "{built}" Re-read the request and fix the dimensions.']
        for attempt in (0, 1):
            params, _ = propose_params(self.llm, d, c, note, attempt)
            if params and params != c.params:
                v = with_place(c, **c.place) if c.place else copy.copy(c)
                v.params = params
                out[f"params#{attempt}"] = v
        seen = set(c.rejected.get("geometry", [])) | {geometry_key(d, c, c)}
        unique: Dict[str, Component] = {}
        for k, v in out.items():
            if not params_valid(v):
                continue
            v = snap_to_cues(d, v)
            key = geometry_key(d, c, v)
            if key not in seen and v.spec_key() not in c.rejected.get("spec", []):
                seen.add(key)
                unique[k] = v
        return unique

    def size_moves(self, c: Optional[Component] = None) -> Dict[str, Component]:
        """Python's own size fixes: swap two dimensions, or make one thin or larger.

        Small models often copy the parent's size into the wrong axis or put the
        thickness on the wrong axis; these moves undo exactly those mistakes.
        """
        d, c = self.design, c or self.comp
        out: Dict[str, Component] = {}
        if c.shape not in ("box", "wedge"):
            return out
        dims = ["width", "depth", "height"]
        parent = d.component(c.place["parent"]) if c.place else None

        def variant(**changes) -> Component:
            v = with_place(c, **c.place) if c.place else copy.copy(c)
            if not c.place:
                v.params = dict(c.params)
            v.params.update(changes)
            return v

        for a, b in (("width", "depth"), ("width", "height"), ("depth", "height")):
            if abs(c.params[a] - c.params[b]) > ABS_TOL:
                out[f"swap_{a}_{b}"] = variant(**{a: c.params[b], b: c.params[a]})
        thin = {min(c.params[k] for k in dims)}
        if parent and parent.size:
            thin.add(min(parent.size))
        for k in dims:
            for t in sorted(thin):
                if t < 0.5 * c.params[k]:
                    out[f"{k}={fmt(t)}"] = variant(**{k: t})
        axis_of = {"width": 0, "depth": 1, "height": 2}
        for k in dims:  # grow: half of the parent's, or of the largest part's, extent on that axis
            i = axis_of[k]
            for t in {parent.size[i] / 2 if parent and parent.size else 0,
                      max((o.size[i] for o in d.components if o.size and o is not c), default=0) / 2}:
                if t > 2 * c.params[k]:
                    out[f"{k}={fmt(t)}"] = variant(**{k: t})
        if c.shape == "wedge":  # a wedge's run: as long as it is tall, or half of that
            run = "depth" if c.params["high_side"] in ("back", "front") else "width"
            for t in (c.params["height"], c.params["height"] / 2):
                if abs(t - c.params[run]) > ABS_TOL:
                    out[f"{run}={fmt(t)}"] = variant(**{run: t})
        return out

    def repair(self, built: str, current_ok: bool = False) -> bool:
        """Replace the component with its best-ranked neighbour. Returns False when the
        current design (free of contradictions) ranks at least as well as every neighbour."""
        d, c = self.design, self.comp
        cue = shape_cue(c)
        if cue and cue != c.shape and cue not in c.rejected.get("shape", []):
            c.notes.setdefault("shape", []).append(f"It is described like a {cue}.")
            return True  # ChooseShape will pick the cued shape, then params and placement follow
        current_key = geometry_key(d, c, c)
        candidates = self.neighbours(built)
        c.rejected.setdefault("spec", []).append(c.spec_key())
        c.rejected.setdefault("geometry", []).append(current_key)
        if not candidates:
            if shape_cue(c) == c.shape:  # the person's own words chose this shape: rethink the size
                c.notes.setdefault("params", []).append(f'This was judged wrong: "{built}"')
                return True
            c.notes.setdefault("shape", []).append(f"Nothing similar fits; it was {shape_phrase(c)}.")
            c.rejected.setdefault("shape", []).append(c.shape)
            return True
        if current_ok:
            candidates = {"current": copy.copy(c), **candidates}
        conflicts = {k: len(cue_conflicts(vd, vd.component(v.name)))
                     for k, v in candidates.items() for vd in [variant_design(d, c, v)]}
        if min(conflicts.values()) > 0:
            # No single move removes every contradiction: let Python search two-move
            # size fixes on its own (no model calls) and keep the clean ones.
            seen = {geometry_key(d, c, v) for v in candidates.values()} | set(c.rejected.get("geometry", []))
            for k1, v1 in list(candidates.items()):
                for k2, v2 in self.size_moves(v1).items():
                    v2 = snap_to_cues(d, v2)
                    key = geometry_key(d, c, v2)
                    if key in seen or not params_valid(v2):
                        continue
                    seen.add(key)
                    vd = variant_design(d, c, v2)
                    n = len(cue_conflicts(vd, vd.component(v2.name)))
                    if n == 0 and sum(1 for k in candidates if "+" in k) < 12:
                        candidates[f"{k1}+{k2}"] = v2
                        conflicts[f"{k1}+{k2}"] = 0
        fewest = min(conflicts.values())
        candidates = {k: v for k, v in candidates.items() if conflicts[k] == fewest}
        scores = rank_variants(self.llm, d, c, candidates, label=f"repair_{c.name}")
        for key, v in candidates.items():
            vd = variant_design(d, c, v)
            scores[key] += CUE_BONUS * cue_score(vd, vd.component(v.name))
        best = max(scores, key=scores.get)
        if "current" in scores and scores[best] - scores["current"] < 0.1:
            best = "current"  # not clearly better than what we have: keep it
        v = candidates[best]
        self.logger.info(f"{c.name}: repair candidates {fmt_scores(scores)} -> {best}")
        if best == "current":
            c.rejected["spec"].pop()
            c.rejected["geometry"].pop()
            return False
        c.params, c.place, c.arrangement = v.params, v.place, v.arrangement
        layout(d)
        return True




class ReviewGate(Step):
    """FAILURE (so the design loop re-enters) when verification sent anything back."""

    def __init__(self, design: Design):
        super().__init__("review_gate", design)

    def update(self):
        if self.design.flagged:
            self.feedback_message = f"reworking {', '.join(self.design.flagged)}"
            return Status.FAILURE
        return Status.SUCCESS


class RenderViews(Step):
    """Fixed cameras of the whole model, plus highlight renders for each component."""

    def __init__(self, design: Design, highlights: bool = False):
        super().__init__("render_views", design)
        self.with_highlights = highlights

    def update(self):
        d = self.design
        views_dir = d.workdir / "views"
        d.views, failures = render_openscad(d.assembly, VIEWS, views_dir, stem="model")
        d.highlights = {}
        if self.with_highlights:
            for c in d.components:
                src = views_dir / f"highlight_{c.name}.scad"
                src.write_text(scad_source(d, highlight=c.name))
                cams = {v: VIEWS[v] for v in HIGHLIGHT_VIEWS}
                d.highlights[c.name], more = render_openscad(src, cams, views_dir, stem=f"highlight_{c.name}")
                failures += more
        for f in failures:
            self.logger.warning(f"render failed: {f}")
        return Status.SUCCESS


# ----- optional visual review ----------------------------------------------

VISION_SYSTEM = ("You check renders of simple CAD models. Answer only from what you can see. "
                 "The red part is the one being asked about; grey see-through parts are the rest.")

VIEW_TEXT = {
    "iso": "an isometric view from the front-right, above",
    "right": "a side view from the right (the front of the object is on the LEFT of the image, "
             "the back is on the RIGHT)",
}

PROBES = {
    "box": "a ball", "panel": "a ball", "wedge": "a ball", "cylinder": "a flat square plate",
    "tube": "a flat square plate", "sphere": "a flat square plate",
}


class CheckComponentVisual(Step):
    """Ask the VLM whether the highlighted component matches its description.

    A probe with a deliberately wrong description runs first: if the VLM says
    "yes" to that, its answer for this component is not trusted ("unclear"). A
    "no" must be repeated on a rephrased question before it costs a repair.
    """

    def __init__(self, design: Design, vlm: OllamaAgent, comp: Component):
        super().__init__(f"visual:{comp.name}", design)
        self.vlm, self.comp = vlm, comp

    def ask(self, description: str, images: List[Path], views: List[str], seed: int) -> dict:
        prompt = "\n".join([
            f"The images show a CAD model of: {self.design.request}",
            *[f"Image {i + 1} is {VIEW_TEXT.get(v, v)}." for i, v in enumerate(views)],
            "",
            f"Is the RED part {description}?",
            "Judge only the red part's shape and where it sits relative to the grey parts.",
        ])
        schema = obj_schema({"reasoning": REASONING,
                             "answer": {"type": "string", "enum": ["yes", "no", "unclear"]}})
        return self.vlm.ask_json(prompt, schema, system=VISION_SYSTEM, images=images,
                                 seed=seed, label=f"visual_{self.comp.name}")

    def update(self):
        d, c = self.design, self.comp
        shots = d.highlights.get(c.name, {})
        views = [v for v in HIGHLIGHT_VIEWS if v in shots]
        if not views:
            d.visual[c.name] = {"answer": "unclear", "reasoning": "no render"}
            return Status.SUCCESS
        images = [shots[v] for v in views]
        try:
            probe = self.ask(PROBES.get(c.shape or "", "a ball"), images, views, seed=7)
            if probe.get("answer") == "yes":
                d.visual[c.name] = {"answer": "unclear", "reasoning": "vision model failed the probe"}
                self.logger.info(f"{c.name}: vision probe failed; not trusted")
                return Status.SUCCESS
            verdict = self.ask(c.description, images, views, seed=0)
            if verdict.get("answer") == "no":
                again = self.ask(f"this: {c.description}", images, views, seed=1)
                if again.get("answer") != "no":
                    verdict = {"answer": "unclear", "reasoning": "answers disagreed"}
        except ValueError:
            verdict = {"answer": "unclear", "reasoning": "unreadable reply"}
        d.visual[c.name] = verdict
        self.logger.info(f"{c.name}: visual {verdict.get('answer')} - {verdict.get('reasoning', '')}")
        return Status.SUCCESS


class VisualVerdict(Step):
    """Turn the visual answers into targeted repairs, keeping the best design so far."""

    def __init__(self, design: Design, llm: OllamaAgent, max_rounds: int = 20):
        super().__init__("visual_verdict", design)
        self.llm, self.max_rounds = llm, max_rounds

    def update(self):
        d = self.design
        if not d.visual:
            return Status.SUCCESS
        score = sum(1 for v in d.visual.values() if v.get("answer") == "yes")
        failed = [n for n, v in d.visual.items() if v.get("answer") == "no" and d.component(n)]
        if d.best is None or score > d.best[0]:
            d.best = (score, copy.deepcopy(d.components))
        elif score < d.best[0]:
            self.logger.info(f"visual score fell ({score} < {d.best[0]}); restoring the best design")
            d.components = copy.deepcopy(d.best[1])
            d.visual_rounds = self.max_rounds
            d.visual = {}
            return Status.FAILURE  # rebuild the restored design; no more visual repairs
        self.logger.info(f"visual score {score}/{len(d.components)}; failed: {failed}")
        if not failed or d.visual_rounds >= self.max_rounds:
            for n in failed:
                note = f"vision check doubts {n}: {d.visual[n].get('reasoning', '')}"
                if note not in d.feedback_notes:
                    d.feedback_notes.append(note)
            return Status.SUCCESS
        d.visual_rounds += 1
        for name in failed:
            comp = d.component(name)
            complaint = d.visual[name].get("reasoning", "it does not match its description")
            schema = obj_schema({"reasoning": REASONING,
                                 "aspect": {"type": "string", "enum": ["shape", "params", "place"]}})
            prompt = "\n".join([
                f"Object: {d.request}",
                f"Component: {comp.summary()}",
                f"A reviewer looking at the render says: {complaint}",
                "",
                "What must change to fix it?",
                "- shape: it should be a different kind of shape",
                "- params: right shape, wrong dimensions, angle or direction",
                "- place: right shape, attached in the wrong place or on the wrong side",
            ])
            answer, _ = self.llm.vote(prompt, schema, ["aspect"], label=f"repair_{name}")
            aspect = answer["aspect"] if answer else "params"
            if aspect == "place" and d.index(name) == 0:
                aspect = "params"
            comp.notes.setdefault(aspect, []).append(f"A reviewer of the render said: {complaint}")
            self.logger.info(f"repair {name}: {aspect}")
        d.visual = {}
        self.feedback_message = f"repairing {', '.join(failed)}"
        return Status.FAILURE


# ----- human ---------------------------------------------------------------


class HumanReview(Step):
    """The person accepts the design or describes changes, which are routed to components."""

    def __init__(self, design: Design, llm: OllamaAgent, input_fn: Callable[[str], str] = input,
                 auto_approve: bool = False):
        super().__init__("human_review", design)
        self.llm, self.input_fn, self.auto_approve = llm, input_fn, auto_approve

    def update(self):
        d = self.design
        if self.auto_approve:
            return Status.SUCCESS
        self.show()
        answer = self.input_fn("Accept? [Enter/y = accept and export, q = quit, or describe changes]\n> ").strip()
        if answer.lower() in ACCEPT_WORDS:
            return Status.SUCCESS
        if answer.lower() in QUIT_WORDS:
            raise UserAbort()
        d.feedback_notes.clear()
        d.human_feedback.append(answer)
        apply_feedback(d, self.llm, answer)
        for c in d.components:
            c.verify_attempts = 0
        d.visual_rounds = 0
        d.best = None
        self.feedback_message = "changes requested"
        return Status.FAILURE

    def show(self) -> None:
        """What the person sees before deciding (the cascade mode shows its verification matrix)."""
        d = self.design
        print("\n" + "=" * 72)
        print(d.request)
        for c in d.components:
            print(f"  - {component_report(d, c)}")
        unsatisfied = d.unsatisfied()
        if unsatisfied:
            print(f"\n  WARNING: {len(unsatisfied)} component(s) failed verification: "
                  f"{', '.join(c.name for c in unsatisfied)}")
        print(f"\nOpenSCAD: {d.assembly}")
        for name, path in d.views.items():
            print(f"  {name:>5}: {path}")
        for note in d.feedback_notes:
            print(f"  note: {note}")
        print("=" * 72)


def apply_feedback(d: Design, llm: OllamaAgent, feedback: str) -> None:
    """Route free-text feedback to component-level changes."""
    names = [c.name for c in d.components]
    schema = obj_schema({"changes": {"type": "array", "minItems": 1, "items": obj_schema({
        "component": {"type": "string", "enum": names + ["new"]},
        "change": {"type": "string", "enum": ["shape", "params", "place", "add", "remove"]},
        "instruction": {"type": "string"},
    })}})
    prompt = "\n".join([
        f"Object: {d.request}",
        "Components:",
        d.summary(),
        "",
        f"The person reviewing the design says: {feedback}",
        "",
        "Turn this into changes. For each change give the component and what changes:",
        "- shape: different kind of shape   - params: dimensions, angle or direction",
        "- place: where it attaches         - remove: delete the component",
        '- add: a new component (component = "new"; instruction = its description)',
    ])
    try:
        changes = llm.ask_json(prompt, schema, label="feedback").get("changes") or []
    except ValueError:
        changes = []
    if not changes:
        for c in d.components:
            c.notes.setdefault("params", []).append(f"The person said: {feedback}")
        return
    for ch in changes:
        kind, instruction = ch.get("change"), str(ch.get("instruction") or feedback)
        comp = d.component(ch.get("component", ""))
        if kind == "add" or comp is None:
            name = slugify(" ".join(instruction.split()[:3]))[:24] or f"part{len(d.components)}"
            while d.component(name):
                name += "_2"
            d.components.append(Component(name, instruction))
            for comp in d.components:
                comp.others = [o.name for o in d.components if o is not comp]
        elif kind == "remove":
            if d.index(comp.name) == 0:
                continue
            for other in d.components:
                if other.place and other.place.get("parent") == comp.name:
                    other.place = None
            d.components.remove(comp)
        else:
            comp.notes.setdefault(kind, []).append(f"The person said: {instruction}")
            comp.description += f" ({instruction})"
            comp.rejected.clear()  # the person's word reopens every option


class ExportModel(Step):
    def __init__(self, design: Design):
        super().__init__("export", design)

    def update(self):
        d = self.design
        ok, message = export_openscad(d.assembly, d.assembly.with_suffix(".3mf"))
        if not ok:
            self.feedback_message = f"export failed: {message}"
            self.logger.error(self.feedback_message)
            return Status.FAILURE
        d.export_path = Path(message)
        self.logger.info(f"exported {d.export_path}")
        return Status.SUCCESS


# ---------------------------------------------------------------------------
# Tree
# ---------------------------------------------------------------------------


def build_tree(design: Design, llm: OllamaAgent, vlm: Optional[OllamaAgent] = None,
               input_fn: Callable[[str], str] = input, auto_approve: bool = False,
               max_rounds: int = 400, max_visual_rounds: int = 20) -> py_trees.behaviour.Behaviour:
    understand = py_trees.composites.Sequence("understand", memory=True, children=[
        ExtractComponents(design, llm),
        ForEach("components", design, lambda d: [component_subtree(d, llm, c) for c in d.components]),
    ])
    build = py_trees.composites.Sequence("build", memory=True, children=[
        Layout(design), EmitScad(design), CompileCheck(design), PhysicalChecks(design),
    ])
    verify = py_trees.composites.Sequence("verify", memory=True, children=[
        StartVerification(design),
        ForEach("verify_components", design, lambda d: [VerifyComponent(d, llm, c) for c in d.components]),
        ReviewGate(design),
    ])
    stages: List[py_trees.behaviour.Behaviour] = [
        understand, AccountForNumbers(design, llm), build, verify, RenderViews(design, highlights=vlm is not None)]
    if vlm is not None:
        stages.append(py_trees.composites.Sequence("visual_review", memory=True, children=[
            ForEach("visual", design, lambda d: [CheckComponentVisual(d, vlm, c) for c in d.components]),
            VisualVerdict(design, llm, max_rounds=max_visual_rounds),
        ]))
    stages.append(HumanReview(design, llm, input_fn=input_fn, auto_approve=auto_approve))
    design_seq = py_trees.composites.Sequence("design", memory=True, children=stages)
    return py_trees.composites.Sequence("cad", memory=True, children=[
        py_trees.decorators.Retry("design_loop", design_seq, num_failures=max_rounds),
        ExportModel(design),
    ])


def run(root: py_trees.behaviour.Behaviour, max_ticks: int = 100000) -> Status:
    """Tick the tree until it stops RUNNING."""
    tree = py_trees.trees.BehaviourTree(root)
    tree.setup()
    for _ in range(max_ticks):
        tree.tick()
        if root.status != Status.RUNNING:
            break
    return root.status


def load_l1(arg: str) -> List[dict]:
    """The person's L1 requirements from a JSON file or an inline JSON string.

    Accepts a list of {id, text, method}, or an object holding that list under
    "l1" (the shape used in benchmarks/*.json). Missing ids are numbered; a
    missing method is left as None (the cascade will choose one later).
    """
    path = Path(arg).expanduser()
    try:
        is_file = path.is_file()
    except OSError:  # an inline JSON string can be too long to be a path
        is_file = False
    data = json.loads(path.read_text() if is_file else arg)
    if isinstance(data, dict):
        data = data.get("l1", data.get("requirements"))
    if not isinstance(data, list):
        raise ValueError("L1 requirements must be a JSON list of {id, text, method}")
    out: List[dict] = []
    for i, raw in enumerate(data, 1):
        if isinstance(raw, str):
            raw = {"text": raw}
        if not isinstance(raw, dict) or not str(raw.get("text", "")).strip():
            raise ValueError(f"L1 requirement {i} has no text: {raw!r}")
        out.append({"id": str(raw.get("id") or f"L1.{i}"), "text": str(raw["text"]).strip(),
                    "method": raw.get("method")})
    return out


def request_with_l1(request: str, l1: Sequence[dict]) -> str:
    """The default pipeline has no notion of requirements, so the baseline sees them as text.

    One line, and without the ids: request_numbers() would read "L1.2" as the
    number 1.2 and AccountForNumbers would then force it into some dimension.
    """
    if not l1:
        return request
    return f"{request.rstrip()} Requirements: " + " ".join(
        r["text"] if r["text"].rstrip().endswith((".", "!", "?")) else r["text"].rstrip() + "." for r in l1)


# Exit codes. 2 is argparse's own usage-error code, so "exported but its checks still
# fail" gets 3: a benchmark must never mistake a bad command line for a built design.
EXIT_OK, EXIT_FAILED, EXIT_USAGE, EXIT_UNSATISFIED, EXIT_INTERRUPTED = 0, 1, 2, 3, 130


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build OpenSCAD models with a local LLM.")
    parser.add_argument("request", nargs="*", help="what to build (prompted if omitted)")
    parser.add_argument("--out", type=Path, default=Path("builds"), help="output directory")
    parser.add_argument("--host", default=HOST, help="Ollama server URL")
    parser.add_argument("--model", default=MODEL, help="model for the text questions")
    parser.add_argument("--judges", default="",
                        help="comma-separated models whose mean P(yes) replaces --model's for every yes/no "
                             "judgement (e.g. ornith-1.5:9b,qwen3.5:9b,gemma4:latest); empty = --model alone")
    parser.add_argument("--num-ctx", type=int, default=None,
                        help="context window for every model (smaller = less memory, so a panel's models "
                             "can stay loaded together)")
    parser.add_argument("--vision", action="store_true",
                        help="also ask a vision model to review highlight renders (slow, often unreliable)")
    parser.add_argument("--vision-model", default=None, help="vision model (default: --model)")
    parser.add_argument("--think", action="store_true", help="let the model reason first (slower)")
    parser.add_argument("--auto", action="store_true", help="accept without asking the person")
    parser.add_argument("--max-visual-rounds", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0,
                        help="offset for every LLM sampling seed; 0 = the default deterministic run")
    parser.add_argument("--l1", default=None, metavar="PATH_OR_JSON",
                        help="the person's L1 requirements: a JSON file or inline JSON list of {id,text,method}")
    parser.add_argument("--mode", default="default", choices=["default", "cascade"],
                        help="default: back-translation verification; cascade: L1s -> frozen typed checks, "
                             "closed-loop design against them (needs --l1; see cascade.py)")
    args = parser.parse_args(argv)

    base_request = " ".join(args.request).strip() or input("What should I build?\n> ").strip()
    if not base_request:
        parser.error("nothing to build")
    try:
        l1 = load_l1(args.l1) if args.l1 else []
    except (ValueError, OSError) as e:  # json.JSONDecodeError is a ValueError
        parser.error(f"--l1: {e}")
    if args.mode == "cascade" and not l1:
        parser.error("--mode cascade needs --l1 (the requirements are what the cascade controls to)")
    request = request_with_l1(base_request, l1)

    py_trees.logging.level = py_trees.logging.Level.INFO
    workdir = args.out / time.strftime("%Y%m%d-%H%M%S")
    judges = [OllamaAgent(m.strip(), args.host, think=args.think, num_ctx=args.num_ctx)
              for m in args.judges.split(",") if m.strip()]
    llm = OllamaAgent(args.model, args.host, log_dir=workdir / "llm", think=args.think, seed_offset=args.seed,
                      judges=judges, num_ctx=args.num_ctx)
    vlm = OllamaAgent(args.vision_model or args.model, args.host, log_dir=workdir / "llm",
                      think=args.think, seed_offset=args.seed) if args.vision else None
    design = Design(request=request, workdir=workdir, seed=args.seed, l1=l1, base_request=base_request)
    cascade_mod = None
    if args.mode == "cascade":
        import cascade as cascade_mod  # imported here: it imports this module back
        root = cascade_mod.build_cascade_tree(design, llm, auto_approve=args.auto)
    else:
        root = build_tree(design, llm, vlm, auto_approve=args.auto, max_visual_rounds=args.max_visual_rounds)
    print(f"Working in {workdir} (OpenSCAD: {OPENSCAD}, mode {args.mode})", flush=True)
    started = time.time()
    try:
        status = run(root)
    except UserAbort:
        write_design_json(design, "aborted")
        print(f"Stopped. Work so far is in {workdir}")
        return EXIT_FAILED
    except KeyboardInterrupt:
        write_design_json(design, "interrupted")
        print(f"\nInterrupted. Work so far is in {workdir}")
        return EXIT_INTERRUPTED
    except Exception:
        write_design_json(design, "crashed")  # benchmarks must see a crash as a crash, then the traceback
        raise
    if status == Status.SUCCESS and cascade_mod is not None:
        rec = cascade_mod.finalize(design, llm)
        write_design_json(design, rec["outcome"])
        print(f"Done: {design.export_path}")
        print(cascade_mod.matrix_text(rec))
        print(f"Matrix: {workdir / 'verification_matrix.md'}; {llm.calls} LLM calls, {time.time() - started:.0f} s")
        return EXIT_OK if rec["outcome"] == "verified" else EXIT_UNSATISFIED
    if status == Status.SUCCESS:
        unsatisfied = design.unsatisfied()
        # verification_summary also counts components still pending (status None) as failures.
        verified = verification_summary(design)["all_verified"]
        write_design_json(design, "verified" if verified else "unsatisfied")
        print(f"Done: {design.export_path}")
        for c in design.components:
            print(f"  - {component_report(design, c)}")
        for note in design.feedback_notes:
            print(f"  note: {note}")
        if not verified:
            # Exported, but it is NOT a pass: EXIT_UNSATISFIED so scripts cannot mistake it for one.
            unchecked = [c.name for c in design.components if c.status is None]
            print(f"UNSATISFIED: {len(unsatisfied)} of {len(design.components)} components failed "
                  f"verification ({', '.join(c.name for c in unsatisfied)})"
                  + (f"; not verified: {', '.join(unchecked)}" if unchecked else ""))
            return EXIT_UNSATISFIED
        return EXIT_OK
    write_design_json(design, "failed")
    print(f"Failed. See {workdir} (LLM transcripts in {workdir / 'llm'})")
    return EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
