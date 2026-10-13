"""Fixed-pile jetty and warehouse quay, using the existing vessel waterline at Z=0."""
import math

from mathutils import Vector
from map_element_buildings import build_group, connection


def build(k, kind):
    harbor = kind == 'harbor'
    root = k.pivot('BuildingRoot', (0, 0, 0), [])
    root['buildingType'] = kind
    root['waterline'] = 0
    root['deckHeight'] = .48
    for name, code in {'quay':'8F9890', 'coping':'BDC4B9', 'brick':'B78165',
                       'roof':'577D83', 'paint':'4E807A', 'canvas':'D5B963', 'glass':'78A4AA'}.items():
        mat = k.M['stone'].copy(); mat.name = 'port_'+name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear, 1)
        k.M[name] = mat

    def box(n,p,s,m='wood',bevel=.008): return k.box(n,p,s,m,bevel)
    def beam(n,a,b,r=.025,m='iron',sides=8): return k.beam(n,a,b,r,m,sides)
    def group(n,objects,start,full,anchor=(0,0,0),cover=False,**kw):
        if cover:
            for obj in objects: obj['inspectionCover'] = True
        return build_group(k,root,n,objects,start,full,anchor,**kw)
    def port(n,p,normal,role,width):
        node = connection(k,root,n,p,role)
        node['normalGltf'] = normal
        node['clearWidth'] = width
        return node
    def berth(p,normal,center,angle):
        node = port('Berth',p,normal,'berth',1.90)
        node['profile'] = 'water-channel-v1'
        node['berthLength'] = 4.50
        node['waterDepth'] = .90
        node['waterline'] = 0
        node['vesselCenterGltf'] = [center[0],center[2],-center[1]]
        node['vesselYaw'] = angle
    def crate(x,y,z,size=.52):
        pieces = [box('crate_core',(x,y,z),(size,size,size),'wood_light')]
        for side in [-1,1]:
            for offset in [-.32,.32]:
                pieces.append(box('crate_band',(x+size*offset,y+side*size*.505,z),(.032,.023,size*.94),'wood_dark',.003))
            pieces.append(beam('crate_brace',(x-size*.43,y+side*size*.52,z-size*.39),
                               (x+size*.43,y+side*size*.52,z+size*.39),.015,'wood_dark',4))
        return pieces
    def bollard(x,y):
        return [box('bollard_base',(x,y,.51),(.24,.22,.06),'iron'),
                beam('bollard_post',(x,y,.54),(x,y,.79),.065),
                beam('bollard_cap',(x-.11,y,.76),(x+.11,y,.76),.047)]
    def ring(n,center,radius,plane,material='iron',tube=.016):
        c=Vector(center);a,b=[Vector(v) for v in plane]
        return [beam(n,tuple(c+radius*(a*math.cos(i*math.tau/24)+b*math.sin(i*math.tau/24))),
                     tuple(c+radius*(a*math.cos((i+1)*math.tau/24)+b*math.sin((i+1)*math.tau/24))),tube,material,6) for i in range(24)]
    def ramp(x,y0,y1,z0,z1,width,material):
        vertices=[(x+side*width/2,y,z-d) for d in [.10,0] for side in [-1,1] for y,z in [(y0,z0),(y1,z1)]]
        return k.mesh('shore_ramp',vertices,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],material)

    if harbor:
        group('Foundation',[box('quay_core',(0,0,-.38),(10,7,1.56),'quay',0)],0,.12)
        for row in range(5):
            stones=[]
            for side in [-1,1]:
                for i in range(14):
                    x=-5+(i+.5)*10/14
                    stones.append(box('quay_face_block',(x,side*3.5,-1.12+(row+.5)*.29),(10/14-.012,.14,.282),
                                      'coping' if (i+row)%5==0 else 'quay'))
            for side in [-1,1]:
                for i in range(10):
                    stones.append(box('quay_end_block',(side*5,-3.5+(i+.5)*.7,-1.12+(row+.5)*.29),(.14,.685,.282),'quay'))
            group('QuayCourse',stones,.10+row*.037,.21+row*.037)
        paving=[]
        for i in range(10):
            for j in range(7):paving.append(box('paving',(i-4.5,j-3,.415),(.992,.992,.13),'coping' if (i+j)%4==0 else 'quay',0))
        group('QuayPaving',paving,.34,.50)
        group('ShoreRamp',[ramp(2.2,-5.5,-3.5,.08,.48,2,'quay')],.08,.22)
        entry=port('LandEntrance',(2.2,-5.5,.08),(0,0,1),'road',2)
        entry['profile']='pedestrian-quay-200-v1'
        for x in [-2.35,2.35]:berth((x,3.58,0),(0,0,-1),(x,4.55,0),math.pi/2)
        # Warehouse front wall is split around a real loading opening.
        walls=[box('back_wall',(-2.1,-2.8,1.52),(4.4,.18,2.08),'brick')]
        for x in [-4.3,.1]:walls.append(box('side_wall',(x,-1.05,1.52),(.18,3.5,2.08),'brick'))
        for x in [-3.66,-.54]:walls.append(box('front_wall',(x,.7,1.52),(1.28,.18,2.08),'brick'))
        walls.append(box('door_header',(-2.1,.7,2.47),(1.84,.18,.18),'brick'))
        group('WarehouseWalls',walls,.23,.48)
        port('WarehouseEntrance',(-2.1,.90,.48),(0,0,-1),'pedestrian',1.70)
        trim=[]
        for x in [-4.3,.1]:
            for y in [-2.8,.7]:trim.append(box('corner_post',(x,y,1.56),(.21,.21,2.16),'coping'))
        for x in [-3.02,-1.18]:trim.append(box('loading_jamb',(x,.80,1.46),(.10,.12,1.96),'wood_dark'))
        trim.append(box('door_rail',(-2.1,.87,2.51),(4.04,.10,.10),'iron'))
        group('WarehouseFrame',trim,.43,.63)
        roof=[]
        # A gable roof has matching end infill; its overhang stays inside the quay footprint.
        for side in [-1,1]:
            for row in range(5):
                xa=-2.1+side*row*.48;xb=-2.1+side*(row+1)*.48
                za=3.40-row*.168;zb=3.40-(row+1)*.168
                v=[(x,y,z-d) for d in [0,.065] for x,z in [(xa,za),(xb,zb)] for y in [-3.02,.92]]
                roof.append(k.mesh('roof_course',v,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],'roof'))
        for y in [-2.8,.7]:
            v=[(x,y+dy,z) for dy in [-.08,.08] for x,z in [(-4.3,2.56),(.1,2.56),(.1,2.565),(-2.1,3.335),(-4.3,2.565)]]
            roof.append(k.mesh('gable_infill',v,[(0,1,2,3,4),(5,9,8,7,6)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)],'brick'))
        roof.append(beam('ridge_cap',(-2.1,-3.07,3.42),(-2.1,.97,3.42),.06,'roof',8))
        group('WarehouseRoof',roof,.58,.78,cover=True)
        for side in [-1,1]:
            cx=-2.1+side*.455
            leaf=[box('sliding_plank',(cx+(i-2)*.177,.835,1.435),(.169,.065,1.89),'wood_light') for i in range(5)]
            for z in [.75,2.10]:leaf.append(box('door_strap',(cx,.88,z),(.85,.026,.055),'iron'))
            leaf.append(beam('door_brace',(cx-.40,.884,.52),(cx+.40,.884,2.35),.025,'wood_dark',4))
            door=group('WarehouseDoor',leaf,.69,.85,(cx,.835,.48),motion='sliding-door',axis=(side,0,0))
            door['slideTravel']=.98
        storage=[]
        for x in [-3.57,-.62]:
            for y in [-2.0,-.90]:
                storage.extend(crate(x,y,.79,.60))
                if y< -1:storage.extend(crate(x,y,1.39,.60))
        storage += [box('sorting_table',(-2.1,-2.20,1.16),(1.20,.60,.09),'wood_light')]
        for x in [-2.58,-1.62]:
            for y in [-2.4,-2.0]:storage.append(box('table_leg',(x,y,.81),(.06,.06,.66),'wood_dark'))
        group('WarehouseStorage',storage,.75,.92)
        fittings=[]
        for x in [-4.55,-.15,4.55]:fittings.extend(bollard(x,3.27))
        for x in [-4.2,-.5,1.0,4.2]:
            fittings.append(box('quay_fender',(x,3.64,-.015),(.18,.20,.90),'wood_dark'))
        group('BerthFittings',fittings,.71,.92)
        crane_base=(2.65,1.88,.48);tip=(2.65,4.26,3.56);travel=1.10;radius=.16
        upgrades=[]
        for x,y in [(3.7,-1.3),(4.3,-1.3),(3.7,-.65)]:upgrades.extend(crate(x,y,.77,.56))
        upgrades += [box('weighing_platform',(2.3,-1.4,.53),(1.6,1.3,.10),'iron'),
                     beam('scale_column',(1.56,-1.4,.58),(1.56,-1.4,1.61),.045),
                     box('scale_readout',(1.56,-1.4,1.61),(.28,.17,.25),'paint')]
        group('CargoYardUpgrade',upgrades,.83,.98,tier=2)
        root['animationBoundsMin']=[-5.2,-1.2,-4.70]
        root['animationBoundsMax']=[5.2,4.1,5.60]
    else:
        base=[box('shore_abutment',(0,-3.45,-.11),(1.60,2.10,.38),'quay',0)]
        piles=[]
        positions=[(side*.64,y) for side in [-1,1] for y in [-2.40,-.80,.80,2.65]]
        positions += [(side*2.3,y) for side in [-1,1] for y in [2.15,3.20]]
        for x,y in positions:
            piles += [beam('timber_pile',(x,y,-.90),(x,y,.36),.095,'wood_dark',10),
                      beam('pile_band',(x,y,.14),(x,y,.23),.100,'iron',10)]
        group('Foundation',base+piles,0,.14)
        frame=[]
        for x in [-.64,.64]:frame.append(box('stringer',(x,.40,.29),(.17,6.0,.14),'wood_dark'))
        for y in [2.15,3.20]:frame.append(box('headstock',(0,y,.28),(5.4,.18,.16),'wood_dark'))
        for y in [-2.40,-.8,.8,2.65]:
            frame.append(beam('pile_cross_brace',(-.64,y,-.48),(.64,y,.26),.055,'wood',6))
        group('PierFrame',frame,.16,.38)
        group('ShoreRamp',[ramp(0,-4.60,-2.60,.08,.48,1.60,'wood')],.20,.40)
        port('LandEntrance',(0,-4.60,.08),(0,0,1),'pedestrian',1.6)
        for batch in range(4):
            planks=[]
            for i in range(batch*8,(batch+1)*8):
                y=-2.6+(i+.5)*4.6/32
                planks.append(box('deck_plank',(0,y,.42),(1.60,4.6/32-.008,.12),'wood_light' if i%5==0 else 'wood',.004))
            group('StemDeck',planks,.30+batch*.055,.43+batch*.055)
        head=[box('head_plank',(0,2+(i+.5)*1.4/8,.42),(5.4,1.4/8-.008,.12),'wood_light' if i%3==0 else 'wood',.004) for i in range(8)]
        group('CrossheadDeck',head,.52,.69)
        fittings=[]
        for x,y in [(-.66,-2.1),(.66,-2.1),(-2.35,2.75),(2.35,2.75)]:fittings.extend(bollard(x,y))
        for side in [-1,1]:
            for y in [-1.8,.8]:fittings.append(box('rubbing_strip',(side*.855,y,.27),(.10,.42,.34),'wood_dark'))
            berth((side*.88,-.5,0),(side,0,0),(side*1.80,-.5,0),0)
        group('MooringFittings',fittings,.68,.84)
        ladder=[]
        for x in [1.35,1.75]:ladder.append(beam('ladder_rail',(x,3.51,-.60),(x,3.51,.99),.026))
        for i in range(6):ladder.append(beam('ladder_rung',(1.35,3.51,-.50+i*.26),(1.75,3.51,-.50+i*.26),.022))
        group('AccessLadder',ladder,.75,.91)
        crane_base=(-.64,-.5,.48);tip=(-1.66,-.5,2.24);travel=.50;radius=.10
        bench=[box('bench_seat',(1.20,2.70,.91),(1.65,.45,.09),'wood_light')]
        for x in [.54,1.86]:bench.append(box('bench_support',(x,2.70,.69),(.12,.40,.42),'wood_dark'))
        bench+=ring('lifering',(2.36,2.45,1.04),.19,[(1,0,0),(0,0,1)],'canvas',.040)
        bench += [beam('ring_stand',(2.36,2.49,.48),(2.36,2.49,1.30),.026)]
        group('RestAndRescue',bench,.84,.99,tier=2)
        root['animationBoundsMin']=[-2.9,-.96,-3.62]
        root['animationBoundsMax']=[2.9,2.80,4.72]

    # The hoist has a fixed jib and a single fall. Cable length and both wheels share one phase.
    base=Vector(crane_base);p=Vector(tip);h=Vector((p.x-base.x,p.y-base.y,0)).normalized()
    axle=Vector((-h.y,h.x,0));z=Vector((0,0,1));pulley_radius=.14 if harbor else .09
    mast_top=Vector((base.x,base.y,p.z+.12))
    structure=[box('crane_foot',tuple(base+z*.055),(.64,.64,.11),'iron'),
               beam('mast',tuple(base),tuple(mast_top),.105 if harbor else .075,'paint',10),
               beam('jib',tuple(mast_top-z*.25),tuple(p),.085 if harbor else .055,'paint',8),
               beam('jib_brace',tuple(base+z*.65),tuple(p),.06 if harbor else .04,'iron',8)]
    for side in [-1,1]:
        structure.append(beam('foot_brace',tuple(base+axle*side*.27),tuple(base+z*.70),.036,'iron'))
    group('CraneStructure',structure,.47,.76)
    drum_center=base+z*.78
    drum_parts=[beam('drum_axle',tuple(drum_center-axle*.29),tuple(drum_center+axle*.29),.027),
                beam('drum_barrel',tuple(drum_center-axle*.15),tuple(drum_center+axle*.15),radius,'wood_dark',16)]
    for side in [-1,1]:drum_parts.extend(ring('drum_cheek',tuple(drum_center+axle*side*.18),radius*1.17,[tuple(h),tuple(z)],'iron',.018))
    drum_parts += [beam('crank_arm',tuple(drum_center+axle*.25),tuple(drum_center+axle*.25+z*radius*1.8),.022),
                   beam('crank_handle',tuple(drum_center+axle*.25+z*radius*1.8),tuple(drum_center+axle*.42+z*radius*1.8),.023,'wood_light')]
    drum=group('HoistDrum',drum_parts,.73,.93,tuple(drum_center),motion='hoist-wheel',axis=tuple(axle))
    drum['hoistRadius']=radius
    sheave_parts=ring('tip_sheave',tuple(p),pulley_radius,[tuple(h),tuple(z)],'iron',.013)
    for i in range(4):
        a=i*math.pi/2
        sheave_parts.append(beam('sheave_spoke',tuple(p),tuple(p+pulley_radius*(h*math.cos(a)+z*math.sin(a))),.011))
    sheave=group('HoistSheave',sheave_parts,.73,.93,tuple(p),motion='hoist-wheel',axis=tuple(axle))
    sheave['hoistRadius']=pulley_radius
    # A tangent incoming rope wraps the sheave before its vertical free end.
    exit_point=drum_center+z*radius
    diff=exit_point-p
    phi=math.atan2(diff.z,diff.dot(h));angle=(phi-math.acos(pulley_radius/diff.length))%math.tau
    tangent=p+pulley_radius*(h*math.cos(angle)+z*math.sin(angle))
    feed=[beam('incoming_rope',tuple(exit_point),tuple(tangent),.010,'rope',6)]
    for i in range(12):
        a=angle*(1-i/12);b=angle*(1-(i+1)/12)
        feed.append(beam('sheave_rope',tuple(p+pulley_radius*(h*math.cos(a)+z*math.sin(a))),tuple(p+pulley_radius*(h*math.cos(b)+z*math.sin(b))),.010,'rope',6))
    group('FixedHoistLine',feed,.77,.95)
    top=p+h*pulley_radius;hook=Vector((top.x,top.y,1.35))
    cable=group('HoistCable',[beam('lifting_rope',tuple(top),tuple(hook),.010,'rope',8)],.80,.97,tuple(top),motion='hoist-cable')
    cable['hoistLength']=top.z-hook.z
    load=[]
    hook_center=hook-z*.065
    for i in range(14):
        a=math.radians(45+270*i/14);b=math.radians(45+270*(i+1)/14)
        load.append(beam('open_hook',tuple(hook_center+.060*(h*math.cos(a)+z*math.sin(a))),tuple(hook_center+.060*(h*math.cos(b)+z*math.sin(b))),.016))
    load.append(beam('hook_shank',tuple(hook),tuple(hook-z*.053),.021))
    cargo=hook-z*.72;size=.52 if harbor else .46
    load += crate(cargo.x,cargo.y,cargo.z,size)
    for dx in [-1,1]:
        for dy in [-1,1]:load.append(beam('cargo_sling',tuple(hook-z*.12),(cargo.x+dx*size*.40,cargo.y+dy*size*.40,cargo.z+size*.50),.009,'rope',6))
    suspended=group('HoistLoad',load,.80,.97,tuple(hook),motion='hoist-load')
    for node in [drum,sheave,cable,suspended]:node['hoistTravel']=travel
    # Construction-only material stacks do not remain after completion.
    group('TemporaryMaterials',[box('timber_stack',(3.8,-2.6,.65),(.9,.55,.34),'wood_light') if harbor else box('timber_stack',(0,-3.5,.49),(1.1,.40,.24),'wood_light')],.10,.25,temporary=True)
    return root
