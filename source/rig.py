# ---------------- rig + facial shapes + pose + export ----------------
import sys, os, math, json, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
import lib; importlib.reload(lib)
from lib import *
ROOT='/workspace/character'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/source/character_master.blend')
scn=bpy.context.scene
DZ=-0.08; K2=(0.83-0.20+DZ)/(0.83-0.20)
def lz(z): return z if z<0.20 else (0.20+(z-0.20)*K2 if z<0.83 else z+DZ)
HCn=Vector((0,0,1.432+DZ))
OBJ={o.name:o for o in bpy.data.objects if o.type=='MESH'}
body=OBJ['CH_Body']; hair=OBJ['CH_Hair']; clothes=OBJ['CH_Clothes']; shoes=OBJ['CH_Shoes']; cornea=OBJ['CH_EyeCornea']; catch=OBJ['CH_EyeCatchlight']
def coords(o):
    a=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get('co',a); return a.reshape(-1,3)
def part(o):
    if 'part' not in o.data.attributes: return np.full(len(o.data.vertices),35)
    a=np.empty(len(o.data.vertices),dtype=np.int32); o.data.attributes['part'].data.foreach_get('value',a); return a
BC=coords(body); BP=part(body)
eye_c={}
for sx in (1,-1):
    m=(BP==3)&(BC[:,0]*sx>0); eye_c[sx]=Vector(BC[m].mean(0))
print('EYES',eye_c)
# ---------------- skeleton ----------------
def smooth01(a,b,x): t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
J={}
J['Hips']=((0,0.008,0.80),(0,0.006,0.90),None)
J['Spine']=((0,0.006,0.90),(0,0.000,1.01),'Hips')
J['Chest']=((0,0.000,1.01),(0,0.004,1.10),'Spine')
J['UpperChest']=((0,0.004,1.10),(0,0.010,1.185),'Chest')
J['Neck']=((0,0.010,1.185),(0,0.012,1.255),'UpperChest')
J['Head']=((0,0.012,1.255),(0,0.012,1.45),'Neck')
for sx,S in ((1,'Left'),(-1,'Right')):
    sh=Vector((0.145*sx,0.008,1.222+DZ)); el=Vector((0.240*sx,0.022,0.985+DZ)); W0=Vector((0.292*sx,0.004,0.775))
    W=W0+Vector((0,0,DZ))
    J[S+'Shoulder']=((0.022*sx,0.004,1.165),tuple(sh),'UpperChest')
    J[S+'UpperArm']=(tuple(sh),tuple(el),S+'Shoulder')
    J[S+'LowerArm']=(tuple(el),tuple(W),S+'UpperArm')
    # hand frame (same math as build.py)
    E_=Vector((0.268*sx,0.014,0.885)); dA=(W0-E_).normalized(); inw=Vector((-sx,0,0)); inw=(inw-dA*inw.dot(dA)).normalized()
    fwd=dA.cross(inw).normalized()
    if fwd.y>0: fwd=-fwd
    th_=math.radians(40); inw=(inw*math.cos(th_)-fwd*math.sin(th_)).normalized(); fwd=dA.cross(inw).normalized()
    if fwd.y>0: fwd=-fwd
    def L(u,v,w): return W0+dA*u+fwd*v+inw*w
    def X(p): q=W0+(p-W0)*1.22; return tuple(q+Vector((0,0,DZ)))
    J[S+'Hand']=(tuple(W),X(L(0.060,0,0.002)),S+'LowerArm')
    J[S+'_palm']=tuple(inw)  # stored for pose
    for fname,(v,ln) in zip(('Index','Middle','Ring','Little'),((-0.0285,0.062),(-0.0095,0.070),(0.0095,0.066),(0.0285,0.054))):
        pos=L(0.056-0.010*abs(v)/0.028,v,0.002); ang=0; pts=[pos]
        for fr,bend in ((0.42,0.14),(0.32,0.24),(0.26,0.22)):
            ang+=bend; d=(dA*math.cos(ang)+inw*math.sin(ang)+fwd*(-v)*0.5).normalized(); pos=pos+d*ln*fr; pts.append(pos)
        par=S+'Hand'
        for k,seg in enumerate(('Proximal','Intermediate','Distal')):
            nm=S+fname+seg; J[nm]=(X(pts[k]),X(pts[k+1]),par); par=nm
    tb=L(0.018,-0.028,0.008); dt=(dA*0.45+fwd*0.75+inw*0.45).normalized(); dt2=(dA*0.80+fwd*0.30+inw*0.50).normalized()
    t1=tb+dt*0.030; t2=t1+dt2*0.026; t3=t2+dt2*0.018
    J[S+'ThumbProximal']=(X(tb),X(t1),S+'Hand'); J[S+'ThumbIntermediate']=(X(t1),X(t2),S+'ThumbProximal'); J[S+'ThumbDistal']=(X(t2),X(t3),S+'ThumbIntermediate')
    hip=(0.084*sx,0.008,lz(0.83)); knee=(0.082*sx,0.004,lz(0.465)); ank=(0.082*sx,0.010,0.095)
    J[S+'UpperLeg']=(hip,knee,'Hips'); J[S+'LowerLeg']=(knee,ank,S+'UpperLeg')
    J[S+'Foot']=(ank,(0.082*sx,-0.085,0.030),S+'LowerLeg'); J[S+'Toes']=((0.082*sx,-0.085,0.030),(0.082*sx,-0.165,0.028),S+'Foot')
    ec=eye_c[sx]; J[S+'Eye']=(tuple(ec),tuple(ec+Vector((0,-0.03,0))),'Head')
PB=json.load(open(ROOT+'/export/ponytail_bones.json'))['bones']
J['Pony_0']=(tuple(PB['Pony_0']['head']),tuple(PB['Pony_0']['tail']),'Head')
J['Pony_1']=(tuple(PB['Pony_1']['head']),tuple(PB['Pony_1']['tail']),'Pony_0')
J['Pony_2']=(tuple(PB['Pony_2']['head']),tuple(PB['Pony_2']['tail']),'Pony_1')
PALM={'Left':Vector(J.pop('Left_palm')),'Right':Vector(J.pop('Right_palm'))}

arm_d=bpy.data.armatures.new('CH_Armature'); arm=bpy.data.objects.new('CH_Armature',arm_d); link(arm)
set_active(arm); bpy.ops.object.mode_set(mode='EDIT')
order=list(J.keys())
for n in order:
    h,t,p=J[n]; eb=arm_d.edit_bones.new(n); eb.head=Vector(h); eb.tail=Vector(t)
for n in order:
    h,t,p=J[n]; eb=arm_d.edit_bones[n]
    if p: eb.parent=arm_d.edit_bones[p]; eb.use_connect=(Vector(arm_d.edit_bones[p].tail)-Vector(h)).length<1e-5 and not n.endswith('Eye')
    d=(eb.tail-eb.head).normalized()
    eb.align_roll(Vector((0,0,1)) if abs(d.y)>0.7 else Vector((0,-1,0)))
bpy.ops.object.mode_set(mode='OBJECT')
DEF=[n for n in order]
print('BONES',len(DEF))

# ---------------- weights ----------------
def segdist(P,a,b):
    a=np.array(a); b=np.array(b); ab=b-a; t=np.clip(((P-a)@ab)/max(ab@ab,1e-12),0,1)
    return np.linalg.norm(P-(a+t[:,None]*ab),axis=1)
TORSO=['Hips','Spine','Chest','UpperChest','Neck','Head']
def side_bones(S,kind):
    if kind=='arm': return [S+'Shoulder',S+'UpperArm',S+'LowerArm',S+'Hand']
    if kind=='leg': return [S+'UpperLeg',S+'LowerLeg',S+'Foot',S+'Toes']
    if kind=='fing': return [n for n in order if n.startswith(S) and any(f in n for f in ('Thumb','Index','Middle','Ring','Little'))]
def dist_weights(P,cands,masks,pw):
    D=np.stack([segdist(P,J[c][0],J[c][1]) for c in cands],1)
    Wt=1.0/np.maximum(D,0.004)**pw
    Wt*=np.stack([masks[c] for c in cands],1)
    s=Wt.sum(1,keepdims=True); s[s==0]=1
    return Wt/s
def body_weights(P,PT):
    n=len(P); x=P[:,0]; z=P[:,2]; ax=np.abs(x)
    cands=TORSO+side_bones('Left','arm')+side_bones('Right','arm')+side_bones('Left','leg')+side_bones('Right','leg')
    one=np.ones(n); M={}
    M['Hips']=smooth01(0.55,0.70,z); M['Spine']=smooth01(0.78,0.86,z); M['Chest']=smooth01(0.88,0.96,z); M['UpperChest']=smooth01(0.98,1.05,z)
    M['Neck']=smooth01(1.10,1.16,z); M['Head']=smooth01(1.22,1.25,z)
    for sx,S in ((1,'Left'),(-1,'Right')):
        sd=smooth01(-0.01,0.01,x*sx)
        armm=np.where(z>1.06,smooth01(0.10,0.15,ax),smooth01(0.13,0.175,ax))*sd
        M[S+'Shoulder']=smooth01(0.03,0.08,ax)*smooth01(1.04,1.10,z)*sd
        M[S+'UpperArm']=armm; M[S+'LowerArm']=armm*smooth01(0.95,0.85,z); M[S+'Hand']=armm*smooth01(0.76,0.70,z)
        legm=smooth01(-0.015,0.015,x*sx)*smooth01(0.86,0.80,z)*(1-smooth01(0.16,0.20,ax)*smooth01(0.70,0.80,z))
        for b in side_bones(S,'leg'): M[b]=legm
    Wt=dist_weights(P,cands,M,4)
    out={c:Wt[:,i] for i,c in enumerate(cands)}
    # hands: hand + fingers (+ forearm near wrist)
    for sx,S in ((1,'Left'),(-1,'Right')):
        hm=(PT==10)&(x*sx>0)
        if not hm.any(): continue
        hc=[S+'LowerArm',S+'Hand']+side_bones(S,'fing')
        Ph=P[hm]; Mh={c:np.ones(hm.sum()) for c in hc}
        Mh[S+'LowerArm']=0.25*np.ones(hm.sum())
        Wh=dist_weights(Ph,hc,Mh,8)
        for c in cands: out[c][hm]=0
        for i,c in enumerate(hc):
            out.setdefault(c,np.zeros(n)); out[c][hm]=Wh[:,i]
    return out
def smooth_weights(o,Wd,mask,it=4,fac=0.5):
    me=o.data; n=len(me.vertices); E=np.empty(len(me.edges)*2,dtype=np.int64); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2)
    E=E[mask[E[:,0]]&mask[E[:,1]]]
    deg=np.bincount(E.ravel(),minlength=n).astype(float); deg[deg==0]=1
    for k in Wd:
        w=Wd[k]
        for _ in range(it):
            acc=np.bincount(E[:,0],weights=w[E[:,1]],minlength=n)+np.bincount(E[:,1],weights=w[E[:,0]],minlength=n)
            w=np.where(mask,w*(1-fac)+fac*acc/deg,w)
        Wd[k]=w
    s=sum(Wd.values()); s[s==0]=1
    for k in Wd: Wd[k]=Wd[k]/s
def write_weights(o,Wd,clear=True,topk=4):
    names=list(Wd.keys()); A=np.stack([Wd[k] for k in names],1)
    idx=np.argsort(-A,1)[:,:topk]
    groups={}
    for k in names: groups[k]=o.vertex_groups.get(k) or o.vertex_groups.new(name=k)
    for i in range(A.shape[0]):
        row=A[i,idx[i]]; s=row.sum()
        if s<=0: continue
        for j,w in zip(idx[i],row/s):
            if w>0.01: groups[names[j]].add([i],float(w),'REPLACE')

# body
P=BC; PT=BP; n=len(P)
Wd=body_weights(P,PT)
for k in DEF: Wd.setdefault(k,np.zeros(n))
headparts=np.isin(PT,[1,2,4,5,6,7,8])
for k in Wd: Wd[k][headparts|(PT==3)]=0
Wd['Head'][headparts]=1
for sx,S in ((1,'Left'),(-1,'Right')): Wd[S+'Eye'][(PT==3)&(P[:,0]*sx>0)]=1
smooth_weights(body,Wd,(PT==9)|(PT==10),it=5,fac=0.5)
elbB=(PT==9)&(np.abs(P[:,0])>0.18)&(P[:,2]>0.82)&(P[:,2]<0.98)
smooth_weights(body,Wd,elbB,it=8,fac=0.5)
BW=Wd
write_weights(body,{k:v for k,v in Wd.items() if v.max()>0})
for o_,sxm in ((cornea,None),(catch,None)):
    C=coords(o_)
    Wc={'LeftEye':(C[:,0]>0).astype(float),'RightEye':(C[:,0]<=0).astype(float)}
    write_weights(o_,Wc)
# clothes: transfer from body surface (parts 9,10)
bm=bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
src=[f for f in bm.faces if all(PT[v.index] in (9,10) for v in f.verts)]
polys=[[v.index for v in f.verts] for f in src]
bvh_b=BVHTree.FromPolygons([tuple(v) for v in P],polys)
bm.free()
def transfer(o,mask=None):
    C=coords(o); n=len(C); out={k:np.zeros(n) for k in BW}
    for i,c in enumerate(C):
        if mask is not None and not mask[i]: continue
        loc,nrm,fi,d=bvh_b.find_nearest(Vector(c))
        if fi is None: continue
        vs=polys[fi]; ws=np.array([1.0/max((Vector(P[v])-loc).length,1e-4) for v in vs]); ws/=ws.sum()
        for k in BW:
            out[k][i]=sum(BW[k][v]*w for v,w in zip(vs,ws))
    return out
CP=part(clothes); CC=coords(clothes)
Wcl=transfer(clothes,mask=~np.isin(CP,[33]))
# socks: legs only
for sx,S in ((1,'Left'),(-1,'Right')):
    m=(CP==33)&(CC[:,0]*sx>0)
    for k in Wcl: Wcl[k][m]=0
    z=CC[m,2]; Wcl[S+'Foot'][m]=smooth01(0.13,0.07,z); Wcl[S+'LowerLeg'][m]=1-Wcl[S+'Foot'][m]
smooth_weights(clothes,Wcl,np.ones(len(CC),bool),it=2,fac=0.4)
elb=(np.abs(CC[:,0])>0.17)&(CC[:,2]>0.80)&(CC[:,2]<1.00)
smooth_weights(clothes,Wcl,elb,it=14,fac=0.5)
write_weights(clothes,{k:v for k,v in Wcl.items() if v.max()>0})
SC=coords(shoes)
write_weights(shoes,{'LeftFoot':(SC[:,0]>0).astype(float),'RightFoot':(SC[:,0]<=0).astype(float)})
# hair: groups exist (Head, Pony_*); tie/flyaways and any unweighted -> Head
HP=part(hair); hv=hair.vertex_groups.get('Head') or hair.vertex_groups.new(name='Head')
for v in hair.data.vertices:
    tot=sum(g.weight for g in v.groups)
    if tot<1e-4: hv.add([v.index],1.0,'REPLACE')
print('WEIGHTS done')

# ---------------- facial shapes ----------------
def head_tree(Pts):
    bm=bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
    pl=[[v.index for v in f.verts] for f in bm.faces if all(BP[v.index]==1 for v in f.verts)]; bm.free()
    return BVHTree.FromPolygons([tuple(v) for v in Pts],pl)
Mz=HCn.z-0.088
def g2(P,cx,cz,r): return np.exp(-((P[:,0]-cx)**2+(P[:,2]-cz)**2)/r**2)
def eye_rot(Pts,sx,ang):
    c=np.array(eye_c[sx]); sc=np.array([1.0,0.76,1.15]); a=math.radians(-4*sx)
    Rz=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
    q=((Pts-c)@Rz)/sc   # to local
    t=math.radians(ang); Rx=np.array([[1,0,0],[0,math.cos(t),-math.sin(t)],[0,math.sin(t),math.cos(t)]])
    q=q@Rx.T
    return (q*sc)@Rz.T+c
def lid_close(Pts,sx,phic,is_lid):
    c=np.array(eye_c[sx]); sc=np.array([1.0,0.76,1.15]); a=math.radians(-4*sx)
    Rz=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
    q=((Pts-c)@Rz)/sc
    ER_=0.0465; xo=np.clip(q[:,0]*sx/ER_,-1,1)
    phie=np.arcsin(np.clip((0.66-0.14*xo)/1.13,-1,1))
    if is_lid.any():
        phi0=np.arctan2(q[:,2],-q[:,1]); edges=np.linspace(-1,1,29); cen=0.5*(edges[1:]+edges[:-1]); tab=[]
        for i in range(28):
            mm=is_lid&(xo>=edges[i])&(xo<edges[i+1])
            tab.append(phi0[mm].min() if mm.sum()>0 else np.nan)
        tab=np.array(tab); ok=~np.isnan(tab)
        if ok.sum()>3:
            tab=np.interp(cen,cen[ok],tab[ok]); tab=np.convolve(np.pad(tab,1,mode='edge'),[0.25,0.5,0.25],'valid')
            phie=np.interp(xo,cen,tab)
    r_=np.sqrt(q[:,1]**2+q[:,2]**2); phi=np.arctan2(q[:,2],-q[:,1])
    phit=math.radians(112)
    pc=phic if np.ndim(phic)==0 else phic
    newphi=np.where(is_lid, phit-(phit-phi)*(phit-pc)/np.maximum(phit-phie,1e-3), phi-(phie-pc))
    q2=q.copy(); q2[:,1]=-r_*np.cos(newphi); q2[:,2]=r_*np.sin(newphi)
    return (q2*sc)@Rz.T+c
Bl=BC.copy()
for sx in (1,-1):
    m=np.isin(BP,[4,5,6])&(BC[:,0]*sx>0)
    lid=BP[m]==4
    Bl[m]=np.where(lid[:,None],lid_close(BC[m],sx,math.radians(-46),lid),lid_close(BC[m],sx,math.radians(-38),lid))
# BigSmile
Sm=BC.copy()
front=smooth01(-0.02,-0.07,BC[:,1])
hm=(BP==1)
D=np.zeros_like(BC)
for sx in (1,-1):
    asym=1.15 if sx>0 else 1.0
    gc=g2(BC,0.058*sx,HCn.z-0.052,0.030)*asym
    D+=gc[:,None]*np.array([0.0020*sx,-0.005,0.0105])
    ex,ez=eye_c[sx].x,eye_c[sx].z
    gl=g2(BC,ex,ez-0.044,0.020)*asym
    D+=gl[:,None]*np.array([0,-0.003,0.0095])
    gm=g2(BC,0.026*sx,Mz+0.005,0.016)*(1.2 if sx>0 else 1.0)
    D+=gm[:,None]*np.array([0.009*sx,-0.002,0.0085])
jaw=smooth01(Mz+0.002,Mz-0.022,BC[:,2])*np.exp(-(BC[:,0]/0.055)**2)
D[:,2]-=0.015*jaw
D[:,1]-=0.002*jaw
D*=front[:,None]
Sm[hm]=BC[hm]+D[hm]
# brows up + arched, slight asymmetry
for sx in (1,-1):
    m=(BP==7)&(BC[:,0]*sx>0)
    arch=np.exp(-((np.abs(BC[m,0])-0.062)/0.028)**2)
    Sm[m,2]+=0.0065+0.0045*arch+(0.003 if sx>0 else 0.0)
    Sm[m,1]-=0.001
    # lids squint slightly + follow
    ml=np.isin(BP,[4,5,6])&(BC[:,0]*sx>0)
    ph_e=math.asin(0.66/1.13); Sm[ml]=lid_close(BC[ml],sx,ph_e-math.radians(12 if sx>0 else 9),BP[ml]==4)
# mouth line -> upper lip edge of grin
tree_s=head_tree(Sm); tree_n=head_tree(BC)
def surf_y(tree,x,z):
    h=tree.ray_cast(Vector((x,-0.5,z)),Vector((0,1,0)))
    return h[0].y if h[0] is not None else None
def ztop(u): return Mz+0.0060+0.0115*u*u+0.0025*u
def zl(u): return Mz+0.0065*u*u+0.0045*u**8+0.0015*max(0,u)
m=np.where(BP==8)[0]
for i in m:
    x,y,z=BC[i]; u=max(-1,min(1,x/0.021)); xn=u*0.039+0.0012; zn=z+(ztop(u)-zl(u))
    y0=surf_y(tree_n,x,z); y1=surf_y(tree_s,xn,zn)
    Sm[i]=(xn,y+((y1-y0) if (y0 is not None and y1 is not None) else 0),zn)
# write shape keys on body
body.shape_key_add(name='Basis')
for nm,arr in (('Blink',Bl),('BigSmile',Sm)):
    k=body.shape_key_add(name=nm,from_mix=False); k.data.foreach_set('co',arr.ravel())
# mouth interior decal (hidden inside head at rest, opens with BigSmile)
NU,NV=25,9; mv=[];mf=[];uv=[];S_=[]
for j in range(NV):
    for i in range(NU):
        u=-1+2*i/(NU-1); vv=j/(NV-1)
        # neutral: collapsed along the mouth line, 6mm inside the skin
        xb=u*0.021; zb=zl(u); yb=surf_y(tree_n,xb,zb); yb=(yb if yb is not None else -0.13)+0.006
        mv.append((xb,yb,zb))
        x=u*0.039+0.0012; zt=ztop(u); depth=0.034*max(0.0,1-u*u)**0.75; z=zt-depth*(1-vv)
        ys=surf_y(tree_s,x,z); ys=(ys if ys is not None else -0.13)-0.0007
        S_.append((x,ys,z)); uv.append((0.5+0.5*u,vv))
for j in range(NV-1):
    for i in range(NU-1):
        a=j*NU+i; mf.append((a,a+1,a+NU+1,a+NU))
mo=mesh_from('CH_Mouth',mv,mf); ul=mo.data.uv_layers.new(name=body.data.uv_layers[0].name)
for poly in mo.data.polygons:
    for li in poly.loop_indices: ul.data[li].uv=uv[mo.data.loops[li].vertex_index]
mm=bpy.data.materials.new('M_Mouth'); mm.use_nodes=True; bsd=mm.node_tree.nodes['Principled BSDF']; bsd.inputs['Roughness'].default_value=0.45
tx=mm.node_tree.nodes.new('ShaderNodeTexImage'); tx.image=bpy.data.images.load(ROOT+'/textures/T_Mouth_BaseColor.png'); mm.node_tree.links.new(tx.outputs[0],bsd.inputs['Base Color'])
mo.data.materials.append(mm)
mo.shape_key_add(name='Basis'); mo.shape_key_add(name='Blink'); k=mo.shape_key_add(name='BigSmile'); k.data.foreach_set('co',np.array(S_).ravel())
a_=mo.data.attributes.new('part','INT','POINT'); a_.data.foreach_set('value',[13]*len(mv))
mo.vertex_groups.new(name='Head').add(list(range(len(mv))),1.0,'REPLACE')
bpy.ops.object.select_all(action='DESELECT'); mo.select_set(True); body.select_set(True); bpy.context.view_layer.objects.active=body; bpy.ops.object.join()
print('SHAPES done', [k.name for k in body.data.shape_keys.key_blocks])
# ---------------- bind ----------------
for o in (body,hair,clothes,shoes,cornea,catch):
    o.parent=arm; md=o.modifiers.new('Armature','ARMATURE'); md.object=arm
    for vg in o.vertex_groups:
        if vg.name not in arm_d.bones: o.vertex_groups.remove(vg)
exec(open(os.path.join(os.path.dirname(__file__),'pose.py')).read())
