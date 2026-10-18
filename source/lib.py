import bpy, bmesh, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj); return obj

def mesh_from(name, verts, faces, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    if smooth: me.shade_smooth()
    return link(bpy.data.objects.new(name, me))

def apply_mods(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); me = bpy.data.meshes.new_from_object(ev)
    old = obj.data; obj.modifiers.clear(); obj.data = me; bpy.data.meshes.remove(old)

def set_active(obj):
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)

def tris(obj):
    dg = bpy.context.evaluated_depsgraph_get(); me = obj.evaluated_get(dg).to_mesh()
    n = sum(len(p.vertices)-2 for p in me.polygons); obj.evaluated_get(dg).to_mesh_clear(); return n

def bvh(obj):
    dg = bpy.context.evaluated_depsgraph_get(); return BVHTree.FromObject(obj, dg)

def smoothstep(a,b,x):
    t = np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)

def sweep(name, P, N, W, T, K=10, flat=0.45, cap_root=True):
    """Tapered clump tube. P points, N up normals, W widths, T thickness."""
    P=[Vector(p) for p in P]; N=[Vector(n).normalized() for n in N]; R=len(P)
    verts=[]; faces=[]
    for i in range(R):
        t = (P[min(i+1,R-1)]-P[max(i-1,0)]).normalized()
        n = (N[i]-t*N[i].dot(t)).normalized(); b = t.cross(n).normalized()
        for k in range(K):
            a = 2*math.pi*k/K; cx=math.cos(a); sy=math.sin(a)
            h = sy*(T[i]/2)*(1 if sy>0 else flat)
            verts.append(P[i] + b*cx*W[i]/2 + n*h)
    for i in range(R-1):
        for k in range(K):
            a=i*K+k; b2=i*K+(k+1)%K; c=(i+1)*K+(k+1)%K; d=(i+1)*K+k
            faces.append((a,b2,c,d))
    tip=len(verts); verts.append(P[-1]+(P[-1]-P[-2]).normalized()*0.004)
    for k in range(K): faces.append(((R-1)*K+k,(R-1)*K+(k+1)%K,tip))
    if cap_root:
        root=len(verts); verts.append(P[0])
        for k in range(K): faces.append(((k+1)%K,k,root))
    return mesh_from(name, verts, faces)

def bezier_pts(ctrl, n):
    ctrl=[np.array(c,float) for c in ctrl]
    out=[]
    for i in range(n):
        t=i/(n-1); pts=list(ctrl)
        while len(pts)>1: pts=[(1-t)*pts[j]+t*pts[j+1] for j in range(len(pts)-1)]
        out.append(pts[0])
    return out

def mat(name, color, rough=0.5, sss=0.0, spec=0.5, emit=None, alpha=1.0, coat=0.0, trans=0.0, ior=1.45):
    m=bpy.data.materials.new(name); m.use_nodes=True
    b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*color,1); b.inputs['Roughness'].default_value=rough
    b.inputs['Specular IOR Level'].default_value=spec
    if sss: 
        b.inputs['Subsurface Weight'].default_value=sss
        b.inputs['Subsurface Radius'].default_value=(1.0,0.35,0.2); b.inputs['Subsurface Scale'].default_value=0.01
    if emit: b.inputs['Emission Color'].default_value=(*emit,1); b.inputs['Emission Strength'].default_value=1.0
    if trans: b.inputs['Transmission Weight'].default_value=trans; b.inputs['IOR'].default_value=ior
    if coat: b.inputs['Coat Weight'].default_value=coat
    if alpha<1: b.inputs['Alpha'].default_value=alpha
    return m

def assign(obj, m):
    obj.data.materials.clear(); obj.data.materials.append(m)
