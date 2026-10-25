exec(open('judge.py').read().split('# ---------- reference models')[0])
def loops(man, z):
    cs = man.slice(z)
    return [np.asarray(p) for p in cs.to_polygons()]
def circ(p):
    c = p.mean(0); r = np.linalg.norm(p-c, axis=1)
    return c, r.min(), r.max()
def signed_area(p):
    x,y=p[:,0],p[:,1]; return 0.5*np.sum(x*np.roll(y,-1)-np.roll(x,-1)*y)
for z in (-4.0, -3.0, -1.7, 5.0, 11.0, 13.0):
    print("== base slice z", z)
    for p in loops(B, z):
        c, rmin, rmax = circ(p); a = signed_area(p)
        bb = (p.min(0).round(3), p.max(0).round(3))
        if abs(a) < 200: print("  loop area %.3f centre (%.3f,%.3f) rmin %.4f rmax %.4f bbox %s" % (a, c[0], c[1], rmin, rmax, bb))
        else: print("  big loop area %.2f bbox %s" % (a, bb))
for z in (13.0, 15.0, 16.0):
    print("== lid slice z", z)
    for p in loops(L, z):
        c, rmin, rmax = circ(p); a = signed_area(p)
        bb = (p.min(0).round(3), p.max(0).round(3))
        if abs(a) < 200: print("  loop area %.3f centre (%.3f,%.3f) rmin %.4f rmax %.4f" % (a, c[0], c[1], rmin, rmax))
        else: print("  big loop area %.2f bbox %s" % (a, bb))
# pilot depth by ray casting down standoff axis & boss axes
def ray_first_hit(tm, origin, direction):
    locs, idx, _ = tm.ray.intersects_location([origin], [direction])
    if len(locs)==0: return None
    d = np.linalg.norm(locs-np.array(origin),axis=1); return locs[np.argsort(d)]
for (x,y) in [(2.5,2.5),(67.5,2.5),(2.5,47.5),(67.5,47.5)]:
    h = ray_first_hit(tb, [x,y,20.0], [0,0,-1])
    print("standoff axis",(x,y),"hits z:", [round(v[2],3) for v in h[:4]])
for (x,y) in [(-4.087006,-3.287006),(73.287006,-3.287006),(-4.087006,53.287006),(73.287006,53.287006)]:
    h = ray_first_hit(tb, [x,y,30.0], [0,0,-1])
    print("boss axis base",(x,y),"hits z:", [round(v[2],3) for v in h[:4]])
    h = ray_first_hit(tl, [x,y,30.0], [0,0,-1])
    print("boss axis lid",(x,y),"hits z:", None if h is None else [round(v[2],3) for v in h[:4]])
# standoff top Z spread: ray down at points on standoff annulus
for (x,y) in [(2.5,2.5),(67.5,2.5),(2.5,47.5),(67.5,47.5)]:
    h = ray_first_hit(tb, [x+1.8,y,20.0], [0,0,-1]); print("standoff top", (x,y), round(h[0][2],4))
