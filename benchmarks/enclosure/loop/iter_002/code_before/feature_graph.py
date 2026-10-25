"""Feature graph: the representation of an assembly-mode design (ARCHITECTURE.md section 3.2).

The default and cascade modes describe a design as a flat list of additive
primitives placed on each other's outside faces, so an opening, a pilot hole, a
cavity or a second printed body cannot be expressed. Assembly mode describes it
as a graph of typed nodes instead:

* ``reference`` - a catalogue part (board, module, jack, plug). Never printed:
  it exists for checks and ghost renders only (``not_printed``).
* ``body`` - a printed body (base, lid); its own primitive is the body's base
  solid.
* ``add`` / ``cut`` - solids unioned into / subtracted from the body their
  ``body`` field names. A ``port_cut`` may name several bodies (it crosses the
  seam).
* ``envelope`` - a keep-out or access volume (generated from datums, M4).

Sizes and positions are expressions, never numbers typed in by the LLM:
``cavity.width = board.width + 2*spec.board_clearance``. Python resolves them
in dependency order, so changing a request number re-derives every size that
depends on it (the size-leak fix in miniature). Placement is datum-relative
(``Pose``): an anchor datum, an offset, an optional axis alignment and an
optional projection onto a plane or a body face.

Geometry is measured with manifold3d, built exactly like the SCAD this module
emits (same primitives, same 4x4 poses through ``multmatrix``, same $fn), so
the measurement and the delivered mesh cannot drift apart silently. A parity
test compiles the SCAD with OpenSCAD and compares.

This module never imports cad_agent. It imports ``parts`` (datums, catalogue
instances); ``parts`` imports this module back for the expression evaluator, so
both use only module attributes at call time.
"""

import ast
import json
import math
import struct
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union

import numpy as np

import parts as pt

try:
    import manifold3d as m3d
except ImportError:  # pragma: no cover - the geometry half is then unavailable
    m3d = None

Expr = Union[int, float, str]
Expr3 = Tuple[Expr, Expr, Expr]

KINDS = ("reference", "body", "add", "cut", "envelope")
NOT_PRINTED = frozenset({"reference", "envelope"})   # never part of a body's solid
BUILD_KINDS = ("body", "add", "cut")
PRIMITIVES = ("box", "cylinder", "tube", "shell", "part")
DEFAULT_SEGMENTS = 64                                # used only when the rules give no "fn"
NAMESPACES = ("spec", "rules", "frame")              # ref prefixes that are not node ids
EPS = 1e-9


# ---------------------------------------------------------------------------
# Expressions: a safe AST subset
# ---------------------------------------------------------------------------


class ExprError(ValueError):
    """An expression that is not in the allowed subset (or does not parse)."""

    def __init__(self, expr: Any, reason: str):
        super().__init__(f"bad expression {expr!r}: {reason}")
        self.expr = expr
        self.reason = reason


class MissingRefError(KeyError):
    """A reference that names nothing known; says which node asked for it."""

    def __init__(self, node: Optional[str], ref: str):
        super().__init__(f"{node or '<expr>'}: unknown reference {ref!r}")
        self.node = node
        self.ref = ref

    def __str__(self):
        return self.args[0]


class CycleError(ValueError):
    def __init__(self, nodes: Sequence[str]):
        super().__init__(f"dependency cycle between nodes: {', '.join(nodes)}")
        self.nodes = list(nodes)


def ceil_to(x: float, step: float) -> float:
    """x rounded up to a whole number of `step`s (step <= 0 returns x)."""
    if step <= 0:
        return float(x)
    return math.ceil(x / step - 1e-9) * step


FUNCTIONS: Dict[str, Callable[..., float]] = {"min": min, "max": max, "abs": abs, "ceil_to": ceil_to}
_BINOPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
           ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b}


def _ref_name(node: ast.AST) -> Optional[str]:
    """The canonical dotted name of a reference node (`a.b`, `n.HOLE[2].x`), or None."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _ref_name(node.value)
        return None if base is None else f"{base}.{node.attr}"
    if isinstance(node, ast.Subscript):
        base = _ref_name(node.value)
        idx = node.slice
        if base is None or not (isinstance(idx, ast.Constant) and type(idx.value) is int):
            return None
        return f"{base}[{idx.value}]"
    return None


_PARSED: Dict[str, ast.AST] = {}


def parse(expr: str) -> ast.AST:
    """Parse and validate an expression string (cached). Raises ExprError."""
    tree = _PARSED.get(expr)
    if tree is not None:
        return tree
    try:
        tree = ast.parse(expr.strip(), mode="eval").body
    except SyntaxError as e:
        raise ExprError(expr, f"syntax error ({e.msg})") from None
    _validate(expr, tree)
    _PARSED[expr] = tree
    return tree


def _validate(expr: str, node: ast.AST) -> None:
    if isinstance(node, ast.Constant):
        if type(node.value) not in (int, float):
            raise ExprError(expr, f"only numbers are allowed as constants, not {node.value!r}")
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in _BINOPS:
            raise ExprError(expr, f"operator {type(node.op).__name__} is not allowed")
        _validate(expr, node.left)
        _validate(expr, node.right)
    elif isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, (ast.USub, ast.UAdd)):
            raise ExprError(expr, f"operator {type(node.op).__name__} is not allowed")
        _validate(expr, node.operand)
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
            raise ExprError(expr, f"only {', '.join(sorted(FUNCTIONS))} may be called")
        if node.keywords or not node.args:
            raise ExprError(expr, "functions take positional arguments only")
        for a in node.args:
            _validate(expr, a)
    elif isinstance(node, (ast.Name, ast.Attribute, ast.Subscript)):
        name = _ref_name(node)
        if name is None:
            raise ExprError(expr, "a reference must be a dotted name with integer indices")
        if name.startswith("_") or "._" in name or name in FUNCTIONS:
            raise ExprError(expr, f"reference {name!r} is not allowed")
    else:
        raise ExprError(expr, f"{type(node).__name__} is not allowed")


def refs(expr: Expr) -> Set[str]:
    """Every reference an expression reads (empty for a number)."""
    if not isinstance(expr, str):
        return set()
    out: Set[str] = set()

    def walk(n: ast.AST) -> None:
        name = _ref_name(n) if isinstance(n, (ast.Name, ast.Attribute, ast.Subscript)) else None
        if name is not None:
            out.add(name)
            return
        for child in ast.iter_child_nodes(n):
            if isinstance(n, ast.Call) and child is n.func:
                continue
            walk(child)

    walk(parse(expr))
    return out


Env = Union[Mapping[str, float], Callable[[str], float]]


def evaluate(expr: Expr, env: Env = None) -> float:
    """The value of an expression. `env` maps a reference to its value (dict or callable).

    An unknown reference raises MissingRefError (node None; callers add the node).
    """
    if isinstance(expr, bool):
        raise ExprError(expr, "a boolean is not a number")
    if isinstance(expr, (int, float)):
        return float(expr)
    if not isinstance(expr, str):
        raise ExprError(expr, f"expected a number or an expression string, got {type(expr).__name__}")

    def lookup(name: str) -> float:
        if env is None:
            raise MissingRefError(None, name)
        if callable(env) and not isinstance(env, Mapping):
            return float(env(name))
        if name not in env:
            raise MissingRefError(None, name)
        return float(env[name])

    def ev(n: ast.AST) -> float:
        if isinstance(n, ast.Constant):
            return float(n.value)
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Div) and b == 0:
                raise ExprError(expr, "division by zero")
            return float(_BINOPS[type(n.op)](a, b))
        if isinstance(n, ast.UnaryOp):
            v = ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.Call):
            return float(FUNCTIONS[n.func.id](*[ev(a) for a in n.args]))
        return lookup(_ref_name(n))

    return ev(parse(expr))


def evaluate3(exprs: Sequence[Expr], env: Env = None) -> np.ndarray:
    if len(exprs) != 3:
        raise ExprError(exprs, "expected three expressions (x, y, z)")
    return np.array([evaluate(e, env) for e in exprs], dtype=float)


# ---------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------


@dataclass
class Pose:
    """Datum-relative placement (ARCHITECTURE.md section 3.2).

    at:         anchor datum ("frame.origin", "board.HOLE[2]", "pico.USB_MOUTH", or an external datum)
    offset:     added to the anchor point, in the world frame (mm, expressions)
    axis:       an axis datum; the node's +Z is rotated onto its direction
    project_to: a plane datum or a body face ("base.face[-X].outer"); the point is moved onto it
                along the plane normal
    rot_z:      rotation about the node's own Z, in degrees, applied before `axis`
    """
    at: str = "frame.origin"
    offset: Tuple[Expr, Expr, Expr] = (0, 0, 0)
    axis: Optional[str] = None
    project_to: Optional[str] = None
    rot_z: Expr = 0

    def exprs(self) -> List[Expr]:
        return list(self.offset) + [self.rot_z]

    def datum_refs(self) -> List[str]:
        return [r for r in (self.at, self.axis, self.project_to) if r]


def rot_z_matrix(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def align_z_to(direction: Sequence[float]) -> np.ndarray:
    """The rotation taking +Z onto `direction` (Rodrigues; the antiparallel case is a half turn about X)."""
    d = np.asarray(direction, dtype=float)
    n = np.linalg.norm(d)
    if n < EPS:
        raise ValueError("cannot align to a zero vector")
    d = d / n
    z = np.array([0.0, 0.0, 1.0])
    v = np.cross(z, d)
    c = float(np.dot(z, d))
    if np.linalg.norm(v) < EPS:
        if c > 0:
            return np.eye(3)
        return np.diag([1.0, -1.0, -1.0])       # half turn about X: +Z -> -Z, still a proper rotation
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1.0 / (1.0 + c))


def matrix(rotation: np.ndarray, translation: Sequence[float]) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = rotation
    m[:3, 3] = np.asarray(translation, dtype=float)
    return m


@dataclass
class PoseContext:
    """What resolve_pose needs: expression values, datum lookup and face-plane lookup."""
    env: Env
    datum: Callable[[str], Any]                    # ref -> parts datum (Point/Axis/Plane or an AxisList item)
    face: Callable[[str], Optional["pt.Plane"]] = lambda ref: None


def anchor_point(d: Any) -> np.ndarray:
    return np.asarray(d.at, dtype=float)


def resolve_pose(pose: Pose, ctx: PoseContext) -> np.ndarray:
    """The 4x4 world matrix of a pose."""
    if pose.at in ("frame.origin", "", None):
        p = np.zeros(3)
    else:
        p = anchor_point(ctx.datum(pose.at))
    p = p + evaluate3(pose.offset, ctx.env)
    if pose.project_to:
        plane = ctx.face(pose.project_to) or ctx.datum(pose.project_to)
        if not isinstance(plane, pt.Plane):
            raise MissingRefError(None, pose.project_to)
        q = np.asarray(plane.at, dtype=float)
        n = np.asarray(plane.normal, dtype=float)
        n = n / np.linalg.norm(n)
        p = p - float(np.dot(p - q, n)) * n
    r = rot_z_matrix(evaluate(pose.rot_z, ctx.env))
    if pose.axis:
        ax = ctx.datum(pose.axis)
        if not hasattr(ax, "dir"):
            raise MissingRefError(None, pose.axis)
        r = align_z_to(ax.dir) @ r
    return matrix(r, p)


# ---------------------------------------------------------------------------
# Nodes and the graph
# ---------------------------------------------------------------------------


@dataclass
class Node:
    id: str
    kind: str                                   # reference | body | add | cut | envelope
    primitive: str                              # box | cylinder | tube | shell | part
    params: Dict[str, Expr] = field(default_factory=dict)
    pose: Pose = field(default_factory=Pose)
    body: Optional[str] = None                  # add/cut: the body (or comma list for a port_cut); body: itself
    role: str = ""                              # floor, wall, lid_plate, lip, standoff, boss, port_cut, pilot ...
    part: Optional[str] = None                  # reference / part primitive: catalogue id
    source: str = "rule"                        # rule:<name> | llm:<decision> | human | estimate
    free: List[Tuple[str, Expr, Expr]] = field(default_factory=list)   # (param, lo, hi) the inner loop may move
    color: Optional[str] = None

    def bodies(self) -> List[str]:
        if self.kind == "body":
            return [self.id]
        return [b.strip() for b in (self.body or "").split(",") if b.strip()]

    def all_exprs(self) -> List[Expr]:
        out = list(self.params.values()) + self.pose.exprs()
        for _, lo, hi in self.free:
            out += [lo, hi]
        return out


FACE_PREFIX = ".face["


def parse_face_ref(ref: str) -> Optional[Tuple[str, str, str]]:
    """'base.face[-X].outer' -> ('base', '-X', 'outer'); None if it is not a face ref."""
    if FACE_PREFIX not in ref:
        return None
    node, rest = ref.split(FACE_PREFIX, 1)
    if "]" not in rest:
        return None
    side, tail = rest.split("]", 1)
    which = tail.lstrip(".") or "outer"
    if side not in ("-X", "+X", "-Y", "+Y", "-Z", "+Z") or which not in ("outer", "inner"):
        return None
    return node, side, which


def _ref_node(ref: str) -> Optional[str]:
    """The node id a reference depends on, or None for spec/rules/frame refs."""
    head = ref.split(".", 1)[0].split("[", 1)[0]
    return None if head in NAMESPACES else head


@dataclass
class Resolved:
    """A resolved graph: every param value, every pose, every placed datum, every part instance."""
    params: Dict[str, Dict[str, float]]
    poses: Dict[str, np.ndarray]
    datums: Dict[str, Any]                      # "board.HOLE" -> world-frame datum
    instances: Dict[str, Any]                   # node id -> parts.PartInstance (in the part frame)
    order: List[str]
    rules: Dict[str, float] = field(default_factory=dict)
    spec: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"params": self.params, "poses": {k: np.round(v, 9).tolist() for k, v in self.poses.items()},
                "order": self.order}

    def segments(self) -> int:
        return int(self.rules.get("fn", DEFAULT_SEGMENTS))


class FeatureGraph:
    def __init__(self, nodes: Iterable[Node] = ()):
        self.nodes: Dict[str, Node] = {}
        for n in nodes:
            self.add(n)

    def add(self, node: Node) -> Node:
        if node.id in self.nodes:
            raise ValueError(f"duplicate node id {node.id!r}")
        if node.kind not in KINDS:
            raise ValueError(f"{node.id}: unknown kind {node.kind!r}")
        if node.primitive not in PRIMITIVES:
            raise ValueError(f"{node.id}: unknown primitive {node.primitive!r}")
        if node.kind in ("add", "cut") and not node.bodies():
            raise ValueError(f"{node.id}: an {node.kind} node needs a body")
        if len(node.bodies()) > 1 and not (node.kind == "cut" and node.role == "port_cut"):
            raise ValueError(f"{node.id}: only a port_cut may modify several bodies")
        if node.primitive == "part" and not node.part:
            raise ValueError(f"{node.id}: a part primitive needs a catalogue id")
        self.nodes[node.id] = node
        return node

    def __iter__(self):
        return iter(self.nodes.values())

    def nodes_of(self, body: str) -> List[Node]:
        """The nodes that build `body`: its body node, then adds, then cuts (references never)."""
        members = [n for n in self.nodes.values() if n.kind in BUILD_KINDS and body in n.bodies()]
        return sorted(members, key=lambda n: BUILD_KINDS.index(n.kind))

    def bodies(self) -> List[str]:
        return [n.id for n in self.nodes.values() if n.kind == "body"]

    def references(self) -> List[Node]:
        return [n for n in self.nodes.values() if n.kind == "reference"]

    # ----- dependencies -----

    def dependencies(self, node: Node) -> Set[str]:
        deps: Set[str] = set()
        all_refs: Set[str] = set()
        for e in node.all_exprs():
            all_refs |= refs(e)
        for r in node.pose.datum_refs():
            if r == "frame.origin":
                continue
            face = parse_face_ref(r)
            all_refs.add(face[0] + ".face" if face else r)
        for r in all_refs:
            head = _ref_node(r)
            if head is None or head == node.id:
                continue
            if "." not in r and "[" not in r:
                continue          # a bare name is an external datum or an error found at resolve time
            deps.add(head)
        return deps

    def order(self, external: Iterable[str] = ()) -> List[str]:
        """Node ids in dependency order. CycleError / MissingRefError name the nodes."""
        external = set(external)
        deps = {}
        for n in self.nodes.values():
            d = set()
            for head in self.dependencies(n):
                if head in self.nodes:
                    d.add(head)
                elif head not in external:
                    ref = next(r for r in self._refs_of(n) if _ref_node(r) == head)
                    raise MissingRefError(n.id, ref)
            deps[n.id] = d
        done: List[str] = []
        state: Dict[str, int] = {}

        def visit(nid: str, path: List[str]) -> None:
            if state.get(nid) == 2:
                return
            if state.get(nid) == 1:
                raise CycleError(path[path.index(nid):])
            state[nid] = 1
            for d in sorted(deps[nid]):
                visit(d, path + [d])
            state[nid] = 2
            done.append(nid)

        for nid in self.nodes:
            visit(nid, [nid])
        return done

    def _refs_of(self, node: Node) -> List[str]:
        out = []
        for e in node.all_exprs():
            out += sorted(refs(e))
        out += [r for r in node.pose.datum_refs() if r != "frame.origin"]
        return out

    # ----- resolution -----

    def resolve(self, spec: Optional[Mapping[str, float]] = None, rules: Optional[Mapping[str, float]] = None,
                datums: Optional[Mapping[str, Any]] = None, catalog: Optional["pt.Catalog"] = None) -> Resolved:
        """Evaluate every expression and pose in dependency order.

        spec / rules: values for `spec.*` / `rules.*`; datums: external named datums (anchors that
        are not node datums); catalog: the parts catalogue for reference and part nodes.
        """
        spec = dict(spec or {})
        rules = dict(rules or {})
        external = dict(datums or {})
        res = Resolved({}, {}, {}, {}, [], rules=rules, spec=spec)
        res.order = self.order(external=[k.split(".", 1)[0].split("[", 1)[0] for k in external])

        def value(node_id: str, ref: str) -> float:
            if ref.startswith("spec."):
                key = ref[len("spec."):]
                if key not in spec:
                    raise MissingRefError(node_id, ref)
                return float(spec[key])
            if ref.startswith("rules."):
                key = ref[len("rules."):]
                if key not in rules:
                    raise MissingRefError(node_id, ref)
                return float(rules[key])
            head, _, rest = ref.partition(".")
            head_node = head.split("[", 1)[0]
            if head_node in res.params and rest in res.params[head_node]:
                return res.params[head_node][rest]
            if head_node in self.nodes and head_node in res.poses:
                try:
                    return pt.datum_value(res.datums, ref)
                except KeyError:
                    pass
            try:
                return pt.datum_value(external, ref)
            except KeyError:
                raise MissingRefError(node_id, ref) from None

        for nid in res.order:
            node = self.nodes[nid]
            params = self._resolve_params(node, lambda r, nid=nid: value(nid, r))
            res.params[nid] = params
            inst = None
            if node.primitive == "part" or node.kind == "reference":
                if not node.part:
                    raise MissingRefError(nid, "part")
                if catalog is None:
                    raise MissingRefError(nid, f"catalog:{node.part}")
                try:
                    inst = catalog.instantiate(node.part, params)
                except KeyError:
                    raise MissingRefError(nid, f"catalog:{node.part}") from None
                res.instances[nid] = inst
                for k, v in inst.params.items():
                    params.setdefault(k, v)

            def env(r: str, nid=nid, params=params) -> float:
                if r.startswith(nid + ".") and r[len(nid) + 1:] in params:
                    return params[r[len(nid) + 1:]]
                if r in params:
                    return params[r]
                return value(nid, r)

            ctx = PoseContext(env=env, datum=lambda r, nid=nid: self._datum(res, external, nid, r),
                              face=lambda r, nid=nid: self._face(res, nid, r))
            try:
                res.poses[nid] = resolve_pose(node.pose, ctx)
            except MissingRefError as e:
                raise MissingRefError(nid, e.ref) from None
            if inst is not None:
                for name, d in inst.datums.items():
                    res.datums[f"{nid}.{name}"] = pt.transform(d, res.poses[nid])
        return res

    def _resolve_params(self, node: Node, outer: Callable[[str], float]) -> Dict[str, float]:
        """A node's params; they may read each other (`shell.x - 2*shell.wall`) but not in a cycle."""
        pending = dict(node.params)
        done: Dict[str, float] = {}
        while pending:
            progressed = False
            for k, e in list(pending.items()):
                local = [r for r in refs(e)
                         if (r in node.params or (r.startswith(node.id + ".") and r[len(node.id) + 1:] in node.params))]
                if any((r.split(".", 1)[-1] if r.startswith(node.id + ".") else r) not in done for r in local):
                    continue

                def env(r: str) -> float:
                    if r.startswith(node.id + ".") and r[len(node.id) + 1:] in done:
                        return done[r[len(node.id) + 1:]]
                    if r in done:
                        return done[r]
                    if "." not in r and "[" not in r:
                        raise MissingRefError(node.id, r)
                    return outer(r)

                try:
                    done[k] = evaluate(e, env)
                except MissingRefError as err:
                    raise MissingRefError(node.id, err.ref) from None
                del pending[k]
                progressed = True
            if not progressed:
                raise CycleError([f"{node.id}.{k}" for k in pending])
        return done

    def _datum(self, res: Resolved, external: Mapping[str, Any], nid: str, ref: str):
        try:
            return pt.lookup_datum(res.datums, ref)
        except KeyError:
            pass
        try:
            return pt.lookup_datum(external, ref)
        except KeyError:
            raise MissingRefError(nid, ref) from None

    def _face(self, res: Resolved, nid: str, ref: str) -> Optional["pt.Plane"]:
        parsed = parse_face_ref(ref)
        if parsed is None:
            return None
        body, side, which = parsed
        if body not in res.params or body not in self.nodes:
            raise MissingRefError(nid, ref)
        return face_plane(self.nodes[body], res.params[body], res.poses[body], side, which)

    # ----- JSON -----

    def to_json(self) -> dict:
        out = []
        for n in self.nodes.values():
            d = asdict(n)
            d["pose"]["offset"] = list(n.pose.offset)
            d["free"] = [list(f) for f in n.free]
            out.append(d)
        return {"schema": 1, "nodes": out}

    @classmethod
    def from_json(cls, data: Union[dict, str]) -> "FeatureGraph":
        if isinstance(data, str):
            data = json.loads(data)
        nodes = []
        for d in data["nodes"]:
            d = dict(d)
            pose = dict(d.pop("pose", {}) or {})
            pose["offset"] = tuple(pose.get("offset", (0, 0, 0)))
            d["free"] = [tuple(f) for f in d.get("free", [])]
            nodes.append(Node(pose=Pose(**pose), **d))
        return cls(nodes)


def face_plane(node: Node, params: Mapping[str, float], pose: np.ndarray, side: str, which: str) -> "pt.Plane":
    """A box or shell face in the world frame. Inner faces exist only for shells (wall/floor offsets)."""
    if node.primitive not in ("box", "shell"):
        raise MissingRefError(node.id, f"face of a {node.primitive}")
    x, y, z = params["x"], params["y"], params["z"]
    axis = "XYZ".index(side[1])
    sign = 1.0 if side[0] == "+" else -1.0
    half = {0: x / 2, 1: y / 2}
    if axis < 2:
        coord = sign * half[axis]
    else:
        coord = z if sign > 0 else 0.0
    if which == "inner":
        if node.primitive != "shell":
            raise MissingRefError(node.id, f"inner face of a {node.primitive}")
        if axis < 2:
            coord -= sign * params["wall"]
        elif sign < 0:
            coord = params["floor"]
        elif not params.get("open_top", 0):
            coord = z - params["wall"]
    at = np.zeros(3)
    at[axis] = coord
    normal = np.zeros(3)
    normal[axis] = sign
    return pt.transform(pt.Plane(at=at.tolist(), normal=normal.tolist()), pose)


# ---------------------------------------------------------------------------
# Geometry (manifold3d) - built exactly like the SCAD below
# ---------------------------------------------------------------------------


def _need_m3d():
    if m3d is None:
        raise RuntimeError("manifold3d is not installed; feature-graph geometry is unavailable")


def _m3(mat: np.ndarray) -> np.ndarray:
    return np.asarray(mat, dtype=float)[:3, :4]


def _box(x: float, y: float, z: float):
    return m3d.Manifold.cube([x, y, z]).translate([-x / 2, -y / 2, 0.0])


def _cyl(d: float, h: float, seg: int):
    return m3d.Manifold.cylinder(h, d / 2, d / 2, seg)


def shell_inner(p: Mapping[str, float]) -> Tuple[float, float, float, float]:
    """The inner box of a shell: (x, y, z0, z1). An open top runs the cut past the rim; no floor past the base."""
    x, y, z, w, f = p["x"], p["y"], p["z"], p["wall"], p.get("floor", p["wall"])
    z0 = f if f > 0 else -1.0
    z1 = z + 1.0 if p.get("open_top", 0) else z - w
    return x - 2 * w, y - 2 * w, z0, z1


def _local_solid(node: Node, p: Mapping[str, float], inst: Any, seg: int):
    prim = node.primitive
    if prim == "box":
        return _box(p["x"], p["y"], p["z"])
    if prim == "cylinder":
        return _cyl(p["d"], p["h"], seg)
    if prim == "tube":
        outer = _cyl(p["od"], p["h"], seg)
        if p["id"] <= 0:
            return outer
        return outer - _cyl(p["id"], p["h"] + 2, seg).translate([0, 0, -1.0])
    if prim == "shell":
        ix, iy, z0, z1 = shell_inner(p)
        outer = _box(p["x"], p["y"], p["z"])
        if ix <= 0 or iy <= 0 or z1 <= z0:
            return outer
        return outer - _box(ix, iy, z1 - z0).translate([0, 0, z0])
    if prim == "part":
        return part_solid(inst, seg)
    raise ValueError(f"{node.id}: no solid for primitive {prim!r}")


def _prim_matrix(g: Any) -> np.ndarray:
    """Part-geometry primitive -> 4x4 placing a +Z-standing local solid (box min corner / cylinder base centre)."""
    if g.primitive == "box":
        return matrix(np.eye(3), g.at)
    return matrix(align_z_to(g.dir), g.at)


def part_solid(inst: Any, seg: int):
    """Union of a part instance's geometry, in the part frame."""
    _need_m3d()
    solids = []
    for g in inst.geometry:
        if g.primitive == "box":
            s = m3d.Manifold.cube(list(g.size))
        else:
            s = _cyl(g.d, g.h, seg)
        solids.append(s.transform(_m3(_prim_matrix(g))))
    return m3d.Manifold.batch_boolean(solids, m3d.OpType.Add) if len(solids) > 1 else solids[0]


def solid(node: Node, resolved: Resolved):
    """The node's solid in the world frame."""
    _need_m3d()
    seg = resolved.segments()
    local = _local_solid(node, resolved.params[node.id], resolved.instances.get(node.id), seg)
    return local.transform(_m3(resolved.poses[node.id]))


def body_solid(graph: FeatureGraph, body: str, resolved: Resolved):
    """difference(union(body base, adds), cuts). Reference and envelope nodes are never read."""
    _need_m3d()
    members = graph.nodes_of(body)
    assert all(n.kind not in NOT_PRINTED for n in members), "a reference or envelope reached a body"
    base = [n for n in members if n.kind == "body"]
    if not base:
        raise ValueError(f"no body node named {body!r}")
    adds = [solid(n, resolved) for n in members if n.kind in ("body", "add")]
    cuts = [solid(n, resolved) for n in members if n.kind == "cut"]
    out = m3d.Manifold.batch_boolean(adds, m3d.OpType.Add) if len(adds) > 1 else adds[0]
    if cuts:
        out = out - (m3d.Manifold.batch_boolean(cuts, m3d.OpType.Add) if len(cuts) > 1 else cuts[0])
    return out


def body_stats(m) -> dict:
    """Volume, bounding box, shell count (connected components) and genus of a solid."""
    bb = m.bounding_box()
    return {"volume": float(m.volume()), "bbox": [list(bb[:3]), list(bb[3:])],
            "shells": len(m.decompose()), "genus": int(m.genus())}


STL_HEADER = "<80sI"   # binary STL: fixed-size text header (NUL padded), then the triangle count


def write_stl(m, path: Path) -> Path:
    """Binary STL from a manifold (the fallback writer when OpenSCAD's CGAL times out)."""
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=float)[:, :3]
    t = np.asarray(mesh.tri_verts, dtype=np.int64)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(struct.pack(STL_HEADER, b"feature_graph manifold", len(t)))
        for tri in t:
            a, b, c = v[tri[0]], v[tri[1]], v[tri[2]]
            n = np.cross(b - a, c - a)
            ln = np.linalg.norm(n)
            n = n / ln if ln > 0 else n
            f.write(struct.pack("<12fH", *n, *a, *b, *c, 0))
    return path


# ---------------------------------------------------------------------------
# SCAD emission (same primitives, same poses)
# ---------------------------------------------------------------------------


def _num(v: float) -> str:
    s = f"{float(v):.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _vec(vs: Sequence[float]) -> str:
    return "[" + ", ".join(_num(x) for x in vs) + "]"


def _multmatrix(mat: np.ndarray) -> str:
    rows = [_vec(r) for r in np.asarray(mat, dtype=float)]
    return "multmatrix([" + ", ".join(rows) + "])"


def _scad_box(x: float, y: float, z: float) -> str:
    return f"translate({_vec([-x / 2, -y / 2, 0])}) cube({_vec([x, y, z])});"


def _scad_cyl(d: float, h: float, seg: int) -> str:
    return f"cylinder(h={_num(h)}, d={_num(d)}, $fn={seg});"


def _scad_local(node: Node, p: Mapping[str, float], inst: Any, seg: int) -> str:
    prim = node.primitive
    if prim == "box":
        return _scad_box(p["x"], p["y"], p["z"])
    if prim == "cylinder":
        return _scad_cyl(p["d"], p["h"], seg)
    if prim == "tube":
        if p["id"] <= 0:
            return _scad_cyl(p["od"], p["h"], seg)
        return (f"difference() {{ {_scad_cyl(p['od'], p['h'], seg)} "
                f"translate([0, 0, -1]) {_scad_cyl(p['id'], p['h'] + 2, seg)} }}")
    if prim == "shell":
        ix, iy, z0, z1 = shell_inner(p)
        outer = _scad_box(p["x"], p["y"], p["z"])
        if ix <= 0 or iy <= 0 or z1 <= z0:
            return outer
        return f"difference() {{ {outer} translate({_vec([0, 0, z0])}) {_scad_box(ix, iy, z1 - z0)} }}"
    if prim == "part":
        return scad_part(inst, seg)
    raise ValueError(f"{node.id}: no SCAD for primitive {prim!r}")


def scad_part(inst: Any, seg: int) -> str:
    bits = []
    for g in inst.geometry:
        local = f"cube({_vec(g.size)});" if g.primitive == "box" else _scad_cyl(g.d, g.h, seg)
        bits.append(f"{_multmatrix(_prim_matrix(g))} {local}")
    return "union() { " + " ".join(bits) + " }"


def scad_node(node: Node, resolved: Resolved) -> str:
    seg = resolved.segments()
    local = _scad_local(node, resolved.params[node.id], resolved.instances.get(node.id), seg)
    return f"{_multmatrix(resolved.poses[node.id])} {local}"


def _comment(text: str) -> str:
    return "// " + " ".join(str(text).split())


def scad_body(graph: FeatureGraph, body: str, resolved: Resolved) -> str:
    """difference(){ union(){ base; adds } cuts } for one body. References are never emitted."""
    members = graph.nodes_of(body)
    assert all(n.kind not in NOT_PRINTED for n in members), "a reference or envelope reached a body"
    adds = [n for n in members if n.kind in ("body", "add")]
    cuts = [n for n in members if n.kind == "cut"]
    if not adds:
        raise ValueError(f"no body node named {body!r}")
    lines = [_comment(f"body {body}"), "difference() {", "  union() {"]
    for n in adds:
        lines += [f"    {_comment(f'{n.kind} {n.id} ({n.role or n.primitive})')}", f"    {scad_node(n, resolved)}"]
    lines.append("  }")
    for n in cuts:
        lines += [f"  {_comment(f'cut {n.id} ({n.role or n.primitive})')}", f"  {scad_node(n, resolved)}"]
    lines.append("}")
    return "\n".join(lines) + "\n"


BODY_COLORS = ["#4f81bd", "#c0504d", "#9bbb59", "#8064a2", "#f79646"]
GHOST_COLOR = "#7f7f7f"


def scad_model(graph: FeatureGraph, resolved: Resolved) -> str:
    """Every body in its colour (closed pose), plus each reference as a %-prefixed ghost line."""
    out = [_comment("assembly: printed bodies in the closed pose; references are % ghosts (never printed)")]
    for i, body in enumerate(graph.bodies()):
        node = graph.nodes[body]
        color = node.color or BODY_COLORS[i % len(BODY_COLORS)]
        inner = scad_body(graph, body, resolved).rstrip("\n").replace("\n", "\n  ")
        out.append(f'color("{color}") {{\n  {inner}\n}}')
    for ref in graph.references():
        out.append(f'%color("{ref.color or GHOST_COLOR}") {scad_node(ref, resolved)} {_comment("ghost " + ref.id)}')
    return "\n".join(out) + "\n"
