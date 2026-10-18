import bpy,bmesh,numpy as np,json,os
from pathlib import Path
from mathutils.kdtree import KDTree
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_paths import WORK as O, BASE, PUBLISHED
REV=os.environ.get('NEUTRAL_REV','n05')
bpy.ops.wm.open_mainfile(filepath=str(BASE),use_scripts=False,load_ui=False);h=bpy.data.objects['Study_ContinuousHeadNeckTorso'];protected=[v.co.copy() for v in h.data.vertices if sum(w.weight for w in v.groups if h.vertex_groups[w.group].name in ['Neck','UpperChest','Chest','Spine'])>.0001];base_bones={b.name:[x for row in b.matrix_local for x in row] for b in bpy.data.objects['CH_Armature'].data.bones};bm=bmesh.new();bm.from_mesh(h.data);eye_points=[v.co.copy() for v in bm.verts if v.is_boundary and v.co.z>1.35];bm.free()
bpy.ops.wm.open_mainfile(filepath=os.environ.get('NEUTRAL_INPUT',str(PUBLISHED)),use_scripts=False,load_ui=False);h=bpy.data.objects['Study_ContinuousHeadNeckTorso'];me=h.data;kd=KDTree(len(me.vertices))
for v in me.vertices:kd.insert(v.co,v.index)
kd.balance();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.normal_update();unseen=set(bm.verts);components=[]
while unseen:
 stack=[unseen.pop()];n=0
 while stack:
  v=stack.pop();n+=1
  for e in v.link_edges:
   q=e.other_vert(v)
   if q in unseen:unseen.remove(q);stack.append(q)
 components.append(n)
boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(len(e.link_faces)>2 for e in bm.edges);degen=sum(f.calc_area()<1e-12 for f in bm.faces);angles=[]
for e in bm.edges:
 p=(e.verts[0].co+e.verts[1].co)/2
 if len(e.link_faces)==2 and p.y<-.05 and 1.268<p.z<1.397:angles.append(float(np.degrees(e.calc_face_angle())))
bone_diff=max(abs(x-y) for b in bpy.data.objects['CH_Armature'].data.bones for x,y in zip(base_bones[b.name],[x for row in b.matrix_local for x in row]));unweighted=sum(not v.groups for v in me.vertices)
out={'revision':REV,'source':'77','vertices':len(me.vertices),'faces':len(me.polygons),'components':components,'boundary_edges':boundary,'nonmanifold_over_two_faces':nonmanifold,'degenerate_faces':degen,'old_neck_points':len(protected),'neck_point_max_error_m':max(kd.find(p)[2] for p in protected),'eye_aperture_points':len(eye_points),'eye_aperture_max_error_m':max(kd.find(p)[2] for p in eye_points),'bone_rest_matrix_error':bone_diff,'unweighted_vertices':unweighted,'lower_face_dihedral_p95_max':np.percentile(angles,[95,100]).tolist(),'limitations':'Geometric sanity checks only; no expression or likeness approval.'}
bm.free();(O/('audit_'+REV+'.json')).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
