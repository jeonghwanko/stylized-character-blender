# ---------------- pose 'HandsOnHip' + renders + export ----------------
set_active(arm); bpy.ops.object.mode_set(mode='POSE')
pbs=arm.pose.bones
for pb in pbs: pb.rotation_mode='QUATERNION'
def upd(): bpy.context.view_layer.update()
def rot_world(name,R):
    pb=pbs[name]; M=pb.matrix.copy(); t=M.translation.copy()
    pb.matrix=Matrix.Translation(t)@R.to_4x4()@Matrix.Translation(-t)@M; upd()
def RY(d): return Matrix.Rotation(math.radians(d),3,'Y')
def RZ(d): return Matrix.Rotation(math.radians(d),3,'Z')
def RX(d): return Matrix.Rotation(math.radians(d),3,'X')
def headp(n): return pbs[n].matrix.translation.copy()
def ydir(n): return (pbs[n].matrix.to_3x3()@Vector((0,1,0))).normalized()
def aim(n,d): rot_world(n,ydir(n).rotation_difference(Vector(d).normalized()).to_matrix())
def blen(n): return arm_d.bones[n].length
def two_bone(up,lo,T,pole):
    S=headp(up); a=blen(up); b=blen(lo); v=T-S; d=min(v.length,a+b-1e-4); ax=v.normalized()
    al=(a*a-b*b+d*d)/(2*d); h=math.sqrt(max(a*a-al*al,0)); pp=(pole-ax*pole.dot(ax)).normalized()
    E=S+ax*al+pp*h; aim(up,E-S); aim(lo,T-headp(lo))
POSE_ON=os.environ.get('NOPOSE') is None
HIPS_SHIFT=Vector((-0.024,0.0,-0.010))
def apply_pose():
    pb=pbs['Hips']; pb.matrix=Matrix.Translation(HIPS_SHIFT)@pb.matrix; upd()
    rot_world('Hips',RY(4.0)@RZ(-6))
    rot_world('Spine',RY(-2.5)); rot_world('Chest',RY(-2.5)@RZ(5)); rot_world('UpperChest',RY(-1.5)@RX(-2))
    rot_world('Neck',RY(2.5)); rot_world('Head',RY(8.0)@RZ(9)@RX(4))
    rot_world('Pony_0',RY(-12)); rot_world('Pony_1',RY(-8)); rot_world('Pony_2',RY(-6))
    # legs
    for S,T,pole,yaw in (('Right',Vector((-0.092,0.010,0.095)),Vector((-0.15,-1,0)),-6),('Left',Vector((0.128,-0.040,0.098)),Vector((0.6,-1,0)),18)):
        two_bone(S+'UpperLeg',S+'LowerLeg',T,pole)
        rest=arm_d.bones[S+'Foot'].matrix_local.to_3x3()
        pbs[S+'Foot'].matrix=Matrix.Translation(headp(S+'Foot'))@(RZ(yaw)@rest).to_4x4(); upd()
    # arms: hands on hips
    for sx,S in ((1,'Left'),(-1,'Right')):
        T=Vector((sx*0.178,0.045,0.858))+HIPS_SHIFT
        two_bone(S+'UpperArm',S+'LowerArm',T,Vector((sx*1.0,0.55,0.15)))
        aim(S+'Hand',Vector((-sx*0.30,-0.62,-0.72)))
        # twist palm toward the hip
        Mr=arm_d.bones[S+'Hand'].matrix_local.to_3x3(); Mc=pbs[S+'Hand'].matrix.to_3x3()
        palm=(Mc@Mr.inverted()@PALM[S]).normalized(); y=ydir(S+'Hand')
        want=Vector((-sx,0.15,0)); want=(want-y*want.dot(y)).normalized(); palm=(palm-y*palm.dot(y)).normalized()
        ang=palm.angle(want); sgn=1 if palm.cross(want).dot(y)>0 else -1
        rot_world(S+'Hand',Matrix.Rotation(sgn*ang,3,y))
        palm_now=want
        for f in ('Index','Middle','Ring','Little'):
            for seg,deg in (('Proximal',14),('Intermediate',18),('Distal',12)):
                n=S+f+seg; yy=ydir(n); axis=yy.cross(palm_now).normalized()
                rot_world(n,Matrix.Rotation(math.radians(-deg),3,axis))
        rot_world(S+'ThumbProximal',Matrix.Rotation(math.radians(10),3,ydir(S+'Hand')))
if POSE_ON: apply_pose()
arm.animation_data_create(); act=bpy.data.actions.new('HandsOnHip'); arm.animation_data.action=act
for fr in (1,30):
    for pb in pbs:
        pb.keyframe_insert('location',frame=fr); pb.keyframe_insert('rotation_quaternion',frame=fr); pb.keyframe_insert('scale',frame=fr)
scn.frame_start=1; scn.frame_end=30; scn.frame_set(1)
bpy.ops.object.mode_set(mode='OBJECT')
TRI=sum(tris(o) for o in (body,hair,clothes,shoes,cornea,catch)); print('RIGTRIS',TRI,{o.name:tris(o) for o in (body,hair,clothes,shoes,cornea,catch)})
# ---------------- renders ----------------
SH=os.environ.get('RSHOTS','hero,pfront,pside,fneutral,fsmile,fsmile34,fblink,pclose').split(',')
os.environ['SHOTS']='none'
exec(open(os.path.join(os.path.dirname(__file__),'render.py')).read())
kb=body.data.shape_keys.key_blocks
def keys(sm=0,bl=0): kb['BigSmile'].value=sm; kb['Blink'].value=bl; body.data.update()
def posed(on): arm.data.pose_position='POSE' if on else 'REST'; upd()
hp=None
if 'hero' in SH: posed(True); keys(1); shot('pose_hero_34',(-1.05,-2.55,1.08),(0,0,0.80),lens=48,res=(900,1200))
if 'pfront' in SH: posed(True); keys(1); shot('pose_front',(0,-6,0.80),(0,0,0.80),ortho=1.95)
if 'pside' in SH: posed(True); keys(1); shot('pose_side',(6,0,0.80),(0,0,0.80),ortho=1.95)
if 'pback' in SH: posed(True); keys(1); shot('pose_back',(0,6,0.80),(0,0,0.80),ortho=1.95)
if 'pelbow' in SH: posed(True); keys(1); shot('pose_elbow_back',(0.9,1.6,1.05),(0,0,0.98),lens=50,res=(1000,1000))
if 'pclose' in SH: posed(True); keys(1); shot('pose_upper_34',(-0.75,-1.25,1.15),(0,0,1.0),lens=50,res=(1000,1000))
if 'fneutral' in SH: posed(False); keys(0); shot('face_neutral',(0.0,-1.15,1.385),(0,0,1.365),lens=85,res=(1000,1000))
if 'fsmile' in SH: posed(False); keys(1); shot('face_bigsmile',(0.0,-1.15,1.385),(0,0,1.365),lens=85,res=(1000,1000))
if 'fsmile34' in SH: posed(False); keys(1); shot('face_bigsmile_34',(-0.65,-0.95,1.405),(0,0,1.365),lens=85,res=(1000,1000))
if 'fsmileside' in SH: posed(False); keys(1); shot('face_bigsmile_side',(1.15,0,1.385),(0,0,1.365),lens=85,res=(1000,1000))
if 'fblink' in SH: posed(False); keys(0,1); shot('face_blink',(0.0,-1.15,1.385),(0,0,1.365),lens=85,res=(1000,1000))
keys(0,0); posed(True)
# remove render helpers before saving/export
for o in [o for o in bpy.data.objects if o.type in ('LIGHT','CAMERA') or o.name=='Ground']: bpy.data.objects.remove(o)
if os.environ.get('EXPORT'):
    EXP=ROOT+'/export'
    bpy.ops.object.select_all(action='DESELECT')
    for o in (arm,body,hair,clothes,shoes,cornea,catch): o.select_set(True)
    bpy.context.view_layer.objects.active=arm
    bpy.ops.export_scene.gltf(filepath=EXP+'/character_game.glb',export_format='GLB',use_selection=True,export_skins=True,export_morph=True,
        export_animations=True,export_animation_mode='ACTIONS',export_yup=True,export_def_bones=False)
    bpy.ops.export_scene.fbx(filepath=EXP+'/character_rigged.fbx',use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,
        bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_force_startend_keying=True,path_mode='COPY',embed_textures=True,
        axis_forward='-Z',axis_up='Y',mesh_smooth_type='FACE',use_armature_deform_only=True,primary_bone_axis='Y',secondary_bone_axis='X')
    bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/source/character_rigged.blend')
    print('EXPORT done')
