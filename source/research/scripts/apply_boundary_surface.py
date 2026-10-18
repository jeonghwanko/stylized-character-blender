import bpy,json,os
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_paths import WORK as O
REV=os.environ.get('NEUTRAL_REV','n02');bpy.ops.wm.open_mainfile(filepath=os.environ.get('NEUTRAL_INPUT',str(O/('neutral_'+REV+'.blend'))),use_scripts=False,load_ui=False);d=json.loads((O/('boundary_solution_'+REV+'.json')).read_text());h=bpy.data.objects['Study_ContinuousHeadNeckTorso'];assert len(h.data.vertices)==len(d['positions'])
for v,p in zip(h.data.vertices,d['positions']):v.co=p
h.data.update();h['broad_boundary_fairing']=d['method'];bpy.ops.wm.save_as_mainfile(filepath=str(O/('neutral_'+REV+'_fair.blend')),compress=True)
