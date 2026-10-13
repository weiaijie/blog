"""C-style cottontail with folding hind limbs, ear hinges and separate muzzle motion."""
import math

from mathutils import Vector


def build(k):
    for name, code in {'coat': '9C8974', 'coat_back': '786F61', 'coat_light': 'B4A38B',
                       'rabbit_cream': 'E3DDC9', 'ear_skin': 'BC9489', 'nose': '786064'}.items():
        material = k.M['wool'].copy()
        material.name = name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear, 1)
        k.M[name] = material
    root = k.pivot('AnimalRoot', (0, 0, 0), [])
    root['faunaSpecies'] = 'rabbit'
    root['gaitFrequency'] = 1.35
    root['sniffAngle'] = .85
    root['juvenileCoat'] = '#777b78'
    root['animationBoundsMin'] = [-.20, 0, -.40]
    root['animationBoundsMax'] = [.20, .78, .42]

    def part(name, anchor, objects, role, young=(.57, .57, .60), index=-1):
        node = k.pivot(name, anchor, objects)
        node.parent = root
        node['animalRole'] = role
        node['youngScale'] = [young[0], young[2], young[1]]
        node['youngPosition'] = [anchor[0]*.57, anchor[2]*.60, -anchor[1]*.57]
        node['legIndex'] = index
        return node

    def loft(name, rings, material, segments=16):
        vertices, faces = [], []
        for y, z, width, height in rings:
            for i in range(segments):
                angle = i*math.tau/segments
                vertices.append((math.sin(angle)*width, y, z+math.cos(angle)*height))
        for j in range(len(rings)-1):
            for i in range(segments):
                a, b = j*segments+i, j*segments+(i+1) % segments
                faces.extend([(a, b, b+segments), (a, b+segments, a+segments)])
        faces.extend([tuple(reversed(range(segments))), tuple(range((len(rings)-1)*segments, len(rings)*segments))])
        return k.mesh(name, vertices, faces, material)

    torso = loft('rounded_rump_and_chest', [(-.235, .21, .012, .025), (-.215, .215, .045, .065),
                  (-.17, .215, .083, .10), (-.09, .218, .111, .127), (.02, .215, .125, .144),
                  (.12, .216, .137, .149), (.205, .203, .112, .119), (.25, .19, .065, .072),
                  (.273, .19, .008, .01)], 'coat', 20)
    torso.data.materials.append(k.M['coat_back'])
    torso.data.materials.append(k.M['rabbit_cream'])
    for polygon in torso.data.polygons:
        p = sum((torso.data.vertices[i].co for i in polygon.vertices), Vector())/len(polygon.vertices)
        polygon.material_index = 1 if p.z > .320 else 2 if p.z < .11 else 0
    part('Body', (0, .04, .24), [torso], 'body')

    anchor = (0, -.14, .245)
    young_head = (.78, .78, .78)
    head = [loft('neck_to_round_skull', [(-.115, .245, .050, .060), (-.17, .292, .072, .083),
                  (-.21, .322, .087, .093), (-.253, .320, .089, .090), (-.284, .305, .078, .070),
                  (-.310, .285, .058, .042), (-.333, .273, .030, .025),
                  (-.342, .273, .012, .012)], 'coat_light', 20)]
    part('Head', anchor, head, 'head', young_head)

    def face(name, objects):
        node = part(name, anchor, objects, 'face', young_head)
        node['followHead'] = True
        return node

    for side in [-1, 1]:
        face('Eye', [k.ico('eye_rim', (side*.077, -.252, .337), (.010, .024, .025), 'coat_back', 2),
                     k.ico('dark_eye', (side*.083, -.257, .339), (.007, .019, .020), 'eye', 2),
                     k.ico('eye_glint', (side*.089, -.264, .347), (.002, .004, .004), 'rabbit_cream', 1)])
    cheeks = []
    for side in [-1, 1]:
        cheeks.append(k.ico('muzzle_lobe', (side*.021, -.334, .267), (.026, .022, .018), 'rabbit_cream', 2))
        for i in range(3):
            cheeks.append(k.beam('whisker', (side*.040, -.348, .27+i*.002),
                                 (side*(.080+i*.012), -.355+i*.020, .262+i*.008), .0007, 'rabbit_cream', 4, .00025))
    face('Muzzle', cheeks)
    nose = k.pivot('NoseTwitch', (0, -.357, .281),
                   [k.ico('nose_pad', (0, -.357, .281), (.015, .007, .009), 'nose', 1)])
    nose['rabbitNose'] = True
    face('NoseCarrier', [nose])
    jaw = k.pivot('ChewingJaw', (0, -.286, .252),
                  [k.ico('lower_lip', (0, -.326, .249), (.033, .025, .012), 'rabbit_cream', 2)])
    jaw['rabbitJaw'] = True
    face('JawCarrier', [jaw])

    for side in [-1, 1]:
        base = Vector((side*.058, -.198, .382))
        vertices, faces = [], []
        widths = [.017, .027, .028, .023, .015, .002]
        for j, width in enumerate(widths):
            t = j/(len(widths)-1)
            center = base+Vector((side*.037*t, .047*t, .193*t))
            for i in range(10):
                a = i*math.tau/10
                vertices.append(tuple(center+Vector((math.cos(a)*width, math.sin(a)*.010*(1-.65*t), 0))))
        for j in range(len(widths)-1):
            for i in range(10):
                a, b = j*10+i, j*10+(i+1) % 10
                faces.append((a, b, b+10, a+10))
        faces.extend([tuple(reversed(range(10))), tuple(range(50, 60))])
        ear = k.mesh('long_pinna', vertices, faces, 'coat')
        inner_vertices = []
        for t, width in [(.12, .013), (.34, .019), (.58, .016), (.80, .009), (.94, .001)]:
            center = base+Vector((side*.037*t, .047*t-.010*(1-.65*t)-.001, .193*t))
            inner_vertices.extend([tuple(center+Vector((-width, 0, 0))), tuple(center+Vector((width, 0, 0)))])
        inset = k.mesh('inner_pinna', inner_vertices, [(j*2, j*2+1, j*2+3, j*2+2) for j in range(4)], 'ear_skin')
        hinge = k.pivot('EarHinge', base, [ear, inset])
        hinge['rabbitEarSide'] = side
        face('EarCarrier', [hinge])

    tail = k.ico('cottontail', (0, .286, .213), (.043, .048, .042), 'rabbit_cream', 2)
    part('Tail', (0, .253, .207), [tail], 'tail', (.50, .50, .54))

    for index in range(4):
        hind = index >= 2
        side = -1 if index % 2 == 0 else 1
        x, y = side*(.112 if hind else .068), .137 if hind else -.146
        a, b, height, drop = (.125, .125, .023, .180) if hind else (.073, .069, .018, .133)
        hip = drop+height
        upper = [k.beam('thigh' if hind else 'upper_foreleg', (x, y, hip), (x, y, hip-a),
                        .057 if hind else .025, 'coat', 12, .033 if hind else .020)]
        if hind:
            upper.append(k.ico('haunch', (x, y, hip-.028), (.064, .077, .080), 'coat', 2))
        upper_node = part('UpperLeg', (x, y, hip), upper, 'upper-leg', (.60, .60, .60), index)
        lower_node = part('LowerLeg', (x, y, hip-a),
                          [k.beam('hock' if hind else 'foreleg', (x, y, hip-a), (x, y, hip-a-b),
                                   .028 if hind else .020, 'coat_light', 10, .017 if hind else .014),
                           k.ico('knee_cover', (x, y, hip-a), (.034, .034, .034) if hind else (.023, .023, .023), 'coat_light', 2)],
                          'lower-leg', (.60, .60, .60), index)
        upper_node['segmentLength'], lower_node['segmentLength'] = a, b
        upper_node['footHeight'], upper_node['restDrop'] = height, drop
        upper_node['kneeBend'] = 1 if hind else -1
        angle = (1 if hind else -1)*math.acos((a*a+drop*drop-b*b)/(2*a*drop))
        knee_z, knee_forward = -a*math.cos(angle), a*math.sin(angle)
        upper_node.rotation_euler.x = -angle
        lower_node.location = (x, y-knee_forward, hip+knee_z)
        lower_node.rotation_euler.x = -math.atan2(-knee_forward, drop+knee_z)
        upper_node['restLegAngle'] = upper_node.rotation_euler.x
        lower_node['restLegAngle'] = lower_node.rotation_euler.x
        rear, front = (.049, .137) if hind else (.025, .052)
        paw = loft('long_hind_foot' if hind else 'fore_paw',
                   [(y+rear, height, .008, height*.45), (y+rear*.45, height, .025 if hind else .018, height),
                    (y-front*.60, height, .030 if hind else .021, height),
                    (y-front, height, .018 if hind else .014, height*.72),
                    (y-front-.006, height, .003, .004)], 'coat_light', 12)
        # The loft is centered on X; only translate vertices, leaving an identity object transform.
        for vertex in paw.data.vertices:
            vertex.co.x += x
        toes = [paw]
        for toe in [-1, 0, 1]:
            toes.append(k.beam('toe_seam', (x+toe*.012, y-front*.75, height*1.84),
                               (x+toe*.009, y-front, height*1.40), .001, 'coat_back', 4))
        part('Foot', (x, y, height), toes, 'foot', (.60, .60, .60), index)
    return root
