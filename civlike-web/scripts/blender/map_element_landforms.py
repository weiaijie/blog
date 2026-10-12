"""Faceted hex landforms with compatible borders and separate seasonal snow zones."""
import math
from mathutils import Vector


def build(k, kind):
    rng=k.RNG;radius=1.75;n=15
    colors={'ground_grass':'73945D','ground_grass_light':'8BA774','ground_loam':'8E805F',
            'ground_rock':'818A89','ground_rock_light':'929B98','ground_rock_dark':'717B7C',
            'ground_snow':'E4F0F0','ground_soil':'716453','ground_subsoil':'5B5D59'}
    for name,code in colors.items():
        mat=k.M['stone'].copy();mat.name=name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color=(*linear,1)
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*linear,1)
        mat.use_backface_culling=False;k.M[name]=mat
    root=k.pivot('LandformRoot',(0,0,0),[])
    root['terrainType']=kind;root['hexRadius']=radius;root['edgeHeight']=.08
    root['edgeProfile']='hex-flat-3.5-v1'
    def norm(x,y):return max(abs(x/radius-y/(math.sqrt(3)*radius)),abs(2*y/(math.sqrt(3)*radius)),abs(x/radius+y/(math.sqrt(3)*radius)))
    def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
    def height(x,y):
        fade=smooth((1-norm(x,y))/.25)
        ripple=.025*(math.sin(x*6+y*3)+.5*math.cos(y*8-x*4))
        if kind=='grassland':z=.04+.025*math.sin(x*2+y)+ripple*.25
        elif kind=='rolling-hills':z=.64*math.exp(-((x+.54)**2/1.0+(y-.23)**2/.38))+.46*math.exp(-((x-.64)**2/.34+(y+.42)**2/.65))+ripple
        else:
            high=2.12 if kind=='snow-peak' else 1.57
            z=max(0,high-1.3*abs(x+.29)-1.5*abs(y-.13),high*.70-1.2*abs(x-.64)-1.6*abs(y+.30),high*.60-1.8*abs(x+.79)-1.3*abs(y+.40))
            z+=.11*abs(math.sin(x*7+y*4))*max(0,1-norm(x,y))
        return .08+max(0,z)*fade
    def attach(obj,parent=root):
        k.bpy.context.view_layer.update();world=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=world;return obj
    vertices=[];indices={}
    for q in range(-n,n+1):
        for r in range(-n,n+1):
            if max(abs(q),abs(r),abs(q+r))>n:continue
            x=radius*(q+.5*r)/n;y=radius*math.sqrt(3)*r/(2*n)
            if max(abs(q),abs(r),abs(q+r))<n:
                x+=rng.uniform(-.025,.025);y+=rng.uniform(-.025,.025)
            indices[q,r]=len(vertices);vertices.append((x,y,height(x,y)))
    faces=[]
    for q in range(-n,n+1):
        for r in range(-n,n+1):
            for tri in [((q,r),(q+1,r),(q,r+1)),((q+1,r),(q+1,r+1),(q,r+1))]:
                if all(p in indices for p in tri):faces.append(tuple(indices[p] for p in tri))
    assert len(faces)==6*n*n
    surface=attach(k.mesh('LandformSurface',vertices,faces,'ground_grass'))
    palette=['ground_grass','ground_grass_light','ground_loam','ground_rock','ground_rock_light','ground_rock_dark']
    for name in palette[1:]:surface.data.materials.append(k.M[name])
    maxheight=max(p[2] for p in vertices)
    snow=[([],[]) for _ in range(14)]
    for face,poly in zip(faces,surface.data.polygons):
        points=[Vector(vertices[j]) for j in face];c=sum(points,Vector())/3
        normal=(points[1]-points[0]).cross(points[2]-points[0]).normalized();edge=norm(c.x,c.y)
        patch=math.sin(c.x*3.3+math.sin(c.y*4))+.55*math.cos(c.y*5.1-c.x)
        rocky=kind in ('rocky-mountain','snow-peak') and (c.z>.32 or normal.z<.68)
        strata=math.sin(c.z*8+c.x*.8)*.2+normal.x*.16-normal.y*.1
        poly.material_index=(4 if strata>.15 else 5 if strata<-.15 else 3) if rocky else 2 if patch>1.02 and edge<.87 else int(patch>.1)
        threshold=.78 if edge>.94 else max(.05,min(.88,.85-.80*(c.z-.08)/max(.1,maxheight-.08)+.13*(1-normal.z)+.045*math.sin(c.x*9+c.y*4)))
        zone=min(13,int(threshold*14));v,f=snow[zone];b=len(v)
        v.extend([(p.x,p.y,p.z+.009) for p in points]);f.append((b,b+1,b+2))
    for i,(v,f) in enumerate(snow):
        if not f:continue
        node=attach(k.pivot('SnowZone',(0,0,0),[k.mesh('snow_cover',v,f,'ground_snow')]))
        node['snowThreshold']=i/14
    # Shared border samples remain exact and level; only the interior is jittered.
    boundary=sorted((p for (q,r),p in zip(indices,vertices) if max(abs(q),abs(r),abs(q+r))==n),key=lambda p:math.atan2(p[1],p[0]))
    for z0,z1,mat in [(-.16,-.035,'ground_subsoil'),(-.035,.08,'ground_soil')]:
        v=[(x,y,z) for z in [z0,z1] for x,y,_ in boundary];count=len(boundary)
        f=[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
        attach(k.mesh('soil_stratum',v,f,mat))
    count=len(boundary)
    attach(k.mesh('soil_underside',[(0,0,-.16)]+[(x,y,-.16) for x,y,_ in boundary],[(0,(i+1)%count+1,i+1) for i in range(count)],'ground_subsoil'))
    for edge in range(6):
        a=(edge+.5)*math.tau/6;normal=Vector((math.cos(a),math.sin(a),0));p=normal*(radius*math.sqrt(3)/2)
        marker=attach(k.pivot('HexEdge',(p.x,p.y,.08),[]))
        marker['connectionKind']='terrain';marker['edgeIndex']=edge;marker['profile']='hex-flat-3.5-v1'
        marker['normalGltf']=[normal.x,0,-normal.y];marker['neighborOffsetGltf']=[2*p.x,0,-2*p.y]
    count={'grassland':125,'rolling-hills':100,'rocky-mountain':40,'snow-peak':25}[kind]
    placed=[]
    for _ in range(count*9):
        if len(placed)>=count:break
        x=rng.uniform(-1.6,1.6);y=rng.uniform(-1.45,1.45)
        if norm(x,y)>.88 or any((x-px)**2+(y-py)**2<.014 for px,py in placed):continue
        z=height(x,y)
        if kind in ('rocky-mountain','snow-peak') and z>.38:continue
        if kind=='grassland' and math.sin(x*3.3+math.sin(y*4))+.55*math.cos(y*5.1-x)>1.10:continue
        placed.append((x,y));parts=[]
        for blade in range(rng.randint(5,9)):
            a=rng.random()*math.tau;h=rng.uniform(.08,.21);w=rng.uniform(.009,.022);dx=math.cos(a);dy=math.sin(a);v=[]
            for j in range(4):
                t=j/3;cx=x+dx*h*.65*t*t;cy=y+dy*h*.65*t*t;width=w*math.sin(math.pi*(.1+.9*t))
                v.extend([(cx-dy*width,cy+dx*width,z+h*t),(cx+dy*width,cy-dx*width,z+h*t)])
            parts.append(k.mesh('bent_grass_blade',v,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(3)],'ground_grass_light' if blade%3==0 else 'ground_grass'))
        tuft=attach(k.pivot('TerrainGrass',(x,y,z),parts));tuft['terrainTuft']=True;tuft['windPhase']=rng.random()*math.tau
        tuft['snowAltitude']=(z-.08)/max(.1,maxheight-.08)
    for i in range(28 if kind in ('rocky-mountain','snow-peak') else 12):
        a=rng.random()*math.tau;r=rng.uniform(.45,1.35);x=math.cos(a)*r;y=math.sin(a)*r
        if norm(x,y)>.90:continue
        z=height(x,y);s=rng.uniform(.035,.105)
        attach(k.ico('scree_fragment',(x,y,z+s*.17),(s,s*.68,s*.45),'ground_rock_light' if i%3==0 else 'ground_rock',1))
