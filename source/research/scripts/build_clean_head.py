"""Fresh broad facial surface and directly authored small smile.
No inverse jaw rotation and no accumulated frozen-smile sculpt offsets.
The unchanged outer boundary shares vertices with the existing head/neck.
"""
import bpy,bmesh,json,math,os,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from mathutils.bvhtree import BVHTree
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_paths import WORK as O, BASE, PARAMETERS
REV=os.environ.get('NEUTRAL_REV','n01');cfg=json.loads((O/('clean_surface_'+REV+'.json')).read_text());src=json.loads((O/'source77.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(BASE),use_scripts=False,load_ui=False)
h=bpy.data.objects['Study_ContinuousHeadNeckTorso'];me=h.data;P=np.array(src['vertices']);tree=BVHTree.FromPolygons([Vector(p) for p in P],src['triangles'],all_triangles=True);C=np.array(cfg['coefficients']);colors=[Vector(c) for c in src['colors']]
def basis(x,knots):
 x=min(max(x,knots[0]+1e-10),knots[-1]-1e-10);b=np.array([float(knots[i]<=x<knots[i+1]) for i in range(len(knots)-1)])
 for k in range(1,4):
  q=np.zeros(len(b)-1)
  for i in range(len(q)):
   if knots[i+k]!=knots[i]:q[i]+=(x-knots[i])/(knots[i+k]-knots[i])*b[i]
   if knots[i+k+1]!=knots[i+1]:q[i]+=(knots[i+k+1]-x)/(knots[i+k+1]-knots[i+1])*b[i+1]
  b=q
 return b
def macro(x,z):return float(basis(x,cfg['knots_x'])@C@basis(z,cfg['knots_z']))
def smooth(t):t=max(0,min(1,t));return t*t*t*(10-15*t+6*t*t)
def smin(a,b,k):q=max(0,min(1,.5+.5*(b-a)/k));return b*(1-q)+a*q-k*q*(1-q)
def ellipsoid(x,y,z,c,r):return (math.sqrt(((x-c[0])/r[0])**2+((y-c[1])/r[1])**2+((z-c[2])/r[2])**2)-1)*min(r)
bm=bmesh.new();bm.from_mesh(me);tag=bm.verts.layers.int.new('NeutralStudyColor');deform=bm.verts.layers.deform.verify();bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();oldverts=list(bm.verts)
for v in bm.verts:v[tag]=v.index
loops=src['boundary_loops'];outer=max(loops,key=lambda q:abs(sum(P[a,0]*P[b,2]-P[b,0]*P[a,2] for a,b in zip(q,q[1:]+q[:1]))));outerv=[oldverts[i] for i in outer];poly=P[outer][:,[0,2]]
def inside(p,poly):
 hit=False
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
def boundary_distance(p,poly):
 a=poly;b=np.roll(poly,-1,axis=0);v=b-a;t=np.clip(np.sum((p-a)*v,axis=1)/np.maximum(np.sum(v*v,axis=1),1e-16),0,1);return float(np.linalg.norm(a+v*t[:,None]-p,axis=1).min())
m=cfg['mouth'];theta=np.linspace(0,2*np.pi,2001);u=np.cos(theta);dense=np.column_stack([m['center_x']+m['radius_x']*u,m['center_z']+m['slope_z_per_x']*m['radius_x']*u+m['arc_z']*u*u+m['half_opening']*np.sin(theta)]);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(dense,axis=0),axis=1))];a=np.linspace(0,arc[-1],m['vertices'],endpoint=False);mouthxz=np.column_stack([np.interp(a,arc,dense[:,i]) for i in range(2)])
assert all(inside(p,poly) for p in mouthxz),'New mouth outside shared facial patch'
def authored_y(x,z):
 base=macro(x,z);nose=cfg['nose'];lo=base-.07;hi=base
 for _ in range(25):
  y=(lo+hi)/2;d=smin(base-y,ellipsoid(x,y,z,nose['center'],nose['radii']),nose['blend_radius'])
  for side in [-1,1]:d=smin(d,ellipsoid(x,y,z,(side*.014,-.144,1.350),(.008,.010,.007)),.005)
  if d>0:lo=y
  else:hi=y
 y=(lo+hi)/2;distance=boundary_distance(np.array([x,z]),mouthxz)
 if distance<.010 and not inside(np.array([x,z]),mouthxz):
  centerline=m['center_z']+m['slope_z_per_x']*(x-m['center_x'])+m['arc_z']*((x-m['center_x'])/m['radius_x'])**2
  lower=z<centerline;amplitude=.0025 if lower else .0012;y-=amplitude*math.sin(math.pi*distance/.010)**2
 return y
def position_color(x,z):
 y=authored_y(x,z);dist=boundary_distance(np.array([x,z]),poly);blend=smooth(dist/.018);hit,normal,fi,dd=tree.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)))
 if hit is not None and blend<1:y=hit.y*(1-blend)+y*blend
 color=np.array(cfg['skin_color']);blush=max(math.exp(-((x-.075)/.047)**2-((z-1.345)/.028)**2),math.exp(-((x+.075)/.047)**2-((z-1.345)/.028)**2));color[:3]=color[:3]*(1-.35*blush)+np.array([.95,.23,.12])*.35*blush
 lipd=boundary_distance(np.array([x,z]),mouthxz);mid=m['center_z']+m['slope_z_per_x']*(x-m['center_x'])+m['arc_z']*((x-m['center_x'])/m['radius_x'])**2
 if lipd<.010:
  weight=math.exp(-(lipd/(.0055 if z<mid else .0025))**2)*(.85 if z<mid else .35);color[:3]=color[:3]*(1-weight)+np.array([.96,.26,.18])*weight
 if blend<1 and fi is not None:
  ids=src['triangles'][fi];a,b,c=P[ids];uv=np.linalg.lstsq(np.column_stack([b-a,c-a]),np.array(hit)-a,rcond=None)[0];ww=[1-uv.sum(),*uv];oldcolor=sum(np.array(src['colors'][i])*w for i,w in zip(ids,ww));color=oldcolor*(1-blend)+color*blend
 return (x,y,z),color
headgroup=h.vertex_groups['Head'].index;newverts=[]
def new_vertex(xz):
 co,col=position_color(*xz);v=bm.verts.new(co);v[tag]=len(colors);colors.append(Vector(col));v[deform][headgroup]=1.;newverts.append(v);return v
mouthv=[new_vertex(p) for p in mouthxz];verts=outerv+mouthv;edges=[]
for start,n in [(0,len(outerv)),(len(outerv),len(mouthv))]:edges.extend((start+i,start+(i+1)%n) for i in range(n))
# Three smoothly spaced rings control the lip roll. The remaining face uses
# a regular4mm chart grid rather than the old smile's irregular dense mesh.
e=np.roll(mouthxz,-1,axis=0)-mouthxz;e/=np.linalg.norm(e,axis=1)[:,None];signed=sum(np.cross(a,b) for a,b in zip(mouthxz,np.roll(mouthxz,-1,axis=0)));norm=np.column_stack([e[:,1],-e[:,0]])*(1 if signed>0 else -1);norm+=np.roll(norm,1,axis=0);norm/=np.linalg.norm(norm,axis=1)[:,None]
for distance in [.0015,.004,.008]:
 ring=mouthxz+norm*distance;start=len(verts);verts.extend(new_vertex(p) for p in ring);edges.extend((start+i,start+(i+1)%len(ring)) for i in range(len(ring)))
for x in np.arange(poly[:,0].min(),poly[:,0].max(),.004):
 for z in np.arange(poly[:,1].min(),poly[:,1].max(),.004):
  p=np.array([x,z])
  if inside(p,poly) and not inside(p,mouthxz) and boundary_distance(p,poly)>.002 and boundary_distance(p,mouthxz)>.0105:verts.append(new_vertex(p))
cv,ce,cf,ov,oe,of=delaunay_2d_cdt([Vector((v.co.x,v.co.z)) for v in verts],edges,[],0,1e-8);mapping=[]
for p,orig in zip(cv,ov):mapping.append(verts[orig[0]] if orig else new_vertex((p.x,p.y)))
faces=[]
for f in cf:
 p=np.array([sum(cv[i].x for i in f)/len(f),sum(cv[i].y for i in f)/len(f)])
 if inside(p,poly) and not inside(p,mouthxz):faces.append([mapping[i] for i in f])
old_rim=[v.co.copy() for v in mouthv];bmesh.ops.delete(bm,geom=[bm.faces[i] for i in src['selected_faces']],context='FACES_ONLY')
for vs in faces:
 f=bm.faces.new(vs);f.material_index=0;f.smooth=True
bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();me.update();ca=me.color_attributes['SkinColor'];attr=me.attributes['NeutralStudyColor']
for lp in me.loops:ca.data[lp.index].color=colors[attr.data[lp.vertex_index].value]
# A new cavity follows the new shared opening, instead of deforming the old
# large-smile bag through itself. Original material and armature stay attached.
bag=bpy.data.objects['V5_MouthInterior'];bv=[];bf=[];N=len(old_rim);center=Vector((m['center_x'],-.08,m['center_z']))
for layer in range(7):
 t=layer/6
 for p in old_rim:
  q=p.lerp(center,t*.72);q.y=p.y+.001+.055*t;bv.append(tuple(q))
for layer in range(6):
 for i in range(N):bf.append((layer*N+i,layer*N+(i+1)%N,(layer+1)*N+(i+1)%N,(layer+1)*N+i))
bf.append(tuple(range(6*N,7*N)));print('OLD_BAG_ATTACHMENT',bag.parent_type,bag.parent_bone,[g.name for g in bag.vertex_groups],flush=True)
bag.data.clear_geometry();bag.data.from_pydata(bv,[],bf);bag.data.update()
# The source cavity has a different attachment convention. Match this new
# cavity explicitly to the continuous head's coordinate/armature convention.
bag.parent=h.parent;bag.parent_type=h.parent_type;bag.parent_bone=h.parent_bone;bag.matrix_parent_inverse=h.matrix_parent_inverse.copy();bag.matrix_world=h.matrix_world.copy()
for group in list(bag.vertex_groups):bag.vertex_groups.remove(group)
bag.vertex_groups.new(name='Head').add(list(range(len(bv))),1.,'REPLACE')
headarm=next(mod for mod in h.modifiers if mod.type=='ARMATURE');bagarm=next((mod for mod in bag.modifiers if mod.type=='ARMATURE'),None)
if bagarm is None:bagarm=bag.modifiers.new('NeutralOralArmature','ARMATURE')
bagarm.object=headarm.object
for ob in bpy.data.objects:
 if ob.type!='MESH':continue
 if ob.name.startswith('V5_Teeth'):
  for v in ob.data.vertices:v.co.x=m['center_x']+(v.co.x-m['center_x'])*.86;v.co.y+=.002
 if ob.name.startswith('V5_Nostril'):
  center=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices);shift=authored_y(center.x,center.z)-center.y-.0004
  for v in ob.data.vertices:v.co.y+=shift
h['neutral_research']='Direct authored small-smile broad surface;81 cubic macro controls; original77/75 preserved; not production rig.'
report={'revision':REV,'source':'77','old_faces_replaced':len(src['selected_faces']),'new_patch_triangles':len(faces),'macro_controls':81,'mouth_vertices':N,'new_head_vertices':len(me.vertices),'new_head_faces':len(me.polygons),'outer_boundary_vertices':len(outer),'method':cfg['method'],'limitations':['New small-smile design inference; no matching neutral front reference.','Partial lower-face retopology, no production UV/morph signoff.','Fixed outer/eye/neck boundary; original underjaw retained.']}
(O/('construction_'+REV+'.json')).write_text(json.dumps(report,indent=2));print(report);bpy.ops.wm.save_as_mainfile(filepath=str(O/('neutral_'+REV+'.blend')),compress=True)
