"""Generation voting: which tests survive a vote across samples, and are they right?

Per L1, a strategy keeps a set of tests (by signature). Metrics over L1s:
precision = kept tests labelled correct / kept tests; covered = at least one correct test
kept; clean = no wrong test kept (what matters for freezing); empty = nothing kept.
"""
import json
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).parent
items = json.load(open(HERE / "gen_unique.json"))
gold = json.load(open(HERE / "gen_gold.json"))
key = {(x["req"], x["l1"], x["sig"]): gold[x["id"]] for x in items}
S = defaultdict(lambda: defaultdict(list))   # (req,l1) -> model -> [set of sigs per sample]
for line in open(HERE / "gen_results.jsonl"):
    r = json.loads(line)
    if isinstance(r["checks"], dict):
        continue
    S[(r["req"], r["l1"])][r["model"]].append({c["sig"] for c in r["checks"] if c["valid"]})
L1S = sorted(S)
O, Q = "ornith-1.5:9b", "qwen3.5:9b"

def single(l, k=0, m=O): return S[l][m][k] if len(S[l][m]) > k else set()
def vote(l, n, need, m=O):
    cnt = defaultdict(int)
    for s in S[l][m][:n]:
        for g in s: cnt[g] += 1
    return {g for g, c in cnt.items() if c >= need}
def cross(l, no=7, nq=3):
    a = set().union(*S[l][O][:no]) if S[l][O] else set()
    b = set().union(*S[l][Q][:nq]) if S[l][Q] else set()
    return a & b
def union(l, n, m=O): return set().union(*S[l][m][:n])

def score(name, f):
    prec_n = prec_d = cov = clean = empty = 0; sizes = []
    for l in L1S:
        kept = f(l); sizes.append(len(kept))
        labs = [key.get((l[0], l[1], g)) for g in kept]
        labs = [x for x in labs if x is not None]
        prec_n += sum(x == "yes" for x in labs); prec_d += len(labs)
        cov += any(x == "yes" for x in labs); clean += all(x == "yes" for x in labs) and bool(labs)
        empty += not kept
    n = len(L1S)
    print(f"{name:44s} precision {prec_n / max(1, prec_d):.2f}  L1s covered {cov / n:.2f}  "
          f"all-correct {clean / n:.2f}  empty {empty / n:.2f}  mean kept {sum(sizes) / n:.1f}")

if __name__ == "__main__":
    print(f"{len(L1S)} L1s")
    score("ornith, 1 sample (today)", lambda l: single(l, 0))
    for k in range(1, 3):
        score(f"ornith, sample {k} alone", lambda l, k=k: single(l, k))
    score("qwen, 1 sample", lambda l: single(l, 0, Q))
    for n, need in ((3, 2), (5, 3), (7, 4), (7, 2), (5, 2)):
        score(f"ornith vote: in >= {need} of {n} samples", lambda l, n=n, need=need: vote(l, n, need))
    score("qwen vote: in >= 2 of 3", lambda l: vote(l, 3, 2, Q))
    score("cross-model: proposed by ornith AND qwen", cross)
    score("cross-model: ornith 1st AND qwen 1st", lambda l: single(l, 0) & single(l, 0, Q))
    score("union of 7 ornith samples (no vote)", lambda l: union(l, 7))
