# ---- shorten legs (~5 heads): remap world z; arms/hands just shift ----
DZ=-0.08; HIPZ=0.83; KNEE0=0.20
K2=(HIPZ-KNEE0+DZ)/(HIPZ-KNEE0)
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name!='Ground':
        mw=o.matrix_world.copy(); o.parent=None; o.matrix_world=mw
        o.data.transform(mw); o.matrix_world=Matrix.Identity(4)
        if o.modifiers: apply_mods(o)
for o in [o for o in bpy.data.objects if o.type=='EMPTY']: bpy.data.objects.remove(o)
def _lz(z):
    if z<KNEE0: return z
    if z<HIPZ: return KNEE0+(z-KNEE0)*K2
    return z+DZ
for o in bpy.data.objects:
    if o.type!='MESH' or o.name=='Ground': continue
    me=o.data; co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    x=np.abs(co[:,0]); z=co[:,2]
    leg=np.where(z<KNEE0,z,np.where(z<HIPZ,KNEE0+(z-KNEE0)*K2,z+DZ))
    w=np.clip((x-0.215)/0.025,0,1); w=w*w*(3-2*w)
    co[:,2]=leg*(1-w)+(z+DZ)*w
    me.vertices.foreach_set('co',co.ravel()); me.update()
# material positions that reference the head
for m in bpy.data.materials:
    if not m.use_nodes: continue
    for nd in m.node_tree.nodes:
        if nd.bl_idname=='ShaderNodeVectorMath' and nd.operation in ('DISTANCE','SUBTRACT'):
            v=nd.inputs[1].default_value
            if 1.2<v[2]<1.6 and not nd.inputs[1].is_linked: nd.inputs[1].default_value=(v[0],v[1],v[2]+DZ)
try:
    import json
    jp='/workspace/character/export/ponytail_bones.json'; J=json.load(open(jp))
    J['tie'][2]+=DZ
    for k in J['bones']:
        for e in ('head','tail'): J['bones'][k][e][2]+=DZ
    J['note']='z already includes leg shortening (DZ=%.3f)'%DZ; json.dump(J,open(jp,'w'),indent=1)
except Exception as ex: print('bones json',ex)
print('REMAP done')
