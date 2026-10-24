"""Blind grading kit: one folder per run under blind/<anon id>/ with the request, the six renders
and a measured part table from design.json (sizes, positions, counts). The key (anon id -> run)
goes to blind_key.json, which graders never see. Re-running adds only new runs."""
import json, random, shutil, sys
from pathlib import Path
sys.path.insert(0, "/Users/robinonsay/python/llm-bt")
HERE = Path(__file__).parent
DEV = {r["id"]: r for r in json.load(open("/Users/robinonsay/python/llm-bt/benchmarks/dev.json"))["requests"]}
key_path = HERE / "blind_key.json"
key = json.loads(key_path.read_text()) if key_path.exists() else {}
known = {v["workdir"] for v in key.values()}
rnd = random.Random(len(key) + 17)
for line in open(HERE / "results.jsonl"):
    r = json.loads(line)
    wd = sorted(Path(r["workdir"]).glob("*/design.json"))
    if r["workdir"] in known or not wd:
        continue
    run = wd[-1].parent
    while True:
        anon = f"R{rnd.randrange(1000, 9999)}"
        if anon not in key:
            break
    out = HERE / "blind" / anon
    out.mkdir(parents=True)
    for png in sorted((run / "views").glob("*.png")):
        shutil.copy(png, out / png.name.replace("model_", ""))
    d = json.loads(wd[-1].read_text())
    lines = [f"Request: {DEV[r['id']]['request']}", "", "Parts as built (mm; x = left-right, y = front-back, z = up):"]
    for c in d["components"]:
        lines.append(f"- {c['name']} x{c.get('count', 1)}: {c.get('shape')} {json.dumps(c.get('params'))}")
        for p in c.get("positions") or []:
            lines.append(f"    copy at min corner {[round(v, 1) for v in p]}, size {[round(v, 1) for v in c.get('size') or []]}")
    (out / "parts.txt").write_text("\n".join(lines) + "\n")
    key[anon] = {"condition": r["condition"], "id": r["id"], "seed": r["seed"], "status": r["status"],
                 "workdir": r["workdir"]}
key_path.write_text(json.dumps(key, indent=1))
print(len(key), "runs in the blind set")
