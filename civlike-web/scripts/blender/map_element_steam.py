"""Game-scale 0-6-0 tank engine with independently inspectable crank-slider gear."""
import math


def build(k):
    b=k.bpy
    for name,code in {'engine_green':'44756B','engine_red':'AD5144','steel':'AAB5B5','coal':'323B3D','smoke':'BDCBCB'}.items():
        mat=k.M['iron'].copy();mat.name=name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color=(*linear,1);mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*linear,1);k.M[name]=mat
    root=k.pivot('SteamLocomotive',(0,0,0),[])
    for key,value in {'vehicleKind':'steam-locomotive','routeProfile':'narrow-rail-0668-v1','wheelbase':1.1,'track':.72,'cargoSlots':0,'accessKind':''}.items():root[key]=value
    def attach(o,parent=root):
        b.context.view_layer.update();world=o.matrix_world.copy();o.parent=parent;o.matrix_world=world;return o
    def box(name,p,size,mat='iron',parent=root):return attach(k.box(name,p,size,mat,.007),parent)
    def beam(name,a,c,r=.018,mat='iron',parent=root):return attach(k.beam(name,a,c,r,mat,12),parent)
    def pivot(name,p,parent=root,**extras):
        o=attach(k.pivot(name,p,[]),parent)
        for key,value in extras.items():o[key]=value
        return o
    def ring(name,x,y,z,r,width,thick,mat,parent=root):
        vertices=[(x+dx,y+math.sin(i*math.tau/24)*radius,z+math.cos(i*math.tau/24)*radius) for dx in [-width/2,width/2] for radius in [r-thick,r] for i in range(24)]
        faces=[(a+i,a+(i+1)%24,c+(i+1)%24,c+i) for a,c in [(0,24),(24,72),(72,48),(48,0)] for i in range(24)]
        return attach(k.mesh(name,vertices,faces,mat),parent)
    def anchor(name,p,parent=root):return pivot('GearAnchor_'+name,p,parent,steamAnchor=name)
    def rod(a,c,length):
        o=pivot('Rod_'+a+'_'+c,(0,0,0),steamRod=[a,c],rodLength=length)
        # Unit Y-up rod after export: endpoints are local (0,0,0) and (0,1,0).
        beam('steel_rod',(0,0,0),(0,0,1),.014,'steel',o)
    for axle,y in enumerate([-.55,0,.55]):
        beam('axle',(-.405,y,.27),(.405,y,.27),.042)
        for side in [-1,1]:
            wheel=pivot('DriverWheel',(side*.36,y,.27),vehicleWheel=True,wheelRadius=.27,wheelSide=side)
            ring('steel_tyre',side*.36,y,.27,.27,.07,.034,'steel',wheel)
            ring('inner_flange',side*.326,y,.27,.287,.018,.05,'iron',wheel)
            beam('hub',(side*.31,y,.27),(side*.41,y,.27),.055,'engine_red',wheel)
            phase=0 if side<0 else math.pi/2
            for i in range(12):
                a=i*math.tau/12;beam('spoke',(side*.36,y,.27),(side*.36,y+math.sin(a)*.229,.27+math.cos(a)*.229),.013,'engine_red',wheel)
            pin=(side*.44,y-math.sin(phase)*.065,.27+math.cos(phase)*.065)
            beam('crank',(side*.40,y,.27),pin,.022,'engine_red',wheel)
            beam('crank_pin',(side*.41,pin[1],pin[2]),(side*.46,pin[1],pin[2]),.019,'steel',wheel)
            anchor(f'pin{side}_{axle}',pin,wheel)
    for side in [-1,1]:
        rod(f'pin{side}_0',f'pin{side}_1',.55);rod(f'pin{side}_1',f'pin{side}_2',.55)
        cross=pivot('Crosshead',(side*.44,-1.015,.27),steamCrosshead=side,connectingLength=.47)
        box('crosshead_block',(side*.44,-1.015,.27),(.06,.085,.065),'steel',cross)
        anchor(f'cross{side}',(side*.44,-1.015,.27),cross)
        rod(f'pin{side}_0',f'cross{side}',.47)
        anchor(f'piston{side}',(side*.44,-1.20,.27));rod(f'cross{side}',f'piston{side}',0)
        beam('cylinder',(side*.44,-1.31,.27),(side*.44,-1.12,.27),.105)
        for z in [.22,.32]:beam('slide_bar',(side*.44,-1.095,z),(side*.44,-.89,z),.012,'steel')
    box('main_frame',(0,0,.38),(.59,2.08,.10))
    box('running_plate',(0,0,.565),(.98,2.20,.055))
    beam('boiler',(0,-.88,.89),(0,.58,.89),.287,'engine_green')
    beam('smokebox',(0,-1.06,.89),(0,-.88,.89),.292)
    beam('smokebox_door',(0,-1.08,.89),(0,-1.06,.89),.251)
    beam('door_latch',(-.06,-1.087,.89),(.06,-1.087,.89),.016,'steel')
    for y in [-.70,-.10,.43]:
        points=[(.295*math.sin(i*math.tau/24),y,.89+.295*math.cos(i*math.tau/24)) for i in range(25)]
        for a,c in zip(points,points[1:]):beam('boiler_band',a,c,.009,'gold')
    beam('chimney',(0,-.91,1.13),(0,-.91,1.49),.078)
    beam('chimney_rim',(0,-.91,1.47),(0,-.91,1.51),.10)
    beam('steam_dome',(0,-.25,1.13),(0,-.25,1.31),.10,'gold')
    for side in [-1,1]:
        box('water_tank',(side*.32,.05,.855),(.23,1.09,.43),'engine_green')
        beam('tank_fill',(side*.32,.08,1.07),(side*.32,.08,1.10),.048,'gold')
        beam('side_handrail',(side*.43,-.68,1.03),(side*.43,.56,1.03),.010,'steel')
        for y in [-.63,.48]:beam('handrail_stanchion',(side*.4,y,1.03),(side*.44,y,1.03),.012)
        box('cab_lower',(side*.43,.77,.78),(.04,.50,.38),'engine_green')
        for y in [.52,1.03]:beam('cab_pillar',(side*.43,y,.94),(side*.43,y,1.39),.023,'engine_green')
        box('cab_window_sill',(side*.43,.77,1.02),(.06,.51,.035),'gold')
        box('step',(side*.48,.93,.42),(.17,.30,.035))
        beam('step_bracket',(side*.43,.91,.43),(side*.43,.91,.59),.018)
    box('cab_rear_lower',(0,1.03,.78),(.90,.045,.38),'engine_green')
    box('cab_front_lower',(0,.52,.79),(.87,.045,.38),'engine_green')
    for x in [-.43,0,.43]:box('front_window_frame',(x,.52,1.19),(.035,.045,.35),'engine_green')
    box('window_top',(0,.52,1.38),(.90,.05,.035),'engine_green')
    roof=[(x,y,1.42+.065*(1-abs(x)/.50)) for y in [.43,1.12] for x in [-.50,-.25,0,.25,.50]]
    attach(k.mesh('curved_cab_roof',roof,[(i,i+1,i+6,i+5) for i in range(4)],'iron'))
    box('cab_floor',(0,.79,.63),(.84,.47,.035),'wood_dark')
    beam('firebox_back',(0,.55,.67),(0,.58,.67),.14)
    for x in [-.15,.15]:beam('control_pipe',(x,.58,.72),(x,.58,1.04),.012,'gold')
    box('coal_bunker',(0,1.11,.87),(.78,.13,.40),'engine_green')
    for i in range(9):attach(k.ico('coal_piece',((i%3-1)*.19,1.105,.98+(i//3)*.018),(.095,.065,.055),'coal',1))
    for end in [-1,1]:
        box('buffer_beam',(0,end*1.22,.45),(1.04,.075,.15),'engine_red')
        for side in [-1,1]:
            beam('buffer',(side*.30,end*1.24,.46),(side*.30,end*1.37,.46),.033)
            box('buffer_plate',(side*.30,end*1.37,.46),(.13,.03,.13),'steel')
        port=pivot('Coupler',(0,end*1.42,.42),vehicleCoupler=end);port['normalGltf']=[0,0,-end]
        beam('drawbar',(0,end*1.23,.42),(0,end*1.42,.42),.028)
    for i in range(10):
        p=(0,-.91+i*.025,1.53+i*.07)
        puff=pivot('Exhaust',p,steamPuff=i)
        attach(k.ico('steam_cloud',p,(.09,.10,.11),'smoke',1),puff)
    root['animationBoundsMin']=[-.60,-.017,-1.46];root['animationBoundsMax']=[.60,2.50,1.46]
    b.context.view_layer.update()
    anchors={o['steamAnchor']:o for o in b.context.scene.objects if o.get('steamAnchor')}
    for o in b.context.scene.objects:
        if 'steamCrosshead' in o:
            pin=anchors[f'pin{o["steamCrosshead"]}_0'].matrix_world.translation
            o.location.y=pin.y-math.sqrt(.47**2-(pin.z-.27)**2)
    b.context.view_layer.update()
    for o in b.context.scene.objects:
        if 'steamRod' in o:
            a,c=[anchors[name].matrix_world.translation for name in o['steamRod']];delta=c-a
            o.location=a;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.scale.z=delta.length
