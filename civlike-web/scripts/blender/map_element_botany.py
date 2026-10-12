"""Separate botanical organs preserve stage changes in the exported GLB hierarchy."""
import math

from mathutils import Vector


def build(k, kind):
    rng = k.RNG
    fruit_colors = ('D77B29','ECA24B') if kind == 'pumpkin-patch' else ('8F3551','B54B68') if kind == 'berry-shrub' else ('BE4E3F','D9684C')
    for name, code in [('petal', 'F8DED2'), ('pollen', 'E5B440'),
                       ('fruit_skin', fruit_colors[0]), ('fruit_light', fruit_colors[1]),
                       ('seed_disk', '655039')]:
        rgb = [int(code[i:i+2],16)/255 for i in (0,2,4)]
        color = [c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        mat = k.M['leaf'].copy()
        mat.name = name
        mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (*color, 1)
        k.M[name] = mat
    for mat in k.M.values():
        mat.use_backface_culling = False
    arboreal = kind in ['apple-tree', 'berry-shrub']
    def ground_height(x, y):
        edge = max(0, min(1, (1.75-max(abs(x),abs(y)))/.2))
        return .055+edge*.014*math.sin(x*4+y*2)*math.cos(y*5)
    def ground_weight(x, y):
        r = math.hypot(x,y)+.055*math.sin(x*9+y*7)
        t = max(0,min(1,(1.2-r)/.7))
        return t*t*(3-2*t)*.92
    if arboreal:
        k.living_soil(ground_height, ground_weight)
    else:
        k.living_soil()

    def attach(obj, parent):
        k.bpy.context.view_layer.update()
        world = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = world

    def organ(name, anchor, objects, role, start, full, end=1.2, gone=1.3, bend=0):
        obj = k.pivot(name, anchor, objects)
        obj['lifeRole'] = role
        obj['lifeStart'] = start
        obj['lifeFull'] = full
        obj['lifeEnd'] = end
        obj['lifeGone'] = gone
        obj['lifeBend'] = bend
        obj['lifePhase'] = rng.random() * math.tau
        return obj

    def leaf(p, angle, length, width, material='leaf', lobed=False):
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        across = Vector((-direction.y, direction.x, 0))
        vertices = []
        for i in range(7):
            t = i / 6
            w = math.sin(math.pi * t) * width
            if lobed:
                w *= 1 + .24 * math.cos(t * math.pi * 6)
            center = Vector(p) + direction * length * t + Vector((0, 0, length * (.3*t-.38*t*t)))
            vertices.extend([tuple(center-across*w), tuple(center+Vector((0, 0, w*.32))), tuple(center+across*w)])
        faces = []
        for i in range(6):
            for j in range(2):
                a = i*3+j
                faces.extend([(a, a+3, a+4), (a, a+4, a+1)])
        return k.mesh('veined_leaf', vertices, faces, material)

    def flower(p, radius, petals=5, material='petal'):
        parts = []
        for i in range(petals):
            a = i*math.tau/petals
            d = Vector((math.cos(a), math.sin(a), 0))
            n = Vector((-d.y, d.x, 0))
            c = Vector(p)
            vertices = [c, c+d*radius*.58-n*radius*.26+Vector((0,0,.012)),
                        c+d*radius, c+d*radius*.58+n*radius*.26+Vector((0,0,.012)),
                        c+d*radius*.53+Vector((0,0,.028))]
            parts.append(k.mesh('flower_petal', [tuple(v) for v in vertices],
                                [(0,1,4),(1,2,4),(2,3,4),(3,0,4)], material))
        parts.append(k.ico('pollen_center', p, (radius*.22, radius*.22, radius*.12), 'pollen', 1))
        return parts

    def fruit(p, radius, pumpkin=False):
        vertices = []
        segments, rings = (30, 14) if pumpkin else (16, 10)
        for j in range(rings+1):
            t = math.pi*j/rings
            for i in range(segments):
                a = math.tau*i/segments
                r = radius*math.sin(t)*(1+.10*math.cos(a*(10 if pumpkin else 5)))
                z = radius*math.cos(t)*(.72 if pumpkin else .91)
                if not pumpkin:
                    z -= radius*.14*math.exp(-(t/.3)**2)
                vertices.append((p[0]+r*math.cos(a),p[1]+r*math.sin(a),p[2]+z))
        faces = []
        for j in range(rings):
            for i in range(segments):
                a = j*segments+i; b = j*segments+(i+1)%segments
                faces.append((a,b,b+segments,a+segments))
        obj = k.mesh('ribbed_pumpkin' if pumpkin else 'apple_skin',vertices,faces,'fruit_skin')
        obj.data.materials.append(k.M['fruit_light'])
        for f in obj.data.polygons:
            f.material_index = int(f.index % segments < segments//4)
        stem = k.beam('fruit_stem', (p[0],p[1],p[2]+radius*.65),
                      (p[0]+radius*.14,p[1],p[2]+radius*1.16), radius*.075, 'bark', 5)
        return [obj, stem]

    def sapling(x, y, z, size=.25):
        parts = [k.beam('seedling_stem',(x,y,z),(x,y,z+size),.012,'leaf',5)]
        for a in [0, math.pi]:
            parts.append(leaf((x,y,z+size*.65), a, size*.8, size*.24, 'leaf_light'))
        organ('Cotyledons',(x,y,z),parts,'shoot',0,.09,.18,.33,.04)

    if kind in ['apple-tree', 'berry-shrub']:
        apple = kind == 'apple-tree'
        h = 2.65 if apple else 1.05
        base = ground_height(0,0)
        sapling(0,0,base,.37 if apple else .23)
        trunk = [k.beam('tapered_trunk',(0,0,base),(.08,.04,h*.77),.13 if apple else .036,'bark',7,.032 if apple else .014)]
        for a in [0,2.2,4.5]:
            trunk.append(k.beam('root_flare',(.24*math.cos(a),.24*math.sin(a),base),
                                (0,0,base+.34),.055 if apple else .018,'bark',5,.016))
        trunk_node = organ('Trunk',(0,0,base),trunk,'structure',.08,.38)
        for j in range(8):
            angle = j*2.399
            anchor = Vector((.025,.01,base+(j%3)*h*.12+h*.2))
            end = Vector((math.cos(angle)*(.85 if apple else .49),math.sin(angle)*(.85 if apple else .49),h*(.62+j*.045)))
            branch = [k.beam('woody_branch',anchor,end,.036 if apple else .018,'bark',6,.009)]
            tips = []
            for n in range(3):
                t = .43+n*.26
                joint = anchor.lerp(end,t)
                tip = joint+Vector((math.cos(angle+n*1.8)*.34,math.sin(angle+n*1.8)*.34,.18))*(1 if apple else .65)
                branch.append(k.beam('twig',joint,tip,.012 if apple else .008,'bark',5,.004))
                tips.append(tip)
            branch_node = organ('Branch',anchor,branch,'structure',.14+j*.008,.41+j*.008,bend=.012)
            attach(branch_node, trunk_node)
            leaves = []
            for n,tip in enumerate(tips):
                for i in range(11):
                    pos = tip+Vector((rng.uniform(-.20,.20),rng.uniform(-.20,.20),rng.uniform(-.07,.18)))
                    leaves.append(k.beam('leaf_petiole',tip,pos,.0035 if apple else .0025,'leaf_dark',4))
                    leaves.append(leaf(pos,angle+i*2.399,.30 if apple else .22,.10 if apple else .071,
                                       ['leaf','leaf_light','leaf_dark'][i%3]))
            foliage_node = organ('Foliage',anchor,leaves,'foliage',.22+j*.01,.46+j*.01,.88,1.01,.028)
            attach(foliage_node, branch_node)
            p = tuple(tips[1]+Vector((0,0,.06)))
            flowers = organ('Blossoms',p,flower(p,.13 if apple else .07), 'blossom',.38,.48,.56,.66,.03)
            attach(flowers, branch_node)
            if apple:
                fp = tuple(Vector(p)-Vector((0,0,.10)))
                parts = fruit(fp,.115+rng.random()*.035)
            else:
                parts = [k.ico('berry',Vector(p)+Vector((math.cos(i*2.4)*.045,math.sin(i*2.4)*.045,-i*.027)),
                               (.042,.041,.048),'fruit_skin',2) for i in range(5)]
            fruits = organ('Fruit',p,parts,'fruit',.53,.76,bend=.025)
            attach(fruits, branch_node)
            fall_x, fall_y = math.cos(angle)*.8, math.sin(angle)*.8
            fall_z = ground_height(fall_x,fall_y)+.024
            fallen = [leaf((fall_x,fall_y,fall_z),angle,.27,.09,'gold')]
            litter = organ('LeafLitter',(fall_x,fall_y,fall_z),fallen,'litter',.87,.91)
            litter['lifeFallHeight'] = h*.55
    elif kind == 'pumpkin-patch':
        for j,(x,y) in enumerate([(-.7,-.6),(.58,-.45),(-.1,.62)]):
            z = k.living_height(x,y)
            sapling(x,y,z)
            points = [Vector((x+math.sin(n*.55+j)*.27,y+(n-3)*.17,z+.03)) for n in range(7)]
            vine = [k.beam('creeping_vine',a,b,.017,'leaf_dark',5) for a,b in zip(points,points[1:])]
            organ('Vine',(x,y,z),vine,'structure',.09,.40)
            for n,p in enumerate(points[1:-1]):
                angle = j*2+n*2.399
                stemend = p+Vector((math.cos(angle)*.17,math.sin(angle)*.17,.16))
                leaves = [k.beam('petiole',p,stemend,.009,'leaf',5),leaf(stemend,angle,.40,.19,'leaf',True)]
                organ('LobedLeaf',p,leaves,'foliage',.18+n*.025,.36+n*.025,.85,1.12,.065)
                if n%2 == 0:
                    fp = tuple(p+Vector((.16,-.12,.10)))
                    organ('PumpkinFlower',fp,flower(fp,.115,5,'pollen'),'blossom',.33+n*.016,.46,.55,.65,.04)
                    radius = .20+rng.random()*.07
                    center = (fp[0],fp[1],k.living_height(fp[0],fp[1])+radius*.72)
                    organ('Pumpkin',(center[0],center[1],center[2]-radius*.72),fruit(center,radius,True),'fruit',.52,.82)
    else:
        for j in range(9):
            x = -.85+(j%3)*.83+rng.uniform(-.13,.13)
            y = -.9+(j//3)*.83+rng.uniform(-.1,.1)
            z = k.living_height(x,y)
            h = rng.uniform(.94,1.42)
            sapling(x,y,z,.17)
            tip = (x+.07,y+.025,z+h)
            stem = [k.beam('sunflower_stem',(x,y,z),tip,.022,'leaf_dark',7,.013)]
            organ('TallStem',(x,y,z),stem,'structure',.07,.43,bend=.022)
            for i in range(4):
                p = (x+i*.016,y,z+h*(.2+i*.15))
                organ('HeartLeaf',p,[leaf(p,i*2.399+j,.32,.135,'leaf',True)],'foliage',.15+i*.035,.33+i*.035,.84,1.13,.10)
            # The head faces outward; petals disappear to reveal a separate seed-bearing disk.
            p = (tip[0],tip[1]-.015,tip[2])
            bud = k.ico('closed_bud',p,(.08,.07,.09),'leaf_dark',2)
            organ('FlowerBud',p,[bud],'bud',.34,.45,.49,.57,.025)
            head = organ('RayFlorets',p,flower(p,.21,16,'pollen'),'blossom',.43,.56,.76,.9,.025)
            head.rotation_euler.x = math.radians(60)
            seedparts = [k.ico('seed_disk',p,(.107,.107,.025),'seed_disk',2)]
            for i in range(45):
                a=i*2.399; r=.09*math.sqrt((i+.5)/45)
                seedparts.append(k.ico('seed',(p[0]+r*math.cos(a),p[1]+r*math.sin(a),p[2]+.025),(.008,.008,.005),'wood_light',1))
            seeds = organ('Seeds',p,seedparts,'seed',.58,.8,bend=.035)
            seeds.rotation_euler.x = math.radians(60)
