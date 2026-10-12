"""Compatible stylized route tiles, authored shapes and staged construction."""
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

KINDS=('dirt-road','stone-road','asphalt-road','rail-track')
RADIUS=1.75
APOTHEM=RADIUS*math.sqrt(3)/2


def build(k,kind):
    b=k.bpy;rng=k.RNG;rail=kind=='rail-track'
    colors={'route_grass':'78925F','route_grass_light':'96AD77','route_soil':'736653',
            'route_dirt':'AE9670','route_rut':'877252','route_gravel':'8A8983',
            'route_paver':'A7ACAB','route_paver_dark':'878E91','route_asphalt':'515E64',
            'route_paint':'E7DDD0','route_steel':'9DAEB5','route_rust':'706153'}
    for name,code in colors.items():
        mat=k.M['stone'].copy();mat.name=name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color=(*linear,1);mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*linear,1)
        if name=='route_steel':mat.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value=.65
        k.M[name]=mat
    root=k.pivot('RouteRoot',(0,0,0),[]);root['routeKind']=kind;root['edgeProfile']='hex-flat-3.5-v1'
    root['routeWidth']=1.30 if rail else 1.45;root['gauge']=.668 if rail else 0
    root['railCenterSpacing']=.72 if rail else 0
    def attach(obj,parent=root):
        b.context.view_layer.update();world=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=world;return obj
    def norm(x,y):return max(abs(x/RADIUS-y/(math.sqrt(3)*RADIUS)),abs(2*y/(math.sqrt(3)*RADIUS)),abs(x/RADIUS+y/(math.sqrt(3)*RADIUS)))
    boundary=[]
    for edge in range(6):
        a=Vector((math.cos(edge*math.tau/6)*RADIUS,math.sin(edge*math.tau/6)*RADIUS,0))
        c=Vector((math.cos((edge+1)*math.tau/6)*RADIUS,math.sin((edge+1)*math.tau/6)*RADIUS,0))
        for j in range(15):boundary.append(a.lerp(c,j/15))
    count=len(boundary)
    vertices=[];grid={};faces=[];n=8
    for q in range(-n,n+1):
        for r in range(-n,n+1):
            if max(abs(q),abs(r),abs(q+r))<=n:
                grid[q,r]=len(vertices);vertices.append((RADIUS*(q+.5*r)/n,RADIUS*math.sqrt(3)*r/(2*n),.08))
    for q in range(-n,n+1):
        for r in range(-n,n+1):
            for tri in [((q,r),(q+1,r),(q,r+1)),((q+1,r),(q+1,r+1),(q,r+1))]:
                if all(p in grid for p in tri):faces.append(tuple(grid[p] for p in tri))
    assert len(faces)==6*n*n
    ground=attach(k.mesh('route_meadow',vertices,faces,'route_grass'));ground.data.materials.append(k.M['route_grass_light'])
    for face in ground.data.polygons:
        x=sum(vertices[i][0] for i in face.vertices)/3;y=sum(vertices[i][1] for i in face.vertices)/3
        face.material_index=int(math.sin(x*3+math.cos(y*4))+.4*math.cos(y*5)>1.05)
    attach(k.mesh('route_earth',[(p.x,p.y,z) for z in [-.16,.08] for p in boundary],
                  [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]+[tuple(reversed(range(count)))],'route_soil'))
    def endpoint(edge):
        a=(edge+.5)*math.tau/6;return Vector((APOTHEM*math.cos(a),APOTHEM*math.sin(a),0))
    for edge in range(6):
        p=endpoint(edge);marker=attach(k.pivot('RoutePort',(p.x,p.y,.28 if rail else .145),[]))
        marker['routePort']=edge;marker['connectionKind']='rail' if rail else 'road'
        marker['profile']='narrow-rail-0668-v1' if rail else 'road-145-v1'
        marker['normalGltf']=[p.x/APOTHEM,0,-p.y/APOTHEM];marker['neighborOffsetGltf']=[2*p.x,0,-2*p.y]
    def path(end):
        a=endpoint(0);d=endpoint(end);c1=a*.48;c2=d*.48
        return [a*(1-t)**3+c1*3*(1-t)**2*t+c2*3*(1-t)*t*t+d*t**3 for t in [i/40 for i in range(41)]]
    def sample(points,i):
        p=points[i];tangent=(points[min(len(points)-1,i+1)]-points[max(0,i-1)]).normalized()
        if i==0 and abs(p.length-APOTHEM)<1e-5:tangent=-p.normalized()
        elif i==len(points)-1 and abs(p.length-APOTHEM)<1e-5:tangent=p.normalized()
        return p,Vector((-tangent.y,tangent.x,0))
    def strip(name,points,width,z0,z1,mat,offset=0):
        v=[];columns=8 if name=='route_surface' and mat=='route_dirt' else 1;stride=columns+3
        for i in range(len(points)):
            p,n=sample(points,i);p=p+n*offset
            v.extend([(p.x+n.x*w,p.y+n.y*w,z0) for w in [-width/2,width/2]])
            for j in range(columns+1):
                w=-width/2+width*j/columns
                rough=(.008*math.sin(p.x*17+p.y*5)*math.cos(p.y*21)-.015*math.exp(-((abs(w)-.31)/.09)**2)) if columns>1 else 0
                z=z1+rough*math.sin(math.pi*i/(len(points)-1))**2
                v.append((p.x+n.x*w,p.y+n.y*w,z))
        faces=[tuple([0]+list(range(2,stride))+[1])];last=(len(points)-1)*stride;faces.append(tuple([last,last+1]+list(reversed(range(last+2,last+stride)))))
        for i in range(len(points)-1):
            a=i*stride;c=a+stride
            faces.extend([(a,c,c+1,a+1),(a,a+2,c+2,c),(a+1,c+1,c+stride-1,a+stride-1)])
            for j in range(columns):faces.append((a+j+2,a+j+3,c+j+3,c+j+2))
        return k.mesh(name,v,faces,mat)
    def union(objects):
        target=objects[0]
        for other in objects[1:]:
            b.context.view_layer.objects.active=target
            mod=target.modifiers.new('junction_union','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=other
            b.ops.object.modifier_apply(modifier=mod.name);b.data.objects.remove(other,do_unlink=True)
        return target
    def staged(obj,parent,start,full):
        node=attach(k.pivot('RouteBuild',(0,0,0),[obj]),parent);node['routeStart']=start;node['routeFull']=full;return node
    def split_bands(obj,parent,start,span):
        # Keep authored topology, separating faces into construction zones rather than scaling the tile.
        groups=[[] for _ in range(8)]
        for face in obj.data.polygons:
            x=sum(obj.data.vertices[i].co.x for i in face.vertices)/len(face.vertices)
            groups[min(7,max(0,int((x+1.75)/3.5*8)))].append(tuple(face.vertices))
        vertices=[tuple(v.co) for v in obj.data.vertices];mat=obj.data.materials[0].name
        for i,faces in enumerate(groups):
            if faces:staged(k.mesh(obj.name+'_course',vertices,faces,mat),parent,start+span*i/8,start+span*(i+1)/8)
        b.data.objects.remove(obj,do_unlink=True)
    for shape,ends in [('straight',[3]),('bend',[2]),('junction',[3,2] if rail else [2,4])]:
        parent=attach(k.pivot('RouteShape',(0,0,0),[]));parent['routeShape']=shape;parent['ports']=[0]+ends
        paths=[path(end) for end in ends]
        width=1.30 if rail else 1.45
        split_bands(union([strip('compacted_base',p,width+.10,.081,.112,'route_gravel') for p in paths]),parent,.05,.25)
        if not rail:
            material={'dirt-road':'route_dirt','stone-road':'route_paver_dark','asphalt-road':'route_asphalt'}[kind]
            surface=union([strip('route_surface',p,width,.109,.145,material) for p in paths])
            bvh=BVHTree.FromPolygons([v.co for v in surface.data.vertices],[tuple(p.vertices) for p in surface.data.polygons])
            split_bands(surface,parent,.32,.43)
        def nearest(x,y):
            pos=Vector((x,y,0));return min((((pos-p).length,points,i) for points in paths for i,p in enumerate(points)),key=lambda item:item[0])
        if kind=='dirt-road':
            for points in paths:
                for side in [-1,1]:
                    rut=strip('wheel_worn_rut',points[3:-3],.08,.1455,.146,'route_rut',side*.31)
                    for vertex in rut.data.vertices:
                        hit,_,_,_=bvh.ray_cast(Vector((vertex.co.x,vertex.co.y,1)),Vector((0,0,-1)))
                        assert hit is not None
                        vertex.co.z=hit.z+(.0015 if vertex.co.z>.14575 else .001)
                    staged(rut,parent,.72,.84)
            for i in range(70):
                x=rng.uniform(-1.45,1.45);y=rng.uniform(-1.35,1.35);distance,_,_=nearest(x,y)
                if norm(x,y)>.87 or distance>.76:continue
                r=rng.uniform(.015,.032);staged(k.ico('road_pebble',(x,y,.146),(r,r*.7,r*.35),'route_gravel',1),parent,.80,.93)
        elif kind=='stone-road':
            for row in range(-9,10):
                for col in range(-8,9):
                    x=col*.20+(row%2)*.10;y=row*.17
                    if norm(x,y)>.89 or nearest(x,y)[0]>.60:continue
                    obj=k.box('staggered_paver',(x+rng.uniform(-.006,.006),y,.153),(.185,.153,.024),'route_paver' if rng.random()>.25 else 'route_paver_dark',.01)
                    obj.rotation_euler.z=rng.uniform(-.035,.035);staged(obj,parent,.40+(x+1.6)*.13,.46+(x+1.6)*.13)
            for points in paths:
                for i in range(4,38,4):
                    p,n=sample(points,i)
                    for side in [-1,1]:
                        q=p+n*side*.69
                        if any(min((q-other).length for other in other_path)<.60 for other_path in paths if other_path is not points):continue
                        curb=k.box('edge_sett',(q.x,q.y,.163),(.22,.10,.04),'route_paver',0)
                        curb.rotation_euler.z=math.atan2(-n.x,n.y);staged(curb,parent,.85,.98)
        elif kind=='asphalt-road':
            for route_index,points in enumerate(paths):
                for i in range(3,37,7):
                    if shape!='junction' or i>=31 or (route_index==0 and i<10):
                        staged(strip('lane_dash',points[i:i+3],.027,.1455,.147,'route_paint'),parent,.80,.9)
                for side in [-1,1]:
                    pieces=[]
                    for i in range(40):
                        p,n=sample(points,i);q=p+n*side*.59
                        inside=any(min((q-other).length for other in other_path)<.58 for other_path in paths if other_path is not points)
                        if not inside:pieces.append(strip('edge_paint',points[i:i+2],.023,.1455,.147,'route_paint',side*.59))
                    if pieces:
                        layer=attach(k.pivot('RoadPaint',(0,0,0),pieces),parent);layer['routeStart']=.84;layer['routeFull']=.94
            for x,y in [(-.70,.84),(.73,-.90)]:
                if nearest(x,y)[0]<.8:continue
                staged(k.box('road_delineator',(x,y,.25),(.052,.052,.34),'route_paint',.004),parent,.9,1)
                staged(k.box('reflector',(x,y-.028,.365),(.04,.012,.045),'tile',.003),parent,.9,1)
        else:
            sleepers=[]
            for points in paths:
                for i in range(2,40,3):
                    p,n=sample(points,i)
                    if any((p-q).length<.13 for q in sleepers):continue
                    sleepers.append(p);obj=k.box('timber_sleeper',(p.x,p.y,.15),(1.08,.105,.085),'wood_dark',.008)
                    obj.rotation_euler.z=math.atan2(n.y,n.x)
                    start=.32+.25*i/40;staged(obj,parent,start,start+.07)
                    for side in [-1,1]:
                        q=p+n*side*.36
                        plate=k.box('rail_fastener',(q.x,q.y,.196),(.13,.10,.02),'route_rust',.002);plate.rotation_euler.z=math.atan2(n.y,n.x)
                        staged(plate,parent,.55,.70)
                for side in [-1,1]:
                    for width_,lo,hi,mat in [(.095,.20,.22,'route_rust'),(.027,.22,.266,'route_steel'),(.052,.266,.28,'route_steel')]:
                        split_bands(strip('rail_profile',points,width_,lo,hi,mat,side*.36),parent,.60,.30)
            if shape=='junction':
                # A compressed switch mechanism, not an engineering turnout radius or interlocking simulation.
                p,n=sample(paths[0],11);q=p+n*.36
                tongue=strip('switch_tongue',paths[0][8:18],.018,.245,.278,'route_steel',.30)
                node=attach(k.pivot('SwitchBlade',(q.x,q.y,.25),[tongue]),parent);node['routeSwitch']=True;node['switchTravel']=[n.x*.075,0,-n.y*.075]
                staged(k.box('points_machine',(-.05,.75,.21),(.25,.18,.18),'route_asphalt',.015),parent,.9,1)
                flag=k.box('points_indicator',(-.05,.75,.52),(.15,.025,.12),'tile',.004)
                lever=attach(k.pivot('SwitchIndicator',(-.05,.75,.39),[flag]),parent);lever['routeIndicator']=True
                staged(k.beam('indicator_post',(-.05,.75,.18),(-.05,.75,.54),.016,'iron',6),parent,.9,1)
        placed=[]
        for _ in range(180):
            x=rng.uniform(-1.55,1.55);y=rng.uniform(-1.4,1.4)
            if norm(x,y)>.90 or nearest(x,y)[0]<width/2+.14 or any((x-a)**2+(y-c)**2<.025 for a,c in placed):continue
            placed.append((x,y));parts=[]
            for j in range(5):
                angle=rng.random()*math.tau;h=rng.uniform(.06,.15);dx=math.cos(angle);dy=math.sin(angle);w=.012
                parts.append(k.mesh('roadside_blade',[(x-dy*w,y+dx*w,.08),(x+dy*w,y-dx*w,.08),
                              (x+dx*h*.3+dy*w*.5,y+dy*h*.3-dx*w*.5,.08+h*.6),
                              (x+dx*h*.6,y+dy*h*.6,.08+h),(x+dx*h*.3-dy*w*.5,y+dy*h*.3+dx*w*.5,.08+h*.6)],
                              [(0,1,2),(0,2,4),(4,2,3)],'route_grass_light'))
            tuft=attach(k.pivot('RoadsideTuft',(x,y,.08),parts),parent);tuft['routeWind']=rng.random()*math.tau
            if len(placed)>=18:break
