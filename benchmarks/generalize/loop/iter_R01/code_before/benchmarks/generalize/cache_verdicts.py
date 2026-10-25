#!/usr/bin/env python
"""Store judge verdicts of one iteration in the judge cache (loop/RUN.md section 5).

  venv/bin/python benchmarks/generalize/cache_verdicts.py NNN verdicts.json [--split holdout]

verdicts.json maps run names (as in iter_NNN/summary.json, e.g. "G01_s1") to verdict objects:

  {"G01_s1": {"verdict": "MEETS", "class": "CORRECT", "score": 1.0, "judge": "iter_001/G01_s1/judge.md"}, ...}

A list of {"name": ..., "verdict": {...}} rows (or {"verdicts": [...]}) is accepted too, and a bare design id
may stand for its run when the iteration holds exactly one run of it. Every verdict needs "verdict"
(MEETS | DNM), "meets" (true | false) or "class" (CORRECT | MINOR | WRONG); extra fields are kept. A verdict given in
the boolean form ("meets" and no "verdict") is stored with the normalised "verdict" string next to it (generalize
delta 003 C0).

Each verdict is stored under (design id, geometry hash of the judged package, sha1 of the design's
requirements.md + design.json + rubric.md as they are now, i.e. the files the judge graded against; a run
whose spec files changed after it ran shows `spec_changed_since_run` in summary.json). A run with no STL
package is skipped and reported (exit 1). summary.json is rebuilt afterwards, so
to_judge / cached and the MEETS / CORRECT counts are current. Held-out verdicts go to
loop/holdout_results/judge_cache.json and only aggregate numbers are printed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_suite as rs  # noqa: E402


def parse_verdicts(data: Any) -> List[Tuple[str, dict]]:
    if isinstance(data, Mapping) and "verdicts" in data and len(data) == 1:
        data = data["verdicts"]
    if isinstance(data, Mapping):
        rows = list(data.items())
    elif isinstance(data, list):
        rows = []
        for r in data:
            if not isinstance(r, Mapping) or "name" not in r or "verdict" not in r:
                raise ValueError(f"a verdict row needs 'name' and 'verdict': {r!r}")
            rows.append((r["name"], r["verdict"]))
    else:
        raise ValueError("verdicts must be an object or a list")
    out = []
    for name, v in rows:
        if not isinstance(v, Mapping) or not ({"verdict", "class", "meets"} & set(v)):
            raise ValueError(f"{name}: a verdict is an object with 'verdict', 'meets' and/or 'class', got {v!r}")
        if "meets" in v and not isinstance(v["meets"], bool):
            raise ValueError(f"{name}: 'meets' must be true or false, got {v['meets']!r}")
        v = dict(v)
        if "verdict" not in v and "meets" in v:   # generalize delta 003 C0: the boolean form, stored normalised
            v["verdict"] = "MEETS" if v["meets"] else "DNM"
        out.append((str(name), v))
    return out


def store_verdicts(paths: rs.Paths, nnn: str, verdicts: Sequence[Tuple[str, dict]], holdout: bool = False) -> dict:
    split_root = "holdout" if holdout else "train"
    summary = rs.build_summary(paths, split_root, nnn)       # current spec hashes
    by_name = {r["name"]: r for r in summary["runs"]}
    by_id: Dict[str, List[dict]] = {}
    for r in summary["runs"]:
        by_id.setdefault(r["id"], []).append(r)
    cache_path = paths.cache_path(split_root)
    cache = rs.load_cache(cache_path)
    stored, skipped = [], []
    for name, v in verdicts:
        row: Optional[dict] = by_name.get(name)
        if row is None and len(by_id.get(name, [])) == 1:
            row = by_id[name][0]
        if row is None:
            skipped.append({"name": name, "reason": "no such run in this iteration"})
            continue
        if not row.get("geometry_sha1"):
            skipped.append({"name": name, "reason": "the run has no STL package"})
            continue
        if not row.get("spec_sha1"):
            skipped.append({"name": name, "reason": "the run records no spec files"})
            continue
        rs.cache_store(cache, row["id"], row["geometry_sha1"], row["spec_sha1"], v,
                       iter=nnn, run=row["name"], package=row.get("package"))
        stored.append(row["name"])
    if stored:
        rs.save_json(cache_path, cache)
    summary = rs.build_summary(paths, split_root, nnn)
    return {"stored": stored, "skipped": skipped, "summary": summary}


def main(argv: Optional[Sequence[str]] = None, paths: Optional[rs.Paths] = None) -> int:
    ap = argparse.ArgumentParser(description="Store judge verdicts in the generalization loop's judge cache.")
    ap.add_argument("iter", help="iteration number NNN")
    ap.add_argument("verdicts", type=Path, help="verdicts JSON file")
    ap.add_argument("--split", choices=("train", "regression", "holdout"), default="train",
                    help="holdout uses loop/holdout_results; train and regression share loop/iter_NNN")
    args = ap.parse_args(argv)
    paths = paths or rs.Paths()
    nnn = rs.iter_label(args.iter)
    holdout = args.split == "holdout"
    res = store_verdicts(paths, nnn, parse_verdicts(json.loads(args.verdicts.read_text())), holdout=holdout)
    s = res["summary"]
    if holdout:
        print(json.dumps({"iter": nnn, "stored": len(res["stored"]), "skipped": len(res["skipped"]),
                          "holdout_score": s.get("holdout_score")}))
    else:
        print(json.dumps({"iter": nnn, "stored": res["stored"], "skipped": res["skipped"], "counts": s["counts"],
                          "regression": s["regression"], "to_judge": s["to_judge"]}, indent=2))
    return 0 if not res["skipped"] else 1


if __name__ == "__main__":
    sys.exit(main())
