# ---------- render setup ----------
import os
scn=bpy.context.scene
scn.render.engine='CYCLES'; scn.cycles.device='CPU'
scn.cycles.samples=int(os.environ.get('SAMPLES','40')); scn.cycles.use_denoising=True
scn.cycles.max_bounces=8; scn.cycles.transmission_bounces=8; scn.cycles.transparent_max_bounces=8
scn.view_settings.view_transform='Standard'; scn.view_settings.look='None'
scn.render.film_transparent=True
w=scn.world or bpy.data.worlds.new('W'); scn.world=w; w.use_nodes=True; nt=w.node_tree
bg=nt.nodes['Background']; bg.inputs[0].default_value=(0.75,0.76,0.80,1); bg.inputs[1].default_value=0.15
bg2=nt.nodes.new('ShaderNodeBackground'); bg2.inputs[0].default_value=(0.86,0.86,0.87,1); bg2.inputs[1].default_value=1.0
lp=nt.nodes.new('ShaderNodeLightPath'); mx=nt.nodes.new('ShaderNodeMixShader')
nt.links.new(lp.outputs['Is Camera Ray'],mx.inputs[0]); nt.links.new(bg.outputs[0],mx.inputs[1]); nt.links.new(bg2.outputs[0],mx.inputs[2])
nt.links.new(mx.outputs[0],nt.nodes['World Output'].inputs[0])
def area(name,loc,energy,color,size,target=(0,0,1.2)):
    l=bpy.data.lights.new(name,'AREA'); l.energy=energy; l.color=color; l.size=size
    o=bpy.data.objects.new(name,l); link(o); o.location=loc
    d=Vector(target)-Vector(loc); o.rotation_euler=d.to_track_quat('-Z','Y').to_euler(); return o
area('Key',(-1.6,-2.2,2.6),26,(1.0,0.92,0.82),1.6)
area('Fill',(2.0,-1.8,1.4),6,(0.85,0.9,1.0),2.0)
area('Rim',(0.6,2.2,2.4),28,(1.0,0.97,0.92),1.2)
area('RimL',(-1.4,1.8,1.6),10,(0.9,0.95,1.0),1.0)
# ground
bpy.ops.mesh.primitive_plane_add(size=8); g=bpy.context.active_object; g.name='Ground'
gm=mat('M_Ground',(0.86,0.86,0.87),rough=0.9); assign(g,gm); g.is_shadow_catcher=True

cam_d=bpy.data.cameras.new('Cam'); cam=bpy.data.objects.new('Cam',cam_d); link(cam); scn.camera=cam
OUT=os.environ.get('OUT','/workspace/character/work')
def shot(name,loc,target,ortho=None,lens=50,res=(900,1200)):
    cam.location=loc; d=Vector(target)-Vector(loc); cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    if ortho: cam_d.type='ORTHO'; cam_d.ortho_scale=ortho
    else: cam_d.type='PERSP'; cam_d.lens=lens
    scn.render.resolution_x,scn.render.resolution_y=res; scn.render.filepath=os.path.join(OUT,name+'.png')
    bpy.ops.render.render(write_still=True)
SHOTS=os.environ.get('SHOTS','front,face,q34').split(',')
for o in bpy.data.objects:
    if o.type=='MESH': o.data.update()
if 'save' in SHOTS:
    bpy.ops.wm.save_as_mainfile(filepath='/workspace/character/source/character_master.blend')
if 'front' in SHOTS: shot('turnaround_front',(0,-6,0.86),(0,0,0.86),ortho=1.95)
if 'side' in SHOTS: shot('turnaround_side',(6,0,0.86),(0,0,0.86),ortho=1.95)
if 'back' in SHOTS: shot('turnaround_back',(0,6,0.86),(0,0,0.86),ortho=1.95)
if 'face' in SHOTS: shot('face_closeup',(0.0,-1.15,1.465),(0,0,1.445),lens=85,res=(1000,1000))
if 'q34' in SHOTS: shot('three_quarter',(-1.9,-3.4,1.25),(0,0,0.88),lens=60,res=(900,1200))
if 'faceq' in SHOTS: shot('face_34',(-0.65,-0.95,1.485),(0,0,1.445),lens=85,res=(1000,1000))
if 'faces' in SHOTS: shot('face_side',(1.15,0,1.465),(0,0,1.445),lens=85,res=(1000,1000))
if 'feet' in SHOTS: shot('feet',(-0.55,-0.75,0.30),(0,-0.03,0.07),lens=60,res=(1000,700))
if 'hback' in SHOTS: shot('hair_back',(0.0,1.45,1.46),(0,0.08,1.38),lens=60,res=(1000,1000))
if 'hside' in SHOTS: shot('hair_side',(1.55,0.12,1.44),(0,0.12,1.38),lens=60,res=(1000,1000))
if 'hand' in SHOTS: shot('hand',(-0.75,-0.45,0.80),(-0.30,0,0.72),lens=85,res=(800,800))
