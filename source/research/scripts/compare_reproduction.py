"""Check reconstructed n05 geometry and skeleton against the published checkpoint."""
import bpy, json, sys, numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_paths import PUBLISHED, WORK

def read(path):
    bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False, load_ui=False)
    meshes = {o.name: (np.array([v.co[:] for v in o.data.vertices]), len(o.data.polygons))
              for o in bpy.data.objects if o.type == 'MESH'}
    bones = {b.name: np.array(b.matrix_local) for b in bpy.data.objects['CH_Armature'].data.bones}
    return meshes, bones

expected, expected_bones = read(PUBLISHED)
actual, actual_bones = read(WORK / 'neutral_n05.blend')
assert expected.keys() == actual.keys()
maximum = 0.0
for name, (points, faces) in expected.items():
    other, other_faces = actual[name]
    assert len(points) == len(other) and faces == other_faces, name
    if np.array_equal(points, other): continue
    tree = KDTree(len(other))
    for i, point in enumerate(other): tree.insert(point, i)
    tree.balance()
    error = max(tree.find(point)[2] for point in points)
    maximum = max(maximum, error)
    assert error < 1e-5, (name, error)
assert expected_bones.keys() == actual_bones.keys()
bone_error = max(float(abs(expected_bones[n] - actual_bones[n]).max()) for n in expected_bones)
assert bone_error == 0
result = dict(meshes=len(actual), maximum_vertex_distance_m=maximum,
              bone_rest_matrix_error=bone_error, passed=True,
              limitation='Geometry reproducibility only, not a likeness or animation approval.')
(WORK / 'reproduction_check.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))
