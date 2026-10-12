"""Composable fortifications, open archways, working gates and cloth pennants."""
import math

from map_element_buildings import build_group, connection


def build(k, kind):
    root = k.pivot('BuildingRoot', (0,0,0), [])
    root['buildingType'] = kind

    def group(name, objects, start, end, anchor=(0,0,0), **kwargs):
        return build_group(k,root,name,objects,start,end,anchor,**kwargs)

    def socket(name,pos,role):
        node=connection(k,root,name,pos,role)
        if role=='wall':
            node['connectionProfile']='curtain-3.2'
            node['walkwayHeight']=3.2
            node['wallThickness']=1.2
            node['connectionNormal']=[-1 if pos[0]<0 else 1,0,0]
        return node

    def stone(pos,size,light=False):
        return k.box('dressed_stone',pos,size,'stone_light' if light else 'stone',.009)

    def arch(y,radius,spring,depth):
        parts=[]
        for i in range(11):
            a,b=i*math.pi/11+.009,(i+1)*math.pi/11-.009
            verts=[(r*math.cos(t),y+dy,spring+r*math.sin(t)) for dy in [-depth/2,depth/2] for r in [radius,radius+.24] for t in [a,b]]
            parts.append(k.mesh('arch_voussoir',verts,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],'stone_light'))
        for side in [-1,1]:
            for i in range(5): parts.append(stone((side*(radius+.12),y,.24+(spring-.24)*(i+.5)/5),(.235,depth,(spring-.24)/5-.02),True))
        return parts

    def wall_courses(w,d,height,door=False,back_door=False):
        count=10
        for level in range(count):
            bottom=.24+level*(height-.24)/count
            h=(height-.24)/count-.018
            parts=[]
            for side in [-1,1]:
                for j in range(7):
                    parts.append(stone((side*(w/2-.12),-d/2+(j+.5)*d/7,bottom+h/2),(.24,d/7-.02,h),j%4==level%4))
                open_width=0
                if door and (side<0 or back_door):
                    open_width=.9 if bottom<1.95 else math.sqrt(max(0,.9**2-(bottom-1.95)**2)) if bottom<2.85 else 0
                intervals=[(-w/2,-open_width),(open_width,w/2)] if open_width else [(-w/2,w/2)]
                for left,right in intervals:
                    length=right-left
                    n=max(1,math.ceil(length/.60))
                    for j in range(n):
                        parts.append(stone((left+(j+.5)*length/n,side*(d/2-.12),bottom+h/2),(length/n-.018,.24,h),j%4==level%4))
            group('WallCourse',parts,.10+level*.044,.18+level*.044,(0,0,bottom))

    def battlements(w,d,z,cx=0,cy=0,tier=1,open_ends=False):
        parts=[]
        for side in [-1,1]:
            parts.append(k.box('parapet',(cx,cy+side*(d/2-.09),z+.14),(w,.22,.28),'stone',.02))
            for i in range(max(2,round(w/.65))):
                n=max(2,round(w/.65))
                parts.append(stone((cx-w/2+w*(i+.5)/n,cy+side*(d/2-.09),z+.47),(w/n*.57,.26,.42),True))
            if not open_ends: parts.append(k.box('side_parapet',(cx+side*(w/2-.09),cy,z+.14),(.22,d,.28),'stone',.02))
        group('Battlements',parts,.69,.86,(cx,cy,z),tier=tier)

    def tower(cx,cy,radius,height):
        for level in range(8):
            z=.24+(height-.24)*level/8
            parts=[]
            for i in range(10):
                a,b=(i+level%2*.5)*math.tau/10,(i+1+level%2*.5)*math.tau/10-.018
                verts=[(cx+r*math.cos(t),cy+r*math.sin(t),h) for h in [z,z+(height-.24)/8-.018] for r in [radius-.19,radius] for t in [a,b]]
                parts.append(k.mesh('tower_block',verts,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],'stone_light' if i%3==level%3 else 'stone'))
            group('TowerCourse',parts,.12+level*.055,.22+level*.055,(cx,cy,z))
        parts=[k.beam('tower_deck',(cx,cy,height-.08),(cx,cy,height),radius,'wood',10)]
        for i in range(10):
            a=i*math.tau/10
            block=stone((cx+math.cos(a)*(radius-.07),cy+math.sin(a)*(radius-.07),height+.25),(.32,.27,.50),True)
            block.rotation_euler.z=a
            parts.append(block)
        group('TowerCrown',parts,.68,.87,(cx,cy,height))

    def flag(x,y,z,width=1,height=.55,tier=1,base=0):
        group('FlagMast',[k.beam('flagpole',(x,y,base),(x,y,z+height+.18),.035,'wood_dark',8),k.ico('finial',(x,y,z+height+.20),(.07,.07,.07),'gold',2)],.83,.94,(x,y,z),tier=tier)
        verts=[]
        for i in range(13):
            t=i/12
            for j in range(4):
                v=j/3
                verts.append((x+t*width,y+.025*math.sin(t*7)*t,z+height*v-.08*t))
        faces=[]
        for i in range(12):
            for j in range(3):
                a=i*4+j
                faces.extend([(a,a+4,a+5),(a,a+5,a+1)])
        cloth=k.mesh('segmented_banner',verts,faces,'teal')
        cloth.data.materials.append(k.M['gold'])
        for face in cloth.data.polygons:
            if face.index%6 in [2,3]: face.material_index=1
        group('Banner',[cloth],.87,.99,(x,y,z),tier=tier,motion='banner')

    dimensions={'watchtower':(2.7,2.7),'castle-keep':(5.9,5.2),'castle-gate':(5.6,2.6),'castle-wall':(4.0,1.45)}
    w,d=dimensions[kind]
    group('Foundation',[k.box('plinth',(0,0,.12),(w,d,.24),'stone',.025)],0,.12)

    if kind=='watchtower':
        wall_courses(2.3,2.3,2.7)
        upper=[k.box('lookout_floor',(0,0,2.77),(2.75,2.75,.18),'wood')]
        for x in [-1.16,1.16]:
            for y in [-1.16,1.16]:
                upper.append(k.box('lookout_post',(x,y,3.61),(.17,.17,1.7),'wood_dark'))
                upper.append(k.beam('corner_brace',(x,y,3.7),(x*.66,y*.66,4.32),.065,'wood_light',4))
        for side in [-1,1]:
            if side<0:
                for x in [-.87,.87]: upper.append(k.box('entry_rail',(x,-1.22,3.45),(.80,.1,.12),'wood_light'))
            else: upper.append(k.box('handrail',(0,side*1.22,3.45),(2.6,.1,.12),'wood_light'))
            upper.append(k.box('side_rail',(side*1.22,0,3.45),(.1,2.6,.12),'wood_light'))
        group('LookoutFrame',upper,.47,.66,(0,0,2.7))
        roof=k.mesh('pavilion_roof',[(-1.55,-1.55,4.43),(1.55,-1.55,4.43),(1.55,1.55,4.43),(-1.55,1.55,4.43),(0,0,5.35)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)],'teal')
        group('Roof',[roof],.65,.81,(0,0,4.43))
        ladder=[]
        for side in [-1,1]: ladder.append(k.beam('ladder_rail',(side*.36,-2.80,.10),(side*.36,-1.23,2.84),.055,'wood_dark',4))
        for i in range(10):
            t=(i+.5)/10
            ladder.append(k.box('ladder_tread',(0,-2.8+1.57*t,.10+2.74*t),(.80,.20,.06),'wood_light'))
        group('AccessLadder',ladder,.74,.90)
        flag(0,0,5.7,.85,.48,base=5.3)
        group('ReinforcingBraces',[k.beam('upper_support',(x,y,2.25),(x*1.17,y*1.17,2.72),.09,'wood_dark',4) for x in [-1.0,1.0] for y in [-1.0,1.0]],.54,.77,tier=2)
        socket('Entrance',(0,-2.95,0),'road')
    elif kind=='castle-keep':
        wall_courses(4.5,3.8,4.4,door=True)
        for x in [-2.2,2.2]:
            for y in [-1.9,1.9]: tower(x,y,.63,5.05)
        group('EntranceArch',arch(-1.94,.90,1.95,.28),.43,.66)
        group('KeepDeck',[k.box('upper_deck',(0,0,4.40),(4.5,3.8,.13),'wood_dark')],.58,.71)
        battlements(4.55,3.85,4.45)
        shutters=[]
        for side in [-1,1]:
            for z in [1.6,3.4]:
                shutters.append(k.box('arrow_slit',(side*1.43,-1.912,z),(.13,.022,.62),'wood_dark',0))
                shutters.append(k.box('slit_sill',(side*1.43,-1.96,z-.35),(.30,.14,.08),'stone_light'))
        group('ArrowSlits',shutters,.64,.83)
        flag(-.5,0,5.65,1.35,.75,base=4.4)
        group('RoofShelter',[k.box('shelter',(0,.5,4.8),(1.45,1.25,.68),'wood'),k.mesh('shelter_roof',[(-.9,-.25,5.1),(.9,-.25,5.1),(.9,1.25,5.1),(-.9,1.25,5.1),(0,.5,5.75)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)],'tile')],.72,.95,tier=2)
        socket('Entrance',(0,-2.65,0),'road')
    elif kind=='castle-wall':
        wall_courses(4.0,1.2,3.14)
        group('WallWalk',[k.box('wall_walk',(0,0,3.14),(4.0,1.2,.12),'stone_light')],.58,.71)
        battlements(4.0,1.2,3.2,open_ends=True)
        hoarding=[]
        for x in [-1.6,-.8,0,.8,1.6]:
            hoarding.append(k.beam('hoarding_bracket',(x,-.48,2.48),(x,-1.0,3.18),.06,'wood_dark',4))
            hoarding.append(k.box('hoarding_post',(x,-1.0,3.69),(.08,.08,1.05),'wood_dark'))
        hoarding.append(k.box('hoarding_floor',(0,-.77,3.19),(4.0,.60,.10),'wood'))
        hoarding.append(k.box('hoarding_cover',(0,-.70,4.27),(4.0,.94,.12),'wood_light'))
        group('TimberHoarding',hoarding,.65,.95,tier=2)
        flag(-.8,.25,4.3,.85,.50,base=3.18)
        socket('WallLeft',(-2,0,0),'wall'); socket('WallRight',(2,0,0),'wall')
    else:
        wall_courses(2.3,2.1,5.15,door=True,back_door=True)
        for x in [-1.82,1.82]: tower(x,0,.84,5.35)
        group('WallJoins',[k.box('wall_connector',(side*2.65,0,1.60),(.30,1.2,3.2),'stone',0) for side in [-1,1]],.22,.64)
        group('GateArches',arch(-1.09,.9,1.95,.30)+arch(1.09,.9,1.95,.30),.41,.68)
        deck=[k.box('gate_roof',(0,0,5.14),(2.3,2.1,.12),'stone_light'),
              k.box('front_walk',(0,-1.01,3.14),(2.3,.18,.12),'wood'),k.box('back_walk',(0,.32,3.14),(2.3,1.73,.12),'wood')]
        group('GateDeck',deck,.58,.72)
        battlements(2.35,2.15,5.2)
        bars=[]
        for i in range(9):
            x=-.80+i*.20
            bars.append(k.box('portcullis_bar',(x,-.74,1.48),(.065,.09,2.44),'iron',.008))
            bars.append(k.beam('bar_point',(x,-.74,.30),(x,-.74,.19),.047,'iron',4,0))
        for z in [.65,1.25,1.85,2.45]: bars.append(k.box('cross_bar',(0,-.74,z),(1.76,.12,.055),'wood_dark'))
        lift=group('Portcullis',bars,.76,.94,(0,-.74,.24),motion='lift')
        lift['gateTravel']=2.32
        bridge=[]
        for i in range(10): bridge.append(k.box('bridge_plank',(-.81+(i+.5)*1.62/10,-1.24,1.51),(1.62/10-.009,.10,2.50),'wood_light',.007))
        for z in [.52,2.49]: bridge.append(k.box('bridge_strap',(0,-1.31,z),(1.73,.055,.10),'iron'))
        bridge.append(k.beam('bridge_hinge',(-.94,-1.24,.26),(.94,-1.24,.26),.09,'iron',10))
        node=group('Drawbridge',bridge,.80,.96,(0,-1.24,.26),motion='bridge',axis=(1,0,0))
        node['bridgeLength']=2.5
        mounts=[]
        for side in [-1,1]:
            x=side*.79
            mounts.append(k.beam('chain_support',(x,-1.0,3.35),(x,-1.28,3.35),.045,'iron',6))
            mounts.append(k.beam('chain_pulley',(x-.05,-1.24,3.35),(x+.05,-1.24,3.35),.10,'iron',10))
            verts=[(x+dx,-1.24+dy,z) for z in [2.76,3.35] for dx,dy in [(-.015,-.015),(.015,-.015),(.015,.015),(-.015,.015)]]
            strap=k.mesh('suspension_chain',verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'iron')
            group('BridgeChain',[strap],.84,.98,motion='chain')
        group('ChainAnchors',mounts,.76,.92)
        flag(-1.82,0,5.95,.90,.56,base=5.33)
        flag(1.82,0,5.95,.90,.56,tier=2,base=5.33)
        socket('RoadFront',(0,-3.74,.26),'road'); socket('RoadBack',(0,1.32,.24),'road')
        socket('WallLeft',(-2.8,0,0),'wall'); socket('WallRight',(2.8,0,0),'wall')
        root['animationBoundsMin']=[-2.9,0,-1.35]
        root['animationBoundsMax']=[3.0,6.85,3.92]
    return root
