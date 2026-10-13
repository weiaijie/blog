"""Continuous character silhouettes, with blended skin weights at the joints."""
import math

from mathutils import Vector


def build(k, kind, rig, skin):
    def loft(name, rings, material, bone='Spine', segments=12):
        vertices = []
        for z, w, d, cy in rings:
            for i in range(segments):
                a = i*math.tau/segments
                vertices.append((w*math.sin(a), cy+d*math.cos(a), z))
        faces = [tuple(reversed(range(segments))), tuple(range((len(rings)-1)*segments, len(rings)*segments))]
        for j in range(len(rings)-1):
            for i in range(segments):
                a = j*segments+i
                c = j*segments+(i+1)%segments
                faces.append((a, c, c+segments, a+segments))
        return skin(k.mesh(name, vertices, faces, material), bone)

    def limb(name, anchors, profile, upper, lower, material, bare_from=None):
        a, b, c = [Vector(p) for p in anchors]
        split = (b-a).length/((b-a).length+(c-b).length)
        vertices, weights = [], []
        sides = 12
        for t, width, depth in profile:
            first = t <= split
            direction = (b-a if first else c-b).normalized()
            center = a.lerp(b, t/split) if first else b.lerp(c, (t-split)/(1-split))
            across = (Vector((1, 0, 0))-direction*direction.x).normalized()
            front = direction.cross(across).normalized()
            blend = max(0, min(1, (t-split+.12)/.24))
            blend = blend*blend*(3-2*blend)
            for i in range(sides):
                angle = i*math.tau/sides
                vertices.append(tuple(center+across*math.sin(angle)*width+front*math.cos(angle)*depth))
                weights.append(blend)
        faces = [tuple(reversed(range(sides))), tuple(range((len(profile)-1)*sides, len(profile)*sides))]
        for j in range(len(profile)-1):
            for i in range(sides):
                p = j*sides+i
                q = j*sides+(i+1)%sides
                faces.append((p, q, q+sides, p+sides))
        obj = k.mesh(name, vertices, faces, material)
        obj.parent = rig
        groups = [obj.vertex_groups.new(name=bone) for bone in [upper, lower]]
        for i, value in enumerate(weights):
            if value < 1: groups[0].add([i], 1-value, 'REPLACE')
            if value > 0: groups[1].add([i], value, 'REPLACE')
        modifier = obj.modifiers.new('JointSkin', 'ARMATURE')
        modifier.object = rig
        if bare_from is not None:
            obj.data.materials.append(k.M['human_skin'])
            for face in obj.data.polygons:
                if all(index//sides >= bare_from for index in face.vertices): face.material_index = 1
        obj['continuousLimb'] = True
        return obj

    farmer = kind == 'farmer'
    loft('shirt_and_waist', [(.86, .184, .116, 0), (1.00, .183, .115, 0), (1.16, .213, .139, -.005),
                           (1.32, .251, .142, 0), (1.385, .225, .119, 0), (1.425, .09, .072, 0)], 'human_shirt')
    loft('trouser_seat', [(.795, .175, .099, .008), (.86, .193, .122, .008), (.99, .178, .105, 0)], 'human_trousers')
    loft('leather_belt', [(1.0, .187, .119, 0), (1.04, .191, .121, 0)], 'human_leather')
    skin(k.box('belt_buckle', (0, -.126, 1.021), (.064, .02, .043), 'iron', .005), 'Spine')
    skin(k.beam('neck', (0, 0, 1.39), (0, 0, 1.515), .058, 'human_skin', 12), 'Head')
    loft('shaped_head', [(1.485, .058, .057, -.013), (1.525, .092, .078, -.013),
                        (1.575, .119, .101, -.006), (1.63, .134, .110, -.003),
                        (1.69, .130, .109, -.001), (1.752, .117, .099, .002), (1.798, .061, .053, .004)], 'human_skin', 'Head', 16)
    skin(k.ico('hair_crown', (0, .02, 1.75), (.128, .102, .072), 'human_hair', 2), 'Head')
    for side in [-1, 1]:
        skin(k.ico('ear', (side*.13, .005, 1.625), (.020, .024, .035), 'human_skin', 2), 'Head')
        skin(k.ico('eye', (side*.047, -.111, 1.654), (.010, .007, .009), 'eye', 2), 'Head')
        skin(k.beam('eyebrow', (side*.026, -.11, 1.677), (side*.073, -.10, 1.678), .005, 'human_hair', 5), 'Head')
        skin(k.box('sideburn', (side*.115, .002, 1.69), (.014, .078, .10), 'human_hair', .004), 'Head')
    skin(k.mesh('short_nose', [(-.018, -.108, 1.658), (.018, -.108, 1.658), (0, -.138, 1.61),
                             (-.023, -.118, 1.598), (.023, -.118, 1.598)],
                [(0, 1, 2), (0, 2, 3), (1, 4, 2), (2, 4, 3), (0, 3, 4, 1)], 'human_skin_light'), 'Head')
    skin(k.beam('mouth', (-.023, -.107, 1.574), (.023, -.107, 1.574), .0035, 'human_hair', 5), 'Head')
    for side in [-1, 1]:
        # The pale collar and shirt inset follow the chest surface.
        points = [(side*.038, -.075, 1.426), (side*.106, -.082, 1.415), (side*.115, -.128, 1.337), (side*.024, -.142, 1.368)]
        skin(k.mesh('folded_collar', points, [(0, 1, 2, 3)], 'human_linen'), 'Spine')
    if farmer:
        skin(k.mesh('shirt_front', [(-.092, -.139, 1.368), (.092, -.139, 1.368), (0, -.147, 1.19)], [(0, 1, 2)], 'human_linen'), 'Spine')
        for side in [-1, 1]:
            skin(k.box('vest_pocket', (side*.127, -.12, 1.085), (.107, .016, .08), 'human_shirt', .009), 'Spine')
        for z in [1.08, 1.15, 1.22]: skin(k.ico('vest_button', (0, -.151, z), (.009, .006, .009), 'human_leather', 1), 'Spine')
        beard = loft('short_farm_beard', [(1.496, .060, .042, -.048), (1.535, .093, .05, -.055),
                                         (1.563, .081, .053, -.061)], 'human_hair', 'Head', 12)
        beard['characterDetail'] = 'beard'

    for side, suffix in [(1, 'R'), (-1, 'L')]:
        hip, knee, ankle = (side*.13, 0, .90), (side*.13, -.045, .53), (side*.13, 0, .16)
        limb('continuous_trouser_'+suffix, [hip, knee, ankle],
             [(0, .101, .105), (.16, .101, .100), (.35, .088, .084), (.48, .074, .073),
              (.56, .070, .072), (.69, .077, .074), (.84, .058, .061), (1, .048, .049)],
             'Thigh'+suffix, 'Shin'+suffix, 'human_trousers')
        boot = []
        for y, z, w, h in [(-.171, .058, .046, .034), (-.14, .067, .072, .047),
                           (-.055, .086, .073, .067), (.018, .092, .061, .081), (.059, .079, .05, .063)]:
            for i in range(10):
                a = i*math.tau/10
                boot.append((side*.13+w*math.sin(a), y, z+h*math.cos(a)))
        faces = [tuple(reversed(range(10))), tuple(range(40, 50))]
        for j in range(4):
            for i in range(10):
                p = j*10+i
                q = j*10+(i+1)%10
                faces.append((p, q, q+10, p+10))
        skin(k.mesh('shaped_boot', boot, faces, 'human_boot'), 'Foot'+suffix)
        skin(k.box('boot_sole', (side*.13, -.055, .013), (.151, .239, .026), 'wood_dark', .008), 'Foot'+suffix)
        skin(k.beam('boot_cuff', (side*.13, 0, .12), (side*.13, 0, .185), .060, 'human_boot', 10, .063), 'Foot'+suffix)
        shoulder, elbow, wrist = (side*.23, 0, 1.36), (side*.34, -.03, 1.10), (side*.40, -.10, .89)
        limb('continuous_arm_'+suffix, [shoulder, elbow, wrist],
             [(0, .095, .083), (.16, .088, .077), (.35, .074, .064), (.48, .065, .055),
              (.56, .060, .052), (.68, .059, .046), (.84, .047, .037), (1, .038, .032)],
             'Arm'+suffix, 'Forearm'+suffix, 'human_linen' if farmer else 'human_shirt', 4)
        open_hand = kind == 'town-resident' and suffix == 'R'
        skin(k.ico('open_palm' if open_hand else 'grasping_palm', (side*.40, -.108, .845),
                   (.038, .021, .041) if open_hand else (.042, .030, .051), 'human_skin_light', 2), 'Hand'+suffix)
        if open_hand:
            for j in range(4):
                x, length = .374+j*.017, .038+(.008 if j in [1, 2] else 0)
                skin(k.beam('greeting_finger', (x, -.108, .819), (x+(j-1.5)*.004, -.108, .819-length), .008, 'human_skin_light', 7), 'HandR')
        skin(k.ico('thumb', (side*.370, -.13, .858), (.020, .021, .031), 'human_skin', 2), 'Hand'+suffix)
