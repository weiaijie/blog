"""Branched pine and true reed panicles, replacing the old solid approximations."""
import math
from mathutils import Vector


def build(k,kind):
    rng=k.RNG;pine=kind=='pine-tree'
    for name,code in [('needle','3F7858'),('needle_light','71A56A'),('candle','AAC57D'),
                      ('pollen_cone','C5A166'),('fruit_cone','916C47'),('seed_wing','C1AA7D'),
                      ('reed_flower','A88E9C'),('reed_seed','D1BFA0'),('shore_water','589D9E')]:
        mat=k.M['leaf'].copy();mat.name=name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb],1)
        k.M[name]=mat
    for mat in k.M.values():mat.use_backface_culling=False

    def height(x,y):
        return .06+.05*math.exp(-(x*x+y*y)*2) if pine else .045+.12*(.5+.5*math.tanh((y+.15+.10*math.sin(x*2))/.4))
    k.living_soil(height,lambda x,y:.75*math.exp(-(x*x+y*y)*2) if pine else 1 if height(x,y)<.10 else .35)
    if not pine:
        k.box('shallow_shore_water',(0,-.675,.075),(3.49,2.15,.028),'shore_water',0)
        k.M['shore_water'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.32

    def organ(name,p,parts,role,start,full,end=1.2,gone=1.3,bend=0,parent=None,axis=None):
        node=k.pivot(name,p,parts)
        if axis is not None:
            k.bpy.context.view_layer.update();worlds=[o.matrix_world.copy() for o in parts]
            node.rotation_mode='QUATERNION';node.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
            k.bpy.context.view_layer.update()
            for obj,world in zip(parts,worlds):obj.matrix_world=world
        for key,value in dict(lifeRole=role,lifeStart=start,lifeFull=full,lifeEnd=end,lifeGone=gone,
                              lifeBend=bend,lifePhase=rng.random()*math.tau,lifeDroopAngle=0).items():node[key]=value
        if parent:
            k.bpy.context.view_layer.update();world=node.matrix_world.copy();node.parent=parent;node.matrix_world=world
        return node

    def blade(p,d,length,width,mat='leaf'):
        p=Vector(p);d=Vector(d).normalized();side=Vector((-d.y,d.x,0))
        if side.length<.01:side=Vector((1,0,0))
        side.normalize();v=[];faces=[]
        for i in range(7):
            t=i/6;w=width*math.sin(math.pi*t);c=p+d*length*t+Vector((0,0,length*(.25*t-.45*t*t)))
            v.extend([tuple(c-side*w),tuple(c+Vector((0,0,w*.16))),tuple(c+side*w)])
        for i in range(6):
            for j in range(2):
                a=i*3+j;faces.extend([(a,a+3,a+4),(a,a+4,a+1)])
        return k.mesh('curved_blade',v,faces,mat)

    def needles(p,q,number=16,length=.25,mat='needle'):
        p=Vector(p);q=Vector(q);axis=(q-p).normalized();right=axis.cross(Vector((0,0,1)))
        if right.length<.01:right=Vector((1,0,0))
        right.normalize();up=right.cross(axis).normalized();v=[];faces=[]
        for i in range(number):
            t=.18+.80*i/max(1,number-1);a=i*2.399;c=p.lerp(q,t)
            for j in range(3):
                direction=(axis*.48+right*math.cos(a+j*.23)+up*math.sin(a+j*.23)).normalized()
                side=direction.cross(axis).normalized()*.010;tip=c+direction*length*rng.uniform(.86,1.12);middle=c.lerp(tip,.48)
                b=len(v);v.extend([tuple(c),tuple(middle-side),tuple(middle+up*.008),tuple(middle+side),tuple(tip)])
                faces.extend([(b,b+1,b+2),(b,b+2,b+3),(b+1,b+4,b+2),(b+2,b+4,b+3)])
        return k.mesh('three_needle_fascicles',v,faces,mat)

    if pine:
        base=Vector((0,0,height(0,0)));tip=base+Vector((.05,-.02,3.35))
        organ('PineSeedling',base,[k.beam('seedling_axis',base,base+Vector((0,0,.25)),.012,'bark',5),needles(base,base+Vector((0,0,.25)),8,.16)],'shoot',0,.09,.20,.34,.015)
        wood=[]
        for i in range(7):wood.append(k.beam('trunk_segment',base.lerp(tip,i/7),base.lerp(tip,(i+1)/7),.15*(1-i/7)+.005,'bark',9,.15*(1-(i+1)/7)+.005))
        for i in range(5):
            a=i*2.399;p=base+Vector((math.cos(a)*.35,math.sin(a)*.35,-.02))
            wood.append(k.beam('root_flare',base+Vector((0,0,.10)),p,.048,'bark',6,.01))
        trunk=organ('PineTrunk',base,wood,'structure',.06,.42)
        for layer in range(4):
            for spoke in range(5):
                a=spoke*math.tau/5+layer*.63;anchor=base.lerp(tip,(.70+layer*.64)/3.35)
                length=(1.06-layer*.19)*rng.uniform(.94,1.09);end=anchor+Vector((math.cos(a)*length,math.sin(a)*length,.18))
                limb=organ('PineLimb',anchor,[k.beam('main_bough',anchor,end,.041-layer*.007,'bark',7,.009)],'structure',.10+layer*.018,.30+layer*.017,1.2,1.3,.012,trunk,end-anchor)
                for twig in range(3):
                    p=anchor.lerp(end,.43+twig*.25);angle=a+(-.7 if twig%2 else .7);q=p+Vector((math.cos(angle)*.31,math.sin(angle)*.31,.15))
                    branch=organ('PineTwig',p,[k.beam('needle_bearing_twig',p,q,.012,'bark',5,.003)],'structure',.11+layer*.012,.29+layer*.01,bend=.018,parent=limb,axis=q-p)
                    leaf=organ('PineNeedles',p,[needles(p,q,16,.26 if layer<2 else .22,'needle_light' if spoke%3==0 else 'needle')],'foliage',.12+twig*.016,.30+twig*.009,bend=.026,parent=branch)
                    leaf['lifeUnfoldAngle']=.16
                    candle=organ('PineCandle',q,[k.beam('new_candle',q,q+Vector((0,0,.11)),.020,'candle',6,.004)],'bud',.14,.24,.37,.53,parent=branch)
                    candle['lifeDroopAngle']=0
                if spoke==1:
                    p=anchor.lerp(end,.74);q=p+Vector((0,0,-.10))
                    peduncle=organ('PineConeStalk',p,[k.beam('cone_stalk',p,q,.010,'bark',5)],'structure',.28,.45,parent=limb,axis=q-p)
                    male=[k.ico('pollen_sac',p+Vector((math.cos(i*2.399)*.045,math.sin(i*2.399)*.045,.025+i*.01)),(.026,.026,.040),'pollen_cone',1) for i in range(6)]
                    organ('PinePollenCones',p,male,'pollen',.34,.47,.56,.67,parent=limb)
                    cone=organ('PineSeedCone',q,[k.beam('cone_axis',q,q+Vector((0,0,-.33)),.026,'fruit_cone',7,.008)],'cone',.51,.79,parent=peduncle)
                    for row in range(3):
                        for i in range(6):
                            angle=i*math.tau/6+row*.52;radial=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-radial.y,radial.x,0))
                            hinge=q+Vector((0,0,-row*.072));v=[tuple(hinge-side*.010),tuple(hinge+side*.010),tuple(hinge+radial*.08+side*.045+Vector((0,0,-.068))),tuple(hinge+radial*.085+Vector((0,0,-.12))),tuple(hinge+radial*.08-side*.045+Vector((0,0,-.068)))]
                            scale=organ('ConeScale',hinge,[k.mesh('woody_cone_scale',v,[(0,1,2),(0,2,3),(0,3,4)],'fruit_cone')],'scale',.52,.80,parent=cone)
                            scale['lifeOpenAngle']=-.67;scale['lifeOpenAxis']=[-math.sin(angle),0,-math.cos(angle)];scale['lifeOpenStart']=.78;scale['lifeOpenFull']=.98
                    seeds=[]
                    for i in range(3):
                        a=i*math.tau/3;s=q+Vector((math.cos(a)*.073,math.sin(a)*.073,-.16))
                        seeds.append(k.ico('pine_seed',s,(.015,.013,.022),'wood_dark',1))
                        seeds.append(blade(s,(math.cos(a),math.sin(a),-.4),.074,.014,'seed_wing'))
                    organ('PineWingedSeeds',q,seeds,'seed',.83,.98,parent=cone)
        leader=organ('PineLeader',tip,[k.beam('leader_tip',tip,tip+Vector((0,0,.22)),.012,'bark',5,.001)],'structure',.15,.34,parent=trunk)
        crown=organ('PineCrownNeedles',tip,[needles(tip,tip+Vector((0,0,.22)),12,.19,'needle_light')],'foliage',.15,.34,bend=.018,parent=leader)
        crown['lifeUnfoldAngle']=.16
    else:
        for i,(x,y) in enumerate([(-1.05,-.30),(-.70,.05),(-.24,-.20),(.25,.08),(.76,-.10),(1.12,.22),(-.85,.64),(.02,.58),(.79,.68)]):
            base=Vector((x,y,height(x,y)));h=1.25+(i%3)*.21+rng.uniform(-.07,.07);tip=base+Vector((.065*math.sin(i),.035*math.cos(i),h))
            organ('ReedShoot',base,[blade(base,(math.cos(i),math.sin(i),1),.26,.022),k.beam('young_reed',base,base+Vector((0,0,.20)),.009,'leaf_dark',5)],'shoot',0,.10,.20,.36,.02)
            parts=[k.beam('jointed_culm',base,tip,.019,'leaf_dark',6,.008)]
            for j in range(5):
                p=base.lerp(tip,.17+j*.16);parts.append(k.beam('culm_node',p,p+Vector((0,0,.018)),.022,'leaf_light',6))
            culm=organ('ReedCulm',base,parts,'structure',.08,.41,bend=.028,axis=tip-base)
            for j in range(5):
                p=base.lerp(tip,.16+j*.155);a=i*2.1+j*2.8
                parts=[blade(p,(math.cos(a),math.sin(a),.50),.55-j*.035,.043),k.beam('leaf_sheath',p-Vector((0,0,.06)),p,.023,'leaf',6)]
                node=organ('ReedLeaf',p,parts,'foliage',.14+j*.024,.36+j*.020,.87,1.16,.047,culm)
                node['lifeDroopAngle']=.32;node['lifeDroopStart']=.83
            axes=[k.beam('panicle_rachis',tip,tip+Vector((0,0,.48)),.010,'wood_light',5,.002)];flowers=[];seeds=[]
            for j in range(7):
                for n in range(3):
                    a=n*math.tau/3+j*1.1+rng.uniform(-.25,.25);p=tip+Vector((0,0,.05+j*.057));r=.21*(1-j/8)*rng.uniform(.76,1.19);q=p+Vector((math.cos(a)*r,math.sin(a)*r,rng.uniform(.055,.12)))
                    axes.append(k.beam('panicle_branch',p,q,.0035,'wood_light',4,.001))
                    for m in range(3):
                        center=p.lerp(q,.40+m*.28)
                        flowers.append(k.mesh('reed_spikelet',[tuple(center+Vector((- .016,0,0))),tuple(center+Vector((0,-.012,.023))),tuple(center+Vector((.016,0,0))),tuple(center+Vector((0,.012,.023))),tuple(center+Vector((0,0,.055)))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'reed_flower'))
                        for side in [0,math.pi/2]:
                            angle=a+side+rng.uniform(-.3,.3);d=Vector((math.cos(angle),math.sin(angle),0));perp=Vector((-d.y,d.x,0))
                            length=rng.uniform(.061,.099);v=[];faces=[]
                            for segment in range(4):
                                t=segment/3;c=center+d*(length*.44*t*t)+Vector((0,0,length*t));width=.014*math.sin(math.pi*t)
                                v.extend([tuple(c-perp*width),tuple(c+perp*width)])
                            for segment in range(3):
                                b=segment*2;faces.extend([(b,b+1,b+3),(b,b+3,b+2)])
                            seeds.append(k.mesh('silky_seed_tuft',v,faces,'reed_seed'))
            rachis=organ('ReedPanicle',tip,axes,'structure',.28,.46,bend=.026,parent=culm)
            rachis['lifeDroopAngle']=.16;rachis['lifeDroopStart']=.70
            organ('ReedFlowering',tip,flowers,'blossom',.34,.48,.57,.70,parent=rachis)
            organ('ReedSeedPlume',tip,seeds,'seed',.55,.84,parent=rachis)
