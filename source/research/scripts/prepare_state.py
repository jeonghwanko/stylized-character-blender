"""Export the geometry of the versioned77 input and its frozen patch selection.
This reproduces an existing experiment; it does not infer a face from reference art.
"""
import bpy, json, numpy as np
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_paths import BASE, PARAMETERS, WORK

bpy.ops.wm.open_mainfile(filepath=str(BASE), use_scripts=False, load_ui=False)
mesh = bpy.data.objects['Study_ContinuousHeadNeckTorso'].data
selection = json.loads((PARAMETERS / 'patch_selection.json').read_text())
assert len(mesh.vertices) == selection['expected_vertices']
assert len(mesh.polygons) == selection['expected_faces']
colors = np.zeros((len(mesh.vertices), 4)); counts = np.zeros(len(mesh.vertices))
for loop in mesh.loops:
    colors[loop.vertex_index] += mesh.color_attributes['SkinColor'].data[loop.index].color
    counts[loop.vertex_index] += 1
colors /= np.maximum(counts[:, None], 1)
mesh.calc_loop_triangles()
result = dict(vertices=[v.co[:] for v in mesh.vertices],
              triangles=[t.vertices[:] for t in mesh.loop_triangles],
              faces=[p.vertices[:] for p in mesh.polygons], colors=colors.tolist())
result.update({k: selection[k] for k in ['selected_faces', 'neck_protected_ids', 'boundary_loops']})
(WORK / 'source77.json').write_text(json.dumps(result))
print('Exported versioned77 state and frozen selection.')
