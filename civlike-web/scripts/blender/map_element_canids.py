"""Stylized fox and wolf: continuous anatomy with grounded articulated paws."""
import math

from mathutils import Vector


def build(k, species):
    fox = species == 'fox'
    width, length, hip, depth = (.145, .40, .39, .16) if fox else (.225, .61, .64, .235)
    colors = {
        'coat': 'C67738' if fox else '8D918A',
        'coat_back': 'AA582B' if fox else '616962',
        'coat_light': 'D4934F' if fox else 'B7B8A6',
        'fur_cream': 'E8DFC2', 'fur_dark': '413F39',
        'inner_ear': 'B79578', 'iris': 'BD9B48', 'claw': '6B6150',
    }
    for name, code in colors.items():
        material = k.M['wool'].copy()
        material.name = name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear, 1)
        k.M[name] = material
    root = k.pivot('AnimalRoot', (0, 0, 0), [])
    root['faunaSpecies'] = species
    root['gaitStride'] = .105 if fox else .17
    root['gaitFrequency'] = 1.60 if fox else 1.10
    root['gaitLift'] = .045 if fox else .065
    root['sniffAngle'] = .86 if fox else .80
    root['juvenileCoat'] = '#777065' if fox else '#77786d'
    leg_factor = .60 if fox else .63

    def part(name, anchor, objects, role, young=(.55, .56, .60), index=-1):
        node = k.pivot(name, anchor, objects)
        node.parent = root
        node['animalRole'] = role
        node['youngScale'] = [young[0], young[2], young[1]]
        node['youngPosition'] = [anchor[0]*.57, anchor[2]*leg_factor, -anchor[1]*.56]
        node['legIndex'] = index
        return node

    def loft(name, rings, material, segments=16):
        vertices, faces = [], []
        for y, z, w, h in rings:
            for i in range(segments):
                angle = i*math.tau/segments
                vertices.append((math.sin(angle)*w, y, z+math.cos(angle)*h))
        for j in range(len(rings)-1):
            for i in range(segments):
                a = j*segments+i
                b = j*segments+(i+1) % segments
                faces.extend([(a, b, b+segments), (a, b+segments, a+segments)])
        faces.extend([tuple(reversed(range(segments))), tuple(range((len(rings)-1)*segments, len(rings)*segments))])
        return k.mesh(name, vertices, faces, material)

    center = hip+depth*.52
    profile = [(-1, .04, .40, .62), (-.80, .03, .84, .98), (-.50, 0, 1, 1),
               (-.20, .03, .94, .82), (.13, .12, .80, .65), (.45, .06, .91, .84),
               (.72, 0, .94, .88), (.92, -.04, .58, .68), (1, -.04, .18, .30)]
    torso = loft('lean_torso' if fox else 'deep_chest_torso',
                 [(y*length, center+z*depth, w*width, h*depth) for y, z, w, h in profile], 'coat')
    torso.data.materials.append(k.M['coat_back'])
    torso.data.materials.append(k.M['fur_cream'])
    for face in torso.data.polygons:
        p = sum((torso.data.vertices[i].co for i in face.vertices), Vector())/len(face.vertices)
        face.material_index = 1 if p.z > center+depth*.54 else 2 if p.z < center-depth*.50 else 0
    part('Body', (0, 0, center), [torso], 'body')

    head_anchor = (0, -length*.36, center)
    hz, hy = hip+depth*1.20, -length*1.13
    hw = .099 if fox else .15
    muzzle = .21 if fox else .25
    head = [loft('rising_neck', [(-length*.36, center, width*.88, depth*.91),
                               (-length*.70, hz-.03, width*.75, depth*.95),
                               (hy+.04, hz+.04, hw*.85, hw*.98)], 'coat')]
    skull = loft('tapered_skull', [(hy+.09, hz+.03, hw*.68, hw*.80),
                                 (hy+.025, hz+.05, hw, hw*1.15),
                                 (hy-.08, hz+.035, hw*.96, hw*.88),
                                 (hy-.15, hz, hw*.63, hw*.53)], 'coat_light')
    head.append(skull)
    head.append(loft('pointed_muzzle' if fox else 'broad_muzzle',
                     [(hy-.075, hz-.016, hw*.74, hw*.60),
                      (hy-muzzle*.82, hz-.047, hw*(.38 if fox else .57), hw*.34),
                      (hy-muzzle-.045, hz-.052, hw*(.22 if fox else .42), hw*.22)], 'fur_cream', 12))
    nose_y = hy-muzzle-.051
    head.append(k.ico('nose', (0, nose_y, hz-.037), (hw*(.29 if fox else .44), .023, .020 if fox else .030), 'fur_dark', 2))
    for side in [-1, 1]:
        head.append(k.beam('mouth_corner', (side*hw*.42, hy-.14, hz-.079),
                           (side*hw*.24, nose_y+.035, hz-.078), .0035 if fox else .005, 'fur_dark', 5))
        head.append(k.mesh('cheek_fur', [(side*hw*.80, hy-.09, hz),
                                        (side*hw*1.32, hy+.055, hz-.035),
                                        (side*hw*.91, hy+.015, hz-.092),
                                        (side*hw*.50, hy-.145, hz-.07)], [(0, 1, 2), (0, 2, 3)], 'fur_cream'))
    # A continuous bib follows the neck, rather than separate floating chest balls.
    head.append(loft('throat_bib', [(-length*.82, hz-.10, width*.58, depth*.48),
                                  (hy+.015, hz-.066, hw*.73, hw*.55),
                                  (hy-.10, hz-.064, hw*.50, hw*.32)], 'fur_cream', 12))
    young_head = (.76, .74, .79)
    part('Head', head_anchor, head, 'head', young_head)

    def face_part(name, objects):
        node = part(name, head_anchor, objects, 'face', young_head)
        node['followHead'] = True
        return node

    for side in [-1, 1]:
        ex, ey, ez = side*hw*.87, hy-.07, hz+.075
        face_part('Eye', [k.ico('eye_socket', (ex, ey, ez), (.013, .031, .023), 'fur_dark', 2),
                          k.ico('iris', (ex+side*.005, ey-.007, ez), (.011, .019, .016), 'iris', 2),
                          k.ico('pupil', (ex+side*.011, ey-.009, ez), (.006, .010, .012), 'eye', 2),
                          k.ico('eye_glint', (ex+side*.014, ey-.016, ez+.006), (.0035, .004, .004), 'fur_cream', 1)])
        base = Vector((side*hw*.72, hy+.025, hz+hw*.85))
        height = .155 if fox else .17
        ear_width = .052 if fox else .07
        points = [base+Vector((-ear_width, -.006, 0)), base+Vector((ear_width, -.006, 0)),
                  base+Vector((side*.022, .017, height)), base+Vector((0, .048, height*.32))]
        ear = k.mesh('pointed_pinna', [tuple(p) for p in points], [(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)], 'fur_dark' if fox else 'coat_back')
        inner = k.mesh('ear_inset', [tuple(base+Vector((-ear_width*.66, -.007, .022))),
                                   tuple(base+Vector((ear_width*.66, -.007, .022))),
                                   tuple(base+Vector((side*.018, .011, height*.81)))], [(0, 1, 2)], 'inner_ear')
        hinge = k.pivot('EarHinge', base, [ear, inner])
        hinge['canidEarSide'] = side
        # Head growth affects the carrier; flicks pivot at the actual ear base.
        face_part('EarCarrier', [hinge])

    start = (0, length*.88, center+.025)
    tail_length = .68 if fox else .74
    tail = loft('bushy_tail' if fox else 'downheld_tail',
                [(start[1]+tail_length*t, start[2]-tail_length*(.28*t if fox else .78*t),
                  w*width*(1 if fox else .72), h*depth*(1 if fox else .68)) for t, w, h in [(0, .30, .28), (.18, .55, .54), (.42, .85, .83),
                                                  (.64, .91, .83), (.80, .67, .62), (.94, .29, .30), (1, .015, .02)]], 'coat')
    tail.data.materials.append(k.M['fur_cream' if fox else 'coat_back'])
    for polygon in tail.data.polygons:
        p = sum((tail.data.vertices[i].co for i in polygon.vertices), Vector())/len(polygon.vertices)
        if (p.y-start[1])/tail_length > (.76 if fox else .58):
            polygon.material_index = 1
    part('Tail', start, [tail], 'tail', (.53, .45, .55))

    foot_height = .030 if fox else .045
    upper_len = (hip-foot_height)*.54
    lower_len = hip-foot_height-upper_len
    radius = .033 if fox else .052
    for index in range(4):
        side = -1 if index % 2 == 0 else 1
        x = side*width*.73
        y = -length*.62 if index < 2 else length*.66
        knee = hip-upper_len
        young = (leg_factor, leg_factor, leg_factor)
        upper_meshes = [k.beam('upper_leg', (x, y, hip), (x, y, knee), radius*1.28, 'coat', 10, radius*.76),
                        k.ico('shoulder' if index < 2 else 'haunch', (x, y+.015, hip+.015),
                              (radius*1.60, radius*2.4, depth*.83), 'coat', 2)]
        upper = part('UpperLeg', (x, y, hip), upper_meshes, 'upper-leg', young, index)
        material = 'fur_dark' if fox else 'coat_light'
        lower_meshes = [k.beam('pastern', (x, y, knee), (x, y, foot_height), radius*.77, material, 10, radius*.56),
                        k.ico('hock', (x, y+.01, knee), (radius*.86, radius, radius*.88), material, 2)]
        lower = part('LowerLeg', (x, y, knee), lower_meshes, 'lower-leg', young, index)
        upper['segmentLength'], lower['segmentLength'] = upper_len, lower_len
        upper['footHeight'] = foot_height
        paw = [k.ico('paw_pad', (x, y-.009, foot_height), (radius*1.11, radius*1.33, foot_height), material, 2)]
        for toe in range(4):
            tx = x+(toe-1.5)*radius*.52
            ty = y-radius*(1.05 if toe in [0, 3] else 1.30)
            paw.append(k.ico('paw_toe', (tx, ty, foot_height*.70), (radius*.38, radius*.65, foot_height*.70), material, 2))
            paw.append(k.beam('claw', (tx, ty-radius*.46, foot_height*.52),
                              (tx, ty-radius*.85, foot_height*.33), radius*.095, 'claw', 5, .001))
        node = part('Foot', (x, y, foot_height), paw, 'foot', young, index)
        node['pawDigits'] = 4
    return root
