"""A broad chin proportion and a dental ribbon authored for the new smile.
Uses n03 once as a preserved clean source; no old jaw-closing experiments.
Keeps neck, eyes, bones and all original77/75 files intact.
"""
import bpy,bmesh,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_paths import WORK as O
bpy.ops.wm.open_mainfile(filepath=str(O/'neutral_n03_fair.blend'),use_scripts=False,load_ui=False)
h=bpy.data.objects['Study_ContinuousHeadNeckTorso'];me=h.data;before=np.array([v.co[:] for v in me.vertices]);protected=[]
def smooth(t):t=max(0,min(1,t));return t*t*t*(10-15*t+6*t*t)
for v in me.vertices:
 if sum(w.weight for w in v.groups if h.vertex_groups[w.group].name in ['Neck','UpperChest','Chest','Spine'])>.0001:protected.append(v.index);continue
 x,y,z=v.co
 weight=smooth((1.319-z)/.044)*smooth((z-1.230)/.030)*smooth((.02-y)/.09)
 # A narrower, rounded chin: no vertical flattening and no jaw rotation.
 v.co.x=-.006+(x+.006)*(1-.14*weight)
 v.co.y+=.005*weight*math.exp(-((x+.006)/.080)**2)
 # Broad nose depth adjustment, smooth over26mm. Rounded tip retained.
 nw=math.exp(-(x/.026)**4-((z-1.358)/.022)**4)*smooth((-.125-y)/.025)
 v.co.y+=.004*nw
me.update();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();mouth=[v for v in bm.verts if v.is_boundary and v.co.z<1.35];adj={v:[] for v in mouth}
for e in bm.edges:
 if e.is_boundary and all(v in adj for v in e.verts):a,b=e.verts;adj[a].append(b);adj[b].append(a)
rim=[mouth[0]];previous=None
while True:
 q=next(v for v in adj[rim[-1]] if v!=previous)
 if q==rim[0]:break
 previous=rim[-1];rim.append(q)
P=np.array([v.co[:] for v in rim]);bm.free();assert len(P)==96
# Directly rebuild the shared cavity from the moved opening.
bag=bpy.data.objects['V5_MouthInterior'];verts=[];faces=[];center=P.mean(0);N=len(P)
for j in range(7):
 t=j/6
 for p in P:
  q=p*(1-.72*t)+center*.72*t;q[1]=p[1]+.001+.055*t;verts.append(q.tolist())
for j in range(6):
 for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
faces.append(tuple(range(6*N,7*N)));bag.data.clear_geometry();bag.data.from_pydata(verts,[],faces);bag.data.update()
for g in list(bag.vertex_groups):bag.vertex_groups.remove(g)
bag.vertex_groups.new(name='Head').add(list(range(len(verts))),1,'REPLACE')
# Original teeth are retained in77; only this diagnostic copy gets a clean
# stylized continuous dental ribbon, tied to the actual new lip edges.
teeth=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('V5_Teeth')];print('REPLACED_TEETH',[o.name for o in teeth]);template=teeth[0];mat=template.data.materials[0]
for o in teeth:bpy.data.objects.remove(o,do_unlink=True)
cfg=json.loads((O/'clean_surface_n02.json').read_text());m=cfg['mouth'];V=[];F=[];steps=65
for i,u in enumerate(np.linspace(-.99,.99,steps)):
 x=m['center_x']+m['radius_x']*u;centerz=m['center_z']+m['slope_z_per_x']*m['radius_x']*u+m['arc_z']*u*u;gap=m['half_opening']*math.sqrt(1-u*u)
 # Interpolate actual upper and lower rim depths at this x.
 side=P[P[:,2]>m['center_z']+m['slope_z_per_x']*(P[:,0]-m['center_x'])+m['arc_z']*((P[:,0]-m['center_x'])/m['radius_x'])**2]
 order=np.argsort(side[:,0]);y=float(np.interp(x,side[order,0],side[order,1]))+.0025
 for z,dy in [(centerz+gap+.001,0),(centerz+gap*.10,.001),(centerz+gap*.10,.005),(centerz+gap+.001,.005)]:V.append((x,y+dy,z))
for i in range(steps-1):
 for j in range(4):F.append((4*i+j,4*(i+1)+j,4*(i+1)+(j+1)%4,4*i+(j+1)%4))
F.extend([(3,2,1,0),tuple(range(4*(steps-1),4*steps))]);mesh=bpy.data.meshes.new('GentleSmile_DentalRibbon');mesh.from_pydata(V,[],F);mesh.materials.append(mat);tooth=bpy.data.objects.new('V5_Teeth_GentleSmileRibbon',mesh);bpy.context.scene.collection.objects.link(tooth);tooth.parent=h.parent;tooth.matrix_parent_inverse=h.matrix_parent_inverse.copy();tooth.matrix_world=h.matrix_world.copy();tooth.vertex_groups.new(name='Head').add(list(range(len(V))),1,'REPLACE');mod=tooth.modifiers.new('Armature','ARMATURE');mod.object=next(m.object for m in h.modifiers if m.type=='ARMATURE')
for p in mesh.polygons:p.use_smooth=True
# Move nostril indicators with the broad nasal adjustment.
for ob in bpy.data.objects:
 if ob.type=='MESH' and ob.name.startswith('V5_Nostril'):
  for v in ob.data.vertices:
   x,y,z=v.co;nw=math.exp(-(x/.026)**4-((z-1.358)/.022)**4)*smooth((-.125-y)/.025);v.co.y+=.004*nw
after=np.array([v.co[:] for v in me.vertices]);d=after-before
out={'source':'neutral_n03_fair','revision':'n04','method':'Broad chin-width/depth proportion edit; unchanged vertical positions; dental ribbon/cavity follow gentle-smile lip rim.','chin_width_factor_at_full_weight':.86,'maximum_displacement_m':float(np.linalg.norm(d,axis=1).max()),'vertical_coordinate_error_m':float(abs(d[:,2]).max()),'protected_neck_error_m':float(abs(d[protected]).max()),'teeth':'New continuous stylized ribbon in this copy only; no production dental rig claim.'};(O/'authoring_n04.json').write_text(json.dumps(out,indent=2));print(out)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'neutral_n04.blend'),compress=True)
