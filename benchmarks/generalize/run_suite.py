#!/usr/bin/env python
"""Run step of the generalization control loop (loop/RUN.md): run cad_agent.py on a list of designs.

This script uses no LLM itself. It runs ``cad_agent.py --mode assembly`` once per design, strictly one
after another (one Ollama user at a time), each under a 20-minute timeout that kills the whole process
group (OpenSCAD children included). For every run it records the exit code, whether renders exist in the
package's ``views/``, and a geometry hash over the package's STL files. It then writes ``runs.jsonl`` (one row
per run, appended) and ``summary.json`` (rebuilt from every row of the iteration) with the judge-cache view:
``to_judge`` (renders present, no cached verdict) and ``cached`` (a verdict reused because the same design,
the same geometry and the same requirements / design.json / rubric were judged before).

Splits:
  train (default)  benchmarks/generalize/designs/<id>/ -> loop/iter_NNN/<id>_sS
  holdout          benchmarks/generalize/holdout/<id>/ -> loop/holdout_results/iter_NNN/<id>_sS
                   (held-out isolation: stdout carries aggregate counts only, and the verdict cache is
                   loop/holdout_results/judge_cache.json, never loop/judge_cache.json)
  regression       benchmarks/enclosure E1-01, V1, V2, V3 as in benchmarks/enclosure/loop/RUN.md
                   -> loop/iter_NNN/<id>_sS (``--regression`` is the same as ``--split regression``)

Every invocation also writes ``code_sha1.txt`` (shasum format, paths relative to the repo) over the agent
modules (every top-level ``*.py`` except tests), ``design_rules.json``, ``controller_rules.json`` and every
``part.json`` of both catalogues, and reports whether it equals the previous iteration's (``code_unchanged``).

Owner decision D1 (migration delta R01) adds two run options:
  --paraphrase K   K = 0: the request and L1s of design.json; K = 1, 2: entry K of the design's paraphrases.json (the
                   same numbers and meaning in other words). Recorded in runs.jsonl (`paraphrase`), in summary.json
                   (`paraphrase`) and in the judge-cache key (K > 0). The regression set has no paraphrases (K ignored).
  --controller stub  the authority probe: cad_agent.py --controller stub (the first offered option of every question,
                   no corrective steps, no LLM calls). Rows are named <id>_sS_stub, are never judged, and give
                   summary.json `stub_verified` (train designs the stub self-verifies, rc 0) and `llm_dependent` (train
                   designs whose LLM-run geometry differs from the stub's).

Usage (see loop/RUN.md for the full procedure):
  venv/bin/python benchmarks/generalize/run_suite.py --iter 001 --seed 1            # all train designs
  venv/bin/python benchmarks/generalize/run_suite.py --iter 001 --seed 1 G01 G16    # a subset
  venv/bin/python benchmarks/generalize/run_suite.py --iter 001 --seed 1 --regression
  venv/bin/python benchmarks/generalize/run_suite.py --iter 005 --seed 5 --paraphrase 2               # train, wording 2
  venv/bin/python benchmarks/generalize/run_suite.py --iter 005 --seed 5 --paraphrase 2 --controller stub
  venv/bin/python benchmarks/generalize/run_suite.py --iter 001 --summarize          # rebuild summary.json only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import struct
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

REPO = Path(__file__).resolve().parents[2]
MODEL = "ornith-1.5:9b"                 # the agent's controller model (one model resident at a time)
OLLAMA = "http://localhost:11434"
NUM_CTX = 8192
DEFAULT_TIMEOUT_S = 20 * 60             # per run
KILL_GRACE_S = 30                       # SIGTERM -> SIGKILL
TIMEOUT_RC = 124                        # rc recorded for a run killed by the timeout
REGRESSION_IDS = ("E1-01", "V1", "V2", "V3")
SPLITS = ("train", "holdout", "regression")
CONTROLLERS = ("llm", "stub")           # cad_agent.py --controller (D1: the stub is the authority probe)
STUB_SUFFIX = "_stub"                   # run-name suffix of a stub-controller run (<id>_sS_stub)
PARAPHRASES = "paraphrases.json"        # next to a design's design.json: {"paraphrases": [entry 1, entry 2, ...]}
CACHE_SCHEMA = 1
# Files every package must hold (enclosure RUN.md 3.4 for the regression set; a generic minimum otherwise:
# "*.stl" means at least one STL file).
PACKAGE_NEED = {"regression": ("base.stl", "lid.stl", "layout.json", "self_report.json"),
                "train": ("design.json", "layout.json", "self_report.json", "*.stl"),
                "holdout": ("design.json", "layout.json", "self_report.json", "*.stl")}
MISSING = b"<missing>"


# ---------------------------------------------------------------------------
# Paths (one object, so tests can point the whole runner at a temporary tree)
# ---------------------------------------------------------------------------


@dataclass
class Paths:
    repo: Path = REPO

    @property
    def generalize(self) -> Path:
        return self.repo / "benchmarks" / "generalize"

    @property
    def enclosure(self) -> Path:
        return self.repo / "benchmarks" / "enclosure"

    @property
    def loop(self) -> Path:
        return self.generalize / "loop"

    @property
    def designs(self) -> Path:
        return self.generalize / "designs"

    @property
    def holdout(self) -> Path:
        return self.generalize / "holdout"

    @property
    def rubric(self) -> Path:
        return self.generalize / "rubric.md"

    @property
    def holdout_results(self) -> Path:
        return self.loop / "holdout_results"

    @property
    def rules(self) -> Path:
        return self.repo / "design_rules.json"

    @property
    def registry(self) -> Path:
        return self.repo / "controller_rules.json"

    @property
    def agent(self) -> Path:
        return self.repo / "cad_agent.py"

    def catalogues(self, split: str) -> List[Path]:
        """The --parts folders for a split, in lookup order. The regression set runs exactly as the enclosure
        loop's RUN.md (its own catalogue only); the generalization designs get both catalogues."""
        if split == "regression":
            return [self.enclosure / "parts"]
        return [self.generalize / "parts", self.enclosure / "parts"]

    def all_catalogues(self) -> List[Path]:
        return [self.generalize / "parts", self.enclosure / "parts"]

    def iter_root(self, split: str) -> Path:
        return self.holdout_results if split == "holdout" else self.loop

    def iter_dir(self, split: str, nnn: str) -> Path:
        return self.iter_root(split) / f"iter_{nnn}"

    def cache_path(self, split: str) -> Path:
        return self.iter_root(split) / "judge_cache.json"

    def rel(self, p: Path) -> str:
        try:
            return str(Path(p).resolve().relative_to(self.repo.resolve()))
        except ValueError:
            return str(p)


def iter_label(n: Any) -> str:
    """'7', '007' and 7 all name iteration 007."""
    s = str(n).strip()
    if not s.isdigit():
        raise ValueError(f"iteration must be a number, got {n!r}")
    return f"{int(s):03d}"


# ---------------------------------------------------------------------------
# Cases: what to run, and which files a verdict depends on
# ---------------------------------------------------------------------------


@dataclass
class Case:
    id: str
    split: str
    request: str
    l1: List[dict]
    spec_files: List[Path] = field(default_factory=list)   # requirements.md, design.json (or source json), rubric
    paraphrase: int = 0                                     # 0 = design.json's wording, K = paraphrases.json entry K
    paraphrase_requested: Optional[int] = None              # set when a held-out design has no entry K (fell back)


def _request_entry(data: Mapping[str, Any], cid: str, source: Path) -> Mapping[str, Any]:
    reqs = data.get("requests") or []
    for r in reqs:
        if r.get("id") == cid:
            return r
    if len(reqs) == 1:
        return reqs[0]
    raise ValueError(f"{source}: no request with id {cid!r}")


def design_ids(root: Path) -> List[str]:
    """Every <root>/<id>/ that holds a design.json, sorted."""
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "design.json").is_file())


def paraphrase_entry(design_dir: Path, k: int) -> Optional[Mapping[str, Any]]:
    """Entry k (1-based) of <design>/paraphrases.json, or None when the file or the entry is missing."""
    f = design_dir / PARAPHRASES
    if not f.is_file():
        return None
    entries = json.loads(f.read_text()).get("paraphrases") or []
    return entries[k - 1] if 0 < k <= len(entries) else None


def load_cases(paths: Paths, split: str, ids: Sequence[str] = (), paraphrase: int = 0) -> List[Case]:
    """The cases of a split. `paraphrase` K > 0 takes each design's request and L1s from entry K of its paraphrases.json
    (D1 disturbance tests): a train design without it is an error; a held-out design without it falls back to its
    design.json wording and records the request (held-out isolation: nothing about it is printed). The regression set
    has no paraphrases and ignores K."""
    if split not in SPLITS:
        raise ValueError(f"unknown split {split!r}")
    if paraphrase < 0:
        raise ValueError(f"paraphrase must be 0 or a paraphrases.json entry number, got {paraphrase}")
    if split == "regression":
        cases = {}
        for src in (paths.enclosure / "enclosure.json", paths.enclosure / "variants.json"):
            for r in json.loads(src.read_text())["requests"]:
                if r["id"] in REGRESSION_IDS:
                    cases[r["id"]] = Case(r["id"], split, r["request"], list(r["l1"]),
                                          [paths.enclosure / "requirements.md", src, paths.enclosure / "rubric.md"])
        want = list(ids) or list(REGRESSION_IDS)
        unknown = [i for i in want if i not in cases]
        if unknown:
            raise ValueError(f"not in the regression set: {', '.join(unknown)}")
        return [cases[i] for i in want]
    root = paths.designs if split == "train" else paths.holdout
    available = design_ids(root)
    want = list(ids) or available
    unknown = [i for i in want if i not in available]
    if unknown:
        raise ValueError(f"no {split} design with id {', '.join(unknown)}")
    out = []
    for cid in want:
        dj = root / cid / "design.json"
        r = _request_entry(json.loads(dj.read_text()), cid, dj)
        case = Case(cid, split, r["request"], list(r["l1"]), [root / cid / "requirements.md", dj, paths.rubric])
        if paraphrase:
            entry = paraphrase_entry(root / cid, paraphrase)
            if entry is not None:
                case.request, case.l1, case.paraphrase = entry["request"], list(entry["l1"]), paraphrase
            elif split == "train":
                raise ValueError(f"{cid}: no paraphrase {paraphrase} in {root / cid / PARAPHRASES}")
            else:
                case.paraphrase_requested = paraphrase
        out.append(case)
    return out


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def spec_sha1(files: Sequence[Path]) -> str:
    """sha1 over the verdict's inputs in order (requirements.md, design.json, rubric.md). Each file enters as
    its length and bytes, so moving bytes between files changes the hash; a missing file enters as a marker,
    so the hash changes when it appears."""
    h = hashlib.sha1()
    for p in files:
        p = Path(p)
        data = p.read_bytes() if p.is_file() else MISSING
        h.update(f"{len(data)}:".encode())
        h.update(data)
    return h.hexdigest()


def stl_files(pkg: Optional[Path]) -> List[Path]:
    if pkg is None or not Path(pkg).is_dir():
        return []
    return sorted((p for p in Path(pkg).rglob("*") if p.is_file() and p.suffix.lower() == ".stl"),
                  key=lambda p: p.relative_to(pkg).as_posix())


STL_ROUND = 1e-4                        # mm: vertex rounding of the canonical geometry hash (delta 002 C3)


def stl_triangles(data: bytes) -> Optional[List[tuple]]:
    """The triangles of an STL file (binary or ASCII) as vertex triples, or None when the bytes are not an STL with at
    least one triangle."""
    if len(data) >= 84:
        n = struct.unpack_from("<I", data, 80)[0]
        if n > 0 and 84 + 50 * n == len(data):
            return [(v[0:3], v[3:6], v[6:9]) for v in (struct.unpack_from("<9f", data, 84 + 50 * k + 12)
                                                        for k in range(n))]
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        return None
    if not text.lstrip().startswith("solid"):
        return None
    try:
        verts = [tuple(float(x) for x in line.split()[1:4]) for line in text.splitlines()
                 if line.strip().startswith("vertex")]
    except ValueError:
        return None
    if not verts or len(verts) % 3 or any(len(v) != 3 for v in verts):
        return None
    return [tuple(verts[i:i + 3]) for i in range(0, len(verts), 3)]


def canonical_stl(data: bytes) -> bytes:
    """The geometry of an STL independent of facet order and file format (delta 002 C3, P-2): each triangle's vertices
    rounded to STL_ROUND and rotated to start at the smallest vertex (the winding, i.e. the facing, is kept), the
    triangles sorted. Bytes that are no STL with triangles are returned unchanged."""
    tris = stl_triangles(data)
    if not tris:
        return data

    def q(v):
        return tuple(int(round(c / STL_ROUND)) for c in v)

    canon = []
    for tri in tris:
        t = [q(v) for v in tri]
        k = min(range(3), key=lambda i: t[i])
        canon.append(tuple(t[k:] + t[:k]))
    canon.sort()
    return ("stl-canonical-1\n" + "\n".join(" ".join(f"{a} {b} {c}" for a, b, c in tri) for tri in canon)).encode()


def geometry_sha1(pkg: Optional[Path]) -> Optional[str]:
    """sha1 of the package's STL files, sorted by path inside the package: each enters as its relative path, its length
    and its canonical geometry (canonical_stl: sorted triangles, vertices rounded to STL_ROUND), so the same geometry
    written in another facet order (OpenSCAD 2021.01 is not deterministic) gets the same key. Renaming base.stl to
    lid.stl is a different geometry. None without STLs."""
    files = stl_files(pkg)
    if not files:
        return None
    h = hashlib.sha1()
    for p in files:
        data = canonical_stl(p.read_bytes())
        h.update(p.relative_to(pkg).as_posix().encode() + b"\0" + f"{len(data)}:".encode())
        h.update(data)
    return h.hexdigest()


def code_files(paths: Paths) -> List[Path]:
    """The agent version: every top-level module except tests, design_rules.json, controller_rules.json (the rule
    registry the agent reads for its authority audit, D1), and every part.json of both catalogues (enclosure loop
    ARCHITECTURE.md 8: the version includes part data)."""
    mods = sorted(p for p in paths.repo.glob("*.py")
                  if not p.name.startswith("test_") and p.name != "__init__.py")
    parts = sorted(p for cat in paths.all_catalogues() if cat.is_dir() for p in cat.glob("*/part.json"))
    rules = [f for f in (paths.rules, paths.registry) if f.is_file()]
    return mods + rules + parts


def code_listing(paths: Paths) -> str:
    """shasum-format lines ("<sha1>  <path relative to the repo>"), so `shasum -c` works from the repo root."""
    return "".join(f"{sha1_file(p)}  {paths.rel(p)}\n" for p in code_files(paths))


def previous_iteration(root: Path, nnn: str, name: str = "code_sha1.txt") -> Optional[Path]:
    """The newest iter_MMM/ (MMM < NNN) under root that holds `name`."""
    best = None
    if not root.is_dir():
        return None
    for d in root.iterdir():
        if not (d.is_dir() and d.name.startswith("iter_") and d.name[5:].isdigit()):
            continue
        if int(d.name[5:]) < int(nnn) and (d / name).is_file():
            if best is None or int(d.name[5:]) > int(best.name[5:]):
                best = d
    return best


def write_code_sha1(paths: Paths, split: str, nnn: str) -> dict:
    """Write iter_NNN/code_sha1.txt and compare it with the previous iteration's. A holdout iteration is also
    compared with the train iteration of the same number (the held-out run must use the train version)."""
    d = paths.iter_dir(split, nnn)
    d.mkdir(parents=True, exist_ok=True)
    listing = code_listing(paths)
    target = d / "code_sha1.txt"
    changed_within = target.is_file() and target.read_text() != listing
    target.write_text(listing)
    prev = previous_iteration(paths.iter_root(split), nnn)
    info = {"code_sha1": hashlib.sha1(listing.encode()).hexdigest(), "files": listing.count("\n"),
            "previous_iter": prev.name if prev else None,
            "code_unchanged": (prev / "code_sha1.txt").read_text() == listing if prev else None,
            "changed_within_iteration": bool(changed_within)}
    if split == "holdout":
        train = paths.iter_dir("train", nnn) / "code_sha1.txt"
        info["matches_train_iter"] = train.read_text() == listing if train.is_file() else None
    return info


# ---------------------------------------------------------------------------
# Judge cache: (design id, geometry hash, spec hash) -> verdict
# ---------------------------------------------------------------------------


def cache_key(cid: str, geometry: str, spec: str, paraphrase: int = 0) -> str:
    """design id | geometry sha1 | spec sha1, plus |p<K> for a paraphrase run (D1): a verdict is reused only for the
    wording it was given for, so MEETS across the paraphrases is measured, never inherited."""
    return f"{cid}|{geometry}|{spec}" + (f"|p{int(paraphrase)}" if paraphrase else "")


def load_cache(path: Path) -> dict:
    if not Path(path).is_file():
        return {"schema": CACHE_SCHEMA, "entries": {}}
    data = json.loads(Path(path).read_text())
    if data.get("schema") != CACHE_SCHEMA or not isinstance(data.get("entries"), dict):
        raise ValueError(f"{path}: not a judge cache (schema {CACHE_SCHEMA})")
    return data


def save_json(path: Path, data: Any) -> None:
    """Write atomically (a crash never leaves half a file)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")
    os.replace(tmp, path)


def cache_lookup(cache: Mapping[str, Any], cid: str, geometry: Optional[str], spec: Optional[str],
                 paraphrase: int = 0) -> Optional[dict]:
    if not geometry or not spec:
        return None
    entry = cache.get("entries", {}).get(cache_key(cid, geometry, spec, paraphrase))
    return entry.get("verdict") if entry else None


def cache_store(cache: dict, cid: str, geometry: str, spec: str, verdict: Mapping[str, Any], paraphrase: int = 0,
                **provenance) -> str:
    if not geometry or not spec:
        raise ValueError(f"{cid}: a verdict needs a geometry hash and a spec hash")
    key = cache_key(cid, geometry, spec, paraphrase)
    cache.setdefault("entries", {})[key] = {"id": cid, "geometry_sha1": geometry, "spec_sha1": spec,
                                            **({"paraphrase": int(paraphrase)} if paraphrase else {}),
                                            "verdict": dict(verdict), "stored": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                            **provenance}
    return key


# ---------------------------------------------------------------------------
# One run
# ---------------------------------------------------------------------------


def packages(out: Path) -> List[Path]:
    """cad_agent.py's timestamp folders under --out (YYYYmmdd-HHMMSS), oldest first."""
    if not out.is_dir():
        return []
    return sorted(p for p in out.iterdir() if p.is_dir() and p.name[:1].isdigit())


def has_renders(pkg: Optional[Path]) -> bool:
    return pkg is not None and any((Path(pkg) / "views").glob("*.png"))


def package_missing(pkg: Optional[Path], need: Iterable[str]) -> List[str]:
    out = []
    for f in need:
        if f == "*.stl":
            if not stl_files(pkg):
                out.append(f)
        elif pkg is None or not (Path(pkg) / f).is_file():
            out.append(f)
    return out


def agent_command(paths: Paths, python: str, case: Case, seed: int, l1_path: Path, out: Path,
                  catalogues: Sequence[Path], rules: Path, controller: str = "llm") -> List[str]:
    cmd = [python, str(paths.agent), "--mode", "assembly", "--auto", "--seed", str(seed),
           "--num-ctx", str(NUM_CTX)]
    if controller != "llm":
        cmd += ["--controller", controller]
    for c in catalogues:
        cmd += ["--parts", str(c)]
    return cmd + ["--rules", str(rules), "--l1", str(l1_path), "--out", str(out), case.request]


def run_with_timeout(cmd: Sequence[str], log: Path, timeout_s: float, cwd: Path) -> tuple:
    """(rc, timed_out). The child runs in its own session; on timeout or Ctrl-C the whole group is killed."""
    with open(log, "wb") as fh:
        p = subprocess.Popen(list(cmd), cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)

        def kill_group():
            for sig, grace in ((signal.SIGTERM, KILL_GRACE_S), (signal.SIGKILL, None)):
                try:
                    os.killpg(p.pid, sig)
                except ProcessLookupError:
                    return
                if grace is None:
                    p.wait()
                    return
                try:
                    p.wait(timeout=grace)
                    return
                except subprocess.TimeoutExpired:
                    continue

        try:
            return p.wait(timeout=timeout_s), False
        except subprocess.TimeoutExpired:
            kill_group()
            fh.write(f"\n[run_suite] killed after {timeout_s:g} s\n".encode())
            return TIMEOUT_RC, True
        except KeyboardInterrupt:
            kill_group()
            raise


def read_outcome(pkg: Optional[Path]) -> dict:
    """outcome / stage / last_note from the package's design.json, and the closed-loop controller's record (D1): its
    steps and kept steps, the stop reason, and the authority audit of controller_trace.json (decisions by class)."""
    if pkg is None or not (Path(pkg) / "design.json").is_file():
        return {}
    try:
        rec = json.loads((Path(pkg) / "design.json").read_text())
    except (OSError, ValueError):
        return {"outcome": "unreadable design.json"}
    assy = rec.get("assembly") or {}
    notes = assy.get("notes") or []
    out = {"outcome": rec.get("outcome"), "stage": assy.get("stage"), "last_note": notes[-1] if notes else None}
    ctl = assy.get("controller") or {}
    if ctl:
        out["controller_run"] = {k: ctl.get(k) for k in ("kind", "steps", "kept", "stop")}
    trace = Path(pkg) / "controller_trace.json"
    if trace.is_file():
        try:
            auth = json.loads(trace.read_text()).get("authority") or {}
            out["authority"] = {"decisions": auth.get("decisions") or {}, "proposal": auth.get("proposal") or {},
                                "llm_share": auth.get("llm_share"),
                                "semantic_rule_decisions": len(auth.get("semantic_rule_decisions") or []),
                                "unregistered": len(auth.get("unregistered") or [])}
        except (OSError, ValueError):
            out["authority"] = {"error": "unreadable controller_trace.json"}
    return out


def run_name(case: Case, seed: int, controller: str = "llm") -> str:
    return f"{case.id}_s{seed}" + (STUB_SUFFIX if controller == "stub" else "")


def run_case(paths: Paths, case: Case, seed: int, nnn: str, *, python: str, timeout_s: float,
             catalogues: Sequence[Path], code_sha1: str, dry_run: bool = False, controller: str = "llm") -> dict:
    d = paths.iter_dir(case.split, nnn)
    inputs = d / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    stem = case.id + (f".p{case.paraphrase}" if case.paraphrase else "")
    (inputs / f"{stem}.request.txt").write_text(case.request)
    l1_path = inputs / f"{stem}.l1.json"
    l1_path.write_text(json.dumps(case.l1, indent=2))
    name = run_name(case, seed, controller)
    out = d / name
    cmd = agent_command(paths, python, case, seed, l1_path, out, catalogues, paths.rules, controller)
    if dry_run:
        return {"name": name, "id": case.id, "split": case.split, "seed": seed, "cmd": cmd,
                "paraphrase": case.paraphrase, "controller": controller}
    out.mkdir(parents=True, exist_ok=True)
    before = set(packages(out))
    start = time.time()
    rc, timed_out = run_with_timeout(cmd, out / "run.log", timeout_s, paths.repo)
    new = [p for p in packages(out) if p not in before]
    pkg = new[-1] if new else None
    row = {"name": name, "id": case.id, "split": case.split, "seed": seed, "controller": controller,
           "paraphrase": case.paraphrase,
           **({"paraphrase_requested": case.paraphrase_requested} if case.paraphrase_requested else {}),
           "rc": rc, "timed_out": timed_out,
           "secs": round(time.time() - start, 1), "package": paths.rel(pkg) if pkg else None,
           "has_renders": has_renders(pkg), "geometry_sha1": geometry_sha1(pkg),
           "stl_files": [p.relative_to(pkg).as_posix() for p in stl_files(pkg)],
           "missing": package_missing(pkg, PACKAGE_NEED[case.split]),
           "spec_files": [paths.rel(p) for p in case.spec_files], "spec_sha1_at_run": spec_sha1(case.spec_files),
           "code_sha1": code_sha1, "catalogues": [paths.rel(c) for c in catalogues],
           "finished": time.strftime("%Y-%m-%dT%H:%M:%S")}
    row.update(read_outcome(pkg))
    with open(d / "runs.jsonl", "a") as fh:
        fh.write(json.dumps(row) + "\n")
    return row


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def read_runs(d: Path) -> List[dict]:
    """runs.jsonl rows, the last row per run name winning (a re-run replaces the earlier row), in first-seen
    order."""
    f = d / "runs.jsonl"
    if not f.is_file():
        return []
    rows: Dict[str, dict] = {}
    for line in f.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r["name"]] = r
    return list(rows.values())


def verdict_flags(v: Optional[Mapping[str, Any]]) -> Dict[str, bool]:
    """MEETS / CORRECT from a judge verdict ({"verdict": "MEETS" | "DNM", "class": "CORRECT" | "MINOR" |
    "WRONG", ...}). A MEETS verdict counts as CORRECT too. Generalize delta 003 C0: the boolean form {"meets": true,
    "class": ...} is accepted as well (iteration 003's orchestrator wrote it, and it was mis-scored as DNM)."""
    if not v:
        return {"meets": False, "correct": False}
    verdict = str(v.get("verdict", "")).upper()
    cls = str(v.get("class", "")).upper()
    meets = verdict == "MEETS" or v.get("meets") is True
    return {"meets": meets, "correct": meets or cls == "CORRECT"}


def is_stub(row: Mapping[str, Any]) -> bool:
    return row.get("controller") == "stub"


def authority_summary(llm_rows: Sequence[dict], stub_rows: Sequence[dict]) -> dict:
    """D1 authority measurement for one iteration: `stub_verified` (train designs the stub run self-verifies, rc 0),
    `llm_dependent` (train designs, run under both controllers, whose LLM-run geometry hash differs from the stub's; two
    runs without geometry are the same), and the closed-loop record summed over the LLM train runs (steps, kept steps,
    decisions by class, semantic-rule decisions)."""
    train = [r for r in llm_rows if r.get("split") == "train"]
    stub = {r["id"]: r for r in stub_rows if r.get("split") == "train"}
    llm = {r["id"]: r for r in train}
    both = sorted(set(stub) & set(llm))
    dependent = [i for i in both if llm[i].get("geometry_sha1") != stub[i].get("geometry_sha1")]
    verified = sorted(i for i, r in stub.items() if r.get("rc") == 0)
    decisions: Dict[str, int] = {}
    steps = kept = semantic = with_steps = 0
    shares = []
    for r in train:
        ctl = r.get("controller_run") or {}
        steps += int(ctl.get("steps") or 0)
        kept += int(ctl.get("kept") or 0)
        with_steps += 1 if ctl.get("kept") else 0
        auth = r.get("authority") or {}
        semantic += int(auth.get("semantic_rule_decisions") or 0)
        for k, v in (auth.get("decisions") or {}).items():
            decisions[k] = decisions.get(k, 0) + int(v)
        if auth.get("llm_share") is not None:
            shares.append(float(auth["llm_share"]))
    designs = sorted(llm)
    return {"stub_verified": len(verified),
            "llm_dependent": dependent,
            "stub": {"runs": len(stub), "verified": verified, "compared": len(both),
                     "same_geometry": [i for i in both if i not in dependent],
                     "verified_share": (len(verified) / len(designs)) if designs else None},
            "controller": {"steps": steps, "kept": kept, "designs_with_kept_steps": with_steps,
                           "decisions": decisions, "semantic_rule_decisions": semantic,
                           "mean_llm_share": round(sum(shares) / len(shares), 4) if shares else None}}


def regression_status(rows: Sequence[dict]) -> str:
    """pass: E1-01 MEETS and V1-V3 at least CORRECT (the enclosure loop's convergence bar, per run judged);
    fail: a judged regression run is below that bar or a regression run has no output; pending: not all
    judged; not_run."""
    reg = {r["id"]: r for r in rows if r.get("split") == "regression" and not is_stub(r)}
    if not reg:
        return "not_run"
    status = "pass"
    for cid in REGRESSION_IDS:
        r = reg.get(cid)
        if r is None:
            status = "pending" if status == "pass" else status
            continue
        if not r.get("geometry_sha1"):
            return "fail"
        v = r.get("verdict")
        if v is None:
            status = "pending" if status == "pass" else status
            continue
        f = verdict_flags(v)
        if not (f["meets"] if cid == REGRESSION_IDS[0] else f["correct"]):
            return "fail"
    return status


def build_summary(paths: Paths, split_root: str, nnn: str, code_info: Optional[dict] = None) -> dict:
    """Rebuild iter_NNN/summary.json from every runs.jsonl row and the judge cache. `split_root` is 'holdout'
    for loop/holdout_results, anything else for loop/ (train and regression share an iteration folder)."""
    d = paths.iter_dir(split_root, nnn)
    cache = load_cache(paths.cache_path(split_root))
    rows = read_runs(d)
    to_judge, cached = [], []
    for r in rows:
        files = [paths.repo / f for f in r.get("spec_files", [])]
        r["spec_sha1"] = spec_sha1(files) if files else None
        r["spec_changed_since_run"] = bool(files) and r["spec_sha1"] != r.get("spec_sha1_at_run")
        if is_stub(r):                       # the authority probe is never judged (D1)
            r["verdict"], r["cache"] = None, "stub"
            continue
        v = cache_lookup(cache, r["id"], r.get("geometry_sha1"), r["spec_sha1"], r.get("paraphrase", 0))
        r["verdict"] = v
        if v is not None:
            r["cache"] = "hit"
            cached.append({"name": r["name"], "id": r["id"], "verdict": v})
        elif r.get("has_renders") and r.get("geometry_sha1"):
            r["cache"] = "miss"
            to_judge.append(r["name"])
        else:
            r["cache"] = "no_package"
    counts: Dict[str, dict] = {}
    for r in rows:
        key = r["split"] + (STUB_SUFFIX if is_stub(r) else "")     # stub rows count apart (train_stub)
        c = counts.setdefault(key, {"runs": 0, "rc": {}, "no_output": 0, "with_renders": 0, "timed_out": 0,
                                    "judged": 0, "meets": 0, "correct": 0, "to_judge": 0})
        c["runs"] += 1
        c["rc"][str(r.get("rc"))] = c["rc"].get(str(r.get("rc")), 0) + 1
        c["no_output"] += 0 if r.get("geometry_sha1") else 1
        c["with_renders"] += 1 if r.get("has_renders") else 0
        c["timed_out"] += 1 if r.get("timed_out") else 0
        c["to_judge"] += 1 if r.get("cache") == "miss" else 0
        if r.get("verdict") is not None:
            f = verdict_flags(r["verdict"])
            c["judged"] += 1
            c["meets"] += f["meets"]
            c["correct"] += f["correct"]
    listing = d / "code_sha1.txt"
    shas = sorted({r.get("code_sha1") for r in rows if r.get("code_sha1")})
    llm_rows = [r for r in rows if not is_stub(r)]
    paras = sorted({int(r.get("paraphrase", 0)) for r in llm_rows if r.get("split") in ("train", "holdout")})
    summary = {"iter": nnn, "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "code_sha1": hashlib.sha1(listing.read_bytes()).hexdigest() if listing.is_file() else None,
               "runs_on_one_code_version": len(shas) <= 1, "code_versions": shas,
               "counts": counts, "regression": regression_status(rows),
               "paraphrase": (paras[0] if len(paras) == 1 else paras) if paras else None,
               **authority_summary(llm_rows, [r for r in rows if is_stub(r)]),
               "to_judge": to_judge, "cached": cached, "runs": rows}
    if code_info:
        summary["code"] = code_info
    elif (d / "summary.json").is_file():      # a rebuild keeps the code comparison of the last Run
        try:
            summary["code"] = json.loads((d / "summary.json").read_text()).get("code")
        except ValueError:
            pass
    if split_root == "holdout":
        h = counts.get("holdout", {"runs": 0, "correct": 0, "judged": 0})
        summary["holdout_score"] = (h["correct"] / h["runs"]) if h["runs"] and h["judged"] == h["runs"] else None
    save_json(d / "summary.json", summary)
    return summary


# ---------------------------------------------------------------------------
# Preflight and CLI
# ---------------------------------------------------------------------------


def preflight(host: str = OLLAMA, model: str = MODEL, need_ollama: bool = True) -> List[str]:
    """Problems that must stop the Run step: another agent running (one run at a time), or, when the runs use the LLM,
    the Ollama server or the model missing (a stub-controller run needs no LLM: need_ollama=False)."""
    problems = []
    for pat in ("cad_agent.py", "benchmarks/run.py"):
        try:
            hit = subprocess.run(["pgrep", "-fl", pat], capture_output=True, text=True).stdout.strip()
        except OSError:
            hit = ""
        if hit:
            problems.append(f"another process is using Ollama ({pat}):\n{hit}")
    if not need_ollama:
        return problems
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=10) as resp:
            names = [m["name"] for m in json.load(resp).get("models", [])]
        if model not in names:
            problems.append(f"model {model} is not on the Ollama server ({', '.join(names) or 'none'})")
    except (OSError, ValueError) as e:
        problems.append(f"Ollama is not reachable at {host}: {e}")
    return problems


def default_python(paths: Paths) -> str:
    venv = paths.repo / "venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def build_parser() -> argparse.ArgumentParser:
    """The command line (also used by the tests that check loop/launch_config.json's commands)."""
    ap = argparse.ArgumentParser(description="Run cad_agent.py on the generalization suite (no LLM here).")
    ap.add_argument("ids", nargs="*", help="design ids (default: every design of the split)")
    ap.add_argument("--iter", required=True, help="iteration number NNN")
    ap.add_argument("--seed", type=int, default=None, help="seed S for every run (required unless --summarize)")
    ap.add_argument("--split", choices=SPLITS, default="train")
    ap.add_argument("--regression", action="store_true", help="same as --split regression")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S, help="seconds per run (default 1200)")
    ap.add_argument("--parts", type=Path, action="append", default=None,
                    help="override the catalogue folders (repeatable; default: both catalogues, or the enclosure "
                         "catalogue for --regression)")
    ap.add_argument("--python", default=None, help="interpreter for cad_agent.py (default: venv/bin/python)")
    ap.add_argument("--summarize", action="store_true", help="only rebuild summary.json from runs.jsonl")
    ap.add_argument("--dry-run", action="store_true", help="print the commands, run nothing")
    ap.add_argument("--no-preflight", action="store_true", help="skip the Ollama / single-user checks")
    ap.add_argument("--paraphrase", type=int, default=0, metavar="K",
                    help="0: design.json's request and L1s; K > 0: entry K of each design's paraphrases.json (D1 "
                         "disturbance tests; ignored for the regression set)")
    ap.add_argument("--controller", choices=CONTROLLERS, default="llm",
                    help="llm (default) or stub: the D1 authority probe (first offered option, no corrective steps, no "
                         "LLM calls); stub runs are named <id>_sS_stub and are never judged")
    return ap


def main(argv: Optional[Sequence[str]] = None, paths: Optional[Paths] = None) -> int:
    paths = paths or Paths()
    ap = build_parser()
    args = ap.parse_args(argv)
    split = "regression" if args.regression else args.split
    nnn = iter_label(args.iter)
    quiet = split == "holdout"            # held-out isolation: aggregate output only

    if args.summarize:
        s = build_summary(paths, split, nnn)
        print(json.dumps({"iter": nnn, "counts": s["counts"], "regression": s["regression"],
                          "to_judge": len(s["to_judge"]), "cached": len(s["cached"])} if quiet else
                         {"iter": nnn, "counts": s["counts"], "regression": s["regression"],
                          "to_judge": s["to_judge"], "cached": [c["name"] for c in s["cached"]],
                          "paraphrase": s["paraphrase"], "stub_verified": s["stub_verified"],
                          "llm_dependent": s["llm_dependent"]}, indent=2))
        return 0
    if args.seed is None:
        ap.error("--seed is required")
    if args.paraphrase < 0:
        ap.error("--paraphrase must be 0 or a paraphrases.json entry number")
    cases = load_cases(paths, split, args.ids, paraphrase=0 if split == "regression" else args.paraphrase)
    catalogues = list(args.parts) if args.parts else paths.catalogues(split)
    python = args.python or default_python(paths)
    if args.dry_run:
        for c in cases:
            row = run_case(paths, c, args.seed, nnn, python=python, timeout_s=args.timeout,
                           catalogues=catalogues, code_sha1="", dry_run=True, controller=args.controller)
            print(" ".join(row["cmd"][:-1]) + " '<request>'" if not quiet else row["name"])
        return 0
    if not args.no_preflight:
        problems = preflight(need_ollama=args.controller != "stub")
        if problems:
            print("preflight failed:\n- " + "\n- ".join(problems), file=sys.stderr)
            return 2
    code = write_code_sha1(paths, split, nnn)
    if not quiet:
        print(f"iter {nnn} split {split}: {len(cases)} runs, seed {args.seed}, controller {args.controller}, "
              f"paraphrase {0 if split == 'regression' else args.paraphrase}, code {code['code_sha1'][:12]} "
              f"(unchanged vs {code['previous_iter']}: {code['code_unchanged']})", flush=True)
    for i, c in enumerate(cases, 1):
        row = run_case(paths, c, args.seed, nnn, python=python, timeout_s=args.timeout, catalogues=catalogues,
                       code_sha1=code["code_sha1"], controller=args.controller)
        if not quiet:
            print(f"[{i}/{len(cases)}] {row['name']} rc={row['rc']} {row['secs']} s renders={row['has_renders']} "
                  f"missing={row['missing']} stage={row.get('stage')}", flush=True)
        else:
            print(f"[{i}/{len(cases)}] done", flush=True)
    s = build_summary(paths, split, nnn, code_info=code)
    if quiet:
        print(json.dumps({"iter": nnn, "runs": len(cases), "to_judge": len(s["to_judge"]),
                          "cached": len(s["cached"])}))
    else:
        print(json.dumps({"counts": s["counts"], "regression": s["regression"], "to_judge": s["to_judge"],
                          "cached": [c["name"] for c in s["cached"]], "code_unchanged": code["code_unchanged"],
                          "paraphrase": s["paraphrase"], "stub_verified": s["stub_verified"],
                          "llm_dependent": s["llm_dependent"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
