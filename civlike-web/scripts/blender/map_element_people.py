"""Stylized workers with deform bones, Blender IK and portable action clips."""
import math
from mathutils import Matrix, Vector

KINDS=('farmer','fisher','woodcutter','merchant')


def build(k,kind):
    b=k.bpy
    b.context.scene.frame_start=0;b.context.scene.frame_end=72
    colors={'human_skin':'BE8B67','human_skin_light':'D5A480','human_hair':'544536',
            'human_shirt':{'farmer':'72895B','fisher':'548B95','woodcutter':'A55948','merchant':'646F9B'}[kind],
            'human_linen':'D9D0B3','human_trousers':'56636A','human_boot':'665342','human_leather':'866A47'}
    for name,code in colors.items():
        mat=k.M['stone'].copy();mat.name=name
        rgb=[int(code[i:i+2],16)/255 for i in (0,2,4)]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        mat.diffuse_color=(*linear,1);mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*linear,1)
        k.M[name]=mat
    data=b.data.armatures.new('WorkerSkeleton');rig=b.data.objects.new('WorkerRig',data)
    b.context.collection.objects.link(rig);b.context.view_layer.objects.active=rig;rig.select_set(True)
    rig['humanProfession']=kind;rig['humanClips']=['Idle','Walk','Work']
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
        skin(k.ico('mitten_hand',(s*.40,-.108,.845),(.044,.033,.059),'human_skin_light',2),'Hand'+side)
        skin(k.ico('thumb',(s*.37,-.13,.858),(.023,.022,.035),'human_skin',1),'Hand'+side)
    # Tools are skinned to the grasp bone, so they also work in external GLB viewers.
    gx,gy,gz=.40,-.10,.89
    if kind=='farmer':
        loft('straw_hat_crown',[(1.76,.142,.13),(1.87,.12,.11),(1.90,.04,.04)],'straw_light','Head',16)
        loft('wide_straw_brim',[(1.762,.27,.245),(1.783,.255,.23)],'straw','Head',20)
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
    else:
        loft('merchant_cap',[(1.755,.147,.13),(1.83,.13,.117),(1.85,.06,.07)],'human_shirt','Head')
        skin(k.box('travel_pack',(0,.17,1.19),(.34,.19,.40),'human_leather',.03),'Spine')
        for s in [-1,1]:skin(k.beam('pack_strap',(s*.11,-.13,1.03),(s*.16,-.13,1.36),.016,'wood_dark',5),'Spine')
        skin(k.box('ledger',(-.40,-.14,.84),(.17,.24,.035),'wood_dark',.007),'HandL')
        skin(k.box('ledger_pages',(-.40,-.14,.863),(.148,.219,.015),'human_linen',.004),'HandL')
        for j in range(4):skin(k.box('ledger_line',(-.40,-.21+j*.04,.873),(.105,.004,.002),'wood',0),'HandL')
        skin(k.ico('coin',(gx,gy-.015,gz-.05),(.025,.025,.008),'gold',2),'HandR')
    # An authored work prop is independent of the skeleton and can be hidden during travel.
    props=[]
    if kind=='woodcutter':
        props.append(k.beam('chopping_stump',(0,-.88,0),(0,-.88,.76),.22,'bark',12,.19))
        props.append(k.beam('cut_wood',(0,-.88,.76),(0,-.88,.77),.185,'wood_light',12))
    elif kind=='farmer':
        props.append(k.box('worked_soil',(0,-.60,.027),(.72,.62,.05),'earth',.02))
        for j in range(4):props.append(k.beam('small_furrow',(-.3,-.85+j*.15,.05),(.3,-.85+j*.15,.05),.024,'earth_light',5))
    if props:
        prop=k.pivot('WorkProp',(0,0,0),props);prop['humanWorkProp']=True
    actions=[]
    rest={p.name:data.bones[p.name].matrix_local.copy() for p in rig.pose.bones}
    def control(name,pos,tilt=0):
        p=rig.pose.bones[name]
        orientation=Matrix.Rotation(tilt,4,'X') @ rest[name].to_3x3().to_4x4()
        orientation.translation=pos;p.matrix=orientation
    for mode in ['Idle','Walk','Work']:
        rig.animation_data_create();rig.animation_data.action=None
        action=b.data.actions.new(mode);action.use_fake_user=True;rig.animation_data.action=action
        for frame in range(73):
            t=frame/72*math.tau
            for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
            spine=rig.pose.bones['Spine'];spine.location.y=-.022
            spine.rotation_euler.x=.009*math.sin(t)
            rig.pose.bones['Head'].rotation_euler.y=.035*math.sin(t)
            for s,side in [(1,'R'),(-1,'L')]:
                phase=t+(0 if s==1 else math.pi);stride=math.sin(phase)
                control('FootTarget'+side,(s*.13,-.19*stride if mode=='Walk' else 0,.16+(.075*max(0,math.cos(phase)) if mode=='Walk' else 0)))
                control('HandTarget'+side,(s*.39,-.10+(.15*stride if mode=='Walk' else .008*math.sin(t+s)),.91))
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
                else:
                    control('HandTargetL',(-.14,-.35,1.10),-.9)
                    control('HandTargetR',(.03+.11*math.cos(t),-.36+.05*math.sin(t),1.15+.045*math.sin(t)),.8)
            b.context.view_layer.update()
            for p in rig.pose.bones:
                if p.name.startswith(('FootTarget','HandTarget')) or p.name in ['Spine','Head']:
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
