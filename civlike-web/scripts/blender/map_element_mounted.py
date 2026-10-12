"""Mounted rider and a balanced two-wheel cart, reusing the articulated horse."""
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import map_element_fauna

KINDS=('rider','horse-cart')


def build(k,kind):
    b=k.bpy;cart=kind=='horse-cart'
    map_element_fauna.build(k,'horse')
    horse=next(o for o in b.context.scene.objects if o.get('faunaSpecies')=='horse')
    del horse['faunaSpecies'];horse['mountedHorse']=True
    body=next(o for o in horse.children if o.get('animalRole')=='body')
    head=next(o for o in horse.children if o.get('animalRole')=='head')
    root=k.pivot('MountedAssembly',(0,0,0),[]);root['mountKind']=kind;root['routeProfile']='road-145-v1'
    horse.parent=root
    horse_group=k.pivot('HorsePlacement',(0,-1.60 if cart else 0,0),[]);horse_group.parent=root;horse.parent=horse_group
    root['strideMeters']=.38/.62;root['cargoSlots']=4 if cart else 0
    for name,code in {'saddle':'73513D','pad':'628C9A','skin_human':'CC9D79','shirt':'568780' if cart else '667CA0','trousers':'596065','boot':'55483C','hair':'514437'}.items():
        mat=k.M['wood'].copy();mat.name='mounted_'+name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color=(*linear,1);mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*linear,1);k.M[name]=mat
    def attach(obj,parent=root):
        b.context.view_layer.update();world=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=world;return obj
    # Horse accessories are authored before moving their container, in the horse's local frame.
    horse_group.location.y=0
    def box(name,p,size,mat='wood',parent=root):return attach(k.box(name,p,size,mat,.007),parent)
    def beam(name,a,c,w=.015,mat='saddle',parent=root):return attach(k.beam(name,a,c,w,mat,8),parent)
    def ico(name,p,size,mat,parent=root):return attach(k.ico(name,p,size,mat,2),parent)
    def pivot(name,p,parent=root,**extras):
        obj=attach(k.pivot(name,p,[]),parent)
        for key,value in extras.items():obj[key]=value
        return obj
    def anchor(name,p,parent):return pivot('Anchor_'+name,p,parent,mountAnchor=name)
    def polyline(name,points,w,mat,parent):
        for a,c in zip(points,points[1:]):beam(name,a,c,w,mat,parent)
    def ring(name,center,rx,rz,mat,parent):
        points=[(center[0]+rx*math.sin(i*math.tau/20),center[1],center[2]+rz*math.cos(i*math.tau/20)) for i in range(21)]
        polyline(name,points,.012,mat,parent)
    # Bridle straps attach to the same head pivot as the mouth, never the scene root.
    for s in [-1,1]:
        polyline('cheek_strap',[(s*.145,-.94,1.98),(s*.18,-1.09,1.84),(s*.13,-1.34,1.63)],.014,'saddle',head)
        ring('bit_ring',(s*.16,-1.34,1.63),.032,.032,'iron',head)
        anchor('bit'+str(s),(s*.16,-1.34,1.63),head)
    beam('browband',(-.15,-1.035,1.98),(.15,-1.035,1.98),.018,'saddle',head)
    polyline('noseband',[(-.14,-1.26,1.64),(-.09,-1.31,1.72),(.09,-1.31,1.72),(.14,-1.26,1.64)],.016,'saddle',head)
    beam('bit_bar',(-.16,-1.34,1.63),(.16,-1.34,1.63),.008,'iron',head)
    # A conforming pad samples the actual horse torso instead of floating above a sphere.
    torso=next(o for o in body.children if o.type=='MESH')
    b.context.view_layer.update();graph=b.context.evaluated_depsgraph_get();surface=BVHTree.FromObject(torso,graph)
    inv=torso.matrix_world.inverted();vertices=[]
    for y in [-.36,-.18,0,.18,.36]:
        for x in [-.34,-.255,-.17,-.085,0,.085,.17,.255,.34]:
            origin=inv@Vector((x,y,3));direction=inv.to_3x3()@Vector((0,0,-1))
            hit=surface.ray_cast(origin,direction)[0]
            if hit is None:raise RuntimeError('Saddle pad missed torso')
            p=torso.matrix_world@hit;vertices.append((x,y,p.z+.016))
    pad=attach(k.mesh('fitted_saddle_pad',vertices,[(r*9+c,r*9+c+1,(r+1)*9+c+1,(r+1)*9+c) for r in range(4) for c in range(8)],'pad'),body)
    pad['saddleSurface']=True
    # Girth surrounds the belly and joins the saddle on each side.
    ring('girth',(0,.08,1.35),.391,.405,'saddle',body)
    for s in [-1,1]:
        box('girth_buckle',(s*.385,.08,1.47),(.022,.045,.07),'iron',body)
    if not cart:
        box('saddle_seat',(0,.015,1.754),(.34,.43,.045),'saddle',body)
        for y,z in [(-.235,1.79),(.26,1.80)]:beam('saddle_rise',(-.17,y,z),(.17,y,z),.035,'saddle',body)
        for s in [-1,1]:
            box('saddle_flap',(s*.31,.04,1.54),(.032,.38,.32),'saddle',body)
            beam('stirrup_leather',(s*.34,-.06,1.67),(s*.43,-.065,1.055),.014,'saddle',body)
            stirrup=pivot('Stirrup',(s*.43,-.065,.925),body,mountStirrup=s)
            polyline('stirrup_iron',[(s*.43,-.065,1.055),(s*.52,-.065,.925),(s*.34,-.065,.925),(s*.43,-.065,1.055)],.011,'iron',stirrup)
            box('stirrup_tread',(s*.43,-.065,.923),(.18,.07,.014),'iron',stirrup)
            anchor('stirrup'+str(s),(s*.43,-.080,.925),body)
        seat=(0,.015,1.835);person_parent=body
    else:
        # Breastcollar, harness saddle, breeching, shaft tugs and rein terrets.
        polyline('breast_collar',[(-.37,-.49,1.38),(-.28,-.70,1.27),(0,-.80,1.22),(.28,-.70,1.27),(.37,-.49,1.38)],.038,'saddle',body)
        polyline('breeching',[(-.38,.45,1.28),(-.29,.79,1.25),(0,.92,1.23),(.29,.79,1.25),(.38,.45,1.28)],.025,'saddle',body)
        for s in [-1,1]:
            polyline('harness_backstrap',[(s*.37,.45,1.28),(s*.28,.10,1.68),(s*.37,-.49,1.38)],.018,'saddle',body)
            ring('shaft_tug',(s*.50,-.12,1.10),.044,.065,'saddle',body)
            beam('tug_drop',(s*.34,-.12,1.64),(s*.50,-.12,1.10),.023,'saddle',body)
            ring('rein_terret',(s*.43,-.05,1.70),.036,.047,'iron',body)
            anchor('guide'+str(s),(s*.43,-.05,1.70),body)
            anchor('trace'+str(s),(s*.37,-.49,1.38),body)
    horse_group.location.y=-1.60 if cart else 0
    # Seated figures retain the worker palette and head scale but have genuine bent limbs.
    if cart:
        for s in [-1,1]:
            axle=pivot('CartWheel',(s*.59,1.02,.52),mountWheelRadius=.52)
            for name,radius,thickness,material in [('iron_tyre',.492,.028,'iron'),('wood_felloe',.46,.033,'wood_light')]:
                vertices=[]
                for i in range(24):
                    a=i*math.tau/24
                    for j in range(6):
                        c=j*math.tau/6;r=radius+thickness*math.cos(c)
                        vertices.append((s*.59+thickness*math.sin(c),1.02+math.sin(a)*r,.52+math.cos(a)*r))
                faces=[(i*6+j,i*6+(j+1)%6,((i+1)%24)*6+(j+1)%6,((i+1)%24)*6+j) for i in range(24) for j in range(6)]
                attach(k.mesh(name,vertices,faces,material),axle)
            beam('wheel_hub',(s*.51,1.02,.52),(s*.67,1.02,.52),.080,'wood_dark',axle)
            for i in range(14):
                a=i*math.tau/14;beam('wood_spoke',(s*.59,1.02,.52),(s*.59,1.02+math.sin(a)*.463,.52+math.cos(a)*.463),.022,'wood_light',axle)
            beam('long_shaft',(s*.50,1.22,.77),(s*.50,-2.16,1.16),.035,'wood')
            anchor('whipple'+str(s),(s*.46,-.04,.915),root)
            for j in range(3):box('spring_leaf',(s*.41,1.02,.66+j*.021),(.065,.60-j*.10,.018),'iron')
            for z in [1.04,1.18,1.32]:box('side_board',(s*.49,1.10,z),(.042,1.36,.12),'wood')
            for y in [.48,1.68]:box('side_post',(s*.50,y,1.13),(.062,.062,.48),'wood_dark')
        beam('cart_axle',(-.64,1.02,.52),(.64,1.02,.52),.05,'iron')
        for i in range(9):box('bed_plank',(0,.46+i*.15,.875),(.98,.142,.058),'wood_light')
        for z in [1.04,1.18,1.32]:box('tailboard',(0,1.78,z),(.98,.042,.12),'wood')
        beam('whippletree',(-.46,-.04,.915),(.46,-.04,.915),.03,'wood_dark')
        for x in [-.32,.32]:beam('seat_support',(x,.37,.91),(x,.29,1.09),.037,'wood_dark')
        box('drivers_bench',(0,.29,1.12),(.95,.34,.07),'wood_light')
        box('footboard',(0,-.08,.53),(.90,.32,.06),'wood_dark')
        for s in [-1,1]:beam('step_bracket',(s*.38,-.08,.51),(s*.38,.43,.86),.026,'iron')
        for i in range(4):
            x=(-.22 if i%2==0 else .22);y=.83+(i//2)*.55;pos=(x,y,1.11)
            cargo=pivot('Cargo',pos,mountCargo=i)
            box('wooden_crate',pos,(.38,.44,.40),'wood_light',cargo)
            for z in [.985,1.235]:box('crate_band',(x,y,z),(.39,.455,.024),'iron',cargo)
            beam('crate_slant',(x-.16,y-.23,.95),(x+.16,y-.23,1.27),.015,'wood_dark',cargo)
        seat=(0,.29,1.205);person_parent=root
    sx,sy,sz=seat
    person=pivot('SeatedPerson',seat,person_parent,seatedPerson=True)
    torso_node=pivot('SeatedTorso',seat,person,mountTorso=True)
    def pp(x,y,z):return (sx+x,sy+y,sz+z)
    rings=[(0,.18,.125),(.18,.165,.115),(.36,.19,.125),(.45,.235,.13),(.50,.13,.09)]
    v=[pp(math.sin(i*math.tau/12)*w,math.cos(i*math.tau/12)*d,z) for z,w,d in rings for i in range(12)]
    f=[tuple(reversed(range(12))),tuple(range(48,60))]+[(j*12+i,j*12+(i+1)%12,(j+1)*12+(i+1)%12,(j+1)*12+i) for j in range(4) for i in range(12)]
    attach(k.mesh('riding_tunic',v,f,'shirt'),torso_node)
    box('waist_belt',pp(0,0,.08),(.345,.247,.042),'saddle',torso_node)
    box('belt_buckle',pp(0,-.134,.08),(.06,.018,.04),'gold',torso_node)
    beam('neck',pp(0,0,.47),pp(0,0,.59),.06,'skin_human',torso_node)
    ico('head',pp(0,-.012,.705),(.128,.112,.169),'skin_human',torso_node)
    ico('hair',pp(0,.023,.80),(.132,.099,.083),'hair',torso_node)
    for s in [-1,1]:
        ico('ear',pp(s*.124,0,.70),(.024,.028,.04),'skin_human',torso_node)
        ico('eye',pp(s*.047,-.115,.735),(.009,.007,.009),'eye',torso_node)
    ico('nose',pp(0,-.127,.69),(.025,.035,.033),'skin_human',torso_node)
    beam('mouth',pp(-.025,-.111,.653),pp(.025,-.111,.653),.004,'hair',torso_node)
    ico('travel_cap',pp(0,.01,.853),(.146,.133,.072),'shirt',torso_node)
    box('cap_brim',pp(0,-.12,.833),(.23,.14,.012),'saddle',torso_node)
    for s in [-1,1]:
        hip=pp(s*.15,0,.015)
        knee=pp(s*(.43 if not cart else .16),-.23,-.36 if not cart else -.10)
        boot=pp(s*(.43 if not cart else .16),-.06 if not cart else -.37,-.845 if not cart else -.565)
        beam('thigh',hip,knee,.088,'trousers',person);ico('knee',knee,(.074,.08,.072),'trousers',person)
        beam('shin',knee,(boot[0],boot[1],boot[2]+.10),.06,'trousers',person)
        box('riding_boot',boot,(.15,.25,.12),'boot',person)
        box('boot_heel',(boot[0],boot[1]+.075,boot[2]-.07),(.14,.075,.035),'boot',person)
        anchor('boot'+str(s),(boot[0],boot[1]-.035,boot[2]-.065),person)
        shoulder=pp(s*.23,0,.43);elbow=pp(s*.30,-.14,.16);hand=pp(s*.15,-.43,.19)
        ico('sleeve',shoulder,(.085,.086,.088),'shirt',torso_node)
        beam('upper_arm',shoulder,elbow,.075,'shirt',torso_node)
        ico('elbow',elbow,(.054,.055,.055),'skin_human',torso_node)
        beam('forearm',elbow,hand,.049,'skin_human',torso_node)
        ico('gloved_hand',hand,(.046,.052,.041),'saddle',torso_node)
        anchor('hand'+str(s),hand,torso_node)
    anchor('seat',seat,person_parent);anchor('pelvis',seat,person)
    # Flexible tubes carry endpoint names; the web driver rebuilds their local vertices.
    def cable(a,c,sag,bulge,width=.009):
        node=pivot('FlexibleHarness',(0,0,0),mountCable=[a,c],cableSag=sag,cableBulge=bulge,cableRadius=width)
        anchors={o['mountAnchor']:o for o in b.context.scene.objects if o.get('mountAnchor')}
        b.context.view_layer.update();start=anchors[a].matrix_world.translation;end=anchors[c].matrix_world.translation
        vertices=[]
        for j in range(13):
            t=j/12;center=start.lerp(end,t)+Vector((bulge*math.sin(t*math.pi),0,-sag*math.sin(t*math.pi)))
            tangent=(end-start).normalized();across=tangent.cross(Vector((0,0,1))).normalized();normal=tangent.cross(across).normalized()
            for i in range(6):vertices.append(tuple(center+width*(across*math.cos(i*math.tau/6)+normal*math.sin(i*math.tau/6))))
        obj=k.mesh('rein' if a.startswith('bit') or a.startswith('guide') else 'trace',vertices,[(j*6+i,j*6+(i+1)%6,(j+1)*6+(i+1)%6,(j+1)*6+i) for j in range(12) for i in range(6)],'saddle')
        attach(obj,node)
    for s in [-1,1]:
        if cart:
            cable('bit'+str(s),'guide'+str(s),.03,s*.075)
            cable('guide'+str(s),'hand'+str(s),.07,s*.09)
            cable('trace'+str(s),'whipple'+str(s),.018,s*.09,.016)
        else:cable('bit'+str(s),'hand'+str(s),.025,s*.12)
