"""Articulated animal assets with species-specific proportions and maturity details."""
import math

from mathutils import Vector


def build(k, species, refined=False):
    bird = species in ['chicken', 'duck']
    duck = species == 'duck'
    pig = species == 'pig'
    deer = species == 'deer'
    goat = species == 'goat'
    dimensions = {
        'sheep': (.36, .61, .67, .32),
        'cow': (.46, .94, .99, .44),
        'horse': (.37, .93, 1.12, .40),
        'chicken': (.22, .30, .28, .25),
        'goat': (.25, .56, .73, .27),
        'pig': (.38, .64, .40, .32),
        'duck': (.23, .39, .17, .22),
        'deer': (.28, .73, 1.04, .30),
    }
    width, length, hip, depth = dimensions[species]
    if refined:
        width, length, hip, depth = {
            'sheep': (.33, .62, .67, .27), 'cow': (.40, .95, .99, .34),
            'horse': (.32, .88, 1.12, .30), 'chicken': (.205, .29, .28, .235),
            'goat': (.235, .57, .73, .235), 'pig': (.37, .66, .40, .29),
            'duck': (.23, .40, .17, .19), 'deer': (.26, .74, 1.04, .25),
        }[species]
    colors = {
        'coat': 'DCD2B4' if species == 'sheep' else 'D5D4C8' if species == 'cow' else '906344' if species == 'horse' else 'D5A368',
        'coat_light': 'EEE3C4' if species == 'sheep' else 'EBE7D8' if species == 'cow' else 'AE7D53' if species == 'horse' else 'E9C899',
        'marking': '46443D' if species == 'cow' else '594737',
        'nose': 'AA7E70' if species == 'cow' else '67594B',
        'inner_ear': 'C3A08C', 'horn': 'C9B88E', 'comb': 'B04A40',
        'beak': 'C99845', 'mane': '493E34', 'fleece': 'E1D9BC',
    }
    colors.update({
        'goat': {'coat':'A39073', 'coat_light':'D4C7AC', 'nose':'574C40', 'mane':'74634B'},
        'pig': {'coat':'CD9990', 'coat_light':'E2B4A7', 'nose':'B47E78', 'inner_ear':'BC817B'},
        'duck': {'coat':'DDDACA', 'coat_light':'F2EBDA', 'marking':'B9B3A0', 'beak':'D69C47'},
        'deer': {'coat':'A57C50', 'coat_light':'CCAB78', 'nose':'594B3C', 'horn':'AA9370', 'inner_ear':'DDD0B0'},
    }.get(species, {}))
    for name, code in colors.items():
        mat = k.M['wool'].copy()
        mat.name = name
        rgb = [int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear = [c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear,1)
        k.M[name] = mat
    k.M['fawn_spots'] = k.M['wool_light'].copy()
    k.M['fawn_spots'].name = 'fawn_spots'
    root = k.pivot('AnimalRoot',(0,0,0),[])
    root['faunaSpecies'] = species
    root['faunaBird'] = bird
    if refined:root['anatomyVersion'] = 2
    leg_factor = .48 if bird else .68

    def part(name, anchor, objects, role, scale=(.57,.55,.62), maturity=0, index=-1):
        obj = k.pivot(name,anchor,objects)
        obj.parent = root
        obj['animalRole'] = role
        obj['youngScale'] = [scale[0],scale[2],scale[1]]
        obj['youngPosition'] = [anchor[0]*.60,anchor[2]*leg_factor,-anchor[1]*.57]
        obj['maturity'] = maturity
        obj['legIndex'] = index
        return obj

    def loft(name, rings, material, segments=12):
        if name == 'anatomical_torso' and not refined:
            rings = [tuple(a[i]+(b[i]-a[i])*t for i in range(4))
                     for a,b in zip(rings,rings[1:]) for t in [0,.33,.66]]+[rings[-1]]
        vertices = []
        for y,z,w,h in rings:
            for i in range(segments):
                a = i*math.tau/segments
                vertices.append((math.sin(a)*w,y,z+math.cos(a)*h))
        faces = []
        for j in range(len(rings)-1):
            for i in range(segments):
                a=j*segments+i; b=j*segments+(i+1)%segments
                faces.extend([(a,b,b+segments),(a,b+segments,a+segments)])
        faces.extend([tuple(reversed(range(segments))),tuple(range((len(rings)-1)*segments,len(rings)*segments))])
        return k.mesh(name,vertices,faces,material)

    def feather(a, b, across, normal, width, material):
        a,b,across,normal = Vector(a),Vector(b),Vector(across),Vector(normal)
        vertices = []
        for t in [0,.2,.5,.8,1]:
            center = a.lerp(b,t)+normal*math.sin(t*math.pi)*.025
            w = width*math.sin(t*math.pi)
            vertices.extend([tuple(center-across*w),tuple(center+normal*.012*math.sin(t*math.pi)),tuple(center+across*w)])
        faces = []
        for i in range(4):
            for j in range(2):
                a=i*3+j
                faces.extend([(a,a+3,a+4),(a,a+4,a+1)])
        return k.mesh('layered_feather',vertices,faces,material)

    body_center = hip+depth*.58
    profile = [
        (-1,.05,.24,.55),(-.76,.08,.86,.93),(-.35,0,1,1),(0,-.05,1.04,.98),(.49,.03,.97,.93),(.82,.08,.71,.73),(1,.04,.2,.35),
    ]
    if pig:
        profile = [(-1,0,.49,.66),(-.78,.03,.89,.97),(-.4,0,1,1),(0,0,1.08,1.02),(.48,.02,1,.95),(.83,.04,.78,.78),(1,.08,.28,.4)]
    elif duck:
        profile = [(-1,.04,.33,.5),(-.72,.09,.86,.91),(-.32,0,1,1),(0,-.03,1.05,.96),(.48,.04,.83,.73),(.85,.15,.49,.44),(1,.2,.14,.2)]
    elif deer or goat:
        profile = [(-1,.14,.05,.1),(-.72,.08,.88,1),(-.3,0,.99,.94),(0,.08,.84,.76),(.48,.08,.91,.83),(.8,.06,.64,.71),(1,.04,.15,.3)]
    if refined:
        profile = [(-1.08,.08,.015,.025),(-.83,.08,.66,.82),(-.58,.05,.98,1),(-.20,-.02,1,.95),
                   (.19,-.03,.89,.83),(.54,.03,.96,.94),(.82,.10,.66,.73),(1.05,.08,.015,.025)]
        if bird:
            profile = [(-1.08,.04,.015,.025),(-.75,.10,.66,.91),(-.30,.05,1,1),(.15,0,.95,.87),
                       (.58,.09,.73,.63),(.91,.17,.26,.23),(1.04,.20,.015,.02)]
        elif pig:
            profile = [(-1.08,.05,.015,.02),(-.83,.04,.74,.9),(-.42,0,1,1),(.1,.02,1.02,.96),
                       (.58,.04,.90,.93),(.85,.09,.61,.74),(1.05,.1,.015,.025)]
    torso = loft('anatomical_torso',[(y*length,body_center+z*depth,width*w,depth*h) for y,z,w,h in profile],'coat',16)
    torso.data.materials.append(k.M['coat_light'])
    torso.data.materials.append(k.M['marking'])
    for face in torso.data.polygons:
        center = face.center
        if species == 'cow':
            # Large coherent patches wrap the torso instead of random triangular speckles.
            center = sum((torso.data.vertices[i].co for i in face.vertices),Vector())/len(face.vertices)
            patch = math.sin(center.y*7+center.z*2)+.75*math.cos(center.x*9-center.y*3)
            face.material_index = 2 if patch>.52 else 0
        else:
            face.material_index = 1 if face.index%16 in [0,1,14,15] else 0
    body_node=part('Body',(0,0,body_center),[torso],'body')
    if deer:
        vertices, faces = [], []
        for face in torso.data.polygons:
            center = sum((torso.data.vertices[i].co for i in face.vertices),Vector())/len(face.vertices)
            if face.index%9==0 and abs(center.x)>.14 and abs(center.y)<length*.72 and center.z>body_center:
                start = len(vertices)
                vertices.extend([tuple(center+(torso.data.vertices[i].co-center)*.60+face.normal*.004) for i in face.vertices])
                faces.append(tuple(range(start,len(vertices))))
        part('FawnSpots',(0,0,body_center),[k.mesh('juvenile_spots',vertices,faces,'fawn_spots')],'juvenile-detail')

    if bird:
        part('Egg',(0,0,.085),[k.ico('eggshell',(0,0,.085),(.058,.063,.085),'wool_light',2)],'egg',(1,1,1))
        head_anchor = (0,-.25,.48) if duck else (0,-.23,.64)
        head_parts = [k.ico('head',(0,-.37,.61) if duck else (0,-.32,.76),(.14,.16,.15) if duck else (.15,.15,.16),'coat_light',2),
                      loft('curved_neck',[(-.20,.35,.10,.10),(-.27,.47,.085,.17),(-.32,.59,.10,.12)],'coat',10) if duck else
                      k.beam('neck',(0,-.17,.43),(0,-.28,.75),.10,'coat',8,.08)]
        beak = loft('flat_bill',[(-.47,.58,.090,.042),(-.58,.56,.092,.026),(-.68,.55,.067,.019),(-.70,.55,.036,.012)],'beak',10) if duck else loft('pointed_beak',[(-.43,.75,.075,.043),(-.51,.735,.035,.024),(-.56,.723,.001,.002)],'beak',6)
        head_parts.append(beak)
        if duck:
            for side in [-1,1]:
                head_parts.append(k.ico('bill_nostril',(side*.044,-.557,.586),(.012,.018,.006),'nose',1))
    else:
        horse = species == 'horse'
        head_anchor = (0,-length*(.43 if refined else .68),hip+depth*.6)
        head_z = hip+(.67 if horse or deer else .19 if pig else .40 if species == 'cow' else .34)
        head_y = -length-(.06 if horse else .12)
        head_parts = [loft('neck',[(-length*.38,hip+.18,width*.71,.26),
                                   (-length*.71,head_z-.16,width*.48,.25),
                                   (head_y+.08,head_z,width*.38,.18)],'coat',12)]
        if refined:
            for obj in head_parts:k.bpy.data.objects.remove(obj,do_unlink=True)
            head_parts = [loft('flowing_neck',[(-length*.23,body_center,width*.79,depth*.88),
                                               (-length*.48,head_z-.33,width*.67,depth*.90),
                                               (-length*.77,head_z-.15,width*.46,.23),
                                               (head_y+.08,head_z,width*.37,.17)],'coat',16)]
        head_rings = [(head_y+.10,head_z+.05,.16,.24),
                                              (head_y-.08,head_z,.17,.21),
                                              (head_y-.30,head_z-.15,.12,.12),
                                              (head_y-.40,head_z-.18,.09,.08)]
        if pig:
            head_rings = [(head_y+.14,head_z+.05,.24,.25),(head_y-.04,head_z,.22,.22),(head_y-.25,head_z-.045,.145,.13),(head_y-.35,head_z-.05,.115,.10)]
        elif goat or deer:
            head_rings = [(head_y+.10,head_z+.03,.13,.19),(head_y-.06,head_z,.14,.16),(head_y-.23,head_z-.12,.09,.095),(head_y-.30,head_z-.14,.07,.055)]
        head_parts.append(loft('tapered_head',head_rings,'skin' if species=='sheep' else 'coat_light',12))
        if species == 'sheep':
            head_parts.append(k.ico('forehead_fleece',(0,head_y+.01,head_z+.22),(.175,.15,.09),'fleece',2))
        muzzle_y = head_y-(.29 if goat or deer else .36 if pig else .34)
        muzzle_z = head_z-(.05 if pig else .14 if goat or deer else .17)
        head_parts.append(k.ico('snout_disc' if pig else 'muzzle',(0,muzzle_y,muzzle_z),(.145,.048,.102) if pig else (.085,.060,.065) if goat or deer else (.18 if species=='cow' else .145,.125,.105),'nose',2))
        for side in [-1,1]:
            head_parts.append(k.ico('nostril',(side*(.057 if pig else .043 if goat or deer else .085),muzzle_y-(.044 if pig else .052 if goat or deer else .10),muzzle_z+.023),(.022,.008,.026) if pig else (.016,.010,.012) if goat or deer else (.025,.014,.018),'eye',2))
        if goat:
            beard = [k.mesh('tapered_beard',[(-.065,head_y-.19,head_z-.16),(.065,head_y-.19,head_z-.16),(.045,head_y-.10,head_z-.15),(0,head_y-.14,head_z-.42)],[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],'mane')]
            node = part('Beard',head_anchor,beard,'adult-detail',(.5,.5,.5),.35)
            node['followHead'] = True
        if horse:
            mane = []
            for i in range(9):
                y = -length*.38-i*.081
                z = hip+.42+i*.045
                mane.append(k.mesh('mane_lock',[(0,y,z),(.045,y+.055,z+.04),(.052,y-.03,z+.16),(0,y-.085,z+.08)],[(0,1,2),(0,2,3)],'mane'))
            mane_node = part('Mane',head_anchor,mane,'adult-detail',(.5,.5,.5),.32)
            mane_node['followHead'] = True
        if species == 'cow':
            udder = [k.ico('udder',(0,length*.42,hip-depth*.13),(.17,.22,.16),'nose',2)]
            for x in [-.075,.075]:
                for y in [length*.32,length*.50]:
                    udder.append(k.beam('teat',(x,y,hip-.13),(x,y,hip-.23),.023,'nose',6,.016))
            udder_node = part('Udder',(0,length*.42,hip),udder,'adult-detail',(.5,.5,.5),.6)
            udder_node['sexTrait'] = 'female'
    if refined and not bird:
        # Weld the overlapping closed volumes; the viewer blends this surface between torso and head anchors.
        neck=head_parts.pop(0)
        k.bpy.context.view_layer.objects.active=torso
        modifier=torso.modifiers.new('ContinuousNeck','BOOLEAN')
        modifier.operation='UNION';modifier.solver='EXACT';modifier.object=neck
        k.bpy.ops.object.modifier_apply(modifier=modifier.name)
        k.bpy.data.objects.remove(neck,do_unlink=True)
        body_node['deformWithHead']=True
        root['neckBlendStart']=length*.25
        root['neckBlendEnd']=length*.77
        for face in torso.data.polygons:face.use_smooth=True
    part('Head',head_anchor,head_parts,'head',(.74,.73,.76) if not bird else (.65,.65,.72))

    def head_detail(name, objects, role='face', maturity=0):
        node = part(name,head_anchor,objects,role,(.74,.73,.76) if not bird else (.65,.65,.72),maturity)
        node['followHead'] = True
        return node

    if bird:
        for side in [-1,1]:
            head_detail('Eye',[k.ico('eye',(side*.111,-.429,.650) if duck else (side*.119,-.389,.806),(.023,.024,.025) if duck else (.026,.025,.028),'eye',2),
                               k.ico('eye_glint',(side*.123,-.442,.659) if duck else (side*.132,-.406,.816),(.008,.008,.008),'wool_light',1)])
        if not duck:
            comb = [k.ico('comb_lobe',(0,-.32+i*.04,.91+math.sin(i*.8)*.025),(.025,.045,.065),'comb',2) for i in range(4)]
            comb.append(k.ico('wattle',(0,-.41,.659),(.032,.047,.064),'comb',2))
            head_detail('Comb',comb,'adult-detail',.42)
        for side in [-1,1]:
            feathers = []
            for i in range(8):
                feathers.append(feather((side*.205,-.075+i*.015,(.43 if duck else .59)-i*.018),
                                         (side*(.235+i*.002),(.27 if duck else .21)+i*.012,(.36 if duck else .48)-i*.013),
                                         (0,0,1),(side,0,0),.06,'coat_light' if i%2 else 'coat'))
            wing = part('Wing',(side*.16,-.08,.39 if duck else .53),feathers,'wing',(.48,.42,.5))
            wing['side'] = side
        tail = []
        for i in range(7):
            tail.append(feather((0,.26,.34) if duck else (0,.19,.51),((i-3)*(.028 if duck else .055),.57 if duck else .41,(.44 if duck else .83)-abs(i-3)*.035),(1,0,0),(0,-.6,.8),.047,'marking' if i%2 else 'coat'))
        part('Tail',(0,.25,.34) if duck else (0,.18,.51),tail,'tail',(.38,.35,.4),.22)
    else:
        for side in [-1,1]:
            eye_x,eye_y = (.123,head_y-.055) if goat or deer else (.146,head_y-.125)
            eyes = [k.ico('eye_rim',(side*eye_x,eye_y,head_z+.055),(.028,.033,.033) if goat or deer else (.043,.033,.041),'marking',2),
                    k.ico('eye',(side*(eye_x+.018),eye_y-.008,head_z+.060),(.014,.022,.022) if goat or deer else (.021,.024,.029),'eye',2),
                    k.ico('eye_glint',(side*(eye_x+.027),eye_y-.016,head_z+.07),(.006,.007,.007),'wool_light',1)]
            head_detail('Eye',eyes)
            a = Vector((side*.13,head_y+.03,head_z+.17))
            b = a+Vector((side*(.08 if horse else .22),.04,.25 if horse else .12 if deer or goat else .045))
            ear = k.ico('ear',a.lerp(b,.55),(.057 if horse else .16,.051,.16 if horse else .09 if deer else .066),'coat',2)
            inner = k.ico('inner_ear',a.lerp(b,.55)+Vector((0,-.032,0)),(.035 if horse else .11,.015,.113 if horse else .06 if deer else .042),'inner_ear',2)
            if pig:
                # Folded triangular pinnae, not rounded ruminant ears.
                k.bpy.data.objects.remove(ear,do_unlink=True)
                k.bpy.data.objects.remove(inner,do_unlink=True)
                ear = k.mesh('folded_ear',[(side*.13,head_y+.02,head_z+.15),(side*.32,head_y+.05,head_z+.20),(side*.29,head_y-.17,head_z+.17),(side*.20,head_y-.035,head_z+.33)],[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],'coat')
                inner = k.mesh('inner_ear',[(side*.155,head_y-.004,head_z+.17),(side*.27,head_y-.145,head_z+.18),(side*.20,head_y-.05,head_z+.31)],[(0,1,2)],'inner_ear')
            ear_node = head_detail('Ear',[ear,inner],'ear')
            ear_node['side'] = side
            if species == 'cow':
                horn = [k.beam('horn_base',(side*.12,head_y+.06,head_z+.19),(side*.22,head_y+.11,head_z+.30),.055,'horn',7,.028),
                        k.beam('horn_tip',(side*.22,head_y+.11,head_z+.30),(side*.25,head_y+.10,head_z+.40),.028,'horn',7,.001)]
                head_detail('Horn',horn,'adult-detail',.36)
            if goat or deer:
                points = [Vector((side*.10,head_y+.05,head_z+.17)),Vector((side*.14,head_y+.08,head_z+.38)),Vector((side*.23,head_y+.22,head_z+.63)),Vector((side*.29,head_y+.37,head_z+.71))]
                horn = [k.beam('antler_beam' if deer else 'swept_horn',a,b,.043-i*.012,'horn',7,.001 if i==2 else .031-i*.012) for i,(a,b) in enumerate(zip(points,points[1:]))]
                if deer:
                    for start,end,radius in [(points[1],(side*.25,head_y-.10,head_z+.57),.025),(points[2],(side*.36,head_y+.17,head_z+.86),.023),(points[2].lerp(points[3],.65),(side*.43,head_y+.33,head_z+.90),.019)]:
                        horn.append(k.beam('antler_tine',start,end,radius,'horn',7,.001))
                node = head_detail('Antler' if deer else 'Horn',horn,'adult-detail',.44 if deer else .30)
                if deer:
                    node['sexTrait'] = 'male'
        tail_start = (0,length*.86,body_center+.06)
        if horse or species == 'cow':
            points = [Vector(tail_start),Vector((.025,length*1.04,body_center-.20)),Vector((.015,length*1.14,hip-.26))]
            tail = [k.beam('tail_segment',a,b,.030 if species=='cow' else .059,'coat' if species=='cow' else 'mane',6,.02) for a,b in zip(points,points[1:])]
            tail.append(k.ico('tail_tuft',points[-1],(.074,.078,.14),'mane',2))
        elif pig:
            points = [Vector((.075*math.sin(t),length*.96+t*.032,body_center+.06+.075*math.cos(t))) for t in [i*math.tau/16 for i in range(21)]]
            tail = [k.beam('curled_tail',a,b,.017,'coat_light',6,.014) for a,b in zip(points,points[1:])]
        elif goat or deer:
            tail = [k.ico('upright_tail',(0,length*.99,body_center+.10),(.07,.13,.12),'coat_light',2)]
        else:
            tail = [k.ico('short_tail',(0,length*.99,body_center),(.08,.16,.08),'fleece',2)]
        part('Tail',tail_start,tail,'tail')
        if species == 'sheep':
            vertices = []
            for v in torso.data.vertices:
                x,y,z = v.co
                ripple = .009*math.sin(y*39+x*22)*math.cos(z*31+y*12)
                vertices.append((x*1.045+math.copysign(abs(ripple),x),y*1.025,body_center+(z-body_center)*1.055+ripple))
            coat = k.mesh('continuous_fleece',vertices,[tuple(f.vertices) for f in torso.data.polygons],'fleece')
            coat.data.materials.append(k.M['coat_light'])
            for f in coat.data.polygons:
                f.material_index = int(k.RNG.random()<.15)
            fleece = [coat]
            wool_node=part('Fleece',(0,0,body_center),fleece,'adult-detail',(.55,.53,.60),.15)
            if refined:wool_node['deformWithHead']=True

    foot_height = .038 if bird else .065
    upper_len = (hip-foot_height)*.53
    lower_len = hip-foot_height-upper_len
    slim = .70 if deer else .77 if goat else 1
    def tapered_limb(name,x,y,top,bottom,profile,material):
        vertices=[]
        for t,w,d in profile:
            for i in range(12):
                a=i*math.tau/12
                vertices.append((x+w*math.sin(a),y+d*math.cos(a),top+(bottom-top)*t))
        faces=[tuple(reversed(range(12))),tuple(range((len(profile)-1)*12,len(profile)*12))]
        for j in range(len(profile)-1):
            for i in range(12):
                p=j*12+i;q=j*12+(i+1)%12;faces.append((p,q,q+12,p+12))
        return k.mesh(name,vertices,faces,material)
    for index in range(2 if bird else 4):
        side = -1 if index%2==0 else 1
        x = side*width*(.54 if bird else .68)
        y = .01 if bird else (-length*.58 if index<2 else length*.63)
        knee = hip-upper_len
        young = (leg_factor,leg_factor,leg_factor)
        upper_parts = [k.beam('upper_leg',(x,y,hip),(x,y,knee),.019 if bird else .095*slim,'beak' if bird else 'coat',9,.013 if bird else .055*slim)]
        if refined and not bird:
            for obj in upper_parts:k.bpy.data.objects.remove(obj,do_unlink=True)
            muscle=(.109 if index<2 else .145)*slim
            upper_parts=[tapered_limb('shaped_forelimb' if index<2 else 'shaped_hindlimb',x,y,hip+.075,knee-.025,
                          [(0,.075*slim,.09*slim),(.15,muscle,.115*slim),(.36,muscle*.83,.102*slim),
                           (.66,.069*slim,.077*slim),(1,.058*slim,.060*slim)],'coat')]
        elif not bird:
            upper_parts.append(k.ico('shoulder' if index<2 else 'haunch',(x,y,hip-.025 if deer or goat else hip-.07),((.095 if index<2 else .14)*slim,.13*slim,.21),'coat',2))
            upper_parts.append(k.ico('knee',(x,y,knee+.015),(.061*slim,.071*slim,.067),'coat_light',2))
        upper = part('UpperLeg',(x,y,hip),upper_parts,'upper-leg',young,index=index)
        lower_parts = [k.beam('lower_leg',(x,y,knee),(x,y,foot_height),.012 if bird else .053*slim,'beak' if bird else 'coat_light',8,.009 if bird else .037*slim)]
        if refined and not bird:
            for obj in lower_parts:k.bpy.data.objects.remove(obj,do_unlink=True)
            lower_parts=[tapered_limb('tapered_shank',x,y,knee+.025,foot_height-.014,
                           [(0,.059*slim,.059*slim),(.23,.060*slim,.066*slim),(.64,.037*slim,.043*slim),
                            (.86,.038*slim,.048*slim),(1,.048*slim,.055*slim)],'coat_light')]
        elif not bird:
            lower_parts.append(k.ico('fetlock',(x,y,foot_height+.026),(.055*slim,.061*slim,.075),'coat_light',2))
        lower = part('LowerLeg',(x,y,knee),lower_parts,'lower-leg',young,index=index)
        upper['segmentLength'] = upper_len
        lower['segmentLength'] = lower_len
        upper['footHeight'] = foot_height
        if refined and not bird:
            upper['restDrop'] = (upper_len+lower_len)*(.997 if index<2 else .98)
            upper['kneeBend'] = -1 if index<2 else 1
        feet = []
        if bird:
            for toe in [-1,0,1]:
                feet.append(k.beam('toe',(x,y,.031),(x+toe*.045,y-.095,.015),.010,'beak',5,.005))
            feet.append(k.beam('back_toe',(x,y,.028),(x,y+.055,.016),.009,'beak',5,.004))
            if duck:
                feet.append(k.mesh('webbed_foot',[(x,y,.028),(x-.060,y-.09,.016),(x,y-.115,.014),(x+.060,y-.09,.016),(x,y-.05,.023)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'beak'))
        else:
            split = species in ['cow','sheep','goat','pig','deer']
            for s in [-1,1] if split else [0]:
                feet.append(k.box('cloven_hoof' if split else 'hoof',(x+s*.030,y-.017,.035),(.052 if split else .105,.14,.07),'hoof',.012))
        part('Foot',(x,y,foot_height),feet,'foot',young,index=index)
    return root
