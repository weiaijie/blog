"""Open-shell sailing craft and powered river barge, waterline at local Z=0."""
import math
from mathutils import Vector

KINDS=('sailboat','river-barge')


def build(k,kind):
    b=k.bpy;sailing=kind=='sailboat'
    for name,code in {'hull_paint':'426F7D','hull_lower':'724D48','canvas':'DADCCB','cabin':'C7CFC7','glass':'75A3B3','steel':'A6B3B1'}.items():
        mat=k.M['wood'].copy();mat.name='vessel_'+name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)];linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color=(*linear,1);shader=mat.node_tree.nodes['Principled BSDF'];shader.inputs['Base Color'].default_value=(*linear,1)
        if name=='glass':shader.inputs['Alpha'].default_value=.32;mat.surface_render_method='DITHERED';mat.use_backface_culling=True
        k.M[name]=mat
    root=k.pivot('VesselRoot',(0,0,0),[]);root['vesselKind']=kind;root['waterline']=0;root['cargoSlots']=0 if sailing else 6
    root['routeProfile']='water-channel-v1'
    def attach(o,parent=root):
        b.context.view_layer.update();world=o.matrix_world.copy();o.parent=parent;o.matrix_world=world;return o
    def box(name,p,size,mat='wood',parent=root):return attach(k.box(name,p,size,mat,.007),parent)
    def beam(name,a,c,w=.015,mat='wood_dark',parent=root):return attach(k.beam(name,a,c,w,mat,8),parent)
    def pivot(name,p,parent=root,**extras):
        o=attach(k.pivot(name,p,[]),parent)
        for key,value in extras.items():o[key]=value
        return o
    stations=[(-1.65,.018,.20),(-1.35,.28,-.12),(-.85,.49,-.28),(-.2,.56,-.34),(.5,.52,-.29),(1.0,.42,-.15),(1.37,.28,.05)] if sailing else [(-1.94,.35,-.02),(-1.56,.65,-.27),(-.9,.69,-.29),(.1,.69,-.29),(1.12,.66,-.26),(1.70,.51,-.07)]
    top=.37 if sailing else .32
    rings=[[(x*w,y,z) for x,z in [(-1,top),(-.92,.03),(-.68,bottom+.035),(0,bottom),(.68,bottom+.035),(.92,.03),(1,top)]] for y,w,bottom in stations]
    outer=[p for ring in rings for p in ring];inner=[(x*.94,y,z+.032) for x,y,z in outer];n=len(outer);faces=[]
    for j in range(len(stations)-1):
        for i in range(6):
            a=j*7+i;faces.extend([(a,a+7,a+8,a+1),(a+n+1,a+n+8,a+n+7,a+n)])
        for i in [0,6]:a=j*7+i;faces.append((a,a+n,a+n+7,a+7))
    for j in [0,len(stations)-1]:
        for i in range(6):a=j*7+i;faces.append((a,a+1,a+n+1,a+n))
    hull=attach(k.mesh('watertight_hull_shell',outer+inner,faces,'hull_paint'))
    hull.data.materials.append(k.M['hull_lower']);hull.data.materials.append(k.M['wood_light'])
    for face in hull.data.polygons:
        center=sum((hull.data.vertices[i].co for i in face.vertices),Vector())/len(face.vertices)
        face.material_index=1 if center.z<0 else 2 if face.index%2 else 0
    for side in [-1,1]:
        for j in range(len(stations)-1):
            y,w,_=stations[j];yy,ww,_=stations[j+1]
            beam('gunwale',(side*w,y,top+.012),(side*ww,yy,top+.012),.022,'wood_dark')
        for y,w,_ in stations[1:-1]:
            beam('inside_frame',(side*w*.91,y,.09),(side*w*.91,y,top),.013,'wood_light')
    for y,w,bottom in [stations[0],stations[-1]]:box('stem_or_transom',(0,y,(bottom+top)/2),(max(.04,w*2),.025,top-bottom),'hull_paint')
    def deck(a,c):
        # A full-width deck patch follows the adjacent hull stations, not a protruding box.
        rows=[p for p in stations if a<=p[0]<=c]
        def width(y):
            for (ya,wa,_),(yb,wb,_) in zip(stations,stations[1:]):
                if ya<=y<=yb:return wa+(wb-wa)*(y-ya)/(yb-ya)
            return stations[-1][1]
        rows=[(a,width(a),0)]+[p for p in rows if a<p[0]<c]+[(c,width(c),0)]
        vertices=[(x*w*.94,y,top-.013) for y,w,_ in rows for x in [-1,0,1]]
        attach(k.mesh('deck_planking',vertices,[(i*3+j,i*3+j+1,(i+1)*3+j+1,(i+1)*3+j) for i in range(len(rows)-1) for j in range(2)],'wood_light'))
        for x in [-.3,-.15,0,.15,.3]:
            for (y,w,_),(yy,ww,_) in zip(rows,rows[1:]):
                if abs(x)<min(w,ww)*.9:beam('deck_seam',(x,y,top-.009),(x,yy,top-.009),.0025,'wood_dark')
    if sailing:
        deck(-1.64,.18);deck(1.04,1.36)
        for side in [-1,1]:
            box('cockpit_bench',(side*.335,.60,.32),(.16,.84,.045),'wood_light')
            box('cockpit_coaming',(side*.25,.60,.38),(.025,.89,.09),'wood_dark')
        for i in range(5):box('cockpit_sole',((i-2)*.085,.60,.07),(.08,.80,.022),'wood')
        box('cabin',(0,-.39,.485),(.48,.65,.26),'cabin')
        box('cabin_roof',(0,-.39,.626),(.54,.71,.033),'hull_paint')
        for side in [-1,1]:
            for y in [-.58,-.25]:box('cabin_window',(side*.244,y,.52),(.008,.18,.095),'glass')
        box('companionway',(0,-.055,.47),(.22,.018,.20),'wood_dark')
        beam('mast',(0,-.30,.35),(0,-.30,2.87),.035,'wood_light')
        beam('forestay',(0,-1.57,.42),(0,-.30,2.83),.005,'rope')
        beam('backstay',(0,1.30,.40),(0,-.30,2.83),.005,'rope')
        for side in [-1,1]:beam('shroud',(side*.48,-.26,.39),(0,-.30,2.66),.005,'rope')
        boom=pivot('Boom',(0,-.30,1.00),vesselBoom=True)
        beam('boom',(0,-.30,1),(0,1.08,1),.023,'wood_light',boom)
        def sail(name,points,parent):
            node=pivot(name,(0,0,0),parent,vesselSail=True,sailCorners=[[x,z,-y] for x,y,z in points])
            a,c,d=[Vector(p) for p in points];v=[];lookup={}
            for i in range(13):
                for j in range(13-i):lookup[i,j]=len(v);v.append(tuple(a+(c-a)*(i/12)+(d-a)*(j/12)))
            f=[]
            for i in range(12):
                for j in range(12-i):
                    f.append((lookup[i,j],lookup[i+1,j],lookup[i,j+1]))
                    if i+j<11:f.append((lookup[i+1,j],lookup[i+1,j+1],lookup[i,j+1]))
            attach(k.mesh('woven_sail',v,f,'canvas'),node)
        sail('Mainsail',[(0,-.30,1.035),(0,-.30,2.79),(0,1.02,1.035)],boom)
        sail('Jib',[(0,-1.46,.49),(0,-.33,2.60),(0,-.40,.79)],root)
        keel=[(-.045,-.48,-.24),(.045,-.48,-.24),(-.03,-.22,-.69),(.03,-.22,-.69),(-.025,.35,-.61),(.025,.35,-.61),(-.045,.52,-.22),(.045,.52,-.22)]
        attach(k.mesh('ballasted_keel',keel,[(0,2,4,6),(1,7,5,3),(0,1,3,2),(2,3,5,4),(4,5,7,6),(6,7,1,0)],'hull_lower'))
        rudder=pivot('Rudder',(0,1.35,.02),vesselRudder=True)
        box('rudder_blade',(0,1.44,-.22),(.045,.24,.52),'wood_dark',rudder)
        beam('rudder_stock',(0,1.35,-.33),(0,1.35,.52),.022,'iron',rudder)
        beam('tiller',(0,1.35,.52),(0,.83,.55),.021,'wood_light',rudder)
    else:
        deck(-1.93,-1.06);deck(.76,1.69)
        box('hold_floor',(0,-.17,-.15),(1.10,1.70,.045),'wood_dark')
        for side in [-1,1]:
            box('hold_side',(side*.55,-.16,.14),(.035,1.80,.39),'hull_paint')
            box('side_walk',(side*.61,-.15,.315),(.10,1.86,.025),'wood_light')
            for y in [-1.42,-.40,.58,1.35]:
                beam('fender_lashing',(side*.61,y,.33),(side*.70,y,.05),.006,'rope')
                attach(k.ico('rope_fender',(side*.69,y,.06),(.064,.12,.095),'rope',2))
        for y in [-1.07,.77]:box('hold_end',(0,y,.14),(1.13,.035,.39),'hull_paint')
        box('wheelhouse_lower',(0,1.19,.52),(.78,.67,.37),'cabin')
        for side in [-1,1]:
            for y in [.85,1.53]:box('window_pillar',(side*.39,y,.87),(.04,.04,.34),'cabin')
            box('side_window',(side*.389,1.19,.86),(.008,.60,.28),'glass')
        for y in [.85,1.53]:
            box('window_sill',(0,y,.704),(.80,.05,.035),'wood_dark')
            for x in [-.13,.13]:box('window_mullion',(x,y,.87),(.025,.035,.34),'cabin')
            box('front_window',(0,y,.86),(.73,.008,.28),'glass')
        box('wheelhouse_roof',(0,1.19,1.065),(.91,.79,.05),'hull_paint')
        box('helm_console',(0,.96,.735),(.36,.13,.09),'wood_dark')
        beam('helm_shaft',(0,.96,.79),(0,1.10,.83),.012,'steel')
        helm=pivot('Helm',(0,1.10,.83),vesselHelm=True)
        for i in range(16):
            a=i*math.tau/16;c=(i+1)*math.tau/16
            beam('helm_rim',(.09*math.cos(a),1.10,.83+.09*math.sin(a)),(.09*math.cos(c),1.10,.83+.09*math.sin(c)),.009,'wood_dark',helm)
        for i in range(4):
            a=i*math.tau/4;beam('helm_spoke',(0,1.10,.83),(.09*math.cos(a),1.10,.83+.09*math.sin(a)),.006,'steel',helm)
        box('rear_door_panel',(0,1.532,.525),(.33,.012,.32),'wood_light')
        beam('door_handle',(.11,1.55,.60),(.11,1.55,.67),.009,'iron')
        beam('exhaust_stack',(.30,.89,1.08),(.30,.89,1.39),.035,'iron')
        box('exhaust_cap',(.30,.89,1.40),(.12,.11,.025),'iron')
        for i in range(6):
            x=-.26 if i%2==0 else .26;y=-.77+(i//2)*.57;p=(x,y,.13)
            cargo=pivot('Cargo',p,vesselCargo=i)
            box('cargo_crate',p,(.46,.49,.45),'wood_light',cargo)
            for z in [0,.27]:box('cargo_iron_band',(x,y,z),(.47,.50,.022),'iron',cargo)
            beam('crate_diagonal',(x-.19,y-.25,-.04),(x+.19,y-.25,.31),.012,'wood_dark',cargo)
        beam('propeller_shaft',(0,1.05,-.19),(0,1.79,-.19),.019,'steel')
        prop=pivot('Propeller',(0,1.72,-.19),vesselPropeller=True)
        beam('prop_hub',(0,1.68,-.19),(0,1.77,-.19),.041,'gold',prop)
        for j in range(3):
            a=j*math.tau/3;points=[]
            for radius,angle,y in [(.035,a-.12,1.70),(.14,a-.40,1.68),(.19,a+.12,1.75),(.16,a+.45,1.78),(.045,a+.32,1.75)]:points.append((math.sin(angle)*radius,y,-.19+math.cos(angle)*radius))
            attach(k.mesh('prop_blade',points,[(0,1,2),(0,2,3),(0,3,4)],'gold'),prop)
        rudder=pivot('Rudder',(0,1.92,-.12),vesselRudder=True)
        beam('upper_rudder_bracket',(0,1.65,.23),(0,1.92,.23),.022,'steel')
        beam('heel_support',(0,1.35,-.04),(0,1.35,-.42),.023,'steel')
        beam('rudder_heel',(0,1.35,-.42),(0,1.92,-.42),.023,'steel')
        box('rudder_blade',(0,1.98,-.18),(.028,.18,.32),'iron',rudder)
        beam('rudder_stock',(0,1.92,-.42),(0,1.92,.30),.017,'steel',rudder)
        beam('tiller_arm',(0,1.92,.27),(.18,1.92,.27),.014,'steel',rudder)
    for y,w in [(stations[1][0],stations[1][1]),(stations[-2][0],stations[-2][1])]:
        for side in [-1,1]:
            x=side*w*.77;beam('mooring_post',(x,y,top),(x,y,top+.10),.022,'iron')
            beam('cleat',(x-.06,y,top+.08),(x+.06,y,top+.08),.014,'iron')
            port=pivot('MooringPoint',(x,y,top+.10),mooringSide=side)
            port['normalGltf']=[side,0,0]
    root['animationBoundsMin']=[-.95,-.82,-2.16]
    root['animationBoundsMax']=[.95,3.05 if sailing else 1.58,2.15]
