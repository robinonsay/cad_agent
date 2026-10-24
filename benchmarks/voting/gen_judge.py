"""Score every generated test with each judge's back-translation P(yes) (the cascade gate's
question), for the "generate broadly, filter with a judge" analysis. Output: gen_judged.json."""
import json, sys
from pathlib import Path
sys.path.insert(0, "/Users/robinonsay/python/llm-bt")
import cad_agent as ca
HERE = Path(__file__).parent
items = json.load(open(HERE / "gen_unique.json"))
out_path = HERE / "gen_judged.json"
out = json.loads(out_path.read_text()) if out_path.exists() else {}
INTRO = "A requirement is usually checked by several small tests, each covering one piece of it.\n\n"
Q = ("Is this test about something the requirement talks about (the same part and the same kind of "
     "property, place or behaviour), with no number or direction that disagrees with the requirement?")
for model in ("ornith-1.5:9b", "qwen3.5:9b", "gemma4:latest"):
    llm = ca.OllamaAgent(model, num_ctx=8192)
    for x in items:
        k = f"{x['id']}|{model}"
        if k in out:
            continue
        out[k] = llm.p_yes(INTRO + f"Requirement: {x['requirement']}\nOne test: {x['test']}\n\n" + Q)
    out_path.write_text(json.dumps(out))
    print(model, "done", flush=True)
