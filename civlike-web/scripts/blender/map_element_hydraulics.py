"""Open masonry water channels with inspectable beds and a rising sluice."""
import math
from map_element_buildings import build_group, connection


def build(k,kind):
    elevated=kind=='aqueduct';length=8.6 if elevated else 4.8;bed=2.08 if elevated else .12
    root=k.pivot('BuildingRoot',(0,0,0),[]);root['buildingType']=kind;root['channelWidth']=.64;root['channelBed']=bed
    for name,code in {'hydro_stone':'A9ADA1','hydro_light':'CAD0BC','hydro_joint':'858E85','hydro_water':'418F9D',
                      'hydro_silt':'9F9571','hydro_grass':'7C9B67','hydro_tuft':'99B874','hydro_paint':'CF765C'}.items():
        mat=k.M['stone'].copy();mat.name=name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color=(*linear,1);shader=mat.node_tree.nodes['Principled BSDF'];shader.inputs['Base Color'].default_value=(*linear,1)
        if name=='hydro_water':shader.inputs['Roughness'].default_value=.24;shader.inputs['Metallic'].default_value=.12
        k.M[name]=mat
    def box(n,p,s,m='hydro_stone',bevel=.009):return k.box(n,p,s,m,bevel)
    def beam(n,a,b,r=.025,m='iron',sides=8):return k.beam(n,a,b,r,m,sides)
    def group(n,parts,start,full,anchor=(0,0,0),**kw):return build_group(k,root,n,parts,start,full,anchor,**kw)
    for side in [-1,1]:
        node=connection(k,root,'ChannelPort',(0,side*length/2,bed),'water')
        node['normalGltf']=[0,0,-side];node['profile']='open-channel-064-v1';node['waterDepth']=.18;node['flowRole']='inlet' if side>0 else 'outlet'
    if elevated:
        piers=[-3.75,-1.25,1.25,3.75]
        group('Foundation',[box('pier_foot',(0,y,.09),(1.38,.90,.18),'hydro_joint') for y in piers],0,.12)
        for row in range(6):
            parts=[]
            for y in piers:
                for side in [-1,1]:parts.append(box('pier_block',(side*.245,y,.18+(row+.5)*.27),(.48,.42,.26),'hydro_light' if (row+int(y*4))%4==0 else 'hydro_stone'))
            group('PierCourse',parts,.09+row*.045,.18+row*.045)
        group('PierCaps',[box('pier_cap',(0,y,1.88),(1.06,.46,.18),'hydro_light') for y in piers],.45,.61)
        for center in [-2.5,0,2.5]:
            for batch in range(3):
                parts=[]
                for i in range(batch*5,(batch+1)*5):
                    a=i*math.pi/15;b=(i+1)*math.pi/15
                    verts=[(x,center+r*math.cos(t),.42+r*math.sin(t)) for x in [-.53,.53] for r,t in [(1.04,a),(1.24,a),(1.24,b),(1.04,b)]]
                    parts.append(k.mesh('aqueduct_voussoir',verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'hydro_light' if i%3 else 'hydro_stone'))
                group('ArchSection',parts,.34+batch*.045,.46+batch*.045)
            fill=[]
            for i in range(20):
                y0=center-1.24+i*2.48/20;y1=y0+2.48/20
                z0=.42+math.sqrt(max(0,1.24**2-(y0-center)**2));z1=.42+math.sqrt(max(0,1.24**2-(y1-center)**2))
                verts=[(x,y,z) for x in [-.50,.50] for y,z in [(y0,z0),(y1,z1),(y1,1.96),(y0,1.96)]]
                fill.append(k.mesh('arch_spandrel',verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'hydro_stone'))
            group('Spandrel',fill,.51,.66)
        # End abutments carry the channel all the way to its end faces.
        for row in range(7):
            parts=[]
            for side in [-1,1]:
                for x in [-.252,.252]:parts.append(box('end_pier_course',(x,side*4.04,(row+.5)*.28),(.496,.52,.274),'hydro_light' if row%3==0 else 'hydro_stone'))
            group('EndAbutment',parts,.12+row*.025,.25+row*.025)
    else:
        ground=[box('earth_core',(0,0,.035),(2.70,4.8,.07),'earth',.015)]
        for side in [-1,1]:ground.append(box('bank_grass',(side*.995,0,.083),(.71,4.8,.026),'hydro_grass',.01))
        group('Foundation',ground,0,.12)
        for row in range(8):
            parts=[];y=-2.1+row*.6
            for side in [-1,1]:
                for j in range(3):
                    x=side*(.76+j*.20);yy=y+k.RNG.uniform(-.18,.18)
                    parts.append(k.ico('bank_pebble',(x,yy,.105),(k.RNG.uniform(.025,.055),.05,.026),'hydro_joint'))
                    if j!=1:
                        for n in range(3):
                            angle=k.RNG.random()*math.tau;h=.10+k.RNG.random()*.13;dx=math.cos(angle);dy=math.sin(angle);w=.022
                            points=[(x-dy*w,yy+dx*w,.10),(x+dy*w,yy-dx*w,.10),(x+dx*.065,yy+dy*.065,.10+h*.72),(x+dx*.12,yy+dy*.12,.10+h)]
                            parts.append(k.mesh('folded_bank_grass',points,[(0,1,2),(0,2,3)],'hydro_tuft'))
            group('BankDetails',parts,.65+row*.015,.76+row*.015)
    for section in range(8):
        y0=-length/2+section*length/8;y1=y0+length/8;center=(y0+y1)/2
        group('ChannelBed',[box('lined_channel_bed',(0,center,bed-.055),(1.06,length/8,.11),'hydro_joint',0),box('silt_lining',(0,center,bed-.002),(.64,length/8,.004),'hydro_silt',0)],.55+section*.015 if elevated else .10+section*.022,.67+section*.015 if elevated else .18+section*.022)
        banks=[]
        for side in [-1,1]:
            for row in range(2):banks.append(box('bank_masonry',(side*.475,center,bed+.10+row*.19),(.27,length/8-.01,.19),'hydro_light' if (section+row)%4==0 else 'hydro_stone'))
            banks.append(box('bank_coping',(side*.475,center,bed+.408),(.30,length/8,.056),'hydro_light'))
        group('ChannelWall',banks,.65+section*.019 if elevated else .27+section*.035,.77+section*.019 if elevated else .39+section*.035)
    if not elevated:
        frame=[]
        for side in [-1,1]:
            frame.extend([box('guide_back',(side*.40,0,.62),(.03,.19,1.0),'iron'),box('guide_foot',(side*.43,0,.14),(.13,.27,.04),'iron')])
            for y in [-.085,.085]:frame.append(box('guide_flange',(side*.365,y,.62),(.095,.035,1.0),'iron'))
        frame.extend([box('sluice_crosshead',(0,0,1.14),(.88,.20,.09),'teal'),box('screw_nut',(0,0,1.20),(.12,.13,.10),'iron')])
        group('SluiceFrame',frame,.58,.78)
        plate=[box('sluice_plate',(0,0,.30),(.69,.08,.36),'teal'),box('gate_rib',(0,-.052,.30),(.62,.045,.05),'iron'),beam('rising_stem',(0,0,.47),(0,0,1.51),.025,'iron',12)]
        for i in range(96):
            a=i*math.tau/12;b=(i+1)*math.tau/12
            plate.append(beam('screw_thread',(.03*math.cos(a),.03*math.sin(a),.50+i*.010),(.03*math.cos(b),.03*math.sin(b),.50+(i+1)*.010),.008,'hydro_light',4))
        gate=group('SluiceGate',plate,.76,.93,motion='hydro-gate');gate['gateTravel']=.36
        wheel=[];radius=.21;z=1.255
        for i in range(16):
            a=i*math.tau/16;b=(i+1)*math.tau/16
            wheel.append(beam('handwheel_rim',(radius*math.cos(a),radius*math.sin(a),z),(radius*math.cos(b),radius*math.sin(b),z),.021,'hydro_paint'))
        for i in range(4):
            a=i*math.pi/2;wheel.append(beam('handwheel_spoke',(.04*math.cos(a),.04*math.sin(a),z),(.20*math.cos(a),.20*math.sin(a),z),.014,'hydro_paint'))
        # Fixed rotating nut and rising non-rotating stem: the handwheel does not climb with the gate.
        obj=group('SluiceHandwheel',wheel,.83,.96,(0,0,z),motion='hydro-wheel',axis=(0,0,1));obj['screwTurns']=3
        maintenance=[box('service_paving',(.96,-.1,.12),(.62,1.2,.045),'hydro_joint')]
        for i in range(7):maintenance.append(box('gauge_tick',(-.365,-.093,.18+i*.055),(.035,.018,.012),'wool_light',0))
        maintenance.extend([beam('rake_handle',(.85,.5,.14),(.92,.64,1.0),.016,'wood'),box('rake_head',(.85,.5,.14),(.30,.055,.04),'iron')])
        group('Maintenance',maintenance,.87,.99,tier=2)
    else:
        walkway=[]
        for i in range(14):
            y=-4.0+i*8.0/13
            walkway.extend([box('inspection_plank',(.82,y,2.12),(.39,.59,.055),'wood_light'),beam('walkway_bracket',(.49,y,1.83),(1.01,y,2.09),.03,'iron')])
            if i%2==0 or i==13:walkway.append(beam('safety_post',(1.0,y,2.12),(1.0,y,2.68),.022,'iron'))
        for z in [2.42,2.68]:walkway.append(beam('safety_rail',(1.0,-4.0,z),(1.0,4.0,z),.018,'iron'))
        group('InspectionWalkway',walkway,.85,.99,tier=2)
    for role,y0,y1 in [('free',-length/2,length/2)] if elevated else [('upstream',.043,length/2),('downstream',-length/2,-.043)]:
        rows=80 if elevated else 32;cols=8
        vertices=[(-.32+i*.64/cols,y0+j*(y1-y0)/rows,bed+.18) for j in range(rows+1) for i in range(cols+1)]
        faces=[(j*(cols+1)+i,j*(cols+1)+i+1,(j+1)*(cols+1)+i+1,(j+1)*(cols+1)+i) for j in range(rows) for i in range(cols)]
        boundary=list(range(cols+1))+[j*(cols+1)+cols for j in range(1,rows+1)]+[rows*(cols+1)+i for i in range(cols-1,-1,-1)]+[j*(cols+1) for j in range(rows-1,0,-1)]
        base=len(vertices);vertices.extend([(vertices[i][0],vertices[i][1],bed) for i in boundary])
        faces.extend([(boundary[i],base+i,base+(i+1)%len(boundary),boundary[(i+1)%len(boundary)]) for i in range(len(boundary))])
        faces.append(tuple(reversed(range(base,len(vertices)))))
        water=k.mesh('channel_water',vertices,faces,'hydro_water')
        node=group('WaterSurface',[water],.93,1)
        node['channelWater']=role;node['channelBed']=bed;node['channelWidth']=.64
        node['channelExtent']=[-y1,-y0]
    root['animationBoundsMin']=[-.80 if elevated else -1.38,-.02,-length/2-.10]
    root['animationBoundsMax']=[1.08 if elevated else 1.38,2.85 if elevated else 1.95,length/2+.10]
