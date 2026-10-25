"""How each cascade loop stopped in a pilot: converged, stagnated, saturated (hit its cap), ...

    python3 benchmarks/voting/stop_reasons.py PILOT_DIR
"""
import glob, json, sys
from collections import Counter, defaultdict
from pathlib import Path

root = Path(sys.argv[1])
loops = defaultdict(Counter)        # (condition, loop kind) -> status counts
iters = defaultdict(list)
outer = defaultdict(Counter)
for line in (root / "results.jsonl").read_text().splitlines():
    r = json.loads(line)
    found = sorted(glob.glob(str(Path(r["workdir"]) / "*" / "design.json")))
    if not found:
        loops[(r["condition"], "run")][r["status"]] += 1
        continue
    c = json.loads(Path(found[-1]).read_text()).get("cascade") or {}
    outer[r["condition"]][c.get("outer_iterations")] += 1
    for name, v in (c.get("loops") or {}).items():
        kind = "translate" if name.startswith("translate") else name
        loops[(r["condition"], kind)][v["status"]] += 1
        iters[(r["condition"], kind)].append(v["iterations"])
for k in sorted(loops):
    it = iters.get(k) or [0]
    print(f"{k[0]:12} {k[1]:10} {dict(loops[k])}  iterations max {max(it)}, mean {sum(it)/len(it):.1f}")
for cond, c in sorted(outer.items()):
    print(f"{cond:12} outer iterations {dict(sorted(c.items(), key=str))}")
