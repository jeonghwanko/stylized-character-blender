import sys, os, math, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix, Quaternion
import lib; importlib.reload(lib)
from lib import *

ROOT='/workspace/character'
HC=Vector((0,0.0,1.470))
clear()
scn=bpy.context.scene

# ---------------- materials ----------------
M={}
M['skin']=mat('M_Skin',(0.98,0.70,0.53),rough=0.48,sss=0.12,spec=0.35)
M['blush']=None
M['sclera']=mat('M_Sclera',(0.96,0.96,0.95),rough=0.3,emit=(1,0.99,0.97))
M['sclera'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=0.12
M['iris']=None
M['cornea']=mat('M_Cornea',(1,1,1),rough=0.0,trans=1.0,ior=1.2,spec=0.6)
M['catch']=mat('M_Catchlight',(1,1,1),rough=1,emit=(1,1,1))
M['lash']=mat('M_Lash',(0.10,0.05,0.03),rough=0.6)
M['brow']=mat('M_Brow',(0.58,0.32,0.12),rough=0.6)
M['mouth']=mat('M_Mouth',(0.32,0.07,0.06),rough=0.6)
M['hair']=None
M['tee']=mat('M_Tee',(0.88,0.88,0.86),rough=0.85)
M['hood']=mat('M_Hoodie',(0.95,0.30,0.22),rough=0.8)
M['hood_rib']=mat('M_HoodieRib',(0.85,0.24,0.17),rough=0.85)
M['shorts']=mat('M_Shorts',(0.07,0.07,0.08),rough=0.75)
M['trim']=mat('M_Trim',(0.9,0.9,0.88),rough=0.7)
M['sock']=mat('M_Sock',(0.92,0.91,0.89),rough=0.9)
M['shoe']=mat('M_ShoeWhite',(0.92,0.92,0.92),rough=0.55)
M['shoe_acc']=mat('M_ShoeCoral',(0.95,0.32,0.24),rough=0.55)
M['sole']=mat('M_Sole',(0.96,0.95,0.93),rough=0.6)
M['string']=mat('M_String',(0.95,0.94,0.92),rough=0.7)
M['tie']=mat('M_HairTie',(0.95,0.30,0.25),rough=0.6)
M['zip']=mat('M_Zip',(0.55,0.15,0.12),rough=0.5)

def skin_shader(m):
    nt=m.node_tree; b=nt.nodes['Principled BSDF']
    tc=nt.nodes.new('ShaderNodeTexCoord'); 
    # blush: two soft spots on cheeks in world space
    def spot(cx):
        sub=nt.nodes.new('ShaderNodeVectorMath'); sub.operation='DISTANCE'
        nt.links.new(tc.outputs['Object'],sub.inputs[0]); sub.inputs[1].default_value=(cx,-0.118,HC.z-0.053)
        mr=nt.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value=0.0; mr.inputs[2].default_value=0.032
        mr.inputs[3].default_value=1.0; mr.inputs[4].default_value=0.0; mr.interpolation_type='SMOOTHSTEP'
        nt.links.new(sub.outputs['Value'],mr.inputs[0]); return mr
    s1=spot(0.072); s2=spot(-0.072)
    mx=nt.nodes.new('ShaderNodeMath'); mx.operation='MAXIMUM'
    nt.links.new(s1.outputs[0],mx.inputs[0]); nt.links.new(s2.outputs[0],mx.inputs[1])
    mix=nt.nodes.new('ShaderNodeMix'); mix.data_type='RGBA'
    mix.inputs[6].default_value=(0.98,0.70,0.53,1); mix.inputs[7].default_value=(0.95,0.42,0.36,1)
    fac=nt.nodes.new('ShaderNodeMath'); fac.operation='MULTIPLY'; fac.inputs[1].default_value=0.55
    nt.links.new(mx.outputs[0],fac.inputs[0]); nt.links.new(fac.outputs[0],mix.inputs[0])
    nt.links.new(mix.outputs[2],b.inputs['Base Color'])
skin_shader(M['skin'])

def iris_mat():
    m=mat('M_Iris',(0.1,0.4,0.6),rough=0.3); nt=m.node_tree; b=nt.nodes['Principled BSDF']
    tc=nt.nodes.new('ShaderNodeAttribute'); tc.attribute_name='eye_local'; sep=nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Vector'],sep.inputs[0])
    cmb=nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(sep.outputs[0],cmb.inputs[0]); nt.links.new(sep.outputs[2],cmb.inputs[1])
    ln=nt.nodes.new('ShaderNodeVectorMath'); ln.operation='LENGTH'; nt.links.new(cmb.outputs[0],ln.inputs[0])
    dv=nt.nodes.new('ShaderNodeMath'); dv.operation='DIVIDE'; dv.inputs[1].default_value=IRIS_R
    nt.links.new(ln.outputs['Value'],dv.inputs[0])
    cr=nt.nodes.new('ShaderNodeValToRGB'); r=cr.color_ramp; r.interpolation='EASE'
    r.elements[0].position=0.40; r.elements[0].color=(0.01,0.01,0.015,1)
    e=r.elements.new(0.46); e.color=(0.10,0.42,0.55,1)
    e=r.elements.new(0.70); e.color=(0.18,0.60,0.72,1)
    e=r.elements.new(0.90); e.color=(0.07,0.30,0.45,1)
    r.elements[-1].position=1.0; r.elements[-1].color=(0.02,0.08,0.14,1)
    nt.links.new(dv.outputs[0],cr.inputs[0])
    # lighten lower half (light pooling)
    mz=nt.nodes.new('ShaderNodeMapRange'); mz.inputs[1].default_value=IRIS_R*0.2; mz.inputs[2].default_value=-IRIS_R
    mz.inputs[3].default_value=0.0; mz.inputs[4].default_value=0.45
    nt.links.new(sep.outputs[2],mz.inputs[0])
    mix=nt.nodes.new('ShaderNodeMix'); mix.data_type='RGBA'; mix.blend_type='SCREEN'
    nt.links.new(mz.outputs[0],mix.inputs[0]); nt.links.new(cr.outputs[0],mix.inputs[6]); mix.inputs[7].default_value=(0.35,0.75,0.75,1)
    # keep pupil dark
    pm=nt.nodes.new('ShaderNodeMapRange'); pm.inputs[1].default_value=0.40; pm.inputs[2].default_value=0.47
    nt.links.new(dv.outputs[0],pm.inputs[0])
    mix2=nt.nodes.new('ShaderNodeMix'); mix2.data_type='RGBA'
    nt.links.new(pm.outputs[0],mix2.inputs[0]); mix2.inputs[6].default_value=(0.01,0.01,0.015,1); nt.links.new(mix.outputs[2],mix2.inputs[7])
    sm_=nt.nodes.new('ShaderNodeMapRange'); sm_.inputs[1].default_value=0.97; sm_.inputs[2].default_value=1.03
    nt.links.new(dv.outputs[0],sm_.inputs[0])
    back=nt.nodes.new('ShaderNodeMath'); back.operation='GREATER_THAN'; back.inputs[1].default_value=0.0
    nt.links.new(sep.outputs[1],back.inputs[0])
    mx_=nt.nodes.new('ShaderNodeMath'); mx_.operation='MAXIMUM'; nt.links.new(sm_.outputs[0],mx_.inputs[0]); nt.links.new(back.outputs[0],mx_.inputs[1])
    mix3=nt.nodes.new('ShaderNodeMix'); mix3.data_type='RGBA'; nt.links.new(mx_.outputs[0],mix3.inputs[0])
    nt.links.new(mix2.outputs[2],mix3.inputs[6]); mix3.inputs[7].default_value=(0.96,0.96,0.95,1)
    nt.links.new(mix3.outputs[2],b.inputs['Base Color'])
    b.inputs['Emission Color'].default_value=(1,0.99,0.97,1); b.inputs['Emission Strength'].default_value=0.0
    return m

def hair_mat():
    m=mat('M_Hair',(0.95,0.62,0.18),rough=0.42,spec=0.45); nt=m.node_tree; b=nt.nodes['Principled BSDF']
    # root-to-tip & AO-ish: darker deeper orange low, bright gold up; driven by world Z and per-clump attribute 'tipt'
    at=nt.nodes.new('ShaderNodeAttribute'); at.attribute_name='hair_t'
    cr=nt.nodes.new('ShaderNodeValToRGB'); r=cr.color_ramp
    r.elements[0].position=0.0; r.elements[0].color=(0.88,0.40,0.03,1)
    e=r.elements.new(0.35); e.color=(1.0,0.60,0.08,1)
    r.elements[-1].position=1.0; r.elements[-1].color=(1.0,0.78,0.22,1)
    nt.links.new(at.outputs['Fac'],cr.inputs[0]); nt.links.new(cr.outputs[0],b.inputs['Base Color'])
    b.inputs['Sheen Weight'].default_value=0.25; b.inputs['Sheen Tint'].default_value=(1,0.85,0.5,1)
    return m

IRIS_R=0.0
# ---------------- head (SDF sculpt base, radially projected clean sphere) ----------------
HC=Vector((0,0.0,1.455))
ER=0.044; EYE_Y=0.84; EYE_SCALE=(1.0,EYE_Y,1.15)
EYE_X=0.059; EYE_Z=-0.012
def sd_ell(p,c,r):
    q=(p-np.array(c))/np.array(r); k0=np.linalg.norm(q,axis=-1); k1=np.linalg.norm(q/np.array(r),axis=-1)
    return k0*(k0-1)/np.maximum(k1,1e-9)
def smin(a,b,k):
    h=np.clip(0.5+0.5*(b-a)/k,0,1); return b*(1-h)+a*h-k*h*(1-h)
def smax(a,b,k): return -smin(-a,-b,k)
PARTS=[  # (center rel HC, radii, blend)
    ((0,0.015,0.025),(0.150,0.150,0.148),None),       # cranium
    ((0,-0.018,-0.050),(0.100,0.104,0.092),0.045),     # jaw / lower face
    ((0.062,-0.066,-0.060),(0.056,0.058,0.050),0.035), # cheek L
    ((-0.062,-0.066,-0.060),(0.056,0.058,0.050),0.035),# cheek R
    ((0,-0.078,-0.108),(0.042,0.042,0.032),0.03),      # chin
    ((0,-0.098,-0.082),(0.044,0.036,0.030),0.025),     # muzzle
    ((0,-0.045,0.058),(0.128,0.100,0.096),0.045),      # forehead
    ((0,-0.138,-0.050),(0.0175,0.0165,0.0150),0.014),  # button nose
]
def head_sdf(p, sockets=True):
    d=None
    for c,r,k in PARTS:
        dd=sd_ell(p,np.array(HC)+np.array(c),r)
        d=dd if d is None else smin(d,dd,k)
    if sockets:
        for sx in (1,-1):
            c=np.array(EYE_CENTERS[sx]); r=np.array((ER*1.10,ER*EYE_Y*1.08,ER*1.15*1.09))
            d=smax(d,-sd_ell(p,c,r),0.014)
    return d
def radial_project(dirs, sockets=True):
    dirs=dirs/np.linalg.norm(dirs,axis=1)[:,None]; hc=np.array(HC)
    ts=np.linspace(0.40,0.01,391); found=np.zeros(len(dirs)); hit=np.zeros(len(dirs),bool)
    for t in ts:
        ins=head_sdf(hc+dirs*t,sockets)<0
        new=ins&~hit; found[new]=t; hit|=ins
    lo=found.copy(); hi=found+0.001
    for _ in range(14):
        mid=(lo+hi)/2; ins=head_sdf(hc+dirs*mid[:,None],sockets)<0
        lo=np.where(ins,mid,lo); hi=np.where(ins,hi,mid)
    return hc+dirs*((lo+hi)/2)[:,None]
# eye centers: front of eye a hair in front of the un-socketed surface
EYE_CENTERS={}
for sx in (1,-1):
    x=EYE_X*sx; z=HC.z+EYE_Z
    ys=np.linspace(-0.25,0.0,400); pts=np.stack([np.full(400,x),ys,np.full(400,z)],1)
    EYE_CENTERS[sx]=(0,0,0)
    d_=head_sdf(pts,sockets=False); y_s=ys[np.argmax(d_<0)]
    EYE_CENTERS[sx]=(x, y_s-0.009+ER*EYE_Y*1.06, z)
def head_shape(P):
    return radial_project(np.asarray(P,float))
def make_sphere(name, seg, rings, rad=1.0):
    me=bpy.data.meshes.new(name); bm=bmesh.new()
    bmesh.ops.create_uvsphere(bm,u_segments=seg,v_segments=rings,radius=rad); bm.to_mesh(me); bm.free()
    me.shade_smooth(); return link(bpy.data.objects.new(name,me))
head=make_sphere('Head',88,62)
co=np.array([v.co for v in head.data.vertices]); co=head_shape(co)
for v,c in zip(head.data.vertices,co): v.co=c
vg=head.vertex_groups.new(name='eyes')
for v in head.data.vertices:
    dmin=min((v.co-Vector(EYE_CENTERS[s])).length for s in (1,-1))
    w=max(0.0,min(1.0,(0.075-dmin)/0.02))
    if w>0: vg.add([v.index],w,'REPLACE')
sm_=head.modifiers.new('sm','SMOOTH'); sm_.factor=0.5; sm_.iterations=4
sm2=head.modifiers.new('sm2','SMOOTH'); sm2.factor=0.8; sm2.iterations=14; sm2.vertex_group='eyes'
apply_mods(head)
assign(head,M['skin'])
hb=bvh(head)
def surf(x,z,front=True):
    o=Vector((x,-0.5 if front else 0.5,z)); hit=hb.ray_cast(o,Vector((0,1 if front else -1,0)))
    return hit[0],hit[1]
def surf_dir(dvec,off=0.0):
    dvec=Vector(dvec).normalized(); o=HC+dvec*0.5; hit=hb.ray_cast(o,-dvec)
    return hit[0]+hit[1]*off, hit[1]

# ears
for sx in (1,-1):
    p,n=surf_dir((sx,0.08,-0.12))
    ear=make_sphere('Ear_'+('L' if sx>0 else 'R'),16,12)
    cc=np.array([v.co for v in ear.data.vertices])
    cc[:,0]=np.where(cc[:,0]*sx>0, cc[:,0]-0.55*sx*np.exp(-((cc[:,1]**2+cc[:,2]**2)/0.35)) , cc[:,0])
    cc*=np.array([0.011,0.020,0.032])
    for v,c in zip(ear.data.vertices,cc): v.co=c
    ear.location=p+Vector((-0.006*sx,0.005,0)); ear.rotation_euler=(0.0,0.0,math.radians(-18*sx))
    assign(ear,M['skin'])

# ---------------- eyes ----------------
IRIS_ANG=math.radians(40); IRIS_R=ER*math.sin(IRIS_ANG)
M['iris']=iris_mat()
eye_objs=[]
for sx in (1,-1):
    side='L' if sx>0 else 'R'
    center=Vector(EYE_CENTERS[sx])
    empty=bpy.data.objects.new('Eye_'+side,None); link(empty); empty.location=center
    empty.scale=EYE_SCALE; empty.rotation_euler=(0,0,math.radians(-4*sx))
    # eyeball (pole forward)
    eb=make_sphere('Eyeball_'+side,24,20,ER)
    eb.data.transform(Matrix.Rotation(math.radians(90),4,'X'))
    me=eb.data; me.materials.append(M['iris'])
    for v in me.vertices:
        c=v.co.normalized(); a=math.acos(max(-1,min(1,-c.y)))
        if a<IRIS_ANG: v.co*= 1-0.05*(1-(a/IRIS_ANG)**2)
    ea=me.attributes.new('eye_local','FLOAT_VECTOR','POINT'); ea.data.foreach_set('vector',[c for v in me.vertices for c in v.co])
    eb.parent=empty
    co_=make_sphere('Cornea_'+side,24,24,ER*1.012); co_.data.transform(Matrix.Rotation(math.radians(90),4,'X'))
    for v in co_.data.vertices:
        c=v.co.normalized(); a=math.acos(max(-1,min(1,-c.y)))
        A_=math.radians(46)
        v.co=v.co.normalized()*ER*((1.0+0.075*(1-(a/A_)**2)) if a<A_ else 1.0)
    bm=bmesh.new(); bm.from_mesh(co_.data)
    kill=[v for v in bm.verts if math.acos(max(-1,min(1,-v.co.normalized().y)))>math.radians(47)]
    bmesh.ops.delete(bm,geom=kill,context='VERTS'); bm.to_mesh(co_.data); bm.free()
    assign(co_,M['cornea']); co_.parent=empty
    # catchlights
    for (lx,lz,rr) in ((0.17,0.22,0.0062),(-0.18,-0.20,0.0028)):
        bpy.ops.mesh.primitive_circle_add(vertices=16,radius=rr,fill_type='NGON')
        cl=bpy.context.active_object; cl.name='Catch_'+side
        cl.data.transform(Matrix.Rotation(math.radians(90),4,'X'))
        dirv=Vector((lx*sx*-1 if False else lx,-1,lz)).normalized()
        cl.location=dirv*ER*1.10; cl.rotation_euler=(0,0,0)
        assign(cl,M['catch']); cl.parent=empty
    # upper lid shell
    ld=make_sphere('Lid_'+side,40,32,ER*1.13); ld.data.transform(Matrix.Rotation(math.radians(90),4,'X'))
    bm=bmesh.new(); bm.from_mesh(ld.data)
    def lidcut(v):
        xo=v.co.x*sx/ER   # outward
        zc=ER*(0.66-0.14*xo)
        return v.co.z>zc and v.co.y<ER*0.30
    kill=[v for v in bm.verts if not lidcut(v)]
    bmesh.ops.delete(bm,geom=kill,context='VERTS'); bm.to_mesh(ld.data); bm.free()
    sol=ld.modifiers.new('sol','SOLIDIFY'); sol.thickness=0.007; sol.offset=-1
    assign(ld,M['skin']); ld.parent=empty
    if False:
     lo=make_sphere('LidLow_'+side,40,32,ER*1.12); lo.data.transform(Matrix.Rotation(math.radians(90),4,'X'))
    if False:
     bm=bmesh.new(); bm.from_mesh(lo.data)
     kill=[v for v in bm.verts if not (v.co.z<-ER*(0.70+0.06*(v.co.x*sx/ER)) and v.co.y<ER*0.30)]
     bmesh.ops.delete(bm,geom=kill,context='VERTS'); bm.to_mesh(lo.data); bm.free()
    # lash line along lid lower edge (front part)
    pts=[]
    for i in range(15):
        t=i/14; ang=math.radians(-62+124*t)  # around forward axis, x from inner to outer
        x=math.sin(ang)*ER*1.15*sx; 
        xo=x*sx/ER; zc=ER*(0.66-0.14*xo)
        y=-math.sqrt(max((ER*1.15)**2-x*x-zc*zc,1e-8))
        pts.append(Vector((x,y,zc)))
    if sx<0: pts=pts  # inner->outer already by sign
    W=[0.0030+0.0030*(i/14)**1.3 for i in range(15)]; T=[0.0042]*15
    N=[ (p.normalized()) for p in pts]
    ll=sweep('LashLine_'+side,pts,N,T,W,K=10,flat=1.0); assign(ll,M['lash']); ll.parent=empty
    # two lashes at outer corner
    for j,(up,out) in enumerate(((0.9,0.8),(0.6,1.0))):
        base=pts[-1-j*2]; 
        dirv=Vector((out*sx,-0.3,up)).normalized()
        P=[base,base+dirv*0.005,base+dirv*0.010+Vector((0.002*sx,0,-0.001))]
        lsh=sweep('Lash_%s%d'%(side,j),P,[Vector((0,-1,0))]*3,[0.0022,0.0016,0.0006],[0.0012]*3,K=6,flat=1.0)
        assign(lsh,M['lash']); lsh.parent=empty
    eye_objs.append(empty)

# brows
for sx in (1,-1):
    pts=[];N=[]
    for i in range(10):
        t=i/9; x=(0.022+0.085*t)*sx; z=HC.z+0.063+0.016*math.sin(math.pi*t*0.85)-0.006*t
        p,n=surf(x,z); pts.append(p+n*0.0025); N.append(n)
    W=[(0.012-0.005*t)*min(1,0.6+t*4) for t in np.linspace(0,1,10)]; W[-1]=0.004
    T=[0.0035]*10
    b=sweep('Brow_'+('L' if sx>0 else 'R'),pts,N,W,T,K=10,flat=0.4); assign(b,M['brow'])

# mouth (small closed smile)
pts=[];N=[]
for i in range(11):
    t=i/10; x=-0.020+0.040*t; z=HC.z-0.085+0.0075*(2*t-1)**2
    p,n=surf(x,z); pts.append(p+n*0.0008); N.append(n)
W=[0.0016+0.0016*math.sin(math.pi*t) for t in np.linspace(0,1,11)]
mo=sweep('Mouth',pts,N,W,[0.0012]*11,K=8,flat=1.0); assign(mo,M['mouth'])

# ---------------- body (skin modifier) ----------------
V=[];E=[];R=[]
def add(p,r,parent=None):
    V.append(p);R.append(r); i=len(V)-1
    if parent is not None: E.append((parent,i))
    return i
pel=add((0,0.008,0.87),(0.122,0.090))
wst=add((0,0.004,0.99),(0.094,0.070),pel)
che=add((0,-0.004,1.10),(0.108,0.080),wst)
uch=add((0,0.004,1.195),(0.112,0.074),che)
nkb=add((0,0.010,1.262),(0.064,0.058),uch)
nkt=add((0,0.012,1.39),(0.049,0.047),nkb)
for sx in (1,-1):
    sh=add((0.145*sx,0.008,1.218),(0.046,0.046),uch)
    el=add((0.240*sx,0.022,0.985),(0.034,0.034),sh)
    wr=add((0.292*sx,0.004,0.775),(0.026,0.022),el)
    hp=add((0.082*sx,0.008,0.83),(0.084,0.084),pel)
    kn=add((0.082*sx,0.004,0.465),(0.050,0.050),hp)
    cf=add((0.082*sx,0.018,0.345),(0.056,0.056),kn)
    an=add((0.082*sx,0.010,0.095),(0.030,0.030),cf)
    ft=add((0.082*sx,-0.075,0.035),(0.030,0.026),an)
body=mesh_from('Body',V,[],smooth=False)
me=body.data; me.from_pydata  # placeholder
me.clear_geometry(); me.from_pydata([tuple(v) for v in V],E,[])
sk=body.modifiers.new('skin','SKIN'); sk.branch_smoothing=0.6; sk.use_smooth_shade=True
for i,r in enumerate(R): me.skin_vertices[0].data[i].radius=r
me.skin_vertices[0].data[0].use_root=True
ss=body.modifiers.new('sub','SUBSURF'); ss.levels=2
apply_mods(body)
set_active(body)
rm=body.modifiers.new('rm','REMESH'); rm.mode='VOXEL'; rm.voxel_size=0.006; rm.use_smooth_shade=True
sm=body.modifiers.new('sm','SMOOTH'); sm.iterations=12; sm.factor=0.8
apply_mods(body)
assign(body,M['skin'])

# hands: metaballs
def hand(sx):
    mb=bpy.data.metaballs.new('HandMB'); mb.resolution=0.003; mb.render_resolution=0.003; mb.threshold=0.6
    ob=bpy.data.objects.new('Hand_tmp',mb); link(ob)
    W=Vector((0.292*sx,0.004,0.775)); E_=Vector((0.240*sx,0.022,0.985))
    dA=(W-E_).normalized(); inward=Vector((-sx,0,0)); fwd=Vector((0,-1,0))
    def q_for(dirv):
        return Vector((1,0,0)).rotation_difference(dirv.normalized())
    def el(kind,co,rad,dirv=None,size=None):
        e=mb.elements.new(); e.type=kind; e.co=co; e.radius=rad
        if dirv is not None: e.rotation=q_for(dirv)
        if size: 
            if kind=='CAPSULE': e.size_x=size
            else: e.size_x,e.size_y,e.size_z=size
        return e
    el('CAPSULE',W+dA*0.012,0.031,dA,0.014)
    pc=W+dA*0.060
    e_=el('ELLIPSOID',pc,0.085,None,(0.42,0.85,0.80)); e_.stiffness=3.0
    kn=W+dA*0.098
    for i,(yy,ln) in enumerate(((-0.024,0.058),(-0.008,0.066),(0.008,0.064),(0.023,0.054))):
        base=kn+Vector((0,yy,0))+dA*(-0.006*abs(yy)/0.024)
        d1=(dA+inward*0.15+Vector((0,yy*0.6,0))).normalized()
        el('CAPSULE',base+d1*ln*0.25,0.0165,d1,ln*0.22).stiffness=2.6
        d2=(d1+inward*0.40).normalized()
        el('CAPSULE',base+d1*ln*0.5+d2*ln*0.20,0.0150,d2,ln*0.18).stiffness=2.6
    tb=W+dA*0.040+Vector((0,-0.036,0))+inward*0.010
    dt=(dA*0.6+fwd*0.45+inward*0.45).normalized()
    el('CAPSULE',tb+dt*0.020,0.0175,dt,0.018)
    el('CAPSULE',tb+dt*0.050,0.0150,dt,0.014)
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get(); me=bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    h=bpy.data.objects.new('Hand_'+('L' if sx>0 else 'R'),me); link(h)
    bpy.data.objects.remove(ob); me.shade_smooth()
    sm=h.modifiers.new('sm','SMOOTH'); sm.iterations=4; apply_mods(h)
    h.data.transform(Matrix.Translation(W)@Matrix.Scale(1.12,4)@Matrix.Translation(-W))
    assign(h,M['skin']); return h
hands=[hand(1),hand(-1)]

exec(open(os.path.join(os.path.dirname(__file__),'build_hair.py')).read())
exec(open(os.path.join(os.path.dirname(__file__),'build_outfit.py')).read())
if os.environ.get('FINAL'): exec(open(os.path.join(os.path.dirname(__file__),'finalize.py')).read())
for o in sorted(bpy.data.objects,key=lambda o:o.name):
    if o.type=='MESH' and os.environ.get('COUNT'): print('TRIS',o.name,tris(o))
exec(open(os.path.join(os.path.dirname(__file__),'render.py')).read())
