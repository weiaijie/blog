"""Compact railway stop and belt-driven workshop with real service clearances."""
import math
from mathutils import Vector
from map_element_buildings import build_group, connection


def build(k, kind):
    root = k.pivot('BuildingRoot', (0, 0, 0), [])
    root['buildingType'] = kind
    for name, code in {'brick':'AD7363','brick_light':'C28B78','slate':'596F78',
                       'glass':'91B9B8','ivory':'DDDCCA','steel':'AFBBBA','red':'BF554A',
                       'rubber':'454A48','machine':'588A7F'}.items():
        mat = k.M['stone'].copy(); mat.name = 'industry_'+name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color = (*linear, 1)
        shader = mat.node_tree.nodes['Principled BSDF']; shader.inputs['Base Color'].default_value = (*linear, 1)
        shader.inputs['Metallic'].default_value = .45 if name == 'steel' else 0
        k.M[name] = mat
    def box(n,p,s,m='brick',bevel=.008): return k.box(n,p,s,m,bevel)
    def beam(n,a,b,r=.025,m='iron',sides=8): return k.beam(n,a,b,r,m,sides)
    def group(n,parts,start,full,anchor=(0,0,0),**kw): return build_group(k,root,n,parts,start,full,anchor,**kw)
    def port(n,p,role,normal):
        node=connection(k,root,n,p,role);node['normalGltf']=normal
        return node
    def ring(n,cx,y,z,r,width,mat='steel',thickness=.045):
        verts=[(cx+radius*math.cos(i*math.tau/32),y+dy,z+radius*math.sin(i*math.tau/32)) for dy in [-width/2,width/2] for radius in [r-thickness,r] for i in range(32)]
        faces=[(a+i,a+(i+1)%32,b+(i+1)%32,b+i) for a,b in [(0,32),(32,96),(96,64),(64,0)] for i in range(32)]
        return k.mesh(n,verts,faces,mat)
    def roof_panel(n,points,start,full,mat='slate',tier=1):
        normal=(Vector(points[1])-Vector(points[0])).cross(Vector(points[2])-Vector(points[0])).normalized()
        if normal.z<-.01 or (abs(normal.z)<.01 and normal.x<0): normal=-normal
        verts=points+[tuple(Vector(p)-normal*.045) for p in points]
        obj=k.mesh(n,verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],mat)
        obj['inspectionCover']=True
        return group(n,[obj],start,full,tier=tier)
    def scaffold(x):
        group('Scaffold',[beam('scaffold_post',(x,y,0),(x,y,2.45),.045) for y in [-1,1]]+[box('scaffold_board',(x,0,1.25),(.36,2.35,.06),'wood')],.22,.38,temporary=True)
    if kind == 'train-station':
        # Track dimensions match rail-track and the existing game-scale rolling stock.
        root['railCenterSpacing']=.72;root['gauge']=.668;root['routeProfile']='narrow-rail-0668-v1'
        group('Foundation',[box('station_base',(-1.10,0,.10),(3.55,7.6,.20),'stone')],0,.12)
        group('TrackBallast',[box('ballast_bed',(1.4,0,.08),(1.40,7.6,.16),'stone')],.06,.18)
        for course in range(4):
            parts=[]
            for i in range(8):
                y=-3.7+(course*8+i)*7.4/31
                parts.append(box('sleeper',(1.4,y,.18),(1.18,.13,.06),'wood_dark'))
                for x in [1.04,1.76]: parts.append(box('rail_chair',(x,y,.214),(.12,.075,.025),'iron'))
            group('TrackSleepers',parts,.14+course*.035,.23+course*.035)
        for course in range(4):
            parts=[];y=-2.85+course*1.90
            for x in [1.04,1.76]:
                parts.extend([box('rail_foot',(x,y,.228),(.092,1.9,.018),'steel',0),box('rail_web',(x,y,.246),(.026,1.9,.030),'iron',0),box('rail_head',(x,y,.27),(.052,1.9,.020),'steel',0)])
            group('RailCourse',parts,.24+course*.035,.34+course*.035)
        for side in [-1,1]:
            node=port('RailPort',(1.4,side*3.8,.28),'rail',(0,0,-side));node['profile']='narrow-rail-0668-v1'
        for i in range(6):
            y=-2.1+(i+.5)*5.7/6
            parts=[box('platform_course',(-1.08,y,.345),(3.52,5.7/6-.008,.29),'stone'),box('platform_edge',(.56,y,.505),(.23,5.7/6-.008,.04),'ivory')]
            for j in range(3):parts.append(box('platform_paver',(-2.45+j*.96,y,.505),(.94,5.7/6-.015,.035),'stone_light'))
            group('PlatformCourse',parts,.12+i*.025,.22+i*.025)
        ramp=k.mesh('platform_access_ramp',[(-.45,-3.8,.20),(.68,-3.8,.20),(.68,-2.1,.49),(-.45,-2.1,.49),(-.45,-2.1,.20),(.68,-2.1,.20)],[(0,1,2,3),(0,3,4),(1,5,2),(4,3,2,5),(0,4,5,1)],'stone_light')
        group('PlatformRamp',[ramp],.18,.30)
        port('PedestrianEntrance',(.1,-3.8,.20),'road',(0,0,1))
        port('BoardingSlot',(.43,0,.525),'passenger',(1,0,0))
        for row in range(7):
            z=.64+row*.24;parts=[]
            for y in [-1.8,1.8]:
                for x in [-2.61,-2.18,-1.75,-1.32,-.89]:
                    if row<5 and -1.95<x<-.95: continue
                    parts.append(box('station_brick',(x,y,z),(.415,.16,.23),'brick_light' if (row+int(x*10))%4==0 else 'brick'))
            for i in range(9):parts.append(box('back_wall_brick',(-2.84,-1.61+i*.40,z),(.16,.385,.23)))
            group('StationWallCourse',parts,.23+row*.04,.33+row*.04)
        # Open waiting-room arcade onto the platform, with glazing above a low side panel.
        frame=[]
        for y in [-1.8,-.65,.65,1.8]:
            frame.extend([beam('arcade_post',(-.66,y,.525),(-.66,y,2.27),.055,'teal'),beam('bracket',(-.66,y,1.97),(-.30,y,2.26),.025,'teal')])
        frame.append(beam('platform_wall_plate',(-.66,-1.9,2.28),(-.66,1.9,2.28),.06,'teal'))
        group('WaitingRoomArcade',frame,.41,.58)
        for side in [-1,1]:
            group('DoorFrame',[box('door_jamb',(x,side*1.81,1.15),(.10,.22,1.30),'ivory') for x in [-1.96,-1.12]]+[box('door_lintel',(-1.54,side*1.81,1.86),(.94,.22,.13),'ivory')],.48,.63)
        benches=[]
        for y in [-.90,.85]:
            for j in range(4):benches.append(box('bench_seat',(-2.44+j*.10,y,.82),(.085,.98,.045),'wood_light'))
            for dy in [-.38,.38]:benches.append(beam('bench_leg',(-2.26,y+dy,.52),(-2.26,y+dy,.82),.035))
            for z in [.96,1.10]:benches.append(box('bench_back',(-2.62,y,z),(.035,.98,.09),'wood'))
            for dy in [-.4,.4]:benches.append(beam('back_support',(-2.62,y+dy,.52),(-2.62,y+dy,1.15),.026))
        group('WaitingBenches',benches,.66,.81)
        for row in range(5):
            for side in [-1,1]:
                x0=-1.74+side*1.20*row/5;x1=-1.74+side*1.20*(row+1)/5
                z0=2.97-.67*row/5;z1=2.97-.67*(row+1)/5
                roof_panel('StationRoof',[(x0,-1.98,z0),(x1,-1.98,z1),(x1,1.98,z1),(x0,1.98,z0)],.60+row*.035,.69+row*.035)
        trusses=[]
        for y in [-1.8,0,1.8]:
            trusses.append(beam('tie_beam',(-2.84,y,2.22),(-.64,y,2.22),.05,'wood_dark'))
            for x in [-2.84,-.64]:trusses.append(beam('roof_rafter',(-1.74,y,2.87),(x,y,2.25),.04,'wood_dark'))
        group('RoofTrusses',trusses,.50,.64)
        for i in range(6):
            y=-3.15+i*1.05
            roof_panel('PlatformCanopy',[(-.57,y,2.31),(.60,y,2.18),(.60,y+1.05,2.18),(-.57,y+1.05,2.31)],.65+i*.025,.75+i*.025,'glass')
        canopy=[]
        for y in [-3.05,-1.65,1.65,3.05]:
            canopy.extend([beam('canopy_column',(-.49,y,.20 if y< -2.1 else .52),(-.49,y,2.23),.032,'teal'),beam('canopy_cantilever',(-.52,y,2.25),(.61,y,2.12),.035,'teal'),beam('canopy_brace',(-.49,y,1.92),(.24,y,2.16),.022,'teal')])
        canopy.append(beam('canopy_edge',(.60,-3.16,2.14),(.60,3.16,2.14),.03,'teal'))
        group('PlatformCanopyFrame',canopy,.52,.67)
        clock=(-1.74,-2.03,2.60)
        parts=[beam('clock_face',(clock[0],clock[1],clock[2]),(clock[0],clock[1]-.055,clock[2]),.24,'ivory',32),ring('clock_rim',clock[0],clock[1]-.04,clock[2],.25,.045,'gold',.023)]
        for i in range(12):
            a=i*math.tau/12
            parts.append(beam('clock_tick',(clock[0]+.19*math.sin(a),clock[1]-.077,clock[2]+.19*math.cos(a)),(clock[0]+.218*math.sin(a),clock[1]-.077,clock[2]+.218*math.cos(a)),.008))
        parts.append(beam('clock_hanger',(-1.74,-2.03,2.83),(-1.74,-1.97,2.97),.025,'iron'))
        group('ClockDial',parts,.82,.93)
        for n,length,rate,y in [('MinuteHand',.18,1.2,-2.12),('HourHand',.12,.1,-2.14)]:
            group(n,[beam('clock_hand',(-1.74,y,2.60),(-1.74,y,2.60+length),.013)],.88,.98,(-1.74,y,2.60),motion='spin',axis=(0,1,0),rate=rate)
        # Lower-quadrant semaphore: a hinged blade and counterweight, not a waving flag.
        group('SignalMast',[beam('signal_post',(2.39,-2.7,.16),(2.39,-2.7,2.63),.043,'ivory'),box('signal_foot',(2.39,-2.7,.14),(.28,.28,.28),'stone')],.60,.78)
        parts=[box('signal_blade',(2.78,-2.7,2.47),(.78,.065,.15),'red'),box('signal_band',(2.91,-2.743,2.47),(.11,.024,.155),'ivory'),beam('counterweight_arm',(2.17,-2.7,2.47),(2.39,-2.7,2.47),.025),box('counterweight',(2.18,-2.7,2.47),(.13,.10,.17),'iron')]
        group('SemaphoreArm',parts,.82,.96,(2.39,-2.7,2.47),motion='semaphore',axis=(0,1,0))
        lamps=[]
        for y in [-2.65,2.65]:
            lamps.extend([beam('lamp_post',(-1.50,y,.20 if y< -2.1 else .52),(-1.50,y,1.91),.025,'teal'),box('lamp_glass',(-1.50,y,1.99),(.17,.17,.21),'ivory'),box('lamp_cap',(-1.50,y,2.12),(.23,.23,.05),'teal')])
        for i in range(3):
            lamps.extend([box('luggage_crate',(-2.27+i*.45,2.75,.76),(.38,.40,.46),'wood'),box('luggage_strap',(-2.27+i*.45,2.75,.76),(.045,.42,.48),'iron')])
        group('PlatformAmenities',lamps,.86,.99,tier=2)
        scaffold(-3.13)
        root['animationBoundsMin']=[-3.4,0,-3.9];root['animationBoundsMax']=[3.3,3.2,3.9]
    else:
        group('Foundation',[box('factory_slab',(0,0,.11),(6.4,4.6,.22),'stone')],0,.12)
        for row in range(6):
            parts=[];z=.35+row*.29
            for side in [-1,1]:
                for j in range(10):
                    y=-1.98+j*.44
                    if side<0 and abs(y)<.9: continue
                    parts.append(box('side_wall_brick',(side*3,y,z),(.18,.42,.275),'brick_light' if j%4==row%4 else 'brick'))
            for j in range(12):parts.append(box('rear_brick',(-2.75+j*.50,2.08,z),(.48,.18,.275)))
            for x in [-2.76,2.76]:parts.append(box('front_pier',(x,-2.08,z),(.46,.22,.275)))
            group('FactoryMasonryCourse',parts,.12+row*.06,.24+row*.06)
        frame=[]
        for y in [-2.05,0,2.05]:
            for x in [-3,-1,1,3]:
                if x==-3 and y==0: continue
                frame.append(beam('steel_post',(x,y,.22),(x,y,2.47),.045,'teal'))
            frame.append(beam('roof_tie',(-3,y,2.4),(3,y,2.4),.055,'teal'))
        for y in [-.90,.90]:frame.append(beam('cargo_jamb',(-3,y,.22),(-3,y,2.47),.045,'teal'))
        group('SteelFrame',frame,.38,.56)
        for side in [-1,1]:
            parts=[]
            for j in range(6):
                x=-2.5+j
                parts.extend([box('clerestory_glass',(x,side*2.09,2.12),(.93,.045,.40),'glass',0),box('window_mullion',(x-.49,side*2.10,2.12),(.04,.08,.46),'ivory')])
            parts.append(box('window_sill',(0,side*2.10,1.895),(6.04,.15,.10),'ivory'))
            group('ClerestoryWindows',parts,.52,.69)
            side_windows=[]
            for j in range(6):
                y=-1.75+j*.70
                side_windows.extend([box('side_clerestory',(side*3,y,2.16),(.045,.65,.46),'glass',0),box('side_mullion',(side*3,y-.34,2.17),(.07,.04,.50),'ivory')])
            side_windows.append(box('side_sill',(side*3,0,1.90),(.17,4.2,.09),'ivory'))
            group('SideWindows',side_windows,.53,.70)
        for bay in range(3):
            x=-3+bay*2
            for row in range(4):
                a=x+row*.5;b=a+.5;za=2.48+row*.20;zb=za+.20
                roof_panel('SawtoothRoof',[(a,-2.24,za),(b,-2.24,zb),(b,2.24,zb),(a,2.24,za)],.60+bay*.04+row*.013,.70+bay*.04+row*.013)
            roof_panel('Northlight',[(x+2,-2.24,2.50),(x+2,-2.24,3.28),(x+2,2.24,3.28),(x+2,2.24,2.50)],.73+bay*.035,.84+bay*.035,'glass')
            ribs=[]
            for y in [-2.23,-1.1,0,1.1,2.23]:
                ribs.extend([beam('sawtooth_rafter',(x,y,2.42),(x+2,y,3.22),.035,'teal'),beam('northlight_mullion',(x+2,y,2.47),(x+2,y,3.25),.025,'ivory')])
            group('SawtoothTruss',ribs,.52+bay*.025,.65+bay*.025)
            for side in [-1,1]:
                y=side*2.23
                vertices=[(xx,y+dy,zz) for dy in [-.018,.018] for xx,zz in [(x,2.48),(x+2,2.48),(x+2,3.28)]]
                glass=k.mesh('gable_glazing',vertices,[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],'glass');glass['inspectionCover']=True
                group('GableGlazing',[glass],.74+bay*.035,.85+bay*.035)
        # Equal-radius pulleys keep a closed, constant-length belt with matching surface speeds.
        cx,cz,r=-1.35,1.1,.38
        machine=[box('motor_plinth',(cx,.64,.40),(1.10,1.35,.36),'stone'),beam('motor_housing',(cx,.20,cz),(cx,1.20,cz),.36,'machine',20)]
        for y in [.31,.45,.59,.73,.87,1.01]:machine.append(beam('cooling_fin',(cx,y,cz),(cx,y+.03,cz),.395,'teal',20))
        for x in [cx-.28,cx+.28]:machine.append(box('motor_foot',(x,.65,.64),(.13,.92,.18),'machine'))
        machine.append(beam('motor_shaft',(cx,-1.75,cz),(cx,.28,cz),.05,'steel'))
        group('MotorAndBearings',machine,.50,.72)
        group('FrontBearing',[beam('bearing_pedestal',(cx,-1.63,.22),(cx,-1.63,.99),.10,'machine'),ring('bearing_sleeve',cx,-1.63,cz,.125,.22,'machine',.070)],.50,.72)
        fly=[ring('flywheel',cx,-1.38,cz,.69,.12,'machine',.075)]
        for i in range(8):
            a=i*math.tau/8;fly.append(beam('flywheel_spoke',(cx,-1.38,cz),(cx+.625*math.cos(a),-1.38,cz+.625*math.sin(a)),.035,'machine'))
        group('Flywheel',fly,.72,.87,(cx,-1.38,cz),motion='spin',axis=(0,1,0),rate=1.8)
        for x in [-1.35,1.35]:
            parts=[ring('belt_pulley',x,-.94,cz,r,.17,'steel',.045)]
            for i in range(6):
                a=i*math.tau/6;parts.append(beam('pulley_spoke',(x,-.94,cz),(x+r*.9*math.cos(a),-.94,cz+r*.9*math.sin(a)),.02,'iron'))
            group('BeltPulley',parts,.68,.85,(x,-.94,cz),motion='spin',axis=(0,1,0),rate=1.8)
        path=[]
        for i in range(33):
            a=-math.pi/2+i*math.pi/32;path.append((1.35+r*math.cos(a),cz+r*math.sin(a)))
        for i in range(33):
            a=math.pi/2+i*math.pi/32;path.append((-1.35+r*math.cos(a),cz+r*math.sin(a)))
        belt=k.mesh('endless_drive_belt',[(x,y,z) for y in [-1.035,-.845] for x,z in path],[(i,(i+1)%66,(i+1)%66+66,i+66) for i in range(66)],'rubber')
        group('DriveBelt',[belt],.75,.90)
        for i in range(8):
            length=5.4+math.tau*r;s=i*length/8;arc=math.pi*r
            if s<arc:
                a=-math.pi/2+s/r;x=1.35+r*math.cos(a);z=cz+r*math.sin(a);a+=math.pi/2
            elif s<arc+2.7: x=1.35-(s-arc);z=cz+r;a=math.pi
            elif s<2*arc+2.7:
                a=math.pi/2+(s-arc-2.7)/r;x=-1.35+r*math.cos(a);z=cz+r*math.sin(a);a+=math.pi/2
            else: x=-1.35+s-2*arc-2.7;z=cz-r;a=0
            p=(x,-.94,z)
            node=group('BeltSplice',[box('belt_stitch',p,(.045,.197,.018),'ivory',0)],.76,.91,p,motion='belt-loop')
            node.rotation_euler.y=-a
            node['beltCenters']=[-1.35,1.35];node['beltRadius']=r;node['beltHeight']=cz;node['beltDepth']=.94;node['beltPhase']=i/8;node['beltSpeed']=1.8*r
        lathe=[box('lathe_bed',(1.35,.08,.70),(.92,1.79,.16),'machine'),beam('driven_shaft',(1.35,-1.09,cz),(1.35,.98,cz),.038,'steel')]
        for y in [-.53,.68]:
            for x in [1.04,1.66]:lathe.append(beam('lathe_leg',(x,y,.22),(x,y,.65),.065,'machine'))
        for y in [-.52,.72]:lathe.append(box('lathe_headstock',(1.35,y,.96),(.43,.24,.48),'machine'))
        lathe.append(box('tool_slide',(1.74,.11,.89),(.30,.35,.21),'steel'))
        lathe.append(beam('cutting_tool',(1.74,.11,1.13),(1.46,.11,1.13),.018,'iron'))
        group('LatheFrame',lathe,.60,.80)
        turning=[beam('workpiece',(1.35,-.33,cz),(1.35,.53,cz),.12,'wood_light',12),beam('chuck',(1.35,-.42,cz),(1.35,-.29,cz),.19,'iron',12)]
        for i in range(3):
            a=i*math.tau/3;turning.append(box('chuck_jaw',(1.35+.13*math.cos(a),-.28,cz+.13*math.sin(a)),(.055,.07,.055),'steel'))
        group('LatheSpindle',turning,.76,.91,(1.35,0,cz),motion='spin',axis=(0,1,0),rate=1.8)
        # A facade extractor gives the complete exterior a readable operating detail.
        fan=[ring('vent_rim',0,-2.18,2.13,.22,.10,'steel',.03)]
        group('VentHousing',fan,.82,.94)
        blades=[]
        for i in range(5):
            a=i*math.tau/5
            blades.append(k.mesh('fan_blade',[(0,-2.245,2.13),(.19*math.cos(a),-2.245,2.13+.19*math.sin(a)),(.17*math.cos(a+.5),-2.245,2.13+.17*math.sin(a+.5))],[(0,1,2)],'iron'))
        group('ExtractorFan',blades,.88,.98,(0,-2.245,2.13),motion='spin',axis=(0,1,0),rate=4.2)
        dock=[box('loading_apron',(-3.70,.6,.18),(1.24,2.3,.36),'stone')]
        for i in range(8):dock.append(box('pallet_slat',(-3.65,.25+i*.19,.40),(.95,.16,.065),'wood_light'))
        for z in [.65,1.09]:
            for y in [.67,1.27]:
                dock.extend([box('finished_crate',(-3.65,y,z),(.70,.55,.44),'wood'),box('crate_band',(-3.65,y,z),(.035,.57,.46),'iron')])
        group('LoadingDock',dock,.85,.99,tier=2)
        roof_panel('LoadingCanopy',[(-4.36,-.64,1.87),(-3,-.64,2.12),(-3,1.84,2.12),(-4.36,1.84,1.87)],.87,.99,'teal',tier=2)
        group('DockColumns',[beam('dock_column',(-4.24,y,.36),(-4.24,y,1.87),.036,'teal') for y in [-.55,1.75]],.77,.90,tier=2)
        port('FactoryEntrance',(0,-2.38,.22),'road',(0,0,1))
        port('CargoPort',(-4.35,-.22,.36),'cargo',(-1,0,0))
        port('LatheWorkplace',(2.1,.10,.22),'craft',(-1,0,0))
        scaffold(3.4)
        root['animationBoundsMin']=[-4.55,0,-2.65];root['animationBoundsMax']=[3.75,3.55,2.65]
