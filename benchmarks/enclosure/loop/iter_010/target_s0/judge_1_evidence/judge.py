import numpy as np, trimesh, manifold3d as m3d, json, math
M = m3d.Manifold
D = "/Users/robinonsay/python/llm-bt/benchmarks/enclosure/loop/iter_010/target_s0/20261024-154021"
OUT = "/private/tmp/claude-501/-Users-robinonsay-python-llm-bt/7d706733-5c1d-44fb-a74b-bc29203e1df6/scratchpad/j10"

def load(p):
    tm = trimesh.load(p, force="mesh")
    man = M(m3d.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                     tri_verts=np.asarray(tm.faces, np.uint32)))
    return tm, man

tb, B = load(D + "/base.stl")
tl, L = load(D + "/lid.stl")
ALL = B + L
R = {}
def rec(k, v):
    R[k] = v; print(k, "=>", v)

for n, (t, m) in {"base": (tb, B), "lid": (tl, L)}.items():
    bb = m.bounding_box()
    rec(f"{n}.status", str(m.status()))
    rec(f"{n}.shells", len(m.decompose()))
    rec(f"{n}.bbox", [round(x, 3) for x in bb])
    rec(f"{n}.vol", round(m.volume(), 2))
    rec(f"{n}.watertight", bool(t.is_watertight))
rec("overlap_base_lid", (B ^ L).volume())
bb = ALL.bounding_box()
rec("assembly_size", [round(bb[3]-bb[0], 3), round(bb[4]-bb[1], 3), round(bb[5]-bb[2], 3)])

def box(x0, y0, z0, x1, y1, z1):
    return M.cube([x1-x0, y1-y0, z1-z0]).translate([x0, y0, z0])
def cylz(x, y, z0, z1, d, n=96):
    return M.cylinder(z1-z0, d/2, d/2, n).translate([x, y, z0])
def cylx(y, z, x0, x1, d, n=96):
    return M.cylinder(x1-x0, d/2, d/2, n).rotate([0, 90, 0]).translate([x0, y, z])

def clear_of(bodies, vol, c):
    inter = bodies ^ vol
    pen = inter.volume()
    if pen > 0.01:
        return {"d": None, "pen": round(pen, 3), "where": [round(x, 3) for x in inter.bounding_box()]}
    return {"d": round(bodies.min_gap(vol, c + 5.0), 4), "pen": 0.0}

def inside(vol, solids, c, big=2000):
    hull = M.hull(solids)
    out = (vol - hull).volume()
    if out > 0.01:
        return {"d": None, "outside": out, "where": (vol - hull).bounding_box()}
    shell = M.cube([big]*3, True) - hull
    return {"d": round(min(vol.min_gap(solids, c+5), vol.min_gap(shell, c+5)), 4)}

# ---------- reference models (requirements.md 2.2 numbers, declared layout poses) ----------
HOLES = [(2.0, 2.0), (68.0, 2.0), (2.0, 48.0), (68.0, 48.0)]
perf = box(0, 0, -1.6, 70, 50, 0)
for hx, hy in HOLES:
    perf = perf - cylz(hx, hy, -2, 1, 2.0)
# Pico at declared pose: x0=0, y0=13.59, z0=2.5 (PCB bottom)
px, py, pz = 0.0, 13.59, 2.5
pico_pcb = box(px, py, pz, px+51, py+21, pz+1)
usb = box(px-1.3, py+6.5, pz+1, px-1.3+5.5, py+14.5, pz+1+2.8)
pico_ko = box(px, py, pz+1, px+51, py+21, pz+2.5)
VPICO = pico_pcb + usb
hdr1 = box(1.37-1.27, 15.2-1.25, 0, 1.37-1.27+50.8, 15.2+1.25, 2.5)
hdr2 = box(1.37-1.27, 32.98-1.25, 0, 1.37-1.27+50.8, 32.98+1.25, 2.5)
jy = [14.600010582941664, 29.84001056943333]
jacks = [box(58, y, 0, 70, y+6, 5) for y in jy]
USB_MOUTH = (px-1.3, py+10.5, pz+1+1.4)
rec("USB_MOUTH", USB_MOUTH)
JACK_MOUTH = [(70.0, y+3, 2.5) for y in jy]
rec("JACK_MOUTH", JACK_MOUTH)
rec("jack_axis_spacing", round(JACK_MOUTH[1][1]-JACK_MOUTH[0][1], 3))

# grid residual (requirements A7 grid)
gx = [5.79 + 2.54*i for i in range(24)]
gy = [3.41 + 2.54*j for j in range(18)]
pins = [(1.37 + 2.54*k, y) for k in range(20) for y in (15.2, 32.98)]
res = []
for x, y in pins:
    res.append(min(math.hypot(x-a, y-b) for a in gx for b in gy))
rec("grid_residual_max", round(max(res), 3))
rec("grid_residual_min", round(min(res), 3))

# RBA pairwise
parts = {"perf": perf, "pico": VPICO, "hdr1": hdr1, "hdr2": hdr2, "j1": jacks[0], "j2": jacks[1]}
pw = {}
ks = list(parts)
for i in range(len(ks)):
    for j in range(i+1, len(ks)):
        v = (parts[ks[i]] ^ parts[ks[j]]).volume()
        if v > 0.0: pw[ks[i]+"-"+ks[j]] = round(v, 4)
rec("RBA_pairwise_overlaps", pw)
nonperf = VPICO + hdr1 + hdr2 + jacks[0] + jacks[1]
bbn = nonperf.bounding_box()
rec("plan_bounds_nonperf", [round(x, 3) for x in bbn])

# envelopes
KO_TOP = box(0, 0, 0, 70, 50, 12.0)
SEAT = [cylz(hx, hy, -50, -1.6, 7.0) for hx, hy in HOLES]
KO_BOT = box(0, 0, -5.6, 70, 50, -1.6)
for s in SEAT: KO_BOT = KO_BOT - s
HOLE_KO = [cylz(hx, hy, 0, 12.0, 7.0) for hx, hy in HOLES]
HOLE_KO_ring = [cylz(hx, hy, 0, 12.0, 7.0) - cylz(hx, hy, -1, 13, 2.9) for hx, hy in HOLES]
ux, uy, uz = USB_MOUTH
V_USB = box(ux-1.5, uy-3.45, uz-0.925, ux+5.0, uy+3.45, uz+0.925) + box(ux-1.5-40, uy-5, uz-3.5, ux-1.5, uy+5, uz+3.5)
V_JACK = [cylx(y, z, 70.0, 71.0, 3.5) + cylx(y, z, 71.0, 111.0, 8.0) for (_, y, z) in JACK_MOUTH]
rim = B.bounding_box()[5]
RBA = perf + nonperf
# plan silhouette of RBA: use a projection
def plan_sweep(man, z0, z1):
    cs = man.project()
    return M.extrude(cs, z1 - z0).translate([0, 0, z0])
RBA_noperfholes = box(0, 0, -1.6, 70, 50, 0) + nonperf
VINST = plan_sweep(RBA_noperfholes, -1.6, rim + 5.0)
for s in SEAT: VINST = VINST - s
DRIVER = [cylz(hx, hy, 0, rim + 50, 6.0) for hx, hy in HOLES]

rec("L3.1.4.2 parts vs HOLE_KO", [clear_of(nonperf, h, 0.0) for h in HOLE_KO])
# board clearance
perf_minus = box(0, 0, -1.6, 70, 50, 0)
for hx, hy in HOLES: perf_minus = perf_minus - cylz(hx, hy, -5, 5, 8.0)
rec("L3.2.1.1 board clearance", clear_of(ALL, perf_minus, 0.5))
rec("L3.2.2.1 V-PICO inside", inside(VPICO, [B, L] and ALL, 0.2))
rec("L3.4.3.1 hdr+jacks inside", inside(hdr1 + hdr2 + jacks[0] + jacks[1], ALL, 0.3))
rec("L3.4.1.1 KO_TOP", clear_of(ALL, KO_TOP, 0.0))
rec("L3.4.2.1 KO_BOT", clear_of(ALL, KO_BOT, 0.0))
rec("L3.3.5.1 HOLE_KO ring", [clear_of(ALL, h, 0.0) for h in HOLE_KO_ring])
rec("L3.5.1.1 USB plug", clear_of(ALL, V_USB, 0.3))
rec("L3.6.1.1 jack plugs", [clear_of(ALL, v, 0.3) for v in V_JACK])
rec("jack envelopes intersect", (V_JACK[0] ^ V_JACK[1]).volume())
rec("L3.11.1.1 install", clear_of(B, VINST, 0.2))
rec("L3.11.2.1 drivers", [clear_of(B, d, 0.0) for d in DRIVER])

# save defect solids for hole KO
for i, h in enumerate(HOLE_KO_ring):
    inter = ALL ^ h
    if inter.volume() > 0.01:
        mm = inter.to_mesh()
        trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts)).export(f"{OUT}/defect_L3.3.5.1_hole{i+1}.stl")

json.dump(R, open(OUT + "/r1.json", "w"), indent=1, default=str)
