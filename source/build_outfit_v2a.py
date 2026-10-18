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
def solid(o,t,off=-1):
    s=o.modifiers.new('sol','SOLIDIFY'); s.thickness=t; s.offset=off; s.use_even_offset=True
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
    neck=1.232 - (0.025 if c.y<0 else 0.0)*max(0,1-abs(c.x)/0.06)
    if 0.94<c.z<neck and abs(c.x)<0.16: f.material_index=1
    elif c.z<0.205:
        f.material_index=2

bbv=bvh(body)
# tee neckline ring
pts=[]
for i in range(33):
    a=2*math.pi*i/32; d=Vector((math.sin(a),-math.cos(a),0))
    zz=1.232-0.025*max(0,-d.y)*1.0
    hit=bbv.ray_cast(Vector((0,0.010,zz))+d*0.3,-d)
    if hit[0] is not None and (hit[0]-Vector((0,0.01,zz))).length<0.12: pts.append(hit[0]+d*0.002)
nl=sweep('TeeNeck',pts,[Vector((0,0,1))]*len(pts),[0.006]*len(pts),[0.012]*len(pts),K=6,flat=1.0); assign(nl,M['tee'])
for sx in (1,-1):
    for zz in (0.168,0.188,0.203):
        pts=[]
        for i in range(25):
            a=2*math.pi*i/24; d=Vector((math.sin(a),-math.cos(a),0)); cen=Vector((0.082*sx,0.012,zz))
            hit=bbv.ray_cast(cen+d*0.2,-d)
            if hit[0] is not None and (hit[0]-cen).length<0.08: pts.append(hit[0]+d*0.0015)
        if len(pts)>4:
            st=sweep('SockStripe_%s%d'%('L' if sx>0 else 'R',int(zz*1000)),pts,[Vector((0,0,1))]*len(pts),[0.003 if zz<0.2 else 0.004]*len(pts),[0.009 if zz<0.2 else 0.012]*len(pts),K=4,flat=1.0); assign(st,M['shoe_acc'] if zz<0.2 else M['sock'])
# --- hoodie ---
V=[];E=[];R=[]
def add2(p,r,parent=None):
    V.append(p);R.append(r); i=len(V)-1
    if parent is not None: E.append((parent,i))
    return i
h0=add2((0,0.006,0.875),(0.142,0.110))
h1=add2((0,0.004,0.99),(0.116,0.090),h0)
h2=add2((0,-0.002,1.10),(0.130,0.100),h1)
h3=add2((0,0.004,1.195),(0.134,0.094),h2)
h4=add2((0,0.010,1.270),(0.072,0.066),h3)
h5=add2((0,0.012,1.31),(0.074,0.068),h4)
for sx in (1,-1):
    s1=add2((0.150*sx,0.008,1.212),(0.064,0.064),h3)
    s2=add2((0.242*sx,0.022,0.985),(0.052,0.052),s1)
    s3=add2((0.286*sx,0.008,0.815),(0.046,0.046),s2)
    s4=add2((0.292*sx,0.006,0.790),(0.040,0.040),s3)
hood=skin_mesh('Hoodie',V,E,R)
def gap_hw(z): return 0.022+0.045*max(0,min(1,(z-0.885)/0.375))**1.6
def hood_cut(c):
    if c.z<0.885 and abs(c.x)<0.20: return True
    if c.z>1.272: return True
    if c.y<0 and abs(c.x)<gap_hw(c.z) and c.z<1.30: return True
    # sleeve ends
    if abs(c.x)>0.27 and c.z<0.80: return True
    return False
delete_faces(hood,hood_cut)
solid(hood,0.007,-1)
sm=hood.modifiers.new('sm','SMOOTH'); sm.iterations=3; sm.factor=0.5
apply_mods(hood); assign(hood,M['hood'])
hbv=bvh(hood)
# collar rib around neck opening
pts=[]
for i in range(41):
    a=math.radians(360*i/40); d=Vector((math.sin(a),-math.cos(a),0))
    if d.y<0 and abs(d.x)<0.16: continue
    hit=hbv.ray_cast(Vector((0,0.01,1.258)),d)
    if hit[0] is not None: pts.append(hit[0]+d*0.004)
if len(pts)>3:
    cl=sweep('HoodieCollar',pts,[Vector((0,0,1))]*len(pts),[0.012]*len(pts),[0.028]*len(pts),K=8,flat=1.0); assign(cl,M['hood_rib'])
# hood bunched behind neck
bpy.ops.mesh.primitive_torus_add(major_radius=0.088,minor_radius=0.040,major_segments=32,minor_segments=12)
hd=bpy.context.active_object; hd.name='Hood'
bm=bmesh.new(); bm.from_mesh(hd.data)
for v in bm.verts:
    a=math.atan2(v.co.y,v.co.x); fy=max(0,v.co.y)/0.128
    v.co.y*=0.95; v.co.z*=0.75; v.co.z+= -0.045*fy*fy - 0.01*(1-fy)
    v.co.x*=1.0+0.15*fy
kill=[v for v in bm.verts if v.co.y< 0.075]
bmesh.ops.delete(bm,geom=kill,context='VERTS'); bm.to_mesh(hd.data); bm.free()
hd.location=(0,0.012,1.262); hd.rotation_euler=(math.radians(8),0,0); hd.data.shade_smooth()
assign(hd,M['hood'])
# hem band
pts=[]
for i in range(40):
    a=math.radians(8+344*i/39); d=Vector((math.sin(a),-math.cos(a),0))
    hit=hbv.ray_cast(Vector((0,0.004,0.897)),d)
    if hit[0] is not None: pts.append(hit[0]+d*0.012)
hem=sweep('HoodieHem',pts,[Vector((0,0,1))]*len(pts),[0.012]*len(pts),[0.040]*len(pts),K=8,flat=1.0,cap_root=True)
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
s0=add2((0,0.008,0.875),(0.150,0.116))
s1=add2((0,0.006,0.985),(0.124,0.098),s0)
for sx in (1,-1):
    l1=add2((0.088*sx,0.008,0.80),(0.098,0.098),s0)
    l2=add2((0.099*sx,0.006,0.675),(0.100,0.100),l1)
shorts=skin_mesh('Shorts',V,E,R)
delete_faces(shorts,lambda c: c.z<0.695 or c.z>0.972)
solid(shorts,0.006,-1); apply_mods(shorts); assign(shorts,M['shorts'])
sbv=bvh(shorts)
for sx in (1,-1):
    pts=[]
    for i in range(33):
        a=2*math.pi*i/32; d=Vector((math.sin(a),-math.cos(a),0))
        cen=Vector((0.097*sx,0.006,0.702)); o=cen+d*0.4; hit=sbv.ray_cast(o,-d)
        if hit[0] is not None and (hit[0]-cen).length<0.14: pts.append(hit[0]+d*0.004)
    if len(pts)>4:
        tr=sweep('ShortsTrim_'+('L' if sx>0 else 'R'),pts,[Vector((0,0,1))]*len(pts),[0.008]*len(pts),[0.022]*len(pts),K=6,flat=1.0)
        assign(tr,M['trim'])
print('SHORTS', len(shorts.data.vertices), [round(min(v.co.z for v in shorts.data.vertices),3), round(max(v.co.z for v in shorts.data.vertices),3)])
pts,nrm=ring_pts(sbv,(0,0.006),0.938,0,360,41,out=0.003); print('WPTS',len(pts))
wb=sweep('ShortsWaist',pts,[Vector((0,0,1))]*len(pts),[0.008]*len(pts),[0.034]*len(pts),K=6,flat=1.0); assign(wb,M['shorts'])
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
    # sole
    bpy.ops.mesh.primitive_cube_add(size=1,location=(fx,-0.035,0.016))
    so=bpy.context.active_object; so.name='Sole_'+side; so.scale=(0.106,0.300,0.032)
    bpy.ops.object.transform_apply(scale=True)
    bv_=so.modifiers.new('bev','BEVEL'); bv_.width=0.016; bv_.segments=4
    so.data.subdivide if False else None
    apply_mods(so)
    bm_=bmesh.new(); bm_.from_mesh(so.data); bmesh.ops.subdivide_edges(bm_,edges=[e for e in bm_.edges if abs(e.verts[0].co.y-e.verts[1].co.y)>0.05],cuts=6,use_grid_fill=True); bm_.to_mesh(so.data); bm_.free()
    for v in so.data.vertices:
        t=max(0,(-v.co.y-0.06)/0.13); v.co.z+=0.025*t*t   # toe spring
        ty=abs((v.co.y+0.035)/0.15); v.co.x=fx+(v.co.x-fx)*(1-0.35*float(smoothstep(0.5,1.0,ty)))
    so.data.shade_smooth(); assign(so,M['sole'])
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
