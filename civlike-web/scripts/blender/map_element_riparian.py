"""Clipped shallow-water hexes with matched river ports and rooted bank vegetation."""
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

RADIUS = 1.75
HALF_LENGTH = RADIUS * math.sqrt(3) / 2
LEVEL = .04


def build(k, kind):
    wet = kind == 'wetland'
    rng = k.RNG
    colors = {'ground_grass': '6D9665', 'ground_grass_light': '8CAD74',
              'bank_mud': '716657', 'bank_silt': 'B1A180', 'bank_gravel': '929B92',
              'bank_deep': '495E58', 'river_water': '438F9B', 'ground_snow': 'E1EBE6',
              'river_ice': 'B8DAD9', 'sedge_dry': 'B4A36B', 'cattail': '735A41'}
    for name, code in colors.items():
        mat = k.M['stone'].copy(); mat.name = name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        rgb = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color = (*rgb, 1)
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*rgb, 1)
        mat.use_backface_culling = False
        k.M[name] = mat
    root = k.pivot('RiparianRoot', (0, 0, 0), [])
    root['terrainType'] = kind; root['hexRadius'] = RADIUS
    root['edgeProfile'] = 'hex-riparian-3.5-v1'; root['waterLevel'] = LEVEL

    def attach(obj):
        k.bpy.context.view_layer.update(); world = obj.matrix_world.copy()
        obj.parent = root; obj.matrix_world = world
        return obj
    def norm(x, y):
        return max(abs(x/RADIUS-y/(3**.5*RADIUS)), abs(2*y/(3**.5*RADIUS)), abs(x/RADIUS+y/(3**.5*RADIUS)))
    def shape(y):
        t = (y/HALF_LENGTH+1)/2
        bulge = math.sin(math.pi*t)**2
        center = (-.22 if wet else .58)*bulge
        half = .4 + bulge*(.30+.11*math.sin(y*5) if wet else .06)
        return center, half, bulge
    def height(x, y):
        center, half, bulge = shape(y); d = abs(x-center)/half
        z = -.08 if d < .65 else -.08+(d-.65)*.12/.35 if d < 1 else .04+(d-1)*.04/.2 if d < 1.2 else .08
        interior = max(0, min(1, (1-norm(x, y))/.20))
        if wet:
            # Low hummocks break up the flooded basin, while both ports stay identical.
            for cx, cy, h, spread in [(-.32,-.45,.19,.038),(.27,.35,.16,.032),(-.77,.57,.09,.09)]:
                z += h*math.exp(-((x-cx)**2+(y-cy)**2)/spread)*interior*bulge
        elif d > .9:
            # Left bank is the inside of the bend; right bank is the steeper cut bank.
            z += (.17 if x > center else .012)*math.exp(-((d-1.35)/.40)**2)*interior*bulge
        if d > 1.2:
            z += (.012+.012*math.sin(x*6+y*3))*interior*bulge
        return z

    n = 15; vertices = []; indices = {}
    for q in range(-n,n+1):
        for r in range(-n,n+1):
            if max(abs(q),abs(r),abs(q+r)) > n: continue
            x = RADIUS*(q+.5*r)/n; y = HALF_LENGTH*r/n
            if abs(r)==n and abs(abs(x)-.4)<RADIUS/n/2:
                x = math.copysign(.4,x)
            if max(abs(q),abs(r),abs(q+r)) < n:
                x += rng.uniform(-.012,.012); y += rng.uniform(-.012,.012)
            indices[q,r] = len(vertices); vertices.append((x,y,height(x,y)))
    faces = []
    for q in range(-n,n+1):
        for r in range(-n,n+1):
            for tri in [((q,r),(q+1,r),(q,r+1)),((q+1,r),(q+1,r+1),(q,r+1))]:
                if all(p in indices for p in tri): faces.append(tuple(indices[p] for p in tri))
    assert len(faces) == 6*n*n
    terrain = k.mesh('ChannelBedAndBanks', vertices, faces, 'ground_grass')
    ground = attach(k.pivot('ChannelTerrain', (0,0,0), [terrain])); ground['riparianGround'] = True
    palette = ['ground_grass','ground_grass_light','bank_mud','bank_silt','bank_gravel','bank_deep']
    for material in palette[1:]: terrain.data.materials.append(k.M[material])
    for face, polygon in zip(faces,terrain.data.polygons):
        x,y,z = (sum(vertices[i][axis] for i in face)/3 for axis in range(3))
        center,half,_ = shape(y); d = abs(x-center)/half
        polygon.material_index = 5 if z < -.025 else 2 if z < .035 else 3 if d < 1.3 and (wet or x < center) else 4 if not wet and x > center and d < 1.6 else int(math.sin(x*4+y*3) > 0)
    boundary = sorted((vertices[i] for (q,r),i in indices.items() if max(abs(q),abs(r),abs(q+r)) == n), key=lambda p:math.atan2(p[1],p[0]))
    count = len(boundary)
    skirt = boundary + [(x,y,-.16) for x,y,_ in boundary]
    attach(k.mesh('SoilSkirt', skirt, [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)], 'bank_mud'))
    attach(k.mesh('Underside', [(0,0,-.16)]+skirt[count:], [(0,(i+1)%count+1,i+1) for i in range(count)], 'bank_deep'))
    for edge in range(6):
        a = (edge+.5)*math.tau/6; nx,ny = math.cos(a),math.sin(a)
        marker = attach(k.pivot('HexEdge', (nx*HALF_LENGTH,ny*HALF_LENGTH,.08), []))
        marker['edgeIndex'] = edge; marker['connectionKind'] = 'terrain'
        marker['profile'] = 'hex-river-080-v1' if edge in [1,4] else 'hex-flat-3.5-v1'
        marker['normalGltf'] = [nx,0,-ny]; marker['neighborOffsetGltf'] = [nx*HALF_LENGTH*2,0,-ny*HALF_LENGTH*2]
        if edge in [1,4]:
            marker['waterLevel'] = LEVEL; marker['bedLevel'] = -.08; marker['waterWidth'] = .8

    def clip(points, below=True):
        result = []
        for a,b in zip(points,points[1:]+points[:1]):
            inside_a = a[2] <= LEVEL if below else a[2] >= LEVEL
            inside_b = b[2] <= LEVEL if below else b[2] >= LEVEL
            if inside_a: result.append(a)
            if inside_a != inside_b:
                t = (LEVEL-a[2])/(b[2]-a[2])
                result.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,LEVEL))
        clean = []
        for point in result:
            if not clean or math.dist(clean[-1],point)>1e-9: clean.append(point)
        if len(clean)>1 and math.dist(clean[0],clean[-1])<1e-9: clean.pop()
        return clean
    water_v = []; water_f = []; depths = []; snow = [([],[]) for _ in range(8)]; ice = [([],[]) for _ in range(5)]
    for face in faces:
        points = [vertices[i] for i in face]
        for below in [True,False]:
            polygon = clip(points,below)
            if len(polygon) < 3: continue
            if below:
                start = len(water_v)
                water_v.extend((x,y,LEVEL) for x,y,_ in polygon); depths.extend(LEVEL-z for _,_,z in polygon)
                water_f.extend((start,start+i,start+i+1) for i in range(1,len(polygon)-1))
                cx = sum(p[0] for p in polygon)/len(polygon); cy = sum(p[1] for p in polygon)/len(polygon)
                patch = .65*math.sin(cx*3+math.sin(cy*4))+.35*math.cos(cy*5-cx*2)
                zone = min(4,int(abs(patch)*5))
                v,f = ice[zone]; b = len(v); v.extend((x,y,LEVEL+.003) for x,y,_ in polygon)
            else:
                zone = min(7,int((.3+.5*abs(math.sin(sum(p[0]*2-p[1] for p in polygon))))*8))
                v,f = snow[zone]; b = len(v); v.extend((x,y,z+.007) for x,y,z in polygon)
            f.extend((b,b+i,b+i+1) for i in range(1,len(polygon)-1))
    water = k.mesh('ClippedWaterSurface',water_v,water_f,'river_water')
    uv = water.data.uv_layers.new(name='FlowDepth')
    for polygon in water.data.polygons:
        for loop in polygon.loop_indices:
            index = water.data.loops[loop].vertex_index
            uv.data[loop].uv = ((water_v[index][1]/HALF_LENGTH+1)/2,depths[index]/.15)
    water_node = attach(k.pivot('RiparianWater',(0,0,0),[water])); water_node['riparianWater'] = True
    water_node['depthScale'] = .15; water_node['flowKind'] = kind
    # Water end faces follow the actual clipped bed cross section, not a full-width blue cap.
    for sign in [-1,1]:
        points = sorted((p for p in boundary if abs(p[1]-sign*HALF_LENGTH)<1e-6),key=lambda p:p[0]); v=[]; f=[]
        for a,b in zip(points,points[1:]):
            if min(a[2],b[2]) >= LEVEL: continue
            a,b = list(a),list(b)
            if a[2] > LEVEL:
                t=(LEVEL-b[2])/(a[2]-b[2]);a=[b[j]+(a[j]-b[j])*t for j in range(3)]
            if b[2] > LEVEL:
                t=(LEVEL-a[2])/(b[2]-a[2]);b=[a[j]+(b[j]-a[j])*t for j in range(3)]
            i=len(v);v.extend([a,b,(b[0],b[1],LEVEL),(a[0],a[1],LEVEL)]);f.append((i,i+1,i+2,i+3))
        attach(k.mesh('WaterPortSection',v,f,'river_water'))
    for kind_z,zones in [('snow',snow),('ice',ice)]:
        for i,(v,f) in enumerate(zones):
            if not f: continue
            zone = attach(k.pivot('BankSnow' if kind_z=='snow' else 'RiverIce',(0,0,0),[k.mesh(kind_z,v,f,'ground_snow' if kind_z=='snow' else 'river_ice')]))
            zone['snowThreshold'] = .15+i*.085 if kind_z=='snow' else .70+i*.045
            if kind_z=='ice': zone['riparianIce'] = True

    bvh = BVHTree.FromPolygons(vertices,faces,all_triangles=True)
    def actual_height(x,y):
        p,_,_,_ = bvh.ray_cast(Vector((x,y,2)),Vector((0,0,-1)))
        assert p is not None
        return p.z
    placed = []
    for _ in range(1400):
        if len(placed) >= (80 if wet else 62): break
        x=rng.uniform(-1.55,1.55);y=rng.uniform(-1.32,1.32)
        if norm(x,y)>.87 or any((x-a)**2+(y-b)**2<.012 for a,b in placed):continue
        z=actual_height(x,y);center,half,_=shape(y);d=abs(x-center)/half
        if z < -.012 or (not wet and x>center and d<1.4):continue
        if z > .075 and rng.random()>.45:continue
        placed.append((x,y));rush=z<.075;parts=[];h=rng.uniform(.20,.39) if rush else rng.uniform(.08,.17)
        for blade in range(6 if rush else 5):
            a=rng.random()*math.tau;dx,dy=math.cos(a),math.sin(a);length=h*rng.uniform(.65,1.1);v=[]
            for j in range(5):
                t=j/4;w=.012*math.sin(math.pi*(.08+.92*t));cx=x+dx*length*.65*t*t;cy=y+dy*length*.65*t*t
                v.extend([(cx-dy*w,cy+dx*w,z+length*t),(cx+dy*w,cy-dx*w,z+length*t)])
            parts.append(k.mesh('folded_sedge',v,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(4)],'sedge_dry' if blade==0 else 'ground_grass_light' if blade%2 else 'ground_grass'))
        if rush and len(placed)%3==0:
            parts.extend([k.beam('cattail_stem',(x,y,z),(x+.015,y,z+h*1.2),.007,'ground_grass',5),k.beam('cattail_head',(x+.013,y,z+h*.98),(x+.017,y,z+h*1.25),.022,'cattail',7)])
        node=attach(k.pivot('RootedSedge',(x,y,z),parts));node['terrainTuft']=True;node['windPhase']=rng.random()*math.tau;node['snowAltitude']=0
    for i in range(35):
        y=rng.uniform(-1.25,1.25);center,half,_=shape(y);x=center-half*rng.uniform(1.05,1.6)
        if norm(x,y)>.87:continue
        z=actual_height(x,y);s=rng.uniform(.015,.045)
        attach(k.ico('alluvial_pebble',(x,y,z+s*.25),(s,s*.67,s*.47),'bank_gravel',1))
    if wet:
        a=(-.83,-.12);b=(-1.14,.27);za=actual_height(*a)+.045;zb=actual_height(*b)+.045
        attach(k.beam('fallen_log',(*a,za),(*b,zb),.053,'bark',8,.035))
        attach(k.beam('broken_branch',(-.97,.055,(za+zb)/2),(-1.12,.02,(za+zb)/2+.12),.019,'wood',5,.009))
