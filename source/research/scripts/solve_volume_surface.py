"""Broad 3D surface fairing across jaw/cheek, not a front-chart boundary.
Coordinates retain explicit positional fidelity. Neck/eye/mouth controls fixed.
This is a diagnostic native branch, never a production morph.
"""
import json,numpy as np,os
from pathlib import Path
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_paths import WORK as O
REV=os.environ.get('NEUTRAL_REV','n03');d=json.loads((O/('surface_'+REV+'.json')).read_text());P=np.array(d['vertices']);T=np.array(d['triangles']);N=len(P);rows=[];cols=[];vals=[];mass=np.zeros(N)
for tri in T:
 p=P[tri];area=np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))/2
 if area<1e-12:continue
 mass[tri]+=area/3
 for k in range(3):
  a,b,c=tri[k],tri[(k+1)%3],tri[(k+2)%3];w=.5*np.clip(np.dot(P[b]-P[a],P[c]-P[a])/(2*area),-50,50);rows.extend([b,c,b,c]);cols.extend([b,c,c,b]);vals.extend([w,w,-w,-w])
L=coo_matrix((vals,(rows,cols)),shape=(N,N)).tocsr();Q=(L.T@diags(1/np.maximum(mass,1e-7))@L).tocsr()
mask=(P[:,2]>1.230)&(P[:,2]<1.402)&(P[:,1]<.035)&(abs(P[:,0])<.155);mask[d['mouth_ids']+d['eye_ids']+d['neck_ids']]=False
free=np.flatnonzero(mask);fixed=np.flatnonzero(~mask);mouth=P[d['mouth_ids']];distance=np.linalg.norm(P[free][:,None,:]-mouth[None,:,:],axis=2).min(1)
nose=((P[free,0]/.032)**2+((P[free,2]-1.358)/.026)**2)
fidelity=20000+200000*np.exp(-(distance/.009)**2)+180000*np.exp(-nose)
A=Q[free][:,free]+diags(fidelity);rhs=-Q[free][:,fixed]@P[fixed]+fidelity[:,None]*P[free];new=P.copy();new[free]=spsolve(A,rhs);D=new-P
oldn=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]);newn=np.cross(new[T[:,1]]-new[T[:,0]],new[T[:,2]]-new[T[:,0]])
out={'revision':REV,'method':'Broad positional-fidelity 3D biharmonic fairing across chin/cheek boundary. Neck, eye aperture and mouth rim fixed. No local wrinkle field.','positions':new.tolist(),'free_vertices':len(free),'maximum_displacement_m':float(np.linalg.norm(D,axis=1).max()),'fixed_error_m':float(abs(D[fixed]).max()),'normal_dot_reversals':int((np.sum(oldn*newn,axis=1)<0).sum())};(O/('boundary_solution_'+REV+'.json')).write_text(json.dumps(out));print({k:v for k,v in out.items() if k!='positions'})
