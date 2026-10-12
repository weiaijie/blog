"""Bamboo shoot development, meadow flowering and buried potato tubers."""
import math
from mathutils import Vector


def build(k, kind):
    rng = k.RNG
    for name, code in [('bamboo_skin','739A54'),('bamboo_node','BCD18C'),('bamboo_leaf','4D824B'),
                       ('bamboo_leaf_light','83AC59'),('shoot_sheath','93735A'),('ray_white','EEE6D5'),
                       ('ray_pink','CE98AF'),('pollen','D9AA44'),('achene','9A7550'),
                       ('potato_skin','C1A077'),('potato_eye','806345'),('potato_petal','BBA3D2'),
                       ('stolon','C1BDA0')]:
        mat = k.M['leaf'].copy(); mat.name = name
        rgb = [int(code[i:i+2],16)/255 for i in (0,2,4)]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb],1)
        k.M[name] = mat
    for mat in k.M.values(): mat.use_backface_culling = False

    def height(x,y):
        if kind=='potato-field': return .065+.13*sum(math.exp(-((x-c)/.35)**2) for c in [-.83,.83])+.007*math.sin(y*12+x*5)
        return .055+.014*math.sin(x*3)*math.cos(y*4)

    def organ(name,p,parts,role,start,full,end=1.2,gone=1.3,bend=0,parent=None):
        node=k.pivot(name,p,parts)
        for key,value in dict(lifeRole=role,lifeStart=start,lifeFull=full,lifeEnd=end,lifeGone=gone,
                              lifeBend=bend,lifePhase=rng.random()*math.tau,lifeDroopAngle=0).items(): node[key]=value
        if parent:
            k.bpy.context.view_layer.update();world=node.matrix_world.copy();node.parent=parent;node.matrix_world=world
        return node

    def leaf(p,d,length,width,mat='leaf',round_tip=False):
        p=Vector(p);d=Vector(d).normalized();side=Vector((-d.y,d.x,0)).normalized();v=[];faces=[]
        for n in range(6):
            t=n/5;w=width*math.sin(math.pi*t)**(.55 if round_tip else 1)
            c=p+d*length*t+Vector((0,0,length*(.28*t-.33*t*t)))
            v.extend([tuple(c-side*w),tuple(c+Vector((0,0,w*.14))),tuple(c+side*w)])
        for n in range(5):
            for j in range(2):
                a=n*3+j;faces.extend([(a,a+3,a+4),(a,a+4,a+1)])
        return k.mesh('folded_blade',v,faces,mat)

    if kind=='potato-field':
        # Two closed soil volumes. Only the near half is removed for inspection.
        for front,y0,y1 in [(False,0,1.75),(True,-1.75,0)]:
            nx,ny=32,16;v=[];faces=[]
            for j in range(ny+1):
                for i in range(nx+1):
                    x=-1.75+3.5*i/nx;y=y0+(y1-y0)*j/ny;v.append((x,y,height(x,y)))
            for j in range(ny):
                for i in range(nx):
                    a=j*(nx+1)+i;faces.extend([(a,a+1,a+nx+2),(a,a+nx+2,a+nx+1)])
            border=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
            base=len(v);v.extend([(v[i][0],v[i][1],-.55) for i in border])
            for n,a in enumerate(border):
                nxt=(n+1)%len(border);faces.append((a,base+n,base+nxt,border[nxt]))
            faces.append(tuple(reversed(range(base,len(v)))))
            soil=k.mesh('hilled_soil',v,faces,'loam')
            soil.data.materials.append(k.M['loam_light'])
            for face in soil.data.polygons:face.material_index=1 if face.index<nx*ny*2 and rng.random()<.3 else 0
            parts=[soil]
            for n in range(26):
                x=rng.uniform(-1.6,1.6);y=rng.uniform(y0+.08,y1-.08)
                parts.append(k.ico('soil_clod',(x,y,height(x,y)),(.028,.045,.02),'loam_light',1))
            cover=k.pivot('FrontSoilCover' if front else 'BackSoil',(0,0,0),parts)
            if front:cover['inspectionCover']=True
    else:
        k.living_soil(height,lambda x,y:.22+.24*math.exp(-(x*x+y*y)))

    if kind=='bamboo':
        for i,(x,y,h) in enumerate([(-.56,.30,2.52),(.27,.66,2.24),(.65,-.30,1.95),(-.50,-.64,1.73),(.06,-.14,2.70)]):
            base=Vector((x,y,height(x,y)));r=.063+(i%2)*.012;parts=[]
            for n in range(5):
                z=n*.072;a=n*2.4
                parts.append(k.beam('overlapping_shoot_sheath',base+Vector((0,0,z)),base+Vector((math.cos(a)*.012,math.sin(a)*.012,z+.13)),r*(1-n*.16),'shoot_sheath',7,.007))
            organ('BambooShoot',base,parts,'shoot',0,.11,.22,.42)
            parent=None
            for j in range(8):
                p=base+Vector((.055*j*math.cos(i*2.1),.055*j*math.sin(i*2.1),h*j/8));q=base+Vector((.055*(j+1)*math.cos(i*2.1),.055*(j+1)*math.sin(i*2.1),h*(j+1)/8))
                rr=r*(1-j*.075)
                internode=organ('BambooInternode',p,[k.beam('culm_internode',p,q,rr,'bamboo_skin',10,rr*.93),k.beam('raised_node',p,p+Vector((0,0,.022)),rr*1.13,'bamboo_node',10)],'structure',.07+j*.025,.27+j*.033,bend=.008,parent=parent)
                internode['lifeRadialGrowth']=1
                sheath=organ('CulmSheath',p,[leaf(p,(math.cos(i),math.sin(i),1),h/8*.9,rr*1.35,'shoot_sheath')],'husk',.05+j*.025,.18+j*.025,.30+j*.035,.46+j*.035,parent=internode)
                sheath['lifeOpenAngle']=.5;sheath['lifeOpenStart']=.28+j*.03;sheath['lifeOpenFull']=.40+j*.03
                if j>=3:
                    for side in [-1,1]:
                        a=i*1.8+j*.7+(math.pi if side<0 else 0);length=.50-(j-3)*.045
                        tip=p+Vector((math.cos(a)*length,math.sin(a)*length,.12))
                        branch=organ('BambooBranch',p,[k.beam('node_branch',p,tip,.012,'bamboo_skin',5,.003)],'structure',.29+j*.02,.50+j*.025,bend=.018,parent=internode)
                        blades=[]
                        for n in range(5):
                            anchor=p.lerp(tip,.30+n*.16);angle=a+(-.85 if n%2 else .85)
                            blades.append(leaf(anchor,(math.cos(angle),math.sin(angle),.2),.28-n*.019,.031,'bamboo_leaf_light' if i%2 else 'bamboo_leaf'))
                        leafnode=organ('BambooLeaves',p,blades,'foliage',.32+j*.021,.54+j*.026,bend=.045,parent=branch)
                        leafnode['lifeUnfoldAngle']=.35
                parent=internode
                if j==7:
                    tip=q+Vector((.035*math.cos(i*2.1),.035*math.sin(i*2.1),.19))
                    crown=organ('BambooTip',q,[k.beam('tapered_culm_tip',q,tip,rr*.93,'bamboo_skin',7,.002)],'structure',.34,.60,parent=internode)
                    blades=[leaf(q.lerp(tip,.35+n*.25),(math.cos(i+n*2.1),math.sin(i+n*2.1),.35),.20,.025,'bamboo_leaf') for n in range(3)]
                    organ('BambooTipLeaves',q,blades,'foliage',.47,.75,bend=.045,parent=crown)
        for i in range(14):
            a=i*2.399;r=.35+(i%4)*.24;p=Vector((math.cos(a)*r,math.sin(a)*r,height(math.cos(a)*r,math.sin(a)*r)+.004))
            node=organ('BambooOldLeaf',p,[leaf(p,(math.cos(a),math.sin(a),.02),.16,.020,'shoot_sheath')],'litter',.86,.99)
            node['lifeFallHeight']=.25

    elif kind=='wildflowers':
        for i in range(12):
            a=i*2.399;r=.24+(i%4)*.28;x=r*math.cos(a);y=r*math.sin(a);base=Vector((x,y,height(x,y)));h=.48+(i%4)*.14
            rosette=[leaf(base+Vector((0,0,.03)),(math.cos(a+n*2.1),math.sin(a+n*2.1),.3),.17,.043) for n in range(3)]
            organ('MeadowRosette',base,rosette,'shoot',0,.09,.20,.34,.02)
            basal=[leaf(base+Vector((0,0,.025)),(math.cos(a+n*2.1),math.sin(a+n*2.1),.3),.27,.063) for n in range(3)]
            organ('MeadowBasalLeaves',base,basal,'foliage',.10,.30,.87,1.13,.025)
            tip=base+Vector((math.cos(a)*.09,math.sin(a)*.09,h))
            stem=organ('MeadowStem',base,[k.beam('slender_flower_stem',base,tip,.012,'leaf_dark',6,.006)],'structure',.08,.41,bend=.025)
            blades=[]
            for n in range(4):
                angle=a+n*2.4;p=base.lerp(tip,.18+n*.14)
                blades.append(leaf(p,(math.cos(angle),math.sin(angle),.25),.22-n*.023,.048-n*.004))
            organ('MeadowLeaves',base,blades,'foliage',.13,.37,.87,1.13,.025,stem)
            bracts=[leaf(tip+Vector((0,0,-.045)),(math.cos(n*math.tau/8),math.sin(n*math.tau/8),.8),.075,.019,'leaf_dark') for n in range(8)]
            receptacle=organ('FlowerReceptacle',tip,bracts,'structure',.24,.40,parent=stem)
            organ('ClosedMeadowBud',tip,[k.ico('closed_flower_bud',tip+Vector((0,0,.032)),(.054,.054,.085),'leaf_dark',2)],'bud',.22,.32,.36,.48,parent=receptacle)
            for n in range(16):
                angle=n*math.tau/16;anchor=tip+Vector((math.cos(angle)*.046,math.sin(angle)*.046,.028))
                ray=organ('MeadowRay',anchor,[leaf(anchor,(math.cos(angle),math.sin(angle),.12),.15,.028,'ray_pink' if i%4==0 else 'ray_white',True)],'blossom',.33,.48,.62,.77,parent=receptacle)
                ray['lifeUnfurlAngle']=1.15;ray['lifeOpenAxis']=[math.sin(angle),0,math.cos(angle)];ray['lifeOpenStart']=.33;ray['lifeOpenFull']=.49
            florets=[k.ico('disc_floret',tip+Vector((math.cos(n*2.399)*.054*math.sqrt(n/13),math.sin(n*2.399)*.054*math.sqrt(n/13),.047)),(.014,.014,.018),'pollen',1) for n in range(14)]
            organ('MeadowDisc',tip,florets,'blossom',.35,.47,.66,.79,parent=receptacle)
            seeds=[]
            for n in range(16):
                p=tip+Vector((math.cos(n*2.399)*.056*math.sqrt(n/15),math.sin(n*2.399)*.056*math.sqrt(n/15),.012))
                seeds.append(k.beam('ribbed_achene',p,p+Vector((0,0,.048)),.012,'achene',5,.007))
            seedhead=organ('MeadowSeedHead',tip,seeds,'seed',.60,.84,parent=receptacle)
            seedhead['lifeDroopAngle']=.14

    else:
        for i,(x,y) in enumerate([(-.83,-.82),(.83,-.70),(-.83,.82),(.83,.78)]):
            ground=Vector((x,y,height(x,y)));root=Vector((x,y,-.27))
            k.ico('planted_seed_tuber',root,(.105,.075,.065),'potato_skin',2)
            base=organ('PotatoUndergroundStem',root,[k.beam('buried_main_stem',root,ground,.018,'stolon',6)],'structure',.03,.22)
            # Canopy and stolons have independent growth around this buried attachment.
            base['lifeRadialGrowth']=1
            organ('PotatoShoot',ground,[leaf(ground+Vector((0,0,.10)),(1,0,.2),.12,.044),leaf(ground+Vector((0,0,.10)),(-1,0,.3),.12,.044),k.beam('young_stem',ground,ground+Vector((0,0,.13)),.01,'leaf_dark',5)],'shoot',0,.09,.20,.34)
            for j in range(5):
                a=j*2.399+i*.4;anchor=root+Vector((0,0,.025+j*.017));tip=anchor+Vector((math.cos(a)*(.28+j*.025),math.sin(a)*(.28+j*.025),-.015))
                stolon=organ('PotatoStolon',anchor,[k.beam('underground_stolon',anchor,tip,.011,'stolon',5,.007)],'stolon',.20,.48,parent=base)
                size=Vector((.125+(j%2)*.025,.085,.074));parts=[k.ico('swollen_stem_tip',tip,size,'potato_skin',2)]
                for eye in range(6):
                    angle=eye*2.399;p=tip+Vector((size.x*.84*math.cos(angle),size.y*.84*math.sin(angle),size.z*.47))
                    parts.append(k.ico('tuber_eye',p,(.010,.008,.004),'potato_eye',1))
                organ('PotatoTuber',tip,parts,'tuber',.34,.87,parent=stolon)
            for j in range(3):
                a=i+j*2.399;tip=ground+Vector((math.cos(a)*.16,math.sin(a)*.16,.62+j*.065))
                stem=organ('PotatoAerialStem',ground,[k.beam('potato_stem',ground,tip,.018,'leaf_dark',6,.008)],'structure',.10,.43,.91,1.25,.018)
                for n in range(4):
                    angle=a+n*2.4;p=ground.lerp(tip,.22+n*.17);d=Vector((math.cos(angle),math.sin(angle),.20));end=p+d*.34
                    parts=[k.beam('compound_leaf_rachis',p,end,.006,'leaf_dark',5)]
                    for pair in range(3):
                        c=p.lerp(end,.22+pair*.25)
                        for side in [-1,1]:
                            across=Vector((-d.y,d.x,0))*side+d*.25
                            parts.append(leaf(c,across,.16+pair*.020,.061))
                    parts.append(leaf(end,d,.18,.066))
                    node=organ('PotatoCompoundLeaf',p,parts,'foliage',.16+n*.024,.35+n*.023,.86,1.025,.03,stem)
                    node['lifeDroopAngle']=.38;node['lifeDroopStart']=.82
                if j==1:
                    for n in range(3):
                        angle=n*math.tau/3;center=tip+Vector((math.cos(angle)*.10,math.sin(angle)*.10,.08))
                        pedicel=organ('PotatoPedicel',tip,[k.beam('flower_pedicel',tip,center,.005,'leaf_dark',5)],'structure',.29,.44,parent=stem)
                        v=[tuple(center+Vector((0,0,-.022)))]+[tuple(center+Vector((math.cos(t*math.tau/10)*(.087 if t%2==0 else .043),math.sin(t*math.tau/10)*(.087 if t%2==0 else .043),.014))) for t in range(10)]
                        flower=k.mesh('five_lobed_corolla',v,[(0,t+1,(t+1)%10+1) for t in range(10)],'potato_petal')
                        anthers=[k.beam('yellow_anther',center+Vector((math.cos(t*math.tau/5)*.013,math.sin(t*math.tau/5)*.013,0)),center+Vector((math.cos(t*math.tau/5)*.009,math.sin(t*math.tau/5)*.009,.052)),.009,'pollen',5,.006) for t in range(5)]
                        organ('PotatoFlower',center,[flower]+anthers,'blossom',.35,.48,.58,.70,parent=pedicel)
