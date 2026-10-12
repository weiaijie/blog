"""Branched, leaf-bearing tree assets; no solid sphere canopy substitutes."""
import math
from mathutils import Vector


def build(k, kind):
    rng = k.RNG
    palm = kind == 'palm-tree'
    birch = kind == 'birch-tree'
    willow = kind == 'willow-tree'
    for name, code in [('birch_bark','D7D8C8'),('bark_mark','4A4940'),('catkin','C6B464'),
                       ('fruit_acorn','956B3C'),('acorn_cap','665737'),('fruit_coconut','9F8050'),
                       ('palm_leaf','538643'),('palm_leaf_light','78964D'),('seed_scale','9C8D57')]:
        mat = k.M['leaf'].copy(); mat.name = name
        rgb = [int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear = [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear,1)
        k.M[name] = mat
    for mat in k.M.values(): mat.use_backface_culling = False

    def height(x,y):
        edge = max(0,min(1,(1.75-max(abs(x),abs(y)))/.2))
        return .055+edge*(.075*math.exp(-(x*x+y*y)*1.8)+.008*math.sin(x*7)*math.cos(y*9))

    k.living_soil(height,lambda x,y: .85*math.exp(-(x*x+y*y)*2.7))

    def attach(child,parent):
        k.bpy.context.view_layer.update()
        world=child.matrix_world.copy(); child.parent=parent; child.matrix_world=world

    def organ(name, anchor, parts, role, start, full, end=1.2, gone=1.3, bend=0, parent=None, axis=None):
        node=k.pivot(name,anchor,parts)
        if axis is not None:
            # Align local Z (glTF local Y) with the branch so axial growth follows its wood.
            k.bpy.context.view_layer.update()
            worlds=[part.matrix_world.copy() for part in parts]
            node.rotation_mode='QUATERNION'
            node.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
            k.bpy.context.view_layer.update()
            for part,world in zip(parts,worlds): part.matrix_world=world
        for key,value in dict(lifeRole=role,lifeStart=start,lifeFull=full,lifeEnd=end,lifeGone=gone,
                              lifeBend=bend,lifePhase=rng.random()*math.tau).items(): node[key]=value
        if parent: attach(node,parent)
        return node

    def blade(p, direction, length, width, mat, shape='narrow'):
        p=Vector(p); direction=Vector(direction).normalized()
        side=direction.cross(Vector((0,0,1)))
        if side.length<.01: side=Vector((1,0,0))
        side.normalize(); verts=[]
        rings=6 if shape in ['oak','birch'] else 4
        for i in range(rings+1):
            t=i/rings
            profile=math.sin(math.pi*t)**(.7 if shape=='oak' else 1)
            if shape=='oak': profile*=.72+.28*math.cos(t*math.pi*8)
            if shape=='birch': profile*=1.2-.5*t+(.12 if i%2 else -.07)
            w=width*profile
            center=p+direction*length*t+Vector((0,0,length*(.14*t-.23*t*t)))
            verts.extend([tuple(center-side*w),tuple(center+Vector((0,0,w*.22))),tuple(center+side*w)])
        faces=[]
        for i in range(rings):
            for j in range(2):
                a=i*3+j; faces.extend([(a,a+3,a+4),(a,a+4,a+1)])
        obj=k.mesh(f'{shape}_leaf_blade',verts,faces,mat)
        return obj

    base=Vector((0,0,height(0,0)))
    seedling_parts=[k.beam('sapling_stem',base,base+Vector((0,0,.28)),.012,'bark',6)]
    for i in range(4):
        a=i*2.399
        seedling_parts.append(blade(base+Vector((0,0,.11+i*.045)),(math.cos(a),math.sin(a),.5),.22,.045,
                                    'palm_leaf' if palm else 'leaf'))
    organ('TreeSeedling',base,seedling_parts,'shoot',0,.09,.17,.32,.025)
    if palm:
        points=[base+Vector((.35*(i/10)**2,-.12*(i/10),2.72*i/10)) for i in range(11)]
    else:
        h=3.1 if birch else 2.55 if willow else 2.8
        points=[base+Vector((.10*math.sin(i*.7),.065*math.sin(i*1.1),h*i/7)) for i in range(8)]
    bark='birch_bark' if birch else 'bark'
    radius=.077 if birch else .13 if palm else .17
    wood=[]
    for i in range(len(points)-1):
        t=i/(len(points)-1)
        taper=.73 if palm else .96
        tip=t+.12 if palm else (i+1)/(len(points)-1)
        wood.append(k.beam('tapered_trunk',points[i],points[i+1],radius*(1-t*taper),bark,9,radius*(1-tip*taper)))
    if not palm:
        for i in range(6):
            a=i*math.tau/6+rng.uniform(-.15,.15)
            end=Vector((math.cos(a)*.42,math.sin(a)*.42,height(math.cos(a)*.42,math.sin(a)*.42)))
            if birch: end=base.lerp(end,.64)
            wood.append(k.beam('root_flare',base+Vector((0,0,.065 if birch else .15)),end,.025 if birch else .055,'bark' if birch else bark,6,.009))
    if birch or palm:
        for i in range(18):
            t=(i+.5)/19; index=min(len(points)-2,int(t*(len(points)-1)))
            p=points[index].lerp(points[index+1],t*(len(points)-1)-index)
            r=radius*(1-t*(.73 if palm else .96))+.003
            for j in range(3 if birch else 9):
                a=j*math.tau/(3 if birch else 9)+i*.63
                arc=.52 if birch else math.tau/9
                wood.append(k.beam('bark_lenticel' if birch else 'leaf_scar',p+Vector((r*math.cos(a),r*math.sin(a),0)),
                                   p+Vector((r*math.cos(a+arc),r*math.sin(a+arc),.007)),.007,'bark_mark' if birch else 'wood_light',4))
    trunk=organ('TreeTrunk',base,wood,'structure',.06,.36)
    trunk['treeSpecies']=kind

    if palm:
        top=points[-1]
        for i in range(11):
            a=i*2.399; length=1.18+rng.random()*.24; high=i>=8
            d=Vector((math.cos(a),math.sin(a),0)); side=Vector((-d.y,d.x,0))
            pts=[top+d*length*t+Vector((0,0,(.95 if high else .62)*t-(.55 if high else 1.04)*t*t)) for t in [n/8 for n in range(9)]]
            parts=[]
            for n in range(8): parts.append(k.beam('frond_rachis',pts[n],pts[n+1],.016*(1-n/10),'palm_leaf',5,.007))
            frond=organ('PalmFrond',top,parts,'structure',.13+i*.006,.38+i*.006,bend=.018,parent=trunk,axis=pts[-1]-top)
            frond['lifeDroopAngle']=.10 if i<2 else 0
            leaves=[]
            for n in range(12):
                t=.14+n*.065; pos=top+d*length*t+Vector((0,0,(.95 if high else .62)*t-(.55 if high else 1.04)*t*t))
                for s in [-1,1]:
                    direction=d*.42+side*s+Vector((0,0,-.18-t*.45))
                    leaves.append(blade(pos,direction,(.45-.20*t),.033,'palm_leaf_light' if i%3==0 else 'palm_leaf'))
            foliage=organ('PalmLeaflets',top,leaves,'foliage',.18+i*.006,.43+i*.006,1.2,1.3,.035,frond)
            foliage['lifeDroopAngle']=0
        for i in range(3):
            a=i*math.tau/3; anchor=top-Vector((0,0,.12)); end=anchor+Vector((math.cos(a)*.24,math.sin(a)*.24,-.28))
            stem=organ('PalmFruitStalk',anchor,[k.beam('fruit_peduncle',anchor,end,.022,'wood_light',6)],'structure',.28,.45,parent=trunk,axis=end-anchor)
            flowers=[]; fruit=[]
            for j in range(4):
                p=end+Vector((math.cos(j*2.399)*.1,math.sin(j*2.399)*.1,-.10*(j%2)))
                flowers.append(k.ico('palm_flower',p,(.04,.04,.055),'catkin',1))
                fruit.append(k.ico('coconut',p,(.115,.105,.145),'fruit_coconut',2))
            organ('PalmFlowers',end,flowers,'blossom',.35,.47,.55,.65,.013,stem)
            organ('Coconuts',end,fruit,'fruit',.54,.83,bend=.012,parent=stem)
        return

    limb_count=10 if birch else 8 if willow else 9
    for i in range(limb_count):
        a=i*2.399+rng.uniform(-.12,.12); t=.40+(i/(limb_count-1))*.54
        idx=min(6,int(t*7)); anchor=points[idx].lerp(points[idx+1],t*7-idx)
        length=(1.23 if willow else .82 if birch else 1.14)*(1-.3*i/limb_count)*rng.uniform(.9,1.12)
        end=anchor+Vector((math.cos(a)*length,math.sin(a)*length,.28 if willow else .45))
        middle=anchor.lerp(end,.50)+Vector((0,0,.15))
        parts=[k.beam('main_limb',anchor,middle,.040 if birch else .065,bark,7,.028),
               k.beam('outer_limb',middle,end,.028,bark,6,.01)]
        branch=organ('BirchBranch' if birch else 'WillowLimb' if willow else 'OakLimb',anchor,parts,'structure',.12+i*.009,.36+i*.007,
                     bend=.006,parent=trunk,axis=end-anchor)
        for n in range(3 if willow or birch else 4):
            q=.38+n*.19
            start=anchor.lerp(middle,q*2) if q<.5 else middle.lerp(end,(q-.5)*2)
            direction=a+(-.8 if n%2 else .8)
            twig_end=start+Vector((math.cos(direction)*.36,math.sin(direction)*.36,-rng.uniform(.78,1.15) if willow else rng.uniform(.18,.38)))
            if willow:
                joints=[start.lerp(twig_end,j/5)+Vector((math.cos(a)*.10*math.sin(j*math.pi/5),math.sin(a)*.10*math.sin(j*math.pi/5),0)) for j in range(6)]
            else: joints=[start,start.lerp(twig_end,.5),twig_end]
            sticks=[k.beam('pendulous_twig' if willow else 'terminal_twig',joints[j],joints[j+1],.012 if j==0 else .007,'wood_light' if willow else bark,5,.004) for j in range(len(joints)-1)]
            twig=organ('WillowPendant' if willow else 'BirchTwig' if birch else 'OakTwig',start,sticks,'structure',.19+n*.018,.42+n*.012,
                       bend=.028 if willow else .018,parent=branch,axis=twig_end-start)
            leaves=[]
            for j in range(16 if willow else 8):
                q=.10+j/(18 if willow else 9); pos=start.lerp(twig_end,q)
                if willow: pos+=Vector((math.cos(a)*.10*math.sin(q*math.pi),math.sin(a)*.10*math.sin(q*math.pi),0))
                angle=direction+(1 if j%2 else -1)*1.25+rng.uniform(-.3,.3)
                petiole=pos+Vector((math.cos(angle)*.035,math.sin(angle)*.035,0))
                leaves.append(k.beam('leaf_petiole',pos,petiole,.003,'leaf_dark',4))
                leaves.append(blade(petiole,(math.cos(angle),math.sin(angle),-.65 if willow else rng.uniform(-.2,.65)),
                                    .34 if willow else .29 if birch else .43,.034 if willow else .100 if birch else .145,
                                    'leaf_light' if (j+i)%3==0 else 'leaf','narrow' if willow else 'birch' if birch else 'oak'))
            organ('WillowLeaves' if willow else 'BirchLeaves' if birch else 'OakLeaves',start,leaves,'foliage',.20+n*.015,.45+n*.009,
                  .88+rng.random()*.03,1.005+rng.random()*.055,.023,twig)
            if n%2: continue
            p=start.lerp(twig_end,.70); floral=[]; harvest=[]
            if willow or birch:
                for j in range(6):
                    pos=p+Vector((0,0,-j*.022))
                    floral.append(k.ico('female_catkin',pos,(.024,.024,.020),'catkin',1))
                    harvest.append(k.ico('seed_capsule',pos,(.027,.026,.022),'seed_scale',1))
            else:
                for j in range(7): floral.append(k.ico('oak_catkin',p+Vector((.014*math.sin(j),0,-j*.024)),(.019,.019,.022),'catkin',1))
                for j in range(2):
                    pos=p+Vector((j*.075,0,-.065))
                    harvest.extend([k.ico('acorn_nut',pos,(.047,.043,.07),'fruit_acorn',1),
                                    k.ico('acorn_cup',pos+Vector((0,0,.045)),(.050,.047,.027),'acorn_cap',1),
                                    k.beam('acorn_stalk',p,pos+Vector((0,0,.06)),.006,bark,5)])
            organ('TreeCatkins',p,floral,'blossom',.34,.46,.55,.65,.02,twig)
            seeds=organ('WillowSeeds' if willow else 'BirchSeeds' if birch else 'Acorns',p,harvest,'seed' if willow or birch else 'fruit',
                        .54,.81,bend=.016,parent=twig)
            seeds['lifeDroopAngle']=0
