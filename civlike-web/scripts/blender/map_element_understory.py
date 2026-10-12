"""Distinct succulent, fern, fungus and floating-leaf lifecycle specimens."""
import math
from mathutils import Vector


def build(k,kind):
    rng=k.RNG
    colors=[('cactus_skin','618B62'),('cactus_rib','789B68'),('areole','D3C49A'),('spine','E3D6B5'),
            ('fruit_cactus','BF5555'),('lily_petal','DF99BE'),('lily_inner','F1C2D7'),('flower_gold','D6AB48'),
            ('lily_water','4C9299'),('lily_vein','386D48'),('spore_brown','8C6044'),('gill','D5C7AF'),
            ('cap_amber','B68A55'),('cap_brown','8B6B54'),('cap_pale','C9B391'),('stipe','DDCFB4')]
    for name,code in colors:
        mat=k.M['leaf'].copy();mat.name=name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb],1)
        k.M[name]=mat
    for mat in k.M.values(): mat.use_backface_culling=False

    def height(x,y): return .055+.018*math.sin(x*3)*math.cos(y*4)*max(0,min(1,(1.75-max(abs(x),abs(y)))/.2))
    if kind=='lily-pad':
        k.box('pond_sediment',(0,0,.015),(3.5,3.5,.12),'earth',0)
        k.box('pond_water',(0,0,.10),(3.46,3.46,.10),'lily_water',0)
        k.M['lily_water'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.3
    else: k.living_soil(height,lambda x,y: .96 if kind=='cactus' else .7*math.exp(-(x*x+y*y)*.8))

    def organ(name,p,parts,role,start,full,end=1.2,gone=1.3,bend=0,parent=None):
        obj=k.pivot(name,p,parts)
        for key,val in dict(lifeRole=role,lifeStart=start,lifeFull=full,lifeEnd=end,lifeGone=gone,lifeBend=bend,lifePhase=rng.random()*math.tau,lifeDroopAngle=0).items(): obj[key]=val
        if parent:
            k.bpy.context.view_layer.update();world=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=world
        return obj

    def leaf(p,d,length,width,mat='leaf',curl=.14):
        p=Vector(p);d=Vector(d).normalized();side=d.cross(Vector((0,0,1)))
        if side.length<.01:side=Vector((1,0,0))
        side.normalize();v=[];faces=[];rings=6 if kind=='fern' else 4
        for i in range(rings+1):
            t=i/rings;w=math.sin(math.pi*t)*width*(.8+.2*math.cos(t*math.pi*6) if kind=='fern' else 1);c=p+d*length*t+Vector((0,0,curl*length*(t-t*t)))
            v.extend([tuple(c-side*w),tuple(c+Vector((0,0,w*.20))),tuple(c+side*w)])
        for i in range(rings):
            for j in range(2):
                a=i*3+j;faces.extend([(a,a+3,a+4),(a,a+4,a+1)])
        return k.mesh('folded_blade',v,faces,mat)

    def petals(name,p,r,parent,mat='lily_petal',count=12):
        for i in range(count):
            a=i*math.tau/count;anchor=Vector(p)+Vector((math.cos(a)*.025,math.sin(a)*.025,0))
            obj=organ(name,anchor,[leaf(anchor,(math.cos(a),math.sin(a),.38),r,r*.21,mat,.6)],'blossom',.32,.46,.58,.71,.025,parent)
            obj['lifeUnfurlAngle']=1.05
            obj['lifeOpenAxis']=[math.sin(a),0,math.cos(a)]
            obj['lifeOpenStart']=.32;obj['lifeOpenFull']=.48

    if kind=='cactus':
        def column(name,p,h,r,start,parent=None):
            p=Vector(p);v=[];faces=[];segments=32;rings=10
            for j in range(rings+1):
                t=j/rings;top=max(0,(t-.80)/.20);rr=r*math.sqrt(max(.002,1-top*top))
                for i in range(segments):
                    a=i*math.tau/segments;rib=1+.10*math.cos(a*8)
                    v.append(tuple(p+Vector((rr*math.cos(a)*rib,rr*math.sin(a)*rib,h*t))))
            for j in range(rings):
                for i in range(segments):
                    a=j*segments+i;b=j*segments+(i+1)%segments;faces.append((a,b,b+segments,a+segments))
            faces.extend([tuple(reversed(range(segments))),tuple(rings*segments+i for i in range(segments))])
            mesh=k.mesh('ribbed_cactus',v,faces,'cactus_skin');mesh.data.materials.append(k.M['cactus_rib'])
            for f in mesh.data.polygons:f.material_index=1 if f.index%4==0 else 0
            node=organ(name,p,[mesh],'structure',start,start+.30,bend=.006,parent=parent)
            spikes=[];areoles=[];tri=[];sv=[]
            for j in range(6):
                z=h*(.12+j*.125)
                for i in range(8):
                    a=i*math.tau/8;c=p+Vector((math.cos(a)*r*1.105,math.sin(a)*r*1.105,z))
                    areoles.append(k.ico('woolly_areole',c,(.019,.019,.022),'areole',1))
                    for n in [-1,0,1]:
                        tip=c+Vector((math.cos(a)*.065,math.sin(a)*.065,n*.035));side=Vector((-math.sin(a)*.004,math.cos(a)*.004,0));b=len(sv)
                        sv.extend([tuple(c-side),tuple(c+side),tuple(tip)]);tri.append((b,b+1,b+2))
            spikes.append(k.mesh('radial_spines',sv,tri,'spine'))
            organ('CactusAreoles',p,areoles+spikes,'armor',start+.05,start+.34,parent=node)
            tip=p+Vector((0,0,h))
            petals('CactusFlower',tip,.16,node,'gill',10)
            organ('CactusFruit',tip,[k.ico('red_cactus_fruit',tip+Vector((0,0,.06)),(.09,.085,.11),'fruit_cactus',2)],'fruit',.54,.82,bend=.035,parent=node)
            return node
        for j,(x,y,h,r) in enumerate([(-.25,.18,1.95,.24),(.85,.55,.78,.23),(-.78,-.72,.42,.18)]):
            p=Vector((x,y,height(x,y)))
            organ('CactusSeedling',p,[k.ico('young_succulent',p+Vector((0,0,.07)),(.06,.06,.09),'cactus_skin',2)],'shoot',0,.09,.18,.31)
            trunk=column('CactusStem',p,h,r,.07)
            if j==0:
                for side,lift in [(-1,.76),(1,1.06)]:
                    anchor=p+Vector((side*.16,0,lift));end=anchor+Vector((side*.43,0,.10))
                    elbow=organ('CactusElbow',anchor,[k.beam('succulent_arm',anchor,end,.11,'cactus_skin',12,.115)],'structure',.17,.42,parent=trunk)
                    column('CactusArm',end,.48 if side==1 else .67,.115,.20,elbow)

    elif kind=='fern':
        for plant,(x,y,s) in enumerate([(-.48,.35,1),(.65,.50,.72),(.05,-.65,.86)]):
            base=Vector((x,y,height(x,y)))
            organ('FernCrozier',base,[k.beam('young_stipe',base,base+Vector((0,0,.15)),.016,'leaf_dark',6),k.ico('coiled_tip',base+Vector((0,0,.16)),(.04,.025,.04),'leaf',2)],'shoot',0,.09,.19,.34,.02)
            for i in range(6):
                a=i*math.tau/6+plant*.7;d=Vector((math.cos(a),math.sin(a),0));parent=None
                pts=[base+d*s*.92*(j/5)+Vector((0,0,s*(1.60*(j/5)-1.10*(j/5)**2))) for j in range(6)]
                for j in range(5):
                    p,q=pts[j:j+2]
                    axis=organ('FernRachis',p,[k.beam('frond_axis',p,q,.014-j*.002,'leaf_dark',5,.006)],'structure',.08+j*.022,.26+j*.036,bend=.008,parent=parent)
                    axis['lifeUnfurlAngle']=.88
                    axis['lifeOpenAxis']=[math.sin(a),0,math.cos(a)]
                    axis['lifeOpenStart']=.10+j*.028;axis['lifeOpenFull']=.30+j*.032
                    pinnae=[];sori=[]
                    for n in range(2):
                        c=p.lerp(q,.25+n*.44);length=s*(.28*(1-j/6))
                        for side in [-1,1]:
                            across=Vector((-d.y,d.x,0))*side+d*.32
                            pinnae.append(leaf(c,across,length,.050*s,'leaf_light' if i%3==0 else 'leaf'))
                            for dot in [.55]:
                                pos=c+across.normalized()*length*dot+Vector((0,0,.14*length*(dot-dot*dot)-.004))
                                sori.append(k.mesh('sorus',[tuple(pos)]+[tuple(pos+Vector((math.cos(a)*.01,math.sin(a)*.01,0))) for a in [v*math.tau/6 for v in range(6)]],[(0,n+1,(n+1)%6+1) for n in range(6)],'spore_brown'))
                    foliage=organ('FernPinnae',p,pinnae,'foliage',.15+j*.022,.34+j*.032,.9,1.2,.02,axis)
                    organ('FernSori',p,sori,'spore',.56,.81,parent=foliage)
                    parent=axis

    elif kind=='mushrooms':
        k.beam('decaying_log',(-1.2,.7,.22),(.85,1.0,.22),.18,'bark',9,.13)
        for i in range(4): k.beam('bark_fissure',(-1.1,.59+i*.06,.29),(.7,.89+i*.035,.30),.013,'wood_dark',4)
        for i in range(7):
            a=i*2.399;r=.35+(i%3)*.25;x=r*math.cos(a);y=r*math.sin(a)-.12
            base=Vector((x,y,height(x,y)));h=.32+(i%3)*.19+rng.uniform(-.035,.035);radius=.25+(i%3)*.09
            organ('FungalPrimordium',base,[k.ico('mushroom_button',base+Vector((0,0,.045)),(.05,.05,.065),'stipe',2)],'shoot',0,.08,.19,.32)
            stem=organ('MushroomStipe',base,[k.beam('stipe',base,base+Vector((.025,0,h)),.045,'stipe',8,.035)],'structure',.10,.44,bend=.009)
            center=base+Vector((.025,0,h));v=[];closed=[];faces=[];segments=24
            def vertex(t,a,z,gap=0):
                v.append(tuple(center+Vector((radius*t*math.cos(a),radius*t*math.sin(a),radius*z))))
                closed.append(center+Vector((radius*t*.46*math.cos(a),radius*t*.46*math.sin(a),radius*(.78*(1-t*t)-gap))))
            for j in range(7):
                t=j/6
                for n in range(segments):vertex(t,n*math.tau/segments,.52*(1-t*t))
            for j in range(6):
                for n in range(segments):
                    p=j*segments+n;q=j*segments+(n+1)%segments;faces.append((p,q,q+segments,p+segments))
            cap_faces=len(faces)
            for n in range(segments):
                a=n*math.tau/segments;b=len(v)
                for t,angle,gap in [(.10,a,.05),(.97,a,.04),(.97,a+.03,.085),(.10,a+.03,.085)]:vertex(t,angle,.52*(1-t*t)-gap,gap)
                faces.append((b,b+1,b+2,b+3))
            cap=k.mesh('morphing_cap',v,faces,['cap_amber','cap_brown','cap_pale'][i%3]);cap.data.materials.append(k.M['gill'])
            for f in cap.data.polygons:f.material_index=1 if f.index>=cap_faces else 0
            cap.shape_key_add(name='Basis');key=cap.shape_key_add(name='ClosedCap')
            for item,co in zip(key.data,closed):item.co=co
            crown=organ('MushroomCap',center,[cap],'cap',.12,.58,.9,1.12,parent=stem)
            spores=[k.ico('spore_bearing_gill',center+Vector((math.cos(n*math.tau/6)*radius*.6,math.sin(n*math.tau/6)*radius*.6,radius*(.52*.64-.055))),(.028,.012,.006),'spore_brown',1) for n in range(6)]
            organ('MushroomSpores',center,spores,'spore',.57,.81,.91,1.14,parent=crown)

    else:
        for i,(x,y,r) in enumerate([(-.73,.5,.46),(.45,.75,.48),(.82,-.35,.42),(-.60,-.7,.48),(.03,-.20,.41),(-1.1,-.06,.32)]):
            p=Vector((x,y,.18));angle=i*2.399;v=[tuple(p)];faces=[];veins=[];segments=32
            for n in range(segments+1):
                a=angle+.22+(math.tau-.44)*n/segments;rr=r*(1+.018*math.sin(a*7))
                v.append(tuple(p+Vector((math.cos(a)*rr,math.sin(a)*rr,.008*math.cos(a*4)))))
            for n in range(segments):faces.append((0,n+1,n+2))
            pad=k.mesh('notched_lily_pad',v,faces,'leaf_dark' if i%2 else 'leaf')
            for n in range(8):
                a=angle+.32+(math.tau-.64)*n/7
                veins.append(k.beam('radial_leaf_vein',p+Vector((0,0,.006)),p+Vector((math.cos(a)*r*.90,math.sin(a)*r*.90,.006+.008*math.cos(a*4)*.90)),.003,'lily_vein',4))
            organ('LilyRolledLeaf',p,[leaf(p,(math.cos(angle),math.sin(angle),.6),.15,.03,'leaf_dark')],'shoot',0,.09,.18,.31,.01)
            floating=organ('LilyPad',p,[pad]+veins,'foliage',.12,.37,.9,1.16,.012)
            floating['lifeBob']=.007
            floating['lifeUnfoldAngle']=0
            if i in [0,2]:
                anchor=p+Vector((.14,.07,0));tip=anchor+Vector((0,0,.22))
                stalk=organ('LilyPeduncle',anchor,[k.beam('flower_stalk',anchor,tip,.018,'leaf_dark',6)],'structure',.20,.41,bend=.016)
                petals('LilyOuterPetal',tip,.27,stalk,count=12)
                petals('LilyInnerPetal',tip+Vector((0,0,.035)),.17,stalk,'lily_inner',9)
                organ('LilyStamens',tip,[k.ico('golden_stamens',tip+Vector((0,0,.045)),(.08,.08,.05),'flower_gold',2)],'blossom',.35,.47,.59,.71,parent=stalk)
                organ('LilySeedPod',tip,[k.ico('seed_pod',tip,(.065,.065,.075),'earth',2)],'fruit',.56,.82,parent=stalk)
