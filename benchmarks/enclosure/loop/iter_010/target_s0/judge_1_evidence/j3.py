exec(open('judge.py').read().split('# ---------- reference models')[0])
# apertures in end walls
def ap(x0,x1):
    slab = box(x0,-3.5,-8.1,x1,53.5,16.6)
    a = slab - ALL
    regs=[r for r in a.decompose() if r.volume()>1.0]
    return [( round(r.volume(),2), [round(v,3) for v in r.bounding_box()]) for r in regs]
print("V-AP-USB (-X wall X -4.3..-1.9):", ap(-4.3,-1.9))
print("V-AP-AUX (+X wall X 71.1..73.5):", ap(71.1,73.5))
print("-Y wall:", ap(-1e9,-1e9+1) if False else "")
def apy(y0,y1):
    slab = box(-4.3,y0,-8.1,73.5,y1,16.6); a = slab-ALL
    return [( round(r.volume(),2), [round(v,3) for v in r.bounding_box()]) for r in a.decompose() if r.volume()>1.0]
print("-Y wall slab:", apy(-3.5,-1.1)); print("+Y wall slab:", apy(51.1,53.5))
# opening section at mid-wall
for name,x in (("USB",-3.1),("AUX",72.3)):
    cs = ALL.rotate([0,90,0]).slice(-x) if False else None
# simpler: ray grid through walls to find opening extents
def opening_extent(x_from, x_to, ys, zs):
    pts=[]
    for y in ys:
        for z in zs:
            locs,_,_ = tb.ray.intersects_location([[x_from,y,z]],[[np.sign(x_to-x_from),0,0]])
            if len(locs)==0: pts.append((y,z)); continue
            d = np.abs(locs[:,0]-x_from)
            if d.min() > abs(x_to-x_from): pts.append((y,z))
    return np.array(pts)
ys=np.arange(-3.4,53.5,0.05); zs=np.arange(-8.0,16.5,0.05)
# USB: ray from x=-4.31 toward +X up to x=-1.89; hits mean wall material
p = opening_extent(-4.35,-1.85, ys, zs)
print("USB opening through-ray extents Y %.2f..%.2f Z %.2f..%.2f n=%d"%(p[:,0].min(),p[:,0].max(),p[:,1].min(),p[:,1].max(),len(p)))
p = opening_extent(73.55,71.05, ys, zs)
for lo,hi in ((10,25),(25,40)):
    q=p[(p[:,0]>lo)&(p[:,0]<hi)]
    print("AUX opening Y %.2f..%.2f Z %.2f..%.2f centre (%.2f,%.2f) n=%d"%(q[:,0].min(),q[:,0].max(),q[:,1].min(),q[:,1].max(),(q[:,0].min()+q[:,0].max())/2,(q[:,1].min()+q[:,1].max())/2,len(q)))
# L3.5.2.1 / L3.6.2.1 oversize inside grown envelopes
ux,uy,uz=-1.3,24.09,4.9
V_USB = box(ux-1.5,uy-3.45,uz-0.925,ux+5.0,uy+3.45,uz+0.925)+box(ux-1.5-40,uy-5,uz-3.5,ux-1.5,uy+5,uz+3.5)
grow = V_USB.minkowski_sum(M.sphere(1.5, 24)) if hasattr(V_USB,'minkowski_sum') else None
apu = box(-4.3,-3.5,-8.1,-1.9,53.5,16.6) - ALL
apu = sum([r for r in apu.decompose() if r.volume()>1.0 and r.bounding_box()[1]>0 and r.bounding_box()[4]<50], M())
print("USB aperture outside grown envelope vol:", (apu - grow).volume())
jy=[17.600010582941664, 32.84001056943333]
VJ = cylx(jy[0],2.5,70,71,3.5)+cylx(jy[0],2.5,71,111,8.0)+cylx(jy[1],2.5,70,71,3.5)+cylx(jy[1],2.5,71,111,8.0)
gj = VJ.minkowski_sum(M.sphere(1.5,24))
apa = box(71.1,-3.5,-8.1,73.5,53.5,16.6) - ALL
apa = sum([r for r in apa.decompose() if r.volume()>1.0 and r.bounding_box()[1]>0 and r.bounding_box()[4]<50], M())
print("AUX aperture outside grown envelopes vol:", (apa - gj).volume())
# unlisted openings: plug the three openings, then see whether cavity connects to outside
plugs = box(-4.5,18.0,0.0,-1.7,30.2,9.6) + cylx(jy[0],2.5,70.9,73.7,9.6) + cylx(jy[1],2.5,70.9,73.7,9.6)
closed = ALL + plugs
big = box(-20,-20,-20,90,70,30)
comps = (big - closed).decompose()
print("void components after plugging listed openings:", [(round(c.volume(),1),[round(v,2) for v in c.bounding_box()]) for c in comps if c.volume()>0.5])
comps2 = (big - ALL).decompose()
print("void components unplugged:", [(round(c.volume(),1)) for c in comps2 if c.volume()>0.5])
