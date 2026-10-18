"""Broad muzzle volume, coordinated skin/oral unit; no jaw close.
The nose-to-lip offset in n03 is excessive in side/75deg actual renders.
Use one broad65x28mm volume field for lips, mouth corner, cheek transition.
"""
import bpy,bmesh,json,math,numpy as np
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_paths import WORK as O
source=json.loads((O/'surface_n03.json').read_text());eye_ids=source['eye_ids']
bpy.ops.wm.open_mainfile(filepath=str(O/'neutral_n04.blend'),use_scripts=False,load_ui=False)
def smooth(t):t=max(0,min(1,t));return t*t*t*(10-15*t+6*t*t)
counts={};maximum=0
for ob in bpy.data.objects:
 if ob.type!='MESH' or not (ob.name=='Study_ContinuousHeadNeckTorso' or ob.name.startswith(('V5_MouthInterior','V5_Teeth','V5_Nostril'))):continue
 changed=0
 for v in ob.data.vertices:
  if ob.name=='Study_ContinuousHeadNeckTorso':
   if v.index in eye_ids:v.co=source['vertices'][v.index];continue
   if sum(w.weight for w in v.groups if ob.vertex_groups[w.group].name in ['Neck','UpperChest','Chest','Spine'])>.0001:continue
  x,y,z=v.co;dy=-.008*math.exp(-((x+.006)/.065)**4-((z-1.323)/.028)**4)*smooth((-y-.060)/.050)
  v.co.y+=dy;maximum=max(maximum,abs(dy));changed+=abs(dy)>1e-6
 ob.data.update();counts[ob.name]=changed
report={'source':'n04','revision':'n05','maximum_anterior_displacement_m':maximum,'field_half_width_height_m':[.065,.028],'changed_by_object':counts,'eye_aperture_restored_from':'n03 fixed eye aperture','method':'Broad anterior muzzle volume jointly moves lip/cheek transition, cavity and new teeth. No added wrinkles; no Z flattening; no inverse jaw rotation.','hypothesis':'Reduce excessive nose-to-upper-lip sagittal offset seen in n03/n04, with same cameras.'};(O/'authoring_n05.json').write_text(json.dumps(report,indent=2));print(report);bpy.ops.wm.save_as_mainfile(filepath=str(O/'neutral_n05.blend'),compress=True)
