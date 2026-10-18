import sys, numpy as np
from skimage.measure import marching_cubes
F=np.load(sys.argv[1]); vox=float(sys.argv[3])
v,f,n,_=marching_cubes(F,0.0,spacing=(vox,vox,vox),allow_degenerate=False)
np.savez(sys.argv[2],v=v.astype(np.float32),f=f.astype(np.int32))
print('MC',len(v),len(f))
