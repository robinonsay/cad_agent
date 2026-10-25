"""Build gallery/index.html: every pilot-2 design's renders, C vs P side by side, with its blind grade.

    python3 benchmarks/voting/pilot2/make_gallery.py [BLIND_DIR]

BLIND_DIR is the folder of blind_prep.py output (R<id>/{iso,front,...}.png, parts.txt).
Images are copied into gallery/img so the page works without the scratchpad.
"""
import glob
import html
import json
import shutil
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
REPO = H.parent.parent.parent
VIEWS = ("iso", "front", "back", "left", "right", "top")
CONDS = (("C_cascade", "C: cascade"), ("P_panel", "P: cascade + panel"))

blind = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/private/tmp/claude-501/-Users-robinonsay-python-llm-bt/7d706733-5c1d-44fb-a74b-bc29203e1df6/scratchpad/pilot2/blind")
key = json.loads((H / "blind_key.json").read_text())
grades = {}
for f in sorted(glob.glob(str(H / "grades_seed*_g*.json"))):
    grades.update(json.loads(Path(f).read_text()))
reqs = {r["id"]: r for r in json.loads((REPO / "benchmarks" / "dev.json").read_text())["requests"]}

out = H / "gallery"
img = out / "img"
img.mkdir(parents=True, exist_ok=True)
runs = {}  # (id, seed, cond) -> info
for rid, m in key.items():
    stem = f"{m['id']}_s{m['seed']}_{m['condition'][0]}"
    for v in VIEWS:
        src = blind / rid / f"{v}.png"
        if src.exists():
            shutil.copyfile(src, img / f"{stem}_{v}.png")
    parts = (blind / rid / "parts.txt").read_text() if (blind / rid / "parts.txt").exists() else ""
    g = grades.get(rid, {"grade": "?", "reason": ""})
    runs[(m["id"], m["seed"], m["condition"])] = dict(stem=stem, status=m["status"], parts=parts, **g)

e = html.escape


def card(r, label):
    if r is None:
        return f'<div class="card missing">{label}: no run</div>'
    good = r["grade"] in ("CORRECT", "MINOR")
    flag = ""
    if r["status"] == "verified" and not good:
        flag = '<span class="flag fp">FALSE PASS</span>'
    elif r["status"] != "verified" and good:
        flag = '<span class="flag ff">false fail</span>'
    thumbs = "".join(f'<img loading="lazy" src="img/{r["stem"]}_{v}.png" title="{v}" data-view="{v}">'
                     for v in VIEWS)
    return f"""<div class="card g-{r['grade']}" data-grade="{r['grade']}" data-status="{r['status']}" data-fp="{int(bool(flag) and 'FALSE' in flag)}">
  <div class="head"><b>{label}</b> <span class="grade">{r['grade']}</span> <span class="status">{r['status']}</span> {flag}</div>
  <img class="main" loading="lazy" src="img/{r['stem']}_iso.png" alt="iso view">
  <div class="thumbs">{thumbs}</div>
  <div class="reason">{e(r['reason'])}</div>
  <details><summary>parts as built</summary><pre>{e(r['parts'])}</pre></details>
</div>"""


sections, nav = [], []
for rid in sorted({k[0] for k in runs}):
    q = reqs.get(rid, {})
    seeds = sorted({k[1] for k in runs if k[0] == rid})
    l1 = "".join(f"<li><b>{e(x['id'])}</b> {e(x['text'])}</li>" for x in q.get("l1", []))
    rows = "".join(
        f'<div class="row"><div class="seed">seed {s}</div>'
        + "".join(card(runs.get((rid, s, c)), lab) for c, lab in CONDS) + "</div>" for s in seeds)
    score = {c: sum(runs[(rid, s, c)]["grade"] in ("CORRECT", "MINOR") for s in seeds if (rid, s, c) in runs)
             for c, _ in CONDS}
    nav.append(f'<a href="#{rid}">{rid} <small>{e(q.get("title", ""))}</small> '
               f'<span class="sc">C {score["C_cascade"]}/{len(seeds)} · P {score["P_panel"]}/{len(seeds)}</span></a>')
    sections.append(f"""<section id="{rid}"><h2>{rid} — {e(q.get('title', ''))}</h2>
<p class="req">{e(q.get('request', ''))}</p><details><summary>L1 requirements</summary><ul>{l1}</ul></details>{rows}</section>""")

page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pilot 2 Renders</title><style>
:root{{--bg:#f6f6f4;--fg:#1d1d1b;--card:#fff;--line:#ddd;--muted:#666;--ok:#2e7d32;--minor:#9a7b00;--bad:#c62828}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161616;--fg:#eee;--card:#222;--line:#3a3a3a;--muted:#aaa}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,sans-serif;display:flex}}
nav{{position:sticky;top:0;height:100vh;overflow:auto;width:250px;flex:none;border-right:1px solid var(--line);padding:12px}}
nav a{{display:block;color:inherit;text-decoration:none;padding:4px 0}} nav .sc{{display:block;color:var(--muted);font-size:12px}}
main{{flex:1;padding:16px;min-width:0}} .filters{{margin-bottom:12px}} .filters label{{margin-right:12px}}
.req{{font-size:15px}} .row{{display:grid;grid-template-columns:60px 1fr 1fr;gap:12px;margin:12px 0;align-items:start}}
.seed{{color:var(--muted);padding-top:8px}}
.card{{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--line);border-radius:6px;padding:8px}}
.g-CORRECT{{border-left-color:var(--ok)}} .g-MINOR{{border-left-color:var(--minor)}} .g-WRONG{{border-left-color:var(--bad)}}
.g-CORRECT .grade{{color:var(--ok)}} .g-MINOR .grade{{color:var(--minor)}} .g-WRONG .grade{{color:var(--bad)}}
.grade{{font-weight:700}} .status{{color:var(--muted)}} .flag{{font-size:11px;padding:1px 5px;border-radius:3px;color:#fff}}
.fp{{background:var(--bad)}} .ff{{background:#777}}
.main{{width:100%;max-height:420px;object-fit:contain;background:#fff;border-radius:4px;cursor:zoom-in;margin-top:6px}}
.thumbs{{display:flex;gap:4px;margin-top:4px}} .thumbs img{{width:16%;cursor:pointer;background:#fff;border-radius:3px;border:2px solid transparent}}
.thumbs img.on{{border-color:#4a7bd0}} .reason{{color:var(--muted);margin-top:4px}}
pre{{white-space:pre-wrap;font-size:12px}} .hide{{display:none}}
#zoom{{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:9}}
#zoom img{{max-width:95vw;max-height:95vh;background:#fff}}
@media (max-width:800px){{nav{{display:none}} .row{{grid-template-columns:1fr}}}}
</style></head><body><nav><b>Pilot 2 — 16 requests × 5 seeds</b>{''.join(nav)}</nav><main>
<div class="filters">Show: <label><input type="checkbox" id="onlyBad"> only WRONG</label>
<label><input type="checkbox" id="onlyFlag"> only false pass / false fail</label>
<span style="color:var(--muted)">Click a thumbnail to switch view; click the big image to zoom.</span></div>
{''.join(sections)}</main><div id="zoom"><img alt=""></div>
<script>
document.querySelectorAll('.thumbs img').forEach(t=>t.onclick=()=>{{const c=t.closest('.card');c.querySelector('.main').src=t.src;
 c.querySelectorAll('.thumbs img').forEach(x=>x.classList.toggle('on',x===t));}});
const z=document.getElementById('zoom');document.querySelectorAll('.main').forEach(m=>m.onclick=()=>{{z.querySelector('img').src=m.src;z.style.display='flex';}});
z.onclick=()=>z.style.display='none';
function filt(){{const b=onlyBad.checked,f=onlyFlag.checked;document.querySelectorAll('.row').forEach(r=>{{
 const cs=[...r.querySelectorAll('.card')];const show=cs.some(c=>(!b||c.dataset.grade==='WRONG')&&(!f||c.querySelector('.flag')));
 r.classList.toggle('hide',!show);}});}}
onlyBad.onchange=filt;onlyFlag.onchange=filt;
</script></body></html>"""
(out / "index.html").write_text(page)
print(f"{len(runs)} runs, {len(list(img.glob('*.png')))} images -> {out / 'index.html'}")
