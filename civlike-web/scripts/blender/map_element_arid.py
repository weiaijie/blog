"""C-style arid landforms; effect meshes retain explicit runtime roles."""
import math

KINDS=('volcano','lava-field','sand-dunes','desert-oasis')


def pond_radius(a):
    return .66*(1+.13*math.sin(a*3)+.08*math.cos(a*5))


def pond_norm(x,y):
    x+=.18;y=(y+.16)/.72
    return math.hypot(x,y)/pond_radius(math.atan2(y,x))


def height(kind,x,y):
    if kind=='volcano':
        r=math.hypot(x+.18,(y-.12)*1.04);a=math.atan2(y-.12,x+.18)
        rim=.47+.025*math.sin(a*5)
        if r<rim:return 1.08+.48*(r/rim)**3
        return max(0,1.56-1.74*(r-rim))*(1+.025*math.sin(a*9))
    if kind=='lava-field':return .08+.045*math.sin(x*5+y*3)+.05*math.cos(y*7-x*2)
    if kind=='sand-dunes':
        u=x+.28*math.sin(y*2)+y*.24
        z=0
        for c,h in [(-.70,.52),(.30,.72),(1.08,.34)]:
            d=u-c;z+=h*math.exp(-(d/(.39 if d<0 else .15))**2)*math.exp(-(y/1.8)**4)
        return .025+z+.011*math.sin(u*52+y*3)
    d=pond_norm(x,y);bank=max(0,min(1,(d-.60)/.55));bank=bank*bank*(3-2*bank)
    return .025+.10*bank+.22*math.exp(-((x-.9)**2/.26+(y-.7)**2/.9))


def detail(k,kind,root,height,norm,attach):
    rng=k.RNG
    def role(name,objects,effect,**data):
        p=attach(k.pivot(name,(0,0,0),objects));p['terrainEffect']=effect
        for key,value in data.items():p[key]=value
        return p
    def ribbon(name,points,width,material,effect=None):
        v=[]
        for i,(x,y) in enumerate(points):
            px,py=points[max(0,i-1)];nx,ny=points[min(len(points)-1,i+1)]
            a=math.atan2(ny-py,nx-px)+math.pi/2
            w=width*(.70+.22*math.sin(i*.71))
            for sign in [-1,1]:
                xx=x+sign*w*math.cos(a);yy=y+sign*w*math.sin(a)
                v.append((xx,yy,height(xx,yy)+.018))
        obj=k.mesh(name,v,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(points)-1)],material)
        return role(name,[obj],effect) if effect else attach(obj)
    if kind in ('volcano','lava-field'):
        mat=k.M['lava_hot'];shader=mat.node_tree.nodes['Principled BSDF']
        shader.inputs['Emission Color'].default_value=mat.diffuse_color
        shader.inputs['Emission Strength'].default_value=.8
        if kind=='volcano':
            # A recessed liquid bowl sits below the irregular rim, not a capped cone.
            v=[(-.18,.12,1.20)]
            for i in range(48):
                a=i*math.tau/48;r=.32*(1+.05*math.sin(a*7));v.append((-.18+r*math.cos(a),.12+r*math.sin(a),1.20))
            role('CraterPool',[k.mesh('molten_crater',v,[(0,i+1,(i+1)%48+1) for i in range(48)],'lava_hot')],'lava')
            for a in [-1.15,-2.90,.40]:
                points=[]
                for i in range(38):
                    r=.43+i*.024;angle=a+.045*math.sin(i*.24)
                    points.append((-.18+r*math.cos(angle),.12+r*math.sin(angle)))
                ribbon('LavaTongue',points,.028,'lava_hot','lava')
            for i in range(14):
                x=-.18+rng.uniform(-.14,.14);y=.12+rng.uniform(-.14,.14)
                p=role('VentAsh',[k.ico('ash',(x,y,1.30),(.034,.032,.05),'ground_rock_light',1)],'ash',effectPhase=i/14)
                p['driftOrigin']=[x,1.30,-y]
        else:
            for j in range(5):
                points=[]
                for i in range(49):
                    y=-1.15+i*2.3/48;x=-1.1+j*.53+.09*math.sin(y*5+j)+.035*math.sin(y*13+j)
                    if norm(x,y)<.91:points.append((x,y))
                ribbon('Fissure',points,.04,'lava_hot','lava')
            for j in range(8):
                x=rng.uniform(-.9,.9);y=rng.uniform(-1,1)
                ribbon('BranchFissure',[(x+i*.018,y+.07*math.sin(i*.2+j)) for i in range(19)],.013,'lava_hot','lava')
        for i in range(42 if kind=='lava-field' else 24):
            a=rng.random()*math.tau;r=rng.uniform(.8,1.4);x=r*math.cos(a);y=r*math.sin(a)
            s=rng.uniform(.05,.13)
            attach(k.ico('basalt_clinker',(x,y,height(x,y)+s*.2),(s,s*.7,s*.6),'ground_rock_dark',1))
    if kind=='sand-dunes':
        for j in range(23):
            points=[]
            for i in range(31):
                y=-1.06+i*2.12/30;x=-1.27+j*.11-.28*math.sin(y*2)-y*.24
                if norm(x,y)<.88:points.append((x,y))
            if len(points)>3:ribbon('WindRipple',points,.003,'sand_ripple')
        for i in range(24):
            y=rng.uniform(-.83,.83);path=[]
            for j in range(321):
                x=-1+j*2/320;yy=y+.03*math.sin(j*.015+i)
                path.extend([x,height(x,yy)+.025,-yy])
            p=role('SandDrift',[k.ico('sand_grain',(0,0,0),(.029,.008,.008),'sand_glint',1)],'sand',effectPhase=i/24)
            p['driftPath']=path
    if kind=='desert-oasis':
        v=[(-.18,-.16,.155)];rings=10;sides=48
        for j in range(1,rings+1):
            for i in range(sides):
                a=i*math.tau/sides;r=pond_radius(a)*.93*j/rings
                v.append((-.18+r*math.cos(a),-.16+r*.72*math.sin(a),.155))
        faces=[(0,i+1,(i+1)%sides+1) for i in range(sides)]
        for j in range(rings-1):
            for i in range(sides):
                a=1+j*sides+i;b=1+j*sides+(i+1)%sides
                faces.extend([(a,b,b+sides),(a,b+sides,a+sides)])
        water=k.mesh('spring_water',v,faces,'oasis_water')
        water.data.materials.append(k.M['oasis_shallow'])
        for p in water.data.polygons:
            if p.index>sides+(rings-3)*sides*2:p.material_index=1
        role('SpringWater',[water],'water')
        for i,(x,y,h) in enumerate([(-.84,.48,1.20),(.44,.54,1.50),(.85,-.45,.93)]):
            z=height(x,y);lean=.14 if i!=1 else -.13
            for j in range(9):
                t=j/9;s=(j+1)/9
                attach(k.beam('palm_trunk',(x+lean*t*t,y,z+h*t),(x+lean*s*s,y,z+h*s),.052*(1-t*.42),'wood',7,.052*(1-s*.42)))
                attach(k.beam('leaf_scar',(x+lean*s*s,y,z+h*s-.02),(x+lean*s*s,y,z+h*s),.057*(1-s*.42),'wood_light',7))
            tip=(x+lean,y,z+h)
            for frond in range(8):
                a=frond*math.tau/8+i*.23;dx=math.cos(a);dy=math.sin(a);length=.47+rng.random()*.18
                parts=[];verts=[];faces=[];rib=[]
                for j in range(13):
                    t=j/12;cx=tip[0]+dx*length*t;cy=tip[1]+dy*length*t;zz=tip[2]+.24*math.sin(t*math.pi)-.18*t*t;w=.008*(1-.8*t)
                    rib.extend([(cx-dy*w,cy+dx*w,zz),(cx+dy*w,cy-dx*w,zz)])
                parts.append(k.mesh('continuous_frond_rachis',rib,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(12)],'ground_grass'))
                for j in range(12):
                    t=(j+.3)/12;cx=tip[0]+dx*length*t;cy=tip[1]+dy*length*t;zz=tip[2]+.24*math.sin(t*math.pi)-.18*t*t
                    w=.16*math.sin(t*math.pi)**.7
                    for sign in [-1,1]:
                        b=len(verts);verts.extend([(cx,cy,zz),(cx-dy*w*sign-dx*.065,cy+dx*w*sign-dy*.065,zz-.045),(cx+dx*.035,cy+dy*.035,zz-.015)])
                        faces.append((b,b+1,b+2))
                parts.append(k.mesh('pinnate_leaflets',verts,faces,'ground_grass_light' if frond%3==0 else 'ground_grass'))
                p=attach(k.pivot('OasisFrond',tip,parts));p['terrainTuft']=True;p['windPhase']=a;p['snowAltitude']=0
            for j in range(3):attach(k.ico('palm_fruit',(tip[0]+.055*math.cos(j*2),tip[1]+.055*math.sin(j*2),tip[2]-.07),(.045,.04,.05),'wood_dark',1))
        for i in range(34):
            a=i*math.tau/34;r=pond_radius(a)*(1.05+rng.random()*.3);x=-.18+r*math.cos(a);y=-.16+r*.72*math.sin(a)
            s=rng.uniform(.015,.043)
            attach(k.ico('shore_pebble',(x,y,height(x,y)+s*.15),(s,s*.7,s*.5),'ground_rock_light',1))
