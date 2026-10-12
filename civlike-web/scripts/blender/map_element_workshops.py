"""Distinct village service buildings with open working spaces and authored mechanisms."""
import math
from mathutils import Matrix
from map_element_buildings import build_group, connection

KINDS = ('stable', 'blacksmith', 'market-hall')


def build(k, kind):
    root = k.pivot('BuildingRoot', (0, 0, 0), [])
    root['buildingType'] = kind
    for name, code in {'plaster':'D7D2BD','slate':'617783','leather':'71504A','canvas':'E1D9B9','ember':'E99639'}.items():
        mat = k.M['wood'].copy(); mat.name = 'workshop_'+name
        rgb = [int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear = [c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        shader=mat.node_tree.nodes['Principled BSDF'];shader.inputs['Base Color'].default_value=(*linear,1)
        if name=='ember':shader.inputs['Emission Color'].default_value=(*linear,1);shader.inputs['Emission Strength'].default_value=1.4
        k.M[name]=mat
    def group(name, objects, start, full, anchor=(0,0,0), **kwargs):
        return build_group(k,root,name,objects,start,full,anchor,**kwargs)
    def box(name,p,size,mat='wood',bevel=.012):return k.box(name,p,size,mat,bevel)
    def beam(name,a,b,r=.035,mat='wood_dark',sides=6):return k.beam(name,a,b,r,mat,sides)
    def socket(name,p,role,normal=(0,0,1)):
        node=connection(k,root,name,p,role);node['normalGltf']=normal
        return node
    def pitched_roof(w,d,eaves,rise,cx=0,cy=0):
        for row in range(6):
            parts=[]
            for side in [-1,1]:
                for col in range(8):
                    a=max(0,row/6-.012);b=min(1,(row+1)/6+.020);y=cy-d/2+col*d/8
                    x0=cx+side*w/2*a;x1=cx+side*w/2*b;z0=eaves+rise*(1-a);z1=eaves+rise*(1-b)
                    verts=[(x0,y,z0),(x1,y,z1),(x1,y+d/8+.014,z1),(x0,y+d/8+.014,z0)]
                    verts += [(x,y,z-.045) for x,y,z in verts]
                    parts.append(k.mesh('overlapping_tile',verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'slate' if kind=='stable' else 'tile'))
            for part in parts:part['inspectionCover']=True
            group('RoofCourse',parts,.59+row*.035,.65+row*.035)
        parts=[beam('ridge',(cx,cy-d/2,eaves+rise+.035),(cx,cy+d/2,eaves+rise+.035),.065,'slate' if kind=='stable' else 'tile')]
        for y in [cy-d/2,cy,cy+d/2]:
            parts.extend([beam('tie_beam',(cx-w*.46,y,eaves-.08),(cx+w*.46,y,eaves-.08),.065),beam('king_post',(cx,y,eaves-.08),(cx,y,eaves+rise-.07),.05)])
            for side in [-1,1]:parts.append(beam('rafter',(cx,y,eaves+rise-.12),(cx+side*w*.49,y,eaves-.10),.055))
        group('RoofTrusses',parts,.45,.60)
    def awning(cx,y,width,depth,z,tier=1):
        verts=[]
        for i in range(17):
            x=cx-width/2+width*i/16
            for j in range(9):
                t=j/8;verts.append((x,y-depth*t,z-.32*t-.10*math.sin(t*math.pi)))
        faces=[(i*9+j,(i+1)*9+j,(i+1)*9+j+1,i*9+j+1) for i in range(16) for j in range(8)]
        cloth=k.mesh('striped_awning',verts,faces,'canvas');cloth.data.materials.append(k.M['teal'])
        for face in cloth.data.polygons:face.material_index=(face.index//16)%2
        group('AwningFabric',[cloth],.80,.94,tier=tier,motion='awning')
        parts=[]
        for x in [cx-width/2,cx+width/2]:
            parts.append(beam('canopy_post',(x,y-depth,.17),(x,y-depth,z-.32),.045))
            parts.append(beam('canopy_rail',(x,y,z),(x,y-depth,z-.32),.025))
        parts.append(beam('front_canopy_beam',(cx-width/2,y-depth,z-.32),(cx+width/2,y-depth,z-.32),.035))
        parts.append(beam('rear_canopy_beam',(cx-width/2,y,z),(cx+width/2,y,z),.035))
        group('AwningFrame',parts,.72,.83,tier=tier)
    def crate(cx,y,z,mat='wood_light'):
        return [box('crate_floor',(cx,y,z),(.62,.55,.06),mat)]+[box('crate_slat',(cx+side*.29,y,z+.14),(.045,.55,.23),mat) for side in [-1,1]]+[box('crate_end',(cx,y+side*.25,z+.14),(.60,.035,.23),mat) for side in [-1,1]]
    w,d=(5.1,4.2) if kind=='market-hall' else (4.9,4.0) if kind=='stable' else (4.2,3.8)
    group('Foundation',[box('stone_plinth',(0,0,.09),(w+.3,d+.3,.18),'stone')],0,.12)
    for row in range(4):
        parts=[]
        for i in range(8):
            x=-w/2+(i+.5)*w/8;y=-d/2+(row+.5)*d/4
            parts.append(box('floor_paving',(x,y,.185),(w/8-.02,d/4-.02,.045),'stone_light' if (i+row)%4 else 'stone'))
        group('FloorCourse',parts,.07+row*.015,.15+row*.015)
    socket('Entrance',(0,-d/2-.18,.18),'road')
    group('Scaffold',[beam('scaffold_upright',(-w/2-.12,y,.12),(-w/2-.12,y,2.2),.045) for y in [-1,1]]+[box('scaffold_board',(-w/2-.12,0,1.25),(.36,2.25,.05))],.22,.38,temporary=True)

    if kind=='stable':
        for level in range(5):
            z=.3+level*.25
            parts=[box('back_board',(0,1.87,z),(4.7,.12,.235),'wood_light')]
            for side in [-1,1]:parts.append(box('side_board',(side*2.34,0,z),(.12,3.75,.235),'wood'))
            group('WallCourse',parts,.12+level*.055,.20+level*.055)
        posts=[]
        for x in [-2.34,-.78,.78,2.34]:
            for y in [-1.85,-.28,1.85]:posts.append(beam('frame_post',(x,y,.2),(x,y,2.15),.075))
        group('FramePosts',posts,.31,.47)
        for x in [-.78,.78]:
            parts=[box('stall_partition',(x,.78,.73),(.06,2.12,1.05),'wood_light')]
            for y in [.05,.4,.75,1.1,1.45]:parts.append(beam('stall_bar',(x,y,1.25),(x,y,1.85),.015,'iron'))
            group('StallPartition',parts,.42,.59)
        for i,cx in enumerate([-1.56,0,1.56]):
            parts=[]
            for j in range(8):parts.append(box('gate_plank',(cx-.65+(j+.5)*1.3/8,-.3,.73),(1.3/8-.014,.055,1.02),'wood'))
            for z in [.4,1.04]:parts.append(box('gate_hinge_strap',(cx,-.335,z),(1.23,.02,.065),'iron'))
            parts.append(beam('diagonal_gate_brace',(cx-.57,-.34,.32),(cx+.57,-.34,1.15),.026,'wood_light'))
            group('StallGate',parts,.64,.80,(cx-.69,-.30,.21),motion='door',axis=(0,0,1),rate=-1)
            rack=[box('manger_bottom',(cx,1.45,.63),(1.1,.42,.06)),box('manger_front',(cx,1.24,.80),(1.1,.05,.34))]
            for dx in [-.55,.55]:rack.append(box('manger_end',(cx+dx,1.45,.8),(.05,.42,.34)))
            for j in range(8):rack.append(beam('hay_rack',(cx-.5+j/7,1.24,1.0),(cx-.5+j/7,1.69,1.52),.018,'iron'))
            rack.append(beam('hay_rack_top',(cx-.52,1.69,1.52),(cx+.52,1.69,1.52),.025,'iron'))
            rack.append(k.ico('loose_hay',(cx,1.54,1.25),(.48,.16,.25),'straw',2))
            for j in range(14):rack.append(beam('hay_stem',(cx+(j%7-3)*.13,1.4,1.13),(cx+(j%7-3)*.12,1.62,1.43+(j%3)*.04),.007,'straw_light',4))
            group('MangerAndHay',rack,.73,.92)
            group('StallBedding',[k.ico('straw_bedding',(cx,.72,.23),(.61,.88,.055),'straw',2)],.85,.97)
            socket('StallSlot'+str(i),(cx,.38,.23),'animal',(0,0,-1))
        pitched_roof(5.15,4.14,2.18,1.0)
        loft=[box('rear_loft',(0,1.38,1.96),(4.5,.83,.08),'wood_dark')]
        for x in [-1.4,0,1.4]:
            loft.append(box('hay_bale',(x,1.38,2.20),(.60,.61,.38),'straw',.045))
            for dx in [-.18,.18]:loft.append(box('bale_binding',(x+dx,1.38,2.20),(.025,.64,.40),'rope'))
        group('HayLoft',loft,.86,.98,tier=2)
        access=[beam('loft_ladder_rail',(2.95,y,.05),(2.36,y,1.97),.025,'wood_light') for y in [1.13,1.63]]
        for i in range(11):
            t=(i+.5)/11;x=2.95-.59*t;z=.05+1.92*t
            access.append(beam('loft_ladder_rung',(x,1.13,z),(x,1.63,z),.024,'wood_dark'))
        group('HayAccess',access,.88,.99,tier=2)
        group('WeatherMast',[beam('weather_mast',(0,.15,3.2),(0,.15,3.72),.026,'iron')],.88,.96)
        group('WeatherVane',[beam('direction_arrow',(-.30,.15,3.67),(.30,.15,3.67),.018,'iron'),k.mesh('arrow_head',[(.31,.15,3.67),(.13,.15,3.80),(.13,.15,3.54)],[(0,1,2)],'gold')],.90,1,(0,.15,3.67),motion='sway',axis=(0,0,1))
    elif kind=='market-hall':
        for row,y in enumerate([-1.9,0,1.9]):
            parts=[]
            for side in [-1,1]:
                x=side*2.30
                parts.extend([box('post_stone_foot',(x,y,.32),(.37,.37,.25),'stone'),beam('oak_post',(x,y,.43),(x,y,2.28),.10)])
                parts.append(beam('knee_brace',(x,y,1.67),(x-side*.52,y,2.20),.06))
            group('ArcadePosts',parts,.18+row*.065,.32+row*.065)
        group('WallPlates',[beam('wall_plate',(side*2.3,-2,2.22),(side*2.3,2,2.22),.095) for side in [-1,1]],.40,.54)
        pitched_roof(5.2,4.4,2.30,1.02)
        for index,(cx,y) in enumerate([(-1.52,-.85),(1.52,-.85),(-1.52,.85),(1.52,.85)]):
            parts=[box('counter_top',(cx,y,.87),(.98,1.22,.07),'wood_light')]
            for dx in [-.39,.39]:
                for dy in [-.48,.48]:parts.append(beam('counter_leg',(cx+dx,y+dy,.21),(cx+dx,y+dy,.85),.045))
            parts.append(box('stall_front',(cx-math.copysign(.48,cx),y,.57),(.045,1.2,.54),'teal' if index%2 else 'wood'))
            group('MarketCounter',parts,.50+index*.04,.67+index*.04)
            goods=crate(cx,y,.93)
            for j in range(12):
                x=cx-.20+(j%3)*.20;yy=y-.16+(j//3)*.10
                if index<2:
                    goods.append(k.ico('produce',(x,yy,1.14+(.07 if j>8 else 0)),(.095,.09,.09),'berry' if index==0 else 'leaf_light',2))
                    goods.append(beam('produce_stem',(x,yy,1.22),(x,yy,1.26),.008,'bark',4))
                elif index==2:goods.append(k.ico('bread_loaf',(x,yy,1.10),(.085,.045,.06),'grain',2))
                else:goods.append(beam('ceramic_pot',(x,yy,1.02),(x,yy,1.18),.075,'tile',10))
            group('StallGoods',goods,.82,.96)
            socket('TradeSlot'+str(index),(math.copysign(.74,cx),y,.21),'trade')
        awning(0,-2.12,3.65,.92,2.12)
        extras=[]
        for side in [-1,1]:
            extras.extend(crate(side*1.65,2.0,.23))
            extras.append(k.ico('grain_sack',(side*1.65,1.97,.67),(.25,.21,.37),'canvas',2))
        group('BulkGoods',extras,.88,.99,tier=2)
        socket('RearEntrance',(0,2.4,.18),'road',(0,0,-1))
    else:
        for level in range(7):
            z=.31+level*.245;parts=[]
            for i in range(7):parts.append(box('rear_stone',(-1.86+(i+.5)*3.72/7,1.74,z),(3.72/7-.015,.22,.232),'stone' if i%3 else 'stone_light'))
            for y in [-1.4,-.85,-.30,.25,.80,1.35]:parts.append(box('side_stone',(-1.93,y,z),(.20,.54,.232),'stone'))
            group('WallCourse',parts,.12+level*.044,.22+level*.044)
        group('WorkshopPosts',[beam('open_front_post',(x,-1.7,.2),(x,-1.7,2.1),.08) for x in [-1.93,1.93]]+[beam('rear_corner',(1.93,1.7,.2),(1.93,1.7,2.1),.08)],.34,.49)
        pitched_roof(4.3,3.85,2.15,.77)
        hearth=[box('hearth_base',(-.86,.94,.51),(1.24,.91,.62),'stone')]
        for side in [-1,1]:hearth.append(box('hearth_cheek',(-.86+side*.59,.94,.99),(.14,.92,.37),'stone'))
        hearth.extend([box('hearth_back',(-.86,1.37,.99),(1.15,.14,.37),'stone'),box('coal_bed',(-.86,.93,.84),(.98,.65,.09),'iron')])
        group('Hearth',hearth,.36,.56)
        hood=[(-1.5,.48,1.28),(-.22,.48,1.28),(-.22,1.48,1.28),(-1.5,1.48,1.28),(-1.10,.89,2.0),(-.62,.89,2.0),(-.62,1.37,2.0),(-1.10,1.37,2.0)]
        group('ForgeHood',[k.mesh('smoke_hood',hood,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'iron')],.57,.73)
        stack=[]
        for row in range(7):stack.append(box('chimney_course',(-.86,1.13,2.0+row*.23),(.57,.58,.22),'stone' if row%2 else 'stone_light'))
        stack.append(box('chimney_cap',(-.86,1.13,3.55),(.72,.73,.09),'stone_light'))
        group('Chimney',stack,.65,.88)
        group('Embers',[k.ico('hot_coal',(-1.15+i*.14,.88+(i%2)*.16,.90),(.09,.08,.065),'ember',1) for i in range(5)],.86,.98,motion='ember')
        anvil=[beam('anvil_stump',(-.70,-.64,.21),(-.70,-.64,.65),.28,'bark',10),box('anvil_foot',(-.70,-.64,.72),(.52,.34,.14),'iron'),box('anvil_waist',(-.70,-.64,.87),(.25,.22,.21),'iron'),box('anvil_face',(-.70,-.64,1.02),(.56,.30,.12),'iron'),k.beam('anvil_horn',(-.44,-.64,1.02),(-.10,-.64,1.02),.12,'iron',8,end=.008)]
        group('Anvil',anvil,.63,.81)
        tools=[box('tool_bench',(1.32,-.75,.82),(.86,1.22,.08),'wood_light')]
        for x in [1.0,1.64]:
            for y in [-1.25,-.25]:tools.append(beam('bench_leg',(x,y,.21),(x,y,.79),.055))
        tools.extend([beam('hammer_handle',(1.10,-1.12,.89),(1.43,-.85,.89),.022,'wood_light'),box('hammer_head',(1.1,-1.12,.90),(.10,.20,.10),'iron')])
        for i in range(3):
            x=1.10+i*.19
            tools.extend([beam('tongs',(x,-.67,.9),(x+.07,-.31,.9),.012,'iron'),beam('tongs',(x+.09,-.67,.9),(x+.04,-.31,.9),.012,'iron')])
        group('ToolBench',tools,.74,.91)
        # Hinged upper leaf, fixed lower leaf and deforming accordion skin share one nozzle anchor.
        cx,hy,hz=.63,.52,.84
        outline=[(cx+math.sin(i*math.tau/20)*(.10+.22*(1-math.cos(i*math.tau/20))*.5),hy+.44*(1-math.cos(i*math.tau/20))) for i in range(20)]
        def leaf(name,z):
            verts=[(x,y,z+dz) for dz in [-.025,.025] for x,y in outline]
            return k.mesh(name,verts,[tuple(range(19,-1,-1)),tuple(range(20,40))]+[(i,(i+1)%20,(i+1)%20+20,i+20) for i in range(20)],'wood_dark')
        lower=[leaf('lower_leaf',hz-.15),beam('air_nozzle',(cx,hy,hz-.055),(-.2,.90,.87),.04,'iron')]
        for x in [cx-.22,cx+.22]:lower.append(beam('bellows_stand',(x,1.0,.21),(x,1.0,hz-.17),.05))
        group('BellowsBase',lower,.61,.77)
        group('BellowsLeaf',[leaf('upper_leaf',hz),beam('bellows_handle',(cx,1.15,hz),(cx,1.51,hz),.034,'wood_light')],.72,.88,(cx,hy,hz),motion='bellows',axis=(1,0,0))
        vertices=[]
        for j in range(5):
            for x,y in outline:
                factor=1+(.07 if j%2 else 0);vertices.append((cx+(x-cx)*factor,hy+(y-hy)*factor,hz-.15+j*.15/4))
        skin=k.mesh('accordion_leather',vertices,[(j*20+i,j*20+(i+1)%20,(j+1)*20+(i+1)%20,(j+1)*20+i) for j in range(4) for i in range(20)],'leather')
        group('BellowsSkin',[skin],.72,.88,(cx,hy,hz),motion='bellows-skin')
        awning(.3,-1.83,2.6,.72,1.99,tier=2)
        socket('ForgeWorkplace',(-.70,-1.23,.21),'craft')
        socket('BellowsWorkplace',(.63,1.53,.21),'craft',(0,0,-1))
    root['animationBoundsMin']=[-w/2-.42,0,-d/2-.50]
    root['animationBoundsMax']=[w/2+.42,3.95,d/2+1.10]
    if kind=='stable':
        # Bake a real footprint that fits the existing adult horse, leaving the runtime root unscaled.
        factor=1.8
        for obj in k.bpy.context.scene.objects:
            obj.location*=factor
            if obj.type=='MESH':obj.data.transform(Matrix.Scale(factor,4))
        for key in ['animationBoundsMin','animationBoundsMax']:root[key]=[v*factor for v in root[key]]
