import bpy,bmesh,json,os
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_paths import WORK as O
REV=os.environ.get('NEUTRAL_REV','n02');bpy.ops.wm.open_mainfile(filepath=os.environ.get('NEUTRAL_INPUT',str(O/('neutral_'+REV+'.blend'))),use_scripts=False,load_ui=False);h=bpy.data.objects['Study_ContinuousHeadNeckTorso'];me=h.data;me.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(me);mouth=[v.index for v in bm.verts if v.is_boundary and v.co.z<1.35];eyes=[v.index for v in bm.verts if v.is_boundary and v.co.z>1.35];bm.free();assert len(mouth)==96,len(mouth)
out={'vertices':[v.co[:] for v in me.vertices],'triangles':[t.vertices[:] for t in me.loop_triangles],'mouth_ids':mouth,'eye_ids':eyes,'neck_ids':[v.index for v in me.vertices if sum(w.weight for w in v.groups if h.vertex_groups[w.group].name in ['Neck','UpperChest','Chest','Spine'])>.0001],'new_vertex_ids':[v.index for v in me.vertices if me.attributes['NeutralStudyColor'].data[v.index].value>=7500]}
(O/('surface_'+REV+'.json')).write_text(json.dumps(out));print(len(out['new_vertex_ids']))
