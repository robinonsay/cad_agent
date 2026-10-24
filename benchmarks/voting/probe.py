"""Ask every probe question under many judge configurations; append raw results to results.jsonl.

Resumable: a (item, config, sample) already in results.jsonl is skipped.
Usage: python3 probe.py PHASE [MODEL]   PHASE in {fast, temp, cot}
"""
import json, re, sys, time
from pathlib import Path
sys.path.insert(0, "/Users/robinonsay/python/llm-bt")
import cad_agent as ca

HERE = Path(__file__).parent
OUT = HERE / "results.jsonl"
ITEMS = json.load(open(HERE / "probe_unlabeled.json"))

BT_INTRO = "A requirement is usually checked by several small tests, each covering one piece of it.\n\n"

def framing(it, f):
    a, b = it["a"], it["b"]
    if it["kind"] == "bt":
        ctx = f"Requirement: {a}\nOne test: {b}\n\n"
        q = {
            "base": BT_INTRO + ctx + "Is this test about something the requirement talks about (the same part and the same kind of property, place or behaviour), with no number or direction that disagrees with the requirement?",
            "adversarial": BT_INTRO + ctx + "Look hard for a way this test could be wrong: a different part, a different kind of property, a stand-in object of the wrong size, or a number or direction that disagrees with the requirement. If you find none, the test is correct. Is the test correct?",
            "checklist": BT_INTRO + ctx + "Check three things: (1) the test is about a part the requirement names; (2) it checks the same kind of thing (size, place, count, fit, stability); (3) every number and direction in the test agrees with the requirement. Are all three true?",
            "inverse": BT_INTRO + ctx + "Is this test about a different part or a different kind of property than the requirement, or does any number or direction in it disagree with the requirement?",
            "evidence": ctx + "If a design passed this test, would that be real evidence that it meets (part of) the requirement?",
        }[f]
    else:
        ctx = f"A person asked for: {a}\n\nIn the current design: {b}\n\n"
        q = {
            "base": ctx + "Is this part of the design what the person asked for?",
            "adversarial": ctx + "Look hard for anything about this part that disagrees with the request: a size, an orientation, a position or a shape. If you find nothing, it matches. Does this part match the request?",
            "checklist": ctx + "Check three things: (1) its sizes agree with every size the request gives for it; (2) its orientation agrees; (3) its position agrees. Are all three true?",
            "inverse": ctx + "Does any size, orientation, position or shape of this part disagree with what the person asked for?",
            "evidence": ctx + "Would the person look at this part and say it is what they asked for?",
        }[f]
    return q

SYSTEM_STRICT = "You are a strict, careful quality engineer. You answer only when sure, and say no when anything disagrees."
YESNO = ca.obj_schema({"answer": {"type": "string", "enum": ["yes", "no"]}})
COT_SUFFIX = ("\n\nThink it through in two to four short sentences, comparing each number, direction and part. "
              "Then finish with a last line that is exactly 'ANSWER: yes' or 'ANSWER: no'.")

done = set()
if OUT.exists():
    for line in OUT.open():
        r = json.loads(line); done.add((r["id"], r["config"], r["sample"]))

def record(it, config, sample, **kw):
    with OUT.open("a") as fh:
        fh.write(json.dumps({"id": it["id"], "config": config, "sample": sample, **kw}) + "\n")

def run(phase, model):
    llm = ca.OllamaAgent(model, ca.HOST, timeout=300)
    short = model.split(":")[0].replace("-1.5", "15")
    jobs = []
    for it in ITEMS:
        if phase == "fast":
            for f in ("base", "adversarial", "checklist", "inverse", "evidence"):
                jobs.append((it, f"{short}|p|{f}", 0, "p", f, ""))
            jobs.append((it, f"{short}|p|strict", 0, "p", "base", SYSTEM_STRICT))
            jobs.append((it, f"{short}|s0|base", 0, "s", "base", 0.0))
        elif phase == "temp":
            for T, n in ((0.3, 5), (0.7, 7), (1.0, 7), (1.5, 7)):
                for k in range(n):
                    jobs.append((it, f"{short}|s{T}|base", k, "s", "base", T))
        elif phase == "cot":
            n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            if not model.startswith("ornith"):
                n = min(n, 3)   # time budget: 3 reasoned samples for the other judges
            for k in range(n):
                jobs.append((it, f"{short}|cot|base", k, "cot", "base", 0.0 if k == 0 else 0.8))
    todo = [j for j in jobs if (j[0]["id"], j[1], j[2]) not in done]
    print(f"{phase} {model}: {len(todo)} of {len(jobs)} to do", flush=True)
    t0 = time.time()
    for n, (it, config, k, how, f, extra) in enumerate(todo):
        q = framing(it, f)
        s = time.time()
        try:
            if how == "p":
                p = llm.p_yes(q, system=extra)
                record(it, config, k, p=p, invert=(f == "inverse"), secs=round(time.time() - s, 2))
            elif how == "s":
                ans = llm.ask_json(q, YESNO, temperature=extra, seed=k, num_predict=24).get("answer")
                record(it, config, k, ans=ans, invert=(f == "inverse"), secs=round(time.time() - s, 2))
            else:
                text = llm.chat(q + COT_SUFFIX, temperature=extra, seed=k, num_predict=300)
                m = re.findall(r"ANSWER:\s*\**\s*(yes|no)", text, re.I)
                record(it, config, k, ans=m[-1].lower() if m else None, text=text[-600:],
                       secs=round(time.time() - s, 2))
        except Exception as e:
            record(it, config, k, error=str(e)[:200])
        if n % 100 == 0:
            print(f"  {n}/{len(todo)} {time.time() - t0:.0f}s", flush=True)
    print(f"done {phase} {model} in {time.time() - t0:.0f}s", flush=True)

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ca.MODEL)
