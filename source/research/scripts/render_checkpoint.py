import bpy,os,math,json
from pathlib import Path
from mathutils import Vector,Matrix
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_paths import WORK as O, PUBLISHED
REV=os.environ.get('STUDY_REV','n05');out=Path(os.environ.get('STUDY_RENDER_DIR',str(O/('renders_'+REV))));out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.environ.get('STUDY_INPUT',str(PUBLISHED)),use_scripts=False,load_ui=False)
scene=bpy.context.scene;arm=bpy.data.objects['CH_Armature'];arm.animation_data.action=None;arm.data.pose_position='POSE'
scene.render.film_transparent=False
for o in scene.objects:
 if o.type=='MESH' and o.data.shape_keys:
  for k in o.data.shape_keys.key_blocks:k.value=.55 if k.name=='BigSmile' else 0
for p in arm.pose.bones:p.matrix_basis.identity();p.rotation_mode='QUATERNION'
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.8
world=bpy.data.worlds.new('Study_GrayWorld');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.8,.8,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
def light(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.3))-o.location).to_track_quat('-Z','Y').to_euler()
if os.environ.get('FACE_CLOSE')=='1':
 scene.view_settings.exposure=1.0
 light('Key',(-2,-3,3.4),100,1.8);light('Fill',(2,-2,1.8),20,2.2);light('Rim',(-.4,2.1,3),70,2.4)
 nt=world.node_tree;bg=nt.nodes['Background'];bg.inputs[0].default_value=(.94,.96,1,1);bg.inputs[1].default_value=.22
 whitebg=nt.nodes.new('ShaderNodeBackground');whitebg.inputs[0].default_value=(1,1,1,1);whitebg.inputs[1].default_value=5
 lp=nt.nodes.new('ShaderNodeLightPath');mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);nt.links.new(bg.outputs[0],mix.inputs[1]);nt.links.new(whitebg.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],nt.nodes['World Output'].inputs[0])
else:light('Key',(-2,-3,3),130,2);light('Fill',(2,-1,2),35,2);light('Rim',(-1,2,3),110,1.7)
clay=bpy.data.materials.new('Study_NeutralClay');clay.use_nodes=True;p=clay.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.35,.36,.38,1);p.inputs['Roughness'].default_value=.65
cd=bpy.data.cameras.new('Study_Camera');cam=bpy.data.objects.new('Study_Camera',cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO'
all_mesh=[o for o in scene.objects if o.type=='MESH'];keep=lambda n:n.startswith(('Study_Continuous','V5_NoseHead','V5_Ear','V5_Eyeball','V5_Iris','V5_Lash','V5_Brow','V5_Nostril','V5_MouthInterior','V5_Teeth','V5_Tongue','V5_Catch')) or n=='CH_Body'
def pose(turn=0,nod=0):
 for p in arm.pose.bones:p.matrix_basis.identity()
 for name,factor in [('Neck',.4),('Head',.6)]:
  p=arm.pose.bones[name];basis=p.bone.matrix_local.to_3x3();w=Matrix.Rotation(math.radians(turn*factor),3,'Z')@Matrix.Rotation(math.radians(nod*factor),3,'X');p.rotation_quaternion=(basis.inverted()@w@basis).to_quaternion()
 bpy.context.view_layer.update()
def shot(name,loc,turn=0,nod=0,color=False):
 pose(turn,nod)
 if os.environ.get('REFERENCE_POSE')=='1':arm.animation_data.action=bpy.data.actions['ReferenceAPose'];scene.frame_set(1);bpy.context.view_layer.update()
 for o in all_mesh:o.hide_render=not keep(o.name) if not color else False
 scene.view_layers[0].material_override=None if color else clay
 close=os.environ.get('FACE_CLOSE')=='1';cam.location=loc;target=Vector((0,0,1.37 if close else 1.29));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=.55 if close else .75
 scene.render.resolution_x=768 if close else 640;scene.render.resolution_y=768;scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);print('DONE',name,flush=True)
shots=os.environ.get('STUDY_SHOTS','front,side,quarter_left,quarter_right,turn,nod_down,nod_up,color').split(',')
if 'front' in shots:shot('clay_front',(0,-5,1.29))
if 'side' in shots:shot('clay_side',(-5,0,1.29))
if 'quarter_left' in shots:shot('clay_quarter_left',(-3.5,-5,1.29))
if 'quarter_right' in shots:shot('clay_quarter_right',(3.5,-5,1.29))
if 'turn' in shots:shot('clay_turn_30',(-3.5,-5,1.29),turn=30)
if 'nod_down' in shots:shot('clay_nod_down',(-3.5,-5,1.29),nod=15)
if 'nod_up' in shots:shot('clay_nod_up',(-3.5,-5,1.29),nod=-15)
if 'color' in shots:shot('color_quarter',(-3.5,-5,1.29),color=True)
if 'face_front' in shots:shot('face_front',(0,-6,1.37),color=True)
if 'face_side' in shots:shot('face_side',(-6,0,1.37),color=True)
if 'face_oblique' in shots:shot('face_oblique',(-6,-2.8,1.37),color=True)
if 'face_oblique_75' in shots:shot('face_oblique_75',(-6,-1.607695,1.37),color=True)
if 'clay_face_oblique' in shots:shot('clay_face_oblique',(-6,-2.8,1.37),color=False)
if 'face_left' in shots:shot('face_left',(-3,-6,1.37),color=True)
if 'face_right' in shots:shot('face_right',(3,-6,1.37),color=True)
if 'clay_face_front' in shots:shot('clay_face_front',(0,-6,1.37),color=False)
if 'clay_face_left' in shots:shot('clay_face_left',(-3,-6,1.37),color=False)
if 'clay_face_side' in shots:shot('clay_face_side',(-6,0,1.37),color=False)
if 'clay_face_right' in shots:shot('clay_face_right',(3,-6,1.37),color=False)
