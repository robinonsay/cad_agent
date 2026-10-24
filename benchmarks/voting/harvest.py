"""Harvest real yes/no judgment questions from pilot LLM logs into a probe set.

Two kinds: bt (does this test check the requirement?) and verify (is this part what the
person asked for?). Adds perturbed copies (a number or direction stated in the
requirement changed) as extra hard negatives. Labels come later (labelers + adjudication).
"""
import json, random, re
from pathlib import Path

HERE = Path(__file__).parent
PILOT = HERE.parent / "pilot"
random.seed(0)

def parse(path):
    t = path.read_text()
    prompt = t.split("=== PROMPT ===\n", 1)[1].split("\n\n=== RESPONSE ===", 1)[0]
    resp = t.split("=== RESPONSE ===\n", 1)[1].strip()
    return prompt, resp

items, seen = [], set()
for f in sorted(PILOT.rglob("llm/*.txt")):
    name = f.name
    if "_bt_" in name:
        prompt, resp = parse(f)
        m = re.search(r"Requirement: (.*)\nOne test: (.*)\n", prompt)
        if not m: continue
        a, b = m.group(1), m.group(2)
        kind = "bt"
    elif "_verify_" in name:
        prompt, resp = parse(f)
        m = re.search(r"A person asked for: (.*)\n\nIn the current design: (.*)\n\n", prompt, re.S)
        if not m: continue
        a, b = m.group(1), m.group(2)
        kind = "verify"
    else:
        continue
    key = (kind, a, b)
    if key in seen: continue
    seen.add(key)
    items.append({"kind": kind, "a": a, "b": b, "source": str(f.relative_to(PILOT)), "orig_resp": resp[:200]})

NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?= ?(mm|degrees|°|g\b))")
DIRS = [("front", "back"), ("left", "right"), ("top", "bottom")]

def perturb(it):
    a, b = it["a"], it["b"]
    stated = {m.group(1) for m in NUM.finditer(a)}
    nums = [m for m in NUM.finditer(b) if m.group(1) in stated]
    if nums and random.random() < 0.6:
        m = random.choice(nums)
        v = float(m.group(1)); nv = v * random.choice([0.5, 0.7, 1.5, 2]) if v > 2 else v + 5
        nv = str(int(round(nv))) if nv == int(round(nv)) or nv > 5 else f"{nv:.1f}"
        return b[:m.start(1)] + nv + b[m.end(1):], f"number {m.group(1)}->{nv}"
    for x, y in DIRS:
        for p, q in ((x, y), (y, x)):
            if re.search(rf"\b{p}\b", a) and re.search(rf"\b{p}\b", b):
                return re.sub(rf"\b{p}\b", q, b, count=1), f"direction {p}->{q}"
    return None

extra = []
for it in items:
    if random.random() < 0.45:
        r = perturb(it)
        if r and (it["kind"], it["a"], r[0]) not in seen:
            seen.add((it["kind"], it["a"], r[0]))
            extra.append({**it, "b": r[0], "perturbed": r[1], "orig_resp": ""})
items += extra
for i, it in enumerate(items):
    it["id"] = f"{it['kind']}{i:03d}"
(HERE / "probe_unlabeled.json").write_text(json.dumps(items, indent=1))
from collections import Counter
print(len(items), Counter((i["kind"], "perturbed" in i) for i in items))
