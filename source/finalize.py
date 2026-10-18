# ---------------- finalize: cleanup, decimate, join, UV, bake, export ----------------
import os
TEX='/workspace/character/textures'; os.makedirs(TEX,exist_ok=True)
def decimate(o,target):
    n=tris(o)
    if n>target:
        d=o.modifiers.new('dec','DECIMATE'); d.ratio=target/n; apply_mods(o)
# body: remove hidden faces
def body_hidden(c):
    if c.z<0.19: return True
    if 0.730<c.z<0.94: return True
    if abs(c.x)>0.125 and c.z>0.805: return True
    if 0.94<=c.z<1.235 and not (c.y<0 and abs(c.x)<0.085): return True
    return False
delete_faces(body,body_hidden)
decimate(body,2600)
decimate(bpy.data.objects['Head'],5200)

for h in hands: decimate(h,520)
decimate(hood,2300)
decimate(bpy.data.objects['Hood'],300)
for e_ in [o for o in bpy.data.objects if o.name.startswith('Ear_')]: decimate(e_,220)
# apply all transforms / parents
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name!='Ground':
        mw=o.matrix_world.copy(); o.parent=None; o.matrix_world=mw
        o.data.transform(mw); o.matrix_world=Matrix.Identity(4)
        if o.modifiers: apply_mods(o)
for o in [o for o in bpy.data.objects if o.type=='EMPTY']: bpy.data.objects.remove(o)
exec(open('/workspace/character/source/remap.py').read())
# groups
def grp(o):
    n=o.name
    if n.startswith(('Cornea',)): return 'Cornea'
    if n.startswith('Catch'): return 'Catch'
    if n.startswith(('Hair',)): return 'Hair'
    if n.startswith(('Head','Ear','Eyeball','Lid','LashLine','Lash_','Brow','Mouth','Body','Hand')): return 'Body'
    if n.startswith(('Sole','Shoe','Lace')): return 'Shoes'
    if n=='Ground': return None
    return 'Clothes'
groups={}
for o in bpy.data.objects:
    if o.type=='MESH':
        g=grp(o)
        if g: groups.setdefault(g,[]).append(o)
# make materials unique per group
used={}
for g,objs in groups.items():
    for o in objs:
        for i,sl in enumerate(o.material_slots):
            m=sl.material
            if m is None: continue
            if m.name in used and used[m.name]!=g:
                key=m.name+'_'+g; m2=bpy.data.materials.get(key) or m.copy(); m2.name=key; sl.material=m2
            else: used[m.name]=g
# subtle bump for cloth & hair -> baked normal
def add_bump(m,scale,strength,stretch=False):
    nt=m.node_tree; b=nt.nodes['Principled BSDF']
    tc=nt.nodes.new('ShaderNodeTexCoord'); nz=nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=scale; nz.inputs['Detail'].default_value=4
    bp=nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=strength
    nt.links.new(tc.outputs['Object'],nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'],bp.inputs['Height']); nt.links.new(bp.outputs['Normal'],b.inputs['Normal'])
for g in ('Clothes','Shoes'):
    for o in groups[g]:
        for sl in o.material_slots:
            if sl.material and not sl.material.get('bumped'): add_bump(sl.material,600,0.08); sl.material['bumped']=1
# part ids (for rigging / facial shapes)
PART_CODES=[('Head',1),('Ear',2),('Eyeball',3),('Lid',4),('LashLine',5),('Lash_',6),('Brow',7),('Mouth',8),('Body',9),('Hand',10),('Cornea',11),('Catch',12),
            ('HairTie',21),('HairFly',22),('Hair',20),('Sock',33),('Sole',40),('Shoe',41),('Lace',42),('Hoodie',30),('Hood',30),('Drawstring',30),('Aglet',30),('Shorts',31)]
for o in bpy.data.objects:
    if o.type!='MESH' or o.name=='Ground': continue
    code=35
    for pre,c in PART_CODES:
        if o.name.startswith(pre): code=c; break
    a_=o.data.attributes.new('part','INT','POINT'); a_.data.foreach_set('value',[code]*len(o.data.vertices))
# join
joined={}
names={'Body':'CH_Body','Hair':'CH_Hair','Clothes':'CH_Clothes','Shoes':'CH_Shoes','Cornea':'CH_EyeCornea','Catch':'CH_EyeCatchlight'}
for g,objs in groups.items():
    set_active(objs[0])
    for o in objs: o.select_set(True)
    bpy.ops.object.join(); o=bpy.context.active_object; o.name=names[g]; o.data.name=names[g]
    joined[g]=o
# UV
atlases={'FaceHair':(['Body','Hair'],2048),'Clothes':(['Clothes'],2048),'Shoes':(['Shoes'],1024)}
scn.render.engine='CYCLES'; scn.cycles.device='CPU'
for an,(gs,res) in atlases.items():
    objs=[joined[g] for g in gs]
    if len(objs)>1:
        for k,o in enumerate(objs):
            a=o.data.attributes.new('atlas_part','INT','FACE'); a.data.foreach_set('value',[k]*len(o.data.polygons))
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join(); objs=[bpy.context.active_object]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=0.004,area_weight=0.0,scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=0.004,rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    imgs={}
    for kind in ('BaseColor','Roughness','Normal'):
        im=bpy.data.images.new('T_%s_%s'%(an,kind),res,res,alpha=False,float_buffer=False)
        if kind!='BaseColor': im.colorspace_settings.name='Non-Color'
        imgs[kind]=im
    mats=set()
    for o in objs:
        for sl in o.material_slots: mats.add(sl.material)
    def set_target(im):
        for m in mats:
            nt=m.node_tree; n=nt.nodes.get('BAKE_TARGET') or nt.nodes.new('ShaderNodeTexImage'); n.name='BAKE_TARGET'
            n.image=im; nt.nodes.active=n
    scn.cycles.samples=4
    bk=scn.render.bake; bk.margin=8; bk.use_clear=True
    set_target(imgs['BaseColor']); bk.use_pass_direct=False; bk.use_pass_indirect=False; bk.use_pass_color=True
    bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR'},margin=8,use_clear=True)
    set_target(imgs['Roughness']); bpy.ops.object.bake(type='ROUGHNESS',margin=8,use_clear=True)
    set_target(imgs['Normal']); bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT',margin=8,use_clear=True)
    for kind,im in imgs.items():
        im.filepath_raw=os.path.join(TEX,im.name+'.png'); im.file_format='PNG'; im.save()
    # final single material per atlas
    fm=bpy.data.materials.new('M_'+an); fm.use_nodes=True; nt=fm.node_tree; b=nt.nodes['Principled BSDF']
    t1=nt.nodes.new('ShaderNodeTexImage'); t1.image=imgs['BaseColor']; nt.links.new(t1.outputs[0],b.inputs['Base Color'])
    t2=nt.nodes.new('ShaderNodeTexImage'); t2.image=imgs['Roughness']; nt.links.new(t2.outputs[0],b.inputs['Roughness'])
    t3=nt.nodes.new('ShaderNodeTexImage'); t3.image=imgs['Normal']; nm=nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value=1.0
    nt.links.new(t3.outputs[0],nm.inputs['Color']); nt.links.new(nm.outputs[0],b.inputs['Normal'])
    b.inputs['Specular IOR Level'].default_value=0.4
    if an=='FaceHair':
        b.inputs['Subsurface Weight'].default_value=0.08; b.inputs['Subsurface Radius'].default_value=(1.0,0.35,0.2); b.inputs['Subsurface Scale'].default_value=0.01
    for o in objs:
        o.data.materials.clear(); o.data.materials.append(fm)
    if len(gs)>1:
        o=objs[0]; bm=bmesh.new(); bm.from_mesh(o.data); lay=bm.faces.layers.int.get('atlas_part')
        hair_faces=[fc for fc in bm.faces if fc[lay]==1]
        bm2=bm.copy(); 
        bmesh.ops.delete(bm,geom=hair_faces,context='FACES'); bm.to_mesh(o.data); bm.free()
        lay2=bm2.faces.layers.int.get('atlas_part')
        bmesh.ops.delete(bm2,geom=[fc for fc in bm2.faces if fc[lay2]==0],context='FACES')
        me2=bpy.data.meshes.new('CH_Hair'); bm2.to_mesh(me2); bm2.free()
        h2=bpy.data.objects.new('CH_Hair',me2); link(h2); me2.materials.clear(); me2.materials.append(fm)
        o.name='CH_Body'; o.data.name='CH_Body'
        for oo in (o,h2):
            if 'atlas_part' in oo.data.attributes: oo.data.attributes.remove(oo.data.attributes['atlas_part'])
        joined['Body']=o; joined['Hair']=h2# simple eye materials
joined['Cornea'].data.materials.clear(); joined['Cornea'].data.materials.append(M['cornea'])
joined['Catch'].data.materials.clear(); joined['Catch'].data.materials.append(M['catch'])
# report
TOT=0
for g,o in joined.items():
    n=tris(o); TOT+=n; print('FINALTRIS',o.name,n)
print('FINALTRIS TOTAL',TOT)
# export
EXP='/workspace/character/export'; os.makedirs(EXP,exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for o in joined.values(): o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(EXP,'character_neutral.glb'),use_selection=True,export_format='GLB',export_yup=True)
bpy.ops.export_scene.fbx(filepath=os.path.join(EXP,'character_neutral.fbx'),use_selection=True,path_mode='COPY',embed_textures=False,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',mesh_smooth_type='FACE')
bpy.ops.wm.save_as_mainfile(filepath='/workspace/character/source/character_master.blend')
