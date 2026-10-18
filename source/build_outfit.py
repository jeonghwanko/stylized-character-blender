# ---------------- outfit ----------------
def skin_mesh(name, V, E, R, sub=2):
    o=mesh_from(name,V,[],smooth=False); me=o.data; me.clear_geometry(); me.from_pydata([tuple(v) for v in V],E,[])
    sk=o.modifiers.new('skin','SKIN'); sk.branch_smoothing=0.7; sk.use_smooth_shade=True
    for i,r in enumerate(R): me.skin_vertices[0].data[i].radius=r
    me.skin_vertices[0].data[0].use_root=True
    s=o.modifiers.new('sub','SUBSURF'); s.levels=sub; apply_mods(o); o.data.shade_smooth(); return o
def delete_faces(o, pred):
    bm=bmesh.new(); bm.from_mesh(o.data)
    kill=[f for f in bm.faces if pred(f.calc_center_median())]
    bmesh.ops.delete(bm,geom=kill,context='FACES'); bm.to_mesh(o.data); bm.free()
def snap_boundary(o,pred,fn):
    bm=bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts:
        if v.is_boundary and pred(v.co): v.co=fn(v.co)
    bm.to_mesh(o.data); bm.free()
def solid(o,t,off=-1):
    s=o.modifiers.new('sol','SOLIDIFY'); s.thickness=t; s.offset=off; s.use_even_offset=True
def smooth_loop(pts,it=4,closed=True):
    P=[Vector(p) for p in pts]; n=len(P)
    for _ in range(it):
        Q=[]
        for i in range(n):
            if not closed and (i==0 or i==n-1): Q.append(P[i]); continue
            Q.append((P[(i-1)%n]+P[i]*2+P[(i+1)%n])/4)
        P=Q
    return P
def ring_pts(bv, center, z, a0, a1, n, out=0.0, axis=None):
    pts=[];nrm=[]
    for i in range(n):
        a=math.radians(a0+(a1-a0)*i/(n-1)); d=Vector((math.sin(a),-math.cos(a),0))
        o=Vector((center[0],center[1],z))+d*0.5; hit=bv.ray_cast(o,-d)
        if hit[0] is None: continue
        pts.append(hit[0]+d*out); nrm.append(d)
    return pts,nrm

# --- body material regions (tee under hoodie, socks) ---
me=body.data
for m_ in (M['skin'],M['tee'],M['sock'],M['shoe_acc']):
    if m_.name not in [x.name for x in me.materials]: me.materials.append(m_)
for f in me.polygons:
    c=f.center
    dv=Vector((c.x,c.y-0.01,0)); dv=dv.normalized() if dv.length>1e-6 else Vector((0,-1,0))
    neck=1.240-0.025*max(0,-dv.y)
    if 0.94<c.z<neck and abs(c.x)<0.16: f.material_index=1
    elif c.z<0.150:
        f.material_index=2

bbv=bvh(body)
# tee neckline ring
pts=[]
for i in range(33):
    a=2*math.pi*i/32; d=Vector((math.sin(a),-math.cos(a),0))
    zz=1.240-0.025*max(0,-d.y)*1.0
    hit=bbv.ray_cast(Vector((0,0.010,zz))+d*0.3,-d)
    if d.y>-0.25: continue
    if hit[0] is not None and (hit[0]-Vector((0,0.01,zz))).length<0.12: pts.append(hit[0]+d*0.002)
pts=smooth_loop(pts,4,False); nl=sweep('TeeNeck',pts,[Vector((0,0,1))]*len(pts),[0.007]*len(pts),[0.018]*len(pts),K=6,flat=1.0); assign(nl,M['tee'])
for sx in (1,-1):
    cen0=Vector((0.082*sx,0.012,0))
    P=[];Ws=[];Ts=[]
    for i in range(9):
        zz=0.060+(0.200-0.060)*i/8; cen=Vector((cen0.x,cen0.y,zz)); pts=[]
        for k in range(16):
            a=2*math.pi*k/16; d=Vector((math.sin(a),-math.cos(a),0))
            hit=bbv.ray_cast(cen+d*0.2,-d)
            if hit[0] is not None and (hit[0]-cen).length<0.09: pts.append(hit[0])
        c=sum(pts,Vector())/len(pts); c.z=zz
        rx=max(abs(p.x-c.x) for p in pts); ry=max(abs(p.y-c.y) for p in pts)
        P.append(c); Ws.append(2*rx+0.007); Ts.append(2*ry+0.007)
    so_=sweep('Sock_'+('L' if sx>0 else 'R'),P,[Vector((0,-1,0))]*9,Ws,Ts,K=20,flat=1.0,cap_root=False)
    so_.data.shade_smooth(); assign(so_,M['sock'])
    sbv_=bvh(so_)
    for zz in (0.150,0.170,0.198):
        pts=[]; cen=Vector((0.082*sx,0.012,zz))
        for i in range(25):
            a=2*math.pi*i/24; d=Vector((math.sin(a),-math.cos(a),0))
            hit=sbv_.ray_cast(cen+d*0.2,-d)
            if hit[0] is not None: pts.append(hit[0]+d*(0.0008 if zz<0.19 else 0.002))
        if len(pts)>4:
            st=sweep('SockStripe_%s%d'%('L' if sx>0 else 'R',int(zz*1000)),pts,[Vector((0,0,1))]*len(pts),[0.002 if zz<0.19 else 0.005]*len(pts),[0.010 if zz<0.19 else 0.014]*len(pts),K=4 if zz<0.19 else 8,flat=1.0); assign(st,M['shoe_acc'] if zz<0.19 else M['sock'])
# --- hoodie ---
V=[];E=[];R=[]
def add2(p,r,parent=None):
    V.append(p);R.append(r); i=len(V)-1
    if parent is not None: E.append((parent,i))
    return i
h0=add2((0,0.006,0.875),(0.150,0.113))
h1=add2((0,0.004,0.99),(0.109,0.087),h0)
h2=add2((0,-0.002,1.10),(0.130,0.100),h1)
h3=add2((0,0.004,1.200),(0.134,0.094),h2)
h4=add2((0,0.010,1.278),(0.075,0.069),h3)
h5=add2((0,0.012,1.32),(0.077,0.071),h4)
for sx in (1,-1):
    s1=add2((0.150*sx,0.008,1.216),(0.066,0.066),h3)
    s2=add2((0.242*sx,0.022,0.985),(0.052,0.052),s1)
    s3=add2((0.286*sx,0.008,0.815),(0.046,0.046),s2)
    s4=add2((0.292*sx,0.006,0.790),(0.040,0.040),s3)
hood=skin_mesh('Hoodie',V,E,R)
def gap_hw(z): return 0.022+0.045*max(0,min(1,(z-0.885)/0.375))**1.6
def hood_cut(c):
    if c.z<0.885 and abs(c.x)<0.20: return True
    if c.z>1.280: return True
    if c.y<0 and abs(c.x)<gap_hw(c.z) and c.z<1.30: return True
    # sleeve ends
    if abs(c.x)>0.27 and c.z<0.80: return True
    return False
hbv0=bvh(hood)
delete_faces(hood,hood_cut)
snap_boundary(hood,lambda c:c.z>1.255 and not (c.y<0 and abs(c.x)<gap_hw(c.z)+0.010),lambda c:Vector((c.x,c.y,1.279)))
snap_boundary(hood,lambda c:c.z<0.91 and abs(c.x)<0.21,lambda c:Vector((c.x,c.y,0.886)))
solid(hood,0.007,-1)
sm=hood.modifiers.new('sm','SMOOTH'); sm.iterations=3; sm.factor=0.5
apply_mods(hood); assign(hood,M['hood'])
hbv=bvh(hood)
# push any body skin poking through the hoodie back inside
nfix=0
for v in body.data.vertices:
    c=v.co
    if c.z<0.89 or c.z>1.262: continue
    if abs(c.x)>0.26 and c.z<0.82: continue
    if c.y<0 and abs(c.x)<gap_hw(c.z)-0.004 and abs(c.x)<0.12: continue
    loc,n,_,_=hbv0.find_nearest(c)
    if loc is None: continue
    if (c-loc).dot(n)>-0.010:
        v.co=loc-n*0.010; nfix+=1
print('BODYFIX',nfix)
# collar rib around neck opening
pts=[]
for i in range(41):
    a=math.radians(360*i/40); d=Vector((math.sin(a),-math.cos(a),0))
    if d.y<0 and abs(d.x)<0.16: continue
    hit=hbv.ray_cast(Vector((0,0.01,1.266)),d)
    if hit[0] is not None: pts.append(hit[0]+d*0.004)
if len(pts)>3:
    pts=smooth_loop(pts,3,False); cl=sweep('HoodieCollar',pts,[Vector((0,0,1))]*len(pts),[0.012]*len(pts),[0.028]*len(pts),K=8,flat=1.0); assign(cl,M['hood_rib'])
# hood folded on upper back: soft pillow
bpy.ops.mesh.primitive_uv_sphere_add(segments=36,ring_count=18,radius=1)
hd=bpy.context.active_object; hd.name='Hood'
bm=bmesh.new(); bm.from_mesh(hd.data)
for v in bm.verts:
    x,y,z=v.co
    # flatten front face (against back), slight crease in middle
    y_=y*0.040 if y>0 else y*0.022
    z_=z*0.078 - 0.012*(x*x)
    x_=x*0.100*(1-0.15*max(0,-z))
    y_+= -0.006*math.exp(-(x*x)/0.02)*max(0,y)
    v.co=Vector((x_,y_,z_))
bm.to_mesh(hd.data); bm.free()
for v in hd.data.vertices:
    x_,yl,z_=v.co.x, v.co.y, v.co.z+1.205
    hit=hbv.ray_cast(Vector((x_,0.6,min(z_,1.268))),Vector((0,-1,0)))
    yb=hit[0].y if hit[0] is not None else 0.09
    v.co=Vector((x_*1.0, yb+0.002+(yl+0.022)/0.062*0.028*(1-0.75*smoothstep(1.19,1.28,z_)), z_))
hd.data.shade_smooth()
sw=hd.modifiers.new('sub','SUBSURF'); sw.levels=1
sm_=hd.modifiers.new('sm','SMOOTH'); sm_.iterations=4; sm_.factor=0.5; apply_mods(hd)
assign(hd,M['hood'])
# hem band
pts=[]
for i in range(40):
    a=math.radians(8+344*i/39); d=Vector((math.sin(a),-math.cos(a),0))
    hit=hbv.ray_cast(Vector((0,0.004,0.897)),d)
    if hit[0] is not None: pts.append(hit[0]+d*0.012)
pts=smooth_loop(pts,4,False); hem=sweep('HoodieHem',pts,[Vector((0,0,1))]*len(pts),[0.012]*len(pts),[0.040]*len(pts),K=8,flat=1.0,cap_root=True)
# sweep's width is along binormal=t x n ; we pass n=z so width is radial thickness, T is vertical
assign(hem,M['hood_rib'])
# zip edges
for sx in (1,-1):
    pts=[];nrm=[]
    for i in range(18):
        z=0.892+ (1.255-0.892)*i/17
        x=sx*(gap_hw(z)+0.004)
        o=Vector((x,-0.5,z)); hit=hbv.ray_cast(o,Vector((0,1,0)))
        if hit[0] is None: continue
        pts.append(hit[0]+Vector((0,-0.002,0))); nrm.append(Vector((0,-1,0)))
    z_=sweep('HoodieZip_'+('L' if sx>0 else 'R'),pts,nrm,[0.012]*len(pts),[0.006]*len(pts),K=6,flat=1.0)
    assign(z_,M['hood_rib'])
# cuffs
for sx in (1,-1):
    c=Vector((0.290*sx,0.006,0.80)); ax=(Vector((0.292*sx,0.006,0.78))-Vector((0.242*sx,0.022,0.985))).normalized()
    u=ax.orthogonal().normalized(); w_=ax.cross(u)
    pts=[c+ (u*math.cos(2*math.pi*i/24)+w_*math.sin(2*math.pi*i/24))*0.041 for i in range(25)]
    nr=[ax]*25
    cf=sweep('HoodieCuff_'+('L' if sx>0 else 'R'),pts,nr,[0.010]*25,[0.032]*25,K=6,flat=1.0)
    assign(cf,M['hood_rib'])
# drawstrings
for sx in (1,-1):
    top=Vector((sx*0.050,-0.075,1.262))
    hit=hbv.ray_cast(Vector((sx*0.055,-0.5,1.24)),Vector((0,1,0)))
    base=hit[0] if hit[0] else top
    ctrl=[np.array(base+Vector((0,-0.004,0))),np.array(base+Vector((sx*0.004,-0.022,-0.05))),np.array(base+Vector((sx*0.010,-0.020,-0.13)))]
    P=[Vector(p) for p in bezier_pts(ctrl,10)]
    ds=sweep('Drawstring_'+('L' if sx>0 else 'R'),P,[Vector((0,-1,0))]*10,[0.006]*10,[0.006]*10,K=6,flat=1.0)
    assign(ds,M['string'])
    bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=0.0045,depth=0.018,location=P[-1]+Vector((0,0,-0.006)))
    ag=bpy.context.active_object; ag.name='Aglet_'+('L' if sx>0 else 'R'); assign(ag,M['zip'])

# --- shorts ---
V=[];E=[];R=[]
s0=add2((0,0.010,0.875),(0.160,0.128))
s1=add2((0,0.006,0.985),(0.124,0.098),s0)
for sx in (1,-1):
    l1=add2((0.090*sx,0.008,0.80),(0.104,0.102),s0)
    l2=add2((0.099*sx,0.004,0.675),(0.104,0.104),l1)
shorts=skin_mesh('Shorts',V,E,R)
sbv0=bvh(shorts); nfx=0
for v in body.data.vertices:
    c=v.co
    if not (0.70<c.z<0.965) or abs(c.x)>0.19: continue
    loc,n,_,dd=sbv0.find_nearest(c)
    if loc is not None and dd<0.03 and (c-loc).dot(n)>-0.009: v.co=loc-n*0.009; nfx+=1
print('SHORTSFIX',nfx)
delete_faces(shorts,lambda c: c.z<0.695 or c.z>0.972)
snap_boundary(shorts,lambda c:c.z<0.76,lambda c:Vector((c.x,c.y,0.697)))
snap_boundary(shorts,lambda c:c.z>0.94,lambda c:Vector((c.x,c.y,0.970)))
solid(shorts,0.006,-1); apply_mods(shorts); assign(shorts,M['shorts'])
sbv=bvh(shorts)
for sx in (1,-1):
    pts=[]
    for i in range(33):
        a=2*math.pi*i/32; d=Vector((math.sin(a),-math.cos(a),0))
        cen=Vector((0.097*sx,0.006,0.702)); o=cen+d*0.4; hit=sbv.ray_cast(o,-d)
        if hit[0] is not None and (hit[0]-cen).length<0.14: pts.append(hit[0]+d*0.004)
    if len(pts)>4:
        pts=smooth_loop(pts[:-1],5); pts.append(pts[0]); tr=sweep('ShortsTrim_'+('L' if sx>0 else 'R'),pts,[Vector((0,0,1))]*len(pts),[0.008]*len(pts),[0.022]*len(pts),K=6,flat=1.0)
        assign(tr,M['trim'])
print('SHORTS', len(shorts.data.vertices), [round(min(v.co.z for v in shorts.data.vertices),3), round(max(v.co.z for v in shorts.data.vertices),3)])
pts,nrm=ring_pts(sbv,(0,0.006),0.938,0,360,41,out=0.003); print('WPTS',len(pts))
pts=smooth_loop(pts[:-1],4); pts.append(pts[0]); wb=sweep('ShortsWaist',pts,[Vector((0,0,1))]*len(pts),[0.008]*len(pts),[0.034]*len(pts),K=6,flat=1.0); assign(wb,M['shorts'])
# shorts drawstring bow
for sx in (1,-1):
    base=Vector((sx*0.010,-0.093,0.935))
    ctrl=[np.array(base),np.array(base+Vector((sx*0.012,-0.008,-0.03))),np.array(base+Vector((sx*0.006,-0.006,-0.06)))]
    P=[Vector(p) for p in bezier_pts(ctrl,8)]
    ds=sweep('ShortsString_'+('L' if sx>0 else 'R'),P,[Vector((0,-1,0))]*8,[0.005]*8,[0.005]*8,K=6,flat=1.0); assign(ds,M['string'])

# --- shoes ---
def shoe_upper_mat(fx):
    m=mat('M_ShoeUpper_%s'%('L' if fx>0 else 'R'),(0.93,0.93,0.92),rough=0.55); nt=m.node_tree; b=nt.nodes['Principled BSDF']
    tc=nt.nodes.new('ShaderNodeTexCoord'); sep=nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'],sep.inputs[0])
    def node(op,a,b_=None):
        n=nt.nodes.new('ShaderNodeMath'); n.operation=op
        for k,v in enumerate((a,b_)):
            if v is None: continue
            if isinstance(v,(int,float)): n.inputs[k].default_value=v
            else: nt.links.new(v,n.inputs[k])
        return n.outputs[0]
    X=sep.outputs[0]; Y=sep.outputs[1]; Z=sep.outputs[2]
    lx=node('ABSOLUTE',node('SUBTRACT',X,fx))
    zc=node('ADD',node('MULTIPLY',node('ADD',Y,0.02),0.16),0.062)
    dz=node('ABSOLUTE',node('SUBTRACT',Z,zc))
    m1=node('MULTIPLY',node('GREATER_THAN',lx,0.030),node('LESS_THAN',dz,0.012))
    m1=node('MULTIPLY',m1,node('MULTIPLY',node('GREATER_THAN',Y,-0.12),node('LESS_THAN',Y,0.075)))
    m2=node('MULTIPLY',node('GREATER_THAN',Y,0.090),node('GREATER_THAN',Z,0.050))
    m3=node('LESS_THAN',Y,-0.162)
    mm=node('MAXIMUM',node('MAXIMUM',m1,m2),m3)
    mix=nt.nodes.new('ShaderNodeMix'); mix.data_type='RGBA'; nt.links.new(mm,mix.inputs[0])
    mix.inputs[6].default_value=(0.93,0.93,0.92,1); mix.inputs[7].default_value=(0.95,0.32,0.24,1)
    nt.links.new(mix.outputs[2],b.inputs['Base Color']); return m

for sx in (1,-1):
    side='L' if sx>0 else 'R'; fx=0.084*sx
    # sole: chunky rounded-rect loft, wider than upper
    def up_w(t):
        w=0.074+0.040*math.sin(math.pi*min(1,t*1.25))**0.7
        if t<0.10: k_=math.sqrt(max(0.05,1-((0.10-t)/0.10)**2)); w*=0.55+0.45*k_
        if t>0.82: k_=math.sqrt(max(0.02,1-((t-0.82)/0.18)**2)); w*=0.35+0.65*k_
        return w
    RS=22; KS=16; sv=[]; sf=[]; band=[]
    for i in range(RS):
        t=i/(RS-1); y=0.127-0.324*t; tu=min(1,max(0,(0.115-y)/0.300))
        w=up_w(tu)+0.022
        e_=1.0
        if t<0.06: e_=math.sqrt(max(0.0,1-((0.06-t)/0.06)**2))
        if t>0.94: e_=math.sqrt(max(0.0,1-((t-0.94)/0.06)**2))
        w*=0.30+0.70*e_; hs=0.052*(0.55+0.45*e_)
        toe=max(0,(-y-0.06)/0.13); zc=0.026+0.025*toe*toe
        for k in range(KS):
            a=2*math.pi*k/KS; c=math.cos(a); s_=math.sin(a)
            xx=math.copysign(abs(c)**0.5,c)*w/2; zz=math.copysign(abs(s_)**0.6,s_)*hs/2
            sv.append(Vector((fx+xx,y,zc+zz)))
    for i in range(RS-1):
        for k in range(KS):
            sf.append((i*KS+k,i*KS+(k+1)%KS,(i+1)*KS+(k+1)%KS,(i+1)*KS+k))
    for cap,rev in ((0,False),(RS-1,True)):
        ci=len(sv); sv.append(sum(sv[cap*KS:(cap+1)*KS],Vector())/KS)
        for k in range(KS):
            f=(cap*KS+k,cap*KS+(k+1)%KS,ci); sf.append(f[::-1] if not rev else f)
    so=mesh_from('Sole_'+side,sv,sf); so.data.materials.append(M['sole']); so.data.materials.append(M['shoe_acc'])
    for p in so.data.polygons:
        kk=p.vertices[0]%KS
        ks=[v%KS for v in p.vertices if v<RS*KS]
        if ks and all(q in (15,0,1,7,8,9) for q in ks) and len(p.vertices)==4 and all(3<=v//KS<=RS-4 for v in p.vertices): p.material_index=1
    so.data.shade_smooth()
    # upper: lofted rounded section heel->toe
    R_=24; P=[];Nn=[];W_=[];T_=[]
    for i in range(R_):
        t=i/(R_-1); y=0.115-0.300*t
        w=0.074+0.040*math.sin(math.pi*min(1,t*1.25))**0.7
        hgt=0.118*(1-t)**0.6*0.55+0.045+0.02*math.sin(math.pi*t)
        if t<0.10: k_=math.sqrt(max(0.05,1-((0.10-t)/0.10)**2)); w*=0.55+0.45*k_; hgt*=0.70+0.30*k_
        if t>0.82: k_=math.sqrt(max(0.02,1-((t-0.82)/0.18)**2)); w*=0.35+0.65*k_; hgt*=0.45+0.55*k_
        zc=0.030+hgt*0.32
        toe=max(0,(-y-0.06)/0.13); zc+=0.022*toe*toe
        P.append(Vector((fx,y,zc))); Nn.append(Vector((0,0,1))); W_.append(w); T_.append(hgt)
    up=sweep('Shoe_'+side,P,Nn,W_,T_,K=16,flat=0.45); up.data.shade_smooth()
    up.location=(0,0,0)
    assign(up,shoe_upper_mat(fx))
    # collar ring
    pts=[Vector((fx+math.cos(2*math.pi*i/20)*0.038, 0.035+math.sin(2*math.pi*i/20)*0.042, 0.118+0.008*math.sin(2*math.pi*i/20))) for i in range(21)]
    cr=sweep('ShoeCollar_'+side,pts,[Vector((0,0,1))]*21,[0.012]*21,[0.016]*21,K=8,flat=1.0); assign(cr,M['shoe_acc'])
    # laces
    for li in range(4):
        y=-0.060+li*0.024; z=0.090-li*0.0 + 0.0
        hit=None
        pts=[Vector((fx-0.022,y,0.0)),Vector((fx,y,0.0)),Vector((fx+0.022,y,0.0))]
        ub=bvh(up)
        P=[];Nn=[]
        for p in pts:
            h_=ub.ray_cast(Vector((p.x,p.y,0.3)),Vector((0,0,-1)))
            if h_[0] is not None: P.append(h_[0]+Vector((0,0,0.004))); Nn.append(Vector((0,0,1)))
        if len(P)==3:
            la=sweep('Lace_%s%d'%(side,li),P,Nn,[0.008]*3,[0.006]*3,K=6,flat=1.0); assign(la,M['string'])
