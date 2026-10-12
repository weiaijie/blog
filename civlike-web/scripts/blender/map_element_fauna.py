"""Articulated animal assets with species-specific proportions and maturity details."""
import math

from mathutils import Vector


def build(k, species):
    bird = species == 'chicken'
    dimensions = {
        'sheep': (.36, .61, .67, .32),
        'cow': (.46, .94, .99, .44),
        'horse': (.37, .93, 1.12, .40),
        'chicken': (.22, .30, .28, .25),
    }
    width, length, hip, depth = dimensions[species]
    colors = {
        'coat': 'DCD2B4' if species == 'sheep' else 'D5D4C8' if species == 'cow' else '906344' if species == 'horse' else 'D5A368',
        'coat_light': 'EEE3C4' if species == 'sheep' else 'EBE7D8' if species == 'cow' else 'AE7D53' if species == 'horse' else 'E9C899',
        'marking': '46443D' if species == 'cow' else '594737',
        'nose': 'AA7E70' if species == 'cow' else '67594B',
        'inner_ear': 'C3A08C', 'horn': 'C9B88E', 'comb': 'B04A40',
        'beak': 'C99845', 'mane': '493E34', 'fleece': 'E1D9BC',
    }
    for name, code in colors.items():
        mat = k.M['wool'].copy()
        mat.name = name
        rgb = [int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear = [c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear,1)
        k.M[name] = mat
    root = k.pivot('AnimalRoot',(0,0,0),[])
    root['faunaSpecies'] = species
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
        if name == 'anatomical_torso':
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
    torso = loft('anatomical_torso',[(y*length,body_center+z*depth,width*w,depth*h) for y,z,w,h in [
        (-1,.05,.24,.55),(-.76,.08,.86,.93),(-.35,0,1,1),(0,-.05,1.04,.98),(.49,.03,.97,.93),(.82,.08,.71,.73),(1,.04,.2,.35),
    ]],'coat',16)
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
    part('Body',(0,0,body_center),[torso],'body')

    if bird:
        part('Egg',(0,0,.085),[k.ico('eggshell',(0,0,.085),(.058,.063,.085),'wool_light',2)],'egg',(1,1,1))
        head_anchor = (0,-.23,.64)
        head_parts = [k.ico('head',(0,-.32,.76),(.15,.15,.16),'coat_light',2),
                      k.beam('neck',(0,-.17,.43),(0,-.28,.75),.10,'coat',8,.08)]
        beak = loft('pointed_beak',[(-.43,.75,.075,.043),(-.51,.735,.035,.024),(-.56,.723,.001,.002)],'beak',6)
        head_parts.append(beak)
    else:
        horse = species == 'horse'
        head_anchor = (0,-length*.68,hip+depth*.6)
        head_z = hip+(.67 if horse else .40 if species == 'cow' else .34)
        head_y = -length-(.06 if horse else .12)
        head_parts = [loft('neck',[(-length*.38,hip+.18,width*.71,.26),
                                   (-length*.71,head_z-.16,width*.48,.25),
                                   (head_y+.08,head_z,width*.38,.18)],'coat',12)]
        head_parts.append(loft('tapered_head',[(head_y+.10,head_z+.05,.16,.24),
                                              (head_y-.08,head_z,.17,.21),
                                              (head_y-.30,head_z-.15,.12,.12),
                                              (head_y-.40,head_z-.18,.09,.08)],'skin' if species=='sheep' else 'coat_light',12))
        if species == 'sheep':
            head_parts.append(k.ico('forehead_fleece',(0,head_y+.01,head_z+.22),(.175,.15,.09),'fleece',2))
        head_parts.append(k.ico('muzzle',(0,head_y-.34,head_z-.17),(.18 if species=='cow' else .145,.125,.105),'nose',2))
        for side in [-1,1]:
            head_parts.append(k.ico('nostril',(side*.085,head_y-.44,head_z-.13),(.025,.014,.018),'eye',2))
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
    part('Head',head_anchor,head_parts,'head',(.74,.73,.76) if not bird else (.65,.65,.72))

    def head_detail(name, objects, role='face', maturity=0):
        node = part(name,head_anchor,objects,role,(.74,.73,.76) if not bird else (.65,.65,.72),maturity)
        node['followHead'] = True
        return node

    if bird:
        for side in [-1,1]:
            head_detail('Eye',[k.ico('eye',(side*.119,-.389,.806),(.026,.025,.028),'eye',2),
                               k.ico('eye_glint',(side*.132,-.406,.816),(.009,.008,.008),'wool_light',1)])
        comb = [k.ico('comb_lobe',(0,-.32+i*.04,.91+math.sin(i*.8)*.025),(.025,.045,.065),'comb',2) for i in range(4)]
        comb.append(k.ico('wattle',(0,-.41,.659),(.032,.047,.064),'comb',2))
        head_detail('Comb',comb,'adult-detail',.42)
        for side in [-1,1]:
            feathers = []
            for i in range(8):
                feathers.append(feather((side*.205,-.075+i*.015,.59-i*.018),
                                         (side*(.235+i*.002),.21+i*.012,.48-i*.013),
                                         (0,0,1),(side,0,0),.06,'coat_light' if i%2 else 'coat'))
            wing = part('Wing',(side*.16,-.08,.53),feathers,'wing',(.48,.42,.5))
            wing['side'] = side
        tail = []
        for i in range(7):
            tail.append(feather((0,.19,.51),((i-3)*.055,.41,.83-abs(i-3)*.035),(1,0,0),(0,-.6,.8),.047,'marking' if i%2 else 'coat'))
        part('Tail',(0,.18,.51),tail,'tail',(.38,.35,.4),.22)
    else:
        for side in [-1,1]:
            eyes = [k.ico('eye_rim',(side*.146,head_y-.125,head_z+.07),(.043,.033,.041),'marking',2),
                    k.ico('eye',(side*.170,head_y-.136,head_z+.074),(.021,.024,.029),'eye',2),
                    k.ico('eye_glint',(side*.182,head_y-.144,head_z+.085),(.008,.009,.009),'wool_light',1)]
            head_detail('Eye',eyes)
            a = Vector((side*.13,head_y+.03,head_z+.17))
            b = a+Vector((side*(.08 if horse else .22),.04,.25 if horse else .045))
            ear = k.ico('ear',a.lerp(b,.55),(.057 if horse else .16,.051,.16 if horse else .066),'coat',2)
            inner = k.ico('inner_ear',a.lerp(b,.55)+Vector((0,-.032,0)),(.035 if horse else .11,.015,.113 if horse else .042),'inner_ear',2)
            ear_node = head_detail('Ear',[ear,inner],'ear')
            ear_node['side'] = side
            if species == 'cow':
                horn = [k.beam('horn_base',(side*.12,head_y+.06,head_z+.19),(side*.22,head_y+.11,head_z+.30),.055,'horn',7,.028),
                        k.beam('horn_tip',(side*.22,head_y+.11,head_z+.30),(side*.25,head_y+.10,head_z+.40),.028,'horn',7,.001)]
                head_detail('Horn',horn,'adult-detail',.36)
        tail_start = (0,length*.86,body_center+.06)
        if horse or species == 'cow':
            points = [Vector(tail_start),Vector((.025,length*1.04,body_center-.20)),Vector((.015,length*1.14,hip-.26))]
            tail = [k.beam('tail_segment',a,b,.030 if species=='cow' else .059,'coat' if species=='cow' else 'mane',6,.02) for a,b in zip(points,points[1:])]
            tail.append(k.ico('tail_tuft',points[-1],(.074,.078,.14),'mane',2))
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
            part('Fleece',(0,0,body_center),fleece,'adult-detail',(.55,.53,.60),.15)

    foot_height = .038 if bird else .065
    upper_len = (hip-foot_height)*.53
    lower_len = hip-foot_height-upper_len
    for index in range(2 if bird else 4):
        side = -1 if index%2==0 else 1
        x = side*width*(.54 if bird else .68)
        y = .01 if bird else (-length*.58 if index<2 else length*.63)
        knee = hip-upper_len
        young = (leg_factor,leg_factor,leg_factor)
        upper_parts = [k.beam('upper_leg',(x,y,hip),(x,y,knee),.019 if bird else .095,'beak' if bird else 'coat',9,.013 if bird else .055)]
        if not bird:
            upper_parts.append(k.ico('shoulder' if index<2 else 'haunch',(x,y,hip-.07),(.095 if index<2 else .14,.13,.21),'coat',2))
            upper_parts.append(k.ico('knee',(x,y,knee+.015),(.061,.071,.067),'coat_light',2))
        upper = part('UpperLeg',(x,y,hip),upper_parts,'upper-leg',young,index=index)
        lower_parts = [k.beam('lower_leg',(x,y,knee),(x,y,foot_height),.012 if bird else .053,'beak' if bird else 'coat_light',8,.009 if bird else .037)]
        if not bird:
            lower_parts.append(k.ico('fetlock',(x,y,foot_height+.026),(.055,.061,.075),'coat_light',2))
        lower = part('LowerLeg',(x,y,knee),lower_parts,'lower-leg',young,index=index)
        upper['segmentLength'] = upper_len
        lower['segmentLength'] = lower_len
        upper['footHeight'] = foot_height
        feet = []
        if bird:
            for toe in [-1,0,1]:
                feet.append(k.beam('toe',(x,y,.031),(x+toe*.045,y-.095,.015),.010,'beak',5,.005))
            feet.append(k.beam('back_toe',(x,y,.028),(x,y+.055,.016),.009,'beak',5,.004))
        else:
            split = species in ['cow','sheep']
            for s in [-1,1] if split else [0]:
                feet.append(k.box('cloven_hoof' if split else 'hoof',(x+s*.030,y-.017,.035),(.052 if split else .105,.14,.07),'hoof',.012))
        part('Foot',(x,y,foot_height),feet,'foot',young,index=index)
    return root
