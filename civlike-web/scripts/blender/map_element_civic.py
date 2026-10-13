"""Gallery inn and small chapel: usable circulation, hollow bell and editable parts."""
import math
from map_element_buildings import build_group, connection


def build(k, kind):
    inn = kind == 'inn'
    root = k.pivot('BuildingRoot', (0, 0, 0), [])
    root['buildingType'] = kind
    for name, code in {'plaster':'DDD8C9', 'slate':'577582', 'glass':'6199AC', 'glass_red':'BC6575', 'bronze':'B48B46'}.items():
        mat = k.M['wood'].copy(); mat.name = 'civic_'+name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        linear = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear, 1)
        if name == 'bronze':
            mat.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = .45
        k.M[name] = mat

    def group(name, objects, start, full, anchor=(0,0,0), **kw):
        return build_group(k, root, name, objects, start, full, anchor, **kw)
    def box(n,p,s,m='wood',b=.01): return k.box(n,p,s,m,b)
    def beam(n,a,b,r=.035,m='wood_dark',s=6): return k.beam(n,a,b,r,m,s)
    def socket(name,p,role,normal=(0,0,1)):
        node=connection(k,root,name,p,role);node['normalGltf']=normal
        return node
    def wall(name, horizontal, fixed, low, high, bottom, top, openings, material):
        # Split horizontal courses at every opening; doors/windows are real voids.
        cuts=sorted(set([bottom,top]+[v for o in openings for v in o[2:] if bottom<v<top]))
        for band,(z0,z1) in enumerate(zip(cuts,cuts[1:])):
            rows=max(1,math.ceil((z1-z0)/.3))
            parts=[]
            for row in range(rows):
                a=z0+(z1-z0)*row/rows;b=z0+(z1-z0)*(row+1)/rows;mid=(a+b)/2
                spans=[(low,high)]
                for left,right,lo,hi in openings:
                    if lo<mid<hi:
                        spans=[(s,e) for x,y in spans for s,e in [(x,min(y,left)),(max(x,right),y)] if e-s>.001]
                for left,right in spans:
                    count=max(1,math.ceil((right-left)/.65))
                    for j in range(count):
                        length=(right-left)/count;c=left+(j+.5)*length
                        pos=(c,fixed,mid) if horizontal else (fixed,c,mid)
                        size=(length-.007,.18,b-a-.008) if horizontal else (.18,length-.007,b-a-.008)
                        parts.append(box(name,pos,size,material,0))
            start=.13+.34*(z0-bottom)/(top-bottom)
            group(name+'Course',parts,start,start+.10)
    def window(horizontal,fixed,c,z,width,height,stained=False):
        parts=[]
        def pane(n,u,v,du,dv,m,depth=.065):
            p=(u,fixed,v) if horizontal else (fixed,u,v)
            size=(du,depth,dv) if horizontal else (depth,du,dv)
            return box(n,p,size,m,.004)
        for i in range(2):
            for j in range(3):
                parts.append(pane('colored_pane',c+(i-.5)*width/2,z+(j-1)*height/3,width/2-.025,height/3-.025,'glass_red' if stained and (i+j)%3==0 else 'glass',.025))
        for u in [c-width/2,c,c+width/2]:parts.append(pane('window_mullion',u,z,.045,height+.08,'wood_dark'))
        for v in [z-height/2,z-height/6,z+height/6,z+height/2]:parts.append(pane('window_transom',c,v,width+.07,.045,'wood_dark'))
        parts.append(pane('window_sill',c,z-height/2-.07,width+.22,.11,'stone_light',.30))
        return parts
    def roof(width,depth,eaves,rise,cy=0):
        for row in range(6):
            parts=[]
            for side in [-1,1]:
                for col in range(9):
                    a=max(0,row/6-.012);b=min(1,(row+1)/6+.018);y=cy-depth/2+col*depth/9
                    x0=side*width/2*a;x1=side*width/2*b;z0=eaves+rise*(1-a);z1=eaves+rise*(1-b)
                    vertices=[(x0,y,z0),(x1,y,z1),(x1,y+depth/9+.012,z1),(x0,y+depth/9+.012,z0)]
                    vertices += [(x,y,z-.055) for x,y,z in vertices]
                    tile=k.mesh('roof_tile',vertices,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'tile' if inn else 'slate')
                    tile['inspectionCover']=True;parts.append(tile)
            group('RoofCourse',parts,.61+row*.035,.68+row*.035)
        trusses=[]
        for y in [cy-depth*.45,cy,cy+depth*.45]:
            trusses.append(beam('tie_beam',(-width*.45,y,eaves-.09),(width*.45,y,eaves-.09),.06))
            for s in [-1,1]:trusses.append(beam('rafter',(0,y,eaves+rise-.12),(s*width*.47,y,eaves-.06),.05))
        trusses.append(beam('ridge',(0,cy-depth/2,eaves+rise+.02),(0,cy+depth/2,eaves+rise+.02),.055,'tile' if inn else 'slate'))
        group('RoofTrusses',trusses,.49,.63)
    def entrance(cx,y,z,width,height,name='Entry',tier=1):
        frame=[box('door_jamb',(cx+s*(width/2+.055),y,z+height/2),(.10,.22,height+.1),'wood_dark') for s in [-1,1]]
        frame.append(box('door_lintel',(cx,y,z+height+.05),(width+.2,.22,.11),'wood_dark'))
        group(name+'Frame',frame,.53,.66,tier=tier)
        leaf=[box('door_plank',(cx-width/2+(i+.5)*width/7,y-.035,z+height/2),(width/7-.009,.06,height),'wood_light',.004) for i in range(7)]
        for dz in [.18,height-.18]:leaf.append(box('door_strap',(cx,y-.075,z+dz),(width*.87,.025,.055),'iron'))
        leaf.append(k.ico('door_handle',(cx+width*.34,y-.10,z+height*.5),(.035,.035,.035),'iron',2))
        node=group(name+'Door',leaf,.65,.80,(cx-width/2,y-.035,z),tier=tier,motion='entry-door',axis=(0,0,1))
        node['doorAngle']=math.pi/2 if name=='Guest' else -math.pi/2
    def gable(y,w,eaves,rise):
        v=[(x,y+dy,z) for dy in [-.06,.06] for x,z in [(-w/2,eaves),(w/2,eaves),(0,eaves+rise)]]
        return k.mesh('gable',v,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'plaster' if inn else 'stone_light')
    w,d=(4.8,3.6) if inn else (3.8,5.2)
    eaves,rise=(4.95,1.05) if inn else (2.75,1.24)
    group('Foundation',[box('foundation',(0,-.30,.08),(w+.32,d+.9,.16),'stone')],0,.12)
    floor=[]
    for i in range(8):
        for j in range(6):floor.append(box('paving',(-w/2+(i+.5)*w/8,-d/2+(j+.5)*d/6,.18),(w/8-.014,d/6-.014,.04),'stone_light' if (i+j)%4 else 'stone',.004))
    group('GroundFloor',floor,.04,.16)
    socket('Entrance',(0,-d/2-.66,0),'road')
    group('EntranceSteps',[box('step',(0,-d/2-.43,.06),(1.18,.48,.12),'stone_light'),box('step',(0,-d/2-.20,.14),(1.18,.27,.12),'stone_light')],.02,.14)
    group('Scaffold',[beam('scaffold',(-w/2-.19,y,0),(-w/2-.19,y,2.5),.04) for y in [-.8,.8]]+[box('scaffold_board',(-w/2-.19,0,1.5),(.38,1.9,.05))],.22,.38,temporary=True)
    front_open=[(-.61,.61,.20,2.43)]
    front_windows=[]
    if inn:
        for x in [-1.5,1.5]:
            front_open.append((x-.34,x+.34,.92,1.65));front_windows.extend(window(True,-1.81,x,1.285,.68,.73))
        for x in [-1.5,0,1.5]:front_open.append((x-.61,x+.61,2.55,4.78))
    wall('FrontWall',True,-d/2,-w/2,w/2,.2,eaves,front_open,'plaster' if inn else 'stone_light')
    for side in [-1,1]:
        openings=[];panes=[]
        for y in [-.95,.95] if inn else [-1.50,.20,1.75]:
            for z in [1.30,3.65] if inn else [1.68]:
                height=.70 if inn else 1.20;width=.60
                openings.append((y-width/2,y+width/2,z-height/2,z+height/2));panes.extend(window(False,side*w/2,y,z,width,height,not inn))
        wall('SideWall',False,side*w/2,-d/2,d/2,.20,eaves,openings,'plaster' if inn else 'stone_light')
        group('SideWindows',panes,.71,.89)
    back_open=[(-.42,.42,1.14,2.34)] if not inn else []
    wall('RearWall',True,d/2,-w/2,w/2,.2,eaves,back_open,'plaster' if inn else 'stone_light')
    if not inn:front_windows.extend(window(True,d/2,0,1.74,.84,1.20,True))
    if front_windows:group('FacadeWindows',front_windows,.70,.88)
    entrance(0,-d/2-.025,.20,1.20,2.20)
    group('Gables',[gable(s*d/2,w,eaves,rise) for s in [-1,1]],.48,.64)
    roof(w+.46,d+.50,eaves+.04,rise)

    if inn:
        frame=[]
        for x in [-2.4,-.76,.76,2.4]:
            for y in [-1.92,1.83]:frame.append(box('timber_post',(x,y,2.575),(.11,.13,4.75),'wood_dark'))
        for z in [.3,2.46,4.92]:
            for y in [-1.92,1.83]:
                spans=[(-2.445,-.61),(.61,2.445)] if z==.3 and y<0 else [(-2.445,2.445)]
                for a,b in spans:frame.append(box('timber_course',((a+b)/2,y,z),(b-a,.13,.13),'wood_dark'))
        for x in [-2.2,2.2]:frame.append(beam('gable_brace',(x,-1.84,4.99),(0,-1.84,5.99),.035))
        group('TimberFrame',frame,.32,.53)
        group('UpperFloor',[box('upper_floor',(0,0,2.49),(4.60,3.45,.12),'wood_light')],.37,.53)
        gallery=[]
        for i in range(14):gallery.append(box('gallery_plank',(-2.43+(i+.5)*4.90/14,-2.48,2.495),(4.90/14-.012,1.30,.11),'wood_light',0))
        for x in [-2.34,-.76,.76,2.34]:gallery.extend([beam('gallery_post',(x,-3.08,0),(x,-3.08,2.47),.065),beam('gallery_brace',(x,-3.08,1.88),(x,-1.91,2.42),.045)])
        for x in [-2.34+i*.39 for i in range(13)]:gallery.append(beam('gallery_baluster',(x,-3.09,2.55),(x,-3.09,3.32),.023))
        gallery.append(beam('gallery_rail',(-2.42,-3.09,3.34),(2.42,-3.09,3.34),.045))
        for z in [2.94,3.34]:gallery.append(beam('gallery_end',(-2.43,-3.1,z),(-2.43,-1.81,z),.025))
        group('Gallery',gallery,.44,.62)
        # Stairs approach the open right-hand end of the gallery, without a rail across the landing.
        steps=[]
        for i in range(12):
            y=1.47-i*.29;z=(i+1)*2.55/12
            steps.append(box('stair_tread',(3.16,y,z-.04),(1.24,.30,.08),'wood_light'))
        for x in [2.51,3.81]:
            steps.append(beam('stair_stringer',(x,1.62,.06),(x,-1.98,2.47),.06))
            steps.append(beam('stair_handrail',(x,1.58,.86),(x,-1.98,3.35),.029))
            for i in [0,3,6,9,11]:
                y=1.47-i*.29;z=(i+1)*2.55/12
                steps.append(beam('stair_post',(x,y,z),(x,y,z+.78),.022))
        steps.append(box('landing',(3.15,-2.505,2.495),(1.38,1.31,.11),'wood_light',0))
        for a,b in [((2.46,-3.16,3.34),(3.84,-3.16,3.34)),((3.84,-3.16,3.34),(3.84,-1.85,3.34))]:steps.append(beam('landing_rail',a,b,.03))
        for y in [-3.16,-1.86]:steps.append(beam('landing_support',(3.84,y,0),(3.84,y,3.34),.045))
        group('ExternalStair',steps,.43,.64)
        socket('StairFoot',(3.16,1.74,0),'pedestrian',(0,0,-1))
        for x in [-1.50,0,1.50]:entrance(x,-1.83,2.55,1.20,2.20,'Guest',tier=1)
        rooms=[]
        for x in [-.75,.75]:rooms.append(box('room_partition',(x,0,3.695),(.08,3.38,2.29),'plaster'))
        for x in [-1.50,0,1.50]:
            rooms.extend([box('bed_frame',(x,.45,2.89),(.95,2.02,.16),'wood'),box('mattress',(x,.45,3.04),(.87,1.90,.14),'wool'),box('blanket',(x,.04,3.12),(.90,1.02,.04),'teal'),box('pillow',(x,1.20,3.14),(.64,.31,.09),'wool_light')])
            for dx in [-.4,.4]:
                for y in [-.48,1.38]:rooms.append(box('bed_leg',(x+dx,y,2.74),(.075,.075,.38)))
            rooms.append(box('headboard',(x,1.50,3.16),(.97,.07,.58),'wood_dark'))
        group('GuestRooms',rooms,.68,.88)
        furniture=[]
        for x in [-1.48,1.48]:
            furniture.append(box('dining_table',(x,0,.85),(.90,1.25,.09),'wood_light'))
            for dx in [-.34,.34]:
                for y in [-.49,.49]:furniture.append(beam('table_leg',(x+dx,y,.2),(x+dx,y,.80),.035))
            for y in [-.9,.9]:furniture.extend([box('bench_seat',(x,y,.49),(.95,.25,.06),'wood'),box('bench_foot',(x-.34,y,.33),(.09,.23,.26)),box('bench_foot',(x+.34,y,.33),(.09,.23,.26))])
        group('DiningRoom',furniture,.70,.91)
        bracket=[beam('sign_bracket',(-2.40,-1.90,3.9),(-2.40,-3.02,3.9),.035,'iron'),beam('sign_brace',(-2.40,-1.9,4.1),(-2.40,-2.84,3.9),.025,'iron')]
        group('SignBracket',bracket,.80,.94)
        sign=[box('hanging_sign',(-2.40,-2.71,3.49),(.12,.63,.52),'teal')]
        for y in [-2.94,-2.48]:sign.append(beam('sign_hanger',(-2.40,y,3.76),(-2.40,y,3.9),.012,'iron'))
        # A raised mug emblem, not illegible miniature text.
        for side in [-1,1]:
            x=-2.40+side*.075
            sign.extend([box('mug_emblem',(x,-2.74,3.48),(.025,.22,.25),'gold'),beam('mug_handle',(x,-2.57,3.41),(x,-2.57,3.56),.018,'gold')])
            for z in [3.41,3.56]:sign.append(beam('mug_handle',(x,-2.64,z),(x,-2.57,z),.018,'gold'))
        group('HangingSign',sign,.87,.99,(-2.4,-2.71,3.9),motion='sign-swing',axis=(0,1,0))
        upgrades=[]
        for x in [-1.5,1.5]:
            upgrades.extend([box('planter',(x,-3.18,2.85),(.55,.22,.18),'wood_light'),box('planter_soil',(x,-3.18,2.95),(.48,.16,.035),'earth')])
            for j in range(5):
                xx=x-.20+j*.10;upgrades.extend([beam('flower_stem',(xx,-3.18,2.96),(xx,-3.18,3.16+(j%2)*.05),.009,'leaf'),k.ico('flower',(xx,-3.18,3.17+(j%2)*.05),(.055,.055,.04),'berry' if j%2 else 'gold',1)])
        group('GalleryPlanters',upgrades,.88,.99,tier=2)
        root['animationBoundsMin']=[-2.8,-.01,-2.2];root['animationBoundsMax']=[3.99,6.3,3.45]
    else:
        buttresses=[]
        for side in [-1,1]:
            for y in [-2.35,-.65,1.1,2.35]:
                for level,(height,width) in enumerate([(1.15,.45),(.95,.32)]):
                    z=.2+height/2 if level==0 else 1.35+height/2
                    buttresses.append(box('buttress',(side*(w/2+.12),y,z),(width,.36,height),'stone'))
                buttresses.append(box('buttress_cap',(side*(w/2+.12),y,2.34),(.4,.43,.09),'stone_light'))
        group('Buttresses',buttresses,.35,.57)
        seats=[]
        for y in [-1.32,-.58,.16,.90]:
            for side in [-1,1]:
                x=side*1.12;seats.extend([box('pew_seat',(x,y,.59),(1.08,.35,.075),'wood_light'),box('pew_back',(x,y-.20,.87),(1.08,.065,.56),'wood')])
                for dx in [-.40,.40]:seats.append(box('pew_leg',(x+dx,y,.38),(.09,.31,.36),'wood_dark'))
        group('Pews',seats,.69,.89)
        altar=[box('altar_step',(0,1.91,.25),(1.5,.95,.10),'stone_light'),box('altar_table',(0,2.01,.91),(1.18,.56,.10),'stone_light')]
        for x in [-.43,.43]:altar.append(box('altar_support',(x,2.01,.58),(.18,.40,.58),'stone'))
        group('Altar',altar,.75,.94)
        belfry=[]
        for x in [-.68,.68]:
            belfry.append(box('belfry_pier',(x,-2.48,4.34),(.20,.50,1.72),'stone_light'))
            belfry.append(box('belfry_foot',(x,-2.48,3.49),(.36,.62,.17),'stone'))
        belfry.append(box('belfry_lintel',(0,-2.48,5.22),(1.64,.63,.17),'stone_light'))
        for x in [-.56,.56]:belfry.append(box('bell_bearing',(x,-2.48,4.98),(.15,.19,.18),'iron'))
        group('BelfryFrame',belfry,.63,.82)
        for side in [-1,1]:
            v=[(0,-2.89,5.77),(side*.92,-2.89,5.30),(side*.92,-2.08,5.30),(0,-2.08,5.77)]
            v += [(x,y,z-.09) for x,y,z in v]
            obj=k.mesh('belfry_roof',v,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'slate');obj['inspectionCover']=True
            group('BelfryRoof',[obj],.79,.92)
        group('RoofFinial',[beam('finial',(0,-2.48,5.73),(0,-2.48,6.14),.03,'iron'),beam('finial_cross',(-.15,-2.48,5.99),(.15,-2.48,5.99),.022,'iron')],.90,.99)
        center=(0,-2.48,4.98)
        # Revolve an outer and inner profile into a closed-thickness shell with an open mouth.
        profile=[(.12,-.12),(.20,-.20),(.24,-.39),(.33,-.59),(.43,-.70),(.43,-.75),(.37,-.75),(.29,-.59),(.19,-.39),(.15,-.22),(.06,-.17)]
        vertices=[(r*math.cos(i*math.tau/24),center[1]+r*math.sin(i*math.tau/24),center[2]+z) for r,z in profile for i in range(24)]
        faces=[(j*24+i,j*24+(i+1)%24,((j+1)%len(profile))*24+(i+1)%24,((j+1)%len(profile))*24+i) for j in range(len(profile)) for i in range(24)]
        bell=[k.mesh('hollow_bell',vertices,faces,'bronze'),box('bell_yoke',(0,-2.48,4.98),(1.12,.15,.15),'wood_dark'),beam('bell_crown',(0,-2.48,4.80),(0,-2.48,4.98),.08,'bronze')]
        bellnode=group('SwingingBell',bell,.83,.97,center,motion='bell-swing',axis=(1,0,0))
        clapper=group('BellClapper',[beam('clapper_shaft',(0,-2.48,4.79),(0,-2.48,4.35),.026,'iron'),k.ico('clapper_ball',(0,-2.48,4.35),(.09,.09,.09),'iron',2)],.86,.98,(0,-2.48,4.79),motion='bell-clapper',axis=(1,0,0))
        k.bpy.context.view_layer.update();world=clapper.matrix_world.copy();clapper.parent=bellnode;clapper.matrix_world=world
        upgrades=[]
        for side in [-1,1]:
            x=side*2.6
            upgrades.append(box('garden_bed',(x,.12,.08),(.70,4.5,.16),'earth'))
            for j in range(7):
                y=-1.7+j*.58
                upgrades.append(k.ico('shrub',(x,y,.35+(.03 if j%2 else 0)),(.32,.34,.26),'leaf' if j%2 else 'leaf_light',2))
            for y in [-2.16,2.4]:upgrades.append(box('bed_coping',(x,y,.16),(.77,.12,.19),'stone_light'))
            for xx in [x-.35,x+.35]:upgrades.append(box('bed_coping',(xx,.12,.16),(.10,4.5,.19),'stone_light'))
        group('CloisterGarden',upgrades,.87,.99,tier=2)
        root['animationBoundsMin']=[-3.12,-.01,-2.94];root['animationBoundsMax']=[3.12,6.22,4.02]
