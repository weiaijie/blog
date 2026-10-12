"""Game-scale transport with separate rolling, steering and access mechanisms."""
import math
from mathutils import Vector

KINDS=('rickshaw','bicycle','early-car','freight-wagon')


def build(k,kind):
    b=k.bpy;rail=kind=='freight-wagon'
    colors={'rubber':'333D40','steel':'A2B0B3','paint':'487F78','car_paint':'994B50','canvas':'D4C6A0','leather':'765242','lamp':'E9D6A0','glass':'BCD9DE'}
    for name,code in colors.items():
        mat=k.M['iron'].copy();mat.name='transport_'+name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color=(*linear,1);shader=mat.node_tree.nodes['Principled BSDF'];shader.inputs['Base Color'].default_value=(*linear,1)
        shader.inputs['Metallic'].default_value=.65 if name=='steel' else .05
        shader.inputs['Roughness'].default_value=.4 if name in ['steel','paint','car_paint'] else .85
        if name=='glass':
            shader.inputs['Alpha'].default_value=.22;shader.inputs['Roughness'].default_value=.18
            mat.diffuse_color=(*linear,.22);mat.surface_render_method='DITHERED';mat.use_backface_culling=True
        k.M[name]=mat
    root=k.pivot('TransportRoot',(0,0,0),[]);root['vehicleKind']=kind
    root['routeProfile']='narrow-rail-0668-v1' if rail else 'road-145-v1'
    root['wheelbase']=1.2 if rail else 1.3 if kind=='early-car' else 1.15 if kind=='bicycle' else 0
    root['track']=.72 if rail else .96 if kind=='early-car' else 1.06 if kind=='rickshaw' else 0
    def attach(obj,parent=root):
        b.context.view_layer.update();world=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=world;return obj
    def box(name,pos,size,mat='iron',bevel=.008,parent=root):return attach(k.box(name,pos,size,mat,bevel),parent)
    def beam(name,a,c,w=.014,mat='iron',parent=root):return attach(k.beam(name,a,c,w,mat,8),parent)
    def pivot(name,pos,parent=root,**extras):
        node=attach(k.pivot(name,pos,[]),parent)
        for key,value in extras.items():node[key]=value
        return node
    def ring(name,pos,r,thick,width,mat,parent=root,segments=24):
        vertices=[]
        for x in [-width/2,width/2]:
            for radius in [r-thick,r]:
                for i in range(segments):
                    a=i*math.tau/segments;vertices.append((pos[0]+x,pos[1]+math.sin(a)*radius,pos[2]+math.cos(a)*radius))
        faces=[]
        for i in range(segments):
            j=(i+1)%segments
            for a,c in [(0,segments),(segments,3*segments),(3*segments,2*segments),(2*segments,0)]:faces.append((a+i,a+j,c+j,c+i))
        return attach(k.mesh(name,vertices,faces,mat),parent)
    def wheel(x,y,r,width,spokes=12,parent=root,style='road'):
        node=pivot('RollingWheel',(x,y,r),parent,vehicleWheel=True,wheelRadius=r,wheelSide=x)
        ring('tread',(x,y,r),r,.024 if style=='bike' else .045,width,'steel' if style=='rail' else 'rubber',node)
        ring('rim',(x,y,r),r-.025 if style=='bike' else r-.038,.018,width*.72,'steel' if style in ['bike','rail'] else 'wood_light',node)
        beam('hub',(x-width*.7,y,r),(x+width*.7,y,r),.027 if style=='bike' else .06,'steel',node)
        for i in range(spokes):
            angle=i*math.tau/spokes
            beam('spoke',(x,y,r),(x,y+math.sin(angle)*(r-.04),r+math.cos(angle)*(r-.04)),.0045 if style=='bike' else .012,'steel' if style in ['bike','rail'] else 'wood_light',node)
        if style=='rail':ring('inner_flange',(x-math.copysign(.038,x),y,r),r+.017,.06,.018,'steel',node)
        return node
    def cargo(pos,size,index,parent=root):
        node=pivot('Cargo',pos,parent,vehicleCargo=index)
        box('crate',pos,size,'wood',.008,node)
        for z in [-.28,.28]:box('crate_band',(pos[0],pos[1],pos[2]+z*size[2]),(size[0]+.012,size[1]+.012,.025),'iron',.002,node)
        beam('crate_brace',(pos[0]-size[0]*.4,pos[1]-size[1]/2-.01,pos[2]-size[2]*.4),(pos[0]+size[0]*.4,pos[1]-size[1]/2-.01,pos[2]+size[2]*.4),.014,'wood_light',node)
    def axle(y,z,width):beam('axle',(-width,y,z),(width,y,z),.032,'iron')
    if kind=='bicycle':
        rear=(0,.6,.30);front=(0,-.55,.30);crank=(0,.12,.30);seat=(0,.23,.83);head=(0,-.55,.83)
        rear_wheel=wheel(0,.6,.30,.035,20,style='bike')
        steering=pivot('SteeringFork',front,vehicleSteer=True,steerSide=0)
        wheel(0,-.55,.30,.035,20,steering,'bike')
        for a,c in [(crank,seat),(seat,head),(head,crank)]:beam('diamond_frame',a,c,.021,'paint')
        for side in [-1,1]:
            rr=(side*.044,rear[1],rear[2]);beam('seat_stay',seat,rr,.012,'paint');beam('chain_stay',crank,rr,.012,'paint')
            beam('fork_leg',(side*.05,-.55,.66),(side*.045,-.55,.30),.014,'steel',steering)
        beam('head_tube',(0,-.55,.67),(0,-.55,.91),.026,'paint')
        beam('handle_stem',(0,-.55,.80),(0,-.55,1.02),.017,'steel',steering)
        beam('handlebar',(-.25,-.55,1.02),(.25,-.55,1.02),.013,'steel',steering)
        for side in [-1,1]:beam('handle_grip',(side*.17,-.55,1.02),(side*.27,-.55,1.02),.022,'rubber',steering)
        beam('seat_post',seat,(0,.23,.94),.014,'steel');box('saddle',(0,.24,.945),(.17,.26,.045),'leather',.014)
        drive=pivot('Crank',crank,vehicleCrank=True,gearRatio=2.5)
        ring('chainring',(.065,.12,.30),.12,.025,.012,'steel',drive)
        beam('crank_shaft',(-.11,.12,.30),(.11,.12,.30),.019,'steel',drive)
        for i in range(3):
            a=i*math.tau/3;beam('chainring_arm',(.065,.12,.30),(.065,.12+math.sin(a)*.10,.30+math.cos(a)*.10),.012,'steel',drive)
        ring('rear_sprocket',(.065,.6,.30),.048,.018,.012,'steel',rear_wheel)
        for side in [-1,1]:
            p=(side*.10,.12+side*.13,.30)
            beam('crank_arm',(side*.10,.12,.30),p,.013,'steel',drive)
            pedal=pivot('Pedal',p,drive,vehiclePedal=True)
            box('pedal_tread',p,(.09,.07,.025),'rubber',.004,pedal)
        angle=math.acos((.12-.048)/.48);points=[]
        for i in range(33):
            a=angle+(math.tau-2*angle)*i/32;points.append((.065,.12+math.cos(a)*.12,.30+math.sin(a)*.12))
        for i in range(17):
            a=-angle+2*angle*i/16;points.append((.065,.6+math.cos(a)*.048,.30+math.sin(a)*.048))
        path=[[x,z,-y] for x,y,z in points];root['chainPath']=path;root['rearSprocketRadius']=.048
        for i in range(56):
            node=pivot('ChainLink',points[0],vehicleChain=i/56)
            box('chain_plate',points[0],(.018,.012,.027),'iron',0,node)
        beam('rear_rack_post',(-.06,.6,.30),(-.06,.54,.68),.009,'steel');beam('rear_rack_post',(.06,.6,.30),(.06,.54,.68),.009,'steel')
        box('rear_rack',(0,.61,.69),(.22,.32,.023),'iron',.002)
    elif kind=='rickshaw':
        for side in [-1,1]:wheel(side*.53,.08,.42,.055,16)
        axle(.08,.42,.58)
        box('footboard',(0,-.37,.27),(.72,.37,.045),'wood')
        box('seat_base',(0,.18,.54),(.80,.69,.12),'paint',.025)
        box('seat_cushion',(0,.13,.635),(.7,.46,.07),'leather',.028)
        box('back_cushion',(0,.48,.85),(.7,.08,.46),'leather',.025)
        for side in [-1,1]:
            beam('shaft',(side*.40,.34,.39),(side*.37,-1.45,.61),.027,'wood')
            beam('hand_grip',(side*.37,-1.45,.61),(side*.37,-1.63,.64),.03,'leather')
            beam('step_support',(side*.32,-.35,.28),(side*.32,.12,.48),.027,'iron')
            beam('armrest_post',(side*.39,-.11,.56),(side*.39,-.11,.89),.02,'paint')
            beam('armrest',(side*.39,-.16,.89),(side*.39,.46,.89),.026,'wood_light')
        # Radial ribs and cloth collapse around their shared rear hinge, not a shrinking roof.
        anchor=(0,.48,.87);angles=[-1.20+i*1.40/4 for i in range(5)]
        for angle in angles:
            rib=pivot('CanopyRib',anchor,vehicleCanopy=angle)
            points=[(x,.48+math.sin(angle)*(.79+.07*(1-abs(x)/.43)),.87+math.cos(angle)*(.79+.07*(1-abs(x)/.43))) for x in [-.43,0,.43]]
            for i in range(2):beam('canopy_rib',points[i],points[i+1],.011,'wood_light',rib)
            for side in [-1,1]:beam('canopy_arm',(side*.43,.48,.87),points[0 if side<0 else 2],.011,'iron',rib)
        vertices=[]
        for i in range(17):
            a=-1.2+1.4*i/16
            for x in [-.43,-.215,0,.215,.43]:
                r=.79+.07*(1-abs(x)/.43);vertices.append((x,.48+math.sin(a)*r,.87+math.cos(a)*r))
        fabric=pivot('CanopyFabric',anchor,vehicleCanopySurface=True)
        # Store cloth vertices around the hinge itself so runtime folding and ribs use the same origin.
        cloth=k.mesh('folding_canvas',[tuple(Vector(p)-Vector(anchor)) for p in vertices],[(i*5+j,i*5+j+1,(i+1)*5+j+1,(i+1)*5+j) for i in range(16) for j in range(4)],'canvas')
        cloth.location=anchor;attach(cloth,fabric)
    elif kind=='early-car':
        for y in [-.65,.65]:
            axle(y,.25,.54)
            for side in [-1,1]:
                parent=pivot('SteeringKnuckle',(side*.48,y,.25),vehicleSteer=True,steerSide=side) if y<0 else root
                wheel(side*.48,y,.25,.10,12,parent)
        box('chassis',(0,0,.35),(.74,1.8,.10),'iron',.012)
        box('hood',(0,-.48,.64),(.67,.65,.44),'car_paint',.035)
        box('radiator',(0,-.827,.63),(.62,.055,.39),'gold',.018)
        for x in range(-5,6):box('radiator_fins',(x*.046,-.859,.63),(.014,.012,.31),'iron',.001)
        box('floor',(0,.38,.47),(.82,1.04,.10),'car_paint')
        box('rear_body',(0,.88,.65),(.84,.07,.42),'car_paint',.015)
        for y in [.17,.64]:
            box('seat',(0,y,.65),(.70,.28,.10),'leather',.025)
            box('seat_back',(0,y+.15,.82),(.70,.055,.32),'leather',.02)
        for side in [-1,1]:
            box('running_board',(side*.51,.02,.32),(.18,.68,.045),'rubber')
            for y in [-.65,.65]:
                points=[(side*.49,y+math.cos(a)*.29,.25+math.sin(a)*.29) for a in [math.pi*i/10 for i in range(11)]]
                vertices=[(p[0]+dx,p[1],p[2]) for p in points for dx in [-.095,.095]]
                attach(k.mesh('wheel_fender',vertices,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(10)],'car_paint'))
            door=pivot('PassengerDoor',(side*.419,-.04,.49),vehicleAccess=True,accessAxis=[0,1,0],accessAngle=-side*1.05)
            box('door_panel',(side*.419,.16,.67),(.036,.39,.36),'car_paint',.016,door)
            beam('door_handle',(side*.448,.25,.79),(side*.448,.33,.79),.011,'gold',door)
            beam('windshield_post',(side*.36,-.13,.7),(side*.36,-.13,1.18),.014,'gold')
            beam('roof_post',(side*.37,.83,.69),(side*.37,.83,1.23),.018,'iron')
            beam('headlamp_shell',(side*.38,-.78,.75),(side*.38,-.88,.75),.085,'gold')
            beam('headlamp_lens',(side*.38,-.881,.75),(side*.38,-.894,.75),.07,'lamp')
        beam('windshield_top',(-.36,-.13,1.18),(.36,-.13,1.18),.014,'gold')
        beam('windshield_bottom',(-.36,-.13,.91),(.36,-.13,.91),.014,'gold')
        box('windshield',(0,-.13,1.04),(.69,.008,.23),'glass',0)
        vertices=[(x,y,1.245+.055*(1-abs(x)/.43)) for y in [-.205,.38,.965] for x in [-.43,-.215,0,.215,.43]]
        attach(k.mesh('arched_fabric_roof',vertices,[(i*5+j,i*5+j+1,(i+1)*5+j+1,(i+1)*5+j) for i in range(2) for j in range(4)],'canvas'))
        for y in [-.195,.95]:
            points=[(x,y,1.235+.055*(1-abs(x)/.43)) for x in [-.43,-.215,0,.215,.43]]
            for i in range(4):beam('roof_bow',points[i],points[i+1],.011,'wood_dark')
        beam('steering_column',(-.18,-.12,.57),(-.18,.01,.91),.016,'iron')
        steering=pivot('SteeringWheel',(-.18,.01,.91),vehicleSteeringWheel=True)
        # Horizontal steering rim with three spokes.
        points=[(-.18+math.cos(i*math.tau/20)*.115,.01+math.sin(i*math.tau/20)*.115,.91) for i in range(21)]
        for i in range(20):beam('steering_rim',points[i],points[i+1],.012,'wood_dark',steering)
        for i in [0,7,14]:beam('steering_spoke',(-.18,.01,.91),points[i],.008,'iron',steering)
        cargo((0,.94,.96),(.52,.24,.22),0)
    else:
        for y in [-.60,.60]:
            axle(y,.22,.44)
            for side in [-1,1]:
                wheel(side*.36,y,.22,.07,8,style='rail')
                box('axle_box',(side*.405,y,.28),(.10,.17,.12),'iron')
                for j in range(3):box('leaf_spring',(side*.405,y,.38+j*.016),(.045,.42-j*.06,.012),'steel',.001)
        box('underframe',(0,0,.43),(.86,1.68,.12),'iron')
        for i in range(9):box('deck_plank',(0,-.72+i*.18,.51),(.90,.172,.045),'wood_light',.004)
        for side in [-1,1]:
            door=pivot('DropSide',(side*.46,0,.535),vehicleAccess=True,accessAxis=[0,0,1],accessAngle=-side*1.52)
            for row in range(3):box('side_plank',(side*.46,0,.60+row*.12),(.035,1.62,.112),'paint',.004,door)
            for y in [-.72,0,.72]:box('side_strap',(side*.486,y,.725),(.018,.048,.40),'iron',.003,door)
        for end in [-1,1]:
            for row in range(3):box('end_plank',(0,end*.825,.60+row*.12),(.90,.035,.112),'paint',.004)
            for side in [-1,1]:
                box('corner_post',(side*.45,end*.825,.71),(.065,.065,.43),'iron')
                beam('buffer',(side*.30,end*.85,.46),(side*.30,end*1.04,.46),.045,'iron')
                box('buffer_plate',(side*.30,end*1.04,.46),(.13,.035,.13),'steel')
            beam('drawbar',(0,end*.81,.42),(0,end*1.09,.42),.03,'iron')
            port=pivot('Coupler',(0,end*1.10,.42),vehicleCoupler=end)
            port['normalGltf']=[0,0,-end]
        for i in range(6):cargo(((-.22 if i%2==0 else .22),-.50+(i//2)*.48,.70),(.36,.38,.30),i)
        beam('brake_lever',(.51,-.6,.24),(.51,.3,.42),.012,'iron')
    root['cargoSlots']=6 if rail else 1 if kind=='early-car' else 0
    root['accessKind']='canopy' if kind=='rickshaw' else 'doors' if kind=='early-car' else 'sides' if rail else ''
