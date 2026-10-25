import numpy as np, trimesh
D="/Users/robinonsay/python/llm-bt/benchmarks/enclosure/loop/iter_010/target_s0/20261024-154021"
for n in ("base","lid"):
    t=trimesh.load(f"{D}/{n}.stl",force="mesh")
    pts,fi=trimesh.sample.sample_surface_even(t,30000,radius=0.3)
    nr=t.face_normals[fi]
    o=pts-nr*1e-3
    locs,ri,_=t.ray.intersects_location(o,-nr,multiple_hits=False)
    th=np.full(len(o),np.inf); th[ri]=np.linalg.norm(locs-o[ri],axis=1)
    # exclude points within 0.3 of an edge: approximate by requiring thickness consistent with nearby; just report low values
    low=th<0.8
    print(n,"samples",len(o),"min thickness %.3f"%th.min(),"count<0.8:",low.sum())
    if low.any():
        P=pts[low]; print("  thin points bbox",P.min(0).round(2),P.max(0).round(2)); print("  samples",np.c_[P[:8].round(2),th[low][:8].round(3)])
