exec(open('judge.py').read().split('# ---------- reference models')[0])
def thick(tm, origins, d):
    out=[]
    for o in origins:
        locs,_,_ = tm.ray.intersects_location([o],[d])
        if len(locs)<2: continue
        t = np.sort(np.dot(locs-np.array(o), d))
        out.append(t[1]-t[0])
    return np.array(out)
def rep(n,a): print(n, "median %.3f min %.3f max %.3f n=%d"%(np.median(a),a.min(),a.max(),len(a)))
# -X wall (ray +X from outside), away from openings/bosses: Y 5..15 & 35..45, Z -3..12 (skip 1..8.8 band near USB? opening only Y 18.7-29.5)
o=[[-10,y,z] for y in np.arange(4,47,2) for z in np.arange(-4,12,2) if not (17<y<31 and -1<z<10)]
#rep("-X wall", thick(tb,o,np.array([1.,0,0])))
o=[[90,y,z] for y in np.arange(4,47,2) for z in np.arange(-4,12,2) if not ((11<y<24 or 26<y<39) and -4<z<9)]
#rep("+X wall", thick(tb,o,np.array([-1.,0,0])))
o=[[x,-10,z] for x in np.arange(2,68,2) for z in np.arange(-4,12,2)]
#rep("-Y wall", thick(tb,o,np.array([0,1.,0])))
o=[[x,70,z] for x in np.arange(2,68,2) for z in np.arange(-4,12,2)]
#rep("+Y wall", thick(tb,o,np.array([0,-1.,0])))
o=[[x,y,-20] for x in np.arange(8,62,2) for y in np.arange(8,42,2)]
#rep("floor", thick(tb,o,np.array([0,0,1.])))
o=[[x,y,30] for x in np.arange(4,66,2) for y in np.arange(4,46,2)]
#rep("lid plate", thick(tl,o,np.array([0,0,-1.])))
# overhang scan
def overhang(tm, flip=False):
    v = tm.vertices.copy(); f = tm.faces
    if flip: v[:,2] = -v[:,2]; v[:,1] = -v[:,1]
    t = trimesh.Trimesh(v, f, process=False)
    zmin = v[:,2].min()
    n = t.face_normals; c = t.triangles_center
    bad = (n[:,2] < -math.cos(math.radians(45))) & (c[:,2] > zmin + 0.05)
    bed = (n[:,2] < -0.999) & (c[:,2] < zmin + 0.05)
    plan = np.ptp(np.asarray(v[:,0]))*np.ptp(np.asarray(v[:,1]))
    return t, bad, bed, plan
for name, tm, flip in (("base",tb,False),("lid",tl,True)):
    t,bad,bed,plan = overhang(tm, flip)
    print(name, "downward faces above bed: area %.2f; bed contact %.1f%%"%(t.area_faces[bad].sum(), 100*t.area_faces[bed].sum()/plan))
    if bad.any():
        cz = t.triangles_center[bad]; 
        # group by z level
        for z in np.unique(np.round(cz[:,2],2)):
            m = np.round(cz[:,2],2)==z
            sel = t.triangles[bad][m].reshape(-1,3)
            print("   z=%.2f area %.2f bbox %s..%s"%(z, t.area_faces[bad][m].sum(), sel.min(0).round(2), sel.max(0).round(2)))
# stability: COM of printed parts + RBA 40 g total -> use printed-volume COM, and support polygon = base underside hull
com = (tb.center_mass*tb.volume + tl.center_mass*tl.volume)/(tb.volume+tl.volume)
print("COM printed (design frame)", com.round(3), "-> above floor underside", round(com[2]+8.1,3))
bv = tb.vertices[np.abs(tb.vertices[:,2]+8.1)<1e-3]
print("support x %.3f..%.3f y %.3f..%.3f"%(bv[:,0].min(),bv[:,0].max(),bv[:,1].min(),bv[:,1].max()))
h = com[2]+8.1
for name,edge in (("-X",com[0]-bv[:,0].min()),("+X",bv[:,0].max()-com[0]),("-Y",com[1]-bv[:,1].min()),("+Y",bv[:,1].max()-com[1])):
    print("tilt to tip toward",name, round(math.degrees(math.atan2(edge,h)),1),"deg")
W = 0.040*9.81
for port,z,edge in (("USB",4.9+8.1,bv[:,0].max()-com[0]),("AUX",2.5+8.1,com[0]-bv[:,0].min())):
    print("pull",port,"restoring %.4f tipping %.4f N*m"%(W*edge/1000, 0.5*z/1000))
