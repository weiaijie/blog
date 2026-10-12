"""Distinct crop organs and attachment hierarchies for the botanical runtime."""
import math
from mathutils import Vector


def build(k, kind):
    rng = k.RNG
    for name, code in [('fruit_kernel','EAC45B'),('fruit_grape','694B91'),('fruit_boll','9A7046'),
                       ('petal','F2DCB1'),('cotton_lint','F4F1E5'),('paddy_water','6AACA8')]:
        mat = k.M['leaf'].copy()
        mat.name = name
        rgb = [int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear = [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear,1)
        k.M[name] = mat
    for mat in k.M.values(): mat.use_backface_culling = False

    def height(x,y):
        if kind != 'rice-paddy': return k.living_height(x,y)
        r = max(abs(x),abs(y))
        return .055-.032*max(0,min(1,(1.3-r)/.1))+.06*max(0,1-abs(r-1.44)/.14)

    k.living_soil(height)
    if kind == 'rice-paddy':
        water = k.box('shallow_paddy_water',(0,0,.048),(2.52,2.52,.018),'paddy_water',0)
        water['paddyWaterLevel'] = .057
        k.M['paddy_water'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .25
        for x in [-1.35,1.35]:
            k.beam('inlet_marker',(x,0,.10),(x,0,.29),.025,'wood_dark',5)

    def attach(child, parent):
        k.bpy.context.view_layer.update()
        world = child.matrix_world.copy()
        child.parent = parent
        child.matrix_world = world

    def organ(name, anchor, parts, role, start, full, end=1.2, gone=1.3, bend=0, parent=None):
        node = k.pivot(name,anchor,parts)
        for key,value in dict(lifeRole=role,lifeStart=start,lifeFull=full,lifeEnd=end,lifeGone=gone,
                              lifeBend=bend,lifePhase=rng.random()*math.tau).items(): node[key]=value
        if parent: attach(node,parent)
        return node

    def leaf(p, direction, length, width, mat='leaf', lobed=False):
        p, direction = Vector(p), Vector(direction).normalized()
        side = direction.cross(Vector((0,0,1)))
        if side.length < .01: side = Vector((1,0,0))
        side.normalize()
        verts=[]
        for i in range(9):
            t=i/8
            w=width*math.sin(math.pi*t)*(1+.30*math.cos(t*math.pi*6) if lobed else 1)
            c=p+direction*length*t+Vector((0,0,length*(.30*t-.40*t*t)))
            verts.extend([tuple(c-side*w),tuple(c+Vector((0,0,w*.22))),tuple(c+side*w)])
        faces=[]
        for i in range(8):
            for j in range(2):
                a=i*3+j
                faces.extend([(a,a+3,a+4),(a,a+4,a+1)])
        return k.mesh('folded_leaf',verts,faces,mat)

    def shoot(x,y,z):
        parts=[k.beam('seedling_stem',(x,y,z),(x,y,z+.14),.009,'leaf',5)]
        for a in [0,math.pi]: parts.append(leaf((x,y,z+.1),(math.cos(a),math.sin(a),.3),.17,.033,'leaf_light'))
        organ('Seedling',(x,y,z),parts,'shoot',0,.09,.18,.32,.035)

    def blossom(p,size=.07):
        parts=[]
        for i in range(5):
            a=i*math.tau/5
            parts.append(leaf(p,(math.cos(a),math.sin(a),.5),size,size*.43,'petal'))
        parts.append(k.ico('flower_center',p,(size*.22,)*3,'gold',1))
        return parts

    def opening(node, angle, axis):
        node['lifeOpenAngle']=angle
        node['lifeOpenAxis']=[axis[0],axis[2],-axis[1]]
        node['lifeOpenStart']=.70
        node['lifeOpenFull']=.92

    if kind == 'corn-field':
        for j in range(6):
            x=-.77+(j%2)*1.42+rng.uniform(-.09,.09)
            y=-.98+(j//2)*.93+rng.uniform(-.10,.10)
            z=height(x,y); h=rng.uniform(1.42,1.86)
            shoot(x,y,z)
            stem=organ('JointedCornStalk',(x,y,z),[k.beam('corn_culm',(x,y,z),(x+.055,y,z+h),.025,'leaf_dark',7,.012)],'structure',.07,.43,bend=.016)
            for i in range(6):
                t=.15+i*.117; p=Vector((x+.055*t,y,z+h*t)); a=j*.7+i*math.pi
                parts=[leaf(p,(math.cos(a),math.sin(a),.38),.57-i*.028,.066,'leaf_light' if i%3==0 else 'leaf'),
                       k.beam('leaf_sheath',p-Vector((0,0,.045)),p+Vector((0,0,.045)),.028,'leaf',7)]
                organ('CornLeaf',p,parts,'foliage',.12+i*.025,.29+i*.026,.9,1.16,.045,stem)
            tip=Vector((x+.055,y,z+h)); tassel=[]; anthers=[]
            for i in range(7):
                a=i*2.399; end=tip+Vector((math.cos(a)*.14,math.sin(a)*.14,.13+i*.016))
                tassel.append(k.beam('tassel_branch',tip,end,.006,'gold',5))
                for n in range(4): anthers.append(k.ico('anther',tip.lerp(end,(n+1)/4),(.012,.012,.025),'petal',1))
            tassel_axis=organ('CornTasselRachis',tip,tassel,'structure',.31,.46,bend=.035,parent=stem)
            organ('MaleTassel',tip,anthers,'blossom',.34,.47,.62,.75,parent=tassel_axis)
            p=Vector((x+.12,y-.035,z+h*.49))
            organ('EarPeduncle',Vector((x+.03,y,p.z-.06)),[k.beam('ear_stalk',Vector((x+.03,y,p.z-.06)),p,.018,'leaf_dark',6)],'structure',.30,.43,parent=stem)
            earparts=[]
            for row in range(9):
                for col in range(8):
                    a=col*math.tau/8; r=.05*(1-.18*abs(row-4)/4)
                    earparts.append(k.ico('corn_kernel',p+Vector((r*math.cos(a),r*math.sin(a),.035+row*.027)),(.024,.024,.022),'fruit_kernel',1))
            organ('CornEar',p,earparts,'fruit',.53,.81,bend=.006,parent=stem)
            for i in range(4):
                a=i*math.tau/4; anchor=p+Vector((math.cos(a)*.065,math.sin(a)*.065,0))
                node=organ('CornHusk',anchor,[leaf(anchor,(-math.cos(a)*.12,-math.sin(a)*.12,1),.39,.048)],'husk',.38,.59,parent=stem)
                opening(node,.25,(-math.sin(a),math.cos(a),0))
            silk=[]
            for i in range(6):
                start=p+Vector((0,0,.29)); end=start+Vector(((i-2.5)*.014,-.06,.10-i*.006))
                silk.append(k.beam('silk_strand',start,end,.0027,'rope',4))
            organ('EarSilks',p,silk,'blossom',.39,.50,.63,.73,.022,stem)

    elif kind == 'rice-paddy':
        for j in range(9):
            x=-.88+(j%3)*.86+rng.uniform(-.065,.065); y=-.86+(j//3)*.86+rng.uniform(-.07,.07)
            z=height(x,y); shoot(x,y,z)
            for culm in range(3):
                a=culm*2.399+j; h=rng.uniform(.65,.91)
                base=Vector((x,y,z)); tip=base+Vector((math.cos(a)*.11,math.sin(a)*.11,h))
                stem=organ('RiceTiller',base,[k.beam('rice_culm',base,tip,.009,'leaf_dark',5)],'structure',.08+culm*.015,.41+culm*.01,bend=.02)
                for i in range(3):
                    p=base.lerp(tip,.18+i*.23); angle=a+i*2.8
                    organ('RiceBlade',p,[leaf(p,(math.cos(angle),math.sin(angle),1),.46,.020)],'foliage',.13+i*.025,.35+i*.025,.88,1.18,.065,stem)
                grains=[]; flowers=[]; framework=[]
                previous=tip
                for n in range(5):
                    t=(n+1)/5
                    joint=tip+Vector((math.cos(a)*.22*t,math.sin(a)*.22*t,.15*t-.23*t*t))
                    framework.append(k.beam('panicle_axis',previous,joint,.006,'gold',5)); previous=joint
                    for side in [-1,1]:
                        end=joint+Vector((-math.sin(a)*.045*side,math.cos(a)*.045*side,-.02))
                        framework.append(k.beam('spikelet_stalk',joint,end,.0025,'gold',4))
                        grains.append(k.ico('rice_grain',end,(.014,.018,.034),'fruit_kernel',1))
                        if n%2==0: flowers.append(k.ico('rice_anther',end,(.012,.012,.018),'petal',1))
                head=organ('RiceRachis',tip,framework,'structure',.30,.46,bend=.04,parent=stem)
                head['lifeDroopAngle']=.30
                head['lifeDroopStart']=.70
                organ('RiceFlowering',tip,flowers,'blossom',.37,.48,.55,.65,parent=head)
                grain=organ('RicePanicle',tip,grains,'seed',.53,.81,parent=head)
                grain['lifeDroopAngle']=0

    elif kind == 'vineyard':
        for y in [-.67,.67]:
            for x in [-1.35,1.35]:
                k.beam('trellis_post',(x,y,height(x,y)),(x,y,1.53),.044,'wood_dark',6)
                k.beam('trellis_brace',(x,y,.65),(x-math.copysign(.32,x),y,1.35),.022,'wood',5)
            for z in [.69,1.16]: k.beam('training_wire',(-1.35,y,z),(1.35,y,z),.009,'iron',5)
            for x in [-.65,.55]:
                base=Vector((x,y,height(x,y))); shoot(*base)
                trunkparts=[k.beam('vine_trunk',base,(x+.04,y,1.12),.037,'bark',7,.015)]
                trunk=organ('VineTrunk',base,trunkparts,'structure',.07,.38)
                for side in [-1,1]:
                    anchor=Vector((x+.04,y,.98)); end=anchor+Vector((side*.48,.04, .18))
                    cane=organ('TrainingCane',anchor,[k.beam('fruiting_cane',anchor,end,.014,'bark',5,.005)],'structure',.17,.43,parent=trunk)
                    for n in range(3):
                        p=anchor.lerp(end,(n+1)/3); a=n*2.1+side
                        organ('VineLeaf',p,[leaf(p,(math.cos(a),math.sin(a),.25),.34,.14,'leaf',True)],'foliage',.2+n*.025,.4+n*.02,.87,1.1,.04,cane)
                    tendril=[]; p=end.copy()
                    for n in range(12):
                        a=n*.8; q=end+Vector((side*(.03+n*.005),.035*math.cos(a),.035*math.sin(a)))
                        tendril.append(k.beam('coiled_tendril',p,q,.003,'leaf_dark',4)); p=q
                    organ('Tendril',end,tendril,'structure',.29,.50,parent=cane)
                    p=anchor.lerp(end,.58); flowerparts=[]; cluster=[]
                    framework=[k.beam('grape_rachis',p,p-Vector((0,0,.33)),.007,'leaf_dark',5)]
                    for n in range(16):
                        t=n/15; a=n*2.399; r=.085*(1-t*.78)
                        pos=p+Vector((r*math.cos(a),r*math.sin(a),-.09-t*.24))
                        framework.append(k.beam('berry_pedicel',Vector((p.x,p.y,pos.z)),pos,.003,'leaf_dark',4))
                        cluster.append(k.ico('grape_berry',pos,(.046,.043,.05),'fruit_grape',2))
                        if n%2==0: flowerparts.append(k.ico('grape_floret',pos,(.017,.017,.02),'petal',1))
                    bunch=organ('BunchFramework',p,framework,'structure',.29,.44,bend=.018,parent=cane)
                    organ('GrapeFlowers',p,flowerparts,'blossom',.36,.48,.55,.64,parent=bunch)
                    organ('GrapeCluster',p,cluster,'fruit',.53,.82,parent=bunch)

    else:
        for j in range(6):
            x=-.75+(j%2)*1.37+rng.uniform(-.08,.08); y=-.95+(j//2)*.88+rng.uniform(-.08,.08)
            z=height(x,y); shoot(x,y,z); h=rng.uniform(.69,.87)
            stem=organ('CottonStem',(x,y,z),[k.beam('cotton_stem',(x,y,z),(x,y,z+h),.019,'leaf_dark',6,.008)],'structure',.07,.40,bend=.025)
            for n in range(3):
                a=n*2.399+j; anchor=Vector((x,y,z+h*(.32+n*.2)))
                end=anchor+Vector((math.cos(a)*.25,math.sin(a)*.25,.11))
                branch=organ('CottonBranch',anchor,[k.beam('fruit_branch',anchor,end,.010,'leaf_dark',5,.005)],'structure',.17+n*.018,.42+n*.018,parent=stem)
                organ('PalmateLeaf',anchor,[leaf(anchor,(math.cos(a+.5),math.sin(a+.5),.45),.34,.13,'leaf',True)],'foliage',.20,.44,.87,1.06,.045,branch)
                organ('CottonFlower',end,blossom(end,.115),'blossom',.36,.49,.55,.65,.02,branch)
                organ('ClosedBoll',end,[k.ico('green_boll',end+Vector((0,0,.045)),(.075,.075,.10),'fruit_boll',2)],'fruit',.54,.70,.75,.88,parent=branch)
                fibers=[]
                for lobe in range(4):
                    angle=lobe*math.tau/4; base=end+Vector((math.cos(angle)*.04,math.sin(angle)*.04,-.025))
                    shell=organ('BollValve',base,[leaf(base,(-math.cos(angle)*.3,-math.sin(angle)*.3,1),.19,.065,'fruit_boll')],'husk',.63,.73,parent=branch)
                    opening(shell,1.35,(-math.sin(angle),math.cos(angle),0))
                    center=end+Vector((math.cos(angle)*.049,math.sin(angle)*.049,.039))
                    fibers.append(k.ico('cotton_lock',center,(.068,.063,.077),'cotton_lint',2))
                    fibers.append(k.ico('lint_tip',center+Vector((0,0,.06)),(.036,.033,.038),'cotton_lint',1))
                lint=organ('OpenCotton',end,fibers,'seed',.76,.94,bend=.018,parent=branch)
                lint['lifeDroopAngle']=0
