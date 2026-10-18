# ---------------- hair ----------------
import random
random.seed(7)
M['hair']=hair_mat()
M['hair_cap']=mat('M_HairCap',(0.85,0.42,0.05),rough=0.6)
hair_objs=[]
def set_hair_t(obj, K, R, base=0.0, span=1.0, jitter=0.0):
    me=obj.data; at=me.attributes.new('hair_t','FLOAT','POINT'); j=random.uniform(-jitter,jitter)
    vals=[]
    for i in range(len(me.vertices)):
        ring=min(i//K, R-1) if i < K*R else (R-1 if i==K*R else 0)
        vals.append(min(1,max(0,base+span*ring/(R-1)+j)))
    at.data.foreach_set('value',vals)
def dirv(phi_deg, elev):
    ph=math.radians(phi_deg); c=math.sqrt(max(0,1-elev*elev))
    return Vector((math.sin(ph)*c, -math.cos(ph)*c, elev))
def slerp(a,b,t):
    a=a.normalized(); b=b.normalized(); om=math.acos(max(-1,min(1,a.dot(b))))
    if om<1e-4: return a
    return (a*math.sin((1-t)*om)+b*math.sin(t*om))/math.sin(om)
def hairline(phi):
    a=abs(phi)
    pts=[(0,0.55),(50,0.42),(80,0.30),(100,0.18),(130,-0.05),(160,-0.32),(180,-0.40)]
    for (a0,e0),(a1,e1) in zip(pts,pts[1:]):
        if a0<=a<=a1: return e0+(e1-e0)*(a-a0)/(a1-a0)
    return pts[-1][1]
T_DIR=Vector((0,0.60,0.80)).normalized()
Tp,Tn=surf_dir(T_DIR,0.0)
TIE=Tp+Tn*0.030
# cap (under-layer, darker) from low-res sphere
cap=make_sphere('HairCap',40,26)
cc=np.array([v.co for v in cap.data.vertices]); d=cc/np.linalg.norm(cc,axis=1)[:,None]
pc=head_shape(cc); nn=(pc-np.array(HC)); nn/=np.linalg.norm(nn,axis=1)[:,None]
pc=pc+nn*0.006
for v,c in zip(cap.data.vertices,pc): v.co=c
bm=bmesh.new(); bm.from_mesh(cap.data)
kill=[]
for v,dd in zip(bm.verts,d):
    phi=math.degrees(math.atan2(dd[0],-dd[1])); 
    if dd[2] < hairline(phi)-0.02: kill.append(v)
bmesh.ops.delete(bm,geom=kill,context='VERTS'); bm.to_mesh(cap.data); bm.free()
assign(cap,M['hair_cap']); hair_objs.append(cap)

K=8
# pulled-back clumps (two layers)
idx=0
for layer,(step,off0,phase) in enumerate(((22,0.002,0),(22,0.007,11))):
    phi=-168+phase
    while phi<=180-6:
        if abs(phi)>(46 if layer==0 else 40):   # front covered by bangs on 2nd layer
            e0=hairline(phi)+0.02
            d0=dirv(phi,e0); R=10
            P=[];N=[];W=[];T=[]
            for i in range(R):
                t=i/(R-1)
                dd=slerp(d0,T_DIR,t*0.93)
                p,n=surf_dir(dd,0.0)
                off=off0+0.006*math.sin(math.pi*t)+0.012*t-0.004*(1-t)**4
                P.append(p+n*off); N.append(n)
                W.append((0.080 if layer==0 else 0.068)*(1.0-0.55*t)+0.004)
                T.append((0.004+0.010*smoothstep(0.0,0.35,t))*(1-0.2*t)+0.002)
            o=sweep('HairBack_%02d'%idx,P,N,W,T,K=K,flat=0.25); set_hair_t(o,K,R,0.15,0.55,0.12)
            assign(o,M['hair']); hair_objs.append(o); idx+=1
        phi+=step
# bangs: 4 big clumps swept from a side part (+x) to -x
bang_specs=[  # start(phi,elev), end(phi,elev), width, curl
    ((34,0.90),(-2,0.50),0.072,0.2),
    ((18,0.92),(-30,0.45),0.076,0.3),
    ((2,0.92),(-58,0.36),0.070,0.35),
    ((50,0.84),(40,0.44),0.056,-0.2),
]
for bi,((p0,e0),(p1,e1),w,curl) in enumerate(bang_specs):
    R=14; P=[];N=[];W=[];T=[]
    d0=dirv(p0,e0); d1=dirv(p1,e1)
    for i in range(R):
        t=i/(R-1)
        dd=slerp(d0,d1,t)
        p,n=surf_dir(dd,0.0)
        off=0.024+0.012*math.sin(math.pi*t)-0.006*t + (0.010*t**3)
        P.append(p+n*off); N.append(n)
        taper=1-smoothstep(0.55,1.0,t)
        W.append(w*1.25*(0.85+0.15*math.sin(math.pi*t))*taper**0.7+0.002); T.append(0.026*(1-0.5*t)*taper**0.5+0.003)
    o=sweep('HairBang_%d'%bi,P,N,W,T,K=K,flat=0.3); set_hair_t(o,K,R,0.45,0.5,0.08)
    assign(o,M['hair']); hair_objs.append(o)
# side strands framing face
side_specs=[(1,80,0.30,1.395,0.040),(1,68,0.36,1.43,0.030),(-1,78,0.30,1.40,0.040)]
for si,(sx,phi,e,zend,w) in enumerate(side_specs):
    R=14; P=[];N=[];W=[];T=[]
    d0=dirv(phi*sx,e+0.08)
    p0,n0=surf_dir(d0,0.012)
    endp=Vector((sx*(0.142 if w>0.035 else 0.135), -0.07 if w>0.035 else -0.095, zend))
    ctrl=[np.array(p0), np.array(p0+n0*0.02+Vector((0,-0.01,-0.04))), np.array(endp+Vector((sx*0.022,0,0.06))), np.array(endp)]
    pts=bezier_pts(ctrl,R)
    for i,pp in enumerate(pts):
        t=i/(R-1); pv=Vector(pp)
        P.append(pv); N.append(Vector((sx,-0.2,0)).normalized())
        W.append(w*1.3*(1-smoothstep(0.5,1,t))**0.8+0.002); T.append(0.016*(1-0.5*t)+0.002)
    o=sweep('HairSide_%d'%si,P,N,W,T,K=K,flat=0.5); set_hair_t(o,K,R,0.5,0.45,0.05)
    assign(o,M['hair']); hair_objs.append(o)
# ponytail
pt_dir=Vector((0,0.45,0.89)).normalized()
NPT=8
for ci in range(NPT):
    a=2*math.pi*ci/NPT
    ox,oy=math.cos(a),math.sin(a)   # ring around ponytail axis
    rnd=lambda r: random.uniform(-r,r)
    R=16
    sp=lambda k: Vector((ox*k*1.35, oy*k*0.8, oy*k*0.5))
    ctrl=[TIE+sp(0.010),
          TIE+Vector((0,0.03,0.08))+sp(0.035)+Vector((rnd(0.01),rnd(0.01),rnd(0.01))),
          TIE+Vector((0,0.15,0.10))+sp(0.050)+Vector((rnd(0.015),rnd(0.015),rnd(0.015))),
          TIE+Vector((0,0.23,-0.06))+sp(0.055)+Vector((rnd(0.02),rnd(0.02),rnd(0.02))),
          TIE+Vector((0,0.20,-0.32))+sp(0.045)+Vector((rnd(0.03),rnd(0.03),rnd(0.04)))]
    pts=bezier_pts([np.array(c) for c in ctrl],R)
    P=[Vector(p) for p in pts]
    N=[sp(1).normalized() if sp(1).length>1e-6 else Vector((0,1,0))]*R
    W=[];T=[]
    for i in range(R):
        t=i/(R-1); bulge=math.sin(math.pi*min(1,t*1.15))
        taper=(1-smoothstep(0.70,1.0,t))
        W.append((0.050+0.050*bulge)*taper**0.8+0.002)
        T.append((0.034+0.026*bulge)*taper**0.6+0.002)
    o=sweep('HairPony_%d'%ci,P,N,W,T,K=K,flat=0.7); set_hair_t(o,K,R,0.35,0.6,0.1)
    assign(o,M['hair']); hair_objs.append(o)
# hair tie
bpy.ops.mesh.primitive_torus_add(major_radius=0.026,minor_radius=0.011,major_segments=16,minor_segments=6)
tie=bpy.context.active_object; tie.name='HairTie'; tie.location=TIE+pt_dir*0.008
tie.rotation_euler=Vector((0,0,1)).rotation_difference(pt_dir).to_euler(); assign(tie,M['tie']); tie.data.shade_smooth()
# stray strands
stray=[(dirv(30,0.92),Vector((0.6,-0.6,0.5))),(dirv(-75,0.62),Vector((-1,-0.2,-0.3)))]
for si,(d0,go) in enumerate(stray):
    p0,n0=surf_dir(d0,0.025); go=go.normalized()
    ctrl=[np.array(p0),np.array(p0+go*0.018+n0*0.008),np.array(p0+go*0.034+n0*0.004-Vector((0,0,0.012)))]
    P=[Vector(p) for p in bezier_pts(ctrl,8)]
    o=sweep('HairStray_%d'%si,P,[n0]*8,[0.009*(1-t)+0.001 for t in np.linspace(0,1,8)],[0.004]*8,K=6,flat=0.6)
    set_hair_t(o,6,8,0.6,0.3); assign(o,M['hair']); hair_objs.append(o)
