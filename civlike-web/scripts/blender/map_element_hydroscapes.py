"""Waterfall height transition and one-sided lake shore, with explicit boundary profiles."""
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from map_element_riparian import RADIUS, HALF_LENGTH


def smooth(t):
    t = max(0, min(1, t))
    return t*t*(3-2*t)


def build(k, kind):
    fall = kind == 'waterfall'
    rng = k.RNG
    for name, code in {'ground_grass':'709665', 'ground_grass_light':'99B57B',
                       'shore_sand':'C3B389', 'shore_wet':'928C73', 'bed_deep':'536F71',
                       'cliff':'818C8E', 'cliff_light':'ADB4AF', 'water':'3C929F',
                       'spray':'CBE9E8', 'ground_snow':'E4ECE6', 'lake_ice':'B8D8D9'}.items():
        mat = k.M['stone'].copy(); mat.name = name
        rgb = [int(code[i:i+2], 16)/255 for i in (0,2,4)]
        rgb = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*rgb,1)
        mat.diffuse_color = (*rgb,1); mat.use_backface_culling = False
        k.M[name] = mat
    root = k.pivot('HydroscapeRoot',(0,0,0),[])
    root['terrainType'] = kind; root['hexRadius'] = RADIUS
    root['animationBoundsMin'] = [-1.85,-.31,-HALF_LENGTH-.05]
    root['animationBoundsMax'] = [1.85,1.65 if fall else .65,HALF_LENGTH+.05]

    def attach(obj):
        k.bpy.context.view_layer.update(); world = obj.matrix_world.copy()
        obj.parent = root; obj.matrix_world = world
        return obj
    def norm(x,y):
        return max(abs(x/RADIUS-y/(3**.5*RADIUS)),abs(2*y/(3**.5*RADIUS)),abs(x/RADIUS+y/(3**.5*RADIUS)))
    def level(y): return .04+1.1*smooth((y+.12)/.28) if fall else .04
    def height(x,y):
        interior = smooth((1-norm(x,y))/.22)
        if fall:
            lift = 1.1*smooth((y-.015)/.10)
            bulge = math.sin(math.pi*(y/HALF_LENGTH+1)/2)**2
            width = .4+.23*math.exp(-((y+.43)/.36)**2)*bulge
            d = abs(x)/width
            section = -.08 if d<.65 else -.08+(d-.65)*.12/.35 if d<1 else .04+(d-1)*.04/.2 if d<1.2 else .08
            z = section+lift
            z += max(0,level(y)-.04-lift)*smooth((d-.65)/.55)
            if d<1:z -= .14*math.exp(-((y+.40)/.30)**2)*max(0,1-d*d)*interior
            if d>1.2:z += (.025+.015*math.sin(x*8+y*3))*interior
            return z
        # Shoreline returns to x=0 on both mixed shore edges, while lake edges are deep.
        bend = (.18*math.sin(y*3.2)+.07*math.cos(y*6))*math.sin(math.pi*(y/HALF_LENGTH+1)/2)**2
        d = x-bend
        if d<-.24:return .08+(.025+.014*math.sin(x*5+y*4))*interior
        if d<0:return .04-d*.04/.24
        if d<.62:return .04-d*.20/.62
        return -.16

    # Retain the previous river's piecewise-linear port, including its original breakpoints.
    river_x=[RADIUS*(i-7.5)/15 for i in range(16)]
    river_x=[math.copysign(.4,x) if abs(abs(x)-.4)<RADIUS/30 else x for x in river_x]
    river_z=[height(x,-HALF_LENGTH) for x in river_x]
    refined_river_x=sorted(river_x+[-.7,-.35,0,.35,.7])
    def river_bed(x):
        for a,b,za,zb in zip(river_x,river_x[1:],river_z,river_z[1:]):
            if a-1e-8<=x<=b+1e-8:return za+(zb-za)*(x-a)/(b-a)
        raise ValueError('River port outside its edge')
    n=20; vertices=[]; indices={}
    for q in range(-n,n+1):
        for r in range(-n,n+1):
            if max(abs(q),abs(r),abs(q+r))>n:continue
            x=RADIUS*(q+.5*r)/n; y=HALF_LENGTH*r/n
            if fall and abs(r)==n:
                x=refined_river_x[q+n if r==n else q]
            elif not fall and abs(r)==n:
                for target in [-.24,0,.62]:
                    if abs(x-target)<RADIUS/n/2:x=target;break
            if max(abs(q),abs(r),abs(q+r))<n:
                x+=rng.uniform(-.009,.009);y+=rng.uniform(-.007,.007)
            z=river_bed(x)+(1.1 if r==n else 0) if fall and abs(r)==n else height(x,y)
            indices[q,r]=len(vertices);vertices.append((x,y,z))
    faces=[]
    for q in range(-n,n+1):
        for r in range(-n,n+1):
            for tri in [((q,r),(q+1,r),(q,r+1)),((q+1,r),(q+1,r+1),(q,r+1))]:
                if all(p in indices for p in tri):faces.append(tuple(indices[p] for p in tri))
    assert len(faces)==6*n*n
    ground_mesh=k.mesh('SculptedBedAndBanks',vertices,faces,'ground_grass')
    ground=attach(k.pivot('HydroscapeGround',(0,0,0),[ground_mesh]));ground['hydroscapeGround']=True
    palette=['ground_grass','ground_grass_light','shore_sand','shore_wet','bed_deep','cliff','cliff_light']
    for material in palette[1:]:ground_mesh.data.materials.append(k.M[material])
    for face,polygon in zip(faces,ground_mesh.data.polygons):
        x,y,z=(sum(vertices[i][j] for i in face)/3 for j in range(3))
        depth=level(y)-z
        if fall and -.12<y<.18 and abs(x)>.42:slot=5+int(z*9)%2
        elif depth>.055:slot=4
        elif depth>-.008:slot=3
        elif depth>-.035:slot=2
        else:slot=int(math.sin(x*5+y*3)>0)
        polygon.material_index=slot
    boundary=sorted((vertices[i] for (q,r),i in indices.items() if max(abs(q),abs(r),abs(q+r))==n),key=lambda p:math.atan2(p[1],p[0]))
    count=len(boundary);bottom=-.30
    attach(k.mesh('SubstrateSkirt',boundary+[(x,y,bottom) for x,y,_ in boundary],[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)],'cliff'))
    attach(k.mesh('Underside',[(0,0,bottom)]+[(x,y,bottom) for x,y,_ in boundary],[(0,(i+1)%count+1,i+1) for i in range(count)],'bed_deep'))
    for edge in range(6):
        angle=(edge+.5)*math.tau/6;nx,ny=math.cos(angle),math.sin(angle)
        edge_height=(1.18 if edge in [0,1,2] else .08) if fall else .08
        marker=attach(k.pivot('HexEdge',(nx*HALF_LENGTH,ny*HALF_LENGTH,edge_height),[]))
        marker['edgeIndex']=edge;marker['connectionKind']='terrain'
        marker['normalGltf']=[nx,0,-ny];marker['neighborOffsetGltf']=[nx*HALF_LENGTH*2,0,-ny*HALF_LENGTH*2]
        if fall:
            marker['profile']='hex-river-080-v1' if edge in [1,4] else 'hex-flat-3.5-v1'
            if edge in [1,4]:
                marker['waterLevel']=1.14 if edge==1 else .04
                marker['bedLevel']=1.02 if edge==1 else -.08;marker['waterWidth']=.8
            # The four sloping side edges need an explicit height-transition mate.
            if edge in [0,2,3,5]:marker['profile']='hex-drop-110-side-v1'
        else:
            marker['profile']='hex-lake-shore-v1' if edge in [1,4] else 'hex-lake-deep-v1' if edge in [0,5] else 'hex-flat-3.5-v1'
            if edge in [0,1,4,5]:marker['waterLevel']=.04
            if edge in [0,5]:marker['bedLevel']=-.16

    # Clip by interpolated depth, preserving one shared water/ground shoreline.
    def clip(points,below):
        result=[]
        for a,b in zip(points,points[1:]+points[:1]):
            da,db=a[3]-a[2],b[3]-b[2]
            ina=da>=0 if below else da<=0;inb=db>=0 if below else db<=0
            if ina:result.append(a)
            if ina!=inb:
                t=da/(da-db);result.append(tuple(a[j]+t*(b[j]-a[j]) for j in range(4)))
        clean=[]
        for point in result:
            if not clean or math.dist(point,clean[-1])>1e-9:clean.append(point)
        if len(clean)>1 and math.dist(clean[0],clean[-1])<1e-9:clean.pop()
        return clean
    water_v=[];water_f=[];depths=[];snow=[([],[]) for _ in range(6)];ice=[([],[]) for _ in range(5)]
    for face in faces:
        points=[(*vertices[i],level(vertices[i][1])) for i in face]
        for below in [True,False]:
            polygon=clip(points,below)
            if len(polygon)<3:continue
            if below:
                start=len(water_v);water_v.extend((x,y,l) for x,y,z,l in polygon);depths.extend(l-z for x,y,z,l in polygon)
                water_f.extend((start,start+i,start+i+1) for i in range(1,len(polygon)-1))
                cx=sum(p[0] for p in polygon)/len(polygon);cy=sum(p[1] for p in polygon)/len(polygon)
                zone=min(4,int(abs(math.sin(cx*3+math.sin(cy*4)))*5))
                v,f=ice[zone];start=len(v);v.extend((x,y,l+.004) for x,y,z,l in polygon)
            else:
                zone=min(5,int(abs(math.sin(sum(p[0]-p[1]*2 for p in polygon)))*6))
                v,f=snow[zone];start=len(v);v.extend((x,y,z+.006) for x,y,z,l in polygon)
            f.extend((start,start+i,start+i+1) for i in range(1,len(polygon)-1))
    water=k.mesh('ContinuousWater',water_v,water_f,'water')
    uv=water.data.uv_layers.new(name='FlowDepth')
    for poly in water.data.polygons:
        for loop in poly.loop_indices:
            i=water.data.loops[loop].vertex_index;uv.data[loop].uv=((water_v[i][1]/HALF_LENGTH+1)/2,depths[i]/1.5)
    node=attach(k.pivot('HydroscapeWater',(0,0,0),[water]));node['hydroscapeWater']=kind;node['depthScale']=1.5
    # Cap each wet boundary segment down to its real bed, not to the block bottom.
    caps=[];cap_faces=[]
    for a,b in zip(boundary,boundary[1:]+boundary[:1]):
        polygon=clip([(*a,level(a[1])),(*b,level(b[1]))],True)
        if len(polygon)<2:continue
        a,b=polygon[0],polygon[1]
        i=len(caps);caps.extend([a[:3],b[:3],(b[0],b[1],b[3]),(a[0],a[1],a[3])]);cap_faces.append((i,i+1,i+2,i+3))
    attach(k.mesh('WaterEdgeSections',caps,cap_faces,'water'))
    for tag,zones in [('snow',snow),('ice',ice)]:
        for i,(v,f) in enumerate(zones):
            if not f:continue
            node=attach(k.pivot('SnowPatch' if tag=='snow' else 'FrozenWater',(0,0,0),[k.mesh(tag,v,f,'ground_snow' if tag=='snow' else 'lake_ice')]))
            node['snowThreshold']=.15+i*.10 if tag=='snow' else .70+i*.045
            if tag=='ice':node['hydroscapeIce']=True

    bvh=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
    def actual(x,y):
        p,_,_,_=bvh.ray_cast(Vector((x,y,3)),Vector((0,0,-1)))
        assert p is not None
        return p.z
    placed=[]
    for _ in range(1600):
        if len(placed)>=56:break
        x=rng.uniform(-1.5,1.5);y=rng.uniform(-1.3,1.3)
        if norm(x,y)>.85 or any((x-a)**2+(y-b)**2<.014 for a,b in placed):continue
        z=actual(x,y)
        if z<level(y)+.012 or (fall and -.22<y<.28):continue
        if not fall and x>-.20:continue
        if rng.random()<.3:continue
        placed.append((x,y));pieces=[];h=rng.uniform(.09,.23)
        for blade in range(6):
            a=rng.random()*math.tau;dx,dy=math.cos(a),math.sin(a);length=h*rng.uniform(.7,1.2);v=[]
            for j in range(5):
                t=j/4;w=.013*math.sin(math.pi*(.1+.9*t));cx=x+dx*length*.5*t*t;cy=y+dy*length*.5*t*t
                v.extend([(cx-dy*w,cy+dx*w,z+length*t),(cx+dy*w,cy-dx*w,z+length*t)])
            pieces.append(k.mesh('shore_blade',v,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(4)],'ground_grass_light' if blade%3 else 'ground_grass'))
        node=attach(k.pivot('RootedBankGrass',(x,y,z),pieces));node['terrainTuft']=True;node['windPhase']=rng.random()*math.tau;node['snowAltitude']=0
    for i in range(45):
        x=rng.uniform(-1.4,1.4);y=rng.uniform(-1.24,1.24)
        if norm(x,y)>.87 or (fall and abs(x)<.68) or (not fall and (x<-.45 or x>.17)):continue
        z=actual(x,y)
        if z<level(y)-.04:continue
        s=rng.uniform(.025,.075)
        rock=k.ico('shore_stone',(x,y,z+s*.25),(s,s*.7,s*.5),'cliff_light' if i%3 else 'cliff',1);attach(rock)
    if fall:
        # Faceted outcrops flank the drop but stay out of the stream and all seam strips.
        for side in [-1,1]:
            for i in range(4):
                x=side*(.68+i*.17);y=.16+rng.uniform(-.035,.035);z=actual(x,y)
                attach(k.ico('jointed_ledge',(x,y,z+.035),(.16,.18,.12),'cliff' if i%2 else 'cliff_light',1))
        for i in range(18):
            x=rng.uniform(-.32,.32);y=rng.uniform(-.31,-.18)
            droplet=k.ico('water_droplet',(x,y,.055),(.014,.014,.026),'spray',1)
            node=attach(k.pivot('CascadeSpray',(x,y,.055),[droplet]));node['cascadeSpray']=True
            vertical=rng.uniform(.50,.90)
            node['sprayVelocityGltf']=[rng.uniform(-.25,.25),vertical,rng.uniform(.08,.28)]
            node['sprayLifetime']=2*vertical/3.6;node['sprayPhase']=i/18
    else:
        a=(-.61,-.45);b=(-.80,-.12)
        attach(k.beam('driftwood',(*a,actual(*a)+.04),(*b,actual(*b)+.04),.04,'bark',8,.025))
