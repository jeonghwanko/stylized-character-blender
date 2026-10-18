# ---------------- hair v3: volumetric SDF clumps -> marching cubes ----------------
import random, subprocess, time, json
random.seed(7)
HAIRDIR='/workspace/character/work/hair'
VENV_PY='/workspace/tools/hairenv/bin/python'
hair_objs=[]

def hair_mat3():
    m=mat('M_Hair',(0.95,0.62,0.18),rough=0.62,spec=0.35); nt=m.node_tree; b=nt.nodes['Principled BSDF']
    def A(name):
        a=nt.nodes.new('ShaderNodeAttribute'); a.attribute_name=name; return a.outputs['Fac']
    def MATH(op,a,b_=None,clamp=False):
        n=nt.nodes.new('ShaderNodeMath'); n.operation=op; n.use_clamp=clamp
        for k,v in enumerate((a,b_)):
            if v is None: continue
            if isinstance(v,(int,float)): n.inputs[k].default_value=v
            else: nt.links.new(v,n.inputs[k])
        return n.outputs[0]
    def MIX(fac,c1,c2):
        n=nt.nodes.new('ShaderNodeMix'); n.data_type='RGBA'; n.clamp_factor=True
        nt.links.new(fac,n.inputs[0]) if not isinstance(fac,(int,float)) else None
        for idx,c in ((6,c1),(7,c2)):
            if isinstance(c,tuple): n.inputs[idx].default_value=c
            else: nt.links.new(c,n.inputs[idx])
        return n.outputs[2]
    ht=A('h_t'); cav=A('h_cav'); pony=A('h_pony')
    cr=nt.nodes.new('ShaderNodeValToRGB'); r=cr.color_ramp
    r.elements[0].position=0.0; r.elements[0].color=(0.78,0.28,0.025,1)
    e=r.elements.new(0.40); e.color=(0.97,0.52,0.07,1)
    e=r.elements.new(0.72); e.color=(1.0,0.62,0.12,1)
    r.elements[-1].position=1.0; r.elements[-1].color=(1.0,0.78,0.34,1)
    nt.links.new(ht,cr.inputs[0])
    base=MIX(MATH('MULTIPLY',cav,0.75),cr.outputs[0],(0.56,0.20,0.025,1))
    geo=nt.nodes.new('ShaderNodeNewGeometry')
    vs=nt.nodes.new('ShaderNodeVectorMath'); vs.operation='SUBTRACT'; nt.links.new(geo.outputs['Position'],vs.inputs[0]); vs.inputs[1].default_value=tuple(HC)
    vn=nt.nodes.new('ShaderNodeVectorMath'); vn.operation='NORMALIZE'; nt.links.new(vs.outputs[0],vn.inputs[0])
    sp=nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(vn.outputs[0],sp.inputs[0])
    dot=nt.nodes.new('ShaderNodeVectorMath'); dot.operation='DOT_PRODUCT'; nt.links.new(vn.outputs[0],dot.inputs[0]); nt.links.new(geo.outputs['Normal'],dot.inputs[1])
    crest=MATH('POWER',MATH('MAXIMUM',dot.outputs['Value'],0.0),5.0)
    def band(x,c,w): return MATH('EXPONENT',MATH('MULTIPLY',MATH('POWER',MATH('DIVIDE',MATH('SUBTRACT',x,c),w),2.0),-1.0))
    hl_head=MATH('MULTIPLY',MATH('MULTIPLY',band(sp.outputs[2],0.74,0.075),crest),MATH('SUBTRACT',1.0,pony))
    sn=nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'],sn.inputs[0])
    nz=MATH('POWER',MATH('MAXIMUM',MATH('SUBTRACT',sn.outputs[2],MATH('MULTIPLY',sn.outputs[1],-0.3)),0.0),2.0)
    hl_pony=MATH('MULTIPLY',MATH('MULTIPLY',band(ht,0.34,0.14),nz),pony)
    hl=MATH('MULTIPLY',MATH('MAXIMUM',hl_head,hl_pony),MATH('SUBTRACT',1.0,cav),clamp=True)
    col=MIX(MATH('MULTIPLY',hl,0.70),base,(1.0,0.90,0.60,1))
    nt.links.new(col,b.inputs['Base Color'])
    b.inputs['Sheen Weight'].default_value=0.06; b.inputs['Sheen Tint'].default_value=(1,0.85,0.5,1)
    b.inputs['Anisotropic'].default_value=0.6
    return m
M['hair']=hair_mat3()

def dirv(phi_deg, elev):
    ph=math.radians(phi_deg); c=math.sqrt(max(0,1-elev*elev))
    return Vector((math.sin(ph)*c, -math.cos(ph)*c, elev))
def slerp(a,b,t):
    a=a.normalized(); b=b.normalized(); om=math.acos(max(-1,min(1,a.dot(b))))
    if om<1e-4: return a
    return (a*math.sin((1-t)*om)+b*math.sin(t*om))/math.sin(om)
def hairline(phi):
    a=abs(phi)
    pts=[(0,0.55),(50,0.42),(80,0.30),(95,0.16),(115,-0.22),(140,-0.52),(180,-0.66)]
    for (a0,e0),(a1,e1) in zip(pts,pts[1:]):
        if a0<=a<=a1: return e0+(e1-e0)*(a-a0)/(a1-a0)
    return pts[-1][1]
T_DIR=Vector((0,0.60,0.80)).normalized()
Tp,Tn=surf_dir(T_DIR,0.0)
TIE=Tp+Tn*0.026

# ---- grid ----
VOX=float(os.environ.get('HAIR_VOX','0.0025'))
LO=np.array([-0.215,-0.215,1.05]); HI=np.array([0.215,0.43,1.70])
NX,NY,NZ=[int(v) for v in np.ceil((HI-LO)/VOX)+1]
gx=LO[0]+np.arange(NX)*VOX; gy=LO[1]+np.arange(NY)*VOX; gz=LO[2]+np.arange(NZ)*VOX
F=np.full((NX,NY,NZ),0.05,np.float32)
t0=time.time()
hc=np.array(HC)
YY,ZZ=np.meshgrid(gy,gz,indexing='ij')
for i in range(NX):
    P=np.stack([np.full(YY.size,gx[i]),YY.ravel(),ZZ.ravel()],1)
    d=P-hc; dist=np.linalg.norm(d,axis=1); m_=dist<0.25
    if not m_.any(): continue
    Pm=P[m_]; dm=d[m_]; rr=dist[m_]
    hs=head_sdf(Pm,sockets=False)
    elev=dm[:,2]/np.maximum(rr,1e-6); phi=np.degrees(np.arctan2(dm[:,0],-dm[:,1]))
    hl=np.interp(np.abs(phi),[0,50,80,95,115,140,180],[0.55,0.42,0.30,0.16,-0.22,-0.52,-0.66])
    fill=smax(hs-0.0035,(hl+0.015-elev)*0.16,0.010)
    col=F[i].reshape(-1); col[m_]=fill.astype(np.float32); F[i]=col.reshape(NY,NZ)
print('HAIR fill',round(time.time()-t0,1))

SAMPLES=[]   # (center, T,B,N, rt,rw,rn, h_t, kind, axis_t)
def resample(P,RW,RN,NR,HT):
    P=np.asarray(P,float); seg=np.linalg.norm(np.diff(P,axis=0),axis=1); s=np.concatenate([[0],np.cumsum(seg)]); L=s[-1]
    out=[]; cur=0.0
    while cur<=L:
        f=lambda arr: np.array([np.interp(cur,s,np.asarray(arr)[:,k]) for k in range(np.asarray(arr).shape[1])])
        p=f(P); rw=np.interp(cur,s,RW); rn=np.interp(cur,s,RN); nr=f(NR); ht=np.interp(cur,s,HT)
        j=min(np.searchsorted(s,cur),len(P)-1); j0=max(j-1,0); j1=min(j0+1,len(P)-1)
        out.append((p,P[j1]-P[j0],rw,rn,nr,ht,cur/L))
        cur+=max(0.0012,0.33*min(rw,rn))
    return out
def add_clump(P,RW,RN,NR,HT,kind,k_blend,axis_t=None):
    global F
    smp=resample(P,RW,RN,NR,HT)
    cs=np.array([s[0] for s in smp]); rmax=max(max(s[2],s[3]) for s in smp)+0.004
    lo_i=np.clip(np.floor((cs.min(0)-rmax-k_blend-LO)/VOX).astype(int),0,None)
    hi_i=np.minimum(np.ceil((cs.max(0)+rmax+k_blend-LO)/VOX).astype(int)+1,[NX,NY,NZ])
    D=np.full(tuple(hi_i-lo_i),0.05,np.float32)
    for (p,tg,rw,rn,nr,ht,u) in smp:
        T_=Vector(tg).normalized(); N_=Vector(nr); N_=(N_-T_*N_.dot(T_)).normalized(); B_=T_.cross(N_)
        rt=max(rw,rn)*0.9
        r_=max(rw,rn,rt)+0.003
        a=np.clip(np.floor((p-r_-LO)/VOX).astype(int),lo_i,hi_i); b=np.clip(np.ceil((p+r_-LO)/VOX).astype(int)+1,lo_i,hi_i)
        if np.any(b<=a): continue
        X,Y,Z=np.meshgrid(gx[a[0]:b[0]]-p[0],gy[a[1]:b[1]]-p[1],gz[a[2]:b[2]]-p[2],indexing='ij')
        R3=np.array([rt,rw,rn])
        q0=(X*T_.x+Y*T_.y+Z*T_.z)/R3[0]; q1=(X*B_.x+Y*B_.y+Z*B_.z)/R3[1]; q2=(X*N_.x+Y*N_.y+Z*N_.z)/R3[2]
        k0=np.sqrt(q0*q0+q1*q1+q2*q2); k1=np.sqrt((q0/R3[0])**2+(q1/R3[1])**2+(q2/R3[2])**2)
        d=(k0*(k0-1)/np.maximum(k1,1e-9)).astype(np.float32)
        sub=D[a[0]-lo_i[0]:b[0]-lo_i[0],a[1]-lo_i[1]:b[1]-lo_i[1],a[2]-lo_i[2]:b[2]-lo_i[2]]
        np.minimum(sub,d,out=sub)
        SAMPLES.append((Vector(p),T_,B_,N_,rt,rw,rn,ht,kind,(axis_t(u) if axis_t else u)))
    sl=(slice(lo_i[0],hi_i[0]),slice(lo_i[1],hi_i[1]),slice(lo_i[2],hi_i[2]))
    F[sl]=smin(F[sl],D,k_blend).astype(np.float32)

def head_pt(d):
    p,n=surf_dir(d,0.0); return p,n

# --- pulled-back clumps: hairline -> tie ---
def back_clump(phi,e0,rmax,lift=1.0,jit=0.0,ht0=0.55):
    d0=dirv(phi,e0); R=40; P=[];RW=[];RN=[];NR=[];HT=[]
    for i in range(R):
        t=i/(R-1)
        dd=slerp(d0,T_DIR,t*0.97)
        p,n=head_pt(dd)
        grow=smoothstep(0.0,0.22,t)
        rw=rmax*(0.62+0.38*math.sin(math.pi*min(1,t*1.5)))*(1-0.62*t**1.3)
        rw=rw*(0.55+0.45*grow)
        rn=(0.55*rw+0.004)*(0.35+0.65*grow)
        h=(rn*0.42+0.004)*lift + 0.004*t
        P.append(p+n*h); RW.append(rw); RN.append(rn); NR.append(n); HT.append(ht0+jit-0.25*t**2)
    add_clump(P,RW,RN,NR,HT,0,0.0045)
back_phis=[-162,-136,-112,-90,-70,-52,52,70,90,112,136,162,180]
for ph in back_phis:
    back_clump(ph,hairline(ph)+0.02,0.036 if abs(ph)>60 else 0.032,jit=random.uniform(-0.08,0.08))
# second, inner layer offset in phase (fills between, slightly lower)
for ph in [-149,-124,-101,-80,-61,61,80,101,124,149,171,-171]:
    back_clump(ph,hairline(ph)+0.06,0.028,lift=0.55,jit=-0.10)
# crown clumps behind the part going back to the tie
for ph,e in ((-30,0.80),(-6,0.86),(36,0.86),(60,0.74)):
    back_clump(ph,e,0.030,lift=1.0,jit=0.05,ht0=0.6)
print('HAIR back',round(time.time()-t0,1))

# --- fringe: big soft clumps from a side part sweeping over the forehead ---
bang_specs=[  # d0, mid, d1, rmax  (roots spread along a side part)
    ((34,0.90),(18,0.74),(4,0.53),0.030),
    ((30,0.94),(6,0.76),(-18,0.44),0.034),
    ((26,0.97),(-12,0.78),(-40,0.49),0.034),
    ((22,0.99),(-30,0.79),(-62,0.40),0.032),
    ((-10,0.97),(-55,0.70),(-82,0.30),0.030),
    ((40,0.92),(56,0.74),(68,0.42),0.030),
    ((46,0.96),(72,0.78),(86,0.36),0.028),
]
for (p0,e0),(pm,em),(p1,e1),rmax in bang_specs:
    d0=dirv(p0,e0); dm=dirv(pm,em); d1=dirv(p1,e1); R=44; P=[];RW=[];RN=[];NR=[];HT=[]
    for i in range(R):
        t=i/(R-1)
        dd=(d0*(1-t)**2+dm*2*t*(1-t)+d1*t*t).normalized(); p,n=head_pt(dd)
        tip=1.0 if t<0.62 else max(0.0,1-((t-0.62)/0.38)**1.6)**0.55
        rw=rmax*(0.78+0.22*math.sin(math.pi*t))*tip+0.004
        rn=0.52*rmax*(0.85+0.25*math.sin(math.pi*t))*tip**0.7+0.003
        h=rn*0.55+0.009+0.010*math.sin(math.pi*min(1,t*1.15))
        P.append(p+n*h); RW.append(rw); RN.append(rn); NR.append(n); HT.append(0.45+0.5*t)
    add_clump(P,RW,RN,NR,HT,1,0.0015)
# --- side strands framing the face ---
side_specs=[(1,80,0.40,Vector((0.142,-0.066,HC.z-0.105)),0.021),(1,66,0.50,Vector((0.130,-0.094,HC.z-0.062)),0.016),(-1,78,0.40,Vector((-0.142,-0.060,HC.z-0.100)),0.021)]
for sx,phi,e,endp,w in side_specs:
    p0,n0=head_pt(dirv(phi*sx,e)); p0=p0+n0*0.010
    ctrl=[np.array(p0),np.array(p0+n0*0.020+Vector((0,-0.012,-0.04))),np.array(endp+Vector((sx*0.020,0.004,0.055))),np.array(endp)]
    pts=bezier_pts(ctrl,30); R=len(pts); P=[];RW=[];RN=[];NR=[];HT=[]
    for i,pp in enumerate(pts):
        t=i/(R-1); tip=1.0 if t<0.45 else (1-((t-0.45)/0.55))**0.9
        P.append(Vector(pp)); RW.append(w*(0.9+0.2*math.sin(math.pi*t))*tip+0.002); RN.append(0.011*tip**0.8+0.002)
        NR.append(Vector((sx,-0.25,0)).normalized()); HT.append(0.5+0.5*t)
    add_clump(P,RW,RN,NR,HT,2,0.004)
print('HAIR front',round(time.time()-t0,1))

# --- ponytail: teardrop mass of big clumps + smaller flicked tips ---
PC=[TIE+Vector((0,0.004,0.004)),TIE+Vector((0,0.07,0.065)),TIE+Vector((0,0.19,0.06)),TIE+Vector((0,0.25,-0.12)),TIE+Vector((0.006,0.165,-0.27)),TIE+Vector((0.03,0.235,-0.39))]
AX=[Vector(p) for p in bezier_pts([np.array(c) for c in PC],120)]
AXs=np.concatenate([[0],np.cumsum([(AX[i+1]-AX[i]).length for i in range(len(AX)-1)])]); AXL=AXs[-1]
def ax_at(t):
    s=t*AXL; j=min(np.searchsorted(AXs,s),len(AX)-1); j0=max(j-1,0)
    f=(s-AXs[j0])/max(AXs[j]-AXs[j0],1e-9) if j>j0 else 0.0
    p=AX[j0].lerp(AX[j],f); tg=(AX[min(j0+1,len(AX)-1)]-AX[j0]).normalized()
    if t>1.0: p=AX[-1]+(AX[-1]-AX[-2]).normalized()*(t-1.0)*AXL
    return p,tg
def env(t):
    if t<0.34: return 0.022+0.056*smoothstep(0,0.34,t)
    return 0.078*max(0.0,1-((t-0.34)/0.66)**1.8)+0.006
def pony_clump(a0,off,rad,t_start,t_end,twist,flick=0.0,ht0=0.30):
    R=48; P=[];RW=[];RN=[];NR=[];HT=[]
    for i in range(R):
        u=i/(R-1); t=t_start+(t_end-t_start)*u
        p,tg=ax_at(min(t,1.0) if t<=1.0 else t)
        ux=Vector((1,0,0)); ux=(ux-tg*ux.dot(tg)).normalized(); vy=tg.cross(ux)
        a=a0+twist*t; E=env(min(t,1.0))
        ofs=off*E*(1+flick*smoothstep(0.6,1.0,u))
        radial=ux*math.cos(a)*1.25+vy*math.sin(a)*0.85
        tip=1.0 if u<0.60 else max(0.0,1-((u-0.60)/0.40)**1.5)**0.7
        rs=smoothstep(0.0,0.06,u) if t_start>0.05 else 1.0
        rw=rad*E*tip*(0.5+0.5*rs)+0.0040; rn=rw*0.80
        P.append(p+radial*ofs); RW.append(rw); RN.append(rn); NR.append(radial); HT.append(ht0+0.70*t)
    add_clump(P,RW,RN,NR,HT,3,0.002,axis_t=lambda uu,ts=t_start,te=t_end: min(1.0,ts+(te-ts)*uu))
big=[(0.0,1.00),(1.25,0.92),(2.5,0.97),(3.75,0.86),(5.0,0.90)]
for a0,te in big:
    pony_clump(a0,0.60,0.50,0.0,te,0.9)
for a0,ts,te,fl in ((0.6,0.40,1.05,0.6),(1.9,0.48,0.99,0.8),(3.2,0.44,1.07,0.5),(4.4,0.50,0.96,0.9),(5.6,0.55,1.02,0.7)):
    pony_clump(a0,0.72,0.34,ts,te,0.9,flick=fl,ht0=0.40)
print('HAIR pony',round(time.time()-t0,1))

# ---- marching cubes (external, scikit-image) ----
np.save(HAIRDIR+'/F.npy',F)
res=subprocess.run([VENV_PY,os.path.join(os.path.dirname(__file__),'mc.py'),HAIRDIR+'/F.npy',HAIRDIR+'/mc.npz',str(VOX)],capture_output=True,text=True)
print('HAIR',res.stdout.strip(),res.stderr[-400:])
dat=np.load(HAIRDIR+'/mc.npz'); V_=dat['v']+LO; F_=dat['f']
hair=mesh_from('HairMass',[tuple(v) for v in V_],[tuple(f) for f in F_])
bm=bmesh.new(); bm.from_mesh(hair.data)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6)
co=np.array([v.co for v in bm.verts]); inside=head_sdf(co,sockets=False)< -0.0035
kill=[v for v,k in zip(bm.verts,inside) if k]
bmesh.ops.delete(bm,geom=kill,context='VERTS')
# drop tiny islands
bm.verts.ensure_lookup_table()
seen=set(); islands=[]
for v in bm.verts:
    if v.index in seen: continue
    stack=[v]; isl=[]; seen.add(v.index)
    while stack:
        x=stack.pop(); isl.append(x)
        for e in x.link_edges:
            o=e.other_vert(x)
            if o.index not in seen: seen.add(o.index); stack.append(o)
    islands.append(isl)
for isl in islands:
    if len(isl)<200: bmesh.ops.delete(bm,geom=isl,context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
bm.to_mesh(hair.data); bm.free(); hair.data.shade_smooth()
sm=hair.modifiers.new('sm','SMOOTH'); sm.factor=0.6; sm.iterations=7; apply_mods(hair)
print('HAIR mc tris',tris(hair))
dec=hair.modifiers.new('dec','DECIMATE'); dec.ratio=min(1.0,float(os.environ.get('HAIR_TRIS','8600'))/max(1,tris(hair))); apply_mods(hair)
hair.data.shade_smooth()
# ensure outward normals (centroid test on a top vertex)
me=hair.data; me.update()
top=max(me.vertices,key=lambda v:v.co.z)
if top.normal.z<0:
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.reverse_faces(bm,faces=bm.faces); bm.to_mesh(me); bm.free()

# ---- per-vertex shading attributes + ponytail bone weights ----
from mathutils import kdtree
kd=kdtree.KDTree(len(SAMPLES))
for i,s in enumerate(SAMPLES): kd.insert(s[0],i)
kd.balance()
n=len(me.vertices); a_t=np.zeros(n); a_cav=np.zeros(n); a_p=np.zeros(n); a_ax=np.zeros(n)
for v in me.vertices:
    best=None
    for (co_,idx,dist) in kd.find_n(v.co,8):
        c,T_,B_,N_,rt,rw,rn,ht,kind,axt=SAMPLES[idx]; d=v.co-c
        q=math.sqrt((d.dot(T_)/rt)**2+(d.dot(B_)/rw)**2+(d.dot(N_)/rn)**2)
        if best is None or q<best[0]: best=(q,ht,kind,axt)
    q,ht,kind,axt=best if best else (3,0.5,0,0)
    a_t[v.index]=ht; a_cav[v.index]=float(smoothstep(1.02,1.55,q)); a_p[v.index]=1.0 if kind==3 else 0.0; a_ax[v.index]=axt if kind==3 else 0.0
# light smoothing of attributes over neighbours
adj=[[] for _ in range(n)]
for e in me.edges: a,b_=e.vertices; adj[a].append(b_); adj[b_].append(a)
for _ in range(2):
    a_cav=np.array([(a_cav[i]*2+sum(a_cav[j] for j in adj[i]))/(2+len(adj[i])) for i in range(n)])
    a_t=np.array([(a_t[i]*2+sum(a_t[j] for j in adj[i]))/(2+len(adj[i])) for i in range(n)])
print('HAIRSTAT cav',np.percentile(a_cav,[10,50,90]).round(2),'t',np.percentile(a_t,[10,50,90]).round(2))
for name,arr in (('h_t',a_t),('h_cav',a_cav),('h_pony',a_p)):
    at=me.attributes.new(name,'FLOAT','POINT'); at.data.foreach_set('value',arr.astype(float).tolist())
# bones: Pony_0..2 along axis, Head for the rest
vg_h=hair.vertex_groups.new(name='Head'); vgs=[hair.vertex_groups.new(name='Pony_%d'%k) for k in range(3)]
cent=[0.0,0.42,0.78]
for v in me.vertices:
    if a_p[v.index]<0.5: vg_h.add([v.index],1.0,'REPLACE'); continue
    t=a_ax[v.index]; w=[max(0.0,1-abs(t-c)/0.36) for c in cent]
    if t<0.06: vg_h.add([v.index],1-t/0.06,'REPLACE')
    s=sum(w) or 1
    for k in range(3):
        if w[k]>0: vgs[k].add([v.index],w[k]/s,'REPLACE')
bones={'Pony_%d'%k:{'head':list(ax_at(c)[0]),'tail':list(ax_at(min(1.0,[0.42,0.78,1.0][k]))[0])} for k,c in enumerate(cent)}
json.dump({'tie':list(TIE),'bones':bones},open('/workspace/character/export/ponytail_bones.json','w'),indent=1)
assign(hair,M['hair']); hair_objs.append(hair)

def flat_attrs(o,ht0,ht1,K,R):
    me=o.data; vals=[]
    for i in range(len(me.vertices)):
        ring=min(i//K,R-1) if i<K*R else R-1
        vals.append(ht0+(ht1-ht0)*ring/(R-1))
    for name,arr in (('h_t',vals),('h_cav',[0.0]*len(vals)),('h_pony',[0.0]*len(vals))):
        at=me.attributes.new(name,'FLOAT','POINT'); at.data.foreach_set('value',arr)
# hair tie
pt_dir=(PC[1]-PC[0]).normalized()
bpy.ops.mesh.primitive_torus_add(major_radius=0.026,minor_radius=0.0115,major_segments=24,minor_segments=10)
tie=bpy.context.active_object; tie.name='HairTie'; tie.location=TIE+pt_dir*0.012
tie.rotation_euler=Vector((0,0,1)).rotation_difference(pt_dir).to_euler(); assign(tie,M['tie']); tie.data.shade_smooth()
# flyaway strands (thin, soft arcs)
fly=[(dirv(24,0.95),Vector((0.5,-0.7,0.6)),0.045),(dirv(-38,0.90),Vector((-0.7,-0.5,0.5)),0.040),(dirv(118,0.55),Vector((0.8,0.3,0.4)),0.040)]
for si,(d0,go,L) in enumerate(fly):
    p0,n0=surf_dir(d0,0.030); go=go.normalized()
    ctrl=[np.array(p0),np.array(p0+go*L*0.5+n0*0.012),np.array(p0+go*L+n0*0.002-Vector((0,0,0.016)))]
    P=[Vector(p) for p in bezier_pts(ctrl,10)]
    o=sweep('HairFly_%d'%si,P,[n0]*10,[0.0045*(1-t)+0.0008 for t in np.linspace(0,1,10)],[0.0022]*10,K=5,flat=1.0)
    flat_attrs(o,0.7,1.0,5,10); assign(o,M['hair']); hair_objs.append(o)
print('HAIR done',round(time.time()-t0,1),'tris',tris(hair))
