"""Judge configurations and ensembles vs gold labels, with cross-validated thresholds.

Every score is P(yes)-like in [0,1]; the decision threshold is chosen on 4/5 of the items
and applied to the held-out 1/5 (5 folds, repeated with 20 shuffles), so no configuration
gets credit for a threshold tuned on its own test items. Paired bootstrap vs the baseline
(the judge the agent uses today: ornith p_yes, base wording).
"""
import json, random, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
gold = {i["id"]: i for i in json.load(open(HERE / "probe_labeled.json"))}
R = defaultdict(lambda: defaultdict(list)); SECS = defaultdict(list)
for line in open(HERE / "results.jsonl"):
    r = json.loads(line)
    if r["id"] not in gold or "error" in r:
        continue
    if "p" in r:
        v = 1 - r["p"] if r.get("invert") else r["p"]
    elif r.get("ans") in ("yes", "no"):
        v = 1.0 if (r["ans"] == "yes") != bool(r.get("invert")) else 0.0
    else:
        continue
    R[r["config"]][r["id"]].append(v); SECS[r["config"]].append(r.get("secs", 0))

KIND = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "all" else None
IDS = sorted(k for k in gold if KIND in (None, gold[k]["kind"]))
Y = {i: gold[i]["gold"] == "yes" for i in IDS}
THRS = [x / 40 for x in range(1, 40)]

def acc_at(score, ids, t):
    return sum((score[i] >= t) == Y[i] for i in ids) / len(ids)

def cv_preds(score, reps=20):
    """id -> fraction of repetitions predicting yes, with thresholds tuned on the other folds."""
    ids = [i for i in IDS if i in score]
    yes = defaultdict(float)
    for rep in range(reps):
        rnd = random.Random(rep); sh = ids[:]; rnd.shuffle(sh)
        folds = [sh[k::5] for k in range(5)]
        for k in range(5):
            train = [i for j, f in enumerate(folds) if j != k for i in f]
            t = max(THRS, key=lambda t: (acc_at(score, train, t), -abs(t - 0.5)))
            for i in folds[k]:
                yes[i] += (score[i] >= t) / reps
    return yes

def auc(score):
    ids = [i for i in IDS if i in score]
    sp = [score[i] for i in ids if Y[i]]; sn = [score[i] for i in ids if not Y[i]]
    return sum((a > b) + 0.5 * (a == b) for a in sp for b in sn) / max(1, len(sp) * len(sn))

def summary(score):
    pr = cv_preds(score)
    ids = list(pr)
    correct = {i: (pr[i] if Y[i] else 1 - pr[i]) for i in ids}
    neg = [i for i in ids if not Y[i]]; pos = [i for i in ids if Y[i]]
    return {"acc": sum(correct.values()) / len(ids), "fa": sum(pr[i] for i in neg) / len(neg),
            "fr": sum(1 - pr[i] for i in pos) / len(pos), "auc": auc(score), "n": len(ids), "correct": correct}

# ---- building blocks ----
def first(c):            # first sample's score
    return {i: v[0] for i, v in R[c].items()}
def mean_k(c, k):        # soft vote over first k samples
    return {i: sum(v[:k]) / k for i, v in R[c].items() if len(v) >= k}
def hard_k(c, k):        # majority of first k sampled answers
    return {i: (1.0 if sum(x >= 0.5 for x in v[:k]) * 2 > k else 0.0) for i, v in R[c].items() if len(v) >= k}
def mean_of(*scores):
    keys = set.intersection(*[set(s) for s in scores])
    return {i: sum(s[i] for s in scores) / len(scores) for i in keys}
def vote_of(*scores, thr=0.5):
    keys = set.intersection(*[set(s) for s in scores])
    return {i: sum(s[i] >= thr for s in scores) / len(scores) for i in keys}
def have(c, k=1):
    return c in R and sum(len(v) >= k for v in R[c].values()) >= 0.95 * len(IDS)

M = ["ornith15", "qwen3.5", "gemma4"]
FR = ["base", "adversarial", "checklist", "inverse", "evidence"]
configs = {}
for m in M:
    for f in FR + ["strict"]:
        if have(f"{m}|p|{f}"):
            configs[f"{m} p_yes {f}"] = (first(f"{m}|p|{f}"), 1)
    if have(f"{m}|s0|base"):
        configs[f"{m} greedy answer"] = (first(f"{m}|s0|base"), 1)
    for k in (1, 3, 5):
        if have(f"{m}|cot|base", k):
            configs[f"{m} reasoned, vote of {k}"] = (hard_k(f"{m}|cot|base", k) if k > 1 else first(f"{m}|cot|base"), k)
            if k > 1:
                configs[f"{m} reasoned, soft {k}"] = (mean_k(f"{m}|cot|base", k), k)
    if all(have(f"{m}|p|{f}") for f in FR):
        configs[f"{m} p_yes, 5 wordings averaged"] = (mean_of(*[first(f"{m}|p|{f}") for f in FR]), 5)
        configs[f"{m} p_yes, base+inverse"] = (mean_of(first(f"{m}|p|base"), first(f"{m}|p|inverse")), 2)
        configs[f"{m} p_yes, 6 incl strict"] = (mean_of(*[first(f"{m}|p|{f}") for f in FR + ["strict"]]), 6) \
            if have(f"{m}|p|strict") else configs[f"{m} p_yes, 5 wordings averaged"]
for T in ("0.3", "0.7", "1.0", "1.5"):
    c = f"ornith15|s{T}|base"
    for k in (1, 3, 5, 7):
        if have(c, k):
            configs[f"ornith T={T} vote of {k}"] = (hard_k(c, k) if k > 1 else first(c), k)
            if k > 1:
                configs[f"ornith T={T} soft {k}"] = (mean_k(c, k), k)
if all(have(f"ornith15|s{T}|base", 2) for T in ("0.3", "0.7", "1.0", "1.5")) and have("ornith15|s0|base"):
    mixed = [first("ornith15|s0|base")] + [first(f"ornith15|s{T}|base") for T in ("0.3", "0.7", "1.0", "1.5")]
    configs["ornith mixed temps 0/.3/.7/1/1.5 vote of 5"] = (vote_of(*mixed), 5)
avail = [m for m in M if have(f"{m}|p|base")]
if len(avail) >= 2:
    configs[f"models {'+'.join(avail)} p_yes averaged"] = (mean_of(*[first(f"{m}|p|base") for m in avail]), len(avail))
    configs[f"models {'+'.join(avail)} greedy vote"] = (vote_of(*[first(f"{m}|s0|base") for m in avail if have(f"{m}|s0|base")]), len(avail))
    if all(have(f"{m}|p|{f}") for m in avail for f in FR):
        configs[f"models x wordings ({len(avail) * 5}) p_yes averaged"] = (
            mean_of(*[first(f"{m}|p|{f}") for m in avail for f in FR]), len(avail) * 5)
    if all(have(f"{m}|cot|base", 3) for m in avail):
        configs[f"models reasoned, vote of {len(avail)} (1 each)"] = (vote_of(*[first(f"{m}|cot|base") for m in avail]), len(avail))
        configs[f"models reasoned, soft {3 * len(avail)} (3 each)"] = (
            mean_of(*[mean_k(f"{m}|cot|base", 3) for m in avail]), 3 * len(avail))
if "qwen3.5" in avail and "gemma4" in avail:
    configs["qwen+gemma p_yes averaged"] = (mean_of(first("qwen3.5|p|base"), first("gemma4|p|base")), 2)

BASE = "ornith15 p_yes base"
res = {name: summary(s) for name, (s, _) in configs.items() if s}
cost = {name: k for name, (_, k) in configs.items()}

def boot(a, b, n=2000):
    ids = list(set(res[a]["correct"]) & set(res[b]["correct"]))
    d = [res[a]["correct"][i] - res[b]["correct"][i] for i in ids]
    rnd = random.Random(0); means = []
    for _ in range(n):
        s = [d[rnd.randrange(len(d))] for _ in d]; means.append(sum(s) / len(s))
    means.sort()
    return sum(d) / len(d), means[int(0.025 * n)], means[int(0.975 * n)]

print(f"kind={KIND or 'all'} items={len(IDS)} (yes {sum(Y.values())})   accuracy etc. with cross-validated threshold")
print(f"{'configuration':48s} {'calls':>5s} {'acc':>6s} {'FA':>5s} {'FR':>5s} {'AUC':>6s}  vs baseline (95% CI)")
for name in sorted(res, key=lambda n: -res[n]["acc"]):
    r = res[name]
    d = boot(name, BASE) if BASE in res and name != BASE else None
    ds = f"{d[0]:+.3f} [{d[1]:+.3f},{d[2]:+.3f}]" if d else ""
    print(f"{name:48s} {cost[name]:5d} {r['acc']:6.3f} {r['fa']:5.2f} {r['fr']:5.2f} {r['auc']:6.3f}  {ds}")
