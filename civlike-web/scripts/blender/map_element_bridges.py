"""Road-compatible masonry arches and a sequenced double-leaf bascule bridge."""
import math
from map_element_buildings import build_group, connection


def build(k, kind):
    stone = kind == 'stone-bridge'
    root = k.pivot('BuildingRoot', (0, 0, 0), [])
    root['buildingType'] = kind
    root['routeWidth'] = 1.45
    root['routeProfile'] = 'road-145-v1'
    root['riverbedHeight'] = -1.8
    for name, code in {'bridge_stone':'989D96', 'bridge_light':'BCC1B5', 'bridge_dark':'778179',
                       'bridge_steel':'548B8D', 'bridge_deck':'58666A', 'bridge_paint':'E0DDC9',
                       'bridge_red':'BA5C4F', 'bridge_moss':'7A965D'}.items():
        mat = k.M['stone'].copy(); mat.name = name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color = (*linear, 1)
        shader = mat.node_tree.nodes['Principled BSDF']; shader.inputs['Base Color'].default_value = (*linear, 1)
        shader.inputs['Metallic'].default_value = .45 if name == 'bridge_steel' else 0
        k.M[name] = mat
    def box(n,p,s,m='bridge_stone',bevel=.009): return k.box(n,p,s,m,bevel)
    def beam(n,a,b,r=.025,m='bridge_steel',sides=8): return k.beam(n,a,b,r,m,sides)
    def group(n,parts,start,full,anchor=(0,0,0),**kw): return build_group(k,root,n,parts,start,full,anchor,**kw)
    def port(n,p,role,normal,profile):
        node = connection(k,root,n,p,role); node['normalGltf']=normal; node['profile']=profile
        return node
    for side in [-1,1]:
        port('RoadPort',(0,side*4.6,.145),'road',(0,0,-side),'road-145-v1')
    # No baked river plane: the actual openings remain available to the map's water surface.
    def prism(n,x0,x1,y0,y1,z0,z1,depth,mat):
        verts=[(x,y,z-d) for d in [0,depth] for x,y,z in [(x0,y0,z0),(x1,y0,z0),(x1,y1,z1),(x0,y1,z1)]]
        return k.mesh(n,verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],mat)
    def pennant(x,y,z):
        group('PennantMast',[beam('mast',(x,y,z),(x,y,z+1.1),.023,'iron'),box('mast_foot',(x,y,z+.04),(.15,.15,.08))],.78,.90)
        verts=[(x+.06+i*.58/10,y,z+.60+j*.34/4) for j in range(5) for i in range(11)]
        faces=[(j*11+i,j*11+i+1,(j+1)*11+i+1,(j+1)*11+i) for j in range(4) for i in range(10)]
        flag=k.mesh('bridge_pennant',verts,faces,'bridge_red')
        group('Pennant',[flag],.89,.99,(x,y,z+.60),motion='banner')
    if stone:
        def height(y): return .145+.28*math.cos(math.pi*y/9.2)**2
        foundation=[box('pier_footing',(0,0,-1.68),(2.55,.72,.24))]
        for side in [-1,1]: foundation.append(box('abutment_footing',(0,side*3.73,-1.68),(2.40,1.74,.24)))
        group('Foundation',foundation,0,.10)
        for row in range(6):
            z=-1.56+(row+.5)*.27;parts=[]
            for y,width in [(0,.52),(-3.77,1.66),(3.77,1.66)]:
                for col in range(5): parts.append(box('pier_course',(-.86+col*.43,y,z),(.415,width-.01,.26),'bridge_dark' if (row+col)%4==0 else 'bridge_stone'))
            group('PierCourse',parts,.08+row*.05,.16+row*.05)
        for side in [-1,1]:
            vertices=[(x,y,z) for z in [-1.56,-.62] for x,y in [(side*.97,-.27),(side*1.39,0),(side*.97,.27)]]
            group('Cutwater',[k.mesh('cutwater',vertices,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'bridge_dark')],.20,.36)
        for center in [-1.50,1.50]:
            port('WaterPort',(1.4,center,-1.35),'water', (1,0,0),'water-arch-246-v1')
            port('WaterPort',(-1.4,center,-1.35),'water', (-1,0,0),'water-arch-246-v1')
            for block in range(24):
                a=block*math.pi/24;b=(block+1)*math.pi/24
                verts=[(x,center+r*math.cos(t),-1.48+r*math.sin(t)) for x in [-1.03,1.03] for r,t in [(1.23,a),(1.50,a),(1.50,b),(1.23,b)]]
                wedge=k.mesh('arch_voussoir',verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'bridge_light' if block%3 else 'bridge_stone')
                group('ArchVoussoir',[wedge],.29+min(block,23-block)*.015,.39+min(block,23-block)*.015)
            for i in range(20):
                y0=center-1.5+i*.15;y1=y0+.15
                bottom=lambda y:-1.48+math.sqrt(max(0,2.25-(y-center)**2))
                polygon=[(y0,bottom(y0)),(y1,bottom(y1)),(y1,height(y1)-.12),(y0,height(y0)-.12)]
                parts=[]
                for row in range(7):
                    clipped=polygon
                    # Clip the arch-shaped fill into horizontal masonry courses, not vertical stripes.
                    for level,sign in [(-1.48+row*.27,1),(-1.48+(row+1)*.27,-1)]:
                        result=[]
                        for a,b in zip(clipped,clipped[1:]+clipped[:1]):
                            inside_a=(a[1]-level)*sign>=0;inside_b=(b[1]-level)*sign>=0
                            if inside_a:result.append(a)
                            if inside_a!=inside_b:
                                t=(level-a[1])/(b[1]-a[1]);result.append((a[0]+t*(b[0]-a[0]),level))
                        clipped=result
                        if not clipped:break
                    if len(clipped)<3:continue
                    n=len(clipped);verts=[(x,y,z) for x in [-1.00,1.00] for y,z in clipped]
                    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
                    parts.append(k.mesh('spandrel_masonry',verts,faces,'bridge_dark' if (i//3+row*2)%7==0 else 'bridge_stone'))
                group('SpandrelFill',parts,.48+i*.004,.59+i*.004)
        for i in range(32):
            y0=-4.6+i*9.2/32;y1=y0+9.2/32
            parts=[prism('road_bed',-.725,.725,y0,y1,height(y0),height(y1),.12,'bridge_dark')]
            # Joints and slight color variation keep paving legible without a noisy top surface.
            for col in range(4):
                x=-.72+col*.36
                parts.append(prism('paving',x,x+.35,y0+.006,y1-.006,height(y0+.006)+.002,height(y1-.006)+.002,.03,'bridge_light' if (col+i)%7==0 else 'bridge_stone'))
            group('DeckCourse',parts,.58+i*.004,.69+i*.004)
            curb=[]
            for side in [-1,1]:
                curb.append(prism('parapet',side*.89-.13,side*.89+.13,y0+.004,y1-.004,height(y0)+.44,height(y1)+.44,.52,'bridge_stone' if i%3 else 'bridge_light'))
                curb.append(prism('parapet_cap',side*.89-.155,side*.89+.155,y0,y1,height(y0)+.49,height(y1)+.49,.065,'bridge_light'))
            group('ParapetCourse',curb,.72+i*.004,.82+i*.004)
        ornaments=[]
        for side in [-1,1]:
            for y in [-3.75,3.75]:
                z=height(y)+.49
                ornaments.extend([box('lantern_pier',(side*.90,y,z+.13),(.33,.33,.26)),beam('lantern_stem',(side*.9,y,z+.26),(side*.9,y,z+.66),.022,'iron'),box('lantern_glass',(side*.9,y,z+.76),(.17,.17,.20),'bridge_paint'),box('lantern_cap',(side*.9,y,z+.88),(.23,.23,.05),'bridge_steel')])
        for i in range(16):
            y=-2.8+i*.37
            ornaments.append(k.ico('moss',((-1 if i%2 else 1)*1.012,y,height(y)-.12),(.03,.12,.07),'bridge_moss',1))
        group('LanternsAndWeathering',ornaments,.86,.99,tier=2)
        pennant(-.9,3.25,height(3.25)+.49)
        root['animationBoundsMin']=[-1.5,-1.85,-4.7];root['animationBoundsMax']=[1.5,1.95,4.7]
    else:
        foundation=[]
        for side in [-1,1]:foundation.append(box('bank_footing',(0,side*3.90,-1.69),(2.50,1.40,.22)))
        group('Foundation',foundation,0,.12)
        for row in range(6):
            parts=[];z=-1.58+(row+.5)*.265
            for side in [-1,1]:
                parts.append(box('bank_masonry',(0,side*3.90,z),(2.30,1.40,.255),'bridge_light' if row%2 else 'bridge_stone'))
                # Side walls leave an empty pocket below the fixed approach for the counterweight.
                for x in [-1.10,1.10]:parts.append(box('bearing_pier',(x,side*2.72,z),(.34,.96,.255)))
            group('AbutmentCourse',parts,.08+row*.05,.19+row*.05)
        for side in [-1,1]:
            parts=[box('fixed_deck',(0,side*3.535,.085),(1.45,2.13,.12),'bridge_deck',0),box('hinge_cover_plate',(0,side*2.435,.1325),(1.45,.07,.025),'bridge_deck',0)]
            for x in [-.86,.86]:parts.append(box('fixed_curb',(x,side*3.95,.14),(.20,1.30,.16),'bridge_light'))
            for i in range(4):
                y=side*(3.32+i*.42)
                for x in [-.94,.94]:parts.append(beam('approach_post',(x,y,.16),(x,y,.69),.022))
            for x in [-.94,.94]:parts.append(beam('approach_rail',(x,side*3.32,.69),(x,side*4.6,.69),.025))
            for x in [-1.28,1.28]:
                for y in [2.42,3.24]:parts.append(beam('pocket_guard_post',(x,side*y,0),(x,side*y,.91),.024))
                parts.append(beam('pocket_guard_rail',(x,side*2.42,.91),(x,side*3.24,.91),.025))
            group('FixedApproach',parts,.41,.61)
            supports=[]
            for x in [-1.08,1.08]:
                supports.extend([box('bearing_block',(x,side*2.40,-.045),(.32,.40,.15),'bridge_dark'),beam('trunnion',(x-.16,side*2.40,.05),(x+.16,side*2.40,.05),.075,'iron',16)])
            group('TrunnionBearings',supports,.38,.55)
            leaf=[box('moving_road',(0,side*1.20,.105),(1.45,2.38,.08),'bridge_deck',0)]
            for x in [-.94,.94]:
                leaf.extend([box('girder_flange',(x,side*1.20,-.035),(.19,2.40,.045),'bridge_steel'),box('girder_web',(x,side*1.20,.10),(.045,2.40,.24),'bridge_steel'),box('girder_top',(x,side*1.20,.245),(.16,2.40,.045),'bridge_steel')])
                for j in range(6):
                    y0=side*(.025+j*.395);y1=y0+side*.395
                    leaf.extend([beam('truss_post',(x,y0,.26),(x,y0,.82),.026),beam('truss_diagonal',(x,y0,.28),(x,y1,.82),.023),beam('truss_top',(x,y0,.82),(x,y1,.82),.03)])
                    leaf.append(box('gusset',(x,y0,.28),(.07,.12,.12),'bridge_steel'))
                    for z in [.26,.31]:leaf.append(beam('rivet',(x-.04,y0,z),(x+.04,y0,z),.014,'bridge_paint',6))
                leaf.append(beam('leaf_end_post',(x,side*2.395,.26),(x,side*2.395,.82),.027))
            for j in range(7):leaf.append(box('cross_girder',(0,side*(.08+j*.37),-.065),(1.88,.055,.09),'bridge_steel'))
            for j in range(5):leaf.append(box('center_dash',(0,side*(.20+j*.46),.147),(.035,.24,.004),'bridge_paint',0))
            leaf.extend([box('counterweight',(0,side*2.87,-.44),(1.37,.52,.39),'bridge_dark'),box('tail_arm',(0,side*2.70,-.19),(.76,.65,.10),'bridge_steel'),box('tail_root',(0,side*2.42,-.10),(.76,.25,.23),'bridge_steel'),beam('leaf_axle',(-1.10,side*2.4,.05),(1.10,side*2.4,.05),.045,'iron',16)])
            node=group('BasculeLeaf',leaf,.56,.80,(0,side*2.40,.05),motion='bascule',axis=(-side,0,0))
            node['basculeAngle']=math.radians(70)
            # Barrier booms are separate from the leaves: road closes before either leaf lifts.
            group('BarrierHousing',[box('barrier_pedestal',(-1.12,side*3.58,.27),(.25,.25,.40),'bridge_steel')],.72,.87)
            boom=[box('barrier_boom',(-.11,side*3.58,.48),(1.98,.065,.065),'bridge_paint',0)]
            for j in range(6):boom.append(box('barrier_stripe',(-.90+j*.32,side*3.58,.48),(.14,.073,.073),'bridge_red',0))
            group('RoadBarrier',boom,.85,.98,(-1.12,side*3.58,.48),motion='road-barrier',axis=(0,-1,0))
        for side in [-1,1]:port('WaterPort',(side*1.50,0,-1.35),'water',(side,0,0),'water-bascule-v1')
        lamps=[]
        for side in [-1,1]:
            x,y=1.08,side*3.75
            lamps.extend([beam('lamp_post',(x,y,0),(x,y,1.25),.03,'iron'),box('lamp_head',(x,y,1.33),(.20,.20,.19),'bridge_paint'),box('lamp_hat',(x,y,1.45),(.28,.28,.06),'bridge_steel')])
        group('BridgeLamps',lamps,.86,.99,tier=2)
        pennant(1.08,3.00,.03)
        root['animationBoundsMin']=[-1.5,-1.85,-4.7];root['animationBoundsMax']=[1.8,3.0,4.7]
    # Temporary centering and scaffold are removed at completion, not baked into the river opening.
    temporary=[]
    for y in [-2.5,-1.3,1.3,2.5]:
        for x in [-.66,.66]:temporary.append(beam('centering_post',(x,y,-1.78),(x,y,-.05),.045,'wood'))
        temporary.append(beam('centering_cross',(-.8,y,-.10),(.8,y,-.10),.05,'wood'))
    group('TemporaryCentering',temporary,.16,.29,temporary=True)
