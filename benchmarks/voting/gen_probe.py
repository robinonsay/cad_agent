"""Sample the L1 -> checks translation N times per L1 (different seeds/temperatures, two models)
and record every proposed check, for a self-consistency (generation vote) analysis.

Designs: the final design.json of each cascade pilot run (seed 0), standing in for the
provisional design the translation sees. Output: gen_results.jsonl (resumable).
"""
import json, sys
from pathlib import Path
sys.path.insert(0, "/Users/robinonsay/python/llm-bt")
import cad_agent as ca, cad_checks as cc, cascade as cs

HERE = Path(__file__).parent
PILOT = HERE.parent / "pilot" / "cascade_L1"
OUT = HERE / "gen_results.jsonl"
DEV = {r["id"]: r for r in json.load(open("/Users/robinonsay/python/llm-bt/benchmarks/dev.json"))["requests"]}
N = {"ornith-1.5:9b": 7, "qwen3.5:9b": 3}

done = set()
if OUT.exists():
    for line in OUT.open():
        r = json.loads(line); done.add((r["req"], r["l1"], r["model"], r["sample"]))

def designs():
    for rd in sorted(PILOT.iterdir()):
        f = next(iter(sorted((rd / "seed0").glob("*/design.json"))), None)
        if f and rd.name in DEV:
            yield rd.name, f

for model, n in N.items():
    llm = ca.OllamaAgent(model, ca.HOST, timeout=300)
    for rid, f in designs():
        d = cc.design_from_json(f, workdir=HERE / "gen_work")
        d.request = DEV[rid]["request"]; d.base_request = DEV[rid]["request"]
        d.l1 = DEV[rid]["l1"]
        d.cascade = cs.CascadeState(l1=list(d.l1))
        for req in d.l1:
            for k in range(n):
                if (rid, req["id"], model, k) in done:
                    continue
                try:
                    checks = cs.ask_checks(llm, d, req, cs.offered_types(req.get("method")), [], k)
                    rec = [{"type": c.type, "params": c.params, "text": c.text or cc.render_check(c),
                            "sig": cs.check_signature(c), "valid": not cc.validate_check(c)} for c in checks]
                except Exception as e:
                    rec = {"error": str(e)[:200]}
                with OUT.open("a") as fh:
                    fh.write(json.dumps({"req": rid, "l1": req["id"], "model": model, "sample": k,
                                         "checks": rec}, default=str) + "\n")
        print(model, rid, "done", flush=True)
print("GENDONE")
