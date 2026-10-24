import json, glob
from collections import Counter, defaultdict
from pathlib import Path
H = Path(__file__).parent
k = json.load(open(H / "blind_key.json"))
g = {}
for f in sorted(glob.glob(str(H / "grades_seed*_g*.json"))):
    g.update(json.load(open(f)))
rows = defaultdict(dict)
for a, v in g.items():
    m = k[a]; rows[(m["id"], m["seed"])][m["condition"]] = (v["grade"], m["status"], v["reason"])
seeds = sorted({s for _, s in rows})
print("seeds graded:", seeds)
T = defaultdict(Counter)
wins = Counter()
for (i, s), cs in sorted(rows.items()):
    for cond, (gr, st, _) in cs.items():
        good = gr in ("CORRECT", "MINOR")
        T[cond]["runs"] += 1; T[cond]["good"] += good; T[cond]["correct"] += gr == "CORRECT"
        T[cond]["verified"] += st == "verified"
        T[cond]["false_pass"] += st == "verified" and not good
        T[cond]["false_fail"] += st != "verified" and good
        T[cond]["bad"] += not good
    if len(cs) == 2:
        a = cs["C_cascade"][0] in ("CORRECT", "MINOR"); b = cs["P_panel"][0] in ("CORRECT", "MINOR")
        wins["C only good" if a and not b else "P only good" if b and not a else "tie"] += 1
for cond, t in T.items():
    print(f"{cond}: good {t['good']}/{t['runs']} (correct {t['correct']}), verified {t['verified']}, "
          f"false pass {t['false_pass']}/{t['verified']}, false fail {t['false_fail']}/{t['good']}")
print("paired:", dict(wins))
by_req = defaultdict(lambda: defaultdict(list))
for (i, s), cs in rows.items():
    for cond, (gr, st, _) in cs.items():
        by_req[i][cond].append(gr[0] + ("v" if st == "verified" else "u"))
for i in sorted(by_req):
    print(i, " C:", " ".join(by_req[i]["C_cascade"]), "  P:", " ".join(by_req[i]["P_panel"]))
