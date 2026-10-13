"""Stylized workers with deform bones, Blender IK and portable action clips."""
import math
from mathutils import Matrix, Vector
import map_element_character_anatomy

KINDS=('farmer','fisher','woodcutter','merchant','builder','town-resident','engineer')


def build(k,kind,refined=False):
    b=k.bpy
    b.context.scene.frame_start=0;b.context.scene.frame_end=72
    colors={'human_skin':'BE8B67','human_skin_light':'D5A480','human_hair':'544536',
            'human_shirt':{'farmer':'72895B','fisher':'548B95','woodcutter':'A55948','merchant':'646F9B',
                           'builder':'638780','town-resident':'967BA1','engineer':'497F91'}[kind],
            'human_linen':'D9D0B3','human_trousers':'56636A','human_boot':'665342','human_leather':'866A47',
            'builder_mallet':'BA996E','engineer_spanner':'A4B5B8','engineer_bolt':'D5BB76'}
    if refined:
        colors['human_trousers']={'farmer':'75614A','fisher':'49636A','woodcutter':'6F5946','merchant':'555267','builder':'596861','town-resident':'675B69','engineer':'485D65'}[kind]
    for name,code in colors.items():
        mat=k.M['stone'].copy();mat.name=name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color=(*linear,1);mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*linear,1)
        k.M[name]=mat
    data=b.data.armatures.new('WorkerSkeleton');rig=b.data.objects.new('WorkerRig',data)
    b.context.collection.objects.link(rig);b.context.view_layer.objects.active=rig;rig.select_set(True)
    rig['humanProfession']=kind;rig['humanClips']=['Idle','Walk','Work']
    if refined:rig['anatomyVersion']=2
    b.ops.object.mode_set(mode='EDIT')
    bones={}
    def bone(name,head,tail,parent=None,deform=True):
        p=data.edit_bones.new(name);p.head=head;p.tail=tail;p.use_deform=deform
        if parent:p.parent=bones[parent]
        bones[name]=p
    bone('Root',(0,0,0),(0,0,.2),deform=False)
    bone('Spine',(0,0,.89),(0,0,1.38),'Root')
    bone('Head',(0,0,1.46),(0,0,1.78),'Spine')
    for s,side in [(1,'R'),(-1,'L')]:
        bone('Thigh'+side,(s*.13,0,.90),(s*.13,-.045,.53),'Spine')
        bone('Shin'+side,(s*.13,-.045,.53),(s*.13,0,.16),'Thigh'+side)
        bone('Foot'+side,(s*.13,0,.16),(s*.13,-.16,.08),'Shin'+side)
        bone('FootTarget'+side,(s*.13,0,.16),(s*.13,-.16,.08),'Root',False)
        bone('Arm'+side,(s*.23,0,1.36),(s*.34,-.03,1.10),'Spine')
        bone('Forearm'+side,(s*.34,-.03,1.10),(s*.40,-.10,.89),'Arm'+side)
        bone('Hand'+side,(s*.40,-.10,.89),(s*.40,-.10,.79),'Forearm'+side)
        bone('HandTarget'+side,(s*.40,-.10,.89),(s*.40,-.10,.79),'Root',False)
    if kind in ['builder','engineer']:
        # The contact bone shares the tool's grasp transform, including exported IK baking.
        y=-.155 if kind=='builder' else -.10
        bone('ToolContact',(.40,y,1.17),(.40,y,1.20),'HandR',False)
    if kind=='engineer':bone('ValveNut',(.16,-.32,1.34),(.16,-.32,1.44),'Root')
    b.ops.object.mode_set(mode='OBJECT')
    for side in ['R','L']:
        for chain,target in [('Shin','Foot'),('Forearm','Hand')]:
            ik=rig.pose.bones[chain+side].constraints.new('IK');ik.target=rig;ik.subtarget=target+'Target'+side;ik.chain_count=2
            ik.use_stretch=False
            copy=rig.pose.bones[target+side].constraints.new('COPY_ROTATION');copy.target=rig;copy.subtarget=target+'Target'+side
    for p in rig.pose.bones:p.rotation_mode='XYZ'
    def skin(obj,name):
        obj.parent=rig;group=obj.vertex_groups.new(name=name);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
        mod=obj.modifiers.new('WorkerSkin','ARMATURE');mod.object=rig
        return obj
    def loft(name,rings,material,parent='Spine',segments=12):
        v=[]
        for z,w,d in rings:
            for i in range(segments):
                a=i*math.tau/segments;v.append((w*math.sin(a),d*math.cos(a),z))
        f=[tuple(reversed(range(segments))),tuple(range((len(rings)-1)*segments,len(rings)*segments))]
        for j in range(len(rings)-1):
            for i in range(segments):
                a=j*segments+i;c=j*segments+(i+1)%segments;f.append((a,c,c+segments,a+segments))
        return skin(k.mesh(name,v,f,material),parent)
    if refined:
        map_element_character_anatomy.build(k,kind,rig,skin)
    else:
        base_anatomy(k,kind,skin,loft)
    # Tools are skinned to the grasp bone, so they also work in external GLB viewers.
    gx,gy,gz=.40,-.10,.89
    if kind=='farmer':
        loft('straw_hat_crown',[(1.76,.142,.13),(1.87,.12,.11),(1.90,.04,.04)],'straw_light','Head',16)
        loft('wide_straw_brim',[(1.762,.27,.245),(1.783,.255,.23)],'straw','Head',20)
        if refined:loft('hat_ribbon',[(1.78,.142,.131),(1.81,.138,.127)],'human_leather','Head',16)
        skin(k.beam('hoe_handle',(gx,gy,gz-.84),(gx,gy,gz+.39),.019,'wood_light',8),'HandR')
        skin(k.box('hoe_blade',(gx,gy-.10,gz-.85),(.25,.20,.027),'iron',.008),'HandR')
        skin(k.box('seed_pouch',(-.19,-.025,.93),(.15,.10,.17),'human_leather',.025),'Spine')
    elif kind=='fisher':
        loft('fishing_hat',[(1.75,.145,.13),(1.85,.116,.105)],'human_shirt','Head')
        loft('hat_brim',[(1.755,.20,.185),(1.77,.20,.185)],'human_linen','Head',16)
        for j in range(8):
            a=(gx,gy-j*.035,gz+j*.15);c=(gx,gy-(j+1)*.035,gz+(j+1)*.15)
            skin(k.beam('rod_section',a,c,.012-j*.001,'wood',6),'HandR')
        skin(k.beam('fishing_line',(gx,gy-.28,gz+1.20),(gx,gy-.58,gz-.54),.0025,'rope',4),'HandR')
        skin(k.ico('float',(gx,gy-.58,gz-.54),(.022,.022,.04),'tile',1),'HandR')
        skin(k.box('woven_creel',(-.20,.045,.94),(.18,.19,.21),'wood_light',.026),'Spine')
        for j in range(6):skin(k.box('creel_weave',(-.20,-.053,.865+j*.031),(.18,.009,.011),'wood_dark',0),'Spine')
    elif kind=='woodcutter':
        skin(k.ico('short_beard',(0,-.081,1.546),(.084,.057,.082),'human_hair',2),'Head')
        for s in [-1,1]:skin(k.box('vest_panel',(s*.135,-.128,1.25),(.13,.025,.28),'human_leather',.008),'Spine')
        skin(k.beam('axe_handle',(gx,gy,gz-.16),(gx,gy,gz+.51),.023,'wood_light',8),'HandR')
        skin(k.mesh('wedge_axe',[(gx-.06,gy-.05,gz+.38),(gx-.06,gy+.035,gz+.56),(gx+.06,gy+.035,gz+.56),(gx+.06,gy-.05,gz+.38),(gx,gy-.24,gz+.37),(gx,gy-.20,gz+.59)],[(0,1,2,3),(0,4,5,1),(3,2,5,4),(1,5,2),(0,3,4)],'iron'),'HandR')
    elif kind=='merchant':
        loft('merchant_cap',[(1.755,.147,.13),(1.83,.13,.117),(1.85,.06,.07)],'human_shirt','Head')
        skin(k.box('travel_pack',(0,.17,1.19),(.34,.19,.40),'human_leather',.03),'Spine')
        for s in [-1,1]:skin(k.beam('pack_strap',(s*.11,-.13,1.03),(s*.16,-.13,1.36),.016,'wood_dark',5),'Spine')
        skin(k.box('ledger',(-.40,-.14,.84),(.17,.24,.035),'wood_dark',.007),'HandL')
        skin(k.box('ledger_pages',(-.40,-.14,.863),(.148,.219,.015),'human_linen',.004),'HandL')
        for j in range(4):skin(k.box('ledger_line',(-.40,-.21+j*.04,.873),(.105,.004,.002),'wood',0),'HandL')
        skin(k.ico('coin',(gx,gy-.015,gz-.05),(.025,.025,.008),'gold',2),'HandR')
    elif kind=='builder':
        loft('work_cap',[(1.75,.146,.134),(1.84,.137,.126),(1.89,.075,.075)],'human_linen','Head',16)
        skin(k.box('cap_peak',(0,-.145,1.759),(.25,.12,.025),'human_leather',.01),'Head')
        skin(k.box('apron_bib',(0,-.139,1.25),(.27,.025,.24),'human_leather',.012),'Spine')
        loft('short_work_apron',[(.78,.194,.146),(.98,.187,.122)],'human_leather')
        for s in [-1,1]:
            skin(k.beam('apron_strap',(s*.10,-.143,1.36),(s*.15,.08,1.37),.013,'human_linen',6),'Spine')
            skin(k.box('apron_pocket',(s*.10,-.146,.90),(.13,.025,.12),'wood_light',.01),'Spine')
        skin(k.beam('mallet_handle',(gx,gy,gz-.12),(gx,gy,gz+.30),.022,'wood_dark',10),'HandR')
        skin(k.box('mallet_head',(gx,gy,gz+.28),(.17,.11,.11),'builder_mallet',.012),'HandR')
        for x in [-.065,.065]:skin(k.box('mallet_iron_band',(gx+x,gy,gz+.28),(.019,.115,.115),'iron',.005),'HandR')
        skin(k.beam('belt_chisel',(-.22,.0,.79),(-.22,.0,1.07),.016,'iron',6),'Spine')
    elif kind=='town-resident':
        skin(k.ico('hair_bun',(0,.116,1.71),(.085,.067,.088),'human_hair',2),'Head')
        for s in [-1,1]:
            skin(k.beam('coat_lapel',(s*.09,-.116,1.395),(s*.045,-.151,1.19),.024,'human_linen',5),'Spine')
            skin(k.box('coat_pocket',(s*.115,-.127,.93),(.09,.018,.075),'human_shirt',.006),'Spine')
        for j in range(4):skin(k.ico('coat_button',(0,-.133,1.13-j*.063),(.012,.008,.012),'gold',1),'Spine')
        skin(k.beam('scarf_collar',(-.075,-.025,1.42),(.07,-.025,1.42),.065,'tile',10),'Spine')
        skin(k.box('scarf_tail',(.073,-.155,1.27),(.066,.023,.22),'tile',.005),'Spine')
        # An open basket has a separate rim, woven walls and actual contents, not a solid box.
        bx,by,bz=-.40,-.108,.64
        skin(k.box('basket_base',(bx,by,bz-.10),(.20,.19,.025),'wood',.01),'HandL')
        for j in range(5):
            z=bz-.08+j*.035
            for s in [-1,1]:
                skin(k.beam('basket_weft',(bx-.10,by+s*.095,z),(bx+.10,by+s*.095,z),.012,'wood_light',6),'HandL')
                skin(k.beam('basket_weft',(bx+s*.10,by-.095,z),(bx+s*.10,by+.095,z),.012,'wood_light',6),'HandL')
        for j in range(7):
            for s in [-1,1]:skin(k.beam('basket_upright',(bx-.09+j*.03,by+s*.095,bz-.10),(bx-.09+j*.03,by+s*.095,bz+.065),.008,'wood_dark',5),'HandL')
        for j in range(12):
            a=j*math.pi/12;c=(j+1)*math.pi/12
            skin(k.beam('basket_handle',(bx+.10*math.cos(a),by,bz+.06+.15*math.sin(a)),
                        (bx+.10*math.cos(c),by,bz+.06+.15*math.sin(c)),.011,'wood_dark',6),'HandL')
        for x,y,z,mat in [(-.045,-.04,.036,'berry'),(.039,-.025,.048,'leaf_light'),(0,.044,.062,'grain')]:
            skin(k.ico('market_produce',(bx+x,by+y,bz+z),(.053,.048,.057),mat,2),'HandL')
    elif kind=='engineer':
        loft('engineer_cap',[(1.75,.146,.134),(1.84,.14,.128),(1.86,.095,.095)],'human_shirt','Head',16)
        skin(k.box('engineer_visor',(0,-.141,1.76),(.25,.15,.026),'wood_dark',.012),'Head')
        for s in [-1,1]:
            skin(k.box('overall_bib_strap',(s*.118,-.127,1.24),(.043,.028,.31),'human_leather',.005),'Spine')
            skin(k.ico('strap_rivet',(s*.118,-.147,1.12),(.013,.01,.013),'gold',1),'Spine')
        skin(k.box('bib_pocket',(0,-.146,1.21),(.16,.018,.11),'human_linen',.005),'Spine')
        for x in [-.035,.012]:skin(k.beam('pocket_pencil',(x,-.16,1.21),(x,-.16,1.33),.008,'tile',6),'Spine')
        skin(k.box('clipboard',(-.40,-.14,.84),(.20,.26,.027),'wood_dark',.006),'HandL')
        skin(k.box('blueprint',(-.40,-.14,.86),(.18,.24,.012),'teal',.003),'HandL')
        for j in range(5):skin(k.box('drawing_grid',(-.40,-.22+j*.04,.867),(.15,.002,.001),'human_linen',0),'HandL')
        for j in range(4):skin(k.box('drawing_grid',(-.46+j*.04,-.14,.868),(.002,.21,.001),'human_linen',0),'HandL')
        skin(k.box('board_clip',(-.40,-.24,.88),(.065,.033,.014),'iron',.003),'HandL')
        skin(k.beam('spanner_shaft',(gx,gy,gz-.13),(gx,gy,gz+.24),.018,'engineer_spanner',8),'HandR')
        skin(k.box('spanner_heel',(gx,gy,gz+.239),(.106,.04,.023),'engineer_spanner',.005),'HandR')
        for s in [-1,1]:skin(k.box('spanner_jaw',(gx+s*.041,gy,gz+.281),(.027,.04,.068),'engineer_spanner',.004),'HandR')
    # An authored work prop is independent of the skeleton and can be hidden during travel.
    props=[]
    if kind=='woodcutter':
        props.append(k.beam('chopping_stump',(0,-.88,0),(0,-.88,.76),.22,'bark',12,.19))
        props.append(k.beam('cut_wood',(0,-.88,.76),(0,-.88,.77),.185,'wood_light',12))
    elif kind=='farmer':
        props.append(k.box('worked_soil',(0,-.60,.027),(.72,.62,.05),'earth',.02))
        for j in range(4):props.append(k.beam('small_furrow',(-.3,-.85+j*.15,.05),(.3,-.85+j*.15,.05),.024,'earth_light',5))
    elif kind=='builder':
        for x in [-.24,.24]:
            for y in [-.69,-.39]:props.append(k.beam('trestle_leg',(x*1.1,y,0),(x,y,.81),.038,'wood',6))
        props.append(k.box('masonry_bench',(0,-.54,.845),(.69,.48,.07),'wood_light',.015))
        props.append(k.box('mortar_bed',(0,-.53,.895),(.47,.27,.035),'stone_light',.008))
        props.append(k.box('setting_brick',(0,-.52,.946),(.38,.22,.078),'tile',.008))
        for j in range(3):props.append(k.box('spare_brick',(.46,-.52,.046+j*.093),(.26,.17,.085),'tile',.01))
    elif kind=='engineer':
        props.append(k.box('service_base',(.16,-.46,.045),(.47,.48,.09),'iron',.015))
        props.append(k.beam('service_column',(.16,-.46,.09),(.16,-.46,1.21),.063,'iron',8))
        props.append(k.box('valve_housing',(.16,-.42,1.34),(.32,.16,.27),'teal',.035))
        props.append(k.beam('valve_nut',(.16,-.348,1.34),(.16,-.301,1.34),.032,'engineer_bolt',6))
        props.append(k.beam('pipe_inlet',(-.11,-.42,1.34),(.43,-.42,1.34),.048,'iron',10))
        for x in [-.11,.43]:props.append(k.beam('pipe_flange',(x-.012,-.42,1.34),(x+.012,-.42,1.34),.08,'iron',10))
        # One skin per fixture part keeps the rotating nut in the same portable Work clip.
        for obj in props:skin(obj,'ValveNut' if obj.name=='valve_nut' else 'Root')
    if props:
        prop=k.pivot('WorkProp',(0,0,0),props);prop['humanWorkProp']=True
    actions=[]
    rest={p.name:data.bones[p.name].matrix_local.copy() for p in rig.pose.bones}
    def control(name,pos,tilt=0,axis='X'):
        p=rig.pose.bones[name]
        orientation=Matrix.Rotation(tilt,4,axis) @ rest[name].to_3x3().to_4x4()
        orientation.translation=pos;p.matrix=orientation
    for mode in ['Idle','Walk','Work']:
        rig.animation_data_create();rig.animation_data.action=None
        action=b.data.actions.new(mode);action.use_fake_user=True;rig.animation_data.action=action
        for frame in range(73):
            t=frame/72*math.tau
            for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
            spine=rig.pose.bones['Spine'];spine.location.y=0 if refined and mode=='Idle' else -.022
            spine.rotation_euler.x=.009*math.sin(t)
            rig.pose.bones['Head'].rotation_euler.y=.035*math.sin(t)
            for s,side in [(1,'R'),(-1,'L')]:
                phase=t+(0 if s==1 else math.pi);stride=math.sin(phase)
                control('FootTarget'+side,(s*.13,-.19*stride if mode=='Walk' else 0,.16+(.075*max(0,math.cos(phase)) if mode=='Walk' else 0)))
                if refined and mode=='Walk':
                    p=(frame/72+(0 if s==1 else .5))%1
                    swing=max(0,(p-.62)/.38)
                    forward=.18*(1-2*p/.62) if p<.62 else .18*(-1+2*swing*swing*(3-2*swing))
                    control('FootTarget'+side,(s*.13,forward,.16+.075*math.sin(swing*math.pi)))
                control('HandTarget'+side,(s*.39,-.10+(.15*stride if mode=='Walk' else .008*math.sin(t+s)),.91))
            if kind=='town-resident':
                control('HandTargetL',(-.40,-.12+.025*math.sin(t),.92))
            if mode=='Work':
                u=.5+.5*math.cos(t)
                if kind=='farmer':
                    angle=-.20-.20*u;right=Vector((0,-.22-.06*(1-u),.96+.15*u))
                    control('HandTargetR',right,angle);control('HandTargetL',right+Vector((0,-.18*math.sin(angle),.18*math.cos(angle))),angle)
                    spine.rotation_euler.x=.12+.12*(1-u)
                elif kind=='woodcutter':
                    angle=1.65*(1-u);right=Vector((0,-.26-.04*(1-u),1.03+.27*u))
                    control('HandTargetR',right,angle);control('HandTargetL',right+Vector((0,-.17*math.sin(angle),.17*math.cos(angle))),angle)
                    spine.rotation_euler.x=.18*(1-u)
                elif kind=='fisher':
                    control('HandTargetR',(.13,-.36,1.06+.018*math.sin(t)),.33)
                    control('HandTargetL',(.10+.025*math.cos(t*2),-.38+.025*math.sin(t*2),.99),.15)
                elif kind=='merchant':
                    control('HandTargetL',(-.14,-.35,1.10),-.9)
                    control('HandTargetR',(.03+.11*math.cos(t),-.36+.05*math.sin(t),1.15+.045*math.sin(t)),.8)
                elif kind=='builder':
                    control('HandTargetR',(0,-.24,1.04+.16*u),math.pi/2*(1-u))
                    control('HandTargetL',(-.21,-.31,1.09),.45)
                    spine.rotation_euler.x=.045*(1-u)
                elif kind=='town-resident':
                    control('HandTargetR',(.36+.055*math.sin(t*2),-.19,1.60),math.pi+.2*math.sin(t*2))
                    rig.pose.bones['Head'].rotation_euler.y=.075*math.sin(t)
                elif kind=='engineer':
                    angle=.4*math.sin(t);bolt=Vector((.16,-.32,1.34))
                    control('HandTargetR',bolt-Matrix.Rotation(angle,3,'Y')@Vector((0,0,.28)),angle,'Y')
                    control('HandTargetL',(-.15,-.32,1.13),-.8)
                    rig.pose.bones['ValveNut'].rotation_euler.z=-angle
            b.context.view_layer.update()
            for p in rig.pose.bones:
                if p.name.startswith(('FootTarget','HandTarget')) or p.name in ['Spine','Head','ValveNut']:
                    p.keyframe_insert(data_path='location',frame=frame)
                    p.keyframe_insert(data_path='rotation_euler',frame=frame)
        actions.append(action)
    rig.animation_data.action=actions[0]
    b.context.scene.frame_set(0)
    # Bounds include every evaluated action and the working tools, not only the bind pose.
    minimum=Vector((100,100,100));maximum=Vector((-100,-100,-100))
    for action in actions:
        rig.animation_data.action=action
        for frame in range(0,73,3):
            b.context.scene.frame_set(frame);graph=b.context.evaluated_depsgraph_get()
            for obj in b.context.scene.objects:
                if obj.type!='MESH':continue
                evaluated=obj.evaluated_get(graph)
                for corner in evaluated.bound_box:
                    p=evaluated.matrix_world@Vector(corner)
                    for axis in range(3):minimum[axis]=min(minimum[axis],p[axis]);maximum[axis]=max(maximum[axis],p[axis])
    rig['animationBoundsMin']=[minimum.x-.04,minimum.z-.04,-maximum.y-.04]
    rig['animationBoundsMax']=[maximum.x+.04,maximum.z+.04,-minimum.y+.04]
    rig.animation_data.action=actions[0];b.context.scene.frame_set(0)


def base_anatomy(k,kind,skin,loft):
    loft('tailored_tunic',[(.84,.18,.12),(.98,.175,.105),(1.17,.19,.13),(1.34,.24,.13),(1.40,.16,.10)],'human_shirt')
    loft('leather_belt',[(.985,.182,.111),(1.025,.18,.111)],'human_leather')
    skin(k.box('belt_buckle',(0,-.119,1.008),(.075,.022,.05),'iron',.005),'Spine')
    skin(k.beam('neck',(0,0,1.37),(0,0,1.51),.065,'human_skin',10),'Head')
    skin(k.ico('faceted_head',(0,-.005,1.625),(.132,.114,.175),'human_skin',2),'Head')
    skin(k.ico('hair_cap',(0,.026,1.73),(.136,.105,.093),'human_hair',2),'Head')
    for s in [-1,1]:
        skin(k.ico('ear',(s*.127,0,1.62),(.026,.032,.044),'human_skin',1),'Head')
        skin(k.ico('eye',(s*.047,-.105,1.65),(.011,.009,.010),'eye',1),'Head')
        skin(k.beam('eyebrow',(s*.02,-.104,1.676),(s*.073,-.099,1.677),.006,'human_hair',4),'Head')
    skin(k.mesh('nose',[(-.018,-.103,1.655),(.018,-.103,1.655),(0,-.158,1.603),(-.024,-.116,1.596),(.024,-.116,1.596)],[(0,1,2),(0,2,3),(1,4,2),(2,4,3)],'human_skin_light'),'Head')
    skin(k.beam('mouth',(-.027,-.109,1.565),(.027,-.109,1.565),.005,'human_hair',4),'Head')
    for s,side in [(1,'R'),(-1,'L')]:
        hip=(s*.13,0,.90);knee=(s*.13,-.045,.53);ankle=(s*.13,0,.16)
        skin(k.beam('trouser_thigh',hip,knee,.093,'human_trousers',9,.072),'Thigh'+side)
        skin(k.ico('knee',knee,(.075,.071,.074),'human_trousers',1),'Shin'+side)
        skin(k.beam('trouser_calf',knee,ankle,.068,'human_trousers',9,.049),'Shin'+side)
        skin(k.box('boot',(s*.13,-.061,.082),(.17,.29,.15),'human_boot',.025),'Foot'+side)
        skin(k.box('boot_sole',(s*.13,-.063,.013),(.176,.296,.026),'wood_dark',.006),'Foot'+side)
        shoulder=(s*.23,0,1.36);elbow=(s*.34,-.03,1.10);wrist=(s*.40,-.10,.89)
        skin(k.ico('sleeve_shoulder',shoulder,(.087,.086,.091),'human_shirt',2),'Arm'+side)
        skin(k.beam('sleeve',shoulder,elbow,.082,'human_shirt',10,.062),'Arm'+side)
        skin(k.ico('elbow',elbow,(.060,.058,.063),'human_skin',1),'Forearm'+side)
        skin(k.beam('forearm',elbow,wrist,.057,'human_skin',9,.038),'Forearm'+side)
        open_hand=kind=='town-resident' and side=='R'
        skin(k.ico('open_palm' if open_hand else 'mitten_hand',(s*.40,-.108,.845),(.038,.021,.041) if open_hand else (.044,.033,.059),'human_skin_light',2),'Hand'+side)
        if open_hand:
            for j in range(4):
                x=.374+j*.017;length=.038+(.008 if j in [1,2] else 0)
                skin(k.beam('greeting_finger',(x,-.108,.819),(x+(j-1.5)*.004,-.108,.819-length),.008,'human_skin_light',7),'HandR')
                skin(k.ico('fingertip',(x+(j-1.5)*.004,-.108,.819-length),(.008,.008,.009),'human_skin_light',1),'HandR')
        skin(k.ico('thumb',(s*.37,-.13,.858),(.023,.022,.035),'human_skin',1),'Hand'+side)
