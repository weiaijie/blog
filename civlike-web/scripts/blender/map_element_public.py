"""Stylized civic hall and oval arena, with usable circulation and separate fabric."""
import math

from map_element_buildings import build_group, connection


def build(k, kind):
    root = k.pivot('BuildingRoot', (0, 0, 0), [])
    root['buildingType'] = kind
    for name, code in {'brick':'AA705D', 'trim':'D1D2C6', 'slate':'547784', 'glass':'6593A1',
                       'canvas':'E1DFCA', 'canvas_red':'AF5965', 'paving':'8B9694', 'sand':'B4AA84'}.items():
        mat = k.M['wool'].copy(); mat.name = 'public_'+name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear, 1)
        k.M[name] = mat

    def box(n, p, s, m='trim', bevel=0): return k.box(n, p, s, m, bevel)
    def beam(n, a, b, r=.035, m='iron', sides=8): return k.beam(n, a, b, r, m, sides)
    def group(name, parts, start, full, anchor=(0, 0, 0), cover=False, **kw):
        if cover:
            for obj in parts: obj['inspectionCover'] = True
        return build_group(k, root, name, parts, start, full, anchor, **kw)
    def port(name, p, normal, width):
        node = connection(k, root, name, p, 'pedestrian')
        node['normalGltf'] = normal; node['clearWidth'] = width
    def banner(x, y, z):
        group('BannerPole', [beam('pole', (x,y,.12), (x,y,z+.09), .028),
                             k.ico('finial', (x,y,z+.11), (.065,.065,.065), 'gold', 2)], .74, .88)
        verts = [(x+i*.09, y, z-j*.17) for j in range(4) for i in range(10)]
        faces = [(j*10+i,j*10+i+1,(j+1)*10+i+1,(j+1)*10+i) for j in range(3) for i in range(9)]
        cloth = k.mesh('civic_flag', verts, faces, 'canvas_red')
        group('Banner', [cloth], .88, .99, motion='banner')

    if kind == 'amphitheater':
        # Every row is split around ground-level entrances and diagonal stair aisles.
        sx = 1.24
        def p(r, a, z): return (sx*r*math.cos(a), r*math.sin(a), z)
        def arc(n, inner, outer, a, b, bottom, top, material='stone_light', segments=1):
            vertices = [p(r, a+(b-a)*i/segments, z) for z in [bottom,top] for r in [inner,outer] for i in range(segments+1)]
            stride = segments+1; layer = stride*2; faces = []
            for i in range(segments):
                faces += [(i,i+1,stride+i+1,stride+i), (layer+i,layer+stride+i,layer+stride+i+1,layer+i+1),
                          (i,layer+i,layer+i+1,i+1), (stride+i,stride+i+1,layer+stride+i+1,layer+stride+i)]
            faces += [(0,stride,layer+stride,layer), (segments,layer+segments,layer+stride+segments,stride+segments)]
            return k.mesh(n, vertices, faces, material)
        # A filled fan avoids the degenerate inner edge of a zero-radius annulus.
        vertices = [(0,0,0),(0,0,.12)]+[p(7.4,i*math.tau/96,z) for z in [0,.12] for i in range(96)]
        faces = []
        for i in range(96):
            j=(i+1)%96
            faces += [(0,2+j,2+i),(1,98+i,98+j),(2+i,2+j,98+j,98+i)]
        group('Foundation', [k.mesh('oval_foundation',vertices,faces,'paving')], 0, .10)
        vertices = [(0,0,.125)]+[p(3.58,i*math.tau/64,.125) for i in range(64)]
        group('Arena', [k.mesh('arena_floor',vertices,[(0,i+1,(i+1)%64+1) for i in range(64)],'sand')], .05, .17)
        sectors = [(q*math.pi/2+.16,q*math.pi/2+math.pi/4-.16) for q in range(4)]
        sectors += [(q*math.pi/2+math.pi/4+.16,(q+1)*math.pi/2-.16) for q in range(4)]
        for row in range(5):
            r = 3.6+row*.58; top = .12+(row+1)*.40
            terraces = []; seats = []
            for a,b in sectors:
                terraces.append(arc('terrace',r,r+.58,a,b,.12,top,'stone',6))
                for i in range(6):
                    aa=a+(b-a)*i/6;bb=a+(b-a)*(i+1)/6
                    seats.append(arc('seat_block',r+.31,r+.57,aa+.003,bb-.003,top,top+.40,'trim' if (row+i)%3 else 'stone_light'))
            group('SeatingTerrace', terraces, .12+row*.065, .22+row*.065)
            group('SeatRow', seats, .52+row*.045, .64+row*.045)
        stairs = []
        for q in range(4):
            a = q*math.pi/2+math.pi/4
            for step in range(10):
                r = 3.6+step*.29; top = .12+(step+1)*.20
                stairs.append(arc('aisle_step',r,r+.29,a-.16,a+.16,.12,top,'trim',4))
            rail_angle=a+.15
            stairs.append(beam('aisle_rail',p(3.64,rail_angle,1.10),p(6.46,rail_angle,3.02),.024))
            for step in [0,3,6,9]:
                r=3.6+(step+.5)*.29;z=.12+(step+1)*.20
                stairs.append(beam('aisle_post',p(r,rail_angle,z),p(r,rail_angle,z+.84),.017))
        group('AisleStairs',stairs,.38,.59)
        promenade=[]
        for q in range(4):
            a=q*math.pi/2+.16;b=(q+1)*math.pi/2-.16
            promenade.append(arc('upper_walk',6.5,7.11,a,b,1.95,2.12,'paving',12))
            for edge in [a,b]:
                promenade.append(beam('walk_end_rail',p(6.52,edge,3.02),p(7.09,edge,3.02),.025))
                for r in [6.52,7.09]:promenade.append(beam('walk_end_post',p(r,edge,2.12),p(r,edge,3.02),.02))
        group('Promenade',promenade,.45,.65)
        piers=[]; arches=[]
        for i in range(24):
            # The cardinal directions lie at arch centers, not at a solid pier.
            a=(i+.5)*math.tau/24
            piers.append(arc('arcade_pier',6.95,7.30,a-.027,a+.027,.12,2.15,'stone_light',2))
            piers.append(arc('pier_capital',6.90,7.34,a-.038,a+.038,2.08,2.22,'trim',2))
            center=i*math.tau/24;span=math.pi/24-.027
            for j in range(9):
                t0=j*math.pi/9;t1=(j+1)*math.pi/9
                # Build an actual curved voussoir around the ellipse's tangent.
                v=[]
                for r in [6.95,7.30]:
                    for radius in [.50,.68]:
                        for t in [t0,t1]:
                            angle=center+span*math.cos(t)*radius/.50
                            v.append(p(r,angle,2.15+radius*math.sin(t)))
                arches.append(k.mesh('arch_stone',v,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],'trim' if j==4 else 'stone_light'))
        group('ArcadePiers',piers,.22,.46)
        group('ArcadeArches',arches,.49,.73)
        cornice=[arc('cornice',6.89,7.36,i*math.tau/32,(i+1)*math.tau/32,2.82,3.06,'trim',3) for i in range(32)]
        group('Cornice',cornice,.69,.85)
        for q in range(4):
            a=q*math.pi/2
            port('ArenaEntry',p(7.4,a,.12),[math.cos(a),0,-math.sin(a)],1.4)
        supports=[]
        for a,b in sectors:
            for angle in [a+.01,b-.01]:
                supports += [beam('mast',p(7.10,angle,2.12),p(7.10,angle,4.58),.04,'wood_dark'),
                             beam('canopy_spar',p(7.10,angle,4.48),p(4.86,angle,3.83),.035,'wood'),
                             beam('spar_brace',p(7.10,angle,3.35),p(6.15,angle,4.20),.022,'wood_dark')]
            for r,z in [(4.86,3.83),(7.10,4.48)]:
                # Shared cross-sections keep the entire curved tether watertight.
                vertices=[];faces=[]
                for i in range(9):
                    angle=a+.01+(b-a-.02)*i/8;cx,cy,cz=p(r,angle,z)
                    nx,ny=math.cos(angle)/sx,math.sin(angle);length=math.hypot(nx,ny)
                    for j in range(6):
                        t=j*math.tau/6
                        vertices.append((cx+.014*math.cos(t)*nx/length,cy+.014*math.cos(t)*ny/length,cz+.014*math.sin(t)))
                for i in range(8):
                    for j in range(6):faces.append((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j))
                faces += [tuple(range(5,-1,-1)),tuple(range(48,54))]
                supports.append(k.mesh('edge_rope',vertices,faces,'rope'))
        group('CanopyMasts',supports,.76,.91,tier=2)
        for index,(a,b) in enumerate(sectors):
            verts=[];uvs=[];faces=[]
            for j in range(5):
                v=j/4;r=4.86+(7.1-4.86)*v
                for i in range(9):
                    u=i/8;angle=a+.01+(b-a-.02)*u
                    verts.append(p(r,angle,3.83+.65*v-.13*math.sin(math.pi*u)*math.sin(math.pi*v)))
                    uvs.append((u,v))
            for j in range(4):
                for i in range(8):faces.append((j*9+i,j*9+i+1,(j+1)*9+i+1,(j+1)*9+i))
            obj=k.mesh('velarium_panel',verts,faces,'canvas' if index%2 else 'canvas_red')
            uv=obj.data.uv_layers.new(name='FabricUV')
            for loop in obj.data.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
            group('Velarium', [obj], .85, .99, tier=2, motion='velarium')
        for x in [-3.1,3.1]:banner(x,-6.65,3.60)
        scaffold=[beam('scaffold',(x,6.75,.12),(x,6.75,2.7),.035,'wood') for x in [-.4,.4]]
        scaffold.append(box('scaffold_deck',(0,6.75,1.75),(1.15,.42,.06),'wood'))
        group('Scaffold',scaffold,.17,.31,temporary=True)
        root['animationBoundsMin']=[-9.3,-.01,-7.6];root['animationBoundsMax']=[9.3,4.75,7.6]
        return

    w,d,floor,eaves=8.4,6.0,.30,3.35
    group('Foundation',[box('foundation',(0,-.75,.075),(8.72,8.1,.15),'stone'),
                        box('floor',(0,0,.225),(8.4,6,.15),'paving'),
                        box('portico_landing',(0,-3.9,.225),(4.5,1.8,.15),'paving')],0,.12)
    steps=[box('entry_step',(0,-5.08,.075),(3.6,.56,.15),'trim'),box('entry_step',(0,-4.80,.225),(3.6,.28,.15),'trim')]
    group('EntranceSteps',steps,.03,.16)
    port('Entrance',(0,-5.36,0),[0,0,1],3.6)
    def wall(name, horizontal, fixed, low, high, openings):
        cuts=sorted(set([floor,eaves]+[z for o in openings for z in o[2:] if floor<z<eaves]))
        for lo,hi in zip(cuts,cuts[1:]):
            parts=[];rows=max(1,math.ceil((hi-lo)/.32))
            for row in range(rows):
                z0=lo+(hi-lo)*row/rows;z1=lo+(hi-lo)*(row+1)/rows;mid=(z0+z1)/2;spans=[(low,high)]
                for a,b,c,e in openings:
                    if c<mid<e:spans=[(s,t) for x,y in spans for s,t in [(x,min(y,a)),(max(x,b),y)] if t-s>.001]
                for a,b in spans:
                    count=max(1,math.ceil((b-a)/.75))
                    for i in range(count):
                        u=a+(i+.5)*(b-a)/count
                        parts.append(box('masonry',(u,fixed,mid) if horizontal else (fixed,u,mid),
                                         ((b-a)/count-.004,.19,z1-z0-.005) if horizontal else (.19,(b-a)/count-.004,z1-z0-.005),'brick'))
            start=.13+.33*(lo-floor)/(eaves-floor);group(name,parts,start,start+.11)
    windows=[]
    def window(horizontal,fixed,c):
        def panel(n,u,z,a,b,mat,depth=.065):
            return box(n,(u,fixed,z) if horizontal else (fixed,u,z),(a,depth,b) if horizontal else (depth,a,b),mat)
        parts=[panel('glazing',c,1.82,1.05,1.45,'glass',.03)]
        for u in [c-.55,c,c+.55]:parts.append(panel('mullion',u,1.82,.05,1.55,'trim'))
        for z in [1.06,1.57,2.08,2.58]:parts.append(panel('transom',c,z,1.15,.045,'trim'))
        parts.extend([panel('sill',c,.985,1.28,.11,'trim',.33),panel('lintel',c,2.66,1.30,.11,'trim',.28)])
        windows.extend(parts)
    for side in [-1,1]:
        opening=[(-1.02,1.02,.3,2.77)] if side<0 else []
        for x in [-2.75,2.75]:opening.append((x-.56,x+.56,1.05,2.60));window(True,side*3,x)
        wall('FrontWall' if side<0 else 'RearWall',True,side*3,-4.2,4.2,opening)
        holes=[]
        for y in [-1.8,0,1.8]:holes.append((y-.56,y+.56,1.05,2.60));window(False,side*4.2,y)
        wall('SideWall',False,side*4.2,-3,3,holes)
    group('Windows',windows,.66,.87)
    trim=[]
    for x in [-4.23,4.23]:
        for y in [-3.03,3.03]:
            for j in range(9):trim.append(box('corner_quoin',(x,y,.48+j*.315),(.27,.28,.28),'trim'))
    for y in [-3,3]:trim.append(box('eave_band',(0,y,3.35),(8.70,.32,.20),'trim'))
    group('FacadeTrim',trim,.48,.69)
    for side in [-1,1]:
        cx=side*.50;leaf=[box('door_panel',(cx,-3.035,1.52),(.98,.07,2.44),'wood_light')]
        for z in [.72,1.54,2.32]:leaf.append(box('door_inset',(cx,-3.082,z),(.77,.035,.50),'wood'))
        leaf.append(beam('door_handle',(side*.15,-3.12,1.38),(side*.15,-3.12,1.64),.017))
        node=group('EntryDoor',leaf,.73,.89,(side,-3.035,.30),motion='entry-door',axis=(0,0,1))
        node['doorAngle']=side*math.pi/2
    structure=[]
    for x in [-1.92,1.92]:
        structure += [box('column_base',(x,-4.43,.39),(.52,.52,.18)),beam('column',(x,-4.43,.48),(x,-4.43,2.99),.17,'trim',12),
                      box('capital',(x,-4.43,3.06),(.53,.53,.18))]
    structure.append(box('portico_architrave',(0,-4.43,3.23),(4.57,.66,.20)))
    for x in [-1.12,1.12]:structure.append(box('tower_support',(x,-2.73,1.78),(.20,.44,2.96),'brick'))
    structure.append(box('tower_lintel',(0,-2.73,3.16),(2.45,.44,.24)))
    group('Portico',structure,.39,.62)
    roof_cuts=[0,.55,1.10,1.40,1.65,2.20,2.75,3.04,3.28]
    for row,(edge0,edge1) in enumerate(zip(roof_cuts,roof_cuts[1:])):
        parts=[]
        for side in [-1,1]:
            a=edge0/3.28;b=edge1/3.28;y0=side*edge0;y1=side*edge1;z0=3.40+1.28*(1-a);z1=3.40+1.28*(1-b)
            # The clock tower penetrates the roof; no tile sheet crosses its footprint.
            spans=[(-4.46,4.46)] if side>0 or edge1<=1.40 or edge0>=3.04 else [(-4.46,-1.02),(1.02,4.46)]
            for left,right in spans:
                count=max(1,math.ceil((right-left)/.55))
                for col in range(count):
                    x0=left+col*(right-left)/count;x1=left+(col+1)*(right-left)/count
                    verts=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z1),(x0,y1,z1)];verts += [(x,y,z-.06) for x,y,z in verts]
                    parts.append(k.mesh('slate_course',verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'slate'))
        group('RoofCourse',parts,.60+row*.030,.67+row*.030,cover=True)
    gables=[]
    for x in [-4.2,4.2]:
        edge=3.34+1.28*(1-3/3.28)
        profile=[(-3,3.35),(3,3.35),(3,edge),(0,4.62),(-3,edge)]
        verts=[(x+dx,y,z) for dx in [-.065,.065] for y,z in profile]
        faces=[(4,3,2,1,0),(5,6,7,8,9)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
        gables.append(k.mesh('gable',verts,faces,'brick'))
    group('Gables',gables,.48,.66)
    pediment=k.mesh('portico_pediment',[(-2.31,-4.78,3.33),(2.31,-4.78,3.33),(0,-4.78,4.05),(-2.31,-3.10,3.33),(2.31,-3.10,3.33),(0,-3.10,4.05)],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'trim')
    group('Pediment',[pediment],.61,.78,cover=True)
    tower=[box('clock_tower',(0,-2.22,4.74),(2.04,1.64,2.78),'brick'),box('clock_cornice',(0,-2.22,6.16),(2.30,1.92,.20))]
    cap=k.mesh('tower_cap',[(-1.25,-3.27,6.28),(1.25,-3.27,6.28),(1.25,-1.17,6.28),(-1.25,-1.17,6.28),(0,-2.22,7.16)],[(0,3,2,1),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'slate')
    tower.append(cap);group('ClockTower',tower,.57,.79,cover=True)
    clock=[beam('clock_dial',(0,-3.05,5.37),(0,-3.11,5.37),.66,'canvas',48)]
    for i in range(12):
        a=i*math.tau/12
        clock.append(beam('hour_mark',(.52*math.sin(a),-3.145,5.37+.52*math.cos(a)),(.59*math.sin(a),-3.145,5.37+.59*math.cos(a)),.014,'iron',4))
    group('ClockDial',clock,.79,.94,cover=True)
    for name,length,rate,depth in [('MinuteHand',.48,-1.20,-3.17),('HourHand',.32,-.10,-3.20)]:
        group(name,[beam('clock_hand',(0,depth,5.30),(0,depth,5.37+length),.025,'iron',4)],.87,.99,(0,depth,5.37),cover=True,motion='spin',axis=(0,-1,0),rate=rate)
    furniture=[]
    for x in [-2.30,2.30]:
        for y in [-1.60,-.10,1.40]:
            furniture.append(box('council_table',(x,y,1.03),(1.45,.68,.09),'wood_light'))
            for dx in [-.57,.57]:
                for dy in [-.23,.23]:furniture.append(box('table_leg',(x+dx,y+dy,.645),(.07,.07,.69),'wood_dark'))
            for dx in [-.42,.42]:
                xx=x+dx;cy=y+.60
                furniture.extend([box('chair_seat',(xx,cy,.74),(.48,.43,.07),'wood'),box('chair_back',(xx,cy+.20,1.02),(.48,.065,.58),'wood')])
                for ddx in [-.18,.18]:
                    for ddy in [-.16,.16]:furniture.append(box('chair_leg',(xx+ddx,cy+ddy,.50),(.05,.05,.40),'wood_dark'))
            furniture += [box('ledger',(x-.30,y,1.10),(.24,.31,.06),'canvas_red'),box('paper',(x+.18,y,1.082),(.22,.26,.012),'canvas')]
    furniture += [box('lectern_base',(0,2.28,.36),(.80,.65,.12),'wood_dark'),box('lectern_post',(0,2.28,.84),(.22,.22,.87),'wood'),box('lectern_top',(0,2.28,1.32),(.90,.68,.09),'wood_light')]
    group('CouncilFurniture',furniture,.71,.93)
    for x in [-3.35,3.35]:banner(x,-3.85,3.55)
    upgrades=[]
    for x in [-3.5,3.5]:
        upgrades += [box('planter',(x,-4.45,.25),(1.10,.58,.32),'trim'),box('soil',(x,-4.45,.425),(.98,.46,.035),'earth')]
        for i in range(4):upgrades.append(k.ico('shrub',(x-.36+i*.24,-4.45,.64),(.24,.22,.24),'leaf_light' if i%2 else 'leaf',2))
    group('Planters',upgrades,.89,.99,tier=2)
    group('Scaffold',[beam('scaffold',(-4.5,y,.15),(-4.5,y,2.8),.035,'wood') for y in [-1,1]]+[box('scaffold_board',(-4.5,0,1.9),(.4,2.3,.06),'wood')],.17,.33,temporary=True)
    root['animationBoundsMin']=[-4.8,-.01,-3.6];root['animationBoundsMax']=[4.8,7.35,5.5]
